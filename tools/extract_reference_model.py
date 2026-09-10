#!/usr/bin/env python3
"""Extract the reference model from ref_arch/Reference Model.dc.html into docs/reference/reference-model.json.

The diagram is an agentic journey: layer order and left-to-right card order carry meaning,
so both are recorded. Read-only against the source; rerun after the .dc.html changes.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "ref_arch" / "Reference Model.dc.html"
OUT = ROOT / "docs" / "reference" / "reference-model.json"

# region and displayed number per area, in reading order. The spine is the journey;
# concerns span it on the left, observe/improve close the loop on the right.
PLACEMENT = {
    "entry":    ("spine", "1."),
    "intake":   ("spine", "2."),
    "agent":    ("spine", "3."),
    "execute":  ("spine", "4."),
    "assure":   ("spine", "5."),
    "observe":  ("loop", "6."),
    "improve":  ("loop", "7."),
    "shared":   ("base", None),
    "concerns": ("rail", None),
}
ORDER = ["entry", "intake", "agent", "execute", "assure", "observe", "improve", "shared", "concerns"]
TITLES = {"concerns": "Cross-Cutting Concerns", "observe": "Observe", "improve": "Self-Improvement"}


def close(text, i, opener, closer):
    """i indexes opener; return index just past its match, ignoring quoted content."""
    depth, j, quote = 0, i, None
    while j < len(text):
        c = text[j]
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return len(text)


def split_args(body):
    out, depth, cur, quote = [], 0, "", None
    for ch in body:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            cur += ch
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def lit(x):
    x = x.strip()
    if x in ("null", "undefined", ""):
        return None
    if x == "true":
        return True
    if x == "false":
        return False
    m = re.match(r"^'(.*)'$", x, re.S)
    if m:
        return m.group(1)
    if re.fullmatch(r"\d+", x):
        return int(x)
    if x.startswith("["):
        return [lit(p) for p in split_args(x[1:-1])]
    return x


def parse_items(blob, misplaced):
    cards = []
    for n, m in enumerate(re.finditer(r"\bitem\(", blob), 1):
        end = close(blob, m.end() - 1, "(", ")")
        a = [lit(x) for x in split_args(blob[m.end():end - 1])] + [None] * 6
        icon, name, sub, std, si, phase = a[:6]
        improvable = si is True
        if isinstance(si, int) and si is not True:  # phase landed in the boolean si slot
            phase = si
            misplaced[name] = si
        cards.append({
            "order": n,
            "name": name,
            "sub": sub,
            "icon": (icon or "").replace("I.", ""),
            "standard": std[1] if isinstance(std, list) and len(std) > 1 else None,
            "status": "built" if (phase or 1) == 1 else "planned",
            "improvable": improvable,
        })
    return cards


def main():
    if not SRC.exists():
        sys.exit(f"missing source: {SRC}")
    script = max(re.findall(r"<script[^>]*>(.*?)</script>", SRC.read_text(), re.S), key=len)

    def array_after(key):
        b = script.index("[", script.find(key))
        return script[b:close(script, b, "[", "]")]

    misplaced = {}
    found = {}

    layers = array_after("layers:")
    for m in re.finditer(r"\{ key: '([a-z]+)'", layers):
        chunk = layers[layers.rindex("{", 0, m.end()):close(layers, layers.rindex("{", 0, m.end()), "{", "}")]
        items = chunk[chunk.index("items:"):]
        items = items[items.index("["):]
        title = re.search(r"title: '([^']+)'", chunk)
        sub = re.search(r"sub: '([^']*)'", chunk)
        found[m.group(1)] = {
            "title": title.group(1) if title else m.group(1),
            "sub": sub.group(1) if sub else "",
            "cards": parse_items(items[:close(items, 0, "[", "]")], misplaced),
        }
    for key in ("concerns", "observe", "improve"):
        found[key] = {"title": TITLES[key], "sub": "",
                      "cards": parse_items(array_after(key + ":"), misplaced)}

    areas = []
    for i, key in enumerate(ORDER, 1):
        if key not in found:
            continue
        region, num = PLACEMENT[key]
        areas.append({"order": i, "key": key, "num": num, "region": region, **found[key]})

    # Evidenced status overrides: cards the diagram calls built where this repo's own
    # evidence says otherwise. Applied here rather than by editing the diagram (which is
    # the owner's statement of intent) or the derived file (which this tool overwrites).
    status_fixes = []
    override_path = ROOT / "docs" / "reference" / "status-corrections.json"
    if override_path.exists():
        by_addr = {c["address"]: c for c in json.loads(override_path.read_text())["corrections"]}
        for area in areas:
            tag = area["num"][:-1] if area["num"] else area["region"]
            for card in area["cards"]:
                fix = by_addr.get(f"{tag}.{card['order']}")
                if not fix:
                    continue
                for field, key in (("status", "status"), ("sub", "sub")):
                    if field in fix and card[key] != fix[field]:
                        status_fixes.append({"card": fix["card"], "address": fix["address"],
                                             "field": key, "was": card[key], "now": fix[field],
                                             "why": fix["why"], "evidence": fix["evidence"]})
                        card[key] = fix[field]

    standards = [{"ref": m.group(1), "name": m.group(2),
                  "maturity": "established" if m.group(3) == "est" else "emerging",
                  "what": m.group(4)}
                 for m in re.finditer(
                     r"\{ n: '(\d)', name: '([^']+)', dot: (\w+), ring: '0', sub: '([^']+)' \}",
                     array_after("standards:"))]

    doc = {
        "generated_from": str(SRC.relative_to(ROOT)),
        "note": "Desired future state. Order is meaningful: areas read in `order`, "
                "cards left to right within an area. Corrections are recorded, not silently applied.",
        "regions": {"spine": "the journey, 1-5", "loop": "closes back onto the spine, 6-7",
                    "rail": "spans every layer", "base": "used by every layer"},
        "areas": areas,
        "standards": standards,
        "corrections": [{"card": k, "was": "rendered built", "now": "planned",
                         "why": f"source passed phase {v} into the boolean si slot, so the phase never applied"}
                        for k, v in sorted(misplaced.items())] + status_fixes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    cards = [c for a in areas for c in a["cards"]]
    print(f"{len(areas)} areas, {len(cards)} cards "
          f"({sum(c['status'] == 'built' for c in cards)} built, "
          f"{sum(c['status'] == 'planned' for c in cards)} planned), "
          f"{len(standards)} standards, {len(misplaced)} corrections -> {OUT.relative_to(ROOT)}")


def check():
    """Verify the extracted JSON accounts for everything in the source. Read-only."""
    script = max(re.findall(r"<script[^>]*>(.*?)</script>", SRC.read_text(), re.S), key=len)
    text = OUT.read_text()
    doc = json.loads(text)
    cards = [c for a in doc["areas"] for c in a["cards"]]
    corrected_subs = {f["now"] for f in doc.get("corrections", []) if f.get("field") == "sub"}
    std_names = {s["name"] for s in doc["standards"]}
    badged = [(c["name"], c["standard"]) for c in cards if c["standard"]]
    corrected = {c["card"] for c in doc["corrections"]}
    want = {f["card"]: f["now"] for f in doc.get("corrections", [])
            if f.get("field", "status") == "status"}

    results = [
        ("every item() captured",
         len(re.findall(r"\bitem\(", script)) == len(cards)),
        ("every area present", len(doc["areas"]) == len(ORDER)),
        ("every name verbatim in source",
         all(f"'{c['name']}'" in script for c in cards)),
        # a corrected sub-line is deliberately not in the source; that is the point of a
        # correction. Exempt exactly the fields a recorded correction changed, no more.
        ("every uncorrected sub verbatim in source",
         all(f"'{c['sub']}'" in script for c in cards
             if c["sub"] and c["sub"] not in corrected_subs)),
        ("every correction names its evidence",
         all(f.get("evidence") and f.get("why") for f in doc.get("corrections", [])
             if "field" in f)),
        ("no empty name or sub", all(c["name"] and c["sub"] for c in cards)),
        ("card order contiguous in every area",
         all([c["order"] for c in a["cards"]] == list(range(1, len(a["cards"]) + 1))
             for a in doc["areas"])),
        ("area order contiguous",
         [a["order"] for a in doc["areas"]] == list(range(1, len(doc["areas"]) + 1))),
        ("spine and loop numbered, rail and base not",
         all((a["num"] is None) == (a["region"] in ("rail", "base")) for a in doc["areas"])),
        ("every card badge resolves", all(s in std_names for _, s in badged)),
        ("every standard used by a card", {s for _, s in badged} == std_names),
        ("status only built or planned",
         {c["status"] for c in cards} <= {"built", "planned"}),
        # a correction may raise a card as well as lower it: evidence promoted 5.1 to built.
        # Assert the card matches what its correction says, not one fixed direction.
        ("every corrected card matches its correction",
         all(c["status"] == want.get(c["name"], c["status"]) for c in cards)),
        ("no escaped unicode", "\\u" not in text),
    ]
    for label, passed in results:
        print(f"  {'PASS' if passed else 'FAIL'}  {label}")
    failed = sum(not p for _, p in results)
    print(f"{len(results) - failed} of {len(results)} checks hold, {len(cards)} cards accounted for")
    return 1 if failed else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    main()
