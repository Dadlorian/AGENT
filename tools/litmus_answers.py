#!/usr/bin/env python3
"""Check and roll up the answers to the litmus questionnaire (STATUS row 67).

Usage:
  python3 tools/litmus_answers.py check [<part.jsonl> ...]   check the parts under docs/litmus/answers/ (or the files named); exit 1 on any error
  python3 tools/litmus_answers.py scorecard                  check every part with coverage on, then write docs/litmus/scorecard.json and scorecard.md

One answer row per question, JSON per line:
  {"question_id": "telemetry-q1", "score": 2, "label": "aligned",
   "evidence": [{"path": "<repo path>", "quote": "<verbatim substring of that file>"} | {"command": "<shell>", "last_line": "<what it printed last>"}],
   "finding": "one or two sentences: what the evidence shows against aligned_looks_like and misaligned_looks_like",
   "gap": "required when score is 1 or below: what is missing (0, 1) or what is wrong (-1); empty otherwise"}

Checks:
  coverage   every question in docs/litmus/questionnaire.json answered exactly once (with coverage on)
  scale      score in the frame's scale and label is that score's label; a score above 0 carries at least one evidence item; a score of 1 or below carries a gap
  evidence   a path exists in the repo and the quote is a verbatim substring of the file; a command re-runs here (timeout 180 s) and its last line matches
  isolation  no text names the owner's separate conformance instrument or its vocabulary (the two answer sets never see each other)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
LITMUS = ROOT / "docs" / "litmus"
ANSWERS = LITMUS / "answers"
Q = LITMUS / "questionnaire.json"
FOREIGN = ["full-stack-questionair", "Conformance Questionnaire", "conformance-answer", "check_answers", "CONFORMS", "SUPERSEDES", "DEVIATES", "UNANSWERABLE",
           "evidence_tier", "PROVEN", "cost_statement"]
FOREIGN_RE = re.compile(r"\b[RKCXSA]\d{1,2}-[DMFS]\b")   # the other instrument's question ids


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def run(cmd: str) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return r.returncode, lines[-1].strip() if lines else ""


def check(rows: list[dict], q: dict, errs: list, full: bool, rerun: bool = True) -> None:
    scale = {s["score"]: s["label"] for s in q["frame"]["scale"]}
    qids = {qq["id"] for s in q["sections"] for qq in s["questions"]}
    seen = set()
    for r in rows:
        qid = r.get("question_id", "?")
        if qid not in qids:
            errs.append(f"{qid}: not a question in the questionnaire"); continue
        if qid in seen:
            errs.append(f"{qid}: answered twice")
        seen.add(qid)
        sc = r.get("score")
        if sc not in scale:
            errs.append(f"{qid}: score {sc!r} not in the scale {sorted(scale)}"); continue
        if r.get("label") != scale[sc]:
            errs.append(f"{qid}: label {r.get('label')!r} is not the scale's label for {sc} ({scale[sc]})")
        ev = r.get("evidence") or []
        if sc > 0 and not ev:
            errs.append(f"{qid}: score {sc} with no evidence")
        if sc <= 1 and not (r.get("gap") or "").strip():
            errs.append(f"{qid}: score {sc} without a gap statement")
        if not (r.get("finding") or "").strip():
            errs.append(f"{qid}: no finding")
        for i, e in enumerate(ev):
            if "path" in e:
                p = ROOT / e["path"]
                if e["path"].startswith("full-stack-questionair") or not p.is_file():
                    errs.append(f"{qid}: evidence[{i}] path {e['path']} does not exist here"); continue
                if not e.get("quote") or e["quote"] not in p.read_text(errors="replace"):
                    errs.append(f"{qid}: evidence[{i}] quote is not a verbatim substring of {e['path']}")
            elif "command" in e:
                if rerun:
                    code, last = run(e["command"])
                    norm = lambda t: re.sub(r"/home/user/AGENT[\w-]*", "<root>", t.strip())   # a worktree prints its own absolute path
                    if norm(last) != norm(e.get("last_line") or ""):
                        errs.append(f"{qid}: evidence[{i}] command re-run printed {last[:70]!r}, answer recorded {(e.get('last_line') or '')[:70]!r}")
            else:
                errs.append(f"{qid}: evidence[{i}] has neither path nor command")
        text = json.dumps(r)
        for f in FOREIGN:
            if f in text:
                errs.append(f"{qid}: names the other instrument ({f!r}); the two answer sets never see each other"); break
        if FOREIGN_RE.search(text):
            errs.append(f"{qid}: carries a question id of the other instrument")
    if full:
        for qid in sorted(qids - seen):
            errs.append(f"coverage: {qid} unanswered")


def load(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        rows += jl(p)
    return rows


def cmd_check(argv: list[str]) -> int:
    q = json.loads(Q.read_text())
    paths = [Path(a) for a in argv] if argv else sorted(ANSWERS.glob("*.jsonl"))
    rows = load(paths)
    errs: list = []
    check(rows, q, errs, full=not argv)
    for e in errs:
        print("ERROR", e)
    print(f"{len(rows)} answers, {len(errs)} errors")
    return 1 if errs else 0


def cmd_scorecard() -> int:
    if cmd_check([]) != 0:
        print("FAIL: no scorecard"); return 1
    q = json.loads(Q.read_text())
    rows = {r["question_id"]: r for r in load(sorted(ANSWERS.glob("*.jsonl")))}
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    secs = []
    for s in q["sections"]:
        per = [(qq["id"], qq["angle"], rows[qq["id"]]["score"]) for qq in s["questions"]]
        scores = [p[2] for p in per]
        by_angle = {}
        for _, a, sc in per:
            by_angle.setdefault(a, []).append(sc)
        secs.append({"id": s["id"], "name": s["name"], "kind": s["kind"], "source": s["source"], "settledness": s["standard"]["settledness"],
                     "min": min(scores), "median": median(scores), "by_angle": {a: min(v) for a, v in by_angle.items()},
                     "misaligned": [p[0] for p in per if p[2] == -1], "absent": [p[0] for p in per if p[2] == 0],
                     "gaps": [{"question_id": p[0], "gap": rows[p[0]]["gap"]} for p in per if p[2] <= 1]})
    labels = {s["score"]: s["label"] for s in q["frame"]["scale"]}
    from collections import Counter
    dist = Counter(r["score"] for r in rows.values())
    out = {"commit": commit, "questions": len(rows), "distribution": {labels[k]: v for k, v in sorted(dist.items())}, "sections": secs}
    (LITMUS / "scorecard.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    L = ["# Litmus scorecard", "", f"Generated by `tools/litmus_answers.py scorecard` at {commit} from `docs/litmus/answers/*.jsonl`. Do not edit by hand. "
         "Each answer carries evidence that resolves in this repo (a verbatim quote from a file, or a command whose last line was re-run here).", "",
         "| Score | Label | Answers |", "|---|---|---|"] + [f"| {k} | {labels[k]} | {v} |" for k, v in sorted(dist.items())]
    L += ["", "| Section | Kind | Settledness | Min | Median | presence | depth | boundary | guarantees | usage | direction | Misaligned | Absent |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in secs:
        ba = s["by_angle"]
        L.append(f"| {s['name']} | {s['kind']} | {s['settledness']} | {s['min']} | {s['median']} | " + " | ".join(str(ba.get(a, "-")) for a in ("presence", "depth", "boundary", "guarantees", "usage", "direction")) +
                 f" | {', '.join(s['misaligned']) or '-'} | {', '.join(s['absent']) or '-'} |")
    L += ["", "## Gaps (score 1 or below)", "", "| Question | Gap |", "|---|---|"]
    for s in secs:
        for g in s["gaps"]:
            L.append(f"| {g['question_id']} | {g['gap'].replace('|', '/')} |")
    (LITMUS / "scorecard.md").write_text("\n".join(L) + "\n")
    print(f"wrote docs/litmus/scorecard.json and scorecard.md: {dict(out['distribution'])}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__); return 2
    if argv[0] == "check":
        return cmd_check(argv[1:])
    if argv[0] == "scorecard":
        return cmd_scorecard()
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
