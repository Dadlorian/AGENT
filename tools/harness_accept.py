#!/usr/bin/env python3
"""Accept one finished harness into the plan (STATUS row 60).

Usage: python3 tools/harness_accept.py <name>
Runs bash harness/<name>/test.sh and stops on failure; merges harness/<name>/plan-entry.json into harness/plan.json
(by name, replacing an existing entry) and removes the entry file; releases the scope claim 60-harness-<name>;
regenerates docs/acceptance and docs/guides. Prints the test's last line and the acceptance summary. Does not commit.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sh(cmd: str) -> tuple[int, str]:
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__); return 2
    name = argv[0]
    hdir = ROOT / "harness" / name
    if not (hdir / "test.sh").is_file():
        print(f"FAIL: {hdir}/test.sh missing"); return 1
    code, out = sh(f"bash harness/{name}/test.sh")
    last = out.splitlines()[-1] if out else ""
    print(f"test.sh: {last}")
    if code != 0:
        print(f"FAIL: harness/{name}/test.sh exit {code}; not accepted"); return 1
    entry = hdir / "plan-entry.json"
    plan_p = ROOT / "harness" / "plan.json"
    plan = json.loads(plan_p.read_text())
    if entry.is_file():
        e = json.loads(entry.read_text())
        e.setdefault("name", name); e.setdefault("dir", f"harness/{name}")
        plan["harnesses"] = [h for h in plan["harnesses"] if h.get("name") != e["name"]] + [e]
        plan_p.write_text(json.dumps(plan, indent=2) + "\n")
        entry.unlink()
        print(f"plan.json: merged {e['name']} (capability: {e.get('capability')})")
    elif not any(h.get("name") == name for h in plan["harnesses"]):
        print(f"FAIL: no plan-entry.json and no plan.json row for {name}"); return 1
    sh(f"python3 tools/scopes.py release 60-harness-{name}")
    for cmd in ("python3 tools/acceptance_check.py", "python3 tools/render_guide.py", "python3 tools/acceptance_check.py"):
        code, out = sh(cmd)
        if code != 0:
            print(f"FAIL: {cmd}: {out.splitlines()[-1] if out else code}"); return 1
    print(sh("python3 tools/acceptance_check.py")[1].splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
