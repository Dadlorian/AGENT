---
name: cap-human-interaction-use
description: How to stop a run and ask someone, as a caller: emit one ask, wait for nothing, and let the decision resume the run on the identifier it already had. The same two shapes whether the decider is a person on a phone, a reviewing agent, or an external system posting an approval it recorded elsewhere. Load it when a step should not run unattended, when adding an approval or a review to a workflow you are composing, when you need a reviewer to change what the run does rather than only whether it proceeds, when a decision was refused and you need to know what to fix, or when you are about to build an approval screen of your own.
---

# cap-human-interaction-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-human-interaction states the contract and cap-human-interaction-implement builds it; this facet reduces both to two things a caller does - emit an ask, accept a decision - so that adding a human step to a workflow is a field on a step rather than a subsystem you own. | sourced | `T-t3-01`, `T-t1-01` "It has to be simple to use." |

## Entities

| Entity |
|---|
| `E-standard-rfc-9457-problem-details` |
| `E-standard-json-schema-2020-12` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| ask (the whole of what a workflow author writes) | prompt, response_schema, proposed {action, diff, irreversibility}, deadline_at - and nothing else; the correlation id, the actor, the ceiling and the audience come from the run you are already in (proposed) | an ask_id; your step suspends and holds nothing open. You do not poll, and you do not get a callback URL to keep (proposed) | proposed | `T-t3-01` |
| decide (the whole of what a decider sends) | ask_id, correlation_id, one of approve, edit, reject or respond, the deciding actor, an idempotency key, and a body when the decision carries one (proposed) | an acknowledgement, or a problem-details object naming what to change; on edit the run continues with your body as its artifact (proposed) | proposed | `X-entry-composition-023` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a run parks, and a person decides - TARGET T1's first way in** (proposed; sources: `T-t1-01`, `X-end-to-end-018`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:example:human",
  "title": "A person edits a proposed patch instead of rejecting it",
  "description": "The run emitted the ask and suspended; a person opened whichever surface is configured and sent the decision back on the same correlation_id. The run continued with the reviewer's patch.",
  "examples": [
    {
      "ask": {
        "ask_id": "ask-deploy-0001",
        "correlation_id": "corr-human-0001",
        "prompt": "Apply this fix to pricing/coupon.py and deploy?",
        "response_schema": {
          "type": "object",
          "required": [
            "patch"
          ],
          "properties": {
            "patch": {
              "type": "string"
            }
          }
        },
        "proposed": {
          "action": "deploy pricing/coupon.py",
          "diff": "-    tier = ctx['tier']\n+    tier = ctx.get('tier', 'standard')",
          "irreversibility": "compensatable"
        },
        "deadline_at": "2026-09-03T18:00:00Z"
      }
    },
    {
      "decision": {
        "ask_id": "ask-deploy-0001",
        "correlation_id": "corr-human-0001",
        "decision": "edit",
        "actor": "user:corey",
        "body": {
          "patch": "-    tier = ctx['tier']\n+    tier = ctx['tier'] if 'tier' in ctx else tenant_default(ctx)"
        },
        "idempotency_key": "ask-deploy-0001-edit"
      }
    }
  ]
}
```

**Worked example 2 (proposed): an agent decides, and an event delivers a decision recorded elsewhere - TARGET T1's other two ways in** (proposed; sources: `T-t1-01`, `X-entry-composition-024`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:hitl:example:agent-and-event",
  "title": "The same two shapes when the decider is not a person",
  "description": "Nothing about the ask changes. Only the actor prefix differs, and the platform records who decided either way. An agent decider is still bound by the ask's audience and by policy.",
  "examples": [
    {
      "decision": {
        "ask_id": "ask-deploy-0001",
        "correlation_id": "corr-human-0001",
        "decision": "approve",
        "actor": "agent:release-reviewer",
        "idempotency_key": "ask-deploy-0001-agent-approve"
      }
    },
    {
      "decision": {
        "ask_id": "ask-window-0002",
        "correlation_id": "corr-human-0001",
        "decision": "respond",
        "actor": "service:change-ticket-webhook",
        "body": {
          "window_hours": 12
        },
        "idempotency_key": "chg-88421-approved"
      }
    }
  ]
}
```

