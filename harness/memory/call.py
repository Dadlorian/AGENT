#!/usr/bin/env python3
"""The minimal call: write one item under a scope and an expiry, recall it,
and show an expired item and a cross-scope item are both excluded.

    ADAPTER=dryrun python3 harness/memory/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling,
the idempotency key and the actor onto the envelope without being asked
(F-b4-01, cap-consumption), and it binds one of three adapters from one
environment variable. "The same recall from both stores" is shown by running
this file once per binding (test.sh does exactly that) and diffing the table.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import Problem, RecallQuery, RememberRequest        # noqa: E402
from adapters.dryrun import DryRunAdapter                          # noqa: E402
from adapters.live import LiveMemoryAdapter                        # noqa: E402
from adapters.second import ScopeKeyedFileAdapter                  # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveMemoryAdapter, "second": ScopeKeyedFileAdapter}


def envelope(kind: str, body: dict) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    key = "idem-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]
    corr = "corr-" + key[5:17]
    actor = os.environ.get("ACTOR", "user:corey")
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/memory", "summary": "write, recall, expire, scope"},
            "correlation": {"run_id": "run-" + key[5:17], "correlation_id": corr},
            "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "0")), "currency": "USD",
                      "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": body}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by test.sh, the same method every harness in this repo uses.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()   # configuration, not code
    env = envelope("remember", {})
    corr, actor = env["correlation"]["correlation_id"], env["actor"]["subject"]
    mine, other = {"principal": actor}, {"agent": "agent:release-reviewer"}
    try:
        mine_item = adapter.remember(RememberRequest.from_dict(
            {"scope": mine, "kind": "semantic", "body": {"claim": "the deploy window is Tuesdays"},
             "produced_by": actor, "correlation_id": corr, "expires_at": "2099-01-01T00:00:00Z"}))
        other_item = adapter.remember(RememberRequest.from_dict(
            {"scope": other, "kind": "semantic", "body": {"claim": "not this run's scope"},
             "produced_by": "agent:release-reviewer", "correlation_id": corr, "expires_at": "2099-01-01T00:00:00Z"}))
        expired_item = adapter.remember(RememberRequest.from_dict(
            {"scope": mine, "kind": "episodic", "body": {"claim": "already stale"},
             "produced_by": actor, "correlation_id": corr, "expires_at": "2020-01-01T00:00:00Z"}))
        result = adapter.recall(RecallQuery.from_dict({"scope": mine, "limit": 10}))
        ids = {it.memory_id for it in result.items}
        recalled_mine = mine_item.memory_id in ids
        expired_excluded = expired_item.memory_id not in ids
        cross_scope_excluded = other_item.memory_id not in ids
    except Problem as problem:
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    table([(adapter.role, recalled_mine, expired_excluded, cross_scope_excluded, len(result.items))],
          ("binding", "recalled_own_scope", "expired_excluded", "cross_scope_excluded", "items_returned"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
