# Using a bounded loop

Long material for `compose-loop`. The skill body is enough to write a conformant loop; this file
carries the full schema, one worked declaration for each of TARGET T1's three ways in, and the two
worked rejections. Everything here is **proposed**: field names follow the loop operator in
`examples/end-to-end/schemas/workflow.schema.json` and the entry envelope in
`examples/end-to-end/schemas/entry.schema.json` so a reader can run the nearest thing that exists.

## 1. The full loop-spec

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:loop:spec:0.1",
  "title": "LoopSpec",
  "type": "object",
  "additionalProperties": false,
  "required": ["op", "id", "max_iterations", "exit_when", "body", "on_cap"],
  "properties": {
    "op":   { "const": "loop" },
    "id":   { "type": "string", "pattern": "^[a-z0-9][a-z0-9-]{1,47}$" },
    "max_iterations": { "type": "integer", "minimum": 1, "maximum": 25 },
    "exit_when": {
      "type": "object", "additionalProperties": false,
      "required": ["judge_step", "verdict"],
      "properties": {
        "judge_step": { "type": "string", "description": "The grading step inside the body." },
        "verdict":    { "enum": ["pass", "fail"] }
      }
    },
    "body": { "type": "object", "description": "One step of the closed operator set." },
    "on_cap": { "const": "escalate" },
    "per_iteration_ceiling_micros": { "type": "integer", "minimum": 0 },
    "max_depth": { "type": "integer", "minimum": 1, "default": 3 },
    "carry_forward": {
      "type": "object", "additionalProperties": false,
      "description": "What one iteration hands the next. Bounded on purpose.",
      "properties": {
        "verdict":          { "const": true },
        "failed_check_ids": { "const": true },
        "result_digest":    { "const": true },
        "window":           { "type": "integer", "minimum": 1, "default": 1,
                              "description": "How many prior iterations' digests travel." }
      }
    }
  }
}
```

`carry_forward` has no member for the criterion, the sampled checks or the criterion-set digest.
That absence is the point: there is nowhere to put them, so nobody has to remember not to.

## 2. One loop, three ways in

The loop is declared once, inside the workflow the intent points at. What differs per entry is the
envelope; the loop-spec is byte-identical in all three.

```json
{ "op": "loop", "id": "fix-loop", "max_iterations": 3, "on_cap": "escalate",
  "exit_when": { "judge_step": "fix-judge", "verdict": "pass" },
  "per_iteration_ceiling_micros": 200000, "max_depth": 3,
  "body": { "op": "sequence", "id": "attempt", "steps": [
    { "op": "agent", "id": "fix", "agent": "code-fixer", "input_from": ["repro", "fix-judge"],
      "task": "Edit only the named files until the failing test passes." },
    { "op": "judge", "id": "fix-judge", "of": "fix", "criterion_ref": "criterion://fix-acceptable/v1" }
  ] } }
```

### A human enters (TARGET T1.1)

```json
{ "envelope_version": "0.1", "kind": "human", "entry_id": "human-checkout-500s",
  "actor": { "subject": "user:corey",
             "delegation_chain": [ { "actor": "user:corey", "obtained_via": "direct" } ] },
  "intent": { "workflow_ref": "workflows/triage-and-fix.json",
              "summary": "Checkout 500s on coupon apply; find it and fix it." },
  "correlation": { "run_id": "run-human-0001", "correlation_id": "corr-human-0001", "depth": 0 },
  "budget": { "ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit" },
  "idempotency_key": "human-checkout-500s-2026-09-03",
  "payload": { "report_text": "POST /checkout/coupon returns 500." } }
