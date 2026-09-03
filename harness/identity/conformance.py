#!/usr/bin/env python3
"""The conformance run every identity adapter must pass.

The same fourteen cases run against any binding: nothing here knows which
adapter answered. Two of them are the corpus assertion cap-identity-implement's
definition of done words as P13 - a chain that is shorter than the hops that
occurred, or whose current actor is not the unit that executed, is counted, not
argued about. Used before and after a swap; the two reports are what proves the
interface held (T-t7-05, T-t9-06).

    python3 harness/identity/conformance.py --adapter dryrun --report out/before.json
    python3 harness/identity/conformance.py --adapter second --report out/after.json
    python3 harness/identity/conformance.py --adapter dryrun --adapter second   # the pair
    python3 harness/identity/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (SUBJECT_PATTERN, TRUST, AttestRequest, Credential,  # noqa: E402
                       DelegationRequest, IdentityAdapter, Problem, ROOT_OBTAINED_VIA,
                       classify_chain, classify_scope, credential_as_dict)
from adapters.dryrun import ExchangeIssuingAdapter                         # noqa: E402
from adapters.live import LiveIssuerAdapter                                # noqa: E402
from adapters.second import AttestedWorkloadAdapter                        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": ExchangeIssuingAdapter, "live": LiveIssuerAdapter,
            "second": AttestedWorkloadAdapter}
# Product names belong in adapters/ and in the env-var table of README.md, nowhere else.
PRODUCTS = re.compile(r"\b(spiffe|spire|svid|keycloak|okta|auth0|hashicorp|vault|entra|cognito|zitadel)\b", re.I)
CREDENTIAL_FIELDS = {"handle", "subject", "chain", "scope", "audience", "issued_at", "expires_at"}
HOP_RECORD_FIELDS = {"run_id", "action_id", "hop_index", "actor", "obtained_via",
                     "enforcement_point", "written_at", "executing_unit", "handle"}
EXPECTED_HOPS = 3          # what the corpus drives: a root, an intake hop, an agent hop


# --- driving one action ------------------------------------------------------
def drive(adapter: IdentityAdapter, index: int) -> dict:
    """One action, end to end. The same code drives every adapter."""
    adapter.current_action = f"action-{index:03d}"
    principal = adapter.verify(adapter.fixture_presented(
        "user:corey", ["read:incident", "call:model", "write:ledger"], "svc:platform", 3600))
    intake = adapter.attest(AttestRequest.from_dict(
        {"unit": "service:intake", "audience": "svc:planner",
         "scope": ["read:incident", "call:model"], "lifetime_s": 1800,
         "platform_facts": {"cell": f"cell-{index:02d}", "uid": 61000 + index},
         "presented": adapter.fixture_presented("service:intake",
                                                ["read:incident", "call:model"], "svc:planner", 1800)}))
    first = adapter.delegate(DelegationRequest.from_dict(
        {"subject": principal, "actor": intake, "scope": ["read:incident", "call:model"],
         "audience": "svc:planner", "lifetime_s": 1200}))
    worker = adapter.attest(AttestRequest.from_dict(
        {"unit": f"agent:worker-{index}", "audience": "svc:model-gateway", "scope": ["call:model"],
         "lifetime_s": 900, "vouched_by": intake,
         "platform_facts": {"cell": f"cell-{index:02d}", "uid": 62000 + index},
         "presented": adapter.fixture_presented(f"agent:worker-{index}", ["call:model"],
                                                "svc:model-gateway", 900)}))
    token = adapter.delegate(DelegationRequest.from_dict(
        {"subject": first, "actor": worker, "scope": ["call:model"],
         "audience": "svc:model-gateway", "lifetime_s": 300}))
    return {"action_id": adapter.current_action, "expected_hops": EXPECTED_HOPS,
            "executing_unit": f"agent:worker-{index}", "credential": token,
            "steps": [("verify", principal), ("attest", intake), ("delegate", first),
                      ("attest", worker), ("delegate", token)]}


def check_corpus(actions: list) -> dict:
    """The P13 counters, computed from what the platform recorded, not from intent."""
    counters = {"actions_checked": len(actions), "missing_subject": 0, "short_chains": 0,
                "cyclic": 0, "executing_unit_mismatch": 0, "findings": []}
    for action in actions:
        cred = action["credential"]
        chain = [hop.actor for hop in cred.chain]
        if not cred.subject or not SUBJECT_PATTERN.match(cred.subject):
            counters["missing_subject"] += 1
            counters["findings"].append(f"{action['action_id']}: subject {cred.subject!r}")
        if len(cred.chain) < 2 or len(cred.chain) < action["expected_hops"]:
            counters["short_chains"] += 1
            counters["findings"].append(
                f"{action['action_id']}: chain {chain} is shorter than the "
                f"{action['expected_hops']} hops that occurred")
        if len(set(chain)) != len(chain):
            counters["cyclic"] += 1
            counters["findings"].append(f"{action['action_id']}: chain {chain} repeats an actor")
        if cred.actor != action["executing_unit"]:
            counters["executing_unit_mismatch"] += 1
            counters["findings"].append(
                f"{action['action_id']}: current actor {cred.actor} is not the unit that executed, "
                f"{action['executing_unit']}")
    return counters


def issued_or_declared(adapter: IdentityAdapter, doc: dict):
    """('issued', credential) or ('declared', problem body). Any other outcome raises."""
    try:
        return "issued", adapter.attest(AttestRequest.from_dict(doc))
    except Problem as problem:
        body = problem.body
        assert body["type"].endswith("adapter-unavailable"), f"unexpected {body['type']}"
        assert body.get("unsupported_operation") in adapter.unsupported, \
            f"refused {body.get('unsupported_operation')!r}, which is not in {adapter.unsupported}"
        assert body["retryable"] is False, "a declared subset is not retryable"
        return "declared", body


def refused(adapter: IdentityAdapter, call, want: str) -> dict:
    before = (adapter.attestations, adapter.exchanges)
    try:
        call()
    except Problem as problem:
        body = dict(problem.body)
        body["_issued"] = (adapter.attestations, adapter.exchanges) != before
        return body
    raise AssertionError(f"expected {want}, got a credential")


# --- the run -----------------------------------------------------------------
def run(name: str, min_actions: int) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "selected_by": "configuration", "adapters_run": 1,
              **adapter.binding(), "cases": []}
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

    baseline = drive(adapter, 1)
    token = baseline["credential"]
    adapter.current_action = "case"      # so a case's own records never join action-001

    @case("an actor is produced by verify, never built by the caller")
    def _verify():
        principal = baseline["steps"][0][1]
        assert isinstance(principal, Credential) and principal.subject == "user:corey", principal.subject
        assert principal.chain[0].obtained_via in ROOT_OBTAINED_VIA, principal.chain[0].obtained_via
        body = refused(adapter, lambda: adapter.delegate(DelegationRequest.from_dict(
            {"subject": {"subject": "user:corey"}, "actor": principal, "scope": ["call:model"],
             "audience": "svc:planner", "lifetime_s": 60})), "document-invalid")
        assert body["status"] == 422 and body["_issued"] is False, body
        return "verify returned the actor; a caller-built actor object is 422 and nothing was issued"

    @case("a unit of work gets a short-lived credential naming it")
    def _attest():
        intake = baseline["steps"][1][1]
        assert intake.subject == "service:intake", intake.subject
        assert intake.chain[0].obtained_via == adapter.attested_via, intake.chain[0].obtained_via
        assert 0 < intake.remaining_s() <= 1800, intake.remaining_s()
        return f"service:intake, {intake.remaining_s()}s left, obtained_via {adapter.attested_via}"

    @case("the form of attestation this binding cannot serve is declared, not answered")
    def _subset():
        facts_only = {"unit": "agent:worker-9", "audience": "svc:model-gateway", "scope": ["call:model"],
                      "lifetime_s": 300, "platform_facts": {"cell": "cell-09", "uid": 62009}}
        held_only = {"unit": "agent:worker-9", "audience": "svc:model-gateway", "scope": ["call:model"],
                     "lifetime_s": 300,
                     "presented": adapter.fixture_presented("agent:worker-9", ["call:model"],
                                                            "svc:model-gateway", 300)}
        outcomes = [issued_or_declared(adapter, facts_only)[0],
                    issued_or_declared(adapter, held_only)[0]]
        assert adapter.unsupported, "a binding that declares nothing has claimed it can do everything"
        assert "declared" in outcomes and "issued" in outcomes, outcomes
        report["subset_outcomes"] = {"from_platform_facts": outcomes[0], "from_held_credential": outcomes[1]}
        return f"facts-only {outcomes[0]}, held-credential {outcomes[1]}, declared {list(adapter.unsupported)}"

    @case("an already-attested party can obtain an identity for a unit it vouches for")
    def _vouched():
        intake = baseline["steps"][1][1]
        state, _ = issued_or_declared(adapter, {
            "unit": "agent:worker-void", "audience": "svc:model-gateway", "scope": ["call:model"],
            "lifetime_s": 300, "vouched_by": intake})
        report["delegated_issuance"] = state
        return f"{state}: the path for a unit the platform cannot observe in place"

    @case("the issued credential carries three hops, current actor first, root last")
    def _chain():
        chain = [(hop.actor, hop.obtained_via) for hop in token.chain]
        assert len(chain) == 3, chain
        assert chain[0][0] == "agent:worker-1" and chain[-1][0] == "user:corey", chain
        assert chain[-1][1] in ROOT_OBTAINED_VIA, f"the chain is rooted in {chain[-1][1]}"
        assert chain[1][1] == "token_exchange", chain
        report["chain"] = [{"actor": a, "obtained_via": v} for a, v in chain]
        return " <- ".join(actor for actor, _ in chain)

    @case("each hop is scoped no wider and expires no later than the one before it")
    def _narrowing():
        steps = [cred for _, cred in baseline["steps"]]
        widths, lifetimes = [], []
        for older, newer in zip(steps, steps[1:]):
            widths.append(classify_scope(older.scope, newer.scope))
            lifetimes.append(newer.remaining_s() <= older.remaining_s())
        assert "wider" not in widths, widths
        assert all(lifetimes), [c.remaining_s() for c in steps]
        assert token.remaining_s() < steps[0].remaining_s(), "the last hop is not shorter-lived"
        report["lifetimes_s"] = [c.remaining_s() for c in steps]
        return f"lifetimes {[c.remaining_s() for c in steps]}, scope {widths}"

    @case("a hop that widens scope is refused and nothing is issued")
    def _widen():
        worker = baseline["steps"][3][1]
        body = refused(adapter, lambda: adapter.delegate(DelegationRequest.from_dict(
            {"subject": token, "actor": worker, "scope": ["call:model", "deploy:prod"],
             "audience": "svc:deployer", "lifetime_s": 120})), "policy-denied")
        assert body["status"] == 403 and body["rule_id"] == "scope-must-narrow", body
        assert body["_issued"] is False and body["retryable"] is False, body
        assert "no credential was issued" in body["detail"], body["detail"]
        report["enforcement_point_observed"] = body["enforcement_point"]
        return f"{body['type']} 403 {body['rule_id']} at {body['enforcement_point']}"

    @case("a hop that extends the lifetime is refused")
    def _lifetime():
        first, worker = baseline["steps"][2][1], baseline["steps"][3][1]
        body = refused(adapter, lambda: adapter.delegate(DelegationRequest.from_dict(
            {"subject": first, "actor": worker, "scope": ["call:model"],
             "audience": "svc:model-gateway", "lifetime_s": 99_999})), "policy-denied")
        assert body["status"] == 403 and body["rule_id"] == "lifetime-must-not-extend", body
        assert body["_issued"] is False, body
        return f"{body['requested_lifetime_s']}s asked, {body['subject_remaining_s']}s left, refused"

    @case("a hop naming an actor already in the chain is refused")
    def _cycle():
        intake = baseline["steps"][1][1]
        body = refused(adapter, lambda: adapter.delegate(DelegationRequest.from_dict(
            {"subject": token, "actor": intake, "scope": ["call:model"],
             "audience": "svc:planner", "lifetime_s": 120})), "policy-denied")
        assert body["status"] == 403 and body["rule_id"] == "chain-must-be-acyclic", body
        assert body["_issued"] is False, body
        return f"{body['actor']} already at a hop of {body['chain']}, refused"

    @case("an expired credential does not verify")
    def _expired():
        stale = adapter.fixture_presented("service:intake", ["call:model"], "svc:planner", -60)
        body = refused(adapter, lambda: adapter.verify(stale), "identity-untrusted")
        assert body["status"] == 401 and body["retryable"] is False, body
        return f"{body['type']} 401, not retryable"

    @case("a chain rooted in nothing does not verify")
    def _unrooted():
        floating = adapter.fixture_presented("service:intake", ["call:model"], "svc:planner", 600,
                                             "token_exchange")
        body = refused(adapter, lambda: adapter.verify(floating), "identity-untrusted")
        assert body["status"] == 401 and body["chain_state"] == "unrooted", body
        return "a self-asserted root is 401, not a formatting problem"

    @case("no credential material, no trust material and no product name reaches the caller")
    def _no_leak():
        seen = json.dumps([credential_as_dict(cred) for _, cred in baseline["steps"]])
        for _, cred in baseline["steps"]:
            material = adapter.material_of(cred.handle)
            assert material and material not in seen, "credential material reached the caller"
        for secret in TRUST["trust_material"].values():
            assert secret not in seen, "trust material reached the caller"
        found = PRODUCTS.search(seen)
        assert not found, f"a product name reached the caller: {found and found.group(0)}"
        assert set(json.loads(seen)[0]) == CREDENTIAL_FIELDS, "the credential grew a field"
        return "a handle, a subject, a chain, a scope, one audience and an expiry, and nothing else"

    @case("authorisation reads the current actor and the top-level scope only")
    def _authorise():
        assert adapter.authorise(token, "call:model") == "agent:worker-1"
        root = baseline["steps"][0][1]
        assert "write:ledger" in root.scope, "the fixture no longer tests what it claims"
        body = refused(adapter, lambda: adapter.authorise(token, "write:ledger"), "policy-denied")
        assert body["status"] == 403 and body["rule_id"] == "scope-must-cover-the-action", body
        return "the root held write:ledger; the action was refused anyway"

    @case("narrowing and chain classification are pure, testable from a table")
    def _pure():
        before = (adapter.attestations, adapter.exchanges, adapter.verifications)
        for held, wanted, want in TRUST["narrowing_vectors"]:
            got = classify_scope(tuple(held), tuple(wanted))
            assert got == want, f"scope {held} -> {wanted} classified {got}, expected {want}"
        for chain, actor, want in TRUST["chain_vectors"]:
            got = classify_chain(tuple(_hop(h) for h in chain), actor)
            assert got == want, f"chain {chain} + {actor} classified {got}, expected {want}"
        assert (adapter.attestations, adapter.exchanges, adapter.verifications) == before, \
            "classification touched the adapter"
        return (f"{len(TRUST['narrowing_vectors'])} scope vectors and {len(TRUST['chain_vectors'])} "
                f"chain vectors, no credential issued")

    @case("one hop record per hop, appended, with the enforcement point read off the answer")
    def _records():
        assert adapter.hops, "no hop record was written"
        for record in adapter.hops:
            assert set(record) == HOP_RECORD_FIELDS, f"record shape {sorted(record)}"
            assert record["enforcement_point"] == adapter.declared_marker, record["enforcement_point"]
            assert record["obtained_via"] in ("direct", "token_exchange", "workload_attestation")
        first_action = [r for r in adapter.hops if r["action_id"].startswith("action-001/")]
        assert len(first_action) == 1 + 2 + 1 + 3, f"{len(first_action)} records for one action"
        assert [r["hop_index"] for r in first_action] == [0, 0, 1, 0, 0, 1, 2], \
            [r["hop_index"] for r in first_action]
        report["hop_records"] = len(adapter.hops)
        return f"{len(adapter.hops)} records, enforcement_point {adapter.declared_marker}"

    @case("the delegation-chain corpus (P13): every action names an actor and a whole chain")
    def _corpus():
        actions = [baseline] + [drive(adapter, i) for i in range(2, min_actions + 1)]
        counters = check_corpus(actions)
        report.update({k: v for k, v in counters.items() if k != "findings"})
        report["findings"] = counters["findings"][:5]
        assert counters["actions_checked"] >= min_actions, counters["actions_checked"]
        for counter in ("missing_subject", "short_chains", "cyclic", "executing_unit_mismatch"):
            assert counters[counter] == 0, f"{counter}={counters[counter]}: {counters['findings'][:2]}"
        return (f"actions_checked={counters['actions_checked']} missing_subject=0 short_chains=0 "
                f"cyclic=0 executing_unit_mismatch=0")

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report.update({"attestations": adapter.attestations, "exchanges": adapter.exchanges,
                   "verifications": adapter.verifications, "refusals": adapter.refusals,
                   "authority_calls": adapter.authority_calls,
                   "breakage_honoured": adapter.honours_forward_break,
                   "product_hits": product_scan(HERE)[0]})
    report.setdefault("actions_checked", 0)
    for counter in ("missing_subject", "short_chains", "cyclic", "executing_unit_mismatch"):
        report.setdefault(counter, -1)
    return cases, report


def _hop(pair):
    from interface import Hop
    return Hop(pair[0], pair[1])


def product_scan(root: str) -> tuple[int, list]:
    """Product names may live in adapters/ and in README.md's env table. Nowhere else.

    Code is what is scanned (.py and .sh): trust.json is data no code branches on,
    and plan-entry.json is the plan row the orchestrator merges, where naming the
    swap candidate is the point.
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
    ap = argparse.ArgumentParser(description="Conformance run for the identity interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--min-actions", type=int, default=int(os.environ.get("MIN_ACTIONS", "50")))
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
        cases, report = run(name, args.min_actions)
        report["adapters_run"] = len(args.adapter or ["dryrun"])
        print(f"# binding {name} ({report['root_of_trust']} / {report['verification_locus']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['entity']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"actions_checked={report['actions_checked']} short_chains={report['short_chains']} "
              f"cyclic={report['cyclic']} executing_unit_mismatch={report['executing_unit_mismatch']} "
              f"authority_calls={report['authority_calls']} marker={report['marker']} "
              f"product_hits={report['product_hits']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s), selected_by=configuration")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
