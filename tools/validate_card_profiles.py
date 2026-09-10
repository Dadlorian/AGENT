#!/usr/bin/env python3
"""Gate for reference-model card profiles: nothing may be asserted.

Every claim-bearing field is either
  origin=sourced   - cites real record ids AND carries a quote that appears verbatim in the
                     SOURCE text of one of them, meaning its `snippet` or `read` field, and
  origin=proposed  - says so in its own text, and cites nothing as evidence.

The rule that does the work is that a record's `claim` field is NOT source text. It is this
repo's own prose about a source. A quote matching it is the repo citing itself, which reads
as evidence and is not. That hole existed in validate_skills.py and let 18 of 946 citations
pass; this checker is written so the same hole cannot open here.

  python3 tools/validate_card_profiles.py           check every profile
  python3 tools/validate_card_profiles.py <path>    check one
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "docs" / "reference" / "cards"
KB = ROOT / "kb"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"

SOURCE_FIELDS = ("snippet", "read")  # deliberately NOT `claim`


def load_source_text() -> dict:
    """id -> the text that actually came off a page or document, never our prose about it."""
    out = {}
    for name in ("research", "facts", "target-facts", "reference-facts", "entities", "edges", "architecture"):
        p = KB / f"{name}.jsonl"
        if not p.is_file():
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if name == "research":
                text = "\n".join(filter(None, (r.get(f) for f in SOURCE_FIELDS)))
            else:
                text = r.get("text") or r.get("name") or ""
            out[r["id"]] = text
    return out


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def check_claim(c: dict, where: str, src: dict, errs: list):
    if not isinstance(c, dict):
        errs.append(f"{where}: not a claim object")
        return
    origin, text = c.get("origin"), c.get("text", "")
    if origin == "proposed":
        if "proposed" not in text.lower() and "our design" not in text.lower():
            errs.append(f"{where}: origin=proposed but the text never says so")
        if c.get("sources") or c.get("quote"):
            errs.append(f"{where}: origin=proposed must not carry sources or a quote")
        return
    if origin != "sourced":
        errs.append(f"{where}: origin must be sourced or proposed, got {origin!r}")
        return
    if c.get("sources") or c.get("quote"):
        errs.append(f"{where}: uses the retired sources/quote shape; a citation is now an "
                    f"{{id, quote}} pair under `evidence`, so no id can ride along unquoted")
        return
    evidence = c.get("evidence") or []
    if not evidence:
        errs.append(f"{where}: origin=sourced with no evidence")
        return
    seen = set()
    for i, e in enumerate(evidence):
        rid, quote = e.get("id"), norm(e.get("quote"))
        at = f"{where}.evidence[{i}]"
        if rid in seen:
            errs.append(f"{at}: cites {rid} twice")
        seen.add(rid)
        if rid not in src:
            errs.append(f"{at}: cites unknown id {rid}")
            continue
        if not quote:
            errs.append(f"{at}: cites {rid} with no quote - an id with no quote is decoration")
            continue
        if quote not in norm(src[rid]):
            errs.append(f"{at}: quote is not verbatim in the SOURCE text of {rid} "
                        f"(a match in that record's own `claim` field does not count)")


def check_profile(path: Path, src: dict, known: set) -> list:
    errs = []
    try:
        p = json.loads(path.read_text())
    except Exception as e:
        return [f"{path.name}: unreadable ({e})"]
    tag = path.name
    if p.get("address") not in known:
        errs.append(f"{tag}: address {p.get('address')!r} is not a card in the reference model")
    for field in ("definition", "landscape", "usage"):
        if field in p:
            check_claim(p[field], f"{tag}.{field}", src, errs)
        else:
            errs.append(f"{tag}: missing {field}")
    for i, s in enumerate(p.get("standards", [])):
        sid = s.get("id")
        if sid and not (ROOT / "standards" / sid / "standard.json").is_file():
            errs.append(f"{tag}.standards[{i}]: no standards/{sid}/standard.json")
        check_claim(s.get("evidence"), f"{tag}.standards[{i}].evidence", src, errs)
    for i, t in enumerate(p.get("tools", [])):
        check_claim(t.get("evidence"), f"{tag}.tools[{i}].evidence", src, errs)
    if not p.get("gaps"):
        errs.append(f"{tag}: gaps is empty - an element with nothing missing is a claim in itself")
    return errs


def main() -> int:
    src = load_source_text()
    model = json.loads(MODEL.read_text())
    known = {f"{a['num'][:-1] if a['num'] else a['region']}.{c['order']}"
             for a in model["areas"] for c in a["cards"]}
    paths = [Path(sys.argv[1])] if len(sys.argv) > 1 else sorted(PROFILES.glob("*.json"))
    if not paths:
        print(f"no profiles under {PROFILES.relative_to(ROOT)}; nothing to check")
        return 0
    errs = []
    for p in paths:
        errs += check_profile(p, src, known)
    for e in errs:
        print(f"error:  {e}")
    print(f"{len(paths)} profiles checked, {len(errs)} errors "
          f"({len(known)} cards in the model, {len(src)} citable records)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
