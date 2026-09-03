"""Second adapter: a different containment technology, not a different product
of the same shape.

Execution model it stands for: the unit is granted a set of capabilities rather
than a machine - no guest kernel, no root filesystem, no network stack at all -
and the runtime inside it is single-shot: one invocation produces one terminal
frame, it streams nothing, and it cannot be cancelled mid-turn. Where the first
adapter reports `cancelled`, this one reports `cancel_timeout` and the boundary
destroys the unit, which is the point: cancellation is enforced by containment,
not by the runtime's goodwill.

This runs as a faithful stub here. Set SECOND_SHIM_CMD to a runtime-spec shim
and the same calls exec it instead; the swap procedure is in README.md and does
not change either way.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
import uuid

from interface import (AdapterBinding, AdmissionHandle, ContainedAgentAdapter, ContainmentReport,
                       IsolationDeclaration, Problem, Session, SessionCapabilities, TurnFrame,
                       TurnRequest, UnitContext, UnitResult, digest)
from adapters.hostside import Broker, Jail

MARKER = "contained-by:capability-granted-unit"

PROFILES = {                       # the same profile names, resolved to capability grants
    "small": {"grants": ["clock", "broker-egress"], "runtime_ceiling_s": 5.0},
    "long": {"grants": ["clock", "broker-egress", "scratch-memory"], "runtime_ceiling_s": 60.0},
}


class _Unit:
    def __init__(self, unit_id, decl, ctx, jail, broker):
        self.unit_id, self.decl, self.ctx = unit_id, decl, ctx
        self.jail, self.broker = jail, broker
        self.frames: queue.Queue = queue.Queue()
        self.killed = False
        self.thread = None
        self.started = None
        self.output_digest = "sha256:" + "0" * 64
        self.probe_done = False


class Adapter(ContainedAgentAdapter):
    name = "second"

    def __init__(self, config=None):
        cfg = config or {}
        self.attempts = int(cfg.get("tuning", {}).get("egress_probe_attempts", 3))
        self.shim_cmd = os.environ.get("SECOND_SHIM_CMD", "")
        self.jail_root = cfg.get("jail_root", os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "out", "jails", "second"))
        self.units: dict[str, _Unit] = {}
        self.sessions: dict[str, str] = {}

    # -- configuration -------------------------------------------------------
    def binding(self) -> AdapterBinding:
        return AdapterBinding(
            adapter="capability-granted-unit",
            profiles=PROFILES,
            declared_gap=[
                "cannot be cancelled mid-turn: it reports cancel_timeout where an interactive "
                "runtime reports cancelled, and the boundary destroys the unit",
                "emits no in-turn frames and raises no permission request",
                "grants the unit no filesystem: the 0700 directory is the host's spool and is "
                "never mounted into the unit",
                "cannot honour boot arguments, block devices or a guest network interface, and "
                "does not claim hardware-level isolation",
            ],
            capabilities_offered=SessionCapabilities(streaming=False, permission_callbacks=False,
                                                     cancellation=False),
            cancel_floor_s=0.0,
            containment_marker=MARKER,
            execution_model={
                "unit_of_resource_granted": "a set of capabilities, with no kernel and no filesystem",
                "start_and_teardown_cost": "no boot: instantiation is part of the call",
                "processes_required_for_progress": "one invocation, nothing held open",
                "prompt_cancellation": "none: the boundary must destroy the unit",
            },
        )

    # -- Isolation -----------------------------------------------------------
    def admit(self, declaration: IsolationDeclaration, context: UnitContext) -> AdmissionHandle:
        if declaration.profile not in PROFILES:
            raise Problem("isolation-unavailable",
                          f"profile {declaration.profile!r} is not resolvable by this adapter",
                          retry_after_s=60, correlation_id=context.correlation_id)
        unit_id = "c-" + uuid.uuid4().hex[:10]
        jail = Jail(self.jail_root, unit_id)
        allow = list(declaration.egress_allowlist) if declaration.egress == "allowlist" else []
        unit = _Unit(unit_id, declaration, context, jail, Broker(allow))
        jail.write_marker(MARKER)          # instantiation is immediate: no boot to wait for
        self.units[unit_id] = unit
        return AdmissionHandle(unit_id=unit_id, profile=declaration.profile, context=context)

    def terminate(self, handle: AdmissionHandle, grace_s: float) -> UnitResult:
        unit = self._unit(handle.unit_id)
        forced = unit.thread is not None and unit.thread.is_alive()
        unit.killed = True
        if unit.thread is not None:
            unit.thread.join(timeout=max(grace_s, 0.1))
        return UnitResult(
            exit_status=0 if unit.probe_done else 1,
            output_digest=unit.output_digest,
            wall_seconds=round(time.monotonic() - unit.started, 3) if unit.started else 0.0,
            egress_attempts_made=unit.broker.made,
            egress_attempts_blocked=unit.broker.blocked,
            stop="forced" if forced else "requested",
        )

    def inspect_containment(self, handle: AdmissionHandle) -> ContainmentReport:
        unit = self._unit(handle.unit_id)
        return ContainmentReport(
            observed_from="host",
            jail_mode=unit.jail.mode(),
            owner_in_host_passwd=unit.jail.owner_in_host_passwd(),
            egress_attempts_made=unit.broker.made,
            egress_attempts_blocked=unit.broker.blocked,
            secrets_seen_inside=unit.broker.secrets_seen_inside(),
            containment_marker=unit.jail.read_marker(),
        )

    # -- Agent runtime -------------------------------------------------------
    def open_session(self, handle: AdmissionHandle, offered: SessionCapabilities) -> Session:
        sid = "s-" + uuid.uuid4().hex[:8]
        self.sessions[sid] = handle.unit_id
        # Nothing interactive is negotiated, whatever the caller offered.
        return Session(session_id=sid, unit_id=handle.unit_id,
                       negotiated=SessionCapabilities(), runtime_marker=MARKER + ":single-shot")

    def prompt(self, session: Session, request: TurnRequest) -> str:
        unit = self._unit(session.unit_id)
        unit.started = time.monotonic()
        unit.thread = threading.Thread(target=self._turn, args=(unit, request), daemon=True)
        unit.thread.start()
        return session.session_id

    def next_frame(self, turn_id: str, timeout_s: float):
        unit = self._unit(self.sessions[turn_id])
        try:
            return unit.frames.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def cancel(self, session: Session, grace_s: float) -> None:
        """Accepted and recorded. This runtime has no way to act on it; the
        declared gap says so, and the boundary is what actually stops the unit."""
        return None

    # -- one invocation ------------------------------------------------------
    def _turn(self, unit: _Unit, request: TurnRequest) -> None:
        cred = unit.broker.credential_for_unit()
        for _ in range(self.attempts):
            unit.broker.connect("models.internal:443")
        unit.output_digest = digest(f"probe|{request.prompt}|profile={unit.decl.profile}|cred={len(cred)}")
        unit.probe_done = True
        if self.shim_cmd:
            self._invoke_shim(unit, request)
            return
        while time.monotonic() - unit.started < request.op_seconds:   # one invocation, no poll loop
            if unit.killed:
                return
            time.sleep(0.005)
        unit.frames.put(TurnFrame(1, "terminal", "invocation returned", stop_reason="end_turn"))

    def _invoke_shim(self, unit: _Unit, request: TurnRequest) -> None:
        """The real path: hand the shim one declaration and one prompt, take one result."""
        payload = json.dumps({"profile": unit.decl.profile, "egress": unit.decl.egress,
                              "grants": PROFILES[unit.decl.profile]["grants"],
                              "prompt": request.prompt, "op_seconds": request.op_seconds})
        try:
            done = subprocess.run(self.shim_cmd, shell=True, input=payload, text=True,
                                  capture_output=True, timeout=request.op_seconds + 5)
            body = json.loads(done.stdout or "{}")
            unit.output_digest = digest(str(body.get("output", "")))
            unit.frames.put(TurnFrame(1, "terminal", "invocation returned", stop_reason="end_turn"))
        except Exception as exc:                       # noqa: BLE001 - reported as a typed problem
            unit.frames.put(TurnFrame(1, "terminal", f"{type(exc).__name__}: {exc}",
                                      stop_reason="terminated"))

    def _unit(self, unit_id: str) -> _Unit:
        if unit_id not in self.units:
            raise Problem("isolation-unavailable", f"unit {unit_id} does not exist")
        return self.units[unit_id]
