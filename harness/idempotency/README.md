# Idempotency harness — one claim over a key and a payload digest

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/idempotency/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/idempotency/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/idempotency/call.py` |
| 4. Prove the interface held | `python3 harness/idempotency/conformance.py --adapter dryrun --adapter second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `ClaimRequest`, `ClaimOutcome` (`fresh`/`duplicate`/`conflict`), `Problem`, and `IdempotencyAdapter` with `claim`, `complete`, `resolve`, `expire`. A conflict is raised as the typed `idempotency-conflict` problem from inside `claim()`, never returned as a value a caller could forget to check |
| `adapters/dryrun.py` | The first enforcing adapter: log-fold-at-entry, in process, in memory. No conditional write happens before a `fresh` answer is given, so it declares `supports_in_flight = False` |
| `adapters/live.py` | Today's real component: the same fold, against a real on-disk, hash-chained JSONL file reached only through `IDEMPOTENCY_LEDGER_PATH`. No product name appears here because none runs this row today (PASS.md B3, F-b3-16) |
| `adapters/second.py` | The swap candidate: a conditional-write lease. A real `threading.Lock` compare-and-set, a monotonic fencing token, and an in-flight state a duplicate can be answered from mid-execution. `supports_in_flight = True` |
| `call.py` | The minimal call: submit one unit of work under a key, replay it, race ten concurrent submissions of it, and reuse the key under a different payload |
| `conformance.py` | The 8 cases every adapter passes, including a race case that asserts differently per adapter's declared `supports_in_flight` |
| `test.sh` | The gate: conformance, the swap proof, one deliberate breakage, and `--live` against an on-disk ledger |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = load_adapter(os.environ.get("ADAPTER", "dryrun"), ...)` | Binds one of three adapters by configuration, not by code |
| `first = submit(adapter, env)` | Submits one unit of work under a key: `claim()` then, only if `fresh`, the side effect and `complete()` |
| `replay = submit(adapter, env)` | Replays the same key and payload: `claim()` answers `duplicate` with the stored result; no second effect |
| `race_outcomes = race(adapter, envelope("race-"+key, 7), 10)` | Ten threads submit the same key at once; with a lease, exactly one wins and the rest wait or are answered mid-flight |
| `submit(adapter, envelope(key, amount=13))` inside `try`/`except Problem` | Reuses the first key under a different payload; refused as the typed `idempotency-conflict`, 409 |
| `table(...)`, `print(...)` | Outcome table, the race tally, and the conflict body |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `KEY` | `human-submit-unit-2026-09-03` | The idempotency key the first two calls and the conflict call share |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |
| `RACE_DELAY_S` (dryrun only) | `0` | Widens the read/write window inside `dryrun.py`'s unlocked check so a genuine race is observable on demand rather than by luck |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `IDEMPOTENCY_LEDGER_PATH` | yes | Path to an existing, already-written, append-only JSONL ledger of the shape `examples/end-to-end/run.py`'s `Ledger` and `harness/linked/linked.py`'s `Ledger` write. `test.sh --live` copies `examples/end-to-end/out/ledger.jsonl` into this harness's own `out/` before pointing here, so the shared example's file is never mutated |

There is no `GATEWAY_URL`-shaped endpoint or key for this element: PASS.md B3 records the adapter today as "key on the wire, no lease" (F-b3-16), which names a convention on an envelope field, not a running service. The nearest real, running thing is the append-only log this platform already writes at entry, so that log — not a network endpoint — is what `adapters/live.py` is reached through.

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 8/8 | Claim/complete/resolve/expire, the replay, the conflict, and the sequential race all hold with no network |
| 1b | Caller code is 28 lines, under 40 | One call is one call |
| 1b–1c | `ADAPTER=dryrun call.py` exits 0; a reused key under a different payload is refused, 409, before any second effect | The minimal call (submit, replay, race, reuse) all hold end to end |
| 2 | Conformance before (dryrun) and after (second), 8/8 each; `sha256` of `interface.py`+`call.py`+`conformance.py` identical | The interface held across a swap of the execution model; the swap was configuration, not a code edit |
| 2 | 3 execution-model axes differ (`unit_of_conditionality`, `supports_in_flight`, `overlapped`) | The second adapter breaks a different assumption than the first: it decides *before* the fact under contention, the fold decides *after* the fact from a completed record |
| 3 | Removing the `with self._lock:` guard from a copy of `adapters/second.py` (leaving the key on the wire) makes its own race case fail: `executions=20`, `overlapped=0`, 7/8 cases pass | Reproduces `cap-idempotency-implement`'s own `definition_of_done` breakage exactly: without a lease, every concurrent copy wins the check |
| 4 | `--live`: conformance against the on-disk ledger, 8/8; `call.py` run against it | Skipped with a message when no ledger exists. When run, the real, unlocked, file-appending fold is timing-dependent under a genuine race — sometimes one winner, sometimes several — which is the row PASS.md B3 records, not a defect in this harness |

## The two adapters behind one interface

| Axis | `adapters/dryrun.py` / `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| `unit_of_conditionality` | log-row (fold at entry) | keyed compare-and-set |
| When the decision is taken | after the fact, from a completed record | before the fact, under contention |
| `supports_in_flight` | `False` | `True` |
| Can a duplicate be answered mid-execution? | No — declared, not asserted | Yes — `overlapped >= 1` in the conformance report |
| What it needs to run | nothing beyond the log the platform already writes | its own store (here: an in-process lock and dict; any keyed conditional-write store swaps in with no interface change) |
| Swap procedure | `ADAPTER=dryrun` or `ADAPTER=live` | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | An unknown adapter name is requested |
| `urn:agentic:problem:idempotency-conflict` | 409 | The same key is claimed under a different payload digest |
| `urn:agentic:problem:adapter-unavailable` | 503 | `adapters/live.py` cannot find `IDEMPOTENCY_LEDGER_PATH` or the file it names |

