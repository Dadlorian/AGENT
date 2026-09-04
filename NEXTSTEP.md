# Next step: clean up after the night run (rows 74, 75, 76)

Documented on 2026-09-04 at the owner's request; nothing here has been done. Each item names the files, the command that shows the problem, and what done looks like. Order matters: 1 and 2 before 3, everything before 8.

## 1. Two examples went red when re-run at index time

Both were green at their close (ledger records 75-steer-close, 75-progress-close). The morning page re-ran every example while other examples were still running, and two went red. Decide whether it is a collision or a real defect before trusting either.

| Example | Symptom | Where to look | Done when |
|---|---|---|---|
| steer | `bash docs/night/hidden/steer.sh` ends "disposition reject, 1092 micros over 1 attempt(s), task status projected from the stream failed" | `examples/steer/run.py` writes under `examples/steer/out/`; the hidden check reads a ledger head; two runs sharing `out/` would explain it | hidden check green run alone, then green while `bash examples/watch/test.sh` runs at the same time |
| progress | `bash examples/progress/test.sh` line 999: a `python3 run.py --crash-at 'draft#2'` process was `Killed` | the crash-and-resume case in `examples/progress/test.sh`; a `Killed` is the kernel (memory) or an outer timeout, not the test; the box has 4 CPUs and the run had two agents plus my index in flight | the test passes alone and under `ulimit -v` of the box; if the crash case needs more memory than the box has, the test declares it and skips with a printed reason rather than dying |

Rule to add while there: every example's `test.sh` writes under its own `out/<run-id>/` (a fresh directory per invocation), so parallel runs never share files. `out/` is now git-ignored (`.gitignore`: `examples/*/out/`, `out/`).

## 2. Two parked examples: done and improve

`docs/night/parked.json` holds both. The run stopped before their second improve round.

| Example | State | Commands | Done when |
|---|---|---|---|
| done | review (14 findings) and improve record exist; visible check green (`passed 76`); hidden check red: `hidden passed 9, failed 4` ("the closure does not declare light_predicate" and three more) | `bash docs/night/hidden/done.sh` lists the four; fix in `examples/done/`, append applied entries to `kb/ceremonies/75-done-improve.json` | visible and hidden green; `python3 tools/check_ceremony.py kb/ceremonies/75-done-review.json kb/ceremonies/75-done-improve.json` at unresolved 0; ledger record 75-done-close; `bash tools/checkpoint.sh "75-done: example closed" examples/done kb/ceremonies docs/night`; entry removed from parked.json |
| improve | review exists (11 findings, both plants caught); no improve record; visible green (`passed 76`); hidden red: `hidden passed 11, failed 2` (a run-step label that does not match what the command prints, and one more) | run the improve step per `state/briefs/example-improve.md` for area improve, then the close per `state/briefs/example-close.md` | same as done, with `kb/ceremonies/75-improve-improve.json` written |

Then the phase-3 boundary that never ran: one lessons row for status_row 75 covering progress, done and improve (`state/lessons.jsonl` has two rows for 75 today), and the brief and `build-example` skill improvements it implies (`state/briefs/example-*.md`, `.claude/skills/build-example`), rendered and validated.

## 3. Re-answered sections whose evidence drifted

The assessors recorded command outputs while phase 3 was still adding examples, so some recorded last lines no longer match a re-run. Eighteen of the 24 files in `docs/litmus/answers-v2/` pass the checker today; six do not:

| File | Errors | Typical cause |
|---|---|---|
| `concern-identity.jsonl` | 6 of 6 | a command counting example areas (5 then, 7 now) |
| `document-validation.jsonl` | 3 of 7 | same |
| `policy.jsonl` | 2 of 6 | `example_areas=5` recorded, `7` printed now |
| `concern-errors.jsonl`, `errors.jsonl`, `telemetry.jsonl` | 1 each | same class |

