---
name: seam-dispatch
description: The Dispatch seam as it should be: one unit of agent work executes under a declared ceiling and returns one typed result whose partial progress is already durable, with the request shape, the result shape, cancellation, ceiling enforcement, partial results, the context a unit receives and folds back, and what a failure returns. It also carries the caller's view - how a person, an agent and an event reach it, the smallest call, and the refusal. Load it when deciding how a unit of agent work is started, bounded, cancelled or resumed; when asking 'what happens to the work already done if this run is killed', 'why did this unit stop', 'what does a retry of this re-do', or 'can we run this somewhere else without changing the caller'; when a request may arrive twice and must execute once; when the context handed down to a sub-unit or the summary handed back is about to be left implicit; and whenever a dispatcher is about to invent its own state names, its own stop reasons or its own error body.
---

# seam-dispatch

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for executing a single unit of agent work and returning one result, so agent execution is pluggable: the request, the result, cancellation, the ceilings, the partial and the failure are the seam's, and what runs the unit is an adapter. | sourced | `F-b5-02`, `F-b5-03`, `E-seam-dispatch` "This is the seam that decides whether agent execution is pluggable at all." |

## Entities

| Entity |
|---|
| `E-seam-dispatch` |
| `E-seam-b5` |
| `E-standard-a2a-messaging` |
| `E-standard-agent-client-protocol` |
| `E-standard-rfc-9457-problem-details` |
| `E-standard-idempotency-key-convention` |
| `E-adapter-firecracker-microvm` |
| `E-swap-candidate-hosted-sandbox-services` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-a2a-messaging` | unverified | unverified | - | `F-b3-08`, `X-seam-dispatch-001`, `X-seam-dispatch-003` |
| `E-standard-agent-client-protocol` | unverified | unverified | - | `F-b3-05`, `X-seam-dispatch-002` |
| `E-standard-rfc-9457-problem-details` | RFC 9457 | unverified | - | `F-b3-13` |
| `E-standard-idempotency-key-convention` | unverified | unverified | - | `F-b3-16` |

- `E-standard-a2a-messaging` version note: The task lifecycle used for the result's state member is adopted from this standard. Two search-only records describe the states and the rule that the stream closes at a terminal state; the specification itself was not fetched from this environment, so no version string is asserted. This skill owns the row for the lifecycle; cap-work-intake owns the row for the messaging envelope.
- `E-standard-agent-client-protocol` version note: The stop-reason vocabulary for why a unit ended is adopted from this standard. cap-agent-runtime owns this standards row and already records the protocol version as unverified with every record on file search-only; this skill reuses that reading rather than asserting a version of its own.
- `E-standard-rfc-9457-problem-details` version note: The failure body of every dispatch operation. cap-errors owns this standards row, keeps the closed problem-type registry and records the specification as not fetched from this environment; this skill names the registry rather than restating it.
- `E-standard-idempotency-key-convention` version note: The key member of the request follows this convention. cap-idempotency owns this standards row; the design note for this seam records the draft as expired without becoming an RFC (claimed), so the convention is adopted and the lease semantics are specified by the platform. The draft was not fetched from this environment.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| dispatch (proposed) | one dispatch request: a document saying what to do, an opaque criterion handle, an actor with its delegation chain, a spend ceiling, a deadline, an isolation profile, an idempotency key, an explicit correlation record, and a declaration of the context this unit receives | one dispatch result: a lifecycle state, a stop reason, timestamps, the partial flag, outputs each carrying a digest and the head at which it became durable, usage, the folded summary handed back to the parent, and a problem object when the state is failed or rejected (proposed) | proposed | `F-b5-03`, `X-seam-dispatch-001` |
| cancel (proposed) | a dispatch id and the grace window declared on its request | acceptance, not a stop: the caller keeps taking frames until the terminal one, whose stop reason is cancelled inside the window and cancel_timeout outside it; cancelling an already-terminal dispatch returns the current result and is not an error (proposed) | proposed | `F-a3-09` |
| resume (proposed) | a new dispatch id carrying previous_dispatch_id, the same idempotency key lineage, and the checkpoint reference the partial recorded | a fresh result that continues from the first incomplete step under whatever ceiling remained; the prior result is never mutated and never promoted (proposed) | proposed | `X-cross-structure-045` |
| replay (proposed) | a dispatch request whose idempotency key has already been claimed | the recorded result of the first execution, byte for byte, with no side effect re-executed; a different request body under the same key is refused as urn:agentic:problem:idempotency-conflict (proposed) | proposed | `X-cross-structure-042`, `X-seam-dispatch-007` |
| read_step (proposed) | a dispatch id, or a run id and a step id | the recorded step: its state, its stop reason, its checkpoint reference, its usage, and any compaction transitions recorded against it, so a reader can tell what a restart will and will not re-do (proposed) | proposed | `X-cross-structure-043` |

### Shapes (JSON Schema 2020-12)

**dispatch-request (proposed summary shape; the full request, result and problem schemas are in references/dispatch-shapes.md)** (proposed; sources: `F-b5-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:request:0.1#summary",
  "title": "DispatchRequest (summary)",
  "type": "object",
  "description": "Proposed. The ceilings and the actor are declared here; what to do is declared in the Document; how it will be judged is not here at all. The full shape, including the actor chain, the isolation profile and the capability list, is in references/dispatch-shapes.md.",
  "required": [
    "dispatch_id",
    "idempotency_key",
    "document",
    "criterion_ref",
    "actor",
    "budget",
    "deadline",
    "isolation",
    "correlation"
  ],
  "properties": {
    "dispatch_id": {
      "type": "string",
      "format": "uuid"
    },
    "previous_dispatch_id": {
      "type": "string",
      "format": "uuid",
      "description": "Set when this dispatch resumes after a partial. Never mutates the previous result."
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255
    },
    "document": {
      "$ref": "urn:agentic:core:document:0.1"
    },
    "criterion_ref": {
      "type": "string",
      "minLength": 1,
      "description": "Opaque handle resolved out of band. The criterion itself must never appear in this object."
    },
    "actor": {
      "type": "object",
      "required": [
        "subject",
        "delegation_chain"
      ]
    },
    "budget": {
      "type": "object",
      "required": [
        "ceiling_micros",
        "currency",
        "on_exceed"
      ],
      "properties": {
        "on_exceed": {
          "const": "terminate_unit"
        }
      }
    },
    "deadline": {
      "type": "object",
      "required": [
        "not_after",
        "max_duration_s"
      ],
      "properties": {
        "cancel_grace_s": {
          "type": "integer",
          "minimum": 1,
          "default": 10
        }
      }
    },
    "isolation": {
      "type": "object",
      "required": [
        "profile",
        "egress"
      ]
    },
    "correlation": {
      "type": "object",
      "required": [
        "run_id",
        "root_dispatch_id"
      ],
      "description": "Explicit members, emitted as resource attributes at dispatch. Never inferred from trace parentage."
    },
    "context": {
      "$ref": "urn:agentic:dispatch:context:0.1"
    }
  }
}
```

**dispatch-result (proposed summary shape)** (proposed; sources: `F-b5-03`, `X-seam-dispatch-001`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:result:0.1#summary",
  "title": "DispatchResult (summary)",
  "type": "object",
  "description": "Proposed. state is the adopted task lifecycle; stop_reason is the adopted stop-reason vocabulary plus exactly five platform endings. The full shape and its conditional rules are in references/dispatch-shapes.md.",
  "required": [
    "dispatch_id",
    "state",
    "stop_reason",
    "started_at",
    "ended_at",
    "partial",
    "outputs",
    "usage",
    "correlation"
  ],
  "properties": {
    "dispatch_id": {
      "type": "string",
      "format": "uuid"
    },
    "state": {
      "enum": [
        "submitted",
        "working",
        "input-required",
        "auth-required",
        "completed",
        "canceled",
        "rejected",
        "failed"
      ]
    },
    "stop_reason": {
      "enum": [
        "end_turn",
        "max_tokens",
        "max_turn_requests",
        "refusal",
        "cancelled",
        "budget_exhausted",
        "deadline_exceeded",
        "policy_denied",
        "cancel_timeout",
        "adapter_unavailable"
      ],
      "description": "The first five are adopted; the last five are the endings the platform itself can cause."
    },
    "partial": {
      "type": "boolean",
      "description": "True whenever state is not completed and outputs is non-empty."
    },
    "outputs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "digest",
          "media_type",
          "recorded_at_head"
        ],
        "properties": {
          "digest": {
            "type": "string",
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "recorded_at_head": {
            "type": "string",
            "description": "State-seam head digest at which this output became durable."
          }
        }
      }
    },
    "usage": {
      "type": "object",
      "required": [
        "cost_micros",
        "currency",
        "wall_ms"
      ]
    },
    "folded": {
      "$ref": "urn:agentic:dispatch:context:0.1#/$defs/folded"
    },
    "correlation": {
      "$ref": "urn:agentic:dispatch:request:0.1#/properties/correlation"
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1",
      "description": "Required when state is failed or rejected."
    }
  }
}
```

