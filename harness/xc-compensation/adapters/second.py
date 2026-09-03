#!/usr/bin/env python3
"""Second register: the same four operations with no engine at all - the
compensation records appended to the platform's own append-only chained log,
beside every other fact about the run.

This is the `second` row of xc-compensation-implement's adapter pair: "declare_
effect appends a compensation record to the platform's append-only chained log
conditional on the expected head, seal_effect appends a second record
referencing it, unwind is a fold of that log at a pinned head walked in reverse,
and unwind_plan is the same fold read forward." PASS.md B3 records the log
itself as the state-persistence adapter of today (F-b3-17, "JSONL + hash
chain"), so this register needs nothing installed that is not already running.

The three axes it differs from the first register on, which is why it is the
second and not a second workflow engine of the same shape:

  where_the_register_lives    an engine-held per-run journal | the platform's own log
  what_must_be_up_to_unwind   the declaring code as a worker | nothing beyond the log
  what_drives_the_reverse_walk history replayed into that code | a fold any process reads

Declared gap the other way round: `unwinds_from_cold_reader = True`. A process
that declared nothing, ran nothing and holds no handle unwinds a run here given
the log and a dispatcher. Its own gaps are the ones the implement facet records:
it cannot drive its own retries or timers, and it gives a total order within the
log rather than across partitions.

Conditional append: every append names the head it expected. In this harness the
log is a single local file and the check is a comparison; against a shared store
it is the store's own conditional write. The shape does not change when that
swap happens.
"""
from __future__ import annotations

import os
import sys
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (CompensationRecord, CompensationRegister, DeclareEffect,  # noqa: E402
                       Problem, UnwindPlan, UnwindReport)
from store import ChainedLog                                                     # noqa: E402


class ChainedLogRegister(CompensationRegister):
    register_marker = "chained-log-fold/0.1"
    where_the_register_lives = "records appended to the platform's own chained log"
    what_must_be_up_to_unwind = "nothing beyond the log: any process folds it at a pinned head"
    what_drives_the_reverse_walk = "a reader folding an ordered log, with no code replayed"
    unwinds_from_cold_reader = True
    processes_required_for_progress = 0        # no server of its own has to be up

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.log = ChainedLog(os.path.join(out_dir, "ledger.jsonl"))
        self._handlers: dict[str, Callable[[dict], str]] = {}

    def _append(self, expected_head: str | None, **fields) -> dict:
        """Conditional on the expected head, so a second writer that moved the
        log on is refused rather than silently interleaved."""
        if expected_head is not None and self.log.head() != expected_head:
            raise Problem("adapter-unavailable",
                          f"expected head {expected_head[:14]}… but the log is at "
                          f"{self.log.head()[:14]}…", adapter=self.register_marker)
        return self.log.append(**fields)

    # -- the four operations -------------------------------------------------
    def _declare(self, req: DeclareEffect) -> CompensationRecord:
        rec = CompensationRecord(
            run_id=req.run_id, step_id=req.step_id, effect_digest=req.effect_digest,
            irreversibility=req.irreversibility, idempotency_key=req.idempotency_key,
            declared_at_head="", state="declared",
            compensating_action=(req.compensating_action.dict() if req.compensating_action else None),
            mandate_ref=req.mandate_ref, correlation_id=req.correlation_id,
            actor=req.actor, entry_kind=req.entry_kind, register_observed=self.register_marker)
        row = self._append(self.log.head(), kind="declare", run_id=req.run_id,
                           step_id=req.step_id, record=rec.dict())
        rec.declared_at_head = row["hash"]        # durable now, before the effect
        return rec

    def seal_effect(self, record: CompensationRecord, response_ref: str) -> CompensationRecord:
        row = self._append(None, kind="seal", run_id=record.run_id, step_id=record.step_id,
                           sealed_response_ref=response_ref,
                           declared_at_head=record.declared_at_head)
        record.state, record.committed_at_head = "committed", row["hash"]
        record.sealed_response_ref = response_ref
        return record

    def unwind(self, run_id: str, reason: str,
               executor: Callable[[dict], str] | None = None,
               stop_after: int | None = None) -> UnwindReport:
        dispatcher = executor or (self._dispatch if self._handlers else None)
        if dispatcher is None:
            raise Problem("adapter-unavailable",
                          f"unwinding {run_id} needs a dispatcher for the declared operators; "
                          "this register folds the log but executes nothing itself",
                          adapter=self.register_marker)
        # Every record, not only the sealed ones (see adapters/dryrun.py).
        return self._walk(self.records(run_id), reason, dispatcher, stop_after, self._save)

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
                          f"operator {action.get('operator')!r} has no handler here")
        return handler(action)

    def _save(self, rec: CompensationRecord) -> None:
        self._append(None, kind="outcome", run_id=rec.run_id, step_id=rec.step_id,
                     state=rec.state, unwind_reason=rec.unwind_reason, note=rec.note,
                     sealed_response_ref=rec.sealed_response_ref)


# The one name every adapter module exports: the entry point of this module.
Adapter = ChainedLogRegister