Command: `LITMUS_ANSWERS_DIR=answers-v2 python3 tools/litmus_answers.py check docs/litmus/answers-v2/<file>`. Fix by an isolated assessor per file (brief `state/briefs/reanswer.md`): re-run each recorded command, replace the recorded last line with what it prints now, and keep the score only if the new output still supports it; otherwise re-score. Never edit a last line to make a check pass. Done when all 24 files print 0 errors and each has a ledger record 76-answer-<section>.

Design fix so this cannot recur (proposed): each answer records the commit it was measured at, and the checker re-runs commands in a worktree at that commit when the tree has moved. One tool change in `tools/litmus_answers.py`.

## 4. Sections not yet re-answered, then the v2 scorecard

Not re-answered: durable-execution, scheduling, concern-budget (moved by progress), provenance, state-persistence, concern-provenance (moved by done); improve moves none. Answer each with `state/briefs/reanswer.md` into `docs/litmus/answers-v2/<section>.jsonl` after items 1 and 2 land. Then copy the v1 rows of any section still without a v2 file into `docs/litmus/answers-v2/carried.jsonl`, and run:

```
LITMUS_ANSWERS_DIR=answers-v2 LITMUS_SCORECARD=scorecard-v2.json python3 tools/litmus_answers.py scorecard
python3 tools/spot_check.py sample litmus 10
```

and have a verifier answer the ten without reading answers-v2 (`state/briefs/spot-check.md`), then `LITMUS_ANSWERS_DIR=answers-v2 python3 tools/spot_check.py compare litmus docs/litmus/spot-check-v2.jsonl`. Done when the v2 scorecard exists, the compare shows no contradictions, and one lessons row for status_row 76 is written.

## 5. The two new future-state areas

`docs/architecture/proposed/steer.json` and `watch.json` (fleet state management; inside-unit observability) were written as proposed blueprint rows with research queries. Fold them into `docs/architecture/blueprint.json` under `gaps`, run `python3 tools/blueprint_check.py` (0 errors) and `python3 tools/kb.py import-blueprint`, then `python3 tools/kb.py verify`.

## 6. Documents that are now behind

- `README.md`: 29 skills (build-example added); a section for `examples/` (seven areas, `docs/examples/index.md`); tools table rows for `checkpoint.sh`, `examples_index.py`, `night_report.py`; the validator line now reads `29 skills checked`.
- `HUMAN-REVIEW.md`: the ledger count (299 today), 29 skills, and a line in section 0 pointing at the v2 scorecard once it exists.
- `docs/skill-graph.md`, `docs/guides/`, `docs/acceptance/matrix.*`: regenerate (`python3 tools/skill_graph.py`, `python3 tools/render_guide.py`, `python3 tools/acceptance_check.py`) and check they still say 16 of 16 accepted.
- `docs/night/report.md`: regenerate after items 1 to 4 (`python3 tools/night_report.py`); its "Actual" line stays "not measured per agent by the engine" until item 7.

## 7. Cost accounting gap

The workflow engine does not report tokens per agent, so the card's estimate (about 11M agent tokens) has no posted actual. The per-agent transcripts are under the workflow's transcript directory (`journal.jsonl` names each agent id). Either sum usage from those transcripts once, or accept that the ledger token line (row 72) is the only durable mechanism and wire it: every agent's ledger record carries `tokens_in`, `tokens_out`. Decide which; document the decision in `state/lessons.jsonl`.

## 8. Close the rows

When 1 to 6 are done: `python3 tools/final_acceptance.py --write` at one commit (15 of 15 expected), `python3 tools/improvement_loop.py plan 7` for the fresh plan, then in `STATUS.md` mark 74, 75 and 76 Done with a measured result each (at most eight words), `python3 tools/status_archive.py`, one ledger record per row, commit and push. Row 21 (the continuous loop) is then the next thing to start, against the fresh plan.

## 9. Still yours

Rows 14 and 45 (fetch access for standards), 37 (live host access so the cells stop being simulated), and the escalation default and seed choice the unit design recommends (bounded cascade with one evidence-gated class step; a generated, hashed seed) if you want them changed before the run example is taken as the pattern.
