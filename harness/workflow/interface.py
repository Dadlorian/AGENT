#!/usr/bin/env python3
"""Durable execution: the capability interface, and nothing else.

The whole vocabulary is four words - a step, an idempotency key, a checkpoint,
a resume point (cap-durable-execution, F-b3-04). Worker registration, task
queues, event-history formats, replay determinism and any server address are
absent on purpose: an executor that keeps its state in a row beside the effect
could never implement them, so a contract that names them is a contract shaped
around one engine (F-a6-02).

No product name appears in this file. They appear in adapters/live.py and in the
env-var table of README.md, and nowhere else.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

INTERFACE_VERSION = "urn:agentic:cap:durable-execution:0.1"

# --------------------------------------------------------------------------
# The entry envelope (cap-consumption). One shape for all four entries of
# TARGET T6.2; kind says which door produced it and nothing below branches on it.
# --------------------------------------------------------------------------
@dataclass
class Envelope:
    kind: Literal["human", "event", "schedule", "external"]
    entry_id: str
    occurred_at: str
    actor: dict                 # {subject, delegation_chain}
    intent: dict                # {workflow_ref, summary} - never the criterion
    correlation: dict           # {run_id, correlation_id, depth}
    budget: dict                # {ceiling_micros, currency, on_exceed}
    idempotency_key: str
    payload: dict
    envelope_version: str = "0.1"

    def dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Typed failures (cap-errors / RFC 9457). The registry is the closed set in
# docs/decomposition.md 2.1.6; an unregistered type is a conformance failure.
# --------------------------------------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":      (422, "The document fails validation", False),
    "criterion-unresolvable": (422, "criterion_ref does not resolve", False),
    "budget-exhausted":      (402, "A step would cross the budget ceiling", False),
    "deadline-exceeded":     (504, "A declared ceiling was reached", True),
    "adapter-unavailable":   (503, "A capability adapter is down", True),
    "idempotency-conflict":  (409, "Same key, different request body", False),
}


class Problem(Exception):
    """A failure a caller branches on without parsing prose (F-b4-07)."""

    def __init__(self, suffix: str, detail: str, **ext: Any):
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail, "retryable": retryable, **ext}
        super().__init__(detail)


# --------------------------------------------------------------------------
# Request, result and record shapes
# --------------------------------------------------------------------------
def step_idempotency_key(run_key: str, step_id: str) -> str:
    """Per step, not per run, and derived so it is identical on every restart."""
    return "sha256:" + hashlib.sha256(f"{run_key}|{step_id}".encode()).hexdigest()[:32]


@dataclass
class BeginRun:
    run_key: str                # the caller's key: same key, same run
    sequence_id: str            # which step sequence to execute
    input_digest: str           # digest of its input
    correlation_id: str
    actor: str
    ceiling_micros: int


@dataclass
class Checkpoint:
    run_key: str
    step_id: str
    step_idempotency_key: str | None   # None only in the deliberate breakage
    output_digest: str
    cost_micros: int
    correlation_id: str
    actor: str
    state: Literal["complete", "failed"] = "complete"
    effect: dict | None = None  # present only when the executor commits the
                                # effect in the same transaction as the checkpoint
    output: dict = field(default_factory=dict)


@dataclass
class StepRecord:
    run_key: str
    step_id: str
    step_idempotency_key: str | None
    state: Literal["pending", "complete", "failed"]
    committed_with_effect: bool
    output_digest: str = ""
    cost_micros: int = 0
    correlation_id: str = ""
    actor: str = ""
    output: dict = field(default_factory=dict)
    problem: dict | None = None


@dataclass
class RunState:
    """What a restart reads: where to continue, and what it already spent."""
    run_key: str
    resume_point: int                 # index of the first incomplete step
    steps_committed: int
    steps_replayed: int               # committed steps skipped rather than re-executed
    terminal: bool
    completed: list[StepRecord] = field(default_factory=list)
    spent_micros: int = 0
    executor_marker: str = ""         # emitted by the running executor, not the binding
    correlation_id: str | None = None
    pending_recovered: int = 0        # commits found half-applied and finished on start
    problem: dict | None = None


# --------------------------------------------------------------------------
# The parked gate: the resume seam a decision arrives on (compose-approval).
# It is expressed in this interface because a gate that is not durable is a gate
# that a crash loses; it is not expressed in any engine's signal vocabulary.
# --------------------------------------------------------------------------
OUTCOMES = ("approve", "edit", "reject", "return_with_notes")


def gate_id_for(run_key: str, gate_step_id: str) -> str:
    """A gate is identified by the run it belongs to and the step that parks it,
    so a restart in another process can find it without an engine handle."""
    return f"{run_key}::{gate_step_id}"


def gate_parts(gate_id: str) -> tuple[str, str]:
    run_key, gate_step_id = gate_id.split("::", 1)
    return run_key, gate_step_id


@dataclass
class GateRecord:
    gate_id: str
    correlation_id: str
    step_id: str                  # the step that would have done the irreversible thing
    view: str                     # required: what the decider is shown
    decider: str                  # user: / agent: / service: / schedule:
    wires: list[str]
    deadline_at: str
    outcomes: tuple[str, ...] = OUTCOMES
    return_to_step_id: str | None = None   # required when return_with_notes is offered


@dataclass
class GateOutcome:
    gate_id: str
    correlation_id: str
    outcome: Literal["approve", "edit", "reject", "return_with_notes"]
    actor: str
    idempotency_key: str          # scoped to gate_id: N deliveries resume the run once
    body: dict = field(default_factory=dict)
    delivered_over: str = ""      # audit only; nothing branches on it


# --------------------------------------------------------------------------
# The bounded loop's outcome (compose-loop). Three termination reasons and no
# fourth: a defect has nowhere to be written, so it shows up instead of passing.
# --------------------------------------------------------------------------
@dataclass
class LoopOutcome:
    loop_id: str
    terminated_by: Literal["verdict_pass", "iteration_ceiling", "budget_ceiling"]
    termination_class: Literal["stop", "cap"]
    iterations_run: int
    cost_micros: int
    last_verdict: dict | None = None
    escalation: dict | None = None   # present when termination_class is cap


# --------------------------------------------------------------------------
# The adapter
# --------------------------------------------------------------------------
class DurableExecutor(ABC):
    """Four operations, plus the two the parked gate rides on.

    Every implementation declares how it behaves rather than being asked to
    behave alike: the four class attributes below are its declared gaps, and the
    conformance run asserts the executor behaved as declared instead of widening
    the contract until both members satisfy it.
    """

    executor_marker: str = "unset"                # read back from the running executor
    effect_commit_mode: Literal["keyed_effect", "same_transaction"] = "keyed_effect"
    replay_determinism_required: bool = True
    processes_required_for_progress: int = 1
    resume_derivation: str = "unset"

    def binding(self) -> dict:
        return {"adapter": type(self).__name__,
                "executor_marker": self.executor_marker,
                "effect_commit_mode": self.effect_commit_mode,
                "replay_determinism_required": self.replay_determinism_required,
                "processes_required_for_progress": self.processes_required_for_progress,
                "resume_derivation": self.resume_derivation,
                "interface_version": INTERFACE_VERSION}

    @abstractmethod
    def begin_run(self, req: BeginRun) -> RunState:
        """Start or resume: the same call. A new key resumes at 0; a key that has
        run before resumes at its first incomplete step."""

    @abstractmethod
    def checkpoint_step(self, req: Checkpoint) -> StepRecord:
        """The checkpoint and the step's effect become durable together, or the
        step is not complete."""

    @abstractmethod
    def resume_point(self, run_key: str) -> RunState:
        """The first incomplete step and how many are already committed."""

    @abstractmethod
    def read_run(self, run_key: str) -> RunState:
        """Terminal state plus the committed step records."""

    @abstractmethod
    def park_gate(self, gate: GateRecord) -> None:
        """Park a step that cannot proceed until a decision arrives."""

    @abstractmethod
    def record_decision(self, outcome: GateOutcome) -> bool:
        """True when this delivery is the one that resumes the run; False when it
        is a redelivery of a decision already applied, or the gate is closed."""


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
