---
name: "xc-compensation-implement"
description: "How to make the compensation guarantee real on this stack, starting from nothing: no register exists today, so this facet proposes the first one - held by the durable-execution engine that PASS.md records as installed and not listening - and a second that keeps the register in the append-only chained log instead, breaking the assumption that a workflow engine is up at all. Load it when writing or reviewing the code that records what will undo an effect, when deciding where the declaration is bound so no operator can commit an effect around it, when planning the migration from a platform that records nothing, when an unwind reproduces on one register and not the other, or when deciding what the second register should be."
---

# xc-compensation-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the placement xc-compensation fixes into something that can run here: two compensation registers behind one declaration point, both reading the same class vocabulary, migrated in without a window in which an effect is committed with no record behind it. | sourced | `F-b3-04`, `F-a6-02` "**Durable execution**" |

## Entities

| Entity |
|---|
| `E-capability-durable-execution` |
| `E-capability-state-persistence` |
| `E-adapter-temporal` |
| `E-adapter-jsonl-hash-chain` |
| `E-not-running-temporal` |
| `E-concern-idempotency` |
| `E-seam-dispatch` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`, `F-b3-04`, `F-b3-17`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:pair-axes:0.1",
  "title": "CompensationPairAxes",
  "description": "Proposed. The three axes on which the two compensation registers differ, stated as properties rather than as product names. measured stays false until the swap has been executed and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "where_the_register_lives",
        "today_value": "the step journal of a workflow engine that owns the run's history",
        "second_value": "records appended to the platform's own chained log, beside every other fact about the run",
        "measured": false
      },
      {
        "axis": "what_must_be_up_to_unwind",
        "today_value": "the engine's server, which holds the history the reverse walk is driven from",
        "second_value": "nothing beyond the log itself: any process can fold it at a pinned head and drive the walk",
        "measured": false
      },
      {
        "axis": "what_drives_the_reverse_walk",
        "today_value": "the engine replaying its own history back into the code that declared the steps",
        "second_value": "a reader folding an ordered log, with no code replayed and no determinism required of the forward steps",
        "measured": false
      }
    ]
  ]
}
```

