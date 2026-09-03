# Errors harness — one typed problem for every boundary

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/errors/test.sh` |
| 2. Produce one problem | `ADAPTER=dryrun python3 harness/errors/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/errors/call.py` |
| 4. Prove the interface held | `python3 harness/errors/conformance.py --adapter dryrun --adapter second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `Problem`, `ProblemException`, `UnregisteredType`, `construct()` (the one gate every Problem passes through), and `ErrorsAdapter` with `raise_problem`, `retry_advice`, `chain` concrete and `classify` abstract. `REGISTRY` is the closed type registry transcribed from `cap-errors/references/problem-registry.md` |
| `adapters/dryrun.py` | Deterministic in-process problem factory. `classify` sees the raised exception directly |
| `adapters/live.py` | Today's component: PASS.md B3 records the errors tool as *absent* (F-b3-13), so this is the same in-process library, gated on `ERRORS_RUN_ID`/`ERRORS_CORRELATION_ID` standing in for real deployment context |
| `adapters/second.py` | The second execution model: an edge component that sees only a wire response (`status`, `media_type`, `body`) and reshapes or falls through to `adapter-unavailable`, never forwarding an untyped body unchanged |
| `call.py` | The minimal call. Caller code is measured below the `>>> CALLER CODE` marker the way `harness/caller_lines.py` measures the other harnesses (this harness is not in its `HARNESSES` tuple, so `test.sh` reimplements the same count inline rather than editing that file) |
| `conformance.py` | The 9 cases every adapter passes, plus the product-name scan |
| `test.sh` | The gate: 23 checks in dry run (26 with `--live` and context set), the swap proof, and one deliberate breakage |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `ask = envelope(suffix, detail)` | One entry envelope; the platform stamps the correlation id into it without being asked |
| `adapter.raise_problem(ask["payload"]["suffix"], ..., ask["correlation"]["correlation_id"])` | Produces one typed problem for a refusal from the closed registry |
| `retryable, retry_after_s = adapter.retry_advice(problem)` | A caller decides to retry or not from `retryable` alone, never from `detail` |
| `adapter.raise_problem("not-a-registered-type", ...)` → `except UnregisteredType` | A type not in the registry is refused before a body is ever built |
| `edge.classify({"status": ..., "media_type": MEDIA_TYPE, "body": problem.body()})` | The same body, reshaped by the edge adapter, compared byte for byte |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `SUFFIX` | `budget-exhausted` | Any registry suffix, to see how `retryable` changes with the type |
| `DETAIL` | one line about the ceiling | The detail string (kept identical across a retryable/non-retryable pair in `test.sh` to prove the decision is not read from it) |
| `ENTRY_KIND`, `ACTOR`, `RUN_ID` | `human`, `user:corey`, `run-harness-errors` | Which of the four entries is acting, as whom, and the run the correlation id is derived from |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `ERRORS_RUN_ID` | yes | Stands in for the real deployment context PASS.md B3 has nothing else to offer: no endpoint, key or socket exists for this element today (*absent*, F-b3-13) |
| `ERRORS_CORRELATION_ID` | yes | Same purpose. Unset, `raise_problem` on the live binding refuses cleanly with `adapter-unavailable` rather than fabricating context |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 9/9 | Registry construction, retry advice, chaining, the untyped fallback and the byte-identical case all hold with no network |
| 1b | Caller code is 25 lines, under 40 | One call is one call; the stamps are the platform's work, not the caller's |
| 1b | `SUFFIX=deadline-exceeded` vs `SUFFIX=policy-denied`, same `DETAIL` | The retry decision comes from `retryable`, not from reading the message |
| 1c | `ADAPTER=live` with no context exits 0 with a typed `adapter-unavailable`, no traceback | The live binding's own reachability gate is itself a registered problem, not a crash |
| 2 | Conformance before (dryrun) and after (second), 9/9 each | The interface held across a swap of execution model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | 3 execution-model axes differ | The second adapter breaks a different assumption than the first; the swap tests the contract, not a competitor of the same shape |
| 3 | `product_hits=0` over the code | No product name anywhere (PASS.md B3 records none for this element) |
| 4 | The edge adapter's media-type/registry check is removed in a copy; the run crashes and names the file | The green run in step 2 can fail; the two adapters are one interface, not independently tested code paths |
| 5 | `--live`: the same 9 cases against the live binding | Skipped with a message when `ERRORS_RUN_ID`/`ERRORS_CORRELATION_ID` are unset |

