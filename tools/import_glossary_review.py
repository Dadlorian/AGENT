#!/usr/bin/env python3
"""Make the ref_arch vocabulary review part of the record.

`ref_arch/uploads/glossary_review_merged.xlsx` is the only copy of how this platform's 91-term
vocabulary was decided: three reviewers (ChatGPT, Opus 5, Gemini) each proposing a term, an
action, an authority class and an alignment verdict, merged into one workbook. It is binary, it
is untracked, and nothing in this repo can read it. This extracts it to
`docs/reference/glossary-review.json` so the reasoning behind every rename is queryable and
version-controlled rather than sitting in a spreadsheet nobody can diff.

WHAT THE WORKBOOK IS HONEST ABOUT, AND WHY IT IS CARRIED VERBATIM
-----------------------------------------------------------------
The `Key` sheet declares its own limits -- the source glossary was never supplied so spelling and
order are unverified, evidence was shown per reviewer but never scored, and the merge was built
by one of the three reviewers with no tie-break privilege taken. Those caveats are the most
load-bearing thing in the workbook and are copied word for word, never summarised: a caveat
paraphrased is a caveat weakened, and this repo has already spent a day on exactly that.

THE HEADLINE IS DISAGREEMENT
----------------------------
`cellplane-glossary.js` records that renames were applied on "consensus >= 2/3". The Summary
sheet says what that threshold bought: all three reviewers agreed on the ACTION for 25 of 91
terms and on ALIGNMENT for 20 of 91. Gemini is the sole outlier 27 times on Action and 30 on
Authority, so a large share of those 2/3 majorities are two reviewers against one consistently
dissenting reviewer -- not three independent judgements converging. Read the counts with their
denominator; "2/3 consensus" unqualified overstates it.

NOTHING HERE IS EVIDENCE
------------------------
Every `Evidence` cell is a source NAME -- "CNCF Cloud Native Glossary: Multitenancy", "OIDC;
OpenAPI; Auth0 API" -- with no URL, no quote and no fetch, proposed by a model. It enters like
anything else: capture -> record -> `stamp_verification.py --fetch` -> cite. This artifact is a
record of how a decision was made, never evidence of industry practice.

  python3 tools/import_glossary_review.py            write docs/reference/glossary-review.json
  python3 tools/import_glossary_review.py --check    exit 1 if the file differs from the workbook
  python3 tools/import_glossary_review.py --flags    the reviewers' own defect list, cross-checked
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "ref_arch" / "uploads" / "glossary_review_merged.xlsx"
OUT = ROOT / "docs" / "reference" / "glossary-review.json"
STANDARDS = ROOT / "standards"

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def sheets(book: zipfile.ZipFile) -> dict:
    """name -> list of rows, each a list of cell strings.

    Strings may be shared or inline depending on which writer produced the file; both are handled
    rather than assuming, because a missing sharedStrings.xml silently yields empty cells.
    """
    shared = []
    if "xl/sharedStrings.xml" in book.namelist():
        for si in ET.fromstring(book.read("xl/sharedStrings.xml")):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{M}}}t")))
    rels = {r.get("Id"): r.get("Target")
            for r in ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))}

    def value(cell):
        kind = cell.get("t")
        if kind == "inlineStr":
            return "".join(x.text or "" for x in cell.iter(f"{{{M}}}t"))
        v = cell.find(f"{{{M}}}v")
        if v is None:
            return ""
        return shared[int(v.text)] if kind == "s" else (v.text or "")

    out = {}
    wb = ET.fromstring(book.read("xl/workbook.xml"))
    for s in wb.find(f"{{{M}}}sheets"):
        target = rels[s.get(f"{{{R}}}id")].lstrip("/")
        path = target if target.startswith("xl/") else f"xl/{target}"
        grid = ET.fromstring(book.read(path))
        out[s.get("name")] = [[value(c) for c in row] for row in grid.iter(f"{{{M}}}row")]
    return out


def table(rows: list) -> list:
    """First row is the header; every later row becomes a dict, blank cells dropped."""
    if not rows:
        return []
    head = rows[0]
    out = []
    for row in rows[1:]:
        rec = {h: (row[i] if i < len(row) else "") for i, h in enumerate(head) if h}
        if any(v for v in rec.values()):
            out.append(rec)
    return out


def build() -> dict:
    book = zipfile.ZipFile(BOOK)
    sh = sheets(book)

    # Key is two columns of prose, carried verbatim as the methodology and its declared limits.
    methodology = {r[0]: r[1] for r in sh.get("Key", [])[1:] if len(r) >= 2 and r[0]}

    # Summary is several small blocks, each introduced by a one-cell title row.
    summary, block = {}, None
    for row in sh.get("Summary", []):
        cells = [c for c in row if c != ""]
        if len(cells) == 1:
            block = cells[0]
            summary[block] = []
        elif block:
            summary[block].append(row)

    # Long is the tidy form: one row per term per reviewer. Wide is derivable from it, so only the
    # agreement and outlier columns it adds are kept -- storing both would be one fact twice.
    long_rows = table(sh.get("Long", []))
    agreement = {}
    for rec in table(sh.get("Wide", [])):
        term = rec.get("Current term")
        if term:
            agreement[term] = {k: v for k, v in rec.items()
                               if k.endswith(("agree", "outlier")) or k == "Term changes"}

    return {
        "generated_from": str(BOOK.relative_to(ROOT)),
        "note": "A record of HOW the vocabulary was decided, not evidence of industry practice. "
                "Every Evidence cell is a source name with no URL, no quote and no fetch, "
                "proposed by a model. It enters like anything else: capture, record, "
                "stamp_verification.py --fetch, cite.",
        "reviewers": ["ChatGPT", "Opus 5", "Gemini"],
        "methodology_verbatim": methodology,
        "summary": summary,
        "agreement_by_term": agreement,
        "flags": table(sh.get("Flags", [])),
        "reviews": long_rows,
    }


def unanimity(data: dict) -> dict:
    """Counts with their denominator. A share reported first has been read as agreement here."""
    fields = ("Proposed", "Action", "Authority", "Alignment")
    terms = data["agreement_by_term"]
    out = {}
    for f in fields:
        col = f"{f} agree"
        vals = [t.get(col) for t in terms.values() if t.get(col)]
        out[f] = {"all three agree": sum(1 for v in vals if v == "3"),
                  "two agree": sum(1 for v in vals if v == "2"),
                  "one each": sum(1 for v in vals if v == "1"),
                  "of": len(vals)}
    return out


def cross_check(data: dict) -> list:
    """The reviewers' own defect list, checked against this repo rather than filed.

    Three of the four substantive flags name standards this repo already has a directory for, so
    they are answerable today with no fetch. A flag is a claim by one reviewer about another's
    evidence; the repo's own standard record decides it.
    """
    have = {d.name: d for d in STANDARDS.iterdir() if d.is_dir()} if STANDARDS.is_dir() else {}

    def record(name):
        p = have[name] / "standard.json" if name in have else None
        if p and p.is_file():
            try:
                return json.loads(p.read_text())
            except Exception:
                return {}
        return None

    out = []

    # ACP: one reviewer expanded it "Agent Control Protocol". The repo's own record decides.
    r = record("agent-client-protocol")
    out.append({
        "flag": "ACP expansion", "raised_by": "Gemini",
        "issue": "ACP expanded as Agent Control Protocol; the other source says Agent Client Protocol",
        "standards_dir": "agent-client-protocol" if r else None,
        "repo_says": (r or {}).get("name", ""),
        "verdict": ("flag is right, repo unaffected - this repo already carries "
                    f"{(r or {}).get('name','')!r} at {(r or {}).get('url','')}")
        if (r or {}).get("name") == "Agent Client Protocol" else "not covered by this repo"})

    # Idempotency-Key and RateLimit: a reviewer marked Authority=Standard where the evidence names
    # an IETF DRAFT. A draft is not a standard -- the same claimed-vs-measured line this repo draws.
    r = record("idempotency-key-convention")
    is_draft = "draft" in ((r or {}).get("body", "") + (r or {}).get("url", "")).lower()
    out.append({
        "flag": "Idempotency key", "raised_by": "Gemini",
        "issue": "marked Authority=Standard where the evidence names an IETF draft",
        "standards_dir": "idempotency-key-convention" if r else None,
        "repo_says": f"{(r or {}).get('name','')} - {(r or {}).get('body','')}",
        "verdict": ("flag is right, repo unaffected - this repo records it as a draft and named "
                    "the directory `-convention`, so it never called it a standard")
        if is_draft else "not covered by this repo"})

    # The Deprecation header and Sunset are two different RFCs, and this repo has a record for
    # neither. Candidate pages exist in the source pool; nothing has been fetched.
    for flag, issue in (("Deprecation",
                         "cites RFC 8594, which defines Sunset; the Deprecation header is RFC 9745"),
                        ("Rate limit headers",
                         "marked Authority=Standard where the evidence names an IETF draft")):
        out.append({"flag": flag, "raised_by": "Gemini", "issue": issue, "standards_dir": None,
                    "repo_says": "",
                    "verdict": "NOT COVERED - no standards/ record exists here either way, so "
                               "this repo can neither confirm nor contradict it"})
    return out


def main() -> int:
    if not BOOK.is_file():
        print(f"{BOOK.relative_to(ROOT)} not found - the ref_arch design set is not present.")
        return 1
    data = build()

    if "--flags" in sys.argv:
        print(f"{len(data['flags'])} flag(s) the reviewers raised on each other's rows:\n")
        for f in data["flags"]:
            print(f"  {f.get('Reviewer',''):9} {f.get('Current term',''):20} "
                  f"{f.get('Field',''):10} {f.get('Issue','')}")
        print("\ncross-checked against this repo's own standards/ directories:\n")
        for c in cross_check(data):
            print(f"  {c['flag']}  (raised by {c['raised_by']})")
            print(f"     issue:   {c['issue']}")
            if c["repo_says"]:
                print(f"     repo:    {c['repo_says']}  [standards/{c['standards_dir']}]")
            print(f"     verdict: {c['verdict']}")
        return 0

    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if not OUT.is_file():
            print(f"{OUT.relative_to(ROOT)} does not exist; run without --check")
            return 1
        if OUT.read_text() != text:
            print(f"{OUT.relative_to(ROOT)} differs from {BOOK.relative_to(ROOT)} - re-run "
                  f"tools/import_glossary_review.py")
            return 1
        print(f"{OUT.relative_to(ROOT)} matches the workbook")
        return 0

    OUT.write_text(text)
    u = unanimity(data)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['reviews'])} reviews over "
          f"{len(data['agreement_by_term'])} terms by {len(data['reviewers'])} reviewers, "
          f"{len(data['flags'])} flags, {len(data['methodology_verbatim'])} methodology notes")
    print("\nunanimity, with its denominator:")
    for field, c in u.items():
        print(f"  {field:10} all three agree on {c['all three agree']:3} of {c['of']}   "
              f"two agree {c['two agree']:3}   one each {c['one each']:3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
