# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is not a running application. It is a design-and-evidence repo for a target "agentic platform"
architecture, built as: 29 Claude Code skills (`.claude/skills/`), 28 harnesses that prove each stack
element swaps behind its interface (`harness/`), a knowledge base derived from source docs with
hash-chained provenance (`kb/`), and 7 user-facing example areas (`examples/`). Everything is
dependency-free Python 3 (stdlib only, no `requirements.txt`/`pyproject.toml`) and bash. There is no
build step, no server to run, no app to launch.

Read `README.md` in full before making structural changes — it is the map of every layer, tool, and
check in this repo and is kept in sync with the tree. `PASS.md` (current state, Part A; target
architecture, Part B) and `TARGET.md` (the composability baseline and T1–T10 measuring sticks) are the
source documents everything else derives from.

## Working here

- **`OWNER.md`** — one line per owner direction, newest last. Read it before doing any work; it holds
  standing rules (e.g. cite everything to the knowledge base or mark it a gap, name every task/agent/scope
  claim by its STATUS row id, keep STATUS.md current in the same commit as the work it describes).
- **`STATUS.md`** — the single view of open work, one row per item with its definition of done as a
  runnable command/file. Closed rows move to `STATUS-ARCHIVE.md` via `tools/status_archive.py`. Do not
  let STATUS.md drift from the state of the repo.
- **`NEXTSTEP.md`** — points at the live scoreboard (`python3 tools/ready_to_build.py`) and the order to
  take the open conditions in. Deliberately short: it went stale for six days once by trying to be a
  hand-written punch list, so the measured state lives in the commands it names, not in its prose.
- Nothing is asserted from memory: a claim in a skill or doc is either cited to a `kb/*.jsonl` record with
  a verbatim quote, or explicitly marked `proposed`.
- Naming convention: agents, scope claims, and ceremony records are named by their STATUS row id, e.g.
  `61-review-c`, never a bare description like `sourcing-03a`.

## Commands

There is no single global test suite; there are per-area gates. Run the ones relevant to what you touched.
Commands are marked `(read-only)` or `(writes)`; `checkpoint.sh` additionally **commits and pushes to
`origin`** — never run it without meaning to publish.

### Skills (`.claude/skills/<name>/skill.json` → rendered `SKILL.md`)
```
python3 tools/validate_skills.py               # (read-only) schema + KB + root-contract check; errors block, warnings don't
python3 tools/render_skill.py --check <dir>    # (read-only) exit 1 if SKILL.md differs from what skill.json renders
python3 tools/render_skill.py <dir> [...]      # (writes) render SKILL.md from skill.json (tables only, every row cited)
python3 tools/render_skill.py --all            # (writes) render every skill under .claude/skills
python3 tools/check_adapter_pairs.py           # (read-only) every cap-/seam- skill has a today adapter and a differing second adapter
python3 tools/skill_graph.py                   # (writes) regenerate docs/skill-graph.md; exits 1 if a focal group won't render under mermaid limits
python3 tools/skill_health.py [--json]         # (read-only) per-skill usage/findings/warnings/measured-state/litmus distance
```

### Knowledge base (`kb/*.jsonl`)
```
python3 tools/kb.py verify                # (read-only) chain + source-line integrity
python3 tools/kb.py ledger-verify         # (read-only) verify the append-only run ledger
python3 tools/kb.py show <id>             # (read-only) resolve any F-/E-/R-/D-/A-/L-/T-/REF-/X- id
python3 tools/kb.py stats                 # (read-only) counts by status/type
python3 tools/kb.py build                 # (writes) rebuild kb/*.jsonl from PASS.md
```
Verified 2026-09-08 at commit `917deaf`: `kb.py verify` → "chains intact, source hash matches, every fact
matches its lines, rebuild is identical"; `kb.py ledger-verify` → `316 records, chain intact` (this count
grows with every checkpoint — don't treat it as a fixed target; re-run rather than trust a stale number).

### Harnesses (`harness/<name>/`, listed in `harness/plan.json`)
Each harness has `interface.py`, three adapters (`dryrun`, `live`, `second`), `call.py` (minimal caller),
`conformance.py`, `test.sh` (the gate, with one deliberate breakage), `README.md`, `provenance.json`.
```
bash harness/<name>/test.sh                     # (read-only) passed N, failed 0
ADAPTER=second python3 harness/<name>/call.py   # (read-only) same caller against the other execution model
python3 tools/harness_accept.py <name>          # (writes, no commit) run the gate, merge plan-entry.json into harness/plan.json, release scope claim, regen acceptance+guides
python3 tools/final_acceptance.py               # (read-only) run every harness gate. Verified 2026-09-08 at 917deaf: 14 of 15 hold (T-t9-06 red: work-intake, dispatch, compose-operators harnesses)
python3 tools/final_acceptance.py --write       # (writes) store docs/acceptance/final.json
```

