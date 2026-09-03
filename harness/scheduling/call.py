#!/usr/bin/env python3
"""The minimal call: declare one unit's schedule, tick it over a window, fire
each occurrence through the ordinary entry envelope, replay one for free.

    ADAPTER=dryrun python3 harness/scheduling/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: build_envelope() (in interface.py) stamps the
correlation id, the budget ceiling, the derived idempotency key and the actor
without being asked (T-t2-03), and one environment variable binds one of
three adapters.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import Problem                       # noqa: E402
from adapters.dryrun import DryRunAdapter            # noqa: E402
from adapters.live import EngineOwnedScheduleAdapter  # noqa: E402
from adapters.second import TickerQueueAdapter       # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": EngineOwnedScheduleAdapter, "second": TickerQueueAdapter}


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
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()    # configuration, not code
    unit_ref = os.environ.get("UNIT_REF", "nightly-fault-sweep")
    rule = os.environ.get("RECURRENCE", "FREQ=DAILY;BYHOUR=2;BYMINUTE=0")
    try:
        adapter.declare({"unit_ref": unit_ref, "recurrence": rule,
                         "starts_at": os.environ.get("STARTS_AT", "2026-09-01T02:00:00"),
                         "timezone": os.environ.get("TZ_NAME", "UTC"), "catch_up": "fire_once"})
        fired = adapter.tick(os.environ.get("NOW", "2026-09-01T00:00:00Z"),
                             int(os.environ.get("WINDOW_S", str(3 * 86400))))
        replay = adapter.fire(unit_ref, fired[0]["occurred_at"]) if fired else None
    except Problem as problem:
        print("PROBLEM (application/problem+json):")
        print(__import__("json").dumps(problem.body, indent=2))
        return 2
    table([(e["kind"], e["occurred_at"], e["idempotency_key"][:20] + "...") for e in fired],
          ("entry", "occurred_at", "idempotency_key"))
    print(f"\nreplay same envelope: {replay == fired[0] if fired else 'n/a'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
