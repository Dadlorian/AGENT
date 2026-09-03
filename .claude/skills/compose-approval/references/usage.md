# compose-approval — worked usage

Long material for `compose-approval`. The skill body is enough to assemble a gate without this file.
Open it for the full schemas, one worked gate declaration per way in, and the worked rejections.

Everything here is **proposed**: it is our design expressed against the knowledge base, not a shape
PASS.md fixes. The caller doctrine these examples obey — the four entries of TARGET T6.2 through one
envelope, one result or one problem object, configuration rather than arguments — is stated once in
`cap-consumption` and is not restated here.

---

## 1. The three ways in (TARGET T1)

TARGET T1 lists three ways in: a human, an agent, an internal or external event. That is a different
enumeration from T6.2's four entries, which `cap-work-intake` and `cap-consumption` own. The gate is
reached the same way from all three: an entry envelope carries the work, the workflow reaches the
step that carries the gate, and the gate parks. The only thing that differs is who is named.

### 1.1 A human starts the work and a human decides (T1.1)

```json
{
  "entry": {
    "declared_by": "user:ops.lead",
    "intent": "Publish the 4.2.0 release once someone signs off on the diff",
    "workflow": "release@v7",
    "correlation_id": "corr-release-0007",
    "idempotency_key": "user-ops-lead-release-4-2-0",
    "budget": { "ceiling_micros": 4000000, "currency": "USD", "on_exceed": "terminate_unit" }
  },
  "gate_declared_on_step": {
    "gate_id": "gate-deploy-0007",
    "correlation_id": "corr-release-0007",
    "step_id": "publish-release",
    "view": "release-diff-summary",
    "decider": { "subject": "user:ops.lead", "wires": ["parked-item", "queued-inbox"] },
    "deadline_at": "2026-09-03T17:00:00Z",
    "outcomes": ["approve", "edit", "reject", "return_with_notes"],
    "return_to_step_id": "build-release-notes",
    "cost_contribution_micros": 0
  }
}
```

Minimal input: the four gate fields the schema marks required plus `decider` and `deadline_at`.
Minimal output: one `GateOutcome`, or one problem object. Nothing else is read back.

### 1.2 An agent starts the work and a human decides (T1.2)

```json
{
  "entry": {
    "declared_by": "agent:triage.bot",
    "intent": "Close finding SEC-118 in the auth surface",
    "workflow": "harden-service@v3",
    "correlation_id": "corr-harden-0912",
    "idempotency_key": "agent-triage-bot-sec-118",
    "budget": { "ceiling_micros": 28000000, "currency": "USD", "on_exceed": "terminate_unit" }
  },
  "gate_declared_on_step": {
    "gate_id": "gate-harden-0912",
    "correlation_id": "corr-harden-0912",
    "step_id": "apply-patch",
    "view": "harden-summary",
    "decider": { "subject": "user:security.oncall", "wires": ["queued-inbox"] },
    "deadline_at": "2026-09-04T09:00:00Z",
    "outcomes": ["approve", "reject", "return_with_notes"],
    "return_to_step_id": "propose-patch"
  }
}
```

The starting actor and the deciding subject are different, and both are recorded. `edit` is left out
of `outcomes` here because the reviewer is not the author of the patch; a gate that offers `edit`
without giving the decider the artifact is the degradation `X-end-to-end-018` warns about.

### 1.3 An event or a schedule starts the work and a human decides (T1.3)

```json
{
  "entry": {
    "declared_by": "service:git.webhook",
    "on_behalf_of": "schedule:nightly.compliance",
    "intent": "Nightly compliance sweep, escalate anything that would change production",
    "workflow": "compliance-sweep@v2",
    "correlation_id": "corr-sweep-20260903",
    "idempotency_key": "git-webhook-9f2c1a-20260903",
    "budget": { "ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit" }
  },
  "gate_declared_on_step": {
    "gate_id": "gate-sweep-20260903",
    "correlation_id": "corr-sweep-20260903",
    "step_id": "apply-remediation",
    "view": "compliance-delta",
    "decider": { "subject": "user:compliance.duty", "wires": ["parked-item"] },
    "deadline_at": "2026-09-03T23:00:00Z",
    "outcomes": ["approve", "reject"],
    "cost_contribution_micros": 0
  }
}
```

