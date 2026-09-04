#!/usr/bin/env python3
"""examples/run — what happens in the sandbox on my behalf; fifty of them at once.

One entry envelope in, one unit out: contract rendered and hashed before the
cell starts, a contained cell admitted from a resource declaration, one agent
turn per attempt with both ceilings enforced outside it, every model call, tool
call and skill load leaving through the host broker, one candidate sealed
write-once into the output role, and the deciding checks run afterwards in a
cell forked from the seeded snapshot with the output mounted read-only.

Read it in this order: `plan()` is the pure function that prices the unit
before anything executes; `attempt()` is one execution of one attempt;
`unit()` is the bounded cascade around it; `fleet()` is fifty of them at once.

Every capability behind this file is a harness adapter selected by
configuration. No product name appears here.

  python3 run.py --entry entries/human.json
  python3 run.py --entry entries/schedule.json        # payload.fleet_size: 50
  ADAPTER=second python3 run.py --entry entries/human.json
  python3 run.py --verify-ledger

Python 3.11 standard library only. No network.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import threading
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import assessor                       # noqa: E402  the deciding checks: host-side, never mounted
import contract as contract_role      # noqa: E402
import driver                         # noqa: E402
import harnesses                      # noqa: E402

OUT = os.path.join(HERE, "out")
REF = harnesses.reference()           # the reference example's validator and hash-chained ledger
ENTRY_SCHEMA = os.path.join(HERE, "..", "end-to-end", "schemas", "entry.schema.json")


def ladder(gi):
    """The class ladder: the routing table's classes ordered by their recorded
    unit price, read at call time from the same table the gateway routes on
    (`gi.ROUTING_TABLE`, loaded from harness/gateway/routing.json). No prefix is
    written down here, so adding or repricing a class moves the ladder and
    nothing in this file changes. Proposed: price order is this example's
    reading of "escalate exactly one class"."""
    return tuple(sorted(gi.ROUTING_TABLE, key=lambda p: gi.ROUTING_TABLE[p]["unit_micros_per_1k"]))


# --- typed failures: one construction point --------------------------------
ERRORS_IFACE, _ERRORS_WIRE = harnesses.errors()   # the registry gate, and the module that renders it
UNREGISTERED = []          # suffixes a harness raised that the closed registry does not carry


def problem(suffix, detail, correlation_id=None, **ext):
    """Every refusal this example returns is built here, by the errors
    capability's one shared construction point, against its closed registry."""
    return ERRORS_IFACE.construct(suffix, detail, correlation_id, **ext)


def render_problem(body: dict) -> dict:
    """Re-render a harness's problem body through the same registry. A suffix
    the closed registry does not carry is recorded rather than smoothed over."""
    suffix = body["type"].rsplit(":", 1)[-1]
    if suffix not in ERRORS_IFACE.REGISTRY:
        if suffix not in UNREGISTERED:
            UNREGISTERED.append(suffix)
        return dict(body, registry="absent")
    return problem(suffix, body["detail"], body.get("correlation_id")).body()


def fail(body: dict) -> int:
    print("PROBLEM (application/problem+json):\n" + json.dumps(body, indent=2, sort_keys=True))
    return 2


# --- the ledger: one record per thing that happened -------------------------
class RunLedger:
    """The reference example's hash-chained ledger, with one lock so fifty
    concurrent units append to one chain. Correlation rides on explicit
    attributes stamped on every record, never on trace parentage."""

    def __init__(self, path):
        self.inner = REF.Ledger(path)
        self.lock = threading.Lock()

    def record(self, env, kind, **fields):
        clock = env["_clock"]
        env["_clock"] = clock + timedelta(seconds=1)
        row = {"ts": clock.isoformat().replace("+00:00", "Z"), "kind": kind,
               "run_id": env["correlation"]["run_id"],
               "correlation_id": env["correlation"]["correlation_id"],
               "actor": env["actor"]["subject"],
               "delegation_depth": len(env["actor"]["delegation_chain"]),
               "entry_kind": env["kind"], "idempotency_key": env["idempotency_key"], **fields}
        with self.lock:
            return self.inner.append(**row)

    def head(self):
        with self.lock:
            return self.inner.head()


