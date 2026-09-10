#!/usr/bin/env python3
"""improve - what the platform learned: spend per done, attempts, which template held.

One improvement pass. It runs at a boundary, works the metric furthest from its
target, puts every candidate revision through an evaluation gate that may say no,
and leaves the standing checkpoint in place when it does. What the caller reads
back is not "it improved": it is how many attempts and how much spend each metric
took, and which named template held under the gate.

Nothing here re-declares a loop, a case set, a rubric, a verdict or a baseline.
The pass is driven through the improvement-loop capability's five operations
(register_scorecard, open_loop, run_iteration, evaluate_exit, read_checkpoint),
and that capability reaches the evaluation capability through its own binding to
it. The entry envelope, its validator and the hash-chained ledger come from
examples/end-to-end. Every problem object is built at one construction point.

  python3 examples/improve/run.py --entry examples/improve/entries/human.json
  python3 examples/improve/run.py --entry entries/schedule.json      # one iteration, then park
  python3 examples/improve/run.py --verify-ledger --ledger out/human.jsonl

Configuration, never a code edit: --gate dryrun|second (or GATE=) selects the
evaluation adapter; the loop driver is selected by the caller's declared
fire_mode. Python 3.11 standard library only, no network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harnesses                                    # noqa: E402

ref = harnesses.reference()                          # the entry schema's own validator,
validate, Ledger, canonical = ref.validate, ref.Ledger, ref.canonical    # and the ledger

ENTRY_SCHEMA = os.path.join(harnesses.ROOT, "examples", "end-to-end", "schemas", "entry.schema.json")
PASS_SCHEMA = os.path.join(HERE, "schemas", "improve.schema.json")
UNIT_SCHEMA = os.path.join(HERE, "schemas", "unit.schema.json")

# The caller's declared fire mode chooses the driver. The mapping is here, in one
# place, so no document names an adapter and no adapter name reaches a document.
DRIVER_FOR = {"in-one-process": "dryrun", "one-iteration-per-fire": "second"}
CLOSING_KINDS = ("pass-completed", "pass-escalated", "pass-failed")


def load(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def digest(obj) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()[:32]


class Refusal(Exception):
    """A typed refusal that ends the pass. Carries problem details and nothing else."""

    def __init__(self, body: dict) -> None:
        super().__init__(body["detail"])
        self.body = body


def table(rows: list[tuple[str, ...]]) -> str:
    w = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = ["  ".join(c.ljust(w[i]) for i, c in enumerate(rows[0])),
           "  ".join("-" * x for x in w)]
    out += ["  ".join(c.ljust(w[i]) for i, c in enumerate(r)) for r in rows[1:]]
    return "\n".join(out)


# --- the documents -----------------------------------------------------------
def read_documents(entry_path: str, il) -> tuple[dict, dict, dict]:
    """The two documents a caller writes and the one they point at, each validated
    with the reference example's validator before anything is registered."""
    env = load(entry_path)
    errs = validate(env, load(ENTRY_SCHEMA))
    if errs:
        raise Refusal(il.problem("document-invalid",
                                 f"the entry envelope was refused: {'; '.join(errs)}").as_dict())
    improve = env["payload"].get("improve")
    if improve is None:
        raise Refusal(il.problem("document-invalid",
                                 "payload.improve is missing: an improvement pass declares the "
                                 "boundary it runs at and how it fires").as_dict())
    errs = validate(improve, load(PASS_SCHEMA))
    if errs:
        raise Refusal(il.problem("document-invalid",
                                 f"payload.improve was refused: {'; '.join(errs)}",
                                 env["correlation"]["correlation_id"]).as_dict())
    # boundary.kind decides who may offer a revision: an outside finding must name
    # the change it is offering, and a ceremony, phase or structure boundary may not
    # carry one in.
    offered, kind = improve.get("revision_offered"), improve["boundary"]["kind"]
    if kind == "partner-finding" and offered is None:
        raise Refusal(il.problem("document-invalid",
                                 "a partner-finding boundary must name the revision it offers",
                                 env["correlation"]["correlation_id"]).as_dict())
    if kind != "partner-finding" and offered is not None:
        raise Refusal(il.problem("document-invalid",
                                 f"a {kind} boundary may not carry payload.improve.revision_offered; "
                                 "a revision offered from outside enters by a partner-finding boundary",
                                 env["correlation"]["correlation_id"]).as_dict())
    unit_path = os.path.join(HERE, env["intent"]["workflow_ref"])
    if not os.path.isfile(unit_path):
        raise Refusal(il.problem("document-invalid",
                                 f"intent.workflow_ref names no task specification: "
                                 f"{env['intent']['workflow_ref']}",
                                 env["correlation"]["correlation_id"]).as_dict())
    unit = load(unit_path)
    errs = validate(unit, load(UNIT_SCHEMA))
    if errs:
        raise Refusal(il.problem("document-invalid",
                                 f"the task specification was refused: {'; '.join(errs)}",
                                 env["correlation"]["correlation_id"]).as_dict())
    return env, improve, unit


