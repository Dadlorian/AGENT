# Next step

Run this before trusting anything below. The file is written by hand; the command is measured.

```
python3 tools/ready_to_build.py     3 of 8 conditions, exits 1 until all hold
python3 tools/phase.py gates        every gate, red ones named
python3 tools/status_check.py --freshness
```

## The plan: bridge.md section 6, steps 1 to 6

Read sections 3, 3b and 4b of bridge.md before the first edit — they are the traps that cost
real time. **Step 6 happens only once `ready_to_build.py` exits 0.** Building before that is how
`examples/archived/` happened.

| step | what | closes | state |
|---|---|---|---|
| 1 | Build the prose gate | R4 | **DONE** 2026-09-10, `tools/prose_gate.py`, row 87 |
| 2 | Attempt ONE example from ONE profile | R7 | **NEXT** |
| 3 | Profile the 8 unprofiled cards | R1 | open |
| 4 | Re-point or retire the archived-facing artifacts | R5 | open |
| 5 | Clear the residue | R2 · R3 | open |
| 6 | Build the remaining areas | — | blocked until the eight hold |

Steps 1 and 2 were independent and could run together. Step 3 is the one worth agents; 4 and 5
are small. Nothing before step 6 is fanned out to nine areas.

## Definition of ready — 3 of 8 met

| # | state | condition | measured now |
|---|---|---|---|
| R1 | open | every card profiled, gate green | 32 of 40 profiled, gate exit 0 |
| R2 | open | no quote still needs a reader | 4 need a person (3 partial, 1 stitched, 0 absent) |
| R3 | open | no undecided citation debt | 23 entries, 23 without an owner_decision |
| R4 | MET | prose carries no unsourced quote or figure | gate exit 0 |
| R5 | open | card->example map points at the areas we will build | map names ['ask', 'done', 'improve', 'progress']...; planned ['1-invocation', '2-orchestration', '3-core-agent', '4-execution'] |
| R6 | MET | the model's purpose is decided (owner) | An industry-aligned reference architecture for an agentic pl |
| R7 | open | one example built from a profile, gaps written down | 0 area(s) built; sufficiency note missing |
| R8 | MET | internal-heavy cards labelled | A card whose citations are majority internal (F/T/REF/A) is  |

## Step 2, the one in flight

Build one area under `examples/reference/` from a card profile, and write **every question the
profile could not answer** into `docs/reference/profile-sufficiency.md`. If it answers
everything, "the card profile is the spec" holds and R7 closes — a real finding either way.
Do it before step 3, or eight more profiles get authored against a spec nobody has tested.

Order note: bridge.md puts step 2 before step 4 on purpose — R7 is the only condition whose
failure is informative, so it is attempted early *even while the others are open*.

## What each later step already has

- **Step 3** — `python3 tools/index_sources.py <card>` for ordered core/primary page candidates;
  `python3 tools/index_glossary.py <card>` for standards and API field names. The glossary covers
  areas 1 to 7 only, so base.1, base.2, base.4 and rail.1 get nothing from it.
- **Step 4** — 7 artifacts still name the archived seven, `CLAUDE.md` in four places, and
  `check_card_example_map.py` is a gate passing on the dead map. STATUS rows 86 and 77.
- **Step 5** — 4 quotes need a reader, 23 citation-debt entries carry no owner decision. Most can
  be re-sourced from the pool rather than decided.

## Keeping this file honest

It went stale for six days once, and `CLAUDE.md` was telling every session to read it first.
Rule: when a step closes, mark it DONE here in the same commit as the work — the same rule
STATUS.md already lives under. The measured columns come from `ready_to_build.py --json`; if they
disagree with the command, the command is right.
