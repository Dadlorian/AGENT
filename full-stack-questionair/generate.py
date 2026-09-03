#!/usr/bin/env python3
"""Generate the questionnaire and a blank answer sheet from properties.json.

The questionnaire is GENERATED. Never hand-edit QUESTIONNAIRE.md -- edit
properties.json and re-run this. Hand-edits are lost on the next run and, worse,
silently diverge from what the checker grades.

Every property is crossed with every angle it declares, so coverage is a
cross-product rather than a list. You cannot forget a question; you can only
fail to declare a property.

Run:  python3 generate.py
"""
from __future__ import annotations
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
SPEC = json.loads((HERE / "properties.json").read_text())

SUFFIX = {"declaration": "D", "demonstration": "M", "falsification": "F", "substitution": "S"}

VERDICTS = ["CONFORMS", "DEVIATES", "SUPERSEDES", "ABSENT", "UNANSWERABLE"]


def questions() -> list[dict]:
    """Every (property x angle) pair, in declaration order. Overrides win."""
    out = []
    for p in SPEC["properties"]:
        for angle in p["angles"]:
            tpl = SPEC["angle_templates"][angle]
            ov = (p.get("overrides") or {}).get(angle) or {}
            out.append({
                "qid": f"{p['id']}-{SUFFIX[angle]}",
                "property_id": p["id"],
                "property": p["name"],
                "group": p["group"],
                "source": p["source"],
                "angle": angle,
                "angle_label": tpl["label"],
                "question": ov.get("question") or tpl["template"].format(name=p["name"]),
                "why": ov.get("why") or "",
                "fails_when": tpl["fails_when"],
                "answered_by": p["answered_by"],
                "sharpened": bool(ov.get("question")),
            })
    return out


def questionnaire(qs: list[dict]) -> str:
    L: list[str] = []
    add = L.append

    add("# Future-State Conformance Questionnaire")
    add("")
    add("**Generated file — do not edit.** It is produced from a property list; edits here are overwritten and, worse, silently diverge from what the checker grades.")
    add("")
    add(f"**{len(qs)} questions over {len(SPEC['properties'])} properties.** Every property is examined from three or four independent angles. That is deliberate and it is the core of the method: **a single question is not a measurement.** Three questions answerable from one paragraph are one question wearing three hats, so each angle below is answered by a *different artifact* — a contract, a worked case, a breaking input, a second adapter.")
    add("")
    add("## The angles, and why each exists")
    add("")
    add("| Angle | Asks | Fails when |")
    add("|---|---|---|")
    for a in ["declaration", "demonstration", "falsification", "substitution"]:
        t = SPEC["angle_templates"][a]
        add(f"| **{t['label']}** | {t['template'].format(name='⟨this property⟩')} | {t['fails_when']} |")
    add("")

    add("## How to answer")
    add("")
    add("**A bare yes, no, or maybe is not an answer.** Every question takes one verdict, and no verdict may be recorded without evidence.")
    add("")
    add("| Verdict | Means | What it must carry |")
    add("|---|---|---|")
    add("| `CONFORMS` | The design does this | The evidence: a quote, a contract, a named section |")
    add("| `DEVIATES` | The design knowingly does not do this | What is given up, and why that was acceptable |")
    add("| `SUPERSEDES` | **The design does something better than what was asked** | What the asked-for version buys, what this version preserves instead, and what it costs. This is the highest bar in the instrument |")
    add("| `ABSENT` | No basis in the deliverable | Nothing — but say so rather than leaving it blank |")
    add("| `UNANSWERABLE` | The question is malformed against this design | Why. **This is logged against the questionnaire, not against the design** |")
    add("")
    add("`SUPERSEDES` exists because an instrument that only accepts conformance punishes the outcome it wanted. A better answer than the one asked for is a good result — it simply carries a heavier burden of proof than agreement does.")
    add("")
    add("`UNANSWERABLE` exists because questionnaires are wrong sometimes. When this instrument's ancestor was run at scale, **two of four rejections turned out to be defects in the checker rather than in the work** — a 50% false-positive rate on the one signal meant to be authoritative. Without an escape hatch, a bad question becomes a false finding about a good design.")
    add("")

    add("### Evidence tiers, and the rule that makes them bite")
    add("")
    add("| Tier | Is |")
    add("|---|---|")
    add("| `E1` | A quoted contract, schema, or interface signature |")
    add("| `E2` | A named section plus a worked example |")
    add("| `E3` | A claim in prose |")
    add("| `E4` | An inference drawn by the reader |")
    add("")
    add("**A `CONFORMS` supported only by `E3` or `E4` is not a `CONFORMS`.** It records as asserted-but-unproven. This is the difference between claimed and measured, made mechanical rather than left to judgement.")
    add("")

    add("### Answer format")
    add("")
    add("One JSON object per line, in a file named `answers.jsonl`. One line per question, all questions present:")
    add("")
    add("```json")
    add(json.dumps({
        "qid": "S2-F",
        "verdict": "CONFORMS",
        "evidence_tier": "E1",
        "evidence": "State contract, section 4.2: 'Two payload shapes cross this boundary: Node and LedgerRow. Nothing else.' Payload registry lists exactly those two.",
        "falsifier": "Enumerate contracts referenced by any inbound seam; a third distinct schema would falsify it.",
        "cost_statement": None,
        "note": ""
    }, indent=None))
    add("```")
    add("")
    add("`cost_statement` is required when and only when the verdict is `SUPERSEDES`. `falsifier` is required on every `CONFORMS`: if you cannot say what would disprove it, you have described an intention.")
    add("")
    add("---")
    add("")

    group = None
    for q in qs:
        if q["group"] != group:
            group = q["group"]
            add(f"## {group}")
            add("")
        if q["angle"] == q_first_angle(qs, q["property_id"]):
            add(f"### {q['property_id']} — {q['property']}")
            add("")
            add(f"*Source: brief {q['source']}. Answered by: {q['answered_by']}.*")
            add("")
        add(f"**{q['qid']} · {q['angle_label']}**")
        add("")
        add(q["question"])
        add("")
        if q["why"]:
            add(f"> **Why this is asked.** {q['why']}")
            add("")
    return "\n".join(L) + "\n"


def q_first_angle(qs: list[dict], pid: str) -> str:
    for q in qs:
        if q["property_id"] == pid:
            return q["angle"]
    return ""


def blank_sheet(qs: list[dict]) -> str:
    rows = []
    for q in qs:
        rows.append(json.dumps({
            "qid": q["qid"], "verdict": "", "evidence_tier": "",
            "evidence": "", "falsifier": "", "cost_statement": None, "note": "",
        }))
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    qs = questions()
    (HERE / "QUESTIONNAIRE.md").write_text(questionnaire(qs))
    (HERE / "answers.blank.jsonl").write_text(blank_sheet(qs))
    (HERE / "questions.json").write_text(json.dumps(qs, indent=1) + "\n")
    sharp = sum(1 for q in qs if q["sharpened"])
    print(f"{len(qs)} questions over {len(SPEC['properties'])} properties")
    print(f"  {sharp} sharpened by a recorded incident, {len(qs) - sharp} from the angle template")
    by: dict[str, int] = {}
    for q in qs:
        by[q["group"]] = by.get(q["group"], 0) + 1
    for k, v in by.items():
        print(f"  {v:>4}  {k}")
    print("wrote QUESTIONNAIRE.md, answers.blank.jsonl, questions.json")
