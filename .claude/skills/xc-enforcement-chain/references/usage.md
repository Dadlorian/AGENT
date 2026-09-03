# xc-enforcement-chain — long material

Proposed throughout unless a knowledge-base id is given. The skill body is enough to judge a chain
and to place an enforcement point; this file carries only what did not fit the progressive-disclosure
budget: the full shapes, the three complete worked entries, the worked refusal, and the slot table.

## 1. The slot table: who owns what

The chain owns the order and the totality. Each slot's semantics belong to the skill named here, and
this file states no rule those skills own.

| Order | Slot | Inverse on exit | Owning skill | Concern (PASS.md B4) |
|---|---|---|---|---|
| 1 | `identity.resolve` | `identity.release` | `xc-identity-delegation` | `E-concern-identity` (`F-b4-03`) |
| 2 | `policy.decide` | `policy.record_outcome` | `xc-policy-gate` | `E-concern-policy` (`F-b4-04`) |
| 3 | `budget.reserve` | `budget.reconcile` | `xc-budget` | `E-concern-budget` (`F-b4-02`) |
| 4 | `telemetry.open` | `telemetry.close` | `xc-correlation` | `E-concern-telemetry` (`F-b4-06`) |
| 5 | `idempotency.claim` | `idempotency.settle` | `xc-idempotency-lease` | `E-concern-idempotency` (`F-b4-08`) |
| 6 | `provenance.open` | `provenance.seal` | `xc-provenance-chain` | `E-concern-provenance` (`F-b4-05`) |

The seventh concern, Errors (`E-concern-errors`, `F-b4-07`), is not a slot. It is the shape every
slot's refusal takes, owned by `xc-typed-errors`, which is why the chain has one return type.

