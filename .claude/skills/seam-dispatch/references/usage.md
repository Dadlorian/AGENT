# seam-dispatch: the caller's view

Proposed. This seam has no separate `-use` skill; the ideal facet carries the usability section and
this file carries the long part of it. The body of `seam-dispatch` is enough to make a first call.
Open this file for the minimal inputs and outputs, the three worked calls - one for each of TARGET
T1's three ways in - and the worked refusal.

The caller doctrine every capability of this platform shares - the four entries of TARGET T6.2
arriving through one entry envelope, one result or one problem object and no third kind of answer,
composing upward instead of adding arguments, changing configuration instead of branching on which
implementation answered, and the cross-cutting guarantees that can be neither requested nor declined -
is stated once in `cap-consumption` and is **not** repeated here. Read that skill first; this file
carries only what is particular to a dispatch.

Ids resolve with `python3 tools/kb.py show <id>`.

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| `dispatch` | the document (what to do), who is acting and on whose behalf, a spend ceiling, a deadline, a key that makes a repeat safe, and a correlation record. Everything else - the isolation profile, the grace window, the context inheritance - has a default. | one result. `state` says how it ended, `stop_reason` says why, `outputs` says what exists and where it became durable, `usage` says what it cost. There is no second call to make before you have an answer. | proposed | `F-b5-02` |
| `cancel` | the dispatch id | acceptance, not a stop. Keep reading until the terminal result: `cancelled` if it landed inside the grace window, `cancel_timeout` if it did not. Cancelling something already terminal returns its result and is not an error. | proposed | `F-a3-09` |
| `resume` | a new dispatch id naming the previous one | a fresh result continuing at the first step whose checkpoint reference is null, under whatever ceiling remained. The prior result is untouched. | proposed | `X-cross-structure-045` |
| a repeat | the same request under the same key | the recorded result of the first execution, with nothing re-executed. A different body under the same key is refused with `urn:agentic:problem:idempotency-conflict`. | proposed | `X-cross-structure-042` |

**The one field to branch on is `stop_reason`.** `state` tells you whether the run is over;
`stop_reason` tells you what to do next. Treat `outputs`, `usage`, `folded` and `step` as data to
pass on, and read a failure by its problem `type`, never by its words.

## The three ways in

`seam-dispatch` states as an invariant that TARGET T1's three ways in - a human, an agent, an
internal or external event - reach a unit of work through the same request, and that how the work
arrived is a member of the entry envelope `cap-work-intake` owns rather than of the dispatch. What
follows shows that: the three calls differ only in the `actor.subject` prefix and the delegation
chain depth. Nothing else in the request changes, and no adapter branches on the producer.

### Worked call 1 (proposed): a human enters

