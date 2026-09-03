#!/usr/bin/env python3
"""Live adapter for today's memory component - which does not exist.

PASS.md has no memory row in any section (blueprint_tool_entry: absent
today), so there is no hosted, embedding-ranked store to bind to on this
host. What is real here is the shape of the seam a live binding would use:
an endpoint and a store path named only by environment variables, never
hard-coded, and a refusal typed adapter-unavailable when they are unset -
exactly what a caller sees today, and what it would see later if the
endpoint it names goes down.

If MEMORY_LIVE_STORE_PATH is set, this stub treats it as a local directory
standing in for the ranked store's own persistence (one JSON file per scope
key, ranked the same crude way adapters/dryrun.py ranks) so the swap
procedure and the conformance run are real end to end; it never calls a
network endpoint. MEMORY_LIVE_ENDPOINT is read and reported in declared_gaps
but never dialed - naming it is the whole of what this stub can honestly do
without a component to reach.

Product names are allowed in this file and nowhere else. Standard library
only; every external touch is guarded so this module never breaks a dry run.
"""
from __future__ import annotations

import json
import os

from interface import (MemoryAdapter, MemoryItem, Problem, Provenance, RecallQuery, Staleness,
                       _digest_id, _scope_holds, item_as_dict, now_iso)


def _from_doc(doc: dict) -> MemoryItem:
    prov, stale = doc["provenance"], doc["staleness"]
    return MemoryItem(doc["memory_id"], doc["scope"], doc["kind"], doc["body"],
                      Provenance(prov["produced_by"], prov["observed_at"], prov["correlation_id"],
                                prov.get("supersedes")),
                      Staleness(stale.get("expires_at"), stale.get("review_after")), doc.get("superseded_by"))


class LiveMemoryAdapter(MemoryAdapter):
    entity = "today's memory component (none exists; a stub reached only through env vars)"
    role = "today"
    retrieval_model = "ranked"
    execution_model = "no component reachable on this host; a local JSON stand-in when MEMORY_LIVE_STORE_PATH is set"
    declared_marker = "live-memory-stub"
    declared_gaps = (
        "no hosted embedding-ranked store exists to bind to: PASS.md has no memory row, so this "
        "adapter has nothing behind MEMORY_LIVE_ENDPOINT to dial and never attempts to",
        "when MEMORY_LIVE_STORE_PATH is unset, every operation refuses adapter-unavailable before "
        "doing anything else - there is no default endpoint to fall back to",
    )

    def __init__(self):
        super().__init__()
        self._path_root = os.environ.get("MEMORY_LIVE_STORE_PATH")
        self._endpoint = os.environ.get("MEMORY_LIVE_ENDPOINT")

    def _require_path(self) -> str:
        if not self._path_root:
            raise Problem("adapter-unavailable",
                          "MEMORY_LIVE_STORE_PATH is not set; there is no component this binding can reach",
                          retry_after_s=30)
        os.makedirs(self._path_root, exist_ok=True)
        return self._path_root

    def _key_path(self, key: str) -> str:
        safe = key.replace("/", "_").replace(":", "_")
        return os.path.join(self._require_path(), f"{safe}.json")

    def _scope_key(self, scope: dict) -> str:
        return "&".join(f"{k}={scope[k]}" for k in sorted(scope))

    def _write(self, item: MemoryItem) -> None:
        path = self._key_path(self._scope_key(item.scope))
        items = self._read(path)
        items.append(item_as_dict(item))
        with open(path + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(items, fh, sort_keys=True)
        os.replace(path + ".tmp", path)

    def _read(self, path: str) -> list:
        if not os.path.isfile(path):
            return []
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _rank(self, item: MemoryItem, need: str | None) -> tuple:
        if not need:
            return (0,)
        hay = " ".join(str(v) for v in item.body.values()).lower()
        return (-sum(1 for w in need.lower().split() if w in hay),)

    def _search(self, query: RecallQuery) -> list:
        path = self._key_path(self._scope_key(query.scope))
        items = [_from_doc(d) for d in self._read(path) if d.get("superseded_by") is None]
        items = [it for it in items if _scope_holds(query.scope, it.scope)]
        items.sort(key=lambda it: self._rank(it, query.need))
        return items[:query.limit]

    def supersede(self, memory_id, body, produced_by, correlation_id, expires_at, review_after=None):
        raise Problem("adapter-unavailable", "supersede is not implemented in the live stub; no component to reach")

    def forget(self, memory_id=None, scope=None, reason="expiry"):
        raise Problem("adapter-unavailable", "forget is not implemented in the live stub; no component to reach")


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveMemoryAdapter
