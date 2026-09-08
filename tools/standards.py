#!/usr/bin/env python3
"""Standards registry and journey: check the data, render STANDARDS.md and JOURNEY.md.

Every column in both pages is computed from the repository, never typed in:
  status      contract   a skill contract names the standard (E-standard entity)
              researched research records match and no contract names it
              known      registry only, no record: a gap to research
  skills      the skills whose contract.standards names the entity
  version     the versions those contracts claim (all unverified until row 14 clears)
  records     research records in kb/research.jsonl whose url, title, claim or query matches
  examples    example folders whose README mentions the standard
  litmus      min and median per section from docs/litmus/scorecard.md

Usage:
  python3 tools/standards.py check     exit 1 on any inconsistency (counts are the first line)
  python3 tools/standards.py render    write STANDARDS.md and JOURNEY.md, then check
"""
import glob
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "docs/standards/standards.json"
JOUR = ROOT / "docs/journey/journey.json"
SKILLS = ROOT / ".claude/skills"
STEP_COUNTS = (5, 7, 9)


def jl(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def head():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


def load():
    reg = json.loads(REG.read_text())
    jour = json.loads(JOUR.read_text())
    entities = {e["id"] for e in jl(ROOT / "kb/entities.jsonl") if e.get("entity_type") == "standard"}
    research = jl(ROOT / "kb/research.jsonl")
    skills = {}
    for p in sorted(SKILLS.glob("*/skill.json")):
        s = json.loads(p.read_text())
        skills[s["name"]] = s
    readmes = {}
    for p in sorted((ROOT / "examples").glob("*/README.md")):
        readmes[p.parent.name] = p.read_text()
    return reg, jour, entities, research, skills, readmes


def scorecard():
    """(name, kind) -> row dict from docs/litmus/scorecard.md; None if absent."""
    p = ROOT / "docs/litmus/scorecard.md"
    if not p.exists():
        return {}
    rows = {}
    for line in p.read_text().splitlines():
        if not line.startswith("| ") or "capability" not in line and "concern" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 13 or cells[1] not in ("capability", "concern"):
            continue
        rows[(cells[0], cells[1])] = {"settledness": cells[2], "min": cells[3], "median": cells[4],
                                      "misaligned": cells[11], "absent": cells[12]}
    return rows


def litmus_row(rows, name):
    if name.endswith(" (concern)"):
        return rows.get((name[: -len(" (concern)")], "concern"))
    return rows.get((name, "capability")) or rows.get((name, "concern"))


def examples_table():
    """folder -> {'last': ..., 'gap': ...} from examples/README.md, by table."""
    out, section = {}, ""
    for line in (ROOT / "examples/README.md").read_text().splitlines():
        if line.startswith("## "):
            section = line
            continue
        m = re.match(r"\| `([a-z-]+)/` \|(.*)\|$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        d = out.setdefault(m.group(1), {})
        if cells[-1].startswith("`passed"):
            d["last"] = cells[-1].strip("`")
        elif section.startswith("## The gap") and len(cells) == 1:
            d["gap"] = cells[0]
    return out


def compute(reg, jour, entities, research, skills, readmes):
    errors, warnings = [], []
    ids = [s["id"] for s in reg["standards"]]
    if len(ids) != len(set(ids)):
        errors.append("duplicate standard ids")
    by_entity_skill = {}
    for name, s in skills.items():
        for st in (s.get("contract") or {}).get("standards", []) or []:
            by_entity_skill.setdefault(st["entity"], []).append((name, st.get("version") or "unverified", st.get("version_status")))
    rows = {}
    for s in reg["standards"]:
        eid = "E-standard-" + s["id"]
        try:
            rx = re.compile(s["match"], re.I)
        except re.error as e:
            errors.append(f"{s['id']}: bad match regex: {e}")
            continue
        hits = [r for r in research if rx.search(" ".join(str(r.get(k) or "") for k in ("url", "title", "claim", "query")))]
        cites = by_entity_skill.get(eid, [])
        exs = [f for f, t in readmes.items() if rx.search(t) or s["name"].lower() in t.lower()]
        versions = sorted({v for _, v, _ in cites if v and v != "unverified"})
        status = "contract" if cites else ("researched" if hits else "known")
        fetched = sum(1 for r in hits if r.get("status") == "fetched")
        rows[s["id"]] = {**s, "entity": eid, "entity_registered": eid in entities, "skills": sorted({n for n, _, _ in cites}),
                         "versions": versions, "records": len(hits), "record_ids": [r["id"] for r in hits[:3]],
                         "fetched": fetched, "examples": exs, "status": status}
        if cites and eid not in entities:
            warnings.append(f"{s['id']}: cited by {sorted({n for n, _, _ in cites})} but no E-standard entity in kb/entities.jsonl")
        for k in ("provenance", "position", "why", "axis", "journey"):
            if not s.get(k):
                errors.append(f"{s['id']}: missing {k}")
        if s.get("axis") not in reg["axes"]:
            errors.append(f"{s['id']}: axis {s.get('axis')} not in axes")
        if s.get("position") not in reg["positions"]:
            errors.append(f"{s['id']}: position {s.get('position')} not in positions")
    for eid in by_entity_skill:
        if eid[len("E-standard-"):] not in rows:
            errors.append(f"{eid} is named by a skill contract but has no registry row")
    for imp in reg.get("implementations", []):
        if imp.get("behind") and imp["behind"] not in rows:
            errors.append(f"implementation {imp['name']}: behind {imp['behind']} not in registry")
    for area in reg.get("no_open_standard", []):
        if area["owner"] not in skills:
            errors.append(f"no_open_standard {area['area']}: owner {area['owner']} is not a skill")

    steps = jour["steps"]
    letters = [st["letter"] for st in steps]
    if len(steps) not in STEP_COUNTS:
        errors.append(f"journey has {len(steps)} steps; allowed {STEP_COUNTS}")
    if letters != sorted(letters) or len(set(letters)) != len(letters) or any(len(l) != 1 for l in letters):
        errors.append(f"journey letters must be single, unique and ordered: {letters}")
    sc = scorecard()
    ex_tab = examples_table()
    ontology = (ROOT / "docs/reference/ontology.md").read_text()
    used_std, used_skill, used_ex = set(), set(), set()
    for st in steps:
        for k in ("person", "agent", "name", "summary"):
            if not st.get(k):
                errors.append(f"step {st['letter']}: missing {k}")
        for sid in st["standards"]:
            if sid not in rows:
                errors.append(f"step {st['letter']}: unknown standard {sid}")
            used_std.add(sid)
        for sk in st["skills"]:
            if sk not in skills:
                errors.append(f"step {st['letter']}: unknown skill {sk}")
            used_skill.add(sk)
        for ex in st["examples"]:
            if ex not in readmes:
                errors.append(f"step {st['letter']}: unknown example {ex}")
            used_ex.add(ex)
        for ent in st["entities"]:
            if not re.search(r"\|\s*" + re.escape(ent) + r"\s*\||\*\*" + re.escape(ent) + r"\*\*|\b" + re.escape(ent) + r"\b", ontology):
                errors.append(f"step {st['letter']}: entity {ent} not in docs/reference/ontology.md")
        for v in st["verbs"]:
            if v not in ontology:
                errors.append(f"step {st['letter']}: verb {v} not in docs/reference/ontology.md")
        for sec in st["litmus"]:
            if sc and litmus_row(sc, sec) is None:
                errors.append(f"step {st['letter']}: litmus section {sec!r} not in docs/litmus/scorecard.md")
        for s in rows.values():
            if st["letter"] in s["journey"] and s["id"] not in st["standards"]:
                errors.append(f"{s['id']} claims journey {st['letter']} but step {st['letter']} does not list it")
        for sid in st["standards"]:
            if sid in rows and st["letter"] not in rows[sid]["journey"]:
                errors.append(f"step {st['letter']} lists {sid} but its registry row does not claim {st['letter']}")
    for sid in rows:
        if sid not in used_std:
            errors.append(f"{sid} appears in no journey step")
    for sk in skills:
        if sk not in used_skill:
            warnings.append(f"skill {sk} appears in no journey step")
    for ex in readmes:
        if ex not in used_ex:
            warnings.append(f"example {ex} appears in no journey step")
    return rows, steps, sc, ex_tab, errors, warnings


def render_standards(reg, rows, h):
    L = []
    L.append(f"# Standards\n\nGenerated by `tools/standards.py render` at {h} from `docs/standards/standards.json`, the skill contracts, `kb/research.jsonl` and `examples/*/README.md`. Do not edit by hand; edit the data file.\n")
    L.append(reg["intent"] + "\n")
    L.append("## How to read a row\n")
    L.append("| Column | Means |\n|---|---|")
    for k, v in reg["ladder"].items():
        L.append(f"| Status `{k}` | {v} |")
    for k, v in reg["positions"].items():
        L.append(f"| Position `{k}` | {v} |")
    L.append("| Version | what the citing contracts claim; every version is unverified until the specification is fetched (STATUS row 14) |")
    L.append("| Records | research records that match; the first ids are listed so a reader can `python3 tools/kb.py show <id>` |")
    L.append("| Examples | example folders whose README names the standard |")
    L.append("| Journey | the steps in JOURNEY.md that expose it |\n")
    counts = {}
    for r in rows.values():
        counts[(r["status"], r["position"])] = counts.get((r["status"], r["position"]), 0) + 1
    L.append("## Where we are\n")
    L.append("| Status | adopt | hold | watch | decline | Total |\n|---|---|---|---|---|---|")
    for st in reg["ladder"]:
        cells = [counts.get((st, p), 0) for p in reg["positions"]]
        L.append(f"| {st} | " + " | ".join(str(c) for c in cells) + f" | {sum(cells)} |")
    L.append(f"| Total | " + " | ".join(str(sum(counts.get((s, p), 0) for s in reg['ladder'])) for p in reg["positions"]) + f" | {len(rows)} |\n")
    for axis in reg["axes"]:
        rs = [r for r in rows.values() if r["axis"] == axis]
        if not rs:
            continue
        L.append(f"## {axis}\n")
        L.append("| Standard | Status | Position | Version claimed | Skills | Journey |\n|---|---|---|---|---|---|")
        for r in rs:
            name = f"[{r['name']}]({r['url']})" if r.get("url") else r["name"]
            ver = ", ".join(r["versions"]) if r["versions"] else ("unverified" if r["skills"] else "-")
            L.append(f"| {name} | {r['status']} | {r['position']} | {ver} | {', '.join(f'`{s}`' for s in r['skills']) or '-'} | {' '.join(r['journey'])} |")
        L.append("")
        for r in rs:
            recs = f"{r['records']} records" + (f" ({', '.join(r['record_ids'])})" if r["record_ids"] else "")
            exs = f"examples {', '.join(r['examples'])}" if r["examples"] else "no example names it"
            L.append(f"- **{r['name']}** ({r['body']}). {r['why']} {recs}; {exs}; provenance {r['provenance']}.")
        L.append("")
    L.append("## Implementations behind the standards\n\nThese are products and patterns, not standards. Each sits behind one standard above, which is what makes it swappable.\n")
    L.append("| Implementation | Behind | Role here | Note |\n|---|---|---|---|")
    for imp in reg["implementations"]:
        L.append(f"| {imp['name']} | {rows[imp['behind']]['name'] if imp.get('behind') else '-'} | {imp['role']} | {imp['note']} |")
    L.append("\n## Areas with no open standard\n\nThe contract is the platform's own here, marked proposed, and re-checked at each phase boundary.\n")
    L.append("| Area | Owning skill | Note |\n|---|---|---|")
    for a in reg["no_open_standard"]:
        L.append(f"| {a['area']} | `{a['owner']}` | {a['note']} |")
    gaps = [r for r in rows.values() if r["position"] == "adopt" and r["status"] != "contract"]
    L.append("\n## Gaps: adopt, not yet in a contract\n")
    L.append("| Standard | Status | Records | Journey | Next |\n|---|---|---|---|---|")
    for r in gaps:
        nxt = "research it (no record)" if r["status"] == "known" else "name it in the owning skill's contract"
        L.append(f"| {r['name']} | {r['status']} | {r['records']} | {' '.join(r['journey'])} | {nxt} |")
    unverified = sum(1 for r in rows.values() if r["skills"] and not r["fetched"])
    L.append(f"\nEvery one of the {unverified} contract-cited standards is search-only; no specification page has been fetched (STATUS rows 14 and 45).\n")
    L.append("## Provenance\n\n`origin owner` rows are standards the owner named. `stack` rows were already cited by a skill or a research record before this registry. `proposed <date>` rows were added here and are marked so a reader knows nobody asked for them yet.\n")
    return "\n".join(L)


def render_journey(jour, rows, steps, sc, ex_tab, skills, h):
    L = []
    L.append(f"# Journey\n\nGenerated by `tools/standards.py render` at {h} from `docs/journey/journey.json`, `docs/standards/standards.json`, the skills, `docs/reference/ontology.md`, `examples/README.md` and `docs/litmus/scorecard.md`. Do not edit by hand; edit the data file.\n")
    L.append(jour["intent"] + "\n")
    L.append("```\n" + "  →  ".join(f"{s['letter']} {s['name']}" for s in steps) + "\n```\n")
    L.append("## Actors\n")
    for k, v in jour["actors"].items():
        L.append(f"- **{k}**: {v}")
    def med(st):
        vals = []
        for sec in st["litmus"]:
            r = litmus_row(sc, sec)
            if r:
                try:
                    vals.append(float(r["median"]))
                except ValueError:
                    pass
        return f"{statistics.median(vals):.1f}" if vals else "-"
    def short(sid):
        return rows[sid].get("short") or re.sub(r"\s*\(.*?\)", "", rows[sid]["name"])
    def lines(items):
        return "<br>".join(items) or "-"
    def step_cell(st):
        return f"**{st['letter']} {st['name']}**"
    L.append("\n## The steps\n\nRead top to bottom in letter order; that is the left-to-right walk. Each later table adds one layer to the same seven rows.\n")
    L.append("| Step | What happens here | The person asks | The agent asks |\n|---|---|---|---|")
    for st in steps:
        L.append(f"| {step_cell(st)} | {st['summary']} | {st['person']} | {st['agent']} |")
    L.append("\n## The domains each step exposes\n\nSkills are the platform's own layers. Entities are the industry ontology objects (`docs/reference/ontology.md`). Verbs are the cell lifecycle the containment interface maps onto.\n")
    L.append("| Step | Skills | Ontology entities | Cell lifecycle verbs |\n|---|---|---|---|")
    for st in steps:
        L.append(f"| {step_cell(st)} | {lines(f'`{x}`' for x in st['skills'])} | {lines(st['entities'])} | {lines(st['verbs'])} |")
    L.append("\n## The standards at play\n\nIn contract: a skill names it. To adopt: the registry says adopt but no skill names it yet, so it is a gap. Watching: held, watched or declined, with the reason in `STANDARDS.md`.\n")
    L.append("| Step | In contract | To adopt | Watching |\n|---|---|---|---|")
    for st in steps:
        inc = [short(x) for x in st["standards"] if rows[x]["status"] == "contract"]
        adopt = [short(x) for x in st["standards"] if rows[x]["position"] == "adopt" and rows[x]["status"] != "contract"]
        watch = [short(x) for x in st["standards"] if rows[x]["position"] != "adopt" and rows[x]["status"] != "contract"]
        L.append(f"| {step_cell(st)} | {lines(inc)} | {lines(adopt)} | {lines(watch)} |")
    L.append("\n## The evidence per step\n\nExamples are the runnable folders with their last visible test line. The litmus median is over the sections mapped to the step (closed scale: -1 misaligned, 0 absent, 1 exists, 2 aligned, 3 leading). Flags are the questions scored misaligned or absent.\n")
    L.append("| Step | Examples | Litmus sections | Median | Flags |\n|---|---|---|---|---|")
    for st in steps:
        exs = [f"`{e}` {ex_tab.get(e, {}).get('last', '')}".strip() for e in st["examples"]]
        flags = [x for sec in st["litmus"] for r in [litmus_row(sc, sec)] if r for x in (r["misaligned"], r["absent"]) if x != "-"]
        L.append(f"| {step_cell(st)} | {lines(exs)} | {lines(st['litmus'])} | {med(st)} | {lines(flags)} |")
    L.append("")
    for st in steps:
        L.append(f"## {st['letter']}. {st['name']}\n")
        L.append(f"- **The person asks**: {st['person']}")
        L.append(f"- **The agent asks**: {st['agent']}")
        L.append("- **Domains**: " + ", ".join(f"[`{s}`](.claude/skills/{s}/SKILL.md)" for s in st["skills"]))
        L.append("- **Entities** (ontology): " + (", ".join(st["entities"]) or "none"))
        L.append("- **Cell lifecycle verbs**: " + (", ".join(st["verbs"]) or "none, the cell does not exist yet" if st["letter"] < "C" else ", ".join(st["verbs"]) or "none"))
        L.append("\n| Standard | Status | Position | Skills naming it |\n|---|---|---|---|")
        for sid in st["standards"]:
            r = rows[sid]
            L.append(f"| {r['name']} | {r['status']} | {r['position']} | {', '.join(r['skills']) or '-'} |")
        if st["examples"]:
            L.append("\n| Example | Last line | First gap it records |\n|---|---|---|")
            for e in st["examples"]:
                t = ex_tab.get(e, {})
                L.append(f"| [`examples/{e}`](examples/{e}/README.md) | {t.get('last', '-')} | {t.get('gap', '-')} |")
        if st["litmus"]:
            L.append("\n| Litmus section | Settledness | Min | Median | Misaligned | Absent |\n|---|---|---|---|---|---|")
            for sec in st["litmus"]:
                r = litmus_row(sc, sec) or {}
                L.append(f"| {sec} | {r.get('settledness', '-')} | {r.get('min', '-')} | {r.get('median', '-')} | {r.get('misaligned', '-')} | {r.get('absent', '-')} |")
        gaps = []
        for sid in st["standards"]:
            r = rows[sid]
            if r["position"] == "adopt" and r["status"] != "contract":
                gaps.append(f"{r['name']} is {r['status']}, not in a contract")
        for sec in st["litmus"]:
            r = litmus_row(sc, sec)
            if r and (r["misaligned"] != "-" or r["absent"] != "-"):
                gaps.append(f"litmus {sec}: misaligned {r['misaligned']}, absent {r['absent']}")
        for e in st["examples"]:
            g = ex_tab.get(e, {}).get("gap")
            if g:
                gaps.append(f"`{e}`: {g}")
        if not st["examples"]:
            gaps.append("no example walks this step")
        if not st["litmus"]:
            gaps.append("no litmus section measures this step")
        L.append("\n**Gaps at this step**\n")
        L.extend(f"- {g}" for g in gaps) if gaps else L.append("- none recorded")
        L.append("")
    L.append("## Where the gaps sit\n")
    L.append("| Step | Standards to adopt | Litmus misaligned or absent | Examples parked |\n|---|---|---|---|")
    for st in steps:
        adopt = [rows[s]["name"] for s in st["standards"] if rows[s]["position"] == "adopt" and rows[s]["status"] != "contract"]
        lit = []
        for sec in st["litmus"]:
            r = litmus_row(sc, sec)
            if r:
                lit += [x for x in (r["misaligned"], r["absent"]) if x != "-"]
        parked = [e for e in st["examples"] if "Parked" in (ROOT / "examples/README.md").read_text().split(f"`{e}/`")[1].split("\n")[0]] if st["examples"] else []
        L.append(f"| {st['letter']} {st['name']} | {', '.join(adopt) or '-'} | {', '.join(lit) or '-'} | {', '.join(parked) or '-'} |")
    L.append("\n## How to use it\n\n- Say where you are by letter. A pre-flight card, a STATUS row or a ceremony names the step it moves.\n- A new standard enters the registry first, with a position and a reason, then the step that exposes it, then the owning skill's contract. A standard in no step is an error.\n- At a phase boundary the improvement loop reads this page: the gaps column is the target, the litmus column is the measure.\n")
    return "\n".join(L)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    reg, jour, entities, research, skills, readmes = load()
    rows, steps, sc, ex_tab, errors, warnings = compute(reg, jour, entities, research, skills, readmes)
    if cmd == "render":
        h = head()
        (ROOT / "STANDARDS.md").write_text(render_standards(reg, rows, h) + "\n")
        (ROOT / "JOURNEY.md").write_text(render_journey(jour, rows, steps, sc, ex_tab, skills, h) + "\n")
    by = {}
    for r in rows.values():
        by[r["status"]] = by.get(r["status"], 0) + 1
    print(f"standards {len(rows)} ({', '.join(f'{k} {v}' for k, v in sorted(by.items()))}); steps {len(steps)}; errors {len(errors)}; warnings {len(warnings)}")
    for e in errors:
        print("ERROR", e)
    for w in warnings:
        print("WARN", w)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
