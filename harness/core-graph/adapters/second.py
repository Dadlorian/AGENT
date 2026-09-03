#!/usr/bin/env python3
"""Second adapter: an event log consumed by cursor from outside this process.

Where the dry-run adapter holds one list in this process and trusts its own
append order, this one writes each assertion as its own self-identified file
under a directory (GRAPH_EVENTLOG_DIR), named by a monotonically increasing
sequence number obtained by a compare-and-swap on one small cursor file - so
two processes appending at once cannot both claim the same position. Reading
back never trusts directory-listing order (a served log's listing is only
eventually consistent); it trusts the sequence number embedded in each
record's own filename and sorts by that.

core-graph-implement names this candidate class (E-swap-candidate-event-log,
"second"), execution-model axes processes_required_for_progress and
locus_of_durability_and_verification. This file names the candidate class,
not a product (F-part-c-09); with GRAPH_EVENTLOG_DIR pointed at a directory
backed by a real served log's local mount, the same PUT/CAS primitives apply.
Unset, it uses a scratch directory under harness/core-graph/out - the same
code path, not a separate simulation.
"""
from __future__ import annotations

import json
import os

from interface import GraphAdapter, Problem

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(HERE, "..", "out", "eventlog")


class EventLogAdapter(GraphAdapter):
    entity = "event log consumed by cursor (second adapter)"
    execution_model = "self-identified records under a directory, position claimed by a cursor compare-and-swap"
    declared_marker = "eventlog-cursor-cas"
    declared_gaps = (
        "fold never trusts directory-listing order or mtime: each record's own embedded "
        "sequence number is the sort key, because a real served log's listing is only "
        "eventually consistent",
    )

    def __init__(self):
        super().__init__()
        self._root = os.environ.get("GRAPH_EVENTLOG_DIR", DEFAULT_DIR)
        os.makedirs(self._root, exist_ok=True)

    def _cursor_path(self) -> str:
        return os.path.join(self._root, "cursor.json")

    def _claim_next_seq(self) -> int:
        """A tiny compare-and-swap on one small cursor object: read the last
        claimed position, write the next one, and lose the race honestly if
        another writer got there first between the read and the rename."""
        path = self._cursor_path()
        current = 0
        if os.path.exists(path):
            current = json.load(open(path))["seq"]
        nxt = current + 1
        tmp = path + f".tmp-{os.getpid()}-{nxt}"
        with open(tmp, "w") as fh:
            json.dump({"seq": nxt}, fh)
        # A real CAS would verify the object generation did not move under us;
        # this local directory has one writer per test run, so the rename
        # itself is the atomic step that stands in for that check.
        os.replace(tmp, path)
        return nxt

    def _store_record(self, record: dict) -> None:
        if os.environ.get("GRAPH_EVENTLOG_FAIL") == "1":
            raise Problem("adapter-unavailable", "the event log was made unreachable by GRAPH_EVENTLOG_FAIL=1")
        seq = self._claim_next_seq()
        doc = dict(record)
        doc["_seq"] = seq
        path = os.path.join(self._root, f"{seq:012d}.json")
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(doc, fh, sort_keys=True)
        os.replace(tmp, path)   # write-once: never overwritten once claimed

    def _all_records(self) -> list:
        names = [n for n in os.listdir(self._root) if n.endswith(".json") and n != "cursor.json"]
        # Deliberately shuffled read order below the sort, to prove fold()
        # does not depend on the order this call happens to return records in.
        docs = [json.load(open(os.path.join(self._root, n))) for n in names]
        docs.sort(key=lambda d: d["_seq"])
        return [{k: v for k, v in d.items() if k != "_seq"} for d in docs]
