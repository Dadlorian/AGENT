---
name: cap-mandate-broker-implement
description: How to build mandate and credential brokering on this stack: the host-side broker that already keeps the real key outside the sandbox, a second binding whose authority a non-issuer can verify offline, the migration from a dummy key plus one filtered egress path to a minted handle per destination and a signed mandate per irreversible action, where a mint and a verification are wired so the platform's guarantees ride on them, and the run that decides whether either binding may serve. Load it when writing or reviewing the broker, the exchange path or the mandate verifier, when a component is about to be handed a static secret, when planning the move off long-lived keys, when someone asks 'where does the mint actually happen', 'can we prove the token never got inside', or 'what did we run to know the expiry check works', and before recording any brokering result as passing.
---

# cap-mandate-broker-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what cap-mandate-broker specifies: two authority bindings selected by configuration, one conformance run that drives both over the same fixtures and diffs acceptances and typed refusals, and the wiring that makes a mint and a mandate verification recorded steps rather than an unobserved call to a key store. build-adapter-pair owns why there are two. | sourced | `F-b1-04`, `F-part-c-05` "chosen to prove the interface is not shaped around its current implementation" |

## Entities

| Entity |
|---|
| `E-sandbox-property-guest-credential` |
| `E-sandbox-property-guest-network` |
| `E-sandbox-property-model-egress` |
| `E-sandbox-property-field-filtering` |
| `E-standard-oauth-2-0-token-exchange` |

## Contract

### Shapes (JSON Schema 2020-12)

