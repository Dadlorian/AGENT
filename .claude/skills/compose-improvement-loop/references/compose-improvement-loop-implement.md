---
name: "compose-improvement-loop-implement"
description: "How the self-improvement loop is actually built here: this repository's own ceremony review-and-improve pass as the first executor - a live session that edits the target file in place and commits, a reviewer's judgment standing in for a gate - a second executor whose sole promotion authority is cap-evaluation's passed outcome and whose only write path is cap-capability-registry's publish, with no session attached; the migration between them; where correlation, an idempotency lease and provenance attach to one candidate iteration; and a definition of done run against this composition's own conformance harness. Load it when writing or reviewing code that seeds, gates or promotes a candidate, when deciding what the second executor should be, when a promotion has to survive with no session attached, when asking whether closed ceremonies already conform to compose-improvement-loop's contract, or when a finding is applied by editing a file directly instead of through a gate."
---

# compose-improvement-loop-implement (folded into `compose-improvement-loop`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed: build compose-improvement-loop's candidate lifecycle on two executors that differ in who or what holds promotion authority, and stage the migration from the review-and-improve loop this repository already runs, which closes findings but gates and promotes neither through cap-evaluation nor cap-capability-registry. | proposed | `F-b1-04`, `F-part-c-05`, `T-t4-04` |

## Entities

| Entity |
|---|
| `E-rule-b1-3` |
| `E-concern-budget` |
| `E-concern-provenance` |

## Contract

### Shapes (JSON Schema 2020-12)

