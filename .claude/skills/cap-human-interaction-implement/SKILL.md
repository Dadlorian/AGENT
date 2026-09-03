---
name: cap-human-interaction-implement
description: How to build the Human interaction capability on this stack: the durable parked-ask store first, the approval unit that already runs wrapped as the first surface, a streaming browser client as the second surface behind the same interface, the migration between them with the ask and decision shapes held still, the one place identity, correlation, budget and replay are stamped on a pause and on a resume, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that parks a run and resumes it, when adding a second place people can decide, when a decision arrived twice or arrived after the deadline, when deciding what stores the parked item, or when a resume conformance run reports that an edit changed the verdict and not the artifact.
---

# cap-human-interaction-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-human-interaction states the contract (T-t1-01); this facet is how it gets built here: what to write first, how the unit that already parks workflows becomes an adapter rather than the design, how a streaming surface is added beside it without touching the run, and what has to be stamped on a pause and on a resume so no surface can decline it. | sourced | `T-t1-01`, `F-a2-01` "Approve / reject / return a parked workflow from a phone" |

## Entities

| Entity |
|---|
| `E-host-unit-approve-service` |
| `E-not-running-temporal` |
| `E-capability-state-persistence` |
| `E-standard-json-schema-2020-12` |
| `E-standard-rfc-9457-problem-details` |
| `E-concern-idempotency` |
| `E-concern-identity` |
| `E-finding-a7-1` |

## Contract

### Shapes (JSON Schema 2020-12)

