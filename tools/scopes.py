#!/usr/bin/env python3
"""Agent scope registry: refuse two live agents editing the same paths (STATUS row 43).

Usage:
  python3 tools/scopes.py claim <agent-label> <path-prefix> [<path-prefix> ...]   exit 1 if any prefix overlaps a live claim
  python3 tools/scopes.py release <agent-label>
  python3 tools/scopes.py list
Claims live in state/agent-scopes.json. A prefix overlaps another if either is a prefix of the other.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "agent-scopes.json"


def load() -> dict:
    return json.loads(STATE.read_text()) if STATE.is_file() else {}


def save(d: dict):
    STATE.write_text(json.dumps(d, indent=2) + "\n")


def overlaps(a: str, b: str) -> bool:
    a, b = a.rstrip("/") + "/", b.rstrip("/") + "/"
    return a.startswith(b) or b.startswith(a)


def main(argv: list[str]) -> int:
    d = load()
    if argv[:1] == ["list"]:
        for k, v in d.items():
            print(k, "->", ", ".join(v))
        print(f"{len(d)} live claims")
        return 0
    if argv[:1] == ["release"] and len(argv) == 2:
        d.pop(argv[1], None); save(d); print("released", argv[1]); return 0
    if argv[:1] == ["claim"] and len(argv) >= 3:
        label, paths = argv[1], argv[2:]
        for other, theirs in d.items():
            if other == label:
                continue
            for p in paths:
                for q in theirs:
                    if overlaps(p, q):
                        print(f"REFUSED: {label} wants {p}, overlaps {other}'s {q}")
                        return 1
        d[label] = paths; save(d); print("claimed", label, "->", ", ".join(paths)); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
