---
name: compose-operators-implement
description: How the closed operator set is actually built here: the interpreted workflow document that runs today, a second engine that compiles the same document ahead of the run, the migration off an operator set that lives in two places at once, where budget, correlation, actor and idempotency attach to an operator, and a definition of done whose breakage is a drift between the schema and the executor. Load it when writing or reviewing the code that walks or compiles a composition, when a component is about to grow its own if-else over operator names, when someone asks 'where is the operator set actually enforced', 'can we run this definition on something else without editing it', or 'why did this workflow run here and refuse there', and before recording any engine-independence result as passing.
---

# compose-operators-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed: build the operator vocabulary compose-operators defines so that the schema is the only place the set is written, two engines with different execution models read the same document unchanged, and engine independence is a report you can run rather than a property anyone asserts - which is build-adapter-pair's test applied to a document instead of to an interface. | proposed | `F-b1-04`, `T-t2-02` "Swappability is a tested property, not an intention." |

## Entities

| Entity |
|---|
| `E-capability-durable-execution` |
| `E-capability-document-validation` |
| `E-standard-json-schema-2020-12` |
| `E-rule-b1-3` |
| `E-rule-b1-7` |

## Contract

### Shapes (JSON Schema 2020-12)

**operator-binding-report (proposed shape; what the conformance run writes, and the fields the definition of done asserts on)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:operator-binding-report:0.1",
  "title": "OperatorBindingReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_ops",
    "engines",
    "engines_run",
    "operators_exercised",
    "drift"
  ],
  "properties": {
    "schema_ops": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "The operator names the schema admits, read from the schema at run time and never retyped in the tool."
    },
    "engines": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "engine_marker",
          "executor_ops",
          "step_order",
          "terminal_outcome"
        ],
        "properties": {
          "engine_marker": {
            "type": "string",
            "description": "Read from the running engine, not from the binding record that selected it."
          },
          "executor_ops": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "step_order": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "terminal_outcome": {
            "enum": [
              "completed",
              "refused",
              "escalated"
            ]
          }
        }
      }
    },
    "engines_run": {
      "type": "integer",
      "minimum": 0
    },
    "operators_exercised": {
      "type": "integer",
      "minimum": 0
    },
    "drift": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Symmetric difference between schema_ops and any engine's executor_ops. A conformant build has this empty."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Both engines read the same document bytes. No pre-pass rewrites, normalises, enriches or lowers the document before one engine sees it and not the other, because the moment one engine needs a transformed copy the swap stops testing anything: build-adapter-pair requires the second engine to run on the first engine's input unchanged, and swappability is a property that has to be tested rather than intended. | sourced | `F-b1-04` "Swappability is a tested property, not an intention." |
