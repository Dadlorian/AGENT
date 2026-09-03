#!/usr/bin/env python3
"""Second adapter: a queue plus a state machine, on the same journal.

Chosen because it breaks the assumptions the first one rests on, not because it
is another engine of the same shape.

  axis                              dry-run                    this one
  --------------------------------  -------------------------  -----------------------
  effect_commit_mode                keyed_effect               same_transaction
  resume_derivation                 fold the whole history     read the last state row
  replay_determinism_required       True                       False

How it works. A checkpoint is not a single append: it is enqueued as one pending
transition, then drained. Draining appends the step record (with the step's own
effect embedded in it), projects the effect onto the external table, writes a
materialised `machine-state` row carrying the completed-key set and the spend so
far, and marks the transition applied. begin_run drains first, so a process that
died between enqueue and drain finishes its predecessor's commit before doing
anything else - a state the dry-run executor cannot be in, reported as
pending_recovered.

Because the effect travels inside the committed record, this executor has no
window between the effect and the checkpoint: a crash before the commit leaves
no orphan effect row. That is a different guarantee, not a better one, and the
conformance run asserts each executor behaved as its own declaration says.

Declared gaps: it cannot commit an effect that lives outside this store in one
transaction (such an effect falls back to the caller's key), it keeps no history
to replay, and it offers no view of a run from a process that cannot read these
files.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (BeginRun, Checkpoint, DurableExecutor, GateOutcome,  # noqa: E402
                       GateRecord, Problem, Receipt, RunState, StepRecord, gate_parts)
from adapters.journal import EffectTable, Journal  # noqa: E402
from adapters.dryrun import _receipt, _record  # noqa: E402


class QueueStateMachineExecutor(DurableExecutor):
    executor_marker = "queue-state-machine/0.1"
    effect_commit_mode = "same_transaction"
    replay_determinism_required = False
    processes_required_for_progress = 1
    resume_derivation = "read-materialised-state"

    def __init__(self, out_dir: str):
        self.journal = Journal(os.path.join(out_dir, "journal.jsonl"))
        self.queue = Journal(os.path.join(out_dir, "queue.jsonl"))
        self.effects = EffectTable(os.path.join(out_dir, "effects.jsonl"))
        self.recovered = 0

    # -- the state machine ---------------------------------------------------
    def _pending(self) -> list[dict]:
        applied = {r["txn_id"] for r in self.queue.records if r.get("kind") == "applied"}
        return [r for r in self.queue.records
                if r.get("kind") == "transition" and r["txn_id"] not in applied]

    def _drain(self) -> int:
        drained = 0
        for txn in self._pending():
            req = txn["step"]
            state_row = self.journal.tail(req["run_key"], "machine-state")
            keys = list(state_row["completed_keys"]) if state_row else []
            spent = state_row["spent_micros"] if state_row else 0
            if req["step_idempotency_key"] not in keys or req["step_idempotency_key"] is None:
                self.journal.append(kind="step-committed", committed_with_effect=bool(txn["effect"]),
                                    effect=txn["effect"], **req)
                if txn["effect"] is not None:
                    self.effects.ensure(req["step_idempotency_key"], txn["effect"])
                keys.append(req["step_idempotency_key"])
                spent += req["cost_micros"]
                self.journal.append(kind="machine-state", run_key=req["run_key"],
                                    position=len(keys), completed_keys=keys,
                                    spent_micros=spent, last_step_id=req["step_id"],
                                    executor_marker=self.executor_marker)
            self.queue.append(kind="applied", txn_id=txn["txn_id"], run_key=req["run_key"])
            drained += 1
        return drained

    # -- the four operations -------------------------------------------------
    def begin_run(self, req: BeginRun) -> RunState:
        broken = self.journal.verify() or self.queue.verify()
        if broken:
            raise Problem("idempotency-conflict",
                          f"run {req.run_key} cannot be resumed: {broken}",
                          correlation_id=req.correlation_id)
        self.recovered = self._drain()      # finish a predecessor's half-done commit
        state = self.resume_point(req.run_key)
        self.journal.append(kind="run-begun", run_key=req.run_key,
                            sequence_id=req.sequence_id, input_digest=req.input_digest,
                            correlation_id=req.correlation_id, actor=req.actor,
                            ceiling_micros=req.ceiling_micros,
                            executor_marker=self.executor_marker,
                            resumed_at=state.resume_point)
        state.executor_marker = self.executor_marker
        state.pending_recovered = self.recovered
        return state

    def checkpoint_step(self, req: Checkpoint) -> StepRecord:
        step = {"run_key": req.run_key, "step_id": req.step_id,
                "step_idempotency_key": req.step_idempotency_key, "state": req.state,
                "output_digest": req.output_digest, "cost_micros": req.cost_micros,
                "correlation_id": req.correlation_id, "actor": req.actor,
                "output": req.output}
        txn_id = f"{req.run_key}:{req.step_id}:{len(self.queue.records)}"
        self.queue.append(kind="transition", txn_id=txn_id, run_key=req.run_key,
                          step=step, effect=req.effect)
        self._drain()
        return _record({**step, "committed_with_effect": req.effect is not None})

    def resume_point(self, run_key: str) -> RunState:
        # One read of the materialised row, not a fold of the history.
        state_row = self.journal.tail(run_key, "machine-state")
        committed = [_record(r) for r in self.journal.of(run_key, "step-committed")]
        begun = self.journal.of(run_key, "run-begun")
        n = state_row["position"] if state_row else 0
        return RunState(run_key=run_key, resume_point=n, steps_committed=n,
                        steps_replayed=0,
                        terminal=bool(self.journal.of(run_key, "run-terminal")),
                        completed=committed,
                        spent_micros=state_row["spent_micros"] if state_row else 0,
                        executor_marker=self.executor_marker,
                        correlation_id=begun[0]["correlation_id"] if begun else None,
                        pending_recovered=self.recovered)

    def read_run(self, run_key: str) -> RunState:
        return self.resume_point(run_key)

    def read_receipt(self, run_key: str) -> Receipt:
        # Same shape, a different store underneath: the counts come off this
        # executor's own journal, not off a path a caller guessed.
        return _receipt(self.journal, self.effects, self.read_run(run_key))

    # -- the resume seam -----------------------------------------------------
    def park_gate(self, gate: GateRecord) -> None:
        run_key, gate_step_id = gate_parts(gate.gate_id)
        self.journal.append(kind="gate-parked", run_key=run_key, gate_step_id=gate_step_id,
                            gate_id=gate.gate_id, step_id=gate.step_id, view=gate.view,
                            decider=gate.decider, wires=gate.wires,
                            deadline_at=gate.deadline_at, outcomes=list(gate.outcomes),
                            return_to_step_id=gate.return_to_step_id,
                            correlation_id=gate.correlation_id)

    def record_decision(self, outcome: GateOutcome) -> bool:
        run_key, gate_step_id = gate_parts(outcome.gate_id)
        parked = [r for r in self.journal.of(run_key, "gate-parked")
                  if r["gate_id"] == outcome.gate_id]
        if not parked:
            raise Problem("document-invalid", f"no parked gate {outcome.gate_id}")
        closed = [r for r in self.journal.of(run_key, "step-committed")
                  if r["step_id"] == gate_step_id]
        prior = [r for r in self.journal.of(run_key, "gate-decided")
                 if r["gate_id"] == outcome.gate_id]
        if closed or any(r["idempotency_key"] == outcome.idempotency_key for r in prior):
            return False
        self.journal.append(kind="gate-decided", run_key=run_key, gate_id=outcome.gate_id,
                            outcome=outcome.outcome, actor=outcome.actor,
                            idempotency_key=outcome.idempotency_key, body=outcome.body,
                            delivered_over=outcome.delivered_over,
                            correlation_id=outcome.correlation_id)
        return True

    def mark_terminal(self, run_key: str, outcome: str, problem: dict | None = None) -> None:
        self.journal.append(kind="run-terminal", run_key=run_key, outcome=outcome,
                            problem=problem, executor_marker=self.executor_marker)


# The one name every adapter module exports: the entry point of this module.
# Binding is by module, never by a per-capability class-name table (the
# divergence harness/linked/components.py used to paper over). The descriptive
# class name above stays - `binding()` reports it, so a report still says which
# executor answered.
Adapter = QueueStateMachineExecutor