# --- the plan: pure, complete before anything executes ----------------------
def plan(unit_doc, envelope, gi, prompt_text):
    """(unit, envelope) -> priced steps. No side effects, no clock, no adapter.

    Prices the worst case (every attempt, and one class step) and the shortest
    finishing path (one attempt at the declared class), so the ceiling can be
    checked against a floor before a cell is ever admitted.
    """
    def one(model_class):
        request = gi.CompletionRequest.from_dict(
            {"model_class": model_class, "messages": [{"role": "user", "content": prompt_text}],
             "idempotency_key": "plan-estimate-only", "ceiling_micros": 10 ** 9})
        return gi.estimate_micros(gi.route(model_class, 10 ** 9, 10 ** 9), request)

    attempts = unit_doc["ceilings"]["attempts"]
    at_class, stepped = one(unit_doc["attempt_class"]), one(unit_doc["escalation_class"])
    steps = [{"step": f"attempt-{n}", "op": "agent-turn", "model_class": unit_doc["attempt_class"],
              "estimate_micros": at_class} for n in range(1, attempts + 1)]
    steps += [{"step": f"measure-{n}", "op": "judge", "model_class": "-", "estimate_micros": 0}
              for n in range(1, attempts + 1)]
    steps.append({"step": "class-step", "op": "agent-turn",
                  "model_class": unit_doc["escalation_class"], "estimate_micros": stepped})
    worst = sum(s["estimate_micros"] for s in steps)
    return steps, worst, at_class


