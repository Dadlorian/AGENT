#!/usr/bin/env python3
"""The two durable files this harness uses, and no register logic.

`ChainedLog` is an append-only, hash-chained file: each record's hash covers the
previous hash, so an edit between processes is detectable. It is the store the
two registers keep their records in - one keeps a per-run journal in it, the
other keeps the platform's own log in it - and it is where a "head" comes from.
Every append is flushed and fsynced before it returns, so an abandoned run is
abandoned on disk, not in a buffer.

`EffectTable` is the world: the side effects a run committed and the
compensations that undid them, appended by the driver and counted by someone
else. Nothing in a run reports its own effect count - an effect a run tallies
for itself cannot show the run double-counting it (harness/workflow, F-a7-03).
Compensations are appended forward, in the table's own vocabulary: a
compensation is another row that moves the entity onward, never a deletion of
the row it undoes (xc-compensation best practice 3, X-xc-compensation-003).

This is a file format, not a component: no product is named here.
"""
from __future__ import annotations

import hashlib
import json
import os

ZERO = "sha256:" + "0" * 64


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class ChainedLog:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._stamp: tuple[int, int] | None = None
        self.records: list[dict] = []
        self.refresh()

    def _file_stamp(self) -> tuple[int, int] | None:
        try:
            st = os.stat(self.path)
        except FileNotFoundError:
            return None
        return (st.st_size, st.st_mtime_ns)

    def refresh(self) -> None:
        """Re-read when the file has moved on. The file is the store, not this
        object's memory: a run abandoned in another process is read back through
        the same handle."""
        stamp = self._file_stamp()
        if stamp != self._stamp:
            self.records = self._load()
            self._stamp = stamp

    def _load(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def head(self) -> str:
        self.refresh()
        return self.records[-1]["hash"] if self.records else ZERO

    def ordinal(self, head: str) -> int:
        """Where a head stands in this log's order. ZERO is -1, so the head
        before the first append is strictly earlier than every record."""
        self.refresh()
        if head == ZERO:
            return -1
        for rec in self.records:
            if rec["hash"] == head:
                return rec["seq"]
        return -2                                   # not this log's head at all

    def append(self, **fields) -> dict:
        self.refresh()
        rec = {"seq": len(self.records), "prev": self.head(), **fields}
        rec["hash"] = "sha256:" + hashlib.sha256(
            (rec["prev"] + canonical(rec)).encode()).hexdigest()
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self.records.append(rec)
        self._stamp = self._file_stamp()
        return rec

    def verify(self) -> str | None:
        self.refresh()
        prev = ZERO
        for i, rec in enumerate(self.records):
            body = {k: v for k, v in rec.items() if k != "hash"}
            want = "sha256:" + hashlib.sha256((prev + canonical(body)).encode()).hexdigest()
            if rec["seq"] != i or rec["prev"] != prev or rec["hash"] != want:
                return f"chain broken at seq {i}"
            prev = rec["hash"]
        return None

    def of(self, run_id: str, kind: str | None = None) -> list[dict]:
        self.refresh()
        return [r for r in self.records
                if r.get("run_id") == run_id and (kind is None or r.get("kind") == kind)]


class EffectTable:
    """The world, counted from outside every register."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def rows(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def has_key(self, key: str) -> bool:
        return any(r.get("key") == key for r in self.rows())

    def append(self, kind: str, key: str, **payload) -> dict:
        row = {"kind": kind, "key": key, **payload}
        with open(self.path, "a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return row

    def ensure(self, kind: str, key: str, **payload) -> dict | None:
        """Append unless this key is already on the table. A compensating action
        has its own key, so an unwind that is retried does not undo twice."""
        if self.has_key(key):
            return None
        return self.append(kind, key, **payload)

    # -- reads a checker makes ----------------------------------------------
    def forward(self, run_id: str | None = None) -> list[dict]:
        return [r for r in self.rows() if r["kind"] == "effect"
                and (run_id is None or r.get("run_id") == run_id)]

    def compensations(self, run_id: str | None = None) -> list[dict]:
        return [r for r in self.rows() if r["kind"] == "compensation"
                and (run_id is None or r.get("run_id") == run_id)]

    def net(self, entity: str) -> int:
        """The entity's balance after every forward row and every compensating
        row. Zero is what "the effect was reversed" looks like from outside."""
        return sum(r.get("delta", 0) for r in self.rows() if r.get("entity") == entity)
