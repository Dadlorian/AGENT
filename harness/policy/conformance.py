#!/usr/bin/env python3
"""The conformance run every policy adapter must pass.

The same fourteen cases run against any binding: nothing here knows which
engine answered. Used before and after a swap; the two reports are what proves
the interface held (T-t7-05, T-t9-06). The report carries the counters
cap-policy-implement's definition of done asserts on - decisions_taken,
spend_delta_micros, rule_id_present, decided_before_first_metered_call,
adapters_run, selected_by - under `policy_conformance_report`.

    python3 harness/policy/conformance.py --adapter dryrun --report out/before.json
    python3 harness/policy/conformance.py --adapter second --report out/after.json
    python3 harness/policy/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (Decision, DecisionRequest, PolicyAdapter, Problem,       # noqa: E402
                       decision_as_dict, digest_of, load_bundle)
from adapters.dryrun import DryRunPolicyAdapter                                 # noqa: E402
from adapters.live import LivePolicyAdapter                                     # noqa: E402
from adapters.second import TypedEntityPolicyAdapter                            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunPolicyAdapter, "live": LivePolicyAdapter, "second": TypedEntityPolicyAdapter}
# Engine, rule-language and vendor names belong in adapters/ and in README.md, nowhere else.
PRODUCTS = re.compile(r"\b(opa|rego|cedar|zanzibar|styra|open ?policy ?agent)\b", re.I)
DECISION_FIELDS = {"effect", "rule_id", "policy_version", "decision_point",
                   "input_digest", "decided_at", "problem"}
PINNED = digest_of(load_bundle())


def ask(dispatch: str, point="dispatch.tool_call", scope="internal", mandates=(),
        tenant="tenant-acme", resource_tenant=None, version=None, **extra) -> dict:
    resource = {"tenant": resource_tenant or tenant, "tool": "tool:web-fetch", "scope": scope}
    if point == "dispatch.data_query":
        resource = {"tenant": resource_tenant or tenant, "query": "count(open incidents)"}
    doc = {"decision_point": point,
           "subject": {"id": "user:corey", "tenant": tenant, "mandates": list(mandates)},
           "action": "invoke",
           "resource": resource,
           "context": {"run_id": "run-" + dispatch, "root_dispatch_id": dispatch},
           "policy_version": version or PINNED}
    doc.update(extra)
    return doc


def run_work(adapter: PolicyAdapter, doc: dict) -> tuple[Decision, list]:
    """admit the unit of work; the list records whether it ever ran."""
    ran: list = []
    dispatch = doc["context"]["root_dispatch_id"]

    def work(meter):
        ran.append(meter.charge(dispatch, 1200))
        return "ran"
    decision, _ = adapter.admit(DecisionRequest.from_dict(doc), work)
    return decision, ran


def refused(adapter: PolicyAdapter, doc: dict, want: str) -> tuple[dict, list]:
    ran: list = []
    dispatch = doc.get("context", {}).get("root_dispatch_id", "unknown")

    def work(meter):
        ran.append(meter.charge(dispatch, 1200))
        return "ran"
    try:
        adapter.admit(DecisionRequest.from_dict(doc), work)
    except Problem as problem:
        body = dict(problem.body)
        if not body["type"].endswith(want):
            raise AssertionError(f"expected {want}, got {body['type']}: {body['detail']}") from None
        return body, ran
    raise AssertionError(f"expected {want}, got an admission")


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "report_adapter": adapter.report_adapter,
              "decision_model": adapter.decision_model, "activation_model": adapter.activation_model,
              "processes_required": adapter.processes_required,
              "conformance_subset": list(adapter.conformance_subset), "cases": []}
    cases: list[tuple[str, str]] = []

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

    @case("one decision for one unit of work")
    def _allow():
        decision, ran = run_work(adapter, ask("d01"))
        assert decision.effect == "allow", decision.effect
        assert decision.rule_id, "an allow with no rule_id is unattributable"
        assert decision.policy_version == PINNED, decision.policy_version
        assert decision.input_digest.startswith("sha256:") and len(decision.input_digest) == 71, decision.input_digest
        assert ran == [1200], "the unit of work did not run on the far side of an allow"
        return f"allow by {decision.rule_id}, pinned to {decision.policy_version[:14]}, work ran"

    @case("a denied unit of work is refused before execution, not after spend")
    def _deny():
        body, ran = refused(adapter, ask("d02", scope="external"), "policy-denied")
        assert body["type"].endswith("policy-denied") and body["status"] == 403, body["type"]
        assert body["rule_id"] == "deny-external-tool-without-mandate", body.get("rule_id")
        assert body["spend_delta_micros"] == 0, f"a deny cost {body['spend_delta_micros']} micros"
        assert ran == [], "the unit of work ran anyway"
        report["deny_type"] = body["type"]
        return f"{body['type']} 403 by {body['rule_id']}, spend_delta_micros=0, work never ran"

    @case("the decision precedes the first metered call of its dispatch")
    def _ordering():
        run_work(adapter, ask("d03"))
        taken, before = adapter.ordering()
        assert taken and before == taken, f"{before} of {taken} decisions preceded the first metered call"
        return f"decided_before_first_metered_call={before} of decisions_taken={taken}"

    @case("every decision is attributable, allow rows included")
    def _attributable():
        assert adapter.rule_id_present(), "a decision was recorded with no rule_id"
        allows = [r["decision"].rule_id for r in adapter.journal if r["decision"].effect == "allow"]
        assert allows and all(allows), "an allow was recorded without the rule that permitted it"
        return f"{len(adapter.journal)} records, {len(allows)} of them allows, every one names a rule"

    @case("a caller cannot decline the gate")
    def _no_bypass():
        body, ran = refused(adapter, ask("d05", enforce=False), "document-invalid")
        assert body["status"] == 422 and body["rejected_fields"] == ["enforce"], body
        assert ran == [], "the unit of work ran anyway"
        assert "no bypass" in body["detail"], body["detail"]
        return "a request carrying a bypass field is 422 and nothing ran"

    @case("the gate is not overridden by the binding")
    def _not_overridden():
        for operation in ("admit", "decide", "explain", "activate"):
            assert getattr(type(adapter), operation) is getattr(PolicyAdapter, operation), \
                f"the binding overrides {operation}, so the platform no longer owns the order of the gate"
        return "admit, decide, explain and activate are the interface's, not the binding's"

    @case("an unregistered decision point is not a default-allow")
    def _unregistered():
        body, ran = refused(adapter, ask("d07", point="dispatch.unregistered"), "decision-point-unregistered")
        assert body["status"] == 422 and body["type"].endswith("decision-point-unregistered"), body
        assert ran == [], "the unit of work ran anyway"
        return f"{body['type']} 422, nothing was assumed"

    @case("a resource that fails the point's declared shape is refused before evaluation")
    def _shape():
        before = adapter.evaluations
        doc = ask("d08")
        doc["resource"].pop("scope")
        body, ran = refused(adapter, doc, "document-invalid")
        assert body["status"] == 422 and body["missing"] == ["scope"], body
        assert adapter.evaluations == before, "the request reached evaluation anyway"
        assert ran == [], "the unit of work ran anyway"
        return "422 before evaluation, no rule was consulted against an assumed shape"

    @case("an unresolvable policy version is refused, so a decision is always replayable")
    def _version():
        body, ran = refused(adapter, ask("d09", version="sha256:" + "0" * 64), "policy-version-unknown")
        assert body["status"] == 409, body
        assert ran == [], "the unit of work ran anyway"
        return f"{body['type']} 409, nothing was decided under an unknown bundle"

    @case("the same question under the same version gives the same answer")
    def _deterministic():
        question = DecisionRequest.from_dict(ask("d10a"))   # decide alone: the same question, twice
        first, second = adapter.decide(question), adapter.decide(question)
        assert (first.effect, first.rule_id) == (second.effect, second.rule_id), (first, second)
        assert first.input_digest == second.input_digest, "the digest of one question changed between runs"
        return f"twice {first.effect}/{first.rule_id}, one input digest"

    @case("explain recomputes the rule from the pinned version, across an activation")
    def _explain():
        decision, _ = run_work(adapter, ask("d11"))
        newer = copy.deepcopy(load_bundle())
        newer["rules"].insert(0, {"rule_id": "deny-everything-under-the-newer-bundle", "decision_point": "*",
                                  "effect": "deny", "detail": "a newer bundle denies this", "when": []})
        version = adapter.activate(newer)
        assert version != PINNED and adapter.active_version == version, "activation did not change the version"
        replayed = adapter.explain(decision.input_digest, decision.policy_version)
        assert (replayed.effect, replayed.rule_id) == (decision.effect, decision.rule_id), replayed
        assert replayed.policy_version == PINNED, replayed.policy_version
        report["activation_versions"] = 2
        return f"the old decision still explains to {replayed.rule_id} under {PINNED[:14]}"

    @case("a cross-tenant resource is denied")
    def _tenant():
        body, ran = refused(adapter, ask("d12", resource_tenant="tenant-other"), "policy-denied")
        assert body["rule_id"] == "deny-cross-tenant-resource", body.get("rule_id")
        assert body["spend_delta_micros"] == 0 and ran == [], body
        return f"{body['rule_id']}, spend_delta_micros=0"

    @case("nothing names an engine, a rule language or a bundle on the way out")
    def _no_leak():
        decision, _ = run_work(adapter, ask("d13"))
        doc = json.dumps(decision_as_dict(decision))
        found = PRODUCTS.search(doc)
        assert not found, f"a product name reached the caller: {found and found.group(0)}"
        assert set(json.loads(doc)) <= DECISION_FIELDS, "the decision grew a field"
        assert adapter.declared_marker not in doc, "the binding's marker reached the caller"
        report["marker"] = adapter.observed_marker
        return "a decision carries an effect, a rule, a version and a digest, and nothing about who answered"

    @case("a point this binding cannot serve is declared, never answered allow")
    def _subset():
        if not adapter.conformance_subset:
            decision, _ = run_work(adapter, ask("d14", point="dispatch.data_query"))
            assert decision.effect in ("allow", "deny") and decision.rule_id, decision
            return "no declared subset; every registered point is answered"
        point = adapter.conformance_subset[0]
        body, ran = refused(adapter, ask("d14", point=point), "adapter-unavailable")
        assert body["status"] == 503 and body["declared_subset"] == list(adapter.conformance_subset), body
        assert ran == [], "the unit of work ran anyway"
        return f"declared subset {list(adapter.conformance_subset)} refused, not answered allow"

    taken, before = adapter.ordering()
    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["denies"] = adapter.denies
    report["metered_micros"] = adapter.meter.spend()
    report["decisions"] = {r["decision"].input_digest: f"{r['decision'].effect}:{r['decision'].rule_id}"
                           for r in adapter.journal}
    report["product_hits"] = product_scan(HERE)[0]
    # The shape cap-policy-implement's definition of done asserts on, per adapter.
    report["policy_conformance_report"] = {
        "adapter": adapter.report_adapter, "decisions_taken": taken,
        "spend_delta_micros": adapter.denied_spend_micros(),
        "rule_id_present": adapter.rule_id_present(),
        "decided_before_first_metered_call": before,
        "adapters_run": 1, "selected_by": "configuration"}
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
    """Engine and rule-language names may live in adapters/ and in README.md. Nowhere else.

    Code is what is scanned (.py and .sh); bundle.json and decision_points.json
    are rule and registry data, and neither names an engine.
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
    ap = argparse.ArgumentParser(description="Conformance run for the policy interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for engine names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no engine or rule-language name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        card = report["policy_conformance_report"]
        print(f"# binding {name} ({report['decision_model']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        failures += 0 if card["decided_before_first_metered_call"] == card["decisions_taken"] else 1
        failures += 0 if card["spend_delta_micros"] == 0 else 1
        failures += 0 if card["rule_id_present"] else 1
        print(f"  adapter={card['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"decisions_taken={card['decisions_taken']} "
              f"decided_before_first_metered_call={card['decided_before_first_metered_call']} "
              f"spend_delta_micros={card['spend_delta_micros']} rule_id_present={card['rule_id_present']} "
              f"subset={report['conformance_subset']} product_hits={report['product_hits']}")
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
