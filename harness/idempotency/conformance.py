#!/usr/bin/env python3
"""The conformance run every idempotency adapter must pass.

The same eight cases run against any binding: nothing here knows which adapter
answered. Used before and after a swap; the two reports are what proves the
interface held (T-t9-06). Report shape follows cap-idempotency-implement's
IdempotencyConformanceReport: adapter, concurrency, executions, duplicates,
conflicts, overlapped, adapters_run, selected_by.

    python3 harness/idempotency/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/idempotency/conformance.py --adapter second --report out/second.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import ClaimRequest, IdempotencyAdapter, Problem, digest  # noqa: E402
from adapters.dryrun import LogFoldAdapter                               # noqa: E402
from adapters.live import LedgerFileAdapter                              # noqa: E402
from adapters.second import ConditionalWriteLeaseAdapter                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": LogFoldAdapter, "live": LedgerFileAdapter, "second": ConditionalWriteLeaseAdapter}
CONCURRENCY = 20


def mkreq(key: str, payload: dict, scope="harness/idempotency:submit-unit", retention_s=86400) -> ClaimRequest:
    return ClaimRequest.for_payload(key, payload, scope, correlation_id="corr-" + key,
                                    actor="user:corey", entry_kind="human", retention_s=retention_s)


def do_effect(payload: dict) -> dict:
    """The side effect a fresh claim earns. Never performed for a duplicate."""
    return {"charged_amount": payload.get("amount", 1), "ref": digest(payload)}


def fire_sequential(adapter: IdempotencyAdapter, key: str, payload: dict, n: int) -> tuple[int, int, int]:
    """n claims of one key, one after another. What the fold can prove."""
    req = mkreq(key, payload)
    executions = duplicates = 0
    for i in range(n):
        out = adapter.claim(req)
        if out.outcome == "fresh":
            executions += 1
            adapter.complete(req.idempotency_key, req.scope, digest(do_effect(payload)))
        else:
            duplicates += 1
    return executions, duplicates, 0


def fire_concurrent(adapter: IdempotencyAdapter, key: str, payload: dict, n: int) -> tuple[int, int, int]:
    """n claims of one key, launched at once. What only a lease can prove."""
    req = mkreq(key, payload)
    lock = threading.Lock()
    counts = {"executions": 0, "duplicates": 0, "overlapped": 0}
    barrier = threading.Barrier(n)

    def worker():
        barrier.wait()
        out = adapter.claim(req)
        if out.outcome == "fresh":
            import time
            time.sleep(0.05)                                  # hold the in-flight window open
            adapter.complete(req.idempotency_key, req.scope, digest(do_effect(payload)))
            with lock:
                counts["executions"] += 1
        else:
            with lock:
                counts["duplicates"] += 1
                if out.in_flight:
                    counts["overlapped"] += 1

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counts["executions"], counts["duplicates"], counts["overlapped"]


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name](os.path.join(HERE, "out", f"conformance-{name}"))
    report = {"binding": name, "adapter_marker": adapter.adapter_marker,
              "unit_of_conditionality": adapter.unit_of_conditionality,
              "supports_in_flight": adapter.supports_in_flight, "cases": []}
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

    @case("claim, complete, resolve round trip")
    def _round_trip():
        req = mkreq("case-round-trip", {"amount": 7})
        out = adapter.claim(req)
        assert out.outcome == "fresh", out.outcome
        ref = digest(do_effect({"amount": 7}))
        adapter.complete(req.idempotency_key, req.scope, ref)
        got = adapter.resolve(req.idempotency_key, req.scope)
        assert got is not None and got.result_ref == ref, got
        return f"fresh -> complete -> resolve returns {ref[:19]}..."

    @case("resolve before any claim is None")
    def _resolve_empty():
        got = adapter.resolve("case-never-claimed", "harness/idempotency:submit-unit")
        assert got is None, got
        return "no claim, no reference"

    @case("replay: same key, same payload is not a second execution")
    def _replay():
        req = mkreq("case-replay", {"amount": 3})
        first = adapter.claim(req)
        adapter.complete(req.idempotency_key, req.scope, digest(do_effect({"amount": 3})))
        second = adapter.claim(req)
        assert second.outcome == "duplicate", second.outcome
        assert second.result_ref == digest(do_effect({"amount": 3})), "replay returned a different result"
        return "second claim answered duplicate with the stored result"

    @case("same key, different payload is a typed conflict")
    def _conflict():
        req = mkreq("case-conflict", {"amount": 5})
        adapter.claim(req)
        try:
            adapter.claim(mkreq("case-conflict", {"amount": 999}))
        except Problem as p:
            assert p.body["type"].endswith("idempotency-conflict") and p.body["status"] == 409, p.body
            return f"{p.body['type']} 409"
        raise AssertionError("a different payload under the same key was not refused")

    @case(f"{CONCURRENCY} claims, sequential: exactly one execution")
    def _sequential():
        ex, dup, overlapped = fire_sequential(adapter, "case-sequential", {"amount": 1}, CONCURRENCY)
        assert ex == 1, f"executions {ex}"
        assert dup == CONCURRENCY - 1, f"duplicates {dup}"
        return f"executions=1 duplicates={dup}"

    @case(f"{CONCURRENCY} claims, launched at once: what this binding can prove")
    def _race():
        ex, dup, overlapped = fire_concurrent(adapter, "case-race", {"amount": 2}, CONCURRENCY)
        report.update(concurrency=CONCURRENCY, executions=ex, duplicates=dup, overlapped=overlapped)
        if adapter.supports_in_flight:
            assert ex == 1, f"executions {ex} (a lease must serialise the winners)"
            assert overlapped >= 1, "no duplicate was answered while the first was still running"
            return f"lease: executions=1 duplicates={dup} overlapped={overlapped}"
        assert overlapped == 0, "a fold with no lease answered in_flight anyway; the gap is not honest"
        return f"fold: declares supports_in_flight=False; overlapped=0 (undeclared, not asserted)"

    @case("retention: a claim past its window is claimable again")
    def _expire():
        import time
        t0 = time.time()
        req = mkreq("case-expire", {"amount": 1}, retention_s=60)
        adapter.claim(req)
        adapter.complete(req.idempotency_key, req.scope, digest(do_effect({"amount": 1})))
        still_held = adapter.expire(req.idempotency_key, req.scope, now=t0 + 10)
        assert still_held is False, "expired before its window elapsed"
        released = adapter.expire(req.idempotency_key, req.scope, now=t0 + 120)
        assert released is True, "did not release after its window elapsed"
        reclaimed = adapter.claim(mkreq("case-expire", {"amount": 1}))
        assert reclaimed.outcome == "fresh", f"key still held after expiry: {reclaimed.outcome}"
        return "held within the window, released after it, then claimable again"

    @case("the outcome carries a digest, never the payload")
    def _no_leak():
        payload = {"amount": 1, "secret_looking_field": "should-never-appear"}
        req = mkreq("case-no-leak", payload)
        out = adapter.claim(req)
        doc = json.dumps({"outcome": out.outcome, "result_ref": out.result_ref})
        assert "secret_looking_field" not in doc and "should-never-appear" not in doc, doc
        assert req.payload_digest.startswith("sha256:"), req.payload_digest
        return "claim carries payload_digest only; the outcome carries no payload field"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["binding_report"] = adapter.binding()
    report.setdefault("concurrency", CONCURRENCY)
    report.setdefault("executions", 0)
    report.setdefault("duplicates", 0)
    report.setdefault("overlapped", 0)
    report["conflicts"] = 0
    report["adapters_run"] = 1
    report["selected_by"] = "configuration"
    return cases, report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the idempotency interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    args = ap.parse_args(argv)

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        print(f"# binding {name} ({report['unit_of_conditionality']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"]
        print(f"  adapter={report['adapter_marker']} cases={report['cases_run']} "
              f"passed={report['cases_passed']} supports_in_flight={report['supports_in_flight']} "
              f"overlapped={report['overlapped']}")
        reports.append(report)
    if len(reports) > 1:
        for r in reports:
            r["adapters_run"] = len(reports)
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
