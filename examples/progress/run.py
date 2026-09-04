#!/usr/bin/env python3
"""progress: plan, develop, test, release, production as five gated stages.

One unit declaration, four doors, one durable run. Read it in this order:

  plan()       prices every stage before anything runs, from the pipeline
               document alone, and is the only thing that decides whether the
               unit is admitted at all.
  Run.step()   is where every guarantee attaches: the ceiling is checked before
               the call, the outward call is keyed so at-least-once delivery is
               effectively-once effect, the checkpoint makes the step durable,
               and a committed step is replayed from the journal on a restart
               rather than executed again.
  Run.stage_*  are the five operators a stage may declare. The walk dispatches
               on the stage's declared `op`, never on its id, so a stage added
               to the document is walked; each handler reads its own declared
               values at the point it decides with them, and nothing below
               re-types a bound, a width, a class or a stage name as a literal.

Every capability here is called, not implemented: durable execution, scheduling,
evaluation, compensation and the closed problem registry are the harnesses under
harness/, bound by name through harnesses.py, and the entry envelope is validated
with the reference example's own validator. No product name appears in this file.

Python 3.11 standard library only, offline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harnesses as H  # noqa: E402

REF = H.reference()                       # the reference example's validator and ledger
SCHED = H.scheduling()                    # the pure recurrence evaluator and its declaration
EVAL = H.evaluation()                     # the case, the scorer, the report, the release gate
ERRI, ERRP = H.errors()                   # the closed registry gate, and the one render point
OPS = H.operators()                       # the composition operators, read from the schema

WORKFLOW_SCHEMA = json.load(open(os.path.join(HERE, "..", "end-to-end", "schemas",
                                              "workflow.schema.json")))
# The operator names a stage may declare. The first tuple is the composition
# capability's closed set, read out of the schema an engine is handed and never
# re-typed here; the second is the one name this area adds on top of it, which
# that set does not carry (README gap G12). A stage declaring anything else is
# refused before an executor is bound.
CAPABILITY_OPS = OPS.operator_names(WORKFLOW_SCHEMA)
LOCAL_OPS = ("effect",)

ENTRY_SCHEMA = json.load(open(os.path.join(HERE, "..", "end-to-end", "schemas", "entry.schema.json")))
PROGRESS_SCHEMA = json.load(open(os.path.join(HERE, "schemas", "progress.schema.json")))

# The published task lifecycle. A state outside this set is not reportable.
TASK_STATES = ("submitted", "working", "input-required", "completed", "failed", "cancelled")

# The four dispositions of the ontology, and no fifth.
DISPOSITIONS = ("accept", "retry", "reject", "escalate")

# Rule 6: the grader is never visible to the graded. The criterion body and the
# rubric bodies live here, behind the opaque handles the documents carry, and
# neither is ever placed in a step's input or in any caller-visible output.
CRITERIA = {"criterion://coupon-fix/v1": {"must_contain": ["regression verified"]}}
RUBRICS = {"rubric://release-coupon/v1": {"required_steps": ["plan", "tool_call", "answer"],
                                          "required_tools": ["read_diff", "run_tests"],
                                          "answer_contains": "coupon tier fix"}}


# --------------------------------------------------------------------------
# Failures. Every one of them is built at the errors capability's own registry
# gate; nothing in this file assembles a problem body of its own.
# --------------------------------------------------------------------------
def refuse(suffix: str, detail: str, correlation_id: str | None = None, **ext):
    return ERRP.ProblemException(ERRI.construct(suffix, detail, correlation_id, **ext))


def problem_body(exc) -> dict:
    """One wire body from either shape: the errors capability's frozen Problem,
    or a capability's own typed condition, which renders through the same
    function. There is no third place a body comes from."""
    if isinstance(exc, ERRP.ProblemException):
        return exc.problem.body()
    return getattr(exc, "body")


def is_problem(exc) -> bool:
    return isinstance(exc, ERRP.ProblemException) or isinstance(getattr(exc, "body", None), dict)


# --------------------------------------------------------------------------
# Planning: a pure function of the pipeline document. It reads no clock, binds
# no executor and spends nothing (F-b1-06).
# --------------------------------------------------------------------------
def plan(pipeline: dict) -> dict:
    rows, floor, worst = [], 0, 0
    for st in pipeline["stages"]:
        if st["op"] == "loop":
            body = sum(b.get("cost_micros", 0) for b in st["body"])
            rows.append((st["id"], "loop", f"1..{st['iterations_permitted']} x {body}",
                         body, body * st["iterations_permitted"]))
            floor += body
            worst += body * st["iterations_permitted"]
        elif st["op"] == "parallel":
            width = len(st["shards"])
            cost = width * st["shard_cost_micros"]
            rows.append((st["id"], "parallel", f"{width} x {st['shard_cost_micros']}", cost, cost))
            floor += cost
            worst += cost
        elif st["op"] == "effect":
            cost = st["cost_micros"] + st["verify"]["cost_micros"]
            rows.append((st["id"], "effect", f"{st['cost_micros']} + verify "
                         f"{st['verify']['cost_micros']}", cost, cost))
            floor += cost
            worst += cost
        else:
            cost = sum(s.get("cost_micros", 0) for s in st.get("steps", [])) + st.get("cost_micros", 0)
            rows.append((st["id"], st["op"], str(cost), cost, cost))
            floor += cost
            worst += cost
    return {"rows": rows, "floor_micros": floor, "worst_micros": worst}


# --------------------------------------------------------------------------
# The schedule door: expansion, catch-up and the replay key.
# --------------------------------------------------------------------------
def expand_schedule(decl_doc: dict) -> dict:
    """Everything the schedule door decides, decided by the scheduling
    capability's pure evaluator and its declaration gate. Nothing here parses a
    rule, and nothing here mints a key from the wall clock."""
    decl = SCHED.ScheduleDeclaration.from_dict(
        {k: decl_doc[k] for k in ("unit_ref", "recurrence", "starts_at", "timezone", "catch_up")})
    now, last = decl_doc["now"], decl_doc["last_fire_at"]
    lookback = dt.datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ") - dt.timedelta(days=decl_doc["lookback_days"])
    window_from = max(last, lookback.strftime("%Y-%m-%dT%H:%M:%SZ"))
    occ = SCHED.occurrences(decl.recurrence, decl.starts_at, decl.timezone, window_from, now)
    missed = [o for o in occ.occurrences if o > last]
    if decl.catch_up == "skip":
        fired = []
    elif decl.catch_up == "fire_once":
        fired = missed[-1:]
    else:
        fired = list(missed)
    return {"declaration": {"unit_ref": decl.unit_ref, "recurrence": decl.recurrence,
                            "starts_at": decl.starts_at, "timezone": decl.timezone,
                            "catch_up": decl.catch_up, "lookback_days": decl_doc["lookback_days"]},
            "window": {"from": window_from, "to": now},
            "occurrences": occ.occurrences, "missed": missed, "fired": fired,
            "keys": [SCHED.idempotency_key(decl.unit_ref, o) for o in fired],
            "declaration_obj": decl}


# --------------------------------------------------------------------------
# Stage gating: what the next stage requires of the one before it. Read out of
# the pipeline document at the moment the walk decides, never re-typed here.
# --------------------------------------------------------------------------
def gate_wants(gate: dict) -> str:
    return repr(gate["outcome_in"]) if "outcome_in" in gate else repr(gate["outcome"])


def gate_met(gate: dict, actual) -> bool:
    if "outcome_in" in gate:
        return actual in gate["outcome_in"]
    return actual == gate["outcome"]


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------
class Replayed:
    def __init__(self, output):
        self.output = output


class Run:
    def __init__(self, env: dict, pipeline: dict, opts, ledger):
        self.env, self.pipeline, self.opts, self.ledger = env, pipeline, opts, ledger
        self.prog = env["payload"]["progress"]
        # The two stage names the report needs are found in the document by the
        # operator they declare, never written down here: the effect stage is
        # the one whose op is `effect`, and the candidate is whatever step the
        # loop's declared judge step judges.
        self.effect_stage = next((st["id"] for st in pipeline["stages"]
                                  if st["op"] == "effect"), None)
        loop_stage = next((st for st in pipeline["stages"] if st["op"] == "loop"), None)
        judged = next((c for c in (loop_stage or {}).get("body", [])
                       if c["id"] == loop_stage["exit_when"]["judge_step"]), None)
        self.candidate_step = (judged or {}).get("of")
        self.run_key = env["idempotency_key"]
        self.corr = env["correlation"]["correlation_id"]
        self.actor = env["actor"]["subject"]
        self.ceiling = env["budget"]["ceiling_micros"]
        self.spent = 0
        self.remaining = self.ceiling
        self.state = "submitted"
        self.states_seen = ["submitted"]
        # A nonce this process minted. It is what a journalled result is
        # recognised by after a restart: a replayed step carries the nonce of
        # the process that first ran it, never the nonce of the one reading it.
        self.nonce = f"proc-{os.getpid()}-{time.time_ns()}"
        self.results: dict = {}
        self.stage_rows: list[dict] = []
        self.outcomes: dict = {}
        self.steps_executed = self.steps_replayed = 0
        self.loop = None
        self.evaluation = None
        self.approval = {"parked": 0, "decision": None, "applied": 0,
                         "deliveries": 0, "deadline_at": None, "contradiction_refused": 0}
        self.compensation = {"declared": None, "plan": None, "sealed": False, "unwind": None}
        self.schedule = None
        self.refusals: list[dict] = []
        self.disposition = None
        self.stop_reason = None
        # An empty plan, so a refusal raised before pricing still reports.
        self.planned = {"rows": [], "floor_micros": 0, "worst_micros": 0}
        self.ex = self.register = self.outward = None
        self.resume_point_at_start = 0
        self.spent_at_bind = 0
        self.correlation_source = "envelope"

    # -- lifecycle ---------------------------------------------------------
    def dispose(self, word: str) -> str:
        """The one place a disposition is set, the way move() is the one place a
        task state is. A word outside the ontology's four is refused rather than
        reported, so `there is no fifth` is a gate and not a comment."""
        if word not in DISPOSITIONS:
            raise refuse("document-invalid",
                         f"{word!r} is not one of the dispositions {list(DISPOSITIONS)}",
                         self.corr)
        self.disposition = word
        return word

    def move(self, state: str) -> None:
        if state not in TASK_STATES:
            raise refuse("document-invalid", f"{state!r} is not one of the published task states")
        if state != self.state:
            self.state = state
            self.states_seen.append(state)

    def record(self, kind: str, **fields) -> dict:
        return self.ledger.append(
            kind=kind, run_id=self.env["correlation"]["run_id"], correlation_id=self.corr,
            actor=self.actor, delegation_depth=len(self.env["actor"]["delegation_chain"]),
            entry_kind=self.env["kind"], idempotency_key=self.run_key,
            unit=self.pipeline["unit_ref"], task_state=self.state, at=self.env["occurred_at"],
            **fields)

    # -- one durable step --------------------------------------------------
    def charge(self, step_id: str, cost: int) -> None:
        if cost > self.remaining:
            raise refuse("budget-exhausted",
                         f"step {step_id} needs {cost} micros and {self.remaining} of the "
                         f"{self.ceiling} ceiling is left; the unit terminates and nothing else does",
                         self.corr, stop_reason="ceiling-reached")

    def step(self, step_id: str, cost: int, work, effect: dict | None = None,
             outward: dict | None = None) -> dict:
        key = self.WF.step_idempotency_key(self.run_key, step_id)
        prior = self.done.get(key)
        if prior is not None:
            self.steps_replayed += 1
            self.record("step-replayed", step=step_id, step_key=key, cost_micros=0,
                        budget_remaining_micros=self.remaining,
                        output_digest=prior.output_digest)
            return prior.output
        self.charge(step_id, cost)
        out = work()
        if outward is not None and not self.outward.has(key):
            # The one place this unit reaches outside itself. Keyed, so a step
            # re-executed after a crash that landed between the call and the
            # checkpoint does not call out a second time.
            self.outward.append(key, {**outward, "step_id": step_id, "run_key": self.run_key})
        if effect is not None and self.ex.effect_commit_mode == "keyed_effect":
            if not self.ex.effects.has(key):
                self.ex.effects.append(key, {**effect, "step_id": step_id, "run_key": self.run_key})
        if self.opts.crash_at and self.opts.crash_at in (step_id, step_id.split("#")[0]):
            sys.stderr.write(f"CRASH: kill -9 at step {step_id}, before its checkpoint\n")
            sys.stderr.flush()
            os.kill(os.getpid(), signal.SIGKILL)
        self.ex.checkpoint_step(self.WF.Checkpoint(
            run_key=self.run_key, step_id=step_id,
            step_idempotency_key=key, output_digest=self.WF.digest(out), cost_micros=cost,
            correlation_id=self.corr, actor=self.actor, output=out,
            effect=None if effect is None or self.ex.effect_commit_mode == "keyed_effect"
            else {**effect, "step_id": step_id, "run_key": self.run_key}))
        self.steps_executed += 1
        self.spent += cost
        self.remaining -= cost
        self.done[key] = Replayed(out)
        self.record("step-committed", step=step_id, step_key=key, cost_micros=cost,
                    budget_remaining_micros=self.remaining, output_digest=self.WF.digest(out))
        return out

    # -- the five stages ---------------------------------------------------
    def stage_sequence(self, st: dict) -> str:
        for s in st["steps"]:
            self.step(s["id"], s["cost_micros"], lambda s=s: {"priced": self.planned["floor_micros"],
                                                              "worst": self.planned["worst_micros"],
                                                              "nonce": self.nonce})
        return st["outcome_on_success"]

    def stage_loop(self, st: dict) -> str:
        body_cost = sum(b.get("cost_micros", 0) for b in st["body"])
        before = self.spent
        passes_on = self.prog["passes_on_iteration"]
        permitted = st["iterations_permitted"]
        per_iteration = st["per_iteration_ceiling_micros"]
        for i in range(1, permitted + 1):
            if body_cost > per_iteration or body_cost > self.remaining:
                return self.cap(st, i - 1, "budget_ceiling", before,
                                f"iteration {i} of loop {st['id']} needs {body_cost} micros; the "
                                f"per-iteration ceiling is {per_iteration} and {self.remaining} "
                                f"of the unit ceiling is left")
            for child in st["body"]:
                sid = f"{child['id']}#{i}"
                if child["op"] == "step":
                    text = (f"candidate {i} for the coupon-tier fix"
                            + (" regression verified" if i >= passes_on else ""))
                    self.results[child["id"]] = self.step(
                        sid, child["cost_micros"],
                        lambda t=text, n=i: {"text": t, "iteration": n, "nonce": self.nonce},
                        outward={"operator": "propose-patch", "iteration": i}
                        if child.get("reaches_outside") else None)
                else:
                    of = self.results.get(child["of"], {}).get("text", "")
                    verdict, why = self.judge(of, child["criterion_ref"])
                    self.results[child["id"]] = self.step(
                        sid, child["cost_micros"],
                        lambda v=verdict, w=why: {"verdict": v, "detail": w, "nonce": self.nonce})
                    self.record("judge-verdict", step=sid, verdict=verdict, of=child["of"],
                                criterion_ref=child["criterion_ref"])
            last = self.results[st["exit_when"]["judge_step"]]
            if last.get("verdict") == st["exit_when"]["verdict"]:
                self.loop = {"loop_id": st["id"], "terminated_by": "verdict_pass",
                             "termination_class": "stop", "iterations_run": i,
                             "iterations_permitted": permitted,
                             "cost_micros": self.spent - before, "last_verdict": last["verdict"]}
                self.record("loop-terminated", **self.loop)
                return "verdict_pass"
        return self.cap(st, permitted, "iteration_ceiling", before,
                        f"loop {st['id']} ran {permitted} of {permitted} permitted iterations "
                        f"without a {st['exit_when']['verdict']} verdict")

    def cap(self, st: dict, iterations: int, reason: str, before: int, detail: str) -> str:
        """A cap terminates the loop, and the document says what that means for
        the unit: `on_cap` is the disposition the caller is answered with, read
        here and checked against the ontology's four. The problem type stays a
        function of which cap was hit, which is the errors capability's to say
        and not the document's."""
        self.loop = {"loop_id": st["id"], "terminated_by": reason, "termination_class": "cap",
                     "iterations_run": max(iterations, 0), "iterations_permitted": st["iterations_permitted"],
                     "cost_micros": self.spent - before,
                     "last_verdict": self.results.get(st["exit_when"]["judge_step"], {}).get("verdict")}
        self.record("loop-terminated", **self.loop)
        self.dispose(st["on_cap"])
        suffix = "deadline-exceeded" if reason == "iteration_ceiling" else "budget-exhausted"
        ext = ({"retry_after_s": 0} if suffix == "deadline-exceeded"
               else {"stop_reason": "loop-per-iteration-ceiling"})
        raise refuse(suffix, detail + f"; the unit declares on_cap {st['on_cap']!r}, so the "
                     f"disposition is {self.disposition}, and the proposed type for a loop that "
                     f"ran out of iterations is urn:agentic:problem:iteration-ceiling-reached",
                     self.corr, **ext)

    def judge(self, text: str, criterion_ref: str):
        criterion = CRITERIA.get(criterion_ref)
        if criterion is None:
            raise refuse("criterion-unresolvable", f"{criterion_ref} does not resolve", self.corr)
        missing = [t for t in criterion["must_contain"] if t not in text]
        return ("pass", "the criterion is met") if not missing else ("fail", "the criterion is not met")

    def stage_parallel(self, st: dict) -> str:
        ev = st["evaluation"]
        case_doc = json.load(open(os.path.join(HERE, ev["case_set_ref"])))
        baseline = json.load(open(os.path.join(HERE, ev["baseline_ref"])))
        by_id = {c["case_id"]: c for c in case_doc["cases"]}
        declared = [cid for shard in st["shards"] for cid in shard["cases"]]
        unknown = sorted(set(declared) - set(by_id))
        if unknown:
            raise refuse("document-invalid",
                         f"the fan-out names case(s) {unknown} that case set "
                         f"{case_doc['case_set_id']} does not carry", self.corr,
                         causes=[{"case_id": c} for c in unknown])
        scores: dict = {}
        for shard in st["shards"]:                      # the fan-out, one durable step per shard
            out = self.step(
                f"shard-{shard['id']}", st["shard_cost_micros"],
                lambda s=shard: {"shard": s["id"], "cases": s["cases"], "nonce": self.nonce,
                                 "scores": {cid: EVAL.score_steps(by_id[cid]["recorded_steps"],
                                                                  RUBRICS[by_id[cid]["rubric_ref"]])
                                            for cid in s["cases"]}})
            scores.update(out["scores"])
        cases = [EVAL.Case(c["case_id"], c["corpus_half"], c["input"], c["rubric_ref"],
                           EVAL.StubPolicy(), c.get("recorded_run_ref")) for c in case_doc["cases"]]
        handle = EVAL.CaseSetHandle(case_doc["case_set_id"], case_doc["version"],
                                    EVAL.digest_cases(cases), len(cases))
        unit = EVAL.UnitRef(ev["unit_ref"], ev["unit_version"])
        verdicts = {cid: EVAL.verdict_of(s) for cid, s in scores.items()}
        report = EVAL.EvaluationReport(
            report_id=EVAL.report_id_for(unit, handle.digest, baseline["baseline_id"], verdicts),
            unit_under_test=unit, case_set=handle, baseline_id=baseline["baseline_id"],
            outcome=EVAL.outcome_for(len(verdicts), verdicts), cases_executed=len(verdicts),
            transitions=EVAL.transitions_for(verdicts, baseline["verdicts"]),
            correlation_id=self.corr, verdicts=verdicts)
        gate = EVAL.gate_stage(report, "ev-" + report.report_id[3:])
        self.evaluation = {**report.as_dict(), "verdicts": verdicts, "gate": gate.as_dict(),
                           "blocks_promotion": gate.blocks_promotion,
                           "shards_declared": len(st["shards"]),
                           "shard_ids": [s["id"] for s in st["shards"]],
                           "dimension_scores": scores}
        self.record("evaluation-gated", status=gate.status, cases_executed=gate.cases_executed,
                    report_id=gate.report_id, blocks_promotion=gate.blocks_promotion,
                    case_set=handle.case_set_id, case_set_digest=handle.digest,
                    baseline_id=baseline["baseline_id"],
                    transitions=[{"case_id": t.case_id, "was": t.was, "now": t.now}
                                 for t in report.transitions])
        return gate.status

    def stage_approval(self, st: dict) -> str:
        sid = "release-gate"
        key = self.WF.step_idempotency_key(self.run_key, sid)
        prior = self.done.get(key)
        if prior is not None:
            self.steps_replayed += 1
            self.record("step-replayed", step=sid, step_key=key, cost_micros=0,
                        budget_remaining_micros=self.remaining, output_digest=prior.output_digest)
            if prior.output["outcome"] == "expired":
                # An expiry is the gate's terminal answer, not a decision the
                # walk can carry forward: replaying it re-raises the refusal the
                # first process ended on, with the deadline read off the step
                # record, so one envelope answers the same way however many
                # processes run it.
                gate_id = self.WF.gate_id_for(self.run_key, sid)
                self.approval.update(parked=1, deadline_at=prior.output["deadline_at"],
                                     decision=None)
                self.move("input-required")
                self.dispose("escalate")
                raise refuse("deadline-exceeded",
                             f"{gate_id} closed undecided at {prior.output['deadline_at']}; "
                             f"{self.prog['decider']} was asked over parked-item and nobody "
                             f"answered", self.corr, retry_after_s=0)
            self.approval.update(decision=prior.output["outcome"], parked=0)
            return prior.output["outcome"]
        deadline = (dt.datetime.strptime(self.env["occurred_at"], "%Y-%m-%dT%H:%M:%SZ")
                    + dt.timedelta(minutes=st["deadline_minutes"])).strftime("%Y-%m-%dT%H:%M:%SZ")
        gate = self.WF.GateRecord(
            gate_id=self.WF.gate_id_for(self.run_key, sid), correlation_id=self.corr,
            step_id="production", view=st["view"], decider=self.prog["decider"],
            wires=["parked-item"], deadline_at=deadline, return_to_step_id=st["return_to_stage"])
        self.ex.park_gate(gate)
        self.approval.update(parked=1, deadline_at=deadline)
        self.move("input-required")
        self.record("approval-parked", gate_id=gate.gate_id, view=gate.view,
                    decider=gate.decider, deadline_at=deadline,
                    decisions_offered=st["decisions_offered"],
                    return_to_stage=gate.return_to_step_id)
        decision = self.prog["decision"]
        if decision == "none":
            self.step(sid, st["cost_micros"],
                      lambda: {"outcome": "expired", "deadline_at": deadline})
            self.dispose("escalate")
            raise refuse("deadline-exceeded",
                         f"{gate.gate_id} closed undecided at {deadline}; {gate.decider} was asked "
                         f"over parked-item and nobody answered", self.corr, retry_after_s=0)
        if decision not in st["decisions_offered"]:
            raise refuse("document-invalid",
                         f"the unit offers {st['decisions_offered']} at this gate; "
                         f"{decision!r} is not one of them", self.corr,
                         causes=[{"decision": decision, "offered": st["decisions_offered"]}])
        applied = 0
        for _ in range(self.opts.deliveries):
            applied += int(self.ex.record_decision(self.WF.GateOutcome(
                gate.gate_id, self.corr, decision, self.prog["decider"],
                idempotency_key=f"gate:{gate.gate_id}:{decision}",
                body=self.prog.get("decision_body", {}), delivered_over="parked-item")))
        if self.opts.contradict:
            other = next(d for d in st["decisions_offered"] if d != decision)
            self.ex.record_decision(self.WF.GateOutcome(
                gate.gate_id, self.corr, other, self.prog["decider"],
                idempotency_key=f"gate:{gate.gate_id}:{other}", delivered_over="parked-item"))
            body = problem_body(refuse(
                "idempotency-conflict",
                f"{gate.gate_id} was already decided {decision!r}; a second, different decision "
                f"{other!r} on the same gate is not applied", self.corr))
            self.approval["contradiction_refused"] = 1
            self.refusals.append({"where": "release.gate", "ends_unit": False, **body})
            self.record("refusal", where="release.gate", ends_unit=False, problem=body)
        self.move("working")
        out = self.step(sid, st["cost_micros"],
                        lambda: {"outcome": decision, "actor": self.prog["decider"],
                                 "body": self.prog.get("decision_body", {})})
        self.approval.update(decision=decision, applied=applied, deliveries=self.opts.deliveries)
        self.record("approval-decided", gate_id=gate.gate_id, decision=decision,
                    decider=self.prog["decider"], deliveries=self.opts.deliveries,
                    resumed_the_run=applied, delivered_over="parked-item")
        return out["outcome"]

    def stage_effect(self, st: dict) -> str:
        comp = st["compensation"]
        note = (self.approval.get("decision") == "edit"
                and self.prog.get("decision_body", {}).get("release_note")) or "coupon tier fix"
        effect_body = {"release": "coupon-fix/1.4.0", "run_key": self.run_key, "release_note": note}
        action = None
        if comp.get("compensating_action"):
            a = comp["compensating_action"]
            action = self.C.CompensatingAction(
                a["operator"], a["input_ref"],
                idempotency_key=self.WF.step_idempotency_key(self.run_key, "undo-" + st["id"]),
                timeout_s=a["timeout_s"])
        rec = self.register.declare_effect(self.C.DeclareEffect(
            run_id=self.run_key, step_id=st["id"], effect_digest=self.C.digest(effect_body),
            irreversibility=comp.get("irreversibility"),
            idempotency_key=self.WF.step_idempotency_key(self.run_key, st["id"]),
            correlation_id=self.corr, actor=self.actor, entry_kind=self.env["kind"],
            compensating_action=action, mandate_ref=comp.get("mandate_ref")))
        self.compensation["declared"] = {"step_id": rec.step_id, "state": rec.state,
                                         "irreversibility": rec.irreversibility,
                                         "register_observed": rec.register_observed,
                                         "declared_at_head": rec.declared_at_head}
        self.record("effect-declared", step=st["id"], irreversibility=rec.irreversibility,
                    declared_at_head=rec.declared_at_head, state=rec.state,
                    compensating_operator=(rec.compensating_action or {}).get("operator"))
        # The read a planner and an approval gate need before the first effect,
        # not after the last one.
        uplan = self.register.unwind_plan(self.run_key)
        self.compensation["plan"] = {"would_unwind": uplan.would_unwind,
                                     "unreachable": uplan.unreachable}
        self.record("unwind-plan-read", would_unwind=uplan.would_unwind,
                    unreachable=uplan.unreachable)
        self.step(st["id"], st["cost_micros"],
                  lambda: {"released": "coupon-fix/1.4.0", "release_note": note, "nonce": self.nonce},
                  effect=effect_body, outward={"operator": "publish-release", "release_note": note})
        sealed = self.register.seal_effect(rec, response_ref="release://coupon-fix/1.4.0#applied")
        self.compensation["sealed"] = sealed.state == "committed"
        self.record("effect-sealed", step=st["id"], state=sealed.state,
                    sealed_response_ref=sealed.sealed_response_ref)
        v = st["verify"]
        verdict = self.prog["verify_outcome"]
        self.step(v["id"], v["cost_micros"], lambda: {"verify": verdict, "nonce": self.nonce})
        if verdict == "pass":
            return "sealed"
        self.register.register_handlers({"roll-back-release": self.roll_back})
        rep = self.register.unwind(self.run_key, "failed")
        self.compensation["unwind"] = {
            "reason": rep.reason, "order": rep.order, "compensated": rep.compensated,
            "not_required": rep.not_required, "unwind_failed": rep.unwind_failed,
            "register_observed": rep.register_observed,
            "outcomes": [{"step_id": o.step_id, "outcome": o.outcome, "operator": o.operator,
                          "detail": o.detail} for o in rep.outcomes]}
        self.record("compensation-unwound", **{k: v for k, v in self.compensation["unwind"].items()
                                               if k != "outcomes"},
                    outcomes=self.compensation["unwind"]["outcomes"])
        self.stop_reason = "post-release-verification-failed"
        self.dispose("retry")
        return "unwound"

    def roll_back(self, action: dict) -> str:
        """The compensating operator: an ordinary forward operation that appends
        a reversing row, under its own key and its own timeout."""
        self.outward.ensure(action["idempotency_key"],
                            {"operator": action["operator"], "undoes": action["undoes_key"],
                             "run_key": self.run_key, "step_id": action["step_id"]})
        return "release://coupon-fix/1.4.0#rolled-back"

    # The operator each handler serves. The keys are the composition
    # capability's closed set plus this area's one local addition, so a name the
    # capability does not publish and this file does not add has nowhere to be
    # dispatched from.
    OPERATORS = {"sequence": stage_sequence, "loop": stage_loop, "parallel": stage_parallel,
                 "approval": stage_approval, "effect": stage_effect}

    # -- the walk ----------------------------------------------------------
    def check_operators(self) -> None:
        """The vocabulary gate, before an executor is bound.

        Every stage's declared `op` is one the walk serves, and the set the walk
        serves cannot drift from the composition capability's: each handler's
        key is either a name the schema admits or one of this area's declared
        local additions, checked here rather than written down twice."""
        drift = [op for op in self.OPERATORS if op not in CAPABILITY_OPS + LOCAL_OPS]
        if drift:
            raise refuse("document-invalid",
                         f"the walk serves {drift}, which the composition capability's schema "
                         f"does not admit and this area does not declare as local", self.corr,
                         causes=[{"op": op} for op in drift])
        for st in self.pipeline["stages"]:
            if st["op"] not in self.OPERATORS:
                raise refuse("document-invalid",
                             f"stage {st['id']!r} declares op {st['op']!r}; the composition "
                             f"capability admits {list(CAPABILITY_OPS)} and this unit walks "
                             f"{list(self.OPERATORS)}", self.corr,
                             causes=[{"stage": st["id"], "op": st["op"]}])

    def execute(self) -> int:
        self.check_operators()
        self.planned = plan(self.pipeline)
        self.record("unit-submitted", sequence_id=self.pipeline["sequence_id"],
                    tenant=self.pipeline["tenant"], ceiling_micros=self.ceiling,
                    workflow_ref=self.env["intent"]["workflow_ref"],
                    process_nonce=self.nonce)
        if self.prog.get("schedule"):
            self.schedule = self.door_schedule()
        self.record("plan-priced", floor_micros=self.planned["floor_micros"],
                    worst_micros=self.planned["worst_micros"], ceiling_micros=self.ceiling,
                    rows=[list(r) for r in self.planned["rows"]])
        if self.planned["floor_micros"] > self.ceiling:
            self.dispose("reject")
            raise refuse("budget-exhausted",
                         f"the plan's shortest finishing path costs {self.planned['floor_micros']} "
                         f"micros and the ceiling is {self.ceiling}; nothing was dispatched",
                         self.corr, stop_reason="estimate-exceeds-ceiling")
        self.bind()
        self.move("working")
        for st in self.pipeline["stages"]:
            gate = st.get("enter_when")
            if gate is not None and not gate_met(gate, self.outcomes.get(gate["stage"])):
                self.stage_rows.append({"stage": st["id"], "op": st["op"], "entered": False,
                                        "outcome": None,
                                        "why": f"{gate['stage']} is "
                                               f"{self.outcomes.get(gate['stage'])!r}, "
                                               f"not {gate_wants(gate)}"})
                self.record("stage-skipped", stage=st["id"], op=st["op"],
                            required=gate, actual=self.outcomes.get(gate["stage"]))
                continue
            self.record("stage-entered", stage=st["id"], op=st["op"], required=gate)
            # The row is appended before the stage runs, so a stage the ceiling
            # or a refusal ended halfway is reported as entered with no outcome
            # rather than as never reached.
            row = {"stage": st["id"], "op": st["op"], "entered": True,
                   "outcome": None, "why": None}
            self.stage_rows.append(row)
            outcome = self.OPERATORS[st["op"]](self, st)
            self.outcomes[st["id"]] = row["outcome"] = outcome
        return 0

    def door_schedule(self) -> dict:
        s = expand_schedule(self.prog["schedule"])
        decl = s.pop("declaration_obj")
        nominal = self.prog["schedule"]["occurrence"]
        built = SCHED.build_envelope(decl, nominal, self.actor, self.ceiling,
                                     self.env["correlation"]["run_id"], self.corr)
        s["nominal"] = nominal
        s["nominal_key"] = SCHED.idempotency_key(decl.unit_ref, nominal)
        s["key_matches_envelope"] = built["idempotency_key"] == self.env["idempotency_key"]
        s["backfill_key"] = SCHED.idempotency_key(decl.unit_ref, nominal)
        s["next_occurrence"] = SCHED.next_after(decl.recurrence, decl.starts_at,
                                                decl.timezone, nominal)
        s["next_key"] = SCHED.idempotency_key(decl.unit_ref, s["next_occurrence"])
        if not s["key_matches_envelope"]:
            raise refuse("idempotency-conflict",
                         f"the envelope carries {self.env['idempotency_key']!r} where the "
                         f"({decl.unit_ref}, {nominal}) occurrence keys to "
                         f"{built['idempotency_key']!r}", self.corr)
        self.record("schedule-expanded", recurrence=decl.recurrence, timezone=decl.timezone,
                    window=s["window"], occurrences=s["occurrences"], missed=s["missed"],
                    catch_up=decl.catch_up, lookback_days=self.prog["schedule"]["lookback_days"])
        for occurrence, key in zip(s["fired"], s["keys"]):
            self.record("schedule-fired", occurrence=occurrence, fire_key=key,
                        nominal_is_this_run=occurrence == nominal)
        return s

    def bind(self) -> None:
        """Binding is configuration: one name, one module, one class. Nothing in
        the walk above branches on which executor or which register answered."""
        self.WF, executor_cls, journal = H.durable(self.opts.executor)
        self.C, register_cls = H.compensation(self.opts.register)
        out_dir = os.path.join(self.opts.out, self.run_key)
        self.ex = executor_cls(out_dir)
        self.register = register_cls(out_dir)
        self.outward = journal.EffectTable(os.path.join(out_dir, "outward-calls.jsonl"))
        state = self.ex.begin_run(self.WF.BeginRun(
            self.run_key, self.pipeline["sequence_id"], self.WF.digest(self.env["payload"]),
            self.corr, self.actor, self.ceiling))
        if state.correlation_id:
            if state.correlation_id != self.corr:
                raise refuse("idempotency-conflict",
                             f"run {self.run_key} was begun under correlation "
                             f"{state.correlation_id}, not {self.corr}", self.corr)
            self.correlation_source = "step-record"
        self.resume_point_at_start = state.resume_point
        self.done = {r.step_idempotency_key: r for r in state.completed if r.step_idempotency_key}
        # The remaining ceiling is recomputed from the committed records, never
        # reset: a restart is not free money.
        self.spent = state.spent_micros
        self.spent_at_bind = state.spent_micros
        self.remaining = self.ceiling - self.spent
        self.record("run-bound", executor_marker=state.executor_marker,
                    effect_commit_mode=self.ex.effect_commit_mode,
                    register_observed=self.register.register_marker,
                    resume_point=state.resume_point, steps_committed=state.steps_committed,
                    spent_micros=self.spent, budget_remaining_micros=self.remaining,
                    correlation_source=self.correlation_source)

    # -- what the caller reads ---------------------------------------------
    def report(self, outcome: str, problem: dict | None) -> dict:
        receipt = self.ex.read_receipt(self.run_key) if self.ex else None
        ladder = self.ladder(outcome)
        return {
            "area": "progress", "unit_ref": self.pipeline["unit_ref"],
            "sequence_id": self.pipeline["sequence_id"], "tenant": self.pipeline["tenant"],
            "entry_kind": self.env["kind"], "actor": self.actor,
            "delegation_depth": len(self.env["actor"]["delegation_chain"]),
            "run_id": self.env["correlation"]["run_id"], "correlation_id": self.corr,
            "correlation_source": self.correlation_source, "run_key": self.run_key,
            "outcome": outcome, "problem": problem, "stop_reason": self.stop_reason,
            "disposition": self.disposition, "task_state": self.state,
            "task_states_seen": self.states_seen, "success_ladder": ladder,
            "executor": {"selected": self.opts.executor,
                         "marker": receipt.executor_marker if receipt else None,
                         "effect_commit_mode": self.ex.effect_commit_mode if self.ex else None,
                         "binding": self.ex.binding() if self.ex else None},
            "register": {"selected": self.opts.register,
                         "marker": self.register.register_marker if self.register else None},
            "plan": {"rows": [list(r) for r in self.planned["rows"]],
                     "floor_micros": self.planned["floor_micros"],
                     "worst_micros": self.planned["worst_micros"]},
            "budget": {"ceiling_micros": self.ceiling, "spent_micros": self.spent,
                       "remaining_micros": self.remaining,
                       "spent_before_this_process_micros": self.spent_at_bind,
                       "remaining_at_bind_micros": self.ceiling - self.spent_at_bind},
            "resume_point_at_start": self.resume_point_at_start,
            "steps_committed": receipt.steps_committed if receipt else 0,
            "steps_executed": self.steps_executed, "steps_replayed": self.steps_replayed,
            "outward_calls": len(self.outward.rows()) if self.outward else 0,
            "effect_rows": len(self.ex.effects.rows()) if self.ex else 0,
            "process_nonce": self.nonce,
            "nonces": {k: v.get("nonce") for k, v in self.results.items() if isinstance(v, dict)},
            "stages": self.stage_rows, "loop": self.loop, "evaluation": self.evaluation,
            "approval": self.approval, "compensation": self.compensation,
            "schedule": self.schedule, "refusals": self.refusals,
            "gates_parked": receipt.gates_parked if receipt else 0,
            "gates_decided": receipt.gates_decided if receipt else 0,
        }

    def ladder(self, outcome: str) -> dict:
        """Success reported on the ontology's ladder, never as one word."""
        ev = self.evaluation or {}
        return {
            "execution": bool(self.ex),
            "instruction": outcome in ("completed", "failed") and self.steps_executed + self.steps_replayed > 0,
            "candidate": self.candidate_step in self.results,
            "validation": ev.get("gate", {}).get("status") == "passed",
            "task": "held-out",
            "outcome": self.outcomes.get(self.effect_stage) == "sealed",
            "promotion": (self.outcomes.get(self.effect_stage) == "sealed"
                          and outcome == "completed"),
        }


