#!/usr/bin/env python3
"""The minimal call: submit a unit of work under a key, replay it, race it, and
reuse the key under a different payload.

    ADAPTER=dryrun python3 harness/idempotency/call.py

Everything below the CALLER CODE marker is what a caller writes. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the envelope here, not asked for by the caller (F-b4-01).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import ClaimRequest, Envelope, Problem, digest, load_adapter  # noqa: E402

SCOPE = "harness/idempotency:submit-unit"


def envelope(key: str, amount: int) -> dict:
    """One entry envelope (cap-consumption shape). The four stamps applied here."""
    actor = os.environ.get("ACTOR", "user:corey")
    return Envelope(
        kind=os.environ.get("ENTRY_KIND", "human"), entry_id="idem-submit-unit",
        occurred_at="2026-09-03T09:12:00Z",
        actor={"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
        intent={"workflow_ref": "harness/idempotency", "summary": "submit one unit of work"},
        correlation={"run_id": "run-" + key, "correlation_id": "corr-" + key, "depth": 0},
        budget={"ceiling_micros": 50_000, "currency": "USD", "on_exceed": "terminate_unit"},
        idempotency_key=key, payload={"amount": amount},
    ).dict()


def submit(adapter, env: dict) -> tuple:
    """claim -> perform the effect only if fresh -> complete. The effect counter
    lives here, outside the adapter, so a duplicate is proven from the caller's
    own count and not from the adapter's self-report."""
    req = ClaimRequest.for_payload(env["idempotency_key"], env["payload"], SCOPE,
                                   env["correlation"]["correlation_id"],
                                   env["actor"]["subject"], env["kind"])
    out = adapter.claim(req)
    if out.outcome == "fresh":
        result_ref = digest({"charged_amount": env["payload"]["amount"]})
        adapter.complete(req.idempotency_key, req.scope, result_ref)
        return out.outcome, result_ref, out.in_flight
    return out.outcome, out.result_ref, out.in_flight


def race(adapter, env: dict, n: int) -> tuple:
    """n concurrent submissions of the same key. One wins; the rest wait or are
    answered while the winner is still working."""
    outcomes = []
    lock = threading.Lock()
    barrier = threading.Barrier(n)

    def worker():
        barrier.wait()
        result = submit(adapter, env)
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return outcomes


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    try:
        adapter = load_adapter(os.environ.get("ADAPTER", "dryrun"),       # configuration, not code
                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "call"))
        key = os.environ.get("KEY", "human-submit-unit-2026-09-03")
        env = envelope(key, amount=42)
        first = submit(adapter, env)                                     # submit one unit of work
        replay = submit(adapter, env)                                    # replay it: same key, same payload
        race_outcomes = race(adapter, envelope("race-" + key, amount=7), 10)  # race the submission
    except Problem as problem:                                           # adapter unreachable, typed
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    try:
        submit(adapter, envelope(key, amount=13))                        # same key, a different payload
        conflict = None
    except Problem as problem:                                           # refused with a typed problem
        conflict = problem.body

    table([("submit", first[0], str(first[1])[:24]), ("replay", replay[0], str(replay[1])[:24])],
          ("call", "outcome", "result_ref"))
    fresh = sum(1 for o in race_outcomes if o[0] == "fresh")
    print(f"\nrace(10): fresh={fresh} duplicate={10 - fresh} "
          f"in_flight_seen={any(o[2] for o in race_outcomes)}")
    print(f"reuse under a different payload: "
          f"{json.dumps(conflict, indent=2) if conflict else 'NOT REFUSED'}")
    won_race = fresh == 1 or not adapter.supports_in_flight   # only a lease is required to win it
    ok = (replay[0] == "duplicate" and replay[1] == first[1] and won_race
          and conflict and conflict["type"].endswith("idempotency-conflict"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
