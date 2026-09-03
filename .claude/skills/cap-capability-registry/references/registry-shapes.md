# Capability registry - full shapes and standards table

Opened only when implementing the record schema, wiring the rollout members, or reviewing a published
record. The body of `cap-capability-registry` is enough to judge the interface and to call it without this
file. Every row is either sourced with a knowledge-base id and a verbatim quote, or marked proposed.
Resolve ids with `python3 tools/kb.py show <id>`.

## 1. Standards this interface names

| Standard | Version | Status | Evidence |
|---|---|---|---|
| Packaging format of the artifact a record names (`E-standard-agent-skills-spec`) | none published | unverified | `X-end-to-end-025` "Anthropic does not currently publish the skill format as an explicitly versioned artifact." — stated by `cap-capability-packaging`; the consequence here is that the record, not the package, carries the version. |
| Discovery-record specification for another party's agent (`E-standard-a2a-messaging`) | none read | unverified | `X-cap-capability-registry-006` "Agent Cards serve as a discovery mechanism" |
| Registry interface with semantic-version ordering | preview under an API freeze | unverified; no entity in this knowledge base (see the skill's first open question) | `X-cap-capability-registry-001` "The Registry API has entered an API freeze (v0.1)" |
| Content-addressed record schema with semantic versioning | none read | unverified; no entity in this knowledge base | `X-cap-capability-registry-003` "OASF records use semantic versioning to indicate the current version" |

No version above was fetched from its specification in this environment, so every one is recorded
unverified rather than guessed.

## 2. `capability-record` in full (proposed)

The summary shape in the skill body carries the required members. The members below are the optional ones
it omits; nothing here is required to resolve or to publish.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:record:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["namespace", "name", "version", "kind", "digest", "signature", "record_schema_version"],
  "properties": {
    "namespace": { "type": "string", "minLength": 1,
                   "description": "The publishing authority. Two records may share a name only across namespaces." },
    "name": { "type": "string", "minLength": 1 },
    "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:[-+][0-9A-Za-z.-]+)*$" },
    "kind": { "enum": ["capability", "agent"] },
    "digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                "description": "Of the artifact the record names, not of the record." },
    "signature": { "type": "string", "minLength": 1,
                   "description": "Over the canonical bytes of every member except this one." },
    "record_schema_version": { "type": "string", "minLength": 1 },
    "good_at": { "type": "array", "items": { "type": "string", "minLength": 20 },
                 "description": "Specific enough to sequence on (T-t6-05)." },
    "not_for": { "type": "string", "minLength": 10 },
    "model_class": { "type": "string", "pattern": "^(f|i|b|cli)-[a-z0-9-]*$",
                     "description": "A routing class, never a vendor (F-a4-01)." },
    "auth_schemes": { "type": "array", "items": { "type": "string" },
                      "description": "What a caller must satisfy to reach it (X-cap-capability-registry-006)." },
    "modalities": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "inputs": { "type": "array", "items": { "type": "string" } },
        "outputs": { "type": "array", "items": { "type": "string" } }
      }
    },
    "acceptance_criteria_ref": { "type": ["string", "null"], "default": null,
      "description": "An opaque identifier only the publisher and the improvement loop resolve. The criterion body never travels in a resolution outcome or a describe response (F-b1-07)." },
    "rollback_to": { "type": ["string", "null"], "default": null,
      "description": "The version this one is rolled back to. A rollback is a resolution that changes, never an edit." },
    "supersedes": { "type": ["string", "null"], "default": null },
    "published_at": { "type": "string", "format": "date-time" },
    "yanked": { "type": "boolean", "default": false,
      "description": "Excluded from constraint resolution; still resolvable by exact version, because a record is never deleted (X-cap-capability-registry-007)." }
  }
}
```

## 3. Rollout members (proposed)

A rollout record is separate from the capability record and is never returned to a resolving caller. It
exists because publication is staged: `X-end-to-end-026` "evaluate locally, gate in CI, canary in
production, then expand or roll back based on quality metrics".

| Member | Meaning |
|---|---|
| `record_id` | The candidate record being promoted. |
| `stage` | `evaluated`, `gated`, `canary`, `expanded` or `rolled-back`. |
| `share` | Fraction of resolutions the canary stage answers with the candidate. |
| `evaluated_against` | The acceptance criteria reference, resolved by the publisher only. |
| `outcome` | What the stage showed, as counts and not as prose. |
| `decided_by` | The actor that promoted or rolled back. |

## 4. Refusal members of `resolution-outcome` (proposed)

Every refusal is an RFC 9457 problem details object; `cap-errors` owns the shape and this interface adds
no vocabulary of its own beyond the four suffixes below.

| `type` suffix | Status | Retryable | Raised when |
|---|---|---|---|
| `record-unresolved` | 404 | no | No record carries that namespace and name. |
| `constraint-unsatisfiable` | 404 | no | The name resolves but no published version satisfies the constraint. |
| `record-unsigned` | 401 | no | The record carries no signature, or the signature does not verify. |
| `record-digest-mismatch` | 409 | no | The signature verifies but the digest does not match the artifact named. |

The last two are refusals, not warnings, on every adapter and under every configuration: that is what the
skill's definition of done breaks on purpose to prove the check can fail.
