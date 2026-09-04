# cap-agent-runtime: the caller's view

Proposed. Folded in from the former `cap-agent-runtime-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-agent-runtime` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `agentic-stack`, which absorbed the former `cap-consumption` in the row-71 fold, and is not repeated here. 7 row(s) of that kind were dropped in the fold: ambient-guarantees, compose-upward, config-not-argument, correlation-id, problem-details, size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make one agent turn callable in three fields and readable in one: say what to do, get back why it stopped. Everything else about running an agent is hidden behind the call, because composability hides the complexity.  
  _sourced_ - `T-t2-01`, `T-t3-01`, `E-capability-agent-runtime` "Composability hides the complexity."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| run_turn (proposed) | the prompt, a correlation id you choose, and optionally how many seconds you are willing to wait for a cancellation to land; everything else has a default | one turn result: why it stopped, whatever it produced, and what it cost. There is no second call to make before you have an answer (proposed) | proposed | `T-t3-01` |
| cancel (proposed) | the handle of a turn that is still running | acceptance, not a stop: keep reading until the terminal result arrives, which says cancelled if it landed in time and cancel_timeout if it did not (proposed) | proposed | - |
| read (proposed) | the turn result | the stop reason, which is the only field you branch on; outputs and usage are data you pass on, and a failure arrives as a typed problem rather than as text to read (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-agent-runtime` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked turn 1 (proposed): a human asks for one turn and it finishes

_proposed_ - sources: -.

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
            "digest": "sha256:0f2b…",
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

### Worked turn 2 (proposed): an event starts a turn and a deadline stops it mid-tool-call

_proposed_ - sources: -.

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
            "digest": "sha256:7a91…",
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

### What a failure looks like (proposed): problem details, not prose

_proposed_ - sources: -.  Also carried in the body of `cap-agent-runtime` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-agent-runtime` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Branch on stop_reason and on nothing else. Treat end_turn as the ordinary ending, max_tokens and max_turn_requests as ran-out-of-room, refusal as declined, and cancelled as stopped on request.**  
  _why:_ The stop reason is a closed set, so the branch is writeable and stays written; any other field you branch on is either data you should pass on or detail that belongs to whatever is running the agent.  
  _sourced_ - `T-t2-02` "enhancing particular aspects of any element without touching the rest"
- **To stop work already running, ask for cancellation and keep reading until the terminal result arrives. Do not close the connection, kill the process, or stop reading early.**  
  _why:_ Proposed guidance: late frames are legal and the terminal result is what tells you whether the stop was clean, so a caller that stops reading early turns a cancellation into an unknown.  
  _proposed_ - `F-a3-09`
- **Prefer a deadline on the work over a cancel you send by hand: set the deadline when you start the turn and let the platform issue the cancel.**  
  _why:_ Proposed. The same grace rules then apply whichever entry started the work, and you do not need a timer, a watcher or a second code path in the caller.  
  _proposed_ - `T-t2-03`

## Other caller invariants

- Proposed: three fields go in and one field is branched on. Sessions, capability negotiation, transports, frame streams, permission callbacks and the identity of the runtime are all below the call, and a caller that never mentions them still gets every one of them handled.  
  _proposed_ - `T-t3-01`, `T-t2-01`
- Proposed: cancel is a request and a hard stop is a failure. A result saying cancelled means the turn ended on request inside the window; a problem saying cancel_timeout means it did not, and the two must not be collapsed by a caller into 'it stopped'.  
  _proposed_ - `F-a3-09`

## Caller practices

- Proposed: ask for streaming only if something is actually watching. A stream you request and discard costs the platform a live session and buys the caller nothing, and it is the one option that makes an otherwise portable call fail against a runtime that has no stream.  
  _proposed_ - -
- cap-agent-runtime already states that a stop reason is not a verdict (F-a7-03). What it adds for a caller: end_turn means the agent stopped, so if you need to know whether the work is acceptable, ask the Judge - do not read end_turn as approval.  
  _sourced_ - `F-a7-03` "Those establish well-formedness, not correctness"
- Proposed: keep whatever a cancelled turn produced. A cancelled turn with outputs is a partial result, not a loss, and discarding it in the caller throws away work the platform already made durable.  
  _proposed_ - -

## Open questions carried over

- **Should a caller ever be allowed to name the runtime it wants?**  
  _deciding evidence:_ Count the cases where a composition genuinely cannot proceed without a specific runtime rather than a specific capability. If every such case turns out to be a capability - cancellable, streaming, callback-capable - then the negotiated capability set already covers it and no runtime selector is needed.  
  _default until then:_ No runtime selector on the call. A caller may state the capabilities it needs and the platform picks; adding a selector later is cheaper than removing one after callers depend on it.  
  `T-t2-01` "Composability hides the complexity."

