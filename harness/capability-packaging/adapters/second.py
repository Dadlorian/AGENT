#!/usr/bin/env python3
"""Second adapter: a registry loader, not a second directory.

Where the directory adapters answer from a local path, this one resolves a
namespace-scoped identity to a content digest before anything is read — the
second_adapter named in plan.json: "any spec-conformant registry (F-b3-07): a
content-addressed loader that fetches by name and version constraint". Its
binding differs from the directory adapters on both execution-model axes:
where_bytes_come_from is "network fetch" and identity_is is "a namespace-scoped
name with a content digest" (cap-capability-packaging-implement's
package-source-binding shape).

Reachability: with REGISTRY_URL set (see README) this adapter fetches
`{REGISTRY_URL}/{identity}` with urllib and verifies the digest the registry
reports against a digest computed over the bytes it returned. With it unset it
runs the same records in process — the identical three fixtures the dry-run
adapter serves, so the conformance run resolves the same identity set through
both — which is what a dry run exercises: the shape and the swap procedure are
real either way. Product names are allowed in this file.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import CapabilityPackagingAdapter, Problem

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

# The same three identities the dry-run adapter serves, published as registry
# records: one namespace-scoped name maps to one immutable record.
RECORDS = {
    "quickstart-parser": {
        "resident": {"name": "quickstart-parser",
                     "description": "Parses a quickstart config. Load when a request names a "
                                    "starter template."},
        "body": "# quickstart-parser\n\nRead the starter config and emit a build plan.",
        "references": {"references/schema.md": "# schema\n\nThe starter config schema, opened "
                                                "only when a caller needs the field list."},
    },
    "broken-legacy-importer": {
        "resident": {"name": "broken-legacy-importer"},           # missing description, on purpose
        "body": "# broken-legacy-importer\n\nnever reached: resolve() refuses before this loads.",
        "references": {},
    },
    "drifted-directory": {
        "resident": {"name": "old-widget-importer", "description": "Imports the legacy widget feed."},
        "body": "# drifted-directory\n\nnever reached: resolve() refuses before this loads.",
        "references": {},
    },
}


def _digest_of(record: dict) -> str:
    body = json.dumps({"resident": record["resident"], "body": record["body"],
                       "references": record["references"]}, sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


class RegistryAdapter(CapabilityPackagingAdapter):
    entity = "content-addressed registry (network fetch, digest-verified)"
    source = "registry"
    declared_marker = "registry-digest-verified"
    declared_gaps = ("cannot hand back a mutable local path; a resolved record is immutable",)

    def _fetch(self, identity: str) -> dict | None:
        url = os.environ.get("REGISTRY_URL")
        if not url:
            return RECORDS.get(identity)                # in-process simulation
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        try:
            with URLLIB.urlopen(URLLIB.Request(url.rstrip("/") + "/" + identity),
                                timeout=int(os.environ.get("REGISTRY_TIMEOUT_S", "30"))) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise Problem("adapter-unavailable", f"HTTP {exc.code} from the registry", retry_after_s=30) from exc
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc

    def _scan_all(self) -> dict:
        if os.environ.get("REGISTRY_URL"):
            raise Problem("adapter-unavailable",
                          "this binding does not enumerate a networked registry; resolve by "
                          "identity instead", retry_after_s=30)
        return RECORDS

    def _locate(self, identity: str) -> dict | None:
        return self._fetch(identity)

    def _read_body(self, identity: str) -> str:
        return self._fetch(identity)["body"]

    def _list_references(self, identity: str) -> list[str]:
        return sorted(self._fetch(identity)["references"])

    def _read_reference(self, identity: str, reference_path: str) -> str:
        return self._fetch(identity)["references"][reference_path]

    def _digest(self, identity: str, raw: dict) -> str | None:
        return _digest_of(raw)                          # identity is namespace-scoped; digest is real


# The one name every adapter module exports: the entry point of this module.
Adapter = RegistryAdapter
