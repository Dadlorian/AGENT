#!/usr/bin/env python3
"""One searchable index over everything addressable in this repo, built once, queried cheaply.

  python3 tools/kb_index.py build            write docs/reference/kb-index.json
  python3 tools/kb_index.py search "<terms>" top hits with their ids
  python3 tools/kb_index.py show <id>        one indexed record

Indexes the *content* - names, purposes, fact text, descriptions - not just identifiers,
so a query like "sandbox isolation network" finds cap-isolation whether or not the word
"isolation" appears in its id. Sources are carried through so a hit can be cited.
"""
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "reference" / "kb-index.json"

STOP = set("""a an and are as at be by for from has have in into is it its of on or that the
to was were will with this these those which what when where how not no than then them they
one two each per any all some other same such only own more most can may must should""".split())


def toks(s):
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t and t not in STOP and len(t) > 2]


def add(recs, rid, kind, name, text, sources=None):
    if rid:
        recs.append({"id": rid, "kind": kind, "name": name or "",
                     "text": " ".join(filter(None, [name, text]))[:1200],
                     "sources": sources or []})


def jsonl(path):
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                yield json.loads(line)


def build():
    r = []
    kb = ROOT / "kb"

    for rec in jsonl(kb / "entities.jsonl"):
        add(r, rec["id"], "entity", rec.get("name"), rec.get("purpose"), rec.get("sources"))
    for rec in jsonl(kb / "architecture.jsonl"):
        if rec.get("type") == "arch-entity":
            add(r, rec["id"], "arch", rec.get("name"),
                " ".join(str(rec.get(k, "")) for k in ("kind", "home_today", "lifetime")),
                rec.get("sources"))
    for f, kind in (("facts.jsonl", "fact"), ("target-facts.jsonl", "target"),
                    ("reference-facts.jsonl", "reference")):
        for rec in jsonl(kb / f):
            add(r, rec["id"], kind, rec.get("name") or rec.get("unit"),
                rec.get("text") or rec.get("statement"), [rec["id"]])
    for rec in jsonl(kb / "research.jsonl"):
        # a research record's substance is in topic/claim/snippet/query, not a summary field;
        # indexing only the title makes every record look empty to a search
        add(r, rec["id"], "research", rec.get("title"),
            " ".join(filter(None, (rec.get("topic"), rec.get("claim"),
                                   rec.get("snippet"), rec.get("query")))),
            [rec["id"]])

    for p in sorted((ROOT / ".claude" / "skills").glob("*/skill.json")):
        d = json.loads(p.read_text())
        std = " ".join(s.get("entity", "") for s in d.get("contract", {}).get("standards", []))
        add(r, d["name"], "skill", d["name"],
            " ".join([d.get("description", ""), str(d.get("purpose", "")), std]))

    q = json.loads((ROOT / "docs" / "litmus" / "questionnaire.json").read_text())
    for s in q["sections"]:
        fs = s.get("future_state") or {}
        add(r, s["id"], "litmus", s.get("name"),
            " ".join([str((s.get("standard") or {}).get("name", "")),
                      str(fs.get("text", ""))[:800]]), s.get("cites"))

    for p in sorted((ROOT / "standards").glob("*/standard.json")):
        d = json.loads(p.read_text())
        add(r, p.parent.name, "standard", d.get("name"),
            " ".join(str(d.get(k, "")) for k in ("why", "acronym", "position")))

    df = defaultdict(int)
    for rec in r:
        rec["_t"] = toks(rec["text"])
        for t in set(rec["_t"]):
            df[t] += 1
    n = len(r)
    for rec in r:
        tf = defaultdict(int)
        for t in rec["_t"]:
            tf[t] += 1
        rec["terms"] = {t: round(c * math.log(1 + n / df[t]), 3) for t, c in tf.items()}
        rec.pop("_t")

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({"records": r}, ensure_ascii=False) + "\n")
    kinds = defaultdict(int)
    for rec in r:
        kinds[rec["kind"]] += 1
    print(f"indexed {n} records: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print(f"-> {INDEX.relative_to(ROOT)} ({INDEX.stat().st_size // 1024} KB)")
    return 0


def load():
    if not INDEX.exists():
        sys.exit("no index; run: python3 tools/kb_index.py build")
    return json.loads(INDEX.read_text())["records"]


def score(records, query, kinds=None, n=8):
    qt = toks(query)
    out = []
    for rec in records:
        if kinds and rec["kind"] not in kinds:
            continue
        s = sum(rec["terms"].get(t, 0) for t in qt)
        if s > 0:
            out.append((round(s, 2), rec))
    out.sort(key=lambda x: -x[0])
    return out[:n]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "build":
        return build()
    if cmd == "search":
        for s, rec in score(load(), " ".join(sys.argv[2:])):
            print(f"  {s:8.2f}  {rec['kind']:9} {rec['id']:34} {rec['name'][:52]}")
        return 0
    if cmd == "show":
        for rec in load():
            if rec["id"] == sys.argv[2]:
                print(json.dumps({k: v for k, v in rec.items() if k != "terms"},
                                 indent=2, ensure_ascii=False))
                return 0
        sys.exit(f"not indexed: {sys.argv[2]}")
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
