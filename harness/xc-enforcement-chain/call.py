#!/usr/bin/env python3
"""The minimal call: one envelope, four doors, one chain, the same order.

    ADAPTER=dryrun python3 harness/xc-enforcement-chain/call.py
    ADAPTER=second python3 harness/xc-enforcement-chain/call.py

Everything below the CALLER CODE marker is what a caller writes: hand each door
the same unit, cross the three points, make the one metered call, and read one
result or one problem. Everything above it is the platform. The caller never
names a slot, never chooses an order, and has no argument anywhere with which to
skip one, exempt one or ask for one - the correlation, the ceiling, the
idempotency key and the actor ride on the unit, and the chain is applied to it.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import units                                                          # noqa: E402
from interface import (CONCERNS, DECLARED_SLOTS, POINTS, Problem,     # noqa: E402
                       attest, drive)
from adapters.dryrun import Adapter as DryRunAdapter                  # noqa: E402
from adapters.live import Adapter as LiveAdapter                      # noqa: E402
from adapters.second import Adapter as SecondAdapter                  # noqa: E402

BINDINGS = {"dryrun": DryRunAdapter, "live": LiveAdapter, "second": SecondAdapter}


def table(rows, header) -> None:
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def fail(problem: Problem) -> int:
    print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
    return 2


def show(adapter, rows, refusals, skipped, fail_open, report) -> int:
    """Presentation, so the caller region below is calls and results only."""
    table([(door, "->".join(POINTS), ctx.slots[-1].seq + 1, result["spent_micros"],
            "yes" if result["chained"] else "NO", ctx.correlation["correlation_id"])
           for door, ctx, result in rows],
          ("door", "points crossed", "slots at the call", "spent_micros", "chained", "correlation"))
    first = rows[0][1]
    print("\nthe chain at the call point, in its one declared order:")
    table([(s.seq, s.slot, CONCERNS[s.slot], "yes" if s.owner_running else "no (counted)",
            s.outcome, s.inverse, s.inverse_seq) for s in first.slots],
          ("seq", "slot", "the concern it carries", "owner running", "outcome", "inverse", "inv seq"))
    print("\nthe unit whose ceiling cannot cover one metered call, at each door:")
    table([(door, b["type"].rsplit(":", 1)[-1], b["status"], b["detail"].split(":")[0],
            b["retryable"]) for door, b in refusals],
          ("door", "problem type", "status", "first refusal", "retryable"))
    print(f"a caller cannot skip a link: the metered call with no context came back "
          f"{'refused (' + skipped['type'].rsplit(':', 1)[-1] + ')' if skipped else 'unrefused'}, "
          f"counted as ungated_metered_calls={report['ungated_metered_calls']}")
    print(f"a link that fails open is detected: fail_open_slots={fail_open} when one slot reports "
          f"passed with no owner running; {report['fail_open_slots']} in the run above")
    print(f"slots recorded no-op because their owner is not running here: "
          f"{report['slots_noop_by_absent_owner']}   chain_context_missing="
          f"{report['chain_context_missing']}   out_of_order={report['out_of_order']}   "
          f"missing_inverse={report['missing_inverse']}")
    print(f"\nchain records digest: {report['records_digest']}   (identical from either "
          f"enforcement point: run this again with ADAPTER=second)")
    print(f"bound by configuration: ADAPTER={os.environ.get('ADAPTER', 'dryrun')}   "
          f"locus={adapter.locus}   read from the refusal: {report['adapter_observed']}")
    return 0 if refusals and report["fail_open_slots"] == 0 else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method every harness uses.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = BINDINGS[os.environ.get("ADAPTER", "dryrun")]()          # configuration, not code
    rows, refusals, seen = [], [], []
    try:
        for door in units.DOORS:                                       # human, event, schedule, external
            unit, ctx = units.unit(door, 0), None
            for point in POINTS:                                       # admission, dispatch, call
                ctx = adapter.enter(point, unit, parent=ctx)
                if point != "call":
                    adapter.exit(ctx, "passed")
            rows.append((door, ctx, adapter.meter(unit, ctx)))         # the one thing that spends
            adapter.exit(ctx, "passed")
        for door in units.DOORS:                                       # one unit the ceiling cannot cover
            try:
                adapter.enter("admission", units.unit(door, 1))
            except Problem as refusal:
                refusals.append((door, refusal.body))
        try:                                                           # a metered call with no context
            adapter.meter(units.unit("human", 3), None)
            skipped = None
        except Problem as refusal:
            skipped = refusal.body
        report = attest(adapter, [units.unit(d, 0) for d in units.DOORS])
        report["adapter_observed"] = refusals[0][1].get("enforced_by", "unread")
    except Problem as problem:                                         # one refusal shape, read by type
        return fail(problem)
    finally:
        adapter.close()
    os.environ["CHAIN_FAIL_OPEN"] = "identity.resolve"                  # one link made to report passed
    hollow = BINDINGS[os.environ.get("ADAPTER", "dryrun")]()
    drive(hollow, [units.unit("human", 4)], lambda unit, body: seen.append(body))
    fail_open = attest(hollow, [units.unit("human", 4)])["fail_open_slots"]
    hollow.close()
    return show(adapter, rows, refusals, skipped, fail_open, report)


if __name__ == "__main__":
    sys.exit(main())
