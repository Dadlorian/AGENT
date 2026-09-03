#!/usr/bin/env python3
"""Aggregate research gaps into docs/research/gaps.json and, with --apply, add gap skills to the manifest.

Usage:
  python3 tools/gaps.py                 aggregate docs/research/*.json gaps_vs_pass -> docs/research/gaps.json
  python3 tools/gaps.py --apply         also add one manifest entry per accepted gap (layer from proposal, wave = 1 + max wave of builds_on)
Only top-level objects carrying a "lens" key are read as lens files; anything else under docs/research/
(a top-level list, a resolution log) is skipped with a printed line.
Gaps are grouped by proposed_capability (case-insensitive slug); an entry naming neither a
proposed_capability nor a gap slugs to "" and is skipped rather than raising. A gap is accepted when at least one lens proposes it with a
target_requirement and sources; duplicates across lenses merge and keep every source. Names: <layer>-<slug>.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "docs" / "research"
MANIFEST = ROOT / "docs" / "skill-manifest.json"


def slug(s: str | None) -> str:
    """Slugify; a missing value yields "" so the caller's `if not key` guard can skip the entry."""
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40].rstrip("-")


def main() -> int:
    groups: dict[str, dict] = {}
    lenses = 0
    for p in sorted(RES.glob("*.json")):
        if p.name == "gaps.json":
            continue
        d = json.loads(p.read_text())
        if not isinstance(d, dict) or "lens" not in d:
            # Not a lens file (docs/research/gap-resolution.json is a top-level list of
            # resolution records). Say so rather than crashing on d.get / d["lens"].
            print(f"skipping {p.name}: not a lens file (no top-level \"lens\" key)")
            continue
        lenses += 1
        for g in d.get("gaps_vs_pass", []):
            key = slug(g.get("proposed_capability") or g.get("gap"))
            if not key:
                continue
            e = groups.setdefault(key, {"key": key, "proposed_capability": g.get("proposed_capability"), "layers": [], "gaps": [], "target_requirements": [], "pass_sections": [], "standards": [], "sources": [], "lenses": []})
            e["gaps"].append(g.get("gap"))
            for f, k in (("proposed_layer", "layers"), ("target_requirement", "target_requirements"), ("pass_section", "pass_sections"), ("governing_standard", "standards")):
                v = g.get(f)
                if v and v not in e[k]:
                    e[k].append(v)
            e["sources"] += [s for s in g.get("sources", []) if s not in e["sources"]]
            if d["lens"] not in e["lenses"]:
                e["lenses"].append(d["lens"])
    out = sorted(groups.values(), key=lambda e: (-len(e["lenses"]), e["key"]))
    (RES / "gaps.json").write_text(json.dumps({"gaps": out, "count": len(out)}, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(out)} distinct gaps from {lenses} lenses; multi-lens: {sum(1 for e in out if len(e['lenses']) > 1)}")
    for e in out[:60]:
        print(f"  [{'/'.join(e['lenses'])}] {e['key']}  layer={','.join(e['layers']) or '?'}  T={','.join(e['target_requirements'])}")
    if "--apply" not in sys.argv:
        return 0
    m = json.loads(MANIFEST.read_text())
    by = {s["name"]: s for s in m["skills"]}
    added = 0
    for e in out:
        layer = (e["layers"] or ["cap"])[0]
        if layer not in ("core", "cap", "xc", "seam", "compose", "build"):
            layer = "cap"
        name = f"{layer}-{e['key']}"
        if name in by:
            continue
        deps = ["agentic-stack"] + (["build-adapter-pair"] if layer in ("cap", "seam") else [])
        wave = 1 + max(by[d]["wave"] if d in by else 0 for d in deps)
        entry = {"name": name, "layer": layer, "wave": max(wave, 2), "facet": "ideal", "purpose": f"Gap found by research: {e['gaps'][0]}",
                 "builds_on": deps, "used_by": [], "definition_of_done": "", "notes_for_author": f"Research gap; sources {', '.join(e['sources'][:6])}; target {', '.join(e['target_requirements'])}; standard {', '.join(e['standards'])}",
                 "origin": "research-gap", "lenses": e["lenses"]}
        m["skills"].append(entry); by[name] = entry
        for d in deps:
            if d in by and name not in by[d]["used_by"]:
                by[d]["used_by"].append(name)
        added += 1
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    print(f"added {added} gap skills to the manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