# --------------------------------------------------------------------------
def table(rows, header) -> None:
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(rep: dict) -> None:
    print(f"unit={rep['unit_ref']}  door={rep['entry_kind']}  actor={rep['actor']}  "
          f"correlation_id={rep['correlation_id']} ({rep['correlation_source']})  "
          f"executor={rep['executor']['marker']}  register={rep['register']['marker']}")
    print("\nplan, before anything runs (a pure function of the unit declaration):")
    table([[*r] for r in rep["plan"]["rows"]],
          ("stage", "operator", "priced as", "floor micros", "worst micros"))
    print(f"floor {rep['plan']['floor_micros']}  worst {rep['plan']['worst_micros']}  "
          f"ceiling {rep['budget']['ceiling_micros']}")
    print("\nstages:")
    table([[s["stage"], s["op"], "yes" if s["entered"] else "no",
            s["outcome"] or "-", s["why"] or "-"] for s in rep["stages"]],
          ("stage", "operator", "entered", "outcome", "why not"))
    if rep["evaluation"]:
        ev = rep["evaluation"]
        print(f"\nevaluation gate: {ev['gate']['status']}  cases {ev['gate']['cases_executed']}  "
              f"report {ev['report_id']}  blocks promotion: "
              f"{'yes' if ev['blocks_promotion'] else 'no'}  "
              f"shards {ev['shards_declared']} ({', '.join(ev['shard_ids'])})")
        table([[c, v, *(ev["dimension_scores"][c][d] for d in ("trajectory", "tool_use",
                                                               "task_completion"))]
               for c, v in sorted(ev["verdicts"].items())],
              ("case", "verdict", "trajectory", "tool_use", "task_completion"))
    print(f"\nsteps: committed {rep['steps_committed']}  executed here {rep['steps_executed']}  "
          f"replayed from the journal {rep['steps_replayed']}  "
          f"resume point at start {rep['resume_point_at_start']}")
    print(f"outward calls {rep['outward_calls']}  effect rows {rep['effect_rows']}  "
          f"spent {rep['budget']['spent_micros']} of {rep['budget']['ceiling_micros']} micros, "
          f"{rep['budget']['remaining_micros']} left")
    print(f"task state {' -> '.join(rep['task_states_seen'])}   disposition "
          f"{rep['disposition']}   outcome {rep['outcome']}")
    print("ladder: " + "  ".join(f"{k}={v}" for k, v in rep["success_ladder"].items()))
    print(f"RESULT door={rep['entry_kind']} outcome={rep['outcome']} "
          f"disposition={rep['disposition']} spent={rep['budget']['spent_micros']}/"
          f"{rep['budget']['ceiling_micros']} micros")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entry", help="the entry document, one per door")
    ap.add_argument("--verify-ledger", action="store_true",
                    help="verify the hash chain of --ledger and exit; runs nothing")
    ap.add_argument("--pipeline", default=None,
                    help="override the unit the envelope's intent.workflow_ref names")
    ap.add_argument("--ledger", default=os.path.join(HERE, "out", "ledger.jsonl"))
    ap.add_argument("--report", default="")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "state"))
    ap.add_argument("--executor", default="dryrun", choices=("dryrun", "second"))
    ap.add_argument("--register", default="dryrun", choices=("dryrun", "second"))
    ap.add_argument("--crash-at", default=None,
                    help="fault injection, not a declared field: kill -9 at this step id "
                         "before its checkpoint is written")
    ap.add_argument("--deliveries", type=int, default=1,
                    help="how many times the one gate decision is delivered")
    ap.add_argument("--contradict", action="store_true",
                    help="deliver a second, different decision on a gate already decided")
    opts = ap.parse_args(argv)
    if opts.verify_ledger:
        broken = REF.Ledger(opts.ledger).verify()
        print(broken or f"chain verified: {opts.ledger}")
        return 2 if broken else 0
    if not opts.entry:
        ap.error("--entry is required unless --verify-ledger is given")

    env = json.load(open(opts.entry))
    errs = REF.validate(env, ENTRY_SCHEMA)
    prog = env.get("payload", {}).get("progress")
    errs += ["payload.progress is required"] if prog is None else REF.validate(prog, PROGRESS_SCHEMA)
    if errs:
        body = problem_body(refuse("document-invalid",
                                   f"{opts.entry} does not validate: {errs[0]}",
                                   env.get("correlation", {}).get("correlation_id"),
                                   causes=[{"detail": e} for e in errs]))
        print("application/problem+json")
        print(json.dumps(body, indent=2))
        return 2

    pipeline_ref = opts.pipeline or env["intent"]["workflow_ref"]
    pipeline = json.load(open(os.path.join(HERE, pipeline_ref)))
    os.makedirs(os.path.dirname(opts.ledger) or ".", exist_ok=True)
    run = Run(env, pipeline, opts, REF.Ledger(opts.ledger))
    try:
        run.execute()
        blocked = (run.evaluation or {}).get("blocks_promotion")
        stopped = [s for s in run.stage_rows if not s["entered"]]
        if run.outcomes.get("production") == "unwound":
            outcome, code = "failed", 3
        elif stopped:
            outcome, code = "failed", 3
            run.stop_reason = run.stop_reason or (
                "evaluation-gate-blocked-promotion" if blocked else "stage-gate-not-met")
            run.dispose(run.disposition or ("retry" if blocked else "reject"))
        else:
            outcome, code = "completed", 0
            run.dispose("accept")
        run.move("completed" if code == 0 else "failed")
        rep = run.report(outcome, None)
        run.record("unit-completed" if code == 0 else "unit-failed", outcome=outcome,
                   disposition=run.disposition, stop_reason=run.stop_reason,
                   spent_micros=run.spent, ladder=rep["success_ladder"])
    except Exception as exc:
        if not is_problem(exc):
            raise
        body = problem_body(exc)
        run.dispose(run.disposition or "escalate")
        run.move("failed")
        run.refusals.append({"where": "unit", "ends_unit": True, **body})
        rep = run.report("failed", body)
        run.record("refusal", where="unit", ends_unit=True, problem=body)
        run.record("unit-failed", outcome="failed", disposition=run.disposition,
                   stop_reason=run.stop_reason, spent_micros=run.spent,
                   ladder=rep["success_ladder"])
        if opts.report:
            json.dump(rep, open(opts.report, "w"), indent=2, default=str)
        print("application/problem+json")
        print(json.dumps(body, indent=2))
        show(rep)
        return 2 if run.spent == 0 else 3
    if opts.report:
        json.dump(rep, open(opts.report, "w"), indent=2, default=str)
    show(rep)
    return code


if __name__ == "__main__":
    sys.exit(main())
