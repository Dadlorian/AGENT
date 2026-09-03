# Dispatch harness — one unit executes and returns one result, planned and judged

One document is planned as a pure call, dispatched as one unit through the seam,
and graded against the document's definition of done as a pure call — and the
plan digest and the verdict are the same whichever dispatcher ran the unit.

PASS.md records Dispatch as one of the two boundaries with no standard to adopt
(F-b5-01), states the unit — *one unit of agent work executes and returns one
result* (F-b5-02) — and records that today there are three implementations and no
contract between them (F-b5-03). This harness is one contract in front of them.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/dispatch/test.sh` |
| 2. Watch the call | `ADAPTER=dryrun python3 harness/dispatch/call.py` |
| 3. Swap the dispatcher | `ADAPTER=second python3 harness/dispatch/call.py` |
| 4. Read the steps back | `python3 -c "import sys; sys.path.insert(0,'harness/dispatch'); from interface import load_dispatcher; [print(s) for s in load_dispatcher('dryrun','harness/dispatch/out/call-dryrun').read_step('dsp-checkout-500s')]"` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 269 | The capability interface: `DispatchRequest`, `DispatchResult`, `Output`, `Usage`, `StepRecord`, the entry `Envelope`, the closed problem registry, `load_dispatcher`, and `Dispatcher` with `dispatch`, `cancel`, `resume`, `replay`, `read_step`. No product name |
| `core.py` | 318 | The two core components: the **Planner** (`plan`, `price_step`, `explain`) and the **Judge** (`judge`, `resolve_criterion`, `criterion_hits`). Both pure. The cost inputs are read at a pinned head in one of two read modes. The validator, the agent registry, the step tree and the criterion bodies are imported from `examples/end-to-end/run.py`, not restated |
| `schemas/dispatch-request.schema.json` | — | The request, published as a file so a shim validates against one copy of the contract instead of hand-writing field checks |
| `fixtures/document.json` | — | The document: what to do, plus a definition of done that names the criterion **by handle** |
| `fixtures/cost-observations.jsonl` | — | 48 measured cost observations, hash-chained so a head names a prefix. `fixtures/heads.json` names the full head and an earlier head at which one selector has no row |
| `adapters/steplog.py` | 70 | The state seam the dispatcher writes step records through: append-only, hash-chained, `fsync` per append. Every append returns the head an output carries as `recorded_at_head` |
| `adapters/base.py` | 440 | What every dispatcher does the same way: the guarantee chain in one fixed order, the step walk, resume, replay, the conflict. The shims supply only `execute_unit` |
| `adapters/dryrun.py` | 58 | Dry-run dispatcher: a session held open for the life of the unit, cancel probed after every checkpoint. `session_held` / `mid_call` |
| `adapters/second.py` | 100 | Second dispatcher: submit one job, poll for one terminal result, in a real second process. `request_response` / `none` — it cannot be stopped once started |
| `adapters/live.py` | 115 | Today's path, reached only through the env vars below. Probes, then reports `adapter-unavailable`. The only file besides the env table that names a product |
| `call.py` | 122 | The minimal call: 19 lines of caller code below the `>>> CALLER CODE` marker |
| `conformance.py` | 474 | The 33 assertions every dispatcher must pass, the migration counter, the caller measurement, the product scan, and the three deliberate breakages |
| `test.sh` | 140 | The gate: the minimal call, conformance, the swap proof, three breakages, and the repair |
| `provenance.json` | — | Which skills, kb ids, research ids and standard this rests on; what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of the entries in `harness/plan.json` |

## The minimal call

| # | What the caller writes | What the platform does without being asked |
|---|---|---|
| 1 | `ADAPTER=dryrun python3 call.py` | selects the dispatcher by configuration; no code path chooses one |
| 2 | `build_request(envelope, document)` | stamps the correlation id, the budget ceiling, the idempotency key and the actor onto the request, and carries the criterion as a **handle** |
| 3 | `core.cost_inputs_at(head)` then `core.plan(document, head, cost_inputs)` twice | folds the cost observations at one pinned head into a table of floors and worst cases; the plan is a pure function of the three values |
| 4 | `dispatcher.dispatch(request)` | validates against the published schema, claims the idempotency key, verifies the delegation chain, records the policy decision, takes the budget reservation, and only then executes — in that order, before the first metered call |
| 5 | `core.judge(result.summary, criterion)` | resolves the criterion out of band; the verdict names check ids and never criterion text |

Output, identical under both dispatchers apart from the marker:

| Row | Dry run | Second dispatcher |
|---|---|---|
| plan run 1 / run 2 | `sha256:4bce5f723c26…` / identical | same |
| plan the dispatcher admitted on | `sha256:4bce5f723c26…` | same |
| dispatch | `completed / end_turn`, 9 outputs, every head recorded | same |
| usage | 551800 micros, 8 steps executed | same |
| judge | `pass` (2 checks) | same |
| marker | `session-held-inprocess/0.1` | `queue-and-poll-oneshot/0.1` |

## Command lines

| Goal | Command |
|---|---|
| Conformance against one dispatcher | `python3 conformance.py --adapter dryrun` |
| The swap, in one report | `python3 conformance.py --adapter dryrun --adapter second --report out/both.json` |
| The seam's breakage | `python3 conformance.py --adapter dryrun --adapter second --break durability` |
| The judge's breakage | `… --break criterion` |
| The planner's breakage | `… --break head` |
| Measure the caller | `python3 conformance.py --caller-lines` |
| Scan for product names outside `adapters/` | `python3 conformance.py --product-scan` |

## Env vars for live mode

Live mode targets the execution path PASS.md Part A records: one **Firecracker**
microVM per agent, started through the **systemd** template unit
`firecracker-cell@.service`, driven over the **Agent Client Protocol** on a vsock
channel, with model egress leaving to the host broker (**LiteLLM**) that holds
the real key. `adapters/live.py` and this table are the only places those names
appear.

| Variable | Meaning | Example |
|---|---|---|
| `DISPATCH_ACP_SOCKET` | the control channel the unit is driven over | `/run/agentic/acp-7.sock` |
| `DISPATCH_UNIT` | the service unit instance that supervises the contained unit | `firecracker-cell@7.service` |
| `GATEWAY_URL` | the host broker a contained unit's model egress leaves through | `http://127.0.0.1:4000` |
| `GATEWAY_KEY` | the scoped key the broker meters against | — |
| `DISPATCH_TIMEOUT_S` | probe and call timeout, default 5 | `5` |
| `ADAPTER` | `dryrun` \| `second` \| `live` — selects the dispatcher | `dryrun` |
| `DISPATCH_PLAN_HEAD` | the head the cost inputs are read at, default the fixture's full head | `sha256:d0e733…` |
| `DISPATCH_OBSERVATIONS` | a working copy of the cost log, default the fixture | `out/cost-observations.jsonl` |
| `DISPATCH_BREAK` | `durability` \| `criterion` \| `head` — the deliberate breakages, so a red run needs no source edit | — |

