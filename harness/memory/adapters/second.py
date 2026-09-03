#!/usr/bin/env python3
"""Second adapter: a file-backed store, one JSON document per scope key.

Where the dry-run store finds candidates by scope match then ranks them, this
one has no ranker at all: `_search` is an exact lookup on the scope key
(the sorted (dimension, value) pairs of `scope`, joined), and `need` only ever
selects among the items already at that key by substring match - never across
keys. That is the axis cap-memory-implement asks the pair to differ on. It can
be read by a person opening a file, cannot answer a need expressed only in
words across scopes, and cannot serve concurrent writers without the coarse
lock this file takes.

Reachability: with MEMORY_SCOPE_STORE_DIR set to a directory the adapter
writes one file per scope key under it - a real path, not a simulation; unset,
it uses a scratch directory under harness/memory/out.
"""
from __future__ import annotations

import glob
import json
import os

from interface import (MemoryAdapter, MemoryItem, Problem, Provenance, RecallQuery, Staleness,
                       _digest_id, _scope_holds, item_as_dict, now_iso)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(HERE, "..", "out", "scope-store")


def _scope_key(scope: dict) -> str:
    return "&".join(f"{k}={scope[k]}" for k in sorted(scope))


def _from_doc(doc: dict) -> MemoryItem:
    prov = doc["provenance"]
    stale = doc["staleness"]
    return MemoryItem(doc["memory_id"], doc["scope"], doc["kind"], doc["body"],
                      Provenance(prov["produced_by"], prov["observed_at"], prov["correlation_id"],
                                prov.get("supersedes")),
                      Staleness(stale.get("expires_at"), stale.get("review_after")),
                      doc.get("superseded_by"))


class ScopeKeyedFileAdapter(MemoryAdapter):
    entity = "file-backed store, one document per exact scope key (second adapter)"
    role = "second"
    retrieval_model = "exact-key"
    execution_model = "one file per scope key on disk, recall is an exact lookup on that key"
    declared_marker = "scope-keyed-file-store"
    declared_gaps = (
        "cannot answer a need expressed only in words across scopes: `need` only ever selects among "
        "items already found at the exact scope key, never ranks across keys",
        "no true concurrent-writer isolation: this file takes a coarse read-modify-write on one JSON "
        "file per key, adequate for this harness's sequential conformance run and not more than that",
    )

    def __init__(self):
        super().__init__()
        self._root = os.environ.get("MEMORY_SCOPE_STORE_DIR", DEFAULT_DIR)
        os.makedirs(self._root, exist_ok=True)

    def _path(self, key: str) -> str:
        safe = key.replace("/", "_").replace(":", "_")
        return os.path.join(self._root, f"{safe}.json")

    def _load(self, key: str) -> list:
        path = self._path(key)
        if not os.path.isfile(path):
            return []
        with open(path, encoding="utf-8") as fh:
            return [_from_doc(d) for d in json.load(fh)]

    def _save(self, key: str, items: list) -> None:
        with open(self._path(key) + ".tmp", "w", encoding="utf-8") as fh:
            json.dump([item_as_dict(it) for it in items], fh, sort_keys=True)
        os.replace(self._path(key) + ".tmp", self._path(key))

    def _write(self, item: MemoryItem) -> None:
        if os.environ.get("SECOND_FAIL") == "1":
            raise Problem("adapter-unavailable", "the scope-keyed store was made unreachable by SECOND_FAIL=1")
        key = _scope_key(item.scope)
        items = self._load(key)
        items.append(item)
        self._save(key, items)

    def _search(self, query: RecallQuery) -> list:
        key = _scope_key(query.scope)
        items = [it for it in self._load(key) if it.superseded_by is None]
        if query.key:
            items = [it for it in items if it.memory_id == query.key]
        if query.need:
            need = query.need.lower()
            items = [it for it in items if any(need in str(v).lower() for v in it.body.values())] or items
        return items[:query.limit]

    def supersede(self, memory_id, body, produced_by, correlation_id, expires_at, review_after=None):
        for path in glob.glob(os.path.join(self._root, "*.json")):
            with open(path, encoding="utf-8") as fh:
                docs = json.load(fh)
            ids = [d["memory_id"] for d in docs]
            if memory_id not in ids:
                continue
            items = [_from_doc(d) for d in docs]
            old = next(it for it in items if it.memory_id == memory_id)
            new_id = _digest_id({"supersedes": memory_id, "body": body, "seq": len(items)})
            new_item = MemoryItem(new_id, dict(old.scope), old.kind, body,
                                  Provenance(produced_by, now_iso(), correlation_id, memory_id),
                                  Staleness(expires_at, review_after))
            items = [it if it.memory_id != memory_id else
                    MemoryItem(it.memory_id, it.scope, it.kind, it.body, it.provenance, it.staleness, new_id)
                    for it in items]
            items.append(new_item)
            self._save(_scope_key(old.scope), items)
            return new_item
        raise Problem("item-not-found", f"{memory_id} is not known to this binding")

    def forget(self, memory_id=None, scope=None, reason="expiry"):
        if memory_id is not None:
            for path in glob.glob(os.path.join(self._root, "*.json")):
                with open(path, encoding="utf-8") as fh:
                    docs = json.load(fh)
                ids = [d["memory_id"] for d in docs]
                if memory_id in ids:
                    kept = [d for d in docs if d["memory_id"] != memory_id]
                    with open(path, "w", encoding="utf-8") as fh:
                        json.dump(kept, fh, sort_keys=True)
                    return 1
            raise Problem("item-not-found", f"{memory_id} is not known to this binding")
        if scope is not None:
            key = _scope_key(scope)
            items = self._load(key)
            if items:
                self._save(key, [])
            return len(items)
        return 0

    def sweep(self) -> int:
        from interface import _expired
        at = now_iso()
        removed = 0
        for path in glob.glob(os.path.join(self._root, "*.json")):
            with open(path, encoding="utf-8") as fh:
                docs = json.load(fh)
            items = [_from_doc(d) for d in docs]
            kept = [it for it in items if not _expired(it, at)]
            removed += len(items) - len(kept)
            if len(kept) != len(items):
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump([item_as_dict(it) for it in kept], fh, sort_keys=True)
        return removed


# The one name every adapter module exports: the entry point of this module.
Adapter = ScopeKeyedFileAdapter
