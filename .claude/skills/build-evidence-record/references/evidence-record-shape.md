# evidence-record: the full proposed shape

Proposed material. The Shapes section of `SKILL.md` carries the summary shape (the nine required
fields and their types). This file carries the full JSON Schema 2020-12 draft with the per-field
constraints and the dirty-tree rule, which is too long for the skill body.

Read this file when you are implementing or validating the record store itself: writing the writer,
writing the checker, or reviewing a record whose fields are present but whose values look wrong.
Reading the skill body is enough to write a record by hand.

Field-level notes the summary shape omits:

- `ran.script_sha256` and `output.text_sha256` are lowercase hex sha256, 64 characters.
- `code_version.tree_hash` is the hash of the tree actually under test, which is not the commit when
  the tree is dirty.
- `output.text` is the observed output, verbatim, truncated only at the end and never paraphrased.
- `supersedes` names the record this one corrects; the superseded record stays in place.
- `prev` is the hash of the preceding record, or the genesis marker; `hash` is taken over this record
  with the `hash` field removed.
- The `allOf` rule at the end is the one that has teeth: `tree_dirty: true` forces `status: claimed`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "evidence-record",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "id",
    "recorded_at",
    "claim",
    "ran",
    "code_version",
    "output",
    "status",
    "prev",
    "hash"
  ],
  "properties": {
    "id": {
      "type": "string",
      "description": "Stable id of this record. Records are appended, never edited; a correction is a new record naming this id in supersedes."
    },
    "recorded_at": {
      "type": "string",
      "format": "date-time"
    },
    "claim": {
      "type": "string",
      "minLength": 1,
      "description": "The statement this record is evidence for, written before the run."
    },
    "ran": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "command",
        "script_sha256"
      ],
      "properties": {
        "command": {
          "type": "string",
          "description": "The exact command line, reproducible as written."
        },
        "script_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "environment": {
          "type": "string",
          "description": "Where it ran: host or session identifier."
        }
      }
    },
    "code_version": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "commit",
        "tree_hash",
        "tree_dirty"
      ],
      "properties": {
        "commit": {
          "type": "string",
          "pattern": "^[0-9a-f]{7,40}$"
        },
        "tree_hash": {
          "type": "string",
          "description": "Hash of the tree under test, which is not the commit when the tree is dirty."
        },
        "tree_dirty": {
          "type": "boolean"
        }
      }
    },
    "output": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "exit_status",
        "text"
      ],
      "properties": {
        "exit_status": {
          "type": "integer"
        },
        "text": {
          "type": "string",
          "description": "The observed output, verbatim and truncated only at the end, never paraphrased."
        },
        "text_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        }
      }
    },
    "status": {
      "enum": [
        "claimed",
        "measured"
      ],
      "description": "measured requires exit_status and text from an actual run on a clean tree; everything else is claimed. There is no third label and no absent label."
    },
    "supersedes": {
      "type": [
        "string",
        "null"
      ],
      "description": "Id of the record this one corrects or contradicts. The superseded record stays in place."
    },
    "prev": {
      "type": "string",
      "description": "Hash of the preceding record, or the genesis marker."
    },
    "hash": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$",
      "description": "Hash over this record with the hash field removed."
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "code_version": {
            "properties": {
              "tree_dirty": {
                "const": true
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "status": {
            "const": "claimed"
          }
        }
      }
    }
  ]
}
```