_proposed_ - sources: `T-t1-01`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:example:human",
  "title": "A person types a request and one unit runs",
  "examples": [
    {
      "sent": {
        "dispatch_id": "6b1f0f9a-3c2d-4a11-9f0e-1a2b3c4d5e6f",
        "idempotency_key": "run-human-0001/fix-coupon-500s",
        "document": { "$ref": "urn:agentic:core:document:0.1", "intent": "Checkout returns 500 on coupon apply since this morning; find it and fix it." },
        "criterion_ref": "criterion://fix-acceptable/v1",
        "actor": {
          "subject": "user:corey",
          "delegation_chain": [ { "actor": "user:corey", "obtained_via": "direct" } ]
        },
        "budget": { "ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit" },
        "deadline": { "not_after": "2026-09-03T10:12:00Z", "max_duration_s": 3600 },
        "isolation": { "profile": "standard", "egress": "none" },
        "correlation": { "run_id": "run-human-0001", "root_dispatch_id": "6b1f0f9a-3c2d-4a11-9f0e-1a2b3c4d5e6f", "depth": 0 }
      },
      "returned": {
        "dispatch_id": "6b1f0f9a-3c2d-4a11-9f0e-1a2b3c4d5e6f",
        "state": "completed",
        "stop_reason": "end_turn",
        "started_at": "2026-09-03T09:12:01Z",
        "ended_at": "2026-09-03T09:12:14Z",
        "partial": false,
        "outputs": [
          { "digest": "sha256:06db7866ae79ab5fdab53468e34271588fd040ea7e3471c81dd6c54383e45a29",
            "media_type": "text/x-diff",
            "recorded_at_head": "sha256:8b2e1cf42af4a63eb9063e417ceeeb11fd92537b6a14b635c5bc5fa7cb13e5c6" }
        ],
        "usage": { "cost_micros": 551800, "currency": "USD", "wall_ms": 13000, "metered_calls": 7 },
        "correlation": { "run_id": "run-human-0001", "root_dispatch_id": "6b1f0f9a-3c2d-4a11-9f0e-1a2b3c4d5e6f", "depth": 0 }
      }
    }
  ]
}
```

Six required members supplied, one result read back. The isolation profile, the ten-second grace
window and the `none` context inheritance were all defaults.

### Worked call 2 (proposed): an agent enters, and folds its context back

_proposed_ - sources: `T-t1-02`, `X-end-to-end-005`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:example:agent",
  "title": "Another party's agent submits work; the sub-unit folds a summary back",
  "examples": [
    {
      "sent": {
        "dispatch_id": "b2c3d4e5-6f70-4812-9a3b-4c5d6e7f8091",
        "idempotency_key": "run-external-0001/triage",
        "document": { "$ref": "urn:agentic:core:document:0.1", "intent": "Reduce the reproduction to one failing test and name the files it touches." },
        "criterion_ref": "criterion://repro-minimal/v1",
        "actor": {
          "subject": "agent:partner-sre-bot",
          "delegation_chain": [
            { "actor": "user:corey", "obtained_via": "direct" },
            { "actor": "service:intake", "obtained_via": "rfc8693_token_exchange" },
            { "actor": "agent:partner-sre-bot", "obtained_via": "workload_attestation" }
          ]
        },
        "budget": { "ceiling_micros": 400000, "currency": "USD", "on_exceed": "terminate_unit" },
        "deadline": { "not_after": "2026-09-03T09:40:00Z", "max_duration_s": 900, "cancel_grace_s": 10 },
        "isolation": { "profile": "standard", "egress": "allowlist", "egress_allowlist": ["repo.internal"] },
        "context": { "inherits": "folded_summary", "budget_tokens": 60000 },
        "correlation": { "run_id": "run-external-0001", "root_dispatch_id": "a1b2c3d4-0000-4000-8000-000000000001", "parent_dispatch_id": "a1b2c3d4-0000-4000-8000-000000000001", "depth": 1 }
      },
      "returned": {
        "dispatch_id": "b2c3d4e5-6f70-4812-9a3b-4c5d6e7f8091",
        "state": "completed",
        "stop_reason": "end_turn",
        "started_at": "2026-09-03T09:31:02Z",
        "ended_at": "2026-09-03T09:33:48Z",
        "partial": false,
        "outputs": [
          { "digest": "sha256:4c0dc2f515d802eb341225bfb42e289eb308b02c0548e7a6d9d8a31c06e35761",
            "media_type": "application/json",
            "recorded_at_head": "sha256:c055919c2902cfa8ff157257c97044e8a3db9cca6496a8c835d04c2fc07af629" }
        ],
        "folded": { "summary_digest": "sha256:29c74640e97142b0cc8c183597ca8e84d7651428239aff477f4071308100f21c", "media_type": "text/markdown", "dropped_token_estimate": 41200 },
        "step": {
          "run_id": "run-external-0001", "step_id": "repro", "attempt": 1,
          "dispatch_id": "b2c3d4e5-6f70-4812-9a3b-4c5d6e7f8091",
          "idempotency_key": "run-external-0001/triage",
          "checkpoint_ref": "sha256:c055919c2902cfa8ff157257c97044e8a3db9cca6496a8c835d04c2fc07af629",
          "replay_semantic": "return_recorded_result",
          "state": "completed",
          "compactions": [
            { "at": "2026-09-03T09:32:40Z", "strategy": "branch_and_fold", "before_tokens": 58900, "after_tokens": 17700,
              "summary_digest": "sha256:29c74640e97142b0cc8c183597ca8e84d7651428239aff477f4071308100f21c" }
          ]
        },
        "usage": { "cost_micros": 218400, "currency": "USD", "wall_ms": 166000, "metered_calls": 4 },
        "correlation": { "run_id": "run-external-0001", "root_dispatch_id": "a1b2c3d4-0000-4000-8000-000000000001", "parent_dispatch_id": "a1b2c3d4-0000-4000-8000-000000000001", "depth": 1 }
      }
    }
  ]
}
```

The parent receives the folded summary and the digests, never the 41,200 tokens the sub-unit read.
The compaction is a recorded transition, so a reader can tell that context was dropped, by which
strategy, and how much.

### Worked call 3 (proposed): an event enters, and the deadline stops it with work already durable

