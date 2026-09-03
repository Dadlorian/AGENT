# cap-human-interaction: the caller's view

Proposed. Folded in from the former `cap-human-interaction-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-human-interaction` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-human-interaction states the contract and cap-human-interaction-implement builds it; this facet reduces both to two things a caller does - emit an ask, accept a decision - so that adding a human step to a workflow is a field on a step rather than a subsystem you own.  
  _sourced_ - `T-t3-01`, `T-t1-01` "It has to be simple to use."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| ask (the whole of what a workflow author writes) | prompt, response_schema, proposed {action, diff, irreversibility}, deadline_at - and nothing else; the correlation id, the actor, the ceiling and the audience come from the run you are already in (proposed) | an ask_id; your step suspends and holds nothing open. You do not poll, and you do not get a callback URL to keep (proposed) | proposed | `T-t3-01` |
| decide (the whole of what a decider sends) | ask_id, correlation_id, one of approve, edit, reject or respond, the deciding actor, an idempotency key, and a body when the decision carries one (proposed) | an acknowledgement, or a problem-details object naming what to change; on edit the run continues with your body as its artifact (proposed) | proposed | `X-entry-composition-023` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-human-interaction` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a run parks, and a person decides - TARGET T1's first way in

_proposed_ - sources: `T-t1-01`, `X-end-to-end-018`.

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

### Worked example 2 (proposed): an agent decides, and an event delivers a decision recorded elsewhere - TARGET T1's other two ways in

_proposed_ - sources: `T-t1-01`, `X-entry-composition-024`.

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

### The failure shape (proposed): a decision that arrives after its ask closed

_proposed_ - sources: `F-b3-13`, `X-cap-human-interaction-008`.  Also carried in the body of `cap-human-interaction` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-human-interaction` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Write the response schema as the shape of the thing you want back, not as a yes/no flag. If the answer is an edited artifact, the schema describes the artifact.**  
  _why:_ The platform validates the decision body against your schema before the run resumes, and it is what the surface generates its form from - so a schema that says only approved: boolean gives every decider a checkbox, whatever the question actually was.  
  _sourced_ - `X-cap-human-interaction-006`, `F-b3-09` "the client renders an appropriate form or prompt, the user responds, and execution resumes"
- **Continue from the decision body, not from what you proposed. On edit and respond, the body is the artifact; on approve there is no body; on reject the body carries notes and the run does not proceed.**  
  _why:_ cap-human-interaction states the four decisions and that an edit changes the artifact rather than the verdict (X-entry-composition-023). A step that reads the verdict and then uses its own proposal is the single most common way an approval turns out to have been decorative.  
  _sourced_ - `X-end-to-end-019` "the agent proposes and the human publishes"
- **Send the decision on the correlation id that came with the ask, and derive the idempotency key from the ask and the decision. Never mint a new run identifier for a decision.**  
  _why:_ cap-human-interaction states the preservation rule (X-entry-composition-015): correlation IDs should be preserved at every boundary. The consequence for you is blunt - a decision on a new identifier starts something instead of resuming something, and the run you meant to steer stays parked until it expires.  
  _sourced_ - `X-entry-composition-015`, `F-b4-08` "Correlation IDs should be preserved at every boundary"
- **Set a deadline you would actually accept, and decide up front what happens when it passes. The default is that the run terminates with a typed expiry problem.**  
  _why:_ Design explicit timeouts for human steps rather than letting approvals sit indefinitely: a run parked with no deadline holds its correlation id, its budget and its place in an audit trail for as long as nobody notices it.  
  _sourced_ - `X-cap-human-interaction-008` "design explicit timeouts for human steps rather than letting approvals sit indefinitely"
- **Read a refusal as a problem-details object: check type first, then retryable, and act on detail. Do not branch on the status code alone and do not retry a refusal marked not retryable.**  
  _why:_ Proposed usage of the failure shape above. The three refusals a caller actually meets are an expired ask, a body that does not match the response schema, and a decider outside the ask's audience; only the second is fixed by sending again.  
  _proposed_ - `F-b3-13`

## Other caller invariants

- You never hold the run open. cap-human-interaction states that the parked state belongs to the platform and cap-human-interaction-implement wires the waiting; for a caller the consequence is that your step suspends, your process may exit, and the arriving decision is what wakes the run - a suspended run should wait at zero cost, however long it takes.  
  _sourced_ - `X-entry-composition-029` "The function waits at zero cost, however long it takes."
- A refusal tells you what to change: cap-errors owns the closed registry, and cap-human-interaction requires every refusal here to be typed and machine-readable, never parsed from prose. As a caller you read type, detail and retryable, and you never scrape a message off a screen.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"

## Caller practices

- Show the diff, not the description: give the reviewer proposed.diff and let the prompt be one line. cap-human-interaction cites the same review-queue prior art for putting the gate on the action; the caller-side consequence is that optional edit-in-place beats approve-then-fix only when the reviewer can see the change they are editing.  
  _sourced_ - `X-end-to-end-018` "Optional edit-in-place beats approve-then-fix."
- Declare the gated actions when you declare the workflow, not when you reach them. cap-human-interaction states the practice from the prior art on file - tools requiring approval can be marked during registration - and what it buys a composer is that the steps which will stop and ask are readable before a run starts.  
  _sourced_ - `X-entry-composition-054` "Tools requiring approval can be marked during registration"
- Let people watch before you make them decide: the run's typed event stream is readable by anyone with the correlation id, and a reviewer who has followed the run answers a different, better question than one who is handed a form cold.  
  _sourced_ - `X-end-to-end-016` "events reflecting everything that happens during a live agent session"
- Proposed: ask once, with everything. Two asks in a row - approve the plan, then approve the patch - double the wall-clock time a run is parked and double the chance it expires; if the second question is always asked, it belongs in the first ask's response schema.  
  _proposed_ - `T-t3-01`

## Open questions carried over

- **May an agent be the decider on an ask a person was asked to answer, when the deadline is close?**  
  _deciding evidence:_ Count, over real asks, how often an expiry would have been avoided by an agent deciding and how often that agent would have decided differently from the person who eventually did. If the second number is not near zero, an agent fallback is an unlogged policy change.  
  _default until then:_ Proposed: no automatic fallback. An agent decides only when the ask's audience names it, and an ask whose audience is a person expires rather than being answered by something else; expiry is visible in the audit trail, a substituted decider is not.  
  `X-cap-human-interaction-008` "design explicit timeouts for human steps"
- **cap-errors' closed problem registry has no row for a decision that arrives after its ask closed, so which type does the refusal carry?**  
  _deciding evidence:_ cap-errors requires 1-3-1 rather than minting a suffix at the call site, so the three options were: reuse the registered `deadline-exceeded`, which is 504 and retryable and so tells a caller to retry a run that has already ended; reuse `idempotency-conflict` for its 409, which names a key collision rather than a closed ask and would make a caller parse a conflict it did not cause; or add one row `human-ask-expired` (409, not retryable, extension members ask_id and closed_at) to docs/decomposition.md section 2.1.6 and use it. The third is recommended and is what the failure shape above shows, pending that row.  
  _default until then:_ `urn:agentic:problem:human-ask-expired`, marked proposed and pending registration; until the row lands an implementation returns `deadline-exceeded` with the ask id in detail rather than inventing a type, accepting that its retryable member misdirects a caller, which is itself the argument for adding the row.  
  `T-t5-02`, `X-cap-human-interaction-008` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation"

