---
name: compose-improvement-loop
description: The self-improvement loop as a composition: build-ceremony's review and improve steps that close a section seed candidate revisions of the producing skill, the author brief, or a discipline; a bounded compose-loop instance retries one candidate against cap-evaluation's gate until it passes or hits a ceiling; a passing candidate is promoted through cap-capability-registry with a rollback state, never edited into a running skill. Load it when a ceremony's applied finding is about to become a revision rather than a hand edit, when deciding whether a candidate may retry or must escalate, when wiring what is allowed to open a new iteration versus what may only steer one already running, when someone asks 'what proves this change actually helped' or 'why can this candidate not just be pushed live', and when reading this repository's own ceremony-01 through ceremony-10 records, state/lessons.jsonl or kb/ledger.jsonl as the measured instance of the loop this contract defines.
---

# compose-improvement-loop

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| build-ceremony states the self-improvement loop as TARGET fixes it (T-t4-04), and cap-evaluation cites the same quote as the reason its own reports and baselines are retained: a ceremony closes each section, re-reviews the output, and improves the skills that produced it. This composition's consequence is architectural, in service of TARGET's scale requirement that agents keep 'working together, managing state, breaking problems down, and self-improving where they can' (T-t6-06): turn a ceremony's applied findings, and cap-evaluation's own recorded regressions, into candidates that retry inside one bounded compose-loop instance and are promoted through cap-capability-registry only on a pass - so a revision can be refused, and 'self-improving' names a checkable pipeline rather than a session conducted carefully. | sourced | `T-t4-04`, `T-t6-06` "improves the skills that produced it, and the loop continues" |

## Entities

