#!/usr/bin/env python3
"""Dry-run adapter: log-fold-at-entry, in process, no network, no lease.

This is the first enforcing adapter cap-idempotency-implement describes (step
2): a fold over an append-only log. claim() looks for a record under this key;
found with the same payload digest, it answers duplicate (with a result only
once complete() has sealed it); found with a different digest, it raises the
typed conflict; not found, it stages a row and answers fresh. Nothing is
reserved atomically in between - no conditional write happens before execution
starts - which is the adapter-today row PASS.md B3 records for this element
(F-b3-16): "key on the wire, no lease". Declared: supports_in_flight = False,
because this adapter has no in-flight state to report, only a completed one or
none. The conformance run's race case proves the gap: without a lock around
"read, then write", two claimants racing the same key can each read "not
found" and each answer fresh.
"""
from __future__ import annotations

import os
import time

from interface import ClaimOutcome, ClaimRequest, IdempotencyAdapter, Problem


class LogFoldAdapter(IdempotencyAdapter):
    adapter_marker = "log-fold-at-entry"
    unit_of_conditionality = "log-row (fold at entry)"
    supports_in_flight = False
    processes_required_for_progress = 1

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.records: dict[str, dict] = {}          # scope|key -> record. The "log".

    def _k(self, key: str, scope: str) -> str:
        return f"{scope}|{key}"

    def claim(self, req: ClaimRequest) -> ClaimOutcome:
        k = self._k(req.idempotency_key, req.scope)
        found = self.records.get(k)                 # step 1: read
        delay = float(os.environ.get("RACE_DELAY_S", "0"))
        if delay:                                    # widens the read/write window on purpose,
            time.sleep(delay)                         # so a real race is observable, not lucky
        if found is not None:
            if found["payload_digest"] != req.payload_digest:
                raise Problem("idempotency-conflict",
                              f"key {req.idempotency_key!r} was claimed with a different payload",
                              idempotency_key=req.idempotency_key)
            return ClaimOutcome(outcome="duplicate", result_ref=found["result_ref"], in_flight=False)
        self.records[k] = {"payload_digest": req.payload_digest, "result_ref": None,   # step 2: write
                            "claimed_at": time.time(), "retention_s": req.retention_s}
        return ClaimOutcome(outcome="fresh")

    def complete(self, key: str, scope: str, result_ref: str) -> None:
        self.records[self._k(key, scope)]["result_ref"] = result_ref

    def resolve(self, key: str, scope: str) -> ClaimOutcome | None:
        found = self.records.get(self._k(key, scope))
        if found is None:
            return None
        return ClaimOutcome(outcome="duplicate", result_ref=found["result_ref"], in_flight=False)

    def expire(self, key: str, scope: str, now: float | None = None) -> bool:
        k = self._k(key, scope)
        found = self.records.get(k)
        if found is None:
            return False
        clock = now if now is not None else time.time()
        if clock - found["claimed_at"] >= found["retention_s"]:
            del self.records[k]
            return True
        return False


# The one name every adapter module exports: the entry point of this module.
Adapter = LogFoldAdapter
