#!/usr/bin/env python3
"""Idempotency: the capability interface, and nothing else.

The whole vocabulary is four calls - claim, complete, resolve, expire - over one
shape, ClaimOutcome, with exactly three answers: fresh (this caller now owns the
one execution), duplicate (someone already ran it; here is the reference), or
conflict (the same key arrived under a different payload). cap-idempotency names
these as the proposed operation set over the recorded standard, which is a field
convention and not a set of calls (F-b3-16, F-b4-08).

What is recorded today (PASS.md B3, F-b3-16) is "key on the wire, no lease": the
key is carried and required on the envelope, and nothing claims it before
execution starts. A key that is only recorded and never claimed deduplicates
nothing - both copies of a duplicated request still run. The whole point of this
interface is the one call a caller cannot skip: claim() must be answered before
the first side-effecting step, never after it, or a duplicate is counted rather
than prevented.

No product name appears in this file. They appear in adapters/live.py and in the
env-var table of README.md, and nowhere else.

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

INTERFACE_VERSION = "urn:agentic:cap:idempotency:0.1"


def digest(obj: Any) -> str:
    """Canonical digest. A claim holds this, never the payload itself
    (cap-idempotency contract.not_exposed): comparing two payloads must never
    become a reason to retain a caller's body for the retention window."""
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
# Typed failures (cap-errors / RFC 9457). The registry is the closed set this
# harness raises from; a conflict is answered through it, not with a format
# minted here (cap-idempotency-implement step 7).
# --------------------------------------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":     (422, "The claim request fails validation", False),
    "idempotency-conflict": (409, "Same key, different payload digest", False),
    "adapter-unavailable":  (503, "A capability adapter is down", True),
}


class Problem(Exception):
    """A failure a caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext: Any):
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --------------------------------------------------------------------------
# The claim request and its three-way outcome (cap-idempotency contract.shapes:
# IdempotencyClaim, ClaimOutcome). The payload never travels past this module -
# only its digest does.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ClaimRequest:
    idempotency_key: str
    payload_digest: str
    scope: str                  # the resource owner the key must be unique within
    correlation_id: str
    actor: str
    entry_kind: str
    retention_s: int = 86400    # declared window; part of the contract (X-cap-idempotency-008)

    @classmethod
    def for_payload(cls, key: str, payload: dict, scope: str, correlation_id: str,
                     actor: str, entry_kind: str, retention_s: int = 86400) -> "ClaimRequest":
        return cls(key, digest(payload), scope, correlation_id, actor, entry_kind, retention_s)


@dataclass
class ClaimOutcome:
    outcome: Literal["fresh", "duplicate", "conflict"]
    result_ref: str | None = None
    in_flight: bool = False     # True only when a duplicate is answered mid-execution
    fencing_token: int | None = None
    problem: dict | None = None


# --------------------------------------------------------------------------
# The adapter
# --------------------------------------------------------------------------
class IdempotencyAdapter(ABC):
    """Four operations. Every implementation declares how it behaves rather than
    being asked to behave alike (cap-idempotency-implement contract.invariants):
    the class attributes below are its declared gaps, and the conformance run
    asserts the adapter behaved as declared instead of widening the contract
    until both members satisfy it. A conflict is raised as the typed Problem
    above from inside claim(); it is never returned as a silent third value a
    caller could forget to check.
    """

    adapter_marker: str = "unset"                                   # read back by a report
    unit_of_conditionality: str = "unset"                            # log-row | keyed-compare-and-set
    supports_in_flight: bool = False                                 # can it answer a duplicate mid-execution?
    processes_required_for_progress: int = 1

    def binding(self) -> dict:
        return {"adapter": type(self).__name__, "adapter_marker": self.adapter_marker,
                "unit_of_conditionality": self.unit_of_conditionality,
                "supports_in_flight": self.supports_in_flight,
                "processes_required_for_progress": self.processes_required_for_progress,
                "interface_version": INTERFACE_VERSION}

    @abstractmethod
    def claim(self, req: ClaimRequest) -> ClaimOutcome:
        """fresh: this caller now owns the one execution. duplicate: someone
        already claimed this key with this payload; result_ref (and in_flight)
        say what to do next. Raises Problem(idempotency-conflict) when the key
        is held under a different payload digest."""

    @abstractmethod
    def complete(self, key: str, scope: str, result_ref: str) -> None:
        """Seal a fresh claim against the result it produced. Every later claim
        of this key answers duplicate with this reference until the window
        elapses."""

    @abstractmethod
    def resolve(self, key: str, scope: str) -> ClaimOutcome | None:
        """The read a planner makes before planning work already done. None
        when the key has never been claimed."""

    @abstractmethod
    def expire(self, key: str, scope: str, now: float | None = None) -> bool:
        """True when a claim whose retention window has elapsed was removed;
        the key is claimable again after. now overrides the clock so the
        window is observable without a real wait (build-adapter-pair T-a7-04:
        verify the runtime effect, not the file that declares it)."""


ADAPTERS = ("dryrun", "second", "live")


def load_adapter(name: str, out_dir: str) -> IdempotencyAdapter:
    """Binding is configuration: one name from the environment, one import, one
    class. Every adapter module exports its entry point as `Adapter`."""
    import importlib
    if name not in ADAPTERS:
        raise Problem("document-invalid", f"unknown adapter {name!r}: choose {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter(out_dir)
