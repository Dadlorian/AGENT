#!/usr/bin/env python3
"""The minimal call: admit one unit of work under one principal.

    ADAPTER=dryrun python3 harness/xc-tenancy/call.py
    ADAPTER=dryrun,second python3 harness/xc-tenancy/call.py   the same five steps from both enforcement points

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling,
the idempotency key and the actor's principal onto the envelope without
being asked, and binds an adapter from one environment variable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import Problem, ScopeRequest                                # noqa: E402
from adapters.dryrun import DryRunTenancyAdapter                           # noqa: E402
from adapters.live import LiveTenancyAdapter                               # noqa: E402
from adapters.second import DatabasePerTenantAdapter                       # noqa: E402

ADAPTERS = {"dryrun": DryRunTenancyAdapter, "live": LiveTenancyAdapter, "second": DatabasePerTenantAdapter}
TENANT_A, TENANT_B = "tenant-northwind", "tenant-acme"


def bindings() -> list:
    """Configuration, not code: one name, or several to ask them the same question."""
    return [ADAPTERS[name]() for name in os.environ.get("ADAPTER", "dryrun").split(",")]


def envelope(operation: str, actor_id: str, principal: str | None, **payload) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    key = "idem-" + hashlib.sha256(f"{actor_id}{principal}{operation}".encode()).hexdigest()[:24]
    dispatch = "disp-" + key[5:17]
    actor = {"id": actor_id}
    if principal:
        actor["principal"] = principal
    payload_doc = {"operation": operation, "actor": actor,
                   "context": {"run_id": "run-" + key[5:17], "root_dispatch_id": dispatch}, **payload}
    os.environ.setdefault("CORRELATION_ID", "corr-" + key[5:17])
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"), "actor": actor,
            "intent": {"workflow_ref": "harness/xc-tenancy", "summary": "one unit scoped to one principal"},
            "correlation": {"run_id": payload_doc["context"]["run_id"], "correlation_id": os.environ["CORRELATION_ID"]},
            "budget": {"ceiling_micros": 500_000, "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": payload_doc}


def report(problem: Problem) -> int:
    print("PROBLEM (application/problem+json):")
    print(json.dumps(problem.body, indent=2))
    return 2


def show(rows: list) -> None:
    header = ("binding", "step", "principal", "outcome", "kind")
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    by_step = {}
    for binding, step, _principal, _outcome, kind in rows:
        by_step.setdefault(step, set()).add(kind)
    agree = all(len(kinds) == 1 for kinds in by_step.values())
    print(f"\nsteps={len(by_step)} bindings={len({r[0] for r in rows})} scoping_decisions_agree={str(agree).lower()}")


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all the harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    steps = [("write", "write", TENANT_A, {"key": "doc-a", "value": "northwind's record"}),
             ("read-own", "read", TENANT_A, {"key": "doc-a"}),
             ("spend", "spend", TENANT_A, {"amount_micros": 1200}),
             ("read-cross", "read", TENANT_B, {"key": "doc-a"}),
             ("noprincipal", "read", None, {"key": "doc-a"})]
    rows, code = [], 0
    for adapter in bindings():                                     # configuration, not code
        for step, op, principal, payload in steps:
            ask = envelope(op, "user:corey", principal, **payload)
            try:
                record, outcome = adapter.admit(ScopeRequest.from_dict(ask["payload"]))
                rows.append((adapter.entity, step, record.principal, outcome, "ok"))
            except Problem as problem:                              # one refusal shape, branched on type
                code = report(problem)
                kind = problem.body["type"].rsplit(":", 1)[1]
                rows.append((adapter.entity, step, principal or "(none)", kind, kind))
    show(rows)
    return code


if __name__ == "__main__":
    sys.exit(main())
