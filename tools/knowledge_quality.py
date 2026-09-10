#!/usr/bin/env python3
"""Grade the evidence under every card profile: not how many citations, but what kind.

`tools/knowledge_pool.py` answers "does a card have a profile, and how many of its
citations rest on a fetched page". That is a coverage question. This tool answers the
trust question the owner actually asked: of the evidence standing behind the reference
model, how much is industry knowledge somebody read, how much is a search-result snippet
nobody opened, and how much is this repo citing its own documents.

Four classes, and the distinction that matters is the second vs the third:

  read      an X- record with status `fetched` whose SNIPPET re-verified against the live
            page in docs/reference/snippet-verification.json. A `drift` verdict whose
            detail names only the `read` field still counts as read: the quoted snippet
            matched, only the longer excerpt carries formatting artifacts.
  unread    an X- record with status `search-only`. The cited URL was never contacted.
            The claim rests on what a search engine returned. This repo measured 17 of 68
            such records contradicting their own page -- roughly one in four -- so this
            class is not weak evidence, it is unverified evidence with a known error rate.
  internal  an F-/T-/REF-/A-/E-/R- record: this repo's own documents. Legitimate for "what
            runs here today" or "what the owner intends", and NOT evidence of industry
            practice. Never count it toward external corroboration.
  broken    cites a record id that no longer resolves.

Exit 1 if any card profile cites a record listed in KNOWN_BAD -- records this repo has
already proven misrepresent their source. Those are not a backlog item; they are live
citations to text that is not on the page.

  python3 tools/knowledge_quality.py            print the report
  python3 tools/knowledge_quality.py --write    also write docs/reference/knowledge-quality.md
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "docs" / "reference" / "cards"
RESEARCH = ROOT / "kb" / "research.jsonl"
SNIPPETS = ROOT / "docs" / "reference" / "snippet-verification.json"
OUT = ROOT / "docs" / "reference" / "knowledge-quality.md"

VERIFICATION = ROOT / "docs" / "reference" / "citation-verification.json"

# Seed list from bridge.md, used only if no verification pass has been run yet. The real list is
# measured: docs/reference/citation-verification.json records, per cited record, whether its page
# was actually captured and whether the quotes profiles draw from it are on that page.
SEED_BAD = {
    "X-litmus-c-016": "fabricated comparison and metric attributed to a real Microsoft URL",
    "X-xc-budget-004": "source states the opposite of its claim (an unimplemented feature request)",
    "X-end-to-end-058": "snippet carries verbatim text from a different record's page",
    "X-cap-evaluation-003": "snippet carries verbatim text from a different record's page",
}


def load_known_bad() -> dict:
    """Records a capture pass proved do not support what is cited from them.

    Only `C_contradicted` counts. `D_unreachable` deliberately does NOT: a page that could not be
    retrieved proves nothing, and treating "I could not check it" as "it is wrong" would be the
    same overreach this repo keeps catching elsewhere.
    """
    if not VERIFICATION.is_file():
        return dict(SEED_BAD)
    doc = json.loads(VERIFICATION.read_text())
    out = {}
    for r in doc.get("records", []):
        if r.get("outcome") == "C_contradicted":
            verdict = r.get("claim_verdict") or "unsupported"
            out[r["id"]] = f"page captured; claim {verdict} ({r.get('notes','') or 'no page support'})"[:160]
    for k, v in SEED_BAD.items():
        out.setdefault(k, v)
    return out


def load_research() -> dict:
    return {r["id"]: r for r in (json.loads(l) for l in RESEARCH.read_text().splitlines() if l.strip())}


def load_internal_ids() -> set:
    """Every non-research KB id, loaded the same way validate_card_profiles.py loads them,
    so `broken` means "resolves nowhere in the KB" rather than "does not start with a
    letter I listed". A prefix test would call every id well-formed and never fire."""
    ids = set()
    for name in ("facts", "target-facts", "reference-facts", "entities", "edges", "architecture"):
        path = ROOT / "kb" / f"{name}.jsonl"
        if path.is_file():
            for line in path.read_text().splitlines():
                if line.strip():
                    ids.add(json.loads(line)["id"])
    return ids


