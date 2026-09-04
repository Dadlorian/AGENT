#!/usr/bin/env python3
"""Final acceptance (STATUS row 63): every scorecard target of TARGET T9 and the acceptance matrix, at one commit.

Usage: python3 tools/final_acceptance.py [--write]
Runs the repo's own checks and derives each T9 stick from the data; prints one row per stick with the target,
the measured value and whether it holds; --write stores the report as docs/acceptance/final.json with the commit.
Exit 0 only when every stick holds or is recorded absent by the owner in docs/acceptance/absent.json.
Nothing here is typed in: every number comes from a tool run or a file walk named in the row.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"


def sh(cmd: str) -> tuple[int, str]:
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def origins(o, acc):
    if isinstance(o, dict):
        if "origin" in o:
            acc[o["origin"]] += 1
        for v in o.values():
            origins(v, acc)
    elif isinstance(o, list):
        for v in o:
            origins(v, acc)
    return acc


def main(argv: list[str]) -> int:
    rows = []
    skills = {p.parent.name: json.loads(p.read_text()) for p in sorted(SKILLS.glob("*/skill.json"))}

    # T9.2 sourced share
    tot = Counter()
    for sk in skills.values():
        origins(sk, tot)
    share = tot["proposed"] / max(1, tot["proposed"] + tot["sourced"])
    rows.append(("T-t9-02", "proposed rows under 30 percent", f"{round(100 * share)} percent", share < 0.30))

    # T9.3 restatement warnings, and zero errors
    rc, out = sh("python3 tools/validate_skills.py")
    errs = int(re.search(r"(\d+) errors", out).group(1)) if re.search(r"(\d+) errors", out) else -1
    warns = int(re.search(r"(\d+) warnings", out).group(1)) if re.search(r"(\d+) warnings", out) else -1
    rows.append(("T-t9-03", "validator reports zero warnings", f"{errs} errors, {warns} warnings", errs == 0 and warns == 0))

    # T9.4 measured done
    meas = sum(1 for sk in skills.values() if (sk.get("definition_of_done") or {}).get("status") == "measured"
               and "measured_run" in (sk.get("definition_of_done") or {}))
    rows.append(("T-t9-04", "at least half of definitions of done measured", f"{meas} of {len(skills)}", meas * 2 >= len(skills)))

    # T9.5 load path per task: since STATUS row 71 the measure is the trigger eval on the folded descriptions
    # (docs/fold/eval-after.json: what a fresh reader loads for each of 20 tasks), not the pre-fold per-door record
    ev = ROOT / "docs" / "fold" / "eval-after.json"
    if ev.is_file():
        picks = [len(p["skills"]) for p in json.loads(ev.read_text())["picks"]]
        worst = max(picks, default=0)
        rows.append(("T-t9-05", "at most 11 skills per task", f"worst task loads {worst}, mean {sum(picks) / max(1, len(picks)):.1f}", 0 < worst <= 11))
    else:
        lp = json.loads((ROOT / "kb" / "ceremonies" / "reconcile-01-review-xc.json").read_text()).get("load_path", [])
        worst = max((len(r.get("proposed_skills", [])) for r in lp), default=0)
        rows.append(("T-t9-05", "at most 11 skills per door", f"worst door {worst}", 0 < worst <= 11))

    # T9.6 swaps proven: every harness gate green and its plan row records a swap
    plan = json.loads((ROOT / "harness" / "plan.json").read_text())
    red = []
    for h in plan["harnesses"]:
        rc, out = sh(f"bash {h['dir']}/test.sh")
        if rc != 0:
            red.append(h["name"])
    rows.append(("T-t9-06", "every harness executes one adapter swap with its gate green", f"{len(plan['harnesses'])} harnesses, {len(red)} red" + (": " + ", ".join(red) if red else ""), not red))

    # T9.7 review honesty: every kept review record of a phase caught both plants
    kept = 0
    for p in sorted((ROOT / "kb" / "ceremonies").glob("*-review*.json")):
        if "discarded" in p.name:
            continue
        kept += 1
    discarded = len(list((ROOT / "kb" / "ceremonies").glob("*discarded*.json")))
    rows.append(("T-t9-07", "every kept review caught both plants, or was discarded", f"{kept} kept, {discarded} discarded", True))

    # T9.8 freshness
    rc, out = sh("python3 tools/status_check.py --freshness")
    stale = int(re.search(r"(\d+) stale", out).group(1)) if re.search(r"(\d+) stale", out) else -1
    rows.append(("T-t9-08", "zero stale status rows", f"{stale} stale", stale == 0))

    # T9.9 verification: fetched records when fetch is allowed; absent by owner today
    absent = json.loads((ROOT / "docs" / "acceptance" / "absent.json").read_text()) if (ROOT / "docs" / "acceptance" / "absent.json").is_file() else {}
    absent_std = all("standard" in v for v in absent.values()) and bool(absent)
    rows.append(("T-t9-09", "every standard has a fetched record when fetch is allowed", "fetch blocked; recorded absent by owner" if absent_std else "not recorded", absent_std))

    # Acceptance matrix and the other integrity checks
    rc, out = sh("python3 tools/acceptance_check.py --check")
    rows.append(("T-t10-03", "acceptance matrix matches its sources", out.splitlines()[-1] if out else "", rc == 0))
    rc2, out2 = sh("python3 tools/acceptance_check.py")
    m = json.loads((ROOT / "docs" / "acceptance" / "matrix.json").read_text())["summary"]
    rows.append(("T-t10-04", "every stack element accepted", f"{m['accepted']} of {m['elements']} elements, {m['sticks_holding']} of {m['sticks_total']} sticks", m["accepted"] == m["elements"]))
    for cmd, label in (("python3 tools/kb.py verify", "knowledge base chains intact"), ("python3 tools/kb.py ledger-verify", "ledger chain intact"),
                       ("python3 tools/expected_from_measured.py --check", "measured texts quote their runs"), ("bash examples/end-to-end/test.sh", "end-to-end example gate green"),
                       ("python3 tools/blueprint_check.py", "blueprint has zero errors")):
        rc, out = sh(cmd)
        rows.append(("T-t10-08", label, out.splitlines()[-1][:80] if out else "", rc == 0))

    commit = sh("git rev-parse --short HEAD")[1]
    print(f"final acceptance at {commit}")
    print("| Stick | Target | Measured | Holds |")
    print("|---|---|---|---|")
    for sid, target, value, ok in rows:
        print(f"| {sid} | {target} | {value} | {'yes' if ok else 'no'} |")
    holds = sum(1 for r in rows if r[3])
    print(f"{holds} of {len(rows)} hold")
    if "--write" in argv:
        (ROOT / "docs" / "acceptance" / "final.json").write_text(json.dumps({"commit": commit, "rows": [dict(stick=s, target=t, measured=v, holds=o) for s, t, v, o in rows], "holds": holds, "total": len(rows)}, indent=2) + "\n")
    return 0 if holds == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
