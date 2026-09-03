# Durable execution: full shapes and the exactly-once argument

Proposed material. The body of `cap-durable-execution` is enough to judge a candidate executor and to
write the contract; open this file when implementing or reviewing the shapes themselves.

Every schema here is JSON Schema 2020-12. Nothing in this file is sourced from PASS.md unless a kb id
is named on the line. Products appear nowhere here: the executor is named only in the skill's Adapters
section.

## 1. Step record

One row per step. This is the whole vocabulary of the capability.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:step-record:0.1",
  "title": "StepRecord",
  "type": "object",
  "additionalProperties": false,
  "required": ["run_key", "step_id", "step_idempotency_key", "state", "committed_with_effect"],
  "properties": {
    "run_key":              { "type": "string", "minLength": 1,
                              "description": "The caller's key for the whole run. Stable across restarts." },
    "step_id":              { "type": "string", "minLength": 1,
                              "description": "Position-independent name of the step in the sequence." },
    "step_idempotency_key": { "type": "string", "minLength": 1,
                              "description": "Derived: hash(run_key, step_id). Never a timestamp, a random value or an attempt counter." },
    "attempt":              { "type": "integer", "minimum": 1, "default": 1,
                              "description": "Diagnostic only. It must not appear in step_idempotency_key." },
    "state":                { "enum": ["pending", "complete", "failed"] },
    "committed_with_effect":{ "type": "boolean",
                              "description": "True only when the checkpoint became durable in the same commit as the step's own effect. False means the effect's own key is the deduplicator and the gap is declared." },
    "effect_ref":           { "type": "string",
                              "description": "Opaque handle to what the step did outside the checkpoint store, when there is one." },
    "output_digest":        { "type": "string", "description": "sha256 of the step's output. Never the output itself." },
    "committed_at":         { "type": "string", "format": "date-time" },
    "problem":              { "$ref": "urn:agentic:problem:0.1" }
  }
}
```

Note the fields that are deliberately absent: worker identity, task queue, history length, a server
address, and any determinism flag. Each of those is a property of one way of achieving durability
(cap-durable-execution, `Deliberately not exposed`).

## 2. Run state

What a restart reads, and what the conformance run asserts on.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:run-state:0.1",
  "title": "RunState",
  "type": "object",
  "additionalProperties": false,
  "required": ["run_key", "resume_point", "steps_committed", "steps_replayed", "terminal"],
  "properties": {
    "run_key":         { "type": "string", "minLength": 1 },
    "resume_point":    { "type": "integer", "minimum": 0,
                         "description": "Index of the first incomplete step. Equal to steps_total when the run is terminal." },
    "steps_total":     { "type": "integer", "minimum": 0 },
    "steps_committed": { "type": "integer", "minimum": 0 },
    "steps_replayed":  { "type": "integer", "minimum": 0,
                         "description": "Committed steps skipped rather than re-executed after a restart. Zero means no restart happened, which is why a resume check asserts it is greater than zero." },
    "terminal":        { "type": "boolean" },
    "correlation_id":  { "type": "string",
                         "description": "Explicit attribute, carried across the restart; trace parentage does not survive it (F-a7-02, stated by agentic-stack)." },
    "problem":         { "$ref": "urn:agentic:problem:0.1" }
  }
}
```

## 3. The exactly-once argument, in four lines

1. A step does two things: it commits an effect, and it records that it did.
2. Two separate writes have no correct order. Effect first, then record: a crash between them repeats
   the effect. Record first, then effect: a crash between them loses the effect while the run believes
   it happened.
3. So the contract demands one commit, `committed_with_effect: true`.
4. Where one commit is impossible - the effect lives outside the checkpoint store - the step's own
   idempotency key is the deduplicator, `committed_with_effect` is false, and the gap is declared and
   asserted on rather than assumed away.

This is why the definition of done asserts an effect count of exactly 1 for the side-effecting step
*and* `steps_replayed > 0`: the first number tests the argument above, and the second proves the crash
that the argument exists for actually occurred.

## 4. Problem types this capability raises

Types are registered in the closed registry `cap-errors` owns; these are the suffixes this boundary
adds (proposed).

| `type` suffix | Status | Raised when |
|---|---|---|
| `durable-run-unresumable` | 409 | A run key exists but its step records cannot be read or are inconsistent. Never fall back to starting again. |
| `durable-step-key-missing` | 422 | A step was submitted with no step idempotency key. This is the deliberate breakage in the definition of done. |
| `durable-effect-unconfirmed` | 503 | A step's effect could not be confirmed committed and its key could not be checked; the run stops rather than guessing. |
