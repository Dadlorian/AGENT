#!/usr/bin/env python3
"""Runnable check for concern-identity-q5: withdrawal mid-run.

closures.json's check: "a test withdraws an identity mid-run and asserts the
next capability call under it returns a typed refusal naming that identity,
and that a single audit record shows both the withdrawal and the run's stop
point." This is that test.

    python3 harness/identity/withdrawal_check.py                    # exit 0: the property holds
    WITHDRAWAL_BREAK=1 python3 harness/identity/withdrawal_check.py  # exit 1: deliberate breakage

WITHDRAWAL_BREAK=1 clears the registry `authorise()` re-checks on every call,
standing in for a build that recorded the withdrawal but only enforced it at
session start (the shape this closure's direction abandons) rather than on the
next capability call the running unit makes. Restore by unsetting the var; the
adapter that runs it is a fresh in-process instance either way, so nothing
outside this process is left in the broken state.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import AttestRequest, Problem  # noqa: E402
from adapters.dryrun import ExchangeIssuingAdapter  # noqa: E402

WITHDRAWN_SUBJECT = "agent:worker-9"
WITHDRAWN_BY = "user:corey"


def main() -> int:
    adapter = ExchangeIssuingAdapter()
    adapter.current_action = "action-withdrawal-001"

    # A unit of work obtains its own identity and is already running under it.
    worker = adapter.attest(AttestRequest.from_dict({
        "unit": WITHDRAWN_SUBJECT, "audience": "svc:model-gateway", "scope": ["call:model"],
        "lifetime_s": 900,
        "presented": adapter.fixture_presented(WITHDRAWN_SUBJECT, ["call:model"],
                                                "svc:model-gateway", 900),
    }))

    # One capability call succeeds under this identity before anything is withdrawn.
    assert adapter.authorise(worker, "call:model") == WITHDRAWN_SUBJECT, \
        "the identity could not make its first call; the scenario proves nothing"

    # The identity is withdrawn mid-run. No signal reaches the unit above.
    withdrawal = adapter.withdraw(WITHDRAWN_SUBJECT, withdrawn_by=WITHDRAWN_BY,
                                  reason="incident-response")

    if os.environ.get("WITHDRAWAL_BREAK") == "1":
        # Deliberate breakage: the withdrawal was recorded but nothing consults
        # it on the next call, i.e. session-length trust instead of per-request.
        adapter._withdrawn.clear()

    hops_before = len(adapter.hops)
    try:
        adapter.authorise(worker, "call:model")   # the unit's next capability call
    except Problem as problem:
        body = problem.body
        assert body["type"] == "urn:agentic:problem:identity-withdrawn", body["type"]
        assert body["status"] == 403, body
        assert body["subject"] == WITHDRAWN_SUBJECT, body
        assert WITHDRAWN_SUBJECT in body["detail"], body["detail"]
        new_records = adapter.hops[hops_before:]
        assert len(new_records) == 1, f"expected one audit record for the stop, got {len(new_records)}"
        record = new_records[0]
        assert record["subject"] == WITHDRAWN_SUBJECT, record
        assert record["withdrawn_by"] == WITHDRAWN_BY, record
        assert record["withdrawn_at"] == withdrawal["withdrawn_at"], record
        assert record["action_id"] == "action-withdrawal-001", record
        assert "stopped_at" in record and record["stopped_at"], record
        print("PROBLEM (application/problem+json):")
        print(json.dumps(body, indent=2))
        print("AUDIT RECORD (one record, both facts):")
        print(json.dumps(record, indent=2))
        print("identity-withdrawal-check PASSED: the next capability call under the withdrawn identity "
              f"was refused, typed identity-withdrawn, naming {WITHDRAWN_SUBJECT}; one audit record shows "
              f"withdrawn_by={record['withdrawn_by']} at {record['withdrawn_at']}, stopped_at "
              f"{record['stopped_at']} in {record['action_id']}")
        return 0
    print("FAIL: the next capability call under a withdrawn identity was granted")
    return 1


if __name__ == "__main__":
    sys.exit(main())
