#!/usr/bin/env python3
"""One-off migration: split docs/standards/standards.json into standards/<id>/standard.json,
one file per standard, plus standards/registry.json for the shared top-level fields, and copy
docs/journey/journey.json to standards/journey.json verbatim.

Every field is copied as-is -- nothing is retyped by hand, nothing is dropped, nothing is
renamed. The `id` string is preserved exactly because kb/entities.jsonl (E-standard-<id>),
skill.json contracts and docs/journey/journey.json steps[].standards[] already key on it.

The `journey` field stays on each standard.json for now even though the target design moves
that relationship to kb/edges.jsonl -- dropping it here would break the byte-identical render
proof this migration exists to pass. Removing it is a later, separate step once the edges
exist and are proven equivalent.

Originals at docs/standards/standards.json and docs/journey/journey.json are not touched by
this script. Run once; re-running overwrites standards/<id>/ and standards/registry.json.

Usage: python3 tools/migrate_standards.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_REG = ROOT / "docs/standards/standards.json"
SRC_JOUR = ROOT / "docs/journey/journey.json"
OUT = ROOT / "standards"


def main():
    reg = json.loads(SRC_REG.read_text())
    entries = reg["standards"]
    registry_top = {k: v for k, v in reg.items() if k != "standards"}
    # Explicit order list: the folder-per-standard split has no other way to remember the
    # original array's sequence, and that sequence is what today's rendered tables show.
    registry_top["order"] = [e["id"] for e in entries]

    OUT.mkdir(exist_ok=True)
    # No sort_keys: preserve the source file's own key order (e.g. reg["ladder"]'s order
    # drives the "Where we are" table's row order in STANDARDS.md).
    (OUT / "registry.json").write_text(json.dumps(registry_top, indent=2) + "\n")

    for entry in entries:
        sid = entry["id"]
        d = OUT / sid
        d.mkdir(exist_ok=True)
        (d / "standard.json").write_text(json.dumps(entry, indent=2) + "\n")

    shutil.copyfile(SRC_JOUR, OUT / "journey.json")

    print(f"wrote standards/registry.json, {len(entries)} standards/<id>/standard.json, standards/journey.json")


if __name__ == "__main__":
    main()
