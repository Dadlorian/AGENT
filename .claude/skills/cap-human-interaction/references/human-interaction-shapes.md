# Human interaction: full shapes, event table and worked decisions

Long material for `cap-human-interaction`. The skill body is enough to judge a pause-and-resume
implementation; open this when you are writing the schemas, the event stream or the fixtures.
Every schema here is **proposed** (our design): PASS.md B3 has no Human interaction row, so nothing
in this file is sourced from it. Ids resolve with `python3 tools/kb.py show <id>`.

## 1. HumanAsk (full)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:ask:0.1",
  "title": "HumanAsk",
  "description": "Proposed. What a run emits when it stops and needs a person. Durable: the surface renders it, the platform owns it.",
  "type": "object",
  "additionalProperties": false,
  "required": ["ask_version", "ask_id", "correlation_id", "run_id", "asked_at", "prompt", "response_schema", "proposed", "deadline_at", "allowed_decisions"],
  "properties": {
    "ask_version": {"const": "0.1"},
    "ask_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,63}$"},
    "correlation_id": {"type": "string", "minLength": 1},
    "run_id": {"type": "string", "minLength": 1},
    "asked_at": {"type": "string", "format": "date-time"},
    "prompt": {"type": "string", "minLength": 1, "maxLength": 2000},
    "response_schema": {"type": "object", "description": "JSON Schema 2020-12. A decision body is validated against this before the run resumes."},
    "proposed": {
      "type": "object",
      "additionalProperties": false,
      "required": ["action", "diff", "irreversibility"],
      "properties": {
        "action": {"type": "string", "minLength": 1},
        "diff": {"type": "string", "description": "The change itself, rendered so a reviewer judges the action rather than the paragraph describing it."},
        "irreversibility": {"enum": ["reversible", "compensatable", "irreversible"], "description": "Reversible: undo is a no-op. Compensatable: an inverse action exists (see xc-compensation). Irreversible: nothing undoes it."}
      }
    },
    "deadline_at": {"type": "string", "format": "date-time"},
    "allowed_decisions": {"type": "array", "minItems": 1, "items": {"enum": ["approve", "edit", "reject", "respond"]}},
    "audience": {"type": "array", "items": {"type": "string", "pattern": "^(user|agent|service):[a-z0-9][a-z0-9._@-]*$"}}
  }
}
```

## 2. HumanDecision (full)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:decision:0.1",
  "title": "HumanDecision",
  "description": "Proposed. What comes back. The run resumes on correlation_id; body carries what changed.",
  "type": "object",
  "additionalProperties": false,
  "required": ["decision_version", "ask_id", "correlation_id", "decision", "actor", "decided_at", "idempotency_key"],
  "properties": {
    "decision_version": {"const": "0.1"},
    "ask_id": {"type": "string", "minLength": 1},
    "correlation_id": {"type": "string", "minLength": 1},
    "decision": {"enum": ["approve", "edit", "reject", "respond"]},
    "actor": {"type": "string", "pattern": "^(user|agent|service|schedule):[a-z0-9][a-z0-9._@-]*$"},
    "decided_at": {"type": "string", "format": "date-time"},
    "body": {"type": "object", "description": "Required for edit, reject and respond; forbidden for approve. Validated against the ask's response_schema."},
    "idempotency_key": {"type": "string", "minLength": 8, "maxLength": 255}
  },
  "allOf": [
    {"if": {"properties": {"decision": {"const": "approve"}}, "required": ["decision"]}, "then": {"not": {"required": ["body"]}}},
    {"if": {"properties": {"decision": {"enum": ["edit", "reject", "respond"]}}, "required": ["decision"]}, "then": {"required": ["body"]}}
  ]
}
```

## 3. Event types on the run stream (proposed)

The prior art on file records around sixteen event types across lifecycle, message, tool-call, state
and interaction categories (`X-cap-human-interaction-002`, `X-end-to-end-016`). The proposed minimum
this capability needs is six; every event carries `type` and `correlation_id`.

| Event `type` | Emitted when | Carries |
|---|---|---|
| `run.started` | a run begins | `run_id`, `correlation_id`, `actor` |
| `step.progress` | a step produces something a person could read | step name, a summary line |
| `tool.proposed` | a gated action is about to run | the `proposed` object from the ask |
| `human.ask` | the run parks | the whole `HumanAsk` |
| `human.decided` | a decision is applied | `decision`, `actor`, `ask_id` |
| `run.finished` | the run reaches a terminal state | terminal state, spend |

## 4. Four worked decisions (proposed fixtures)

```json
{"decision_version": "0.1", "ask_id": "ask-deploy-0001", "correlation_id": "corr-human-0001",
 "decision": "approve", "actor": "user:corey", "decided_at": "2026-09-03T10:04:00Z",
 "idempotency_key": "ask-deploy-0001-approve"}
```

```json
{"decision_version": "0.1", "ask_id": "ask-deploy-0001", "correlation_id": "corr-human-0001",
 "decision": "edit", "actor": "user:corey", "decided_at": "2026-09-03T10:05:00Z",
 "body": {"patch": "--- a/pricing/coupon.py\n+++ b/pricing/coupon.py\n@@\n-    tier = ctx['tier']\n+    tier = ctx.get('tier', 'standard')\n"},
 "idempotency_key": "ask-deploy-0001-edit"}
```

```json
{"decision_version": "0.1", "ask_id": "ask-deploy-0001", "correlation_id": "corr-human-0001",
 "decision": "reject", "actor": "user:corey", "decided_at": "2026-09-03T10:06:00Z",
 "body": {"notes": "Coupon tiers are configured per-tenant; defaulting hides the real bug."},
 "idempotency_key": "ask-deploy-0001-reject"}
```

```json
{"decision_version": "0.1", "ask_id": "ask-window-0002", "correlation_id": "corr-human-0001",
 "decision": "respond", "actor": "user:corey", "decided_at": "2026-09-03T10:07:00Z",
 "body": {"window_hours": 12}, "idempotency_key": "ask-window-0002-respond"}
```

## 5. Refusals (proposed, RFC 9457 problem details)

`human-ask-expired` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry `cap-errors` owns; until that row lands an implementation
returns the registered `deadline-exceeded` with the ask id in `detail`. `document-invalid` below is already registered.

```json
{"type": "urn:agentic:problem:human-ask-expired", "title": "The ask is no longer open", "status": 409,
 "detail": "ask-deploy-0001 expired at 2026-09-03T18:00:00Z; the run terminated with deadline_exceeded.",
 "retryable": false, "correlation_id": "corr-human-0001"}
```

```json
{"type": "urn:agentic:problem:document-invalid", "title": "Decision body does not match the ask", "status": 422,
 "detail": "$.body: required property 'patch' is missing for decision 'edit'.",
 "retryable": false, "correlation_id": "corr-human-0001"}
```

Both suffixes need a row in the closed registry `cap-errors` owns before either is emitted.
