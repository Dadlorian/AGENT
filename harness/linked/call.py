#!/usr/bin/env python3
"""The minimal call: one document through all four doors, linked end to end.

    python3 harness/linked/call.py

    ADAPTER_CONTAINMENT=second ADAPTER_GATEWAY=second \
    ADAPTER_TRACE=second ADAPTER_WORKFLOW=second python3 harness/linked/call.py

Everything below the CALLER CODE marker is what a caller writes: pick a door,
hand it the document, read one result or one problem. Everything else is
the platform - it stamps correlation, identity, the ceiling and the idempotency
key, prices the plan before anything runs, dispatches one contained agent turn
that makes one completion by model class, traces every level, checkpoints every
step, and refuses in one shape. No component is named anywhere in this file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import doors                                          # noqa: E402
from interface import Problem, Result                 # noqa: E402
from linked import platform                           # noqa: E402


def table(rows, header) -> None:
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def report(place, answers: list[Result]) -> int:
    table([(a.kind, a.actor_subject, a.identity_hops, a.subject_digest[7:19],
            a.plan_digest[7:19], a.stop_reason, a.spent_micros, a.ceiling_micros)
           for a in answers],
          ("door", "actor", "hops", "subject", "plan", "stop", "spent", "ceiling"))
    trace = [place.receipts[a.run_id].trace for a in answers]
    print(f"\nsubjects {len({a.subject_digest for a in answers})}   "
          f"plans {len({a.plan_digest for a in answers})}   "
          f"actors {len({a.actor_subject for a in answers})}   "
          f"runs {len({a.run_id for a in answers})}")
    print(f"one trace per run: groups {sorted({t['run_id_groups'] for t in trace})}   "
          f"levels {sorted({t['levels_covered'] for t in trace})}   "
          f"distinct trace ids {sorted({t['distinct_trace_ids'] for t in trace})}   "
          f"spans missing run.id {sorted({t['spans_missing_run_id'] for t in trace})}")
    print("\nbound by configuration: " + "  ".join(f"{k}={v}" for k, v in place.selected().items()))
    print("read from the running components: " + "  ".join(f"{k}={v}" for k, v in place.markers().items()))
    return 0


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all five harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(HERE, "out", "call"))
    ap.add_argument("--ceiling-micros", type=int, help="override the ceiling every door carries")
    args = ap.parse_args()
    subject = dict(doors.SUBJECT)
    if args.ceiling_micros is not None:
        subject["budget"] = {**subject["budget"], "ceiling_micros": args.ceiling_micros}

    place = platform(args.out)                       # the four capabilities, bound by configuration
    answers = []
    for door in doors.DOORS:                         # human, event, schedule, external
        answer = place.submit(door.envelope(subject).dict())
        if isinstance(answer, Problem):              # one handler, branched on type
            print("PROBLEM (application/problem+json):")
            print(json.dumps(answer.body, indent=2))
            return 2
        answers.append(answer)                       # one result per door, same shape
    return report(place, answers)


if __name__ == "__main__":
    sys.exit(main())
