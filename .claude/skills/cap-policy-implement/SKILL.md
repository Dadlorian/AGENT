---
name: cap-policy-implement
description: How to build the Policy capability on this stack: what the rule sets that exist today already give you and what they do not, a first enforcing adapter that wraps the engine already provisioned behind one decide call, a second with a different execution model that evaluates in process against a typed entity model, the migration between them, where the call is wired so no path can skip it, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that asks for a decision, when adding a decision point or a rule bundle to the running system, when choosing where the policy-decided record is written, when a refusal arrives after money has been spent, or when a conformance run reports a non-zero spend delta on a denied dispatch.
---

# cap-policy-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-policy into something that runs here: one decide call, two engines behind it whose execution models differ, a policy-decided record on every decision, and consultation wired ahead of the first metered call rather than alongside it. | sourced | `F-a6-04`, `F-a5-05`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |

## Entities

| Entity |
|---|
| `E-capability-policy` |
| `E-not-running-policy-in-the-gate-path` |
| `E-provisioning-concern-policy` |
| `E-adapter-opa` |
| `E-swap-candidate-cedar` |
| `E-swap-candidate-any-policy-engine-with-a-decision-api` |

## Contract

### Shapes (JSON Schema 2020-12)

**PolicyConformanceReport (the counters the definition of done below asserts on, per adapter)** (sourced; sources: `T-t9-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:report:0.1",
  "title": "PolicyConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "decisions_taken",
    "spend_delta_micros",
    "rule_id_present",
    "decided_before_first_metered_call",
    "adapters_run"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "out-of-process-document-query",
        "in-process-typed-entity"
      ]
    },
    "decisions_taken": {
      "type": "integer",
      "minimum": 1
    },
    "spend_delta_micros": {
      "type": "integer",
      "minimum": 0,
      "description": "Ledger delta for the denied dispatch. Must be 0."
    },
    "rule_id_present": {
      "type": "boolean",
      "description": "True only if every policy-decided record carries a non-empty rule_id, allow rows included."
    },
    "decided_before_first_metered_call": {
      "type": "integer",
      "minimum": 0,
      "description": "Dispatches whose decision timestamp precedes the first metered call. Must equal decisions_taken."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    },
    "selected_by": {
      "const": "configuration",
      "description": "Recorded at runtime. A code edit between runs would not be a swap."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| the starting point is rule sets that already exist and decide nothing, so the first change is a call site, not a rule language. cap-policy states the recorded state (F-a6-04) and the decision contract (F-b4-04); this facet only builds against them, and treating this as a green-field capability would produce a second rule set beside one nobody consults. | sourced | `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |
| cap-policy fixes deterministic refusal before execution, not after spend (F-b4-04). The build consequence: the policy-decided record must be written before the call is issued rather than after the outcome is known - a record written afterwards can report a refusal but cannot cause one, which is the difference between the enforcement path and a report about it. | sourced | `F-b4-04` "Refusal is deterministic and happens before execution, not after spend" |
| Proposed: the input digest is computed over canonical bytes before evaluation, so two engines asked the same question agree on what the question was. Digesting a serialised form would make key ordering or whitespace look like a different request and break the cross-adapter agreement assertion for reasons that have nothing to do with policy. Research query: does RFC 8785 JSON canonicalization (already governing state-persistence and provenance per F-b5-05) also fix the canonical-bytes-before-digest rule for a policy DecisionRequest specifically, or is that extension this facet's own and still uncovered? | proposed | `F-b1-04` |
| Proposed: the call is wired into the platform's own call path at the registered decision points, never into each caller, and no request field can turn it off. A new entry kind or a new agent therefore inherits consultation by construction, because it reaches execution through the same path. Research query: cap-policy's own instructions row already hands decision placement to xc-policy-gate rather than owning it here (docs/decomposition.md); does xc-policy-gate or xc-enforcement-chain carry a kb-cited row this facet could point to instead of restating placement as its own invariant? | proposed | `T-t2-03`, `F-b4-01` |
| the correlation fields, the actor and the pinned policy_version are stamped onto the DecisionRequest by the platform and are not read from the caller's payload. agentic-stack states the correlation finding (F-a7-02); the consequence here is that a denied dispatch often produces no execution at all, so the decision record is the only place those fields will ever be written for it. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| build-definition-of-done already names the structurally-green trap (F-a7-03): a gate can pass while asserting nothing. The build consequence here: an engine that cannot serve a registered decision point declares that subset rather than answering allow. A documented conformance subset is honest; an engine that reports a decision it did not take is precisely the failure the pair exists to expose. | sourced | `F-a7-03` "A deterministic gate can be structurally green and mean nothing" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Inventory what already exists before writing anything: the rule sets provisioned for the policy concern, and the fact that nothing on the execution path consults them. Do not re-derive the contract; cap-policy states it. | The recorded state for policy in the gate path is that conformance checks exist; not wired into the enforcement path. The gap is a missing call, so an implementation that starts by authoring rules widens the gap it was meant to close. | sourced | `F-a6-04`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |
| 2 | Build the first enforcing adapter by wrapping the engine already provisioned for this concern behind decide: post the canonical DecisionRequest to its decision endpoint, read the JSON answer, and map it into the Decision shape. Introduce no new engine and no new store. | Proposed. The engine is already provisioned as the implementation of the policy concern (claimed, per PASS.md A5), so the cheapest correct first step adds the call and the mapping rather than a dependency, and it keeps the first migration step independently revertible. | sourced | `F-a5-05` "Rego / Open Policy Agent" |
| 3 | Stand up the decision-point registry next, starting with dispatch-admit, and refuse a request naming an unregistered point with the registered document-invalid problem rather than with a deny. Research query: is there a fetched (not search-only) source fixing 'dispatch-admit' as the first decision point to register, or is the starting point itself this repository's own design with only the refusal-shape half (cap-document-validation, cap-errors) already covered? | Proposed, following cap-policy's registration rule. A missing registration is a build error in the caller; answering it with a deny would make a wiring mistake look like a policy outcome and would be counted as one. | proposed | `F-b3-09`, `F-b4-07` |
| 4 | Write the policy-decided record at the moment of the decision, carrying rule_id, policy_version, input_digest and the correlation fields, for allow as well as deny, and only then issue the first metered call. Research query: does docs/decomposition.md's policy-decided record definition become citable once it is folded into a kb record, or does F-b4-04 cover only the before-execution ordering and not the specific field list (rule_id, policy_version, input_digest)? | Proposed. docs/decomposition.md rows P10 and X3 both assert on that record and on its timestamp relative to the first metered call, so recording after the fact makes the criterion unmeasurable even when the behaviour is right. | proposed | `F-b4-04` |
| 5 | Build the second adapter as an in-process evaluator over a typed entity model that denies by default, serving the same decide call with no wire hop. Research query: does a fetched read of the decision-API standard this capability adopts (F-a5-05) state a deny-by-default posture as a property of the standard itself, rather than of build-adapter-pair's generic swappability axis, which would source the deny-by-default claim specifically? | Proposed second adapter, per the manifest and the recorded swap-candidate column. It breaks a different assumption than the first: the first evaluates an open JSON document out of process and can be reached only over a boundary, while the second evaluates a schema-checked entity model inside the calling process. That is the axis the pair has to differ on for the swap to prove anything. | proposed | `F-b3-11`, `F-b1-04` |
| 6 | Wire the cross-cutting edges once, at the same place: stamp correlation onto the request, append the decision through the state seam, and hand a denial to the typed-failure path as the registered policy-denied problem. Give no call site a flag that skips any of the three. | Proposed wiring. cap-errors owns the failure shape (F-b4-07) and cap-policy owns the decision; what is left to this facet is that all three edges are attached at one point, because three separately attached edges are three separate places a new call site can forget one. | sourced | `F-b4-07`, `T-t2-03` "every cross-cutting concern are managed across the entire structure" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Consult at the call site, on the actual arguments, not once over the plan: cap-policy cites the finding that dynamic tool-switching, where agents select tools at runtime, defeats static policy. In implementation terms that means the tool-invoke point is inside the executor's call wrapper, not in the planner. | sourced | `X-end-to-end-062` "Dynamic tool-switching, where agents select tools at runtime, defeats static policy." |
| Attach the call by construction rather than by convention, so that there's no need for engineers to remember extra config steps: cap-policy states this as a practice, and here it means the decision is taken inside the shared dispatch and tool wrappers, where a new call site cannot be written without passing through it. | sourced | `X-cross-structure-024` "there's no need for engineers to remember extra config steps" |
| agentic-stack and build-definition-of-done state the configuration finding (F-a7-04): a configuration row can overlay and replace what a file declares, with the file itself validated and reviewed but never taking effect. The specific trap here: verify which bundle is actually serving by reading policy_version off a live Decision, not by reading the bundle file, because a rule set can be provisioned, reviewed and merged while the engine keeps serving the bundle it loaded at start. | sourced | `F-a7-04` "overlays and replaces `router_settings` on every gateway load" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-opa` | today | Part A records Rego / Open Policy Agent as the implementation of the policy provisioning concern (claimed), and PASS.md B3 names OPA as the adapter today for this capability. The first enforcing adapter wraps that engine: decide posts the canonical DecisionRequest to its decision endpoint over the local boundary and maps the returned JSON into a Decision, with the rule set loaded as a digest-addressed bundle. Nothing about the rule language changes; what changes is that something now asks. | Cannot answer without the engine reachable, so it inherits that process's availability, and cannot evaluate inside an isolated unit that has no path to it. Because it evaluates an open JSON document, it cannot itself tell a missing field from a field the rules never read, which is why the decision-point registry validates the input first. | cap-policy already records the two roles and the axis they differ on (F-b3-11, F-b1-04). What this facet adds is the procedure: keep decide, DecisionRequest and Decision byte-identical, select the engine by configuration only, run the identical P10 suite against each, and require the merged report to show adapters_run == 2, selected_by == configuration, and a declared conformance subset for any decision point an engine cannot serve. | claimed | `F-a5-05`, `F-b3-11`, `E-adapter-opa`, `E-provisioning-concern-policy` "Rego / Open Policy Agent" |
| `E-swap-candidate-cedar` | second | The second adapter is Cedar, the recorded swap candidate alongside any policy engine with a decision API, embedded as a library and evaluated in process against a typed entity model. Search-only research describes it as a declarative open-source authorization language and engine designed for fine-grained role-based and attribute-based policies, more strict and structured with emphasis on safety by default (deny by default). decide becomes a function call: entities and the request are marshalled from the same canonical DecisionRequest, and the returned determination is mapped into the same Decision. | Cannot express a decision over data outside its entity model, cannot evaluate the first engine's rules at all, and cannot be updated without redeploying the process that embeds it, where the first engine reloads a bundle in place. Its failure modes are the first engine's inverted, which is the point of the pair. | As above and owned jointly with cap-policy: configuration selects the engine, the suite is unchanged, and the merged report must additionally assert decisions_agree == true, meaning both returned the same effect and rule_id for the byte-identical request. Disagreement is a finding about the rule translation, not a licence to fork the interface. | claimed | `F-b3-11`, `X-cap-policy-004`, `E-swap-candidate-cedar`, `E-swap-candidate-any-policy-engine-with-a-decision-api` "Cedar · any policy engine with a decision API" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/policy/test.sh && python3 harness/policy/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 372cdc1: exit 0; last lines:   adapter=in-process-typed-entity cases=14 passed=14 decisions_taken=8 decided_before_first_metered_call=8 spend_delta_micros=0 rule_id_present=True subset=['dispatch.data_query'] product_hits=0 \| conformance PASSED: 28/28 cases, 2 binding(s) |
| Deliberate breakage | Append an engine-name comment (`# breakage: opa`) to the end of harness/policy/call.py, outside adapters/. Restored with `git checkout -- harness/policy/call.py`. |
| Expected failure | Measured by tools/measure.py at 372cdc1: exit 1; last lines:   FAIL both adapters failed \| passed 30, failed 8 |
| Status | measured |
| Evidence | `F-a6-04`, `F-b4-04` "not wired into the enforcement path" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-policy`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which of the two engines is primary once both exist? | Measure, under the P10 suite for each: evaluation latency at the tool-invoke point on the hot path, the number of separate processes that must be running for a decision to be answered, and how many registry decision points each can serve without a declared subset. The middle number is the one that decides it, given how much of what is defined here is currently not running. | The already-provisioned out-of-process engine is primary, because it is what exists and because it can serve the whole registry today; the in-process engine stays as the second implementation and as the path for units that cannot reach a decision endpoint. | `F-a5-05`, `F-b1-04` |
| How is one rule set kept equivalent across two engines with different languages? | Count, over the registry, how many decision points need a hand-written rule in each language, and measure how often the cross-adapter agreement assertion fails after a rule edit. A high failure rate after edits means the translation, not the interface, is the load-bearing thing. | Proposed: a single declarative rule table as the source, compiled to both languages, with the agreement assertion in the conformance run as the check that the compilation is faithful. Reversible to hand-written pairs at the cost of a divergence per edit. | `F-b3-11`, `F-b1-04` |
| Is the policy-decided record written through the state seam on the run's own log, or to a separate decision store? | Measure the added write latency at the decision points on the hot path, and count how many audit questions need a decision and a dispatch in one ordered log rather than joined after the fact. | Proposed: through the state seam onto the same append-only log, so the ordering assertion that a decision precedes the first metered call is a comparison within one log rather than across two clocks. | `F-b4-04` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-policy 2831cb4f, 2026-09-03 |
