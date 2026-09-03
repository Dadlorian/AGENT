# Memory harness — write, recall, expire, scope

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/memory/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/memory/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/memory/call.py` |
| 4. Prove the interface held | `python3 harness/memory/conformance.py --adapter dryrun --adapter second` |

PASS.md's inventory of what is defined but not running is stated because an
inventory that omits this is not an inventory (F-a6-01) — memory is in none
of its rows. There is no memory row to migrate from; what this harness
replaces is the habit of handing a run its predecessor's whole transcript
instead of writing items it can recall (cap-memory-implement step 4). No
ratified standard governs this interface (cap-memory: "none found"); the
binding record and recall shapes here are this repository's own design.

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 269 | The capability interface: `RememberRequest`, `MemoryItem`, `RecallQuery`, `RecallResult`, `Problem`, and `MemoryAdapter` with `remember`, `recall`, `supersede`, `forget`. `remember` and `recall` are concrete: no adapter can decline the staleness check on a write or the on-read expiry filter on a recall |
| `adapters/dryrun.py` | 98 | An in-memory, ranked-shaped store. No disk, no network. Failure path on `DRYRUN_FAIL=1` |
| `adapters/live.py` | 108 | Today's component — which does not exist: PASS.md has no memory row, so this is a stub reached only through `MEMORY_LIVE_STORE_PATH`/`MEMORY_LIVE_ENDPOINT`, refusing `adapter-unavailable` when unset. Product names live here |
| `adapters/second.py` | 154 | The second execution model, per cap-memory-implement's adapters: a file-backed store, one JSON document per exact scope key, `recall` an exact lookup — the axis it must differ on from the ranked store |
| `call.py` | 86 | The minimal call. 27 lines below the `>>> CALLER CODE` marker |
| `conformance.py` | 233 | The 10 cases every adapter passes, plus the product-name scan |
| `test.sh` | 137 | The gate: 23 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `adapter.remember(RememberRequest.from_dict({... "expires_at": "2099-..."}))` | Writes one item under `mine` scope with an expiry; refused before it is applied if the scope or the staleness policy is missing |
| A second `remember(...)` under `other` scope | To show a later recall never crosses it |
| A third `remember(...)` under `mine` scope with `expires_at` already past | To show a later recall never serves it |
| `adapter.recall(RecallQuery.from_dict({"scope": mine, "limit": 10}))` | Recalls by scope; the returned ids are checked for the own item present, the expired item absent, the other-scope item absent |
| `except Problem as problem: print(problem.body)` | One handler for every failure, branched on `type`, never on prose |

`test.sh` runs this same file once per binding (`ADAPTER=dryrun`, then
`ADAPTER=second`) — that is how "the same recall from both stores" is shown,
the same method `harness/state-persistence` uses for its own swap proof.

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `DRYRUN_FAIL` | unset | `1` makes the dry-run adapter refuse every write with `adapter-unavailable` |
| `SECOND_FAIL` | unset | `1` makes the scope-keyed store refuse every write with `adapter-unavailable` |
| `MEMORY_CLOCK` | unset | A fixed ISO timestamp for `now_iso()`, for deterministic ages |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `MEMORY_LIVE_STORE_PATH` | yes | A directory this stub uses as a local stand-in for the hosted, embedding-ranked store's own persistence. Unset, every operation refuses `adapter-unavailable` before touching anything |
| `MEMORY_LIVE_ENDPOINT` | no | Read and reported in `declared_gaps`; never dialed. There is no hosted memory component in this tree to reach — PASS.md's blueprint has no memory row (`blueprint_tool_entry`: absent today) |

`adapters/live.py` implements `remember` and `recall` only. `supersede` and
`forget` refuse `adapter-unavailable`: there is no component behind this
binding that could honour a correction or a deletion, so `test.sh --live`
exercises the minimal call (write, recall, expiry exclusion, scope exclusion)
and does not run the full 10-case conformance suite against `live`.

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 10/10 | The staleness refusal, the scope refusal, cross-scope exclusion, expiry exclusion, provenance on every item, the policy-denied refusal, and supersede/forget all hold with no disk, no network |
| 1b | Caller code is 27 lines, under 40, and names no adapter storage file | One call is one call; the stamps are the platform's work, not the caller's |
| 1b | The minimal call's table shows all three columns `True` | The item was recalled, the expired sibling was not, the cross-scope sibling was not — on this run |
| 1c | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` | The failure path is exercised, not only the happy one |
| 2 | Conformance before (dryrun) and after (second), 10/10 each | The interface held across a swap of the retrieval model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 2b | `adapters_run=2 stores_reached_distinct=2 result_divergence=0` | The same fixtures, recalled from both stores, return the identical recallable item ids |
| 2 | 5 axes differ (execution model, retrieval model, entity, marker, declared gaps) | The second adapter breaks a different assumption; the swap tests the contract, not a competitor of the same shape |
| 3 | `product_hits=0` over the code | No product name outside `adapters/` |
| 4 | `expired_served=1` on both bindings after `_expired(...)` is cut from `recall()`, `cross_scope_hits=0` unaffected | The on-read expiry rule is enforced in the shared `recall()` wrapper, not by an adapter that could quietly skip it; the scope check and the expiry check fail for independent reasons |
| 5 (`--live`) | Skipped unless `MEMORY_LIVE_STORE_PATH` is set; when set, the minimal call passes (write, recall, both exclusions) | Nothing live was measured in a default run; see `provenance.json` for what was measured against the local stub path |

