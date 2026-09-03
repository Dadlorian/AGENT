#!/usr/bin/env python3
"""Generate docs/skill-graph.md from every skill.json as focal groups (STATUS row 49).

Usage: python3 tools/skill_graph.py [--max-edges N] [--max-chars N]
Reads the data (name, layer, description, composes_with) rather than the rendered SKILL.md,
so the graph cannot drift from the source the validator checks.

One diagram of every builds_on edge (514 at 102 skills) exceeds the mermaid defaults recorded in
kb/research.jsonl: X-skill-graph-001 (maxEdges 500) and X-skill-graph-002 (maxTextSize 50000).
GitHub's own limits are an open gap (X-skill-graph-003), so the defaults are the budget.
The page is therefore split into focal groups, each a diagram that is counted against both budgets:
  overview          one node per layer, one edge per layer pair carrying its edge count
  layer groups      core+seam, capabilities, cross-cutting, composition: ideal facets only, an
                    -implement facet folded into its ideal, build- and root sources left out
  build disciplines build-to-build and root-to-build edges, plus how many skills each is applied to
  door load paths   the per-door skill chain from the reconcile-01 review (docs/architecture/load-path.md)
Every edge still appears somewhere: the per-layer tables list builds_on and used_by in full.
Exit 1 if any diagram exceeds a budget, so a graph that would not render cannot be committed.
A builds_on target with no skill.json on disk is reported as a warning and counted, never dropped in silence.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skills import SKILLS, ROOT, ROOT_SKILL, LAYERS  # noqa: E402

LAYER_TITLES = {
    "root": "Root", "core": "Core", "cap": "Capabilities", "xc": "Cross-cutting",
    "seam": "Seams", "compose": "Composition", "build": "Build disciplines",
}
LOAD_PATH_RECORD = ROOT / "kb" / "ceremonies" / "reconcile-01-review-xc.json"
OUT = ROOT / "docs" / "skill-graph.md"
MAX_EDGES = 500     # X-skill-graph-001
MAX_CHARS = 50000   # X-skill-graph-002


def load_skills() -> dict:
    skills = {}
    for d in sorted(SKILLS.iterdir()):
        sj = d / "skill.json"
        if not sj.is_file():
            continue
        sk = json.loads(sj.read_text())
        cw = sk.get("composes_with") or {}
        skills[sk.get("name", d.name)] = {
            "layer": "root" if sk.get("name", d.name) == ROOT_SKILL else sk.get("layer", ""),
            "desc": sk.get("description", ""),
            "builds_on": sorted(cw.get("builds_on") or []),
            "used_by": sorted(cw.get("used_by") or []),
        }
    return skills


def ideal(name: str) -> str:
    """Fold an -implement facet into the ideal it implements."""
    return name[: -len("-implement")] if name.endswith("-implement") else name


class Budget:
    def __init__(self, max_edges: int, max_chars: int):
        self.max_edges, self.max_chars, self.over = max_edges, max_chars, []

    def block(self, title: str, lines: list[str], edges: int) -> list[str]:
        text = "\n".join(["graph LR"] + lines)
        ok = edges <= self.max_edges and len(text) <= self.max_chars
        if not ok:
            self.over.append(f"{title}: {edges} edges (limit {self.max_edges}), {len(text)} chars (limit {self.max_chars})")
        note = f"{edges} edges, {len(text)} characters, within the mermaid defaults." if ok else \
            f"OVER BUDGET: {edges} edges, {len(text)} characters."
        return [note, "", "```mermaid", text, "```", ""]


def edge_lines(edges: list[tuple[str, str]], layer_of: dict) -> list[str]:
    """Edges grouped in subgraphs by layer so a reader sees which layer each node belongs to."""
    nodes = sorted({n for e in edges for n in e})
    by_layer = defaultdict(list)
    for n in nodes:
        by_layer[layer_of[n]].append(n)
    lines = []
    for layer in LAYERS:
        if by_layer.get(layer):
            lines.append(f"    subgraph {layer}_[\"{LAYER_TITLES.get(layer, layer)}\"]")
            lines += [f"        {n}" for n in by_layer[layer]]
            lines.append("    end")
    lines += [f"    {a} --> {b}" for a, b in edges]
    return lines


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-edges", type=int, default=MAX_EDGES)
    ap.add_argument("--max-chars", type=int, default=MAX_CHARS)
    args = ap.parse_args(argv)
    budget = Budget(args.max_edges, args.max_chars)

    skills = load_skills()
    layer_of = {n: s["layer"] for n, s in skills.items()}
    dangling = 0
    all_edges: list[tuple[str, str]] = []
    for name, s in skills.items():
        for b in s["builds_on"]:
            if b in skills:
                all_edges.append((b, name))
            else:
                print(f"warning: {name} builds_on {b}, which was not loaded; edge omitted from the graph")
                dangling += 1

    out = ["# Skill graph", "",
           "Generated by `tools/skill_graph.py` from every skill.json. Do not edit by hand.", "",
           f"{len(skills)} skills, {len(all_edges)} builds_on edges. One diagram of every edge exceeds the mermaid "
           f"edge budget ({MAX_EDGES}, X-skill-graph-001; text budget {MAX_CHARS} characters, X-skill-graph-002), "
           "so the graph is split into focal groups. Each group states its edge count against that budget. "
           "Every edge appears in the per-layer tables at the end.", ""]

    # 1. Overview: layers as nodes, edge counts between layers.
    pair = Counter((layer_of[a], layer_of[b]) for a, b in all_edges)
    lines = []
    for l in LAYERS:
        n_sk = sum(1 for n in skills if layer_of[n] == l)
        if n_sk:
            lines.append(f"    {l}_[\"{LAYER_TITLES[l]}: {n_sk} skills, {pair.get((l, l), 0)} edges within\"]")
    cross = {k: c for k, c in pair.items() if k[0] != k[1]}
    for (a, b), c in sorted(cross.items()):
        lines.append(f"    {a}_ -->|{c}| {b}_")
    out += ["## Overview by layer", "",
            "Node labels carry the skill count per layer and the edges that stay inside it; edge labels carry how many builds_on edges run from one layer to the other. "
            "Build disciplines and the root reach almost every skill, which is why they are kept out of the focal groups below.", ""]
    out += budget.block("Overview", lines, len(cross))

    # 2. Focal groups: ideal facets only, build/root sources excluded.
    def focal(title: str, target_layers: set[str], why: str):
        seen, edges = set(), []
        for a, b in all_edges:
            if layer_of[b] not in target_layers or layer_of[a] in {"build", "root"}:
                continue
            e = (ideal(a), ideal(b))
            if e[0] != e[1] and e not in seen:
                seen.add(e)
                edges.append(e)
        out.extend([f"## {title}", "", why, ""])
        out.extend(budget.block(title, edge_lines(edges, layer_of), len(edges)))

    focal("Core and seams", {"core", "seam"},
          "What the five core components and the two seams build on. An `-implement` facet is folded into its ideal; the build disciplines and the root are omitted here and shown in their own group.")
    focal("Capabilities", {"cap"},
          "What each capability interface builds on. Same folding and omissions as above.")
    focal("Cross-cutting concerns", {"xc"},
          "What each cross-cutting concern builds on: the capability it places, and the concerns it chains with.")
    focal("Composition", {"compose"},
          "What each composition assembles. A composition introduces no new interface, so its edges point only downward.")

    # 3. Build disciplines: their own edges, plus reach.
    bedges = sorted({(a, b) for a, b in all_edges if layer_of[b] == "build"})
    out += ["## Build disciplines", "",
            "How the authoring disciplines build on each other and on the root. The table shows how many skills each discipline is applied to; those edges are omitted from every diagram above.", ""]
    out += budget.block("Build disciplines", edge_lines(bedges, layer_of), len(bedges))
    reach = Counter(a for a, b in all_edges if layer_of[a] in {"build", "root"} and layer_of[b] != "build")
    out += ["| Discipline | Applied to |", "|---|---|"]
    out += [f"| `{n}` | {c} skills |" for n, c in sorted(reach.items(), key=lambda x: (-x[1], x[0]))]
    out.append("")

    # 4. Door load paths from the reconcile-01 review record.
    if LOAD_PATH_RECORD.is_file():
        lp = json.loads(LOAD_PATH_RECORD.read_text()).get("load_path", [])
        out += ["## Load path per door", "",
                f"The skills a composer loads for each entry door, from `{LOAD_PATH_RECORD.relative_to(ROOT)}` "
                "(budget 11 per task, TARGET T9.5; the table view is docs/architecture/load-path.md).", ""]
        for row in lp:
            chain = [s for s in row.get("proposed_skills", []) if s in skills]
            lines = [f"    {a} --> {b}" for a, b in zip(chain, chain[1:])]
            out += [f"### {row.get('door', '?')} door: {len(chain)} skills, within budget: {'yes' if row.get('meets_budget') else 'no'}", ""]
            out += budget.block(f"{row.get('door')} door", lines, len(lines))

    # 5. Per-layer tables carry every edge.
    for layer in LAYERS:
        members = [n for n in skills if layer_of[n] == layer]
        if not members:
            continue
        out += [f"## {LAYER_TITLES.get(layer, layer)}", "", "| Skill | Builds on | Used by | Purpose |", "|---|---|---|---|"]
        for n in sorted(members):
            s = skills[n]
            short = s["desc"].split(". ")[0].rstrip(".")
            bo_w = ", ".join(f"`{x}`" for x in s["builds_on"]) or "-"
            ub_w = ", ".join(f"`{x}`" for x in s["used_by"] if x in skills) or "-"
            out.append(f"| `{n}` | {bo_w} | {ub_w} | {short} |")
        out.append("")

    if budget.over:
        for line in budget.over:
            print(f"FAIL: {line}")
        print("docs/skill-graph.md not written: a diagram over budget would not render")
        return 1
    OUT.write_text("\n".join(out) + "\n")
    print(f"wrote docs/skill-graph.md with {len(skills)} skills, {len(all_edges)} edges in focal groups, {dangling} dangling builds_on edges")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
