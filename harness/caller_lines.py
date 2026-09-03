#!/usr/bin/env python3
"""One method for the two things every harness claims about its minimal call.

TARGET T3 asks how much a caller writes, and T7.2 asks that every call reach the
component through the capability interface. Both were measured differently in
each harness before this file existed - four marker spellings, two harnesses
asserting nothing, and one caller reading an adapter's own storage by path. They
are measured here, once, for all five:

  caller lines   the non-blank, non-comment lines of call.py below its single
                 `>>> CALLER CODE` marker, up to the module entry guard
                 (`if __name__`) or the end of the file. Presentation lives
                 above the marker in every harness, so the count is interface
                 calls, the inputs handed to them, and reading one result or one
                 problem - nothing else. The bound is 40 (the author brief).

  storage named  a call.py may not name a file in an adapter's own storage.
                 An adapter keeps its state where it likes; a caller that opens
                 it by path has left the interface and would break the moment a
                 hosted component answered instead. Configuration the caller
                 does own (binding.json, an envelope it wrote) is not storage,
                 so the rule is the storage suffixes below, not "no open()".

Usage:

    python3 harness/caller_lines.py                 the table, exit 1 if a rule fails
    python3 harness/caller_lines.py workflow --count        the number alone
    python3 harness/caller_lines.py workflow --interface-only   the storage rule

Python 3.11 standard library only. No product name appears here.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HARNESS = os.path.dirname(os.path.abspath(__file__))
HARNESSES = ("containment", "gateway", "observability", "workflow", "linked")
MARKER = ">>> CALLER CODE"
GUARD = "if __name__"
BOUND = 40
STORAGE_SUFFIXES = (".jsonl", ".ndjson", ".db", ".sqlite", ".sqlite3", ".journal")
STORAGE = re.compile(r"""["'][^"']*(""" + "|".join(s.replace(".", r"\.") for s in STORAGE_SUFFIXES) + r""")["']""")


def call_py(name: str) -> str:
    return os.path.join(HARNESS, name, "call.py")


def region(name: str) -> list[str]:
    """The caller region: below the one marker, above the entry guard."""
    with open(call_py(name)) as fh:
        lines = fh.read().splitlines()
    marks = [i for i, line in enumerate(lines) if MARKER in line]
    if len(marks) != 1:
        raise SystemExit(f"{name}/call.py: expected exactly one {MARKER!r} marker, "
                         f"found {len(marks)}")
    body = lines[marks[0] + 1:]
    end = next((i for i, line in enumerate(body) if line.startswith(GUARD)), len(body))
    return [line for line in body[:end]
            if line.strip() and not line.strip().startswith("#")]


def count(name: str) -> int:
    return len(region(name))


def storage_hits(name: str) -> list[tuple[int, str]]:
    """Lines of call.py that name a file in an adapter's own storage."""
    with open(call_py(name)) as fh:
        return [(n, line.strip()) for n, line in enumerate(fh, 1)
                if STORAGE.search(line)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("harness", nargs="?", choices=HARNESSES)
    ap.add_argument("--count", action="store_true", help="print the number alone")
    ap.add_argument("--interface-only", action="store_true",
                    help="exit 1 if call.py names an adapter's own storage")
    args = ap.parse_args(argv)

    if args.harness and args.count:
        print(count(args.harness))
        return 0
    if args.harness and args.interface_only:
        hits = storage_hits(args.harness)
        for n, line in hits:
            print(f"{args.harness}/call.py:{n}: names adapter storage: {line}")
        return 1 if hits else 0

    names = [args.harness] if args.harness else list(HARNESSES)
    rows, failed = [], 0
    for name in names:
        lines, hits = count(name), storage_hits(name)
        failed += (lines >= BOUND) + bool(hits)
        rows.append((name, str(lines), "yes" if lines < BOUND else "NO",
                     "none" if not hits else f"{len(hits)} LINE(S)"))
    header = ("harness", "caller lines", f"under {BOUND}", "adapter storage named")
    widths = [max(len(r[i]) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(h.ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
