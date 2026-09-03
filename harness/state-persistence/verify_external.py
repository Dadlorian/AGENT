#!/usr/bin/env python3
"""An independent verifier. Does not import interface.py or any adapter.

Reads a JSON array of full records (record_id, kind, partition, body) from
stdin, in log order - the caller's own view of a partition, exactly what a
third party would hold: the records, not our code. It does two things no
adapter's own reader is trusted to do for itself:

  1. recomputes the RFC 9162 Merkle root from the record ids and reports it,
     so a conformance case can compare it against the head the adapter itself
     returned, without ever importing this project's tree-building functions.
  2. recomputes each record's content id from its kind, partition, body and
     position, and reports the first index whose stored id does not match -
     "chain_break_at". The tree above only proves a claimed id's position;
     this is the separate check that the bytes still match the id they claim.

    python3 verify_external.py < records.json
    {"count": N, "root_hash": "sha256:...", "chain_break_at": -1}
"""
from __future__ import annotations

import hashlib
import json
import sys

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def content_id(kind: str, partition: str, body, seq: int) -> str:
    digest = hashlib.sha256(canonical_bytes({"kind": kind, "partition": partition, "body": body,
                                             "seq": seq})).hexdigest()
    return "sha256:" + digest


def leaf_hash(record_id: str) -> bytes:
    return hashlib.sha256(LEAF_PREFIX + record_id.encode("utf-8")).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(NODE_PREFIX + left + right).digest()


def split_point(n: int) -> int:
    k = 1
    while k < n:
        k *= 2
    return k // 2


def merkle_root(record_ids: list[str]) -> bytes:
    n = len(record_ids)
    if n == 0:
        return hashlib.sha256(b"").digest()
    if n == 1:
        return leaf_hash(record_ids[0])
    k = split_point(n)
    return node_hash(merkle_root(record_ids[:k]), merkle_root(record_ids[k:]))


def main() -> int:
    docs = json.loads(sys.stdin.read() or "[]")
    ids = [d["record_id"] for d in docs]
    root = merkle_root(ids)
    chain_break_at = -1
    for i, d in enumerate(docs):
        if d.get("body") is None:            # a tombstone: content is gone by design, not by tampering
            continue
        if content_id(d["kind"], d["partition"], d["body"], i) != d["record_id"]:
            chain_break_at = i
            break
    print(json.dumps({"count": len(ids), "root_hash": "sha256:" + root.hex(), "chain_break_at": chain_break_at}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
