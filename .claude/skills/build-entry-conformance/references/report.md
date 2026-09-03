# entry-conformance-report: the full shape and the check matrix

Proposed. The skill body is enough to run the suite; open this file when you are writing or reviewing the
report emitter, the CI job that reads it, or a reviewer's check over a recorded run.

## Full report schema (proposed, JSON Schema 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:entry-conformance:report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "subject_digest",
    "client_shape",
    "doors",
    "counters",
    "verdict"
  ],
  "properties": {
    "subject_digest": {
      "type": "string",
      "description": "Digest of the one document driven through every door."
    },
    "client_shape": {
      "enum": [
        "generated-from-description",
        "raw-script"
      ]
    },
    "doors": {
      "type": "array",
      "minItems": 4,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "kind",
          "actor_subject",
          "manifest_digest",
          "identity_hops",
          "budget_source",
          "checks"
        ],
        "properties": {
          "kind": {
            "enum": [
              "human",
              "event",
              "schedule",
              "external"
            ]
          },
          "actor_subject": {
            "type": "string"
          },
          "manifest_digest": {
            "type": "string"
          },
          "identity_hops": {
            "type": "integer",
            "minimum": 1
          },
          "budget_source": {
            "enum": [
              "caller",
              "standing-allocation",
              "pre-authorised",
              "parent"
            ]
          },
          "checks": {
            "type": "object",
            "additionalProperties": {
              "enum": [
                "pass",
                "fail",
                "not-run"
              ]
            }
          }
        }
      }
    },
    "counters": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "doors_checked",
        "manifests_distinct",
        "typed_refusals",
        "replay_noops"
      ],
      "properties": {
        "doors_checked": {
          "type": "integer",
          "minimum": 0
        },
        "manifests_distinct": {
          "type": "integer",
          "minimum": 0
        },
        "typed_refusals": {
          "type": "integer",
          "minimum": 0
        },
        "replay_noops": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "verdict": {
      "enum": [
        "pass",
        "fail",
        "inconclusive"
      ]
    }
  }
}
```

## The check matrix

Every cell is `pass`, `fail` or `not-run`. A `not-run` cell never rounds up to a pass, and a report with any
`not-run` cell resolves to `inconclusive` rather than `pass` (skill invariant on doors_checked).

| Check (`checks` key) | Asserted per door | Fails when |
|---|---|---|
| `manifest_identical` | the door's resolved manifest digest equals the other three | any door resolves a different plan from the same document |
| `identity_attached` | hop count and subject prefix expected for that door, on the entry record and every step record | a hop is missing, or the door's chain is indistinguishable from another door's |
| `budget_attached` | the budget source for that door and a ceiling that is enforced, not merely present | the ceiling is carried but never checked, or the source is wrong for the door |
| `steer_not_start` | an internal event with no parent is refused; the same event against a live correlation steers it | an internal event mints root work, or a legitimate steer is refused |
| `typed_refusal` | a malformed entry returns `application/problem+json` with a type from the closed registry and writes nothing durable | prose comes back, an unregistered type comes back, or a record was written |
| `replay_noop` | the same entry under its original idempotency key returns the same result with zero new records | records are appended, or a second dispatch happens |

## Where today's measured instance sits in the matrix

`examples/end-to-end/test.sh` (29 checks, measured 2026-09-03) fills these cells and no others:

| Cell | Doors covered | Doors not covered |
|---|---|---|
| `manifest_identical` | none - each door is checked alone | all four |
| `identity_attached` | none - the actor is printed, never asserted | all four |
| `budget_attached` | human (refusal before execution and mid-run) | event, schedule, external |
| `typed_refusal` | human (`document-invalid`, 422, nothing written) | event, schedule, external |
| `replay_noop` | human | event, schedule, external |
| `steer_not_start` | none - no internal-event case exists | all |

Client shape: the instance drives every door from repository code, so `client_shape` is neither
`generated-from-description` nor `raw-script` yet, and design rule 4 (`F-b1-05`) is unexercised at these doors.
