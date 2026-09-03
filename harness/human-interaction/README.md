# Human-interaction harness — a run parked on a person, resumed by one decision

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/human-interaction/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/human-interaction/call.py` |
| 3. Swap the surface | `ADAPTER=second python3 harness/human-interaction/call.py` |
| 4. Prove the interface held | `python3 harness/human-interaction/conformance.py --surface dryrun --surface second` |
| 5. Break it on purpose | `python3 harness/human-interaction/conformance.py --surface second --break-client-held` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 425 | The capability interface: `HumanAsk`, `HumanDecision`, `ParkedAsk`, `ResumeAck`, `StreamEvent`, `Problem`, and `HumanSurface` with ask, watch, decide, expire. `ask` and `decide` are concrete, so no surface can decline the deadline, the response schema, the actor, the criterion check or the replay rule |
| `store.py` | 309 | The parked-ask store: platform state, not a surface's. An append-only log; state is a fold over it; a decision's lease and the ask's state transition are one appended record under one atomic lock |
| `run.py` | 105 | The run that parks: draft, gate, publish. `park_run` returns and its object is discarded; `resume_run` is built from the decision alone, so the surface may be gone in between |
| `adapters/dryrun.py` | 63 | First surface, in process: one parked item, request and response, no network. Declares what it cannot do. Failure path on `DRYRUN_FAIL=1` |
| `adapters/live.py` | 111 | Today's component, over HTTP at operator-supplied URLs. Product and host names live here |
| `adapters/second.py` | 131 | Second surface: a streaming client over server-sent events, replayable from a position, renders the run in flight. Also holds `--break-client-held` |
| `call.py` | 158 | The minimal call. 29 lines below the `>>> CALLER CODE` marker, counted by `harness/caller_lines.py`; everything above it is the platform stamping the envelope and the decision |
| `conformance.py` | 512 | The 25 cases every surface passes, the cross-surface resume, and the product-name scan |
| `test.sh` | 127 | The gate: 39 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of the entries in `harness/plan.json` |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `store = ParkedAskStore(fresh(...))` | The parked state, which belongs to the platform and outlives every surface |
| `surface = load_surface(adapter, store)` | Binds one of three surfaces by configuration, not by code |
| `ask = park_run(surface, envelope, T_PARK, "ask-release-0001", DEADLINE)` | Parks one run on an ask with a deadline. The envelope stamps correlation id, ceiling, idempotency key and actor without being asked |
| `ack = surface.decide(edit, T_DECIDE)` | One decision through this surface. `ack.artifact` is what the run continues with — on an edit, the reviewer's body |
| `dup = surface.decide(edit, T_DECIDE)` | The same decision again: `outcome duplicate`, `applied False`. One act, delivered twice |
| `result = resume_run(ack, T_DECIDE, store)` | The run continues, on the correlation id it was parked with |
| `surface.decide(decision(ask, "approve", {}), ...)` | A second, different decision on the same ask → `idempotency-conflict` 409 |
| `surface.decide(decision(late, "approve", {}), T_LATE)` | A decision after the deadline → `deadline-exceeded` 504, ask terminal |
| `except Problem as problem: print(problem.body)` | One handler for every failure, branched on `type`, never on prose |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `second` or `live` |
| `DRYRUN_FAIL` | unset | `1` makes the first surface undeliverable, to see the typed failure path |
| `STREAM_URL` | unset | Points `adapters/second.py` at a real event stream instead of the in-process one (claimed) |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `APPROVE_DELIVER_URL` | yes | Full URL the operator supplies for posting one parked ask to the approval unit on this host. Today that unit is `approve.service` — systemd, enabled, running, bound on a Tailscale address `100.125.65.101:8088`, purpose "Approve / reject / return a parked workflow from a phone" (PASS.md A2, `F-a2-01`); the `approve` and `hitl` Ansible roles configure it (PASS.md A5, `F-a5-01`) |
| `APPROVE_ITEM_URL` | no | Full URL for reading one item back, so the adapter takes the signed-in subject from the unit rather than trusting the body it was handed. Unset: the decision's own actor is used |
| `APPROVE_TOKEN` | yes | Bearer credential for that unit |
| `APPROVE_TIMEOUT_S` | no | Per-request timeout, default 20 |

No route is invented. None of that unit's paths is recorded anywhere on file, so each URL is supplied whole by the operator, and the harness address above is never assumed by the interface — the approval interface must not assume that private network, or the ask cannot be answered from anywhere else.

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | `call.py` exits 0; pause correlation == resume correlation | A decision resumes the same run, on the identifier the run already had |
| 1 | The published headline is the reviewer's | An edit changes the artifact, not only the verdict: the agent proposes and the human publishes |
| 1 | The same decision again returns `duplicate`, `applied False` | The lease and the state transition are one write; a retrying phone resumes the run once |
| 1 | A second decision → `idempotency-conflict` 409 | A decision presented after the ask closed is refused, not applied |
| 1 | A late decision → `deadline-exceeded` 504, `ask_terminal` | Every ask has a deadline, and an expiry is a typed problem rather than a run quietly still parked |
| 1 | Stamps printed from the pause and from the resume | Identity, correlation and the ceiling are applied by the platform at both ends of the human boundary; a surface is a caller and cannot decline them |
| 1b | Caller code is 29 lines, under 40, and names no store or adapter file | One call is one call. Both measured by `harness/caller_lines.py`, the one method the harnesses share |
| 1c | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` 503 | The failure path is exercised, not only the happy one |
| 2 | Conformance, first surface, 25/25 | The four decisions, the deadline, the replay rule, the refusals, the stamps and the declared gaps all hold with no network |
| 2 | `resumed_on_same_correlation 4`, `edit_changed_artifact true`, `duplicate_resumes 0`, `untyped_refusals 0` | The four assertions the owner skill's definition of done names |
| 2 | `product_hits 0` | No product or host name outside `adapters/` |
| 3 | Conformance before (first surface) and after (streaming), 25/25 each | The interface held across a swap of who renders the ask |
| 3 | `sha256` of `interface.py`, `store.py`, `run.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 3 | `adapters_run 2`, two distinct surface markers, `selected_by configuration` | The pair is real and neither is load-bearing |
| 3 | One store, one open ask: parked on the first surface, decided on the second | The ask outlives the surface, which is the property the pair exists to test |
| 3 | `delivery_model` differs: `request_response` vs `stream` | The second surface breaks a different assumption; it is not a second approval page of the same shape |
| 4 | `--break-client-held` on the streaming surface exits 1 with `duplicate_resumes 9` and `resumed_on_same_correlation 3` | A resume from the client's own copy has no lease and no state transition: nine of ten deliveries apply again and one case resumes on an identifier the client minted |
| 4 | The same run on the first surface still exits 0 with `duplicate_resumes 0` | Singling out one surface is the point: a run that fails both, or neither, has not tested the swap |
| 4 | The suite passes again once the store is the resume point | The green run in step 3 can fail, and does |
| 5 | `--live`: the same 25 cases against `APPROVE_DELIVER_URL` | Skipped with a message when the env vars are unset. Nothing live has been measured here |

## The two surfaces behind one interface

| Axis | `adapters/dryrun.py` and `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Execution model | request/response over one parked item | a stream a person watches for the whole run |
| What a person sees | the ask and its outcome only | `run.started`, `step.progress`, `tool.proposed`, then the ask inline |
| `renders_run_in_flight` | `False` — the reviewer sees the question, not the work | `True` |
| `replayable_from_position` | `False` — `watch(since=n)` is refused with a type | `True` — replays from a position, so a decider who was disconnected loses nothing |
| `requires_open_session` | `False` — it is queued for whoever opens it | `True` — nobody sees an ask while disconnected, unless it is replayed |
| `max_edit_bytes` | 256: an edit is a form field, and a larger one is refused rather than truncated | 65536: a diff-sized edit fits |
| Where the ask lives | the store, never the surface | the store, never the surface |
| Swap procedure | `ADAPTER=live` / `--surface live` | `ADAPTER=second`; no code edit, same fixtures, one store, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The ask has no deadline, no response schema or no view; it carries the grading criterion or a surface handle; the decision is not offered, fails the ask's response schema, names no actor, arrives on a handle the surface minted, or is larger than the surface declared it can hold |
| `urn:agentic:problem:deadline-exceeded` | 504 | The ask closed at its deadline. The run terminated there; the ask is terminal (`ask_state: expired`, `ask_terminal: true`) and a new run is the remedy |
| `urn:agentic:problem:idempotency-conflict` | 409 | A second, different decision on an ask already decided, or an ask id parked twice |
| `urn:agentic:problem:adapter-unavailable` | 503 | The surface could not deliver the ask, or the approval unit did not answer |

