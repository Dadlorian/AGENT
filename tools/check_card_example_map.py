"""Gate for docs/reference/card-example-map.json: the join between the 40 reference-model cards
and the nine example areas under examples/reference/.

Placement is no longer a judgement. A card belongs to exactly one area by construction, because the
areas ARE the model's own nine, so the map is derived by tools/build_card_example_map.py and this
gate checks the derivation held. The judgement moved to where it can be checked against a built
artifact: whether an area actually demonstrates a card is recorded in
examples/reference/<area>/cards.json.

What this enforces:

  - every card address in reference-model.json appears exactly once in the map
    (no silent omissions, no duplicates)
  - every area a card names is one of the planned areas in build-principles.json --
    an area need not exist yet to be named
  - for an area that DOES exist, its cards.json accounts for every card mapped to it,
    as `demonstrates` or as a recorded gap in `not_demonstrated`
  - every litmus id named is a real section in docs/litmus/questionnaire.json
  - every entry has a non-empty `why`, and `origin` is `proposed` on every entry

  python3 tools/check_card_example_map.py           check the map
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "docs" / "reference" / "card-example-map.json"
MODEL_PATH = ROOT / "docs" / "reference" / "reference-model.json"
QUESTIONNAIRE_PATH = ROOT / "docs" / "litmus" / "questionnaire.json"
# Until 2026-09-11 this pointed at examples/archived/, so the gate passed on seven areas that had
# been deleted -- a green check over dead work. The map is now derived by
# tools/build_card_example_map.py onto the nine planned areas, so what must hold is: every named
# area is one we plan to build, and for any area that EXISTS, every card mapped to it is accounted
# for in that area's own cards.json, as demonstrated or as a recorded gap.
PRINCIPLES = ROOT / "docs" / "reference" / "build-principles.json"
EXAMPLES_DIR = ROOT / "examples" / "reference"


def model_addresses() -> set:
    model = json.loads(MODEL_PATH.read_text())
    return {
        f"{a['num'][:-1] if a['num'] else a['region']}.{c['order']}"
        for a in model["areas"] for c in a["cards"]
    }


def litmus_ids() -> set:
    q = json.loads(QUESTIONNAIRE_PATH.read_text())
    return {s["id"] for s in q["sections"]}


def planned_areas() -> set:
    """The areas the owner decided to build. An area need not exist yet to be named."""
    return set(json.loads(PRINCIPLES.read_text()).get("example_areas", []))


def built_areas() -> dict:
    """name -> cards.json, for areas that exist and declare what they cover."""
    out = {}
    if not EXAMPLES_DIR.is_dir():
        return out
    for p in sorted(EXAMPLES_DIR.iterdir()):
        cj = p / "cards.json"
        if p.is_dir() and cj.is_file():
            out[p.name] = json.loads(cj.read_text())
    return out


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
    known_areas = planned_areas()
    built = built_areas()

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
                    errs.append(f"{tag}: area {a!r} is not one of the planned example areas in "
                                f"build-principles.json")
                elif a in built:
                    covered = set(built[a].get("demonstrates") or []) | {
                        g.get("address") for g in (built[a].get("not_demonstrated") or [])}
                    if addr not in covered:
                        errs.append(f"{tag}: area {a!r} exists and its cards.json accounts for "
                                    f"neither demonstrating nor gapping card {addr!r}")

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
          f"{len(known_areas)} planned areas of which {len(built)} built, "
          f"{len(known_litmus)} litmus sections, {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
