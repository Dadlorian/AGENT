#!/usr/bin/env python3
"""The durable flow, and the platform work around it. One process, one attempt.

Read it in this order: FLOW is the declared sequence; Driver.run walks it once;
Driver.step is where every guarantee attaches - budget recomputed from the
committed records, correlation re-attached from the record rather than minted,
the actor re-asserted, the idempotency key derived so it is identical on every
restart, and the checkpoint written after the effect (or with it, when the
executor declares it can).

This module is spawned as a subprocess by call.py and conformance.py so that
`--crash-at` can be a real `kill -9`: the process dies with the effect on disk
and no checkpoint, which is the window a resume has to survive.

Python 3.11 standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from interface import (BeginRun, Checkpoint, Envelope, GateOutcome, GateRecord,  # noqa: E402
                       LoopOutcome, Problem, digest, gate_id_for, step_idempotency_key)

# --------------------------------------------------------------------------
# The declared flow: one step, a bounded loop with a judge exit and a ceiling,
# a parked gate, the irreversible step, and a close. Data, not code.
# --------------------------------------------------------------------------
FLOW = {
    "sequence_id": "durable-publish/0.1",
    "steps": [
        {"op": "step", "id": "intake", "cost_micros": 15000},
        {"op": "loop", "id": "fix-loop", "max_iterations": 3,
         "per_iteration_ceiling_micros": 200000, "on_cap": "escalate",
         "exit_when": {"judge_step": "judge", "verdict": "pass"},
         "body": [{"op": "step", "id": "draft", "cost_micros": 60000},
                  {"op": "judge", "id": "judge", "of": "draft",
                   "criterion_ref": "criterion://publishable/v1"}]},
        {"op": "gate", "id": "gate-publish", "guards": "publish",
         "view": "release-brief", "return_to_step_id": "intake",
         "deadline_minutes": 60},
        {"op": "effect", "id": "publish", "cost_micros": 20000},
        {"op": "step", "id": "notify", "cost_micros": 10000},
    ],
}

# Rule 6: the grader is never visible to the graded. The criterion body lives
# here, behind an opaque handle, and is never placed in a step's input.
CRITERIA = {"criterion://publishable/v1": {"must_contain": ["regression verified"]}}


def judge(text: str, criterion_ref: str) -> tuple[str, str]:
    """Pure function (result, criterion) -> verdict."""
    criterion = CRITERIA.get(criterion_ref)
    if criterion is None:
        raise Problem("criterion-unresolvable", f"{criterion_ref} does not resolve")
    missing = [t for t in criterion["must_contain"] if t not in text]
    return ("pass", "all required evidence present") if not missing else ("fail", f"missing {missing}")


def executor_for(name: str, out_dir: str):
    """Selecting an executor is configuration. Nothing else in this file, and
    nothing in call.py, branches on which one answered."""
    if name == "dryrun":
        from adapters.dryrun import JournalExecutor
        return JournalExecutor(out_dir)
    if name == "second":
        from adapters.second import QueueStateMachineExecutor
        return QueueStateMachineExecutor(out_dir)
    if name == "live":
        from adapters.live import WorkflowEngineExecutor
        return WorkflowEngineExecutor(out_dir)
    raise Problem("document-invalid", f"unknown adapter {name!r}")


class Driver:
    def __init__(self, ex, env: dict, opts):
        self.ex, self.env, self.opts = ex, env, opts
        self.run_key = env["idempotency_key"]
        self.corr = env["correlation"]["correlation_id"]
        self.actor = env["actor"]["subject"]
        self.ceiling = env["budget"]["ceiling_micros"]
        self.decisions = list(opts.decision) or ["approve:user:corey"]
        self.results: dict[str, dict] = {}
        self.rows: list[tuple] = []
        self.round = 0
        self.loop_outcome: LoopOutcome | None = None
        self.replayed = self.prior_seen = self.executed = 0
        self.gates_parked = self.returns = self.expired = 0
        self.resumes_per_gate_max = self.late_applied = 0
        self.wires: list[str] = []
        self.stopped_by: str | None = None

        state = ex.begin_run(BeginRun(self.run_key, FLOW["sequence_id"],
                                      digest(env["payload"]), self.corr, self.actor,
                                      self.ceiling))
        # Correlation is re-attached from the record; a restart never mints a new
        # root, and it never trusts trace parentage to reconnect the two halves.
        self.correlation_source = "envelope"
        if state.correlation_id:
            if state.correlation_id != self.corr:
                raise Problem("idempotency-conflict",
                              f"run {self.run_key} was begun under correlation "
                              f"{state.correlation_id}, not {self.corr}")
            self.correlation_source = "step-record"
        self.state = state
        self.prior_ids = {r.step_id for r in state.completed}
        self.done = {r.step_idempotency_key: r for r in state.completed
                     if r.step_idempotency_key}
        # Budget remaining is recomputed from the committed step records. A
        # restart that reset the ceiling would have turned a crash into free money.
        self.spent = state.spent_micros
        self.remaining = self.ceiling - self.spent
        self.orphan_effects = ex.effects.orphans(set(self.done)) if hasattr(ex, "effects") else 0

    # -- one durable step ----------------------------------------------------
    def sid(self, base: str) -> str:
        return base if self.round == 0 else f"{base}@r{self.round}"

    def key(self, step_id: str) -> str | None:
        if self.opts.break_idempotency:
            return None                     # the deliberate breakage, nothing else changed
        return step_idempotency_key(self.run_key, step_id)

    def charge(self, step_id: str, cost: int) -> None:
        if cost > self.remaining:
            raise Problem("budget-exhausted",
                          f"step {step_id} needs {cost} micros, {self.remaining} left",
                          step_id=step_id, correlation_id=self.corr)

    def step(self, step_id: str, cost: int, work, effect: dict | None = None) -> dict:
        key = self.key(step_id)
        prior = self.done.get(key) if key else None
        if prior is not None:
            self.replayed += 1
            self.rows.append((step_id, "replayed", 0, self.remaining, "skipped"))
            return prior.output
        if step_id in self.prior_ids:
            self.prior_seen += 1
        self.charge(step_id, cost)
        out = work()
        mode = self.ex.effect_commit_mode
        if effect is not None and mode == "keyed_effect":
            # The effect first, then the checkpoint. The window between them is
            # this executor's declared gap; the key on the table is what closes it.
            if not self.ex.effects.has(key):
                self.ex.effects.append(key, {**effect, "step_id": step_id,
                                             "run_key": self.run_key})
        if self.opts.crash_at == step_id:
            sys.stderr.write(f"CRASH: kill -9 at step {step_id} before its checkpoint\n")
            sys.stderr.flush()
            os.kill(os.getpid(), signal.SIGKILL)
        self.ex.checkpoint_step(Checkpoint(
            run_key=self.run_key, step_id=step_id, step_idempotency_key=key,
            output_digest=digest(out), cost_micros=cost, correlation_id=self.corr,
            actor=self.actor, output=out,
            effect=None if effect is None or mode == "keyed_effect"
            else {**effect, "step_id": step_id, "run_key": self.run_key}))
        self.executed += 1
        self.spent += cost
        self.remaining -= cost
        if key:
            self.done[key] = Checkpointed(out)
        self.rows.append((step_id, "ran", cost, self.remaining, "ok"))
        return out

    # -- operators -----------------------------------------------------------
    def do_plain(self, node) -> None:
        sid = self.sid(node["id"])
        self.results[node["id"]] = self.step(
            sid, node["cost_micros"], lambda: {"text": f"{node['id']} done", "step": sid})

    def do_loop(self, node) -> None:
        body_cost = sum(b.get("cost_micros", 0) for b in node["body"])
        cost_before = self.spent
        for i in range(1, node["max_iterations"] + 1):
            if body_cost > self.remaining or body_cost > node["per_iteration_ceiling_micros"]:
                self.loop_outcome = self.cap(node, i - 1, "budget_ceiling", cost_before,
                                             Problem("budget-exhausted",
                                                     f"loop {node['id']} cannot afford iteration {i}: "
                                                     f"{body_cost} needed, {self.remaining} left",
                                                     correlation_id=self.corr).body)
                return
            for child in node["body"]:
                if child["op"] == "step":
                    sid = self.sid(f"{child['id']}#{i}")
                    passes = (not self.opts.loop_never_pass) and (i >= 2 or self.round >= 1)
                    text = (f"{child['id']} attempt {i}" + (" regression verified" if passes else ""))
                    self.results[child["id"]] = self.step(
                        sid, child["cost_micros"], lambda t=text, s=sid: {"text": t, "step": s})
                else:
                    sid = self.sid(f"{child['id']}#{i}")
                    of = self.results.get(child["of"], {}).get("text", "")
                    verdict, why = judge(of, child["criterion_ref"])
                    self.results[child["id"]] = self.step(
                        sid, 0, lambda v=verdict, w=why: {"verdict": v, "detail": w,
                                                          "text": v})
            last = self.results[node["exit_when"]["judge_step"]]
            if last.get("verdict") == node["exit_when"]["verdict"]:
                self.loop_outcome = LoopOutcome(
                    loop_id=node["id"], terminated_by="verdict_pass", termination_class="stop",
                    iterations_run=i, cost_micros=self.spent - cost_before, last_verdict=last)
                return
        self.loop_outcome = self.cap(
            node, node["max_iterations"], "iteration_ceiling", cost_before,
            Problem("deadline-exceeded",
                    f"loop {node['id']} ran {node['max_iterations']} of "
                    f"{node['max_iterations']} iterations without a pass verdict",
                    correlation_id=self.corr,
                    proposed_type="urn:agentic:problem:iteration-ceiling-reached").body)

    def cap(self, node, iterations, reason, cost_before, problem) -> LoopOutcome:
        """A cap termination escalates. There is no value that means carry on."""
        return LoopOutcome(loop_id=node["id"], terminated_by=reason, termination_class="cap",
                           iterations_run=max(iterations, 1),
                           cost_micros=self.spent - cost_before,
                           last_verdict=self.results.get(node["exit_when"]["judge_step"]),
                           escalation=problem)

    def do_gate(self, node) -> str:
        sid = self.sid(node["id"])
        key = self.key(sid)
        prior = self.done.get(key) if key else None
        if prior is not None:
            self.replayed += 1
            self.rows.append((sid, "replayed", 0, self.remaining, "decision already durable"))
            return prior.output["outcome"]
        gate = GateRecord(
            gate_id=gate_id_for(self.run_key, sid), correlation_id=self.corr,
            step_id=node["guards"], view=node["view"], decider=self.opts.decider,
            wires=[self.opts.wire], deadline_at=self.deadline(node), 
            return_to_step_id=node["return_to_step_id"])
        self.ex.park_gate(gate)
        self.gates_parked += 1
        raw = self.decisions[min(self.round, len(self.decisions) - 1)]
        outcome, _, actor = raw.partition(":")
        actor = actor or self.opts.decider
        if self.opts.gate_expired:
            # The deadline is a cap, not a stop: expiry terminates the run.
            self.expired += 1
            late = GateOutcome(gate.gate_id, self.corr, outcome, actor,
                               idempotency_key=f"gate:{gate.gate_id}:{outcome}",
                               delivered_over=self.opts.wire)
            self.step(sid, 0, lambda: {"outcome": "expired"})   # closes the gate
            self.late_applied += int(self.ex.record_decision(late))
            raise Problem("deadline-exceeded",
                          f"{gate.gate_id} on step {gate.step_id} closed undecided at "
                          f"{gate.deadline_at}; decider {gate.decider} was asked over "
                          f"{self.opts.wire}", correlation_id=self.corr,
                          instance=f"urn:agentic:gate:{gate.gate_id}")
        applied = 0
        for _ in range(self.opts.deliveries):
            oc = GateOutcome(gate.gate_id, self.corr, outcome, actor,
                             idempotency_key=f"gate:{gate.gate_id}:{outcome}",
                             body={"notes": self.opts.notes} if outcome != "approve" else {},
                             delivered_over=self.opts.wire)
            applied += int(self.ex.record_decision(oc))
        self.resumes_per_gate_max = max(self.resumes_per_gate_max, applied)
        self.wires.append(self.opts.wire)
        self.step(sid, 0, lambda: {"outcome": outcome, "actor": actor,
                                   "delivered_over": self.opts.wire})
        self.rows.append((sid, "gate", 0, self.remaining, f"{outcome} by {actor}"))
        return outcome

    def deadline(self, node) -> str:
        base = dt.datetime.strptime(self.env["occurred_at"], "%Y-%m-%dT%H:%M:%SZ")
        minutes = -60 if self.opts.gate_expired else node["deadline_minutes"]
        return (base + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def do_effect(self, node) -> None:
        sid = self.sid(node["id"])
        self.results[node["id"]] = self.step(
            sid, node["cost_micros"], lambda: {"text": f"published {self.run_key}"},
            effect={"published_run": self.run_key, "at": self.env["occurred_at"]})

    # -- the walk ------------------------------------------------------------
    def walk_from(self, start: int) -> int | None:
        for i in range(start, len(FLOW["steps"])):
            node = FLOW["steps"][i]
            op = node["op"]
            if op == "step":
                self.do_plain(node)
            elif op == "loop":
                self.do_loop(node)
                if self.loop_outcome.termination_class == "cap":
                    raise Problem(self.loop_outcome.escalation["type"].rsplit(":", 1)[-1],
                                  self.loop_outcome.escalation["detail"],
                                  correlation_id=self.corr,
                                  loop_outcome=loop_dict(self.loop_outcome))
            elif op == "gate":
                outcome = self.do_gate(node)
                if outcome == "reject":
                    self.stopped_by = "reject"
                    return None
                if outcome == "return_with_notes":
                    self.returns += 1
                    if self.returns > 2:
                        raise Problem("deadline-exceeded",
                                      f"gate returned {self.returns} times, bound is 2",
                                      correlation_id=self.corr)
                    back = [n["id"] for n in FLOW["steps"]].index(node["return_to_step_id"])
                    return back
            elif op == "effect":
                self.do_effect(node)
        return None

    def run(self) -> None:
        idx = 0
        while True:
            restart = self.walk_from(idx)
            if restart is None:
                return
            self.round += 1
            idx = restart


class Checkpointed:
    def __init__(self, output):
        self.output = output


def loop_dict(lo: LoopOutcome | None) -> dict | None:
    if lo is None:
        return None
    d = dict(lo.__dict__)
    return d


def report(d: Driver, outcome: str, problem: dict | None) -> dict:
    committed = d.ex.read_run(d.run_key)
    return {
        "run_key": d.run_key, "adapter_selected": d.opts.adapter,
        "executor_marker": d.state.executor_marker,      # read from the running executor
        "binding": d.ex.binding(), "outcome": outcome, "problem": problem,
        "entry_kind": d.env["kind"], "actor": d.actor,
        "correlation_id": d.corr, "correlation_source": d.correlation_source,
        "resume_point_at_start": d.state.resume_point,
        "pending_recovered": d.state.pending_recovered,
        "orphan_effect_at_start": d.orphan_effects,
        "effect_commit_mode": d.ex.effect_commit_mode,
        "steps_committed": committed.steps_committed, "steps_executed": d.executed,
        "steps_replayed": d.replayed, "prior_step_ids_seen": d.prior_seen,
        "budget_ceiling_micros": d.ceiling, "spent_micros": d.spent,
        "budget_remaining_micros": d.remaining,
        "loop": loop_dict(d.loop_outcome),
        "gates_parked": d.gates_parked, "resumes_per_gate_max": d.resumes_per_gate_max,
        "return_reentered_named_step": d.returns, "expired_gates": d.expired,
        "late_decisions_applied": d.late_applied,
        "sweeper_source": "scheduling-occurrence", "wires_used": sorted(set(d.wires)),
        "stopped_by": d.stopped_by, "rows": d.rows,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run one attempt of the durable flow.")
    ap.add_argument("--entry", required=True)
    ap.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--result", default="")
    ap.add_argument("--crash-at", default=None, help="kill -9 at this step, before its checkpoint")
    ap.add_argument("--decision", action="append", default=[],
                    help="outcome[:actor], one per gate ask, e.g. return_with_notes:agent:bot")
    ap.add_argument("--decider", default="user:corey")
    ap.add_argument("--wire", default="parked-item")
    ap.add_argument("--deliveries", type=int, default=1)
    ap.add_argument("--notes", default="tighten the release note")
    ap.add_argument("--budget-micros", type=int, default=None)
    ap.add_argument("--loop-never-pass", action="store_true")
    ap.add_argument("--gate-expired", action="store_true")
    ap.add_argument("--break-idempotency", action="store_true",
                    help="deliberate breakage: write the checkpoint with the step id alone")
    opts = ap.parse_args(argv)

    env = json.load(open(opts.entry))
    if opts.budget_micros is not None:
        env["budget"]["ceiling_micros"] = opts.budget_micros
    ex = None
    try:
        ex = executor_for(opts.adapter, opts.out)
        d = Driver(ex, env, opts)
        d.run()
        out = report(d, "stopped-on-reject" if d.stopped_by else "completed", None)
        ex.mark_terminal(d.run_key, out["outcome"])
    except Problem as p:
        try:
            out = report(d, "failed", p.body)
            ex.mark_terminal(d.run_key, "failed", p.body)
        except Exception:
            out = {"run_key": env["idempotency_key"], "adapter_selected": opts.adapter,
                   "outcome": "failed", "problem": p.body,
                   "executor_marker": getattr(ex, "executor_marker", "unset")}
        if opts.result:
            json.dump(out, open(opts.result, "w"), indent=2, default=str)
        print("PROBLEM (application/problem+json):")
        print(json.dumps(p.body, indent=2, default=str))
        return 2
    if opts.result:
        json.dump(out, open(opts.result, "w"), indent=2, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
