---
name: "xc-budget-implement"
description: "How to make the budget ceiling real on this stack: today's enforcement bound to the scoped keys the model gateway already carries, a second enforcement point the platform holds itself and draws from before every dispatch, how to migrate from one to both without a window where nothing stops spend, where the ceiling attaches to correlation, provenance, policy and typed failures, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that refuses a call for cost, when a cap only bounds what flows through the gateway, when delegated work outspends the run that authorised it, when a reservation is left held by a unit that crashed, or when deciding what the second enforcement point should be."
---

# xc-budget-implement (folded into `xc-guarantees`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the guarantee in xc-budget into something that runs here: two enforcement points behind one ceiling, the second one drawing from a platform-held lease before each dispatch so that spend outside the model gateway is bounded too, migrated in without a window in which nothing stops a call. | sourced | `F-b4-02`, `F-a4-07` "Every unit of work carries a ceiling" |

## Entities

| Entity |
|---|
| `E-concern-budget` |
| `E-adapter-litellm` |
| `E-swap-candidate-any-keyed-lease-store` |
| `E-service-gateway-db-1` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:budget:pair-axes:0.1",
  "title": "BudgetPairAxes",
  "description": "Proposed. The three axes on which the two enforcement points differ, stated as properties rather than as product names. measured stays false until the swap has been executed and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "unit_of_resource_granted",
        "today_value": "spend allowance on one key within a time window",
        "second_value": "a reservation against one root unit of work's ceiling",
        "measured": false
      },
      {
        "axis": "locus_of_durability_and_verification",
        "today_value": "the gateway's own spend ledger",
        "second_value": "the platform's append-only state, verifiable at a pinned head",
        "measured": false
      },
      {
        "axis": "processes_required_for_progress",
        "today_value": "the gateway must be reachable for the ceiling to bind",
        "second_value": "the draw happens before dispatch and binds even when no metered call follows",
        "measured": false
      }
    ]
  ]
}
```

**budget-conformance report (proposed; the fields the definition of done asserts on)** (proposed; sources: `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:budget:conformance-report:0.1",
  "title": "BudgetConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. Written per adapter and once across adapters, so a green run names what it actually checked rather than only its exit code.",
  "required": [
    "adapter",
    "dispatches_checked",
    "roots",
    "unbounded",
    "terminated_on_budget",
    "overshoot_violations",
    "enforcement_point_observed"
  ],
  "properties": {
    "adapter": {
      "type": "string",
      "description": "The entity id of the enforcement adapter under test."
    },
    "dispatches_checked": {
      "type": "integer",
      "minimum": 0
    },
    "roots": {
      "type": "integer",
      "minimum": 0
    },
    "unbounded": {
      "type": "integer",
      "minimum": 0,
      "description": "Dispatches with a null or absent ceiling."
    },
    "terminated_on_budget": {
      "type": "integer",
      "minimum": 0
    },
    "overshoot_micros_max": {
      "type": "integer",
      "minimum": 0
    },
    "overshoot_violations": {
      "type": "integer",
      "minimum": 0
    },
    "enforcement_point_observed": {
      "type": "string",
      "description": "Read from the refusal that came back, never from the binding that selected the adapter."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two enforcement points differ on three of build-adapter-pair's axes - unit_of_resource_granted, locus_of_durability_and_verification and processes_required_for_progress - recorded in the shape above. Another gateway with per-key caps would agree with today's on all three, so swapping to it would test a vendor and not the guarantee. | proposed | `F-b1-04` "Swappability is a tested property, not an intention." |
| agentic-stack and build-adapter-pair state design rule 1 (F-b1-02). Its consequence here: which enforcement point refused a call is configuration, and no core code, no workflow and no caller branches on it; a refusal names its enforcement point in the report, not in a field a caller can read and route on. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| agentic-stack states that what runs is substrate (F-part-c-11). Its consequence here: the scoped keys that already cap spend on this host are not replaced, they become the first enforcement point, and the platform-held lease is added beside them rather than in place of them. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| The ceiling and its placement are xc-budget's (F-b4-02). On this stack one enforcement point is not enough, because a cap that lives at the model gateway - the adapter cap-model-access-implement owns - bounds only what crosses the gateway, and a run also spends on isolation, tool calls and delegated descendants that never appear in a completion request. | sourced | `F-b4-02`, `X-xc-budget-001` "Exceeding it terminates the unit, not the platform" |
| Proposed: the migration never has a window in which nothing stops a call. The existing key caps keep enforcing while the lease is introduced, both run together over the same corpus, and only then does the lease become authoritative for the root ceiling with the key caps left in place as a backstop. | proposed | `F-a4-07` |
| The contents of a record of a run are build-evidence-record's (F-a5-04). Every statement in this skill about how an enforcement point behaves is claimed until the conformance report and its evidence record exist, and a reworded sentence never upgrades a label. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's enforcement point as a thin binding onto the scoped keys the model gateway already carries: map one root unit of work to the key group its class prefix resolves to, read the remaining allowance before dispatch, and treat the gateway's refusal as the authoritative stop. | xc-budget records that this property is already measured on this substrate (F-a4-07): the keys stop spend rather than noting it. Building on the mechanism that already refuses calls is the smaller change and it starts the pair from a real enforcement point rather than an intention. | sourced | `F-a4-07`, `F-a1-04` "verified to terminate spend rather than merely record it" |
| 2 | Proposed: build the second enforcement point as a platform-held reservation lease. Reserve the priced floor of a dispatch from the root's remaining ceiling before the dispatch starts, write the reservation through the state seam, reconcile it with the actual cost afterwards, and expire an unreconciled reservation at the unit's deadline plus grace. | Proposed: this breaks the assumption that the model gateway is the only place spend occurs. A reservation taken before dispatch binds work that never reaches the gateway at all, and the expiry is what stops a crashed unit from holding a root's ceiling forever. | proposed | `F-b3-16`, `F-b4-02` |
| 3 | Apply build-adapter-pair: record differs_in_execution_model from the shape above, leave measured false until the swap has actually been run, and write each enforcement point's gaps down as gaps rather than as caveats; proposed pointer, see that skill. | differs_in_execution_model, its axes and the rule that measured stays false until the swap has run belong to build-adapter-pair; four sibling skills carried the sentence verbatim (consolidation part B, kb/ceremonies/implement-clusters.json). | sourced | `F-b1-04` "Swappability is a tested property, not an intention." |
| 4 | Migrate in three steps with no gap: keep the key caps enforcing and add the lease in shadow, recording what it would have refused; run both over the same corpus and reconcile the two refusal sets; then make the lease authoritative for the root ceiling and keep the key caps as a per-key backstop. | The shadow step is what shows the lease refuses the same calls plus the ones the gateway never sees, and it is the only step in which a disagreement between the two is cheap. Switching in one move would replace a mechanism measured to work with one that has never refused anything. | sourced | `F-a4-07`, `F-part-c-11` "Do not propose replacing what runs" |
| 5 | Wire the cross-cutting attachments at both enforcement points: stamp the root run identifier as an explicit attribute on every draw and every reconcile, append both as records in the append-only chained store, and return the registered typed refusal rather than a message. | agentic-stack states that correlation must ride on an explicit attribute set at dispatch (F-a7-02) because parentage did not survive the agent boundary; a draw whose root cannot be identified cannot be subtracted from the right ceiling. The chained store is what makes a later edit to a spend record detectable. | sourced | `F-a7-02`, `F-a5-03` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Read the enforcement point from the refusal that actually came back, not from the binding that selected the adapter, and make the conformance report carry that observed value. | agentic-stack states the silently-discarded-configuration finding (F-a7-04), measured on this very gateway: a stored row overlaid the settings written in the documented file. A ceiling believed to be in force because it was configured is exactly that failure with money attached. | sourced | `F-a7-04` "Configuration written in the documented place was silently discarded." |
| 7 | Apply build-definition-of-done: run the definition of done below over both enforcement points and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Test the ceiling by watching a call be refused, never by reading the configured limit. The one measurement on file for this boundary is that a limit which stops spend and a limit which records it look identical in configuration and differ entirely in effect. | sourced | `F-a4-07` "hard budget cap, verified to terminate spend rather than merely record it" |
| Report the counts per enforcement point. A corpus replayed through two adapters can leave one of them with nothing to refuse and still exit green - the structurally-green-gate finding is agentic-stack's (F-a7-03) and xc-budget draws it for a budget corpus; this is the code-level form. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: reconcile from actuals and never from the reservation. Copying the reserved figure into the reconciled one produces a ledger that always balances and a ceiling that drifts by exactly the estimation error, which is the failure that is hardest to see because nothing ever disagrees. | proposed | `X-end-to-end-047` |
| Expect the two enforcement points to disagree in the shadow step and treat the difference as the finding rather than as noise: the draws the lease refuses and the gateway never saw are the spend that a gateway-only cap was always missing. The records on file describe that gateway pattern as the converged one, which is why the gap is easy to overlook. | sourced | `X-xc-budget-001` "a dedicated AI gateway sits between application code and provider APIs" |
| Keep the conformance suite in the enforcement path rather than beside it. Why this layer exists is xc-budget's (F-a6-04); the code-level trap is that a budget suite replaying a stored corpus never touches the path a live dispatch takes, so wire it to the same draw the dispatcher calls. | sourced | `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-litellm` | today | reserve, draw, reconcile and remaining served by the scoped virtual keys of the model gateway PASS.md B3 names in the model-access row and PASS.md A1 records running on this host, with its configuration, its keys and its spend ledger held in the gateway database container. A draw is the gateway accepting or refusing the call; reconciliation is the gateway's own spend ledger; remaining is that ledger read back per key group. | Proposed: cannot bound spend that does not cross the gateway - isolation time, tool calls, and any descendant that never issues a completion request - and cannot express one ceiling per root unit of work, because its unit is a key within a time window rather than a run tree. It also binds only while the gateway is reachable. | Select the enforcement point by configuration, replay the same corpus of dispatches through both, and compare the refusal sets: assert that every refusal the gateway produced is also produced by the lease, and record the refusals only the lease produced as the gap the pair exists to expose. Read the enforcement point from the refusal, not from the binding. | claimed | `F-b3-03`, `F-a4-07`, `F-a1-04` "Gateway config, virtual keys, spend ledger" |
| `E-swap-candidate-any-keyed-lease-store` | second | the same four operations served by a platform-held reservation lease drawn before each dispatch: reserve takes a lease against the root unit of work's remaining ceiling, draw pre-checks the priced floor of the next dispatch against what the lease holds, reconcile writes the actual cost through the state seam, and remaining is a pure read at a pinned head. Budget has no adapter column of its own in PASS.md B3 because it is a platform obligation rather than an external dependency, so this is realised on the keyed lease store PASS.md B3 names as the swap candidate for leases. | Proposed: cannot know a cost the provider has not reported yet, so it holds an estimate between dispatch and reconciliation and can over-reserve; cannot refuse a call that bypasses dispatch entirely; and needs its own expiry, because a unit that crashes while holding a lease would otherwise consume the root's ceiling permanently. | Proposed: the axes that differ are unit_of_resource_granted (a key's allowance in a window versus a reservation against one root's ceiling), locus_of_durability_and_verification (the gateway's spend ledger versus the platform's append-only state at a pinned head) and processes_required_for_progress (the gateway must be reachable versus a draw that binds before any metered call). Select by configuration with no code edit between runs, then compare both reports against the same declared gaps. | claimed | `F-b3-16`, `F-b4-02`, `F-b1-04` "any keyed lease store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/gateway/test.sh && python3 harness/gateway/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at fb96f80: exit 0; last lines:   adapter=provider-native asynchronous batch (claim-and-poll) cases=12 passed=12 dispatches=7 refusals=2 overshoot_violations=0 endpoint_marker=batch-job-accepted product_hits=0 \| conformance PASSED: 24/24 cases, 2 binding(s) |
| Deliberate breakage | sed -i '235s#.*#        if estimate >= request.ceiling_micros \* 100:#' harness/gateway/interface.py |
| Expected failure | Measured by tools/measure.py at fb96f80: exit 1; last lines:   ok   product_hits went from 0 to 1 \| passed 16, failed 9 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b4-02` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `xc-budget`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Budget has no capability row in PASS.md B3, so it has no adapter or swap-candidate entity of its own, and the second enforcement point here is recorded against the keyed lease store named as the swap candidate for leases. Should Budget get its own entity pair? | 1-3-1 applied (TARGET T5), the same way xc-budget records its own standard-entity gap: (a) add E-adapter-gateway-virtual-key and E-swap-candidate-platform-budget-lease, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) record the pair against the existing gateway and keyed-lease-store entities and say so in the row, which is what this skill does; (c) leave the pair to a later wave, which would leave this guarantee with one enforcement point. Recommendation followed: (b). The question closes when a ceremony rebuilds the knowledge base and the two entities exist. | Keep the pair on the existing entities, with the reason stated in the adapter row so a reader is not sent to the wrong capability's row. | `F-b3-16`, `T-t5-02` "When a problem comes up, use 1-3-1" |
| How much overshoot does the pre-check actually allow on this stack, and how much latency does it add per call? (xc-budget carries the granularity question; this is the measurement that closes it) | Run the corpus with high per-call cost variance through both enforcement points and record `overshoot_micros_max` and the added per-call latency for each. If the lease's overshoot exceeds one call's worth, the priced floor is the wrong quantity to reserve and the reservation should be the priced ceiling instead. | Reserve the priced floor and assert overshoot is at most one call's worth, which is the bound the definition of done already checks. | `F-b1-06` "Cost is knowable before commitment" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-budget 2831cb4f, 2026-09-03 |
