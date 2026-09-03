#!/usr/bin/env python3
"""Live adapter: the log-fold-at-entry mechanism running on this host today.

PASS.md B3 records the adapter today for this element as "key on the wire, no
lease" (F-b3-16): no third-party product runs it. What is real is the
append-only, hash-chained log the core already writes and folds at entry -
the same mechanism examples/end-to-end/run.py's Ledger and
harness/linked/linked.py's Ledger implement, and the same file this harness's
dry run keeps only in memory. This adapter is that mechanism against a real
file on disk, reached only through IDEMPOTENCY_LEDGER_PATH (see README.md) -
never a hard-coded path, so a caller pointed at a different host's ledger
changes one environment variable and nothing else. This adapter only appends;
point it at a copy of a ledger, never at another harness's live file, unless
you mean to add real records to it.

No product name appears here because none runs this today; that absence is
itself the row PASS.md B3 records. Standard library only.
"""
from __future__ import annotations

import json
import os
import time

from interface import ClaimOutcome, ClaimRequest, IdempotencyAdapter, Problem, digest


class LedgerFileAdapter(IdempotencyAdapter):
    adapter_marker = "log-fold-at-entry-on-disk"
    unit_of_conditionality = "log-row (fold at entry, hash-chained file)"
    supports_in_flight = False
    processes_required_for_progress = 1

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.path = os.environ.get("IDEMPOTENCY_LEDGER_PATH")
        if not self.path:
            raise Problem("adapter-unavailable",
                          "IDEMPOTENCY_LEDGER_PATH is not set; the on-disk ledger cannot be "
                          "reached and no claim was made", retry_after_s=1)
        if not os.path.exists(self.path):
            raise Problem("adapter-unavailable",
                          f"{self.path} does not exist; point IDEMPOTENCY_LEDGER_PATH at a "
                          "ledger this platform has already written", retry_after_s=1)
        self._load()

    def _load(self) -> None:
        self.records = [json.loads(l) for l in open(self.path) if l.strip()]

    def _head(self) -> str:
        return self.records[-1]["hash"] if self.records else "sha256:" + "0" * 64

    def _append(self, **fields) -> dict:
        rec = {"seq": len(self.records), "prev": self._head(), **fields}
        rec["hash"] = digest([rec["prev"], rec])
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        self.records.append(rec)
        return rec

    def _state(self, key: str, scope: str) -> dict | None:
        """Fold the log forward for this key: the row a fresh reader of the
        file would land on, claimed/completed/expired applied in order."""
        row = None
        for r in self.records:
            if r.get("scope") != scope or r.get("idempotency_key") != key:
                continue
            if r["kind"] == "idempotency-claimed":
                row = dict(r)
            elif r["kind"] == "idempotency-completed" and row is not None:
                row["result_ref"] = r["result_ref"]
            elif r["kind"] == "idempotency-expired":
                row = None
        return row

    def claim(self, req: ClaimRequest) -> ClaimOutcome:
        found = self._state(req.idempotency_key, req.scope)
        if found is not None:
            if found["payload_digest"] != req.payload_digest:
                raise Problem("idempotency-conflict",
                              f"key {req.idempotency_key!r} was claimed on {self.path} with a "
                              "different payload", idempotency_key=req.idempotency_key)
            return ClaimOutcome(outcome="duplicate", result_ref=found.get("result_ref"), in_flight=False)
        self._append(kind="idempotency-claimed", idempotency_key=req.idempotency_key,
                     scope=req.scope, payload_digest=req.payload_digest, result_ref=None,
                     claimed_at=time.time(), retention_s=req.retention_s,
                     correlation_id=req.correlation_id, actor=req.actor, entry_kind=req.entry_kind)
        return ClaimOutcome(outcome="fresh")

    def complete(self, key: str, scope: str, result_ref: str) -> None:
        self._append(kind="idempotency-completed", idempotency_key=key, scope=scope,
                     result_ref=result_ref)

    def resolve(self, key: str, scope: str) -> ClaimOutcome | None:
        found = self._state(key, scope)
        if found is None or found.get("result_ref") is None:
            return None
        return ClaimOutcome(outcome="duplicate", result_ref=found["result_ref"], in_flight=False)

    def expire(self, key: str, scope: str, now: float | None = None) -> bool:
        found = self._state(key, scope)
        if found is None:
            return False
        clock = now if now is not None else time.time()
        if clock - found["claimed_at"] < found["retention_s"]:
            return False
        self._append(kind="idempotency-expired", idempotency_key=key, scope=scope)
        return True


# The one name every adapter module exports: the entry point of this module.
Adapter = LedgerFileAdapter
