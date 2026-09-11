# Next step

**The scoreboard is a command, not this file.** Run it first; it is measured and this page is not:

```
python3 tools/ready_to_build.py      3 of 8 conditions, exits 1 until all hold
python3 tools/phase.py gates         every gate, red ones named
python3 tools/status_check.py        STATUS.md is the row-level view
```

## What we are following

`bridge.md` section 6 is the plan — steps 1 to 6, ordered so each protects the ones after it.
Sections 3, 3b and 4b are the traps that cost real time. Read those before the first edit.

Steps 1 to 5 close the eight conditions below. **Step 6 (build the example areas) happens only
once `ready_to_build.py` exits 0** — building before that is how `examples/archived/` happened.

## Definition of ready — 3 of 8 met

| # | state | condition | check |
|---|---|---|---|
| R1 | open | every card profiled, gate green | `python3 tools/validate_card_profiles.py` |
| R2 | open | no quote still needs a reader | `python3 tools/knowledge_pool.py` |
| R3 | open | no undecided citation debt | `docs/reference/citation-debt.json` |
| R4 | met | prose carries no unsourced quote or figure | `python3 tools/prose_gate.py` |
| R5 | open | card->example map points at the areas we will build | `docs/reference/card-example-map.json vs build-principles.json` |
| R6 | met | the model's purpose is decided (owner) | `docs/reference/build-principles.json` |
| R7 | open | one example built from a profile, gaps written down | `examples/reference/<area>/ + docs/reference/profile-sufficiency.md` |
| R8 | met | internal-heavy cards labelled | `docs/reference/build-principles.json` |

## Order to take them

1. **R7 — one example from one profile.** The only condition whose failure is informative.
   "The card profile is the spec" has never been tested. Build one area under
   `examples/reference/` from a profile and write every question the profile could not answer
   into `docs/reference/profile-sufficiency.md`. Do this before step 3, or eight more profiles
   get authored against a spec nobody has proven sufficient.
2. **R5 — re-point the archived-facing artifacts.** `card-example-map.json` maps all 40 cards to
   the archived seven and `check_card_example_map.py` passes on it, so a gate is green on dead
   work. STATUS row 86.
3. **R1 — the 8 unprofiled cards.** The step worth agents. `tools/index_sources.py <card>` gives
   ordered core/primary candidates; `tools/index_glossary.py <card>` gives standards and API
   field names for areas 1 to 7 — but **not** for base or rail, so base.1, base.2, base.4 and
   rail.1 get nothing from it.
4. **R2 and R3 — the residue.** 4 quotes needing a reader, 23 citation-debt entries with no
   owner decision. Most can be re-sourced from the pool rather than decided.

## Where nothing is tracked

`NEXTSTEP.md` was stale from 2026-09-04 until 2026-09-10: its whole punch list targeted the
seven example areas that moved under `examples/archived/` on 2026-09-09. It is kept short on purpose now — the measured state lives in the commands at the
top, and a hand-written list of what to do next drifts the moment the work moves. The superseded
version is in git history at `bf57082`.
