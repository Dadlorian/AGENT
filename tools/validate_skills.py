#!/usr/bin/env python3
"""Check every skill in .claude/skills against the agentic-stack root contract.

Usage: python3 tools/validate_skills.py [--manifest docs/skill-manifest.json]

Errors (exit 1):
  - missing or malformed SKILL.md frontmatter; name != directory; description > 1024 chars
  - layer prefix not one of core- cap- xc- seam- compose- build- (agentic-stack exempt)
  - missing "## Composes with" section (agentic-stack exempt)
  - a link naming a skill that does not exist
  - asymmetric links: A says it builds on B but B does not say A builds on it, or vice versa
  - a product name outside an adapter section in a core-, compose-, or build- skill,
    or outside an adapter section in a cap-, xc-, or seam- skill
  - a referenced scripts/ references/ assets/ path that does not exist
  - if a manifest is given: a skill directory that is not in the manifest
Warnings:
  - body over 500 lines
  - no "claimed" or "measured" label anywhere in a skill that states facts about the host
  - a manifest skill whose directory has not been written yet
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
LAYERS = ("core-", "cap-", "xc-", "seam-", "compose-", "build-")
ROOT_SKILL = "agentic-stack"

# Products named in PASS.md Part A and B3's adapter/swap columns. Standards (OPA/Rego, MCP, ACP, OTLP...) are not products.
PRODUCTS = [
    "LiteLLM", "Firecracker", "goose", "Langfuse", "ClickHouse", "Postgres", "PostgreSQL", "Redis", "MinIO",
    "Temporal", "Tailscale", "Ansible", "SGLang", "vLLM", "Qwen", "Gemini", "OpenAI", "GPT", "Cursor",
    "Claude Code", "Restate", "DBOS", "Inngest", "gVisor", "Kata", "Cloud Hypervisor", "OpenRouter",
    "Phoenix", "Braintrust", "Cedar", "Sigstore", "SPIFFE", "SPIRE", "RunPod", "polkit", "systemd", "docker",
]
PRODUCT_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in PRODUCTS) + r")\b")
PATH_RE = re.compile(r"(?<![\w/`])((?:scripts|references|assets)/[\w./-]+)")
LINK_RE = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`")


def frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip("\"'")
    return fm, text[end + 4:]


def sections(body: str) -> list[tuple[str, str]]:
    """Split body into (heading, text) pairs; text before the first heading has heading ''."""
    out, cur, buf = [], "", []
    for line in body.splitlines():
        if line.startswith("#"):
            out.append((cur, "\n".join(buf)))
            cur, buf = line.lstrip("#").strip(), []
        else:
            buf.append(line)
    out.append((cur, "\n".join(buf)))
    return out


def composes_with(body: str) -> tuple[set[str], set[str]] | None:
    for heading, text in sections(body):
        if heading.lower().startswith("composes with"):
            builds_on, used_by = set(), set()
            for line in text.splitlines():
                low = line.lower()
                names = set(LINK_RE.findall(line))
                if "builds on" in low or "depends on" in low:
                    builds_on |= names
                elif "used by" in low or "builds on this" in low or "extends this" in low:
                    used_by |= names
            return builds_on, used_by
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=ROOT / "docs" / "skill-manifest.json")
    args = ap.parse_args()

    dirs = {p.name: p for p in SKILLS.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}
    errors: list[str] = []
    warnings: list[str] = []
    links: dict[str, tuple[set[str], set[str]]] = {}
    bodies: dict[str, str] = {}

    for name, d in sorted(dirs.items()):
        text = (d / "SKILL.md").read_text()
        fm, body = frontmatter(text)
        bodies[name] = body
        if fm is None:
            errors.append(f"{name}: no frontmatter")
            continue
        if fm.get("name") != name:
            errors.append(f"{name}: frontmatter name is {fm.get('name')!r}")
        if not fm.get("description"):
            errors.append(f"{name}: missing description")
        elif len(fm["description"]) > 1024:
            errors.append(f"{name}: description is {len(fm['description'])} chars (max 1024)")
        if name != ROOT_SKILL and not name.startswith(LAYERS):
            errors.append(f"{name}: no layer prefix {LAYERS}")
        if body.count("\n") > 500:
            warnings.append(f"{name}: body is {body.count(chr(10))} lines")
        for rel in sorted(set(PATH_RE.findall(body))):
            if not (d / rel).exists():
                errors.append(f"{name}: references missing file {rel}")

        cw = composes_with(body)
        if name != ROOT_SKILL:
            if cw is None:
                errors.append(f"{name}: no '## Composes with' section")
            else:
                links[name] = cw

        # product purity: products only inside a section whose heading mentions adapter/substrate/today
        for heading, text in sections(body):
            allowed = any(w in heading.lower() for w in ("adapter", "substrate", "today", "swap"))
            if allowed:
                continue
            hits = sorted(set(PRODUCT_RE.findall(text)))
            if hits:
                where = heading or "(preamble)"
                errors.append(f"{name}: product name(s) {hits} outside an adapter section, in '{where}'")

        if name != ROOT_SKILL and not re.search(r"\b(claimed|measured)\b", body, re.I):
            warnings.append(f"{name}: no claimed/measured label anywhere")

    all_names = set(dirs) | {ROOT_SKILL}
    manifest_names: set[str] = set()
    if args.manifest.is_file():
        manifest_names = {s["name"] for s in json.loads(args.manifest.read_text())["skills"]}
    all_names |= manifest_names  # forward references to unwritten manifest skills are allowed
    for name, (bo, ub) in links.items():
        for b in bo:
            if b not in all_names:
                errors.append(f"{name}: builds on unknown skill {b}")
            elif b != ROOT_SKILL and b in links and name not in links[b][1]:
                errors.append(f"{name} builds on {b}, but {b} does not list {name} under used by")
        for u in ub:
            if u not in all_names:
                errors.append(f"{name}: used by unknown skill {u}")
            elif u in links and name not in links[u][0]:
                errors.append(f"{name} says used by {u}, but {u} does not list {name} under builds on")

    if manifest_names:
        for missing in sorted(manifest_names - set(dirs)):
            warnings.append(f"manifest lists {missing} but no skill directory exists yet")
        for extra in sorted(set(dirs) - manifest_names - {ROOT_SKILL}):
            errors.append(f"skill directory {extra} is not in the manifest")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error:   {e}")
    print(f"{len(dirs)} skills, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
