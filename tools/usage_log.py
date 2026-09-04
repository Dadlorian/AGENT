#!/usr/bin/env python3
"""Record one skill load (STATUS row 72). Wired as a Claude Code PreToolUse hook on the Skill tool in .claude/settings.json.

Reads the hook's JSON from stdin ({"tool_name": "Skill", "tool_input": {"skill": "<name>", ...}, "session_id": ...})
and appends {"skill", "at", "session"} to state/usage.jsonl. Never blocks the tool: any failure exits 0 silently.
The self-improvement loop reads this file at a ceremony to know whether a skill was used at all (owner rule, 2026-09-03).
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
        skill = (d.get("tool_input") or {}).get("skill")
        if not skill:
            return 0
        rec = {"skill": skill.split(":")[-1], "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "session": (d.get("session_id") or "")[:12]}
        with (ROOT / "state" / "usage.jsonl").open("a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
