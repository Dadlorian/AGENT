#!/usr/bin/env python3
"""Falsify the named proof: prose that names its own evidence is checked against that evidence.

  python3 tools/named_proof.py              every area under examples/reference/
  python3 tools/named_proof.py <area>       one area
  python3 tools/named_proof.py --selftest   plant a drifted quote and a stale promise

WHY
---
state/lessons.jsonl, ceremony 75, 2026-09-04: "Every sentence in a README, a unit's `_` note or
provenance.json that names its own evidence must be checked against that evidence rather than
believed." It stayed prose, and tools/prose_gate.py -- which does exactly this -- says so in its own
docstring: "corpus: docs/reference/cards only". So an example area's README could attribute a quote
to a record id, or print a command beside the last line it promises, and nothing read either.

TWO OF THE LESSON'S FOUR ARMS
-----------------------------
  (a) quote attributed to a record id   the quote must be verbatim in that record's source text
  (c) printed command and its promise   the command is run as written, TWICE, and the promised text
                                        must appear in both runs with the same last line. Twice
                                        because the lesson says so: "run every command exactly as
                                        printed, twice where it writes into a persistent state
                                        directory, and assert the two runs give the same RESULT
                                        line". A command whose second run differs is a printed
                                        promise that is true once.

Arms (b) -- break the claim and require the NAMED section, not the suite, to fail -- and (d) -- a
scan check's scope asserted equal to the sentence it backs -- are not here. They are carried as
lesson 13b-named-proof-bd rather than closed by implication.

VERDICTS ARE TYPED
  exact       verbatim in the cited record / the promise appeared in real output
  formatting  present but for case, whitespace or dashes
  drifted     a long prefix matches and the tail does not -- a person has to read it   BLOCKS
  absent      not in the cited record at all                                           BLOCKS
  stale       the command ran and its output does not carry the promised line          BLOCKS
  unstable    the promise held, but the two runs printed different last lines          BLOCKS
  unrunnable  the command could not be executed as printed                             BLOCKS
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"
SOURCE_FIELDS = ("snippet", "read")
BLOCKING = ("drifted", "absent", "stale", "unstable", "unrunnable")
PROSE_FILES = ("README.md", "provenance.json")
ID = r"[FTREADLX]-[a-z0-9-]+|REF-[a-z0-9-]+"
MIN_WORDS = 5


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "")).strip()


def loose(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", norm(s).lower())


def source_text() -> dict:
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
            out[r["id"]] = ("\n".join(filter(None, (r.get(f) for f in SOURCE_FIELDS)))
                            if name == "research" else (r.get("text") or r.get("name") or ""))
    return out


def verdict(quote: str, src: str) -> str:
    q, s = norm(quote), norm(src)
    if q in s:
        return "exact"
    if loose(q) and loose(q) in loose(s):
        return "formatting"
    head = " ".join(q.split()[:MIN_WORDS])
    return "drifted" if loose(head) and loose(head) in loose(s) else "absent"


def arm_a(area: Path, src: dict) -> list:
    """A quote and a record id within the same paragraph: the id is the attribution."""
    findings = []
    for name in PROSE_FILES:
        p = area / name
        if not p.is_file():
            continue
        text = p.read_text()
        for para in re.split(r"\n\s*\n", text):
            ids = re.findall(ID, para)
            if not ids:
                continue
            for raw in re.findall(r"[\"“]([^\"”]{12,})[\"”]", para):
                if len(raw.split()) < MIN_WORDS:
                    continue
                pool = " || ".join(src.get(i, "") for i in ids)
                findings.append({"where": f"{name}", "kind": "quote",
                                 "verdict": verdict(raw, pool), "cites": sorted(set(ids)),
                                 "what": norm(raw)[:70]})
    return findings


def arm_c(area: Path) -> list:
    """A printed command with a promise beside it, inside a fenced block. Run it, diff the promise."""
    readme = area / "README.md"
    if not readme.is_file():
        return []
    findings = []
    for block in re.findall(r"```[a-z]*\n(.*?)```", readme.read_text(), re.S):
        for line in block.splitlines():
            m = re.match(r"^((?:bash|python3) [^\s].*?)\s{3,}(\S.*)$", line.strip())
            if not m:
                continue
            cmd, promise = m.group(1).strip(), m.group(2).strip()
            if not re.search(r"\d", promise):
                continue     # only promises with a number in them are checkable this way
            outs, failed = [], None
            for _ in range(2):
                try:
                    r = subprocess.run(cmd, shell=True, cwd=area, capture_output=True,
                                       text=True, timeout=600)
                    outs.append(r.stdout + r.stderr)
                except Exception as e:
                    failed = e
                    break
            if failed is not None:
                findings.append({"where": "README.md", "kind": "command", "verdict": "unrunnable",
                                 "cites": [cmd], "what": f"{promise[:50]} ({failed})"})
                continue
            core = re.sub(r"^the [a-z ]+ gate:\s*", "", promise, flags=re.I)
            def last(o):
                lines = [l for l in o.strip().splitlines() if l.strip()]
                return norm(lines[-1]) if lines else ""
            if not all(norm(core) in norm(o) for o in outs):
                v, extra = "stale", ""
            elif last(outs[0]) != last(outs[1]):
                v, extra = "unstable", f" | run1 {last(outs[0])[:28]!r} run2 {last(outs[1])[:28]!r}"
            else:
                v, extra = "exact", ""
            findings.append({"where": "README.md", "kind": "command", "verdict": v,
                             "cites": [cmd], "what": f"{cmd} -> promised {core[:40]!r}{extra}"})
    return findings


def check(area: Path, src=None) -> list:
    src = src if src is not None else source_text()
    return arm_a(area, src) + arm_c(area)


def report(area: Path, findings: list) -> int:
    for f in sorted(findings, key=lambda f: f["verdict"] not in BLOCKING):
        mark = "BLOCK" if f["verdict"] in BLOCKING else "ok"
        print(f"  {mark:5} {f['where']:14} {f['kind']:7} {f['verdict']:10} {f['what'][:62]}")
    blocking = [f for f in findings if f["verdict"] in BLOCKING]
    dist = {}
    for f in findings:
        dist[f["verdict"]] = dist.get(f["verdict"], 0) + 1
    print(f"{area.name}: {len(findings)} named proof(s) - "
          + "  ".join(f"{v} {k}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))
    print(f"{len(blocking)} need a person.\n")
    return 1 if blocking else 0


def selftest() -> int:
    import shutil, tempfile
    areas = sorted(p.parent for p in (ROOT / "examples/reference").glob("*/README.md"))
    if not areas:
        print("FAIL - no area to plant in")
        return 1
    area, src = areas[0], source_text()
    clean = [f for f in check(area, src) if f["verdict"] in BLOCKING]
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / area.name
        shutil.copytree(area, fake, ignore=shutil.ignore_patterns("__pycache__", "out"))
        t = (fake / "README.md").read_text()
        t += ('\n\nPlanted: the standard states "At a high-level an OCI implementation would download'
              ' an OCI Image then unpack that image into a filesystem bundle of our own devising."'
              ' (`X-refmodel-3-3-environment-011`)\n\n```\nbash test.sh    the visible gate:'
              ' passed 999, failed 0\n```\n')
        # A command that answers differently the second time: its promise holds, its result does
        # not. Appended to `t` -- not written straight to the file -- because the write below is
        # what lands, and an earlier draft of this self-test wrote the plant and then overwrote it.
        (fake / "flaky.sh").write_text(
            '#!/usr/bin/env bash\nf="$(dirname "$0")/.flaky-marker"\n'
            'echo "promise 1 holds"\n'
            'if [ -f "$f" ]; then echo "second run differs"; else touch "$f"; echo "first run"; fi\n')
        t += '\n```\nbash flaky.sh    promise 1 holds\n```\n' 
        (fake / "README.md").write_text(t)
        dirty = [f for f in check(fake, src) if f["verdict"] in BLOCKING]
    kinds = {f["verdict"] for f in dirty}
    print("self-test - plant a drifted attributed quote and a stale printed promise")
    print(f"  before planting: {len(clean)} blocking finding(s)")
    print(f"  after planting:  {len(dirty)} blocking finding(s) {sorted(kinds)}")
    ok = not clean and {"drifted", "stale", "unstable"} <= kinds
    print("PASS - a drifted quote, a stale promise and an unstable command all fail, "
          "and none fires without the plant" if ok
          else "FAIL - a planted defect was not caught")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    src = source_text()
    if args:
        a = Path(args[0])
        return report(a if a.is_absolute() else ROOT / a, check(a if a.is_absolute() else ROOT / a, src))
    areas = sorted(p.parent for p in (ROOT / "examples/reference").glob("*/README.md"))
    if not areas:
        print("no example area carries prose yet; nothing to check")
        return 0
    return max(report(a, check(a, src)) for a in areas)


if __name__ == "__main__":
    sys.exit(main())
