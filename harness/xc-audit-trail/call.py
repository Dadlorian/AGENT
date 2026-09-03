#!/usr/bin/env python3
"""The minimal call: project a run into a trail, fetch it by correlation id,
attribute one entry to its actor and delegation chain.

    ADAPTER=dryrun python3 harness/xc-audit-trail/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it binds one of three adapters from one environment
variable, and the actor, delegation chain and correlation triple are already
on every entry the trail returns - a caller never stamps them itself
(T-t2-03).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import Problem  # noqa: E402
from adapters.dryrun import LocalChainedTrailAdapter  # noqa: E402
from adapters.live import LiveLedgerTrailAdapter  # noqa: E402
from adapters.second import ExternalCheckableLogAdapter  # noqa: E402

ADAPTERS = {"dryrun": LocalChainedTrailAdapter, "live": LiveLedgerTrailAdapter,
           "second": ExternalCheckableLogAdapter}


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
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()   # configuration, not code
    try:
        trail = adapter.project()                               # a run's records, projected
        correlation_id = trail[0].correlation["correlation_id"]
        run = adapter.fetch_by_correlation(correlation_id)       # everything under one correlation id
        who = adapter.attribute(run[0].entry_id)                 # actor and delegation chain
    except Problem as problem:
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    table([(e.entry_id[:28], e.kind, e.actor, e.correlation["correlation_id"]) for e in run[:5]],
         ("entry", "kind", "actor", "correlation_id"))
    print(f"\ntrail entries      {len(trail)}")
    print(f"under {correlation_id}  {len(run)}")
    print(f"attributed to      {who['actor']}, via {len(who['delegation_chain'])}-hop delegation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