### Examples (`examples/<area>/` — run, ask, watch, steer, progress, done, improve)
```
bash examples/<area>/test.sh              # (read-only) visible check the author could see
bash docs/night/hidden/<area>.sh          # (read-only) hidden check written by an isolated reviewer (run only at close, not by the author)
bash examples/end-to-end/test.sh          # (read-only) the reference example
python3 tools/examples_index.py           # (writes) regenerate the seven-area x four-door matrix at docs/examples/index.md
```
Verified 2026-09-08: `bash examples/end-to-end/test.sh` → `passed 30, failed 0`.

### Docs, standards, acceptance
```
python3 tools/acceptance_check.py --check     # (read-only) docs/acceptance/matrix.md hand-edit check
python3 tools/acceptance_check.py             # (writes) regenerate docs/acceptance/matrix.md
python3 tools/render_guide.py --check         # (read-only) docs/guides/<element>.md hand-edit check
python3 tools/blueprint_check.py              # (read-only) docs/architecture/blueprint.json source-of-truth check
python3 tools/standards.py check              # (read-only) STANDARDS.md + JOURNEY.md consistency vs. skills/KB/examples/scorecard
python3 tools/litmus_check.py check           # (read-only) litmus questionnaire coverage/citation/contamination check
```
Re-measured 2026-09-11: `acceptance_check.py --check` → **13 of 16 elements accepted, 77 of 80 sticks
hold**. The older "16 of 16, 80 of 80" reading was already wrong when written: commit `9a53ecc`
(2026-09-10) added `proposed` rows to cap-work-intake, cap-provenance and cap-scheduling and did not
regenerate the matrix, which was last written on 2026-09-09. `acceptance_check` is **not** one of
`phase.py`'s 29 gates, so nothing surfaced the drift — run the command rather than quoting either
number. STATUS row 94. `standards.py check` → "standards 41 ...; steps 7; errors 0;
warnings 4" (4 warnings are pre-existing: standards cited by a skill with no matching `E-` entity yet —
not a regression to chase blindly, but don't add a fifth).

### Status and commit discipline
```
python3 tools/status_check.py                 # (read-only) keep STATUS.md a clean single table
python3 tools/status_check.py --freshness     # (read-only) find stale claims
python3 tools/status_archive.py --dry-run     # (read-only) show what would move
python3 tools/status_archive.py               # (writes) move Done rows to STATUS-ARCHIVE.md, appended, with closing date + commit
bash tools/checkpoint.sh "<message>" <paths>  # (writes, COMMITS AND PUSHES to origin claude/auto-skill-creation-i8javu) runs validate_skills + kb verify first, refuses on red
```
Verified 2026-09-08: `status_check.py --freshness` → `freshness: 8 live rows, 0 claims, 0 stale`.

### Full definition of done
All read-only; run these before considering a change complete:
```
python3 tools/validate_skills.py
python3 tools/kb.py verify
python3 tools/kb.py ledger-verify
python3 tools/final_acceptance.py
python3 tools/acceptance_check.py --check
python3 tools/status_check.py --freshness
bash examples/end-to-end/test.sh
```
Don't assume this list is currently all-green — as of 2026-09-08 (`917deaf`), `final_acceptance.py` is
14 of 15 (three harnesses red), matching STATUS rows 74–77 still Open. Check `STATUS.md` and
`NEXTSTEP.md` for the current punch list before treating a red result here as something you broke.

## Architecture

### Skills as data, not prose
Every skill under `.claude/skills/<name>/` is authored as `skill.json` against a schema, then *rendered*
to `SKILL.md` by `tools/render_skill.py` — never hand-edited. `skill.json` fields: `name`, `layer`, `wave`,
`description` (≤60 words, what triggers loading it), `purpose`, `entities`, `contract`, `instructions`,
`best_practices`, `adapters`, `definition_of_done`, `composes_with`, `open_questions`, `provenance`,
`folded` (former skills folded in whole, preserved under `references/`). Layers: `root` (1, `agentic-stack`
— every skill assumes it), `core` (1, `core-components`), `cap` (18, one per capability interface),
`xc` (1, `xc-guarantees`), `seam` (2, dispatch/state), `compose` (2), `build` (4). Loading `agentic-stack`
first is mandatory for any work in this repo; each skill also names a `-implement` sibling under
`composes_with` for when you're writing code against the contract, not just reading it.

