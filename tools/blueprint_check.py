#!/usr/bin/env python3
"""Hold docs/architecture/blueprint.json to the source-of-truth rule.

Usage: python3 tools/blueprint_check.py [path]
Errors:
  - a "sources" id that does not exist in kb/ (facts, entities, edges, target, reference, research)
  - a "quote" that is not a verbatim substring of one cited record
  - an entry (any object inside a top-level list) with neither sources nor "status":"gap" nor the word proposed
  - a status:gap entry not represented in the top-level "gaps" list (matched by "where" prefix or claim text)
  - provenance kb heads that do not match kb/meta.json
Prints counts: entries, sourced, gap, and the unsourced ones.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"


def load_kb():
    text = {}
    for f in ("facts", "entities", "edges", "target-facts", "reference-facts", "research"):
        p = KB / f"{f}.jsonl"
        if p.is_file():
            for line in p.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    text[r["id"]] = r.get("text") or r.get("snippet") or json.dumps(r, ensure_ascii=False)
    return text


def main(path: str) -> int:
    d = json.loads(Path(path).read_text())
    kb = load_kb()
    meta = json.loads((KB / "meta.json").read_text())
    errs, n, sourced, gaps = [], 0, 0, 0
    gap_list = d.get("gaps", [])
    gap_keys = {str(g.get("where", "")) for g in gap_list} | {str(g.get("claim", ""))[:40] for g in gap_list}
    for section, items in d.items():
        if not isinstance(items, list):
            continue
        for i, e in enumerate(items):
            if not isinstance(e, dict):
                continue
            n += 1
            where = f"{section}[{i}]"
            srcs = e.get("sources") or []
            for s in srcs:
                if s not in kb:
                    errs.append(f"{where}: unknown source {s}")
            q = e.get("quote")
            if q and not any(q in kb.get(s, "") for s in srcs):
                errs.append(f"{where}: quote is not a substring of any cited record: {q[:50]!r}")
            blob = json.dumps(e, ensure_ascii=False).lower()
            if srcs and not errs[-1:] == [f"{where}: unknown source {srcs[-1]}"]:
                sourced += 1
            if e.get("status") == "gap":
                gaps += 1
                if section != "gaps" and not any(k and (k in where or k in blob) for k in gap_keys):
                    errs.append(f"{where}: status gap but not listed in gaps[]")
            elif not srcs and "proposed" not in blob and section not in ("gaps", "open_questions", "myopia_check"):
                errs.append(f"{where}: no sources, not a gap, not marked proposed")
    for k, v in (d.get("provenance", {}).get("kb_heads") or {}).items():
        if meta["heads"].get(k) != v:
            errs.append(f"provenance head {k} does not match kb/meta.json")
    for e in errs:
        print("error:", e)
    print(f"{n} entries, {sourced} sourced, {gaps} gaps, {len(gap_list)} listed gaps, {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/architecture/blueprint.json"))
