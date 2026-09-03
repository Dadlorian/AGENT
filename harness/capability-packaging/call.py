#!/usr/bin/env python3
"""The minimal call: discover a package by name, read it at every tier, refuse a
broken one, then show the same package resolved by digest from the second loader.

    ADAPTER=dryrun python3 harness/capability-packaging/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it stamps the correlation id, the budget ceiling, the
idempotency key and the actor onto the envelope without being asked (F-b4-01),
and it binds one of three adapters from one environment variable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import PackageRequest, Problem, resolution_as_dict          # noqa: E402
from adapters.dryrun import DryRunAdapter                                  # noqa: E402
from adapters.live import LiveSkillFilesAdapter                            # noqa: E402
from adapters.second import RegistryAdapter                                # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveSkillFilesAdapter, "second": RegistryAdapter}


def envelope(identity: str, trigger: str, reference_path: str) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    body = {"identity": identity, "trigger": trigger, "reference_path": reference_path}
    key = "idem-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]
    corr = "corr-" + key[5:17]
    os.environ.setdefault("CORRELATION_ID", corr)
    os.environ.setdefault("RUN_ID", "run-" + key[5:17])
    actor = os.environ.get("ACTOR", "user:corey")
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/capability-packaging", "summary": "load one package by identity"},
            "correlation": {"run_id": os.environ["RUN_ID"], "correlation_id": corr},
            "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "50000")),
                      "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": body}


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(ask, found, resolution, refusal, second) -> int:
    """Presentation, so the caller region below is calls and results only."""
    table([(ask["kind"], found["identity"], found["name"], resolution.source,
            ",".join(resolution.tiers_loaded), resolution.digest)],
          ("entry", "identity", "name", "source", "tiers_loaded", "digest"))
    print("\nresident fields discovered:", json.dumps(found))
    print("\nrefused (application/problem+json):")
    print(json.dumps(refusal, indent=2))
    print("\nsame identity, second loader, resolved by digest:")
    print(json.dumps(resolution_as_dict(second), indent=2) if second is not None
          else "  not mirrored in the second loader's fixture set (identity-space mismatch, live mode only)")
    return 0


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()    # configuration, not code
    ask = envelope(os.environ.get("IDENTITY", "quickstart-parser"),
                   os.environ.get("TRIGGER", "a request names a starter template"),
                   os.environ.get("REFERENCE_PATH", "references/schema.md"))
    try:
        req = PackageRequest.from_dict(ask["payload"])
        found = next((e for e in adapter.list_resident() if e["identity"] == req.identity), None)
        if found is None:
            adapter.resolve(req.identity)             # not listed -> raises the typed refusal
        resolution = adapter.load_body(req.identity, req.trigger)          # tiers 1 + 2
        opened = adapter.open_reference(req.identity, req.reference_path)  # tier 3, its own resolve()
        resolution.reference, resolution.tiers_loaded = opened.reference, resolution.tiers_loaded + ["reference"]
        try:
            adapter.resolve(os.environ.get("BROKEN_IDENTITY", "broken-legacy-importer"))
            raise AssertionError("the broken fixture resolved; the refusal path was not exercised")
        except Problem as caught:                         # one refusal shape, branched on type
            refusal = caught.body                         # Python clears the name after `except`
        try:
            second = ADAPTERS["second"]().resolve(req.identity)            # the second loader, by digest
        except Problem:
            second = None                                 # this identity is not in that source's fixtures
    except Problem as problem:
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    return show(ask, found, resolution, refusal, second)


if __name__ == "__main__":
    sys.exit(main())
