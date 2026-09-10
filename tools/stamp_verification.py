#!/usr/bin/env python3
"""Stamp research records with whether their own page actually says what they claim.

This is the tool that makes "citable" mean "checked". Before it existed, nothing connected
the two: `validate_card_profiles.py` never consulted a record's status, so a record whose
page nobody had opened was exactly as citable as one read line by line. Every defect found
on 2026-09-10 -- 45 of 46 profile-cited records failing verification -- entered through that
gap.

The stamp is written ONLY from a real fetch through the SAME path the gate uses (plain GET,
then `capture.html_to_text`). It is never hand-written, and there is deliberately only one
`method` value: two fetch paths that disagree is what produced 13 of 39 drifts in the repair
batch, when authors quoted `capture.py`'s markdown rung and the gate re-read stripped HTML.

Per field, not per record. That distinction is the point: a record can have a genuine
`snippet` and a fabricated `read`, and `validate_card_profiles.py` accepts a quote from
either -- so an invented `read` launders an invented quote past every checker. Stamping each
field separately lets the gate reject exactly the quotes that rest on unverified text.

`unreachable` is not a failure verdict. A page that cannot be retrieved proves nothing about
the record; conflating "I could not check it" with "it is wrong" would be the same overreach
this repo keeps catching elsewhere. Those records stay citable, carry their reason, and are
counted in every report so they never become invisible.

  python3 tools/stamp_verification.py --seed     stamp from the existing gate report (no network)
  python3 tools/stamp_verification.py --fetch    re-fetch and stamp every cited record
  python3 tools/stamp_verification.py --report   print coverage, write nothing
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

RESEARCH_DIR = ROOT / "kb" / "research"
GATE_REPORT = ROOT / "docs" / "reference" / "snippet-verification.json"
VERIFICATION = ROOT / "docs" / "reference" / "citation-verification.json"
CARDS = ROOT / "docs" / "reference" / "cards"
METHOD = "http+html_to_text"
TODAY = "2026-09-10"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def cited_quotes() -> dict:
    """id -> the set of quotes card profiles actually draw from that record.

    Verification is quote-level, not field-level. A `read` excerpt of several hundred
    characters can drift on a single markdown artifact while the one sentence a card quotes is
    genuinely on the page; a field-level verdict would reject that honest citation while
    accepting nothing a quote-level check would not.
    """
    out = {}

    def walk(o):
        if isinstance(o, dict):
            ev = o.get("evidence")
            if isinstance(ev, list):
                for e in ev:
                    if isinstance(e, dict) and str(e.get("id", "")).startswith("X-") and e.get("quote"):
                        out.setdefault(e["id"], set()).add(norm(e["quote"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for f in sorted(CARDS.glob("*.json")):
        walk(json.loads(f.read_text()))
    return out


def cited_records() -> set:
    """Every X- record a card profile cites."""
    out = set()

    def walk(o):
        if isinstance(o, dict):
            ev = o.get("evidence")
            if isinstance(ev, list):
                for e in ev:
                    if isinstance(e, dict) and str(e.get("id", "")).startswith("X-"):
                        out.add(e["id"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for f in sorted(CARDS.glob("*.json")):
        walk(json.loads(f.read_text()))
    return out


def stamps_from_gate_report() -> dict:
    """The gate's own output is already a real fetch through the real path -- reuse it
    rather than hammering every host a second time to learn what it just measured."""
    if not GATE_REPORT.is_file():
        return {}
    doc = json.loads(GATE_REPORT.read_text())
    date = (doc.get("generated") or doc.get("checked_at") or "")[:10] or "unknown"
    out = {}
    for e in doc.get("records", doc.get("entries", [])):
        verdict, detail = e.get("verdict"), (e.get("detail") or {})
        if verdict == "unreachable":
            out[e["id"]] = {
                "checked_at": date, "method": METHOD, "http_status": e.get("http_status"),
                "page_sha256": None, "snippet_verbatim": False, "read_verbatim": None,
                "unreachable": True,
                "reason": str(e.get("error") or "page could not be retrieved")[:200],
            }
            continue
        drifted = set(detail) if isinstance(detail, dict) else set()
        out[e["id"]] = {
            "checked_at": date, "method": METHOD, "http_status": e.get("http_status"),
            "page_sha256": None,
            "snippet_verbatim": "snippet" not in drifted,
            "read_verbatim": (None if "read" not in drifted and verdict == "verified" else "read" not in drifted),
            "unreachable": False, "reason": None,
        }
    return out


def stamps_from_capture_pass() -> dict:
    """Records the 2026-09-10 capture pass proved could not be retrieved, so a citation to
    them can carry an honest reason rather than an absent stamp."""
    if not VERIFICATION.is_file():
        return {}
    doc = json.loads(VERIFICATION.read_text())
    out = {}
    for r in doc.get("records", []):
        if r.get("outcome") != "D_unreachable":
            continue
        out[r["id"]] = {
            "checked_at": doc.get("generated", "2026-09-10"), "method": METHOD,
            "http_status": r.get("http_status"), "page_sha256": None,
            "snippet_verbatim": False, "read_verbatim": None, "unreachable": True,
            "reason": (r.get("notes") or "page could not be retrieved")[:200],
        }
    return out


STOP = set("the a an and or of to in for with that this is are was were be been it its as on at "
           "by from not you your we our their they".split())
# Hosts that answer 200 with only part of the document. An absent quote here means "the part we
# can reach does not contain it", never "the source does not say it" -- arXiv's API returns the
# abstract, and paywalled hosts return a stub. Calling those `absent` would be the same overreach
# this repo keeps catching: treating "I could not check it" as "it is wrong".
PARTIAL_PAGE_HOSTS = ("arxiv.org", "medium.com", "doi.org", "mdpi.com")


def loose(s: str) -> str:
    """Strip everything that is presentation rather than content, so a flattened bullet list or a
    stripped line number stops looking like a different sentence."""
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("`", "").replace("*", "")
    s = re.sub(r"^\s*\d+\s+", "", s, flags=re.M)          # leading line numbers in code listings
    s = re.sub(r"[\u2010-\u2015\-]", " ", s)                # dashes and bullet markers
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).lower().strip()


def _runs(q: str, page: str, minlen: int = 25):
    out, i = [], 0
    while i < len(q):
        best = None
        for j in range(len(q), i + minlen - 1, -1):
            pos = page.find(q[i:j])
            if pos != -1:
                best = (q[i:j], pos)
                break
        if best:
            out.append(best)
            i += len(best[0])
        else:
            i += 1
    return out


def classify_quote(quote: str, page: str, host: str = "", http_ok: bool = True):
    """Say WHAT KIND of difference this is, never just true/false.

    A boolean is what made this session's reporting wrong: `verified: false` meant both "the author
    flattened a bullet list" and "the author invented a statistic", and a reader (including me)
    supplied the difference from imagination. The verdicts below are ordered by how much they
    should worry someone, and only two of them should ever block.
    """
    q, P = norm(quote), norm(page)
    partial_host = any(h in (host or "") for h in PARTIAL_PAGE_HOSTS)
    if not http_ok or len(P) < 200:
        return "unretrievable", {"page_chars": len(P)}
    if q in P:
        return "exact", {}
    ql, Pl = loose(q), loose(P)
    if ql and ql in Pl:
        return "formatting", {}
    parts = _runs(q, P)
    covered = sum(len(seg) for seg, _ in parts) / max(1, len(q))
    if len(parts) >= 2 and covered >= 0.75:
        pos = [p for _, p in parts]
        if max(pos) - min(pos) > 200:
            return "stitched", {"parts": len(parts), "spread": max(pos) - min(pos)}
        return "formatting", {"parts": len(parts)}
    toks = {t for t in re.findall(r"\w+", ql) if len(t) > 4 and t not in STOP}
    overlap = (sum(1 for t in toks if t in Pl) / len(toks)) if toks else 0.0
    if partial_host:
        return "unretrievable", {"reason": "host serves only part of the document",
                                 "content_overlap": round(overlap, 2)}
    if overlap < 0.55:
        return "absent", {"content_overlap": round(overlap, 2)}
    return "partial", {"content_overlap": round(overlap, 2), "covered": round(covered, 2)}


def qhash(q: str) -> str:
    return hashlib.sha256(norm(q).encode()).hexdigest()


def fetch_stamp(rec: dict, quotes=None) -> dict:
    import verify_snippets as V
    fetcher = getattr(fetch_stamp, "_f", None) or V.Fetcher()
    fetch_stamp._f = fetcher
    status, html, err = fetcher.fetch(rec["url"])
    if not html:
        return {"checked_at": TODAY, "method": METHOD, "http_status": status,
                "page_sha256": None, "snippet_verbatim": False, "read_verbatim": None,
                "unreachable": True, "reason": str(err or f"HTTP {status}")[:200],
                "verified_quotes": [], "quote_verdicts": {}}
    page = norm(V.html_to_text(html))
    host = urlparse(rec["url"]).hostname or ""
    return {
        "checked_at": TODAY, "method": METHOD, "http_status": status,
        "page_sha256": hashlib.sha256(page.encode()).hexdigest(),
        "snippet_verbatim": norm(rec.get("snippet")) in page,
        "read_verbatim": (norm(rec["read"]) in page) if rec.get("read") else None,
        "unreachable": False, "reason": None,
        "verified_quotes": sorted(qhash(q) for q in (quotes or set())
                                  if classify_quote(q, page, host, True)[0] in ("exact", "formatting")),
        "quote_verdicts": {qhash(q): classify_quote(q, page, host, True)[0]
                           for q in sorted(quotes or set())},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="stamp from the existing gate report, no network")
    ap.add_argument("--fetch", action="store_true", help="re-fetch every cited record and stamp it")
    ap.add_argument("--report", action="store_true", help="print coverage, write nothing")
    args = ap.parse_args()

    cited = cited_records()
    quotes = cited_quotes()
    stamps = {}
    if args.seed or args.report:
        stamps.update(stamps_from_gate_report())
        stamps.update(stamps_from_capture_pass())   # unreachable wins: it is the stronger statement

    written = 0
    covered = unreachable = unstamped = 0
    for path in sorted(RESEARCH_DIR.glob("*.jsonl")):
        lines, out, changed = path.read_text().splitlines(), [], False
        for line in lines:
            if not line.strip():
                out.append(line)
                continue
            rec = json.loads(line)
            if rec["id"] not in cited:
                out.append(line)
                continue
            stamp = fetch_stamp(rec, quotes.get(rec["id"])) if args.fetch else stamps.get(rec["id"])
            if stamp is None:
                unstamped += 1
                out.append(line)
                continue
            if stamp["unreachable"]:
                unreachable += 1
            else:
                covered += 1
            if args.report:
                out.append(line)
                continue
            if rec.get("verification") != stamp:
                rec["verification"] = stamp
                changed = True
                written += 1
                out.append(json.dumps(rec, ensure_ascii=False, sort_keys=True))
            else:
                out.append(line)
        if changed and not args.report:
            path.write_text("\n".join(out) + "\n")

    print(f"{len(cited)} records cited by card profiles: {covered} verified against their page, "
          f"{unreachable} unreachable (recorded, still citable), {unstamped} with no stamp")
    if not args.report:
        print(f"wrote {written} stamps")
    if unstamped:
        print(f"NOTE: {unstamped} cited record(s) have no stamp; run --fetch to reach them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
