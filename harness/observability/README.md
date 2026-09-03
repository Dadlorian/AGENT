# Harness: observability

Capability: telemetry. Standard: OTLP with GenAI semantic conventions (unverified).
One run, one trace, reassembled by grouping on an attribute and never by trace parentage.

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface only: the correlation record, the unit, the signal, RFC 9457 problem details, the closed registry, the attribute mapping, the report shape, and the abstract adapter with `bind`, `emit`, `measure`, `describe_mapping`, `fetch_run`. No product name. |
| `adapters/dryrun.py` | Deterministic, in-process, no network. Serialises on the way in and parses on the way out, so a read crosses a real boundary. Exercises the failure path. |
| `adapters/live.py` | Today's component, reached only through the env vars below. Posts OTLP/HTTP JSON with `urllib` under a guarded import. |
| `adapters/second.py` | A collector pipeline into a columnar store: receive, redact, export flat rows. Different wire, different execution model, same interface. |
| `call.py` | The minimal call. The caller writes an intent and a payload; the platform stamps the rest and owns the dispatch seam. |
| `conformance.py` | The same eight cases against any adapter, plus `--merge` for the swap proof and `--break-stamp` for the breakage. |
| `test.sh` | The gate. Dry-run is measured here; `--live` is skipped with a message when the env vars are unset. |
| `provenance.json` | Owner skill, co-skill, blueprint entry, kb and research ids, and what is measured versus claimed. |

## The minimal call

| Step | Command or code |
|---|---|
| Run it | `ADAPTER=dryrun python3 harness/observability/call.py` |
| Swap the backend | `ADAPTER=second python3 harness/observability/call.py` — configuration only, no code edit |
| What the caller writes | `enter(kind="human", intent={...}, payload={...})` — 17 lines below the `>>> CALLER CODE` marker, counted and asserted under 40 by `harness/caller_lines.py` from `test.sh` |
| What the platform stamps, unasked | correlation record (`run_id`, `root_dispatch_id`, `depth`, `entry_kind`), budget ceiling, idempotency key, actor subject |
| What comes back | one result, or one problem object — never both, never a third kind |
| What it prints | one row per signal with its level, its own minted trace id, and its `run.id`, then the proof line |
| The proof | `distinct trace ids: 3 · groups on run.id: 1 · levels covered: 3/3 · spans missing run.id: 0` |

## The attribute mapping, version `agentic-genai-mapping/0.1`

| Correlation field | Resource attribute | Note |
|---|---|---|
| `run_id` | `run.id` | The grouping key. Equality on it returns one group per run whatever the trace ids say. |
| `root_dispatch_id` | `correlation.id` | The same value the co-skill names `root_dispatch_id`: the dispatch the run entered through. |
| `parent_dispatch_id` | `correlation.parent_id` | Recorded below depth 0, never used to reassemble. |
| `depth` | `correlation.depth` | |
| `entry_kind` | `entry.kind` | Human, event, schedule or external; nothing downstream branches on it. |
| — | `telemetry.mapping_version` | Read back off the wire by the report, never from the configuration that set it. |

## Env vars for live

| Variable | Required | Meaning |
|---|---|---|
| `TRACE_URL` | yes | OTLP/HTTP JSON trace ingestion endpoint of `observe-langfuse-web-1` (Langfuse, trace UI and ingestion API) |
| `TRACE_KEY` | yes | The credential value that endpoint expects |
| `TRACE_AUTH_SCHEME` | no | `Bearer` by default; set `Basic` where the deployment authenticates that way |
| `TRACE_QUERY_URL` | no | The read-back surface; the run id is appended as `run_id`. Unset, `fetch_run` returns problem details rather than guessing at an endpoint. |
| `TRACE_TIMEOUT` | no | Seconds, default 10 |
| `COLLECTOR_URL` | no | Second adapter: the collector's OTLP/HTTP receiver. Unset, the pipeline runs in process. |
| `COLLECTOR_STORE` | no | Second adapter: a path the columnar rows are appended to as JSON lines |
| `ADAPTER` | no | `dryrun` (default), `live`, `second` |

## The adapter pair

| Adapter | Execution model | Wire | Semantic queries | Role |
|---|---|---|---|---|
| `dryrun` | In-process object store, deterministic, no network | Serialised dicts | declared supported | Runs here so the whole interface, including the failure path, is exercised with nothing installed |
| `live` | Hosted service with a model-aware ingestion API, reached over the network | OTLP/HTTP JSON | declared supported | Today's component |
| `second` | Local receive-process-export pipeline into a columnar store, no service behind it | OTLP/HTTP JSON, read back by parsing rows | declared **unsupported**, rather than reported false-with-an-asterisk | The second adapter: a different execution model, not a different product of the same shape |

## What each test proves

| Test | What it proves |
|---|---|
| 1. conformance against `dryrun` | A depth-3 run whose every level mints its own root trace still reassembles: `levels_covered == 3`, `run_id_groups == 1`, `spans_missing_run_id == 0`, `spans_missing_root_dispatch_id == 0`, mapping version read off the wire. `distinct_trace_ids == 3` is reported and never constrained. |
| 2. swap proof | The identical run against `second`, selected by `ADAPTER=`; both exit 0, the merged report shows `adapters_run == 2` and `selected_by == "configuration"`, and the six correlation counters are identical across the pair. The two adapters differ on `semantic_queries_supported`, so the pair is not one thing run twice. |
| 3. the minimal call | The caller's output is byte-identical whichever adapter answered, so nothing downstream can tell them apart. |
| 4. deliberate breakage | Stop re-stamping at the child-dispatch boundary and let the child agent mint its own identifiers: both adapters exit 1 with `levels_covered == 1`, `run_id_groups == 0`, `spans_missing_run_id == 2`, identically — which locates the fault in the dispatch path rather than in either adapter, and reproduces PASS.md A7 finding 1. |
| 5. the failure path | An unreachable adapter and an unknown run answer with RFC 9457 problem details typed from the closed registry; a type still marked proposed falls back to the registered one rather than being minted. No traceback reaches the caller. |
| 6. the boundary in the source | No product name in `interface.py`, `call.py` or `conformance.py`; caller code 17 lines, under 40, naming no adapter storage (`harness/caller_lines.py`); the unit shape has nowhere to put a parent span, so no implementation can quietly rely on parentage. |

## What would pin the integration, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| An emitter carrying the backend's own SDK types | Emitters build `TelemetryUnit` and hand it to `emit`; both backends receive byte-identical OTLP/HTTP JSON from one shared builder, and the second adapter reads back by parsing the wire — an interface that had leaked in-memory types could not feed it at all. |
| A query that starts from a parent span rather than a stamped attribute | `TelemetryUnit` has no parent field and no operation takes a parent; `reassemble` groups on `run.id` and reads no trace id. `test.sh` asserts both. |
| The vocabulary half moving at the transport half's cadence | The mapping table and its version sit in front of both adapters; a revision is one edit and a version bump, and no emitter contains a literal attribute key. |
| A caller able to tell which backend answered | The interface names no destination, query language or UI concept; `emit` and `measure` return nothing, and no operation takes a sampling or enable argument — asserted as case C1. |
| A field that exists only in the hosted backend's object model | Anything the pipeline adapter cannot accept must not appear on the interface; `semantic_queries_supported` is declared per adapter and reported, never asserted. |
| The backend being replaced | The blueprint's impact row for this component reads: affected adapters, the telemetry adapter; affected tests, the telemetry conformance run; core unaffected. That is this harness's test 2. |
