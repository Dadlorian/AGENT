---
name: "compose-approval-implement"
description: "How to build the approval gate compose-approval fixes on this stack: the parked-item wire that runs today, a queued decision inbox as the second wire because it breaks the assumption that a decider is looking when the ask arrives, where the gate record and the lease are bound so both wires pass through one resume seam, how to migrate from gates that live inside an orchestrator that is not listening, where correlation, identity, budget, provenance and typed errors attach to a park and to a resume, and a definition of done whose breakage moves one binding. Load it when writing or reviewing the code that parks a run, delivers an ask or applies a decision, when a decision resumed a run twice, when a gate stayed open past its deadline because nothing swept it, when choosing what the second decision channel should be, or when a gate passes on one channel and not the other."
---

# compose-approval-implement (folded into `cap-human-interaction`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the gate compose-approval fixes into something that runs here: two decision wires behind one resume seam, a durable gate record that outlives every process, and a migration that never leaves a window in which one decision can be applied twice. | sourced | `F-a2-01`, `F-b3-16` "Approve / reject / return a parked workflow from a phone" |

## Entities

| Entity |
|---|
| `E-host-unit-approve-service` |
| `E-not-running-temporal` |
| `E-concern-idempotency` |
| `E-concern-identity` |
| `E-capability-state-persistence` |
| `E-capability-scheduling` |
| `E-capability-work-intake` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this wire pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`, `X-entry-composition-024`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:approval:pair-axes:0.1",
  "title": "ApprovalWirePairAxes",
  "description": "Proposed. The three axes the two decision wires differ on, stated as properties rather than as product names. measured stays false until the swap has been run and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "who_initiates_delivery",
        "today_value": "the decider, who opens the parked item and pulls it",
        "second_value": "the platform, which pushes the ask into a durable queue whether or not anyone is there",
        "measured": false
      },
      {
        "axis": "delivery_multiplicity",
        "today_value": "one post per decision, and a lost post is a decision that never happened",
        "second_value": "at-least-once, so the same decision is redelivered until it is acknowledged and arrives more than once by design",
        "measured": false
      },
      {
        "axis": "decider_presence_required",
        "today_value": "a live session at the moment of deciding; nothing is delivered to someone who is not looking",
        "second_value": "none; the ask sits in the queue and the decision is accepted whenever it is produced, including after the deadline",
        "measured": false
      }
    ]
  ]
}
```