# --- one execution of one attempt -------------------------------------------
def attempt(ctx, n, model_class, folded):
    """One attempt: seed, admit, one turn, brokered capability calls, one sealed
    candidate, then measure outside the cell. Returns the attempt-ledger row."""
    env, unit_doc, led = ctx["env"], ctx["unit"], ctx["ledger"]
    ci, ad, callmod = ctx["ci"], ctx["cell"], ctx["callmod"]
    unit_out = ctx["unit_out"]

    # 2. render the contract, hash it, ledger the digest -- before the cell starts
    manifest = contract_role.render(unit_doc, env, n, folded, unit_out)
    led.record(env, "contract-sealed", unit=unit_doc["unit"], attempt=n,
               contract_digest=manifest["contract_digest"],
               stable_prefix_digest=manifest["stable_prefix_digest"],
               resident_tokens=manifest["resident_tokens"],
               entries=len(manifest["entries"]), cost_micros=0)

    # 4. admit the cell from a resource declaration; nothing here names a machine
    decl = ci.IsolationDeclaration.from_dict(unit_doc["isolation"])
    unit_ctx = ci.UnitContext(correlation_id=env["correlation"]["correlation_id"],
                              run_id=env["correlation"]["run_id"], actor=env["actor"]["subject"],
                              idempotency_key=f"{env['idempotency_key']}#a{n}",
                              ceiling_s=unit_doc["ceilings"]["wall_seconds"])
    handle = ad.admit(decl, unit_ctx)
    led.record(env, "cell-admitted", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               profile=handle.profile, egress=decl.egress, credentials=decl.credentials,
               contract_digest=manifest["contract_digest"], cost_micros=0)

    # the seeded snapshot the measure cell is forked from, taken before the turn
    seed, seed_gap = None, None
    try:
        seed = ad.pause(handle)
    except ci.Problem as exc:
        seed_gap = render_problem(exc.body)

    session = ad.open_session(handle, ci.SessionCapabilities(streaming=True, permission_callbacks=True,
                                                             cancellation=True))
    request = ci.TurnRequest(driver.prompt(manifest, unit_doc["task"]),
                             unit_doc["ceilings"]["turn_op_seconds"],
                             unit_doc["ceilings"]["cancel_grace_s"])
    turn = callmod.Dispatch(ad, handle, session, request).start()      # both ceilings live out here
    led.record(env, "turn-started", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               streaming=session.negotiated.streaming,
               cancellation=session.negotiated.cancellation,
               runtime_marker=session.runtime_marker, cost_micros=0)

    # 5. what the unit reaches for, each time it reaches: brokered, never direct
    capabilities = brokered_calls(ctx, env, unit_doc, manifest, n, handle, model_class)

    # 6. one candidate, sealed write-once into the output role
    sealed_dir = os.path.join(unit_out, "output", f"attempt-{n}")
    candidate = driver.produce(manifest, folded, ctx["stuck"], capabilities["completion_text"], sealed_dir)
    candidate_digest = contract_role.digest(open(candidate["path"], "rb").read())
    led.record(env, "output-sealed", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               entry="coupon.py", output_digest=candidate_digest, bytes=candidate["bytes"],
               durable_at_head=led.head(), cost_micros=0)

    visible = driver.run_visible(candidate["path"])
    led.record(env, "visible-checks", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               outcomes=[{"check_id": c, "outcome": o} for c, o in visible], decides=False,
               cost_micros=0)

    if ctx["widen"]:                       # deliberate breakage: widen the seed after it was ledgered
        os.chmod(os.path.join(manifest["mount"], "policy.json"), 0o600)
        with open(os.path.join(manifest["mount"], "policy.json"), "a") as fh:
            fh.write('\n{"widened": "after the digest was ledgered"}\n')

    result, unit_result = turn.finish()                # terminate is inside finish; the cell is now terminal
    report_c = ad.inspect_containment(handle)          # asserted by the host, never by the unit
    led.record(env, "cell-terminated", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               stop_reason=result.stop_reason, terminated_by=result.terminated_by or "-",
               frames=result.frames, frames_after_terminal=result.frames_after_terminal,
               jail_mode=report_c.jail_mode, owner_in_host_passwd=report_c.owner_in_host_passwd,
               egress_made=report_c.egress_attempts_made, egress_blocked=report_c.egress_attempts_blocked,
               secrets_seen_inside=report_c.secrets_seen_inside,
               containment_marker=report_c.containment_marker, observed_from=report_c.observed_from,
               cost_micros=0)

    # 7. measure, in a cell forked from the seeded snapshot, output read-only.
    # Measured: the measure cell is admitted from the seed and terminated after.
    # Claimed, and labelled as such on the record below: the check bodies run
    # host-side. The isolation interface serves admit, terminate, snapshot and
    # one prompt turn; it publishes no operation that runs a host-supplied check
    # inside a cell, so `checks_ran` says where they ran rather than implying it
    # (README gap 10).
    measure_cell, measure_kind = None, "forked-from-seeded-snapshot"
    if seed is not None:
        measure_cell = ad.resume(seed)
    else:
        measure_kind = "fresh-admission (this isolation class serves no snapshot)"
        measure_cell = ad.admit(decl, unit_ctx)
    report = assessor.measure(unit_doc["deciding_criteria_ref"], {
        "candidate": candidate["path"], "tag": f"{env['correlation']['run_id']}-{n}",
        "source_tests": os.path.join(HERE, "source", "tests"),
        "source_tests_digest_before": ctx["source_tests_digest"],
        "contract_digest_read_back": contract_role.read_back(manifest),
        "contract_digest_ledgered": manifest["contract_digest"],
    }, kinds=ctx["kinds"])
    ad.terminate(measure_cell, unit_doc["ceilings"]["cancel_grace_s"])
    led.record(env, "check-report", unit=unit_doc["unit"], attempt=n, unit_id=measure_cell.unit_id,
               measure_cell=measure_kind, checks_ran="host-side", outcome=report["outcome"],
               behavioural_run=report["behavioural_run"], checks_run=report["checks_run"],
               criterion_ref=report["criterion_ref"], cost_micros=0)

    row = {"attempt": n, "unit_id": handle.unit_id, "model_class": model_class, "cold": not folded,
           "candidate_digest": candidate_digest, "candidate_shape": candidate["shape"],
           "outcome": report["outcome"], "failure_signature": assessor.failure_signature(report),
           "tokens_in": capabilities["tokens_in"], "tokens_out": capabilities["tokens_out"],
           "cost_micros": capabilities["cost_micros"], "stop_reason": result.stop_reason,
           "visible": visible, "report": report, "seed_gap": seed_gap,
           "contract_digest": manifest["contract_digest"],
           "stable_prefix_digest": manifest["stable_prefix_digest"],
           "capabilities": capabilities}
    led.record(env, "attempt-recorded", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               model_class=model_class, candidate_digest=candidate_digest,
               outcome=report["outcome"], cold=row["cold"],
               tokens_in=row["tokens_in"], tokens_out=row["tokens_out"],
               cost_micros=row["cost_micros"])
    return row


