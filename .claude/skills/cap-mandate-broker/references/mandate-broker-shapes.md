# Mandate broker: full shapes and bounds vocabulary

Proposed throughout. Open this only when implementing the mint request, the mandate record or the
verification outcome. The body of `cap-mandate-broker` is enough to judge the interface and to call it
without this file.

Every claim here is proposed design unless it names a knowledge-base id. Ids resolve with
`python3 tools/kb.py show <id>`.

## 1. mint request (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:mandate-broker:mint-request:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["actor", "delegation_chain", "audience", "scope", "lifetime_seconds", "correlation_id"],
  "properties": {
    "actor": {"type": "string", "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$"},
    "delegation_chain": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["actor", "obtained_via"],
        "properties": {
          "actor": {"type": "string"},
          "obtained_via": {"enum": ["direct", "token_exchange", "workload_attestation"]}
        }
      }
    },
    "audience": {"type": "string", "minLength": 1},
    "scope": {"type": "array", "items": {"type": "string", "minLength": 1}},
    "lifetime_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
    "mandate_ref": {"type": ["string", "null"], "default": null},
    "correlation_id": {"type": "string", "minLength": 1}
  }
}
```

Notes (proposed):

- `audience` is one string, not an array. A list would make replay across destinations a configuration
  choice rather than an impossibility.
- `lifetime_seconds` has an upper bound in the schema so a long-lived credential cannot be requested by a
  caller that has simply asked for a very large number.
- `mandate_ref` is present only when the credential is being minted to carry out an action already bounded
  by a mandate. It names the mandate; it never inlines its bounds.
- The delegation chain member reuses the `obtained_via` vocabulary the reference entry envelope in
  `examples/end-to-end/schemas/entry.schema.json` already fixes, so an entry and a mint agree on how an
  actor came to be acting.

## 2. mandate record: bounds vocabulary (proposed)

| Bound | Applies to action class | Meaning | Refusal type when violated |
|---|---|---|---|
| `ceiling_micros` + `currency` | spend | Total that may be spent under this mandate | `urn:agentic:problem:mandate-ceiling-exceeded` |
| `destinations` | spend, deploy, send | The destination identifiers the mandate may be used against | `urn:agentic:problem:mandate-destination-out-of-bounds` |
| `not_before` / `not_after` | all | The period the authority is valid for | `urn:agentic:problem:mandate-expired` |
| `max_actions` | all | How many times the mandate may be exercised | `urn:agentic:problem:mandate-exhausted` |
| `environment` | deploy | Which environment a deploy may land in | `urn:agentic:problem:mandate-destination-out-of-bounds` |

`action_class` is closed to `spend`, `deploy` and `send` (proposed). Anything that is not irreversible is a
scoped credential, not a mandate: minting one is cheap and expiring, and a mandate is a record someone has
to be able to review months later.

## 3. verification outcome (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:mandate-broker:verification:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["mandate_id", "action", "accepted", "checks", "verifier"],
  "properties": {
    "mandate_id": {"type": "string", "minLength": 8},
    "action": {
      "type": "object",
      "additionalProperties": false,
      "required": ["action_class", "destination"],
      "properties": {
        "action_class": {"enum": ["spend", "deploy", "send"]},
        "destination": {"type": "string", "minLength": 1},
        "amount_micros": {"type": "integer", "minimum": 0},
        "currency": {"type": "string", "pattern": "^[A-Z]{3}$"}
      }
    },
    "accepted": {"type": "boolean"},
    "checks": {
      "type": "object",
      "additionalProperties": false,
      "required": ["signature_verified", "within_validity", "within_bounds"],
      "properties": {
        "signature_verified": {"type": "boolean"},
        "within_validity": {"type": "boolean"},
        "within_bounds": {"type": "boolean"}
      }
    },
    "verifier": {
      "type": "object",
      "additionalProperties": false,
      "required": ["is_issuer", "contacted_issuer"],
      "properties": {
        "is_issuer": {"const": false},
        "contacted_issuer": {"const": false}
      }
    },
    "problem": {"type": ["object", "null"], "default": null}
  }
}
```

The `verifier` member is two constants on purpose (proposed): the conformance run asserts that the
verification that passed was performed by a party that did not issue the mandate and did not reach the
issuer, which is the property `X-cap-mandate-broker-005` records — "verification doesn't depend on
contacting the issuer".

## 4. Refusal types (proposed)

All refusals are problem details, the shape `cap-errors` owns for the whole platform (`F-b3-13`). The types
this interface adds to the registry:

| Type | Status | Retryable | When |
|---|---|---|---|
| `urn:agentic:problem:credential-audience-mismatch` | 401 | false | A credential minted for one destination was presented at another |
| `urn:agentic:problem:credential-expired` | 401 | false | Presented after `expires_at`; there is no refresh path |
| `urn:agentic:problem:mint-refused-by-policy` | 403 | false | The policy decision refused the mint; no handle was produced |
| `urn:agentic:problem:scope-widening-refused` | 403 | false | An exchange asked for a scope wider than the input's |
| `urn:agentic:problem:mandate-expired` | 403 | false | Outside `not_before` / `not_after` |
| `urn:agentic:problem:mandate-destination-out-of-bounds` | 403 | false | The action names a destination the mandate does not list |
| `urn:agentic:problem:mandate-ceiling-exceeded` | 403 | false | The action would take the total past `ceiling_micros` |
| `urn:agentic:problem:mandate-signature-invalid` | 401 | false | The signature does not verify against the published key |

None of them is retryable (proposed). An expired mandate is expired on the second attempt too, and a
scope-widening request will not start being in scope by being asked again.

## 5. Standards on file

| Standard | What this interface takes from it | Records | Version |
|---|---|---|---|
| Token exchange | Exchanging one token for another with a different audience and a scope that only narrows | `X-cap-mandate-broker-001`, `X-cap-mandate-broker-002`, `X-end-to-end-032` | unverified; all records search-only |
| Tool-access authorization with resource indicators | The destination validates that the credential was issued for it | `X-end-to-end-028`, `X-cap-mandate-broker-003`, `X-cap-mandate-broker-004` | unverified; all records search-only |
| Verifiable credentials as mandates | A signed, expiring, scope-limited authority a non-issuer can check offline | `X-cap-mandate-broker-005`, `X-end-to-end-070`, `X-end-to-end-071` | unverified; all records search-only |

No version string is asserted anywhere in this skill. Every record on file for these three is
`status: search-only`; none was fetched from this environment.
