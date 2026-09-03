---
name: cap-identity-use
description: How to use the Identity capability as a caller: name yourself once on what you send, and every hop after that is added for you. Load it when writing a client, an agent, a webhook receiver or a scheduled job against this platform, when you are about to add a user_id or an on_behalf_of field of your own, when one agent hands work to another and you wonder who the audit will name, when a workload asks where to get its credentials, or when a call came back 401 identity-untrusted and retrying did not help.
---

# cap-identity-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Reduce identity to one thing a caller does: say who the work is for. cap-identity states the contract (F-b4-03) and cap-identity-implement wires it; what is left for you is one object on the envelope, and the chain behind it is the platform's work. | sourced | `F-b4-03`, `T-t3-01` "Every action names an actor" |

## Entities

| Entity |
|---|
| `E-capability-identity` |
| `E-concern-identity` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| enter (proposed) | your envelope with one object on it: actor.subject, the principal the work is for, and a one-hop delegation_chain naming how you were established | the work runs, and every record it produces carries that subject and the chain as it grew | proposed | `F-b4-03` |
| hand work to an agent (proposed) | nothing extra: you call a workflow, a loop or another agent the ordinary way | a chain one hop longer, with the acting agent as the current actor and you still named behind it; you neither build the hop nor pass a token | proposed | `F-b4-03` |
| be a workload (proposed) | nothing you hold: you are attested from facts about where you are running | a short-lived identity you did not have to be given, and no secret to rotate; asking for a long-lived credential is the thing you do not do | proposed | `X-end-to-end-029` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a person asks for something** (proposed; sources: `F-b4-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:example:human",
  "title": "One hop, named once",
  "description": "The actor object from examples/end-to-end/entries/human.json. You write these four lines; nothing else about identity is yours. Run on 2026-09-03: all 14 ledger records for that run carry actor user:corey and delegation_depth 1.",
  "examples": [
    {
      "subject": "user:corey",
      "delegation_chain": [
        {
          "actor": "user:corey",
          "obtained_via": "direct"
        }
      ]
    }
  ]
}
```

**Worked example 2 (proposed): an outside agent submits work on someone's behalf** (proposed; sources: `F-b4-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:example:external",
  "title": "Three hops, still named once",
  "description": "The actor object from examples/end-to-end/entries/external.json. The partner agent named itself and the person it acts for; the intake hop was added on the way in. Read it current actor first: the partner agent is acting now and the person it acts for is last. Run on 2026-09-03: all 14 ledger records for that run carry delegation_depth 3.",
  "examples": [
    {
      "subject": "agent:partner-sre-bot",
      "delegation_chain": [
        {
          "actor": "agent:partner-sre-bot",
          "obtained_via": "workload_attestation"
        },
        {
          "actor": "service:intake",
          "obtained_via": "token_exchange"
        },
        {
          "actor": "user:corey",
          "obtained_via": "direct"
        }
      ]
    }
  ]
}
```

**The one failure (proposed): identity-untrusted, in the problem-details shape cap-errors fixes** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:example:untrusted",
  "title": "The chain did not verify",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Returned with media type application/problem+json when a presented credential or a hop of the chain does not verify. Not retryable: re-sending the same thing produces the same answer. The fix is a fresh credential or a fresh attestation, not a retry.",
  "examples": [
    {
      "type": "urn:agentic:problem:identity-untrusted",
      "title": "The delegation chain does not verify",
      "status": 401,
      "detail": "hop 2 of 3 (service:intake) presented a credential that expired at 2026-09-03T09:18:00Z",
      "retryable": false
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| All three of TARGET T1's ways in name an actor the same way. A human must be able to enter the system, an agent must be able to enter the system, and an internal or external event must be able to enter the system; each carries the same actor object on the same envelope, and nothing downstream branches on which of the three it was. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "2. An agent must be able to enter the system." |
| Proposed: one object is the whole obligation. There is no token to fetch, no header to sign, no chain to build and no way to ask to run without an actor; cap-identity fixes the contract and cap-identity-implement puts issuance and verification on the platform's own paths. | proposed | `F-b4-03`, `T-t3-01` |
| Enhancing one aspect leaves the rest untouched: changing how credentials are issued, shortening their lifetime, or adding a hop between you and the work changes nothing in a caller that named itself once, because the name is the only thing it was ever asked for. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The obligation is kept to one object because a contract that is daunting or overly complex will not be used, and a caller that finds identity expensive will invent a user field of its own that nobody can verify. | sourced | `T-t3-02`, `T-t3-01` "It cannot be daunting or overly complex, or no one will use it." |
| You cannot gain anything by writing names into the chain: the consumer of a token MUST only consider the token's top-level claims and the party identified as the current actor by the act claim. The rest of the chain is read by audits, not by the thing deciding whether your call is allowed. | sourced | `X-cross-structure-038` "the consumer of a token MUST only consider the token's top-level claims and the party identified as the current actor by the act claim." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: you never see the credential, the trust material or which adapter answered. What comes back to you and what lands in the audit are names and how each name was established, which is why a change of issuer is invisible to you. | proposed | - |
| Proposed: naming a principal is not the same as being allowed to act for them. What you may do is decided by the policy gate and the budget ceiling on the same envelope, and putting a more powerful name in the chain does not move that line. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put one actor object on the envelope: a subject of the form scheme:identifier, where the scheme is user, service, agent or schedule, and a one-hop delegation_chain saying how you were established (direct, token_exchange or workload_attestation). | Proposed. It is the shape the runnable reference already validates in examples/end-to-end/schemas/entry.schema.json, and cap-identity carries it as ActorIdentity; writing it by hand once is the entire caller-side obligation. | proposed | `F-b4-03` |
| 2 | Do not build the chain yourself, and do not add hops for work you hand off. When your request reaches an agent, a workflow or a loop, the platform adds the hop and names the agent as the current actor. | Proposed usage of what cap-identity-implement wires at dispatch. A chain assembled by callers is a chain each caller can get wrong, and the audit cannot tell a mistaken hop from a fabricated one. | proposed | `F-b4-03` |
| 3 | If you are a workload rather than a person, do not ask for a credential and do not bake one into your image. Be attested from where you run, and let the identity you get expire. | Short-lived, cryptographically verifiable identity documents remove the need for vulnerable static secrets by issuing and rotating identities continuously, so a planted secret buys you nothing and costs you a rotation you will forget. | sourced | `X-end-to-end-029` "eliminating the need for vulnerable static secrets by issuing and rotating identities continuously" |
| 4 | Read the chain when you want to know who did something, and read only its first element when you want to know who is acting now. Do not use anything behind that element to decide whether something is allowed. | Proposed reading rule, following the constraint cap-identity records from the standard: the prior actors are there for the audit, and a client that starts branching on them has built an authorisation rule out of an audit trail. | proposed | `X-cross-structure-038` |
| 5 | Handle exactly one failure: identity-untrusted at status 401, not retryable. Get a fresh credential or a fresh attestation and send again; do not loop on the same envelope. | Proposed. The failure shape and its registry belong to cap-errors, so a client that already reads type and retryable needs no new branch beyond recognising one more registered type. | proposed | `F-b4-07` |
| 6 | Do not add an identity field of your own. If you need to say who something is for, that is the subject; if you need to say who asked you to do it, that is the hop the platform adds. | Proposed. A parallel user field is not verified by anything, so it splits the audit into a trustworthy half and a decorative half, and PASS.md A6 records that a system with no identity field at all is where this started. | proposed | `F-a6-05` |
| 7 | To see all of this run, use examples/end-to-end: the four entry files carry the two worked examples above, and the assertion in the definition of done below reads the actor off every record the run appended. | Proposed, and it is the shortest route from this page to something running: the reference runner needs no services and prints the actor of each entry it processes. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: name yourself once, at the moment you decide to do the thing, and carry that name with the intent. A subject minted at send time is a new principal on every retry, and the audit then shows several people asking for one thing. | proposed | `F-b4-03` |
| cap-identity states the baggage hazard for this record; the caller-side consequence is the one that bites you: do not put the credential anywhere it will be copied along with the request. Do not put secrets, tokens, or PII in baggage. Names travel; proofs do not. | sourced | `X-cross-structure-006` "Do not put secrets, tokens, or PII in baggage." |
| Expect to ask for credentials to other systems somewhere else, which cap-identity-implement records as the boundary this capability must not grow past. Having a verifiable identity does not hand you cloud provider credentials, API keys, and database passwords; those come from the mandate broker, which is a different call with a different audit. | sourced | `X-end-to-end-030` "cloud provider credentials, API keys, and database passwords" |
| Proposed: log the subject and the depth of the chain next to your own record of the intent. When two systems disagree about who did something, those two values are what make the platform's records and yours line up. | proposed | `F-a7-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `cd examples/end-to-end && bash test.sh` to produce the corpus, then the identity assertion over what it appended: `python3 -c "import json;r=[json.loads(l) for l in open('out/ledger.jsonl')];m=[x for x in r if not x.get('actor')];d=[x for x in r if x.get('entry_kind')=='external' and x.get('delegation_depth')!=3];print(f'records={len(r)} missing_actor={len(m)} external_wrong_depth={len(d)}');raise SystemExit(1 if m or d or len(r)<50 else 0)"`. It asserts that every record of every run names an actor and that the three-hop entry of worked example 2 kept its three hops all the way to the ledger. |
| Expected | test.sh exits 0 and prints `passed 29, failed 0`; the assertion prints `records=56 missing_actor=0 external_wrong_depth=0` and exits 0. |
| Deliberate breakage | In `examples/end-to-end/run.py`, in the `record` method, replace the value of the `delegation_depth=` argument, `len(self.env["actor"]["delegation_chain"])`, with `1`. That is what dispatching without performing the exchange for the acting agent looks like from the ledger's side. Change nothing else. |
| Expected failure | test.sh still exits 0 and still prints `passed 29, failed 0` - the existing suite asserts nothing about identity, which is the useful half of this breakage - while the assertion prints `records=56 missing_actor=0 external_wrong_depth=14` and exits 1. Measured in session cap-identity 2831cb4f on 2026-09-03: both runs were performed, the broken run against a copy of examples/end-to-end in this session's scratchpad, and the repository tree was left unmodified (run.py sha256 e54d31b921b707bc672c3ec6f680a7c0a77fdc9b70202ff56699e4f01d55f7e9 before and after). |
| Status | measured |
| Evidence | `F-b4-03`, `F-a6-05` "Every action names an actor, including delegated agent actors" |

## Composes with

Builds on: `cap-identity`, `cap-identity-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What does a caller do when the person it acts for is not the person who started the run, for example a scheduled entry firing work a human configured weeks ago? | Whether the schedule entry in examples/end-to-end names the schedule or the person as subject, and which one an audit of a disputed action would need. Today that file names the schedule as subject with the person as an earlier hop. | Proposed: name the schedule as the subject and keep the person as the hop that established it, so the current actor is the thing that actually fired and the person is still recorded behind it. | `T-t6-02` "a human, an event, a schedule (time), and an external system or agent" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-identity 2831cb4f, 2026-09-03 |
