# Lease placement — long material

Proposed throughout unless a row cites a knowledge-base id. Open this only when you need the full
schema, the per-entry derivation table, the attach state machine, or the worked envelopes in full.
The skill body is enough to wire the guarantee and to judge an implementation without this file.

Resolve every id here with `python3 tools/kb.py show <id>`.

## 1. Full IdempotencyLease schema (proposed)

The summary shape in the skill body carries the required members. This is the whole object,
including the members a store needs but a reader of the contract does not.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:idempotency:lease:0.1",
  "title": "IdempotencyLease",
  "type": "object",
  "additionalProperties": false,
  "required": ["key", "scope", "derivation", "payload_digest", "owner",
               "acquired_at", "expires_at", "fencing_token", "state"],
  "properties": {
    "key":            { "type": "string", "minLength": 8, "maxLength": 255 },
    "scope":          { "type": "string", "minLength": 1,
                        "description": "The boundary within which the key must be unique. Published per boundary." },
    "derivation":     { "enum": ["caller_supplied", "payload_fingerprint"] },
    "fingerprint_fields": { "type": "array", "items": { "type": "string" }, "minItems": 1,
                        "description": "JSON pointers into the envelope, in declared order. Required when derivation is payload_fingerprint." },
    "payload_digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "owner":          { "type": "string", "description": "The executing unit, not the entering actor." },
    "acquired_at":    { "type": "string", "format": "date-time" },
    "expires_at":     { "type": "string", "format": "date-time" },
    "renewed_at":     { "type": "string", "format": "date-time" },
    "fencing_token":  { "type": "integer", "minimum": 1 },
    "state":          { "enum": ["held", "sealed", "reclaimed"] },
    "result_ref":     { "type": ["string", "null"] },
    "sealed_at":      { "type": "string", "format": "date-time" },
    "retention_s":    { "type": "integer", "minimum": 1,
                        "description": "How long a sealed lease keeps answering replayed. A different number from the lease duration." },
    "entry_adapter":  { "type": "string", "description": "Which entry adapter derived the key; recorded so a derivation change is attributable." },
    "correlation":    { "$ref": "urn:agentic:dispatch:request:0.1#/properties/correlation" }
  },
  "allOf": [
    { "if":   { "properties": { "derivation": { "const": "payload_fingerprint" } }, "required": ["derivation"] },
      "then": { "required": ["fingerprint_fields"] } },
    { "if":   { "properties": { "state": { "const": "sealed" } }, "required": ["state"] },
      "then": { "required": ["result_ref", "sealed_at", "retention_s"] } }
  ]
}
```

## 2. Key derivation per entry adapter (proposed)

The rule is stated per adapter and published beside it, per the skill body's instruction 2. The
draft the convention comes from already pairs a key with a fingerprint (`X-entry-composition-047`,
"An idempotency fingerprint MAY be used in conjunction with an idempotency key to determine the
uniqueness of a request."). Values below are the proposed first cut.

| Entry adapter | Protocol carries a key? | Derivation | Fields selected |
|---|---|---|---|
| A person acting through a chat or form surface | no, the surface mints one per submit | `caller_supplied` after the surface stamps it, so a double-click reuses it | — |
| An agent or external system submitting a task | usually, on the request header | `caller_supplied` | — |
| A webhook delivery from an internal or external producer | sometimes, as a delivery id that changes per redelivery | `payload_fingerprint` | the producer's own event id plus the fields that name the subject of the event |
| A recurrence firing | no | `payload_fingerprint` | the recurrence identifier plus the occurrence instant, so two firings of one occurrence share a key and two occurrences do not |
| A resumed step inside a run | no | `payload_fingerprint` | the run id, the step id and the attempt-invariant inputs of that step |

Two rules that keep the table honest. A delivery id that changes on redelivery is never the key on
its own, because the redelivery is exactly the case the lease exists for
(`X-entry-composition-002` records that the event specification standardises the delivery method and
its registration handshake, not the identity of the action). And nothing selected may be a value the
platform itself stamps at arrival, such as a receipt timestamp, because it moves on every copy.

## 3. Attach state machine (proposed)

States are the `state` member above; the arrows are the outcomes `acquire` returns.

| From | Event | To | Answer to the caller |
|---|---|---|---|
| — (no lease) | acquire | `held` | `granted` with owner, expiry, fencing token |
| `held` | acquire, same payload digest | `held` | `attached`, waits on the in-flight execution's result |
| `held` | acquire, different payload digest | `held` | `conflict`, the registered problem object |
| `held` | seal, current fencing token | `sealed` | ack |
| `held` | seal, stale fencing token | unchanged | refused: the lease was reclaimed under this owner |
| `held` | renew from owner before expiry | `held` | expiry moved forward |
| `held` | expiry passes unsealed | `reclaimed` | next acquire is `granted` with an incremented token |
| `sealed` | acquire, same payload digest, within retention | `sealed` | `replayed` with the result reference |
| `sealed` | acquire after retention elapsed | `held` | `granted`: replay safety for that key has ended, which is why retention is declared |

The two-writer case is the one to read twice: reclaim increments the fencing token, so the
previous owner returning from a pause is refused at seal rather than overwriting the result the
new owner produced.

## 4. The three ways in, worked in full (proposed)

Taken from the shared entry envelope in `examples/end-to-end/entries/`. Only the members this
guarantee reads are shown; the envelopes carry identity, correlation and budget as well.

**A human enters the system** (`T-t1-01`)

```json
{
  "in":  { "kind": "human",
           "actor": { "subject": "user:corey" },
           "idempotency_key": "human-checkout-500s-2026-09-03",
           "payload_digest": "sha256:11f2c0..." },
  "derivation": "caller_supplied",
  "out": { "outcome": "granted", "owner": "run-human-0001",
           "expires_at": "2026-09-03T09:27:00Z", "fencing_token": 1 }
}
```

**An agent enters the system** (`T-t1-02`), fifteen seconds later, same logical fault

```json
{
  "in":  { "kind": "external",
           "actor": { "subject": "agent:partner-sre-bot" },
           "idempotency_key": "partner-sre-bot-task-77c1a9",
           "payload_digest": "sha256:11f2c0..." },
  "derivation": "caller_supplied",
  "out": { "outcome": "attached", "attached_to": "run-human-0001",
           "in_flight": true, "result_ref": null }
}
```

The agent supplied its own key and still attached: the scope for this boundary is the payload
digest within the fault's subject, so two producers of one action meet on the same claim. A
boundary that scopes keys per submitting actor would have executed twice here, which is why the
scope is published per boundary rather than assumed.

**An internal or external event enters the system** (`T-t1-03`), after the first run sealed

```json
{
  "in":  { "kind": "event",
           "actor": { "subject": "service:alerting" },
           "idempotency_key": null,
           "payload_digest": "sha256:11f2c0..." },
  "derivation": "payload_fingerprint",
  "fingerprint_fields": ["payload.alert", "payload.service", "payload.route", "payload.window_hours"],
  "out": { "outcome": "replayed", "result_ref": "ledger://run-human-0001/result", "fencing_token": 1 }
}
```

**A recurrence fires**, the fourth entry of the consumption reference (`T-t6-02`), same shape

```json
{
  "in":  { "kind": "schedule",
           "actor": { "subject": "schedule:nightly-fault-sweep" },
           "idempotency_key": "nightly-fault-sweep-2026-09-03",
           "payload_digest": "sha256:9ac410..." },
  "derivation": "caller_supplied",
  "out": { "outcome": "granted", "owner": "run-schedule-0001",
           "expires_at": "2026-09-03T02:15:00Z", "fencing_token": 1 }
}
```

## 5. The rejection, in full (proposed)

`urn:agentic:problem:idempotency-conflict` is a registered row of the closed registry in
docs/decomposition.md section 2.1.6 (409, not retryable, "Same key, different request body"). No
new type is minted by this guarantee.

```json
{
  "type": "urn:agentic:problem:idempotency-conflict",
  "title": "Idempotency conflict",
  "status": 409,
  "detail": "key human-checkout-500s-2026-09-03 is held under payload digest sha256:11f2c0 and this request carries sha256:7d0ba4",
  "instance": "urn:agentic:lease:human-checkout-500s-2026-09-03",
  "retryable": false,
  "correlation": { "run_id": "run-human-0002", "correlation_id": "corr-human-0002", "depth": 0 }
}
```

`retryable` is false because re-sending the same body under the same key cannot succeed: the
caller must either send the original body or mint a new key. cap-errors owns the object, the media
type and the registry (`F-b4-07`, "Typed and machine-readable. Never parsed from prose").
