#!/usr/bin/env python3
"""Run every LIVE example area's own gate, and discover them rather than listing them.

phase.py ran thirteen gates and none of them looked at examples/, so a phase could close green
while the example area it was built to produce was broken or absent. This closes that: the loop
decides from an exit code instead of from an agent's report of its own work.

Discovery, not a hardcoded list, on purpose. Every artifact in this repo that hardcoded the seven
example areas went stale when they were archived (STATUS row 86, seven artifacts). A gate that
globs cannot go stale the same way: a new area under examples/reference/ is gated the moment it
exists, and an archived one stops being gated the moment it moves.

  python3 tools/examples_gate.py          run every live area's test.sh
  python3 tools/examples_gate.py --list   name what would run, run nothing
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


def areas() -> list:
    """Live areas only: examples/<area>/test.sh and examples/reference/<area>/test.sh.
    examples/archived/ is deliberately excluded -- it is kept as evidence, not as work."""
    found = []
    for path in sorted(EXAMPLES.glob("*/test.sh")):
        if path.parent.name != "archived":
            found.append(path)
    found += sorted(EXAMPLES.glob("reference/*/test.sh"))
    return found


def main() -> int:
    found = areas()
    if "--list" in sys.argv:
        for p in found:
            print(f"  {p.relative_to(ROOT)}")
        print(f"{len(found)} live example gate(s)")
        return 0
    if not found:
        print("no live example areas yet; nothing to gate "
              "(examples/reference/ is empty by design until STATUS row 79)")
        return 0
    failed = []
    for p in found:
        r = subprocess.run(["bash", str(p)], cwd=p.parent, capture_output=True,
                           text=True, timeout=900)
        tail = (r.stdout + r.stderr).strip().splitlines()
        last = tail[-1][:80] if tail else ""
        print(f"  {'PASS' if r.returncode == 0 else 'FAIL'}  "
              f"{str(p.parent.relative_to(ROOT)):34} {last}")
        if r.returncode != 0:
            failed.append(str(p.parent.relative_to(ROOT)))
    print(f"{len(found) - len(failed)}/{len(found)} example gates green"
          + (f"; RED: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
