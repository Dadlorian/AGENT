---
name: "cap-human-interaction"
description: "Human interaction contract and build, approval gates included: a person enters a run, watches it as a typed event stream, and steers it by approving, editing, rejecting or answering on the same correlation id. Load it when a run must stop and ask someone, when designing review or approval steps, or when a parked item has no deadline."
---

# cap-human-interaction

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for a run that has to stop and ask a person something: what the pause emits, what a decision may carry back, and on what identifier the run resumes - so that a human is a first-class way into a running system rather than a screen bolted onto one workflow. | sourced | `T-t1-01`, `X-entry-composition-020`, `X-end-to-end-017` "A human must be able to enter the system." |

## Entities

| Entity |
|---|
| `E-standard-a2a-messaging` |
| `E-standard-model-context-protocol` |
| `E-standard-json-schema-2020-12` |
| `E-standard-rfc-9457-problem-details` |
| `E-capability-work-intake` |
| `E-host-unit-approve-service` |
| `E-not-running-temporal` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-ag-ui` | unverified | unverified | https://docs.ag-ui.com/introduction | `X-cap-human-interaction-001`, `X-entry-composition-020`, `X-entry-composition-021` |
| `E-standard-a2a-messaging` | unverified | unverified | https://a2a-protocol.org/v0.3.0/specification/ | `F-b3-08`, `X-end-to-end-014`, `X-entry-composition-014` |
| `E-standard-model-context-protocol` | unverified | unverified | - | `F-b3-06`, `X-entry-composition-016`, `X-cap-human-interaction-006` |

- `E-standard-ag-ui` version note: proposed entity id and version unverified: PASS.md B3 has no Human interaction row, so kb/entities.jsonl carries no entity for this standard and none may be added without rewriting the entity chain every written skill pins; the manifest records the AG-UI Agent-User Interaction Protocol with version unverified, and all three records on file for it are search-only, so no version string is asserted here
- `E-standard-a2a-messaging` version note: the manifest records the A2A input-required task state at v0.3.0; the records on file are search-only and the specification text was not fetched from this environment, so no version string is asserted here
- `E-standard-model-context-protocol` version note: the manifest records MCP elicitation/create at revision 2025-06-18; both records on file are search-only and neither is the specification itself, so no revision string is asserted here

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| ask (call name is ours; elicitation mid-session with a message and a JSON schema is the sourced mechanism) | a proposed action with its diff and its irreversibility class, a prompt written for a person, a JSON Schema for the response the run will accept, the correlation id of the run, and a deadline | a parked interaction record held by the platform, plus an ask event on the run's typed stream; the run is now suspended and holds no open connection to anyone (proposed) | sourced | `X-entry-composition-016`, `X-end-to-end-063` "servers can now ask users for input mid-session by sending an elicitation/create request with a message and a JSON schema" |
| watch (call name is ours; the continuous typed event stream is the sourced mechanism) | a correlation id and an optional position in the stream | an ordered sequence of typed events for that run - what it is doing, what it is about to do, and what it is waiting for - readable by a person who has not been asked for anything yet (proposed) | sourced | `X-entry-composition-021`, `X-end-to-end-016` "AG-UI transmits a continuous sequence of JSON-formatted events through standard web protocols like HTTP, SSE, or WebSockets. Each event carries a type field that identifies the action taking place" |
| decide (call name is ours; the four decisions and the resume are the sourced ones) | the same correlation id, one of approve, edit, reject or respond, an optional edited artifact or notes valid against the ask's response schema, the deciding actor, and an idempotency key | a resume acknowledgement; on edit, the artifact the run continues with is the reviewer's, not the one that was proposed (proposed) | sourced | `X-entry-composition-023`, `X-end-to-end-018` "the action can be approved as-is (approve), modified before running (edit), rejected with feedback (reject), or responded to directly (respond)" |
| expire (call name is ours; the timeout-rather-than-wait-forever rule is the sourced one) | a parked interaction whose deadline has passed | a typed problem on the run and a terminal state for the ask; nothing resumes afterwards on that ask, and a decision arriving late is refused rather than applied (proposed) | sourced | `X-cap-human-interaction-008`, `F-b3-13` "you should design explicit timeouts for human steps rather than letting approvals sit indefinitely" |

### Shapes (JSON Schema 2020-12)

**HumanAsk (proposed summary shape; the full schema, the decision schema and the event-type table are in references/human-interaction-shapes.md)** (sourced; sources: `X-entry-composition-016`, `X-entry-composition-023`, `X-cap-human-interaction-008`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:ask:0.1",
  "title": "HumanAsk",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ask_id",
    "correlation_id",
    "prompt",
    "response_schema",
    "proposed",
    "deadline_at"
  ],
  "properties": {
    "ask_id": {
      "type": "string",
      "minLength": 1
    },
    "correlation_id": {
      "type": "string",
      "minLength": 1,
      "description": "The run's own correlation id. A decision comes back on this, not on a handle the surface minted."
    },
    "prompt": {
      "type": "string",
      "minLength": 1,
      "description": "Written for a person. Never carries the criterion the result will be judged against."
    },
    "response_schema": {
      "type": "object",
      "description": "A JSON Schema 2020-12 document. The platform validates a decision's body against it before the run resumes."
    },
    "proposed": {
      "type": "object",
      "required": [
        "action",
        "diff",
        "irreversibility"
      ],
      "description": "What the run is about to do, what it would change, and how hard it is to undo.",
      "properties": {
        "action": {
          "type": "string"
        },
        "diff": {
          "type": "string"
        },
        "irreversibility": {
          "enum": [
            "reversible",
            "compensatable",
            "irreversible"
          ]
        }
      }
    },
    "deadline_at": {
      "type": "string",
      "format": "date-time",
      "description": "Required. An ask with no deadline is a run that waits forever."
    },
    "allowed_decisions": {
      "type": "array",
      "items": {
        "enum": [
          "approve",
          "edit",
          "reject",
          "respond"
        ]
      },
      "default": [
        "approve",
        "edit",
        "reject",
        "respond"
      ]
    }
  }
}
```

