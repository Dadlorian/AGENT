---
name: "build-ceremony"
description: "Close a section with a ceremony: a review record of findings, then an improve record marking each applied or declined with the files touched. Load it when a wave or section ends, when writing or checking a record under kb/ceremonies/, and for the pre-build solution blueprint (formerly build-solution-architecture) and the litmus questionnaires."
---

# build-ceremony

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make the end of a section a checkable event rather than a habit: the section's output is re-reviewed, the skills that produced it are improved, the lessons are carried forward, and the loop continues. | sourced | `T-t4-04`, `T-t4-02` "at the end of each section a ceremony re-reviews the output, improves the skills that produced it, and the loop continues" |

## Entities

| Entity |
|---|
| `E-rule-b1-1` |
| `E-finding-a7-2` |
| `E-standard-json-schema-2020-12` |
| `E-standard-agent-skills-spec` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | - | `F-b3-09` |
| `E-standard-agent-skills-spec` | unverified | unverified | - | `F-b3-07` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| continue | a written improve record | the next section, started without waiting for approval of the ceremony | sourced | `T-t5-01` "Do not stop at ceremonies; run them and continue." |

### Shapes (JSON Schema 2020-12)

**review-record (proposed summary shape; full field-level schema in references/ceremony-records.md, worked example kb/ceremonies/ceremony-01-review.json)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ceremony review record",
  "description": "Summary shape. Field-level constraints are in references/ceremony-records.md.",
  "type": "object",
  "required": [
    "ceremony",
    "section",
    "reviewer",
    "date",
    "findings",
    "metrics"
  ],
  "properties": {
    "findings": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "id",
          "skill",
          "location",
          "severity",
          "category",
          "finding",
          "evidence",
          "suggested_change"
        ],
        "properties": {
          "severity": {
            "enum": [
              "block",
              "fix",
              "nit"
            ]
          }
        }
      }
    }
  }
}
```

**improve-record (proposed summary shape; full field-level schema in references/ceremony-records.md, worked example kb/ceremonies/ceremony-01-improve.json)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ceremony improve record",
  "description": "Summary shape. Every id in the paired review record appears exactly once across applied and declined; JSON Schema cannot express that join, so the checker asserts it.",
  "type": "object",
  "required": [
    "ceremony",
    "improver",
    "date",
    "applied",
    "declined",
    "metrics_after",
    "lessons_for_next_section"
  ],
  "properties": {
    "applied": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "finding",
          "change",
          "files"
        ],
        "properties": {
          "files": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string"
            }
          }
        }
      }
    },
    "declined": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "finding",
          "reason"
        ]
      }
    },
    "metrics_after": {
      "type": "object",
      "required": [
        "validator_errors"
      ]
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| A section is not finished when its artifacts exist; it is finished when the ceremony has re-reviewed the output and improved the skills that produced it. | sourced | `T-t4-04` "at the end of each section a ceremony re-reviews the output, improves the skills that produced it, and the loop continues" |
| The ceremony is never a gate that waits: it runs to a written improve record and the next section starts. | sourced | `T-t5-01` "Do not stop at ceremonies; run them and continue." |
| findings are raised against the contract a skill states, not against whatever implementation currently sits behind it, per design rule 1 as agentic-stack states it (F-b1-02, E-rule-b1-1). A review that only reports what today's adapter does has reviewed the adapter, not the skill. | sourced | `F-b1-02`, `E-rule-b1-1` "Every external dependency sits behind a capability interface." |
| Proposed: the ceremony is in its own scope. This skill, the two record shapes and the author brief are reviewable artifacts of the section that used them, and a ceremony that never changes the ceremony is a result to be explained, not assumed. Research query: unresearched; this is our own scope rule with no external analogue sought. | proposed | - |
| a ceremony that records zero findings is reported as such with what was checked, because a review whose checks all skipped is the green-gate failure agentic-stack states from F-a7-03, applied to review rather than to a pipeline. | sourced | `F-a7-03`, `E-finding-a7-2` "A deterministic gate can be structurally green and mean nothing." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the ceremony introduces no runtime interface and no platform component. It is an authoring discipline over repository artifacts and records, so nothing in the running system may depend on a ceremony record being present. Research query: unresearched; a repo-authoring-discipline-versus-runtime-component boundary has no external standard sought yet. | proposed | - |
| Proposed: the ceremony does not re-open a settled design rule. A finding that disagrees with one is recorded as an open question on the affected skill with its deciding evidence, never applied as a silent edit. Research query: unresearched beyond this repo's own D-not_open decisions (not a citable kb id); no external change-control precedent has been searched. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Run the ceremony at the end of every section, before any work on the next section begins: set the stage, review what happened, generate insights, agree on a small set of improvement actions, and close with clear owners and next steps. | The method makes the self-improvement loop the way every item is worked through, and the published retrospective flow ends on a bounded action set with owners, which is what separates a retrospective from a discussion. | sourced | `T-t4-04`, `X-build-ceremony-008` "set the stage, review what happened, generate insights, agree on a small set of improvement actions, and close with clear owners and next steps" |
| 2 | Review the artifacts on disk and the traces of the runs that produced them, not the authors' summaries of what they did. | Reflective improvement in the prior art works from the execution trace: it extracts the module's inputs, outputs and reasoning and returns a score plus text feedback, which is credit assignment a summary cannot support. | sourced | `X-build-ceremony-002`, `X-build-ceremony-001` "From the execution traces, GEPA extracts the module's inputs, outputs, and reasoning, and calls a feedback function which returns a numeric score and text feedback" |
| 3 | Number the ceremony before writing anything: N is one counter global to the repository, never per-section. List kb/ceremonies/ceremony-*-review.json, take one more than the highest N on disk, and use that same N for the review record, the improve record, the row in the learning store, the ledger record and any known-issues file. A number is never reused or reset, even when the caller hands you a different one; report the number you actually used back to whoever asked for the other one, so its counter self-corrects instead of colliding again next section (proposed). Research query: no prior-art search has been run for a numbering convention for chained review/improve record pairs (versus, e.g., how migration or changelog tooling numbers sequential entries). | Proposed: the number, not the section name, is what pairs a review record with its improve record and what the ceremony checker keys the lessons row, the ledger record and the known-issues file on. A caller that derives N from a position in its own run collides with a closed ceremony and would overwrite it; ceremony 2 of this repository was asked for as ceremony 1 and was renumbered under the 1-3-1 protocol rather than overwriting ceremony 1's closed records. Three sections in a row were then handed a stale number, because a runner that derives N from a fixed base cannot learn from the renumbering unless the corrected number is reported back to it. | proposed | - |
| 4 | Write one review record under the number from step 3, conforming to the review-record shape defined above: each finding is filled in with its own id, skill, location, severity, category, evidence and suggested change. | Proposed: a finding without a location and a verbatim evidence quote can be neither applied nor refuted, so it silently becomes an opinion the next author is free to ignore. The field list itself is the review-record shape already defined in this skill's Shapes section and is not repeated here. | proposed | - |
| 5 | Verify each finding against the sources before recording it: resolve every cited id with the knowledge-base tool and re-run the renderer and validator over the skill you are accusing. Research query: unresearched; no prior-art search has been run for a reviewer self-verification step against cited sources before a finding is recorded. | Proposed: a reviewer working from memory manufactures findings, and a manufactured finding costs the improve step a real edit to an artifact that was correct. | proposed | - |
| 6 | Write one improve record conforming to the improve-record shape defined above: every finding id resolved as applied, with the change and files touched, or declined, with a reason, exactly once across the two lists and never a third disposition. Then re-render and re-validate every skill the improve step touched and record the validator result in metrics_after (proposed). | Proposed: the rendered skill file is generated, so an improvement that is not re-rendered leaves the readable artifact contradicting its own data and the ceremony would have made the repository worse. The resolution shape is stated once, in the Shapes section, and is not repeated here. | proposed | - |
| 7 | Integrate only actionable updates into the skills and the author brief rather than accumulating every observation, and write the lessons to the persistent learning store the next section reads before it starts. | In the reflective loop the Reflector identifies what helped or hurt and the Curator integrates updates into the playbook, which is what keeps the playbook usable rather than merely longer; the learning store is the persistent file the next run reads at its start, which is what closes the feedback loop rather than ending it at the review. | sourced | `X-build-ceremony-003`, `X-build-ceremony-005` "Reflector reviews the outcome and identifies what helped or hurt, and Curator/Mutator integrates updates into the playbook" |
| 8 | Record the section's metrics in the review record and the post-improvement metrics in the improve record, using the same counters both times. | Versioning the artifact lets a later reader diff it against the previous version and measure whether it improved, instead of asserting that it did. | sourced | `X-build-ceremony-007` "updating a template allows you to diff it against the previous version and measure whether outputs improved" |
| 9 | If the ceremony surfaces a blocker, define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation, recording the choice as an open question with its deciding evidence; if no recommendation emerges, drop the two lowest, find two more, and repeat. | The operating protocol fixes this as the response to a problem, so the ceremony resolves and continues instead of parking the section. | sourced | `T-t5-02`, `T-t5-03` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Feed the reflective step the whole trace, error messages and reasoning included, rather than a pass or fail signal: the prior art proposes targeted improvements from traces without needing a dense reward. | sourced | `X-build-ceremony-001` "uses full execution traces including error messages and reasoning to identify and propose targeted prompt improvements without requiring dense reward signals" |
| Treat the trace as the entry point and the exit point of the improvement loop, so a change made by a ceremony is checked by the traces of the next section rather than by the confidence of the person who made it. | sourced | `X-build-ceremony-004` "Reliable agents are built from a trace-centered improvement loop that begins with tracing and returns to tracing" |
| Diagnostic evaluation of authored skills can be automated without task-specific labels or handcrafted reward functions, by using models as general-purpose judges. | sourced | `X-build-ceremony-006` "computes diagnostic evaluations without requiring task-specific labels or handcrafted reward functions, using LLMs as general-purpose judges" |
| Proposed: when the same defect appears in more than one skill of a section, change the author brief once rather than patching each skill, and record the brief change; the wave-1 ceremony found one shared fact independently re-derived in four skills, which is a brief defect wearing four costumes. Research query: unresearched beyond this repo's own wave-1 ceremony record; no external precedent for a shared-defect-to-brief-change rule has been searched. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/check_ceremony.py kb/ceremonies/66-litmus-review.json kb/ceremonies/66-litmus-improve.json |
| Expected | Measured by tools/measure.py at 4445dfd: exit 0; last lines: findings_checked=21, unresolved=0, duplicated=0, missing_files=0, unknown_finding_ids=0 |
| Deliberate breakage | Drop the first entry of the applied list in kb/ceremonies/66-litmus-improve.json without adding it to declined, so a finding the review recorded is resolved in neither list: python3 -c "import json;p='kb/ceremonies/66-litmus-improve.json';d=json.load(open(p));d['applied']=d['applied'][1:];json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"; restore with git checkout -- kb/ceremonies/66-litmus-improve.json. |
| Expected failure | Measured by tools/measure.py at 4445dfd: exit 1; last lines: findings_checked=21, unresolved=1, duplicated=0, missing_files=0, unknown_finding_ids=0 \| unresolved: ['R66-001'] |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `build-solution-architecture` | Produce, before a section is built, one blueprint that shows where the impacts are, because standards, systems and components will all change. | `references/build-solution-architecture.md` |
| `build-litmus-questionnaire` | The measuring sticks walk down each stack element and the standards it interoperates with: one section per capability interface in PASS.md B3, whose middle column is the contract, and one per cross-cutting concern in B4. Each section states the idealistic future state a build could reach inside the window and asks about it from several angles, so that how the element is used is what gets measured. The frame that fixes the window, the closed scale, the six angles, the settledness classes and the isolation rule is the owner's; it is proposed here and recorded in docs/litmus/frame.json. | `references/build-litmus-questionnaire.md` |

## Composes with

Builds on: `agentic-stack`, `build-skill-authoring`

Used by: `build-evidence`, `build-skill-authoring`, `cap-capability-packaging`, `cap-durable-execution`, `cap-evaluation`, `cap-human-interaction`, `cap-identity`, `cap-provenance`, `cap-state-persistence`, `compose-improvement-loop`, `compose-workflow`, `xc-guarantees`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should the reviewer be an agent other than the one that authored the section, and should its findings be scored automatically? | One section reviewed twice, once by an author of the section and once by a separate reviewer, with the two finding sets compared for defects each missed; and a model-judge scoring pass compared against the recorded findings. | A reviewer separate from the section's authors writes the review record by hand, and no automated score is recorded, since automated diagnostic evaluation is available in the prior art but unmeasured here. | `X-build-ceremony-006` "using LLMs as general-purpose judges" |
| Can metrics_after ever be labelled measured rather than claimed for anything other than the validator error count? | A run in which the counters in metrics and metrics_after are produced by the same tool over the same tree, with the tree hash recorded, so the difference is an observation rather than a recount. | Only counters produced by a tool in the run are reported; every judgement about whether the section got better stays claimed. | `T-t4-01` "Treat this as a baseline target and improve on it." |
| Which records would source this skill's ten proposed rows, and does the ceremony discipline have a knowledge-base anchor at all beyond T-t4-04? | Counted at ceremony 71 (finding R71A-045): 10 of this skill's 24 origin-carrying rows are proposed, 42 percent, above the T-t9-02 stick of at most 30 percent that tools/acceptance_check.py applies to a capability skill. The sourcing pass recorded in kb/ceremonies/71-source-b.json covered cap-policy, cap-provenance and cap-errors and did not reach this skill. The candidate records a pass would draw on are T-t4-04 (a ceremony at the end of each section re-reviews the output and improves the skills that produced it), T-t10-09 (the remaining elements are accepted through a formal ceremony per layer, run in parallel where scopes are disjoint), REF-12-17 and the research rows X-end-to-end-053 and X-end-to-end-054 on GEPA and ACE; none of them carries the numbering rule, the record shapes or the author-brief rule, which is why those rows are proposed rather than misquoted. | Proposed: the overshoot stands recorded here rather than repaired by attaching a quote that does not support the whole row; the numbering, record-shape and author-brief rows stay origin=proposed until a record that states them exists, and tools/acceptance_check.py does not apply the stick to a build skill. | - |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/build-ceremony-author |
