---
name: build-skill-authoring
description: How to author a skill in this repository as data rather than prose: a skill.json conforming to schemas/skill.schema.json, rendered to SKILL.md, with every statement either cited to knowledge-base ids and anchored by a verbatim quote, or marked proposed. Load this before writing or changing any skill here, before adding a skill to docs/skill-manifest.json, before adding a layer prefix or touching the schema or the validator, and when onboarding an author who has not written a skill in this repo. Covers finding kb records before writing a claim, the field order the schema lists, honest proposed marking, a description that says when to load, choosing builds_on narrowly and keeping links symmetric with the manifest, wave ordering for a new skill, the progressive-disclosure budget and when long material moves to references/, and the render-then-validate loop that must end at zero errors.
---

# build-skill-authoring

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Package each piece of this repo as a spec-conformant skill rather than prose: it names the capability and the standard that governs it with a version, and never a product, so a tool or a registry we did not write can read it. | sourced | `F-b3-07`, `F-part-c-09`, `F-part-c-10` "any spec-conformant registry" |

## Entities

| Entity |
|---|
| `E-capability-capability-packaging` |
| `E-standard-agent-skills-spec` |
| `E-constraint-c-constraint-203` |
| `E-constraint-c-constraint-204` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-agent-skills-spec` | version unverified | unverified | - | `F-b3-07` |

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: every skill is a directory under .claude/skills containing skill.json; SKILL.md is the render of that file and is never edited by hand, so the prose cannot drift from the data. Research query: capability-packaging spec conventions for whether a package's rendered documentation must be a generated artifact rather than a hand-authored file. | proposed | - |
| Proposed: every statement in a skill carries exactly one origin. origin=sourced requires at least one F-, E- or R- id and a quote that is a verbatim substring of one cited record; origin=proposed requires the word proposed in its own text. There is no third kind, and an unmarked sentence is a validation error, not a style problem. Research query: spec-conformant packaging literature on requiring exactly one of a cited-evidence or a marked-design status per statement, with no unmarked third state. | proposed | - |
| Claimed and measured are kept apart per row: a definition of done is status claimed until someone ran it and said where and when, and rewording never upgrades it. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Every skill carries a definition of done with a machine-checkable criterion and the deliberate breakage that proves the criterion can fail. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| No product, vendor or hostname appears in any field except adapters[]; a skill with no adapters names none anywhere. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| Every standard a skill cites is named together with its version, and an existing standard is preferred to an original design; each interface names the standard that governs it. | sourced | `F-part-c-10`, `F-b1-03` "Cite the standard and its version" |
| Proposed: where a version has not been read from the published spec in this environment, the skill writes version_status unverified and the literal phrase version unverified rather than a number, because an invented version is a fabrication that reads exactly like a fact. Research query: standards-tracking practice on the literal placeholder a spec-conformant record writes when a cited standard's version was never fetched. | proposed | - |
| Proposed: every skill records the PASS.md sha256 and the three knowledge-base chain heads it was built against, and its composes_with equals its docs/skill-manifest.json entry exactly, so a stale or unlinked skill fails validation instead of passing quietly. Research query: provenance-chain practice on binding a generated artifact's declared dependency links to a single source-of-truth manifest rather than letting them diverge. | proposed | - |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the knowledge-base text itself is not republished inside a skill. A row carries ids plus one verbatim quote; a reader who needs the rest runs python3 tools/kb.py show <id>, which keeps the skill short and keeps PASS.md the single copy. Research query: capability-packaging spec on whether a package should embed its cited source text or only a resolvable reference to it. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Load the agentic-stack root contract, then read your skill's entry in docs/skill-manifest.json: layer, wave, purpose, builds_on, used_by, definition_of_done row and notes_for_author. Not externally researchable: this is this repo's own manifest-first authoring order (docs/skill-manifest.json before skill.json). | Proposed: those fields are already decided by docs/decomposition.md, and the validator compares your composes_with against the manifest entry exactly. Deciding them again in skill.json only produces an error. | proposed | - |
| 2 | Run `python3 tools/kb.py verify`, then copy source.sha256 and the three heads from kb/meta.json into provenance.kb_source_sha256 and provenance.kb_heads. | A skill built against a stale knowledge base cites text that no longer matches PASS.md. The chained digests make an edit between runs detectable, and the validator refuses a skill whose provenance does not match the current chain. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| 3 | Find the records before writing the claim: `python3 tools/kb.py tree` for the entity graph, `grep -n '"section": "B3"' kb/facts.jsonl` to reach a section, then `python3 tools/kb.py show <id>` to read one record's exact text, line range and status. | The record carries the status PASS.md gave it. Restating from memory is how a target becomes a fact and a claim becomes a measurement. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 4 | Write skill.json in the order schemas/skill.schema.json lists its properties: name, layer, wave, description, purpose, entities, contract, instructions, best_practices, adapters, definition_of_done, composes_with, open_questions, provenance. Omit an optional block rather than filling it with padding, and write the description to say both what the skill covers and the situations that must load it, in 40 to 1024 characters, naming the triggering artifacts (a file, a layer, a schema, an onboarding author) rather than a topic. Research query: JSON Schema authoring practice on writing an object's fields in the order its schema declares them, for diffability. | Proposed: a fixed order makes two skills diffable against each other and makes a missing block visible at a glance, and the schema's additionalProperties:false rejects any field you invent. The description is the only part read before the skill is loaded, so a vague one means the skill is never opened at the moment it was needed. | proposed | - |
| 5 | For each statement pick one origin and stop. origin=sourced: list the ids you actually read and set quote to a span you copied out of one of them character for character. origin=proposed: say proposed in the text and claim nothing about PASS.md. Research query: citation-checking practice on requiring a quote to be copied character for character rather than retyped from memory. | Proposed: the quote is checked as a substring of a cited record, so a paraphrased quote fails; and a proposed row that omits the word reads as sourced to a human even though no id backs it. | proposed | - |
| 6 | Name capabilities and standards in every field, and confine product, vendor and version names to adapters[]. If your skill has no adapters, it names no products at all. | A product name in a contract row means an adapter has leaked into the architecture, and the validator scans the rendered SKILL.md for a fixed product list outside the Adapters section. | sourced | `F-part-c-09`, `F-part-c-10` "name capabilities and standards, never products" |
| 7 | Fill definition_of_done with a runnable command, the expected output, a concrete breakage a person could apply, and the exact failure it produces. Set status measured only if you ran both here and the expected_failure says in which session and on what date; otherwise claimed. | A criterion nothing can fail is not a criterion, and a status of measured with no run behind it is the fabrication the claimed-versus-measured rule exists to prevent. | sourced | `F-part-c-04`, `F-part-c-08` "A criterion nothing can fail is not a criterion" |
| 8 | Set composes_with.builds_on and composes_with.used_by to the manifest entry's lists, unchanged. Choose builds_on narrowly: name only the skills whose contract you actually rely on, never the whole layer. Research query: dependency-graph practice on keeping a composed unit's builds_on link list narrow to what its contract actually uses, versus naming a whole layer. | Proposed: these links are the architecture graph, the validator requires them symmetric and equal to the manifest, and a skill that builds on everything forces a reader to load everything, which defeats loading skills narrowly. | proposed | - |
| 9 | To add a skill that is not in the manifest: add it to docs/decomposition.md first, then to docs/skill-manifest.json with name, layer, wave, purpose, builds_on, used_by, a definition_of_done row and notes_for_author, adding this skill's name to the used_by list of each skill it builds on; its wave must be strictly greater than the wave of everything in its builds_on. Add a new layer prefix only when none of the seven existing layers can hold it - root (reserved for the root contract alone, which the schema and the validator allow for no other skill), core, cap, xc, seam, compose, build - and then edit the schema's name pattern and layer enum, LAYERS in tools/validate_skills.py, and the layers block in docs/skill-manifest.json in the same change. Research query: layered-architecture practice on when a new top-level partition is warranted versus fitting a new unit into an existing one. | Proposed: the manifest is generated from the decomposition and must not drift from it; a wave that does not exceed its dependencies claims a skill can be authored before the contract it quotes exists, and the validator rejects the asymmetric half of a one-sided link. The prefix set is the top-level partition of the repo, so an eighth layer re-partitions every existing skill's meaning: a skill that merely feels new almost always belongs to an existing layer, and root is not available, it is taken. | proposed | - |
| 10 | Keep the rendered SKILL.md inside the progressive-disclosure budget: hold to roughly 3 to 10 rows per table, and move long material (a full schema, a table of standards, worked examples) into references/ inside the skill directory, named from the row that points at it. If the material you planned for references/ was dropped or never needed, delete the directory: an empty references/ is dead scaffolding, and the validator warns about it. Then render with `python3 tools/render_skill.py .claude/skills/<name>` and run `python3 tools/validate_skills.py`, fixing every error and every warning naming your skill; only warnings about skills not written yet may remain. Research query: progressive-disclosure practice on a numeric per-table row ceiling for a rendered reference document, and when material must move to a linked file. | Proposed: SKILL.md is loaded whole whenever the skill is loaded, so material a reader needs only sometimes should cost nothing until it is opened - and it is a build artifact of skill.json, so the validator re-renders your data and compares, and a hand edit to SKILL.md is reported as stale rather than silently kept. The budget is a checked warning, not advice: this skill was itself over it at 13 instructions until ceremony 6. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: one purpose per skill. If the purpose sentence needs an and, it is two skills; splitting keeps each one loadable on its own and keeps the links meaningful. Research query: software-module design practice on one-responsibility-per-unit as a splitting rule (the 'and' test) for reusable components. | proposed | - |
| Proposed: compose by name, not by copy. A skill names its neighbour under builds_on and cites the same knowledge-base ids; it never restates the neighbour's rows, so a change lands in one place. Not externally researchable: this is the compose-by-name-not-by-copy rule this repo's own author brief and validator state as a defect check. | proposed | - |
| Keep products out of every field but adapters[]: a product name in a purpose, invariant or instruction is the signal that the skill has been written around today's implementation instead of the contract. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| Do not restate a fact a skill under builds_on has stated elsewhere. The green-gate finding - that a deterministic gate can be structurally green and mean nothing, because those checks establish well-formedness, not correctness - is held once in the agentic-stack root contract (F-a7-03); cite it from there and add only what is new here, namely that a skill's check asserts on a non-zero count of things actually checked rather than on an exit code. | sourced | `F-a7-03` "Those establish well-formedness, not correctness." |
| Record what you could not source as an open question with the evidence that would decide it and the default until then, instead of filling the gap with a plausible sentence. | sourced | `F-part-c-06` "A required output, not an apology" |
| Proposed: a contract.standards row's version field is a value a reader scans, not the sentence explaining it. Put the version string a record actually names, or 'unverified', in version; put which record named it, whether the specification was fetched, and which skill owns the row in version_note, which renders as a footnote under the Standards table. The validator warns above 60 characters. Research query: technical-writing practice on separating a scannable value field from its justifying footnote in a rendered table. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/render_skill.py .claude/skills/build-skill-authoring && python3 tools/validate_skills.py` |
| Expected | rendered build-skill-authoring/SKILL.md, then 'N skills checked, 0 errors' with no error line naming build-skill-authoring; the only warnings are manifest skills not written yet |
| Deliberate breakage | In a copy of .claude/skills/build-skill-authoring/skill.json, apply three mutations one at a time and re-run the validator: (a) delete the sources array from contract.invariants[2] while leaving origin=sourced; (b) change one character of that invariant's quote; (c) delete one name from composes_with.used_by so the link no longer matches the manifest. |
| Expected failure | (a) '.contract.invariants[2] is origin=sourced but has no sources' together with '.contract.invariants[2].quote is not a verbatim substring of any cited record'; (b) ".contract.invariants[2].quote is not a verbatim substring of any cited record: 'Distinguish **claimed** from **measured** throughOut'"; (c) 'composes_with differs from docs/skill-manifest.json'. Every mutated run also reports 'SKILL.md is not the render of skill.json' and exits 1. Measured in session claude/auto-skill-creation-i8javu on 2026-09-03: the three mutations exited 1 with 4, 3 and 3 errors and those exact strings; the restored file re-rendered and exited 0 with no error naming this skill. |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: `build-entry-conformance`, `build-interface-versioning`, `build-simplicity-budget`, `cap-agent-runtime`, `cap-capability-packaging`, `cap-capability-registry`, `cap-document-validation`, `cap-durable-execution`, `cap-errors`, `cap-evaluation`, `cap-human-interaction`, `cap-idempotency`, `cap-identity`, `cap-isolation`, `cap-mandate-broker`, `cap-memory`, `cap-model-access`, `cap-policy`, `cap-provenance`, `cap-scheduling`, `cap-state-persistence`, `cap-telemetry`, `cap-tool-access`, `cap-work-intake`, `compose-agent`, `compose-approval`, `compose-improvement-loop`, `compose-loop`, `compose-operators`, `core-document`, `core-graph`, `core-judge`, `core-ledger`, `core-planner`, `seam-dispatch`, `seam-state`, `xc-audit-trail`, `xc-budget`, `xc-compensation`, `xc-correlation`, `xc-enforcement-chain`, `xc-idempotency-lease`, `xc-identity-delegation`, `xc-policy-gate`, `xc-provenance-chain`, `xc-tenancy`, `xc-typed-errors`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What version of the packaging spec that governs a skill file should this repo cite? | A fetch of the spec's canonical URL recording its version string and publication date; documentation fetches were blocked from this environment, so no version was read. | The standard is recorded with version_status unverified and the literal phrase version unverified, and no number is written. | `F-b3-07`, `F-part-c-10` "Cite the standard and its version" |
| Should the three sibling authoring disciplines list one another under composes_with, given that each is itself authored under this skill's rules? | A decision in docs/decomposition.md on whether wave-1 skills may link to each other; the manifest currently gives every wave-1 build- skill builds_on agentic-stack only and no build- skill in any used_by list. | Follow the manifest exactly and leave the sibling links absent, because the validator requires composes_with to equal the manifest entry. | `F-part-c-06` "A required output, not an apology" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
