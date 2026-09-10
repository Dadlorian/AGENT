#!/usr/bin/env python3
"""Offline unit tests for tools/capture.py's html_to_text() converter.

No network access -- these assert against inline HTML strings only, so they run
fast and deterministically. Network-dependent proof of the capture() rung ladder
against real URLs lives in docs/reference/capture-trial.json (produced by running
capture() over a sample drawn from kb/research.jsonl), not here.

Usage: python3 tools/capture_test.py
Exit 0 if every case passes, 1 otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import html_to_text  # noqa: E402

CASES = [
    (
        "inline tags emit no phantom space at their boundary",
        '<p>see <a href="#">this</a>.</p>',
        "see this.",
    ),
    (
        "script/style/noscript/nav/footer/form content is dropped entirely",
        '<html><head><style>.x{color:red}</style></head><body>'
        '<nav>Home | About</nav>'
        '<script>var x = 1;</script>'
        '<noscript>Enable JS</noscript>'
        '<p>Hello <strong>world</strong>!</p>'
        '<form><input type="text"></form>'
        '<footer>&copy; 2026</footer>'
        "</body></html>",
        "Hello world!",
    ),
    (
        "header and aside content is KEPT (not skipped) -- both routinely carry "
        "real quotable prose (hero titles, quick-answer callouts), and for a "
        "verbatim-substring check, dropping real text causes a false accusation "
        "of drift, which is worse than a little extra boilerplate leaking through",
        '<header class="hero"><h1>Title</h1><p>Hero subtitle text.</p></header>'
        '<aside id="quick-answer"><p>The real quoted answer lives here.</p></aside>',
        None,  # checked via substring assertions below, not full equality
    ),
    (
        "adjacent table cells do not fuse into one word",
        "<table><tr><td>foo</td><td>bar</td></tr></table>",
        None,  # checked via assertion below: "foobar" must NOT appear
    ),
    (
        "named and numeric HTML entities are unescaped",
        "<p>Fish &amp; Chips &mdash; &lt;tag&gt;</p>",
        "Fish & Chips — <tag>",
    ),
    (
        "block elements each get a boundary; list items separate",
        "<ul><li>one</li><li>two</li></ul><p>after</p>",
        "one\n\ntwo\n\nafter",
    ),
]


def run() -> int:
    failures = 0
    for name, html_in, expected in CASES:
        got = html_to_text(html_in)
        if name.startswith("header and aside"):
            ok = "Hero subtitle text." in got and "The real quoted answer lives here." in got
            if not ok:
                failures += 1
                print(f"FAIL: {name}\n  got: {got!r}")
            else:
                print(f"PASS: {name}")
            continue
        if name.startswith("adjacent table cells"):
            ok = "foobar" not in got and "foo" in got and "bar" in got
            if not ok:
                failures += 1
                print(f"FAIL: {name}\n  got: {got!r}")
            else:
                print(f"PASS: {name}")
            continue
        if got != expected:
            failures += 1
            print(f"FAIL: {name}\n  expected: {expected!r}\n  got:      {got!r}")
        else:
            print(f"PASS: {name}")

    total = len(CASES)
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
