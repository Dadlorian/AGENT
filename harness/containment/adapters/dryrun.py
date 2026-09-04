"""Dry-run adapter: one contained unit simulated in this process.

Execution model it stands for: a machine is granted, a process is held open for
the whole turn, and the runtime cancels itself mid-turn when asked. Deterministic,
no network, no privileges. Containment is still asserted from outside the unit -
the host creates and stats the directory, and the host-side broker decides every
egress attempt - so the report is produced by the host, never by the unit.

What this adapter is not: a hardware boundary. That is its first declared gap.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid

from interface import (AdapterBinding, AdmissionHandle, ContainedAgentAdapter, ContainmentReport,
                       IsolationDeclaration, LifecycleCapabilities, Problem, Session,
                       SessionCapabilities, SnapshotHandle, TurnFrame, TurnRequest, UnitContext,
                       UnitResult, digest)
from adapters.hostside import Broker, Jail
import context_guarantees

MARKER = "contained-by:simulated-machine-unit"

PROFILES = {                       # the two unit shapes on this substrate, behind one declaration
    "small": {"runtime_ceiling_s": 5.0, "grant": "one machine"},
    "long": {"runtime_ceiling_s": 60.0, "grant": "one machine, larger runtime ceiling"},
}


class _Unit:
    def __init__(self, unit_id, decl, ctx, jail, broker):
        self.unit_id, self.decl, self.ctx = unit_id, decl, ctx
        self.jail, self.broker = jail, broker
        self.frames: queue.Queue = queue.Queue()
        self.cancel_requested = False
        self.killed = False
        self.thread = None
        self.started = None
        self.output_digest = "sha256:" + "0" * 64
        self.probe_done = False
        self.paused = False


class Adapter(ContainedAgentAdapter):
    name = "dryrun"

    def __init__(self, config=None):
        cfg = config or {}
        self.poll = float(cfg.get("tuning", {}).get("cancel_poll_interval_s", 0.02))
        self.attempts = int(cfg.get("tuning", {}).get("egress_probe_attempts", 3))
        self.jail_root = cfg.get("jail_root", os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "out", "jails", "dryrun"))
        self.units: dict[str, _Unit] = {}
        self.sessions: dict[str, str] = {}
        self.snapshots: dict[str, dict] = {}

    # -- configuration -------------------------------------------------------
    def binding(self) -> AdapterBinding:
        return AdapterBinding(
            adapter="simulated-machine-unit",
            profiles=PROFILES,
            declared_gap=[
                "no hardware boundary: the unit is simulated in this process",
                "cannot serve a real model call; the broker hands out a dummy credential only",
            ],
            capabilities_offered=SessionCapabilities(streaming=True, permission_callbacks=True,
                                                     cancellation=True),
            cancel_floor_s=0.05,
            containment_marker=MARKER,
            execution_model={
                "unit_of_resource_granted": "a machine with a kernel and a root filesystem",
                "start_and_teardown_cost": "a boot floor no profile can lower",
                "processes_required_for_progress": "one process held open for the whole turn",
                "prompt_cancellation": "cancels mid-turn on request",
            },
            lifecycle_offered=LifecycleCapabilities(pause=True, resume=True, fork=True),
        )

    # -- Isolation -----------------------------------------------------------
    def admit(self, declaration: IsolationDeclaration, context: UnitContext) -> AdmissionHandle:
        if declaration.profile not in PROFILES:
            raise Problem("isolation-unavailable",
                          f"profile {declaration.profile!r} is not resolvable by this adapter",
                          retry_after_s=60, correlation_id=context.correlation_id)
        unit_id = "u-" + uuid.uuid4().hex[:10]
        context_guarantees.LEDGER.guard_admission(context, unit_id)   # C01-F: every field, read here
        jail = Jail(self.jail_root, unit_id)
        allow = list(declaration.egress_allowlist) if declaration.egress == "allowlist" else []
        unit = _Unit(unit_id, declaration, context, jail, Broker(allow))
        jail.write_marker(MARKER)                       # the running unit marks itself
        self.units[unit_id] = unit
        return AdmissionHandle(unit_id=unit_id, profile=declaration.profile, context=context)

    def terminate(self, handle: AdmissionHandle, grace_s: float) -> UnitResult:
        unit = self._unit(handle.unit_id)
        forced = unit.thread is not None and unit.thread.is_alive()
        unit.killed = True
        if unit.thread is not None:
            unit.thread.join(timeout=max(grace_s, 0.1))
        context_guarantees.LEDGER.release(handle.unit_id)   # C01-F: the ledger's claim on this unit ends here
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

    # -- Machine-state lifecycle ----------------------------------------------
    # A microVM class offers these; this adapter stands for one, so it serves
    # them for real (in-process) rather than declaring the gap. `_state` is the
    # unit's memory (its declared shape and turn progress) plus its filesystem
    # (the jail's marker file and mode) - the two halves a snapshot must cover.
    def _state(self, unit: _Unit) -> dict:
        return {
            "profile": unit.decl.profile, "egress": unit.decl.egress,
            "egress_allowlist": list(unit.decl.egress_allowlist),
            "probe_done": unit.probe_done, "output_digest": unit.output_digest,
            "cancel_requested": unit.cancel_requested, "killed": unit.killed,
            "egress_made": unit.broker.made, "egress_blocked": unit.broker.blocked,
            "marker": unit.jail.read_marker(), "jail_mode": unit.jail.mode(),
        }

    def state_digest(self, handle: AdmissionHandle) -> str:
        """The same digest pause and resume compute. Exposed so a caller (or the
        lifecycle check) can assert it is unchanged before any further syscall."""
        return digest(json.dumps(self._state(self._unit(handle.unit_id)), sort_keys=True))

    def pause(self, handle: AdmissionHandle) -> SnapshotHandle:
        unit = self._unit(handle.unit_id)
        snapshot_id = "snap-" + uuid.uuid4().hex[:10]
        state = self._state(unit)
        self.snapshots[snapshot_id] = {"unit_id": unit.unit_id, "state": state, "decl": unit.decl,
                                       "context": unit.ctx}
        unit.paused = True
        return SnapshotHandle(snapshot_id=snapshot_id, unit_id=unit.unit_id,
                              state_digest=digest(json.dumps(state, sort_keys=True)))

    def resume(self, snapshot: SnapshotHandle) -> AdmissionHandle:
        if snapshot.snapshot_id not in self.snapshots:
            raise Problem("isolation-unavailable", f"snapshot {snapshot.snapshot_id} does not exist")
        rec = self.snapshots[snapshot.snapshot_id]
        return AdmissionHandle(unit_id=self._restore(rec), profile=rec["decl"].profile,
                               context=rec["context"])

    def fork(self, handle: AdmissionHandle) -> AdmissionHandle:
        """Clone the running (or paused) unit from its current state, without
        re-provisioning: `admit`'s declaration resolution never runs again."""
        unit = self._unit(handle.unit_id)
        rec = {"decl": unit.decl, "state": self._state(unit), "context": unit.ctx}
        return AdmissionHandle(unit_id=self._restore(rec), profile=unit.decl.profile, context=unit.ctx)

    def _restore(self, rec: dict) -> str:
        """Shared by resume and fork: materialize a fresh unit from a state dict,
        restoring memory and filesystem exactly, provisioning nothing new."""
        decl, state = rec["decl"], rec["state"]
        unit_id = "u-" + uuid.uuid4().hex[:10]
        jail = Jail(self.jail_root, unit_id)
        broker = Broker(list(decl.egress_allowlist) if decl.egress == "allowlist" else [])
        broker.made, broker.blocked = state["egress_made"], state["egress_blocked"]
        unit = _Unit(unit_id, decl, rec["context"], jail, broker)
        jail.write_marker(state["marker"])
        unit.probe_done, unit.output_digest = state["probe_done"], state["output_digest"]
        unit.cancel_requested, unit.killed = state["cancel_requested"], state["killed"]
        self.units[unit_id] = unit
        return unit_id

    # -- Agent runtime -------------------------------------------------------
    def open_session(self, handle: AdmissionHandle, offered: SessionCapabilities) -> Session:
        mine = self.binding().capabilities_offered
        negotiated = SessionCapabilities(
            streaming=offered.streaming and mine.streaming,
            permission_callbacks=offered.permission_callbacks and mine.permission_callbacks,
            cancellation=offered.cancellation and mine.cancellation,
        )
        sid = "s-" + uuid.uuid4().hex[:8]
        self.sessions[sid] = handle.unit_id
        return Session(session_id=sid, unit_id=handle.unit_id, negotiated=negotiated,
                       runtime_marker=MARKER + ":interactive")

    def prompt(self, session: Session, request: TurnRequest) -> str:
        floor = self.binding().cancel_floor_s
        if request.grace_s < floor:
            raise Problem("document-invalid",
                          f"grace {request.grace_s}s is below this adapter's cancel floor {floor}s")
        unit = self._unit(session.unit_id)
        context_guarantees.LEDGER.guard_dispatch(unit.ctx, unit.unit_id)   # C01-F: dispatch point
        unit.started = time.monotonic()
        unit.thread = threading.Thread(target=self._turn, args=(unit, session, request), daemon=True)
        unit.thread.start()
        return session.session_id

    def next_frame(self, turn_id: str, timeout_s: float):
        unit = self._unit(self.sessions[turn_id])
        try:
            return unit.frames.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def cancel(self, session: Session, grace_s: float) -> None:
        unit = self._unit(session.unit_id)
        unit.cancel_requested = True          # acceptance, not a kill

    # -- the simulated unit --------------------------------------------------
    def _turn(self, unit: _Unit, session: Session, request: TurnRequest) -> None:
        seq = 0
        try:
            # C01-F: capability-call point - the first reach for a broker capability
            context_guarantees.LEDGER.guard_capability_call(unit.ctx, unit.unit_id,
                                                             "broker.credential_for_unit")
        except Problem as problem:
            unit.frames.put(TurnFrame(1, "terminal", f"capability call refused: {problem.body['detail']}",
                                      stop_reason="terminated"))
            return
        cred = unit.broker.credential_for_unit()               # a dummy key, from the host broker
        for _ in range(self.attempts):                          # the probe attempts egress
            unit.broker.connect("models.internal:443")
        unit.output_digest = digest(f"probe|{request.prompt}|profile={unit.decl.profile}|cred={len(cred)}")
        unit.probe_done = True
        if session.negotiated.streaming:
            seq += 1
            unit.frames.put(TurnFrame(seq, "update", "egress probe complete"))
        next_check = unit.started + self.poll
        while True:
            now = time.monotonic()
            if unit.killed:
                return                                          # destroyed from outside: no more frames
            if now >= next_check:
                next_check = now + self.poll
                if unit.cancel_requested:
                    unit.frames.put(TurnFrame(seq + 1, "terminal", "cancelled mid-tool-call",
                                              stop_reason="cancelled"))
                    return
                if session.negotiated.streaming:
                    seq += 1
                    unit.frames.put(TurnFrame(seq, "update", f"tool call running t={now - unit.started:.2f}s"))
            if now - unit.started >= request.op_seconds:
                unit.frames.put(TurnFrame(seq + 1, "terminal", "tool call finished", stop_reason="end_turn"))
                return
            time.sleep(0.005)

    def _unit(self, unit_id: str) -> _Unit:
        if unit_id not in self.units:
            raise Problem("isolation-unavailable", f"unit {unit_id} does not exist")
        return self.units[unit_id]