def scorecard_of(unit: dict, offered: dict | None, il):
    """The scorecard and the ordered candidates, read as data. A candidate names the
    gate it will be put through and carries no criterion; an offered revision is put
    ahead of the unit's own candidates for its metric and gated identically."""
    metrics = tuple(il.Metric(m["metric_id"], m["direction"], float(m["current"]),
                              float(m["target"]), float(m["scale"]))
                    for m in unit["scorecard"]["metrics"])
    rows = list(unit["candidates"])
    if offered is not None:
        first = next((i for i, c in enumerate(rows) if c["metric_id"] == offered["metric_id"]),
                     len(rows))
        rows.insert(first, {k: v for k, v in offered.items()})
    candidates = [il.CandidateChange(c["candidate_id"], c["metric_id"], il.GateSpec(**c["gate"]),
                                     float(c["value_if_promoted"]), c["rationale"]) for c in rows]
    return il.Scorecard(unit["scorecard"]["scorecard_id"], metrics), candidates, rows


# --- the pass ----------------------------------------------------------------
class Pass:
    """One improvement pass: the stamps every record carries, and the ledger."""

    def __init__(self, env: dict, improve: dict, unit: dict, ledger: Ledger) -> None:
        self.env, self.improve, self.unit, self.ledger = env, improve, unit, ledger
        chain = env["actor"]["delegation_chain"]
        self.stamp = {
            "run_id": env["correlation"]["run_id"],
            "correlation_id": env["correlation"]["correlation_id"],
            "actor": env["actor"]["subject"],
            "delegation_depth": len(chain) - 1,          # derived from the chain, not declared
            "entry_kind": env["kind"],
            "idempotency_key": env["idempotency_key"],
            "boundary_kind": improve["boundary"]["kind"],
            "boundary_ref": improve["boundary"]["ref"],
        }

    def record(self, kind: str, **fields) -> dict:
        return self.ledger.append(kind=kind, **self.stamp, **fields)

    def rows(self, kind: str) -> list[dict]:
        return [r for r in self.ledger.records if r["kind"] == kind]

    def closed(self) -> dict | None:
        return next((r for r in self.ledger.records
                     if r["kind"] in CLOSING_KINDS
                     and r.get("idempotency_key") == self.env["idempotency_key"]), None)


def loop_id_for(improve: dict) -> str:
    """One boundary is one pass: the loop id is derived from the boundary the caller
    declared, so re-firing the same boundary resumes that loop and a different
    boundary opens a new one."""
    body = canonical([improve["boundary"]["kind"], improve["boundary"]["ref"]])
    return "il-" + hashlib.sha256(body.encode()).hexdigest()[:12]


