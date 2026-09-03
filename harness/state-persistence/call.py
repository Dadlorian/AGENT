#!/usr/bin/env python3
"""The minimal call: put a record, read it pinned, prove it, and race two writers.

    ADAPTER=dryrun python3 harness/state-persistence/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling,
the idempotency key and the actor onto the envelope without being asked
(F-b4-01, cap-consumption), and it binds one of three adapters from one
environment variable. This capability's own concurrency control is the
expected head and the fencing token, not the envelope's idempotency key, which
is why the key is stamped but never read below the marker.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import AppendRequest, Head, Problem, verify_inclusion_proof         # noqa: E402
from adapters.dryrun import DryRunAdapter                                          # noqa: E402
from adapters.live import LiveLedgerAdapter                                        # noqa: E402
from adapters.second import ObjectStoreAdapter                                     # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveLedgerAdapter, "second": ObjectStoreAdapter}


def envelope(partition: str, body: dict) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    key = "idem-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]
    corr = "corr-" + key[5:17]
    actor = os.environ.get("ACTOR", "user:corey")
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/state-persistence", "summary": "one record, pinned, proved"},
            "correlation": {"run_id": "run-" + key[5:17], "correlation_id": corr},
            "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "0")), "currency": "USD",
                      "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": {"partition": partition, "body": body}}


def request(partition: str, kind: str, body: dict, head: Head) -> dict:
    """A caller's write, shaped from the head it last resolved."""
    return {"partition": partition, "kind": kind, "body": body, "fencing_token": head.size + 1,
            "expected_head": head.chain_digest if head.size else None}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(partition, rec1, pinned, verified, no_fork) -> int:
    table([(partition, rec1.record_id[:19] + "...", len(pinned), verified, no_fork)],
          ("partition", "record_id", "records_at_pin", "proof_verified", "no_fork"))
    return 0


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all five harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()   # configuration, not code
    partition = os.environ.get("PARTITION", "demo")
    text = os.environ.get("BODY", "one opaque record")
    try:
        h0 = adapter.resolve_head(partition)
        rec1, h1 = adapter.append(AppendRequest.from_dict(request(partition, "note", {"text": text}, h0)))
        rec2, h2 = adapter.append(AppendRequest.from_dict(request(partition, "note", {"text": "a later write"}, h1)))
        pinned = adapter.read_at(partition, h1)                 # h1 is pinned: rec2 must not appear
        verified = verify_inclusion_proof(adapter.prove(partition, rec1.record_id, h1))
        adapter.append(AppendRequest.from_dict(request(partition, "note", {"text": "writer A"}, h2)))
        try:                                                    # writer B raced writer A for the same head
            adapter.append(AppendRequest.from_dict(request(partition, "note", {"text": "writer B"}, h2)))
            no_fork = False
        except Problem:
            no_fork = True
    except Problem as problem:                                  # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    return show(partition, rec1, pinned, verified, no_fork)


if __name__ == "__main__":
    sys.exit(main())
