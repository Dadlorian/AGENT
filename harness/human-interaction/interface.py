#!/usr/bin/env python3
"""Human interaction: the capability interface, and nothing else.

The whole vocabulary is four operations and three records: a run *asks*, a person
*watches*, a person *decides*, and an unanswered ask *expires*; the records are
the ask, the decision, and the parked row the platform stores between them
(cap-human-interaction contract.operations).

What is deliberately absent. No session token, no chat thread id, no stream
cursor, no push receipt and no screen: a surface handle on the ask or the
decision would mean the run can only be resumed by whoever holds one particular
screen (cap-human-interaction not_exposed, F-part-c-09). There is also no
force-continue, no skip and no admin override: every one of those is an unlogged
approval by another name, and the parked row is the only place a deciding actor
is recorded.

Two things are concrete here rather than left to an adapter. `ask()` refuses a
malformed ask and stores it before any surface sees it, and `decide()` takes the
lease and the state transition in one write in the store - so a surface cannot
decline the deadline, the response schema, the actor or the replay rule. A
surface is a caller, and a caller cannot decline the platform's guarantees
(F-b1-08, F-b4-01).

No product name and no host name appears in this file. They appear in
adapters/live.py and in the env-var table of README.md, and nowhere else.

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

INTERFACE_VERSION = "urn:agentic:cap:human-interaction:0.1"

DECISIONS = ("approve", "edit", "reject", "respond")
"""The one enumeration of decisions (cap-human-interaction invariants: four
decisions, not two). An approve/reject pair has nowhere to put an edit."""


# --------------------------------------------------------------------------
# The entry envelope (cap-consumption). One shape for all four entries of
# TARGET T6.2; `kind` says which door produced it and nothing below branches on
# it. A parked ask is answered by a human, but the run behind it may have come
# in through any door.
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


def stamps_from(envelope: dict) -> dict:
    """What the platform stamps on the pause and again on the resume.

    Identity, correlation, budget and replay are applied by the platform at both
    ends of the human boundary, not by whichever surface is in front of the
    person (cap-human-interaction-implement invariants; F-b4-01). Correlation
    rides on an explicit attribute, never on trace parentage - a human boundary
    is the longest gap in any run, so there is no live trace left to be a parent
    by the time someone decides (F-b4-06).
    """
    return {"correlation_id": envelope["correlation"]["correlation_id"],
            "run_id": envelope["correlation"]["run_id"],
            "actor": envelope["actor"]["subject"],
            "delegation_chain": envelope["actor"]["delegation_chain"],
            "ceiling_micros": envelope["budget"]["ceiling_micros"],
            "entry_kind": envelope["kind"],
            "idempotency_key": envelope["idempotency_key"]}


# --------------------------------------------------------------------------
# Typed failures (cap-errors / RFC 9457). The registry is the closed set in
# docs/decomposition.md 2.1.6; an unregistered type is a conformance failure.
#
# `urn:agentic:problem:human-ask-expired` is proposed and not yet a row there,
# so an ask closed by its deadline returns the registered `deadline-exceeded`
# with the ask id in `detail` and `ask_state` as a declared extension member -
# exactly what cap-human-interaction says to do until that row lands.
# --------------------------------------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":      (422, "The document fails validation", False),
    "deadline-exceeded":     (504, "A declared ceiling was reached", True),
    "idempotency-conflict":  (409, "Same key, different request body", False),
    "adapter-unavailable":   (503, "A capability adapter is down", True),
}


class Problem(Exception):
    """A failure a caller branches on by type, never by reading prose (F-b4-07)."""

    def __init__(self, suffix: str, detail: str, **ext: Any):
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --------------------------------------------------------------------------
# The three records
# --------------------------------------------------------------------------
SURFACE_HANDLE_FIELDS = ("session", "session_id", "thread", "thread_id", "cursor",
                         "stream_position", "push_receipt", "socket", "screen",
                         "connection_id", "device_token")
"""Fields that name a screen. None may appear on an ask or on a decision."""


@dataclass
class HumanAsk:
    """What the pause emits (cap-human-interaction shapes: HumanAsk).

    `deadline_at` is required: an ask with no deadline is a run that waits
    forever. `response_schema` is required: the ask is typed, not prose, which is
    what makes a decision machine-checkable before the run continues.
    """
    ask_id: str
    correlation_id: str
    prompt: str                 # written for a person; never carries the criterion
    response_schema: dict       # JSON Schema; the decision body is checked against it
    proposed: dict              # {action, diff, irreversibility}
    deadline_at: str
    allowed_decisions: tuple[str, ...] = DECISIONS

    def dict(self) -> dict:
        d = asdict(self)
        d["allowed_decisions"] = list(self.allowed_decisions)
        return d


@dataclass
class HumanDecision:
    """What comes back (cap-human-interaction shapes: HumanDecision).

    It arrives on the run's own `correlation_id`, not on a handle a surface
    minted, and it names the actor who decided: a decision is an action and names
    an actor like any other (F-b4-03).
    """
    ask_id: str
    correlation_id: str
    decision: Literal["approve", "edit", "reject", "respond"]
    actor: str                  # user: / agent: / service: / schedule:
    idempotency_key: str        # the same decision delivered ten times resumes once
    body: dict = field(default_factory=dict)

    def dict(self) -> dict:
        return asdict(self)


@dataclass
class ParkedAsk:
    """The stored row both surfaces render and the run resumes from
    (cap-human-interaction-implement shapes: ParkedAsk).

    It is written before either surface exists. `resume_token` is derived from
    the ask id and the correlation id, never minted per surface, so two surfaces
    showing one ask derive the same token.
    """
    ask: dict
    state: Literal["open", "decided", "expired"]
    stored_at: str
    resume_token: str
    attempts: list[dict] = field(default_factory=list)
    decision: dict | None = None
    stamps: dict = field(default_factory=dict)     # the pause stamp
    deliveries: list[dict] = field(default_factory=list)

    def dict(self) -> dict:
        return asdict(self)


@dataclass
class ResumeAck:
    """What a decision returns, and what the run continues with.

    `artifact` is the artifact the run continues with: on edit it is the
    reviewer's body and not the one that was proposed, because the agent proposes
    and the human publishes. A resume that records an edit and then continues
    with the proposed artifact has recorded a preference, not applied a decision.
    """
    ask_id: str
    correlation_id: str
    outcome: Literal["applied", "duplicate", "refused"]
    applied: bool
    decision: str
    artifact: dict
    stamps: dict                  # the resume stamp: same shape as the pause stamp
    surface: str                  # audit only; nothing in the run branches on it
    decided_by: str = ""
    resumed_at: str = ""

    def dict(self) -> dict:
        return asdict(self)


@dataclass
class StreamEvent:
    """One typed event on the run's stream. Each event carries a `type` field
    that identifies the action taking place (X-entry-composition-021); the type
    names below are this repository's, because no event-type name is on file for
    the standard - only that the events are typed."""
    type: str
    correlation_id: str
    seq: int
    at: str
    data: dict = field(default_factory=dict)

    def dict(self) -> dict:
        return asdict(self)


EVENT_TYPES = ("run.started", "step.progress", "tool.proposed", "human.ask",
               "human.decided", "human.refused", "ask.expired", "run.finished")


# --------------------------------------------------------------------------
# A JSON Schema subset, enough to check a decision body against the ask's
# response schema in this harness. The real checker is the document-validation
# capability; this is a deliberate subset and is declared as one, not a second
# validator anyone should import.
# --------------------------------------------------------------------------
_TYPES = {"object": dict, "string": str, "integer": int, "number": (int, float),
          "boolean": bool, "array": list}


def validate_subset(schema: dict, body: Any, path: str = "body") -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected and not isinstance(body, _TYPES.get(expected, object)):
        return [f"{path}: expected {expected}"]
    if expected == "object":
        for name in schema.get("required", []):
            if name not in body:
                errors.append(f"{path}.{name}: required")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for name in body:
                if name not in props:
                    errors.append(f"{path}.{name}: not permitted")
        for name, sub in props.items():
            if name in body:
                errors += validate_subset(sub, body[name], f"{path}.{name}")
    if "enum" in schema and body not in schema["enum"]:
        errors.append(f"{path}: not one of {schema['enum']}")
    if "minLength" in schema and isinstance(body, str) and len(body) < schema["minLength"]:
        errors.append(f"{path}: shorter than {schema['minLength']}")
    return errors


# --------------------------------------------------------------------------
# Derived identifiers
# --------------------------------------------------------------------------
def resume_token_for(ask_id: str, correlation_id: str) -> str:
    """Derived, never minted per surface: two surfaces showing one ask derive the
    same token, so a decision from either resumes the same run."""
    return "rt-" + hashlib.sha256(f"{ask_id}|{correlation_id}".encode()).hexdigest()[:32]


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --------------------------------------------------------------------------
# The adapter: a surface. It renders asks and carries decisions; it never owns
# the parked state.
# --------------------------------------------------------------------------
class HumanSurface(ABC):
    """Four operations. Two of them are concrete on purpose.

    Every implementation declares how it behaves rather than being asked to
    behave alike: the class attributes below are its declared gaps, and the
    conformance run asserts the surface behaved as declared instead of widening
    the contract until both members satisfy it.
    """

    surface_marker: str = "unset"
    delivery_model: Literal["request_response", "stream"] = "request_response"
    renders_run_in_flight: bool = False
    replayable_from_position: bool = False
    requires_open_session: bool = False
    max_edit_bytes: int = 256          # a form field, unless the surface says otherwise
    selected_by: str = "configuration"

    def __init__(self, store):
        self.store = store

    def binding(self) -> dict:
        return {"adapter": type(self).__name__,
                "surface_marker": self.surface_marker,
                "delivery_model": self.delivery_model,
                "renders_run_in_flight": self.renders_run_in_flight,
                "replayable_from_position": self.replayable_from_position,
                "requires_open_session": self.requires_open_session,
                "max_edit_bytes": self.max_edit_bytes,
                "selected_by": self.selected_by,
                "interface_version": INTERFACE_VERSION}

    # -- concrete: the platform's work, identical on every surface -----------
    def ask(self, ask: HumanAsk, envelope: dict, now: str) -> ParkedAsk:
        """Park the run on an ask. The row is stored before the surface is told,
        so an ask that a surface never delivered is still an ask the platform
        holds (F-b3-17: the parked state belongs to the platform)."""
        check_ask(ask)
        parked = self.store.park(ask, stamps_from(envelope), now)
        try:
            attempt = self.deliver(parked)
        except Problem as problem:                 # a surface that cannot deliver
            self.store.record_delivery(ask.ask_id, {"surface": self.surface_marker,
                                                    "delivered": False,
                                                    "problem": problem.body["type"]})
            raise
        self.store.record_delivery(ask.ask_id, attempt)
        return self.store.read(ask.ask_id)

    def watch(self, correlation_id: str, since: int = 0) -> list[StreamEvent]:
        """What a person sees. A surface that cannot answer from a position says
        so by declaration and refuses with a type, rather than silently returning
        the whole stream (F-b4-07)."""
        if since and not self.replayable_from_position:
            raise Problem("document-invalid",
                          f"{self.surface_marker} cannot answer from a position: it is "
                          f"request/response over one parked item, not a replayable stream",
                          surface=self.surface_marker, correlation_id=correlation_id)
        return self.project(self.store.events(correlation_id, since))

    def decide(self, decision: HumanDecision, now: str) -> ResumeAck:
        """One decision, delivered through this surface. The lease and the state
        transition are one write in the store; the surface authenticates the
        person and puts that subject on the decision, and the store never trusts
        a surface about who decided (F-b4-03, F-b4-08)."""
        body_bytes = len(json.dumps(decision.body, separators=(",", ":")))
        if body_bytes > self.max_edit_bytes:
            raise Problem("document-invalid",
                          f"{self.surface_marker} declares max_edit_bytes={self.max_edit_bytes}; "
                          f"this decision body is {body_bytes} bytes and was refused rather "
                          f"than truncated",
                          surface=self.surface_marker, ask_id=decision.ask_id)
        decision.actor = self.authenticate(decision)
        return self.store.apply(decision, self.surface_marker, now)

    def expire(self, ask_id: str, now: str) -> ParkedAsk:
        """Close an ask whose deadline has passed. Terminal: nothing resumes on
        that ask afterwards, and a decision arriving late is refused rather than
        applied."""
        return self.store.expire(ask_id, now)

    # -- surface-specific ----------------------------------------------------
    @abstractmethod
    def deliver(self, parked: ParkedAsk) -> dict:
        """Put the ask in front of a person. Returns one delivery attempt record."""

    @abstractmethod
    def project(self, events: list[StreamEvent]) -> list[StreamEvent]:
        """What this surface shows of the run's stream."""

    @abstractmethod
    def authenticate(self, decision: HumanDecision) -> str:
        """The subject this surface authenticated, put on the decision."""


