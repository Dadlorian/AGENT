# Scheduling harness — recurrence as a pure function, firing as an entry

One recurrence rule, one time zone, one window in; the occurrence set out,
computed by a pure function no adapter may recompute differently. A fired
occurrence enters through the same envelope schema `entries/schedule.json`
already uses (`examples/end-to-end/schemas/entry.schema.json`).

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/scheduling/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/scheduling/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/scheduling/call.py` |
| 4. Run the vector corpus | `python3 harness/scheduling/conformance.py --vectors --adapter dryrun --adapter second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `parse_rule`, the shared pure `occurrences()`/`next_after()`/`generate()` evaluator, `ScheduleDeclaration`, `build_envelope` (the one envelope builder every adapter shares), `idempotency_key`, `ConformanceReport`, `Problem`, and `SchedulingAdapter` with `occurrences`, `next_after`, `declare`, `fire`, `tick`. `declare` and `fire` are concrete so no adapter can build its own envelope or skip the rule-part refusal |
| `adapters/dryrun.py` | Synchronous standalone evaluator: `declare` and `fire` run entirely in the call, no queue |
| `adapters/live.py` | Today's component: engine-owned schedules (Temporal), reached only through env vars. Refuses `BYSETPOS` at declare time (its calendar spec cannot express it) and reports `adapter-unavailable` for everything else — PASS.md A6 records the server not listening |
| `adapters/second.py` | The second adapter: the standalone evaluator behind a ticker (`enqueue`) and a queue (`drain`) — two observable steps a synchronous call has none of |
| `call.py` | The minimal call: 19 lines below the `>>> CALLER CODE` marker — declare, tick, read the fired envelopes, replay one for free |
| `conformance.py` | The case suite every adapter passes (`--adapter`), and the vector-corpus run (`--vectors`) that produces the `RecurrenceConformanceReport` shape |
| `tests/vectors/rfc5545/vectors.json` | 43 hand-derived vectors: rule, zone, window, expected occurrences, one of five classes (`dst_forward`, `dst_back`, `leap_day`, `bysetpos`, `general`) |
| `test.sh` | The gate: conformance, the vector corpus, the swap proof, one deliberate breakage |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `adapter.declare({...})` | Registers one unit's recurrence, zone, anchor and catch-up policy. Refuses a malformed rule or a part this adapter cannot evaluate |
| `adapter.tick(now, window_s)` | Every occurrence the evaluator reports inside the window, each fired through the shared envelope builder |
| `adapter.fire(unit_ref, occurrence)` again | The same idempotency key, the same envelope — a replay, not a second fire |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `UNIT_REF` | `nightly-fault-sweep` | The declared unit |
| `RECURRENCE` | `FREQ=DAILY;BYHOUR=2;BYMINUTE=0` | The RRULE string |
| `STARTS_AT`, `TZ_NAME` | `2026-09-01T02:00:00`, `UTC` | The anchor and its IANA zone |
| `NOW`, `WINDOW_S` | `2026-09-01T00:00:00Z`, `259200` | The tick window (3 days) |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `SCHEDULING_ENGINE_ADDR` | yes | `host:port` of the engine's frontend, gRPC `7233` (PASS.md A6: data directory present, server not listening) |
| `SCHEDULING_ENGINE_NAMESPACE` | no | Namespace the schedules live in, default `default` |
| `SCHEDULING_TIMEOUT_S` | no | Probe timeout in seconds, default 5 |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 7/7 | Declare, fire, replay, and four typed refusals hold with no network |
| 1a | Vector run: `vectors_run=43`, `mismatches=0`, all four classes covered | The evaluator matches its hand-derived expected occurrences, over 40 vectors, across every DST/calendar class the definition of done names |
| 1b | One vector per class printed directly | A DST-forward gap, a DST-back repeat, a leap day and a BYSETPOS rule are each visible, not only counted |
| 1c | Caller code is 19 lines, under 40 | One call is one call |
| 1c | `RECURRENCE=not-a-rule` exits 2 with `document-invalid` | A malformed rule is refused before any adapter state changes |
| 1d | `ADAPTER=live` with no engine reachable exits 2, no traceback | The live binding fails closed and typed, not with a crash |
| 1d | The live binding's own 7 cases still pass, `declared: 0` | A failed registration is never miscounted as a success |
| 2 | Conformance before (dryrun) and after (second), 7/7 each; `sha256` of `interface.py`+`call.py`+`conformance.py` identical | The swap was configuration, not a code edit |
| 2 | 43/43 vectors identical between `DryRunAdapter` and `TickerQueueAdapter`, read directly off both | Both adapters produce identical occurrence sets, vector for vector |
| 2 | `enqueue`/`drain` show a non-empty queue mid-flight | The second adapter's execution model (ticker, then a separate consumer) is real, not a relabelled synchronous call |
| 3 | `product_hits=0` over the code outside `adapters/` | No product name leaks past the adapter boundary |
| 4 | The idempotency key is minted from wall-clock time instead of unit+occurrence: the case suite fails on the replay case, `mismatches=0` on the vector corpus | The defect is isolated to firing, not the RFC 5545 math — the two are independently testable |
| 5 | `--live`: the same 7 cases against `SCHEDULING_ENGINE_ADDR` | Skipped with a message when the env var is unset. Nothing live has been measured here |