**broker-binding (proposed): the configuration record that selects an authority binding, and the only file that changes when the pair is swapped** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:mandate-broker:binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "binding_id",
    "role",
    "authority_kind",
    "verification",
    "operations"
  ],
  "properties": {
    "binding_id": {
      "type": "string",
      "minLength": 1
    },
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "authority_kind": {
      "enum": [
        "issuer_validated_token",
        "offline_verifiable_credential"
      ],
      "description": "Proposed: the axis the pair differs on, stated as a field so a conformance report can group by it instead of by product name."
    },
    "verification": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "verifier_is_issuer",
        "contacts_issuer"
      ],
      "properties": {
        "verifier_is_issuer": {
          "type": "boolean"
        },
        "contacts_issuer": {
          "type": "boolean"
        }
      }
    },
    "operations": {
      "type": "array",
      "minItems": 1,
      "items": {
        "enum": [
          "mint",
          "exchange",
          "attach",
          "issue_mandate",
          "verify_mandate"
        ]
      },
      "description": "Proposed: which of cap-mandate-broker's five operations this binding serves. A binding that serves a subset declares it here rather than failing at call time."
    },
    "max_lifetime_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3600
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed file boundary, under design rule 1 as agentic-stack and build-adapter-pair carry it (F-b1-02): every key store, token client, signature library and network client lives inside a binding directory, so a core module that can name a key path has made the broker load-bearing. Research query: unresearched; no prior-art search has been run for file-level boundary rules that keep credential and signing libraries out of a core module. | proposed | `F-b1-02` "The core imports interfaces, never implementations" |
| Swapping the pair is a configuration change to a broker-binding record and nothing else. build-adapter-pair states the rule (F-b1-04); the consequence here is a concrete file boundary: if a swap needs an edit anywhere but the binding record and the binding directory, the pair has not been proved and the run that says it has is wrong. | sourced | `F-b1-04`, `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| The guest keeps no real secret and reaches nothing directly. What runs today already puts a dummy key inside and defaults egress to off; the implementation may narrow that, never widen it, so 'the credential never entered the unit of work' stays checkable by inspecting the guest rather than by trusting the broker. | sourced | `F-a3-04`, `F-a3-05` "Egress is a flag, default off" |
| cap-mandate-broker states that expiry is the revocation mechanism (X-cap-mandate-broker-006). The consequence for the build is that there is no renewal endpoint to write: a task that outlives its authority fails and is re-dispatched with a fresh mint, and no code path exists that could hand back a longer-lived credential. | sourced | `X-cap-mandate-broker-006` "non-refreshable by design" |
| A binding that cannot express a bound records it as a gap in the conformance report rather than skipping the fixture. build-definition-of-done states why (F-a7-03): a skipped fixture is how a pair passes while only one half was ever exercised. | sourced | `F-a7-03` "with every behavioural stage skipped" |
| Every conformance run is an evidence record before its result is quoted anywhere. build-evidence-record owns the record's fields (F-a5-04); the consequence here is that the brokering pair stays labelled claimed until a run on a named session and date has produced both the passing and the failing output. | sourced | `F-a5-04`, `F-part-c-08` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed pointer, see cap-mandate-broker's not_exposed row on the credential bytes, the signing keys and the issuer's key store: the build consequence is that both live only inside the binding directory, and a test fixture holds a throwaway key generated at run time, never a copy of a real one. | proposed | - |
| Proposed pointer, see cap-mandate-broker's not_exposed row on the token service endpoint and the transport to it: the build consequence is that the conformance report names only the binding_id and the authority_kind, never the endpoint or retry policy. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put both bindings behind the broker-binding record and keep key paths, token clients, signature verification and network calls inside their binding directories. Select the binding by configuration at start-up; never by an import in core or seam code. | build-adapter-pair states rule 3 (F-b1-04) and cap-mandate-broker fixes five operations and nothing about where a key lives; a core module that can name a key path has already decided which binding wins, and the swap the pair is supposed to prove becomes an edit rather than a setting. | sourced | `F-b1-02`, `F-b1-04` "Every interface ships with at least two adapters" |
| 2 | Build today's binding on what already runs: the host-side broker outside the sandbox that holds the real key, picks the endpoint and drops model and destination overrides by name. Extend it from one egress path to a mint per destination, and have it return a handle rather than a token. | cap-mandate-broker's today row is this broker (F-a3-07); the work is not a new component but two changes to an existing one - one destination per authority instead of one endpoint for all, and a handle at the boundary instead of a credential. | sourced | `F-a3-07`, `F-a3-08` "Model and destination overrides dropped by name at the broker" |
| 3 | Build the second binding as a mandate a verifier that did not issue it can check offline: sign the whole record, publish the key, and run the verifier in a process that holds no issuer key and makes no call to the issuer. Assert both of those in the run, not in a comment. | cap-mandate-broker chooses the pair on where verification happens (X-cap-mandate-broker-005). A verifier that quietly reaches the issuer passes the same fixtures while proving nothing, so the two verifier constants are the only evidence that the second execution model is real. | sourced | `X-cap-mandate-broker-005`, `X-end-to-end-070` "cryptographically signed records of what the user approved" |
| 4 | Proposed migration, in this order: inventory every destination a unit of work reaches today; mint and attach in shadow beside the current path and diff the requests that leave the host; flip one destination at a time to refuse an unminted request; then add mandates for the spend, deploy and send classes; then remove every remaining static credential and fail the build if one reappears. | Proposed: the inventory is what stops a flip from breaking a destination nobody remembered, the shadow diff is what shows the attach point is byte-equivalent before anything depends on it, and doing mandates after destinations means each step has one observable failure mode instead of two. Research query: has this repository's host-side broker (F-a3-07/F-a3-08) recorded a destination inventory or a shadow-diff run for any prior migration, that would fix this order rather than leave it a proposal. | proposed | - |
| 5 | Wire the cross-cutting concerns onto the mint and verification paths: set the correlation attribute explicitly at dispatch and carry it on every mint, ask policy before minting rather than after, and append an evidence record for every mint, exchange and mandate verification. | agentic-stack and build-adapter-pair carry the correlation finding (F-a7-02): correlation must ride on an explicit resource attribute set at dispatch, so a mint made inside a unit of work is unattributable unless the attribute was set where the work was dispatched. | sourced | `F-a7-02`, `F-b1-08` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Have each binding report at start-up the authority kind it serves, the operations it implements, the maximum lifetime it will mint and the trust anchor it verifies against, and compare that report against its binding record. Fail start-up on a mismatch. | build-evidence-record carries the silent-override finding (F-a7-04): configuration written in the documented place had no runtime effect, so a binding record that says it mints five-minute credentials proves nothing until the running process has said so, which is why the report is compared rather than the file read. | sourced | `F-a7-04` "had no runtime effect" |
| 7 | Write one conformance run parameterised over the binding records: drive the same fixtures through every configured binding, assert the per-binding counters, and diff acceptances, refusals and refusal types across bindings. Include a scan of the guest filesystem and environment after the run. | cap-mandate-broker states the replay property (X-cap-mandate-broker-004); the consequence for the run is that neither it nor 'the credential never got inside the sandbox' is visible from a mint that returned successfully, so the run needs a second destination and a post-run scan. | sourced | `X-cap-mandate-broker-004`, `F-a3-05` "stops a stolen or misdirected token from being replayed against a different service" |
| 8 | Record each conformance run as an evidence record naming the command, the fixture set, the code version and tree hash, and whether the tree was dirty, and leave the pair labelled claimed until a run has produced both the passing and the failing output on a named session and date. | build-evidence-record owns the claimed-versus-measured distinction (F-part-c-08); the consequence here is that a brokering result is the one result nobody should take on trust, because the thing it asserts is that a secret did not leak. | sourced | `F-part-c-08`, `F-a5-04` "Distinguish **claimed** from **measured** throughout" |
| 9 | Proposed: open cap-mandate-broker's references/mandate-broker-shapes.md when implementing the mint request, the mandate record, the verification outcome or the refusal types. The body of this skill is enough to build and wire the pair without opening that file. | Proposed: the full shapes and the refusal registry belong to the contract rather than to the build, and duplicating them here would give the next author two places to change one field. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: generate every key a test uses at run time and throw it away with the fixture. A committed test key is a long-lived credential in the repository, which is the exact thing this capability exists to remove. Research query: does this repository's own test-fixture policy (a CI secret-scan record, or a decision under kb/decisions.jsonl) already say a committed key fails the build, which would source this rather than leave it a proposed practice. | proposed | - |
| Count what the run exercised, not what it exited with: build-definition-of-done carries the structurally-green finding (F-a7-03), where a run passed because the generated work contained nothing those tools apply to. Assert bindings_run, destinations_probed, mandates_verified and sandbox_credential_sightings as numbers and fail on a zero, because a brokering run pointed at one destination with no expired fixture exercises neither audience nor expiry and still exits green. | sourced | `F-a7-03` "because the generated work contained nothing those tools apply to" |
| Proposed: keep the shadow phase long enough to see the destinations that are reached rarely. The inventory finds the paths that are exercised; the diff over time finds the ones that are not, and those are where a static credential survives a migration. Research query: what is the longest observed interval between calls to a rarely-reached destination in this platform's own dispatch record, which would fix a minimum shadow-phase duration instead of leaving it a judgment call. | proposed | - |
| Proposed: make an unminted outbound request fail closed at the attach point rather than being passed through unauthenticated. A request that leaves without an authority is the failure mode that looks like success until the destination happens to be permissive. Research query: does X-cap-mandate-broker-007's proxy-attaches-at-network-layer pattern, or a fetched (not search-only) read of it, state a fail-closed default at the attach point specifically, which would source this rather than leave it a proposed practice. | proposed | - |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-vsock-credential-broker` | today | Proposed adapter and proposed entity id, for the reason cap-mandate-broker records: PASS.md B3 has no mandate or credential-brokering row, so no adapter entity exists for this capability. Built on the host-side broker in PASS.md A3, reached over vsock from a guest with no network and a dummy key, extended to mint one handle per destination and to serve exchange and attach; the real key, the endpoint choice and the by-name override filter stay on the host side of the boundary. | Proposed: cannot issue an authority a third party can check, cannot express a ceiling or a validity period inside the credential, and cannot survive the host that holds the key - so it serves mint, exchange and attach, and leaves issue_mandate and verify_mandate to the second binding. | Point the runner at config/broker/mandate.json instead of config/broker/today.json and change nothing else. The same fixtures must produce the same acceptances and the same typed refusals for the operations both bindings serve, and a gap for the ones only one serves. | claimed | `F-a3-07`, `F-a3-05`, `F-a3-04` "vsock → host broker, which holds the real key and picks the endpoint" |
| `E-swap-candidate-verifiable-credential-mandate` | second | Proposed adapter and proposed entity id, same reason. A mandate signed as a verifiable credential, carrying the ceiling, the destinations and the validity period, verified by a process holding no issuer key and making no issuer call; it serves issue_mandate and verify_mandate over the identical fixtures. | Proposed: cannot attach itself to an outbound request, cannot be withdrawn before its validity period ends without a separate status channel, and cannot keep its bounds from the party it is shown to. | The execution models differ on where verification happens: one authority is validated by the issuer that minted it, the other is checked offline by a holder. The conformance run groups its report by the binding record's authority_kind, so the report shows the axis rather than a pair of names. | claimed | `X-cap-mandate-broker-005`, `X-end-to-end-071`, `F-b1-04` "delegated tasks where the human signs an Intent Mandate upfront and the agent acts autonomously later" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/identity/test.sh |
| Expected | Two checks, both from the repository root. (1) Cross-binding conformance, proposed tool: `python3 tools/conformance_mandate_broker.py --binding config/broker/today.json --binding config/broker/mandate.json --fixtures tests/fixtures/mandate-broker --report out/mandate-broker-conformance.json`, over a fixture set of one credential minted for destination A and presented at A and at B, and three mandates - one within bounds and validity, one past expiry, one naming a destination outside its bounds - verified by a process with no issuer key. Assert adapters_run >= 2, credentials_minted > 0, accepted_at_intended == credentials_minted, accepted_at_other == 0, mandates_verified == 3, mandates_accepted == 1, refusals == 3, refusals_typed == refusals with every refusal carrying a `urn:agentic:problem:` type, verifier_is_issuer == false, contacts_issuer == false, and sandbox_credential_sightings == 0 from a scan of the guest filesystem and environment after the run. (2) Containment: `grep -rIlE '(BEGIN [A-Z ]*PRIVATE KEY\|api[_-]?key\|client_secret\|/etc/broker/keys)' src/core/ src/seam/` returns no files, so key material and key paths appear only inside the binding directories. Gap: no harness covers this capability yet (STATUS row 60). harness/identity/README.md and provenance.json list cap-mandate-broker (not cap-mandate-broker-implement) as a co-skill; its delegation and single-audience-format checks (scope narrowing, lifetime shortening, acyclicity) do not run this criterion's destination-bound credential-acceptance and mandate-verification counters (credentials_minted, accepted_at_intended, accepted_at_other, mandates_verified, mandates_accepted, refusals). (1) exit 0 with one line per binding reading `binding=<role> authority_kind=<kind> credentials_minted=1 accepted_at_intended=1 accepted_at_other=0 mandates_verified=3 mandates_accepted=1 refusals=3 refusals_typed=3 sandbox_credential_sightings=0` followed by `adapters_run=2 refusal_divergence=0`. (2) grep exits 1 printing nothing. Until that proposed tool exists, `bash harness/identity/test.sh` (owned by cap-identity-implement) is the running gate: every check line reads ok and the script exits 0. Gap: no harness covers this capability yet (STATUS row 60); the nearest gate is harness/identity/test.sh, owned by cap-identity-implement. Its delegation and single-audience-format checks (scope narrowing, lifetime shortening, acyclicity) do not exercise this skill's destination-bound credential-acceptance and mandate-verification counters (credentials_minted, accepted_at_intended, accepted_at_other, mandates_verified, mandates_accepted, refusals). |
| Deliberate breakage | In one change, drop the audience comparison at destination B so it accepts any well-formed credential, and hard-code the broker's key path inside a core module. |
| Expected failure | Check (1) exits non-zero with `accepted_at_other=1 refusals=2` on both bindings, naming destination B as having accepted a credential minted for A while the expiry and out-of-bounds refusals still stand - which is what shows the run tells audience apart from expiry rather than passing or failing as a block. Check (2) exits 0 and prints the core module that now names the key path. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-mandate-broker`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Where does the attach point sit once a unit of work reaches more than one kind of destination: one broker per destination class, or one broker that routes? | Count, over a shadow migration, how many distinct destination classes a single unit reaches and how many of the by-name override filters differ between them; one filter set for all of them argues for one broker, several argue for one per class. | Proposed: one broker that routes, because what runs today already picks the endpoint at the broker, and splitting it duplicates the by-name override filter cap-mandate-broker cites (F-a3-08), which is the part most likely to drift. | `F-a3-07`, `F-a3-08` "Model and destination overrides dropped by name at the broker" |
| How is a mandate withdrawn before its validity period ends, given the second binding is verified offline? | Measure how often an approving actor wants to withdraw inside the validity window; if it is rare, short validity periods are cheaper than a status channel every verifier must reach, which would undo offline verification. | Proposed: keep validity periods short enough that expiry is the withdrawal mechanism, and record the requirement here rather than adding a revocation lookup that would make an offline verifier reach the issuer after all. | `X-cap-mandate-broker-005` "decentralised" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-mandate-broker 2831cb4f, 2026-09-03 |