```

Back: `{"loop_id":"fix-loop","terminated_by":"verdict_pass","termination_class":"stop",
"iterations_run":2,"cost_micros":317400}` plus the result of the last `fix` step.

### An agent enters (TARGET T1.2)

```json
{ "envelope_version": "0.1", "kind": "external", "entry_id": "ext-partner-sre-4471",
  "actor": { "subject": "agent:partner-sre-bot",
             "delegation_chain": [ { "actor": "agent:partner-sre-bot", "obtained_via": "workload_attestation" },
                                   { "actor": "service:intake", "obtained_via": "token_exchange" },
                                   { "actor": "user:corey", "obtained_via": "token_exchange" } ] },
  "intent": { "workflow_ref": "workflows/triage-and-fix.json", "summary": "Partner-filed fault." },
  "correlation": { "run_id": "run-ext-0001", "correlation_id": "corr-ext-0001",
                   "parent_correlation_id": "corr-partner-88", "depth": 1 },
  "budget": { "ceiling_micros": 600000, "currency": "USD", "on_exceed": "terminate_unit" },
  "idempotency_key": "partner-sre-4471", "payload": { "report_text": "5xx on /checkout/coupon" } }
```

The loop is the same; the ceiling is smaller and `depth: 1` counts against `max_depth`, so a loop
nested inside this one resolves against a bound that is already one level down.

### An event enters (TARGET T1.3)

```json
{ "envelope_version": "0.1", "kind": "schedule", "entry_id": "schedule-nightly-fault-sweep",
  "actor": { "subject": "schedule:nightly-fault-sweep",
             "delegation_chain": [ { "actor": "schedule:nightly-fault-sweep", "obtained_via": "workload_attestation" },
                                   { "actor": "user:corey", "obtained_via": "token_exchange" } ] },
  "intent": { "workflow_ref": "workflows/triage-and-fix.json", "summary": "Nightly sweep." },
  "correlation": { "run_id": "run-schedule-0001", "correlation_id": "corr-schedule-0001", "depth": 0 },
  "budget": { "ceiling_micros": 400000, "currency": "USD", "on_exceed": "terminate_unit" },
  "idempotency_key": "nightly-fault-sweep-2026-09-03",
  "payload": { "recurrence": "FREQ=DAILY;BYHOUR=2;BYMINUTE=0" } }
```

An internal producer - `service:alerting` - enters the same way with `kind: "event"`. What it may
not do is emit an entry from inside a running iteration: internal results steer, they never start.

## 3. Two worked rejections

### The budget ceiling (registered type)

```json
{ "type": "urn:agentic:problem:budget-exhausted",
  "title": "Budget exhausted",
  "status": 402,
  "detail": "loop fix-loop iteration 3 would draw 200000 micros against 118300 remaining on run-schedule-0001",
  "retryable": false,
  "correlation": { "run_id": "run-schedule-0001", "correlation_id": "corr-schedule-0001", "depth": 0 },
  "loop_outcome": { "loop_id": "fix-loop", "terminated_by": "budget_ceiling",
                    "termination_class": "cap", "iterations_run": 2, "cost_micros": 381700 } }
```

### The iteration ceiling (proposed type, pending registration)

The suffix `iteration-ceiling-reached` is **proposed and pending registration**: it has no row in the
closed registry in `docs/decomposition.md` section 2.1.6. Until that row lands, the platform returns
the registered `urn:agentic:problem:deadline-exceeded` with the same `loop_outcome` attached, and
this skill's first open question carries the row it would add.

```json
{ "type": "urn:agentic:problem:iteration-ceiling-reached",
  "title": "Iteration ceiling reached without a pass verdict",
  "status": 504,
  "detail": "loop fix-loop ran 3 of 3 iterations; last verdict fail on checks patch-applies, test-passes",
  "retryable": false,
  "correlation": { "run_id": "run-human-0001", "correlation_id": "corr-human-0001", "depth": 0 },
  "loop_outcome": { "loop_id": "fix-loop", "terminated_by": "iteration_ceiling",
                    "termination_class": "cap", "iterations_run": 3, "cost_micros": 594100 } }
```

Both are caps, and both go to a human. Neither is a result: a caller that renders either as a
completed run has collapsed stop and cap, which is the failure this skill exists to prevent.