`urn:agentic:problem:human-ask-expired` is proposed and has no row in the closed registry of `docs/decomposition.md` 2.1.6, so an expired ask returns the registered `deadline-exceeded` with the ask id in `detail`, exactly as `cap-human-interaction` says to do until that row lands. Its registry `retryable` value is left as the registry states it; `ask_terminal` is the declared extension member that says nothing resumes on this ask.

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| An ask that is a message on one surface rather than a record | `store.py` is written before either surface and stores the ask before it is delivered; `ParkedAsk.resume_token` is derived from the ask id and the correlation id, never minted per surface, and the conformance run parks on one surface and decides on the other against one store |
| A gate whose deciding subject is whoever happens to hold a screen | The surface authenticates and puts the subject on the decision; `HumanDecision.actor` is required, the delegation chain grows by one hop at the resume, and there is no force-continue, skip or override on the interface — a case asserts the operation set |
| A parked state that a surface owns, so a reload loses the ask | The state is a fold over the store's own log. A conformance case parks with one surface object, discards it, and decides with another |
| A decision that resumes on a handle the surface minted | A decision whose `correlation_id` is not the run's is refused `document-invalid`; the deliberate breakage is exactly this, and it fails |
| An approval surface reachable only on one private network | No network appears in the interface. The live adapter takes whole URLs from the environment, and the second surface reaches the same store over a different wire entirely |
| A contract expressed in the vocabulary of an orchestrator's signals — the one this capability was designed around is currently down | The pause and the resume are capability operations here; nothing in `interface.py`, `store.py` or `run.py` names an engine, a signal, a worker or a queue |
| An interface shaped so an edit degrades into approve-with-a-comment | Four decisions, one enumeration, and `edit_changed_artifact` is a conformance assertion rather than a claim: the artifact the run continues with must equal the reviewer's body |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 39 checks, 0 failures |
| The four decisions resuming on one correlation id, across both surfaces | Measured: 25/25 cases per surface, `adapters_run 2` |
| Live mode against `APPROVE_DELIVER_URL` | Claimed. The unit's routes, its payloads, its auth and its subject field are unverified; nothing below the reachability check in `adapters/live.py` has been executed |
| The second surface against a real browser client | Claimed as a faithful stub: the event framing, the position replay and the swap procedure are real and run here; no browser and no `STREAM_URL` endpoint was attached |
| The standard, "AG-UI agent-to-user interaction events" | No protocol version string is on file: every record for it is a search result, and the blueprint records the version as none found. The typed-event property is what this harness implements; no event-type name is asserted from the standard, and the names in `EVENT_TYPES` are this repository's own |
| The JSON Schema check in `interface.validate_subset` | A deliberate subset for this harness. The real checker is the document-validation capability |
