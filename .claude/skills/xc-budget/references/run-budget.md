# Run budget: full shapes and worked instances

Proposed throughout unless a knowledge-base id is named. Open this file only when writing the schemas
themselves, the reservation lease, the cost record, or the worked declarations; the skill body is enough
to judge whether an implementation enforces the ceiling.

## 1. The full run-budget object

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:budget:run-budget:0.1",
  "title": "RunBudget",
  "type": "object",
  "additionalProperties": false,
  "required": ["ceiling_micros", "currency", "on_exceed", "max_delegation_depth", "max_fanout"],
  "properties": {
    "ceiling_micros": { "type": "integer", "minimum": 0,
                        "description": "One ceiling for the whole root unit of work (F-b4-02)." },
    "currency":       { "type": "string", "pattern": "^[A-Z]{3}$" },
    "token_ceiling":  { "type": "integer", "minimum": 0,
                        "description": "Optional second ceiling in tokens, for workloads priced per token." },
    "on_exceed":      { "const": "terminate_unit",
                        "description": "A const, not an enum. There is no opt-out to express (F-b4-01)." },
    "max_delegation_depth": { "type": "integer", "minimum": 1, "default": 3 },
    "max_fanout":           { "type": "integer", "minimum": 1, "default": 20 },
    "mid_run_outcome":      { "enum": ["continue", "narrow", "require_approval", "stop"], "default": "stop" },
    "warn_at_fraction":     { "type": "number", "minimum": 0, "maximum": 1, "default": 0.8,
                              "description": "Where mid_run_outcome is evaluated. Never a licence to pass zero." }
  }
}
```

## 2. The reservation lease

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:budget:reservation:0.1",
  "title": "BudgetReservation",
  "type": "object",
  "additionalProperties": false,
  "required": ["reservation_id", "root_run_id", "dispatch_id", "owner", "reserved_micros", "expires_at", "state"],
  "properties": {
    "reservation_id":   { "type": "string", "format": "uuid" },
    "root_run_id":      { "type": "string", "minLength": 1,
                          "description": "The root whose single ceiling this draws from, however deep the caller sits." },
    "dispatch_id":      { "type": "string", "format": "uuid" },
    "owner":            { "type": "string", "description": "Who holds the lease, so a dead holder is identifiable." },
    "reserved_micros":  { "type": "integer", "minimum": 0 },
    "actual_micros":    { "type": "integer", "minimum": 0,
                          "description": "Present once reconciled. Never copied from reserved_micros." },
    "expires_at":       { "type": "string", "format": "date-time",
                          "description": "The unit's deadline plus grace. An unreconciled reservation expires here rather than consuming the root's ceiling forever." },
    "state":            { "enum": ["held", "reconciled", "expired", "refused"] },
    "depth":            { "type": "integer", "minimum": 0 },
    "fanout_index":     { "type": "integer", "minimum": 0 }
  }
}
```

## 3. The cost record

The columns are those of a published cost-and-usage specification with split cost allocation
(X-end-to-end-047, X-end-to-end-048): a shared cost is split across the descendants that caused it rather
than attributed to whichever leaf happened to make the call. Version unverified: the records naming that
specification are search results, not pages that were read, so no version string is asserted here.

| Member | Meaning |
|---|---|
| `root_run_id` | The root whose ceiling was drawn from |
| `dispatch_id` | The descendant that spent |
| `billed_cost_micros` | What was charged |
| `effective_cost_micros` | What this descendant is allocated after a shared cost is split |
| `charge_category` | Usage, tax, credit, adjustment |
| `cost_status` | `committed` at submission, `reconciled` when the actual arrived |
| `recorded_at_head` | The state head the record was written at, so a reader can pin it |

## 4. Three ways in, one ceiling (TARGET T1)

The same ceiling object, declared by a human, by an agent, and by an event. Only `actor.subject` differs;
nothing downstream of intake branches on which of them produced it, which is what makes the guarantee
undeclinable rather than per-door. The fourth entry of TARGET T6.2, a schedule, is shown last: it is a
different enumeration from T1's three ways in, not a fourth way in.

```json
{
  "actor": { "subject": "user:corey", "delegation_chain": [{ "actor": "user:corey", "obtained_via": "direct" }] },
  "budget": { "ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit",
              "max_delegation_depth": 3, "max_fanout": 20 }
}
```

```json
{
  "actor": { "subject": "agent:partner-sre-bot",
             "delegation_chain": [{ "actor": "agent:partner-sre-bot", "obtained_via": "workload_attestation" },
                                  { "actor": "service:intake", "obtained_via": "token_exchange" }] },
  "budget": { "ceiling_micros": 400000, "currency": "USD", "on_exceed": "terminate_unit",
              "max_delegation_depth": 2, "max_fanout": 4 }
}
```

```json
{
  "actor": { "subject": "service:alerting",
             "delegation_chain": [{ "actor": "service:alerting", "obtained_via": "workload_attestation" }] },
  "budget": { "ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit",
              "max_delegation_depth": 3, "max_fanout": 20 }
}
```

```json
{
  "actor": { "subject": "schedule:nightly-fault-sweep",
             "delegation_chain": [{ "actor": "schedule:nightly-fault-sweep", "obtained_via": "workload_attestation" }] },
  "budget": { "ceiling_micros": 900000, "currency": "USD", "on_exceed": "terminate_unit",
              "max_delegation_depth": 3, "max_fanout": 8 }
}
```

## 5. The refusal, in full

`budget-exhausted` is a registered row of the closed type registry in docs/decomposition.md section 2.1.6.
This guarantee mints no type of its own.

```json
{
  "type": "urn:agentic:problem:budget-exhausted",
  "title": "Budget exhausted",
  "status": 402,
  "detail": "step fix#2 would draw 200200 micros against 118300 remaining on root run run-human-0001",
  "instance": "urn:agentic:dispatch:9f3c1b2e-2c0b-4d1a-9a55-1f9d2c7a8b41",
  "dispatch_id": "9f3c1b2e-2c0b-4d1a-9a55-1f9d2c7a8b41",
  "stop_reason": "budget_exhausted",
  "retryable": false,
  "correlation": { "run_id": "run-human-0001", "correlation_id": "corr-human-0001", "depth": 1 }
}
```

Two things it does not carry: the criterion the work would have been judged against (design rule 6,
F-b1-07), and any field a caller could set to make the next attempt exempt.
