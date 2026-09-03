#!/usr/bin/env python3
"""The improvement-loop conformance run: the same cases against any driver.

  python3 conformance.py --adapter dryrun --report out/before.json
  python3 conformance.py --adapter second --report out/after.json
  python3 conformance.py --merge out/before.json out/after.json --report out/merged.json
  python3 conformance.py --adapter dryrun --break-gate       # the deliberate breakage

Exit 0 when every case passes, 1 when one fails, 2 when the driver refused to be
constructed (problem details are printed, never a traceback). No product name
appears in this file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import fields

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import (DRIVERS, EvaluationAdapter, FAILED, INCONCLUSIVE, IterationRecord,
                       PASSED, REPORT_SCHEMA, TERMINATED_BY, CandidateChange, DriverUnavailable,
                       Gate, GateSpec, LoopSpec, Metric, Problem, Scorecard,
                       candidate_carries_no_criterion, ceiling_is_required,
                       interface_operations, load_driver, load_gate_adapter,
                       no_in_place_edit_operation, promote_on_pass, promote_regardless,
                       records_digest, validate)

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
CID = "d-conformance-0001"
BUDGET, PER_ITERATION = 3_000_000, 250_000


def fixture(name: str = "scorecard.json") -> tuple[Scorecard, list[CandidateChange]]:
    with open(os.path.join(FIXTURES, name)) as fh:
        row = json.load(fh)
    metrics = tuple(Metric(m["metric_id"], m["direction"], float(m["current"]),
                           float(m["target"]), float(m["scale"])) for m in row["metrics"])
    candidates = [CandidateChange(c["candidate_id"], c["metric_id"], GateSpec(**c["gate"]),
                                  float(c["value_if_promoted"]), c["rationale"])
                  for c in row["candidates"]]
    return Scorecard(row["scorecard_id"], metrics), candidates


def drive(driver, loop_id: str, ceiling: int | None, scorecard_id: str, budget: int = BUDGET):
    """Open a loop and run it to termination, one iteration per fire. This is the
    whole driving code: it is identical for every driver, which is the point."""
    spec = LoopSpec(loop_id, ceiling, budget, PER_ITERATION)
    opened = driver.open_loop(spec, scorecard_id)
    if isinstance(opened, Problem):
        return driver, opened, [], None
    records, outcome = [], driver.evaluate_exit(loop_id)
    while outcome is None:
        driver = driver.next_fire()
        before = driver.read_checkpoint(loop_id)
        record = driver.run_iteration(loop_id, correlation_id=CID)
        if isinstance(record, Problem):
            return driver, record, records, None
        records.append((record, before))
        outcome = driver.evaluate_exit(loop_id)
    return driver, opened, records, outcome


def run(adapter_name: str, break_gate: bool, gate_name: str) -> tuple[dict, list[tuple[str, bool, str]]]:
    rule = promote_regardless if break_gate else promote_on_pass
    gate = Gate(load_gate_adapter(gate_name))
    driver = load_driver(adapter_name, gate=gate, decision_rule=rule)
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> bool:
        checks.append((name, bool(ok), detail))
        return bool(ok)

    scorecard, candidates = fixture()

    # C1 - register_scorecard: content digest, stable across two registrations
    handle = driver.register_scorecard(scorecard, candidates)
    again = driver.register_scorecard(scorecard, candidates)
    check("C1 register_scorecard returns a digest, the metrics and the candidates",
          not isinstance(handle, Problem) and handle.metric_count == 3
          and handle.candidate_count == 6, getattr(handle, "digest", str(handle)))
    check("C1b the same scorecard registered twice agrees on the digest",
          handle.digest == again.digest, handle.digest)

    # C2 - a loop with no iteration ceiling is refused before anything runs
    unbounded = driver.open_loop(LoopSpec("il-unbounded", None, BUDGET, PER_ITERATION),
                                 handle.scorecard_id)
    no_state = driver.read_checkpoint("il-unbounded")
    check("C2 a loop declared with no iteration ceiling is refused",
          isinstance(unbounded, Problem) and unbounded.type.endswith("document-invalid")
          and unbounded.status == 422, getattr(unbounded, "detail", str(unbounded))[:110])
    check("C2b the refusal left no loop open and no checkpoint written",
          isinstance(no_state, Problem), getattr(no_state, "type", "a checkpoint exists"))

    # C3 - the loop itself
    driver, opened, records, outcome = drive(driver, "il-scorecard", 8, handle.scorecard_id)
    ok_loop = outcome is not None and not isinstance(opened, Problem)
    rows = [r for r, _ in records]
    check("C3 open_loop writes the checkpoint the first fire resumes from",
          not isinstance(opened, Problem) and opened.iteration_index == 0
          and opened.values == scorecard.values(), getattr(opened, "checkpoint_id", str(opened)))

    # C4 - one iteration works the metric furthest from its target
    picked = [r.metric_id for r in rows]
    furthest_first = bool(rows) and picked[0] == "measured_done_share"
    all_furthest = all(
        r.distance_before >= max(
            (m.distance for m in scorecard.with_values(before.values).metrics
             if m.metric_id != r.metric_id), default=0.0)
        for r, before in records)
    check("C4 the first iteration works the metric furthest from its target, not the first listed",
          furthest_first and scorecard.metrics[0].metric_id == "measured_done_share"
          and picked[:1] != ["proposed_share"], ", ".join(picked))
    check("C4b every iteration works the furthest metric of the checkpoint it resumed from",
          all_furthest, ", ".join(f"{r.metric_id}@{r.distance_before:.2f}" for r in rows))

    # C5 - a failed gate declines and leaves the previous checkpoint in place
    failed = [(r, b) for r, b in records if r.gate_outcome == FAILED]
    held_on_failed = bool(failed) and all(
        r.decision == "declined" and r.reason == "gate_failed"
        and r.checkpoint_id == b.checkpoint_id and not r.checkpoint_advanced for r, b in failed)
    check("C5 a failed gate declines the candidate and leaves the previous checkpoint in place",
          held_on_failed,
          "; ".join(f"{r.candidate_id}: {r.decision}, checkpoint {b.checkpoint_id}->{r.checkpoint_id}"
                    for r, b in failed) or "no gate returned failed")

    # C6 - inconclusive is treated exactly like failed, never silently promoted
    unsure = [(r, b) for r, b in records if r.gate_outcome == INCONCLUSIVE]
    check("C6 an inconclusive gate is treated exactly like a failed one",
          bool(unsure) and all(r.decision == "declined" and r.reason == "gate_inconclusive"
                               and r.checkpoint_id == b.checkpoint_id for r, b in unsure),
          "; ".join(f"{r.candidate_id}: {r.decision}/{r.reason}" for r, b in unsure) or "none seen")

    # C7 - a passed gate promotes, moves the metric and writes a new checkpoint
    passed = [(r, b) for r, b in records if r.gate_outcome == PASSED]
    check("C7 a passed gate promotes the candidate and advances the checkpoint",
          bool(passed) and all(r.decision == "promoted" and r.reason is None
                               and r.checkpoint_advanced and r.checkpoint_id != b.checkpoint_id
                               and r.distance_after <= r.distance_before for r, b in passed),
          f"{len(passed)} promoted")

    # C8 - the loop stops when every target holds
    check("C8 the loop stops when every target holds, on the three-valued termination enum",
          ok_loop and outcome.terminated_by == "verdict_pass"
          and outcome.termination_class == "stop"
          and outcome.targets_held == outcome.targets_total
          and outcome.terminated_by in TERMINATED_BY,
          f"{getattr(outcome, 'terminated_by', '?')} after "
          f"{getattr(outcome, 'iterations_run', '?')} iterations")
    check("C8b the outcome counts what the records say",
          ok_loop and outcome.iterations_run == len(rows)
          and outcome.cost_micros == len(rows) * PER_ITERATION,
          f"{len(rows)} records, cost {getattr(outcome, 'cost_micros', '?')}")

    # C9 - the iteration ceiling caps the loop and escalates
    driver_cap, _, cap_rows, cap_outcome = drive(driver.next_fire(), "il-capped", 2,
                                                 handle.scorecard_id)
    cap_ok = cap_outcome is not None
    check("C9 a loop that runs its ceiling caps and escalates rather than carrying on",
          cap_ok and cap_outcome.terminated_by == "iteration_ceiling"
          and cap_outcome.termination_class == "cap" and cap_outcome.iterations_run == 2
          and cap_outcome.escalation is not None,
          f"{getattr(cap_outcome, 'terminated_by', '?')} after {len(cap_rows)} iterations")
    check("C9b the escalation returns a registered problem type and names the proposed one",
          cap_ok and cap_outcome.escalation["type"].endswith("deadline-exceeded")
          and "iteration-ceiling-reached" in cap_outcome.escalation["detail"],
          cap_ok and cap_outcome.escalation["type"] or "")

    # C10 - the budget ceiling is the third and last way to end
    _, _, bud_rows, bud_outcome = drive(driver_cap.next_fire(), "il-budget", 8,
                                        handle.scorecard_id, budget=600_000)
    check("C10 the budget ceiling ends the loop before an iteration it cannot pay for",
          bud_outcome is not None and bud_outcome.terminated_by == "budget_ceiling"
          and bud_outcome.termination_class == "cap"
          and bud_outcome.cost_micros <= 600_000
          and bud_outcome.escalation["type"].endswith("budget-exhausted"),
          f"{getattr(bud_outcome, 'terminated_by', '?')} at "
          f"{getattr(bud_outcome, 'cost_micros', '?')} micros")

    # C11 - a re-delivered iteration is not a second one
    driver_idem, _, idem_rows, _ = drive(driver.next_fire(), "il-replay", 2, handle.scorecard_id)
    promoted_first = next(r for r, _ in idem_rows if r.decision == "promoted")
    written_before = driver_idem.checkpoints_written()
    standing = driver_idem.read_checkpoint("il-replay")
    replay = driver_idem.run_iteration("il-replay", correlation_id=CID,
                                       idempotency_key=promoted_first.idempotency_key)
    after = driver_idem.read_checkpoint("il-replay")
    check("C11 a re-delivered iteration returns the first record and checkpoints nothing new",
          not isinstance(replay, Problem) and replay.as_dict() == promoted_first.as_dict()
          and after.checkpoint_id == standing.checkpoint_id
          and driver_idem.checkpoints_written() == written_before,
          f"{getattr(replay, 'record_id', str(replay))}, checkpoints "
          f"{written_before}->{driver_idem.checkpoints_written()}")

    # C12 - the gate is the evaluation capability's own interface, unchanged
    check("C12 the gate is the evaluation capability's own adapter, not a second gate",
          isinstance(driver.gate.adapter, EvaluationAdapter)
          and driver.gate.handle.case_set_id == "cs-release-review",
          f"{driver.gate.name}/{driver.gate.handle.case_set_id}")
    check("C12b every record names the gate report that decided it",
          bool(rows) and all(r.report_id.startswith("er-") and r.cases_executed >= 0 for r in rows),
          ", ".join(sorted({r.report_id for r in rows})))

    # C13 - design assertions: the interface offers no other way in
    check("C13 the interface carries exactly the five operations the core imports",
          interface_operations() == ("evaluate_exit", "open_loop", "read_checkpoint",
                                     "register_scorecard", "run_iteration"),
          ", ".join(interface_operations()))
    check("C13b no operation edits a target in place", no_in_place_edit_operation())
    check("C13c a candidate has nowhere to put the criterion it is graded against",
          candidate_carries_no_criterion())
    check("C13d the declaration schema requires an iteration ceiling", ceiling_is_required())

    # C14 - what survives a lost process is what the driver declares
    fresh = load_driver(adapter_name, gate=gate, decision_rule=rule)
    resumed = fresh.read_checkpoint("il-scorecard")
    survived = not isinstance(resumed, Problem)
    check("C14 the driver's declared survives_process_loss is what a fresh binding does",
          survived == driver.survives_process_loss,
          f"declared {driver.survives_process_loss}, a fresh binding "
          f"{'resumed' if survived else 'refused with ' + getattr(resumed, 'type', '?')}")

    # C15 - the failure path answers with problem details from a closed registry
    unknown = driver.run_iteration("il-does-not-exist", correlation_id=CID)
    check("C15 an unknown loop answers with typed problem details, never an exception",
          isinstance(unknown, Problem) and unknown.type.endswith("criterion-unresolvable")
          and unknown.status == 422, getattr(unknown, "type", type(unknown).__name__))
    check("C15b an iteration record carries every field the shape declares",
          bool(rows) and set(rows[0].as_dict()) == {f.name for f in fields(IterationRecord)},
          str(len(fields(IterationRecord))) + " fields")

    report = {
        "adapter": driver.name, "role": driver.role, "execution_model": driver.execution_model,
        "checkpoint_store": driver.checkpoint_store,
        "survives_process_loss": driver.survives_process_loss,
        "promotion_authority": driver.promotion_authority, "gate": driver.gate.name,
        "checks_total": len(checks), "checks_passed": sum(1 for _, ok, _ in checks if ok),
        "iterations_run": outcome.iterations_run if ok_loop else 0,
        "terminated_by": outcome.terminated_by if ok_loop else "iteration_ceiling",
        "termination_class": outcome.termination_class if ok_loop else "cap",
        "metric_order": picked, "gate_outcomes": [r.gate_outcome for r in rows],
        "decisions": [r.decision for r in rows],
        "promoted": sum(1 for r in rows if r.decision == "promoted"),
        "declined": sum(1 for r in rows if r.decision == "declined"),
        "checkpoint_held_on_failed_gate": bool(held_on_failed),
        "checkpoints_written": driver.checkpoints_written(),
        "records_digest": records_digest([r.as_dict() for r in rows]),
        "unbounded_refused_with": getattr(unbounded, "type", "not refused"),
        "cap_terminated_by": cap_outcome.terminated_by if cap_ok else "verdict_pass",
        "cap_escalation_type": cap_outcome.escalation["type"] if cap_ok else "",
        "budget_terminated_by": bud_outcome.terminated_by if bud_outcome else "verdict_pass",
        "cost_micros": outcome.cost_micros if ok_loop else 0,
        "scorecard_digest": handle.digest,
        "replayed_record_is_same": not isinstance(replay, Problem)
        and replay.as_dict() == promoted_first.as_dict(),
        "selected_by": "configuration", "adapters_run": 1,
    }
    return report, checks


def merge(paths: list[str]) -> tuple[dict, list[tuple[str, bool, str]]]:
    """The swap proof: the identical scorecard through two drivers, diffed iteration
    by iteration. adapters_run and record_divergence are what promote a harness to
    gating."""
    reports = []
    for path in paths:
        with open(path) as fh:
            reports.append(json.load(fh))
    a, b = reports[0], reports[1]
    agreed = ("iterations_run", "terminated_by", "termination_class", "metric_order",
              "gate_outcomes", "decisions", "promoted", "declined",
              "checkpoint_held_on_failed_gate", "records_digest", "unbounded_refused_with",
              "cap_terminated_by", "cap_escalation_type", "budget_terminated_by",
              "cost_micros", "scorecard_digest", "replayed_record_is_same")
    divergence = sum(1 for k in agreed if a[k] != b[k])
    axes = [ax for ax in ("execution_model", "checkpoint_store", "survives_process_loss")
            if a[ax] != b[ax]]
    checks = [
        ("S1 both drivers ran the identical registered scorecard",
         a["scorecard_digest"] == b["scorecard_digest"], a["scorecard_digest"]),
        ("S2 the iteration records are identical", a["records_digest"] == b["records_digest"],
         a["records_digest"]),
        ("S3 no field a caller reads diverges across the swap", divergence == 0,
         ", ".join(k for k in agreed if a[k] != b[k])),
        ("S4 the pair differs on a declared execution axis", bool(axes), ", ".join(axes) or "none"),
        ("S5 both drivers passed their own conformance run",
         a["checks_passed"] == a["checks_total"] and b["checks_passed"] == b["checks_total"],
         f"{a['checks_passed']}/{a['checks_total']} and {b['checks_passed']}/{b['checks_total']}"),
    ]
    merged = dict(a)
    merged.update(adapters=[a["adapter"], b["adapter"]], adapters_run=len(reports),
                  record_divergence=divergence, axes_differ=axes,
                  checks_total=len(checks), checks_passed=sum(1 for _, ok, _ in checks if ok))
    return merged, checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"), choices=DRIVERS)
    ap.add_argument("--gate", default=os.environ.get("GATE", "dryrun"))
    ap.add_argument("--merge", nargs=2, metavar=("A", "B"))
    ap.add_argument("--break-gate", action="store_true",
                    help="deliberate breakage: the checkpoint advances whatever the gate said")
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        report, checks = (merge(args.merge) if args.merge
                          else run(args.adapter, args.break_gate, args.gate))
    except DriverUnavailable as exc:
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
