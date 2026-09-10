#!/usr/bin/env python3
"""Resolve every reference-model card against existing evidence, via the KB index.

  python3 tools/resolve_reference_model.py          report + write coverage json
  python3 tools/resolve_reference_model.py 3.1      explain one card's hits

Each card's name and sub-line are the query. Hits carry real ids, so a mapping can be
cited rather than asserted. Banding is by score, and the score is printed - a weak top
hit is shown as weak, never rounded up into a citation.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb_index  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "docs" / "reference" / "reference-model.json"
OUT = ROOT / "docs" / "reference" / "reference-model-coverage.json"

# a card badge names a standard directory outright - exact, not scored
BADGE = {"ACP": "agent-client-protocol", "AG-UI": "ag-ui", "A2A": "a2a-messaging",
         "MCP": "model-context-protocol", "AGENTS.md": "agents-md"}

COVERED, PARTIAL = 12.0, 6.0
BAND = {"covered": "OK ", "partial": " ~ ", "gap": "  X"}


def band(top):
    return "covered" if top >= COVERED else ("partial" if top >= PARTIAL else "gap")


def address(area, card):
    return f"{area['num'][:-1] if area['num'] else area['region']}.{card['order']}"


def main():
    model = json.loads(MODEL.read_text())
    records = kb_index.load()
    only = sys.argv[1] if len(sys.argv) > 1 else None

    rows, counts = [], {"covered": 0, "partial": 0, "gap": 0}
    ecounts = {"covered": 0, "partial": 0, "gap": 0}
    for area in model["areas"]:
        printed = False
        for card in area["cards"]:
            addr = address(area, card)
            if only and addr != only:
                continue
            query = f"{card['name']} {card['sub']}"
            # two independent questions, deliberately not merged:
            #   design  - is this card connected to what the platform actually models?
            #   evidence - is there sourced research behind it?
            hits = kb_index.score(records, query,
                                  kinds={"skill", "litmus", "standard", "entity", "arch"}, n=5)
            eviq = kb_index.score(records, query, kinds={"research"}, n=3)
            top = hits[0][0] if hits else 0.0
            evi = eviq[0][0] if eviq else 0.0
            b = band(top)
            counts[b] += 1
            ecounts[band(evi)] += 1

            if not printed and not only:
                print(f"\n{area['num'] or ''} {area['title']}")
                printed = True
            evidence = [{"id": r["id"], "kind": r["kind"], "score": s} for s, r in hits[:3]]
            badge = BADGE.get(card.get("standard"))
            if badge:
                evidence.insert(0, {"id": badge, "kind": "standard", "score": "badge"})
            shown = ", ".join(f"{e['id']}" for e in evidence[:2])
            print(f"  {BAND[b]} {addr:8} {card['name']:26} design{top:6.1f}  "
                  f"evidence{evi:6.1f} {BAND[band(evi)].strip() or 'ok':7} {shown}")
            if only:
                for s, r in hits:
                    print(f"        {s:8.2f} {r['kind']:9} {r['id']}\n                 {r['name'][:90]}")
            rows.append({"address": addr, "area": area["key"], "card": card["name"],
                         "status": card["status"], "coverage": b, "top_score": top,
                         "evidence_coverage": band(evi), "evidence_score": evi,
                         "research": [{"id": r["id"], "score": s2} for s2, r in eviq],
                         "evidence": evidence})
    if only:
        return 0
    total = sum(counts.values())
    print(f"\nDESIGN   covered {counts['covered']}, partial {counts['partial']}, gap {counts['gap']}, of {total}")
    print(f"EVIDENCE covered {ecounts['covered']}, partial {ecounts['partial']}, gap {ecounts['gap']}, of {total}")
    OUT.write_text(json.dumps({"bands": {"covered": COVERED, "partial": PARTIAL},
                               "design_counts": counts, "evidence_counts": ecounts,
                               "cards": rows}, indent=2, ensure_ascii=False) + "\n")
    print(f"-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
