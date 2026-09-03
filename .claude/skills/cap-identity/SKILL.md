---
name: cap-identity
description: The ideal state of the Identity capability: every action names an actor, delegated agent actors included, and the chain that produced the right to act is explicit rather than reconstructed afterwards. Load it when deciding what an action records about who asked for it, when one agent hands work to another, when a unit of work needs a credential nobody hand-issued, when judging whether an implementation's actor model is conformant, or when a review asks why an authorisation decision reads only one hop of a chain. Also load it when a component is about to invent its own user field, when a service account is about to be shared between agents, when a long-lived secret is about to be planted inside a sandbox, or when an audit cannot say which agent actually did a thing.
---

# cap-identity

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one actor model for the whole platform, so that every action names an actor and the delegation behind it is explicit and verifiable, by adopting the two standards recorded for this capability instead of inventing a user field per component. | sourced | `F-b4-03`, `F-b3-14`, `E-concern-identity`, `E-capability-identity` "Every action names an actor, including delegated agent actors. Delegation chains are explicit" |

## Entities

| Entity |
|---|
| `E-capability-identity` |
| `E-concern-identity` |
| `E-standard-oauth-2-0-token-exchange` |
| `E-standard-workload-identity` |
| `E-adapter-identity-absent` |
| `E-not-running-identity` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-oauth-2-0-token-exchange` | RFC 8693 (a search-only research record titles it 'RFC 8693 OAuth 2.0 Token Exchange January 2020'; the specification itself was not fetched from this environment) | unverified | https://datatracker.ietf.org/doc/html/rfc8693 | `F-b3-14`, `X-cap-identity-001`, `X-cap-identity-002` |
| `E-standard-workload-identity` | unverified: the recorded column names workload identity as the governing standard without naming a document, and no specification was fetched here | unverified | - | `F-b3-14`, `X-cap-identity-005` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| attest | a unit of work and the platform facts observable about where it is running; for a unit the platform cannot observe in place, the attesting party plus the identity of the unit it vouches for | a short-lived credential naming that unit as a subject, with no long-lived secret issued, planted or stored | sourced | `X-cap-identity-005`, `X-cap-identity-007`, `X-cross-structure-035` "which ensures that identities are tied to real, verifiable conditions at runtime" |
| delegate | a subject token naming the principal the work is done for, an actor token naming the agent that will act, and the scope and audience the issued token is for | a scoped token whose act claim names the current actor and nests the prior ones, least recent most deeply nested, so the chain travels with the call | sourced | `X-cross-structure-036`, `X-entry-composition-048`, `X-cap-identity-002` "The outermost act claim represents the current actor while nested act claims represent prior actors. The least recent actor is the most deeply nested." |
| verify (proposed operation name; the recorded row names the standards, not the calls) | a presented credential or token and the trust material for its domain | the current actor and the chain behind it, or the registered identity-untrusted failure; verification resolves locally against distributed trust material rather than a call to an authority per action | proposed | `X-cap-identity-008`, `F-b3-14` |

### Shapes (JSON Schema 2020-12)

**ActorIdentity (proposed shape, from docs/decomposition.md section 2.1 and examples/end-to-end/schemas/entry.schema.json; the attest and delegate request and response schemas are in references/identity-shapes.md)** (proposed; sources: `F-b4-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:actor:0.1",
  "title": "ActorIdentity",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "subject",
    "delegation_chain"
  ],
  "properties": {
    "subject": {
      "type": "string",
      "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "The principal the work is done for. Never null, whichever way the work entered."
    },
    "delegation_chain": {
      "type": "array",
      "minItems": 1,
      "description": "Current actor first, least recent last, which is the order the runnable reference in examples/end-to-end carries and the order nested act claims unwrap in. The first element is the only element an authorisation decision may read.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "actor",
          "obtained_via"
        ],
        "properties": {
          "actor": {
            "type": "string"
          },
          "obtained_via": {
            "enum": [
              "direct",
              "token_exchange",
              "workload_attestation"
            ]
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every action names an actor, including delegated agent actors, and the delegation chain that produced it is explicit rather than inferred from logs after the fact. | sourced | `F-b4-03`, `E-concern-identity` "including delegated agent actors. Delegation chains are explicit" |
| The starting point is nothing rather than something: what runs today has no identity field anywhere in the system, so this capability is adopted rather than migrated, and the P13 check below starts red by construction. | sourced | `F-a6-05`, `E-not-running-identity`, `E-adapter-identity-absent` "No identity field anywhere in the system" |
| Two standards govern this one capability, a token-exchange standard for delegation between principals and a workload identity standard for units the platform runs itself. agentic-stack states design rule 2 (F-b1-03); this row is only its application to Identity, where the interface must satisfy both at once. | sourced | `F-b3-14`, `F-b1-03`, `E-standard-oauth-2-0-token-exchange`, `E-standard-workload-identity` "OAuth 2.0 Token Exchange · workload identity" |
| An issued token that carries a subject and no actor is impersonation, not delegation, and cannot satisfy the explicit-chain contract: delegation is impossible with only a subject_token and no actor_token. | sourced | `X-cross-structure-036` "delegation is impossible with only a subject_token and no actor_token" |
| The chain is an audit artifact, not an authorisation input. A consumer decides on the top-level claims and the party identified as the current actor; prior actors identified by any nested act claims are informational only. | sourced | `X-cross-structure-038` "Prior actors identified by any nested act claims are informational only" |
| The chain records who acted, not what each hop was allowed to spend or do: act captures only the identity of each actor in the chain, not the authorization constraints applied at each hop. Budget and policy attenuation are therefore carried by their own concerns and never read out of the chain. | sourced | `X-end-to-end-032` "Act captures only the identity of each actor in the chain, not the authorization constraints applied at each hop" |
| Proposed: a chain names the current actor first and the least recent actor last, is acyclic, and ends at a root that was attested from platform facts rather than asserted by a caller. A cycle or a chain that terminates at a self-asserted name is a verification failure, not a formatting problem. | proposed | `F-b4-03` |
| Proposed: this capability is defined without reference to the policy engine. Policy consumes identity and identity does not consume policy, so an actor model built alongside today's rules would encode those rules into the shape of the actor. | proposed | `F-b4-04` |
| Proposed: credentials are short-lived and issued per unit. A shared, long-lived secret cannot name an actor, because every holder of it produces the same subject and the chain behind that subject cannot be distinguished. | proposed | `X-end-to-end-029` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the credential itself never leaves the verification boundary. A document, a ledger record, a telemetry attribute or a failure body carries the subject and the obtained_via of each hop, never the token or certificate that proved them. | proposed | `X-cross-structure-006` |
| Proposed: which issuer or attestor minted a credential is not part of the contract, so no caller can branch on it and no core code can come to depend on one issuer's claim set. | proposed | `F-b3-14` |
| Proposed: prior actors are not offered to the authorisation decision at all. Recording them for audit is required; exposing them to a rule invites a rule that reads them, which is the failure the informational-only constraint exists to prevent. | proposed | `X-cross-structure-038` |
| Proposed: the criterion an actor's output will be judged against never appears in a credential's claims, in the delegation chain, or in anything the verification boundary hands back to the actor it authenticated. agentic-stack states design rule 6 (F-b1-07); the consequence here is that an actor learns who it is and on whose behalf it acts, never how its work will be scored. | proposed | `F-b1-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Adopt the two recorded standards whole and design no actor model of our own: a token-exchange grant for delegation and a workload identity scheme for units the platform runs. agentic-stack states design rule 2 (F-b1-03); what this adds is that Identity is the one capability whose interface has to satisfy two standards at once. | The recorded row names both, and a bespoke actor object here would be original design at a boundary where two published decisions already exist. | sourced | `F-b3-14`, `F-b1-03` "OAuth 2.0 Token Exchange · workload identity" |
| 2 | Fix the interface at the two operations above, attest and delegate, plus verify, and let every other concern consume their output rather than deriving an actor of its own. | Proposed operation set. A capability that also decided what an actor may do would be a policy engine, and the concerns that need identity (tenancy, provenance, the policy gate, memory scoping) each need the same actor, not a variant of it. | proposed | `F-b4-03`, `X-end-to-end-002` |
| 3 | Require an actor token on every delegation, and treat an exchange performed with a subject token alone as a defect rather than a shortcut. | Delegation and impersonation differ by one request parameter: send the actor token and the issued token can carry both parties; omit it and the agent simply becomes the user, which erases exactly the fact this capability exists to record. | sourced | `X-cross-structure-036` "Send actor_token and the issued token can carry both parties; omit it and the agent simply becomes the user." |
| 4 | Express the chain as nested act claims that grow at each hop, and read only the current actor when deciding whether a call is allowed. | The chain grows as each service calls the next, so the last consumer can see who is acting on behalf of whom with the original actor still named; that chain provides a complete audit trail of how the request propagated through the system, which is what makes the delegation explicit rather than reconstructed. | sourced | `X-cross-structure-037`, `X-cross-structure-038` "This chain provides a complete audit trail of how the request propagated through the system." |
| 5 | Attest a unit from facts about where it runs rather than from a secret handed to it, and for a unit the platform cannot observe in place, issue through a delegated path in which an attested party vouches for it. | Attestation ties identities to real, verifiable conditions at runtime, and a delegated workload can obtain identity documents and trust material on behalf of workloads that cannot be attested directly, which is the alternative to planting a long-lived secret inside a sandbox. | sourced | `X-cap-identity-007`, `X-cross-structure-035` "can obtain SVIDs and bundles on behalf of workloads that cannot be attested" |
| 6 | Verify a presented credential against distributed trust material at the point of use, and do not require a call to an authority for every action. | Trust material distributed to the workloads themselves enables trusted, peer-to-peer authentication without the need to contact a central authority for every transaction, which keeps verification available when the issuer is not and keeps its cost off the per-action path. | sourced | `X-cap-identity-008` "enabling trusted, peer-to-peer authentication without the need to contact a central authority for every transaction" |
| 7 | Judge an implementation by the P13 criterion below rather than by whether an actor field exists: a corpus of recorded actions, every one with a subject, every delegated one with a chain of at least two hops, and the final hop matching the identity of the unit that actually executed the action. | Proposed judging rule, applying the discipline build-definition-of-done states. A field that is present but populated by whatever the caller sent is indistinguishable, on inspection, from an identity model; only the corpus assertion tells them apart. | proposed | `F-a6-05` |
| 8 | Open references/identity-shapes.md when you need the attest and delegate request and response schemas, a worked act-claim chain, or the mapping from each recorded standard to the operations it governs. This skill body is enough to judge an implementation without it. | Proposed, progressive disclosure. The full schemas and a nested claim example are long material that a reader deciding whether an actor model is conformant does not need in front of them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| A chain that is merely forwarded is not a chain: each service in the middle of the chain must validate the incoming access token and then request a new access token, so a hop that passes the caller's token through unchanged has added no actor and recorded nothing. | sourced | `X-cap-identity-004` "each service in the middle of the chain must validate the incoming access token and then request a new access token" |
| Do not expect this capability to hand out third-party credentials. Workloads with a verifiable identity still need OAuth tokens, cloud provider credentials, API keys, and database passwords, and brokering those is a separate capability with its own contract. | sourced | `X-end-to-end-030` "they also need OAuth tokens, cloud provider credentials, API keys, and database passwords" |
| Keep identity out of indiscriminately propagated context: do not put secrets, tokens, or PII in baggage. What crosses a boundary is a non-secret reference to an actor, which is why the shape above carries names and an obtained_via rather than the credential. | sourced | `X-cross-structure-006` "Do not put secrets, tokens, or PII in baggage." |
| Model an agent calling a tool on the middle-tier pattern that already exists for services: a backend service acts on behalf of the original user when calling downstream services, preserving the user's identity while adding itself to the chain. The agent case is that pattern with an agent in the middle, not a new problem. | sourced | `X-cap-identity-003` "a backend service acts on behalf of the original user when calling downstream services" |
| Proposed: set the actor on the same explicit attribute the platform already uses to correlate work, at the moment work is dispatched. agentic-stack states the correlation finding (F-a7-02); the consequence here is that a delegated hop whose actor is attached later is attributable only if that hop happened to survive in a log. | proposed | `F-a7-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P13, made precise: `python3 tools/conformance/identity_chain.py --corpus <ledger> --min-actions 50 --report out/identity.json` (proposed tool, built with the first Identity adapter). Over a corpus of at least 50 recorded actions it asserts that every action carries a non-empty `actor.subject`, that every action whose current actor differs from its subject carries a `delegation_chain` of at least two hops, that every chain is acyclic and ordered current actor first, and that the hop naming the current actor matches the workload identity of the unit that executed the action. P13 words that last assertion as the final hop, under the opposite chain ordering; see the open question below. |
| Expected | exit 0 with `actions_checked >= 50`, `missing_subject == 0`, `short_chains == 0`, `cyclic == 0`, `executing_unit_mismatch == 0` |
| Deliberate breakage | Dispatch one agent action without performing the token exchange for the agent actor, so that action reaches the ledger with the human subject and a one-hop chain. Change nothing else. |
| Expected failure | exit 1 with `short_chains == 1` and `executing_unit_mismatch == 1`, the report naming that action's identifier, while every other action still passes. Claimed: PASS.md A6 records no identity field anywhere in the system, so neither the field, the exchange nor the tool exists here and this check starts red by construction, which is the correct starting state rather than a defect to hide. |
| Status | claimed |
| Evidence | `F-a6-05`, `F-b4-03` "No identity field anywhere in the system" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-adapter-pair`, `build-skill-authoring`, `cap-errors`

Used by: `cap-human-interaction`, `cap-identity-implement`, `cap-identity-use`, `cap-mandate-broker`, `cap-memory`, `xc-identity-delegation`, `xc-tenancy`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which spelling of the hop mechanism is normative? examples/end-to-end/schemas/entry.schema.json enumerates obtained_via as direct, token_exchange and workload_attestation, while docs/decomposition.md section 2.1 enumerates rfc8693_token_exchange, workload_attestation and direct for the same field. | An edit to one of the two, after which a single enum appears in the runnable example and in the dispatch shape. Until that edit, the two are the same three hop kinds under two spellings of one member. | 1-3-1 applied and recorded on 2026-09-03. Options: (a) adopt the runnable example's token_exchange in docs/decomposition.md; (b) adopt rfc8693_token_exchange in the example and its four entry files; (c) accept both as aliases. Recommendation and default: (a), carried into this skill's ActorIdentity shape. The enum names a class of mechanism, the governing standard is already named once in contract.standards where its version status is honest, a version-bearing enum value has to change when the standard revs, and aliases would put two spellings of one hop kind in front of every consumer. | `T-t5-02`, `F-b3-14` "define the problem, identify the three best possible solutions that align to the goal" |
| Which end of delegation_chain is the current actor? The four entry files in examples/end-to-end all put the current actor first (subject equals delegation_chain[0].actor), while docs/decomposition.md section 2.1 describes the same field as oldest hop first and row P13 asserts on the final hop. | An edit to one of the two, after which one ordering holds in the runnable reference, in the dispatch shape and in the P13 assertion. Until then a checker written against either one reports the other as a chain assembled backwards. | 1-3-1 applied and recorded on 2026-09-03. Options: (a) adopt the runnable reference's current-actor-first ordering and reword docs/decomposition.md and P13 to assert on the hop naming the current actor; (b) reorder the four entry files and the reference runner to oldest-first; (c) leave the order unspecified and add an explicit pointer member to the current actor. Recommendation and default: (a), carried into the ActorIdentity shape above. It is the ordering that actually runs, it matches how nested act claims unwrap outermost first, and (c) adds a member whose only job is to say which way a list is sorted. | `T-t5-02`, `X-entry-composition-048` "identify the three best possible solutions that align to the goal, and follow the recommendation" |
| Can a version be verified for the workload identity standard at all, given that the recorded column names a category rather than a document? | A fetch of a canonical specification for workload identity recording a version string and a date; the research on file for it is search-only, and the proxy blocked documentation fetches in this session. | Recorded as unverified in contract.standards above, with the token-exchange standard's RFC number carried as unverified for the same reason. | `F-b3-14`, `X-cap-identity-005` "a short-lived credential that serves as a workload's identity" |
| Where does the adapter pair for this capability live, given that PASS.md records today's adapter as absent? | Whether a reviewer reading only this skill can name both adapters and the axis on which their execution models differ; if not, the pair belongs here as well as in the implement facet. | The pair, the execution-model difference between them and the swap procedure are recorded once in cap-identity-implement, which builds on build-adapter-pair. This skill states only that the pair is owed and that neither member of it runs today. | `F-b1-04`, `F-a6-05` "No identity field anywhere in the system" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-identity 2831cb4f, 2026-09-03 |
