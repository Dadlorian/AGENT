# Criterion sets, sampling, the audit, and worked gradings

Long material for `core-judge`. Everything here is **proposed** unless a kb id is given beside it.
The skill body is enough to grade a result and to judge an implementation; open this file only when
writing the full criterion-set schema, the sampling rule, the audit procedure, or a rejection instance.

Resolve every id below with `python3 tools/kb.py show <id>`.

## 1. Full criterion-set and grading-record schemas (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:judge:criterion-set:0.1",
  "title": "CriterionSet",
  "description": "The set behind a criterion_ref. PASS.md fixes the signature (F-b2-05); the fields are ours.",
  "type": "object",
  "additionalProperties": false,
  "required": ["criterion_ref", "criterion_version", "checks"],
  "properties": {
    "criterion_ref": {"type": "string", "pattern": "^criterion://[a-z0-9./-]+$"},
    "criterion_version": {"type": "string", "pattern": "^v[0-9]+$"},
    "document_ref": {"type": "string", "description": "The document whose definition-of-done check ids this set grades. A check_id absent there is a defect in the set."},
    "checks": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["check_id", "criterion", "kind"],
        "properties": {
          "check_id":   {"type": "string", "minLength": 1},
          "criterion":  {"type": "string", "minLength": 1, "description": "The text. Never leaves the Judge."},
          "kind":       {"enum": ["behavioural", "well_formedness"]},
          "sampleable": {"type": "boolean", "default": true},
          "weight":     {"type": "integer", "minimum": 1, "default": 1}
        }
      }
    },
    "held_out": {
      "type": "array",
      "description": "Audit-only checks. Never applied in a routine grading, never named in a verdict.",
      "items": {"$ref": "#/properties/checks/items"}
    },
    "sampling": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "in_loop_drop_fraction": {"type": "number", "minimum": 0, "maximum": 0.5, "default": 0.25},
        "min_checks_applied":    {"type": "integer", "minimum": 1, "default": 2}
      }
    }
  }
}
```

The grading record (`urn:agentic:core:judge:grading-record:0.1`, summarised in the skill body) is what the
Ledger stores. Two fields deserve their reason written down. `checks_applied` exists because a grading that
applied nothing must be reported inconclusive rather than pass - the same shape of failure
`build-definition-of-done` records as measured in F-a7-03. `sample_seed` exists because a verdict nobody can
reproduce is an anecdote; with the seed, the criterion version and the result digest, the grading replays.

## 2. The sampling rule (proposed)

```
seed            = sha256(result_digest || criterion_set_digest || dispatch_id)
applied         = every check with sampleable = false
candidates      = every check with sampleable = true, ordered by check_id
drop_count      = floor(len(candidates) * in_loop_drop_fraction)     # closing mode: 0
applied        += candidates minus drop_count entries chosen by seed
assert len(applied) >= min_checks_applied                            # else: inconclusive, not pass
```

Three properties this buys, in the order they matter:

| Property | How the rule gives it | What breaks without it |
|---|---|---|
| replayable | the seed is derived, never drawn from a live random source | C4 assertion (a): 100 runs no longer agree |
| unpredictable across gradings | the result digest is in the seed, so a new attempt reshuffles | a fixed subset is learnable from outcomes (X-end-to-end-012) |
| never empty | `min_checks_applied` floors the sample | a judge that passes work it did not check (F-a7-03) |

## 3. The audit (proposed)

The held-out set is graded by a second judge configured independently of the routine one, over a sample of
recorded gradings, on a cadence drawn from the same seed material rather than from a calendar. Its output is
a divergence count, and divergence is an alarm: it opens an investigation into the criterion set and the
units graded against it. It never rewrites a verdict that a loop has already terminated on. Human judgment
is what the held-out set encodes (X-core-judge-004), which is why divergence is evidence about the routine
judge and not a score for the unit.

## 4. Worked grading A: a human's work is graded (proposed)

TARGET T1 lists three ways in (T-t1-01, T-t1-02, T-t1-03). None of them calls the Judge: an entry produces a
document, dispatch executes a step, and a grading step grades the result. The way in survives as `actor` on
the grading record and appears nowhere in the verdict.

```json
{
  "recorded": {
    "actor": "user:corey",
    "run_id": "run-human-0001",
    "step_id": "fix-judge#1",
    "criterion_ref": "criterion://fix-acceptable/v1",
    "criterion_version": "v1",
    "criterion_set_digest": "sha256:8c1f...",
    "grading_mode": "in_loop",
    "applied_check_ids": ["patch-present", "regression-verified"],
    "checks_applied": 2,
    "sample_seed": "sha256:41ab...",
    "result_digest": "sha256:9d02...",
    "verdict": {
      "verdict": "fail",
      "criterion_ref": "criterion://fix-acceptable/v1",
      "failed_check_ids": ["regression-verified"],
      "detail": "1 check failed: regression-verified"
    }
  },
  "returned_to_the_graded_unit": {
    "verdict": "fail",
    "criterion_ref": "criterion://fix-acceptable/v1",
    "failed_check_ids": ["regression-verified"],
    "detail": "1 check failed: regression-verified"
  }
}
```

The two objects side by side are the whole of design rule 6 on this component: everything the audit needs is
in the first, and the second names ids the document already declared.

## 5. Worked grading B: an event's work, closing mode (proposed)

The same grading entered by an internal producer (T-t1-03), on the grading that closes the loop. Only
`actor` and `grading_mode` differ, and the full set is applied because closing mode drops nothing.

```json
{
  "actor": "service:alerting",
  "run_id": "run-event-0001",
  "step_id": "fix-judge#2",
  "criterion_ref": "criterion://fix-acceptable/v1",
  "grading_mode": "closing",
  "applied_check_ids": ["patch-present", "regression-verified", "no-new-lint", "diff-scoped"],
  "checks_applied": 4,
  "verdict": {"verdict": "pass", "criterion_ref": "criterion://fix-acceptable/v1", "failed_check_ids": [], "detail": "4 checks applied, 0 failed"}
}
```

A scheduled producer is the same object with `"actor": "schedule:nightly-fault-sweep"`; nothing downstream
of the grading may branch on either.

## 6. Worked grading C: an agent's work, and what it may not learn (proposed)

An agent entering the system (T-t1-02) is graded twice on two attempts. The applied subsets differ because
the result digest changed, and the verdicts name only ids:

```json
[
  {"actor": "agent:partner-sre-bot", "grading_mode": "in_loop", "applied_check_ids": ["patch-present", "diff-scoped"],
   "verdict": {"verdict": "fail", "criterion_ref": "criterion://fix-acceptable/v1", "failed_check_ids": ["diff-scoped"], "detail": "1 check failed: diff-scoped"}},
  {"actor": "agent:partner-sre-bot", "grading_mode": "in_loop", "applied_check_ids": ["patch-present", "regression-verified", "no-new-lint"],
   "verdict": {"verdict": "pass", "criterion_ref": "criterion://fix-acceptable/v1", "failed_check_ids": [], "detail": "3 checks applied, 0 failed"}}
]
```

An agent that could read `applied_check_ids` would learn the set in a handful of attempts, which is why that
field is recorded and not returned.

## 7. Worked example D: the failure shape (proposed)

What a caller receives when the handle resolves to nothing. `cap-errors` owns the shape and its closed
registry (F-b3-13); `core-judge` adds no failure format and no type of its own. `criterion-unresolvable` is
a registered row in `docs/decomposition.md` section 2.1.6, so this is the type an implementation returns
rather than a fail verdict.

```json
{
  "sent": {
    "dispatch_id": "0f5f9a1c-2f0a-4e37-9a45-9a2a3b5f0c11",
    "criterion_ref": "criterion://fix-acceptable/v9",
    "actor": {"subject": "agent:partner-sre-bot"}
  },
  "received_on_the_wire": {
    "media_type": "application/problem+json",
    "type": "urn:agentic:problem:criterion-unresolvable",
    "title": "criterion_ref does not resolve",
    "status": 422,
    "detail": "no criterion set is registered for this handle at any version",
    "retryable": false,
    "instance": "urn:agentic:core:judge:grading:fix-judge#1",
    "dispatch_id": "0f5f9a1c-2f0a-4e37-9a45-9a2a3b5f0c11"
  },
  "what_the_caller_does": "registers the criterion set, or corrects the handle, and resubmits under the same idempotency key; it never retries the work, because the work was never the problem"
}
```

The caller branches on `type`, never on the wording of `detail`. Note what is absent: no field of this
problem names a check, and none carries criterion text - a failure to resolve the grader must not become the
one path by which the grader becomes visible.

## 8. Judging an implementation (proposed)

The four properties in the skill body, as things a run produces:

| Property | Asserted as | Fails when |
|---|---|---|
| deterministic | `verdicts_distinct == 1` over 100 runs of one grading | a live random source, a clock, or an unpinned grading engine |
| criterion hidden | `criterion_hits == 0` over >= 50 recorded dispatch requests | criterion text inlined into the document handed to dispatch |
| something was checked | `checks_applied > 0` on every grading reported pass | an empty or non-matching criterion set |
| audit acted on | a recorded divergence with an investigation record against it | an audit whose output nobody reads, which is a score by another name |
