# cap-work-intake: the caller's view

Proposed. Folded in from the former `cap-work-intake-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-work-intake` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-work-intake states the contract this rests on (F-b3-08); this facet reduces it to one thing a caller does: fill the envelope and send it. Normalising, validating, stamping identity and correlation, applying the ceiling and making the submission safe to repeat are the platform's work, not yours.  
  _sourced_ - `F-b3-08`, `T-t3-01` "A2A messaging · CloudEvents"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| submit (proposed) | one envelope: which kind of producer you are, who is acting and on whose behalf, which workflow and why, a correlation identifier, a ceiling, a key that identifies this submission, and your body as payload | an acknowledgement carrying the entry identifier, the correlation identifier and the job digest; the job runs after you have gone, and you follow it by correlation | proposed | `F-b3-08`, `T-t6-02` |
| submit again with the same key (proposed) | the identical envelope, because your side retried, crashed mid-send, or fired twice | the same acknowledgement and nothing new run; a repeated submission is a no-op rather than a second job, which is why the key is required rather than optional | proposed | `F-b4-08` |
| read a refusal (proposed) | an envelope the platform will not accept - a missing field, a field of your own, an unmapped format, or a key already used for a different job | problem details naming the offending field, with retryable telling you whether sending it again could ever help; there is exactly one failure format and you parse no prose | proposed | `F-b3-13`, `F-b4-07` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-work-intake` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a person types a fault report

_proposed_ - sources: `T-t1-01`, `F-b3-08`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:example:human",
  "title": "A human entry, filled once",
  "description": "Free text from a chat surface, one delegation hop, and nothing about how the work will be done. Reproduced in examples/end-to-end on 2026-09-03: `python3 run.py --entry entries/human.json` exits 0, prints `RESULT  entry=human  actor=user:corey  correlation=corr-human-0001`, and closes with `completed: 11 steps, spent 551800 of 1500000 micros, estimate was 750000`.",
  "examples": [
    {
      "envelope_version": "0.1",
      "kind": "human",
      "entry_id": "human-checkout-500s",
      "occurred_at": "2026-09-03T09:12:00Z",
      "actor": {
        "subject": "user:corey",
        "delegation_chain": [
          {
            "actor": "user:corey",
            "obtained_via": "direct"
          }
        ]
      },
      "intent": {
        "workflow_ref": "workflows/triage-and-fix.json",
        "summary": "Checkout returns 500 on coupon apply since this morning; find it and fix it."
      },
      "correlation": {
        "run_id": "run-human-0001",
        "correlation_id": "corr-human-0001",
        "depth": 0
      },
      "budget": {
        "ceiling_micros": 1500000,
        "currency": "USD",
        "on_exceed": "terminate_unit"
      },
      "idempotency_key": "human-checkout-500s-2026-09-03",
      "payload": {
        "report_text": "POST /checkout/coupon returns 500. Traceback ends at pricing/coupon.py line 88, KeyError: 'tier'."
      }
    }
  ]
}
```

### Worked example 2 (proposed): another agent delegates the same kind of job

_proposed_ - sources: `T-t1-02`, `F-b3-08`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:example:external",
  "title": "An agent entry, three hops, no human in the loop",
  "description": "Same envelope, same workflow, same fields. What differs is the subject, the chain length and a parent correlation pointing back at the submitter's own run; the submitting agent is not present when the job ends. Reproduced in examples/end-to-end on 2026-09-03: `python3 run.py --entry entries/external.json` exits 0, prints `RESULT  entry=external  actor=agent:partner-sre-bot  correlation=corr-external-0001`, and closes with the same `completed: 11 steps, spent 551800 of 1500000 micros` line as the human entry.",
  "examples": [
    {
      "envelope_version": "0.1",
      "kind": "external",
      "entry_id": "external-partner-agent-task",
      "occurred_at": "2026-09-03T09:20:15Z",
      "actor": {
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
      },
      "intent": {
        "workflow_ref": "workflows/triage-and-fix.json",
        "summary": "Partner agent submits a fault it found while running its own checks."
      },
      "correlation": {
        "run_id": "run-external-0001",
        "correlation_id": "corr-external-0001",
        "parent_correlation_id": "corr-partner-77c1",
        "depth": 1
      },
      "budget": {
        "ceiling_micros": 1500000,
        "currency": "USD",
        "on_exceed": "terminate_unit"
      },
      "idempotency_key": "partner-sre-bot-task-77c1a9",
      "payload": {
        "report_text": "Synthetic checkout probe failed 9/10 runs; response body cites pricing/coupon.py line 88 KeyError: 'tier'."
      }
    }
  ]
}
```

### The failure you handle (proposed): problem details, measured

_proposed_ - sources: `F-b3-13`.  Also carried in the body of `cap-work-intake` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:example:problem",
  "title": "A refused submission",
  "$ref": "urn:agentic:problem:0.1",
  "description": "cap-errors owns this shape and its registry; intake adds no failure format of its own. Measured in examples/end-to-end on 2026-09-03 by adding a producer-specific field to the event entry: exit code 2, media type application/problem+json, nothing admitted and nothing written.",
  "examples": [
    {
      "type": "urn:agentic:problem:document-invalid",
      "title": "Envelope failed schema validation",
      "status": 422,
      "detail": "$: property 'priority' is not allowed",
      "retryable": false,
      "instance": "entries/event.json"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-work-intake` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Make the idempotency key from something your own side already uses to identify this submission - the alert identifier, the message identifier, the delivery identifier - never a fresh random value per attempt.**  
  _why:_ Every externally-triggered action is safe to replay, and the key is how the platform knows two arrivals are one act. A fresh value per attempt turns your retry into a second job, and you will find out when both of them finish.  
  _sourced_ - `F-b4-08` "Every externally-triggered action is safe to replay"
