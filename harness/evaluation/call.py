#!/usr/bin/env python3
"""The minimal call: register a case set, replay a recorded run against it, score
the trajectory, read one verdict - and watch a gate refuse to call an empty run green.

Two regions. The caller region below the CALLER CODE marker is everything a caller
writes: an intent and a payload. Everything above it is the platform - it stamps
the correlation id, the budget ceiling, the idempotency key and the actor without
being asked, registers the corpus, drives the five interface operations and reads
the gate's status off the report's counters. Nothing here names a harness, a store
or a backend.

  ADAPTER=dryrun|live|second python3 call.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import (Case, DIMENSIONS, INCONCLUSIVE, PASSED, StubPolicy, UnitRef,
                       AdapterUnavailable, gate_stage, load_adapter)
from unit_under_test import BASELINE_VERSION, REGRESSED_VERSION, UNIT_REF

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus")
CASE_SET_ID, BASELINE_ID = "cs-release-review", "bl-2026-08-27"
BUDGET_CEILING_MICROS = 2_000_000
PER_CASE_MICROS = 100_000            # the ceiling is checked per case, not once per report


# --- platform: the cross-cutting stamps the caller never asks for ------------
def stamp(kind: str, intent: dict, payload: dict) -> dict:
    """Build the entry envelope. correlation, budget, idempotency_key and actor are
    applied here; there is no argument by which a caller supplies or declines them."""
    key = hashlib.sha256(json.dumps([kind, intent, payload], sort_keys=True).encode()).hexdigest()[:16]
    return {
        "kind": kind,
        "actor": {"subject": {"human": "user:corey", "event": "service:release-bot",
                              "schedule": "schedule:nightly", "external": "agent:partner"}[kind],
                  "delegation": []},
        "intent": intent,
        "correlation": {"run_id": f"run-{kind}-{key[:8]}", "root_dispatch_id": f"d-{kind}-{key[:8]}",
                        "depth": 0, "entry_kind": kind},
        "budget": {"ceiling_micros": BUDGET_CEILING_MICROS, "per_case_micros": PER_CASE_MICROS},
        "idempotency_key": key,
        "payload": payload,
    }


def corpus_cases(name: str = "case-set.json") -> tuple[str, str, list[Case]]:
    """The corpus a caller points at, read as data. A case carries a rubric handle
    and never a rubric body, so what is graded cannot travel into what is graded."""
    with open(os.path.join(CORPUS, name)) as fh:
        row = json.load(fh)
    cases = [Case(c["case_id"], c["corpus_half"], c["input"], c["rubric_ref"],
                  StubPolicy(**c["stub_policy"]), c.get("recorded_run_ref"))
             for c in row["cases"]]
    return row["case_set_id"], row["version"], cases


def enter(kind: str, intent: dict, payload: dict, adapter: str = "dryrun") -> dict:
    """One entry envelope in, one answer out: a result or problem details.
    Registers the case set, evaluates, and gates - the five operations and nothing else."""
    env = stamp(kind, intent, payload)
    try:
        impl = load_adapter(adapter)
    except AdapterUnavailable as exc:
        return exc.problem.as_dict()
    case_set_id, version, cases = corpus_cases()
    handle = impl.register_case_set(cases, version, case_set_id)
    if not hasattr(handle, "digest"):
        return handle.as_dict()
    ref, _, unit_version = payload["unit"].partition("@")
    report = impl.evaluate(UnitRef(ref, unit_version), payload["case_set"], payload["baseline"],
                           correlation_id=env["correlation"]["root_dispatch_id"],
                           mode="replay", case_filter=payload.get("case_filter"))
    if not hasattr(report, "outcome"):
        return report.as_dict()
    evidence = "ev-" + hashlib.sha256(report.report_id.encode()).hexdigest()[:10]
    stage = gate_stage(report, evidence)
    return {"adapter": impl.name, "digest": handle.digest,
            "unit": f"{report.unit_under_test.ref}@{report.unit_under_test.version}",
            "outcome": report.outcome, "cases_executed": report.cases_executed,
            "transitions": [{"case_id": t.case_id, "was": t.was, "now": t.now,
                             "dimension_scores": t.dimension_scores} for t in report.transitions],
            "verdicts": dict(report.verdicts), "report_id": report.report_id,
            "served_effects": report.served_effects, "executed_effects": report.executed_effects,
            "spend_micros": report.cases_executed * PER_CASE_MICROS,
            "ceiling_micros": env["budget"]["ceiling_micros"],
            "gate": stage.as_dict(), "blocks_promotion": stage.blocks_promotion,
            "correlation_id": report.correlation_id}


def _table(rows: list[tuple[str, ...]]) -> str:
    w = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = ["  ".join(c.ljust(w[i]) for i, c in enumerate(rows[0])),
           "  ".join("-" * x for x in w)]
    out += ["  ".join(c.ljust(w[i]) for i, c in enumerate(r)) for r in rows[1:]]
    return "\n".join(out)


def report(runs: dict[str, dict]) -> int:
    """Presentation and the two proofs it prints, so the caller region below is the
    call, the answer and the one branch on a problem - nothing else."""
    cand, skipped = runs["candidate"], runs["skipped"]
    print(f"adapter={cand['adapter']}  corpus digest={cand['digest']}  "
          f"correlation.id={cand['correlation_id']}  budget={cand['spend_micros']}/"
          f"{cand['ceiling_micros']} micros ({PER_CASE_MICROS} per case)")
    print(_table([("run", "unit under test", "cases executed", "outcome", "transitions",
                   "gate status", "blocks promotion")]
                 + [(label, r["unit"], str(r["cases_executed"]), r["outcome"],
                     ",".join(f"{t['case_id']} {t['was']}->{t['now']}" for t in r["transitions"]) or "-",
                     r["gate"]["status"], "yes" if r["blocks_promotion"] else "no")
                    for label, r in runs.items()]))
    print("\nper case, candidate run (the ordered trace is scored, not the final answer):")
    moved = {t["case_id"]: t for t in cand["transitions"]}
    print(_table([("case", "verdict", *DIMENSIONS, "against baseline")]
                 + [(case_id, verdict,
                     *(moved.get(case_id, {}).get("dimension_scores", {}).get(d, "pass")
                       for d in DIMENSIONS),
                     f"{moved[case_id]['was']} -> {moved[case_id]['now']}" if case_id in moved else "held")
                    for case_id, verdict in sorted(cand["verdicts"].items())]))
    named = [t for t in cand["transitions"] if t["now"] == "fail"]
    trajectory_scored = any(t["dimension_scores"].get("tool_use") == "fail"
                            and t["dimension_scores"].get("task_completion") == "pass" for t in named)
    print()
    if named and trajectory_scored:
        t = named[0]
        print(f"PROOF: the verdict names {t['case_id']} - tool_use {t['was']} -> fail while "
              f"task_completion still passes, so the trajectory was scored, not the answer")
    else:
        print("PROOF FAILED: no case was named, or the failure was visible in the final answer")
    empty_is_green = (skipped["cases_executed"] == 0 and skipped["outcome"] == INCONCLUSIVE
                      and skipped["gate"]["status"] != PASSED and skipped["blocks_promotion"])
    print(f"PROOF: a gate cannot report success with every case skipped - cases_executed="
          f"{skipped['cases_executed']}, outcome={skipped['outcome']}, "
          f"gate status={skipped['gate']['status']}, promotion blocked" if empty_is_green
          else f"PROOF FAILED: an empty run read as {skipped['gate']['status']} with "
               f"{skipped['cases_executed']} cases executed")
    print(f"effects served from the record: {cand['served_effects']}   "
          f"effects executed: {cand['executed_effects']}   "
          f"baseline run outcome: {runs['baseline']['outcome']} "
          f"({runs['baseline']['cases_executed']} cases)")
    return 0 if (named and trajectory_scored and empty_is_green
                 and runs["baseline"]["outcome"] == PASSED) else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method every harness uses.
# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"))
    parser.add_argument("--candidate", default=f"{UNIT_REF}@{REGRESSED_VERSION}",
                        help="the version being gated; defaults to the regressed candidate")
    args = parser.parse_args()
    runs = {}
    for label, unit, only in (("baseline", f"{UNIT_REF}@{BASELINE_VERSION}", None),
                              ("candidate", args.candidate, None),
                              ("skipped", args.candidate, "none")):
        answer = enter(                                  # the whole call
            kind="human",
            intent={"run": "gate-a-release", "why": "a candidate may not ship until the corpus says so"},
            payload={"unit": unit, "case_set": CASE_SET_ID, "baseline": BASELINE_ID,
                     "case_filter": only},
            adapter=args.adapter,
        )
        if "type" in answer:                             # one problem, never both
            print("application/problem+json")
            print(json.dumps(answer, indent=2))
            return 2
        runs[label] = answer
    return report(runs)


if __name__ == "__main__":
    raise SystemExit(main())
