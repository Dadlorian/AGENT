# State-persistence harness — an opaque record, appended and proved

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/state-persistence/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/state-persistence/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/state-persistence/call.py` |
| 4. Prove the interface held | `python3 harness/state-persistence/conformance.py --adapter dryrun --adapter second` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 353 | The capability interface: `AppendRequest`, `StateRecord`, `Head`, `InclusionProof`, `ConsistencyProof`, `Problem`, and `StatePersistenceAdapter` with append, resolve_head, read_at, prove, prove_consistency, redact. `append` is concrete, so no adapter can decline the expected-head check or the fencing check. Also holds the RFC 9162 merkle math (`mth`, `audit_path`, `root_from_inclusion_proof`, `consistency_proof`, `verify_consistency`) as pure functions |
| `adapters/dryrun.py` | 100 | An in-memory chained, provable log. No disk, no network. Failure path on `DRYRUN_FAIL=1` |
| `adapters/live.py` | 154 | Today's component: this repository's own ledger, `kb/ledger.jsonl` read directly and appended via the subprocess `tools/kb.py ledger`. Product names live here |
| `adapters/second.py` | 169 | The second execution model: a content-addressed merkle log over an object-store stub (`OBJSTORE_DIR`, a local directory standing in for a bucket), head advanced by compare-and-swap |
| `verify_external.py` | 81 | The independent verifier: no import of `interface.py`, invoked as a subprocess. Recomputes the merkle root and each record's content id from scratch |
| `call.py` | 92 | The minimal call. 21 lines below the `>>> CALLER CODE` marker; everything above it is the platform stamping the envelope |
| `conformance.py` | 265 | The 11 cases every adapter passes, plus the product-name scan over code |
| `test.sh` | 162 | The gate: 20 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `h0 = adapter.resolve_head(partition)` | The only call allowed to be non-deterministic; made once, before anything is written |
| `rec1, h1 = adapter.append(...)` | Puts one opaque record; refused before it is applied if the head moved or the field vocabulary is wrong |
| `rec2, h2 = adapter.append(...)` | A second, later write |
| `pinned = adapter.read_at(partition, h1)` | Reads back at `h1`, pinned: `rec2` does not appear even though it already landed |
| `verified = verify_inclusion_proof(adapter.prove(partition, rec1.record_id, h1))` | An inclusion proof for `rec1`, checkable from the record, the proof and the head alone |
| Two more `adapter.append(...)` calls, both against `h2` | Two writers racing for the same head: the first wins, the second is refused `head-moved` - never a fork |
| `except Problem as problem: print(problem.body)` | One handler for every failure, branched on `type`, never on prose |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `PARTITION` | `demo` | The partition a run writes to |
| `BODY` | `one opaque record` | The text put in the first record's body |
| `DRYRUN_FAIL` | unset | `1` makes the dry-run adapter refuse every append with `adapter-unavailable` |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `STATE_LEDGER_PATH` | yes | The JSONL file to read (recommended: `kb/ledger.jsonl`, this repo's live instance, F-b3-17) |
| `STATE_LEDGER_PARTITION` | no | Default `kb-ledger`. This binding serves one partition only - the live ledger has one global sequence |
| `STATE_KB_TOOL` | no | Default `python3 tools/kb.py`. `append` shells out to `<tool> ledger '<json>'`; **note:** `tools/kb.py`'s `ledger` subcommand always writes to `kb/ledger.jsonl` itself, with no path override, so a write here reaches the real project ledger regardless of `STATE_LEDGER_PATH` |

`test.sh --live` was **not** run against the real ledger in this harness: only the read path (`resolve_head`, `read_at`, `prove`, `prove_consistency`) was exercised, against a scratch copy, because appending unreviewed test records into this project's actual ledger was judged out of scope for a dry run. See `provenance.json`.

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 11/11 | Append, the pinned read, the proof, the fork refusal, the fencing token, redaction and the external verifier all hold with no disk, no network |
| 1b | Caller code is 21 lines, under 40, and names no adapter storage file | One call is one call; the stamps are the platform's work, not the caller's |
| 1b | The minimal call's table shows `proof_verified=True` and `no_fork=True` | The four things the minimal call promises actually happened on this run |
| 1c | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` | The failure path is exercised, not only the happy one |
| 2 | Conformance before (dryrun) and after (second), 11/11 each | The interface held across a swap of the execution model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py`, `verify_external.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | 4 execution-model axes differ | The second adapter breaks different assumptions; the swap tests the contract, not a competitor of the same shape |
| 3 | `product_hits=0` over the code | No product name outside `adapters/` |
| 4 | One record's body edited in place, `record_id` left unchanged, in a copy of the second adapter's store | `chain_break_at` goes from `-1` to the edited index under an independent verifier that never imports this project's own tree code; the merkle root over the (unchanged) ids still matches, showing the tree proves position while the content-id check is what catches a tampered body |
| 5 | `--live`: skipped, `STATE_LEDGER_PATH` unset here | Nothing live was measured in this run of the gate; see `provenance.json` for what was measured read-only against a scratch copy |

