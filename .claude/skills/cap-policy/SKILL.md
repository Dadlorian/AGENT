---
name: cap-policy
description: The ideal state of the Policy capability: one decision API that takes a structured request and returns a deterministic allow or deny together with the rule that decided it, before anything is spent. Load it when deciding what a refusal means and when it is taken, when adding a decision point or a rule set, when choosing or judging a policy engine, when a review asks whether the rule language has leaked into the interface, or when someone proposes letting a caller skip the check on a fast path. Also load it when a refusal arrives after work has already run, when a denial comes back as a message rather than a typed answer, when a decision cannot be replayed because nothing recorded which rules were active, or when the same allow-or-deny logic is about to be written a second time inside a caller.
---

# cap-policy

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for refusal: a structured request in, a deterministic allow or deny plus the rule that decided it out, taken before execution rather than after spend, so that the rule language and the engine behind it stay adapter detail. | sourced | `F-b4-04`, `F-b3-11`, `E-concern-policy`, `E-capability-policy` "Refusal is deterministic and happens before execution, not after spend" |

## Entities

| Entity |
|---|
| `E-capability-policy` |
| `E-concern-policy` |
| `E-standard-rego-opa` |
| `E-adapter-opa` |
| `E-swap-candidate-cedar` |
| `E-swap-candidate-any-policy-engine-with-a-decision-api` |
| `E-not-running-policy-in-the-gate-path` |
| `E-provisioning-concern-policy` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-rego-opa` | unverified | unverified | https://www.openpolicyagent.org/docs/policy-language | `F-b3-11`, `X-cap-policy-002`, `E-standard-rego-opa` |

- `E-standard-rego-opa` version note: unverified. The recorded row names a declarative policy language paired with a decision API rather than a ratified specification, and the research records for this capability are search-only: no specification text was fetched from this environment, so no version string is asserted.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| decide (proposed operation set; the recorded standard is a language plus a decision API, not a set of calls) | a DecisionRequest: the named decision point, the subject, the action, the resource, the run context, and the pinned policy_version the request must be evaluated against | a Decision carrying effect allow or deny, the rule_id that decided it, the policy_version it was evaluated under, and the digest of the input; the same request under the same version always yields the same answer | proposed | `F-b4-04`, `X-cross-structure-031` |
| activate (proposed) | a policy bundle and its digest | the digest now serving as policy_version, after which every decision names it; the previous version stays resolvable so an old decision can still be explained | proposed | `F-b4-04` |
| explain (proposed) | a recorded decision, by its input digest and policy_version | the rule that decided and the inputs it read, recomputed by re-evaluating the pinned version rather than by trusting a stored narrative; this is the read an auditor and a planner both need | proposed | `F-b4-04` |
| register_decision_point (proposed) | a decision point name and the JSON Schema its resource and context must satisfy | the point admitted into the registry; a decision requested at an unregistered point is refused as a conformance failure rather than evaluated against an assumed shape | proposed | `F-b3-09` |

### Shapes (JSON Schema 2020-12)

**DecisionRequest (proposed shape; the full schema, the decision-point registry and the engine-selection criteria are in references/policy-decision.md)** (proposed; sources: `F-b4-04`, `X-cross-structure-031`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:request:0.1",
  "title": "DecisionRequest",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "decision_point",
    "subject",
    "action",
    "resource",
    "context",
    "policy_version"
  ],
  "properties": {
    "decision_point": {
      "type": "string",
      "description": "A registered place a decision is taken. An unregistered name is a conformance failure, not a default-allow."
    },
    "subject": {
      "type": "object",
      "description": "Who is asking, in the actor shape cap-identity owns."
    },
    "action": {
      "type": "string"
    },
    "resource": {
      "type": "object",
      "description": "What is acted on. Validated against the decision point's declared schema before evaluation."
    },
    "context": {
      "type": "object",
      "required": [
        "run_id",
        "root_dispatch_id"
      ],
      "properties": {
        "run_id": {
          "type": "string"
        },
        "root_dispatch_id": {
          "type": "string"
        }
      }
    },
    "policy_version": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest of the activated bundle. Pinned, so the decision is replayable."
    }
  }
}
```

