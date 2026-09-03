# cap-model-access: the caller's view

Proposed. Folded in from the former `cap-model-access-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-model-access` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 4 row(s) of that kind were dropped in the fold: ambient-guarantees, compose-upward, problem-details, size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make a completion callable with a class and your messages, and readable as one answer: ask for the kind of model the work needs, not for a vendor, and let the platform decide where the call goes and whether it comes back now or overnight.  
  _sourced_ - `T-t2-01`, `T-t3-01`, `T-t6-04`, `E-capability-model-access` "Composability hides the complexity."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| ask (proposed) | the model class the work needs and your messages; a deadline and a ceiling if you have them, and nothing else | one ticket. It normally comes back already redeemed, with the answer and what it cost attached; if you gave a deadline far enough out, it comes back pending and cheap and you collect it later (proposed) | proposed | `T-t3-01`, `T-t6-04` |
| collect (proposed) | a ticket | the same ticket, redeemed, with the answer and the reconciled cost - or not-yet with the earliest time to ask again, or a typed problem. There is no other call, and no separate interface for the slow path (proposed) | proposed | `T-t2-01` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-model-access` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked call 1 (proposed): a human's step needs an answer now

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:example:interactive",
  "title": "Ask an interactive class, read the answer",
  "description": "Sent: a class and messages. Returned: a redeemed ticket. You did not name a provider, choose an endpoint, set a temperature or write a retry.",
  "examples": [
    {
      "sent": {
        "model_class": "i-fast",
        "messages": [
          {
            "role": "user",
            "content": "Name the failing component and the fault family in this trace."
          }
        ],
        "idempotency_key": "human-checkout-500s-2026-09-03"
      },
      "returned": {
        "ticket_id": "tkt-8f31c0",
        "state": "redeemed",
        "model_class": "i-fast",
        "cancellable": true,
        "result": {
          "text": "checkout-service; upstream timeout family; repro: pytest tests/test_coupon.py::test_500",
          "cost_micros": 15300,
          "cost_status": "reconciled",
          "model_class": "i-fast"
        }
      }
    }
  ]
}
```

### Worked call 2 (proposed): a nightly event has ten thousand of them and can wait

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:example:batch",
  "title": "The same call, with a deadline",
  "description": "The only field that changed is the deadline, and the class. The ticket comes back pending and is collected later; cancellable is false because work already submitted may not be stoppable. Nothing else about the call differs.",
  "examples": [
    {
      "sent": {
        "model_class": "b-deep",
        "messages": [
          {
            "role": "user",
            "content": "Count occurrences of this fault family in the retained window."
          }
        ],
        "idempotency_key": "nightly-fault-sweep-2026-09-03",
        "deadline": "2026-09-04T06:00:00Z"
      },
      "returned_from_ask": {
        "ticket_id": "tkt-2b7d41",
        "state": "pending",
        "model_class": "b-deep",
        "cancellable": false,
        "earliest_retry": "2026-09-03T23:30:00Z"
      },
      "returned_from_collect": {
        "ticket_id": "tkt-2b7d41",
        "state": "redeemed",
        "model_class": "b-deep",
        "cancellable": false,
        "result": {
          "text": "412 occurrences; 9 distinct services; peak 02:10-02:40Z",
          "cost_micros": 15200,
          "cost_status": "reconciled",
          "model_class": "b-deep"
        }
      }
    }
  ]
}
```

### What a failure looks like (proposed): problem details, not prose

_proposed_ - sources: -.  Also carried in the body of `cap-model-access` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:example:no-endpoint",
  "title": "The class you asked for has nowhere to go",
  "$ref": "urn:agentic:problem:0.1",
  "description": "A class that cannot be routed is a failure with a type. It is never quietly answered by a different class. Branch on type; read detail only to report it. `urn:agentic:problem:no-endpoint-for-class` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `adapter-unavailable`, which is also 503 and retryable, with the unserved class in detail.",
  "examples": [
    {
      "type": "urn:agentic:problem:no-endpoint-for-class",
      "title": "No endpoint serves this model class",
      "status": 503,
      "detail": "no adapter binding declares class b-deep; the request was not sent and no spend was incurred",
      "retryable": true,
      "retry_after_s": 120,
      "correlation_id": "corr-schedule-0001"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-model-access` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Pick the class by what the work is worth, not by what you have heard is good: a free local class for bulk and smoke checks, an interactive class when someone is waiting, a batch class when nothing is, a coding-CLI class when the job is to change a repository.**  
  _why:_ cap-model-access states that the prefix carries the contract (T-t6-04). What this adds for a caller: the class is the only lever you have, so it is the lever that should carry your cost-versus-latency decision rather than a model name that will be stale next month.  
  _sourced_ - `T-t6-04`, `F-a4-01` "Prefix carries the contract."
