---
name: cap-idempotency-use
description: How to use the Idempotency capability as a caller: put one field on what you send, send it again as often as you like, and get one execution and one answer back. Load it when writing a client, a webhook receiver, a retry loop or a scheduled job against this platform, when deciding what to do after a timeout with no answer, when the same alert or message could be delivered twice, when you are tempted to check first and then send, or when a repeated send came back with a 409 you did not expect.
---

# cap-idempotency-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-idempotency states the contract this rests on (F-b4-08); this facet reduces it to one thing a caller does: generate one random key per intent and put it on the envelope. Everything else, including recognising the repeat and answering it, is the platform's work. | sourced | `F-b4-08`, `T-t3-01` "Every externally-triggered action is safe to replay" |

## Entities

| Entity |
|---|
| `E-capability-idempotency` |
| `E-concern-idempotency` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| send (proposed) | your envelope, with one extra field: idempotency_key, a random identifier you generate once per intent and reuse for every re-send of that same intent | the result of the one execution, whether this was the first send or the fifth | proposed | `F-b4-08` |
| re-send (proposed) | the byte-identical envelope again, after a timeout, a crash, a redelivery or a manual re-fire | the first answer, unchanged, with nothing re-run and nothing new appended to the log; you do not have to know whether the first send arrived | proposed | `F-b4-08` |
| read a conflict (proposed) | the same key with a changed body, which is the one thing you are not allowed to do | a typed problem of type urn:agentic:problem:idempotency-conflict with status 409 and retryable false; the fix is a new key, not a retry | proposed | `X-cap-idempotency-002` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): the same request sent twice** (proposed; sources: `F-b4-08`)

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