def load_verdicts() -> dict:
    """id -> True if the record's SNIPPET verified against the live page."""
    if not SNIPPETS.is_file():
        return {}
    doc = json.loads(SNIPPETS.read_text())
    out = {}
    for e in doc.get("records", doc.get("entries", [])):
        detail = e.get("detail") or {}
        drifted_fields = set(detail) if isinstance(detail, dict) else set()
        # snippet verified unless the snippet itself is what drifted
        out[e["id"]] = e.get("verdict") == "verified" or (
            e.get("verdict") == "drift" and "snippet" not in drifted_fields)
    return out


def classify(rid: str, research: dict, verdicts: dict, internal: set) -> str:
    if rid not in research:
        return "internal" if rid in internal else "broken"
    rec = research[rid]
    if rec["status"] == "fetched":
        return "read" if verdicts.get(rid, False) else "unread"
    return "unread"


def cited_ids(profile: dict):
    """Every {id, quote} pair anywhere in a profile."""
    def walk(o):
        if isinstance(o, dict):
            ev = o.get("evidence")
            if isinstance(ev, list):
                for e in ev:
                    if isinstance(e, dict) and e.get("id"):
                        yield e["id"]
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    yield from walk(profile)


def main() -> int:
    research, verdicts, internal = load_research(), load_verdicts(), load_internal_ids()
    known_bad = load_known_bad()
    paths = sorted(CARDS.glob("*.json"))
    if not paths:
        print("no card profiles found")
        return 0

    rows, totals = [], collections.Counter()
    unread_records = collections.defaultdict(set)
    violations = []

    for p in paths:
        prof = json.loads(p.read_text())
        counts = collections.Counter()
        for rid in cited_ids(prof):
            kind = classify(rid, research, verdicts, internal)
            counts[kind] += 1
            totals[kind] += 1
            if kind == "unread":
                unread_records[rid].add(prof["address"])
            if rid in known_bad:
                violations.append((prof["address"], p.name, rid, known_bad[rid]))
        n = sum(counts.values())
        if n:
            rows.append({"address": prof["address"], "card": prof["card"], "total": n,
                         "read": counts["read"], "unread": counts["unread"],
                         "internal": counts["internal"], "broken": counts["broken"],
                         "pct_read": round(100 * counts["read"] / n)})

    n = sum(totals.values())
    ext = totals["read"] + totals["unread"]
    lines = []
    add = lines.append
    add("# Knowledge quality — what KIND of evidence stands behind the model")
    add("")
    add("Generated by `python3 tools/knowledge_quality.py`. Re-run it rather than trusting these "
        "figures later; every one is a join against a real record, not a score.")
    add("")
    add("`knowledge_pool.py` asks whether a card is covered. This asks whether its evidence is "
        "worth trusting, which is a different question and the one that decides whether examples "
        "can safely be built on it.")
    add("")
    # --- what the SYSTEM decided about each quote, so a reader is not left interpreting a boolean
    verdicts = collections.Counter()
    for rec in research.values():
        verdicts.update(((rec.get("verification") or {}).get("quote_verdicts") or {}).values())
    if verdicts:
        vt = sum(verdicts.values())
        add("## Every quote, typed")
        add("")
        add("Not whether a citation passed, but **what kind of difference** there is between the "
            "sentence a card asserts and the page it names. A bare true/false is what made this "
            "repo's own reporting wrong: it scored a flattened bullet list and an invented statistic "
            "identically, and the difference got supplied from imagination.")
        add("")
        add("| Verdict | Meaning | Quotes | Share | Gate |")
        add("|---|---|---:|---:|---|")
        MEAN = {
          "exact": ("the quote is byte-identical on the page", "passes"),
          "formatting": ("same words; markdown, a flattened list, line numbers or a pronoun differ", "passes"),
          "unretrievable": ("the page could not be read - proves nothing either way", "recorded"),
          "partial": ("part is on the page, part is not - **a person must read this one**", "blocks until reviewed"),
          "stitched": ("two non-adjacent passages joined into one sentence", "blocks"),
          "absent": ("the page does not contain this, or anything close", "blocks"),
        }
        for k in ("exact", "formatting", "unretrievable", "partial", "stitched", "absent"):
            if verdicts.get(k):
                m, g = MEAN[k]
                add(f"| `{k}` | {m} | {verdicts[k]} | {100*verdicts[k]/vt:.1f}% | {g} |")
        add("")
        need = verdicts.get("partial", 0) + verdicts.get("stitched", 0) + verdicts.get("absent", 0)
        add(f"**{need} of {vt} quotes need a human decision.** Everything else the system settled on "
            f"its own. That number, not the percentage above, is the one to act on.")
        add("")
    add("| Class | What it means | Citations | Share |")
    add("|---|---|---:|---:|")
    add(f"| **read** | External page fetched, and the quoted snippet re-verified against the live page | {totals['read']} | {100*totals['read']/n:.1f}% |")
    add(f"| **unread** | External source, page never opened — a search-result snippet | {totals['unread']} | {100*totals['unread']/n:.1f}% |")
    add(f"| **internal** | This repo's own documents (F/T/REF/A) — intent or current state, not industry practice | {totals['internal']} | {100*totals['internal']/n:.1f}% |")
    add(f"| **broken** | Cites an id that resolves nowhere in the knowledge base | {totals['broken']} | {100*totals['broken']/n:.1f}% |")
    add("")
    add(f"**{n} citations across {len(rows)} card profiles.** {ext} are external "
        f"({100*ext/n:.1f}%); of those, {totals['unread']} ({100*totals['unread']/ext:.1f}% of external) "
        f"rest on a page nobody opened.")
    add("")
    add(f"This repo measured 17 of 68 search-only records contradicting their own page. At that "
        f"rate the {totals['unread']} unread citations carry roughly "
        f"**{round(totals['unread']*17/68)} citations that their source does not support**.")
    add("")

    if violations:
        add("## Live citations to records already proven wrong")
        add("")
        add(f"These are not a backlog. Each names a record this repo has already checked and found "
            f"to misrepresent its own page, and each is currently load-bearing in a card profile. "
            f"**{len(violations)} citations across {len({v[0] for v in violations})} profiles** — a record "
            f"appearing twice for one card is propping up two separate assertions in two different "
            f"claim fields, so both sites have to be fixed. `validate_card_profiles.py` only forbids "
            f"citing an id twice inside one claim object, so a half-fix still passes it.")
        add("")
        add("| Card | Profile | Record | What is wrong with it |")
        add("|---|---|---|---|")
        for a, f, rid, why in sorted(violations):
            add(f"| {a} | `{f}` | `{rid}` | {why} |")
        add("")

    add("## The verification target")
    add("")
    add(f"Only **{len(unread_records)} distinct records** stand behind every unread citation in the "
        f"whole model, across "
        f"{len({urlparse(research[r]['url']).hostname for r in unread_records if r in research})} hosts. "
        f"That is the list that has to be checked before an example is built on a profile — not the "
        f"whole search-only corpus.")
    add("")
    add("| Record | Cards depending on it | Host |")
    add("|---|---|---|")
    for rid, cards in sorted(unread_records.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        host = urlparse(research[rid]["url"]).hostname if rid in research else "?"
        flag = " **(page checked: unsupported)**" if rid in known_bad else ""
        add(f"| `{rid}`{flag} | {', '.join(sorted(cards))} | {host} |")
    add("")
    add("## By card, weakest first")
    add("")
    add("| Card | Name | read | unread | internal | total | % read |")
    add("|---|---|---:|---:|---:|---:|---:|")
    for r in sorted(rows, key=lambda r: (r["pct_read"], r["address"])):
        add(f"| {r['address']} | {r['card']} | {r['read']} | {r['unread']} | {r['internal']} "
            f"| {r['total']} | {r['pct_read']}% |")
    add("")

    text = "\n".join(lines) + "\n"
    if "--write" in sys.argv:
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        print(text)

    print(f"{n} citations: {totals['read']} read, {totals['unread']} unread, "
          f"{totals['internal']} internal, {totals['broken']} broken; "
          f"{len(unread_records)} distinct records to verify")
    if violations:
        print(f"FAIL: {len(violations)} live citation(s) across "
              f"{len({v[0] for v in violations})} profile(s) to records already proven to "
              f"misrepresent their page")
        for a, f, rid, why in sorted(violations):
            print(f"  {a:7} {f:14} {rid}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