## The two adapters behind one interface

| Axis | `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| What it reaches | Nothing: no memory component exists on this host (declared, not defaulted) | A directory on this host: one JSON file per exact scope key |
| Retrieval model | Ranked — crude keyword overlap against `need`, standing in for the hosted store's embedding rank | Exact-key — `need` only ever selects among items already at that key, never ranks across keys |
| Concurrency | None: single scratch file per key, no compare-and-swap | A coarse read-modify-write per key file; adequate for this harness's sequential run, no more |
| Supersede / forget | Refused `adapter-unavailable`: no component to reach | Supported: rewrites the scope-key file(s), old item marked `superseded_by`, never edited body-first |
| Swap procedure | `ADAPTER=live`, `MEMORY_LIVE_STORE_PATH` set | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The remember or recall document is malformed, names a field outside the vocabulary, or a recall names no scope dimension |
| `urn:agentic:problem:staleness-missing` | 422 | A write's `expires_at` is absent or explicitly null — refused, never defaulted |
| `urn:agentic:problem:policy-denied` | 403 | A recall names a scope the actor does not hold (`rule_id: memory.scope.not-held`) |
| `urn:agentic:problem:item-not-found` | 404 | `supersede` or `forget` names a `memory_id` unknown to this binding |
| `urn:agentic:problem:adapter-unavailable` | 503, retryable | This binding cannot serve the operation (write disabled by env, or the live stub with no store path set) |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A caller reading a store's own scope-key file, index name or embedding client | `RememberRequest`, `MemoryItem`, `RecallQuery`, `RecallResult` are the only vocabulary; `test.sh` step 1b mirrors `harness/state-persistence`'s storage-suffix rule |
| Ranking inputs (an embedding, a similarity threshold, a `k`) leaking into the interface | `RecallQuery` carries only `scope`, `need`, `key`, `limit`; ranking is entirely inside `adapters/dryrun.py`'s and `adapters/live.py`'s own `_rank` |
| Expiry enforced only by a background sweep that might not be running | `recall()` is concrete in `interface.py` and filters expired items on every call; the deliberate breakage (step 4) is exactly this line removed |
| The scope predicate applied as a filter after a limit, leaking who was excluded through timing (cap-memory-implement's stated risk) | Each adapter's `_search` applies the scope predicate as part of the query it executes (a dict-key match for the dry run, a file path for the second adapter), not as a post-filter over an unbounded result |
| A store believed to isolate scopes because nothing has tried to cross one | Conformance cases 4 and 6 write at two scopes and recall at each, asserting the other scope's item is absent both ways |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof, the same-recall-from-both-stores check, and the breakage | Measured by `test.sh`: 23 checks, 0 failures |
| The live stub's minimal call (write, recall, expiry exclusion, cross-scope exclusion) against a local `MEMORY_LIVE_STORE_PATH` | Measured, read-write, against a scratch directory (`test.sh --live` with the env var set: 25 checks, 0 failures) |
| The live stub's `supersede` and `forget` | Claimed as unreachable, not measured: they refuse `adapter-unavailable` by design, because no memory component exists on this host to honour a correction or a deletion (PASS.md's blueprint has no memory row) |
| A real hosted, embedding-ranked store behind `adapters/live.py` | Claimed. `MEMORY_LIVE_ENDPOINT` is read and reported in `declared_gaps` but never dialed — there is nothing on file to dial |
| `adapters/second.py` against a real multi-process concurrent writer | Claimed. Exercised only sequentially, single-process, in this harness's conformance run |
| The standard | None found for this capability (cap-memory: "no ratified standard... the one protocol proposal found is a 2026 preprint"); the item, recall and binding shapes here are this repository's own design, not adopted from a fetched spec |
