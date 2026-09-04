#!/usr/bin/env python3
"""Closure C15-F check: a real lease over a key, not a key alone on the wire.

Runs the two properties the closure's mechanism names, against the
conditional-write lease adapter (`adapters/second.py`) that already
implements them:

  1. race_case      - two concurrent claim()s of the same key against the
                       same adapter instance: exactly one is answered fresh
                       (performs the side effect); the other is rejected,
                       answered duplicate, not also allowed to proceed.
  2. crash_recovery_case - claim() without ever calling complete() (the
                       process crashes mid-write): a retry against the
                       still-live lease is rejected outright (duplicate,
                       in_flight); only once the lease's TTL has lapsed
                       (expire() past retention_s) does a retry answer fresh
                       again.

This is the property PASS.md B3 (F-b3-16) records as missing from today's
adapter ("key on the wire, no lease") and cap-idempotency's lease semantics
name as the fix: claim and write atomic, the claim itself a time-bounded
lease. adapters/dryrun.py and adapters/live.py fail this check by
construction (no lock, no lease) - that is their declared gap, not a bug in
this script. adapters/second.py is the adapter that must pass it.

    python3 harness/idempotency/lease_check.py

Exit 0 when both properties hold; exit 1 (with the failing assertion
printed) otherwise - including when the lease's own lock is removed, which
is this check's deliberate breakage (same anchor `test.sh` section 3
patches in `adapters/second.py`).
"""
from __future__ import annotations

import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import ClaimRequest, digest                # noqa: E402
from adapters.second import ConditionalWriteLeaseAdapter  # noqa: E402

SCOPE = "harness/idempotency:lease-check"


def mkreq(key: str, payload: dict, retention_s: int = 60) -> ClaimRequest:
    return ClaimRequest.for_payload(key, payload, SCOPE, correlation_id="corr-" + key,
                                     actor="user:corey", entry_kind="human", retention_s=retention_s)


def race_case(adapter: ConditionalWriteLeaseAdapter) -> str:
    """Two concurrent claims, same key, same handler: exactly one performs
    the side effect; the other is rejected rather than also proceeding."""
    req = mkreq("race-key", {"amount": 11})
    barrier = threading.Barrier(2)
    results: list[str] = []
    lock = threading.Lock()

    def worker() -> None:
        barrier.wait()                                     # both claim() calls land together
        out = adapter.claim(req)
        if out.outcome == "fresh":
            time.sleep(0.05)                                # hold the lease open so the loser's
            adapter.complete(req.idempotency_key, req.scope, digest({"charged": True}))  # claim lands inside the live window
        with lock:
            results.append(out.outcome)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    fresh = results.count("fresh")
    assert fresh == 1, f"expected exactly one fresh claim, got {fresh} of {results}"
    assert "duplicate" in results, f"the second claim was not rejected/duplicate: {results}"
    return f"outcomes={results}"


def crash_recovery_case(adapter: ConditionalWriteLeaseAdapter) -> str:
    """Claim, then crash before complete(): a retry against the still-live
    lease is rejected outright; only once the TTL has lapsed does a retry
    proceed."""
    key = "crash-key"
    req = mkreq(key, {"amount": 5}, retention_s=60)
    t0 = time.time()

    first = adapter.claim(req)
    assert first.outcome == "fresh", f"first claim should start the operation, got {first.outcome}"
    # The process dies here: complete() is never called. The lease is left in flight.

    retry_live = adapter.claim(req)
    assert retry_live.outcome != "fresh", \
        "a retry against a still-live lease was allowed to proceed - the crash was not held"
    assert retry_live.outcome == "duplicate" and retry_live.in_flight, \
        f"expected an in-flight duplicate while the lease is live, got {retry_live}"

    still_live = adapter.expire(key, req.scope, now=t0 + 30)
    assert still_live is False, "the lease released before its TTL elapsed"

    released = adapter.expire(key, req.scope, now=t0 + 61)
    assert released is True, "the lease was not released once its TTL elapsed"

    retry_after_ttl = adapter.claim(req)
    assert retry_after_ttl.outcome == "fresh", \
        f"a retry after the lease's TTL lapsed was still refused: {retry_after_ttl.outcome}"

    return "rejected while live, released at TTL, fresh on retry"


def main() -> int:
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "lease-check")
    passed = True
    for name, case in (("race", race_case), ("crash-recovery", crash_recovery_case)):
        adapter = ConditionalWriteLeaseAdapter(out_dir)
        try:
            print(f"  ok   {name}: {case(adapter)}")
        except AssertionError as exc:
            print(f"  FAIL {name}: {exc}")
            passed = False
    print("lease_check " + ("PASSED" if passed else "FAILED"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
