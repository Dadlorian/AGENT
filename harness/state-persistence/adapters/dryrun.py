#!/usr/bin/env python3
"""Dry-run adapter: an in-memory chained, provable log. No disk, no network.

Deterministic given the same sequence of calls: record ids are content
addresses, chain digests fold the previous digest, and the tree is the same
merkle math interface.py defines. Execution model: single mutable structure
held by this process, order is call order - the axis the second adapter (an
object store with a compare-and-swap head) deliberately breaks.
"""
from __future__ import annotations

import datetime
import os

from interface import (AppendRequest, ConsistencyProof, Head, InclusionProof, Problem,
                       StatePersistenceAdapter, StateRecord, audit_path, canonical_bytes,
                       consistency_proof, digest_id, mth, sha256_hex, as_digest)


def _now() -> str:
    fixed = os.environ.get("STATE_CLOCK")     # a fixed clock keeps a dry run's written_at deterministic
    dt = datetime.datetime.fromisoformat(fixed) if fixed else datetime.datetime.now(datetime.timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


class DryRunAdapter(StatePersistenceAdapter):
    entity = "in-memory chained log (dry run)"
    execution_model = "single mutable structure held by this process, order is call order"
    declared_marker = "dryrun-state-store"

    def __init__(self):
        super().__init__()
        self._records: dict[str, list[StateRecord]] = {}   # partition -> ordered records
        self._by_id: dict[str, dict[str, StateRecord]] = {}

    def _append_locked(self, request: AppendRequest, head: Head) -> tuple[StateRecord, Head]:
        if os.environ.get("DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable", "the dry-run store was made unreachable by DRYRUN_FAIL=1")
        records = self._records.setdefault(request.partition, [])
        rid = digest_id({"kind": request.kind, "partition": request.partition, "body": request.body,
                         "seq": len(records)})
        chain = sha256_hex(((head.chain_digest if records else "genesis") + rid).encode())
        record = StateRecord(rid, records[-1].record_id if records else None, chain, request.kind,
                             request.partition, request.fencing_token, _now(), request.body)
        records.append(record)
        self._by_id.setdefault(request.partition, {})[rid] = record
        return record, self._head(request.partition)

    def _head(self, partition: str) -> Head:
        records = self._records.get(partition, [])
        root = as_digest(mth([r.record_id for r in records]))
        chain = records[-1].chain_digest if records else "genesis"
        return Head(partition, len(records), root, chain, None)

    def resolve_head(self, partition: str) -> Head:
        return self._head(partition)

    def read_at(self, partition: str, head: Head, selector: dict | None = None) -> list[StateRecord]:
        records = self._records.get(partition, [])[:head.size]     # the pin: never see what landed after
        if not selector:
            return list(records)
        kind = selector.get("kind")
        rid = selector.get("record_id")
        out = records
        if kind is not None:
            out = [r for r in out if r.kind == kind]
        if rid is not None:
            out = [r for r in out if r.record_id == rid]
        return out

    def prove(self, partition: str, record_id: str, head: Head) -> InclusionProof:
        records = self._records.get(partition, [])[:head.size]
        ids = [r.record_id for r in records]
        if record_id not in ids:
            raise Problem("record-unverifiable", f"{record_id} is not in partition {partition!r} at this head")
        idx = ids.index(record_id)
        path = [as_digest(h) for h in audit_path(ids, idx)]
        return InclusionProof(record_id, idx, head, path)

    def prove_consistency(self, partition: str, old_head: Head, new_head: Head) -> ConsistencyProof:
        records = self._records.get(partition, [])[:new_head.size]
        ids = [r.record_id for r in records]
        path = [as_digest(h) for h in consistency_proof(old_head.size, ids)]
        return ConsistencyProof(old_head, new_head, path)

    def redact(self, partition: str, record_id: str, authority: str) -> StateRecord:
        by_id = self._by_id.get(partition, {})
        if record_id not in by_id:
            raise Problem("record-unverifiable", f"{record_id} is not known in partition {partition!r}")
        old = by_id[record_id]
        tomb = StateRecord(old.record_id, old.prev_record_id, old.chain_digest, old.kind, old.partition,
                           old.fencing_token, old.written_at, None)
        by_id[record_id] = tomb
        records = self._records[partition]
        records[records.index(old)] = tomb    # record_id is unchanged: every prior proof still verifies
        return tomb


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunAdapter
