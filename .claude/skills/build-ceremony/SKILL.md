---
name: build-ceremony
description: The discipline of closing a section with a ceremony: a review record of findings against what the section produced, then an improve record that marks every finding applied or declined with the files it touched, then continuing. Load it when a wave or section of skills is finished and the next one is about to start, when you are writing or checking a review or improve record under kb/ceremonies/, when you are deciding whether a finding should change a skill or the author brief, when carrying lessons from one pass into the next, or when a retrospective, post-mortem, or end-of-batch check is being run over work this repo produced. Also load it when someone proposes to skip the end-of-section check because the output looked fine, or when a review produced no findings at all.
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
| review | the section name, the artifacts the section produced on disk, and the traces of the runs that produced them | one review record conforming to the review-record shape: findings with id, skill, location, severity, category, finding, evidence quote and suggested_change, plus metrics and what_worked (proposed operation) | proposed | `T-t4-04` |
| improve | the review record and the artifacts it names | one improve record conforming to the improve-record shape: every finding id resolved as applied (with the change and the files touched) or declined (with the reason), plus brief_changes, metrics_after and lessons_for_next_section (proposed operation) | proposed | `T-t4-04` |
| carry | the improve record's lessons_for_next_section and brief_changes | the persistent learning store and the author brief the next section reads before it starts (proposed operation) | proposed | `X-build-ceremony-005` |
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
| Proposed: a ceremony number is a counter global to the repository, not a per-section one. It is one more than the highest ceremony-NN-review.json on disk, it is never reused and never reset, and the same N ties the review record, the improve record, the lessons row, the ledger record and any known-issues file together. A caller that derives the number from its own position in a run is corrected, not obeyed, because obeying it overwrites a closed ceremony. Research query: no prior-art search has been run for a numbering convention for chained review/improve record pairs (versus, e.g., how migration or changelog tooling numbers sequential entries). | proposed | - |
| Proposed: a decline is recorded with its reason in the same record. There is no silent third disposition, and a finding is never removed from the review record to make the improve record close. | proposed | - |
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
| 3 | Number the ceremony before writing anything: N is one counter global to the repository, never per-section. List kb/ceremonies/ceremony-*-review.json, take one more than the highest N on disk, and use that same N for the review record, the improve record, the row in the learning store, the ledger record and any known-issues file. A number is never reused or reset, even when the caller hands you a different one; report the number you actually used back to whoever asked for the other one, so its counter self-corrects instead of colliding again next section (proposed). | Proposed: the number, not the section name, is what pairs a review record with its improve record and what the ceremony checker keys the lessons row, the ledger record and the known-issues file on. A caller that derives N from a position in its own run collides with a closed ceremony and would overwrite it; ceremony 2 of this repository was asked for as ceremony 1 and was renumbered under the 1-3-1 protocol rather than overwriting ceremony 1's closed records. Three sections in a row were then handed a stale number, because a runner that derives N from a fixed base cannot learn from the renumbering unless the corrected number is reported back to it. | proposed | - |
| 4 | Write one review record under the number from step 3, conforming to the review-record shape: every finding gets an id, the skill and location it lands on, a severity of block, fix or nit, a category, the finding, a verbatim evidence quote from the artifact, and a suggested change. | Proposed: a finding without a location and a verbatim evidence quote can be neither applied nor refuted, so it silently becomes an opinion the next author is free to ignore. | proposed | - |
| 5 | Verify each finding against the sources before recording it: resolve every cited id with the knowledge-base tool and re-run the renderer and validator over the skill you are accusing. | Proposed: a reviewer working from memory manufactures findings, and a manufactured finding costs the improve step a real edit to an artifact that was correct. | proposed | - |
| 6 | Write one improve record conforming to the improve-record shape, resolving every finding id as applied with its change and the files it touched, or declined with its reason; then re-render and re-validate every skill the improve step touched and record the validator result in metrics_after (proposed). | Proposed: applied-or-declined with no third state is what makes the ceremony checkable, and an unresolved finding is the failure mode the check exists to catch. The rendered skill file is generated, so an improvement that is not re-rendered leaves the readable artifact contradicting its own data and the ceremony would have made the repository worse. | proposed | - |
| 7 | Integrate only actionable updates into the skills and the author brief rather than accumulating every observation, and write the lessons to the persistent learning store the next section reads before it starts. | In the reflective loop the Reflector identifies what helped or hurt and the Curator integrates updates into the playbook, which is what keeps the playbook usable rather than merely longer; the learning store is the persistent file the next run reads at its start, which is what closes the feedback loop rather than ending it at the review. | sourced | `X-build-ceremony-003`, `X-build-ceremony-005` "Reflector reviews the outcome and identifies what helped or hurt, and Curator/Mutator integrates updates into the playbook" |
| 8 | Record the section's metrics in the review record and the post-improvement metrics in the improve record, using the same counters both times. | Versioning the artifact lets a later reader diff it against the previous version and measure whether it improved, instead of asserting that it did. | sourced | `X-build-ceremony-007` "updating a template allows you to diff it against the previous version and measure whether outputs improved" |
| 9 | If the ceremony surfaces a blocker, define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation, recording the choice as an open question with its deciding evidence; if no recommendation emerges, drop the two lowest, find two more, and repeat. | The operating protocol fixes this as the response to a problem, so the ceremony resolves and continues instead of parking the section. | sourced | `T-t5-02`, `T-t5-03` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |
| 10 | Open references/ceremony-records.md only when writing a ceremony checker or adding a field to either record; the two summary shapes above are enough to run a ceremony by hand (proposed). | Proposed: the discipline has to stay small enough to be used, and a reader who meets a full field-level schema first will treat the ceremony as overhead. | proposed | `T-t3-02` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Feed the reflective step the whole trace, error messages and reasoning included, rather than a pass or fail signal: the prior art proposes targeted improvements from traces without needing a dense reward. | sourced | `X-build-ceremony-001` "uses full execution traces including error messages and reasoning to identify and propose targeted prompt improvements without requiring dense reward signals" |
| Treat the trace as the entry point and the exit point of the improvement loop, so a change made by a ceremony is checked by the traces of the next section rather than by the confidence of the person who made it. | sourced | `X-build-ceremony-004` "Reliable agents are built from a trace-centered improvement loop that begins with tracing and returns to tracing" |
| Diagnostic evaluation of authored skills can be automated without task-specific labels or handcrafted reward functions, by using models as general-purpose judges. | sourced | `X-build-ceremony-006` "computes diagnostic evaluations without requiring task-specific labels or handcrafted reward functions, using LLMs as general-purpose judges" |
| Proposed: when the same defect appears in more than one skill of a section, change the author brief once rather than patching each skill, and record the brief change; the wave-1 ceremony found one shared fact independently re-derived in four skills, which is a brief defect wearing four costumes. | proposed | - |
| Proposed: one finding names one location. A finding phrased about the section as a whole has no file to touch, so it can only be declined or restated, and it wastes the improve step either way. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/check_ceremony.py kb/ceremonies/ceremony-01-review.json kb/ceremonies/ceremony-01-improve.json (proposed tool, not yet written): validate both files against the review-record and improve-record shapes, then assert findings_checked > 0, unresolved == 0 (every review finding id appears exactly once across applied and declined), duplicated == 0, missing_files == 0 (every path in an applied entry's files exists), and unknown_finding_ids == 0. |
| Expected | findings_checked=7, unresolved=0, duplicated=0, missing_files=0, unknown_finding_ids=0; exit 0 |
| Deliberate breakage | Delete the C1-007 entry from the applied list of kb/ceremonies/ceremony-01-improve.json without adding it to declined, so the finding is recorded in the review and resolved in neither list. |
| Expected failure | unresolved=1 naming C1-007, exit 1. A second breakage, pointing an applied entry's files at a path that does not exist, must give missing_files=1 and exit 1. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: `build-entry-conformance`, `build-interface-versioning`, `build-simplicity-budget`, `cap-capability-registry`, `cap-evaluation`, `cap-human-interaction`, `cap-mandate-broker`, `cap-memory`, `compose-improvement-loop`, `compose-operators`, `xc-audit-trail`, `xc-compensation`, `xc-enforcement-chain`, `xc-tenancy`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should the reviewer be an agent other than the one that authored the section, and should its findings be scored automatically? | One section reviewed twice, once by an author of the section and once by a separate reviewer, with the two finding sets compared for defects each missed; and a model-judge scoring pass compared against the recorded findings. | A reviewer separate from the section's authors writes the review record by hand, and no automated score is recorded, since automated diagnostic evaluation is available in the prior art but unmeasured here. | `X-build-ceremony-006` "using LLMs as general-purpose judges" |
| Can metrics_after ever be labelled measured rather than claimed for anything other than the validator error count? | A run in which the counters in metrics and metrics_after are produced by the same tool over the same tree, with the tree hash recorded, so the difference is an observation rather than a recount. | Only counters produced by a tool in the run are reported; every judgement about whether the section got better stays claimed. | `T-t4-01` "Treat this as a baseline target and improve on it." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/build-ceremony-author |
