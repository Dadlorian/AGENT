#!/usr/bin/env python3
"""Dry-run adapter: an in-memory assertion log. No disk, no network.

Execution model: a single mutable list held by this process, order is
append (call) order - the axis the second adapter (records self-identified
by sequence, consumed by cursor from a directory) deliberately breaks.
"""
from __future__ import annotations

import os

from interface import GraphAdapter, Problem


class DryRunAdapter(GraphAdapter):
    entity = "in-memory assertion log (dry run)"
    execution_model = "single mutable list held by this process, order is append order"
    declared_marker = "dryrun-graph-store"

    def __init__(self):
        super().__init__()
        self._records: list = []

    def _store_record(self, record: dict) -> None:
        if os.environ.get("DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable", "the dry-run store was made unreachable by DRYRUN_FAIL=1")
        self._records.append(dict(record))

    def _all_records(self) -> list:
        return list(self._records)
