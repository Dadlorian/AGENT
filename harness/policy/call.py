#!/usr/bin/env python3
"""The minimal call: one decision for one unit of work, before anything is spent.

    ADAPTER=dryrun python3 harness/policy/call.py
    ADAPTER=dryrun,second python3 harness/policy/call.py   the same decision from both engines

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling, the
idempotency key, the actor and its tenant onto the envelope without being asked
(F-b4-01), pins the policy version, and binds an adapter from one environment
variable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import DecisionRequest, Problem, digest_of, load_bundle      # noqa: E402
from adapters.dryrun import DryRunPolicyAdapter                            # noqa: E402
from adapters.live import LivePolicyAdapter                                # noqa: E402
from adapters.second import TypedEntityPolicyAdapter                       # noqa: E402

ADAPTERS = {"dryrun": DryRunPolicyAdapter, "live": LivePolicyAdapter, "second": TypedEntityPolicyAdapter}


def bindings() -> list:
    """Configuration, not code: one name, or several to ask them the same question."""
    return [ADAPTERS[name]() for name in os.environ.get("ADAPTER", "dryrun").split(",")]


def envelope() -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    tenant = os.environ.get("TENANT", "tenant-acme")
    actor = os.environ.get("ACTOR", "user:corey")
    key = "idem-" + hashlib.sha256(f"{actor}{tenant}{os.environ.get('SCOPE', 'internal')}".encode()).hexdigest()[:24]
    dispatch = "disp-" + key[5:17]
    subject = {"id": actor, "tenant": tenant,
               "delegation_chain": [{"actor": actor, "obtained_via": "direct"}],
               "mandates": ["mandate:external-tool"] if os.environ.get("MANDATE") else []}
    resource = {"tenant": os.environ.get("RESOURCE_TENANT", tenant),
                "tool": os.environ.get("TOOL", "tool:web-fetch"),
                "scope": os.environ.get("SCOPE", "internal")}
    if os.environ.get("QUERY"):          # a free-form point: a different resource shape
        resource = {"tenant": resource["tenant"], "query": os.environ["QUERY"]}
    payload = {"decision_point": os.environ.get("POINT", "dispatch.tool_call"),
               "subject": subject, "action": os.environ.get("ACTION", "invoke"),
               "resource": resource,
               "context": {"run_id": "run-" + key[5:17], "root_dispatch_id": dispatch},
               "policy_version": os.environ.get("VERSION", digest_of(load_bundle()))}
    if os.environ.get("DECLINE"):        # the refusal demo: a caller trying to turn the gate off
        payload["enforce"] = False
    os.environ.setdefault("CORRELATION_ID", "corr-" + key[5:17])
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": subject, "intent": {"workflow_ref": "harness/policy", "summary": "one decision for one unit of work"},
            "correlation": {"run_id": payload["context"]["run_id"], "correlation_id": os.environ["CORRELATION_ID"]},
            "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "200000")),
                       "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": payload}


def work_for(ask: dict):
    """The unit of work. It is reachable only on the far side of an allow, and
    every metered call it makes is charged through the meter it is handed."""
    dispatch = ask["payload"]["context"]["root_dispatch_id"]

    def work(meter):
        meter.charge(dispatch, 1200)          # the first metered call of this dispatch
        return f"unit of work ran, {meter.spend(dispatch)} micros metered"
    return work


def report(problem: Problem) -> int:
    print("PROBLEM (application/problem+json):")
    print(json.dumps(problem.body, indent=2))
    return 2


def show(ask: dict, rows: list) -> None:
    header = ("binding", "effect", "rule_id", "policy_version", "spend_micros", "outcome")
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    seen = {(r[1], r[2]) for r in rows}
    print(f"\nentry={ask['kind']} decision_point={ask['payload']['decision_point']} "
          f"bindings={len(rows)} decisions_agree={str(len(seen) == 1).lower()}")


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all the harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    ask = envelope()
    try:
        request = DecisionRequest.from_dict(ask["payload"])   # a bypass field never gets past this
    except Problem as problem:
        return report(problem)
    rows, code = [], 0
    for adapter in bindings():                                # configuration, not code
        try:
            decision, outcome = adapter.admit(request, work_for(ask))
            rows.append((adapter.entity, decision.effect, decision.rule_id,
                         decision.policy_version[:14], adapter.meter.spend(), outcome))
        except Problem as problem:                            # one refusal shape, branched on type
            code = report(problem)
            rows.append((adapter.entity, "refused", problem.body.get("rule_id", "-"),
                         problem.body["type"].rsplit(":", 1)[1],
                         problem.body.get("spend_delta_micros", 0), problem.body["detail"][:44]))
    show(ask, rows)
    return code


if __name__ == "__main__":
    sys.exit(main())
