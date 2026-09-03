#!/usr/bin/env python3
"""Live adapter: today's component for scheduling, engine-owned schedules.

Today's component is **Temporal**, the same one harness/workflow names: PASS.md
A6 records "Data directory present; server not listening on `7233`/`8233`"
(F-a6-02), and cap-scheduling-implement's own recorded row for this adapter is
"Temporal schedules" (E-adapter-temporal-schedules, F-b3-15). This binding's
first honest behaviour is therefore the same as harness/workflow's: report
itself unavailable rather than pretend a server answers.

Two things this file does NOT do, both stated directly in
cap-scheduling-implement's adapters section:

  1. occurrences() and next_after() are NOT recomputed against the engine.
     "Here it maps declare and fire only; occurrences and next_after are
     served by the platform's own evaluator, because the engine offers no
     pure call the vector corpus can drive." They inherit the shared pure
     evaluator from SchedulingAdapter/interface.py unchanged.
  2. declare() does not accept a rule part the engine's calendar spec cannot
     express. "Its calendar-based expression is similar to cron expressions
     (X-cap-scheduling-006), so any rule part outside that expression must be
     refused at declare time" -- BYSETPOS has no cron-family equivalent, so
     it is this binding's own declared_gaps, independent of whether the
     server is reachable at all.

Reached only through environment variables (see README):

  SCHEDULING_ENGINE_ADDR        host:port of the frontend, gRPC 7233
  SCHEDULING_ENGINE_NAMESPACE   namespace the schedules live in
  SCHEDULING_TIMEOUT_S            probe timeout, default 5

Imports are guarded: the SDK is not installed in this environment, so nothing
is imported at module load and the adapter degrades to a probe that reports
adapter-unavailable. Every line past the probe is claimed, not measured: it
has never run against a listening frontend from here.
"""
from __future__ import annotations

import importlib.util
import os
import socket

from interface import Problem, ScheduleDeclaration, SchedulingAdapter, parse_instant

SDK_MODULE = "temporalio"


def sdk_available() -> bool:
    try:
        return importlib.util.find_spec(SDK_MODULE) is not None
    except (ImportError, ValueError):
        return False


class EngineOwnedScheduleAdapter(SchedulingAdapter):
    entity = "engine-owned schedules (Temporal today; PASS.md A6: data directory present, server not listening)"
    adapter_name = "in-engine-schedule"
    declared_gaps = ("BYSETPOS",)   # this binding's own limit; unrelated to reachability

    def __init__(self):
        super().__init__()
        self.addr = os.environ.get("SCHEDULING_ENGINE_ADDR", "")
        self.namespace = os.environ.get("SCHEDULING_ENGINE_NAMESPACE", "default")
        self.timeout = float(os.environ.get("SCHEDULING_TIMEOUT_S", "5"))

    def _unavailable(self, detail: str) -> Problem:
        return Problem("adapter-unavailable", detail, retry_after_s=30,
                       instance=f"urn:agentic:adapter:live:{self.addr or 'unset'}")

    def probe(self) -> None:
        """A TCP connect to the address the environment names. No path is
        guessed: the port comes from PASS.md A6 and the address from the env."""
        if not self.addr:
            raise self._unavailable("SCHEDULING_ENGINE_ADDR is unset; live mode has no endpoint")
        host, _, port = self.addr.rpartition(":")
        if not host or not port.isdigit():
            raise self._unavailable(f"SCHEDULING_ENGINE_ADDR {self.addr!r} is not host:port")
        try:
            socket.create_connection((host, int(port)), timeout=self.timeout).close()
        except OSError as exc:
            raise self._unavailable(
                f"nothing listening on {self.addr}: {type(exc).__name__}: {exc}") from exc
        if not sdk_available():
            raise self._unavailable(
                f"{self.addr} answers but the {SDK_MODULE} SDK is not importable here; "
                "the mapping in this module's header is the swap procedure")

    def _declare(self, decl: ScheduleDeclaration) -> ScheduleDeclaration:
        self.probe()
        raise self._unavailable(
            f"create-or-update schedule {decl.unit_ref} on namespace {self.namespace}: "
            "the frontend answered but this mapping has never been run from here")

    def _fire(self, decl: ScheduleDeclaration, envelope: dict) -> None:
        self.probe()
        raise self._unavailable(f"trigger {decl.unit_ref} at {envelope['occurred_at']}")

    def tick(self, now: str, window_s: int) -> list:
        # The engine owns its own timer once a schedule is registered with it;
        # this platform never polls it (step 1's "tick" belongs to the
        # standalone adapter only). Reads still work with no server at all.
        raise self._unavailable("the engine owns its own firing timer; there is no tick to drive here")


# The one name every adapter module exports: the entry point of this module.
Adapter = EngineOwnedScheduleAdapter
