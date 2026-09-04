#!/usr/bin/env python3
"""Score a trigger eval (STATUS row 71): did the descriptions alone lead a fresh reader to the right skill?

Usage: python3 tools/trigger_eval.py score before|after
Reads docs/fold/trigger-prompts.json (20 tasks, each with expect_before and expect_after) and docs/fold/eval-<which>.json
(the picks a reader made from the descriptions alone). Prints hit rate (an expected skill is among the picks),
first-pick rate (the first pick is expected), mean picks per task, and the misses.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "score":
        print(__doc__); return 2
    which = argv[1]
    prompts = json.loads((ROOT / "docs" / "fold" / "trigger-prompts.json").read_text())["prompts"]
    picks = {p["id"]: p["skills"] for p in json.loads((ROOT / "docs" / "fold" / f"eval-{which}.json").read_text())["picks"]}
    key = f"expect_{which}"
    hit = first = 0
    n_picks = 0
    misses = []
    for p in prompts:
        exp, got = set(p[key]), picks.get(p["id"], [])
        n_picks += len(got)
        if exp & set(got):
            hit += 1
        if got and got[0] in exp:
            first += 1
        else:
            misses.append((p["id"], sorted(exp), got[:3]))
    n = len(prompts)
    print(f"{which}: {n} tasks, hit {hit}/{n}, first pick right {first}/{n}, mean picks {n_picks / n:.1f}")
    for m in misses:
        print("  miss:", m[0], "expected", m[1], "got", m[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
