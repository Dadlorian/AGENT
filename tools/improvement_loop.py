#!/usr/bin/env python3
"""The self-improvement loop, rebuilt (STATUS row 72): runs at a ceremony or phase boundary, never per iteration.

UNITS: a skill, or a capability (STATUS row 88)
----------------------------------------------
Until 2026-09-11 the only unit was a skill, so a finding about a tool, a gate or an example area
could not enter a plan at all. That is why three lessons written at ceremony 75 on 2026-09-04 sat
as prose and all three recurred on 2026-09-11: nothing was pulling on them. A loop that cannot
take a finding as an item cannot improve the thing the finding is about.

The second unit is **capability debt**: a row in state/lessons.jsonl whose `sharper_check` names no
tool that exists, i.e. a lesson that is written down and does not run. Its stop condition is
mechanical -- the sharper_check names a tool under tools/ that exists AND is wired into
tools/phase.py's GATES -- so "we learned something" cannot be marked done by asserting it.

Usage:
  python3 tools/improvement_loop.py plan [N]       rank every skill by tools/skill_health.py and write state/improvement-plan.json with the top N (default 5)
  python3 tools/improvement_loop.py check          exit 1 unless every item in the plan moved toward its target (re-answered litmus score, warnings, open findings)
  python3 tools/improvement_loop.py --selftest    plant an unmoved item, prove the check refuses it

An item is one skill with one target drawn from the record that says what the future state looks like:
  the litmus question it scored misaligned or absent on (docs/litmus/questionnaire.json: aligned_looks_like is the target text),
  else the lowest-scoring litmus question of its section, else its open review findings, else "used at least once".
The stopping point per item is stated in the item; "make it better" without a target is not an item (owner rule, 2026-09-03).
The plan is what the next improvement phase works; it is regenerated at the next boundary from the records, never edited by hand.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "state" / "improvement-plan.json"
LESSONS = ROOT / "state" / "lessons.jsonl"
PHASE = ROOT / "tools" / "phase.py"


def tool_stems() -> set:
    return {p.stem for p in (ROOT / "tools").glob("*.py")}


def tools_named(text: str) -> list:
    """Tool names a sharper_check actually names, whether written `tools/x.py`, `x.py` or `x`."""
    stems = tool_stems()
    return sorted({w for w in re.findall(r"[a-z_]{4,}", text or "") if w in stems})


def wired_gates() -> set:
    """Which tools tools/phase.py actually runs. A check nothing runs is the defect, not the fix."""
    return {m for m in re.findall(r"tools/([a-z_]+)\.py", PHASE.read_text())}


def self_tested_gates() -> set:
    """Which of those gates also have a PROVEN FAILURE MODE wired beside them.

    Found by testing this loop rather than by reasoning about it: a tool that prints a message and
    exits 0 satisfied `exists and is wired` and closed a capability item. A gate that cannot fail is
    not a gate -- the repo has known this since ceremony 75 and it reappeared inside the mechanism
    built to stop it reappearing. So the stop condition also requires a self-test gate for the same
    tool: an argv that names the tool AND carries a --selftest (or a *_test.py gate for it), which
    by this repo's convention plants a defect and requires it caught.
    """
    text = PHASE.read_text()
    out = set()
    for argv in re.findall(r"\[([^\]]*?)\]", text):
        if "--selftest" not in argv:
            continue
        out |= {m for m in re.findall(r"tools/([a-z_]+)\.py", argv)}
    # `tools/<x>_test.py` is this repo's other spelling of the same thing (card_profile_test.py).
    for m in re.findall(r"tools/([a-z_]+)_test\.py", text):
        out.add(m)
        out.add(m + "_gate")
    return out


def capability_candidates() -> list:
    """Lessons that are written down and do not run, oldest first -- age is the rank, because an
    old lesson still in prose is one that has had the most chances to recur."""
    out = []
    for line in LESSONS.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        sc = str(r.get("sharper_check") or "")
        if not sc:
            continue
        named = tools_named(sc)
        runs = set(named) & wired_gates()
        proven = set(named) & self_tested_gates()
        if runs and proven:
            continue          # it runs, a gate runs it, and that gate is proven able to fail
        out.append({"ceremony": r.get("ceremony"), "date": r.get("date"), "section": r.get("section"),
                    "sharper_check": sc, "tools_named": named,
                    "recurred_at": r.get("recurred_at") or [],
                    "why": "names no tool that exists" if not named
                           else (f"names {named} but tools/phase.py runs none of them" if not runs
                                 else f"tools/phase.py runs {sorted(runs)} but no self-test gate "
                                      f"proves it can fail -- a gate that cannot fail is not a gate")})
    # Rank: a lesson with NO tool at all outranks one whose tool merely is not wired, because the
    # first has no implementation and the second has half of one. Then oldest first -- an old
    # lesson still in prose has had the most chances to recur, and three of these did.
    # A lesson that has already cost a recurrence outranks everything: it is the one with
    # demonstrated, not argued, value. Then no-tool-at-all before tool-not-wired, then oldest.
    return sorted(out, key=lambda r: (not r["recurred_at"], bool(r["tools_named"]),
                                      str(r.get("date") or "")))


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
    # Capability debt first: a lesson that does not run has already cost a recurrence, and every
    # skill item below is guarded by gates that these lessons are the missing half of.
    for c in capability_candidates():
        items.append({"unit": f"lesson:{c['ceremony']}", "kind": "capability", "rank": -1,
                      "since": c["date"], "section": c["section"], "why": c["why"],
                      "recurred_at": c["recurred_at"],
                      "target": {"kind": "capability",
                                 "sharper_check": c["sharper_check"][:400],
                                 "target": "the sharper_check names a tool under tools/ that exists, "
                                           "that tools/phase.py runs, and that has a self-test gate "
                                           "beside it proving it can fail",
                                 "stop": "named tool is wired into phase.py GATES and has a "
                                         "self-test gate proving it can fail"}})
    for r in rows:
        if not r["candidate"]:
            continue
        items.append({"unit": r["skill"], "kind": "skill", "skill": r["skill"], "rank": r["rank"],
                      "used": r["used"], "open_findings": r["open"], "warnings": r["warnings"],
                      "done": r["done"], "target": target_for(r, questions, answers)})
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    plan = {"at": commit,
            "rule": "capability debt: lessons that have already recurred first, then no tool at all "
                    "before tool-not-wired, then oldest; then "
                    "skills by rank: misaligned or absent litmus "
                    "answer, then median under aligned, then open findings, then never used",
            "units": sorted({i["kind"] for i in items[:n]}),
            "items": items[:n], "candidates_total": len(items)}
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    print(f"improvement plan at {commit}: {len(items[:n])} items of {len(items)} candidates")
    for it in items[:n]:
        t = it["target"]
        extra = (f" {t['question_id']} now {t.get('label_now')}" if t["kind"] == "litmus"
                 else (f" since {it.get('since')}, {it.get('why')}"
                       + (f", RECURRED at {it['recurred_at']}" if it.get("recurred_at") else ""))
                 if t["kind"] == "capability" else "")
        print(f"  {it['unit']}: {t['kind']}{extra}\n      stop when {t['stop']}")
    return 0


def check_items(items: list) -> list:
    """Verdict per plan item. Pure: reads the repo's state, writes nothing."""
    rows = {r["skill"]: r for r in health()}
    questions, answers = litmus()
    bad = []
    for it in items:
        t = it["target"]
        if it.get("kind") == "capability":
            still = {f"lesson:{c['ceremony']}" for c in capability_candidates()}
            if it["unit"] in still:
                bad.append(f"{it['unit']}: {t['stop']} -- still prose")
            continue
        r = rows.get(it.get("skill", it.get("unit")))
        if not r:
            continue
        if t["kind"] == "litmus":
            a = answers.get(t["question_id"], {})
            if (a.get("score") or 0) < 2:
                bad.append(f"{it['unit']}: {t['question_id']} still {a.get('label', 'unanswered')}")
        elif t["kind"] == "findings" and r["open"]:
            bad.append(f"{it['unit']}: {r['open']} findings still open")
        elif t["kind"] == "usage" and r["used"] == 0:
            bad.append(f"{it['unit']}: still never used")
        if r["warnings"]:
            bad.append(f"{it['unit']}: {r['warnings']} validator warnings")
    return bad


