---
name: "cap-identity-implement"
description: "How to build the Identity capability on this stack from a starting point of nothing: a first adapter that issues exchanged tokens at each hop, a second whose execution model is the opposite of it, attesting units from platform facts and verifying against distributed trust material with no authority call per action, the order to migrate in, where issuance and verification are wired so no entry can skip them, and a definition of done with the breakage that makes it fail. Load it when writing the code that puts an actor on a request, when an agent hands work to another agent, when a sandboxed unit needs a name without a planted secret, when choosing where credentials are minted and verified, or when a conformance run reports actions with a one-hop chain."
---

# cap-identity-implement (folded into `cap-identity`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-identity into something that runs here: two operations, two adapters whose execution models differ, and every entry and every dispatch hop carrying an actor that was verified rather than asserted. | sourced | `F-b3-14`, `F-a6-05`, `E-capability-identity`, `E-adapter-identity-absent` "OAuth 2.0 Token Exchange · workload identity" |

## Entities

| Entity |
|---|
| `E-capability-identity` |
| `E-adapter-identity-absent` |
| `E-not-running-identity` |
| `E-swap-candidate-any-oidc-provider` |
| `E-standard-oauth-2-0-token-exchange` |
| `E-standard-workload-identity` |

## Contract

### Shapes (JSON Schema 2020-12)

