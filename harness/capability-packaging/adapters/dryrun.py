#!/usr/bin/env python3
"""Dry-run adapter: three fixture packages, in process, no filesystem, no network.

Same bytes every run, so a gate can assert on them. Source is "directory":
identity is a path-shaped name and digest is always None (F-b3-07's adapter
today has no digest to offer). One fixture is well-formed, one is missing its
required description field, and one has drifted so its declared name no longer
matches the identity that resolves it — the three refusal cases every adapter
must produce identically (T-t9-06).
"""
from __future__ import annotations

import os

from interface import CapabilityPackagingAdapter, Problem

FIXTURES = {
    "quickstart-parser": {
        "resident": {"name": "quickstart-parser",
                     "description": "Parses a quickstart config. Load when a request names a "
                                    "starter template."},
        "body": "# quickstart-parser\n\nRead the starter config and emit a build plan.",
        "references": {"references/schema.md": "# schema\n\nThe starter config schema, opened "
                                                "only when a caller needs the field list."},
    },
    "broken-legacy-importer": {
        # missing "description" on purpose: the refusal path every adapter must exercise
        "resident": {"name": "broken-legacy-importer"},
        "body": "# broken-legacy-importer\n\nnever reached: resolve() refuses before this loads.",
        "references": {},
    },
    "drifted-directory": {
        # frontmatter still says the old name; the directory (identity) was renamed around it
        "resident": {"name": "old-widget-importer", "description": "Imports the legacy widget feed."},
        "body": "# drifted-directory\n\nnever reached: resolve() refuses before this loads.",
        "references": {},
    },
}


class DryRunAdapter(CapabilityPackagingAdapter):
    entity = "dry-run in-process fixture packages"
    source = "directory"
    declared_marker = "dryrun-directory-scan"

    def _scan_all(self) -> dict:
        if os.environ.get("DRYRUN_FAIL") == "1":       # the failure path, exercised on demand
            raise Problem("adapter-unavailable",
                          "the dry-run source was made unreachable by DRYRUN_FAIL=1", retry_after_s=1)
        return FIXTURES

    def _locate(self, identity: str) -> dict | None:
        if os.environ.get("DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable",
                          "the dry-run source was made unreachable by DRYRUN_FAIL=1", retry_after_s=1)
        return FIXTURES.get(identity)

    def _read_body(self, identity: str) -> str:
        return FIXTURES[identity]["body"]

    def _list_references(self, identity: str) -> list[str]:
        return sorted(FIXTURES[identity]["references"])

    def _read_reference(self, identity: str, reference_path: str) -> str:
        return FIXTURES[identity]["references"][reference_path]

    def _digest(self, identity: str, raw: dict) -> str | None:
        return None                                    # identity is a path; no digest to offer


# The one name every adapter module exports: the entry point of this module.
# Binding is by module, never by a per-capability class-name table. The
# descriptive class name above stays — a report still says which adapter answered.
Adapter = DryRunAdapter
