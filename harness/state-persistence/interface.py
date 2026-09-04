#!/usr/bin/env python3
"""State persistence: one opaque record, appended under a head, provable without the log.

Read it in this order. AppendRequest is the whole caller vocabulary for a write;
a selector plus a Head is the whole vocabulary for a read. The merkle_* functions
are pure - a tree built and audited from nothing but SHA-256, testable from a
table with no store running, exactly as route() is tested in harness/gateway.
StatePersistenceAdapter.append() is a template method: it checks the expected
head and the fencing token before any adapter code runs, so two writers racing
for the same partition are refused identically whichever adapter is bound.

Tree hashing follows RFC 9162 (leaf/node domain separation, MTH, PATH, PROOF);
record identity follows RFC 8785 in spirit (canonical JSON: sorted keys, no
insignificant whitespace) rather than the full JCS number-formatting rules,
since every field this harness hashes is a string, an int or a nested object of
those (F-b5-05, X-xc-provenance-chain-006; both RFCs unverified here - search
results, never fetched).

No product name, bucket, path or database appears in this file (T-t7-02).
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

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) -----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "Request is not a well-formed state record", False),
    "head-moved": (409, "Another writer advanced the head first", True),
    "record-unverifiable": (422, "The proof does not check out against the head supplied", False),
    "adapter-unavailable": (503, "This binding cannot serve the operation", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --- Canonical bytes and content addressing (RFC 8785 in spirit) ------------
def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest_id(obj) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def as_digest(raw: bytes) -> str:
    """Hex-encodes bytes that are ALREADY a digest (an mth() root, a path sibling).

    Never re-hash these - sha256_hex(mth(ids)) would hash the root a second
    time and every proof built from it would fail to verify.
    """
    return "sha256:" + raw.hex()


# --- Merkle tree math (RFC 9162 MTH / PATH / PROOF) --------------------------
# Pure functions. No adapter state, no clock, no store. A conformance case
# round-trips these over random tree sizes with no store running at all.
LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def _leaf_hash(record_id: str) -> bytes:
    return hashlib.sha256(LEAF_PREFIX + record_id.encode("utf-8")).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(NODE_PREFIX + left + right).digest()


def _split_point(n: int) -> int:
    """The largest power of two strictly less than n (RFC 9162 section 2.1)."""
    k = 1
    while k < n:
        k *= 2
    return k // 2


def mth(record_ids: list[str]) -> bytes:
    """MTH(D_n): the root hash over an ordered sequence of record ids."""
    n = len(record_ids)
    if n == 0:
        return hashlib.sha256(b"").digest()          # MTH({}) is the hash of the empty string
    if n == 1:
        return _leaf_hash(record_ids[0])
    k = _split_point(n)
    return _node_hash(mth(record_ids[:k]), mth(record_ids[k:]))


def audit_path(record_ids: list[str], m: int) -> list[bytes]:
    """PATH(m, D_n): the inclusion proof for the leaf at index m."""
    n = len(record_ids)
    if n <= 1:
        return []
    k = _split_point(n)
    if m < k:
        return audit_path(record_ids[:k], m) + [mth(record_ids[k:])]
    return audit_path(record_ids[k:], m - k) + [mth(record_ids[:k])]


def root_from_inclusion_proof(leaf_index: int, tree_size: int, record_id: str, path: list[bytes]) -> bytes:
    """Reconstructs the root from a leaf and its path alone - no other record is read."""
    if not (0 <= leaf_index < tree_size):
        raise Problem("record-unverifiable", f"leaf_index {leaf_index} is out of range for tree_size {tree_size}")
    fn, sn = leaf_index, tree_size - 1
    r = _leaf_hash(record_id)
    for h in path:
        if fn == sn or (fn & 1):
            r = _node_hash(h, r)
            while not (fn & 1) and fn != 0:
                fn >>= 1
                sn >>= 1
        else:
            r = _node_hash(r, h)
        fn >>= 1
        sn >>= 1
    if sn != 0:
        raise Problem("record-unverifiable", "the inclusion path is shorter than the tree requires")
    return r


def _sub_proof(m: int, record_ids: list[str], complete: bool) -> list[bytes]:
    n = len(record_ids)
    if m == n:
        return [] if complete else [mth(record_ids)]
    k = _split_point(n)
    if m <= k:
        return _sub_proof(m, record_ids[:k], complete) + [mth(record_ids[k:])]
    return _sub_proof(m - k, record_ids[k:], False) + [mth(record_ids[:k])]


def consistency_proof(m: int, record_ids: list[str]) -> list[bytes]:
    """PROOF(m, D_n): that the tree of size len(record_ids) extends the one of size m."""
    if m == 0 or m == len(record_ids):
        return []
    return _sub_proof(m, record_ids, True)


def verify_consistency(m: int, n: int, proof: list[bytes], old_root: bytes, new_root: bytes) -> bool:
    """True iff the log of size n extends the log of size m with nothing removed or reordered."""
    if m == 0:
        return True
    if m == n:
        return not proof and old_root == new_root
    fn, sn = m - 1, n - 1
    while fn & 1:
        fn >>= 1
        sn >>= 1
    p = list(proof)
    if fn:
        if not p:
            return False
        node0 = node1 = p.pop(0)
    else:
        node0 = node1 = old_root
    for h in p:
        if sn == 0:
            return False
        if (fn & 1) or fn == sn:
            node0 = _node_hash(h, node0)
            node1 = _node_hash(h, node1)
            while not (fn & 1) and fn != 0:
                fn >>= 1
                sn >>= 1
        else:
            node1 = _node_hash(node1, h)
        fn >>= 1
        sn >>= 1
    return node0 == old_root and node1 == new_root and sn == 0


# --- The caller vocabulary --------------------------------------------------
ALLOWED = {"partition", "kind", "body", "expected_head", "fencing_token"}
REQUIRED = {"partition", "kind", "body", "fencing_token"}


@dataclass(frozen=True)
class AppendRequest:
    partition: str
    kind: str
    body: dict
    fencing_token: int
    expected_head: str | None = None   # the chain_digest the writer believes is current; None means "empty"

    @classmethod
    def from_dict(cls, doc: dict) -> "AppendRequest":
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "an append request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid", f"fields {extra} are not in the append vocabulary", rejected_fields=extra)
        missing = sorted(REQUIRED - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        if not isinstance(doc["partition"], str) or not doc["partition"]:
            raise Problem("document-invalid", "partition must be a non-empty string")
        if not isinstance(doc["kind"], str) or not doc["kind"]:
            raise Problem("document-invalid", "kind must be a non-empty string; this interface never interprets it")
        if not isinstance(doc["body"], dict):
            raise Problem("document-invalid", "body must be an object; the store never inspects its fields")
        token = doc["fencing_token"]
        if not isinstance(token, int) or isinstance(token, bool) or token < 0:
            raise Problem("document-invalid", "fencing_token must be a non-negative integer")
        return cls(doc["partition"], doc["kind"], doc["body"], token, doc.get("expected_head"))


@dataclass(frozen=True)
class StateRecord:
    """The full record. record_id and chain_digest fold nothing but what a
    third party could recompute from the bytes stored; nothing here is generated
    by a binding's own storage layout."""
    record_id: str
    prev_record_id: str | None
    chain_digest: str
    kind: str
    partition: str
    fencing_token: int
    written_at: str
    body: dict | None            # None only for a tombstone


