#!/usr/bin/env python3
"""Live adapter for the evidence records running on this host today.

Product names are allowed in this file and nowhere else. Today's component for
this capability is the append-only JSONL evidence store (PASS.md A5: each record
names the script SHA-256, git commit, tree hash under test, and whether the tree
was dirty, ~2,445 records across 308 runs; F-a5-04), hash-chained so a manual
edit between runs is detectable (F-a5-03). In this repository the live instance
of that shape is kb/ledger.jsonl, appended by tools/kb.py ledger. Nothing signs
it, which is exactly the gap this adapter closes.

It wraps rather than replaces: the existing record is read (never written), put
in the predicate's evidence link, and the signed envelope is appended to a
second file beside it. Every existing reader of kb/ledger.jsonl keeps working
and the migration is revertible by not reading the new file.

Reached only through the environment variables in README.md:
  EVIDENCE_STORE         path of the live hash-chained evidence records
  ATTESTATION_STORE      path the signed envelopes are appended to, beside them
  PROVENANCE_KEY_FILE    file holding the key this deployment signs with
No network is involved: this component is a local store, so there is no
endpoint and no socket, and urllib is not imported.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import AttestRequest, Envelope, Problem, canonical
from adapters.dryrun import LocalSignedRecordAdapter


class LiveEvidenceStoreAdapter(LocalSignedRecordAdapter):
    entity = "the evidence records on this host (kb/ledger.jsonl today), with a signed envelope beside them"
    declared_gaps = LocalSignedRecordAdapter.declared_gaps + (
        "the evidence store is read and never written by this adapter; sealing a run stays tools/kb.py ledger",)

    def __init__(self):
        # deliberately not calling LocalSignedRecordAdapter.__init__: that one
        # truncates a dry-run store, and a live store is appended to.
        super(LocalSignedRecordAdapter, self).__init__()
        self.evidence = self._env("EVIDENCE_STORE")
        self.path = self._env("ATTESTATION_STORE")
        self.key_file = self._env("PROVENANCE_KEY_FILE")
        if not os.path.isfile(self.evidence):
            raise Problem("adapter-unavailable",
                          f"EVIDENCE_STORE {self.evidence} does not exist; nothing was signed", retry_after_s=30)
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        records = self._records() if os.path.isfile(self.path) else []
        self.head = records[-1]["hash"] if records else "genesis"

    @staticmethod
    def _env(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the evidence store on this host cannot be reached and "
                          f"no statement was emitted",
                          retry_after_s=30)
        return value

    def _signer(self, request: AttestRequest) -> tuple:
        try:
            key = open(self.key_file, "rb").read().strip()
        except OSError as exc:
            raise Problem("adapter-unavailable", f"PROVENANCE_KEY_FILE: {exc}", retry_after_s=30) from exc
        if len(key) < 32:
            raise Problem("adapter-unavailable", "the signing key is shorter than 32 bytes", retry_after_s=30)
        return "host-held-key-v1", key, {"keyid": "host-held-key-v1",
                                         "authority": "possession of the key file this host holds",
                                         "expires": None}

    def verifying_material(self, keyid: str) -> dict:
        return {"keyid": keyid, "material": open(self.key_file, "rb").read().strip().hex(), "issuer": None,
                "source": "out of band: the key file this host holds"}

    def _evidence_head(self) -> dict:
        """The last record of the live store: read only, and only its identity."""
        last = None
        with open(self.evidence) as fh:
            for line in fh:
                if line.strip():
                    last = json.loads(line)
        if last is None:
            return {"id": None, "hash": None}
        return {"id": last.get("id"), "hash": last.get("hash")}

    def _append(self, statement_id: str, envelope: Envelope, request: AttestRequest, bound: dict) -> None:
        record = {"id": statement_id, "prev": self.head, "envelope": envelope.to_dict(),
                  "subjects": [s.digest for s in request.subjects],
                  "actor": bound["actor"], "code_version": bound["code_version"],
                  "correlation": request.correlation,
                  "evidence_record": self._evidence_head()}
        record["hash"] = hashlib.sha256(canonical(record)).hexdigest()
        with open(self.path, "a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        self.head = record["hash"]


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveEvidenceStoreAdapter
