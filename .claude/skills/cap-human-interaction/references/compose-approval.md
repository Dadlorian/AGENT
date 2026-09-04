---
name: "compose-approval"
description: "How to assemble an approval gate as a composition rather than a screen: a step that stops before an irreversible action, parks on a durable record carrying a named view, a deadline, a stated decider and the wire a decision may arrive over, and resumes exactly once on the run's own correlation id with one of approve, edit, reject or return-with-notes. Load it when a workflow has to stop and ask a person before doing something it cannot undo, when designing a review step or a sign-off, when deciding what happens if nobody answers, when a decision may be delivered twice or arrive after the run ended, when someone proposes a second inbox or a bespoke approval page, or when a parked item has no owner, no deadline and no way to say change this and try again."
---

# compose-approval (folded into `cap-human-interaction`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the recipe for a gate: a workflow runs up to an irreversible action and stops on a durable record, a person is given something they can actually decide from, and the run continues exactly once on the identifier it already had - so that pausing for a human is a composition of capabilities this platform already owns rather than a feature of whichever screen is in front of the decider. | sourced | `X-compose-approval-001`, `F-b4-08`, `T-t6-02` "the workflow runs up to the point of the irreversible action and stops, storing its state" |

## Entities

| Entity |
|---|
| `E-rule-b1-5` |
| `E-rule-b1-6` |
| `E-rule-b1-7` |
| `E-seam-state` |
| `E-concern-idempotency` |
| `E-concern-identity` |
| `E-capability-work-intake` |
| `E-capability-scheduling` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| declare_gate (proposed operator set; the composition adds a gate to a step, it does not define what an ask is - cap-human-interaction owns that) | the step whose action is irreversible, a named view the decider is shown, the deciding subject and the wires a decision may arrive over, a deadline, the outcome set, and the step to re-enter on return-with-notes (proposed) | a gate declaration resolved with the plan: refused before execution if the view is missing, if the deadline is missing, or if the plan would nest past its depth bound (proposed) | proposed | `REF-10-05`, `REF-5-2-13`, `REF-3-2-10` |
| return_with_notes (proposed) | the fourth outcome: the decider's notes and the gate id | re-entry at the step named on the gate with the notes as input, under the budget that remains, and a fresh gate id; this is the only outcome that puts work back into the graph rather than ending the gate (proposed) | proposed | `F-a2-01`, `X-end-to-end-018` |

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: four outcomes, and only one of them puts work back. cap-human-interaction states the four decisions a person may return (X-entry-composition-023); this composition binds three of them to gate outcomes that end the gate - approve, edit and reject - and adds return-with-notes, which re-enters the graph at the step named on the gate with the notes as input and parks again. This is the one enumeration of outcomes in this skill and every other row points at it. The unit PASS.md A2 records already offers the triple plus the return. | sourced | `F-a2-01`, `X-entry-composition-023` "Approve / reject / return a parked workflow from a phone" |
| cap-human-interaction fixes resume identity for the interface: the client continues the interaction by sending a new message with the same taskId and contextId. The consequence a composition must preserve is that the gate record stores the run's own correlation id and an outcome is matched against it, so the run that continues is provably the run that parked and not a new one wearing its name. | sourced | `X-end-to-end-014` "the client continues the interaction by sending a new message with the same taskId and contextId" |
| xc-idempotency-lease states the placement of the claim and cap-idempotency the claim itself: Every externally-triggered action is safe to replay. A delivered decision is externally triggered, so the consequence here is that the resume boundary acquires its own lease scoped to the gate id - ten deliveries of one outcome resume the run once, a duplicate arriving while the first resume is still running attaches to it, and a decision delivered after the gate closed is a no-op rather than a second run. | sourced | `F-b4-08`, `T-t2-03` "Every externally-triggered action is safe to replay" |
| agentic-stack states design rule 5 as a test (F-b1-06): Planning is a pure function and completes before execution begins. Three consequences a gate must preserve, the last two following the reference example: the gate declares its own cost contribution so a parent estimate is the sum of its children rather than a guess; the depth bound is checked at resolve time, so a sub-plan that would nest past the limit is refused before anything executes; and a parked gate accrues no spend at all, because it holds no process while it waits. | sourced | `F-b1-06`, `REF-5-2-12`, `REF-5-2-13`, `X-entry-composition-029` "Planning is a pure function and completes before execution begins" |
| The cross-cutting guarantees are not suspended while a run is parked, and a gate is not a place a caller may opt out of them: cap-work-intake and cap-consumption state the rule for an entry - the platform applies each; a caller cannot decline them - and the consequence a composition must preserve is that the gate record, the ask, the outcome and the resumed step each carry the run's correlation attributes, a non-null actor, a budget ceiling and a lease, so a gate offering a way to continue without any of them is not a gate. | sourced | `F-b4-01`, `F-b1-08` "The platform applies each; a caller cannot decline them." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the criterion never travels in the view. agentic-stack states design rule 6 (F-b1-07), that an agent sees its outcome, never the criterion it is judged against; what a gate forbids is putting the grading rule into the view, the response schema or the notes a return carries back, because everything a gate shows can be read by the unit that resumes and will be graded. A human reviewer may be shown the criterion by the Judge's own surface; the parked gate is not that surface. | proposed | `F-b1-07` |
| Proposed: there is no force-resume, no skip and no administrative continue that leaves the gate open. Each of those is an unrecorded approval by another name, and the gate record is the only place the deciding actor is written down. The only ways out of a parked gate are the four outcomes and expiry. | proposed | `F-b4-03`, `X-end-to-end-063` |
| Proposed: no wire handle escapes into the composition. A session token, a message receipt, an inbox cursor or a delivery id may be recorded for audit, but none of them may become the gate id, the correlation id or the idempotency key, or the run becomes resumable only by whoever holds one particular channel and the second channel can never be proved equivalent. | proposed | `F-b1-04`, `X-entry-composition-022` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put the gate immediately before the step whose action is irreversible, not around the plan, and declare it there with five things: the named view, the deciding subject, the wires a decision may arrive over, the deadline, and the outcome set including the step to re-enter on return-with-notes. | Proposed, following the reference example: a plan with a gate is five fields and one gate declaration with its view, and the view is required the moment the step declares a human gate. A gate around the whole plan asks a person to approve something they cannot see the boundary of. | proposed | `REF-3-4-03`, `REF-3-2-10` |
| 2 | Resolve the gate with the plan, before anything executes: refuse a gate with no view, refuse a gate with no deadline, refuse a child that would nest past the depth bound, and reconcile the plan estimate against the sum of the children rather than against a top-level guess. | agentic-stack states design rule 5 (F-b1-06) and this skill's invariant draws its three consequences. Doing the refusals at resolve time is what makes them cheap: a gate discovered to be undecidable while a person is waiting has already cost the run everything up to that step. | sourced | `F-b1-06`, `REF-5-2-13` "Planning is a pure function and completes before execution begins" |
| 3 | Park by writing a durable gate record through the state seam at the moment the step would have executed, and hold no process, no connection and no in-memory timer while waiting. | A suspended step waits at zero cost, however long it takes, and a checkpointed run can pause, resume, rewind and branch; a gate implemented as a blocked worker converts a person going home into a lost run. | sourced | `X-entry-composition-029`, `X-cross-structure-046` "The function waits at zero cost, however long it takes" |
| 4 | Emit the ask through cap-human-interaction, one per wire the gate named, and let it own what a person sees and answers. Do not draw a screen in the composition and do not open a second inbox. | Proposed: cap-human-interaction fixes the ask, the typed response schema and the four decisions; a composition that renders its own approval page has made the gate resumable only from that page, which is the coupling both layers exist to remove. | proposed | `X-entry-composition-016`, `X-compose-approval-005` |
| 5 | Register the deadline as an occurrence through cap-scheduling rather than as a timer inside whatever is running, and make expiry write the gate terminal and terminate the run with the registered deadline-exceeded problem. | cap-human-interaction states the rule that you should design explicit timeouts for human steps rather than letting approvals sit indefinitely; the composition-level consequence is where the clock lives, because a timer inside a process dies with the process and leaves a gate that is open forever with nobody watching it. | sourced | `X-cap-human-interaction-008`, `F-b3-15` "you should design explicit timeouts for human steps rather than letting approvals sit indefinitely" |
| 6 | Acquire the idempotency lease on the resume boundary, scoped to the gate id, before any outcome is applied - not at the door the run originally came in through, and not inside any one wire's handler. | xc-idempotency-lease states that the claim is applied across the whole structure and not only at the door (T-t2-03), so a delivered decision is an external trigger at a later boundary and needs its own claim there. This is the single line the definition of done below deletes to prove the check can fail. | sourced | `T-t2-03`, `F-b4-08` "State, telemetry, and every cross-cutting concern are managed across the entire structure" |
| 7 | Bind the deciding actor onto the outcome and extend the run's delegation chain by that hop before the run continues, refusing an outcome from a subject the gate did not name with the registered policy-denied. | xc-identity-delegation states the guarantee for every action (F-b4-03); deciding a gate is an action like any other, and a resume whose actor is null is an approval that nobody can be shown to have given. | sourced | `F-b4-03` "Every action names an actor" |
| 8 | Deliver the outcome into the platform through cap-work-intake's one envelope, as an entry that steers the existing correlation id, and never as a new root run with its own budget. | cap-work-intake states that all four entries enter through the same shape, and cap-scheduling draws the same rule for a firing schedule, so a decision does not get a private door either; the composition-level consequence is that the envelope carries the existing correlation id, which is what keeps the resumed run inside the ceiling, the chain and the trace it already had. | sourced | `T-t6-02`, `F-b3-08` "All four enter through the same shape." |
| 9 | Implement return-with-notes as a re-entry edge rather than a fourth verdict: write the notes, re-enter at the step the gate named, deduct nothing from the outcome set, spend from the budget that remains, and open a fresh gate id when that step reaches the gate again. | The unit PASS.md A2 records already offers return alongside approve and reject, and a reviewer who can only approve or reject has to reject work that needed one change; an edit-in-place review beats approve-then-fix, and a return is the same idea when the change is not the reviewer's to make. | sourced | `F-a2-01`, `X-end-to-end-018` "Optional edit-in-place beats approve-then-fix." |
| 10 | Proposed: open references/usage.md when you need the worked gate declaration for each of TARGET T1's three ways in, the full ApprovalGate and GateOutcome schemas, or the worked rejection. The body of this skill is enough without it. | Proposed: our progressive-disclosure convention. The three worked declarations and two full schemas are longer than the recipe they illustrate, and a reader assembling a gate needs the recipe first. | proposed | `T-t3-01` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Gate only the irreversible or high-cost actions. The research on file is blunt about the cost of the alternative: gating everything overloads reviewers and trains them to approve without reading, which converts a control into a rubber stamp while every metric still says the gate is there. | sourced | `X-compose-approval-006`, `X-end-to-end-063` "gating everything overloads reviewers and trains them to approve without reading" |
| Give the decider the artifact, not a verdict box. Optional edit-in-place beats approve-then-fix, and a gate whose view is a summary with two buttons quietly degrades edit and return-with-notes into approve-with-a-comment. | sourced | `X-end-to-end-018`, `X-end-to-end-019` "Optional edit-in-place beats approve-then-fix." |
| Test the clock and the duplicate in the same fixture. Prior art states the pair as one rule: messages will be delivered more than once, and every step should have a timeout - so a suite that fires ten copies but never lets a deadline pass has tested half of what a gate is for, and one that expires gates but never duplicates a decision has tested the other half. | sourced | `X-xc-compensation-006`, `X-cap-human-interaction-008` "Every step in a saga should have a timeout" |
| agentic-stack states the structurally-green-gate finding (F-a7-03): those establish well-formedness, not correctness. Its consequence for an approval suite is that a run in which no gate ever parked will pass every assertion about duplicate resumes, so assert that gates were declared and parked before asserting anything about how they resumed. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/workflow/test.sh && python3 harness/workflow/conformance.py --adapter dryrun --adapter second |
| Expected | exit 0, `passed 23, failed 0` from the gate, and one line per executor reading `executor_marker=in-process-journal/0.1` and `executor_marker=queue-state-machine/0.1` with `steps_committed=8 steps_replayed=6 effects_for_publish=1 duplicate_effects=0 declared_gap_honoured=true checks=28/28`, closing on `adapters_run=2 distinct_markers=2`. The 28 checks include the four decided outcomes, ten deliveries of one decision resuming the run once, and an expiry followed by a late decision that is a no-op. It is the gate compose-approval-implement owns; run here on 2026-09-03 and exited 0. Claimed, stated as the gap: what this run swaps is the durable executor, not the decision wire - `wire` appears nowhere in harness/workflow/conformance.py or test.sh and flow.py takes one --wire with a single default of parked-item - so this facet's own `wires_run >= 2`, its `views_missing == 0` and its `gates_parked == 5` counters have never been measured, and tools/conformance/approval_gate.py does not exist in this repository. |
| Deliberate breakage | In harness/workflow/adapters/dryrun.py, break the redelivery dedup in record_decision so a prior gate-decided record is never recognised as a duplicate: sed -i 's/for r in prior)/for r in [])/' harness/workflow/adapters/dryrun.py, then git checkout -- harness/workflow/adapters/dryrun.py. |
| Expected failure | exit 1 with `FAIL every check passed (expected [], got [{"check": "F ten deliveries of one decision resume the run once", "detail": "applied=10"}])` and `passed 18, failed 5`: only the exactly-once assertion moves, while parking, the four outcomes, the expiry case and both executor markers stay green, so a reader can tell the fault was the missing claim rather than a broken gate. Claimed here: this edit moves the resume seam compose-approval-implement owns; nothing on disk can make the wire-swap counter fail today because only one wire exists. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-08` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `cap-work-intake`, `cap-scheduling`, `xc-idempotency-lease`

Used by: `compose-approval-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Who may answer a gate, and over what wire, once plans nest? This skill makes the decider and the wires declared fields, which answers the shape of the question but not the resolution rule: at depth 3 with a gate at each level, is the decider the root run's owner, the subject the ask names, or whoever the parent escalated to? | cap-human-interaction carries the same open question for the interface (REF-11-07, REF-7-07); what would settle it here is parking a gate at each level of a depth-3 run across both wires and recording, per gate, which subject the policy admitted and which wire carried the decision. The reference names running each stage as its own workflow as the common workaround rather than an answer. | Proposed: the gate declaration resolves its decider from the root run's owner unless the step overrides it, and an outcome is accepted from any listed wire that can authenticate that subject against the correlation id. The reference records this as a gap against this skill (REF-12-10) and the declared fields are the part of it this skill closes. | `REF-12-10`, `REF-11-07`, `REF-7-07` |
| Where does the expiry sweep run, given that the orchestrator human-in-the-loop signals were designed around is recorded as not listening? | 1-3-1 applied (TARGET T5) and recorded on 2026-09-03. Options: (a) an occurrence registered through cap-scheduling, evaluated by whatever serves that capability; (b) a deadline field on the gate record swept by the same reader that resumes; (c) a durable timer inside the executor that owns the run. Recommendation followed: (a), because it is the only one that keeps expiry working when nothing is executing and the run holds no process. What would settle it is measuring how long a gate stays open past its deadline under each, with the executor stopped. | Proposed: register the deadline through cap-scheduling and treat the sweep as an entry like any other. (c) is refused outright here because it reintroduces the process the park just released. | `T-t5-02`, `F-a6-02` "human-in-the-loop signals are designed around it and it is currently down" |
| Is return-with-notes a fourth outcome of the gate or an edge of the graph that a gate happens to trigger? | Whether a returned run ever needs anything the gate does not already carry - a different budget slice, a different criterion, a different decider on the second pass. If it never does, it is an outcome; if it does, it is an edge core-graph owns and the gate only names its target. | Proposed: an outcome, with return_to_step_id on the gate. Modelling it as a graph edge would put the reviewer's judgment into the plan's topology, and the reviewer decides at run time which the plan cannot know at resolve time. | `F-a2-01`, `T-t5-02` "return a parked workflow from a phone" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session compose-approval 2831cb4f, 2026-09-03 |
