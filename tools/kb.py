#!/usr/bin/env python3
"""Source-of-truth knowledge base, derived from PASS.md by script.

Every record is traceable: it carries the source file, its SHA-256, the exact line range,
and the exact text. Records are hash-chained so an edit between builds is detectable.
The build is deterministic: running it twice on the same PASS.md yields identical files.

Usage:
  python3 tools/kb.py build            rebuild kb/*.jsonl from PASS.md
  python3 tools/kb.py verify           check chains, file hash, and that every fact's text still matches its lines
  python3 tools/kb.py show <id>        print one record (F-, E-, S-, R- ids)
  python3 tools/kb.py tree             print the knowledge tree (entities grouped, with edges)
  python3 tools/kb.py stats            counts by status and type
  python3 tools/kb.py merge-research   merge kb/research/*.jsonl into kb/research.jsonl (chained, sorted by id)
  python3 tools/kb.py ledger '<json>'  append one run record to kb/ledger.jsonl (chained; adds git commit, tree hash, dirty flag, time)
  python3 tools/kb.py ledger-verify    check the ledger chain

Files:
  kb/facts.jsonl      one record per fact (table row, list item, or paragraph) in PASS.md
  kb/target-facts.jsonl  one record per numbered requirement in TARGET.md (T- ids, status target-owner)
  kb/reference-facts.jsonl  docs/reference/composable-plan.md as REF- records, status reference (an example, never a fact)
  kb/research.jsonl   research records (X- ids) merged from kb/research/*.jsonl by `merge-research`
  kb/entities.jsonl   named things the facts are about, each citing the facts it comes from
  kb/edges.jsonl      typed links between entities, each citing the fact that states the link
  kb/meta.json        source file hash, record counts, head hashes of each chain

Status of a fact is derived from the text, never assigned by hand:
  measured              Part A, and the row, its section heading, or the section intro says "verified" or "measured"
  claimed               Part A otherwise
  defined_not_running   Part A6
  target                Part B (design intent, not a statement about the host)
  ask                   Part C
  meta                  the document preamble
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "PASS.md"
TARGET_SRC = ROOT / "TARGET.md"
KB = ROOT / "kb"
FACTS, ENTITIES, EDGES, META = KB / "facts.jsonl", KB / "entities.jsonl", KB / "edges.jsonl", KB / "meta.json"
TARGET_FACTS = KB / "target-facts.jsonl"
REF_SRC = ROOT / "docs" / "reference" / "composable-plan.md"
REF_FACTS = KB / "reference-facts.jsonl"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(rec: dict) -> str:
    return json.dumps({k: v for k, v in rec.items() if k != "hash"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def chain(records: list[dict]) -> list[dict]:
    prev = "genesis"
    out = []
    for r in records:
        r = dict(r)
        r["prev"] = prev
        r["hash"] = sha256(canonical(r).encode())
        prev = r["hash"]
        out.append(r)
    return out


def slug(s: str) -> str:
    s = re.sub(r"[`*_]", "", s)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s


# ---------------------------------------------------------------- parsing PASS.md

def parse_units(lines: list[str]) -> list[dict]:
    """Split the document into units: table rows, numbered items, paragraphs. Each keeps its line range."""
    units, part, section, i = [], "meta", "", 0
    section_intro: dict[str, str] = {}
    section_title: dict[str, str] = {}
    table_header: list[str] | None = None
    n = len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s or s == "---":
            i += 1
            continue
        m = re.match(r"^# PART ([ABC])\b", s)
        if m:
            part, section, table_header = m.group(1), f"Part {m.group(1)}", None
            i += 1
            continue
        m = re.match(r"^## ([ABC]\d)\.\s*(.*)$", s)
        if m:
            section, table_header = m.group(1), None
            section_title[section] = m.group(2)
            i += 1
            continue
        m = re.match(r"^##+\s+(\d+(?:\.\d+)*)\b", s)
        if m and part not in ("A", "B", "C"):
            section, table_header = m.group(1).replace(".", "-"), None
            i += 1
            continue
        if s.startswith("#"):
            i += 1
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if table_header is None:
                table_header = cells
                i += 1
                continue
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                i += 1
                continue
            units.append({"kind": "row", "part": part, "section": section, "line_start": i + 1, "line_end": i + 1,
                          "text": s, "columns": dict(zip(table_header, cells))})
            i += 1
            continue
        table_header = None
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            units.append({"kind": "item", "part": part, "section": section, "line_start": i + 1, "line_end": i + 1,
                          "text": s, "index": int(m.group(1))})
            i += 1
            continue
        if s.startswith("- "):
            units.append({"kind": "bullet", "part": part, "section": section, "line_start": i + 1, "line_end": i + 1, "text": s})
            i += 1
            continue
        # paragraph: consecutive non-empty, non-structural lines
        start = i
        buf = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("|", "#", "- ")) and not re.match(r"^\d+\.\s", lines[i].strip()) and lines[i].strip() != "---":
            buf.append(lines[i].strip())
            i += 1
        if not buf:  # a line no branch claimed; never loop forever on it
            i += 1
            continue
        text = " ".join(buf)
        u = {"kind": "paragraph", "part": part, "section": section, "line_start": start + 1, "line_end": i, "text": text}
        units.append(u)
        if section and section not in section_intro:
            section_intro[section] = text
    for u in units:
        u["section_intro"] = section_intro.get(u["section"], "")
        u["section_title"] = section_title.get(u["section"], "")
    return units


def status_of(u: dict) -> str:
    if u["part"] == "meta":
        return "meta"
    if u["part"] == "B":
        return "target"
    if u["part"] == "C":
        return "ask"
    if u["section"] == "A6":
        return "defined_not_running"
    for probe in (u["text"], u["section_intro"], u["section_title"]):
        if re.search(r"\b(verified|measured)\b", probe, re.I):
            return "measured"
    return "claimed"


def build_facts(units: list[dict], src_hash: str) -> list[dict]:
    facts = []
    counters: dict[str, int] = {}
    for u in units:
        key = u["section"] or u["part"]
        counters[key] = counters.get(key, 0) + 1
        fid = f"F-{slug(key)}-{counters[key]:02d}"
        rec = {
            "id": fid, "type": "fact", "kind": u["kind"], "part": u["part"], "section": u["section"],
            "status": status_of(u),
            "source": {"file": "PASS.md", "sha256": src_hash, "line_start": u["line_start"], "line_end": u["line_end"]},
            "text": u["text"],
        }
        if "columns" in u:
            rec["columns"] = u["columns"]
        if "index" in u:
            rec["index"] = u["index"]
        facts.append(rec)
    return facts


def strip_md(s: str) -> str:
    return re.sub(r"[`*]", "", s).strip()


def build_entities_edges(facts: list[dict]) -> tuple[list[dict], list[dict]]:
    ents: dict[str, dict] = {}
    edges: list[dict] = []

    def ent(etype: str, name: str, fid: str, **attrs) -> str:
        eid = f"E-{etype.replace(chr(95), chr(45))}-{slug(name)}"
        if eid not in ents:
            ents[eid] = {"id": eid, "type": "entity", "entity_type": etype, "name": name, "sources": [fid], **attrs}
        else:
            if fid not in ents[eid]["sources"]:
                ents[eid]["sources"].append(fid)
            for k, v in attrs.items():
                ents[eid].setdefault(k, v)
        return eid

    def edge(rel: str, src: str, dst: str, fid: str, **attrs):
        edges.append({"id": f"R-{slug(rel)}-{slug(src[2:])}-{slug(dst[2:])}", "type": "edge", "rel": rel, "from": src, "to": dst, "sources": [fid], **attrs})

    platform = None
    for f in facts:
        c = f.get("columns")
        sec, fid = f["section"], f["id"]
        if sec == "A1" and c:
            ent("service", strip_md(c["Service"]), fid, image=strip_md(c["Image"]), port=strip_md(c["Port"]), purpose=c["Purpose"], status=f["status"])
        elif sec == "A2" and c:
            ent("host_unit", strip_md(c["Unit"]), fid, unit_type=c["Type"], bind=strip_md(c["Bind"]), purpose=c["Purpose"], status=f["status"])
        elif sec == "A3" and c:
            ent("sandbox_property", strip_md(c["Element"]), fid, value=c["Value"], status=f["status"])
        elif sec == "A4" and c:
            rc = ent("routing_class", strip_md(c["Prefix"]), fid, contract=c["Contract"], count=strip_md(c["Count"]), status=f["status"])
            for m in re.findall(r"`([^`]+)`", c["Members"]):
                mg = ent("model_group", m, fid, status=f["status"])
                edge("member_of", mg, rc, fid)
        elif sec == "A5" and c:
            ent("provisioning_concern", strip_md(c["Concern"]), fid, implementation=c["Implementation"], status=f["status"])
        elif sec == "A6" and c:
            ent("not_running", strip_md(c["Element"]), fid, detail=c["Status"], status=f["status"])
        elif sec == "A7" and f["kind"] == "paragraph":
            m = re.match(r"^\*\*(\d+)\.\s*(.+?)\*\*", f["text"])
            if m:
                ent("finding", f"A7.{m.group(1)}", fid, title=m.group(2), status=f["status"])
        elif sec == "B1" and f["kind"] == "item":
            m = re.match(r"^\d+\.\s*\*\*(.+?)\*\*", f["text"])
            ent("rule", f"B1.{f['index']}", fid, title=m.group(1) if m else f["text"])
        elif sec == "B2" and c:
            ent("core_component", strip_md(c["Component"]), fid, is_=c["Is"], without=c["Remove it and…"])
        elif sec == "B3" and c:
            cap = ent("capability", strip_md(c["Capability"]), fid)
            std_cell = strip_md(c["Standard"])
            if std_cell.startswith("—"):
                seam = ent("seam", "B5", fid)
                edge("designed_in", cap, seam, fid, note="no standard")
            else:
                for s in [x.strip() for x in std_cell.split("·")]:
                    sid = ent("standard", s, fid, version="unverified")
                    edge("governed_by", cap, sid, fid)
            today = strip_md(c["Adapter today"])
            if today.startswith("absent"):
                ent_absent = ent("adapter", f"{strip_md(c['Capability'])} (absent)", fid, status="absent")
                edge("implemented_today_by", cap, ent_absent, fid)
            else:
                for a in [x.strip() for x in today.split(",")]:
                    aid = ent("adapter", a, fid)
                    edge("implemented_today_by", cap, aid, fid)
            swaps = strip_md(c["Swap candidates"])
            if not swaps.startswith("—"):
                for s in [x.strip() for x in swaps.split("·")]:
                    sid = ent("swap_candidate", s, fid)
                    edge("swappable_to", cap, sid, fid)
        elif sec == "B4" and c:
            if platform is None:
                platform = ent("platform", "platform", fid)
            con = ent("concern", strip_md(c["Concern"]), fid, contract=c["Contract"])
            edge("applies", platform, con, fid)
            for m in re.findall(r"A7 finding (\d)", c["Contract"]):
                edge("informed_by", con, f"E-finding-a7-{m}", fid)
        elif sec == "B5" and f["kind"] == "paragraph":
            m = re.match(r"^\*\*(Dispatch|State)\*\*", f["text"])
            if m:
                s = ent("seam", m.group(1), fid, detail=f["text"])
                edge("part_of", s, "E-seam-b5", fid)
        elif sec == "C" or f["part"] == "C":
            if f["kind"] == "item":
                ent("ask_item", f"C.{f['index']}", fid, text=f["text"])
            elif f["kind"] == "bullet":
                ent("constraint", f"C-constraint-{f['source']['line_start']}", fid, text=f["text"])
    # A7 findings inform B4 rows; make sure referenced finding entities exist
    for e in edges:
        for side in ("from", "to"):
            if e[side] not in ents:
                raise SystemExit(f"edge {e['id']} references unknown entity {e[side]}")
    return list(ents.values()), edges


def write_jsonl(path: Path, records: list[dict]):
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def build_target(src_hash: str, lines: list[str]) -> list[dict]:
    """TARGET.md: every numbered item under a ## T<n> heading is one requirement, status 'target-owner'."""
    out, section = [], ""
    for i, raw in enumerate(lines):
        t = raw.strip()
        m = re.match(r"^## (T\d+)\.", t)
        if m:
            section = m.group(1)
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", t)
        if m and section:
            out.append({"id": f"T-{section.lower()}-{int(m.group(1)):02d}", "type": "fact", "kind": "item", "part": "T", "section": section,
                        "status": "target-owner", "source": {"file": "TARGET.md", "sha256": src_hash, "line_start": i + 1, "line_end": i + 1},
                        "text": t, "index": int(m.group(1))})
    return out


