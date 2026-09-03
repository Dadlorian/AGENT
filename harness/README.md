# Harness

`harness/plan.json` lists all 28 harnesses; each directory's `README.md` carries its own step table. This file describes the first five in depth and the caller-line measurement they share.

## The five harnesses

| Harness | Capability behind the interface | Minimal call | Second adapter it swaps to |
|---|---|---|---|
| `containment` | isolation, and the agent turn one contained unit serves | start one contained unit, run one agent turn, cancel it mid-turn, read the stop reason and the containment report | a unit granted capabilities instead of a machine, single-shot, no cancellation |
| `gateway` | model access | one completion by model class under a scoped ceiling; a vendor name in the request is refused | a provider-native asynchronous batch path, claim-and-poll |
| `observability` | telemetry | one trace whose spans carry the run and root dispatch ids, reassembled by grouping and not by parentage | a collector pipeline into a columnar store, no semantic queries |
| `workflow` | durable execution and scheduling | one durable flow: a step, a parked approval, a bounded loop, a crash, a resume at the first incomplete step | a queue plus a state machine, effect committed in the same transaction |
| `linked` | consumption: the one way in, over the other four | one document through all four doors, contained turn, gateway call, traced, orchestrated | all four component adapters at once, and each alone |

## The one command each

| Harness | Command | Last line it prints |
|---|---|---|
| `containment` | `bash harness/containment/test.sh` | `passed 25, failed 0` |
| `gateway` | `bash harness/gateway/test.sh` | `passed 25, failed 0` |
| `observability` | `bash harness/observability/test.sh` | `passed 37, failed 0` |
| `workflow` | `bash harness/workflow/test.sh` | `passed 23, failed 0` |
| `linked` | `bash harness/linked/test.sh` | `passed 32, failed 0` |

## What a caller writes, measured one way

`python3 harness/caller_lines.py` is the only method. It counts the non-blank,
non-comment lines of a harness's `call.py` below its single `>>> CALLER CODE`
marker, up to the module entry guard, and it fails if any `call.py` names a file
in an adapter's own storage. Presentation lives above the marker in all five, so
the number is interface calls, the inputs handed to them, and reading one result
or one problem. Each `test.sh` asserts its own number through the same script,
so no harness reports a count nobody checked.

| Harness | Caller lines | Bound | Adapter storage named in `call.py` |
|---|---|---|---|
| `containment` | 17 | under 40 | none |
| `gateway` | 13 | under 40 | none |
| `observability` | 17 | under 40 | none |
| `workflow` | 21 | under 40 | none |
| `linked` | 18 | under 40 | none |

## Two conventions that keep the five comparable

| Convention | Where it is enforced | What it prevents |
|---|---|---|
| One `>>> CALLER CODE` marker per `call.py`, presentation above it | `harness/caller_lines.py`, called by all five `test.sh` | four spellings of the same marker and two harnesses that measured nothing |
| Every adapter module exports its entry point as `Adapter` | `harness/linked/components.py` binds `module.Adapter` for all four capabilities; `harness/workflow/interface.py` `load_executor` uses the same rule | a per-capability class-name table in the one file that composes them |

## What swapping each component moves

Rows are `docs/architecture/blueprint.json` impact entries. The last column is
what this section actually ran, not what the row predicts.

| Component | Blueprint row | Adapters it names | Tests it names | Skills it names | What the section measured |
|---|---|---|---|---|---|
| trace backend | the trace backend is replaced | the telemetry adapter | the telemetry conformance run | `cap-telemetry-implement` | 37 checks before and after `ADAPTER=second`; in `linked`, `ADAPTER_TRACE=second` alone leaves the other three markers unmoved |
| durable executor | the durable executor is replaced | the durable-execution adapter | the crash-and-resume run, the idempotency lease run | `cap-durable-execution`, `cap-durable-execution-implement`, `compose-loop`, `xc-idempotency-lease` | 28 conformance cases on both executors, distinct executor markers; in `linked`, `ADAPTER_WORKFLOW=second` alone leaves the other three unmoved |
| model gateway | the model gateway is replaced | the model-access adapter, and the batch path | the routing-table run, the ceiling-terminates-spend run | `cap-model-access`, `cap-model-access-implement`, `xc-budget` | 12 cases on the synchronous and the batch path; in `linked`, the class, the ceiling and the spend aggregation hold across the swap |
| isolation | isolation moves from hardware virtualisation to container or workspace-level containment | the isolation adapter, and the mandate adapter | the containment-report assertions, the tenancy noisy-neighbour run | `cap-isolation`, `cap-isolation-implement`, `xc-tenancy`, `cap-mandate-broker` | the report is asserted by the host on both adapters; the second reports `cancel_timeout` where the first reports `cancelled`, and the boundary stops it either way |
| agent runtime | the agent runtime is replaced | the agent-runtime adapter, and the correlation stamping | the cancellation run, the depth-3 correlation run | `cap-agent-runtime`, `cap-agent-runtime-implement`, `xc-correlation`, `seam-dispatch` | negotiated capabilities differ between the pair and the turn still ends; in `linked`, every span carries the run id whichever runtime minted the trace |
| entry envelope | the event envelope specification version moves | every intake mapper, one per producer; the envelope schema | `examples/end-to-end/test.sh` across all four entry fixtures, the entry-conformance suite | `cap-work-intake`, `cap-work-intake-implement`, `cap-consumption`, `xc-correlation` | one schema and four producers in `linked`; the cross-door check fails the moment one door's envelope drifts |
| attribute vocabulary | the GenAI semantic-convention attribute vocabulary is revised | the telemetry attribute-mapping adapter only | the telemetry conformance run, `examples/end-to-end/test.sh` | `cap-telemetry`, `cap-telemetry-implement`, `xc-correlation`, `cap-evaluation` | the mapping version is read back off the wire, not from the configuration that set it |
| local inference engine | the local inference engine is replaced | the model-access adapter for the free local class | the class-routing run | `cap-model-access-implement` | the routing table is data; the class-routing vectors run with no engine present |

## Measured versus claimed

| Harness | Measured here | Claimed until run on the host |
|---|---|---|
| `containment` | 25 gate checks; conformance on both adapters; the boundary destroys the unit on both; no secret inside a unit | the microVM cell and the runtime over its wire protocol; every operation in `adapters/live.py` |
| `gateway` | 25 gate checks; 12 conformance cases per adapter; class routing, the ceiling refusal before dispatch, the vendor-name refusal | the gateway on this host at `GATEWAY_URL`; the provider batch route at `BATCH_SUBMIT_URL` |
| `observability` | 37 gate checks; one group per run over three unrelated trace ids; the breakage reproduces the runtime's own trace behaviour | the trace backend at `TRACE_URL`; the deployed collector at `COLLECTOR_URL` |
| `workflow` | 23 gate checks; 28 conformance cases per executor; a real `kill -9` at the side-effecting step and one effect row after the resume | the workflow engine at `WORKFLOW_ADDR`; its history, workers and task queues |
| `linked` | 32 gate checks; 23 conformance cases per adapter set; one subject and one plan across four doors; four replay no-ops; four typed refusals | every component's live adapter at once; the second client shape build-entry-conformance also requires |

## What is not measured anywhere in this section

| Gap | Where it is recorded |
|---|---|
| live mode, every harness | each `provenance.json`, `claimed` |
| a client generated from a published description document | `harness/linked/provenance.json`, `claimed` |
| standard versions | every `provenance.json` carries `unverified`; STATUS row 14 |
| an internal event that steers an existing run rather than starting one | `harness/linked/README.md`, what this harness does not check |
