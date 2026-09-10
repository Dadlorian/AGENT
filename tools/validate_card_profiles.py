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
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "docs" / "reference" / "cards"
KB = ROOT / "kb"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"
DEBT = ROOT / "docs" / "reference" / "citation-debt.json"

SOURCE_FIELDS = ("snippet", "read")  # deliberately NOT `claim`


def load_debt() -> dict:
    """Citations that predate the `citable means verified` rule, enumerated once by a human-run
    pass so the rule can block NEW defects without the repo going red on old ones.

    This is the repo's existing idiom (`known_red` in phase.py, `status-corrections.json`) and it
    carries the same danger: an exemption list that grows quietly stops being debt and becomes
    permission. Nothing writes to this file automatically, every entry names why, and the count is
    printed on every run so it cannot go unnoticed.
    """
    if not DEBT.is_file():
        return {}
    return {(e["profile"], e["json_path"], e["quote_sha256"]): e["why"]
            for e in json.loads(DEBT.read_text()).get("entries", [])}


def load_verification() -> dict:
    """id -> {field: was_that_field_verified_against_the_page}, from the record's own stamp.

    Written only by tools/stamp_verification.py from a real fetch. The per-field shape is the
    load-bearing part: a record can carry a genuine `snippet` and a fabricated `read`, and the
    quote rule below accepts a quote from either -- so without this, an invented `read`
    launders an invented quote past every checker. Twice on 2026-09-10 a repair agent did
    exactly that to its own output, caught by review and not by tooling.
    """
    out = {}
    for line in (KB / "research.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        v = r.get("verification")
        if not v:
            continue
        out[r["id"]] = {
            "quotes": set(v.get("verified_quotes") or ()),
            "verdicts": dict(v.get("quote_verdicts") or {}),
            "unreachable": bool(v.get("unreachable")),
            "reason": v.get("reason"),
        }
    return out


def load_field_text() -> dict:
    """id -> {field: text} for research records, so a quote can be attributed to the field it
    actually came from rather than to a flattened blob."""
    out = {}
    p = KB / "research.jsonl"
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        out[r["id"]] = {f: r.get(f) or "" for f in SOURCE_FIELDS}
    return out


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


DEBT_INDEX: dict = {}


def tag_of(at: str) -> str:
    return at.split(".", 1)[0] + ".json" if not at.split(".", 1)[0].endswith(".json") else at.split(".", 1)[0]


def path_of(at: str) -> str:
    """`3-5.json.landscape.evidence[1]` -> `$.landscape.evidence[1]`, matching citation-debt.json."""
    rest = at.split(".json.", 1)[1] if ".json." in at else at
    return "$." + rest


def check_quote_is_verified(rid, quote, at, fields, stamps, errs, exempt):
    """A quote is valid only if it lives in a field this record's stamp marks verbatim.

    This is what makes `citable` mean `checked`. Before it, nothing connected the two: a
    record whose page nobody had ever opened was exactly as citable as one read line by line,
    which is how 45 of 46 profile-cited records came to fail verification.
    """
    if not rid.startswith("X-"):
        return                      # F-/T-/REF-/A-/E- are this repo's own documents, not pages
    stamp = stamps.get(rid)
    if stamp is None:
        errs.append(f"{at}: cites {rid}, which carries no verification stamp - run "
                    f"tools/stamp_verification.py; an unchecked page is not evidence")
        return
    if stamp["unreachable"]:
        exempt.append((at, rid, stamp.get("reason") or "unreachable"))
        return
    qh = hashlib.sha256(quote.encode()).hexdigest()
    verdict = stamp["verdicts"].get(qh)
    # Act on WHAT KIND of difference this is. A bare true/false is what let a flattened bullet list
    # and an invented statistic be reported with the same word.
    if verdict in ("exact", "formatting"):
        return
    if verdict == "unretrievable":
        exempt.append((at, rid, "page could not be read; nothing proven either way"))
        return
    if verdict in ("stitched", "partial", "absent"):
        key = (tag_of(at), path_of(at), qh)
        if key in DEBT_INDEX:
            exempt.append((at, rid, f"{verdict}, recorded: " + DEBT_INDEX[key]))
            return
        why = {"stitched": "this quote is two non-adjacent passages joined into one sentence - the "
                           "page never says it as a single statement",
               "partial": "part of this quote is on the page and part is not - a person has to read "
                          "it and decide; no check can tell a faithful paraphrase from an invented one",
               "absent": "the page does not contain this quote, or anything close to it"}[verdict]
        errs.append(f"{at}: {rid} quote verdict `{verdict}` - {why}")
        return
    if qh not in stamp["quotes"]:
        key = (tag_of(at), path_of(at), qh)
        if key in DEBT_INDEX:
            exempt.append((at, rid, "recorded debt: " + DEBT_INDEX[key]))
            return
        errs.append(f"{at}: this exact quote was NOT found on {rid}'s page when it was last "
                    f"fetched - the record may carry it, but the page does not. Re-source it, "
                    f"or re-run tools/stamp_verification.py --fetch if the quote just changed")


def check_claim(c: dict, where: str, src: dict, errs: list, fields=None, stamps=None, exempt=None):
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
            continue
        if stamps is not None:
            check_quote_is_verified(rid, quote, at, fields, stamps, errs, exempt)


def check_profile(path: Path, src: dict, known: set, fields=None, stamps=None, exempt=None) -> list:
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
            check_claim(p[field], f"{tag}.{field}", src, errs, fields, stamps, exempt)
        else:
            errs.append(f"{tag}: missing {field}")
    for i, s in enumerate(p.get("standards", [])):
        sid = s.get("id")
        if sid and not (ROOT / "standards" / sid / "standard.json").is_file():
            errs.append(f"{tag}.standards[{i}]: no standards/{sid}/standard.json")
        check_claim(s.get("evidence"), f"{tag}.standards[{i}].evidence", src, errs, fields, stamps, exempt)
    for i, t in enumerate(p.get("tools", [])):
        check_claim(t.get("evidence"), f"{tag}.tools[{i}].evidence", src, errs, fields, stamps, exempt)
    if not p.get("gaps"):
        errs.append(f"{tag}: gaps is empty - an element with nothing missing is a claim in itself")
    return errs


def main() -> int:
    global DEBT_INDEX
    DEBT_INDEX = load_debt()
    src, fields, stamps, exempt = load_source_text(), load_field_text(), load_verification(), []
    model = json.loads(MODEL.read_text())
    known = {f"{a['num'][:-1] if a['num'] else a['region']}.{c['order']}"
             for a in model["areas"] for c in a["cards"]}
    paths = [Path(sys.argv[1])] if len(sys.argv) > 1 else sorted(PROFILES.glob("*.json"))
    if not paths:
        print(f"no profiles under {PROFILES.relative_to(ROOT)}; nothing to check")
        return 0
    errs = []
    for p in paths:
        errs += check_profile(p, src, known, fields, stamps, exempt)
    for e in errs:
        print(f"error:  {e}")
    if exempt:
        print(f"note:   {len(exempt)} citation(s) rest on pages that could not be retrieved. "
              f"Recorded, not defects - nothing is proven either way:")
        for at, rid, why in sorted(exempt)[:12]:
            print(f"          {rid:34} {why[:70]}")
        if len(exempt) > 12:
            print(f"          ... and {len(exempt) - 12} more")
    print(f"{len(paths)} profiles checked, {len(errs)} errors "
          f"({len(known)} cards in the model, {len(src)} citable records, "
          f"{len(stamps)} verification-stamped, {len(exempt)} exempt of which "
          f"{len(DEBT_INDEX)} are recorded debt in docs/reference/citation-debt.json)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
