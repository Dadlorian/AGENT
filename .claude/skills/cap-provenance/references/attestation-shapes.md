# Attestation shapes (long material)

Proposed. Open this only when you need the full schemas or the field mapping; the skill body is
enough to judge an implementation without it. Every shape here is origin=proposed: the recorded
standards (`F-b3-12`) fix a document format, and the field sets below are our reading of it.

## 1. The three layers

| Layer | Owner | What a foreign verifier does with it |
|---|---|---|
| Envelope | the standard | Checks the signature over the Pre-Authentication Encoding of `payloadType` and `payload` (`X-cap-provenance-003`) |
| Statement | the standard | Reads `_type`, `subject[]` and `predicateType`; matches subject digests against the artifact (`X-cross-structure-050`) |
| Predicate | us, per type | Opaque unless the verifier knows the type; this is where everything of ours lives |

## 2. Statement (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:statement:0.1",
  "title": "Statement",
  "type": "object",
  "additionalProperties": false,
  "required": ["_type", "subject", "predicateType", "predicate"],
  "properties": {
    "_type": { "const": "https://in-toto.io/Statement/v1" },
    "subject": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "digest"],
        "additionalProperties": false,
        "properties": {
          "name": { "type": "string", "description": "Stable identifier, never a path or a URL." },
          "digest": {
            "type": "object",
            "required": ["sha256"],
            "properties": { "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" } }
          }
        }
      }
    },
    "predicateType": { "type": "string", "format": "uri" },
    "predicate": { "type": "object" }
  }
}
```

## 3. Build-shaped predicate: field mapping (proposed)

The established model binds builder, recipe, materials and subject (`X-cross-structure-051`). Each
column names what the platform already records, so nothing here is a new thing to collect.

| Predicate field | Filled from | Concern half it discharges |
|---|---|---|
| `builder.id` | the workload identity of the executing unit | actor |
| `buildType` | the workflow identifier | inputs |
| `invocation.configSource` | the code version and tree hash under test | code version |
| `invocation.parameters` | the resolved configuration, not the declared file | code version |
| `resolvedDependencies` | the digest of every input document and prior step result | inputs |
| `subject[].digest` | the digest of the output the statement is about | the thing attested |

## 4. Agent-action predicate (proposed, no standard behind it)

Full schema is in the skill body under `contract.shapes`. Two notes that do not fit there:

- `decision_refs` carries the policy and budget decision record ids, so a reader can ask why the
  action was permitted without the predicate restating the rule. The criterion a result is judged
  against never appears here (design rule 6, stated in `agentic-stack`).
- `tool` names a class, never a vendor, matching how callers request model classes elsewhere in the
  platform.

## 5. Trust policy (proposed)

What `verify` is given, and what an outside verifier is given instead of it:

| Field | Meaning | Available to an outside verifier? |
|---|---|---|
| `accepted_signers` | identities whose signatures count | yes, it is the verifier's own input |
| `expected_builder_id` | the unit expected to have produced the subject | yes |
| `expected_source` | the repository or workflow expected to be named | yes |
| `require_log_inclusion` | whether an inclusion proof must accompany the envelope | yes, where the store is a log |

Nothing in this table reads our evidence store. That is the point of the P11 criterion running with
the store unmounted.
