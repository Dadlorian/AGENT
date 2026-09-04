#!/usr/bin/env python3
"""Capability registry: one signed record per capability or agent, resolved by
name and a version constraint, digest-matched against the package it names.

Read it in this order. PublishRequest and Query are the whole caller
vocabulary: a namespace-scoped name, a semantic version and package bytes to
publish, or a name and a constraint to resolve - never a directory, an index
file or a store host. resolve() is a template method: it filters the versions
under a name to the ones the constraint allows, walks them from newest to
oldest, and for each checks the signature and then the digest against the
package bytes the adapter holds today - refusing and continuing on either
failure - until one verifies or none do. No adapter can skip that walk or
serve a record that did not verify (cap-capability-registry step 3).
publish() is a template method too: it refuses to rewrite a (namespace, name,
version) that already exists, so a change is always a new record.

No product name, path or endpoint appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only; hashlib and hmac are the only primitives.
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

import hashlib
import hmac
import json
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

INTERFACE_VERSION = "0.1"
RECORD_SCHEMA_VERSION = "urn:agentic:cap:capability-registry:record:0.1"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)*$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
CONSTRAINT_CLAUSE = re.compile(r"^(>=|<=|==|>|<)\s*(\d+\.\d+\.\d+)$")

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07,
# docs/decomposition.md 2.1.6) -----------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "Request is not a well-formed registry request", False),
    "adapter-unavailable": (503, "No store serves this binding", True),
    # cap-capability-registry's worked rejection: "record-unsigned" is proposed
    # and pending registration in docs/decomposition.md 2.1.6; until it has a
    # row an implementation returns the registered identity-untrusted, which
    # is also 401 and not retryable, with the unverified version named in
    # detail (skill.json contract.shapes "Worked example 2").
    "identity-untrusted": (401, "The record does not verify", False),
    "record-not-found": (404, "No record satisfies this name and version constraint", False),
}
PROPOSED_TYPE = PROBLEM_BASE + "record-unsigned"


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


def digest_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(doc: dict) -> bytes:
    """Sorted-key JSON, standing in for a canonical form (RFC 8785 unverified)."""
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()


def mac(key: bytes, message: bytes) -> str:
    """hashlib and hmac only. Stands in for a signature: it proves the record
    was made by a holder of the key. Swapping it for an asymmetric signer
    changes this function and the two adapters' _signer/_material and
    nothing else."""
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def parse_semver(version: str) -> tuple:
    m = SEMVER.match(version)
    if not m:
        return None
    return tuple(int(g) for g in m.groups())


def satisfies(version: str, constraint: str) -> bool:
    """Space-separated ANDed clauses: '>=1.0.0 <2.0.0'. A non-semver version
    never satisfies a constraint (cap-capability-registry step 2: a version a
    registry cannot parse falls out of ordering, it is not guessed at)."""
    parsed = parse_semver(version)
    if parsed is None:
        return False
    for clause in constraint.split():
        m = CONSTRAINT_CLAUSE.match(clause)
        if not m:
            raise Problem("document-invalid", f"constraint clause {clause!r} is not understood")
        op, bound = m.group(1), parse_semver(m.group(2))
        ok = {">=": parsed >= bound, "<=": parsed <= bound, "==": parsed == bound,
              ">": parsed > bound, "<": parsed < bound}[op]
        if not ok:
            return False
    return True


# --- The caller vocabulary --------------------------------------------------
ALLOWED_PUBLISH = {"namespace", "name", "version", "kind", "package_bytes_hex", "good_at",
                    "auth_schemes", "acceptance_criteria_ref", "rollback_to", "actor", "correlation"}
REQUIRED_PUBLISH = {"namespace", "name", "version", "kind", "package_bytes_hex", "actor"}


@dataclass(frozen=True)
class PublishRequest:
    namespace: str
    name: str
    version: str
    kind: str
    package_bytes: bytes
    good_at: tuple = ()
    auth_schemes: tuple = ()
    acceptance_criteria_ref: str | None = None
    rollback_to: str | None = None
    actor: str = ""
    correlation: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, doc: dict) -> "PublishRequest":
        """The one gate a publish request passes. No path, no store, no signer."""
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a publish request is an object")
        extra = sorted(set(doc) - ALLOWED_PUBLISH)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the publish vocabulary; a caller names a "
                          f"namespace, a name, a version and the package's bytes, never a store "
                          f"or a signer", rejected_fields=extra)
        missing = sorted(REQUIRED_PUBLISH - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        if parse_semver(doc["version"]) is None:
            raise Problem("document-invalid",
                          f"version {doc['version']!r} is not a semantic version; a record without "
                          f"one falls out of ordering rather than being guessed at (cap-capability-"
                          f"registry step 2)", version=doc["version"])
        if doc["kind"] not in ("capability", "agent"):
            raise Problem("document-invalid", "kind must be 'capability' or 'agent'")
        try:
            package_bytes = bytes.fromhex(doc["package_bytes_hex"])
        except ValueError as exc:
            raise Problem("document-invalid", f"package_bytes_hex is not hex: {exc}") from exc
        return cls(doc["namespace"], doc["name"], doc["version"], doc["kind"], package_bytes,
                   tuple(doc.get("good_at", ())), tuple(doc.get("auth_schemes", ())),
                   doc.get("acceptance_criteria_ref"), doc.get("rollback_to"),
                   doc.get("actor", ""), doc.get("correlation", {}) or {})


@dataclass(frozen=True)
class Query:
    name: str          # "namespace/name"
    constraint: str

    @classmethod
    def from_dict(cls, doc: dict) -> "Query":
        if not isinstance(doc, dict) or set(doc) - {"name", "constraint"}:
            raise Problem("document-invalid", "a query carries exactly name and constraint")
        if not isinstance(doc.get("name"), str) or not doc["name"]:
            raise Problem("document-invalid", "name must be a non-empty string")
        if not isinstance(doc.get("constraint"), str) or not doc["constraint"]:
            raise Problem("document-invalid", "constraint must be a non-empty string")
        return cls(doc["name"], doc["constraint"])


@dataclass
class CapabilityRecord:
    """capability-registry:record:0.1 (skill.json contract.shapes). Immutable
    once appended; a change is a new record under the same name."""
    namespace: str
    name: str
    version: str
    kind: str
    digest: str
    signature: str
    record_schema_version: str
    good_at: list
    auth_schemes: list
    acceptance_criteria_ref: str | None
    rollback_to: str | None
    published_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    def unsigned(self) -> dict:
        """Every field except the signature - what the signature is computed over."""
        doc = self.to_dict()
        doc.pop("signature")
        return doc


@dataclass
class Verification:
    signature_verified: bool
    digest_matched: bool


@dataclass
class ResolutionOutcome:
    """capability-registry:resolution:0.1. Never raised - a caller branches on
    `resolved`, never on an exception, for a domain-level refusal."""
    query: dict
    resolved: bool
    verification: Verification
    record: CapabilityRecord | None = None
    problem: dict | None = None

    def to_dict(self) -> dict:
        doc = {"query": self.query, "resolved": self.resolved,
               "verification": asdict(self.verification)}
        if self.record is not None:
            doc["record"] = self.record.to_dict()
        if self.problem is not None:
            doc["problem"] = self.problem
        return doc


# --- The interface the core imports -----------------------------------------
class CapabilityRegistryAdapter(ABC):
    """One registry interface: resolve, list_versions, describe, publish, verify.

    resolve and publish are concrete so that no binding can decline the
    verify-before-serve walk or the immutability check; verify is concrete so
    every binding is judged by the same two checks in the same order.
    """

    entity = "adapter"
    resolution = "unset"          # signed-index | registry-fetch
    identity_is = "unset"         # a path plus a version string | a content digest
    network_required = False
    trust_anchor = "unset"
    declared_gaps: tuple = ()

    def __init__(self):
        self.resolutions = 0
        self.refusals = 0
        self.refusal_log: list = []       # each entry carries a typed problem body

    # 1. verify -- signature first, then digest; both checked, neither skipped
    def verify(self, record: CapabilityRecord) -> Verification:
        key = self._verifying_material(record.namespace, record.name)
        sig_ok = key is not None and hmac.compare_digest(
            mac(key, canonical(record.unsigned())), record.signature)
        if not sig_ok:
            return Verification(False, False)
        package = self._package_bytes(record.namespace, record.name, record.version)
        digest_ok = package is not None and digest_of(package) == record.digest
        return Verification(sig_ok, digest_ok)

    # 2. resolve -- walk candidates newest to oldest; refuse and continue on
    #    a failed verification; never fall back outside the constraint
    def resolve(self, query: Query) -> ResolutionOutcome:
        raw = self._all_versions(query.name)
        candidates = sorted((v for v in raw if parse_semver(v) and satisfies(v, query.constraint)),
                            key=parse_semver, reverse=True)
        if not candidates:
            problem = {"type": PROBLEM_BASE + "record-not-found",
                       **{k: v for k, v in dict(zip(("status", "title", "retryable"),
                                                     REGISTRY["record-not-found"])).items()}}
            problem["detail"] = f"no version of {query.name!r} satisfies {query.constraint!r}"
            return ResolutionOutcome(asdict(query), False, Verification(False, False), None, problem)
        last_problem = None
        for version in candidates:
            record = self._record(query.name, version)
            verification = self.verify(record)
            if verification.signature_verified and verification.digest_matched:
                self.resolutions += 1
                return ResolutionOutcome(asdict(query), True, verification, record, None)
            self.refusals += 1
            reason = ("carries no signature that verifies" if not verification.signature_verified
                      else "digest no longer matches the package tree it names")
            last_problem = render_body(
                PROBLEM_BASE + "identity-untrusted", REGISTRY["identity-untrusted"][1], 401,
                f"{query.name} {version} {reason}", False,
                {"proposed_type": PROPOSED_TYPE if not verification.signature_verified else None})
            self.refusal_log.append(last_problem)
            last_verification = verification
        return ResolutionOutcome(asdict(query), False, last_verification, None, last_problem)

    # 3. list_versions -- every published version, semver-first then by
    #    publish order for anything that did not parse (skill.json operation)
    def list_versions(self, name: str) -> list:
        raw = self._all_versions(name)
        semver_ok = sorted((v for v in raw if parse_semver(v)), key=parse_semver, reverse=True)
        rest = sorted(v for v in raw if not parse_semver(v))
        return semver_ok + rest

    # 4. describe -- the resolved record's machine-readable description
    def describe(self, name: str, version: str) -> dict:
        record = self._record(name, version)
        return {"good_at": record.good_at, "auth_schemes": record.auth_schemes,
               "kind": record.kind, "namespace": record.namespace}

    # 5. publish -- never rewrites; a change is always a new record
    def publish(self, request: PublishRequest) -> CapabilityRecord:
        name = f"{request.namespace}/{request.name}"
        if request.version in self._all_versions(name):
            self.refusals += 1
            raise Problem("document-invalid",
                          f"{name} {request.version} is already published; a change is a new "
                          f"version, never an edit to the one that is there (X-cap-capability-"
                          f"registry-007)", namespace=request.namespace, name=request.name,
                          version=request.version)
        keyid, key = self._signer(request)
        record = CapabilityRecord(request.namespace, request.name, request.version, request.kind,
                                  digest_of(request.package_bytes), "", RECORD_SCHEMA_VERSION,
                                  list(request.good_at), list(request.auth_schemes),
                                  request.acceptance_criteria_ref, request.rollback_to,
                                  self._now())
        record.signature = mac(key, canonical(record.unsigned()))
        self._append(name, request.version, record, request.package_bytes)
        return record

    # --- adapter-specific primitives: everything below is confined to a store ---
    @abstractmethod
    def _all_versions(self, name: str) -> dict:
        """name -> {version: True, ...}, every version this source knows of that name."""

    @abstractmethod
    def _record(self, name: str, version: str) -> CapabilityRecord:
        ...

    @abstractmethod
    def _package_bytes(self, namespace: str, name: str, version: str) -> bytes | None:
        """The package bytes this store holds today for that identity, or None."""

    @abstractmethod
    def _signer(self, request: PublishRequest) -> tuple:
        """(keyid, key bytes). Where the key comes from is the adapter's business."""

    @abstractmethod
    def _verifying_material(self, namespace: str, name: str) -> bytes | None:
        ...

    @abstractmethod
    def _append(self, name: str, version: str, record: CapabilityRecord, package_bytes: bytes) -> None:
        """Write the record beside the store, never in place of one that is there."""

    @abstractmethod
    def _now(self) -> str:
        ...

    def binding(self) -> dict:
        """What a report says about who answered. No caller ever reads this."""
        return {"adapter": self.adapter_kind, "entity": self.entity, "resolution": self.resolution,
               "identity_is": self.identity_is, "network_required": self.network_required,
               "trust_anchor": self.trust_anchor, "declared_gaps": list(self.declared_gaps)}

    adapter_kind = "unset"        # signed-index | registry-fetch
