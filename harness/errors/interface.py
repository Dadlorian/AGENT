#!/usr/bin/env python3
"""Errors: one typed, machine-readable failure object for every boundary.

Read it in this order. REGISTRY is the closed problem-type registry, transcribed
from cap-errors's references/problem-registry.md (itself from
docs/decomposition.md section 2.1.6; proposed). construct() is the one gate
every Problem passes through: an unregistered suffix, or an extension member a
suffix does not declare, never gets past it (F-b3-13, X-cap-errors-003).
ErrorsAdapter is the interface the core imports: raise_problem is concrete so
no adapter can bypass the registry gate; retry_advice is concrete so no
adapter can infer retryable from a status code (X-cross-structure-040);
classify is the one place the two adapters differ, because an in-process
adapter sees the raise site and an edge adapter sees only the wire (F-b1-04).

No product name appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

INTERFACE_VERSION = "0.1"
MEDIA_TYPE = "application/problem+json"
PROBLEM_BASE = "urn:agentic:problem:"

# suffix -> (status, title, retryable, declared extension members)
# Transcribed from cap-errors/references/problem-registry.md section 2.
REGISTRY = {
    "document-invalid":       (422, "The document is not well-formed", False, ("causes",)),
    "criterion-unresolvable": (422, "criterion_ref does not resolve", False, ()),
    "identity-untrusted":     (401, "The delegation chain does not verify", False, ()),
    "policy-denied":          (403, "A deterministic pre-execution refusal", False, ("rule_id",)),
    "budget-exhausted":       (402, "A metered call would cross the ceiling", False, ("stop_reason",)),
    "deadline-exceeded":      (504, "Wall clock ceiling reached", True, ("retry_after_s",)),
    "cancel-timeout":         (500, "Grace window elapsed, unit destroyed", False, ("stop_reason",)),
    "isolation-unavailable":  (503, "No isolation adapter could admit the unit", True, ("retry_after_s",)),
    "adapter-unavailable":    (503, "A capability adapter is down, or raised an untyped failure", True, ("retry_after_s",)),
    "idempotency-conflict":   (409, "Same key, different request body", False, ()),
}


class UnregisteredType(ValueError):
    """A suffix with no row in the closed registry, or an extension member its
    row does not declare. Construction fails closed: this can never reach a
    wire body (cap-errors invariant: 'An unregistered type URI is a
    conformance failure on this platform', X-cap-errors-003)."""


@dataclass(frozen=True)
class Problem:
    """The RFC 9457 wire shape (application/problem+json), plus the platform's
    explicit retryable and correlation_id members (cap-errors contract.shapes)."""
    type: str
    title: str
    status: int
    detail: str
    retryable: bool
    correlation_id: str | None = None
    causes: tuple = ()
    ext: dict = field(default_factory=dict)  # rule_id, stop_reason, retry_after_s, ...

    def body(self) -> dict:
        """The wire object, in a fixed key order so two adapters can be
        compared byte for byte."""
        doc = {"type": self.type, "title": self.title, "status": self.status,
               "detail": self.detail, "retryable": self.retryable}
        if self.correlation_id:
            doc["correlation_id"] = self.correlation_id
        doc.update(self.ext)
        if self.causes:
            doc["causes"] = [c.body() if isinstance(c, Problem) else c for c in self.causes]
        return doc

    def canonical(self) -> bytes:
        return json.dumps(self.body(), sort_keys=True, separators=(",", ":")).encode()

    def suffix(self) -> str:
        return self.type[len(PROBLEM_BASE):]


class ProblemException(Exception):
    """A Problem, raised. What a caller actually catches (cap-errors: 'Never
    parsed from prose' -- a caller branches on .problem.type, never on str(exc))."""

    def __init__(self, problem: Problem):
        self.problem = problem
        super().__init__(problem.detail)


def construct(suffix: str, detail: str, correlation_id: str | None = None, **ext) -> Problem:
    """The one gate every Problem passes through."""
    row = REGISTRY.get(suffix)
    if row is None:
        raise UnregisteredType(f"{suffix!r} has no row in the closed registry; "
                                f"registered suffixes are {sorted(REGISTRY)}")
    status, title, retryable, declared = row
    extra = sorted(set(ext) - set(declared))
    if extra:
        raise UnregisteredType(f"{suffix!r} does not declare extension member(s) {extra}; "
                                f"declared members for this type are {declared or ()!r}")
    return Problem(PROBLEM_BASE + suffix, title, status, detail, retryable, correlation_id, (), dict(ext))


def problem_from_body(doc: dict) -> Problem:
    """Rebuild a Problem from a wire body already known to be well-formed and
    registered. Used by classify() when a body has already passed the checks
    that gate it, so no field is re-derived, only re-shaped."""
    fixed = {"type", "title", "status", "detail", "retryable", "correlation_id", "causes"}
    causes = tuple(problem_from_body(c) for c in doc.get("causes", ()))
    return Problem(doc["type"], doc["title"], doc["status"], doc.get("detail", ""),
                   doc["retryable"], doc.get("correlation_id"), causes,
                   {k: v for k, v in doc.items() if k not in fixed})


class ErrorsAdapter(ABC):
    """One failure interface: raise_problem, classify, retry_advice, chain.

    raise_problem and retry_advice are concrete here so that no adapter can
    bypass the registry gate or infer retryable from a status code; classify
    is the one operation each execution model must supply for itself.
    """

    entity = "adapter"
    execution_model = "in-process"   # in-process | edge-filter (F-b1-04)
    declared_marker = "unset"
    declared_gaps: tuple = ()

    def __init__(self):
        self.responses_checked = 0
        self.untyped = 0
        self.unregistered_types = 0
        self.wrong_media_type = 0

    # 1. raise_problem -- the only way a registered Problem is minted. It
    # always raises; there is no return value a caller could forget to check.
    def raise_problem(self, suffix: str, detail: str, correlation_id: str | None = None,
                       **ext) -> None:
        problem = construct(suffix, detail, correlation_id, **ext)
        self.responses_checked += 1
        raise ProblemException(problem)

    # 2. retry_advice -- read the member, never infer from status
    @staticmethod
    def retry_advice(problem: Problem) -> tuple[bool, int | None]:
        return problem.retryable, problem.ext.get("retry_after_s")

    # 3. chain -- append an inner Problem, innermost last
    @staticmethod
    def chain(outer: Problem, inner: Problem) -> Problem:
        return Problem(outer.type, outer.title, outer.status, outer.detail, outer.retryable,
                        outer.correlation_id, outer.causes + (inner,), dict(outer.ext))

    # 4. classify -- the seam where execution model matters
    @abstractmethod
    def classify(self, wire: dict) -> Problem:
        """wire: {"status": int, "media_type": str, "body": dict | str}.

        A registered, well-formed body is reshaped and returned unchanged in
        content. A body this adapter cannot type falls through to
        adapter-unavailable with the untyped payload in detail, and is
        counted -- never silently forwarded (cap-errors-implement rule 2)."""

    def _fallback(self, raw_detail: str, wrong_media_type: bool = False) -> Problem:
        self.responses_checked += 1
        self.untyped += 1
        if wrong_media_type:
            self.wrong_media_type += 1
        return construct("adapter-unavailable", raw_detail, retry_after_s=30)
