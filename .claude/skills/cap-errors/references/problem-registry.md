# Problem shape and closed type registry

Reference material for `cap-errors`. The skill body is enough to judge an implementation; open this
file when you need the full schema, the registry rows, or the extension members a given type declares.

Everything here is **proposed** and is transcribed from `docs/decomposition.md` section 2.1.6, which is
this repository's first-cut design for what a Dispatch failure returns. Nothing in this file is a quote
from PASS.md. The governing standard is cited in the skill body (`E-standard-rfc-9457-problem-details`,
version unverified).

## 1. Full Problem schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:0.1",
  "title": "Problem",
  "type": "object",
  "required": ["type", "title", "status"],
  "properties": {
    "type":     { "type": "string", "format": "uri",
                  "description": "Must be a member of the type registry below. Unregistered types are a conformance failure." },
    "title":    { "type": "string" },
    "status":   { "type": "integer", "minimum": 100, "maximum": 599 },
    "detail":   { "type": "string" },
    "instance": { "type": "string", "format": "uri" },
    "dispatch_id": { "type": "string", "format": "uuid" },
    "stop_reason": { "$ref": "urn:agentic:dispatch:result:0.1#/properties/stop_reason" },
    "retryable":   { "type": "boolean" },
    "retry_after_s": { "type": "integer", "minimum": 0 },
    "rule_id":     { "type": "string", "description": "Set when type is policy-denied." },
    "correlation": { "$ref": "urn:agentic:dispatch:request:0.1#/properties/correlation" },
    "causes":      { "type": "array", "items": { "$ref": "urn:agentic:problem:0.1" },
                     "description": "Delegated failure chain, innermost last." }
  }
}
```

## 2. The closed type registry

Closed at authoring time and extended only by adding a row to `docs/decomposition.md` section 2.1.6
first. Every suffix below is prefixed with `urn:agentic:problem:`.

| Type suffix | Status | Retryable | Raised when | Declared extension members |
|---|---|---|---|---|
| `document-invalid` | 422 | no | The document fails JSON Schema 2020-12 validation | `causes` (one per offending field) |
| `criterion-unresolvable` | 422 | no | `criterion_ref` does not resolve | — |
| `identity-untrusted` | 401 | no | The delegation chain does not verify | — |
| `policy-denied` | 403 | no | A deterministic pre-execution refusal | `rule_id` |
| `budget-exhausted` | 402 | no | A metered call would cross the ceiling | `stop_reason` |
| `deadline-exceeded` | 504 | yes | Wall clock ceiling reached | `retry_after_s` |
| `cancel-timeout` | 500 | no | Grace window elapsed, unit destroyed | `stop_reason` |
| `isolation-unavailable` | 503 | yes | No isolation adapter could admit the unit | `retry_after_s` |
| `adapter-unavailable` | 503 | yes | A capability adapter is down, or raised a failure it could not type | `retry_after_s` |
| `idempotency-conflict` | 409 | no | Same key, different request body | — |

## 3. The two rules that make the registry enforceable

1. `retryable` is a member, not an inference from status. A 503 that is not retryable must say so.
2. A failure that cannot be typed is itself a conformance failure of the adapter. It is reported as
   `adapter-unavailable` with the untyped payload in `detail`, and it is counted. An adapter whose
   untyped-failure count is non-zero is not conformant.

## 4. Naming note

The skill manifest's fold-in for this item names `budget-exceeded`, `cancelled`, `timeout`,
`schema-invalid` and `partial-result`. Those are the same concerns as `budget-exhausted`,
`cancel-timeout`, `deadline-exceeded` and `document-invalid` above, except `partial-result`, which is
not a failure: a partial result returns through the Dispatch result shape with `partial: true`, not
through a problem body. The registry spelling is normative until a row edit in
`docs/decomposition.md` section 2.1.6 says otherwise. See this skill's second open question.
