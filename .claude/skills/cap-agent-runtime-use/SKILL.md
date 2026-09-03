---
name: cap-agent-runtime-use
description: How to run one agent turn and read what came back: the three fields you supply, the one field you branch on, two worked turns, what a failure looks like, and why swapping the thing that runs the agent changes nothing you wrote. Load it when a human, an agent or an event needs an agent to do one piece of work, when writing the caller side of a step in a workflow or a loop, when deciding what to do with a turn that stopped early or was cancelled, when a deadline has to stop work that is already running, or when you are about to write a branch on which agent answered.
---

# cap-agent-runtime-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make one agent turn callable in three fields and readable in one: say what to do, get back why it stopped. Everything else about running an agent is hidden behind the call, because composability hides the complexity. | sourced | `T-t2-01`, `T-t3-01`, `E-capability-agent-runtime` "Composability hides the complexity." |

## Entities

| Entity |
|---|
| `E-capability-agent-runtime` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| run_turn (proposed) | the prompt, a correlation id you choose, and optionally how many seconds you are willing to wait for a cancellation to land; everything else has a default | one turn result: why it stopped, whatever it produced, and what it cost. There is no second call to make before you have an answer (proposed) | proposed | `T-t3-01` |
| cancel (proposed) | the handle of a turn that is still running | acceptance, not a stop: keep reading until the terminal result arrives, which says cancelled if it landed in time and cancel_timeout if it did not (proposed) | proposed | - |
| read (proposed) | the turn result | the stop reason, which is the only field you branch on; outputs and usage are data you pass on, and a failure arrives as a typed problem rather than as text to read (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**Worked turn 1 (proposed): a human asks for one turn and it finishes** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:example:end-turn",
  "title": "One turn, run to completion",
  "description": "Sent: three fields. Returned: a terminal result. Nothing was negotiated, streamed or configured by the caller.",
  "examples": [
    {
      "sent": {
        "prompt": [
          {
            "kind": "text",
            "content": "make the failing test in tests/test_ledger.py pass"
          }
        ],
        "correlation_id": "run-2026-09-03-0011",
        "cancel_grace_s": 10
      },
      "returned": {
        "stop_reason": "end_turn",
        "terminal": true,
        "frames_after_terminal": 0,
        "outputs": [
          {
            "digest": "sha256:0f2b\u2026",
            "media_type": "text/x-diff"
          }
        ],
        "usage": {
          "wall_ms": 41200,
          "tokens_in": 8100,
          "tokens_out": 1900
        },
        "correlation_id": "run-2026-09-03-0011"
      }
    }
  ]
}
```

**Worked turn 2 (proposed): an event starts a turn and a deadline stops it mid-tool-call** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:example:cancelled",
  "title": "One turn, cancelled while a tool call was running",
  "description": "The caller issued no cancel; the deadline above the turn did. Work already produced is returned rather than discarded, and the reason says what happened.",
  "examples": [
    {
      "sent": {
        "prompt": [
          {
            "kind": "text",
            "content": "summarise the retained log window for fault family disk-io"
          }
        ],
        "correlation_id": "evt-2026-09-03-0042",
        "cancel_grace_s": 10
      },
      "returned": {
        "stop_reason": "cancelled",
        "terminal": true,
        "frames_after_terminal": 0,
        "cancel_to_terminal_s": 8.1,
        "outputs": [
          {
            "digest": "sha256:7a91\u2026",
            "media_type": "text/markdown"
          }
        ],
        "usage": {
          "wall_ms": 13400,
          "tokens_in": 22000,
          "tokens_out": 400
        },
        "correlation_id": "evt-2026-09-03-0042"
      }
    }
  ]
}
```

