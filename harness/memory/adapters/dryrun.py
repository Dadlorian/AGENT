#!/usr/bin/env python3
"""Dry-run adapter: an in-memory ranked-shaped store. No disk, no network.

Execution model: a Python list held by this process; recall ranks candidates
by a crude keyword overlap with `need` when one is given, otherwise returns
every item at the matching scope - standing in for the hosted, embedding-
ranked store PASS.md's manifest names as today's component (no memory row
exists in PASS.md, so this is a stand-in for the axis, not a product). This is
the axis the second adapter deliberately breaks: exact key lookup instead of
ranking.
"""
from __future__ import annotations

import os

from interface import MemoryAdapter, MemoryItem, Problem, RecallQuery, RememberRequest, _scope_holds


class DryRunAdapter(MemoryAdapter):
    entity = "in-memory ranked-shaped store (dry run)"
    role = "today"
    retrieval_model = "ranked"
    execution_model = "single mutable list held by this process, candidates found by scope match then ranked"
    declared_marker = "dryrun-ranked-memory-store"

    def __init__(self):
        super().__init__()
        self._items: dict[str, MemoryItem] = {}
        self._order: list[str] = []

    def _write(self, item: MemoryItem) -> None:
        if os.environ.get("DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable", "the dry-run store was made unreachable by DRYRUN_FAIL=1")
        self._items[item.memory_id] = item
        self._order.append(item.memory_id)

    def _rank(self, item: MemoryItem, need: str | None) -> tuple:
        if not need:
            return (0,)
        hay = " ".join(str(v) for v in item.body.values()).lower()
        overlap = sum(1 for w in need.lower().split() if w in hay)
        return (-overlap,)

    def _search(self, query: RecallQuery) -> list:
        if query.key:
            item = self._items.get(query.key)
            return [item] if item and _scope_holds(query.scope, item.scope) and item.superseded_by is None else []
        matched = [self._items[mid] for mid in self._order
                  if _scope_holds(query.scope, self._items[mid].scope) and self._items[mid].superseded_by is None]
        matched.sort(key=lambda it: self._rank(it, query.need))
        return matched[:query.limit]

    def supersede(self, memory_id, body, produced_by, correlation_id, expires_at, review_after=None):
        from interface import Provenance, Staleness, _digest_id
        old = self._items.get(memory_id)
        if old is None:
            raise Problem("item-not-found", f"{memory_id} is not known to this binding")
        new_id = _digest_id({"supersedes": memory_id, "body": body, "seq": len(self._order)})
        from interface import now_iso
        new_item = MemoryItem(new_id, dict(old.scope), old.kind, body,
                              Provenance(produced_by, now_iso(), correlation_id, memory_id),
                              Staleness(expires_at, review_after))
        self._items[memory_id] = MemoryItem(old.memory_id, old.scope, old.kind, old.body, old.provenance,
                                            old.staleness, superseded_by=new_id)
        self._items[new_id] = new_item
        self._order.append(new_id)
        return new_item

    def forget(self, memory_id=None, scope=None, reason="expiry"):
        removed = 0
        if memory_id is not None:
            if memory_id in self._items:
                del self._items[memory_id]
                self._order.remove(memory_id)
                removed = 1
            else:
                raise Problem("item-not-found", f"{memory_id} is not known to this binding")
            return removed
        if scope is not None:
            gone = [mid for mid in self._order if _scope_holds(scope, self._items[mid].scope)]
            for mid in gone:
                del self._items[mid]
                self._order.remove(mid)
            return len(gone)
        return 0

    def sweep(self) -> int:
        from interface import now_iso, _expired
        at = now_iso()
        gone = [mid for mid, it in self._items.items() if _expired(it, at)]
        for mid in gone:
            del self._items[mid]
            self._order.remove(mid)
        return len(gone)


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunAdapter
