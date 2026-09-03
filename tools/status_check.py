#!/usr/bin/env python3
"""Check STATUS.md stays a single clean table.

Usage: python3 tools/status_check.py [STATUS.md]
Rules (errors):
  - the file is one heading and one table, nothing else
  - columns are exactly: #, Work item, Definition of done, Status, Result
  - live row numbers strictly increase (gaps allowed); archive rows are in closing order with unique numbers
  - STATUS-ARCHIVE.md uses the same columns plus Closed, and every row is Done
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
ARCH_COLUMNS = COLUMNS + ["Closed"]
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
    cols = ARCH_COLUMNS if header == ARCH_COLUMNS else COLUMNS
    if header != cols:
        errs.append(f"columns must be {COLUMNS} or {ARCH_COLUMNS}, found {header}")
    last = 0
    seen_nums = set()
    for raw in table[2:]:
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if len(cells) != len(cols):
            errs.append(f"row {raw[:30]!r}: {len(cells)} cells, expected {len(cols)}"); continue
        row = dict(zip(cols, cells))
        try:
            n = int(row["#"])
        except ValueError:
            errs.append(f"row number {row['#']!r} is not an integer"); n = last + 1
        if cols is ARCH_COLUMNS:
            if n in seen_nums:
                errs.append(f"row number {n} appears twice in the archive")
        elif n <= last:
            errs.append(f"row numbering must increase: {n} after {last}")
        seen_nums.add(n)
        last = n
        if cols is ARCH_COLUMNS and row["Status"] != "Done":
            errs.append(f"row {n}: archive rows must be Done")
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
    print(f"{path}: {last and len(table) - 2} rows, {len(errs)} errors")
    return 1 if errs else 0


def freshness() -> int:
    """Row 44 gate: no Done row left in the live table, and every row that says an agent is running has a live scope claim."""
    import json as _json
    errs = []
    lines = [l for l in Path("STATUS.md").read_text().splitlines() if l.startswith("|")][2:]
    claims = _json.loads(Path("state/agent-scopes.json").read_text()) if Path("state/agent-scopes.json").is_file() else {}
    for raw in lines:
        c = [x.strip() for x in raw.strip("|").split("|")]
        n, item, status, result = c[0], c[1], c[3], c[4]
        if status == "Done":
            errs.append(f"row {n}: Done but not archived")
        if "running" in result.lower():
            words = [w.lower() for w in item.split() if len(w) > 3]
            if not any(any(w in k.lower() for w in words) for k in claims):
                errs.append(f"row {n}: says running but no live scope claim matches '{item}'")
    for e in errs:
        print("stale:", e)
    print(f"freshness: {len(lines)} live rows, {len(claims)} claims, {len(errs)} stale")
    return 1 if errs else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--freshness"]:
        sys.exit(freshness())
    targets = sys.argv[1:] or [p for p in ("STATUS.md", "STATUS-ARCHIVE.md") if Path(p).is_file()]
    sys.exit(max(main(t) for t in targets))
