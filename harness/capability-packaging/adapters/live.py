#!/usr/bin/env python3
"""Live adapter for the packaging source running on this host today.

Product names are allowed in this file and nowhere else. Today that source is
this repository's `.claude/skills/` tree: one directory per package, a
`SKILL.md` whose frontmatter carries `name` and `description`, an optional
`references/` directory read on demand (F-b3-07: "skill files"; this repo's
`.claude/skills/` directories are the live instance, blueprint tool entry).

Reached only through SKILLS_ROOT (README.md). Source is "directory": identity
is the package's directory name and digest is always None, matching the dry-run
adapter's execution model — both are the "today" side of the pair.

Standard library only; no YAML dependency. Frontmatter here is two single-line
`key: value` pairs between `---` markers, which is what `tools/render_skill.py`
emits, so a hand-rolled two-line parser is exact rather than approximate.
"""
from __future__ import annotations

import os

from interface import CapabilityPackagingAdapter, Problem


def _parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    body = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            body[key.strip()] = value.strip()
    return body


class LiveSkillFilesAdapter(CapabilityPackagingAdapter):
    entity = "this host's .claude/skills/ tree"
    source = "directory"
    declared_marker = "live-skills-root-scan"
    declared_gaps = ("cannot verify two copies of a package are the same; identity is a path "
                     "and this source produces no digest",)

    def _root(self) -> str:
        root = os.environ.get("SKILLS_ROOT")
        if not root:
            raise Problem("adapter-unavailable",
                          "SKILLS_ROOT is not set; the live packaging source cannot be reached",
                          retry_after_s=30)
        if not os.path.isdir(root):
            raise Problem("adapter-unavailable", f"SKILLS_ROOT {root!r} is not a directory",
                          retry_after_s=30)
        return root

    def _raw(self, identity: str) -> dict | None:
        root = self._root()
        skill_md = os.path.join(root, identity, "SKILL.md")
        if not os.path.isfile(skill_md):
            return None
        with open(skill_md, encoding="utf-8") as fh:
            frontmatter = _parse_frontmatter(fh.read())
        resident = {k: v for k, v in frontmatter.items() if k in ("name", "description") and v}
        return {"resident": resident}

    def _scan_all(self) -> dict:
        root = self._root()
        out = {}
        for identity in sorted(os.listdir(root)):
            raw = self._raw(identity)
            if raw is not None:
                out[identity] = raw
        return out

    def _locate(self, identity: str) -> dict | None:
        return self._raw(identity)

    def _read_body(self, identity: str) -> str:
        with open(os.path.join(self._root(), identity, "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        parts = text.split("---", 2)
        return parts[2].strip() if len(parts) == 3 else text

    def _list_references(self, identity: str) -> list[str]:
        ref_dir = os.path.join(self._root(), identity, "references")
        if not os.path.isdir(ref_dir):
            return []
        return sorted(f"references/{name}" for name in os.listdir(ref_dir)
                     if os.path.isfile(os.path.join(ref_dir, name)))

    def _read_reference(self, identity: str, reference_path: str) -> str:
        with open(os.path.join(self._root(), identity, reference_path), encoding="utf-8") as fh:
            return fh.read()

    def _digest(self, identity: str, raw: dict) -> str | None:
        return None                                    # identity is a path; no digest to offer


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveSkillFilesAdapter
