---
name: xc-budget
description: The budget guarantee as a placement, not a request: every unit of work carries a ceiling that the platform applies outside the unit, and exceeding it terminates that unit rather than the platform. Load it when a run, a workflow, a bounded loop or a delegated sub-agent needs a spend limit, when deciding where the limit is checked and who decrements it, when a request object is about to grow a field that skips or raises its own limit, when work fans out and nobody can say what the whole tree will cost, when a cap only records spend instead of stopping it, when someone asks what happens to half-finished outputs after the money runs out, or when a review asks how a human, an agent and an event all end up under the same ceiling.
---

# xc-budget

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the budget guarantee as a placement: one ceiling per root unit of work, applied by the platform outside the unit that spends, decremented by every descendant of that unit, and terminating that unit and nothing else when it is crossed. | sourced | `F-b4-02`, `F-b4-01`, `E-concern-budget` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |

## Entities

| Entity |
|---|
| `E-concern-budget` |
| `E-capability-model-access` |
| `E-not-running-policy-in-the-gate-path` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| reserve (proposed operation set; PASS.md states the budget contract as one sentence, not as a list of calls) | the root unit of work, its ceiling and currency, and the delegation depth and fan-out bounds that apply to its tree (proposed) | a reservation lease against that root's remaining ceiling, with an owner and an expiry (proposed) | proposed | `F-b4-02` |
| draw (proposed) | a lease, the dispatch about to run, and the priced floor of that dispatch (proposed) | an allowance for that dispatch, or the registered typed refusal when the draw would cross what is left (proposed) | proposed | `F-b4-02`, `F-b4-07` |
| reconcile (proposed) | an allowance and the cost actually incurred, which may arrive long after the work was authorised (proposed) | the root's remaining ceiling recomputed from actuals, never from the estimate that was reserved (proposed) | proposed | `F-b4-02`, `X-end-to-end-047` |
| remaining (proposed) | a root unit of work and a pinned state head (proposed) | what is left of that root's ceiling and the depth and fan-out already consumed by its tree, as a pure read (proposed) | proposed | `X-end-to-end-045`, `T-t2-03` |

### Shapes (JSON Schema 2020-12)

