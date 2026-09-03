# Harness: evaluation

Capability: evaluation. Standard: none adopted - the case-set, replay and verdict
shapes are this repository's design; the research records behind each are cited in
`provenance.json`. One corpus, replayed with every external effect served from the
record, scored over the ordered trace, and a gate that cannot call an empty run green.

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface only: `Case` and its stub policy, `CaseSetHandle`, `Trajectory`, `CaseVerdict`, `EvaluationReport`, `GateStageResult`, RFC 9457 problem details and their closed registry, the scoring rules, the three-valued outcome, the two schemas, and the abstract adapter with `register_case_set`, `evaluate`, `replay_case`, `score_trajectory`, `promote_baseline`. No product name. |
| `adapters/dryrun.py` | Deterministic, in-process, no network. Serialises on the way in and parses on the way out, so a read crosses a real boundary. Exercises the refusal path. |
| `adapters/live.py` | Today's component - the trace backend every run already lands in - reached only through the env vars below. `urllib` under a guarded import; per-case verdicts leave as `gen_ai.evaluation.result`. |
| `adapters/second.py` | A test-runner-shaped harness with no collector and no server: cases, records, baselines and reports are files, and a verdict is an assertion. |
| `corpus/` | The registered corpus as data: six cases (three recorded, three synthetic), the recorded runs their effects are served from, the rubric bodies, and the stored baseline. `case-set-unrecorded.json` is the probe whose effect the record does not hold. |
| `unit_under_test.py` | The thing being scored, not part of the interface: a release reviewer at `1.4.0`, and at `1.4.1-rc` with the diff call dropped before answering. |
| `call.py` | The minimal call. The caller writes an intent and a payload; the platform stamps the rest, registers the corpus and reads the gate off the report. |
| `conformance.py` | The same 22 cases against any adapter, plus `--merge` for the swap proof and `--break-gate` for the breakage. |
| `test.sh` | The gate. Dry-run is measured here; `--live` is skipped with a message when the env vars are unset. |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb and research ids, and what is measured versus claimed. |
| `plan-entry.json` | This harness's row, in the shape of the entries in `harness/plan.json`. |

## The minimal call

| Step | Command or code |
|---|---|
| Run it | `ADAPTER=dryrun python3 harness/evaluation/call.py` |
| Swap the harness | `ADAPTER=second python3 harness/evaluation/call.py` — configuration only, no code edit |
| What the caller writes | `enter(kind="human", intent={...}, payload={"unit": "agent:release-reviewer@1.4.1-rc", "case_set": "cs-release-review", "baseline": "bl-2026-08-27", "case_filter": None})` — 23 lines below the `>>> CALLER CODE` marker, counted and asserted under 40 by `harness/caller_lines.py` |
| What the platform stamps, unasked | correlation id, budget ceiling **and a per-case ceiling** (a corpus is the cheapest way to spend a budget by accident), idempotency key, actor subject |
| What it does | registers one case set, replays one recorded run per case with effects served from the record, scores each trajectory, compares to the stored baseline, and reads the gate stage off the report's counters |
| What comes back | one report, or one problem object — never both, never a third kind |
| The proofs it prints | `PROOF: the verdict names cs-r2 - tool_use pass -> fail while task_completion still passes` and `PROOF: a gate cannot report success with every case skipped - cases_executed=0, outcome=inconclusive` |

## The three-valued outcome, and why the third value exists

| cases_executed | any case failing | outcome | gate status | promotion |
|---|---|---|---|---|
| 6 | no | `passed` | `passed` | allowed |
| 6 | yes | `failed` | `failed` | blocked |
| 0 | — | `inconclusive` | `inconclusive` | blocked |
| no report at all | — | — | `skipped` | blocked |

`GateStageResult.status` is copied from `cases_executed` and `outcome`. It is never
derived from an exit code, because a stage that skipped everything exits zero.

## Env vars for live

| Variable | Required | Meaning |
|---|---|---|
| `EVAL_TRACE_URL` | yes | Ingestion endpoint of `observe-langfuse-web-1` (Langfuse, trace UI and ingestion API — PASS.md A1) that case sets, reports and per-case verdicts are written to |
| `EVAL_TRACE_QUERY_URL` | yes | The read-back surface; `run_ref`, `case_set_id`, `baseline_id` or `report_id` is appended as a query parameter |
| `EVAL_TRACE_KEY` | yes | The credential value that endpoint expects |
| `EVAL_TRACE_AUTH_SCHEME` | no | `Bearer` by default; set `Basic` where the deployment authenticates that way |
| `EVAL_TRACE_TIMEOUT` | no | Seconds, default 10 |
| `EVAL_CASE_SET_ROOT` | no | Where rubric bodies are resolved from, default `harness/evaluation/corpus`. Rubric bodies deliberately never travel to the trace store, because the unit under test reads its own traces |
| `EVAL_FIXTURE_ROOT` | no | Second adapter: the fixture root, default `harness/evaluation/out/fixtures`. No process, no port, no credential |
| `ADAPTER` | no | `dryrun` (default), `live`, `second` |

