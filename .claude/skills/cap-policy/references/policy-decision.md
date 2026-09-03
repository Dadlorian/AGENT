# Policy decision: full schemas, registry format, engine criteria

Proposed material. The skill body is enough to judge an implementation without this file; open it when
you need the complete shapes, the decision-point registry format, or the criteria table for selecting an
engine. Every claim here is proposed unless it names a kb id.

## 1. Full DecisionRequest (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:request:0.1",
  "title": "DecisionRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["decision_point", "subject", "action", "resource", "context", "policy_version"],
  "properties": {
    "decision_point": {
      "type": "string",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$",
      "description": "A registered decision point. Unregistered names are refused, never defaulted to allow."
    },
    "subject": {
      "type": "object",
      "required": ["actor"],
      "properties": {
        "actor": { "type": "string", "description": "Workload or human identity. cap-identity owns the shape." },
        "delegation_chain": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Innermost last. Length >= 2 for a delegated action."
        }
      },
      "description": "Who is asking. This capability reads it; it does not verify it."
    },
    "action": { "type": "string", "description": "What is being attempted, from the decision point's declared verb set." },
    "resource": { "type": "object", "description": "What is acted on. Validated against the decision point's declared schema first." },
    "context": {
      "type": "object",
      "required": ["run_id", "root_dispatch_id"],
      "additionalProperties": true,
      "properties": {
        "run_id": { "type": "string" },
        "root_dispatch_id": { "type": "string" },
        "budget_remaining_micros": { "type": "integer", "minimum": 0 }
      },
      "description": "Correlation fields are stamped by the platform, not supplied by the caller."
    },
    "policy_version": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest of the activated bundle. A request without it cannot be replayed and is refused."
    }
  }
}
```

## 2. Full Decision (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:decision:0.1",
  "title": "Decision",
  "type": "object",
  "additionalProperties": false,
  "required": ["effect", "rule_id", "policy_version", "decision_point", "input_digest", "decided_at"],
  "properties": {
    "effect": { "enum": ["allow", "deny"] },
    "rule_id": { "type": "string", "minLength": 1 },
    "policy_version": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "decision_point": { "type": "string" },
    "input_digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "decided_at": { "type": "string", "format": "date-time" },
    "evaluation_micros": { "type": "integer", "minimum": 0, "description": "Cost of deciding, not of the work decided about." },
    "problem": { "$ref": "urn:agentic:problem:0.1", "description": "Required when effect is deny; shape owned by cap-errors." }
  },
  "allOf": [
    { "if": { "properties": { "effect": { "const": "deny" } }, "required": ["effect"] },
      "then": { "required": ["problem"] } }
  ]
}
```

## 3. Decision-point registry (proposed)

One row per place a decision is taken. A request naming a point absent from this table is a conformance
failure of the caller, answered with the registered `document-invalid` problem type rather than with a deny,
because a missing registration is a build error and a deny would hide it.

| Decision point | Subject | Action verbs | Resource shape | Consulted at |
|---|---|---|---|---|
| `dispatch-admit` | the entry's actor | `submit` | the entry envelope | before the plan is priced |
| `tool-invoke` | the executing unit | `call` | tool name plus the actual arguments | immediately before each tool call |
| `model-call` | the executing unit | `complete`, `embed` | model class and estimated cost | before each metered call |
| `state-append` | the writing component | `append` | record kind and subject | before the record is sealed |
| `artifact-export` | the run's actor | `export` | artifact digest and destination class | before bytes leave the platform |

The registry is closed at authoring time and extended only by adding a row, the same rule cap-errors applies
to its problem-type registry.

## 4. Criteria for judging a candidate engine (proposed)

Ordered. The first two are the contract from `F-b4-04` and are pass/fail; the rest are comparisons.

| # | Criterion | How it is checked | Failing it means |
|---|---|---|---|
| 1 | Decisions are deterministic under a pinned bundle | Evaluate the same request 1000 times; require one distinct `(effect, rule_id)` | Not usable, whatever else it offers |
| 2 | Consultable before resource consumption begins | The decision can be taken with no result and no spend in the request | Not usable; the engine can only report |
| 3 | Decision names a rule | The engine can return a stable identifier for the rule that decided, for allow as well as deny | Row P10's `rule_id` assertion is unsatisfiable |
| 4 | Bundle is content-addressable | Activation takes a digest and decisions can name it | Replay and audit become approximate |
| 5 | Evaluation cost is bounded | Worst-case evaluation time over the registry's largest input is measured, not assumed | Policy becomes a latency source on every call |
| 6 | Serves the whole registry | Every decision point in section 3 is expressible | The pair proves nothing; one engine is load-bearing |

## 5. What this file deliberately does not contain

- Where a decision is consulted, and the rule that it must precede the first metered call. That is
  `xc-policy-gate`, and `F-a6-04` records what happens when the two are treated as one thing.
- The failure shape. `cap-errors` owns it and the `policy-denied` row of its registry.
- Product configuration of either engine. `cap-policy-implement` carries the adapter detail.
