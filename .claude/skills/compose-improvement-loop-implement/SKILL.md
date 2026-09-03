---
name: compose-improvement-loop-implement
description: How the self-improvement loop is actually built here: this repository's own ceremony review-and-improve pass as the first executor - a live session that edits the target file in place and commits, a reviewer's judgment standing in for a gate - a second executor whose sole promotion authority is cap-evaluation's passed outcome and whose only write path is cap-capability-registry's publish, with no session attached; the migration between them; where correlation, an idempotency lease and provenance attach to one candidate iteration; and a definition of done run against this repository's own tools/ceremony_check.py. Load it when writing or reviewing code that seeds, gates or promotes a candidate, when deciding what the second executor should be, when a promotion has to survive with no session attached, when asking whether closed ceremonies already conform to compose-improvement-loop's contract, or when a finding is applied by editing a file directly instead of through a gate.
---

# compose-improvement-loop-implement

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
| Proposed: the pair differs on one named axis build-adapter-pair requires filled in rather than asserted - who or what holds promotion authority. Today's executor makes a session reviewer's read of a diff the authority; the second makes cap-evaluation's passed outcome the only authority, with no reviewer and no session in the promotion path at all. | proposed | `F-b1-04`, `F-part-c-05` |
| compose-improvement-loop already states that promote_revision writes only to cap-capability-registry, never to a target's checked-out file. Today's executor is non-conformant on exactly this point: build-ceremony's improve record applies a finding by editing the target skill.json and its render directly and committing, which is the in-place edit the ideal facet's invariant on X-cap-capability-registry-007 forbids. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| compose-improvement-loop already states that gate_revision runs cap-evaluation's evaluate before a candidate may be promoted. Today's executor has no such call: the review record's severity field and a reviewer's prose stand in for a gate, and nothing here can return outcome=failed on measured evidence the way cap-evaluation's evaluate can. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Proposed: both executors emit the same CandidateOutcome record - compose-improvement-loop's own shape, unchanged - so nothing downstream can tell which one ran. On today's executor evaluation_report_id and registry_record are always null; the conformance suite asserts the shape holds regardless, rather than special-casing either executor's nulls. | proposed | `F-b1-04` |
| build-evidence-record already states that a result produced from a dirty tree may never carry the label measured, because nobody else can reproduce the tree it ran against (F-a5-04). The consequence owned here: the baseline and breakage runs of tools/ceremony_check.py recorded in this skill's definition of done ran against a working tree where kb/ledger.jsonl and state/lessons.jsonl - two of the three files that command reads - carried unrelated uncommitted changes from a concurrent session, so both runs are labelled claimed despite being real, observed output. | sourced | `F-a5-04` "whether the tree was dirty" |
| Proposed: today's diagnostic never refuses anything. tools/ceremony_check.py prints a numbering PROBLEM line when ceremony numbers collide or a section repeats, and still exits 0 - it is evidence for a human to read, not a gate a pipeline can depend on. This is the same non-conformance as the missing cap-evaluation call, stated at the level of the one tool this repository actually runs today. | proposed | `F-part-c-04` |
| Proposed: this repository's own reviewer bias gap, which compose-improvement-loop's invariants name as unresolved, is a property of the session executor specifically - a session reviewer is a single model or person with no held-out audit - and is not inherited by the second executor, whose sole authority is cap-evaluation's evaluate and which core-judge already requires to run against a held-out criterion set on an unpredictable cadence. | proposed | `F-b1-07` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: neither executor's vocabulary reaches the candidate - no reviewer identity, no commit sha, no registry signing key appears in an ImprovementCandidate or a CandidateOutcome. They appear in the executor binding and in the Adapters table below, and nowhere else, the way agentic-stack already requires products to stay out of core and interface material (F-part-c-09). | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Bind to today's executor first: map a closed build-ceremony's applied finding directly onto a CandidateOutcome with decision=promoted, evaluation_report_id null and registry_record null, and write that binding as configuration conforming to the executor-binding shape above. | Proposed: an adapter is a binding a conformance suite can run, not a claim that an existing script is close enough; writing it down is what exposes the two gaps step 2 names rather than leaving them implicit. | proposed | `F-b1-04` |
| 2 | Name today's two non-conformances precisely before building anything: no gate_revision call exists, so a reviewer's judgment is the only authority a finding is applied on; and promote_revision writes the target skill.json in place through a git commit, so there is no rollback_to and no prior version to resolve back to if the applied change regresses. | compose-improvement-loop already states both as invariants of its own contract, under this same quote (T-t4-04); migration begins by naming the gap the thing being wrapped actually has, not by assuming it is close enough to conform. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| 3 | Proposed: close the missing-gate stage first. Wire gate_revision to a real cap-evaluation adapter and require outcome=passed - never a reviewer's approval alone - before a candidate's finding may be marked applied in the section's improve record. | cap-evaluation already states that a self-improvement loop should make its gate a precondition for applying its own change, not a report written afterwards; today's ceremony applies first and reviews as a separate pass, which is that ordering reversed. | proposed | `T-t4-04` |
| 4 | Proposed: close the edited-in-place stage. Wire promote_revision to cap-capability-registry's publish with rollback_to set, and stop writing to a target's checked-out skill.json from anywhere except a later session that checks out the newly published version on purpose. | cap-capability-registry already states that a change is a new version record, never an edit to the one that is there; a promotion that still writes the checked-out file directly has not closed this stage, whatever the gate reports. | proposed | `T-t4-04` |
| 5 | Build the second executor on both stages closed at once: seed_candidate and author_revision may still run inside a session or an event handler, but promotion authority moves entirely to cap-evaluation's outcome and cap-capability-registry's publish. Kill the authoring session mid-candidate and resume promotion from the passed EvaluationReport alone, with no session attached. | build-adapter-pair requires the second adapter to break a real assumption of the first; the assumption today's executor rests on is that a live session both authors and approves a candidate in one unbroken run, and the second breaks exactly that. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 6 | Proposed: write one conformance suite against compose-improvement-loop's CandidateOutcome shape, parameterised over both executors: assert the same required fields hold on both, edited_in_place is false on both, and registry_record is non-null only on the second. | Two suites drift into two contracts, and the suite is the only thing that can report adapters_run == 2 rather than one executor and one intention. | proposed | `F-b1-02` |
| 7 | Wire the cross-cutting concerns to the candidate iteration, not to the section: re-stamp correlation attributes on every candidate's spans and CandidateOutcome, take an idempotency lease on promote_revision so a re-delivered passed EvaluationReport cannot publish a second registry record for the same candidate_id, and record provenance per artifact a promotion produces. | Correlation must ride on an explicit resource attribute set at dispatch, which agentic-stack records as the measured A7 finding; a candidate iteration is a dispatch boundary, and promote_revision is exactly the step whose retry could otherwise double-publish. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 8 | Proposed: migrate in shadow. Replay this repository's own ten closed ceremonies' applied and declined findings through the executor binding's candidate, gate and promote shape, and compare the resulting promoted and declined counts against the real applied and declined lists on file in kb/ceremonies/ceremony-01-improve.json through ceremony-10-improve.json. Cut over only when they agree. | The recorded ceremonies are the only population of real findings available, and a shadow comparison is what turns a claim that the binding preserves behaviour into a check that can fail. | proposed | `F-part-c-08` |
| 9 | Run the definition of done below, record it as an evidence record naming the command, the git commit, the tree hash and whether the tree was dirty, and keep both adapter rows claimed until a clean-tree run exists for both. | build-evidence-record already refuses the measured label on a dirty tree; swappability is a tested property and not an intention, so the pair stays claimed until the swap and the gate have both actually been run on a tree nobody else has to take on faith. | sourced | `F-a5-04` "whether the tree was dirty" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Measure the executor you already have against the contract before wrapping it, the way compose-improvement-loop itself measures the loop's effect under this same quote. This repository's own `python3 tools/ceremony_check.py`, run in this session, reports 'numbering ok (contiguous from 1, one section each)' and a findings-per-skill trend of 1.00 at ceremony 1 falling to 0.00 by ceremony 8 and 10 - real evidence the review-and-improve half of the loop works - and the same run shows the tool's own numbering check never exits non-zero even when it prints a PROBLEM line, which is the diagnostic-not-a-gate finding step 2 names. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Proposed: for a session-driven executor, a change to the author brief or a skill does not reach a ceremony already in flight, because the process reads what it was launched with. Put anything that must take effect mid-run where the next iteration reads it fresh from disk, and treat that asymmetry as a property of this executor rather than a defect in the loop. | proposed | `F-a7-04` |
| Proposed: do not let the registry's vocabulary - version, digest, signature, rollback_to - name a field inside a candidate's rationale or an ImprovementCandidate's seed. Audit the binding for concepts that only mean something under one executor and push each back into the adapter row, the shaping audit build-adapter-pair prescribes. | proposed | `F-meta-04` |
| Proposed: keep the no-session resume test in the suite rather than in a runbook. Today's executor cannot even be asked to resume with no session attached, since it has none to lose; the second executor's entire reason for existing is that this is exactly the case it has to survive. | proposed | `F-part-c-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-ceremony-review-improve-session` | today | This repository's own review-and-improve pass: build-ceremony's review record names a finding, a live session edits the target skill.json and its render to address it, re-renders and re-validates, and commits; the review record's severity and a reviewer's prose stand in for a gate, and the commit itself is the promotion. Its records are kb/ceremonies/ceremony-01 through ceremony-10 (and the ceremony-11 compose and xc groups in progress), state/lessons.jsonl and kb/ledger.jsonl, read with `python3 tools/ceremony_check.py`. E-adapter-ceremony-review-improve-session is a proposed entity id, not a knowledge-base entity: kb/entities.jsonl carries adapter entities only for the capability rows of PASS.md B3, and this composition has no row there. | It has no cap-evaluation gate - nothing can return outcome=failed on measured evidence, only a reviewer's read of a diff - and it has no registry, so a promoted change has no rollback_to and no prior version to resolve back to if it regresses. Its own diagnostic, tools/ceremony_check.py, never exits non-zero even when it prints a numbering PROBLEM line, so nothing downstream is gated by its output either. Every record it wrote in this session carries dirty true for at least one of the three files it reads, which is why this row is claimed rather than measured. | Express a closed ceremony's applied finding as a candidate_source of ceremony_finding and set promotion_authority to session_reviewer in the executor binding; select the other executor by setting promotion_authority to evaluation_gate and registry_publish to true, with nothing in compose-improvement-loop's own contract changing. | claimed | `T-t4-04`, `F-a5-04` "improves the skills that produced it, and the loop continues" |
| `E-adapter-evaluation-gated-registry-pipeline` | second | The SECOND executor for this composition: cap-evaluation's evaluate is the sole promotion authority - a passed outcome, never a reviewer's judgment - and cap-capability-registry's publish is the only write path, both triggered by an event with no session attached, such as a webhook on a closed ceremony's improve record or a scheduled cap-evaluation replay against the current baseline. E-adapter-evaluation-gated-registry-pipeline is a proposed entity id, not a knowledge-base entity: this composition has no row in PASS.md B3 for kb/entities.jsonl to carry an adapter entity for. | It is not built and not wired to anything running today. cap-evaluation's own open question records that PASS.md has no Evaluation row and both its adapters are claimed; cap-capability-registry's own open question records the same for its registry interface. This row inherits both gaps rather than resolving them, so the pair is unproven until at least one real gate and one real registry exist to publish to. | Set promotion_authority to evaluation_gate and registry_publish to true in the executor binding and run the same conformance suite; if any CandidateOutcome field or any ImprovementCandidate field has to change to run on this executor, the boundary is shaped around the session executor. | claimed | `F-b1-04`, `F-part-c-05` "the second exists to prove the first is not load-bearing" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Two checks against this repository's own today-adapter, run from the repository root. (a) `python3 tools/ceremony_check.py`: assert the printed numbering line reads 'ok (contiguous from 1, one section each)' and the last trend line (ceremony 10) reads '0.00 findings/skill'. (b) inject the deliberate breakage below, re-run the same command, assert the numbering line now starts 'PROBLEM:' and names a duplicated ceremony number and a reused section, and assert the process exit code is unchanged (0) in both (a) and (b) - the non-conformance step 2 names. |
| Expected | (a) 'numbering ok (contiguous from 1, one section each)' and '   10: 0.00 findings/skill, proposed share 0.39'. (b) 'numbering PROBLEM: numbers are [5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], expected [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]; section reused across ceremonies: wave-3b'. Exit code 0 in both (a) and (b). |
| Deliberate breakage | Copy kb/ceremonies/ceremony-05-review.json to kb/ceremonies/ceremony-005-review.json - the same ceremony number 5, since the tool parses the number from the filename with `ceremony-(\d+)-review` - leaving every other file untouched, then delete the copy immediately after the run. |
| Expected failure | The numbering line changes exactly as shown above and the trend lines are unaffected, while the exit code stays 0 in both runs - naming the diagnostic itself as the thing that does not gate, not the numbers it reports. Status claimed: both commands were run for real in this session on 2026-09-03 (session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96) and produced exactly the output above; the injected file was removed immediately afterward and `git rev-parse HEAD^{tree}` returned to dc76d3da43bd59d83bb9bd1c270647c856bb0163, its value before the injection. The result is recorded claimed rather than measured because build-evidence-record refuses the measured label on a dirty tree (F-a5-04), and kb/ledger.jsonl and state/lessons.jsonl - two of the three files this command reads - carried unrelated uncommitted changes from a concurrent ceremony-11 session throughout both runs. |
| Status | claimed |
| Evidence | `F-a5-04` "whether the tree was dirty" |

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
