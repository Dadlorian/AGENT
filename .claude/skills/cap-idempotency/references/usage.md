# cap-idempotency: the caller's view

Proposed. Folded in from the former `cap-idempotency-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-idempotency` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-idempotency states the contract this rests on (F-b4-08); this facet reduces it to one thing a caller does: generate one random key per intent and put it on the envelope. Everything else, including recognising the repeat and answering it, is the platform's work.  
  _sourced_ - `F-b4-08`, `T-t3-01` "Every externally-triggered action is safe to replay"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| send (proposed) | your envelope, with one extra field: idempotency_key, a random identifier you generate once per intent and reuse for every re-send of that same intent | the result of the one execution, whether this was the first send or the fifth | proposed | `F-b4-08` |
| re-send (proposed) | the byte-identical envelope again, after a timeout, a crash, a redelivery or a manual re-fire | the first answer, unchanged, with nothing re-run and nothing new appended to the log; you do not have to know whether the first send arrived | proposed | `F-b4-08` |
| read a conflict (proposed) | the same key with a changed body, which is the one thing you are not allowed to do | a typed problem of type urn:agentic:problem:idempotency-conflict with status 409 and retryable false; the fix is a new key, not a retry | proposed | `X-cap-idempotency-002` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-idempotency` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): the same request sent twice

_proposed_ - sources: `F-b4-08`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:example:replay",
  "title": "A re-send is a no-op",
  "description": "Send an entry envelope carrying idempotency_key 'human-checkout-500s-2026-09-03', then send the identical envelope again. Reproduced in examples/end-to-end on 2026-09-03: the second send exits 0 and prints 'REPLAY: idempotency key already completed at seq 13; nothing re-run, nothing appended.', the record count is unchanged at 56, and the first outcome is returned.",
  "examples": [
    {
      "sent_twice": true,
      "idempotency_key": "human-checkout-500s-2026-09-03",
      "answer": {
        "outcome": "duplicate",
        "run_id": "run-human-0001",
        "entry": "human",
        "spent_micros": 551800,
        "state": "completed"
      },
      "records_appended_by_the_second_send": 0
    }
  ]
}
```

### Worked example 2 (proposed): the same key with a different body

_proposed_ - sources: `F-b4-07`.  Also carried in the body of `cap-idempotency` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:example:conflict",
  "title": "Same key, different envelope",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Change one field of the payload and re-send under the same key. Reproduced in examples/end-to-end on 2026-09-03: exit code 2, body on stdout with media type application/problem+json, nothing executed.",
  "examples": [
    {
      "type": "urn:agentic:problem:idempotency-conflict",
      "title": "Same idempotency key, different envelope",
      "status": 409,
      "detail": "key human-checkout-500s-2026-09-03 was completed at seq 13 with a different body",
      "retryable": false
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-idempotency` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Put it on the envelope as idempotency_key and send. Send the identical envelope again whenever you are unsure the first one arrived: after a timeout, after a crash, after a redelivery, or because a schedule fired twice.**  
  _why:_ Proposed usage of the contract cap-idempotency states (F-b4-08). Re-sending is cheaper and more reliable than asking whether the first send landed, and asking is itself a request that can time out.  
  _proposed_ - `F-b4-08`
- **Reuse the key for every re-send of that one intent, and never for anything else: don't use the same key across different user sessions or checkout attempts.**  
  _why:_ cap-idempotency states this scoping rule (X-cap-idempotency-004); the consequence for a caller is that a key reused across attempts merges two things that were meant to happen twice, and the second one silently does not happen. The symptom is a missing action with no error anywhere.  
  _sourced_ - `X-cap-idempotency-004` "Don't use the same key across different user sessions or checkout attempts."
- **Do not change the body between sends of one key. If the intent changed, it is a new intent: mint a new key.**  
  _why:_ cap-idempotency states the normative uniqueness rule (X-cap-idempotency-002): the idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload. For a caller that means a changed body under an old key is a conflict, not an update.  
  _sourced_ - `X-cap-idempotency-002` "The idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload."
- **Handle exactly one failure, the 409 in worked example 2, and handle it by minting a new key rather than retrying. Everything else that comes back is the ordinary answer or an ordinary typed failure.**  
  _why:_ Proposed. The failure shape and its registry belong to cap-errors, so a caller that already reads type and retryable needs no new branch for this capability beyond recognising one more registered type.  
  _proposed_ - `F-b4-07`
- **Ask the boundary you send to for its retention window, and treat a re-send after that window as a fresh request that will execute again.**  
  _why:_ cap-idempotency states that retention windows, parameter-mismatch behaviour, and concurrency handling all differ between providers; what a caller has to take from that is that the window belongs to the boundary rather than to the field, so a re-send weeks later is not protected by a key that has expired.  
  _sourced_ - `X-cap-idempotency-007` "retention windows, parameter-mismatch behaviour, and concurrency handling all differ between providers"
- **Proposed: if you want to see all of this run, use examples/end-to-end. Section 3 of its test.sh is the replay in worked example 1, and re-sending a modified envelope under the same key reproduces worked example 2.**  
  _why:_ Proposed, and it is the shortest route from this page to a working example: the reference runner is small, needs no services, and prints the replay line and the problem body verbatim.  
  _proposed_ - -

## Other caller invariants

- Proposed: one field is the whole obligation. There is no claim call to make, no lock to take, no check-then-send dance, and no way to ask for replay safety or to decline it; cap-idempotency fixes the contract and cap-idempotency-implement wires it into the entry path.  
  _proposed_ - `F-b4-08`, `T-t3-01`
- Proposed: the key travels with the request, so composition is free. A workflow, a loop or an agent that re-sends on your behalf inherits the same key and therefore the same answer, and a duplicate that arrives through a different entry kind is still the same duplicate.  
  _proposed_ - `T-t2-03`

## Caller practices

- Judge your own client by the definition cap-idempotency cites (X-cap-idempotency-003), the ability to apply the same operation multiple times without changing the result beyond the first try: if your retry path can produce a second effect anywhere, the key on the envelope has not saved you.  
  _sourced_ - `X-cap-idempotency-003` "the ability to apply the same operation multiple times without changing the result beyond the first try"
- Add deduplication on your own side of the boundary too, rather than treating the platform's key as the only defence: add message deduplication in your consumers to handle queue redeliveries. A redelivery you never noticed is one your retry logic never got to see.  
  _sourced_ - `X-cap-idempotency-006` "add message deduplication in your consumers to handle queue redeliveries"
- Proposed: prefer re-sending over polling for whether the first send arrived. A re-send answers the question and completes the work in one call, where a poll adds a request that can itself fail, and leaves you with two code paths to keep correct.  
  _proposed_ - `F-b4-08`
- Proposed: log the key you generated next to the intent, not only in the outgoing request. When something looks like it happened twice, the key is what makes the two arrivals findable; without it you are comparing timestamps.  
  _proposed_ - `F-a7-02`

## Open questions carried over

- **What does a caller do when a re-send arrives while the first execution is still running?**  
  _deciding evidence:_ Whether the answering adapter can report an in-flight duplicate at all; cap-idempotency-implement records that the log-fold adapter cannot and the lease adapter can, and the P15 race criterion is what shows which is running.  
  _default until then:_ Proposed: wait and re-send rather than escalating. Under the lease adapter the caller is told the first execution is in flight; under the fold adapter a second execution may start, which is the gap the pair exists to make visible rather than something a caller can work around.  
  `F-b3-16`

