# compose-operators: the six operator shapes in full

Proposed. The body of `compose-operators` is enough to compose a workflow and to know why a seventh operator is refused; this file carries the six schemas at full length, the fan-out tolerance member, the nesting proof and the widening rule worked through one example. Ids resolve with `python3 tools/kb.py show <id>`.

Every shape here is JSON Schema 2020-12, the dialect named in the skill's Standards row (`F-b3-09`, owned by `cap-document-validation`). None of these schemas is an adopted standard: the vocabulary is ours (proposed).

## The closed set

| Operator | Required members | Child slot | What it decides | Origin |
|---|---|---|---|---|
| `sequence` | `op` `id` `steps` | `steps[]` | order: each child sees the results of the ones before it | proposed |
| `parallel` | `op` `id` `branches` | `branches[]` | fan-out and fan-in; `tolerate.failed` is how many units may fail | proposed |
| `loop` | `op` `id` `max_iterations` `exit_when` `body` | `body` | bounded repetition with three terminations | proposed |
| `approval` | `op` `id` `asks` `view` `decisions` `returns` | none | park, and resume on a decision returned on the same correlation id | proposed |
| `agent` | `op` `id` `agent` `input_from` `task` | none | one call to a declared profile; the profile picks the model class | proposed |
| `judge` | `op` `id` `of` `criterion_ref` | none | grade a step against a criterion the graded step never sees | proposed |

Six rows, and the set is closed: `python3 tools/kb.py show REF-1-02` is the rule that says a seventh row would be new syntax rather than new capability.

## step

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:step:0.1",
  "title": "Step",
  "description": "One operator from the closed set. Every child slot below takes a step, so the vocabulary nests without a second format (REF-2-05, stated by core-document).",
  "anyOf": [
    {"$ref": "#/$defs/sequence"},
    {"$ref": "#/$defs/parallel"},
    {"$ref": "#/$defs/loop"},
    {"$ref": "#/$defs/approval"},
    {"$ref": "#/$defs/agent"},
    {"$ref": "#/$defs/judge"}
  ],
  "$defs": {
    "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{1,39}$"},

    "sequence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "id", "steps"],
      "properties": {
        "op": {"const": "sequence"},
        "id": {"$ref": "#/$defs/id"},
        "steps": {"type": "array", "minItems": 1, "items": {"$ref": "urn:agentic:compose:step:0.1"}}
      }
    },

    "parallel": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "id", "branches"],
      "description": "Fan out over independent branches, fan in when all have returned. Branch order does not affect the result. tolerate is the only place a failure count is meaningful (REF-5-3-07).",
      "properties": {
        "op": {"const": "parallel"},
        "id": {"$ref": "#/$defs/id"},
        "branches": {"type": "array", "minItems": 2, "items": {"$ref": "urn:agentic:compose:step:0.1"}},
        "tolerate": {
          "type": "object",
          "additionalProperties": false,
          "required": ["failed"],
          "default": {"failed": 0},
          "properties": {"failed": {"type": "integer", "minimum": 0}}
        }
      }
    },

    "loop": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "id", "max_iterations", "exit_when", "body"],
      "description": "Bounded repetition. It ends on the exit verdict, on max_iterations, or on the budget ceiling, whichever comes first. There is no unbounded loop operator, and `stop` (done) is never merged with `cap` (escalate) (REF-5-3-08).",
      "properties": {
        "op": {"const": "loop"},
        "id": {"$ref": "#/$defs/id"},
        "max_iterations": {"type": "integer", "minimum": 1, "maximum": 25},
        "exit_when": {
          "type": "object",
          "additionalProperties": false,
          "required": ["judge_step", "verdict"],
          "properties": {
            "judge_step": {"$ref": "#/$defs/id"},
            "verdict": {"enum": ["pass", "fail"]}
          }
        },
        "on_cap": {"enum": ["escalate"], "default": "escalate",
                   "description": "A cap terminates the step as a failure that goes to a human. A stop terminates it as a success. They are not the same field."},
        "body": {"$ref": "urn:agentic:compose:step:0.1"}
      }
    },

    "approval": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "id", "asks", "view", "decisions", "returns"],
      "description": "Park the unit and wait for a person to return a decision on the same correlation id. The wait is not a budget cost. `view` is required: a gate with no view is not decidable (REF-10-05).",
      "properties": {
        "op": {"const": "approval"},
        "id": {"$ref": "#/$defs/id"},
        "asks": {"type": "string", "minLength": 1},
        "view": {"type": "string", "minLength": 1},
        "decisions": {"type": "array", "minItems": 2,
                      "items": {"enum": ["approve", "edit", "reject"]}},
        "returns": {"type": "object", "additionalProperties": false, "required": ["fields"],
                    "properties": {"fields": {"type": "object"}}},
        "on_reject": {"enum": ["stop", "continue"], "default": "stop"}
      }
    },

    "agent": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "id", "agent", "input_from", "task"],
      "description": "Call one declared profile. The profile decides the model class; the step never names a model, an endpoint or a vendor (F-part-c-09).",
      "properties": {
        "op": {"const": "agent"},
        "id": {"$ref": "#/$defs/id"},
        "agent": {"type": "string"},
        "input_from": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "task": {"type": "string", "minLength": 1}
      }
    },

    "judge": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "id", "of", "criterion_ref"],
      "description": "Grade a step's result against a criterion the graded step never sees (F-b1-07). criterion_ref is an opaque handle; the criterion body lives outside the composition entirely.",
      "properties": {
        "op": {"const": "judge"},
        "id": {"$ref": "#/$defs/id"},
        "of": {"$ref": "#/$defs/id"},
        "criterion_ref": {"type": "string", "pattern": "^criterion://[a-z0-9./-]+$"}
      }
    }
  }
}
```

## How nesting works, and why it needs no syntax

`sequence.steps`, `parallel.branches` and `loop.body` all `$ref` the root `step` schema. There is therefore no sub-plan type, no separate plan format and no translation between levels: a loop whose body is a sequence of an agent call and a judge is the same shape as the top-level document, one level down. This is `core-document`'s recursion rule (`REF-2-05`) read as a schema constraint rather than as prose.

Depth is a property of the instance, not of the schema, which is exactly why the bound has to be checked when the composition is resolved rather than declared in the type (`REF-5-2-13`; stated for the typed structure by `core-graph`).

## The widening rule, worked

A new capability - say a static analyser that can be asked for a second opinion - arrives like this:

| What changes | What does not |
|---|---|
| a new agent profile named `static-analyser` in the registry the `agent` operator's `agent` field resolves against | the `agent` operator's schema |
| a new `criterion://` resource the `judge` operator's `criterion_ref` can name | the `judge` operator's schema |
| a new `view` name an `approval` operator can render through | the `approval` operator's schema |

No field is added, no operator is added, and no caller relearns anything (`REF-1-02`). If a proposal cannot be expressed as a wider set of legal values for a field that already exists, it is a request for a seventh operator and is refused at this layer, not at review.

## What has no shape here, deliberately

The judging criterion, the record of attempts already made and the referent a result is compared against have no member on any operator, at any depth (`REF-5-5-01`, `F-b1-07`). There is no field to omit and no field to forget to strip: the shapes above are the enforcement.
