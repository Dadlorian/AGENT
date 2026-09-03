---
name: cap-durable-execution
description: The ideal state of the Durable execution capability: a multi-step unit of work survives a crash and resumes at the first incomplete step, expressed as step, idempotency key, checkpoint and resume point and nothing more. Load it when deciding how a long piece of work is broken into steps that survive a restart, when asking 'what happens to this run if the machine dies at step 11', 'how do we not do that side effect twice', or 'can we run this without a workflow server at all', when a design starts to assume replayable deterministic code, worker registration or a task queue, and whenever a checkpointing contract is about to be written in the vocabulary of whichever engine happens to be installed.
---

# cap-durable-execution

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for making a multi-step unit of work survive a crash and continue at the first incomplete step, so what the core imports is step, key, checkpoint and resume point rather than the feature list of whatever engine runs the steps today. | sourced | `F-b3-04`, `F-b3-01`, `E-capability-durable-execution` "The middle column is the contract" |

## Entities

| Entity |
|---|
| `E-capability-durable-execution` |
| `E-seam-b5` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| begin_run (proposed operation set; PASS.md gives this capability a row and no calls) | the caller's run key, the identity of the step sequence to execute, and the digest of its input | a run handle plus a resume point: the first step index for a new run, and the first incomplete step for a key that has run before, so starting and resuming are the same call (proposed) | proposed | `F-b4-08` |
| checkpoint_step (proposed) | a run handle, the step's own idempotency key, the digest of what the step produced, and the record of the effect it committed | a committed checkpoint, or nothing: the checkpoint and the step's effect become durable together, so a step is complete only when both are (proposed) | proposed | `F-b4-08` |
| resume_point (proposed) | a run handle | the first incomplete step and the number of steps already committed, which is what a restart reads to know where to continue and what a check reads to know a crash really happened (proposed) | proposed | `X-cap-durable-execution-001` |
| read_run (proposed) | a run handle or a run key | the run's terminal state and its committed step records; a failure arrives as the typed problem object rather than as an engine-specific status string (proposed) | proposed | `F-b4-07` |

### Shapes (JSON Schema 2020-12)

**step-record (proposed summary shape; the full schemas are in references/durable-execution-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:step-record:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "run_key",
    "step_id",
    "step_idempotency_key",
    "state",
    "committed_with_effect"
  ],
  "description": "Proposed. One row per step. It is the whole vocabulary of the capability: which step, under which key, complete or not, and committed together with its effect or not at all.",
  "properties": {
    "run_key": {
      "type": "string",
      "minLength": 1
    },
    "step_id": {
      "type": "string",
      "minLength": 1
    },
    "step_idempotency_key": {
      "type": "string",
      "minLength": 1,
      "description": "Per step, not per run. Derived from the run key and the step id so it is identical on every restart."
    },
    "state": {
      "enum": [
        "pending",
        "complete",
        "failed"
      ]
    },
    "committed_with_effect": {
      "type": "boolean",
      "description": "True only when the checkpoint became durable in the same commit as the step's own effect."
    },
    "output_digest": {
      "type": "string"
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1"
    }
  }
}
```

**run-state (proposed summary shape)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:run-state:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "run_key",
    "resume_point",
    "steps_committed",
    "steps_replayed",
    "terminal"
  ],
  "description": "Proposed. What a restart reads. resume_point is the index of the first incomplete step; steps_replayed is how many committed steps were skipped rather than re-executed.",
  "properties": {
    "run_key": {
      "type": "string",
      "minLength": 1
    },
    "resume_point": {
      "type": "integer",
      "minimum": 0
    },
    "steps_committed": {
      "type": "integer",
      "minimum": 0
    },
    "steps_replayed": {
      "type": "integer",
      "minimum": 0
    },
    "terminal": {
      "type": "boolean"
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1"
    }
  }
}
```

