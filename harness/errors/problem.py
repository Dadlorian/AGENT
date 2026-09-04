#!/usr/bin/env python3
"""The one shared construction point for every Problem body this capability
renders.

errors-q5 (docs/maturity/closures.json): "Is the production of the failure
object owned by one place the core imports, so a new capability adapter
cannot invent its own failure shape?" This module is that place. It is the
only file under harness/errors that calls the Problem dataclass constructor
-- construct_problem() below is the one call site -- and the only file that
knows how to render the RFC 9457 wire shape (application/problem+json):
type, title, status, detail, plus the platform's retryable and
correlation_id members, plus whatever extension members a registry row
declares (X-maturity-a-003: "Mature frameworks define one shared
ProblemDetail construction type that all typed exceptions are mapped into,
rather than each error site building its own body"; X-maturity-a-004:
centralized, framework-wide construction with no per-site opt-in is the
settling direction, e.g. Spring Boot 4's default Problem Details handling).

interface.py's construct() (the registry gate) and chain() (append a cause)
and problem_from_body() (reshape an already-validated wire body) all end
here rather than building a Problem themselves -- that is what keeps a new
capability adapter from inventing its own failure shape: there is nowhere
else in this tree for it to build one. harness/errors/test.sh's
construction-scan step (conformance.py --construction-scan) is the
mechanical check: it scans every .py file under harness/errors for a direct
direct call to the Problem constructor and asserts there is exactly one, right here.

No product name appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

MEDIA_TYPE = "application/problem+json"
PROBLEM_BASE = "urn:agentic:problem:"


@dataclass(frozen=True)
class Problem:
    """The RFC 9457 wire shape (application/problem+json), plus the
    platform's explicit retryable and correlation_id members (cap-errors
    contract.shapes). Defined once, here."""
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
        compared byte for byte. The only place this platform renders
        application/problem+json."""
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
        return self.type[len(PROBLEM_BASE):] if self.type.startswith(PROBLEM_BASE) else self.type


class ProblemException(Exception):
    """A Problem, raised. What a caller actually catches (cap-errors: 'Never
    parsed from prose' -- a caller branches on .problem.type, never on str(exc))."""

    def __init__(self, problem: Problem):
        self.problem = problem
        super().__init__(problem.detail)


def construct_problem(type_: str, title: str, status: int, detail: str, retryable: bool,
                       correlation_id: str | None = None, causes: tuple = (),
                       ext: dict | None = None) -> Problem:
    """THE construction point: the only function anywhere under
    harness/errors that calls the Problem constructor. A capability's own registry gate
    (interface.py's construct()) validates a suffix and its declared
    extension members and then calls this; chain() and problem_from_body()
    reshape an already-validated Problem/body and also call this -- never
    the dataclass constructor directly. That is the property the
    construction-scan step in test.sh checks by grepping the tree for a
    second call site."""
    return Problem(type_, title, status, detail, retryable, correlation_id,
                    tuple(causes), dict(ext or {}))


_RENDER_COUNT = 0  # incremented once per render_body() call, by every capability that
# imports it. The platform-wide test (platform_conformance.py --raise-all) raises every
# typed condition every harness under harness/ defines and asserts the counter rose by
# exactly that many -- proof that each one rendered through this function, not a local
# copy (errors-q5's second clause: "a test that raises every typed condition the build
# defines and asserts each is rendered by that same single path, never a second one").


def render_body(type_: str, title: str, status: int, detail: str, retryable: bool,
                 ext: dict | None = None) -> dict:
    """The one function anywhere under harness/ that assembles the RFC 9457 wire
    dict (application/problem+json: type, title, status, detail, retryable, plus
    extension members). errors-q5: a capability keeps its own closed registry and
    its own typed exception/condition class -- cap-errors names each capability's
    own typed conditions, and that is correct -- but the *serialization* into the
    wire shape is owned here alone. Every other harness's Problem.__init__ (or, for
    the two dataclass-shaped interfaces, its as_dict()) calls this instead of
    building the dict itself; platform_conformance.py's construction scan is the
    mechanical check that no second hand-built dict with this key set exists
    anywhere else under harness/, and --raise-all is the dynamic companion that
    raises every row of every registry and confirms each one passed through here."""
    global _RENDER_COUNT
    _RENDER_COUNT += 1
    doc = {"type": type_, "title": title, "status": status, "detail": detail, "retryable": retryable}
    doc.update(ext or {})
    return doc


def render_count() -> int:
    """How many times render_body() has run in this process. Read by
    platform_conformance.py --raise-all before and after raising every typed
    condition across every harness loaded into that process."""
    return _RENDER_COUNT


def reshape_from_body(doc: dict) -> Problem:
    """Rebuild a Problem from a wire body a caller's gate has already found
    well-formed and registered (e.g. adapters/second.py's classify(), after
    its own media-type and registry checks pass). No field is re-derived --
    only re-shaped -- and it still goes through construct_problem(), never
    the dataclass constructor directly, so an edge adapter reshaping a body
    is not a second place a failure body gets built."""
    fixed = {"type", "title", "status", "detail", "retryable", "correlation_id", "causes"}
    causes = tuple(reshape_from_body(c) for c in doc.get("causes", ()))
    return construct_problem(doc["type"], doc["title"], doc["status"], doc.get("detail", ""),
                              doc["retryable"], doc.get("correlation_id"), causes,
                              {k: v for k, v in doc.items() if k not in fixed})
