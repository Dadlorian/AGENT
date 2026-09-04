# cap-mandate-broker: the caller's view

Proposed. Folded in from the former `cap-mandate-broker-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-mandate-broker` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 0 row(s) of that kind were dropped in the fold.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make brokered authority usable in two moves: name a destination and act with the handle you get back, or name an action class and act under a mandate someone approved. A caller never sees a credential, never picks an issuer, and never writes an expiry.  
  _sourced_ - `T-t3-01` "It has to be simple to use."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| approve (proposed): what a human does | an action class - spend, deploy or send - a ceiling, the destinations it may be used against, and how long the approval lasts | a signed mandate somebody else can check later; nothing runs yet and nothing is minted (proposed) | proposed | - |
| reach (proposed): what an agent does | one destination identifier, and the mandate reference if the action is irreversible | a handle to use for that one call, and the call itself; the credential is added outside the sandbox and the agent never sees it (proposed) | proposed | - |
| act (proposed): what an event triggers | the entry envelope's actor and delegation chain, unchanged, plus the destination the triggered work needs | the same handle an agent or a human would get; an event that names no approving actor gets no mandate and so cannot take an irreversible action (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-mandate-broker` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a human approves bounds up front and an agent acts under them later

_proposed_ - sources: -.

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

### Worked example 2 (proposed): an event triggers work, and a handle presented at the wrong destination is refused

_proposed_ - sources: -.  Also carried in the body of `cap-mandate-broker` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:mandate-broker:example:audience-refused",
  "title": "A credential minted for one destination is worth nothing at another",
  "description": "An alert enters as an event and the work it triggers reaches a metrics service. A later step tries to reuse the same authority against a deploy endpoint. The second destination refuses it on its own audience check, and the refusal is a problem details object with a type the caller branches on. No retry is attempted, because the answer will not change. `urn:agentic:problem:credential-audience-mismatch` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `identity-untrusted`, which is also 401 and not retryable, naming both destinations in detail, as the open question below records.",
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

## What a caller does

Step 1 below is carried in the body of `cap-mandate-broker` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Mint one handle per destination. If the next call goes somewhere else, ask for another handle; never carry one across.**  
  _why:_ cap-mandate-broker binds a handle to a single audience (X-cap-mandate-broker-003), so reusing one is not a shortcut - it is a call that will be refused by the destination itself, and worked example 2 is exactly that case.  
  _sourced_ - `X-cap-mandate-broker-003` "the resource server should reject any token whose audience does not match its own identifier"
- **For anything you cannot take back - money moving, a deploy landing, a message leaving - get a mandate first: an approving person states the ceiling, the destinations and how long the approval lasts, and you name it when you act.**  
  _why:_ A human must be able to enter the system, and approving bounds once is how a person stays in the loop for work that will happen when they are not watching; worked example 1 is the shape of it.  
  _sourced_ - `T-t1-01`, `X-end-to-end-071` "the human signs an Intent Mandate upfront and the agent acts autonomously later"
- **When work is triggered by an event or a schedule, pass the entry envelope's actor and delegation chain through unchanged. Do not substitute a service account of your own to make a refusal go away.**  
  _why:_ An internal or external event must be able to enter the system on the same terms as a person or an agent; replacing the actor turns a refusal into an unattributable action, which is the one thing a mandate exists to prevent.  
  _sourced_ - `T-t1-03` "An internal or external event must be able to enter the system."
- **On a refusal, branch on the problem's type member and stop. Show detail to a person; do not parse it, key metrics on it, or retry a refusal marked retryable false.**  
  _why:_ cap-mandate-broker adopts the platform's failure shape rather than inventing one (F-b3-13): title and detail are written for readers and may be reworded, while the type is the part you were promised. An expired mandate is still expired on the second attempt, and a handle minted for another destination will not start matching.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"
- **Let the handle expire with your task. Do not cache it, pass it to a sub-agent for later, or ask for a longer lifetime; if a task outlives its authority, let it fail and be re-dispatched.**  
  _why:_ cap-mandate-broker makes expiry the revocation mechanism (X-cap-mandate-broker-006), so a cached handle is not an optimisation - it is the one way a caller can recreate the long-lived secret the platform just removed.  
  _sourced_ - `X-cap-mandate-broker-006` "non-refreshable by design"
