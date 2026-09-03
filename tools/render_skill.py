#!/usr/bin/env python3
"""Render SKILL.md from skill.json. Tables only; every row carries its sources.

Usage:
  python3 tools/render_skill.py <skill-dir> [...]     write SKILL.md
  python3 tools/render_skill.py --all                 every skill under .claude/skills
  python3 tools/render_skill.py --check <skill-dir>   exit 1 if SKILL.md differs from the render
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"


def cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def ids(rec: dict) -> str:
    return ", ".join(f"`{i}`" for i in rec.get("sources", [])) or "-"


def ev(rec: dict) -> str:
    """Sources plus the verbatim quote that anchors them."""
    q = rec.get("quote")
    return ids(rec) + (f' "{q}"' if q else "")


def origin(rec: dict) -> str:
    return rec.get("origin", "")


def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return out + [""]


def render(sk: dict) -> str:
    L = ["---", f"name: {sk['name']}", f"description: {sk['description']}", "---", "", f"# {sk['name']}", ""]
    L += ["Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.", ""]
    L += ["## Purpose", ""] + table(["Statement", "Origin", "Evidence"], [[sk["purpose"]["text"], origin(sk["purpose"]), ev(sk["purpose"])]])
    if sk.get("entities"):
        L += ["## Entities", ""] + table(["Entity"], [[f"`{e}`"] for e in sk["entities"]])
    c = sk.get("contract") or {}
    if c:
        L += ["## Contract", ""]
        if c.get("standards"):
            L += ["### Standards", ""] + table(["Standard", "Version", "Version status", "URL", "Sources"],
                                               [[f"`{s['entity']}`", s["version"], s["version_status"], s.get("url") or "-", ids(s)] for s in c["standards"]])
            notes = [s for s in c["standards"] if s.get("version_note")]
            if notes:
                L += [f"- `{s['entity']}` version note: {s['version_note']}" for s in notes] + [""]
        if c.get("operations"):
            L += ["### Operations", ""] + table(["Operation", "Input", "Output", "Origin", "Evidence"],
                                                [[o["name"], o["input"], o["output"], origin(o), ev(o)] for o in c["operations"]])
        if c.get("shapes"):
            L += ["### Shapes (JSON Schema 2020-12)", ""]
            for s in c["shapes"]:
                L += [f"**{s['name']}** ({origin(s)}; sources: {ids(s)})", "", "```json", json.dumps(s["schema"], indent=2), "```", ""]
        if c.get("invariants"):
            L += ["### Invariants", ""] + table(["Invariant", "Origin", "Evidence"], [[i["text"], origin(i), ev(i)] for i in c["invariants"]])
        if c.get("not_exposed"):
            L += ["### Deliberately not exposed", ""] + table(["Item", "Origin", "Evidence"], [[i["text"], origin(i), ev(i)] for i in c["not_exposed"]])
    L += ["## Instructions", ""] + table(["Step", "Action", "Why", "Origin", "Evidence"],
                                         [[str(i["step"]), i["action"], i["why"], origin(i), ev(i)] for i in sk["instructions"]])
    if sk.get("best_practices"):
        L += ["## Best practices", ""] + table(["Practice", "Origin", "Evidence"], [[b["text"], origin(b), ev(b)] for b in sk["best_practices"]])
    if sk.get("adapters"):
        L += ["## Adapters", ""] + table(["Adapter", "Role", "Maps to", "Cannot", "Swap procedure", "Status", "Evidence"],
                                         [[f"`{a['entity']}`", a["role"], a["maps_to"], a["cannot"], a["swap_procedure"], a["status"], ev(a)] for a in sk["adapters"]])
    d = sk["definition_of_done"]
    L += ["## Definition of done", ""] + table(["Field", "Value"], [["Criterion", d["criterion"]], ["Expected", d["expected"]], ["Deliberate breakage", d["breakage"]],
                                                                    ["Expected failure", d["expected_failure"]], ["Status", d["status"]], ["Evidence", ev(d)]])
    cw = sk["composes_with"]
    L += ["## Composes with", "", "Builds on: " + (", ".join(f"`{n}`" for n in cw["builds_on"]) or "-"), "", "Used by: " + (", ".join(f"`{n}`" for n in cw["used_by"]) or "-"), ""]
    if sk.get("open_questions"):
        L += ["## Open questions", ""] + table(["Question", "Deciding evidence", "Default until then", "Evidence"],
                                               [[q["question"], q["evidence"], q["default"], ev(q)] for q in sk["open_questions"]])
    p = sk["provenance"]
    L += ["## Provenance", ""] + table(["Field", "Value"], [["PASS.md sha256", p["kb_source_sha256"]], ["kb facts head", p["kb_heads"]["facts"]],
                                                            ["kb entities head", p["kb_heads"]["entities"]], ["kb edges head", p["kb_heads"]["edges"]], ["Author", p.get("author", "-")]])
    return "\n".join(L).rstrip() + "\n"


USAGE = """usage: python3 tools/render_skill.py [--check] (--all | <skill-dir> [<skill-dir> ...])

  --all      render (or, with --check, compare) every skill under .claude/skills
  --check    do not write; exit 1 if any SKILL.md differs from its render
"""


def main(argv: list[str]) -> int:
    check = "--check" in argv
    rest = [a for a in argv if a != "--check"]
    # Parse the flags before treating anything as a path, so an unknown flag prints usage
    # instead of dying on a FileNotFoundError for "--bogus/skill.json".
    unknown = [a for a in rest if a.startswith("-") and a != "--all"]
    if unknown:
        print(f"error: unrecognized argument {unknown[0]}", file=sys.stderr)
        print(USAGE, file=sys.stderr, end="")
        return 2
    if "--all" in rest:
        if len(rest) > 1:
            print("error: --all takes no other paths", file=sys.stderr)
            print(USAGE, file=sys.stderr, end="")
            return 2
        dirs = sorted(p for p in SKILLS.iterdir() if (p / "skill.json").is_file())
    else:
        if not rest:
            print(USAGE, file=sys.stderr, end="")
            return 2
        dirs = [Path(a) for a in rest]
    for d in dirs:
        if not (d / "skill.json").is_file():
            print(f"error: {d}/skill.json not found", file=sys.stderr)
            return 2
    rc = 0
    for d in dirs:
        sk = json.loads((d / "skill.json").read_text())
        out = render(sk)
        md = d / "SKILL.md"
        if check:
            if not md.is_file() or md.read_text() != out:
                print(f"STALE {d.name}/SKILL.md (run tools/render_skill.py {d})")
                rc = 1
        else:
            md.write_text(out)
            print(f"rendered {d.name}/SKILL.md")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
