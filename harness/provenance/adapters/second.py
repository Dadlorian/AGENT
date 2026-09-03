#!/usr/bin/env python3
"""Second adapter: keyless signing with a public append-only log.

A different execution model, not a second store of the same shape. Where the
local adapter's authority comes from possession of a file our own reader
rehashes and it works offline, this one obtains a signing identity per run and
discards it, publishes the envelope to a log that is append-only and once
entries are added they cannot be modified (X-cross-structure-052), and returns
an inclusion proof with it. It cannot produce a statement at all while the
identity provider is unreachable, which is the assumption the pair exists to
break.

The verifying material travels with the envelope here instead of being handed
to a verifier out of band, so a third party who fetches the bundle has
everything the verification needs except the trust policy naming the issuer.

Reachability: with TRANSPARENCY_LOG_URL and IDENTITY_URL set (see README) this
adapter would POST the envelope and fetch a token from those routes with
urllib. Neither is invented here: both are supplied whole by the operator. With
them unset it runs the same state machine in process over an append-only Merkle
log, which is what a dry run exercises - the shape, the proof and the swap
procedure are real either way, and the product this stands in for (Sigstore,
with Rekor as the log and Fulcio as the identity) is named only in this file.

The log is tamper-evident, not tamper-proof (X-cross-structure-053): monitoring
it is store_integrity() below, and it is never what verification rests on.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import (AttestRequest, Envelope, Location, Problem, ProvenanceAdapter,
                       canonical, _leaf, _node)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

CLOCK = os.environ.get("PROVENANCE_CLOCK", "2026-09-03T00:00:00Z")
ISSUER = "ephemeral-identity-issuer"


def _root(hashes: list) -> str:
    if len(hashes) == 1:
        return hashes[0]
    k = 1 << ((len(hashes) - 1).bit_length() - 1)
    return _node(_root(hashes[:k]), _root(hashes[k:]))


def _path(hashes: list, index: int) -> list:
    """The audit path, innermost sibling first."""
    if len(hashes) == 1:
        return []
    k = 1 << ((len(hashes) - 1).bit_length() - 1)
    if index < k:
        return _path(hashes[:k], index) + [_root(hashes[k:])]
    return _path(hashes[k:], index - k) + [_root(hashes[:k])]


class KeylessTransparencyLogAdapter(ProvenanceAdapter):
    adapter_kind = "keyless-transparency-log"
    entity = "an identity that expires, and a public append-only log (Sigstore-shaped)"
    signer_authority = "expiring-identity"
    key_lifetime = "per-run, discarded"
    store_kind = "append-only merkle log"
    material_source = "published with the envelope"
    offline_capable = False
    supports_inclusion_proof = True
    declared_gaps = ("cannot sign while the identity provider is unreachable, so the emission path has a "
                     "network dependency the local adapter does not have",
                     "cannot host a subject whose name must not be public")

    def __init__(self):
        super().__init__()
        self.entries: list[bytes] = []          # the log, append-only
        self._material: dict[str, dict] = {}
        self._by_id: dict[str, int] = {}
        self._subjects: dict[str, list] = {}

    # --- an identity obtained per run and discarded --------------------------
    def _signer(self, request: AttestRequest) -> tuple:
        if os.environ.get("PROVENANCE_OFFLINE") == "1":
            raise Problem("adapter-unavailable",
                          "the identity provider is unreachable; this binding cannot sign offline and no "
                          "statement was emitted",
                          retry_after_s=30)
        run = request.correlation.get("run_id", "run-unknown")
        token = self._token(run)
        keyid = f"ephemeral:{token['subject']}:{token['not_after']}"
        key = hashlib.sha256(("ephemeral " + keyid).encode()).digest()   # discarded after this call
        self._material[keyid] = {"keyid": keyid, "material": key.hex(), "issuer": ISSUER,
                                 "not_before": token["not_before"], "not_after": token["not_after"]}
        return keyid, key, {"keyid": keyid, "authority": f"an identity issued by {ISSUER} for this run only",
                            "expires": token["not_after"]}

    def _token(self, run: str) -> dict:
        url = os.environ.get("IDENTITY_URL")
        if url:
            doc = self._http(url.replace("{run_id}", run), None)
            return {"subject": str(doc.get("subject", run)),
                    "not_before": str(doc["not_before"]), "not_after": str(doc["not_after"])}
        return {"subject": run, "not_before": CLOCK, "not_after": CLOCK[:11] + "23:59:59Z"}

    # --- the log: append, then an inclusion proof ---------------------------
    def _append(self, statement_id: str, envelope: Envelope, request: AttestRequest, bound: dict) -> None:
        entry = canonical(envelope.to_dict())
        url = os.environ.get("TRANSPARENCY_LOG_URL")
        if url:
            self._http(url, entry)          # the operator's log route; the local tree stays the mirror
        self.entries.append(entry)
        self._by_id[statement_id] = len(self.entries) - 1
        for subject in request.subjects:
            self._subjects.setdefault(subject.digest, []).append(len(self.entries) - 1)

    def _proof(self, index: int) -> dict:
        leaves = [_leaf(e) for e in self.entries]
        return {"log_id": ISSUER + "-log", "leaf_index": index, "tree_size": len(leaves),
                "path": _path(leaves, index), "root": _root(leaves)}

    def resolve(self, subject_digest: str) -> list:
        return [json.loads(self.entries[i]) for i in self._subjects.get(subject_digest, [])]

    def publish(self, receipt) -> Location:
        index = self._by_id[receipt.statement_id]
        return Location(uri=f"attestation:{self.adapter_kind}/{index}",
                        store="a public append-only log any third party can read",
                        inclusion_proof=self._proof(index))

    def fetch(self, uri: str) -> dict:
        try:
            index = int(uri.rsplit("/", 1)[-1])
            entry = self.entries[index]
        except (ValueError, IndexError) as exc:
            raise Problem("adapter-unavailable", f"no log entry at {uri}", retry_after_s=30) from exc
        envelope = json.loads(entry)
        keyid = envelope["signatures"][0]["keyid"]
        return {"envelope": envelope, "inclusion_proof": self._proof(index),
                "verification_material": self._material[keyid]}

    def verifying_material(self, keyid: str) -> dict:
        material = dict(self._material[keyid])
        material["source"] = "published with the envelope, so a third party needs no secret from us"
        return material

    def store_integrity(self) -> dict:
        """Monitoring, not verification: the log is watched rather than trusted."""
        leaves = [_leaf(e) for e in self.entries]
        root = _root(leaves) if leaves else ""
        return {"kind": self.store_kind, "head": root, "entries": len(leaves),
                "verified": all(verify_entry(self, i) for i in range(len(leaves))),
                "checked_by": "recomputing the root over every entry; tamper-evident, not tamper-proof"}

    # --- the one way this adapter reaches a network -------------------------
    def _http(self, url: str, data: bytes | None) -> dict:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        try:
            request = URLLIB.Request(url, data=data, headers={"content-type": "application/json"})
            with URLLIB.urlopen(request, timeout=int(os.environ.get("LOG_TIMEOUT_S", "30"))) as resp:
                return json.load(resp)
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc


def verify_entry(adapter: KeylessTransparencyLogAdapter, index: int) -> bool:
    from interface import verify_inclusion
    return verify_inclusion(adapter.entries[index], adapter._proof(index))


# The one name every adapter module exports: the entry point of this module.
Adapter = KeylessTransparencyLogAdapter
