#!/usr/bin/env python3
"""Move Done rows from STATUS.md to STATUS-ARCHIVE.md, keeping row numbers.

Usage: python3 tools/status_archive.py            archive every Done row
       python3 tools/status_archive.py --dry-run  show what would move
The archive has the same five columns plus Closed (date and commit). Rows are appended, never rewritten.
"""
from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE, ARCH = ROOT / "STATUS.md", ROOT / "STATUS-ARCHIVE.md"
ARCH_HEADER = ["# Status archive", "", "| # | Work item | Definition of done | Status | Result | Closed |", "|---|---|---|---|---|---|"]


def rows(path: Path):
    lines = path.read_text().splitlines() if path.is_file() else []
    head = [l for l in lines if not l.startswith("|")]
    table = [l for l in lines if l.startswith("|")]
    return head, table[:2], table[2:]


def main(dry: bool) -> int:
    head, hdr, body = rows(LIVE)
    done = [r for r in body if r.split("|")[4].strip() == "Done"]
    keep = [r for r in body if r.split("|")[4].strip() != "Done"]
    if not done:
        print("nothing to archive"); return 0
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    closed = f"{datetime.date.today().isoformat()} {sha}"
    if dry:
        for r in done: print("would archive:", r[:80]); return 0
    ahead, ahdr, abody = rows(ARCH)
    if not ahdr:
        ahead, ahdr, abody = ARCH_HEADER[:2], ARCH_HEADER[2:], []
    seen = {r.split("|")[1].strip() for r in abody}
    new = [r.rstrip().rstrip("|").rstrip() + f" | {closed} |" for r in done if r.split("|")[1].strip() not in seen]
    ARCH.write_text("\n".join([*[l for l in ahead if l.strip()], "", *ahdr, *abody, *new]) + "\n")
    LIVE.write_text("\n".join([*[l for l in head if l.strip()], "", *hdr, *keep]) + "\n")
    print(f"archived {len(new)} rows; {len(keep)} live rows remain")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
