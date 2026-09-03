---
name: build-worked-example
description: The discipline of writing a worked example of this platform in use, so every example answers the same six questions, shows one document through all four entries, and is graded by the same six criteria. Load it before writing or reviewing any example under docs/reference/ or examples/, when a new entry point, capability or composition needs a demonstration, when someone asks 'what would a caller actually write' or 'what does this look like from the event or schedule door', or when an example names a product or restates a default. v1: it fixes the shape of an example and its check; it does not fix where examples live or how they are run.
---

# build-worked-example

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make every worked example of the platform answer the same questions and pass the same check, so the four entries of TARGET T6.2 are demonstrated rather than assumed and an example can be graded, not just read. The examples exist to show composability from the consumer's side: what a caller does not have to write because defaults, named files and late binding carry it. | sourced | `T-t6-02` "Four entries cover nearly every situation" |

## Contract

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every example answers six questions in order: what the caller writes, what resolves and from which layer, what the card shows before spend, where a human decides and what they are shown, what comes back (the return shape cap-consumption fixes, not one restated here), and what could be swapped without the caller noticing. The card question is only answerable because planning completes before execution. | sourced | `F-b1-06` "Cost is knowable before commitment." |
| Every example shows one document through all four entries as cap-consumption names them, byte-identical, with a four-door table whose rows are: what fires it, starts or steers, whose identity, whose money, what the gate does, where the card goes. Only resolution differs between the columns; the entries themselves are not redefined here. | sourced | `T-t6-02` "a human, an event, a schedule (time), and an external system or agent" |
| Every example is graded on six criteria, pass or fail: compact, composed not restated, priced before spend, decidable (every gate has a view), swappable (no product in the caller's document), provable (the return carries verdict, usage and trace). A product in the caller's document fails swappable, by the adapter-column rule cap-consumption states. | sourced | `F-part-c-09` "Products belong in the adapter column only." |
| An example never shows the grading criterion to the thing graded: the instrument is named by reference on the card and never appears in a step's input. | sourced | `F-b1-07` "The grader is never visible to the graded." |
| Every number and every run in an example is labelled claimed or measured. Illustrative numbers are labelled illustrative and never measured. | sourced | `F-part-c-08` "**claimed** from **measured**" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Load agentic-stack, then read docs/reference/composable-plan.md sections 3, 4 and 10: the simplicity mechanisms, the four-door example, and the rubric. Copy its section shape; do not copy its numbers. Research query: not externally researchable: this names this repo's own reference document and its section numbers. | Proposed: the reference is the one worked instance of this discipline. Its shape is the template; its numbers are illustrative and were never measured. | proposed | - |
| 2 | Write the caller's document first, at the smallest size that shows the point: one line of intent if it can, five fields if it must, the optional keys only where the problem needs them. Every value a profile or capability already carries is deleted. | An example that restates a default teaches the reader to restate defaults, which is the opposite of simple to use. | sourced | `T-t3-01` "has to be simple to use" |
| 3 | Answer the six questions in order under six headings: what the caller writes, what resolves (a table with a layer column: caller, capability, platform), the card before spend, where a human decides and the view they see, what comes back (the fixed return shape), what could be swapped. | The card is only honest if resolution ran before anything was spent; putting the card before the execution section in the example mirrors the stage order. | sourced | `F-b1-06` "Planning is a pure function and completes before execution" |
| 4 | Add the four-door table with the exact header row `\| \| Human \| Time (schedule) \| External (system or agent) \| Internal (event) \|` and the six rows named in the invariants. If a column cannot be filled, write what is missing in that cell rather than dropping the column. Research query: table-design practice on writing 'what is missing' into a cell rather than omitting a column when data for it does not exist. | Proposed: the source material worked only the human door; the other three were demonstrated nowhere. A missing column hidden by omission is how that happens again. | proposed | - |
| 5 | Grade the example against the six criteria in a table with rows `R-1` to `R-6`, each pass or fail with one reason. A fail stays in the example with its reason; it is not fixed by deleting the row. Research query: rubric-grading practice on labelling each criterion pass or fail with a reason, and keeping a failing row visible rather than removing it. | Proposed: an example with a visible fail row is a gap register. One with the row removed is marketing. | proposed | - |
| 6 | State in the first paragraph whether the example is reference-only or runnable, label every number claimed, measured or illustrative, keep products out of the caller's document and out of every section except one adapter table, then run this skill's definition-of-done check on the file. | Products in the caller's document mean the abstraction leaked to the top, which is the adapter-column rule cap-consumption states for every caller of this platform; the check catches a dropped door or rubric row, not a leaked product, so the product rule is read by eye. | sourced | `F-part-c-09`, `F-part-c-08` "Products belong in the adapter column only." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: write the event, schedule and external columns before polishing the human one. The human door is the one everybody writes first and the other three are where the design gets tested. Research query: documentation practice on writing the hardest or least-common cases of an example first, then the common case, to test a design rather than merely illustrate it. | proposed | - |
| Proposed: one example per point. A document that shows depth, fan-out and late binding at once teaches none of them; the reference page shows them as three separate documents for that reason. Research query: worked-example pedagogy on cognitive load: whether a single example that combines multiple concepts teaches each concept less effectively than separate single-concept examples. | proposed | - |
| Proposed: grade the example before polishing its prose. A rubric row that fails on the first draft is the finding; prose written before the grade tends to argue the row into passing. Research query: review-practice literature on grading or checking a work product before revising its prose, to avoid post-hoc justification of a result already decided. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | f=${EXAMPLE:-docs/reference/composable-plan.md}; grep -q 'What the caller writes' "$f" && grep -q 'What resolves' "$f" && grep -q 'What comes back' "$f" && grep -q '^\| \| Human \| Time (schedule) \| External (system or agent) \| Internal (event) \|' "$f" && [ "$(grep -c '^\| R-[1-6] \|' "$f")" -eq 6 ] && echo PASS \|\| { echo FAIL; exit 1; } |
| Expected | Measured by tools/measure.py at fd2fa05: exit 0; last lines: PASS |
| Deliberate breakage | Copy docs/reference/composable-plan.md to the scratchpad, delete the `\| Internal (event) \|` cell from the four-door header row, and run the criterion with EXAMPLE pointing at the copy. |
| Expected failure | Measured by tools/measure.py at fd2fa05: exit 1; last lines: FAIL |
| Status | measured |
| Evidence | `F-part-c-04` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-simplicity-budget`, `cap-consumption`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should examples live under docs/reference/ (reference-only) and examples/ (runnable) as two homes, or one? | A second example written under this skill, and whether its readers found it. | Proposed: Two homes, as today: reference-only under docs/reference/, runnable under examples/. Revisit when the third example is written. | - |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/agent-integration-reference-jwnh2q |
