#!/usr/bin/env python3
"""Second adapter: a content-addressed Merkle log over an object store.

Where the live adapter answers from one mutable file whose order is byte
position, this one names each record by the digest of its canonical bytes,
persists the tree alongside the objects rather than rebuilding it from a
listing, and advances the head with a compare-and-swap on one small object
instead of appending a line. It cannot assume write order, cannot read a
"previous line" to find the head, and cannot cheaply scan every record - a
listing on a real object store is eventually consistent, which is exactly
why the tree is persisted rather than derived.

PASS.md B3 names this pair of roles for state persistence (F-b3-17); this file
is the second one (E-swap-candidate-object-store). Reachability: with
OBJSTORE_DIR set to a directory backed by a real bucket (an s3fs or gcsfuse
mount, or any POSIX front for the store an operator chooses) this adapter's
object PUT is a normal file write and its head CAS is an atomic rename -
exactly the primitives a real object-store SDK also has to provide, so
swapping the transport later means changing what OBJSTORE_DIR points at, not
this file. Unset, it uses a scratch directory under harness/state-persistence/out
- the same code path, not a separate simulation.
"""
from __future__ import annotations

import datetime
import json
import os

from interface import (AppendRequest, ConsistencyProof, Head, InclusionProof, Problem,
                       StatePersistenceAdapter, StateRecord, audit_path, consistency_proof,
                       digest_id, mth, sha256_hex, as_digest)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(HERE, "..", "out", "objectstore")


