---
name: "build-solution-architecture"
description: "The solution-architecture lens applied before a section is built: one blueprint that lists the standards at play with a version or unverified, enumerates every state type exhaustively before pruning, fills the four-door entry matrix, reads each component through its capability's adapter boundary, maps what a change breaks, is myopia-checked by an independent reviewer, turns everything uncited into a triaged gap with a research query, and counts what a builder must read. Load it before writing or revising docs/architecture/blueprint.json, before a section's skills are authored, when someone asks where does this state live, who owns it, which door reaches it, or what breaks if we swap this, when a design is about to name a component instead of a capability, when a review hands back findings on an architecture record, and when an architecture claim has no citation behind it."
---

# build-solution-architecture (folded into `build-ceremony`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Produce, before a section is built, one blueprint that shows where the impacts are, because standards, systems and components will all change. | sourced | `T-t7-04` "Standards will change, systems will change, and components will change; the harness shows where the impacts are." |

## Contract

### Shapes (JSON Schema 2020-12)

**Blueprint, top level (proposed)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Solution architecture blueprint, top level (proposed)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "standards_at_play",
    "state_types",
    "entry_matrix",
    "tool_entries",
    "impact_map",
    "myopia_check",
    "open_questions",
    "gaps",
    "usability",
    "provenance"
  ],
  "properties": {
    "standards_at_play": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "state_types": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "entry_matrix": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "tool_entries": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "impact_map": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "myopia_check": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "open_questions": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "gaps": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "usability": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entry"
      }
    },
    "provenance": {
      "type": "object",
      "required": [
        "kb_source_sha256",
        "kb_heads"
      ],
      "properties": {
        "kb_source_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "kb_heads": {
          "type": "object"
        }
      }
    }
  },
  "$defs": {
    "entry": {
      "type": "object",
      "description": "One row. It lists resolving kb ids under \"sources\" with a \"quote\" that is a verbatim substring of one of them, or it carries \"status\": \"gap\", or its text says proposed. The per-section columns are in references/blueprint-shape.md.",
      "anyOf": [
        {
          "required": [
            "sources"
          ]
        },
        {
          "required": [
            "status"
          ]
        }
      ]
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every row is one of three kinds and there is no fourth: it cites kb ids that all resolve, or it carries status gap, or its text says proposed (proposed: the rule tools/blueprint_check.py enforces). Research query: JSON Schema anyOf/oneOf patterns for validating a closed three-state tagged record (cited, gap-status, or proposed) with no untagged fourth state. | proposed | - |
| A row counts as sourced only when every id it cites resolves, so one unknown id makes the whole row unsourced rather than partly sourced (proposed: the rule tools/blueprint_check.py enforces). Research query: reference-integrity checking practice on treating a record with any one broken cross-reference as wholly unresolved rather than partially resolved. | proposed | - |
| Every status gap row outside gaps[] is represented in gaps[], matched by its where prefix or its claim text, so a gap cannot be admitted in one section and hidden from the gap count (proposed: the rule tools/blueprint_check.py enforces). Research query: single-source-of-truth linting practice for a status recorded in two places in one document, cross-checked for consistency by a script. | proposed | - |
| Every state row carries a pinning risk, because the blueprint is an overlay across components and never pins the integration to one of them. | sourced | `T-t7-01` "it never pins the integration to a component" |
| Every component row is read through the capability that owns it and names the adapter boundary that hides it, never the other way round. | sourced | `T-t7-02` "Every harness call goes through the capability interface, and the component sits behind an adapter." |
| As agentic-stack fixes it for skills, products belong in the adapter column only; in a blueprint that column is the component field of a tool entry, and no caller action, state row or entry-matrix cell may name one. | sourced | `F-part-c-09` "Products belong in the adapter column only." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Enumerate the standards at play first: one row per standard with the capabilities it governs, what it fixes, what it leaves open, and a version or the literal word unverified. Never write a version you did not read in a record. | agentic-stack holds the rule that each interface names the standard that governs it; the blueprint is where that is checked across the whole surface at once, and an unread version number is a fabrication rather than a citation. | sourced | `F-b1-03`, `F-part-c-10` "Cite the standard and its version." |
| 2 | Enumerate every state type exhaustively before pruning any of them, one row each with owner capability, home today taken from PASS.md or the word gap, ideal home, lifetime, the boundaries it crosses, and its pinning risk. | Pruning before enumerating is how a state kind disappears without anyone deciding it should; the pinning-risk column is where the never-pin-the-integration test is applied per state, and home today is a host fact, so it is read from the inventory or recorded as absent. | sourced | `T-t7-01`, `F-meta-02` "it never pins the integration to a component" |
| 3 | Fill the entry matrix: the four doors, a human, an event, a schedule and an external system or agent per the work-intake contract, against every state each door touches, with the minimal caller action and what the platform stamps without being asked. | One shape across four doors is only true if it is written out door by door; a state with no row under any door is a guarantee the builder has no way to learn about, and a caller action of nothing is the honest entry for a guarantee the platform applies rather than the caller requests. | sourced | `T-t6-02`, `F-b4-01` "All four enter through the same shape." |
| 4 | Write each component as a tool entry through its capability lens: the adapter boundary as what it exposes and what it hides, what must stay loose, what would pin the platform to it, the second adapter, and the minimal harness call. | A component read through its own feature list becomes the architecture; read through the interface, it is one adapter behind a call that can be made in isolation and then linked to the others. | sourced | `T-t7-02`, `T-t7-03` "Each component has a minimal call in isolation, and the same calls are linked across the composable elements." |
| 5 | Build the impact map: for each change that can realistically land, list the affected adapters, the affected tests, the affected skills, and whether the core is untouched. | A change whose blast radius is not written down is discovered during the change; the whether-the-core-is-untouched column is the standing check that a swap really is a swap of one adapter. | sourced | `T-t7-04`, `T-t7-05` "Changing a component means swapping its adapter, and the conformance run proves the interface held." |
| 6 | Hand the finished draft to an independent reviewer for a myopia check that returns findings by severity and, separately, a missing-state-types list; then apply or decline each finding in a revision record naming the rows it touched. | The author of a blueprint cannot see what it never named; a target toward perfection is only reached by someone else reading it and by the revision that answers them row by row. | sourced | `T-t7-06`, `T-t4-04` "This direction is a target toward perfection, not a fixed definition; improve on it." |
| 7 | Turn anything uncited into a gap row with a research query, never into an invented value, and triage every gap into three classes: a standard-version gap, a does-a-standard-exist gap, and a host fact the owner decides. | The two research classes are closed by real search results or recorded as none found, while a host-absent fact is design work no search can settle, so mixing them sends a researcher after an answer that does not exist. | sourced | `T-t8-02`, `T-t8-01` "Standard-version gaps and does-a-standard-exist gaps are closed by research with real search results, or recorded as none found." |
| 8 | Close with a usability budget: per door, count the blueprint rows and the skill files a builder must read for the simplest task, state the budget those counts are measured against, name the load path that would meet it, and mark each row met or not met. | Simplicity that is asserted is not measured; a count per door separates the caller-facing claim, which the one-declaration common case meets, from the builder-facing one, which nothing had measured before the budget was written. | sourced | `T-t3-02`, `T-t3-01` "It cannot be daunting or overly complex, or no one will use it." |
| 9 | Run python3 tools/blueprint_check.py before and after every revision and fix every error it names; record the counts it prints (entries, sourced, gaps, listed gaps, errors) in the revision record. Research query: Not externally researchable: the checker is this repo's own script (tools/blueprint_check.py) and its printed counts are its own contract.. | Proposed: the checker is the definition of a well-formed blueprint, and the printed counts are the only claim about coverage that is not an impression. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Label entries with the enumeration the blueprint actually cites and say which one it is: the four consumption entries are a human, an event, a schedule (time), and an external system or agent, which is not the same list as the three ways in, and a table whose labels match neither cannot be read against the contract it names. | sourced | `T-t6-02` "a human, an event, a schedule (time), and an external system or agent" |
| A state type named in prose is not in the blueprint: a kind mentioned in a self-review paragraph carries no owner, no lifetime and no pinning risk until it is promoted to a row with the same columns as every other, so promote it or say in the row why it stays prose (proposed: from the missing-state-types list the myopia review returned). Research query: review-remediation practice on requiring a finding be promoted into the structured record rather than left standing as narrative text. | proposed | - |
| Count what a builder must read per door rather than asserting the design is simple; a number can be compared against a budget and an impression cannot. | sourced | `T-t3-02` "no one will use it" |
| Record what could not be decided and the evidence that would decide it as an open question in the blueprint itself, never as a silent default in a row. | sourced | `F-part-c-06` "What you could not decide, and what evidence would decide it." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/blueprint_check.py docs/architecture/blueprint.json |
| Expected | Measured by tools/measure.py at 9b3f40c: exit 0; last lines: 288 entries, 276 sourced, 31 gaps, 41 listed gaps, 0 errors |
| Deliberate breakage | Append a knowledge-base id that does not exist to the first entry-matrix row's sources in docs/architecture/blueprint.json itself, run the criterion against the mutated file, then restore it byte for byte from a copy taken before the mutation: python3 -c "import json;p='docs/architecture/blueprint.json';d=json.load(open(p));d['entry_matrix'][0]['sources'].append('F-none-99');json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)". The checker reads the path the criterion names, so the mutation has to be applied to that file and undone, not to a copy the criterion would never open. |
| Expected failure | Measured by tools/measure.py at 9b3f40c: exit 1; last lines: error: entry_matrix[0]: unknown source F-none-99 \| 288 entries, 275 sourced, 31 gaps, 41 listed gaps, 1 errors |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is the builder-facing usability budget the platform's to own, or is the simplicity requirement scoped to the caller only? | The measured reads per door for the simplest task, against a stated budget, beside the caller-side count for the same task; the owner decides whether the builder-side number is a platform obligation or a note. | Until the owner decides, record both counts, mark the builder rows not met, and treat the builder budget as proposed rather than as a gate. | `T-t3-01` "It has to be simple to use." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session session_01XDYnrM4HZbMdASzsqN4j96 |
