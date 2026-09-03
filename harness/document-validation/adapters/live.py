#!/usr/bin/env python3
"""Live adapter for the schema store on this host today.

PASS.md B3 records this capability's tool today only as "in place" (F-b3-09):
there is no separate network service to reach, no key, no endpoint -- the
checker examples/end-to-end/run.py carries is the component. What "live" means
here is real I/O against a real, operator-named schema store directory on this
host, reached only through DOCVALID_SCHEMA_STORE_DIR (see README.md), instead
of the harness's own bundled fixtures. Product names are allowed in this file
and nowhere else; none apply to this capability's in-place tool.

Same execution model as dryrun.py -- schema read per call -- because that is
what today's in-place checker does; the two differ only in reachability and
where the schema resource lives, which is exactly the property "live" proves.
"""
from __future__ import annotations

import os

from interface import DocumentValidationAdapter, PreparedHandle, Problem, load_json_file
from adapters._walk import check as walk_check


class LiveSchemaStoreAdapter(DocumentValidationAdapter):
    entity = "schema store on this host (DOCVALID_SCHEMA_STORE_DIR)"
    execution_model = "schema read per call"
    processes_required_for_progress = 0
    declared_marker = "live-store-walk"
    declared_gaps = ("resolves only inside the configured store; no remote $ref is fetched",)

    def _store_dir(self) -> str:
        store = os.environ.get("DOCVALID_SCHEMA_STORE_DIR")
        if not store:
            raise Problem("schema-unavailable",
                          "DOCVALID_SCHEMA_STORE_DIR is not set; the live schema store cannot be reached",
                          retry_after_s=30)
        return store

    def _read_schema(self, schema_uri: str) -> dict:
        if os.path.isabs(schema_uri):
            raise Problem("request-invalid",
                          "live mode resolves a schema_uri inside DOCVALID_SCHEMA_STORE_DIR only, "
                          "never an absolute path -- the operator-named store is the resource",
                          schema_uri=schema_uri)
        path = os.path.join(self._store_dir(), schema_uri)
        return load_json_file(path, schema_uri)

    def _compile(self, schema_doc: dict) -> object:
        self.schema_reads += 1
        return schema_doc

    def _check(self, handle: PreparedHandle, instance) -> tuple[list, int]:
        self.schema_reads += 1
        return walk_check(handle.compiled, instance)


Adapter = LiveSchemaStoreAdapter
