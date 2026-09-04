---
name: "xc-enforcement-chain-implement"
description: "How to make the enforcement chain real on this stack: a first implementation that wires the three points already enforcing on this host - the approval unit at admission, the dispatcher at dispatch, the host broker and the gateway's scoped key at the call - into one chain with one shared context, a second implementation that runs out of process and admits nothing it has not seen, the migration off three unrelated checks that share no context, where correlation, provenance, identity and typed refusals attach to a slot, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that enters or exits an enforcement point, when a call site is reached with no chain context, when deciding whether the second implementation should be in-process or beside the workload, when a slot has no owner running yet and must not be reported as passed, or when an attestation is green on one implementation and red on the other."
---

# xc-enforcement-chain-implement (folded into `xc-guarantees`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the ordered chain xc-enforcement-chain defines into something that runs here: two implementations behind one chain contract, the second placed outside the process so that a unit which never calls the chain cannot proceed, adopted without a window in which a door runs unchained, and honest about the slots whose owners are not running on this host yet. | sourced | `F-a6-04`, `F-a6-05` "No identity field anywhere in the system" |

## Entities

| Entity |
|---|
| `E-host-unit-approve-service` |
| `E-sandbox-property-model-egress` |
| `E-sandbox-property-field-filtering` |
| `E-not-running-policy-in-the-gate-path` |
| `E-not-running-identity` |
| `E-not-running-typed-errors` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:enforcement-chain:pair-axes:0.1",
  "title": "EnforcementChainPairAxes",
  "description": "Proposed. The three axes on which the two chain implementations differ, stated as properties rather than product names. measured stays false until the swap has been executed and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "locus_of_traversal",
        "today_value": "in the process that constructs the unit and issues the call, which must be built to enter the chain",
        "second_value": "in a separate process the unit's traffic must cross, which admits or refuses whatever arrives",
        "measured": false
      },
      {
        "axis": "processes_required_for_progress",
        "today_value": "one process; a chain failure and a unit failure are the same fault",
        "second_value": "two; the unit cannot proceed while the admitting process is unreachable, which is a refusal rather than a bypass",
        "measured": false
      },
      {
        "axis": "reach_over_unmodified_workloads",
        "today_value": "none; a runtime or tool server we did not write is never chained",
        "second_value": "full; the workload is unchanged and the chain runs beside it",
        "measured": false
      }
    ]
  ]
}
```

**chain-conformance report (proposed; the fields the definition of done asserts on, written per implementation and once across implementations)** (proposed; sources: `F-a7-03`, `F-a6-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:enforcement-chain:implement-report:0.1",
  "title": "EnforcementChainImplementReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. Written per implementation so a green run names what it actually checked, and once across implementations so a swap that never ran cannot report as two.",
  "required": [
    "adapter",
    "ways_in",
    "points_covered",
    "units_checked",
    "metered_units",
    "slots_missing",
    "out_of_order",
    "missing_inverse",
    "ungated_metered_calls",
    "chain_context_missing",
    "adapter_observed"
  ],
  "properties": {
    "adapter": {
      "type": "string",
      "description": "The entity id of the implementation under test."
    },
    "adapter_observed": {
      "type": "string",
      "description": "Read from the refusal that came back, never from the binding that selected the implementation."
    },
    "ways_in": {
      "type": "array",
      "items": {
        "enum": [
          "human",
          "event",
          "schedule",
          "external"
        ]
      },
      "description": "TARGET T6.2's four entries, not T1's three ways in: schedule starts a new root run and event only steers an existing one."
    },
    "points_covered": {
      "type": "array",
      "items": {
        "enum": [
          "admission",
          "dispatch",
          "call"
        ]
      }
    },
    "units_checked": {
      "type": "integer",
      "minimum": 0
    },
    "metered_units": {
      "type": "integer",
      "minimum": 0
    },
    "slots_missing": {
      "type": "integer",
      "minimum": 0
    },
    "out_of_order": {
      "type": "integer",
      "minimum": 0
    },
    "missing_inverse": {
      "type": "integer",
      "minimum": 0
    },
    "ungated_metered_calls": {
      "type": "integer",
      "minimum": 0
    },
    "chain_context_missing": {
      "type": "integer",
      "minimum": 0,
      "description": "Units that reached a point with no chain context at all. Separates a lost binding from a chain that ran and skipped a slot."
    },
    "slots_noop_by_absent_owner": {
      "type": "integer",
      "minimum": 0,
      "description": "Slots recorded no-op because their owner is not running on this host yet. Reported, never counted as passed."
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
| Proposed: the two implementations differ on three of build-adapter-pair's axes - locus_of_traversal, processes_required_for_progress and reach_over_unmodified_workloads - recorded in the shape above. A second in-process chain written in another language would agree with the first on all three, so swapping to it would test a library rather than the placement. | proposed | `F-b1-04` |
| xc-enforcement-chain owns the declared slot order, the three named points and the totality rule (T-t2-03). What this build adds is that both implementations must satisfy the same attestation over the same corpus and the same three doors, so an implementation that cannot show a zero for slots_missing and ungated_metered_calls is not an alternative, it is unfinished. | sourced | `T-t2-03` "every cross-cutting concern are managed across the entire structure" |
| agentic-stack states design rule 1 as a test (F-b1-02). Its consequence here: which implementation traversed the chain is configuration. No core code, no workflow and no caller branches on it; the implementation appears in the conformance report and in adapter_observed, never in a field a caller can read and route on. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| agentic-stack states that what runs is substrate (F-part-c-11). Its consequence here: the three points that already refuse on this host - the approval unit, the broker holding the real credential, the gateway's scoped key - are not replaced. They become the first implementation's slots, joined by one shared chain context, and the out-of-process implementation is added beside them rather than instead of them. | sourced | `F-part-c-11`, `F-a2-01` "Part A is substrate, not scope. Do not propose replacing what runs." |
| A slot whose owner is not running on this host is recorded as a no-op and counted, never reported as passed: this host has no identity field anywhere, typed errors are absent, and the decision engine is not on the enforcement path, so the first attestation is honestly partial and the counts say which slots are hollow. | sourced | `F-a6-05`, `F-a6-06`, `F-a6-04`, `E-not-running-identity` "\| Typed errors \| Absent \|" |
| Apply build-evidence-record: every statement here about how an implementation behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test, and rewording a sentence never upgrades a label; proposed pointer, see that skill. | proposed | `F-a5-04`, `F-part-c-08` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the first implementation by joining the three points that already refuse on this host into one chain with one shared context: the host approval unit at admission, the dispatcher at dispatch, and the broker that holds the real credential together with the gateway's scoped key at the call. | These are the only places on this host that stop anything today, and they share no context, so a unit refused at one is invisible at the others. xc-budget already records that the scoped key terminates spend rather than merely recording it; joining the three is what turns three unrelated checks into the chain xc-enforcement-chain defines. | sourced | `F-a2-01`, `F-a3-07`, `F-a4-07` "verified to terminate spend rather than merely record it" |
| 2 | Record every slot whose owner is not running yet as a no-op with the reason, and surface the count as slots_noop_by_absent_owner; never let an absent owner render as a passed slot. | Three of the six slots have no owner running on this host: there is no identity field anywhere, typed errors are absent, and the decision engine is defined but off the enforcement path. A chain that reports six passed slots over three hollow ones is the structurally-green gate with a new name. | sourced | `F-a6-05`, `F-a6-06`, `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |
| 3 | Proposed: build the second implementation out of process - a helper beside the workload, or an admission step in front of it - that sees the unit's traffic at a boundary it cannot route around, runs the same declared slots, and refuses anything arriving without a context it issued. | Proposed: this breaks the assumption the first implementation rests on, that everything which starts work was built to enter the chain. An out-of-process placement chains an agent runtime or a tool server we did not write, and its unreachability is a refusal rather than a silent bypass, so the two fail for different reasons. | proposed | `X-cross-structure-020`, `F-b1-04` |
| 4 | Apply build-adapter-pair: record differs_in_execution_model from the shape above, leave measured false until the swap has actually been run, and write each implementation's gaps down as gaps rather than as caveats; proposed pointer, see that skill. | differs_in_execution_model, its axes and the rule that measured stays false until the swap has run belong to build-adapter-pair, and swappability is the design rule this pair exists to satisfy rather than assert. | sourced | `F-b1-04` "Swappability is a tested property, not an intention." |
| 5 | Adopt in three stages with no window in which a door runs unchained: shadow, where both implementations enter and exit while the unit proceeds and ungated_metered_calls and chain_context_missing are counted; compare, where the two refusal sets are reconciled over one corpus; then enforce, where the context check is switched on at all three points and all three doors at once. | The shadow stage is the only one in which a disagreement is cheap, and it is where calls made by code that never enters the chain are first counted. Switching one point or one door at a time leaves the others open while the report already reads green, which is the structurally-green-gate finding agentic-stack records applied to a rollout. | sourced | `F-a7-03`, `F-part-c-11` "Those establish well-formedness, not correctness" |
| 6 | Wire the cross-cutting guarantees onto the slot records themselves: stamp the run identifier and root dispatch identifier as explicit attributes on every slot and inverse, and append them through the append-only chained store so the attestation reads them at a pinned head rather than from the chain's own memory. | agentic-stack states that correlation must ride on an explicit attribute set at dispatch (F-a7-02) because parentage did not survive the agent boundary, and that the chained store makes a later edit detectable (F-a5-03). An ordering claim read out of the process that enforced it is that process vouching for itself. | sourced | `F-a7-02`, `F-a5-03` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Read which implementation enforced from the refusal that actually came back and put that value in adapter_observed, never from the binding, the unit file or the configuration that selected it. | agentic-stack states the silently-discarded-configuration finding (F-a7-04), measured on this host: values written where the documentation says were overlaid by a stored row. A chain believed installed because it was configured is that failure with an enforcement decision attached. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 8 | Run the definition of done below over both implementations and each of TARGET T6.2's four entries, then run its breakage, and record both outputs as evidence records naming the script hash, the commit, the tree hash under test and whether the tree was dirty. | build-evidence-record fixes what a record contains (F-a5-04); a result from a dirty tree is not reproducible and may not be labelled measured. Running the breakage is what shows the attestation can fail rather than that it merely passed. | sourced | `F-a5-04`, `F-part-c-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Report metered_units and slots_noop_by_absent_owner per implementation: one corpus replayed through two implementations can leave the out-of-process one with nothing to admit and still exit green, the way a nine-stage pipeline ran green because the generated work contained nothing those tools apply to (F-a7-03, agentic-stack's finding, whose gate-level consequence build-definition-of-done owns; xc-enforcement-chain owns the consequence for the four zero counts). | sourced | `F-a7-03` "because the generated work contained nothing those tools apply to" |
| Expect the two implementations to disagree during the shadow stage and treat the difference as the finding rather than as noise. Where it lands in code is chain_context_missing and ungated_metered_calls: the calls made by code that was never built to enter the chain, which the in-process implementation can never report on itself. | sourced | `X-cross-structure-020` "handles cross-cutting concerns without touching the application code" |
| Proposed: make traversal a property of deployment rather than of a code review. Attach the chain where units and calls are constructed, and let the out-of-process implementation be injected at deploy time, so a new component is chained by existing, not by remembering; xc-enforcement-chain states the rule and this is where it lands in the build. | proposed | `X-cross-structure-024` |
| Proposed: keep the conformance run on the same code path a live unit takes, replaying the corpus through the real enter and exit calls. A suite that reads a stored corpus and never touches the chain reproduces exactly the state this build exists to leave behind: a check that exists beside an enforcement path that does not consult it. | proposed | `F-a6-04` |
| Proposed: give the out-of-process implementation no degraded mode. Under load or on partial failure it refuses with the registered adapter-unavailable row rather than admitting unchained traffic, because a chain that thins itself when busy removes its guarantees exactly when they cost most. | proposed | `F-b4-07`, `F-b4-01` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-litellm` | today | enter, exit and attest_chain served in process by the three enforcement points PASS.md Part A already runs, joined by one chain context: admission by the host approval unit that parks a workflow for a person to approve, reject or return; the call point's credential and destination slots by the broker that holds the real key, picks the endpoint and drops model and destination overrides by name; and the call point's budget slot by the model gateway's scoped virtual key with a hard budget cap, which xc-budget records as terminating spend rather than merely recording it. The dispatch point is new code around the existing dispatcher. | Proposed: cannot chain a unit whose code was not built to enter the chain, so an agent runtime or a tool server we did not write stays off it; cannot fill the identity, policy and typed-error slots at all on this host, since none of those owners is running; and a chain fault and a unit fault are the same process, so a crash removes the enforcement and the work together with nothing left to refuse. | Select the implementation by configuration with no code edit between runs, replay the same corpus through both and through all three doors, and compare: assert every refusal this implementation produced is also produced by the out-of-process one, and record the calls the out-of-process one refused that this one never saw as ungated_metered_calls. Read the implementation from the refusal, not from the binding. | claimed | `F-a2-01`, `F-a3-07`, `F-a3-08`, `F-a4-07`, `F-b3-03` "Model and destination overrides dropped by name at the broker" |
| `E-swap-candidate-out-of-process-enforcement-sidecar` | second | Proposed implementation, and a proposed entity id: the knowledge base has no capability row for an enforcement chain, so no adapter or swap-candidate entity exists to name here. The same three operations served by a helper process beside the workload, or an admission step in front of it, which the unit's traffic must cross: enter is an admit call the workload never makes for itself, exit is recorded when the wrapped traffic completes or the process observing it ends, and attest_chain is unchanged because it reads records rather than call sites. | Proposed: cannot see anything that does not cross its boundary, so an entirely in-process side effect is invisible to it; adds a second process to every unit's critical path and a hop to every call it wraps; and cannot express a slot needing state only the unit holds, which has to stay on the in-process implementation. | Proposed: the axes, in the form build-adapter-pair defines, are locus_of_traversal (inside the process that issues the call versus a process the traffic must cross), processes_required_for_progress (one versus two, where the second's absence is a refusal) and reach_over_unmodified_workloads (none versus full). Select by configuration, run the same corpus through both, and compare both reports against the same declared gaps. | claimed | `F-b1-04`, `X-cross-structure-020` "Every interface ships with at least two adapters" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/xc-enforcement-chain/test.sh && python3 harness/xc-enforcement-chain/conformance.py --adapter dryrun --adapter second --min-units 100 |
| Expected | Measured by tools/measure.py at 5dd855c: exit 0; last lines:   ok   identical chain records from 2 enforcement points (db7461f6c118), differing on 2 loci \| conformance PASSED: 26/26 |
| Deliberate breakage | In harness/xc-enforcement-chain/interface.py, unbind the event door's intake path from the admission point (meter the unit and continue before the chain runs, the same edit the gate applies to a copy in its step 4), run the criterion (chain_context_missing and ungated_metered_calls become non-zero for the event door alone and the gate exits 1), then git checkout harness/xc-enforcement-chain/interface.py. |
| Expected failure | Measured by tools/measure.py at 5dd855c: exit 1; last lines:   ok   the run names the case that broke it \| passed 25, failed 11 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-08` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `xc-enforcement-chain`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The chain is a placement across several capabilities, not a capability row, so PASS.md B3 has no adapter or swap-candidate entity for it and the second implementation here carries a minted id. Should the pair get entities of its own? | 1-3-1 applied (TARGET T5): (a) mint entities for an in-process chain and an out-of-process chain, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) record today's implementation against the model-gateway adapter entity whose scoped key is the one slot that already enforces, and mark the second implementation's id as proposed in the row that states it, which is what this skill does; (c) defer the pair to a later wave, which would leave this guarantee with one implementation and nothing to prove swappability. Recommendation followed: (b). The question closes when a ceremony rebuilds the knowledge base and the two entities exist. | Keep today's row on the existing model-gateway adapter entity, since its scoped key is the one point of the chain that measurably refuses today, and keep the second implementation's entity id marked proposed in its own row. | `F-b3-03`, `F-a4-07`, `T-t5-02` |
| Does the out-of-process implementation run one instance per isolated unit, or one per host serving many units? | Measure the added latency per call and the resident cost per unit under both, over the shadow corpus, and count the refusals each can express: a per-unit instance can hold unit-scoped state a shared one cannot, and a shared one cannot be starved by one unit's traffic. | Proposed: one per isolated unit while the unit count is small, because it keeps a slot's state next to the unit it belongs to and makes a failure blast-radius of one; revisit at the scale TARGET T6.6 names, where a per-unit process per agent is the dominant cost. | `T-t6-06`, `F-b1-04` |
| At the enforce stage, must all three points and all three doors be switched on in one change, or can the call point follow the other two? | Count, during shadow, how many refusals occur only at the call point. If that set is non-empty, switching the call point last leaves the calls it alone would refuse running unchained for the length of the gap, and the report reads green throughout because the other two points pass. | All at once. A staged switch is a period in which the attestation is green and the guarantee is partial, which is precisely the state this build exists to end. | `F-a7-03`, `F-a6-04` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-enforcement-chain 2831cb4f, 2026-09-03 |