Nobody is watching at 02:00. That is the case the queued wire exists for and the case an in-process
timer loses: the gate parks on a durable record, the deadline is an occurrence, and the decision is
delivered whenever the duty reviewer next opens the item.

---

## 2. The outcome, delivered

```json
{
  "gate_id": "gate-release-0007",
  "correlation_id": "corr-release-0007",
  "outcome": "return_with_notes",
  "actor": "user:ops.lead",
  "body": { "notes": "Version bump is right, changelog omits the migration step. Add it and re-open." },
  "idempotency_key": "gate-release-0007-user-ops-lead-01",
  "delivered_over": "queued-inbox"
}
```

Delivered ten times, this resumes the run once. The tenth delivery attaches to the first resume and
reads back its result. The same body under a different `idempotency_key` is a second decision on a
gate that is already closed, and is refused (section 3.2).

---

## 3. The rejections a caller handles

Every type below is a registered row of the closed registry in `docs/decomposition.md` section 2.1.6,
which `cap-errors` owns. This composition adds no new problem type.

### 3.1 Nobody decided before the deadline

```json
{
  "type": "urn:agentic:problem:deadline-exceeded",
  "title": "The gate closed before anyone decided",
  "status": 504,
  "detail": "gate-deploy-0007 on step publish-release opened at 2026-09-03T09:00:00Z with deadline 2026-09-03T17:00:00Z and closed undecided; decider user:ops.lead was asked over wire parked-item and wire queued-inbox.",
  "retryable": false,
  "correlation_id": "corr-release-0007",
  "instance": "urn:agentic:gate:gate-deploy-0007"
}
```

The deadline is a cap, not a stop: the run terminates as a failure that escalates. A decision
presented afterwards is a no-op, so `retryable` is false on the gate that closed and the remedy is a
new run.

### 3.2 The same key, a different decision

```json
{
  "type": "urn:agentic:problem:idempotency-conflict",
  "title": "Same idempotency key, different outcome body",
  "status": 409,
  "detail": "gate-release-0007-user-ops-lead-01 was first seen with outcome approve and is now presented with outcome reject.",
  "retryable": false,
  "correlation_id": "corr-release-0007"
}
```

### 3.3 A subject the gate did not name, or a wire it did not list

```json
{
  "type": "urn:agentic:problem:policy-denied",
  "title": "Not a decider for this gate",
  "status": 403,
  "detail": "gate-harden-0912 names decider user:security.oncall over wire queued-inbox; the outcome was presented by user:intern.a over wire parked-item.",
  "retryable": false,
  "rule_id": "gate.decider.subject-and-wire",
  "correlation_id": "corr-harden-0912"
}
```

A scope refusal is `policy-denied` with a `rule_id`; it is not a new type.

### 3.4 An outcome body that does not fit the gate's response schema

```json
{
  "type": "urn:agentic:problem:document-invalid",
  "title": "Outcome body failed validation",
  "status": 422,
  "detail": "gate-release-0007 requires notes when outcome is return_with_notes; body has no notes member.",
  "retryable": false,
  "correlation_id": "corr-release-0007"
}
```

---

## 4. The full schemas

### 4.1 ApprovalGate

