#!/usr/bin/env python3
"""Check STATUS.md stays a single clean table.

Usage: python3 tools/status_check.py [STATUS.md]
Rules (errors):
  - the file is one heading and one table, nothing else
  - columns are exactly: #, Work item, Definition of done, Status, Result
  - rows are numbered 1..n contiguously
  - Status is one of: Done, In progress, Open, Blocked, Not started
  - every cell is one statement: no semicolons, no parentheses, no " and then ", no "depends", "after", "requires", "blocked by"
  - a cell has at most 12 words; the Work item cell at most 5
  - a Done row's Result is not empty and not "Awaiting" anything
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

COLUMNS = ["#", "Work item", "Definition of done", "Status", "Result"]
STATUSES = {"Done", "In progress", "Open", "Blocked", "Not started"}
BANNED = ["depends", "after ", "requires", "blocked by", " and then ", ";", "(", ")"]
LIMITS = {"Work item": 5, "Definition of done": 12, "Status": 2, "Result": 8}


def main(path: str) -> int:
    lines = [l.rstrip("\n") for l in Path(path).read_text().splitlines()]
    errs: list[str] = []
    body = [l for l in lines if l.strip()]
    if not body or not body[0].startswith("# "):
        errs.append("first line must be a single heading")
    table = [l for l in body[1:] if l.startswith("|")]
    other = [l for l in body[1:] if not l.startswith("|")]
    if other:
        errs.append(f"only a table is allowed; found prose: {other[0][:60]!r}")
    if len(table) < 3:
        errs.append("table needs a header, a separator, and at least one row")
        print("\n".join(errs)); return 1
    header = [c.strip() for c in table[0].strip("|").split("|")]
    if header != COLUMNS:
        errs.append(f"columns must be {COLUMNS}, found {header}")
    expect = 1
    for raw in table[2:]:
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if len(cells) != len(COLUMNS):
            errs.append(f"row {raw[:30]!r}: {len(cells)} cells, expected {len(COLUMNS)}"); continue
        row = dict(zip(COLUMNS, cells))
        if row["#"] != str(expect):
            errs.append(f"row numbering: expected {expect}, found {row['#']!r}")
        expect += 1
        if row["Status"] not in STATUSES:
            errs.append(f"row {row['#']}: status {row['Status']!r} not in {sorted(STATUSES)}")
        for col, limit in LIMITS.items():
            words = len(row[col].split())
            if words > limit:
                errs.append(f"row {row['#']}: {col} has {words} words, limit {limit}")
            low = " " + row[col].lower() + " "
            for b in BANNED:
                if b in low:
                    errs.append(f"row {row['#']}: {col} contains {b.strip()!r}")
            if not row[col]:
                errs.append(f"row {row['#']}: {col} is empty")
        if row["Status"] == "Done" and row["Result"].lower().startswith("awaiting"):
            errs.append(f"row {row['#']}: Done but result is pending")
    for e in errs:
        print("error:", e)
    print(f"{expect - 1} rows, {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "STATUS.md"))
