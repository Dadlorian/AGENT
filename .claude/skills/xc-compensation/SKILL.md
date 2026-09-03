---
name: xc-compensation
description: The unwind guarantee as a placement: before a unit of work commits a side effect, the platform has already recorded how reversible that effect is and, where the class allows one, the compensating action that undoes it, so a failed or cancelled run walks the record backwards instead of leaving half a transaction behind. Load it when a step is about to call something that cannot be taken back, when deciding what happens to the four effects already committed when the fifth fails, when a run is cancelled mid-flight, when someone asks how a workflow is rolled back, reversed, refunded or cleaned up, when a saga or an undo path is being designed, when an approval gate needs a field to fire on, or when a review asks which effects in a plan can never be reversed and what the platform does about them.
---

# xc-compensation

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix compensation as a placement rather than as error-handling: an effect's irreversibility class and its compensating action are recorded before the effect is committed, the platform applies this at the dispatch and step boundaries whichever way in the work arrived, and a failed or cancelled run is unwound from that record instead of from whatever the failing step happened to remember. | sourced | `F-b4-01`, `T-t2-03`, `E-concern-idempotency` "These are the difference between a working system and a production one" |

## Entities

| Entity |
|---|
| `E-concern-idempotency` |
| `E-capability-idempotency` |
| `E-capability-durable-execution` |
| `E-core-component-ledger` |
| `E-core-component-graph` |
| `E-seam-dispatch` |
| `E-standard-idempotency-key-convention` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-idempotency-key-convention` | unverified | unverified | - | `F-b3-16`, `X-end-to-end-044` |

- `E-standard-idempotency-key-convention` version note: cap-idempotency owns this standard row and records the draft it names; nothing was fetched from this environment. It is listed here because the key that makes a replay safe is the same key a compensating action is claimed under, not because it governs compensation: saga-style compensation has no published specification, which is why every shape below is proposed.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| declare_effect (proposed operation set; no published specification governs compensation, so the calls below are ours) | the step about to commit an effect, its irreversibility class, the compensating action that undoes it when the class admits one, and the digest of the effect's request (proposed) | a compensation record durable at a head strictly before the effect is committed, or a refusal when the class is absent or when the class is irreversible and no mandate covers the step (proposed) | proposed | `X-end-to-end-041`, `X-xc-compensation-002` "you must map a backward-facing compensating node" |
| seal_effect (proposed) | a declared compensation record and the response the effect actually returned (proposed) | the record moved to committed and sealed against that response, which is what a later replay returns instead of re-committing the effect; xc-idempotency-lease states the crash window this closes (X-end-to-end-042) (proposed) | proposed | `X-end-to-end-042`, `F-b4-08` "if a tool call succeeds but the agent crashes before saving state, a resumed workflow may retry the call" |
| unwind (proposed) | a run handle and the point to unwind from, with the reason: failed, cancelled, or refused after the fact (proposed) | the committed records walked in reverse, each compensating action executed under its own key, and a per-record outcome of compensated, not-required or unwind-failed (proposed) | proposed | `X-end-to-end-041`, `X-xc-compensation-002` "the orchestrator executes the compensation chain in reverse order" |
| unwind_plan (proposed accessor) | a run handle, or a plan that has not executed yet (proposed) | the ordered list of what would be unwound and, separately, the effects classed irreversible that no unwind can reach; this is the read an approval gate and a planner need before the first effect rather than after the last (proposed) | proposed | `X-end-to-end-043`, `X-end-to-end-063` "some side effects reverse cleanly, some can only be compensated" |

### Shapes (JSON Schema 2020-12)

**CompensationRecord (proposed summary shape; the full schema, the class table and the unwind report are in references/usage.md)** (proposed; sources: `X-end-to-end-043`, `X-end-to-end-041`, `F-b4-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:record:0.1",
  "title": "CompensationRecord",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. One record per side effect, written through the state seam before the effect is committed. There is no field here a caller may leave out: irreversibility has no default, and a compensating action is required by the class that admits one.",
  "required": [
    "run_id",
    "step_id",
    "effect_digest",
    "irreversibility",
    "idempotency_key",
    "declared_at_head",
    "state"
  ],
  "properties": {
    "run_id": {
      "type": "string"
    },
    "step_id": {
      "type": "string"
    },
    "effect_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "irreversibility": {
      "enum": [
        "reversible",
        "compensable",
        "irreversible"
      ],
      "description": "Declared per effect. There is no default: an absent class is a refused declaration, not a reversible effect."
    },
    "compensating_action": {
      "type": "object",
      "description": "Required when irreversibility is compensable: the logical inverse, declared as a step in its own right so it is planned, priced and graded like any other.",
      "required": [
        "operator",
        "input_ref",
        "idempotency_key"
      ],
      "properties": {
        "operator": {
          "type": "string"
        },
        "input_ref": {
          "type": "string"
        },
        "idempotency_key": {
          "type": "string",
          "minLength": 1,
          "maxLength": 255
        },
        "timeout_s": {
          "type": "integer",
          "minimum": 1
        }
      },
      "additionalProperties": false
    },
    "mandate_ref": {
      "type": [
        "string",
        "null"
      ],
      "description": "Required when irreversibility is irreversible: the authority under which an unreachable effect was allowed to happen at all. cap-mandate-broker owns what it contains."
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255
    },
    "declared_at_head": {
      "type": "string",
      "description": "The head the declaration became durable at. Strictly earlier than the head the effect's own record carries."
    },
    "committed_at_head": {
      "type": [
        "string",
        "null"
      ]
    },
    "sealed_response_ref": {
      "type": [
        "string",
        "null"
      ],
      "description": "Set when the effect returned; a replay under the same key returns this rather than re-committing."
    },
    "state": {
      "enum": [
        "declared",
        "committed",
        "compensated",
        "not-required",
        "unwind-failed"
      ]
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "irreversibility": {
            "const": "compensable"
          }
        },
        "required": [
          "irreversibility"
        ]
      },
      "then": {
        "required": [
          "compensating_action"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "irreversibility": {
            "const": "irreversible"
          }
        },
        "required": [
          "irreversibility"
        ]
      },
      "then": {
        "required": [
          "mandate_ref"
        ]
      }
    }
  ]
}
```

**reaching the guarantee from each of TARGET T6.2's four entries (proposed worked instances; minimal inputs and outputs, on the shared entry envelope in examples/end-to-end)** (proposed; sources: `T-t6-02`, `REF-3-4-10`, `REF-3-4-15`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:ways-in:0.1",
  "title": "CompensationWaysIn",
  "description": "Proposed. Nobody calls this guarantee. The minimal input is the step declaration a caller was already writing; the minimal output is what the platform recorded before the effect and what it did with it afterwards. cap-consumption fixes the caller doctrine these four entries share; this shows only what compensation adds to it.",
  "type": "array",
  "examples": [
    [
      {
        "way_in": "a human enters the system",
        "in": {
          "actor": {
            "subject": "user:corey"
          },
          "step": "refund-the-coupon-charge",
          "irreversibility": "compensable",
          "compensating_action": {
            "operator": "payments.void",
            "input_ref": "step.out.charge_id"
          }
        },
        "out": {
          "declared_at_head": "sha256:4c1a90",
          "committed_at_head": "sha256:4c1a91",
          "state": "committed"
        }
      },
      {
        "way_in": "an external system or agent enters the system (T6.2's External door; can start a run or steer one)",
        "in": {
          "actor": {
            "subject": "agent:partner-sre-bot"
          },
          "step": "post-the-status-update",
          "irreversibility": "irreversible",
          "mandate_ref": "mandate:status-page:2026-09-03"
        },
        "out": {
          "state": "committed",
          "compensating_action": null,
          "note": "No unwind exists for this class, so the gate ran before the effect rather than a compensation after it."
        }
      },
      {
        "way_in": "an event enters the system (T6.2's Internal door; steers a run that already exists and never starts one - REF-3-4-10, REF-3-4-15)",
        "in": {
          "actor": {
            "subject": "service:alerting"
          },
          "step": "open-the-incident-ticket",
          "irreversibility": "compensable",
          "compensating_action": {
            "operator": "tickets.close",
            "input_ref": "step.out.ticket_id"
          }
        },
        "out": {
          "state": "compensated",
          "unwind_reason": "failed",
          "compensated_at_head": "sha256:4c1aa7"
        }
      },
      {
        "way_in": "a schedule fires (T6.2's Time door; starts a new root run under its own standing allocation and never steers - REF-3-4-10)",
        "in": {
          "actor": {
            "subject": "schedule:nightly-fault-sweep"
          },
          "step": "write-the-sweep-report",
          "irreversibility": "reversible"
        },
        "out": {
          "state": "not-required",
          "unwind_reason": "cancelled",
          "note": "A reversible effect is re-derived by the next run; the record exists so the unwind can say so rather than guess."
        }
      }
    ]
  ]
}
```

