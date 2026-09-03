# Improvement-loop harness

One capability: a loop that works the metric furthest from its target, gates each
candidate change through an evaluation that can say no, checkpoints the outcome, and
stops when every target holds or a ceiling ends it. The gate is not declared here -
it is `harness/evaluation`'s own interface, imported and used unchanged.

## Files

| File | What is in it |
|---|---|
| `interface.py` | The whole contract: `Metric`, `Scorecard`, `CandidateChange`, `GateSpec`, `LoopSpec`, `IterationRecord`, `Checkpoint`, `LoopOutcome`, `Problem`, and `ImprovementLoopDriver` with its five operations. Imports the gate from `harness/evaluation/interface.py`. No product name. |
| `adapters/dryrun.py` | A bounded loop held in one process, in-memory checkpoints, nothing to install. |
| `adapters/live.py` | This repository's own ceremony loop (`state/loop-workflow.js`, `kb/ceremonies/`, `state/lessons.jsonl`), reached only through the env vars below. Reads the real records; writes only its own shadow. |
| `adapters/second.py` | One iteration per fire: no process between iterations, checkpoints on disk, a fresh binding per fire. |
| `call.py` | The minimal call: 22 lines of caller code below the `>>> CALLER CODE` marker. |
| `conformance.py` | The 25 cases every driver passes, the merge that is the swap proof, and `--break-gate`. |
| `fixtures/scorecard.json` | The scorecard and the candidates offered for each metric. Fixture values named after TARGET T9's rows; nothing here measures this repository. |
| `test.sh` | The gate: conformance, the minimal call on both drivers, the swap proof, the breakage, the failure path, the boundary check. |
| `provenance.json` | Owner and co-skills, kb and research ids, what is measured and what is claimed. |
| `plan-entry.json` | This harness's row, in the shape of `harness/plan.json`'s entries. |

## The minimal call

| Step | What the caller writes | What the platform does unasked |
|---|---|---|
| 1 | an intent and a payload naming the scorecard and one loop declaration | stamps the actor, the correlation id, the budget ceiling and the idempotency key |
| 2 | `ADAPTER=dryrun\|live\|second GATE=dryrun\|second python3 call.py` | registers the scorecard, opens the loop, refuses one with no iteration ceiling, runs one iteration per fire and reads the outcome |
| 3 | reads one result or one problem object | keeps the previous checkpoint in place whenever the gate did not say `passed` |

| It prints | Value on the dry-run driver |
|---|---|
| iterations | 6: `measured_done_share` (failed, held), `measured_done_share` (passed), `stale_status_rows` (inconclusive, held), `stale_status_rows` (passed), `proposed_share` (passed), `measured_done_share` (passed) |
| termination | `terminated_by=verdict_pass (stop)`, targets held 3/3, cost 1500000 of 3000000 micros |
| proof 1 | every iteration worked the metric furthest from its target |
| proof 2 | a gate that said `failed` left checkpoint `ck-a16c7afd5613` in place; 2 declined iterations moved no checkpoint |
| proof 3 | a loop with no iteration ceiling is refused with `urn:agentic:problem:document-invalid` (422), 0 iterations |
| the same scorecard under a ceiling of 2 | `terminated_by=iteration_ceiling (cap)`, escalated with `urn:agentic:problem:deadline-exceeded` |

## Env vars for live

| Variable | Required | What it points at |
|---|---|---|
| `IMPROVE_LOOP_CEREMONY_DIR` | yes | the ceremony records to read, e.g. `kb/ceremonies` |
| `IMPROVE_LOOP_SHADOW_DIR` | yes | where this adapter writes. It never writes into the records above |
| `IMPROVE_LOOP_STATE_FILE` | no | the component's own checkpoint, e.g. `state/loop.json` |
| `IMPROVE_LOOP_LESSONS` | no | the lessons file, e.g. `state/lessons.jsonl` |
| `IMPROVE_LOOP_FIRE_CMD` | no | the command that fires one iteration of the section loop. Unset means read-only: the records on disk are the iterations and nothing is launched |
| `IMPROVE_LOOP_FIRE_TIMEOUT` | no | seconds a fire may take, default 900 |
| `ADAPTER` / `GATE` | no | which driver answers, and which evaluation adapter is the gate |

## What each test proves

| Test | What it proves |
|---|---|
| 1. conformance, dry-run | 25 cases: the digest is stable, the furthest metric is the one worked, a failed gate declines and holds the checkpoint, an inconclusive gate is treated exactly like a failed one, a passed gate promotes, the loop stops on one of exactly three conditions, and a re-delivered iteration is not a second one |
| 1b. caller lines | 22 lines of caller code, under the bound of 40, naming no file in a driver's own storage |
| 2. the minimal call, both drivers | identical output from `dryrun` and `second` apart from the adapter header line; all three proofs printed by both |
| 3. swap proof | conformance before with `dryrun`, after with `ADAPTER=second`, no code edit (the sha256 of `interface.py`, `call.py` and `conformance.py` is identical), `adapters_run=2`, `record_divergence=0`, identical `records_digest`, and the pair differs on three declared axes |
| 4. deliberate breakage | `--break-gate` makes the checkpoint advance whatever the gate said. Both drivers exit 1 on the same two checks (C5, C6) while the unbounded refusal and the ceiling cap are unmoved, so the fault reads as the checkpoint rule and not as a driver |
| 5. failure path | an unconfigured live driver exits 2 with `application/problem+json`, `urn:agentic:problem:adapter-unavailable`, and no traceback |
| 6. boundary | no component or product name outside `adapters/`; five operations, none that edits a target; a candidate has nowhere to put a criterion; the gate object is the evaluation harness's own |
| `--live` | the same 25 cases against this repository's ceremony records, read-only, writing only the shadow directory |

## What would pin this, and how the boundary avoids it

| What could pin the integration | Where it would show | How the boundary avoids it |
|---|---|---|
| Blueprint impact row "the durable executor is replaced" names `compose-loop`: today's iteration is a live session, tomorrow's is a durable step | a driver that only advances while one process is alive | `next_fire()` and the checkpoint are the whole of what an iteration needs; the second driver holds no process between iterations and writes the same records |
| The loop that runs today promotes by editing a target file in place and committing, with a reviewer's judgment as the only authority | a promotion path that names a file, a diff or a commit | no operation on the interface edits a target: a promotion moves a checkpoint and a metric value, and `promotion_authority` is a declared field, not a code path |
| That loop has no evaluation gate at all | a `decision` that no report id backs | the gate is `harness/evaluation`'s interface, imported; every record names the report that decided it, and `inconclusive` is not a softer `failed` |
| A fourth termination reason (candidates exhausted, returns flattened) | an outcome enum that grows | `terminated_by` has exactly three members; running out of candidates is a typed refusal, not a fourth ending |
| `docs/architecture/blueprint.json` has no `tool_entries` row and no `impact_map` row for this composition | a swap nobody can price | the plan row and this table state it; the composition owns no state type of its own - the checkpoint is `compose-loop`'s iteration record and the gate's report is `cap-evaluation`'s |