def build_reference(src_hash: str, lines: list[str]) -> list[dict]:
    """docs/reference/composable-plan.md: an owner-supplied EXAMPLE, status 'reference'. Never a fact about the host or the target;
    skills may cite it as an example (REF- ids) but a REF- citation does not make a row sourced to PASS or TARGET."""
    units = parse_units(lines)
    out, counters = [], {}
    for u in units:
        key = u["section"] or "top"
        counters[key] = counters.get(key, 0) + 1
        rec = {"id": f"REF-{slug(key)}-{counters[key]:02d}", "type": "fact", "kind": u["kind"], "part": "REF", "section": u["section"],
               "status": "reference", "source": {"file": "docs/reference/composable-plan.md", "sha256": src_hash, "line_start": u["line_start"], "line_end": u["line_end"]},
               "text": u["text"]}
        if "columns" in u:
            rec["columns"] = u["columns"]
        out.append(rec)
    return out


def build() -> int:
    KB.mkdir(exist_ok=True)
    if REF_SRC.is_file():
        rdata = REF_SRC.read_bytes()
        rfacts = chain(build_reference(sha256(rdata), rdata.decode().split("\n")))
        write_jsonl(REF_FACTS, rfacts)
    else:
        rfacts = []
    tdata = TARGET_SRC.read_bytes()
    tfacts = chain(build_target(sha256(tdata), tdata.decode().split("\n")))
    write_jsonl(TARGET_FACTS, tfacts)
    data = SRC.read_bytes()
    src_hash = sha256(data)
    lines = data.decode().split("\n")
    units = parse_units(lines)
    facts = build_facts(units, src_hash)
    ents, edges = build_entities_edges(facts)
    facts, ents, edges = chain(facts), chain(ents), chain(edges)
    write_jsonl(FACTS, facts)
    write_jsonl(ENTITIES, ents)
    write_jsonl(EDGES, edges)
    META.write_text(json.dumps({
        "source": {"file": "PASS.md", "sha256": src_hash, "lines": len(lines)},
        "sources": {"PASS.md": src_hash, "TARGET.md": sha256(tdata), **({"docs/reference/composable-plan.md": sha256(REF_SRC.read_bytes())} if rfacts else {})},
        "counts": {"facts": len(facts), "entities": len(ents), "edges": len(edges), "target_facts": len(tfacts), "reference_facts": len(rfacts)},
        "heads": {"facts": facts[-1]["hash"], "entities": ents[-1]["hash"], "edges": edges[-1]["hash"], "target_facts": tfacts[-1]["hash"], **({"reference_facts": rfacts[-1]["hash"]} if rfacts else {})},
        "builder": "tools/kb.py",
    }, indent=2) + "\n")
    print(f"built {len(facts)} facts, {len(ents)} entities, {len(edges)} edges from PASS.md {src_hash[:12]}; {len(tfacts)} target facts from TARGET.md; {len(rfacts)} reference facts")
    return 0


