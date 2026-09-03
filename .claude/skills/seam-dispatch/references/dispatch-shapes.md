# seam-dispatch: the full shapes

Proposed. The body of `seam-dispatch` is enough to judge a candidate dispatcher and to make a first
call. Open this file when implementing or reviewing the wire shapes, when adding a member, or when
deciding whether a value belongs to the seam or to an adapter.

The summary shapes in `contract.shapes` are the same objects with the nested members elided. Nothing
here contradicts them; anything that did would be a defect in this file. Ids resolve with
`python3 tools/kb.py show <id>`.

## Where each shape comes from

| Shape | `$id` | Origin | Evidence |
|---|---|---|---|
| DispatchRequest | `urn:agentic:dispatch:request:0.1` | proposed, refined from the design note for this seam | `F-b5-03` "It must specify: the request shape" |
| DispatchResult | `urn:agentic:dispatch:result:0.1` | proposed; `state` adopted, `stop_reason` adopted plus five | `X-seam-dispatch-001`, `X-seam-dispatch-002` |
| DispatchStepRecord | `urn:agentic:dispatch:step:0.1` | proposed | `X-cross-structure-042`, `X-cross-structure-043`, `X-seam-dispatch-007` |
| DispatchContext | `urn:agentic:dispatch:context:0.1` | proposed | `X-end-to-end-004`, `X-end-to-end-005` |
| Problem | `urn:agentic:problem:0.1` | owned by `cap-errors`; named here, not redefined | `F-b4-07` |

## DispatchRequest, in full

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:request:0.1",
  "title": "DispatchRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["dispatch_id", "idempotency_key", "document", "criterion_ref",
               "actor", "budget", "deadline", "isolation", "correlation"],
  "properties": {
    "dispatch_id":     { "type": "string", "format": "uuid" },
    "context_id":      { "type": "string", "format": "uuid",
                         "description": "Groups related dispatches. Adopted from the task-lifecycle standard's context identifier (claimed, version unverified)." },
    "previous_dispatch_id": { "type": "string", "format": "uuid",
                         "description": "Set when this dispatch resumes after a partial. Never mutates the previous result." },
    "idempotency_key": { "type": "string", "minLength": 1, "maxLength": 255,
                         "description": "Derived from the run id and the step id. A repeat of the same logical step carries the same key; a new step never does." },
    "document":        { "$ref": "urn:agentic:core:document:0.1" },
    "criterion_ref":   { "type": "string", "minLength": 1,
                         "description": "Opaque handle. The criterion itself must never appear in this object." },
    "actor": {
      "type": "object", "additionalProperties": false,
      "required": ["subject", "delegation_chain"],
      "properties": {
        "subject": { "type": "string", "description": "Workload or user identity URI, e.g. user:corey, agent:partner-sre-bot, service:alerting, schedule:nightly-fault-sweep." },
        "delegation_chain": {
          "type": "array", "minItems": 1,
          "items": {
            "type": "object", "additionalProperties": false,
            "required": ["actor", "obtained_via"],
            "properties": {
              "actor":        { "type": "string" },
              "obtained_via": { "enum": ["rfc8693_token_exchange", "workload_attestation", "direct"] }
            }
          },
          "description": "Token-exchange act-claim chain, oldest hop first. xc-identity-delegation owns the acyclicity rule."
        }
      }
    },
    "budget": {
      "type": "object", "additionalProperties": false,
      "required": ["ceiling_micros", "currency", "on_exceed"],
      "properties": {
        "ceiling_micros": { "type": "integer", "minimum": 0 },
        "currency":       { "type": "string", "pattern": "^[A-Z]{3}$" },
        "token_ceiling":  { "type": "integer", "minimum": 0 },
        "on_exceed":      { "const": "terminate_unit" }
      },
      "description": "on_exceed is a const, not an enum: exceeding terminates the unit, not the platform, and a caller cannot choose otherwise."
    },
    "deadline": {
      "type": "object", "additionalProperties": false,
      "required": ["not_after", "max_duration_s"],
      "properties": {
        "not_after":      { "type": "string", "format": "date-time" },
        "max_duration_s": { "type": "integer", "minimum": 1 },
        "cancel_grace_s": { "type": "integer", "minimum": 1, "default": 10 }
      }
    },
    "isolation": {
      "type": "object", "additionalProperties": false,
      "required": ["profile", "egress"],
      "properties": {
        "profile": { "type": "string", "description": "Named resource profile, resolved by the isolation adapter." },
        "egress":  { "enum": ["none", "allowlist"], "default": "none" },
        "egress_allowlist": { "type": "array", "items": { "type": "string" } },
        "credentials": { "const": "broker_only",
                         "description": "No real secret enters the unit. The unit reaches a broker that holds the key." }
      },
      "allOf": [{ "if":   { "properties": { "egress": { "const": "allowlist" } } },
                  "then": { "required": ["egress_allowlist"] } }]
    },
    "capabilities": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "tool_endpoints": { "type": "array", "items": { "type": "string", "format": "uri" },
                            "description": "Tool servers, per the tool-access standard cap-tool-access owns (version unverified)." },
        "skills":         { "type": "array", "items": { "type": "string" },
                            "description": "Capability packages by name, per the packaging standard cap-capability-packaging owns (version unverified)." }
      }
    },
    "context": { "$ref": "urn:agentic:dispatch:context:0.1" },
    "correlation": {
      "type": "object", "additionalProperties": false,
      "required": ["run_id", "root_dispatch_id"],
      "properties": {
        "run_id":            { "type": "string" },
        "root_dispatch_id":  { "type": "string", "format": "uuid" },
        "parent_dispatch_id":{ "type": "string", "format": "uuid" },
        "depth":             { "type": "integer", "minimum": 0 }
      },
      "description": "Emitted as resource attributes at dispatch. Correlation must not depend on trace-parent propagation."
    }
  }
}
```

## DispatchResult, in full

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:result:0.1",
  "title": "DispatchResult",
  "type": "object",
  "additionalProperties": false,
  "required": ["dispatch_id", "state", "stop_reason", "started_at", "ended_at",
               "partial", "outputs", "usage", "correlation"],
  "properties": {
    "dispatch_id": { "type": "string", "format": "uuid" },
    "state": {
      "enum": ["submitted", "working", "input-required", "auth-required",
               "completed", "canceled", "rejected", "failed"],
      "description": "Adopted task lifecycle. Terminal states are completed, canceled, rejected, failed."
    },
    "stop_reason": {
      "enum": ["end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled",
               "budget_exhausted", "deadline_exceeded", "policy_denied", "cancel_timeout",
               "adapter_unavailable"],
      "description": "First five adopted from the published stop-reason vocabulary (claimed, version unverified). The last five are the endings the platform itself can cause."
    },
    "started_at": { "type": "string", "format": "date-time" },
    "ended_at":   { "type": "string", "format": "date-time" },
    "partial":    { "type": "boolean",
                    "description": "True whenever state is not 'completed' and outputs is non-empty. Derived, never set by the executor." },
    "outputs": {
      "type": "array",
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["digest", "media_type", "recorded_at_head"],
        "properties": {
          "digest":     { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
          "media_type": { "type": "string" },
          "inline":     { "type": "string", "contentEncoding": "base64" },
          "ref":        { "type": "string", "format": "uri" },
          "recorded_at_head": { "type": "string",
                                "description": "State-seam head digest at which this output became durable." }
        }
      }
    },
    "usage": {
      "type": "object", "additionalProperties": false,
      "required": ["cost_micros", "currency", "wall_ms"],
      "properties": {
        "cost_micros":   { "type": "integer", "minimum": 0 },
        "currency":      { "type": "string", "pattern": "^[A-Z]{3}$" },
        "tokens_in":     { "type": "integer", "minimum": 0 },
        "tokens_out":    { "type": "integer", "minimum": 0 },
        "wall_ms":       { "type": "integer", "minimum": 0 },
        "metered_calls": { "type": "integer", "minimum": 0 }
      }
    },
    "step": { "$ref": "urn:agentic:dispatch:step:0.1" },
    "folded": { "$ref": "urn:agentic:dispatch:context:0.1#/$defs/folded" },
    "attestation_ref": { "type": "string",
                         "description": "Signed statement describing this result; xc-provenance-chain owns the envelope and the orphan rule (versions unverified)." },
    "correlation":     { "$ref": "urn:agentic:dispatch:request:0.1#/properties/correlation" },
    "problem":         { "$ref": "urn:agentic:problem:0.1" }
  },
  "allOf": [
    { "if":   { "properties": { "state": { "enum": ["failed", "rejected"] } }, "required": ["state"] },
      "then": { "required": ["problem"] } },
    { "if":   { "properties": { "state": { "const": "completed" } }, "required": ["state"] },
      "then": { "properties": { "partial": { "const": false } } } }
  ]
}
```

