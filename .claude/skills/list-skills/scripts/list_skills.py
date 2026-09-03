#!/usr/bin/env python3
"""Print a table of every skill in this repo's .claude/skills directory.

Usage: python3 list_skills.py [--json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def find_skills_dir() -> Path | None:
    here = Path.cwd().resolve()
    for c in [here, *here.parents]:
        d = c / ".claude" / "skills"
        if d.is_dir():
            return d
    return None


def read_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fm: dict = {}
    key = None
    for line in text[4:end].splitlines():
        if line.startswith((" ", "\t")) and key:
            fm[key] = (fm[key] + " " + line.strip()).strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            fm[key] = value.strip().strip("\"'")
    return fm


def main() -> int:
    root = find_skills_dir()
    if root is None:
        print("no .claude/skills directory found")
        return 1
    rows = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        md = d / "SKILL.md"
        if not md.is_file():
            continue
        fm = read_frontmatter(md)
        rows.append({
            "name": fm.get("name", d.name),
            "invoke": f"/{fm.get('name', d.name)} {fm.get('argument-hint', '')}".strip(),
            "auto": fm.get("disable-model-invocation", "false").lower() != "true",
            "description": fm.get("description", ""),
            "path": str(md.relative_to(root.parent.parent)),
        })
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print(f"{root} has no skills yet")
        return 0
    width = max(len(r["invoke"]) for r in rows)
    for r in rows:
        auto = "auto" if r["auto"] else "manual"
        print(f"{r['invoke']:<{width}}  [{auto}]  {r['description']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
