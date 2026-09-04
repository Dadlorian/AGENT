---
name: "cap-model-access"
description: "One contract for a completion from a class of model - no vendor, endpoint or sampling knob named by the caller, no way to tell a second from overnight - plus how a gateway is built, paired and swapped. Load it when a step reaches a language model, or when routing, fallbacks, batch work or ceilings are being written."
---

# cap-model-access

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for obtaining a completion from a class of model rather than from a named vendor, so what the core imports is the completions interface and the standard that governs it, while the gateway serving it stays an adapter that can be replaced. | sourced | `F-b3-03`, `F-a4-01`, `F-b3-01`, `E-capability-model-access` "Prefix carries the contract." |

## Entities

| Entity |
|---|
| `E-capability-model-access` |
| `E-standard-openai-compatible-completions` |
| `E-adapter-litellm` |
| `E-swap-candidate-direct-provider-sdks` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-openai-compatible-completions` | unverified | unverified | - | `F-b3-03`, `X-cap-model-access-001`, `X-cap-model-access-002` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| route (operation set the recorded row gives a standard to, not a list of calls) | the requested model class, the unit of work, the budget remaining for that unit, and the policy verdict already reached for it | one endpoint selection and the reason for it. Proposed: it is a pure function evaluated before any adapter is called, so a routing rule can be tested with no model running and no spend (proposed). The budget-remaining input is the same ceiling every unit of work carries. | sourced | `X-end-to-end-056`, `X-end-to-end-058`, `F-b4-02` "Every unit of work carries a ceiling" |
| submit | a completion request naming a model class, the messages, the caller's idempotency key, and the ceiling for the call | a claim ticket. Proposed: a synchronous adapter returns one already redeemed with the result attached and a batch adapter returns one to be claimed later, so 'get me a completion' and 'get me a completion eventually and cheaply' are the same call (proposed) | sourced | `F-a4-01`, `F-b4-08` "Every externally-triggered action is safe to replay" |
| claim | a claim ticket | the completion result, or not-yet with the earliest time to ask again, or a typed problem. Proposed: the result validates against one result schema whichever adapter answered, and carries the cost actually incurred so a spend committed at submission can be reconciled here (proposed) | sourced | `F-b4-07`, `F-b4-02` "Typed and machine-readable" |
| cancel (proposed) | a claim ticket | an acknowledgement that says which of two things happened: the work stopped, or the request to stop was merely recorded. Proposed: submitted work may not be stoppable and its cost may still be owed, so the caller is told which, rather than being promised a stop the adapter cannot make (proposed) | proposed | `F-b4-02` |

### Shapes (JSON Schema 2020-12)

**completion-request (summary shape governed by the recorded completions standard; the full schemas and the worked routing table are in references/model-access-shapes.md)** (sourced; sources: `X-cap-model-access-002`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:completion-request:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "model_class",
    "messages",
    "idempotency_key",
    "ceiling_micros"
  ],
  "description": "The whole caller vocabulary, governed by the standard this row cites, the one other providers implement. There is no vendor, no member model, no endpoint and no field naming which adapter should answer.",
  "properties": {
    "model_class": {
      "type": "string",
      "pattern": "^(f|i|b|cli)-[a-z0-9-]*$",
      "description": "Routing class by prefix, matching the agent profile shape in examples/end-to-end. A bare prefix pins the class and leaves the member to routing."
    },
    "messages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "role",
          "content"
        ],
        "properties": {
          "role": {
            "enum": [
              "system",
              "user",
              "assistant",
              "tool"
            ]
          },
          "content": {
            "type": "string"
          }
        }
      }
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1
    },
    "ceiling_micros": {
      "type": "integer",
      "minimum": 0
    },
    "max_output_tokens": {
      "type": "integer",
      "minimum": 1
    },
    "deadline": {
      "type": "string",
      "format": "date-time",
      "description": "How much lateness the caller will accept. This, and not an adapter name, is what makes a request eligible for the cheap slow path."
    }
  }
}
```

