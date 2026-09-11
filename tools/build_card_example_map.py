#!/usr/bin/env python3
"""Derive docs/reference/card-example-map.json from the reference model and the planned areas.

  python3 tools/build_card_example_map.py           rewrite the map
  python3 tools/build_card_example_map.py --check   exit 1 if the map differs from what this renders

WHY THIS IS DERIVED NOW
-----------------------
The old map was a hand judgement: 40 cards assigned by reasoning to seven journey areas, each with
a `why` explaining what that area demonstrated about that card. Those seven were archived on
2026-09-09, and the map kept pointing at them -- a blocking gate passing on deleted work.

Under the replacement structure a card belongs to exactly one area BY CONSTRUCTION: the areas are
the reference model's own nine, so card 3.3 sits in area 3 and nowhere else. There is no judgement
left in the placement, so it is derived and the gate checks the derivation.

The judgement moved rather than vanished. "Does this area actually demonstrate this card" is now
recorded per area in examples/reference/<area>/cards.json, as `demonstrates` and
`not_demonstrated`, where it can be checked against a built artifact instead of argued in prose.
`litmus` stays a hand mapping and is carried across from the previous map by address.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "docs" / "reference" / "reference-model.json"
PRINCIPLES = ROOT / "docs" / "reference" / "build-principles.json"
OUT = ROOT / "docs" / "reference" / "card-example-map.json"


def tokens(s: str) -> set:
    return {w for w in re.split(r"[^a-z]+", s.lower()) if len(w) > 3}


def build() -> dict:
    model = json.loads(MODEL.read_text())
    planned = json.loads(PRINCIPLES.read_text())["example_areas"]
    areas = sorted(model["areas"], key=lambda a: a["order"])
    if len(areas) != len(planned):
        raise SystemExit(f"model has {len(areas)} areas, build-principles names {len(planned)}")

    prior = {}
    if OUT.is_file():
        prior = {c["address"]: c for c in json.loads(OUT.read_text()).get("cards", [])}

    cards = []
    for area, dirname in zip(areas, planned):
        # Position gives the pairing; a shared word proves the pairing is not an off-by-one.
        if not (tokens(area["title"]) & tokens(dirname)):
            raise SystemExit(f"area {area['title']!r} and directory {dirname!r} share no word - "
                             f"the orders may have diverged; fix before deriving")
        pre = area["num"][:-1] if area["num"] else area["region"]
        for c in area["cards"]:
            addr = f"{pre}.{c['order']}"
            cards.append({
                "address": addr,
                "card": c["name"],
                "areas": [dirname],
                "origin": "proposed",
                "why": f"derived: card {addr} {c['name']!r} sits in reference-model area "
                       f"{area['order']} {area['title']!r}, whose example area is {dirname}. "
                       f"Whether {dirname} demonstrates this card is recorded in that area's "
                       f"cards.json, not asserted here.",
                "litmus": prior.get(addr, {}).get("litmus", []),
            })
    return {
        "note": "Derived by tools/build_card_example_map.py from docs/reference/reference-model.json "
                "and docs/reference/build-principles.json. Do not hand-edit. Placement is a "
                "derivation; whether an area demonstrates a card lives in "
                "examples/reference/<area>/cards.json. `litmus` is carried across by address from "
                "the previous hand map and remains a judgement.",
        "generated_from": ["docs/reference/reference-model.json",
                           "docs/reference/build-principles.json"],
        "cards": cards,
    }


def main() -> int:
    d = build()
    text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    planned = set(json.loads(PRINCIPLES.read_text())["example_areas"])
    named = {a for c in d["cards"] for a in c["areas"]}
    print(f"{len(d['cards'])} cards over {len(named)} areas; "
          f"all named areas planned: {named <= planned}; "
          f"cards with a litmus mapping carried across: "
          f"{sum(1 for c in d['cards'] if c['litmus'])}")
    if "--check" in sys.argv:
        if not OUT.is_file() or OUT.read_text() != text:
            print(f"error: {OUT.relative_to(ROOT)} differs from what its sources render")
            return 1
        print(f"{OUT.relative_to(ROOT)} matches its sources")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
