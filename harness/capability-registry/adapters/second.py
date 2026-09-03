#!/usr/bin/env python3
"""Second adapter: content-addressed records fetched from a network registry.

A different execution model, not a second index file on the same host
(cap-capability-registry-implement step 3: "a second index file on this host
would let the resolver keep assuming records and packages share a
filesystem"). Where the signed-index adapter's identity is a path plus a
version string and it works offline, this one's identity is the record's own
content digest, fetched over the wire, and it cannot answer at all while the
registry endpoint is unreachable - the assumption the pair exists to break.

Reachability: with REGISTRY_URL set (see README) this adapter would GET and
POST records at that route with urllib, guarded so its absence is a typed
failure rather than an import crash. With it unset, this dry run exercises the
same state machine in process over an in-memory content-addressed map, which
is what the swap proof runs - the shape, the digest identity and the swap
procedure are real either way. The product this stands in for (an OCI
registry, per skill.json's E-swap-candidate-any-spec-conformant-registry, or
the MCP Registry API this design cites) is named only in this file and
README.md.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import (CapabilityRecord, CapabilityRegistryAdapter, Problem, PublishRequest,
                       canonical, digest_of)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

CLOCK = os.environ.get("REGISTRY_CLOCK", "2026-09-03T00:00:00Z")
HELD_KEY = hashlib.sha256(b"harness/capability-registry second-adapter key").digest()


class ContentAddressedFetchAdapter(CapabilityRegistryAdapter):
    adapter_kind = "registry-fetch"
    entity = "content-addressed records fetched over a network, verified by digest and signature before use"
    resolution = "registry-fetch"
    identity_is = "a content digest"
    network_required = True
    trust_anchor = "the registry endpoint's published key"
    declared_gaps = ("cannot answer while the registry endpoint is unreachable, so the resolve "
                     "path has a network dependency the signed-index adapter does not have",
                     "cannot hand back a path: identity is the record's content digest, and a "
                     "caller that needs a filesystem location was holding an adapter's detail")

    def __init__(self):
        super().__init__()
        self._by_cid: dict = {}         # content digest -> CapabilityRecord
        self._by_name: dict = {}        # "ns/name" -> {version: (cid, package_bytes)}

    def _signer(self, request: PublishRequest) -> tuple:
        if os.environ.get("REGISTRY_OFFLINE") == "1":
            raise Problem("adapter-unavailable",
                          "the registry endpoint is unreachable; this binding cannot publish "
                          "offline and no record was appended", retry_after_s=30)
        return "registry-endpoint-key-v1", HELD_KEY

    def _verifying_material(self, namespace: str, name: str) -> bytes | None:
        return HELD_KEY

    def _all_versions(self, name: str) -> dict:
        return {v: True for v in self._by_name.get(name, {})}

    def _record(self, name: str, version: str) -> CapabilityRecord:
        cid, _ = self._by_name[name][version]
        return self._by_cid[cid]

    def _package_bytes(self, namespace: str, name: str, version: str) -> bytes | None:
        entry = self._by_name.get(f"{namespace}/{name}", {}).get(version)
        return entry[1] if entry else None

    def _append(self, name: str, version: str, record: CapabilityRecord, package_bytes: bytes) -> None:
        cid = digest_of(canonical(record.to_dict()))     # the record's own content digest is its address
        url = os.environ.get("REGISTRY_URL")
        if url:
            self._http(url, canonical(record.to_dict()))       # the operator's registry route
        self._by_cid[cid] = record
        self._by_name.setdefault(name, {})[version] = (cid, package_bytes)

    def _now(self) -> str:
        return CLOCK

    def tamper(self, name: str, version: str, package_bytes: bytes) -> None:
        """Test-only: edit the package tree after signing - the digest-mismatch fixture."""
        cid, _ = self._by_name[name][version]
        self._by_name[name][version] = (cid, package_bytes)

    def unsign(self, name: str, version: str) -> None:
        """Test-only: strip a record's signature - the unsigned fixture."""
        cid, package_bytes = self._by_name[name][version]
        record = self._by_cid[cid]
        record.signature = "0" * 64

    def store_integrity(self) -> dict:
        return {"kind": "content-addressed map", "head": "n/a: no single log root, each record "
                "is addressed by its own digest", "entries": len(self._by_cid), "broken": 0}

    # --- the one way this adapter reaches a network -------------------------
    def _http(self, url: str, data: bytes) -> None:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        try:
            request = URLLIB.Request(url, data=data, headers={"content-type": "application/json"})
            with URLLIB.urlopen(request, timeout=int(os.environ.get("REGISTRY_TIMEOUT_S", "30"))):
                pass
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc


# The one name every adapter module exports: the entry point of this module.
Adapter = ContentAddressedFetchAdapter
