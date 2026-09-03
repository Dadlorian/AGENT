#!/usr/bin/env python3
"""Plant two known defects before a review, then check the review caught them, then remove them.

Usage:
  python3 tools/plant.py plant <skill-name>            adds a misquoted sourced row and a restated-without-naming row; records them in state/plants.json
  python3 tools/plant.py check <review-file.json>      exit 1 unless the review's findings mention both planted rows (by skill and location)
  python3 tools/plant.py unplant                       restores the skill from the saved copy
A review that misses a plant is discarded (T-t9-07).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "plants.json"


def plant(name: str) -> int:
    p = ROOT / ".claude" / "skills" / name / "skill.json"
    backup = ROOT / "state" / f"plant-backup-{name}.json"
    shutil.copy(p, backup)
    sk = json.loads(p.read_text())
    bp = sk.setdefault("best_practices", [])
    i1 = len(bp)
    bp.append({"text": "Every unit of work must be retried three times before it is reported as failed.", "origin": "sourced", "sources": ["F-b1-02"], "quote": "The core imports interfaces, never implementations"})
    i2 = len(bp)
    bp.append({"text": "A criterion nothing can fail is not a criterion, so every gate carries a breakage.", "origin": "sourced", "sources": ["F-part-c-04"], "quote": "A criterion nothing can fail is not a criterion"})
    p.write_text(json.dumps(sk, indent=2, ensure_ascii=False) + "\n")
    STATE.write_text(json.dumps({"skill": name, "backup": str(backup), "plants": [{"location": f"best_practices[{i1}]", "kind": "quote-misfit"}, {"location": f"best_practices[{i2}]", "kind": "restated-without-naming"}]}, indent=2))
    import subprocess
    subprocess.run(["python3", "tools/render_skill.py", f".claude/skills/{name}"], cwd=ROOT, capture_output=True)
    print(f"planted 2 defects in {name} at best_practices[{i1}] and [{i2}]")
    return 0


def check(review: str) -> int:
    st = json.loads(STATE.read_text())
    text = Path(review).read_text().lower()
    missed = []
    for pl in st["plants"]:
        loc = pl["location"].lower()
        if not (st["skill"].lower() in text and (loc in text or loc.replace("best_practices", "best_practices ") in text)):
            missed.append(pl)
    if missed:
        print(f"REVIEW MISSED {len(missed)} plant(s): {missed}; discard the review")
        return 1
    print("review caught both plants")
    return 0


def unplant() -> int:
    st = json.loads(STATE.read_text())
    shutil.move(st["backup"], ROOT / ".claude" / "skills" / st["skill"] / "skill.json")
    import subprocess
    subprocess.run(["python3", "tools/render_skill.py", f".claude/skills/{st['skill']}"], cwd=ROOT, capture_output=True)
    STATE.unlink()
    print(f"unplanted {st['skill']}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["plant"] and len(a) == 2:
        sys.exit(plant(a[1]))
    if a[:1] == ["check"] and len(a) == 2:
        sys.exit(check(a[1]))
    if a == ["unplant"]:
        sys.exit(unplant())
    print(__doc__); sys.exit(2)
