# Graph harness — typed nodes, three typed edge kinds, validity decidable in memory

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/core-graph/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/core-graph/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/core-graph/call.py` |
| 4. Prove the interface held | `python3 harness/core-graph/conformance.py --adapter dryrun --adapter second` |
| 5. Prove both stores agree | `python3 harness/core-graph/conformance.py --cross-store dryrun second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `Node`, `Edge`, `Problem`, `GraphValue`, `ValidityReport`, and `GraphAdapter` with `append_node`, `append_edge`, `retract_edge`, `graph_value`, `neighbors`, `path_exists`. `assert_node`/`assert_edge`/`validate` are pure, top-level functions callable with no adapter at all. `append_node`/`append_edge` are concrete on the base class, so no adapter can admit an ill-typed node or edge |
| `adapters/dryrun.py` | An in-memory assertion log. No disk, no network. Failure path on `DRYRUN_FAIL=1` |
| `adapters/live.py` | Today's component: this repository's own ledger, `kb/ledger.jsonl` read directly and appended via the subprocess `tools/kb.py ledger`, tagged by `graph_partition`. Product names live here |
| `adapters/second.py` | The second execution model: an event log where each assertion is its own self-identified file under a directory, position claimed by a compare-and-swap on one small cursor file, read back sorted by the embedded sequence number rather than trusted directory-listing order |
| `call.py` | The minimal call. 27 lines below the `>>> CALLER CODE` marker; everything above it is the platform stamping the actor |
| `conformance.py` | The 10 cases every adapter passes, the cross-store verdict check, and the product-name scan over code |
| `test.sh` | The gate: 20 checks in dry run, the swap proof, the cross-store check, and one deliberate breakage |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |
| `plan-entry.json` | This harness's row, in `harness/plan.json`'s shape, for the orchestrator to merge |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `primary = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `nodes = assert_sample(primary, actor)` | Asserts one node of three kinds and one edge of each of the three edge kinds (implementation, existence, interface) |
| `assert_edge({...}, {"iface": ..., "doc": ...})` | An implementation edge from a document node to an interface node — ill-typed — refused with a typed problem, calling the pure function directly, no adapter, no store attached at all |
| `primary.neighbors(IDS["iface"], "implementation", direction="in")` | Expands one hop: which implementation nodes could serve this interface |
| `primary.retract_edge("edge-exist", "no longer applies", actor)` | Retracts one edge; the original record is never removed, only the fold's active view changes |
| `assert_sample(counterpart, actor)` then the same retraction | The identical assertions, replayed on the other store |
| `validate(primary.graph_value())` vs `validate(counterpart.graph_value())` | Both bindings must reach the same validity verdict over the same assertion log |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `ACTOR` | `user:corey` | Who `asserted_by` names on every node and edge |
| `DRYRUN_FAIL` | unset | `1` makes the dry-run adapter refuse every append with `adapter-unavailable` |
| `GRAPH_EVENTLOG_DIR` | `harness/core-graph/out/eventlog` | Where the second adapter's self-identified record files live |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `GRAPH_LEDGER_PATH` | yes | The JSONL file to read (recommended: `kb/ledger.jsonl`, this repo's live instance, F-b3-17) |
| `GRAPH_LEDGER_PARTITION` | no | Default `core-graph-harness`. Records are filtered by this `graph_partition` tag so a run here never collides with an unrelated ledger entry |
| `GRAPH_KB_TOOL` | no | Default `python3 tools/kb.py`. `append` shells out to `<tool> ledger '<json>'` |

`test.sh --live` was **not** run against the real ledger's write path in this harness: appending unreviewed test records into this project's actual ledger was judged out of scope for a dry run, the same call `state-persistence` made. The read path (`graph_value` via `_read_all`) was measured separately against a scratch copy of `kb/ledger.jsonl` with three fabricated `graph_partition`-tagged records appended; see `provenance.json`.

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 10/10 | Every closed node kind, every closed edge type, both design-rule-1 rejections (implementation edge to a non-interface target; existence edge between two implementations), a malformed edge, `neighbors`, `path_exists`, `retract`, `validate` with no store, and the 300-case property test all hold with no disk, no network |
| 1b | Caller code is 27 lines, under 40, and names no adapter storage file | One call is one call; the stamps are the platform's work, not the caller's |
| 1b | The minimal call's table shows a typed refusal, `implementers_found=1`, `retracted=True`, `both_stores_agree=True` | The five things the minimal call promises actually happened on this run |
| 1c | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` | The failure path is exercised, not only the happy one |
| 2 | Conformance before (dryrun) and after (second), 10/10 each | The interface held across a swap of the execution model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | 4 execution-model axes differ | The second adapter breaks different assumptions; the swap tests the contract, not a competitor of the same shape |
| 2b | `verdict_mismatches == 0` between dryrun and second over the same assertion log | Both stores, given the same records, fold and validate to one identical verdict — core-graph-implement's own definition of done |
| 3 | `product_hits=0` over the code | No product name outside `adapters/` |
| 4 | The checker widened to accept any implementation-edge target, an independent oracle (never patched, never importing the widened function) still marks the resulting edge invalid | `false_accepts` becomes non-zero on the very first case while the widened checker itself reports `rejections=0` — the breakage core-graph's own definition of done names, showing which rule was widened rather than only that something failed |
| 5 | `--live`: skipped, `GRAPH_LEDGER_PATH` unset by default | Nothing live was measured in this run of the gate; see `provenance.json` for the scratch-copy read-path measurement |