**executor-binding (proposed shape; the configuration that selects which executor advances a candidate, and the only place either executor is named)** (proposed; sources: `T-t2-02`, `F-b1-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:improvement-loop:executor-binding:0.1",
  "title": "ImprovementLoopExecutorBinding",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A candidate declaration carries none of this: swapping the executor is a configuration edit, so the conformance suite can run the same candidate twice by changing one value.",
  "required": [
    "executor",
    "promotion_authority",
    "registry_publish"
  ],
  "properties": {
    "executor": {
      "type": "string",
      "description": "The adapter id from this skill's Adapters table."
    },
    "promotion_authority": {
      "enum": [
        "session_reviewer",
        "evaluation_gate"
      ],
      "description": "The axis this pair differs on: whose judgment a promotion rests on."
    },
    "registry_publish": {
      "type": "boolean",
      "description": "False on today's executor: a promotion is the git commit that edits the target file. True on the second: a promotion is a new cap-capability-registry record."
    },
    "candidate_source": {
      "enum": [
        "ceremony_finding",
        "evaluation_transition"
      ],
      "default": "ceremony_finding"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| promote_revision publishes a new cap-capability-registry record and never writes a target's checked-out file. compose-improvement-loop owns this invariant and this build inherits it unchanged: an executor whose promotion is a commit against the target file has not met it, however green its own checks are, which is why stage 3 of the migration below exists. | sourced | `X-cap-capability-registry-007` "new versioned records rather than in-place edits" |
| A gate outcome, not a reviewer's approval, authorises a promotion: gate_revision runs cap-evaluation's evaluate and only outcome=passed may reach promote_revision. compose-improvement-loop owns that operation and this build inherits it unchanged; an executor that cannot return failed on measured evidence has no gate at all, whatever its review record carries. | sourced | `X-end-to-end-040` "A regression suite is the gate that makes a self-improvement loop safe to run automatically." |
| A result produced from a dirty tree may never carry the label measured, because nobody else can reproduce the tree it ran against. build-evidence-record owns that rule; on this build it decides the status of the Adapters table below, and it is why the today row there is claimed rather than measured. | sourced | `F-a5-04` "whether the tree was dirty" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: neither executor's vocabulary reaches the candidate - no reviewer identity, no commit sha, no registry signing key appears in an ImprovementCandidate or a CandidateOutcome. They appear in the executor binding and in the Adapters table below, and nowhere else, the way agentic-stack already requires products to stay out of core and interface material (F-part-c-09). | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Name today's two non-conformances precisely before building anything: no gate_revision call exists, so a reviewer's judgment is the only authority a finding is applied on; and promote_revision writes the target skill.json in place through a git commit, so there is no rollback_to and no prior version to resolve back to if the applied change regresses. | compose-improvement-loop owns both of these as invariants of its own contract; this step only locates them in the executor being wrapped, because a migration begins by naming the gap in what already runs rather than by proposing to replace it. | sourced | `F-part-c-11`, `T-t4-04` "Do not propose replacing what runs." |
| 2 | Proposed: close the missing-gate stage first. Wire gate_revision to a real cap-evaluation adapter and require outcome=passed - never a reviewer's approval alone - before a candidate's finding may be marked applied in the section's improve record. | cap-evaluation already states that a self-improvement loop should make its gate a precondition for applying its own change, not a report written afterwards; today's ceremony applies first and reviews as a separate pass, which is that ordering reversed. | proposed | `T-t4-04` |
| 3 | Proposed: close the edited-in-place stage. Wire promote_revision to cap-capability-registry's publish with rollback_to set, and stop writing to a target's checked-out skill.json from anywhere except a later session that checks out the newly published version on purpose. | cap-capability-registry already states that a change is a new version record, never an edit to the one that is there; a promotion that still writes the checked-out file directly has not closed this stage, whatever the gate reports. | proposed | `T-t4-04` |
| 4 | Build the second executor on both stages closed at once: seed_candidate and author_revision may still run inside a session or an event handler, but promotion authority moves entirely to cap-evaluation's outcome and cap-capability-registry's publish. Kill the authoring session mid-candidate and resume promotion from the passed EvaluationReport alone, with no session attached. | build-adapter-pair requires the second adapter to break a real assumption of the first; the assumption today's executor rests on is that a live session both authors and approves a candidate in one unbroken run, and the second breaks exactly that. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 5 | Wire the cross-cutting concerns to the candidate iteration, not to the section: re-stamp correlation attributes on every candidate's spans and CandidateOutcome, take an idempotency lease on promote_revision so a re-delivered passed EvaluationReport cannot publish a second registry record for the same candidate_id, and record provenance per artifact a promotion produces. | xc-correlation owns the dispatch-attribute rule, xc-idempotency-lease the keyed lease and xc-provenance-chain the per-artifact record; this step only says where the three attach in this composition. Correlation must ride on an explicit resource attribute set at dispatch, which agentic-stack records as the measured A7 finding; a candidate iteration is a dispatch boundary, and promote_revision is exactly the step whose retry could otherwise double-publish. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Run the definition of done below, record it as an evidence record naming the command, the git commit, the tree hash and whether the tree was dirty, and keep both adapter rows claimed until a clean-tree run exists for both. | build-evidence-record already refuses the measured label on a dirty tree; swappability is a tested property and not an intention, so the pair stays claimed until the swap and the gate have both actually been run on a tree nobody else has to take on faith. | sourced | `F-a5-04` "whether the tree was dirty" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Measure the executor you already have against the contract before wrapping it, the way compose-improvement-loop itself measures the loop's effect under this same quote. This repository's own `python3 tools/ceremony_check.py`, run in this session, reports 'numbering ok (contiguous from 1, one section each)' and a findings-per-skill trend of 1.00 at ceremony 1 falling to 0.00 by ceremony 8 and 10 - real evidence the review-and-improve half of the loop works - and the same run shows the tool's own numbering check never exits non-zero even when it prints a PROBLEM line, which is the diagnostic-not-a-gate finding step 2 names. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Proposed: for a session-driven executor, a change to the author brief or a skill does not reach a ceremony already in flight, because the process reads what it was launched with. Put anything that must take effect mid-run where the next iteration reads it fresh from disk, and treat that asymmetry as a property of this executor rather than a defect in the loop. | proposed | `F-a7-04` |
| Proposed: keep the no-session resume test in the suite rather than in a runbook. Today's executor cannot even be asked to resume with no session attached, since it has none to lose; the second executor's entire reason for existing is that this is exactly the case it has to survive. | proposed | `F-part-c-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-ceremony-review-improve-session` | today | This repository's own review-and-improve pass: build-ceremony's review record names a finding, a live session edits the target skill.json and its render to address it, re-renders and re-validates, and commits; the review record's severity and a reviewer's prose stand in for a gate, and the commit itself is the promotion. Its records are kb/ceremonies/ceremony-01 through ceremony-10 (and the ceremony-11 compose and xc groups in progress), state/lessons.jsonl and kb/ledger.jsonl, read with `python3 tools/ceremony_check.py`. E-adapter-ceremony-review-improve-session is a proposed entity id, not a knowledge-base entity: kb/entities.jsonl carries adapter entities only for the capability rows of PASS.md B3, and this composition has no row there. | It has no cap-evaluation gate - nothing can return outcome=failed on measured evidence, only a reviewer's read of a diff - and it has no registry, so a promoted change has no rollback_to and no prior version to resolve back to if it regresses. Its own diagnostic, tools/ceremony_check.py, never exits non-zero even when it prints a numbering PROBLEM line, so nothing downstream is gated by its output either. Every record it wrote in this session carries dirty true for at least one of the three files it reads, which is why this row is claimed rather than measured. | Express a closed ceremony's applied finding as a candidate_source of ceremony_finding and set promotion_authority to session_reviewer in the executor binding; select the other executor by setting promotion_authority to evaluation_gate and registry_publish to true, with nothing in compose-improvement-loop's own contract changing. | claimed | `T-t4-04`, `F-a5-04` "improves the skills that produced it, and the loop continues" |
| `E-adapter-evaluation-gated-registry-pipeline` | second | The SECOND executor for this composition: cap-evaluation's evaluate is the sole promotion authority - a passed outcome, never a reviewer's judgment - and cap-capability-registry's publish is the only write path, both triggered by an event with no session attached, such as a webhook on a closed ceremony's improve record or a scheduled cap-evaluation replay against the current baseline. E-adapter-evaluation-gated-registry-pipeline is a proposed entity id, not a knowledge-base entity: this composition has no row in PASS.md B3 for kb/entities.jsonl to carry an adapter entity for. | It is not built and not wired to anything running today. cap-evaluation's own open question records that PASS.md has no Evaluation row and both its adapters are claimed; cap-capability-registry's own open question records the same for its registry interface. This row inherits both gaps rather than resolving them, so the pair is unproven until at least one real gate and one real registry exist to publish to. | Set promotion_authority to evaluation_gate and registry_publish to true in the executor binding and run the same conformance suite; if any CandidateOutcome field or any ImprovementCandidate field has to change to run on this executor, the boundary is shaped around the session executor. | claimed | `F-b1-04`, `F-part-c-05` "the second exists to prove the first is not load-bearing" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/compose-improvement-loop/test.sh && python3 harness/compose-improvement-loop/conformance.py --adapter dryrun --report harness/compose-improvement-loop/out/measure-before.json && python3 harness/compose-improvement-loop/conformance.py --adapter second --report harness/compose-improvement-loop/out/measure-after.json && python3 harness/compose-improvement-loop/conformance.py --merge harness/compose-improvement-loop/out/measure-before.json harness/compose-improvement-loop/out/measure-after.json --report harness/compose-improvement-loop/out/measure-merged.json |
| Expected | Measured by tools/measure.py at ebb7068: exit 0; last lines:   ok   S5 both drivers passed their own conformance run   [25/25 and 25/25] \| conformance PASSED: 5/5 cases, merged swap proof |
| Deliberate breakage | sed -i 's/return outcome == PASSED/return True/' harness/compose-improvement-loop/interface.py -- in promote_on_pass, the decision rule every driver is bound with by default, this makes the checkpoint advance on every gate outcome (failed and inconclusive included), not only on passed - the same symptom the harness's own --break-gate flag reproduces (promote_regardless), but reached here by editing the rule callers actually run rather than by passing that flag. Restored with git checkout -- harness/compose-improvement-loop/interface.py. |
| Expected failure | Measured by tools/measure.py at ebb7068: exit 1; last lines:   ok   the declaration schema requires an iteration ceiling \| passed 47, failed 15 |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Composes with

Builds on: `compose-improvement-loop`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which knowledge-base entity names this repository's own ceremony review-and-improve pass as an adapter? `python3 tools/kb.py tree` shows adapter and swap-candidate entities only for the capability rows of PASS.md B3, and this composition has no row there, so the today row above uses a minted id, the same gap build-adapter-pair already names under this quote. | Either an entity added to kb/entities.jsonl for compositions generally, following compose-loop-implement's own E-adapter-section-loop-script, or a decision that composition adapters are named only in skills. | Keep E-adapter-ceremony-review-improve-session as a proposed entity id declared in the row, and leave it out of the skill's entities list so nothing resolves it as a knowledge-base record. | `F-part-c-06` "A required output, not an apology." |
| Should the second executor's gate replay against a case set built from this repository's own closed ceremonies, or against a synthetic corpus written for skill-revision generally? compose-improvement-loop states the quote below for the same underlying record. | A case set built from the ten closed ceremonies' findings, replayed through a candidate authored against each, compared against a synthetic corpus's pass rate on the same candidates; cap-evaluation already requires both halves for its own corpus (X-cap-evaluation-002). | Start from this repository's own closed ceremonies as the recorded half, since they are the only population of real findings on file, and add synthetic cases for skill layers no closed ceremony has exercised yet. | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Is one candidate one idempotency key, or does a retried gate_revision on the same content_ref reuse the key from the failed attempt? | A candidate retried twice with the same content_ref but a different loop_id, checked against whether the registry treats the second promotion as a new record or a conflict; xc-idempotency-lease owns the lease semantics this composition would reuse rather than redefine. | One idempotency key per (candidate_id, loop_id) pair, so a retried candidate under a fresh loop_id is free to promote even if an earlier loop_id for the same target failed. | `F-b4-08` "Every externally-triggered action is safe to replay" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
