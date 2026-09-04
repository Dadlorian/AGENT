#!/usr/bin/env python3
"""Memory: remember, recall, supersede, forget - scoped items a later run can act on
without being handed its predecessor's transcript (cap-memory).

Read it in this order. Problem is the one typed refusal shape every adapter
raises. RememberRequest.from_dict is the whole caller vocabulary for a write -
a scope, a body, a kind, provenance and a staleness policy. MemoryAdapter.remember
and MemoryAdapter.recall are template methods: remember refuses a write with no
expiry before any adapter code runs, and recall drops an expired item on read
before any adapter code sees the result - so the on-read expiry rule holds
identically whichever store answers, which is exactly the seam the deliberate
breakage in test.sh targets.

No ratified standard governs this interface (cap-memory: "none found"); the
binding record and recall shapes are this repository's own design.

No product name, endpoint or store path appears in this file (T-t7-02).
Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
# Found by walking up from this file's own directory, not by a fixed "../errors"
# offset: several harnesses' test.sh copy interface.py into out/breakage/ (and
# deeper) for a deliberate-breakage run, and a fixed relative offset would miss
# harness/errors/problem.py from there. The walk stays inside the repository
# tree either way (out/breakage/ is still nested under this harness's own
# directory), and stops at the first "errors" sibling that actually has it.
_search_dir = _errors_os.path.dirname(_errors_os.path.abspath(__file__))
for _ in range(10):
    _candidate = _errors_os.path.join(_search_dir, "errors")
    if _errors_os.path.isfile(_errors_os.path.join(_candidate, "problem.py")):
        if _candidate not in _errors_sys.path:
            _errors_sys.path.append(_candidate)  # appended, never inserted at 0: this
            # harness's own adapters/ package must resolve before errors/adapters/ does
        break
    _up = _errors_os.path.dirname(_search_dir)
    if _up == _search_dir:
        break
    _search_dir = _up
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import datetime
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry (cap-errors) --
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "Request is not a well-formed memory document", False),
    "staleness-missing": (422, "A write with no staleness policy is refused, not defaulted", False),
    "policy-denied": (403, "The scope is not yours", False),
    "item-not-found": (404, "No such memory item at this binding", False),
    "adapter-unavailable": (503, "This binding cannot serve the operation", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


def _digest_id(obj) -> str:
    canon = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "mem-" + hashlib.sha256(canon).hexdigest()[:24]


def now_iso(clock_env: str | None = None) -> str:
    import os
    fixed = os.environ.get(clock_env or "MEMORY_CLOCK")
    dt = datetime.datetime.fromisoformat(fixed) if fixed else datetime.datetime.now(datetime.timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


SCOPE_DIMENSIONS = ("principal", "agent", "run", "org")
KINDS = ("working", "episodic", "semantic", "procedural")

# --- The caller vocabulary: remember ----------------------------------------
ALLOWED = {"scope", "kind", "body", "produced_by", "correlation_id", "expires_at", "review_after"}
REQUIRED = {"scope", "kind", "body", "produced_by", "correlation_id"}


@dataclass(frozen=True)
class RememberRequest:
    scope: dict
    kind: str
    body: dict
    produced_by: str
    correlation_id: str
    expires_at: str | None
    review_after: str | None = None

    @classmethod
    def from_dict(cls, doc: dict) -> "RememberRequest":
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a remember request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid", f"fields {extra} are not in the remember vocabulary", rejected_fields=extra)
        missing = sorted(REQUIRED - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        scope = doc["scope"]
        if not isinstance(scope, dict) or not scope:
            raise Problem("document-invalid", "scope must be a non-empty object naming at least one dimension")
        bad_dims = sorted(set(scope) - set(SCOPE_DIMENSIONS))
        if bad_dims:
            raise Problem("document-invalid", f"scope dimensions {bad_dims} are not principal/agent/run/org", rejected_fields=bad_dims)
        if doc["kind"] not in KINDS:
            raise Problem("document-invalid", f"kind must be one of {KINDS}")
        if not isinstance(doc["body"], dict):
            raise Problem("document-invalid", "body must be an object; the store never inspects its fields")
        if "expires_at" not in doc or doc.get("expires_at") is None:
            raise Problem("staleness-missing", "every write carries a staleness policy; expires_at was absent or null")
        return cls(dict(scope), doc["kind"], doc["body"], doc["produced_by"], doc["correlation_id"],
                   doc["expires_at"], doc.get("review_after"))


@dataclass(frozen=True)
class Provenance:
    produced_by: str
    observed_at: str
    correlation_id: str
    supersedes: str | None = None


@dataclass(frozen=True)
class Staleness:
    expires_at: str | None
    review_after: str | None = None


@dataclass(frozen=True)
class MemoryItem:
    memory_id: str
    scope: dict
    kind: str
    body: dict
    provenance: Provenance
    staleness: Staleness
    superseded_by: str | None = None


@dataclass(frozen=True)
class RecallQuery:
    scope: dict
    need: str | None = None
    key: str | None = None
    limit: int = 10

    @classmethod
    def from_dict(cls, doc: dict) -> "RecallQuery":
        scope = doc.get("scope")
        if not isinstance(scope, dict) or not scope:
            raise Problem("document-invalid", "a recall must name at least one scope dimension")
        bad_dims = sorted(set(scope) - set(SCOPE_DIMENSIONS))
        if bad_dims:
            raise Problem("document-invalid", f"scope dimensions {bad_dims} are not principal/agent/run/org", rejected_fields=bad_dims)
        limit = doc.get("limit", 10)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise Problem("document-invalid", "limit must be a positive integer")
        return cls(dict(scope), doc.get("need"), doc.get("key"), limit)


@dataclass(frozen=True)
class RecallResult:
    items: list
    scope_applied: dict
    age_seconds: list


def item_as_dict(item: MemoryItem) -> dict:
    doc = asdict(item)
    return {k: v for k, v in doc.items() if v is not None}


def _age_seconds(item: MemoryItem, at: str) -> int:
    obs = datetime.datetime.fromisoformat(item.provenance.observed_at.replace("Z", "+00:00"))
    now = datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
    return max(0, int((now - obs).total_seconds()))


def _expired(item: MemoryItem, at: str) -> bool:
    if item.staleness.expires_at is None:
        return False
    return item.staleness.expires_at <= at


def _scope_holds(needle: dict, haystack: dict) -> bool:
    """True iff every dimension named in needle is present in haystack with the same value."""
    return all(haystack.get(k) == v for k, v in needle.items())


# --- The interface the core imports -----------------------------------------
class MemoryAdapter(ABC):
    """remember, recall, supersede, forget.

    remember and recall are concrete template methods: no adapter can decline
    the staleness-policy check on a write, or the on-read expiry filter on a
    recall - the two invariants cap-memory states as non-negotiable. Scope
    matching is delegated to _search, because the scope predicate must be part
    of the query the store executes, never a filter applied to results
    afterward (cap-memory-implement), which is exactly what a store answering
    by exact scope key and a store answering by ranked search each have to do
    for themselves.
    """

    entity = "adapter"
    role = "today"                       # "today" or "second" - the binding record's role
    retrieval_model = "ranked"           # "ranked" or "exact-key" - the axis the pair differs on
    execution_model = "unset"
    declared_marker = "unset"            # what this binding reports it reached at start-up
    declared_gaps: tuple = ()

    def __init__(self):
        self.remembers = 0
        self.recalls = 0
        self.refusals = 0
        self.expired_dropped = 0
        self.observed_marker = ""

    # 1. remember -- concrete: no write without a staleness policy
    def remember(self, request: RememberRequest) -> MemoryItem:
        if not request.scope:
            self.refusals += 1
            raise Problem("document-invalid", "scope must name at least one dimension")
        if request.expires_at is None:
            self.refusals += 1
            raise Problem("staleness-missing", "every write carries a staleness policy; expires_at was absent")
        item = MemoryItem(
            memory_id=_digest_id({"scope": request.scope, "kind": request.kind, "body": request.body,
                                  "correlation_id": request.correlation_id, "seq": self.remembers}),
            scope=dict(request.scope), kind=request.kind, body=request.body,
            provenance=Provenance(request.produced_by, now_iso(), request.correlation_id, None),
            staleness=Staleness(request.expires_at, request.review_after))
        self._write(item)
        self.remembers += 1
        self.observed_marker = self.declared_marker
        return item

    @abstractmethod
    def _write(self, item: MemoryItem) -> None:
        """Adapter-specific store. Reached only after the staleness check has held."""

    # 2. recall -- concrete wrapper: on-read expiry is enforced here, once, for every binding
    def recall(self, query: RecallQuery, actor_scope: dict | None = None) -> RecallResult:
        if not query.scope:
            self.refusals += 1
            raise Problem("document-invalid", "a recall must name at least one scope dimension")
        if actor_scope is not None and not _scope_holds(query.scope, actor_scope):
            self.refusals += 1
            raise Problem("policy-denied",
                          f"recall named scope {query.scope}; the actor holds {actor_scope}",
                          rule_id="memory.scope.not-held")
        at = now_iso()
        candidates = self._search(query)
        kept = [it for it in candidates if not _expired(it, at)]
        self.expired_dropped += len(candidates) - len(kept)
        self.recalls += 1
        self.observed_marker = self.declared_marker
        return RecallResult(kept, dict(query.scope), [_age_seconds(it, at) for it in kept])

    @abstractmethod
    def _search(self, query: RecallQuery) -> list:
        """Adapter-specific candidate search. Must apply the scope predicate itself,
        as part of the query it executes, not as a filter on its own results."""

    # 3. supersede -- a correction is a new item, never an edit in place
    @abstractmethod
    def supersede(self, memory_id: str, body: dict, produced_by: str, correlation_id: str,
                 expires_at: str | None, review_after: str | None = None) -> MemoryItem:
        ...

    # 4. forget -- one item, or a scope plus a reason; expiry also happens without this call
    @abstractmethod
    def forget(self, memory_id: str | None = None, scope: dict | None = None, reason: str = "expiry") -> int:
        ...

    # optional: a background sweep, never required for on-read correctness
    def sweep(self) -> int:
        return 0
