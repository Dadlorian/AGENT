---
name: compose-operators
description: The closed set of composition operators a caller may write - sequence, parallel with fan-out and tolerate, bounded loop, approval gate, agent call, judge - each with its shape as JSON Schema 2020-12, how they nest because a step is itself a document, and the rule that new capability widens what a field may say and never what syntax a caller must learn. Load it before you add a control structure, a branch, a retry, a gate or a seventh operator to a plan; when someone asks 'how do I express this workflow', 'where does the loop bound live', 'why is there no goto', 'can this definition run on a different engine', or 'what stops a nested plan lying about its cost'; and whenever a criterion, a record of earlier attempts, or the thing a result is compared against is about to travel down a tree with the work.
---

# compose-operators

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed: fix one closed set of six deterministic operators - sequence, parallel, loop, approval, agent, judge - as the entire step vocabulary a caller may write, so that composability hides the complexity and every later capability arrives as a wider set of legal values rather than as new syntax to learn. | proposed | `T-t2-01`, `X-entry-composition-030` "Composability hides the complexity." |

## Entities

| Entity |
|---|
| `E-core-component-document` |
| `E-core-component-graph` |
| `E-core-component-planner` |
| `E-core-component-judge` |
| `E-capability-document-validation` |
| `E-capability-durable-execution` |
| `E-standard-json-schema-2020-12` |
| `E-rule-b1-6` |
| `E-rule-b1-7` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | https://json-schema.org/draft/2020-12 | `F-b3-09` |

- `E-standard-json-schema-2020-12` version note: The dialect the operator shapes below are written in, named by the document-validation row of PASS.md B3 and owned by cap-document-validation, which records it unverified because the specification was not fetched. It governs the shape of the document, not the operator vocabulary: no published standard governs the set of operators itself, and the nearest declarative prior art is recorded as an open question rather than adopted.

### Shapes (JSON Schema 2020-12)

