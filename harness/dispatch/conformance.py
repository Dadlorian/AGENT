#!/usr/bin/env python3
"""The conformance run every dispatcher must pass, and the report the swap proof
compares.

    python3 harness/dispatch/conformance.py --adapter dryrun --adapter second

It is one suite over three definitions of done:

  S  the Dispatch seam      a malformed request refused before anything happens;
                            a cancel reaching a terminal state inside the grace
                            window; a ceiling that terminates the unit with a
                            recorded spend; an interrupted run whose partial
                            outputs are already durable; every failure typed;
                            resume, replay and the conflict; the ordering of the
                            guarantee chain; the step chain verifying.
  P  the Planner            the same document planned twice at the same head is
                            byte-identical, priced from records and not from a
                            sampled estimate, refused rather than guessed where a
                            cost row is missing, and identical across bindings.
  J  the Judge              one result graded a hundred times gives one verdict;
                            over fifty recorded requests the criterion string
                            appears zero times.

Nothing here reads a dispatcher's account of itself where it can count from
outside: the step records are read through `read_step`, the effect of a replay
is measured by the step log not growing, and the marker is read from the running
dispatcher rather than from the binding that selected it - two green runs of one
dispatcher read exactly like a proven swap otherwise.

Python 3.11 standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import core  # noqa: E402
from adapters.base import FIXTURE_OBSERVATIONS  # noqa: E402
from adapters.steplog import StepLog  # noqa: E402
from call import build_request  # noqa: E402
from interface import (ADAPTERS, Dispatcher, DispatchRequest, Problem,  # noqa: E402
                       canonical, is_typed, load_dispatcher)

FIXTURES = os.path.join(HERE, "fixtures")
MARKER, GUARD, BOUND = ">>> CALLER CODE", "if __name__", 40
STORAGE = re.compile(r"""["'][^"']*(\.jsonl|\.ndjson|\.db|\.sqlite|\.journal)["']""")
PRODUCTS = ("firecracker", "systemd", "litellm", "temporal", "langfuse", "opa ",
            "openai", "anthropic", "kubernetes", "docker")
CORPUS = 50
GRADINGS = 100
TRIP_CEILING = 600_000        # above the plan's floor, below what the unit spends
BREAKAGES = ("", "durability", "criterion", "head")


def document(breakage: str = "") -> dict:
    doc = json.load(open(os.path.join(FIXTURES, "document.json")))
    if breakage == "criterion":
        # The breakage core-judge names: inline the criterion text into the
        # document's definition of done, which dispatch then carries to the unit.
        doc["definition_of_done"]["must_contain"] = core.criterion_tokens()
    return doc


def envelope() -> dict:
    return core.load_example("entries/human.json")


def heads() -> dict:
    return json.load(open(os.path.join(FIXTURES, "heads.json")))


def request(dispatch_id: str, breakage: str = "", **kw) -> DispatchRequest:
    req = build_request(envelope(), document(breakage), dispatch_id=dispatch_id, **kw)
    req.idempotency_key = f"{dispatch_id}-key"
    return req


class NoNetwork:
    """A socket guard around the planner: a plan that reached for an estimate
    would have to open one, and this counts every attempt instead of trusting
    that it did not."""

    def __enter__(self):
        self.connects_inet = 0
        self.real = socket.socket

        def guarded(family=socket.AF_INET, *a, **k):
            if family in (socket.AF_INET, socket.AF_INET6):
                self.connects_inet += 1
                raise OSError("the planner opened an internet socket")
            return self.real(family, *a, **k)

        socket.socket = guarded
        return self

    def __exit__(self, *exc):
        socket.socket = self.real
        return False


def conform(adapter: str, base: str, breakage: str = "") -> dict:
    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, ok: bool, detail: str = "") -> bool:
        checks.append((name, bool(ok), detail))
        return bool(ok)

    def d(case: str) -> str:
        path = os.path.join(base, case)
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)
        return path

    def dispatcher(case: str) -> Dispatcher:
        return load_dispatcher(adapter, d(case))

    problems: list[dict] = []

    def refusal(fn) -> dict | None:
        """Every refusal in this suite lands here, so the untyped count is taken
        over all of them rather than over the ones someone remembered."""
        try:
            fn()
            return None
        except Problem as p:
            problems.append(p.body)
            return p.body

    report: dict = {"adapter": adapter}

    # -- S1 a malformed request is refused before anything happens ----------
    s1 = dispatcher("s1-malformed")
    bad = request("dsp-malformed")
    bad.budget = {"ceiling_micros": -1, "currency": "USD", "on_exceed": "never"}
    body = refusal(lambda: s1.dispatch(bad))
    chk("S1 a malformed request is refused with document-invalid",
        body is not None and body["type"] == "urn:agentic:problem:document-invalid",
        str(body and body["type"]))
    chk("S1 the refusal had no side effect: no step was recorded",
        s1.read_step("dsp-malformed") == [], f"{len(s1.read_step('dsp-malformed'))} steps")

    # -- S9 identity: a hop that widens scope is refused before execution ----
    s9 = dispatcher("s9-delegation")
    widened = request("dsp-widened")
    widened.actor = {"subject": "agent:fixer",
                     "delegation_chain": [{"actor": "user:corey", "obtained_via": "direct"},
                                          {"actor": "agent:fixer", "obtained_via": "delegation",
                                           "widens_scope": True}]}
    body = refusal(lambda: s9.dispatch(widened))
    chk("S9 a delegation hop that widens scope is refused with policy-denied",
        body is not None and body["type"] == "urn:agentic:problem:policy-denied",
        str(body and body["type"]))
    chk("S9 nothing was spent on the refused dispatch",
        s9.read_step("dsp-widened") == [])

    # -- S2/S4 cancel, and what an interrupted run leaves behind -------------
    s2 = dispatcher("s2-cancel")
    creq = request("dsp-cancel")
    creq.deadline["cancel_grace_s"] = 2
    accepted = s2.cancel("dsp-cancel", creq.deadline["cancel_grace_s"])
    started = time.monotonic()
    cancelled = s2.dispatch(creq)
    elapsed = time.monotonic() - started
    expected_stop = "cancelled" if s2.cancellation_reach == "mid_call" else "cancel_timeout"
    chk("S2 the cancel was accepted rather than answered with a stop",
        accepted["accepted"] and accepted["already_terminal"] is False)
    chk("S2 a terminal state was reached inside cancel_grace_s",
        elapsed <= creq.deadline["cancel_grace_s"] and cancelled.state in ("canceled", "completed"),
        f"{elapsed:.2f}s of {creq.deadline['cancel_grace_s']}s, state={cancelled.state}")
    chk("S2 the stop reason is the one this adapter's declared reach allows",
        cancelled.stop_reason == expected_stop,
        f"{cancelled.stop_reason} (reach={s2.cancellation_reach})")
    chk("S4 the interrupted run is partial", cancelled.partial, f"partial={cancelled.partial}")
    heads_present = [o.recorded_at_head for o in cancelled.outputs if o.name != "plan"]
    chk("S4 at least one output is durable: recorded_at_head is not null",
        len(heads_present) >= 1 and all(h for h in heads_present),
        f"{len(heads_present)} outputs, nulls={sum(1 for h in heads_present if not h)}")
    chk("S2 cancelling an already-terminal dispatch returns the result, not an error",
        (s2.cancel("dsp-cancel", 2) or {}).get("result", {}).get("dispatch_id") == "dsp-cancel")

    # -- S3 the ceiling terminates the unit ---------------------------------
    s3 = dispatcher("s3-budget")
    breq = request("dsp-budget", ceiling_micros=TRIP_CEILING)
    trip = s3.dispatch(breq)
    chk("S3 a unit that would cross its ceiling stops with budget_exhausted",
        trip.stop_reason == "budget_exhausted" and trip.state == "failed", trip.stop_reason)
    chk("S3 the recorded spend is non-zero and at most the ceiling",
        0 < trip.usage.spend_micros <= TRIP_CEILING,
        f"{trip.usage.spend_micros} of {TRIP_CEILING}")
    chk("S3 the terminating failure is typed", is_typed(trip.problem),
        str((trip.problem or {}).get("type")))
    if trip.problem:
        problems.append(trip.problem)

    # -- S6 resume continues at the first incomplete step -------------------
    rreq = request("dsp-budget-resume", ceiling_micros=2_000_000)
    rreq.idempotency_key = breq.idempotency_key
    rreq.previous_dispatch_id = "dsp-budget"
    resumed = s3.resume(rreq)
    chk("S6 the resumed unit completed", resumed.state == "completed", resumed.stop_reason)
    chk("S6 committed steps were replayed, not re-executed",
        resumed.usage.steps_replayed > 0,
        f"{resumed.usage.steps_replayed} replayed, {resumed.usage.steps_executed} executed")
    chk("S6 the resume carried the earlier spend rather than starting free",
        resumed.usage.spend_micros > trip.usage.spend_micros,
        f"{trip.usage.spend_micros} -> {resumed.usage.spend_micros}")
    chk("S6 the prior partial result was not mutated",
        s3.log.by(kind="dispatch-terminal", dispatch_id="dsp-budget")[-1]["stop_reason"]
        == "budget_exhausted")

    # -- S7/S8 replay and the conflict --------------------------------------
    s7 = dispatcher("s7-replay")
    preq = request("dsp-replay")
    first = s7.dispatch(preq)
    committed_before = len(s7.log.by(kind="step-committed"))
    again = s7.dispatch(preq)
    committed_after = len(s7.log.by(kind="step-committed"))
    chk("S7 a repeated request returns the recorded result byte for byte",
        canonical(again.dict()) == canonical(first.dict()))
    chk("S7 nothing was re-executed on the replay",
        committed_after == committed_before, f"{committed_before} -> {committed_after}")
    conflict = request("dsp-replay-conflict", ceiling_micros=999_999)
    conflict.idempotency_key = preq.idempotency_key
    body = refusal(lambda: s7.dispatch(conflict))
    chk("S8 the same key with a different body is refused as idempotency-conflict",
        body is not None and body["type"] == "urn:agentic:problem:idempotency-conflict",
        str(body and body["type"]))

    # -- S10 ordering and the chain -----------------------------------------
    records = s7.log.records()
    policy = next((r["seq"] for r in records
                   if r["kind"] == "policy-decision" and r["dispatch_id"] == "dsp-replay"), None)
    metered = next((r["seq"] for r in records
                    if r["kind"] == "step-committed" and r["dispatch_id"] == "dsp-replay"), None)
    chk("S10 the policy decision is recorded before the first metered call",
        policy is not None and metered is not None and policy < metered, f"{policy} < {metered}")
    chk("S10 the step chain verifies, so a checkpoint is distinguishable from an edit",
        s7.log.verify() is None, str(s7.log.verify()))

    # -- S5 every failure body is typed -------------------------------------
    # content_type is no longer a body member (errors-q5: it was this adapter's
    # own invented shape, no other body carried it -- media type is transport
    # metadata, rendered once by the shared point, never a per-adapter body key).
    untyped = [p for p in problems if not is_typed(p)]
    chk("S5 every failure body is typed, with the registered type as its `type` member",
        not untyped, f"{len(problems)} problems, {len(untyped)} untyped")

    # -- P the Planner ------------------------------------------------------
    binding = load_dispatcher(adapter, d("p-plan"))
    with NoNetwork() as guard:
        inputs = binding.cost_inputs(binding.head_for_plan())
        plan_1 = core.plan(document(breakage), binding.head_for_plan(), inputs)
        plan_2 = core.plan(document(breakage), binding.head_for_plan(), inputs)
    chk("P1 the same document at the same head plans byte-identically",
        plan_1.plan_digest == plan_2.plan_digest,
        f"{plan_1.plan_digest[:19]} vs {plan_2.plan_digest[:19]}")
    chk("P2 the planner opened no internet socket", guard.connects_inet == 0,
        f"connects_inet={guard.connects_inet}")
    chk("P3 the plan priced steps rather than asserting on an empty plan",
        plan_1.steps_priced > 0, f"steps_priced={plan_1.steps_priced}")
    body = refusal(lambda: core.plan(document(breakage), heads()["head_before_cli"],
                                     binding.cost_inputs(heads()["head_before_cli"])))
    chk("P4 a step with no cost row at this head is refused, not estimated",
        body is not None and body.get("step_id") == "fix#1"
        and body["type"] == "urn:agentic:problem:document-invalid",
        f"{body and body.get('step_id')} / {body and body.get('proposed_type')}")

    # -- J the Judge --------------------------------------------------------
    criterion = core.resolve_criterion(document()["definition_of_done"]["criterion_ref"])
    graded = first.summary
    verdicts = {core.judge(graded, criterion).verdict for _ in range(GRADINGS)}
    applied = min(core.judge(graded, criterion).checks_applied for _ in range(GRADINGS))
    chk("J1 one result graded a hundred times gives one verdict",
        len(verdicts) == 1, f"verdicts_distinct={len(verdicts)} over {GRADINGS} runs")
    chk("J1 every grading decided at least one check", applied > 0,
        f"checks_applied_min={applied}")
    sampled = core.judge(graded, criterion, mode="in_loop")
    chk("J1 in-loop grading applies a proper subset, deterministically",
        0 < sampled.checks_applied <= len(criterion["checks"])
        and sampled.verdict == core.judge(graded, criterion, mode="in_loop").verdict,
        f"{sampled.checks_applied} of {len(criterion['checks'])} checks")

    corpus = load_dispatcher(adapter, d("j-corpus"))
    for i in range(CORPUS):
        refusal(lambda i=i: corpus.admit(request(f"dsp-corpus-{i:03d}", breakage)))
    scanned = sum(1 for _ in open(corpus.requests_path))
    hits = core.criterion_hits([corpus.requests_path])
    chk("J2 the corpus is large enough to mean something", scanned >= CORPUS,
        f"requests_scanned={scanned}")
    chk("J2 the criterion string appears nowhere the graded unit can read",
        hits == 0, f"criterion_hits={hits}")
    chk("J2 the verdict a unit is handed back names check ids, not criterion text",
        core.criterion_hits([]) == 0 and not any(
            token in core.judge(graded, criterion).detail for token in core.criterion_tokens()))

    passed = sum(1 for _, ok, _ in checks if ok)
    report.update({
        "dispatcher_marker": binding.dispatcher_marker,
        "binding": binding.binding(),
        "plan_digest": plan_1.plan_digest, "plan_head": plan_1.head,
        "read_mode": plan_1.read_mode, "steps_priced": plan_1.steps_priced,
        "plans_computed": 2, "connects_inet": guard.connects_inet,
        "verdict": core.judge(graded, criterion).verdict,
        "verdicts_distinct": len(verdicts), "checks_applied_min": applied,
        "requests_scanned": scanned, "criterion_hits": hits,
        "spend_micros": first.usage.spend_micros,
        "cancel_stop_reason": cancelled.stop_reason,
        "partial_outputs_with_head": sum(1 for h in heads_present if h),
        "partial_outputs_without_head": sum(1 for h in heads_present if not h),
        "steps_replayed_on_resume": resumed.usage.steps_replayed,
        "problems_seen": len(problems), "untyped": len(untyped),
        "assertions_run": len(checks), "assertions_passed": passed,
        "failures": [{"check": n, "detail": det} for n, ok, det in checks if not ok],
        "checks": [{"check": n, "ok": ok, "detail": det} for n, ok, det in checks]})
    return report


# --------------------------------------------------------------------------
# The migration counter, the caller measurement and the product scan
# --------------------------------------------------------------------------
def migrated_paths(out_dir: str) -> tuple[int, list[dict]]:
    """How many execution paths answer through the seam.

    PASS.md records three implementations of dispatch and no contract between
    them (F-b5-03) but does not name them, which seam-dispatch-implement carries
    as an open question. What is countable here is the number of shims that
    answer every seam shape: each declares its execution model, subclasses the
    one interface, and refuses a malformed request with the registered type
    without reaching its executor - the live shim included, on a host where its
    executor is not reachable at all.
    """
    rows = []
    for name in ADAPTERS:
        shim = load_dispatcher(name, os.path.join(out_dir, "migrated", name))
        bad = request(f"dsp-shape-{name}")
        bad.correlation = {"run_id": "x"}          # missing root_dispatch_id
        try:
            shim.dispatch(bad)
            typed = False
        except Problem as p:
            typed = p.body["type"] == "urn:agentic:problem:document-invalid"
        rows.append({"path": name, "marker": shim.dispatcher_marker,
                     "unit_lifetime": shim.unit_lifetime,
                     "cancellation_reach": shim.cancellation_reach,
                     "answers_seam_shapes": bool(isinstance(shim, Dispatcher) and typed)})
    return sum(1 for r in rows if r["answers_seam_shapes"]), rows


def append_observation(path: str, selector: str, micros: int) -> str:
    """One more measured cost, appended to the chained log the way any producer
    would. Used only by the `head` breakage, to move the log under a binding
    that resolves the head itself instead of reading at the head it was handed."""
    log = StepLog(path)
    return log.append(kind="cost-observation", selector=selector, micros=micros,
                      window="2026-09", unit="micros")


def caller_lines() -> tuple[int, list[str]]:
    lines = open(os.path.join(HERE, "call.py")).read().splitlines()
    marks = [i for i, line in enumerate(lines) if MARKER in line]
    assert len(marks) == 1, f"expected one {MARKER} marker, found {len(marks)}"
    body = lines[marks[0] + 1:]
    end = next((i for i, line in enumerate(body) if line.startswith(GUARD)), len(body))
    counted = [line for line in body[:end] if line.strip() and not line.strip().startswith("#")]
    storage = [f"call.py:{n}: {line.strip()}" for n, line in enumerate(lines, 1)
               if STORAGE.search(line)]
    return len(counted), storage


def product_scan() -> list[str]:
    """A product name outside adapters/ and the README env table is a contract
    shaped around one executor."""
    hits = []
    # conformance.py itself is excluded: it has to carry the names it looks for.
    for name in ("interface.py", "core.py", "call.py",
                 os.path.join("adapters", "base.py"), os.path.join("adapters", "steplog.py")):
        for n, line in enumerate(open(os.path.join(HERE, name)), 1):
            low = line.lower()
            for product in PRODUCTS:
                if product in low:
                    hits.append(f"{name}:{n}: {line.strip()}")
    return hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the Dispatch seam.")
    ap.add_argument("--adapter", action="append", default=[], choices=ADAPTERS)
    ap.add_argument("--out", default=os.path.join(HERE, "out", "conformance"))
    ap.add_argument("--report", default="")
    ap.add_argument("--break", dest="breakage", choices=BREAKAGES, default="",
                    help="the deliberate breakage: the run must fail")
    ap.add_argument("--caller-lines", action="store_true")
    ap.add_argument("--product-scan", action="store_true")
    args = ap.parse_args(argv)

    if args.caller_lines:
        lines, storage = caller_lines()
        print("\n".join(storage) or "call.py names no adapter storage")
        print(f"caller_lines={lines} bound={BOUND} storage_named={len(storage)}")
        return 1 if lines >= BOUND or storage else 0
    if args.product_scan:
        hits = product_scan()
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={len(hits)}")
        return 1 if hits else 0

    if args.breakage:
        os.environ["DISPATCH_BREAK"] = args.breakage
    adapters = args.adapter or ["dryrun"]
    work_log = ""
    if args.breakage == "head":
        # Nothing in the fixture is edited: the run gets its own copy of the
        # cost log, and one observation is appended to it between the two
        # bindings' invocations. Only the binding that resolves the head itself
        # can notice, which is what makes the report name it.
        os.makedirs(args.out, exist_ok=True)
        work_log = os.path.join(args.out, "cost-observations.jsonl")
        shutil.copy(FIXTURE_OBSERVATIONS, work_log)
        os.environ["DISPATCH_OBSERVATIONS"] = work_log
    per = []
    for i, name in enumerate(adapters):
        if work_log and i:
            append_observation(work_log, "agent:cli-", 900_000)
        per.append(conform(name, os.path.join(args.out, name), args.breakage))
    paths, path_rows = migrated_paths(args.out)
    digests = sorted({p["plan_digest"] for p in per})
    verdicts = sorted({p["verdict"] for p in per})
    markers = sorted({p["dispatcher_marker"] for p in per})
    report = {"adapters_run": len(per), "migrated_paths": paths, "paths": path_rows,
              "plan_digest_mismatches": max(0, len(digests) - 1),
              "verdict_mismatches": max(0, len(verdicts) - 1),
              "distinct_markers": markers, "breakage": args.breakage,
              "criterion_hits": sum(p["criterion_hits"] for p in per),
              "untyped": sum(p["untyped"] for p in per), "per_adapter": per}
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)

    ok = True
    for p in per:
        for failure in p["failures"]:
            print(f"  FAIL [{p['adapter']}] {failure['check']}: {failure['detail']}")
        print(f"adapter={p['adapter']} marker={p['dispatcher_marker']} "
              f"assertions_run={p['assertions_run']} "
              f"failed={p['assertions_run'] - p['assertions_passed']} untyped={p['untyped']} "
              f"plan_digest={p['plan_digest'][7:19]} verdict={p['verdict']} "
              f"cancel_stop={p['cancel_stop_reason']} criterion_hits={p['criterion_hits']}")
        ok = ok and not p["failures"] and p["assertions_run"] > 0
    print(f"adapters_run={report['adapters_run']} migrated_paths={paths} "
          f"plan_digest_mismatches={report['plan_digest_mismatches']} "
          f"verdict_mismatches={report['verdict_mismatches']} "
          f"distinct_markers={len(markers)}")
    if paths != 3:
        print(f"  FAIL migrated_paths is {paths}, not 3")
        ok = False
    if report["plan_digest_mismatches"] or report["verdict_mismatches"]:
        print("  FAIL two bindings planned or graded differently for the same document")
        ok = False
    if len(per) > 1 and len(markers) != len(per):
        print("  FAIL the same dispatcher answered twice; that is not a swap")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
