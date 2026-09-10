#!/usr/bin/env python3
"""Fetch a URL and return clean text, trying the most faithful method first.

`tools/verify_snippets.py` re-fetches research-record source pages and strips them
to plain text with a regex tag-stripper to check a claimed-verbatim `snippet` is
really on the page. Regex tag-stripping is not a real HTML parser: it mishandles
inline-tag boundaries (phantom spaces), doesn't understand element nesting, and
has no structured fallback for pages that expose a cleaner representation than
their rendered HTML. This module is the capability that replaces it: given a URL,
return the cleanest text available and say which method ("rung") produced it.

Four rungs, tried in order, first success wins:

  1. api       -- known structured sources with a real API/raw form:
                  arXiv abstract/pdf pages (export.arxiv.org Atom API),
                  GitHub blob pages (rewritten to raw.githubusercontent.com).
  2. markdown  -- request the page with `Accept: text/markdown`, and separately
                  try the path with `.md` appended. Accepted only if the response
                  does not look like an HTML document.
  3. service   -- keyless third-party "reader" services that render a page to
                  markdown server-side: pure.md (preferred; returns markdown with
                  YAML frontmatter) then urltomarkdown.herokuapp.com (fallback).
                  Accepted only if the response does not look like an HTML
                  document and is non-trivially long. Useful for ordinary pages
                  whose markup defeats rung 3's HTML parser (e.g. content
                  assembled client-side that a plain GET's raw HTML never shows).
  4. html      -- a real HTML parser (html.parser.HTMLParser subclass), not regex.
                  Drops script/style/noscript/svg/nav/footer/header/aside/form
                  content entirely, emits a newline at block-element boundaries,
                  emits nothing extra at inline-element boundaries (no phantom
                  spaces), unescapes entities, and collapses whitespace per line
                  while preserving paragraph breaks. This is the fallback that
                  must work for ordinary web pages -- most of the corpus is this.

Usage:
  python3 tools/capture.py <url>            human-readable report + text preview
  python3 tools/capture.py <url> --json     full JSON, including the full text

Importable:
  from capture import capture, html_to_text
  result = capture(url)   # {"url", "rung", "http_status", "bytes", "text", "error"}
"""
from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from html.parser import HTMLParser
from urllib.parse import quote, urlparse, urlunparse

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 20  # seconds
MIN_HOST_DELAY = 1.0  # seconds between two requests to the same host
BASE_DELAY = 0.2  # seconds between any two requests, regardless of host

ARXIV_API = "http://export.arxiv.org/api/query?id_list={id}"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

_ARXIV_URL_RE = re.compile(r"^https?://(?:www\.)?arxiv\.org/(abs|pdf|html)/([^?#]+)", re.IGNORECASE)
_GH_BLOB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$")


# ---------------------------------------------------------------------------
# Polite, rate-limited fetcher shared by all rungs.
# ---------------------------------------------------------------------------

class _Fetcher:
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

    def get(self, url: str, accept: str | None = None):
        """Returns (status_or_None, headers_or_None, raw_bytes_or_None, error_or_None)."""
        host = urlparse(url).netloc
        self._wait(host)
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }
        headers["Accept"] = accept or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        req = urllib.request.Request(url, headers=headers)
        now = time.monotonic()
        self._last_by_host[host] = now
        self._last_any = now
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                status = resp.status
                raw = resp.read()
                final_headers = resp.headers
                return status, final_headers, raw, None
        except urllib.error.HTTPError as e:
            return e.code, e.headers, None, f"HTTPError {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return None, None, None, f"URLError: {e.reason}"
        except (socket.timeout, TimeoutError):
            return None, None, None, "timeout"
        except (ConnectionError, OSError) as e:
            return None, None, None, f"{type(e).__name__}: {e}"


_fetcher = _Fetcher()


def decode_body(raw: bytes, headers) -> str:
    encoding = (headers.get("Content-Encoding") or "").lower() if headers else ""
    if encoding == "gzip":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    elif encoding == "deflate":
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            pass
    charset = None
    if headers is not None and hasattr(headers, "get_content_charset"):
        charset = headers.get_content_charset()
    charset = charset or "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except (LookupError, TypeError):
        return raw.decode("utf-8", errors="replace")


def fetch_raw(url: str, accept: str | None = None):
    return _fetcher.get(url, accept=accept)


# ---------------------------------------------------------------------------
# Rung 3: real HTML -> text converter.
# ---------------------------------------------------------------------------

