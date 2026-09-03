#!/usr/bin/env python3
"""The conformance run every tenancy adapter must pass.

The same corpus of cases runs against any binding: nothing here knows
whether the boundary is a filtered column or a separate store. Used before
and after a swap; the two reports are what proves the interface held
(T-t7-05, T-t9-06). The report carries the counters xc-tenancy-implement's
definition of done names - units_checked, principals_covered,
no_principal_admitted, cross_tenant_reads, cross_tenant_recalls,
cross_tenant_spend, adapters_run - under `tenancy_conformance_report`.

    python3 harness/xc-tenancy/conformance.py --adapter dryrun --report out/before.json
    python3 harness/xc-tenancy/conformance.py --adapter second --report out/after.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import Problem, ScopeRequest, TenancyAdapter                     # noqa: E402
from adapters.dryrun import DryRunTenancyAdapter                                # noqa: E402
from adapters.live import LiveTenancyAdapter                                    # noqa: E402
from adapters.second import DatabasePerTenantAdapter                            # noqa: E402

ADAPTERS = {"dryrun": DryRunTenancyAdapter, "live": LiveTenancyAdapter, "second": DatabasePerTenantAdapter}
TENANT_A, TENANT_B = "tenant-northwind", "tenant-acme"


def ask(dispatch: str, operation: str, principal: str | None, **payload) -> dict:
    actor = {"id": "user:corey"}
    if principal:
        actor["principal"] = principal
    return {"operation": operation, "actor": actor,
            "context": {"run_id": "run-" + dispatch, "root_dispatch_id": dispatch}, **payload}


def admitted(adapter: TenancyAdapter, doc: dict):
    return adapter.admit(ScopeRequest.from_dict(doc))


def refused(adapter: TenancyAdapter, doc: dict, want: str) -> dict:
    try:
        admitted(adapter, doc)
    except Problem as problem:
        body = dict(problem.body)
        if not body["type"].endswith(want):
            raise AssertionError(f"expected {want}, got {body['type']}: {body['detail']}") from None
        return body
    raise AssertionError(f"expected {want}, got an admission")


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "report_adapter": adapter.report_adapter,
              "locus_of_the_tenant_boundary": adapter.locus_of_the_tenant_boundary,
              "failure_mode_of_a_wrong_or_missing_principal": adapter.failure_mode_of_a_wrong_or_missing_principal,
              "provisioning_cost_of_a_new_principal": adapter.provisioning_cost_of_a_new_principal, "cases": []}
    cases: list[tuple[str, str]] = []
    leak = {"reads": 0, "recalls": 0, "spend": 0}      # measured here, not self-reported by the adapter

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            except Exception as exc:            # a case never crashes the run; it fails and is named
                cases.append(("FAIL", f"{label}: {type(exc).__name__}: {exc}"))
            return fn
        return wrap

    # --- seed: two principals write disjoint keys, so a corpus reads real data, not fixtures ---
    admitted(adapter, ask("s01", "write", TENANT_A, key="doc-a", value="northwind's record"))
    admitted(adapter, ask("s02", "write", TENANT_B, key="doc-b", value="acme's record"))
    admitted(adapter, ask("s03", "write", TENANT_A, key="note-a", value="northwind's note"))
    admitted(adapter, ask("s04", "write", TENANT_B, key="note-b", value="acme's note"))

    @case("a unit under one principal is admitted, its record carries that principal and identity.resolve")
    def _admit():
        record, _ = admitted(adapter, ask("d01", "write", TENANT_A, key="doc-a2", value="another record"))
        assert record.principal == TENANT_A, record.principal
        assert record.resolved_at == "identity.resolve", record.resolved_at
        assert record.adapter == adapter.report_adapter, record.adapter
        return f"principal={record.principal} resolved_at={record.resolved_at} adapter={record.adapter}"

    @case("a read under the writing principal returns its own value")
    def _read_own():
        _, value = admitted(adapter, ask("d02", "read", TENANT_A, key="doc-a"))
        assert value == "northwind's record", value
        return f"read doc-a as {TENANT_A}: {value!r}"

    @case("a spend under one principal is scoped to that principal's own ceiling")
    def _spend_own():
        _, remaining = admitted(adapter, ask("d03", "spend", TENANT_A, amount_micros=1000))
        assert remaining == 499_000, remaining
        _, other = admitted(adapter, ask("d04", "spend", TENANT_B, amount_micros=1000))
        assert other == 499_000, other      # tenant B's ceiling is untouched by tenant A's spend
        return f"tenant A remaining={remaining} tenant B remaining={other}, independent ledgers"

    @case("a spend exceeding one principal's ceiling terminates only that principal's unit")
    def _spend_exceeds():
        body = refused(adapter, ask("d05", "spend", TENANT_A, amount_micros=10_000_000), "budget-exceeded")
        assert body["principal"] == TENANT_A, body
        _, still_ok = admitted(adapter, ask("d06", "spend", TENANT_B, amount_micros=1000))
        assert still_ok >= 0, still_ok       # tenant B still spends after tenant A's ceiling was hit
        return f"{body['type']} for {body['principal']}, tenant B still spends: {still_ok}"

    @case("a read across principals is refused with a typed problem, not a redacted view")
    def _read_cross():
        try:
            _, value = admitted(adapter, ask("d07", "read", TENANT_A, key="doc-b"))
        except Problem as problem:
            assert problem.body["status"] == 403 and problem.body["rule_id"] == "tenancy-scope", problem.body
            return f"{problem.body['type']} 403 by {problem.body['rule_id']}, no value disclosed"
        leak["reads"] += 1
        raise AssertionError(f"a cross-tenant read returned {value!r} instead of a typed refusal")

    @case("a recall across principals returns only the caller's own keys, never a count of the other's")
    def _recall_cross():
        _, keys_a = admitted(adapter, ask("d08", "recall", TENANT_A))
        _, keys_b = admitted(adapter, ask("d09", "recall", TENANT_B))
        foreign_a, foreign_b = set(keys_a) & {"doc-b", "note-b"}, set(keys_b) & {"doc-a", "note-a", "doc-a2"}
        leak["recalls"] += len(foreign_a) + len(foreign_b)
        assert not foreign_a and not foreign_b, f"{TENANT_A} saw {foreign_a}, {TENANT_B} saw {foreign_b}"
        return f"{TENANT_A} recalls {sorted(keys_a)}, {TENANT_B} recalls {sorted(keys_b)}"

    @case("a unit with no principal is refused at entry, before any store is touched")
    def _no_principal():
        touched_before = adapter.counters()["units_checked"]
        body = refused(adapter, ask("d10", "read", None, key="doc-a"), "no-principal")
        assert body["status"] == 422, body
        assert adapter.counters()["units_checked"] == touched_before, "the entry check let a unit through"
        return f"{body['type']} 422, units_checked unchanged at {touched_before}"

    @case("a caller cannot decline the gate with an advisory field")
    def _no_bypass():
        doc = ask("d11", "read", TENANT_A, key="doc-a")
        doc["enforce"] = False
        try:
            admitted(adapter, doc)
        except Problem as problem:
            assert problem.body["status"] == 422 and problem.body["rejected_fields"] == ["enforce"], problem.body
            return "a request carrying a bypass field is 422, refused before resolve_scope even ran"
        raise AssertionError("a bypass field was accepted")

    @case("a spend naming a different target principal is refused, not silently charged there")
    def _spend_impersonation():
        try:
            _, remaining = admitted(adapter, ask("d12", "spend", TENANT_A, amount_micros=500,
                                                 target_principal=TENANT_B))
        except Problem as problem:
            assert problem.body["type"].endswith("cross-tenant-denied"), problem.body
            return f"{problem.body['type']} for a spend by {TENANT_A} naming target {TENANT_B}"
        leak["spend"] += 1
        raise AssertionError(f"a spend by {TENANT_A} targeting {TENANT_B} was admitted, remaining={remaining}")

    counters = adapter.counters()
    counters["cross_tenant_reads"] = leak["reads"]
    counters["cross_tenant_recalls"] = leak["recalls"]
    counters["cross_tenant_spend"] = leak["spend"]
    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["tenancy_conformance_report"] = {**counters, "adapters_run": 1, "selected_by": "configuration"}
    return cases, report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the tenancy interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    args = ap.parse_args(argv)

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        card = report["tenancy_conformance_report"]
        print(f"# binding {name} ({card['adapter']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"]
        failures += 0 if card["principals_covered"] >= 2 else 1
        failures += 0 if card["no_principal_admitted"] == 0 else 1
        failures += 0 if card["cross_tenant_reads"] == 0 else 1
        failures += 0 if card["cross_tenant_recalls"] == 0 else 1
        failures += 0 if card["cross_tenant_spend"] == 0 else 1
        print(f"  adapter={card['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"units_checked={card['units_checked']} principals_covered={card['principals_covered']} "
              f"no_principal_admitted={card['no_principal_admitted']} "
              f"cross_tenant_reads={card['cross_tenant_reads']} cross_tenant_recalls={card['cross_tenant_recalls']} "
              f"cross_tenant_spend={card['cross_tenant_spend']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s), adapters_run={len(reports)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
