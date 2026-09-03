# Ceremony records: full shapes and worked examples

Proposed. This file is long material split out of `skill.json` under the progressive-disclosure budget.
The two summary shapes in the skill body are enough to run a ceremony by hand; open this file only when
writing a ceremony checker or adding a field to either record.

Worked examples on disk, both from ceremony 1 over wave 1:

- `kb/ceremonies/ceremony-01-review.json` (7 findings, 0 block, 4 fix, 3 nit)
- `kb/ceremonies/ceremony-01-improve.json` (7 applied, 0 declined, `validator_errors: 0`)

## review-record (full, proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/Dadlorian/AGENT/schemas/ceremony-review.schema.json",
  "title": "ceremony review record",
  "type": "object",
  "additionalProperties": false,
  "required": ["ceremony", "section", "reviewer", "date", "findings", "metrics"],
  "properties": {
    "ceremony": { "type": "integer", "minimum": 1 },
    "section": { "type": "string", "minLength": 1, "description": "The unit reviewed, e.g. a wave name." },
    "reviewer": { "type": "string", "minLength": 1, "description": "Who or what performed the review." },
    "date": { "type": "string", "format": "date" },
    "findings": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "skill", "location", "severity", "category", "finding", "evidence", "suggested_change"],
        "properties": {
          "id": { "type": "string", "pattern": "^C[0-9]+-[0-9]{3}$" },
          "skill": { "type": "string", "description": "Skill name the finding lands on." },
          "location": { "type": "string", "description": "Field path or file location inside that skill." },
          "severity": { "enum": ["block", "fix", "nit"] },
          "category": { "type": "string", "description": "Free-form class, e.g. honesty, usefulness, rule, usability." },
          "finding": { "type": "string", "minLength": 1 },
          "evidence": { "type": "string", "minLength": 1, "description": "Verbatim text copied from the artifact or the cited record." },
          "suggested_change": { "type": "string", "minLength": 1 }
        }
      }
    },
    "metrics": {
      "type": "object",
      "description": "Counters for the section as reviewed. Same counter names must be reused in metrics_after.",
      "properties": {
        "skills": { "type": "integer", "minimum": 0 },
        "rows_total": { "type": "integer", "minimum": 0 },
        "rows_sourced": { "type": "integer", "minimum": 0 },
        "rows_proposed": { "type": "integer", "minimum": 0 },
        "findings_block": { "type": "integer", "minimum": 0 },
        "findings_fix": { "type": "integer", "minimum": 0 },
        "findings_nit": { "type": "integer", "minimum": 0 }
      }
    },
    "brief_improvements": { "type": "array", "items": { "type": "string" } },
    "what_worked": { "type": "array", "items": { "type": "string" } }
  }
}
```

## improve-record (full, proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/Dadlorian/AGENT/schemas/ceremony-improve.schema.json",
  "title": "ceremony improve record",
  "type": "object",
  "additionalProperties": false,
  "required": ["ceremony", "improver", "date", "applied", "declined", "metrics_after", "lessons_for_next_section"],
  "properties": {
    "ceremony": { "type": "integer", "minimum": 1 },
    "improver": { "type": "string", "minLength": 1 },
    "date": { "type": "string", "format": "date" },
    "applied": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["finding", "change", "files"],
        "properties": {
          "finding": { "type": "string", "pattern": "^C[0-9]+-[0-9]{3}$" },
          "change": { "type": "string", "minLength": 1, "description": "What was changed, in terms a reader can check against the files." },
          "files": { "type": "array", "minItems": 1, "items": { "type": "string" }, "description": "Repository-relative paths that must exist." }
        }
      }
    },
    "declined": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["finding", "reason"],
        "properties": {
          "finding": { "type": "string", "pattern": "^C[0-9]+-[0-9]{3}$" },
          "reason": { "type": "string", "minLength": 1 }
        }
      }
    },
    "brief_changes": { "type": "array", "items": { "type": "string" } },
    "metrics_after": {
      "type": "object",
      "required": ["validator_errors"],
      "properties": {
        "rows_total": { "type": "integer", "minimum": 0 },
        "rows_sourced": { "type": "integer", "minimum": 0 },
        "rows_proposed": { "type": "integer", "minimum": 0 },
        "validator_errors": { "type": "integer", "minimum": 0 }
      }
    },
    "lessons_for_next_section": { "type": "array", "minItems": 1, "items": { "type": "string" } }
  }
}
```

## Joins the schemas cannot express

A checker asserts these across the pair, because JSON Schema validates one document at a time:

1. `unresolved == 0`: every `findings[].id` in the review record appears in the improve record.
2. `duplicated == 0`: no id appears in both `applied` and `declined`, or twice in either.
3. `unknown_finding_ids == 0`: no id in `applied` or `declined` is absent from the review record.
4. `missing_files == 0`: every path in an `applied[].files` entry exists in the tree.
5. Counter names used in `metrics` and `metrics_after` overlap, so a before/after diff is possible.
