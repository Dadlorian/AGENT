---
name: build-adapter-pair
description: The discipline of shipping two adapters behind one capability interface, where the second is chosen because it breaks a different assumption than the first. Load it when picking a second implementation for a boundary, when writing the conformance suite both implementations must pass, when wiring the swap into CI, or when auditing whether a contract has been quietly shaped around whatever runs today. Also load it when a boundary has only one implementation, when someone says the thing behind it can be changed later, when a review asks whether a field belongs to the capability or to the thing behind it, or when a proposed alternative is a different product of the same shape.
---

# build-adapter-pair

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make swappability a tested property rather than an intention: every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing and that the interface is not shaped around its current implementation. | sourced | `F-b1-04`, `F-part-c-05`, `E-rule-b1-3` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing" |

## Entities

| Entity |
|---|
| `E-rule-b1-3` |
| `E-ask-item-c-4` |
| `E-capability-isolation` |
| `E-standard-oci-runtime-spec` |
| `E-adapter-firecracker-microvm` |
| `E-swap-candidate-gvisor` |
| `E-capability-state-persistence` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-object-store` |
| `E-finding-a7-2` |
| `E-finding-a7-3` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model (proposed shape; the seven axes are ours, from docs/decomposition.md section 4, not from PASS.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "differs_in_execution_model",
  "description": "Carried by an adapter pair. The pair is rejected unless at least one entry has today_value != second_value; a check cannot express that inequality in JSON Schema, so the tool asserts it.",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "axis",
      "today_value",
      "second_value"
    ],
    "properties": {
      "axis": {
        "enum": [
          "start_and_teardown_cost",
          "processes_required_for_progress",
          "result_or_claim_ticket",
          "prompt_cancellation",
          "locus_of_durability_and_verification",
          "unit_of_resource_granted",
          "replay_determinism_required"
        ]
      },
      "today_value": {
        "type": "string",
        "minLength": 1,
        "description": "The today adapter's value on this axis, stated as a property and never as a product name."
      },
      "second_value": {
        "type": "string",
        "minLength": 1,
        "description": "The second adapter's value on the same axis."
      },
      "measured": {
        "type": "boolean",
        "default": false,
        "description": "True only when the difference was observed in a run, not inferred from documentation."
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The pair exists at all: an interface ships with at least two adapters. One adapter is an implementation, not a boundary. | sourced | `F-b1-04` "Every interface ships with at least two adapters" |
| The second adapter's job is proof, not redundancy: it is chosen to prove the interface is not shaped around its current implementation. | sourced | `F-part-c-05`, `F-b1-04` "chosen to prove the interface is not shaped around its current implementation" |
| Both adapters satisfy the same named standard, and what the core imports is the interface, never either implementation. | sourced | `F-b1-02`, `F-b1-03` "The core imports interfaces, never implementations" |
| The swap touches configuration and adapters only. If swapping the implementation requires touching the core, the boundary is drawn wrong and the pair has found the defect it exists to find. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| The interface survives the swap and the implementation does not: the contract is stated as the capability plus its standard, so the adapter changes and the core does not. | sourced | `F-b3-18`, `F-b3-01` "the adapter changes and the core does not" |
| Proposed: every pair carries a non-empty differs_in_execution_model conforming to the shape in this skill's Shapes section, naming the axis and both adapters' values on it; an empty field, or identical values on every axis, rejects the pair. | proposed | - |
| Neither adapter obliges a caller to take a client library we wrote; if integration requires our SDK, the boundary is bespoke and the pair is proving the wrong thing. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| A pair is claimed until the swap has been executed and recorded; swappability is a tested property, not an intention, and the two labels are kept apart. | sourced | `F-b1-04`, `F-part-c-08` "Swappability is a tested property, not an intention." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Product names, versions and hostnames stay in the adapter rows. The interface, its invariants and its conformance suite name capabilities and standards only. | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the boundary as a capability plus the standard that governs it - 'a unit of work does X, per <standard>, version cited or unverified' - before naming any implementation, then check that today's implementation is only one of several ways to satisfy that sentence. | The Isolation row is the stated template for the whole table: the architecture names the capability and the standard, satisfies it with today's adapter, and when the workload changes the adapter changes and the core does not. | sourced | `F-b3-18`, `F-b1-03` "the adapter changes and the core does not" |
| 2 | Require two adapters per interface and treat the second as a proof obligation rather than a spare: it exists to prove the first is not load-bearing and that the interface is not shaped around its current implementation. | Design rule 3 makes swappability a tested property rather than an intention, and the ask names the second adapter's purpose as exactly that proof. | sourced | `F-b1-04`, `F-part-c-05` "Swappability is a tested property, not an intention." |
| 3 | Proposed: choose the second adapter by asking whether it breaks a different assumption, scoring candidates on the seven execution-model axes the Shapes section enumerates - start and teardown cost, how many separate processes must run for work to progress, whether a call returns a result or a claim ticket, whether cancellation can be honoured promptly, where durability and verification live, what unit of resource is granted, and whether replay determinism is required. Reject any candidate scoring identically to the first on every axis. | Proposed, from docs/decomposition.md section 4. A candidate with the same execution model can be swapped in while the interface stays shaped around that shared model, so the swap succeeds and demonstrates nothing. | proposed | - |
| 4 | Proposed: record the answer in the machine-readable differs_in_execution_model field defined under Shapes, naming the axis and both values. An empty field rejects the pair, and the author must find a different second adapter rather than argue for the one in hand. | Proposed, from docs/decomposition.md section 3.5 row B2. A judgement that lives only in prose cannot be checked, and the check is what lets this discipline fail. | proposed | - |
| 5 | Write one conformance suite against the interface and parameterise it over adapters: the suite imports the interface only, never an adapter type, and both adapters run the identical assertions with no per-adapter skips or per-adapter expected values. | The core imports interfaces, never implementations, so the contract, not either implementation, is what both adapters must satisfy. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| 6 | Give the conformance suite a deliberate breakage and run it: remove one interface guarantee from an adapter, or feed the suite a stub adapter that returns success for everything, and record which assertion fails. | A criterion nothing can fail is not a criterion, so a suite that has never been seen to fail is not yet evidence that either adapter conforms. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| 7 | Proposed: exercise the swap in CI rather than on paper. Run the full conformance suite once per adapter on every change, selecting the adapter by configuration alone with no code edit between runs, and fail the job if either run is skipped or reports zero behavioural assertions. | Proposed convention, for the reason the agentic-stack root contract records under F-a7-03: a swap job that runs but asserts nothing repeats a known failure in a new place. | proposed | `F-a7-03` |
| 8 | Proposed: audit the interface for shaping. List every field, operation and error in the contract and ask, for each, which adapter's vocabulary named it. Anything only the first adapter's model can honour is that adapter's detail leaking into the contract: express it in the capability's own terms, make it an optional negotiated capability, or delete it. | Proposed procedure. If an implementation cannot be swapped without touching the core, the boundary is drawn wrong, and a field only one adapter can honour is how that happens quietly. | proposed | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 9 | Check that integrating either adapter needs no client library we wrote, and fix the boundary before shipping the pair if it does. | If integration requires our SDK, a boundary is bespoke where a standard existed, and a pair behind a bespoke boundary proves only that we can swap our own code. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| 10 | Assert in the conformance suite that telemetry, policy, provenance and budget hold identically under both adapters, instead of being supplied by one adapter's implementation. | Those guarantees are applied by the platform and not requested by the caller, so they belong to the platform around the pair and must survive the swap unchanged. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| 11 | Proposed: label the pair claimed until the swap has actually been executed and its result recorded, and never upgrade the label by rewording the description. | Proposed convention. The standing constraint is to distinguish claimed from measured throughout, and a pair described as swappable is an intention until a run says otherwise. | proposed | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 12 | When no candidate differs on any axis, record it as an open question with the measurement that would decide it and a default, instead of shipping a same-shape pair that satisfies the count of two. | What could not be decided is a required output, not an apology. | sourced | `F-part-c-06` "A required output, not an apology." |
| 13 | Proposed: read references/execution-model-axes.md before scoring a candidate when the second adapter feels different but you cannot name the axis, or when reviewing a pair whose difference field reads as a vendor name rather than a property. | Proposed reference material. It holds the axis catalogue, the three-part wrapper test, and a worked pair written by knowledge-base entity id, all of which are too long for this table. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: the green-gate finding (F-a7-03) is stated in the agentic-stack root contract and is not restated here. What it adds for a pair: count the behavioural assertions that actually ran under each adapter, because a swap job can be green with none of them executed under either. | proposed | `F-a7-03` |
| Verify which adapter actually served the call at runtime rather than trusting the configuration that selected it: values written in the documented place have validated, reviewed correctly, and had no runtime effect. | sourced | `F-a7-04`, `E-finding-a7-3` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Correlation must ride on an explicit resource attribute set at dispatch, so the telemetry assertions in a conformance suite still hold under an adapter that mints its own root trace instead of inheriting one. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| Callers request a class, never a vendor: if selecting between the pair leaks a vendor name into caller code, the choice has escaped the adapter row and the swap is no longer a configuration change. | sourced | `F-a4-01`, `F-part-c-09` "Callers request a class, never a vendor" |
| A route in the substrate that is widely adopted can still be written around a fixed list of implementations: one such route branches only on three provider names and refuses a fourth provider actually in use. Check that the route your adapters both depend on admits both of them, instead of reading wide adoption as implementation-neutrality. | sourced | `F-a4-08` "route, which branches only on" |
| Name the property being preserved across the swap, not the container holding it: where the store changes, the chain is the valuable idea and should survive, the file is not. | sourced | `F-b5-05` "The chain is the valuable idea and should survive; the file is not" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/check_adapter_pairs.py --skills .claude/skills` (proposed tool, built alongside the first `cap-` skill in wave 3). For every `cap-` and `seam-` skill it asserts: exactly one adapter with role today, at least one with role second, a non-empty differs_in_execution_model naming an axis and both adapters' values, and at least one axis whose two values differ. |
| Expected | exit 0 with `pairs_checked > 0`, `single_adapter == 0`, `empty_axis == 0`, `same_model_pairs == 0` |
| Deliberate breakage | Add a `cap-` skill whose second adapter is a thin wrapper of the first: copy the today adapter's row, change only the entity id, and leave differs_in_execution_model empty. Then run it a second time with that field filled in by hand but carrying the same axis values as the first adapter. |
| Expected failure | First run exits 1 with `empty_axis == 1`, naming the skill and the adapter entity. Second run still exits 1 with `same_model_pairs == 1`, because no axis value differs - the case that counting two adapters cannot catch. Claimed: no `cap-` skill exists in wave 1 and the tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: `build-interface-versioning`, `cap-agent-runtime`, `cap-agent-runtime-implement`, `cap-capability-packaging`, `cap-capability-packaging-implement`, `cap-capability-registry`, `cap-capability-registry-implement`, `cap-document-validation`, `cap-document-validation-implement`, `cap-durable-execution`, `cap-durable-execution-implement`, `cap-errors`, `cap-errors-implement`, `cap-evaluation`, `cap-evaluation-implement`, `cap-human-interaction`, `cap-human-interaction-implement`, `cap-idempotency`, `cap-idempotency-implement`, `cap-identity`, `cap-identity-implement`, `cap-isolation`, `cap-isolation-implement`, `cap-mandate-broker`, `cap-mandate-broker-implement`, `cap-memory`, `cap-memory-implement`, `cap-model-access`, `cap-model-access-implement`, `cap-policy`, `cap-policy-implement`, `cap-provenance`, `cap-provenance-implement`, `cap-scheduling`, `cap-scheduling-implement`, `cap-state-persistence`, `cap-state-persistence-implement`, `cap-telemetry`, `cap-telemetry-implement`, `cap-tool-access`, `cap-tool-access-implement`, `cap-work-intake`, `cap-work-intake-implement`, `compose-agent-implement`, `compose-approval-implement`, `compose-improvement-loop-implement`, `compose-loop-implement`, `compose-operators-implement`, `compose-workflow-implement`, `core-document-implement`, `core-graph-implement`, `core-judge-implement`, `core-ledger-implement`, `core-planner-implement`, `seam-agent-ingress`, `seam-agent-ingress-implement`, `seam-dispatch`, `seam-dispatch-implement`, `seam-entry-envelope`, `seam-entry-envelope-implement`, `seam-state`, `seam-state-implement`, `xc-audit-trail-implement`, `xc-budget-implement`, `xc-compensation-implement`, `xc-correlation-envelope-implement`, `xc-correlation-implement`, `xc-enforcement-chain-implement`, `xc-idempotency-lease-implement`, `xc-identity-delegation-implement`, `xc-policy-gate-implement`, `xc-provenance-chain-implement`, `xc-tenancy-implement`, `xc-typed-errors-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does every capability admit a second adapter that differs in execution model, or do some admit only a narrower difference that still satisfies design rule 3? | For each capability, score its candidate second adapters on the axis list and record the widest true difference found. A capability where no candidate differs on any axis is recorded as an exception with its reason, and the count of such exceptions is the answer. | The pair is still required and the difference field records the narrowest true difference; a pair with no true difference is rejected rather than granted an exception. | `F-b1-04`, `F-part-c-05` "Every interface ships with at least two adapters" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/build-adapter-pair 2831cb4f |
