# Decomposition strategy for PASS.md Part B

Scope: this document answers PASS.md Part C items 1 through 5. It fixes which skills exist in this repo and in what order they are built. `docs/skill-manifest.json` is generated from it and must not drift from it.

## How to read the labels

Every factual statement in this document carries one of two labels, per the root contract.

- **measured** appears only where a measurement is quoted from PASS.md itself, and it names the section: "measured, per PASS.md A7".
- **claimed** covers everything else: design intent, inferred behaviour, standard versions read from search results, and anything about a running host. This agent has no access to the running host, so almost everything below is claimed.

Nothing here is upgraded from claimed to measured by rewording.

## Prior-art search: what ran

Search was available and ran. Queries issued, in order:

1. "standard contract for dispatching one unit of agent work request result cancellation timeout"
2. "A2A protocol task lifecycle states specification version 2026"
3. "Agent Client Protocol ACP specification version session/cancel session/prompt stop reason"
4. "Model Context Protocol specification latest revision date 2026 version"
5. "OCI Runtime Specification latest release version 2026"
6. "OpenTelemetry GenAI semantic conventions stable version 2026 gen_ai.agent"
7. "in-toto attestation framework v1 DSSE v1 SLSA v1.1 CloudEvents 1.0.2 spec version"
8. "open standard for durable execution portable workflow contract Restate DBOS Temporal interoperability spec"
9. "RFC 9162 Certificate Transparency v2 Merkle tree tamper-evident log append-only state store"
10. "IETF draft-ietf-httpapi-idempotency-key-header status 2026 RFC"
11. "Agent Skills spec SKILL.md specification version agentskills 2026"

One direct fetch was blocked: `https://a2a-protocol.org/latest/specification/` returned `EGRESS_BLOCKED` from the network egress proxy. Everything asserted about A2A below therefore rests on search-result summaries, not on the specification text, and is labelled claimed with the version unverified.

**Result of the search for Part C item 2.** No published standard was found that defines a portable contract for "one unit of agent work executes and returns one result", and none was found for a durable-execution wire contract across engines (claimed, from queries 1 and 8). Search surfaced an ISA committee call and a CNCF sandbox workflow DSL, neither of which is a dispatch contract (claimed). PASS.md B5's judgement that Dispatch and State have no standard to adopt is therefore supported by search rather than contradicted by it.

What search did find is that Dispatch does not have to be original in its *parts*, only in its assembly. Four published pieces cover most of the surface:

| Piece of Dispatch | Prior art to adopt | Version |
|---|---|---|
| Task lifecycle and terminal states | A2A protocol task states (`submitted`, `working`, `input-required`, `auth-required`, `completed`, `canceled`, `rejected`, `failed`), `taskId` plus `contextId` grouping | A2A v1.0, Linux Foundation (claimed, version unverified, spec text not fetched) |
| Why a turn stopped | Agent Client Protocol stop reasons (`end_turn`, `max_tokens`, `max_turn_requests`, `refusal`, `cancelled`) and its rule that clients keep accepting updates after cancel until the terminal frame | Agent Client Protocol, protocol version unverified (TypeScript SDK v0.21.1 seen in search results, claimed) |
| Failure shape | RFC 9457 Problem Details for HTTP APIs | RFC 9457 |
| Replay safety of an externally-triggered dispatch | Idempotency-Key HTTP header field | draft-ietf-httpapi-idempotency-key-header-07, expired, never became an RFC (claimed) |

What remains genuinely ours in Dispatch: budget as an enforced ceiling rather than a recorded number, durable partial results, and the rule that the grading criterion never crosses the boundary.

For State, search found the integrity primitive but not the store. RFC 9162 (Certificate Transparency Version 2.0) defines an append-only Merkle log with inclusion and consistency proofs. RFC 8785 (JSON Canonicalization Scheme) defines the byte form to hash. The in-toto Attestation Framework and DSSE define how to sign a tree head so a tool we did not write can verify it. What remains ours: the write model, the single-writer guarantee, retention with redaction, and the query surface a pure planner needs.

---

# 1. Ordered build sequence

Five core components, sixteen capabilities, two seams, seven cross-cutting concerns, plus the authoring disciplines and the compositions. Items inside a wave are independent of each other and can be authored by parallel agents in the same pass. A wave starts only when the previous wave is complete.

The organising principle: **a real dependency is one where you cannot write the interface without the other thing already fixed. An apparent dependency is one where you cannot run the implementation without it.** Build order follows the first, not the second.

## Wave 1: authoring disciplines

Nothing in this repo can be checked until the checking discipline exists. These four skills are what every later author uses, so they are built first and depend only on the root contract.

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `build-definition-of-done` | the root contract's definition of done | the pieces it will be applied to | The discipline is "criterion plus breakage plus both measured outputs". It is shaped by the rule, not by the subject. |
| `build-adapter-pair` | design rule 3 | the capabilities it will be applied to | The test of a second adapter is "does it differ in execution model", which is answerable before any capability exists. |
| `build-evidence-record` | the claimed-versus-measured rule; the evidence-record fields already in use (script SHA-256, git commit, tree hash, dirty flag), per PASS.md A5 (claimed) | the provenance capability and its attestation format | Recording what you measured and attesting to an artifact are different jobs. The first is a note-taking discipline; the second is a signed envelope. Conflating them is how a claim gets laundered into a measurement. |
| `build-skill-authoring` | the skill layering and naming convention in the root contract | every skill it governs | The convention is fixed by the root contract. |

## Wave 2: the two interfaces every other interface quotes

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `cap-errors` (RFC 9457) | nothing but the authoring disciplines | the transport (HTTP) it names | RFC 9457 defines a media type and a member set. Nothing forces the transport to be HTTP for the *shape* to be adopted; a JSON-RPC or stdio adapter can carry the same object. |
| `cap-document-validation` (JSON Schema 2020-12) | nothing but the authoring disciplines | `cap-errors`; the Document itself | Neither is real. JSON Schema 2020-12 defines its own output formats for validation results, so a validator does not need our problem shape to report a failure; mapping its output into problem details is the consumer's job, and keeping that separation is what lets the validator be swapped for one in another language runtime. And a validator is built against the meta-schema and the official test suite, not against our document shape, which is what lets the Document be declared rather than described. |

These two are separated from the other fourteen capabilities because every other interface in the system quotes them. An interface that cannot say "this input is malformed" and "this operation failed, here is the type" in a fixed shape will invent its own, and then there are sixteen error vocabularies.

## Wave 3: the Document, and the fourteen remaining capability interfaces