**claim-ticket (proposed summary shape)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:claim-ticket:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ticket_id",
    "state",
    "model_class"
  ],
  "description": "Proposed. What submit always returns. state is redeemed on the synchronous path and pending on the batch path; the caller reads the same two fields either way.",
  "properties": {
    "ticket_id": {
      "type": "string",
      "minLength": 1
    },
    "state": {
      "enum": [
        "pending",
        "redeemed",
        "failed",
        "cancelled"
      ]
    },
    "model_class": {
      "type": "string"
    },
    "result": {
      "type": "object",
      "description": "Present when state is redeemed. One result schema for every adapter.",
      "required": [
        "text",
        "cost_micros"
      ],
      "properties": {
        "text": {
          "type": "string"
        },
        "cost_micros": {
          "type": "integer",
          "minimum": 0
        },
        "tokens_in": {
          "type": "integer",
          "minimum": 0
        },
        "tokens_out": {
          "type": "integer",
          "minimum": 0
        },
        "cost_status": {
          "enum": [
            "committed",
            "reconciled"
          ]
        }
      }
    },
    "earliest_retry": {
      "type": "string",
      "format": "date-time"
    },
    "cancellable": {
      "type": "boolean",
      "description": "Whether a cancel on this ticket can stop the work, or can only record that a stop was asked for."
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1"
    }
  }
}
```

**What a failure looks like (proposed): problem details, not prose [caller's view, folded from cap-model-access-use]** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:model-access:example:no-endpoint",
  "title": "The class you asked for has nowhere to go",
  "$ref": "urn:agentic:problem:0.1",
  "description": "A class that cannot be routed is a failure with a type. It is never quietly answered by a different class. Branch on type; read detail only to report it. `urn:agentic:problem:no-endpoint-for-class` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `adapter-unavailable`, which is also 503 and retryable, with the unserved class in detail.",
  "examples": [
    {
      "type": "urn:agentic:problem:no-endpoint-for-class",
      "title": "No endpoint serves this model class",
      "status": 503,
      "detail": "no adapter binding declares class b-deep; the request was not sent and no spend was incurred",
      "retryable": true,
      "retry_after_s": 120,
      "correlation_id": "corr-schedule-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The class prefix is the entire routing vocabulary a caller has - prefix carries the contract (T-t6-04), and agentic-stack states that a caller requests a class and never a vendor (F-a4-01) - so a request field that names a vendor, a member model or an endpoint is not an extension of the contract but a hole in it. | sourced | `F-a4-01`, `T-t6-04` "Prefix carries the contract." |
| The governing standard is the de facto completions shape named in this capability's row, adopted whole rather than remodelled. Every record on file for it is a search result rather than a page that was read, so its version is recorded as unverified and no version string is asserted. | sourced | `F-b3-03`, `F-b1-03`, `X-cap-model-access-002`, `E-standard-openai-compatible-completions` "adopt it whole rather than modelling our own shape" |
| Proposed: every completion is a future with a claim ticket. Submit always returns a ticket; a synchronous adapter returns one already redeemed. Two calls, one for fast answers and one for cheap ones, would be two interfaces wearing one name and would let the caller learn which adapter answered. Research query: does any async-completion convention already in this platform (e.g. cap-durable-execution's checkpoint/resume, cap-work-intake's envelope) define an equivalent already-redeemed ticket for a synchronous path, so this row can cite it instead of inventing one? | proposed | `F-b3-03` |
| Proposed: routing is a pure function from class, unit of work, budget remaining and policy verdict to an endpoint selection, evaluated before the adapter is called. Routing inside the adapter can only be tested by spending money on a live model; routing in front of it can be tested from a table. Research query: X-end-to-end-056 and X-end-to-end-058 describe routing as a distinct decision layer and its composition with policy and budget signals generally; is there a fetched primary source (not search-only) that names the exact four inputs this row lists? | proposed | `X-end-to-end-056`, `X-end-to-end-058` |
| Nothing in this interface branches on a vendor's name (proposed). The failure this rule exists to prevent has already happened on this substrate: batch work for one member model had to bypass the standard's own batch route entirely, because that route branches on three provider names and refuses a fourth (recorded claimed, per PASS.md A4; the member model and route are named in the Adapters section, not here). | sourced | `F-a4-08` "which branches only on `openai`/`azure`/`vertex_ai` and refuses" |
| Every unit of work carries a ceiling, and this is the boundary where the ceiling is spent. Proposed consequence for a slow path: spend is committed when work is submitted and the true figure arrives when the ticket is claimed, so the interface carries both a committed and a reconciled cost rather than assuming the two coincide. | sourced | `F-b4-02` "Every unit of work carries a ceiling" |
| cap-errors owns the failure shape (F-b4-07). What this boundary adds: three of its failures are peculiar to it and each needs a type rather than a status string, namely a class with no endpoint routing can reach, a ceiling exhausted before or during a call, and a cancel the adapter cannot honour. | sourced | `F-b4-07` "Never parsed from prose" |
| agentic-stack and build-adapter-pair state design rule 3 (F-b1-04). Its consequence here: the second adapter must differ from today's on how a result arrives and whether a call in flight can be stopped, because another gateway of the same shape would agree with the first on both and the swap would test configuration rather than the contract. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a model through the same call with the same two fields. Which one asked is not a field of the request, so the answer, the cost and the record are the same shape whichever way the work arrived. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: swapping the gateway, adding a model to a class, changing where a class is routed, or moving a class from the fast path to the cheap one changes nothing in a caller that sends a class and reads a ticket. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Vendor names, member model identifiers, endpoint hostnames, credentials, and which adapter answered: callers request a class, never a vendor, and the prefix carries the contract. A caller that can read any of these can branch on them, and a caller that branches on them has made the adapter part of the contract (proposed, drawn out from the cited fact). | sourced | `F-a4-01` "Callers request a class, never a vendor." |
| Sampling and decoding parameters that only some backends accept are not part of the contract; the records on file note that support for the common ones varies by provider and by self-hosted backend. They belong to an adapter's defaults, where a backend that ignores one is a declared gap rather than a silently dropped field. | sourced | `X-cap-model-access-006` "support varies across providers and self-hosted backends" |
| agentic-stack states design rule 6 (F-b1-07). What it forbids here specifically: the criterion a result will be judged against never travels in a completion request, because a request body is the one place where the graded work and the grading rule would otherwise meet. | sourced | `F-b1-07` "The grader is never visible to the graded." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Name the de facto completions shape as this interface's standard, adopt its request and result vocabulary whole, and record its version as unverified until a published specification has actually been fetched and read. | Where a standard exists the rule is to adopt it rather than model our own shape, and the only records on file for this one are search results, so a version string here would be invented rather than cited. | sourced | `F-b1-03`, `F-b3-03`, `X-cap-model-access-002` "standard that other providers implement" |
| 2 | Define submit to return a claim ticket in every case, and define claim as the only way to read a result. Give the synchronous path a ticket that is already redeemed rather than a second, shorter call. Research query: see the claim-ticket research query on the sibling invariant row above. | Proposed. Latency between the two paths differs by orders of magnitude and one returns a result while the other returns a ticket; one interface that always returns a ticket is the only shape both can satisfy without the caller learning which one it got. | proposed | `F-b3-03` |
| 3 | Put routing in front of the adapter as a pure function of class, unit of work, budget remaining and policy verdict, and give it a table of test vectors that runs with no model reachable. Research query: see the routing research query on the sibling invariant row above. | Proposed. Selecting which model handles a query is a decision layer with its own literature rather than a detail of a gateway's configuration; in front of the adapter it is testable, inside it is only observable by spending. | proposed | `X-end-to-end-056`, `X-end-to-end-058` |
| 4 | Reject every proposed request field that names a vendor, a member model, an endpoint or an adapter, and reject any code path that branches on such a name. Where a caller wants the cheap slow path, take a deadline instead. | agentic-stack states that the prefix carries the contract (F-a4-01). What this adds: a deadline expresses what the caller actually knows, while an adapter name expresses a guess about how the platform is configured today. | sourced | `F-a4-01`, `F-a4-08` "Callers request a class" |
| 5 | Keep parameters that only some backends honour out of the contract and put them in adapter defaults, with any backend that ignores one recorded as a declared gap. | The records on file say support for the common inference parameters varies by provider and by self-hosted backend, so a contract field that some adapters drop silently is worse than no field: the caller believes it took effect. | sourced | `X-cap-model-access-006` "verify the exact fields your server accepts" |
| 6 | Make the budget concern handle a spend committed at submission and reconciled when the ticket is claimed, and carry both figures on the result rather than overwriting one with the other. | Every unit of work carries a ceiling, and a slow path spends hours before the true cost is known; a design that assumes commitment and reconciliation coincide has no answer for a unit that ends between them. | sourced | `F-b4-02` "Exceeding it terminates the unit, not the platform" |
| 7 | Choose the second adapter on execution-model axes as build-adapter-pair defines them: result_or_claim_ticket, prompt_cancellation and start_and_teardown_cost must all differ from today's adapter. | agentic-stack and build-adapter-pair carry design rule 3 (F-b1-04): the second adapter is chosen to prove the interface is not shaped around its current implementation (F-part-c-05), and a hosted gateway of the same shape as the installed one agrees with it on all three axes. | sourced | `F-b1-04`, `F-part-c-05` "chosen to prove the interface is not shaped around its current implementation" |
| 8 | Return every failure as the typed problem object cap-errors defines, including no-endpoint-for-class, budget-exhausted and cancel-not-honoured, and never let an unroutable class fall back silently to another one. | cap-errors owns the failure shape (F-b4-07): typed and machine-readable, so an unroutable class comes back as a type the caller can branch on rather than as a quiet substitution of the class it asked for (F-a4-01). | sourced | `F-b4-07`, `F-a4-01` "Typed and machine-readable" |
| 9 | Send the class the work needs and your messages, plus an idempotency key you can reproduce. Take every default. Do not send a model name, a provider, an endpoint, a temperature or an adapter. | It has to be simple to use, and every field you fill in is a decision you now own; which endpoint can serve a class is a fact the platform has and you do not. | sourced | `T-t3-01` "It has to be simple to use." |
| 10 | Proposed: open references/model-access-shapes.md when writing or reviewing the full request, ticket and routing-table schemas. The body of this skill is enough to judge a candidate adapter and to write the contract without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full schemas exceed the progressive-disclosure budget for a skill body, and a reader deciding whether a gateway may serve this interface does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Assert routing behaviour by observing which endpoint answered, never by reading the file that declares it: agentic-stack records that configuration written in the documented place was silently discarded (F-a7-04), and it was measured on this very boundary, where a stored row overlaid the routing settings written in the documented file. | sourced | `F-a7-04` "Configuration written in the documented place was silently discarded." |
| Keep the property this substrate already has: a scoped key with a hard budget cap that was verified to stop spend rather than merely record it. A design where the ceiling is a number in a report is a ceiling only in the sense that a speed limit sign is a governor. | sourced | `F-a4-07`, `F-b4-02` "verified to terminate spend rather than merely record it" |
| Treat model selection as its own decision layer rather than as a prefix convention living inside a gateway's configuration: the records on file describe choosing which model handles a query as a cost-quality trade-off across a pool. Those records are search results rather than pages that were read, so take them as the shape of the problem and not as a measurement. | sourced | `X-end-to-end-056` "optimising cost–quality trade-offs across a pool of LLMs" |
| Assert the number of adapters actually run and the number of tickets actually redeemed, not the exit code of the suite: agentic-stack records the structurally-green-gate finding (F-a7-03), where those stages establish well-formedness, not correctness, and a conformance run that exercised only the fast adapter reports the same green as one that exercised both. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed, following the reference example in docs/reference/composable-plan.md: keep the driver file the only place a class is bound to a vendor. What a class resolves to is widened or swapped by editing one driver definition, which changes every caller at once and changes no caller's request; a routing change that obliges callers to send a different value has moved the vendor back into the call, which is the failure the class prefix exists to prevent. | proposed | `REF-5-1-03`, `REF-12-12` "a driver definition \| what `model: cheap` resolves to \| swap a vendor without a caller noticing" |
| Proposed: treat a silent fallback to another class as the failure this interface exists to prevent. The work completes, the bill arrives, and nothing in the result says the class asked for was not the class used, so the conformance run asserts the class that answered rather than the class that was requested. Research query: unresearched; no prior-art search has been run for how model gateways report a class-level routing substitution back to the caller. | proposed | `F-a4-01` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-litellm` | today | route, submit, claim and cancel served by a synchronous request/response gateway that speaks one OpenAI-compatible API over every provider. PASS.md B3 names LiteLLM in this row's adapter column. submit holds the connection and returns a ticket already redeemed; cancel is closing the connection; routing is the gateway's own group and fallback configuration. | Proposed: cannot return an answer hours later at batch pricing, cannot survive the caller going away mid-call, and holds one connection per call in flight. Its routing configuration is also the boundary where PASS.md A7 finding 3 was measured - a LiteLLM_Config row in Postgres overlays and replaces router_settings on every gateway load - so a routing change here is not in effect merely because it was written where the documentation says. | Select the adapter by configuration, send the same request object through both, and assert that both results validate against the one result schema and that the endpoint which answered was read from the response rather than from the binding that selected it. | claimed | `F-b3-03`, `F-a1-02`, `F-a7-04` "OpenAI-compatible completions \| LiteLLM" |
| `E-swap-candidate-direct-provider-sdks` | second | the same four operations served by provider-native asynchronous batch submission with claim-and-poll: submit hands the work to a provider's own batch endpoint and returns a pending ticket, claim polls it, and the result arrives hours later at batch pricing. This is grounded rather than hypothetical - batch on this substrate already runs through Gemini's native :batchGenerateContent via LiteLLM passthrough, deliberately not through the OpenAI-shaped /v1/batches route, which branches only on openai/azure/vertex_ai and refuses Gemini (claimed, per PASS.md A4). | Proposed: cannot answer interactively, and cannot promise a stop - cancelling a submitted batch is a separate call whose effect may be a partial refund rather than a halt, so its tickets carry cancellable false. It also commits spend at submission and reconciles it on claim, which is the case a synchronous-only design never has to represent. | Proposed: the axes that differ are result_or_claim_ticket (a result versus a ticket to redeem), prompt_cancellation (close the connection versus a separate call that may not stop the work) and start_and_teardown_cost (a call in seconds versus a submission answered in hours at batch pricing). Select by configuration with no code edit between runs, then compare both reports against the same declared gaps. | claimed | `F-b3-03`, `F-a4-08`, `F-b1-04` "not the OpenAI-shaped `/v1/batches` route, which branches only on" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/gateway/test.sh && python3 harness/gateway/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 372cdc1: exit 0; last lines:   adapter=provider-native asynchronous batch (claim-and-poll) cases=12 passed=12 dispatches=7 refusals=2 overshoot_violations=0 endpoint_marker=batch-job-accepted product_hits=0 \| conformance PASSED: 24/24 cases, 2 binding(s) |
| Deliberate breakage | Append a product-name comment (`# breakage: litellm`) to the end of harness/gateway/call.py, outside adapters/. Restored with `git checkout -- harness/gateway/call.py`. |
| Expected failure | Measured by tools/measure.py at 372cdc1: exit 1; last lines:   FAIL hits not counted \| passed 18, failed 7 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-02` "The core imports interfaces, never implementations" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `cap-model-access-implement` | Turn the contract in cap-model-access into something that runs here: two adapters behind one completions interface, the model classes that exist today brought in front of it group by group, and every ceiling attached around the submission and around the claim rather than inside the gateway. | `references/cap-model-access-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-evidence`, `build-skill-authoring`, `cap-errors`

Used by: `xc-guarantees`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is routing policy a capability of its own with its own two adapters, or an operation of this one? | A second routing implementation that is not part of a gateway exists in the records on file, described as a programmable routing layer that composes routing, policy and reasoning budget rather than reading a caller's prefix. If a routing table can be swapped for it without touching this interface, routing is an operation here; if the swap needs new request fields, routing is its own boundary and deserves its own skill. | Keep route as an operation of this capability, pure and in front of the adapter, and record the contrast as unproven: the record is a search result, not a page that was read. | `X-end-to-end-057`, `X-end-to-end-058` "composes routing, policies, reasoning budgets and workflow signals into a unified inference layer" |
| The end-to-end consumption reference returns a completion result directly and has no ticket to claim, so the claim ticket defined here has no counterpart in it. Which shape wins? | Add one batch-class step to the reference workflow and see whether the runner needs a new field to hold a pending call, or whether a ticket that is already redeemed on the synchronous path is indistinguishable from what it returns today. | Keep the ticket in the interface and treat the reference's direct result as the redeemed case, since the alternative is two interfaces and the reference already routes by model class. | `T-t6-01`, `T-t6-04` "callers request a model class, not a vendor" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-model-access 2831cb4f, 2026-09-03 |