**run-budget (proposed summary shape; the full schema, the reservation lease, the cost record and the three worked declarations are in references/run-budget.md)** (proposed; sources: `F-b4-02`, `X-end-to-end-045`, `X-end-to-end-046`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:budget:run-budget:0.1",
  "title": "RunBudget",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. One ceiling per root unit of work, decremented by every descendant. on_exceed is a const rather than an enum: there is no opt-out to express, so there is no request that carries one.",
  "required": [
    "ceiling_micros",
    "currency",
    "on_exceed",
    "max_delegation_depth",
    "max_fanout"
  ],
  "properties": {
    "ceiling_micros": {
      "type": "integer",
      "minimum": 0
    },
    "currency": {
      "type": "string",
      "pattern": "^[A-Z]{3}$"
    },
    "token_ceiling": {
      "type": "integer",
      "minimum": 0
    },
    "on_exceed": {
      "const": "terminate_unit"
    },
    "max_delegation_depth": {
      "type": "integer",
      "minimum": 1,
      "default": 3
    },
    "max_fanout": {
      "type": "integer",
      "minimum": 1,
      "default": 20
    },
    "mid_run_outcome": {
      "enum": [
        "continue",
        "narrow",
        "require_approval",
        "stop"
      ],
      "default": "stop",
      "description": "What a mid-run control does when the remaining ceiling crosses a warning band. It never includes carrying on past zero."
    }
  }
}
```

**budget-exhausted refusal (proposed worked instance; the type is the registered row of the closed registry in docs/decomposition.md section 2.1.6 and cap-errors owns the object)** (proposed; sources: `F-b4-07`, `F-b4-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:budget:exhausted-instance:0.1",
  "title": "BudgetExhaustedInstance",
  "description": "Proposed. The one failure this guarantee returns, shown rather than described. It is a problem object, never prose, and retryable is false because the ceiling does not refill on its own.",
  "allOf": [
    {
      "$ref": "urn:agentic:problem:0.1"
    }
  ],
  "examples": [
    {
      "type": "urn:agentic:problem:budget-exhausted",
      "title": "Budget exhausted",
      "status": 402,
      "detail": "step fix#2 would draw 200200 micros against 118300 remaining on root run run-human-0001",
      "stop_reason": "budget_exhausted",
      "retryable": false,
      "correlation": {
        "run_id": "run-human-0001",
        "correlation_id": "corr-human-0001",
        "depth": 1
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every unit of work carries a ceiling, and crossing it ends that unit and nothing above it. A run with no ceiling is not a cheap run, it is an unbounded one, and a crossing that takes the platform down with it has confused the unit for the host. | sourced | `F-b4-02`, `E-concern-budget` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| The tree is bounded by an explicit maximum delegation depth and maximum fan-out carried on the root budget, refused at dispatch rather than discovered when the money runs out. A cost bound alone lets one root spawn an unbounded number of cheap descendants, and the records on file show a shipped product reaching for exactly these two bounds. | sourced | `X-end-to-end-046` "capped concurrently-running subagents at 20 and stopped subagents from spawning nested subagents" |
| cap-errors owns the failure object (F-b4-07). What this guarantee adds is that its refusal is the registered budget-exhausted row, carrying stop_reason budget_exhausted and retryable false, so a caller branches on a type and never on the words 'budget' appearing in a message. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| A unit terminated on budget keeps the outputs that were already durable, as a partial rather than a loss. The records on file argue that returning what exists beats returning nothing, and a ceiling that also destroys paid-for work charges twice for one overrun. | sourced | `X-xc-budget-005` "allow systems to return partial results instead of failing completely" |
| The reference example in docs/reference/composable-plan.md: a stop and a cap are opposite terminations and are never collapsed into one halt. A stop condition firing means the work is done and the unit terminates as a success; a cap firing means an unbounded unit ran long and the unit terminates as a failure that escalates to a person. One shared halt reason makes a success indistinguishable from an escalation in the ledger, and the reference records that merge as a mistake already made once. | sourced | `REF-5-3-08`, `REF-5-3-03`, `REF-5-3-04`, `REF-12-14` "`stop` and `cap` are opposites and must not be collapsed" |
| The same reference: a step that fans out carries a per-unit share as well as the root ceiling, and a unit crossing its share is a hard ceiling on that unit rather than a draw on its siblings. Without the per-unit share the first unit can spend the root allowance and the rest fail for want of money rather than on their own merits; how many units may fail stays a property of the fan-out, not of the unit and not of the plan. | sourced | `REF-5-3-01`, `REF-5-3-07`, `REF-12-14` "per-unit budget \| the step \| one unit exceeds its share \| throws, hard ceiling" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| There is no field, header, role or configuration flag that skips the check, raises a ceiling from inside the unit it bounds, or converts a stop into a warning. Cross-cutting guarantees are not optional, and the only honest way to say so in a schema is to leave nothing to set. | sourced | `F-b1-08`, `F-b4-01` "Cross-cutting guarantees are not optional" |
| cap-model-access already keeps the measured property that a scoped key with a hard budget cap stops spend (F-a4-07). What this guarantee refuses to expose is the opposite: a ceiling that appears only as a number in a report, since a limit that is observed after the fact is a speed limit sign and not a governor. | sourced | `F-a4-07` "with a hard budget cap" |
| agentic-stack states design rule 6 (F-b1-07). What it forbids here specifically: neither the budget object nor the refusal it returns may carry the criterion a result will be judged against, because a detail string written to explain an overrun is an easy place for the rule to leak to the thing being graded. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put the ceiling on the entry envelope, required on every entry, with on_exceed as a const rather than an enum, and reject an envelope that omits it instead of defaulting one in. | The platform applies the guarantee rather than the caller requesting it, so the schema must offer nothing to negotiate. A default ceiling silently invented at intake is an unbounded run wearing a number. | sourced | `F-b4-01`, `F-b4-02` "The platform applies each; a caller cannot decline them" |
| 2 | Proposed (docs/decomposition.md section 2.1.4): enforce outside the unit. Take a reservation lease at dispatch against the root's remaining ceiling, pre-check every metered call against what the lease still holds, reconcile with the actual cost afterwards, and expire an unreconciled reservation at the deadline plus grace. Research query: see the reservation-lease research query on the budget invariant row below. | A unit that enforces its own ceiling can decline to. cap-model-access records the substrate's measured behaviour here (F-a4-07): scoped keys already stop spend rather than note it, so matching that model is the smaller change, and the lease is what stops a crashed unit from consuming a root's ceiling forever. | proposed | `F-a4-07`, `F-b4-02` "terminate spend rather than merely record it" |
| 3 | Proposed: carry the root run identifier on every descendant dispatch and decrement the one root ceiling from every one of them, so the delegation tree shares a ceiling rather than each level receiving a fresh one. | Per-key and per-call caps bound a key and a call, not a tree. Every cross-cutting concern is managed across the whole structure whichever entry point was used, and a budget that resets at each hop is managed per hop. | sourced | `T-t2-03`, `X-end-to-end-045` "State, telemetry, and every cross-cutting concern are managed across the entire structure" |
| 4 | Proposed: set a maximum delegation depth and a maximum fan-out on the root budget and refuse the dispatch that would cross either, rather than letting the cost ceiling discover the runaway afterwards. Research query: has the depth-3/fan-out-20 pair actually been measured against this platform's own delegation tree, or is it carried over unmodified from one search-only record about a different product? | Cost is the slowest of the three signals: a root can spawn an unbounded number of individually cheap descendants and only the depth and fan-out bounds catch that before the spend does. The records on file show these two bounds being added to a shipped agent fleet and then tuned, which is the shape of the problem rather than a value to copy. | proposed | `X-end-to-end-046` "reinstated nesting at a default depth of 3" |
| 5 | Compare the plan's priced floor with the remaining ceiling before anything is dispatched, and refuse there when the floor already exceeds it, rather than starting work that cannot finish. | Cost is knowable before commitment because planning completes before execution begins, so the cheapest refusal is available for free. The policy row of PASS.md B4 states the analogous rule for refusals, that they are deterministic and happen before execution rather than after spend; this row proposes the same placement for the ceiling. | sourced | `F-b1-06`, `F-b4-04` "Planning is a pure function and completes before execution begins." |
| 6 | Return the registered budget-exhausted problem object with status 402 and retryable false, set the unit's stop reason to budget_exhausted, and leave every already-durable output in place as a partial. | cap-errors owns the failure object and its closed type registry (F-b4-07); this guarantee only supplies one registered row of it. Discarding durable outputs on the way out would charge for the work twice, once in money and once in the result. | sourced | `F-b4-07`, `X-xc-budget-005` "Typed and machine-readable. Never parsed from prose" |
| 7 | Wire the identical check on every way in and prove it by replaying one corpus through each: a human entering the system, an agent entering the system, and an internal or external event entering the system. | TARGET T1 names those three ways in, and a guarantee that is only wired on the path someone remembered is declinable by choosing another door. Running one corpus through each door is what turns 'cannot be declined' into a count. cap-model-access states the same record (T-t1-01) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-03` "An internal or external event must be able to enter the system." |
| 8 | Proposed: write the cost record in a published cost-and-usage vocabulary that already models split cost allocation, rather than inventing columns, and keep the estimate and the reconciled actual as separate members. Research query: has FOCUS 1.3's split-cost-allocation dataset actually been fetched and checked against this guarantee's reconcile shape, rather than adopted from a search-only announcement of its ratification? | Splitting one shared cost across the descendants that caused it is exactly the run-scoped problem here, and a ratified specification already has those columns. The records naming it are search results rather than pages that were read, so its version is unverified and no version string is asserted here. | proposed | `X-end-to-end-047`, `X-end-to-end-048` "columns for splitting shared costs" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Judge a ceiling by whether it stops a call, not by whether it appears in a report: cap-model-access carries the measured property that this substrate's scoped keys already do the former (F-a4-07). Any candidate mechanism that cannot refuse the next call is telemetry with a threshold. | sourced | `F-a4-07` "verified to terminate spend rather than merely record it" |
| agentic-stack already states the structurally-green-gate finding (F-a7-03). What it adds here: a budget check that ran over a corpus containing no expensive dispatch reports the same green as one that caught an overrun, so assert the number of dispatches actually checked and the number of ceilings actually crossed, never the exit code alone. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack already states the silently-discarded-configuration finding (F-a7-04). What it adds here: a cap that was written where the documentation says is not a cap that took effect, so prove enforcement by observing a refused call, not by reading the row or the file that declares the limit. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Do not let exhaustion turn into a silent retry on something cheaper. The records on file describe automatic fallback chains as graceful degradation, and applied to a ceiling that converts a stop the caller can see into a narrowing nobody recorded; narrowing is one of the declared mid-run outcomes and it is written down when it happens. | sourced | `X-xc-budget-004` "automatically retry with a fallback chain of alternative models" |
| Treat a cap that lives only at the model gateway as bounding only what flows through the gateway. The records on file describe the gateway pattern and describe quotas as tokens per user or key within a time window, which is not the same shape as one ceiling per run tree, and it never sees spend that happens anywhere else. | sourced | `X-xc-budget-001`, `X-xc-budget-003` "restricting how many tokens each user or API key can consume within a time window" |
| Keep the check in the enforcement path rather than beside it. The inventory of what runs today already records a concern whose conformance checks exist and are not wired into the path that enforces them, which is the exact failure this layer exists to avoid repeating for budget. | sourced | `F-a6-04`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first implementation of this guarantee (docs/decomposition.md section 3.4 row X1): `python3 tools/conformance_budget.py --corpus out/dispatches.jsonl --min-dispatches 100 --report out/budget-conformance.json`. Over a corpus of at least 100 dispatches it asserts that every dispatch carries a non-null `budget.ceiling_micros`, that every dispatch resolves to exactly one root run id whose descendants all drew from that root's ceiling, and that for every dispatch terminated on budget the recorded spend is at most the ceiling plus one call's worth of overshoot. It reports `dispatches_checked`, `unbounded`, `roots`, `overshoot_violations` and asserts `dispatches_checked >= 100`, `unbounded == 0` and `overshoot_violations == 0`. |
| Expected | exit 0 and one summary line `dispatches_checked=100 roots=<n> unbounded=0 terminated_on_budget=<k> overshoot_violations=0`, with `terminated_on_budget` greater than zero so the overshoot assertion had something to assert on. |
| Deliberate breakage | Make `budget` optional in the dispatch request schema, submit one dispatch without it into the same corpus, and change nothing else. |
| Expected failure | The non-null assertion fails and unbounded dispatches appear: `unbounded` becomes 1, the run exits non-zero naming the dispatch id with the null ceiling, and `dispatches_checked` stays at or above 100, which is what shows the failure is the missing ceiling rather than a corpus that was never read. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-02` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`, `cap-model-access`

Used by: `compose-loop`, `core-planner`, `seam-dispatch`, `xc-budget-implement`, `xc-enforcement-chain`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| At what granularity is the ceiling enforced: a pre-check before each metered call with a reservation lease, or periodic reconciliation within a tolerance band? (docs/decomposition.md open question 7) | Measure worst-case overshoot in currency units on a workload with high per-call cost variance, and measure the latency the pre-check adds per call. Whichever keeps overshoot inside one call's worth without adding latency a caller can feel wins. | The pre-check with a reservation lease. The substrate's existing behaviour already is the pre-check model, so matching it is the smaller change and the tolerance band would be a new failure mode rather than a saved one. | `F-a4-07`, `F-b4-02` "hard budget cap, verified to terminate spend" |
| The cost-and-usage schema this guarantee should adopt has no E-standard- entity in the knowledge base, so it cannot be entered in contract.standards without rebuilding the knowledge base, which would invalidate the provenance heads of every skill already written. How should the governing standard be recorded until then? | 1-3-1 applied (TARGET T5): (a) add the entity and rebuild the knowledge base, which breaks every written skill's provenance; (b) name the standard in an invariant and an instruction citing the research records, and record the missing entity here; (c) leave the standard unnamed until a later wave. Recommendation followed: (b). Deciding evidence for closing the question is a ceremony that adds the entity as part of a knowledge-base rebuild, at which point this row becomes a contract.standards entry with version_status unverified until the specification is actually fetched and read. | The standard is named in capability terms in instruction 8 and its version is left unverified, because the records naming it are search results rather than pages that were read. | `X-end-to-end-047`, `T-t5-02` "When a problem comes up, use 1-3-1" |
| What are the right defaults for maximum delegation depth and maximum fan-out, and are they per root or per profile? | Run the consumption reference's fan-out workflow at increasing depth and width and record where the marginal descendant stops paying for itself. The one datum on file is a product that capped concurrent descendants at twenty, removed nesting entirely, then reinstated it at depth three within three days, which says the values are tuned rather than derived. | Depth 3 and fan-out 20 on the root budget, carried in the shape above and marked proposed, since they come from one search-only record about another system. | `X-end-to-end-046` "on July 24, version 2.1.219 reinstated nesting at a default depth of 3" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-budget 2831cb4f, 2026-09-03 |
