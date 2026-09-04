#!/usr/bin/env python3
"""Audit trail: every action attributable to an actor, reachable by correlation id,
chained so interference is detectable, checked by a process other than the writer.

Read it in this order. AppendRequest is the whole writer vocabulary: an action,
an actor, its delegation chain, a correlation pair and an entry kind - never a
free-text log line. TrailAdapter.append() is a template method: it stamps the
hash chain and refuses an entry missing an actor or a correlation id before any
adapter code runs, so no binding can mint an unattributable entry. scan() is
also concrete: it recomputes the chain over whatever project() returns and
reports independent/scheduled/store_observed as it finds them, never as it was
told to expect them (F-a7-04) - the caller (scan.py) supplies the identity and
whether it was invoked on a schedule, and scan() only ever reports what those
turned out to be, never a value it assumed.

No product name, endpoint or store path appears in this file (T-t7-02, F-b1-02).
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

INTERFACE_VERSION = "0.1"
KINDS = ("user", "agent", "service", "schedule")   # TARGET T6.2's four entries

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) -----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {
    "document-invalid": (422, "The audit request is not well formed", False),
    "adapter-unavailable": (503, "No trail store serves this window", True),
    "independence-violated": (409, "The scan was not run independently of the writer", False),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


def canonical(doc: dict) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- The caller vocabulary --------------------------------------------------
ALLOWED = {"action", "actor", "delegation_chain", "correlation", "kind", "at"}
REQUIRED = {"action", "actor", "correlation", "kind"}


@dataclass(frozen=True)
class AppendRequest:
    action: str
    actor: str
    delegation_chain: tuple
    correlation: dict          # {"run_id":..., "correlation_id":...}
    kind: str                  # one of KINDS
    at: str = ""                # adapter stamps its clock when empty

    @classmethod
    def from_dict(cls, doc: dict) -> "AppendRequest":
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "an audit request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the audit vocabulary; the trail is applied by the "
                          f"platform from records it already writes, so there is nothing to opt into",
                          rejected_fields=extra)
        missing = sorted(REQUIRED - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        if not isinstance(doc["actor"], str) or not doc["actor"]:
            raise Problem("document-invalid", "actor must be a non-empty string; every action is attributable")
        corr = doc["correlation"]
        if not isinstance(corr, dict) or not corr.get("run_id") or not corr.get("correlation_id"):
            raise Problem("document-invalid",
                          "correlation must carry run_id and correlation_id; the whole run has to be "
                          "reachable by one correlation id")
        if doc["kind"] not in KINDS:
            raise Problem("document-invalid", f"kind must be one of {KINDS}", got=doc["kind"])
        chain = tuple(doc.get("delegation_chain") or [{"actor": doc["actor"], "obtained_via": "direct"}])
        if chain[-1]["actor"] != doc["actor"]:
            raise Problem("document-invalid", "the delegation chain must end at the actor named on the entry")
        return cls(doc["action"], doc["actor"], chain, dict(corr), doc["kind"], doc.get("at", ""))


@dataclass(frozen=True)
class AuditEntry:
    entry_id: str
    seq: int
    prev: str
    hash: str
    action: str
    actor: str
    delegation_chain: tuple
    correlation: dict
    kind: str
    at: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["delegation_chain"] = list(self.delegation_chain)
        return d


def entry_hash(prev: str, action: str, actor: str, delegation_chain, correlation: dict, kind: str, at: str) -> str:
    """The chain: every field but the hash itself and the entry_id it derives from."""
    return sha256_hex(canonical({"prev": prev, "action": action, "actor": actor,
                                 "delegation_chain": list(delegation_chain), "correlation": correlation,
                                 "kind": kind, "at": at}))


@dataclass
class ScanReport:
    """The AuditTrailConformanceReport shape xc-audit-trail-implement fixes."""
    store: str
    store_observed: str
    from_head: str
    to_head: str
    entries_checked: int
    actors_missing: int
    correlation_missing: int
    chain_breaks: int
    coverage_start: str
    external_verifications: int
    oldest_retained_entry_age_days: int
    scheduled_runs_observed: int
    independent: bool
    scheduled: bool
    entry_kinds_seen: list
    adapters_run: int
    first_break_at: int = -1

    def to_dict(self) -> dict:
        return asdict(self)


# --- The interface the core imports -----------------------------------------
class TrailAdapter(ABC):
    """One trail interface. project, fetch_by_correlation, attribute, append, scan."""

    entity = "adapter"
    execution_model = "unset"
    writer_identity = "actor:writer-process"     # who append() runs as; scan is independent iff it differs
    declared_gaps: tuple = ()
    external_checkable = False                   # can a party holding none of our credentials verify?

    def __init__(self):
        self.appended = 0
        self.refusals = 0

    # 1. append -- always chains, always attributes
    def append(self, request: AppendRequest) -> AuditEntry:
        if not isinstance(request, AppendRequest):
            self.refusals += 1
            raise Problem("document-invalid", "append takes a validated AppendRequest")
        prev = self.head()
        at = request.at or self._clock()
        h = entry_hash(prev, request.action, request.actor, request.delegation_chain,
                       request.correlation, request.kind, at)
        entry = AuditEntry(entry_id="urn:agentic:audit:" + h[:24], seq=self._next_seq(), prev=prev, hash=h,
                           action=request.action, actor=request.actor,
                           delegation_chain=request.delegation_chain, correlation=request.correlation,
                           kind=request.kind, at=at)
        self._append(entry)
        self.appended += 1
        return entry

    # 2. project -- records into the entry shape, read-only
    @abstractmethod
    def project(self, from_seq: int | None = None, to_seq: int | None = None) -> list:
        ...

    # 3. fetch_by_correlation -- everything under one correlation id
    def fetch_by_correlation(self, correlation_id: str) -> list:
        return [e for e in self.project() if e.correlation.get("correlation_id") == correlation_id]

    # 4. attribute -- the actor and delegation chain for one entry
    def attribute(self, entry_id: str) -> dict:
        for e in self.project():
            if e.entry_id == entry_id:
                return {"actor": e.actor, "delegation_chain": list(e.delegation_chain)}
        raise Problem("document-invalid", f"no entry {entry_id} in this trail")

    # 5. scan -- run from a process other than the one that appends; report what actually ran
    def scan(self, identity: str, scheduled: bool, from_seq: int | None = None,
             to_seq: int | None = None) -> ScanReport:
        entries = self.project(from_seq, to_seq)
        chain_breaks = actors_missing = correlation_missing = 0
        first_break = -1
        kinds = set()
        prev = entries[0].prev if entries else self.head()
        for i, e in enumerate(entries):
            expect = entry_hash(prev, e.action, e.actor, e.delegation_chain, e.correlation, e.kind, e.at)
            if e.prev != prev or e.hash != expect:
                chain_breaks += 1
                if first_break < 0:
                    first_break = e.seq
            prev = e.hash
            if not e.actor:
                actors_missing += 1
            if not e.correlation.get("correlation_id"):
                correlation_missing += 1
            kinds.add(e.kind)
        oldest_days = self._age_days(entries[0].at) if entries else 0
        return ScanReport(
            store=self.adapter_kind, store_observed=self.entity,
            from_head=entries[0].prev if entries else "genesis",
            to_head=entries[-1].hash if entries else self.head(),
            entries_checked=len(entries), actors_missing=actors_missing,
            correlation_missing=correlation_missing, chain_breaks=chain_breaks,
            coverage_start=self.coverage_start(), external_verifications=self.external_verifications(),
            oldest_retained_entry_age_days=oldest_days,
            scheduled_runs_observed=1 if scheduled else 0,
            independent=(identity != self.writer_identity), scheduled=scheduled,
            entry_kinds_seen=sorted(kinds), adapters_run=1,
            first_break_at=(first_break if chain_breaks else -1))

    # --- adapter's own business -----------------------------------------
    @abstractmethod
    def head(self) -> str:
        """The current chain head, or 'genesis' for an empty trail."""

    @abstractmethod
    def coverage_start(self) -> str:
        """The instant from which the trail is attributable (ISO-8601)."""

    @abstractmethod
    def external_verifications(self) -> int:
        """How many times a party holding none of our credentials has checked this window."""

    @abstractmethod
    def store_integrity(self) -> dict:
        """What this binding says about its own store. Never what the scan rests on."""

    @abstractmethod
    def _append(self, entry: AuditEntry) -> None:
        ...

    @abstractmethod
    def _next_seq(self) -> int:
        ...

    @abstractmethod
    def _clock(self) -> str:
        ...

    @abstractmethod
    def _age_days(self, at: str) -> int:
        ...

    def binding(self) -> dict:
        return {"adapter": self.adapter_kind, "entity": self.entity, "execution_model": self.execution_model,
                "external_checkable": self.external_checkable, "declared_gaps": list(self.declared_gaps)}

    adapter_kind = "unset"       # jsonl-hash-chain | external-checkable-log