## The two adapters behind one interface

| Axis | `adapters/dryrun.py` / `adapters/live.py` (in-process) | `adapters/second.py` (edge-filter) |
|---|---|---|
| How many processes must run to answer | one -- the raise site itself | two -- an upstream process plus this filter, reached only after the first has already answered |
| What `classify` is handed | the Python exception raised at the failure site | a wire dict: `status`, `media_type`, `body` |
| What it can populate | `rule_id`, `causes`, a detail written for the caller | only what the upstream body already carried; it reshapes, it never invents |
| Untyped detection | `str(type(exc))` on an exception this site never registered | the media type and the presence of a registered `type` member on the wire body |
| Swap procedure | `ADAPTER=live` | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

## Failures a caller can get

| `type` | Status | Retryable | Raised when |
|---|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | no | The document fails schema validation |
| `urn:agentic:problem:criterion-unresolvable` | 422 | no | `criterion_ref` does not resolve |
| `urn:agentic:problem:identity-untrusted` | 401 | no | The delegation chain does not verify |
| `urn:agentic:problem:policy-denied` | 403 | no | A deterministic pre-execution refusal (`rule_id`) |
| `urn:agentic:problem:budget-exhausted` | 402 | no | A metered call would cross the ceiling |
| `urn:agentic:problem:deadline-exceeded` | 504 | yes | Wall clock ceiling reached (`retry_after_s`) |
| `urn:agentic:problem:cancel-timeout` | 500 | no | Grace window elapsed, unit destroyed |
| `urn:agentic:problem:isolation-unavailable` | 503 | yes | No isolation adapter could admit the unit |
| `urn:agentic:problem:adapter-unavailable` | 503 | yes | A capability adapter is down, or raised a failure it could not type |
| `urn:agentic:problem:idempotency-conflict` | 409 | no | Same key, different request body |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A caller branching on `detail` text instead of `type`/`retryable` | `retry_advice` reads only the members; `test.sh` runs a retryable and a non-retryable case with the identical detail string and asserts the decision still differs |
| A registry that drifts because each adapter keeps its own copy (best_practices in `cap-errors-implement`) | Both adapters import the same `REGISTRY` from `interface.py`; nothing in either adapter file restates a row |
| An edge filter silently forwarding a body it did not understand (`cap-errors-implement` best_practices) | `classify` on the edge adapter falls through to `adapter-unavailable` and counts `untyped`/`wrong_media_type`; the deliberate breakage removes exactly that guard and the run stops passing |
| Widening the interface so the edge adapter can fake `rule_id`/`causes` it never saw | The gap is declared on `adapters/second.py` instead (`cap-errors-implement` step 4); the byte-identical case only asserts parity for a body the upstream already carried whole |
| A caller catching a bare `Exception` and reading `str(e)` | `raise_problem` always raises `ProblemException`, never returns one to forget to raise; a caller has exactly one thing to catch |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 23 checks, 0 failures |
| Live mode against `ERRORS_RUN_ID`/`ERRORS_CORRELATION_ID` | Measured by `test.sh --live` with those two set: 26 checks, 0 failures. There is no separate live component to reach (PASS.md B3: *absent*), so "live" here is the same in-process library under real deployment context rather than a network boundary |
| The standard, "RFC 9457 problem details" | Version unverified: recorded as a search result, not a fetched page (T-t9-09) |
| `unit_micros`-style pricing, budget or policy wiring beyond `budget-exhausted`/`policy-denied` construction | Not exercised here; this harness types the failure body, it does not implement the budget or policy capabilities themselves |