**step (proposed summary shape; the six operator schemas in full, the fan-out tolerance member and the worked nesting are in references/operator-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:step:0.1",
  "title": "Step",
  "description": "A step is one operator from the closed set. Every operator's child slot takes a step, so the vocabulary nests without a second format. Adding a seventh member here is new syntax, which the closed-schema rule forbids.",
  "anyOf": [
    {
      "$ref": "#/$defs/sequence"
    },
    {
      "$ref": "#/$defs/parallel"
    },
    {
      "$ref": "#/$defs/loop"
    },
    {
      "$ref": "#/$defs/approval"
    },
    {
      "$ref": "#/$defs/agent"
    },
    {
      "$ref": "#/$defs/judge"
    }
  ],
  "$defs": {
    "sequence": {
      "required": [
        "op",
        "id",
        "steps"
      ],
      "properties": {
        "op": {
          "const": "sequence"
        }
      }
    },
    "parallel": {
      "required": [
        "op",
        "id",
        "branches"
      ],
      "properties": {
        "op": {
          "const": "parallel"
        },
        "tolerate": {
          "$ref": "#/$defs/tolerate"
        }
      }
    },
    "loop": {
      "required": [
        "op",
        "id",
        "max_iterations",
        "exit_when",
        "body"
      ],
      "properties": {
        "op": {
          "const": "loop"
        }
      }
    },
    "approval": {
      "required": [
        "op",
        "id",
        "asks",
        "view",
        "decisions",
        "returns"
      ],
      "description": "decisions is this operator's caller-facing narrowing of compose-approval's ApprovalGate.outcomes: same four-member enum, same return_with_notes value. return_to_step_id is required when decisions includes return_with_notes, matching compose-approval's ApprovalGate.return_to_step_id.",
      "properties": {
        "op": {
          "const": "approval"
        },
        "decisions": {
          "type": "array",
          "minItems": 2,
          "items": {
            "enum": [
              "approve",
              "edit",
              "reject",
              "return_with_notes"
            ]
          }
        },
        "return_to_step_id": {
          "type": "string",
          "description": "The step re-entered with the decider's notes when return_with_notes fires; required exactly when decisions includes return_with_notes (compose-approval's GateOutcome.outcome=return_with_notes)."
        }
      }
    },
    "agent": {
      "required": [
        "op",
        "id",
        "agent",
        "input_from",
        "task"
      ],
      "properties": {
        "op": {
          "const": "agent"
        }
      }
    },
    "judge": {
      "required": [
        "op",
        "id",
        "of",
        "criterion_ref"
      ],
      "properties": {
        "op": {
          "const": "judge"
        }
      }
    },
    "tolerate": {
      "type": "object",
      "required": [
        "failed"
      ],
      "properties": {
        "failed": {
          "type": "integer",
          "minimum": 0,
          "default": 0
        }
      }
    }
  }
}
```

**termination (proposed shape for the machine-readable fields the loop and fan-out invariants below name; reason reuses compose-loop's LoopOutcome.terminated_by vocabulary verbatim rather than re-deriving it)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:termination:0.1",
  "title": "Termination",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "step_id",
    "reason",
    "outcome"
  ],
  "properties": {
    "step_id": {
      "type": "string"
    },
    "reason": {
      "enum": [
        "verdict_pass",
        "iteration_ceiling",
        "budget_ceiling",
        "tolerate_exceeded",
        "approval_rejected"
      ],
      "description": "verdict_pass, iteration_ceiling and budget_ceiling are compose-loop's own three LoopOutcome.terminated_by values, named identically here so a nested loop and a bare compose-loop declaration report the same string for the same event. tolerate_exceeded (parallel) and approval_rejected (approval) are this operator set's own reasons; compose-loop never emits either. There is no separate bare 'cap' value: a cap termination is always one of iteration_ceiling or budget_ceiling."
    },
    "outcome": {
      "enum": [
        "success",
        "failure",
        "escalated"
      ],
      "description": "Extends compose-loop's two-way stop/cap split rather than replacing it: verdict_pass is a stop and reports success; iteration_ceiling and budget_ceiling are a cap and report escalated. failure is a third, non-escalating class that applies only to tolerate_exceeded and approval_rejected - reasons a bare compose-loop declaration never produces - so a loop nested inside a composition still only ever reports success or escalated, exactly as compose-loop's own outcome space requires."
    },
    "iterations_run": {
      "type": "integer",
      "minimum": 0
    },
    "units_failed": {
      "type": "integer",
      "minimum": 0
    },
    "unbounded": {
      "const": false
    }
  }
}
```

