# xc-compensation: full shapes and worked entries

Proposed throughout. The body of `SKILL.md` is enough to wire the guarantee and to judge an
implementation of it; this file exists so the long material does not sit in the skill body.
Open it when you need the full record schema, the class table, the unwind report, or the four
entry envelopes in full.

## 1. The three irreversibility classes

| Class | What it means | What the platform does before the effect | What an unwind does |
|---|---|---|---|
| `reversible` | A later run re-derives the same state; nothing outside the platform changed | records the declaration | marks the record `not-required` |
| `compensable` | Something outside the platform changed and a logical inverse exists | records the declaration and the compensating action as a step of its own | runs that step under its own key |
| `irreversible` | Nothing that exists can take the effect back | requires a mandate reference, and where a person owns the decision an approval | marks the record `unwind-failed` and reports it; there is no inverse to run |

There is no fourth class and no default. An effect-committing step that declares none is refused
before the run starts with the registered `urn:agentic:problem:document-invalid`.

## 2. CompensationRecord, in full

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:record:0.1",
  "title": "CompensationRecord",
  "type": "object",
  "additionalProperties": false,
  "required": ["run_id", "step_id", "effect_digest", "irreversibility",
               "idempotency_key", "declared_at_head", "state"],
  "properties": {
    "run_id":        { "type": "string" },
    "step_id":       { "type": "string" },
    "parent_step_id": { "type": ["string", "null"],
                        "description": "Set when the effect was committed by a sub-unit, so the reverse walk covers the whole structure and not only the outermost run." },
    "effect_digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "effect_operator": { "type": "string" },
    "irreversibility": { "enum": ["reversible", "compensable", "irreversible"] },
    "compensating_action": {
      "type": "object",
      "additionalProperties": false,
      "required": ["operator", "input_ref", "idempotency_key"],
      "properties": {
        "operator":        { "type": "string" },
        "input_ref":       { "type": "string",
                             "description": "A reference into the forward step's recorded output, resolved at unwind time, never a copy of it." },
        "idempotency_key": { "type": "string", "minLength": 1, "maxLength": 255 },
        "timeout_s":       { "type": "integer", "minimum": 1 }
      }
    },
    "mandate_ref":      { "type": ["string", "null"] },
    "idempotency_key":  { "type": "string", "minLength": 1, "maxLength": 255 },
    "declared_at_head": { "type": "string" },
    "committed_at_head": { "type": ["string", "null"] },
    "sealed_response_ref": { "type": ["string", "null"] },
    "compensated_at_head": { "type": ["string", "null"] },
    "state": { "enum": ["declared", "committed", "compensated", "not-required", "unwind-failed"] },
    "actor": { "type": "object",
               "description": "The entering actor and its delegation chain, carried so a reclaimed or failed unwind can be attributed. cap-identity owns the shape." },
    "correlation": { "type": "object",
                     "description": "run id and correlation id as explicit attributes, never inferred from parentage." }
  },
  "allOf": [
    { "if":   { "properties": { "irreversibility": { "const": "compensable" } },
                "required": ["irreversibility"] },
      "then": { "required": ["compensating_action"] } },
    { "if":   { "properties": { "irreversibility": { "const": "irreversible" } },
                "required": ["irreversibility"] },
      "then": { "required": ["mandate_ref"] } }
  ]
}
```

## 3. UnwindReport

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:unwind-report:0.1",
  "title": "UnwindReport",
  "type": "object",
  "additionalProperties": false,
  "required": ["run_id", "reason", "records", "outcome"],
  "properties": {
    "run_id": { "type": "string" },
    "reason": { "enum": ["failed", "cancelled", "refused-after-the-fact"] },
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["step_id", "irreversibility", "outcome"],
        "properties": {
          "step_id":         { "type": "string" },
          "irreversibility": { "enum": ["reversible", "compensable", "irreversible"] },
          "outcome":         { "enum": ["replayed", "compensated", "not-required", "unwind-failed"] },
          "problem":         { "$ref": "urn:agentic:problem:0.1" }
        }
      },
      "description": "In reverse order of commitment, which is the order they were run in."
    },
    "outcome": { "enum": ["unwound", "partially-unwound"] }
  }
}
```