The summary shape in the skill body carries the required members. The full document adds the members
a resolver and an auditor need and nothing a caller must write.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:approval-gate:0.1",
  "title": "ApprovalGate",
  "type": "object",
  "additionalProperties": false,
  "required": ["gate_id", "correlation_id", "step_id", "view", "decider", "deadline_at", "outcomes"],
  "properties": {
    "gate_id": { "type": "string", "minLength": 1 },
    "correlation_id": { "type": "string", "minLength": 1 },
    "root_dispatch_id": { "type": "string", "format": "uuid" },
    "step_id": { "type": "string", "minLength": 1 },
    "view": { "type": "string", "minLength": 1 },
    "view_digest": { "type": "string", "description": "Digest of what the decider was actually shown, recorded so a decision is attributable to a view." },
    "decider": {
      "type": "object",
      "additionalProperties": false,
      "required": ["subject", "wires"],
      "properties": {
        "subject": { "type": "string", "pattern": "^(user|agent|service|schedule):[a-z0-9][a-z0-9._@-]*$" },
        "wires": { "type": "array", "minItems": 1, "items": { "type": "string" } },
        "resolved_from": { "enum": ["root_run_owner", "step_override", "policy_decision"] }
      }
    },
    "deadline_at": { "type": "string", "format": "date-time" },
    "on_deadline": { "const": "escalate", "description": "A const, not an enum: the deadline is a cap and not a stop, so a caller cannot choose to expire into success." },
    "outcomes": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": { "enum": ["approve", "edit", "reject", "return_with_notes"] }
    },
    "return_to_step_id": { "type": "string" },
    "response_schema": { "type": "object" },
    "irreversibility": { "enum": ["reversible", "compensatable", "irreversible"] },
    "cost_contribution_micros": { "type": "integer", "minimum": 0 },
    "depth": { "type": "integer", "minimum": 0, "description": "Checked against the plan's depth bound at resolve time, never at run time." },
    "parked_at": { "type": "string", "format": "date-time" },
    "parked_at_head": { "type": "string", "description": "The state head at which the gate record became durable." },
    "state": { "enum": ["declared", "parked", "decided", "expired"] }
  },
  "allOf": [
    {
      "if": { "properties": { "outcomes": { "contains": { "const": "return_with_notes" } } } },
      "then": { "required": ["return_to_step_id"] }
    }
  ]
}
```

### 4.2 GateOutcome

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:gate-outcome:0.1",
  "title": "GateOutcome",
  "type": "object",
  "additionalProperties": false,
  "required": ["gate_id", "correlation_id", "outcome", "actor", "idempotency_key"],
  "properties": {
    "gate_id": { "type": "string", "minLength": 1 },
    "correlation_id": { "type": "string", "minLength": 1 },
    "outcome": { "enum": ["approve", "edit", "reject", "return_with_notes"] },
    "actor": { "type": "string", "pattern": "^(user|agent|service|schedule):[a-z0-9][a-z0-9._@-]*$" },
    "delegation_hop": {
      "type": "object",
      "additionalProperties": false,
      "required": ["actor", "obtained_via"],
      "properties": {
        "actor": { "type": "string" },
        "obtained_via": { "enum": ["rfc8693_token_exchange", "workload_attestation", "direct"] }
      },
      "description": "The hop appended to the run's chain by the act of deciding."
    },
    "body": { "type": "object" },
    "view_digest": { "type": "string", "description": "What the decider says they were shown. Compared against the gate's own view_digest." },
    "idempotency_key": { "type": "string", "minLength": 8 },
    "delivered_over": { "type": "string" },
    "delivered_at": { "type": "string", "format": "date-time" }
  },
  "allOf": [
    {
      "if": { "properties": { "outcome": { "enum": ["edit", "reject", "return_with_notes"] } }, "required": ["outcome"] },
      "then": { "required": ["body"] }
    }
  ]
}
```

---

## 5. What a conformance fixture has to contain

Five cases, because four of them can pass while the fifth is entirely missing:

| Case | What it delivers | What it proves |
|---|---|---|
| approve | one outcome, ten times | `resumes_per_gate == 1`, and the duplicate attaches |
| edit | a body that replaces the artifact | the run continues with the reviewer's body, not the proposal |
| reject | a body carrying notes | the run terminates as a failure that escalates |
| return | notes plus a re-entry | the named step runs again with a fresh gate id |
| expire | nothing, then a decision after the close | `deadline-exceeded` returned, `late_decisions_applied == 0` |

Assert `gates_parked` and `views_missing` **before** any of the five: a suite in which no gate ever
parked passes every duplicate assertion, which is the structurally-green failure `F-a7-03` records.