@dataclass(frozen=True)
class Head:
    partition: str
    size: int
    root_hash: str
    chain_digest: str
    sealed_at: str | None = None


@dataclass(frozen=True)
class InclusionProof:
    record_id: str
    leaf_index: int
    head: Head
    path: list       # list[str] of "sha256:..." sibling digests, leaf to root


@dataclass(frozen=True)
class ConsistencyProof:
    old_head: Head
    new_head: Head
    path: list


def record_as_dict(record: StateRecord) -> dict:
    return {k: v for k, v in asdict(record).items() if v is not None}


def proof_as_dict(proof) -> dict:
    doc = asdict(proof)
    return doc


# --- The interface the core imports -----------------------------------------
class StatePersistenceAdapter(ABC):
    """append, resolve_head, read_at, prove, prove_consistency, redact.

    append is concrete here so that no adapter can decline the expected-head
    check or the fencing check: two writers racing for one partition are
    refused identically whichever adapter answers.
    """

    entity = "adapter"
    execution_model = "single mutable file, order is byte order"  # what makes the swap real, not cosmetic
    declared_marker = "unset"
    declared_gaps: tuple = ()

    def __init__(self):
        self.appends = 0
        self.refusals = 0
        self.observed_marker = ""
        self._max_token: dict[str, int] = {}   # partition -> highest fencing token accepted

    # 1. append -- concrete: enforces the race check before any adapter code runs
    def append(self, request: AppendRequest) -> tuple[StateRecord, Head]:
        head = self.resolve_head(request.partition)
        current = head.chain_digest if head.size else None
        if request.expected_head != current:
            self.refusals += 1
            raise Problem("head-moved",
                          f"expected head {request.expected_head!r} but the current head of partition "
                          f"{request.partition!r} is {current!r}; the append was not applied",
                          partition=request.partition, expected_head=request.expected_head, current_head=current)
        seen = self._max_token.get(request.partition, -1)
        if request.fencing_token <= seen:
            self.refusals += 1
            raise Problem("head-moved",
                          f"fencing token {request.fencing_token} is not after the last accepted token {seen} "
                          f"for partition {request.partition!r}; a delayed writer was refused",
                          partition=request.partition, fencing_token=request.fencing_token, last_token=seen)
        record, new_head = self._append_locked(request, head)
        self._max_token[request.partition] = request.fencing_token
        self.appends += 1
        self.observed_marker = self.declared_marker
        return record, new_head

    @abstractmethod
    def _append_locked(self, request: AppendRequest, head: Head) -> tuple[StateRecord, Head]:
        """Adapter-specific write. Reached only after the head and the token have held."""

    # 2. resolve_head -- the only call allowed to be non-deterministic
    @abstractmethod
    def resolve_head(self, partition: str) -> Head:
        ...

    # 3. read_at -- deterministic at a pinned head, whatever was appended since
    @abstractmethod
    def read_at(self, partition: str, head: Head, selector: dict | None = None) -> list[StateRecord]:
        ...

    # 4. prove -- checkable from the record, the proof and the head alone
    @abstractmethod
    def prove(self, partition: str, record_id: str, head: Head) -> InclusionProof:
        ...

    # 5. prove_consistency -- the later log extends the earlier one
    @abstractmethod
    def prove_consistency(self, partition: str, old_head: Head, new_head: Head) -> ConsistencyProof:
        ...

    # 6. redact -- a tombstone, never a delete; every prior proof still verifies
    @abstractmethod
    def redact(self, partition: str, record_id: str, authority: str) -> StateRecord:
        ...


def verify_inclusion_proof(proof: InclusionProof) -> bool:
    """What a party holding only the record, the proof and the head can run."""
    root = bytes.fromhex(proof.head.root_hash.split(":", 1)[1])
    try:
        got = root_from_inclusion_proof(proof.leaf_index, proof.head.size, proof.record_id,
                                        [bytes.fromhex(p.split(":", 1)[1]) for p in proof.path])
    except Problem:
        return False
    return got == root
