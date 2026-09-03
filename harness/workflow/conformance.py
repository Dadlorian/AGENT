#!/usr/bin/env python3
"""The conformance run every executor must pass. The same nine cases against any
adapter, and the report is what the swap proof compares.

    python3 harness/workflow/conformance.py --adapter dryrun --adapter second

Nothing here reads the run's own account of its side effect: the effect rows are
counted from effects.jsonl by this file, because an effect a run tallies for
itself cannot show the run double-counting it. The executor marker is read back
from the running executor and from the journal it wrote, never from the binding
that selected it - two green runs of the same executor read exactly like a
proven swap otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from call import build_envelope  # noqa: E402

EXPECT_STEPS = 8            # intake, draft#1, judge#1, draft#2, judge#2, gate, publish, notify
EXPECT_SPEND = 165000
KILLED_STEP = "publish"


def flow(out_dir: str, adapter: str, *extra: str, break_idem: bool = False):
    os.makedirs(out_dir, exist_ok=True)
    entry = os.path.join(out_dir, "entry.json")
    if not os.path.exists(entry):
        json.dump(build_envelope(), open(entry, "w"), indent=2)
    result = os.path.join(out_dir, f"result-{len(os.listdir(out_dir))}.json")
    cmd = [sys.executable, os.path.join(HERE, "flow.py"), "--entry", entry,
           "--adapter", adapter, "--out", out_dir, "--result", result, *extra]
    if break_idem:
        cmd.append("--break-idempotency")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    data = json.load(open(result)) if os.path.exists(result) else None
    return proc.returncode, data, proc


def rows(out_dir: str, name: str) -> list[dict]:
    path = os.path.join(out_dir, name)
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def effects_for(out_dir: str, step_id: str) -> int:
    """Count rows for a step by its base id, so a step re-entered after a
    return-with-notes is still the same side effect."""
    return sum(1 for r in rows(out_dir, "effects.jsonl")
               if str(r.get("step_id", "")).split("@")[0] == step_id)


def conform(adapter: str, base: str, break_idem: bool = False) -> dict:
    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, ok: bool, detail: str = "") -> bool:
        checks.append((name, bool(ok), detail))
        return bool(ok)

    def d(case: str) -> str:
        p = os.path.join(base, case)
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p, exist_ok=True)
        return p

    # -- A. crash at the side-effecting step, then resume --------------------
    a = d("a-crash-resume")
    rc1, _, p1 = flow(a, adapter, "--crash-at", KILLED_STEP, break_idem=break_idem)
    chk("A1 the kill landed", rc1 in (-9, 137), f"rc {rc1}")
    orphans = effects_for(a, KILLED_STEP)
    rc2, r2, p2 = flow(a, adapter, break_idem=break_idem)
    chk("A2 the resumed attempt completed", rc2 == 0 and r2 and r2["outcome"] == "completed",
        f"rc {rc2}")
    r2 = r2 or {}
    chk("A3 it resumed at the first incomplete step, not at zero",
        r2.get("resume_point_at_start", 0) > 0, f"resume_point={r2.get('resume_point_at_start')}")
    chk("A4 committed steps were skipped, not re-executed",
        r2.get("steps_replayed", 0) > 0, f"steps_replayed={r2.get('steps_replayed')}")
    chk("A5 the run committed every step exactly once",
        r2.get("steps_committed") == EXPECT_STEPS, f"steps_committed={r2.get('steps_committed')}")
    n_eff = effects_for(a, KILLED_STEP)
    chk("A6 one effect for the killed step, counted from outside", n_eff == 1, f"rows={n_eff}")
    chk("A7 no duplicate effect", max(0, n_eff - 1) == 0, f"duplicates={max(0, n_eff - 1)}")
    chk("A8 the human was asked once across the crash",
        sum(1 for r in rows(a, "journal.jsonl") if r["kind"] == "gate-parked") == 1)
    chk("A9 budget was recomputed from the committed records, not reset",
        r2.get("budget_remaining_micros") == r2.get("budget_ceiling_micros", 0) - EXPECT_SPEND,
        f"remaining={r2.get('budget_remaining_micros')} spent={r2.get('spent_micros')}")
    corrs = {r.get("correlation_id") for r in rows(a, "journal.jsonl") if r.get("correlation_id")}
    chk("A10 one correlation id across the crash, re-attached from the record",
        corrs == {"corr-wf-0001"} and r2.get("correlation_source") == "step-record",
        f"{sorted(corrs)} via {r2.get('correlation_source')}")
    marker = r2.get("executor_marker")
    journal_markers = {r["executor_marker"] for r in rows(a, "journal.jsonl")
                       if "executor_marker" in r}
    chk("A11 the marker was read from the running executor",
        marker and journal_markers == {marker}, f"{marker} vs {sorted(journal_markers)}")
    mode = r2.get("effect_commit_mode")
    gap_ok = (orphans > 0) == (mode == "keyed_effect")
    chk("A12 the executor behaved as its declared gap says",
        gap_ok, f"{mode}: orphan effect rows at the crash = {orphans}")

    # -- B. the bounded loop exits on the judge verdict ----------------------
    loop = r2.get("loop") or {}
    chk("B1 the loop exited on the judge verdict",
        loop.get("terminated_by") == "verdict_pass" and loop.get("termination_class") == "stop",
        str(loop.get("terminated_by")))
    chk("B2 it ran the iterations it needed and no more", loop.get("iterations_run") == 2,
        f"iterations_run={loop.get('iterations_run')}")

    # -- C. the loop's iteration ceiling escalates --------------------------
    c = d("c-loop-ceiling")
    rc, r, _ = flow(c, adapter, "--loop-never-pass", break_idem=break_idem)
    lo = (r or {}).get("loop") or {}
    chk("C1 a loop that never passes stops at its ceiling and escalates",
        rc == 2 and lo.get("terminated_by") == "iteration_ceiling"
        and lo.get("termination_class") == "cap", f"rc {rc} {lo.get('terminated_by')}")
    chk("C2 the cap returns a registered problem type",
        (r or {}).get("problem", {}).get("type") == "urn:agentic:problem:deadline-exceeded",
        str((r or {}).get("problem", {}).get("type")))
    chk("C3 the substitution for the unregistered type is recorded, not invented",
        (lo.get("escalation") or {}).get("proposed_type")
        == "urn:agentic:problem:iteration-ceiling-reached")

    # -- D. the loop's budget ceiling ---------------------------------------
    dd = d("d-loop-budget")
    rc, r, _ = flow(dd, adapter, "--budget-micros", "120000", break_idem=break_idem)
    lo = (r or {}).get("loop") or {}
    chk("D1 a loop that cannot afford its next iteration terminates the unit",
        rc == 2 and lo.get("terminated_by") == "budget_ceiling"
        and (r or {}).get("problem", {}).get("type") == "urn:agentic:problem:budget-exhausted",
        f"rc {rc} {lo.get('terminated_by')}")

    # -- E. the four outcomes, answered by a human, an agent and a schedule --
    for case, dec, want_effects, want_outcome in (
            ("approve", ["approve:user:corey"], 1, "completed"),
            ("edit", ["edit:agent:reviewer-bot"], 1, "completed"),
            ("reject", ["reject:schedule:gate-sweeper"], 0, "stopped-on-reject"),
            ("return", ["return_with_notes:user:corey", "approve:agent:release-bot"], 1,
             "completed")):
        e = d("e-gate-" + case)
        args = [x for dsn in dec for x in ("--decision", dsn)]
        rc, r, _ = flow(e, adapter, *args, break_idem=break_idem)
        ok = rc == 0 and (r or {}).get("outcome") == want_outcome \
            and effects_for(e, KILLED_STEP) == want_effects
        chk(f"E {case} decides the gate and the run continues accordingly", ok,
            f"rc {rc} outcome={(r or {}).get('outcome')} effects={effects_for(e, KILLED_STEP)}")
        if case == "return":
            chk("E return re-entered the named step exactly once",
                (r or {}).get("return_reentered_named_step") == 1
                and (r or {}).get("gates_parked") == 2,
                f"returns={(r or {}).get('return_reentered_named_step')}")

    # -- F. ten deliveries of one decision resume the run once --------------
    f = d("f-deliveries")
    rc, r, _ = flow(f, adapter, "--deliveries", "10", break_idem=break_idem)
    applied = sum(1 for x in rows(f, "journal.jsonl") if x["kind"] == "gate-decided")
    chk("F ten deliveries of one decision resume the run once",
        rc == 0 and (r or {}).get("resumes_per_gate_max") == 1 and applied == 1,
        f"applied={applied}")

    # -- G. the deadline is a cap, and a late decision is a no-op -----------
    g = d("g-expiry")
    rc, r, _ = flow(g, adapter, "--gate-expired", break_idem=break_idem)
    chk("G an undecided gate expires as a typed failure and a late decision is ignored",
        rc == 2 and (r or {}).get("expired_gates") == 1
        and (r or {}).get("late_decisions_applied") == 0
        and (r or {}).get("problem", {}).get("type") == "urn:agentic:problem:deadline-exceeded",
        f"rc {rc} late={(r or {}).get('late_decisions_applied')}")

    # -- H. replaying a finished run runs nothing again ---------------------
    h = d("h-replay")
    flow(h, adapter, break_idem=break_idem)
    before = len(rows(h, "effects.jsonl"))
    rc, r, _ = flow(h, adapter, break_idem=break_idem)
    chk("H replaying a finished run re-executes nothing and appends no effect",
        rc == 0 and (r or {}).get("steps_executed") == 0
        and (r or {}).get("steps_replayed") == EXPECT_STEPS
        and len(rows(h, "effects.jsonl")) == before,
        f"executed={(r or {}).get('steps_executed')} effects={len(rows(h, 'effects.jsonl'))}")

    # -- I. an unreadable record is a typed failure, never a silent restart --
    i = d("i-tamper")
    flow(i, adapter, break_idem=break_idem)
    path = os.path.join(i, "journal.jsonl")
    lines = open(path).read().splitlines()
    hit = next((n for n, l in enumerate(lines) if '"cost_micros": 60000' in l), None)
    chk("I0 the journal had a record to tamper with", hit is not None)
    if hit is not None:
        lines[hit] = lines[hit].replace('"cost_micros": 60000', '"cost_micros": 1')
    open(path, "w").write("\n".join(lines) + "\n")
    rc, r, _ = flow(i, adapter, break_idem=break_idem)
    chk("I a tampered journal refuses with a typed problem instead of restarting",
        rc == 2 and (r or {}).get("problem", {}).get("type")
        == "urn:agentic:problem:idempotency-conflict", f"rc {rc}")

    passed = sum(1 for _, ok, _ in checks if ok)
    return {"adapter": adapter, "executor_marker": marker,
            "binding": r2.get("binding", {}),
            "steps_committed": r2.get("steps_committed"),
            "steps_replayed": r2.get("steps_replayed"),
            "resume_point_at_start": r2.get("resume_point_at_start"),
            "prior_step_ids_seen": r2.get("prior_step_ids_seen"),
            "effects_for_killed_step": n_eff, "duplicate_effects": max(0, n_eff - 1),
            "declared_gap_honoured": gap_ok,
            "budget_remaining_after_resume_micros": r2.get("budget_remaining_micros"),
            "gates_parked": r2.get("gates_parked"),
            "checks_passed": passed, "checks_total": len(checks),
            "failures": [{"check": n, "detail": det} for n, ok, det in checks if not ok],
            "checks": [{"check": n, "ok": ok, "detail": det} for n, ok, det in checks]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the durable-execution conformance suite.")
    ap.add_argument("--adapter", action="append", default=[], required=False)
    ap.add_argument("--out", default=os.path.join(HERE, "out", "conformance"))
    ap.add_argument("--report", default="")
    ap.add_argument("--break-idempotency", action="store_true",
                    help="the deliberate breakage: the step record carries no idempotency key")
    args = ap.parse_args(argv)
    adapters = args.adapter or ["dryrun"]

    per = [conform(a, os.path.join(args.out, a), args.break_idempotency) for a in adapters]
    report = {"adapters_run": len(per), "break_idempotency": args.break_idempotency,
              "per_adapter": per,
              "distinct_markers": sorted({p["executor_marker"] for p in per if p["executor_marker"]})}
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        json.dump(report, open(args.report, "w"), indent=2)

    ok = True
    for p in per:
        for fmark in p["failures"]:
            print(f"  FAIL [{p['adapter']}] {fmark['check']}: {fmark['detail']}")
        print(f"adapter={p['adapter']} executor_marker={p['executor_marker']} "
              f"steps_committed={p['steps_committed']} steps_replayed={p['steps_replayed']} "
              f"effects_for_{KILLED_STEP}={p['effects_for_killed_step']} "
              f"duplicate_effects={p['duplicate_effects']} "
              f"declared_gap_honoured={str(p['declared_gap_honoured']).lower()} "
              f"checks={p['checks_passed']}/{p['checks_total']}")
        ok = ok and not p["failures"]
    print(f"adapters_run={len(per)} distinct_markers={len(report['distinct_markers'])}")
    if len(per) > 1 and len(report["distinct_markers"]) != len(per):
        print("  FAIL the same executor answered twice; that is not a swap")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
