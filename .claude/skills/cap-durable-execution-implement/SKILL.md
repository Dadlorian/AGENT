---
name: "cap-durable-execution-implement"
description: "How to build the Durable execution capability on this stack: a thin adapter over the external workflow orchestrator that is installed but not listening, a second adapter that has no server at all, how to bring workflows that checkpoint nothing today in front of one interface, where budget, policy, identity, telemetry, provenance and idempotency attach to a step and to a restart, and a definition of done with the crash that makes it fail. Load it when writing or reviewing the code that starts, checkpoints, resumes or reads a multi-step run, when wiring an executor behind the step interface, when deciding what the second executor should be, when a resumed run has to continue under the budget it had left, or when a restart quietly re-does a side effect."
---

# cap-durable-execution-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-durable-execution into something that runs here: two executors behind one step interface, workflows that checkpoint nothing today brought in front of it one at a time, and every ceiling attached around the step and around the restart rather than inside the executor. | sourced | `F-a6-02`, `F-b3-04`, `E-capability-durable-execution` "Data directory present; server not listening" |

## Entities

| Entity |
|---|
| `E-capability-durable-execution` |
| `E-not-running-temporal` |

## Contract

### Shapes (JSON Schema 2020-12)

**DurableExecutionAdapterBinding (what selects an executor, and the only place an executor is named)** (sourced; sources: `T-t7-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:adapter-binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "processes_required_for_progress",
    "effect_commit_mode"
  ],
  "description": "Proposed. Read by the executor factory only. Nothing in the core, and no caller, reads this object or branches on adapter.",
  "properties": {
    "adapter": {
      "type": "string",
      "description": "Adapter entity id. Selecting an executor is configuration; there is no code path that chooses one."
    },
    "processes_required_for_progress": {
      "type": "integer",
      "minimum": 1,
      "description": "Separate processes that must be running for a run to advance. The measurement open question 2 turns on this number."
    },
    "effect_commit_mode": {
      "enum": [
        "same_transaction",
        "keyed_effect"
      ],
      "description": "Whether this executor can commit a checkpoint in the same transaction as the step's effect, or whether the step's own idempotency key is the deduplicator."
    },
    "replay_determinism_required": {
      "type": "boolean",
      "default": false
    },
    "executor_marker": {
      "type": "string",
      "description": "Emitted by the running executor at begin_run and asserted against, so a swap that never happened is visible."
    }
  }
}
```

**DurableExecutionConformanceReport (the counters the definition of done asserts on)** (sourced; sources: `T-t9-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "per_adapter"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 2,
      "description": "Distinct executors exercised. Fewer than two means the swap was not tested."
    },
    "per_adapter": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "adapter",
          "executor_marker",
          "steps_committed",
          "steps_replayed",
          "effects_for_killed_step",
          "duplicate_effects",
          "declared_gap_honoured"
        ],
        "properties": {
          "adapter": {
            "type": "string"
          },
          "executor_marker": {
            "type": "string",
            "description": "Read from the running executor, not from the binding record."
          },
          "steps_committed": {
            "type": "integer",
            "minimum": 0
          },
          "steps_replayed": {
            "type": "integer",
            "minimum": 1,
            "description": "Greater than zero, or the kill did not happen and the run proved nothing."
          },
          "effects_for_killed_step": {
            "type": "integer",
            "minimum": 1,
            "maximum": 1
          },
          "duplicate_effects": {
            "type": "integer",
            "minimum": 0,
            "maximum": 0
          },
          "budget_remaining_after_resume_micros": {
            "type": "integer",
            "minimum": 0,
            "description": "Recomputed from the committed step records, never reset by the restart."
          },
          "declared_gap_honoured": {
            "type": "boolean",
            "description": "True when the executor behaved as its declared gap says it will, including when the declared behaviour is that it cannot commit the effect in the same transaction."
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| agentic-stack states that what runs is substrate and is not to be replaced (F-part-c-11). The consequence here is narrow and unusual: the installed orchestrator becomes today's adapter even though it is not currently listening, so no instruction in this skill asks anyone to uninstall it, and none assumes it will answer either. | sourced | `F-part-c-11`, `F-a6-02` "Do not propose replacing what runs." |
| agentic-stack states that the cross-cutting guarantees are applied by the platform and cannot be declined (F-b4-01). What this adds, as this skill's own consequence and proposed: they attach around each step and around the restart, so an executor that offers its own retry policy, its own budget or its own audit trail has offered a second, declinable copy that must not be wired. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them" |
| A ceiling belongs to the unit of work, so a resumed run continues under what is left of it rather than under a fresh one: budget remaining is recomputed from the committed step records at resume, and a restart that resets the ceiling has turned a crash into free money. | sourced | `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| build-evidence-record owns the append-only chained record (F-a5-03). What this adds, as this skill's own consequence and proposed: the step log is the same idea applied per run, so checkpoints are appended and chained rather than updated in place, and a resumed run verifies the chain before it trusts a resume point. | sourced | `F-a5-03` "a manual edit between runs is detectable" |
| Proposed: the step key stays a string the caller supplies. The keyed lease that makes a key exclusive is enforcement applied a wave above this interface, so building a lease into the executor here would tie replay safety to one executor and make it unswappable. Research query: is there a recorded decision or open question fixing the boundary between a durable-execution step key and a cap-idempotency claim key, so this row can cite that boundary instead of asserting it here? | proposed | `F-b3-16` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's adapter as a thin translation onto the external workflow orchestrator: map begin_run onto starting or describing a run, checkpoint_step onto its step-completion record, and resume_point onto the first step its history has no completion for. Add nothing to the interface to accommodate it, and let it report unavailable when nothing is listening. | cap-durable-execution states that the interface must not assume a server (F-a6-02). What this adds at the code level, as this skill's own consequence and proposed: the adapter is the only place allowed to know there is a server, so 'the orchestrator is down' becomes a typed failure of one adapter rather than an outage of the capability. | sourced | `F-a6-02`, `F-b3-04` "server not listening on `7233`/`8233`" |
| 2 | Build the second adapter as an in-process transactional step log over a relational database: one row per step, written in the same database transaction as the step's own effect where the effect is a database write, and a resume that is a single query for the first step with no committed row. | Proposed: this is the pair's proof - durability moves from a separate server's history to a row beside the effect, nothing is replayed, and the number of processes required for a run to advance becomes one. The record on file for the database-backed engine is a search result, so the mechanism is cited and the design consequence is ours. Research query: is there a fetched (not search-only) source describing the exact same-transaction step-row mechanism for a relational-database-backed durable executor, which would let this row's mechanism claim itself be cited rather than only the search result that inspired it? | proposed | `X-cap-durable-execution-006`, `F-b1-04` |
| 3 | Record differs_in_execution_model with the three axes named in the invariants, and write each adapter's gaps down as gaps: the orchestrator cannot advance a run while unreachable and needs deterministic step code; the step log cannot commit an effect that lives outside its database in one transaction. | build-adapter-pair already states that a swap needing a core change means the boundary is drawn wrong (F-meta-04). What this adds, as this skill's own consequence and proposed: widening the contract until both executors satisfy every member is the quiet version of that failure, so each gap is declared and the conformance run asserts on it instead. | sourced | `F-meta-04`, `F-b1-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 4 | Migrate one workflow at a time: put the step interface in front of a sequence that today runs start to finish with no checkpoint, keep it running, and count workflows converted. Do not attempt a cutover of all of them, and do not let a converted and an unconverted workflow look alike from the outside. | Proposed. The consumption reference on file deduplicates a whole completed key and appends zero records on replay, which is the degenerate case of this interface; a half-migrated set where some runs resume mid-sequence and some restart from zero is indistinguishable to whoever reads the code next. Research query: is there a recorded migration record (kb/ceremonies or an evidence record) from another capability in this platform that converted callers one at a time behind a shared interface, confirming this is the platform's own established pattern rather than invented here? | proposed | - |
| 5 | Recompute budget remaining, re-evaluate policy and re-assert the actor at every resume, from the committed step records rather than from anything the executor carried across the restart. | Refusal is deterministic and happens before execution rather than after spend, and a restart is an execution: a resumed run that skips the gate has found the opt-out that design rule 7 forbids, and one that trusts an in-memory budget has lost the number the crash destroyed. | sourced | `F-b4-04`, `F-b4-02` "Refusal is deterministic and happens before execution, not after spend" |
| 6 | Carry the correlation identifier explicitly on every step record and re-attach it after the restart; never expect the executor's own run identity, or trace parentage, to reconnect a resumed run to the work that started it. | agentic-stack already states the trace-context finding (F-a7-02). What this adds, as this skill's own consequence and proposed: a crash and restart is a second boundary where context is minted afresh, so a resumed run silently becomes a new root unless the identifier is a field on the record the restart reads. | sourced | `F-a7-02`, `F-b4-06` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Assert which executor actually answered by reading a marker the running executor emits at begin_run, rather than trusting the binding record that selected it. | agentic-stack already states the silent-configuration finding (F-a7-04). What this adds, as this skill's own consequence and proposed: here the same failure mode produces two green conformance runs of the same executor, which reads as a proven swap and is not one. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: implement resume before implementing anything else, including retries and parallel steps. Resume is the property the whole capability exists for and the one the definition of done gates on; retries built first will be written against a run that always starts at zero. Research query: is there a recorded build order or retrospective on this stack showing resume built and proven before retries or parallel steps, rather than this being an un-evidenced preference? | proposed | `F-b4-08` |
| Proposed: make the side-effecting step in the conformance suite genuinely observable - a row appended to a table someone else counts - rather than a counter inside the run. An effect the run itself reports cannot show the run double-counting it. Research query: is there a recorded conformance run whose side-effecting step wrote to a table outside the run's own report, confirming this pattern was actually used rather than only recommended? | proposed | `F-part-c-04` |
| cap-durable-execution already states the green-resume trap (F-a7-03). What it adds for an implementer, as this skill's own consequence and proposed: assert steps_replayed on the report rather than in a log line, because a suite whose kill silently failed will otherwise pass every other assertion it makes. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-temporal` | today | begin_run, checkpoint_step, resume_point and read_run built as a translation layer over the external workflow orchestrator PASS.md B3 names in this row, Temporal: history on a separate server, a crashed run rescheduled by replaying that history, and step completion read from that history. PASS.md A6 records its data directory present with nothing listening on 7233/8233, so this adapter's first honest behaviour is to report itself unavailable. | Proposed: cannot advance a run while the server is unreachable; requires the executed step code to be deterministic so history can be replayed; requires workers registered before any step runs; and cannot commit a checkpoint in the same transaction as an effect written to another store, so its effect_commit_mode is keyed_effect. | Point the binding at the other executor and re-run the 20-step crash suite. No core change is expected. Assert the executor marker read from the running executor, not the adapter name written in the binding. | claimed | `F-b3-04`, `F-a6-02`, `X-cap-durable-execution-002` "the Temporal Server detects the Worker's failure and reschedules the Workflow" |
| `E-swap-candidate-dbos` | second | the same four operations served by an in-process transactional step log: one row per step in a relational database, committed in the same transaction as the step's own effect where that effect is a database write, resume as a query for the first step with no committed row, and nothing replayed. A research record on file describes DBOS reusing Postgres as the durability layer for workflows while Temporal runs a dedicated cluster. | Proposed: cannot join a checkpoint to an effect that lives outside its database in one transaction - that case falls back to the step's own idempotency key with effect_commit_mode keyed_effect - and offers no cross-process history, no replay, and no view of a run from a machine that cannot reach the database. | Proposed: the axes that differ are locus_of_durability_and_verification, processes_required_for_progress (a server plus a registered worker versus one) and replay_determinism_required (true versus false). Select by configuration with no code edit between runs, then compare both reports against the same declared gaps. | claimed | `X-cap-durable-execution-006`, `F-b3-04`, `F-b1-04` "reuses Postgres as the durability layer for workflows, while Temporal runs a dedicated cluster" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/workflow/test.sh && python3 harness/workflow/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 16d354c: exit 0; last lines: adapter=second executor_marker=queue-state-machine/0.1 steps_committed=8 steps_replayed=6 effects_for_publish=1 duplicate_effects=0 declared_gap_honoured=true checks=28/28 \| adapters_run=2 distinct_markers=2 |
| Deliberate breakage | In harness/workflow/flow.py, make Attempt.key() always return None instead of the step's idempotency key (the harness's own --break-idempotency behaviour, made the default so the criterion needs no extra flag) and change nothing else; restore with git checkout -- harness/workflow/flow.py. |
| Expected failure | Measured by tools/measure.py at 16d354c: exit 1; last lines:   FAIL the same suite passes again once the key is restored (expected 0, got 1) \| passed 13, failed 10 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b4-08` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-durable-execution`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What does a step whose effect lives outside the checkpoint store commit, when the executor cannot join the two in one transaction? | Count, over the workflows actually migrated, how many steps have an effect the checkpoint store cannot transact with. If the number is small, the keyed-effect fallback is enough; if most steps are outside, the fallback is the normal path and deserves its own conformance case rather than a declared gap. | effect_commit_mode keyed_effect: the step's own idempotency key deduplicates, the gap is declared on the binding, and the conformance run asserts the executor behaved as declared. The key alone is what the platform has today, so the fallback is honest about what it rests on. | `F-b3-16` "key on the wire, no lease" |
| Where does the step log live relative to the platform's own persistence, and who is its single writer? | Measure write contention per run at the concurrency the platform actually reaches, and audit whether any consumer of the step log depends on strict order across runs rather than within one. | One writer per run, and the step log kept behind the same interface as any other durable store rather than bound to the platform's state seam; cap-durable-execution records that this capability needs a place to checkpoint and not a specific one. | `F-b5-05` "the write model, concurrency and single-writer guarantees" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-durable-execution 2831cb4f, 2026-09-03 |