**HumanDecision (proposed summary shape; the full schema is in references/human-interaction-shapes.md)** (sourced; sources: `X-entry-composition-023`, `F-b4-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:decision:0.1",
  "title": "HumanDecision",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ask_id",
    "correlation_id",
    "decision",
    "actor",
    "idempotency_key"
  ],
  "properties": {
    "ask_id": {
      "type": "string",
      "minLength": 1
    },
    "correlation_id": {
      "type": "string",
      "minLength": 1
    },
    "decision": {
      "enum": [
        "approve",
        "edit",
        "reject",
        "respond"
      ]
    },
    "actor": {
      "type": "string",
      "pattern": "^(user|agent|service|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "Who decided. A decision is an action and names an actor like any other."
    },
    "body": {
      "type": "object",
      "description": "Required for edit and respond, valid against the ask's response_schema. On edit this is the artifact the run continues with; on reject it carries the notes."
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 8,
      "description": "The same decision delivered ten times resumes the run once."
    }
  }
}
```

**The failure shape (proposed): a decision that arrives after its ask closed [caller's view, folded from cap-human-interaction-use]** (proposed; sources: `F-b3-13`, `X-cap-human-interaction-008`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:example:human-ask-expired",
  "title": "The ask is no longer open",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Media type application/problem+json. The ask was closed by its own deadline before any decision arrived, and the run terminated at that point with the registered `deadline-exceeded`; a decision presented afterwards is refused rather than applied, so a new run is the remedy and this problem is not retryable. `urn:agentic:problem:human-ask-expired` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `deadline-exceeded` with the ask id in detail, as the open question below records.",
  "examples": [
    {
      "type": "urn:agentic:problem:human-ask-expired",
      "title": "The ask is no longer open",
      "status": 409,
      "detail": "ask-deploy-0001 closed at 2026-09-03T18:00:00Z after 8h open and the run terminated with deadline-exceeded; the decision presented at 2026-09-03T18:04:11Z was not applied.",
      "retryable": false,
      "correlation_id": "corr-human-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The pause is a state of the run, not a call the client makes: an agent can pause mid-execution and ask for approval, and the point of doing it this way is that it allows the agent to either continue or backtrack without the session ending. | sourced | `X-cap-human-interaction-003`, `X-end-to-end-020` "An agent can pause mid-execution and ask for approval" |
| A decision resumes the same run, not a new one: the client continues the interaction by sending a new message with the same taskId and contextId, so the identifier a person answers on is the identifier the run already had. | sourced | `X-end-to-end-014`, `X-entry-composition-014` "the client continues the interaction by sending a new message with the same taskId and contextId" |
| The ask is typed, not prose: servers can now ask users for input mid-session by sending an elicitation/create request with a message and a JSON schema, which is what makes a response machine-checkable before the run continues. | sourced | `X-entry-composition-016`, `X-cap-human-interaction-006` "servers can now ask users for input mid-session by sending an elicitation/create request with a message and a JSON schema" |
| Four decisions, not two: the action can be approved as-is (approve), modified before running (edit), rejected with feedback (reject), or responded to directly (respond). This is the one enumeration of decisions in this skill; every other row points at it rather than restating a shorter list. | sourced | `X-entry-composition-023`, `X-end-to-end-018` "approved as-is (approve), modified before running (edit), rejected with feedback (reject), or responded to directly (respond)" |
| An edit changes the artifact, not only the verdict: the agent proposes and the human publishes, with the agent's output existing in a "draft" state that the user can review, edit, and then promote to live. A resume that records an edit and then continues with the originally proposed artifact has recorded a preference, not applied a decision. | sourced | `X-end-to-end-019`, `X-end-to-end-018` "the agent proposes and the human publishes" |
| The parked state belongs to the platform, not to whoever is holding the screen: the interrupt sends the value to whoever holds the execution handle (a CLI prompt, web UI, or API consumer), and the graph state is checkpointed automatically, so the surface can crash, reload or be replaced between the ask and the decision. | sourced | `X-entry-composition-022`, `X-cross-structure-045` "the graph state is checkpointed automatically" |
| Every ask has a deadline: you should design explicit timeouts for human steps rather than letting approvals sit indefinitely, and an expiry is a typed problem on the run rather than a run that is quietly still parked. | sourced | `X-cap-human-interaction-008`, `F-b3-13` "you should design explicit timeouts for human steps rather than letting approvals sit indefinitely" |
| Watching is part of the interface, not a separate product: AG-UI transmits a continuous sequence of JSON-formatted events through standard web protocols like HTTP, SSE, or WebSockets. Each event carries a type field that identifies the action taking place, so a person can follow a run they have not been asked anything about. | sourced | `X-entry-composition-021`, `X-end-to-end-016` "AG-UI transmits a continuous sequence of JSON-formatted events through standard web protocols like HTTP, SSE, or WebSockets. Each event carries a type field that identifies the action taking place" |
| And the reason this interface is drawn at all (proposed): PASS.md A6 records that durable workflow orchestration and human-in-the-loop signals are designed around today's adapter and it is currently down, so the pause and resume primitives are defined here as capability operations and an orchestrator that provides them is an adapter underneath, never the definition. | sourced | `F-a6-02`, `E-not-running-temporal`, `F-b1-02` "Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down" |
| All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach this capability the same way, and enhancing one aspect of it leaves the rest untouched: change the surface people decide on, tighten a response schema, or add a deadline sweeper, and no workflow that parks is edited - the ask and the decision are the only things any of them named. cap-identity states the same record (T-t1-01) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion never travels in a HumanAsk: an agent sees its outcome, never the criterion it is judged against. agentic-stack states design rule 6 (F-b1-07); what this interface forbids (proposed) is putting the grading rule into prompt, response_schema or proposed.diff, because everything in an ask is visible to the graded unit that will read the decision back. A reviewer may be shown the criterion by the Judge's own surface; the parked item is not that surface. | sourced | `F-b1-07` "sees its outcome, never the criterion" |
| Proposed: no surface handle escapes the adapter. A session token, a chat thread id, a browser stream cursor, a phone push receipt - none appear on the ask or the decision; they are mapped onto ask_id, correlation_id and the idempotency key or they are dropped, so the run cannot be resumed only by whoever holds a particular screen. Research query: does the A2A or AG-UI correlation-preservation guidance (X-entry-composition-015) name surface handles as explicitly out of scope, or is that exclusion this repo's own extension of the products-only rule? | proposed | `F-part-c-09`, `X-entry-composition-015` |
| Proposed: the interface exposes no way to resume without a decision. There is no force-continue, no skip and no admin override that leaves the ask open, because each of those is an unlogged approval by another name and the parked item is the only place the deciding actor is recorded. Research query: has an admin-override path ever been attempted against this interface and been refused, or is 'unlogged approval by another name' argued from the loop-cap and irreversibility-gate literature (X-end-to-end-063) rather than observed here? | proposed | `X-end-to-end-063` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Model the stop as a parked state of the run that emits an ask, and let the run hold no open connection while it waits. Do not model it as a synchronous call from the run into a person's screen. | An agent can pause mid-execution and ask for approval, and the value of doing it that way is that the run can continue or backtrack without the session ending; a synchronous call ties the run's survival to a screen someone may close. | sourced | `X-cap-human-interaction-003`, `X-entry-composition-022` "An agent can pause mid-execution and ask for approval" |
| 2 | Put a prompt, a response JSON Schema, the run's correlation id, the proposed action with its diff and irreversibility class, a named view that renders what is being decided, and a deadline on every ask. Refuse to park an ask that is missing any of them. | The reason each field is there: the schema makes the answer checkable, the correlation id is what the decision comes back on, the diff and the irreversibility class are what a reviewer needs to judge an action before it happens, and the deadline is what stops a run waiting forever - design explicit timeouts for human steps rather than letting approvals sit indefinitely. An ask completed later has a window in which a run is parked with nobody accountable for it. The view is required for the same reason (proposed), following the reference example in docs/reference/composable-plan.md: a gate whose view is missing is not decidable, and a reviewer shown raw output is being asked to grade the work rather than to decide it. | sourced | `X-entry-composition-016`, `X-end-to-end-063`, `X-cap-human-interaction-008`, `REF-10-05`, `REF-3-4-03` "you should design explicit timeouts for human steps rather than letting approvals sit indefinitely" |
| 3 | Accept exactly the four decisions named in the invariants above and make edit rewrite the artifact the run continues with, then carry that artifact forward as the run's own. Do not ship approve and reject alone and leave edit to a later re-run. | Optional edit-in-place beats approve-then-fix - a reviewer who can only reject has to explain the fix in prose and wait for a second run, and the second run starts from the same proposal the first one made. | sourced | `X-end-to-end-018`, `X-entry-composition-023` "Optional edit-in-place beats approve-then-fix." |
| 4 | Checkpoint the parked interaction on the platform side and hand the surface only the correlation id and the ask. Never let the client hold the state the run needs to continue. | The graph state is checkpointed automatically in the prior art on file, which is what lets the surface crash, reload or be swapped between the ask and the decision; a client that holds the state makes every surface a single point of failure for every run parked on it. | sourced | `X-entry-composition-022`, `X-cross-structure-045` "the graph state is checkpointed automatically" |
| 5 | Validate a decision's body against the ask's response_schema with the platform's one validator before the run resumes, and reject a body that does not conform instead of letting the run interpret it. | cap-document-validation owns the validation contract and the dialect (F-b3-09); the consequence here is that a human decision is the one input to a run that was typed by a person under time pressure, so it is exactly the input that must not be parsed leniently by whatever step reads it next. | sourced | `F-b3-09`, `X-cap-human-interaction-006` "The server sends a JSON Schema describing what it needs, the client renders an appropriate form or prompt, the user responds, and execution resumes." |
| 6 | Make resume idempotent on the decision's key: the same decision delivered many times resumes the run once, and a decision arriving after the deadline is refused as a typed problem rather than applied. | Every externally-triggered action is safe to replay, and a decision is the most externally triggered thing in the platform - it arrives from a phone, a browser or a retrying webhook, and a resume applied twice runs an irreversible action twice. cap-idempotency owns the claim that makes a replay safe (F-b4-08); the key here is the decision's, not the request's. | sourced | `F-b4-08`, `X-end-to-end-042` "Every externally-triggered action is safe to replay" |
| 7 | Emit the run as an ordered typed event stream that a person can watch without having been asked anything, and give every event a type field and the run's correlation id. | Events reflecting everything that happens during a live agent session, from token-level message updates to tool invocations and UI state patches, are what makes a long run reviewable at all; an interface that only speaks when it needs an answer gives a reviewer no basis for the answer. | sourced | `X-end-to-end-016`, `X-entry-composition-021` "with events reflecting everything that happens during a live agent session, from token-level message updates to tool invocations and UI state patches" |
| 8 | Return every refusal - a body that fails the response schema, a decision on an expired or unknown ask, a decider the policy does not allow - as a typed problem from the platform's registry, never as a status code alone or a message only the screen shows. | cap-errors owns the failure shape and the closed registry (F-b3-13); the consequence here is that the caller is a person mid-decision, so a refusal that does not name what to change turns an approval queue into a support conversation. | sourced | `F-b3-13`, `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 9 | Write the ask on the step that is about to do something hard to undo: prompt, response schema, the proposed action with its diff and irreversibility class, and a deadline. Then return; the platform suspends the run. | This skill states this as a best practice from the prior art on file - approval gates on irreversible actions are the typical defenses - so the gate belongs where something becomes hard to undo rather than at a fixed step number. What is yours as a caller is only the four fields; storing, notifying, timing out and resuming are the platform's. | sourced | `X-end-to-end-063` "approval gates on irreversible actions are the typical defenses" |
| 10 | Open references/human-interaction-shapes.md when you need the full ask and decision schemas, the event-type table or the four worked decision instances. This skill body is enough to judge a pause-and-resume implementation without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The full schemas and the event table are long material, and a reader deciding whether a run should stop and ask does not need them yet. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Ask about the action, not about the run: hard caps on autonomous loops, plan-validation checkpoints, and approval gates on irreversible actions are the typical defenses, so put the gate where something becomes hard to undo rather than at a fixed step number. | sourced | `X-end-to-end-063` "approval gates on irreversible actions are the typical defenses" |
| Declare which actions need a person up front rather than deciding at the moment of the call: prior art on file marks tools requiring approval during registration, so the set of gated actions is readable before a run starts instead of discovered while one is parked. | sourced | `X-entry-composition-054` "Tools requiring approval can be marked during registration" |
| Keep the correlation id the same object on both sides of the human boundary: correlation IDs should be preserved at every boundary, and a surface that mints its own thread identity is a surface whose decisions cannot be joined back to the run they steered. | sourced | `X-entry-composition-015` "Correlation IDs should be preserved at every boundary" |
| Let the decision arrive as an event the run reacts to: external actors like approval UIs send decisions into the workflow as signals, and the workflow reacts when the signal arrives without polling from inside the workflow, which is also what keeps a parked run costing nothing while it waits. | sourced | `X-entry-composition-024`, `X-entry-composition-029` "External actors like approval UIs send decisions into the workflow as signals, and the workflow reacts when the signal arrives without polling from inside the workflow." |
| Proposed: give a reviewer the diff before the prose. The prompt says what is being asked; proposed.diff says what will change, and a reviewer who has to reconstruct the change from a paragraph approves the paragraph rather than the action. Research query: does the draft-then-promote pattern (X-end-to-end-019) itself specify diff-before-prose ordering, or is that this repo's own extension of a related but distinct interaction mode? | proposed | `X-end-to-end-019` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-parked-approval-unit` | today | Proposed adapter, and a proposed entity id: PASS.md B3 has no Human interaction row, so no adapter entity exists for this capability. What runs is the host unit recorded in PASS.md A2, a systemd unit bound on a Tailscale address whose purpose is to Approve / reject / return a parked workflow from a phone, plus a command-line client over the same typed event stream. Both are request/response: the decider opens a page or runs a command, sees one parked item, and posts one decision. | Cannot show a run in flight - it appears only once there is something to approve, so a reviewer sees the question and not the work that produced it. It cannot carry an edit larger than a form field, has nowhere to render a diff, and cannot deliver an ask to someone who is not already looking; and because it returns a verdict rather than an artifact, edit and respond degrade into approve-with-a-comment. | Keep the ask and the decision shapes still and move only who renders them. cap-human-interaction-implement owns the migration steps and the wiring; this row records what runs today and the axis the pair differs on. | claimed | `F-a2-01`, `E-host-unit-approve-service` "Approve / reject / return a parked workflow from a phone" |
| `E-swap-candidate-ag-ui-browser-stream` | second | Proposed adapter, and a proposed entity id: a browser client speaking the AG-UI event protocol, which transmits a continuous sequence of JSON-formatted events through standard web protocols like HTTP, SSE, or WebSockets. Each event carries a type field that identifies the action taking place, so the same parked ask arrives as one event in a stream the person was already watching, and the decision goes back on the same correlation id. | Cannot work with a decider who is not connected when the ask is emitted unless the stream is replayable from a position, and cannot be the only path on a phone with no session open. That is the axis: the first adapter is request/response over a single parked item, the second is a stream a person watches for the whole run, so an ask shaped around either one's liveness fails on the other - which is why the ask is a durable record and the stream is a view of it. | Select the surface adapter by configuration only, with no code edit between runs, and run the identical four-decision resume fixture through each; the merged report must show adapters_run >= 2 and the same resumed-on-same-correlation result for both. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is that the second adapter is chosen for a different execution model - a stream rather than a request - not for being a different approval product. | claimed | `F-b1-04`, `X-entry-composition-021`, `X-end-to-end-017` "AG-UI transmits a continuous sequence of JSON-formatted events through standard web protocols like HTTP, SSE, or WebSockets. Each event carries a type field that identifies the action taking place" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/human-interaction/test.sh && python3 harness/human-interaction/conformance.py --surface dryrun --surface second |
| Expected | Measured by tools/measure.py at bf17237: exit 0; last lines: # one store, one ask: parked by parked-item-request-response/0.1, decided by event-stream-client/0.1, same correlation True \| adapters_run=2 failures=0 |
| Deliberate breakage | In harness/human-interaction/store.py, stop refusing a decision whose correlation_id is not the parked ask's (make that comparison never true), run the criterion (a decision on a foreign handle is accepted and the gate exits 1), then git checkout harness/human-interaction/store.py. |
| Expected failure | Measured by tools/measure.py at bf17237: exit 1; last lines:   FAIL the same suite passes again once the store is the resume point (expected 0, got 1) \| passed 33, failed 6 |
| Status | measured |
| Evidence | `F-b1-04`, `F-b4-08` "Every externally-triggered action is safe to replay" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `cap-human-interaction-implement` | cap-human-interaction states the contract (T-t1-01); this facet is how it gets built here: what to write first, how the unit that already parks workflows becomes an adapter rather than the design, how a streaming surface is added beside it without touching the run, and what has to be stamped on a pause and on a resume so no surface can decline it. | `references/cap-human-interaction-implement.md` |
| `compose-approval` | Fix the recipe for a gate: a workflow runs up to an irreversible action and stops on a durable record, a person is given something they can actually decide from, and the run continues exactly once on the identifier it already had - so that pausing for a human is a composition of capabilities this platform already owns rather than a feature of whichever screen is in front of the decider. | `references/compose-approval.md` |
| `compose-approval-implement` | Turn the gate compose-approval fixes into something that runs here: two decision wires behind one resume seam, a durable gate record that outlives every process, and a migration that never leaves a window in which one decision can be applied twice. | `references/compose-approval-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-ceremony`, `build-evidence`, `build-skill-authoring`, `cap-document-validation`, `cap-errors`, `cap-idempotency`, `cap-identity`, `cap-scheduling`, `cap-work-intake`

Used by: `build-evidence`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which standard governs this interface, given that PASS.md B3 has no Human interaction row and therefore no standard column to read? The manifest names three - an event protocol for the surface, a task state for the pause, and a typed request kind for the ask - and they overlap. | 1-3-1 applied and recorded on 2026-09-03. Options: (a) name all three, each governing one part - the event protocol governs watch, the task state governs the pause and resume identity, the typed request kind governs the ask's schema; (b) pick the event protocol alone and treat the other two as adapters that map into it; (c) declare no governing standard and design the pause here, as the two seam boundaries do. Recommendation and default: (a). What would settle it is a fetch of all three specifications recording whether their identifiers and states can be mapped one-to-one; the proxy blocked documentation fetches in this session, so all three are recorded with version unverified. | All three, each governing one operation, with version unverified. (b) makes the pause a property of one surface protocol, which is the coupling this interface exists to remove, and (c) is only warranted where nobody has published a decision - the recorded position is that everything else in B3 is a decision someone else already published. | `T-t5-02`, `F-b5-06` "Everything else in B3 is a decision someone else already published." |
| Where does the adapter pair for this capability live, and under what entity ids, given that kb/entities.jsonl has no adapter or swap-candidate entity for a capability PASS.md does not have a row for? | 1-3-1 applied and recorded on 2026-09-03. Options: (a) carry the pair here with proposed entity ids declared as proposed in the row itself, as cap-errors-implement does for its own missing swap candidate; (b) append new entities to kb/entities.jsonl, which rewrites the entity chain head that every written skill pins in provenance; (c) defer the pair to cap-human-interaction-implement and carry none here. Recommendation and followed: (a). It keeps swappability visible in the ideal facet, and (b) would invalidate fifty-odd skills to add two rows. | The pair is carried above with proposed entity ids, and a kb rebuild that adds a Human interaction row to PASS.md B3 is what would replace them with real ones. build-adapter-pair states the rule this serves (F-b1-04); what is decided here is only where the pair for a rowless capability may live. | `T-t5-02`, `F-b1-04` "Swappability is a tested property, not an intention." |
| Is a human decision an entry into the platform, or a message into a run that already exists? | Whether a decision ever needs the fields an entry envelope requires that it does not already inherit from the run it resumes - a workflow reference, a budget ceiling of its own, an intent. If it never does, it is a message into an existing run and belongs on the correlation id rather than at intake. | Proposed: a message into an existing run. TARGET T1.1's first entry - a human starting work - is served by work intake; this interface serves the second and third times that person is needed, and giving a decision its own entry envelope would mint a second run id for something that must resume the first. | `T-t1-01`, `F-b3-08` "A human must be able to enter the system." |
| Who may answer a gate, and over what wire, once a plan nests? A depth-3 run with a gate at each level has to say whether the decider is the root run's owner, the subject named on the ask, or whoever holds the surface, and whether a decision may arrive over a wire other than the one that watched. | Park a gate at each level of a depth-3 run across both surfaces this capability ships and record, per gate, which subject the policy admitted as decider and which wire carried the decision; the reference example lists this as unsolved and names the common workaround, running each stage as its own workflow, as a constraint rather than an answer. | Until then: the ask names one deciding subject, resolved from the root run's owner and the policy verdict, and a decision is accepted from any surface that can authenticate that subject against the run's correlation id. | `REF-11-07`, `REF-7-07`, `REF-12-10` "Who may answer a gate, over what wire" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-human-interaction 2831cb4f, 2026-09-03 |
