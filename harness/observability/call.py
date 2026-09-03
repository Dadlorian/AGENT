#!/usr/bin/env python3
"""The minimal call: one run, one trace, reassembled by grouping and not by parentage.

Two regions. The caller region below the CALLER CODE marker is everything a
caller writes: an intent and a payload. Everything above it is the platform - it stamps the
correlation record, the budget ceiling, the idempotency key and the actor without
being asked, binds the telemetry context at the one dispatch seam, and crosses a
simulated agent boundary that mints its own root trace at every level, which is
PASS.md A7 finding 1. Nothing here names a backend.

  ADAPTER=dryrun|live|second python3 call.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import (MAPPING_VERSION_KEY, OPERATION_NAMES, ROOT_DISPATCH_ID_KEY,
                       RUN_ID_KEY, AdapterUnavailable, CorrelationRecord, Problem,
                       TelemetryUnit, load_adapter)

DEPTH = 3                       # a depth-3 task tree: the smallest thing that reproduces the finding
BASE_INSTANT = "2026-09-03T00:00:%02dZ"
BUDGET_CEILING_MICROS = 2_000_000


# --- platform: the cross-cutting stamps the caller never asks for ------------
def stamp(kind: str, intent: dict, payload: dict) -> dict:
    """Build the entry envelope. correlation, budget, idempotency_key and actor
    are applied here; there is no argument by which a caller supplies or declines
    them, and no flag anywhere that switches telemetry off."""
    key = hashlib.sha256(json.dumps([kind, intent, payload], sort_keys=True).encode()).hexdigest()[:16]
    return {
        "kind": kind,
        "actor": {"subject": {"human": "user:corey", "event": "service:alerting",
                              "schedule": "schedule:nightly", "external": "agent:partner"}[kind],
                  "delegation": []},
        "intent": intent,
        "correlation": {"run_id": f"run-{kind}-{key[:8]}", "root_dispatch_id": f"d-{kind}-{key[:8]}",
                        "depth": 0, "entry_kind": kind},
        "budget": {"ceiling_micros": BUDGET_CEILING_MICROS},
        "idempotency_key": key,
        "payload": payload,
    }


def _trace_id(run_id: str, level: int) -> str:
    """The agent boundary mints its own root trace and ignores whatever context
    was injected into it, so each level gets an unrelated trace id."""
    return hashlib.sha256(f"{run_id}/{level}/minted-by-the-agent".encode()).hexdigest()[:32]


def dispatch_tree(adapter, correlation: CorrelationRecord, break_stamp: bool = False) -> dict:
    """The dispatch seam. bind() is called here and nowhere else, so every signal
    below inherits the correlation record whatever the runtime does to the trace.

    break_stamp is the deliberate breakage: the platform stops re-stamping at the
    child-dispatch boundary, so each child agent binds a record it minted itself -
    exactly what a runtime that ignores an injected trace header does today."""
    spans = metrics = 0
    for level in range(DEPTH):
        record = correlation if level == 0 else replace(
            correlation, depth=level,
            parent_dispatch_id=f"{correlation.root_dispatch_id}-{level - 1}")
        if break_stamp and level > 0:
            record = CorrelationRecord(run_id=f"minted-run-{level}",
                                       root_dispatch_id=f"minted-d-{level}",
                                       depth=level, entry_kind=correlation.entry_kind)
        ctx = adapter.bind(record)
        adapter.emit(ctx, TelemetryUnit(
            operation=OPERATION_NAMES["entry" if level == 0 else "dispatch"],
            started_at=BASE_INSTANT % (level * 2), ended_at=BASE_INSTANT % (level * 2 + 1),
            outcome="ok", attributes={"gen_ai.operation.name": "invoke_agent"},
            trace_id=_trace_id(correlation.run_id, level)))
        spans += 1
        if level == DEPTH - 1:
            adapter.measure(ctx, "step_duration", 1000.0 * level)
            metrics += 1
    return {"spans_emitted": spans, "metrics_emitted": metrics}


def reassemble(adapter, run_id: str, emitted: dict) -> dict | Problem:
    """Group on the attribute. run_id_groups is 1 only when one run.id value
    accounts for every span the run emitted; a group that is missing part of the
    run is not one group per run. Nothing here reads a trace id or a parent."""
    got = adapter.fetch_run(run_id)
    if isinstance(got, Problem):
        return got
    spans = [s for s in got if s.kind == "span"]
    with_run = [s for s in spans if s.resource.get(RUN_ID_KEY) == run_id]
    with_root = [s for s in spans if s.resource.get(ROOT_DISPATCH_ID_KEY)]
    complete = len(with_run) == emitted["spans_emitted"] and len(with_run) > 0
    return {
        "signals": got,
        "levels_covered": len({s.resource.get("correlation.depth") for s in with_run}),
        "run_id_groups": 1 if complete and len({s.resource[RUN_ID_KEY] for s in with_run}) == 1 else 0,
        "distinct_trace_ids": len({s.unit.get("trace_id") for s in spans if s.unit.get("trace_id")}),
        "spans_missing_run_id": emitted["spans_emitted"] - len(with_run),
        "spans_missing_root_dispatch_id": emitted["spans_emitted"] - len(with_root),
        "mapping_version": next((s.resource.get(MAPPING_VERSION_KEY) for s in spans), ""),
        "signals_checked": len(got),
    }


def enter(kind: str, intent: dict, payload: dict, adapter: str = "dryrun",
          break_stamp: bool = False) -> dict:
    """One entry envelope in, one answer out: a result or problem details."""
    env = stamp(kind, intent, payload)
    try:
        impl = load_adapter(adapter)
    except AdapterUnavailable as exc:
        return exc.problem.as_dict()
    record = CorrelationRecord(**env["correlation"])
    emitted = dispatch_tree(impl, record, break_stamp=break_stamp)
    out = reassemble(impl, record.run_id, emitted)
    if isinstance(out, Problem):
        return out.as_dict()
    out.update(adapter=impl.name, run_id=record.run_id,
               root_dispatch_id=record.root_dispatch_id, correlation_id=record.root_dispatch_id,
               semantic_queries_supported=impl.semantic_queries_supported, **emitted)
    return out


def table(answer: dict) -> str:
    rows = [("level", "kind", "operation", "trace id (minted per level)", "run.id", "correlation.id")]
    for s in answer["signals"]:
        rows.append((str(s.resource.get("correlation.depth", "-")), s.kind,
                     s.unit.get("operation", s.unit.get("instrument", "-")),
                     (s.unit.get("trace_id") or "-")[:16], s.resource.get(RUN_ID_KEY, "MISSING"),
                     s.resource.get(ROOT_DISPATCH_ID_KEY, "MISSING")))
    w = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines = ["  ".join(c.ljust(w[i]) for i, c in enumerate(rows[0])),
             "  ".join("-" * w[i] for i in range(len(w)))]
    lines += ["  ".join(c.ljust(w[i]) for i, c in enumerate(r)) for r in rows[1:]]
    return "\n".join(lines)


def report(answer: dict) -> int:
    """Presentation and the proof it prints, so the caller region below is the
    call, the answer and the one branch on a problem - nothing else."""
    print(f"adapter={answer['adapter']}  run.id={answer['run_id']}  "
          f"correlation.id={answer['root_dispatch_id']}  mapping={answer['mapping_version']}")
    print(table(answer))
    print(f"\ndistinct trace ids: {answer['distinct_trace_ids']}   "
          f"groups on run.id: {answer['run_id_groups']}   "
          f"levels covered: {answer['levels_covered']}/{DEPTH}   "
          f"spans missing run.id: {answer['spans_missing_run_id']}")
    one_tree = (answer["run_id_groups"] == 1 and answer["levels_covered"] == DEPTH
                and answer["spans_missing_run_id"] == 0)
    print("PROOF: one tree, not " + str(answer["distinct_trace_ids"])
          + " - reassembled by grouping on run.id, never by trace parentage" if one_tree
          else f"PROOF FAILED: the run did not reassemble - "
               f"{answer['spans_missing_run_id']} span(s) below the top level carry no run.id, "
               f"so grouping returns {answer['run_id_groups']} group(s) covering "
               f"{answer['levels_covered']} of {DEPTH} levels")
    return 0 if one_tree else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all five harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"))
    parser.add_argument("--break-stamp", action="store_true",
                        help="deliberate breakage: stop re-stamping at child dispatch")
    args = parser.parse_args()
    answer = enter(                                  # the whole call
        kind="human",
        intent={"run": "triage-and-fix", "why": "a failing nightly check needs diagnosis"},
        payload={"repo": "agentic-stack", "check": "nightly"},
        adapter=args.adapter, break_stamp=args.break_stamp,
    )
    if "type" in answer:                             # one problem, never both
        print("application/problem+json")
        print(json.dumps({k: v for k, v in answer.items() if k != "signals"}, indent=2))
        return 2
    return report(answer)


if __name__ == "__main__":
    raise SystemExit(main())
