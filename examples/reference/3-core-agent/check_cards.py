#!/usr/bin/env python3
"""Structural check on this area's claim file. Nothing is demonstrated by implication.

  - the area names the card addresses it demonstrates, and the ones it does not
  - every address named is a real card in docs/reference/reference-model.json
  - every claim is `sourced` with evidence, or `proposed` and says so
  - every card in this area of the model appears in exactly one of the two lists
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
AREA_ORDER = 3


def model_addresses(model: dict) -> set:
    return {f"{a['num'][:-1] if a['num'] else a['region']}.{c['order']}"
            for a in model["areas"] for c in a["cards"]}


def main() -> int:
    errs = []
    d = json.loads((HERE / "cards.json").read_text())
    model = json.loads((ROOT / "docs/reference/reference-model.json").read_text())
    known = model_addresses(model)

    demonstrated = list(d.get("demonstrates") or [])
    gaps = list(d.get("not_demonstrated") or [])
    named = set(demonstrated) | {g.get("address") for g in gaps}

    for addr in sorted(named):
        if addr not in known:
            errs.append(f"address {addr!r} is not a card in reference-model.json")
    if d.get("address") not in demonstrated:
        errs.append(f"the area's own address {d.get('address')!r} is not in `demonstrates`")

    area = next(a for a in model["areas"] if a["order"] == AREA_ORDER)
    expected = {f"{area['num'][:-1]}.{c['order']}" for c in area["cards"]}
    for addr in sorted(expected - named):
        errs.append(f"card {addr!r} is in this area of the model and appears in neither list")
    for addr in sorted(named - expected):
        errs.append(f"card {addr!r} is named but does not belong to area {AREA_ORDER}")

    for g in gaps:
        if not (g.get("why") or "").strip():
            errs.append(f"gap {g.get('address')!r} has no `why`")

    for i, c in enumerate(d.get("claims") or []):
        if c.get("origin") not in ("sourced", "proposed"):
            errs.append(f"claims[{i}]: origin is {c.get('origin')!r}")
        elif c["origin"] == "sourced" and not c.get("evidence"):
            errs.append(f"claims[{i}]: sourced with no evidence -- {c.get('text', '')[:50]}")
        for e in c.get("evidence") or []:
            if not (e.get("id") and e.get("quote")):
                errs.append(f"claims[{i}]: an evidence entry has no id or no quote")

    for e in errs:
        print(f"  error: {e}")
    print(f"{len(demonstrated)} demonstrated, {len(gaps)} recorded as gaps, "
          f"{len(d.get('claims') or [])} claims, {len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
