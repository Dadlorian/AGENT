#!/usr/bin/env python3
"""The minimal call: one typed problem, a retry decision from the type alone,
an unregistered type refused at construction, and a byte-identical body from
the edge adapter.

    ADAPTER=dryrun python3 harness/errors/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id onto the envelope
without being asked (F-b4-06), and binds one of three adapters from one
environment variable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import MEDIA_TYPE, ProblemException, UnregisteredType   # noqa: E402
from adapters.dryrun import DryRunAdapter                              # noqa: E402
from adapters.live import LiveProblemFactory                           # noqa: E402
from adapters.second import EdgeFilterAdapter                          # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveProblemFactory, "second": EdgeFilterAdapter}


def envelope(suffix: str, detail: str) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    run_id = os.environ.get("RUN_ID", "run-harness-errors")
    corr = "corr-" + hashlib.sha256(run_id.encode()).hexdigest()[:12]
    actor = os.environ.get("ACTOR", "user:corey")
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/errors", "summary": "one typed refusal"},
            "correlation": {"run_id": run_id, "correlation_id": corr},
            "payload": {"suffix": suffix, "detail": detail}}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by the same method harness/caller_lines.py uses for the other harnesses.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()      # configuration, not code
    ask = envelope(os.environ.get("SUFFIX", "budget-exhausted"),
                   os.environ.get("DETAIL", "the call would cross the ceiling"))

    # 1. produce one typed problem for a refusal from the closed registry
    try:
        adapter.raise_problem(ask["payload"]["suffix"], ask["payload"]["detail"],
                               ask["correlation"]["correlation_id"])
    except ProblemException as exc:
        problem = exc.problem

    # 2. decide retry or not from the type alone, never from the message
    retryable, retry_after_s = adapter.retry_advice(problem)
    decision = f"retry after {retry_after_s}s" if retryable else "do not retry"

    # 3. a problem whose type is not in the registry is refused at construction
    try:
        adapter.raise_problem("not-a-registered-type", "should never construct a body")
        rejected = "NOT REJECTED"
    except UnregisteredType:
        rejected = "rejected before a body was ever built"
    except ProblemException as exc:            # the binding itself refused first (e.g. live, no context)
        rejected = f"adapter refused before the registry check: {exc.problem.type}"

    # 4. the same body, read back off the wire by the edge adapter, byte for byte
    edge = EdgeFilterAdapter()
    reshaped = edge.classify({"status": problem.status, "media_type": MEDIA_TYPE, "body": problem.body()})
    identical = reshaped.canonical() == problem.canonical()

    table([(problem.suffix(), problem.status, decision, rejected, identical)],
          ("type", "status", "retry_decision", "unregistered_type", "byte_identical_on_second"))
    print("\n" + json.dumps(problem.body(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
