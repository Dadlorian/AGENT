#!/usr/bin/env python3
"""Gate for docs/reference/card-example-map.json: the hand mapping between the
40 reference-model cards and the seven example areas, now under examples/archived/.

This is a judgment mapping between two vocabularies that were never joined
(reference-model cards vs. litmus sections / example areas), not a sourced
fact, so it carries no citation check the way validate_card_profiles.py does.
What this gate enforces instead is structural honesty:

  - every card address in reference-model.json appears exactly once in the map
    (no silent omissions, no duplicates)
  - every area named in a card's `areas` list is a real directory under examples/archived/
  - every litmus id named in a card's `litmus` list is a real section id in
    docs/litmus/questionnaire.json
  - every entry has a non-empty `why`
  - `origin` is `proposed` on every entry, because this mapping proposes and
    does not claim sourced evidence

  python3 tools/check_card_example_map.py           check the map
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "docs" / "reference" / "card-example-map.json"
MODEL_PATH = ROOT / "docs" / "reference" / "reference-model.json"
QUESTIONNAIRE_PATH = ROOT / "docs" / "litmus" / "questionnaire.json"
# The seven areas this map describes were archived on 2026-09-09 (see
# examples/archived/README.md). The map is the measurement that justified archiving them,
# so it is checked against where they now live, not against the empty new structure.
EXAMPLES_DIR = ROOT / "examples" / "archived"


def model_addresses() -> set:
    model = json.loads(MODEL_PATH.read_text())
    return {
        f"{a['num'][:-1] if a['num'] else a['region']}.{c['order']}"
        for a in model["areas"] for c in a["cards"]
    }


def litmus_ids() -> set:
    q = json.loads(QUESTIONNAIRE_PATH.read_text())
    return {s["id"] for s in q["sections"]}


def example_areas() -> set:
    if not EXAMPLES_DIR.is_dir():
        return set()
    return {p.name for p in EXAMPLES_DIR.iterdir() if p.is_dir()}


def main() -> int:
    errs = []
    if not MAP_PATH.is_file():
        print(f"error:  {MAP_PATH.relative_to(ROOT)} does not exist")
        return 1
    try:
        doc = json.loads(MAP_PATH.read_text())
    except Exception as e:
        print(f"error:  {MAP_PATH.relative_to(ROOT)} unreadable ({e})")
        return 1

    cards = doc.get("cards")
    if not isinstance(cards, list):
        print("error:  top-level `cards` is not a list")
        return 1

    known_addresses = model_addresses()
    known_litmus = litmus_ids()
    known_areas = example_areas()

    seen_addresses = {}
    for i, c in enumerate(cards):
        tag = f"cards[{i}]"
        if not isinstance(c, dict):
            errs.append(f"{tag}: not an object")
            continue
        addr = c.get("address")
        tag = f"cards[{i}] ({addr!r})"

        if addr is None:
            errs.append(f"{tag}: missing address")
        elif addr not in known_addresses:
            errs.append(f"{tag}: address {addr!r} is not a card in reference-model.json")
        else:
            seen_addresses[addr] = seen_addresses.get(addr, 0) + 1

        areas = c.get("areas")
        if not isinstance(areas, list):
            errs.append(f"{tag}: `areas` is not a list")
        else:
            for a in areas:
                if a not in known_areas:
                    errs.append(f"{tag}: area {a!r} is not a real directory under examples/")

        litmus = c.get("litmus")
        if not isinstance(litmus, list):
            errs.append(f"{tag}: `litmus` is not a list")
        else:
            for lid in litmus:
                if lid not in known_litmus:
                    errs.append(f"{tag}: litmus id {lid!r} is not a section in "
                                f"docs/litmus/questionnaire.json")

        why = c.get("why")
        if not why or not isinstance(why, str) or not why.strip():
            errs.append(f"{tag}: `why` is empty")

        origin = c.get("origin")
        if origin != "proposed":
            errs.append(f"{tag}: origin must be 'proposed', got {origin!r}")

    # every card address in the model appears exactly once
    for addr in sorted(known_addresses):
        n = seen_addresses.get(addr, 0)
        if n == 0:
            errs.append(f"missing: card {addr!r} from reference-model.json has no entry in the map")
        elif n > 1:
            errs.append(f"duplicate: card {addr!r} appears {n} times in the map")

    for e in errs:
        print(f"error:  {e}")
    print(f"{len(cards)} entries checked, {len(known_addresses)} cards in the model, "
          f"{len(known_areas)} example areas, {len(known_litmus)} litmus sections, "
          f"{len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
