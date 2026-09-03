#!/usr/bin/env python3
"""What every dispatcher does the same way, so the shims differ only in how the
unit executes.

The guarantee chain is here and in one fixed order (seam-dispatch-implement
step 5): claim the idempotency key, verify the delegation chain, record the
policy decision, take the budget reservation, then execute. Correlation is
stamped at dispatch as explicit members rather than inherited, because an
injected trace context is measured not to survive the agent boundary (F-a7-02).
A guarantee applied inside the unit would be a guarantee the unit could decline.

The step id and the step idempotency key are allocated here before execution and
the checkpoint reference is written at the first durable output, so an executor
that keeps no journal of its own still satisfies the seam's resume and replay
rules (seam-dispatch-implement step 6). `run_steps` is shared by the in-process
session and by the one-shot worker; the adapters supply only `execute_unit`.

No product name appears in this file.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import core  # noqa: E402
from adapters.steplog import StepLog  # noqa: E402
from interface import (Dispatcher, DispatchRequest, DispatchResult, Output,  # noqa: E402
                       Problem, StepRecord, Usage, canonical, digest, is_typed)

ROOT = os.path.dirname(HERE)
SCHEMA = os.path.join(ROOT, "schemas", "dispatch-request.schema.json")
FIXTURE_OBSERVATIONS = core.COST_OBSERVATIONS
observations_path = core.cost_source
HEADS = os.path.join(ROOT, "fixtures", "heads.json")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def breakage() -> str:
    """The deliberate breakages, selected by configuration so no source edit is
    needed between a green run and a red one."""
    return os.environ.get("DISPATCH_BREAK", "")


def pinned_head() -> str:
    return os.environ.get("DISPATCH_PLAN_HEAD") or json.load(open(HEADS))["head_full"]


def step_key(idempotency_key: str, step_id: str) -> str:
    """Per step, not per run, and derived so it is identical on every restart."""
    return "sha256:" + hashlib.sha256(f"{idempotency_key}|{step_id}".encode()).hexdigest()[:32]


# --------------------------------------------------------------------------
# The unit: the same step walk under both execution models.
# --------------------------------------------------------------------------
def run_steps(req_body: dict, plan: dict, log: StepLog, work,
              probe_cancel, prior: dict | None = None) -> dict:
    """Execute the document's steps under the ceiling, checkpointing each one.

    `work` is the executor's per-step call; `probe_cancel` is how this execution
    model learns a cancel was accepted - the session polls it after every
    checkpoint, and the one-shot worker has nothing to poll, which is the
    declared difference between the two adapters rather than a bug in one.
    """
    document = req_body["document"]
    workflow = core.load_example(document["workflow_ref"])
    agents = {a["name"]: a for a in core.load_example("agents.json")["agents"]}
    criterion = core.resolve_criterion(req_body["criterion_ref"])
    correlation = req_body["correlation"]
    prior = prior or {}
    floors = {s["step_id"]: s["floor_micros"] for s in plan["steps"]}

    state = {"remaining": req_body["budget"]["ceiling_micros"] - prior.get("spend_micros", 0),
             "spend": prior.get("spend_micros", 0), "outputs": [], "results": {},
             "executed": 0, "replayed": 0, "tokens_in": 0, "tokens_out": 0,
             "stop": "", "problem": None, "verdicts": [], "cancelled_after": None,
             "started": time.monotonic()}
    broken = breakage() == "durability" and os.environ.get("DISPATCH_BREAKABLE") == "1"

    def checkpoint(step_id: str, kind: str, text: str, cost: int, **extra) -> str | None:
        """The checkpoint reference is the head the record landed at. Under the
        deliberate breakage the result is assembled before this write returns,
        so the head a caller reads back is null while the record still exists."""
        record = dict(kind=kind, dispatch_id=req_body["dispatch_id"],
                      idempotency_key=req_body["idempotency_key"], step_id=step_id,
                      step_idempotency_key=step_key(req_body["idempotency_key"], step_id),
                      state="complete", cost_micros=cost,
                      output_digest=digest(text), output_text=text,
                      correlation_id=correlation.get("correlation_id", correlation["run_id"]),
                      actor=req_body["actor"]["subject"], ts=now(), **extra)
        if broken:
            log.append(**record)
            return None
        return log.append(**record)

    def already(step_id: str) -> dict | None:
        rec = prior.get("steps", {}).get(step_id)
        return rec if rec and rec.get("state") == "complete" else None

    def agent_step(node, iteration):
        sid = node["id"] + (f"#{iteration}" if iteration else "")
        done = already(sid)
        if done:                                   # committed work is not re-executed
            state["replayed"] += 1
            state["results"][node["id"]] = {"text": done["output_text"]}
            state["outputs"].append(Output(sid, done["output_digest"], "text/plain",
                                           done.get("checkpoint_ref")))
            return True
        floor = floors.get(sid, 0)
        if state["remaining"] < floor:             # reservation, before the metered call
            state["stop"] = "budget_exhausted"
            state["problem"] = Problem(
                "budget-exhausted",
                f"step {sid} reserves {floor} micros, {state['remaining']} left of the ceiling",
                step_id=sid, correlation=correlation).body
            return False
        profile = agents[node["agent"]]
        step_input = {"attempt": iteration or 1}
        for ref in node["input_from"]:
            if ref == "entry.payload":
                step_input[ref] = json.dumps(document["payload"])[:200]
            elif ref in state["results"]:
                step_input[ref] = state["results"][ref]["text"][:200]
        if "fix-judge" in node["input_from"]:      # the verdict travels, the criterion does not
            step_input["previous_verdict"] = state["results"].get("fix-judge", {}).get("verdict", "none")
            step_input.pop("fix-judge", None)
        out = work(profile, node["task"], step_input, correlation)
        state["spend"] += out["cost_micros"]
        state["remaining"] -= out["cost_micros"]
        state["tokens_in"] += out.get("tokens_in", 0)
        state["tokens_out"] += out.get("tokens_out", 0)
        state["executed"] += 1
        state["results"][node["id"]] = out
        head = checkpoint(sid, "step-committed", out["text"], out["cost_micros"],
                          op="agent", agent=node["agent"], model_class=profile["model_class"],
                          step_input=step_input)
        state["outputs"].append(Output(sid, digest(out["text"]), "text/plain", head))
        return True

    def judge_step(node, iteration):
        sid = node["id"] + (f"#{iteration}" if iteration else "")
        graded = state["results"].get(node["of"], {}).get("text", "")
        verdict = core.judge(graded, criterion)
        state["results"][node["id"]] = {"text": verdict.verdict, "verdict": verdict.verdict}
        state["verdicts"].append({"step_id": sid, "verdict": verdict.verdict,
                                  "checks_applied": verdict.checks_applied,
                                  "detail": verdict.detail})
        checkpoint(sid, "step-judged", verdict.verdict, 0, op="judge",
                   criterion_ref=node["criterion_ref"], checks_applied=verdict.checks_applied,
                   verdict_detail=verdict.detail)
        return verdict.verdict

    def walk(node, iteration=None) -> bool:
        if state["stop"]:
            return False
        op = node["op"]
        if op == "sequence":
            return all(walk(child, iteration) for child in node["steps"])
        if op == "parallel":       # one process here; the fan-out is the contract
            return all(walk(branch, iteration) for branch in node["branches"])
        if op == "loop":
            for i in range(1, node["max_iterations"] + 1):
                if not walk(node["body"], i):
                    return False
                if state["results"].get(node["exit_when"]["judge_step"], {}).get("verdict") \
                        == node["exit_when"]["verdict"]:
                    break
            return True
        if op == "agent":
            if not agent_step(node, iteration):
                return False
        elif op == "judge":
            judge_step(node, iteration)
        elif op == "approval":     # compose-approval owns the parked gate; here the
            checkpoint(node["id"], "step-approved",   # decision rides on the declared context
                       req_body.get("context", {}).get("standing_decision", "approve"), 0,
                       op="approval")
        if probe_cancel():         # the cancel probe: after the checkpoint, never before
            state["stop"] = "cancelled"
            state["cancelled_after"] = node["id"]
            return False
        if time.monotonic() - state["started"] > req_body["deadline"]["max_duration_s"]:
            state["stop"] = "deadline_exceeded"
            state["problem"] = Problem("deadline-exceeded",
                                       f"unit ran past max_duration_s "
                                       f"{req_body['deadline']['max_duration_s']}",
                                       correlation=correlation).body
            return False
        return True

    walk(workflow["root"])
    summary = "\n".join(o["text"] for o in state["results"].values()
                        if isinstance(o, dict) and "text" in o)
    stop = state["stop"] or "end_turn"
    lifecycle = {"": "completed", "end_turn": "completed", "cancelled": "canceled",
                 "budget_exhausted": "failed", "deadline_exceeded": "failed"}[stop]
    return {"state": lifecycle, "stop_reason": stop, "summary": summary,
            "outputs": [o.__dict__ for o in state["outputs"]],
            "spend_micros": state["spend"], "steps_executed": state["executed"],
            "steps_replayed": state["replayed"], "tokens_in": state["tokens_in"],
            "tokens_out": state["tokens_out"], "problem": state["problem"],
            "verdicts": state["verdicts"], "cancelled_after": state["cancelled_after"]}


# --------------------------------------------------------------------------
# The dispatcher
# --------------------------------------------------------------------------
class SeamDispatcher(Dispatcher):
    """The seam's five operations, with the guarantee chain around them. A shim
    supplies `execute_unit` and its four declared attributes, and nothing else.
    """

    binding_role = "today"
    cost_read_mode = "scan-and-fold"
    breakable = False              # only the shim the durability breakage targets

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.log = StepLog(os.path.join(out_dir, "steps.jsonl"))
        self.requests_path = os.path.join(out_dir, "recorded-dispatch-requests.jsonl")
        self.cancels_path = os.path.join(out_dir, "cancels.json")
        self.schema = json.load(open(SCHEMA))

    # -- plan inputs, read at one pinned head -------------------------------
    def cost_inputs(self, head: str) -> dict:
        if self.cost_read_mode == "scan-and-fold":
            return core.load_cost_inputs(observations_path(), head, "scan-and-fold")
        snaps = os.path.join(self.out_dir, "snapshots")
        core.materialise(observations_path(), head, snaps)
        return core.load_cost_inputs(snaps, head, "snapshot-by-digest")

    def head_for_plan(self) -> str:
        """The head the plan is read at. The `head` breakage makes one binding
        resolve it itself at call time instead of reading at the head it was
        handed, which is the only thing that changes."""
        if breakage() == "head" and self.binding_role == "second":
            return core.head_of(core.observations(observations_path()))
        return pinned_head()

    def plan_for(self, req_body: dict) -> core.Plan:
        head = self.head_for_plan()
        return core.plan(req_body["document"], head, self.cost_inputs(head))

    # -- the record the criterion leak scan reads ---------------------------
    def record_request(self, req_body: dict) -> None:
        row = {"dispatch_id": req_body["dispatch_id"], "document": req_body["document"],
               "criterion_ref": req_body["criterion_ref"], "context": req_body.get("context", {}),
               "isolation": req_body["isolation"], "actor": req_body["actor"]}
        with open(self.requests_path, "a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    # -- the guarantee chain ------------------------------------------------
    def admit(self, req: DispatchRequest, resuming: bool = False) -> core.Plan:
        body = req.dict()
        self.record_request(body)
        errs = core.validate(body, self.schema)                       # 0. shape, first
        if errs:
            raise Problem("document-invalid", "; ".join(errs[:4]),
                          dispatch_id=req.dispatch_id, instance="dispatch-request")
        prior = self.completed(req.idempotency_key)                   # 1. idempotency claim
        if prior and not resuming:
            if prior["request_digest"] != digest(body):
                raise Problem("idempotency-conflict",
                              f"key {req.idempotency_key} completed at seq {prior['seq']} "
                              f"with a different request body")
            raise _Replay(prior)
        for hop in req.actor["delegation_chain"]:                     # 2. delegation chain
            if hop.get("widens_scope"):
                raise Problem("policy-denied",
                              f"hop {hop.get('actor')} widens scope; a delegation may narrow "
                              f"and never widen", rule="delegation.no-widening")
        self.log.append(kind="policy-decision", dispatch_id=req.dispatch_id,  # 3. policy, recorded
                        idempotency_key=req.idempotency_key, decision="allow",
                        rule="dispatch.admit", actor=req.actor["subject"],
                        correlation_id=req.correlation.get("correlation_id", ""),
                        run_id=req.correlation["run_id"], ts=now())
        plan = self.plan_for(body)                                    # 4. budget reservation
        if plan.floor_micros > req.budget["ceiling_micros"]:
            raise Problem("budget-exhausted",
                          f"the shortest finishing path costs {plan.floor_micros} micros and the "
                          f"ceiling is {req.budget['ceiling_micros']}; refused before execution",
                          correlation=req.correlation)
        self.log.append(kind="dispatch-admitted", dispatch_id=req.dispatch_id,
                        idempotency_key=req.idempotency_key, request_digest=digest(body),
                        plan_digest=plan.plan_digest, plan_head=plan.head,
                        floor_micros=plan.floor_micros, worst_micros=plan.worst_micros,
                        ceiling_micros=req.budget["ceiling_micros"],
                        run_id=req.correlation["run_id"],
                        root_dispatch_id=req.correlation["root_dispatch_id"],
                        correlation_id=req.correlation.get("correlation_id", ""),
                        actor=req.actor["subject"], dispatcher=self.dispatcher_marker, ts=now())
        return plan

    # -- the five operations ------------------------------------------------
    def dispatch(self, req: DispatchRequest) -> DispatchResult:
        return self._execute(req, resuming=False)

    def resume(self, req: DispatchRequest) -> DispatchResult:
        return self._execute(req, resuming=True)

    def replay(self, req: DispatchRequest) -> DispatchResult:
        body = req.dict()
        prior = self.completed(req.idempotency_key)
        if not prior:
            raise Problem("idempotency-conflict",
                          f"key {req.idempotency_key} has no completed result to replay")
        if prior["request_digest"] != digest(body):
            raise Problem("idempotency-conflict",
                          f"key {req.idempotency_key} was completed with a different request body")
        return self.result_from(prior)

    def cancel(self, dispatch_id: str, grace_s: int) -> dict:
        """Acceptance, not a stop. Cancelling a dispatch that already reached a
        terminal state returns the current result and is not an error."""
        cancels = json.load(open(self.cancels_path)) if os.path.exists(self.cancels_path) else {}
        terminal = self.log.by(kind="dispatch-terminal", dispatch_id=dispatch_id)
        cancels[dispatch_id] = {"grace_s": grace_s, "accepted_at": now(),
                                "monotonic": time.monotonic(),
                                "already_terminal": bool(terminal)}
        with open(self.cancels_path, "w") as fh:
            json.dump(cancels, fh, indent=1, sort_keys=True)
        return {"accepted": True, "dispatch_id": dispatch_id, "grace_s": grace_s,
                "already_terminal": bool(terminal),
                "result": self.result_from(terminal[-1]).dict() if terminal else None}

    def read_step(self, dispatch_id: str, step_id: str | None = None) -> list[StepRecord]:
        out = []
        for rec in self.log.records():
            if rec.get("dispatch_id") != dispatch_id or not rec.get("step_id"):
                continue
            if step_id and rec["step_id"] != step_id:
                continue
            out.append(StepRecord(dispatch_id, rec["step_id"], rec["step_idempotency_key"],
                                  rec.get("state", "complete"), rec.get("hash"),
                                  rec.get("cost_micros", 0), rec.get("output_digest", ""),
                                  rec.get("correlation_id", ""), rec.get("actor", "")))
        return out

    # -- what an executor is asked for --------------------------------------
    def execute_unit(self, req_body: dict, plan: dict, prior: dict) -> dict:
        raise NotImplementedError

    def cancel_record(self, dispatch_id: str) -> dict | None:
        if not os.path.exists(self.cancels_path):
            return None
        return json.load(open(self.cancels_path)).get(dispatch_id)

    # -- shared plumbing ----------------------------------------------------
    def completed(self, idempotency_key: str) -> dict | None:
        done = [r for r in self.log.by(kind="dispatch-terminal")
                if r.get("idempotency_key") == idempotency_key and r.get("state") == "completed"]
        return done[-1] if done else None

    def prior_state(self, idempotency_key: str) -> dict:
        """What a resume reads: the committed steps of this key's lineage and
        what they already spent. The first step with no record is where a
        restart continues."""
        steps, spend = {}, 0
        for rec in self.log.records():
            if rec.get("idempotency_key") != idempotency_key or not rec.get("step_id"):
                continue
            if rec.get("state") == "complete":
                steps[rec["step_id"]] = {"output_text": rec.get("output_text", ""),
                                         "output_digest": rec.get("output_digest", ""),
                                         "checkpoint_ref": rec.get("hash"),
                                         "state": "complete"}
                spend += rec.get("cost_micros", 0)
        return {"steps": steps, "spend_micros": spend}

    def _execute(self, req: DispatchRequest, resuming: bool) -> DispatchResult:
        started = now()
        body = req.dict()
        try:
            plan = self.admit(req, resuming=resuming)
        except _Replay as replay:
            return self.result_from(replay.record)
        prior = self.prior_state(req.idempotency_key) if resuming else {}
        outcome = self.execute_unit(body, plan.dict(), prior)
        outputs = [Output("plan", plan.plan_digest, "application/json",
                          self.log.head())] + \
                  [Output(**o) for o in outcome["outputs"]]
        stop, state = outcome["stop_reason"], outcome["state"]
        cancel = self.cancel_record(req.dispatch_id)
        if cancel and stop != "cancelled":
            # A cancel was accepted and the unit did not stop on it. Which
            # ending that is depends on this adapter's declared reach, not on
            # what would read better: an executor that cannot be stopped once
            # started reports cancel_timeout.
            stop = "cancel_timeout" if self.cancellation_reach == "none" else stop
            state = "canceled"
        partial = state != "completed" and bool(outcome["outputs"])
        usage = Usage(outcome["spend_micros"], outcome["steps_executed"],
                      outcome["steps_replayed"], outcome["tokens_in"], outcome["tokens_out"])
        problem = outcome["problem"]
        result = DispatchResult(req.dispatch_id, state, stop, started, now(), partial,
                                outputs, usage, req.correlation, outcome["summary"],
                                problem, self.dispatcher_marker)
        self.log.append(kind="dispatch-terminal", dispatch_id=req.dispatch_id,
                        idempotency_key=req.idempotency_key, request_digest=digest(body),
                        state=state, stop_reason=stop, partial=partial,
                        plan_digest=plan.plan_digest, result=result.dict(),
                        dispatcher=self.dispatcher_marker,
                        correlation_id=req.correlation.get("correlation_id", ""),
                        run_id=req.correlation["run_id"], ts=now())
        return result

    def result_from(self, record: dict) -> DispatchResult:
        """The recorded result, byte for byte. A replay does not re-label what
        the first execution reported; that a replay happened is visible in the
        step log not growing, which is what a caller can check from outside."""
        stored = dict(record["result"])
        usage = Usage(**stored.pop("usage"))
        outputs = [Output(**o) for o in stored.pop("outputs")]
        return DispatchResult(outputs=outputs, usage=usage, **stored)


class _Replay(Exception):
    """A completed key answers with its stored result; nothing is re-executed."""

    def __init__(self, record: dict):
        self.record = record
        super().__init__("replay")


__all__ = ["SeamDispatcher", "run_steps", "now", "breakage", "pinned_head",
           "observations_path", "FIXTURE_OBSERVATIONS",
           "step_key", "Problem", "is_typed", "canonical"]
