#!/usr/bin/env python3
"""Check the SECOND link in the anti-fabrication chain: that a research record's
`snippet` (claimed verbatim from its source page) actually appears on that page.

`tools/validate_skills.py` already enforces the first link -- a skill's quote must be
a verbatim substring of the research record it cites. Nothing before this tool checked
the record's `snippet` against the live page itself. A fetched-with-WebFetch record can
carry a snippet with artifacts the summarizer introduced (fabricated backticks, invented
list numbering, markdown-italic underscores, swapped quote-mark style) that a
substring-of-the-record check can never catch, because the corruption is IN the record.

This tool re-fetches every `status: fetched` research record's URL with a plain HTTP GET
(stdlib urllib, not WebFetch -- WebFetch's summarization step is the thing under
suspicion here), strips HTML to plain text, collapses whitespace on both sides, and
asserts the snippet is a substring of the page text. Whitespace is the ONLY thing
normalised -- no case-folding, no quote-mark canonicalisation, no punctuation stripping
-- because the point is to catch real drift, not paper over it.

Usage:
  python3 tools/verify_snippets.py                 verify all fetched records, write report
  python3 tools/verify_snippets.py --limit 10       smoke run on the first 10
  python3 tools/verify_snippets.py --check          exit 1 if any record is "drift"

Writes docs/reference/snippet-verification.json: a counts summary plus one entry per
record (id, url, verdict, http status, and for "drift" the longest prefix of the
snippet that WAS found on the page, showing exactly where it diverged).

Does not modify kb/research.jsonl or any other source file.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
import gzip
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESEARCH = ROOT / "kb" / "research.jsonl"
DEFAULT_OUTPUT = ROOT / "docs" / "reference" / "snippet-verification.json"

# tools/capture.py is a real HTML parser (html.parser.HTMLParser subclass), not a
# regex tag-stripper. It replaces the previous inline strip_html()/_tag_repl()
# implementation here, which handled inline-vs-block tag boundaries by hand-listing
# tag names and was still capable of manufacturing phantom whitespace on markup it
# didn't anticipate. Same directory as this script, so it's on sys.path[0].
from capture import html_to_text  # noqa: E402

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 20  # seconds
MIN_HOST_DELAY = 1.0  # seconds between two requests to the same host
BASE_DELAY = 0.2  # seconds between any two requests, regardless of host

_WS_RE = re.compile(r"\s+")


def normalize_ws(text: str) -> str:
    """Collapse runs of whitespace to a single space. The only normalisation applied."""
    return _WS_RE.sub(" ", text).strip()


def strip_html(raw_html: str) -> str:
    """Delegates to capture.html_to_text -- a real HTML parse (drops
    script/style/nav/etc., newline at block boundaries, nothing extra at inline
    boundaries) -- then this module's own normalize_ws() collapses it further."""
    return html_to_text(raw_html)


def load_fetched(research_path: Path, limit: int | None) -> list[dict]:
    records = []
    with research_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("status") == "fetched":
                records.append(rec)
    if limit is not None:
        records = records[:limit]
    return records


class Fetcher:
    """Sequential, polite HTTP GET: at least MIN_HOST_DELAY seconds between two
    requests to the same host, plus BASE_DELAY between every request."""

    def __init__(self):
        self._last_by_host: dict[str, float] = {}
        self._last_any: float = 0.0

    def _wait(self, host: str) -> None:
        now = time.monotonic()
        wait_for = 0.0
        last_host = self._last_by_host.get(host)
        if last_host is not None:
            wait_for = max(wait_for, MIN_HOST_DELAY - (now - last_host))
        wait_for = max(wait_for, BASE_DELAY - (now - self._last_any))
        if wait_for > 0:
            time.sleep(wait_for)

    def fetch(self, url: str):
        """Returns (status_or_None, page_text_or_None, error_or_None)."""
        host = urlparse(url).netloc
        self._wait(host)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        now = time.monotonic()
        self._last_by_host[host] = now
        self._last_any = now
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                status = resp.status
                raw = resp.read()
                encoding = (resp.headers.get("Content-Encoding") or "").lower()
                if encoding == "gzip":
                    raw = gzip.decompress(raw)
                elif encoding == "deflate":
                    raw = zlib.decompress(raw)
                charset = resp.headers.get_content_charset() or "utf-8"
                try:
                    text = raw.decode(charset, errors="replace")
                except (LookupError, TypeError):
                    text = raw.decode("utf-8", errors="replace")
                return status, text, None
        except urllib.error.HTTPError as e:
            return e.code, None, f"HTTPError {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return None, None, f"URLError: {e.reason}"
        except (socket.timeout, TimeoutError):
            return None, None, "timeout"
        except (ConnectionError, OSError) as e:
            return None, None, f"{type(e).__name__}: {e}"


