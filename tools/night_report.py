#!/usr/bin/env python3
"""Write docs/night/report.md, the morning page for the overnight run (STATUS rows 75, 76), from records only."""
import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def sh(c):
    r = subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True); o = (r.stdout + r.stderr).strip().splitlines(); return o[-1] if o else f"exit {r.returncode}"
night = json.loads((ROOT / "state" / "night.json").read_text()) if (ROOT / "state" / "night.json").is_file() else {}
led = [json.loads(l) for l in (ROOT / "kb" / "ledger.jsonl").read_text().splitlines() if l.strip()]
rows75 = [r for r in led if r.get("status_row") == 75]; rows76 = [r for r in led if r.get("status_row") == 76]
parked = json.loads((ROOT / "docs" / "night" / "parked.json").read_text()) if (ROOT / "docs" / "night" / "parked.json").is_file() else []
L = ["# Morning page", "", f"Estimate: {night.get('estimate', '?')}. Actual: {night.get('actual', 'not yet posted')}. Started {night.get('started', '?')}, ended {night.get('ended', '?')}.", "",
     "## Examples (row 75)", ""]
sh("python3 tools/examples_index.py")
L += (ROOT / "docs" / "examples" / "index.md").read_text().splitlines()[4:]
L += ["", "## Answers moved (row 76)", "", f"Mechanism items closed: {sum(1 for r in rows76 if 'B1' in str(r.get('ceremony')))}; sections re-answered: {sum(1 for r in rows76 if 'answer' in str(r.get('ceremony')))}.", ""]
if (ROOT / "docs" / "litmus" / "scorecard-v2.md").is_file():
    L += [l for l in (ROOT / "docs" / "litmus" / "scorecard-v2.md").read_text().splitlines() if l.startswith("|")][:8]
L += ["", "## Parked (needs you)", ""] + ([f"- {p}" for p in parked] or ["- nothing parked"])
L += ["", "## Checks at the end", "", "| Check | Last line |", "|---|---|"]
for c in ("python3 tools/validate_skills.py", "python3 tools/kb.py verify", "python3 tools/kb.py ledger-verify", "python3 tools/status_check.py --freshness", "bash examples/end-to-end/test.sh"):
    L.append(f"| `{c}` | {sh(c)} |")
L += ["", f"Ledger records this night: {len(rows75) + len(rows76)}."]
(ROOT / "docs" / "night" / "report.md").write_text("\n".join(L) + "\n"); print("wrote docs/night/report.md")
