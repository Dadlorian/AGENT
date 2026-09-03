#!/usr/bin/env python3
"""The state seam the dispatcher writes step records through.

Append-only and hash-chained, so a manual edit between runs is detectable and a
resume that trusts a record can tell a checkpoint from an edit (F-a5-03). Every
append returns the new head, and that head is what an output carries as
`recorded_at_head`: a result naming an output whose head is null is a result
naming something no later reader can find.

The log is the dispatcher's, not the executor's. An executor with no journal of
its own therefore satisfies the seam's resume and replay rules unchanged, which
is the whole reason the record lives here (seam-dispatch-implement step 6).

Every read re-reads the file, so a unit that ran in another process is visible
through the same handle.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os

ZERO = "sha256:" + "0" * 64


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class StepLog:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def records(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        return [json.loads(line) for line in open(self.path) if line.strip()]

    def head(self) -> str:
        recs = self.records()
        return recs[-1]["hash"] if recs else ZERO

    def append(self, **fields) -> str:
        """Write one record and return the head it produced. The fsync is what
        makes a crash in another process a real crash rather than a lost buffer."""
        recs = self.records()
        rec = {"seq": len(recs), "prev": recs[-1]["hash"] if recs else ZERO, **fields}
        rec["hash"] = "sha256:" + hashlib.sha256((rec["prev"] + canonical(rec)).encode()).hexdigest()
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return rec["hash"]

    def verify(self) -> str | None:
        prev = ZERO
        for i, rec in enumerate(self.records()):
            body = {k: v for k, v in rec.items() if k != "hash"}
            want = "sha256:" + hashlib.sha256((prev + canonical(body)).encode()).hexdigest()
            if rec["prev"] != prev or rec["hash"] != want or rec["seq"] != i:
                return f"chain broken at seq {i}"
            prev = rec["hash"]
        return None

    def by(self, **match) -> list[dict]:
        return [r for r in self.records()
                if all(r.get(k) == v for k, v in match.items())]