def check_ask(ask: HumanAsk) -> None:
    """Everything an ask must be before it is stored.

    The criterion check is the one that is easy to lose: everything in an ask is
    visible to the graded unit that will read the decision back, so an agent sees
    its outcome, never the criterion it is judged against (F-b1-07).
    """
    if not ask.deadline_at:
        raise Problem("document-invalid", "an ask with no deadline is a run that waits forever",
                      ask_id=ask.ask_id)
    if not ask.prompt or not ask.correlation_id:
        raise Problem("document-invalid", "an ask needs a prompt and the run's correlation id",
                      ask_id=ask.ask_id)
    if not isinstance(ask.response_schema, dict) or not ask.response_schema:
        raise Problem("document-invalid", "the ask is typed, not prose: a response schema is required",
                      ask_id=ask.ask_id)
    for name in ("action", "diff", "irreversibility"):
        if name not in ask.proposed:
            raise Problem("document-invalid", f"proposed.{name} is required: a gate with no view "
                                              f"is undecidable", ask_id=ask.ask_id)
    if ask.proposed["irreversibility"] not in ("reversible", "compensatable", "irreversible"):
        raise Problem("document-invalid", "irreversibility is one of reversible, compensatable, "
                                          "irreversible", ask_id=ask.ask_id)
    blob = json.dumps(ask.dict()).lower()
    if "criterion" in blob or "rubric" in blob:
        raise Problem("document-invalid",
                      "the criterion never travels in an ask: the graded unit reads the decision back",
                      ask_id=ask.ask_id)
    handles = [f for f in SURFACE_HANDLE_FIELDS if f'"{f}"' in blob]
    if handles:
        raise Problem("document-invalid",
                      f"an ask may not carry a surface handle: {handles}", ask_id=ask.ask_id)


ADAPTERS = ("dryrun", "second", "live")


def load_surface(name: str, store) -> HumanSurface:
    """Binding is configuration: one name from the environment, one import, one
    class. Every adapter module in this harness exports its entry point as
    `Adapter`, so there is no per-adapter class-name table here or anywhere
    else. `binding()` still reports the class that answered, so a report says
    which surface served without a caller naming it."""
    import importlib
    if name not in ADAPTERS:
        raise Problem("document-invalid",
                      f"unknown adapter {name!r}: choose {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter(store)
