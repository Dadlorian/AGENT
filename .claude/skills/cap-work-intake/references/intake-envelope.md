# Work intake: the full envelope, the per-producer mapping, and the equivalence fixtures

Proposed material. The `cap-work-intake` skill body is enough to judge an intake implementation
without this file; open it when you are writing a producer mapper, publishing the envelope schema,
or building the equivalence fixture corpus the definition of done runs over.

Every shape below is **proposed** unless a row says otherwise. PASS.md fixes only the capability row
(`F-b3-08`): the standards, the adapters today, and the swap candidate.

---

## 1. The full entry envelope

A worked instance of this shape, with all four producer kinds filled in, is in
`examples/end-to-end/schemas/entry.schema.json` and `examples/end-to-end/entries/`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:envelope:0.1",
  "title": "EntryEnvelope",
  "type": "object",
  "additionalProperties": false,
  "required": ["envelope_version", "kind", "entry_id", "occurred_at", "actor",
               "intent", "correlation", "budget", "idempotency_key", "payload"],
  "properties": {
    "envelope_version": { "const": "0.1" },
    "kind": { "enum": ["human", "event", "schedule", "external"] },
    "entry_id": { "type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,63}$" },
    "occurred_at": { "type": "string", "format": "date-time" },
    "actor": {
      "type": "object", "additionalProperties": false,
      "required": ["subject", "delegation_chain"],
      "properties": {
        "subject": { "type": "string", "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$" },
        "delegation_chain": {
          "type": "array", "minItems": 1,
          "items": {
            "type": "object", "additionalProperties": false,
            "required": ["actor", "obtained_via"],
            "properties": {
              "actor": { "type": "string" },
              "obtained_via": { "enum": ["direct", "token_exchange", "workload_attestation"] }
            }
          }
        }
      }
    },
    "intent": {
      "type": "object", "additionalProperties": false,
      "required": ["workflow_ref", "summary"],
      "properties": {
        "workflow_ref": { "type": "string", "minLength": 1 },
        "document_ref": { "type": "string" },
        "criterion_ref": { "type": "string",
          "description": "Opaque handle only. The criterion text must never appear in this envelope." },
        "summary": { "type": "string", "minLength": 1, "maxLength": 400 }
      }
    },
    "correlation": {
      "type": "object", "additionalProperties": false,
      "required": ["run_id", "correlation_id"],
      "properties": {
        "run_id": { "type": "string", "minLength": 1 },
        "correlation_id": { "type": "string", "minLength": 1 },
        "parent_correlation_id": { "type": "string" },
        "depth": { "type": "integer", "minimum": 0 }
      }
    },
    "budget": {
      "type": "object", "additionalProperties": false,
      "required": ["ceiling_micros", "currency", "on_exceed"],
      "properties": {
        "ceiling_micros": { "type": "integer", "minimum": 0 },
        "currency": { "type": "string", "pattern": "^[A-Z]{3}$" },
        "on_exceed": { "const": "terminate_unit" }
      }
    },
    "idempotency_key": { "type": "string", "minLength": 8, "maxLength": 255 },
    "payload": { "type": "object" }
  }
}
```

Notes that are easy to lose:

- `on_exceed` is a `const`, not an `enum`. A producer cannot express an opt-out.
- `criterion_ref` is a handle. Design rule 6 (`F-b1-07`) is what forbids the text.
- `payload` has no declared properties on purpose. Anything routing needs is mapped up into the
  envelope by the producer's mapper.

---

## 2. Per-producer mapping table

Each row says where the envelope's identity fields come from, so that no adapter invents them.

| Envelope field | Request-pushed event producer | Agent-message producer | Repository event | Schedule occurrence | Command line |
|---|---|---|---|---|---|
| `kind` | `event` or `human`, per the producer's declared role | `external` | `event` | `schedule` | `human` |
| `entry_id` | derived from the event `source` + `id` pair | derived from the message id | derived from repository + delivery id | derived from unit ref + occurrence instant | derived from invocation nonce |
| `occurred_at` | event `time` | message send time | hook `created_at` | the occurrence instant, not the firing instant | invocation time |
| `actor.subject` | the authenticated caller | the submitting agent's workload identity | the service that owns the hook | `schedule:<unit>` | the signed-in user |
| `actor.delegation_chain` | one hop, or the exchanged chain | attested agent hop, then the exchange, then the human origin | attested service hop, then exchange | the declaring actor's chain | one direct hop |
| `intent.workflow_ref` | event `type` mapped through the routing table | the task type mapped through the routing table | hook event name mapped | the unit the schedule is declared on | the named command |
| `correlation.run_id` | minted at intake | minted at intake | minted at intake | minted at intake | minted at intake |
| `correlation.parent_correlation_id` | absent | the submitting agent's own correlation, when it sends one | absent | absent | absent |
| `idempotency_key` | `source` + `id` | message id | delivery id | unit ref + occurrence instant | invocation nonce |
| `payload` | the event `data` member, unread | the message parts, unread | the hook body, unread | the declaration's parameters | the parsed arguments |

The rule the table encodes: **only `correlation.run_id` is minted by intake.** Everything that
identifies the submission comes from the producer, because the producer is the only party that knows
whether two submissions are the same act.

---

## 3. The equivalence fixture corpus

`fixtures/intake/one-job.json` holds one logical job expressed once, plus the three producer-native
renderings of it. The conformance runner feeds each rendering to its adapter and compares.

| Fixture | What it varies | What must stay equal | What must differ |
|---|---|---|---|
| `one-job` | producer only | `job_digest` | `entry_id`, `idempotency_key`, `actor.subject` |
| `one-job-retried` | the same producer sends twice | `job_digest`, `idempotency_key` | nothing; the second is a no-op with `duplicate_of` set |
| `two-jobs-one-producer` | payload differs by one character | nothing | `job_digest` |
| `same-job-different-summary` | `intent.summary` reworded | nothing | `job_digest`, deliberately: the summary is part of the job |
| `producer-stamps-a-field` | one adapter adds `priority` | nothing | `job_digest`; this is the definition-of-done breakage |
| `missing-actor` | actor omitted | — | refused with problem type `document-invalid`, nothing admitted |
| `criterion-in-payload` | the definition of done pasted into `payload` | — | refused: the grader rule is checked at intake, not assumed |

`distinct_job_digests`, `distinct_entry_ids`, `invalid` and `adapters_run` are the four counters the
report carries. A report where `adapters_run` is 1 has measured normalisation and not swappability.

---

## 4. Refusals a producer can get

All are problem details from the registry `cap-errors` owns; intake defines no failure format of its
own.

| Problem type | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The normalised envelope fails the schema; the offending JSON Pointer is named in `detail` |
| `urn:agentic:problem:unknown-producer-format` | 415 | The declared format has no mapper registered |
| `urn:agentic:problem:idempotency-conflict` | 409 | The same key arrived with a different job digest |
| `urn:agentic:problem:policy-denied` | 403 | A rule refused this actor or this workflow reference before anything was admitted |

A refusal names the field. Intake is where most producer mistakes surface, and a refusal a producer
cannot act on turns every new integration into a conversation.
