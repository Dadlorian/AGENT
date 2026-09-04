# Ledger shapes, worked entries and the worked rejection

Long material for `core-ledger`. Proposed throughout unless a row cites a knowledge-base id; the skill body
is enough to append correctly and to judge an implementation without this file. Open it when you are writing
the full entry schema, the kind vocabulary, the entry a producer kind you have not handled yet would append,
or the refusal a conflicting key returns.

Resolve every id named here with `python3 tools/kb.py show <id>`.

## 1. Entry kinds (proposed vocabulary; closed set)

| Kind | Terminal | Appended when | Carries |
|---|---|---|---|
| `run-started` | no | The envelope validated and the plan was priced | `envelope_digest`, `plan_estimate_micros`, `budget_ceiling_micros` |
| `step-observed` | no | One unit of work returned a result | `step_id`, `cost_micros`, `budget_remaining_micros`, `output_digest` |
| `judged` | no | A verdict was reached on a step | `step_id`, `criterion_ref`, `verdict` — never the criterion body |
| `approval-parked` | no | Work stopped for a human decision | `step_id`, `prompt_digest` |
| `approval-returned` | no | The human decision came back | `step_id`, `decision` |
| `run-completed` | yes | The run reached an outcome, success or failure | `outcome`, `cost_micros`, `problem` when it failed |
| `superseded` | no | An earlier entry was corrected | `supersedes`, `reason` |

Exactly one terminal entry exists per `idempotency_key`. That is the count the definition of done asserts on,
and the count a store that overwrites on a duplicate key drives to 0 or 2 (PASS.md B2, `F-b2-06`).

## 2. Full entry schema (proposed)

