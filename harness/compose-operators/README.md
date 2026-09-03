# Compose-operators harness — the closed operator set, on two engines

One composition — `examples/end-to-end/workflows/triage-and-fix.json`, which uses
every operator exactly once — driven from one entry envelope through two engines
with different execution models: the interpreted walk that runs today, and a
compiled state machine that reads the tree once before the run and never again.
Same ledger of steps, same loop termination reason, same parked approval and
resume, same agent selection, same verdict; a seventh operator and a loop with
no ceiling are refused before anything is priced or dispatched.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/compose-operators/test.sh` |
| 2. Watch the call | `ADAPTER=dryrun python3 harness/compose-operators/call.py` |
| 3. Swap the engine | `ADAPTER=second python3 harness/compose-operators/call.py` |
| 4. Read the binding report | `python3 harness/compose-operators/conformance.py --engine dryrun --engine second --report out/operators-conformance.json` |
| 5. Break it | `python3 harness/compose-operators/conformance.py --engine dryrun --engine second --break-drift` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 408 | The capability interface: `operator_names` (the closed set, read from the schema and nowhere else), the envelope, the typed problem registry, `Termination`, `ParkedGate`, `RunOutcome`, `Graph`, `Priced`, `ResolvedDefault`, `load_engine`, and `CompositionEngine` — `executor_ops`, `start`, `resume` abstract; `validate_workflow`, `compose`, `to_graph`, `price`, `step_of`, `resolved_default` shared. No product name |
| `adapters/base.py` | 308 | What both engines share: `Stepper`, the leaf effect of an operator, subclassed from the reference runner's `Run` so an agent call, a judge and a ledger record exist once; the park store; the pre-flight budget refusal; the re-typing of the runner's problems into this interface's registry |
| `adapters/dryrun.py` | 195 | The interpreted engine: dispatch table built by asking for one arm per operator name the schema admits, then a recursive walk. `during-walk`, `call-stack-frame`, durable at the gate boundary, failure reported as a tree position |
| `adapters/second.py` | 230 | The compiled engine: the document is lowered once into a static state machine, the transitions are the queue, one committed state row per step. `before-run`, `committed-transition-row`, durable at every step, failure reported as a state and a transition |
| `adapters/live.py` | 73 | Today's component: the same interpreted walk with agent operators dispatched over the model gateway named by the env vars below. Probes first and reports a typed `adapter-unavailable`. The only file besides the env table that names a product |
| `call.py` | 140 | The minimal call: build the envelope, bind one engine, run, park, resume, redeliver, and try two illegal documents. 22 lines of caller code; it opens no ledger, park file or state log |
| `conformance.py` | 426 | The 39 cases every engine must pass and the operator-binding report the swap proof compares |
| `test.sh` | 150 | The gate: the minimal call, conformance, the swap proof, the deliberate breakage, the repair |
| `provenance.json` | — | Which skills, kb ids, research ids and standard this rests on; what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of the rows in `harness/plan.json` |

## The minimal call

| # | What the caller writes | What the platform does without being asked |
|---|---|---|
| 1 | `ADAPTER=dryrun python3 call.py` | selects the engine by configuration; no code path chooses one |
| 2 | `build_envelope()` — kind, entry id, intent, payload | stamps the correlation id, the budget ceiling, the idempotency key and the actor onto the same envelope (F-b4-01) |
| 3 | `engine.start(envelope, workflow, agents)` | validates the document against the operator schema, refuses before pricing if the shortest finishing path exceeds the ceiling, walks or compiles the tree, decrements the budget per step, writes correlation, actor and a per-step idempotency key onto every record, and parks at the approval operator |
| 4 | `engine.resume(gate.gate_id, "approve", "delivery-1")` | applies the decision once on the run's own correlation id; nine redeliveries of the same key are counted and ignored |
| 5 | `engine.start(envelope, bad_document, agents)` | refuses a seventh operator and an unbounded loop with `urn:agentic:problem:document-invalid`, before pricing and dispatch, writing no ledger record |

Output, identical under both engines apart from the marker line:

| Row | Both engines |
|---|---|
| start | 17 steps, parked at `ship-approval`, 1 gate parked |
| resume | 3 more steps, outcome `completed`, decision applied once, 1 redelivery ignored |
| loop | `verdict_pass`, 2 iterations, `unbounded=false` |
| agents | 8 agent steps, each resolving the profile the document declares |
| verdict | `fix-judge#1=fail; fix-judge#2=pass`, spent 551800 micros of 1500000 |
| operators | 6 of 6 exercised: agent, approval, judge, loop, parallel, sequence |
| refused | an operator outside the closed set → `document-invalid`; a loop with no ceiling → `document-invalid` |
| marker | `interpreted-walk/0.1` · `compiled-state-machine/0.1` |

