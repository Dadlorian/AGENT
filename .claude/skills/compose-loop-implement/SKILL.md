---
name: compose-loop-implement
description: How a bounded loop is actually built here: the section loop this repository ran as the first executor, a durable executor with no session as the second, the three ways today's loop is not yet conformant, where the ceiling, the correlation attributes, the lease and the typed refusals attach to an iteration, and a definition of done whose breakage is in the wiring rather than in the contract. Load it when writing or reviewing the code that advances iterations, when binding a loop declaration to an executor, when a loop has to survive the death of the process driving it, when deciding what the second executor should be, when a resumed run repeats work it already committed, or when asking where this repository's own loop terminates and whether that reason is one of the three.
---

# compose-loop-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed: build the bounded loop compose-loop specifies on two executors that differ in where a loop's state lives between iterations, and stage the migration from the loop this repository already ran, which is bounded but not yet conformant. | proposed | `F-b1-04`, `T-t4-04`, `F-part-c-05` |

## Entities

| Entity |
|---|
| `E-capability-durable-execution` |
| `E-not-running-temporal` |
| `E-concern-budget` |
| `E-concern-idempotency` |
| `E-rule-b1-3` |

## Contract

### Shapes (JSON Schema 2020-12)

**executor-binding (proposed shape; the configuration that selects which executor advances a loop, and the only place either executor is named)** (proposed; sources: `T-t2-02`, `F-b1-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:loop:executor-binding:0.1",
  "title": "LoopExecutorBinding",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A loop declaration carries none of this: swapping the executor is a configuration edit, so the conformance suite can run the same loop twice by changing one value.",
  "required": [
    "executor",
    "checkpoint_scope",
    "state_between_iterations"
  ],
  "properties": {
    "executor": {
      "type": "string",
      "description": "The adapter id from this skill's Adapters table."
    },
    "checkpoint_scope": {
      "const": "iteration",
      "description": "Per iteration, never per loop. A binding that offers per-loop is the breakage in this skill's definition of done."
    },
    "state_between_iterations": {
      "enum": [
        "session_process",
        "external_store"
      ],
      "description": "The axis the pair differs on, in the field build-adapter-pair calls differs_in_execution_model."
    },
    "resume": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "lease_ttl_s": {
          "type": "integer",
          "minimum": 1
        },
        "max_resumes": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the pair differs on one named axis - where a loop's state lives between iterations. Today's executor holds it in the process of a live session; the second holds it in a store the executor reads on restart. build-adapter-pair requires that axis to be filled in rather than asserted, and a pair that cannot fill it proves nothing. | proposed | `F-b1-04`, `F-part-c-05` |
| Proposed: the loop declaration is byte-identical on both executors and names neither of them. If a loop has to be rewritten to move executors, the boundary is drawn wrong and the pair has found the defect it exists to find, which is what agentic-stack's rule 1 test asks (F-b1-02). | proposed | `F-b1-02`, `F-meta-04` |
| Proposed: today's binding is non-conformant on exactly three counts, and each is a migration stage rather than an excuse - there is no budget ceiling on the run, the exit condition is the section list running out rather than a verdict, and the script leaves the loop early when the checkpoint phase does not push, which is a fourth termination reason compose-loop forbids. | proposed | `T-t4-04`, `F-b4-02` |
| Proposed: both executors emit the same loop-outcome and the same problem objects, so nothing downstream can tell which one ran. The conformance suite asserts that equality directly rather than inspecting each executor's own status vocabulary. | proposed | `F-b4-07`, `F-b1-04` |
| Proposed: build-evidence-record governs what may be labelled measured here (F-a5-04). Every record this repository's own loop wrote carries dirty true, so the loop's runs are evidence that it ran and terminated, and are not a measurement of conformance to the loop contract; the adapter rows below are labelled accordingly. | proposed | `F-a5-04`, `F-part-c-08` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: neither executor's vocabulary reaches the loop - no run id of theirs, no status string of theirs, no replay concept of theirs appears in a loop declaration, a loop-outcome or a problem object. They appear in the binding and in the Adapters table below, and nowhere else. | proposed | `F-part-c-09`, `F-b1-02` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Bind the loop contract to the executor that already runs: map the section list to max_iterations, one section's research, author, review and improve pass to the body, and the checkpoint phase to the per-iteration commit. Write the binding as configuration conforming to the executor-binding shape above. | Proposed: an adapter is a binding that a conformance suite can run, not a claim that an existing script is close enough. Writing it is what exposes the three gaps in step 2 to 4. | proposed | `F-b1-04` |
| 2 | Close the fourth exit first. The script leaves its loop when a section's checkpoint phase does not push, which terminates the run for a reason outside the three compose-loop allows. Map that condition to a cap with on_cap escalate and a typed problem, and assert in the binding's test that no other early exit remains. | Proposed: a fourth termination is the one defect the loop contract names as fatal, and it is already present in the thing being wrapped, so migration begins by removing it rather than by adding features. | proposed | `T-t4-04`, `F-b4-07` |
| 3 | Supply the exit condition the script does not have. Today the loop ends when the section list is exhausted, which is an iteration ceiling wearing the clothes of success; wire evaluate_exit to a criterion_ref resolved outside the body so a run can end on a pass verdict, and classify the exhausted list as the cap it is. | Proposed: without a verdict the loop has two of the three terminations and no way to end as done, so every run reads as a cap and the stop-versus-cap distinction compose-loop states cannot be observed. | proposed | `F-b2-05` |
| 4 | Attach the ceiling. The run carries no budget object today, so wire a root ceiling and a per-iteration slice through the budget interface, decrement per iteration and per descendant dispatch, and make a crossing terminate the loop while the runner survives. | Proposed: xc-budget places the ceiling outside the unit that spends (F-b4-02); a loop whose only bound is its iteration count is bounded in attempts and unbounded in money, because one iteration can fan out. | proposed | `F-b4-02`, `F-b4-01` |
| 5 | Build the second executor on the durable-execution interface: one iteration is one step, the checkpoint and the iteration's effect commit together, and the loop's state lives in a store rather than in a process. Start it, kill it mid-iteration, and resume it with no session attached. | Proposed: the assumption the first executor rests on is that a live session survives the whole loop. The second breaks exactly that, which is the test build-adapter-pair applies to a second adapter (F-b1-04). | proposed | `F-b1-04`, `F-b3-04` |
| 6 | Write one conformance suite against the loop contract - the three terminations, the outcome shape, the resume point - and parameterise it over both executors, selecting one by configuration. The suite imports the loop interface only and never either binding. | Proposed: two suites drift into two contracts, and the suite is the only thing that can say adapters_run equals two rather than one adapter and one intention. | proposed | `F-b1-02`, `F-part-c-04` |
| 7 | Wire the cross-cutting concerns to the iteration, not to the run: re-stamp the correlation attributes on every iteration's spans and problem objects instead of relying on parentage, take an idempotency lease on the resume path, record provenance per artifact an iteration produces, and return both ceilings as typed problems. | Correlation must ride on an explicit resource attribute set at dispatch, which agentic-stack records as the measured A7 finding; an iteration is a dispatch boundary, so this is where the finding bites in a loop. | sourced | `F-a7-02`, `F-b4-08` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 8 | Migrate in shadow: replay the sections this repository already ran through the new binding, and compare per section the termination reason, the iteration count and the cost against the records on file in kb/ledger.jsonl and kb/ceremonies/. Cut over only when both executors agree on all three for every replayed section. | Proposed: the recorded run is the only population of real iterations available, and a shadow comparison is what turns a claim that the binding preserves behaviour into a check that can fail. | proposed | `F-part-c-08` |
| 9 | Record every conformance run as an evidence record naming the command, the script hash, the commit, the tree hash and whether the tree was dirty, and keep the adapter rows claimed until a clean-tree run of the suite exists for both executors. | Proposed: build-evidence-record refuses the measured label on a dirty tree (F-a5-04), and swappability is a tested property rather than an intention, so the pair stays claimed until the swap has actually been run. | proposed | `F-a5-04`, `F-b1-04` |
| 10 | Run the definition of done below on both executors in one invocation, and publish adapters_run, unbounded, resumed_at_iteration and iterations_replayed as named counters rather than an exit code. | Proposed: build-definition-of-done requires a criterion that asserts on a non-zero count of things actually checked, and an exit code alone cannot tell a run that checked both executors from a run that checked neither. | proposed | `F-a7-03`, `F-part-c-04` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: measure the executor you already have against the contract before wrapping it. This repository's own section loop ran ten ceremonies with its records on file in kb/ledger.jsonl and kb/ceremonies/, and it ended by exhausting its section list; that is evidence of a bounded loop and not of a conformant one, and the difference is the whole migration. | proposed | `T-t4-04`, `F-part-c-08` "at the end of each section a ceremony re-reviews the output, improves the skills that produced it, and the loop continues" |
| Proposed: for a session-driven executor, a change to the script does not reach the run already in flight, because the process executes the code it was launched with. Put anything that must take effect during a run where the iteration reads it fresh from disk, and treat that asymmetry as a property of this executor rather than a bug in the loop. | proposed | `F-a7-04` |
| Proposed: do not let the second executor's vocabulary name the fields. Audit the binding for concepts that only mean something under one of them - replay, worker, history, session - and push each back into the adapter, which is the shaping audit build-adapter-pair prescribes. | proposed | `F-meta-04`, `F-b1-05` |
| Proposed: keep the crash test in the suite rather than in a runbook. A resume that is only ever exercised by hand is a resume that works on the day it was written, and the durable executor's entire reason for being here is that it survives a death the first executor cannot. | proposed | `F-part-c-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-section-loop-script` | today | The section loop this repository ran: a script driven by one live session that walks a list of sections, and for each runs research, then parallel authors, then a review and an improve pass that checkpoints by committing. Its records are kb/ledger.jsonl and kb/ceremonies/ceremony-01 through ceremony-10. E-adapter-section-loop-script is a proposed entity id, not a knowledge-base entity: the adapter entities in kb/entities.jsonl exist only for the capability rows of PASS.md B3, and a composition has no row there. | It has no budget ceiling, no verdict-based exit and one termination outside the three - it leaves the loop when a section's checkpoint does not push. Its state lives in the process, so the death of the session ends the run, and every record it wrote carries dirty true, which is why this row is claimed rather than measured. | Express the section list as max_iterations and the per-section pass as the body, then select the other executor by changing state_between_iterations in the executor binding; nothing in the loop declaration changes. | claimed | `T-t4-04`, `F-a5-04` "Work through every item with a self-improvement loop" |
| `E-adapter-temporal` | second | The durable-execution capability's own adapter (F-b3-04) serving here as the SECOND executor for this composition: each iteration is a checkpointed step whose history lives on a server, so the loop advances with no session attached and a restart resumes at the first incomplete iteration. | It is not listening today - PASS.md A6 records the data directory present, nothing on its ports, and durable workflow orchestration designed around it while it is down - so this row is claimed and the pair is unproven until the engine is up or a serverless step log is put in its place. | Set state_between_iterations to external_store in the executor binding and run the same conformance suite; if any loop declaration or assertion has to change, the boundary is shaped around the first executor. | claimed | `F-b3-04`, `F-a6-02`, `F-b1-04` "Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Run the loop conformance suite once per executor in one invocation, with a crash injected on the durable one: `python3 tools/loop_conformance.py --runs 100 --executor session && python3 tools/loop_conformance.py --runs 100 --executor durable --kill-at-iteration 2`. Assert adapters_run == 2, runs_checked == 100 on each, unbounded == 0, resumed_at_iteration == 3 and iterations_replayed == 0 on the durable executor, and outcome_diff == 0 between the two executors' loop-outcome records once executor id and timestamps are removed. |
| Expected | session: runs_checked=100, unbounded=0; durable: runs_checked=100, unbounded=0, resumed_at_iteration=3, iterations_replayed=0; adapters_run=2, outcome_diff=0; exit 0 |
| Deliberate breakage | In the executor binding, move the checkpoint commit from the end of each iteration to the end of the loop - set checkpoint_scope to loop and bind the commit to the loop node rather than to the iteration index - leaving the loop declaration and every assertion untouched. |
| Expected failure | durable: resumed_at_iteration=1, iterations_replayed=2, exit 1 at the resume assertion, while runs_checked=100, unbounded=0, adapters_run=2 and every termination-reason assertion stay green on both executors, so exactly one counter moves and it names the binding rather than the loop contract. Status claimed: neither tools/loop_conformance.py nor either binding exists in this repository yet, and the durable executor is not listening. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion." |

## Composes with

Builds on: `compose-loop`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which knowledge-base entity names this repository's own section loop as an adapter? `python3 tools/kb.py tree` shows adapter and swap-candidate entities only for the capability rows of PASS.md B3, and a composition has no row there, so the today row above uses a minted id. | Either an entity added to kb/entities.jsonl for compositions, or a decision that composition adapters are named only in skills. 1-3-1 applied: reuse a B3 adapter entity (wrong row, and the validator warns for good reason), leave the row without an entity (the schema requires one), or mint and say so - the third was taken because it is the only one that is both honest and checkable, and build-adapter-pair states why an undecidable pair is recorded as an open question rather than shipped quietly (F-part-c-06). | Keep E-adapter-section-loop-script as a proposed entity id declared in the row, and leave it out of the skill's entities list so nothing resolves it as a knowledge-base record. | `F-part-c-06` "A required output, not an apology." |
| What serves as the second executor while the durable engine is not listening? The pair is unproven until something advances a loop with no session attached. | Either the engine started and the crash test run against it, or a serverless step log - a committed row beside each iteration's effect - built and run through the same suite. Both would produce adapters_run == 2 from a real run rather than from a binding that exists on paper, which is the pair obligation build-adapter-pair owns (F-b1-04). | Keep the durable engine as the declared second executor, keep both adapter rows claimed, and treat a serverless step log as the fallback if the engine stays down. | `F-a6-02`, `F-b1-04` "Every interface ships with at least two adapters" |
| Is one ceremony - a review pass and an improve pass over the same section - one iteration or two? The answer decides what max_iterations counts and what a checkpoint covers when this repository's loop is expressed as a conformant one. | A replay of the recorded sections under both readings, comparing resume behaviour after a crash between the review and the improve pass: whichever reading resumes without re-running a committed improve is the right unit. | One section is one iteration, with the review and improve passes as steps of the body, because the checkpoint the script already commits is per section. | `T-t4-04` "at the end of each section a ceremony re-reviews the output" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation compose-loop 2026-09-03 |
