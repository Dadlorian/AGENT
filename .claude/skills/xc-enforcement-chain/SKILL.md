---
name: xc-enforcement-chain
description: One ordered interception chain through which every unit of work passes, whichever way it entered: six typed slots applied in one declared order on the way in and in the inverse order on the way out, at three named points - admission before a work item is accepted, dispatch before a unit runs, and call before each model or tool call. Load it when asking where a cross-cutting guarantee is actually applied rather than what it decides, when a new concern needs somewhere to attach, when one door into the platform received a check the others did not, when a tool chosen at runtime reaches the outside without passing anything, when an agent loop has no ceiling on its own iterations, when an irreversible action is about to run on an approval granted earlier for something else, when someone proposes a fast path around a whole point, a trusted caller or a per-team exemption, or when a review asks what precisely a caller cannot decline.
---

# xc-enforcement-chain

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| xc-typed-errors, xc-budget and xc-correlation each carry one guarantee across every entry point (T-t2-03). This skill fixes the single structure that carries all of them: one ordered chain of typed slots, applied at named enforcement points, entered before anything is spent and unwound in the inverse order on the way out, so that a guarantee is a property of the path rather than of the caller who remembered it. | sourced | `T-t2-03`, `F-b1-08` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |

## Entities

| Entity |
|---|
| `E-concern-budget` |
| `E-concern-identity` |
| `E-concern-policy` |
| `E-concern-provenance` |
| `E-concern-telemetry` |
| `E-concern-errors` |
| `E-concern-idempotency` |
| `E-rule-b1-7` |
| `E-not-running-policy-in-the-gate-path` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| enter (proposed operation set; PASS.md states the cross-cutting concerns as a table of contracts, not as a chain of calls) | the enforcement point being crossed, the unit about to cross it, and the chain context of the enclosing point if there is one (proposed) | a chain context carrying one slot record per declared slot in declared order, or the typed refusal of the first slot that refused; nothing metered runs for a unit that holds no chain context for the point it is crossing (proposed) | proposed | `F-b4-01`, `T-t2-03` |
| exit (proposed) | the chain context handed back by enter, and the outcome of the work the point wrapped, success or failure (proposed) | the same context sealed, with each slot's inverse recorded in the reverse of the entry order, on the failure path as well as the success path (proposed) | proposed | `F-b4-01` |
| attest_chain (proposed) | a corpus of units read at a pinned state head, and the declared slot order (proposed) | per unit and per point: which slots ran, in which order, which inverses ran on exit, and counts of slots_missing, out_of_order, missing_inverse and metered calls reached with no chain context (proposed) | proposed | `F-a7-03` |

### Shapes (JSON Schema 2020-12)

