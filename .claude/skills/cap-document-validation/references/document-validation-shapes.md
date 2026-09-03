# Document validation: full shapes

Proposed throughout. The body of `cap-document-validation` is enough to judge a validator and to call
the capability; open this file only when implementing the outcome shape, the error unit, or the
conformance report, or when reviewing someone who did. Every id here resolves with
`python3 tools/kb.py show <id>`.

## Why these are here and not in the body

The skill body carries summary shapes. A schema longer than about 25 rendered lines is long material
and belongs in a reference file, so the body stays loadable and the full shape stays exact.

## validation-outcome, full (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:outcome:0.1",
  "title": "ValidationOutcome",
  "type": "object",
  "additionalProperties": false,
  "required": ["valid", "dialect", "schema_uri", "errors", "keywords_checked", "adapter_role"],
  "properties": {
    "valid": { "type": "boolean" },
    "dialect": {
      "type": "string",
      "description": "The dialect URI the adapter actually resolved at run time, not the one the schema file declares. See the dialect_in_effect operation (F-a7-04 is why this field exists)."
    },
    "schema_uri": { "type": "string", "minLength": 1 },
    "adapter_role": { "enum": ["today", "second"] },
    "keywords_checked": {
      "type": "integer", "minimum": 0,
      "description": "Count of schema keywords actually evaluated. A validation reporting valid=true with keywords_checked=0 is inconclusive, not a pass (F-a7-03)."
    },
    "instances_served_by_handle": { "type": "integer", "minimum": 1 },
    "errors": {
      "type": "array",
      "items": { "$ref": "#/$defs/error_unit" }
    }
  },
  "$defs": {
    "error_unit": {
      "type": "object",
      "additionalProperties": false,
      "required": ["instance_location", "keyword_location", "message"],
      "properties": {
        "instance_location": {
          "type": "string",
          "description": "Location of the offending node inside the instance, as a JSON Pointer (X-cap-document-validation-005)."
        },
        "keyword_location": {
          "type": "string",
          "description": "Pointer to the keyword in the schema that rejected it, relative to the schema resource."
        },
        "absolute_keyword_location": {
          "type": "string",
          "description": "Optional. Absolute URI of that keyword, needed when references cross schema resources."
        },
        "message": { "type": "string", "minLength": 1 }
      }
    }
  }
}
```

Rules that the shape alone does not carry:

| Rule | Reason |
|---|---|
| `errors` is empty if and only if `valid` is true | A caller must not have to check both fields to know what happened. |
| `errors` holds every violation from one pass, in instance order | Stopping at the first failure makes repair iterative (X-cap-document-validation-005). |
| No adapter-specific field is ever added | Two conformant adapters must be indistinguishable to a caller reading only the outcome. |
| Message text is never parsed by a consumer | The located fields are the machine-readable part; the message is for a human. |

## conformance-report, full (proposed)

The report the definition of done asserts on. One object per adapter, plus a summary.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["suite", "adapters_run", "adapters"],
  "properties": {
    "suite": { "type": "string", "description": "Path or revision of the official suite directory that was run." },
    "adapters_run": { "type": "integer", "minimum": 2 },
    "adapters": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["role", "cases_run", "required_failed", "optional_failed", "dialect_in_effect"],
        "properties": {
          "role": { "enum": ["today", "second"] },
          "cases_run": { "type": "integer", "exclusiveMinimum": 1000 },
          "required_failed": { "type": "integer", "minimum": 0 },
          "optional_failed": { "type": "integer", "minimum": 0 },
          "dialect_in_effect": { "type": "string" },
          "failed_case_ids": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

`required_failed` and `optional_failed` are kept apart because the suite marks some cases optional;
folding them together lets an adapter look conformant by skipping the ones it cannot do, and lets a
conformant adapter look broken for an optional case nothing in this platform uses.

## Reading the breakage

The definition of done's breakage configures one adapter for an older draft. It is the right breakage
because it changes nothing a reviewer can see in a schema file and everything about what is enforced:
the older draft has no `$dynamicRef`, so those cases fail while ordinary documents keep passing. That
is exactly the failure mode `F-a7-04` describes, made visible by the `dialect_in_effect` field.