def learned(records: list[dict], unit: dict, templates: dict[str, str]) -> dict:
    """Read back out of the ledger, never carried forward from the runner: per metric,
    the attempts spent, the spend, the candidate and template that held, and the
    distance closed. Every number here is computed from iteration-recorded rows -
    the spend included: what an iteration cost is the `spend_micros` that iteration's
    own record carries, never a count of rows times a number read out of the
    declaration, so a driver that charged a different amount for one iteration moves
    this table."""
    rows = [r for r in records if r["kind"] == "iteration-recorded"]
    spend = lambda rs: sum(int(r["spend_micros"]) for r in rs)
    metrics = {}
    for m in unit["scorecard"]["metrics"]:
        mine = [r for r in rows if r["metric_id"] == m["metric_id"]]
        held = [r for r in mine if r["decision"] == "promoted"]
        metrics[m["metric_id"]] = {
            "attempts": len(mine),
            "micros": spend(mine),
            "held_candidate": held[-1]["candidate_id"] if held else None,
            "held_template": templates.get(held[-1]["candidate_id"]) if held else None,
            "distance_at_open": mine[0]["distance_before"] if mine else None,
            "distance_now": mine[-1]["distance_after"] if mine else None,
        }
    by_template: dict[str, dict[str, int]] = {}
    for r in rows:
        t = templates.get(r["candidate_id"], "(unnamed)")
        row = by_template.setdefault(t, {"offered": 0, "held": 0})
        row["offered"] += 1
        row["held"] += 1 if r["decision"] == "promoted" else 0
    return {"per_metric": metrics, "by_template": by_template,
            "iterations": len(rows), "micros": spend(rows),
            "promoted": sum(1 for r in rows if r["decision"] == "promoted"),
            "declined": sum(1 for r in rows if r["decision"] == "declined")}


def print_plan(unit: dict, values: dict, spec, il, label: str) -> None:
    """Priced before anything runs, at every fire: the distances standing now, the
    floor if every gate passed first time, and the worst case at the ceiling."""
    card = il.Scorecard(unit["scorecard"]["scorecard_id"],
                        tuple(il.Metric(m["metric_id"], m["direction"], float(m["current"]),
                                        float(m["target"]), float(m["scale"]))
                              for m in unit["scorecard"]["metrics"])).with_values(values)
    offered: dict[str, int] = {}
    for c in unit["candidates"]:
        offered[c["metric_id"]] = offered.get(c["metric_id"], 0) + 1
    print(f"plan ({label}): {spec.loop_id}, ceiling {spec.iteration_ceiling} iterations at "
          f"{spec.per_iteration_micros} micros")
    print(table([("metric", "dir", "now", "target", "distance", "candidates offered", "means")]
                + [(m.metric_id, m.direction, f"{m.current:g}", f"{m.target:g}",
                    f"{m.distance:.2f}", str(offered.get(m.metric_id, 0)), row["means"])
                   for m, row in zip(card.metrics, unit["scorecard"]["metrics"])]))
    away = [m for m in card.metrics if not m.holds]
    floor = len(away) * spec.per_iteration_micros
    worst = spec.iteration_ceiling * spec.per_iteration_micros
    print(f"  {len(away)} metric(s) away from target: floor {floor} micros if every gate passes "
          f"first time, worst case {worst} at the iteration ceiling, ceiling "
          f"{spec.budget_ceiling_micros}")
    return floor


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entry", help="the entry document at one of the four doors")
    parser.add_argument("--ledger", help="receipt path; defaults to out/<entry kind>.jsonl")
    parser.add_argument("--gate", default=os.environ.get("GATE", "dryrun"),
                        help="evaluation adapter, by configuration: dryrun|second")
    parser.add_argument("--promote-regardless", action="store_true",
                        help="THE DELIBERATE BREAKAGE: promote whatever the gate said")
    parser.add_argument("--verify-ledger", action="store_true", help="verify a receipt's hash chain")
    args = parser.parse_args(argv)

    if args.verify_ledger:
        path = os.path.join(os.getcwd(), args.ledger) if args.ledger \
            else os.path.join(HERE, "out", "human.jsonl")
        led = Ledger(path)
        broken = led.verify()
        print(broken or f"chain verifies: {len(led.records)} records, head {led.head()}")
        return 2 if broken else 0
    if not args.entry:
        parser.error("--entry is required unless --verify-ledger is given")

    # The interface is needed to build a problem object, so it is loaded before the
    # documents are read; the driver it hands back is chosen once fire_mode is known.
    il, build = harnesses.improvement_loop()
    entry_path = args.entry if os.path.isabs(args.entry) else os.path.join(os.getcwd(), args.entry)
    try:
        env, improve, unit = read_documents(entry_path, il)
    except Refusal as refusal:
        print("application/problem+json")
        print(json.dumps(refusal.body, indent=2))
        return 2

    # An explicit --ledger is resolved against the caller's working directory, like
    # --entry; only the default lands inside the example.
    ledger_path = os.path.join(os.getcwd(), args.ledger) if args.ledger \
        else os.path.join(HERE, "out", f"{env['kind']}.jsonl")
    # Each receipt gets its own adapter store, so two passes never read each other's
    # checkpoints, and the key is the receipt's resolved path rather than its
    # basename: two runs given `a/probe.jsonl` and `b/probe.jsonl` are two passes,
    # not one pass with two receipts. Both stores stay inside out/.
    resolved = os.path.realpath(ledger_path)
    stem = (os.path.splitext(os.path.basename(resolved))[0] + "-"
            + hashlib.sha256(resolved.encode()).hexdigest()[:8])
    os.environ.setdefault("IMPROVE_LOOP_FIRE_ROOT", os.path.join(HERE, "out", "fires", stem))
    os.environ.setdefault("EVAL_FIXTURE_ROOT", os.path.join(HERE, "out", "gate", stem))
    run = Pass(env, improve, unit, Ledger(ledger_path))

    done = run.closed()
    if done is not None:                       # the same key, already closed: no second pass
        print(f"REPLAY: {env['idempotency_key']} already closed as {done['kind']} at seq "
              f"{done['seq']}; 0 records appended")
        return 0

    try:
        return run_pass(run, il, build, args)
    except Refusal as refusal:
        print("application/problem+json")
        print(json.dumps(refusal.body, indent=2))
        return 2


