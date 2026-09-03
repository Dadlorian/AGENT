#!/usr/bin/env python3
"""Scaffold a new project skill under .claude/skills/<name>/.

Usage:
    python3 scaffold_skill.py <name> --description "..." [--argument-hint "..."]
        [--with-scripts] [--with-references] [--skills-dir PATH]

Creates:
    <skills-dir>/<name>/SKILL.md          frontmatter + instruction skeleton
    <skills-dir>/<name>/evals/evals.json  empty test-prompt list
    <skills-dir>/<name>/scripts/          (optional)
    <skills-dir>/<name>/references/       (optional)

Refuses to overwrite an existing skill directory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def default_skills_dir() -> Path:
    """Walk up from cwd to find a .claude/skills dir, else use cwd/.claude/skills."""
    here = Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        d = candidate / ".claude" / "skills"
        if d.is_dir():
            return d
    return here / ".claude" / "skills"


SKILL_TEMPLATE = """---
name: {name}
description: {description}
{extra_frontmatter}---

# {title}

<!-- One or two sentences: what this skill does and the outcome the user gets. -->

## When this runs

<!-- Restate the trigger in plain words. Mention $ARGUMENTS if the user passes input via /{name} <args>. -->

## Steps

1. <!-- First concrete action. Prefer the imperative: "Read X", "Run Y". -->
2. <!-- ... -->
3. <!-- Finish by telling the user what was produced and where. -->

## Output

<!-- Exact shape of the result: a file path, a message template, a table. Be specific so results are consistent run to run. -->

## Notes

<!-- Edge cases, things to avoid, and *why*. Explain reasoning instead of shouting MUST/NEVER. -->
"""

EVALS_TEMPLATE = {
    "skill_name": "",
    "evals": [
        {
            "id": 1,
            "prompt": "<a realistic thing a user would type that should use this skill>",
            "expected_output": "<what a good result looks like>",
            "files": [],
            "expectations": [],
        }
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="kebab-case skill name, e.g. release-notes")
    ap.add_argument("--description", required=True, help="When to use it and what it does (this drives triggering)")
    ap.add_argument("--argument-hint", default=None, help="Shown in the / menu, e.g. '[file] [style]'")
    ap.add_argument("--user-only", action="store_true", help="Set disable-model-invocation: true (only /name triggers it)")
    ap.add_argument("--with-scripts", action="store_true", help="Create a scripts/ directory")
    ap.add_argument("--with-references", action="store_true", help="Create a references/ directory")
    ap.add_argument("--skills-dir", type=Path, default=None, help="Override the .claude/skills location")
    args = ap.parse_args()

    if not NAME_RE.match(args.name):
        print(f"error: name '{args.name}' must be kebab-case (lowercase letters, digits, single hyphens)", file=sys.stderr)
        return 2
    if len(args.description) > 1024:
        print("error: description is over 1024 characters; tighten it", file=sys.stderr)
        return 2

    skills_dir = (args.skills_dir or default_skills_dir()).resolve()
    skill_dir = skills_dir / args.name
    if skill_dir.exists():
        print(f"error: {skill_dir} already exists; pick another name or edit it in place", file=sys.stderr)
        return 1

    extra = ""
    if args.argument_hint:
        extra += f"argument-hint: {args.argument_hint}\n"
    if args.user_only:
        extra += "disable-model-invocation: true\n"

    title = " ".join(w.capitalize() for w in args.name.split("-"))
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=args.name, description=args.description, extra_frontmatter=extra, title=title)
    )
    evals = dict(EVALS_TEMPLATE)
    evals["skill_name"] = args.name
    (skill_dir / "evals").mkdir()
    (skill_dir / "evals" / "evals.json").write_text(json.dumps(evals, indent=2) + "\n")
    if args.with_scripts:
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / ".gitkeep").touch()
    if args.with_references:
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / ".gitkeep").touch()

    print(f"created {skill_dir}")
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(skills_dir)}")
    print(f"\nnext: fill in {skill_dir / 'SKILL.md'}, then run validate_skill.py {skill_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