The body of the skill carries the summary shape; this is the whole of it.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:ledger:entry:0.1",
  "title": "LedgerEntry",
  "type": "object",
  "additionalProperties": false,
  "required": ["seq", "prev", "hash", "run_id", "kind", "actor",
               "idempotency_key", "correlation_id", "recorded_at"],
  "properties": {
    "seq":             { "type": "integer", "minimum": 0 },
    "prev":            { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "hash":            { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "run_id":          { "type": "string", "minLength": 1 },
    "kind":            { "enum": ["run-started", "step-observed", "judged", "approval-parked",
                                  "approval-returned", "run-completed", "superseded"] },
    "terminal":        { "type": "boolean", "default": false },
    "actor":           { "type": "string",
                         "pattern": "^(user|agent|service|schedule):[a-z0-9][a-z0-9._@-]*$" },
    "delegation_depth":{ "type": "integer", "minimum": 0 },
    "entry_kind":      { "enum": ["human", "event", "schedule", "external"] },
    "idempotency_key": { "type": "string", "minLength": 1 },
    "envelope_digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "correlation_id":  { "type": "string", "minLength": 1 },
    "step_id":         { "type": "string" },
    "criterion_ref":   { "type": "string", "format": "uri",
                         "description": "Opaque handle. The criterion body is never an entry field." },
    "verdict":         { "enum": ["pass", "fail"] },
    "cost_micros":     { "type": "integer", "minimum": 0 },
    "budget_remaining_micros": { "type": "integer", "minimum": 0 },
    "policy_decision": { "enum": ["allow", "deny"] },
    "output_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "supersedes":      { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "problem":         { "$ref": "urn:agentic:problem:0.1" },
    "recorded_at":     { "type": "string", "format": "date-time" }
  }
}
```

`hash` commits to `prev` and to the canonical body of this entry, which is what makes an edit anywhere
behind it stop recomputing — the property the store running today already has (`F-a5-03`).

## 3. One worked entry per way in (TARGET T1)

Three producers, one shape. The only field that differs by producer is `actor` and the envelope fields it
carries; the kind vocabulary, the chain fields and the cross-cutting fields are identical, which is what
lets one fold answer the dedup question whichever way the work came in.

### 3.1 A human enters (`T-t1-01`)

```json
{
  "seq": 0,
  "prev": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "hash": "sha256:50873a6c37f3d80c8a6cfdb5e1c715d91dc668ff8b33a88a963dd6e2b4ead07d",
  "run_id": "run-human-0001",
  "kind": "run-started",
  "terminal": false,
  "actor": "user:corey",
  "delegation_depth": 1,
  "entry_kind": "human",
  "idempotency_key": "human-checkout-500s-2026-09-03",
  "envelope_digest": "sha256:7e5e86708876cce91126bb435cf21aaaaf89b44d5f7b6760cb9598d9c4c009d6",
  "correlation_id": "corr-human-0001",
  "policy_decision": "allow",
  "budget_remaining_micros": 1500000,
  "recorded_at": "2026-09-03T09:12:01Z"
}
```

### 3.2 An agent enters (`T-t1-02`)

```json
{
  "seq": 1,
  "prev": "sha256:50873a6c37f3d80c8a6cfdb5e1c715d91dc668ff8b33a88a963dd6e2b4ead07d",
  "hash": "sha256:d096193c95c1957c983632e11f317e52c2c4b5877d90a04f8020c4a9154f1bf2",
  "run_id": "run-external-0001",
  "kind": "step-observed",
  "terminal": false,
  "actor": "agent:partner-sre-bot",
  "delegation_depth": 3,
  "entry_kind": "external",
  "idempotency_key": "partner-task-7c41e2",
  "correlation_id": "corr-external-0001",
  "step_id": "triage",
  "cost_micros": 15300,
  "budget_remaining_micros": 1484700,
  "policy_decision": "allow",
  "output_digest": "sha256:0c7ac1524c7ab5870f1018b8f3547b8b4c6324ebedc61530354010f890d6b716",
  "recorded_at": "2026-09-03T09:14:02Z"
}
```

### 3.3 An internal or external event enters (`T-t1-03`)

A fired recurrence rule is the same producer kind reaching the same shape; only the subject prefix differs
(`service:` for something that happened, `schedule:` for a time that arrived).

```json
{
  "seq": 14,
  "prev": "sha256:8b2e1cf42af4a63eb9063e417ceeeb11fd92537b6a14b635c5bc5fa7cb13e5c6",
  "hash": "sha256:520500057d324ee2bb91c9834b2a80f5fbbe3134c032670a391dd7637c583492",
  "run_id": "run-event-0001",
  "kind": "run-completed",
  "terminal": true,
  "actor": "service:alerting",
  "delegation_depth": 2,
  "entry_kind": "event",
  "idempotency_key": "alert-8f31c0-checkout-500s",
  "envelope_digest": "sha256:3e81b9cd3e17efe3f6592369bc59c5c3a042b5d473198bb1bfa92ed1c7535dad",
  "correlation_id": "corr-event-0001",
  "cost_micros": 551800,
  "budget_remaining_micros": 948200,
  "policy_decision": "allow",
  "recorded_at": "2026-09-03T09:07:42Z"
}
```

A schedule entry is the same record with `"actor": "schedule:nightly-fault-sweep"` and
`"entry_kind": "schedule"`. Nothing else about the entry, the fold or the dedup query changes, which is
what TARGET T2.2 asks for: the producer can be enhanced without touching the rest.

## 4. The worked rejection

Same key, different body. The registered row in the closed registry in `docs/decomposition.md`
section 2.1.6 is `idempotency-conflict`, 409, not retryable, raised when the same key arrives with a
different request body. No new type is minted here.

```json
{
  "type": "urn:agentic:problem:idempotency-conflict",
  "title": "Same idempotency key, different envelope",
  "status": 409,
  "detail": "key alert-8f31c0-checkout-500s completed at seq 14 with envelope_digest sha256:3e81b9cd... ; this submission carries sha256:b1907d40...",
  "instance": "urn:agentic:run:run-event-0001",
  "retryable": false,
  "correlation": "corr-event-0002"
}
```

What the caller does with it is mechanical: compare the two digests, and either resubmit under a new key
because the work really is different, or fix the body back because the change was accidental. The rule
that makes that possible is stated in the skill body — a refusal is typed and never parsed from prose
(`F-b4-07`, `F-b3-13`, owned by `cap-errors`).

A replay, by contrast, is not a rejection at all: the answer comes back with `state: "terminal"`,
`records_appended: 0` and the prior entry, and the caller returns that entry as the result.

## 5. Reading order for an implementer

1. Section 1, to know what may be appended at all.
2. Section 2, to write the append path and the chain.
3. Section 3, to check that one fold serves every producer.
4. Section 4, to render the refusal without inventing a type.
