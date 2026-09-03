---
name: build-status-table
description: How STATUS.md is kept: one heading and one table with five fixed columns, one plain statement per cell, a closed status vocabulary, no dependency language, and a checker that rejects anything else. Load it before editing STATUS.md or STATUS-ARCHIVE.md, when a row turns Done and should be archived, when adding a work item or changing its status, when a status cell starts to explain instead of state, when someone asks where are we or what is left, and when a report is about to grow prose, sub-bullets, or run-on sentences. Also load it when a row is marked Done without a result, or when a new column seems necessary.
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
| Columns are exactly: #, Work item, Definition of done, Status, Result. (proposed: our convention) | proposed | - |
| Status is one of Done, In progress, Open, Blocked, Not started. (proposed: our convention) | proposed | - |
| Every cell is one statement: no semicolons, no parentheses, no dependency words, at most 12 words, work item at most 5. (proposed: our convention) | proposed | - |
| As agentic-stack states, a Done row carries a measured result, never a pending one. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| Dependencies live in docs/skill-manifest.json and the ledger, never in the table. (proposed: our convention) | proposed | - |
| STATUS.md is the owner's view: every commit that changes the state of a work item updates its row in the same commit (proposed: owner rule). | proposed | - |
| STATUS.md holds only rows that can still change; Done rows move to STATUS-ARCHIVE.md with their number and a Closed cell, by python3 tools/status_archive.py, never by hand (proposed: our convention). | proposed | - |
| Row numbers are permanent; the live table may have gaps and never renumbers (proposed: our convention). | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Run python3 tools/status_check.py before and after every edit of STATUS.md. | Proposed: the checker is the definition; a table that fails it is not the status. | proposed | - |
| 2 | Add a work item as one row: a five-word name, a definition of done that is a verifiable statement, a status from the closed set, and a result that is a number or a plain fact. | Proposed: one idea per cell keeps the table readable at a glance. | proposed | - |
| 3 | Write the definition of done as the state that would make the row Done, not as the work to do. | As agentic-stack states, a criterion nothing can fail is not a criterion, so state the observable end. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| 4 | Mark a row Done only when the result was measured; otherwise leave it Open or In progress and put the current number in Result. | As agentic-stack states, claimed and measured are kept apart. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 5 | When a cell needs a second idea, split the row or move the detail to the run summary. Never widen the table. | Proposed: the table is the decision view, not the record. | proposed | - |
| 6 | Keep row numbers contiguous; retire a row by marking it Done or by deleting it and renumbering. | Proposed: stable numbering lets a conversation refer to a row. | proposed | - |
| 7 | Before committing any change that moves a work item, edit its row and run the checker; commit the row with the change. | Proposed: the owner reads the table, not the log; a stale row is a false statement. | proposed | - |
| 8 | When a row turns Done, run python3 tools/status_archive.py in the same commit so the live view stays compact; both files must pass python3 tools/status_check.py. | Proposed: the owner reads the live table at a glance; the archive keeps the history without rewriting it. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Prefer a number in Result over a word; 29 of 29 beats passing. (proposed: our convention) | proposed | - |
| Blocked names what blocks it in the Result cell in three words or fewer. (proposed: our convention) | proposed | - |
| As agentic-stack states, facts belong in the table and reasons in the ceremony records; products only in adapter columns. | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/status_check.py |
| Expected | N rows, 0 errors |
| Deliberate breakage | Change one Result cell to a run-on with a dependency word: 'Verified; depends on the loop (see row 5)' |
| Expected failure | exit 1 with: error: row 1: Result contains 'depends'; error: row 1: Result contains ';'; error: row 1: Result contains '('; error: row 1: Result contains ')'; 22 rows, 4 errors. Measured 2026-09-03 in session claude/auto-skill-creation-i8javu; restored file passes with 22 rows, 0 errors. An earlier attempt edited the wrong line and passed; that run was not a measurement and is recorded in the ledger. |
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