**Decision (proposed shape; what crosses the interface, whichever engine served it)** (proposed; sources: `F-b4-04`, `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:decision:0.1",
  "title": "Decision",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "effect",
    "rule_id",
    "policy_version",
    "decision_point",
    "input_digest",
    "decided_at"
  ],
  "properties": {
    "effect": {
      "enum": [
        "allow",
        "deny"
      ]
    },
    "rule_id": {
      "type": "string",
      "minLength": 1,
      "description": "The rule that decided. Required for allow as well as deny, so an allow is as attributable as a refusal."
    },
    "policy_version": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "decision_point": {
      "type": "string"
    },
    "input_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "decided_at": {
      "type": "string",
      "format": "date-time"
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1",
      "description": "Required when effect is deny. The failure shape and the registered type belong to cap-errors."
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "effect": {
            "const": "deny"
          }
        },
        "required": [
          "effect"
        ]
      },
      "then": {
        "required": [
          "problem"
        ]
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The contract this capability must deliver is one sentence: refusal is deterministic and happens before execution, not after spend. | sourced | `F-b4-04`, `E-concern-policy` "Refusal is deterministic and happens before execution, not after spend" |
| The recorded row names the swap candidates for this capability as any policy engine with a decision API, so the capability is the decision API and the rule language is adapter detail; an interface that only one language can satisfy is drawn around an engine rather than around a decision. | sourced | `F-b3-11`, `E-capability-policy`, `E-swap-candidate-any-policy-engine-with-a-decision-api` "any policy engine with a decision API" |
| The shape that decision API takes in the prior art is document in, decision out: an engine evaluates the input against the specified policies to return an access decision in JSON, which is why this interface passes a structured request and receives a structured answer rather than exposing an evaluation session. | sourced | `X-cross-structure-031`, `X-cap-policy-002` "evaluates the input against the specified policies to return an access decision in JSON" |
| The recorded language of the standard is declarative and structured on both sides: it is designed to evaluate structured data such as JSON inputs and return structured decisions, so a decision that has to be parsed out of prose is outside the standard this capability names. | sourced | `X-cap-policy-002`, `E-standard-rego-opa` "designed to evaluate structured data such as JSON inputs and return structured decisions" |
| What runs today is defined and off the path: conformance checks exist; not wired into the enforcement path. This capability is therefore adopted into the path rather than migrated within it, and a check that exists is not evidence that a decision is taken. | sourced | `F-a6-04`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |
| Proposed: decide is a pure function of the DecisionRequest and the pinned policy_version. No clock read, no network fetch, no model call and no ambient state may enter evaluation, because a decision that can differ between two evaluations of the same input is not deterministic and cannot be replayed by an auditor. | proposed | `F-b4-04` |
| Proposed: every Decision carries a non-empty rule_id, for allow as well as deny, and every decision is recorded as a policy-decided record naming it. docs/decomposition.md row P10 asserts on exactly that record; an unattributed allow makes the question why was this permitted unanswerable while leaving the refusal path looking healthy. | proposed | `F-b4-04`, `F-a6-04` |
| Proposed: the resource and context of a request are validated against the decision point's declared schema before evaluation. cap-document-validation owns that contract and the dialect that governs it (F-b3-09); the consequence here is that an unregistered or unvalidated input is refused rather than evaluated against a shape the rule author only assumed. | proposed | `F-b3-09` |
| Proposed: a deny leaves this interface as the registered policy-denied problem produced by cap-errors, which owns the typed failure shape and its closed registry (F-b4-07). This capability mints no failure object of its own, so a caller that already reads typed failures needs no new parser for a refusal. | proposed | `F-b4-07` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the rule source text and the engine's evaluation trace do not cross the interface. A caller receives effect, rule_id, policy_version and input_digest, so rewriting a rule set is not a breaking change to anything that reads a decision. | proposed | `F-b3-11` |
| Proposed: there is no advisory mode, no dry-run flag and no bypass on the enforcement path. agentic-stack states design rule 7 as a test (F-b4-01): the platform applies policy rather than the caller requesting it, so a request field that could turn the decision off would be the hole that rule names. | proposed | `F-b4-01`, `T-t2-03` |
| Proposed: the engine, its rule language and its version never appear in a Decision. A swap has to be invisible to every reader of a decision, or the interface has leaked the thing behind it. | proposed | `F-b3-11` |
| Proposed: the criterion a result will be judged against never travels in a DecisionRequest's resource or context object, and no decision point is registered whose schema would admit one. agentic-stack states design rule 6 (F-b1-07); the consequence here is that resource and context are open objects, which makes a decision request the easiest place to hand a graded agent the rule it is graded by, so a registered schema that carries a grading criterion is a conformance failure rather than a policy input. | proposed | `F-b1-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from the two recorded lines and design nothing before you have both: the governing standard is a declarative policy language paired with a decision API, and the contract is that refusal is deterministic and happens before execution, not after spend. | The row fixes what governs the boundary and the concern row fixes what it must deliver. A decision API designed without the timing clause becomes a reporting API, which is what an after-the-fact check is. | sourced | `F-b3-11`, `F-b4-04` "Refusal is deterministic and happens before execution, not after spend" |
| 2 | Define the interface as one call, decide(DecisionRequest) returning Decision, and put nothing engine-shaped in it: no rule handles, no partial evaluation objects, no query strings in a rule language. | The prior art for this boundary is a query with a JSON input that evaluates the input against the specified policies to return an access decision in JSON. Anything richer than document in, decision out can only be implemented by engines shaped like the first one. | sourced | `X-cross-structure-031`, `F-b3-11` "evaluates the input against the specified policies to return an access decision in JSON" |
| 3 | Register every decision point with a name and a declared JSON Schema for its resource and context, and refuse a decision requested at an unregistered point instead of evaluating it. | Proposed. A rule author writes against a shape; if the shape is only implied, a caller that omits a field gets an allow from a rule that never fired rather than an error, and nothing in the record shows the difference. cap-document-validation owns the validation contract this leans on. | proposed | `F-b3-09` |
| 4 | Pin the policy bundle: activate a bundle by digest, put that digest in every DecisionRequest, and copy it onto every Decision and every policy-decided record. | Proposed. Determinism is a claim about a fixed rule set, so a decision that does not name the version it was taken under cannot be re-evaluated later, and a bundle that changed mid-run turns one run into two policy regimes with no way to tell which decisions belong to which. | proposed | `F-b4-04` |
| 5 | Require rule_id on both effects and record a policy-decided entry for every call, not only for denials. | Proposed, and it is what docs/decomposition.md row P10 asserts on. Recording only refusals makes the allow path invisible, and an enforcement point that has silently stopped consulting policy looks exactly like one where nothing was denied. | proposed | `F-a6-04` |
| 6 | Return a denial as the registered policy-denied problem with the rule_id on it, and define no failure object here. | Proposed composition. cap-errors already fixes the typed failure shape and holds the closed registry (F-b4-07); a second refusal format would be one more thing every caller has to learn for the case that matters most. | proposed | `F-b4-07` |
| 7 | Judge a candidate engine on two properties before any feature comparison: that its decisions are deterministic, and that it can be consulted before resource consumption begins. | The requirement in the prior art is that policy decisions must be deterministic and evaluated before resource consumption begins. An engine that is expressive but consulted after the first metered call fails the contract however good its language is. | sourced | `X-cap-policy-006`, `F-b4-04` "Policy decisions must be deterministic and evaluated before resource consumption begins" |
| 8 | Stop at the decision. Where it is consulted, and the rule that it must precede the first metered call, belong to xc-policy-gate; do not fold placement into this interface. | Merging the two is what produced the recorded state where conformance checks exist; not wired into the enforcement path. Defining a decision and placing it are separately checkable, and only one of them was ever done here. | sourced | `F-a6-04`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |
| 9 | Proposed: open references/policy-decision.md when you need the full request and decision schemas, the decision-point registry format, or the engine-selection criteria table. This skill body is enough to judge an implementation without it. | Proposed, progressive disclosure. The registry format and the criteria table are long material, and inlining them would make the contract longer than the decision it governs. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Evaluate at the moment of the call, on the actual arguments, rather than once at plan time: dynamic tool-switching, where agents select tools at runtime, defeats static policy. A decision taken over an intended plan says nothing about the call that was finally made. | sourced | `X-end-to-end-062` "Dynamic tool-switching, where agents select tools at runtime, defeats static policy." |
| Keep the decision out of the entry protocol. Interoperability protocols can carry governance messages as payloads but cannot interpret, validate, or enforce their governance semantics, so a platform that trusts an inbound field claiming a check already happened has no decision of its own. | sourced | `X-entry-composition-059` "cannot interpret, validate, or enforce their governance semantics" |
| Apply the decision once for everything rather than per caller: compose cross-cutting behaviors—telemetry, safety filters, caching, policy enforcement—once and apply them to every agent consistently. Policy written into each agent is policy that a new agent silently lacks. | sourced | `X-cross-structure-026` "policy enforcement—once and apply them to every agent consistently" |
| Make consultation automatic rather than remembered, so that there's no need for engineers to remember extra config steps. Any design where a new call site has to opt in produces coverage that decays with every addition, and the gap is invisible until it is exploited. | sourced | `X-cross-structure-024` "there's no need for engineers to remember extra config steps" |
| Proposed: verify which bundle digest is actually serving decisions at runtime rather than reading the file that declares it. agentic-stack states the configuration finding (F-a7-04); the consequence here is that a rule set reviewed and merged is not a rule set in force, and policy_version on a live Decision is the only evidence that it is. | proposed | `F-a7-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-opa` | today | The recorded adapter-today column for this capability is OPA under the Rego / OPA standard, and Part A records Rego / Open Policy Agent as the implementation of the provisioning policy concern (claimed). It serves decide as an out-of-process query: the caller posts a JSON input document to a decision endpoint and reads a JSON decision back, with the rule set loaded as a bundle. Research for this capability is search-only and records it as an open-source policy engine that evaluates authorization decisions using Rego policies decoupled from application code, reaching CNCF graduated status on January 29, 2021. | Cannot be evaluated inside the calling unit without shipping the engine with it, so an isolated unit with no egress reaches it only through the boundary that already exists. Its evaluation is open-world over arbitrary JSON, so the engine does not itself check that the input matched the shape the rule author assumed; that check has to be the registry's. It is also what the recorded state says is defined and not in the enforcement path today. | Keep DecisionRequest and Decision unchanged and select the serving engine by configuration only, with no code edit between runs. agentic-stack already states design rule 3 as a test (F-b1-04): the second adapter exists to prove the first is not load-bearing. What is new here is the axis, recorded in the second row; cap-policy-implement owns the step-by-step procedure and the per-adapter conformance subsets. | claimed | `F-b3-11`, `F-a5-05`, `X-cap-policy-001`, `E-adapter-opa`, `E-provisioning-concern-policy` "Rego / OPA \| OPA" |
| `E-swap-candidate-cedar` | second | Cedar is the recorded swap candidate, alongside any policy engine with a decision API. Search-only research describes it as a declarative open-source authorization language and engine designed for fine-grained role-based and attribute-based policies, evaluated in process against a typed entity model, more strict and structured with emphasis on safety by default (deny by default), and built around application-level authorization rather than general document evaluation. | Cannot express a decision over data that does not fit its entity model, and cannot serve rules written in the first adapter's language at all. It is the narrower engine of the two, and that is what makes it a test: anything the interface needs which only the general-purpose evaluator can provide shows up as a decision the second adapter cannot take. | The axis the pair is chosen for is the execution model, not the vendor: an out-of-process query that evaluates an open JSON document under a general-purpose language, against an in-process evaluation over a schema-checked entity model that denies by default. A suite that passes over both cannot have been shaped around either one's evaluation style. Run the identical P10 conformance suite against each with the engine selected by configuration; the merged report must show adapters_run == 2 and identical effect and rule_id for the byte-identical request. | claimed | `F-b3-11`, `X-cap-policy-004`, `X-cap-policy-005`, `E-swap-candidate-cedar` "Cedar · any policy engine with a decision API" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P10, made precise and run over the adapter pair above: `python3 tools/conformance/policy_decision.py --adapter today --adapter second --entry examples/end-to-end/entries/human.json --deny-rule deny-external-tool-without-mandate --report out/policy.json` (proposed tool, built with the first enforcing adapter), the engine selected by configuration with no code edit between runs. Per adapter it submits a dispatch that a policy rule denies and asserts `spend_delta_micros == 0` for that dispatch, that a `policy-decided` record exists carrying a non-empty `rule_id`, and that the result is `state: "rejected"` with problem type `urn:agentic:problem:policy-denied`. Across adapters it asserts `adapters_run >= 2` and `decisions_agree == true`, meaning both returned the same effect and the same rule_id for the byte-identical DecisionRequest. |
| Expected | exit 0 with, per adapter, `spend_delta_micros=0`, `rule_id` non-empty, `state=rejected`, `problem_type=urn:agentic:problem:policy-denied`, followed by `adapters_run=2` and `decisions_agree=true`. |
| Deliberate breakage | Move the policy consultation to after the first metered call, changing nothing else, and re-run the same command. |
| Expected failure | exit 1 with `spend_delta_micros > 0` for both engines and the `policy-decided` record timestamped after the first metered call, while `state=rejected` and the problem type still pass, which is the useful part: the refusal still looks correct and the money is already gone. This is the check that would have caught policy being defined and not wired into the enforcement path. Claimed: nothing consults a decision on the enforcement path today and the conformance tool is not written, so neither the criterion nor the breakage has been run here. |
| Status | claimed |
| Evidence | `F-b4-04`, `F-a6-04` "Refusal is deterministic and happens before execution, not after spend" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-adapter-pair`, `build-skill-authoring`, `cap-errors`, `cap-document-validation`

Used by: `cap-mandate-broker`, `cap-policy-implement`, `cap-policy-use`, `xc-enforcement-chain`, `xc-policy-gate`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does this adapter pair differ enough in execution model to prove the interface, given that docs/decomposition.md section 4.6 places it among the pairs that differ along narrower axes, a policy engine with a different policy language and the same decision API? | Run the P10 suite under both and classify every assertion that fails: a failure caused by the language is a syntax difference and proves nothing, while a failure caused by open-document versus typed-entity evaluation, or by out-of-process versus in-process consultation, is the interface being tested. If every failure is of the first kind, the pair must be replaced. | Keep the pair and record the axis as out-of-process open-document evaluation against in-process schema-checked evaluation that denies by default, which is a difference in where and how evaluation runs rather than in vendor. | `F-b3-11`, `F-b1-04` |
| Is a decision request an open document, or a typed entity model with a declared schema per decision point? | Count, across the decision points the platform actually needs, how many require an attribute that a typed entity model cannot carry. If that count is zero, the typed model is the stronger contract and the registry becomes the schema rather than a guard in front of it. | An open document with a declared schema per registered decision point, because it is the shape both candidate engines can serve and it is reversible toward the typed model, where the reverse is not true. | `F-b3-09`, `F-b3-11` |
| Is rule_id an identifier a policy author assigns, or a digest of the rule text? | Across a period of rule edits, count how many refusals would change their rule_id under each option without any change to which requests are denied, and how many audit questions need to distinguish the rule from its current wording. | An author-assigned identifier, carried alongside policy_version so the exact text is still recoverable. A digest changes on every reformatting, which would make a stable refusal look like a new one to anything counting refusals by rule. | `F-b4-04` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-policy 2831cb4f, 2026-09-03 |
