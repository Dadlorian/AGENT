#!/usr/bin/env python3
"""Dry-run adapter: deterministic checks, in process, no network.

Same execution model as today's in-place checker (F-b3-09): a schema is read
and walked fresh on every validate() call, no compiled artifact is kept beyond
the raw schema document. Reads schema files straight off this repo's disk (no
env var, no network, no key) -- deterministic because the files are static, and
that is what makes this adapter usable with zero configuration, including
against the platform's real shipped schemas.
"""
from __future__ import annotations

import os

from interface import (DIALECT_2020_12, DocumentValidationAdapter, PreparedHandle,
                       Problem, REPO_ROOT, load_json_file, resolve_path)
from adapters._walk import check as walk_check

HERE = os.path.dirname(os.path.abspath(__file__))


class DryRunAdapter(DocumentValidationAdapter):
    entity = "dry-run in-process checker (walk-per-document)"
    execution_model = "schema read per call"
    processes_required_for_progress = 0
    declared_marker = "dryrun-walk"

    def _read_schema(self, schema_uri: str) -> dict:
        if os.environ.get("DRYRUN_FAIL") == "1":         # the failure path, exercised on demand
            raise Problem("schema-unavailable", "the dry-run schema store was made unreachable by DRYRUN_FAIL=1",
                          schema_uri=schema_uri, retry_after_s=1)
        path = resolve_path(schema_uri, REPO_ROOT)
        return load_json_file(path, schema_uri)

    def _compile(self, schema_doc: dict) -> object:
        self.schema_reads += 1     # a no-op compile: the raw document is what gets walked, every call
        return schema_doc

    def _check(self, handle: PreparedHandle, instance) -> tuple[list, int]:
        self.schema_reads += 1     # walked fresh again for this instance -- nothing was cached from prepare
        return walk_check(handle.compiled, instance)


Adapter = DryRunAdapter
