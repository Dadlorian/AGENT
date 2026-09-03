# Capability-registry harness

One signed record per capability or agent, resolved by name and a version constraint, digest-matched
against the package it names, never edited in place. Capability: capability registry. Standard: MCP
Registry API v0.1, in preview (unverified; A-standard-mcp-registry-api). Blueprint tool entry: today's
resolution is by directory path in this repository - `.claude/skills/` indexed by
`docs/skill-manifest.json` (F-b3-07 "skill files"; blueprint state "registry record and version",
`home_today`: "capability packages resolved as files on disk"). Second adapter: a content-addressed
store fetching records over a network, per `cap-capability-registry-implement`'s adapters; a faithful
stub here (`E-swap-candidate-any-spec-conformant-registry`).

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability only: `PublishRequest`, `Query`, `CapabilityRecord`, `ResolutionOutcome`, `Verification`, `Problem`, and the `CapabilityRegistryAdapter` operations `resolve`, `list_versions`, `describe`, `publish`, `verify`. `resolve()` walks candidates newest-to-oldest, refusing and continuing on a bad signature or digest, never falling back outside the constraint. No product name. |
| `adapters/dryrun.py` | A signed, append-only, hash-chained index kept in process: a key this deployment holds, no network. Failure path on `REGISTRY_FAIL=1`. Carries `tamper`/`unsign` test hooks used only by `conformance.py`. |
| `adapters/live.py` | Today's component: `.claude/skills/` indexed by `docs/skill-manifest.json`, read never written, each skill signed and given a synthetic first version `1.0.0` the first time this adapter runs - the shadow-publish step of the proposed migration, run for real. Env vars only. |
| `adapters/second.py` | Content-addressed records fetched over a network: identity is the record's own content digest, not a path plus a version string, and it cannot sign or resolve while the endpoint is unreachable. |
| `call.py` | The minimal call, 28 lines of caller code below the `>>> CALLER CODE` marker. |
| `conformance.py` | The 11 cases every adapter passes, the digest-check-downgraded-to-a-warning breakage, the product scan and the caller-line count. |
| `test.sh` | The gate: conformance, the swap proof, the breakage; `--live` for this host. |
| `provenance.json` | Which skills, kb ids and research ids this harness stands on; what is measured and what is claimed. |
| `plan-entry.json` | This harness's row, in the shape of an entry in `harness/plan.json`. |

## The minimal call

`ADAPTER=dryrun python3 harness/capability-registry/call.py` (or `ADAPTER=second`, or `ADAPTER=live`).

| Step | The caller writes | What comes back |
|---|---|---|
| 1 | `adapter = ADAPTERS[os.environ["ADAPTER"]]()` | the binding, chosen by configuration |
| 2 | `adapter.publish(PublishRequest.from_dict(payload))` | an immutable `CapabilityRecord`, signed, digest of the package it names |
| 3 | `adapter.resolve(Query(name, ">=1.0.0 <2.0.0"))` | one record, chosen by semver ordering, with `verification` |
| 4 | `adapter.verify(record)` | `signature_verified` and `digest_matched`, checked in that order |
| 5 | publish a second version with a `rollback_to` field, then republish the first version | the republish is refused: a change is a new version, never an edit |
| 6 | `adapter.resolve(Query(name, "==" + record.rollback_to))` | the earlier record - a rollback is a resolution, not an edit |
| 7 | `adapter.verify(forged_record)` | `signature_verified=False`, never served |

The caller never names a store, an index file or a host, and there is no publish flag beyond the
package itself. The correlation id, budget ceiling, idempotency key and actor are stamped onto the
envelope by `call.py` above the marker, without being asked.

## Env vars for live