Every item here depends on wave 2 and on nothing else in this wave. That independence is the point: this is the widest parallel wave, fourteen capability interfaces plus one core component.

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `core-document` | `cap-document-validation`, `cap-errors` | the Planner, the Judge, the Ledger | The Document is data. It declares intent, a definition of done, and steps. It is written before anything reads it, and it must be, because a planner that shapes the document has made planning impure. |
| `cap-isolation` | `cap-errors` | the agent runtime that will run inside it | Isolation's contract is "a unit of work runs with declared resources and declared egress". What the unit *is* is opaque to it. Coupling them is what produces a sandbox that only runs one agent. |
| `cap-model-access` | `cap-errors` | the budget concern; the identity concern | Both are real *enforcement* dependencies and neither is an *interface* dependency. The completions interface is defined by the OpenAI-compatible shape. Budget and identity wrap calls made through it, which is why they sit a wave above and not below. |
| `cap-durable-execution` | `cap-errors` | `cap-idempotency`; the state seam | Neither is real. A step key is a string the caller supplies; the keyed lease that makes the key mean something is enforcement and is applied a wave above. And durable execution needs *a* place to checkpoint, not *our* state seam. Binding it to the seam is how an orchestrator becomes unswappable. |
| `cap-agent-runtime` | `cap-errors` | `cap-isolation`; `cap-tool-access` | The control protocol is defined independent of where the process runs and of what tools it can reach. An agent runtime that only speaks when sandboxed has confused two boundaries. |
| `cap-tool-access` | `cap-errors` | the agent runtime | Tool servers are addressed by protocol, not by client. Any conformant client reaches them. |
| `cap-capability-packaging` | `cap-document-validation` for frontmatter validation | the agent runtime that loads skills | The packaging format is a file layout and a frontmatter contract. Loading is a consumer concern. |
| `cap-work-intake` | `cap-errors`, `cap-document-validation` | `cap-idempotency`; `cap-scheduling`; the durable executor | None is real. Intake accepts an envelope and produces a validated document; replay safety is applied above by the idempotency lease, not built into the envelope. A schedule is one producer among several, not the intake mechanism, and building intake around the scheduler is how HTTP and git-event intake end up as special cases. |
| `cap-telemetry` | `cap-errors` | trace parentage across the agent boundary | Not real, and this is the sharpest case in the table. W3C trace context does not survive the agent boundary; a depth-3 task tree produces three unrelated root traces (measured, per PASS.md A7 finding 1). The interface must therefore be built on explicit resource attributes set at dispatch, which is a *weaker* dependency than parentage, not a stronger one. |
| `cap-policy` | `cap-errors`; `cap-document-validation` for the input document | the enforcement point | The decision API is "input document in, decision plus rule id out". Where the decision is consulted is `xc-policy-gate`'s problem. Conformance checks that exist but are not wired into the enforcement path (claimed, per PASS.md A6) is exactly what happens when these two are treated as one thing. |
| `cap-provenance` | `cap-errors` | the state seam; the ledger | An attestation is a signed statement about an artifact. It is verifiable standing alone by an external tool, which is the whole point (PASS.md B4). If verification needs our store, we have failed the requirement. |
| `cap-identity` | `cap-errors` | the policy engine | Policy consumes identity; identity does not need policy to be defined. Building them together produces an identity model shaped by today's rules. |
| `cap-scheduling` | `cap-errors` | the durable executor's schedule feature | RFC 5545 recurrence evaluation is a pure function from a rule and a window to a set of occurrences. Sourcing it from an orchestrator's scheduler makes the orchestrator unswappable for a reason unrelated to orchestration. |
| `cap-idempotency` | `cap-errors` | the ledger as dedup authority | The key convention and the lease store are separable. The Ledger is *an* implementation of the lease store, and PASS.md B3 records today's state as "key on the wire, no lease" (claimed), which is precisely the gap this interface names. |
| `cap-state-persistence` | `cap-errors` | the graph and the ledger shapes | Persistence is "put a record, get it back, prove nobody changed it". It is defined over opaque records. `seam-state` is the thing that knows records are graph edges and ledger entries. |

## Wave 4: the rest of the core, and the seven cross-cutting concerns

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `core-graph` | `core-document`, `cap-errors` | `cap-state-persistence`, `seam-state` | The graph is a typed structure with three edge kinds: existence, interface, implementation. Typing and validity are decidable in memory. Persistence is a separate seam and adding it here is how the graph acquires a storage engine's shape. |
| `core-judge` | `core-document` (the definition of done lives there), `cap-errors` | `cap-isolation` | Hiding the criterion from the graded (design rule 6) is a property of what Dispatch is allowed to put in a request, not a property of the Judge. The Judge is a pure function of result and criterion. |
| `core-ledger` | `core-document`, `cap-errors` | `cap-state-persistence` | The Ledger is the append-only, cross-run dedup authority. It is defined by its fold and its dedup rule. Where the log physically lives is `seam-state`. |
| `xc-typed-errors` | `cap-errors` | every adapter | The discipline is "no failure is ever parsed from prose, every failure has a registry type". It is enforced by a check over adapters, but it is defined before them. |
| `xc-correlation` | `cap-telemetry` | trace parentage | See wave 3. Correlation rides on explicit attributes set at dispatch (remedy for a measured failure, per PASS.md A7 finding 1). |
| `xc-identity-delegation` | `cap-identity` | the dispatch seam | Delegation chains are a claim structure. Dispatch carries them; it does not define them. PASS.md A6 records no identity field anywhere in the system (claimed), so there is nothing to retrofit around. |
| `xc-policy-gate` | `cap-policy`, `cap-errors` | the durable executor | The gate is "refusal is deterministic and happens before any metered call". That is a placement rule over the call path, independent of who runs the call path. |
| `xc-provenance-chain` | `cap-provenance`, `build-evidence-record` | `seam-state` | An attestation must verify with an external tool. Chaining attestations to a log head is `seam-state`'s job; producing and signing them is not. |
| `xc-budget` | `cap-model-access` (the metered surface), `cap-errors` | `core-planner` | The planner *prices*; the budget *enforces*. Building enforcement on top of the planner would mean a unit with no plan has no ceiling. Every unit of work carries a ceiling (PASS.md B4), planned or not. |
| `xc-idempotency-lease` | `cap-idempotency`, `cap-state-persistence` | `core-ledger`; `cap-durable-execution` | Neither is real. A lease is a keyed compare-and-set with an owner and an expiry, so any store with a conditional write provides one. Building it on the Ledger specifically would tie replay safety to one projection of the log when the persistence interface already offers everything a lease needs. |

Note on why there are both `cap-` and `xc-` skills for identity, policy, provenance, telemetry, errors and idempotency: the `cap-` skill defines the interface and its adapters. The `xc-` skill defines the enforcement point and the way it must not be declinable. Merging them produced PASS.md A6's failure mode, where conformance checks exist and are not in the enforcement path (claimed). Budget has no `cap-` row in PASS.md B3 because it is not an external dependency; it is purely a platform obligation.

## Wave 5: the Planner, and the two seams

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `core-planner` | `core-document`, `core-graph`, `xc-budget` for the cost vocabulary | `cap-model-access`; `seam-dispatch` | This is the load-bearing non-dependency of the whole design. Planning is a pure function that completes before execution begins (design rule 5). If the planner calls a model to estimate, planning spends, and cost is no longer knowable before commitment. The planner consumes a cost table and historical cost quantiles as *inputs*, which is data, not a client. |
| `seam-dispatch` | `core-document`, `core-judge`, `cap-isolation`, `cap-agent-runtime`, `cap-durable-execution`, `cap-errors`, and all seven `xc-` skills | `core-planner`; `seam-state` | Dispatch executes one unit and returns one result. It does not plan, and a plan is not required to dispatch. It writes through the state seam but is defined against a narrower "durably record this output" obligation, so it is authored against that obligation and wired to the seam after. |
| `seam-state` | `core-graph`, `core-ledger`, `cap-state-persistence`, `xc-provenance-chain`, `cap-errors` | `seam-dispatch` | State is written by more than dispatch: intake, scheduling and policy decisions all append. Shaping it around dispatch would make the log a dispatch journal. |

Dispatch and State are in the same wave and are independent of each other by construction. That independence is deliberate and is the thing to protect: if authoring one forces a change in the other, the seam boundary is drawn wrong.

## Wave 6: workflow composition

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `compose-workflow` | `seam-dispatch`, `seam-state`, `core-planner`, `cap-durable-execution`, `cap-work-intake` | a specific orchestrator | A workflow is a plan whose steps are dispatches, checkpointed after each step. That is expressible over any durable-execution adapter, including a queue plus a state machine. PASS.md A6 records the orchestrator as down (claimed), which is the reason not to define workflow in its terms. |

## Wave 7: loop and approval

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `compose-loop` | `compose-workflow`, `core-judge`, `xc-budget` | a model with a particular context window | A loop is dispatch, judge, decide, repeat, bounded by budget and iteration count. The termination condition is a verdict from the Judge and a ceiling from budget, both external to the model. |
| `compose-approval` | `compose-workflow`, `cap-work-intake`, `cap-scheduling`, `xc-idempotency-lease` | the durable executor's signal feature | Park-and-resume is a workflow that suspends on a durable state record and resumes on an external event. It needs an idempotent resume and a timeout, not a vendor signal primitive. Human-in-the-loop is designed around an orchestrator that is currently down (claimed, per PASS.md A6), which is precisely why it must not be defined in that orchestrator's terms. |

`compose-approval` earns a place rather than being folded into `compose-workflow` because its resume is externally triggered and therefore must be idempotent and time-bounded in a way that an internal step transition is not. That difference is a different set of checks, so it is a different skill.

## Wave 8: agent composition

