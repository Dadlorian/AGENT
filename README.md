# AGENT

## What this is

| | |
|---|---|
| 1 | `PASS.md` states current state (Part A) and a target architecture (Part B): a five-piece core, capability interfaces, cross-cutting guarantees, and two seams. |
| 2 | `TARGET.md` extends that into a composability baseline and the measuring sticks (T1 to T10); this repo is `PASS.md` Part B built out as 102 linked Claude Code skills (101 under `docs/skill-manifest.json` plus the `agentic-stack` root the manifest excludes by design), 28 harnesses that prove each stack element swaps behind its interface, and 16 integration guides. |
| 3 | Every claim a skill makes is either cited to a knowledge-base record with a verbatim quote, or marked `proposed`; nothing is asserted from memory. |
| 4 | `STATUS.md` is the owner's single view of what is open; `STATUS-ARCHIVE.md` holds every closed row with its commit. `OWNER.md` holds the owner's corrections, one line each. |

## How to use it

Open Claude Code in this repo. Skills load on demand from their `SKILL.md` frontmatter `description` — Claude Code matches your task against it and pulls in that skill plus what it names under `builds_on`.

| You want to work on | Load path |
|---|---|
| Anything in this repo | `agentic-stack` first, always — every other skill assumes it |
| What every caller sends and gets back | `agentic-stack` → `cap-consumption` |
| Driving a single agent turn | `agentic-stack` → `build-definition-of-done`, `build-adapter-pair`, `build-skill-authoring`, `cap-errors` → `cap-agent-runtime` |
| Running a unit of work isolated | `agentic-stack` → `build-definition-of-done`, `build-adapter-pair`, `build-skill-authoring`, `cap-errors` → `cap-isolation` |
| A cost ceiling on a run | `agentic-stack` → `build-definition-of-done`, `build-skill-authoring`, `cap-model-access`, `cap-errors` → `xc-budget` |
| Who is acting and on whose behalf | `agentic-stack` → `build-definition-of-done`, `build-skill-authoring`, `cap-identity` → `xc-identity-delegation` |
| Integrating one stack element | `docs/guides/<element>.md` — the standard, the operations, the adapters and a runnable step table, all pulled from the data |

Each skill also names its `-implement` sibling (how to build it on this stack) under `composes_with`; load that when writing code, not just reading the contract. `docs/architecture/load-path.md` lists what each of the four doors loads, against the budget of 11 skills per task.

## The layers

| Layer | Count | What it is |
|---|---|---|
| root | 1 | `agentic-stack` — vocabulary, the 7 design rules as tests, claimed vs. measured, definition of done. Every skill assumes it. |
| core | 10 | The 5 owned components — Document, Planner, Graph, Judge, Ledger — each an ideal + implement pair. |
| cap | 43 | One skill per capability interface (agent runtime, isolation, model access, errors, identity, …), each naming a standard, today's adapter, and a second adapter. `cap-consumption` is the one cross-capability member: the call shape every capability shares. |
| xc | 22 | 7 cross-cutting guarantees a caller cannot decline (budget, identity, policy, provenance, telemetry/correlation, errors, idempotency), each an ideal + implement pair. |
| seam | 4 | Dispatch and State — the 2 boundaries with no standard to adopt, so original design was warranted. |
| compose | 10 | Assembling workflows, loops, approvals and agents from the layers below; introduces no new interface. |
| build | 12 | Authoring disciplines every skill in this repo follows: definition of done with a breakage, adapter pairing, evidence recording, ceremony, solution architecture, skill authoring itself. |

`docs/skill-graph.md` draws the `builds_on` edges as focal groups, each kept under the mermaid rendering limits.

## The harnesses and guides

| | |
|---|---|
| Where | `harness/<name>/` — 28 of them, listed in `harness/plan.json` |
| What each holds | `interface.py` (no product names), three adapters (`dryrun`, `live`, `second`), `call.py` (the minimal caller), `conformance.py`, `test.sh` (the gate with one deliberate breakage), `README.md` (a step table), `provenance.json` (measured vs. claimed, kb ids) |
| Run one | `bash harness/<name>/test.sh` → `passed N, failed 0`; then `ADAPTER=second python3 harness/<name>/call.py` runs the same caller on the other execution model |
| Guides | `docs/guides/<element>.md`, one per stack element in `PASS.md` B3, rendered by `tools/render_guide.py` from the skill data and the harness step table; 16 of 16 runnable |
| Acceptance | `docs/acceptance/matrix.md` walks five sticks (sourced, measured, swap, standard, guide) down every element; 16 of 16 accepted, the standard stick recorded absent by the owner in `absent.json` because page fetch is blocked |
| Live mode | Every harness's `live` adapter is claimed, not measured: it has never run against the host from a session (STATUS row 37) |