def brokered_calls(ctx, env, unit_doc, manifest, n, handle, model_class):
    """Every capability the unit reaches for while its turn is open. Each one
    leaves through the host: the unit holds no credential, names no endpoint,
    and carries the run's correlation as an explicit attribute."""
    led = ctx["ledger"]
    out = {"refusals": [], "tools": {}, "skills": {}}

    # capability packaging: resident up front, body on trigger, reference on demand
    pack = ctx["packaging"]()
    declared = json.load(open(os.path.join(manifest["mount"], "skills.json")))["packages"][0]
    resident = [e for e in pack.list_resident() if e["identity"] == declared["identity"]]
    resolution = pack.load_body(declared["identity"], declared["trigger"])
    opened = pack.open_reference(declared["identity"], declared["reference_path"])
    out["skills"] = {"identity": declared["identity"], "resident_listed": len(resident),
                     "tiers_loaded": list(resolution.tiers_loaded) + ["reference"],
                     "body_chars": len(resolution.body or ""), "reference_chars": len(opened.reference or "")}
    led.record(env, "capability-call", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               capability="capability-packaging", identity=declared["identity"],
               tiers_loaded=out["skills"]["tiers_loaded"], cost_micros=0)

    # tool access: the declared surface, not the catalogue; two typed refusals
    ti, tool = ctx["ti"], ctx["tools"]()
    tools_doc = json.load(open(os.path.join(manifest["mount"], "tools.json")))
    def stamp(part):
        return ti.CallContext(correlation_id=env["correlation"]["correlation_id"],
                              run_id=f"{env['correlation']['run_id']}#a{n}",
                              actor=env["actor"]["subject"],
                              idempotency_key=f"{env['idempotency_key']}#a{n}#{part}",
                              protocol_revision=tools_doc["revision"],
                              ceiling_calls=tools_doc["ceiling_calls"],
                              policy_verdict=tools_doc["policy_verdict"])
    binding = tool.bind_server(tools_doc["server_ref"], tools_doc["declared_surface"], stamp("bind"))
    catalogue = tool.list_tools(binding)
    read = tool.call_tool(binding, "notes.read", {"path": "notes/decisions.md"}, stamp("read"))
    for name, args in (("notes.append", {"path": "notes/decisions.md", "text": "x"}),
                       ("notes.flaky", {"path": "notes/decisions.md"})):
        try:
            tool.call_tool(binding, name, args, stamp(name))
            out["refusals"].append({"tool": name, "refused": False})
        except ti.Problem as exc:
            body = render_problem(exc.body)
            out["refusals"].append({"tool": name, "type": body["type"],
                                    "rule_id": exc.body.get("rule_id", "-")})
    out["tools"] = {"published": len(catalogue), "declared_surface": len(tools_doc["declared_surface"]),
                    "server_marker": binding.server_marker, "revision": binding.revision,
                    "read_ok": read.ok, "refused": len(out["refusals"])}
    led.record(env, "capability-call", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               capability="tool-access", published=len(catalogue),
               declared_surface=len(tools_doc["declared_surface"]),
               refused=[r.get("rule_id", "-") for r in out["refusals"]], cost_micros=0)

    # model access: one completion by class, through the broker. No vendor name.
    gi, gw = ctx["gi"], ctx["gateway"]()
    ask = gi.CompletionRequest.from_dict(
        {"model_class": model_class,
         "messages": [{"role": "user", "content": driver.prompt(manifest, unit_doc["task"])}],
         "idempotency_key": f"{env['idempotency_key']}#a{n}#model",
         "ceiling_micros": env["budget"]["ceiling_micros"], "cache": "ephemeral"})
    ticket = gw.submit(ask)
    while ticket.state == "pending":
        ticket = gw.claim(ticket)
    completion = ticket.result
    out.update({"completion_text": completion.text, "tokens_in": completion.tokens_in,
                "tokens_out": completion.tokens_out, "cost_micros": completion.cost_micros,
                "cached_tokens": completion.cached_tokens, "cost_status": completion.cost_status})
    led.record(env, "capability-call", unit=unit_doc["unit"], attempt=n, unit_id=handle.unit_id,
               capability="model-access", model_class=model_class, ticket_state=ticket.state,
               tokens_in=completion.tokens_in, tokens_out=completion.tokens_out,
               cached_tokens=completion.cached_tokens, cost_status=completion.cost_status,
               cost_micros=completion.cost_micros)
    return out


