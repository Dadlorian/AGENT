# Linked harness — one document, four doors, four components

The four component harnesses run as themselves here: imported as modules and
driven through their own capability interfaces. Nothing of theirs is copied,
and no component is named in any file of this harness.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/linked/test.sh` |
| 2. Watch the call | `python3 harness/linked/call.py` |
| 3. Swap every component at once | `ADAPTER_CONTAINMENT=second ADAPTER_GATEWAY=second ADAPTER_TRACE=second ADAPTER_WORKFLOW=second python3 harness/linked/call.py` |
| 4. Prove the interface held | `python3 harness/linked/conformance.py --report out/report.json` |
| 5. See the breakage fail | `python3 harness/linked/conformance.py --break-door-budget` |
| 6. Run against the host | `bash harness/linked/test.sh --live` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 233 | The consumption interface: the entry envelope, the door fields, the resolved plan, one result, one problem from a closed registry, and the two abstract halves (`Entry`, `Platform`). No product name |
| `doors.py` | 116 | The one subject document and the four producers. Every door builds its envelope with the same code, so a door cannot grow a member of its own |
| `components.py` | 142 | How the four component harnesses are reached: one import window per component, an adapter wrapper so a lazy import finds its own package, and the four environment variables that select adapters |
| `linked.py` | 369 | The platform: the ledger a replay is decided against, the pure plan, the one `submit`, the contained turn whose outward call is one completion, and the run read back |
| `call.py` | 83 | The minimal call. 9 lines of caller code between the two markers |
| `conformance.py` | 271 | The 23 cases any set of adapters must pass, and the report the swap proof compares |
| `test.sh` | 140 | The gate: 31 checks in dry run, the swap proof, the one-at-a-time swaps, the breakage |
| `provenance.json` | — | Owner skill, co-skills, kb and research ids, what is measured and what is claimed |
| `out/` | written | Reports, the ledger, the executor journal, per-unit jails, run logs |

## The minimal call

| # | What the caller writes | What the platform did without being asked |
|---|---|---|
| 1 | `place = platform(out)` | Bound four capabilities from four environment variables; nothing downstream branches on which answered |
| 2 | `for door in doors.DOORS:` | Four producers, one envelope shape; `kind` says which door and nothing reads it to decide |
| 3 | `door.envelope(subject)` | Stamped the correlation ids, the delegation chain, the ceiling and the idempotency key |
| 4 | `place.submit(envelope.dict())` | Validated against the published entry schema; refused a replay from the ledger before touching a component |
| 5 | — | Priced the resolved plan as a pure function and refused a ceiling that cannot pay for it, before dispatch |
| 6 | — | Began a durable run, committed three steps, and dispatched one contained agent turn inside one of them |
| 7 | — | Made the turn's outward call one completion by model class, capped at what was left of the ceiling |
| 8 | — | Emitted a span at each of the three levels carrying the run id and the root dispatch id |
| 9 | `if isinstance(answer, Problem)` | One refusal shape for every failure at every depth, branched on `type` and never on prose |

| What comes back | Value at every door |
|---|---|
| subject digest | one, identical across the four doors |
| resolved plan digest | one, identical across the four doors |
| actor / delegation hops | four distinct actors; 1, 2, 2, 3 hops |
| stop reason | `end_turn` |
| spend | the sum of the three step costs, under the one ceiling |
| trace | 1 group on the run id, 3 levels, 3 unrelated trace ids, 0 spans missing the run id |

## How the four are linked

| Layer | Capability interface | What one run does |
|---|---|---|
| door | this harness | one envelope, per-door actor, correlation and key |
| flow | durable execution | `begin_run`, three `checkpoint_step`s, `read_run` |
| turn | isolation and the agent turn | one unit admitted, one session, one prompt, terminate, containment report read by the host |
| call | model access | one completion by class, ceiling = budget remaining, no vendor named |
| trace | telemetry | `bind` at each level, spans at depth 0, 1, 2, one metric |

## Environment variables

| Variable | Default | What it selects |
|---|---|---|
| `ADAPTER_CONTAINMENT` | `dryrun` | `dryrun`, `second` or `live` for the isolation and agent-turn component |
| `ADAPTER_GATEWAY` | `dryrun` | `dryrun`, `second` or `live` for the model-access component |
| `ADAPTER_TRACE` | `dryrun` | `dryrun`, `second` or `live` for the telemetry component |
| `ADAPTER_WORKFLOW` | `dryrun` | `dryrun`, `second` or `live` for the durable-execution component |

Live mode needs every component's own variables at once; each component harness
owns its table. `test.sh --live` skips with the list of what is unset.

| Component | Its live variables (see that harness's README) |
|---|---|
| containment | `CELL_START_CMD`, `CELL_STOP_CMD`, `CELL_JAIL_ROOT`, `BROKER_EGRESS_COUNTERS`, `ACP_STDIO_CMD` or `ACP_SOCKET` |
| gateway | `GATEWAY_URL`, `GATEWAY_KEY` |
| observability | `TRACE_URL`, `TRACE_KEY`, optionally `TRACE_QUERY_URL` |
| workflow | `WORKFLOW_ADDR`, optionally `WORKFLOW_NAMESPACE`, `WORKFLOW_TASK_QUEUE` |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | The minimal call, 4 doors | One document reaches the same resolved plan through a person, an event, a clock and another agent |
| 1b | 9 lines of caller code | The stamps, the plan, the ceiling, the trace and the checkpoints are the platform's work |
| 2 | Conformance, 23/23 | A1–A8 cross-door, B1–B6 linkage, C1–C4 budget, D1–D2 replay, E1–E2 typed refusals, F1 no product name |
| 3 | Swap all four to `second` | The same 23 cases pass with four different implementations and `call.py` byte-identical |
| 3b | Swap one at a time | Exactly one marker moves per swap: the other three components do not notice |
| 4 | `--break-door-budget` | One door with a ceiling of its own fails 4 cross-door checks while every per-door check stays green |
| 5 | Repair | The suite passes again once the door is restored, so the breakage was the defect and not the run |

## What the conformance run measures

| Case | What is asserted | Where the number comes from |
|---|---|---|
| A2, A3 | one subject digest and one plan digest over four doors | the envelopes and the pure plan, compared across doors |
| A6 | the envelopes differ only on `kind`, `entry_id`, `occurred_at`, `actor`, `correlation`, `idempotency_key` | a field-by-field diff of the four envelopes |
| A7 | 1, 2, 2, 3 delegation hops | the chain each door built |
| B1, B2 | one unit per run, marker read from inside it, no secret seen, every egress attempt blocked | the containment report the host asserted |
| B3 | one completion per run and no server named in any result | the gateway's own dispatch counter, and a product scan of the result JSON |
| B4 | three steps committed | the executor's `read_run`, not the run's own tally |
| B5, B6 | 1 group, 3 levels, 3 trace ids, 0 missing ids | the telemetry backend's `fetch_run`, grouped on the run id |
| C1, C2 | spend equals the sum of the nested costs, and the executor agrees | the platform's per-step costs against the executor's own total |
| C3 | the innermost ceiling is the budget remaining | the ceiling handed to the completion request |
| C4 | a ceiling below the plan is refused with 0 spend, 0 dispatches, 0 units, 0 durable records | counters read after the refusal |
| D1, D2 | a replay returns the same result and writes nothing | ledger, dispatch and unit counters before and after |
| E1 | four typed 422 refusals that write nothing | one malformed entry per door |
| F1 | no product named | a regex scan of every `.py` file here |

## What would pin this, and how the boundary avoids it

| If it changes (blueprint impact row) | What it would move here | What absorbs it |
|---|---|---|
| the trace backend is replaced | nothing above the telemetry adapter | `ADAPTER_TRACE`; step 3b measures that only its marker moves |
| the durable executor is replaced | nothing; the contract above it is unchanged | `ADAPTER_WORKFLOW`; the flow is `begin_run`, `checkpoint_step`, `read_run` and no engine vocabulary |
| the model gateway is replaced | the routing table and the batch path | `ADAPTER_GATEWAY`; the caller names a class, and the batch path is the second adapter already proven here |
| isolation moves to container-level containment | the containment report's guarantees weaken | `ADAPTER_CONTAINMENT`; the report is asserted by the host, so a weaker unit shows up in B1 and B2 rather than passing quietly |
| the agent runtime is replaced | the stop reason and trace continuity | the turn is one prompt and one stop reason; every span carries the run id, so a runtime that mints its own trace still reassembles |
| the event envelope specification version moves | every producer and the envelope schema | one schema, four producers, and A6 fails the moment one door drifts |
| the GenAI attribute vocabulary is revised | the attribute mapping only | the mapping version is read back off the wire and reported per run |

## What this harness does not check

| Gap | Why it is stated rather than passed |
|---|---|
| the second client shape | build-entry-conformance drives each door twice, once from a client generated from a published description document. There is no such document here, so the report records `client_shape: raw-script` |
| an internal event that steers rather than starts | the four doors of TARGET T6.2 are covered; the internal-event rule belongs to the intake capability and is not exercised here |
| live mode | claimed, not measured: no component's live adapter has been run against the host from this session |
