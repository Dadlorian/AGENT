#!/usr/bin/env python3
"""Fold skills per docs/fold/plan.json (STATUS row 71): 103 directories become the plan's targets.

Usage: python3 tools/fold_skills.py [--dry-run]
For each target: the first source is the base and keeps the body; every other source is stored whole under `folded`
and rendered to references/<source>.md; the definition of done is the implement facet's when one is among the sources;
builds_on and used_by are remapped through the plan, deduplicated and made symmetric; waves are recomputed from
builds_on. Source directories are removed (their references/*.md move to the target, prefixed by the source name).
Also remaps docs/skill-manifest.json, harness/plan.json, harness/*/provenance.json and state/grandfathered.json.
Then run: python3 tools/render_skill.py --all && python3 tools/validate_skills.py
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"


def load(name: str) -> dict:
    return json.loads((SKILLS / name / "skill.json").read_text())


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    plan = json.loads((ROOT / "docs" / "fold" / "plan.json").read_text())
    to_target = {s: t["name"] for t in plan["targets"] for s in t["sources"]}
    manifest = json.loads((ROOT / "docs" / "skill-manifest.json").read_text())
    mf = {m["name"]: m for m in manifest["skills"]}
    targets: dict[str, dict] = {}
    builds: dict[str, set[str]] = {}
    for t in plan["targets"]:
        base = load(t["sources"][0])
        sk = copy.deepcopy(base)
        sk["name"], sk["layer"] = t["name"], t["layer"]
        folded = {}
        for src in t["sources"][1:]:
            folded[src] = load(src)
        impl = next((s for s in t["sources"] if s == t["sources"][0] + "-implement"), None)
        if impl:
            sk["definition_of_done"] = folded[impl]["definition_of_done"]
        if folded:
            sk["folded"] = folded
        b = set()
        for src in t["sources"]:
            for n in load(src)["composes_with"]["builds_on"]:
                b.add(to_target.get(n, n))
        b.discard(t["name"])
        builds[t["name"]] = b
        targets[t["name"]] = sk
    used: dict[str, set[str]] = {n: set() for n in targets}
    for n, bs in builds.items():
        for m in bs:
            if m in used:
                used[m].add(n)
            else:
                print(f"WARN {n} builds on {m}, not a target")
    # waves by layer: the loop that used waves as a build order is over; builds_on cycles make a derived wave meaningless
    LAYER_WAVE = {"root": 0, "build": 1, "core": 2, "cap": 3, "xc": 4, "seam": 5, "compose": 6}
    wave = {n: LAYER_WAVE[sk["layer"]] for n, sk in targets.items()}
    for n, sk in targets.items():
        sk["composes_with"] = {"builds_on": sorted(builds[n]), "used_by": sorted(used[n])}
        sk["wave"] = wave[n]
    if dry:
        for t in plan["targets"]:
            sk = targets[t["name"]]
            print(f"{t['name']:<28} <- {len(t['sources']):>2} sources  dod={'implement' if any(s == t['sources'][0] + '-implement' for s in t['sources']) else 'base':<9} builds_on={len(builds[t['name']]):>2} used_by={len(used[t['name']]):>2} wave={wave[t['name']]}")
        return 0
    # write targets, move references, remove sources
    for t in plan["targets"]:
        name, sk = t["name"], targets[t["name"]]
        tdir = SKILLS / name
        tdir.mkdir(exist_ok=True)
        for src in t["sources"]:
            sdir = SKILLS / src
            refs = sdir / "references"
            if refs.is_dir():
                (tdir / "references").mkdir(exist_ok=True)
                for f in sorted(refs.glob("*.md")):
                    dest = tdir / "references" / (f.name if src == name else f"{src}-{f.name}")
                    if src != name:
                        shutil.move(str(f), str(dest))
        (tdir / "skill.json").write_text(json.dumps(sk, indent=2, ensure_ascii=False) + "\n")
        for src in t["sources"]:
            if src != name:
                shutil.rmtree(SKILLS / src)
    # manifest
    skills_out = []
    for t in plan["targets"]:
        base = t["sources"][0]
        m = dict(mf.get(base) or {"name": base, "layer": t["layer"], "wave": 0, "purpose": targets[t["name"]]["purpose"]["text"]})
        m["name"], m["layer"], m["wave"] = t["name"], t["layer"], wave[t["name"]]
        m["facet"] = "folded" if len(t["sources"]) > 1 else m.get("facet", "ideal")
        m["builds_on"], m["used_by"] = sorted(builds[t["name"]]), sorted(used[t["name"]])
        if len(t["sources"]) > 1:
            m["notes_for_author"] = "Folded (STATUS row 71): " + ", ".join(t["sources"][1:]) + ". " + (m.get("notes_for_author") or "")
        skills_out.append(m)
    manifest["skills"] = skills_out
    manifest["facets"]["folded"] = "several former skills folded into one; each former skill is rendered whole under references/"
    (ROOT / "docs" / "skill-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    # harness plan and provenance
    hp = ROOT / "harness" / "plan.json"
    plan_h = json.loads(hp.read_text())
    for h in plan_h["harnesses"]:
        h["owner_skill"] = to_target.get(h["owner_skill"], h["owner_skill"])
        co = [to_target.get(c, c) for c in h.get("co_skills", [])]
        h["co_skills"] = sorted({c for c in co if c != h["owner_skill"]})
        pv = ROOT / h["dir"] / "provenance.json"
        if pv.is_file():
            d = json.loads(pv.read_text())
            if "owner_skill" in d:
                d["owner_skill"] = to_target.get(d["owner_skill"], d["owner_skill"])
            if "co_skills" in d:
                d["co_skills"] = sorted({to_target.get(c, c) for c in d["co_skills"]} - {d.get("owner_skill")})
            pv.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    hp.write_text(json.dumps(plan_h, indent=2) + "\n")
    gf = ROOT / "state" / "grandfathered.json"
    if gf.is_file():
        gf.write_text(json.dumps(sorted({to_target.get(n, n) for n in json.loads(gf.read_text())}), indent=0) + "\n")
    print(f"folded {len(to_target)} skills into {len(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
