#!/usr/bin/env python3
"""Dry-run adapter: a synchronous standalone evaluator, in process, no queue.

Same instants every run: occurrences() and next_after() are the shared pure
evaluator (interface.py) unchanged; declare() and fire() run entirely inside
this call, with no ticker, no queue and nothing enqueued. tick() computes the
window directly and fires every occurrence it finds before returning. This is
the simplest thing that can run here with no network (the author brief's
"deterministic in-process adapter"); adapters/second.py implements the same
evaluator behind a ticker-plus-queue pipeline instead, which is the execution
model cap-scheduling-implement's step 2 actually describes.
"""
from __future__ import annotations

import os

from interface import Problem, ScheduleDeclaration, SchedulingAdapter, parse_instant


class DryRunAdapter(SchedulingAdapter):
    entity = "dry-run in-process standalone evaluator (synchronous)"
    adapter_name = "standalone-evaluator"
    declared_marker = "dryrun-standalone-sync"

    def _declare(self, decl: ScheduleDeclaration) -> ScheduleDeclaration:
        if os.environ.get("SCHEDULING_DRYRUN_FAIL") == "1":
            self.refused += 1
            raise Problem("adapter-unavailable",
                          "the dry-run evaluator was made unreachable by SCHEDULING_DRYRUN_FAIL=1")
        return decl

    def _fire(self, decl: ScheduleDeclaration, envelope: dict) -> None:
        pass   # nothing to hand off to; the envelope is already built and returned

    def tick(self, now: str, window_s: int) -> list:
        to = parse_instant(now)
        from datetime import timedelta
        window_to = (to + timedelta(seconds=window_s)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fired = []
        for unit_ref, decl in self._declarations.items():
            oc = self.occurrences(decl.recurrence, decl.starts_at, decl.timezone, now, window_to)
            for instant in oc.occurrences:
                fired.append(self.fire(unit_ref, instant))
        return fired


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunAdapter
