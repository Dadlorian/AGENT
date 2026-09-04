# Morning page

Estimate: about 11M agent tokens (card of 2026-09-04). Actual: not measured per agent by the engine; 118 agent runs started, 116 finished; per-run usage in the workflow journal. Started 2026-09-04T04:30Z, ended 2026-09-04T15:20Z (stopped by the owner at the progress close).

## Examples (row 75)

| Area | human | event | schedule | external | Visible check | Hidden check | README |
|---|---|---|---|---|---|---|---|
| run | yes | yes | yes | yes | passed 50, failed 0 | hidden passed 13, failed 0 | `examples/run/README.md` |
| ask | yes | yes | yes | yes | passed 63, failed 0 | hidden passed 18, failed 0 | `examples/ask/README.md` |
| watch | yes | yes | yes | yes | passed 73, failed 0 | hidden passed 13, failed 0 | `examples/watch/README.md` |
| steer | yes | yes | yes | yes | passed 96, failed 0 | failed: disposition reject, 1092 micros over 1 attempt(s), task status projected from the stream failed. Ledger head sha256:05fd96a8803c... | `examples/steer/README.md` |
| progress | yes | yes | yes | yes | examples/progress/test.sh: line 999: 24672 Killed                  python3 run.py --entry entries/human.json --ledger out/crash2.jsonl --report out/crash2-a.rep.json --out out/crash2state --crash-at 'draft#2' > out/crash2-a.log 2>&1 | hidden passed 15, failed 0 | `examples/progress/README.md` |
| done | yes | yes | yes | yes | passed 76, failed 0 | AssertionError: the closure does not declare light_predicate | `examples/done/README.md` |
| improve | yes | yes | yes | yes | passed 76, failed 0 | AssertionError: run steps whose label is not what the command prints: [('5', 'the fifth fire closes it', 'parked: iteration 1 of il-ae83f41269fd recorded; the next fi')] | `examples/improve/README.md` |

## Answers moved (row 76)

Mechanism items closed: 14; sections re-answered: 10.


## Parked (needs you)

- {'area': 'done', 'why': 'stopped by the owner at 15:20Z before the improve-b round; visible passed 76, failed 0; hidden AssertionError: the closure does not declare light_predicate', 'state': 'review and hidden checks written; findings applied, hidden red'}
- {'area': 'improve', 'why': "stopped by the owner at 15:20Z before the improve-b round; visible passed 76, failed 0; hidden AssertionError: run steps whose label is not what the command prints: [('5', 'the fifth fire closes it', 'parked: iteration 1 of il-ae83f41269fd recorded; the next fi')]", 'state': 'review and hidden checks written; findings not yet applied'}

## Checks at the end

| Check | Last line |
|---|---|
| `python3 tools/validate_skills.py` | of which restate-and-extend (MECH-2): 0 |
| `python3 tools/kb.py verify` | kb verified: chains intact, source hash matches, every fact matches its lines, rebuild is identical |
| `python3 tools/kb.py ledger-verify` | ledger verified: 299 records, chain intact |
| `python3 tools/status_check.py --freshness` | freshness: 7 live rows, 0 claims, 0 stale |
| `bash examples/end-to-end/test.sh` | passed 30, failed 0 |

Ledger records this night: 30.