def cmd_selftest() -> int:
    """Plant an item that has NOT moved and require refusal. Found necessary by testing:
    a tool printing a message and exiting 0 satisfied the old stop condition and closed a real
    item, so this check was itself a check that could not fail."""
    candidates = capability_candidates()
    if not candidates:
        print("FAIL - no capability debt on disk to plant with")
        return 1
    planted = [{"unit": f"lesson:{candidates[0]['ceremony']}", "kind": "capability",
                "target": {"kind": "capability", "stop": "named tool is wired and self-tested"}}]
    control = [{"unit": "lesson:75-run-boundary", "kind": "capability",
                "target": {"kind": "capability", "stop": "named tool is wired and self-tested"}}]
    bad_planted, bad_control = check_items(planted), check_items(control)
    print("self-test - plant a capability item that has not moved, and a control that has")
    print(f"  planted {planted[0]['unit']}: {len(bad_planted)} refusal(s)")
    print(f"  control lesson:75-run-boundary: {len(bad_control)} refusal(s)")
    ok = len(bad_planted) == 1 and len(bad_control) == 0
    print("PASS - the check refuses an unmoved item and passes a moved one" if ok
          else "FAIL - the check does not distinguish moved from unmoved")
    return 0 if ok else 1


def cmd_check() -> int:
    plan = json.loads(PLAN.read_text())
    bad = check_items(plan["items"])
    for b in bad:
        print("NOT MOVED", b)
    moved = len(plan["items"]) - len({b.split(":")[0] + ":" + b.split(":")[1] if b.startswith("lesson:") else b.split(":")[0] for b in bad})
    print(f"{moved} of {len(plan['items'])} items moved to their stop")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["plan"]:
        return cmd_plan(int(argv[1]) if len(argv) > 1 else 5)
    if argv[:1] == ["check"]:
        return cmd_check()
    if argv[:1] == ["--selftest"] or argv[:1] == ["selftest"]:
        return cmd_selftest()
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
