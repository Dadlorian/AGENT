#!/usr/bin/env python3
"""The Dispatch seam: the capability interface, and nothing else.

One unit of agent work executes under a declared ceiling and returns one typed
result whose partial progress is already durable (F-b5-02, F-b5-03). The whole
vocabulary is a request, a result, a step record and a typed problem. Sessions,
sockets, queues, service units, hardware virtualisation and endpoints are absent on
purpose: a dispatcher that is one request-response into someone else's sandbox
could never implement them, so a contract that names them is a contract shaped
around whichever executor runs today.

No product name appears in this file. They appear in adapters/live.py and in the
env-var table of README.md, and nowhere else.

Read it in this order: DispatchRequest and DispatchResult are the two shapes the
seam exists to fix; STOP_REASONS is what a caller may branch on; Dispatcher is
the five operations and the four declared attributes every shim answers with.

Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
_errors_path = _errors_os.path.join(
    _errors_os.path.dirname(_errors_os.path.abspath(__file__)), "..", "errors")
if _errors_path not in _errors_sys.path:
    _errors_sys.path.append(_errors_path)  # appended, never inserted at 0: this
    # harness's own adapters/ package must resolve before errors/adapters/ does
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

INTERFACE_VERSION = "urn:agentic:seam:dispatch:0.1"


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


# --------------------------------------------------------------------------
# Typed failures (cap-errors / RFC 9457). One closed registry; a failure whose
# type is not a row here is an untyped failure and the conformance run counts it.
# --------------------------------------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":       (422, "The dispatch request fails validation", False),
    "criterion-unresolvable": (422, "criterion_ref does not resolve", False),
    "budget-exhausted":       (402, "A step would cross the budget ceiling", False),
    "deadline-exceeded":      (504, "A declared ceiling was reached", True),
    "policy-denied":          (403, "A policy decision refused this dispatch", False),
    "adapter-unavailable":    (503, "A capability adapter is unreachable", True),
    "idempotency-conflict":   (409, "Same key, different request body", False),
}


class Problem(Exception):
    """A failure a caller branches on without parsing prose (F-b4-07).

    `proposed_type` records a type this platform would register but has not, so
    a substitution is visible in the body rather than invented in the registry.
    """

    def __init__(self, suffix: str, detail: str, **ext: Any):
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


def is_typed(body: dict | None) -> bool:
    """A failure body is typed when its type is a row in the closed registry."""
    if not body:
        return False
    t = str(body.get("type", ""))
    return t.startswith(PROBLEM_BASE) and t[len(PROBLEM_BASE):] in REGISTRY


# --------------------------------------------------------------------------
# The entry envelope (cap-consumption). One shape for all four entries of
# TARGET T6.2; kind says which door produced it and nothing below branches on it.
# The fixture envelopes under examples/end-to-end/entries/ are this shape.
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
# The request and the result
# --------------------------------------------------------------------------
STATES = ("submitted", "working", "input-required", "auth-required",
          "completed", "canceled", "rejected", "failed")

# The first five are adopted from the agent control protocol; the last five are
# the endings the platform itself can cause.
STOP_REASONS = ("end_turn", "max_tokens", "max_turn_requests", "refusal",
                "cancelled", "budget_exhausted", "deadline_exceeded",
                "policy_denied", "cancel_timeout", "adapter_unavailable")


@dataclass
class DispatchRequest:
    """What to do is in the document; how it will be judged is not here at all.

    `criterion_ref` is an opaque handle. The criterion body must never appear in
    this object, in a step payload, or in anything the graded unit can read
    (F-b1-07); the conformance run scans recorded requests and counts.
    """
    dispatch_id: str
    idempotency_key: str
    document: dict                 # {document_id, workflow_ref, payload, definition_of_done}
    criterion_ref: str
    actor: dict                    # {subject, delegation_chain}
    budget: dict                   # {ceiling_micros, currency, on_exceed}
    deadline: dict                 # {not_after, max_duration_s, cancel_grace_s}
    isolation: dict                # {profile, egress}
    correlation: dict              # {run_id, root_dispatch_id, correlation_id}
    context: dict = field(default_factory=dict)   # what this unit receives
    previous_dispatch_id: str | None = None
    request_version: str = INTERFACE_VERSION

    def dict(self) -> dict:
        # An absent optional member is absent, not null: the published schema
        # types `previous_dispatch_id` and a null would be a shape violation.
        return {k: v for k, v in asdict(self).items()
                if not (k == "previous_dispatch_id" and v is None)}


@dataclass
class Output:
    """An output a later reader can find: a digest and the head it became
    durable at. A result naming an output with no head is the seam's central
    promise breaking, which is what the deliberate breakage does."""
    name: str
    digest: str
    media_type: str
    recorded_at_head: str | None


@dataclass
class Usage:
    spend_micros: int = 0
    steps_executed: int = 0
    steps_replayed: int = 0
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass
class DispatchResult:
    dispatch_id: str
    state: str                     # one of STATES
    stop_reason: str               # one of STOP_REASONS
    started_at: str
    ended_at: str
    partial: bool
    outputs: list[Output]
    usage: Usage
    correlation: dict
    summary: str = ""              # the folded summary handed back to the parent
    problem: dict | None = None
    dispatcher_marker: str = ""    # read back from the dispatcher that answered

    def dict(self) -> dict:
        d = asdict(self)
        d["usage"] = asdict(self.usage)
        d["outputs"] = [asdict(o) for o in self.outputs]
        return d


@dataclass
class StepRecord:
    """Allocated by the dispatcher before execution, written through the state
    seam at the first durable output, and read by resume to find the first step
    whose checkpoint reference is null. Executors keep no journal of their own."""
    dispatch_id: str
    step_id: str
    step_idempotency_key: str
    state: Literal["pending", "complete", "failed"]
    checkpoint_ref: str | None = None
    cost_micros: int = 0
    output_digest: str = ""
    correlation_id: str = ""
    actor: str = ""
    stop_reason: str = ""


# --------------------------------------------------------------------------
# The adapter
# --------------------------------------------------------------------------
class Dispatcher(ABC):
    """Five operations, and four attributes each shim declares about itself.

    The pair differs in execution model, not in brand: one holds a session open
    for the life of the unit and can be stopped mid-call; the other is one
    request-response into an executor that cannot be stopped once started. The
    conformance run asserts each behaved as it declared, rather than widening
    the contract until both members satisfy it.
    """

    dispatcher_marker: str = "unset"
    unit_lifetime: Literal["session_held", "request_response"] = "session_held"
    cancellation_reach: Literal["mid_call", "none"] = "mid_call"
    keeps_own_journal: bool = False
    executor_reached_over: str = "in-process"

    def binding(self) -> dict:
        return {"adapter": type(self).__name__,
                "dispatcher_marker": self.dispatcher_marker,
                "unit_lifetime": self.unit_lifetime,
                "cancellation_reach": self.cancellation_reach,
                "keeps_own_journal": self.keeps_own_journal,
                "interface_version": INTERFACE_VERSION}

    @abstractmethod
    def dispatch(self, req: DispatchRequest) -> DispatchResult:
        """One unit executes and returns one result (F-b5-02)."""

    @abstractmethod
    def cancel(self, dispatch_id: str, grace_s: int) -> dict:
        """Acceptance, not a stop. The caller keeps reading until the terminal
        result, whose stop reason is `cancelled` inside the window and
        `cancel_timeout` outside it. Cancelling a terminal dispatch returns the
        current result and is not an error."""

    @abstractmethod
    def resume(self, req: DispatchRequest) -> DispatchResult:
        """Continue from the first step whose checkpoint reference is null,
        under whatever ceiling remained. The prior result is never mutated."""

    @abstractmethod
    def replay(self, req: DispatchRequest) -> DispatchResult:
        """The recorded result of the first execution, byte for byte, with no
        side effect re-executed. A different body under the same key is refused
        as idempotency-conflict."""

    @abstractmethod
    def read_step(self, dispatch_id: str, step_id: str | None = None) -> list[StepRecord]:
        """The recorded steps: state, checkpoint reference, usage and stop
        reason, so a reader can tell what a restart will and will not re-do."""


ADAPTERS = ("dryrun", "second", "live")


def load_dispatcher(name: str, out_dir: str) -> Dispatcher:
    """Binding is configuration: one name from the environment, one import, one
    class. Every adapter module exports its entry point as `Adapter`, so there
    is no per-adapter class-name table here or anywhere else."""
    import importlib
    if name not in ADAPTERS:
        raise Problem("document-invalid",
                      f"unknown adapter {name!r}: choose {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter(out_dir)