## 2. Full chain-context and slot record

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:enforcement-chain:context:0.1-full",
  "title": "ChainContextFull",
  "type": "object",
  "additionalProperties": false,
  "required": ["point", "unit_id", "correlation", "slots", "entered_seq", "chain_version"],
  "properties": {
    "point": { "enum": ["admission", "dispatch", "call"] },
    "unit_id": { "type": "string", "format": "uuid" },
    "parent_context_id": {
      "type": "string",
      "description": "The chain context of the enclosing point. A call point's context names its dispatch point's context, so a traversal is reconstructable without walking a trace tree (see xc-correlation)."
    },
    "chain_version": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest of the declared slot list and order in force for this traversal. Two units that disagree here were chained by different platforms."
    },
    "entered_seq": { "type": "integer", "minimum": 0 },
    "exited_seq": { "type": "integer", "minimum": 0 },
    "correlation": {
      "type": "object",
      "required": ["run_id", "root_dispatch_id"],
      "properties": {
        "run_id": { "type": "string" },
        "root_dispatch_id": { "type": "string" },
        "depth": { "type": "integer", "minimum": 0 }
      }
    },
    "slots": {
      "type": "array",
      "minItems": 6,
      "maxItems": 6,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["slot", "seq", "outcome"],
        "properties": {
          "slot": {
            "enum": ["identity.resolve", "policy.decide", "budget.reserve",
                     "telemetry.open", "idempotency.claim", "provenance.open"]
          },
          "seq": { "type": "integer", "minimum": 0 },
          "outcome": { "enum": ["passed", "no-op", "refused"] },
          "handle": {
            "type": "string",
            "description": "Opaque handle the owning skill returns: an admission token, a reservation lease, a span id, a claim id. The chain stores it and never interprets it."
          },
          "inverse_seq": { "type": "integer", "minimum": 0 },
          "inverse_outcome": { "enum": ["done", "no-op", "failed"] }
        }
      }
    }
  }
}
```

Two rules the shape encodes. First, `maxItems: 6` as well as `minItems: 6`: a chain that grew a
seventh slot at one point is not the same chain, and `chain_version` is what makes that detectable.
Second, there is no `skipped` outcome and no `bypass` member — a slot the platform declared a no-op
for a point records `no-op` and is still counted by the attestation.

## 3. The three ways in, complete (TARGET T1: `T-t1-01`, `T-t1-02`, `T-t1-03`)

The caller-side doctrine — one envelope, one result or one problem — is stated once in
`cap-consumption` and is not restated here. What these show is that none of the three supplies
anything chain-shaped, and all three produce the same six slots in the same order.

### 3.1 A human (`T-t1-01`)

```json
{
  "entry": {
    "kind": "human",
    "actor": { "subject": "user:corey", "delegation_chain": [ { "actor": "user:corey", "obtained_via": "direct" } ] },
    "intent": "roll back the failed deploy on the staging fleet",
    "correlation": { "run_id": "run-h-0001", "root_dispatch_id": "disp-h-0001", "depth": 0 },
    "budget": { "ceiling_micros": 2000000, "on_exceed": "stop" },
    "idempotency_key": "ui-corey-2026-09-03T09:14:22Z-01"
  },
  "chain_context": {
    "point": "admission",
    "unit_id": "disp-h-0001",
    "chain_version": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "entered_seq": 3,
    "correlation": { "run_id": "run-h-0001", "root_dispatch_id": "disp-h-0001", "depth": 0 },
    "slots": [
      { "slot": "identity.resolve",   "seq": 4, "outcome": "passed", "inverse_seq": 41 },
      { "slot": "policy.decide",      "seq": 5, "outcome": "passed", "inverse_seq": 40 },
      { "slot": "budget.reserve",     "seq": 6, "outcome": "passed", "inverse_seq": 39 },
      { "slot": "telemetry.open",     "seq": 7, "outcome": "passed", "inverse_seq": 38 },
      { "slot": "idempotency.claim",  "seq": 8, "outcome": "passed", "inverse_seq": 37 },
      { "slot": "provenance.open",    "seq": 9, "outcome": "passed", "inverse_seq": 36 }
    ]
  }
}
```

### 3.2 An agent (`T-t1-02`)

```json
{
  "entry": {
    "kind": "external",
    "actor": {
      "subject": "agent:partner-sre-bot",
      "delegation_chain": [
        { "actor": "service:partner-gateway", "obtained_via": "workload_attestation" },
        { "actor": "agent:partner-sre-bot", "obtained_via": "rfc8693_token_exchange" }
      ]
    },
    "intent": "open a remediation run for incident INC-4417",
    "correlation": { "run_id": "run-a-0001", "root_dispatch_id": "disp-a-0001", "depth": 0 },
    "budget": { "ceiling_micros": 500000, "on_exceed": "stop" },
    "idempotency_key": "partner-sre-bot/INC-4417/1"
  },
  "chain_context": {
    "point": "admission",
    "unit_id": "disp-a-0001",
    "entered_seq": 2,
    "slots": [
      { "slot": "identity.resolve",   "seq": 3, "outcome": "passed", "inverse_seq": 22 },
      { "slot": "policy.decide",      "seq": 4, "outcome": "passed", "inverse_seq": 21 },
      { "slot": "budget.reserve",     "seq": 5, "outcome": "passed", "inverse_seq": 20 },
      { "slot": "telemetry.open",     "seq": 6, "outcome": "passed", "inverse_seq": 19 },
      { "slot": "idempotency.claim",  "seq": 7, "outcome": "passed", "inverse_seq": 18 },
      { "slot": "provenance.open",    "seq": 8, "outcome": "passed", "inverse_seq": 17 }
    ]
  }
}
```

The delegation chain is longer here and nothing else differs. That is the point: the door changed,
the chain did not.

### 3.3 An internal or external event (`T-t1-03`)

```json
{
  "entry": {
    "kind": "event",
    "actor": { "subject": "service:alerting", "delegation_chain": [ { "actor": "service:alerting", "obtained_via": "workload_attestation" } ] },
    "intent": "triage alert cpu-saturation on cell-14",
    "correlation": { "run_id": "run-e-0001", "root_dispatch_id": "disp-e-0001", "depth": 0 },
    "budget": { "ceiling_micros": 250000, "on_exceed": "stop" },
    "idempotency_key": "alerting/cpu-saturation/cell-14/2026-09-03T09:00Z"
  },
  "chain_context": {
    "point": "admission",
    "unit_id": "disp-e-0001",
    "entered_seq": 1,
    "slots": [
      { "slot": "identity.resolve",   "seq": 2, "outcome": "passed", "inverse_seq": 14 },
      { "slot": "policy.decide",      "seq": 3, "outcome": "passed", "inverse_seq": 13 },
      { "slot": "budget.reserve",     "seq": 4, "outcome": "passed", "inverse_seq": 12 },
      { "slot": "telemetry.open",     "seq": 5, "outcome": "passed", "inverse_seq": 11 },
      { "slot": "idempotency.claim",  "seq": 6, "outcome": "passed", "inverse_seq": 10 },
      { "slot": "provenance.open",    "seq": 7, "outcome": "passed", "inverse_seq": 9 }
    ]
  }
}
```

A schedule producer (`schedule:nightly-audit`) enters by the same door as the event producer and
differs only in its subject prefix; TARGET T6.2 counts it as a fourth entry, TARGET T1 counts three
ways in, and this file follows T1 because the chain is wired per door and not per clock.

## 4. The worked refusal, in full

The unit above (`disp-e-0001`) is admitted, dispatched, and then at depth 2 asks for a model call
that would cross the run's ceiling. The `budget.reserve` slot of the `call` point refuses. The type
is the registered `budget-exhausted` row of the closed registry in `docs/decomposition.md` section
2.1.6; `cap-errors` owns the object and `xc-typed-errors` owns the rule that it is never prose.

```json
{
  "type": "urn:agentic:problem:budget-exhausted",
  "title": "Budget exhausted",
  "status": 402,
  "detail": "enforcement point call, slot budget.reserve: the model call would cross the ceiling of run-e-0001",
  "instance": "urn:agentic:run:run-e-0001/call/17",
  "dispatch_id": "disp-e-0001",
  "stop_reason": "cap",
  "retryable": false,
  "correlation": { "run_id": "run-e-0001", "root_dispatch_id": "disp-e-0001", "depth": 2 }
}
```

What the object does not carry, and why:

- no engine, process or host that decided — a caller cannot act on it and a swap must be invisible;
- no criterion and no criterion text — design rule 6 (`F-b1-07`), stated in the skill body;
- no free-text remedy — `retryable` is a member, so nothing is inferred from the words or the status.

The chain context for that call point records `budget.reserve` with `outcome: "refused"`, the two
slots before it as `passed`, the three after it as absent from the entry pass — and every slot that
did run gets its inverse on the way out, because the exit runs on the failure path too.

## 5. Reading the attestation

`attest_chain` reports counts, not a boolean. The four that decide the definition of done:

| Count | Zero means | Non-zero names |
|---|---|---|
| `slots_missing` | every declared slot ran at every point | the point and slot that was absent |
| `out_of_order` | `seq` increased in the declared order | the unit and the inversion |
| `missing_inverse` | every slot that ran was unwound on exit | the units that leaked a reservation, claim or span |
| `ungated_metered_calls` | no call was reached without a chain context | the call sites that are off the chain |

Read them next to `metered_units` and `units_checked`. A corpus in which nothing spent prints four
zeros and proves nothing — the finding `agentic-stack` records as `F-a7-03`.