| Which engine answered is read from the running engine, never inferred from the configuration that selected it. agentic-stack carries the measured finding that configuration written in the documented place can have no runtime effect; the consequence for this build is that a binding record says what was requested while an engine marker emitted at start says what actually served, and only the second can catch a fallback that silently ran both legs on one engine. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| The second engine is chosen because it breaks a different assumption, not because it is a different product. build-adapter-pair owns that test and its axes (F-b1-04); the axis this pair turns on is when the operator tree is read - during the walk in one process, or once before the run, after which there is no tree - and that difference is recorded in differs_in_execution_model rather than asserted in prose. | sourced | `F-b1-04` "Every interface ships with at least two adapters" |
| No engine name, endpoint or vendor may appear in a workflow document, and the build enforces that rather than trusting it - the conformance run greps every document under test for the engine markers it knows about and fails on a hit, per agentic-stack's own rule that products belong in the adapter column only. | sourced | `F-part-c-09` "Products belong in the adapter column only." |
| Proposed: cross-cutting guarantees attach to the operator, not to the caller's document, and the document declares them as constant values so a reader can see them and a caller cannot set them. The consequence at build time is that the correlation attribute, the budget decrement, the actor chain and the step idempotency key are written by the engine on every operator record, and a step record missing any of the four fails the run rather than being back-filled. | sourced | `F-b4-01`, `F-b4-06` "Correlation rides on explicit attributes, not trace parentage" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's engine as an interpreter over the document: read the operator schema, derive the dispatch table from the operator names it admits, and walk the tree node by node. Do not write a second list of operator names beside the walk - if the code needs an if-else per operator, key it off the derived set so a name the schema does not admit cannot be reached. | Proposed: the interpreted engine is what runs today, and its one structural defect is that the set of operators it can execute is written in code next to a schema that also writes it. Deriving one from the other is the whole difference between a closed set and a set that is closed twice, differently. | proposed | - |
| 2 | Build the second engine as a compiler: lower the same document once into a static state machine, enqueue its transitions, and let a worker advance the machine by committing one state row per step. The compiled engine must accept the document unchanged, with no pre-pass of its own. | Proposed: this is the pair's proof obligation. An engine that reads the tree before the run cannot rely on anything the interpreter settled by looking at the tree mid-walk, so any field the compiler has to guess at is a field the schema was missing. | proposed | - |
| 3 | Record differs_in_execution_model with at least the three axes this pair actually turns on - processes required for progress, where durability lives, and whether a call returns a result or a ticket - using the shape and the axis names build-adapter-pair defines, and never a product name as a value. | A pair whose difference is not written down as an axis and two values is a pair nobody can check; build-adapter-pair rejects a pair whose axes agree, because a second implementation of the same shape proves nothing. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 4 | Migrate in four stages, each independently revertible: (1) derive the interpreter's dispatch from the schema and assert set equality at start-up; (2) put the conformance report in front of the interpreted engine alone, so its baseline is recorded before a second engine exists; (3) add the compiled engine and select it by configuration only; (4) add a declared cost contribution per operator so the reconciliation leg can move from claimed to measured. | Proposed: stage 1 removes the drift that exists today, stage 2 fixes what 'unchanged' means before anything can be compared against it, stage 3 is the swap, and stage 4 is the only stage that needs a schema change - keeping them apart means a failure names its stage. | proposed | - |
| 5 | Wire the cross-cutting concerns at the operator boundary in both engines: stamp the correlation attribute on every step record explicitly rather than relying on parentage, decrement the budget from the entry ceiling before each step and refuse the step that would cross it, carry the actor's delegation chain onto every record, and give each step its own idempotency key rather than reusing the run's. | xc-correlation owns the dispatch-attribute rule, xc-budget the decrement-and-refuse ceiling, xc-identity-delegation the actor chain and xc-idempotency-lease the per-step key; this step only says where the four attach at the operator boundary. agentic-stack carries the correlation finding as measured in PASS.md A7 (F-a7-02), and the consequence here is that a run key alone deduplicates a whole submission while a restart mid-composition needs the step to be the unit (F-b4-08). | sourced | `F-a7-02`, `F-b4-08` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Apply build-definition-of-done: run the criterion below, then run its deliberate breakage, and record both outputs as an evidence record carrying the tree hash under test and whether the tree was dirty. Label the result measured only where the exact strings were produced by a run in this repository. | agentic-stack and build-definition-of-done both state it (F-part-c-04): a green run that never had a red is not evidence that anything is checked, and a measurement taken from a dirty tree cannot be reproduced by the person who reads it. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Keep one composition that exercises every operator exactly once and run it on both engines on every change, rather than a large suite that exercises four operators heavily and two never - compose-operators already owns the finding this guards against: a deterministic gate can be structurally green and mean nothing. | sourced | `F-a7-03` "Only diff, syntax and format ran." |
| Treat the durable-execution engine that PASS.md A6 records as present but not listening as a reason to keep the composition expressible over a queue and a state machine, not as a reason to wait for it. The composition is defined over the step interface, so a down orchestrator delays the adapter, never the vocabulary. | sourced | `F-a6-02` "Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down" |
| Proposed: report the engine marker in the same line as the result, always. A report that names the adapter it asked for rather than the one that answered is the shape of the configuration finding PASS.md A7 already recorded. | proposed | `F-a7-04` "Configuration written in the documented place was silently discarded." |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-interpreted-workflow-document` | today | the walk itself: examples/end-to-end/run.py reads examples/end-to-end/workflows/triage-and-fix.json, dispatches each agent operator through one dispatch interface, evaluates each judge operator against a criterion held outside the document, and parks at the approval operator. compose-operators carries the same pair at contract level; what this row adds is where the code is and what has to change in it. Proposed entity id: no capability row in PASS.md B3 covers composition operators, so there is no E- record to reuse. | Cannot today prove its own operator set: the set it can execute is an if-else chain in run.py and the set it admits is the anyOf in schemas/workflow.schema.json, and nothing asserts the two are equal - which is precisely the binding stage 1 of the migration installs and the breakage below attacks. | Select the engine by configuration only, hand the compiled engine the same document and the same schema, and compare the operator-binding-report from both runs. Measured on 2026-09-03: `bash examples/end-to-end/test.sh` reports `passed 29, failed 0` for this engine alone. | measured | `T-t10-07` "inside the end-to-end example or beside it" |
| `E-swap-candidate-a-queue-plus-a-state-machine` | second | a build in which the document is lowered once, before the run, into a static state machine: each operator becomes one or more transitions, each transition is a message, and progress is one committed state row per step. compose-operators names this pair at contract level and reuses this entity from the durable-execution row of PASS.md B3 rather than minting one; the build detail here is that no worker ever holds the tree. | Cannot resolve anything at run time that the compiler could not resolve at compile time, so a document that relies on being re-read mid-walk simply fails to compile; and cannot report a failure as a position in the tree, only as a state and a transition, which is why the report compares step order rather than stack traces. | Compile the same document against the same schema, run the same conformance report with this engine selected, and assert engines_run >= 2 with an empty drift array and identical step order and terminal outcome. A difference is a defect in the schema's completeness, not in either engine. | claimed | `F-b3-04` "Restate · DBOS · Inngest · a queue plus a state machine" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/compose-operators/test.sh && python3 harness/compose-operators/conformance.py --engine dryrun --engine second |
| Expected | Measured by tools/measure.py at c754723: exit 0; last lines: engine_marker=compiled-state-machine/0.1 schema_ops=6 executor_ops=6 drift=0 operators_exercised=6 terminal_outcome=completed checks=39/39 \| engines_run=2 step_order=identical terminal_outcome=identical distinct_markers=2 differ=nothing |
| Deliberate breakage | In harness/compose-operators/adapters/dryrun.py, make the interpreted engine register a branch operator arm the schema does not admit regardless of the gate's own flag (the operator set is then written in two places), run the criterion (drift lists branch, executor_ops is 7 on that engine while the compiled engine stays clean, and the gate exits 1), then git checkout harness/compose-operators/adapters/dryrun.py. |
| Expected failure | Measured by tools/measure.py at c754723: exit 1; last lines:   FAIL the same suite exits 0 again (expected 0, got 1) \| passed 29, failed 5 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-04` "Swappability is a tested property, not an intention." |

## Composes with

Builds on: `compose-operators`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Where does the compiled engine's state machine live, given that the durable-execution adapter PASS.md B3 names for this row is recorded as present but not listening? | A reachable durable executor, or a decision to build the queue-plus-state-machine leg against the state seam directly. Applying TARGET T5's 1-3-1, the candidates were: wait for the orchestrator, build the compiled engine on the state seam's append-only log, or run it on an in-process queue with a committed row per transition. The second was taken, because it needs nothing that is currently down and it is the leg that makes the pair's axes differ. | The compiled engine commits one state row per transition through the state seam and reads its work from a queue, with no dependency on an external orchestrator. | `F-a6-02`, `T-t5-02` "Data directory present; server not listening" |
| Does a declared cost contribution per operator belong in the operator schema, or beside it in a capability definition the operator's verb resolves to? | A three-level composition priced both ways, with the parent estimate reconciled against the sum of children in each. Until stage 4 of the migration runs, the reconciliation leg of the criterion above cannot be measured at all. | Proposed: beside it, in the capability definition the agent operator's profile already resolves to, so the operator schema stays the control-flow vocabulary and does not acquire a cost field per operator. | `REF-5-2-12` "Every kind must declare its cost contribution in its own envelope" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-compose-operators |
