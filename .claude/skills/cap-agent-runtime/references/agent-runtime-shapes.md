# Agent runtime: full shapes and the stop-reason table

Proposed material. The body of `cap-agent-runtime` is enough to judge a candidate runtime and to call
the capability; open this file when implementing or reviewing the shapes themselves.

Every schema here is JSON Schema 2020-12. Nothing in this file is sourced from PASS.md unless a kb id
is named on the line.

## 1. Session capabilities, negotiated at session open

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:session-capabilities:0.1",
  "title": "SessionCapabilities",
  "type": "object",
  "additionalProperties": false,
  "required": ["streaming_updates", "permission_callbacks", "cancellable_mid_turn"],
  "properties": {
    "streaming_updates":    { "type": "boolean", "default": false },
    "permission_callbacks": { "type": "boolean", "default": false },
    "cancellable_mid_turn": { "type": "boolean", "default": false },
    "cancel_floor_s": {
      "type": "number", "minimum": 0,
      "description": "Observed floor for reaching a terminal frame after cancel. cancel_grace_s must be at or above it."
    },
    "max_turn_requests_supported": { "type": "boolean", "default": false }
  }
}
```

Rule: every member defaults to `false`. A caller reads the negotiated set once and writes no branch
for a capability it did not get. A runtime that negotiates all three is the interactive case; one that
negotiates none is the single-shot case, and both serve the same interface.

## 2. Turn request

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:turn-request:0.1",
  "title": "TurnRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["session_id", "prompt", "cancel_grace_s", "correlation_id"],
  "properties": {
    "session_id": { "type": "string", "minLength": 1 },
    "prompt": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["kind", "content"],
        "properties": {
          "kind":       { "enum": ["text", "resource_ref", "prior_turn_digest"] },
          "content":    { "type": "string" },
          "media_type": { "type": "string" }
        }
      },
      "description": "Carries the task. Never the criterion the result is judged against (design rule 6, F-b1-07)."
    },
    "cancel_grace_s":    { "type": "integer", "minimum": 1, "default": 10 },
    "correlation_id":    { "type": "string", "minLength": 1 },
    "max_turn_requests": { "type": "integer", "minimum": 1 },
    "deadline":          { "type": "string", "format": "date-time" }
  }
}
```

`cancel_grace_s` is per request rather than global because each adapter has a different cancel floor.
The default of 10 is the substrate reference point plus headroom (F-a3-09, recorded status claimed).

## 3. Turn result

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:turn-result:0.1",
  "title": "TurnResult",
  "type": "object",
  "additionalProperties": false,
  "required": ["session_id", "stop_reason", "terminal", "frames_after_terminal", "usage", "correlation_id"],
  "properties": {
    "session_id":  { "type": "string", "minLength": 1 },
    "stop_reason": {
      "enum": ["end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled",
               "cancel_timeout", "adapter_unavailable"]
    },
    "terminal":              { "const": true },
    "frames_after_terminal": { "type": "integer", "minimum": 0, "maximum": 0 },
    "cancel_to_terminal_s":  { "type": "number", "minimum": 0 },
    "outputs": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["digest", "media_type"],
        "properties": {
          "digest":     { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
          "media_type": { "type": "string" },
          "ref":        { "type": "string", "format": "uri" }
        }
      }
    },
    "usage": {
      "type": "object",
      "additionalProperties": false,
      "required": ["wall_ms"],
      "properties": {
        "wall_ms":       { "type": "integer", "minimum": 0 },
        "tokens_in":     { "type": "integer", "minimum": 0 },
        "tokens_out":    { "type": "integer", "minimum": 0 },
        "metered_calls": { "type": "integer", "minimum": 0 }
      }
    },
    "correlation_id": { "type": "string", "minLength": 1 },
    "problem":        { "$ref": "urn:agentic:problem:0.1" }
  },
  "allOf": [
    { "if":   { "properties": { "stop_reason": { "enum": ["cancel_timeout", "adapter_unavailable", "refusal"] } },
                "required": ["stop_reason"] },
      "then": { "required": ["problem"] } }
  ]
}
```

`frames_after_terminal` is capped at 0 in the schema rather than merely described, so a conformance
run asserts on a member instead of on a sentence.

## 4. Stop-reason table

| Value | Origin | Terminal state means | Carries a problem |
|---|---|---|---|
| `end_turn` | protocol (proposed: read from a design note, not the specification) | the agent finished its turn | no |
| `max_tokens` | protocol (same caveat) | a token ceiling ended the turn | no |
| `max_turn_requests` | protocol (same caveat) | the per-turn request ceiling was reached | no |
| `refusal` | protocol (same caveat) | the agent declined the prompt | yes |
| `cancelled` | protocol (same caveat) | cancel was honoured inside the grace window | no |
| `cancel_timeout` | ours (proposed) | the grace window expired and the unit was hard-stopped | yes |
| `adapter_unavailable` | ours (proposed) | the runtime could not be reached or could not type its own failure | yes |

Three further reasons - budget exhaustion, deadline expiry and policy denial - belong to the dispatch
seam above this capability, not to the runtime: they are decided by a ceiling outside the unit, and a
runtime that reported them would be enforcing a guarantee it is not the enforcement point for.

## 5. Conformance report emitted by the definition of done

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["adapters_run", "per_adapter"],
  "properties": {
    "adapters_run": { "type": "integer", "minimum": 2 },
    "per_adapter": {
      "type": "array", "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["adapter", "op_seconds", "cancel_at_s", "grace_s",
                     "cancel_to_terminal_s", "stop_reason", "frames_after_terminal"],
        "properties": {
          "adapter":               { "type": "string", "description": "Adapter entity id, so a failure names one implementation." },
          "op_seconds":            { "type": "integer", "minimum": 1 },
          "cancel_at_s":           { "type": "integer", "minimum": 0 },
          "grace_s":               { "type": "integer", "minimum": 1 },
          "cancel_to_terminal_s":  { "type": "number",  "minimum": 0 },
          "stop_reason":           { "type": "string" },
          "frames_after_terminal": { "type": "integer", "minimum": 0 },
          "negotiated":            { "$ref": "urn:agentic:cap:agent-runtime:session-capabilities:0.1" }
        }
      }
    }
  }
}
```

`negotiated` is included so the run records what the session actually agreed to, not what it asked
for (F-a7-04).