Run it with `bash harness/dispatch/test.sh --live`. With both unit variables
unset it skips and says so. With one set and nothing listening, the adapter
answers `urn:agentic:problem:adapter-unavailable` (503, retryable) rather than
failing open — which is the only live behaviour measured here.

## What each test proves

| Check | Proves |
|---|---|
| **S1** a malformed request is refused with `document-invalid`, no step recorded | the shape is checked against the published schema before anything else happens, and a refusal costs nothing |
| **S2** cancel is accepted, a terminal state is reached inside `cancel_grace_s` | cancel is acceptance, not a stop; the caller reads until the terminal result |
| **S2** the stop reason matches the adapter's declared reach | the session-held dispatcher reports `cancelled`; the one-shot dispatcher, which cannot be stopped once started, honestly reports `cancel_timeout`. Neither is widened to look like the other |
| **S2** cancelling an already-terminal dispatch returns the result | a late cancel is not an error |
| **S3** the ceiling terminates the unit with `budget_exhausted` and spend `0 < spend ≤ ceiling` | the ceiling stops spend rather than recording it, and the reservation is taken before the metered call |
| **S4** the interrupted run is `partial` with at least one output whose `recorded_at_head` is not null | partial progress is already durable — the seam's central promise |
| **S5** every failure body is `application/problem+json` with a type in the closed registry | `untyped=0`, counted over every refusal the suite provoked rather than the ones someone remembered |
| **S6** resume continues at the first incomplete step, replays 7 committed steps, and carries the earlier spend | a restart is not free money, and committed work is not re-executed |
| **S7** a repeated request returns the recorded result byte for byte, and the step log does not grow | a replay re-executes nothing; measured from outside, not from the run's own tally |
| **S8** the same key with a different body is `idempotency-conflict` | the key is claimed, not merely carried |
| **S9** a delegation hop that widens scope is refused with `policy-denied` before execution | a delegation may narrow and never widen |
| **S10** the policy decision is recorded before the first metered call | the decision is in the enforcement path, not beside it; asserted as an ordering, not as "a checker ran" |
| **S10** the step chain verifies | a resume that trusts an unchained record cannot tell a checkpoint from an edit |
| **P1** two plans of one document at one head are byte-identical | planning is a pure function |
| **P2** `connects_inet=0` under a socket guard | the planner priced from records; it did not sample an estimate |
| **P3** `steps_priced=9` | the identity assertion had a priced plan to assert on |
| **P4** an earlier head with no cost row refuses, naming `fix#1` | a missing row is a refusal, not a default. The body records `proposed_type: urn:agentic:problem:step-unpriceable`, the type this platform would register and has not |
| **P5** `plan_digest_mismatches=0` across the two bindings | scan-and-fold and snapshot-by-digest read the same records and agree byte for byte |
| **J1** 100 gradings of one result give `verdicts_distinct=1`, `checks_applied_min=2` | the engine is deterministic and every grading decided something |
| **J1** in-loop grading applies a proper subset, deterministically | sampling is per grading, not per engine |
| **J2** `requests_scanned=50`, `criterion_hits=0` | design rule 6 made checkable: the criterion appears nowhere in what dispatch carries |
| **J3** `verdict_mismatches=0` across dispatchers | the verdict is a property of the result and the criterion, not of who ran the unit |
| **migrated_paths=3** | all three shims answer the seam's shapes, the live one included on a host where its executor is unreachable |
| swap proof | the same 33 assertions pass before and after, with different markers, different declared `unit_lifetime` and different `cancellation_reach`, `adapters_run=2`, and `call.py` unchanged |
| breakage 4a (seam) | the result is assembled before the state-seam write returns: the targeted dispatcher reports an output whose `recorded_at_head` is null, the run exits non-zero, **the other dispatcher still reports no failure** — the fault is one shim's, and the report says so |
| breakage 4b (judge) | the criterion text is inlined into the document's definition of done: `criterion_hits=100`, and it fails **identically under both engines** while `verdicts_distinct` stays 1 — hiding the criterion is a property of what dispatch may put in a request, not of the engine that grades |
| breakage 4c (planner) | one binding resolves the head itself while a record lands: `plan_digest_mismatches` goes non-zero while **every per-binding assertion stays green** and `connects_inet` stays 0 — which isolates the fault to one loader's wiring rather than to the planner sampling a price |

