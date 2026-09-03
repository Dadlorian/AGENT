---
name: core-judge
description: The Judge: a pure function from a result and a criterion to a verdict, where the criterion is resolved out of band and never travels with the work, and where hiding it is treated as necessary but not sufficient - sampling the criterion set per grading and a periodic held-out audit are part of the contract, not an add-on. Load it before deciding what 'done' means for a unit of work, before a definition of done is handed to the thing that will be graded, when a grading step is added to a workflow or a loop's exit condition is written, and when someone asks 'who decides this is finished', 'why can the agent not see the rubric', 'why did the same result get two different verdicts', or 'how would we notice that the agents had learned to satisfy the checks without doing the work'.
---

# core-judge

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one grading contract - a pure function of a result and a criterion, returning a verdict - so that 'done' is a decidable property of the work rather than an opinion held by whoever ran it. | sourced | `F-b2-05`, `F-b2-01` "pure function `(result, criterion) → verdict`" |

## Entities

| Entity |
|---|
| `E-core-component-judge` |
| `E-core-component-document` |
| `E-rule-b1-6` |
| `E-seam-dispatch` |
| `E-capability-errors` |
| `E-finding-a7-2` |
| `E-standard-json-schema-2020-12` |
| `E-standard-rfc-9457-problem-details` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | https://json-schema.org/draft/2020-12 | `F-b3-09`, `F-b1-03` |
| `E-standard-rfc-9457-problem-details` | RFC 9457 | unverified | - | `F-b3-13`, `F-b1-03` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| judge (the operation this component is judged on; PASS.md names the function, the call signature below is proposed) | a result value and a resolved criterion set (proposed: plus the sample seed derived in sample_criterion) | a verdict of pass or fail plus the check ids that decided it; a pure, total function of its arguments, with no clock, no network call and no store handle | sourced | `F-b2-05` "pure function `(result, criterion) → verdict`" |
| resolve_criterion (proposed operation; the out-of-band path the Judge alone may take) | a criterion_ref, the opaque handle a dispatch request carries (proposed) | the criterion set behind that handle, or a typed problem of the registered type urn:agentic:problem:criterion-unresolvable when the handle names nothing; reachable from the Judge and from nothing the graded unit runs (proposed) | proposed | `F-b1-07` |
| sample_criterion (proposed operation; the mitigation hiding alone does not provide) | a criterion set, a grading mode of in_loop or closing, and a seed derived from the result digest, the criterion-set digest and the dispatch id (proposed) | the subset of checks applied in this grading - a proper subset in in_loop mode and the whole set in closing mode - which is deterministic for one grading and unpredictable across gradings (proposed) | proposed | `X-end-to-end-013` |
| explain (proposed accessor; what the graded unit is allowed to read) | a verdict (proposed) | the verdict, the ids of the checks that failed and a detail written from those ids; it never carries criterion text, the sampled subset, or the criterion-set digest (proposed) | proposed | `F-b1-07` |
| audit (proposed operation; run against the routine judge, never in its path) | a sample of recorded gradings and a held-out criterion set kept out of every routine grading (proposed) | a divergence count between the routine verdicts and the held-out ones; an alarm that opens an investigation, never a score and never a correction to a verdict already returned (proposed) | proposed | `X-end-to-end-013`, `X-core-judge-004` |

### Shapes (JSON Schema 2020-12)

