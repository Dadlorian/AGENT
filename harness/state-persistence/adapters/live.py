#!/usr/bin/env python3
"""Live adapter for the JSONL + hash chain running on this host today.

Product names are allowed in this file and nowhere else. Today's instance is
this repository's own ledger (PASS.md B3, F-b3-17): the file at
STATE_LEDGER_PATH (README recommends kb/ledger.jsonl) and the tool that owns
its chaining, `python3 tools/kb.py` (STATE_KB_TOOL), whose `ledger` subcommand
appends one record with `prev` set to the previous record's hash and `hash` set
to sha256 over the canonical record - the exact hash-chain design F-b3-17 names.

Execution model: a single mutable append-only file, one writer, order is byte
position. tools/kb.py's own ledger command takes no expected-previous
argument, so it has no compare-and-swap of its own; this adapter narrows the
race by re-reading the file immediately before shelling out and refusing if it
moved, but cannot close the window between that read and the subprocess call
without changing tools/kb.py, which is out of scope here (declared gap below).

Standard library only; the subprocess call is guarded so this module never
breaks a dry run on a host with no ledger tool available.
"""
from __future__ import annotations

import json
import os
import subprocess

from interface import (AppendRequest, ConsistencyProof, Head, InclusionProof, Problem,
                       StatePersistenceAdapter, StateRecord, audit_path, consistency_proof, mth, sha256_hex, as_digest)


class LiveLedgerAdapter(StatePersistenceAdapter):
    entity = "this repository's ledger (kb/ledger.jsonl via tools/kb.py, today)"
    execution_model = "single mutable append-only file, one writer, order is byte position"
    declared_marker = "kb-ledger-jsonl"
    declared_gaps = (
        "one partition only: the live ledger has a single global sequence; a request naming a "
        "different partition is refused rather than silently rehomed",
        "prove and prove_consistency rebuild the tree from the file's hash column on every call, "
        "because no tree is persisted alongside it; cost grows with the log, which is exactly the "
        "shape a persisted tree (or the object-store adapter) exists to fix",
        "no compare-and-swap at the tool layer: tools/kb.py ledger takes no expected-previous "
        "argument, so this adapter's re-read-before-append narrows the race window but a writer "
        "outside this harness could still land between the re-read and the subprocess call",
        "redact is unsupported: the live tool has no field-drop or delete path, only append",
        "content-id recomputation does not apply to this binding: a record's id here is tools/kb.py's own "
        "hash column over the full stored record including its bookkeeping fields, not this harness's "
        "{kind, partition, body, seq} scheme, so verify_external.py's chain_break_at is not meaningful here",
    )

    def _env(self, name: str, default: str | None = None) -> str:
        value = os.environ.get(name, default)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the live ledger cannot be reached", retry_after_s=30)
        return value

    def _partition(self) -> str:
        return os.environ.get("STATE_LEDGER_PARTITION", "kb-ledger")

    def _path(self) -> str:
        return self._env("STATE_LEDGER_PATH")

    def _tool(self) -> list[str]:
        return self._env("STATE_KB_TOOL", "python3 tools/kb.py").split()

    def _read_all(self) -> list[dict]:
        path = self._path()
        if not os.path.isfile(path):
            return []
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def _to_record(self, rec: dict, partition: str) -> StateRecord:
        rid = "sha256:" + rec["hash"]
        prev = None if rec.get("prev") in (None, "genesis") else "sha256:" + rec["prev"]
        body = {k: v for k, v in rec.items() if k not in ("id", "hash", "prev", "type", "kind", "time")}
        return StateRecord(rid, prev, rid, rec.get("kind", "ledger"), partition,
                           0, rec.get("time", ""), body)

    def _check_partition(self, partition: str) -> None:
        if partition != self._partition():
            raise Problem("adapter-unavailable",
                          f"this binding serves partition {self._partition()!r} only; {partition!r} was requested",
                          partition=partition)

    def _head(self, records: list[dict], partition: str) -> Head:
        ids = ["sha256:" + r["hash"] for r in records]
        root = as_digest(mth(ids))
        chain = ids[-1] if ids else "genesis"
        return Head(partition, len(records), root, chain, None)

    def resolve_head(self, partition: str) -> Head:
        self._check_partition(partition)
        return self._head(self._read_all(), partition)

    def _append_locked(self, request: AppendRequest, head: Head) -> tuple[StateRecord, Head]:
        # Narrow the race: re-read immediately before the write (declared gap: cannot close it).
        current = self._head(self._read_all(), request.partition)
        if current.chain_digest != head.chain_digest:
            raise Problem("head-moved",
                          f"the ledger moved between resolve_head and append: {head.chain_digest!r} -> "
                          f"{current.chain_digest!r}; the append was not sent", partition=request.partition)
        payload = dict(request.body)
        payload["kind"] = request.kind
        tool = self._tool()
        repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        try:
            proc = subprocess.run(tool + ["ledger", json.dumps(payload)], cwd=repo_root,
                                  capture_output=True, text=True, timeout=30)
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=10) from exc
        if proc.returncode != 0:
            raise Problem("adapter-unavailable", f"tools/kb.py ledger exited {proc.returncode}: {proc.stderr[:300]}",
                          retry_after_s=10)
        records = self._read_all()
        record = self._to_record(records[-1], request.partition)
        return record, self._head(records, request.partition)

    def read_at(self, partition: str, head: Head, selector: dict | None = None) -> list[StateRecord]:
        self._check_partition(partition)
        records = self._read_all()[:head.size]
        out = [self._to_record(r, partition) for r in records]
        if not selector:
            return out
        kind, rid = selector.get("kind"), selector.get("record_id")
        if kind is not None:
            out = [r for r in out if r.kind == kind]
        if rid is not None:
            out = [r for r in out if r.record_id == rid]
        return out

    def prove(self, partition: str, record_id: str, head: Head) -> InclusionProof:
        self._check_partition(partition)
        records = self._read_all()[:head.size]
        ids = ["sha256:" + r["hash"] for r in records]
        if record_id not in ids:
            raise Problem("record-unverifiable", f"{record_id} is not in the ledger at this head")
        idx = ids.index(record_id)
        path = [as_digest(h) for h in audit_path(ids, idx)]
        return InclusionProof(record_id, idx, head, path)

    def prove_consistency(self, partition: str, old_head: Head, new_head: Head) -> ConsistencyProof:
        self._check_partition(partition)
        records = self._read_all()[:new_head.size]
        ids = ["sha256:" + r["hash"] for r in records]
        path = [as_digest(h) for h in consistency_proof(old_head.size, ids)]
        return ConsistencyProof(old_head, new_head, path)

    def redact(self, partition: str, record_id: str, authority: str) -> StateRecord:
        raise Problem("adapter-unavailable", "redact is unsupported: the live ledger tool has no delete path")


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveLedgerAdapter
