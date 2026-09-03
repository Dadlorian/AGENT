# Document-validation harness — a declared shape against a published dialect

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/document-validation/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/document-validation/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/document-validation/call.py` |
| 4. Prove the interface held | `python3 harness/document-validation/conformance.py --adapter dryrun --adapter second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `ValidationRequest`, `ValidationOutcome`, `ValidationError`, `PreparedHandle`, `Problem`, and `DocumentValidationAdapter` with `prepare`, `dialect_in_effect`, `validate`, `check_schema`. `prepare` and `validate` are concrete, so no adapter can skip the dialect gate (a schema declaring no dialect, or one other than 2020-12, is refused before any instance is checked) |
| `adapters/_walk.py` | Shared walk-per-document check (used by `dryrun.py` and `live.py`): re-interprets the raw schema dict on every call, one JSON Schema 2020-12 keyword subset — `$ref`, `anyOf`, `if`/`then`/`else`, `type`, `const`, `enum`, `pattern`, `min`/`maxLength`, `minimum`/`maximum`, `minItems`, `contains`, `items`, `required`, `properties`, `additionalProperties` |
| `adapters/dryrun.py` | Deterministic, in-process, no network, no env var. Reads schema files straight off this repo's disk. `DRYRUN_FAIL=1` exercises the failure path |
| `adapters/live.py` | Today's component (F-b3-09: "in place") reached only through `DOCVALID_SCHEMA_STORE_DIR` — a real, operator-named schema store on this host |
| `adapters/second.py` | The second adapter: compiles the schema once in `prepare()` into a tree of closures, then checks instances against the compiled form — a different execution model, never re-reading schema structure per call. `DOCVALID_SECOND_SUBPROCESS=1` hands the compiled check to a short-lived child process instead |
| `adapters/_second_worker.py` | The out-of-process half of `second.py`, used only when `DOCVALID_SECOND_SUBPROCESS=1` |
| `schemas/sample.schema.json` | Harness fixture exercising `$ref`, `if`/`then`, `contains`, array `items` together |
| `schemas/anyof.schema.json` | Harness fixture where `anyOf` is the schema's only top-level keyword |
| `schemas/bad-dialect.schema.json`, `schemas/no-dialect.schema.json` | Fixtures for the dialect refusal cases |
| `call.py` | The minimal call. 10 lines below the `>>> CALLER CODE` marker, counted directly by `test.sh` |
| `conformance.py` | The 14 cases every adapter passes, plus the validator-library-name scan over code |
| `test.sh` | The gate: 24 checks in dry run (27 with `--live`), the swap proof, and one deliberate breakage |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `ask = envelope(schema_uri, instance_kind)` | One entry envelope; the platform stamps correlation id, idempotency key and actor into it without being asked |
| `outcome = adapter.validate(ValidationRequest.from_dict(ask["payload"]))` | One document checked against one schema resource. Refuses a schema declaring no dialect, or one other than 2020-12, before any instance is checked |
| `except Problem as problem: print(problem.body)` | One handler for every failure, branched on `type`, never on prose |
| `show(outcome)` | valid, dialect, schema_uri, error count, the first violation's pointer and message |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `SCHEMA_URI` | `examples/end-to-end/schemas/entry.schema.json` | The schema resource to validate against |
| `INSTANCE_KIND` | `malformed` | `malformed` (5 required fields missing) or `valid` (a well-formed entry envelope) |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |
| `DRYRUN_FAIL` | unset | `1` makes the dry-run schema store unreachable, to see the refusal |
| `DOCVALID_SECOND_SUBPROCESS` | unset | `1` runs the second adapter's compiled check in a child process instead of in-process |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `DOCVALID_SCHEMA_STORE_DIR` | yes | Directory `live.py` resolves every `schema_uri` inside. Point it at this repo's root to run the same conformance suite live (`SCHEMA_URI` values are repo-relative paths); point it elsewhere to validate against a different operator-controlled schema store |