| Entity |
|---|
| `E-core-component-judge` |
| `E-core-component-planner` |
| `E-rule-b1-5` |
| `E-rule-b1-6` |
| `E-rule-b1-7` |
| `E-concern-budget` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| promote_revision (cap-capability-registry's publish, cited by name and reused unchanged) | a passed EvaluationReport, the candidate's content_ref, and rollback_to set to the target's currently resolved registry version (proposed) | cap-capability-registry already states that a change is a new version record, never an edit to the one that is there; the consequence here is that promote_revision writes only there, and the candidate's outcome - promoted with the record, or declined with the reason - is appended to the section's improve record and to kb/ledger.jsonl | sourced | `X-cap-capability-registry-007` "Mutable metadata are represented as new versioned records rather than in-place edits" |

### Shapes (JSON Schema 2020-12)

**ImprovementCandidate (proposed summary shape; keeps ceremony, finding_id and case_id spelled the way build-ceremony's review-record shape and cap-evaluation's EvaluationReport already spell them, so a ceremony finding and a loop candidate carry the same fields; the worked seed_candidate call for each of TARGET T1's three ways in, and the worked rejection, are in references/usage.md)** (proposed; sources: `T-t4-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:improvement-loop:candidate:0.1",
  "title": "ImprovementCandidate",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A candidate never carries the criterion or the case set it will be scored against, only the seed that justified authoring it.",
  "required": [
    "candidate_id",
    "ceremony",
    "target",
    "seed",
    "rationale",
    "status"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "ceremony": {
      "type": "integer",
      "minimum": 1,
      "description": "The build-ceremony number this candidate was seeded from or during."
    },
    "target": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind",
        "name",
        "ref"
      ],
      "properties": {
        "kind": {
          "enum": [
            "skill",
            "brief",
            "discipline"
          ]
        },
        "name": {
          "type": "string"
        },
        "ref": {
          "type": "string",
          "description": "Path or URI to the content this candidate revises."
        }
      }
    },
    "seed": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "kind",
        "ref"
      ],
      "properties": {
        "kind": {
          "enum": [
            "finding",
            "transition"
          ]
        },
        "ref": {
          "type": "string",
          "description": "A build-ceremony finding id, e.g. C9-001, or a cap-evaluation case_id."
        }
      }
    },
    "rationale": {
      "type": "string",
      "minLength": 1,
      "description": "The failure this candidate addresses. Never the rubric or case-set text."
    },
    "loop_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "The compose-loop instance this candidate is iterating inside."
    },
    "iteration_index": {
      "type": "integer",
      "minimum": 0,
      "default": 0
    },
    "content_ref": {
      "type": [
        "string",
        "null"
      ]
    },
    "status": {
      "enum": [
        "proposed",
        "gated",
        "promoted",
        "declined"
      ]
    }
  }
}
```

**CandidateOutcome (proposed summary shape); decision is exactly two values because a candidate still iterating has neither, and a third value would make an in-flight candidate misreadable as closed** (proposed; sources: `T-t4-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:improvement-loop:outcome:0.1",
  "title": "CandidateOutcome",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. What close_iteration writes to the section's improve record and to the ledger.",
  "required": [
    "candidate_id",
    "evaluation_report_id",
    "decision"
  ],
  "properties": {
    "candidate_id": {
      "type": "string"
    },
    "evaluation_report_id": {
      "type": "string",
      "description": "cap-evaluation's report_id for the gating run that decided this."
    },
    "decision": {
      "enum": [
        "promoted",
        "declined"
      ]
    },
    "reason": {
      "type": [
        "string",
        "null"
      ],
      "enum": [
        "iteration_ceiling",
        "budget_ceiling",
        null
      ],
      "description": "Set only when decision is declined."
    },
    "registry_record": {
      "type": [
        "object",
        "null"
      ],
      "additionalProperties": false,
      "properties": {
        "namespace": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "version": {
          "type": "string"
        },
        "digest": {
          "type": "string"
        },
        "rollback_to": {
          "type": [
            "string",
            "null"
          ]
        }
      },
      "description": "cap-capability-registry's own record; set only when decision is promoted."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| build-ceremony and cap-evaluation state this quote, each for its own record (T-t4-04): a section is not finished until the ceremony has re-reviewed the output and improved the producing skills. This composition's consequence: a candidate is seeded only from a finding_id in that closed review/improve pair, or from a transition cap-evaluation records against the current baseline - never from a candidate inventing its own justification mid-authoring. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| compose-loop states that a loop terminates on exactly one of three conditions and classifies a pass verdict as stop, the other two as cap, and that the two must never be collapsed (REF-5-3-08, F-b4-02). This composition's consequence: gate_revision's outcome maps onto that same enum unchanged - passed is verdict_pass, and failed inside the ceiling re-enters author_revision rather than closing anything - so a candidate still iterating is neither promoted nor declined. | sourced | `REF-5-3-08`, `F-b4-02` "`stop` firing means done. `cap` firing means escalate." |
| core-judge and cap-evaluation state design rule 6 (F-b1-07): the grader is never visible to the graded. This composition's consequence: author_revision's retry input is failed_check_ids and a verdict only, across every iteration of the same candidate_id - the loop is the place this rule is cheapest to break, because the obvious way to fix a candidate is to show it what it failed. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| cap-capability-registry states that a record is immutable and a change is a new version, never an edit in place. This composition's consequence: promote_revision never writes to a target's checked-out file; a passed candidate becomes a new registry record with rollback_to set to the resolved baseline, which is not yet how the skills in this repository are edited - a gap named as an open question and carried into compose-improvement-loop-implement. | sourced | `X-cap-capability-registry-007` "Mutable metadata are represented as new versioned records rather than in-place edits" |
| compose-loop states, following the reference example, that internal steers but never starts (REF-3-4-15, T-t4-04, T-t6-02). This composition's consequence: a running iteration may report a lesson into the rationale of the next candidate, but the compose-loop instance that gates and promotes a candidate is opened only by a person closing a ceremony, a schedule, or the outside event that produced the seed - never by author_revision or iterate_or_close themselves. | sourced | `REF-3-4-15`, `T-t4-04` "A loop that can mint its own root work has no provenance and no ceiling." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| core-judge and cap-evaluation state design rule 6 (F-b1-07): the grader is never visible to the graded. On this composition it forbids the case set and the rubric text gate_revision scores against from reaching author_revision's retry input, which carries a verdict and failed_check_ids only. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Close the section with build-ceremony first and read its closed review and improve records. Seed one ImprovementCandidate per finding or transition worth an automated gate rather than a direct hand edit - never from a justification authored mid-loop - naming target {kind, name, ref} and the seed, with a rationale that describes the failure and never the criterion behind it. | build-ceremony and cap-evaluation state this quote, each for its own record (T-t4-04): a section closes only once it has been re-reviewed and improved. A candidate with no such origin has invented its own reason to exist, which is exactly the unattributed change a ceremony exists to prevent; not every applied finding needs a candidate, but a finding that changes a contract, a shape or a definition of done is exactly the kind a gate should check before it ships. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| 2 | Author the revision's content_ref. On the first pass, author it from the finding or transition alone; on a retry, author it from the finding plus the prior EvaluationReport's verdict and failed_check_ids only, never with the case set. | core-judge owns the rule that the grader is never visible to the graded (F-b1-07); the consequence owned here is that this is the one step of the loop structurally placed to leak it, because it holds both the candidate and, on a retry, the verdict that came back. | sourced | `F-b1-07` "never the criterion it is judged against" |
| 3 | Wrap the retry in one compose-loop declaration before author_revision runs a second time: max_iterations, a per-iteration budget slice, exit_when naming gate_revision's verdict, on_cap escalate. agentic-stack and compose-loop state that planning is a pure function completed before execution begins (F-b1-06, F-b2-03). | Cost is knowable before commitment only because the ceiling is declared first; a candidate authored before its loop is declared is a retry with no bound on how many times it may fail. | sourced | `F-b1-06`, `F-b2-03` "Planning is a pure function and completes before execution begins." |
| 4 | Proposed: gate every iteration through cap-evaluation's evaluate against the target's registered case_set_id and the current baseline_id, in replay mode by default. Treat an inconclusive outcome exactly like failed for promotion purposes - never promote on a run that executed nothing. | cap-evaluation already states that outcome has three values so a run that executed nothing cannot read as a pass; the consequence here is specific to promotion, the one place in this loop where reading inconclusive as passing would be irreversible. | proposed | `T-t4-04` |
| 5 | On a failed outcome inside the ceiling, re-enter author_revision in the same loop_id and candidate_id with only the EvaluationReport's verdict and failed_check_ids - never with the case set, the rubric, or the record of the prior content_ref that was tried. | core-judge and cap-evaluation state design rule 6 (F-b1-07); a candidate that also saw its own prior attempts would be optimising against a map of what to avoid saying rather than what to avoid doing, which core-judge's invariant on leaked history already forbids at any depth. | sourced | `F-b1-07` "never the criterion it is judged against" |
| 6 | On a passed outcome, call cap-capability-registry's publish with rollback_to set to the target's currently resolved version. Append the CandidateOutcome to the section's improve record and to kb/ledger.jsonl; never write to the target's checked-out file. | cap-capability-registry states that a change is a new version record, never an edit to the one that is there; a promotion that writes to the checked-out skill.json instead is the exact defect compose-improvement-loop-implement's second executor - cap-evaluation's passed outcome as the sole promotion authority, cap-capability-registry's publish as the only write path - is chosen to close. | sourced | `X-cap-capability-registry-007` "Mutable metadata are represented as new versioned records rather than in-place edits" |
| 7 | Proposed: on iteration_ceiling or budget_ceiling, close as compose-loop's cap: record the candidate declined with the ceiling name as reason, escalate to a human, and never silently drop it or retry past the declared bound. | compose-loop already states that stop and cap are opposites and must not be collapsed; a declined candidate with no recorded reason reads, downstream, exactly like one nobody ever tried. | proposed | `REF-5-3-08` "`stop` firing means done. `cap` firing means escalate." |
| 8 | Feed every CandidateOutcome - promoted or declined, and why - into build-ceremony's carry operation: lessons_for_next_section always, and brief_changes when the candidate revised the author brief or a discipline rather than a single skill. | build-ceremony and cap-evaluation state this quote, each for its own record (T-t4-04); a candidate's outcome that never reaches the next ceremony's lessons is a finding the loop paid to discover twice, and cap-evaluation's own retained reports are the analogous record on the gate's side. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| 9 | Proposed: start a new root loop_id only when the trigger is a person closing a ceremony, a schedule, or an outside event such as a merge or a monitored regression. A candidate's own retry re-enters the loop_id it was seeded in and never opens a second one. | compose-loop already states, following the reference example, that internal steers but never starts; a self-improvement loop is exactly the case TARGET names this constraint for, because a loop that could mint its own root work would have no actor to attribute a promotion to and no ceiling to spend against. | proposed | `REF-3-4-15` "A loop that can mint its own root work has no provenance and no ceiling." |
| 10 | Proposed: measure the loop's own effect as a population trend, not a single run. Run `python3 tools/ceremony_check.py` over kb/ceremonies/*, state/lessons.jsonl and kb/ledger.jsonl before claiming the discipline is working, and read the printed findings-per-skill and proposed-row-share lines rather than one ceremony's outcome; this repository's own run is today's measured instance, and compose-improvement-loop-implement names the gaps between it and this contract. | Proposed: agentic-stack and build-definition-of-done already state that a criterion nothing can fail is not a criterion and that a structurally green run can mean nothing; a loop judged by its most recent ceremony alone could be improving on average and still look broken, or the reverse. | proposed | `F-part-c-04`, `F-a7-03` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: this repository's own ceremony trend, read with `python3 tools/ceremony_check.py`, is evidence the review/improve discipline works at all - block-plus-fix findings per skill fell from 1.00 at ceremony 1 to 0.07 or below by ceremony 4 and to 0.00 at ceremonies 8 and 10 - but the same trend names an unresolved defect this loop has not closed: the proposed-row share sits between 0.34 and 0.58 across all ten ceremonies with no consistent downward trend, so a rising share of what this repository states is not yet grounded in a source and no gate here catches that. | proposed | `F-part-c-04` |
| A defect a reviewer has corrected by hand in ceremony after ceremony is exactly what this loop exists to gate: TARGET T4 asks that a ceremony improve the skills that produced the output and that the loop continue - the line cap-evaluation cites for its own retained reports. build-ceremony owns the ceremony-number rule itself - a repository-global counter, never derived from a caller's position in its own run, and marked proposed there because no record fixes it - and this repository's state/lessons.jsonl shows that correction being re-applied by hand across at least five consecutive closed ceremonies, which is a candidate seed rather than a job for the next reviewer's memory. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Proposed: core-judge states that a judge grading with a model carries systematic biases - position, verbosity, self-preference - and should not grade its own model family's output without a bias control in the criterion set (X-core-judge-002). This repository's own ceremony 11 compose-group review names its reviewer as a single model with no held-out audit behind it - name this as an open defect rather than a settled property of the loop. | proposed | `X-core-judge-002` |
| Accept a self-modification only on measured evidence using two splits - a held-in split that checks the targeted weakness was resolved, and a held-out split the proposer never sees that checks nothing else regressed - rather than on the targeted case alone. | sourced | `X-compose-improvement-loop-006` "a held-in split that checks the targeted weakness was resolved, and a held-out split the proposer never sees that checks nothing else regressed" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/compose-improvement-loop/test.sh && python3 harness/compose-improvement-loop/conformance.py --adapter dryrun --report harness/compose-improvement-loop/out/measure-before.json && python3 harness/compose-improvement-loop/conformance.py --adapter second --report harness/compose-improvement-loop/out/measure-after.json && python3 harness/compose-improvement-loop/conformance.py --merge harness/compose-improvement-loop/out/measure-before.json harness/compose-improvement-loop/out/measure-after.json --report harness/compose-improvement-loop/out/measure-merged.json |
| Expected | exit 0, `passed 62, failed 0` from the gate, `ok   S5 both drivers passed their own conformance run   [25/25 and 25/25]` and `conformance PASSED: 5/5 cases, merged swap proof` from the merge. That covers the promote-only-on-pass rule, the iteration ceiling the declaration schema requires, and one candidate driven through two executors with no code edit between them. It is the gate compose-improvement-loop-implement owns; run here on 2026-09-03 and exited 0. Claimed, stated as the gap: tools/improvement_loop_conformance.py, the fixture ceremony and the candidate registry do not exist, so this facet's own counters - promoted + declined == 20 over seeded candidates, edited_in_place == 0, rollback_to set on every promoted record - have never been run, and this repository's review/improve half still edits target files in place, which is the defect the second executor exists to close. |
| Deliberate breakage | Make the default decision rule advance the checkpoint on every gate outcome, failed and inconclusive included, rather than only on a passed one, and restore the file afterwards. |
| Expected failure | exit 1 with `passed 47, failed 15`: the merged swap proof and the per-driver runs fail together because a candidate is promoted with no passing verdict behind it, while the declaration-schema checks - including the iteration ceiling - stay green, so the report names the promotion rule rather than the loop's bounds. Claimed here: the edit moves the driver binding compose-improvement-loop-implement owns; nothing on disk writes a registry record with rollback_to, so this facet's promotion counters cannot be made to fail today. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-evidence-record`, `build-ceremony`, `build-research-record`, `core-judge`, `cap-evaluation`, `cap-capability-registry`, `compose-loop`

Used by: `compose-improvement-loop-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is one ceremony finding one candidate, or can several findings against the same target become one candidate iteration? build-ceremony and cap-evaluation both state the quote below for their own record. | A closed ceremony whose applied list carries more than one finding against the same skill, replayed both ways through gate_revision, comparing whether a combined candidate's failed_check_ids are still attributable to one finding when it fails. | One finding, one candidate, so a declined outcome always names a single seed and a promoted outcome's rollback undoes exactly one change. | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Should a candidate that revises the author brief or a discipline skill be gated by cap-evaluation at all, given that neither has a registered case_set_id the way a capability skill's contract does? | A case set built from this repository's own closed ceremonies - replaying each ceremony's review against the brief version in force at the time and checking whether a later brief version reduces the same findings - would give brief_changes something to be gated against; none has been built. | A brief or discipline candidate is authored and recorded the way ceremonies already do it - a human or model author edits it and a ceremony reviews the result - and is not yet routed through gate_revision; this is a scope gap named here rather than silently assumed closed. | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Does the audit core-judge's contract already requires (a held-out re-grading of routine verdicts) apply to a ceremony's own findings, given that this repository's ceremonies today are graded by a single reviewing model with no stated bias control? | A sample of closed ceremony findings re-reviewed by a model outside the family that authored the section, with divergence counted the way core-judge's audit operation counts it against the routine judge. | No audit runs yet; the gap is named in this skill's invariants and best practices as a known, unresolved bias in today's adapter rather than assumed acceptable. | `F-b1-07` "The grader is never visible to the graded" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
