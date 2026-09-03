#!/usr/bin/env python3
"""The platform side of the linked section: one envelope in, one answer out.

Everything here is applied on the caller's behalf. Read it in this order:

  Ledger        the append-only, chained record a replay is decided against
  Linked.plan   the pure function envelope -> resolved plan, priced and
                complete before anything executes (F-b1-06)
  Linked.submit the one operation: validate, refuse a replay, price the plan,
                refuse a ceiling that cannot pay for it, then run
  Linked._turn  one durable step that dispatches one contained agent turn,
                whose own outward call is one completion by model class
  Linked._trace the run read back and reassembled by grouping on the run id

Four capability interfaces are used and no component is named: containment and
the agent turn, model access, telemetry, durable execution. Which
implementation serves each is read from the environment by components.py and
is never visible here or above.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import components  # noqa: E402
from interface import (Envelope, Plan, PlanStep, Platform, Problem, Receipt,  # noqa: E402
                       Result, digest)

# --- the declared unit of work: data, not code ------------------------------
FLOW = {
    "sequence_id": "linked-triage/0.1",
    "steps": [
        {"id": "intake", "op": "step", "cost_micros": 15000},
        {"id": "triage", "op": "agent-turn", "model_class": "i-fast"},
        {"id": "close", "op": "step", "cost_micros": 10000},
    ],
}
TURN = {"profile": "small", "op_seconds": 0.05, "grace_s": 0.5, "ceiling_s": 5.0}
MAX_OUTPUT_TOKENS = 256
MAX_CLAIMS = 8
LEVELS = 3                       # entry, the contained turn, the model call


def prompt_for(env: Envelope) -> str:
    """The task, and never the criterion it will be judged against."""
    return f"{env.intent['summary']}\n\nreport: {env.payload['report_text']}"


def _trace_id(seed: str) -> str:
    """Each level mints its own root trace, which is what a runtime that
    ignores an injected context does. Nothing reassembles a run from these."""
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


class Ledger:
    """Append-only and hash-chained: an entry that already completed is found
    here, so a replay is decided before any component is touched."""

    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.records = [json.loads(l) for l in open(path)] if os.path.exists(path) else []

    def head(self) -> str:
        return self.records[-1]["hash"] if self.records else "sha256:" + "0" * 64

    def append(self, **fields: Any) -> dict:
        rec = {"seq": len(self.records), "prev": self.head(), **fields}
        rec["hash"] = digest([rec["prev"], rec])
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        self.records.append(rec)
        return rec

    def completed(self, key: str) -> dict | None:
        return next((r for r in self.records if r.get("idempotency_key") == key), None)


class Linked(Platform):
    """The four component harnesses composed behind one entry envelope."""

    def __init__(self, out_dir: str) -> None:
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.parts = {name: components.Component(name) for name in components.COMPONENTS}
        self.schema, self.validate = components.entry_schema()
        self.ledger = Ledger(os.path.join(out_dir, "ledger.jsonl"))
        self.unavailable: Problem | None = None
        self.cont = self._bind("containment",
                               {"tuning": {"egress_probe_attempts": 3},
                                "jail_root": os.path.join(out_dir, "jails")})
        self.gw = self._bind("gateway")
        self.tr = self._bind("trace")
        self.wf = self._bind("workflow", out_dir)
        self.receipts: dict[str, Receipt] = {}
        self.units_admitted = 0
        self.observed: dict[str, str] = {}

    def _bind(self, name: str, *args):
        """An adapter that cannot be configured is one typed problem the caller
        reads later, never an exception out of construction."""
        try:
            return self.parts[name].build(*args)
        except Exception as exc:                       # noqa: BLE001
            body = getattr(exc, "body", None)
            if body is None and hasattr(exc, "problem"):
                body = exc.problem.as_dict()
            if body is None:
                raise
            self.unavailable = Problem.adopt(body, capability=name)
            return None

    # -- what a caller never asks for ---------------------------------------
    def iface(self, name: str):
        return self.parts[name].interface

    def selected(self) -> dict[str, str]:
        """Which adapter each capability is bound to. Configuration, reported
        for the swap proof and read by nothing that decides anything."""
        return {name: part.adapter_name for name, part in self.parts.items()}

    def markers(self) -> dict[str, str]:
        """Read from the running components: the marker the host read out of
        the unit, the marker the gateway response carried, the executor marker
        the journal was written with, and the telemetry pair's declared axis."""
        return dict(self.observed)

    def durable_records(self) -> int:
        rows = len(self.ledger.records)
        journal = os.path.join(self.out_dir, "journal.jsonl")
        if os.path.exists(journal):
            rows += sum(1 for line in open(journal) if line.strip())
        return rows

    # -- the plan: pure, and complete before anything runs -------------------
    def plan(self, env: Envelope) -> Plan:
        gi = self.iface("gateway")
        steps: list[PlanStep] = []
        for node in FLOW["steps"]:
            if node["op"] == "agent-turn":
                request = gi.CompletionRequest.from_dict(
                    {"model_class": node["model_class"],
                     "messages": [{"role": "user", "content": prompt_for(env)}],
                     "idempotency_key": "plan-estimate-only",
                     "ceiling_micros": env.ceiling_micros,
                     "max_output_tokens": MAX_OUTPUT_TOKENS})
                decision = gi.route(node["model_class"], env.ceiling_micros, env.ceiling_micros)
                estimate = gi.estimate_micros(decision, request)
                steps.append(PlanStep(node["id"], node["op"], node["model_class"], estimate))
            else:
                steps.append(PlanStep(node["id"], node["op"], "-", node["cost_micros"]))
        return Plan(FLOW["sequence_id"], tuple(steps),
                    sum(s.estimate_micros for s in steps), env.ceiling_micros)

    # -- the one operation ---------------------------------------------------
    def submit(self, doc: Mapping[str, Any]) -> Result | Problem:
        errors = self.validate(doc, self.schema)
        if errors:
            return Problem("document-invalid", "; ".join(errors[:3]),
                           entry_kind=doc.get("kind", "unknown"))
        env = Envelope.from_dict(doc)
        before = self.durable_records()
        try:
            prior = self.ledger.completed(env.idempotency_key)
            if prior is not None:
                if prior["envelope_digest"] != env.envelope_digest():
                    raise Problem("idempotency-conflict",
                                  f"key {env.idempotency_key} completed at seq {prior['seq']} "
                                  f"with a different envelope",
                                  correlation_id=env.correlation_id)
                self.receipts[env.run_id] = replace(
                    Receipt(**prior["receipt"]), durable_records_written=0,
                    units_admitted=0, gateway_dispatches=0)
                return replace(Result(**prior["result"]), outcome="replayed")
            if self.unavailable is not None:
                raise self.unavailable
            plan = self.plan(env)
            if plan.total_micros > env.ceiling_micros:
                raise Problem("budget-exhausted",
                              f"the resolved plan costs {plan.total_micros} micros and the ceiling "
                              f"is {env.ceiling_micros}; nothing was dispatched and no spend was "
                              f"incurred", correlation_id=env.correlation_id,
                              plan_micros=plan.total_micros, ceiling_micros=env.ceiling_micros,
                              enforcement_point="platform-pre-execution")
            return self._run(env, plan, before)
        except Problem as problem:
            if not problem.body.get("correlation_id"):
                problem.body["correlation_id"] = env.correlation_id
            problem.body.setdefault("durable_records_written", self.durable_records() - before)
            return problem
        except Exception as exc:                       # a component's own typed failure
            body = getattr(exc, "body", None)
            if body is None:
                raise
            return Problem.adopt(body, correlation_id=env.correlation_id,
                                 durable_records_written=self.durable_records() - before)

    # -- the run -------------------------------------------------------------
    def _run(self, env: Envelope, plan: Plan, before: int) -> Result:
        wi, ti = self.iface("workflow"), self.iface("trace")
        clock = datetime.strptime(env.occurred_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        instants = [(clock + timedelta(seconds=n)).strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(9)]
        record = ti.CorrelationRecord(run_id=env.run_id, root_dispatch_id=env.correlation_id,
                                      depth=0, entry_kind=env.kind)

        units_before, dispatches_before = self.units_admitted, self.gw.dispatches
        state = self.wf.begin_run(wi.BeginRun(
            run_key=env.idempotency_key, sequence_id=plan.sequence_id,
            input_digest=digest(env.payload), correlation_id=env.correlation_id,
            actor=env.actor_subject, ceiling_micros=env.ceiling_micros))
        remaining, costs, receipt = env.ceiling_micros - state.spent_micros, {}, {}

        for node, priced in zip(FLOW["steps"], plan.steps):
            key = wi.step_idempotency_key(env.idempotency_key, node["id"])
            if node["op"] == "agent-turn":
                cost, receipt = self._turn(env, remaining, key, record, instants)
            else:
                cost = node["cost_micros"]
            if cost > remaining:
                raise Problem("budget-exhausted",
                              f"step {node['id']} costs {cost} micros and {remaining} is left",
                              correlation_id=env.correlation_id, step_id=node["id"])
            self.wf.checkpoint_step(wi.Checkpoint(
                run_key=env.idempotency_key, step_id=node["id"], step_idempotency_key=key,
                output_digest=digest([node["id"], receipt.get("output_digest", "")]),
                cost_micros=cost, correlation_id=env.correlation_id, actor=env.actor_subject,
                output={"op": node["op"]}))
            remaining -= cost
            costs[node["id"]] = cost

        # the entry span, emitted at the level the run entered on
        ctx = self.tr.bind(record)
        self.tr.emit(ctx, ti.TelemetryUnit(
            operation=ti.OPERATION_NAMES["entry"], started_at=instants[0], ended_at=instants[6],
            outcome="ok", attributes={"gen_ai.operation.name": "invoke_agent"},
            trace_id=_trace_id(f"{env.run_id}/entry")))
        self.tr.measure(ctx, "step_duration", float(len(FLOW["steps"])))

        final = self.wf.read_run(env.idempotency_key)
        spent = env.ceiling_micros - remaining
        self.observed.update(
            containment=receipt.get("containment_marker", "absent"),
            gateway=self.gw.observed_marker or "absent",
            workflow=final.executor_marker,
            trace=f"semantic_queries_supported={self.tr.semantic_queries_supported}")
        result = Result(
            kind=env.kind, actor_subject=env.actor_subject, identity_hops=env.identity_hops,
            run_id=env.run_id, correlation_id=env.correlation_id,
            subject_digest=env.subject_digest(), plan_digest=plan.digest(),
            envelope_digest=env.envelope_digest(), outcome="completed",
            stop_reason=receipt["stop_reason"], spent_micros=spent,
            ceiling_micros=env.ceiling_micros)
        note = Receipt(
            run_id=env.run_id, kind=env.kind, step_costs=costs,
            nested_ceiling_micros=receipt["nested_ceiling_micros"],
            steps_committed=final.steps_committed, executor_spent_micros=final.spent_micros,
            trace=self._trace(env.run_id), containment=receipt["containment"],
            markers=self.markers(), units_admitted=self.units_admitted - units_before,
            gateway_dispatches=self.gw.dispatches - dispatches_before,
            negotiated=receipt["negotiated"], durable_records_written=0)
        self.ledger.append(kind="run-completed", idempotency_key=env.idempotency_key,
                           envelope_digest=env.envelope_digest(), run_id=env.run_id,
                           result=result.dict(), receipt=note.dict())
        self.receipts[env.run_id] = replace(note, durable_records_written=self.durable_records() - before)
        return result

    # -- one contained agent turn, whose outward call is one completion ------
    def _turn(self, env: Envelope, remaining: int, key: str, record, instants) -> tuple[int, dict]:
        ci, ti = self.iface("containment"), self.iface("trace")
        decl = ci.IsolationDeclaration.from_dict({"profile": TURN["profile"], "egress": "none"})
        unit = self.cont.admit(decl, ci.UnitContext(
            correlation_id=env.correlation_id, run_id=env.run_id, actor=env.actor_subject,
            idempotency_key=key, ceiling_s=TURN["ceiling_s"]))
        self.units_admitted += 1
        session = self.cont.open_session(unit, ci.SessionCapabilities(True, True, True))
        turn = self.cont.prompt(session, ci.TurnRequest(
            prompt_for(env), TURN["op_seconds"], TURN["grace_s"]))

        ticket = self._completion(env, remaining, key)          # the unit's outward call
        deadline, stop, frames = time.monotonic() + TURN["ceiling_s"], None, 0
        while stop is None and time.monotonic() < deadline:
            frame = self.cont.next_frame(turn, 0.02)
            if frame is None:
                continue
            frames += 1
            if frame.kind == "terminal":
                stop = frame.stop_reason
        unit_result = self.cont.terminate(unit, TURN["grace_s"])
        report = self.cont.inspect_containment(unit)

        child = replace(record, depth=1, parent_dispatch_id=record.root_dispatch_id)
        ctx = self.tr.bind(child)
        self.tr.emit(ctx, ti.TelemetryUnit(
            operation=ti.OPERATION_NAMES["dispatch"], started_at=instants[1], ended_at=instants[4],
            outcome="ok", attributes={"gen_ai.operation.name": "invoke_agent"},
            trace_id=_trace_id(session.runtime_marker + unit.unit_id)))
        leaf = replace(record, depth=2, parent_dispatch_id=f"{record.root_dispatch_id}-1")
        self.tr.emit(self.tr.bind(leaf), ti.TelemetryUnit(
            operation=ti.OPERATION_NAMES["tool"], started_at=instants[2], ended_at=instants[3],
            outcome="ok", attributes={"gen_ai.operation.name": "execute_tool"},
            trace_id=_trace_id(ticket.ticket_id)))
        return ticket.result.cost_micros, {
            "stop_reason": stop or "terminated",
            "nested_ceiling_micros": remaining,
            "output_digest": unit_result.output_digest,
            "containment_marker": report.containment_marker,
            "negotiated": {"streaming": session.negotiated.streaming,
                           "cancellation": session.negotiated.cancellation,
                           "frames": frames},
            "containment": {"observed_from": report.observed_from, "jail_mode": report.jail_mode,
                            "owner_in_host_passwd": report.owner_in_host_passwd,
                            "egress_attempts_made": report.egress_attempts_made,
                            "egress_attempts_blocked": report.egress_attempts_blocked,
                            "secrets_seen_inside": report.secrets_seen_inside,
                            "marker": report.containment_marker,
                            "unit_stop": unit_result.stop},
        }

    def _completion(self, env: Envelope, remaining: int, key: str):
        """One completion by model class, under what is left of the ceiling.
        No vendor, member model or endpoint is named here or anywhere above."""
        gi = self.iface("gateway")
        request = gi.CompletionRequest.from_dict(
            {"model_class": FLOW["steps"][1]["model_class"],
             "messages": [{"role": "user", "content": prompt_for(env)}],
             "idempotency_key": key, "ceiling_micros": remaining,
             "max_output_tokens": MAX_OUTPUT_TOKENS})
        ticket, claims = self.gw.submit(request), 0
        while ticket.state == "pending" and claims < MAX_CLAIMS:
            ticket, claims = self.gw.claim(ticket), claims + 1
        if ticket.state != "redeemed" or ticket.result is None:
            raise Problem("adapter-unavailable",
                          f"the completion was still {ticket.state} after {claims} claims",
                          correlation_id=env.correlation_id, retry_after_s=30)
        return ticket

    # -- the run read back ---------------------------------------------------
    def _trace(self, run_id: str) -> dict:
        ti = self.iface("trace")
        got = self.tr.fetch_run(run_id)
        if isinstance(got, ti.Problem):
            return {"problem": got.as_dict()}
        spans = [s for s in got if s.kind == "span"]
        with_run = [s for s in spans if s.resource.get(ti.RUN_ID_KEY) == run_id]
        with_root = [s for s in spans if s.resource.get(ti.ROOT_DISPATCH_ID_KEY)]
        one_group = len(with_run) == LEVELS and len({s.resource[ti.RUN_ID_KEY] for s in with_run}) == 1
        return {"signals": len(got), "spans": len(spans),
                "levels_covered": len({s.resource.get("correlation.depth") for s in with_run}),
                "run_id_groups": 1 if one_group else 0,
                "distinct_trace_ids": len({s.unit.get("trace_id") for s in spans if s.unit.get("trace_id")}),
                "spans_missing_run_id": LEVELS - len(with_run),
                "spans_missing_root_dispatch_id": LEVELS - len(with_root),
                "mapping_version": next((s.resource.get(ti.MAPPING_VERSION_KEY) for s in spans), "")}


def platform(out_dir: str) -> Linked:
    """One line for a caller: the four capabilities, bound by configuration."""
    return Linked(out_dir)
