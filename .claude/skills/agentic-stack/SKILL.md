---
name: agentic-stack
description: Root contract for building the agentic platform in PASS.md. Load first whenever work touches the platform: its core (Document, Planner, Graph, Judge, Ledger), any capability interface, standard, or adapter, the Dispatch or State seams, a cross-cutting guarantee, a workflow, loop, or agent composition, or any skill in this repo. Fixes the vocabulary, the seven design rules as pass/fail tests, claimed versus measured labeling, the definition of done, and how skills cite the knowledge base. Every other skill assumes this one is loaded.
---

# agentic-stack

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn PASS.md Part B into linked skills without inventing facts: every statement cites a knowledge-base record derived from PASS.md, and everything that is ours is marked proposed. | sourced | `F-meta-02`, `F-meta-03`, `F-meta-04`, `F-part-c-08` "Part A names products. Part B names capabilities and the standard that governs each" |

## Entities

| Entity |
|---|
| `E-rule-b1-1` |
| `E-rule-b1-2` |
| `E-rule-b1-3` |
| `E-rule-b1-4` |
| `E-rule-b1-5` |
| `E-rule-b1-6` |
| `E-rule-b1-7` |
| `E-core-component-document` |
| `E-core-component-planner` |
| `E-core-component-graph` |
| `E-core-component-judge` |
| `E-core-component-ledger` |
| `E-seam-dispatch` |
| `E-seam-state` |
| `E-finding-a7-1` |
| `E-finding-a7-2` |
| `E-finding-a7-3` |

## Contract

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Rule 1 as a test: does the core import only interfaces? A product name inside core code, core docs, or a core skill fails. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| Rule 2 as a test: does each interface name its governing standard? An interface without a cited standard is either mis-drawn or belongs in B5. | sourced | `F-b1-03`, `F-b5-01` "Each interface names the standard that governs it" |
| Rule 3 as a test: does the interface ship with two adapters, the second different enough to prove the first is not load-bearing? | sourced | `F-b1-04` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing" |
| Rule 4 as a test: can a caller integrate with nothing we wrote? A required client library of ours means the boundary is bespoke. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| Rule 5 as a test: is cost known before execution starts? Planning is a pure function that completes before execution. | sourced | `F-b1-06`, `F-b2-03` "Planning is a pure function and completes before execution begins" |
| Rule 6 as a test: is the grading criterion hidden from the thing graded? An agent sees its outcome, never the criterion. | sourced | `F-b1-07`, `F-b2-05` "An agent sees its outcome, never the criterion it is judged against" |
| Rule 7 as a test: are telemetry, policy, provenance, and budget applied by the platform with no opt-out? | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| Part A names products. Part B names capabilities and standards. If Part B cannot swap an implementation without touching the core, the boundary is wrong. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| The core is exactly Document, Planner, Graph, Judge, Ledger. Zero outward dependencies. Everything else is an adapter. | sourced | `F-b2-01`, `F-b2-07` "This is the entire owned surface. Everything else is an adapter." |
| Dispatch and State are the only boundaries with no standard to adopt and the only places original design is warranted. | sourced | `F-b5-01`, `F-b5-06` "Two boundaries have no standard to adopt" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Products, versions, and hostnames do not appear in core, interface, or composition material. They belong in adapter columns only. | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Run `python3 tools/kb.py verify` before citing anything. If it fails, rebuild with `python3 tools/kb.py build` and re-check every skill's provenance heads. | A fact is only sourceable while the knowledge base still matches PASS.md byte for byte. The chain and file hash make a silent edit detectable, the same idea as the hash-chained task store. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| 2 | Resolve every id you rely on with `python3 tools/kb.py show <id>` and read the exact text and its line range before restating it. | Restating from memory is how claims get upgraded to measurements. The record carries the status derived from the text; keep it. | sourced | `F-part-c-08`, `F-a7-01` "Distinguish **claimed** from **measured** throughout" |
| 3 | Write skills as `skill.json` conforming to `schemas/skill.schema.json`; render SKILL.md with `python3 tools/render_skill.py <dir>`; never edit SKILL.md by hand. | Proposed: our convention. A rendered file cannot drift from its data, and the validator rejects one that does. | proposed | - |
| 4 | Mark every statement origin=sourced with at least one F-, E-, or R- id, or origin=proposed with the word proposed in the text. | Proposed: our convention. The reader must be able to tell, per row, what PASS.md says and what we added. | proposed | - |
| 5 | Name capabilities and standards everywhere except the Adapters section. Cite a standard's version, or write unverified. | Products in the core mean the adapter has leaked into the architecture. An invented version number is a fabrication. | sourced | `F-part-c-09`, `F-part-c-10`, `F-b1-03` "name capabilities and standards, never products" |
| 6 | Give every piece a definition of done with a machine-checkable criterion, a deliberate breakage, and the status of both (claimed until run). | A criterion nothing can fail is not a criterion. A green gate can be structurally green and mean nothing. | sourced | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion" |
| 7 | Fill composes_with with exact skill names from docs/skill-manifest.json and run `python3 tools/validate_skills.py` until it reports zero errors. This root skill is the one exception: its own composes_with is empty by design, so read 'Builds on: -' and 'Used by: -' here as 'exempt', not as 'unused' - every other skill lists agentic-stack under builds_on and the validator exempts the root from the used_by symmetry check. | Proposed: our convention. The links are the architecture graph; the validator checks they are symmetric and that nothing is cited that does not exist. Listing every skill in the root's used_by would restate the whole manifest in a file that changes on every new skill. | proposed | - |
| 8 | Treat Part A as substrate. Do not propose replacing what runs; describe it only as today's adapter. | The ask constrains it, and Part B's own framing says today's components appear only as adapters. | sourced | `F-part-c-11`, `F-meta-03`, `F-part-b-01` "Part A is substrate, not scope. Do not propose replacing what runs." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Correlation must ride on an explicit resource attribute set at dispatch, because trace context did not survive the agent boundary when tried. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| Well-formedness checks (diff, syntax, format) are not correctness checks; a gate whose behavioural stages all skipped proves nothing. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Configuration written in the documented place can be silently overridden by a stored row; verify runtime effect, not file contents. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Callers request a class of model, never a vendor; the prefix carries the contract. | sourced | `F-a4-01` "Callers request a class, never a vendor" |
| Load skills narrowly: this one, then the layer skill for the piece in hand, then only the neighbours it names under composes_with. (proposed: our convention, not in PASS.md) | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/kb.py verify && python3 tools/validate_skills.py |
| Expected | kb verified; N skills checked, 0 errors |
| Deliberate breakage | Change one character of one fact's text in kb/facts.jsonl (the record no longer hashes to its stored digest), run the criterion (tools/kb.py verify reports the chain broken and exits non-zero), then git checkout kb/facts.jsonl. |
| Expected failure | kb verify: 'FAIL: chain broken at facts F-meta-01' and 'text does not match PASS.md lines 3-3'; validate_skills: 'cites unknown id F-none-99' and 'quote is not a verbatim substring'. Measured in session claude/auto-skill-creation-i8javu on 2026-09-03; both breakages exited 1 and the restored state exited 0. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: -

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which standards' versions can be verified against their published specs from this environment? | A fetch of each standard's canonical URL recording the version string and the date; the proxy blocked documentation fetches in this session. | Every standard is recorded as version unverified until fetched. | `F-part-c-10` "Cite the standard and its version" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
