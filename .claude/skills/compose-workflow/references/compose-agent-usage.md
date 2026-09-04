# Using an agent

Long material for `compose-agent`. The skill body is enough to declare and admit a conformant
agent unit; this file carries the full agent-profile schema, the full delegation-call shape, one
worked declaration for each of TARGET T1's three ways in, and two worked rejections. Everything
here is **proposed**: field names follow `examples/end-to-end/schemas/agent-profile.schema.json`,
`examples/end-to-end/agents.json` and the entry envelope in
`examples/end-to-end/schemas/entry.schema.json` so a reader can run the nearest thing that exists.

## 1. The full agent-profile schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:example:agent-profile:0.1",
  "title": "Agent profile registry",
  "type": "object",
  "additionalProperties": false,
  "required": ["registry_version", "agents"],
  "properties": {
    "registry_version": { "const": "0.1" },
    "agents": { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/profile" } }
  },
  "$defs": {
    "profile": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "good_at", "not_for", "model_class", "tools", "inputs", "outputs", "cost_class", "max_concurrency"],
      "properties": {
        "name":        { "type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,47}$" },
        "good_at":     { "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 20 },
                         "description": "Specific enough to route on: 'turns a stack trace into a failing-test command', not 'good at code'." },
        "not_for":     { "type": "string", "minLength": 10, "description": "The call that should go to a different profile." },
        "model_class": { "type": "string", "pattern": "^(f|i|b|cli)-[a-z0-9-]*$",
                         "description": "Routing class by prefix: f- free local GPU, i- interactive metered, b- asynchronous batch, cli- coding CLI as a model." },
        "tools":       { "type": "array", "items": { "type": "string" } },
        "inputs":      { "$ref": "#/$defs/shape" },
        "outputs":     { "$ref": "#/$defs/shape" },
        "cost_class":  { "enum": ["free", "low", "medium", "high"] },
        "max_concurrency": { "type": "integer", "minimum": 1, "maximum": 512 }
      }
    },
    "shape": {
      "type": "object",
      "additionalProperties": false,
      "required": ["required", "fields"],
      "properties": {
        "required": { "type": "array", "items": { "type": "string" } },
        "fields":   { "type": "object", "description": "field name to declared type: string, string[], integer, boolean, object" }
      }
    }
  }
}
```

## 2. The full delegation-call shape

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:agent:delegation-call:0.1",
  "title": "DelegationCall",
  "type": "object",
  "additionalProperties": false,
  "description": "Not an entry envelope: it reports into a run that already exists rather than minting one (REF-3-4-15).",
  "required": ["sub_agent", "task", "delegation_chain", "budget_slice_micros", "parent_correlation_id"],
  "properties": {
    "sub_agent": { "type": "string" },
    "task":      { "type": "string", "minLength": 1 },
    "delegation_chain": {
      "type": "array", "minItems": 2,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["actor", "obtained_via"],
        "properties": {
          "actor":       { "type": "string" },
          "obtained_via": { "enum": ["direct", "token_exchange", "workload_attestation"] }
        }
      },
      "description": "The parent's chain plus exactly one new hop for the sub-agent. Field names follow examples/end-to-end/schemas/entry.schema.json's actor.delegation_chain."
    },
    "budget_slice_micros":   { "type": "integer", "minimum": 0, "description": "Cut from the parent's remaining ceiling, never a fresh root ceiling." },
    "parent_correlation_id": { "type": "string", "minLength": 1 }
  }
}
```

## 3. One agent, three ways in

The agent step is declared once, inside the workflow the intent points at. What differs per entry
is the envelope; the step is byte-identical in all three, following the same pattern compose-loop's
reference file uses for a loop.

```json
{ "op": "agent", "id": "fix", "agent": "code-fixer", "input_from": ["repro", "fix-judge"],
  "task": "Edit only the named files until the failing test passes." }
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

Back: one turn result from `code-fixer` (`i-fast`... no - `cli-` class, per `agents.json`), reconciled
against the admission plan, plus `{"unit_id":"fix-0001","cost_micros":214300}`.

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

Inside this run, `triage-router` (`i-fast`) may itself call `delegate` to hand off to `code-fixer`
(`cli-`): the `DelegationCall` above carries `parent_correlation_id: "corr-ext-0001"`, a
`delegation_chain` with one new hop appended for `code-fixer`, and a `budget_slice_micros` cut from
whatever remains of the 600000-micros ceiling - never a fresh root.

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

An internal producer - `service:alerting` - enters the same way with `kind: "event"`. What none of
the three may do is call `declare_agent` from inside a running turn to mint a fresh root agent
invocation: a running unit's result may steer a later step, per REF-3-4-15, but it may not start one.

## 4. Two worked rejections

### An undeclared tool (registered type)

```json
{ "type": "urn:agentic:problem:policy-denied",
  "title": "Tool outside the unit's declared tool surface",
  "status": 403,
  "detail": "unit code-fixer-0007 requested run_shell, which is not in its declared tools [read_file, write_file, run_tests]",
  "retryable": false,
  "rule_id": "declared-tool-surface",
  "correlation": { "run_id": "run-human-0001", "correlation_id": "corr-human-0001", "depth": 0 } }
```

### A delegation that would exceed its slice (registered type)

```json
{ "type": "urn:agentic:problem:budget-exhausted",
  "title": "Budget exhausted",
  "status": 402,
  "detail": "delegate call from triage-router to code-fixer would draw 300000 micros against 118300 remaining on run-ext-0001",
  "retryable": false,
  "correlation": { "run_id": "run-ext-0001", "correlation_id": "corr-ext-0001", "parent_correlation_id": "corr-partner-88", "depth": 1 } }
```

Both are typed problem objects, never prose. Neither is a result: a caller that renders either as a
completed unit has let a refusal look like an answer, which is the failure this skill's not_exposed
section and its definition of done both exist to keep visible.
