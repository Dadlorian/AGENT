#!/usr/bin/env python3
"""One view of what stands behind every card of the reference model.

This file used to be two: `knowledge_pool.py` asked whether a card was *covered* and
`knowledge_quality.py` asked whether its evidence was *worth trusting*. Two tools, two
documents, similar-looking percentages, and nothing forcing them to agree -- so they drifted,
and a reader (including the model writing the reports) picked whichever number was in front of
them. That gap is the reason this repo spent a session repairing citations it had already
called verified. One document now, or the gap comes back.

Three questions, in the order they should be asked:

  1. WHAT KIND of difference is there between the sentence a card asserts and the page it
     names? Typed per quote, computed by a real fetch (tools/stamp_verification.py), never a
     bare true/false -- a boolean scores a flattened bullet list and an invented statistic
     identically, which is exactly how this repo's own reporting went wrong.
  2. WHERE does a card's evidence come from -- a page someone read, a search snippet nobody
     opened, or this repo's own documents? The third is legitimate for "what we run today" and
     is NOT evidence of industry practice; an example built from a mostly-internal card
     demonstrates our own design.
  3. IS the card covered at all, and how deeply?

Exits non-zero if a profile cites a record a capture pass proved does not support it.

  python3 tools/knowledge_pool.py            print the report
  python3 tools/knowledge_pool.py --write    write docs/reference/knowledge-pool.md
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "docs" / "reference" / "cards"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"
RESEARCH = ROOT / "kb" / "research.jsonl"
KB = ROOT / "kb"
DEBT = ROOT / "docs" / "reference" / "citation-debt.json"
VERIFICATION = ROOT / "docs" / "reference" / "citation-verification.json"
OUT = ROOT / "docs" / "reference" / "knowledge-pool.md"
FETCHED_BAR = 3

VERDICT_MEANING = {
    "exact":         ("the quote is byte-identical on the page", "passes"),
    "formatting":    ("same words; markdown, a flattened list, line numbers or a pronoun differ", "passes"),
    "unretrievable": ("the page could not be read - proves nothing either way", "recorded"),
    "partial":       ("part is on the page, part is not - **a person must read this one**", "blocks until reviewed"),
    "stitched":      ("two non-adjacent passages joined into one sentence", "blocks"),
    "absent":        ("the page does not contain this, or anything close", "blocks"),
}


def load():
    research = {r["id"]: r for r in (json.loads(l) for l in RESEARCH.read_text().splitlines() if l.strip())}
    internal = set()
    for name in ("facts", "target-facts", "reference-facts", "entities", "edges", "architecture"):
        p = KB / f"{name}.jsonl"
        if p.is_file():
            for line in p.read_text().splitlines():
                if line.strip():
                    internal.add(json.loads(line)["id"])
    model = json.loads(MODEL.read_text())
    profiles = {}
    for f in sorted(CARDS.glob("*.json")):
        d = json.loads(f.read_text())
        profiles[d["address"]] = (f.name, d)
    return research, internal, model, profiles


def cites(profile):
    def walk(o):
        if isinstance(o, dict):
            ev = o.get("evidence")
            if isinstance(ev, list):
                for e in ev:
                    if isinstance(e, dict) and e.get("id"):
                        yield e
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    yield from walk(profile)


def known_bad() -> dict:
    if not VERIFICATION.is_file():
        return {}
    return {r["id"]: (r.get("notes") or "page captured; claim not supported")[:150]
            for r in json.loads(VERIFICATION.read_text()).get("records", [])
            if r.get("outcome") == "C_contradicted"}


def main() -> int:
    research, internal, model, profiles = load()
    bad = known_bad()
    debt_n = len(json.loads(DEBT.read_text()).get("entries", [])) if DEBT.is_file() else 0

    verdicts = collections.Counter()
    for rec in research.values():
        verdicts.update(((rec.get("verification") or {}).get("quote_verdicts") or {}).values())

    rows, totals, violations, unread_recs = [], collections.Counter(), [], collections.defaultdict(set)
    for area in model["areas"]:
        num = area["num"][:-1] if area["num"] else area["region"]
        for card in area["cards"]:
            addr = f"{num}.{card['order']}"
            fname, prof = profiles.get(addr, (None, None))
            c = collections.Counter()
            if prof:
                for e in cites(prof):
                    rid = e["id"]
                    if rid in research:
                        rec = research[rid]
                        v = rec.get("verification") or {}
                        if rec["status"] == "fetched" and not v.get("unreachable"):
                            c["read"] += 1
                        else:
                            c["unread"] += 1
                            unread_recs[rid].add(addr)
                        if rid in bad:
                            violations.append((addr, fname, rid, bad[rid]))
                    elif rid in internal:
                        c["internal"] += 1
                    else:
                        c["broken"] += 1
            n = sum(c.values())
            totals.update(c)
            grade = ("undocumented" if not prof else
                     "documented" if c["read"] >= FETCHED_BAR else "unread")
            rows.append({"area": area["title"], "address": addr, "card": card["name"],
                         "status": card["status"], "grade": grade, "n": n,
                         "read": c["read"], "unread": c["unread"], "internal": c["internal"],
                         "gaps": len(prof.get("gaps", [])) if prof else 0,
                         "pct": round(100 * c["read"] / n) if n else 0})

    n = sum(totals.values())
    vt = sum(verdicts.values())
    need = verdicts.get("partial", 0) + verdicts.get("stitched", 0) + verdicts.get("absent", 0)
    grades = collections.Counter(r["grade"] for r in rows)
    L = []
    A = L.append
    A("# Knowledge pool — what stands behind every card")
    A("")
    A("Generated by `python3 tools/knowledge_pool.py --write`. Every figure is a join against a real "
      "record, not a score. **Re-run it rather than trusting these numbers later.**")
    A("")
    A("This was two documents — one asking whether a card was *covered*, one asking whether its "
      "evidence was *trustworthy*. They drifted, their percentages looked alike, and the difference "
      "got read wrong. It is one document now for that reason.")
    A("")
    A("## 1. Every quote, typed — the number to act on")
    A("")
    A("Not whether a citation passed, but **what kind of difference** there is between the sentence a "
      "card asserts and the page it names. A bare true/false scored a flattened bullet list and an "
      "invented statistic identically.")
    A("")
    A("| Verdict | Meaning | Quotes | Share | Gate |")
    A("|---|---|---:|---:|---|")
    for k in ("exact", "formatting", "unretrievable", "partial", "stitched", "absent"):
        if verdicts.get(k):
            m, g = VERDICT_MEANING[k]
            A(f"| `{k}` | {m} | {verdicts[k]} | {100*verdicts[k]/vt:.1f}% | {g} |")
    A("")
    A(f"**{need} of {vt} quotes need a human decision.** The system settled the rest on its own. "
      f"No check can separate a faithful paraphrase of a page from an invented quote — both share the "
      f"source's vocabulary — so `partial` is deliberately a *needs-a-reader* bucket, not a verdict.")
    if debt_n:
        A("")
        A(f"{debt_n} citations predating this rule are enumerated in "
          f"`docs/reference/citation-debt.json`. That file is debt, not permission: nothing writes to "
          f"it automatically.")
    A("")
    if violations:
        A("## Live citations to records already proven unsupported")
        A("")
        A("| Card | Profile | Record | What is wrong |")
        A("|---|---|---|---|")
        for a, f, rid, why in sorted(set(violations)):
            A(f"| {a} | `{f}` | `{rid}` | {why} |")
        A("")
    A("## 2. Where the evidence comes from")
    A("")
    A("| Class | What it means | Citations | Share |")
    A("|---|---|---:|---:|")
    A(f"| **read** | A page someone fetched and whose quote was checked against it | {totals['read']} | {100*totals['read']/n:.1f}% |")
    A(f"| **unread** | External source, page never opened — a search-result snippet | {totals['unread']} | {100*totals['unread']/n:.1f}% |")
    A(f"| **internal** | This repo's own documents (F/T/REF/A) — our intent or current state, **not industry practice** | {totals['internal']} | {100*totals['internal']/n:.1f}% |")
    A(f"| **broken** | Resolves nowhere in the knowledge base | {totals['broken']} | {100*totals['broken']/n:.1f}% |")
    A("")
    A(f"**{n} citations across {len([r for r in rows if r['n']])} profiled cards.** "
      f"An example built from a card whose evidence is mostly `internal` demonstrates this repo's own "
      f"design, not an industry pattern — that is a real decision, not a scoring artifact.")
    A("")
    if unread_recs:
        A("## 3. Records still to check")
        A("")
        A(f"**{len(unread_recs)} distinct records** stand behind every `unread` citation in the model, "
          f"across {len({urlparse(research[r]['url']).hostname for r in unread_recs if r in research})} "
          f"hosts. That is the list to close before building on those cards.")
        A("")
        A("| Record | Cards | Host |")
        A("|---|---|---|")
        for rid, cds in sorted(unread_recs.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            host = urlparse(research[rid]["url"]).hostname if rid in research else "?"
            A(f"| `{rid}` | {', '.join(sorted(cds))} | {host} |")
        A("")
    A("## 4. By card")
    A("")
    A(f"**{grades['documented']} documented · {grades['unread']} unread · "
      f"{grades['undocumented']} undocumented**, of {len(rows)} cards. "
      f"*documented* = a profile with {FETCHED_BAR}+ read citations; *unread* = a profile whose "
      f"sources are search snippets; *undocumented* = no profile at all.")
    A("")
    for area in model["areas"]:
        ar = [r for r in rows if r["area"] == area["title"]]
        if not ar:
            continue
        A(f"### {area['title']}")
        A("")
        A("| Card | Name | Model | Grade | read | unread | internal | total | % read | gaps |")
        A("|---|---|---|---|---:|---:|---:|---:|---:|---:|")
        for r in ar:
            A(f"| {r['address']} | {r['card']} | {r['status']} | {r['grade']} | {r['read']} | "
              f"{r['unread']} | {r['internal']} | {r['n']} | {r['pct']}% | {r['gaps']} |")
        A("")

    text = "\n".join(L) + "\n"
    if "--write" in sys.argv:
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        print(text)
    print(f"{n} citations: {totals['read']} read, {totals['unread']} unread, "
          f"{totals['internal']} internal, {totals['broken']} broken | "
          f"{vt} quotes typed, {need} need a person | "
          f"{grades['documented']}/{grades['unread']}/{grades['undocumented']} "
          f"documented/unread/undocumented")
    if violations:
        print(f"FAIL: {len(set(violations))} live citation(s) to records proven unsupported")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
