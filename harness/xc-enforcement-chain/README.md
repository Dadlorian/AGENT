# Enforcement-chain harness — one ordered chain, four doors, two places it runs

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/xc-enforcement-chain/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/xc-enforcement-chain/call.py` |
| 3. Swap the enforcement point | `ADAPTER=second python3 harness/xc-enforcement-chain/call.py` |
| 4. Prove the chain held | `python3 harness/xc-enforcement-chain/conformance.py --adapter dryrun --adapter second --min-units 100` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 403 | The capability interface: `Unit`, `SlotRecord`, `ChainContext`, `Problem`, the closed `DECLARED_SLOTS` in their one order, `CONCERNS`, `OWNERS`, `evaluate`/`slot_rows`, `EnforcementChainAdapter` with enter, exit, meter and traverse, `drive` and `attest`. `enter`, `exit` and `meter` are concrete, so no binding can shorten the chain, reorder it, skip the inverses, or let a metered call with no context go uncounted |
| `units.py` | 60 | The corpus: 26 units per door × 4 doors = 104, read from `examples/end-to-end/entries/*.json`. Index 1 is the unit whose ceiling cannot cover one metered call, index 2 reuses index 0's idempotency key for a different body, the rest are plain |
| `edge.py` | 57 | The admitting process: the same chain, run as a process the traffic must cross, one request per line |
| `adapters/dryrun.py` | 51 | The chain in the process that constructs the unit — the shape of the three points that already refuse on this host, joined by one shared context. No network. Failure path on `CHAIN_FAIL=1` |
| `adapters/live.py` | 133 | Today's points reached only through environment variables: the approval unit at admission, the decision engine, the gateway's scoped key, the host broker at the call. Product names live here |
| `adapters/second.py` | 109 | The out-of-process point: a child process over a pipe, or the operator's admission endpoint when `CHAIN_EDGE_URL` is set. Refuses anything arriving with a context it did not issue |
| `call.py` | 118 | The minimal call. 34 lines below the `>>> CALLER CODE` marker, counted by `harness/caller_lines.py` |
| `conformance.py` | 307 | The 13 cases every enforcement point passes, the report the definition of done asserts on, and the product-name scan |
| `test.sh` | 187 | The gate: 36 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of the entries in `harness/plan.json`, for the orchestrator to merge |

## The chain

| seq | Slot | The concern a caller hears about | Owner running here | Inverse (run in reverse on exit) |
|---|---|---|---|---|
| 0 | `identity.resolve` | identity, and the tenancy principal it carries | no — `F-a6-05` | `identity.release` |
| 1 | `policy.decide` | policy, including a cross-principal refusal | no — `F-a6-04` | `policy.record` |
| 2 | `budget.reserve` | budget, including a per-principal ceiling | yes — `F-a4-07` | `budget.settle` |
| 3 | `telemetry.open` | correlation, stamped onto every record | yes — `F-a1-05` | `telemetry.close` |
| 4 | `idempotency.claim` | idempotency | yes — `F-a5-03` | `idempotency.release` |
| 5 | `provenance.open` | correlation, carried into the provenance statement | yes — `F-a5-04` | `provenance.seal` |

Tenancy is not a seventh slot and correlation is not an eighth: the principal is bound at `identity.resolve` and refused at `policy.decide` and `budget.reserve` (xc-tenancy), and the correlation is stamped by `telemetry.open` and carried into `provenance.open` (xc-correlation). A slot whose owner is not running here records a no-op with its reason and is counted as `slots_noop_by_absent_owner`; a slot that reports `passed` with no owner running is a link that fails open and is counted as `fail_open_slots`.

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = BINDINGS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three enforcement points by configuration, not by code |
| `adapter.enter(point, unit, parent=ctx)` | Crosses one point. Six slots, one declared order, no argument in which to pass an order, a subset or an exemption. Returns a chain context or raises the first slot's refusal |
| `adapter.meter(unit, ctx)` | The only thing that spends. With no context for the call point it is counted as `ungated_metered_calls`, and refused outright where the point is outside the process |
| `adapter.exit(ctx, "passed")` | Unwinds every slot's inverse in the reverse of the entry order, on the refused path as well as the passing one |
| `attest(adapter, units)` | The report: counts per door and per point, `adapter_observed` read from the refusal that came back |
| `except Problem as refusal:` | One refusal shape for the whole chain, branched on `type`, never on prose |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `CHAIN_FAIL` | unset | `1` makes the in-process chain unreachable, to see the typed failure |
| `CHAIN_EDGE_DOWN` | unset | `1` makes the admitting process unreachable: a refusal, never a bypass |
| `CHAIN_FAIL_OPEN` | unset | A slot name; that slot reports `passed` with no owner running, so the detection can be seen failing |
| `CHAIN_EXAMPLE_DIR` | the repo's `examples/end-to-end` | Where the four door fixtures are read from; the gate's breakage run relocates the tree and points this at the same corpus |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `APPROVE_URL` | yes | The whole URL of the approval unit that parks a workflow at the admission point (PASS.md A2 records `approve.service` on a private address; no path or payload is on file, so none is invented) |
| `BROKER_SOCKET` | yes | The host-side broker the call point exchanges for a scoped credential (PASS.md A3: the broker holds the real key and drops model and destination overrides by name) |
| `GATEWAY_URL`, `GATEWAY_KEY` | for the budget slot | The model gateway's scoped virtual key with a hard cap, which terminates spend rather than recording it (PASS.md A4) |
| `POLICY_URL` | no | The decision engine's decision API. Unset is the state PASS.md A6 records: present, not on the enforcement path, so the slot records a no-op |
| `IDENTITY_URL` | no | Nothing serves this on the host today (PASS.md A6: no identity field anywhere) |
| `TELEMETRY_URL`, `STATE_URL`, `EVIDENCE_URL` | no | The trace backend, the hash-chained task store and the append-only evidence store, each supplied whole by the operator |
| `CHAIN_EDGE_URL`, `CHAIN_EDGE_TOKEN` | no | The operator's own out-of-process admission endpoint for `adapters/second.py`. Unset means the same program runs as a child process |
| `CHAIN_TIMEOUT_S`, `CHAIN_EDGE_TIMEOUT_S` | no | Per-request timeout in seconds, default 30 |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | 13/13 cases, `units_checked=104 metered_units=96` | The chain was attested over more than a hundred units and something was actually metered, so the assertions had something to assert on |
| 1 | `slots_missing=0 out_of_order=0 missing_inverse=0` | Every point crossed carried all six slots in the declared order, and every slot was unwound in reverse on exit, refused units included |
| 1 | `ungated_metered_calls=0 chain_context_missing=0` | No unit reached a metered call without a chain context for that point |
| 1 | `ways_in=human,event,schedule,external points=admission,dispatch,call` | All four of TARGET T6.2's entries and all three points were covered by one chain |
| 1b | Caller code is 34 lines, under 40, and names no storage | One call is one call, measured by `harness/caller_lines.py`, the one method the harnesses share |
| 1b | Four doors, one first refusal: `budget-exhausted` 402 at `budget.reserve` | The same chain applies the same checks in the same order whichever door the envelope came through |
| 1b | `ungated_metered_calls=1` after a caller skipped the chain | A caller cannot skip a link: what it can do is be counted doing it, and be refused where the point is outside the process |
| 1b | `fail_open_slots=3` under `CHAIN_FAIL_OPEN`, `0` in the honest run | A link that fails open is detected rather than reported as passed |
| 1b | Identical `chain records digest` from both points | The two enforcement points produce the same records, so a swap is comparable rather than plausible |
| 1c | `CHAIN_FAIL=1` and `CHAIN_EDGE_DOWN=1` exit 2 | Both failure paths are typed problem details; the out-of-process point's absence is a refusal, never a bypass |
| 2 | Same conformance before and after, same tree hash | The swap is configuration: no code changed between the two runs |
| 2 | `axes_differing=3` | Locus of traversal, processes required for progress and reach over unmodified workloads all differ, so the swap tests the placement and not a library |
| 2 | `slots_noop_by_absent_owner=592` on both | Three hollow slots are reported as hollow on both points, never as passed |
| 3 | `product_hits=0` | No product name outside `adapters/` and the table above |
| 4 | One door unbound: `chain_context_missing=26` and `ungated_metered_calls=26` for `event` alone, `0` for the other three, `units_checked=104`, `adapters_run=2` | The criterion can fail, and it fails by naming the one door that lost its binding rather than by going red everywhere |
| 4 | 26 unbound calls still spent in process, all refused out of process | The pair fails for different reasons, which is what makes the second point worth having |

## What would pin us, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| "A decision input that is a Rego document, or an engine that is consulted only in a conformance check and not in the path — which is the state today" (policy tool entry) | The slot takes a unit and returns `passed`, `no-op` or `refused` with a registered problem; no policy language crosses the interface. The engine being off the path is recorded as a no-op with its reason and counted, not rendered as a pass |
| "A credential path that assumes a host process and a vsock, which a hosted sandbox with no host broker could not serve" (broker tool entry) | The call point is a slot in the chain, not a socket: `adapters/second.py` serves the same slot from a process the traffic crosses, and `adapters/live.py` is the only file that knows a socket exists |
| "An ask that is a message on one surface rather than a record; or a gate whose deciding subject is whoever happens to hold a screen" (approval tool entry) | Admission is a point with a chain context and a sealed record, not a conversation; the context is the platform's state and outlives whatever surface answered |
| "A request field that names a vendor, a member model or an endpoint" (gateway tool entry) | The budget slot reads a ceiling and an estimate off the unit. No routing vocabulary, key or endpoint appears in `interface.py`, `call.py`, `units.py`, `edge.py` or `conformance.py` — checked by the product scan |
| A chain that only exists where we wrote the code | The second point runs beside the workload and refuses anything it did not issue a context for, which is the only way an agent runtime or a tool server we did not write gets chained |