## The end-to-end example

| | |
|---|---|
| Where | `examples/end-to-end/` — dependency-free Python, no network by default |
| What | 4 entries (`human`, `event`, `schedule`, `external`) into 1 envelope shape, 1 workflow using every operator once, 1 hash-chained ledger |
| Run it | `bash examples/end-to-end/test.sh` → `passed 30, failed 0` |
| Reference doc | `docs/reference/composable-plan.md` — one team's worked example of a composable plan (four doors, nesting, fan-out, late binding); an illustration, not a definition — cited as `REF-` ids |
| Grading discipline | `.claude/skills/build-worked-example/` — the 6 questions every example answers and the 6 criteria it's graded on |

## Knowledge base and provenance

| File | ID prefix | Holds |
|---|---|---|
| `kb/facts.jsonl` | `F-` | One record per row/item in `PASS.md`, hash-chained to its exact source lines |
| `kb/target-facts.jsonl` | `T-` | One record per numbered requirement in `TARGET.md` |
| `kb/reference-facts.jsonl` | `REF-` | `docs/reference/composable-plan.md`, status `reference` — an example followed, never a fact |
| `kb/research.jsonl` | `X-` | 555 search records merged from `kb/research/*.jsonl`; every one is `search-only` — no page fetch has been verified in this environment |
| `kb/entities.jsonl` | `E-` | 184 named things the facts are about (capabilities, adapters, standards, …) |
| `kb/edges.jsonl` | `R-` (rel) | 109 typed links between entities, each citing the fact that states the link |
| `kb/decisions.jsonl` | `D-` | 110 decisions lifted from `docs/decomposition.md` by line |
| `kb/architecture.jsonl` | `A-` | 803 blueprint entries imported from `docs/architecture/blueprint.json` |
| `kb/ledger.jsonl` | `L-` | 190 append-only, hash-chained run records; every measured run, ceremony and phase close |
| `kb/ceremonies/` | | 98 records: sourcing, measure, review and improve, named by the STATUS row they served |

| To… | Run |
|---|---|
| Resolve any id | `python3 tools/kb.py show <id>` |
| Verify the chain and every fact's text against its source lines | `python3 tools/kb.py verify` |
| Verify the ledger | `python3 tools/kb.py ledger-verify` |
| See counts by status/type | `python3 tools/kb.py stats` |

## The loop and ceremonies

| | |
|---|---|
| The first build | Research (`kb/research/*.jsonl`) → author a `skill.json` → render `SKILL.md` → validate, per section; each section closed with a **review** record and an **improve** record (`kb/ceremonies/ceremony-<N>-review.json`, `-improve.json`), 11 ceremonies |
| The acceptance phases | STATUS rows 59 to 63, one per layer group, each running the nine-step ceremony in `docs/acceptance/ceremony.json`: claim, source, measure, plant two defects, review, plant check (a review that misses a plant is discarded), improve, lessons, close |
| Naming | Every agent, scope claim and record is named by its STATUS row id (`61-review-c`), per `OWNER.md` |
| Where lessons go | `state/lessons.jsonl` (17 rows) and `state/author-brief.md`; the briefs a crew reads are under `state/briefs/` |
| Trend | `python3 tools/ceremony_check.py` — findings-per-skill fell from 1.00 (ceremony 1) to 0.00–0.14 by ceremonies 8–10 |

## Human review

`HUMAN-REVIEW.md` is the checklist: for every folder, what it holds, the command that checks it by machine, what only a person can judge, and what a problem looks like. It starts with six commands that cover the whole repo, and ends with where a finding is recorded (a line in `OWNER.md`, a review record under `kb/ceremonies/`, or a decision on a Blocked row in `STATUS.md`).

| Folder | Checked by | A person judges |
|---|---|---|
| `.claude/skills/` | `tools/validate_skills.py`, `tools/check_adapter_pairs.py`, `tools/skill_graph.py` | does the quote support the statement; would the description load on the right task; is the criterion runnable |
| `kb/` | `tools/kb.py verify`, `ledger-verify` | do the research urls resolve to what was recorded |
| `kb/ceremonies/` | `tools/check_ceremony.py`, `tools/ceremony_check.py` | were declined findings rightly declined; did every kept review catch its plants |
| `harness/` | `bash harness/<name>/test.sh`, `conformance.py` | is the second adapter a real second execution model; does the breakage assert failure |
| `docs/` | `tools/acceptance_check.py --check`, `tools/render_guide.py --check`, `tools/blueprint_check.py` | do you still accept the sticks recorded absent; does a guide's step table work by hand |
| `examples/end-to-end/` | `bash examples/end-to-end/test.sh` | does the example satisfy the ids its provenance claims |
| `state/` | `tools/status_check.py --freshness` | are the briefs the method you want; should the grandfathered list be emptied |
| root files | `tools/status_check.py` | are the sticks, rules and Blocked rows still your decisions |

