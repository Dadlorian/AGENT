#!/usr/bin/env python3
"""The grader is never visible to the graded -- the part of that a tool can decide.

  python3 tools/grader_isolation.py             check every live example area
  python3 tools/grader_isolation.py --selftest  plant each violation, prove they fail

WHY
---
state/lessons.jsonl, ceremony 71-outcome, 2026-09-04: "The graders sat in the tree, so a
without-skill agent read and satisfied the checker: the grader was visible to the graded (design
rule 6). Graders for an outcome eval live outside the tree until grading."

WHAT THIS CAN AND CANNOT DECIDE
-------------------------------
It cannot decide the core of the lesson. This repo's graders are committed at
docs/night/hidden/<area>.sh, in the same tree as the areas they grade, so an author who wants to
read one can. No check inside the repo can prevent that; the control is procedural -- the grader is
written by an agent that never saw the area, and this repo does that.

What it can decide is the three ways the separation gets lost by accident rather than by intent:

  missing   a live area has no grader at all, so "the hidden check decides" is an empty claim
  inside    a grader sits in the area it grades, where its author reads it while authoring
  invoked   an area's own gate runs its grader, which makes the hidden check part of the
            visible one and collapses the two into a gate the author can tune

Naming the grader's path in prose is NOT a violation: the path is public, the contents are the
point, and pretending otherwise would fail this repo's own README for stating where its grader is.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIDDEN = ROOT / "docs" / "night" / "hidden"
BLOCKING = ("missing", "inside", "invoked")
# A reference to the grader inside a runnable line, not inside a comment or a prose file.
INVOKE = re.compile(r"^[^#\n]*\b(?:bash|sh|source|\.)\s+\S*night/hidden/\S+", re.M)


# examples/end-to-end/ is gated like an area and is not one. examples/reference/README.md says so
# outright: "examples/end-to-end/ stays where it is. It is the reference walk across all of them,
# not one of them." The grader rule is about areas, so it is out of scope here -- declared with its
# citation rather than quietly skipped, because an undeclared exclusion is how a rule loses its
# corpus. It still has a visible gate; tools/examples_gate.py runs it.
NOT_AN_AREA = {"end-to-end"}


def live_areas(root: Path = None) -> list:
    base = (root or ROOT) / "examples"
    found = [p.parent for p in sorted(base.glob("*/test.sh"))
             if p.parent.name not in ({"archived"} | NOT_AN_AREA)]
    found += [p.parent for p in sorted(base.glob("reference/*/test.sh"))]
    return found


def check(areas, hidden: Path = None) -> list:
    hidden = hidden or HIDDEN
    findings = []
    for area in areas:
        grader = hidden / f"{area.name}.sh"
        if not grader.is_file():
            findings.append({"area": area.name, "verdict": "missing",
                             "what": f"no grader at {grader.name}"})
        for f in sorted(area.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            if f.name == f"{area.name}.sh" and f.parent != hidden:
                findings.append({"area": area.name, "verdict": "inside",
                                 "what": f"a grader-named file sits in the area: {f.name}"})
            if f.suffix in (".sh", ".py"):
                try:
                    if INVOKE.search(f.read_text()):
                        findings.append({"area": area.name, "verdict": "invoked",
                                         "what": f"{f.name} runs its own grader"})
                except Exception:
                    pass
        if not any(x["area"] == area.name for x in findings):
            findings.append({"area": area.name, "verdict": "separate",
                             "what": f"grader at {grader.name}, not in the area, "
                                     f"not invoked by it"})
    return findings


def report(findings: list) -> int:
    for f in sorted(findings, key=lambda f: f["verdict"] not in BLOCKING):
        mark = "BLOCK" if f["verdict"] in BLOCKING else "ok"
        print(f"  {mark:5} {f['area']:22} {f['verdict']:9} {f['what'][:60]}")
    bad = [f for f in findings if f["verdict"] in BLOCKING]
    print(f"{len({f['area'] for f in findings})} live area(s); {len(bad)} need a person.")
    print("note: the grader being readable at all is procedural, not checkable here -- "
          "see this tool's docstring.")
    return 1 if bad else 0


def selftest() -> int:
    import shutil, tempfile
    areas = live_areas()
    clean = [f for f in check(areas) if f["verdict"] in BLOCKING]
    caught = set()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "examples" / "reference" / "fake").mkdir(parents=True)
        # Mirror the real layout: the invoke pattern looks for `night/hidden/`, so a temp tree
        # that flattens it would let the plant pass and the arm ship unproven.
        (d / "docs" / "night" / "hidden").mkdir(parents=True)
        area = d / "examples" / "reference" / "fake"
        (area / "test.sh").write_text("echo hi\n")
        # 1. no grader anywhere
        H = d / "docs" / "night" / "hidden"
        caught |= {f["verdict"] for f in check([area], H)}
        # 2. grader exists, but a copy sits inside the area
        (H / "fake.sh").write_text("echo grade\n")
        (area / "fake.sh").write_text("echo grade\n")
        caught |= {f["verdict"] for f in check([area], H)}
        (area / "fake.sh").unlink()
        # 3. the area's own gate runs its grader
        (area / "test.sh").write_text("bash ../../../docs/night/hidden/fake.sh\n")
        caught |= {f["verdict"] for f in check([area], H)}
    print("self-test - plant a missing grader, a grader inside the area, and an area that runs it")
    print(f"  before planting: {len(clean)} blocking finding(s) in the real tree")
    print(f"  planted verdicts caught: {sorted(caught & set(BLOCKING))}")
    ok = not clean and set(BLOCKING) <= caught
    print("PASS - all three separations fail when broken, and none fires in the real tree" if ok
          else "FAIL - a planted violation was not caught")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    areas = live_areas()
    if not areas:
        print("no live example areas; nothing to check")
        return 0
    return report(check(areas))


if __name__ == "__main__":
    sys.exit(main())
