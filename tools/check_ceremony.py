#!/usr/bin/env python3
"""Validate a ceremony review record against its improve record.

Usage: python3 tools/check_ceremony.py <review.json> <improve.json>

Loads the review record's findings and the improve record's applied and declined lists,
then asserts: findings_checked > 0 (the review is not empty), unresolved == 0 (every
review finding id appears exactly once across applied and declined), duplicated == 0
(no finding id appears more than once across applied+declined, and none appears in both),
missing_files == 0 (every path in an applied entry's files exists on disk), and
unknown_finding_ids == 0 (every id in applied/declined names a real finding in the review).

Prints "findings_checked=N, unresolved=N, duplicated=N, missing_files=N,
unknown_finding_ids=N" and exits 0 only when findings_checked > 0 and every count is 0,
naming the offending ids otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    review = json.loads(Path(argv[0]).read_text())
    improve = json.loads(Path(argv[1]).read_text())

    finding_ids = [f["id"] for f in review.get("findings", [])]
    applied = improve.get("applied", [])
    declined = improve.get("declined", [])
    applied_ids = [a["finding"] for a in applied]
    declined_ids = [d["finding"] for d in declined]
    all_resolved = applied_ids + declined_ids

    seen: dict[str, int] = {}
    for fid in all_resolved:
        seen[fid] = seen.get(fid, 0) + 1
    duplicated_ids = sorted(fid for fid, n in seen.items() if n > 1)

    unresolved_ids = sorted(set(finding_ids) - set(all_resolved))
    unknown_ids = sorted(set(all_resolved) - set(finding_ids))

    missing = []
    for a in applied:
        for f in a.get("files", []):
            if not Path(f).is_file():
                missing.append((a.get("finding"), f))

    findings_checked = len(finding_ids)
    unresolved = len(unresolved_ids)
    duplicated = len(duplicated_ids)
    missing_files = len(missing)
    unknown_finding_ids = len(unknown_ids)

    print(
        f"findings_checked={findings_checked}, unresolved={unresolved}, "
        f"duplicated={duplicated}, missing_files={missing_files}, "
        f"unknown_finding_ids={unknown_finding_ids}"
    )
    if unresolved:
        print("unresolved:", unresolved_ids)
    if duplicated:
        print("duplicated:", duplicated_ids)
    if missing:
        print("missing_files:", missing)
    if unknown_ids:
        print("unknown_finding_ids:", unknown_ids)

    ok = (
        findings_checked > 0
        and unresolved == 0
        and duplicated == 0
        and missing_files == 0
        and unknown_finding_ids == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
