#!/usr/bin/env python3
"""Second adapter: a conditional-write lease, the swap candidate PASS.md B3
names for this element - "any keyed lease store" (F-b3-16).

Different execution model from the fold: claim() takes a real compare-and-set
under a lock before execution begins, holding an in-flight state and a
monotonic fencing token; a duplicate arriving while the winner is still working
is answered mid-flight (in_flight=True), which the fold can never do. complete()
seals the row; expire() releases it after its declared retention window.

This harness's lock and dict are the faithful stub the author brief allows: the
compare-and-set, the fencing token and the in-flight answer are real and pass
the same conformance suite as any external keyed store would. A production
binding swaps the dict for Redis SETNX, a Postgres UPSERT ... ON CONFLICT, or
any other store offering a keyed conditional write (F-b3-16); the shape here
does not change when that swap happens; product names are deliberately absent
because the row itself never names one.
"""
from __future__ import annotations

import threading
import time

from interface import ClaimOutcome, ClaimRequest, IdempotencyAdapter, Problem


class ConditionalWriteLeaseAdapter(IdempotencyAdapter):
    adapter_marker = "conditional-write-lease"
    unit_of_conditionality = "keyed-compare-and-set"
    supports_in_flight = True
    processes_required_for_progress = 1     # in-process stub; a networked store needs 0 of this process

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self._lock = threading.Lock()
        self._leases: dict[str, dict] = {}
        self._fence = 0

    def _k(self, key: str, scope: str) -> str:
        return f"{scope}|{key}"

    def claim(self, req: ClaimRequest) -> ClaimOutcome:
        k = self._k(req.idempotency_key, req.scope)
        with self._lock:                                     # the conditional write: atomic
            row = self._leases.get(k)
            if row is None:
                self._fence += 1
                self._leases[k] = {"payload_digest": req.payload_digest, "state": "in_flight",
                                   "result_ref": None, "fencing_token": self._fence,
                                   "claimed_at": time.time(), "retention_s": req.retention_s}
                return ClaimOutcome(outcome="fresh", fencing_token=self._fence)
            if row["payload_digest"] != req.payload_digest:
                raise Problem("idempotency-conflict",
                              f"key {req.idempotency_key!r} is leased under a different payload",
                              idempotency_key=req.idempotency_key)
            return ClaimOutcome(outcome="duplicate", result_ref=row["result_ref"],
                                in_flight=(row["state"] == "in_flight"), fencing_token=row["fencing_token"])

    def complete(self, key: str, scope: str, result_ref: str) -> None:
        with self._lock:
            row = self._leases[self._k(key, scope)]
            row["state"], row["result_ref"] = "sealed", result_ref

    def resolve(self, key: str, scope: str) -> ClaimOutcome | None:
        with self._lock:
            row = self._leases.get(self._k(key, scope))
            if row is None:
                return None
            return ClaimOutcome(outcome="duplicate", result_ref=row["result_ref"],
                                in_flight=(row["state"] == "in_flight"), fencing_token=row["fencing_token"])

    def expire(self, key: str, scope: str, now: float | None = None) -> bool:
        with self._lock:
            k = self._k(key, scope)
            row = self._leases.get(k)
            if row is None:
                return False
            clock = now if now is not None else time.time()
            if clock - row["claimed_at"] < row["retention_s"]:
                return False
            del self._leases[k]
            return True


# The one name every adapter module exports: the entry point of this module.
Adapter = ConditionalWriteLeaseAdapter
