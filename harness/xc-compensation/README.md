# Compensation harness — the unwind guarantee, behind one interface, over two registers

Five effects declare their irreversibility class and their compensating action
before any of them commits; four commit, the fifth fails, and the register is
walked backwards. Nothing compensates on this stack today, so both registers
here are the first ones: one holds the record in an execution engine's step
journal, the other in the platform's own append-only chained log.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/xc-compensation/test.sh` |
| 2. Watch the call | `ADAPTER=dryrun python3 harness/xc-compensation/call.py` |
| 3. Swap the register | `ADAPTER=second python3 harness/xc-compensation/call.py` |
| 4. Read a plan before the first effect | `python3 -c "import sys; sys.path.insert(0,'harness/xc-compensation'); from interface import load_register; print(load_register('dryrun','harness/xc-compensation/out/call-dryrun').unwind_plan('run-saga-dryrun'))"` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 449 | The capability interface: envelope, `CompensatingAction`, `DeclareEffect`, `CompensationRecord`, `UnwindPlan`, `UnwindReport`, the typed `Problem`, `NothingToReverse`, `load_register`, and `CompensationRegister` with `declare_effect`, `seal_effect`, `unwind`, `unwind_plan`, `records`, `head`, `head_ordinal`. The refusals and the reverse walk are here, so no register can be the lenient one. No product name |
| `store.py` | 152 | Two files, no register logic: an append-only hash-chained log (`fsync` per append, so an abandoned run is abandoned on disk) and the effect table someone else counts |
| `adapters/dryrun.py` | 125 | First register: an engine-held per-run step journal. Unwinds by replaying history into the declaring code; declares `unwinds_from_cold_reader = False` |
| `adapters/second.py` | 138 | Second register: records appended to the platform's own chained log, conditional on the expected head. Unwinds as a fold any process can drive; declares `unwinds_from_cold_reader = True` |
| `adapters/live.py` | 151 | Today's component, reached only through the env vars below. Probes, then reports `adapter-unavailable`. The only file besides the env table that names a product |
| `driver.py` | 196 | The run: declare every class first, commit, kill inside an effect or between steps, replay or unwind. The compensating operators are ordinary forward operations that append a reversing row |
| `call.py` | 132 | The minimal call — 29 lines of caller code |
| `conformance.py` | 381 | The 25 cases and 11 assertions every register must pass, and the report the swap proof compares |
| `test.sh` | 148 | The gate: conformance, the swap proof, the deliberate breakage |
| `plan-entry.json` | — | This harness's row, in the shape of `harness/plan.json`'s entries |
| `provenance.json` | — | Which skills, kb ids, research ids and standard this rests on; what is measured and what is claimed |

## The minimal call

| # | What the caller writes | What the platform does without being asked |
|---|---|---|
| 1 | `ADAPTER=dryrun python3 call.py` | selects the register by configuration; no code path chooses one |
| 2 | `envelope("human", run_id, actor)` | stamps the correlation id, the budget ceiling, the idempotency key and the actor onto the same envelope for all four entries |
| 3 | `run.declare(SAGA)` — five steps, each with a class and, where the class admits one, a compensating action | refuses a step with no class (422), a compensable step with no compensating action (422) and an irreversible step with no mandate (403), before the run starts; makes each declaration durable at a head strictly earlier than the effect it covers; derives the compensating action's own idempotency key |
| 4 | `register.unwind_plan(run_id)` | answers what would be unwound and, separately, what no unwind reaches — read before the first effect, not after the last |
| 5 | `run.commit(effect)` ×4 | writes the effect to a table the register never reads, then seals the record against the response a later replay returns |
| 6 | `run.unwind("failed")` | walks the register backwards under one unwinder, runs each compensating action under its own key and timeout, and records `compensated`, `not-required` or `unwind-failed` per record |

Output, identical under both registers apart from the marker line:

| Row | Dry run (engine journal) | Second register (chained log) |
|---|---|---|
| declarations | 5, each durable before its effect | same |
| commits | 4 sealed, the fifth never happens | same |
| `unwind_order` | publish-the-release-note, provision-the-workspace, open-the-incident-ticket, charge-the-card, reserve-the-inventory | same |
| `compensations_in_order` | the four committed steps, in reverse | same |
| world after the unwind | every compensable entity back to 0 | same |
| cancelled mid-flight | same order, reason `cancelled` | same |
| refusals | 422, 422, 403 | same |
| `register_observed` | `engine-step-journal/0.1` | `chained-log-fold/0.1` |

## Env vars for live