| Item | Truly depends on | Apparent dependency that is not real | Why not real |
|---|---|---|---|
| `compose-agent` | `compose-loop`, `cap-agent-runtime`, `cap-tool-access`, `cap-capability-packaging`, `cap-isolation` | any particular agent product | An agent is a loop with a tool surface and a packaged capability set, running isolated. Everything it needs is an interface by this wave. It is built last because it is the widest consumer, not because it is the most important. |

## Summary of the sequence

| Wave | Contents | Count |
|---|---|---|
| 1 | authoring disciplines | 4 |
| 2 | errors, document validation | 2 |
| 3 | Document, fourteen capability interfaces | 15 |
| 4 | Graph, Judge, Ledger, seven cross-cutting concerns | 10 |
| 5 | Planner, Dispatch, State | 3 |
| 6 | workflow | 1 |
| 7 | loop, approval | 2 |
| 8 | agent | 1 |

Eight waves, thirty-eight skills, plus the root contract at wave 0.

---

# 2. First-cut design for Dispatch and State

Both designs adopt published pieces wherever one exists and confine original design to what search showed has no published answer. Everything in this section is claimed unless it quotes a PASS.md measurement.

## 2.1 Dispatch

**Contract in one sentence.** One unit of agent work executes and returns one result, under a declared ceiling, with a typed outcome, whose partial progress is durable before the outcome is known.

### 2.1.1 Request shape

Design decisions, each with its reason.

- The request is a document plus a set of ceilings plus an actor plus a correlation record. It is not a script. What to do is declared in the Document; how much may be spent doing it is declared here.
- The definition of done is **not** in the request. The request carries `criterion_ref`, an opaque handle the Judge resolves out of band. Design rule 6: the grader is never visible to the graded. A criterion that arrives in the request is a target.
- Correlation is carried as explicit fields, never inferred from trace parentage. W3C trace context does not survive the agent boundary and a depth-3 task tree produces three unrelated root traces (measured, per PASS.md A7 finding 1).
- `idempotency_key` is required, not optional. Every externally-triggered action is safe to replay (PASS.md B4). The header field convention is defined in draft-ietf-httpapi-idempotency-key-header-07, which expired without becoming an RFC (claimed), so the convention is adopted and the lease semantics are specified by us in 2.1.6.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:request:0.1",
  "title": "DispatchRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["dispatch_id", "idempotency_key", "document", "criterion_ref",
               "actor", "budget", "deadline", "isolation", "correlation"],
  "properties": {
    "dispatch_id":     { "type": "string", "format": "uuid" },
    "context_id":      { "type": "string", "format": "uuid",
                         "description": "Groups related dispatches. Adopted from A2A contextId (claimed, version unverified)." },
    "previous_dispatch_id": { "type": "string", "format": "uuid",
                         "description": "Set when this dispatch resumes after a partial. Never mutates the previous result." },
    "idempotency_key": { "type": "string", "minLength": 1, "maxLength": 255 },
    "document":        { "$ref": "urn:agentic:core:document:0.1" },
    "criterion_ref":   { "type": "string", "minLength": 1,
                         "description": "Opaque handle. The criterion itself must never appear in this object." },
    "actor": {
      "type": "object", "additionalProperties": false,
      "required": ["subject", "delegation_chain"],
      "properties": {
        "subject": { "type": "string", "description": "Workload or user identity URI." },
        "delegation_chain": {
          "type": "array", "minItems": 1,
          "items": {
            "type": "object", "additionalProperties": false,
            "required": ["actor", "obtained_via"],
            "properties": {
              "actor":        { "type": "string" },
              "obtained_via": { "enum": ["rfc8693_token_exchange", "workload_attestation", "direct"] }
            }
          },
          "description": "RFC 8693 OAuth 2.0 Token Exchange act-claim chain, oldest hop first."
        }
      }
    },
    "budget": {
      "type": "object", "additionalProperties": false,
      "required": ["ceiling_micros", "currency", "on_exceed"],
      "properties": {
        "ceiling_micros": { "type": "integer", "minimum": 0 },
        "currency":       { "type": "string", "pattern": "^[A-Z]{3}$" },
        "token_ceiling":  { "type": "integer", "minimum": 0 },
        "on_exceed":      { "const": "terminate_unit" }
      },
      "description": "on_exceed is a const, not an enum. Exceeding terminates the unit, not the platform, and a caller cannot choose otherwise (PASS.md B4)."
    },
    "deadline": {
      "type": "object", "additionalProperties": false,
      "required": ["not_after", "max_duration_s"],
      "properties": {
        "not_after":      { "type": "string", "format": "date-time" },
        "max_duration_s": { "type": "integer", "minimum": 1 },
        "cancel_grace_s": { "type": "integer", "minimum": 1, "default": 10 }
      }
    },
    "isolation": {
      "type": "object", "additionalProperties": false,
      "required": ["profile", "egress"],
      "properties": {
        "profile": { "type": "string", "description": "Named resource profile, resolved by the isolation adapter." },
        "egress":  { "enum": ["none", "allowlist"], "default": "none" },
        "egress_allowlist": { "type": "array", "items": { "type": "string" } },
        "credentials": { "const": "broker_only",
                         "description": "No real secret enters the unit. The unit reaches a broker that holds the key." }
      },
      "allOf": [{ "if":   { "properties": { "egress": { "const": "allowlist" } } },
                  "then": { "required": ["egress_allowlist"] } }]
    },
    "capabilities": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "tool_endpoints": { "type": "array", "items": { "type": "string", "format": "uri" },
                            "description": "Model Context Protocol servers, revision 2026-07-28 (claimed)." },
        "skills":         { "type": "array", "items": { "type": "string" },
                            "description": "Agent Skills spec packages by name (version unverified)." }
      }
    },
    "correlation": {
      "type": "object", "additionalProperties": false,
      "required": ["run_id", "root_dispatch_id"],
      "properties": {
        "run_id":            { "type": "string" },
        "root_dispatch_id":  { "type": "string", "format": "uuid" },
        "parent_dispatch_id":{ "type": "string", "format": "uuid" },
        "depth":             { "type": "integer", "minimum": 0 }
      },
      "description": "Emitted as OTLP resource attributes at dispatch. Correlation must not depend on traceparent propagation."
    }
  }
}
```

### 2.1.2 Result shape

The state machine is A2A's, not ours (claimed, version unverified, spec text not fetched because the domain was egress-blocked). The stop-reason vocabulary is ACP's, extended by exactly three values that ACP has no reason to carry: budget exhaustion, deadline expiry, and policy denial.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:dispatch:result:0.1",
  "title": "DispatchResult",
  "type": "object",
  "additionalProperties": false,
  "required": ["dispatch_id", "state", "stop_reason", "started_at", "ended_at",
               "partial", "outputs", "usage", "correlation"],
  "properties": {
    "dispatch_id": { "type": "string", "format": "uuid" },
    "state": {
      "enum": ["submitted", "working", "input-required", "auth-required",
               "completed", "canceled", "rejected", "failed"],
      "description": "A2A task lifecycle. Terminal states are completed, canceled, rejected, failed."
    },
    "stop_reason": {
      "enum": ["end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled",
               "budget_exhausted", "deadline_exceeded", "policy_denied", "cancel_timeout",
               "adapter_unavailable"],
      "description": "First five adopted from Agent Client Protocol stop reasons (claimed)."
    },
    "started_at": { "type": "string", "format": "date-time" },
    "ended_at":   { "type": "string", "format": "date-time" },
    "partial":    { "type": "boolean",
                    "description": "True whenever state is not 'completed' and outputs is non-empty." },
    "outputs": {
      "type": "array",
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["digest", "media_type", "recorded_at_head"],
        "properties": {
          "digest":     { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
          "media_type": { "type": "string" },
          "inline":     { "type": "string", "contentEncoding": "base64" },
          "ref":        { "type": "string", "format": "uri" },
          "recorded_at_head": { "type": "string",
                                "description": "State-seam head digest at which this output became durable." }
        }
      }
    },
    "usage": {
      "type": "object", "additionalProperties": false,
      "required": ["cost_micros", "currency", "wall_ms"],
      "properties": {
        "cost_micros":   { "type": "integer", "minimum": 0 },
        "currency":      { "type": "string", "pattern": "^[A-Z]{3}$" },
        "tokens_in":     { "type": "integer", "minimum": 0 },
        "tokens_out":    { "type": "integer", "minimum": 0 },
        "wall_ms":       { "type": "integer", "minimum": 0 },
        "metered_calls": { "type": "integer", "minimum": 0 }
      }
    },
    "attestation_ref": { "type": "string",
                         "description": "DSSE envelope over an in-toto Statement describing this result (versions unverified)." },
    "correlation":     { "$ref": "urn:agentic:dispatch:request:0.1#/properties/correlation" },
    "problem":         { "$ref": "urn:agentic:problem:0.1" }
  },
  "allOf": [
    { "if":   { "properties": { "state": { "enum": ["failed", "rejected"] } }, "required": ["state"] },
      "then": { "required": ["problem"] } },
    { "if":   { "properties": { "state": { "const": "completed" } }, "required": ["state"] },
      "then": { "properties": { "partial": { "const": false } } } }
  ]
}
```

### 2.1.3 Cancellation semantics

Cancellation is a request that a unit reach a terminal state, not a kill. Five rules.

1. **Cancel is asynchronous and idempotent.** Cancelling a dispatch that is already terminal returns the current result and is not an error.
2. **Late frames are legal.** A consumer must keep accepting output frames after issuing cancel, until the terminal frame arrives. This follows ACP's guidance that agents may send final updates before responding with the cancelled stop reason (claimed).
3. **There is a grace window, and it is bounded.** Default `cancel_grace_s` is 10. The default is chosen because a mid-tool-call cancel ends the turn in about 8 seconds against a 45 second operation with zero trailing frames (measured, per PASS.md A3), so 10 seconds is the observed behaviour plus headroom rather than a guess. The value is per-request because a different isolation or runtime adapter will have a different floor.
4. **Grace expiry is a hard stop, and it is a failure, not a cancellation.** If the window elapses, the isolation adapter destroys the unit and the result is `state: "failed"`, `stop_reason: "cancel_timeout"`, with a problem object. Reporting a hard kill as a clean cancel would hide an adapter that cannot cancel.
5. **A cancelled dispatch with durable outputs is a partial, not a loss.** `partial: true`, outputs retained, attestation produced over what exists.

### 2.1.4 Timeout and budget enforcement

Two ceilings, independent, both enforced outside the unit.

| Ceiling | Enforced by | Mechanism | Result on breach |
|---|---|---|---|
| Wall clock | the dispatcher | monotonic timer against `not_after` and `max_duration_s`, whichever is sooner | cancel is issued, then the grace rules in 2.1.3 apply; `stop_reason: "deadline_exceeded"` |
| Spend | the model-access broker | a reservation lease is taken at dispatch for `ceiling_micros`; each metered call is pre-checked against remaining reservation and post-reconciled with actual cost | the call is refused with an RFC 9457 problem of type `.../budget-exhausted`; the unit then terminates with `stop_reason: "budget_exhausted"` |

Why outside the unit: a unit that enforces its own ceiling can decline to. The substrate already demonstrates the correct pattern, with scoped keys carrying hard budget caps that terminate spend rather than merely record it (measured, per PASS.md A4). This design keeps that property and adds the reservation lease so that a unit which crashes without reconciling does not leave the budget permanently consumed. Unreconciled reservations expire at `not_after` plus grace.

Both ceilings terminate the unit, never the platform. That is a `const` in the schema rather than an enum, so there is no request that opts out.

### 2.1.5 Partial-result handling

The rule: **an output is durable before the dispatch is terminal, or it does not exist.**

- Every output is written through the state seam and gets a `recorded_at_head` before the result is assembled. A result therefore never claims an output that a later reader cannot find.
- `partial: true` whenever the state is not `completed` and `outputs` is non-empty. Partial outputs carry the same digest and the same attestation form as complete ones. There is no second-class artifact.
- A partial is never promoted. Resuming means a **new** `dispatch_id` with `previous_dispatch_id` set. The ledger is append-only across runs (PASS.md B2), so mutating a prior result is not available even as a mistake.
- The three interrupted states (`input-required`, `auth-required`) and the `working` state are non-terminal and always imply `partial: true` if outputs exist. They are the mechanism by which a park-and-resume workflow suspends without discarding progress.

### 2.1.6 What a failure returns

RFC 9457 problem details, media type `application/problem+json`. Never prose (PASS.md B4). Extension members are declared, not ad hoc.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:0.1",
  "title": "Problem",
  "type": "object",
  "required": ["type", "title", "status"],
  "properties": {
    "type":     { "type": "string", "format": "uri",
                  "description": "Must be a member of the type registry below. Unregistered types are a conformance failure." },
    "title":    { "type": "string" },
    "status":   { "type": "integer", "minimum": 100, "maximum": 599 },
    "detail":   { "type": "string" },
    "instance": { "type": "string", "format": "uri" },
    "dispatch_id": { "type": "string", "format": "uuid" },
    "stop_reason": { "$ref": "urn:agentic:dispatch:result:0.1#/properties/stop_reason" },
    "retryable":   { "type": "boolean" },
    "retry_after_s": { "type": "integer", "minimum": 0 },
    "rule_id":     { "type": "string", "description": "Set when type is policy-denied." },
    "correlation": { "$ref": "urn:agentic:dispatch:request:0.1#/properties/correlation" },
    "causes":      { "type": "array", "items": { "$ref": "urn:agentic:problem:0.1" },
                     "description": "Delegated failure chain, innermost last." }
  }
}
```

First-cut type registry, closed at authoring time and extended only by adding a row here:

| Type suffix | Status | Retryable | Raised when |
|---|---|---|---|
| `document-invalid` | 422 | no | The document fails JSON Schema 2020-12 validation |
| `criterion-unresolvable` | 422 | no | `criterion_ref` does not resolve |
| `identity-untrusted` | 401 | no | The delegation chain does not verify |
| `policy-denied` | 403 | no | A deterministic pre-execution refusal, carries `rule_id` |
| `budget-exhausted` | 402 | no | A metered call would cross the ceiling |
| `deadline-exceeded` | 504 | yes | Wall clock ceiling reached |
| `cancel-timeout` | 500 | no | Grace window elapsed, unit destroyed |
| `isolation-unavailable` | 503 | yes | No isolation adapter could admit the unit |
| `adapter-unavailable` | 503 | yes | A capability adapter is down |
| `idempotency-conflict` | 409 | no | Same key, different request body |

Two rules that make this enforceable rather than decorative. First, `retryable` is a field, not an inference from status: a 503 that is not retryable must say so. Second, a failure that cannot be typed is itself a conformance failure of the adapter, reported as `adapter-unavailable` with the untyped payload in `detail`, and it is counted. An adapter whose untyped-failure count is non-zero is not conformant.

## 2.2 State

**Contract in one sentence.** The graph and the ledger are two projections of one append-only, tamper-evident log, written by one writer per run and read at a pinned snapshot.

### 2.2.1 Write model

- **One log, two projections.** There is not a graph store and a ledger store. There is a log of immutable facts, and both the graph and the ledger are folds over it. Two stores would need a distributed transaction to stay consistent; one log does not.
- **Records are facts, never updates.** Record kinds in the first cut: `node-asserted`, `edge-asserted`, `document-declared`, `dispatch-submitted`, `dispatch-observed`, `ledger-entry`, `policy-decided`, `attestation-recorded`, `head-sealed`. Retraction is a new `edge-asserted` record with `retracts` set, not a delete.
- **Records are content-addressed.** `record_id = sha256(JCS(body))` where JCS is RFC 8785 JSON Canonicalization Scheme. Canonical bytes are what makes two independent writers agree on an identity.
- **Current state is a fold.** Anything that cannot be derived by folding the log from empty is not state, it is cache.

### 2.2.2 Concurrency and single-writer guarantees

- **Partition by `run_id`. Exactly one writer per partition.** Cross-run total order is not guaranteed and is not needed: cross-run continuity is provided by the sealed head, not by interleaving.
- **Single writer is enforced by a fencing lease, not by a single process.** The writer holds a lease with a monotonically increasing fencing token. Every append carries the token. The store rejects an append whose token is lower than the highest it has seen. This survives a writer that pauses, is presumed dead, and wakes up.
- **Every append is conditional on the head.** An append states `prev_record_id` and is accepted only if that equals the current head, a compare-and-swap. This is the general form of the hash chain that exists today, where each run's closing digest is the next run's opening digest (claimed, per PASS.md A5).
- **Readers are unbounded and never block writers.** A reader takes a head digest and reads at it.

Failure mode this closes: a writer that thinks it holds the lease, appends, and silently forks the chain. Compare-and-swap makes the second writer's append fail rather than branch.

### 2.2.3 Integrity mechanism

Keep the chain. Add proofs.

- **Chain, retained.** Each record carries `prev_record_id` and `chain_digest = sha256(prev_chain_digest || record_id)`. This is the idea PASS.md B5 says should survive, and it does.
- **Merkle tree, added.** The same records form an append-only Merkle tree per RFC 9162 (Certificate Transparency Version 2.0). This buys two proofs the linear chain cannot give cheaply:
  - **inclusion proof**: this record is in this log, verified in O(log n) instead of rehashing the whole log;
  - **consistency proof**: this log is an extension of the log I saw last time, with nothing removed or reordered.
- **Sealed heads.** At run close, a `head-sealed` record is written carrying `{tree_size, root_hash, chain_digest, sealed_at}`. The closing sealed head of run N is the opening sealed head of run N+1, which preserves exactly the property PASS.md A5 describes: a manual edit between runs is detectable (claimed, per PASS.md A5). The difference is that detection is now a proof rather than a rehash.
- **Signed so an external tool verifies it.** The sealed head is wrapped in an in-toto Statement (in-toto Attestation Framework v1, version unverified) inside a DSSE envelope (version unverified). PASS.md B4 requires provenance verifiable with a tool we did not write, and a sealed head signed this way is verifiable by any DSSE and in-toto verifier.

Why not just keep the chain: verifying 2,445 records across 308 runs (measured, per PASS.md A5) by rehashing is tractable today and is not tractable at a hundred times that, and more importantly a chain gives no way for a third party to verify one record without the whole log.

### 2.2.4 Retention

Three classes, because they have three different lifetimes and one policy for all of them will be wrong for two of them.

| Class | Content | Default retention | Deletable |
|---|---|---|---|
| Chain | record headers, `record_id`, `prev_record_id`, `chain_digest`, kind, timestamps, sealed heads | forever | no |
| Body | the record's fields | 400 days | yes, by tombstone |
| Payload | large artifacts referenced by digest | 90 days, extendable by hold flag | yes, by tombstone |

**Redaction without breaking integrity.** The chain commits to `record_id`, which is the hash of the canonical body. A body may be replaced by a tombstone that preserves `record_id` and records who redacted it and under what authority. The chain and every inclusion proof still verify, because neither ever needed the body, only its digest. This is what makes it possible to delete a leaked secret or a personal-data field without invalidating every subsequent record, and a store that cannot do that will eventually be asked to choose between compliance and integrity.

A `hold` flag on a payload suspends retention expiry. Holds are themselves records.

### 2.2.5 The query surface a planner needs

Design rule 5 says planning is a pure function that completes before execution. A pure function cannot read a moving store. Therefore **every query takes `at_head` and is deterministic at that head.** Same head, same answer, forever. That single constraint is what makes rule 5 checkable rather than aspirational.

| Query | Signature | Why the planner needs it |
|---|---|---|
| resolve head | `resolve_head(run_id) -> {tree_size, root_hash, chain_digest, sealed}` | Pins the snapshot. This is the only non-deterministic call and it is made once, before planning starts. |
| get document | `get_document(document_id, at_head) -> Document` | The plan is a function of the document. |
| neighbors | `neighbors(node_id, edge_type in {existence, interface, implementation}, direction, at_head) -> [node]` | Expanding a step into candidate implementations is a walk over typed edges. |
| path exists | `path_exists(from, to, edge_types, max_depth, at_head) -> {found, path}` | Answers "is there an implementation reachable for this interface" without loading the graph. |
| prior result | `prior_result(idempotency_key or document_digest, at_head) -> DispatchResult or null` | The Ledger is the deduplication authority (PASS.md B2). A planner that cannot ask this will plan work that has already been done. |
| cost history | `cost_history(selector, window, at_head) -> {p50_micros, p95_micros, n}` | Cost must be knowable before commitment. A rate card alone does not price a step whose call count varies; measured quantiles do. This is the query that makes the Planner's purity affordable, because it turns a prediction into a lookup. |
| open dispatches | `open_dispatches(run_id, at_head) -> [dispatch]` | Non-terminal work from a prior run must be reconciled, not re-planned. |
| verify | `verify(record_id, at_head) -> inclusion_proof` | Lets any consumer, including one we did not write, check a record without the log. |

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:record:0.1",
  "title": "StateRecord",
  "type": "object",
  "additionalProperties": false,
  "required": ["record_id", "prev_record_id", "chain_digest", "kind",
               "run_id", "fencing_token", "written_at", "actor", "body"],
  "properties": {
    "record_id":     { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                       "description": "sha256 over RFC 8785 canonical JSON of body." },
    "prev_record_id":{ "type": ["string", "null"], "pattern": "^sha256:[0-9a-f]{64}$" },
    "chain_digest":  { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "kind": { "enum": ["node-asserted", "edge-asserted", "document-declared",
                       "dispatch-submitted", "dispatch-observed", "ledger-entry",
                       "policy-decided", "attestation-recorded", "head-sealed", "tombstone"] },
    "run_id":        { "type": "string" },
    "fencing_token": { "type": "integer", "minimum": 0 },
    "written_at":    { "type": "string", "format": "date-time" },
    "actor":         { "$ref": "urn:agentic:dispatch:request:0.1#/properties/actor" },
    "retracts":      { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "body":          { "type": ["object", "null"],
                       "description": "Null only for a tombstone, where record_id still commits to the original body." },
    "retention": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "class":     { "enum": ["chain", "body", "payload"] },
        "expires_at":{ "type": "string", "format": "date-time" },
        "hold":      { "type": "boolean", "default": false }
      }
    }
  }
}
```

---

# 3. Definition of done, with the breakage that proves it can fail

One row per core component, capability and seam, then supplementary rows for the cross-cutting, composition and authoring skills so that every skill in the manifest points at a row. A criterion nothing can fail is not a criterion (PASS.md C3). The whole reason this table exists is PASS.md A7 finding 2: a nine-stage pipeline ran structurally green with every behavioural stage skipped because the generated work contained nothing those tools applied to (measured, per PASS.md A7 finding 2). Every criterion below therefore asserts on a **non-zero count of things actually checked**, not merely on an exit code.

All commands and expected results are claimed. None has been executed by this agent.

## 3.1 Core components

| Row | Piece | Machine-checkable criterion | Deliberate breakage that makes it fail |
|---|---|---|---|
| C1 | Document | `document-validate --schema urn:agentic:core:document:0.1 fixtures/positive/*.json fixtures/negative/*.json` exits 0, reports `positive=12 passed`, `negative=9 rejected`, and `checked>0` | Remove `"definition_of_done"` from the schema's `required` array. The negative fixture `missing-dod.json` now validates, the negative count drops to 8, the run exits non-zero. |
| C2 | Planner | Run `plan --document D --head H` twice under `strace -f -e trace=connect,sendto`. Assert the two plan JSON files are byte-identical AND the count of `AF_INET`/`AF_INET6` connects is exactly 0. | Make the planner call the model-access interface to estimate a step cost. Connect count becomes non-zero and the two plans diverge on a sampled estimate. This is the check that keeps design rule 5 true. |
| C3 | Graph | Property test over 10,000 generated graphs: an `implementation` edge whose target node is not of kind `interface` is rejected, and an `existence` edge is never accepted between two `implementation` nodes. Assert `rejections>0` and `false_accepts==0`. | Widen the edge type check to accept any node kind as an `implementation` target. A counterexample is found in under 100 generated cases and `false_accepts` becomes non-zero. |
| C4 | Judge | Two assertions. (a) `judge --result R --criterion C` produces an identical verdict across 100 runs. (b) `grep -F -c "$(cat criterion.txt)" recorded-dispatch-requests.jsonl` returns 0 over a corpus of at least 50 recorded requests. | Inline the criterion text into the document's `definition_of_done` field that is passed to dispatch. The grep count becomes non-zero and (b) fails. This is design rule 6 made checkable. |
| C5 | Ledger | Fold the log from empty and assert the computed head equals the stored sealed head. Then submit a dispatch whose `idempotency_key` is already terminal and assert exactly one dispatch record exists for that key and the prior result is returned. | Make the ledger overwrite rather than append on a duplicate key. The recomputed head diverges from the stored head and the dispatch-record count for the key becomes 2. |

