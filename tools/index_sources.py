#!/usr/bin/env python3
"""Candidate sources for a card, ordered so the best-verifiable ones come first.

`docs/reference/REF-ARCH-INDEX.md` holds 5,828 URLs that four model runs proposed against a
244-question questionnaire, already addressed by card: a question id `3.1.7` belongs to card
3.1 Harness, and the index's sections are the model's own areas (8 -> base, 10 -> rail).

**Nothing here is evidence.** These are URLs a model suggested; no page has been opened. They
enter the knowledge base the same way everything else does -- capture, stamp, gate. What the
index buys is the one thing that was missing when this repo built its corpus: knowing which URL
to try first. The citations that survived verification came from standards bodies and official
docs; the 23 in citation-debt.json came from blogs, Medium and arXiv bodies.

THE ORDERING IS THREE INDEPENDENT AXES, and conflating two of them is a trap this file exists to
prevent:

  trust   core (standards body / formal spec) > primary (official docs) > research. WILD is
          untiered and unknown -- dropped entirely.
  dated   whether the page carries a publication date. A FACT, NOT A QUALITY.
  recency only meaningful for a page that has a date.

The index's own `Bucket` column folds dated-ness into recency: B3 means "older OR undated". So
filtering to B1/B2 -- the obvious move -- deletes 362 of the 435 `core` rows, and 317 of those
are dropped purely for being undated. A living specification carries no dateline; that is what a
current standard looks like. Undated is therefore ranked AHEAD of dated-but-old, never dropped.

  python3 tools/index_sources.py 1.5              candidates for one card
  python3 tools/index_sources.py 1.5 --limit 20   just the top 20
  python3 tools/index_sources.py --coverage       usable candidates per card, whole model
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "reference" / "REF-ARCH-INDEX.md"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"
SECTION_TO_AREA = {"8": "base", "10": "rail"}
TRUST_RANK = {"core": 0, "primary": 1, "research": 2}
# Hosts this repo has measured as unreadable by its own fetcher. Not a judgement on the source --
# arXiv's API returns abstracts and Medium answers 403, so a quote from either cannot be stamped.
UNFETCHABLE = ("arxiv.org", "medium.com", "doi.org", "mdpi.com", "kaggle.com")


def rows():
    """Yield every index row with its owning card address and question id."""
    card = question = None
    for line in INDEX.read_text().splitlines():
        if line.startswith("### "):
            question = line[4:].strip()
            m = re.match(r"^(U|\d+)\.(\d+)(?:\.(\d+))?$", question)
            card = None
            if m and m.group(1) != "U":
                sec = SECTION_TO_AREA.get(m.group(1), m.group(1))
                card = f"{sec}.{m.group(2)}"
            continue
        if not line.startswith("| ") or card is None:
            continue
        p = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(p) < 8 or p[0] in ("Trust", "---") or not p[7].startswith("http"):
            continue
        dated = "†" not in p[3] and p[3].strip("— ") != ""
        yield {"card": card, "question": question, "trust": p[0], "bucket": p[1], "tier": p[2],
               "date": p[3].replace("†", "").strip(), "dated": dated, "models": p[5],
               "also": p[6], "url": p[7],
               "host": urlparse(p[7]).hostname or "?"}


def usable(r) -> bool:
    """WILD is untiered and unknown. A dated row that is genuinely old is demoted out; an UNDATED
    row is kept, because undated is not old."""
    if r["trust"] == "WILD":
        return False
    return not (r["bucket"] == "B3" and r["dated"])


def order_key(r):
    # trust first; then dated-and-recent, then undated, then dated-and-old; then corroboration
    recency = {"B1": 0, "B2": 1}.get(r["bucket"], 2) if r["dated"] else 1.5
    corroboration = -len(r["models"].split())
    return (TRUST_RANK.get(r["trust"], 9), recency, corroboration, r["host"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("card", nargs="?", help="card address, e.g. 1.5 or rail.1")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--coverage", action="store_true", help="usable candidates per card")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    all_rows = [r for r in rows() if usable(r)]

    if args.coverage or not args.card:
        model = json.loads(MODEL.read_text())
        per = collections.defaultdict(collections.Counter)
        for r in all_rows:
            per[r["card"]][r["trust"]] += 1
        print(f"{'card':8} {'core':>5} {'primary':>8} {'research':>9} {'total':>6}")
        for area in model["areas"]:
            num = area["num"][:-1] if area["num"] else area["region"]
            for c in area["cards"]:
                a = f"{num}.{c['order']}"
                k = per.get(a, collections.Counter())
                print(f"{a:8} {k['core']:5} {k['primary']:8} {k['research']:9} {sum(k.values()):6}")
        print(f"\n{len(all_rows)} usable candidates (WILD and dated-old removed) of "
              f"{sum(1 for _ in rows())} index rows")
        return 0

    picked = sorted((r for r in all_rows if r["card"] == args.card), key=order_key)
    if not picked:
        print(f"no candidates for card {args.card!r}")
        return 1
    if args.json:
        print(json.dumps(picked[:args.limit], indent=2))
        return 0
    print(f"card {args.card}: {len(picked)} usable candidates "
          f"(WILD and dated-old removed). Top {min(args.limit, len(picked))}:\n")
    print(f"  {'trust':9} {'when':10} {'runs':5} {'q':9} url")
    for r in picked[:args.limit]:
        when = r["date"] if r["dated"] else "undated"
        warn = "  <- this repo's fetcher cannot read this host" if any(
            h in r["host"] for h in UNFETCHABLE) else ""
        print(f"  {r['trust']:9} {when:10} {len(r['models'].split()):<5} {r['question']:9} "
              f"{r['url'][:88]}{warn}")
    print(f"\nThese are CANDIDATES, not evidence. Capture with tools/capture.py, write records, "
          f"then `python3 tools/stamp_verification.py --fetch` before citing any of them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