## The two adapters behind one interface

| Axis | `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Where order comes from | Byte position in one mutable file | A persisted tree, advanced by compare-and-swap on one small head object |
| Identity | The ledger tool's own hash column, over the whole record including bookkeeping fields | The digest of `{kind, partition, body, seq}` alone |
| Writer model | One writer, one file, no compare-and-swap at the tool layer | Immutable objects; the tree and the head are the only two things ever overwritten, and only via CAS |
| Proof cost | Rebuilt from the file's hash column on every call - grows with the log | Read from a persisted tree file - does not require a listing |
| Redact | Unsupported: the live tool has no delete or field-drop path | Supported: the object's `body` is overwritten with `None` in place, `record_id` unchanged |
| Swap procedure | `ADAPTER=live` | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The append names a field outside the six-field vocabulary, or a required field is malformed |
| `urn:agentic:problem:head-moved` | 409, retryable | The expected head no longer matches, or the fencing token is not after the last one accepted for the partition |
| `urn:agentic:problem:record-unverifiable` | 422 | A proof does not reconstruct the head it was taken against, or names a record not in the log at that head |
| `urn:agentic:problem:adapter-unavailable` | 503, retryable | This binding cannot serve the operation (a wrong partition, a store unreachable, redact on the live binding) |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A caller reading a store's own file format directly | `AppendRequest`, `StateRecord`, `Head` and the proof shapes are the only vocabulary; `harness/caller_lines.py`'s storage-suffix rule is mirrored in `test.sh` step 1b |
| Proving a record by rehashing the entire log | `prove` returns a path whose length is logarithmic in the tree size (asserted in conformance case 3), never a full scan |
| A store believed tamper-evident because nothing has tried to edit it | The breakage step edits a record in place and shows an independent, never-imported verifier catches it |
| Treating "the tree didn't change" as proof the content didn't change | `verify_external.py` recomputes each record's content id separately from the merkle root check - the tree only proves position, not that stored bytes still match their claimed id |
| A routing/config change believed in effect because of where it was written (PASS.md A7 finding 3, same pattern this project's own ledger shows) | The expected head and the fencing token are checked fresh, from `resolve_head`, on every append; nothing is cached |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 20 checks, 0 failures |
| The live adapter's read path (`resolve_head`, `read_at`, `prove`, `prove_consistency`) | Measured, read-only, against a scratch copy of `kb/ledger.jsonl` (59 records); see `provenance.json` |
| The live adapter's write path (`append`, via `tools/kb.py ledger`) | Claimed. Never invoked here: that subcommand always targets the real project ledger with no path override |
| The second adapter against a real object-store bucket (`OBJSTORE_DIR` pointed at a mount) | Claimed. Exercised only against a local scratch directory |
| Out-of-order object arrival on the second adapter | Claimed by design (the tree is read from a persisted file, never a listing), not exercised: this harness's conformance run is single-process and sequential |
| The standard, RFC 9162 and RFC 8785 | Version unverified: the only record on file for either (X-xc-provenance-chain-006) is a search result, not a fetched page |
