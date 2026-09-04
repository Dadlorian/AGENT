#!/usr/bin/env python3
"""examples/watch - how I see it from where I am, and the steps inside a unit.

One entry envelope in, one *trajectory* out: the recorded path of a unit of
agent work, rendered on the surface the caller declared, and reassembled by
grouping on the run id rather than by walking a trace parent.

Read it in this order:
  plan()          prices the unit before anything runs (pure, no adapter)
  Observation     the platform's one emission path: every span, metric, log
                  record and problem object leaves through here, redacted and
                  sampled by declarations the caller cannot narrow
  run_unit()      the steps inside the unit - admit, turn, model, tool, park,
                  resume - each handing Observation facts, never a signal
  render()        what the declared surface shows, read back from the store
  audit()         the four counters this example is graded on, read back off
                  the telemetry adapter's own query surface

Every capability behind this file is a harness adapter selected by
configuration. No product name appears here.

  python3 run.py --entry entries/human.json
  python3 run.py --entry entries/external.json          # parks, then resumes
  ADAPTER=second python3 run.py --entry entries/human.json
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
WATCH_SCHEMA = os.path.join(HERE, "schemas", "watch.schema.json")

# The published task lifecycle, adopted and not invented: an unknown state name
# is a defect here rather than a new word.
TASK_STATES = ("submitted", "working", "input-required", "completed",
               "failed", "cancelled", "rejected")

SURFACE_FOR = {"stream": "second", "poll": "dryrun"}   # a declared surface -> an adapter name


# --- typed failures: one construction point ---------------------------------
ERRORS_IFACE, _ERRORS_WIRE = harnesses.errors()
REFUSED_MEMBERS: list[str] = []        # extension members the closed registry would not carry


def problem(suffix: str, detail: str, correlation_id: str | None = None, **ext) -> dict:
    """Every refusal this example returns is built by the errors capability's one
    shared construction point, against its closed registry.

    The registry closes the extension members too, not only the type: a member it
    does not declare for that type is refused at construction, recorded here, and
    dropped - so the fact that lands in `detail` prose instead of in a member a
    machine can read is measured rather than assumed (README gap G4)."""
    try:
        return ERRORS_IFACE.construct(suffix, detail, correlation_id, **ext).body()
    except ERRORS_IFACE.UnregisteredType as exc:
        REFUSED_MEMBERS.append(str(exc))
        declared = ERRORS_IFACE.REGISTRY[suffix][3]
        kept = {k: v for k, v in ext.items() if k in declared}
        return ERRORS_IFACE.construct(suffix, detail, correlation_id, **kept).body()


def render_problem(body: dict) -> dict:
    """Re-render a harness's problem body through the same registry."""
    suffix = body["type"].rsplit(":", 1)[-1]
    if suffix not in ERRORS_IFACE.REGISTRY:
        return dict(body, registry="absent")
    ext = {k: body[k] for k in ("rule_id", "retry_after_s", "stop_reason") if k in body}
    return problem(suffix, body["detail"], body.get("correlation_id"), **ext)


def fail(body: dict) -> int:
    print("PROBLEM (application/problem+json):\n" + json.dumps(body, indent=2, sort_keys=True))
    return 2