def verify() -> int:
    ok = True
    meta = json.loads(META.read_text())
    data = SRC.read_bytes()
    if sha256(data) != meta["source"]["sha256"]:
        print(f"FAIL: PASS.md hash {sha256(data)[:12]} != recorded {meta['source']['sha256'][:12]}")
        ok = False
    lines = data.decode().split("\n")
    tlines = TARGET_SRC.read_bytes().decode().split("\n")
    if sha256(TARGET_SRC.read_bytes()) != meta["sources"]["TARGET.md"]:
        print("FAIL: TARGET.md hash changed since build")
        ok = False
    for f in read_jsonl(TARGET_FACTS):
        if f["text"] != tlines[f["source"]["line_start"] - 1].strip():
            print(f"FAIL: {f['id']} text does not match TARGET.md line {f['source']['line_start']}")
            ok = False
    if REF_FACTS.is_file():
        rlines = REF_SRC.read_bytes().decode().split("\n")
        for f in read_jsonl(REF_FACTS):
            sl, el = f["source"]["line_start"], f["source"]["line_end"]
            if f["text"] != " ".join(l.strip() for l in rlines[sl - 1:el] if l.strip()):
                print(f"FAIL: {f['id']} text does not match the reference lines {sl}-{el}")
                ok = False
    for name, path in (("facts", FACTS), ("entities", ENTITIES), ("edges", EDGES), ("target_facts", TARGET_FACTS)) + ((("reference_facts", REF_FACTS),) if REF_FACTS.is_file() else ()):
        recs = read_jsonl(path)
        prev = "genesis"
        for r in recs:
            if r["prev"] != prev or r["hash"] != sha256(canonical(r).encode()):
                print(f"FAIL: chain broken at {name} {r['id']}")
                ok = False
                break
            prev = r["hash"]
        if recs and recs[-1]["hash"] != meta["heads"][name]:
            print(f"FAIL: {name} head {recs[-1]['hash'][:12]} != meta {meta['heads'][name][:12]}")
            ok = False
    # every fact's text must still be what its lines say
    for f in read_jsonl(FACTS):
        s, e = f["source"]["line_start"], f["source"]["line_end"]
        span = " ".join(l.strip() for l in lines[s - 1:e] if l.strip())
        if f["text"] != span:
            print(f"FAIL: {f['id']} text does not match PASS.md lines {s}-{e}")
            ok = False
    # rebuild in memory and compare: the build must be deterministic
    units = parse_units(lines)
    facts2 = chain(build_facts(units, sha256(data)))
    if [f["hash"] for f in facts2] != [f["hash"] for f in read_jsonl(FACTS)]:
        print("FAIL: rebuilding from PASS.md gives different facts (kb is stale; run build)")
        ok = False
    print("kb verified: chains intact, source hash matches, every fact matches its lines, rebuild is identical" if ok else "kb verification FAILED")
    return 0 if ok else 1


