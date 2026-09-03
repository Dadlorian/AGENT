#!/usr/bin/env python3
"""Check every skill against the schema, the knowledge base, and the root contract.

Usage: python3 tools/validate_skills.py [--manifest docs/skill-manifest.json]

Errors (exit 1):
  - skill dir without skill.json, or skill.json violating schemas/skill.schema.json (checked by the
    rules below, since no JSON Schema library is available here; the schema file is the contract)
  - name != directory; layer prefix mismatch; description length out of range
  - any cited id (F-, E-, R-) that does not exist in kb/, including the entities list
  - any item with origin=sourced and no sources or no quote; a quote that is not a verbatim substring
    of a cited record; any item with origin=proposed whose text does not say "proposed"
  - provenance kb heads or PASS.md hash that do not match kb/meta.json (skill built on a stale kb)
  - SKILL.md not identical to the render of skill.json
  - composes_with links naming unknown skills, or asymmetric links
  - product names outside Adapters in SKILL.md
  - if a manifest exists: a skill dir that is not in the manifest, or links differing from it
Warnings:
  - manifest skill not written yet
  - fewer than 3 instructions
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_skill import render  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
KB = ROOT / "kb"
ROOT_SKILL = "agentic-stack"
LAYERS = {"root": None, "core": "core-", "cap": "cap-", "xc": "xc-", "seam": "seam-", "compose": "compose-", "build": "build-"}
PRODUCTS = [
    "LiteLLM", "Firecracker", "goose", "Langfuse", "ClickHouse", "Postgres", "PostgreSQL", "Redis", "MinIO",
    "Temporal", "Tailscale", "Ansible", "SGLang", "vLLM", "Qwen", "Gemini", "OpenAI", "GPT", "Cursor",
    "Claude Code", "Restate", "DBOS", "Inngest", "gVisor", "Kata", "Cloud Hypervisor", "OpenRouter",
    "Phoenix", "Braintrust", "Cedar", "Sigstore", "SPIFFE", "SPIRE", "RunPod", "polkit", "systemd", "docker",
]
PRODUCT_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in PRODUCTS) + r")\b")
ID_RE = re.compile(r"^[FERTX]-[a-z0-9-]+$")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


KB_TEXT: dict[str, str] = {}


def load_kb() -> tuple[set[str], dict]:
    ids = set()
    for f in ("facts", "entities", "edges", "target-facts", "research"):
        if not (KB / f"{f}.jsonl").is_file():
            continue
        for line in (KB / f"{f}.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                ids.add(r["id"])
                KB_TEXT[r["id"]] = r.get("text") or json.dumps(r, ensure_ascii=False)
    return ids, json.loads((KB / "meta.json").read_text())


def walk_sourced(obj, path, errs, kb_ids, name):
    """Recursively enforce: sources exist in kb; origin=sourced needs sources; origin=proposed must say so."""
    if isinstance(obj, dict):
        if "sources" in obj:
            if not isinstance(obj["sources"], list):
                errs.append(f"{name}: {path}.sources is not a list")
            else:
                for s in obj["sources"]:
                    if not ID_RE.match(str(s)) or s not in kb_ids:
                        errs.append(f"{name}: {path} cites unknown id {s}")
        if "quote" in obj:
            q = str(obj["quote"])
            srcs = [x for x in obj.get("sources", []) if x in KB_TEXT]
            if len(q) < 8:
                errs.append(f"{name}: {path}.quote is too short to be evidence")
            elif not any(q in KB_TEXT[x] for x in srcs):
                errs.append(f"{name}: {path}.quote is not a verbatim substring of any cited record: {q[:60]!r}")
        if "origin" in obj:
            if obj["origin"] == "sourced" and not obj.get("sources"):
                errs.append(f"{name}: {path} is origin=sourced but has no sources")
            if obj["origin"] == "sourced" and not obj.get("quote"):
                errs.append(f"{name}: {path} is origin=sourced but has no quote (verbatim evidence required)")
            if obj["origin"] == "proposed":
                text = " ".join(str(obj.get(k, "")) for k in ("text", "action", "why", "name", "input", "output"))
                if "proposed" not in text.lower() and "our design" not in text.lower():
                    errs.append(f"{name}: {path} is origin=proposed but the text does not say so")
            if obj["origin"] not in ("sourced", "proposed"):
                errs.append(f"{name}: {path}.origin must be sourced or proposed")
        for k, v in obj.items():
            walk_sourced(v, f"{path}.{k}", errs, kb_ids, name)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_sourced(v, f"{path}[{i}]", errs, kb_ids, name)


def check_structure(sk: dict, name: str, errs: list[str]):
    req = ["name", "layer", "description", "purpose", "instructions", "definition_of_done", "composes_with", "provenance"]
    for k in req:
        if k not in sk:
            errs.append(f"{name}: missing required field {k}")
    allowed = set(req) | {"wave", "entities", "contract", "best_practices", "adapters", "open_questions"}
    for k in sk:
        if k not in allowed:
            errs.append(f"{name}: unknown field {k}")
    if sk.get("name") != name:
        errs.append(f"{name}: skill.json name is {sk.get('name')!r}")
    layer = sk.get("layer")
    if layer not in LAYERS:
        errs.append(f"{name}: layer {layer!r} not one of {list(LAYERS)}")
    elif layer == "root":
        if name != ROOT_SKILL:
            errs.append(f"{name}: only {ROOT_SKILL} may have layer root")
    elif not name.startswith(LAYERS[layer]):
        errs.append(f"{name}: layer {layer} requires prefix {LAYERS[layer]}")
    d = sk.get("description", "")
    if not (40 <= len(d) <= 1024):
        errs.append(f"{name}: description length {len(d)} not in 40..1024")
    for key in ("purpose",):
        if not isinstance(sk.get(key), dict) or "text" not in sk[key] or "origin" not in sk[key]:
            errs.append(f"{name}: {key} must be an object with text and origin")
    ins = sk.get("instructions", [])
    if not isinstance(ins, list) or not ins:
        errs.append(f"{name}: instructions must be a non-empty list")
    else:
        for i, it in enumerate(ins):
            for k in ("step", "action", "why", "origin"):
                if k not in it:
                    errs.append(f"{name}: instructions[{i}] missing {k}")
    dod = sk.get("definition_of_done", {})
    for k in ("criterion", "expected", "breakage", "expected_failure", "status"):
        if k not in dod:
            errs.append(f"{name}: definition_of_done missing {k}")
    if dod.get("status") not in ("claimed", "measured", None):
        errs.append(f"{name}: definition_of_done.status must be claimed or measured")
    for a in sk.get("adapters", []):
        for k in ("entity", "role", "maps_to", "cannot", "swap_procedure", "status", "sources", "quote"):
            if k not in a:
                errs.append(f"{name}: adapter missing {k}")
        if a.get("role") not in ("today", "second"):
            errs.append(f"{name}: adapter role must be today or second")
    for s in (sk.get("contract") or {}).get("standards", []):
        for k in ("entity", "version", "version_status", "sources"):
            if k not in s:
                errs.append(f"{name}: standard missing {k}")
        if s.get("version_status") not in ("verified", "unverified"):
            errs.append(f"{name}: standard version_status must be verified or unverified")
    cw = sk.get("composes_with", {})
    for k in ("builds_on", "used_by"):
        for n in cw.get(k, []):
            if not NAME_RE.match(n):
                errs.append(f"{name}: composes_with.{k} has bad name {n!r}")
    p = sk.get("provenance", {})
    for k in ("kb_source_sha256", "kb_heads"):
        if k not in p:
            errs.append(f"{name}: provenance missing {k}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=ROOT / "docs" / "skill-manifest.json")
    ap.add_argument("--only", action="append", default=[], help="report only errors/warnings naming these skills (links to others are still loaded)")
    args = ap.parse_args()
    kb_ids, meta = load_kb()
    errs: list[str] = []
    warns: list[str] = []
    skills: dict[str, dict] = {}

    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        name = d.name
        sj = d / "skill.json"
        if not sj.is_file():
            errs.append(f"{name}: no skill.json (skills are data; SKILL.md is rendered)")
            continue
        try:
            sk = json.loads(sj.read_text())
        except json.JSONDecodeError as e:
            errs.append(f"{name}: skill.json is not valid JSON: {e}")
            continue
        skills[name] = sk
        check_structure(sk, name, errs)
        walk_sourced(sk, "", errs, kb_ids, name)
        for e in sk.get("entities", []):
            if e not in kb_ids:
                errs.append(f"{name}: entities lists unknown id {e}")
        p = sk.get("provenance", {})
        if p.get("kb_source_sha256") != meta["source"]["sha256"]:
            errs.append(f"{name}: provenance PASS.md hash does not match kb/meta.json (rebuild the skill against the current kb)")
        for k, v in (p.get("kb_heads") or {}).items():
            if meta["heads"].get(k) != v:
                errs.append(f"{name}: provenance kb head '{k}' does not match kb/meta.json")
        md = d / "SKILL.md"
        try:
            rendered = render(sk)
            if not md.is_file() or md.read_text() != rendered:
                errs.append(f"{name}: SKILL.md is not the render of skill.json (run tools/render_skill.py)")
        except (KeyError, TypeError) as e:
            errs.append(f"{name}: cannot render ({e!r})")
            rendered = ""
        # product purity: only inside the Adapters section
        section, allowed = "", False
        for line in rendered.splitlines():
            if line.startswith("## "):
                section = line[3:].strip()
                allowed = section.lower().startswith("adapters")
                continue
            if not allowed:
                hits = sorted(set(PRODUCT_RE.findall(line)))
                if hits:
                    errs.append(f"{name}: product name(s) {hits} outside Adapters, in section '{section or 'frontmatter'}'")
        if len(sk.get("instructions", [])) < 3:
            warns.append(f"{name}: fewer than 3 instructions")

    manifest_names: set[str] = set()
    manifest: dict[str, dict] = {}
    if args.manifest.is_file():
        manifest = {s["name"]: s for s in json.loads(args.manifest.read_text())["skills"]}
        manifest_names = set(manifest)
    known = set(skills) | manifest_names | {ROOT_SKILL}
    for name, sk in skills.items():
        cw = sk.get("composes_with", {})
        for b in cw.get("builds_on", []):
            if b not in known:
                errs.append(f"{name}: builds on unknown skill {b}")
            elif b in skills and b != ROOT_SKILL and name not in skills[b]["composes_with"]["used_by"]:
                errs.append(f"{name} builds on {b}, but {b} does not list {name} under used_by")
        for u in cw.get("used_by", []):
            if u not in known:
                errs.append(f"{name}: used by unknown skill {u}")
            elif u in skills and name not in skills[u]["composes_with"]["builds_on"]:
                errs.append(f"{name} says used by {u}, but {u} does not list {name} under builds_on")
        if name in manifest:
            m = manifest[name]
            if sorted(m.get("builds_on", [])) != sorted(cw.get("builds_on", [])) or sorted(m.get("used_by", [])) != sorted(cw.get("used_by", [])):
                errs.append(f"{name}: composes_with differs from docs/skill-manifest.json")
    if manifest_names:
        for missing in sorted(manifest_names - set(skills)):
            warns.append(f"manifest lists {missing} but it is not written yet")
        for extra in sorted(set(skills) - manifest_names - {ROOT_SKILL}):
            errs.append(f"{extra} is not in docs/skill-manifest.json")

    if args.only:
        errs = [e for e in errs if any(e.startswith(o + ":") or e.startswith(o + " ") for o in args.only)]
        warns = [w for w in warns if any(w.startswith(o + ":") or w.startswith(o + " ") for w in args.only)]
    for w in warns:
        print(f"warning: {w}")
    for e in errs:
        print(f"error:   {e}")
    scope = f"{', '.join(args.only)}: " if args.only else f"{len(skills)} skills checked, "
    print(f"{scope}{len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
