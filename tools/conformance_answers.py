#!/usr/bin/env python3
"""Check the answers to the owner's Future-State Conformance Questionnaire (STATUS row 68) against this repo.

Usage:
  python3 tools/conformance_answers.py check [<part.jsonl> ...]   check the parts under full-stack-questionair/answers/ (or the files named); exit 1 on any error
  python3 tools/conformance_answers.py grade                      join the parts into full-stack-questionair/answers.jsonl and run the owner's check_answers.py on it

The owner's instrument fixes the answer contract (verdict, evidence tier, falsifier, cost statement) and its own checker enforces it.
This wrapper adds what the instrument leaves to judgement, so the answers can be trusted against this repo:
  location   every CONFORMS, DEVIATES or SUPERSEDES names at least one path that exists in this repo (the deliverable is the repo)
  quote      evidence at E1 or E2 contains a passage in quotes, at least 20 characters, that is a verbatim substring of one named file
  isolation  no text names the separate litmus questionnaire or its vocabulary (the two answer sets never see each other)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FSQ = ROOT / "full-stack-questionair"
ANSWERS = FSQ / "answers"
FOREIGN = ["litmus", "docs/litmus", "questionnaire.json", "aligned_looks_like", "misaligned_looks_like", "settledness", "leading"]
FOREIGN_RE = re.compile(r"\b[a-z][a-z-]*-q\d{1,2}\b")   # the litmus question ids
PATH_RE = re.compile(r"(?<![\w/])((?:\.claude|harness|docs|kb|tools|examples|schemas|state|PASS\.md|TARGET\.md|README\.md|OWNER\.md|STATUS\.md)[\w./-]*)")
QUOTE_RE = re.compile(r"[\"'“‘]([^\"'”’]{20,})[\"'”’]")


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def check(rows: list[dict], errs: list) -> None:
    for r in rows:
        qid = r.get("qid", "?")
        v = r.get("verdict")
        text = json.dumps(r, ensure_ascii=False)
        low = text.lower()
        for f in FOREIGN:
            if f.lower() in low:
                errs.append(f"{qid}: names the other instrument ({f!r})"); break
        if FOREIGN_RE.search(text):
            errs.append(f"{qid}: carries a question id of the other instrument")
        if v not in ("CONFORMS", "DEVIATES", "SUPERSEDES"):
            continue
        ev = r.get("evidence") or ""
        paths = [p.rstrip(".,;:)") for p in PATH_RE.findall(ev)]
        existing = [p for p in paths if (ROOT / p).exists()]
        if not existing:
            errs.append(f"{qid}: {v} names no path that exists in this repo (found {paths[:3]})"); continue
        if r.get("evidence_tier") in ("E1", "E2"):
            quotes = QUOTE_RE.findall(ev)
            if not quotes:
                errs.append(f"{qid}: {r.get('evidence_tier')} evidence carries no quoted passage of 20 characters or more"); continue
            files = [(ROOT / p) for p in existing if (ROOT / p).is_file()]
            texts = [f.read_text(errors="replace") for f in files]
            if not any(q in t for q in quotes for t in texts):
                errs.append(f"{qid}: no quoted passage is a verbatim substring of a named file ({[p for p in existing][:2]})")


def cmd_check(argv: list[str]) -> int:
    paths = [Path(a) for a in argv] if argv else sorted(ANSWERS.glob("*.jsonl"))
    rows = [r for p in paths for r in jl(p)]
    errs: list = []
    check(rows, errs)
    for e in errs:
        print("ERROR", e)
    print(f"{len(rows)} answers, {len(errs)} errors")
    return 1 if errs else 0


def cmd_grade() -> int:
    if cmd_check([]) != 0:
        print("FAIL: not graded"); return 1
    rows = [r for p in sorted(ANSWERS.glob("*.jsonl")) for r in jl(p)]
    (FSQ / "answers.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    r = subprocess.run(["python3", "check_answers.py", "answers.jsonl"], cwd=FSQ, capture_output=True, text=True)
    print(r.stdout + r.stderr)
    return r.returncode


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__); return 2
    if argv[0] == "check":
        return cmd_check(argv[1:])
    if argv[0] == "grade":
        return cmd_grade()
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