**criterion-set (proposed summary shape; the full schema, the sampling rules, a worked grading for each of TARGET T1's three ways in and a worked rejection are in references/judge-shapes.md)** (proposed; sources: `F-b2-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:judge:criterion-set:0.1",
  "title": "CriterionSet",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "criterion_ref",
    "criterion_version",
    "checks"
  ],
  "properties": {
    "criterion_ref": {
      "type": "string",
      "pattern": "^criterion://[a-z0-9./-]+$",
      "description": "The opaque handle a dispatch request carries. The set behind it never travels with the request."
    },
    "criterion_version": {
      "type": "string",
      "minLength": 1,
      "description": "An immutable version. A criterion set is never edited in place; a change makes a new version."
    },
    "checks": {
      "type": "array",
      "minItems": 1,
      "description": "Each entry names a check_id of a definition-of-done check in the document (core-document's check shape) and carries the criterion text for it.",
      "items": {
        "type": "object",
        "required": [
          "check_id",
          "criterion"
        ],
        "properties": {
          "check_id": {
            "type": "string",
            "minLength": 1
          },
          "criterion": {
            "type": "string",
            "minLength": 1
          },
          "sampleable": {
            "type": "boolean",
            "default": true,
            "description": "False pins a check into every grading; a set with no sampleable check cannot be sampled and is reported as such."
          }
        }
      }
    },
    "held_out": {
      "type": "array",
      "description": "Checks reserved for the audit. Never applied in a routine grading, so a unit optimised against routine outcomes has not seen them.",
      "items": {
        "type": "object"
      }
    }
  }
}
```

**verdict (proposed shape; this is the whole of what may travel back to the graded unit)** (proposed; sources: `F-b1-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:judge:verdict:0.1",
  "title": "Verdict",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "verdict",
    "criterion_ref",
    "failed_check_ids",
    "detail"
  ],
  "properties": {
    "verdict": {
      "enum": [
        "pass",
        "fail"
      ]
    },
    "criterion_ref": {
      "type": "string",
      "pattern": "^criterion://[a-z0-9./-]+$"
    },
    "failed_check_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Ids only. A check_id is a label the document already declared; the criterion behind it is not."
    },
    "detail": {
      "type": "string",
      "description": "Composed from failed_check_ids. A detail that quotes criterion text is design rule 6 broken in the field a reader trusts least."
    }
  }
}
```

**grading-record (proposed shape; what is recorded, which is strictly more than what is returned)** (proposed; sources: `F-part-c-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:judge:grading-record:0.1",
  "title": "GradingRecord",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "verdict",
    "criterion_ref",
    "criterion_version",
    "criterion_set_digest",
    "grading_mode",
    "applied_check_ids",
    "checks_applied",
    "sample_seed",
    "result_digest"
  ],
  "properties": {
    "verdict": {
      "$ref": "urn:agentic:core:judge:verdict:0.1"
    },
    "criterion_ref": {
      "type": "string"
    },
    "criterion_version": {
      "type": "string"
    },
    "criterion_set_digest": {
      "type": "string",
      "description": "Digest of the immutable set, so a verdict can be replayed against exactly what graded it."
    },
    "grading_mode": {
      "enum": [
        "in_loop",
        "closing"
      ]
    },
    "applied_check_ids": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "checks_applied": {
      "type": "integer",
      "minimum": 0,
      "description": "A grading with checks_applied of 0 is reported inconclusive, never pass."
    },
    "sample_seed": {
      "type": "string"
    },
    "result_digest": {
      "type": "string"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The Judge is a pure function of a result and a criterion: same result, same criterion set, same sample seed, same verdict, every time. Remove it and "done" becomes an opinion, which is the failure this component exists to prevent. | sourced | `F-b2-05` ""done" becomes an opinion" |
| Proposed: purity here is total, not partial: the function takes no clock, no random source, no store handle and no network call. A judge that reads anything not passed to it cannot be replayed, and a verdict that cannot be replayed is the opinion this component replaces. | proposed | `F-b2-05`, `F-b1-06` |
| agentic-stack states design rule 6 as a test (F-b1-07): the grader is never visible to the graded. The consequence owned here is a division of one object into two - a request carries criterion_ref and nothing else, and the criterion set is fetched by the Judge through resolve_criterion; a criterion that arrives with the work has become a target for the work. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| Proposed: hiding the criterion is necessary and not sufficient. Published work on rubric-based reinforcement learning records that a policy trained against a fixed rubric long enough will learn to exploit the difference, and the published mitigation is rubric dropout with a full-rubric evaluation; this contract adopts both as sample_criterion and audit rather than treating rule 6 as the whole defence. | proposed | `X-end-to-end-012`, `X-end-to-end-013` |
| Proposed: the sample is deterministic for one grading and unpredictable across gradings. The seed is derived from the result digest, the criterion-set digest and the dispatch id, so a grading replays to the identical verdict while no two gradings apply the same subset; a sample drawn from a live random source would make the determinism invariant above unprovable. | proposed | `X-end-to-end-013`, `F-part-c-04` |
| Proposed: the audit is an alarm, not a score. Divergence between the routine judge and the held-out set opens an investigation into the criterion set and the units graded by it; it never revises a verdict already returned, because a verdict that can be revised after the fact is not a decision the loop could have terminated on. | proposed | `X-end-to-end-013`, `X-core-judge-004` |
| Proposed: a grading in which no check applied is reported inconclusive, never pass. build-definition-of-done owns the measured finding behind this (F-a7-03); the consequence on this contract is a counted field, checks_applied, in the grading record, so a criterion set that matched nothing cannot close work by silence. | proposed | `F-a7-03`, `F-part-c-04` |
| core-document owns the definition of done and the check ids this contract grades against (F-b2-02); the consequence here is directional: the Judge reads check ids declared in the document and adds none of its own, so a criterion that grades something the document never declared is a defect in the criterion set rather than a stricter judge. | sourced | `F-b2-02` "declared intent, definition of done, steps" |
| cap-errors owns the failure shape and its closed registry (F-b4-07); the consequence here is that an unresolvable criterion_ref returns the registered type urn:agentic:problem:criterion-unresolvable and never a fail verdict, because failing a unit for the grader's missing handle would make an infrastructure fault look like unfinished work. | sourced | `F-b4-07`, `F-b3-13` "Typed and machine-readable. Never parsed from prose" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Criterion text, to the unit being graded and to everything it can read. agentic-stack states design rule 6 (F-b1-07); on this interface it forbids the criterion in a dispatch request, in a step payload, in the verdict's detail string, and in any telemetry payload or prompt log the graded unit can reach - the handle travels, the set does not. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| Proposed: the sampled subset and the criterion-set digest. Both are recorded in the grading record and neither is returned: a unit that learns which checks ran this time, or that two gradings used the same set, can infer the set across a handful of attempts, and the sampling would have bought nothing. | proposed | `X-end-to-end-012` |
| Proposed: the held-out criteria and the audit schedule, to everything outside the audit itself - including the routine judge. A held-out check that appears in a routine grading is no longer held out, and an audit that runs on a predictable schedule is one a unit can be optimised around. | proposed | `X-end-to-end-013` |
| Proposed: which grading engine produced the verdict, and the model class or check runner behind it. A verdict is a verdict; a caller that can see how it was reached will branch on it, and the pair of adapters core-judge-implement builds stops being swappable. | proposed | `F-meta-04` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the grading function as a pure, total function of a result and a resolved criterion set: no clock, no random source, no store handle, no network call, and one verdict for every input including malformed results. | This is the signature PASS.md fixes for the component, and totality is what stops a grading from throwing where a fail verdict belongs; a judge that can raise instead of deciding hands the decision back to whoever called it. | sourced | `F-b2-05` "pure function `(result, criterion) → verdict`" |
| 2 | Put the criterion behind a handle: dispatch carries criterion_ref, the Judge calls resolve_criterion, and no code path accepts criterion text as an argument from the caller who submitted the work. | agentic-stack states design rule 6 (F-b1-07) and core-document keeps criterion text out of every document view a graded unit is handed; the consequence owned here is that the rule survives refactoring only if the criterion cannot be passed in at all, since an optional criterion argument will be filled by the first caller who finds it convenient. | sourced | `F-b1-07` "never the criterion it is judged against" |
| 3 | Sample the criterion set on every in-loop grading and apply the full set on the closing grading, seeding the sample from the result digest, the criterion-set digest and the dispatch id. | The published mitigation for a rubric that leaks through outcomes is to drop criteria before scoring while evaluating against the full rubric; deriving the seed rather than drawing it keeps the grading replayable, which is the property the C4 criterion asserts over 100 runs. | sourced | `X-end-to-end-013`, `X-end-to-end-012` "rubric dropout, which randomly drops criteria before computing reward so the policy never optimizes the same rubric twice, while evaluation always uses the full rubric" |
| 4 | Keep a held-out criterion set out of every routine grading and re-grade a sample of recorded gradings against it on an unpredictable cadence; raise an alarm on divergence and change no returned verdict. | A gold set is what turns automated grading into something whose bias is detectable rather than assumed; an audit that adjusted verdicts would make the loop's exit condition retroactive, and one that ran on a schedule would be as learnable as the rubric it protects. | sourced | `X-core-judge-004`, `X-end-to-end-013` "The golden set methodology establishes human judgment as the criterion standard for evaluating automated systems" |
| 5 | Return the verdict shape and record the grading record: ids, counts, digests and the seed are written to the ledger; the verdict, the failed check ids and a detail composed from those ids are what travel back. | The split is what makes rule 6 checkable rather than asserted: core-document states what the graded unit may see of a document, and this is the same line drawn through the reply - everything the audit needs is recorded, everything the graded unit could optimise against stays out of the response, and a single object serving both readers always leaks toward the one that reads it more often. | sourced | `F-b1-07`, `F-part-c-08` "An agent sees its outcome" |
| 6 | Reach the Judge the same way from all three ways in. TARGET T1's three - a human, an agent, and an internal or external event - reach it only as a grading step inside a workflow or dispatch, never by calling it directly, and the way in survives as the actor on the grading record and nowhere in the verdict. | A grading callable directly by an entry path is a grading whose criterion the entry path can choose; keeping the Judge downstream of dispatch is what makes 'the criterion never travelled' a property of one code path rather than of every caller's good behaviour. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| 7 | Return an unresolvable handle, a criterion set whose checks name nothing in the document, and a malformed result as typed problems or as an inconclusive grading; never as a fail verdict. | cap-errors owns the registry these types come from (F-b3-13) and core-document returns declaration failures the same way; the consequence here is that a fail verdict is a statement about the work, so spending one on the grader's own fault teaches a loop to retry work that was never the problem. | sourced | `F-b3-13`, `F-b4-07` "— adopt the RFC directly" |
| 8 | Judge a candidate implementation on four properties: an identical verdict across 100 runs of the same grading; zero occurrences of any criterion string in a corpus of recorded dispatch requests; checks_applied counted and non-zero on every grading reported pass; and a recorded audit divergence that someone acted on. | agentic-stack and build-definition-of-done state that a criterion nothing can fail is not a criterion (F-part-c-04); each property here is a count or a comparison rather than an exit code, because the failure this component invites is a judge that returns pass without applying anything. | sourced | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion" |
| 9 | Proposed: open references/judge-shapes.md when you are writing the full criterion-set schema, the sampling rules, the audit procedure, or a rejection instance, or when you need the worked grading for a way in you have not handled yet. The body of this skill is enough to grade a result and to judge an implementation without it. | Proposed: the full schemas, the three worked gradings and the worked rejection are longer than the progressive-disclosure budget allows in the body, and a reader deciding what 'done' means does not need them; a reader implementing the sampler does. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack, build-definition-of-done and core-document already state the green-gate finding (F-a7-03). What it adds here: a criterion set made only of well-formedness checks produces a judge that passes everything and means nothing, so count behavioural checks in the set before trusting a pass. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Deterministic checks are the right instrument where the answer is verifiable and the wrong one where it is not, so split the criterion set by what each check can actually decide rather than by which engine is convenient. | sourced | `X-core-judge-005` "Deterministic checks are reliable but narrow" |
| A judge that grades with a model carries systematic biases - position, verbosity, self-preference - so treat bias controls as part of the criterion set rather than as tuning, and never let a judge grade output from its own model family without one. | sourced | `X-core-judge-002` "position bias (favoring first or last responses), verbosity bias (rewarding longer answers), and self-preference bias" |
| Version criterion sets immutably and require every scoring decision to cite the check it came from; a criterion set edited in place makes every earlier verdict unreplayable and every audit divergence unattributable. | sourced | `X-core-judge-008` "compiles criteria into versioned immutable bundles, requires judges to cite auditable evidence for every scoring decision" |
| Emit the verdict on the standard evaluation carrier the telemetry conventions already define rather than inventing a field for it, so a verdict is readable by tools nobody here wrote. | sourced | `X-end-to-end-006`, `F-b1-05` "gen_ai.evaluation.result providing a standard carrier for evaluator scores and explanations" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.1 row C4, made precise. Two assertions in one run. (a) `judge --result fixtures/result.json --criterion-ref criterion://fix-acceptable/v1 --runs 100 --report out/judge-conformance.json` asserts `verdicts_distinct == 1` and `checks_applied > 0` on every run. (b) `grep -F -c "$(cat fixtures/criterion.txt)" out/recorded-dispatch-requests.jsonl` returns 0 over a corpus of at least 50 recorded requests, asserted as `requests_scanned >= 50` and `criterion_hits == 0`. |
| Expected | exit 0 and the two lines `runs=100 verdicts_distinct=1 checks_applied=4` and `requests_scanned=50 criterion_hits=0`. |
| Deliberate breakage | Inline the criterion text into the document's `definition_of_done` field that is passed to dispatch, and re-record the 50 requests, changing nothing else. |
| Expected failure | The grep count becomes non-zero, `criterion_hits` reports 50, assertion (b) fails and the run exits non-zero - while (a) still reports `verdicts_distinct=1`, so the report names design rule 6 as what broke rather than determinism. This is design rule 6 made checkable. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-07` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`, `core-document`

Used by: `cap-evaluation`, `compose-improvement-loop`, `compose-loop`, `core-judge-implement`, `seam-dispatch`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the Judge run inside isolation with its own criterion access, or outside it? | Over 200 recorded dispatches, grep every payload the graded unit could read for the criterion string; and separately measure whether judging outside creates a serialisation bottleneck at the concurrency the platform actually reaches. | Outside. Design rule 6 is the stronger constraint and the bottleneck is hypothetical until measured; a judge inside the boundary puts the criterion one filesystem away from the thing it grades. | `F-b1-07` "The grader is never visible to the graded" |
| Does the Judge grade the result alone, or the trajectory that produced it? | Count, over a corpus of gradings, how many disagreements between a verdict and a later human review turn on something visible only in the ordered execution trace rather than in the result. A high count argues for extending the signature; a low one leaves the extra input as attack surface for the criterion to leak into. | The result alone, as PASS.md's signature fixes it, with trajectory grading recorded as a proposed extension rather than adopted: current practice does evaluate the complete ordered execution trace, so the gap is real, but widening the input is a change to a core signature and needs the count first. | `X-end-to-end-010`, `F-b2-05` "Trajectory-based evaluation evaluates the complete, ordered execution trace" |
| Does criterion sampling apply to the grading that closes the work, or only to gradings inside a loop? | Compare, over a run history, how often a unit passes a sampled grading and then fails the full set. A high rate means in-loop sampling is closing work that was not done; a low rate means the sample is representative and the closing grading could be sampled too. | In-loop gradings are sampled and the closing grading applies the full set, which is the shape the published mitigation takes - drop criteria while scoring, evaluate against the whole rubric. The grading_mode field carries the distinction so the answer can change without a shape change. | `X-end-to-end-013` "while evaluation always uses the full rubric" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
