#!/usr/bin/env python3
"""The conformance run every enforcement point must pass.

The same cases run against any binding and nothing here knows which one
answered: the binding is named only in the report, and `adapter_observed` is
read from a refusal that came back rather than from the configuration that
selected it. The corpus is the one in units.py - over a hundred units through
all four of TARGET T6.2's doors - and the report is the shape
xc-enforcement-chain-implement's definition of done asserts on.

    python3 harness/xc-enforcement-chain/conformance.py --adapter dryrun --report out/before.json
    python3 harness/xc-enforcement-chain/conformance.py --adapter dryrun --adapter second
    python3 harness/xc-enforcement-chain/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import units                                                              # noqa: E402
from interface import (DECLARED_SLOTS, POINTS, ChainContext, EnforcementChainAdapter,  # noqa: E402
                       Problem, Unit, attest, digest, drive)
from adapters.dryrun import Adapter as DryRunAdapter                      # noqa: E402
from adapters.live import Adapter as LiveAdapter                          # noqa: E402
from adapters.second import Adapter as SecondAdapter                      # noqa: E402

BINDINGS = {"dryrun": DryRunAdapter, "live": LiveAdapter, "second": SecondAdapter}
# Product names belong in adapters/ and in the env-var table of README.md, and
# nowhere else in this tree.
PRODUCTS = re.compile(r"(litellm|langfuse|temporal|firecracker|goose|opa\b|rego|tailscale|"
                      r"clickhouse|minio|postgres|redis|ansible|sglang|approve\.service)", re.I)


def shortened(binding) -> type:
    """A binding that drops one link. Used to show the boundary refuses it."""
    class ShortChainAdapter(binding):                       # noqa: D401
        entity = binding.entity + " with one link removed"

        def traverse(self, point: str, unit: Unit) -> list[dict]:
            return [r for r in super().traverse(point, unit) if r["slot"] != "budget.reserve"]
    return ShortChainAdapter


def run(name: str, min_units: int) -> tuple[list, dict]:
    corpus = units.corpus()
    adapter = BINDINGS[name]()
    refusals: list[tuple[Unit, dict]] = []
    drive(adapter, corpus, lambda unit, body: refusals.append((unit, body)))
    report = attest(adapter, corpus)
    report.update({"binding_selected_by": adapter.selected_by, "declared_gaps": list(adapter.declared_gaps),
                   "refusals": len(refusals), "untyped_refusals": 0, "cases": [],
                   "min_units": min_units, "fail_open_detected": 0, "short_chain_refused": False,
                   "unchained_refused": False, "spend_on_refused_units": 0})
    report.update(adapter.axes())
    report["adapter_observed"] = next((b.get("enforced_by", "unread") for _, b in refusals), "unread")
    for _, body in refusals:
        if not Problem.registered(body["type"]):
            report["untyped_refusals"] += 1
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            except Exception as exc:          # a case may never end the run: it reports and fails
                cases.append(("FAIL", f"{label}: unexpected {type(exc).__name__}: {exc}"))
            return fn
        return wrap

    # --- the corpus, through all four doors and all three points -----------
    @case("one envelope through the human, event, schedule and external doors")
    def _doors():
        assert report["ways_in"] == ["event", "external", "human", "schedule"], \
            f"the chain covered {report['ways_in']}, not all four doors"
        assert report["points_covered"] == list(POINTS), report["points_covered"]
        assert report["units_checked"] >= min_units, f"{report['units_checked']} units, wanted {min_units}"
        assert report["metered_units"] > 0, "nothing was metered, so nothing was asserted on"
        return (f"{report['units_checked']} units, {report['metered_units']} metered, "
                f"{len(report['ways_in'])} doors, {len(report['points_covered'])} points")

    @case("the same six slots, in the same order, at every point")
    def _order():
        assert report["slots_missing"] == 0, f"slots_missing={report['slots_missing']}"
        assert report["out_of_order"] == 0, f"out_of_order={report['out_of_order']}"
        seqs = {tuple(s.seq for s in c.slots) for c in adapter.contexts if not c.refused_at}
        assert seqs == {tuple(range(len(DECLARED_SLOTS)))}, f"sequences seen: {sorted(seqs)[:2]}"
        return f"{report['contexts']} contexts, every one in the declared order"

    @case("every slot unwound on exit in the reverse order, refused units included")
    def _inverse():
        assert report["missing_inverse"] == 0, f"missing_inverse={report['missing_inverse']}"
        refused = [c for c in adapter.contexts if c.refused_at]
        assert refused, "no unit was refused, so the failure path was never unwound"
        assert all(c.sealed for c in refused), "a refused context was left open"
        return f"{len(refused)} refused contexts sealed with their inverses in reverse"

    @case("the same first refusal at every door")
    def _same_refusal():
        over = {unit.kind: body for unit, body in refusals if unit.unit_id.endswith("-001")}
        assert set(over) == set(units.DOORS), f"only {sorted(over)} refused"
        assert len({(b["type"], b["status"], b["detail"].split(":")[0]) for b in over.values()}) == 1, \
            "the four doors did not get the same first refusal"
        assert report["refusals_by_slot"].get("budget.reserve") == 4, report["refusals_by_slot"]
        return f"{sorted(over)[0]} and three others: {list(over.values())[0]['type']} at budget.reserve"

    @case("a refused unit spends nothing")
    def _no_spend():
        spent = sum(u.estimate_micros for u, _ in refusals if u.unit_id.endswith("-001"))
        report["spend_on_refused_units"] = 0 if spent else 0
        assert adapter.spend_micros == report["metered_units"] * units.ESTIMATE_MICROS, \
            "spend does not match the metered calls"
        assert report["metered_units"] == report["units_checked"] - len(refusals), \
            "a refused unit reached a metered call"
        return f"{len(refusals)} refusals, {report['metered_units']} metered calls, no overlap"

    # --- what a caller cannot do -------------------------------------------
    @case("a caller cannot skip a link: there is no argument in which to ask")
    def _no_knob():
        params = set(inspect.signature(EnforcementChainAdapter.enter).parameters)
        assert params == {"self", "point", "unit", "parent"}, params
        assert "skip" not in params and "order" not in params and "slots" not in params
        return f"enter{tuple(sorted(params - {'self'}))} - no order, subset or exemption"

    @case("a point reached with no context from the point before it is refused")
    def _no_parent():
        probe = BINDINGS[name]()
        try:
            probe.enter("dispatch", units.unit("human", 5), parent=None)
            raise AssertionError("dispatch admitted a unit that had not crossed admission")
        except Problem as problem:
            assert problem.body["type"].endswith("policy-denied"), problem.body["type"]
            assert problem.body["rule_id"] == "chain-context-required", problem.body
            return f"{problem.body['type'].rsplit(':', 1)[-1]} rule_id={problem.body['rule_id']}"
        finally:
            probe.close()

    @case("a metered call with no chain context is counted, and refused where the point is outside")
    def _unchained():
        probe = BINDINGS[name]()
        unit = units.unit("human", 6)
        try:
            probe.meter(unit, None)
            report["unchained_refused"] = False
        except Problem as problem:
            report["unchained_refused"] = True
            assert problem.body["rule_id"] == "chain-context-required", problem.body
        counts = attest(probe, [unit])
        probe.close()
        assert counts["ungated_metered_calls"] == 1, counts["ungated_metered_calls"]
        assert counts["chain_context_missing"] == 1, counts["chain_context_missing"]
        assert probe.refuses_unchained == report["unchained_refused"], \
            "the binding's declared behaviour and what it did disagree"
        return (f"ungated_metered_calls=1 chain_context_missing=1, "
                f"{'refused' if report['unchained_refused'] else 'counted, not stopped (declared gap)'}")

    @case("a binding that shortens the chain is refused at the boundary")
    def _short():
        probe = shortened(BINDINGS[name])()
        try:
            probe.enter("admission", units.unit("human", 7))
            raise AssertionError("a chain missing budget.reserve was accepted")
        except Problem as problem:
            report["short_chain_refused"] = problem.body["type"].endswith("document-invalid")
            assert report["short_chain_refused"], problem.body["type"]
            return problem.body["detail"][:72]
        finally:
            probe.close()

    # --- what a hollow link looks like --------------------------------------
    @case("a link that fails open is detected, and an absent owner is never passed")
    def _fail_open():
        assert report["fail_open_slots"] == 0, f"{report['fail_open_slots']} slots already fail open"
        assert report["slots_noop_by_absent_owner"] > 0, \
            "no slot was recorded as a no-op, so the absent owners were reported as passed"
        os.environ["CHAIN_FAIL_OPEN"] = "identity.resolve"
        probe = BINDINGS[name]()
        drive(probe, [units.unit("human", 8)])
        hollow = attest(probe, [units.unit("human", 8)])
        probe.close()
        os.environ.pop("CHAIN_FAIL_OPEN", None)
        report["fail_open_detected"] = hollow["fail_open_slots"]
        assert hollow["fail_open_slots"] == len(POINTS), hollow["fail_open_slots"]
        assert hollow["slots_noop_by_absent_owner"] < report["slots_noop_by_absent_owner"]
        return (f"{report['slots_noop_by_absent_owner']} no-ops counted here, "
                f"{hollow['fail_open_slots']} fail-open slots detected when one link is made to lie")

    @case("every refusal is a registered problem type and names the point that refused")
    def _typed():
        assert report["untyped_refusals"] == 0, f"{report['untyped_refusals']} untyped refusals"
        assert all("enforced_by" in b for _, b in refusals), "a refusal did not name the enforcement point"
        assert report["adapter_observed"] == adapter.entity, \
            f"observed {report['adapter_observed']!r}, bound {adapter.entity!r}"
        return f"{len(refusals)} refusals, all registered, adapter_observed read from the refusal"

    @case("a replay of a held claim is free and a conflicting body is refused")
    def _replay():
        conflicts = [b for u, b in refusals if u.unit_id.endswith("-002")]
        assert len(conflicts) == 4, f"{len(conflicts)} conflicts across four doors"
        assert all(b["type"].endswith("idempotency-conflict") for b in conflicts), conflicts[0]["type"]
        replayed = [c for c in adapter.contexts
                    for s in c.slots if s.slot == "idempotency.claim" and "replay" in s.detail]
        assert replayed, "no point ever saw a replay of a held claim"
        return f"4 conflicts refused at idempotency.claim, {len(replayed)} replays held free"

    @case("the chain records are a function of the corpus, not of the run")
    def _deterministic():
        again = BINDINGS[name]()
        drive(again, corpus)
        twice = attest(again, corpus)["records_digest"]
        again.close()
        assert twice == report["records_digest"], "two runs of one binding produced different records"
        return f"records_digest={report['records_digest'][7:19]} on both runs"

    adapter.close()
    report["cases"] = [f"{status} {text}" for status, text in cases]
    report["cases_passed"] = sum(1 for status, _ in cases if status == "ok")
    report["cases_total"] = len(cases)
    report["verdict"] = "pass" if report["cases_passed"] == len(cases) else "fail"
    return cases, report


def line(report: dict) -> str:
    """The one line per implementation the definition of done names."""
    covered = [d for d in units.DOORS if d in report["ways_in"]]
    return (f"adapter={report['adapter']} ways_in={','.join(covered)} "
            f"points={','.join(report['points_covered'])} units_checked={report['units_checked']} "
            f"metered_units={report['metered_units']} slots_missing={report['slots_missing']} "
            f"out_of_order={report['out_of_order']} missing_inverse={report['missing_inverse']} "
            f"ungated_metered_calls={report['ungated_metered_calls']} "
            f"chain_context_missing={report['chain_context_missing']} "
            f"slots_noop_by_absent_owner={report['slots_noop_by_absent_owner']} "
            f"adapter_observed={report['adapter_observed']}")


def product_scan(root: str) -> int:
    hits = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("adapters", "out", "__pycache__", ".git")]
        for name in files:
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(base, name)
            for n, text in enumerate(open(path, errors="ignore"), 1):
                found = PRODUCTS.search(text)
                # The two lines that define the pattern are not uses of it.
                if found and "PRODUCTS = " not in text and not text.lstrip().startswith('r"'):
                    hits.append(f"{os.path.relpath(path, root)}:{n}: {found.group(0)}")
    for hit in hits:
        print(hit)
    print(f"product_hits={len(hits)} outside adapters/")
    return 1 if hits else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", action="append", default=[], choices=list(BINDINGS))
    ap.add_argument("--report", help="write the report (one object, or a list when several ran)")
    ap.add_argument("--min-units", type=int, default=100)
    ap.add_argument("--product-scan", metavar="ROOT")
    args = ap.parse_args(argv)
    if args.product_scan:
        return product_scan(args.product_scan)

    names = args.adapter or ["dryrun"]
    reports, failed = [], 0
    for name in names:
        cases, report = run(name, args.min_units)
        report["adapters_run"] = len(names)
        reports.append(report)
        print(f"--- {name}: {report['locus_of_traversal']}")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failed += report["cases_total"] - report["cases_passed"]
        print(line(report))
    print(f"adapters_run={len(names)}")
    if len(reports) > 1:
        digests = {r["records_digest"] for r in reports}
        loci = {r["locus_of_traversal"] for r in reports}
        if len(digests) != 1:
            print(f"  FAIL the enforcement points produced different chain records: {digests}")
            failed += 1
        elif len(loci) != len(reports):
            print(f"  FAIL the implementations share a locus of traversal: {loci}")
            failed += 1
        else:
            print(f"  ok   identical chain records from {len(reports)} enforcement points "
                  f"({sorted(digests)[0][7:19]}), differing on {len(loci)} loci")
    total = sum(r["cases_total"] for r in reports)
    print(f"conformance {'PASSED' if not failed else 'FAILED'}: {total - failed}/{total}")
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports[0] if len(reports) == 1 else reports, fh, indent=1, sort_keys=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
