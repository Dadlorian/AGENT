# core-planner: full shapes, worked calls, worked refusal

Long material for `core-planner`. Open it when you are writing the full plan or cost-input
schema, when you need the worked call for a way in you have not handled yet, or when you are
rendering a refusal and want the instance rather than the rule. The skill body is enough to
call the planner and to judge an implementation without this file.

Everything below is **proposed** unless it cites a knowledge-base id: PASS.md names the
function `document -> plan + cost` (F-b2-03) and design rule 5 (F-b1-06); it does not give
these field names.

## 1. Cost inputs (proposed)

The cost table and the quantiles are one value, read at the pinned head and passed in.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:plan:cost-inputs:0.1",
  "title": "Cost inputs",
  "type": "object",
  "additionalProperties": false,
  "required": ["cost_inputs_version", "at_head", "rows"],
  "properties": {
    "cost_inputs_version": { "const": "0.1" },
    "at_head": { "type": "string", "minLength": 1 },
    "currency": { "type": "string", "default": "USD" },
    "rows": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["selector", "unit_micros"],
        "properties": {
          "selector": {
            "type": "string",
            "pattern": "^[a-z0-9-]+/[a-z0-9-]+$",
            "description": "operator/model_class. A selector, never a vendor or an endpoint."
          },
          "unit_micros": { "type": "integer", "minimum": 0, "description": "The rate card figure." },
          "p50_micros": { "type": "integer", "minimum": 0, "description": "Measured quantile from cost_history at this head." },
          "p95_micros": { "type": "integer", "minimum": 0 },
          "observations": { "type": "integer", "minimum": 0, "description": "n behind the quantiles. Zero means rate card only, and the plan says so." }
        }
      }
    }
  }
}
```

Pricing rule (proposed): a step is priced at `p50_micros` for its floor and `p95_micros` for its
worst case when `observations` is at or above the configured minimum; otherwise both come from
`unit_micros` and the derivation records `quantile: "p50"` with `observations: 0`, so a reader can
see the estimate was a rate card and not a measurement. A selector with no row at all is a refusal,
never a default (see section 4).

## 2. Plan, in full (proposed)

The summary shape is in the skill body. In full, a plan adds only bookkeeping:

| Field | Type | Why it is there |
|---|---|---|
| `plan_version` | const `"0.1"` | The revision a caller says it speaks. |
| `document_digest` | `sha256:` | What was priced. Two plans of one document are comparable only through this. |
| `at_head` | string | The pinned head every read was taken at. |
| `cost_inputs_digest` | `sha256:` | Which cost inputs produced the numbers, so a price change is attributable. |
| `steps[]` | plan-step | Ordered. Each carries its own floor, worst case and derivation. |
| `floor_micros` | integer | Sum of step floors. What a ceiling is checked against before anything starts. |
| `worst_case_micros` | integer | Sum of step worst cases. What a human approves against. |
| `requested_by` | actor string | Carried from the envelope for audit. Recorded, never branched on. |
| `alternatives[]` | optional | Priced candidates that were rejected, when `compare` ran. |

## 3. Three worked calls, one per way in (TARGET T1: T-t1-01, T-t1-02, T-t1-03)

The call is identical in all three. Only the envelope that carried the document differs, and the
only trace of it on the plan is `requested_by`.

### 3.1 A human declared the work (T-t1-01)

```json
{
  "call": "plan",
  "document_digest": "sha256:1f0c9a2b3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8",
  "at_head": "head:run-human-0001:47",
  "cost_inputs_digest": "sha256:aa11bb22cc33dd44ee55ff6677889900aa11bb22cc33dd44ee55ff6677889900",
  "requested_by": "user:corey"
}
```

```json
{
  "plan_version": "0.1",
  "document_digest": "sha256:1f0c9a2b3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8",
  "at_head": "head:run-human-0001:47",
  "cost_inputs_digest": "sha256:aa11bb22cc33dd44ee55ff6677889900aa11bb22cc33dd44ee55ff6677889900",
  "requested_by": "user:corey",
  "steps": [
    {
      "step_id": "triage",
      "operator": "agent",
      "model_class": "i-fast",
      "floor_micros": 40000,
      "worst_case_micros": 90000,
      "check_ids": ["dod-1"],
      "derivation": { "cost_table_row": "agent/i-fast", "quantile": "p50", "observations": 312 }
    },
    {
      "step_id": "fix",
      "operator": "loop",
      "model_class": "cli-",
      "floor_micros": 120000,
      "worst_case_micros": 360000,
      "check_ids": ["dod-2", "dod-3"],
      "derivation": { "cost_table_row": "loop/cli-", "quantile": "p95", "observations": 88 }
    }
  ],
  "floor_micros": 160000,
  "worst_case_micros": 450000
}
```

### 3.2 An agent declared the work (T-t1-02)

Same call, different requester; the second step is a replay because the Ledger already holds a
result for it at this head (F-b2-06), so it is planned at zero rather than re-priced.

```json
{
  "call": "plan",
  "document_digest": "sha256:2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c",
  "at_head": "head:run-partner-0007:47",
  "cost_inputs_digest": "sha256:aa11bb22cc33dd44ee55ff6677889900aa11bb22cc33dd44ee55ff6677889900",
  "requested_by": "agent:partner-sre-bot"
}
```

```json
{
  "plan_version": "0.1",
  "requested_by": "agent:partner-sre-bot",
  "steps": [
    {
      "step_id": "repro",
      "operator": "agent",
      "model_class": "f-grunt",
      "floor_micros": 25000,
      "worst_case_micros": 25000,
      "check_ids": ["dod-1"],
      "derivation": { "cost_table_row": "agent/f-grunt", "quantile": "p50", "observations": 1204 }
    },
    {
      "step_id": "logs",
      "operator": "agent",
      "model_class": "b-deep",
      "floor_micros": 0,
      "worst_case_micros": 0,
      "replay_of": "dispatch:9f2c1a",
      "check_ids": ["dod-2"],
      "derivation": { "cost_table_row": "agent/b-deep", "quantile": "p50", "observations": 41 }
    }
  ],
  "floor_micros": 25000,
  "worst_case_micros": 25000
}
```

### 3.3 An event declared the work (T-t1-03)

An internal alert and a recurrence rule are both events; the actor grammar tells them apart and
nothing downstream reads it.

```json
{
  "call": "plan",
  "document_digest": "sha256:3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d",
  "at_head": "head:run-sweep-0031:47",
  "cost_inputs_digest": "sha256:aa11bb22cc33dd44ee55ff6677889900aa11bb22cc33dd44ee55ff6677889900",
  "requested_by": "service:alerting"
}
```

```json
{
  "plan_version": "0.1",
  "requested_by": "schedule:nightly-fault-sweep",
  "steps": [
    {
      "step_id": "sweep",
      "operator": "agent",
      "model_class": "f-smoke",
      "floor_micros": 8000,
      "worst_case_micros": 12000,
      "check_ids": ["dod-1"],
      "derivation": { "cost_table_row": "agent/f-smoke", "quantile": "p95", "observations": 903 }
    }
  ],
  "floor_micros": 8000,
  "worst_case_micros": 12000
}
```

## 4. The worked refusal

A step whose selector has no row in the cost inputs is refused. Until the registry row named in
this skill's open question exists, the refusal is returned as the registered `document-invalid`
(422, not retryable), with the step and the missing selector in `causes`. Nothing is spent, and
no partial plan is returned.

```json
{
  "type": "urn:agentic:problem:document-invalid",
  "title": "The declared work cannot be priced at this head",
  "status": 422,
  "detail": "Step 'notify' selects cost row 'notify/i-escalate', which has no row in the cost inputs at head:run-human-0001:47.",
  "instance": "urn:agentic:plan:run-human-0001",
  "retryable": false,
  "correlation": { "run_id": "run-human-0001", "correlation_id": "corr-human-0001", "depth": 0 },
  "causes": [
    {
      "type": "urn:agentic:problem:document-invalid",
      "title": "Missing cost selector",
      "status": 422,
      "detail": "step_id=notify selector=notify/i-escalate cost_inputs_digest=sha256:aa11bb22...",
      "retryable": false
    }
  ]
}
```

Read it as: the plan was refused, not estimated; `retryable` is false because a retry with the same
inputs at the same head returns the same refusal; and the fix is a cost-inputs row or a different
operator, both of which change the inputs rather than the planner.
