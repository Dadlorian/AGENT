#!/usr/bin/env python3
"""Validate one or more skill directories.

Usage:
    python3 validate_skill.py <skill-dir> [<skill-dir> ...]
    python3 validate_skill.py --all            # every skill under .claude/skills

Checks (errors fail the run, warnings do not):
    - SKILL.md exists and has YAML frontmatter delimited by ---
    - name is present, kebab-case, and matches the directory name
    - description is present and <= 1024 characters
    - no unknown frontmatter keys (warning)
    - SKILL.md body is under 500 lines (warning)
    - no leftover <!-- template comments --> (warning)
    - every relative path mentioned in the body that looks like scripts/..., references/..., assets/... exists
    - evals/evals.json, if present, parses and has at least one non-placeholder prompt (warning)
Exit code 0 when no errors.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KNOWN_KEYS = {
    "name", "description", "argument-hint", "disable-model-invocation", "user-invocable",
    "allowed-tools", "model", "context", "agent", "hooks", "paths", "compatibility",
    "license", "metadata", "version",
}
PATH_RE = re.compile(r"(?<![\w/])((?:scripts|references|assets)/[\w./-]+)")


def parse_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    if not text.startswith("---\n"):
        return None, text, "SKILL.md does not start with a '---' frontmatter block"
    end = text.find("\n---", 4)
    if end == -1:
        return None, text, "frontmatter block is not closed with '---'"
    block = text[4:end]
    body = text[end + 4:]
    fm: dict = {}
    current_key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and current_key:
            fm[current_key] = (fm[current_key] + "\n" + line.strip()).strip()
            continue
        if ":" not in line:
            return None, body, f"cannot parse frontmatter line: {line!r}"
        key, _, value = line.partition(":")
        current_key = key.strip()
        value = value.strip()
        if value in (">", "|", ">-", "|-"):
            value = ""
        fm[current_key] = value.strip("\"'")
    return fm, body, None


def validate(skill_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing {skill_md}"], warnings
    text = skill_md.read_text()
    fm, body, err = parse_frontmatter(text)
    if err:
        return [err], warnings
    assert fm is not None

    name = fm.get("name", "")
    if not name:
        errors.append("frontmatter is missing 'name'")
    elif not NAME_RE.match(name):
        errors.append(f"name '{name}' is not kebab-case")
    elif name != skill_dir.name:
        errors.append(f"name '{name}' does not match directory '{skill_dir.name}'")

    desc = fm.get("description", "")
    if not desc:
        errors.append("frontmatter is missing 'description' (this is what triggers the skill)")
    elif len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars; limit is 1024")
    elif len(desc) < 40:
        warnings.append("description is very short; say both what it does and when to use it")

    for key in fm:
        if key not in KNOWN_KEYS:
            warnings.append(f"unknown frontmatter key '{key}' (typo?)")

    body_lines = body.count("\n")
    if body_lines > 500:
        warnings.append(f"body is {body_lines} lines; move detail into references/ to keep it under 500")
    if "<!--" in body:
        warnings.append("body still contains template comments (<!-- ... -->)")
    if body.strip() == "":
        errors.append("SKILL.md body is empty")

    for rel in sorted(set(PATH_RE.findall(body))):
        if not (skill_dir / rel).exists():
            errors.append(f"body references '{rel}' but that file does not exist")

    evals = skill_dir / "evals" / "evals.json"
    if evals.is_file():
        try:
            data = json.loads(evals.read_text())
            prompts = [e.get("prompt", "") for e in data.get("evals", [])]
            if not any(p and not p.startswith("<") for p in prompts):
                warnings.append("evals/evals.json has no real test prompts yet")
            if data.get("skill_name") != name:
                warnings.append("evals/evals.json skill_name does not match the skill name")
        except json.JSONDecodeError as e:
            errors.append(f"evals/evals.json is not valid JSON: {e}")

    return errors, warnings


def main(argv: list[str]) -> int:
    if not argv or argv == ["--help"] or argv == ["-h"]:
        print(__doc__)
        return 0
    if argv == ["--all"]:
        here = Path.cwd().resolve()
        root = next((c / ".claude" / "skills" for c in [here, *here.parents] if (c / ".claude" / "skills").is_dir()), None)
        if root is None:
            print("error: no .claude/skills directory found above the current directory", file=sys.stderr)
            return 2
        targets = sorted(p for p in root.iterdir() if p.is_dir())
    else:
        targets = [Path(a) for a in argv]

    failed = 0
    for skill_dir in targets:
        errors, warnings = validate(skill_dir)
        status = "FAIL" if errors else "ok"
        print(f"[{status}] {skill_dir}")
        for e in errors:
            print(f"    error:   {e}")
        for w in warnings:
            print(f"    warning: {w}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