# --- the ledger -------------------------------------------------------------
class Ledger:
    """The reference example's hash-chained ledger. Correlation rides on explicit
    attributes stamped on every record, never on trace parentage."""

    def __init__(self, path, env):
        self.inner, self.env = REF.Ledger(path), env
        self.clock = datetime.strptime(env["occurred_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    def now(self) -> str:
        self.clock += timedelta(seconds=1)
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
    priced = gi.estimate_micros(gi.route(unit_doc["attempt_class"], 10 ** 9, 10 ** 9), request)
    rows = []
    for kind in unit_doc["observation"]["step_kinds"]:
        rows.append({"step": kind, "model_class": unit_doc["attempt_class"] if kind == "model" else "-",
                     "estimate_micros": priced if kind == "model" else 0})
    return rows, sum(r["estimate_micros"] for r in rows)


# --- the platform's one emission path ---------------------------------------
class Observation:
    """Every signal this run emits leaves through here.

    The caller wrapped nothing: a step hands facts to `step()`, `log()` or
    `refusal()` and never builds a signal. Three declarations are read at the
    point each decision is taken - the operation name from the adapter's own
    published mapping, the redaction set from the unit's `redact_always` unioned
    with the caller's `redact_additional`, and the head sampling decision from
    `sampling.head_percent` - and none of them can narrow what the platform
    retains: `retain_always` names the kinds and outcomes the sampler never sees.
    """

    def __init__(self, tel, ocall, oi, store, hi, env, unit_doc, watch, ledger):
        self.tel, self.ocall, self.oi, self.store, self.hi = tel, ocall, oi, store, hi
        self.env, self.unit, self.watch, self.ledger = env, unit_doc, watch, ledger
        mapping = tel.describe_mapping()                    # read off the adapter, never transcribed
        self.mapping_version, self.operations = mapping.version, dict(mapping.operations)
        self.instruments_published = hasattr(mapping, "instruments")
        obs = unit_doc["observation"]
        self.redact = tuple(sorted(set(obs["redact_always"]) | set(watch["redact_additional"])))
        self.retain = tuple(obs["retain_always"])
        self.step_kinds = tuple(obs["step_kinds"])
        self.head_percent = watch["sampling"]["head_percent"]
        self.detail = watch["detail"]
        self.instrument = obs["instrument"]
        self.correlation = oi.CorrelationRecord(
            run_id=env["correlation"]["run_id"],
            root_dispatch_id=env["correlation"]["correlation_id"],
            depth=env["correlation"].get("depth", 0), entry_kind=env["kind"])
        self.ctx = tel.bind(self.correlation)               # the one dispatch seam
        self.steps: list[dict] = []
        self.emitted = {"span": 0, "metric": 0, "log_record": 0, "problem_object": 0}
        self.sampled_out = 0
        self.unmapped: list[str] = []
        self.events: list[str] = []

    # -- identifiers ---------------------------------------------------------
    def trace_for(self, key: str) -> str:
        """The agent boundary mints its own root trace at every step and ignores
        whatever context was injected, which is the finding this example is built
        on. In `unit` detail there is one operation, so there is one trace."""
        seed = "entry" if self.detail == "unit" else key
        return hashlib.sha256(
            f"{self.correlation.run_id}/{seed}/minted-by-the-runtime".encode()).hexdigest()[:32]

    def _operation(self, kind: str):
        name = self.operations.get(kind)
        if name is not None:
            return name, None
        self.unmapped.append(kind)
        return self.operations["dispatch"], kind

    def _redacted(self, attributes: dict) -> dict:
        return {k: ("[redacted]" if k in self.redact else v) for k, v in attributes.items()}

    def _kept(self, kind: str, outcome: str, key: str) -> bool:
        if kind in self.retain or f"outcome:{outcome}" in self.retain:
            return True
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 100 < self.head_percent

    # -- the four emission kinds --------------------------------------------
    def step(self, kind, started, ended, outcome, attributes, ctx=None, trace_key=None):
        """One step of the unit. In `steps` detail each becomes its own named
        lifecycle operation; in `unit` detail they are folded into the one
        operation that covers the whole unit of agent work."""
        if kind not in self.step_kinds:
            raise SystemExit(f"the unit declares step kinds {list(self.step_kinds)}; "
                             f"{kind!r} is not one of them and was not observed")
        self.steps.append({"kind": kind, "started": started, "ended": ended,
                           "outcome": outcome, "attributes": dict(attributes),
                           "ctx": ctx or self.ctx, "trace_key": trace_key or kind})
        self.ledger.record("step-observed", step=kind, outcome=outcome,
                           attributes=sorted(self._redacted(attributes)), cost_micros=0)

    def _emit_span(self, kind, started, ended, outcome, attributes, ctx, trace_key):
        operation, unmapped = self._operation(kind)
        attrs = self._redacted(attributes) | {"gen_ai.operation.name": operation}
        if unmapped:
            attrs["operation.unmapped_kind"] = unmapped
        trace_id = self.trace_for(trace_key)
        if not self._kept("span", outcome, f"{self.correlation.run_id}/{trace_key}"):
            self.sampled_out += 1
            return
        self.tel.emit(ctx, self.oi.TelemetryUnit(operation=operation, started_at=started,
                                                 ended_at=ended, outcome=outcome,
                                                 attributes=attrs, trace_id=trace_id))
        self.emitted["span"] += 1

    def metric(self, kind, value_ms, attributes, ctx=None):
        """Token and cost totals ride as attributes on a first-class metric, not
        only on a span, so a sampling decision cannot take the cost with it."""
        self.tel.measure(ctx or self.ctx, self.instrument, float(value_ms),
                         self._redacted(attributes) | {"step": kind})
        self.emitted["metric"] += 1

    def log(self, body, severity, trace_key, attributes=None, ctx=None):
        self.tel.log(ctx or self.ctx, self.oi.LogRecord(
            body=body, severity_text=severity, trace_id=self.trace_for(trace_key),
            attributes=self._redacted(attributes or {})))
        self.emitted["log_record"] += 1

    def refusal(self, body: dict, trace_key: str, ends_unit: bool, ctx=None):
        """A failure is a signal like any other: bound to the same trace identity
        as the step that raised it, at the moment it is produced."""
        row = self.oi.REGISTRY.get(body["type"].rsplit(":", 1)[-1])
        self.tel.emit_problem(ctx or self.ctx, self.oi.Problem(
            type=body["type"], title=body["title"], status=body["status"],
            detail=body["detail"], retryable=body["retryable"],
            correlation_id=self.correlation.root_dispatch_id, trace_id=self.trace_for(trace_key)))
        self.emitted["problem_object"] += 1
        self.ledger.record("refusal", step=trace_key, problem_type=body["type"],
                           status=body["status"], ends_unit=ends_unit,
                           rule_id=body.get("rule_id", "-"),
                           in_telemetry_registry=row is not None, cost_micros=0)

    def event(self, type_, at, data, emitted_by_surface: bool = False):
        """One typed event on the run's stream. The vocabulary is the capability's
        (`EVENT_TYPES`); a name it does not carry is a gap, never a mint.

        Two of the eight types are put on the store by the surface itself, when a
        person is asked and when a person decides. They pass through the same gate
        with `emitted_by_surface=True` so the vocabulary check covers the whole
        stream rather than the six names this runner happens to emit, and the
        store still holds exactly one of each. `self.events` is therefore the list
        of names that passed the gate, and `test.sh` asserts it against the store,
        so the guarantee this file states about itself is the one it enforces."""
        if type_ not in self.hi.EVENT_TYPES:
            raise SystemExit(f"{type_!r} is not one of the published event types {self.hi.EVENT_TYPES}")
        if not emitted_by_surface:
            self.store.emit_event(type_, self.correlation.root_dispatch_id, at, data)
        self.events.append(type_)

    def child(self, depth: int, mint_own: bool):
        """A second dispatch on the same run - a resume after a person decided.
        The platform re-stamps the run id at the child boundary; `mint_own` is the
        deliberate breakage in which it does not."""
        if mint_own:
            record = self.oi.CorrelationRecord(run_id=f"minted-{self.correlation.run_id}",
                                               root_dispatch_id=f"minted-{depth}",
                                               depth=depth, entry_kind=self.correlation.entry_kind)
        else:
            record = self.oi.CorrelationRecord(
                run_id=self.correlation.run_id, root_dispatch_id=self.correlation.root_dispatch_id,
                parent_dispatch_id=self.correlation.root_dispatch_id, depth=depth,
                entry_kind=self.correlation.entry_kind)
        return self.tel.bind(record)

    def close(self):
        """Emit the spans. One operation for the whole unit, or one per step."""
        if not self.steps:
            return
        if self.detail == "unit":
            folded = {}
            for s in self.steps:
                for k, v in s["attributes"].items():
                    folded[f"{s['kind']}.{k}" if s["kind"] != "entry" else k] = v
            first, last = self.steps[0], self.steps[-1]
            outcome = "error" if any(s["outcome"] == "error" for s in self.steps) else last["outcome"]
            self._emit_span("entry", first["started"], last["ended"], outcome, folded, self.ctx, "entry")
        else:
            for s in self.steps:
                self._emit_span(s["kind"], s["started"], s["ended"], s["outcome"],
                                s["attributes"], s["ctx"], s["trace_key"])


# --- the steps inside the unit ----------------------------------------------
def run_unit(obs, env, unit_doc, ledger, args, ci, cell, callmod, gi, gw, ti, tool):
    """Admit a cell, take one turn, call a model and a tool through the host, and
    (when the caller declared it) park on a person and resume. Each step hands
    Observation its facts; nothing here formats a signal or names a backend."""
    corr = env["correlation"]
    entry_started = ledger.now()
    subject = env["payload"]["subject"]
    obs.event("run.started", ledger.now(),
              {"unit": unit_doc["unit"], "entry_kind": env["kind"], "actor": env["actor"]["subject"]})
    obs.log(f"unit {unit_doc['unit']} started from the {env['kind']} door", "INFO", "entry",
            {"task_summary": subject})

    # -- dispatch: one contained turn, both ceilings enforced outside it -----
    decl = ci.IsolationDeclaration.from_dict(unit_doc["isolation"])
    unit_ctx = ci.UnitContext(correlation_id=corr["correlation_id"], run_id=corr["run_id"],
                              actor=env["actor"]["subject"], idempotency_key=env["idempotency_key"],
                              ceiling_s=unit_doc["ceilings"]["wall_seconds"])
    handle = cell.admit(decl, unit_ctx)
    # the whole declaration lands on the receipt, allowlist included: a caller who
    # widens egress must be able to read back what was admitted, and a field the
    # record never carries is a field a change to which nothing can detect
    ledger.record("cell-admitted", step="dispatch", unit_id=handle.unit_id, profile=handle.profile,
                  egress=decl.egress, egress_allowlist=list(decl.egress_allowlist),
                  credentials=decl.credentials, wall_ceiling_s=unit_ctx.ceiling_s, cost_micros=0)
    session = cell.open_session(handle, ci.SessionCapabilities(streaming=True, permission_callbacks=True,
                                                              cancellation=True))
    prompt = f"{unit_doc['task']}\n\ninput: {subject}"
    request = ci.TurnRequest(prompt, unit_doc["ceilings"]["turn_op_seconds"],
                             unit_doc["ceilings"]["cancel_grace_s"])
    # the cancel window the boundary accepted, and the floor the running adapter
    # publishes that it was accepted against. Same reasoning as the allowlist on
    # the receipt above: a cancel window no record carries is a window nobody can
    # audit after the fact, and a declared value nothing writes down is a value a
    # change to which nothing can detect. The floor is the host's, not the
    # caller's - a caller who declares less than it is refused at `prompt()`.
    cancel_floor_s = cell.binding().cancel_floor_s
    t0 = time.monotonic()
    dispatch = callmod.Dispatch(cell, handle, session, request).start()
    if args.cancel:
        time.sleep(unit_doc["ceilings"]["turn_op_seconds"] / 2)
        dispatch.cancel()                       # the reader may cancel; the boundary enforces the grace
    result, _unit_result = dispatch.finish()
    turn_ms = round((time.monotonic() - t0) * 1000, 3)
    report = cell.inspect_containment(handle)
    for seq in range(1, result.frames + 1):     # the frames the boundary saw, as typed events
        obs.event("step.progress", ledger.now(),
                  {"frame": seq, "of": result.frames, "streaming": session.negotiated.streaming})
    obs.step("dispatch", entry_started, ledger.now(),
             "ok" if result.stop_reason == "end_turn" else "error",
             {"prompt": prompt, "stop_reason": result.stop_reason, "frames": result.frames,
              "frames_after_terminal": result.frames_after_terminal,
              "cancellation_negotiated": session.negotiated.cancellation,
              "cancel_grace_s": request.grace_s, "cancel_floor_s": cancel_floor_s,
              "jail_mode": report.jail_mode, "observed_from": report.observed_from})
    obs.metric("dispatch", turn_ms, {"cost_micros": 0, "tokens_in": 0, "tokens_out": 0})
    obs.log(f"turn closed with stop reason {result.stop_reason}, held open by a "
            f"{request.grace_s}s cancel window over the adapter's {cancel_floor_s}s floor",
            "INFO" if result.stop_reason == "end_turn" else "WARN", "dispatch",
            {"frames": result.frames})

    # -- model: one completion by class, through the broker ------------------
    m0 = time.monotonic()
    ask = gi.CompletionRequest.from_dict(
        {"model_class": unit_doc["attempt_class"], "messages": [{"role": "user", "content": prompt}],
         "idempotency_key": f"{env['idempotency_key']}#model",
         "ceiling_micros": env["budget"]["ceiling_micros"]})
    ticket = gw.submit(ask)
    while ticket.state == "pending":
        ticket = gw.claim(ticket)
    completion = ticket.result
    obs.step("model", ledger.now(), ledger.now(), "ok",
             {"completion": completion.text, "gen_ai.request.model_class": unit_doc["attempt_class"],
              "gen_ai.usage.input_tokens": completion.tokens_in,
              "gen_ai.usage.output_tokens": completion.tokens_out,
              "cost_micros": completion.cost_micros, "cost_status": completion.cost_status})
    obs.metric("model", round((time.monotonic() - m0) * 1000, 3),
               {"cost_micros": completion.cost_micros, "tokens_in": completion.tokens_in,
                "tokens_out": completion.tokens_out})

    # -- tool: the declared surface, and one refusal folded into the record --
    tools_doc = unit_doc["tools"]
    def stamp(part):
        return ti.CallContext(correlation_id=corr["correlation_id"], run_id=corr["run_id"],
                              actor=env["actor"]["subject"],
                              idempotency_key=f"{env['idempotency_key']}#{part}",
                              protocol_revision=tools_doc["revision"],
                              ceiling_calls=tools_doc["ceiling_calls"],
                              policy_verdict=tools_doc["policy_verdict"])
    binding = tool.bind_server(tools_doc["server_ref"], tools_doc["declared_surface"], stamp("bind"))
    catalogue = tool.list_tools(binding)
    t1 = time.monotonic()
    refused, attempted = [], 0
    for role in ("read", "refused"):
        spec = tools_doc[role]
        obs.event("tool.proposed", ledger.now(), {"tool": spec["name"], "role": role})
        attempted += 1
        try:
            tool.call_tool(binding, spec["name"], spec["args"], stamp(role))
        except ti.Problem as exc:
            body = render_problem(exc.body)
            refused.append(body.get("rule_id", "-"))
            obs.refusal(body, "tool", ends_unit=False)
    obs.step("tool", ledger.now(), ledger.now(), "ok",
             {"gen_ai.tool.name": tools_doc["read"]["name"], "published": len(catalogue),
              # the capability derives the binding handle from the server reference it
              # was given, so the handle on the wire is what makes `tools.server_ref`
              # a read value rather than a carried one
              "tool_binding": binding.handle, "server_marker": binding.server_marker,
              "declared_surface": len(tools_doc["declared_surface"]), "refused": len(refused),
              # a ceiling that only shows up when it is crossed is a ceiling nobody
              # can audit on a run that stayed inside it: the permitted count and the
              # attempted count go on the step, so two legal ceilings are two records
              "calls_permitted": tools_doc["ceiling_calls"], "calls_attempted": attempted,
              "refused_rules": ",".join(refused)})
    obs.metric("tool", round((time.monotonic() - t1) * 1000, 3),
               {"cost_micros": 0, "tokens_in": 0, "tokens_out": 0})

    # -- park on a person, then resume as a second dispatch ------------------
    decision_row = None
    if obs.watch["pause_for_decision"]:
        decision_row = park_and_resume(obs, env, unit_doc, ledger, args)

    outcome = {"end_turn": "completed", "cancelled": "cancelled"}.get(result.stop_reason, "failed")
    obs.step("entry", entry_started, ledger.now(), "ok" if outcome == "completed" else "error",
             {"entry.kind": env["kind"], "actor": env["actor"]["subject"], "task_summary": subject,
              "outcome": outcome})
    obs.event("run.finished", ledger.now(), {"outcome": outcome, "stop_reason": result.stop_reason})
    return {"outcome": outcome, "stop_reason": result.stop_reason, "frames": result.frames,
            "tokens_in": completion.tokens_in, "tokens_out": completion.tokens_out,
            "cost_micros": completion.cost_micros, "refused_rules": refused,
            "published": len(catalogue), "decision": decision_row,
            "containment_marker": report.containment_marker}


def park_and_resume(obs, env, unit_doc, ledger, args):
    """input-required, then working again. The resume is a second dispatch with
    its own trace id on the same run id, which is the whole reason correlation
    cannot ride on trace parentage: by the time a person decides there is no
    live trace left to be a parent."""
    hi, spec = obs.hi, unit_doc["ask"]
    corr = env["correlation"]["correlation_id"]
    parked_at = ledger.now()
    deadline = (datetime.strptime(parked_at, "%Y-%m-%dT%H:%M:%SZ")
                + timedelta(seconds=spec["deadline_seconds"])).isoformat() + "Z"
    ask = hi.HumanAsk(ask_id=f"ask-{env['entry_id']}", correlation_id=corr, prompt=spec["prompt"],
                      response_schema=spec["response_schema"], proposed=spec["proposed"],
                      deadline_at=deadline, allowed_decisions=tuple(spec["allowed_decisions"]))
    obs.surface.ask(ask, env, parked_at)        # the store holds it; the surface only renders it
    obs.event("human.ask", parked_at, {"ask_id": ask.ask_id}, emitted_by_surface=True)
    ledger.record("approval-parked", step="ask", state="input-required", ask_id=ask.ask_id,
                  deadline_at=deadline, cost_micros=0)

    decided_at = ledger.now()
    decision = hi.HumanDecision(ask_id=ask.ask_id, correlation_id=corr, decision="approve",
                                actor="user:corey", idempotency_key=f"{env['idempotency_key']}#decide",
                                body={"component": "pricing/coupon.py"})
    ack = obs.surface.decide(decision, decided_at)
    obs.event("human.decided", decided_at, {"ask_id": ask.ask_id}, emitted_by_surface=True)
    child_ctx = obs.child(obs.correlation.depth + 1, args.mint_on_resume)
    obs.step("dispatch", decided_at, ledger.now(), "ok",
             {"resume": True, "decision": ack.decision, "decided_by": ack.decided_by,
              "resumed_on": ack.correlation_id}, ctx=child_ctx, trace_key="dispatch-resume")
    obs.log("run resumed on the correlation id it was parked with", "INFO", "dispatch-resume",
            {"ask_id": ask.ask_id}, ctx=child_ctx)
    ledger.record("approval-returned", step="ask", state="working", ask_id=ask.ask_id,
                  decision=ack.decision, applied=ack.applied,
                  resumed_on_same_correlation=ack.correlation_id == corr, cost_micros=0)

    # a second, different decision on a closed ask: refused, and the refusal is
    # an event on the same stream rather than a line in a log nobody reads
    second = hi.HumanDecision(ask_id=ask.ask_id, correlation_id=corr, decision="reject",
                              actor="user:corey", idempotency_key=f"{env['idempotency_key']}#again",
                              body={"component": "checkout/api.py"})
    try:
        obs.surface.decide(second, ledger.now())
        conflict = None
    except hi.Problem as exc:
        conflict = render_problem(exc.body)
        obs.refusal(conflict, "dispatch-resume", ends_unit=False, ctx=child_ctx)
        obs.event("human.refused", ledger.now(),
                  {"ask_id": ask.ask_id, "problem_type": conflict["type"]})
    return {"decision": ack.decision, "applied": ack.applied, "artifact": ack.artifact,
            "resumed_on_same_correlation": ack.correlation_id == corr,
            "second_decision_refused": None if conflict is None else conflict["type"]}


# --- what the caller sees ----------------------------------------------------
def task_status(events) -> str:
    """A pure projection of the typed event stream onto the published task
    lifecycle. There is no status-change event in the published vocabulary, so
    the state is derived rather than subscribed to - README gap G2."""
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


def render(surface, hi, correlation_id, since):
    """What the declared surface shows of the run. A surface that cannot answer
    from a position refuses with a type rather than silently replaying the whole
    stream, so `since` is read here, at the point of decision."""
    try:
        return surface.watch(correlation_id, since), None
    except hi.Problem as exc:
        return [], render_problem(exc.body)


def audit(obs, ocall, oi):
    """Read every signal back off the adapter's own query surface and group on
    the run id. Nothing here reads a trace id or a parent."""
    got = obs.tel.fetch_run(obs.correlation.run_id)
    if isinstance(got, oi.Problem):
        return {"error": got.as_dict()}
    spans = ocall.reassemble(obs.tel, obs.correlation.run_id,
                             {"spans_emitted": obs.emitted["span"]})
    per_kind = {}
    for kind in ("span", "metric", "log_record", "problem_object"):
        sigs = [s for s in got if s.kind == kind]
        per_kind[kind] = {
            "read_back": len(sigs),
            "missing_run_id": sum(1 for s in sigs if s.resource.get(oi.RUN_ID_KEY) != obs.correlation.run_id),
            "missing_correlation_id": sum(1 for s in sigs if not s.resource.get(oi.ROOT_DISPATCH_ID_KEY)),
        }
    span_traces = {s.unit.get("trace_id") for s in got if s.kind == "span"}
    orphan_problems = sum(1 for s in got if s.kind == "problem_object"
                          and s.unit.get("trace_id") not in span_traces)
    cost_total = sum(s.unit.get("attributes", {}).get("cost_micros", 0)
                     for s in got if s.kind == "metric")
    return {"signals_read_back": len(got),
            "signals": [{"kind": s.kind, "resource": s.resource, "unit": s.unit} for s in got],
            "per_kind": per_kind,
            "signal_groups": len({s.resource.get(oi.RUN_ID_KEY) for s in got}),
            "run_id_groups": spans["run_id_groups"], "levels_covered": spans["levels_covered"],
            "distinct_trace_ids": spans["distinct_trace_ids"],
            "spans_missing_run_id": spans["spans_missing_run_id"],
            "spans_missing_correlation_id": spans["spans_missing_root_dispatch_id"],
            "mapping_version_on_the_wire": spans["mapping_version"],
            "problem_objects_without_a_span_trace": orphan_problems,
            "metric_cost_micros_total": cost_total}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))