**IdentityConformanceReport (proposed shape; the counters the definition of done below asserts on, per adapter)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:report:0.1",
  "title": "IdentityConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "actions_checked",
    "missing_subject",
    "short_chains",
    "cyclic",
    "executing_unit_mismatch",
    "adapters_run"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "exchange-issuing-provider",
        "attested-workload-identity"
      ]
    },
    "actions_checked": {
      "type": "integer",
      "minimum": 0
    },
    "missing_subject": {
      "type": "integer",
      "minimum": 0
    },
    "short_chains": {
      "type": "integer",
      "minimum": 0,
      "description": "Delegated actions whose chain has fewer than two hops."
    },
    "cyclic": {
      "type": "integer",
      "minimum": 0
    },
    "executing_unit_mismatch": {
      "type": "integer",
      "minimum": 0,
      "description": "Actions whose current-actor hop is not the identity of the unit that executed them. P13 words this as the final hop, under the chain ordering cap-identity records as an open question."
    },
    "unsupported": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Operations this adapter declares it does not implement. A declared subset is honest; an adapter that answers an operation it cannot provide is the failure the pair exists to expose."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    },
    "selected_by": {
      "const": "configuration",
      "description": "Recorded at runtime. A code edit between runs would not be a swap."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Both adapters implement the identical attest, delegate and verify from cap-identity, the running one is chosen by configuration with no code edit between runs, and the choice is recorded in the report. build-adapter-pair states that the second adapter exists to prove the first is not load-bearing (F-b1-04); what this facet adds is that an unobservable swap here is indistinguishable from running the same issuer twice. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| Proposed: an adapter that cannot express an on-behalf-of chain declares delegate unsupported rather than answering it with a one-hop chain. A documented conformance subset is honest; a silently truncated chain looks exactly like an action nobody delegated. Research query: is there a recorded conformance subset declaration on this stack showing an adapter refusing an on-behalf-of chain as unsupported rather than truncating it, confirming this pattern is already used elsewhere on this platform? | proposed | `X-cross-structure-034` |
| Proposed: the actor on a request is produced by verify and never constructed in application code. A caller-supplied actor object is an assertion, and an assertion that is written into the ledger becomes indistinguishable from a verified fact once the run is over. | sourced | `F-b4-03` "Every action names an actor, including delegated agent actors." |
| Proposed: the exchange happens at each hop where the acting party changes, before the downstream call, so the chain is built forward as work moves. A chain reconstructed afterwards from logs is a reconstruction, and cap-identity records that the chain has to be explicit. | sourced | `X-cap-identity-004` "each service in the middle of the chain must validate the incoming access token and then request a new access token" |
| Proposed: credentials never reach the log. What is appended is the subject, the obtained_via of each hop and a credential handle; the token or certificate stays inside the verification boundary, which is what makes the ledger safe to read widely. Research query: is there a recorded audit or provenance record schema on this stack showing a credential handle stored beside a subject with no raw token present, confirming this exclusion is enforced rather than only intended? | proposed | `X-cross-structure-006` |
| Issuance and verification sit on the platform's own entry and dispatch paths, not in each caller, and there is no flag, header or field by which a request can ask to run without an actor. TARGET T2.3, also cited by cap-identity and build-definition-of-done, states that every cross-cutting concern is managed across the entire structure, whichever entry point was used; what this facet adds is that a new entry kind inherits it by construction because it reaches execution through the same path. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| Proposed: cap-identity already fixes the identity-untrusted failure in the problem-details shape cap-errors owns, at status 401 and not retryable; this facet adds no failure object of its own. | proposed | `F-b4-07` |
| Apply build-evidence-record: the conformance run and its breakage are written to the evidence store naming the code version and the tree hash under test, and stay claimed until they have actually been run here, against a system that has an identity field at all; proposed pointer, see that skill. | proposed | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Do not re-derive the contract: cap-identity states the concern (F-b4-03), the two governing standards (F-b3-14) and the absent starting point (F-a6-05). Begin by making the actor object required on the entry envelope and on the dispatch request, which the consumption reference in examples/end-to-end already carries and the running system does not. | Proposed sequencing. There is no identity field anywhere in the system, so the first change is the field and its requiredness; every later step is enforcement of something that at least exists on the wire. | sourced | `F-a6-05`, `F-b4-03` "Every action names an actor, including delegated agent actors." |
| 2 | Build the first adapter as an exchange-issuing provider: it speaks the token-exchange grant, holds the platform's own actor credentials, and returns a token scoped to the audience of the next call with the act claim extended by one hop. | A new grant type urn:ietf:params:oauth:grant-type:token-exchange is defined in the specification, and the grant can be used to exchange tokens to a different scope, audience or subject, which is exactly the per-hop operation the chain needs. | sourced | `X-cap-identity-002` "The Token Exchange grant can be used to exchange tokens to a different scope, audience or subject." |
| 3 | Build the second adapter on workload attestation: the platform observes where a unit runs and issues it a short-lived identity document, and peers verify one another against distributed trust material instead of asking an issuer per call. | Its execution model is the opposite of the first adapter's on the axis that matters here. The first calls a central authority at every hop and hands out bearer tokens; the second attests once from platform facts and then enables trusted, peer-to-peer authentication without the need to contact a central authority for every transaction. | sourced | `X-cap-identity-008`, `X-cap-identity-007` "verify the SVID locally, enabling trusted, peer-to-peer authentication" |
| 4 | Give the second adapter a delegated issuance path for units the platform cannot observe in place, rather than pre-planting a credential inside the sandbox: an already-attested party obtains the identity document on the unit's behalf. | A delegated workload can obtain SVIDs and bundles on behalf of workloads that cannot be attested directly, which is what makes attestation usable for isolated units; the alternative is a long-lived secret in an image, which names nobody in particular. | sourced | `X-cross-structure-035`, `X-end-to-end-029` "A delegated workload can obtain SVIDs and bundles on behalf of workloads" |
| 5 | Wire it at two places only: the entry path, where the presented credential is verified and the first hop is written, and the dispatch of each unit, where the exchange for the acting agent happens before the call. Give callers no way to pass a flag that skips either. | Proposed wiring, following the placement cap-identity takes from TARGET T2.3. Two enforcement points cover every arrival and every hand-off inside a run; a third would be a component deciding its own actor, which is the property this concern does not have. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| 6 | Record the verified subject and the chain into provenance and onto the explicit correlation attribute the platform already sets at dispatch, and record the credential only as a handle. | Proposed. agentic-stack states the correlation finding (F-a7-02); the consequence here is that a delegated hop whose actor is attached later is attributable only if that hop survived in a log, and the whole point of an explicit chain is not to depend on that. | sourced | `F-a7-02`, `F-b4-05` "Correlation must ride on an explicit resource attribute set at dispatch." |
| 7 | Migrate in that order and keep both adapters live behind one call: required actor field, then verification at entry, then exchange at each hop, then attestation of the units themselves, then the second adapter selected by configuration. Do not delete the first adapter once the second exists. | Proposed migration. Each step is independently revertible and each one makes the P13 counters move, and an interface with one surviving implementation drifts back into the shape of whatever issues its tokens. Research query: is there a recorded migration ledger entry from another capability in this platform where each independently-revertible step was actually rolled back once, confirming reversibility rather than only asserting it? | proposed | `F-b1-04` |
| 8 | Apply build-adapter-pair: run one conformance run parameterised over the adapters, selected by configuration with no code edit between runs, and record `selected_by` and the adapter that actually answered in the one report shape, with each adapter's unsupported list declared; proposed pointer, see that skill's references/conformance-run-shape.md. | The parameterised suite and the configuration-only swap are build-adapter-pair's step; the report shape it did not state was added there as references/conformance-run-shape.md rather than written out again in five capability skills (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-b1-04` "Every interface ships with at least two adapters" |
| 9 | Open references/identity-adapters.md when you need the per-adapter operation mapping, what each adapter cannot do, or the step-by-step swap procedure. This skill body is enough to build either adapter without it. | Proposed, progressive disclosure. The mapping table and the swap runbook are long material that a reader building the first adapter does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Make every middle hop do the full move, not half of it: each service in the middle of the chain must validate the incoming access token and then request a new access token where the scope, audience, client, issuer and role claims are such that the next service in the chain will accept it. A hop that validates but forwards has recorded nothing. | sourced | `X-cap-identity-004` "request a new access token where the scope, audience, client, issuer and role claims are such that the next service in the chain will accept it" |
| Prefer the transport-level binding for service-to-service calls and keep bearer tokens for the hops that actually delegate: an attested certificate integrates directly with mutual TLS (mTLS), the standard mechanism for service-to-service authentication, so the identity of the caller is established before any token is parsed. | sourced | `X-cap-identity-006` "which integrates directly with mutual TLS (mTLS) — the standard mechanism for service-to-service authentication" |
| Verify at runtime which adapter actually answered and what lifetime it actually issued, rather than trusting the configuration that selected it, the same discipline build-evidence-record and agentic-stack apply to a case where configuration written in the documented place had no runtime effect (F-a7-04); a credential lifetime is only observable by holding a credential past it and watching the call fail. | sourced | `F-a7-04` "had no runtime effect" |
| Do not let this capability grow into a secret store. A unit with a verifiable identity still needs OAuth tokens, cloud provider credentials, API keys, and database passwords, and brokering those belongs to the mandate broker with its own contract and its own audit. | sourced | `X-end-to-end-030` "cloud provider credentials, API keys, and database passwords" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-identity-absent` | today | Nothing runs: the recorded adapter for Identity is *absent* and PASS.md A6 records no identity field anywhere in the system. The first adapter to exist is therefore the exchange-issuing provider described in this skill, an OIDC provider serving the RFC 8693 token-exchange grant, and it is what the second is paired against rather than an incumbent to replace. | Cannot be cited as evidence of anything running, and cannot name a unit it did not authenticate: a client gets a token only by presenting a credential it already holds, so an isolated unit has to be handed a secret before it can obtain an identity at all. It also puts a call to a central authority on every hop. | Introduce the required actor field, verify at entry against the provider, then exchange at each dispatch hop. The envelope shape does not change afterwards; only who fills the chain and when. | claimed | `F-b3-14`, `F-a6-05`, `E-adapter-identity-absent` "SPIFFE/SPIRE · any OIDC provider" |
| `E-swap-candidate-spiffe-spire` | second | SPIFFE/SPIRE workload attestation: the agent attests a workload against platform facts and issues a short-lived X.509-SVID, peers verify presented SVIDs locally against distributed trust bundles, and the Delegated Identity API issues to workloads the agent cannot attest in place. It implements attest and verify natively. | Cannot express an on-behalf-of chain: an SVID names one workload, so delegate is a declared conformance subset for this adapter unless the chain is carried in a JWT-SVID's claims, which is the open question below. It also needs an agent on every node, where the first adapter needs only a reachable endpoint. | Select the adapter by configuration only, run the identical P13 corpus assertion against each, and require the merged report to show adapters_run == 2 with selected_by == configuration and the unsupported list recorded for the attestation adapter. | claimed | `F-b3-14`, `X-cross-structure-034`, `X-cross-structure-035` "The Secure Production Identity Framework for Everyone (SPIFFE) standard enables workload-to-workload authentication using X.509 or JWT-based service identity documents (SVIDs)." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/identity/test.sh && python3 harness/identity/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at b923246: exit 0; last lines:   adapter=attested workload identity with a local trust bundle cases=16 passed=16 actions_checked=50 short_chains=0 cyclic=0 executing_unit_mismatch=0 authority_calls=0 marker=workload-attestor product_hits=0 \| conformance PASSED: 32/32 cases, 2 binding(s), selected_by=configuration |
| Deliberate breakage | In harness/identity/adapters/dryrun.py, make _break_this_hop() always forward the incoming credential unchanged on an agent actor's first hop, instead of only under IDENTITY_BREAK=forward-token (the harness README's breakage, made the default rather than env-gated so the criterion needs no extra variable) and change nothing else; restore with git checkout -- harness/identity/adapters/dryrun.py. |
| Expected failure | Measured by tools/measure.py at b923246: exit 1; last lines:   FAIL the same suite passes again once the hop is restored (expected 0, got 1) \| passed 36, failed 10 |
| Status | measured |
| Evidence | `F-a6-05`, `F-b1-04` "No identity field anywhere in the system" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-identity`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Can the attestation adapter carry a delegation chain at all, or is delegate permanently a declared subset for it? | Whether an identity document in its JWT form can carry the nested act structure and still verify against a trust bundle. The research on file records that identity documents come in X.509 or JWT form but says nothing about additional claims, and nothing was fetched here. | Proposed: delegate stays in the unsupported list for that adapter, and a deployment that needs both attestation and chains runs the exchange adapter in front of it. Recording the subset is what keeps the pair honest. | `X-cross-structure-034` "X.509 or JWT-based service identity documents" |
| Which adapter is primary once both exist? | Measure, per adapter over the P13 corpus: added latency per hop, how many separate processes must be running for one action to obtain an identity, and how a unit inside an isolated sandbox gets named at all. The last is decisive given how much of what is defined here is currently not running. | Proposed: attestation is primary for naming units and the exchange adapter is primary for delegation between principals, both behind the one interface. That is a split by operation, not a fallback, and it is the arrangement the definition of done above measures. | `F-b1-04`, `F-a6-05` "the second exists to prove the first is not load-bearing" |
| How is a delegated hop attenuated, given that the chain records only who acted? | Count, across recorded runs, how many hops would have been refused by a ceiling or a rule that the chain cannot express. cap-identity records that the chain carries identity and not the constraints applied at each hop. | Proposed: the budget ceiling and the policy decision travel in their own members of the envelope and the dispatch request, and this capability neither reads nor writes them. | `X-end-to-end-032` "not the authorization constraints applied at each hop" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-identity 2831cb4f, 2026-09-03 |
