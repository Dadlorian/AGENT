#!/usr/bin/env python3
"""The durable store the two in-process executors share: an append-only,
hash-chained journal, and an external effect table that someone else counts.

This is a file format, not a component: no product is named here. Every append
is flushed and fsynced before it returns, which is what makes `kill -9` in
flow.py a real crash rather than a lost buffer.
"""
from __future__ import annotations

import hashlib
import json
import os

ZERO = "sha256:" + "0" * 64


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class Journal:
    """Append-only and chained: each record's hash covers the previous hash, so
    an edit between processes is detectable (the same idea as the task store)."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.records = self._load()

    def _load(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def head(self) -> str:
        return self.records[-1]["hash"] if self.records else ZERO

    def append(self, **fields) -> dict:
        rec = {"seq": len(self.records), "prev": self.head(), **fields}
        rec["hash"] = "sha256:" + hashlib.sha256(
            (rec["prev"] + canonical(rec)).encode()).hexdigest()
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self.records.append(rec)
        return rec

    def verify(self) -> str | None:
        prev = ZERO
        for i, rec in enumerate(self.records):
            body = {k: v for k, v in rec.items() if k != "hash"}
            want = "sha256:" + hashlib.sha256((prev + canonical(body)).encode()).hexdigest()
            if rec["seq"] != i or rec["prev"] != prev or rec["hash"] != want:
                return f"chain broken at seq {i}"
            prev = rec["hash"]
        return None

    def of(self, run_key: str, kind: str | None = None) -> list[dict]:
        return [r for r in self.records
                if r.get("run_key") == run_key and (kind is None or r.get("kind") == kind)]

    def tail(self, run_key: str, kind: str) -> dict | None:
        rows = self.of(run_key, kind)
        return rows[-1] if rows else None


class EffectTable:
    """The side effect the conformance run counts from outside. Nothing in a run
    reports its own effect count: an effect a run tallies for itself cannot show
    the run double-counting it."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def rows(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def has(self, key: str | None) -> bool:
        # A step with no idempotency key cannot be recognised on a retry. That is
        # the whole point of the deliberate breakage, so it is not defended here.
        return bool(key) and any(r.get("key") == key for r in self.rows())

    def append(self, key: str | None, payload: dict) -> dict:
        row = {"key": key, **payload}
        with open(self.path, "a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return row

    def ensure(self, key: str | None, payload: dict) -> dict | None:
        """Append unless this key is already on the table. Used by an executor
        that projects its committed effects, so recovery is idempotent."""
        if self.has(key):
            return None
        return self.append(key, payload)

    def count_for(self, step_id: str) -> int:
        return sum(1 for r in self.rows() if r.get("step_id") == step_id)

    def orphans(self, committed_keys: set[str]) -> int:
        """Effect rows whose step never committed: the window a keyed-effect
        executor declares it has, and a same-transaction executor declares it
        does not."""
        return sum(1 for r in self.rows() if r.get("key") not in committed_keys)