- **Read the two worked examples above, then stop. Open cap-mandate-broker only if you have to judge whether an authority is correctly scoped, and cap-mandate-broker-implement only if you are building a broker rather than calling one.**  
  _why:_ A destination, sometimes a mandate reference, and one outcome to read is the whole consuming surface; making someone learn token exchange and credential formats before they can make a call is the kind of weight that stops a platform from being used at all.  
  _sourced_ - `T-t3-02` "It cannot be daunting or overly complex, or no one will use it."

## Other caller invariants

- A caller never holds a credential. cap-mandate-broker states why (F-a3-05); for a caller the consequence is simply that there is nothing to store, nothing to rotate and nothing to leak: a handle is worthless to anyone who reads it, including you.  
  _sourced_ - `F-a3-05` "No real secret inside the VM"
- The complexity is hidden on purpose: a caller never chooses an issuer, a key, a signing algorithm, a lifetime or a trust anchor. All of those exist, and cap-mandate-broker-implement is where they are decided; none of them appears in what a caller writes.  
  _sourced_ - `T-t2-01` "Composability hides the complexity."
- Failure arrives as a problem details object, the shape cap-mandate-broker adopts for this interface (F-b3-13), never as a stack trace from a key store or a bare 401 from a destination. A caller branches on the type member and reads retryable; it never matches on wording.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"
- Nothing you get back tells you how you will be scored. cap-mandate-broker states design rule 6 on this interface (F-b1-07): a mandate carries a ceiling, destinations and a validity period, and never the criterion the work done under it will be judged against.  
  _sourced_ - `F-b1-07` "An agent sees its outcome, never the criterion it is judged against"

## Caller practices

- Proposed: log the handle id, the destination and the expiry, and nothing else. That is enough to explain any refusal afterwards, and a handle id is designed to be useless to whoever reads the log.  
  _proposed_ - -
- Proposed: ask for the narrowest scope that does the job, not the scope you might need later. A second handle costs one call; an over-scoped one is the blast radius of every mistake made under it.  
  _proposed_ - -
- Proposed: when you need a mandate, ask for the bounds you can justify in a sentence - this much, to these destinations, until this date. A person approving something they cannot restate is not really approving it.  
  _proposed_ - -
- Proposed: put the correlation id you were given on every mint. It is what ties an action taken hours later back to the entry that caused it, and nobody can add it afterwards.  
  _proposed_ - -

## Open questions carried over

- **What should a caller do when it needs an irreversible action and no mandate exists yet - refuse, or park the work and ask a person?**  
  _deciding evidence:_ Count how often work reaches an irreversible step with no mandate, and how many of those a person approves within the run's budget; if most are approved, parking is cheaper than a failed run, and if most are not, refusing early saves the spend.  
  _default until then:_ Proposed: refuse with a typed problem naming the action class and the bounds that would be needed, and leave asking a person to whichever composition wanted the action. A brokering call that blocks waiting for a human has turned a two-move surface into a workflow.  
  `T-t3-02` "It cannot be daunting or overly complex"
- **cap-errors' closed problem registry has no row for a credential presented at a destination it was not minted for, so which type does the refusal carry?**  
  _deciding evidence:_ cap-errors requires 1-3-1 rather than minting a suffix at the call site, so the three options were: reuse the registered `identity-untrusted`, which is 401 and not retryable but names a delegation chain that does not verify, when here the chain verifies and only the audience is wrong; reuse `policy-denied`, which implies a policy rule refused the call when no policy was consulted; or add one row `credential-audience-mismatch` (401, not retryable, extension members audience_minted_for and audience_presented_at) to docs/decomposition.md section 2.1.6 and use it. The third is recommended and is what the worked example and the definition of done show, pending that row.  
  _default until then:_ `urn:agentic:problem:credential-audience-mismatch`, marked proposed and pending registration; until the row lands an implementation returns `identity-untrusted` with both destinations in detail rather than inventing a type, and a caller mints a new handle for the destination it actually needs.  
  `T-t5-02`, `F-b3-13` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation"