`partially-unwound` is the honest outcome whenever any record is `unwind-failed`, including every
`irreversible` record the run committed. It is reported as
`urn:agentic:problem:compensation-unresolved`, which is proposed and pending registration in
docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an
implementation returns the registered `adapter-unavailable`, which is also 503 and retryable, with
one entry per unwound-failed record in `causes`.

## 4. The four entries, in full

The envelopes are the ones in `examples/end-to-end/entries/`. Compensation adds nothing to them:
what it adds is per step, inside the workflow the envelope names. cap-consumption fixes the caller
doctrine all four share.

```json
[
  { "way_in": "human",
    "actor": { "subject": "user:corey",
               "delegation_chain": [{ "actor": "user:corey", "obtained_via": "direct" }] },
    "step": { "id": "refund-the-coupon-charge",
              "operator": "payments.refund",
              "irreversibility": "compensable",
              "compensating_action": { "operator": "payments.void",
                                       "input_ref": "step.out.charge_id",
                                       "idempotency_key": "human-checkout-500s-2026-09-03/comp/3",
                                       "timeout_s": 30 } },
    "recorded": { "declared_at_head": "sha256:4c1a90", "committed_at_head": "sha256:4c1a91",
                  "state": "committed" } },

  { "way_in": "external system or agent",
    "actor": { "subject": "agent:partner-sre-bot",
               "delegation_chain": [{ "actor": "agent:partner-sre-bot", "obtained_via": "workload_attestation" },
                                    { "actor": "service:intake", "obtained_via": "token_exchange" }] },
    "step": { "id": "post-the-status-update",
              "operator": "statuspage.publish",
              "irreversibility": "irreversible",
              "mandate_ref": "mandate:status-page:2026-09-03" },
    "recorded": { "declared_at_head": "sha256:4c1a94", "committed_at_head": "sha256:4c1a95",
                  "state": "committed",
                  "note": "No compensating action exists for this class. The gate ran before the effect." } },

  { "way_in": "event",
    "actor": { "subject": "service:alerting",
               "delegation_chain": [{ "actor": "service:alerting", "obtained_via": "workload_attestation" }] },
    "step": { "id": "open-the-incident-ticket",
              "operator": "tickets.open",
              "irreversibility": "compensable",
              "compensating_action": { "operator": "tickets.close",
                                       "input_ref": "step.out.ticket_id",
                                       "idempotency_key": "alert-8f31c0-checkout-500s/comp/1",
                                       "timeout_s": 30 } },
    "recorded": { "state": "compensated", "unwind_reason": "failed",
                  "compensated_at_head": "sha256:4c1aa7" } },

  { "way_in": "schedule",
    "actor": { "subject": "schedule:nightly-fault-sweep",
               "delegation_chain": [{ "actor": "schedule:nightly-fault-sweep", "obtained_via": "workload_attestation" }] },
    "step": { "id": "write-the-sweep-report",
              "operator": "reports.write",
              "irreversibility": "reversible" },
    "recorded": { "state": "not-required", "unwind_reason": "cancelled" } }
]
```

## 5. The refusals, in full

```json
[
  { "type": "urn:agentic:problem:document-invalid", "title": "Document invalid", "status": 422,
    "detail": "step 3 'payments.charge' commits an effect and declares no irreversibility class; there is no default",
    "retryable": false,
    "correlation": { "run_id": "run-human-0001", "correlation_id": "corr-human-0001", "depth": 0 } },

  { "type": "urn:agentic:problem:policy-denied", "title": "Policy denied", "status": 403,
    "rule_id": "compensation.irreversible-requires-mandate",
    "detail": "step 5 'email.send' is declared irreversible and carries no mandate_ref; nothing can unwind it",
    "retryable": false,
    "correlation": { "run_id": "run-event-0001", "correlation_id": "corr-event-0001", "depth": 0 } }
]
```