## Command lines

| Goal | Command |
|---|---|
| One engine, all 39 cases | `python3 conformance.py --engine dryrun` |
| Both engines, one report | `python3 conformance.py --engine dryrun --engine second --report out/both.json` |
| The deliberate breakage | `python3 conformance.py --engine dryrun --engine second --break-drift` |
| The live engine's refusal | `ADAPTER=live python3 call.py` |
| Live mode | `bash test.sh --live` |

## Env vars for live mode

Live mode dispatches an agent operator through the model gateway PASS.md B3
records as in place — **LiteLLM** at `$GATEWAY_URL`. The operator vocabulary,
the schema, the documents and both other engines never name it.

| Variable | Meaning | Example |
|---|---|---|
| `GATEWAY_URL` | base URL of the OpenAI-compatible gateway | `http://127.0.0.1:4000` |
| `GATEWAY_KEY` | scoped key the gateway meters against | — |
| `GATEWAY_TIMEOUT_S` | probe and call timeout, default 5 | `5` |
| `ADAPTER` | `dryrun` \| `second` \| `live` — selects the engine | `dryrun` |

With `GATEWAY_URL` unset, `test.sh --live` skips and says so; `ADAPTER=live
python3 call.py` exits 2 with `urn:agentic:problem:adapter-unavailable` (503,
retryable) rather than failing open. That refusal is the only live behaviour
measured here.

## What each test proves

| Check | Proves |
|---|---|
| A1–A3 the set is read from the schema, and the running engine dispatches exactly it | the operator set is written once. A set written twice drifts silently, because each copy is internally consistent |
| A4 the document validates with 0 errors | the closed set is closed by the imported validator, not by hand-rolled field checks |
| B1–B2 parked, then completed | the approval operator stops the run rather than deciding for the human |
| B3 all six operators exercised by one document | build-definition-of-done's finding: a large suite that never reaches two operators reports success having checked nothing about them |
| B4 ten deliveries, one resume | the gate-scoped delivery key deduplicates redelivery |
| B5–B6 every record carries correlation, actor, budget and its own step key | the four guarantees attach to the operator, not to the caller's document; a run key alone would deduplicate a whole submission, and a restart mid-composition needs the step |
| B7 the marker on every record is the running engine's | a swap that never happened is visible; two green runs of one engine read like a proven swap otherwise (F-a7-04) |
| B8–B9 agent selection and verdicts | the step names a profile and never a model; the judge grades against a criterion held outside the document |
| B10–B11 loop termination and budget decrement | `verdict_pass`, 2 iterations, `unbounded=false`, spend rising step by step from the entry ceiling |
| C1–C2 the iteration ceiling escalates | a cap is a typed failure that goes to a human, not a quiet completion |
| C3 criterion leaks = 0 | the sentinel criterion body and its handle reached nothing the graded unit could read, over 7 agent turns |
| C3b the verdict travelled where the criterion did not | the retried step saw `previous_verdict` and never the criterion |
| C4 the budget ceiling terminates the unit | the third and last loop termination reason |
| C5 no fourth reason | every termination named one of the five values in the closed vocabulary |
| C6 the failure landed where the engine declares it can report one | a tree position on one engine, a state and a transition on the other; neither is widened to look like the other |
| D approve / edit / reject / return_with_notes | four decisions; reject stops before the step after the gate; return re-enters the named step exactly once, parks again, and completes on the second decision |
| E a seventh operator and an unbounded loop | refused with a typed problem before pricing and dispatch, with no ledger file written; the chained-call form refuses the same operator and names the step |
| F1 graphs identical | the graph built from the document equals the graph built from the chained-call form of the same composition |
| F2 the depth bound is checked at resolve | `depth_bound_checked_at=resolve`, naming the step that would nest past it |
| F3 reconcile | every parent's estimate is the sum of its children's, and the root total equals the imported planner's flat total |
| F4–F5 `step_of` and `resolved_default` | control flow readable without the work; every value names exactly one layer it came from |
| G1 no engine name or endpoint in any document | the markers are read from the adapter classes, so the check cannot go stale against a renamed engine |
| G2 every failure body is a registered row | no untyped failure reached a caller |
| swap proof | the same 39 cases pass on both engines, with distinct markers read from the running engine, identical step order, identical terminal outcome, and nothing else moved; all four declared axes differ |
| breakage | registering one operator arm the schema does not admit fails the run on the binding alone: `drift=["branch"] engine=interpreted schema_ops=6 executor_ops=7`, while the compiled engine reports `drift=0` — which localises the fault to one engine's wiring rather than to the vocabulary |