# --- the bounded cascade around the attempt ---------------------------------
def unit(ctx):
    """The unit's task lifecycle, which is the published one: submitted ->
    working -> completed | failed | input-required. No state is invented here."""
    env, unit_doc, led = ctx["env"], ctx["unit"], ctx["ledger"]
    esc = unit_doc["escalation"]
    permitted = esc["class_steps_permitted"]      # the bound lives on the document
    rungs = ladder(ctx["gi"])
    led.record(env, "unit-submitted", unit=unit_doc["unit"], state="submitted",
               template=unit_doc["template"], form=unit_doc["form"],
               source_ref=unit_doc["source_ref"], attempt_ceiling=ctx["attempts"],
               class_steps_permitted=permitted, contract_digest="-", cost_micros=0)
    model_class, steps_taken, folded, rows = unit_doc["attempt_class"], 0, None, []
    state, stop_reason, last_signature = "working", None, None
    for n in range(1, ctx["attempts"] + 1):
        row = attempt(ctx, n, model_class, folded)
        rows.append(row)
        if row["stop_reason"] != "end_turn":     # a cap fired: it ends the unit, not the platform
            state, stop_reason = "failed", row["stop_reason"]
            break
        if row["outcome"] == "passed":
            state, stop_reason = "completed", "end_turn"
            break
        folded = assessor.outcomes_for_unit(row["report"])
        signature = row["failure_signature"]
        if signature and signature == last_signature and steps_taken < permitted:
            to_class = step_class(rungs, unit_doc, model_class)
            if to_class != model_class:      # no record for a rung that does not exist
                model_class, steps_taken = to_class, steps_taken + 1
                led.record(env, "escalated", unit=unit_doc["unit"], attempt=n,
                           policy=esc["policy"], trigger=esc["trigger"],
                           failure_signature=signature, to_class=model_class,
                           class_steps_taken=steps_taken, class_steps_permitted=permitted,
                           ladder=list(rungs), cost_micros=0)
        last_signature = signature
    else:
        state, stop_reason = "input-required", "attempt_ceiling"
        led.record(env, "approval-parked", unit=unit_doc["unit"], state="input-required",
                   asks=esc["on_ceiling"], attempts=ctx["attempts"], cost_micros=0)
    led.record(env, "unit-" + ("completed" if state == "completed" else
                               "parked" if state == "input-required" else "failed"),
               unit=unit_doc["unit"], state=state, stop_reason=stop_reason or "-",
               attempts_used=len(rows), class_steps_taken=steps_taken,
               class_steps_permitted=permitted,
               cost_micros=sum(r["cost_micros"] for r in rows))
    return {"state": state, "stop_reason": stop_reason, "attempts": rows,
            "class_stepped": steps_taken > 0, "class_steps_taken": steps_taken,
            "spent_micros": sum(r["cost_micros"] for r in rows)}