# NOTE: header/aside are deliberately NOT in the skip set, despite being named in
# the original rung-3 spec alongside nav/footer/form. Measured evidence overrode
# the spec here: on https://futureagi.com/glossary/canary-deployment/, the page's
# genuine, verbatim "quick answer" callout text lives inside
# <aside id="quick-answer" class="short-answer">, and a page's hero title/subtitle
# routinely lives inside <header class="hero">. For a verbatim-substring check,
# the two failure modes are not symmetric: extra boilerplate text can only ever
# cause a missed "drift" (harmless -- it just means the check tries harder), but
# discarding real body text causes a false accusation of fabrication. nav/footer/
# form remain skipped because they are reliably chrome (site nav, copyright,
# search boxes), not prose a source would be quoted from.
_SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "form"}
_BLOCK_TAGS = {
    "p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "br", "tr", "td", "th", "dt", "dd", "table", "figcaption", "main",
    "section", "article", "blockquote", "pre",
}
_WS_LINE_RE = re.compile(r"[ \t\f\v\xa0]+")  # ASCII whitespace plus non-breaking space (&nbsp;)


class _TextExtractor(HTMLParser):
    """Drops non-content elements, emits newlines at block boundaries, emits
    nothing extra at inline boundaries (no phantom spaces), leaves entity
    unescaping to html.unescape() over the assembled text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if self._skip_depth > 0:
            return
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        self._chunks.append(data)

    def get_text(self) -> str:
        return html.unescape("".join(self._chunks))


def _clean_lines(raw: str) -> str:
    """Collapse whitespace within each line; collapse runs of blank lines
    (paragraph boundaries) down to a single blank line."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_WS_LINE_RE.sub(" ", ln).strip() for ln in raw.split("\n")]
    out: list[str] = []
    blank = False
    for ln in lines:
        if ln == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip("\n")


def html_to_text(raw_html: str) -> str:
    """The rung-3 converter: a real HTML parse, not a regex strip. Exported so
    other tools (verify_snippets.py) can reuse it directly."""
    parser = _TextExtractor()
    parser.feed(raw_html)
    parser.close()
    return _clean_lines(parser.get_text())


def _looks_like_html(text: str) -> bool:
    head = text.lstrip().lower()
    return head.startswith("<!doctype") or head.startswith("<html")


# ---------------------------------------------------------------------------
# Rung 1: api -- arXiv Atom API, GitHub raw.
# ---------------------------------------------------------------------------

def _arxiv_id(url: str) -> str | None:
    m = _ARXIV_URL_RE.match(url)
    if not m:
        return None
    ident = m.group(2).rstrip("/")
    if ident.endswith(".pdf"):
        ident = ident[:-4]
    return ident or None


def _fetch_arxiv(ident: str) -> dict | None:
    api_url = ARXIV_API.format(id=ident)
    status, headers, raw, error = fetch_raw(api_url, accept="application/atom+xml")
    if raw is None or status is None or status >= 300:
        return None
    text_xml = decode_body(raw, headers)
    try:
        root = ET.fromstring(text_xml)
    except ET.ParseError:
        return None
    entry = root.find("atom:entry", ATOM_NS)
    if entry is None:
        return None
    title_el = entry.find("atom:title", ATOM_NS)
    summary_el = entry.find("atom:summary", ATOM_NS)
    title = _clean_lines(html.unescape(title_el.text or "")) if title_el is not None else ""
    summary = _clean_lines(html.unescape(summary_el.text or "")) if summary_el is not None else ""
    if not title and not summary:
        return None
    text = f"Title: {title}\n\nAbstract: {summary}".strip()
    return {"rung": "api", "http_status": status, "bytes": len(raw), "text": text, "source": "arxiv-atom-api"}


def _github_raw_url(url: str) -> str | None:
    m = _GH_BLOB_RE.match(url)
    if not m:
        return None
    owner, repo, branch, path = m.groups()
    path = path.split("?")[0].split("#")[0]
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def try_api(url: str) -> dict | None:
    ident = _arxiv_id(url)
    if ident:
        try:
            result = _fetch_arxiv(ident)
            if result:
                return result
        except Exception:
            return None
        return None

    host = urlparse(url).netloc.lower()
    raw_url = None
    if host == "raw.githubusercontent.com":
        raw_url = url
    else:
        raw_url = _github_raw_url(url)
    if raw_url:
        try:
            status, headers, raw, error = fetch_raw(raw_url, accept="text/plain")
        except Exception:
            return None
        if raw is None or status is None or status >= 300:
            return None
        text = decode_body(raw, headers)
        return {
            "rung": "api",
            "http_status": status,
            "bytes": len(raw),
            "text": text.strip(),
            "source": "github-raw",
        }
    return None


# ---------------------------------------------------------------------------
# Rung 2: markdown -- Accept header, then .md path.
# ---------------------------------------------------------------------------

def _append_md(url: str) -> str | None:
    parsed = urlparse(url)
    path = parsed.path
    if not path or path == "/" or path.endswith(".md"):
        return None
    new_path = path.rstrip("/") + ".md"
    return urlunparse(parsed._replace(path=new_path, query="", fragment=""))


