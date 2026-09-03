#!/usr/bin/env python3
"""The minimal call: one signed statement over one artifact, checked from the envelope alone.

    ADAPTER=dryrun python3 harness/provenance/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it produces the run's build record, stamps the
correlation id, the budget ceiling, the idempotency key and the actor onto the
envelope without being asked (F-b4-01, F-b1-08), and binds one of three
adapters from one environment variable. There is no attest flag: a caller sends
what it was already sending.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (AttestRequest, PREDICATE_BUILD, Problem, TrustPolicy,  # noqa: E402
                       digest_of)
from adapters.dryrun import LocalSignedRecordAdapter                          # noqa: E402
from adapters.live import LiveEvidenceStoreAdapter                            # noqa: E402
from adapters.second import KeylessTransparencyLogAdapter                     # noqa: E402

ADAPTERS = {"dryrun": LocalSignedRecordAdapter, "live": LiveEvidenceStoreAdapter,
            "second": KeylessTransparencyLogAdapter}
HERE = os.path.dirname(os.path.abspath(__file__))
CLOCK = os.environ.get("PROVENANCE_CLOCK", "2026-09-03T00:00:00Z")


def code_version() -> dict:
    """What produced it: the script hashes and the commit, as the evidence store already records."""
    scripts = {n: hashlib.sha256(open(os.path.join(HERE, n), "rb").read()).hexdigest()
               for n in ("call.py", "interface.py")}
    return {"scripts_sha256": scripts, "git_commit": os.environ.get("GIT_COMMIT", "unset"),
            "interface_version": "0.1"}


def build(source: bytes) -> bytes:
    """The run: one input in, one artifact out. Deterministic, so a gate can assert on it."""
    return b"report: " + hashlib.sha256(source).hexdigest().encode() + b"\n"


def envelope(artifact: bytes, source: bytes) -> dict:
    """One entry envelope (cap-consumption shape). The stamps are applied here."""
    actor = os.environ.get("ACTOR", "user:corey")
    key = "idem-" + digest_of(artifact)[7:31]
    corr = {"run_id": os.environ.get("RUN_ID", "run-" + key[5:17]),
            "correlation_id": os.environ.get("CORRELATION_ID", "corr-" + key[5:17])}
    predicate = {"builder": {"id": "harness/provenance", "actor": actor,
                             "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
                 "code_version": code_version(),
                 "materials": [{"name": "source", "digest": digest_of(source)}],
                 "invocation": {"workflow_ref": "harness/provenance", "correlation": corr,
                                "decision_refs": ["budget:ceiling_micros", "policy:allow"]},
                 "started_at": CLOCK, "ended_at": CLOCK}
    if os.environ.get("SKIP_PROVENANCE"):        # the refusal demo: a caller asking to opt out
        payload_extra = {"attest": False}
    else:
        payload_extra = {}
    payload = {"subjects": [{"name": "report", "digest": digest_of(artifact)}],
               "predicate_type": PREDICATE_BUILD, "predicate": predicate,
               "actor": actor, "correlation": corr, "idempotency_key": key, **payload_extra}
    return {"envelope_version": "0.1", "kind": os.environ.get("ENTRY_KIND", "human"),
            "actor": {"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/provenance", "summary": "one artifact, attested"},
            "correlation": corr,
            "budget": {"ceiling_micros": int(os.environ.get("CEILING_MICROS", "200000")),
                       "currency": "USD", "on_exceed": "terminate_unit"},
            "idempotency_key": key, "payload": payload}


def policy(adapter, keyid: str, digest: str, want_proof: bool) -> TrustPolicy:
    """The trust policy handed to a verifier: accepted signers and expected values."""
    material = adapter.verifying_material(keyid)
    accepted = ({material["keyid"]: material["material"]} if material.get("issuer") is None
                else {material["issuer"]: "accepted by issuer"})
    return TrustPolicy(accepted, {"report": digest}, (PREDICATE_BUILD,), want_proof, CLOCK)


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(ask, receipt, where, good, bad, found) -> int:
    """Presentation, so the caller region below is calls and results only."""
    table([(ask["kind"], receipt.signer["keyid"][:28], where.store[:34],
            "yes" if good.accepted else "no", "no" if not bad.accepted else "YES", len(found))],
          ("entry", "signer", "published to", "verifies", "verifies after 1 byte edited", "resolved"))
    print(f"\nstatement  {receipt.statement_id}")
    print(f"checks     {'; '.join(good.checks)}")
    print(f"one byte   {bad.reason}")
    print(f"problem    {json.dumps(bad.problem())}")
    return 0 if good.accepted and not bad.accepted else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by the same rule as harness/caller_lines.py, the one method all the
# harnesses use (conformance.py --caller-lines applies it here).
# --------------------------------------------------------------------------
def main() -> int:
    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()      # configuration, not code
    source = os.environ.get("SOURCE_TEXT", "one input line").encode()
    artifact = build(source)
    ask = envelope(artifact, source)
    try:
        receipt = adapter.attest(AttestRequest.from_dict(ask["payload"]))
        where = adapter.publish(receipt)                            # stored where a third party can fetch it
        bundle = adapter.fetch(where.uri)                           # fetched back, byte for byte
        trust = policy(adapter, receipt.signer["keyid"], digest_of(artifact), bool(where.inclusion_proof))
        good = adapter.verify(bundle["envelope"], trust, where.inclusion_proof, bundle["verification_material"])
        edited = artifact[:-1] + bytes([artifact[-1] ^ 1])          # one byte of the artifact
        bad = adapter.verify(bundle["envelope"],
                             policy(adapter, receipt.signer["keyid"], digest_of(edited),
                                    bool(where.inclusion_proof)),
                             where.inclusion_proof, bundle["verification_material"])
        found = adapter.resolve(digest_of(artifact))
    except Problem as problem:                                      # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(json.dumps(problem.body, indent=2))
        return 2
    return show(ask, receipt, where, good, bad, found)


if __name__ == "__main__":
    sys.exit(main())
