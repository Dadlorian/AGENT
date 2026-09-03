#!/usr/bin/env python3
"""Expand docs/skill-manifest.json into three facets per item and emit the loop's sections.

Usage:
  python3 tools/manifest_facets.py expand      rewrite docs/skill-manifest.json with <item>, <item>-implement, <item>-use
  python3 tools/manifest_facets.py sections    write state/loop-args.json (sections grouped by wave, with kb ids and facets)
  python3 tools/manifest_facets.py check       link symmetry and wave order

Facet rules (proposed convention):
  <item>            the ideal definition; keeps the original entry's links
  <item>-implement  builds_on: <item>, build-adapter-pair, build-definition-of-done (+ build-evidence-record)
  <item>-use        builds_on: <item>, <item>-implement
  build- skills and agentic-stack are not expanded (they are disciplines, not areas).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "skill-manifest.json"
ARGS = ROOT / "state" / "loop-args.json"
IMPL_DEPS = ["build-adapter-pair", "build-definition-of-done", "build-evidence-record"]


def load():
    return json.loads(MANIFEST.read_text())


def check(m) -> bool:
    names = {s["name"] for s in m["skills"]} | {"agentic-stack"}
    wave = {s["name"]: s["wave"] for s in m["skills"]}
    wave["agentic-stack"] = 0
    by = {s["name"]: s for s in m["skills"]}
    ok = True
    for s in m["skills"]:
        for b in s["builds_on"]:
            if b not in names:
                print("missing", b, "from", s["name"]); ok = False
            elif wave[b] >= s["wave"]:
                print("wave violation", s["name"], "builds_on", b); ok = False
            elif b != "agentic-stack" and s["name"] not in by[b]["used_by"]:
                print("asymmetric", s["name"], "->", b); ok = False
        for u in s["used_by"]:
            if u not in names:
                print("missing", u, "in used_by of", s["name"]); ok = False
            elif s["name"] not in by[u]["builds_on"]:
                print("asymmetric used_by", s["name"], "->", u); ok = False
    print("manifest check:", "OK" if ok else "FAIL", len(m["skills"]), "skills")
    return ok


def expand() -> int:
    m = load()
    if any(s["name"].endswith("-implement") for s in m["skills"]):
        print("already expanded"); return 0
    by = {s["name"]: s for s in m["skills"]}
    new = []
    for s in list(m["skills"]):
        if s["layer"] == "build":
            continue
        base = s["name"]
        impl = {"name": f"{base}-implement", "layer": s["layer"], "wave": s["wave"] + 1, "facet": "implement",
                "purpose": f"How to implement {base} on our stack: today's adapter, the second adapter, migration, cross-cutting wiring, definition of done with breakage.",
                "builds_on": [base] + [d for d in IMPL_DEPS if d in by], "used_by": [f"{base}-use"],
                "definition_of_done": s.get("definition_of_done", ""), "notes_for_author": s.get("notes_for_author", "")}
        use = {"name": f"{base}-use", "layer": s["layer"], "wave": s["wave"] + 2, "facet": "use",
               "purpose": f"How a human, an agent, or an event uses {base}: minimal inputs and outputs, worked examples, failure shape, what it composes with.",
               "builds_on": [base, f"{base}-implement"], "used_by": [],
               "definition_of_done": "", "notes_for_author": "TARGET.md T1-T3 govern this facet: three entry points, hidden complexity, simple to use."}
        for k in ("capability", "standard", "adapter_today", "second_adapter"):
            if k in s:
                impl[k] = s[k]
        s["facet"] = "ideal"
        s["used_by"] = sorted(set(s["used_by"]) | {impl["name"], use["name"]})
        new += [impl, use]
        for d in IMPL_DEPS:
            if d in by:
                by[d]["used_by"] = sorted(set(by[d]["used_by"]) | {impl["name"]})
    for s in m["skills"]:
        if s["layer"] == "build":
            s["facet"] = "discipline"
    m["skills"] += new
    # waves: implement/use of an item may now exceed a downstream ideal that builds on the ideal only; that is fine.
    m["facets"] = {"ideal": "the ideal definition of the area", "implement": "how to implement it on our stack", "use": "how a composer uses it", "discipline": "authoring disciplines (build- layer)"}
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    print(f"expanded to {len(m['skills'])} skills")
    return 0 if check(m) else 1


def sections() -> int:
    m = load()
    ents = {}
    for line in (ROOT / "kb" / "entities.jsonl").read_text().splitlines():
        r = json.loads(line); ents[r["id"]] = r
    def kb_ids(s):
        ids = []
        cap = s.get("capability")
        if cap:
            eid = "E-capability-" + re.sub(r"[^a-z0-9]+", "-", cap.lower()).strip("-")
            if eid in ents:
                ids.append(eid); ids += ents[eid]["sources"]
        for e in ents.values():
            if e["entity_type"] in ("core-component", "seam", "concern") and e["name"].lower() in s["name"]:
                ids.append(e["id"]); ids += e["sources"]
        return sorted(set(ids)) or ["F-b1-02"]
    items = {}
    for s in m["skills"]:
        if s["layer"] == "build" and s["facet"] == "discipline":
            base = s["name"]
        else:
            base = re.sub(r"-(implement|use)$", "", s["name"])
        it = items.setdefault(base, {"name": base, "layer": s["layer"], "wave": None, "kb_ids": None, "facets": []})
        it["facets"].append({"skill": s["name"], "facet": s["facet"]})
        if s["facet"] in ("ideal", "discipline"):
            it["wave"] = s["wave"]; it["kb_ids"] = kb_ids(s)
    order = {"ideal": 0, "discipline": 0, "implement": 1, "use": 2}
    secs = {}
    for it in items.values():
        it["facets"].sort(key=lambda f: order[f["facet"]])
        secs.setdefault(it["wave"], []).append(it)
    out = {"sections": [{"name": f"wave-{w}", "items": sorted(secs[w], key=lambda i: i["name"])} for w in sorted(secs)],
           "brief": "/home/user/AGENT/state/author-brief.md", "date": "2026-09-03", "startAt": 0}
    ARGS.parent.mkdir(exist_ok=True)
    ARGS.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {ARGS}: {len(out['sections'])} sections, {sum(len(s['items']) for s in out['sections'])} items, {sum(len(i['facets']) for s in out['sections'] for i in s['items'])} skills")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"expand": expand, "sections": sections, "check": lambda: 0 if check(load()) else 1}.get(cmd, lambda: (print(__doc__), 2)[1])())
