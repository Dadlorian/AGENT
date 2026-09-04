#!/usr/bin/env python3
"""C09-F closure check: bind all three emission kinds - spans, log records and
problem objects - to the same trace identity per unit of work, and count each
kind separately in the audit rather than reporting one total.

  python3 correlation_audit.py --adapter dryrun
  python3 correlation_audit.py --adapter dryrun --break-problem-trace   # deliberate breakage

Drives call.py's dispatch seam (the same stamp()/dispatch_tree() every other
check in this harness uses) rather than a parallel path of its own, and reads
every signal back off the adapter's own query surface via fetch_run(), never
out of an emitter's memory.

For one depth-3 run it asserts, per signal kind (span, log_record,
problem_object), that signals_checked > 0 (an audit that collected nothing
cannot report success) and that missing_run_id == missing_root_dispatch_id == 0
on the resource attributes; and, per level, that the span, the log record and
the problem object emitted for that level carry one identical trace id - the
"same trace and span identifiers" C09-F's closure names, which resource
attributes alone do not check. Exit 0 pass, 1 fail, 2 the adapter could not be
reached.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from call import DEPTH, dispatch_tree, stamp
from interface import (ROOT_DISPATCH_ID_KEY, RUN_ID_KEY, AdapterUnavailable,
                       CorrelationRecord, Problem, load_adapter)

KINDS = ("span", "log_record", "problem_object")


def run(adapter_name: str, break_problem_trace: bool = False) -> tuple[dict, list[str]]:
    """Returns (report, failures). A failure is a contract violation, in words."""
    fails: list[str] = []
    impl = load_adapter(adapter_name)

    env = stamp("human", {"run": "correlation-audit", "why": "C09-F: bind and count three emission kinds"},
               {"fixture": "depth-3-three-kinds"})
    record = CorrelationRecord(**env["correlation"])
    dispatch_tree(impl, record, break_problem_trace=break_problem_trace)

    got = impl.fetch_run(record.run_id)
    if isinstance(got, Problem):
        fails.append(f"the run could not be read back: {got.title}")
        got = []

    per_kind: dict[str, dict[str, int]] = {}
    for kind in KINDS:
        sigs = [s for s in got if s.kind == kind]
        missing_run = sum(1 for s in sigs if s.resource.get(RUN_ID_KEY) != record.run_id)
        missing_root = sum(1 for s in sigs if not s.resource.get(ROOT_DISPATCH_ID_KEY))
        per_kind[kind] = {"signals_checked": len(sigs), "missing_run_id": missing_run,
                          "missing_root_dispatch_id": missing_root}
        if len(sigs) == 0:
            fails.append(f"{kind}: signals_checked is 0 - the audit collected nothing for this kind")
        if missing_run:
            fails.append(f"{kind}: missing_run_id {missing_run}, expected 0")
        if missing_root:
            fails.append(f"{kind}: missing_root_dispatch_id {missing_root}, expected 0")

    # Same trace identity across the three kinds, per unit of work (per level):
    # resource attributes alone (checked above) would not have caught a problem
    # object built without its trace id, because a resource attribute and a
    # top-level trace_id field are two different places to omit a stamp.
    by_depth: dict[object, dict[str, str | None]] = {}
    for s in got:
        if s.kind not in KINDS:
            continue
        by_depth.setdefault(s.resource.get("correlation.depth"), {})[s.kind] = s.unit.get("trace_id")
    trace_mismatches = 0
    for depth in sorted(by_depth, key=lambda d: (d is None, d)):
        by_kind = by_depth[depth]
        missing_kinds = [k for k in KINDS if k not in by_kind]
        values = set(by_kind.values())
        if missing_kinds or len(values) != 1 or None in values or "" in values:
            trace_mismatches += 1
            fails.append(f"level {depth}: span/log_record/problem_object do not share one trace id "
                         f"(missing {missing_kinds or 'none'}, trace ids {by_kind})")
    if not by_depth:
        trace_mismatches += 1
        fails.append("no level produced all three kinds to compare trace ids across")

    report = {
        "adapter": adapter_name,
        "run_id": record.run_id,
        "levels_run": DEPTH,
        "per_signal_kind": per_kind,
        "levels_compared": len(by_depth),
        "trace_id_shared_per_level": trace_mismatches == 0,
    }
    return report, fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"))
    ap.add_argument("--break-problem-trace", action="store_true",
                    help="deliberate breakage: drop the trace id off the problem object at level 0")
    ap.add_argument("--report")
    args = ap.parse_args()

    try:
        report, fails = run(args.adapter, break_problem_trace=args.break_problem_trace)
    except AdapterUnavailable as exc:
        print("application/problem+json")
        print(json.dumps(exc.problem.as_dict(), indent=2))
        return 2

    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        json.dump(report, open(args.report, "w"), indent=2, sort_keys=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    for f in fails:
        print(f"  FAIL {f}")
    print(f"correlation_audit: {'PASS' if not fails else f'FAIL ({len(fails)})'} adapter={args.adapter}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
