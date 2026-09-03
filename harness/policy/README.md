# Policy harness — one decision for one unit of work, before anything is spent

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/policy/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/policy/call.py` |
| 3. See a typed deny | `SCOPE=external python3 harness/policy/call.py` |
| 4. Swap the engine | `ADAPTER=second python3 harness/policy/call.py` |
| 5. Ask both the same question | `ADAPTER=dryrun,second python3 harness/policy/call.py` |
| 6. Prove the interface held | `python3 harness/policy/conformance.py --adapter dryrun --adapter second` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 350 | The capability interface: `DecisionRequest`, `Decision`, `Meter`, `Problem`, and `PolicyAdapter` with decide, activate, explain, register_decision_point, plus `admit` — the gate. `decide` and `admit` are concrete, so no adapter can decline the registry check, the declared-shape check, the version pin, or the order (decide, then the metered call) |
| `decision_points.json` | 28 | The decision point registry: three points and the resource shape each declares. An unregistered point is refused, never assumed |
| `bundle.json` | 61 | The rule set as data, plus the entity model a typed engine can express. The digest of these canonical bytes is the `policy_version` every decision is pinned to |
| `adapters/dryrun.py` | 81 | Open-JSON-document evaluation in process. No network, same answer every run. Failure path on `POLICY_FAIL=1` |
| `adapters/live.py` | 99 | Today's component, reached at `POLICY_DECISION_URL` via `urllib` behind a guarded import. Product names live here |
| `adapters/second.py` | 112 | The second decision model: a typed entity set compiled into the process, deny by default, no network, and a declared conformance subset for what its model cannot express |
| `call.py` | 119 | The minimal call. 19 lines below the `>>> CALLER CODE` marker; everything above it is the platform stamping the envelope and pinning the version |
| `conformance.py` | 311 | The 14 cases every adapter passes, the definition-of-done counters, and the engine-name scan over code |
| `test.sh` | 160 | The gate: 38 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of an entry in `harness/plan.json`, for the orchestrator to merge |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `ask = envelope()` | One entry envelope; the platform stamps correlation id, ceiling, idempotency key, actor and tenant, and pins the policy version, without being asked |
| `request = DecisionRequest.from_dict(ask["payload"])` | The closed vocabulary. A field that would turn the gate off is 422 here, before any engine is reached |
| `for adapter in bindings():` | One name or several, from `ADAPTER`. Configuration, not code |
| `decision, outcome = adapter.admit(request, work_for(ask))` | One decision for the unit of work. The work is reachable only on the far side of an allow, and every metered call it makes is charged through the meter it is handed |
| `except Problem as problem: report(problem)` | One handler for every failure, branched on `type`, never on prose. A deny arrives as `policy-denied` 403 with the rule that fired and `spend_delta_micros: 0` |
| `show(ask, rows)` | Binding, effect, rule_id, policy version, spend, outcome — and `decisions_agree` when more than one engine answered |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live`, `second`, or a comma-separated list to ask several the same question |
| `POINT` | `dispatch.tool_call` | Any registered point: `admission.entry`, `dispatch.tool_call`, `dispatch.data_query` |
| `SCOPE` | `internal` | `external` trips the mandate rule and returns a typed deny |
| `MANDATE` | unset | Puts a mandate on the subject, so the external call is allowed |
| `TENANT`, `RESOURCE_TENANT` | `tenant-acme` | Differ to see the cross-tenant deny |
| `QUERY` | unset | Sends a free-form resource, which the typed-entity binding declares it cannot serve |
| `DECLINE` | unset | Adds a bypass field to the request, to see the refusal |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |
| `POLICY_FAIL` | unset | `1` makes the dry-run decision endpoint unreachable |
| `POLICY_CLOCK` | unset | Fixes `decided_at`, which is never an input to the decision or its digest |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `POLICY_DECISION_URL` | yes | The full decision URL of the policy engine on this host (OPA with Rego today: PASS.md A5 records the policy concern as Rego / Open Policy Agent, PASS.md B3 names OPA as the adapter today). Supplied whole by the operator: no route is invented here |
| `POLICY_TOKEN` | no | Bearer token, if the engine requires one |
| `POLICY_BUNDLE_VERSION` | no | The digest of the bundle the engine actually serves, so a request pinned to it resolves |
| `POLICY_TIMEOUT_S` | no | Per-decision timeout in seconds, default 30 |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 14/14 | The registry, the declared shape, the version pin, the ordering, the typed deny, determinism, explain and the tenancy rule all hold with nothing reachable |
| 1 | `decided_before_first_metered_call == decisions_taken`, `spend_delta_micros == 0`, `rule_id_present` | The three counters `cap-policy-implement`'s definition of done asserts on, measured per adapter |
| 1b | Caller code is 19 lines, under 40, and names no adapter storage | One decision is one call; the stamps are the platform's work. Measured by `harness/caller_lines.py`, the one method the harnesses share, called as a module because its `HARNESSES` tuple is the orchestrator's to extend |
| 1b | `SCOPE=external` exits 2 with `policy-denied` 403 | A refusal is typed, names the rule that fired, and carries `spend_delta_micros: 0` |
| 1b | `DECLINE=1` exits 2 with `document-invalid` 422 | There is no advisory mode, no dry-run flag and no bypass field: the vocabulary is closed, so a caller cannot decline the gate |
| 1b | `RESOURCE_TENANT=…` exits 2 | A tenancy window is refused deterministically before execution, like any other policy decision |
| 1c | `POLICY_FAIL=1` exits 2 with `adapter-unavailable` 503 | The failure path is exercised: no decision means no admission, not a default-allow |
| 2 | Conformance before (dryrun) and after (second), 14/14 each | The interface held across a swap of the decision model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py`, `bundle.json`, `decision_points.json` identical across both runs | The swap was configuration, not a code edit |
| 2 | 4 execution-model axes differ; `decisions_agree=true` over every shared decision | The second engine breaks different assumptions and still returns the same effect and the same `rule_id` for the byte-identical request |
| 3 | `product_hits=0` over the code | No engine, rule-language or vendor name outside `adapters/` |
| 4 | The decision moved after the first metered call, in a copy, on one adapter only | The green run can fail: `decided_before_first_metered_call` falls from 9/9 to 2/9, `spend_delta_micros` on denied dispatches rises from 0 to 2400, the run names the binding that took over the gate, and the untouched adapter is still 14/14 |
| 5 | `--live`: the same 14 cases against `POLICY_DECISION_URL` | Skipped with a message when the env var is unset. Nothing live has been measured here |

## The two adapters behind one interface

| Axis | `adapters/live.py` and `adapters/dryrun.py` (today's model) | `adapters/second.py` (second) |
|---|---|---|
| What the engine reads | an open JSON document | a typed entity set, marshalled before evaluation |
| How a new rule set starts serving | the bundle is swapped in place; the binding keeps running | the entity model and rules are recompiled into the process |
| What must be reachable to decide | the decision endpoint, out of process | nothing; it is a function call in the calling process |
| What it declares it cannot serve | nothing; every registered point is answered | `dispatch.data_query`, whose rule reads a free-form field outside the entity model — declared as a subset and refused 503, never answered allow |
| Swap procedure | `ADAPTER=live` | `ADAPTER=second`; no code edit, same cases, compare the two reports |

The dry-run and live bindings report as the same decision model (`out-of-process-document-query`) because that is the model they evaluate; the dry run runs it in process so a gate can assert on it with nothing reachable.

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:policy-denied` | 403 | A rule denied. Carries `rule_id`, `policy_version`, `input_digest` and `spend_delta_micros` |
| `urn:agentic:problem:document-invalid` | 422 | The request carries a field outside the vocabulary — a bypass flag included — or the resource fails the shape the decision point declares |
| `urn:agentic:problem:decision-point-unregistered` | 422 | No point is registered under that name. A conformance failure, never a default-allow |
| `urn:agentic:problem:policy-version-unknown` | 409 | The pinned version is not resolvable here, so the decision could not be replayed and none was given |
| `urn:agentic:problem:adapter-unavailable` | 503 | No engine answered: the endpoint is unreachable, or the binding declared this point outside the subset it can serve |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A decision input that is a rule-language document | `DecisionRequest` is a closed six-field JSON vocabulary, digested over canonical bytes before evaluation, and the same bytes are put to both engines. Conformance asserts they agree |
| An engine consulted only in a conformance check and not in the path — which is the state today (PASS.md A6) | `admit` composes the decision with the unit of work: the work is only reachable on the far side of an allow, and the ordering is counted, not asserted |
| A caller able to decline the check on a fast path | The vocabulary is closed and `admit`/`decide` are concrete on the interface. A bypass field is 422; a binding that overrides the gate is caught by the conformance run, which is exactly the deliberate breakage |
| A decision that cannot be replayed because nothing recorded which rules were active | Every request pins a `policy_version` digest; an unresolvable version is 409; `explain` re-evaluates the pinned bundle rather than reading a stored narrative |
| An unattributed allow, which leaves "why was this permitted" unanswerable while the refusal path looks healthy | `rule_id` is required for allow as well as deny, and `rule_id_present` is a reported counter |
| An engine answering allow for a decision point it cannot actually express | A binding declares the subset; the declared point is refused 503 with the subset named, and the conformance case asserts a declared subset is not an allow |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 38 checks, 0 failures |
| Live mode against `POLICY_DECISION_URL` | Claimed. The decision URL, the request wrapper and the answer mapping are unverified against a real engine |
| The rule set, the entity model and the three decision points | Proposed fixtures of this harness, not a recorded rule set |
| `adapters/second.py` | A faithful stub of the typed-entity execution model, not a binding to that engine. Its shape, its declared subset and its swap procedure are real; the engine is not linked in |
| The standard, "Rego / OPA decision API" | Version unverified: `OPA 1.0, with Rego v1 syntax available from v0.59.0 onward` is search-sourced, and page fetch is blocked in this environment |