def load_all() -> dict[str, dict]:
    idx = {}
    for p in (FACTS, ENTITIES, EDGES, TARGET_FACTS, KB / "research.jsonl", REF_FACTS):
        if not p.is_file():
            continue
        for r in read_jsonl(p):
            idx[r["id"]] = r
    return idx


def show(rid: str) -> int:
    r = load_all().get(rid)
    if not r:
        print(f"no record {rid}")
        return 1
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


def tree() -> int:
    idx = load_all()
    ents = [r for r in idx.values() if r["type"] == "entity"]
    edges = [r for r in idx.values() if r["type"] == "edge"]
    by_type: dict[str, list[dict]] = {}
    for e in ents:
        by_type.setdefault(e["entity_type"], []).append(e)
    for t, es in by_type.items():
        print(f"{t} ({len(es)})")
        for e in es:
            outs = [f"{x['rel']} -> {x['to']}" for x in edges if x["from"] == e["id"]]
            print(f"  {e['id']}  [{', '.join(e['sources'])}]")
            for o in outs:
                print(f"      {o}")
    return 0


def stats() -> int:
    facts = read_jsonl(FACTS)
    ents = read_jsonl(ENTITIES)
    edges = read_jsonl(EDGES)
    by = lambda rs, k: {v: sum(1 for r in rs if r.get(k) == v) for v in sorted({r.get(k) for r in rs})}  # noqa: E731
    print("facts by status:", json.dumps(by(facts, "status")))
    print("facts by section:", json.dumps(by(facts, "section")))
    print("entities by type:", json.dumps(by(ents, "entity_type")))
    print("edges by rel:", json.dumps(by(edges, "rel")))
    return 0


