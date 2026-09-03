#!/usr/bin/env python3
"""Live adapter: today's component for durable execution.

Today's component is **Temporal**. PASS.md A6 records it as "Data directory
present; server not listening on `7233`/`8233`. Durable workflow orchestration
and human-in-the-loop signals are designed around it and it is currently down"
(F-a6-02). This adapter's first honest behaviour is therefore to report itself
unavailable: "the orchestrator is down" is a typed failure of one adapter, never
an outage of the capability.

This is the only module besides README's env-var table where a product is named.
Everything above this file speaks step / key / checkpoint / resume point.

Reached only through environment variables (see README):

  WORKFLOW_ADDR        host:port of the frontend, gRPC 7233 or the UI/HTTP 8233
  WORKFLOW_NAMESPACE   namespace the runs live in
  WORKFLOW_TASK_QUEUE  queue the workers poll
  WORKFLOW_API_KEY     credential, when the frontend requires one
  WORKFLOW_TIMEOUT_S   probe and call timeout, default 5

The mapping onto the interface, which adds nothing to it:

  begin_run        start the run under run_key as the workflow id, or describe
                   the existing one; resume_point is the first step its history
                   has no completion for
  checkpoint_step  the step-completion record in that history
  resume_point     read that history and return the first incomplete step
  read_run         terminal state plus the completed step records
  park_gate        a durable timer plus an awaited decision on the run
  record_decision  a decision sent into the run from outside, deduplicated by
                   the gate-scoped key before it is applied

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (BeginRun, Checkpoint, DurableExecutor, GateOutcome,  # noqa: E402
                       GateRecord, Problem, RunState, StepRecord)

SDK_MODULE = "temporalio"          # the SDK for the component named above


def sdk_available() -> bool:
    try:
        return importlib.util.find_spec(SDK_MODULE) is not None
    except (ImportError, ValueError):
        return False


class WorkflowEngineExecutor(DurableExecutor):
    executor_marker = "workflow-engine-frontend/unverified"
    effect_commit_mode = "keyed_effect"      # history lives apart from the effect
    replay_determinism_required = True       # history is replayed onto fresh code
    processes_required_for_progress = 2      # a server, and a registered worker
    resume_derivation = "replay-server-history"

    def __init__(self, out_dir: str | None = None):
        self.addr = os.environ.get("WORKFLOW_ADDR", "")
        self.namespace = os.environ.get("WORKFLOW_NAMESPACE", "default")
        self.task_queue = os.environ.get("WORKFLOW_TASK_QUEUE", "")
        self.timeout = float(os.environ.get("WORKFLOW_TIMEOUT_S", "5"))
        self._client = None

    # -- reachability --------------------------------------------------------
    def _unavailable(self, detail: str) -> Problem:
        return Problem("adapter-unavailable", detail, adapter=self.executor_marker,
                       instance=f"urn:agentic:adapter:live:{self.addr or 'unset'}")

    def probe(self) -> None:
        """A TCP connect to the address the environment names. No path is
        guessed: the ports come from PASS.md A6 and the address from the env."""
        if not self.addr:
            raise self._unavailable("WORKFLOW_ADDR is unset; live mode has no endpoint")
        host, _, port = self.addr.rpartition(":")
        if not host or not port.isdigit():
            raise self._unavailable(f"WORKFLOW_ADDR {self.addr!r} is not host:port")
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
    def begin_run(self, req: BeginRun) -> RunState:
        self._connect()
        raise self._unavailable(
            f"start-or-describe {req.run_key} on namespace {self.namespace}: "
            "the frontend answered but this mapping has never been run from here")

    def checkpoint_step(self, req: Checkpoint) -> StepRecord:
        self._connect()
        raise self._unavailable(f"record completion of step {req.step_id}")

    def resume_point(self, run_key: str) -> RunState:
        self._connect()
        raise self._unavailable(f"read history for {run_key}")

    def read_run(self, run_key: str) -> RunState:
        self._connect()
        raise self._unavailable(f"describe {run_key}")

    def park_gate(self, gate: GateRecord) -> None:
        self._connect()
        raise self._unavailable(f"park gate {gate.gate_id} with deadline {gate.deadline_at}")

    def record_decision(self, outcome: GateOutcome) -> bool:
        self._connect()
        raise self._unavailable(f"send decision {outcome.outcome} to {outcome.gate_id}")

    def mark_terminal(self, run_key: str, outcome: str, problem: dict | None = None) -> None:
        raise self._unavailable(f"close {run_key} as {outcome}")
