---
name: cap-mandate-broker-use
description: How to reach something outside the sandbox, or do something you cannot take back, without ever holding a secret: name one destination and get a handle, or name one action class and act under a signed mandate somebody approved. Load it when a unit of work has to call an API, a database or a partner service, when a person needs to approve spending, deploying or sending up front so an agent can act later on its own, when an alert or a schedule triggers work that will touch the outside world, when someone asks 'what do I pass to make this call', 'who do I ask for permission', 'why was this refused', or 'do I need the key', and before anyone puts a token in an environment variable, a config file or a prompt.
---

# cap-mandate-broker-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make brokered authority usable in two moves: name a destination and act with the handle you get back, or name an action class and act under a mandate someone approved. A caller never sees a credential, never picks an issuer, and never writes an expiry. | sourced | `T-t3-01` "It has to be simple to use." |

## Entities

| Entity |
|---|
| `E-sandbox-property-guest-credential` |
| `E-sandbox-property-model-egress` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| approve (proposed): what a human does | an action class - spend, deploy or send - a ceiling, the destinations it may be used against, and how long the approval lasts | a signed mandate somebody else can check later; nothing runs yet and nothing is minted (proposed) | proposed | - |
| reach (proposed): what an agent does | one destination identifier, and the mandate reference if the action is irreversible | a handle to use for that one call, and the call itself; the credential is added outside the sandbox and the agent never sees it (proposed) | proposed | - |
| act (proposed): what an event triggers | the entry envelope's actor and delegation chain, unchanged, plus the destination the triggered work needs | the same handle an agent or a human would get; an event that names no approving actor gets no mandate and so cannot take an irreversible action (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a human approves bounds up front and an agent acts under them later** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:mandate-broker:example:approve-then-act",
  "title": "Approval and action are separated in time, and the bounds travel with the mandate",
  "description": "A person approves a ceiling and a set of destinations on Tuesday. On Thursday an agent acts under that mandate: it names one destination, receives a handle, and the credential is attached outside the sandbox. The verifier that accepts the action holds no issuer key and makes no call to the issuer.",
  "examples": [
    {
      "approve": {
        "actor": "user:corey",
        "mandate": {
          "mandate_id": "mandate-invoice-run-0007",
          "approved_by": "user:corey",
          "action_class": "spend",
          "bounds": {
            "ceiling_micros": 250000000,
            "currency": "USD",
            "destinations": [
              "payments.partner-co"
            ]
          },
          "not_before": "2026-09-01T00:00:00Z",
          "not_after": "2026-09-08T00:00:00Z"
        }
      },
      "act": {
        "actor": "agent:invoice-settler",
        "mint": {
          "audience": "payments.partner-co",
          "scope": [
            "payments:create"
          ],
          "mandate_ref": "mandate-invoice-run-0007",
          "lifetime_seconds": 300
        },
        "handle": {
          "handle_id": "hdl-7c1f9a2e4b60",
          "audience": "payments.partner-co",
          "expires_at": "2026-09-03T09:12:41Z",
          "refreshable": false
        }
      },
      "verification": {
        "mandate_id": "mandate-invoice-run-0007",
        "action": {
          "action_class": "spend",
          "destination": "payments.partner-co",
          "amount_micros": 41500000,
          "currency": "USD"
        },
        "accepted": true,
        "checks": {
          "signature_verified": true,
          "within_validity": true,
          "within_bounds": true
        },
        "verifier": {
          "is_issuer": false,
          "contacted_issuer": false
        }
      }
    }
  ]
}
```

**Worked example 2 (proposed): an event triggers work, and a handle presented at the wrong destination is refused** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:mandate-broker:example:audience-refused",
  "title": "A credential minted for one destination is worth nothing at another",
  "description": "An alert enters as an event and the work it triggers reaches a metrics service. A later step tries to reuse the same authority against a deploy endpoint. The second destination refuses it on its own audience check, and the refusal is a problem details object with a type the caller branches on. No retry is attempted, because the answer will not change.",
  "examples": [
    {
      "entry": {
        "kind": "event",
        "actor": "service:alerting",
        "correlation_id": "corr-event-0001"
      },
      "first_call": {
        "audience": "metrics.internal",
        "handle_id": "hdl-2b8d0f61ac33",
        "accepted": true
      },
      "second_call": {
        "audience_presented_at": "deploy.internal",
        "handle_id": "hdl-2b8d0f61ac33",
        "accepted": false,
        "problem": {
          "type": "urn:agentic:problem:credential-audience-mismatch",
          "title": "This authority was not issued for this destination",
          "status": 401,
          "detail": "hdl-2b8d0f61ac33 was minted for metrics.internal and was presented at deploy.internal",
          "retryable": false,
          "correlation_id": "corr-event-0001"
        }
      },
      "what_the_caller_does": "mint a new handle for deploy.internal, which requires a mandate because a deploy is irreversible"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Three ways in, one request. TARGET T1's three ways in are a human, an agent and an event - a different enumeration from T6.2's four entries - and all three name a destination, or a destination plus a mandate reference, and get the same handle back. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "A human must be able to enter the system." |
| A caller never holds a credential. cap-mandate-broker states why (F-a3-05); for a caller the consequence is simply that there is nothing to store, nothing to rotate and nothing to leak: a handle is worthless to anyone who reads it, including you. | sourced | `F-a3-05` "No real secret inside the VM" |
| The complexity is hidden on purpose: a caller never chooses an issuer, a key, a signing algorithm, a lifetime or a trust anchor. All of those exist, and cap-mandate-broker-implement is where they are decided; none of them appears in what a caller writes. | sourced | `T-t2-01` "Composability hides the complexity." |
| Enhancing one aspect leaves the rest untouched: shortening lifetimes, adding a destination, moving to an offline-verifiable mandate, or re-signing with a new key changes nothing in a caller that named a destination and an action class, because those are the only two things it was ever asked to write down. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Failure arrives as a problem details object, the shape cap-mandate-broker adopts for this interface (F-b3-13), never as a stack trace from a key store or a bare 401 from a destination. A caller branches on the type member and reads retryable; it never matches on wording. | sourced | `F-b3-13` "RFC 9457 problem details" |
| Nothing you get back tells you how you will be scored. cap-mandate-broker states design rule 6 on this interface (F-b1-07): a mandate carries a ceiling, destinations and a validity period, and never the criterion the work done under it will be judged against. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | To reach something outside the sandbox: name the one destination you are calling and use the handle you get back. Do not look for a key, an environment variable, a config file or a secret in your prompt - there is not one, and there is not meant to be. | The credential is added outside the sandbox after you have made an ordinary call, so a caller that goes looking for one is trying to rebuild a thing the platform removed on purpose. | sourced | `T-t2-01` "Composability hides the complexity." |
| 2 | Mint one handle per destination. If the next call goes somewhere else, ask for another handle; never carry one across. | cap-mandate-broker binds a handle to a single audience (X-cap-mandate-broker-003), so reusing one is not a shortcut - it is a call that will be refused by the destination itself, and worked example 2 is exactly that case. | sourced | `X-cap-mandate-broker-003` "the resource server should reject any token whose audience does not match its own identifier" |
| 3 | For anything you cannot take back - money moving, a deploy landing, a message leaving - get a mandate first: an approving person states the ceiling, the destinations and how long the approval lasts, and you name it when you act. | A human must be able to enter the system, and approving bounds once is how a person stays in the loop for work that will happen when they are not watching; worked example 1 is the shape of it. | sourced | `T-t1-01`, `X-end-to-end-071` "the human signs an Intent Mandate upfront and the agent acts autonomously later" |
| 4 | When work is triggered by an event or a schedule, pass the entry envelope's actor and delegation chain through unchanged. Do not substitute a service account of your own to make a refusal go away. | An internal or external event must be able to enter the system on the same terms as a person or an agent; replacing the actor turns a refusal into an unattributable action, which is the one thing a mandate exists to prevent. | sourced | `T-t1-03` "An internal or external event must be able to enter the system." |
| 5 | On a refusal, branch on the problem's type member and stop. Show detail to a person; do not parse it, key metrics on it, or retry a refusal marked retryable false. | cap-mandate-broker adopts the platform's failure shape rather than inventing one (F-b3-13): title and detail are written for readers and may be reworded, while the type is the part you were promised. An expired mandate is still expired on the second attempt, and a handle minted for another destination will not start matching. | sourced | `F-b3-13` "RFC 9457 problem details" |
| 6 | Let the handle expire with your task. Do not cache it, pass it to a sub-agent for later, or ask for a longer lifetime; if a task outlives its authority, let it fail and be re-dispatched. | cap-mandate-broker makes expiry the revocation mechanism (X-cap-mandate-broker-006), so a cached handle is not an optimisation - it is the one way a caller can recreate the long-lived secret the platform just removed. | sourced | `X-cap-mandate-broker-006` "non-refreshable by design" |
| 7 | Read the two worked examples above, then stop. Open cap-mandate-broker only if you have to judge whether an authority is correctly scoped, and cap-mandate-broker-implement only if you are building a broker rather than calling one. | A destination, sometimes a mandate reference, and one outcome to read is the whole consuming surface; making someone learn token exchange and credential formats before they can make a call is the kind of weight that stops a platform from being used at all. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: log the handle id, the destination and the expiry, and nothing else. That is enough to explain any refusal afterwards, and a handle id is designed to be useless to whoever reads the log. | proposed | - |
| Proposed: ask for the narrowest scope that does the job, not the scope you might need later. A second handle costs one call; an over-scoped one is the blast radius of every mistake made under it. | proposed | - |
| Proposed: when you need a mandate, ask for the bounds you can justify in a sentence - this much, to these destinations, until this date. A person approving something they cannot restate is not really approving it. | proposed | - |
| Proposed: put the correlation id you were given on every mint. It is what ties an action taken hours later back to the entry that caused it, and nobody can add it afterwards. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | The smallest round trip, from the repository root, with the proposed broker tool: approve bounds with `python3 tools/broker.py approve --actor user:corey --action-class spend --ceiling-micros 250000000 --currency USD --destination payments.partner-co --not-after 2026-09-08T00:00:00Z`, then act with `python3 tools/broker.py act --actor agent:invoice-settler --destination payments.partner-co --mandate mandate-invoice-run-0007 --amount-micros 41500000 --report out/broker-use.json`. It asserts accepted == true, that the handle's audience is payments.partner-co and its refreshable member is false, that the verification was performed with is_issuer false and contacted_issuer false, and that no credential material appears anywhere in the report. |
| Expected | exit 0 and one line reading `actor=agent:invoice-settler audience=payments.partner-co accepted=true refreshable=false is_issuer=false contacted_issuer=false credential_in_report=0`. |
| Deliberate breakage | Present the same handle at a second destination: `python3 tools/broker.py act --actor agent:invoice-settler --destination deploy.internal --handle hdl-7c1f9a2e4b60`. |
| Expected failure | exit non-zero with `accepted=false`, and the report carries a problem details body whose type is `urn:agentic:problem:credential-audience-mismatch`, whose retryable member is false, and whose detail names both the destination the handle was minted for and the one it was presented at. The handle is refused rather than accepted with a warning, which is the property a caller is relying on when it does not check anything itself. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `cap-mandate-broker`, `cap-mandate-broker-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What should a caller do when it needs an irreversible action and no mandate exists yet - refuse, or park the work and ask a person? | Count how often work reaches an irreversible step with no mandate, and how many of those a person approves within the run's budget; if most are approved, parking is cheaper than a failed run, and if most are not, refusing early saves the spend. | Proposed: refuse with a typed problem naming the action class and the bounds that would be needed, and leave asking a person to whichever composition wanted the action. A brokering call that blocks waiting for a human has turned a two-move surface into a workflow. | `T-t3-02` "It cannot be daunting or overly complex" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-mandate-broker 2831cb4f, 2026-09-03 |