LEDGER = KB / "ledger.jsonl"
RESEARCH = KB / "research.jsonl"


def merge_research() -> int:
    recs = []
    for p in sorted((KB / "research").glob("*.jsonl")):
        recs += read_jsonl(p)
    recs.sort(key=lambda r: r["id"])
    ids = [r["id"] for r in recs]
    dups = {i for i in ids if ids.count(i) > 1}
    if dups:
        print(f"FAIL: duplicate research ids {sorted(dups)[:5]}")
        return 1
    for r in recs:
        r.pop("prev", None)
        r.pop("hash", None)
    write_jsonl(RESEARCH, chain(recs))
    print(f"merged {len(recs)} research records into kb/research.jsonl")
    return 0


def git(*args) -> str:
    import subprocess
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def ledger_append(payload: dict) -> int:
    import datetime
    recs = read_jsonl(LEDGER) if LEDGER.is_file() else []
    prev = recs[-1]["hash"] if recs else "genesis"
    rec = {"id": f"L-{len(recs) + 1:05d}", "type": "ledger", "time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "git_commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"), "dirty": bool(git("status", "--porcelain")),
           "kb_heads": json.loads(META.read_text())["heads"], **payload}
    rec["prev"] = prev
    rec["hash"] = sha256(canonical(rec).encode())
    with LEDGER.open("a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    print(rec["id"], rec["hash"][:12])
    return 0


def ledger_verify() -> int:
    prev = "genesis"
    n = 0
    for r in (read_jsonl(LEDGER) if LEDGER.is_file() else []):
        if r["prev"] != prev or r["hash"] != sha256(canonical(r).encode()):
            print(f"FAIL: ledger chain broken at {r['id']}")
            return 1
        prev, n = r["hash"], n + 1
    print(f"ledger verified: {n} records, chain intact")
    return 0


if __name__ == "__main__":
    cmds = {"build": build, "verify": verify, "tree": tree, "stats": stats, "merge-research": merge_research, "ledger-verify": ledger_verify}
    if len(sys.argv) >= 3 and sys.argv[1] == "ledger":
        sys.exit(ledger_append(json.loads(sys.argv[2])))
    if len(sys.argv) >= 3 and sys.argv[1] == "show":
        sys.exit(show(sys.argv[2]))
    if len(sys.argv) == 2 and sys.argv[1] in cmds:
        sys.exit(cmds[sys.argv[1]]())
    print(__doc__)
    sys.exit(2)
