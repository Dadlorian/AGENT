#!/usr/bin/env python3
"""Run a skill's definition of done and record the result; the only way a row becomes "measured".

Usage: python3 tools/measure.py <skill-name> [--breakage-cmd "<shell that applies the breakage>" --restore-cmd "<shell that undoes it>"]
Runs definition_of_done.criterion, then (if given) the breakage, the criterion again, and the restore.
Writes the real outputs into the skill's definition_of_done (status measured only if the clean run passed
and the breakage run failed), re-renders, and appends a ledger record with both outputs. Never edits text by hand.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: str) -> tuple[int, str]:
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()[-600:]


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__); return 2
    name = argv[0]
    opts = dict(zip(argv[1::2], argv[2::2]))
    p = ROOT / ".claude" / "skills" / name / "skill.json"
    sk = json.loads(p.read_text())
    d = sk["definition_of_done"]
    rc1, out1 = run(d["criterion"])
    result = {"clean_exit": rc1, "clean_output": out1}
    ok = rc1 == 0
    if "--breakage-cmd" in opts:
        run(opts["--breakage-cmd"])
        rc2, out2 = run(d["criterion"])
        run(opts.get("--restore-cmd", "git checkout -- ."))
        result.update({"breakage_exit": rc2, "breakage_output": out2})
        ok = ok and rc2 != 0
    d["status"] = "measured" if ok else "claimed"
    d["measured_run"] = {"by": "tools/measure.py", "commit": run("git rev-parse --short HEAD")[1], **result}
    p.write_text(json.dumps(sk, indent=2, ensure_ascii=False) + "\n")
    run(f"python3 tools/render_skill.py .claude/skills/{name}")
    ledger = json.dumps({"kind": "measure", "skill": name, "agent": "tools/measure.py", "result": result, "status": d["status"]})
    run(f"python3 tools/kb.py ledger '{ledger}'")
    print(f"{name}: {d['status']} (clean exit {rc1}" + (f", breakage exit {result.get('breakage_exit')}" if "breakage_exit" in result else "") + ")")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
