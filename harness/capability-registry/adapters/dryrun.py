#!/usr/bin/env python3
"""Dry-run adapter: a signed, append-only index beside the package bytes it
names, kept in process. The same bytes every run, so a gate can assert on
them. Authority comes from possession of a key this deployment holds
(cap-capability-registry-implement step 2). The index is hash-chained so an
edit between runs is detectable (F-a5-03), the same integrity scheme the
evidence store on this host already uses rather than a second one invented
here.

This is the shape of today's adapter (F-b3-07: "skill files"; blueprint state
"registry record and version": home_today "capability packages resolved as
files on disk"), run here without touching the real .claude/skills tree. The
live adapter below wraps that tree for real.
"""
from __future__ import annotations

import hashlib
import os

from interface import CapabilityRecord, PublishRequest, canonical, digest_of

HELD_KEY = hashlib.sha256(b"harness/capability-registry dry-run held key").digest()
CLOCK = os.environ.get("REGISTRY_CLOCK", "2026-09-03T00:00:00Z")

from interface import CapabilityRegistryAdapter  # noqa: E402


class SignedIndexAdapter(CapabilityRegistryAdapter):
    adapter_kind = "signed-index"
    entity = "an append-only, hash-chained index kept beside the package bytes, signed with a key this deployment holds"
    resolution = "signed-index"
    identity_is = "a path plus a version string"
    network_required = False
    trust_anchor = "a key this deployment holds"
    declared_gaps = ("cannot serve a caller with no access to this store",
                     "cannot be verified by a party that does not trust this deployment's key",
                     "cannot hold two records that differ only in content without the (namespace, name, version) triple already telling them apart")

    def __init__(self):
        super().__init__()
        self._store: dict = {}          # "ns/name" -> {version: (record, package_bytes)}
        self.head = "genesis"
        self.chain: list = []

    def _signer(self, request: PublishRequest) -> tuple:
        if os.environ.get("REGISTRY_FAIL") == "1":       # the failure path, exercised on demand
            from interface import Problem
            raise Problem("adapter-unavailable",
                          "the signing key is unreadable (REGISTRY_FAIL=1); no record was appended",
                          retry_after_s=1)
        return "registry-held-key-v1", HELD_KEY

    def _verifying_material(self, namespace: str, name: str) -> bytes | None:
        return HELD_KEY

    def _all_versions(self, name: str) -> dict:
        return {v: True for v in self._store.get(name, {})}

    def _record(self, name: str, version: str) -> CapabilityRecord:
        return self._store[name][version][0]

    def _package_bytes(self, namespace: str, name: str, version: str) -> bytes | None:
        entry = self._store.get(f"{namespace}/{name}", {}).get(version)
        return entry[1] if entry else None

    def _append(self, name: str, version: str, record: CapabilityRecord, package_bytes: bytes) -> None:
        self._store.setdefault(name, {})[version] = (record, package_bytes)
        entry = {"prev": self.head, "record": record.to_dict()}
        entry_hash = hashlib.sha256(canonical(entry)).hexdigest()
        self.chain.append({**entry, "hash": entry_hash})
        self.head = entry_hash

    def _now(self) -> str:
        return CLOCK

    def tamper(self, name: str, version: str, package_bytes: bytes) -> None:
        """Test-only: edit the package tree after signing, without touching the
        record - the digest-mismatch fixture (cap-capability-registry-implement
        DoD). No caller of this interface can reach this method."""
        record, _ = self._store[name][version]
        self._store[name][version] = (record, package_bytes)

    def unsign(self, name: str, version: str) -> None:
        """Test-only: strip a record's signature - the unsigned fixture."""
        record, package_bytes = self._store[name][version]
        record.signature = "0" * 64
        self._store[name][version] = (record, package_bytes)

    def store_integrity(self) -> dict:
        prev, broken = "genesis", 0
        for entry in self.chain:
            body = {"prev": entry["prev"], "record": entry["record"]}
            if entry["prev"] != prev or hashlib.sha256(canonical(body)).hexdigest() != entry["hash"]:
                broken += 1
            prev = entry["hash"]
        return {"kind": "hash-chained index", "head": prev, "entries": len(self.chain), "broken": broken}


# The one name every adapter module exports: the entry point of this module.
Adapter = SignedIndexAdapter
