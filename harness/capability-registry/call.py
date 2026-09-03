#!/usr/bin/env python3
"""The minimal call: publish one signed record, resolve it, verify its digest,
show it cannot be edited in place, roll back, and refuse a bad signature.

    ADAPTER=dryrun python3 harness/capability-registry/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it builds the entry envelope (cap-consumption
shape), stamps the correlation id, the budget ceiling, the idempotency key and
the actor onto it without being asked (F-b4-01, F-b1-08), and binds one of
three adapters from one environment variable. There is no publish flag beyond
naming the package: a caller sends what it was already sending.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import PublishRequest, Query, Problem, digest_of              # noqa: E402
from adapters.dryrun import SignedIndexAdapter                               # noqa: E402
from adapters.live import LiveSkillFilesAdapter                              # noqa: E402
from adapters.second import ContentAddressedFetchAdapter                     # noqa: E402

ADAPTERS = {"dryrun": SignedIndexAdapter, "live": LiveSkillFilesAdapter, "second": ContentAddressedFetchAdapter}
NAMESPACE = os.environ.get("REGISTRY_NAMESPACE", "acme")
NAME = os.environ.get("PACKAGE_NAME", "widget")


def envelope(payload: dict) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    actor = os.environ.get("ACTOR", "user:corey")
    key = "idem-" + digest_of(json.dumps(payload, sort_keys=True).encode())[7:31]
    corr = {"run_id": os.environ.get("RUN_ID", "run-" + key[5:17]),
            "correlation_id": os.environ.get("CORRELATION_ID", "corr-" + key[5:17])}
    payload = {**payload, "actor": actor, "correlation": corr}
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor}, "intent": {"workflow_ref": "harness/capability-registry"},
            "correlation": corr,
            "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "200000")),
                       "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": payload}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(rec1, resolved, verified, rerun, rolled_back, forged) -> int:
    table([(f"{rec1.namespace}/{rec1.name}", resolved.record.version, verified.digest_matched,
            "no (refused)" if rerun is None else "??", rolled_back.record.version, "no" if not forged else "YES")],
          ("package", "resolved to", "digest matches", "in-place edit accepted", "rolled back to", "forged signature accepted"))
    return 0 if verified.digest_matched and rerun is None and not forged else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()      # configuration, not code
    package_v1 = os.environ.get("PACKAGE_BYTES", "one input line").encode()
    ask1 = envelope({"namespace": NAMESPACE, "name": NAME, "version": "1.0.0", "kind": "capability",
                     "package_bytes_hex": package_v1.hex(), "good_at": ["a worked example twenty chars"]})
    try:
        record1 = adapter.publish(PublishRequest.from_dict(ask1["payload"]))
        resolved = adapter.resolve(Query(f"{NAMESPACE}/{NAME}", ">=1.0.0 <2.0.0"))
        verified = adapter.verify(resolved.record)
        package_v2 = package_v1 + b" v2"
        ask2 = envelope({"namespace": NAMESPACE, "name": NAME, "version": "1.1.0", "kind": "capability",
                         "package_bytes_hex": package_v2.hex(), "rollback_to": "1.0.0"})
        record2 = adapter.publish(PublishRequest.from_dict(ask2["payload"]))
        rerun = None
        try:
            adapter.publish(PublishRequest.from_dict(ask1["payload"]))       # the in-place-edit attempt
            rerun = "accepted"
        except Problem:
            pass                                                             # refused: immutable
        rolled_back = adapter.resolve(Query(f"{NAMESPACE}/{NAME}", f"=={record2.rollback_to}"))
        forged = copy.deepcopy(record2)
        forged.signature = "f" * 64
        forged_result = adapter.verify(forged)
    except Problem as problem:                                     # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    return show(record1, resolved, verified, rerun, rolled_back, forged_result.signature_verified)


if __name__ == "__main__":
    sys.exit(main())
