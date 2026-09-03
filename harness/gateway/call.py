#!/usr/bin/env python3
"""The minimal call: one completion by model class, under a ceiling, no vendor named.

    ADAPTER=dryrun python3 harness/gateway/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling,
the idempotency key and the actor onto the envelope without being asked
(F-b4-01), and it binds one of three adapters from one environment variable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import CompletionRequest, Problem                      # noqa: E402
from adapters.dryrun import DryRunAdapter                             # noqa: E402
from adapters.live import LiveGatewayAdapter                          # noqa: E402
from adapters.second import BatchClaimAdapter                         # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveGatewayAdapter, "second": BatchClaimAdapter}


def envelope(model_class: str, prompt: str) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    body = {"model_class": model_class, "messages": [{"role": "user", "content": prompt}]}
    if os.environ.get("VENDOR"):          # the refusal demo: a caller naming a vendor
        body["vendor"] = os.environ["VENDOR"]
    ceiling = int(os.environ.get("CEILING_MICROS", "200000"))
    key = "idem-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]
    body.update({"idempotency_key": key, "ceiling_micros": ceiling})
    corr = "corr-" + key[5:17]
    os.environ.setdefault("CORRELATION_ID", corr)          # carried on every live request header
    os.environ.setdefault("RUN_ID", "run-" + key[5:17])
    actor = os.environ.get("ACTOR", "user:corey")
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/gateway", "summary": "one completion by model class"},
            "correlation": {"run_id": os.environ["RUN_ID"], "correlation_id": corr},
            "budget": {"ceiling_micros": ceiling, "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": body}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(ask: dict, ticket) -> int:
    """Presentation, so the caller region below is calls and results only."""
    got = ticket.result
    table([(ask["kind"], ticket.model_class, ticket.state, got.cost_micros,
            ask["budget"]["ceiling_micros"] - got.cost_micros, got.cost_status)],
          ("entry", "model_class", "ticket", "cost_micros", "budget_left", "cost_status"))
    print("\n" + got.text)
    return 0


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all five harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()    # configuration, not code
    ask = envelope(os.environ.get("MODEL_CLASS", "i-fast"),
                   os.environ.get("PROMPT", "In one line: what does a routing class hide from its caller?"))
    try:
        ticket = adapter.submit(CompletionRequest.from_dict(ask["payload"]))
        while ticket.state == "pending":        # a fast path is redeemed already; a slow one is claimed
            ticket = adapter.claim(ticket)
    except Problem as problem:                  # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    return show(ask, ticket)


if __name__ == "__main__":
    sys.exit(main())
