# Idempotency claim: full schemas, state machine, retention windows

Long material for `cap-idempotency`. Proposed: the skill body is enough to judge an
implementation; open this only when you are writing the store, the claim record, or the
retention policy. Every id here resolves with `python3 tools/kb.py show <id>`.

## 1. Full claim record (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:claim:0.1",
  "title": "IdempotencyClaim",
  "type": "object",
  "additionalProperties": false,
  "required": ["idempotency_key", "payload_digest", "scope", "claimed_at", "retention_s", "state"],
  "properties": {
    "idempotency_key": {
      "type": "string", "minLength": 8, "maxLength": 255,
      "description": "Supplied by the originator. A UUID or a similar random identifier is RECOMMENDED (X-cap-idempotency-005)."
    },
    "payload_digest": {
      "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "sha256 over the canonical bytes of the payload. The payload is never stored."
    },
    "scope": {
      "type": "string",
      "description": "The resource owner the key must be unique within; uniqueness MUST be defined by the resource owner (X-cap-idempotency-005)."
    },
    "state": { "enum": ["in_flight", "sealed", "released", "expired"] },
    "claimed_at": { "type": "string", "format": "date-time" },
    "sealed_at": { "type": ["string", "null"], "format": "date-time" },
    "retention_s": { "type": "integer", "minimum": 1 },
    "result_ref": {
      "type": ["string", "null"],
      "description": "Opaque reference to the first result. Never the result body; holding the key is not authorisation."
    },
    "fencing_token": {
      "type": "integer", "minimum": 0,
      "description": "Monotonic per scope. An append or seal carrying a lower token is rejected, so a claimant that paused and woke cannot seal over a newer one."
    },
    "entry_kind": {
      "type": "string",
      "description": "Recorded, never branched on. The claim behaves the same whichever entry point was used (T-t2-03)."
    },
    "correlation_id": {
      "type": "string",
      "description": "Explicit attribute, not inferred from trace parentage (agentic-stack, F-a7-02)."
    }
  }
}
```

## 2. Outcome state machine (proposed)

| From | Event | To | `claim` answers |
|---|---|---|---|
| absent | claim(key, digest) | in_flight | `fresh` |
| in_flight | claim(key, same digest) | in_flight | `duplicate`, `in_flight: true`, `result_ref` absent until sealed |
| in_flight | claim(key, different digest) | in_flight | `conflict` with a problem body |
| in_flight | complete(key, result_ref) | sealed | — |
| in_flight | execution failed, failure retryable | released | next claim answers `fresh` |
| in_flight | execution failed, failure not retryable | sealed | `duplicate` returning the same failure |
| sealed | claim(key, same digest) | sealed | `duplicate` with `result_ref` |
| sealed | claim(key, different digest) | sealed | `conflict` |
| sealed \| released | retention_s elapsed | expired | next claim answers `fresh` |

The `in_flight` duplicate is the row that a key without a lease cannot produce, and it is what
the P15 race criterion asserts on.

## 3. Published retention windows (claimed, from search-only records)

| Window | Record |
|---|---|
| 24 hours, "to balance deduplication coverage with storage costs" | `X-cap-idempotency-008`, `X-cap-idempotency-004` |
| 7 to 14 days after first submission | `X-cap-idempotency-008` |
| Unspecified by the convention itself; windows, parameter-mismatch behaviour and concurrency handling differ between providers | `X-cap-idempotency-007` |

None of these records was fetched; each is a search-result snippet. Treat every number here as
claimed and cite the record, not the vendor.

## 4. What a conforming implementation must show

Proposed checklist, in the order the checks get harder:

1. A sequential replay of the same key and payload returns the first answer and appends nothing.
2. The same key under a different payload digest returns the registered `idempotency-conflict`
   problem, not a second execution.
3. N concurrent claims of one key produce exactly one `fresh`; the rest are `duplicate`, and at
   least one of them carries `in_flight: true`.
4. After `retention_s`, the same key is claimable again and answers `fresh`.
5. The same conformance suite passes against a second adapter selected by configuration alone.