**dispatch-step-record (proposed): the durability contract in one object** (proposed; sources: `X-cross-structure-043`, `X-seam-dispatch-007`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:step:0.1",
  "title": "DispatchStepRecord",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. Every dispatch is a recorded step, so a reader can tell what a restart resumes and what a repeat returns without knowing which executor ran it. A durable engine fills this from its own journal; a queue plus a state machine fills it from the state seam.",
  "required": [
    "run_id",
    "step_id",
    "dispatch_id",
    "idempotency_key",
    "replay_semantic",
    "state"
  ],
  "properties": {
    "run_id": {
      "type": "string",
      "minLength": 1
    },
    "step_id": {
      "type": "string",
      "minLength": 1,
      "description": "Stable across restarts of the same logical step, so the resume point names a step and not an attempt."
    },
    "attempt": {
      "type": "integer",
      "minimum": 1,
      "default": 1
    },
    "dispatch_id": {
      "type": "string",
      "format": "uuid"
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1,
      "description": "Derived from the run id and the step id, so a repeat of the same logical step carries the same key and a new step never does."
    },
    "checkpoint_ref": {
      "type": [
        "string",
        "null"
      ],
      "description": "State-seam head digest, or null before the first output is durable. A restart resumes at the first step whose checkpoint_ref is null."
    },
    "replay_semantic": {
      "const": "return_recorded_result",
      "description": "A const, not an enum: a repeat under a claimed key returns the recorded result and re-executes no effect. There is no request that opts out."
    },
    "state": {
      "enum": [
        "submitted",
        "working",
        "input-required",
        "auth-required",
        "completed",
        "canceled",
        "rejected",
        "failed"
      ]
    },
    "compactions": {
      "type": "array",
      "items": {
        "$ref": "urn:agentic:dispatch:context:0.1#/$defs/compaction"
      }
    }
  }
}
```

**dispatch-context (proposed): what the unit receives, what it folds back, and every compaction in between** (proposed; sources: `X-end-to-end-004`, `X-end-to-end-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:context:0.1",
  "title": "DispatchContext",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. The request declares what context the unit receives; the result declares the summary folded back to the parent; a compaction is a recorded transition rather than an invisible one, so a reader can tell that context was dropped and by which strategy.",
  "required": [
    "inherits",
    "budget_tokens"
  ],
  "properties": {
    "inherits": {
      "enum": [
        "none",
        "folded_summary",
        "full_parent"
      ],
      "default": "none",
      "description": "none is the default: a sub-unit starts fresh unless the parent says otherwise."
    },
    "budget_tokens": {
      "type": "integer",
      "minimum": 0,
      "description": "The context ceiling for this unit, independent of the spend ceiling."
    },
    "carried_digests": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^sha256:[0-9a-f]{64}$"
      },
      "description": "Handed down by reference, never by value, so what a unit read is auditable."
    }
  },
  "$defs": {
    "folded": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "summary_digest",
        "media_type"
      ],
      "description": "What the parent receives back. Appending only this is what keeps a parent's context bounded when a sub-unit ran long.",
      "properties": {
        "summary_digest": {
          "type": "string",
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        "media_type": {
          "type": "string"
        },
        "dropped_token_estimate": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "compaction": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "at",
        "strategy",
        "before_tokens",
        "after_tokens"
      ],
      "properties": {
        "at": {
          "type": "string",
          "format": "date-time"
        },
        "strategy": {
          "enum": [
            "summarise_and_restart",
            "branch_and_fold"
          ],
          "description": "The two strategies the adapter pair must be able to declare. Which one is the platform default is an open question of this skill."
        },
        "before_tokens": {
          "type": "integer",
          "minimum": 0
        },
        "after_tokens": {
          "type": "integer",
          "minimum": 0
        },
        "summary_digest": {
          "type": "string",
          "pattern": "^sha256:[0-9a-f]{64}$"
        }
      }
    }
  }
}
```

**What a refusal looks like (proposed worked instance): a registered problem object, never prose** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:example:budget-exhausted",
  "title": "The ceiling would have been crossed, so the unit terminated",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Branch on type; use retryable and retry_after_s as given; read detail only to report it. The type is a member of the closed registry cap-errors owns.",
  "examples": [
    {
      "type": "urn:agentic:problem:budget-exhausted",
      "title": "A metered call would cross the declared ceiling",
      "status": 402,
      "detail": "ceiling 1500000 micros, reserved 1500000, recorded spend 1487300, next call estimated 41000",
      "dispatch_id": "0f1e2d3c-4b5a-4697-8899-aabbccddeeff",
      "stop_reason": "budget_exhausted",
      "retryable": false,
      "correlation": {
        "run_id": "run-event-0001",
        "root_dispatch_id": "0f1e2d3c-4b5a-4697-8899-aabbccddeeff",
        "depth": 0
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| One unit of agent work executes and returns one result. Everything the seam specifies hangs off that sentence: one request in, one result out, and no second call a caller must make before there is an answer. | sourced | `F-b5-02`, `E-seam-dispatch` "**Dispatch** — one unit of agent work executes and returns one result." |
| This is one of the two boundaries agentic-stack names as having no standard to adopt (F-b5-01), so the design effort spent here is warranted; what that buys is an obligation, because the seam must specify all six of the request shape, the result shape, cancellation semantics, timeout and budget enforcement, partial-result handling and what a failure returns. A dispatcher that specifies five of the six is not this seam. | sourced | `F-b5-03`, `F-b5-01` "It must specify: the request shape, the result shape, cancellation semantics, timeout and budget enforcement, partial-result handling, and what a failure returns." |
| Proposed: an output is durable before the dispatch is terminal, or it does not exist. Every output is written through the state seam and carries the head digest at which it became durable before the result is assembled, so a result never names an output a later reader cannot find, and partial is true whenever the state is not completed and outputs is non-empty. | proposed | `X-cross-structure-045` |
| Proposed: every dispatch is a recorded step carrying a run id, a stable step id, an idempotency key derived from the two, and a checkpoint reference that is null until the first output is durable. A restart resumes at the first step whose checkpoint reference is null, and a repeat under a claimed key returns the recorded result rather than re-executing the effect. Both are satisfiable by a durable engine and by a queue plus a state machine, which is why the obligation is written as a record and not as an engine. | proposed | `X-cross-structure-042`, `X-cross-structure-043`, `F-b3-04` |
| Two ceilings, spend and wall clock, are independent, both enforced outside the unit, and both terminate the unit rather than the platform - xc-budget owns that rule (F-b4-02). What this seam adds: the on_exceed member is a const rather than an enum, so there is no request that opts out, and a unit that enforced its own ceiling could decline to. | sourced | `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| Cancellation is a request that a unit reach a terminal state, not a kill: it is asynchronous and idempotent, late frames are legal until the terminal frame, the grace window is per request, and expiry of the window is a failure carrying cancel_timeout rather than a clean cancellation. cap-agent-runtime owns the reference point on the substrate (F-a3-09), recorded claimed; the seam's addition is that a cancelled dispatch with durable outputs is a partial and not a loss. | sourced | `F-a3-09` "`session/cancel` mid-tool-call ends the turn in ~8s against a 45s operation, zero trailing frames" |
| Proposed: context is declared, not assumed. The request says what context the unit receives and under what token ceiling, the result says what summary is folded back to the parent, and every compaction is a recorded transition naming its strategy, its timestamp and the tokens before and after. A context that shrinks invisibly makes a result irreproducible and gives a reader no way to tell a short answer from a truncated one. | proposed | `X-end-to-end-004`, `X-end-to-end-005` |
| A failure returns a typed, machine-readable problem object whose type is a member of the closed registry cap-errors owns (F-b4-07), never prose and never an adapter's native error. A failure an adapter cannot type is itself a conformance failure of that adapter: it is reported against the registered adapter-unavailable type with the untyped payload in the detail member, and it is counted, and a non-zero count means the adapter is not conformant. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a unit of work through the same request. How the work arrived is a member of the entry envelope cap-work-intake owns and never a member of the dispatch, so one dispatcher covers all three and no adapter branches on the producer. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| Enhancing one aspect of a dispatch leaves the rest untouched, and the cross-cutting guarantees ride on it whichever entry point was used: swapping what executes the unit, adding a stop reason, tightening a ceiling or changing where the unit runs changes nothing in a caller that reads state, stop_reason, outputs, usage and problem. cap-errors and cap-isolation state the same composability record for their own boundaries; here it is the test that decides whether the seam is drawn correctly. | sourced | `T-t2-02`, `T-t2-03` "enhancing particular aspects of any element without touching the rest" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion the result will be judged against, and any verdict. The request carries only an opaque criterion handle the Judge resolves out of band, because agentic-stack and core-judge state design rule 6 (F-b1-07) and a criterion that arrives in the request is a target rather than a grade. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| Which product executed the unit, in what kind of sandbox, at what version, on what host. agentic-stack states that products belong in the adapter column only (F-part-c-09); here that means the result carries no executor identity a caller could branch on, and the adapters section below is the only place in this skill where one is named. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| Proposed: the unit's raw transcript, its tool-call loop and the prompts it built. The result exposes digests, usage, the recorded steps and the folded summary; a caller that reads a transcript has bound itself to one executor's internals and will break on the second adapter. | proposed | - |
| Real credentials. cap-isolation owns the substrate row that no real secret enters the unit (F-a3-05); the dispatch consequence is that the request carries an isolation profile and a broker-only credential mode, never a key, so a recorded request is safe to keep for as long as the ledger keeps it. | sourced | `F-a3-05` "No real secret inside the VM" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Adopt a published task lifecycle for the result's state member and a published stop-reason vocabulary for why the unit ended. Extend the stop reasons by exactly the five endings the platform itself can cause and neither vocabulary has cause to carry: budget exhaustion, deadline expiry, policy denial, cancel-grace expiry and adapter unavailability. Do not invent a state name. | Original design effort is warranted at this boundary because no standard governs the seam as a whole, not because no prior art exists for its parts; a state machine invented here would spend that budget where a lifecycle is already published, and the stop reason is the one field every consumer branches on, so an open set makes the branch unwriteable. | sourced | `X-seam-dispatch-001`, `F-b5-01` "each long-running interaction is a Task with an explicit state machine (SUBMITTED → WORKING → COMPLETED/FAILED/CANCELED/REJECTED/INPUT_REQUIRED/AUTH_REQUIRED)" |
| 2 | Put every ceiling in the request and keep the criterion out of it: carry an opaque criterion handle and nothing that resolves it. Enforce both ceilings outside the unit, and declare the on-exceed behaviour as a constant rather than a choice. | agentic-stack and core-judge state design rule 6 (F-b1-07): a criterion in the request is a target the unit can optimise against. A unit that enforced its own ceiling could decline to, and a caller that could choose what happens on breach could choose to keep going. | sourced | `F-b1-07`, `F-b4-02` "6. **The grader is never visible to the graded.**" |
| 3 | Write durability into the contract rather than leaving it to whichever executor is installed: every output goes through the state seam and carries the head digest at which it became durable before the result is assembled, the partial flag is derived from the state and the outputs rather than set by the executor, and a partial is resumed with a new dispatch id naming the previous one instead of being promoted in place. | Proposed. A result that claims an output a later reader cannot find is a lie no caller can detect; and mutating a prior result would make the append-only ledger's history disagree with the answer, which core-ledger's write model does not allow even as a mistake. | proposed | `X-cross-structure-045`, `F-b2-06` |
| 4 | Make every dispatch a recorded step: a run id, a stable step id, an idempotency key derived from the two, a checkpoint reference that is null until the first output is durable, and a replay semantic fixed to returning the recorded result. Assert the same record can be produced by a durable engine and by a queue plus a state machine before you accept it. | A key on the wire only tells a receiver that a request is a repeat; what makes the repeat safe is the record that says which execution owns the key and what it returned. Writing the obligation as a record rather than as an engine is what keeps the seam satisfiable by both execution models, which is the swap this interface has to survive. | sourced | `X-seam-dispatch-007`, `X-cross-structure-042`, `F-b3-04` "An idempotency key is a unique identifier the caller attaches so the receiver can recognise a repeat." |
| 5 | Declare the context contract in the same two shapes: the request says what context the unit inherits and under what token ceiling, the result says what summary is folded back, and every compaction is appended as a transition naming its strategy, its timestamp and the tokens before and after. Default inheritance to none. | Folding a branch back by appending only the result is what keeps a parent bounded when a sub-unit ran long; an unrecorded compaction makes the difference between a short answer and a truncated one invisible to the reader and to the Judge. | sourced | `X-end-to-end-005`, `X-end-to-end-004` "branch a separate working context to solve an independent sub-task and fold the intermediate steps in the branch before resuming back to the main thread by appending only the result" |
| 6 | Bound cancellation: accept it asynchronously and idempotently, keep taking frames until the terminal one, take the grace window from the request, and when the window elapses destroy the unit and report a failure carrying cancel_timeout - never a clean cancellation. Keep the durable outputs and mark the result partial. | Proposed: cap-agent-runtime owns the observed cancel behaviour on the substrate (F-a3-09), which is where the ten-second default comes from. Reporting a hard kill as a clean cancel would hide an adapter that cannot cancel, which is exactly the adapter the conformance suite exists to find. | proposed | `F-a3-09` |
| 7 | Carry correlation as explicit members of the request and of every result, span, log record and problem object it produces, and stamp them at dispatch rather than inheriting them. | agentic-stack and xc-correlation already state the trace-context finding (F-a7-02). What this seam adds: dispatch is the boundary the finding was measured at, so the correlation members belong in the request shape here and a sub-dispatch re-stamps them rather than relying on parentage. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 8 | Return every failure as a problem object whose type is a row of the closed registry cap-errors owns, set retryable as a field rather than leaving it inferred from the status, and count per adapter the failures that could not be typed. | Proposed: cap-errors and xc-typed-errors own the failure shape; what this adds is the counter. A registry is only closed if something checks it, so an adapter's untyped-failure count is the number that decides conformance rather than the intention to be typed. | proposed | `F-b4-07`, `F-b5-03` |
| 9 | Choose the second adapter on execution model, not on brand: something with no host-side session to hold open, no callbacks and nothing to cancel mid-call, so any requirement that was really a property of today's executor fails immediately. Run one conformance suite over both, and require it to name which adapter failed. | build-adapter-pair states that the second adapter exists to prove the first is not load-bearing (F-b1-04). What this adds here: three implementations exist today with no contract between them, so a suite that reports a single aggregate pass would leave the seam exactly as unpluggable as it is now. | sourced | `F-b1-04`, `F-b5-03` "Today there are three implementations and no contract between them." |
| 10 | Proposed: to call this seam rather than serve it, read cap-consumption first for the doctrine every capability shares, then open references/usage.md for the minimal inputs and outputs and the three worked calls - one per way in - and the worked refusal. Open references/dispatch-shapes.md when implementing or reviewing the full request, result and problem schemas. The body of this skill is enough to judge a candidate dispatcher and to make a first call without either file. | Proposed: the full schemas and the worked calls are past the progressive-disclosure budget for a skill body, and the caller doctrine is stated once in cap-consumption so that naming it costs less than repeating it and cannot drift from it. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the green-gate finding (F-a7-03). What it adds here: a unit that reached a terminal state establishes well-formedness, not correctness, so reaching a terminal state is never on its own a pass. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed - no record in this knowledge base carries the stop-reason vocabulary, so this is our reading, not a sourced fact: state completed with stop_reason end_turn says the unit ended, not that its output is acceptable; ask core-judge and never substitute the stop reason for a verdict. | proposed | - |
| agentic-stack and cap-agent-runtime already state the silent-configuration finding (F-a7-04). What it adds here: read back the grace window, the isolation profile and the ceiling the adapter actually applied from the recorded step, not from the request you sent, because an adapter that silently floors a ten-second grace at sixty looks identical to one that honoured it until the day a cancel matters. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Proposed: derive the idempotency key from the run id and the step id rather than minting one per attempt. A key that changes on retry deduplicates nothing, and a key reused across two logical steps merges two answers into one. | proposed | `X-seam-dispatch-007` |
| Never promote a partial into a complete result. Resume with a new dispatch id naming the previous one, because the ledger is append-only across runs and is the deduplication authority; rewriting a prior result would put the answer and the history in disagreement with no way to tell which is right. | sourced | `F-b2-06` "append-only across runs; the deduplication authority" |
| Proposed: set each adapter's grace default from its own measured cancel floor and store it beside the adapter, rather than shipping one platform-wide constant. Ten seconds is generous for a dispatcher that stops in about eight and impossible for a hosted single-shot executor that cannot stop at all, and one constant would make the honest adapter look broken. | proposed | `F-a3-09` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-firecracker-microvm` | today | dispatch, cancel, resume and read_step served by a control-protocol dispatcher that speaks JSON-RPC over a host-to-guest socket into one hardware-virtualised unit per dispatch. cap-isolation owns this entity's capability row; here it is the executor the seam dispatches into, with the ceilings enforced host-side and the outputs written through the state seam before the result is assembled. | Proposed: cannot serve a dispatch where the platform does not own the hardware, and cannot outlive the host that holds the socket, so its resume path depends on the same machine still being there. Its cancel latency is a property of its own control loop rather than of the seam. | Select the dispatcher by configuration, keep the request and result shapes fixed, and run one conformance suite over both adapters from the same parameterisation. No core change is expected: the core imports the dispatch, not the executor. | claimed | `F-b3-02`, `F-a3-03`, `F-a3-01` "Agent Client Protocol (ACP), JSON-RPC over stdio" |
| `E-swap-candidate-hosted-sandbox-services` | second | the same dispatch and cancel served over HTTP into a hosted single-shot sandbox: it takes the request, runs to a terminal state, and returns one result. There is no session to hold open, no host-side socket, no callback and no in-unit frame stream. cap-isolation lists this class in the same capability row as the adapter above. | Proposed: cannot be cancelled mid-call, so a cancel is at best a request to abandon and its honest terminal is cancel_timeout where the first adapter reports cancelled; cannot stream partial frames, so its partial outputs appear only at the checkpoints it wrote; and it cannot use a host-side broker socket for model egress, so the credential path has to be reachable over the network or the isolation profile is unserveable. | Proposed: the axes that must differ are unit_lifetime (a session held open on our hardware for the duration, versus one request-response on someone else's) and cancellation_reach (cancellable mid-call within the grace window, versus not stoppable once started). Run the same suite over both, selecting by configuration with no code edit between runs, and require per-adapter assertion counts so one failing adapter is named rather than averaged away. | claimed | `F-b3-02`, `F-b1-04` "hosted sandbox services" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first implementation of this seam: `python3 tools/conformance_dispatch.py --adapter today --adapter second --report out/dispatch-conformance.json`. Per adapter it asserts five things: a malformed request is rejected with problem type `urn:agentic:problem:document-invalid`; a cancel issued mid-run reaches a terminal state within `deadline.cancel_grace_s`; a request whose spend ceiling is exceeded terminates with `stop_reason: "budget_exhausted"` and a recorded spend that is non-zero and at most the ceiling; an interrupted run leaves `partial: true` with at least one output carrying a non-null `recorded_at_head`; and every failure body is served as `application/problem+json` with a `type` present in the closed registry in docs/decomposition.md section 2.1.6. Across adapters it asserts `adapters_run >= 2`, and per adapter `assertions_run > 0` and `untyped == 0`. |
| Expected | exit 0 and one line per adapter of the form `adapter=<today\|second> assertions_run=5 failed=0 untyped=0`, followed by `adapters_run=2`. The report names each adapter separately; there is no aggregate pass line. |
| Deliberate breakage | Have one adapter return its native error object instead of problem details - the same body, served as `application/json` with the adapter's own field names - and change nothing else, then re-run. |
| Expected failure | The failure-shape assertion fails for that adapter only: `untyped` becomes non-zero for it, the run exits non-zero, and the report names which adapter broke while the other still reports `failed=0 untyped=0`. That the suite singles out one adapter is the point, because the state this replaces is three implementations with no contract between them. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b5-03` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-adapter-pair`, `build-evidence-record`, `core-document`, `core-judge`, `cap-isolation`, `cap-agent-runtime`, `cap-durable-execution`, `cap-errors`, `xc-budget`, `xc-policy-gate`, `xc-identity-delegation`, `xc-correlation`, `xc-typed-errors`, `xc-provenance-chain`, `xc-idempotency-lease`

Used by: `seam-dispatch-implement`, `xc-compensation`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The knowledge base has no dispatch-specific adapter entity - E-seam-dispatch carries no swappable_to edge and no adapter of its own - so which entities should the adapter pair be recorded against? | 1-3-1 applied. The three options: record the pair against the Isolation capability row's entities, because what dispatches today is defined by the unit it dispatches into and both entities are sourced from that one row; mint dispatch-specific entity ids; or defer the pair to the -implement facet. Minting would put ids in the skill that `python3 tools/kb.py tree` can never resolve, and deferring would leave the ideal facet unable to name either side of the swap it demands. Recommendation taken: reuse the Isolation row's entities and say in each row that cap-isolation owns them. Deciding evidence for revisiting: a knowledge-base entity for a dispatcher, derived from a source rather than minted. | The pair is recorded as the microVM executor and the hosted single-shot sandbox class, both entities of the Isolation capability row, with the seam-level difference stated in each row's cannot and swap_procedure. | `F-b3-02`, `T-t5-02` "use 1-3-1: define the problem" |
| Can the adopted task lifecycle and the adopted stop-reason vocabulary be verified against their published specifications, and at which versions? | A fetch of each specification recording the enumerated states, the enumerated stop reasons and the version string, with the date. Every record on file for both is a search result rather than the specification text, and the design note for this seam records the lifecycle as adopted with the specification not fetched because the domain was egress-blocked. | Both standards rows read version unverified, both enums are carried as proposed in the result shape, and a consumer branching on a value outside the published enum is treated as a conformance failure until the specifications are read. | `X-seam-dispatch-001`, `X-seam-dispatch-003` "the stream must close when the task reaches a terminal state" |
| Which compaction strategy is the platform default when a unit's context ceiling is reached: summarise the run so far and restart the same unit, or branch a fresh sub-unit and fold only its result back? | The two are recorded separately in research and differ in what a reader can reconstruct afterwards: a restart keeps one lineage and loses the intermediate steps, while a branch keeps the sub-unit's steps addressable and appends only its result to the parent. The deciding evidence is a run under both strategies comparing the Judge's verdict and the reconstructable step history at equal token cost. | Neither is the default. The compaction transition records which strategy ran, the adapter declares which it supports, and the conformance suite asserts only that a compaction was recorded - so the choice can be made on evidence later without changing the shapes. | `X-end-to-end-004`, `X-end-to-end-005` "Compaction is the practice of taking a conversation nearing the context window limit, summarizing its contents, and reinitiating a new context window with the summary." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session seam-dispatch 2831cb4f, 2026-09-03 |