**approval-conformance report (proposed; the counters the definition of done asserts on, written per wire and once across wires)** (proposed; sources: `F-a7-03`, `F-b4-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:approval:conformance-report:0.1",
  "title": "ApprovalConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A green run names what it checked and where the claim was taken, not only its exit code.",
  "required": [
    "wire",
    "gates_parked",
    "views_missing",
    "resumes_per_gate_max",
    "resumed_on_same_correlation",
    "expired_gates",
    "late_decisions_applied",
    "lease_boundary_observed"
  ],
  "properties": {
    "wire": {
      "type": "string",
      "description": "The entity id of the decision wire selected by configuration."
    },
    "gates_parked": {
      "type": "integer",
      "minimum": 0
    },
    "views_missing": {
      "type": "integer",
      "minimum": 0
    },
    "resumes_per_gate_max": {
      "type": "integer",
      "minimum": 0,
      "description": "The largest number of continuations any one gate produced across its deliveries."
    },
    "resumed_on_same_correlation": {
      "type": "integer",
      "minimum": 0
    },
    "return_reentered_named_step": {
      "type": "integer",
      "minimum": 0
    },
    "expired_gates": {
      "type": "integer",
      "minimum": 0
    },
    "late_decisions_applied": {
      "type": "integer",
      "minimum": 0
    },
    "lease_boundary_observed": {
      "type": "string",
      "description": "Read from the granted lease record, never from the binding that was configured. The value that passes is the shared resume seam; a wire name here is the fault the breakage introduces."
    },
    "sweeper_source": {
      "type": "string",
      "description": "What closed the expired gates: the scheduling occurrence, or a timer inside a process."
    },
    "wires_run": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| agentic-stack states design rule 1 (F-b1-02). Its consequence here: which wire carried a decision is configuration and audit, never control flow. delivered_over is recorded on the outcome and no workflow, no gate and no core component branches on it, or the second wire can never be run through the same fixture as the first. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| PASS.md A6 records that durable workflow orchestration and the human-in-the-loop signals were designed around a component whose server is not listening. The consequence for this build is that the gate is not defined in that component's vocabulary at all: the parked gate is a record in the state seam, the deadline is a scheduling occurrence, and the claim is a lease - three things that already have interfaces here - so nothing about a gate waits for that server to come back. | sourced | `F-a6-02`, `E-not-running-temporal` "Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down" |
| agentic-stack states that what runs is substrate (F-part-c-11). Its consequence here: the unit that already parks, shows and decides is not replaced. It becomes wire one, its verdict is mapped onto the outcome shape compose-approval fixes, and what is added in front of it is the gate record, the resume seam and the lease - not a new approval product. | sourced | `F-part-c-11`, `F-a2-01` "Part A is substrate, not scope. Do not propose replacing what runs." |
| Proposed, and the single most load-bearing binding in this build: the lease is acquired once, at the shared resume seam every wire passes through, and never inside a wire's own handler. compose-approval states the placement as a contract; what this adds is that the binding is observable - the granted lease record names the boundary it was taken at, and the conformance report reads that field rather than the configuration that set it. | proposed | `F-b4-08`, `F-a6-04` |
| Proposed: the migration never has a window in which one decision can be applied twice. The gate record and the lease are added in shadow first, recording what they would have refused while the existing unit still resumes runs on its own; only then does the resume seam become the only path, and only then is the second wire enabled. Adding the second wire before the seam is what would create the window. | proposed | `F-b3-16`, `T-t2-03` |
| Apply build-evidence-record: every statement here about how a wire behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test and whether the tree was dirty. Rewording a sentence never upgrades a label; proposed pointer, see that skill. | sourced | `F-a5-04`, `F-part-c-08` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build wire one as a thin binding over the unit that already runs: it shows one parked item and posts one decision. Map its three verdicts onto the outcome shape compose-approval fixes, add the gate id, the correlation id and the deciding subject to what it posts, and change nothing else about it. | compose-approval states that the unit PASS.md A2 records already offers approve, reject and return (F-a2-01); building the pair from what runs rather than from an intention is what makes the first wire real, and it makes the gap explicit - this wire delivers nothing to someone who is not looking at it. | sourced | `F-a2-01`, `F-part-c-11` "Approve / reject / return a parked workflow from a phone" |
| 2 | Proposed: build wire two as a queued decision inbox. The ask is pushed into a durable queue as a message, the decision comes back as an at-least-once delivery with no session behind it, and the wire acknowledges only after the resume seam has answered. | Proposed: this breaks the assumption that a decider is present when the ask arrives. Prior art on file describes exactly this shape - external actors send decisions into the workflow as signals and the workflow reacts when the signal arrives without polling from inside the workflow - and it is the wire that makes the ten-deliveries case a real condition rather than a synthetic one. | sourced | `X-entry-composition-024`, `X-entry-composition-029` "the workflow reacts when the signal arrives without polling from inside the workflow" |
| 3 | Write the gate record through cap-state-persistence, keyed by correlation id and gate id, and make the record durable at a head before any ask is emitted on any wire. | Proposed: an ask that exists on a wire before the gate exists in the store is a decision that can arrive with nothing to apply it to. Ordering the two writes this way is also what lets a wire be deleted and rebuilt between the ask and the decision without losing the run. | proposed | `F-b3-17`, `X-cross-structure-046` |
| 4 | Put one resume seam in front of every wire and bind the lease acquisition, the actor binding and the response-schema validation inside it, in that order, before any outcome is applied. Record the boundary on the granted lease record so a report can observe where the claim was taken. | compose-approval states that the resume boundary acquires its own lease (F-b4-08); at code level the risk is not that the claim is absent but that it is bound per wire, in which case the first wire looks correct and the second bypasses it. The recorded boundary is what turns that into something a run can assert on rather than something a reviewer has to read for. | sourced | `F-b4-08`, `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |
| 5 | Bind the deadline sweep to the gate record through cap-scheduling, not to a wire and not to whatever process is running the workflow, and have the sweep write the gate terminal and return the registered deadline-exceeded problem. | compose-approval's second open question records the 1-3-1 that chose this; the build-level reason is that a wire-owned sweep expires only its own asks, so a gate reachable from two wires would expire twice on one and never on the other, and a process-owned timer expires nothing at all once the process ends. | sourced | `X-cap-human-interaction-008`, `F-b3-15` "you should design explicit timeouts for human steps rather than letting approvals sit indefinitely" |
| 6 | Migrate in three stages with no gap: write gate records and take leases in shadow while the existing unit still resumes runs, recording every would-be refusal; then make the resume seam the only path for the wire that already exists; then enable the second wire. | Proposed: doing it in the other order - second wire first - is the one sequence that creates a window in which two paths can both apply the same decision, which is precisely the failure this composition exists to prevent, introduced by the work of preventing it. | proposed | `F-b3-16`, `T-t2-03` |
| 7 | Wire the cross-cutting guarantees onto the park and the resume as two distinct points: stamp the run's correlation attributes on the ask, the outcome and the resumed step; append the deciding hop to the delegation chain; resume under the ceiling that remains rather than a fresh one; record the view digest the decider saw as an attributable input; and return only registered problem types from both wires. | The guarantees are managed across the entire structure, whichever entry point was used, and a park is the point where a run is most likely to lose them, because the process that held them has gone away. Each of the five is owned elsewhere - xc-correlation for the correlation attributes, xc-identity-delegation for the deciding hop, xc-budget for the ceiling that remains, xc-provenance-chain for the view digest as an attributable input and xc-typed-errors for the registered problem types - and what this step places is where they attach: on the park and on the resume as two distinct points, so a gate that satisfies four of them and drops one still reports green on every gate assertion. | sourced | `T-t2-03`, `F-b4-01` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| 8 | Run the conformance suite in the definition of done against both wires, selected by configuration with no code edit between runs, and write an evidence record per run before labelling anything measured. What that suite swaps today is the two executors, not the two wires: harness/workflow's conformance and gate name no wire at all and flow.py takes one --wire with a single default of parked-item, so wires_run stays claimed until the second wire of step 6 exists. | build-adapter-pair states that swappability is a tested property, not an intention (F-b1-04), and build-evidence-record states what a record has to name; a pair described in a table and never run through one suite is two implementations, not a proven boundary. | sourced | `F-b1-04`, `F-a5-04` "Swappability is a tested property, not an intention." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Report the counters per wire and refuse to merge them. compose-approval draws the structurally-green consequence for a gate suite from F-a7-03; at build level the sharper version is that a merged report can show one continuation per gate while one wire produced ten and the other produced none, because the fixture never reached it. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Expect the two wires to disagree about ordering and treat the difference as the finding, not as noise. A pulled decision arrives once when a person acts; a pushed one arrives repeatedly and may arrive after the gate closed. What must not differ between them is how many times the run continued and whether a late decision was applied. | sourced | `X-xc-compensation-006`, `X-entry-composition-024` "messages will be delivered more than once, and every participant must handle duplicates gracefully" |
| Proposed: keep the gate record small and let it reference rather than contain. The view, the proposed artifact and the reviewer's edited body live where artifacts live and the gate holds digests, or a record designed to be read on every sweep inherits the size and retention policy of whatever the largest reviewed artifact happens to be. | proposed | `F-b3-17`, `F-b4-05` |
| Keep the gate on the live path. PASS.md A6 records a concern whose checks exist and sit outside the path that enforces them, and an approval suite that replays a stored fixture can pass in full while the workflow that actually runs never parks at all. | sourced | `F-a6-04` "not wired into the enforcement path" |
| Proposed: rehearse the crash between the ask and the decision on both wires, not only the duplicate. Kill everything after the ask is emitted, bring it back, and deliver the decision; a gate that only survives a tidy shutdown has tested the queue, not the record the queue is a view of. | proposed | `X-cross-structure-046`, `X-end-to-end-042` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-parked-approval-unit` | today | Proposed adapter, and a proposed entity id: PASS.md B3 has no Human interaction row, so no adapter entity exists to name here and cap-human-interaction mints the same id for the same thing. What runs is the host unit PASS.md A2 records, reachable on a private address, whose stated purpose compose-approval quotes as the source of the outcome triple plus the return. As a decision wire it serves park by rendering one item, and resume by posting one decision when a person is looking at it. | Cannot deliver an ask to a decider who is not already looking, cannot redeliver a decision that was lost in flight, and cannot accept a decision produced while nothing was connected. It renders one item rather than a run in flight, so a reviewer sees the question and not the work that produced it, and it has nowhere to put an artifact the reviewer would edit in place. | Keep the gate record, the outcome shape and the resume seam still and move only what carries the ask and the decision. The wire is selected by configuration; the identical five-case fixture runs against each and the merged report must show wires_run at least 2. | claimed | `F-a2-01`, `E-host-unit-approve-service` "Approve / reject / return a parked workflow from a phone" |
| `E-swap-candidate-queued-decision-inbox` | second | Proposed adapter, and a proposed entity id: a durable queue the platform pushes the ask into and reads decisions back from, with no session anywhere in it. Prior art on file describes the shape - external actors send decisions into the workflow as signals, and the workflow reacts when the signal arrives without polling from inside the workflow - and delivery is at-least-once, so a decision arrives more than once by construction rather than by accident. | Cannot show anyone anything: it carries a view reference, not a view, so it needs a renderer it does not own. It cannot tell a decider that a gate is about to expire, gives no ordering guarantee between two decisions produced close together, and cannot make progress when its own broker is unreachable, where the first wire needs only the item to be openable. That is the axis: pull by a present decider against push to an absent one, and one post against redelivery until acknowledged. | Proposed: the axes are who_initiates_delivery, delivery_multiplicity and decider_presence_required, recorded in the shape above. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is that the second wire is chosen for having no decider present rather than for being a different approval product, which is what makes the ten-deliveries and late-decision cases real conditions on it. | claimed | `F-b1-04`, `X-entry-composition-024` "External actors like approval UIs send decisions into the workflow as signals" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/workflow/test.sh && python3 harness/workflow/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at eaca633: exit 0; last lines: adapter=second executor_marker=queue-state-machine/0.1 steps_committed=8 steps_replayed=6 effects_for_publish=1 duplicate_effects=0 declared_gap_honoured=true checks=28/28 \| adapters_run=2 distinct_markers=2 |
| Deliberate breakage | In harness/workflow/adapters/dryrun.py, break the redelivery dedup in record_decision so a prior gate-decided record is never recognised as a duplicate: sed -i 's/for r in prior)/for r in [])/' harness/workflow/adapters/dryrun.py. Ten deliveries of the same decision then each re-apply instead of the first one landing and the rest being no-ops. Restore with git checkout -- harness/workflow/adapters/dryrun.py. |
| Expected failure | Measured by tools/measure.py at eaca633: exit 1; last lines:   FAIL the same suite passes again once the key is restored (expected 0, got 1) \| passed 18, failed 5 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-04` "the second exists to prove the first is not load-bearing" |

## Composes with

Builds on: `compose-approval`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Both wire entities are minted here. The knowledge base has no adapter or swap-candidate entity for a decision channel, because PASS.md B3 has no Human interaction row to hang one on. Where should they live? | 1-3-1 applied (TARGET T5) and recorded on 2026-09-03, the same way cap-human-interaction records the gap for its own pair. Options: (a) carry the pair here with proposed entity ids declared as proposed in the rows themselves; (b) append entities to kb/entities.jsonl, which rewrites the entity chain head every written skill pins in provenance; (c) reuse the host-unit entity as the adapter id, which would put a unit of the running host where an adapter belongs. Recommendation followed: (a). | Proposed: the pair stays on minted ids, declared as proposed in each row, and cap-human-interaction's identical row for the first wire is the precedent. A knowledge-base rebuild that adds a Human interaction row to PASS.md B3 is what replaces them. | `T-t5-02`, `F-b1-04` "define the problem, identify the three best possible solutions that align to the goal" |
| How long should the lease on a resume boundary live, given that a gate may stay open for days while a lease that outlives a crashed owner blocks the key? | The two durations are unrelated: the gate's deadline bounds how long a person has, the lease bounds how long one delivery may hold the claim. Measure the time from delivery to applied outcome per wire and set the lease above its tail, then measure how many redeliveries a normal queued decision produces inside that window. | Proposed: a lease scoped to the delivery rather than to the gate, short enough that a crashed resume clears within one redelivery interval, with the value carried per wire rather than globally. No number is proposed because none has been measured on this stack. | `F-b4-08`, `X-xc-compensation-006` "if a service does not respond within a defined period" |
| Should the second wire acknowledge a delivery it could not apply because the gate had already closed, or leave it for redelivery? | Whether a late decision is observable to the person who made it. Measure how many late deliveries occur per expired gate; if acknowledging silently makes a decider believe they decided, the acknowledgement has to carry the registered deadline-exceeded problem back rather than an empty success. | Proposed: acknowledge, and return the problem object on the acknowledgement path. Leaving it for redelivery converts one late decision into an unbounded retry against a gate that will never open. | `X-cap-human-interaction-008`, `F-b4-07` "Typed and machine-readable. Never parsed from prose" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session compose-approval 2831cb4f, 2026-09-03 |