## 3.2 Capability interfaces

| Row | Capability | Machine-checkable criterion | Deliberate breakage that makes it fail |
|---|---|---|---|
| P1 | Isolation | Conformance suite runs one fixture unit under both adapters and asserts: exit codes equal, output digests equal, jail directory mode is `0700` with an owner uid absent from `/etc/passwd`, and a connect attempt from inside to an address outside the declared allowlist fails. Assert `egress_attempts_blocked == egress_attempts_made` and `egress_attempts_made > 0`. | Add `0.0.0.0/0` to the default `egress_allowlist`. The blocked count drops below the attempted count under both adapters. |
| P2 | Model access | Dispatch the same request object through the synchronous adapter and the asynchronous batch adapter; both results validate against one result schema. Additionally `grep -rIl -E '(litellm\|openrouter\|gemini\|sglang)' src/core/ src/seam/` returns no files. | Add a branch on adapter name inside the caller so the batch path takes a different code path. The grep matches and the "no product names in core" assertion fails, which is design rule 1 made checkable. |
| P3 | Durable execution | Run a 20-step workflow with a side-effecting step; `kill -9` the executor at step 11; restart. Assert each side-effecting step has exactly one committed effect keyed by its step idempotency key, and that `steps_replayed > 0` so the crash actually happened. | Drop the idempotency key from the step record. The effect count for step 11 becomes 2. |
| P4 | Agent runtime | Start a 45 second tool call, send cancel at t=5s. Assert a terminal frame arrives within `cancel_grace_s`, `stop_reason == "cancelled"`, and zero frames arrive after the terminal frame. Reference point: about 8 seconds against a 45 second operation with zero trailing frames (measured, per PASS.md A3). | Raise the adapter's internal cancel poll interval above the grace window. The terminal frame arrives late, the dispatcher hard-stops, and `stop_reason` becomes `cancel_timeout` instead of `cancelled`. |
| P5 | Tool access | `mcp-conformance --revision 2026-07-28 --endpoint $URL` reports zero failures **and** `tools/list` returns a count greater than zero, and each listed tool's input schema validates against JSON Schema 2020-12. | Unregister every tool. Conformance still passes and the tool count assertion fails. This is the exact condition PASS.md A6 records, an endpoint live and authenticated with zero tools registered (claimed), which a conformance-only check would have called green. |
| P6 | Capability packaging | Every skill directory has a `SKILL.md` with `name` and `description` frontmatter, `name` equals the directory name, and every entry in its `Composes with` section resolves to an existing skill and appears symmetrically in that skill's own section. Assert `links_checked > 0` and `dangling == 0` and `asymmetric == 0`. | Rename one skill directory without updating the links that name it. `dangling` becomes non-zero. |
| P7 | Work intake | Submit one logical job three ways: as a CloudEvent over HTTP, as an A2A message, and via an RFC 5545 schedule occurrence. Assert the three resulting documents have identical digests and three distinct `dispatch_id`s. | Let the HTTP intake path stamp a default `priority` field. The digests diverge and the equality assertion fails. |
| P8 | Document validation | Run the validator against the official JSON-Schema-Test-Suite `draft2020-12` directory. Assert 100% of required cases pass and `cases_run > 1000`. | Configure the validator for draft-07. `$dynamicRef` and `$recursiveRef` cases fail and the pass rate drops below 100%. |
| P9 | Telemetry | Execute a depth-3 task tree. Query the collector for all spans carrying resource attribute `run.id == R`. Assert the span count covers all three levels and that grouping by `run.id` yields exactly one group, while explicitly permitting more than one distinct `trace_id`. | Remove the `run.id` resource attribute injection at dispatch. The query returns only the top level and correlation collapses into three unrelated trees, reproducing PASS.md A7 finding 1 (measured, per PASS.md A7). |
| P10 | Policy | Submit a dispatch that a policy rule denies. Assert the spend ledger delta for that dispatch is exactly 0, a `policy-decided` record exists carrying a `rule_id`, and the result is `state: "rejected"` with problem type `.../policy-denied`. | Move the policy consultation to after the first metered call. The spend delta becomes greater than 0. This is the check that would have caught policy existing but not being in the enforcement path (claimed, per PASS.md A6). |
| P11 | Provenance | Produce an artifact, then verify its attestation with a third-party verifier that we did not write. Assert the external verifier exits 0 and that `attestations_verified > 0`. | Rebuild the artifact from a modified input without regenerating the attestation. The external verifier exits non-zero on subject digest mismatch. |
| P12 | Errors | Fuzz every adapter's failure paths. Assert every failure response carries media type `application/problem+json`, every `type` value is present in the registry in section 2.1.6, `responses_checked > 200`, and `untyped == 0`. | Have one adapter return a plain-text HTTP 500. `untyped` becomes non-zero. |
| P13 | Identity | For a corpus of at least 50 recorded actions, assert every action carries a `subject`, every delegated action carries a `delegation_chain` of length at least 2, and the final hop matches the executing unit's workload identity. | Dispatch without performing the RFC 8693 token exchange for the agent actor. The chain length assertion fails. There is currently no identity field anywhere in the system (claimed, per PASS.md A6), so this check starts red by construction and that is correct. |
| P14 | Scheduling | Evaluate the RFC 5545 recurrence test vectors including a DST spring-forward boundary, a DST fall-back boundary, a leap day, and a `BYSETPOS` rule. Assert every computed occurrence set equals the expected set and `vectors_run > 40`. | Replace the RRULE evaluator with a fixed-interval cron. The DST vector produces an occurrence one hour off and the leap-day vector produces the wrong date. |
| P15 | Idempotency | Fire the same externally-triggered request 100 times concurrently with one key. Assert exactly one execution occurred and 99 responses returned the first result, and that at least one of the 99 was served while the first was still running. | Remove the lease acquisition while keeping the key on the wire, which is the state PASS.md B3 records today (claimed). The execution count exceeds 1. |
| P16 | State persistence | Write N records under both adapters. Assert an independent verifier recomputes the same head digest under both, that an inclusion proof verifies for a randomly chosen record, and that `records_written > 1000`. | Edit one record body in place in the store. The verifier reports a chain break at that index and the inclusion proof for that record fails. |

## 3.3 Seams

| Row | Seam | Machine-checkable criterion | Deliberate breakage that makes it fail |
|---|---|---|---|
| S1 | Dispatch | One conformance suite runs against every dispatch adapter and asserts, per adapter: malformed requests are rejected with `document-invalid`; a cancel reaches a terminal state within the grace window; a request whose ceiling is exceeded terminates with `budget_exhausted` and a non-zero recorded spend below the ceiling; an interrupted run leaves `partial: true` with at least one output carrying `recorded_at_head`; and every failure body is `application/problem+json`. Assert `adapters_run >= 2` and `assertions_run > 0` per adapter. PASS.md B5 records three implementations with no contract between them today (claimed). | Have one adapter return its native error object instead of problem details. The failure-shape assertion fails for that adapter while the others pass, which is the point: the suite must be able to single out one adapter. |
| S2 | State | Two assertions. (a) The consistency proof between run N's sealed head and run N+1's sealed head verifies with an external Merkle verifier. (b) Every planner query is snapshot-pinned: run each of the eight queries 100 times at a fixed `at_head` while a writer appends concurrently, and assert all 100 results per query are identical. | Let one query read the live head instead of the pinned head. Its 100 results diverge once the concurrent writer appends, and (b) fails while (a) still passes, isolating the fault to the query surface. |

