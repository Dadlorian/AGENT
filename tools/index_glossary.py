#!/usr/bin/env python3
"""The ref_arch control-plane glossary, addressed by reference-model card.

`ref_arch/cellplane-glossary.js` is the glossary of record for the designed control plane: 90
terms, each carrying the standard that governs it, that standard's own word where it differs,
and the API field name. Its layers are the reference model's own areas, so it is already
addressed at the architecture rather than needing to be mapped onto it later.

WHAT IT IS WORTH, AND WHAT IT IS NOT
------------------------------------
It is NOT another source pool. `tools/index_sources.py` offers URLs nobody has opened; most of
this glossary's standards already have a `standards/<id>/` directory here, so those entries are
a CROSS-CHECK against material the repo already holds, needing no fetch.

What is genuinely new is narrower than "90 terms" and more useful: the glossary binds a specific
CLAUSE to a specific entity -- `RFC 8693 'act' claim`, `A2A input-required`, `ACP cwd`,
`OTel gen_ai.evaluation.*` -- where a card profile today binds a whole standard to a whole card.
And it carries the API field name (`act[]`, `rrule`, `acceptance_criteria[]`, `Idempotency-Key`),
which is the `usage` field's missing content.

NOTHING HERE IS EVIDENCE
------------------------
The glossary's `std` values are pointers a design session wrote, and
`ref_arch/uploads/glossary_consensus.json` backs them with `evidence` arrays that are source
NAMES -- "CNCF Cloud Native Glossary: Multitenancy", "OIDC; OpenAPI; Auth0 API" -- with no URL,
no quote and no fetch, proposed by three models voting. Under this repo's rules they enter
exactly like anything else: capture -> record -> `stamp_verification.py --fetch` -> cite. A term
appearing here is a reason to go and check a standard, never a citation.

SIX TERMS PUT A VOTE WHERE A STANDARD GOES
------------------------------------------
`Cost estimate -> Consensus 2/3` and `Raise ceiling -> Consensus 2/3` record HOW THE NAME WAS
CHOSEN in the field that is supposed to say WHAT GOVERNS THE ENTITY. That is the same shape as a
record's `read` being structurally a second `claim`: a provenance label reads as a standard and
is not one. They are flagged `vote` below so no card is profiled off them.

  python3 tools/index_glossary.py <card>       terms whose layer is that card's area
  python3 tools/index_glossary.py --coverage   terms available per card, zeros included
  python3 tools/index_glossary.py --json       machine-readable
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "ref_arch" / "cellplane-glossary.js"
STANDARDS = ROOT / "standards"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"

# The glossary's own layer ids against the reference model's area ids. `tenancy` and `api` are
# deliberately mapped to nothing: they are cross-cutting in the control plane's own framing and
# the glossary never claims they are `rail`, so asserting that here would be this tool inventing
# an alignment. `base` has NO layer at all -- that absence is the finding, not an oversight.
LAYER_TO_AREA = {
    "entry": "1", "control": "2", "agent": "3", "runtime": "4",
    "assure": "5", "observe": "6", "improve": "7",
    "tenancy": None, "api": None,
}

# A `std` value that records how a name was chosen, not what governs the entity.
# Three different things live in the `std` field and must not be graded as one.
# `ours` is an honest "this is our design" -- the same declaration as origin=proposed, and not a
# defect. A CONSENSUS or "your pick" label records how the NAME was chosen and says nothing about
# what governs the entity; that is the defect. A bare "convention" is neither: real practice, but
# nothing citable to point at.
VOTE = re.compile(r"consensus|your pick", re.I)
OURS = re.compile(r"^ours\b", re.I)
CONVENTION = re.compile(r"convention|^best practice$", re.I)

# Where the glossary's wording and this repo's directory name differ. Only genuine renames --
# never a guess that two different standards are the same one.
ALIAS = {
    "rfc-8693": "oauth-2-0-token-exchange",
    "spiffe-svid": "workload-identity",
    "rfc-5545-rrule": "rfc-5545-recurrence-rules",
    "cloudevents-1-0": "cloudevents",
    "acp": "agent-client-protocol",
    "mcp": "model-context-protocol",
    "oci-container": "oci-image-spec",
    "otel-gen-ai-evaluation": "genai-semantic-conventions",
    "rfc-9457-problem-details": "rfc-9457-problem-details",
}
# A clause-level pointer resolves to the standard it is a clause OF.
FAMILY = [
    (re.compile(r"^rfc\s*8693", re.I), "oauth-2-0-token-exchange"),
    (re.compile(r"^a2a\b", re.I), "a2a-messaging"),
    (re.compile(r"^acp\b", re.I), "agent-client-protocol"),
    (re.compile(r"^agents\.md", re.I), "agents-md"),
    (re.compile(r"^oci runtime", re.I), "oci-runtime-spec"),
    (re.compile(r"^in-toto", re.I), "in-toto"),
    (re.compile(r"^otel gen_?ai|^otel genai", re.I), "genai-semantic-conventions"),
    (re.compile(r"^cloudevents", re.I), "cloudevents"),
    (re.compile(r"^json schema", re.I), "json-schema-2020-12"),
]


def parse_glossary() -> list:
    """Read the `T(layer, term, def, std, map, field, used)` rows out of the JS source.

    Splitting is quote-aware because several definitions contain an escaped apostrophe, and a
    naive `split(',')` silently truncates them.
    """
    if not GLOSSARY.is_file():
        return []
    src = GLOSSARY.read_text()
    out = []
    for raw in re.findall(r"T\((.*?)\),\n", src, re.S):
        args, cur, in_q, esc = [], "", False, False
        for ch in raw:
            if esc:
                cur += ch
                esc = False
            elif ch == "\\":
                cur += ch
                esc = True
            elif ch == "'":
                in_q = not in_q
                cur += ch
            elif ch == "," and not in_q:
                args.append(cur.strip())
                cur = ""
            else:
                cur += ch
        args.append(cur.strip())
        args = [a.strip().strip("'").replace("\\'", "'") for a in args]
        if len(args) >= 4:
            args += [""] * (7 - len(args))
            out.append(dict(zip(("layer", "term", "definition", "std", "map", "field", "used"),
                                args[:7])))
    return out


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"[`'\"]", "", text.lower())).strip("-")


def classify(std: str, have: set) -> list:
    """One `std` value into its parts, each typed and resolved to a standards/ directory.

    Split on the glossary's own separator only. An earlier pass also split on `/` and turned
    `ISO/IEC/IEEE 29148` into three bogus standards -- a reminder that a separator is part of a
    source's meaning, not punctuation to be normalised away.
    """
    parts = []
    for chunk in std.split("·"):
        name = chunk.strip()
        if not name:
            continue
        if OURS.search(name):
            kind = "ours"
        elif VOTE.search(name):
            kind = "vote"
        elif CONVENTION.search(name):
            kind = "convention"
        else:
            kind = "standard"
        directory = None
        if kind == "standard":
            s = ALIAS.get(slug(name), slug(name))
            if s in have:
                directory = s
            else:
                for pattern, fam in FAMILY:
                    if pattern.search(name) and fam in have:
                        directory = fam
                        break
        parts.append({"name": name, "kind": kind, "standard_dir": directory})
    return parts


def cards() -> list:
    model = json.loads(MODEL.read_text())
    out = []
    for area in model["areas"]:
        num = area["num"][:-1] if area["num"] else area["region"]
        for card in area["cards"]:
            out.append({"address": f"{num}.{card['order']}", "area": num,
                        "name": card.get("name", ""), "status": card.get("status", "")})
    return out


def terms_for(area: str, terms: list, have: set) -> list:
    out = []
    for t in terms:
        if LAYER_TO_AREA.get(t["layer"]) != area:
            continue
        e = dict(t)
        e["std_parts"] = classify(t["std"], have)
        out.append(e)
    return out


def main() -> int:
    argv = sys.argv[1:]
    if not GLOSSARY.is_file():
        print(f"{GLOSSARY.relative_to(ROOT)} not found - the ref_arch design set is not present.")
        return 1
    terms = parse_glossary()
    have = {d.name for d in STANDARDS.iterdir() if d.is_dir()} if STANDARDS.is_dir() else set()
    all_cards = cards()

    if "--json" in argv:
        print(json.dumps({c["address"]: terms_for(c["area"], terms, have) for c in all_cards},
                         indent=2))
        return 0

    if "--coverage" in argv:
        by_area = {}
        for t in terms:
            by_area.setdefault(LAYER_TO_AREA.get(t["layer"]), []).append(t)
        print(f"{len(terms)} glossary terms, {len(LAYER_TO_AREA)} layers, "
              f"{len(all_cards)} cards in the model\n")
        print(f"  {'card':10} {'name':30} {'status':8} terms  standards-with-a-dir")
        zero = []
        for c in all_cards:
            ts = by_area.get(c["area"], [])
            dirs = {p["standard_dir"] for t in ts for p in classify(t["std"], have)
                    if p["standard_dir"]}
            if not ts:
                zero.append(c["address"])
            print(f"  {c['address']:10} {c['name'][:30]:30} {c['status']:8} "
                  f"{len(ts):5}  {len(dirs)}")
        unmapped = [l for l, a in LAYER_TO_AREA.items() if a is None]
        print(f"\n{len(zero)} card(s) the glossary does not reach: {', '.join(zero)}")
        print(f"layers mapped to no area: {', '.join(unmapped)} "
              f"({sum(1 for t in terms if LAYER_TO_AREA.get(t['layer']) is None)} terms). "
              f"The glossary has no `base` layer at all.")
        # Graded by kind. A term whose `std` is ONLY a vote label has nothing governing it and
        # cannot be profiled from; a term that names a real standard AND carries a vote label is
        # perfectly usable, the label is just noise beside it. Reported as one number those are
        # 37 defects; graded, they are 6.
        parts = {t["term"]: classify(t["std"], have) for t in terms}
        only_vote = [t for t, ps in parts.items()
                     if ps and all(p["kind"] == "vote" for p in ps)]
        ours = [t for t, ps in parts.items() if ps and all(p["kind"] == "ours" for p in ps)]
        mixed = [t for t, ps in parts.items()
                 if any(p["kind"] == "vote" for p in ps) and t not in only_vote]
        print(f"{len(only_vote)} term(s) whose governing field holds ONLY a vote - nothing governs "
              f"them, do not profile a card from these: {', '.join(sorted(only_vote))}")
        print(f"{len(mixed)} more carry a vote label beside a real standard - the standard is "
              f"usable, the label is not a source")
        print(f"{len(ours)} term(s) declare themselves this design's own (`ours`) - honest, and "
              f"the direct equivalent of origin=proposed; not a defect")
        print("\nNothing here is evidence. capture -> record -> stamp_verification.py --fetch -> cite.")
        return 0

    target = next((a for a in argv if not a.startswith("--")), None)
    if not target:
        print(__doc__.strip().splitlines()[0])
        print("\n  python3 tools/index_glossary.py <card>       e.g. 1.5, 4.1, base.1")
        print("  python3 tools/index_glossary.py --coverage")
        return 1
    card = next((c for c in all_cards if c["address"] == target), None)
    if not card:
        print(f"{target!r} is not a card in the reference model")
        return 1
    rows = terms_for(card["area"], terms, have)
    print(f"card {card['address']} - {card['name']} ({card['status']}), area {card['area']}")
    if not rows:
        print(f"\nThe glossary has no layer for area {card['area']}. This card gets nothing from "
              f"it; use tools/index_sources.py for candidate pages instead.")
        return 0
    print(f"{len(rows)} term(s) in this card's area. The glossary binds terms to an AREA, not to "
          f"a card, so these are candidates for every card in area {card['area']}.\n")
    for t in rows:
        print(f"  {t['term']}")
        print(f"     {t['definition'][:150]}")
        for p in t["std_parts"]:
            where = (f"standards/{p['standard_dir']}" if p["standard_dir"]
                     else ("NO standards/ dir" if p["kind"] == "standard" else ""))
            mark = {"vote": "VOTE on the name - says nothing about what governs this; do not cite",
                    "ours": "this design's own, equivalent to origin=proposed",
                    "convention": "convention, not a standard"}.get(p["kind"], "")
            print(f"     std: {p['name']:46} {where} {mark}".rstrip())
        if t["map"]:
            print(f"     the standard's own word: {t['map']}")
        if t["field"]:
            print(f"     API field: {t['field']}")
    print("\nNothing here is evidence. capture -> record -> stamp_verification.py --fetch -> cite.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