## What would pin this, and how the boundary avoids it

`docs/architecture/blueprint.json` has no `tool_entries` row for composition
operators — the component here is the workflow runner in
`examples/end-to-end/run.py`. The nearest rows are the two capabilities a
composition rides on, and their `would_pin` lines are what this harness has to
avoid.

| Would pin the integration | How this harness avoids it |
|---|---|
| The operator set written in the executor as well as in the schema (the defect the interpreted engine has today) | the dispatch table is built by asking for one arm per name the schema admits; `executor_ops` is read from the engine's own inventory and compared, so a set written twice is a failing check rather than a silent door |
| Blueprint, durable execution: "a contract mentioning deterministic workflow code, worker registration or an event-history format" | `interface.py` names a step, an operator, a termination, a parked gate and a problem. Where progress lives and what makes it durable are *declared attributes* of an engine (`progress_unit`, `durable_at`), asserted by the conformance run rather than required by the contract |
| Blueprint, human interaction: "a gate whose deciding subject is whoever happens to hold a screen" | the gate is a record with an id, a correlation id and a declared decision set; a decision is one call with a delivery key, and ten deliveries resume once |
| A document that names an engine, an endpoint or a vendor | `G1` greps every document under test against the markers read from the adapter classes; the schema and the documents are unchanged between engines, which is the property under test rather than a convenience |
| A failure contract written in tree positions | the locus is `{path}` on one engine and `{state, transition}` on the other, and both are asserted against the engine's own declaration; the termination reason and the step id are what the swap proof compares |
| A caller that can tell which engine answered, or knows where it keeps its state | `call.py` prints the marker it read back, opens no ledger, park file or state log, and is byte-identical across the swap |

Per the blueprint's impact map, replacing the durable executor touches the
durable-execution adapter and the crash-and-resume run and leaves the core
alone; this harness is the same claim one layer up — replacing the *engine*
under a composition moves an adapter module and nothing in the document.

## Deviations from the skills, and why

| Skill text | Here | Why |
|---|---|---|
| `compose-operators` prices a nested plan and asserts `reconcile=ok` against declared per-operator cost contributions | reconciliation is asserted against the fold of the imported planner's leaf estimates (`F3`) | No cost declaration per operator exists in this repository yet; stage 4 of the migration is the only stage that needs a schema change. The leg that can be measured is measured, and the missing one is named rather than reported green |
| `compose-operators` gives the parallel operator a `tolerate` member and a `tolerate_exceeded` termination | the vocabulary carries both; no run produces `tolerate_exceeded` | The example's schema has no `tolerate` member, which that skill records as an open question. The reason is admitted by the closed vocabulary and never emitted, so a defect has nowhere to hide |
| `compose-operators` requires `view` on the approval operator | the example's schema requires `asks`, `decisions` and `returns`, and the document carries no `view` | The document and the schema under test are the ones this repository ships; changing them to fit the skill would have made the engine-independence result a result about a document nobody runs |
| `compose-agent`'s criterion check counts leaks into files, environment, tool list and prompt | counted from what the dispatch adapter was handed — task, input and declared tools — over 7 agent turns | A leak is counted from outside the unit. **Measured finding:** the criterion body *does* reach the ledger, because the imported judge writes its reason (`missing ['<token>']`) into the record. `C3c` asserts that rather than asserting it away: it is a leak into the audit record, not into anything the graded unit can read, and fixing it means changing what `run.py` records |
| `compose-loop-implement` asserts a crash mid-iteration resumes at iteration 3 with 0 iterations replayed | not asserted | Crash-and-resume is the durable-execution harness's proof (`harness/workflow`), which runs a real `kill -9`. This harness parks and resumes at the gate boundary, which is the seam the operator vocabulary owns |
| `compose-approval-implement` asserts an expired gate and a late decision | not asserted | The deadline sweep belongs to `cap-scheduling` and is exercised in `harness/workflow`; the operator here declares the decision set, and the gate's deadline is not a field of the example's approval operator |