def run_pass(run: Pass, il, build, args) -> int:
    env, improve, unit = run.env, run.improve, run.unit
    corr = env["correlation"]["correlation_id"]
    offered = improve.get("revision_offered")
    scorecard, candidates, rows = scorecard_of(unit, offered, il)
    templates = {c["candidate_id"]: c["template"] for c in rows}

    # promotion.authority is read here, at the point where the rule is chosen. There
    # is one legal value and no document member that names another.
    rule = il.promote_regardless if args.promote_regardless else il.promote_on_pass
    authority = "operator-override(breakage)" if args.promote_regardless \
        else unit["promotion"]["authority"]
    # fire_mode is read here, at the point where the driver is chosen: nothing else
    # in this file branches on it until the loop decides whether to park.
    driver = build(DRIVER_FOR[improve["fire_mode"]],
                   gate=il.Gate(il.load_gate_adapter(args.gate)), decision_rule=rule)

    loop_id = loop_id_for(improve)
    spec = il.LoopSpec(loop_id, unit["loop"]["iteration_ceiling"],
                       env["budget"]["ceiling_micros"], unit["loop"]["per_iteration_micros"],
                       unit["loop"]["on_cap"])

    standing = driver.read_checkpoint(loop_id)          # a Problem means no loop here yet
    resuming = not isinstance(standing, il.Problem)
    values = standing.values if resuming else scorecard.values()
    floor = print_plan(unit, values, spec, il, "resumed" if resuming else "first fire")

    if not resuming:
        run.record("pass-submitted", unit_id=unit["unit_id"], unit_digest=digest(unit),
                   template=unit["template"], fire_mode=improve["fire_mode"],
                   driver=driver.name, gate=driver.gate.name, promotion_authority=authority,
                   rollback_to=unit["promotion"]["rollback_to"],
                   ceiling_micros=spec.budget_ceiling_micros)
        if floor > spec.budget_ceiling_micros:
            body = il.problem("budget-exhausted",
                              f"the pass would need at least {floor} micros to move every metric "
                              f"once and the ceiling is {spec.budget_ceiling_micros}; no case was "
                              "replayed and no loop was opened", corr).as_dict()
            run.record("refusal", at="plan", type=body["type"], status=body["status"],
                       ended_pass=True, detail=body["detail"])
            raise Refusal(body)

    handle = driver.register_scorecard(scorecard, candidates)
    if isinstance(handle, il.Problem):
        raise Refusal(handle.as_dict())
    if not resuming:
        run.record("scorecard-registered", scorecard_id=handle.scorecard_id,
                   scorecard_digest=handle.digest, metrics=handle.metric_count,
                   candidates=handle.candidate_count)
        if offered is not None:
            run.record("revision-offered", candidate_id=offered["candidate_id"],
                       metric_id=offered["metric_id"], template=offered["template"],
                       slot=offered["slot"], offered_by=env["actor"]["subject"],
                       tried_at_attempt=1, carries_criterion=False)
        opened = driver.open_loop(spec, handle.scorecard_id)
        if isinstance(opened, il.Problem):
            run.record("refusal", at="open_loop", type=opened.type, status=opened.status,
                       ended_pass=True, detail=opened.detail)
            raise Refusal(opened.as_dict())
        run.record("loop-opened", loop_id=loop_id, iteration_ceiling=spec.iteration_ceiling,
                   per_iteration_micros=spec.per_iteration_micros,
                   budget_ceiling_micros=spec.budget_ceiling_micros,
                   open_checkpoint_id=opened.checkpoint_id, values=opened.values)
        open_checkpoint = opened.checkpoint_id
    else:
        # A resumed fire reads the loop it is resuming out of its own receipt. If the
        # store holds a checkpoint and the receipt holds no loop-opened, the two have
        # been separated: that is a typed refusal, not an exception out of an
        # unguarded read - every other store read on this path is checked the same way.
        opened_rows = run.rows("loop-opened")
        if not opened_rows:
            body = il.problem("document-invalid",
                              f"loop {loop_id!r} has a standing checkpoint in the driver's "
                              f"store and this receipt holds no loop-opened record; a resumed "
                              "fire is refused rather than opening a second loop over the same "
                              "checkpoint", corr).as_dict()
            run.record("refusal", at="resume", type=body["type"], status=body["status"],
                       ended_pass=True, detail=body["detail"])
            raise Refusal(body)
        open_checkpoint = opened_rows[-1]["open_checkpoint_id"]

    rollback_to = unit["promotion"]["rollback_to"]
    fresh: list[dict] = []
    outcome = driver.evaluate_exit(loop_id)
    if isinstance(outcome, il.Problem):
        raise Refusal(outcome.as_dict())
    while outcome is None:
        driver = driver.next_fire()                    # a per-fire driver rebinds here
        before = driver.read_checkpoint(loop_id)
        if isinstance(before, il.Problem):
            raise Refusal(before.as_dict())
        record = driver.run_iteration(loop_id, correlation_id=corr)
        if isinstance(record, il.Problem):
            run.record("refusal", at="run_iteration", type=record.type, status=record.status,
                       ended_pass=True, detail=record.detail)
            run.record("learned", **learned(run.ledger.records, unit, templates))
            run.record("pass-failed", loop_id=loop_id, disposition="reject",
                       iterations_run=len(run.rows("iteration-recorded")))
            raise Refusal(record.as_dict())
        body = record.as_dict()
        # The iteration's own key and the envelope's are two different keys; the
        # record's correlation id is the envelope's, which the stamp already carries.
        body["iteration_key"] = body.pop("idempotency_key")
        assert body.pop("correlation_id") == corr
        row = dict(body, template=templates.get(record.candidate_id),
                   rollback_to=rollback_to,
                   rollback_to_checkpoint_id=(before.checkpoint_id
                                              if rollback_to == "previous_checkpoint"
                                              else open_checkpoint),
                   promotion_authority=authority)
        run.record("iteration-recorded", **row)
        fresh.append(row)
        outcome = driver.evaluate_exit(loop_id)
        if isinstance(outcome, il.Problem):
            raise Refusal(outcome.as_dict())
        if outcome is None and improve["fire_mode"] == "one-iteration-per-fire":
            run.record("pass-parked", loop_id=loop_id,
                       iterations_run=len(run.rows("iteration-recorded")),
                       resume_from=row["checkpoint_id"])
            print_iterations(fresh)
            print_receipt(run)
            print(f"parked: iteration {row['iteration_index']} of {loop_id} recorded; the next "
                  f"fire resumes from checkpoint {row['checkpoint_id']}")
            return 0

    learn = learned(run.ledger.records, unit, templates)
    run.record("learned", **learn)
    body = outcome.as_dict()
    disposition = "accept" if body["terminated_by"] == "verdict_pass" else "escalate"
    kind = "pass-completed" if disposition == "accept" else "pass-escalated"
    run.record(kind, loop_id=loop_id, disposition=disposition, **{
        k: v for k, v in body.items() if k != "loop_id"})
    print_iterations(fresh)
    print_learned(learn, unit, body)
    escalation = body.get("escalation")
    if escalation:
        print(f"\nescalation: {escalation['type']} ({escalation['status']}) {escalation['detail']}")
    print_receipt(run)
    print(f"{kind.split('-')[1]}: disposition {disposition}, terminated_by "
          f"{body['terminated_by']} ({body['termination_class']}), "
          f"{body['iterations_run']} iterations, targets held {body['targets_held']}/"
          f"{body['targets_total']}, spent {body['cost_micros']} of "
          f"{env['budget']['ceiling_micros']} micros, rollback state "
          f"{body['final_checkpoint_id']}")
    return 0


