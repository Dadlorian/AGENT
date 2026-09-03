#!/usr/bin/env python3
"""Honesty spot-check of an answer set (STATUS rows 67 and 68): a verifier who never saw the crew's answers re-answers a sample.

Usage:
  python3 tools/spot_check.py sample litmus|conformance <n> [<seed>]     print n question ids, chosen deterministically from the seed (default: HEAD)
  python3 tools/spot_check.py compare litmus <verifier.jsonl>             agreement between the verifier's rows and docs/litmus/answers/*.jsonl
  python3 tools/spot_check.py compare conformance <verifier.jsonl>        agreement between the verifier's rows and full-stack-questionair/answers/*.jsonl

Agreement, litmus: exact score match, and within one step; a crew score of 2 or 3 where the verifier scores 0 or -1 is a contradiction and is listed.
Agreement, conformance: verdict match; a crew CONFORMS where the verifier says ABSENT or DEVIATES is a contradiction and is listed.
The sample is the plant of this step: a set that contradicts its verifier on more than one in five sampled questions is re-answered by a different crew.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def ids(instr: str) -> list[str]:
    if instr == "litmus":
        q = json.loads((ROOT / "docs" / "litmus" / "questionnaire.json").read_text())
        return [qq["id"] for s in q["sections"] for qq in s["questions"]]
    return [q["qid"] for q in json.loads((ROOT / "full-stack-questionair" / "questions.json").read_text())]


def crew(instr: str) -> dict[str, dict]:
    d = ROOT / "docs" / "litmus" / "answers" if instr == "litmus" else ROOT / "full-stack-questionair" / "answers"
    key = "question_id" if instr == "litmus" else "qid"
    return {r[key]: r for p in sorted(d.glob("*.jsonl")) for r in jl(p)}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__); return 2
    cmd, instr = argv[0], argv[1]
    if cmd == "sample":
        n = int(argv[2])
        seed = argv[3] if len(argv) > 3 else subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        rng = random.Random(seed)
        allq = ids(instr)
        print("\n".join(sorted(rng.sample(allq, n))))
        return 0
    if cmd == "compare":
        ver = jl(Path(argv[2]))
        c = crew(instr)
        key = "question_id" if instr == "litmus" else "qid"
        exact = near = 0
        contradictions = []
        for v in ver:
            r = c.get(v[key])
            if not r:
                print(f"{v[key]}: no crew answer"); continue
            if instr == "litmus":
                a, b = r["score"], v["score"]
                exact += a == b; near += abs(a - b) <= 1
                if a >= 2 and b <= 0:
                    contradictions.append((v[key], a, b))
            else:
                a, b = r["verdict"], v["verdict"]
                exact += a == b; near += a == b
                if a == "CONFORMS" and b in ("ABSENT", "DEVIATES"):
                    contradictions.append((v[key], a, b))
        n = len(ver)
        print(f"{instr}: {n} sampled, {exact} exact, {near} within one step, {len(contradictions)} contradictions")
        for cd in contradictions:
            print("  contradiction:", *cd)
        return 1 if n and len(contradictions) * 5 > n else 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
