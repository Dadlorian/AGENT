#!/usr/bin/env python3
"""Dry-run adapter: a local signed envelope, in process, no network, no clock.

The same bytes every run, so a gate can assert on them. Authority comes from
possession of a key this deployment holds; the envelope is appended beside the
existing record in a hash-chained file, never in place of it, so every reader of
the record keeps working and the migration is revertible by not reading the new
file (cap-provenance-implement instruction 2).

It declares log inclusion proofs unsupported rather than reporting zero of them.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import (AttestRequest, Envelope, Location, Problem, ProvenanceAdapter,
                       canonical, digest_of)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELD_KEY = hashlib.sha256(b"harness/provenance dry-run held key").digest()


class LocalSignedRecordAdapter(ProvenanceAdapter):
    adapter_kind = "local-signed-jsonl"
    entity = "append-only hash-chained records, signed with a key this deployment holds"
    signer_authority = "possession"
    key_lifetime = "long-lived"
    store_kind = "hash-chained jsonl"
    material_source = "out-of-band trust policy"
    offline_capable = True
    supports_inclusion_proof = False
    declared_gaps = ("log inclusion proofs are unsupported, not zero: a third party must trust that the "
                     "file it was handed is the file that was written",
                     "the signing key does not expire, so revocation is an operational act, not a deadline")

    def __init__(self, path: str | None = None):
        super().__init__()
        self.path = path or os.path.join(HERE, "out", "dryrun-attestations.jsonl")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        open(self.path, "w").close()          # a dry run starts from an empty store
        self.head = "genesis"

    # --- signing -------------------------------------------------------------
    def _signer(self, request: AttestRequest) -> tuple:
        if os.environ.get("PROVENANCE_FAIL") == "1":     # the failure path, exercised on demand
            raise Problem("adapter-unavailable",
                          "the signing key is unreadable (PROVENANCE_FAIL=1); no statement was emitted and "
                          "no envelope was written",
                          retry_after_s=1)
        return "local-held-key-v1", HELD_KEY, {
            "keyid": "local-held-key-v1", "authority": "possession of a key this deployment holds",
            "expires": None}

    # --- the store: the envelope beside the record, chained ------------------
    def _append(self, statement_id: str, envelope: Envelope, request: AttestRequest, bound: dict) -> None:
        record = {"id": statement_id, "prev": self.head, "envelope": envelope.to_dict(),
                  "subjects": [s.digest for s in request.subjects],
                  "actor": bound["actor"], "code_version": bound["code_version"],
                  "correlation": request.correlation}
        record["hash"] = hashlib.sha256(canonical(record)).hexdigest()
        with open(self.path, "a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        self.head = record["hash"]

    def _records(self) -> list:
        with open(self.path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def resolve(self, subject_digest: str) -> list:
        return [r["envelope"] for r in self._records() if subject_digest in r["subjects"]]

    def publish(self, receipt) -> Location:
        return Location(uri=f"attestation:{self.adapter_kind}/{receipt.statement_id}",
                        store="a file a third party is handed", inclusion_proof=None)

    def fetch(self, uri: str) -> dict:
        want = uri.rsplit("/", 1)[-1]
        for record in self._records():
            if record["id"] == want:
                return {"envelope": record["envelope"], "inclusion_proof": None,
                        "verification_material": {"keyid": "local-held-key-v1", "material": None,
                                                  "issuer": None,
                                                  "note": "held key; the verifier is given it out of band"}}
        raise Problem("adapter-unavailable", f"no envelope at {uri}", retry_after_s=30)

    def verifying_material(self, keyid: str) -> dict:
        return {"keyid": keyid, "material": HELD_KEY.hex(), "issuer": None,
                "source": "out of band: the deployment that holds the key hands the verifier a trust policy"}

    def store_integrity(self) -> dict:
        records, prev, broken = self._records(), "genesis", 0
        for record in records:
            body = {k: v for k, v in record.items() if k != "hash"}
            if record["prev"] != prev or hashlib.sha256(canonical(body)).hexdigest() != record["hash"]:
                broken += 1
            prev = record["hash"]
        return {"kind": self.store_kind, "head": prev, "entries": len(records), "verified": broken == 0,
                "checked_by": "our own reader, which is integrity for us and evidence for nobody else"}


# The one name every adapter module exports: the entry point of this module.
Adapter = LocalSignedRecordAdapter
