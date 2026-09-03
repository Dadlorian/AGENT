#!/usr/bin/env python3
"""Dry-run adapter: an in-process state machine journaled to a file.

Runs here, no network, deterministic. Durability is one append-only chained
journal; the resume point is derived by folding the whole history for a run key,
and the step's effect is deduplicated by the step's own idempotency key rather
than committed in the same transaction as the checkpoint.

Declared gaps (asserted by the conformance run, never widened away):
  - effect_commit_mode = keyed_effect: there is a window between the effect and
    the checkpoint. A crash inside it leaves an orphan effect row, and the retry
    is safe only because the key is on the table.
  - replay_determinism_required = True: the resume point is a fold of history, so
    the driver must re-walk the same flow to reach the same step.
  - It has no view of a run from any process that cannot read this file.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (BeginRun, Checkpoint, DurableExecutor, GateOutcome,  # noqa: E402
                       GateRecord, Problem, Receipt, RunState, StepRecord, gate_parts)
from adapters.journal import EffectTable, Journal  # noqa: E402


def _receipt(journal: Journal, effects: EffectTable, state: RunState) -> Receipt:
    """The caller's read, assembled from wherever this executor keeps its state.

    Both in-process executors keep it in the same journal, so they share this
    function; an executor with a server behind it would answer the same shape
    from the server, which is the point of the operation being on the interface
    rather than in a caller that knows about files.
    """
    return Receipt(
        run_key=state.run_key, executor_marker=state.executor_marker,
        resume_point=state.resume_point, steps_committed=state.steps_committed,
        terminal=state.terminal, spent_micros=state.spent_micros,
        gates_parked=len(journal.of(state.run_key, "gate-parked")),
        gates_decided=len(journal.of(state.run_key, "gate-decided")),
        effects=[r for r in effects.rows() if r.get("run_key") == state.run_key],
        problem=state.problem)


def _record(r: dict) -> StepRecord:
    return StepRecord(run_key=r["run_key"], step_id=r["step_id"],
                      step_idempotency_key=r.get("step_idempotency_key"),
                      state=r.get("state", "complete"),
                      committed_with_effect=r.get("committed_with_effect", False),
                      output_digest=r.get("output_digest", ""),
                      cost_micros=r.get("cost_micros", 0),
                      correlation_id=r.get("correlation_id", ""),
                      actor=r.get("actor", ""), output=r.get("output", {}))


class JournalExecutor(DurableExecutor):
    executor_marker = "in-process-journal/0.1"
    effect_commit_mode = "keyed_effect"
    replay_determinism_required = True
    processes_required_for_progress = 1
    resume_derivation = "fold-whole-history"

    def __init__(self, out_dir: str):
        self.journal = Journal(os.path.join(out_dir, "journal.jsonl"))
        self.effects = EffectTable(os.path.join(out_dir, "effects.jsonl"))

    # -- the four operations -------------------------------------------------
    def begin_run(self, req: BeginRun) -> RunState:
        broken = self.journal.verify()
        if broken:
            # A run whose record cannot be trusted is a typed failure, never a
            # silent restart from step one.
            raise Problem("idempotency-conflict",
                          f"run {req.run_key} cannot be resumed: {broken}",
                          correlation_id=req.correlation_id)
        state = self.resume_point(req.run_key)
        self.journal.append(kind="run-begun", run_key=req.run_key,
                            sequence_id=req.sequence_id, input_digest=req.input_digest,
                            correlation_id=req.correlation_id, actor=req.actor,
                            ceiling_micros=req.ceiling_micros,
                            executor_marker=self.executor_marker,
                            resumed_at=state.resume_point)
        state.executor_marker = self.executor_marker
        return state

    def checkpoint_step(self, req: Checkpoint) -> StepRecord:
        if req.effect is not None:
            raise Problem("adapter-unavailable",
                          "this executor declares effect_commit_mode keyed_effect and "
                          "cannot commit an effect in the same transaction")
        r = self.journal.append(
            kind="step-committed", run_key=req.run_key, step_id=req.step_id,
            step_idempotency_key=req.step_idempotency_key, state=req.state,
            committed_with_effect=False, output_digest=req.output_digest,
            cost_micros=req.cost_micros, correlation_id=req.correlation_id,
            actor=req.actor, output=req.output)
        return _record(r)

    def resume_point(self, run_key: str) -> RunState:
        committed = [_record(r) for r in self.journal.of(run_key, "step-committed")]
        begun = self.journal.of(run_key, "run-begun")
        terminal = bool(self.journal.of(run_key, "run-terminal"))
        return RunState(run_key=run_key, resume_point=len(committed),
                        steps_committed=len(committed), steps_replayed=0,
                        terminal=terminal, completed=committed,
                        spent_micros=sum(c.cost_micros for c in committed),
                        executor_marker=self.executor_marker,
                        correlation_id=begun[0]["correlation_id"] if begun else None)

    def read_run(self, run_key: str) -> RunState:
        return self.resume_point(run_key)

    def read_receipt(self, run_key: str) -> Receipt:
        return _receipt(self.journal, self.effects, self.read_run(run_key))

    # -- the resume seam a decision arrives on -------------------------------
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
            return False           # a redelivery, or the gate is already closed
        self.journal.append(kind="gate-decided", run_key=run_key, gate_id=outcome.gate_id,
                            outcome=outcome.outcome, actor=outcome.actor,
                            idempotency_key=outcome.idempotency_key, body=outcome.body,
                            delivered_over=outcome.delivered_over,
                            correlation_id=outcome.correlation_id)
        return True

    # -- used by the driver, not part of the contract -------------------------
    def mark_terminal(self, run_key: str, outcome: str, problem: dict | None = None) -> None:
        self.journal.append(kind="run-terminal", run_key=run_key, outcome=outcome,
                            problem=problem, executor_marker=self.executor_marker)


# The one name every adapter module exports: the entry point of this module.
# Binding is by module, never by a per-capability class-name table (the
# divergence harness/linked/components.py used to paper over). The descriptive
# class name above stays - `binding()` reports it, so a report still says which
# executor answered.
Adapter = JournalExecutor
