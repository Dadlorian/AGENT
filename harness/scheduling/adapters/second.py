#!/usr/bin/env python3
"""Second adapter: the standalone evaluator behind a ticker and a queue.

Where the dry-run adapter fires synchronously -- one call, occurrences
computed and every envelope built before it returns -- this one splits that
into two steps cap-scheduling-implement names directly (step 2): "a library
call... plus a ticker that asks it for a short forward window and enqueues
one message per occurrence", then a separate consumer that "builds the
envelope". `enqueue()` is the ticker: it reads the pure evaluator and writes
one message per occurrence to a durable queue, nothing more. `drain()` is the
consumer: it reads the queue and fires each message through the one shared
envelope builder every adapter uses. tick() runs both for a caller that wants
one call, but a caller may also run them apart -- crash between them, and the
queue still holds what was not yet drained, which a synchronous call can
never demonstrate.

Because occurrences() is a pure function of its four inputs, re-asking for an
overlapping window costs nothing and the derived idempotency key collapses
any duplicate a second enqueue would produce (cap-scheduling-implement's own
best practice); this adapter is what makes that claim checkable.

Reachability: with SCHEDULING_QUEUE_PATH set (see README), the queue is a
JSONL file on disk -- a real, inspectable artifact, not a Python list -- so a
drain in a second process can pick up what a first process enqueued and
crashed before draining. Unset, the queue lives in memory for the duration
of one process, which is what a dry run exercises. Both are the same
adapter; only where the queue's bytes live differs.
"""
from __future__ import annotations

import json
import os

from interface import Problem, ScheduleDeclaration, SchedulingAdapter, parse_instant


class TickerQueueAdapter(SchedulingAdapter):
    entity = "standalone evaluator behind a ticker and a queue (enqueue-then-drain)"
    adapter_name = "standalone-evaluator"

    def __init__(self):
        super().__init__()
        self.enqueued = 0
        self.drained = 0
        self._queue_path = os.environ.get("SCHEDULING_QUEUE_PATH")
        self._mem_queue: list[dict] = []
        if self._queue_path and os.path.exists(self._queue_path):
            os.remove(self._queue_path)      # a fresh queue per process, like the other harnesses' journals

    def _declare(self, decl: ScheduleDeclaration) -> ScheduleDeclaration:
        if os.environ.get("SCHEDULING_SECOND_FAIL") == "1":
            self.refused += 1
            raise Problem("adapter-unavailable",
                          "the ticker-queue evaluator was made unreachable by SCHEDULING_SECOND_FAIL=1")
        return decl

    def _fire(self, decl: ScheduleDeclaration, envelope: dict) -> None:
        pass   # the envelope is already built by the shared builder; nothing more to hand off

    # -- the two steps a synchronous adapter cannot show separately ----------
    def _write_queue(self, message: dict) -> None:
        if self._queue_path:
            os.makedirs(os.path.dirname(os.path.abspath(self._queue_path)) or ".", exist_ok=True)
            with open(self._queue_path, "a") as fh:
                fh.write(json.dumps(message) + "\n")
        else:
            self._mem_queue.append(message)

    def _read_queue(self) -> list[dict]:
        if self._queue_path:
            if not os.path.exists(self._queue_path):
                return []
            with open(self._queue_path) as fh:
                return [json.loads(line) for line in fh if line.strip()]
        return list(self._mem_queue)

    def _clear_queue(self) -> None:
        if self._queue_path:
            if os.path.exists(self._queue_path):
                os.remove(self._queue_path)
        else:
            self._mem_queue.clear()

    def enqueue(self, now: str, window_s: int) -> int:
        """The ticker: one message per occurrence, nothing fired yet."""
        from datetime import timedelta
        to = (parse_instant(now) + timedelta(seconds=window_s)).strftime("%Y-%m-%dT%H:%M:%SZ")
        added = 0
        for unit_ref, decl in self._declarations.items():
            oc = self.occurrences(decl.recurrence, decl.starts_at, decl.timezone, now, to)
            for instant in oc.occurrences:
                self._write_queue({"unit_ref": unit_ref, "occurrence": instant})
                self.enqueued += 1
                added += 1
        return added

    def drain(self) -> list:
        """The consumer: read the queue, fire each message, clear the queue."""
        messages = self._read_queue()
        fired = []
        for message in messages:
            fired.append(self.fire(message["unit_ref"], message["occurrence"]))
            self.drained += 1
        self._clear_queue()
        return fired

    def tick(self, now: str, window_s: int) -> list:
        self.enqueue(now, window_s)
        return self.drain()


# The one name every adapter module exports: the entry point of this module.
Adapter = TickerQueueAdapter
