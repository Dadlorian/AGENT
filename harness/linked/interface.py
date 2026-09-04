#!/usr/bin/env python3
"""The consumption interface: one envelope in, one result or one problem out.

This is the whole caller vocabulary of the linked section. Read it in this
order:

  Envelope        the one entry shape all four doors produce (T-t6-02)
  DOOR_FIELDS     the members a door is allowed to differ on, and no others
  subject_digest  the digest of everything else - the document itself
  Plan / PlanStep the resolved plan, priced before anything executes (F-b1-06)
  Result          the one typed result
  Problem         the one typed failure, from a closed registry (F-b4-07)
  Entry           the abstract door: raw message in, envelope out
  Platform        the abstract consumer: envelope in, result or problem out

There is no third kind of answer, no field naming which implementation
answered, and no product name anywhere in this file.

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
from typing import Any, Mapping

ENVELOPE_VERSION = "0.1"
ENTRY_KINDS = ("human", "event", "schedule", "external")

# --- Typed failures: RFC 9457 problem details, one closed registry ----------
# The registry is the union of the four component registries plus this
# section's own rows, so a problem raised three levels down is either in it or
# is a conformance failure. Nothing is minted outside this table.
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":       (422, "The entry envelope fails validation", False),
    "budget-exhausted":       (402, "The work would cross the ceiling", False),
    "idempotency-conflict":   (409, "Same idempotency key, different envelope", False),
    "adapter-unavailable":    (503, "A capability adapter is unreachable", True),
    "isolation-unavailable":  (503, "No isolation adapter could admit the unit", True),
    "runtime-unavailable":    (503, "No agent runtime could serve the turn", True),
    "criterion-unresolvable": (422, "criterion_ref does not resolve", False),
    "deadline-exceeded":      (504, "A declared ceiling was reached", True),
}


class Problem(Exception):
    """A failure a caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext: Any) -> None:
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)

    @staticmethod
    def registered(type_uri: str) -> bool:
        return (type_uri.startswith(PROBLEM_BASE)
                and type_uri[len(PROBLEM_BASE):] in REGISTRY)

    @classmethod
    def adopt(cls, body: Mapping[str, Any], **ext: Any) -> "Problem":
        """A problem a component raised, carried out unchanged except for the
        correlation this section adds. A type outside the closed registry is
        refused here rather than passed to a caller."""
        type_uri = str(body.get("type", ""))
        if not cls.registered(type_uri):
            raise KeyError(f"component raised an unregistered problem type {type_uri!r}")
        out = cls.__new__(cls)
        Exception.__init__(out, body.get("detail", ""))
        out.body = {**body, **ext}
        return out


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --- The one entry shape ----------------------------------------------------
# A door may differ on these members and on nothing else: which door it was,
# that door's own message identity and clock, who is acting, the correlation
# the platform minted, and the key that makes the submission safe to repeat.
DOOR_FIELDS = ("kind", "entry_id", "occurred_at", "actor", "correlation", "idempotency_key")


@dataclass(frozen=True)
class Envelope:
    kind: str
    entry_id: str
    occurred_at: str
    actor: dict
    intent: dict
    correlation: dict
    budget: dict
    idempotency_key: str
    payload: dict
    envelope_version: str = ENVELOPE_VERSION

    @classmethod
    def from_dict(cls, doc: Mapping[str, Any]) -> "Envelope":
        return cls(**{f: doc[f] for f in cls.__dataclass_fields__ if f in doc})

    def dict(self) -> dict:
        return asdict(self)

    def subject(self) -> dict:
        """Everything a door may not change: the document, what to run with it,
        and what it may spend."""
        return {k: v for k, v in self.dict().items() if k not in DOOR_FIELDS}

    def subject_digest(self) -> str:
        return digest(self.subject())

    def envelope_digest(self) -> str:
        return digest(self.dict())

    @property
    def run_id(self) -> str:
        return self.correlation["run_id"]

    @property
    def correlation_id(self) -> str:
        return self.correlation["correlation_id"]

    @property
    def actor_subject(self) -> str:
        return self.actor["subject"]

    @property
    def identity_hops(self) -> int:
        return len(self.actor["delegation_chain"])

    @property
    def ceiling_micros(self) -> int:
        return int(self.budget["ceiling_micros"])


# --- The resolved plan: a pure function of the envelope ---------------------
@dataclass(frozen=True)
class PlanStep:
    step_id: str
    op: str
    model_class: str
    estimate_micros: int


@dataclass(frozen=True)
class Plan:
    sequence_id: str
    steps: tuple[PlanStep, ...]
    total_micros: int
    ceiling_micros: int

    def digest(self) -> str:
        return digest({"sequence_id": self.sequence_id, "ceiling_micros": self.ceiling_micros,
                       "total_micros": self.total_micros,
                       "steps": [asdict(s) for s in self.steps]})


# --- The one result, and what is deliberately not in it --------------------
@dataclass(frozen=True)
class Result:
    """What every door reads back. There is nothing here that names a
    containment technology, a vendor, a backend or an executor, and nothing a
    caller could branch on to learn which implementation answered."""
    kind: str
    actor_subject: str
    identity_hops: int
    run_id: str
    correlation_id: str
    subject_digest: str
    plan_digest: str
    envelope_digest: str
    outcome: str                       # "completed" | "replayed"
    stop_reason: str
    spent_micros: int
    ceiling_micros: int

    def dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Receipt:
    """Not part of the answer. What this section measures about one run: the
    per-step spend, the trace as it was read back, the containment report the
    host asserted, and the markers read from the running components. The
    conformance run and the section's own tables read it; a caller never sees
    it, which is why the swap proof can compare markers without any of them
    reaching a result."""
    run_id: str
    kind: str
    step_costs: dict = field(default_factory=dict)
    nested_ceiling_micros: int = 0
    steps_committed: int = 0
    executor_spent_micros: int = 0
    trace: dict = field(default_factory=dict)
    containment: dict = field(default_factory=dict)
    markers: dict = field(default_factory=dict)
    units_admitted: int = 0
    gateway_dispatches: int = 0
    durable_records_written: int = 0
    negotiated: dict = field(default_factory=dict)

    def dict(self) -> dict:
        return asdict(self)


# --- The two abstract halves ------------------------------------------------
class Entry(ABC):
    """One door. A producer's own message goes in; the one envelope comes out.
    A door supplies the actor and its own message identity; correlation, budget
    and the idempotency key are stamped for it and cannot be declined."""

    kind: str = "unset"

    @abstractmethod
    def envelope(self, subject: Mapping[str, Any]) -> Envelope:
        ...


class Platform(ABC):
    """The one operation a caller makes. One entry envelope in, one result or
    one problem out - never both, never a third kind."""

    @abstractmethod
    def submit(self, doc: Mapping[str, Any]) -> Result | Problem:
        ...
