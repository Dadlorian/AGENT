#!/usr/bin/env python3
"""examples/steer - approve, edit, reject, retry, escalate; and the operator's
reconnect, restart and replace of a stuck unit.

One entry envelope in, one steered unit out. Everything this run does that has
an effect - admitting the unit, the metered completion, firing the deploy,
applying a person's decision, touching a stuck cell - is put to one decision
point first, and is reachable only on the far side of an allow.

Read it in this order:
  plan()           prices the unit before anything runs (pure, no adapter)
  Gate             the one mediation point: it assembles the decision input from
                   platform-held facts, pins the policy version, takes the
                   decision, and runs the work inside the allow. Nothing in this
                   file calls a capability without going through it.
  run_unit()       the steps: admit, checkpoint, turn, intervene, complete,
                   propose, park, decide, retry, escalate, fire
  intervene()      the operator's three verbs, as capability operations
  Gate.journal()   what the run is graded on, read back off the engine's own
                   decision journal rather than off anything this file counted

Every capability behind this file is a harness adapter selected by
configuration. No product name appears here.

  python3 run.py --entry entries/human.json
  python3 run.py --entry entries/external.json          # reject, retry, escalate
  ENGINE=second python3 run.py --entry entries/human.json
  CELL=second   python3 run.py --entry entries/schedule.json
  python3 run.py --verify-ledger --ledger out/human.jsonl

Python 3.11 standard library only. No network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harnesses                       # noqa: E402

OUT = os.path.join(HERE, "out")
REF = harnesses.reference()            # the entry-schema validator and the hash-chained ledger
ENTRY_SCHEMA = os.path.normpath(os.path.join(HERE, "..", "end-to-end", "schemas", "entry.schema.json"))
STEER_SCHEMA = os.path.join(HERE, "schemas", "steer.schema.json")
POLICY_DIR = os.path.join(HERE, "policy")

# The published task lifecycle, adopted and not invented: an unknown state name
# is a defect here rather than a new word.
TASK_STATES = ("submitted", "working", "input-required", "completed",
               "failed", "cancelled", "rejected")

# The ontology's dispositions, adopted whole: what happens next after an
# attempt is judged. Not a fifth word, and not "success".
DISPOSITIONS = ("accept", "retry", "reject", "escalate")

SURFACE_FOR = {"stream": "second", "parked-item": "dryrun"}   # a declared surface -> an adapter
INTERVENTIONS = ("none", "reconnect", "restart", "replace")


# --- typed failures: one construction point ---------------------------------
ERRORS_IFACE, _ERRORS_WIRE = harnesses.errors()
STANDARD_MEMBERS = {"type", "title", "status", "detail", "retryable", "correlation_id"}
DROPPED_MEMBERS: list[str] = []        # extension members the closed registry would not carry
UNREGISTERED_TYPES: list[str] = []     # types a capability raised that the closed registry has no row for


def problem(suffix: str, detail: str, correlation_id: str | None = None, **ext) -> dict:
    """Every refusal this example returns is built by the errors capability's one
    shared construction point, against its closed registry. The registry closes
    the extension members too: a member it does not declare for that type is
    refused at construction, recorded here, and dropped."""
    try:
        return ERRORS_IFACE.construct(suffix, detail, correlation_id, **ext).body()
    except ERRORS_IFACE.UnregisteredType as exc:
        DROPPED_MEMBERS.append(str(exc))
        declared = ERRORS_IFACE.REGISTRY[suffix][3]
        kept = {k: v for k, v in ext.items() if k in declared}
        return ERRORS_IFACE.construct(suffix, detail, correlation_id, **kept).body()


def render_problem(body: dict) -> dict:
    """Re-render a capability's problem body through the one shared registry.

    Two things are measured rather than assumed. A type no row carries comes
    back marked `registry: absent` instead of being quietly re-typed, and every
    extension member the row does not declare is recorded as dropped - so a
    refusal that loses the fact a caller needed loses it visibly."""
    suffix = body["type"].rsplit(":", 1)[-1]
    if suffix not in ERRORS_IFACE.REGISTRY:
        UNREGISTERED_TYPES.append(body["type"])
        return dict(body, registry="absent")
    declared = ERRORS_IFACE.REGISTRY[suffix][3]
    ext = {k: v for k, v in body.items() if k not in STANDARD_MEMBERS}
    for key in sorted(ext):
        if key not in declared:
            DROPPED_MEMBERS.append(f"{suffix}:{key}")
    kept = {k: v for k, v in ext.items() if k in declared}
    return ERRORS_IFACE.construct(suffix, body["detail"], body.get("correlation_id"), **kept).body()


def fail(body: dict) -> int:
    print("PROBLEM (application/problem+json):\n" + json.dumps(body, indent=2, sort_keys=True))
    return 2


class Refused(Exception):
    """A refusal that ends the unit. Carries the rendered problem body."""

    def __init__(self, body: dict, state: str = "rejected"):
        self.body, self.state = body, state
        super().__init__(body["detail"])


# --- the ledger -------------------------------------------------------------
class Ledger:
    """The reference example's hash-chained ledger. Correlation rides on explicit
    attributes stamped on every record, never on trace parentage - and a human
    boundary is the longest gap in any run, so by the time someone decides there
    is no live trace left to be a parent."""

    def __init__(self, path, env):
        self.inner, self.env = REF.Ledger(path), env
        self.clock = datetime.strptime(env["occurred_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    def now(self) -> str:
        self.clock += timedelta(seconds=1)
        return self.clock.isoformat().replace("+00:00", "Z")

    def advance(self, seconds: int) -> str:
        self.clock += timedelta(seconds=int(seconds))
        return self.clock.isoformat().replace("+00:00", "Z")

    def record(self, kind, **fields):
        env = self.env
        return self.inner.append(
            ts=self.now(), kind=kind,
            run_id=env["correlation"]["run_id"], correlation_id=env["correlation"]["correlation_id"],
            actor=env["actor"]["subject"], delegation_depth=len(env["actor"]["delegation_chain"]),
            entry_kind=env["kind"], idempotency_key=env["idempotency_key"], **fields)


# --- the plan: pure, complete before anything executes ----------------------
def plan(unit_doc, env, gi):
    """(unit, envelope) -> priced steps and the floor. No side effects, no clock,
    no adapter: cost is knowable before commitment."""
    request = gi.CompletionRequest.from_dict(
        {"model_class": unit_doc["attempt_class"],
         "messages": [{"role": "user", "content": unit_doc["task"]}],
         "idempotency_key": "plan-estimate-only", "ceiling_micros": 10 ** 9})
    per_call = gi.estimate_micros(gi.route(unit_doc["attempt_class"], 10 ** 9, 10 ** 9), request)
    attempts = unit_doc["steering"]["retries_permitted"] + 1
    rows = [("admit the cell", "-", 0),
            ("checkpoint before the turn", "-", 0),
            ("one contained turn", "-", 0),
            ("one completion by class", unit_doc["attempt_class"], per_call),
            ("park the gate on a person", "-", 0),
            ("fire the declared effect", "-", 0)]
    return rows, per_call, per_call * attempts


# --- the one mediation point -------------------------------------------------
class Gate:
    """Every action of this run passes through here before it happens.

    Three things are the platform's and not the caller's. The *input* is
    assembled here from platform-held facts - the tenant directory, the
    envelope's own delegation chain, the ceiling remaining at this moment - so a
    caller cannot shape the question it will be judged on. The *version* is
    pinned to the digest of the bundle serving now, so the answer can be replayed
    later. And the *order* is fixed by the capability interface: `admit` takes
    the decision and only then reaches the work, so nothing runs on the far side
    of a deny.
    """

    def __init__(self, pi, engine, env, unit_doc, tenants, ledger, per_call_micros, bypass=False):
        self.pi, self.engine, self.env, self.unit = pi, engine, env, unit_doc
        self.tenants, self.ledger = tenants, ledger
        self.per_call = per_call_micros
        self.bypass = bypass
        self.ceiling = env["budget"]["ceiling_micros"]
        self.spent = 0
        self.rows: list[dict] = []
        self.bundles: dict = {}          # set by main(); the rule sets that may start serving
        self.revise = False              # activate the second bundle while the unit is parked
        self.activated: dict = {}        # label -> version, in the order they served
        self.down_at: str | None = None  # the point at which the engine is made unreachable

    # -- the input, assembled by the platform --------------------------------
    def subject(self, actor: str | None = None) -> dict:
        """Who is acting, and what they carry - read from the tenant directory
        and from the envelope's own delegation chain, never from a member a
        caller filled in.

        `actor` names a different acting subject for actions a person takes
        rather than the run: a decision at the human boundary is an action, and
        it names the person who took it. Their mandates are their own - acting
        directly is acting with none - so a run's mandates cannot be borrowed by
        whoever happens to be looking at the ask.
        """
        chain = self.env["actor"]["delegation_chain"]
        if actor is None:
            actor = self.env["actor"]["subject"]
            mandates = [hop["actor"] for hop in chain[1:] if hop["obtained_via"] != "direct"]
        else:
            mandates = []
        tenant = self.tenants.get(actor)
        if tenant is None:
            raise Refused(problem("identity-untrusted",
                                  f"{actor} holds no tenancy on this platform, so no decision input could be "
                                  f"assembled for it; an unknown principal is not a principal with no mandates",
                                  self.env["correlation"]["correlation_id"]))
        return {"id": actor, "tenant": tenant, "mandates": mandates}

    def decider(self) -> str:
        """The person this run acts for, read off the delegation chain: the last
        human hop, or the acting subject where there is none. Platform-held, like
        every other member of the input."""
        humans = [hop["actor"] for hop in self.env["actor"]["delegation_chain"]
                  if hop["actor"].startswith("user:")]
        return humans[-1] if humans else self.env["actor"]["subject"]

    def context(self, dispatch_id: str) -> dict:
        remaining = self.ceiling - self.spent
        return {"run_id": self.env["correlation"]["run_id"],
                "root_dispatch_id": dispatch_id,
                "correlation_id": self.env["correlation"]["correlation_id"],
                "entry_kind": self.env["kind"],
                "delegation_depth": len(self.env["actor"]["delegation_chain"]),
                "budget_remaining_micros": remaining,
                "budget_exhausted": remaining < self.per_call}

    # -- the gate ------------------------------------------------------------
    def gated(self, point, action, resource, dispatch_id, work=None, actor=None):
        """One decision, then the work. Returns (row, outcome, problem_body)."""
        ran = {"work": False}

        def wrapped(meter):
            ran["work"] = True
            return work(meter) if work is not None else None

        if self.down_at == point:
            # The engine is made unreachable at this point. What follows is the
            # fail-closed question asked at one enforcement point: an undecided
            # request is refused, and recorded as undecided rather than denied.
            os.environ["POLICY_FAIL"] = "1"
        doc = {"decision_point": point, "subject": self.subject(actor), "action": action,
               "resource": resource, "context": self.context(dispatch_id),
               "policy_version": self.engine.active_version}
        if self.bypass:
            # What a caller would send to turn the gate off. The vocabulary is
            # closed, so this is refused at the interface before any engine runs.
            doc["advisory"] = True
        before = self.engine.meter.spend(dispatch_id)
        decision = outcome = body = None
        effect, rule_id, digest_in = "undecided", "-", "-"
        version = doc["policy_version"]
        try:
            request = self.pi.DecisionRequest.from_dict(doc)
            digest_in = request.digest()
            decision, outcome = self.engine.admit(request, wrapped)
            effect, rule_id, version = decision.effect, decision.rule_id, decision.policy_version
        except self.pi.Problem as exc:
            raw = exc.body
            body = render_problem(raw)
            rule_id = raw.get("rule_id", "-")
            version = raw.get("policy_version", version)
            digest_in = raw.get("input_digest", digest_in)
            effect = "deny" if raw["type"].endswith("policy-denied") else "undecided"
        after = self.engine.meter.spend(dispatch_id)
        row = {"decision_point": point, "action": action, "dispatch_id": dispatch_id,
               "effect": effect, "rule_id": rule_id, "policy_version": version,
               "input_digest": digest_in, "work_ran": ran["work"],
               "spend_before_micros": before, "spend_after_micros": after,
               "problem_type": body["type"] if body else None,
               "resource": dict(resource), "decided_at": decision.decided_at if decision else "-"}
        self.rows.append(row)
        self.ledger.record("policy-decided", step=point, effect=effect, rule_id=rule_id,
                           policy_version=version, input_digest=digest_in,
                           dispatch_id=dispatch_id, work_ran=ran["work"],
                           spend_delta_micros=after - before,
                           problem_type=row["problem_type"], cost_micros=0)
        return row, outcome, body

    def charge(self, dispatch_id: str, micros: int) -> None:
        self.spent += micros

    def activate(self, bundle: dict) -> str:
        """A new rule set starts serving. The previous version stays resolvable,
        so a decision taken under it can still be replayed."""
        return self.engine.activate(bundle)

    def explain(self, input_digest: str, version: str):
        return self.engine.explain(input_digest, version)

    def journal(self) -> dict:
        taken, before_spend = self.engine.ordering()
        return {"decisions_taken": taken,
                "decided_before_that_action_spent": before_spend,
                "denied_dispatch_spend_micros": self.engine.denied_spend_micros(),
                "rule_id_present_on_every_decision": self.engine.rule_id_present(),
                "evaluations": self.engine.evaluations, "denies": self.engine.denies,
                "declared_subset": list(self.engine.conformance_subset),
                "engine": {"decision_model": self.engine.decision_model,
                           "activation_model": self.engine.activation_model,
                           "processes_required": self.engine.processes_required,
                           "reported_as": self.engine.report_adapter}}


# --- the operator's three verbs, as capability operations --------------------
def intervene(cell, ci, handle, operation, snapshot, session_caps):
    """reconnect, restart, replace - each an operation on the isolation adapter,
    not a script. Where the containment class cannot serve one, the adapter
    answers with a typed unsupported result and the platform records it as
    unserved; nothing here emulates a lifecycle operation the class does not
    have."""
    out = {"operation": operation, "served": False, "unit_before": handle.unit_id,
           "unit_after": None, "problem": None, "detail": None, "reprovisioned": False,
           "checkpoint_digest": snapshot.state_digest if snapshot else None,
           "unit_digest_at_intervention": None, "state_digest_after": None,
           "attached_to_a_unit_the_boundary_had_destroyed": None}
    try:
        if operation == "reconnect":
            session = cell.open_session(handle, session_caps)
            report = cell.inspect_containment(handle)
            out.update(served=True, unit_after=handle.unit_id, session_id=session.session_id,
                       negotiated={"streaming": session.negotiated.streaming,
                                   "permission_callbacks": session.negotiated.permission_callbacks,
                                   "cancellation": session.negotiated.cancellation},
                       containment_marker=report.containment_marker,
                       attached_to_a_unit_the_boundary_had_destroyed=True,
                       detail="re-attached to the unit the platform still holds; no new machine and "
                              "no re-resolution of the declaration - and nothing on this interface "
                              "says whether the unit was still attachable")
        elif operation == "restart":
            here = cell.pause(handle)                  # this unit's state now, read the same way
            out["unit_digest_at_intervention"] = here.state_digest
            if snapshot is None:
                snapshot = here                        # no pre-turn checkpoint: restart from now
                out["checkpoint_digest"] = here.state_digest
            restored = cell.resume(snapshot)
            after = cell.pause(restored)               # the same digest, before any further syscall
            report = cell.inspect_containment(restored)
            out.update(served=True, unit_after=restored.unit_id, state_digest_after=after.state_digest,
                       containment_marker=report.containment_marker,
                       detail="restored from the checkpoint taken before the turn; the declaration was "
                              "not resolved again")
        elif operation == "replace":
            here = cell.pause(handle)
            out["unit_digest_at_intervention"] = here.state_digest
            clone = cell.fork(handle)
            after = cell.pause(clone)                  # what the clone carries, read the same way
            report = cell.inspect_containment(clone)
            out.update(served=True, unit_after=clone.unit_id, state_digest_after=after.state_digest,
                       containment_marker=report.containment_marker,
                       detail="cloned from the stuck unit's own state, not from the checkpoint; the "
                              "stuck unit stays on file for whoever reads it")
    except ci.Problem as exc:
        out["problem"] = render_problem(exc.body)
        out["detail"] = exc.body["detail"]
    return out


# --- the steps inside the unit ----------------------------------------------
def run_unit(gate, env, unit_doc, ledger, args, ci, cell, callmod, gi, gw, store, surface, hi):
    corr = env["correlation"]["correlation_id"]
    steer = env["payload"]["steer"]
    steering = unit_doc["steering"]
    effect_decl = unit_doc["effect"]
    tenant = unit_doc["tenant"]
    events = []

    def event(type_, data):
        if type_ not in hi.EVENT_TYPES:
            raise SystemExit(f"{type_!r} is not one of the published event types {hi.EVENT_TYPES}")
        store.emit_event(type_, corr, ledger.now(), data)
        events.append(type_)

    event("run.started", {"unit": unit_doc["unit"], "entry_kind": env["kind"],
                          "actor": env["actor"]["subject"]})

    attempts_permitted = steering["retries_permitted"] + 1        # read at the loop bound
    escalation = steering["escalation"]
    report = {"attempts": [], "interventions": [], "retries": 0, "escalations": 0,
              "disposition": None, "artifact": None, "effect_fired": False,
              "asks": [], "refusals": [], "cost_micros": 0, "escalated_ask": None}
    decided = None
    attempt = 0

    while attempt < attempts_permitted:
        attempt += 1
        row = one_attempt(gate, env, unit_doc, ledger, args, ci, cell, callmod, gi, gw,
                          store, surface, hi, event, attempt, report)
        report["attempts"].append(row)
        if row["outcome"] == "gate-refused":
            report["disposition"] = "reject"
            return terminal(report, "failed", events)
        decided = row["decision"]
        if decided == "reject":
            if attempt < attempts_permitted:
                report["retries"] += 1
                ledger.record("retry", step="disposition", disposition="retry", attempt=attempt,
                              next_attempt=attempt + 1, attempts_permitted=attempts_permitted,
                              trigger="the gate rejected the proposal", cost_micros=0)
                continue
            break
        if decided is None:                                        # nobody decided; the ask expired
            report["disposition"] = "reject"
            return terminal(report, "failed", events)
        report["disposition"] = "accept"
        break

    if decided == "reject":
        # the attempts the unit permitted are spent: escalate one step, at most once
        if escalation["steps_permitted"] < 1:
            report["disposition"] = "reject"
            ledger.record("escalation-declined", step="disposition", disposition="reject",
                          steps_permitted=escalation["steps_permitted"],
                          trigger=escalation["trigger"], cost_micros=0)
            return terminal(report, "failed", events)
        report["escalations"] += 1
        report["disposition"] = "escalate"
        ledger.record("escalation", step="disposition", disposition="escalate",
                      steps_permitted=escalation["steps_permitted"], step_taken=1,
                      authority=escalation["authority"], trigger=escalation["trigger"],
                      attempts_spent=attempt, cost_micros=0)
        row = ask_and_decide(gate, env, unit_doc, ledger, args, store, surface, hi, event,
                             attempt=attempt, report=report, escalated=True,
                             authority=escalation["authority"],
                             decision_name=args.escalation_decision or steer["decision"])
        report["escalated_ask"] = {"attempt": attempt, "escalated": True, **row}
        if row["decision"] is None:
            return terminal(report, "failed", events)
        if row["decision"] == "reject":
            report["disposition"] = "reject"
            return terminal(report, "failed", events)
        report["artifact"] = row["artifact"]
        report["disposition"] = "accept"

    # the effect the gate stood in front of, decided again now that it may fire
    fired = fire_effect(gate, env, unit_doc, ledger, args, event, report, attempt)
    return terminal(report, "completed" if fired else "failed", events)


def terminal(report, state, events):
    report["state"] = state
    report["events"] = events
    return report


def one_attempt(gate, env, unit_doc, ledger, args, ci, cell, callmod, gi, gw,
                store, surface, hi, event, attempt, report):
    """One attempt: a cell, a checkpoint, a turn, an operator's verb where the
    turn did not finish, one completion, and the gate."""
    corr = env["correlation"]
    steer = env["payload"]["steer"]
    tenant = unit_doc["tenant"]
    row = {"attempt": attempt, "escalated": False}

    # -- admit the cell: declared resources, declared egress -----------------
    decl = ci.IsolationDeclaration.from_dict(unit_doc["isolation"])
    unit_ctx = ci.UnitContext(correlation_id=corr["correlation_id"], run_id=corr["run_id"],
                              actor=env["actor"]["subject"], idempotency_key=env["idempotency_key"],
                              ceiling_s=unit_doc["ceilings"]["wall_seconds"])
    handle = cell.admit(decl, unit_ctx)
    ledger.record("cell-admitted", step="dispatch", attempt=attempt, unit_id=handle.unit_id,
                  profile=handle.profile, egress=decl.egress, credentials=decl.credentials,
                  cost_micros=0)

    # -- the checkpoint the operator's restart will restore from -------------
    snapshot = None
    if unit_doc["intervention_policy"]["checkpoint_before_turn"]:
        try:
            snapshot = cell.pause(handle)
            ledger.record("cell-checkpointed", step="dispatch", attempt=attempt,
                          unit_id=handle.unit_id, snapshot_id=snapshot.snapshot_id,
                          state_digest=snapshot.state_digest, cost_micros=0)
        except ci.Problem as exc:
            body = render_problem(exc.body)
            report["refusals"].append({"where": "checkpoint", "type": body["type"],
                                       "status": body["status"], "ends_unit": False})
            ledger.record("refusal", step="checkpoint", attempt=attempt, problem_type=body["type"],
                          status=body["status"], ends_unit=False, rule_id="-", cost_micros=0)

    # -- one contained turn, both ceilings enforced outside it ---------------
    caps = ci.SessionCapabilities(streaming=True, permission_callbacks=True, cancellation=True)
    session = cell.open_session(handle, caps)
    op_seconds = (unit_doc["ceilings"]["stall_op_seconds"]
                  if (steer["stall_first_turn"] and attempt == 1)
                  else unit_doc["ceilings"]["turn_op_seconds"])
    request = ci.TurnRequest(f"{unit_doc['task']}\n\ninput: {env['payload']['subject']}",
                             op_seconds, unit_doc["ceilings"]["cancel_grace_s"])
    dispatch = callmod.Dispatch(cell, handle, session, request).start()
    result, _unit_result = dispatch.finish()
    for seq in range(1, result.frames + 1):
        event("step.progress", {"frame": seq, "of": result.frames, "attempt": attempt})
    stuck = result.stop_reason != "end_turn"
    ledger.record("turn-observed", step="dispatch", attempt=attempt, unit_id=handle.unit_id,
                  stop_reason=result.stop_reason, terminated_by=result.terminated_by or "-",
                  frames=result.frames, stuck=stuck, op_seconds=op_seconds, cost_micros=0)
    row.update(stop_reason=result.stop_reason, terminated_by=result.terminated_by,
               frames=result.frames, stuck=stuck, unit_id=handle.unit_id,
               checkpointed=snapshot is not None)

    # -- the operator steers the stuck cell ----------------------------------
    if stuck and steer["intervention"] != "none":
        row["intervention"] = steer_the_cell(gate, env, unit_doc, ledger, ci, cell, handle,
                                             snapshot, caps, steer["intervention"], attempt, report)

    # -- one completion by class: the metered call, decided first ------------
    dispatch_id = f"{corr['correlation_id']}#model-{attempt}"

    def completion(meter):
        ask = gi.CompletionRequest.from_dict(
            {"model_class": unit_doc["attempt_class"],
             "messages": [{"role": "user", "content": request.prompt}],
             "idempotency_key": f"{env['idempotency_key']}#model-{attempt}",
             "ceiling_micros": max(1, gate.ceiling - gate.spent)})
        ticket = gw.submit(ask)
        while ticket.state == "pending":
            ticket = gw.claim(ticket)
        meter.charge(dispatch_id, ticket.result.cost_micros)
        return ticket.result

    drow, priced, body = gate.gated("dispatch.model_call", "complete",
                                    {"tenant": tenant, "model_class": unit_doc["attempt_class"],
                                     "attempt": attempt}, dispatch_id, completion)
    if body is not None:
        raise Refused(body, state="failed")
    gate.charge(dispatch_id, priced.cost_micros)
    report["cost_micros"] += priced.cost_micros
    ledger.record("model-called", step="model", attempt=attempt,
                  model_class=unit_doc["attempt_class"], tokens_in=priced.tokens_in,
                  tokens_out=priced.tokens_out, cost_micros=priced.cost_micros)
    row.update(cost_micros=priced.cost_micros, tokens_in=priced.tokens_in,
               tokens_out=priced.tokens_out)

    # -- the effect is admitted once here, and again after the pause ---------
    effect_decl = unit_doc["effect"]
    prow, _o, pbody = gate.gated(effect_decl["decision_point"], "fire",
                                 {"tenant": tenant, "tool": effect_decl["tool"],
                                  "scope": effect_decl["scope"], "attempt": attempt},
                                 f"{corr['correlation_id']}#effect-{attempt}-proposed")
    event("tool.proposed", {"tool": effect_decl["tool"], "scope": effect_decl["scope"],
                            "attempt": attempt, "effect": prow["effect"]})
    row["effect_decision_before_pause"] = {"effect": prow["effect"], "rule_id": prow["rule_id"],
                                           "policy_version": prow["policy_version"],
                                           "input_digest": prow["input_digest"]}
    report["effect_decision_before_pause"] = row["effect_decision_before_pause"]
    if pbody is not None:
        row.update(outcome="gate-refused", decision=None, artifact=None)
        report["refusals"].append({"where": "effect-proposed", "type": pbody["type"],
                                   "status": pbody["status"], "ends_unit": True})
        ledger.record("refusal", step="effect-proposed", attempt=attempt,
                      problem_type=pbody["type"], status=pbody["status"], ends_unit=True,
                      rule_id=prow["rule_id"], cost_micros=0)
        return row

    # -- park a person in front of the effect --------------------------------
    row.update(ask_and_decide(gate, env, unit_doc, ledger, args, store, surface, hi, event,
                              attempt=attempt, report=report, escalated=False, authority="",
                              decision_name=steer["decision"]))
    return row


def steer_the_cell(gate, env, unit_doc, ledger, ci, cell, handle, snapshot, caps,
                   operation, attempt, report):
    """The operator's verb. Refused by the unit's own declaration first, then by
    policy, and only then reaching the isolation adapter."""
    tenant = unit_doc["tenant"]
    dispatch_id = f"{env['correlation']['correlation_id']}#intervention-{attempt}"
    permitted = unit_doc["intervention_policy"]["permitted"]
    if operation not in permitted:
        body = problem("document-invalid",
                       f"the unit permits the interventions {permitted} and {operation!r} is not one of "
                       f"them; it was refused by name before any decision was asked for",
                       env["correlation"]["correlation_id"])
        report["refusals"].append({"where": "intervention", "type": body["type"],
                                   "status": body["status"], "ends_unit": False})
        ledger.record("refusal", step="intervention", attempt=attempt, problem_type=body["type"],
                      status=body["status"], ends_unit=False, rule_id="-", cost_micros=0)
        out = {"operation": operation, "served": False, "problem": body,
               "refused_by": "the unit's intervention policy"}
        report["interventions"].append(out)
        return out

    result_box = {}

    def work(_meter):
        result_box["out"] = intervene(cell, ci, handle, operation, snapshot, caps)
        return result_box["out"]

    row, _outcome, body = gate.gated(unit_doc["intervention_policy"]["decision_point"], operation,
                                     {"tenant": tenant, "operation": operation,
                                      "unit_id": handle.unit_id}, dispatch_id, work)
    if body is not None:
        report["refusals"].append({"where": "intervention", "type": body["type"],
                                   "status": body["status"], "ends_unit": False})
        ledger.record("refusal", step="intervention", attempt=attempt, problem_type=body["type"],
                      status=body["status"], ends_unit=False, rule_id=row["rule_id"], cost_micros=0)
        out = {"operation": operation, "served": False, "problem": body,
               "refused_by": f"policy rule {row['rule_id']}", "work_ran": row["work_ran"]}
        report["interventions"].append(out)
        return out
    out = result_box["out"]
    out["decided_by_rule"] = row["rule_id"]
    ledger.record("intervention", step="intervention", attempt=attempt, operation=operation,
                  served=out["served"], unit_before=out["unit_before"],
                  unit_after=out["unit_after"] or "-", rule_id=row["rule_id"],
                  checkpoint_digest=out["checkpoint_digest"] or "-",
                  state_digest_after=out["state_digest_after"] or "-",
                  problem_type=(out["problem"] or {}).get("type", "-"), cost_micros=0)
    if out["problem"] is not None:
        report["refusals"].append({"where": "intervention", "type": out["problem"]["type"],
                                   "status": out["problem"]["status"], "ends_unit": False})
    report["interventions"].append(out)
    return out


def ask_and_decide(gate, env, unit_doc, ledger, args, store, surface, hi, event,
                   attempt, report, escalated, authority, decision_name):
    """input-required, then working again - or a deadline that closes the ask.

    The ask is stored before any surface sees it, the decision comes back on the
    run's own correlation id, and applying it is itself an action the gate
    decides: who may decide an escalated ask is a rule, not a convention.
    """
    corr = env["correlation"]["correlation_id"]
    steer = env["payload"]["steer"]
    gate_decl = unit_doc["gate"]
    tenant = unit_doc["tenant"]
    suffix = f"esc-{attempt}" if escalated else f"{attempt}"
    ask_id = f"ask-{env['entry_id']}-{suffix}"
    parked_at = ledger.now()
    deadline = (datetime.strptime(parked_at, "%Y-%m-%dT%H:%M:%SZ")
                + timedelta(seconds=gate_decl["deadline_seconds"])).isoformat() + "Z"
    prompt = gate_decl["prompt"] if not escalated else (
        f"Escalated after {attempt} attempt(s): {gate_decl['prompt']}")
    ask = hi.HumanAsk(ask_id=ask_id, correlation_id=corr, prompt=prompt,
                      response_schema=gate_decl["response_schema"],
                      proposed=gate_decl["proposed"], deadline_at=deadline,
                      allowed_decisions=tuple(unit_doc["steering"]["decisions_offered"]))
    try:
        surface.ask(ask, env, parked_at)
    except hi.Problem as exc:
        # the same envelope submitted twice parks no second ask: the store holds
        # one row per ask id and a redelivery is a replay, not a new question
        raise Refused(render_problem(exc.body), state="failed")
    ledger.record("approval-parked", step="gate", state="input-required", attempt=attempt,
                  ask_id=ask_id, escalated=escalated, authority=authority or "-",
                  deadline_at=deadline, irreversibility=gate_decl["proposed"]["irreversibility"],
                  offered=",".join(unit_doc["steering"]["decisions_offered"]), cost_micros=0)
    report["asks"].append({"ask_id": ask_id, "escalated": escalated, "authority": authority,
                           "deadline_at": deadline})

    # A rule set starts serving while this unit is parked. The unit holds no
    # residual authorisation across the pause: the effect it was admitted to
    # fire is decided again on the far side, against the rules in force then.
    if gate.revise and "v2" not in gate.activated:
        version = gate.activate(gate.bundles["v2"])
        gate.activated["v2"] = version
        ledger.record("policy-activated", step="gate", policy_version=version,
                      bundle_label=gate.bundles["v2"]["bundle_version_label"],
                      while_task_state="input-required", ask_id=ask_id, cost_micros=0)

    now = ledger.advance(steer["decision_delay_seconds"])
    if decision_name == "none":
        try:
            parked = surface.expire(ask_id, now)
        except hi.Problem as exc:
            # The deadline is the store's to enforce, not this runner's to
            # assume. A sweep asked for before the ask is due is refused, typed,
            # and ends the unit the way every other refusal here does: nobody
            # decided and the ask is still open, so there is nothing to resume
            # on. A traceback would be a refusal a caller has to parse from
            # prose (`F-b4-07`).
            refused = render_problem(exc.body)
            # This refusal ends the unit the same way an admission refusal does
            # (`fail()`), so it is surfaced to the caller the same way: printed
            # as the typed problem body, not left to a summary table only.
            print("PROBLEM (application/problem+json):\n" + json.dumps(refused, indent=2, sort_keys=True))
            report["refusals"].append({"where": "ask", "type": refused["type"],
                                       "status": refused["status"], "ends_unit": True})
            ledger.record("refusal", step="gate", attempt=attempt, ask_id=ask_id,
                          problem_type=refused["type"], status=refused["status"],
                          ends_unit=True, rule_id="-", cost_micros=0)
            event("human.refused", {"ask_id": ask_id, "problem_type": refused["type"]})
            return {"outcome": "sweep-refused", "decision": None, "artifact": None,
                    "ask_id": ask_id, "problem": refused}
        body = problem("deadline-exceeded",
                       f"{ask_id} closed at {deadline} with no decision; the unit ends rather than "
                       f"waiting, because an ask with no deadline is a run that waits forever",
                       corr, retry_after_s=0)
        report["refusals"].append({"where": "ask", "type": body["type"], "status": body["status"],
                                   "ends_unit": True})
        ledger.record("ask-expired", step="gate", state="failed", attempt=attempt, ask_id=ask_id,
                      ask_state=parked.state, problem_type=body["type"], cost_micros=0)
        return {"outcome": "expired", "decision": None, "artifact": None, "ask_id": ask_id}

    decider = args.decider or (authority if escalated else gate.decider())
    body_doc = dict(steer["decision_body"])
    if decision_name == "edit" and not body_doc:
        body_doc = {"component": "pricing/discount.py", "note": "edited by the reviewer"}
    if args.decision_body is not None:
        body_doc = json.loads(args.decision_body)

    # applying a person's decision is an action like any other
    drow, _o, dbody = gate.gated("steer.decision", decision_name,
                                 {"tenant": tenant, "ask_id": ask_id, "decision": decision_name,
                                  "authority": authority, "attempt": attempt},
                                 f"{corr}#decision-{suffix}", actor=decider)
    if dbody is not None:
        report["refusals"].append({"where": "steer.decision", "type": dbody["type"],
                                   "status": dbody["status"], "ends_unit": True})
        ledger.record("refusal", step="steer.decision", attempt=attempt, problem_type=dbody["type"],
                      status=dbody["status"], ends_unit=True, rule_id=drow["rule_id"], cost_micros=0)
        event("human.refused", {"ask_id": ask_id, "problem_type": dbody["type"],
                                "rule_id": drow["rule_id"]})
        return {"outcome": "gate-refused", "decision": None, "artifact": None, "ask_id": ask_id}

    decision = hi.HumanDecision(ask_id=ask_id, correlation_id=corr, decision=decision_name,
                                actor=decider,
                                idempotency_key=f"{env['idempotency_key']}#{suffix}-{decision_name}",
                                body=body_doc)
    try:
        ack = surface.decide(decision, now)
    except hi.Problem as exc:
        refused = render_problem(exc.body)
        report["refusals"].append({"where": "decision", "type": refused["type"],
                                   "status": refused["status"], "ends_unit": True})
        ledger.record("refusal", step="decision", attempt=attempt, problem_type=refused["type"],
                      status=refused["status"], ends_unit=True, rule_id="-", cost_micros=0)
        event("human.refused", {"ask_id": ask_id, "problem_type": refused["type"]})
        return {"outcome": "refused", "decision": None, "artifact": None, "ask_id": ask_id}

    ledger.record("approval-returned", step="gate", state="working", attempt=attempt,
                  ask_id=ask_id, decision=ack.decision, applied=ack.applied,
                  decided_by=ack.decided_by, escalated=escalated,
                  resumed_on_same_correlation=ack.correlation_id == corr,
                  artifact_digest=hashlib.sha256(
                      json.dumps(ack.artifact, sort_keys=True).encode()).hexdigest()[:16],
                  resume_delegation_depth=len(ack.stamps["delegation_chain"]), cost_micros=0)

    # a redelivery of the same decision is one act arriving twice; a different
    # decision on a decided ask is a conflict, and both are recorded
    replay = hi.HumanDecision(ask_id=ask_id, correlation_id=corr, decision=decision_name,
                              actor=decider, idempotency_key=decision.idempotency_key,
                              body=body_doc)
    conflict = hi.HumanDecision(ask_id=ask_id, correlation_id=corr,
                                decision="approve" if decision_name != "approve" else "reject",
                                actor=decider, idempotency_key=f"{decision.idempotency_key}#again",
                                body={})
    replay_outcome = conflict_type = None
    try:
        replay_outcome = surface.decide(replay, now).outcome
    except hi.Problem as exc:                                  # not expected: a replay is free
        replay_outcome = render_problem(exc.body)["type"]
    try:
        surface.decide(conflict, now)
    except hi.Problem as exc:
        conflict_body = render_problem(exc.body)
        conflict_type = conflict_body["type"]
        report["refusals"].append({"where": "second-decision", "type": conflict_type,
                                   "status": conflict_body["status"], "ends_unit": False})
        ledger.record("refusal", step="second-decision", attempt=attempt,
                      problem_type=conflict_type, status=conflict_body["status"],
                      ends_unit=False, rule_id="-", cost_micros=0)
        event("human.refused", {"ask_id": ask_id, "problem_type": conflict_type})

    report["artifact"] = ack.artifact
    return {"outcome": "decided", "decision": ack.decision, "artifact": ack.artifact,
            "ask_id": ask_id, "decided_by": ack.decided_by,
            "resumed_on_same_correlation": ack.correlation_id == corr,
            "replay_outcome": replay_outcome, "second_decision_refused": conflict_type,
            "resume_delegation_depth": len(ack.stamps["delegation_chain"]),
            "surface": ack.surface}


def fire_effect(gate, env, unit_doc, ledger, args, event, report, attempt):
    """The side-effecting step the gate stood in front of. It is decided again
    here, against the rule set in force now: an allow names the single action it
    admits and the moment it was taken, and this one was taken before a person
    was asked."""
    effect_decl = unit_doc["effect"]
    tenant = unit_doc["tenant"]
    corr = env["correlation"]["correlation_id"]
    fired = {"ran": False}

    if args.carry_decision:
        # BREAKAGE: the resume reuses the allow taken before the pause instead of
        # taking a fresh decision. Nothing else changes.
        before = report["effect_decision_before_pause"]
        report["effect_decision_after_resume"] = dict(before, carried=True)
        report["decisions_at_effect"] = 1
        report["effect_fired"] = True
        ledger.record("effect-applied", step="effect", attempt=attempt, tool=effect_decl["tool"],
                      decided_again=False, rule_id=before["rule_id"],
                      policy_version=before["policy_version"], cost_micros=0)
        return True

    def apply(_meter):
        fired["ran"] = True
        return {"tool": effect_decl["tool"], "artifact": report["artifact"]}

    row, _out, body = gate.gated(effect_decl["decision_point"], "fire",
                                 {"tenant": tenant, "tool": effect_decl["tool"],
                                  "scope": effect_decl["scope"], "attempt": attempt},
                                 f"{corr}#effect-{attempt}-resumed", apply)
    report["effect_decision_after_resume"] = {"effect": row["effect"], "rule_id": row["rule_id"],
                                              "policy_version": row["policy_version"],
                                              "input_digest": row["input_digest"],
                                              "carried": False}
    report["decisions_at_effect"] = 2
    if body is not None:
        report["refusals"].append({"where": "effect-resumed", "type": body["type"],
                                   "status": body["status"], "ends_unit": True})
        ledger.record("refusal", step="effect-resumed", attempt=attempt, problem_type=body["type"],
                      status=body["status"], ends_unit=True, rule_id=row["rule_id"], cost_micros=0)
        event("tool.proposed", {"tool": effect_decl["tool"], "attempt": attempt,
                                "effect": row["effect"]})
        return False
    report["effect_fired"] = fired["ran"]
    ledger.record("effect-applied", step="effect", attempt=attempt, tool=effect_decl["tool"],
                  decided_again=True, rule_id=row["rule_id"], policy_version=row["policy_version"],
                  artifact_digest=hashlib.sha256(
                      json.dumps(report["artifact"], sort_keys=True).encode()).hexdigest()[:16],
                  cost_micros=0)
    return fired["ran"]


# --- what the caller sees ----------------------------------------------------
def task_status(events) -> str:
    """A pure projection of the typed event stream onto the published task
    lifecycle. There is no status-change event in the published vocabulary, so
    the state is derived rather than subscribed to."""
    state = "submitted"
    for event in events:
        if event.type == "run.started":
            state = "working"
        elif event.type == "human.ask":
            state = "input-required"
        elif event.type == "human.decided":
            state = "working"
        elif event.type == "ask.expired":
            state = "failed"
        elif event.type == "run.finished":
            state = event.data.get("outcome", "completed")
    if state not in TASK_STATES:
        raise SystemExit(f"{state!r} is not one of the published task states {TASK_STATES}")
    return state


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))


# --- wiring ------------------------------------------------------------------
def parse(argv):
    ap = argparse.ArgumentParser(description="Run one unit and steer it.")
    ap.add_argument("--entry", help="path to an entry envelope")
    ap.add_argument("--unit", help="override the unit the envelope's intent.workflow_ref names")
    ap.add_argument("--ledger", default=os.path.join(OUT, "run.jsonl"))
    ap.add_argument("--report", help="write the run report as JSON here")
    ap.add_argument("--engine", help="policy engine adapter (default $ENGINE or dryrun)")
    ap.add_argument("--cell", help="containment adapter (default $CELL or dryrun)")
    ap.add_argument("--surface", choices=["stream", "parked-item"], help="override payload.steer.surface")
    ap.add_argument("--decision", choices=["approve", "edit", "reject", "none"],
                    help="override payload.steer.decision")
    ap.add_argument("--decision-body", help="override the decision body (JSON)")
    ap.add_argument("--escalation-decision", choices=["approve", "edit", "reject", "none"],
                    help="what the escalation authority decides (default: the same as --decision)")
    ap.add_argument("--decider", help="who decides (default: the entry's actor, or the escalation authority)")
    ap.add_argument("--intervention", choices=list(INTERVENTIONS),
                    help="override payload.steer.intervention")
    ap.add_argument("--delay", type=int, help="override payload.steer.decision_delay_seconds")
    ap.add_argument("--stall", dest="stall", action="store_const", const=True, default=None)
    ap.add_argument("--no-stall", dest="stall", action="store_const", const=False)
    ap.add_argument("--retries", type=int, help="override the unit's steering.retries_permitted")
    ap.add_argument("--escalation-steps", type=int,
                    help="override the unit's steering.escalation.steps_permitted")
    ap.add_argument("--budget-micros", type=int, help="override the envelope ceiling")
    ap.add_argument("--revise-policy", action="store_true",
                    help="activate the second bundle while the run is parked")
    ap.add_argument("--carry-decision", action="store_true",
                    help="deliberate breakage: reuse the pre-pause allow instead of deciding again")
    ap.add_argument("--bypass", action="store_true",
                    help="send a field that would turn the gate off, to see it refused")
    ap.add_argument("--engine-down-at",
                    help="make the decision engine unreachable at this decision point")
    ap.add_argument("--verify-ledger", action="store_true")
    return ap.parse_args(argv)


def overrides(steer, unit_doc, args):
    applied = []
    for flag, node, key in (("surface", steer, "surface"), ("decision", steer, "decision"),
                            ("intervention", steer, "intervention"),
                            ("delay", steer, "decision_delay_seconds"),
                            ("stall", steer, "stall_first_turn")):
        value = getattr(args, flag)
        if value is not None:
            node[key] = value
            applied.append(f"payload.steer.{key}={value}")
    if args.decision_body is not None:
        steer["decision_body"] = json.loads(args.decision_body)
        applied.append("payload.steer.decision_body=<given>")
    if args.retries is not None:
        unit_doc["steering"]["retries_permitted"] = args.retries
        applied.append(f"steering.retries_permitted={args.retries}")
    if args.escalation_steps is not None:
        unit_doc["steering"]["escalation"]["steps_permitted"] = args.escalation_steps
        applied.append(f"steering.escalation.steps_permitted={args.escalation_steps}")
    return applied


def main(argv=None):
    args = parse(argv)
    if args.verify_ledger:
        led = REF.Ledger(args.ledger)
        broken = led.verify()
        print(f"ledger {args.ledger}: {len(led.records)} records, " + (broken or "chain verifies"))
        return 2 if broken else 0
    if not args.entry:
        return fail(problem("document-invalid", "--entry is required unless --verify-ledger is given"))

    env = json.load(open(args.entry))
    errs = REF.validate(env, json.load(open(ENTRY_SCHEMA)))
    if errs:
        return fail(problem("document-invalid", "; ".join(errs[:4]), causes=errs[:4]))
    steer_errs = REF.validate(env.get("payload", {}).get("steer"), json.load(open(STEER_SCHEMA)))
    if steer_errs:
        return fail(problem("document-invalid", "payload.steer: " + "; ".join(steer_errs[:4]),
                            env["correlation"]["correlation_id"], causes=steer_errs[:4]))

    unit_path = args.unit or os.path.join(HERE, env["intent"]["workflow_ref"])
    unit_doc = json.load(open(unit_path))
    steer = env["payload"]["steer"]
    applied = overrides(steer, unit_doc, args)
    if args.budget_micros is not None:
        env["budget"]["ceiling_micros"] = args.budget_micros
        applied.append(f"budget.ceiling_micros={args.budget_micros}")

    os.makedirs(OUT, exist_ok=True)
    ledger = Ledger(args.ledger, env)
    engine_name = args.engine or os.environ.get("ENGINE", "dryrun")
    cell_name = args.cell or os.environ.get("CELL", "dryrun")
    pi, PolicyAdapter = harnesses.policy(engine_name)
    hi, hstore, HSurface = harnesses.human(SURFACE_FOR[steer["surface"]])
    ci, CellAdapter, callmod = harnesses.containment(cell_name)
    gi, GatewayAdapter = harnesses.gateway("dryrun")

    points = json.load(open(os.path.join(POLICY_DIR, "points.json")))["points"]
    bundles = {name: json.load(open(os.path.join(POLICY_DIR, f"bundle.{name}.json")))
               for name in ("v1", "v2")}
    tenants = json.load(open(os.path.join(POLICY_DIR, "tenants.json")))["subjects"]
    engine = PolicyAdapter(bundle=bundles["v1"], points=points)

    store = hstore.ParkedAskStore(os.path.join(
        OUT, "asks", os.path.splitext(os.path.basename(args.ledger))[0],
        env["correlation"]["correlation_id"]))
    surface = HSurface(store)
    cell = CellAdapter(json.load(open(os.path.join(harnesses.ROOT, "harness", "containment",
                                                   "binding.json"))))

    steps, per_call, floor = plan(unit_doc, env, gi)
    ceiling = env["budget"]["ceiling_micros"]
    gate = Gate(pi, engine, env, unit_doc, tenants, ledger, per_call, bypass=args.bypass)
    gate.bundles = bundles
    gate.revise = args.revise_policy
    gate.down_at = args.engine_down_at
    os.environ.pop("POLICY_FAIL", None)
    gate.activated = {"v1": engine.active_version}

    print(f"INTENT  {env['intent']['summary']}")
    print(f"PLAN  {unit_doc['unit']}: {unit_doc['steering']['retries_permitted'] + 1} attempt(s) "
          f"permitted, one completion each at {per_call} micros, shortest finishing path {floor}, "
          f"ceiling {ceiling}. Gate: {steer['decision']} on a '{steer['surface']}' surface; "
          f"operator intervention '{steer['intervention']}'"
          + (f"; overrides {applied}" if applied else ""))
    table([(s[0], s[1], s[2]) for s in steps], ("step", "model_class", "est_micros"))
    ledger.record("unit-submitted", step="-", state="submitted", plan_floor_micros=floor,
                  ceiling_micros=ceiling, workflow_ref=env["intent"]["workflow_ref"],
                  unit=unit_doc["unit"], summary=env["intent"]["summary"],
                  attempt_class=unit_doc["attempt_class"],
                  retries_permitted=unit_doc["steering"]["retries_permitted"],
                  escalation_steps_permitted=unit_doc["steering"]["escalation"]["steps_permitted"],
                  surface=steer["surface"], intervention=steer["intervention"],
                  policy_version=engine.active_version, cost_micros=0)

    corr = env["correlation"]["correlation_id"]
    report = {"entry": env["kind"], "run_id": env["correlation"]["run_id"], "correlation_id": corr,
              "steer": steer, "overrides": applied, "engine_adapter": engine_name,
              "cell_adapter": cell_name, "policy_versions": gate.activated}

    try:
        # admission: the first decision, before a cell exists
        arow, _out, abody = gate.gated("admission.entry", "admit",
                                       {"tenant": unit_doc["tenant"],
                                        "workflow_ref": env["intent"]["workflow_ref"],
                                        "summary": env["intent"]["summary"]},
                                       f"{corr}#admission")
        report["admission"] = arow
        if abody is not None:
            raise Refused(abody, state="rejected")

        run = run_unit(gate, env, unit_doc, ledger, args, ci, cell, callmod, gi,
                       GatewayAdapter(), store, surface, hi)
        state = run.pop("state")
        run.pop("events")           # the stream is the record; a second list would be a second truth
        store.emit_event("run.finished", corr, ledger.now(),
                         {"outcome": state, "disposition": run["disposition"]})
        report["run"] = run
    except Refused as refused:
        state = refused.state
        report["problem"] = refused.body
        report["run"] = {"disposition": "reject", "refusals": [
            {"where": "admission", "type": refused.body["type"],
             "status": refused.body["status"], "ends_unit": True}]}
        ledger.record("refusal", step="admission", problem_type=refused.body["type"],
                      status=refused.body["status"], ends_unit=True,
                      rule_id=refused.body.get("rule_id", "-"), cost_micros=0)
        ledger.record("unit-" + state, step="-", state=state, cost_micros=0)
        report["journal"] = gate.journal()
        report["decisions"] = gate.rows
        report["status"] = state
        report["dropped_registry_members"] = DROPPED_MEMBERS
        report["unregistered_types"] = UNREGISTERED_TYPES
        if args.report:
            json.dump(report, open(args.report, "w"), indent=1, sort_keys=True, default=str)
        return fail(refused.body)

    all_events = store.events(corr)
    projected = task_status(all_events)
    if projected != state:
        raise SystemExit(f"the projection says {projected!r} and the run says {state!r}")
    ledger.record("unit-" + state, step="-", state=state,
                  disposition=report["run"]["disposition"], cost_micros=report["run"]["cost_micros"])

    report["status"] = state
    report["events_on_the_stream"] = [e.type for e in all_events]
    report["events_rendered"] = [e.type for e in surface.watch(corr, 0)]
    report["binding"] = surface.binding()
    report["journal"] = gate.journal()
    report["decisions"] = gate.rows
    report["dropped_registry_members"] = DROPPED_MEMBERS
    report["unregistered_types"] = UNREGISTERED_TYPES
    report["cell_binding"] = {"adapter": cell.binding().adapter,
                              "lifecycle_offered": {
                                  "pause": cell.binding().lifecycle_offered.pause,
                                  "resume": cell.binding().lifecycle_offered.resume,
                                  "fork": cell.binding().lifecycle_offered.fork},
                              "execution_model": dict(cell.binding().execution_model)}

    # the pre-pause decision, replayed against the version it was pinned to
    before = report["run"].get("effect_decision_before_pause")
    if before and before["input_digest"] != "-":
        try:
            replayed = gate.explain(before["input_digest"], before["policy_version"])
            report["replayed_pre_pause_decision"] = {"effect": replayed.effect,
                                                     "rule_id": replayed.rule_id,
                                                     "policy_version": replayed.policy_version}
        except pi.Problem as exc:
            report["replayed_pre_pause_decision"] = render_problem(exc.body)

    print(f"\nDECISIONS  engine={engine_name} ({engine.decision_model})  "
          f"points={sorted({r['decision_point'] for r in gate.rows})}")
    table([(r["decision_point"], r["action"], r["effect"], r["rule_id"],
            r["policy_version"][:14] + "...", r["work_ran"],
            r["spend_after_micros"] - r["spend_before_micros"])
           for r in gate.rows],
          ("point", "action", "effect", "rule", "version", "work ran", "spend"))

    run = report["run"]
    print(f"\nSTEERING  disposition {run['disposition']}, {run['retries']} retry, "
          f"{run['escalations']} escalation (permitted "
          f"{unit_doc['steering']['escalation']['steps_permitted']}), "
          f"{len(run['asks'])} ask(s), effect fired: {run['effect_fired']}")
    if run["interventions"]:
        table([(i["operation"], i["served"], i.get("unit_before", "-"),
                i.get("unit_after") or "-", (i.get("problem") or {}).get("type", "-"))
               for i in run["interventions"]],
              ("intervention", "served", "unit before", "unit after", "problem"))
    if run["refusals"]:
        table([(r["where"], r["type"].rsplit(":", 1)[-1], r["status"], r["ends_unit"])
               for r in run["refusals"]], ("refused at", "type", "status", "ends the unit"))
    print(f"\n{state}: disposition {run['disposition']}, {run['cost_micros']} micros over "
          f"{len(run['attempts'])} attempt(s), task status projected from the stream {projected}. "
          f"Ledger head {ledger.inner.head()[:19]}...")

    if args.report:
        json.dump(report, open(args.report, "w"), indent=1, sort_keys=True, default=str)
    return 0 if state == "completed" else 3


if __name__ == "__main__":
    sys.exit(main())
