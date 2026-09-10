#!/usr/bin/env python3
"""Is the reference model ready to build examples from? Answer measured, not asserted.

"Ready" has been an opinion in this repo, and opinions are how seven example areas got built on
an unproven structure and then archived. Each condition below is a command or a named artifact,
so readiness is something you run rather than something someone declares.

Two of the eight are deliberately NOT machine-decidable -- what the reference model is *for*, and
whether a card profile is sufficient to build from. The first is owner intent; the second can only
be answered by attempting one example and writing down what the profile failed to tell you. Both
are recorded as artifacts so the tool can see that a person answered them, without pretending to
answer them itself.

  python3 tools/ready_to_build.py           print the table, exit 1 if not ready
  python3 tools/ready_to_build.py --json    machine-readable
"""
from __future__ import annotations

import collections
import glob
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRINCIPLES = ROOT / "docs" / "reference" / "build-principles.json"
DEBT = ROOT / "docs" / "reference" / "citation-debt.json"
SUFFICIENCY = ROOT / "docs" / "reference" / "profile-sufficiency.md"


def run(argv):
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=900)
    return p.returncode, (p.stdout + p.stderr).strip()


def conditions():
    out = []

    # R1 -- every card has a profile that passes the gate
    model = json.loads((ROOT / "docs/reference/reference-model.json").read_text())
    total = sum(len(a["cards"]) for a in model["areas"])
    have = len(glob.glob(str(ROOT / "docs/reference/cards/*.json")))
    code, _ = run(["python3", "tools/validate_card_profiles.py"])
    out.append(("R1", "every card profiled, gate green", have == total and code == 0,
                f"{have} of {total} profiled, gate exit {code}",
                "python3 tools/validate_card_profiles.py"))

    # R2 -- no quote left needing a human read
    research = [json.loads(l) for l in (ROOT / "kb/research.jsonl").read_text().splitlines() if l.strip()]
    v = collections.Counter()
    for r in research:
        v.update(((r.get("verification") or {}).get("quote_verdicts") or {}).values())
    need = v["partial"] + v["stitched"] + v["absent"]
    out.append(("R2", "no quote still needs a reader", need == 0,
                f"{need} need a person ({v['partial']} partial, {v['stitched']} stitched, {v['absent']} absent)",
                "python3 tools/knowledge_pool.py"))

    # R3 -- citation debt burned down, or every entry carries an owner decision
    entries = json.loads(DEBT.read_text()).get("entries", []) if DEBT.is_file() else []
    undecided = [e for e in entries if not e.get("owner_decision")]
    out.append(("R3", "no undecided citation debt", not undecided,
                f"{len(entries)} entries, {len(undecided)} without an owner_decision",
                "docs/reference/citation-debt.json"))

    # R4 -- prose is gated. Nothing reads text/role/covers/note today; a fabricated figure with no
    # quote attached passes every checker, which is how two invented statistics survived.
    gate = ROOT / "tools" / "prose_gate.py"
    code = run(["python3", "tools/prose_gate.py"])[0] if gate.is_file() else None
    out.append(("R4", "prose carries no unsourced quote or figure", gate.is_file() and code == 0,
                "tools/prose_gate.py does not exist" if not gate.is_file() else f"gate exit {code}",
                "python3 tools/prose_gate.py"))

    # R5 -- the card->example map names the areas we will actually build
    m = json.loads((ROOT / "docs/reference/card-example-map.json").read_text())
    named = {a for c in m.get("cards", []) for a in c.get("areas", [])}
    planned = set(json.loads(PRINCIPLES.read_text()).get("example_areas", [])) if PRINCIPLES.is_file() else set()
    ok = bool(planned) and named and named <= planned
    out.append(("R5", "card->example map points at the areas we will build", ok,
                f"map names {sorted(named)[:4]}{'...' if len(named) > 4 else ''}; "
                f"{'no planned set recorded' if not planned else 'planned ' + str(sorted(planned)[:4])}",
                "docs/reference/card-example-map.json vs build-principles.json"))

    # R6 -- owner has said what the reference model is FOR (industry description vs this platform).
    # 31.7% of citations are this repo citing itself; the answer changes which cards can carry an
    # example at all. Intent, not evidence -- a person must write it.
    pr = json.loads(PRINCIPLES.read_text()) if PRINCIPLES.is_file() else {}
    out.append(("R6", "the model's purpose is decided (owner)", bool(pr.get("model_purpose")),
                pr.get("model_purpose", "not recorded")[:60] if pr else "build-principles.json does not exist",
                "docs/reference/build-principles.json"))

    # R7 -- a profile has been PROVEN sufficient to build from, by building one and writing down
    # what it did not tell you. Until then "the profile is the spec" is an assertion.
    areas = [d for d in glob.glob(str(ROOT / "examples/reference/*")) if Path(d).is_dir()]
    out.append(("R7", "one example built from a profile, gaps written down",
                bool(areas) and SUFFICIENCY.is_file(),
                f"{len(areas)} area(s) built; sufficiency note {'present' if SUFFICIENCY.is_file() else 'missing'}",
                "examples/reference/<area>/ + docs/reference/profile-sufficiency.md"))

    # R8 -- cards whose evidence is mostly this repo are labelled, so nobody demonstrates our own
    # design as an industry pattern by accident
    out.append(("R8", "internal-heavy cards labelled", bool(pr.get("internal_share_policy")),
                pr.get("internal_share_policy", "not recorded")[:60] if pr else "not recorded",
                "docs/reference/build-principles.json"))
    return out


def main() -> int:
    conds = conditions()
    if "--json" in sys.argv:
        print(json.dumps([{"id": i, "what": w, "met": m, "now": n, "check": c}
                          for i, w, m, n, c in conds], indent=2))
    else:
        met = sum(1 for *_, m, _, _ in [(c[0], c[1], c[2], c[3], c[4]) for c in conds] if m)
        print("READY TO BUILD — definition of ready\n")
        for i, what, ok, now, check in conds:
            print(f"  [{'x' if ok else ' '}] {i}  {what:46} {now}")
            print(f"        check: {check}")
        print(f"\n{met} of {len(conds)} conditions met.")
        if met < len(conds):
            print("NOT READY. Building before these hold is how examples/archived/ happened.")
    return 0 if all(c[2] for c in conds) else 1


if __name__ == "__main__":
    sys.exit(main())