def longest_matching_prefix(snippet_norm: str, page_norm: str) -> str:
    """Longest prefix of snippet_norm that occurs as a substring of page_norm.
    Monotonic (a found prefix's own prefixes are all found too), so binary search."""
    lo, hi = 0, len(snippet_norm)
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if snippet_norm[:mid] in page_norm:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return snippet_norm[:best]


def verify_record(rec: dict, fetcher: Fetcher) -> dict:
    rid = rec.get("id")
    url = rec.get("url")
    snippet = rec.get("snippet") or ""
    snippet_norm = normalize_ws(snippet)

    entry = {"id": rid, "url": url, "verdict": None, "http_status": None}

    if not url:
        entry["verdict"] = "unreachable"
        entry["error"] = "record has no url"
        return entry

    status, page_html, error = fetcher.fetch(url)
    entry["http_status"] = status

    if page_html is None or status is None or status >= 300:
        entry["verdict"] = "unreachable"
        entry["error"] = error or f"HTTP {status}"
        return entry

    page_norm = normalize_ws(strip_html(page_html))

    if not snippet_norm:
        entry["verdict"] = "drift"
        entry["error"] = "record has empty snippet"
        return entry

    # `read` is a verbatim excerpt too, and carries as much quotable text as `snippet`.
    # Checking only one of them leaves half the record unverified, which is the same
    # class of hole that let 30 summariser-corrupted snippets through in the first place.
    fields = {"snippet": snippet_norm}
    read_norm = normalize_ws(rec.get("read") or "")
    if read_norm:
        fields["read"] = read_norm

    failed = {}
    for name, value in fields.items():
        if value in page_norm:
            continue
        matched = longest_matching_prefix(value, page_norm)
        failed[name] = {
            "matched_prefix": matched,
            "matched_length": len(matched),
            "field_length": len(value),
            "diverged_after": matched[-40:] if matched else "",
            "diverged_continuation": value[len(matched):len(matched) + 60],
        }

    entry["fields_checked"] = sorted(fields)
    if not failed:
        entry["verdict"] = "verified"
    else:
        entry["verdict"] = "drift"
        entry["drifted_fields"] = sorted(failed)
        entry["detail"] = failed
        # keep the flat snippet keys the earlier report shape used
        if "snippet" in failed:
            entry["matched_prefix"] = failed["snippet"]["matched_prefix"]
            entry["matched_length"] = failed["snippet"]["matched_length"]
            entry["snippet_length"] = failed["snippet"]["field_length"]

    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--research", type=Path, default=DEFAULT_RESEARCH, help="path to research.jsonl")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="path to write the report json")
    parser.add_argument("--limit", type=int, default=None, help="only verify the first N fetched records (smoke run)")
    parser.add_argument("--check", action="store_true", help="exit non-zero if any record is classified 'drift'")
    args = parser.parse_args()

    records = load_fetched(args.research, args.limit)
    fetcher = Fetcher()

    results = []
    for i, rec in enumerate(records, 1):
        entry = verify_record(rec, fetcher)
        results.append(entry)
        print(f"[{i}/{len(records)}] {entry['verdict']:<11} {entry.get('http_status')!s:<5} {entry['id']}", file=sys.stderr)

    counts = {"verified": 0, "drift": 0, "unreachable": 0}
    for entry in results:
        counts[entry["verdict"]] += 1

    report = {
        "counts": counts,
        "total": len(results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(args.research.relative_to(ROOT)) if args.research.is_relative_to(ROOT) else str(args.research),
        "limit": args.limit,
        "records": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    summary = (
        f"verified={counts['verified']} drift={counts['drift']} "
        f"unreachable={counts['unreachable']} (total={len(results)}) -> {args.output}"
    )
    print(summary)

    if args.check and counts["drift"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
