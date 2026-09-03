#!/usr/bin/env python3
"""The evaluation conformance run: the same twelve cases against any adapter.

  python3 conformance.py --adapter dryrun --report out/before.json
  python3 conformance.py --adapter second --report out/after.json
  python3 conformance.py --merge out/before.json out/after.json --report out/merged.json
  python3 conformance.py --adapter dryrun --break-gate       # the deliberate breakage

Exit 0 when every case passes, 1 when one fails, 2 when the adapter refused to be
constructed (problem details are printed, never a traceback). No product name
appears in this file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import (ADAPTERS, DIMENSIONS, FAILED, GATE_SCHEMA, INCONCLUSIVE, PASSED,
                       REPORT_SCHEMA, AdapterUnavailable, Case, Problem, StubPolicy,
                       UnitRef, case_carries_no_rubric_body, gate_stage,
                       gate_stage_from_exit_code, interface_operations, load_adapter,
                       no_execute_operation, report_pins_versions, validate)
from unit_under_test import BASELINE_VERSION, REGRESSED_VERSION, UNIT_REF

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")
CASE_SET_ID, BASELINE_ID = "cs-release-review", "bl-2026-08-27"
PROBE_SET_ID = "cs-unrecorded-probe"
CID = "d-conformance-0001"


def load_cases(name: str) -> tuple[str, str, list[Case]]:
    with open(os.path.join(CORPUS, name)) as fh:
        row = json.load(fh)
    return row["case_set_id"], row["version"], [
        Case(c["case_id"], c["corpus_half"], c["input"], c["rubric_ref"],
             StubPolicy(**c["stub_policy"]), c.get("recorded_run_ref")) for c in row["cases"]]


def rubric_markers() -> list[str]:
    with open(os.path.join(CORPUS, "rubrics.json")) as fh:
        return [r["marker"] for r in json.load(fh).values()]


def run(adapter_name: str, break_gate: bool) -> tuple[dict, list[tuple[str, bool, str]]]:
    impl = load_adapter(adapter_name)
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> bool:
        checks.append((name, bool(ok), detail))
        return bool(ok)

    baseline_unit = UnitRef(UNIT_REF, BASELINE_VERSION)
    candidate = UnitRef(UNIT_REF, REGRESSED_VERSION)
    case_set_id, version, cases = load_cases("case-set.json")

    # C1 - register_case_set: content digest, stable across two registrations
    handle = impl.register_case_set(cases, version, case_set_id)
    again = impl.register_case_set(cases, version, case_set_id)
    check("C1 register_case_set returns an id and a content digest",
          hasattr(handle, "digest") and handle.case_count == 6, getattr(handle, "digest", ""))
    check("C1b identical cases registered twice agree on the digest",
          handle.digest == again.digest, handle.digest)

    # C2 - the corpus at the baseline version
    base = impl.evaluate(baseline_unit, case_set_id, BASELINE_ID, correlation_id=CID)
    ok_base = hasattr(base, "outcome")
    check("C2 six cases execute, three recorded and three synthetic",
          ok_base and base.cases_executed == 6, str(getattr(base, "cases_executed", base)))
    check("C2b outcome passed with no transition against the baseline",
          ok_base and base.outcome == PASSED and not base.transitions,
          f"{getattr(base, 'outcome', '?')}, {len(getattr(base, 'transitions', []))} transitions")

    # C3 - replay serves recorded effects and executes none
    recorded = next(c for c in cases if c.case_id == "cs-r2")
    traj = impl.replay_case(baseline_unit, recorded)
    served_from_record = (not isinstance(traj, Problem)
                          and any(s["kind"] == "observation" and s["result"].get("files") == 37
                                  for s in traj.steps))
    check("C3 a recorded effect is served from the record, not executed",
          served_from_record and base.served_effects >= 1 and base.executed_effects == 0,
          f"served={getattr(base, 'served_effects', '?')} executed={getattr(base, 'executed_effects', '?')}")

    # C4 - the regression: the trajectory moves while the answer does not
    cand = impl.evaluate(candidate, case_set_id, BASELINE_ID, correlation_id=CID)
    moved = [t for t in getattr(cand, "transitions", [])]
    named = moved[0].case_id if len(moved) == 1 else ""
    dims = moved[0].dimension_scores if moved else {}
    check("C4 the candidate fails with exactly one transition, and it is named",
          hasattr(cand, "outcome") and cand.outcome == FAILED and named == "cs-r2",
          f"{getattr(cand, 'outcome', '?')}: {[ (t.case_id, t.was, t.now) for t in moved]}")
    check("C4b the failure is on the trajectory, not the final answer",
          dims.get("tool_use") == "fail" and dims.get("task_completion") == "pass",
          json.dumps(dims))

    # C5 - a run that executed nothing
    empty = impl.evaluate(candidate, case_set_id, BASELINE_ID, correlation_id=CID,
                          case_filter="none")
    check("C5 an empty selector reports inconclusive, never passed",
          hasattr(empty, "outcome") and empty.cases_executed == 0
          and empty.outcome == INCONCLUSIVE,
          f"{getattr(empty, 'outcome', '?')} on {getattr(empty, 'cases_executed', '?')} cases")

    # C6 - the gate stage reads the report's counters, never an exit code
    gate = (gate_stage_from_exit_code(empty, "ev-break", 0) if break_gate
            else gate_stage(empty, "ev-conformance"))
    gate_pass = gate_stage(base, "ev-conformance")
    check("C6 a gate over a zero-case report cannot report success",
          gate.status == INCONCLUSIVE and gate.blocks_promotion,
          f"stage={gate.stage} status={gate.status} cases_executed={gate.cases_executed}")
    check("C6b the gate over the passing report reports passed and does not block",
          gate_pass.status == PASSED and not gate_pass.blocks_promotion, gate_pass.status)
    check("C6c the stage record validates against GateStageResult",
          not validate(gate.as_dict(), GATE_SCHEMA), "; ".join(validate(gate.as_dict(), GATE_SCHEMA)))

    # C7 - an effect the record does not hold is refused, never executed
    probe_id, probe_version, probe_cases = load_cases("case-set-unrecorded.json")
    impl.register_case_set(probe_cases, probe_version, probe_id)
    refused = impl.replay_case(baseline_unit, probe_cases[0])
    probe = impl.evaluate(baseline_unit, probe_id, BASELINE_ID, correlation_id=CID)
    check("C7 replay refuses an unrecorded effect with typed problem details",
          isinstance(refused, Problem) and refused.type.endswith("unrecorded-effect")
          and refused.status == 422, getattr(refused, "type", type(refused).__name__))
    check("C7b the refusal fails the case and executes nothing",
          hasattr(probe, "outcome") and probe.outcome == FAILED
          and probe.unrecorded_effects == 1 and probe.executed_effects == 0,
          f"{getattr(probe, 'outcome', '?')} unrecorded={getattr(probe, 'unrecorded_effects', '?')}")

    # C8 - the rubric body never travels into the unit under test
    markers, leaks = rubric_markers(), 0
    for case in cases:
        t = impl.replay_case(baseline_unit, case)
        if isinstance(t, Problem):
            continue
        body = json.dumps([t.unit_saw, t.steps])
        leaks += sum(m in body for m in markers)
    check("C8 no rubric body reached the unit under test", leaks == 0, f"{leaks} marker(s) seen")

    # C9 - the report pins what it scored, and two runs of it agree
    repeat = impl.evaluate(baseline_unit, case_set_id, BASELINE_ID, correlation_id=CID)
    check("C9 the report pins the unit version beside the corpus digest",
          ok_base and report_pins_versions(base)
          and base.case_set.digest == handle.digest,
          f"{base.unit_under_test.version} / {base.case_set.digest}")
    check("C9b the same corpus and the same unit produce the same report id",
          repeat.report_id == base.report_id, base.report_id)

    # C10 - promoting a baseline appends; the previous one is retained
    before_ids = set(impl.baseline_ids())
    promoted = impl.promote_baseline(base.report_id, "the corpus passed at the pinned version")
    after_ids = set(impl.baseline_ids())
    old_body = impl.load_baseline(BASELINE_ID)
    retained = (BASELINE_ID in after_ids and not isinstance(old_body, Problem)
                and "promoted_from" not in old_body and before_ids <= after_ids)
    check("C10 promote_baseline appends and retains the previous baseline",
          isinstance(promoted, str) and promoted != BASELINE_ID and promoted in after_ids
          and retained, f"{promoted}, {len(after_ids)} baselines, previous intact={retained}")

    # C11 - design assertions: the interface offers no other way in
    check("C11 the interface carries exactly the five operations the core imports",
          interface_operations() == ("evaluate", "promote_baseline", "register_case_set",
                                     "replay_case", "score_trajectory"),
          ", ".join(interface_operations()))
    check("C11b no operation executes an effect", no_execute_operation())
    check("C11c a case has nowhere to put the text it is graded against",
          case_carries_no_rubric_body())

    # C12 - the failure path answers with problem details from a closed registry
    unknown = impl.evaluate(baseline_unit, "cs-does-not-exist", BASELINE_ID, correlation_id=CID)
    no_baseline = impl.evaluate(baseline_unit, case_set_id, "bl-does-not-exist", correlation_id=CID)
    check("C12 an unresolved case set answers with typed problem details",
          isinstance(unknown, Problem) and unknown.type.endswith("case-set-unresolved")
          and unknown.status == 404, getattr(unknown, "type", "?"))
    check("C12b an unregistered problem type falls back rather than being minted",
          isinstance(no_baseline, Problem) and no_baseline.type.endswith("adapter-unavailable"),
          getattr(no_baseline, "type", "?"))

    report = {
        "adapter": impl.name, "role": impl.role, "execution_model": impl.execution_model,
        "trajectory_source": impl.trajectory_source,
        "emit_evaluation_result": impl.emit_evaluation_result,
        "checks_total": len(checks), "checks_passed": sum(1 for _, ok, _ in checks if ok),
        "cases_executed": base.cases_executed, "outcome": base.outcome,
        "transitions": len(base.transitions), "regressed_outcome": cand.outcome,
        "regressed_transitions": len(moved), "transitions_named": [t.case_id for t in moved],
        "unrecorded_effects": probe.unrecorded_effects,
        "executed_effects": base.executed_effects + probe.executed_effects,
        "served_effects": base.served_effects, "digest": handle.digest,
        "report_id": base.report_id, "verdicts": dict(cand.verdicts),
        "gate_status_zero_case": gate.status, "gate_blocks_zero_case": gate.blocks_promotion,
        "rubric_markers_seen_by_unit": leaks, "baseline_retained": retained,
        "selected_by": "configuration", "adapters_run": 1,
    }
    return report, checks


def merge(paths: list[str]) -> tuple[dict, list[tuple[str, bool, str]]]:
    """The swap proof: the identical corpus through two adapters, diffed case by
    case. adapters_run and verdict_divergence are what promote a harness to gating."""
    reports = []
    for path in paths:
        with open(path) as fh:
            reports.append(json.load(fh))
    a, b = reports[0], reports[1]
    agreed = ("cases_executed", "outcome", "transitions", "transitions_named",
              "regressed_outcome", "regressed_transitions", "unrecorded_effects", "executed_effects",
              "served_effects", "digest", "report_id", "verdicts",
              "gate_status_zero_case", "rubric_markers_seen_by_unit")
    divergence = sum(1 for k in agreed if a[k] != b[k])
    per_case = sum(1 for c in set(a["verdicts"]) | set(b["verdicts"])
                   if a["verdicts"].get(c) != b["verdicts"].get(c))
    axes = [ax for ax in ("execution_model", "trajectory_source", "emit_evaluation_result")
            if a[ax] != b[ax]]
    checks = [
        ("S1 both adapters ran the identical registered corpus", a["digest"] == b["digest"], a["digest"]),
        ("S2 every per-case verdict agrees", per_case == 0, f"{per_case} case(s) differ"),
        ("S3 no field a caller reads diverges across the swap", divergence == 0,
         ", ".join(k for k in agreed if a[k] != b[k])),
        ("S4 the pair differs on a declared execution axis", bool(axes), ", ".join(axes) or "none"),
        ("S5 both adapters passed their own conformance run",
         a["checks_passed"] == a["checks_total"] and b["checks_passed"] == b["checks_total"],
         f"{a['checks_passed']}/{a['checks_total']} and {b['checks_passed']}/{b['checks_total']}"),
    ]
    merged = dict(a)
    merged.update(adapters=[a["adapter"], b["adapter"]], adapters_run=len(reports),
                  verdict_divergence=divergence + per_case, axes_differ=axes,
                  checks_total=len(checks), checks_passed=sum(1 for _, ok, _ in checks if ok))
    return merged, checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"), choices=ADAPTERS)
    ap.add_argument("--merge", nargs=2, metavar=("A", "B"))
    ap.add_argument("--break-gate", action="store_true",
                    help="deliberate breakage: the gate reads its status from the exit code")
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        report, checks = merge(args.merge) if args.merge else run(args.adapter, args.break_gate)
    except AdapterUnavailable as exc:
        print("application/problem+json")
        print(json.dumps(exc.problem.as_dict(), indent=2))
        return 2

    label = "merged swap proof" if args.merge else f"adapter={report['adapter']}"
    for name, ok, detail in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"   [{detail}]" if detail else ""))
    errs = validate(report, REPORT_SCHEMA)
    for err in errs:
        print(f"  FAIL report shape: {err}")
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
    passed = sum(1 for _, ok, _ in checks if ok)
    ok = passed == len(checks) and not errs
    print(f"conformance {'PASSED' if ok else 'FAILED'}: {passed}/{len(checks)} cases, {label}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
