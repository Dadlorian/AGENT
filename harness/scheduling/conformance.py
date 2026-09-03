#!/usr/bin/env python3
"""The conformance run every scheduling adapter must pass.

Two kinds of case run here: the ordinary adapter cases (declare, fire, replay,
refuse) run against whichever binding --adapter names, same shape as every
other harness's conformance run; and the vector corpus, which runs against
the shared pure evaluator directly (cap-scheduling-implement: occurrences is
served by the same evaluator on every binding, so running the corpus once per
binding would only prove the wiring, not the math -- the corpus is what
proves the math). --vectors runs the corpus and prints the
RecurrenceConformanceReport shape cap-scheduling-implement's definition_of_done
asserts against (T-t9-06, F-b1-04).

    python3 harness/scheduling/conformance.py --adapter dryrun --report out/before.json
    python3 harness/scheduling/conformance.py --adapter second --report out/after.json
    python3 harness/scheduling/conformance.py --vectors --adapter dryrun --adapter second --report out/vectors.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (ConformanceReport, Problem, ScheduleDeclaration,  # noqa: E402
                       SchedulingAdapter, idempotency_key, occurrences, parse_rule)
from adapters.dryrun import DryRunAdapter                                # noqa: E402
from adapters.live import EngineOwnedScheduleAdapter                     # noqa: E402
from adapters.second import TickerQueueAdapter                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": EngineOwnedScheduleAdapter, "second": TickerQueueAdapter}
VECTOR_CORPUS = os.path.join(HERE, "tests", "vectors", "rfc5545", "vectors.json")
CORPUS_CLASSES = {"dst_forward", "dst_back", "leap_day", "bysetpos"}


def unit(unit_ref="nightly-sweep", rule="FREQ=DAILY;BYHOUR=2;BYMINUTE=0",
        starts_at="2026-01-01T02:00:00", tzname="UTC", catch_up="skip") -> dict:
    return {"unit_ref": unit_ref, "recurrence": rule, "starts_at": starts_at,
            "timezone": tzname, "catch_up": catch_up}


def refused(fn, want_type: str, **kw) -> dict:
    try:
        fn(**kw)
    except Problem as problem:
        return problem.body
    raise AssertionError(f"expected {want_type}, got a result")


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "adapter_name": adapter.adapter_name,
              "selected_by": adapter.selected_by, "declared_gaps": list(adapter.declared_gaps), "cases": []}
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

    live = name == "live"

    @case("occurrences is a pure function, testable from a table with no adapter reached")
    def _pure():
        oc = occurrences("FREQ=DAILY;COUNT=3", "2026-01-01T09:00:00", "UTC",
                         "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z")
        assert oc.occurrences == ["2026-01-01T09:00:00Z", "2026-01-02T09:00:00Z", "2026-01-03T09:00:00Z"], oc.occurrences
        assert oc.truncated is False
        return f"{len(oc.occurrences)} occurrences, no clock read, no adapter touched"

    @case("declare then fire produces the standard entry envelope")
    def _declare_fire():
        if live:
            return refused(adapter.declare, "adapter-unavailable", doc=unit())["type"] + " (no server here; skips to the refusal case below)"
        decl = adapter.declare(unit())
        envelope = adapter.fire(decl.unit_ref, decl.starts_at)
        for field in ("envelope_version", "kind", "entry_id", "occurred_at", "actor", "intent",
                     "correlation", "budget", "idempotency_key", "payload"):
            assert field in envelope, f"envelope missing {field}"
        assert envelope["kind"] == "schedule", envelope["kind"]
        assert envelope["idempotency_key"] == idempotency_key(decl.unit_ref, decl.starts_at)
        return f"kind={envelope['kind']} idempotency_key={envelope['idempotency_key'][:16]}..."

    @case("a replay with the same key is free: the same envelope, no second fire")
    def _replay():
        if live:
            return refused(adapter.declare, "adapter-unavailable", doc=unit())["type"] + " (no server here)"
        decl = adapter.declare(unit(unit_ref="replay-unit"))
        before = adapter.fired
        first = adapter.fire(decl.unit_ref, decl.starts_at)
        second = adapter.fire(decl.unit_ref, decl.starts_at)
        assert first == second, "a replay produced a different envelope"
        assert adapter.fired == before + 1, "a replay incremented the fired counter"
        return f"fired={adapter.fired}, one envelope reused across two fire() calls"

    @case("a malformed rule is refused before any adapter state changes")
    def _malformed():
        before = adapter.declared
        body = refused(adapter.declare, "document-invalid", doc=unit(rule="not-a-rule"))
        assert body["status"] == 422, body
        assert adapter.declared == before, "the malformed rule still counted as declared"
        return f"{body['type']} 422, declared unchanged at {adapter.declared}"

    @case("catch_up outside the three-value vocabulary is refused")
    def _bad_catchup():
        body = refused(adapter.declare, "document-invalid", doc=unit(catch_up="whenever"))
        assert body["status"] == 422, body
        return f"{body['type']} 422"

    @case("firing an undeclared unit is refused, never silently accepted")
    def _undeclared_fire():
        body = refused(adapter.fire, "document-invalid", unit_ref="never-declared", occurrence_instant="2026-01-01T00:00:00Z")
        assert body["status"] == 422, body
        return f"{body['type']} 422"

    @case("a rule part outside RFC 5545 is refused, distinct from a malformed string")
    def _unsupported_grammar():
        body = refused(adapter.declare, "unsupported-rule-part", doc=unit(rule="FREQ=SECONDLY"))
        assert body["type"].endswith("unsupported-rule-part"), body
        assert "unsupported_parts" in body, body
        return f"{body['type']} 422 unsupported_parts={body['unsupported_parts']}"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["declared"] = adapter.declared
    report["fired"] = adapter.fired
    report["refused"] = adapter.refused
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def vector_report(name: str, vectors: list[dict]) -> ConformanceReport:
    adapter = ADAPTERS[name]()
    mismatches = 0
    covers = set()
    unsupported = set()
    for v in vectors:
        try:
            oc = adapter.occurrences(v["rule"], v["starts_at"], v["timezone"], v["window"]["from"], v["window"]["to"])
        except Problem as problem:
            unsupported.update(problem.body.get("unsupported_parts", []))
            mismatches += 1
            continue
        if oc.occurrences != v["expected"]:
            mismatches += 1
        else:
            covers.add(v["class"])
    return ConformanceReport(adapter=adapter.adapter_name, selected_by=adapter.selected_by,
                             vectors_run=len(vectors), mismatches=mismatches,
                             corpus_covers=sorted(covers & CORPUS_CLASSES),
                             unsupported_parts=sorted(unsupported))


def product_scan(root: str) -> tuple[int, list]:
    """Product names live in adapters/ and README's env table. Nowhere else."""
    import re
    products = re.compile(r"(temporal|litellm|openrouter|gemini|sglang|vllm|openai|anthropic|firecracker|langfuse)", re.I)
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__", "tests")]
        for name in sorted(filenames):
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, name)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = products.search(line)
                if found and "products = " not in line.lower():
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the scheduling interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--vectors", action="store_true", help="run the RFC 5545 vector corpus instead of the case suite")
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0

    if args.vectors:
        corpus = json.load(open(VECTOR_CORPUS))["vectors"]
        reports, failures = [], 0
        for name in args.adapter or ["dryrun"]:
            r = vector_report(name, corpus)
            missing = CORPUS_CLASSES - set(r.corpus_covers)
            ok = r.mismatches == 0 and r.vectors_run > 40 and not missing
            failures += 0 if ok else 1
            print(f"# adapter {r.adapter} vectors_run={r.vectors_run} mismatches={r.mismatches} "
                  f"corpus_covers={r.corpus_covers} unsupported_parts={r.unsupported_parts}")
            reports.append(r.as_dict())
        if reports:
            adapters_run = len(reports)
            for r in reports:
                r["adapters_run"] = adapters_run
        if args.report:
            os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
            with open(args.report, "w") as fh:
                json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
        print(f"conformance {'PASSED' if not failures else 'FAILED'} (vectors): {len(reports)} binding(s)")
        return 1 if failures else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        print(f"# binding {name} ({report['adapter_name']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"declared={report['declared']} fired={report['fired']} refused={report['refused']} "
              f"product_hits={report['product_hits']}")
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
