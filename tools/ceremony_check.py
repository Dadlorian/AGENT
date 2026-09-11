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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "kb" / "ceremonies"


def jl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def parse_name(name: str) -> tuple:
    """`ceremony-12-review-79-reference-example.json` -> (12, '-79-reference-example')."""
    m = re.search(r"ceremony-(\d+)-review(.*)\.json$", name)
    return int(m.group(1)), m.group(2)


def lesson_for(lessons: dict, n: int):
    """A lessons row keys `ceremony` as an int for early ceremonies and as `<n>-<section>` since."""
    if n in lessons:
        return lessons[n]
    for k, v in lessons.items():
        if isinstance(k, str) and (k == str(n) or k.startswith(f"{n}-")):
            return v
    return None


def main() -> int:
    # `ceremony-*-review.json` only. The repo moved to suffixed names -- one per fan-out group
    # (`-xc`, `-compose`) and, since the owner's naming rule, one per STATUS row
    # (`-79-reference-example`). This tool kept the narrow glob and silently stopped seeing every
    # ceremony after 10, while still printing `numbering ok` over the set it could see. The trend
    # below is the repo's own evidence that the improvement loop works; it was measuring a corpus
    # that had stopped growing. Widened, and the pairing follows the suffix.
    reviews = sorted(C.glob("ceremony-*-review*.json"))
    lessons = {r.get("ceremony"): r for r in jl(ROOT / "state" / "lessons.jsonl")}
    ledger = jl(ROOT / "kb" / "ledger.jsonl")
    brief_commits = subprocess.run(["git", "log", "--format=%h %s", "--", "state/author-brief.md"], cwd=ROOT, capture_output=True, text=True).stdout.strip().splitlines()
    trend = []
    for rp in reviews:
        n, suffix = parse_name(rp.name)
        rv = json.loads(rp.read_text())
        im = None
        for cand in (C / f"ceremony-{n:02d}-improve{suffix}.json",
                     C / f"ceremony-{n}-improve{suffix}.json"):
            if cand.is_file():
                im = json.loads(cand.read_text())
                break
        m = rv.get("metrics", {})
        sev = {s: sum(1 for f in rv.get("findings", []) if f.get("severity") == s) for s in ("block", "fix", "nit")}
        skills = m.get("skills")   # None for a ceremony over an area or a tool, not skills
        print(f"ceremony {n} [{rv.get('section', '?')}]")
        over = f"over {skills} skills" if skills else "no skills denominator (not a skills ceremony)"
        print(f"  review   findings block={sev['block']} fix={sev['fix']} nit={sev['nit']} {over}; "
              f"rows sourced={m.get('rows_sourced')} proposed={m.get('rows_proposed')}")
        if im:
            ma = im.get("metrics_after", {})
            print(f"  improve  applied={len(im.get('applied', []))} declined={len(im.get('declined', []))} validator_errors_after={ma.get('validator_errors')} lessons={len(im.get('lessons_for_next_section', []))}")
        else:
            print("  improve  (not yet)")
        print(f"  lessons  row for ceremony {n} in state/lessons.jsonl: "
              f"{'yes' if lesson_for(lessons, n) else 'NO'}")
        led = [r for r in ledger if r.get("ceremony") == n
               or (r.get("kind") == "ceremony" and r.get("ceremony") == n)]
        print(f"  ledger   {led[0]['id'] + ' ' + led[0].get('result', '')[:80] if led else 'NO record'}")
        known = list(C.glob(f"section-{n:02d}-known-issues.json"))
        print(f"  known    {'broken: ' + ', '.join(json.loads(known[0].read_text()).get('broken', [])) if known else 'none'}")
        total_rows = (m.get("rows_sourced") or 0) + (m.get("rows_proposed") or 0)
        per_skill = (sev["block"] + sev["fix"]) / skills if skills else None
        trend.append((n, per_skill, sev["block"] + sev["fix"],
                      (m.get("rows_proposed") or 0) / total_rows if total_rows else None))
    # Ceremony numbers are a repository-global counter: contiguous from 1, never reused, one section per number.
    nums = [parse_name(rp.name)[0] for rp in reviews]
    sections = [json.loads(rp.read_text()).get("section") for rp in reviews]
    problems = []
    # A number may carry several records -- one per fan-out group, or per STATUS row. What must
    # hold is that the numbers used are contiguous from 1, not that there is exactly one file each.
    distinct = sorted(set(nums))
    if distinct != list(range(1, len(distinct) + 1)):
        problems.append(f"numbers used are {distinct}, expected {list(range(1, len(distinct) + 1))}")
    dup_sections = sorted({s for s in sections if sections.count(s) > 1})
    if dup_sections:
        problems.append("section reused across ceremonies: " + ", ".join(map(str, dup_sections)))
    fanned = sorted({n for n in distinct if nums.count(n) > 1})
    print(f"numbering {len(reviews)} review record(s) over {len(distinct)} ceremony number(s)"
          + (f"; fanned out: {fanned}" if fanned else "")
          + ("  ok" if not problems else "  PROBLEM: " + "; ".join(problems)))
    print("brief   commits touching state/author-brief.md:", len(brief_commits))
    for c in brief_commits[:6]:
        print("   ", c)
    if len(trend) > 1:
        print("trend   (block+fix findings per skill, proposed share) per ceremony:")
    for n, per_skill, raw, share in trend:
        # A denominator of 1 was being supplied for ceremonies that reviewed no skills, which turned
        # a raw finding count into a rate. A number without its measurement is not a fact.
        rate = (f"{per_skill:.2f} findings/skill" if per_skill is not None
                else f"{raw} findings, no skills denominator")
        print(f"   {n}: {rate}, proposed share "
              + (f"{share:.2f}" if share is not None else "not recorded"))
    rated = [t for t in trend if t[1] is not None]
    print(f"\n{len(rated)} of {len(trend)} ceremonies carry a skills denominator; the trend line is "
          f"over those {len(rated)}. The rest reviewed areas or tools and are counted, not rated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
