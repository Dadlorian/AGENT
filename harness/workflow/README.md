# Workflow harness — durable execution, a parked approval, a bounded loop

One durable flow: a step, a bounded loop with a judge exit and a ceiling, a
parked approval a human, an agent or a schedule can answer four ways, an
irreversible step, a real `kill -9`, and a resume at the first incomplete step
with no side effect repeated.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/workflow/test.sh` |
| 2. Watch the call | `ADAPTER=dryrun python3 harness/workflow/call.py` |
| 3. Swap the executor | `ADAPTER=second python3 harness/workflow/call.py` |
| 4. Read the receipt | `python3 -c "import sys; sys.path.insert(0,'harness/workflow'); from interface import load_executor; print(load_executor('dryrun','harness/workflow/out/call-dryrun').read_receipt('wf-release-publish-2026-09-03'))"` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 308 | The capability interface: envelope, step record, run state, receipt, gate record, gate outcome, loop outcome, typed problem, `load_executor`, and `DurableExecutor` with `begin_run`, `checkpoint_step`, `resume_point`, `read_run`, `read_receipt`, `park_gate`, `record_decision`. No product name |
| `adapters/journal.py` | 140 | The store the two in-process executors share: an append-only hash-chained journal and the effect table someone else counts. `fsync` per append, which is what makes the crash real; every read re-reads the file, so a run that crashed in another process is visible through the same handle |
| `adapters/dryrun.py` | 158 | Dry-run executor: an in-process state machine journaled to a file. `keyed_effect`, resume by folding the whole history |
| `adapters/second.py` | 179 | Second executor: a queue plus a state machine on the same journal. `same_transaction`, resume by reading the last materialised state row |
| `adapters/live.py` | 148 | Today's component, reached only through the env vars below. Probes, then reports `adapter-unavailable`. The only file besides the env table that names a product |
| `flow.py` | 407 | The declared flow and the driver: one attempt per process, every guarantee attached around the step and around the restart. **`begin_run`, `checkpoint_step`, `park_gate`, `record_decision` and `read_run` are called here, not in `call.py`** — a crash has to be a process death, so the flow runs as a subprocess |
| `call.py` | 126 | The minimal call: build the envelope, bind one executor, crash, resume, and read the run back with two interface calls of its own — `resume_point` after the crash and `read_receipt` after the resume. It opens no journal, queue or effect file |
| `conformance.py` | 258 | The nine cases every executor must pass, and the report the swap proof compares |
| `test.sh` | 105 | The gate: conformance, the swap proof, the deliberate breakage |
| `provenance.json` | — | Which skills, kb ids, research ids and standard this rests on; what is measured and what is claimed |

## The minimal call

| # | What the caller writes | What the platform does without being asked |
|---|---|---|
| 1 | `ADAPTER=dryrun python3 call.py` | selects the executor by configuration; no code path chooses one |
| 2 | `build_envelope()` — kind, entry id, intent, payload | stamps the correlation id, the budget ceiling, the idempotency key and the actor onto the same envelope |
| 3 | `attempt(entry, adapter, …, "--crash-at", "publish")` | runs the flow to the irreversible step and dies there with `kill -9` |
| 4 | `attempt(entry, adapter, …)` | rereads the journal, resumes at the first incomplete step, recomputes the budget from the committed records, re-attaches the correlation id from the record, and does not ask the human again |
| 5 | `executor.resume_point(run_key)` after the crash, `executor.read_receipt(run_key)` after the resume | answers where a restart continues, what it spent, how many gates were parked and decided, and the effect rows the run committed — from wherever that executor keeps its state, never from a path the caller knows |

Output, identical under both executors apart from the marker line:

| Row | Dry run | Second adapter |
|---|---|---|
| attempt 1 | killed at publish (rc -9) | killed at publish (rc -9) |
| crash | resume_point 10 read through the interface, 10 steps committed, 210000 micros spent | same |
| attempt 2 | resumed at step 10, 10 replayed, 2 run | resumed at step 10, 10 replayed, 2 run |
| gate | 2 parked, 10 deliveries each, 2 decisions applied, 0 re-parked | same |
| loop | verdict_pass, 1 iteration, stop | same |
| effect | 1 effect row on the receipt | 1 row |
| budget | 240000 spent, 1260000 left of 1500000 | same |
| marker | `in-process-journal/0.1` (keyed_effect) | `queue-state-machine/0.1` (same_transaction) |

## Command lines

| Goal | Command |
|---|---|
| One attempt, no crash | `python3 flow.py --entry out/call-dryrun/entry.json --adapter dryrun` |
| Return the work with notes, then approve | `--decision return_with_notes:user:corey --decision approve:agent:release-bot` |
| An agent decides; a schedule decides | `--decision edit:agent:reviewer-bot` · `--decision reject:schedule:gate-sweeper` |
| Ten deliveries of one decision | `--deliveries 10` |
| Trip the loop's iteration ceiling | `--loop-never-pass` |
| Trip the budget mid-loop | `--budget-micros 120000` |
| Let the gate expire | `--gate-expired` |
| The deliberate breakage | `python3 conformance.py --adapter dryrun --adapter second --break-idempotency` |

## Env vars for live mode

Live mode targets the frontend of the workflow engine PASS.md A6 records as
installed with its server not listening — **Temporal**. Nothing else in this
harness names it.

| Variable | Meaning | Example |
|---|---|---|
| `WORKFLOW_ADDR` | `host:port` of the frontend: the gRPC port `7233` or the UI/HTTP port `8233` (PASS.md A6) | `127.0.0.1:7233` |
| `WORKFLOW_NAMESPACE` | namespace the runs live in | `default` |
| `WORKFLOW_TASK_QUEUE` | queue the workers poll | `agentic-durable` |
| `WORKFLOW_API_KEY` | credential, where the frontend requires one | — |
| `WORKFLOW_TIMEOUT_S` | probe and call timeout, default 5 | `5` |
| `ADAPTER` | `dryrun` \| `live` \| `second` — selects the executor | `dryrun` |

Run it with `bash harness/workflow/test.sh --live`. With `WORKFLOW_ADDR` unset it
skips and says so. With it set and nothing listening, the adapter answers
`urn:agentic:problem:adapter-unavailable` (503, retryable) rather than failing
open — which is the only live behaviour measured here.

## What each test proves

| Check | Proves |
|---|---|
| 1b caller code is 21 lines, under 40 | measured by `harness/caller_lines.py`, the one method all five harnesses use, so the number is comparable across them instead of being counted four ways |
| 1b the caller names no adapter storage | the same script fails `call.py` if it names a `.jsonl`, `.db` or `.sqlite` file: T7.2 as a check, not a habit. Reading the journal by path is exactly what a hosted executor would break |
| 1b the receipt's effect count equals the count from outside | the new interface read tells the truth: the gate counts the rows itself and compares. An executor's own tally is what a caller reads, never what proves it honest |
| A0 the resume point was read through the interface | after a real `kill -9` in another process, `resume_point` answers from the store rather than from this process's memory |
| A1 the kill landed (`rc -9`) | the crash is a process death, not a return value; a suite whose kill silently failed passes everything else |
| A2–A3 resumed at the first incomplete step | the run continued where it stopped instead of starting again |
| A4 committed steps were skipped | work already durable is not re-executed |
| A5 every step committed exactly once | the crash did not double the ledger |
| A6–A7 one effect row, no duplicate | counted from `effects.jsonl` by the test, never from the run's own tally |
| A8 the human was asked once | a durable decision survives the crash; the gate is not re-parked |
| A9 budget recomputed from committed records | a restart is not free money |
| A10 one correlation id, re-attached from the record | a resumed run does not become a new root (PASS.md A7 finding 1) |
| A11 marker read from the running executor | a swap that never happened is visible; two green runs of one executor read like a proven swap otherwise |
| A12 declared gap honoured | the keyed-effect executor really does leave an orphan effect at the crash; the same-transaction one really does not. Neither is widened to look like the other |
| B1–B2 loop exits on the judge verdict in 2 iterations | the bounded loop ends on the exit condition and the criterion never reaches the graded step |
| C1–C3 iteration ceiling escalates | a cap is a failure that goes to a human, typed as the registered `deadline-exceeded`, recording the proposed type it substitutes for |
| D1 budget ceiling terminates the unit | the third and last termination reason; there is no fourth to write |
| E approve / edit / reject / return_with_notes | four outcomes, answered by a `user:`, an `agent:` and a `schedule:`; reject leaves zero effect rows; return re-enters the named step once |
| F ten deliveries resume once | the gate-scoped key deduplicates redelivery |
| G expiry plus a late decision | the deadline is a cap, not a stop; a decision after it is a no-op |
| H replaying a finished run | zero steps executed, zero effect rows appended |
| I a tampered journal | an unreadable record is a typed `idempotency-conflict`, never a silent restart from step one |
| swap proof | the same 28 checks pass before and after, with different executor markers and `adapters_run=2` |
| breakage | dropping the idempotency key from the step record fails **both** executors — 14 steps committed instead of 8, nothing replayed, the human asked twice — and additionally repeats the side effect on the keyed-effect one. Both failing is what says the defect is in the step record and not in one engine |

The breakage report is also the clearest reading of the pair: `resume_point_at_start`
stays above zero under the breakage, so duplication is still distinguishable from
a kill that never landed.

## What would pin this, and how the boundary avoids it

From `docs/architecture/blueprint.json`, tool entry *Temporal (data directory
present, server not listening)*:

| Would pin the integration | How this harness avoids it |
|---|---|
| "A contract mentioning deterministic workflow code, worker registration or an event-history format" | `interface.py` names a step, an idempotency key, a checkpoint and a resume point, and nothing else. Determinism, workers and history appear only as *declared attributes of an adapter* (`replay_determinism_required`, `processes_required_for_progress`, `resume_derivation`), which the conformance run asserts rather than requires |
| A contract that assumes a server is reachable | the interface is served today by an executor with no server; the live adapter's first honest behaviour is to report itself unavailable, so "the orchestrator is down" is a typed failure of one adapter, not an outage of the capability |
| A gate defined in the engine's signal vocabulary | the parked gate is a record in the journal, the deadline is an occurrence, and a decision is deduplicated by a gate-scoped key. Which wire carried it is recorded in `delivered_over` for audit, and nothing branches on it |
| An executor that brings its own retry policy, budget or audit trail | budget, correlation, identity and idempotency attach in `flow.py` around the step and around the restart. An executor's own copy would be a second, declinable one |
| A caller that can tell which executor answered, or that knows where the executor keeps its state | `call.py` prints the marker, reads the run back through `resume_point` and `read_receipt`, and opens no file of the executor's. Selecting an executor is configuration; `flow.py`'s only branch on an executor is on its **declared** `effect_commit_mode`, never on its name |

Impact, per the blueprint's impact map: replacing the durable executor touches
the durable-execution adapter, the crash-and-resume run and the idempotency-lease
run; the core is unaffected.

## Deviations from the skills, and why

| Skill text | Here | Why |
|---|---|---|
| `cap-durable-execution-implement` expects `steps_replayed > 0` to hold under the breakage, distinguishing duplication from a kill that never landed | `steps_replayed` is 0 under the breakage; `resume_point_at_start > 0` and `prior_step_ids_seen > 0` carry that distinction instead | With no key on the record, nothing can be *recognised* as complete, so nothing can be skipped. The counter that survives the breakage is the one read from the store rather than from the skip decision |
| The second adapter it names is an in-process transactional step log in a relational database | a queue plus a state machine on the same journal, which `plan.json` names for this harness | Same three axes differ, and no database is running here. The row it commits beside the effect is a journal record rather than a table row |
| `compose-approval-implement` asserts `lease_boundary_observed == "resume-seam"` | not asserted | The keyed lease is enforcement a wave above this interface (`xc-idempotency-lease`). Here the gate-scoped key alone deduplicates redelivery, which is what the platform has today |
