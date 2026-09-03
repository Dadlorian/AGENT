#!/usr/bin/env python3
"""Walk the acceptance measuring sticks down every stack element (TARGET T10, STATUS row 51).

Usage: python3 tools/acceptance_check.py            write docs/acceptance/matrix.json and matrix.md, print the summary
       python3 tools/acceptance_check.py --check    exit 1 if the files on disk differ from what the sources derive

Nothing here is typed in by hand. Each row is derived from:
  the element, its standard, the tool that holds it today and the swap options   PASS.md B3 rows (F-b3-02..17)
  the standard's version and whether it was fetched                              kb/architecture.jsonl standard entries
  the owning skills                                                              .claude/skills/cap-<element>{,-implement}/skill.json
  the harness and its swap proof                                                 harness/plan.json
  the integration guide                                                          docs/guides/<element>.md, present or absent
The five sticks per element and the stop rule are this repo's design (origin proposed, T-t10-03, T-t10-04):
  sourced   the ideal skill's proposed rows are at most 30 percent of its rows      (T-t9-02)
  measured  the implement skill's definition of done has a measured run           (T-t9-04)
  swap      a harness exists for the element and its plan records a swap proof    (T-t9-06)
  standard  the standard's version record was fetched, not only searched          (T-t9-09)
  guide     an integration guide exists and names a runnable example              (T-t10-07)
An element is accepted when all five hold, or the owner has recorded the missing stick as absent (T-t8-01 style).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"
SKILLS = ROOT / ".claude" / "skills"
OUT_DIR = ROOT / "docs" / "acceptance"
GUIDES = ROOT / "docs" / "guides"
SOURCED_MAX = 0.30


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def origins(o, acc):
    if isinstance(o, dict):
        if "origin" in o:
            acc[o["origin"]] = acc.get(o["origin"], 0) + 1
        for v in o.values():
            origins(v, acc)
    elif isinstance(o, list):
        for v in o:
            origins(v, acc)
    return acc


def skill(name: str) -> dict | None:
    p = SKILLS / name / "skill.json"
    return json.loads(p.read_text()) if p.is_file() else None


def derive() -> dict:
    facts = {f["id"]: f for f in jl(KB / "facts.jsonl")}
    standards = [r for r in jl(KB / "architecture.jsonl") if r.get("kind") == "standard"]
    plan = json.loads((ROOT / "harness" / "plan.json").read_text()) if (ROOT / "harness" / "plan.json").is_file() else {"harnesses": []}
    by_cap = {h.get("capability"): h for h in plan.get("harnesses", [])}
    absent = {}
    dec = OUT_DIR / "absent.json"   # owner-recorded absences, if any
    if dec.is_file():
        absent = json.loads(dec.read_text())

    rows = []
    for fid in sorted(facts):
        if not re.match(r"F-b3-(0[2-9]|1[0-7])$", fid):
            continue
        cells = [c.strip() for c in facts[fid]["text"].strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        element = cells[0].strip("*")
        key = element.lower().replace(" ", "-")
        ideal, impl = skill(f"cap-{key}"), skill(f"cap-{key}-implement")
        std = next((s for s in standards if fid in (s.get("sources") or [])), None)
        harness = next((h for c, h in by_cap.items() if c and element.lower() in c), None)
        o = origins(ideal, {}) if ideal else {}
        share = (o.get("proposed", 0) / max(1, o.get("proposed", 0) + o.get("sourced", 0))) if ideal else None
        dod = ((impl or {}).get("definition_of_done") or {}).get("status")
        guide = GUIDES / f"{key}.md"
        guide_runs = guide.is_file() and "runnable: yes" in guide.read_text() and any(
            (ROOT / c.split()[0]).is_file() or (ROOT / c.split()[1]).is_file()
            for c in re.findall(r"`([^`]+)`", guide.read_text().split("## Runnable")[-1].split("## Definition")[0]) if len(c.split()) > 1)
        std_version = std.get("version", "") if std else "no standard entry"
        sticks = {
            "sourced": {"holds": share is not None and share <= SOURCED_MAX, "value": f"{round(100 * share)} percent proposed" if share is not None else "no ideal skill", "stick": "T-t9-02"},
            "measured": {"holds": dod == "measured", "value": dod or "no implement skill", "stick": "T-t9-04"},
            "swap": {"holds": bool(harness) and "swap" in json.dumps(plan.get("rules", [])).lower(), "value": harness["name"] if harness else "no harness", "stick": "T-t9-06"},
            "standard": {"holds": bool(std) and "unverified" not in std_version and "search" not in std_version and "none" not in std_version, "value": std_version, "stick": "T-t9-09"},
            "guide": {"holds": guide_runs, "value": (str(guide.relative_to(ROOT)) + (" (runnable)" if guide_runs else " (no runnable example)")) if guide.is_file() else "absent", "stick": "T-t10-07"},
        }
        for k, why in (absent.get(key) or {}).items():
            if k in sticks:
                sticks[k]["absent_by_owner"] = why
        holds = sum(1 for s in sticks.values() if s["holds"] or s.get("absent_by_owner"))
        rows.append({
            "element": element, "key": key, "source": fid,
            "standard": cells[1], "standard_id": std["id"] if std else None,
            "today": cells[2], "swap_options": cells[3],
            "skills": [n for n, s in ((f"cap-{key}", ideal), (f"cap-{key}-implement", impl)) if s],
            "harness": harness["dir"] if harness else None,
            "sticks": sticks, "holds": holds, "accepted": holds == len(sticks),
        })
    accepted = sum(1 for r in rows if r["accepted"])
    return {"derived_from": ["PASS.md B3 via kb/facts.jsonl", "kb/architecture.jsonl", "harness/plan.json", ".claude/skills/*/skill.json", "docs/guides/"],
            "sticks": {"sourced": "T-t9-02", "measured": "T-t9-04", "swap": "T-t9-06", "standard": "T-t9-09", "guide": "T-t10-07"},
            "stop_rule": {"origin": "proposed", "text": "an element is accepted when all five sticks hold or the owner recorded the missing stick as absent", "cites": ["T-t10-03", "T-t10-04", "T-t8-01"]},
            "elements": rows, "summary": {"elements": len(rows), "accepted": accepted,
                                          "sticks_holding": sum(r["holds"] for r in rows), "sticks_total": 5 * len(rows)}}


def render(m: dict) -> str:
    L = ["# Acceptance matrix", "", "Generated by `tools/acceptance_check.py`. Do not edit by hand. "
         "Each row is one stack element from PASS.md B3; each stick is a TARGET item; the stop rule is T10.3 and T10.4.", "",
         f"{m['summary']['accepted']} of {m['summary']['elements']} elements accepted; "
         f"{m['summary']['sticks_holding']} of {m['summary']['sticks_total']} sticks hold.", "",
         "| Element | Standard | Version on file | Today | Swap options | Harness | Sourced | Measured | Swap | Standard | Guide | Holds |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in m["elements"]:
        s = r["sticks"]
        def mark(k):
            return "yes" if s[k]["holds"] else ("absent" if s[k].get("absent_by_owner") else "no")
        L.append(f"| {r['element']} | {r['standard']} | {s['standard']['value']} | {r['today']} | {r['swap_options']} | {r['harness'] or '-'} | "
                 f"{mark('sourced')} ({s['sourced']['value']}) | {mark('measured')} ({s['measured']['value']}) | {mark('swap')} ({s['swap']['value']}) | "
                 f"{mark('standard')} | {mark('guide')} | {r['holds']} of 5 |")
    L += ["", "## Sticks", "", "| Stick | Holds when | Target item |", "|---|---|---|",
          "| Sourced | the ideal skill's proposed rows are at most 30 percent | T9.2 |",
          "| Measured | the implement skill's definition of done has a measured run | T9.4 |",
          "| Swap | a harness covers the element and its plan records the swap rule | T9.6 |",
          "| Standard | the version record was fetched, not only searched | T9.9 |",
          "| Guide | docs/guides/<element>.md exists and its runnable section names a command on disk | T10.7 |", ""]
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    m = derive()
    js, md = json.dumps(m, indent=2) + "\n", render(m)
    jp, mp = OUT_DIR / "matrix.json", OUT_DIR / "matrix.md"
    if "--check" in argv:
        stale = [str(p.relative_to(ROOT)) for p, t in ((jp, js), (mp, md)) if not p.is_file() or p.read_text() != t]
        if stale:
            print("FAIL: stale against sources: " + ", ".join(stale))
            return 1
        print("acceptance matrix matches its sources")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        jp.write_text(js); mp.write_text(md)
    s = m["summary"]
    print(f"{s['accepted']} of {s['elements']} elements accepted, {s['sticks_holding']} of {s['sticks_total']} sticks hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
