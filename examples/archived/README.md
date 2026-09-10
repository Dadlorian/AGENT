# Archived — the seven user-journey example areas

Superseded 2026-09-09. Kept because the work is real and its evidence is still cited: ceremony
records under `kb/ceremonies/75-*`, `kb/architecture.jsonl` and 21 litmus answer files all point
at these paths, and rewriting them would falsify where that work actually happened.

## What these were

Seven areas — ask, run, watch, steer, progress, done, improve — organised as the order a user meets
a piece of work. Each carried a six-table README, four entry doors, a visible check (`test.sh`) and
a hidden check written by an isolated reviewer.

They were not wrong. They were organised before there was a model to organise them by.

## Why they were replaced

Measured, not asserted — see `docs/reference/card-example-gaps.md`:

- Each area cuts vertically through **4 to 6 of the reference model's 9 areas**, while the model
  cuts by layer. The boundaries were stages in a story, not seams in the architecture.
- **8 of 40 cards had no example at all**: External Event, Workflow & Dispatch, Workspace, Compute
  Resources, Context/Memory Handling, Analyze, Knowledge, Operations.
- Load was uneven — `run/` carried 12 cards, `watch/` and `progress/` 6 each — and **`progress/`
  owned none distinctively**, every card it touched being better shown elsewhere, despite having the
  longest README of the seven.

The replacement derives its structure from `docs/reference/reference-model.json` instead, so an
example's boundary matches a real seam.

## What still works here

Each area's `test.sh` still runs in place. Paths inside these folders are self-relative, so the
checks are unaffected by the move. What broke is anything *outside* naming the old path:
`docs/night/hidden/*.sh`, `tools/examples_index.py`, `JOURNEY.md` via `tools/standards.py`, and the
litmus evidence commands in `docs/litmus/answers*/`. Those were already failing on evidence drift
(row 76, 36 errors) before this move.

Do not add to this directory. It is a record, not a place to work.