def try_markdown(url: str) -> dict | None:
    try:
        status, headers, raw, error = fetch_raw(url, accept="text/markdown")
    except Exception:
        status, raw, headers = None, None, None
    if raw is not None and status is not None and status < 300:
        text = decode_body(raw, headers)
        if not _looks_like_html(text):
            return {
                "rung": "markdown",
                "http_status": status,
                "bytes": len(raw),
                "text": text.strip(),
                "source": "accept-header",
            }

    md_url = _append_md(url)
    if md_url and md_url != url:
        try:
            status2, headers2, raw2, error2 = fetch_raw(md_url, accept="text/markdown")
        except Exception:
            return None
        if raw2 is not None and status2 is not None and status2 < 300:
            text2 = decode_body(raw2, headers2)
            if not _looks_like_html(text2):
                return {
                    "rung": "markdown",
                    "http_status": status2,
                    "bytes": len(raw2),
                    "text": text2.strip(),
                    "url": md_url,
                    "source": "dot-md",
                }
    return None


# ---------------------------------------------------------------------------
# Rung 3: service -- keyless third-party reader services (page -> markdown).
# ---------------------------------------------------------------------------

MIN_SERVICE_TEXT_LEN = 200  # "non-trivially long" floor for a service response

PURE_MD_TEMPLATE = "https://pure.md/{url}"
URLTOMARKDOWN_TEMPLATE = "https://urltomarkdown.herokuapp.com/?url={url}"


def _looks_like_service_success(text: str) -> bool:
    """A service response counts as success only if it is not HTML and is
    non-trivially long -- a short/empty body usually means the service itself
    errored (rate limit, unsupported page) while still returning HTTP 200."""
    if not text or _looks_like_html(text):
        return False
    return len(text.strip()) >= MIN_SERVICE_TEXT_LEN


def _try_pure_md(url: str) -> dict | None:
    service_url = PURE_MD_TEMPLATE.format(url=url)
    try:
        status, headers, raw, error = fetch_raw(service_url, accept="text/markdown, text/plain;q=0.9, */*;q=0.8")
    except Exception:
        return None
    if raw is None or status is None or status >= 300:
        return None
    text = decode_body(raw, headers)
    if not _looks_like_service_success(text):
        return None
    return {
        "rung": "service",
        "http_status": status,
        "bytes": len(raw),
        "text": text.strip(),
        "source": "pure.md",
    }


def _try_urltomarkdown(url: str) -> dict | None:
    service_url = URLTOMARKDOWN_TEMPLATE.format(url=quote(url, safe=""))
    try:
        status, headers, raw, error = fetch_raw(service_url, accept="text/markdown, text/plain;q=0.9, */*;q=0.8")
    except Exception:
        return None
    if raw is None or status is None or status >= 300:
        return None
    text = decode_body(raw, headers)
    if not _looks_like_service_success(text):
        return None
    return {
        "rung": "service",
        "http_status": status,
        "bytes": len(raw),
        "text": text.strip(),
        "source": "urltomarkdown",
    }


def try_service(url: str) -> dict | None:
    """Keyless "reader" services, tried in order, first success wins: pure.md
    (markdown with YAML frontmatter, preferred), then urltomarkdown (fallback).
    Success requires a non-HTML, non-trivially-long response -- see
    _looks_like_service_success."""
    for attempt in (_try_pure_md, _try_urltomarkdown):
        try:
            result = attempt(url)
        except Exception:
            result = None
        if result:
            return result
    return None


# ---------------------------------------------------------------------------
# Rung 4: html -- always attempted as the final fallback.
# ---------------------------------------------------------------------------

def try_html(url: str) -> dict:
    try:
        status, headers, raw, error = fetch_raw(url, accept=None)
    except Exception as e:
        return {"rung": "failed", "http_status": None, "bytes": 0, "text": None, "error": str(e)}
    if raw is None or status is None or status >= 300:
        return {
            "rung": "failed",
            "http_status": status,
            "bytes": 0,
            "text": None,
            "error": error or f"HTTP {status}",
        }
    page = decode_body(raw, headers)
    try:
        text = html_to_text(page)
    except Exception as e:
        return {
            "rung": "failed",
            "http_status": status,
            "bytes": len(raw),
            "text": None,
            "error": f"parse error: {e}",
        }
    return {"rung": "html", "http_status": status, "bytes": len(raw), "text": text}


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def capture(url: str) -> dict:
    """Try api, then markdown, then service, then html. Returns a dict with at
    least {"url", "rung", "http_status", "bytes", "text", "error"}."""
    for attempt in (try_api, try_markdown, try_service):
        try:
            result = attempt(url)
        except Exception:
            result = None
        if result:
            result.setdefault("url", url)
            result.setdefault("error", None)
            return result

    result = try_html(url)
    result.setdefault("url", url)
    result.setdefault("error", None)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("--json", action="store_true", help="emit full JSON, including the full text")
    args = parser.parse_args()

    result = capture(args.url)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        text = result.get("text") or ""
        print(f"url: {result.get('url')}")
        print(f"rung: {result.get('rung')}")
        print(f"http_status: {result.get('http_status')}")
        print(f"bytes: {result.get('bytes')}")
        if result.get("error"):
            print(f"error: {result['error']}")
        print("--- text preview (first 500 chars) ---")
        print(text[:500])

    return 0 if result.get("rung") != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
