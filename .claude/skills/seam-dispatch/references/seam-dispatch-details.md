---
name: "seam-dispatch-details"
description: "Overflow reference for seam-dispatch: contract shapes cut from the body, unchanged with their citations, to keep the body inside the progressive-disclosure budget. Load it when you need the full dispatch-context schema."
---

# seam-dispatch-details (folded into `seam-dispatch`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for executing a single unit of agent work and returning one result, so agent execution is pluggable, the F-b5-03 sentence xc-identity-delegation also carries: the request, the result, cancellation, the ceilings, the partial and the failure are the seam's, and what runs the unit is an adapter. | sourced | `F-b5-02`, `F-b5-03`, `E-seam-dispatch` "This is the seam that decides whether agent execution is pluggable at all." |

## Contract

### Shapes (JSON Schema 2020-12)

**dispatch-context (proposed): what the unit receives, what it folds back, and every compaction in between** (proposed; sources: `X-end-to-end-004`, `X-end-to-end-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:context:0.1",
  "title": "DispatchContext",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. The request declares what context the unit receives; the result declares the summary folded back to the parent; a compaction is a recorded transition rather than an invisible one, so a reader can tell that context was dropped and by which strategy.",
  "required": [
    "inherits",
    "budget_tokens"
  ],
  "properties": {
    "inherits": {
      "enum": [
        "none",
        "folded_summary",
        "full_parent"
      ],
      "default": "none",
      "description": "none is the default: a sub-unit starts fresh unless the parent says otherwise."
    },
    "budget_tokens": {
      "type": "integer",
      "minimum": 0,
      "description": "The context ceiling for this unit, independent of the spend ceiling."
    },
    "carried_digests": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^sha256:[0-9a-f]{64}$"
      },
      "description": "Handed down by reference, never by value, so what a unit read is auditable."
    }
  },
  "$defs": {
    "folded": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "summary_digest",
        "media_type"
      ],
      "description": "What the parent receives back. Appending only this is what keeps a parent's context bounded when a sub-unit ran long.",
      "properties": {
        "summary_digest": {
          "type": "string",
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        "media_type": {
          "type": "string"
        },
        "dropped_token_estimate": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "compaction": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "at",
        "strategy",
        "before_tokens",
        "after_tokens"
      ],
      "properties": {
        "at": {
          "type": "string",
          "format": "date-time"
        },
        "strategy": {
          "enum": [
            "summarise_and_restart",
            "branch_and_fold"
          ],
          "description": "The two strategies the adapter pair must be able to declare. Which one is the platform default is an open question of this skill."
        },
        "before_tokens": {
          "type": "integer",
          "minimum": 0
        },
        "after_tokens": {
          "type": "integer",
          "minimum": 0
        },
        "summary_digest": {
          "type": "string",
          "pattern": "^sha256:[0-9a-f]{64}$"
        }
      }
    }
  }
}
```

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/dispatch/test.sh && python3 harness/dispatch/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 595225d: exit 0; last lines: adapter=second marker=queue-and-poll-oneshot/0.1 assertions_run=33 failed=0 untyped=0 plan_digest=4bce5f723c26 verdict=pass cancel_stop=cancel_timeout criterion_hits=0 \| adapters_run=2 migrated_paths=3 plan_digest_mismatches=0 verdict_mismatches=0 distinct_markers=2 |
| Deliberate breakage | In harness/dispatch/adapters/base.py, make the dispatcher assemble the result before the state-seam write returns unconditionally (the durability branch the gate only enables under its own flag), run the criterion (partial_outputs_without_head becomes 1 on the targeted dispatcher and the gate exits 1), then git checkout harness/dispatch/adapters/base.py. |
| Expected failure | Measured by tools/measure.py at 595225d: exit 1; last lines:   FAIL the same suite exits 0 again (expected 0, got 1) \| passed 31, failed 8 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b5-03` "a machine-checkable definition of done, plus the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: -

Used by: -

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session seam-dispatch 2831cb4f, 2026-09-03 |