# --- wiring ------------------------------------------------------------------
def parse(argv):
    ap = argparse.ArgumentParser(description="Run one unit and watch it from the declared surface.")
    ap.add_argument("--entry", help="path to an entry envelope")
    ap.add_argument("--unit", help="override the unit the envelope's intent.workflow_ref names")
    ap.add_argument("--ledger", default=os.path.join(OUT, "run.jsonl"))
    ap.add_argument("--report", help="write the run report as JSON here")
    ap.add_argument("--surface", choices=["stream", "poll"], help="override payload.watch.surface")
    ap.add_argument("--detail", choices=["unit", "steps"], help="override payload.watch.detail")
    ap.add_argument("--since", type=int, help="override payload.watch.since")
    ap.add_argument("--head-percent", type=int, help="override payload.watch.sampling.head_percent")
    ap.add_argument("--redact-additional", help="override payload.watch.redact_additional (comma separated)")
    ap.add_argument("--pause", dest="pause", action="store_const", const=True, default=None)
    ap.add_argument("--no-pause", dest="pause", action="store_const", const=False)
    ap.add_argument("--cancel", action="store_true", help="cancel the turn mid-flight")
    ap.add_argument("--budget-micros", type=int, help="override the envelope ceiling")
    ap.add_argument("--mint-on-resume", action="store_true",
                    help="deliberate breakage: the resume mints its own run id instead of re-stamping")
    ap.add_argument("--verify-ledger", action="store_true")
    return ap.parse_args(argv)


