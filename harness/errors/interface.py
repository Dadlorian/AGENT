#!/usr/bin/env python3
"""Errors: one typed, machine-readable failure object for every boundary.

Read it in this order. REGISTRY is the closed problem-type registry, transcribed
from cap-errors's references/problem-registry.md (itself from
docs/decomposition.md section 2.1.6; proposed). construct() is the one gate
every Problem passes through: an unregistered suffix, or an extension member a
suffix does not declare, never gets past it (F-b3-13, X-cap-errors-003). It
does not build the Problem object itself -- problem.py's construct_problem()
does that, the one shared point every path here (construct(), chain(),
problem_from_body()) renders into (errors-q5, X-maturity-a-003, X-maturity-a-004).
ErrorsAdapter is the interface the core imports: raise_problem is concrete so
no adapter can bypass the registry gate; retry_advice is concrete so no
adapter can infer retryable from a status code (X-cross-structure-040);
classify is the one place the two adapters differ, because an in-process
adapter sees the raise site and an edge adapter sees only the wire (F-b1-04).

No product name appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from problem import (MEDIA_TYPE, PROBLEM_BASE, Problem, ProblemException,  # noqa: F401
                      construct_problem, reshape_from_body)

INTERFACE_VERSION = "0.1"

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


# Problem, ProblemException and the wire-rendering methods (body/canonical)
# live in problem.py, the one shared construction point -- not here. This
# file adds only what is specific to the errors capability: the closed
# registry and the gate that checks a suffix against it.


def construct(suffix: str, detail: str, correlation_id: str | None = None, **ext) -> Problem:
    """The one gate every Problem passes through. Validates the suffix and
    its extension members against the closed registry, then hands the
    validated fields to problem.py's construct_problem() -- it never builds
    the Problem object itself."""
    row = REGISTRY.get(suffix)
    if row is None:
        raise UnregisteredType(f"{suffix!r} has no row in the closed registry; "
                                f"registered suffixes are {sorted(REGISTRY)}")
    status, title, retryable, declared = row
    extra = sorted(set(ext) - set(declared))
    if extra:
        raise UnregisteredType(f"{suffix!r} does not declare extension member(s) {extra}; "
                                f"declared members for this type are {declared or ()!r}")
    return construct_problem(PROBLEM_BASE + suffix, title, status, detail, retryable, correlation_id, (), dict(ext))


def problem_from_body(doc: dict) -> Problem:
    """Rebuild a Problem from a wire body already known to be well-formed and
    registered. Used by classify() when a body has already passed the checks
    that gate it, so no field is re-derived, only re-shaped. Delegates to
    problem.py's reshape_from_body(), which itself routes through
    construct_problem() -- not a second construction path."""
    return reshape_from_body(doc)


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

    # 3. chain -- append an inner Problem, innermost last. Reshapes an
    # already-validated Problem through construct_problem(), same as
    # problem_from_body() -- never the dataclass constructor directly.
    @staticmethod
    def chain(outer: Problem, inner: Problem) -> Problem:
        return construct_problem(outer.type, outer.title, outer.status, outer.detail, outer.retryable,
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