def step_class(rungs, unit_doc, current):
    """One class up the ladder. Data, not a branch on a member name: `rungs` is
    the routing table's classes by unit price. A class the routing table does
    not carry is never stepped to and never stepped from - the run keeps the
    class it has rather than raising on a table this file does not own."""
    declared = unit_doc["escalation_class"]
    here = next((p for p in rungs if current.startswith(p)), None)
    target = next((p for p in rungs if declared.startswith(p)), None)
    if here is None or target is None:
        return current
    return declared if rungs.index(target) > rungs.index(here) else current


# --- fifty of them at once ---------------------------------------------------
def fleet(base_env, size, ctx_factory, share_run_id=False):
    """Fifty units at once. Each is its own unit: its own run id, correlation
    id, idempotency key, contract digest, cell, jail and ledger records.

    `share_run_id` is the negative case: units that reuse one run id are
    refused at admission by the run-level admission budget, which is what makes
    a fleet fifty units rather than one unit fifty times.
    """
    results, lock = {}, threading.Lock()

    def one(i):
        env = json.loads(json.dumps({k: v for k, v in base_env.items() if k != "_clock"}))
        env["correlation"] = {"run_id": base_env["correlation"]["run_id"] if share_run_id
                              else f"{base_env['correlation']['run_id']}-{i:03d}",
                              "correlation_id": f"{base_env['correlation']['correlation_id']}-{i:03d}",
                              "depth": 0}
        env["idempotency_key"] = f"{base_env['idempotency_key']}-{i:03d}"
        env["_clock"] = base_env["_clock"] + timedelta(seconds=i * 100)
        try:
            outcome = unit(ctx_factory(env, i))
            row = {"i": i, "state": outcome["state"], "attempts": len(outcome["attempts"]),
                   "cost_micros": outcome["spent_micros"],
                   "unit_id": outcome["attempts"][0]["unit_id"],
                   "candidate_digest": outcome["attempts"][-1]["candidate_digest"],
                   "containment": outcome["attempts"][-1]["report"]["outcome"],
                   "correlation_id": env["correlation"]["correlation_id"]}
        except Exception as exc:                       # a refusal is a result, not a crash
            body = getattr(exc, "body", None)
            row = {"i": i, "state": "rejected", "attempts": 0, "cost_micros": 0,
                   "problem": render_problem(body) if body else f"{type(exc).__name__}: {exc}",
                   "correlation_id": env["correlation"]["correlation_id"]}
        with lock:
            results[i] = row

    threads = [threading.Thread(target=one, args=(i,)) for i in range(size)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return [results[i] for i in sorted(results)]


# --- wiring ------------------------------------------------------------------
def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def build_context(env, unit_doc, args, led, shared):
    unit_out = os.path.join(OUT, "units", env["correlation"]["correlation_id"])
    shutil.rmtree(unit_out, ignore_errors=True)
    os.makedirs(unit_out, exist_ok=True)
    return {"env": env, "unit": unit_doc, "ledger": led, "unit_out": unit_out,
            "attempts": args.attempts or unit_doc["ceilings"]["attempts"],
            "stuck": args.stuck, "widen": args.widen_contract,
            "kinds": ("well_formedness",) if args.criteria == "wellformedness-only" else assessor.KINDS,
            "source_tests_digest": shared["source_tests_digest"],
            "ci": shared["ci"], "cell": shared["cell"], "callmod": shared["callmod"],
            "gi": shared["gi"], "gateway": shared["gateway"],
            "ti": shared["ti"], "tools": shared["tools"], "packaging": shared["packaging"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entry", help="path to an entry envelope (one of entries/*.json)")
    ap.add_argument("--unit", default=None, help="unit declaration; default: the entry's workflow_ref")
    ap.add_argument("--ledger", default=os.path.join(OUT, "ledger.jsonl"))
    ap.add_argument("--fleet", type=int, default=0,
                    help="override payload.fleet_size, which is where the fan-out is declared")
    ap.add_argument("--share-run-id", action="store_true",
                    help="fleet negative case: every unit reuses one run id")
    ap.add_argument("--attempts", type=int, help="override the declared attempt ceiling")
    ap.add_argument("--budget-micros", type=int, help="override the envelope ceiling")
    ap.add_argument("--ceiling-seconds", type=float,
                    help="override the unit's wall-clock ceiling; below the turn length it fires mid-turn")
    ap.add_argument("--stuck", action="store_true",
                    help="the attempter never learns; the same deciding check fails the same way twice")
    ap.add_argument("--widen-contract", action="store_true",
                    help="deliberate breakage: widen the contract mount after its digest was ledgered")
    ap.add_argument("--criteria", default="full", choices=["full", "wellformedness-only"])
    ap.add_argument("--verify-ledger", action="store_true")
    ap.add_argument("--json", action="store_true", help="print the unit result as JSON")
    args = ap.parse_args(argv)

    if args.verify_ledger:
        led = REF.Ledger(args.ledger)
        broken = led.verify()
        print(f"ledger {args.ledger}: {len(led.records)} records, " + (broken or "chain verifies"))
        return 2 if broken else 0
    if not args.entry:
        ap.error("--entry is required unless --verify-ledger is given")

    envelope = json.load(open(args.entry))
    errs = REF.validate(envelope, json.load(open(ENTRY_SCHEMA)))
    if errs:
        return fail(problem("document-invalid", "; ".join(errs[:4]),
                            envelope.get("correlation", {}).get("correlation_id")).body())
    if args.budget_micros is not None:
        envelope["budget"]["ceiling_micros"] = args.budget_micros
    envelope["_clock"] = datetime.strptime(envelope["occurred_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)
    unit_doc = json.load(open(args.unit or os.path.join(HERE, envelope["intent"]["workflow_ref"])))
    if args.ceiling_seconds is not None:
        unit_doc["ceilings"]["wall_seconds"] = args.ceiling_seconds

    adapter_name = os.environ.get("ADAPTER", "dryrun")
    ci, cell_cls, callmod = harnesses.containment(adapter_name)
    gi, gateway_cls = harnesses.gateway(os.environ.get("GATEWAY_ADAPTER", "dryrun"))
    ti, tool_cls = harnesses.tool_access(os.environ.get("TOOLS_ADAPTER", "dryrun"))
    _, pack_cls = harnesses.packaging(os.environ.get("PACKAGING_ADAPTER", "dryrun"))
    cell = cell_cls({"tuning": {"cancel_poll_interval_s": 0.02, "egress_probe_attempts": 3},
                     "jail_root": os.path.join(OUT, "jails", adapter_name)})
    shared = {"ci": ci, "cell": cell, "callmod": callmod, "gi": gi,
              "gateway": lambda: gateway_cls(), "ti": ti,
              "tools": lambda: tool_cls({"budget": {"ceiling_calls": 8}}),
              "packaging": lambda: pack_cls(),
              "source_tests_digest": assessor.tree_digest(os.path.join(HERE, "source", "tests"))}

    # 3. price the plan before anything runs
    manifest_preview = contract_role.render(unit_doc, envelope, 0, None,
                                            os.path.join(OUT, "plan-preview"))
    steps, worst, per_attempt = plan(unit_doc, envelope, gi,
                                     driver.prompt(manifest_preview, unit_doc["task"]))
    ceiling = envelope["budget"]["ceiling_micros"]
    # The fan-out is declared in the envelope the door sent, so the difference
    # between the schedule door and the others is in the document. --fleet is an
    # override for a caller who wants a different width than the door declared.
    fleet_size = args.fleet or envelope["payload"].get("fleet_size", 1)
    print(f"PLAN  {unit_doc['unit']}  cell={cell.binding().adapter}  units={fleet_size}  "
          f"worst case {worst * fleet_size} micros, shortest finishing path "
          f"{per_attempt * fleet_size}, ceiling {ceiling} per unit")
    table([(s["step"], s["op"], s["model_class"], s["estimate_micros"]) for s in steps],
          ("step", "op", "model_class", "est_micros"))
    led = RunLedger(args.ledger)
    if per_attempt > ceiling:
        led.record(envelope, "unit-rejected", unit=unit_doc["unit"], state="rejected",
                   stop_reason="budget_exhausted", shortest_path_micros=per_attempt,
                   ceiling_micros=ceiling, cells_admitted=0, cost_micros=0)
        return fail(problem("budget-exhausted",
                            f"the shortest finishing path costs {per_attempt} micros and the ceiling "
                            f"is {ceiling}; refused before execution, no cell was admitted",
                            envelope["correlation"]["correlation_id"], stop_reason="budget_exhausted").body())

    if fleet_size > 1 or args.share_run_id:
        rows = fleet(envelope, fleet_size,
                     lambda env, i: build_context(env, unit_doc, args, led, shared),
                     share_run_id=args.share_run_id)
        states = {}
        for row in rows:
            states[row["state"]] = states.get(row["state"], 0) + 1
        table([(r["i"], r["correlation_id"], r["state"], r["attempts"], r["cost_micros"],
                (r.get("candidate_digest") or r.get("problem", {}).get("type", "-"))[:34]) for r in rows[:10]],
              ("#", "correlation_id", "state", "attempts", "cost_micros", "candidate / problem"))
        if len(rows) > 10:
            print(f"... {len(rows) - 10} more")
        print(f"\nFLEET  {len(rows)} units, " +
              ", ".join(f"{v} {k}" for k, v in sorted(states.items())) +
              f", distinct correlation ids {len({r['correlation_id'] for r in rows})}, "
              f"distinct candidates {len({r.get('candidate_digest') for r in rows if r.get('candidate_digest')})}")
        if args.json:
            print(json.dumps({"fleet": rows, "states": states,
                              "unregistered_problem_types": UNREGISTERED}, indent=2, sort_keys=True))
        return 0

    outcome = unit(build_context(envelope, unit_doc, args, led, shared))
    last = outcome["attempts"][-1]
    print(f"\nRESULT  entry={envelope['kind']}  actor={envelope['actor']['subject']}  "
          f"correlation={envelope['correlation']['correlation_id']}  cell={cell.binding().adapter}")
    table([(r["attempt"], r["model_class"], "cold" if r["cold"] else "folded", r["stop_reason"],
            r["candidate_digest"][:19], r["outcome"], r["failure_signature"] or "-", r["cost_micros"])
           for r in outcome["attempts"]],
          ("attempt", "model_class", "context", "stop_reason", "candidate", "outcome", "failed", "cost"))
    print()
    table([(c["check_id"], c["kind"], c["outcome"]) for c in last["report"]["checks"]] or [("-", "-", "-")],
          ("deciding check", "kind", "outcome"))
    print(f"\nvisible checks (do not decide): " +
          ", ".join(f"{c}={o}" for c, o in last["visible"]))
    print(f"tool access: {last['capabilities']['tools']['published']} published, "
          f"{last['capabilities']['tools']['declared_surface']} in the declared surface, "
          f"{last['capabilities']['tools']['refused']} refused before dispatch")
    print(f"skills: {last['capabilities']['skills']['identity']} tiers "
          f"{last['capabilities']['skills']['tiers_loaded']}")
    print(f"contract: stable prefix {last['stable_prefix_digest'][:19]} "
          f"(identical across attempts), digest {last['contract_digest'][:19]}")
    print(f"\n{outcome['state']}: {len(outcome['attempts'])} attempts, class stepped "
          f"{outcome['class_stepped']}, spent {outcome['spent_micros']} of {ceiling} micros, "
          f"ledger head {led.head()[:19]}...")
    if UNREGISTERED:
        print(f"gap: problem types raised with no row in the closed registry: {UNREGISTERED}")
    if args.json:
        print(json.dumps({"state": outcome["state"], "attempts": [
            {k: v for k, v in r.items() if k not in ("report", "capabilities")}
            for r in outcome["attempts"]], "unregistered_problem_types": UNREGISTERED},
            indent=2, sort_keys=True))
    return 0 if outcome["state"] == "completed" else 3


if __name__ == "__main__":
    sys.exit(main())