**The failure shape (proposed): a decision that arrives too late** (proposed; sources: `F-b3-13`, `X-cap-human-interaction-008`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:example:human-ask-expired",
  "title": "The ask is no longer open",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Media type application/problem+json. The run already ended with deadline_exceeded, so there is nothing to resume; a new run is the remedy, not a retry.",
  "examples": [
    {
      "type": "urn:agentic:problem:human-ask-expired",
      "title": "The ask is no longer open",
      "status": 409,
      "detail": "ask-deploy-0001 expired at 2026-09-03T18:00:00Z after 8h open; the run terminated with deadline_exceeded.",
      "retryable": false,
      "correlation_id": "corr-human-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| You never hold the run open. cap-human-interaction states that the parked state belongs to the platform and cap-human-interaction-implement wires the waiting; for a caller the consequence is that your step suspends, your process may exit, and the arriving decision is what wakes the run - a suspended run should wait at zero cost, however long it takes. | sourced | `X-entry-composition-029` "The function waits at zero cost, however long it takes." |
| The three ways in are the same two shapes. TARGET T1 names a human, an agent, and an internal or external event as the ways into the system; here all three send one HumanDecision differing only in the actor prefix - user:, agent:, service: - and each is recorded as the deciding actor. This is the one enumeration of ways in used in this skill. | sourced | `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: composability allows enhancing particular aspects of any element without touching the rest. Change the surface people decide on, tighten a response schema, or add a deadline sweeper, and no workflow that parks is edited - the ask and the decision are the only things any of them named. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| A refusal tells you what to change: cap-errors owns the closed registry, and cap-human-interaction requires every refusal here to be typed and machine-readable, never parsed from prose. As a caller you read type, detail and retryable, and you never scrape a message off a screen. | sourced | `F-b3-13` "RFC 9457 problem details" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the ask on the step that is about to do something hard to undo: prompt, response schema, the proposed action with its diff and irreversibility class, and a deadline. Then return; the platform suspends the run. | cap-human-interaction states this as a best practice from the prior art on file - approval gates on irreversible actions are the typical defenses - so the gate belongs where something becomes hard to undo rather than at a fixed step number. What is yours as a caller is only the four fields; storing, notifying, timing out and resuming are the platform's. | sourced | `X-end-to-end-063` "approval gates on irreversible actions are the typical defenses" |
| 2 | Write the response schema as the shape of the thing you want back, not as a yes/no flag. If the answer is an edited artifact, the schema describes the artifact. | The platform validates the decision body against your schema before the run resumes, and it is what the surface generates its form from - so a schema that says only approved: boolean gives every decider a checkbox, whatever the question actually was. | sourced | `X-cap-human-interaction-006`, `F-b3-09` "the client renders an appropriate form or prompt, the user responds, and execution resumes" |
| 3 | Continue from the decision body, not from what you proposed. On edit and respond, the body is the artifact; on approve there is no body; on reject the body carries notes and the run does not proceed. | cap-human-interaction states the four decisions and that an edit changes the artifact rather than the verdict (X-entry-composition-023). A step that reads the verdict and then uses its own proposal is the single most common way an approval turns out to have been decorative. | sourced | `X-end-to-end-019` "the agent proposes and the human publishes" |
| 4 | Send the decision on the correlation id that came with the ask, and derive the idempotency key from the ask and the decision. Never mint a new run identifier for a decision. | cap-human-interaction states the preservation rule (X-entry-composition-015): correlation IDs should be preserved at every boundary. The consequence for you is blunt - a decision on a new identifier starts something instead of resuming something, and the run you meant to steer stays parked until it expires. | sourced | `X-entry-composition-015`, `F-b4-08` "Correlation IDs should be preserved at every boundary" |
| 5 | Set a deadline you would actually accept, and decide up front what happens when it passes. The default is that the run terminates with a typed expiry problem. | Design explicit timeouts for human steps rather than letting approvals sit indefinitely: a run parked with no deadline holds its correlation id, its budget and its place in an audit trail for as long as nobody notices it. | sourced | `X-cap-human-interaction-008` "design explicit timeouts for human steps rather than letting approvals sit indefinitely" |
| 6 | Do not build an approval screen, an approval inbox or a notifier of your own. If the surface you need does not exist, add it as a surface adapter behind this interface and read cap-human-interaction-implement's conformance checklist. | A screen of your own is a second place decisions are recorded, a second set of identifiers, and a second thing to authenticate; and it takes the four decisions out of the interface and into one workflow. It cannot be daunting or overly complex, or no one will use it - which cuts both ways: one surface everyone knows beats three that each do a little more. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |
| 7 | Read a refusal as a problem-details object: check type first, then retryable, and act on detail. Do not branch on the status code alone and do not retry a refusal marked not retryable. | Proposed usage of the failure shape above. The three refusals a caller actually meets are an expired ask, a body that does not match the response schema, and a decider outside the ask's audience; only the second is fixed by sending again. | proposed | `F-b3-13` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Show the diff, not the description: give the reviewer proposed.diff and let the prompt be one line. cap-human-interaction cites the same review-queue prior art for putting the gate on the action; the caller-side consequence is that optional edit-in-place beats approve-then-fix only when the reviewer can see the change they are editing. | sourced | `X-end-to-end-018` "Optional edit-in-place beats approve-then-fix." |
| Declare the gated actions when you declare the workflow, not when you reach them. cap-human-interaction states the practice from the prior art on file - tools requiring approval can be marked during registration - and what it buys a composer is that the steps which will stop and ask are readable before a run starts. | sourced | `X-entry-composition-054` "Tools requiring approval can be marked during registration" |
| Let people watch before you make them decide: the run's typed event stream is readable by anyone with the correlation id, and a reviewer who has followed the run answers a different, better question than one who is handed a form cold. | sourced | `X-end-to-end-016` "events reflecting everything that happens during a live agent session" |
| Proposed: ask once, with everything. Two asks in a row - approve the plan, then approve the patch - double the wall-clock time a run is parked and double the chance it expires; if the second question is always asked, it belongs in the first ask's response schema. | proposed | `T-t3-01` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | The caller-side half of cap-human-interaction's criterion: `python3 tools/conformance/human_resume.py --decider user:corey --decider agent:release-reviewer --decider service:change-ticket-webhook --case approve --case edit --case reject-with-notes --case partial --report out/hitl-use.json` (proposed tool). One workflow parks one ask; each of TARGET T1's three ways in delivers one decision per case against it. It asserts `resumed_on_same_correlation == cases_run` for every decider, `edit_changed_artifact == true`, `workflow_edits == 0` (no workflow file changed between deciders) and `untyped_refusals == 0`. |
| Expected | exit 0 with `deciders_run: 3`, `resumed_on_same_correlation: 4` per decider, `edit_changed_artifact: true`, `workflow_edits: 0` and `untyped_refusals: 0` |
| Deliberate breakage | Give the event decider its own decision endpoint that mints a fresh run identifier instead of posting on the ask's correlation id, changing nothing else, and re-run the same command. |
| Expected failure | exit 1 with `resumed_on_same_correlation: 0` for `service:change-ticket-webhook` while the other two deciders still report 4 - the parked ask is still open and a second, unrelated run now exists. Singling out one decider is the point: a failure that hits all three is a broken fixture, not a broken boundary. Claimed: the tool, the fixture and both surface adapters do not exist here and neither run has been performed, so this check starts red by construction. |
| Status | claimed |
| Evidence | `T-t1-01`, `X-entry-composition-015` "A human must be able to enter the system." |

## Composes with

Builds on: `cap-human-interaction`, `cap-human-interaction-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| May an agent be the decider on an ask a person was asked to answer, when the deadline is close? | Count, over real asks, how often an expiry would have been avoided by an agent deciding and how often that agent would have decided differently from the person who eventually did. If the second number is not near zero, an agent fallback is an unlogged policy change. | Proposed: no automatic fallback. An agent decides only when the ask's audience names it, and an ask whose audience is a person expires rather than being answered by something else; expiry is visible in the audit trail, a substituted decider is not. | `X-cap-human-interaction-008` "design explicit timeouts for human steps" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-human-interaction 2831cb4f, 2026-09-03 |
