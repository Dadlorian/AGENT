#!/usr/bin/env python3
"""Check every skill against the schema, the knowledge base, and the root contract.

Usage: python3 tools/validate_skills.py [--manifest docs/skill-manifest.json]

Errors (exit 1):
  - skill dir without skill.json, or skill.json violating schemas/skill.schema.json (checked by the
    rules below, since no JSON Schema library is available here; the schema file is the contract)
  - name != directory; layer prefix mismatch; description length out of range
  - any cited id (F-, E-, R-) that does not exist in kb/, including the entities list
  - any item with origin=sourced and no sources or no quote; a quote that is not a verbatim substring
    of a cited record; any item with origin=proposed whose text does not say "proposed"
  - provenance kb heads or PASS.md hash that do not match kb/meta.json (skill built on a stale kb)
  - SKILL.md not identical to the render of skill.json
  - composes_with links naming unknown skills, or asymmetric links
  - product names outside Adapters in SKILL.md
  - if a manifest exists: a skill dir that is not in the manifest, or links differing from it
Warnings:
  - manifest skill not written yet
  - fewer than 3 instructions
  - a table outside the author brief's checked budget (6-10 instructions, 3-10 invariants,
    3-8 best practices)
  - a row restating a kb id under the same verbatim quote as the root contract or a builds_on
    skill, without naming that skill: compose by name, not by copy (author-brief defect item 2)
  - a cap ideal skill with neither an adapters[] pair nor an open question saying where its pair
    lives (author-brief defect item 9)
  - a cap ideal skill with no not_exposed row citing design rule 6, the grader rule (author-brief
    defect item 11): the rule has to be stated, not merely satisfied by the shape of the schema
  - an adapter row citing another capability's adapter or swap-candidate entity in its sources:
    a citation that exists but points at the wrong row of the capability table (defect item 12)
  - an ideal facet the manifest gives the usability section, with no -use sibling to carry it, that
    is missing a worked declaration for one of TARGET T1's three ways in or a worked rejection
    (author-brief defect item 13)
  - a problem type urn:agentic:problem:<suffix> whose suffix has no row in the closed registry in
    docs/decomposition.md section 2.1.6 and is not marked "pending registration" near where the skill
    states it, with a registered type named as the fallback (author-brief defect item 14)
  - an -implement facet whose definition_of_done breakage repeats its ideal facet's word for word,
    or is wholly contained in it (ceremony 10, C10-001): the pair then demonstrates one failure mode
    twice, and nothing shows the build's own wiring, migration stage, binding or gate can fail
  - an adapters[].entity id that resolves nowhere in kb/entities.jsonl and is not said to be proposed
    in the row that states it (ceremony 9, C9-001): the schema checks only the E-(adapter|swap-
    candidate)- name pattern and the unknown-id error covers the top-level entities list, so a minted
    id is otherwise indistinguishable from a knowledge-base-backed one without grepping the kb
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_skill import render  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
KB = ROOT / "kb"
ROOT_SKILL = "agentic-stack"
LAYERS = {"root": None, "core": "core-", "cap": "cap-", "xc": "xc-", "seam": "seam-", "compose": "compose-", "build": "build-"}
PRODUCTS = [
    "LiteLLM", "Firecracker", "goose", "Langfuse", "ClickHouse", "Postgres", "PostgreSQL", "Redis", "MinIO",
    "Temporal", "Tailscale", "Ansible", "SGLang", "vLLM", "Qwen", "Gemini", "OpenAI", "GPT", "Cursor",
    "Claude Code", "Restate", "DBOS", "Inngest", "gVisor", "Kata", "Cloud Hypervisor", "OpenRouter",
    "Phoenix", "Braintrust", "Cedar", "Sigstore", "SPIFFE", "SPIRE", "RunPod", "polkit", "systemd", "docker",
]
# an adapter entity id a skill mints because the knowledge base has none: the row has to say so,
# in the row, in these words (ceremony 9, C9-001).
MINTED_ENTITY_RE = re.compile(r"proposed[^.]{0,80}entity id", re.I)
PRODUCT_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in PRODUCTS) + r")\b")
ID_RE = re.compile(r"^(F|E|R|T|X|REF)-[a-z0-9-]+$")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


KB_TEXT: dict[str, str] = {}
# entity records, needed to tell whether a cited entity belongs to the capability row a skill is about
ENTITIES: dict[str, dict] = {}
GRADER_RULE = "F-b1-07"  # design rule 6: the grader is never visible to the graded

# A skill whose manifest note says it "also carries the usability section (how a human, an agent, and an
# event reach it; minimal inputs/outputs; failure shape)" has no -use sibling to carry that section, so it
# is held to the same bar: a worked instance per producer, and a worked rejection. Producers are told apart
# by the subject prefix the declared_by / actor grammar already fixes (user:, agent:, service: | schedule:).
USABILITY_NOTE = "usability section"
USABILITY_EVIDENCE = {
    "a human producer (\"user:...\")": re.compile(r'"user:[a-z0-9]'),
    "an agent producer (\"agent:...\")": re.compile(r'"agent:[a-z0-9]'),
    "an event producer (\"service:...\" or \"schedule:...\")": re.compile(r'"(?:service|schedule):[a-z0-9]'),
    "a worked rejection (urn:agentic:problem:...)": re.compile(r"urn:agentic:problem"),
}


# cap-errors keeps the problem-type registry closed: a suffix with no row in docs/decomposition.md
# section 2.1.6 is a type no conformant implementation may emit. A skill may still name one it needs,
# the way core-graph names graph-assertion-invalid, but only marked proposed and pending registration
# with a registered fallback, so no caller branches on a URI that cannot legally come back.
PROBLEM_RE = re.compile(r"urn:agentic:problem:([a-z][a-z0-9-]+)")
PENDING = "pending registration"
PROBLEM_WINDOW = 1500  # chars between the suffix and its marker, within one file of the skill
# a standards row's version is a scannable value; the justification goes in version_note
VERSION_MAX = 60
DECOMP = ROOT / "docs" / "decomposition.md"


def registered_problem_types() -> set[str]:
    """The suffixes with a row in the closed registry, read from the design doc rather than hard-coded."""
    types = set()
    for line in (DECOMP.read_text().splitlines() if DECOMP.is_file() else []):
        m = re.match(r"\|\s*`([a-z][a-z0-9-]+)`\s*\|\s*(\d{3})\s*\|\s*(yes|no)\s*\|", line.strip())
        if m:
            types.add(m.group(1))
    return types


def unmarked_problem_types(skill_dir: Path, registered: set[str]) -> list[str]:
    """Suffixes this skill states that are neither registered nor marked pending registration."""
    files = [skill_dir / "skill.json"] + sorted((skill_dir / "references").glob("*.md"))
    texts = [f.read_text() for f in files if f.is_file()]
    stated, marked = set(), set()
    for t in texts:
        for m in PROBLEM_RE.finditer(t):
            suffix = m.group(1)
            if suffix in registered or suffix in ("example",):
                continue
            stated.add(suffix)
            if any(abs(k.start() - m.start()) <= PROBLEM_WINDOW for k in re.finditer(re.escape(PENDING), t)):
                marked.add(suffix)
    return sorted(stated - marked)


def load_kb() -> tuple[set[str], dict]:
    ids = set()
    for f in ("facts", "entities", "edges", "target-facts", "research", "reference-facts"):
        if not (KB / f"{f}.jsonl").is_file():
            continue
        for line in (KB / f"{f}.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                ids.add(r["id"])
                KB_TEXT[r["id"]] = r.get("text") or json.dumps(r, ensure_ascii=False)
                if f == "entities":
                    ENTITIES[r["id"]] = r
    return ids, json.loads((KB / "meta.json").read_text())


def walk_sourced(obj, path, errs, kb_ids, name):
    """Recursively enforce: sources exist in kb; origin=sourced needs sources; origin=proposed must say so."""
    if isinstance(obj, dict):
        if "sources" in obj:
            if not isinstance(obj["sources"], list):
                errs.append(f"{name}: {path}.sources is not a list")
            else:
                for s in obj["sources"]:
                    if not ID_RE.match(str(s)) or s not in kb_ids:
                        errs.append(f"{name}: {path} cites unknown id {s}")
        if "quote" in obj:
            q = str(obj["quote"])
            srcs = [x for x in obj.get("sources", []) if x in KB_TEXT]
            if len(q) < 8:
                errs.append(f"{name}: {path}.quote is too short to be evidence")
            elif not any(q in KB_TEXT[x] for x in srcs):
                errs.append(f"{name}: {path}.quote is not a verbatim substring of any cited record: {q[:60]!r}")
        if "origin" in obj:
            if obj["origin"] == "sourced" and not obj.get("sources"):
                errs.append(f"{name}: {path} is origin=sourced but has no sources")
            if obj["origin"] == "sourced" and not obj.get("quote"):
                errs.append(f"{name}: {path} is origin=sourced but has no quote (verbatim evidence required)")
            if obj["origin"] == "proposed":
                text = " ".join(str(obj.get(k, "")) for k in ("text", "action", "why", "name", "input", "output"))
                if "proposed" not in text.lower() and "our design" not in text.lower():
                    errs.append(f"{name}: {path} is origin=proposed but the text does not say so")
            if obj["origin"] not in ("sourced", "proposed"):
                errs.append(f"{name}: {path}.origin must be sourced or proposed")
        for k, v in obj.items():
            walk_sourced(v, f"{path}.{k}", errs, kb_ids, name)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_sourced(v, f"{path}[{i}]", errs, kb_ids, name)


def rows_of(sk: dict):
    """Every statement row in a skill: instructions, contract tables, best practices, open questions."""
    out = list(sk.get("instructions", []) or [])
    c = sk.get("contract", {}) or {}
    for k in ("invariants", "operations", "shapes", "standards", "not_exposed", "best_practices"):
        v = c.get(k) or []
        if isinstance(v, list):
            out += [x for x in v if isinstance(x, dict)]
    for k in ("best_practices", "open_questions", "adapters"):
        v = sk.get(k) or []
        if isinstance(v, list):
            out += [x for x in v if isinstance(x, dict)]
    p = sk.get("purpose")
    if isinstance(p, dict):
        out.append(p)
    return out


def norm_breakage(text: str | None) -> str:
    """Compare breakages by their words: punctuation and case never make two edits different."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def check_structure(sk: dict, name: str, errs: list[str]):
    req = ["name", "layer", "description", "purpose", "instructions", "definition_of_done", "composes_with", "provenance"]
    for k in req:
        if k not in sk:
            errs.append(f"{name}: missing required field {k}")
    allowed = set(req) | {"wave", "entities", "contract", "best_practices", "adapters", "open_questions"}
    for k in sk:
        if k not in allowed:
            errs.append(f"{name}: unknown field {k}")
    if sk.get("name") != name:
        errs.append(f"{name}: skill.json name is {sk.get('name')!r}")
    layer = sk.get("layer")
    if layer not in LAYERS:
        errs.append(f"{name}: layer {layer!r} not one of {list(LAYERS)}")
    elif layer == "root":
        if name != ROOT_SKILL:
            errs.append(f"{name}: only {ROOT_SKILL} may have layer root")
    elif not name.startswith(LAYERS[layer]):
        errs.append(f"{name}: layer {layer} requires prefix {LAYERS[layer]}")
    d = sk.get("description", "")
    if not (40 <= len(d) <= 1024):
        errs.append(f"{name}: description length {len(d)} not in 40..1024")
    for key in ("purpose",):
        if not isinstance(sk.get(key), dict) or "text" not in sk[key] or "origin" not in sk[key]:
            errs.append(f"{name}: {key} must be an object with text and origin")
    ins = sk.get("instructions", [])
    if not isinstance(ins, list) or not ins:
        errs.append(f"{name}: instructions must be a non-empty list")
    else:
        for i, it in enumerate(ins):
            for k in ("step", "action", "why", "origin"):
                if k not in it:
                    errs.append(f"{name}: instructions[{i}] missing {k}")
    dod = sk.get("definition_of_done", {})
    for k in ("criterion", "expected", "breakage", "expected_failure", "status"):
        if k not in dod:
            errs.append(f"{name}: definition_of_done missing {k}")
    if dod.get("status") not in ("claimed", "measured", None):
        errs.append(f"{name}: definition_of_done.status must be claimed or measured")
    for a in sk.get("adapters", []):
        for k in ("entity", "role", "maps_to", "cannot", "swap_procedure", "status", "sources", "quote"):
            if k not in a:
                errs.append(f"{name}: adapter missing {k}")
        if a.get("role") not in ("today", "second"):
            errs.append(f"{name}: adapter role must be today or second")
    for s in (sk.get("contract") or {}).get("standards", []):
        for k in ("entity", "version", "version_status", "sources"):
            if k not in s:
                errs.append(f"{name}: standard missing {k}")
        if s.get("version_status") not in ("verified", "unverified"):
            errs.append(f"{name}: standard version_status must be verified or unverified")
    cw = sk.get("composes_with", {})
    for k in ("builds_on", "used_by"):
        for n in cw.get(k, []):
            if not NAME_RE.match(n):
                errs.append(f"{name}: composes_with.{k} has bad name {n!r}")
    p = sk.get("provenance", {})
    for k in ("kb_source_sha256", "kb_heads"):
        if k not in p:
            errs.append(f"{name}: provenance missing {k}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=ROOT / "docs" / "skill-manifest.json")
    ap.add_argument("--only", action="append", default=[], help="report only errors/warnings naming these skills (links to others are still loaded)")
    args = ap.parse_args()
    kb_ids, meta = load_kb()
    REGISTERED_PROBLEMS = registered_problem_types()
    errs: list[str] = []
    warns: list[str] = []
    skills: dict[str, dict] = {}
    manifest_names: set[str] = set()
    manifest: dict[str, dict] = {}
    if args.manifest.is_file():
        manifest = {s["name"]: s for s in json.loads(args.manifest.read_text())["skills"]}
        manifest_names = set(manifest)

    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        name = d.name
        sj = d / "skill.json"
        if not sj.is_file():
            errs.append(f"{name}: no skill.json (skills are data; SKILL.md is rendered)")
            continue
        try:
            sk = json.loads(sj.read_text())
        except json.JSONDecodeError as e:
            errs.append(f"{name}: skill.json is not valid JSON: {e}")
            continue
        skills[name] = sk
        check_structure(sk, name, errs)
        walk_sourced(sk, "", errs, kb_ids, name)
        for e in sk.get("entities", []):
            if e not in kb_ids:
                errs.append(f"{name}: entities lists unknown id {e}")
        p = sk.get("provenance", {})
        if p.get("kb_source_sha256") != meta["source"]["sha256"]:
            errs.append(f"{name}: provenance PASS.md hash does not match kb/meta.json (rebuild the skill against the current kb)")
        for k, v in (p.get("kb_heads") or {}).items():
            if meta["heads"].get(k) != v:
                errs.append(f"{name}: provenance kb head '{k}' does not match kb/meta.json")
        md = d / "SKILL.md"
        try:
            rendered = render(sk)
            if not md.is_file() or md.read_text() != rendered:
                errs.append(f"{name}: SKILL.md is not the render of skill.json (run tools/render_skill.py)")
        except (KeyError, TypeError) as e:
            errs.append(f"{name}: cannot render ({e!r})")
            rendered = ""
        # product purity: only inside the Adapters section
        section, allowed = "", False
        for line in rendered.splitlines():
            if line.startswith("## "):
                section = line[3:].strip()
                allowed = section.lower().startswith("adapters")
                continue
            if not allowed:
                hits = sorted(set(PRODUCT_RE.findall(line)))
                if hits:
                    errs.append(f"{name}: product name(s) {hits} outside Adapters, in section '{section or 'frontmatter'}'")
        if len(sk.get("instructions", [])) < 3:
            warns.append(f"{name}: fewer than 3 instructions")
        # swappability is a tested property: a cap ideal skill (no -implement/-use facet suffix)
        # either carries its adapter pair or names, as an open question, where the pair lives and why.
        if sk.get("layer") == "cap" and not name.endswith(("-implement", "-use")) and not sk.get("adapters"):
            if not any("adapter" in (q.get("question") or "").lower() for q in sk.get("open_questions", [])):
                warns.append(f"{name}: cap ideal skill with no adapters[] and no open question naming where the adapter pair lives")
        # design rule 6 is stated, not merely satisfied: a cap ideal skill says what the grader rule
        # forbids on its own interface, so a reader checking the skill against the seven rules can
        # find it without comparing siblings (author-brief defect item 11).
        if sk.get("layer") == "cap" and not name.endswith(("-implement", "-use")):
            ne = (sk.get("contract") or {}).get("not_exposed") or []
            if not any(GRADER_RULE in (r.get("sources") or []) for r in ne if isinstance(r, dict)):
                warns.append(f"{name}: cap ideal skill with no not_exposed row citing {GRADER_RULE} (the grader rule)")
        # an adapter entity id that resolves nowhere is a minted id: legitimate when the capability
        # has no such entity, but only if the row says so, since nothing else tells a reader it is
        # proposed and `kb.py tree` will never show it (ceremony 9, C9-001).
        for a in sk.get("adapters", []):
            eid = a.get("entity")
            if eid in ENTITIES or not eid:
                continue
            prose = " ".join(str(a.get(k, "")) for k in ("maps_to", "cannot", "swap_procedure"))
            if not MINTED_ENTITY_RE.search(prose):
                warns.append(f"{name}: adapter row entity {eid} resolves nowhere in kb/entities.jsonl; "
                             f"say in the row that it is a proposed entity id, and record the gap as an "
                             f"open question")
        # an adapter row's sources may cite adapter entities of its own capability (a row split across
        # two entities, a sibling swap candidate), never another capability's: the ids exist either way,
        # so only the fact each entity is sourced from tells them apart (author-brief defect item 12).
        for a in sk.get("adapters", []):
            own = set((ENTITIES.get(a.get("entity"), {}) or {}).get("sources") or []) | set(a.get("sources") or [])
            for sid in a.get("sources") or []:
                e = ENTITIES.get(sid)
                if not e or sid == a.get("entity") or e.get("entity_type") not in ("adapter", "swap_candidate"):
                    continue
                if not (set(e.get("sources") or []) & own):
                    warns.append(f"{name}: adapter row {a.get('entity')} cites {sid}, whose kb record is sourced from "
                                 f"{', '.join(e.get('sources') or []) or 'nothing'} -- another capability's row")
        # an ideal facet the manifest tells to carry the usability section has no -use sibling to carry
        # it, so it is held to the same completeness bar: a worked declaration for each of TARGET T1's
        # three ways in, and a worked rejection rather than a prose rule (author-brief defect item 13).
        note = (manifest.get(name) or {}).get("notes_for_author") or ""
        if USABILITY_NOTE in note and f"{name}-use" not in manifest:
            body = sj.read_text() + "".join(
                f.read_text() for f in sorted((d / "references").glob("*.md")))
            absent = [what for what, pat in USABILITY_EVIDENCE.items() if not pat.search(body)]
            if absent:
                warns.append(f"{name}: manifest gives it the usability section, but nothing in the skill "
                             f"or its references shows {'; '.join(absent)}")
        # every problem type a skill states resolves to a row in cap-errors' closed registry, or is
        # marked proposed and pending registration where it is stated (author-brief defect item 14).
        for suffix in unmarked_problem_types(d, REGISTERED_PROBLEMS):
            warns.append(f"{name}: states urn:agentic:problem:{suffix}, which has no row in the closed registry in "
                         f"docs/decomposition.md section 2.1.6 and is not marked '{PENDING}' where it is stated")
        # a standards row's `version` is a value a reader scans, not the paragraph explaining it:
        # anything longer than VERSION_MAX belongs in version_note, which renders as a footnote
        # under the Standards table (ceremony 8, C8-001).
        for s in (sk.get("contract") or {}).get("standards", []):
            v = str(s.get("version") or "")
            if len(v) > VERSION_MAX:
                warns.append(f"{name}: standards row {s.get('entity')} has a {len(v)}-character version; keep "
                             f"`version` under {VERSION_MAX} characters and move the justification to version_note")
        # an empty references/ directory is dead scaffolding: progressive disclosure means a reader who
        # opens references/ finds the long material an instruction sent them to (ceremony 8, C8-002).
        refs = d / "references"
        if refs.is_dir() and not any(refs.iterdir()):
            warns.append(f"{name}: empty references/ directory; add the long material or remove the directory")
        for field, rows, lo, hi in (
            ("instructions", sk.get("instructions", []), 6, 10),
            ("invariants", sk.get("contract", {}).get("invariants", []), 3, 10),
            ("best_practices", sk.get("contract", {}).get("best_practices", []) or sk.get("best_practices", []), 3, 8),
        ):
            if rows and not lo <= len(rows) <= hi:
                warns.append(f"{name}: {len(rows)} {field}, outside the checked budget of {lo} to {hi}")

    # an ideal facet and its -implement facet each carry a deliberate breakage; if the second is a
    # copy of the first, the pair proves the same criterion can fail twice and the build itself -
    # its wiring, its migration stages, its bindings, its gate - is never shown to be checkable
    # (ceremony 10, C10-001). Only an outright copy is reported, since a genuinely escalated
    # breakage (the same fault applied at one binding only) is a legitimate second failure mode.
    for name, sk in skills.items():
        if not name.endswith("-implement") or name[: -len("-implement")] not in skills:
            continue
        ideal = skills[name[: -len("-implement")]]
        a = norm_breakage((ideal.get("definition_of_done") or {}).get("breakage"))
        b = norm_breakage((sk.get("definition_of_done") or {}).get("breakage"))
        if a and b and (a == b or a in b or b in a):
            warns.append(f"{name}: definition_of_done breakage repeats {name[: -len('-implement')]}'s "
                         f"word for word; break something the build owns (wiring, a migration stage, "
                         f"a binding, the gate) so the pair shows two failure modes")

    # compose by name, not by copy: a row citing an id its root contract or a builds_on skill
    # already cites must name that skill, so a change to the fact lands in one place.
    # keyed by (id, quote): the same id under the same verbatim quote is a restated fact, where the
    # same id under a different quote is usually a sibling citing the same record for its own point.
    cited_by: dict[tuple[str, str], set[str]] = {}
    for name, sk in skills.items():
        for r in rows_of(sk):
            q = (r.get("quote") or "").strip()
            if not q:
                continue
            for sid in r.get("sources") or []:
                cited_by.setdefault((sid, q), set()).add(name)
    for name, sk in skills.items():
        if name == ROOT_SKILL:
            continue
        owners = set(sk.get("composes_with", {}).get("builds_on", [])) | {ROOT_SKILL}
        owners.discard(name)
        for r in rows_of(sk):
            # every prose field a row can carry: an adapter row's words live in maps_to, cannot and
            # swap_procedure, an open question's in question, evidence and default, so a row that does
            # name its owner there is not reported.
            text = " ".join(str(r.get(k, "")) for k in (
                "text", "action", "why", "note", "maps_to", "cannot", "swap_procedure",
                "question", "evidence", "default", "input", "output"))
            q = (r.get("quote") or "").strip()
            if not q:
                continue
            for sid in r.get("sources") or []:
                also = sorted((cited_by.get((sid, q), set()) & owners) - {name})
                if also and not any(o in text for o in also):
                    w = (f"{name}: restates {sid} under the same quote as {', '.join(also)}, without "
                         f"naming it (compose by name, not by copy)")
                    if w not in warns:  # one line per skill and id, however many rows repeat it
                        warns.append(w)

    known = set(skills) | manifest_names | {ROOT_SKILL}
    for name, sk in skills.items():
        cw = sk.get("composes_with", {})
        for b in cw.get("builds_on", []):
            if b not in known:
                errs.append(f"{name}: builds on unknown skill {b}")
            elif b in skills and b != ROOT_SKILL and name not in skills[b]["composes_with"]["used_by"]:
                errs.append(f"{name} builds on {b}, but {b} does not list {name} under used_by")
        for u in cw.get("used_by", []):
            if u not in known:
                errs.append(f"{name}: used by unknown skill {u}")
            elif u in skills and name not in skills[u]["composes_with"]["builds_on"]:
                errs.append(f"{name} says used by {u}, but {u} does not list {name} under builds_on")
        if name in manifest:
            m = manifest[name]
            if sorted(m.get("builds_on", [])) != sorted(cw.get("builds_on", [])) or sorted(m.get("used_by", [])) != sorted(cw.get("used_by", [])):
                errs.append(f"{name}: composes_with differs from docs/skill-manifest.json")
    if manifest_names:
        for missing in sorted(manifest_names - set(skills)):
            warns.append(f"manifest lists {missing} but it is not written yet")
        for extra in sorted(set(skills) - manifest_names - {ROOT_SKILL}):
            errs.append(f"{extra} is not in docs/skill-manifest.json")

    if args.only:
        errs = [e for e in errs if any(e.startswith(o + ":") or e.startswith(o + " ") for o in args.only)]
        warns = [w for w in warns if any(w.startswith(o + ":") or w.startswith(o + " ") for o in args.only)]
    for w in warns:
        print(f"warning: {w}")
    for e in errs:
        print(f"error:   {e}")
    scope = f"{', '.join(args.only)}: " if args.only else f"{len(skills)} skills checked, "
    print(f"{scope}{len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