**resolved-default (proposed shape; the record resolved_default returns for one field of one step)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:resolved-default:0.1",
  "title": "ResolvedDefault",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "step_id",
    "field",
    "value",
    "resolved_from"
  ],
  "properties": {
    "step_id": {
      "type": "string"
    },
    "field": {
      "type": "string"
    },
    "value": {},
    "resolved_from": {
      "enum": [
        "caller",
        "capability",
        "platform"
      ],
      "description": "Exactly one layer, in that precedence order."
    },
    "override": {
      "type": "boolean",
      "default": false,
      "description": "A caller override is legal and is recorded; it is never silent."
    },
    "non_conformant": {
      "type": "boolean",
      "default": false,
      "description": "Set true whenever override is true. REF-3-2-11 states an override is legal, logged, and tagged non-conformant; this field is where that tag is written, so the record captures not only that an override happened but that it is marked as one."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The operators are model-free and deterministic. Which child runs next is decided by the document and by verdicts already recorded, never by a model reading the situation, so the same document over the same results always takes the same path; prior art shows deterministic composition is separable from model choice even when the nodes being composed are agents. | sourced | `X-entry-composition-032`, `X-entry-composition-031` "is deterministic in how it executes its sub-agents" |
| Every loop is bounded, and there is no unbounded loop operator to write. compose-loop states the vocabulary once, as LoopOutcome.terminated_by: a loop ends on verdict_pass, on iteration_ceiling, or on budget_ceiling, whichever comes first, and this operator's termination record reuses those three names rather than re-deriving them. Stop and cap are opposites and are never collapsed into one halt: a stop firing terminates the step as a success; a cap firing terminates it as a failure that escalates to a human. The same bounding discipline governs nesting: depth is bounded and the bound is checked while the composition is resolved, not while it runs, so a nested operator that would pass the limit is refused before any step executes. | sourced | `F-b4-02`, `X-compose-loop-001` "Exceeding it terminates the unit, not the platform" |
| Proposed: the approval operator's decisions enum is the caller-facing narrowing of compose-approval's own four-outcome vocabulary, never an independent one. compose-approval states as an invariant that a gate has exactly four outcomes and only one of them, return_with_notes, puts work back into the graph; this operator's decisions enum names the identical four values, and a decisions array containing return_with_notes requires return_to_step_id, naming the step re-entered with the decider's notes, exactly as compose-approval's ApprovalGate.return_to_step_id does for a full gate record. Fields this operator does not carry - decider, deadline_at, response_schema - resolve from the platform default the approval capability applies rather than from the caller, per the resolved_default precedence invariant above. | proposed | `F-a2-01`, `REF-3-2-11` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The judging criterion, at any depth and in any operator's fields. agentic-stack states design rule 6 (F-b1-07); what it forbids on this vocabulary is specific - the judge operator carries an opaque criterion_ref and never the criterion body, no agent operator's task or input_from may name a step whose result is a criterion, and no child document may inherit one from its parent. | sourced | `F-b1-07` "The grader is never visible to the graded." |
| Products, engines, endpoints, model vendors and store paths, in any field of any operator. agentic-stack states the rule (F-part-c-09); the consequence here is that a workflow document names a class and a capability and is therefore executable by any conformant engine, which is what makes engine independence a test rather than a claim. | sourced | `F-part-c-09` "name capabilities and standards, never products" |
| Arbitrary cycles, goto, dynamic operator construction and the multi-merge and discriminator patterns the workflow-pattern catalogue enumerates. They are omitted deliberately, not overlooked: each one makes the reachable set of a composition undecidable before it runs, and cost known before commitment depends on that set being decidable. | sourced | `F-b1-06`, `X-compose-operators-003` "Cost is knowable before commitment." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the work as steps drawn from the closed set of six operators and nothing else: sequence, parallel, loop, approval, agent, judge. If the shape you want is not one of the six, you are describing a capability rather than a control structure - express it as a legal value of an existing field (another agent profile, another criterion_ref, another view) instead of reaching for a seventh operator. | A caller who can learn six operators in one sitting never has to relearn the interface as the platform grows, which is the whole point of keeping the primitive count low; the moment a new capability needs new syntax, the schema is open and will accrete forever. Proposed: the six-operator set is ours, not PASS.md's. | sourced | `X-entry-composition-030` "few enough primitives to make it quick to learn" |
| 2 | Validate the composed document against the operator schema through cap-document-validation before anything is priced, graphed or dispatched, and treat the rejection as the answer rather than as a warning: an operator outside the closed set must fail here, not at the step that tries to run it. | The closed set is only closed if something mechanical closes it. Checking through the imported validator rather than a hand-rolled field check is what makes the same rejection appear identically for every entry and every engine. Proposed: the validation call site is ours; the interface is cap-document-validation's. | sourced | `F-b3-09` "any 2020-12 validator" |
| 3 | Price the composition with core-planner and reconcile before you accept the number: each operator declares its own cost contribution, and a parent's total must equal the sum of its children's at every level. Print the reconciliation next to the estimate. | A nested composition that reports a parent figure nobody derived cannot be checked against actuals, and cost known before commitment is the rule the whole planning step exists to satisfy. Proposed: the reconciliation print is ours. | sourced | `F-b1-06` "Cost is knowable before commitment." |
| 4 | Give every loop all three of its terminations before you write the body: the exit verdict it is waiting for, the iteration ceiling, and the budget ceiling it inherits per compose-loop's own contract. Record which one fired, and keep a stop that means done distinct from a cap that means escalate. | A loop with two of the three terminations is an unbounded loop wearing a bound, and a single shared halt cannot tell a reader whether the work finished or ran out of road - a mistake the reference records as already made once. Proposed: the three-termination rule is ours. | sourced | `F-b4-02` "Exceeding it terminates the unit, not the platform" |
| 5 | Make each operator a durable step: checkpoint after every step rather than after the whole composition, so a restart resumes at the first incomplete step instead of replaying from the beginning. The interface for that is cap-durable-execution's; do not name an engine in the document (proposed). | Proposed: a composition that checkpoints only at the end is a single step wearing a tree, and it is the difference between a restart that resumes and a restart that repeats every side effect already committed. | proposed | - |
| 6 | Let the platform carry correlation, budget, actor and idempotency through every operator, declare in the document that they are carried rather than chosen, and check afterwards that the criterion, the attempt history and the referent appear nowhere a step could read them. | The cross-cutting guarantees are applied rather than requested, so a caller who could set them has been handed a way to decline them; and the three things that must never travel are exactly the ones whose leak turns every verdict below that point into self-grading. | sourced | `F-b4-01`, `REF-5-5-01` "The platform applies each; a caller cannot decline them." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: name a composition instead of spelling its control flow out inline - a step that references a defined sub-plan carries its loops, gates and views on one line, and complexity that lives in a named file can be improved for every caller at once. | proposed | `REF-10-03`, `REF-3-2-02` "complexity lives in a named file" |
| Count what executed, not what passed. A conformance run over a composition asserts how many distinct operators were exercised and how many steps actually dispatched, because a deterministic gate can be structurally green and mean nothing. | sourced | `F-a7-03` "A deterministic gate can be structurally green and mean nothing." |
| Keep one reference composition that exercises every operator exactly once, and assert that count in the gate. An operator nobody has run is a claim about the vocabulary rather than a member of it, and a deterministic gate can otherwise be structurally green and mean nothing. | sourced | `F-a7-03` "Only diff, syntax and format ran." |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-interpreted-workflow-document` | today | compose, to_graph and step_of served by interpreting the document while the run walks it. examples/end-to-end/schemas/workflow.schema.json declares the six operators as a closed anyOf over step, examples/end-to-end/workflows/triage-and-fix.json uses every one of them exactly once, and examples/end-to-end/run.py walks that tree node by node in one process, dispatching each agent operator through one dispatch interface. Proposed entity id: the knowledge base has no capability row for composition operators, so there is no E- record to reuse and this id is ours. | Cannot know the full reachable set before the walk reaches it, because the tree is read as it is executed; cannot run two branches of a fan-out concurrently, since the fan-out is the contract here and not the threading; and cannot survive the loss of its process, because nothing between steps is committed anywhere an executor could resume from. | Point the second engine at the same document and the same schema, run one conformance report over both, and assert engines_run >= 2 with identical step order and identical terminal outcome. Nothing in the document changes, which is the property under test rather than a convenience. | measured | `X-end-to-end-066` "compatible across different AI frameworks" |
| `E-swap-candidate-a-queue-plus-a-state-machine` | second | the same six operators, compiled ahead of the run instead of interpreted during it: the document is lowered once into a static state machine whose transitions are enqueued, so a step is a message, the next step is chosen by a committed state row rather than by a call stack, and the operator tree exists only at compile time. This is the second execution model the interface has to survive, and it is reused from the durable-execution row of PASS.md B3 rather than minted. | Cannot admit a document whose shape is not fully known before the run, so anything the interpreting engine could settle by looking at the tree mid-walk has to already be a declared field; and cannot report a failure as a position in a tree, because by run time there is no tree, only a state and a queue. | Compile the same workflow document against the same operator schema, run the conformance report with the compiled engine selected, and compare step order, termination reasons and terminal outcome against the interpreted run; a difference is a defect in the schema's completeness, not in either engine. | claimed | `F-b3-04`, `X-end-to-end-067` "a queue plus a state machine" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first implementation of this vocabulary: `python3 tools/conformance_operators.py --workflow examples/end-to-end/workflows/triage-and-fix.json --schema examples/end-to-end/schemas/workflow.schema.json --engine interpreted --engine compiled --report out/operators-conformance.json`. It asserts, in this order: the document validates against the operator schema through the imported validator with 0 errors; the graph built from the document is identical, node for node and edge for edge, to the graph built from the equivalent chained-call form of the same composition; operators_exercised == 6; depth_bound_checked_at == "resolve"; every parent's estimate equals the sum of its children's; every loop termination names one of exit_verdict, iteration_ceiling or budget_ceiling with unbounded == false; and across engines, engines_run >= 2 with identical step order and identical terminal outcome. |
| Expected | exit 0 and one line reading `validated=0-errors graphs_identical=true operators_exercised=6 depth_bound_checked_at=resolve reconcile=ok unbounded=0 engines_run=2`. Two legs are measured today, on 2026-09-03: `bash examples/end-to-end/test.sh` reports `passed 29, failed 0`, of which `ok   agent registry and workflow validate (0)` is the validation leg and four `reached completed` lines are the interpreted engine running every operator once. The graph-equality leg, the reconciliation leg and the second-engine leg are claimed: no chained-call form, no cost declaration per operator and no compiled engine exist in this repository yet. |
| Deliberate breakage | Append a seventh step to the composed document whose operator is outside the closed set - `{"op": "branch", "id": "pick", "cases": []}` added to `root.steps` of workflows/triage-and-fix.json - and change nothing else. |
| Expected failure | The composition is refused before it is priced or dispatched: the imported validator returns 1 error, `$.root: matches none of the allowed step shapes`, the run exits 2 with `application/problem+json` typed `urn:agentic:problem:document-invalid`, and no ledger record is written. Measured on 2026-09-03 in this session: the same validator returned `valid` for the unmodified document and exactly `$.root: matches none of the allowed step shapes` (1 error) for the modified one, so the closed set is closed by something that can fail. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-research-record`, `build-ceremony`, `core-document`, `core-graph`, `core-planner`, `cap-document-validation`, `cap-durable-execution`

Used by: `compose-operators-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| There is no capability row for composition operators in PASS.md B3, so `python3 tools/kb.py tree` returns no adapter or swap-candidate entity for this layer and today's adapter id above is minted. Which id should a composition's execution model be recorded under? | A B3 row for composition, or a decision that composition rides on the durable-execution row it already reuses for its second adapter. Applying TARGET T5's 1-3-1: the three candidates were a new B3 row, reuse of the durable-execution row for both adapters, and a minted id for the interpreted engine beside the reused one; the third was taken because the interpreted engine is not a durable executor and recording it as one would misstate what runs. | Today's adapter carries the proposed entity id above and says so in its own row; the second adapter reuses the real durable-execution swap candidate. Neither id appears under this skill's entities list. | `T-t5-02`, `F-b3-04` "identify the three best possible solutions" |
| The parallel operator in examples/end-to-end/schemas/workflow.schema.json has no tolerate member, while failure tolerance is stated here as a property of the fan-out. Should the example's schema gain the member, or should this skill drop it? | A fan-out in that example that is expected to survive one failing unit; today every branch must succeed, so the question has never been forced. Recorded here as a disagreement with the consumption reference rather than resolved silently. | The member is proposed as an addition to the example's parallel operator, defaulting to `{"failed": 0}`, which is exactly the behaviour the example has today - so adopting it changes no existing run and makes the currently implicit rule writable. | `REF-5-3-07` "On the unit you cannot say "any failure is fatal"." |
| Should the operator vocabulary adopt the declarative, runtime-portable agent specification the research records as prior art, as its interchange form rather than only as an influence? | A fetched copy of that specification and a mapping of all six operators onto it with nothing left over; the research records are search-only, so neither the version nor the operator coverage has been read. | The vocabulary stays ours and is written in JSON Schema 2020-12, with the prior art cited as evidence that a portable declarative definition is achievable rather than as a standard adopted. | `X-entry-composition-052`, `X-end-to-end-066` "a portable, shareable, platform-agnostic configuration language" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-compose-operators |
