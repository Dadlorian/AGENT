#!/usr/bin/env python3
"""Show whether each ceremony validated and fed the self-improvement loop.

Usage: python3 tools/ceremony_check.py
Per ceremony N it prints, from the records themselves (nothing inferred):
  review    findings by severity, rows sourced/proposed          (kb/ceremonies/ceremony-NN-review.json)
  improve   applied/declined, validator errors after             (kb/ceremonies/ceremony-NN-improve.json)
  lessons   whether a row for N exists in state/lessons.jsonl     (what the next section's agents read)
  brief     whether the brief changed at that ceremony            (git log on state/author-brief.md)
  ledger    the ledger record for the ceremony                    (kb/ledger.jsonl)
  known     known-issues file for the section, if any
Then the trend across ceremonies: findings per skill and proposed share, which should fall if the loop improves.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "kb" / "ceremonies"


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def main() -> int:
    reviews = sorted(C.glob("ceremony-*-review.json"))
    lessons = {r.get("ceremony"): r for r in jl(ROOT / "state" / "lessons.jsonl")}
    ledger = jl(ROOT / "kb" / "ledger.jsonl")
    brief_commits = subprocess.run(["git", "log", "--format=%h %s", "--", "state/author-brief.md"], cwd=ROOT, capture_output=True, text=True).stdout.strip().splitlines()
    trend = []
    for rp in reviews:
        n = int(re.search(r"ceremony-(\d+)-review", rp.name).group(1))
        rv = json.loads(rp.read_text())
        ip = C / f"ceremony-{n:02d}-improve.json"
        im = json.loads(ip.read_text()) if ip.is_file() else None
        m = rv.get("metrics", {})
        sev = {s: sum(1 for f in rv.get("findings", []) if f.get("severity") == s) for s in ("block", "fix", "nit")}
        skills = m.get("skills") or 1
        print(f"ceremony {n} [{rv.get('section', '?')}]")
        print(f"  review   findings block={sev['block']} fix={sev['fix']} nit={sev['nit']} over {skills} skills; rows sourced={m.get('rows_sourced')} proposed={m.get('rows_proposed')}")
        if im:
            ma = im.get("metrics_after", {})
            print(f"  improve  applied={len(im.get('applied', []))} declined={len(im.get('declined', []))} validator_errors_after={ma.get('validator_errors')} lessons={len(im.get('lessons_for_next_section', []))}")
        else:
            print("  improve  (not yet)")
        print(f"  lessons  row for ceremony {n} in state/lessons.jsonl: {'yes' if n in lessons else 'NO'}")
        led = [r for r in ledger if r.get("kind") == "ceremony" and r.get("ceremony") == n]
        print(f"  ledger   {led[0]['id'] + ' ' + led[0].get('result', '')[:80] if led else 'NO record'}")
        known = list(C.glob(f"section-{n:02d}-known-issues.json"))
        print(f"  known    {'broken: ' + ', '.join(json.loads(known[0].read_text()).get('broken', [])) if known else 'none'}")
        total_rows = (m.get("rows_sourced") or 0) + (m.get("rows_proposed") or 0)
        trend.append((n, (sev["block"] + sev["fix"]) / skills, (m.get("rows_proposed") or 0) / total_rows if total_rows else None))
    print("brief   commits touching state/author-brief.md:", len(brief_commits))
    for c in brief_commits[:6]:
        print("   ", c)
    if len(trend) > 1:
        print("trend   (block+fix findings per skill, proposed share) per ceremony:")
        for n, fps, ps in trend:
            print(f"   {n}: {fps:.2f} findings/skill, proposed share {ps if ps is None else round(ps, 2)}")
    else:
        print("trend   needs at least two ceremonies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
