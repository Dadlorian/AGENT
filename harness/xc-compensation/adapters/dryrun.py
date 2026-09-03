#!/usr/bin/env python3
"""Dry-run register: a per-run step journal held by the execution engine, in
process, no network.

This is the register xc-compensation-implement's `today` row describes, built
out and run here: declare_effect is a journalled entry written before the
effect's own activity, seal_effect a second entry carrying the response
reference, unwind a reverse walk the engine drives over its own history, and
unwind_plan a read of that history before the run continues. The engine it
describes is installed and not listening on this host (F-a6-02), so the honest
thing this adapter can be is the same execution model with the server's role
played in process: the history is durable, and the reverse walk is driven by
replaying it into the code that declared the steps.

Declared gap, and the axis that makes the pair a pair: `unwinds_from_cold_reader
= False`. A process that did not register the declaring code as a worker cannot
unwind a run here, however much of the history it can see - which is why the
second register exists. The conformance run asserts this register behaves as
declared rather than widening the contract until both members satisfy it.
"""
from __future__ import annotations

import os
import sys
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (CompensationRecord, CompensationRegister, DeclareEffect,  # noqa: E402
                       Problem, UnwindPlan, UnwindReport)
from store import ChainedLog                                                     # noqa: E402


class EngineJournalRegister(CompensationRegister):
    register_marker = "engine-step-journal/0.1"
    where_the_register_lives = "the step journal of the engine that owns the run's history"
    what_must_be_up_to_unwind = "the declaring code registered as a worker of this engine"
    what_drives_the_reverse_walk = "the engine replaying its own history into the declaring code"
    unwinds_from_cold_reader = False
    processes_required_for_progress = 1        # in process here; a server plus a worker when hosted

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.log = ChainedLog(os.path.join(out_dir, "engine-journal.jsonl"))
        self._handlers: dict[str, Callable[[dict], str]] = {}

    # -- the four operations -------------------------------------------------
    def _declare(self, req: DeclareEffect) -> CompensationRecord:
        rec = CompensationRecord(
            run_id=req.run_id, step_id=req.step_id, effect_digest=req.effect_digest,
            irreversibility=req.irreversibility, idempotency_key=req.idempotency_key,
            declared_at_head="", state="declared",
            compensating_action=(req.compensating_action.dict() if req.compensating_action else None),
            mandate_ref=req.mandate_ref, correlation_id=req.correlation_id,
            actor=req.actor, entry_kind=req.entry_kind, register_observed=self.register_marker)
        row = self.log.append(kind="declare", run_id=req.run_id, step_id=req.step_id,
                              record=rec.dict())
        rec.declared_at_head = row["hash"]        # durable now, before the effect
        return rec

    def seal_effect(self, record: CompensationRecord, response_ref: str) -> CompensationRecord:
        row = self.log.append(kind="seal", run_id=record.run_id, step_id=record.step_id,
                              sealed_response_ref=response_ref,
                              declared_at_head=record.declared_at_head)
        record.state, record.committed_at_head = "committed", row["hash"]
        record.sealed_response_ref = response_ref
        return record

    def unwind(self, run_id: str, reason: str,
               executor: Callable[[dict], str] | None = None,
               stop_after: int | None = None) -> UnwindReport:
        if not self._handlers:
            # The declared gap, honoured rather than papered over: this register
            # replays history into the declaring code, so a dispatcher handed in
            # at unwind time is not enough. A caller reads a typed 503, never a
            # half-done walk.
            raise Problem("adapter-unavailable",
                          f"no worker registered here to replay {run_id}'s history into; "
                          "this register drives the reverse walk from the declaring code",
                          adapter=self.register_marker)
        # Every record, not only the sealed ones: a run killed between the
        # effect and its seal leaves a declared record whose effect may have
        # happened, and that is exactly the one an unwind must attempt.
        return self._walk(self.records(run_id), reason, self._dispatch, stop_after, self._save)

    def unwind_plan(self, run_id: str) -> UnwindPlan:
        plan = UnwindPlan(run_id=run_id, register_observed=self.register_marker)
        for rec in reversed(self.records(run_id)):   # declared as well as sealed:
            # a plan is read before the first effect, not only after the last
            entry = {"step_id": rec.step_id, "irreversibility": rec.irreversibility,
                     "operator": (rec.compensating_action or {}).get("operator")}
            if rec.irreversibility == "irreversible":
                plan.unreachable.append({**entry, "mandate_ref": rec.mandate_ref})
            else:
                plan.would_unwind.append(entry)
        return plan

    # -- the reads -----------------------------------------------------------
    def records(self, run_id: str) -> list[CompensationRecord]:
        return self._fold(self.log.of(run_id))

    def head(self) -> str:
        return self.log.head()

    def head_ordinal(self, head: str) -> int:
        return self.log.ordinal(head)

    # -- internals -----------------------------------------------------------
    def _dispatch(self, action: dict) -> str:
        handler = self._handlers.get(action.get("operator", ""))
        if handler is None:
            raise Problem("adapter-unavailable",
                          f"operator {action.get('operator')!r} is not registered on this worker")
        return handler(action)

    def _save(self, rec: CompensationRecord) -> None:
        """Append-only: an outcome is a further record referencing the one it
        undoes, never an edit of it (xc-compensation invariant 5)."""
        self.log.append(kind="outcome", run_id=rec.run_id, step_id=rec.step_id,
                        state=rec.state, unwind_reason=rec.unwind_reason, note=rec.note,
                        sealed_response_ref=rec.sealed_response_ref)


# The one name every adapter module exports: the entry point of this module.
Adapter = EngineJournalRegister
