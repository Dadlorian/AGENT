# Memory item, scope grammar and retention defaults (proposed)

Proposed long material for `cap-memory`. The skill body is enough to draw and review the interface
without this file; open it when writing the item schema, the scope grammar, or the retention table.
Every shape here is origin=proposed: PASS.md has no memory row, and no ratified standard governs the
interface (`X-end-to-end-003`, "no prior protocol provides verified memory portability").

## 1. Scope grammar (proposed)

A scope is a set of tags, not a path. At least one dimension is required on a write and on a recall.
Subjects are the actor subjects `cap-identity` establishes.

| Dimension | Subject form | Means | Recall widens to it? |
|---|---|---|---|
| `principal` | `user:<name>` | what this person's runs should know | no |
| `agent` | `agent:<name>` | what this agent has learned about its own work | no |
| `run` | `run:<correlation-id>` | working notes for one run | promoted, never widened in place |
| `org` | `org:<name>` | shared context every principal in the org may read | write here deliberately; it cannot be un-shared |

A selector naming two dimensions means both must match. There is no wildcard, and there is no
"all scopes" selector: a caller that wants everything it may see enumerates the dimensions it holds.

## 2. Full MemoryItem schema (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:memory:item:0.1",
  "title": "MemoryItem",
  "type": "object",
  "additionalProperties": false,
  "required": ["memory_id", "scope", "kind", "body", "provenance", "staleness"],
  "properties": {
    "memory_id": {"type": "string", "pattern": "^mem-[0-9a-z-]{4,}$"},
    "scope": {
      "type": "object",
      "additionalProperties": false,
      "minProperties": 1,
      "properties": {
        "principal": {"type": "string", "pattern": "^user:"},
        "agent": {"type": "string", "pattern": "^agent:"},
        "run": {"type": "string", "pattern": "^run:"},
        "org": {"type": "string", "pattern": "^org:"}
      }
    },
    "kind": {"enum": ["working", "episodic", "semantic", "procedural"]},
    "body": {
      "type": "object",
      "required": ["claim"],
      "properties": {
        "claim": {"type": "string", "description": "one thing a later run can act on"},
        "detail": {"type": "string"},
        "refs": {"type": "array", "items": {"type": "string"}}
      }
    },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["produced_by", "observed_at", "correlation_id"],
      "properties": {
        "produced_by": {"type": "string", "description": "user:, agent:, service: or schedule: subject"},
        "observed_at": {"type": "string", "format": "date-time"},
        "correlation_id": {"type": "string"},
        "supersedes": {"type": ["string", "null"]},
        "superseded_by": {"type": ["string", "null"]}
      }
    },
    "staleness": {
      "type": "object",
      "additionalProperties": false,
      "required": ["expires_at"],
      "properties": {
        "expires_at": {"type": ["string", "null"], "format": "date-time"},
        "review_after": {"type": ["string", "null"], "format": "date-time"},
        "policy": {"enum": ["ttl", "review", "pinned"]}
      }
    }
  }
}
```

`expires_at: null` is legal only when `policy` is `pinned`, and a pinned item still carries
`review_after`. This is what stops "no expiry" from being the silent default the prior art warns
about (`X-cap-memory-004`, "no temporal validity model with no expiry dates or conflict detection").

## 3. Retention defaults (proposed)

| Kind | Default policy | Default horizon | Rationale on file |
|---|---|---|---|
| `working` | ttl | end of run | scoped to the run that made it |
| `episodic` | ttl | 30 days | `X-cap-memory-005`, "raw episodic data should always carry one" |
| `semantic` | review | review after 90 days | `X-cap-memory-004`, staleness is noted, not hidden |
| `procedural` | review | review after 180 days | corrected by supersession, `X-cap-memory-008` |

## 4. Refusal types (proposed)

Problem details in the shape `cap-errors` owns; the media type is `application/problem+json`. All three types below are
proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry `cap-errors` owns: until those rows land, `memory-scope-denied` is
returned as the registered `policy-denied` with a `rule_id` naming the scope rule (which is what `cap-memory-use`'s worked
refusal shows), `memory-staleness-policy-missing` as `document-invalid`, and `memory-item-gone` as `idempotency-conflict`.

| Type | When |
|---|---|
| `urn:agentic:problem:memory-scope-denied` | the recall names a scope the caller's actor does not hold |
| `urn:agentic:problem:memory-staleness-policy-missing` | a write with no `staleness` object |
| `urn:agentic:problem:memory-item-gone` | supersede or forget names an item already expired or superseded |
