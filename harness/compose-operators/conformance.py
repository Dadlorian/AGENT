#!/usr/bin/env python3
"""The conformance run every engine must pass, and the report the swap proof
compares.

    python3 harness/compose-operators/conformance.py --engine dryrun --engine second

One composition - examples/end-to-end/workflows/triage-and-fix.json, which uses
every operator exactly once - is driven through every engine named, from the
same entry envelope, and the report is the operator-binding-report
compose-operators-implement asks for: the operator names read from the schema,
the operator names read from each running engine, the step order each produced,
its terminal outcome, and the symmetric difference between the two op sets.

Two things are read from the running engine rather than from the binding record
that selected it: `engine_marker` (a report that names the adapter it asked for
cannot catch a fallback that ran both legs on one engine) and `executor_ops`
(an operator set written twice drifts, and the drift is silent because each
copy is internally consistent).

Python 3.11 standard library only. No product name appears in this file.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXAMPLE = os.path.join(ROOT, "examples", "end-to-end")
for path in (HERE, EXAMPLE, os.path.join(HERE, "adapters")):
    if path not in sys.path:
        sys.path.insert(0, path)

import run as runner                                                   # noqa: E402
from call import build_envelope                                        # noqa: E402
from interface import (Problem, is_typed, load_engine, operator_names)  # noqa: E402

WORKFLOW = os.path.join(EXAMPLE, "workflows", "triage-and-fix.json")
SCHEMA = os.path.join(EXAMPLE, "schemas", "workflow.schema.json")
AGENTS = os.path.join(EXAMPLE, "agents.json")

SENTINEL = "a-token-no-profile-emits"          # the criterion body, mounted nowhere
SENTINEL_REF = "criterion://never-pass/v1"
def engine_words() -> tuple[str, ...]:
    """The engine names this run knows about, read from the adapter classes
    themselves rather than typed here: a document that names any of them, or any
    endpoint, has stopped being the portable artifact. Typing the names into
    this file would put a product name above the adapter boundary as well."""
    import importlib
    from interface import ADAPTERS
    words = set()
    for name in ADAPTERS:
        marker = importlib.import_module(f"adapters.{name}").Adapter.engine_marker
        words |= {marker, marker.split("/")[0]}
    return tuple(sorted(words | {"http"}))
STAMPS = ("correlation_id", "actor", "delegation_depth", "idempotency_key",
          "step_idempotency_key", "budget_remaining_micros", "engine_marker")


class Recording:
    """A dispatch adapter that remembers everything the unit was allowed to read,
    so a criterion leak is counted from outside the unit rather than asserted."""

    name = "recording"

    def __init__(self):
        self.inner, self.seen = runner.DryRunAdapter(), []

    def complete(self, profile, task, step_input, correlation):
        self.seen.append({"profile": profile["name"], "task": task,
                          "input": json.dumps(step_input), "tools": profile.get("tools", [])})
        return self.inner.complete(profile, task, step_input, correlation)


def fixtures():
    return (json.load(open(SCHEMA)), json.load(open(WORKFLOW)),
            {a["name"]: a for a in json.load(open(AGENTS))["agents"]})


def variant(doc, kind):
    v = copy.deepcopy(doc)
    if kind == "outside-the-set":
        v["root"]["steps"].append({"op": "branch", "id": "pick", "cases": []})
    elif kind == "unbounded":
        for step in v["root"]["steps"]:
            if step["op"] == "loop":
                step.pop("max_iterations")
    elif kind == "sentinel-criterion":
        for step in v["root"]["steps"]:
            if step["op"] == "loop":
                step["body"]["steps"][1]["criterion_ref"] = SENTINEL_REF
    return v


def chained(engine, doc):
    """The same composition written as chained calls instead of read from a
    file. compose() refuses an operator outside the closed set here too, before
    anything is priced or dispatched."""
    step = doc["root"]["steps"]
    root = {"op": "sequence", "id": "root", "steps": [
        step[0],
        {"op": "parallel", "id": "decompose", "branches": step[1]["branches"]},
        {"op": "loop", "id": "fix-loop", "max_iterations": step[2]["max_iterations"],
         "exit_when": step[2]["exit_when"], "body": step[2]["body"]},
        step[3], step[4], step[5]]}
    return engine.compose(root, doc["name"], doc.get("description", ""))


def new_engine(name, out_dir, schema, extra_ops=(), dispatch=None):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    return load_engine(name, schema, out_dir, runner.validate,
                       extra_ops=extra_ops, dispatch=dispatch)


def ledger_rows(out_dir):
    rows = []
    for name in os.listdir(out_dir):
        if name.endswith("-ledger.jsonl"):
            rows += [json.loads(line) for line in open(os.path.join(out_dir, name))]
    return rows


def conform(name: str, base: str, break_drift: bool = False) -> dict:
    schema, doc, agents = fixtures()
    checks: list[tuple[str, bool, str]] = []
    extra = ("branch",) if (break_drift and name == "dryrun") else ()

    def chk(label, ok, detail=""):
        checks.append((label, bool(ok), str(detail)))
        return bool(ok)

    def case(tag):
        return os.path.join(base, tag)

    # -- A. the binding: the schema is the only place the set is written -----
    engine = new_engine(name, case("a-binding"), schema, extra_ops=extra)
    schema_ops = engine.schema_ops()
    executor_ops = engine.executor_ops()
    drift = sorted(set(schema_ops) ^ set(executor_ops))
    chk("A1 the operator set read from the schema has six members",
        len(schema_ops) == 6, ",".join(schema_ops))
    chk("A2 the running engine dispatches exactly the operators the schema admits",
        not drift, f"drift={drift}")
    chk("A3 the closed set is read from the schema, not retyped in this harness",
        operator_names(schema) == schema_ops)
    chk("A4 the document validates against the operator schema", not engine.validate_workflow(doc),
        f"errors={len(engine.validate_workflow(doc))}")

    # -- B. one run of the composition, from one entry envelope --------------
    rec = Recording()
    run_dir = case("b-run")
    engine = new_engine(name, run_dir, schema, extra_ops=extra, dispatch=rec)
    envelope = build_envelope()
    parked = engine.start(envelope, doc, agents)
    chk("B1 the run parked at the approval operator rather than deciding for the human",
        parked.outcome == "parked" and parked.parked.step_id == "ship-approval",
        f"{parked.outcome}")
    deliveries = [engine.resume(parked.parked.gate_id, "approve", "delivery-1")
                  for _ in range(10)]
    done = deliveries[0]
    ignored = sum(d.duplicate_deliveries_ignored for d in deliveries)
    chk("B2 the run completed", done.outcome == "completed", done.outcome)
    ops = tuple(sorted(set(parked.operators_exercised) | set(done.operators_exercised)))
    chk("B3 every operator in the closed set was exercised exactly by this one document",
        set(ops) == set(schema_ops), f"operators_exercised={len(ops)}: {','.join(ops)}")
    chk("B4 ten deliveries of one decision resume the run once",
        done.gates_decided == 1 and ignored == 9, f"decided={done.gates_decided} ignored={ignored}")
    rows = ledger_rows(run_dir)
    missing = [r["kind"] for r in rows if any(s not in r for s in STAMPS)]
    chk("B5 every step record carries correlation, actor, budget and its own step key",
        not missing, f"records missing a stamp: {missing}")
    keys = {r["step_idempotency_key"] for r in rows if r.get("step_id", "-") != "-"}
    chk("B6 a step key is per step, not the run key reused",
        len(keys) > 1 and envelope["idempotency_key"] not in keys, f"{len(keys)} distinct")
    markers = {r["engine_marker"] for r in rows}
    chk("B7 the marker on every record is the one the running engine reports",
        markers == {engine.engine_marker}, f"{sorted(markers)} vs {engine.engine_marker}")
    selected = {**parked.agents, **done.agents}
    declared = {n["id"]: n["agent"] for n, _d in engine._walk(doc["root"]) if n["op"] == "agent"}
    chk("B8 every agent step selected the profile the document declares",
        all(declared[sid.split("#")[0]] == profile for sid, profile in selected.items()),
        f"{len(selected)} agent steps")
    verdicts = {**parked.verdicts, **done.verdicts}
    chk("B9 the judge graded each iteration and the verdicts are the same both times",
        verdicts == {"fix-judge#1": "fail", "fix-judge#2": "pass"}, str(verdicts))
    loop = [t for t in parked.terminations if t.step_id == "fix-loop"]
    chk("B10 the loop terminated on the judge verdict, bounded",
        len(loop) == 1 and loop[0].reason == "verdict_pass" and loop[0].outcome == "success"
        and loop[0].iterations_run == 2 and loop[0].unbounded is False,
        str(loop[0].__dict__ if loop else None))
    spent = parked.spent_micros + 0
    chk("B11 the budget was decremented from the entry ceiling, step by step",
        done.spent_micros > spent > 0
        and done.spent_micros < envelope["budget"]["ceiling_micros"],
        f"parked at {spent}, completed at {done.spent_micros}")

    # -- C. the loop's other two termination reasons -------------------------
    leak_rec = Recording()
    ceiling_dir = case("c-iteration-ceiling")
    engine_c = new_engine(name, ceiling_dir, schema, extra_ops=extra, dispatch=leak_rec)
    capped = engine_c.start(build_envelope(), variant(doc, "sentinel-criterion"), agents)
    term = capped.terminations[0] if capped.terminations else None
    chk("C1 a loop that never passes stops at its declared ceiling and escalates",
        capped.outcome == "refused" and term and term.reason == "iteration_ceiling"
        and term.outcome == "escalated" and term.iterations_run == 3
        and term.unbounded is False, f"{capped.outcome} {term and term.reason}")
    chk("C2 the cap is a typed failure, not a quiet completion",
        is_typed(capped.problem)
        and capped.problem["type"] == "urn:agentic:problem:deadline-exceeded",
        str(capped.problem and capped.problem["type"]))
    readable = " ".join(x["task"] + x["input"] + json.dumps(x["tools"])
                        for x in leak_rec.seen)
    leaks = readable.count(SENTINEL) + readable.count(SENTINEL_REF)
    chk("C3 the criterion body and its handle reached nothing the graded unit could read",
        leaks == 0, f"criterion_leaks={leaks} over {len(leak_rec.seen)} agent turns")
    chk("C3b the verdict travelled to the next iteration where the criterion did not",
        any("previous_verdict" in x["input"] for x in leak_rec.seen),
        "the retried step saw a verdict and never the criterion")
    in_ledger = json.dumps(ledger_rows(ceiling_dir)).count(SENTINEL)
    chk("C3c the criterion body reaches the ledger, which is recorded, not asserted away",
        in_ledger > 0, f"the imported judge writes its reason into {in_ledger} records "
                       f"(see README, deviations)")
    budget_dir = case("d-budget-ceiling")
    engine_d = new_engine(name, budget_dir, schema, extra_ops=extra)
    tight = build_envelope()
    tight["budget"]["ceiling_micros"] = 400000
    broke = engine_d.start(tight, doc, agents)
    bterm = [t for t in broke.terminations if t.reason == "budget_ceiling"]
    chk("C4 a loop that cannot afford its next iteration terminates on the budget ceiling",
        broke.outcome == "refused" and bterm and bterm[0].outcome == "escalated"
        and broke.problem["type"] == "urn:agentic:problem:budget-exhausted",
        f"{broke.outcome} {[t.reason for t in broke.terminations]}")
    reasons = {t.reason for t in list(parked.terminations) + list(capped.terminations)
               + list(broke.terminations)}
    chk("C5 no run reported a termination reason outside the closed vocabulary",
        reasons <= {"verdict_pass", "iteration_ceiling", "budget_ceiling",
                    "tolerate_exceeded", "approval_rejected"}, str(sorted(reasons)))
    chk("C6 the failure was reported where this engine declares it can report one",
        set(broke.locus or {}) == ({"path"} if engine.failure_locus == "tree-position"
                                   else {"state", "transition"}), str(broke.locus))

    # -- D. the four decisions the approval operator declares ----------------
    outcomes = {}
    for decision, want in (("approve", "completed"), ("edit", "completed"),
                           ("reject", "stopped-on-reject")):
        d_dir = case("e-gate-" + decision)
        eng = new_engine(name, d_dir, schema, extra_ops=extra)
        park = eng.start(build_envelope(), doc, agents)
        out = eng.resume(park.parked.gate_id, decision, "delivery-1")
        after_gate = [r for r in out.ledger if r.get("step_id") == "regression"]
        outcomes[decision] = out.outcome
        chk(f"D {decision} decides the gate and the composition continues accordingly",
            out.outcome == want and bool(after_gate) == (decision != "reject"),
            f"{out.outcome}, steps after the gate: {len(after_gate)}")
    r_dir = case("e-gate-return")
    eng = new_engine(name, r_dir, schema, extra_ops=extra)
    park = eng.start(build_envelope(), doc, agents)
    returned = eng.resume(park.parked.gate_id, "return_with_notes", "delivery-1",
                          note="tighten the regression test")
    final = eng.resume(returned.parked.gate_id, "approve", "delivery-2")
    reruns = [r for r in returned.ledger if r.get("step_id") == "brief"]
    chk("D return_with_notes re-entered the named step exactly once and parked again",
        returned.reentered_step == "brief" and len(reruns) == 1
        and returned.outcome == "parked" and returned.gates_parked == 2,
        f"reentered={returned.reentered_step} parked={returned.gates_parked}")
    chk("D the returned work then completed on the second decision",
        final.outcome == "completed" and final.gates_decided == 2, final.outcome)

    # -- E. refusals, before anything is priced or dispatched ----------------
    ref_dir = case("f-refusals")
    eng = new_engine(name, ref_dir, schema, extra_ops=extra)
    for tag, label in (("outside-the-set", "an operator outside the closed set"),
                       ("unbounded", "a loop with no ceiling")):
        try:
            eng.start(build_envelope(), variant(doc, tag), agents)
            chk(f"E {label} is refused", False, "it was admitted")
        except Problem as refused:
            wrote = [f for f in os.listdir(ref_dir) if f.endswith("-ledger.jsonl")]
            chk(f"E {label} is refused with a typed problem, before pricing and dispatch",
                is_typed(refused.body)
                and refused.body["type"] == "urn:agentic:problem:document-invalid"
                and not wrote, f"{refused.body['type']}, ledger files written: {len(wrote)}")
    try:
        eng.compose({"op": "branch", "id": "pick", "cases": []}, "chained-form")
        chk("E the chained-call form refuses the same operator", False, "it was composed")
    except Problem as refused:
        chk("E the chained-call form refuses the same operator, naming the step",
            refused.body.get("step_id") == "pick", refused.body["detail"][:60])
    unbounded = sum(1 for _n, _d in eng._walk(doc["root"])
                    if _n["op"] == "loop" and "max_iterations" not in _n)
    chk("E no admitted loop is unbounded", unbounded == 0, f"unbounded={unbounded}")

    # -- F. the document operations every engine shares ----------------------
    from_file = eng.to_graph(doc)
    from_calls = eng.to_graph(chained(eng, doc))
    chk("F1 the graph of the document equals the graph of the chained-call form",
        from_file.key() == from_calls.key(),
        f"{len(from_file.nodes)} nodes, {len(from_file.edges)} edges")
    try:
        eng.to_graph(doc, depth_bound=2)
        chk("F2 the depth bound is checked when the document is resolved", False, "not checked")
    except Problem as refused:
        chk("F2 the depth bound is checked when the document is resolved, naming the step",
            refused.body.get("depth_bound_checked_at") == "resolve"
            and refused.body.get("step_id"), refused.body["detail"][:60])
    priced = eng.price(doc, agents, runner.COST_MICROS)
    flat_total = runner.plan(doc, agents, envelope)[1]
    chk("F3 every parent's estimate is the sum of its children's contributions",
        priced.reconciles() and priced.estimate_micros == flat_total,
        f"root={priced.estimate_micros} planner={flat_total}")
    view = eng.step_of(doc, "fix-loop")
    chk("F4 a reader can walk the control flow without reading the work",
        view["op"] == "loop" and view["slots"]["body"] == ["attempt"]
        and "task" not in json.dumps(view["fields"]), str(view["slots"]))
    caller = eng.resolved_default(doc, "ship-approval", "on_reject")
    platform = eng.resolved_default(doc, "ship-approval", "budget")
    chk("F5 every resolved value names exactly one layer it came from",
        caller.resolved_from == "caller" and platform.resolved_from == "platform"
        and platform.value == "decrement_per_step_from_entry_ceiling",
        f"{caller.value} from {caller.resolved_from}; {platform.resolved_from}")

    # -- G. hygiene -----------------------------------------------------------
    text = json.dumps([doc, variant(doc, "sentinel-criterion"),
                       chained(eng, doc)]).lower()
    hits = [w for w in engine_words() if w in text]
    chk("G1 no engine name and no endpoint appears in any document under test",
        not hits, f"hits={hits} against {len(engine_words())} known markers")
    bodies = [capped.problem, broke.problem]
    chk("G2 every failure body is a row in the closed problem registry",
        all(is_typed(b) for b in bodies), str([b["type"] for b in bodies]))

    step_order = parked.step_order() + done.step_order()
    passed = sum(1 for _l, ok, _d in checks if ok)
    return {"engine": name, "engine_marker": engine.engine_marker,
            "binding": engine.binding(), "schema_ops": list(schema_ops),
            "executor_ops": list(executor_ops), "drift": drift,
            "operators_exercised": len(ops), "operators": list(ops),
            "step_order": step_order, "terminal_outcome": done.outcome,
            "loop_termination": [t.__dict__ for t in parked.terminations],
            "ceiling_termination": [t.__dict__ for t in capped.terminations],
            "budget_termination": [t.__dict__ for t in broke.terminations],
            "verdicts": verdicts, "agents_selected": selected,
            "parked_step": parked.parked.step_id, "gate_decisions": outcomes,
            "spent_micros": done.spent_micros, "criterion_leaks": leaks,
            "unbounded": unbounded, "failure_locus": engine.failure_locus,
            "checks_passed": passed, "checks_total": len(checks),
            "failures": [{"check": l, "detail": d} for l, ok, d in checks if not ok],
            "checks": [{"check": l, "ok": ok, "detail": d} for l, ok, d in checks]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the operator conformance suite.")
    ap.add_argument("--engine", action="append", default=[])
    ap.add_argument("--out", default=os.path.join(HERE, "out", "conformance"))
    ap.add_argument("--report", default="")
    ap.add_argument("--break-drift", action="store_true",
                    help="the deliberate breakage: register an operator arm in the "
                         "interpreted engine that the schema does not admit")
    args = ap.parse_args(argv)
    engines = args.engine or ["dryrun"]

    per = []
    for name in engines:
        try:
            per.append(conform(name, os.path.join(args.out, name), args.break_drift))
        except Problem as problem:
            per.append({"engine": name, "engine_marker": "-", "drift": [],
                        "step_order": [], "terminal_outcome": "refused",
                        "checks_passed": 0, "checks_total": 0,
                        "failures": [{"check": "the engine refused to run at all",
                                      "detail": json.dumps(problem.body)}]})

    orders = {json.dumps(p["step_order"]) for p in per}
    outcomes = {p["terminal_outcome"] for p in per}
    markers = sorted({p["engine_marker"] for p in per})
    comparable = ("loop_termination", "ceiling_termination", "budget_termination",
                  "verdicts", "agents_selected", "parked_step", "gate_decisions",
                  "spent_micros", "operators_exercised")
    differ = [k for k in comparable if len({json.dumps(p.get(k), sort_keys=True)
                                            for p in per}) > 1]
    report = {"schema_ops": per[0].get("schema_ops", []), "engines_run": len(per),
              "engines": [{"engine_marker": p["engine_marker"],
                           "executor_ops": p.get("executor_ops", []),
                           "step_order": p["step_order"],
                           "terminal_outcome": p["terminal_outcome"]} for p in per],
              "operators_exercised": min((p.get("operators_exercised", 0) for p in per),
                                         default=0),
              "drift": sorted({d for p in per for d in p["drift"]}),
              "step_orders_identical": len(orders) == 1,
              "terminal_outcomes_identical": len(outcomes) == 1,
              "distinct_markers": markers, "differ_across_engines": differ,
              "break_drift": args.break_drift, "per_engine": per}
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        json.dump(report, open(args.report, "w"), indent=2, default=str)

    ok = True
    for p in per:
        for failure in p["failures"]:
            print(f"  FAIL [{p['engine']}] {failure['check']}: {failure['detail']}")
        print(f"engine_marker={p['engine_marker']} schema_ops={len(p.get('schema_ops', []))} "
              f"executor_ops={len(p.get('executor_ops', []))} drift={len(p['drift'])} "
              f"operators_exercised={p.get('operators_exercised', 0)} "
              f"terminal_outcome={p['terminal_outcome']} "
              f"checks={p['checks_passed']}/{p['checks_total']}")
        ok = ok and not p["failures"] and not p["drift"]
    if len(per) > 1:
        print(f"engines_run={len(per)} step_order={'identical' if report['step_orders_identical'] else 'DIFFERS'} "
              f"terminal_outcome={'identical' if report['terminal_outcomes_identical'] else 'DIFFERS'} "
              f"distinct_markers={len(markers)} differ={differ or 'nothing'}")
        if not report["step_orders_identical"] or not report["terminal_outcomes_identical"] \
                or differ or len(markers) != len(per):
            print("  FAIL the engines did not agree on the same document")
            ok = False
    else:
        print(f"engines_run={len(per)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
