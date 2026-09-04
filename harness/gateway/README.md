# Gateway harness — model access by class

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/gateway/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/gateway/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/gateway/call.py` |
| 4. Prove the interface held | `python3 harness/gateway/conformance.py --adapter dryrun --adapter second` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 266 | The capability interface: `CompletionRequest`, `ClaimTicket`, `CompletionResult`, `CancelAck`, `Problem`, and `ModelAccessAdapter` with route, submit, claim, cancel. `submit` is concrete, so no adapter can decline the class check, the ceiling check or the idempotency check |
| `routing.json` | 18 | The 25 groups of PASS.md A4 as data: four classes, their members, their defaults, and the routing test vectors. Member names are data; no code branches on one |
| `adapters/dryrun.py` | 49 | Deterministic completions in process. No network, no spend, same bytes every run. Failure path on `DRYRUN_FAIL=1` |
| `adapters/live.py` | 97 | Today's component: POST `/v1/chat/completions` at `GATEWAY_URL` with `GATEWAY_KEY`, via `urllib` behind a guarded import. Product names live here |
| `adapters/second.py` | 145 | The second serving path: provider-native asynchronous batch, claim-and-poll. Submit returns pending, claim polls, cost is committed then reconciled, nothing is stoppable |
| `call.py` | 85 | The minimal call. 13 lines below the `>>> CALLER CODE` marker, counted by `harness/caller_lines.py`; everything above it is the platform stamping the envelope |
| `conformance.py` | 269 | The 12 cases every adapter passes, plus the product-name scan over code |
| `mechanisms.py` | 172 | model-access-q2: the six mechanisms beyond a plain completion - streaming, a tool-call turn, schema-constrained structured output, a cache directive, reasoning effort, and the prompt/cached/reasoning/completion usage record - exercised on `dryrun` and `second` alike and verified from the response, never from the request having been merely accepted (`python3 harness/gateway/mechanisms.py`) |
| `test.sh` | 112 | The gate: 25 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skill, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `ask = envelope(model_class, prompt)` | One entry envelope; the platform stamps correlation id, ceiling, idempotency key and actor into it without being asked |
| `ticket = adapter.submit(CompletionRequest.from_dict(ask["payload"]))` | One completion by class. Refuses a vendor name (422) and a request over its cap (402) before any call |
| `while ticket.state == "pending": ticket = adapter.claim(ticket)` | A fast path is already redeemed; a slow one is claimed. The caller cannot tell which answered |
| `except Problem as problem: print(problem.body)` | One handler for every failure, branched on `type`, never on prose |
| `table(...)`, `print(got.text)` | Class, ticket state, cost, budget left, cost status, then the completion |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `MODEL_CLASS` | `i-fast` | Any class: a bare prefix (`f-`, `i-`, `b-`, `cli-`) or a member of one |
| `PROMPT` | one line about routing classes | The user message |
| `CEILING_MICROS` | `200000` | The ceiling stamped on the envelope; `100` trips the cap refusal |
| `VENDOR` | unset | Adds a `vendor` field to the request, to see the refusal |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `GATEWAY_URL` | yes | Base URL of the OpenAI-compatible model gateway on this host (LiteLLM today: `gateway-litellm-1`, `127.0.0.1:4000`, PASS.md A1) |
| `GATEWAY_KEY` | yes | The group's scoped virtual key, which carries its hard budget cap (PASS.md A4). Sent as `Authorization: Bearer` |
| `GATEWAY_TIMEOUT_S` | no | Per-request timeout in seconds, default 120 |
| `BATCH_SUBMIT_URL` | no | Full URL of the provider's batch submit route for `adapters/second.py`. Supplied whole by the operator: no batch route is invented here. Unset means the in-process state machine runs |
| `BATCH_STATUS_URL` | no | Full URL of the batch status route, with `{job_id}` where the job id goes |
| `BATCH_KEY`, `BATCH_TIMEOUT_S`, `BATCH_POLLS` | no | Bearer key, timeout, and how many polls the in-process simulation takes to be ready (default 2) |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 12/12 | Class routing, the cap, the refusals, idempotency, cancel and the marker all hold with no network |
| 1b | Caller code is 13 lines, under 40, and names no adapter storage | One call is one call; the stamps are the platform's work, not the caller's. Both are measured by `harness/caller_lines.py`, the one method all five harnesses share |
| 1b | `VENDOR=…` exits 2 with `document-invalid` 422 | A request naming a vendor is refused, and nothing was dispatched |
| 1b | `CEILING_MICROS=100` exits 2 with `budget-exhausted` 402 | A request over its cap is refused before the call, at `platform-pre-dispatch`, with no spend incurred |
| 1b | `MODEL_CLASS=gpt-4o` exits 2 | A vendor's model name is not a routing class |
| 1c | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` 503 | The failure path is exercised, not only the happy one |
| 2 | Conformance before (dryrun) and after (second), 12/12 each | The interface held across a swap of the serving path |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py`, `routing.json` identical across both runs | The swap was configuration, not a code edit |
| 2 | 4 execution-model axes differ | The second adapter breaks different assumptions; the swap tests the contract, not a competitor of the same shape |
| 3 | `product_hits=0` over the code | No product name outside `adapters/` |
| 4 | A branch on the adapter name in a copy of `call.py` makes the run exit 1 and names the file | The green run in step 3 can fail; the two adapters are one interface |
| 5 | `--live`: the same 12 cases against `GATEWAY_URL` | Skipped with a message when the env vars are unset. Nothing live has been measured here |

## The two adapters behind one interface

| Axis | `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| How a completion is served | synchronous | asynchronous batch |
| What submit returns | a ticket already redeemed | a ticket pending, with an `earliest_retry` |
| How a result is read | claim returns it unchanged | claim polls until it is ready |
| When cost is known | reconciled when the POST returns | committed at submit, reconciled at claim |
| Whether work can be stopped | it has already finished; a cancel is recorded | it cannot be stopped; a cancel is recorded and cost may still be owed |
| Swap procedure | `ADAPTER=live` | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The request names a vendor, an endpoint or any field outside the vocabulary, or `model_class` is not a routing class |
| `urn:agentic:problem:budget-exhausted` | 402 | The call would cross the ceiling. Refused before dispatch, with `enforcement_point` naming which point refused |
| `urn:agentic:problem:adapter-unavailable` | 503 | No member serves the class, a policy verdict leaves nowhere to route, or the endpoint cannot be reached |
| `urn:agentic:problem:idempotency-conflict` | 409 | The same key returns with a different body |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A request field that names a vendor, a member model or an endpoint | `CompletionRequest.from_dict` refuses any field outside the six-field vocabulary, and `model_class` must match the class pattern. Both are conformance cases |
| A passthrough route only one gateway offers, which is how batch already runs here | The batch path is a second adapter behind the same four operations; its routes come whole from `BATCH_SUBMIT_URL` and `BATCH_STATUS_URL`, so a passthrough is configuration, not interface |
| A caller learning which adapter answered, then branching on it | The ticket carries a class, a state and a result and nothing else; the endpoint marker is read from the response into the report, never into the ticket. The deliberate breakage is exactly this branch |
| Treating a per-key cap as the run's ceiling | The ceiling is checked at `platform-pre-dispatch` before any call; the gateway's scoped key cap is a second enforcement point behind it, reported as `gateway-scoped-key` when it is the one that refuses |
| Routing rules that can only be tested by spending | `route()` is pure, its table is data, and its vectors run with no model reachable |
| A routing change believed to be in effect because of where it was written — measured on this substrate, where a config row in Postgres overlays and replaces `router_settings` on every gateway load (PASS.md A7 finding 3) | Routing is in front of the adapter, in `routing.json`, and the conformance run asserts the selection from the table rather than from the gateway's loaded configuration |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 25 checks, 0 failures |
| Live mode against `GATEWAY_URL` | Claimed. The request shape, the cost field and the correlation headers are unverified against a real endpoint |
| `unit_micros_per_1k` prices in `routing.json` | Proposed test fixtures. Only the free class is a fact (PASS.md A4) |
| The standard, "OpenAI-compatible completions" | Version unverified: every record on file for it is a search result, not a fetched page |
