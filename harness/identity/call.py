#!/usr/bin/env python3
"""The minimal call: one unit of work gets an identity, exchanges it for one
downstream call, and a hop that asks for more is refused.

    ADAPTER=dryrun python3 harness/identity/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling, the
idempotency key and the actor onto the envelope without being asked, presents
what arrived at the door, and binds one of three adapters from one environment
variable. The caller never builds an actor: an actor here is what verify and
attest returned.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (AttestRequest, Credential, DelegationRequest, Problem,  # noqa: E402
                       credential_as_dict)
from adapters.dryrun import ExchangeIssuingAdapter                             # noqa: E402
from adapters.live import LiveIssuerAdapter                                    # noqa: E402
from adapters.second import AttestedWorkloadAdapter                            # noqa: E402

ADAPTERS = {"dryrun": ExchangeIssuingAdapter, "live": LiveIssuerAdapter,
            "second": AttestedWorkloadAdapter}


def envelope(adapter) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here.

    The presented credential is what arrived at the door from outside the
    platform; the caller does not mint it and cannot read what is behind it.
    """
    principal = os.environ.get("PRINCIPAL", "user:corey")
    key = "idem-" + hashlib.sha256(principal.encode()).hexdigest()[:24]
    corr = "corr-" + key[5:17]
    os.environ.setdefault("CORRELATION_ID", corr)
    os.environ.setdefault("RUN_ID", "run-" + key[5:17])
    presented = adapter.fixture_presented(principal, ["read:incident", "call:model", "write:ledger"],
                                          "svc:platform", 3600, "direct")
    wide = os.environ.get("WIDEN_SCOPE", "deploy:prod")
    return {
        "envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
        "actor": {"subject": principal,
                  "delegation_chain": [{"actor": principal, "obtained_via": "direct"}]},
        "intent": {"workflow_ref": "harness/identity",
                   "summary": "one unit of work acts for a principal, one hop at a time"},
        "correlation": {"run_id": os.environ["RUN_ID"], "correlation_id": corr},
        "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "200000")),
                   "currency": "USD", "on_exceed": "terminate_unit"},
        "idempotency_key": key,
        "payload": {
            "presented_credential": presented,
            "intake_unit": {"unit": "service:intake", "audience": "svc:planner",
                            "scope": ["read:incident", "call:model"], "lifetime_s": 1800,
                            "platform_facts": {"cell": "cell-04", "image_digest": "sha256:1f2e", "uid": 61001},
                            "presented": adapter.fixture_presented(
                                "service:intake", ["read:incident", "call:model"], "svc:planner", 1800,
                                "direct")},
            "worker_unit": {"unit": "agent:worker-7", "audience": "svc:model-gateway",
                            "scope": ["call:model"], "lifetime_s": 900,
                            "platform_facts": {"cell": "cell-11", "image_digest": "sha256:9ab3", "uid": 61007},
                            "presented": adapter.fixture_presented(
                                "agent:worker-7", ["call:model"], "svc:model-gateway", 900, "direct")},
            "first_hop": {"scope": ["read:incident", "call:model"], "audience": "svc:planner",
                          "lifetime_s": 1200},
            "second_hop": {"scope": ["call:model"], "audience": "svc:model-gateway", "lifetime_s": 300},
            "widening_hop": {"scope": ["call:model", wide], "audience": "svc:deployer", "lifetime_s": 300},
        },
    }


def hop(ask: dict, name: str, subject: Credential, actor: Credential) -> DelegationRequest:
    """One hop of the chain, from the envelope the platform stamped."""
    return DelegationRequest.from_dict(dict(ask["payload"][name], subject=subject, actor=actor))


def unit(ask: dict, name: str, **extra) -> AttestRequest:
    return AttestRequest.from_dict(dict(ask["payload"][name], **extra))


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(adapter, steps, token: Credential, refusal: Problem) -> int:
    """Presentation, so the caller region below is calls and results only."""
    table([(label, cred.actor, len(cred.chain), " ".join(cred.scope), cred.audience,
            cred.remaining_s()) for label, cred in steps],
          ("step", "current actor", "hops", "scope", "audience", "seconds left"))
    print("\ndelegation chain on the issued credential, current actor first:")
    for index, link in enumerate(credential_as_dict(token)["chain"]):
        print(f"  hop {index}  {link['actor']:<24} obtained_via {link['obtained_via']}")
    print("\nthe hop that asked for more (application/problem+json):")
    print(json.dumps(refusal.body, indent=2))
    print(f"\nverifications {adapter.verifications}  attestations {adapter.attestations}  "
          f"exchanges {adapter.exchanges}  refusals {adapter.refusals}  "
          f"authority calls {adapter.authority_calls}")
    return 0


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all the harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()    # configuration, not code
    try:
        ask = envelope(adapter)
        principal = adapter.verify(ask["payload"]["presented_credential"])   # never constructed here
        intake = adapter.attest(unit(ask, "intake_unit"))
        first = adapter.delegate(hop(ask, "first_hop", principal, intake))
        worker = adapter.attest(unit(ask, "worker_unit", vouched_by=intake))
        token = adapter.delegate(hop(ask, "second_hop", first, worker))
    except Problem as problem:                  # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    try:
        adapter.delegate(hop(ask, "widening_hop", token, worker))
    except Problem as refusal:                  # the hop that asks for more is refused
        return show(adapter, [("verify", principal), ("attest", intake), ("delegate", first),
                              ("attest", worker), ("delegate", token)], token, refusal)
    print("FAIL: a hop widened its scope and was granted")
    return 1


if __name__ == "__main__":
    sys.exit(main())
