#!/usr/bin/env python3
"""Grade a returned answer sheet against the questionnaire.

Two jobs, and the second is the one that matters.

  1. Enforce the answer contract. A verdict with no evidence is not a verdict;
     a CONFORMS resting on prose is not a CONFORMS; a SUPERSEDES with no stated
     cost is a preference. These are mechanical and are checked mechanically.

  2. Roll each property up to the SHAPE of its evidence, not to a score. A
     number would hide the one distinction worth having: whether a property is
     proven, merely shown, or merely asserted.

Deliberately NOT shipped with the questionnaire. The rollup is the grader, and
the brief's own design rule 6 says the grader is not visible to the graded --
that applies to this instrument as much as to the system it grades.

Run:  python3 check_answers.py answers.jsonl
"""
from __future__ import annotations
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
QS = {q["qid"]: q for q in json.loads((HERE / "questions.json").read_text())}
SPEC = json.loads((HERE / "properties.json").read_text())
PROPS = {p["id"]: p for p in SPEC["properties"]}

VERDICTS = {"CONFORMS", "DEVIATES", "SUPERSEDES", "ABSENT", "UNANSWERABLE"}
TIERS = {"E1", "E2", "E3", "E4"}
STRONG = {"E1", "E2"}


def load(path: str) -> dict[str, dict]:
    rows = {}
    for n, line in enumerate(pathlib.Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"   FAIL  line {n} is not valid JSON: {e}")
            continue
        rows[r.get("qid", f"?line{n}")] = r
    return rows


def contract(rows: dict[str, dict]) -> tuple[int, list[str]]:
    """Job 1: the answer contract. Returns (violations, downgraded qids)."""
    bad = 0
    downgraded = []
    missing = [q for q in QS if q not in rows]
    extra = [q for q in rows if q not in QS]
    if missing:
        bad += len(missing)
        print(f"   FAIL  {len(missing)} question(s) unanswered -- a skipped question makes an omission look identical to a non-issue")
        for q in missing[:12]:
            print(f"         missing: {q}")
        if len(missing) > 12:
            print(f"         ... and {len(missing) - 12} more")
    for q in extra:
        bad += 1
        print(f"   FAIL  {q}: answer for a question that does not exist")

    for qid, r in sorted(rows.items()):
        if qid not in QS:
            continue
        v, tier = r.get("verdict", ""), r.get("evidence_tier", "")
        ev = (r.get("evidence") or "").strip()
        if v not in VERDICTS:
            bad += 1
            print(f"   FAIL  {qid}: verdict {v!r} is not one of {sorted(VERDICTS)}")
            continue
        if v == "ABSENT":
            continue
        if v == "UNANSWERABLE":
            if not ev:
                bad += 1
                print(f"   FAIL  {qid}: UNANSWERABLE must say why -- it is a finding against this questionnaire")
            continue
        if not ev:
            bad += 1
            print(f"   FAIL  {qid}: {v} with no evidence -- a verdict without evidence is an opinion")
        if tier not in TIERS:
            bad += 1
            print(f"   FAIL  {qid}: evidence_tier {tier!r} is not one of {sorted(TIERS)}")
        if v == "CONFORMS":
            if tier in {"E3", "E4"}:
                downgraded.append(qid)
                print(f"   DOWNGRADE  {qid}: CONFORMS resting on {tier} -- records as asserted, not conformant")
            if not (r.get("falsifier") or "").strip():
                bad += 1
                print(f"   FAIL  {qid}: CONFORMS with no falsifier -- if nothing could disprove it, it is an intention")
        if v == "SUPERSEDES" and not (r.get("cost_statement") or "").strip():
            bad += 1
            print(f"   FAIL  {qid}: SUPERSEDES with no cost_statement -- a better answer still has to say what it gives up")
    return bad, downgraded


def met(r: dict | None, downgraded: list[str]) -> bool:
    if not r:
        return False
    if r.get("qid") in downgraded:
        return False
    return r.get("verdict") in {"CONFORMS", "SUPERSEDES"}


def rollup(rows: dict[str, dict], downgraded: list[str]) -> None:
    """Job 2: the shape of each property's evidence."""
    order = ["PROVEN", "SHOWN", "ASSERTED", "DEVIATED", "ABSENT"]
    buckets: dict[str, list[str]] = {k: [] for k in order}
    swap_ok, swap_no = [], []

    for pid, p in PROPS.items():
        d = met(rows.get(f"{pid}-D"), downgraded)
        m = met(rows.get(f"{pid}-M"), downgraded)
        f = met(rows.get(f"{pid}-F"), downgraded)
        if "substitution" in p["angles"]:
            (swap_ok if met(rows.get(f"{pid}-S"), downgraded) else swap_no).append(pid)
        deviated = any((rows.get(f"{pid}-{s}") or {}).get("verdict") == "DEVIATES" for s in "DMF")
        if d and m and f:
            state = "PROVEN"
        elif d and m:
            state = "SHOWN"
        elif d:
            state = "ASSERTED"
        elif deviated:
            state = "DEVIATED"
        else:
            state = "ABSENT"
        buckets[state].append(pid)

    print("\n━━ property rollup — the shape of the evidence, not a score\n")
    meaning = {
        "PROVEN":   "declared, demonstrated, and falsifiable",
        "SHOWN":    "declared and demonstrated, but nothing could disprove it",
        "ASSERTED": "declared only -- a claim",
        "DEVIATED": "knowingly not done, with a stated reason",
        "ABSENT":   "no basis in the deliverable",
    }
    for k in order:
        ids = buckets[k]
        print(f"  {k:<9} {len(ids):>3}   {meaning[k]}")
        if ids:
            print(f"            {' '.join(ids)}")
    print()
    print(f"  swappability proven   {len(swap_ok):>3}   {' '.join(swap_ok)}")
    print(f"  swappability unproven {len(swap_no):>3}   {' '.join(swap_no)}")

    un = [q for q, r in rows.items() if r.get("verdict") == "UNANSWERABLE"]
    if un:
        print(f"\n  ⚠ {len(un)} question(s) returned UNANSWERABLE. These are findings against THIS")
        print("    questionnaire, not against the deliverable. Fix the question or retire it:")
        for q in un:
            print(f"      {q}  {rows[q].get('evidence','')[:90]}")

    print("\n  Read the clusters, not the totals. Gaps spread evenly mean an immature design;")
    print("  gaps concentrated in one group mean a specific blind spot, which is far more useful.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: check_answers.py answers.jsonl"); sys.exit(2)
    rows = load(sys.argv[1])
    print(f"━━ answer contract  ({len(rows)} row(s) against {len(QS)} question(s))\n")
    bad, downgraded = contract(rows)
    if not bad and not downgraded:
        print("   PASS  every question answered, every verdict carries its evidence")
    rollup(rows, downgraded)
    sys.exit(1 if bad else 0)
