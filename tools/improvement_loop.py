#!/usr/bin/env python3
"""The self-improvement loop, rebuilt (STATUS row 72): runs at a ceremony or phase boundary, never per iteration.

Usage:
  python3 tools/improvement_loop.py plan [N]       rank every skill by tools/skill_health.py and write state/improvement-plan.json with the top N (default 5)
  python3 tools/improvement_loop.py check          exit 1 unless every item in the plan moved toward its target (re-answered litmus score, warnings, open findings)

An item is one skill with one target drawn from the record that says what the future state looks like:
  the litmus question it scored misaligned or absent on (docs/litmus/questionnaire.json: aligned_looks_like is the target text),
  else the lowest-scoring litmus question of its section, else its open review findings, else "used at least once".
The stopping point per item is stated in the item; "make it better" without a target is not an item (owner rule, 2026-09-03).
The plan is what the next improvement phase works; it is regenerated at the next boundary from the records, never edited by hand.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "state" / "improvement-plan.json"


def health() -> list[dict]:
    return json.loads(subprocess.run(["python3", "tools/skill_health.py", "--json"], cwd=ROOT, capture_output=True, text=True).stdout)


def litmus():
    q = json.loads((ROOT / "docs" / "litmus" / "questionnaire.json").read_text())
    questions = {qq["id"]: (s["id"], qq) for s in q["sections"] for qq in s["questions"]}
    answers = {}
    for p in sorted((ROOT / "docs" / "litmus" / "answers").glob("*.jsonl")):
        for l in p.read_text().splitlines():
            if l.strip():
                r = json.loads(l); answers[r["question_id"]] = r
    return questions, answers


def target_for(row: dict, questions, answers) -> dict:
    if row["target_flags"]:
        qid = row["target_flags"][0]
        sec, qq = questions[qid]
        a = answers.get(qid, {})
        return {"kind": "litmus", "question_id": qid, "score_now": a.get("score"), "label_now": a.get("label"),
                "target": qq["aligned_looks_like"], "misaligned": qq["misaligned_looks_like"], "evidence_expected": qq["evidence_expected"],
                "stop": "re-answered at score 2 (aligned) or better with evidence the checker verifies"}
    key = row["skill"].replace("cap-", "")
    mine = [(a["score"], qid) for qid, a in answers.items() if questions[qid][0] in (key, f"concern-{key}")]
    if mine:
        s, qid = sorted(mine)[0]
        qq = questions[qid][1]
        return {"kind": "litmus", "question_id": qid, "score_now": s, "label_now": answers[qid]["label"], "target": qq["aligned_looks_like"],
                "misaligned": qq["misaligned_looks_like"], "evidence_expected": qq["evidence_expected"], "stop": "re-answered at score 2 or better"}
    if row["open"]:
        return {"kind": "findings", "open": row["open"], "target": "every open review finding applied or declined in an improve record", "stop": "open findings 0"}
    return {"kind": "usage", "target": "loaded by a task at least once; if no task loads it in a phase, its description or its existence is the finding", "stop": "used >= 1 or folded"}


def cmd_plan(n: int) -> int:
    rows = health()
    questions, answers = litmus()
    items = []
    for r in rows:
        if not r["candidate"]:
            continue
        items.append({"skill": r["skill"], "rank": r["rank"], "used": r["used"], "open_findings": r["open"], "warnings": r["warnings"],
                      "done": r["done"], "target": target_for(r, questions, answers)})
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    plan = {"at": commit, "rule": "top candidates by rank: misaligned or absent litmus answer, then median under aligned, then open findings, then never used", "items": items[:n], "candidates_total": len(items)}
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    print(f"improvement plan at {commit}: {len(items[:n])} items of {len(items)} candidates")
    for it in items[:n]:
        t = it["target"]
        print(f"  {it['skill']}: {t['kind']}" + (f" {t['question_id']} now {t.get('label_now')}" if t["kind"] == "litmus" else "") + f" -> stop when {t['stop']}")
    return 0


def cmd_check() -> int:
    plan = json.loads(PLAN.read_text())
    rows = {r["skill"]: r for r in health()}
    questions, answers = litmus()
    bad = []
    for it in plan["items"]:
        r = rows.get(it["skill"])
        t = it["target"]
        if not r:
            continue   # folded away is a legitimate outcome
        if t["kind"] == "litmus":
            a = answers.get(t["question_id"], {})
            if (a.get("score") or 0) < 2:
                bad.append(f"{it['skill']}: {t['question_id']} still {a.get('label', 'unanswered')}")
        elif t["kind"] == "findings" and r["open"]:
            bad.append(f"{it['skill']}: {r['open']} findings still open")
        elif t["kind"] == "usage" and r["used"] == 0:
            bad.append(f"{it['skill']}: still never used")
        if r["warnings"]:
            bad.append(f"{it['skill']}: {r['warnings']} validator warnings")
    for b in bad:
        print("NOT MOVED", b)
    print(f"{len(plan['items']) - len({b.split(':')[0] for b in bad})} of {len(plan['items'])} items moved to their stop")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["plan"]:
        return cmd_plan(int(argv[1]) if len(argv) > 1 else 5)
    if argv[:1] == ["check"]:
        return cmd_check()
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
