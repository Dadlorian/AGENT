# Provenance harness

One signed statement binding an artifact to the code version, inputs and actor that produced it,
checked from the envelope alone. Capability: provenance. Standard: in-toto Statement v1 in a DSSE
envelope with SLSA predicates (versions on file unverified). Blueprint tool entry: the JSONL
evidence records PASS.md B3 names today (F-b3-12); `kb/ledger.jsonl` is the live instance of that
shape. Second adapter: Sigstore, or any attestation store.

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability only: `AttestRequest`, `Envelope`, `Receipt`, `Location`, `TrustPolicy`, `VerifyResult`, `Problem`, and the `ProvenanceAdapter` operations `attest`, `verify`, `resolve`, `publish`. `verify()` is a module function that reads no store and no adapter. No product name. |
| `adapters/dryrun.py` | Local signed records: a key this deployment holds, envelopes appended beside the record in a hash chain. Runs here, no network. Failure path on `PROVENANCE_FAIL=1`. |
| `adapters/live.py` | The evidence records on this host (`kb/ledger.jsonl` today), read never written, with the signed envelope appended to a second file beside them. Env vars only. |
| `adapters/second.py` | Keyless signing with a public append-only log: an identity obtained per run and discarded, an inclusion proof returned with the envelope, and no ability to sign offline. |
| `call.py` | The minimal call, 22 lines of caller code below the `>>> CALLER CODE` marker. |
| `conformance.py` | The 13 cases every adapter passes, the store-unmounted verifier subprocess, the two breakages, the product scan and the caller-line count. |
| `test.sh` | The gate: conformance, the swap proof, the breakages; `--live` for this host. |
| `provenance.json` | Which skills, kb ids and research ids this harness stands on; what is measured and what is claimed. |
| `plan-entry.json` | This harness's row, in the shape of an entry in `harness/plan.json`. |

## The minimal call

`ADAPTER=dryrun python3 harness/provenance/call.py` (or `ADAPTER=second`, or `ADAPTER=live`).

| Step | The caller writes | What comes back |
|---|---|---|
| 1 | `adapter = ADAPTERS[os.environ["ADAPTER"]]()` | the binding, chosen by configuration |
| 2 | `adapter.attest(AttestRequest.from_dict(payload))` | a `Receipt`: a DSSE envelope over an in-toto Statement, and who signed it |
| 3 | `adapter.publish(receipt)` | a `Location` a third party fetches from, with an inclusion proof where the store is a log |
| 4 | `adapter.fetch(location.uri)` | the same envelope, byte for byte, plus the verifying material |
| 5 | `adapter.verify(envelope, policy, proof, material)` | `accepted` with the checks that were made |
| 6 | the same call with one byte of the artifact edited | rejected, `subject_mismatches=1`, as problem details 422 |
| 7 | `adapter.resolve(digest)` | every envelope naming that digest as a subject |

The caller never names a signer, a key, a store or a format, and there is no attest flag: a request
carrying one is refused 422 with nothing emitted. The correlation id, budget ceiling, idempotency
key and actor are stamped onto the envelope by `call.py` above the marker, without being asked.

## Env vars for live

| Variable | What it names | Unset |
|---|---|---|
| `EVIDENCE_STORE` | the live hash-chained evidence records to read (`kb/ledger.jsonl` on this host) | typed `adapter-unavailable` 503, nothing emitted |
| `ATTESTATION_STORE` | the file the signed envelopes are appended to, beside the records | as above |
| `PROVENANCE_KEY_FILE` | the file holding the key this host signs with (hex, at least 32 bytes) | as above |
| `TRANSPARENCY_LOG_URL`, `IDENTITY_URL`, `LOG_TIMEOUT_S` | the second adapter's log and identity routes, supplied whole by the operator | the same state machine runs in process |
| `PROVENANCE_FAIL`, `PROVENANCE_OFFLINE`, `SKIP_PROVENANCE`, `PROVENANCE_CLOCK` | the failure paths and the fixed clock the gate uses | off |
| `PROVENANCE_EXTERNAL_VERIFIER_BIN` | the name of an external verifier binary on PATH (e.g. `cosign`) that shares no codebase with this repository; `verifier_identity()` in `conformance.py` looks it up and reports it as the independent verifier when found | no such binary is looked for, `external_verifier_independent` is `false`, and the report says so in `external_verifier` (C11-F: the honest gap, not an in-repo substitute) |

There is no endpoint and no socket: today's component for this capability is a local store, so the
live adapter opens files and imports no network library at all.

## What each test proves

| Step in `test.sh` | What it proves |
|---|---|
| 1 | 13 conformance cases pass against the dry-run adapter, and the verification among them ran in another process with our store unreachable |
| 1b | the caller region is 22 lines, names no adapter storage, reads a verified statement, sees the one-byte edit rejected, and cannot opt out of provenance |
| 1c | the adapter's own failure path is a typed 503 that says nothing was emitted |
| 2 | the same 13 cases pass on the second adapter with the interface, caller and suite byte-identical between runs (one sha256 over all three), and the two bindings differ on 7 execution-model axes |
| 3 | no product name appears outside `adapters/` |
| 4 | the definition-of-done breakage: the artifact is rebuilt and the statement is not, so the run exits 1 with `subject_mismatches=1`, `attestations_verified=0` and a non-zero verifier exit, with the store still unmounted |
| 4b | a second breakage: an envelope whose signature is dropped is rejected on the second adapter too |
| 5 (`--live`) | the same 13 cases against the evidence records on this host, or a clear skip naming the env vars |

## What would pin, and how the boundary avoids it

| From the blueprint | The pin | How this harness avoids it |
|---|---|---|
| `would_pin`: a record shape only our own verifier can read | verification that has to walk our chain, our reader or our store | `verify()` is a module function taking an envelope and a trust policy; the gate runs it in a separate process with the store path pointed at somewhere that does not exist, and asserts no adapter module was imported |
| `must_stay_loose`: verification stays possible with a tool we did not write | a house format nothing else parses | the outer two layers are the published ones (`application/vnd.in-toto+json`, `_type https://in-toto.io/Statement/v1`, signature over the PAE); only the predicate is ours, and it is marked proposed |
| `pinning_risk` (state type): pins to a house record format if verification needs a tool we wrote | one store's assumptions leaking into the interface | the store is the swap axis: a hash-chained file and an append-only log both serve `publish`/`fetch`/`resolve`, and the local one declares inclusion proofs unsupported rather than reporting zero |

## What is claimed, not measured

| Claim | Why |
|---|---|
| verification by a tool nobody here wrote | no such verifier is available in this environment; the store-unmounted subprocess is this repository's own code, so the property measured is "reads only the envelope", not "reads a foreign verifier" |
| public verifiability | `hmac-sha256` over the PAE stands in for a signature (hashlib and hmac only, no signing library here), so the verifying material is the signing key; swapping it for an asymmetric signer changes `mac()` in `interface.py` and nothing else |
| the standards' versions | every record on file for in-toto, SLSA and DSSE is a search result, not a fetched page (STATUS row 45); the DSSE PAE spelling and the log's proof format are unverified for the same reason |
| the networked form of the second adapter | until `TRANSPARENCY_LOG_URL` and `IDENTITY_URL` point at real routes; the dry run exercises its state machine, its proof and its swap in process |