- **If the answer is not needed now, say so with a deadline and let the ticket come back pending. Do not write your own overnight queue, and do not send a batch of one to a fast class because waiting felt complicated.**  
  _why:_ Proposed. The deadline is the whole of the cheap path's interface; a queue you build yourself has to solve claim, expiry, cost reconciliation and restart, which is the work this boundary already did.  
  _proposed_ - `T-t2-01`
- **Read the answer and the cost off the ticket. Do not branch on which endpoint answered, how long it took, or whether the ticket came back redeemed or pending - collect handles both.**  
  _why:_ Proposed. Those are the fields that will break on the next routing change; the class you asked for and the answer you got are the ones that will not.  
  _proposed_ - `T-t2-02`

## Other caller invariants

- cap-model-access states that the class prefix is the caller's whole routing vocabulary (T-t6-04). What that means at the call site: you name the kind of model the work needs and never a vendor, a model name, an endpoint or a key - there is no field for any of them, and their absence is what lets the platform move the work without telling you.  
  _sourced_ - `T-t6-04` "callers request a model class, not a vendor"
- Proposed: two fields go in and one ticket comes back. There is no separate batch call, no polling loop you write, no fallback list you maintain, and no way to ask which endpoint answered; a deadline, not an adapter name, is how you say the work can wait and be cheap.  
  _proposed_ - `T-t3-01`, `T-t2-01`
- A failure arrives as a typed problem object, governed by the problem-details standard cap-errors adopts, and never as prose to interpret. Branch on its type: a class with nowhere to go, a ceiling exhausted and a cancel that could not be honoured are three different outcomes, and only one of them is worth retrying.  
  _sourced_ - `F-b4-07`, `F-b3-13` "RFC 9457 problem details"
- Proposed: the idempotency key is yours and it is the whole of your replay safety. The same key means the same call; a different key means a second call that will be answered, and paid for, again.  
  _proposed_ - `F-b4-08`

## Caller practices

- Reuse one correlation id across the ask and the collect, including a collection that happens hours later, so a submission and its answer are one thing in the record rather than two unrelated calls.  
  _sourced_ - `T-t2-03` "managed across the entire structure, whichever entry point was used"
- Proposed: give the ceiling you actually mean, per call, rather than leaving it to a default. The ceiling is the only thing standing between a loop with a bad exit condition and a bill, and it is one integer.  
  _proposed_ - `F-b4-02`
- Proposed: keep a pending ticket. It is the receipt for work already paid for at submission, and discarding it because the process restarted means asking for the same answer twice and paying twice.  
  _proposed_ - `F-b4-08`
- cap-model-access already states that model selection is a decision layer of its own. What it adds for a caller: when a class keeps giving answers that are too weak or too expensive, the fix is a routing change behind the interface, not a special case in your code that names a better model.  
  _sourced_ - `X-end-to-end-056` "selecting which model should handle a given query"

## Open questions carried over

- **Should a caller ever be able to pin a specific model inside a class, for a reproduction or a comparison?**  
  _deciding evidence:_ Count the cases where someone genuinely needs the same member twice rather than the same class twice. If they are all evaluations and regressions, they belong to a comparison harness that names members deliberately, not to the call every step makes.  
  _default until then:_ No pinning field. The class is the whole vocabulary, and a comparison harness can hold its own binding; adding the field would let every caller pin, and the interface would be a vendor list again within a quarter.  
  `T-t3-02`, `T-t6-04` "It cannot be daunting or overly complex"