**the refusals this guarantee returns (proposed worked instances; cap-errors owns the object and the closed registry)** (proposed; sources: `F-b4-07`, `X-end-to-end-043`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:refusal-instances:0.1",
  "title": "CompensationRefusals",
  "description": "Proposed. Shown rather than described. An effect-committing step with no declared irreversibility class is refused before the run starts, and an irreversible step with no mandate is refused deterministically before spend, both with registered types. The third case has no registered row: urn:agentic:problem:compensation-unresolved is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns, and until that row lands an implementation returns the registered adapter-unavailable, which is also 503 and retryable, naming the records it could not unwind in detail, as the open question below records.",
  "type": "array",
  "examples": [
    [
      {
        "type": "urn:agentic:problem:document-invalid",
        "title": "Document invalid",
        "status": 422,
        "detail": "step 3 'payments.charge' commits an effect and declares no irreversibility class; there is no default",
        "retryable": false,
        "correlation": {
          "run_id": "run-human-0001",
          "correlation_id": "corr-human-0001",
          "depth": 0
        }
      },
      {
        "type": "urn:agentic:problem:policy-denied",
        "title": "Policy denied",
        "status": 403,
        "rule_id": "compensation.irreversible-requires-mandate",
        "detail": "step 5 'email.send' is declared irreversible and carries no mandate_ref; nothing can unwind it",
        "retryable": false,
        "correlation": {
          "run_id": "run-event-0001",
          "correlation_id": "corr-event-0001",
          "depth": 0
        }
      },
      {
        "type": "urn:agentic:problem:adapter-unavailable",
        "title": "Compensation unresolved",
        "status": 503,
        "detail": "unwind of run-external-0001 left 1 of 4 records unwind-failed: tickets.close timed out; proposed type urn:agentic:problem:compensation-unresolved",
        "retryable": true,
        "correlation": {
          "run_id": "run-external-0001",
          "correlation_id": "corr-external-0001",
          "depth": 0
        }
      }
    ]
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the declaration precedes the effect. A compensation record is durable at a strictly earlier head than the effect it covers, so a crash between the two leaves a declared record with no effect, which is recoverable, rather than an effect with no record, which is not. | proposed | `X-end-to-end-041`, `X-end-to-end-042` "For every forward-facing action node in your graph, you must map a backward-facing compensating node" |
| Proposed: irreversibility is a declared class per effect with three members and no default - reversible, compensable, irreversible - and an effect-committing step that declares none is refused rather than assumed reversible. The cheap assumption is the dangerous one, because the class that cannot be unwound looks exactly like the class that needs no unwinding until the run fails. | proposed | `X-end-to-end-043` "some side effects reverse cleanly, some can only be compensated, and some like a sent email or captured payment cannot be taken back by any mechanism that exists" |
| Proposed: a compensating action is a new forward operation that is the logical inverse of the effect, declared as a step in its own right, not a rollback of stored state. There is nothing to roll back once an effect has left the platform, and a store that only appends has no earlier version to restore. | proposed | `X-xc-compensation-002`, `X-xc-compensation-003` "A compensating transaction is a new operation that is the logical inverse of the one it undoes." |
| Unwinding is not the first answer to a repeat. cap-idempotency and xc-idempotency-lease state the replay contract (F-b4-08); the consequence here is an order of preference: where the effect is held under a live key the platform replays the sealed response, and it compensates only where the run is being abandoned rather than resumed. Compensating what could have been replayed spends twice and changes the world twice. | sourced | `F-b4-08`, `F-b3-16`, `E-concern-idempotency` "Every externally-triggered action is safe to replay" |
| Proposed: every compensating action is itself a side effect, so it takes its own idempotency key, its own lease and its own record, and an unwind interrupted halfway resumes where it stopped instead of compensating an already-compensated effect. xc-idempotency-lease owns the lease placement this reuses. | proposed | `X-xc-compensation-006`, `F-b4-08` "every participant must handle duplicates gracefully" |
| Proposed: the irreversible class does not produce a compensation, it produces a gate. An effect nothing can reverse is admitted only under a mandate recorded before it runs - cap-mandate-broker owns what a mandate contains and cap-human-interaction the approval an operator gives - so the class declared here is the field those gates fire on rather than a second policy of their own. | proposed | `X-end-to-end-063`, `X-end-to-end-043` "approval gates on irreversible actions are the typical defenses" |
| The record is append-only and is never edited: a compensation appends a further record referencing the one it undoes, and a class is corrected by declaring a new step, not by rewriting the old declaration. cap-idempotency states that the core already owns an append-only deduplication authority (F-b2-06), and an unwind that could rewrite its own history could also hide an effect it failed to reverse. | sourced | `F-b2-06`, `E-core-component-ledger` "append-only across runs; the deduplication authority" |
| Proposed: one unwinder per run drives the reverse walk, and the effects being unwound do not listen for each other. A walk that each participant triggers independently has no single place that knows how far it got, which is exactly the state a crash mid-unwind leaves behind. | proposed | `X-xc-compensation-005`, `X-xc-compensation-001` "In orchestration, a single orchestrator manages the transaction flow, invoking services and handling compensations when needed." |
| agentic-stack states design rule 7 as a test (F-b1-08): telemetry, policy, provenance and budget are applied by the platform, not requested by the caller. xc-enforcement-chain names the dispatch point and its own slots as the one place every unit crosses before a call proceeds; this guarantee's declare_effect binds at that same dispatch point and again at the step boundary beneath it - not as a seventh slot of the chain, but as a check riding alongside `budget.reserve` and `idempotency.claim` at the same crossing - so there is no argument, flag or handler a caller supplies to obtain unwinding and none to opt out of declaring a class. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| Proposed consequence of TARGET T2.3, which xc-idempotency-lease states for the lease: the record and the unwind cover the whole structure, so an effect committed by a resumed step, by a sub-unit two levels down or by a delivered approval declares its class at that boundary. A guarantee held only at the outermost run unwinds only what the outermost run did itself. | proposed | `T-t2-03`, `X-end-to-end-041` "State, telemetry, and every cross-cutting concern are managed across the entire structure" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: there is no field, header, role or configuration value that skips the declaration, supplies a default class, or marks a run exempt from unwinding. xc-idempotency-lease states the same for the lease (F-b4-01, F-b1-08); the only honest way to say a guarantee is applied rather than requested is to leave nothing for a caller to set. | proposed | `F-b1-08`, `F-b4-01` "The platform applies each; a caller cannot decline them" |
| Proposed: the authority a compensating action runs under. A record names a mandate reference, never a credential, so unwinding never becomes a path by which a unit obtains a permission it was refused on the forward pass; cap-mandate-broker owns minting and verification. | proposed | `X-end-to-end-063` |
| agentic-stack states design rule 6 (F-b1-07). What it forbids here specifically: the criterion a result will be judged against never travels on a compensation record, on an unwind plan or in the detail string of an unwind failure - the last being the easy leak, because a failure is written to explain why the work did not meet what was asked of it. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Declare the irreversibility class on every step that commits a side effect, in the document that declares the work, and refuse the document when an effect-committing step carries none. | core-document owns the artifact that carries declared intent, a definition of done and steps (F-b2-02), and a class declared there is available to the Planner before anything runs. Declaring it at the call site instead would put the answer to 'can this be taken back' inside the step that is about to take it. | sourced | `F-b2-02`, `X-end-to-end-043` "declared intent, definition of done, steps" |
| 2 | Write the compensation record through the state seam before the effect is committed and seal it with the response afterwards, so the record's declaration head is strictly earlier than the effect's. | A record written after the effect is a record that a crash between the two removes, and that gap is precisely the window in which a resumed workflow re-commits an effect it cannot see. Two heads, in order, are what makes the ordering checkable rather than intended. | sourced | `X-end-to-end-042`, `F-b4-08` "which without an idempotency key can mean duplicate payments, duplicate tickets, or duplicate deploys" |
| 3 | Pair every compensable effect with a compensating action declared as a step of its own - operator, input reference, key and timeout - rather than as a callback attached to the forward step. | A compensating action that is a step is planned, priced, graded and retried like any other work, and it can be reviewed before the run starts. One that is a callback is invisible to the Planner and is tested only on the day it is needed, which is the day it must not fail. | sourced | `X-xc-compensation-002`, `X-end-to-end-041` "Every step that can fail must have a well-tested compensating transaction." |
| 4 | Route an effect declared irreversible to a mandate and, where a person owns the decision, to an approval gate, before it is committed - never to a compensating action. | Some effects cannot be taken back by any mechanism that exists, so the only control left is the one applied in front of them, which is xc-enforcement-chain's call point rather than a route this guarantee invents. Making the class the field that gate reads keeps one classification for both purposes rather than a policy list that drifts from the record. | sourced | `X-end-to-end-043`, `X-end-to-end-063` "Hard caps on autonomous loops, plan-validation checkpoints, and approval gates on irreversible actions are the typical defenses." |
| 5 | On failure or cancellation, unwind from the last committed record backwards under one unwinder per run, and record a per-record outcome of compensated, not-required or unwind-failed. | Reverse order is what makes each compensation see the world its own effect left behind rather than a world three later effects have changed. Recording an outcome per record is what lets a second attempt resume rather than start again, and what makes a partial unwind visible instead of silently absorbed. | sourced | `X-end-to-end-041`, `X-xc-compensation-005` "if a downstream node raises an unrecoverable exception, the orchestrator executes the compensation chain in reverse order" |
| 6 | Give every compensating action its own idempotency key and its own lease, derived the same way the forward effect's was, and its own timeout. | xc-idempotency-lease owns the placement; the consequence here is that an unwind interrupted halfway is a duplicate delivery like any other, and a compensation with no timeout turns one unreachable destination into a run that never finishes failing. | sourced | `X-xc-compensation-006`, `F-b4-08` "Every step in a saga should have a timeout" |
| 7 | Prefer replay to compensation whenever the effect is still held under a live key and the run is resuming rather than being abandoned, and record which of the two happened. | cap-idempotency states the replay contract (F-b4-08); compensating an effect that could have been replayed spends the budget twice and changes the world twice, and a record that does not say which path ran leaves nobody able to tell the two apart afterwards. | sourced | `F-b4-08`, `F-b3-16` "key on the wire, no lease" |
| 8 | Return every refusal as the platform's typed problem object: an undeclared class as the registered document-invalid, an irreversible step with no mandate as the registered policy-denied carrying a rule id, and an unwind that could not complete as the fallback named in the refusal shape above. | cap-errors holds the type registry closed, and core-document and seam-dispatch already state the typed-failure rule (F-b4-07); this guarantee supplies no new failure format. A caller repairing a declaration branches on a type; a caller told an unwind failed needs a type it can escalate on rather than a sentence to read. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 9 | Prove the guarantee cannot be declined by replaying one corpus through each of TARGET T6.2's four entries - human, event, schedule and external - killing a run mid-effect in each, and asserting that every committed effect has an earlier compensation record and that every abandoned run either replayed or compensated every record it committed. A schedule-entered run starts root work of its own and must be killed mid-effect on its own right, not folded into the event case that only steers. | xc-enforcement-chain already proves its own chain over these same four entries; this guarantee is proved the same way over the same doors rather than over T1's narrower three, because a guarantee wired on the path someone remembered is declinable by choosing another door, and entry is where doors multiply. Counting the compensations that actually executed on all four is what turns cannot be declined into a number rather than a number for three of them. | sourced | `T-t6-02` "Four entries cover nearly every situation: a human, an event, a schedule (time), and an external system or agent." |
| 10 | Open references/usage.md when you need the full compensation record schema, the class table with its worked examples, the unwind report shape or the four entry envelopes in full. Proposed: the body of this skill is enough to wire the guarantee and to judge an implementation of it. | Proposed, progressive disclosure. The class table and the unwind report are long material, and a reader deciding whether an effect can be unwound does not need them open. TARGET T3 warns that something daunting will not be used. | proposed | `T-t3-02` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: classify by what the destination does, not by what the code returns. A call that returns a success object having already sent a message is irreversible whatever its signature says, and the class is the only place that distinction is written down. | proposed | `X-end-to-end-043` "There is no universal undo" |
| Exercise the compensating action on the schedule you exercise the forward one, because it is the branch that only runs on the worst day. A well-tested compensating transaction is the stated requirement; an untested one is a declaration that reads correctly and fails at the moment nothing else is working either. | sourced | `X-xc-compensation-002` "Every step that can fail must have a well-tested compensating transaction." |
| Compensate forward, in the store's own vocabulary. Where state is kept as an append-only sequence there is no earlier row to put back, so the compensation is another entry that moves the entity onward, and treating it as a delete is how a compensation becomes a second bug. | sourced | `X-xc-compensation-003` "Instead, it adds new entries that transition the state of entities to the new values." |
| agentic-stack already states the structurally-green-gate finding (F-a7-03). What it adds here: a corpus in which no run ever failed exercises no unwind at all and still exits green, so assert the number of compensations that actually executed and the number of runs actually killed mid-effect, never the exit code alone. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack already states the silently-discarded-configuration finding (F-a7-04). What it adds here: a compensating action named in a declaration is not a compensating action that runs, so prove the guarantee by observing an effect being reversed, not by reading the record that promised it. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Proposed: count the irreversible steps in a plan before it runs and treat a rising count as a design finding rather than an approval queue. Trading strict transactional guarantees for availability is the deliberate bargain of this pattern, and a plan whose effects are mostly unreachable has taken the cost without the benefit. | proposed | `X-xc-compensation-001` "trading strict ACID guarantees for better availability and scalability" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first implementation of this placement (docs/decomposition.md section 3.4 has no compensation row; the open question below records the row this would add): `python3 tools/conformance/compensation.py --entries examples/end-to-end/entries --corpus out/effects.jsonl --kill-mid-effect 0.25 --report out/compensation.json`. Over a corpus replayed through each of TARGET T6.2's four entries - human, event, schedule, external - it asserts that every committed effect has a compensation record durable at a strictly earlier head, that every effect-committing step submitted without an irreversibility class was refused with the registered `document-invalid` rather than admitted, that every step classed irreversible carries a mandate reference, and that every run killed mid-effect either replayed the sealed response or ran the declared compensating action for each record it had committed. It reports `effects_checked`, `undeclared_class_admitted`, `records_after_effect`, `irreversible_without_mandate`, `runs_killed`, `replayed`, `compensated`, `unwind_failed` and `ways_in_covered`, and asserts `effects_checked > 0`, `undeclared_class_admitted == 0`, `records_after_effect == 0`, `irreversible_without_mandate == 0`, `runs_killed > 0`, `replayed + compensated == effects committed by killed runs`, `unwind_failed == 0` and `ways_in_covered == 4`. |
| Expected | exit 0 and one summary line `effects_checked=<n> undeclared_class_admitted=0 records_after_effect=0 irreversible_without_mandate=0 runs_killed=<k> replayed=<r> compensated=<c> unwind_failed=0 ways_in_covered=4`, with `k` greater than zero and `r + c` equal to the number of effects the killed runs had committed, so the unwind assertion had something to assert on. |
| Deliberate breakage | Let an absent irreversibility class default to reversible instead of refusing the document: leave the class optional in the declaration and treat a missing value as reversible everywhere else, and re-run the same command. |
| Expected failure | exit non-zero with `undeclared_class_admitted` equal to the number of effect-committing steps that declared no class, and `replayed + compensated` short of the effects the killed runs committed by exactly those steps, because an effect silently classed reversible has no compensating action to run and no mandate gate in front of it, while `effects_checked` holds its value and `ways_in_covered` stays 3 - which is what shows the failure is the default rather than a corpus that was never replayed. Claimed: nothing declares an irreversibility class today and this tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `X-end-to-end-043` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-research-record`, `build-ceremony`, `core-document`, `cap-durable-execution`, `cap-idempotency`, `xc-idempotency-lease`, `seam-dispatch`, `xc-enforcement-chain`

Used by: `xc-compensation-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| docs/decomposition.md section 3.4 lists seven cross-cutting rows, X1 to X7, and none of them is compensation, so this guarantee's definition of done has no row to be made precise from. Which row should be added? | 1-3-1 applied (TARGET T5), the way xc-idempotency-lease records its own gaps: (a) fold compensation into X7, the idempotency-lease row, which would make one criterion assert two different placements and let a green run hide which of them was exercised; (b) add an X8 row stating the criterion and the breakage this skill's definition of done names, which is the option recommended and followed here; (c) leave it unrowed until a ceremony decides, which leaves the guarantee with no entry in the document every other cross-cutting concern is checked from. The question closes when X8 exists in section 3.4. | Proposed: the criterion and breakage stated in this skill's definition of done stand as the X8 row, and an implementation cites this skill until that row is written. | `T-t5-02`, `F-b4-01` "When a problem comes up, use 1-3-1" |
| An unwind that leaves records in unwind-failed has no registered problem type. Should `compensation-unresolved` be added to the closed registry? | core-document and seam-dispatch already state the typed-failure rule (F-b4-07), and cap-errors requires 1-3-1 rather than minting a suffix at the call site, so the three options were: reuse `adapter-unavailable`, which is 503 and retryable and describes the destination that would not answer but not the run left half-unwound; reuse `policy-denied`, which misnames a failure nobody refused; or add one row, `compensation-unresolved` (503, retryable, extension member `causes`, one per record left unwound) to docs/decomposition.md section 2.1.6 and use it. The third is recommended, and the refusal shape above returns the first as the fallback meanwhile. | `urn:agentic:problem:compensation-unresolved`, marked proposed and pending registration; until the row lands an implementation returns the registered `adapter-unavailable` with the unwound-failed records in `causes` rather than inventing a type at the call site. | `F-b4-07`, `T-t5-02` "Typed and machine-readable. Never parsed from prose" |
| This ideal facet carries no adapters[] of its own: where the compensation register lives and the axis the two candidates differ on are recorded in xc-compensation-implement. Is that the right split for an xc- skill? | 1-3-1 applied (TARGET T5) exactly as xc-idempotency-lease records the same split for the lease: (a) carry the pair here too, which duplicates rows the implement facet owns and gives a reader two places to change; (b) keep the placement here and the register there, and say so, which is what this row does; (c) leave the pair unstated, which would leave the guarantee with no named way to run. Recommendation followed: (b). The question closes if a ceremony extends the adapter-pair check from cap- ideal skills to xc- ones. | Proposed: the pair lives in xc-compensation-implement, whose definition of done runs over both registers and asserts adapters_run at least 2. | `T-t5-02`, `F-b1-04` "Every interface ships with at least two adapters" |
| Does an effect classed reversible need a compensation record at all, or only a class on its step? | Count, over a corpus of killed runs, how many reversible effects an unwind had to reason about and how many of those a later run would have re-derived anyway. A count near zero argues the record is bookkeeping; a non-trivial count argues that an unwind which cannot see a reversible effect cannot tell a not-required outcome from a missed one. | Proposed: record every effect, including reversible ones, and let the unwind mark them not-required. One record shape for all three classes keeps the ordering assertion - a record before every effect - a single check rather than a check with an exemption in it. | `X-end-to-end-041` "For every forward-facing action node in your graph" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-compensation 2831cb4f, 2026-09-03 |
