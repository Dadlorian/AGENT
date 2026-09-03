---
name: "build-status-table"
description: "How STATUS.md is kept: one heading and one table with five fixed columns, one plain statement per cell, a closed status vocabulary, no dependency language, and a checker that rejects anything else. Load it before editing STATUS.md or STATUS-ARCHIVE.md, when a row turns Done and should be archived, when adding a work item or changing its status, when a status cell starts to explain instead of state, when someone asks where are we or what is left, and when a report is about to grow prose, sub-bullets, or run-on sentences. Also load it when a row is marked Done without a result, or when a new column seems necessary."
---

# build-status-table

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Give the owner one table that states where the work is, in the simplest form, so a decision can be made without reading prose. | sourced | `T-t3-01` "It has to be simple to use." |

## Contract

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The file is a single heading and a single table. Anything else is rejected by the checker. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |
| As agentic-stack states, a Done row carries a measured result, never a pending one. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| Dependencies live in docs/skill-manifest.json and the ledger, never in the table. (proposed: our convention) Research query: project-tracking practice on keeping a dependency graph out of a status view and in a separate artifact. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Add a work item as one row: a five-word name, a definition of done that is a verifiable statement, a status from the closed set, and a result that is a number or a plain fact. Research query: one-idea-per-row conventions in status-reporting tables for glanceable readability. | Proposed: one idea per cell keeps the table readable at a glance. | proposed | - |
| 2 | Write the definition of done as the state that would make the row Done, not as the work to do. | As agentic-stack states, a criterion nothing can fail is not a criterion, so state the observable end. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| 3 | Mark a row Done only when the result was measured; otherwise leave it Open or In progress and put the current number in Result. | As agentic-stack states, claimed and measured are kept apart. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 4 | When a cell needs a second idea, split the row or move the detail to the run summary. Never widen the table. Research query: practice on splitting a table row versus widening a table when a cell needs a second idea. | Proposed: the table is the decision view, not the record. | proposed | - |
| 5 | Keep row numbers contiguous; retire a row by marking it Done or by deleting it and renumbering. Research query: stable-numbering practice for referring to a row in conversation across edits. | Proposed: stable numbering lets a conversation refer to a row. | proposed | - |
| 6 | Before committing any change that moves a work item, edit its row and run the checker; commit the row with the change. Research query: pre-commit checking practice: running a validator before and after a change to a tracked document, in the same commit as the change. | Proposed: the owner reads the table, not the log; a stale row is a false statement. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Prefer a number in Result over a word; 29 of 29 beats passing. (proposed: our convention) Research query: status-reporting practice on preferring a measured number over a qualitative word in a result field. | proposed | - |
| Blocked names what blocks it in the Result cell in three words or fewer. (proposed: our convention) Research query: practice on naming a blocker concisely in a status field rather than describing it at length. | proposed | - |
| As agentic-stack states, facts belong in the table and reasons in the ceremony records; products only in adapter columns. | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/status_check.py |
| Expected | Measured by tools/measure.py at 1d15132: exit 0; last lines: STATUS.md: 13 rows, 0 errors \| STATUS-ARCHIVE.md: 50 rows, 0 errors |
| Deliberate breakage | Replace the Result cell of the row numbered 13 in STATUS.md with a run-on carrying a dependency word and a parenthetical, then run the criterion and restore the file byte for byte from the copy taken in the same command: `cp STATUS.md <backup> && sed -i '/^\| 13 \|/s/[^\|]*\|$/ Verified; depends on the loop (see row 5) \|/' STATUS.md`. The checker reads STATUS.md at a fixed path, so the mutation is applied to that file and undone, not to a copy the criterion would never open. |
| Expected failure | Measured by tools/measure.py at 1d15132: exit 1; last lines: STATUS.md: 13 rows, 4 errors \| STATUS-ARCHIVE.md: 50 rows, 0 errors |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: -

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