## What would pin this, and how the boundary avoids it

From `docs/architecture/blueprint.json` (tool entry *firecracker-cell@.service*,
and the impact row for a revision of the agent control protocol):

| Would pin the integration | How this harness avoids it |
|---|---|
| "A field only hardware virtualisation could honour — boot arguments, a block-device layout, a guest kernel" | `interface.py` names a document, ceilings, an isolation *declaration* and a correlation record. The isolation profile is two strings; nothing in the request could only be honoured by a virtual machine |
| An interface that takes an agent rather than a document handle | `dispatch` takes a document and a criterion handle. Which agent profiles the steps use is the document's business |
| A contract that assumes a session can be held open, a callback taken, or a socket reached | the second dispatcher has none of those and passes the same 33 assertions. It is run first after any shape change, so a new dependence fails the day it is written |
| A stop-reason or lifecycle vocabulary invented per executor | both vocabularies are enumerated once in `interface.py`; the five platform endings are decided by the shim, never by the executor |
| An executor that keeps its own journal, its own retry, its own resume state | the step record, the idempotency key and the checkpoint reference are allocated and written by the dispatcher. The one-shot executor keeps nothing and still resumes and replays |
| A caller that can tell which executor answered | `call.py` prints the marker and reads the run back through the interface. It opens no queue, journal or result file of the executor's — `--caller-lines` fails the gate if it names one |

Impact, per the blueprint's impact map: a revision of the agent control protocol
moves every runtime adapter and the dispatch conformance run, which reads the
stop reason; the core is unaffected.

## Deviations from the skills, and why

| Skill text | Here | Why |
|---|---|---|
| `seam-dispatch-implement` asserts `migrated_paths == 3` for the three execution paths PASS.md records | counted as the three **shims** that answer the seam's shapes | F-b5-03 states the count but names none of the three, which the skill itself carries as an open question. What is countable here is the number of shims answering the contract; the counter is honest about what it counted |
| Its definition of done expects `assertions_run=5` per adapter | 33 per adapter | The five it names are all present (S1–S5). This run adds resume, replay, the conflict, the ordering, the chain, and the planner and judge assertions the co-skills require |
| Its invariant expects the identity and typed-error assertions to be **red** on the first run | S9 and S5 are green in this harness | The harness stamps an actor with a delegation chain and types every failure, so its own assertions pass. Against the substrate they are red: PASS.md records no identity field anywhere in the system (F-a6-05) and typed errors as absent (F-a6-06). The assertions stay in the suite and are the ones the live adapter would fail first |
| `core-planner`'s definition of done measures purity with `strace -e trace=connect` | measured in-process by a socket guard that counts and refuses `AF_INET`/`AF_INET6` | The same count, `connects_inet`, taken without a tracer this environment need not have. A planner that reached for an estimate has to open one |
| `core-judge`'s definition of done expects `checks_applied=4` | 2 | The criterion set is the worked example's, imported rather than invented; it carries two checks. `checks_applied_min > 0` is the assertion that matters |
| `seam-dispatch` says a cancel arrives mid-flight | the cancel is registered for the dispatch id before the unit starts | The probe is the same code path — after every checkpoint, never before one — and registering first makes the case deterministic rather than a race. The session stops after its first committed step, which is what leaves exactly one durable partial output |
| `seam-dispatch` carries the parked approval | the approval step's decision rides on the request's declared context | `compose-approval` owns the parked gate and `harness/workflow` exercises it; this harness dispatches a unit rather than parking one |
| `harness/caller_lines.py` is the one method for the caller measurement | measured by `conformance.py --caller-lines`, with the same marker, the same bound and the same storage rule | That script's harness list is fixed and this harness may not edit it. The `>>> CALLER CODE` marker is in place, so adding `dispatch` to its list later needs no change here |
