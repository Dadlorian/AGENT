# Full shapes for the definition-of-done discipline

Proposed: these are our design, not text from PASS.md. The skill body is enough to apply the
discipline; open this file only when you are writing the record store, the gate that emits a
`gate-outcome`, or the validator that compares a declared configuration against an attested
effective one. Summary shapes for the first two are in the skill's `contract.shapes`.

Source records: `F-part-c-04` (a criterion nothing can fail is not a criterion), `F-a7-03`
(a gate structurally green with every behavioural stage skipped), `F-a7-04` (configuration
written in the documented place had no runtime effect), `X-cross-structure-050` and
`X-build-definition-of-done-004` (in-toto Statement inside a DSSE envelope),
`X-build-definition-of-done-005` (attested values compared against reference values).

## 1. `definition-of-done` record

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:definition-of-done:0.1",
  "title": "definition-of-done",
  "type": "object",
  "additionalProperties": false,
  "required": ["piece", "criterion", "expected", "breakage", "expected_failure", "status"],
  "properties": {
    "piece": {
      "type": "string",
      "minLength": 1,
      "description": "The skill, component, capability or seam this record is the gate for."
    },
    "criterion": {
      "type": "object",
      "additionalProperties": false,
      "required": ["command", "asserts_nonzero_count_of"],
      "properties": {
        "command": { "type": "string", "minLength": 1 },
        "asserts_nonzero_count_of": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 },
          "description": "Named counters the command asserts are greater than zero. An exit code is not a counter."
        },
        "criterion_ref": {
          "type": "string",
          "description": "Handle the runner resolves out of band. The criterion body never travels with the work under test."
        }
      }
    },
    "expected": { "type": "string", "minLength": 1 },
    "breakage": {
      "type": "object",
      "additionalProperties": false,
      "required": ["edit", "reversible"],
      "properties": {
        "edit": { "type": "string", "minLength": 1 },
        "reversible": { "const": true },
        "scope": {
          "type": "string",
          "enum": ["subject", "harness"],
          "description": "Must be 'subject'. A breakage that disables the harness proves nothing."
        }
      }
    },
    "expected_failure": {
      "type": "string",
      "minLength": 1,
      "description": "The exact output the criterion produces under the breakage, including the counter that moves."
    },
    "status": { "enum": ["claimed", "measured"] },
    "measured_at": {
      "type": "object",
      "additionalProperties": false,
      "required": ["session", "date", "tree_dirty"],
      "properties": {
        "session": { "type": "string" },
        "date": { "type": "string", "format": "date" },
        "tree_dirty": { "type": "boolean" }
      },
      "description": "Required when status is 'measured'."
    }
  },
  "allOf": [
    {
      "if": { "properties": { "status": { "const": "measured" } }, "required": ["status"] },
      "then": { "required": ["measured_at"] }
    }
  ]
}
```

## 2. `gate-outcome`

The field that makes A7 finding 2 detectable is `stages[].applicable`. A run whose applicable
behavioural stages sum to zero is `inconclusive`, never `pass`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:gate-outcome:0.1",
  "title": "gate-outcome",
  "type": "object",
  "additionalProperties": false,
  "required": ["piece", "verdict", "stages", "counts"],
  "properties": {
    "piece": { "type": "string", "minLength": 1 },
    "verdict": { "enum": ["pass", "fail", "inconclusive"] },
    "stages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["name", "kind", "applicable", "ran", "checked"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "kind": {
            "enum": ["structural", "behavioural"],
            "description": "structural = diff, syntax, format. behavioural = tests, type checking, analysis, coverage, security."
          },
          "applicable": { "type": "boolean" },
          "ran": { "type": "boolean" },
          "checked": { "type": "integer", "minimum": 0 },
          "skip_reason": { "type": "string" }
        }
      }
    },
    "counts": {
      "type": "object",
      "additionalProperties": false,
      "required": ["applicable_behavioural", "ran_behavioural", "checked_total"],
      "properties": {
        "applicable_behavioural": { "type": "integer", "minimum": 0 },
        "ran_behavioural": { "type": "integer", "minimum": 0 },
        "checked_total": { "type": "integer", "minimum": 0 }
      }
    },
    "exit_code": {
      "type": "integer",
      "description": "Recorded for debugging. It is not the verdict and no consumer may read it as one."
    }
  }
}
```

Decision rule, in order:

1. any stage that ran and failed -> `fail`
2. `counts.applicable_behavioural == 0` -> `inconclusive`
3. `counts.checked_total == 0` -> `inconclusive`
4. otherwise -> `pass`

## 3. `effective-configuration` attestation predicate

Carried as the predicate of an in-toto Statement inside a DSSE envelope, so a validator we did not
write can check the signature. The subject is the adapter build; the predicate is what the adapter
actually resolved at start-up, not the file it was handed.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:effective-configuration:0.1",
  "title": "effective-configuration-predicate",
  "type": "object",
  "additionalProperties": false,
  "required": ["adapter", "resolved_at", "effective", "sources"],
  "properties": {
    "adapter": { "type": "string", "minLength": 1 },
    "resolved_at": { "type": "string", "format": "date-time" },
    "effective": {
      "type": "object",
      "description": "The configuration in force after every overlay, as the process sees it."
    },
    "sources": {
      "type": "array",
      "minItems": 1,
      "description": "Ordered list of the layers that contributed, last one wins.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["layer", "digest"],
        "properties": {
          "layer": { "enum": ["default", "file", "environment", "stored-row", "flag"] },
          "digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
          "overrode": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

The validator compares `effective` against the declared configuration and reports
`mismatched_keys`. A non-empty `mismatched_keys` is a failed definition of done for that adapter,
whatever the gate's exit code was.