_proposed_ - sources: `T-t1-03`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:example:event",
  "title": "An alert starts a unit; the wall-clock ceiling ends it as a partial",
  "examples": [
    {
      "sent": {
        "dispatch_id": "0f1e2d3c-4b5a-4697-8899-aabbccddeeff",
        "idempotency_key": "alert-8f31c0-checkout-500s",
        "document": { "$ref": "urn:agentic:core:document:0.1", "intent": "Error-rate alert on the checkout service crossed threshold; triage it." },
        "criterion_ref": "criterion://triage-acceptable/v1",
        "actor": {
          "subject": "service:alerting",
          "delegation_chain": [
            { "actor": "user:corey", "obtained_via": "direct" },
            { "actor": "service:alerting", "obtained_via": "rfc8693_token_exchange" }
          ]
        },
        "budget": { "ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit" },
        "deadline": { "not_after": "2026-09-03T09:09:00Z", "max_duration_s": 60, "cancel_grace_s": 10 },
        "isolation": { "profile": "standard", "egress": "none" },
        "correlation": { "run_id": "run-event-0001", "root_dispatch_id": "0f1e2d3c-4b5a-4697-8899-aabbccddeeff", "depth": 0 }
      },
      "returned": {
        "dispatch_id": "0f1e2d3c-4b5a-4697-8899-aabbccddeeff",
        "state": "canceled",
        "stop_reason": "deadline_exceeded",
        "started_at": "2026-09-03T09:07:42Z",
        "ended_at": "2026-09-03T09:08:49Z",
        "partial": true,
        "outputs": [
          { "digest": "sha256:5c1e4c89711e95eecb66c76e4cadd4a6e85659282ffe032ded6ce4a55e489209",
            "media_type": "application/json",
            "recorded_at_head": "sha256:076299b204ba57d863eb74a166f531e2a8f9b4b5d426b9ffd52ccdbaba0f11a4" }
        ],
        "usage": { "cost_micros": 15300, "currency": "USD", "wall_ms": 67000, "metered_calls": 1 },
        "correlation": { "run_id": "run-event-0001", "root_dispatch_id": "0f1e2d3c-4b5a-4697-8899-aabbccddeeff", "depth": 0 }
      }
    }
  ]
}
```

The deadline was reached, cancel was issued, and the unit reached a terminal state inside the grace
window - so this is `canceled` with `deadline_exceeded`, not a failure. One output already carries a
`recorded_at_head`, so `partial` is true and the work is not lost. Resuming means a **new**
dispatch id naming this one; nothing here is promoted or rewritten.

## The worked refusal

A refusal is an object, not a sentence. The one in the body of `seam-dispatch` is a spend refusal;
here is a schedule-triggered run refused before it spent anything.

_proposed_ - sources: `F-b4-07`, `T-t1-03`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:example:policy-denied",
  "title": "A recurring sweep was refused before execution",
  "$ref": "urn:agentic:problem:0.1",
  "examples": [
    {
      "sent_actor": { "subject": "schedule:nightly-fault-sweep",
                      "delegation_chain": [ { "actor": "user:corey", "obtained_via": "direct" },
                                            { "actor": "schedule:nightly-fault-sweep", "obtained_via": "rfc8693_token_exchange" } ] },
      "returned": {
        "type": "urn:agentic:problem:policy-denied",
        "title": "Egress allowlist is not permitted for this actor on this profile",
        "status": 403,
        "detail": "rule egress.allowlist.requires_human_actor refused the request; no metered call was made",
        "instance": "urn:agentic:dispatch:9c8b7a65-0f1e-4d2c-8b3a-5e6f70819203",
        "dispatch_id": "9c8b7a65-0f1e-4d2c-8b3a-5e6f70819203",
        "stop_reason": "policy_denied",
        "rule_id": "egress.allowlist.requires_human_actor",
        "retryable": false,
        "correlation": { "run_id": "run-schedule-0007", "root_dispatch_id": "9c8b7a65-0f1e-4d2c-8b3a-5e6f70819203", "depth": 0 }
      }
    }
  ]
}
```

What a caller does with it: branch on `type`, which is a member of the closed registry `cap-errors`
owns; use `retryable` as given rather than inferring it from the status; report `detail`, never parse
it. `rule_id` names the rule, so a refusal is answerable without reading prose. `xc-policy-gate`
owns the rule that this decision is recorded before the first metered call, which is why `usage`
does not appear at all: nothing was spent.

## What a swap leaves untouched

`seam-dispatch` carries this as an invariant and it is not repeated here: swapping what executes the
unit, adding a stop reason, tightening a ceiling or moving where the unit runs changes nothing in a
caller that reads `state`, `stop_reason`, `outputs`, `usage` and `problem`. If a caller of yours
would have to change when the executor changes, the field it depends on belongs to the adapter and
should not have been in the result.
