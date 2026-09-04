#!/usr/bin/env python3
"""Per-skill health, read at a ceremony by the self-improvement loop (STATUS row 72): was it used, how well, and how far from the target.

Usage: python3 tools/skill_health.py [--json]
One row per skill on disk. Every number comes from a record:
  used        loads recorded in state/usage.jsonl (the PreToolUse hook), counting former names that folded into it
  findings    review findings naming it or a former name across kb/ceremonies/*review*.json; open = not in any improve record's applied or declined
  warnings    validator warnings under its name today
  done        definition_of_done.status (measured or claimed) and the commit of the measured run
  target      the litmus scorecard for the PASS.md rows it owns (docs/litmus/scorecard.json): median score and the misaligned or absent question ids;
              the target is TARGET.md's future state, so a median under 2 (aligned) marks the skill an improvement candidate
Candidates print first: misaligned or absent answers, then median under 2, then open findings, then never used.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def main(argv: list[str]) -> int:
    plan = json.loads((ROOT / "docs" / "fold" / "plan.json").read_text())
    to_target = {s: t["name"] for t in plan["targets"] for s in t["sources"]}
    names = sorted(p.name for p in SKILLS.iterdir() if (p / "skill.json").is_file())
    for n in names:
        to_target.setdefault(n, n)
    used = Counter(to_target.get(r["skill"], r["skill"]) for r in jl(ROOT / "state" / "usage.jsonl"))
    findings, resolved = defaultdict(list), set()
    for p in sorted((ROOT / "kb" / "ceremonies").glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        for f in d.get("findings", []) if isinstance(d.get("findings"), list) else []:
            if isinstance(f, dict) and f.get("skill") and f.get("id"):
                findings[to_target.get(f["skill"].split(",")[0].strip(), f["skill"])].append(f["id"])
        for k in ("applied", "declined"):
            for a in d.get(k, []) if isinstance(d.get(k), list) else []:
                if isinstance(a, dict):
                    resolved.add(a.get("finding") or a.get("id"))
    out = subprocess.run(["python3", "tools/validate_skills.py"], cwd=ROOT, capture_output=True, text=True).stdout
    warns = Counter(m.group(1) for m in re.finditer(r"^warning:\s+([a-z0-9-]+):", out, re.M))
    score = {}
    sc = ROOT / "docs" / "litmus" / "scorecard.json"
    if sc.is_file():
        q = {s["id"]: s for s in json.loads((ROOT / "docs" / "litmus" / "questionnaire.json").read_text())["sections"]}
        for s in json.loads(sc.read_text())["sections"]:
            key = s["id"].replace("concern-", "")
            skill = f"cap-{key}" if f"cap-{key}" in names else ("xc-guarantees" if key in ("budget",) else None)
            if skill:
                score.setdefault(skill, {"medians": [], "flags": []})
                score[skill]["medians"].append(s["median"])
                score[skill]["flags"] += s.get("misaligned", []) + s.get("absent", [])
    rows = []
    for n in names:
        sk = json.loads((SKILLS / n / "skill.json").read_text())
        dd = sk.get("definition_of_done", {})
        fl = findings.get(n, [])
        open_f = [f for f in fl if f not in resolved]
        t = score.get(n)
        median = (sum(t["medians"]) / len(t["medians"])) if t else None
        flags = t["flags"] if t else []
        cand = bool(flags) or (median is not None and median < 2) or bool(open_f) or used[n] == 0
        rows.append({"skill": n, "used": used[n], "findings": len(fl), "open": len(open_f), "warnings": warns[n],
                     "done": dd.get("status"), "measured_at": (dd.get("measured_run") or {}).get("commit"),
                     "target_median": median, "target_flags": flags, "candidate": cand,
                     "rank": (0 if flags else 1 if (median is not None and median < 2) else 2 if open_f else 3 if used[n] == 0 else 4)})
    rows.sort(key=lambda r: (r["rank"], r["skill"]))
    if "--json" in argv:
        print(json.dumps(rows, indent=1)); return 0
    print("| Skill | Used | Findings (open) | Warnings | Done | Target median | Flags | Candidate |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['skill']} | {r['used']} | {r['findings']} ({r['open']}) | {r['warnings']} | {r['done'] or '-'}{' @' + r['measured_at'] if r['measured_at'] else ''} | {r['target_median'] if r['target_median'] is not None else '-'} | {', '.join(r['target_flags']) or '-'} | {'yes' if r['candidate'] else 'no'} |")
    print(f"\n{sum(1 for r in rows if r['candidate'])} of {len(rows)} skills are improvement candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
