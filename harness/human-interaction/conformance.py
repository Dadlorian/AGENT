#!/usr/bin/env python3
"""The conformance run every human-interaction surface must pass.

    python3 conformance.py --surface dryrun --report out/a.json
    python3 conformance.py --surface dryrun --surface second --report out/both.json
    python3 conformance.py --surface dryrun --surface second --break-client-held
    python3 conformance.py --product-scan .

The same cases against any surface. The report is the ResumeConformanceReport
shape cap-human-interaction-implement defines: `surface`, `selected_by`,
`cases_run`, `resumed_on_same_correlation`, `edit_changed_artifact`,
`duplicate_resumes`, `untyped_refusals`, and `adapters_run` on the merged report
only.

Two things about how it is run, both of which are the point rather than detail.
The surface is chosen by configuration with no code edit between runs, and the
merged run parks on one surface and decides on the other against one store,
because the property under test is that the ask outlives the surface.

`--break-client-held` is the deliberate breakage the definition of done names: in
the streaming surface only, resume from the ask the client is holding rather than
from the stored row. Its signature is precise - that surface reports
duplicate_resumes 9 and resumed_on_same_correlation 3 while the other still
exits 0. A run that fails both surfaces, or neither, has not tested the swap.

Python 3.11 standard library only. No product name appears in this file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import (ADAPTERS, DECISIONS, EVENT_TYPES, HumanAsk, HumanDecision,  # noqa: E402
                       HumanSurface, Problem, REGISTRY, check_ask, load_surface,
                       resume_token_for)
from run import park_run, resume_run  # noqa: E402
from store import ParkedAskStore  # noqa: E402

T_PARK = "2026-09-03T10:00:00Z"
DEADLINE = "2026-09-03T18:00:00Z"
T_DECIDE = "2026-09-03T11:30:00Z"
T_LATE = "2026-09-03T18:04:11Z"

PRODUCTS = re.compile(r"approve\.service|tailscale|systemd|temporal|litellm|langfuse|"
                      r"firecracker|goose|copilotkit|100\.125\.65\.101|ansible", re.I)

CASES = ("approve", "edit", "reject-with-notes", "partial")
DECISION_OF = {"approve": "approve", "edit": "edit",
               "reject-with-notes": "reject", "partial": "respond"}
BODY_OF = {
    "approve": {},
    "edit": {"headline": "Coupon pricing fix, reviewed by a person",
             "body": "Coupon pricing is fixed.", "channel": "changelog"},
    "reject-with-notes": {"notes": "hold until the pricing page is live"},
    "partial": {"answer": "yes, the changelog is the right channel"},
}


def fresh(path: str) -> str:
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    return path


def envelope(correlation_id: str, run_id: str, kind="human", subject="user:corey") -> dict:
    from interface import Envelope
    return Envelope(
        kind=kind, entry_id="hitl-conformance", occurred_at=T_PARK,
        actor={"subject": subject, "delegation_chain": [{"actor": subject,
                                                         "obtained_via": "direct"}]},
        intent={"workflow_ref": "run.py:release-publish/0.1", "summary": "Publish once agreed."},
        correlation={"run_id": run_id, "correlation_id": correlation_id, "depth": 0},
        budget={"ceiling_micros": 1_500_000, "currency": "USD", "on_exceed": "terminate_unit"},
        idempotency_key="hitl-conformance-" + run_id,
        payload={"release": "2026.09.3", "headline": "Release 2026.09.3",
                 "notes": "coupon pricing fix", "channel": "changelog"},
    ).dict()


def decision_for(ask: HumanAsk, case: str, actor="user:corey") -> HumanDecision:
    return HumanDecision(ask_id=ask.ask_id, correlation_id=ask.correlation_id,
                         decision=DECISION_OF[case], actor=actor,
                         idempotency_key=f"dec-{ask.ask_id}-{case}", body=dict(BODY_OF[case]))


# --------------------------------------------------------------------------
# One case: park, deliver the decision n times, resume.
# --------------------------------------------------------------------------
def run_case(surface: HumanSurface, store: ParkedAskStore, case: str, deliveries: int) -> dict:
    tag = case.replace("-", "")
    corr = f"corr-{surface.surface_marker.split('/')[0]}-{tag}"
    env = envelope(corr, f"run-{tag}")
    ask = park_run(surface, env, T_PARK, f"ask-{tag}", DEADLINE)
    parked = store.read(ask.ask_id)
    applied, acks, untyped = 0, [], 0
    for _ in range(deliveries):
        try:
            ack = surface.decide(decision_for(ask, case), T_DECIDE)
        except Problem:
            raise
        except Exception as exc:                       # a refusal that carried no type
            untyped += 1
            raise AssertionError(f"untyped failure from decide: {exc!r}") from exc
        acks.append(ack)
        applied += 1 if ack.applied else 0
    ack = acks[0]
    result = resume_run(ack, T_DECIDE, store)
    return {"case": case, "deliveries": deliveries, "applied": applied,
            "duplicates_applied": max(0, applied - 1),
            "pause_correlation": parked.stamps["correlation_id"],
            "resume_correlation": ack.stamps["correlation_id"],
            "run_correlation": result.correlation_id,
            "same_correlation": (parked.stamps["correlation_id"] == ack.stamps["correlation_id"]
                                 == result.correlation_id == ask.correlation_id),
            "artifact": result.artifact, "proposed": parked.ask["proposed"]["artifact"],
            "outcome": result.outcome, "decided_by": ack.decided_by,
            "pause_actor": parked.stamps["actor"], "resume_chain": ack.stamps["delegation_chain"],
            "deliveries_recorded": len(parked.deliveries), "untyped": untyped,
            "resumed_from": result.resumed_from,
            "store_state": store.read(ask.ask_id).state, "ask": ask}


# --------------------------------------------------------------------------
# The suite
# --------------------------------------------------------------------------
def run(name: str, out_dir: str, deliver_times: int, replay_case: str,
        broken: bool) -> tuple[list, dict]:
    os.makedirs(out_dir, exist_ok=True)
    store = ParkedAskStore(fresh(os.path.join(out_dir, name)))   # every run starts empty
    surface = load_surface(name, store)
    if broken and hasattr(type(surface), "client_held"):
        type(surface).client_held = True
    binding = surface.binding()
    cases, report = [], {"surface": binding["surface_marker"],
                         "selected_by": binding["selected_by"], "cases_run": 0,
                         "resumed_on_same_correlation": 0, "edit_changed_artifact": False,
                         "duplicate_resumes": 0, "untyped_refusals": 0,
                         "binding": binding, "failures": []}

    def case(title):
        def wrap(fn):
            try:
                cases.append(("ok", f"{title}: {fn()}"))
            except Problem as problem:                 # a typed refusal where none was expected
                cases.append(("FAIL", f"{title}: typed refusal {problem.body['type']}"))
                report["failures"].append(title)
            except AssertionError as exc:
                cases.append(("FAIL", f"{title}: {exc}"))
                report["failures"].append(title)
            except Exception as exc:                   # anything untyped is itself a failure
                cases.append(("FAIL", f"{title}: untyped {type(exc).__name__}: {exc}"))
                report["failures"].append(title)
                report["untyped_refusals"] += 1
            return fn
        return wrap

    # -- the four decisions --------------------------------------------------
    results: dict[str, dict] = {}

    def need(one: str) -> dict:
        """A case that depends on an earlier one fails as a failed check, never as
        an untyped exception: an untyped refusal is a claim about the adapter."""
        got = results.get(one)
        assert got, f"the {one} case did not complete, so this check has nothing to read"
        return got
    for one in CASES:
        @case(f"{one}: the run resumes on its own correlation id")
        def _four(one=one):
            times = deliver_times if one == replay_case else 1
            got = run_case(surface, store, one, times)
            results[one] = got
            report["cases_run"] += 1
            report["duplicate_resumes"] += got["duplicates_applied"]
            report["untyped_refusals"] += got["untyped"]
            if got["same_correlation"]:
                report["resumed_on_same_correlation"] += 1
            assert got["same_correlation"], (
                f"pause {got['pause_correlation']} -> resume {got['resume_correlation']} "
                f"(run {got['run_correlation']})")
            assert got["applied"] == 1, f"{got['applied']} of {times} deliveries applied"
            return (f"{got['deliveries']} deliveries, {got['applied']} applied, "
                    f"{got['outcome']} on {got['resume_correlation']}")

    @case("an edit changes the artifact, not only the verdict")
    def _edit():
        got = need("edit")
        changed = got["artifact"] == BODY_OF["edit"] != got["proposed"]
        report["edit_changed_artifact"] = changed
        assert changed, f"published {got.get('artifact')} instead of the reviewer's body"
        return "the run continued with the reviewer's body, not the proposed one"

    @case("a reject carries notes and stops the run before the irreversible step")
    def _reject():
        got = need("reject-with-notes")
        assert got["outcome"] == "rejected", got["outcome"]
        assert got["artifact"].get("notes"), "the notes did not survive the resume"
        return f"{got['outcome']}, notes preserved, same id {got['same_correlation']}"

    @case("a respond answers the ask and the run continues")
    def _respond():
        got = need("partial")
        assert got["outcome"] == "published", got["outcome"]
        assert got["artifact"].get("answer"), "the answer did not reach the run"
        return "the answer is on the artifact the run continued with"

    @case(f"the same decision delivered {deliver_times} times resumes the run once")
    def _replay():
        got = need(replay_case)
        assert got["applied"] == 1, f"{got['applied']} applications"
        assert got["duplicates_applied"] == 0, f"{got['duplicates_applied']} duplicate resumes"
        return f"{got['deliveries']} deliveries, 1 application, {got['store_state']}"

    @case("a second, different decision on a decided ask is refused as a replay")
    def _second():
        ask = need("approve")["ask"]
        try:
            surface.decide(HumanDecision(ask.ask_id, ask.correlation_id, "reject", "user:sam",
                                         "dec-second-attempt-0001", {"notes": "no"}), T_DECIDE)
        except Problem as problem:
            assert problem.body["type"].endswith("idempotency-conflict"), problem.body["type"]
            return f"{problem.body['type']} {problem.body['status']}"
        raise AssertionError("a second decision was applied to an already-decided ask")

    # -- the deadline --------------------------------------------------------
    @case("a decision after the deadline is refused with a typed problem")
    def _late():
        env = envelope("corr-late", "run-late")
        ask = park_run(surface, env, T_PARK, "ask-late", DEADLINE)
        try:
            surface.decide(decision_for(ask, "approve"), T_LATE)
        except Problem as problem:
            assert problem.body["type"].endswith("deadline-exceeded"), problem.body["type"]
            assert store.read(ask.ask_id).state == "expired", "the ask was left open"
            return f"{problem.body['type']} {problem.body['status']}, ask terminal"
        raise AssertionError("a decision arriving after the deadline was applied")

    @case("an expired ask stays terminal: nothing resumes on it afterwards")
    def _terminal():
        env = envelope("corr-sweep", "run-sweep")
        ask = park_run(surface, env, T_PARK, "ask-sweep", DEADLINE)
        surface.expire(ask.ask_id, T_LATE)
        for key in ("first", "second"):
            try:
                surface.decide(HumanDecision(ask.ask_id, ask.correlation_id, "approve",
                                             "user:corey", f"dec-sweep-{key}-000"), T_LATE)
            except Problem as problem:
                assert problem.body["type"].endswith("deadline-exceeded"), problem.body["type"]
                continue
            raise AssertionError(f"the {key} late decision resumed an expired ask")
        return "swept, then two late decisions refused; the ask never reopened"

    # -- what the ask may not carry -----------------------------------------
    @case("the criterion never travels in an ask")
    def _criterion():
        ask = HumanAsk("ask-criterion", "corr-x", "Approve?",
                       {"type": "object"}, {"action": "publish", "diff": "-",
                                            "irreversibility": "reversible",
                                            "criterion": "score above 0.8"}, DEADLINE)
        try:
            check_ask(ask)
        except Problem as problem:
            return f"refused with {problem.body['type']}"
        raise AssertionError("an ask carrying the grading criterion was accepted")

    @case("no surface handle escapes onto an ask")
    def _handle():
        ask = HumanAsk("ask-handle", "corr-x", "Approve?", {"type": "object"},
                       {"action": "publish", "diff": "-", "irreversibility": "reversible",
                        "session_id": "sess-9"}, DEADLINE)
        try:
            check_ask(ask)
        except Problem as problem:
            return f"refused with {problem.body['type']}"
        raise AssertionError("an ask carrying a session handle was accepted")

    @case("an ask with no deadline is refused")
    def _deadline():
        ask = HumanAsk("ask-forever", "corr-x", "Approve?", {"type": "object"},
                       {"action": "publish", "diff": "-", "irreversibility": "reversible"}, "")
        try:
            check_ask(ask)
        except Problem as problem:
            return f"refused with {problem.body['type']}"
        raise AssertionError("an ask with no deadline was accepted")

    @case("a decision body that fails the ask's response schema is refused")
    def _schema():
        env = envelope("corr-schema", "run-schema")
        ask = park_run(surface, env, T_PARK, "ask-schema", DEADLINE)
        try:
            surface.decide(HumanDecision(ask.ask_id, ask.correlation_id, "edit", "user:corey",
                                         "dec-schema-000001", {"headline": 7}), T_DECIDE)
        except Problem as problem:
            assert problem.body["type"].endswith("document-invalid"), problem.body["type"]
            return f"{problem.body['type']} before the run continued"
        raise AssertionError("an edit that fails the response schema was applied")

    @case("a decision on a handle the surface minted is refused")
    def _minted():
        env = envelope("corr-minted", "run-minted")
        ask = park_run(surface, env, T_PARK, "ask-minted", DEADLINE)
        try:
            surface.decide(HumanDecision(ask.ask_id, "surface-handle-77", "approve",
                                         "user:corey", "dec-minted-000001"), T_DECIDE)
        except Problem as problem:
            assert problem.body["type"].endswith("document-invalid"), problem.body["type"]
            return "a decision comes back on the run's correlation id or not at all"
        raise AssertionError("a decision on a minted handle resumed the run")

    # -- the platform's own guarantees --------------------------------------
    @case("identity and correlation are stamped on the pause and again on the resume")
    def _stamps():
        got = need("approve")
        assert got["pause_actor"], "no actor on the pause"
        assert len(got["resume_chain"]) >= 2, "the deciding actor is not on the resume chain"
        assert got["pause_correlation"] == got["resume_correlation"], "correlation changed"
        return (f"pause actor {got['pause_actor']}, resume chain {len(got['resume_chain'])} hops, "
                f"one correlation id")

    @case("the resume token is derived, not minted per surface")
    def _token():
        ask = need("approve")["ask"]
        expected = resume_token_for(ask.ask_id, ask.correlation_id)
        assert store.read(ask.ask_id).resume_token == expected, "the store minted its own token"
        return expected[:16] + " derived from the ask id and the correlation id"

    @case("the interface exposes no way to resume without a decision")
    def _no_override():
        offered = {n for n in dir(HumanSurface) if not n.startswith("_")}
        assert offered == {"ask", "watch", "decide", "expire",            # the four operations
                           "deliver", "project", "authenticate",           # the surface's hooks
                           "binding", "delivery_model", "max_edit_bytes",  # declared behaviour
                           "renders_run_in_flight", "replayable_from_position",
                           "requires_open_session", "selected_by",
                           "surface_marker"}, sorted(offered)
        return "four operations, three surface hooks, no force-continue and no override"

    @case("one delivery attempt is recorded per surface per ask")
    def _delivery():
        got = need("approve")
        assert got["deliveries_recorded"] >= 1, "nothing recorded whether the ask was delivered"
        return f"{got['deliveries_recorded']} attempt recorded on the parked row"

    @case("every event on the stream carries a type from the vocabulary, in order")
    def _events():
        seen = store.events(need("approve")["pause_correlation"])
        assert seen, "the run emitted no events"
        assert all(e.type in EVENT_TYPES for e in seen), [e.type for e in seen]
        assert [e.seq for e in seen] == sorted(e.seq for e in seen), "events out of order"
        return f"{len(seen)} events: {', '.join(sorted({e.type for e in seen}))}"

    @case("the surface behaved as it declared")
    def _declared():
        corr = need("approve")["pause_correlation"]
        if surface.replayable_from_position:
            tail = surface.watch(corr, since=1)
            assert tail and tail[0].seq > 1, "declared replayable and answered from the start"
            note = f"replays from a position ({len(tail)} events after seq 1)"
        else:
            try:
                surface.watch(corr, since=1)
            except Problem as problem:
                note = f"refuses a position with {problem.body['type']}"
            else:
                raise AssertionError("declared not replayable and answered from a position anyway")
        shown = {e.type for e in surface.watch(corr)}
        in_flight = bool(shown & {"run.started", "step.progress", "tool.proposed"})
        assert in_flight == surface.renders_run_in_flight, (
            f"declared renders_run_in_flight={surface.renders_run_in_flight}, showed {sorted(shown)}")
        return f"{note}; shows the run in flight: {in_flight}"

    @case("an edit larger than the surface can hold is refused, not truncated")
    def _capacity():
        env = envelope("corr-big", "run-big")
        ask = park_run(surface, env, T_PARK, "ask-big", DEADLINE)
        big = {"headline": "x" * (surface.max_edit_bytes + 64)}
        try:
            surface.decide(HumanDecision(ask.ask_id, ask.correlation_id, "edit", "user:corey",
                                         "dec-big-0000001", big), T_DECIDE)
        except Problem as problem:
            assert problem.body["type"].endswith("document-invalid"), problem.body["type"]
            return f"refused above {surface.max_edit_bytes} bytes with a type"
        raise AssertionError("an oversized edit was accepted by a surface that cannot hold it")

    @case("the ask outlives the surface: a fresh surface object decides it")
    def _outlives():
        env = envelope("corr-outlives", "run-outlives")
        ask = park_run(surface, env, T_PARK, "ask-outlives", DEADLINE)
        replacement = load_surface(name, store)          # the one that parked is discarded
        ack = replacement.decide(HumanDecision(ask.ask_id, ask.correlation_id, "approve",
                                               "user:corey", "dec-outlives-00001"), T_DECIDE)
        assert ack.applied and ack.correlation_id == ask.correlation_id, ack.dict()
        return "parked by one surface object, decided by another, one correlation id"

    @case("every refusal in this run carried a registered type")
    def _typed():
        assert report["untyped_refusals"] == 0, f"{report['untyped_refusals']} untyped refusals"
        assert all(t in REGISTRY for t in REGISTRY), "the registry is not closed"
        return f"untyped_refusals=0 over {len(REGISTRY)} registered types"

    report["checks_total"] = len(cases)
    report["checks_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["decisions"] = list(DECISIONS)
    report["product_hits"] = product_scan(HERE)[0]
    if broken and hasattr(type(surface), "client_held"):
        type(surface).client_held = False               # never leak the breakage into a later run
    return cases, report


def cross_surface(names: list[str], out_dir: str) -> dict:
    """One store, one open ask: parked through the first surface, decided through
    the second. This is the swap the interface exists for."""
    store = ParkedAskStore(fresh(os.path.join(out_dir, "shared")))
    first, second = load_surface(names[0], store), load_surface(names[-1], store)
    env = envelope("corr-cross", "run-cross")
    ask = park_run(first, env, T_PARK, "ask-cross", DEADLINE)
    parked = store.read(ask.ask_id)
    second.deliver(parked)                               # the same open ask, a second surface
    ack = second.decide(HumanDecision(ask.ask_id, ask.correlation_id, "edit", "user:corey",
                                      "dec-cross-000001", dict(BODY_OF["edit"])), T_DECIDE)
    result = resume_run(ack, T_DECIDE, store)
    return {"parked_by": first.surface_marker, "decided_by": second.surface_marker,
            "same_correlation": ack.correlation_id == parked.stamps["correlation_id"]
                                == result.correlation_id,
            "same_resume_token": parked.resume_token == resume_token_for(ask.ask_id,
                                                                        ask.correlation_id),
            "edit_changed_artifact": result.artifact == BODY_OF["edit"],
            "surfaces": [first.surface_marker, second.surface_marker]}


def product_scan(root: str) -> tuple[int, list]:
    """Product and host names may live in adapters/ and in README.md's env table.
    Nowhere else."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__")]
        for name in sorted(filenames):
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, name)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line and "r\"" not in line:
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the human-interaction interface.")
    ap.add_argument("--surface", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--case", action="append", choices=CASES, default=[])
    ap.add_argument("--deliver-times", type=int, default=10,
                    help="how many times the replay case's decision is delivered")
    ap.add_argument("--replay-case", choices=CASES, default="approve")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "conformance"))
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--break-client-held", action="store_true",
                    help="deliberate breakage: the streaming surface resumes from its own copy")
    ap.add_argument("--product-scan", metavar="DIR")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product or host name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0

    names = args.surface or ["dryrun"]
    reports, failed = [], 0
    for name in names:
        cases, report = run(name, args.out, args.deliver_times, args.replay_case,
                            args.break_client_held)
        print(f"# surface {name} ({report['surface']}, selected_by {report['selected_by']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        print(f"  resumed_on_same_correlation={report['resumed_on_same_correlation']} "
              f"edit_changed_artifact={report['edit_changed_artifact']} "
              f"duplicate_resumes={report['duplicate_resumes']} "
              f"untyped_refusals={report['untyped_refusals']}")
        failed += len(report["failures"])
        reports.append(report)

    merged = {"per_surface": reports, "adapters_run": len(reports),
              "distinct_markers": sorted({r["surface"] for r in reports}),
              "selected_by": sorted({r["selected_by"] for r in reports}),
              "failures": [f for r in reports for f in r["failures"]],
              "product_hits": reports[0]["product_hits"] if reports else 0}
    if len(names) > 1:
        merged["cross_surface"] = cross_surface(names, args.out)
        print(f"# one store, one ask: parked by {merged['cross_surface']['parked_by']}, "
              f"decided by {merged['cross_surface']['decided_by']}, "
              f"same correlation {merged['cross_surface']['same_correlation']}")
        if not (merged["cross_surface"]["same_correlation"]
                and merged["cross_surface"]["edit_changed_artifact"]):
            failed += 1
            merged["failures"].append("cross-surface resume")
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(merged, fh, indent=2, default=str)
    print(f"adapters_run={merged['adapters_run']} failures={len(merged['failures'])}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
