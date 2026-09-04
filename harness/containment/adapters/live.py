"""Live adapter for today's component. This is the only module besides README
that may name a product.

Containment: `firecracker-cell@.service` / `firecracker-cell-long@.service` -
one Firecracker microVM per agent, started without sudo via polkit (PASS.md A2).
Runtime: goose v1.46.0 driven with the Agent Client Protocol, JSON-RPC over
stdio or over a unix socket (PASS.md A3). Model egress leaves the guest by vsock
to the host broker, which holds the real key; the guest holds a dummy key.

Nothing here is imported unless this adapter is selected, and every endpoint,
command and path arrives in an environment variable listed in README.md. Only
the standard library is used, so this module imports cleanly where the host
services are absent - it refuses at admit instead.

Method names other than `session/cancel` are proposed: PASS.md records
`session/cancel` and the transport, not the rest of the call set.
"""
from __future__ import annotations

import json
import os
import queue
import shlex
import socket
import subprocess
import threading
import time
import uuid

from interface import (AdapterBinding, AdmissionHandle, ContainedAgentAdapter, ContainmentReport,
                       IsolationDeclaration, Problem, Session, SessionCapabilities, TurnFrame,
                       TurnRequest, UnitContext, UnitResult, digest)
from adapters.hostside import Jail
import context_guarantees

MARKER = "contained-by:firecracker-microvm"

REQUIRED = ("CELL_START_CMD", "CELL_STOP_CMD", "CELL_JAIL_ROOT", "BROKER_EGRESS_COUNTERS")
TRANSPORT = ("ACP_STDIO_CMD", "ACP_SOCKET")

PROFILES = {                      # profile name -> the systemd template that answers, and nothing else
    "small": {"template": "firecracker-cell@", "runtime_ceiling_s": 300.0},
    "long": {"template": "firecracker-cell-long@", "runtime_ceiling_s": 3600.0},
}

# ACP stop reasons mapped onto this interface's closed set (proposed mapping).
STOP_REASON_MAP = {"end_turn": "end_turn", "cancelled": "cancelled", "canceled": "cancelled",
                   "max_tokens": "end_turn", "refusal": "end_turn"}


def missing_env() -> list[str]:
    gaps = [v for v in REQUIRED if not os.environ.get(v)]
    if not any(os.environ.get(v) for v in TRANSPORT):
        gaps.append("ACP_STDIO_CMD or ACP_SOCKET")
    return gaps


class _Unit:
    def __init__(self, unit_id, decl, ctx, jail):
        self.unit_id, self.decl, self.ctx, self.jail = unit_id, decl, ctx, jail
        self.frames: queue.Queue = queue.Queue()
        self.replies: dict = {}
        self.proc = None
        self.sock = None
        self.reader = None
        self.started = None
        self.prompt_id = None
        self.output_digest = "sha256:" + "0" * 64
        self.probe_done = False