### Harnesses prove swappability
Each of the 28 `harness/<name>/` directories exists to prove one capability interface can swap its
implementation without touching the caller: a `dryrun` adapter (fast, deterministic), a `live` adapter
(claimed only — no harness has run against a real host from a session, see STATUS row 37), and a `second`
adapter (a genuinely different execution model, checked by `check_adapter_pairs.py`). `call.py` is
intentionally the minimal caller (test.sh asserts it's under 40 lines) — this is the piece meant to be
read as "how would I actually call this."

### Knowledge base and provenance chain
`kb/*.jsonl` is derived, not hand-written: `facts.jsonl` (F-, from PASS.md), `target-facts.jsonl` (T-,
from TARGET.md), `reference-facts.jsonl` (REF-, from the worked example doc), `research.jsonl` (X-,
search-only — no page fetch has been verified in this environment), `entities.jsonl` (E-),
`edges.jsonl` (R-), `decisions.jsonl` (D-), `architecture.jsonl` (A-, from the blueprint),
`ledger.jsonl` (L-, append-only hash-chained run records). Every fact record carries its source file,
SHA-256, exact line range, and exact text — `tools/kb.py verify` re-checks all of it. Treat this chain as
the single source of truth for "is this claim sourced"; never add a claim to a skill without either an
`F-`/`T-`/`REF-` citation or an explicit `proposed` marker.

### Examples are the target-state user view
`examples/<area>/` (run, ask, watch, steer, progress, done, improve — the order a user meets them) each
hold: `contract.py`/`contract` (the interface), `driver.py` (invokes it), `assessor.py` (judges the
result), `harnesses.py`, `entries/` (the four "doors": human, event, schedule, external — one envelope
shape), `units/`, `source/`. Every README carries six tables (ideal, standards, one call per door +
document, what the user sees, how it composes from the six compose operators, extension points/gaps).
The visible check (`test.sh`, author-written) and hidden check (`docs/night/hidden/<area>.sh`,
written by an isolated reviewer and run only at close) are deliberately separate — a gate the author
can see and tune is not the same evidence as one they can't.

### The ceremony/ledger discipline for changes
Sections of work close with a **review** record and an **improve** record under `kb/ceremonies/`
(`ceremony-<N>-review.json` / `-improve.json`), checked by `tools/check_ceremony.py` (every finding
applied or declined exactly once). `tools/plant.py` plants two known defects before a review and checks
the review caught them — a review that misses a plant is discarded and re-run. This is the mechanism
`tools/ceremony_check.py` tracks. Re-measured 2026-09-11: findings-per-skill fell 1.00 → 0.00 over
ceremonies 1–10 and rose to 0.29–0.50 at ceremony 11. The older "fell to 0.00–0.14" reading was
taken while that tool's glob could not see the suffixed records ceremonies 11 and 12 use, so the
window excluded the rise — run the command rather than quoting this line.

When closing a STATUS row, the pattern is: do the work → review → improve → ledger record →
`bash tools/checkpoint.sh "<row>: <summary>" <paths>`.

### Model routing (Part A of PASS.md, today's stack — not built by this repo)
Callers request a *model class* (e.g. `i-claude-sonnet`), never a vendor or specific model — this is the
principle the target architecture (`cap-model-access`) generalizes. See `PASS.md` A4 for the live routing
table if you need to understand what "today's adapter" means for the model-access capability.

## Known limits (don't re-litigate these as if they were oversights)

- ~30% of rows across every `skill.json` are `origin: proposed` (this repo's own design, not sourced
  fact) — under the declared 30% stick.
- No standard's version has been verified against its published spec: page fetch is blocked in this
  environment (STATUS rows 14, 45); all research records are `search-only`.
- Every harness's `live` adapter is claimed, not measured, for the same reason (STATUS row 37).
- Every reviewer to date has been a model (Sonnet or Opus); `HUMAN-REVIEW.md` is the checklist for the
  first human pass — use it to know what a person still needs to judge vs. what's machine-checked.
