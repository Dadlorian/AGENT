#!/usr/bin/env python3
"""The minimal call: validate one document, read one typed outcome.

    ADAPTER=dryrun python3 harness/document-validation/call.py

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
from interface import DIALECT_2020_12, Problem, ValidationRequest         # noqa: E402
from adapters.dryrun import DryRunAdapter                                 # noqa: E402
from adapters.live import LiveSchemaStoreAdapter                          # noqa: E402
from adapters.second import CompiledSchemaAdapter                         # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveSchemaStoreAdapter, "second": CompiledSchemaAdapter}

DEFAULT_SCHEMA = "examples/end-to-end/schemas/entry.schema.json"
VALID_ENVELOPE = {
    "envelope_version": "0.1", "kind": "human", "entry_id": "harness-docvalid-call-0001",
    "occurred_at": "2026-09-03T00:00:00Z",
    "actor": {"subject": "user:corey", "delegation_chain": [{"actor": "user:corey", "obtained_via": "direct"}]},
    "intent": {"workflow_ref": "harness/document-validation", "summary": "one document validated"},
    "correlation": {"run_id": "run-docvalid-call", "correlation_id": "corr-docvalid-call"},
    "budget": {"ceiling_micros": 0, "currency": "USD", "on_exceed": "terminate_unit"},
    "idempotency_key": "idem-docvalid-call-000001", "payload": {}}
MALFORMED_ENVELOPE = {k: v for k, v in VALID_ENVELOPE.items() if k != "actor"}   # actor is required


def envelope(schema_uri: str, instance_kind: str) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    instance = VALID_ENVELOPE if instance_kind == "valid" else MALFORMED_ENVELOPE
    body = {"schema_uri": schema_uri, "dialect": DIALECT_2020_12, "instance": instance}
    key = "idem-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:24]
    corr = "corr-" + key[5:17]
    os.environ.setdefault("CORRELATION_ID", corr)
    os.environ.setdefault("RUN_ID", "run-" + key[5:17])
    actor = os.environ.get("ACTOR", "user:corey")
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/document-validation", "summary": "check one document against its schema"},
            "correlation": {"run_id": os.environ["RUN_ID"], "correlation_id": corr},
            "budget": {"ceiling_micros": 0, "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": body}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(outcome) -> int:
    """Presentation, so the caller region below is calls and results only."""
    first = outcome.errors[0].as_dict() if outcome.errors else {}
    table([(outcome.valid, outcome.dialect, outcome.schema_uri, len(outcome.errors),
            first.get("instance_location", ""), first.get("message", ""))],
          ("valid", "dialect", "schema_uri", "error_count", "first_pointer", "first_message"))
    return 0


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted directly by test.sh below this marker, the same MARKER convention
# harness/caller_lines.py applies to the other four harnesses in this tree.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()          # configuration, not code
    ask = envelope(os.environ.get("SCHEMA_URI", DEFAULT_SCHEMA), os.environ.get("INSTANCE_KIND", "malformed"))
    try:
        outcome = adapter.validate(ValidationRequest.from_dict(ask["payload"]))
    except Problem as problem:                                        # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    return show(outcome)


if __name__ == "__main__":
    sys.exit(main())