**compensation-conformance report (proposed; the fields the definition of done asserts on, written per register and once across registers)** (proposed; sources: `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:compensation:conformance-report:0.1",
  "title": "CompensationConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A green run names what it actually checked rather than only its exit code, and names the register it observed rather than the one it selected.",
  "required": [
    "register",
    "effects_checked",
    "undeclared_class_admitted",
    "records_after_effect",
    "irreversible_without_mandate",
    "runs_killed",
    "replayed",
    "compensated",
    "unwind_failed",
    "ways_in_covered",
    "register_observed"
  ],
  "properties": {
    "register": {
      "type": "string",
      "description": "The entity id of the compensation register selected by configuration."
    },
    "effects_checked": {
      "type": "integer",
      "minimum": 0
    },
    "undeclared_class_admitted": {
      "type": "integer",
      "minimum": 0
    },
    "records_after_effect": {
      "type": "integer",
      "minimum": 0,
      "description": "Compensation records whose declaration head is not strictly earlier than the effect's. The ordering assertion this build owns."
    },
    "irreversible_without_mandate": {
      "type": "integer",
      "minimum": 0
    },
    "runs_killed": {
      "type": "integer",
      "minimum": 0
    },
    "replayed": {
      "type": "integer",
      "minimum": 0
    },
    "compensated": {
      "type": "integer",
      "minimum": 0
    },
    "unwind_failed": {
      "type": "integer",
      "minimum": 0
    },
    "unwinds_resumed": {
      "type": "integer",
      "minimum": 0,
      "description": "Unwinds themselves interrupted and continued without re-running an already-compensated record."
    },
    "ways_in_covered": {
      "type": "integer",
      "minimum": 0
    },
    "register_observed": {
      "type": "string",
      "description": "Read from the compensation record that came back, never from the binding that selected the register."
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
| Proposed: the two registers differ on three of build-adapter-pair's axes - where_the_register_lives, what_must_be_up_to_unwind and what_drives_the_reverse_walk - recorded in the shape above. A second workflow engine of the same shape would agree with the first on all three, so swapping to it would test a vendor and not the guarantee. | proposed | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| agentic-stack states design rule 1 (F-b1-02). Its consequence here: which register recorded a compensation is configuration, and no core code, no workflow and no caller branches on it. The register appears in the conformance report, never in a field a caller can read and route on. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| Nothing compensates today. The recorded adapter for durable execution has its data directory present and nothing listening, and no other component records what would undo an effect, so this facet builds the first register rather than replacing one - which is agentic-stack's substrate rule (F-part-c-11) applied to an empty column. | sourced | `F-a6-02`, `F-part-c-11`, `E-not-running-temporal` "Data directory present; server not listening" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the first register behind the durable-execution interface: declare_effect writes a journalled entry before the step that commits the effect, seal_effect writes a second entry carrying the response reference, and unwind is a reverse walk the engine itself drives over its own history. | cap-durable-execution already owns step, checkpoint and resume point, and a compensation record is a checkpoint with an inverse attached, so the first register costs an interface binding rather than a new subsystem. It also makes the gap explicit: the engine that would drive that walk is recorded as down, so this register is proposed and not observed. | sourced | `F-b3-04`, `F-a6-02` "Durable workflow orchestration and human-in-the-loop signals are designed around it" |
| 2 | Proposed: build the second register as compensation records appended to the platform's own chained log through the state seam, with the reverse walk being a fold over that log at a pinned head. | Proposed: this breaks the assumption that a workflow engine is running. Records stop needing a server to be readable, an unwind can be driven by any process that can read the log, and the ordering assertion becomes a comparison of two heads in one sequence rather than a claim about an engine's internal history. | proposed | `F-b3-17`, `F-b1-04` "object store · relational · event log" |
| 3 | Bind declare_effect into the one call path that commits a side effect - the dispatch and step boundaries - and make an outbound call that did not cross that binding a conformance failure rather than an unrecorded effect. | xc-compensation states that the guarantee is applied at those boundaries; at code level the only way a caller can decline it is to reach a destination by a path that never asked. A binding per operator is declinable by adding an operator, and the count of effects that bypassed the binding is the number that says whether it is. | sourced | `F-b5-02`, `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| 4 | Publish the class vocabulary and the record shape as one versioned resource read by both registers and by the document validator, rather than as constants inside either register. | xc-compensation states that the class is declared in the document (F-b2-02); the declaration is refused by validation at declare time and re-read by the unwind days later, possibly on the other register, and one resource is what keeps those three readings the same. Versioning it is what lets a fourth class be added without silently reclassifying records already written under three. | sourced | `F-b2-02` "declared intent, definition of done, steps" |
| 5 | Migrate in three stages with no gap: declare in shadow while nothing is gated and count the effect-committing steps that carry no class; then refuse those documents; then turn unwind on at the dispatch boundary and afterwards at the step boundary where sub-units commit their own effects. | agentic-stack states the substrate rule (F-part-c-11). Here it means the shadow stage is the only one in which a disagreement about which steps commit effects is cheap, and it produces the inventory that says how much of the existing workflow corpus is unclassified. Turning unwind on everywhere at once would put an untested reverse walk in front of every failure the platform has. | sourced | `F-part-c-11`, `T-t2-03` "Part A is substrate, not scope. Do not propose replacing what runs." |
| 6 | Wire the cross-cutting attachments on both registers: stamp run and correlation identifiers as explicit attributes on every declare, seal and unwind event; carry the entering actor and its delegation chain onto every record; draw a compensating action's spend from the run's own ceiling; and return the registered problem types rather than an engine's native status. | agentic-stack states that correlation must ride on an explicit attribute set at dispatch (F-a7-02) because parentage did not survive the agent boundary, and an unwind whose run cannot be identified cannot be attributed to the effects it was reversing. An unwind funded outside the ceiling is also the one path by which a terminated unit keeps spending. | sourced | `F-a7-02`, `F-b4-03`, `F-b4-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Read the register from the compensation record that actually came back and put that value in the conformance report, never the binding that selected it. | agentic-stack and build-evidence-record state the silently-discarded-configuration finding (F-a7-04): values written in the documented place validated, reviewed correctly and had no runtime effect. A compensation believed to be recorded because a register was configured is that same failure with an unreversed effect behind it. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: kill the run inside the effect, not between steps. A harness that only stops runs at step boundaries never produces a committed effect whose record was written late, which is the exact fault the ordering assertion exists to catch and the one this facet's breakage injects. | proposed | `X-end-to-end-042` "if a tool call succeeds but the agent crashes before saving state" |
| Expect the two registers to disagree about ordering under concurrency and treat the difference as the finding rather than as noise; build-adapter-pair states why the pair exists at all (F-b1-04). An engine-held journal serialises entries per run while an appended log serialises them per partition, so the interleaving of two sub-units' records may differ. What must not differ is which records were compensated and which were left unwound. | sourced | `F-b1-04`, `F-b3-17` "Swappability is a tested property, not an intention." |
| Report the counts per register. One corpus replayed through two registers can leave one of them with no run killed inside an effect and still exit green - xc-compensation draws that green-gate consequence for a compensation corpus (F-a7-03), and this is its code-level form. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: keep the compensating action's input a reference resolved at unwind time, not a copy of the forward step's output taken at declare time. A copy taken before the effect ran cannot name the identifier the effect returned, which is usually the only thing the inverse needs. | proposed | `X-xc-compensation-002` "the logical inverse of the one it undoes" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-temporal` | today | Nothing compensates today: no component of this platform records what would undo an effect, and the adapter PASS.md B3 names for durable execution has its data directory present with nothing listening, so the register described here is the first one proposed rather than something observed. Built out, it serves declare_effect as a journalled entry written before the effect's own activity, seal_effect as a second entry carrying the response reference, unwind as a reverse walk the engine drives over its own history, and unwind_plan as a read of that history before the run continues. | Proposed: as it stands it records nothing, because its server is not up; the durable workflow orchestration built around it is currently down. Built out, it still cannot record or unwind while that server is unreachable, cannot cover an effect committed by a unit the engine did not start, and cannot let a reverse walk be driven by a process that does not speak to it. | Select the register by configuration only, with no code edit between runs, and replay the identical corpus of effects and killed runs through both from the same published class vocabulary. xc-compensation owns the placement this pair realises; this row records only the roles PASS.md B3 fixes and the axes the pair differs on. | claimed | `F-b3-04`, `F-a6-02` "it is currently down" |
| `E-adapter-jsonl-hash-chain` | second | The same four operations served with no engine at all: declare_effect appends a compensation record to the platform's append-only chained log conditional on the expected head, seal_effect appends a second record referencing it, unwind is a fold of that log at a pinned head walked in reverse, and unwind_plan is the same fold read forward. This entity is recorded against PASS.md B3's state-persistence row rather than a compensation row, because B3 has no compensation row for either register to belong to, as the open question below records. | Proposed: cannot drive its own retries or timers, so a compensating action that must be reattempted needs a driver above the log; cannot give a total order across runs, only within a partition; and cannot replay code, so it can never reconstruct an in-memory state a forward step held and never wrote down. | Proposed: the axes that differ are where_the_register_lives (an engine-held journal versus the platform's own chained log), what_must_be_up_to_unwind (that engine's server versus nothing beyond the log) and what_drives_the_reverse_walk (history replayed into the declaring code versus a fold read by any process). Run the identical suite against each and require the merged report to show adapters_run at least 2. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is the axes, not the rule. | claimed | `F-b3-17`, `F-b1-04` "JSONL + hash chain" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/xc-compensation/test.sh && python3 harness/xc-compensation/conformance.py --register dryrun && python3 harness/xc-compensation/conformance.py --register second |
| Expected | Measured by tools/measure.py at 203ae35: exit 0; last lines:   register=second effects_checked=64 undeclared_class_admitted=0 records_after_effect=0 irreversible_without_mandate=0 runs_killed=12 replayed=28 compensated=36 unwind_failed=0 unwinds_resumed=1 ways_in_covered=4 register_observed=chained-log-fold/0.1 \| conformance PASSED: 25/25 cases, 1 register(s), adapters_run=2 |
| Deliberate breakage | On the second register only (harness/xc-compensation/adapters/second.py), apply to the file itself the edit the gate applies to its copy in step 3 (harness/xc-compensation/test.sh:82-103): drop the declare append in _declare (second.py:76-79) so nothing is durable before the effect, and write the record in seal_effect on the same append as the effect (second.py:82), leaving the class vocabulary, the mandate check and the first register untouched. Restore with git checkout -- harness/xc-compensation/adapters/second.py. Note that the gate's step 3 then finds its own anchor block already edited and reports `AssertionError: anchor block not found in _declare`, which is the breakage showing up a second time rather than a failure to apply it. |
| Expected failure | Measured by tools/measure.py at 203ae35: exit 1; last lines:   File "<stdin>", line 11, in <module> \| AssertionError: anchor block not found in _declare; second.py changed shape |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b3-17` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `xc-compensation`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| PASS.md B3 has no compensation row, so both registers here are entities recorded against other capabilities' rows - durable execution and state persistence. Should compensation have a row and entities of its own? | 1-3-1 applied (TARGET T5), the way xc-idempotency-lease-implement records its own entity gap: (a) mint entity ids for two compensation registers, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) reuse the recorded entities of the two rows the registers actually sit in and say in each row which row it belongs to, which is what this skill does; (c) leave the pair unnamed, which would leave the guarantee with no named way to run at all. Recommendation followed: (b). The question closes when a ceremony rebuilds the knowledge base with a compensation row. | Proposed: keep the pair on the recorded entities of the durable-execution and state-persistence rows, and say in each adapter row which row its entity belongs to, so a reader is not told a compensation capability exists in PASS.md when it does not. | `T-t5-02`, `F-b3-04` "use 1-3-1: define the problem" |
| Who drives a compensating action's retries and timeouts on the second register, which has no timer of its own? | Measure, over the killed-run corpus, how many compensating actions fail on first attempt and how many of those succeed on a second within their timeout. If the count is near zero the unwinder can attempt once and report; if it is not, the second register needs a driver above the log and that driver becomes part of the swap rather than of the register. | Proposed: the unwinder retries within the compensating action's declared timeout and reports unwind-failed after it, so the retry policy lives with the unwind and both registers behave identically. xc-compensation states the timeout rule (X-xc-compensation-006). No number is proposed here because none has been measured on this stack. | `X-xc-compensation-006` "Every step in a saga should have a timeout" |
| Does the ordering assertion survive when the two registers disagree about what a head means - an engine's journal position against a chained log's record digest? | build-evidence-record states the chained-store property the second register rests on (F-a5-03). Compare, for the same corpus, whether the pair of positions the first register reports can be totally ordered against the pair the second reports. If they cannot, the assertion has to be phrased over a per-register ordering relation rather than over a shared head value. | Proposed: assert the ordering per register using that register's own position type, and require only that the relation be a strict one; the conformance report carries both positions so a reader can see which register produced them. | `F-a5-03` "a manual edit between runs is detectable" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-compensation 2831cb4f, 2026-09-03 |
