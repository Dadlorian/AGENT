#!/usr/bin/env python3
"""Grade a definition of done by running it: criterion exits 0 clean, breakage applied makes it exit non-zero, restore brings it back."""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
d = json.loads(Path(sys.argv[1]).read_text())
def sh(c):
    r = subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True); return r.returncode
before = subprocess.run("git status --porcelain", shell=True, cwd=ROOT, capture_output=True, text=True).stdout
c0 = sh(d.get("criterion", "false"))
sh(d.get("breakage", "true"))
c1 = sh(d.get("criterion", "false"))
sh(d.get("restore", "true"))
c2 = sh(d.get("criterion", "false"))
after = subprocess.run("git status --porcelain", shell=True, cwd=ROOT, capture_output=True, text=True).stdout
checks = {"criterion passes clean": c0 == 0, "breakage makes it fail": c1 != 0, "restore makes it pass again": c2 == 0, "tree restored (git status unchanged)": before == after,
          "criterion names kb.py verify": "kb.py verify" in d.get("criterion", "")}
for k, v in checks.items():
    print(("ok  " if v else "FAIL"), k)
print(f"{sum(checks.values())} of {len(checks)}")
sys.exit(0 if all(checks.values()) else 1)