## The adapter pair

| Adapter | Execution model | Trajectory source | Verdict carrier | Role |
|---|---|---|---|---|
| `dryrun` | In-process object store, deterministic, no network | In-memory record | declared present | Runs here so the whole interface, including the refusal path, is exercised with nothing installed |
| `live` | Collector-backed: a trace store, a worker and a columnar database must be running | Trace backend read back over HTTP | `gen_ai.evaluation.result` per case | Today's component: the store every run already lands in. Cannot score a run whose trace never arrived, and cannot answer in a checkout with nothing running |
| `second` | **No server at all**: a filesystem | Fixture file | declared **absent**, rather than false-with-an-asterisk | The second adapter. Chosen for having nothing running, not for being a different evaluation product of the same shape; an operation shaped around a live trace stream fails here outright rather than degrading |

## What each test proves

| Test | What it proves |
|---|---|
| 1. conformance against `dryrun` | 22/22 cases: a corpus of six registers with a stable content digest; the six execute; `outcome == passed` and `transitions == 0` at the pinned baseline version; the candidate fails with exactly one transition and it is **named**; two effects are served from the record and none executed; an effect the record does not hold is refused with `422 unrecorded-effect`; no rubric marker reaches the unit; a report pins the unit version beside the corpus digest; a promoted baseline is appended and the previous one is still readable. |
| 1b. the minimal call | 23 lines of caller code, under 40, naming no file in an adapter's own storage (`harness/caller_lines.py`). |
| 2. the minimal call, both adapters | The caller's tables and both PROOF lines are identical whichever harness answered, so nothing downstream can tell them apart. |
| 3. swap proof | The identical registered corpus through `second`, selected by `ADAPTER=`; the sha256 of `interface.py`, `call.py` and `conformance.py` is unchanged between the two runs; the merged report shows `adapters_run == 2`, `verdict_divergence == 0`, `selected_by == configuration`, and the pair differing on all three declared axes (`execution_model`, `trajectory_source`, `emit_evaluation_result`). |
| 4. deliberate breakage | The gate derives `status` from the exit code instead of the report's counters. Nothing else changes: both harnesses still report `outcome=passed`, `regressed_outcome=failed`, `transitions_named=cs-r2`. The zero-case run is what moves — `status=passed cases_executed=0` — C6 fails identically on both adapters and the run exits 1, which locates the fault in the gate rather than in either harness. This is the structurally-green pipeline of PASS.md A7 reproduced on purpose. |
| 5. the failure path | An unconfigured live adapter exits 2 with RFC 9457 problem details typed from the closed registry; an unregistered type falls back to the registered one rather than being minted. No traceback reaches the caller. |
| 6. the boundary in the source | No product name in `interface.py`, `call.py`, `conformance.py` or the unit under test; the interface carries exactly the five operations and none that executes an effect; a case has a rubric handle and nowhere to put a rubric body. |

## What would pin the integration, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A metric class, a dataset loader or a test-runner decorator in a core signature (`state_types[26].pinning_risk`) | The interface names a case set, a rubric handle, a trajectory and a report. `conformance.py` asserts the operation set is exactly the five; the storage hooks an adapter fills in are not reachable from `call.py`. |
| A verdict that only exists on a running collector | `emit_evaluation_result` is declared per adapter and reported; the second adapter leaves it false and the report a caller reads is byte-identical, asserted as swap check S3. |
| A replay that quietly re-executes an effect | `EFFECT_MODES` has one value, the interface has no execute operation, `executed_effects` is reported and asserted zero, and an effect the record does not hold is refused rather than performed. |
| A rubric readable by the thing being graded | A case carries `rubric_ref` and has no field for a body (asserted); the handle is resolved inside the scorer after the trajectory exists; rubric bodies are never written to the trace store the unit can read. |
| A gate whose status comes from an exit code | `gate_stage` reads `cases_executed` and `outcome`; test 4 breaks exactly this and the run fails. |
| A report that cannot be compared with another | The report pins the unit version beside the corpus digest, and `report_id` is derived from what was scored, so two adapters that agree produce the same id. |
| The trace backend being replaced | The blueprint's impact row for that component reads: affected adapters, the telemetry adapter; affected tests, the conformance run; core unaffected — and lists `cap-evaluation` among the affected skills. That is this harness's test 3. |
