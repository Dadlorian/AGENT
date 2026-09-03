#!/usr/bin/env python3
"""Live adapter for today's component: this repository's own ledger.

Product names are allowed in this file and nowhere else. core-graph-implement
names no adapter of the Graph itself (PASS.md Part A has no Graph row); its
own recommendation, taken here, is that what is adapted beneath the Graph is
the record store its node and edge assertions round-trip through - the same
JSONL, hash-chained ledger cap-state-persistence-implement adapts
(F-b3-17, F-a5-03). Today's instance is the file at GRAPH_LEDGER_PATH
(README recommends kb/ledger.jsonl) and the tool that owns its chaining,
`python3 tools/kb.py` (GRAPH_KB_TOOL), whose `ledger` subcommand appends one
record with `prev`/`hash` set exactly as F-b3-17 describes.

Execution model: a single mutable append-only file, one writer, order is
byte position - the axis the second adapter's cursor-claimed, self-identified
records deliberately break. Every record this adapter writes or reads carries
a `graph_partition` tag so this harness's own runs never collide with an
unrelated ledger entry.
"""
from __future__ import annotations

import json
import os
import subprocess

from interface import GraphAdapter, Problem


class LiveLedgerAdapter(GraphAdapter):
    entity = "this repository's ledger (kb/ledger.jsonl via tools/kb.py, today)"
    execution_model = "single mutable append-only file, one writer, order is byte position"
    declared_marker = "kb-ledger-jsonl"
    declared_gaps = (
        "one partition tag only: records are filtered by graph_partition on read; a mixed "
        "ledger with an unrelated entry of the same node_id/edge_id would collide",
        "no compare-and-swap at the tool layer: tools/kb.py ledger takes no expected-previous "
        "argument, so two writers racing here are not refused the way the object-backed second "
        "adapter's cursor claim refuses them",
    )

    def _partition(self) -> str:
        return os.environ.get("GRAPH_LEDGER_PARTITION", "core-graph-harness")

    def _path(self) -> str:
        path = os.environ.get("GRAPH_LEDGER_PATH")
        if not path:
            raise Problem("adapter-unavailable", "GRAPH_LEDGER_PATH is not set; the live ledger cannot be reached",
                          retry_after_s=30)
        return path

    def _tool(self) -> list:
        return os.environ.get("GRAPH_KB_TOOL", "python3 tools/kb.py").split()

    def _read_all(self) -> list:
        path = self._path()
        if not os.path.isfile(path):
            return []
        with open(path, encoding="utf-8") as fh:
            raw = [json.loads(line) for line in fh if line.strip()]
        tag = self._partition()
        out = []
        for rec in raw:
            if rec.get("graph_partition") != tag:
                continue
            if rec.get("kind") == "node-asserted":
                out.append({"record_kind": "node-asserted", "node": rec["node"]})
            elif rec.get("kind") == "edge-asserted":
                out.append({"record_kind": "edge-asserted", "edge": rec["edge"]})
        return out

    def _store_record(self, record: dict) -> None:
        payload = {"kind": record["record_kind"], "graph_partition": self._partition()}
        if record["record_kind"] == "node-asserted":
            payload["node"] = record["node"]
        else:
            payload["edge"] = record["edge"]
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

    def _all_records(self) -> list:
        return self._read_all()


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveLedgerAdapter
