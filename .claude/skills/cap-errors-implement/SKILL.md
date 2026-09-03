---
name: cap-errors-implement
description: How to build the Errors capability on this stack: the first adapter, a second one with a different execution model, what to do when there is nothing to migrate from, how the budget, policy, identity, idempotency and correlation guarantees land in a failure body, and a definition of done with the breakage that makes it fail. Load it when you are writing or reviewing the code that produces a failure, when wiring a capability adapter's failure path, when adding an edge component that answers on behalf of a service, when a cross-cutting concern needs somewhere to report a refusal, or when a conformance run reports untyped failures and you have to find which adapter produced them.
---

# cap-errors-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-errors into something that runs here: two adapters behind one failure shape, every untyped failure path converted, and every cross-cutting refusal landing on a registered problem type rather than in a log line. | sourced | `F-b4-07`, `F-a6-06`, `E-adapter-errors-absent` "Typed and machine-readable. Never parsed from prose" |

## Entities

| Entity |
|---|
| `E-capability-errors` |
| `E-concern-errors` |
| `E-standard-rfc-9457-problem-details` |
| `E-adapter-errors-absent` |
| `E-not-running-typed-errors` |

## Contract

### Shapes (JSON Schema 2020-12)

**ErrorsConformanceReport (proposed shape; the counters that the definition of done below asserts on)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:errors:conformance-report:0.1",
  "title": "ErrorsConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "per_adapter"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 2,
      "description": "Distinct adapters exercised. Fewer than two means the swap was not tested."
    },
    "per_adapter": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "adapter",
          "responses_checked",
          "untyped",
          "unregistered_types",
          "wrong_media_type"
        ],
        "properties": {
          "adapter": {
            "type": "string",
            "description": "Adapter entity id, so a failure names one implementation and not the capability."
          },
          "responses_checked": {
            "type": "integer",
            "minimum": 0
          },
          "untyped": {
            "type": "integer",
            "minimum": 0,
            "description": "Failures the adapter could not type. Non-zero means this adapter is not conformant."
          },
          "unregistered_types": {
            "type": "integer",
            "minimum": 0
          },
          "wrong_media_type": {
            "type": "integer",
            "minimum": 0
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two adapters differ on processes_required_for_progress, in the sense build-adapter-pair defines. The first raises and renders the problem inside the failing process; the second is a separate process on the response path that never enters the service. A pair that agrees on that axis proves nothing and is rejected. | proposed | `F-b1-04` |
| Proposed: the swap is configuration. No caller, and no code in the core, selects between the adapters or branches on which one answered; agentic-stack states design rule 1 (F-b1-02) and this is its consequence for the failure path. | proposed | `F-b1-02` |
| Proposed: there is nothing to migrate. Typed errors are recorded as Absent, so the work is conversion of untyped failure paths rather than translation of an existing error object, and the count of converted paths is the progress measure. | proposed | `F-a6-06` |
| A budget refusal lands on the budget-exhausted row because exceeding a ceiling terminates the unit, not the platform: the problem body is what tells the caller which of the two happened. | sourced | `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| A policy refusal lands on the policy-denied row carrying rule_id, and it is emitted before any spend, because refusal is deterministic and happens before execution, not after spend. | sourced | `F-b4-04` "Refusal is deterministic and happens before execution, not after spend" |
| A replayed externally-triggered action with the same key and a different body lands on the idempotency-conflict row, because every externally-triggered action is safe to replay and a conflict is the one case where that promise cannot be kept silently. | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| Proposed: none of these wirings is optional and none is requested by the caller. agentic-stack states the no-opt-out rule (F-b1-08, F-b4-01); what this adds is that the failure body is where a caller would first notice an opt-out, because a declined guarantee has no registered type to report under. | proposed | `F-b4-01` |
| Proposed: every claim in this skill is claimed until the conformance report exists, recorded the way build-evidence-record requires. No adapter here has been run, so nothing about their behaviour may be labelled measured. | proposed | `F-part-c-08` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the first adapter in-process: one library that owns the closed registry, constructs a Problem only from a registered suffix, and refuses construction otherwise. Do not let handlers assemble the object field by field. | Proposed. If the registry is data the library enforces rather than a table in a document, an unregistered type cannot reach a client at all, which turns the registry invariant in cap-errors into a compile- or construct-time failure instead of a conformance-run finding. | proposed | - |
| 2 | Enumerate every failure path in what runs, map each to a registry row, and convert them one at a time. Where the failure has no row, route it through classify to adapter-unavailable and increment the untyped counter rather than inventing a suffix. | Typed errors are recorded as Absent, so this is conversion from nothing rather than migration from an existing shape; the counter is what stops an unconverted path from looking finished. | sourced | `F-a6-06`, `E-not-running-typed-errors` "Typed errors \| Absent" |
| 3 | Build the second adapter as a filter at the edge that maps an upstream failure into the problem-details body without the service being touched, and record its execution-model difference against the first as build-adapter-pair requires. | The second exists to prove the first is not load-bearing: an in-process library and an edge filter disagree about how many processes must run for a failure to be produced and about how much context is available at the point of production, which is what makes the pair evidence rather than a spare. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 4 | Give the second adapter the failing case honestly: it can only see the wire response, so it cannot populate rule_id, causes or the raise-site detail unless the service already emitted them. Declare that gap in the pair's record instead of widening the interface to close it. | Proposed. Widening the contract so both adapters can satisfy every member is how an interface gets shaped around its implementations; the honest alternative is a declared gap that the conformance suite asserts on. | proposed | `F-meta-04` |
| 5 | Wire the cross-cutting refusals to their rows: budget to budget-exhausted with the spend that would have crossed the ceiling, policy to policy-denied carrying rule_id and emitted before any spend, identity to identity-untrusted, idempotency to idempotency-conflict. | Each concern already has a contract; the failure body is where a caller observes it. Refusal is deterministic and happens before execution, not after spend, so a policy problem emitted after a metered call is the wrong object at the wrong time. | sourced | `F-b4-04`, `F-b4-02`, `F-b4-03`, `F-b4-08` "Refusal is deterministic and happens before execution, not after spend" |
| 6 | Proposed: copy the explicit correlation attribute set at dispatch onto every problem body, and assert in the conformance suite that it survives both adapters. | Proposed wiring. agentic-stack states the correlation finding (F-a7-02); the consequence here is that the edge-filter adapter mints its response outside the failing process, so a body that inherits nothing is exactly the case that finding predicts. | proposed | `F-a7-02`, `F-b4-06` |
| 7 | Write one conformance suite against the capability and parameterise it over adapters, selecting the adapter by configuration with no code edit between runs, and emit the report shape defined above. | The core imports interfaces, never implementations, so the suite must import the capability and never an adapter type; a per-adapter branch inside the suite would test two things and prove neither swappable. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| 8 | Verify at runtime which adapter actually answered, rather than trusting the configuration that selected it, by asserting the report's adapter field against a marker the running adapter emits. | agentic-stack already states the configuration finding (F-a7-04): values written to the documented place validated, reviewed correctly, and had no runtime effect. What this step adds: assert the report's adapter field against a marker the running adapter emits rather than against the binding record, because a swap job that never left the first adapter reports two green runs of the same code. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 9 | Apply build-definition-of-done: run the definition of done below and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: convert the failure paths of the noisiest adapter first. The untyped counter is a whole number, so the fastest route to a meaningful conformance number is the component that produces the most untyped failures, not the one that is easiest to edit. | proposed | - |
| Proposed: keep the registry in one place that both adapters read. An edge filter with its own copy of the type list is a second registry, and two registries drift in the direction of whichever one is easier to edit. | proposed | `X-cap-errors-003` |
| Proposed: when an existing library already speaks the older RFC 7807 member set, treat it as an adapter detail and normalise on the way out rather than accepting the older shape into the contract, since RFC 7807 has been succeeded by RFC 9457. | proposed | `X-cap-errors-005` |
| Proposed: give the edge filter a deliberate pass-through test. Its most likely defect is silently forwarding an upstream body it did not understand, which is indistinguishable from success unless a fixture upstream returns something untyped on purpose. | proposed | - |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-errors-absent` | today | Nothing yet: the recorded adapter for this capability is absent, so the in-process problem-details library described in this skill is the first adapter to exist rather than an incumbent to replace. | Cannot be cited as evidence of anything running; there is no measured behaviour to inherit, and every failure path in the current system is untyped by default. | Introduce the in-process library behind the capability, convert failure paths to registry rows one at a time, and count the remainder as untyped until conversion completes. | claimed | `F-b3-13`, `F-a6-06` "RFC 9457 problem details \| *absent*" |
| `E-swap-candidate-gateway-problem-filter` | second | Proposed adapter, and a proposed entity id: no swap-candidate entity exists for this capability because the recorded swap-candidate column is the instruction to adopt the RFC directly. It is a filter at the edge that maps an upstream failure into the problem-details body and media type without the service being touched. | Cannot see raise-site context: it holds only the wire response, so rule_id, causes and a detail written at the point of failure are unavailable unless the service already emitted them. It also needs a separate process on the response path, where the first adapter needs none. | Select the adapter by configuration only, run the same conformance suite against each, and assert adapters_run is at least two with a runtime marker proving the second actually served. | claimed | `F-b3-13`, `F-b1-04` "— adopt the RFC directly" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P12, extended with the swap: `python3 tools/conformance/errors_fuzz.py --adapter in-process --iterations 250 --report out/errors-a.json` then the same command with `--adapter edge-filter --report out/errors-b.json`, the adapter chosen by configuration with no code edit between runs. Both reports must validate against the ErrorsConformanceReport shape above and assert, per adapter, media type application/problem+json on every failure response, every type value present in the registry in docs/decomposition.md section 2.1.6, `responses_checked > 200`, and `untyped == 0`. |
| Expected | both runs exit 0; the merged report shows `adapters_run == 2` and, for each adapter, `untyped == 0`, `unregistered_types == 0`, `wrong_media_type == 0`, `responses_checked > 200` |
| Deliberate breakage | Make the edge-filter adapter pass one upstream failure through unchanged, so that path answers with a plain-text HTTP 500. Leave the in-process adapter untouched. |
| Expected failure | The edge-filter run exits 1 with `untyped == 1` and `wrong_media_type == 1`, naming that adapter and that path, while the in-process run still exits 0 with `untyped == 0`. Singling out one adapter is the point: a suite that fails both, or neither, has not tested the swap. Claimed: typed errors are absent, neither adapter exists and the fuzz tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-04`, `F-a6-06` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-errors`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The second adapter has no entity in the knowledge base. E-swap-candidate-gateway-problem-filter is a proposed id minted here because the schema requires an adapter entity and the recorded swap-candidate column for Errors is an instruction rather than a candidate list. Should it become a real entity? | Whether a knowledge-base rebuild that derives swap candidates from sources other than the B3 table produces an entity for this filter. Until then the id resolves nowhere and a reader must take this row as proposed. | Keep the proposed id, keep the row marked claimed, and do not list the id under entities so the validator's entity check is not silently satisfied by an invented record. | `F-b3-13` "— adopt the RFC directly" |
| Can the edge-filter adapter reach `untyped == 0` at all, given that it cannot type what an upstream never described? | Run the fuzz suite against a fixture upstream that returns a known mix of typed and untyped failures, and measure how many the filter can classify from status code and body alone. If a residue remains, the honest answer is a declared conformance subset rather than a claim of parity. | Require parity and let the suite fail. A declared subset is available if the measurement shows the residue is small and unrelated to the paths the platform actually uses, but overclaiming parity is worse than documenting the subset. | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-errors 2831cb4f, 2026-09-03 |