| Variable | What it is | Default |
|---|---|---|
| `COMPENSATION_ADDR` | `host:port` of the workflow engine frontend that would hold the register — **Temporal**, gRPC `7233` or HTTP `8233`. PASS.md A6 records it installed with nothing listening (F-a6-02) | unset — live mode is skipped |
| `COMPENSATION_NAMESPACE` | namespace the runs live in | `default` |
| `COMPENSATION_TASK_QUEUE` | queue the workers holding the declaring code poll | unset |
| `COMPENSATION_API_KEY` | credential, when the frontend requires one | unset |
| `COMPENSATION_TIMEOUT_S` | probe and call timeout | `5` |
| `FAIL_OPERATOR` | a compensating operator whose destination will not answer, used to exercise the unwind-failed path | unset |
| `ADAPTER` | `dryrun`, `second` or `live` | `dryrun` |

## What each test proves

| Test | What it proves |
|---|---|
| 1 the 25 conformance cases | the refusals fire before the run (422/422/403 with a rule id), the four entries of T6.2 walk one identical order, a resumed run replays its sealed responses instead of compensating, an interrupted unwind resumes without running a compensation twice, an irreversible effect is unreachable rather than compensated, and no criterion travels on a record, a plan or a failure detail |
| 1 the 11 assertions | `effects_checked=64 > 0`, `undeclared_class_admitted=0`, `records_after_effect=0`, `irreversible_without_mandate=0`, `runs_killed=12 > 0`, `unwind_failed=0`, `unwinds_resumed=1`, `ways_in_covered=4`, and `replayed(28) + compensated(36) = 64`, the effects the killed runs had committed — a corpus in which nothing was killed would exercise no unwind and still exit green (F-a7-03) |
| 1 ordering, counted from outside | for every effect row in the world there is a record declared before that effect and strictly before the record it was sealed into, compared with `head_ordinal` — never with a field the register reports about itself |
| 1 the world, not the record | every reversal is counted from the effect table, so "the compensation ran" is observed rather than read off the declaration that promised it (F-a7-04) |
| 1b the minimal call | 29 lines of caller code; the caller names no register, no head and no store |
| 2 the swap proof | 25/25 before and 25/25 after, the sha256 of `interface.py`+`call.py`+`conformance.py`+`driver.py`+`store.py` identical across both runs, five declared axes differing, and one identical unwind order from both registers |
| 3 the deliberate breakage | writing the record with the effect instead of strictly before it on the **second register only**: `records_after_effect` goes to 64, `unwind_failed` to 8 — the runs killed between the effect and its record — while `undeclared_class_admitted` and `irreversible_without_mandate` stay 0, the first register fails nothing of its own, and `adapters_run` still reports 2. A run that failed both, or neither, would not have tested the binding |
| 4 `--live` | skipped with a message when `COMPENSATION_ADDR` is unset. Pointed at `127.0.0.1:7233` on this host it returns a typed 503 (`nothing listening`), which is F-a6-02 observed rather than quoted |

## What would pin, and how the adapter boundary avoids it

| The pin (blueprint) | How this harness avoids it |
|---|---|
| `state_types[32]`: "Pins to an engine's saga primitive if compensation is that engine's API" | the interface names a class, a compensating action, two heads and a reverse walk; no engine primitive, no worker registration, no replay determinism and no server address appears above `adapters/live.py` |
| `gaps[8]` (`compensation-home`): "PASS.md names no component that holds a compensation record or an irreversibility class" | the second register needs nothing that is not already running — PASS.md B3 records the chained log as today's state-persistence adapter (F-b3-17) — so the guarantee does not wait on the engine that is down |
| A second workflow engine as the "second adapter" | it would agree with the first on all three of xc-compensation-implement's axes, and prove a vendor rather than the guarantee. The pair here differs on where the register lives, what must be up to unwind, and what drives the reverse walk |
| The register leaking into a caller's branch | `register_observed` is read from the record that came back and appears only in the report; `call.py` branches on nothing, and the conformance run asserts the two markers differ while the two orders do not |

## What is claimed, not measured

| Claim | Why |
|---|---|
| Live mode | the engine is installed and not listening (F-a6-02); the mapping in `adapters/live.py` has never been run against a listening frontend from here |
| The operation set | `declare_effect` / `seal_effect` / `unwind` / `unwind_plan` are xc-compensation's proposed calls: the saga / compensating-transaction pattern is prior art, not a specification, so there is no published contract to conform to |
| `compensation-unresolved` | the type an unresolved unwind should carry is proposed and unregistered; this harness returns the registered `adapter-unavailable` (503, retryable) with the failed records in `causes` and names the proposed type in the detail |
| The dry-run register | it plays the engine's execution model in process, because the engine's server is down; the axis it declares (`unwinds_from_cold_reader = False`) is real and asserted, but no hosted engine answered it here |