def overrides(watch, args):
    applied = []
    for flag, path in (("surface", ("surface",)), ("detail", ("detail",)), ("since", ("since",)),
                       ("head_percent", ("sampling", "head_percent")), ("pause", ("pause_for_decision",))):
        value = getattr(args, flag)
        if value is not None:
            node = watch
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
            applied.append(f"{'.'.join(path)}={value}")
    if args.redact_additional is not None:
        watch["redact_additional"] = [k for k in args.redact_additional.split(",") if k]
        applied.append(f"redact_additional={watch['redact_additional']}")
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
    watch_errs = REF.validate(env.get("payload", {}).get("watch"), json.load(open(WATCH_SCHEMA)))
    if watch_errs:
        return fail(problem("document-invalid", "payload.watch: " + "; ".join(watch_errs[:4]),
                            env["correlation"]["correlation_id"], causes=watch_errs[:4]))
    # the task specification is the one the envelope points at; --unit overrides it
    unit_path = args.unit or os.path.join(HERE, env["intent"]["workflow_ref"])
    unit_doc = json.load(open(unit_path))
    watch = env["payload"]["watch"]
    applied = overrides(watch, args)
    if args.budget_micros is not None:
        env["budget"]["ceiling_micros"] = args.budget_micros

    os.makedirs(OUT, exist_ok=True)
    ledger = Ledger(args.ledger, env)
    oi, OAdapter, ocall = harnesses.observability(os.environ.get("ADAPTER", "dryrun"))
    hi, hstore, HAdapter = harnesses.human(SURFACE_FOR[watch["surface"]])
    ci, CAdapter, callmod = harnesses.containment("dryrun")
    gi, GAdapter = harnesses.gateway("dryrun")
    ti, TAdapter = harnesses.tool_access("dryrun")

    # The parked state is durable and belongs to the platform, not to a surface;
    # it is keyed by the ledger this run writes to, so two differential runs of
    # one envelope are two runs and not one ask parked twice.
    store = hstore.ParkedAskStore(os.path.join(
        OUT, "asks", os.path.splitext(os.path.basename(args.ledger))[0],
        env["correlation"]["correlation_id"]))
    obs = Observation(OAdapter(), ocall, oi, store, hi, env, unit_doc, watch, ledger)
    obs.surface = HAdapter(store)

    steps, floor = plan(unit_doc, env, gi)
    ceiling = env["budget"]["ceiling_micros"]
    print(f"INTENT  {env['intent']['summary']}")
    print(f"PLAN  {unit_doc['unit']}: {len(steps)} steps, shortest finishing path {floor} micros, "
          f"ceiling {ceiling}. Watching from '{watch['surface']}' at detail '{watch['detail']}', "
          f"head sampling {watch['sampling']['head_percent']}%"
          + (f", overrides {applied}" if applied else ""))
    table([(s["step"], s["model_class"], s["estimate_micros"]) for s in steps],
          ("step", "model_class", "est_micros"))
    ledger.record("unit-submitted", step="-", state="submitted", plan_floor_micros=floor,
                  ceiling_micros=ceiling, surface=watch["surface"], detail=watch["detail"],
                  head_percent=watch["sampling"]["head_percent"], workflow_ref=env["intent"]["workflow_ref"],
                  unit=unit_doc["unit"], summary=env["intent"]["summary"],
                  attempt_class=unit_doc["attempt_class"], cost_micros=0)

    def reject(body: dict, stop_reason: str) -> int:
        """One rejection path for every refusal that ends the unit, whoever raised
        it: the errors capability builds the body, the run gets its span because
        `retain_always` names outcome:error, the stream gets its terminal event and
        the ledger gets its row. Used by the ceiling check below and by any typed
        problem a capability raises out of the unit."""
        refused_at = ledger.now()
        obs.refusal(body, "entry", ends_unit=True)
        obs.event("run.finished", ledger.now(), {"outcome": "rejected", "stop_reason": stop_reason})
        obs.step("entry", refused_at, ledger.now(), "error",
                 {"entry.kind": env["kind"], "actor": env["actor"]["subject"],
                  "task_summary": env["payload"]["subject"], "outcome": "rejected"})
        obs.close()
        ledger.record("unit-rejected", step="-", state="rejected", problem_type=body["type"], cost_micros=0)
        if args.report:
            json.dump({"entry": env["kind"], "run_id": env["correlation"]["run_id"],
                       "status": "rejected", "watch": watch, "overrides": applied,
                       "events_on_the_stream": [e.type for e in store.events(
                           env["correlation"]["correlation_id"])],
                       "events_through_the_gate": obs.events,
                       "emitted": obs.emitted, "problem": body,
                       "registry_refused_members": REFUSED_MEMBERS,
                       "audit": audit(obs, ocall, oi)}, open(args.report, "w"), indent=1, sort_keys=True)
        return fail(body)

    if floor > ceiling:
        return reject(problem("budget-exhausted",
                              f"the shortest finishing path costs {floor} micros and the ceiling is "
                              f"{ceiling}; refused before any cell was admitted",
                              env["correlation"]["correlation_id"], stop_reason="budget_exhausted",
                              # what the concern asks a failure to carry - which ceiling, and by
                              # how much - offered as members and refused by the closed registry
                              ceiling_micros=ceiling, exceeded_by_micros=floor - ceiling),
                      "budget_exhausted")

    try:
        outcome = run_unit(obs, env, unit_doc, ledger, args, ci, CAdapter(json.load(
            open(os.path.join(harnesses.ROOT, "harness", "containment", "binding.json")))),
            callmod, gi, GAdapter(), ti, TAdapter())
    except ci.Problem as exc:
        # a containment declaration the host refuses - an egress allowlist that
        # declares nothing, a cancel grace below the adapter's own floor - comes
        # back as the same typed object as every other refusal, not as a traceback
        return reject(render_problem(exc.body), "containment_refused")
    obs.close()

    events, watch_problem = render(obs.surface, hi, env["correlation"]["correlation_id"], watch["since"])
    all_events = store.events(env["correlation"]["correlation_id"])
    status = task_status(all_events)
    report = audit(obs, ocall, oi)
    ledger.record("unit-" + status, step="-", state=status, spans=obs.emitted["span"],
                  sampled_out=obs.sampled_out, cost_micros=outcome["cost_micros"])

    binding = obs.surface.binding()
    print(f"\nTRAJECTORY  surface={watch['surface']} ({binding['delivery_model']}, "
          f"replayable={binding['replayable_from_position']})  since={watch['since']}  "
          f"rendered {len(events)} of {len(all_events)} events on the run's stream  "
          f"task status {status}, projected from the stream")
    if watch_problem:
        print("OBSERVATION REFUSED (application/problem+json):\n"
              + json.dumps(watch_problem, indent=2, sort_keys=True))
    table([(e.seq, e.type, e.at, json.dumps(e.data, sort_keys=True)[:58]) for e in events]
          or [("-", "-", "-", "nothing this surface renders")], ("seq", "event", "at", "data"))

    print(f"\nSIGNALS  adapter={obs.tel.name}  mapping={report['mapping_version_on_the_wire']}  "
          f"operations={sorted(set(obs.operations.values()))}  unmapped={obs.unmapped}")
    table([(k, v["read_back"], v["missing_run_id"], v["missing_correlation_id"])
           for k, v in report["per_kind"].items()],
          ("kind", "read back", "missing run.id", "missing correlation.id"))
    print(f"\ndistinct trace ids: {report['distinct_trace_ids']}   groups on run.id: "
          f"{report['run_id_groups']}   levels: {report['levels_covered']}   "
          f"spans sampled out: {obs.sampled_out}   "
          f"problem objects off any span's trace: {report['problem_objects_without_a_span_trace']}   "
          f"cost on metrics: {report['metric_cost_micros_total']} micros")
    print(f"\n{status}: stop reason {outcome['stop_reason']}, {outcome['frames']} frames, "
          f"{outcome['tokens_in']}+{outcome['tokens_out']} tokens, {outcome['cost_micros']} micros, "
          f"refused tool calls {outcome['refused_rules']}. Ledger head {ledger.inner.head()[:19]}...")

    if args.report:
        json.dump({"entry": env["kind"], "run_id": env["correlation"]["run_id"], "status": status,
                   "watch": watch, "overrides": applied, "binding": binding,
                   "events_rendered": [e.type for e in events],
                   "events_on_the_stream": [e.type for e in all_events],
                   "events_through_the_gate": obs.events,
                   "watch_problem": watch_problem, "emitted": obs.emitted,
                   "sampled_out": obs.sampled_out, "unmapped_operations": obs.unmapped,
                   "instruments_published_by_the_mapping": obs.instruments_published,
                   "redact_set": list(obs.redact), "registry_refused_members": REFUSED_MEMBERS,
                   "outcome": outcome, "audit": report},
                  open(args.report, "w"), indent=1, sort_keys=True)
    return 0 if status == "completed" else 3


if __name__ == "__main__":
    sys.exit(main())
