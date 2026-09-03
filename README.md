# AGENT

## What this is

| | |
|---|---|
| 1 | `PASS.md` states current state (Part A) and a target architecture (Part B): a five-piece core, capability interfaces, cross-cutting guarantees, and two seams. |
| 2 | `TARGET.md` extends that into a composability baseline; this repo is `PASS.md` Part B built out as 100 linked Claude Code skills under `docs/skill-manifest.json`, plus the `agentic-stack` root the manifest excludes by design (101 skill directories on disk), self-improved through 11 ceremonies. |
| 3 | Every claim a skill makes is either cited to a knowledge-base record with a verbatim quote, or marked `proposed`; nothing is asserted from memory. |

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

Each skill also names its `-implement` sibling (how to build it on this stack) under `composes_with`; load that when writing code, not just reading the contract.

## The layers

| Layer | Count | What it is |
|---|---|---|
| root | 1 | `agentic-stack` — vocabulary, the 7 design rules as tests, claimed vs. measured, definition of done. Every skill assumes it. |
| core | 10 | The 5 owned components — Document, Planner, Graph, Judge, Ledger — each an ideal + implement pair. |
| cap | 43 | One skill per capability interface (agent runtime, isolation, model access, errors, identity, …), each naming a standard, today's adapter, and a second adapter. `cap-consumption` is the one cross-capability member: the call shape every capability shares. |
| xc | 22 | 7 cross-cutting guarantees a caller cannot decline (budget, identity, policy, provenance, telemetry/correlation, errors, idempotency), each an ideal + implement pair. |
| seam | 4 | Dispatch and State — the 2 boundaries with no standard to adopt, so original design was warranted. |
| compose | 10 | Assembling workflows, loops, approvals and agents from the layers below; introduces no new interface. |
| build | 11 | Authoring disciplines every skill in this repo follows: definition of done with a breakage, adapter pairing, evidence recording, ceremony, skill authoring itself. |

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
| `kb/research.jsonl` | `X-` | 552 search records; every one is `search-only` — no page fetch has been verified in this environment |
| `kb/entities.jsonl` | `E-` | 184 named things the facts are about (capabilities, adapters, standards, …) |
| `kb/edges.jsonl` | `R-` (rel) | 109 typed links between entities, each citing the fact that states the link |
| `kb/ledger.jsonl` | `L-` | 28 append-only, hash-chained run records |

| To… | Run |
|---|---|
| Resolve any id | `python3 tools/kb.py show <id>` |
| Verify the chain and every fact's text against its source lines | `python3 tools/kb.py verify` |
| See counts by status/type | `python3 tools/kb.py stats` |

## The loop and ceremonies

| | |
|---|---|
| How a section runs | Research (`kb/research/*.jsonl`) → author a skill.json → render `SKILL.md` → validate, for each item in the section |
| How a section closes | A ceremony: a **review** record scores findings (`block`/`fix`/`nit`) against what the section produced, then an **improve** record marks each finding applied or declined with the files it touched, before the loop continues |
| Where records live | `kb/ceremonies/ceremony-<N>-review.json` and `-improve.json`; lessons folded into `state/lessons.jsonl` and `state/author-brief.md` |
| Count | 11 ceremonies — numbered 1 through 10, then ceremony 11 fanned into 3 parallel groups (`compose`, `xc`, `round2`) |
| Trend | `python3 tools/ceremony_check.py` — findings-per-skill fell from 1.00 (ceremony 1) to 0.00–0.14 by ceremony 8–10; proposed-row share held near 0.4–0.6 throughout |
| Also ran | A consolidation audit (`consolidation-review.json`) and apply (`-apply-A/B.json`) cut the plan from 127 to 99 skills in one pass; a reference pass (`reference-pass-01.json`) folded 9 gaps from the worked example into 9 skills |

## Tools

| Script | Purpose |
|---|---|
| `tools/kb.py` | Build/verify/query the knowledge base derived from `PASS.md`, `TARGET.md`, and the reference doc; append ledger records |
| `tools/render_skill.py` | Render `SKILL.md` from `skill.json` — tables only, every row carries its sources |
| `tools/validate_skills.py` | Check every skill against the schema, the knowledge base, and the root contract; errors block, warnings don't |
| `tools/manifest_facets.py` | Expand `docs/skill-manifest.json` into ideal/implement facets and emit the loop's sections |
| `tools/ceremony_check.py` | Show whether each ceremony validated and fed the self-improvement loop; print the trend |
| `tools/skill_graph.py` | Generate `docs/skill-graph.md` from every `skill.json` |
| `tools/gaps.py` | Aggregate research gaps into `docs/research/gaps.json`, and with `--apply`, add gap skills to the manifest |

## Definition of done

| Check | Command | Expected |
|---|---|---|
| Every skill valid | `python3 tools/validate_skills.py` | `101 skills checked, 0 errors, NEWWARN warnings` |
| Ceremonies fed the loop | `python3 tools/ceremony_check.py` | `numbering ok (contiguous from 1, one section each)` |
| Knowledge base intact | `python3 tools/kb.py verify` | chain and source-line checks pass |
| Reference example runs | `bash examples/end-to-end/test.sh` | `passed 30, failed 0` |
| Full picture | `kb/ceremonies/run-summary.json` | totals, trend, and known defects in one file |

## Known defects

| | |
|---|---|
| 1 | Proposed share is near half: 1458 of 2965 rows (49%) across every `skill.json` are `origin: proposed`, not `sourced`. |
| 2 | No standard's version has been verified against its published spec — all 552 research records are `search-only`; live page fetch was blocked. |
| 3 | The reviewer on every ceremony record is the same model family (`sonnet`) grading its own or a sibling instance's output — no independent or human reviewer. |
| 4 | Ceremony numbering drifted 9 times in a row (ceremonies 2–10); each had to renumber itself off the directory listing rather than trust the number it was handed. |
| 5 | Consolidation cut 127 planned skills to 99 in one same-day pass, not something caught incrementally across waves. |
| 6 | 2 skills (`cap-agent-runtime`, `cap-errors`) still exceed the checked 6–10 instruction budget; 35 "compose by name" warnings are unresolved. |
| 7 | 7 reviewer findings were declined outright with no independent check on the decision. |

Full detail: `kb/ceremonies/run-summary.json`.