def print_receipt(run: Pass) -> None:
    """The receipt line, before the closing line, so what a reader is promised at the
    end of a command does not move when a record is added."""
    print(f"\nreceipt: {os.path.relpath(run.ledger.path, HERE)}, {len(run.ledger.records)} "
          f"records, head {run.ledger.head()}")


def print_iterations(rows: list[dict]) -> None:
    if not rows:
        return
    print("\niterations this fire (the metric furthest from its target, each time):")
    print(table([("it", "metric worked", "distance", "candidate", "template", "gate",
                  "cases", "decision", "checkpoint", "moved", "rollback to")]
                + [(str(r["iteration_index"]), r["metric_id"],
                    f"{r['distance_before']:.2f}->{r['distance_after']:.2f}", r["candidate_id"],
                    r["template"] or "-", r["gate_outcome"], str(r["cases_executed"]),
                    r["decision"], r["checkpoint_id"],
                    "yes" if r["checkpoint_advanced"] else "held",
                    r["rollback_to_checkpoint_id"]) for r in rows]))


def print_learned(learn: dict, unit: dict, body: dict) -> None:
    print("\nwhat the platform learned (read back out of the receipt, not carried forward):")
    print(table([("metric", "attempts", "micros spent", "candidate that held",
                  "template that held", "distance")]
                + [(m["metric_id"], str(row["attempts"]), str(row["micros"]),
                    row["held_candidate"] or "-", row["held_template"] or "-",
                    "-" if row["distance_at_open"] is None
                    else f"{row['distance_at_open']:.2f}->{row['distance_now']:.2f}")
                   for m in unit["scorecard"]["metrics"]
                   for row in [learn["per_metric"][m["metric_id"]]]]))
    print(table([("template", "revisions gated", "held", "did not hold")]
                + [(t, str(r["offered"]), str(r["held"]), str(r["offered"] - r["held"]))
                   for t, r in sorted(learn["by_template"].items())]))
    held = body["targets_held"]
    print(f"  {learn['iterations']} iterations, {learn['promoted']} promoted and "
          f"{learn['declined']} declined, {learn['micros']} micros over "
          f"{held} target(s) held" + (f" = {learn['micros'] // held} micros per target held"
                                      if held else ""))


if __name__ == "__main__":
    raise SystemExit(main())