## The two adapters behind one interface

| Axis | `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Who owns the firing timer | the engine itself | this platform's own ticker |
| How firing is observed | one opaque call to the engine | `enqueue` then `drain`, two steps, a queue in between |
| What a crash between firing steps leaves behind | nothing observable from here | a non-empty queue a second process can drain |
| Rule parts refused at declare time | `BYSETPOS` (its calendar spec cannot express it) | none (the standalone evaluator implements the whole grammar this harness supports) |
| Reachability | claimed: PASS.md A6 records the server not listening | measured here: an in-memory queue, or a JSONL file at `SCHEDULING_QUEUE_PATH` |
| Swap procedure | `ADAPTER=live` | `ADAPTER=second`; no code edit, same vector corpus, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The recurrence string is not `FREQ=...;PART=value;...`, `catch_up` is outside `skip`/`fire_once`/`fire_all`, a window is malformed, or `fire` names a unit that was never declared |
| `urn:agentic:problem:unsupported-rule-part` | 422 | The rule uses a `FREQ` or a part outside `{DAILY,WEEKLY,MONTHLY,YEARLY}` / `{INTERVAL,COUNT,UNTIL,BYDAY,BYMONTH,BYMONTHDAY,BYSETPOS,BYHOUR,BYMINUTE,BYSECOND}`, or the selected adapter's own `declared_gaps` (live: `BYSETPOS`) |
| `urn:agentic:problem:adapter-unavailable` | 503 | The engine cannot be reached, or an adapter's own failure path (`SCHEDULING_DRYRUN_FAIL=1`, `SCHEDULING_SECOND_FAIL=1`) is exercised |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A caller computing "next Tuesday" from an engine's own cron-family calendar spec | `occurrences()`/`next_after()` are one pure function over RFC 5545 grammar, shared by every adapter (F-b3-15); an adapter's execution model differs only in how it declares and fires |
| Recurrence read from wherever the engine happens to store it | The declaration (`unit_ref`, `recurrence`, `starts_at`, `timezone`, `catch_up`) is the whole migration boundary and never moves; `interface.py` is what changes between the two runs of the vector corpus — nothing does |
| A schedule becoming a fifth, privileged way into the platform | `fire()` always returns the same envelope shape `T-t6-02` fixes for a human, event, schedule or external entry — `kind: "schedule"`, nothing more |
| A retry or a catch-up firing the same occurrence's side effect twice | The idempotency key is derived from `unit_ref` + occurrence instant only, never from wall-clock firing time (cap-scheduling-implement step 6); check 4 breaks exactly that derivation to prove it |
| An engine's own cron semantics silently swallowing a declared zone (its own scheduler is UTC by default) | The zone is a required field on every declaration and every evaluator call; the vector corpus's `dst_forward`/`dst_back` classes assert the computed instant actually shifts across a transition, not a fixed 24h step |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the vector corpus, the swap proof and the breakage | Measured by `test.sh`: 35 checks, 0 failures |
| Live mode against `SCHEDULING_ENGINE_ADDR` | Claimed. PASS.md A6 records the engine's data directory present but its server not listening; `adapters/live.py` has never reached a frontend from here |
| The vector corpus's expected occurrences | Hand-derived from RFC 5545 semantics by the evaluator that ships here; 8 of the non-DST vectors were independently cross-checked against `python-dateutil`'s `rrule` on the authoring host and matched byte for byte (not a shipped dependency — stdlib `zoneinfo` only ships in `interface.py`) |
| The DST-gap and fall-back-repeat convention (`fold=0`, Python's default) | A documented design choice, not a fact RFC 5545 itself settles — cap-scheduling's own open research question asks whether the standard fixes this at all |
| The standard's version | Unverified: every record on file for it is a search result, not a fetched page |