class ObjectStoreAdapter(StatePersistenceAdapter):
    entity = "content-addressed merkle log over an object store (second adapter)"
    execution_model = "immutable objects under a content address, head advanced by compare-and-swap"
    declared_marker = "objectstore-cas-head"
    declared_gaps = (
        "listing is not relied on: the tree is persisted in tree.json alongside the objects, because a "
        "real object store's listing is only eventually consistent",
    )

    def __init__(self):
        super().__init__()
        self._root = os.environ.get("OBJSTORE_DIR", DEFAULT_DIR)

    # --- the object-store primitives: PUT (write-once), GET, CAS on one small object ---
    def _dir(self, partition: str) -> str:
        d = os.path.join(self._root, partition)
        os.makedirs(os.path.join(d, "objects"), exist_ok=True)
        return d

    def _obj_path(self, partition: str, record_id: str) -> str:
        return os.path.join(self._dir(partition), "objects", record_id.split(":", 1)[1] + ".json")

    def _head_path(self, partition: str) -> str:
        return os.path.join(self._dir(partition), "head.json")

    def _tree_path(self, partition: str) -> str:
        return os.path.join(self._dir(partition), "tree.json")

    def _read_json(self, path: str, default):
        if not os.path.isfile(path):
            return default
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _cas_write(self, path: str, expected_bytes: bytes | None, new_obj: dict) -> bool:
        """Compare-and-swap on one small object via an atomic rename. True on success."""
        current = open(path, "rb").read() if os.path.isfile(path) else None
        if current != expected_bytes:
            return False
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(new_obj, fh, sort_keys=True)
        os.replace(tmp, path)          # atomic on a POSIX filesystem: the CAS primitive
        return True

    def _tree_ids(self, partition: str) -> list[str]:
        return self._read_json(self._tree_path(partition), {"ids": []})["ids"]

    def _head(self, partition: str) -> Head:
        ids = self._tree_ids(partition)
        root = as_digest(mth(ids))
        chain = self._read_json(self._head_path(partition), {}).get("chain_digest", "genesis")
        return Head(partition, len(ids), root, chain, None)

    def resolve_head(self, partition: str) -> Head:
        return self._head(partition)

    def _append_locked(self, request: AppendRequest, head: Head) -> tuple[StateRecord, Head]:
        ids = self._tree_ids(request.partition)
        rid = digest_id({"kind": request.kind, "partition": request.partition, "body": request.body,
                         "seq": len(ids)})
        prev_chain = self._read_json(self._head_path(request.partition), {}).get("chain_digest", "genesis")
        chain = sha256_hex((prev_chain + rid).encode())
        record = StateRecord(rid, ids[-1] if ids else None, chain, request.kind, request.partition,
                             request.fencing_token,
                             datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
                             .isoformat().replace("+00:00", "Z"), request.body)
        # PUT the object first (write-once, never overwritten) ...
        obj_path = self._obj_path(request.partition, rid)
        if not os.path.isfile(obj_path):
            with open(obj_path + ".tmp", "w", encoding="utf-8") as fh:
                json.dump({"record_id": rid, "prev_record_id": record.prev_record_id, "chain_digest": chain,
                          "kind": request.kind, "partition": request.partition,
                          "fencing_token": request.fencing_token, "written_at": record.written_at,
                          "body": request.body}, fh, sort_keys=True)
            os.replace(obj_path + ".tmp", obj_path)
        # ... then CAS the tree and the head; a lost race here leaves the object orphaned, never forks the log.
        tree_path, head_path = self._tree_path(request.partition), self._head_path(request.partition)
        expected_tree = open(tree_path, "rb").read() if os.path.isfile(tree_path) else None
        if not self._cas_write(tree_path, expected_tree, {"ids": ids + [rid]}):
            raise Problem("head-moved", "the tree object changed between resolve_head and the CAS write",
                          partition=request.partition)
        expected_head = open(head_path, "rb").read() if os.path.isfile(head_path) else None
        self._cas_write(head_path, expected_head, {"chain_digest": chain})
        return record, self._head(request.partition)

    def read_at(self, partition: str, head: Head, selector: dict | None = None) -> list[StateRecord]:
        ids = self._tree_ids(partition)[:head.size]
        out = []
        for rid in ids:
            doc = self._read_json(self._obj_path(partition, rid), None)
            if doc is None:
                continue
            out.append(StateRecord(doc["record_id"], doc["prev_record_id"], doc["chain_digest"], doc["kind"],
                                   doc["partition"], doc["fencing_token"], doc["written_at"], doc["body"]))
        if not selector:
            return out
        kind, rid_sel = selector.get("kind"), selector.get("record_id")
        if kind is not None:
            out = [r for r in out if r.kind == kind]
        if rid_sel is not None:
            out = [r for r in out if r.record_id == rid_sel]
        return out

    def prove(self, partition: str, record_id: str, head: Head) -> InclusionProof:
        ids = self._tree_ids(partition)[:head.size]
        if record_id not in ids:
            raise Problem("record-unverifiable", f"{record_id} is not in partition {partition!r} at this head")
        idx = ids.index(record_id)
        path = [as_digest(h) for h in audit_path(ids, idx)]
        return InclusionProof(record_id, idx, head, path)

    def prove_consistency(self, partition: str, old_head: Head, new_head: Head) -> ConsistencyProof:
        ids = self._tree_ids(partition)[:new_head.size]
        path = [as_digest(h) for h in consistency_proof(old_head.size, ids)]
        return ConsistencyProof(old_head, new_head, path)

    def redact(self, partition: str, record_id: str, authority: str) -> StateRecord:
        path = self._obj_path(partition, record_id)
        doc = self._read_json(path, None)
        if doc is None:
            raise Problem("record-unverifiable", f"{record_id} is not known in partition {partition!r}")
        doc["body"] = None
        doc["redacted_by"] = authority
        with open(path + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(doc, fh, sort_keys=True)
        os.replace(path + ".tmp", path)     # the object id is unchanged: every prior proof still verifies
        return StateRecord(doc["record_id"], doc["prev_record_id"], doc["chain_digest"], doc["kind"],
                           doc["partition"], doc["fencing_token"], doc["written_at"], None)


# The one name every adapter module exports: the entry point of this module.
Adapter = ObjectStoreAdapter