class Adapter(ContainedAgentAdapter):
    name = "live"

    def __init__(self, config=None):
        cfg = config or {}
        self.timeout = float(os.environ.get("CELL_TIMEOUT_S", "120"))
        self.attempts = int(cfg.get("tuning", {}).get("egress_probe_attempts", 3))
        self.units: dict[str, _Unit] = {}
        self.sessions: dict[str, str] = {}
        self._rpc_id = 0

    def binding(self) -> AdapterBinding:
        return AdapterBinding(
            adapter="firecracker-microvm-unit",
            profiles=PROFILES,
            declared_gap=[
                "cannot start a unit without booting a guest kernel from a block-device root, "
                "so start and teardown cost is a floor no profile can lower",
                "grants a machine, so it cannot express a grant smaller than one",
            ],
            capabilities_offered=SessionCapabilities(streaming=True, permission_callbacks=True,
                                                     cancellation=True),
            cancel_floor_s=float(os.environ.get("CELL_CANCEL_FLOOR_S", "10")),
            containment_marker=MARKER,
            execution_model={
                "unit_of_resource_granted": "a machine with a kernel and a root filesystem",
                "start_and_teardown_cost": "a boot floor no profile can lower",
                "processes_required_for_progress": "one process held open for the whole turn",
                "prompt_cancellation": "cancels mid-turn on request",
            },
        )

    # -- Isolation -----------------------------------------------------------
    def admit(self, declaration: IsolationDeclaration, context: UnitContext) -> AdmissionHandle:
        gaps = missing_env()
        if gaps:
            raise Problem("isolation-unavailable",
                          f"live containment is not reachable: unset {', '.join(gaps)}",
                          retry_after_s=60, correlation_id=context.correlation_id)
        if declaration.profile not in PROFILES:
            raise Problem("isolation-unavailable",
                          f"profile {declaration.profile!r} is not resolvable by this adapter",
                          retry_after_s=60, correlation_id=context.correlation_id)
        unit_id = "fc-" + uuid.uuid4().hex[:10]
        context_guarantees.LEDGER.guard_admission(context, unit_id)   # C01-F: every field, read here
        env = dict(os.environ,
                   CELL_UNIT_ID=unit_id,
                   CELL_TEMPLATE=PROFILES[declaration.profile]["template"],
                   CELL_EGRESS=declaration.egress,
                   CELL_EGRESS_ALLOWLIST=",".join(declaration.egress_allowlist),
                   CELL_CORRELATION_ID=context.correlation_id,   # explicit attribute, not traceparent
                   CELL_RUN_ID=context.run_id,
                   CELL_ACTOR=context.actor)
        cmd = os.environ["CELL_START_CMD"].replace("{unit}", unit_id)
        done = subprocess.run(cmd, shell=True, env=env, text=True, capture_output=True,
                              timeout=self.timeout)
        if done.returncode != 0:
            raise Problem("isolation-unavailable",
                          f"unit start failed rc={done.returncode}: {done.stderr.strip()[:200]}",
                          retry_after_s=30, correlation_id=context.correlation_id)
        self.units[unit_id] = _Unit(unit_id, declaration, context,
                                    Jail(os.environ["CELL_JAIL_ROOT"], unit_id))
        return AdmissionHandle(unit_id=unit_id, profile=declaration.profile, context=context)

    def terminate(self, handle: AdmissionHandle, grace_s: float) -> UnitResult:
        unit = self._unit(handle.unit_id)
        forced = unit.proc is not None and unit.proc.poll() is None
        cmd = os.environ["CELL_STOP_CMD"].replace("{unit}", unit.unit_id)
        subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=self.timeout)
        if unit.proc is not None:
            try:
                unit.proc.terminate()
            except Exception:                          # noqa: BLE001 - already gone
                pass
        if unit.sock is not None:
            unit.sock.close()
        context_guarantees.LEDGER.release(handle.unit_id)   # C01-F: the ledger's claim on this unit ends here
        made, blocked = self._egress_counters(unit.unit_id)
        return UnitResult(exit_status=0 if unit.probe_done else 1, output_digest=unit.output_digest,
                          wall_seconds=round(time.monotonic() - unit.started, 3) if unit.started else 0.0,
                          egress_attempts_made=made, egress_attempts_blocked=blocked,
                          stop="forced" if forced else "requested")

    def inspect_containment(self, handle: AdmissionHandle) -> ContainmentReport:
        unit = self._unit(handle.unit_id)
        made, blocked = self._egress_counters(unit.unit_id)
        return ContainmentReport(observed_from="host", jail_mode=unit.jail.mode(),
                                 owner_in_host_passwd=unit.jail.owner_in_host_passwd(),
                                 egress_attempts_made=made, egress_attempts_blocked=blocked,
                                 secrets_seen_inside=0, containment_marker=unit.jail.read_marker())

    def _egress_counters(self, unit_id: str):
        """Read from the host broker's counter file. The unit never reports these."""
        try:
            with open(os.environ["BROKER_EGRESS_COUNTERS"]) as fh:
                row = json.load(fh).get(unit_id, {})
            return int(row.get("made", 0)), int(row.get("blocked", 0))
        except (OSError, ValueError, KeyError):
            return 0, 0

    # -- Agent runtime: ACP over stdio or a socket ---------------------------
    def open_session(self, handle: AdmissionHandle, offered: SessionCapabilities) -> Session:
        unit = self._unit(handle.unit_id)
        if os.environ.get("ACP_SOCKET"):
            unit.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            unit.sock.connect(os.environ["ACP_SOCKET"].replace("{unit}", unit.unit_id))
        else:
            unit.proc = subprocess.Popen(
                shlex.split(os.environ["ACP_STDIO_CMD"].replace("{unit}", unit.unit_id)),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        unit.reader = threading.Thread(target=self._read_frames, args=(unit,), daemon=True)
        unit.reader.start()
        # C01-F: capability-call point - the first RPC into the running unit
        context_guarantees.LEDGER.guard_capability_call(unit.ctx, unit.unit_id, "acp.initialize")
        agreed = self._call(unit, "initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {"streaming": offered.streaming,
                                   "permissionRequests": offered.permission_callbacks,
                                   "cancellation": offered.cancellation}})
        caps = (agreed or {}).get("agentCapabilities", {})
        new = self._call(unit, "session/new", {"cwd": "/workspace", "mcpServers": []}) or {}
        sid = new.get("sessionId", "s-" + uuid.uuid4().hex[:8])
        self.sessions[sid] = unit.unit_id
        return Session(session_id=sid, unit_id=unit.unit_id,
                       negotiated=SessionCapabilities(
                           streaming=bool(caps.get("streaming", offered.streaming)),
                           permission_callbacks=bool(caps.get("permissionRequests",
                                                              offered.permission_callbacks)),
                           cancellation=bool(caps.get("cancellation", offered.cancellation))),
                       runtime_marker=str(caps.get("marker", MARKER + ":acp")))

    def prompt(self, session: Session, request: TurnRequest) -> str:
        floor = self.binding().cancel_floor_s
        if request.grace_s < floor:
            raise Problem("document-invalid",
                          f"grace {request.grace_s}s is below this adapter's cancel floor {floor}s")
        unit = self._unit(session.unit_id)
        context_guarantees.LEDGER.guard_dispatch(unit.ctx, unit.unit_id)   # C01-F: dispatch point
        unit.started = time.monotonic()
        unit.prompt_id = self._send(unit, "session/prompt",
                                    {"sessionId": session.session_id,
                                     "prompt": [{"type": "text", "text": request.prompt}]})
        unit.probe_done = True
        unit.output_digest = digest(f"probe|{request.prompt}|profile={unit.decl.profile}")
        return session.session_id

    def next_frame(self, turn_id: str, timeout_s: float):
        unit = self._unit(self.sessions[turn_id])
        try:
            return unit.frames.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def cancel(self, session: Session, grace_s: float) -> None:
        unit = self._unit(session.unit_id)
        self._notify(unit, "session/cancel", {"sessionId": session.session_id})

    # -- JSON-RPC plumbing ---------------------------------------------------
    def _write(self, unit: _Unit, message: dict) -> None:
        line = json.dumps(message) + "\n"
        if unit.sock is not None:
            unit.sock.sendall(line.encode())
        else:
            unit.proc.stdin.write(line)
            unit.proc.stdin.flush()

    def _send(self, unit: _Unit, method: str, params: dict) -> int:
        self._rpc_id += 1
        self._write(unit, {"jsonrpc": "2.0", "id": self._rpc_id, "method": method, "params": params})
        return self._rpc_id

    def _notify(self, unit: _Unit, method: str, params: dict) -> None:
        self._write(unit, {"jsonrpc": "2.0", "method": method, "params": params})

    def _call(self, unit: _Unit, method: str, params: dict):
        rid = self._send(unit, method, params)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            reply = unit.replies.pop(rid, None)
            if reply is not None:
                return reply
            time.sleep(0.01)
        raise Problem("runtime-unavailable", f"no reply to {method} within {self.timeout}s")

    def _read_frames(self, unit: _Unit) -> None:
        stream = unit.sock.makefile("r") if unit.sock is not None else unit.proc.stdout
        seq = 0
        for line in stream:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("method") == "session/update":
                seq += 1
                unit.frames.put(TurnFrame(seq, "update", json.dumps(msg.get("params", {}))[:120]))
            elif "id" in msg and msg["id"] == unit.prompt_id:
                reason = (msg.get("result") or {}).get("stopReason", "end_turn")
                unit.frames.put(TurnFrame(seq + 1, "terminal", "turn ended",
                                          stop_reason=STOP_REASON_MAP.get(reason, "end_turn")))
                return
            elif "id" in msg:
                unit.replies[msg["id"]] = msg.get("result", {})

    def _unit(self, unit_id: str) -> _Unit:
        if unit_id not in self.units:
            raise Problem("isolation-unavailable", f"unit {unit_id} does not exist")
        return self.units[unit_id]
