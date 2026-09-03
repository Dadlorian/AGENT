---
name: cap-model-access-implement
description: How to build the Model access capability on this stack: a thin adapter over the model gateway that already runs on the host, a second adapter that answers hours later with a ticket instead of a result, how to bring the model classes that exist today in front of one interface, where budget, policy, identity, telemetry, provenance and idempotency attach to a submission and again to a claim hours later, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code behind a completion call, when wiring a gateway or a batch endpoint behind the class prefix, when deciding what the second adapter should be, when a routing change appears to have been applied and was not, or when a slow call's cost has to be reconciled long after the work was authorised.
---

# cap-model-access-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-model-access into something that runs here: two adapters behind one completions interface, the model classes that exist today brought in front of it group by group, and every ceiling attached around the submission and around the claim rather than inside the gateway. | sourced | `F-a1-02`, `F-b3-03`, `E-capability-model-access`, `E-adapter-litellm` "Model gateway" |

## Entities

| Entity |
|---|
| `E-capability-model-access` |
| `E-adapter-litellm` |
| `E-swap-candidate-direct-provider-sdks` |
| `E-service-gateway-cli-bridge-1` |

## Contract

### Shapes (JSON Schema 2020-12)

**ModelAccessAdapterBinding (proposed shape; what selects an adapter, and the only place an adapter is named)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:adapter-binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "result_or_claim_ticket",
    "prompt_cancellation",
    "cost_settlement"
  ],
  "description": "Proposed. Read by the adapter factory only. Nothing in the core and no caller reads this object or branches on adapter.",
  "properties": {
    "adapter": {
      "type": "string",
      "description": "Adapter entity id. Selecting an adapter is configuration; there is no code path that chooses one."
    },
    "result_or_claim_ticket": {
      "enum": [
        "result",
        "claim_ticket"
      ],
      "description": "Whether submit can answer in the call or only hands back a ticket to redeem later."
    },
    "prompt_cancellation": {
      "enum": [
        "close_connection",
        "separate_call",
        "none"
      ],
      "description": "How, if at all, work in flight can be stopped. separate_call means a cancel may be recorded rather than honoured."
    },
    "cost_settlement": {
      "enum": [
        "immediate",
        "committed_then_reconciled"
      ],
      "description": "Whether the true cost is known when the call returns, or only when the ticket is claimed."
    },
    "classes_served": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^(f|i|b|cli)-[a-z0-9-]*$"
      },
      "description": "Which model classes this adapter can serve. A class no adapter serves is a routing failure, never a substitution."
    },
    "endpoint_marker": {
      "type": "string",
      "description": "Emitted by the answering endpoint on every response and asserted against, so a routing change that never took effect is visible."
    }
  }
}
```

**ModelAccessConformanceReport (proposed shape; the counters the definition of done asserts on)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "results_validated",
    "product_hits",
    "per_adapter"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 2,
      "description": "Distinct adapters exercised with the same request object. Fewer than two means the swap was not tested."
    },
    "results_validated": {
      "type": "integer",
      "minimum": 2
    },
    "product_hits": {
      "type": "integer",
      "maximum": 0,
      "description": "Files under the core and the seams naming any adapter's product. Design rule 1 made checkable."
    },
    "per_adapter": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "adapter",
          "endpoint_marker",
          "ticket_state",
          "result_schema_valid",
          "cost_status",
          "declared_gap_honoured"
        ],
        "properties": {
          "adapter": {
            "type": "string"
          },
          "endpoint_marker": {
            "type": "string",
            "description": "Read from the response, not from the binding that selected the adapter."
          },
          "ticket_state": {
            "enum": [
              "redeemed"
            ]
          },
          "result_schema_valid": {
            "type": "boolean"
          },
          "cost_status": {
            "enum": [
              "reconciled"
            ]
          },
          "budget_reserved_micros": {
            "type": "integer",
            "minimum": 0
          },
          "budget_reconciled_micros": {
            "type": "integer",
            "minimum": 0
          },
          "declared_gap_honoured": {
            "type": "boolean",
            "description": "True when the adapter behaved as its binding declares, including when the declared behaviour is that a cancel cannot be honoured."
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
| Proposed pointer, see cap-model-access's invariant that the second adapter must differ from today's on how a result arrives and whether a call in flight can be stopped (F-b1-04): the build consequence is a selection criterion on three of build-adapter-pair's axes - result_or_claim_ticket, prompt_cancellation and start_and_teardown_cost, recorded in that skill's differs_in_execution_model field - and a candidate that agrees with today's adapter on all three is rejected and another is found. | proposed | `F-b1-04` |
| Apply build-adapter-pair: selecting the adapter is configuration, and no core code and no caller branches on which one answered - the swap test agentic-stack states as design rule 1; proposed pointer, see that skill. | proposed | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| agentic-stack states that what runs is substrate and is not to be replaced (F-part-c-11). The consequence here: the model gateway measured on this host, one API over every provider bound to loopback, becomes today's adapter rather than a thing to migrate off, and the coding-CLI bridge beside it becomes another endpoint behind the same class prefix rather than a second interface. | sourced | `F-part-c-11`, `F-a1-02`, `F-a1-03` "Do not propose replacing what runs." |
| agentic-stack states that the cross-cutting guarantees are applied by the platform and cannot be declined (F-b4-01). What this adds: on a slow path they attach twice, once around the submission and once around the claim hours later, so an adapter offering its own retries, its own spend cap or its own audit trail has offered a second, declinable copy that must not be wired. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them" |
| cap-model-access already states the measured hard-cap property (F-a4-07). What this adds is a proposed mechanism for the gap between submission and claim: the ceiling is reserved at submit and reconciled at claim, and a reservation that is never reconciled expires, so that a stop-spend cap still stops spend when the true figure arrives hours late and a crashed unit does not consume its ceiling forever. | sourced | `F-a4-07`, `F-b4-02` "verified to terminate spend rather than merely record it" |
| cap-model-access states that routing configuration on this boundary was measured to have no runtime effect (F-a7-04). What this adds at the code level: the adapter asserts the endpoint that answered from a marker on the response, so the conformance run cannot pass by exercising the same endpoint twice under two names. | sourced | `F-a7-04` "silently discarded" |
| build-evidence-record owns the append-only chained record (F-a5-03). What this adds: a cost reconciled hours after it was committed is a second record about the same call, so it is appended and chained rather than written over the first, and the difference between the two figures stays readable. | sourced | `F-a5-03` "a manual edit between runs is detectable" |
| build-evidence-record and F-part-c-08 state the claimed-versus-measured distinction. The consequence here: every statement in this skill about how an adapter behaves is claimed until the conformance report and its evidence record exist. Neither adapter here has been run behind this interface in this repository; the gateway itself is measured as running, which is not the same as measured as conformant. The gateway being up is a measurement about the gateway, not about this interface. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's adapter as a thin translation onto the model gateway already running on this host: submit posts the completions request and returns a ticket already redeemed, claim reads that ticket, cancel closes the connection. Add nothing to the interface to accommodate it. | cap-model-access fixes the contract as class, request and claim ticket; the adapter is the only place allowed to know there is a gateway, so 'the gateway is unreachable' becomes a typed failure of one adapter rather than an outage of the capability. | sourced | `F-a1-02`, `F-b3-03` "Model gateway" |
| 2 | Build the second adapter as provider-native asynchronous batch submission with claim-and-poll: submit hands the work to a provider's own batch endpoint and returns a pending ticket, claim polls it, and the ticket declares that a cancel cannot be honoured. Research query: does any provider's batch-API documentation on file (X-cap-model-access-001..006) describe claim-and-poll semantics and an unhonourable cancel specifically, or only the synchronous completions shape, which would source this row rather than leave it a proposed design? | Proposed: this is the pair's proof - the answer stops being a result and becomes a ticket, cancellation stops being possible, and the cost stops being known when the call returns. Batch on this substrate already runs past the standard's own batch route rather than through it (claimed, per PASS.md A4), so the shape is grounded rather than hypothetical. | proposed | `F-a4-08`, `F-b1-04` |
| 3 | Record differs_in_execution_model with those three axes, and write each adapter's gaps down as gaps: the synchronous gateway cannot answer hours later at batch pricing; the batch adapter cannot answer interactively and cannot promise a stop. | build-adapter-pair already states that a swap needing a core change means the boundary is drawn wrong (F-meta-04). What this adds: widening the request shape until both adapters satisfy every field is the quiet version of that failure, so each gap is declared on the binding and the conformance run asserts the adapter honoured it. | sourced | `F-meta-04`, `F-b1-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 4 | Migrate one class group at a time, in the order free local GPU, interactive metered, coding CLI as a model, asynchronous batch: put the interface in front of the calls that already use that prefix, keep them running, and count callers converted. | The prefix groups already exist on this substrate, including one whose members are coding CLIs exposed as chat-completions endpoints, so the migration is putting a contract in front of a working convention rather than inventing one. Batch goes last because it is the group that forces the claim ticket, and converting it first would mean redesigning the interface mid-migration. | sourced | `F-a4-02`, `F-a4-05`, `F-a1-03` "Exposes coding CLIs as chat-completions endpoints" |
| 5 | Reserve the ceiling at submit against the caller's unit of work, reconcile it at claim, and expire an unreconciled reservation after a deadline plus grace. Re-evaluate policy and re-assert the actor at claim as well as at submit. | Refusal is deterministic and happens before execution rather than after spend, and on a slow path the claim is a second execution hours later under a token that may have expired; a claim that skips the gate has found the opt-out design rule 7 forbids, and a reservation never released leaves a unit's ceiling permanently consumed. | sourced | `F-b4-04`, `F-b4-02`, `F-b4-03` "Refusal is deterministic and happens before execution, not after spend" |
| 6 | Carry the correlation identifier explicitly on the request, on the ticket and on the reconciliation record, and re-attach it when the ticket is claimed; never expect trace parentage to reconnect a claim to the submission that created it. | agentic-stack already states the trace-context finding (F-a7-02). What this adds: hours can pass between submit and claim, and no trace context survives that gap at all, so the identifier has to be a field on the ticket the claim reads. | sourced | `F-a7-02`, `F-b4-06` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Assert which endpoint actually answered from a marker on the response, not from the binding that selected the adapter, and make the routing test vectors run against that marker. | cap-model-access states the silently-discarded-configuration finding for this boundary (F-a7-04). What this adds: here the same failure mode produces two green conformance runs against the same endpoint, which reads as a proven swap and is not one. | sourced | `F-a7-04` "on every gateway load" |
| 8 | Apply build-definition-of-done: run the definition of done below and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: implement the claim ticket before implementing anything else, including retries, streaming and fallbacks. It is the one shape the fast path does not need and the slow path cannot do without; built afterwards, it becomes a special case bolted onto a synchronous design. Research query: does a build-order record for another claim-ticket-bearing capability in this repository (cap-durable-execution-implement, cap-scheduling-implement) already show retries or streaming built before the ticket and failing, which would source this ordering rather than leave it a proposed practice? | proposed | `F-b1-04` |
| Proposed: make the conformance suite's request object a fixture on disk that both adapters receive byte for byte. A request the suite builds per adapter can differ between them without anyone noticing, which is the exact defect the run exists to detect. Research query: does build-adapter-pair's own conformance-suite guidance name a shared on-disk fixture as the mechanism for byte-identical requests across adapters, which would source this rather than leave it a proposed practice? | proposed | `F-part-c-04` |
| cap-model-access already states the structurally-green-gate trap (F-a7-03). What it adds for an implementer: assert adapters_run and results_validated on the report rather than in a log line, because a suite whose batch adapter was skipped for being slow will otherwise pass every other assertion it makes. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: let the batch adapter fail the interactive cases honestly instead of emulating a synchronous call by polling in a loop until it answers. An emulated fast path hides the property the pair exists to prove and turns a four-order-of-magnitude latency difference into a timeout nobody can explain. Research query: has a conformance run in this repository already caught a polling emulation hiding a latency difference on another adapter pair, which would source this specific failure mode rather than leave it a proposed practice? | proposed | `F-b1-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-litellm` | today | route, submit, claim and cancel built as a translation layer over the model gateway PASS.md B3 names in this row and PASS.md A1 records running on this host: gateway-litellm-1, image ghcr.io/berriai/litellm-database:v1.97.0, bound to 127.0.0.1:4000, one OpenAI-compatible API over every provider, with a companion cli-bridge exposing coding CLIs as chat-completions endpoints behind the same class prefix. | Proposed: cannot return an answer hours later at batch pricing and cannot survive the caller going away mid-call. Its routing configuration is where PASS.md A7 finding 3 was measured - a LiteLLM_Config row in Postgres overlays and replaces router_settings on every gateway load - so a routing change is not in effect merely because it was written where the documentation says. | Point the binding at the other adapter and re-run the same request fixture. No core change is expected. Assert the endpoint marker read from the response, not the adapter name written in the binding. | claimed | `F-b3-03`, `F-a1-02`, `F-a1-03`, `F-a7-04` "one OpenAI-compatible API over every provider" |
| `E-swap-candidate-direct-provider-sdks` | second | the same four operations served by provider-native asynchronous batch submission with claim-and-poll: submit posts the work to a provider's own batch endpoint and returns a pending ticket, claim polls until the result is ready, and cost is committed at submission and reconciled on claim. PASS.md A4 records this already happening on this substrate - batch runs through Gemini's native :batchGenerateContent via LiteLLM passthrough, not the OpenAI-shaped /v1/batches route, which branches only on openai/azure/vertex_ai and refuses Gemini (claimed). | Proposed: cannot answer interactively and cannot promise a stop, so its tickets carry cancellable false and its binding declares prompt_cancellation separate_call. It also cannot report a final cost when submit returns, which is why cost_settlement is committed_then_reconciled and why the budget concern has to hold a reservation. | Proposed: the axes that differ are result_or_claim_ticket, prompt_cancellation and start_and_teardown_cost. Select by configuration with no code edit between runs, send the same request fixture through both, then compare both reports against the same declared gaps. | claimed | `F-b3-03`, `F-a4-08`, `F-b1-04` "direct provider SDKs" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/gateway/test.sh && python3 harness/gateway/conformance.py --adapter dryrun --adapter second |
| Expected | Proposed tool, built with the first implementation of this interface: `python3 tools/conformance_model_access.py --adapter today --adapter second --request fixtures/model-access/request.json --report out/model-access-conformance.json`. It sends the one request fixture, byte for byte, through the synchronous adapter and the asynchronous batch adapter and asserts per adapter that ticket_state is redeemed, result_schema_valid is true against the single result schema, cost_status is reconciled, budget_reconciled_micros was recomputed rather than copied from budget_reserved_micros, declared_gap_honoured is true, and endpoint_marker read from the response equals the adapter selected in the binding. Across adapters it asserts adapters_run >= 2 and results_validated == adapters_run. It then runs `grep -rIl -E '(litellm\|openrouter\|gemini\|sglang)' src/core/ src/seam/` and asserts product_hits == 0. Earlier criterion named tools/conformance_model_access.py, replaced by the harness on 2026-09-03. |
| Deliberate breakage | Append a product-name comment (`# breakage: litellm`) to the end of harness/gateway/call.py, outside adapters/. Restored with `git checkout -- harness/gateway/call.py`. |
| Expected failure | test.sh's product-name scan (check 3) fails with product_hits going from 0 to 1, and the immediately following `conformance.py --adapter dryrun --adapter second` run also reports product_hits=1 and a non-zero exit, because every conformance run scans the whole harness tree outside adapters/ for a vendor name, not only the --product-scan invocation. |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-02` "The core imports interfaces, never implementations" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-model-access`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the coding-CLI class belong behind this interface as a third adapter, or is it an agent runtime wearing a completions shape? | Compare what a caller of that class actually needs against the request shape: if it needs tool permission callbacks, streamed updates or mid-turn cancellation, it is an agent session and belongs to the agent-runtime boundary; if a prompt in and text out is enough, the bridge that already exposes those CLIs as chat-completions endpoints is a third adapter here. | Keep it behind this interface, because it already answers on a chat-completions endpoint and its class prefix is already part of the routing vocabulary; revisit the moment a caller of that class asks for a callback. | `F-a1-03`, `F-a4-05` "Coding CLI as a model" |
| Where does the budget reservation live, and what expires it when a claim never comes? cap-model-access states the ceiling rule (F-b4-02); this asks only how it is held across a gap of hours. | Measure, over the batch work actually submitted, how many tickets are never claimed and how long the longest legitimate gap between submit and claim is. The second number sets the grace period; the first says whether expiry is an edge case or the normal path. | A reservation held against the unit of work with an expiry at the request deadline plus grace, so the ceiling is restored without a claim; the alternative, reconciling only on claim, gives an abandoned submission an unbounded hold on the unit's budget. | `F-b4-02` "Every unit of work carries a ceiling" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-model-access 2831cb4f, 2026-09-03 |