**Worked example 2 (proposed): the same key with a different body** (proposed; sources: `F-b4-07`)

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

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| All three of TARGET T1's ways in reach this the same way. A human must be able to enter the system, an agent must be able to enter the system, and an internal or external event must be able to enter the system; each carries the same idempotency_key field on the same envelope, and nothing downstream branches on which of the three it was. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| Proposed: one field is the whole obligation. There is no claim call to make, no lock to take, no check-then-send dance, and no way to ask for replay safety or to decline it; cap-idempotency fixes the contract and cap-idempotency-implement wires it into the entry path. | proposed | `F-b4-08`, `T-t3-01` |
| Enhancing one aspect leaves the rest untouched: changing the retention window, moving the claim from a log fold to a lease store, or adding a new entry kind changes nothing in a caller that sends one key per intent, because the key is the only thing it was ever asked for. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The obligation is kept to one field because a contract that is daunting or overly complex will not be used, and a caller that finds replay safety expensive will simply not send the key. | sourced | `T-t3-02`, `T-t3-01` "It cannot be daunting or overly complex, or no one will use it." |
| Proposed: the key travels with the request, so composition is free. A workflow, a loop or an agent that re-sends on your behalf inherits the same key and therefore the same answer, and a duplicate that arrives through a different entry kind is still the same duplicate. | proposed | `T-t2-03` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: you never see the claim, the lease, the fencing token or which adapter answered. A duplicate looks like the first answer, which is the point; if a caller could tell them apart it would start branching on the difference. | proposed | - |
| Proposed: holding the key does not entitle you to the first result. If the first send was made by someone else, identity and policy decide what comes back, not possession of the key. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Generate one random identifier per intent, at the moment you decide to do the thing, and store it with the intent rather than minting it at the moment of sending. | It is RECOMMENDED that a UUID or a similar random identifier be used as an idempotency key. A key generated at send time is new on every retry, so the retry looks like a new intent, which is the failure this field exists to prevent. | sourced | `X-cap-idempotency-005` "It is RECOMMENDED that a UUID or a similar random identifier be used as an idempotency key." |
| 2 | Put it on the envelope as idempotency_key and send. Send the identical envelope again whenever you are unsure the first one arrived: after a timeout, after a crash, after a redelivery, or because a schedule fired twice. | Proposed usage of the contract cap-idempotency states (F-b4-08). Re-sending is cheaper and more reliable than asking whether the first send landed, and asking is itself a request that can time out. | proposed | `F-b4-08` |
| 3 | Reuse the key for every re-send of that one intent, and never for anything else: don't use the same key across different user sessions or checkout attempts. | cap-idempotency states this scoping rule (X-cap-idempotency-004); the consequence for a caller is that a key reused across attempts merges two things that were meant to happen twice, and the second one silently does not happen. The symptom is a missing action with no error anywhere. | sourced | `X-cap-idempotency-004` "Don't use the same key across different user sessions or checkout attempts." |
| 4 | Do not change the body between sends of one key. If the intent changed, it is a new intent: mint a new key. | cap-idempotency states the normative uniqueness rule (X-cap-idempotency-002): the idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload. For a caller that means a changed body under an old key is a conflict, not an update. | sourced | `X-cap-idempotency-002` "The idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload." |
| 5 | Handle exactly one failure, the 409 in worked example 2, and handle it by minting a new key rather than retrying. Everything else that comes back is the ordinary answer or an ordinary typed failure. | Proposed. The failure shape and its registry belong to cap-errors, so a caller that already reads type and retryable needs no new branch for this capability beyond recognising one more registered type. | proposed | `F-b4-07` |
| 6 | Ask the boundary you send to for its retention window, and treat a re-send after that window as a fresh request that will execute again. | cap-idempotency states that retention windows, parameter-mismatch behaviour, and concurrency handling all differ between providers; what a caller has to take from that is that the window belongs to the boundary rather than to the field, so a re-send weeks later is not protected by a key that has expired. | sourced | `X-cap-idempotency-007` "retention windows, parameter-mismatch behaviour, and concurrency handling all differ between providers" |
| 7 | Proposed: if you want to see all of this run, use examples/end-to-end. Section 3 of its test.sh is the replay in worked example 1, and re-sending a modified envelope under the same key reproduces worked example 2. | Proposed, and it is the shortest route from this page to a working example: the reference runner is small, needs no services, and prints the replay line and the problem body verbatim. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Judge your own client by the definition cap-idempotency cites (X-cap-idempotency-003), the ability to apply the same operation multiple times without changing the result beyond the first try: if your retry path can produce a second effect anywhere, the key on the envelope has not saved you. | sourced | `X-cap-idempotency-003` "the ability to apply the same operation multiple times without changing the result beyond the first try" |
| Add deduplication on your own side of the boundary too, rather than treating the platform's key as the only defence: add message deduplication in your consumers to handle queue redeliveries. A redelivery you never noticed is one your retry logic never got to see. | sourced | `X-cap-idempotency-006` "add message deduplication in your consumers to handle queue redeliveries" |
| Proposed: prefer re-sending over polling for whether the first send arrived. A re-send answers the question and completes the work in one call, where a poll adds a request that can itself fail, and leaves you with two code paths to keep correct. | proposed | `F-b4-08` |
| Proposed: log the key you generated next to the intent, not only in the outgoing request. When something looks like it happened twice, the key is what makes the two arrivals findable; without it you are comparing timestamps. | proposed | `F-a7-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `cd examples/end-to-end && bash test.sh`. Section 3 sends the human entry envelope a second time, unchanged, and asserts: exit code 0, the answer is recognised as a replay, and the ledger record count is unchanged. |
| Expected | exit 0 and a closing line `passed 29, failed 0`, with section 3 printing `ok   replay exits 0 (0)`, `ok   replay recognised`, and `ok   no records appended (56)`. |
| Deliberate breakage | In `examples/end-to-end/run.py`, replace the line `prior = ledger.completed(envelope["idempotency_key"])` with `prior = None`, which keeps the key on the wire and removes the only thing that claims it. Change nothing else. |
| Expected failure | exit 1 and `passed 27, failed 2`: section 3 reports `FAIL replay not recognised` and `FAIL no records appended (expected 56, got 70)`, because the second send re-ran the whole workflow and appended fourteen more records. `ok   replay exits 0 (0)` still passes, which is the useful part: nothing errored, the work simply happened twice. Measured in session cap-idempotency 2831cb4f on 2026-09-03; both runs were performed and run.py was restored. |
| Status | measured |
| Evidence | `F-b4-08`, `F-b3-16` "Every externally-triggered action is safe to replay" |

## Composes with

Builds on: `cap-idempotency`, `cap-idempotency-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What does a caller do when a re-send arrives while the first execution is still running? | Whether the answering adapter can report an in-flight duplicate at all; cap-idempotency-implement records that the log-fold adapter cannot and the lease adapter can, and the P15 race criterion is what shows which is running. | Proposed: wait and re-send rather than escalating. Under the lease adapter the caller is told the first execution is in flight; under the fold adapter a second execution may start, which is the gap the pair exists to make visible rather than something a caller can work around. | `F-b3-16` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-idempotency 2831cb4f, 2026-09-03 |
