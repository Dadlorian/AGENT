# xc-audit-trail: the full entry shape, the three ways in, and the rejection

Proposed throughout. The skill body is enough to judge whether a trail is attributable, queryable,
tamper-evident and retained; this file exists so that the shapes are not guessed and the caller
doctrine is not restated. `cap-consumption` owns that doctrine - the four entries of TARGET T6.2
through one envelope, one result or one problem object, configuration rather than a new argument -
and every example below follows it rather than describing it again.

## 1. The full audit entry

Proposed. The summary shape in the skill body carries the fields the monitor asserts on; this is the
whole record. Nothing here is a payload body, and nothing here is a grading criterion.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:audit-trail:entry:full:0.1",
  "title": "AuditEntryFull",
  "type": "object",
  "additionalProperties": false,
  "required": ["entry_id", "prev_entry_id", "chain_digest", "occurred_at", "actor",
               "delegation_chain", "action", "outcome", "correlation", "retention_class"],
  "properties": {
    "entry_id":       { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                        "description": "sha256 over the canonical bytes of the entry body." },
    "prev_entry_id":  { "type": ["string", "null"], "pattern": "^sha256:[0-9a-f]{64}$" },
    "chain_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "occurred_at":    { "type": "string", "format": "date-time" },
    "recorded_at":    { "type": "string", "format": "date-time",
                        "description": "When the platform wrote it. A wide gap between the two is itself reportable." },
    "actor":          { "type": "string", "pattern": "^(user|agent|service|schedule):" },
    "delegation_chain": {
      "type": "array", "minItems": 1, "items": { "type": "string" },
      "description": "Explicit hops, root workload identity last. xc-identity-delegation owns the shape and the acyclicity rule." },
    "action": {
      "type": "object", "additionalProperties": false,
      "required": ["kind"],
      "properties": {
        "kind":            { "type": "string", "description": "From a closed taxonomy, not free text." },
        "target_ref":      { "type": "string", "description": "What was acted on, by id or digest. Never the bytes." },
        "target_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
        "policy_decision": { "type": "object", "description": "The decision that admitted or refused the action, with its rule_id. xc-policy-gate owns it." },
        "cost_micros":     { "type": "integer", "minimum": 0 }
      }
    },
    "outcome":  { "enum": ["allowed", "denied", "succeeded", "failed"] },
    "problem":  { "type": "object", "description": "The typed problem object when outcome is denied or failed. cap-errors owns it." },
    "correlation": {
      "type": "object", "additionalProperties": false,
      "required": ["run_id", "root_dispatch_id", "correlation_id"],
      "properties": {
        "run_id":            { "type": "string" },
        "root_dispatch_id":  { "type": "string" },
        "correlation_id":    { "type": "string" }
      }
    },
    "code_version": { "type": "string" },
    "sealed_head":  { "type": "string", "description": "The sealed head this entry falls under; seam-state owns the sealing." },
    "retention_class": { "enum": ["chain", "body", "payload"] },
    "expires_at":      { "type": "string", "format": "date-time" },
    "hold":            { "type": "boolean", "default": false }
  }
}
```

## 2. One entry per way in

Proposed. TARGET T1 names three ways in - a human, an agent, an internal or external event - and the
claim being shown is that nothing in the entry, the query or the scan branches on which was used.
The three differ in the `actor` prefix and in nothing else.

```json
[
  {
    "entry_id": "sha256:1f0a4c2d9b7e5613a8c04f2e6d13b8a75c9e02f4a61d8b3c7e50f9a2d64b81c3",
    "prev_entry_id": "sha256:0a11c9f0d3b62e47a8c15d09f7b34e26c1d80a95f3e62b74c09d18a35b7e0f42",
    "chain_digest": "sha256:7c19a0b6e24f85d1c0378ae59b2f46071da8c3f9e50b27a4c86d10f35b7e92aa",
    "occurred_at": "2026-09-03T10:14:02Z",
    "actor": "user:corey",
    "delegation_chain": ["user:corey"],
    "action": { "kind": "document.declared", "target_ref": "doc-0091", "cost_micros": 0 },
    "outcome": "succeeded",
    "correlation": { "run_id": "run-human-0001", "root_dispatch_id": "disp-0001", "correlation_id": "corr-human-0001" },
    "sealed_head": "head:4b7e2c10",
    "retention_class": "body"
  },
  {
    "entry_id": "sha256:2b8e01c7d4a9f36502be7c1d8a0f45e93c26b7d1058fa9e3b47c02d16e8a5f70",
    "prev_entry_id": "sha256:1f0a4c2d9b7e5613a8c04f2e6d13b8a75c9e02f4a61d8b3c7e50f9a2d64b81c3",
    "chain_digest": "sha256:5d92c48b0e17a3f6c81de07b34a95f2c6e8017d4b93a0c5f2e64d18b70a9c3f5",
    "occurred_at": "2026-09-03T10:16:41Z",
    "actor": "agent:planner-01",
    "delegation_chain": ["agent:planner-01", "user:corey", "workload:dispatch-01"],
    "action": { "kind": "tool.called", "target_ref": "repo.write", "policy_decision": { "rule_id": "tool.write.allowed" }, "cost_micros": 1840 },
    "outcome": "allowed",
    "correlation": { "run_id": "run-agent-0042", "root_dispatch_id": "disp-0042", "correlation_id": "corr-agent-0042" },
    "sealed_head": "head:4b7e2c10",
    "retention_class": "body"
  },
  {
    "entry_id": "sha256:3c7d19a0b6e24f85d1c0378ae59b2f46071da8c3f9e50b27a4c86d10f35b7e92",
    "prev_entry_id": "sha256:2b8e01c7d4a9f36502be7c1d8a0f45e93c26b7d1058fa9e3b47c02d16e8a5f70",
    "chain_digest": "sha256:9c31b7d0e5a24f68c1de73f0a2b95c48d6e70a13f5c92b84d0e17a36c48b9f52",
    "occurred_at": "2026-09-03T10:19:08Z",
    "actor": "service:git-webhook",
    "delegation_chain": ["service:git-webhook", "workload:gateway-01"],
    "action": { "kind": "dispatch.submitted", "target_ref": "wf-review", "cost_micros": 0 },
    "outcome": "succeeded",
    "correlation": { "run_id": "run-event-0007", "root_dispatch_id": "disp-0007", "correlation_id": "corr-event-0007" },
    "sealed_head": "head:4b7e2c10",
    "retention_class": "body"
  }
]
```

The monitor is the fourth producer and the one this guarantee owns, entered from the clock rather
than from a request. Its own run is an entry like any other:

```json
{
  "entry_id": "sha256:4d80c1f5a92b63e07c4a18d3b7e0952c6f31da84095cb27e63d1a80f45c29e17",
  "occurred_at": "2026-09-04T02:00:00Z",
  "actor": "schedule:audit-monitor-daily",
  "delegation_chain": ["schedule:audit-monitor-daily", "workload:audit-monitor"],
  "action": { "kind": "audit.scanned", "target_ref": "head:4b7e2c10..head:9f21ad04" },
  "outcome": "succeeded",
  "correlation": { "run_id": "run-monitor-0114", "root_dispatch_id": "disp-0114", "correlation_id": "corr-monitor-0114" },
  "retention_class": "chain"
}
```

## 3. The minimal call, per way in

Proposed. Each is one call against the standard envelope `cap-consumption` fixes; none of them
mentions the audit trail when producing an entry, because nothing produces entries on request.

| Way in | What is written | What is read back |
|---|---|---|
| A human asks who did this | nothing; the human calls `trail` with a correlation id and a pinned head | the ordered entries for that run, each with actor and delegation chain |
| An agent acts | nothing the agent writes; the platform records the action it performed | the agent sees its own outcome, never the criterion, and never a way to edit the entry |
| An event enters | nothing the producer writes; the entry is derived from the dispatch the event caused | the producer's result, unchanged by the presence of the trail |
| The clock fires the monitor | the monitor report, appended to the trail it scanned | the counts in the report, or a typed problem document |

## 4. The worked rejection

Proposed. A scan that finds a broken chain returns an object, never prose. The suffix
`audit-chain-broken` is proposed and pending registration in the closed registry in
docs/decomposition.md section 2.1.6; until that row exists the scan returns the registered
`adapter-unavailable` row shown here and names the break in `detail`.

```json
{
  "type": "urn:agentic:problem:adapter-unavailable",
  "title": "Audit chain does not verify",
  "status": 503,
  "detail": "entry sha256:2b8e01c7d4a9f365... has chain_digest sha256:5d92c48b0e17a3f6... but recomputes to sha256:e004a71c8b2d55f9...; the window head:4b7e2c10..head:9f21ad04 is not verified and the store cannot be relied on to serve",
  "retryable": true,
  "retry_after_s": 0,
  "correlation": {
    "run_id": "run-monitor-0114",
    "root_dispatch_id": "disp-0114",
    "correlation_id": "corr-monitor-0114"
  }
}
```

`retryable` reads true because that is what the registered row carries; the break itself is not
retryable, which is the argument recorded in this skill's open question for adding a row.

## 5. What a reviewer asks, and which field answers it

| Question | Field |
|---|---|
| Who did this, and under whose authority? | `actor`, `delegation_chain` |
| Everything that happened in this run? | `correlation.run_id`, `correlation.correlation_id` |
| Was this record altered after the fact? | `chain_digest`, plus the inclusion proof against `sealed_head` |
| Can someone who distrusts us check it? | the signed sealed head, checked with a verifier we did not write |
| Is it still here after the retention period? | `retention_class`, `expires_at`, `hold` |
