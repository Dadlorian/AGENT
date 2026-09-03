# Model access: full shapes and routing table (proposed)

Proposed. Long material moved out of `skill.json` under the progressive-disclosure budget. The
skill body is enough to judge a candidate adapter and to write the contract; open this file only
when writing or reviewing the schemas themselves, or the routing test vectors.

Every schema here is JSON Schema 2020-12 and every one is **proposed**: PASS.md gives Model access
a row, a standard and an adapter column (`F-b3-03`), not a list of calls. The one sourced constraint
the shapes encode is that a caller names a class and never a vendor (`F-a4-01`).

## 1. completion-request

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:completion-request:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["model_class", "messages", "idempotency_key", "ceiling_micros"],
  "properties": {
    "model_class": {"type": "string", "pattern": "^(f|i|b|cli)-[a-z0-9-]*$"},
    "messages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["role", "content"],
        "properties": {
          "role": {"enum": ["system", "user", "assistant", "tool"]},
          "content": {"type": "string"},
          "tool_call_id": {"type": "string"}
        }
      }
    },
    "idempotency_key": {"type": "string", "minLength": 1},
    "ceiling_micros": {"type": "integer", "minimum": 0},
    "max_output_tokens": {"type": "integer", "minimum": 1},
    "deadline": {"type": "string", "format": "date-time"},
    "correlation_id": {"type": "string", "minLength": 1},
    "actor": {"type": "string", "minLength": 1}
  }
}
```

`deadline` is the only eligibility signal for the cheap slow path. There is deliberately no
`adapter`, `provider`, `model`, `endpoint`, `api_base` or `api_key` member: a caller that can set
one can branch on it, and the adapter has then become part of the contract.

## 2. claim-ticket

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:claim-ticket:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["ticket_id", "state", "model_class", "cancellable"],
  "properties": {
    "ticket_id": {"type": "string", "minLength": 1},
    "state": {"enum": ["pending", "redeemed", "failed", "cancelled"]},
    "model_class": {"type": "string"},
    "cancellable": {"type": "boolean"},
    "earliest_retry": {"type": "string", "format": "date-time"},
    "result": {"$ref": "urn:agentic:cap:model-access:completion-result:0.1"},
    "problem": {"$ref": "urn:agentic:problem:0.1"}
  },
  "allOf": [
    {"if": {"properties": {"state": {"const": "redeemed"}}, "required": ["state"]},
     "then": {"required": ["result"]}},
    {"if": {"properties": {"state": {"const": "failed"}}, "required": ["state"]},
     "then": {"required": ["problem"]}}
  ]
}
```

## 3. completion-result

One result schema for every adapter. The conformance run in the skill's definition of done
validates both adapters' results against this and nothing else.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:completion-result:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["text", "cost_micros", "cost_status", "model_class"],
  "properties": {
    "text": {"type": "string"},
    "model_class": {"type": "string"},
    "cost_micros": {"type": "integer", "minimum": 0},
    "cost_status": {"enum": ["committed", "reconciled"]},
    "tokens_in": {"type": "integer", "minimum": 0},
    "tokens_out": {"type": "integer", "minimum": 0},
    "finish_reason": {"enum": ["stop", "length", "tool_call", "content_filter", "cancelled"]}
  }
}
```

`cost_status` is what makes the slow path representable: a batch submission commits spend when it
is submitted and the true figure arrives when the ticket is claimed. A synchronous adapter returns
`reconciled` immediately; a batch adapter returns `committed` first and `reconciled` on claim.

## 4. routing-decision and its test vectors

Routing is a pure function of `(model_class, unit_of_work, budget_remaining_micros, policy_verdict)`.
Because it takes no live state, it is tested from a table with no model reachable and no spend.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:routing-decision:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["endpoint_id", "reason", "class_honoured"],
  "properties": {
    "endpoint_id": {"type": "string", "minLength": 1},
    "reason": {"enum": ["class-default", "deadline-eligible", "budget-constrained", "policy-restricted"]},
    "class_honoured": {"type": "boolean"},
    "problem": {"$ref": "urn:agentic:problem:0.1"}
  }
}
```

`class_honoured` exists so that a routing decision which could not satisfy the requested class is
a visible fact rather than a silent substitution. When it is false, `route` returns a problem
instead of an endpoint; there is no fallback to a different class.

| Vector | class | budget remaining | policy verdict | deadline | expected |
|---|---|---|---|---|---|
| 1 | `i-fast` | above the ceiling | allow | none | class-default endpoint, `class_honoured` true |
| 2 | `b-deep` | above the ceiling | allow | 6 hours out | deadline-eligible endpoint, `cancellable` false on the ticket |
| 3 | `i-escalate` | below the estimated cost | allow | none | problem `budget-exhausted`, no endpoint |
| 4 | `i-fast` | above the ceiling | deny | none | problem `policy-denied`, no endpoint, zero spend |
| 5 | `f-grunt` | any | allow | none | local endpoint, `cost_micros` 0 expected |
| 6 | unknown class | any | allow | none | problem `no-endpoint-for-class`, never a substitution |

Vectors 3 and 4 are the ones that make routing worth testing: both must decide before any call is
made, which is only possible because routing sits in front of the adapter.
