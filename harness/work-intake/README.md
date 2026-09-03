# Work-intake harness — one document, four producers, one job

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/work-intake/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/work-intake/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/work-intake/call.py` |
| 4. Prove the interface held | `python3 harness/work-intake/conformance.py --adapter dryrun --adapter second` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 299 | The capability interface: `ProducerMessage`, `Envelope`, `Acknowledgement`, `Manifest`, `Problem`, and `WorkIntakeAdapter` with accept, normalise, job_digest, admit. `accept` and `admit` are concrete, so no binding can decline the unmapped-producer refusal, the schema check or the replay check. `resolve_manifest` is a pure function outside every adapter, because intake admits and does not plan |
| `producers.py` | 60 | The four doors and the one document, read from `examples/end-to-end/entries/*.json`. Nothing is invented here: the door identities and the job are the fixtures the end-to-end example already ships |
| `adapters/dryrun.py` | 93 | The request-pushed producers in process: a command line, a repository event, a schedule occurrence and an event pushed over a request — the four PASS.md B3 records today, one mapper each. No network, same bytes every run. Failure path on `INTAKE_FAIL=1` |
| `adapters/live.py` | 136 | Today's component: a structured event POSTed to `INTAKE_URL`, via `urllib` behind a guarded import. Product names live here |
| `adapters/second.py` | 145 | The second execution model: an agent submits a task and detaches, so the acknowledgement is recorded for collection instead of read off the wire by whoever sent it |
| `call.py` | 91 | The minimal call. 17 lines below the `>>> CALLER CODE` marker, counted by `harness/caller_lines.py`; everything above it is presentation and the platform's stamps |
| `conformance.py` | 322 | The 15 cases every binding passes, plus the product-name scan over code |
| `test.sh` | 153 | The gate: 28 checks in dry run, the swap proof, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of the entries in `harness/plan.json`, for the orchestrator to merge |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = BINDINGS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `adapter.accept(adapter.render_message(door, producers.SUBJECT))` | One producer-native message in, one canonical envelope out. Refuses an unregistered producer (403), a malformed task (422) and an unmappable message (422) before anything is recorded |
| `adapter.admit(envelope)` | An acknowledgement: entry id, correlation id, job digest, accepted. Never a result — the producer may be gone before anything runs |
| `resolve_manifest(envelope)` | The priced plan, resolved outside the adapter as a pure function, so the doors can be compared without running anything |
| `adapter.admit(rows[0][1])` | The same key again: `duplicate_of` is set and no entry is written |
| `except Problem as problem: fail(problem)` | One handler for every failure, branched on `type`, never on prose |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `INTAKE_FAIL` | unset | `1` makes the dry-run intake path unreachable, to see the typed failure |
| `INTAKE_EXAMPLE_DIR` | the repo's `examples/end-to-end` | Where the fixtures and the entry schema are read from; the gate's breakage run relocates the tree and points this at the same corpus |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `INTAKE_URL` | yes | The whole URL of the intake endpoint on this host, supplied by the operator. PASS.md records an Ansible role named `git_events` among the nine configuration-management roles (A5) and the producers today as CLI, git event, HTTP and schedule (B3); no path, port or payload profile for any of them is on file, so none is invented here |
| `INTAKE_TOKEN` | no | Bearer token for that endpoint, when it wants one |
| `INTAKE_TIMEOUT_S` | no | Per-request timeout in seconds, default 30 |
| `INTAKE_A2A_URL` | no | Full URL of the agent-messaging route for `adapters/second.py`. Unset means the in-process state machine runs |
| `INTAKE_A2A_METHOD` | no | The protocol method name, supplied by the operator: both records on file for the protocol are search results, not fetched specification text, so no method name is asserted here. Required whenever `INTAKE_A2A_URL` is set |
| `INTAKE_A2A_TOKEN` | no | Bearer token for that route |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 15/15 | Normalisation, equivalence, the schema, the refusals, the replay and the marker all hold with no network |
| 1 | `distinct_job_digests=1 distinct_entry_ids=4` | One logical job submitted four ways is one job and four submissions — the definition of normalised |
| 1 | `invalid=0 untyped_refusals=0` | Every envelope passed the published schema and every refusal was problem details |
| 1b | Caller code is 17 lines, under 40, and names no adapter storage | One call is one call. Measured by `harness/caller_lines.py`, the one method the harnesses share, with this row appended in-process because the file's roster is fixed to the five rows of `harness/plan.json` |
| 1b | `call.py` prints one job digest, one resolved manifest, four submissions | The four doors produce one identical envelope job and one identical resolved manifest |
| 1b | `duplicate_of=…, still 4 entries recorded` | A replay under the same idempotency key is free |
| 1b | `urn:agentic:problem:document-invalid` | A malformed task gets a typed refusal, not prose and not a stack trace |
| 1c | `INTAKE_FAIL=1` exits 2 with `adapter-unavailable` 503 | The failure path is exercised, not only the happy one, and nothing was admitted |
| 2 | Conformance before (dryrun) and after (second), 15/15 each | The interface held across a swap of the execution model |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py`, `producers.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | 4 execution-model axes differ; job digest and manifest digest identical | The second binding breaks different assumptions and still produces the same job — the swap test and the normalisation test are one run |
| 2 | Merged run: `adapters_run=2`, `selected_by=configuration` in both | The definition of done's merged assertion, run here |
| 3 | `product_hits=0` over the code | No product name outside `adapters/` |
| 4 | The request-pushed mapper stamps a default `priority`: that run exits 1 with `invalid` 0 → 4 while the agent-message run still exits 0 | The green run in step 1 can fail, and the suite singles out one adapter. A run that failed both, or neither, would not have tested the swap |
| 5 | `--live`: the same 15 cases against `INTAKE_URL` | Skipped with a message when the variable is unset. Nothing live has been measured here |

## The two adapters behind one interface

| Axis | `adapters/live.py` and `adapters/dryrun.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| How a producer submits | builds a message and hands it over in one hop | sends a task message and detaches |
| Is the producer there for the answer | yes, it is holding the submission open | no, it may be gone before anything runs |
| How the acknowledgement is delivered | inside the same hop | recorded for later collection |
| Which producer identity becomes the key | the producer's own message identity (source plus id) | the submitting agent's message identifier |
| What the correlation looks like | root: depth 0, no parent | the agent's own correlation becomes the parent, depth 1 |
| Who the first delegation hop is | the producer that built the message | the submitting agent's attested identity, ahead of the door's own chain |
| Swap procedure | `ADAPTER=dryrun` / `ADAPTER=live` | `ADAPTER=second`; no code edit, same corpus, compare the two reports |

## Failures a producer can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The envelope fails the published schema, or the mapper cannot map the message |
| `urn:agentic:problem:policy-denied` | 403 | The producer's format has no registered mapper. Carries `rule_id: refuse-unmapped-producer` |
| `urn:agentic:problem:idempotency-conflict` | 409 | The same key arrives with a different job |
| `urn:agentic:problem:adapter-unavailable` | 503 | The intake path cannot be reached. Nothing was admitted |

Every row is a row of the closed registry in `docs/decomposition.md` section 2.1.6. Intake mints no failure type of its own.

## What would pin this to a component, and how the boundary avoids it

| Would pin | How this harness avoids it |
|---|---|
| A producer attaching a field of its own to every job | Every producer here sends `priority` on every message; a conformance case asserts it reaches no envelope, and the schema's `additionalProperties: false` refuses it if a mapper ever stamps it |
| A transport handle riding along in the envelope — a request id, a repository ref, a command line, a broker offset, a message id | `ProducerMessage.transport` is what the adapter observed; a case asserts no member of it appears anywhere in the envelope |
| An intake that returns a result, so the producer must hold a connection open | `ack_carries_result` is a const false on the interface, and a case asserts the acknowledgement's field set. The second adapter's producer could never be served otherwise |
| An intake that also starts work, which could not be swapped for a mapper | `work_started` is counted and asserted zero; `resolve_manifest` is a module-level pure function and a case asserts no adapter has one |
| A key minted on arrival, so a retry becomes a second job | The key is derived from the producer's own message identity, and the replay case asserts a resubmission writes nothing |
| A door with a field the others lack, or a new front door per producer | `DOOR_FIELDS` names the six members a producer may differ on; the job digest and the resolved manifest are computed over everything else and asserted equal across four doors and both bindings |
| A refusal a human has to read | Every refusal is a registered problem type; `untyped_refusals` is a counter in the report, and a mapper that trips is converted into `document-invalid` rather than a stack trace |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 28 checks, 0 failures |
| Live mode against `INTAKE_URL` | Claimed. No intake endpoint has been reached from here, so the request shape, the acknowledgement body and the headers are unverified against a real endpoint |
| The second adapter's networked form | Claimed until `INTAKE_A2A_URL` and `INTAKE_A2A_METHOD` point at a real route; the dry run exercises its mapping and its detached acknowledgement in process |
| The standards, "A2A messaging and CloudEvents" | Versions unverified: every record on file for either is a search result, not a fetched page (STATUS row 45 records the fetch block) |
| The identity on an envelope | The delegation chain is new construction: PASS.md A6 records no identity field anywhere in the system, so the chain here is supplied by the producer fixtures and attested by nobody |
| The `priority` attribute, the transport members and the four producer message shapes | Proposed test fixtures. No producer payload profile for this host is on file |