## Tools

| Script | Purpose |
|---|---|
| `tools/kb.py` | Build/verify/query the knowledge base derived from `PASS.md`, `TARGET.md`, and the reference doc; append and verify ledger records; import the blueprint |
| `tools/render_skill.py` | Render `SKILL.md` from `skill.json` — tables only, every row carries its sources |
| `tools/validate_skills.py` | Check every skill against the schema, the knowledge base, and the root contract; errors block, warnings don't |
| `tools/measure.py` | Run a skill's definition of done with its breakage and restore; the only writer of `status: measured` |
| `tools/expected_from_measured.py` | Make a measured definition of done's expected texts quote its own run; `--check` reports drift |
| `tools/check_adapter_pairs.py` | Check every `cap-` and `seam-` skill has a today adapter and a differing second adapter |
| `tools/plant.py` | Plant two known defects before a review, check the review caught them, remove them |
| `tools/check_ceremony.py` | Check a review record against its improve record: every finding applied or declined once, every touched file exists |
| `tools/ceremony_check.py` | Show whether each loop ceremony validated and fed the self-improvement loop; print the trend |
| `tools/scopes.py` | Claim and release agent scopes; refuses overlapping paths and labels that do not start with a live STATUS row id |
| `tools/status_check.py` | Keep `STATUS.md` one clean table; `--freshness` finds stale claims |
| `tools/status_archive.py` | Move Done rows to `STATUS-ARCHIVE.md` with the closing date and commit |
| `tools/acceptance_check.py` | Derive `docs/acceptance/matrix.md` from the facts, standards, plan, skills and guides; `--check` finds hand edits |
| `tools/render_guide.py` | Render `docs/guides/<element>.md` from the skill data and the harness step table; `--check` finds hand edits |
| `tools/harness_accept.py` | Accept one finished harness: run its gate, merge its plan entry, release its claims, regenerate matrix and guides |
| `tools/final_acceptance.py` | Derive every T9 and T10 stick at one commit; `--write` stores `docs/acceptance/final.json` |
| `tools/blueprint_check.py` | Hold `docs/architecture/blueprint.json` to the source-of-truth rule |
| `tools/skill_graph.py` | Generate `docs/skill-graph.md` from every `skill.json` as focal groups, each counted against the mermaid edge and text limits; exit 1 when one would not render |
| `tools/manifest_facets.py` | Expand `docs/skill-manifest.json` into ideal/implement facets and emit the loop's sections |
| `tools/gaps.py` | Aggregate research gaps into `docs/research/gaps.json`, and with `--apply`, add gap skills to the manifest |

## Definition of done

| Check | Command | Expected |
|---|---|---|
| Every skill valid | `python3 tools/validate_skills.py` | `102 skills checked, 0 errors, 0 warnings` |
| Knowledge base intact | `python3 tools/kb.py verify` | chain and source-line checks pass |
| Ledger intact | `python3 tools/kb.py ledger-verify` | `190 records, chain intact` |
| Every stick holds | `python3 tools/final_acceptance.py` | `15 of 15 hold` (runs all 28 harness gates) |
| Acceptance matrix current | `python3 tools/acceptance_check.py --check` | `16 of 16 elements accepted, 80 of 80 sticks hold` |
| Status fresh | `python3 tools/status_check.py --freshness` | `0 stale` |
| Reference example runs | `bash examples/end-to-end/test.sh` | `passed 30, failed 0` |
| Scorecard at one commit | `docs/acceptance/final.json` | the commit it names and every row `holds: true` |

## Known limits

| | |
|---|---|
| 1 | 810 of 2725 rows across every `skill.json` (29.7%) are `origin: proposed`: this repo's own design, under the 30% stick, not sourced facts. |
| 2 | No standard's version has been verified against its published spec: all 555 research records are `search-only`, because page fetch is blocked here (STATUS rows 14 and 45). The standard stick is recorded absent by the owner for all 16 elements. |
| 3 | Every harness's live adapter is claimed, not measured; no run has reached the host from a session (STATUS row 37). |
| 4 | 47 of 102 definitions of done are still claimed; 55 have a measured run. |
| 5 | Every reviewer to date is a model (Sonnet or Opus); one Sonnet review missed both planted defects and was discarded and re-run. `HUMAN-REVIEW.md` is the first human pass. |
| 6 | `state/grandfathered.json` lists all 102 skills, exempting them from two validator rules that no skill currently needs. |
| 7 | The skill layout (102 skills, ideal/implement pairs) awaits the owner's choice among the options in `kb/ceremonies/64-structure-review.json` (STATUS row 64). |