## 3.4 Cross-cutting concerns

| Row | Concern | Criterion | Breakage |
|---|---|---|---|
| X1 | Budget | Over a corpus of at least 100 dispatches, assert every dispatch has a non-null `budget.ceiling_micros`, and that for every terminated-on-budget dispatch, recorded spend is at most the ceiling plus one call's worth of overshoot. | Allow `budget` to be omitted from the request. The non-null assertion fails and unbounded dispatches appear. |
| X2 | Identity delegation | Assert no recorded action has a null `actor`, and delegation chains are acyclic and terminate at a root workload identity. | Permit a `direct` hop to name an actor already present earlier in the chain. The acyclicity check fails. |
| X3 | Policy gate | Assert that for every dispatch, the timestamp of the `policy-decided` record precedes the timestamp of the first metered call, over at least 100 dispatches, with zero inversions. | Consult policy asynchronously in parallel with the first call. Inversions become non-zero. |
| X4 | Provenance chain | Assert every artifact digest referenced by a result has a corresponding `attestation-recorded` record whose subject digest matches, with zero orphans over at least 100 artifacts. | Emit an output without recording an attestation. The orphan count becomes non-zero. |
| X5 | Correlation | Assert every span, log record and problem object emitted during a run carries `run.id` and `root_dispatch_id`, with zero omissions. | Emit spans from a sub-agent without re-stamping the resource attributes, relying on parentage instead. Omissions become non-zero, which is PASS.md A7 finding 1 reproduced (measured, per PASS.md A7). |
| X6 | Typed errors | Assert zero occurrences of failure information being extracted by string matching anywhere outside the problem-details parser: `grep -rn -E 'match.*(error\|failed\|timeout)' src/ --include='*.py'` outside `src/problem/` returns nothing. | Add a retry heuristic that matches on the substring "rate limit" in a response body. The grep matches. |
| X7 | Idempotency lease | Assert that for every externally-triggered action, a lease record exists with an owner and an expiry, and that no two executions share a key. Assert `keys_checked > 0`. | Let the lease expiry be unbounded. A crashed owner blocks the key forever; the check that a lease older than its expiry is reclaimable fails. |

## 3.5 Compositions and authoring disciplines

| Row | Skill | Criterion | Breakage |
|---|---|---|---|
| M1 | Workflow | A workflow of 20 dispatch steps completes with every step's result durable at a head, and a mid-run restart resumes at the first incomplete step, with `steps_resumed > 0`. | Checkpoint after the whole workflow rather than after each step. Restart replays from step 1 and the resume-point assertion fails. |
| M2 | Loop | A loop terminates on one of exactly three conditions: a Judge verdict of pass, an iteration ceiling, or a budget ceiling. Assert over 100 runs that every termination names one of the three and `unbounded == 0`. | Remove the iteration ceiling. A run with a permanently failing verdict and a large budget never terminates and the test times out. |
| M3 | Approval | A parked workflow resumes exactly once when the same approval event is delivered 10 times, and expires with `deadline_exceeded` if no event arrives before its deadline. | Remove the idempotency lease from the resume path. The workflow resumes more than once. |
| M4 | Agent | An agent unit runs isolated with declared tools and skills, and asserts: the criterion string is absent from everything the unit can read, the tool list matches the declared list exactly, and no undeclared skill is loaded. | Mount the criterion file into the unit's filesystem. The absence assertion fails, which is design rule 6 checked at the composition level rather than only at the Judge. |
| B1 | Definition of done | Every skill in the repo has a `Definition of done` section naming a command, an expected result, and a breakage. Assert `skills_checked == skills_total` and `missing == 0`. | Add a skill with a criterion but no breakage. `missing` becomes non-zero. |
| B2 | Adapter pair | Every `cap-` and `seam-` skill names two adapters, and a machine-readable field records how their execution models differ. Assert `pairs_checked > 0`, `single_adapter == 0`. | Set a skill's second adapter to a different vendor with the same execution model. The differs-in-execution-model field is empty and the check fails. |
| B3 | Evidence record | Every recorded result carries the script SHA-256, the git commit, the tree hash under test, whether the tree was dirty, and a claimed-or-measured label. Assert `records_checked > 0` and `unlabelled == 0` and `dirty_and_measured == 0`. | Record a result from a dirty tree labelled measured. `dirty_and_measured` becomes non-zero. A measurement from a dirty tree is not reproducible and must not be labelled measured. |
| B4 | Skill authoring | Every skill has a layer prefix from the allowed set, a `Composes with` section, and every standard it cites carries a version or the literal phrase `version unverified`. Assert `skills_checked > 0` and `uncited_standards == 0`. | Cite a standard with no version and no `version unverified` marker. The count becomes non-zero. |

---

# 4. Second adapters chosen to prove the interface

Design rule 3: the second adapter exists to prove the first is not load-bearing. The test applied here is not "is it a different product" but **"does it break a different assumption"**. A second vendor of the same shape proves nothing, because the interface can be shaped around the shape and still swap.

Five capabilities are given proof-grade second adapters. All five claims about adapter behaviour are claimed; none has been run by this agent.

## 4.1 Isolation

| | |
|---|---|
| Standard | OCI Runtime Spec, v1.2 or later; search results indicate v1.3.0 is current (claimed, version unverified) |
| Adapter today | Firecracker microVM |
| Second adapter | WebAssembly component sandbox, run through an OCI-conformant shim |

**Why this is a real proof.** Firecracker is hardware virtualisation: a kernel, a block device root, a boot, an IP stack that can be given or withheld. A Wasm component has none of those. There is no kernel to configure, no filesystem unless one is granted, no network stack at all, and the syscall surface is capability-granted rather than filtered. Start time differs by orders of magnitude in the direction that matters.

What this forces the interface to do: express a unit of work as *declared resources and declared egress*, not as a machine configuration. If the interface has a field that only a VM can honour, a Wasm adapter cannot implement it and the field was a Firecracker detail leaking into the contract. The current sandbox already has the right instincts, with egress as a flag defaulting off and a dummy credential inside the guest (claimed, per PASS.md A3), and both of those translate to a Wasm adapter unchanged. A field like "kernel boot args" would not.

The honest caveat: whether a Wasm shim can claim full OCI Runtime Spec conformance is open, and it appears in section 5 as an open question rather than being asserted here.

## 4.2 Durable execution

| | |
|---|---|
| Standard | none; see PASS.md B5 and section 2 above (claimed, confirmed by search query 8) |
| Adapter today | external workflow orchestrator with deterministic replay |
| Second adapter | in-process transactional step log over a relational database |

**Why this is a real proof.** The execution models are opposite. The orchestrator model puts history on a separate server, requires workflow code to be deterministic so it can be replayed, and fails when the server is unreachable. The transactional step log has no server: durability is a database transaction committed alongside the step's own effect, and there is no replay determinism requirement at all because nothing is replayed.

What this forces the interface to do: express *step, idempotency key, checkpoint, resume point* and nothing more. Any concept that only makes sense with replay, such as "this call must be deterministic" or "worker registration", would be unimplementable by the second adapter and is therefore an orchestrator detail, not a durable-execution concept.

This pair carries extra weight because the orchestrator is currently down: the data directory is present and the server is not listening, while human-in-the-loop is designed around it (claimed, per PASS.md A6). An interface with a second adapter that needs no server is the difference between a design and a dependency.

## 4.3 Model access

| | |
|---|---|
| Standard | OpenAI-compatible chat completions (de facto, no ratified version; version unverified) |
| Adapter today | synchronous request/response gateway |
| Second adapter | asynchronous provider-native batch submission with claim-and-poll |

**Why this is a real proof.** Latency differs by four orders of magnitude, and more importantly the shape of the call differs: one returns a result, the other returns a ticket. A synchronous adapter can be cancelled by closing the connection; a batch job cannot, and cancelling it means a separate API call whose effect may be a partial refund rather than a stop.

What this forces the interface to do: model a completion as a *future with a claim ticket*, so that "get me a completion" and "get me a completion eventually and cheaply" are one interface rather than two. It also forces the budget concern to handle a spend that is committed at submission and reconciled hours later, which is a case a synchronous-only design never has to think about.

