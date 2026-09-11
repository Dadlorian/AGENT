#!/usr/bin/env python3
"""Gate for the PROSE around a citation, which nothing else in this repo reads.

`validate_card_profiles.py` checks that every `evidence[].quote` is verbatim on its page. It
never reads the prose that surrounds the quote -- `text`, `role`, `covers`, `note`, and the
`gaps[]` fields. So a figure or a quotation sitting in that prose with no quote attached passes
every check in the repo. That is how "$47,000 / 264-hour", "28.7x-35.2x" and a Firecracker
"5-30ms" resume time survived; each was caught by a person reading, three times in one day, and
never by a tool.

This closes that hole for `docs/reference/cards/`. It does NOT cover the other corpora that
carry the same defect class -- `.claude/skills/*/skill.json`, `docs/maturity/parts/*.json`,
`docs/consumption/unit-design.json`. `--corpus` takes a directory so they can be added; silence
here is not coverage.

WHAT IT DOES NOT DO, on purpose
-------------------------------
It cannot tell a faithful paraphrase from an invented one, and it does not try. It answers one
narrower question: is this quoted span, or this number, present in the source text of the
records the enclosing claim actually cites? Matching proposes; only a reader decides.

VERDICTS ARE TYPED, NEVER BOOLEAN
---------------------------------
The repo learned this the expensive way: a bare pass/fail scored a lowercased first letter and
an invented statistic identically, and the difference got supplied from imagination. The same
six verdicts `stamp_verification.py` uses for quotes are used here for prose:

  exact       present verbatim in the cited source text
  formatting  present but for case, punctuation, dashes or list flattening -- a real match
  partial     a long prefix matches and the tail does not; a person has to read it
  stitched    two non-adjacent passages joined, usually by an author-inserted ellipsis
  elsewhere   verbatim somewhere in the KB but NOT in what this claim cites -- mis-attribution
  absent      nothing close to it anywhere in the knowledge base

WHAT BLOCKS
-----------
Only `stitched`, `elsewhere` and `absent`, and only inside the `text` of an `origin: sourced`
claim. That scope is structural, not a tuning knob: a sourced claim's whole contract is "this
prose is backed by these records", so its prose must trace to them. `gaps[]` carries no
`evidence` field in the schema -- it is uncitable by construction, and its numbers are this
repo's own measurements -- so findings there are reported and never block. Blocking on prose
that has no evidence to trace to would turn this gate into an exemption-list farm, which is the
failure mode `citation-debt.json` already demonstrates.

  python3 tools/prose_gate.py                 check every card profile
  python3 tools/prose_gate.py <path>          check one
  python3 tools/prose_gate.py --all           report non-blocking findings too
  python3 tools/prose_gate.py --json          machine-readable
  python3 tools/prose_gate.py --selftest      plant a fabricated figure, prove the gate sees it
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "docs" / "reference" / "cards"
KB = ROOT / "kb"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"

SOURCE_FIELDS = ("snippet", "read")   # deliberately NOT `claim` -- that is our prose about a source
# `research_query` is deliberately absent: it holds a search string or a literal
# `kb_index.py search "..."` command, so its quoted spans are query terms, not citations.
PROSE_FIELDS = ("role", "covers", "note", "what", "why_it_matters")
MIN_QUOTE_WORDS = 6                   # below this a quoted span is a term or scare quote, not a citation
BLOCKING = ("stitched", "elsewhere", "absent")


# ----------------------------------------------------------------- source text

def load_source_text() -> dict:
    """id -> the text that actually came off a page or document, never our prose about it.

    Same rule as validate_card_profiles.py: a research record's source text is its `snippet` or
    `read`. A quote matching the record's own `claim` field is this repo citing itself.
    """
    out = {}
    for name in ("research", "facts", "target-facts", "reference-facts",
                 "entities", "edges", "architecture", "decisions"):
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
    out.update(model_rows())
    return out


def model_rows() -> dict:
    """The reference model's own card rows, as citable internal source text.

    A card profile quoting its own name or subtitle -- card 7.2 opens "This card's own subtitle
    -- ..." -- is quoting `docs/reference/reference-model.json`, which is a document of this repo
    exactly as `F-`/`T-`/`REF-` records are. Without it the gate reads a correct self-reference as
    a fabrication. The `MODEL:` prefix keeps it visibly internal: it is evidence of what this
    model says, never evidence of industry practice.
    """
    out = {}
    model = json.loads(MODEL.read_text())
    for area in model["areas"]:
        num = area["num"][:-1] if area["num"] else area["region"]
        for card in area["cards"]:
            out[f"MODEL:{num}.{card['order']}"] = " ".join(
                filter(None, (card.get("name"), card.get("sub"))))
    return out


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def loose(s: str) -> str:
    """Normalisation that survives the differences that are NOT defects.

    A page rendered through the markdown rung and the same page rendered through html_to_text
    differ in exactly these ways -- case, smart quotes, em/en dashes, the `*` and `|` of a
    flattened table, a trailing period. `tools/verify_snippets.py` and `tools/capture.py` are
    documented as returning different text for the same URL (BRIEF.md), so treating any of this
    as evidence of fabrication would manufacture defects out of a fetcher choice.
    """
    s = unicodedata.normalize("NFKD", s or "").lower()
    for a, b in (("—", "-"), ("–", "-"), ("’", "'"),
                 ("“", '"'), ("”", '"'), ("·", " ")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ----------------------------------------------------------------- detectors

QUOTE_RE = re.compile(r'"([^"]+)"')
ELLIPSIS_RE = re.compile(r"\s*(?:\.\.\.|…|\[\.\.\.\])\s*")

# A quantity a reader would take as a measured fact. The lookbehind deliberately does NOT exclude
# a preceding hyphen: "28.7x-35.2x" is one range and both halves must be seen. An earlier draft of
# this detector excluded them and could not see half of the very figure this gate exists for.
FIGURE_RE = re.compile(
    r"(?<![\w.$])("
    r"\$\s?[\d,]+(?:\.\d+)?"                                                  # $47,000
    r"|[\d,]+(?:\.\d+)?\s*[-\u2013]\s*[\d,]+(?:\.\d+)?\s?(?:x|%|ms|\u00b5s|ns|KB|MB|GB|TB)\b"   # 5-30ms as one range
    r"|[\d,]+(?:\.\d+)?\s?(?:x|%|ms|\u00b5s|ns|KB|MB|GB|TB)\b"                # 28.7x, 67KB
    r"|[\d,]+(?:\.\d+)?[-–]?\s?(?:hour|minute|second|day|week|month|year)s?\b"
    r"|\d[\d,]*\.\d+"                                                         # 0.88
    r"|\d{1,3}(?:,\d{3})+"                                                    # 44,000
    r")")

UNIT_FAMILY = {"hour": "hour", "hours": "hour", "minute": "minute", "minutes": "minute",
               "second": "second", "seconds": "second", "day": "day", "days": "day",
               "week": "week", "weeks": "week", "month": "month", "months": "month",
               "year": "year", "years": "year"}


def card_addresses() -> set:
    model = json.loads(MODEL.read_text())
    return {f"{a['num'][:-1] if a['num'] else a['region']}.{c['order']}"
            for a in model["areas"] for c in a["cards"]}


def structural(token: str, context: str, addresses: set) -> str | None:
    """Numbers that are addresses, identifiers or versions -- not measurements.

    112 of the 160 numbers in these profiles are card addresses (`3.3`, `rail.5`). Reporting
    those as unsourced figures is how a detector produces a flood that gets ignored, and an
    ignored gate is worse than none.
    """
    t = token.strip()
    if t in addresses:
        return "card address"
    if re.fullmatch(r"\d{4}\.\d{4,5}", t):
        return "arXiv id"
    if re.fullmatch(r"10\.\d{4,9}", t) and "/" in context:
        return "DOI"   # the real DOI shape only -- `t.startswith("10.")` also ate 10.5x
    if re.fullmatch(r"(19|20)\d{2}", t):
        return "year"
    if re.fullmatch(r"\d+\.\d+(?:\.\d+)*", t) and re.search(
            r"(?:v|version\s+|RFC\s*|draft[- ])" + re.escape(t), context, re.I):
        return "version"
    if re.search(r"(?:STATUS |row |rows )" + re.escape(t) + r"\b", context, re.I):
        return "STATUS row"
    return None


def figure_verdict(token: str, pool_n: str, pool_l: str, all_n: str, all_l: str) -> str:
    """Type one quantity against the cited source text.

    `formatting` is load-bearing here. Card rail-3 says "Stripe stores idempotency keys for 24
    hours" and its cited record says "within a 24-hour window". The number and its unit are both
    on the page; only the rendering differs. A literal-substring test calls that a fabrication,
    which is precisely the overreach this repo keeps catching in itself.
    """
    t = norm(token)
    if t in pool_n:
        return "exact"
    tl = loose(token)
    if tl and tl in pool_l:
        return "formatting"
    m = re.match(r"([\d,]+(?:\.\d+)?)\s*[-–]?\s*([a-z%$]*)", tl)
    if m:
        value, unit = m.group(1), UNIT_FAMILY.get(m.group(2), m.group(2))
        if unit and re.search(re.escape(value) + r"\s*[-–]?\s*" + re.escape(unit), pool_l):
            return "formatting"
        if not unit and re.search(r"(?<![\d.])" + re.escape(value) + r"(?![\d.])", pool_l):
            return "formatting"
    if tl and tl in all_l:
        return "elsewhere"
    return "absent"


MAX_ELISION = 200          # characters an author may elide inside one sentence
SENTENCE_END = re.compile(r"[.!?]\s")


def elided_or_stitched(quote: str, pool_n: str, pool_l: str, all_l: str) -> str | None:
    """An author-inserted ellipsis is two different things, and the difference is the finding.

    An ELISION drops a parenthetical from inside one sentence -- the page does say it as a single
    statement, so the quote is faithful:
        source  ...insert in Milvus [7] (with separate upsert for updates) and add or upsert...
        prose   ...insert in Milvus [7] ... and add or upsert...
    A STITCH joins passages across sentence boundaries into a statement the page never makes.

    Presence alone types both identically, which is the "graded by kind it was one" mistake
    bridge.md records. So measure the gap in the source between consecutive parts: short, and
    crossing no sentence boundary, is an elision.
    """
    parts = [p for p in ELLIPSIS_RE.split(quote) if len(p.split()) >= 3]
    if not parts:
        return None
    hay = pool_n.lower()
    spans, cursor = [], 0
    for part in parts:
        needle = norm(part).lower()
        i = hay.find(needle, cursor)
        if i < 0:
            spans = []
            break
        spans.append((i, i + len(needle)))
        cursor = i + len(needle)
    if len(spans) == len(parts):
        for (_, end), (start, _) in zip(spans, spans[1:]):
            gap = pool_n[end:start]
            if len(gap) > MAX_ELISION or SENTENCE_END.search(gap):
                return "stitched"
        return "formatting"
    if all(loose(p) in pool_l or loose(p) in all_l for p in parts):
        return "stitched"
    return None


def quote_verdict(quote: str, pool_n: str, pool_l: str, all_n: str, all_l: str) -> str:
    """Type one quoted span against the cited source text."""
    qn = norm(quote)
    if qn in pool_n:
        return "exact"
    ql = loose(quote)
    if not ql:
        return "exact"
    if ql in pool_l:
        return "formatting"
    if ELLIPSIS_RE.search(quote):
        v = elided_or_stitched(quote, pool_n, pool_l, all_l)
        if v:
            return v
    step = max(1, len(ql) // 25)
    for L in range(len(ql), 15, -step):
        if ql[:L] in pool_l:
            return "partial" if L / len(ql) >= 0.55 else ("elsewhere" if ql in all_l else "absent")
    if ql in all_l:
        return "elsewhere"
    return "absent"


# ----------------------------------------------------------------- the walk

def prose_sites(profile: dict, tag: str) -> list:
    """Every prose string, paired with the evidence it is answerable to.

    `binding` is what decides whether a finding blocks:
      cited     the `text` of an origin=sourced claim -- its contract is that these records back it
      declared  the `text` of an origin=proposed claim -- says it is our reasoning, cites nothing
      sibling   role/covers/note, answerable to the evidence of the entry they sit in
      uncitable gaps[] -- the schema gives it no evidence field at all
    """
    sites = []

    def walk(node, path, inherited):
        if isinstance(node, dict):
            origin = None
            if "origin" in node and "text" in node:
                origin = node.get("origin")
                inherited = [e.get("id") for e in (node.get("evidence") or [])
                             if isinstance(e, dict)]
                sites.append({"at": f"{path}.text", "text": node["text"], "ids": inherited,
                              "binding": "cited" if origin == "sourced" else "declared"})
            for k, v in node.items():
                if k == "text" and origin:
                    continue
                if isinstance(v, str) and k in PROSE_FIELDS:
                    ev = node.get("evidence")
                    sib = ([e.get("id") for e in (ev.get("evidence") or []) if isinstance(e, dict)]
                           if isinstance(ev, dict) else inherited)
                    sites.append({"at": f"{path}.{k}", "text": v, "ids": sib,
                                  "binding": "uncitable" if ".gaps[" in f"{path}.{k}" else "sibling"})
                else:
                    walk(v, f"{path}.{k}", inherited)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]", inherited)

    walk(profile, tag, [])
    return sites


def check_profile(path: Path, src: dict, all_n: str, all_l: str, addresses: set) -> list:
    try:
        profile = json.loads(path.read_text())
    except Exception as e:
        return [{"at": path.name, "kind": "unreadable", "verdict": "absent",
                 "binding": "cited", "what": str(e)}]
    findings = []
    # Its OWN model row only. Card 3.5 quoting card 7.2's subtitle is still an attribution to
    # something it does not cite, and must still flag.
    own = [f"MODEL:{profile.get('address')}"]
    for site in prose_sites(profile, path.name):
        pooled = " || ".join(src.get(i, "") for i in site["ids"] + own)
        pool_n, pool_l = norm(pooled), loose(pooled)
        for span in QUOTE_RE.findall(site["text"]):
            if len(span.split()) < MIN_QUOTE_WORDS:
                continue
            v = quote_verdict(span, pool_n, pool_l, all_n, all_l)
            findings.append({"at": site["at"], "kind": "quote", "verdict": v,
                             "binding": site["binding"], "what": norm(span)[:160],
                             "cites": site["ids"]})
        for tok in FIGURE_RE.findall(site["text"]):
            why = structural(tok, site["text"], addresses)
            if why:
                continue
            v = figure_verdict(tok, pool_n, pool_l, all_n, all_l)
            findings.append({"at": site["at"], "kind": "figure", "verdict": v,
                             "binding": site["binding"], "what": norm(tok),
                             "cites": site["ids"]})
    return findings


WHY = {
    "stitched": "two non-adjacent passages joined into one span; the source never says it as a "
                "single statement",
    "elsewhere": "present in the knowledge base but NOT in any record this claim cites - it is "
                 "attributed to the wrong source",
    "absent":    "not in the cited source text, and nothing close to it anywhere in the "
                 "knowledge base",
    "partial":   "part of it is in the cited source and part is not; no string test separates a "
                 "faithful paraphrase from an invented one - a person has to read it",
}


def report(findings: list, show_all: bool) -> int:
    blocking = [f for f in findings if f["binding"] == "cited" and f["verdict"] in BLOCKING]
    human = [f for f in findings if f["binding"] == "cited" and f["verdict"] == "partial"]
    counts = {}
    for f in findings:
        counts.setdefault(f["kind"], {}).setdefault(f["verdict"], 0)
        counts[f["kind"]][f["verdict"]] += 1

    for f in sorted(blocking, key=lambda f: f["at"]):
        print(f"error:  {f['at']}  {f['kind']} `{f['verdict']}` - {WHY[f['verdict']]}")
        print(f"          {f['what']}")
        print(f"          claim cites: {', '.join(f['cites']) or '(nothing)'}")
    for f in sorted(human, key=lambda f: f["at"]):
        print(f"reader: {f['at']}  {f['kind']} `partial` - {WHY['partial']}")
        print(f"          {f['what']}")

    if show_all:
        other = [f for f in findings
                 if f["binding"] != "cited" and f["verdict"] in BLOCKING + ("partial",)]
        if other:
            print(f"\nnote:   {len(other)} finding(s) in prose that carries no evidence to trace "
                  f"to - reported, never blocking:")
            for f in sorted(other, key=lambda f: f["at"]):
                print(f"          [{f['binding']:9}] {f['at']:48} {f['kind']} "
                      f"`{f['verdict']}`  {f['what'][:60]}")

    # Report the number that needs a person, with its denominator and the full distribution.
    # A share reported first has been read as "we have evidence" every time it was tried here.
    print()
    for kind in ("quote", "figure"):
        c = counts.get(kind, {})
        total = sum(c.values())
        if not total:
            continue
        dist = "  ".join(f"{v} {k}" for k, v in sorted(c.items(), key=lambda x: -x[1]))
        print(f"{kind:7} spans in prose: {total} - {dist}")
    need = len(blocking) + len(human)
    print(f"\n{need} of {len(findings)} prose spans need a human "
          f"({len(blocking)} blocking in origin=sourced text, {len(human)} partial).")
    print("corpus: docs/reference/cards only. skills/, docs/maturity/, docs/consumption/ "
          "carry the same defect class and are NOT checked here.")
    return 1 if blocking else 0


def selftest() -> int:
    """Plant a fabricated figure and a fabricated quotation in a sourced claim; prove the gate
    sees both, and that it does not see them once removed.

    A criterion nothing can fail is not a criterion (F-part-c-04). This runs entirely in memory,
    so it never leaves a planted defect behind in a real profile the way an edit-and-revert can.
    """
    src, addresses = load_source_text(), card_addresses()
    all_n = norm(" || ".join(src.values()))
    all_l = loose(" || ".join(src.values()))
    base = json.loads((CARDS / "3-3.json").read_text())

    clean = [f for f in check_profile_dict(base, "SELFTEST", src, all_n, all_l, addresses)
             if f["binding"] == "cited" and f["verdict"] in BLOCKING]
    planted = json.loads(json.dumps(base))
    planted["definition"]["text"] += (
        ' Firecracker resumes a snapshot in 5-30ms at a cost of $47,000 per year, and the'
        ' specification states "every sandbox is restored in constant time regardless of'
        ' memory size".')
    dirty = [f for f in check_profile_dict(planted, "SELFTEST", src, all_n, all_l, addresses)
             if f["binding"] == "cited" and f["verdict"] in BLOCKING]

    got = {(f["kind"], f["what"]) for f in dirty} - {(f["kind"], f["what"]) for f in clean}
    print("self-test - deliberate breakage in an origin=sourced claim's text")
    print(f"  before planting: {len(clean)} blocking finding(s) on 3-3.json")
    print(f"  after planting:  {len(dirty)} blocking finding(s)")
    for kind, what in sorted(got):
        print(f"     caught  {kind:6} {what[:80]}")
    wanted = {"5-30ms", "$47,000"}
    caught_figs = {w for k, w in got if k == "figure"}
    caught_quote = any(k == "quote" for k, w in got)
    ok = wanted <= caught_figs and caught_quote and not clean
    print(f"  figures caught: {sorted(caught_figs)}; fabricated quotation caught: {caught_quote}")
    print("PASS - the gate fails on planted prose and is green without it" if ok
          else "FAIL - the gate did not catch the planted defects")
    return 0 if ok else 1


def check_profile_dict(profile, tag, src, all_n, all_l, addresses):
    findings = []
    for site in prose_sites(profile, tag):
        pooled = " || ".join(src.get(i, "") for i in site["ids"])
        pool_n, pool_l = norm(pooled), loose(pooled)
        for span in QUOTE_RE.findall(site["text"]):
            if len(span.split()) < MIN_QUOTE_WORDS:
                continue
            findings.append({"at": site["at"], "kind": "quote",
                             "verdict": quote_verdict(span, pool_n, pool_l, all_n, all_l),
                             "binding": site["binding"], "what": norm(span)[:160],
                             "cites": site["ids"]})
        for tok in FIGURE_RE.findall(site["text"]):
            if structural(tok, site["text"], addresses):
                continue
            findings.append({"at": site["at"], "kind": "figure",
                             "verdict": figure_verdict(tok, pool_n, pool_l, all_n, all_l),
                             "binding": site["binding"], "what": norm(tok),
                             "cites": site["ids"]})
    return findings


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if "--selftest" in args:
        return selftest()
    show_all = "--all" in args
    as_json = "--json" in args
    corpus = CARDS
    for i, a in enumerate(args):
        if a == "--corpus" and i + 1 < len(args):
            corpus = Path(args[i + 1])
    paths = [Path(a) for a in args if not a.startswith("--") and a != str(corpus)]
    if not paths:
        paths = sorted(corpus.glob("*.json"))
    if not paths:
        print(f"no profiles under {corpus}; nothing to check")
        return 0

    src, addresses = load_source_text(), card_addresses()
    all_n = norm(" || ".join(src.values()))
    all_l = loose(" || ".join(src.values()))
    findings = []
    for p in paths:
        findings += check_profile(p, src, all_n, all_l, addresses)

    if as_json:
        print(json.dumps(findings, indent=2))
        return 1 if any(f["binding"] == "cited" and f["verdict"] in BLOCKING for f in findings) else 0
    return report(findings, show_all)


if __name__ == "__main__":
    sys.exit(main())