**What a failure looks like (proposed): problem details, not prose [caller's view, folded from cap-durable-execution-use]** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:example:unresumable",
  "title": "The run exists and cannot be continued",
  "$ref": "urn:agentic:problem:0.1",
  "description": "A run that cannot be resumed is a failure with a type. It is never quietly restarted from the first step. Branch on type; read detail only to report it. `urn:agentic:problem:durable-run-unresumable` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `idempotency-conflict`, which is also 409 and not retryable, with the run key and the last committed step in detail.",
  "examples": [
    {
      "type": "urn:agentic:problem:durable-run-unresumable",
      "title": "Run cannot be resumed",
      "status": 409,
      "detail": "step records for run_key human-checkout-500s-2026-09-03 end at step 11 with no committed effect record; continuing would repeat a side effect",
      "retryable": false,
      "correlation_id": "corr-human-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| This capability's row names no standard and points at the section that covers boundaries with nothing published to adopt, so unlike every other capability interface there is no specification to take whole: the contract below is ours to write and must be labelled as such. | sourced | `F-b3-04`, `E-capability-durable-execution`, `E-seam-b5` "*(no standard; see B5)*" |
| Proposed: the interface expresses step, idempotency key, checkpoint and resume point, and nothing else. A concept that only means something under replay - deterministic workflow code, worker registration, a task queue, an event history format - is an engine detail that a step log in a database could never implement, so it does not belong in the contract. Research query: has a step-log-in-a-database adapter (X-cap-durable-execution-006's relational-store-backed engine) actually been run to confirm every field on this list is truly absent from its schema, or is the list reasoned from the vendor's marketing description alone? | proposed | `F-b3-04` |
| Proposed: a step's checkpoint and the step's own effect become durable in one commit, or the step is not complete. A checkpoint written after the effect leaves a window in which a crash produces the effect twice; a checkpoint written before it leaves one in which the effect never happens and the run believes it did. Research query: is there a fetched primary source on the exactly-once-commit ordering this row asserts, rather than deriving it from first principles about crash windows? | proposed | - |
| Every externally-triggered action is safe to replay, and here that obligation lands per step rather than per run: a run key alone deduplicates whole submissions, while a restart in the middle needs each step to carry its own key. | sourced | `F-b4-08`, `E-capability-durable-execution` "Every externally-triggered action is safe to replay" |
| The interface must not assume a server is reachable: the orchestrator this capability is served by today has its data directory present and nothing listening, while durable workflow orchestration and human-in-the-loop signals are designed around it (claimed, per PASS.md A6). An interface that needs a running server is a design that is already down. | sourced | `F-a6-02`, `E-not-running-temporal` "Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down" |
| How durability is achieved is invisible at the interface: durable execution is a class of engine that journals every step so a run can resume from exactly where it stopped, regardless of what crashed. A second adapter that instead commits a row beside the effect and replays nothing is a genuinely different execution model on the same interface (proposed, drawn from the cited pair of vendor comparisons). A caller that can tell which one answered is reading a field that should not exist. | sourced | `X-cap-durable-execution-001`, `X-cap-durable-execution-006` "Durable execution is a class of workflow engine that journals every step so an agent can resume from exactly where it stopped, regardless of what crashed." |
| agentic-stack states design rule 3 (F-b1-04). Its consequence here is that the second adapter must break the assumption the first one rests on - a separate server holding history - rather than being another engine of the same shape, or the pair proves nothing about this interface. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| cap-errors owns the failure shape (F-b4-07). What this boundary adds: a lost or unreadable checkpoint is a failure with a type, never a silent restart from step one, because a run that quietly begins again is indistinguishable from one that resumed correctly. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a run through the same call with the same two fields. Which one started it is not a field of the run, so a crash and a restart are handled identically whichever way the work arrived. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: changing the executor, moving where checkpoints are stored, or adding steps to the sequence changes nothing in a caller that sends a key and reads an outcome. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: worker registration, task queues, event-history formats, determinism requirements on the caller's code, and any server endpoint or namespace. Each is a property of one way of achieving durability and none is needed to know which step to run next. Research query: does the second, step-log-style adapter's own interface confirm none of these fields is unavoidable, closing the loop this row currently only argues from the first adapter's shape? | proposed | - |
| Recurrence and scheduling are a separate capability with a published standard of its own, so 'run this every night' is not a durable-execution operation even when the same engine happens to offer it; sourcing it here would make that engine unswappable for a reason unrelated to durability. | sourced | `F-b3-15` "RFC 5545 recurrence rules" |
| Proposed: the identity of the durable store. This capability needs a place to checkpoint, not the platform's own state seam; binding the contract to one store is how the thing behind it stops being swappable. Research query: does seam-state's own contract explicitly disclaim durable execution's checkpoint store as out of scope, or is the boundary between the two only asserted here? | proposed | - |
| The criterion a unit's result will be judged against never travels in a step input, a checkpoint, or an event history the resumed unit can read back: an agent sees its outcome, never the criterion it is judged against. agentic-stack states design rule 6 (F-b1-07); the consequence here (proposed) is that resume replays what the unit already did, and a replayed input is still an input, so anything hidden from the unit on the first attempt stays hidden on every later one. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability with no standard to adopt, and write the contract in four words before any engine is named: step, idempotency key, checkpoint, resume point. Mark the whole contract as ours rather than adopted. | build-skill-authoring and agentic-stack require an interface to cite the standard that governs it; this row has none, so the honest move is to say so and keep the vocabulary small enough that nothing else can creep in. | sourced | `F-b3-04`, `F-b1-03` "*(no standard; see B5)*" |
| 2 | Give every step its own idempotency key, derived from the run key and the step id, and record it on the step record before the step's effect is attempted. | Replay safety is an obligation on every externally-triggered action, and a run-level key only protects the resubmission case; the crash-at-step-11 case is protected by the per-step key and by nothing else. | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| 3 | Define step completion as one commit of the checkpoint and the step's effect together, and define resume as 'the first step with no such commit'. Where an effect cannot join that commit, require the effect's own idempotency key to be the deduplicator and record that gap explicitly. Research query: see the one-commit research query on the sibling invariant row above. | Proposed. This is the one rule that decides whether a resumed run repeats work: the two-writes ordering problem has no correct order, so the contract has to demand a single commit or an explicitly keyed effect instead. | proposed | - |
| 4 | Reject any proposed field that only means something under replay - deterministic execution, worker or task-queue identity, history size, a server address - and put it in the adapter instead. Research query: see the interface-scope research query on the sibling invariant row above. | Proposed. A field the in-process step log cannot implement would force every future adapter to imitate one engine's execution model, which is exactly the shaping that a second adapter exists to catch. | proposed | `F-b1-04` |
| 5 | Design so that a run can make progress with no separate process running, and count the processes required for progress as a property of each adapter rather than of the interface. | The orchestrator on this substrate is present with nothing listening while the work designed around it waits (claimed, per PASS.md A6), so an interface that presumes a reachable server has already failed on the host it was written for. | sourced | `F-a6-02` "server not listening on `7233`/`8233`" |
| 6 | Pick the second adapter on execution-model axes, as build-adapter-pair defines them: locus_of_durability_and_verification, processes_required_for_progress and replay_determinism_required must all differ from today's adapter. | agentic-stack states design rule 3 (F-b1-04). What this adds: another engine that also journals history onto a separate server would agree with today's adapter on all three axes, so the swap would test configuration rather than the contract. | sourced | `F-b1-04`, `F-part-c-05` "chosen to prove the interface is not shaped around its current implementation" |
| 7 | Judge a candidate engine by the crash criterion in this skill's definition of done, run from one suite over both adapters, before it is allowed to serve the interface. | agentic-stack and build-definition-of-done already state that a criterion nothing can fail is not a criterion (F-part-c-04). What this adds: the property worth gating on here is exactly-once effect under a real kill, because every other property of an executor is visible without crashing it. | sourced | `F-part-c-04`, `F-b1-04` "A criterion nothing can fail is not a criterion" |
| 8 | Return every failure as the typed problem object cap-errors defines, including 'this run cannot be resumed', and never let an unreadable checkpoint fall back to starting again. | cap-errors owns the failure shape (F-b4-07); what this adds is that the most expensive failure of this capability is silent, so it has to be given a name and a type before it can be observed at all. | sourced | `F-b4-07` "Never parsed from prose" |
| 9 | Send a run key you can reproduce and the steps in order. Take every default. Do not send a resume flag, an attempt number or a starting index - there is no field for them and you would not want to own the decision. | It has to be simple to use, and every field you fill in is a decision you now own; the resume point is derived from what is already committed, which is a fact the platform has and you do not. | sourced | `T-t3-01` "It has to be simple to use." |
| 10 | Proposed: open references/durable-execution-shapes.md when implementing or reviewing the full step-record and run-state schemas or the exactly-once argument behind them. The body of this skill is enough to judge an engine and to write the contract without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full schemas exceed the progressive-disclosure budget for a skill body, and a reader deciding whether an engine may serve this interface does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the green-gate finding (F-a7-03). What it adds here: a resume check that never crashed proves nothing, so assert steps_replayed > 0 as well as the effect count, or a run that simply completed will report the same green as one that survived a kill. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Expect the workload the research on file describes: runs that go on for hours, pause for human approval, resume from a crash with the same tool-call history, and bill nothing while they wait. The record is a search result rather than a page that was read, so treat it as the shape of the demand and not as a measurement. | sourced | `X-cap-durable-execution-007` "resume from a crash with the same tool-call history, and bill nothing while they wait" |
| Proposed: derive the step key from the run key and the step id, never from a timestamp, a random value or an attempt counter. A key that changes on restart is indistinguishable from no key at all, and it fails only under the crash it was meant to survive. | proposed | `F-b4-08` |
| Keep undo out of this interface (proposed). Reversing prior operations with compensating transactions is a real pattern in the records on file, but it is a placement rule over a sequence of steps rather than a checkpointing primitive, and merging the two would make compensation an engine feature that only one adapter can supply. | sourced | `X-cap-durable-execution-003` "prior operations being reversed using compensating transactions" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-temporal` | today | begin_run, checkpoint_step, resume_point and read_run served by an external workflow orchestrator with deterministic replay: history lives on a separate server, and a crashed run is rescheduled by replaying that history onto the workflow code. PASS.md B3 names Temporal in this row's adapter column. | Proposed: cannot make progress while the server is unreachable, which is the state PASS.md A6 records for it - data directory present, nothing listening on 7233/8233. It also requires the executed code to be deterministic so history can be replayed, and requires workers to be registered before any step runs; neither requirement is expressible in the interface. | Select the executor by configuration, run the same 20-step crash suite against both adapters, and assert the effect count per step and steps_replayed from the run state rather than from the engine's own console. | claimed | `F-b3-04`, `F-a6-02` "\| Temporal \| Restate · DBOS · Inngest" |
| `E-swap-candidate-dbos` | second | the same four operations served by an in-process transactional step log over a relational database: the checkpoint is a row committed in the same database transaction as the step's own effect, and resume is a query for the first step with no committed row. A research record on file describes DBOS reusing Postgres as the durability layer while Temporal runs a dedicated cluster. | Proposed: cannot checkpoint an effect that lives outside the database in one commit - that case falls back to the step's own idempotency key - and offers no cross-process history, no replay and no view of a run from a machine that cannot reach the database. It has nothing to register and nothing to replay, which is the point. | Proposed: the axes that differ are locus_of_durability_and_verification (history on a separate server versus a row beside the effect), processes_required_for_progress (a server and a registered worker versus one) and replay_determinism_required (true versus false). Select by configuration with no code edit between runs and compare both reports against the same declared gaps. | claimed | `F-b3-04`, `X-cap-durable-execution-006`, `F-b1-04` "DBOS reuses Postgres as the durability layer for workflows, while Temporal runs a dedicated cluster" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first implementation of this interface: `python3 tools/conformance_durable_execution.py --adapter today --adapter second --steps 20 --side-effecting-step 11 --kill-at 11 --report out/durable-execution-conformance.json`. Per adapter it runs a 20-step workflow with a side-effecting step, sends `kill -9` to the executor at step 11, restarts it, and asserts that each side-effecting step has exactly one committed effect keyed by its step idempotency key and that `steps_replayed > 0` so the crash actually happened. Across adapters it asserts `adapters_run >= 2`. |
| Expected | exit 0 and one line per adapter of the form `adapter=<entity> steps_committed=20 steps_replayed=<greater than 0> effects_for_step_11=1 duplicate_effects=0`, followed by `adapters_run=2`. |
| Deliberate breakage | Drop the idempotency key from the step record - write the checkpoint with the step id alone - change nothing else, and re-run the same command. |
| Expected failure | The restart cannot tell the retried step 11 from a new one, the effect count for step 11 becomes 2, `duplicate_effects` becomes non-zero, and the run exits non-zero naming the adapter and the step; `steps_replayed` stays greater than 0, which is what shows the failure is duplication and not a crash that never happened. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-08` "Every externally-triggered action is safe to replay" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`

Used by: `cap-durable-execution-implement`, `compose-operators`, `seam-dispatch`, `xc-compensation`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which durable-execution adapter is primary: the external orchestrator with replay, or the in-process transactional step log? | Measure, for a 50-step workflow under both, restart-to-resume latency, steps per second, and the number of separate processes that must be running for a workflow to make progress. The last number is the one that matters, given a data directory present with no server listening. | The in-process transactional step log, because its answer to the last measurement is one; the orchestrator stays as today's adapter and the interface presumes neither. | `F-a6-02` "Data directory present; server not listening" |
| The end-to-end consumption reference deduplicates a whole completed key and appends zero records; it has no mid-run resume point, so the resume_point operation defined here has no counterpart there yet. Which shape wins? | Extend the reference runner with a mid-run kill and see whether resuming needs a new field on its per-step ledger record, or whether the existing step id and idempotency key already identify the first incomplete step. | Treat whole-key replay as the degenerate case where the resume point is 'terminal', and keep the per-step resume point in the interface, since the reference already writes one ledger record per step. | `T-t6-01` "There is one way to consume the platform, shown as code end to end" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-durable-execution 2831cb4f, 2026-09-03 |
