# Policy gate: full shapes and worked entries

Proposed throughout. Open this only when writing the record schemas, the conformance report, or the
entry envelopes. The body of `xc-policy-gate` is enough to judge a placement and to wire the gate.

## 1. `policy-decided` record (full)

`policy-decided` is one of the record kinds in the append-only log (docs/decomposition.md 2.2.1).
The gate writes it *before* the admission token is returned, so the ordering is a fact on disk.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:record:policy-decided:0.1",
  "title": "PolicyDecidedRecord",
  "type": "object",
  "additionalProperties": false,
  "required": ["record_kind", "record_id", "prev_record_id", "seq", "run_id", "dispatch_id",
               "decision_point", "effect", "rule_id", "policy_version", "input_digest", "decided_at"],
  "properties": {
    "record_kind":    { "const": "policy-decided" },
    "record_id":      { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "prev_record_id": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "seq":            { "type": "integer", "minimum": 0,
                        "description": "Monotonic within the run partition. The ordering assertion prefers this to the clock." },
    "run_id":         { "type": "string" },
    "dispatch_id":    { "type": "string", "format": "uuid" },
    "decision_point": { "type": "string", "minLength": 1 },
    "effect":         { "enum": ["allow", "deny"] },
    "rule_id":        { "type": "string", "minLength": 1,
                        "description": "Required for allow as well as deny: an unattributed admission is as unanswerable as an unattributed refusal." },
    "policy_version": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "input_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "decided_at":     { "type": "string", "format": "date-time" },
    "problem":        { "$ref": "urn:agentic:problem:0.1",
                        "description": "Required when effect is deny. cap-errors owns the object and the closed type registry." }
  },
  "allOf": [
    { "if": { "properties": { "effect": { "const": "deny" } }, "required": ["effect"] },
      "then": { "required": ["problem"] } }
  ]
}
```

## 2. Gate conformance report (the fields the definition of done asserts on)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:policy-gate:conformance-report:0.1",
  "title": "PolicyGateConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": ["placement", "dispatches_checked", "metered_dispatches", "denied",
               "missing_decision", "inversions", "spend_delta_micros_on_denied"],
  "properties": {
    "placement":                    { "type": "string", "description": "The entity id of the gate placement under test. Read from the refusal that came back, never from the binding that selected it." },
    "dispatches_checked":           { "type": "integer", "minimum": 0 },
    "metered_dispatches":           { "type": "integer", "minimum": 0, "description": "Dispatches that reached at least one metered call. A zero here makes an inversion count of zero meaningless." },
    "denied":                       { "type": "integer", "minimum": 0 },
    "missing_decision":             { "type": "integer", "minimum": 0, "description": "Dispatches with no policy-decided record at all. Distinct from an inversion: the decision was never taken, not taken late." },
    "inversions":                   { "type": "integer", "minimum": 0 },
    "min_interval_ms":              { "type": "integer", "description": "Smallest gap between a decision and the first metered call. Negative means an inversion." },
    "spend_delta_micros_on_denied": { "type": "integer", "minimum": 0 },
    "ways_in_covered":              { "type": "array", "items": { "enum": ["human", "agent", "event"] },
                                      "description": "TARGET T1's three ways in. A run that covered fewer has not shown the gate is undeclinable by choosing another door." },
    "placements_run":               { "type": "integer", "minimum": 0 }
  }
}
```

## 3. The three ways in, in full

TARGET T1 names three: a human, an agent, and an internal or external event. The entry envelopes
below are the ones in `examples/end-to-end/entries/`, abbreviated to the fields the gate reads. The
point of showing all three is that the gate reads the same two fields in every case, and returns the
same admission token shape.

### A human enters

```json
{ "kind": "human",
  "actor": { "subject": "user:corey",
             "delegation_chain": [{ "actor": "user:corey", "obtained_via": "direct" }] },
  "correlation": { "run_id": "run-human-0001", "root_dispatch_id": "disp-human-0001", "depth": 0 } }
```

```json
{ "dispatch_id": "disp-human-0001", "decision_point": "dispatch.admit", "effect": "allow",
  "rule_id": "allow-owner-repo-write", "policy_version": "sha256:0f2c...", "decided_seq": 4 }
```

### An agent enters

```json
{ "kind": "external",
  "actor": { "subject": "agent:partner-sre-bot",
             "delegation_chain": [{ "actor": "agent:partner-sre-bot", "obtained_via": "workload_attestation" },
                                  { "actor": "service:intake", "obtained_via": "token_exchange" },
                                  { "actor": "user:corey", "obtained_via": "direct" }] },
  "correlation": { "run_id": "run-external-0001", "root_dispatch_id": "disp-external-0001", "depth": 1 } }
```

```json
{ "dispatch_id": "disp-external-0001", "decision_point": "dispatch.admit", "effect": "allow",
  "rule_id": "allow-partner-read-only", "policy_version": "sha256:0f2c...", "decided_seq": 3 }
```

### An event enters

```json
{ "kind": "event",
  "actor": { "subject": "service:alerting",
             "delegation_chain": [{ "actor": "service:alerting", "obtained_via": "workload_attestation" },
                                  { "actor": "service:intake", "obtained_via": "token_exchange" }] },
  "correlation": { "run_id": "run-event-0001", "root_dispatch_id": "disp-event-0001", "depth": 0 } }
```

A schedule enters with `"subject": "schedule:nightly-dependency-audit"` and is the same case: the
gate reads the actor and the correlation, and nothing else about how the work arrived.

### The same event, refused

```json
{ "type": "urn:agentic:problem:policy-denied",
  "title": "Policy denied",
  "status": 403,
  "detail": "decision point dispatch.admit refused disp-event-0001: egress to an unapproved host is not permitted for this actor",
  "dispatch_id": "disp-event-0001",
  "rule_id": "deny-egress-unapproved-host",
  "retryable": false,
  "correlation": { "run_id": "run-event-0001", "root_dispatch_id": "disp-event-0001", "depth": 0 } }
```

`urn:agentic:problem:policy-denied` is a registered row of the closed registry in
docs/decomposition.md section 2.1.6 (403, not retryable, carries `rule_id`). The gate mints no
type of its own. The spend ledger delta for `disp-event-0001` is exactly `0`, because the refusal
arrived before the first metered call rather than after it.

## 4. What the ordering assertion actually compares

For each dispatch, take the `policy-decided` record `(decided_at, seq)` and the first metered call
`(started_at, seq)` in the same run partition. Compare `seq` first and fall back to the timestamp
only across partitions; a coarse clock will produce ties, and a tie read as "precedes" is how an
inversion hides. A dispatch with no `policy-decided` record is `missing_decision`, not an inversion:
the two failures have different causes and conflating them makes the breakage unreadable.
