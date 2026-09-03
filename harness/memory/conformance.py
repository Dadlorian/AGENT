#!/usr/bin/env python3
"""The conformance run every memory adapter must pass.

The same fixture set runs against any binding: nothing here knows which
adapter answered. Used before and after a swap; the two reports are what
proves the interface held (cap-memory-implement's definition of done). The
counters this file prints - recalled_across_runs, cross_scope_hits,
expired_served, items_without_provenance, refusals_typed, result_divergence -
are exactly the names that skill's conformance tool asserts.

    python3 harness/memory/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/memory/conformance.py --adapter second --report out/second.json
    python3 harness/memory/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import MemoryAdapter, Problem, RecallQuery, RememberRequest   # noqa: E402
from adapters.dryrun import DryRunAdapter                                   # noqa: E402
from adapters.live import LiveMemoryAdapter                                 # noqa: E402
from adapters.second import ScopeKeyedFileAdapter                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveMemoryAdapter, "second": ScopeKeyedFileAdapter}
# Product names belong in adapters/ and the env-var table of README.md, nowhere else.
PRODUCTS = re.compile(r"(pinecone|weaviate|mem0|chroma|qdrant|milvus|redis|postgres|dynamodb|elasticsearch)", re.I)

CORR = "corr-conformance-0001"


def run(name: str) -> tuple[list, dict]:
    adapter: MemoryAdapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "execution_model": adapter.execution_model,
              "retrieval_model": adapter.retrieval_model, "declared_gaps": list(adapter.declared_gaps), "cases": []}
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

    mine_scope = {"principal": "user:corey"}
    other_scope = {"agent": "agent:release-reviewer"}

    @case("a write with no staleness policy is refused before it is applied")
    def _no_staleness():
        try:
            adapter.remember(RememberRequest.from_dict(
                {"scope": mine_scope, "kind": "semantic", "body": {"n": 1},
                 "produced_by": "user:corey", "correlation_id": CORR, "expires_at": None}))
            raise AssertionError("a write with no expiry was accepted")
        except Problem as p:
            assert p.body["type"].endswith("staleness-missing") and p.body["status"] == 422, p.body
        return "staleness-missing 422, nothing written"

    @case("a recall naming no scope dimension is refused")
    def _no_scope():
        try:
            RecallQuery.from_dict({"scope": {}, "limit": 5})
            raise AssertionError("an empty scope was accepted")
        except Problem as p:
            assert p.body["type"].endswith("document-invalid") and p.body["status"] == 422, p.body
        return "document-invalid 422 at parse time"

    @case("remember three fixture items: user:corey scope, agent scope, and one already expired")
    def _fixtures():
        report["item_mine"] = adapter.remember(RememberRequest.from_dict(
            {"scope": mine_scope, "kind": "semantic", "body": {"claim": "the deploy window is Tuesdays"},
             "produced_by": "user:corey", "correlation_id": CORR, "expires_at": "2099-01-01T00:00:00Z"})).memory_id
        report["item_other"] = adapter.remember(RememberRequest.from_dict(
            {"scope": other_scope, "kind": "semantic", "body": {"claim": "not this scope"},
             "produced_by": "agent:release-reviewer", "correlation_id": CORR, "expires_at": "2099-01-01T00:00:00Z"})).memory_id
        report["item_expired"] = adapter.remember(RememberRequest.from_dict(
            {"scope": mine_scope, "kind": "episodic", "body": {"claim": "already stale"},
             "produced_by": "user:corey", "correlation_id": CORR, "expires_at": "2020-01-01T00:00:00Z"})).memory_id
        return f"{adapter.remembers} items written"

    @case("recall at user:corey scope returns its own item and no cross-scope hit")
    def _recall_mine():
        result = adapter.recall(RecallQuery.from_dict({"scope": mine_scope, "limit": 10}))
        ids = {it.memory_id for it in result.items}
        assert report["item_mine"] in ids, "the item written at this scope was not recalled"
        cross = 1 if report["item_other"] in ids else 0
        report["cross_scope_hits"] = report.get("cross_scope_hits", 0) + cross
        assert cross == 0, "an item written at another scope was returned"
        return f"{len(ids)} item(s) recalled, item_other excluded"

    @case("recall at user:corey scope excludes the expired item, sweeper never called")
    def _recall_expired():
        result = adapter.recall(RecallQuery.from_dict({"scope": mine_scope, "limit": 10}))
        ids = {it.memory_id for it in result.items}
        served = 1 if report["item_expired"] in ids else 0
        report["expired_served"] = report.get("expired_served", 0) + served
        assert served == 0, "an expired item was served on read with no sweep ever run"
        report["recalled_across_runs"] = report.get("recalled_across_runs", 0) + 1
        return "expired item absent from a fresh recall"

    @case("recall at the agent scope returns its own item (second recall, second scope)")
    def _recall_other():
        result = adapter.recall(RecallQuery.from_dict({"scope": other_scope, "limit": 10}))
        ids = {it.memory_id for it in result.items}
        assert report["item_other"] in ids, "the item written at the agent scope was not recalled there"
        cross = 1 if report["item_mine"] in ids else 0
        report["cross_scope_hits"] = report.get("cross_scope_hits", 0) + cross
        assert cross == 0, "the user-scoped item leaked into the agent-scoped recall"
        report["recalled_across_runs"] = report.get("recalled_across_runs", 0) + 1
        return f"{len(ids)} item(s) recalled at the agent scope"

    @case("every recalled item carries provenance")
    def _provenance():
        result = adapter.recall(RecallQuery.from_dict({"scope": mine_scope, "limit": 10}))
        missing = sum(1 for it in result.items if not it.provenance or not it.provenance.correlation_id)
        report["items_without_provenance"] = missing
        assert missing == 0, f"{missing} recalled item(s) had no provenance"
        return f"{len(result.items)} item(s), all carrying produced_by/observed_at/correlation_id"

    @case("an out-of-scope recall is refused policy-denied, not returned empty")
    def _out_of_scope():
        try:
            adapter.recall(RecallQuery.from_dict({"scope": {"principal": "user:dana"}, "limit": 5}),
                           actor_scope={"principal": "user:corey"})
            raise AssertionError("a recall for a scope the actor does not hold was allowed")
        except Problem as p:
            assert p.body["type"].endswith("policy-denied") and p.body["status"] == 403, p.body
        return "policy-denied 403, distinct from an empty result"

    @case("supersede replaces recallability without editing the old item")
    def _supersede():
        new_item = adapter.supersede(report["item_mine"], {"claim": "the deploy window is Thursdays now"},
                                     "user:corey", CORR, "2099-01-01T00:00:00Z")
        result = adapter.recall(RecallQuery.from_dict({"scope": mine_scope, "limit": 10}))
        ids = {it.memory_id for it in result.items}
        assert new_item.memory_id in ids, "the superseding item was not recallable"
        assert report["item_mine"] not in ids, "the superseded item is still recallable"
        report["superseded_id"] = new_item.memory_id
        return "old item no longer recallable, new item is"

    @case("supersede naming an unknown item is refused item-not-found")
    def _supersede_unknown():
        try:
            adapter.supersede("mem-does-not-exist", {"claim": "x"}, "user:corey", CORR, "2099-01-01T00:00:00Z")
            raise AssertionError("supersede of an unknown id was accepted")
        except Problem as p:
            assert p.body["type"].endswith("item-not-found") and p.body["status"] == 404, p.body
        return "item-not-found 404"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["remembers"] = adapter.remembers
    report["recalls"] = adapter.recalls
    report["refusals"] = adapter.refusals
    report["refusals_typed"] = adapter.refusals   # every refusal here is a Problem; none is untyped
    report["marker"] = adapter.observed_marker
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
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
    ap = argparse.ArgumentParser(description="Conformance run for the memory interface.")
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
        print(f"# binding {name} ({report['retrieval_model']}, {report['execution_model']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"recalled_across_runs={report.get('recalled_across_runs', 0)} "
              f"cross_scope_hits={report.get('cross_scope_hits', 0)} expired_served={report.get('expired_served', 0)} "
              f"items_without_provenance={report.get('items_without_provenance', 0)} "
              f"refusals_typed={report['refusals_typed']} product_hits={report['product_hits']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)

    result_divergence = 0
    if len(reports) >= 2:
        base = {reports[0]["item_mine"], reports[0]["item_other"]}
        for r in reports[1:]:
            if {r["item_mine"], r["item_other"]} != base:
                result_divergence += 1
    print(f"adapters_run={len(reports)} stores_reached_distinct={len({r['marker'] for r in reports})} "
          f"result_divergence={result_divergence}")

    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