This pair is directly grounded in the substrate rather than hypothetical: batch already runs through a provider's native batch endpoint via gateway passthrough, deliberately not through the OpenAI-shaped batch route, which branches on three provider names and refuses the provider in question (claimed, per PASS.md A4). That is an interface mismatch that already happened once, in production, in the OpenAI-shaped standard itself. Building the second adapter first is how it does not happen again.

## 4.4 Agent runtime

| | |
|---|---|
| Standard | Agent Client Protocol (protocol version unverified; TypeScript SDK v0.21.1 seen in search results, claimed) |
| Adapter today | interactive ACP agent over JSON-RPC on stdio |
| Second adapter | single-shot non-interactive agent with no client callbacks |

**Why this is a real proof.** The interactive adapter has a live bidirectional session: it streams updates, asks the client for tool permission mid-turn, and can be cancelled mid-tool-call. The single-shot adapter has none of that. It takes a document, runs to completion or failure, and returns. There is no session to cancel, no permission callback, no stream.

What this forces the interface to do: make the *prompt turn with a stop reason* the unit, and make everything interactive optional. A permission callback that the interface requires is a callback the batch adapter cannot make, so it becomes an optional capability negotiated at session start rather than a precondition. Cancellation must then be expressible as "the result may be `cancelled` and the adapter may be unable to honour cancel promptly", which is exactly why the grace window in 2.1.3 is per-request rather than global.

## 4.5 State persistence

| | |
|---|---|
| Standard | none for the store; RFC 9162 for the integrity primitive, RFC 8785 for canonical bytes |
| Adapter today | hash-chained append-only line-delimited JSON, one file, one writer |
| Second adapter | content-addressed Merkle log with inclusion and consistency proofs over an object store |

**Why this is a real proof.** Verification cost and topology both change. The chained file verifies by rehashing from the beginning, needs the whole file present, and has exactly one reader-writer locality. The Merkle log verifies one record in O(log n) with a proof, lets a third party verify without holding the log, and is stored as immutable objects with no in-place append at all.

What this forces the interface to do: express integrity as *give me a proof about this record at this head*, not as *rehash the log*. A method named `rehash_all()` would be unimplementable against an object store of any size and is therefore a file-format detail. It also forces the retention design in 2.2.4, because a store where objects are immutable cannot redact in place, which is what surfaced the tombstone-preserving-digest mechanism.

The chain is preserved rather than discarded, which is what PASS.md B5 asks: the chain is the valuable idea, the file is not.

## 4.6 The remaining eleven capabilities

Every `cap-` skill in the manifest names two adapters, because design rule 3 admits no exception. The eleven not detailed above have second adapters that are meaningfully different but along narrower axes, for example a policy engine with a different policy language and the same decision API, or a second RFC 5545 evaluator with a different implementation lineage. They are listed in the manifest and each `cap-` skill must record how its pair differs in execution model, checked by row B2 in section 3.5. A pair that cannot fill in that field is a pair that proves nothing, and the author must find a different second adapter.

---

# 5. What could not be decided, and what evidence would decide it

Ten open questions. Each has a default so that work is not blocked, and each default is reversible at the cost named in the last column. This section is a required output, not an apology.

| # | Open question | Options | Measurement or experiment that decides it | Default until then |
|---|---|---|---|---|
| 1 | Does Dispatch adopt the full A2A task lifecycle or a subset? | (a) full lifecycle including `input-required` and `auth-required`; (b) a five-state subset with no interrupted states | Instrument 200 real dispatches and count entries into each interrupted state. If both are zero across a representative workload including approval flows, the subset is sufficient. Also: refetch the A2A specification, which was egress-blocked here, and confirm the state names and version. | Full lifecycle. The two interrupted states are permitted and may go unused; removing a state later is cheaper than adding one after adapters exist. |
| 2 | Which durable-execution adapter is primary? | (a) external orchestrator with replay; (b) in-process transactional step log | Measure, for a 50-step workflow under both: restart-to-resume latency, steps per second, and the number of separate processes that must be running for a workflow to make progress. The last number is the one that matters, given a data directory present with no server listening (claimed, per PASS.md A6). | The in-process transactional step log, because its answer to the last measurement is one. |
| 3 | Does the Merkle tree replace the hash chain or wrap it? | (a) replace, tree only; (b) wrap, keep the linear chain and add the tree | Measure full-verification wall time for the existing store, about 2,445 records across 308 runs (measured, per PASS.md A5), under both, and audit whether any existing consumer depends on strict linear order. | Wrap. The cross-run opening-digest property is already relied on and is cheap to keep. |
| 4 | What is the single-writer partition key? | (a) `run_id`; (b) document root; (c) one global writer | Measure write contention and, in the 308-run history (measured, per PASS.md A5), the frequency of edges that cross run boundaries. High cross-run edge frequency argues for a coarser partition. | `run_id`. It matches how work is already grouped and keeps the writer count equal to the concurrent run count. |
| 5 | Can the Wasm isolation adapter honestly claim OCI Runtime Spec conformance? | (a) require full OCI conformance from every isolation adapter; (b) declare the interface OCI-shaped with a documented conformance subset | Run the OCI runtime-tools validation suite against both adapters and record which assertions the Wasm shim cannot satisfy. If the failing set is small and unrelated to what the platform uses, (b) is honest. | (b), with the subset written down and every claim of conformance labelled claimed until the suite has run. Overclaiming conformance is worse than documenting a subset. |
| 6 | Does the Judge run inside or outside isolation? | (a) outside, the criterion never crosses the boundary; (b) inside a separate isolated unit with its own criterion access | Over 200 recorded dispatches, grep every payload the graded unit could read for the criterion string; and separately measure whether judging outside creates a serialisation bottleneck at the concurrency the platform actually reaches. | Outside. Design rule 6 is the stronger constraint and the bottleneck is hypothetical until measured. |
| 7 | Budget enforcement granularity | (a) pre-check before each metered call with a reservation lease; (b) periodic reconciliation with a tolerance band | Measure worst-case overshoot in currency units on a workload with high per-call cost variance, and measure the added latency of the pre-check per call. | (a). Scoped keys already terminate spend rather than record it (measured, per PASS.md A4), so the platform's existing behaviour is the pre-check model and matching it is the smaller change. |
| 8 | Is the correlation identifier a resource attribute or a span attribute? | (a) OTLP resource attribute set at dispatch; (b) span attribute on every span; (c) both | Emit both for one week across depth-3 trees and measure which survives the agent boundary and which is dropped or truncated by each collector in the path. Note that GenAI semantic conventions remain pre-stable with every `gen_ai.*` attribute at Development stability as of mid-2026 (claimed, from search), so this may need revisiting when they stabilise. | (a), the resource attribute, because it is the direct remedy for a measured failure (measured, per PASS.md A7 finding 1). |
| 9 | Do problem details need a structured retry policy or a boolean? | (a) `retryable` boolean only; (b) boolean plus `retry_after_s`; (c) full backoff policy object | Across the run history, count how many distinct failure types actually differ in the retry behaviour a caller should adopt. If the answer is two or three, a policy object is over-modelled. | (b). It is one extra optional field and it covers the rate-limit case that a boolean cannot. |
| 10 | Does work intake need both A2A and CloudEvents, or is one canonical? | (a) two first-class intake schemas; (b) one canonical envelope with translators | Implement the A2A-to-CloudEvents translator and measure whether any A2A field is lossy, in particular `contextId` grouping and any task-state field that has no CloudEvents equivalent. Lossless means (b). | (b), CloudEvents as the canonical envelope (version unverified) with A2A as a producer that maps into it. One canonical shape is what makes the P7 digest-equality check possible at all. |

## Two things deliberately not listed as open

They look like open questions and are not, because a rule already decides them.

- **Whether the Planner may call a model to improve its estimates.** It may not. Design rule 5 settles it and row C2 checks it. Measuring that estimates would improve does not reopen it; it would argue for a better cost table, which is data the Planner already consumes.
- **Whether a caller may opt out of a cross-cutting concern for a fast path.** It may not. Design rule 7 settles it, and `on_exceed` is a `const` in the request schema so the opt-out is not expressible. A caller who can decline one has found a hole.
