# cap-identity: the caller's view

Proposed. Folded in from the former `cap-identity-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-identity` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Reduce identity to one thing a caller does: say who the work is for. cap-identity states the contract (F-b4-03) and cap-identity-implement wires it; what is left for you is one object on the envelope, and the chain behind it is the platform's work.  
  _sourced_ - `F-b4-03`, `T-t3-01` "Every action names an actor"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| enter (proposed) | your envelope with one object on it: actor.subject, the principal the work is for, and a one-hop delegation_chain naming how you were established | the work runs, and every record it produces carries that subject and the chain as it grew | proposed | `F-b4-03` |
| hand work to an agent (proposed) | nothing extra: you call a workflow, a loop or another agent the ordinary way | a chain one hop longer, with the acting agent as the current actor and you still named behind it; you neither build the hop nor pass a token | proposed | `F-b4-03` |
| be a workload (proposed) | nothing you hold: you are attested from facts about where you are running | a short-lived identity you did not have to be given, and no secret to rotate; asking for a long-lived credential is the thing you do not do | proposed | `X-end-to-end-029` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-identity` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a person asks for something

_proposed_ - sources: `F-b4-03`.

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

### Worked example 2 (proposed): an outside agent submits work on someone's behalf

_proposed_ - sources: `F-b4-03`.

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

### The one failure (proposed): identity-untrusted, in the problem-details shape cap-errors fixes

_proposed_ - sources: `F-b4-07`.  Also carried in the body of `cap-identity` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-identity` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Do not build the chain yourself, and do not add hops for work you hand off. When your request reaches an agent, a workflow or a loop, the platform adds the hop and names the agent as the current actor.**  
  _why:_ Proposed usage of what cap-identity-implement wires at dispatch. A chain assembled by callers is a chain each caller can get wrong, and the audit cannot tell a mistaken hop from a fabricated one.  
  _proposed_ - `F-b4-03`
- **If you are a workload rather than a person, do not ask for a credential and do not bake one into your image. Be attested from where you run, and let the identity you get expire.**  
  _why:_ Short-lived, cryptographically verifiable identity documents remove the need for vulnerable static secrets by issuing and rotating identities continuously, so a planted secret buys you nothing and costs you a rotation you will forget.  
  _sourced_ - `X-end-to-end-029` "eliminating the need for vulnerable static secrets by issuing and rotating identities continuously"
- **Read the chain when you want to know who did something, and read only its first element when you want to know who is acting now. Do not use anything behind that element to decide whether something is allowed.**  
  _why:_ Proposed reading rule, following the constraint cap-identity records from the standard: the prior actors are there for the audit, and a client that starts branching on them has built an authorisation rule out of an audit trail.  
  _proposed_ - `X-cross-structure-038`
- **Handle exactly one failure: identity-untrusted at status 401, not retryable. Get a fresh credential or a fresh attestation and send again; do not loop on the same envelope.**  
  _why:_ Proposed. The failure shape and its registry belong to cap-errors, so a client that already reads type and retryable needs no new branch beyond recognising one more registered type.  
  _proposed_ - `F-b4-07`
- **Do not add an identity field of your own. If you need to say who something is for, that is the subject; if you need to say who asked you to do it, that is the hop the platform adds.**  
  _why:_ Proposed. A parallel user field is not verified by anything, so it splits the audit into a trustworthy half and a decorative half, and PASS.md A6 records that a system with no identity field at all is where this started.  
  _proposed_ - `F-a6-05`
- **To see all of this run, use examples/end-to-end: the four entry files carry the two worked examples above, and the assertion in the definition of done below reads the actor off every record the run appended.**  
  _why:_ Proposed, and it is the shortest route from this page to something running: the reference runner needs no services and prints the actor of each entry it processes.  
  _proposed_ - -

## Other caller invariants

- Proposed: one object is the whole obligation. There is no token to fetch, no header to sign, no chain to build and no way to ask to run without an actor; cap-identity fixes the contract and cap-identity-implement puts issuance and verification on the platform's own paths.  
  _proposed_ - `F-b4-03`, `T-t3-01`
- You cannot gain anything by writing names into the chain: the consumer of a token MUST only consider the token's top-level claims and the party identified as the current actor by the act claim. The rest of the chain is read by audits, not by the thing deciding whether your call is allowed.  
  _sourced_ - `X-cross-structure-038` "the consumer of a token MUST only consider the token's top-level claims and the party identified as the current actor by the act claim."

## Caller practices

- Proposed: name yourself once, at the moment you decide to do the thing, and carry that name with the intent. A subject minted at send time is a new principal on every retry, and the audit then shows several people asking for one thing.  
  _proposed_ - `F-b4-03`
- cap-identity states the baggage hazard for this record; the caller-side consequence is the one that bites you: do not put the credential anywhere it will be copied along with the request. Do not put secrets, tokens, or PII in baggage. Names travel; proofs do not.  
  _sourced_ - `X-cross-structure-006` "Do not put secrets, tokens, or PII in baggage."
- Expect to ask for credentials to other systems somewhere else, which cap-identity-implement records as the boundary this capability must not grow past. Having a verifiable identity does not hand you cloud provider credentials, API keys, and database passwords; those come from the mandate broker, which is a different call with a different audit.  
  _sourced_ - `X-end-to-end-030` "cloud provider credentials, API keys, and database passwords"
- Proposed: log the subject and the depth of the chain next to your own record of the intent. When two systems disagree about who did something, those two values are what make the platform's records and yours line up.  
  _proposed_ - `F-a7-02`

## Open questions carried over

- **What does a caller do when the person it acts for is not the person who started the run, for example a scheduled entry firing work a human configured weeks ago?**  
  _deciding evidence:_ Whether the schedule entry in examples/end-to-end names the schedule or the person as subject, and which one an audit of a disputed action would need. Today that file names the schedule as subject with the person as an earlier hop.  
  _default until then:_ Proposed: name the schedule as the subject and keep the person as the hop that established it, so the current actor is the thing that actually fired and the person is still recorded behind it.  
  `T-t6-02` "a human, an event, a schedule (time), and an external system or agent"