**chain-context (proposed summary shape; the full slot record, the three worked entries and the worked refusal are in references/usage.md)** (proposed; sources: `F-b4-01`, `F-b1-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:enforcement-chain:context:0.1",
  "title": "ChainContext",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. What one traversal of one enforcement point produces. There is no field for a skipped, advisory or deferred slot, and no field in which a caller may supply the order: the order is declared by the platform and the slot list is closed.",
  "required": [
    "point",
    "unit_id",
    "correlation",
    "slots",
    "entered_seq"
  ],
  "properties": {
    "point": {
      "enum": [
        "admission",
        "dispatch",
        "call"
      ],
      "description": "The named enforcement point being crossed. The same chain runs at each."
    },
    "unit_id": {
      "type": "string",
      "format": "uuid"
    },
    "entered_seq": {
      "type": "integer",
      "minimum": 0
    },
    "correlation": {
      "type": "object",
      "required": [
        "run_id",
        "root_dispatch_id"
      ]
    },
    "slots": {
      "type": "array",
      "minItems": 6,
      "description": "One record per declared slot, in declared order: identity resolve, policy decide, budget reserve, telemetry open, idempotency claim, provenance open. A slot may record a no-op; it may not be absent.",
      "items": {
        "type": "object",
        "required": [
          "slot",
          "seq",
          "outcome"
        ],
        "properties": {
          "slot": {
            "enum": [
              "identity.resolve",
              "policy.decide",
              "budget.reserve",
              "telemetry.open",
              "idempotency.claim",
              "provenance.open"
            ]
          },
          "seq": {
            "type": "integer",
            "minimum": 0
          },
          "outcome": {
            "enum": [
              "passed",
              "no-op",
              "refused"
            ]
          },
          "inverse_seq": {
            "type": "integer",
            "minimum": 0,
            "description": "Sequence of this slot's inverse on exit. Inverses run in the reverse of the entry order, whatever the outcome of the wrapped work."
          }
        }
      }
    }
  }
}
```

**chained entry, T6.2's four entries (proposed worked instances; TARGET T6.2 names a human, an event, a schedule and an external system or agent, and the same chain stands at the admission point of all four)** (proposed; sources: `T-t6-02`, `REF-3-4-10`, `REF-3-4-15`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:enforcement-chain:entry:0.1",
  "title": "ChainedEntry",
  "type": "object",
  "description": "Proposed. The minimum a caller supplies is the entry envelope cap-consumption already fixes; the chain is applied to it and there is nothing to add, set or request. What comes back is one result or one problem object. These four are the same envelope entering by all four of TARGET T6.2's doors and traversing the same six slots. The event and schedule rows are not interchangeable: the reference example this repo follows states that an internal event steers work that already exists and never starts it, while a schedule entry starts root work of its own (REF-3-4-10, REF-3-4-15) - so the event row below carries a correlation the run already had, and the schedule row opens a new one.",
  "examples": [
    {
      "entry": {
        "kind": "human",
        "actor": {
          "subject": "user:corey"
        },
        "correlation": {
          "run_id": "run-h-0001",
          "root_dispatch_id": "disp-h-0001"
        }
      },
      "chain": {
        "point": "admission",
        "unit_id": "disp-h-0001",
        "slots_run": 6,
        "refused_at": null
      }
    },
    {
      "entry": {
        "kind": "external",
        "actor": {
          "subject": "agent:partner-sre-bot"
        },
        "correlation": {
          "run_id": "run-a-0001",
          "root_dispatch_id": "disp-a-0001"
        }
      },
      "chain": {
        "point": "admission",
        "unit_id": "disp-a-0001",
        "slots_run": 6,
        "refused_at": null
      }
    },
    {
      "entry": {
        "kind": "event",
        "actor": {
          "subject": "service:alerting"
        },
        "correlation": {
          "run_id": "run-e-0001",
          "root_dispatch_id": "disp-e-0001"
        },
        "note": "steers a live run; admitted only against a correlation that already exists"
      },
      "chain": {
        "point": "admission",
        "unit_id": "disp-e-0001",
        "slots_run": 6,
        "refused_at": null
      }
    },
    {
      "entry": {
        "kind": "schedule",
        "actor": {
          "subject": "schedule:nightly-fault-sweep"
        },
        "correlation": {
          "run_id": "run-s-0001",
          "root_dispatch_id": "disp-s-0001"
        },
        "note": "starts a new root run under the schedule's own standing allocation, not a caller's"
      },
      "chain": {
        "point": "admission",
        "unit_id": "disp-s-0001",
        "slots_run": 6,
        "refused_at": null
      }
    }
  ]
}
```

**worked refusal at the call point (proposed instance; the type is the registered budget-exhausted row of the closed registry in docs/decomposition.md section 2.1.6, and cap-errors owns the object)** (proposed; sources: `F-b4-07`, `F-b4-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:enforcement-chain:refusal:0.1",
  "title": "ChainRefusalInstance",
  "description": "Proposed. What a caller actually receives when a slot refuses, shown rather than described. It names the point and the slot, never the engine or process that decided, and it arrives before the call it refused, so the spend for that call is zero.",
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
      "detail": "enforcement point call, slot budget.reserve: the model call would cross the ceiling of run-e-0001",
      "dispatch_id": "disp-e-0001",
      "retryable": false,
      "correlation": {
        "run_id": "run-e-0001",
        "root_dispatch_id": "disp-e-0001",
        "depth": 2
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| agentic-stack states design rule 7 as a test (F-b1-08): the platform applies the cross-cutting guarantees rather than the caller requesting them. What the chain adds is where 'the platform' is: there is exactly one traversal path from any entry to any metered call, and a call reached without a chain context for its point is a defect that is counted, not a caller's choice. | sourced | `F-b1-08`, `E-rule-b1-7` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| Proposed: the chain's contents are PASS.md B4's concerns - Budget, Identity, Policy, Provenance, Telemetry, Errors, Idempotency - of which six are ordered slots (identity resolve, policy decide, budget reserve, telemetry open, idempotency claim, provenance open) and the seventh, Errors, is not a slot but the shape every slot's refusal takes, so the chain has one return type and not six. Research query: is there a fetched source classifying Errors as the shape every refusal takes rather than a seventh slot, or is that this skill's own reading of B4's seven-row table? | proposed | `F-b4-01`, `E-concern-budget`, `E-concern-identity`, `E-concern-policy`, `E-concern-provenance`, `E-concern-telemetry`, `E-concern-errors`, `E-concern-idempotency` "These are the difference between a working system and a production one." |
| The order is declared and total: every slot runs at every point in the declared order and each has its inverse on exit in the reverse order, on the failure path as well as the success path. A slot may record a no-op; it may not be absent, because the prior art's whole property is that the interceptors surround the target operation regardless of outcome. | sourced | `X-xc-enforcement-chain-005` "Interceptors form a chain that always surrounds and invokes a fixed target operation, ensuring every interceptor executes both before and after the target regardless of outcomes." |
| xc-policy-gate owns the rule that refusal precedes spend (F-b4-04). What the chain adds is that the rule holds at three points and not one: admission, dispatch and every model or tool call each take the decision and the reservation before the thing they wrap begins, so a unit admitted once cannot spend unboundedly afterwards. | sourced | `F-b4-04`, `E-concern-policy` "Refusal is deterministic and happens before execution, not after spend" |
| In-path enforcement at the call point is not redundant with the earlier points, because the thing being enforced against is chosen after them: enforcement must sit where the call is actually made, so that a boundary still refuses when everything upstream was satisfied. | sourced | `X-end-to-end-062` "Infrastructure-level governance provides a hard enforcement boundary even when prompt injection succeeds at the LLM level." |
| xc-typed-errors states that a guarantee holds across the whole structure rather than per entry point (T-t2-03). What the chain adds is that the structure is one object: the same declared slot list, in the same order, at the same three points, whichever of TARGET T1's three ways in was used - so a new door is wired by attaching the chain, never by re-deriving the checks. | sourced | `T-t2-03`, `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| The call point carries two containment controls that no upstream point can supply: a hard ceiling on autonomous iterations, and an approval gate that fires on any action declared irreversible regardless of an approval granted earlier for the run. | sourced | `X-end-to-end-063` "Hard caps on autonomous loops, plan-validation checkpoints, and approval gates on irreversible actions are the typical defenses." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| agentic-stack states design rule 7 (F-b1-08): cross-cutting guarantees are applied by the platform, not requested by the caller. For the chain, declining is inexpressible rather than forbidden: no entry shape carries a slots array, an order array, a skip list, a point selector, a bypass field, a trusted-caller class or an advisory mode, so there is nothing to negotiate and a fast path has no field to live in. The only way a slot does not run is that the platform declared it a no-op for that point, which is recorded in the chain context and counted by the attestation, not left to a caller's configuration. | sourced | `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| agentic-stack states design rule 6 (F-b1-07). What the chain must not expose: the criterion a result will be judged against never travels in a chain context, a slot record or a refusal. A refusal names the point and the slot that refused, never the standard the work would have been measured by. | sourced | `F-b1-07`, `E-rule-b1-7` "An agent sees its outcome, never the criterion it is judged against" |
| No engine, process or product behind a slot appears in a chain context or a refusal. A caller learns which point and which slot refused, which is what they can act on; which implementation decided is configuration and appears only in the conformance report. (agentic-stack and build-skill-authoring apply the same rule generally; this row applies it to a chain refusal specifically.) | sourced | `F-part-c-09` "Products belong in the adapter column only." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Declare the chain once, as an ordered list of typed slots with one owning skill per slot, and let the chain own only two things: the order and the totality. Never restate what a slot decides here. | Proposed: each slot's semantics already belong to a guarantee skill - xc-policy-gate for the decision, xc-budget for the ceiling, xc-correlation for the stamped identifiers, xc-typed-errors for the refusal shape. A chain that also decides is a second owner for every rule, and the two owners drift. Research query: is there a fetched source on a single-owner-per-concern rule for an interception chain specifically, or is that this skill's own extension of the sidecar/AOP prior art it cites elsewhere? | proposed | `F-b4-01` |
| 2 | Name the enforcement points and put the same chain at each: admission, before a work item is accepted; dispatch, before a unit runs; call, before each model or tool call. Add a point by naming it, never by adding a check somewhere unnamed. | cap-policy already draws the consequence for its own decision that runtime tool choice defeats a plan-time check; the chain's consequence is structural: the call point is the only place that sees the arguments a unit actually chose, so a platform with only admission and dispatch points is enforcing against a plan and not against a call. | sourced | `X-end-to-end-062`, `X-cross-structure-030` "Dynamic tool-switching, where agents select tools at runtime, defeats static policy." |
| 3 | Order the slots so that everything that can refuse runs before anything that can spend, and record each slot's sequence position as it runs: identity resolve, policy decide, budget reserve, telemetry open, idempotency claim, provenance open. | xc-policy-gate owns the ordering rule for the decision and xc-budget owns the ceiling; what the chain adds is that both are positions in one list, so 'before spend' is checkable as a sequence rather than argued per call site. | sourced | `F-b4-04`, `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| 4 | Run each slot's inverse on exit, in the reverse of the entry order, and run it on the failure path too: reserve is reconciled, the claim is settled, the span and the provenance record are closed whether the unit succeeded, refused or crashed. | The prior art's defining property is that the chain surrounds the target operation and executes on both sides regardless of outcome; an exit that runs only on success leaks reservations and leaves open spans exactly on the runs that most need reading. | sourced | `X-xc-enforcement-chain-005` "ensuring every interceptor executes both before and after the target regardless of outcomes" |
| 5 | Make traversal automatic: attach the chain where units are constructed and calls are issued, so that no engineer adds a call to it and no configuration step is required to get it. | cap-policy already draws this consequence for automatic consultation of its decision; for the chain the same mechanism is what makes 'cannot decline' true, because a step that has to be remembered is declined by being forgotten, and the forgetting is silent. | sourced | `X-cross-structure-024`, `X-cross-structure-025` "there's no need for engineers to remember extra config steps" |
| 6 | Give the call point a hard ceiling on autonomous iterations and a gate that fires on any action declared irreversible, and make the irreversible gate fire regardless of an approval already granted for the run. | These are the containment controls the risk taxonomy on file names, and neither can be supplied upstream: an iteration count only exists once the loop is running, and an approval granted at admission was granted for a plan, not for the specific irreversible action a later turn chose. | sourced | `X-end-to-end-063`, `X-end-to-end-061` "Hard caps on autonomous loops, plan-validation checkpoints, and approval gates on irreversible actions are the typical defenses." |
| 7 | Wire the identical chain on each of TARGET T6.2's four entries - a human, an event, a schedule and an external system or agent - and prove it by replaying one corpus through each door and asserting the same slot order, the same inverses and zero ungated metered calls for all four. A schedule entry starts a new root run under its own standing allocation; an event entry only steers a run that already exists and is admitted just where a correlation for it is already open (REF-3-4-10, REF-3-4-15). | cap-work-intake carries the four-door claim this reads from (T-t6-02). A guarantee wired only on the path someone remembered is declined by choosing another door, and entry is where doors multiply. Replaying one corpus through each of the four is what turns 'whichever entry point was used' into a number, and treating schedule as a fourth alias of T1's three ways in would leave the one door that mints its own root work unchecked. | sourced | `T-t6-02`, `REF-3-4-10`, `REF-3-4-15` "Four entries cover nearly every situation: a human, an event, a schedule (time), and an external system or agent." |
| 8 | Return the refusal of the first slot that refuses as one typed problem from the closed registry, naming the point and the slot in its detail, and stop the traversal there rather than collecting further refusals. | xc-typed-errors owns the rule that no failure is discovered by matching a string; what the chain adds is that a caller who sees one object still learns where in the chain it stopped, which is the only part of the traversal they can act on. | sourced | `F-b4-07`, `E-concern-errors` "Typed and machine-readable" |
| 9 | For usability, add nothing to the caller's side: a human, an agent and an event all reach the chain by submitting the entry envelope cap-consumption fixes, supply no slot, flag or order, and read back either one result or one problem object naming the point and slot that refused. | Proposed: the chain is the part of the platform a caller most wants to configure and least should, so the usability answer is that there is no chain-shaped input at all; cap-consumption states the caller doctrine once, and restating it here would give it a second owner. Research query: has a caller ever been observed reaching for a chain-shaped input field (a slot list, an order override) before this row asserted there is none to reach for, or is the absence purely a design choice with no counter-example on file? | proposed | `T-t6-02`, `T-t3-01` |
| 10 | Proposed: open references/usage.md when you need the full chain-context and slot-record schemas, the three complete worked entries, the worked refusal in full, or the slot-to-owner table. The body of this skill is enough to judge a chain and to place a point without it. | Proposed: the full schemas and three complete envelopes exceed the progressive-disclosure budget for a skill body, and a reader deciding whether a call is on the chain does not need them open. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| cap-policy already cites this record for consulting one decision everywhere; what the chain adds is the reason to define the whole set once rather than concern by concern: a single composition point is what keeps the unit's own logic free of them, so a new concern is added in one file rather than in every agent. | sourced | `X-cross-structure-026` "keeping the core reasoning focused on business goals while shared concerns stay centralized" |
| Prefer a placement that can enforce against a workload you cannot modify. The prior art on file describes a helper process alongside the application handling the cross-cutting concerns with no change to the application, which is the only shape that also works for an agent runtime or a tool server we did not write; the records are search results rather than pages that were read. | sourced | `X-cross-structure-020` "A sidecar is a helper process that runs alongside your application and handles cross-cutting concerns without touching the application code." |
| Treat enforcement as inherently cross-cutting rather than as a component's own business: the records on file describe policy-relevant events spanning agents, models, services and tools, which is why a per-component check leaves the gaps between components unguarded. | sourced | `X-xc-enforcement-chain-003`, `X-xc-enforcement-chain-006` "making policy enforcement cross-cutting rather than local to any single component" |
| cap-policy already states that interoperability protocols cannot enforce governance semantics. What this adds for the chain, as this skill's own proposed consequence: adopting a protocol at the door buys transport, not enforcement, so the chain is what a new door inherits and the protocol choice never changes which slots run. | sourced | `X-entry-composition-059`, `X-entry-composition-060` "Current protocols can transport governance-related messages as opaque payloads" |
| agentic-stack already states the structurally-green-gate finding (F-a7-03). What it adds here, as this skill's own proposed consequence: report metered calls and slot executions alongside the zero counts, because a corpus in which nothing spent and a corpus that is properly chained both print zero ungated calls. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack already states the silently-discarded-configuration finding (F-a7-04). What it adds here, as this skill's own proposed consequence: prove a point is on the chain by watching a call be refused at it on the live path, not by reading the wiring that installed it; an installed chain and an enforced chain are indistinguishable from the file. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Proposed: fail closed at slot granularity. A slot whose owner is unreachable is a refusal returned as the registered adapter-unavailable row, not a no-op and not a pass-through; a chain that thins itself under load has removed exactly the guarantees that load makes expensive. Research query: is there a fetched source recommending fail-closed behaviour at the granularity of one slot (versus the whole chain or the whole point), or is that this skill's own extension of the general fail-closed principle? | proposed | `F-b4-01`, `F-b4-07` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 harness/xc-enforcement-chain/conformance.py --adapter dryrun --adapter second --min-units 100 |
| Expected | exit 0, last line `conformance PASSED: 26/26`, with one summary line per enforcement point reading `ways_in=human,event,schedule,external points=admission,dispatch,call units_checked=104 metered_units=96 slots_missing=0 out_of_order=0 missing_inverse=0 ungated_metered_calls=0 chain_context_missing=0`, then `adapters_run=2` and identical chain records from both points (records_digest=db7461f6c118): metered_units is above zero, so the ordering assertion had something to order against. What this run stands in for: the criterion this facet carried before ceremony 61 (finding R61B-018) moved its prose out of the criterion field, which is the check this guarantee ultimately needs and which nothing on disk runs yet - The manifest row for this piece, made precise: `python3 tools/conformance/enforcement_chain.py --corpus out/units.jsonl --points admission,dispatch,call --ways-in human,event,schedule,external --min-units 100 --report out/chain.json` (proposed tool, built with the first chained point). Reading a pinned state head, for every unit and every point it crossed it asserts that a chain context exists, that all six declared slots appear with strictly increasing `seq` in the declared order, that each slot's inverse appears on exit with `inverse_seq` in the reverse of that order including on units that failed, and that no metered call has a start sequence earlier than the last entry slot of its point. It reports `units_checked`, `ways_in`, `points_covered`, `metered_units`, `slots_missing`, `out_of_order`, `missing_inverse` and `ungated_metered_calls`, and asserts `units_checked >= 100`, `metered_units > 0`, all four of TARGET T6.2's entries covered (human, event, schedule, external), that every schedule-entered unit started a new root run rather than steering an existing one and every event-entered unit steered an existing correlation rather than starting one, all three points covered, and `slots_missing == out_of_order == missing_inverse == ungated_metered_calls == 0`. Expected of that check: exit 0 and one summary line `units_checked=100 ways_in=human,event,schedule,external points=admission,dispatch,call metered_units=<m> slots_missing=0 out_of_order=0 missing_inverse=0 ungated_metered_calls=0`, with `metered_units` greater than zero so the ordering assertion had something to order against. |
| Deliberate breakage | sed -i 's/if self.refuses_unchained:/if False:/' harness/xc-enforcement-chain/interface.py -- a metered call that arrives with no chain context for the call point is charged instead of refused, so the chain becomes advisory at the one place that spends. Restore with git checkout harness/xc-enforcement-chain/interface.py. |
| Expected failure | exit 1 with ungated_metered_calls above zero on the enforcement point that no longer refuses, while slots_missing, out_of_order and missing_inverse stay 0 and units_checked stays at or above 100 - which shows the corpus was still read and the assertion still ran rather than the run having gone empty. Status claimed: tools/measure.py has recorded neither run for this pair here. The breakage the prose criterion above stood for, and what it expected: Activate a policy bundle that denies everything and replay the same corpus through all four entries, changing nothing else: every unit must now be refused at the `policy.decide` slot of the first point it reaches, with `metered_units == 0` and a refusal recorded for every entry. exit 1 naming any entry that still produced a completed unit or a non-zero metered call under deny-all - that path is reaching work without traversing the chain - while `slots_missing`, `out_of_order` and `missing_inverse` stay 0 and `units_checked` stays at or above 100, which shows the corpus was still read and the assertion still ran rather than the run having gone empty. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-01` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-research-record`, `build-ceremony`, `cap-policy`, `xc-budget`, `xc-policy-gate`, `xc-typed-errors`, `cap-work-intake`, `xc-correlation`

Used by: `xc-enforcement-chain-implement`, `xc-tenancy`, `xc-compensation`, `xc-audit-trail`, `xc-audit-trail-implement`, `build-entry-conformance`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should `idempotency.claim` run before `budget.reserve` rather than after it, so that a replayed unit cannot draw a reservation it will never use? | Replay a corpus containing duplicate idempotency keys under both orders and read the reservation store afterwards: whichever order leaves no reservation drawn for a unit that was deduplicated is the one that satisfies the zero-spend property literally rather than by reversal. Count the reservations released by the exit inverse under the current order; if that count is non-zero in normal operation, the order is wrong. | Keep the declared order (identity, policy, budget, telemetry, idempotency, provenance) because it is what the manifest row for this piece names, and rely on the exit inverse to release a reservation held by a deduplicated unit. The question closes when the replay above has been run. | `F-b4-08`, `F-b4-02`, `T-t5-02` "Every externally-triggered action is safe to replay" |
| This guarantee has no governing standard: the pattern it implements is advice applied at a pointcut, and the records on file name it as prior art rather than as a specification. Should a standard be recorded for it anyway? | 1-3-1 applied (TARGET T5): (a) mint a standard entity for the interception pattern, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) carry no standards row here and let each slot's own capability name the standard that governs it, which is what this skill does; (c) adopt an unrelated transport standard as a proxy, which would name a specification that does not govern this. Recommendation followed: (b). The question closes if an interception or enforcement-placement specification is ever ratified and entered as an entity. | No standards row here. Each slot's capability names its own standard, and this skill states only the order, the points and the totality. | `X-cross-structure-029`, `F-b1-03`, `T-t5-02` "AOP adds behavior to existing code (an advice) without modifying the code" |
| Refusal by absence - a credential that simply cannot reach a forbidden destination - is a second shape of enforcement that needs no chain traversal at all. Does it replace a slot at the call point, or sit under it? | Count the call-point refusals that a credential scope would have made impossible in the first place. If the two sets are equal the slot is buying only an error message; if the chain refuses cases the credential cannot express, both are needed and the chain is the place the refusal becomes typed. | Both, with the chain on top: cap-mandate-broker owns the credential that cannot reach the destination, and the call point still runs its slots so that a refusal is a typed problem rather than an unexplained connection failure. | `F-b4-07`, `T-t5-02` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-enforcement-chain 2831cb4f, 2026-09-03 |
