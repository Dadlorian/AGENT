#!/usr/bin/env python3
"""The next ceremony number, read off disk.

A ceremony number is a repository-global counter. It used to be computed positionally by the
orchestration script and handed to agents as a hint, with a paragraph in two prompts telling the
model the hint was "stale four sections running, so treat it as a guess". state/loop.json records
the result: "Ninth collision in a row; the fix cannot reach a running workflow". The disk shows
it plainly -- numbering stops at 11 with three suffixed variants (-compose, -round, -xc) where
12 and 13 belong.

A counter is a category someone already discovered. Applying it is script work, not agent work,
so it lives here and the prompts lose the paragraph.

  python3 tools/ceremony_next.py           print the next number
  python3 tools/ceremony_next.py --check   exit 1 if any number is used twice
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CEREMONIES = ROOT / "kb" / "ceremonies"
PATTERN = re.compile(r"^ceremony-(\d+)(?:-([a-z0-9]+))?-(review|improve)(?:-(.+))?\.json$")


def used() -> dict:
    """number -> the suffixes recorded under it. A suffix is how a collision was worked around,
    so more than one suffix on a number is the collision still sitting there."""
    out = {}
    if not CEREMONIES.is_dir():
        return out
    for p in sorted(CEREMONIES.glob("ceremony-*.json")):
        m = PATTERN.match(p.name)
        if not m:
            continue
        n = int(m.group(1))
        suffix = m.group(4) or m.group(2) or ""
        out.setdefault(n, set()).add(suffix)
    return out


def main() -> int:
    seen = used()
    nxt = (max(seen) + 1) if seen else 1
    if "--check" not in sys.argv:
        print(nxt)
        return 0
    collided = {n: sorted(s for s in v if s) for n, v in seen.items()
                if len([s for s in v if s]) > 1}
    for n, suffixes in sorted(collided.items()):
        print(f"error:  ceremony {n} carries {len(suffixes)} suffixed variants "
              f"({', '.join(suffixes)}) - each was a separate ceremony that collided on one "
              f"number; they belong at {n}, {n + 1}, {n + 2}...")
    print(f"{len(seen)} ceremony numbers used, highest {max(seen) if seen else 0}, "
          f"next {nxt}, {len(collided)} collided")
    return 1 if collided else 0


if __name__ == "__main__":
    sys.exit(main())
