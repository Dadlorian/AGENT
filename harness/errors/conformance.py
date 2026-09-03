#!/usr/bin/env python3
"""The conformance run every errors adapter must pass.

The same cases run against any binding: nothing here knows which adapter
answered, except the two cases that read execution_model, which is exactly
the axis the second adapter must differ on (F-b1-04). Used before and after
a swap; the two reports are what proves the interface held (T-t9-06).

    python3 harness/errors/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/errors/conformance.py --adapter second --report out/second.json
    python3 harness/errors/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (MEDIA_TYPE, PROBLEM_BASE, REGISTRY, ErrorsAdapter,   # noqa: E402
                       Problem, ProblemException, UnregisteredType, construct)
from adapters.dryrun import DryRunAdapter                                    # noqa: E402
from adapters.live import LiveProblemFactory                                 # noqa: E402
from adapters.second import EdgeFilterAdapter                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveProblemFactory, "second": EdgeFilterAdapter}
# Product names would live in adapters/ and README.md's env table. None exist for this
# capability (PASS.md B3: *absent*), so this scan only guards against one appearing later.
PRODUCTS = re.compile(r"(litellm|openrouter|gemini|sglang|vllm|openai|anthropic|cursor|goose|firecracker|temporal|langfuse)", re.I)


def raised(adapter: ErrorsAdapter, suffix: str, detail: str, want_type: str, **kw) -> dict:
    before = adapter.responses_checked
    try:
        adapter.raise_problem(suffix, detail, "corr-conformance", **kw)
    except ProblemException as exc:
        body = dict(exc.problem.body())
        body["_responses_checked_delta"] = adapter.responses_checked - before
        return body
    raise AssertionError(f"expected {want_type}, but raise_problem returned instead of raising")


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "execution_model": adapter.execution_model,
              "declared_gaps": list(adapter.declared_gaps), "cases": []}
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except ProblemException as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.problem.type} - {exc.problem.detail}"))
            return fn
        return wrap

    @case("one typed problem for a registry refusal")
    def _happy():
        body = raised(adapter, "budget-exhausted", "the call would cross the ceiling", "budget-exhausted")
        assert body["type"] == PROBLEM_BASE + "budget-exhausted", body["type"]
        assert body["status"] == 402 and body["retryable"] is False, body
        assert body["correlation_id"] == "corr-conformance", "the correlation stamp did not survive"
        return f"{body['type']} {body['status']} retryable={body['retryable']}"

    @case("every registry row constructs and carries its declared media type")
    def _every_row():
        for suffix, (status, _title, retryable, declared) in REGISTRY.items():
            ext = {m: (1 if m == "retry_after_s" else "r-1" if m == "rule_id" else "timeout")
                   for m in declared if m != "causes"}
            body = raised(adapter, suffix, f"exercising {suffix}", suffix, **ext)
            assert body["status"] == status and body["retryable"] is retryable, (suffix, body)
        return f"{len(REGISTRY)} registry rows constructed, each with its declared status and retryable"

    @case("retry_advice reads the member, never the message")
    def _retry_from_type():
        retry_body = raised(adapter, "deadline-exceeded", "no useful words here at all", "deadline-exceeded",
                            retry_after_s=7)
        no_retry_body = raised(adapter, "policy-denied", "no useful words here at all", "policy-denied",
                               rule_id="r-1")
        assert retry_body["retryable"] is True and retry_body["retry_after_s"] == 7, retry_body
        assert no_retry_body["retryable"] is False, no_retry_body
        assert retry_body["detail"] == no_retry_body["detail"], "the two details were made identical on purpose"
        return "identical detail text, opposite retry advice, read from retryable and retry_after_s alone"

    @case("a type with no row in the closed registry is refused at construction")
    def _unregistered():
        before = adapter.responses_checked
        try:
            adapter.raise_problem("not-a-registered-type", "should never reach a body")
            raise AssertionError("construction succeeded for an unregistered suffix")
        except UnregisteredType:
            pass
        assert adapter.responses_checked == before, "an unregistered suffix was still counted as a response"
        return "UnregisteredType raised, no response counted, no body ever built"

    @case("an extension member the row does not declare is refused")
    def _undeclared_ext():
        try:
            adapter.raise_problem("identity-untrusted", "d", rule_id="r-1")
            raise AssertionError("construction succeeded with an undeclared extension member")
        except UnregisteredType:
            pass
        return "rule_id is not declared for identity-untrusted; construction refused"

    @case("chain appends the inner problem, innermost last")
    def _chain():
        outer = construct("adapter-unavailable", "outer", retry_after_s=5)
        inner = construct("deadline-exceeded", "inner", retry_after_s=1)
        chained = adapter.chain(outer, inner)
        assert chained.causes == (inner,), chained.causes
        assert chained.body()["causes"][-1]["type"] == inner.type, "innermost is not last"
        return f"causes=[{chained.causes[0].suffix()}], innermost last"

    @case("an untyped failure is converted, counted, and never crashes the caller")
    def _classify_untyped():
        before = adapter.untyped
        if adapter.execution_model == "in-process":
            try:
                raise RuntimeError("a fault this raise site never mapped to a registry row")
            except RuntimeError as exc:
                problem = adapter.classify(exc)
        else:
            problem = adapter.classify({"status": 500, "media_type": "text/plain", "body": "internal error"})
        assert problem.type == PROBLEM_BASE + "adapter-unavailable", problem.type
        assert adapter.untyped == before + 1, "the untyped counter did not increment"
        return f"classified to {problem.type}, untyped={adapter.untyped}"

    @case("the edge adapter's own failure path: wrong media type is counted")
    def _wrong_media_type():
        edge = EdgeFilterAdapter()
        problem = edge.classify({"status": 500, "media_type": "text/plain", "body": "boom"})
        assert problem.type == PROBLEM_BASE + "adapter-unavailable", problem.type
        assert edge.wrong_media_type == 1 and edge.untyped == 1, (edge.wrong_media_type, edge.untyped)
        return "text/plain body counted as untyped and wrong_media_type, never forwarded unchanged"

    @case("byte-identical problem bodies from both adapters")
    def _byte_identical():
        origin = DryRunAdapter()
        try:
            origin.raise_problem("policy-denied", "a deterministic pre-execution refusal",
                                 "corr-byte-identical", rule_id="r-budget-cap")
            raise AssertionError("expected a raise")
        except ProblemException as exc:
            body_a = exc.problem.body()
        edge = EdgeFilterAdapter()
        reshaped = edge.classify({"status": body_a["status"], "media_type": MEDIA_TYPE, "body": body_a})
        assert reshaped.canonical() == json.dumps(body_a, sort_keys=True, separators=(",", ":")).encode(), \
            "the edge adapter changed a body it should only have reshaped"
        return f"{len(body_a)} members, canonical JSON identical byte for byte across both adapters"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["responses_checked"] = adapter.responses_checked
    report["untyped"] = adapter.untyped
    report["unregistered_types"] = adapter.unregistered_types
    report["wrong_media_type"] = adapter.wrong_media_type
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
    """No product name should appear anywhere in this harness (PASS.md B3: absent)."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("out", "__pycache__")]
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
    ap = argparse.ArgumentParser(description="Conformance run for the errors interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name in this harness")
        print(f"product_hits={count}")
        return 1 if count else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        print(f"# binding {name} ({report['execution_model']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"responses_checked={report['responses_checked']} untyped={report['untyped']} "
              f"unregistered_types={report['unregistered_types']} wrong_media_type={report['wrong_media_type']} "
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
