#!/usr/bin/env python3
"""The conformance run every compensation register must pass.

The same cases run against any binding: nothing here knows which register
answered, and every count that matters is taken from outside it - the effect
table for what happened in the world, `head_ordinal` for what became durable
first. Used before and after a swap; the two reports are what proves the
interface held (T-t9-06).

The report is xc-compensation-implement's CompensationConformanceReport:
register, effects_checked, undeclared_class_admitted, records_after_effect,
irreversible_without_mandate, runs_killed, replayed, compensated, unwind_failed,
unwinds_resumed, ways_in_covered, register_observed, adapters_run.

    python3 harness/xc-compensation/conformance.py --register dryrun --report out/before.json
    python3 harness/xc-compensation/conformance.py --register second --report out/after.json

Two counters are deliberately kept apart, because a run in which nothing ever
failed exercises no unwind at all and still exits green (F-a7-03):
`unwind_failed` counts records the corpus left unreversed and is asserted zero;
`unwind_failed_when_destination_refuses` counts the isolated case where a
compensating action is pointed at a destination that will not answer, and is
asserted to be non-zero and typed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from driver import CORPUS, SAGA, Run, envelope, handlers  # noqa: E402
from interface import DeclareEffect, Problem, digest, load_register  # noqa: E402
from store import EffectTable                                        # noqa: E402

WAYS_IN = [("human", "user:corey"), ("event", "service:alerting"),
           ("schedule", "schedule:nightly-fault-sweep"), ("external", "agent:partner-sre-bot")]


def fresh(register_name: str, tag: str):
    out = os.path.join(HERE, "out", "conformance", register_name, tag)
    shutil.rmtree(out, ignore_errors=True)
    return load_register(register_name, out), EffectTable(os.path.join(out, "effects.jsonl"))


def declare_raw(register, run_id: str, **over) -> None:
    """A declaration built by hand, to reach the refusals a driver would not
    let a caller express."""
    base = dict(run_id=run_id, step_id="charge-the-card",
                effect_digest=digest({"step": "charge-the-card"}),
                irreversibility="compensable", idempotency_key="k-" + run_id,
                correlation_id="corr-" + run_id, actor="user:corey", entry_kind="human")
    register.declare_effect(DeclareEffect(**{**base, **over}))


def ordering_violations(register, table) -> int:
    """The assertion this build owns, taken from outside the register: for every
    effect in the world there is a record whose declaration was durable before
    that effect happened, and strictly before the record the effect was sealed
    into. A missing record counts as a violation, because it is the same defect
    seen one step later."""
    bad = 0
    for row in table.forward():
        rec = next((r for r in register.records(row["run_id"])
                    if r.step_id == row["step_id"]), None)
        if rec is None or not rec.declared_at_head:
            bad += 1
            continue
        declared = register.head_ordinal(rec.declared_at_head)
        if declared > register.head_ordinal(row["head_at_commit"]):
            bad += 1                                   # the record came after the effect
        elif rec.committed_at_head and declared >= register.head_ordinal(rec.committed_at_head):
            bad += 1                                   # not strictly earlier than its own seal
    return bad


def unreversed(run, effects) -> int:
    """Effects the unwind left standing in the world. An effect whose record the
    unwind never saw is left here, which is how a declaration written after the
    effect shows up as a number rather than as an opinion."""
    return sum(1 for e in effects
               if e.irreversibility == "compensable" and run.net(e) != 0)


def corpus(register_name: str, rep: dict, cases: list) -> None:
    """One corpus replayed through each of TARGET T6.2's four entries. Each way
    in kills two runs inside an effect and abandons them, and kills one between
    steps and resumes it - so `replayed + compensated` has something to be equal
    to, and no way in is exercised only on the path someone remembered."""
    orders, kinds = [], set()
    for kind, actor in WAYS_IN:
        register, table = fresh(register_name, f"corpus-{kind}")
        # 1. killed inside an effect, then abandoned: failed
        failed = Run(register, table, envelope(kind, f"run-failed-{kind}", actor))
        failed.run(CORPUS, commit_upto=5, kill="inside-effect")
        r1 = failed.unwind("failed")
        # 2. killed inside an effect, then abandoned: cancelled mid-flight
        cancelled = Run(register, table, envelope(kind, f"run-cancelled-{kind}", actor))
        cancelled.run(SAGA, commit_upto=4, kill="inside-effect")
        r2 = cancelled.unwind("cancelled")
        # 3. killed between steps, then resumed: the sealed responses are replayed
        resumed = Run(register, table, envelope(kind, f"run-resumed-{kind}", actor))
        resumed.run(CORPUS, commit_upto=7, kill="between-steps")
        replayed = resumed.replay()
        before = len(table.forward(resumed.run_id))
        for e in CORPUS:                                    # the resumed attempt re-runs nothing
            if any(r.step_id == e.step_id and r.sealed_response_ref
                   for r in register.records(resumed.run_id)):
                continue
            resumed.commit(e)
        after = len(table.forward(resumed.run_id))

        rep["runs_killed"] += 3
        rep["compensated"] += r1.compensated + r2.compensated
        rep["replayed"] += len(replayed)
        rep["unwind_failed"] += (r1.unwind_failed + r2.unwind_failed
                                 + unreversed(failed, CORPUS[:5]) + unreversed(cancelled, SAGA[:4]))
        rep["killed_run_effects"] += (len(table.forward(failed.run_id))
                                      + len(table.forward(cancelled.run_id)) + before)
        rep["effects_checked"] += len(table.forward())
        rep["records_after_effect"] += ordering_violations(register, table)
        for r in register.records(failed.run_id):
            kinds.add(r.entry_kind)                         # read from the record, not the loop
            rep["register_observed"] = r.register_observed
        orders.append((kind, r1.order, r2.order))
        cases.append(("ok" if after == before else "FAIL",
                      f"[{kind}] resumed run replayed {len(replayed)} sealed responses and "
                      f"committed no second effect ({before} effect rows before, {after} after)"))
        cases.append(("ok" if r1.compensated == 5 and r1.unwind_failed == 0 else "FAIL",
                      f"[{kind}] failed run: {r1.compensated} compensations ran in reverse order, "
                      f"{r1.not_required} not required, {r1.unwind_failed} failed"))
        cases.append(("ok" if r2.order == [e.step_id for e in SAGA][::-1] else "FAIL",
                      f"[{kind}] cancelled mid-flight unwinds the same way: {r2.order[0]} first"))
    rep["ways_in_covered"] = len(kinds)
    same = all(o[1] == orders[0][1] and o[2] == orders[0][2] for o in orders)
    cases.append(("ok" if same else "FAIL",
                  "the four entries produce one identical unwind order; nothing branched on the door"))


def run(register_name: str) -> tuple[list, dict]:
    cases: list[tuple[str, str]] = []
    rep = {"register": register_name, "effects_checked": 0, "undeclared_class_admitted": 0,
           "records_after_effect": 0, "irreversible_without_mandate": 0, "runs_killed": 0,
           "replayed": 0, "compensated": 0, "unwind_failed": 0, "unwinds_resumed": 0,
           "ways_in_covered": 0, "register_observed": "", "killed_run_effects": 0,
           "unwind_failed_when_destination_refuses": 0, "adapters_run": 1}

    def case(text: str):
        def wrap(fn):
            try:
                cases.append((fn(), text))
            except AssertionError as exc:
                cases.append(("FAIL", f"{text} -- {exc}"))
            except Problem as exc:                      # a register that would not answer
                cases.append(("FAIL", f"{text} -- {exc.body['type']}: {exc.body['detail']}"))
            return fn
        return wrap

    reg0, _ = fresh(register_name, "refusals")

    @case("an effect-committing step with no irreversibility class is refused, 422, before the run")
    def _():
        try:
            declare_raw(reg0, "run-no-class", irreversibility=None)
            rep["undeclared_class_admitted"] += 1
            return "FAIL"
        except Problem as p:
            assert p.body["status"] == 422 and p.body["type"].endswith("document-invalid"), p.body
            return "ok"

    @case("a class outside the three members is refused, 422; there is no fourth")
    def _():
        try:
            declare_raw(reg0, "run-bad-class", irreversibility="probably-fine")
            rep["undeclared_class_admitted"] += 1
            return "FAIL"
        except Problem as p:
            assert p.body["status"] == 422, p.body
            return "ok"

    @case("compensable with no compensating action is refused, 422")
    def _():
        try:
            declare_raw(reg0, "run-no-action")
            return "FAIL"
        except Problem as p:
            assert p.body["status"] == 422, p.body
            return "ok"

    @case("irreversible with no mandate is refused, 403, with a rule id and no compensation")
    def _():
        try:
            declare_raw(reg0, "run-no-mandate", irreversibility="irreversible",
                        step_id="send-the-receipt-email")
            rep["irreversible_without_mandate"] += 1
            return "FAIL"
        except Problem as p:
            assert p.body["status"] == 403, p.body
            assert p.body["rule_id"] == "compensation.irreversible-requires-mandate", p.body
            return "ok"

    @case("irreversible with a compensating action is refused: that class produces a gate")
    def _():
        from interface import CompensatingAction
        try:
            declare_raw(reg0, "run-irrev-action", irreversibility="irreversible",
                        mandate_ref="mandate:x", compensating_action=CompensatingAction(
                            "mail.unsend", "step.out.ref", "k-unsend"))
            return "FAIL"
        except Problem as p:
            assert p.body["status"] == 422, p.body
            return "ok"

    # The corpus: four entries, three killed runs each.
    corpus(register_name, rep, cases)

    @case("a reversible effect is not-required and an irreversible one is unreachable in the plan")
    def _():
        register, table = fresh(register_name, "classes")
        r = Run(register, table, envelope("schedule", "run-classes", "schedule:sweep"))
        r.run(CORPUS[5:], commit_upto=2)
        plan = register.unwind_plan(r.run_id)
        assert [p["step_id"] for p in plan.unreachable] == ["send-the-receipt-email"], plan
        assert plan.would_unwind[0]["step_id"] == "write-the-sweep-report", plan
        report = r.unwind("failed")
        assert report.compensated == 0 and report.not_required == 2, report
        assert r.net(CORPUS[6]) == 1, "an irreversible effect stays in the world"
        return "ok"

    @case("an interrupted unwind resumes and does not run an already-compensated record twice")
    def _():
        register, table = fresh(register_name, "resumed-unwind")
        r = Run(register, table, envelope("human", "run-interrupted", "user:corey"))
        r.run(SAGA, commit_upto=5, kill="inside-effect")
        first = r.unwind("failed", stop_after=2)
        assert first.interrupted and first.compensated == 2, first
        second = r.unwind("failed")                       # the same unwinder, continuing
        rep["unwinds_resumed"] += 1
        assert second.already_compensated == 2, second
        assert second.compensated == 3, second
        keys = [row["key"] for row in table.compensations(r.run_id)]
        assert len(keys) == len(set(keys)) == 5, keys     # each compensation ran exactly once
        assert all(r.net(e) == 0 for e in SAGA), "every compensable effect is reversed"
        return "ok"

    @case("a compensating action whose destination will not answer is typed, and names its causes")
    def _():
        register, table = fresh(register_name, "unwind-failed")
        r = Run(register, table, envelope("external", "run-refused", "agent:partner-sre-bot"))
        r.handlers = handlers(table, fail_operator="payments.void")   # one destination is down
        register.register_handlers(r.handlers)
        r.run(SAGA, commit_upto=3)
        report = r.unwind("failed")
        rep["unwind_failed_when_destination_refuses"] += report.unwind_failed
        assert report.unwind_failed == 1, report
        assert report.problem["status"] == 503 and report.problem["retryable"], report.problem
        assert report.problem["type"].endswith("adapter-unavailable"), report.problem
        assert "compensation-unresolved" in report.problem["detail"], report.problem
        assert report.problem["causes"][0]["operator"] == "payments.void", report.problem
        rec = next(x for x in register.records(r.run_id) if x.step_id == "charge-the-card")
        assert rec.state == "unwind-failed", rec
        return "ok"

    @case("the declared gap is honoured: a process that declared nothing unwinds, or is refused")
    def _():
        register, table = fresh(register_name, "cold-reader")
        r = Run(register, table, envelope("human", "run-cold", "user:corey"))
        r.run(SAGA, commit_upto=3)
        cold = load_register(register_name, register.out_dir)          # same store, no handlers
        try:
            report = cold.unwind(r.run_id, "cancelled", executor=r.dispatch)
            assert register.unwinds_from_cold_reader, "unwound without declaring it could"
            assert report.compensated == 3, report
            return "ok"
        except Problem as p:
            assert not register.unwinds_from_cold_reader, p.body
            assert p.body["status"] == 503, p.body
            return "ok"

    @case("the record and the plan carry no criterion, and neither does an unwind failure")
    def _():
        register, table = fresh(register_name, "no-criterion")
        r = Run(register, table, envelope("human", "run-leak-check", "user:corey"))
        r.run(SAGA, commit_upto=2)
        report = r.unwind("failed")
        blob = json.dumps([x.dict() for x in register.records(r.run_id)]
                          + [report.dict()]).lower()
        for word in ("criterion", "definition_of_done", "rubric", "grading"):
            assert word not in blob, f"{word} travels on a compensation record (F-b1-07)"
        return "ok"

    @case("the register's own records are append-only: the chain verifies and nothing was edited")
    def _():
        register, table = fresh(register_name, "append-only")
        r = Run(register, table, envelope("human", "run-appendonly", "user:corey"))
        r.run(SAGA, commit_upto=3)
        r.unwind("failed")
        assert register.log.verify() is None, register.log.verify()
        declares = [x for x in register.log.records if x.get("kind") == "declare"]
        outcomes = [x for x in register.log.records if x.get("kind") == "outcome"]
        assert len(declares) == 5 and len(outcomes) >= 3, (len(declares), len(outcomes))
        return "ok"

    @case("both registers walk one identical order over the same corpus")
    def _():
        orders = []
        for name in ("dryrun", "second"):
            register, table = fresh(name, "cross-order")
            r = Run(register, table, envelope("human", "run-cross", "user:corey"))
            r.run(CORPUS, commit_upto=5, kill="inside-effect")
            orders.append((name, r.unwind("failed").order))
        rep["adapters_run"] = 2                    # both were run, whatever they answered
        assert orders[0][1] == orders[1][1], orders
        return "ok"

    rep["cases_run"] = len(cases)
    rep["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    rep["binding_report"] = load_register(register_name, os.path.join(HERE, "out")).binding()
    rep["selected_by"] = "configuration"
    return cases, rep


ASSERTIONS = [
    ("effects_checked > 0", lambda r: r["effects_checked"] > 0),
    ("undeclared_class_admitted == 0", lambda r: r["undeclared_class_admitted"] == 0),
    ("records_after_effect == 0", lambda r: r["records_after_effect"] == 0),
    ("irreversible_without_mandate == 0", lambda r: r["irreversible_without_mandate"] == 0),
    ("runs_killed > 0", lambda r: r["runs_killed"] > 0),
    ("unwind_failed == 0", lambda r: r["unwind_failed"] == 0),
    ("unwinds_resumed >= 1", lambda r: r["unwinds_resumed"] >= 1),
    ("ways_in_covered == 4", lambda r: r["ways_in_covered"] == 4),
    ("replayed + compensated == effects committed by killed runs",
     lambda r: r["replayed"] + r["compensated"] == r["killed_run_effects"]),
    ("a refused destination was observed, typed",
     lambda r: r["unwind_failed_when_destination_refuses"] >= 1),
    ("adapters_run >= 2", lambda r: r["adapters_run"] >= 2),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the compensation interface.")
    ap.add_argument("--register", action="append", default=[], choices=("dryrun", "second", "live"))
    ap.add_argument("--report", help="write the report JSON here")
    args = ap.parse_args(argv)

    reports, failures = [], 0
    for name in args.register or ["dryrun"]:
        cases, rep = run(name)
        print(f"# register {name} ({rep['binding_report']['register_marker']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        for text, check in ASSERTIONS:
            ok = check(rep)
            print(f"  {'ok' if ok else 'FAIL':4} {text}")
            failures += 0 if ok else 1
        failures += rep["cases_run"] - rep["cases_passed"]
        print("  register={register} effects_checked={effects_checked} "
              "undeclared_class_admitted={undeclared_class_admitted} "
              "records_after_effect={records_after_effect} "
              "irreversible_without_mandate={irreversible_without_mandate} "
              "runs_killed={runs_killed} replayed={replayed} compensated={compensated} "
              "unwind_failed={unwind_failed} unwinds_resumed={unwinds_resumed} "
              "ways_in_covered={ways_in_covered} register_observed={register_observed}"
              .format(**rep))
        reports.append(rep)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} register(s), adapters_run={max(r['adapters_run'] for r in reports)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
