#!/usr/bin/env python3
"""The litmus questionnaire (STATUS row 66): the idealistic future state per PASS.md B3 row and B4 concern, asked from several angles.

Usage:
  python3 tools/litmus_check.py check [<part.json> ...]   check the parts under docs/litmus/parts/ (or the files named), exit 1 on any error
  python3 tools/litmus_check.py merge                     merge the parts in PASS.md order into docs/litmus/questionnaire.json, then check and render
  python3 tools/litmus_check.py render                    write docs/litmus/questionnaire.md from questionnaire.json

Checks, all of which the crew's isolation depends on:
  coverage     every B3 row (F-b3-02..17) and B4 concern (F-b4-02..08) has exactly one section, with the id this file fixes
  shape        the fields schemas/litmus.schema.json requires, the closed enums, unique question ids
  angles       each section has min_questions..max_questions questions, over at least min_angles angles, including every required angle (docs/litmus/frame.json)
  citations    every cited id resolves in kb/ (F-, T-, X-, including kb/research/*.jsonl not yet merged); a sourced text carries a quote that is a verbatim substring of one cited record; a proposed text says proposed
  contamination no text names anything this repo built (skill, harness, tool, doc and state names); no product name outside standard.why and direction.text
  distinct     no two questions anywhere share the same question text or the same evidence_expected (review 66-litmus-review: B3 and B4 pairs repeated each other)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_skills import PRODUCTS  # noqa: E402

LITMUS = ROOT / "docs" / "litmus"
PARTS = LITMUS / "parts"
FRAME = LITMUS / "frame.json"
OUT_JSON = LITMUS / "questionnaire.json"
OUT_MD = LITMUS / "questionnaire.md"

# PASS.md order, fixed here so every part uses the same ids (source -> id, kind, name)
CANON = [
    ("F-b3-02", "isolation", "capability", "Isolation"), ("F-b3-03", "model-access", "capability", "Model access"),
    ("F-b3-04", "durable-execution", "capability", "Durable execution"), ("F-b3-05", "agent-runtime", "capability", "Agent runtime"),
    ("F-b3-06", "tool-access", "capability", "Tool access"), ("F-b3-07", "capability-packaging", "capability", "Capability packaging"),
    ("F-b3-08", "work-intake", "capability", "Work intake"), ("F-b3-09", "document-validation", "capability", "Document validation"),
    ("F-b3-10", "telemetry", "capability", "Telemetry"), ("F-b3-11", "policy", "capability", "Policy"),
    ("F-b3-12", "provenance", "capability", "Provenance"), ("F-b3-13", "errors", "capability", "Errors"),
    ("F-b3-14", "identity", "capability", "Identity"), ("F-b3-15", "scheduling", "capability", "Scheduling"),
    ("F-b3-16", "idempotency", "capability", "Idempotency"), ("F-b3-17", "state-persistence", "capability", "State persistence"),
    ("F-b4-02", "concern-budget", "concern", "Budget"), ("F-b4-03", "concern-identity", "concern", "Identity"),
    ("F-b4-04", "concern-policy", "concern", "Policy"), ("F-b4-05", "concern-provenance", "concern", "Provenance"),
    ("F-b4-06", "concern-telemetry", "concern", "Telemetry"), ("F-b4-07", "concern-errors", "concern", "Errors"),
    ("F-b4-08", "concern-idempotency", "concern", "Idempotency"),
]
BY_SOURCE = {s: (i, k, n) for s, i, k, n in CANON}
ANGLES = {"presence", "depth", "boundary", "guarantees", "usage", "direction"}
SETTLED = {"baseline", "contested", "emerging", "none"}
PRODUCT_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in PRODUCTS) + r")\b")
PRODUCT_OK_FIELDS = {"standard.why", "direction.text"}
TEXT_FIELDS = ("text", "why", "question", "evidence_expected", "aligned_looks_like", "misaligned_looks_like", "claim", "research_query", "quote", "name")


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def kb_records() -> dict[str, str]:
    recs = {}
    for f in ("facts.jsonl", "target-facts.jsonl", "research.jsonl"):
        for r in jl(ROOT / "kb" / f):
            recs[r["id"]] = r.get("text") or r.get("snippet") or ""
    for p in (ROOT / "kb" / "research").glob("*.jsonl"):
        for r in jl(p):
            recs.setdefault(r["id"], (r.get("snippet") or "") + "\n" + (r.get("read") or ""))
            recs[r["id"]] = (r.get("snippet") or "") + "\n" + (r.get("read") or "")
    return recs


def repo_names() -> list[str]:
    """Names of things this repo built. A questionnaire written in isolation cannot know them."""
    names = set()
    for d in (ROOT / ".claude" / "skills").iterdir():
        if d.is_dir():
            names.add(d.name)
    for d in (ROOT / "harness").iterdir():
        if d.is_dir() and d.name != "__pycache__":
            names.add("harness/" + d.name)
    for p in (ROOT / "tools").glob("*.py"):
        names.add(p.name)
    names.update(["STATUS.md", "STATUS-ARCHIVE.md", "OWNER.md", "HUMAN-REVIEW.md", "kb/ceremonies", "skill.json", "SKILL.md",
                  "docs/guides", "docs/acceptance", "examples/end-to-end", "state/briefs", "agentic-stack",
                  "full-stack-questionair", "Conformance Questionnaire", "conformance-answer", "check_answers", "properties.json"])  # the owner's separate instrument; the two never name each other
    return sorted(names, key=len, reverse=True)


def walk_text(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_text(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_text(v, f"{path}[{i}]")
    elif isinstance(obj, str) and path.rsplit(".", 1)[-1] in TEXT_FIELDS:
        yield path, obj


def check_cited(c: dict, where: str, recs: dict, errs: list):
    for k in ("text", "origin", "cites"):
        if k not in c:
            errs.append(f"{where}: missing {k}"); return
    if c["origin"] not in ("sourced", "proposed"):
        errs.append(f"{where}: origin {c['origin']!r} is not sourced or proposed")
    for cid in c["cites"]:
        if cid not in recs:
            errs.append(f"{where}: cites {cid}, which resolves to nothing in kb/")
    if c["origin"] == "sourced":
        q = c.get("quote", "")
        if not q:
            errs.append(f"{where}: sourced without a quote")
        elif not any(q in recs.get(cid, "") for cid in c["cites"]):
            errs.append(f"{where}: quote is not a verbatim substring of any cited record: {q[:60]!r}")
    elif "proposed" not in c["text"].lower():
        errs.append(f"{where}: proposed text does not say proposed")


def check_sections(sections: list[dict], frame: dict, recs: dict, names: list[str], errs: list, require_full_coverage: bool):
    rules = frame["rules"]
    seen_sources, qids = {}, set()
    for s in sections:
        sid = s.get("id", "?")
        for k in ("id", "kind", "source", "name", "standard", "future_state", "direction", "questions", "gaps"):
            if k not in s:
                errs.append(f"{sid}: missing {k}")
        src = s.get("source")
        if src not in BY_SOURCE:
            errs.append(f"{sid}: source {src} is not a B3 row or B4 concern"); continue
        cid, kind, _ = BY_SOURCE[src]
        if sid != cid or s.get("kind") != kind:
            errs.append(f"{sid}: section for {src} must have id {cid} and kind {kind}")
        if src in seen_sources:
            errs.append(f"{sid}: {src} already has section {seen_sources[src]}")
        seen_sources[src] = sid
        st = s.get("standard", {})
        if st.get("settledness") not in SETTLED:
            errs.append(f"{sid}: standard.settledness {st.get('settledness')!r} not in {sorted(SETTLED)}")
        for cid2 in st.get("cites", []):
            if cid2 not in recs:
                errs.append(f"{sid}: standard cites {cid2}, which resolves to nothing")
        if st.get("settledness") != "none" and not st.get("cites"):
            errs.append(f"{sid}: standard.settledness {st.get('settledness')} cites nothing")
        check_cited(s.get("future_state", {}), f"{sid}.future_state", recs, errs)
        check_cited(s.get("direction", {}), f"{sid}.direction", recs, errs)
        qs = s.get("questions", [])
        if not rules["min_questions"] <= len(qs) <= rules["max_questions"]:
            errs.append(f"{sid}: {len(qs)} questions, rule is {rules['min_questions']}..{rules['max_questions']}")
        angles = {q.get("angle") for q in qs}
        if len(angles & ANGLES) < rules["min_angles"]:
            errs.append(f"{sid}: {len(angles & ANGLES)} angles, rule is at least {rules['min_angles']}")
        for a in rules["required_angles"]:
            if a not in angles:
                errs.append(f"{sid}: no question from the {a} angle")
        for q in qs:
            qid = q.get("id", "?")
            if qid in qids:
                errs.append(f"{sid}: duplicate question id {qid}")
            qids.add(qid)
            if not qid.startswith(sid + "-q"):
                errs.append(f"{sid}: question id {qid} must start with {sid}-q")
            if q.get("angle") not in ANGLES:
                errs.append(f"{qid}: angle {q.get('angle')!r} not in {sorted(ANGLES)}")
            for k in ("question", "evidence_expected", "aligned_looks_like", "misaligned_looks_like"):
                if not q.get(k):
                    errs.append(f"{qid}: missing {k}")
            check_cited({"text": q.get("question", ""), "origin": q.get("origin"), "cites": q.get("cites", []), "quote": q.get("quote", "")}, qid, recs, errs)
        for g in s.get("gaps", []):
            if not g.get("claim") or not g.get("research_query"):
                errs.append(f"{sid}: a gap without claim or research_query")
        # contamination
        for path, text in walk_text(s):
            for n in names:
                if n in text:
                    errs.append(f"{sid}: {path} names something this repo built: {n!r}")
                    break
            field = ".".join(p for p in re.sub(r"\[\d+\]", "", path).split(".")[-2:])
            if field not in PRODUCT_OK_FIELDS and not path.startswith("gaps"):
                m = PRODUCT_RE.search(text)
                if m:
                    errs.append(f"{sid}: {path} names a product ({m.group(1)}); products belong only in standard.why and direction.text")
    seen_text: dict[str, str] = {}
    for s in sections:
        for q in s.get("questions", []):
            for k in ("question", "evidence_expected"):
                key = k + ":" + re.sub(r"\s+", " ", (q.get(k) or "").strip().lower())
                if key in seen_text:
                    errs.append(f"{q.get('id')}: {k} repeats {seen_text[key]} word for word")
                seen_text.setdefault(key, q.get("id", "?"))
    if require_full_coverage:
        for src, (cid, _, _) in BY_SOURCE.items():
            if src not in seen_sources:
                errs.append(f"coverage: no section for {src} ({cid})")


def load_parts(paths: list[Path]) -> list[dict]:
    secs = []
    for p in paths:
        d = json.loads(p.read_text())
        for s in d.get("sections", []):
            s.setdefault("part", p.stem)
            secs.append(s)
    return secs


def cmd_check(argv: list[str]) -> int:
    frame = json.loads(FRAME.read_text())
    if argv:
        paths = [Path(a) for a in argv]
        sections = load_parts(paths)
        full = False
    elif OUT_JSON.is_file() and not any(PARTS.glob("*.json")):
        sections = json.loads(OUT_JSON.read_text())["sections"]
        full = True
    else:
        sections = load_parts(sorted(PARTS.glob("*.json")))
        full = True
    errs: list[str] = []
    check_sections(sections, frame, kb_records(), repo_names(), errs, full)
    for e in errs:
        print("ERROR", e)
    nq = sum(len(s.get("questions", [])) for s in sections)
    print(f"{len(sections)} sections, {nq} questions, {len(errs)} errors")
    return 1 if errs else 0


def cmd_merge() -> int:
    if cmd_check([]) != 0:
        print("FAIL: not merged"); return 1
    sections = load_parts(sorted(PARTS.glob("*.json")))
    order = {s: i for i, (s, *_r) in enumerate(CANON)}
    sections.sort(key=lambda s: order[s["source"]])
    out = {"version": "1", "frame": json.loads(FRAME.read_text()), "sections": sections}
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} with {len(sections)} sections")
    return cmd_render()


def cell(t: str) -> str:
    return t.replace("|", "\\|").replace("\n", " ")


def cmd_render() -> int:
    q = json.loads(OUT_JSON.read_text())
    f = q["frame"]
    L = ["# Litmus questionnaire", "", "Generated by `tools/litmus_check.py` from `docs/litmus/questionnaire.json`. Do not edit by hand. "
         "Every section reflects on one PASS.md B3 row or B4 concern (`python3 tools/kb.py show <id>`); it was written by a crew that read PASS.md Part B and the web and nothing this repo built.", "",
         f"Window: {f['window']['from']} to {f['window']['to']} ({f['window']['means']}).", "", "## Scale", "", "| Score | Label | Means |", "|---|---|---|"]
    L += [f"| {s['score']} | {s['label']} | {cell(s['means'])} |" for s in f["scale"]]
    L += ["", "## Angles", "", "| Angle | Asks |", "|---|---|"] + [f"| {a['id']} | {cell(a['asks'])} |" for a in f["angles"]]
    L += ["", "## Sections", "", "| Section | Kind | Source | Standard | Settledness | Questions |", "|---|---|---|---|---|---|"]
    L += [f"| [{s['name']}](#{s['id']}) | {s['kind']} | `{s['source']}` | {cell(s['standard']['name'])} | {s['standard']['settledness']} | {len(s['questions'])} |" for s in q["sections"]]
    for s in q["sections"]:
        L += ["", f"## {s['name']} ({s['kind']}) <a id=\"{s['id']}\"></a>", "", f"Source: `{s['source']}`. Standard: {cell(s['standard']['name'])}, {s['standard']['settledness']}: {cell(s['standard']['why'])} " + " ".join(f"`{c}`" for c in s["standard"]["cites"]), "",
              "| | Statement | Origin | Sources |", "|---|---|---|---|",
              f"| Future state | {cell(s['future_state']['text'])} | {s['future_state']['origin']} | " + " ".join(f"`{c}`" for c in s["future_state"]["cites"]) + " |",
              f"| Direction | {cell(s['direction']['text'])} | {s['direction']['origin']} | " + " ".join(f"`{c}`" for c in s["direction"]["cites"]) + " |", "",
              "| Id | Angle | Question | Evidence expected | Aligned looks like | Misaligned looks like | Sources |", "|---|---|---|---|---|---|---|"]
        for qq in s["questions"]:
            L.append(f"| {qq['id']} | {qq['angle']} | {cell(qq['question'])} | {cell(qq['evidence_expected'])} | {cell(qq['aligned_looks_like'])} | {cell(qq['misaligned_looks_like'])} | " + " ".join(f"`{c}`" for c in qq["cites"]) + " |")
        if s["gaps"]:
            L += ["", "| Gap | Research query |", "|---|---|"] + [f"| {cell(g['claim'])} | {cell(g['research_query'])} |" for g in s["gaps"]]
    OUT_MD.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__); return 2
    if argv[0] == "check":
        return cmd_check(argv[1:])
    if argv[0] == "merge":
        return cmd_merge()
    if argv[0] == "render":
        return cmd_render()
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
