#!/usr/bin/env python3
"""The conformance run every adapter must pass. Identical cases, any adapter,
selected by configuration; it is the swap proof and the breakage detector.

  python3 conformance.py --adapter dryrun --report out/tel-a.json
  python3 conformance.py --adapter second --report out/tel-b.json
  python3 conformance.py --merge out/tel-a.json out/tel-b.json

It drives call.py's dispatch seam rather than a parallel path of its own, and it
reads every counter back off the adapter's own query surface, never out of an
emitter's memory. Exit 0 pass, 1 fail, 2 the adapter could not be reached.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from call import DEPTH, dispatch_tree, reassemble, stamp
from interface import (MAPPING_VERSION_KEY, REGISTRY, REPORT_SCHEMA, ROOT_DISPATCH_ID_KEY,
                       RUN_ID_KEY, AdapterUnavailable, CorrelationRecord, Problem,
                       TelemetryAdapter, load_adapter, unit_has_no_parent_field, validate)

FORBIDDEN_PARAMS = {"sample", "sampling", "sample_rate", "enabled", "disable", "force", "backend"}


def run(adapter_name: str, break_stamp: bool = False) -> tuple[dict, list[str]]:
    """Returns (report, failures). A failure is a contract violation, in words."""
    fails: list[str] = []
    impl: TelemetryAdapter = load_adapter(adapter_name)

    # C1  telemetry cannot be requested or declined: no operation takes a sampling
    #     or enable argument, and emit hands nothing back to branch on.
    for op in ("bind", "emit", "measure"):
        params = set(inspect.signature(getattr(impl, op)).parameters)
        if params & FORBIDDEN_PARAMS:
            fails.append(f"C1 {op}() exposes an opt-out parameter: {sorted(params & FORBIDDEN_PARAMS)}")
    if impl.emit.__doc__ is not None and inspect.signature(impl.emit).return_annotation not in (None, "None", inspect.Signature.empty):
        fails.append("C1 emit() returns a value a caller could branch on")

    # C2  no parentage anywhere on the interface: there is nowhere to put a parent.
    if not unit_has_no_parent_field():
        fails.append("C2 the unit shape carries a parent field, so reassembly could rely on it")

    # C3  one depth-3 run across a boundary that mints its own root trace at every level.
    env = stamp("human", {"run": "conformance", "why": "the depth-3 correlation fixture"},
                {"fixture": "depth-3"})
    record = CorrelationRecord(**env["correlation"])
    emitted = dispatch_tree(impl, record, break_stamp=break_stamp)

    # C4  reassemble by grouping on the attribute, from the adapter's query surface.
    got = reassemble(impl, record.run_id, emitted)
    if isinstance(got, Problem):
        fails.append(f"C4 the run could not be read back: {got.title}")
        got = {"levels_covered": 0, "run_id_groups": 0, "distinct_trace_ids": 0,
               "spans_missing_run_id": emitted["spans_emitted"],
               "spans_missing_root_dispatch_id": emitted["spans_emitted"],
               "mapping_version": "", "signals_checked": 0, "signals": []}

    if got["levels_covered"] != DEPTH:
        fails.append(f"C4 levels_covered {got['levels_covered']}, expected {DEPTH}")
    if got["run_id_groups"] != 1:
        fails.append(f"C4 run_id_groups {got['run_id_groups']}, expected 1")
    if got["spans_missing_run_id"] != 0:
        fails.append(f"C4 spans_missing_run_id {got['spans_missing_run_id']}, expected 0")
    if got["spans_missing_root_dispatch_id"] != 0:
        fails.append(f"C4 spans_missing_root_dispatch_id {got['spans_missing_root_dispatch_id']}, expected 0")
    if got["signals_checked"] <= 0:
        fails.append("C4 signals_checked is 0: nothing was read back")
    if got["distinct_trace_ids"] < 1:
        fails.append("C4 distinct_trace_ids is 0; it is reported and never constrained above 1")

    # C5  a metric joins to the spans on run.id, same resource attributes.
    metrics = [s for s in got["signals"] if s.kind == "metric"]
    if not metrics:
        fails.append("C5 no metric was read back for the run")
    elif any(m.resource.get(RUN_ID_KEY) != record.run_id
             or not m.resource.get(ROOT_DISPATCH_ID_KEY) for m in metrics):
        fails.append("C5 a metric does not carry the run's correlation attributes")

    # C6  the mapping version is read back off the wire, never from configuration.
    declared = impl.describe_mapping().version
    on_wire = got["mapping_version"]
    if not on_wire:
        fails.append("C6 no mapping version on the emitted telemetry")
    elif on_wire != declared:
        fails.append(f"C6 mapping version on the wire {on_wire!r} != declared {declared!r}")
    for sig in got["signals"]:
        if sig.resource.get(MAPPING_VERSION_KEY) != on_wire:
            fails.append("C6 a signal was emitted against a different mapping version")
            break

    # C7  the failure path: a run that cannot be shown answers with problem details.
    miss = impl.fetch_run("run-that-was-never-dispatched")
    if not isinstance(miss, Problem):
        fails.append("C7 an unknown run returned data instead of problem details")
    else:
        suffix = miss.type.rsplit(":", 1)[-1]
        if suffix not in REGISTRY:
            fails.append(f"C7 problem type {miss.type} is not in the closed registry")
        elif not REGISTRY[suffix]["registered"]:
            fails.append(f"C7 problem type {miss.type} is proposed and not yet registered")
        if not isinstance(miss.status, int) or not isinstance(miss.retryable, bool):
            fails.append("C7 problem details are not machine-readable")

    report = {
        "adapter": adapter_name,
        "levels_covered": got["levels_covered"],
        "run_id_groups": got["run_id_groups"],
        "distinct_trace_ids": got["distinct_trace_ids"],
        "mapping_version": on_wire,
        "spans_missing_run_id": got["spans_missing_run_id"],
        "spans_missing_root_dispatch_id": got["spans_missing_root_dispatch_id"],
        "signals_checked": got["signals_checked"],
        "semantic_queries_supported": impl.semantic_queries_supported,
        "selected_by": "configuration",
        "adapters_run": 1,
    }
    # C8  the report is machine-checkable against the declared shape.
    fails += [f"C8 report {e}" for e in validate(report, REPORT_SCHEMA)]
    return report, fails


def merge(paths: list[str]) -> tuple[dict, list[str]]:
    """The swap proof: two adapters, one interface, counters that must agree."""
    reports = [json.load(open(p)) for p in paths]
    fails = []
    merged = {"adapters_run": len(reports), "selected_by": "configuration",
              "adapters": [r["adapter"] for r in reports]}
    if len(reports) < 2:
        fails.append("swap proof needs two reports")
    if len({r["adapter"] for r in reports}) != len(reports):
        fails.append("the same adapter ran twice; that is not a swap")
    for k in ("levels_covered", "run_id_groups", "spans_missing_run_id",
              "spans_missing_root_dispatch_id", "mapping_version"):
        vals = {r[k] for r in reports}
        merged[k] = reports[0][k]
        if len(vals) != 1:
            fails.append(f"the interface did not hold: {k} differs across adapters {vals}")
    merged["distinct_trace_ids"] = [r["distinct_trace_ids"] for r in reports]
    merged["semantic_queries_supported"] = {r["adapter"]: r["semantic_queries_supported"]
                                            for r in reports}
    return merged, fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"))
    ap.add_argument("--report")
    ap.add_argument("--break-stamp", action="store_true")
    ap.add_argument("--merge", nargs="*", help="merge report files into the swap proof")
    args = ap.parse_args()

    if args.merge:
        report, fails = merge(args.merge)
    else:
        try:
            report, fails = run(args.adapter, break_stamp=args.break_stamp)
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
    print(f"conformance: {'PASS' if not fails else f'FAIL ({len(fails)})'} adapter={report.get('adapter', report.get('adapters'))}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
