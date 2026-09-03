#!/usr/bin/env python3
"""Combined reading of the two questionnaires (STATUS row 69), joined per PASS.md row, reading only the two answer sets.

Usage: python3 tools/combined_reading.py            write docs/combined/reading.json and reading.md
       python3 tools/combined_reading.py --check    exit 1 if the files on disk differ from what the answers derive

Inputs, and nothing else:
  docs/litmus/scorecard.json                  the litmus assessment (row 67): per section, min and median score, per-angle minimum, gaps
  full-stack-questionair/answers.jsonl        the conformance answers (row 68), rolled up here the way the owner's checker rolls them up
  full-stack-questionair/properties.json      only to map each property to its PASS.md source row
The two crews never saw each other; this join is the first place their results meet. A row where the outward view (litmus) and the
inward view (conformance) disagree is the finding: a property PROVEN against the brief but scored absent or misaligned against the
future state means the brief itself is behind; a property ABSENT against the brief but scored aligned means the build went past the brief undocumented.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "combined"
NAMES = {"isolation": "F-b3-02", "model access": "F-b3-03", "durable execution": "F-b3-04", "agent runtime": "F-b3-05", "tool access": "F-b3-06",
         "capability packaging": "F-b3-07", "work intake": "F-b3-08", "document validation": "F-b3-09", "telemetry": "F-b3-10", "policy": "F-b3-11",
         "provenance": "F-b3-12", "errors": "F-b3-13", "identity": "F-b3-14", "scheduling": "F-b3-15", "idempotency": "F-b3-16", "state persistence": "F-b3-17"}
CONCERNS = {"budget": "F-b4-02", "identity": "F-b4-03", "policy": "F-b4-04", "provenance": "F-b4-05", "telemetry": "F-b4-06", "errors": "F-b4-07", "idempotency": "F-b4-08"}
CORE = {"document": "F-b2-02", "planner": "F-b2-03", "graph": "F-b2-04", "judge": "F-b2-05", "ledger": "F-b2-06"}
SEAMS = {"dispatch": "F-b5-02", "state": "F-b5-04"}


def source_to_fid(src: str) -> str | None:
    s = src.strip()
    m = re.match(r"B1 rule (\d)", s)
    if m:
        return f"F-b1-{int(m.group(1)) + 1:02d}"
    m = re.match(r"B3 (.+)", s)
    if m:
        return NAMES.get(m.group(1).lower())
    m = re.match(r"B4 (.+)", s)
    if m:
        return CONCERNS.get(m.group(1).lower())
    m = re.match(r"B2 (.+)", s)
    if m:
        return CORE.get(m.group(1).lower())
    m = re.match(r"B5 (.+)", s)
    if m:
        return SEAMS.get(m.group(1).lower())
    m = re.match(r"Part C output (\d)", s)
    if m:
        return f"F-part-c-{int(m.group(1)) + 1:02d}"
    return None


def conformance_rollup() -> dict[str, dict]:
    fsq = ROOT / "full-stack-questionair"
    ap = fsq / "answers.jsonl"
    if not ap.is_file():
        return {}
    rows = {r["qid"]: r for r in (json.loads(l) for l in ap.read_text().splitlines() if l.strip())}
    props = json.loads((fsq / "properties.json").read_text())["properties"]
    strong = {"E1", "E2"}

    def met(r):
        return bool(r) and r.get("verdict") in ("CONFORMS", "SUPERSEDES") and (r.get("verdict") != "CONFORMS" or r.get("evidence_tier") in strong)
    out = {}
    for p in props:
        d, m, f = (met(rows.get(f"{p['id']}-{s}")) for s in "DMF")
        dev = any((rows.get(f"{p['id']}-{s}") or {}).get("verdict") == "DEVIATES" for s in "DMF")
        state = "PROVEN" if d and m and f else "SHOWN" if d and m else "ASSERTED" if d else "DEVIATED" if dev else "ABSENT"
        swap = met(rows.get(f"{p['id']}-S")) if "substitution" in p["angles"] else None
        un = [s for s in "DMFS" if (rows.get(f"{p['id']}-{s}") or {}).get("verdict") == "UNANSWERABLE"]
        out[p["id"]] = {"property": p["name"], "source": p["source"], "fid": source_to_fid(p["source"]), "state": state, "swap_proven": swap, "unanswerable": un}
    return out


def derive() -> dict:
    sc = ROOT / "docs" / "litmus" / "scorecard.json"
    litmus = json.loads(sc.read_text()) if sc.is_file() else {"commit": None, "sections": []}
    conf = conformance_rollup()
    by_fid: dict[str, dict] = {}
    for s in litmus["sections"]:
        by_fid.setdefault(s["source"], {})["litmus"] = {"section": s["id"], "min": s["min"], "median": s["median"], "misaligned": s["misaligned"], "absent": s["absent"], "gaps": len(s["gaps"])}
    for pid, p in conf.items():
        if p["fid"]:
            by_fid.setdefault(p["fid"], {}).setdefault("conformance", []).append({"property": pid, "state": p["state"], "swap_proven": p["swap_proven"], "unanswerable": p["unanswerable"]})
    rows = []
    for fid in sorted(by_fid):
        r = by_fid[fid]
        lit, con = r.get("litmus"), r.get("conformance", [])
        states = [c["state"] for c in con]
        tension = None
        if lit and states:
            if "PROVEN" in states and lit["min"] <= 0:
                tension = "proven against the brief, absent or misaligned against the future state: the brief is behind"
            elif all(s == "ABSENT" for s in states) and lit["min"] >= 2:
                tension = "absent against the brief, aligned against the future state: the build went past the brief undocumented"
            elif lit["min"] == -1:
                tension = "misaligned: an error to correct whatever the brief says"
        rows.append({"fid": fid, "litmus": lit, "conformance": con, "tension": tension})
    return {"litmus_commit": litmus.get("commit"), "rows": rows,
            "summary": {"rows": len(rows), "with_both": sum(1 for r in rows if r["litmus"] and r["conformance"]), "tensions": sum(1 for r in rows if r["tension"])}}


def render(d: dict) -> str:
    L = ["# Combined reading", "", "Generated by `tools/combined_reading.py` from `docs/litmus/scorecard.json` and `full-stack-questionair/answers.jsonl`. Do not edit by hand. "
         "The two answer sets were produced by crews that never saw each other; this is the first place they meet, joined by the PASS.md row both cite.", "",
         f"{d['summary']['rows']} PASS.md rows; {d['summary']['with_both']} answered by both instruments; {d['summary']['tensions']} tensions.", "",
         "| PASS row | Litmus section | Litmus min | Litmus median | Misaligned | Conformance properties | Tension |", "|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        lit = r["litmus"] or {}
        con = "; ".join(f"{c['property']} {c['state']}" + (" swap" if c["swap_proven"] else "") for c in r["conformance"]) or "-"
        L.append(f"| `{r['fid']}` | {lit.get('section', '-')} | {lit.get('min', '-')} | {lit.get('median', '-')} | {', '.join(lit.get('misaligned', [])) or '-'} | {con} | {r['tension'] or '-'} |")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    d = derive()
    js, md = json.dumps(d, indent=2) + "\n", render(d)
    jp, mp = OUT / "reading.json", OUT / "reading.md"
    if "--check" in argv:
        stale = [str(p.relative_to(ROOT)) for p, t in ((jp, js), (mp, md)) if not p.is_file() or p.read_text() != t]
        if stale:
            print("FAIL: stale against the answers: " + ", ".join(stale)); return 1
        print("combined reading matches the answers"); return 0
    OUT.mkdir(parents=True, exist_ok=True)
    jp.write_text(js); mp.write_text(md)
    print(f"wrote docs/combined/reading.md: {d['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