## The failure body

`cap-errors` owns the problem object and the closed type registry; this seam names rows, it does not
add them. The ten registered suffixes and their statuses live in `docs/decomposition.md` section
2.1.6 and are read from there by `tools/validate_skills.py`, so there is no second copy to drift.

The rows a dispatch raises, and the stop reason each pairs with:

| Registered type suffix | Raised by this seam when | Paired stop reason |
|---|---|---|
| `document-invalid` | the request or its document fails validation | none: the dispatch never started |
| `criterion-unresolvable` | the opaque criterion handle does not resolve | none: the dispatch never started |
| `identity-untrusted` | the delegation chain does not verify | none: the dispatch never started |
| `policy-denied` | a deterministic pre-execution refusal, carrying its rule id | `policy_denied` |
| `budget-exhausted` | a metered call would cross the declared ceiling | `budget_exhausted` |
| `deadline-exceeded` | the wall-clock ceiling was reached | `deadline_exceeded` |
| `cancel-timeout` | the grace window elapsed and the unit was destroyed | `cancel_timeout` |
| `isolation-unavailable` | no isolation adapter could admit the unit | `adapter_unavailable` |
| `adapter-unavailable` | a capability adapter is down, or a failure could not be typed | `adapter_unavailable` |
| `idempotency-conflict` | the same key arrived with a different request body | none: the repeat was refused |

Two rules keep this enforceable rather than decorative. `retryable` is a field, not an inference from
the status, so a 503 that is not retryable says so. And a failure an adapter cannot type is reported
against `adapter-unavailable` with the untyped payload in `detail` **and counted**; an adapter whose
untyped count is non-zero is not conformant, which is the assertion in this skill's definition of done.