There is no networked "document validation" service on PASS.md's tool list for this capability (F-b3-09 records the tool only as "in place" — the checker `examples/end-to-end/run.py` already carries). `live.py` proves the same walk-per-document adapter serves a real, operator-named schema store rather than the harness's own bundled fixtures, which is what "live" means for a capability whose component has no endpoint or key.

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 14/14 | Validation, the dialect gate, the failing pointer, `check_schema`, `prepare` caching, `dialect_in_effect` and the outcome shape all hold with no network |
| 1b | Caller code is 10 lines, under 40, names no adapter storage | One call is one call; the stamps are the platform's work, not the caller's |
| 1b | `SCHEMA_URI=…bad-dialect…` exits 2 with `dialect-unsupported` 422 | A schema declaring a dialect other than 2020-12 is refused, not silently checked |
| 1c | `DRYRUN_FAIL=1` exits 2 with `schema-unavailable` 503 | The failure path is exercised, not only the happy one |
| 2 | Conformance before (dryrun) and after (second), 14/14 each | The interface held across a swap of the execution model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | `execution_model` and `schema_reads` differ between reports | The second adapter breaks a different assumption: compile-once versus walk-per-document |
| 2 | Every shared fixture's `{valid, dialect, errors}` is identical between the two reports | Both adapters give the same outcome on the same fixtures |
| 3 | `product_hits=0` over the code | No validator library name outside `adapters/` |
| 4 | An import of a validator library injected into a copy of `call.py` makes the scan exit 1 and names the file | The green scan in step 3 can fail; the two adapters are one interface |
| 5 | `--live`: the same cases against `DOCVALID_SCHEMA_STORE_DIR` | Skipped with a message when the env var is unset |

## The two adapters behind one interface

| Axis | `adapters/dryrun.py` / `adapters/live.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Start and teardown cost | schema read per call — the raw dict is walked fresh every `validate()` | schema compiled ahead of use — `prepare()` builds a closure tree once, reused across instances |
| Processes required for progress | 0 | 0 by default; 1 when `DOCVALID_SECOND_SUBPROCESS=1` hands the compiled check to a child process |
| Where the schema resource lives | this repo's disk (`dryrun.py`) or an operator-named store (`live.py`) | this repo's disk, same resolution as `dryrun.py` |
| Swap procedure | `ADAPTER=dryrun` or `ADAPTER=live` | `ADAPTER=second`; no code edit, same fixtures, compare the two reports' `outcomes` |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:request-invalid` | 400 | The validation request names a field outside the vocabulary, or is missing `schema_uri`, `dialect` or `instance` |
| `urn:agentic:problem:dialect-unsupported` | 422 | The schema resource declares no `$schema` dialect, or one other than the caller's expected dialect |
| `urn:agentic:problem:schema-unavailable` | 503, retryable | The schema resource could not be read (missing file, unset `DOCVALID_SCHEMA_STORE_DIR`, malformed JSON) |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A field naming a validator library or its native error class | `ValidationOutcome` carries only `valid`, `dialect`, `schema_uri`, `keywords_checked` and `errors` (each `instance_location`, `keyword_location`, `message`) — a conformance case asserts the outcome has exactly those fields and no library name appears in it |
| A schema silently checked against an assumed dialect | `check_dialect()` runs before any instance is checked, on every adapter, because it lives in the base class's `prepare()`, not in adapter code |
| A caller learning which adapter answered, then branching on it | Nothing in `ValidationOutcome` names the adapter; only the conformance report (never returned to a caller) carries `execution_model` |
| Treating "in place" as meaning no second execution model is possible | `adapters/second.py` proves a compile-once adapter is a real, different implementation of the same interface, not a redefinition of what "in place" means |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 24 checks, 0 failures |
| `--live` against `DOCVALID_SCHEMA_STORE_DIR` | Measured by `test.sh --live` when the env var is set: 27 checks, 0 failures. Claimed as a general "live" component beyond this: no separate networked document-validation service exists on PASS.md's tool list for this capability (F-b3-09) |
| `DOCVALID_SECOND_SUBPROCESS=1`'s out-of-process path | Measured to run and produce the same outcomes as the in-process path for the fixtures in `conformance.py`, not load-tested |
| The standard, "JSON Schema 2020-12" | Version unverified: every record on file for it (`X-cap-document-validation-001..006`) is a search result, not a fetched page (absent by owner, STATUS row 45: page fetch is blocked in this environment) |
| The 2020-12 keyword subset both adapters support | Matches exactly what `examples/end-to-end/run.py`'s in-place checker already supports; not the full 2020-12 vocabulary, and no case in `conformance.py` exercises a keyword outside that subset |