## What would pin this to a component, and how the adapter boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A request field carrying the raw payload rather than its digest | `ClaimRequest.for_payload` stores only `digest(payload)`; the conformance run's "no leak" case asserts the outcome never carries the payload |
| Judging an implementation by the sequential case only | `conformance.py` runs both a sequential case (which every adapter passes) and a concurrent one, asserted differently by declared `supports_in_flight` rather than papered over |
| Treating "key on the wire" as already deduplicating | `dryrun.py` and `live.py` implement it literally — a fold with no lock — so the race case shows, honestly, what it cannot do, rather than the harness asserting a property no adapter here provides |
| One surviving adapter once a lease exists | `cap-idempotency-implement` step 4 says keep the fold; this harness ships both, and both pass the same 8 cases |
| A conflict answered as a bespoke error shape | `claim()` raises the platform's own `Problem`/`idempotency-conflict`, the same registry every other harness in this repo raises from |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 16 checks, 0 failures |
| `--live` against an on-disk ledger | Measured when a ledger file exists (20 checks, 0 failures, run on 2026-09-03 against a copy of `examples/end-to-end/out/ledger.jsonl`); the exact race outcome under real file I/O is timing-dependent by design and is reported, not asserted |
| The standard, "Idempotency-Key header convention" | Version unverified: `draft-ietf-httpapi-idempotency-key-header-07` is a search-only record placing it in the IETF httpapi working group as an expired draft; the draft text itself was not fetched from this environment (cap-idempotency, X-cap-idempotency-001) |
| `IdempotencyClaim`, `ClaimOutcome`, `claim`/`complete`/`resolve`/`expire` | Proposed shapes and operation names: `cap-idempotency` states the recorded standard is a field convention, not a set of calls, so this vocabulary is this repo's design over it |
| `adapters/second.py`'s in-process lock as a stand-in for "any keyed lease store" | A faithful stub, per the author brief: the compare-and-set, the fencing token and the in-flight answer are real and pass the same suite a networked store would; only the store itself (Redis, Postgres, or similar) is not networked here |
