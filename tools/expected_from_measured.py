#!/usr/bin/env python3
"""Make a measured definition of done's expected texts say what the measured run actually printed.

Usage: python3 tools/expected_from_measured.py <skill> [<skill> ...]     rewrite and re-render
       python3 tools/expected_from_measured.py --check                    exit 1 and list skills whose texts drift

A measured skill's `expected` and `expected_failure` were authored before the run and often describe a later stage
the command chain never reaches (a gate that fails first short-circuits what follows; review 61-review-c, 2026-09-03).
For a skill whose measured_run exists, this tool sets both fields from the run's own output, keeps the authored text
under `expected_design` / `expected_failure_design` the first time, and never touches status or measured_run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"


def tail(text: str, n: int = 2) -> str:
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return " | ".join(lines[-n:]) if lines else "(no output)"


def derived(dd: dict) -> tuple[str, str]:
    m = dd["measured_run"]
    exp = f"Measured by tools/measure.py at {m.get('commit', '?')}: exit {m.get('clean_exit')}; last lines: {tail(m.get('clean_output', ''))}"
    fail = f"Measured by tools/measure.py at {m.get('commit', '?')}: exit {m.get('breakage_exit')}; last lines: {tail(m.get('breakage_output', ''))}"
    return exp, fail


def drifts(dd: dict) -> bool:
    exp, fail = derived(dd)
    return dd.get("expected") != exp or dd.get("expected_failure") != fail


def main(argv: list[str]) -> int:
    if argv[:1] == ["--check"]:
        bad = []
        for sj in sorted(SKILLS.glob("*/skill.json")):
            dd = json.loads(sj.read_text()).get("definition_of_done") or {}
            if dd.get("status") == "measured" and "measured_run" in dd and drifts(dd):
                bad.append(sj.parent.name)
        print(f"{len(bad)} measured skills whose expected texts drift from their measured run" + (": " + ", ".join(bad) if bad else ""))
        return 1 if bad else 0
    for name in argv:
        sj = SKILLS / name / "skill.json"
        sk = json.loads(sj.read_text())
        dd = sk["definition_of_done"]
        if dd.get("status") != "measured" or "measured_run" not in dd:
            print(f"{name}: not measured, left alone"); continue
        exp, fail = derived(dd)
        dd.setdefault("expected_design", dd.get("expected", ""))
        dd.setdefault("expected_failure_design", dd.get("expected_failure", ""))
        dd["expected"], dd["expected_failure"] = exp, fail
        sj.write_text(json.dumps(sk, indent=2, ensure_ascii=False) + "\n")
        subprocess.run(["python3", "tools/render_skill.py", f".claude/skills/{name}"], cwd=ROOT, capture_output=True)
        print(f"{name}: expected texts now quote the measured run")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
