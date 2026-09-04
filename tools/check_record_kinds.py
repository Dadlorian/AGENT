#!/usr/bin/env python3
"""Check that every mention of the state-seam record-kind list agrees with the canonical one.

Closure for S2-F (conformance): docs/decomposition.md 2.2.1 once listed nine record kinds in
prose while .claude/skills/seam-state/SKILL.md and references/state-seam.md declared ten
(missing `tombstone`). The mechanism: one closed, versioned enumeration of record kinds,
referenced by exactly one canonical location; every other document derives from it rather
than re-declaring it, so a change in cardinality cannot silently diverge between two counts.

Canonical location: the table under "## 1. The closed record-kind list (canonical, version N)"
in .claude/skills/seam-state/references/state-seam.md. This script parses that table, then
parses every other occurrence of the kind list in the docs tree it knows about:

  - references/state-seam.md itself: the `"kind": { "enum": [...] }` field of the full
    StateRecord JSON Schema in section 2 (the same file must not disagree with itself).
  - .claude/skills/seam-state/SKILL.md: the `"kind": { "enum": [...] }` field of the
    StateRecord summary shape.
  - docs/decomposition.md: the prose list in 2.2.1, "Record kinds in the first cut: ...".

and fails (exit 1) if any occurrence's count or member set disagrees with the canonical one.
Exits 0 when every occurrence matches exactly, and there was at least one occurrence to check.

Usage: python3 tools/check_record_kinds.py [--root .]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STATE_SEAM = ".claude/skills/seam-state/references/state-seam.md"
SKILL = ".claude/skills/seam-state/SKILL.md"
DECOMPOSITION = "docs/decomposition.md"

KIND_TOKEN = re.compile(r"`([a-z][a-z-]*)`")
JSON_ENUM = re.compile(r'"kind"\s*:\s*\{\s*"enum"\s*:\s*\[(.*?)\]', re.DOTALL)
QUOTED = re.compile(r'"([a-z][a-z-]*)"')


def read(root: Path, rel: str) -> str:
    path = root / rel
    if not path.exists():
        raise FileNotFoundError(f"missing file: {rel}")
    return path.read_text(encoding="utf-8")


def canonical_from_table(text: str) -> list[str]:
    """Extract the ordered kind list from state-seam.md section '## 1. ...' table."""
    start = text.find("## 1. The closed record-kind list")
    if start == -1:
        raise ValueError(f"{STATE_SEAM}: no '## 1. The closed record-kind list' heading")
    end = text.find("\n## 2.", start)
    section = text[start:end if end != -1 else len(text)]
    kinds = []
    for line in section.splitlines():
        m = re.match(r"\|\s*`([a-z][a-z-]*)`\s*\|", line)
        if m:
            kinds.append(m.group(1))
    if not kinds:
        raise ValueError(f"{STATE_SEAM}: no `kind` rows found under section 1")
    return kinds


def kinds_from_json_enum(text: str, label: str) -> list[str]:
    m = JSON_ENUM.search(text)
    if not m:
        raise ValueError(f"{label}: no \"kind\": {{ \"enum\": [...] }} found")
    return QUOTED.findall(m.group(1))


def kinds_from_decomposition_prose(text: str) -> list[str]:
    m = re.search(r"first cut:\s*(.*?)\.\s*This list is a mirror", text)
    if not m:
        raise ValueError(f"{DECOMPOSITION}: no 'Record kinds in the first cut: ...' prose found")
    return KIND_TOKEN.findall(m.group(1))


def compare(label: str, kinds: list[str], canonical: list[str], canonical_set: set[str]) -> list[str]:
    problems = []
    kind_set = set(kinds)
    if len(kinds) != len(canonical):
        problems.append(
            f"{label}: count {len(kinds)} != canonical count {len(canonical)} "
            f"(kinds={kinds!r})"
        )
    if kind_set != canonical_set:
        missing = canonical_set - kind_set
        extra = kind_set - canonical_set
        detail = []
        if missing:
            detail.append(f"missing {sorted(missing)}")
        if extra:
            detail.append(f"extra {sorted(extra)}")
        problems.append(f"{label}: member set disagrees with canonical ({'; '.join(detail)})")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root (default: current directory)")
    args = ap.parse_args()
    root = Path(args.root)

    try:
        state_seam_text = read(root, STATE_SEAM)
        skill_text = read(root, SKILL)
        decomp_text = read(root, DECOMPOSITION)

        canonical = canonical_from_table(state_seam_text)
        canonical_set = set(canonical)

        occurrences = {
            f"{STATE_SEAM} (section 2 JSON Schema)": kinds_from_json_enum(state_seam_text, STATE_SEAM),
            f"{SKILL} (StateRecord summary shape)": kinds_from_json_enum(skill_text, SKILL),
            f"{DECOMPOSITION} (2.2.1 prose)": kinds_from_decomposition_prose(decomp_text),
        }
    except (FileNotFoundError, ValueError) as exc:
        print(f"check_record_kinds: FAIL - {exc}")
        return 1

    problems: list[str] = []
    for label, kinds in occurrences.items():
        problems.extend(compare(label, kinds, canonical, canonical_set))

    print(f"canonical={STATE_SEAM} count={len(canonical)} kinds={canonical}")
    for label, kinds in occurrences.items():
        print(f"occurrence: {label}: count={len(kinds)}")

    if problems:
        print("check_record_kinds: FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("check_record_kinds: PASS - canonical list and all occurrences agree "
          f"({len(occurrences)} occurrences checked, {len(canonical)} kinds each)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
