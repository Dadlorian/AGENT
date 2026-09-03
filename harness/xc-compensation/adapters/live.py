#!/usr/bin/env python3
"""Live register: today's component for this capability.

There is no component of this platform that records what would undo an effect:
PASS.md names none, the blueprint's state_types row 32 has `home_today: gap`,
and the owner decision recorded against it is that the gap is design work, not a
fact to research (T-t8-01). xc-compensation-implement therefore proposes the
first register on the engine PASS.md B3 names for durable execution - **Temporal**
- which A6 records as "Data directory present; server not listening on
`7233`/`8233`. Durable workflow orchestration and human-in-the-loop signals are
designed around it and it is currently down" (F-a6-02).

So this adapter's first honest behaviour is to report itself unavailable: "the
engine that would hold the register is down" is a typed failure of one adapter,
never an outage of the capability, and never a compensation silently skipped.

This is the only module besides README's env-var table where a product is named.
Everything above this file speaks class / record / declaration head / unwind.

Reached only through environment variables (see README):

  COMPENSATION_ADDR        host:port of the engine frontend, gRPC 7233 or HTTP 8233
  COMPENSATION_NAMESPACE   namespace the runs live in
  COMPENSATION_TASK_QUEUE  queue the workers that hold the declaring code poll
  COMPENSATION_API_KEY     credential, when the frontend requires one
  COMPENSATION_TIMEOUT_S   probe and call timeout, default 5

The mapping onto the interface, which adds nothing to it:

  declare_effect  a journalled entry written before the effect's own activity,
                  carrying the class, the compensating action and the key; the
                  entry's event id is the declaration head
  seal_effect     a second entry carrying the response reference; its event id
                  is the committed head, necessarily later in the same history
  unwind          a reverse walk the engine drives over that history, replayed
                  into the registered worker that declared the steps
  unwind_plan     a read of the same history before the run continues
  records/head    describe the run and read its history; no caller opens the
                  engine's own storage on this host to assemble them

Imports are guarded: the SDK is not installed in this environment, so nothing is
imported at module load and the adapter degrades to a probe that reports
`adapter-unavailable`. Every line below the probe is claimed, not measured: it
has never been run against a listening frontend from here.
"""
from __future__ import annotations

import importlib.util
import os
import socket
import sys
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (CompensationRecord, CompensationRegister, DeclareEffect,  # noqa: E402
                       Problem, UnwindPlan, UnwindReport)

SDK_MODULE = "temporalio"          # the SDK for the component named above


def sdk_available() -> bool:
    try:
        return importlib.util.find_spec(SDK_MODULE) is not None
    except (ImportError, ValueError):
        return False


class EngineRegister(CompensationRegister):
    register_marker = "engine-step-journal/unverified"
    where_the_register_lives = "the step journal of the engine that owns the run's history"
    what_must_be_up_to_unwind = "the engine's frontend, and a worker holding the declaring code"
    what_drives_the_reverse_walk = "the engine replaying its own history into the declaring code"
    unwinds_from_cold_reader = False
    processes_required_for_progress = 2        # a frontend, and a registered worker

    def __init__(self, out_dir: str | None = None):
        self.addr = os.environ.get("COMPENSATION_ADDR", "")
        self.namespace = os.environ.get("COMPENSATION_NAMESPACE", "default")
        self.task_queue = os.environ.get("COMPENSATION_TASK_QUEUE", "")
        self.timeout = float(os.environ.get("COMPENSATION_TIMEOUT_S", "5"))
        self._client = None
        self._handlers: dict[str, Callable[[dict], str]] = {}

    # -- reachability --------------------------------------------------------
    def _unavailable(self, detail: str) -> Problem:
        return Problem("adapter-unavailable", detail, adapter=self.register_marker,
                       instance=f"urn:agentic:adapter:live:{self.addr or 'unset'}")

    def probe(self) -> None:
        """A TCP connect to the address the environment names. No path is
        guessed: the ports come from PASS.md A6 and the address from the env."""
        if not self.addr:
            raise self._unavailable("COMPENSATION_ADDR is unset; live mode has no endpoint")
        host, _, port = self.addr.rpartition(":")
        if not host or not port.isdigit():
            raise self._unavailable(f"COMPENSATION_ADDR {self.addr!r} is not host:port")
        try:
            socket.create_connection((host, int(port)), timeout=self.timeout).close()
        except OSError as exc:
            raise self._unavailable(
                f"nothing listening on {self.addr}: {type(exc).__name__}: {exc}") from exc
        if not sdk_available():
            raise self._unavailable(
                f"{self.addr} answers but the {SDK_MODULE} SDK is not importable here; "
                "the mapping in this module's header is the swap procedure")

    def _connect(self):
        if self._client is None:
            self.probe()
            import importlib
            self._client = importlib.import_module(SDK_MODULE)   # guarded: only after the probe
        return self._client

    # -- the four operations -------------------------------------------------
    def _declare(self, req: DeclareEffect) -> CompensationRecord:
        self._connect()
        raise self._unavailable(
            f"journal the declaration for step {req.step_id} of {req.run_id} on namespace "
            f"{self.namespace}: the frontend answered but this mapping has never been run here")

    def seal_effect(self, record: CompensationRecord, response_ref: str) -> CompensationRecord:
        self._connect()
        raise self._unavailable(f"seal step {record.step_id} against its response")

    def unwind(self, run_id: str, reason: str,
               executor: Callable[[dict], str] | None = None,
               stop_after: int | None = None) -> UnwindReport:
        self._connect()
        raise self._unavailable(f"drive the reverse walk of {run_id} ({reason}) "
                                f"on task queue {self.task_queue or 'unset'}")

    def unwind_plan(self, run_id: str) -> UnwindPlan:
        self._connect()
        raise self._unavailable(f"read the history of {run_id} for an unwind plan")

    def records(self, run_id: str) -> list[CompensationRecord]:
        self._connect()
        raise self._unavailable(f"describe {run_id} and read its compensation records")

    def head(self) -> str:
        self._connect()
        raise self._unavailable("read the current history head")

    def head_ordinal(self, head: str) -> int:
        self._connect()
        raise self._unavailable(f"read the position of {head[:14]}… in the history")


# The one name every adapter module exports: the entry point of this module.
Adapter = EngineRegister
