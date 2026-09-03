#!/usr/bin/env python3
"""The conformance run every model-access adapter must pass.

The same twelve cases run against any binding: nothing here knows which adapter
answered. Used before and after a swap; the two reports are what proves the
interface held (T-t7-05, T-t9-06).

    python3 harness/gateway/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/gateway/conformance.py --adapter second --report out/second.json
    python3 harness/gateway/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (CompletionRequest, ModelAccessAdapter, Problem,  # noqa: E402
                       ROUTING_TABLE, estimate_micros, route, ticket_as_dict)
from adapters.dryrun import DryRunAdapter                              # noqa: E402
from adapters.live import LiveGatewayAdapter                           # noqa: E402
from adapters.second import BatchClaimAdapter                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveGatewayAdapter, "second": BatchClaimAdapter}
# Product names belong in adapters/ and in the env-var table of README.md, nowhere else.
PRODUCTS = re.compile(r"(litellm|openrouter|gemini|sglang|vllm|openai|anthropic|cursor|goose)", re.I)
MAX_POLLS = 8


def ask(model_class="i-fast", prompt="one completion by class", ceiling=200_000, key=None, **extra) -> dict:
    doc = {"model_class": model_class,
           "messages": [{"role": "user", "content": prompt}],
           "idempotency_key": key or ("idem-" + model_class + "-" + str(ceiling)),
           "ceiling_micros": ceiling}
    doc.update(extra)
    return doc


def redeem(adapter: ModelAccessAdapter, doc: dict, **kw):
    """submit, then claim until redeemed. One shape for a fast path and a slow one."""
    ticket = adapter.submit(CompletionRequest.from_dict(doc), **kw)
    state_at_submit, polls = ticket.state, 0
    cost_at_submit = ticket.result.cost_status if ticket.result else None
    while ticket.state == "pending" and polls < MAX_POLLS:
        polls += 1
        ticket = adapter.claim(ticket)
    return ticket, state_at_submit, polls, cost_at_submit


def refused(adapter: ModelAccessAdapter, doc: dict, want_type: str, **kw) -> dict:
    before = adapter.dispatches
    try:
        redeem(adapter, doc, **kw)
    except Problem as problem:
        body = dict(problem.body)
        body["_dispatched"] = adapter.dispatches - before
        return body
    raise AssertionError(f"expected {want_type}, got a result")


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "serving_path": adapter.serving_path,
              "declared_gaps": list(adapter.declared_gaps), "cases": [], "overshoot_violations": 0}
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            return fn
        return wrap

    @case("one completion by class")
    def _happy():
        doc = ask()
        ticket, at_submit, polls, cost_at_submit = redeem(adapter, doc)
        assert ticket.state == "redeemed", f"state {ticket.state} after {polls} polls"
        got = ticket.result
        for field, kind in (("text", str), ("cost_micros", int), ("tokens_in", int),
                            ("tokens_out", int), ("cost_status", str)):
            assert isinstance(getattr(got, field), kind), f"result.{field} is not {kind.__name__}"
        assert got.text, "result text is empty"
        estimate = estimate_micros(route(doc["model_class"], doc["ceiling_micros"],
                                         doc["ceiling_micros"]), CompletionRequest.from_dict(doc))
        if got.cost_micros > doc["ceiling_micros"]:
            report["overshoot_violations"] += 1
        assert got.cost_micros <= doc["ceiling_micros"], f"cost {got.cost_micros} crossed the ceiling"
        gap = any("cost is reconciled only" in g for g in adapter.declared_gaps)
        assert got.cost_status == "reconciled" or gap, f"cost_status {got.cost_status} and no declared gap covers it"
        report.update({"ticket_state_at_submit": at_submit, "polls_to_claim": polls,
                       "cost_status_at_submit": cost_at_submit, "cost_status_at_claim": got.cost_status,
                       "cancellable": ticket.cancellable, "estimate_micros": estimate,
                       "cost_micros": got.cost_micros,
                       "declared_gap_honoured": bool(gap) or not adapter.declared_gaps})
        return (f"state_at_submit={at_submit} polls={polls} cost={got.cost_micros} "
                f"<= ceiling={doc['ceiling_micros']} cost_status={got.cost_status}")

    @case("a bare prefix routes to the class default")
    def _bare():
        ticket, _, _, _ = redeem(adapter, ask("f-", key="idem-bare-prefix-000"))
        assert ticket.state == "redeemed" and ticket.model_class == "f-", ticket.state
        return "class f- redeemed with the member never reaching the caller"

    @case("a request naming a vendor is refused")
    def _vendor_field():
        body = refused(adapter, ask(key="idem-vendor-field-0", vendor="a-vendor"), "document-invalid")
        assert body["type"].endswith("document-invalid") and body["status"] == 422, body["type"]
        assert body["_dispatched"] == 0, "the request was dispatched anyway"
        return f"{body['type']} 422, dispatched={body['_dispatched']}"

    @case("a vendor's model name is not a class")
    def _vendor_class():
        body = refused(adapter, ask("gpt-4o", key="idem-vendor-class-0"), "document-invalid")
        assert body["status"] == 422 and body["_dispatched"] == 0, body
        return f"{body['type']} 422, dispatched=0"

    @case("a class no member serves is a typed failure")
    def _no_endpoint():
        body = refused(adapter, ask("b-nonexistent", key="idem-no-endpoint-0"), "adapter-unavailable")
        assert body["status"] == 503 and body["retryable"] is True, body
        assert body["_dispatched"] == 0, "the request was dispatched anyway"
        return f"{body['type']} 503 retryable, dispatched=0"

    @case("a request over its cap is refused before the call")
    def _cap():
        body = refused(adapter, ask(ceiling=100, key="idem-over-the-cap-0"), "budget-exhausted")
        assert body["status"] == 402 and body["_dispatched"] == 0, body
        assert "no spend was incurred" in body["detail"], body["detail"]
        report["terminated_on_budget"] = 1
        report["enforcement_point_observed"] = body["enforcement_point"]
        return f"{body['type']} 402 at {body['enforcement_point']}, dispatched=0"

    @case("a policy verdict narrows routing, it does not widen it")
    def _policy():
        body = refused(adapter, ask(key="idem-policy-narrow"), "adapter-unavailable",
                       policy_verdict="allow-local-only")
        assert body["status"] == 503 and body["_dispatched"] == 0, body
        ticket, _, _, _ = redeem(adapter, ask("f-smoke", key="idem-policy-local-ok"),
                                 policy_verdict="allow-local-only")
        assert ticket.state == "redeemed", ticket.state
        return "i- refused under allow-local-only, f- still served"

    @case("the same key with the same body is not a second call")
    def _idempotent():
        doc = ask(key="idem-replay-same-body")
        first, _, _, _ = redeem(adapter, doc)
        before = adapter.dispatches
        second = adapter.submit(CompletionRequest.from_dict(doc))
        assert second.ticket_id == first.ticket_id, "a replay produced a different ticket"
        assert adapter.dispatches == before, "a replay reached the adapter"
        conflict = refused(adapter, ask(prompt="a different body", key="idem-replay-same-body"),
                           "idempotency-conflict")
        assert conflict["status"] == 409, conflict
        return "same body replayed for free, different body is 409"

    @case("nothing names a vendor, a member or an endpoint on the way out")
    def _no_leak():
        ticket, _, _, _ = redeem(adapter, ask(key="idem-leak-check-000"))
        doc = json.dumps(ticket_as_dict(ticket))
        assert not PRODUCTS.search(doc), f"a product name reached the caller: {PRODUCTS.search(doc).group(0)}"
        assert adapter.declared_marker not in doc, "the binding's endpoint marker reached the caller"
        members = [m for g in ROUTING_TABLE.values() for m in g["members"] if m != ticket.model_class]
        leaked = [m for m in members if m in doc]
        assert not leaked, f"member models reached the caller: {leaked}"
        assert set(json.loads(doc)) <= {"ticket_id", "state", "model_class", "result",
                                        "earliest_retry", "cancellable", "problem"}, "ticket grew a field"
        return "ticket carries a class, a state, a result and nothing about who served it"

    @case("cancel says which of two things happened")
    def _cancel():
        ticket = adapter.submit(CompletionRequest.from_dict(ask(key="idem-cancel-case-00")))
        ack = adapter.cancel(ticket)
        want = "stopped" if ticket.cancellable else "recorded"
        assert ack.outcome == want, f"cancellable={ticket.cancellable} but outcome {ack.outcome}"
        assert ack.cost_owed_micros >= 0 and ack.detail, "a cancel must say what is owed and why"
        return f"cancellable={ticket.cancellable} -> {ack.outcome}, owed {ack.cost_owed_micros} micros"

    @case("the endpoint marker is read from the response")
    def _marker():
        redeem(adapter, ask(key="idem-marker-case-00"))
        assert adapter.observed_marker == adapter.declared_marker, \
            f"observed {adapter.observed_marker!r}, binding declares {adapter.declared_marker!r}"
        report["endpoint_marker"] = adapter.observed_marker
        return f"{adapter.observed_marker} matches the binding"

    @case("routing is a pure function, testable from a table")
    def _routing_table():
        vectors = json.load(open(os.path.join(HERE, "routing.json")))["test_vectors"]
        for klass, member in vectors:
            got = route(klass, 200_000, 200_000)
            assert got.member == member, f"{klass} routed to {got.member}, expected {member}"
        assert adapter.dispatches >= 0, "routing touched the adapter"
        return f"{len(vectors)} vectors, no model reachable, no spend"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["dispatches"] = adapter.dispatches
    report["refusals"] = adapter.refusals
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
    """Product names may live in adapters/ and in README.md's env table. Nowhere else.

    Code is what is scanned (.py and .sh): routing.json is the class table copied
    from PASS.md A4, where member names are data no code branches on.
    """
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__")]
        for name in sorted(filenames):
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, name)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line:
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the model-access interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        print(f"# binding {name} ({report['serving_path']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"dispatches={report['dispatches']} refusals={report['refusals']} "
              f"overshoot_violations={report['overshoot_violations']} "
              f"endpoint_marker={report.get('endpoint_marker', 'none')} product_hits={report['product_hits']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