**What a failure looks like (proposed): problem details, not prose** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:example:cancel-timeout",
  "title": "The grace window expired and the unit was hard-stopped",
  "$ref": "urn:agentic:problem:0.1",
  "description": "A hard stop is a failure, never a clean cancellation. Branch on type; read detail only to report it.",
  "examples": [
    {
      "type": "urn:agentic:problem:cancel-timeout",
      "title": "Turn did not reach a terminal frame inside the grace window",
      "status": 504,
      "detail": "cancel issued at t=5s, grace 10s, no terminal frame by t=15s; the unit was destroyed",
      "retryable": true,
      "retry_after_s": 30,
      "stop_reason": "cancel_timeout",
      "correlation_id": "evt-2026-09-03-0042"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a turn through the same call. How the work arrived is not a field of the turn, so one caller-side handler covers all three. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Proposed: three fields go in and one field is branched on. Sessions, capability negotiation, transports, frame streams, permission callbacks and the identity of the runtime are all below the call, and a caller that never mentions them still gets every one of them handled. | proposed | `T-t3-01`, `T-t2-01` |
| Enhancing one aspect leaves the rest untouched: replacing the runtime, adding a stop reason, turning streaming on, or moving where the turn executes changes nothing in a caller that reads stop_reason, outputs and usage. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Budget, policy, identity, telemetry and provenance are applied around every turn whichever entry point started it, and there is no field for asking for them or declining them. | sourced | `T-t2-03`, `F-b4-01` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| Proposed: a failure arrives as the typed problem object, which cap-agent-runtime requires this boundary to return and cap-errors defines (F-b4-07). Branch on its type; read detail only to show a person, and never to decide anything. | proposed | `F-b4-07` |
| Proposed: cancel is a request and a hard stop is a failure. A result saying cancelled means the turn ended on request inside the window; a problem saying cancel_timeout means it did not, and the two must not be collapsed by a caller into 'it stopped'. | proposed | `F-a3-09` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Send the prompt, a correlation id you chose, and nothing else unless you have a reason. Take the default grace window; take the default capability set. | It has to be simple to use, and every field you fill in is a decision you now own. The defaults are the ones the platform can change under you without breaking your call. | sourced | `T-t3-01` "It has to be simple to use." |
| 2 | Branch on stop_reason and on nothing else. Treat end_turn as the ordinary ending, max_tokens and max_turn_requests as ran-out-of-room, refusal as declined, and cancelled as stopped on request. | The stop reason is a closed set, so the branch is writeable and stays written; any other field you branch on is either data you should pass on or detail that belongs to whatever is running the agent. | sourced | `T-t2-02` "enhancing particular aspects of any element without touching the rest" |
| 3 | To stop work already running, ask for cancellation and keep reading until the terminal result arrives. Do not close the connection, kill the process, or stop reading early. | Proposed guidance: late frames are legal and the terminal result is what tells you whether the stop was clean, so a caller that stops reading early turns a cancellation into an unknown. | proposed | `F-a3-09` |
| 4 | Prefer a deadline on the work over a cancel you send by hand: set the deadline when you start the turn and let the platform issue the cancel. | Proposed. The same grace rules then apply whichever entry started the work, and you do not need a timer, a watcher or a second code path in the caller. | proposed | `T-t2-03` |
| 5 | Read a failure as a problem object: branch on type, use retryable and retry_after_s as given, and never parse the words. | cap-agent-runtime requires this boundary to return typed failures and cap-agent-runtime-implement wires the runtime's untyped paths onto it (F-b4-07); what this adds for a caller is that the runtime's own message text is not part of the contract and will change under you. | sourced | `F-b4-07` "Never parsed from prose" |
| 6 | Compose upward, not inward: a turn is one step. Retries, several turns in sequence, an approval in the middle, and a whole agent are built above this call rather than by adding fields to it. | Any entry can call complex workflows, agents and loops that run across the entire stack, so the complexity belongs to the composition and this call stays the same size no matter how large the thing above it gets. | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| 7 | To change which runtime, model class or execution style serves your turn, change configuration. Do not add an argument, and do not write a branch on which one answered. | A caller-side branch on the implementation is the boundary leaking, and it is the one change that would make every future swap your problem instead of a configuration change. | sourced | `T-t2-02`, `F-b1-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| 8 | If this page starts to feel like something you must study before calling, stop and cut it rather than adding to it: the caller-facing surface is three fields in and one field out. | It cannot be daunting or overly complex, or no one will use it - which makes size a property of the interface to defend, not a documentation problem to solve later. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Set the correlation id yourself and reuse it across every step of the same piece of work, including the failure paths, so the whole run can be found from one value whichever entry point started it. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| Proposed: ask for streaming only if something is actually watching. A stream you request and discard costs the platform a live session and buys the caller nothing, and it is the one option that makes an otherwise portable call fail against a runtime that has no stream. | proposed | - |
| cap-agent-runtime already states that a stop reason is not a verdict (F-a7-03). What it adds for a caller: end_turn means the agent stopped, so if you need to know whether the work is acceptable, ask the Judge - do not read end_turn as approval. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: keep whatever a cancelled turn produced. A cancelled turn with outputs is a partial result, not a loss, and discarding it in the caller throws away work the platform already made durable. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/render_skill.py .claude/skills/cap-agent-runtime-use && python3 tools/validate_skills.py --only cap-agent-runtime-use`. This skill has no Adapters section, so the validator's product-purity check covers the whole page: it proves that nothing a caller reads here - the operations, the worked turns, the failure - names the runtime that serves the turn, which is the promise this facet makes. |
| Expected | `rendered cap-agent-runtime-use/SKILL.md` then `cap-agent-runtime-use: 0 errors, 0 warnings`, exit 0. |
| Deliberate breakage | In the first worked turn, replace the `media_type` value `text/x-diff` with the name of the runtime that runs agents today (the product PASS.md A3 names in its Agent runtime row), re-render, and re-run the validator. |
| Expected failure | exit 1 with `cap-agent-runtime-use: product name(s) ['<the A3 runtime name>'] outside Adapters, in section 'Contract'` and a closing `cap-agent-runtime-use: 1 errors, 0 warnings`. Measured in session cap-agent-runtime 2831cb4f on 2026-09-03: the breakage produced exactly that line with the runtime's name in the list, and exit 1; restoring the file returned 0 errors, 0 warnings and exit 0. |
| Status | measured |
| Evidence | `F-part-c-04`, `T-t2-01` "Composability hides the complexity." |

## Composes with

Builds on: `cap-agent-runtime`, `cap-agent-runtime-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should a caller ever be allowed to name the runtime it wants? | Count the cases where a composition genuinely cannot proceed without a specific runtime rather than a specific capability. If every such case turns out to be a capability - cancellable, streaming, callback-capable - then the negotiated capability set already covers it and no runtime selector is needed. | No runtime selector on the call. A caller may state the capabilities it needs and the platform picks; adding a selector later is cheaper than removing one after callers depend on it. | `T-t2-01` "Composability hides the complexity." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-agent-runtime 2831cb4f, 2026-09-03 |