- **Say what happened in the payload and what you want in intent. Do not describe how the work should be done, and do not add a field of your own to the envelope.**  
  _why:_ Proposed. Routing, metering and audit read the envelope and treat the payload as opaque, so a field you add is a field nothing reads and the schema refuses; and instructions about method age faster than the request they were attached to.  
  _proposed_ - `F-b3-08`
- **Name every hop of the delegation chain when you are submitting for someone else, oldest last, rather than submitting as yourself.**  
  _why:_ Every action names an actor, including delegated agent actors. Delegation chains are explicit - so an audit of what your submission caused should reach the person or system it was really for, and a one-hop chain from an agent quietly loses that.  
  _sourced_ - `F-b4-03` "Every action names an actor, including delegated agent actors. Delegation chains are explicit"
- **Send the correlation identifier you already have as the parent correlation, and let the platform mint the run identifier. Do not reuse your own run identifier as the platform's.**  
  _why:_ Proposed. This is what lets someone follow one incident across your system and this one; reusing your identifier as the platform's collides with someone else's the first time two systems submit at once, and the collision is silent.  
  _proposed_ - `F-b4-06`
- **Handle one failure: problem details with a type and a retryable flag. Fix the field it names when retryable is false; retry only when it is true. Do not parse the title or the detail text.**  
  _why:_ cap-work-intake already routes every refusal through cap-errors' registry rather than defining a failure of its own (F-b3-13), so a caller that reads type and retryable needs no branch per producer. Typed and machine-readable. Never parsed from prose is the reason the detail string is for a person, not for your code.  
  _sourced_ - `F-b3-13`, `F-b4-07` "Typed and machine-readable. Never parsed from prose"
- **Before building a second way in because the envelope did not fit, write down the field you wanted and ask for a mapper instead. A producer joins by mapping, not by getting its own path.**  
  _why:_ Proposed. The second path is always cheaper on the day and is what the one-shape rule exists to prevent: it will not carry the actor, the ceiling or the replay key, and nothing that traces the platform will know it happened.  
  _proposed_ - `T-t6-02`

## Other caller invariants

- Proposed: you fill ten fields and get one identifier back. There is no client library to hold, no registration call, no negotiation of a format, and no way to ask for or decline the identity, correlation, budget and replay handling the envelope carries; cap-work-intake fixes the contract and cap-work-intake-implement wires the builder.  
  _proposed_ - `F-b3-08`, `T-t3-01`
- A producer has no private path in, and this is checked rather than asserted. cap-work-intake states the one-shape rule from TARGET T6.2 (T-t6-02); what this facet adds is the measurement: a producer-specific field added to an otherwise valid entry is refused by the same validator that admits the other three, and the other three still pass. Measured in examples/end-to-end on 2026-09-03; the run is the definition of done below.  
  _sourced_ - `T-t6-02`, `F-b3-13` "All four enter through the same shape."

## Caller practices

- Name an entry for what happened, not for the fix you have in mind. cap-work-intake cites the same record for this (X-cap-work-intake-004): an event represents the fact that something has happened within the system, and for you the consequence is that a submission named after today's remedy is misleading in the audit trail the moment the remedy changes.  
  _sourced_ - `X-cap-work-intake-004` "An event represents the fact that something has happened within the system"
- Proposed: set a ceiling you would actually be willing to spend, not the largest number that will be accepted. The ceiling is the only statement you make about how much this job is worth, and it is what stops a loop that is going nowhere.  
  _proposed_ - `F-b4-02`
- Proposed: submit once and follow by correlation rather than holding the submission open. A job that takes minutes outlives your request, and code written to wait for a result becomes the reason someone later asks for a synchronous path.  
  _proposed_ - `T-t6-03`
- Proposed: keep one submitter in your codebase, not one per source. The envelope is the same for a chat message, an alert and a partner agent, so a second submitter is duplicated validation and a second place to forget the delegation chain.  
  _proposed_ - `T-t2-02`

## Open questions carried over

- **What does a caller do when the same key comes back as a conflict rather than as a duplicate?**  
  _deciding evidence:_ Count, across real submitters, how often a key is reused with a changed body: if it is almost always a bug in the submitter, a hard refusal is right; if it is usually a legitimate correction, the platform owes callers a way to supersede a submission.  
  _default until then:_ Proposed: a hard refusal naming both digests, and a new key for a corrected job. A supersede that silently replaces an accepted submission is indistinguishable from a lost one when someone reads the audit trail later.  
  `F-b4-08`