## The two adapters behind one interface

| Axis | `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Where order comes from | Byte position in one mutable file | Each record's own embedded sequence number, never directory-listing order |
| Position claimed by | Nothing — no compare-and-swap at the tool layer | A compare-and-swap rename on one small cursor object before the record is written |
| Processes required for progress | Zero: a local file this process opens directly | Conceptually one served log; here, a directory any process can read by cursor |
| Record identity | The ledger tool's own hash column | The `edge_id`/`node_id` the caller supplied, embedded in the record itself |
| Swap procedure | `ADAPTER=live` | `ADAPTER=second`; no code edit, same `assert_sample`, compare `graph_value()` and `validate()` |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:graph-assertion-invalid` | 422 | A node's kind is outside the closed set, an edge's type rule is violated (an implementation edge not running implementation→interface, an existence edge between two implementations, an interface edge not targeting an interface), a required field is missing, or a field outside the vocabulary is present |
| `urn:agentic:problem:adapter-unavailable` | 503, retryable | This binding cannot serve the operation (the dry-run store made unreachable, the event log made unreachable, or a live-ledger env var unset) |

**Pending registry row** (core-graph's own open question): `graph-assertion-invalid` is this harness's proposed name; `docs/decomposition.md` section 2.1.6 has no row for a refused graph assertion yet. Until it does, this is marked `proposed` in `provenance.json`, following the skill's own stated default.

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A node identified by a file offset or a row key | `node_id` is a name matched against a pattern (`^[a-z0-9][a-z0-9._-]{2,127}$`); no adapter's own identifier scheme ever reaches `Node` or `Edge` |
| A caller checking edge validity by asking a store | `assert_edge` and `validate` take a `nodes`/`GraphValue` argument already in memory; neither ever calls an adapter method, so the ill-typed-edge case in `call.py` runs with no adapter instantiated for it at all |
| A walk implemented as "load the graph and filter" | `neighbors` and `path_exists` take an `edge_type`/`max_depth` and stop after that many hops; case 7 in `conformance.py` asserts a bound refuses reachability outside it |
| A rule that only the type checker's own code path enforces, so widening it silently widens every check of it | `conformance.py`'s `_oracle_invalid` is a duplicated, independently authored ground truth; `test.sh` step 4 widens `interface.check_edge_type` itself and shows the oracle still catches the counterexample |
| A store that interprets a record instead of returning it opaquely | `GraphAdapter._store_record`/`_all_records` pass dicts; `fold()` — the only code that knows what `node-asserted`/`edge-asserted` mean — lives in `interface.py`, imported by every adapter, never duplicated inside one |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof, the cross-store check and the breakage | Measured by `test.sh`: 20 checks, 0 failures |
| The live adapter's read path (`graph_value` via `_read_all`) | Measured, read-only, against a scratch copy of `kb/ledger.jsonl` with three fabricated `graph_partition`-tagged records appended: `nodes_checked=2 edges_checked=1 rejections=0 false_accepts=0` |
| The live adapter's write path (`append_node`/`append_edge`, via `tools/kb.py ledger`) | Claimed. Never invoked here: appending unreviewed test records into the project's actual ledger was judged out of scope for a dry run |
| The second adapter's real served-log transport (a networked cursor consumer rather than a local directory) | Claimed. `GRAPH_EVENTLOG_DIR` was exercised only against a local scratch directory; the self-identified-record and cursor-CAS design is what a real served log's client would also need, but no such service was pointed at here |
| Concurrent writers racing the second adapter's cursor claim | Claimed by design (the rename is atomic and the sequence is read fresh on every claim), not exercised: this harness's runs are single-process and sequential |
| Whether an agent is a node kind of its own, and whether one `existence` edge type is enough for both containment and derivation | Open questions core-graph itself leaves open (see its `open_questions`); this harness ships the five-kind, three-type set as specified and does not resolve either |
