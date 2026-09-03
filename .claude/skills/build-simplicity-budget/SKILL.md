---
name: "build-simplicity-budget"
description: "Hold every element to a counted simplicity budget: one call or one declaration for the common case, options additive with defaults, and an escape hatch that hands full control back. Load it before adding a required field, a required handler, a new concept or a new knob to any envelope, schema, profile or interface; when a review says a surface is simple, clean or easy and offers no number; when someone asks why a first successful run takes so much setup, or how much a unit costs to keep resident; when a schema's required list grows; when deciding whether a new capability belongs in the default path, the options tier or the escape hatch; and when judging onboarding cost or the risk that a surface is too daunting for anyone to adopt."
---

# build-simplicity-budget

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed as the eighth design rule alongside the seven in agentic-stack: every element carries three counted ceilings, so the target requirement that it cannot be daunting or overly complex is checked rather than asserted. | proposed | `T-t3-01`, `T-t3-02`, `F-b1-01` "It cannot be daunting or overly complex, or no one will use it." |

## Entities

| Entity |
|---|
| `E-concern-budget` |

## Contract

### Shapes (JSON Schema 2020-12)

**simplicity-budget-declaration (proposed shape; the worked declaration for the entry envelope is in references/counting-method.md)** (proposed; sources: `T-t3-01`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:simplicity-budget:declaration:0.1",
  "title": "Simplicity budget declaration (proposed)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "element",
    "source_of_truth",
    "ceilings",
    "counted",
    "counted_on",
    "escape_hatch"
  ],
  "properties": {
    "element": {
      "type": "string",
      "minLength": 3
    },
    "source_of_truth": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      }
    },
    "ceilings": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "first_run_concepts",
        "resident_metadata",
        "minimum_implementation"
      ],
      "properties": {
        "first_run_concepts": {
          "type": "integer",
          "minimum": 1
        },
        "resident_metadata": {
          "type": "integer",
          "minimum": 0
        },
        "minimum_implementation": {
          "type": "integer",
          "minimum": 1
        }
      }
    },
    "counted": {
      "$ref": "#/properties/ceilings"
    },
    "counted_on": {
      "type": "string",
      "format": "date"
    },
    "escape_hatch": {
      "type": "string",
      "minLength": 10
    }
  }
}
```

**simplicity-budget-check-result (proposed shape; the three counting expressions behind it are in references/counting-method.md)** (proposed; sources: `F-b4-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:simplicity-budget:check:0.1",
  "title": "Simplicity budget check result (proposed)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "element",
    "counted",
    "ceilings",
    "exceeded",
    "verdict",
    "measured_on"
  ],
  "properties": {
    "element": {
      "type": "string"
    },
    "counted": {
      "type": "object"
    },
    "ceilings": {
      "type": "object"
    },
    "exceeded": {
      "type": "array",
      "items": {
        "enum": [
          "first_run_concepts",
          "resident_metadata",
          "minimum_implementation"
        ]
      }
    },
    "verdict": {
      "enum": [
        "within",
        "exceeded"
      ]
    },
    "measured_on": {
      "type": "string",
      "format": "date"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The layering that keeps the counts low is three tiers, flag then options then closure, which is the practical implementation of progressive disclosure. | sourced | `X-entry-composition-038` "This three-tier model (flag, then options, then closure) is the practical implementation of Progressive Disclosure." |
| An advanced capability is reached through a default that can be overridden, not through a parameter the caller is required to supply upfront. | sourced | `X-entry-composition-039` "sensible defaults with the option to override, rather than requiring explicit configuration of every parameter" |
| The measurable instance of a bounded resident tier is the three-tier skill model, where only the name and description load at startup (~30-50 tokens per skill) and everything else loads on demand. | sourced | `X-entry-composition-036` "only the name and description load at startup (~30-50 tokens per skill)" |
| A minimum implementation surface is countable: a conforming agent registers three named handlers and one connect call, so a claim about how hard something is to implement resolves to a number. | sourced | `X-entry-composition-010` "you can register handlers such as initialize(...), newSession(...), and prompt(...), then call connect(stream)" |
| The Budget concern in PASS.md B4 gives the shape this discipline reuses at authoring time: every unit of work carries a ceiling, and exceeding it terminates the unit, not the platform. | sourced | `F-b4-02`, `E-concern-budget` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| A count over its ceiling rejects the change, it does not warn, on the model of a resource quota that enforces its budget by rejecting the creation of resources that would exceed the established limits. The element gets the new concept only by giving up another required one, by moving it into the options tier with a default, or by raising the ceiling in a recorded decision. | sourced | `X-build-simplicity-budget-004` "rejecting the creation of resources that would exceed the established limits" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The budget never caps capability. It caps what is required; advanced options stay available but not required upfront, and the escape hatch that hands full control back is part of the element, not an exception to it. | sourced | `X-entry-composition-039` "Well-designed APIs present a simple surface area for common use cases, with advanced options available but not required upfront." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Name the element and list the machine-readable files that are its source of truth (a JSON Schema, a registry, an interface definition). Every later count is read from those files by a command, never from a description of them. Research query: budget-declaration practice on whether the source-of-truth files for a counted limit must be machine-readable rather than descriptive prose. | Proposed: a count taken from prose drifts from the artifact the day after it is written, and the next author cannot re-run it. | proposed | - |
| 2 | Count first_run_concepts: the concepts a caller must author for one first successful run, which for a declarative element is the length of its required list. Research query: onboarding-cost research on whether required-field count is a validated proxy for first-run adoption friction. | Proposed: this is the number a newcomer pays before anything works at all, and the target requirement is about adoption, not expressiveness. | proposed | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |
| 3 | Count resident_metadata: what rides with every unit regardless of the work in it, which for an envelope is the required fields minus the payload. | This is the tier paid on every call rather than once, the same distinction the three-tier skill model draws in this skill's invariants between what loads at startup and what loads on demand. | sourced | `X-entry-composition-036` "the full SKILL.md loads when triggered, and reference files load only when needed during execution" |
| 4 | Count minimum_implementation: the handlers or fields someone must implement to stand up a conforming implementation of the element, counted from the definition rather than from the reference implementation. | The handler-plus-connect count in this skill's invariants shows the measure exists; counting from the reference implementation instead measures its conveniences, not the contract. | sourced | `X-entry-composition-010` "you can register handlers such as initialize(...), newSession(...), and prompt(...), then call connect(stream)" |
| 5 | Write the three ceilings as a simplicity-budget-declaration (contract.shapes), setting each ceiling to the count measured today unless a research record supports a lower one, and record counted_on and the escape hatch that hands full control back. Research query: simplicity-budget declaration practice on setting a ceiling to today's measured count as a ratchet rather than to a target value. | Proposed: a ceiling at today's count is a ratchet, so the next required concept has to be argued for rather than added silently, and the escape hatch is what makes the low ceiling honest instead of limiting. | proposed | - |
| 6 | Wire the check as the element's definition of done in the form build-definition-of-done requires: the counting command, its expected output, and a deliberate breakage that adds one required concept to a throwaway copy and makes the same command exit non-zero. | build-definition-of-done already owns this rule (F-part-c-04); the only thing this discipline adds is which command counts and what the breakage is. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion." |
| 7 | Source any ceiling that is not a ratchet to a research record with a verbatim snippet, following build-research-record; a number with no record is written as proposed and says so. Research query: whether a counted ceiling with no supporting research record should default to proposed or block the declaration. | Proposed: a ceiling is the part of this discipline most likely to be invented, and an invented number is indistinguishable from a measured one once it is in a table. | proposed | - |
| 8 | When a count exceeds its ceiling, apply 1-3-1 over exactly three options, move the concept into the options tier with a default, drop another required concept, or raise the ceiling with the reason recorded, then follow the recommendation and record it; carry an unresolved overrun into the section ceremony that build-ceremony defines rather than leaving it open. | The operating protocol names 1-3-1 for exactly this, and an overrun that nobody decides on becomes a permanent exception. | sourced | `T-t5-02` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Enforce the ceiling in a command, not in a paragraph asking authors to keep things small: real enforcement is code, not prose. | sourced | `X-build-simplicity-budget-003` "real enforcement is code, not prose" |
| Reject at admission rather than after the fact, the way a resource quota works by rejecting the creation of resources that would exceed the established limits, so the count is checked when the field is added and not when someone complains. | sourced | `X-build-simplicity-budget-004` "rejecting the creation of resources that would exceed the established limits" |
| Push rarely used capability down a tier instead of deleting it; progressive disclosure defers advanced features rather than removing them, by deferring some advanced or rarely-used features to a secondary screen. | sourced | `X-entry-composition-037` "deferring some advanced or rarely-used features to a secondary screen" |
| A ceiling is a cap per period or per unit, not a total: token budgeting works by setting explicit caps on how many tokens a user, session, or feature can consume within a given period, and a simplicity ceiling is scoped to one element the same way. | sourced | `X-build-simplicity-budget-001` "setting explicit caps on how many tokens a user, session, or feature can consume within a given period" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 -c 'import json,sys; e=json.load(open(sys.argv[1])); a=json.load(open(sys.argv[2])); c=[len(e["required"]), len([f for f in e["required"] if f!="payload"]), len(a["$defs"]["profile"]["required"])]; ok=c[0]<=10 and c[1]<=9 and c[2]<=9; print("first_run_concepts",c[0],"resident_metadata",c[1],"minimum_implementation",c[2],"verdict","within" if ok else "exceeded"); sys.exit(0 if ok else 1)' examples/end-to-end/schemas/entry.schema.json examples/end-to-end/schemas/agent-profile.schema.json |
| Expected | Measured by tools/measure.py at fd2fa05: exit 0; last lines: first_run_concepts 10 resident_metadata 9 minimum_implementation 9 verdict within |
| Deliberate breakage | D=$(mktemp -d); python3 -c 'import json,sys; s=json.load(open("examples/end-to-end/schemas/entry.schema.json")); s["required"].append("priority"); s["properties"]["priority"]={"type":"string"}; json.dump(s,open(sys.argv[1],"w"))' "$D/entry.schema.json"; then run the criterion with "$D/entry.schema.json" as its first argument (the repository tree is left untouched) |
| Expected failure | Measured by tools/measure.py at fd2fa05: exit 1; last lines: first_run_concepts 11 resident_metadata 10 minimum_implementation 9 verdict exceeded |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Composes with

Builds on: `agentic-stack`, `build-ceremony`, `build-definition-of-done`, `build-research-record`, `build-skill-authoring`

Used by: `build-worked-example`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is there a published standard that governs a counted simplicity budget, or does progressive disclosure remain the named pattern with the three-tier skill model as its only measurable instance? | A fetched specification that defines counted limits on a surface, recorded as a research record with a verbatim snippet; searches so far returned the pattern and its instances, not a specification. | No standard is named in contract.standards, and the discipline stands as proposed with its three counts as the check. | `X-entry-composition-037`, `X-entry-composition-036` "Progressive disclosure is an interaction design pattern used to make applications easier to learn and less error-prone" |
| Should the resident_metadata ceiling of roughly 30-50 tokens per unit be applied to the skills in this repository, whose descriptions run to several hundred characters each? | A count of name plus description across the rendered skills against that ceiling, and a decision on whether the description's trigger clauses are worth the resident cost. | The entry envelope is the measured element; skill descriptions are counted but not capped, and the question is carried to the next ceremony. | `X-entry-composition-036` "only the name and description load at startup (~30-50 tokens per skill)" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/build-simplicity-budget 2026-09-03 |