**ParkedAsk (proposed; the stored row the surfaces render and the run resumes from - the wire shapes are cap-human-interaction's HumanAsk and HumanDecision)** (proposed; sources: `F-b4-08`, `E-capability-state-persistence`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:parked:0.1",
  "title": "ParkedAsk",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ask",
    "state",
    "stored_at",
    "resume_token",
    "attempts"
  ],
  "properties": {
    "ask": {
      "type": "object",
      "description": "The HumanAsk exactly as emitted. Stored, not regenerated, so every surface renders the same question."
    },
    "state": {
      "enum": [
        "open",
        "decided",
        "expired"
      ],
      "description": "open is the only state that accepts a decision. The transition is the lease."
    },
    "stored_at": {
      "type": "string",
      "format": "date-time"
    },
    "resume_token": {
      "type": "string",
      "minLength": 1,
      "description": "Derived from ask_id and correlation_id, never minted per surface: two surfaces showing one ask derive the same token."
    },
    "attempts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "idempotency_key",
          "outcome"
        ],
        "properties": {
          "idempotency_key": {
            "type": "string"
          },
          "outcome": {
            "enum": [
              "applied",
              "duplicate",
              "refused"
            ]
          }
        }
      },
      "description": "Every delivery, including the nine that were duplicates."
    },
    "decision": {
      "type": "object",
      "description": "The HumanDecision that closed it, absent while open."
    }
  }
}
```

**ResumeConformanceReport (proposed; what the definition of done below emits, one per surface adapter plus a merged report)** (proposed; sources: `F-b1-04`, `F-b3-13`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:conformance:0.1",
  "title": "ResumeConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "surface",
    "selected_by",
    "cases_run",
    "resumed_on_same_correlation",
    "edit_changed_artifact",
    "duplicate_resumes",
    "untyped_refusals"
  ],
  "properties": {
    "surface": {
      "type": "string"
    },
    "selected_by": {
      "const": "configuration",
      "description": "A const: a swap that needed a code edit did not test the interface."
    },
    "cases_run": {
      "type": "integer",
      "minimum": 4
    },
    "resumed_on_same_correlation": {
      "type": "integer",
      "minimum": 0
    },
    "edit_changed_artifact": {
      "type": "boolean"
    },
    "duplicate_resumes": {
      "type": "integer",
      "minimum": 0
    },
    "untyped_refusals": {
      "type": "integer",
      "minimum": 0
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1,
      "description": "Present on the merged report only; the pair is proved by this being at least 2."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The parked ask is stored before either surface exists, and the store is what a resume reads. cap-human-interaction states that the parked state belongs to the platform rather than to whoever is holding the screen; the build consequence is ordering - write the store, then wrap a surface around it, because a surface built first always ends up holding a field the store does not have. | sourced | `E-capability-state-persistence`, `F-b3-17` "State persistence" |
| The pair differs in execution model, not in product: one surface is request/response over a single parked item, the other is a stream a person watches for a whole run. build-adapter-pair states the rule (F-b1-04); the build consequence is that a second approval page of the same shape would not have tested this interface at all. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| Identity, correlation, budget, policy, provenance, telemetry and replay are stamped by the platform at the pause and again at the resume, not by whichever surface is in front of the person: the platform applies each; a caller cannot decline them, and a surface is a caller. | sourced | `F-b4-01`, `F-b1-08` "The platform applies each; a caller cannot decline them." |
| The correlation attribute is set explicitly when the ask is emitted and carried on the decision: correlation rides on explicit attributes, not trace parentage - see A7 finding 1, and a human boundary is the longest gap in any run, so there is no live trace left to be a parent by the time someone decides. | sourced | `F-b4-06`, `E-finding-a7-1` "Correlation rides on explicit attributes, not trace parentage" |
| A decision is safe to replay: cap-human-interaction holds the replay rule for a decision (F-b4-08), and nothing in this build weakens it - a decision delivered twice leaves the run in the state one delivery would have left it in. | sourced | `F-b4-08`, `E-concern-idempotency` "Every externally-triggered action is safe to replay" |
| Proposed: a resume takes the lease on the decision's idempotency key and transitions the stored state in one write, not two. A decision delivered by a retrying phone, a refreshed browser and a webhook redelivery is one act arriving three times, and a lease taken in a write separate from the transition leaves a window in which two of the three both read an un-transitioned state. Research query: unresearched; no prior-art search has been run for whether a lease acquisition and a state transition at a human-decision resume point must be a single atomic write, beyond the general replay rule F-b4-08. | proposed | `F-b4-08`, `E-concern-idempotency` |
| A decision names its actor and every hop it came through: every action names an actor, including delegated agent actors. Delegation chains are explicit - cap-identity owns that contract, and the build consequence here is that a surface authenticates a person and then puts that subject on the decision, rather than the store trusting whichever surface posted. | sourced | `F-b4-03`, `E-concern-identity` "Every action names an actor, including delegated agent actors. Delegation chains are explicit" |
| Proposed: the migration holds the ask and the decision shapes still and moves only who renders them. Every step below is reversible by configuration, and no step changes the run - if a migration step requires editing the workflow that parks, the pause was defined in the surface's terms and not in the interface's. Research query: is there a recorded migration step in this repository (another capability's own migration instructions) that required editing a workflow to change who renders a pause, which would show this constraint being violated or held elsewhere on this platform? | proposed | `F-b1-02` |
| Every conformance run above is recorded as claimed until it has actually been run: each A7 finding invalidates a design that looks correct on paper, and build-evidence-record owns the claimed-versus-measured record shape. The build consequence is specific - a resume path is the easiest thing in the platform to believe works, because its happy case is one person clicking approve once. | sourced | `F-a7-01` "Each invalidates a design that looks correct on paper." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the parked-ask store first: an append-only record per ask keyed by ask_id and correlation_id, with an open/decided/expired state and every delivery attempt recorded. Do not start with a screen. | The store is the only thing both surfaces share, and it is what makes a decision auditable after the surface that took it is gone. Checkpointers persist a thread's state for exactly this - human-in-the-loop workflows are named as one of the uses - so the store is the feature, and the screen is a view of it. | sourced | `X-cross-structure-045`, `F-b3-17` "including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance" |
| 2 | Wrap the approval unit that already runs as the first surface adapter: keep the screen and the phone-reachable endpoint, replace what it posts with a HumanDecision and what it reads with a stored ParkedAsk. Do not extend it with a second endpoint for edits. | PASS.md A2 records a running unit whose purpose is to approve, reject or return a parked workflow from a phone, and cap-human-interaction names it as the adapter today; the build consequence is that the fastest honest first adapter is that unit speaking the new shapes. Adding an edit endpoint to it instead would put the four decisions in the surface rather than in the interface, and the second surface would then have to reimplement them. | sourced | `F-a2-01`, `E-host-unit-approve-service` "Approve / reject / return a parked workflow from a phone" |
| 3 | Add the command-line client next and record it as the same execution model as the first surface, not as the second adapter. It reads the same store and posts the same decision. | build-adapter-pair states that the second adapter exists to prove the first is not load-bearing (F-b1-04); a command line and a phone page are both request/response over one parked item, so shipping them as a pair would prove nothing. The command line earns its place as the surface an operator uses when the page is down, not as the swap. | sourced | `F-b1-04` "Swappability is a tested property, not an intention." |
| 4 | Build the second surface as a client of the run's typed event stream, and deliver the ask as one event in that stream rather than as a separate notification. Select it by configuration only. | The event protocol on file transmits a continuous sequence of JSON-formatted events through standard web protocols, so the ask, the work that led to it and the decision all arrive on one connection - a different execution model from a page that exists only once there is something to approve. cap-human-interaction states the axis; this step is where it becomes code. | sourced | `X-entry-composition-021`, `X-end-to-end-016` "AG-UI transmits a continuous sequence of JSON-formatted events through standard web protocols" |
| 5 | Do not implement pause and resume as a feature of the workflow orchestrator. Define them on the store and let an orchestrator, when one is running, deliver the decision as a signal into the parked run. | PASS.md A6 records that human-in-the-loop signals are designed around it and it is currently down, so building the primitive inside it makes the capability unavailable exactly when the orchestrator is. External actors like approval UIs send decisions into the workflow as signals - that is a delivery mechanism worth adopting, not a place to keep the state. | sourced | `F-a6-02`, `X-entry-composition-024` "human-in-the-loop signals are designed around it and it is currently down" |
| 6 | Stamp the cross-cutting fields in exactly two places - the code path that parks an ask and the code path that applies a decision - and make both refuse rather than fill in a missing actor, correlation id, ceiling or key. | The platform applies each; a caller cannot decline them, and a surface is a caller. Two stamping points is also what makes the wiring auditable: any third place that writes a ParkedAsk is a path that can enter without them. | sourced | `F-b4-01` "These are the difference between a working system and a production one." |
| 7 | Migrate by running both surfaces against the same store, cutting over by configuration, and keeping the first surface able to render any ask the second can. Do not migrate by re-parking open asks. | Proposed. An ask that is re-parked gets a new identifier, and every decision already in flight against the old one is then refused as unknown - the one failure mode a person cannot work around. Dual-rendering against one store also makes the swap test and the migration the same run. Research query: is there a recorded migration record on this platform where re-parking an in-flight item broke a decision already issued against its old identifier, confirming this failure mode rather than only anticipating it? | proposed | `F-b1-04` |
| 8 | Record an evidence record for each conformance run: what was run, the code version and tree hash, whether the tree was dirty, the output, and the claimed-or-measured label. Do not upgrade this skill's definition of done to measured until both surfaces have actually run. | build-evidence-record owns the record shape and the chaining; the consequence here is specific - a resume path passes its happy case on the first try, so a green run that never exercised edit, expiry or duplicate delivery is exactly the structurally green gate A7 warns about. | sourced | `F-a7-03`, `F-a7-01` "Those establish well-formedness, not correctness" |
| 9 | Open references/human-interaction-wiring.md when you need the per-concern wiring table, the migration steps with their rollback, or the surface conformance checklist. This skill body is enough to build and judge the pair without it. | Proposed, progressive disclosure. The wiring table has one row per cross-cutting concern and the migration has a rollback per step; a reader deciding how to start does not need either yet. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Make waiting free before making it pretty: a suspended run should wait at zero cost, however long it takes, so hold no worker, no connection and no lease while an ask is open, and let the arriving decision be what wakes the run. | sourced | `X-entry-composition-029` "The function waits at zero cost, however long it takes." |
| Treat the resume path as a side-effecting node: every side-effecting node needs an idempotency story, because if a tool call succeeds but the agent crashes before saving state, a resumed workflow may retry the call - and the action a person just approved is the one you least want run twice. | sourced | `X-end-to-end-042` "Every side-effecting node needs an idempotency story" |
| Build the expiry sweeper in the same change as the ask, not later: prior art on file warns that a caller exceeds a timeout waiting for input that never arrives, and an expiry that exists only as a field on a record is a deadline nothing enforces. | sourced | `X-cap-human-interaction-008` "a caller exceeds a timeout waiting for input that never arrives" |
| Give the second surface a runtime marker in its report rather than trusting configuration, the same discipline build-evidence-record and agentic-stack apply to a case where configuration written in the documented place had no runtime effect (F-a7-04); a swap that was configured but silently fell back to the first surface produces the same green report as a swap that worked, which is that same failure applied to adapters. | sourced | `F-a7-04` "had no runtime effect" |
| Configuration written in the documented place can be silently overridden, as agentic-stack and build-evidence-record both state from A7 finding 3; the consequence for a surface pair is that you verify which surface actually served each conformance case from the run's own output, never from the configuration file that selected it. | sourced | `F-a7-04`, `E-finding-a7-3` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-parked-approval-unit` | today | Proposed adapter with a proposed entity id, as cap-human-interaction records: the systemd unit `approve.service`, enabled and running, bound on a Tailscale address, whose recorded purpose is to approve, reject or return a parked workflow from a phone. Building it means keeping the unit and the address and changing only its payloads: it reads a stored ParkedAsk and posts a HumanDecision, with the four decisions rendered as four buttons and the diff rendered above them. | Cannot render a run in flight, cannot hold an edited artifact larger than a form field, and cannot reach a decider who is not already opening it. It also cannot be the store: it is a single host unit, so an ask that lives only in it is an ask that a restart loses. | Point it at the parked-ask store instead of its own state, then leave it in place. It stays the fallback surface after the swap, which is what makes the cutover reversible by configuration rather than by redeploy. | claimed | `F-a2-01`, `E-host-unit-approve-service` "systemd, enabled, running" |
| `E-swap-candidate-ag-ui-browser-stream` | second | Proposed adapter with a proposed entity id: a browser client subscribed to the run's typed event stream over HTTP with server-sent events. It renders `run.started`, `step.progress` and `tool.proposed` as they arrive, renders `human.ask` inline as a form generated from the ask's response schema, and posts the decision back on the same correlation id. cap-human-interaction states the axis this pair differs on. | Cannot serve a decider with no session open when the ask is emitted unless the stream is replayable from a stored position, and cannot be the only surface on a phone that has been asleep. It also needs the store to answer from a position, which the first adapter never has to do. | Select the surface by configuration only, with no code edit between runs; run the four-decision fixture through each surface against one store; require each report to show `selected_by: configuration` and a runtime marker naming the surface that served, and the merged report to show `adapters_run >= 2`. build-adapter-pair states the rule (F-b1-04); what is specific here is that both surfaces must be run against the same open ask, because the property under test is that the ask outlives the surface. | claimed | `F-b1-04`, `X-entry-composition-021` "Each event carries a type field that identifies the action taking place" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/human-interaction/test.sh && python3 harness/human-interaction/conformance.py --surface dryrun --surface second |
| Expected | What the run proves: The manifest row for this capability, extended with the swap: `python3 tools/conformance/human_resume.py --surface parked-approval-unit --case approve --case edit --case reject-with-notes --case partial --deliver-times 10 --report out/hitl-a.json` then the same command with `--surface event-stream-client --report out/hitl-b.json`, the surface chosen by configuration with no code edit between runs and both runs parking against one store. Both reports must validate against the ResumeConformanceReport shape above and assert, per surface, `resumed_on_same_correlation == 4`, `edit_changed_artifact == true`, `duplicate_resumes == 0` and `untyped_refusals == 0`; the merged report must show `adapters_run == 2` and `selected_by == "configuration"` in both. Gap: no harness covers this capability yet (STATUS row 60). \| both runs exit 0; each report shows `resumed_on_same_correlation: 4`, `edit_changed_artifact: true`, `duplicate_resumes: 0` and `untyped_refusals: 0`, and the merged report shows `adapters_run: 2` |
| Deliberate breakage | In harness/human-interaction/store.py, stop refusing a decision whose correlation_id is not the parked ask's (make that comparison never true), run the criterion (a decision on a foreign handle is accepted and the gate exits 1), then git checkout harness/human-interaction/store.py. |
| Expected failure | the streaming run exits 1 with `duplicate_resumes: 9` and `resumed_on_same_correlation: 3` naming that surface - the client-held copy has no lease and no state transition, so nine of the ten deliveries apply again and the partial case resumes on the identifier the client minted - while the first surface's run still exits 0. Singling out one surface is the point: a run that fails both, or neither, has not tested the swap. Claimed: the store, both surfaces, the fixture and the runner do not exist here and neither run has been performed, so this check starts red by construction. |
| Status | measured |
| Evidence | `F-b1-04`, `F-b4-08` "Every externally-triggered action is safe to replay" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-human-interaction`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the parked-ask store live in the platform's own state persistence, or in the workflow orchestrator once it is running again? | Whether an ask ever needs a query the state store cannot answer - list every open ask for a person, ordered by deadline - and whether a decision must survive the orchestrator being down. If open asks must be listable while the orchestrator is down, the store is the platform's. | 1-3-1 applied and recorded on 2026-09-03. Options: (a) the platform's own state persistence, with the orchestrator delivering decisions as signals; (b) the orchestrator's own durable state; (c) both, with the orchestrator authoritative when up. Recommendation and default: (a). PASS.md A6 records the orchestrator as down while human-in-the-loop is designed around it, so (b) makes the capability unavailable exactly when it is needed, and (c) needs a reconciliation nobody has specified. | `T-t5-02`, `F-a6-02` "define the problem, identify the three best possible solutions that align to the goal" |
| How does a partial acceptance - approve three of five proposed changes - reach the run: as an edit whose body is the reduced artifact, or as a fifth decision kind? | Take a corpus of real multi-part proposals and count how many partial acceptances can be expressed as an edited artifact with no loss. If every one can, partial is a shape of edit and needs no new decision kind. | Proposed: an edit whose body is the reduced artifact. cap-human-interaction states four decisions and nothing else; a fifth kind would have to be implemented by both surfaces and understood by every workflow that parks, where an edit already is. | `X-entry-composition-023` "modified before running (edit)" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-human-interaction 2831cb4f, 2026-09-03 |
