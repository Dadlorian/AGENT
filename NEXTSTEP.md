# Next step: clean up after the night run (rows 74, 75, 76)

Updated 2026-09-04 after the cleanup batch. Items marked DONE landed in the cleanup; everything else is what to try later, in this order. Nothing below the DONE marks has been done.

## What the cleanup batch already did (DONE)

- Item 1 (re-run reds): steer was a real defect (a mid-run typed refusal printed no problem banner), fixed; progress's "Killed" was the crash case killing itself as designed, the real defect was the test racing itself over a shared ledger path, now serialized with a lock (`examples/*/.test.lock`, git-ignored).
- Item 2, half: improve closed (88 visible, 13 hidden, 9 applied, 2 declined). The phase-3 boundary ran: one lessons row, briefs and `build-example` improved.
- Item 3: the six drifted answer files refreshed with scores held honestly (all six at 0 errors at the time).
- Item 4, half: the six remaining sections re-answered (durable-execution 5 aligned 1 leading; scheduling 4 aligned 3 exists; concern-budget 7 aligned; provenance 3 aligned 3 exists; state-persistence 5 aligned 2 exists; concern-provenance 5 aligned 1 misaligned: the bundle publishes its own signing key, so a forged statement verifies).
- Item 5: the two new areas are in the blueprint as gaps (318 entries, 0 errors), imported into the knowledge base.
- Item 6: README and HUMAN-REVIEW refreshed for 29 skills and the examples; guides, graph and matrix regenerated (16 of 16 accepted).
- Item 7: tokens summed from the transcripts (`docs/night/cost.json`): 129 agents, 0.78M output, 23.6M cache-creation, 1,086M cache-read; posted against the estimate in `state/night.json` with the lesson to estimate in the four usage classes.

## A. The done example: two hidden assertions after three improve rounds (row 75)

State: 14 of 14 review findings applied; `bash examples/done/test.sh` prints `passed 81, failed 0`; `bash docs/night/hidden/done.sh` prints `hidden passed 11, failed 2`. Rounds two and three each targeted exactly these two and did not move them, so a fourth round is the wrong move.

| Assertion | What the hidden script says | What the improver did | Try |
|---|---|---|---|
| h-06 "a statement names neither the code version nor the run" | 17 of 21 statements carry no `git_commit`, `interface_version`, `scripts_sha256` or run id, "and no gap row says so" | rewrote README gap G15 to name the 17, the stores, the fields and why (`emit.py`'s signature) | read `docs/night/hidden/done.sh` h-06 and see what form of gap row it parses (a row id, a count, a store name); either make G15 match that form, or, better, make every statement carry the code version and run id, which is what the future state asks and the `xc-provenance-chain` reference already specifies |
| h-07 "a declared gate rule is decoration" | with `subject-digest-must-match` dropped from the declaration, the gate still refuses on subject mismatch | built one `trust_policy()` from `promotion.gate_rules` used by both `gate()` and `write_bundle()`, and a test arm proving the declared/undeclared difference | run the hidden script's own harness (it invokes the example with the rule removed and reads the refusal); the standalone verifier the bundle ships may still carry `expected_subjects` from an earlier build under `out/`: run with a clean `out/` first; if it still refuses, the verifier reads the rule from a place the declaration does not reach, so make the bundle's verifier policy derive from the declaration only |

Rule to settle it: an isolated reviewer (Opus) reads both the example and the hidden script and rules which side is wrong, records the ruling in `kb/ceremonies/75-done-ruling.json`, and only then one improve round. Then close: `python3 tools/check_ceremony.py kb/ceremonies/75-done-review.json kb/ceremonies/75-done-improve.json`, ledger `75-done-close`, `bash tools/checkpoint.sh "75-done: example closed" examples/done kb/ceremonies docs/night`, remove the entry from `docs/night/parked.json`.

## B. The v2 scorecard: 7 drifted rows (row 76)

`LITMUS_ANSWERS_DIR=answers-v2 python3 tools/litmus_answers.py check` prints `144 answers, 7 errors`, so `LITMUS_ANSWERS_DIR=answers-v2 LITMUS_SCORECARD=scorecard-v2.json python3 tools/litmus_answers.py scorecard` refuses to write. The seven are the same class as before: recorded command outputs that count things in the tree (statements, bodies, example areas, ledger length) moved while the last assessors and the done rounds ran together.

Try, in order:
1. The design fix first, so this is the last time: in `tools/litmus_answers.py`, record `measured_at` (short commit) on every answer's evidence when written, and in `check`, when a command's output differs, re-run it in a temporary worktree at `measured_at` (`git worktree add /tmp/lit-<commit> <commit>`) before calling it an error; a match at the recorded commit passes; only a mismatch at the recorded commit is a defect. The reanswer brief then tells assessors to run `git rev-parse --short HEAD` into each evidence row.
2. Then either backfill `measured_at` from each file's checkpoint commit (`git log --format=%h -1 -- docs/litmus/answers-v2/<section>.jsonl`) and re-check, or refresh the seven by hand the way item 3 was done (re-run, replace the last line, keep the score only if the finding still holds).
3. Build the scorecard, then the spot-check: `python3 tools/spot_check.py sample litmus 10`, a verifier answers the ten per `state/briefs/spot-check.md` into `docs/litmus/spot-check-v2.jsonl` without reading answers-v2, then `LITMUS_ANSWERS_DIR=answers-v2 python3 tools/spot_check.py compare litmus docs/litmus/spot-check-v2.jsonl`.
4. One lessons row for status_row 76.

What the re-answers already say, so the scorecard will not surprise you: still below aligned after the examples are scheduling q2, q5, q7; provenance q3, q5, q6; state-persistence q5, q7; telemetry q4; concern-provenance q6 misaligned (published signing key); and whatever the seven refreshed rows settle to. Those become the next improvement plan.

## C. Regenerate and close (rows 74, 75, 76)

After A and B: `python3 tools/examples_index.py`, `python3 tools/night_report.py`, `python3 tools/improvement_loop.py plan 7`, `python3 tools/final_acceptance.py --write` (runs every harness; expect 15 of 15), then in STATUS.md mark 74, 75 and 76 Done with a measured result each (at most eight words), `python3 tools/status_archive.py`, one ledger record per row, `bash tools/checkpoint.sh "rows 74-76 closed" STATUS.md STATUS-ARCHIVE.md docs state`.

## D. Structural fixes worth doing before the next run

- **Examples must not share files.** Every `test.sh` and `run.py` under `examples/` writes under `out/<run-id>/` per invocation (progress is serialized with a lock as a stopgap; done's suite does `rm -rf out`, which is what made concurrent runs report spurious failures).
- **Hidden checks that count things in the tree are fragile** for the same reason; a hidden check reads only its own example's outputs from its own run directory.
- **The workflow engine caps at CPUs minus two (2 here).** Run lanes as direct agents with `tools/checkpoint.sh`, or as several workflows, not one.
- **Estimate cost in the four usage classes** (uncached input, cache creation, cache read, output) per model class, and post actuals from `docs/night/cost.json`'s method; the ledger token line (row 72) is still not wired.
- **Concurrency and the checker**: the `measured_at` change in B.1 is the durable fix; until then never run assessors while examples are being edited.

## E. Still yours

Rows 14 and 45 (fetch access for standards), 37 (live host access so the cells stop being simulated), and the unit design's escalation default and seed choice if you want them changed before the run example is taken as the pattern. Row 21 (the continuous loop) starts against the plan from C.
