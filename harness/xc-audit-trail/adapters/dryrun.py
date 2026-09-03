#!/usr/bin/env python3
"""Dry-run adapter: an in-memory hash-chained trail, seeded with a deterministic
fixture. No disk, no network. Execution model: single mutable list held by this
process, order is append order - the first store's assumption (whoever holds
the file holds the only copy) is exactly what adapters/second.py breaks.

The fixture spans a synthetic 200-day window under a fixed clock so
oldest_retained_entry_age_days is measurable without waiting 200 days, and
cycles all four TARGET T6.2 entry kinds under three correlation ids so
fetch_by_correlation has more than one bucket to prove.
"""
from __future__ import annotations

import datetime
import os

from interface import AppendRequest, AuditEntry, Problem, TrailAdapter, entry_hash

FIXTURE_ENTRIES = int(os.environ.get("TRAIL_FIXTURE_ENTRIES", "24"))


def _clock() -> datetime.datetime:
    fixed = os.environ.get("TRAIL_CLOCK", "2026-09-03T00:00:00Z")
    return datetime.datetime.fromisoformat(fixed.replace("Z", "+00:00"))


class LocalChainedTrailAdapter(TrailAdapter):
    entity = "in-memory hash-chained trail, seeded fixture (dry run)"
    execution_model = "single mutable list held by this process; we hold the only copy"
    adapter_kind = "jsonl-hash-chain"
    declared_gaps = ("nothing external checks this store; deleting it and its reader is one action",)
    external_checkable = False

    def __init__(self):
        super().__init__()
        self._entries: list[AuditEntry] = []
        self._seq = 0
        if os.environ.get("TRAIL_NO_SEED") != "1":
            self._seed()

    # --- fixture -----------------------------------------------------------
    def _seed(self) -> None:
        now = _clock()
        actors = [
            ("user", "user:corey", [{"actor": "user:corey", "obtained_via": "direct"}]),
            ("agent", "agent:planner", [{"actor": "user:corey", "obtained_via": "direct"},
                                        {"actor": "agent:planner", "obtained_via": "delegated"}]),
            ("service", "service:scheduler", [{"actor": "service:scheduler", "obtained_via": "direct"}]),
            ("schedule", "schedule:nightly-scan", [{"actor": "schedule:nightly-scan", "obtained_via": "direct"}]),
        ]
        corrs = [{"run_id": f"run-{i}", "correlation_id": f"corr-{i}"} for i in range(3)]
        for i in range(FIXTURE_ENTRIES):
            kind, actor, chain = actors[i % 4]
            corr = corrs[i % 3]
            days_ago = 200 - int(200 * i / max(FIXTURE_ENTRIES - 1, 1))
            at = (now - datetime.timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")
            req = AppendRequest(action=f"seed-action-{i}", actor=actor, delegation_chain=tuple(chain),
                                correlation=corr, kind=kind, at=at)
            self.append(req)

    # --- writer path ---------------------------------------------------------
    def _append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _clock(self) -> str:
        return _clock().isoformat().replace("+00:00", "Z")

    def _age_days(self, at: str) -> int:
        then = datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
        return max(0, (_clock() - then).days)

    # --- reads -----------------------------------------------------------
    def project(self, from_seq=None, to_seq=None) -> list:
        if os.environ.get("TRAIL_DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable", "the dry-run trail was made unreachable by TRAIL_DRYRUN_FAIL=1")
        out = self._entries
        if from_seq is not None:
            out = [e for e in out if e.seq >= from_seq]
        if to_seq is not None:
            out = [e for e in out if e.seq <= to_seq]
        return list(out)

    def head(self) -> str:
        return self._entries[-1].hash if self._entries else "genesis"

    def coverage_start(self) -> str:
        return self._entries[0].at if self._entries else self._clock()

    def external_verifications(self) -> int:
        return 0    # this store is checkable only by our own reader (F-b4-05)

    def store_integrity(self) -> dict:
        return {"kind": "in-memory list", "entries": len(self._entries), "head": self.head(), "verified": True}

    # --- test-only: tamper one entry in place, id and hash left untouched --
    def tamper(self, seq: int, new_action: str) -> None:
        for i, e in enumerate(self._entries):
            if e.seq == seq:
                self._entries[i] = AuditEntry(e.entry_id, e.seq, e.prev, e.hash, new_action, e.actor,
                                              e.delegation_chain, e.correlation, e.kind, e.at)
                return
        raise AssertionError(f"no entry at seq {seq}")