| Variable | What it names | Unset |
|---|---|---|
| `SKILLS_DIR` | the skill directories this host resolves by path (`.claude/skills`) | typed `adapter-unavailable` 503, nothing registered |
| `SKILL_MANIFEST` | the index naming which of them are registered (`docs/skill-manifest.json`) | as above |
| `REGISTRY_KEY_FILE` | the file holding the key this deployment signs with (hex, at least 16 bytes) | as above |
| `REGISTRY_NAMESPACE` | the namespace published records are filed under | defaults to `agentic-stack` |
| `REGISTRY_URL`, `REGISTRY_TIMEOUT_S` | the second adapter's registry route, supplied whole by the operator | the same state machine runs in process |
| `REGISTRY_FAIL`, `REGISTRY_OFFLINE`, `REGISTRY_CLOCK` | the failure paths and the fixed clock the gate uses | off |

There is no endpoint and no socket for the live adapter: today's component is files on this host, so
it opens files and imports no network library at all.

## What each test proves

| Step in `test.sh` | What it proves |
|---|---|
| 1 | 11 conformance cases pass against the signed-index adapter, over three fixture records under one name: `resolved_records=1`, `served_unverified=0`, `refusals=2`, `refusals_typed=2` |
| 1b | the caller region is 28 lines, names no adapter storage, publishes, resolves, verifies, rolls back and refuses a forged signature |
| 1c | the adapter's own failure path is a typed 503 that says nothing was appended |
| 2 | the same 11 cases pass on the content-addressed adapter with the interface, caller and suite byte-identical between runs (one sha256 over all three), the two bindings differ on 3+ execution-model axes, and both resolve the same fixture set to the same digest (`record_divergence=0`) |
| 3 | no product name appears outside `adapters/` |
| 4 | the definition-of-done breakage: the digest check is downgraded from a refusal to a warning, so the tampered record is served (`served_unverified=1`) while the unsigned one is still caught (`refusals=1`) - the run exits non-zero |
| 5 (`--live`) | the same 11 cases against `.claude/skills/`, real skill.json files signed and chained (104 skills scanned on this host), or a clear skip naming the env vars |

## What would pin, and how the boundary avoids it

| From the blueprint | The pin | How this harness avoids it |
|---|---|---|
| `pinning_risk` (registry record state): "pins to a directory layout the moment any component joins a path to reach a capability" | a caller that names `.claude/skills/<x>/skill.json` instead of a name and a constraint | `resolve()` and `publish()` take a namespace-scoped name and a version string; no operation accepts a path, and the live adapter's directory scan happens once, inside `_scan()`, never exposed to a caller |
| `must_stay_loose` (F-b3-07): any spec-conformant registry can swap in | a house index format nothing else parses | identity is the swap axis: `identity_is` is `"a path plus a version string"` on the signed-index adapter and `"a content digest"` on the second; `resolve`, `list_versions`, `describe`, `publish`, `verify` are identical on both |
| cap-capability-registry invariant: "verification is a precondition of resolution ... there is no configuration under which it is served with a warning instead" | a resolver that logs a digest mismatch and serves the record anyway | the breakage (test.sh step 4) is exactly that configuration, reintroduced on purpose, and it is what makes the gate fail - the property is only real because something can break it |

## What is claimed, not measured

| Claim | Why |
|---|---|
| the MCP Registry API's version | recorded on file as "v0.1, in preview (unverified)" (X-cap-capability-registry-001); no fetched page confirms a later state |
| public verifiability | `hmac-sha256` stands in for a signature (hashlib and hmac only, no signing library here); the verifying material is the signing key, so swapping `mac()` in `interface.py` for an asymmetric signer changes that function and the two adapters' `_signer`/`_verifying_material`, and nothing else |
| the networked form of the second adapter | until `REGISTRY_URL` points at a real route; the dry run exercises its content-addressed identity, its fetch-refusal-when-offline and its swap in process |
| the RFC 9457 problem type for an unverified record | `record-unsigned` is proposed and not yet in the closed registry `cap-errors` owns (skill.json's worked example 2); this harness returns the registered `identity-untrusted` (401) instead, per that skill's own stated fallback |
| that another party's live scan of `.claude/skills/` would find the same 104 skills every time | measured once on this host on 2026-09-03; the manifest and the tree can both change between runs |
