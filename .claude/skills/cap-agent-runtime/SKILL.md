---
name: cap-agent-runtime
description: The ideal state of the Agent runtime capability: one prompt turn with a stop reason as the unit of agent execution, governed by the Agent Client Protocol, with the operations the core imports, the turn shapes, what the boundary refuses to expose, and the criteria that decide whether a candidate runtime may serve the interface. Load it when deciding how a single agent turn is started, streamed, permitted or cancelled, when asking 'why did that turn stop', 'how do we stop a run that is already mid-tool-call', or 'can we drive a different agent without touching the core', and whenever an interface is about to require a live session, a stream or a callback that a one-shot, headless or batch runner could never provide.
---

# cap-agent-runtime

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for driving an agent through a single prompt turn and learning why that turn stopped, so the middle column is what the core imports and any conformant agent can serve it. | sourced | `F-b3-05`, `F-b3-01`, `E-capability-agent-runtime` "The middle column is the contract" |

## Entities

| Entity |
|---|
| `E-capability-agent-runtime` |
| `E-standard-agent-client-protocol` |
| `E-swap-candidate-any-acp-speaking-agent` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-agent-client-protocol` | wire protocol v1 stable; v2 Draft since 2026-07-20 | unverified | - | `F-b3-05`, `X-cap-agent-runtime-001`, `X-cap-agent-runtime-004`, `X-gap-a-001` |

- `E-standard-agent-client-protocol` version note: X-gap-a-001 (search-only, not fetched): "On July 20, 2026, the ACP team released the first Draft of version 2 of the Agent Client Protocol." v1 stability and SDK languages per X-cap-agent-runtime-001/-004. Row owned by cap-agent-runtime.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| open_session (call name is ours; sessions are one of the four things the standard itself standardizes) | an agent binding plus the client capabilities on offer: streaming updates, tool-permission callbacks, mid-turn cancellation | a session handle and the capability set actually negotiated, every member defaulting to false, so nothing interactive is a precondition of the interface (proposed) | sourced | `X-cap-agent-runtime-002` "ACP standardizes AI agent interaction (prompts, sessions, file permissions, streaming) between editors and coding agents." |
| prompt (call name is ours; prompts are one of the four things the standard itself standardizes) | a session handle and one prompt, carrying the task and never the criterion the result is judged against | one turn result carrying a stop reason; the turn is over when, and only when, a terminal frame carrying that reason has arrived (proposed) | sourced | `X-cap-agent-runtime-002` "ACP standardizes AI agent interaction (prompts, sessions, file permissions, streaming) between editors and coding agents." |
| cancel | a session handle and the per-request grace window | acceptance of the request, not a kill: the caller keeps taking frames until the terminal frame, whose stop reason is cancelled if it arrives inside the window and cancel_timeout if it does not (proposed) | sourced | `F-a3-09` "mid-tool-call ends the turn in ~8s against a 45s operation, zero trailing frames" |
| receive_updates (call name is ours; streaming is one of the four things the standard itself standardizes; optional and negotiated) | a session handle whose negotiated set has streaming updates true | an ordered stream of in-turn frames; when the capability was not negotiated the caller sees only the terminal frame and nothing else about the interface changes (proposed) | sourced | `X-cap-agent-runtime-002` "ACP standardizes AI agent interaction (prompts, sessions, file permissions, streaming) between editors and coding agents." |
| answer_permission_request (call name is ours; file permissions are one of the four things the standard itself standardizes; optional and negotiated) | a permission request raised mid-turn and the caller's decision | the decision handed back to the agent; a runtime that negotiated no callbacks never raises one, so the caller has no branch to write for it (proposed) | sourced | `X-cap-agent-runtime-002` "ACP standardizes AI agent interaction (prompts, sessions, file permissions, streaming) between editors and coding agents." |

### Shapes (JSON Schema 2020-12)

**session-capabilities (proposed summary shape; the full shapes and the stop-reason table are in references/agent-runtime-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:session-capabilities:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "streaming_updates",
    "permission_callbacks",
    "cancellable_mid_turn"
  ],
  "description": "Proposed. Negotiated at session open. Every member defaults to false, so a caller that reads this set never assumes an interactive capability is present.",
  "properties": {
    "streaming_updates": {
      "type": "boolean",
      "default": false
    },
    "permission_callbacks": {
      "type": "boolean",
      "default": false
    },
    "cancellable_mid_turn": {
      "type": "boolean",
      "default": false
    },
    "cancel_floor_s": {
      "type": "number",
      "minimum": 0,
      "description": "The adapter's observed floor for reaching a terminal frame after cancel. cancel_grace_s must be set at or above it."
    }
  }
}
```

**turn-request (proposed summary shape)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:turn-request:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "session_id",
    "prompt",
    "cancel_grace_s",
    "correlation_id"
  ],
  "properties": {
    "session_id": {
      "type": "string",
      "minLength": 1
    },
    "prompt": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object"
      },
      "description": "Content handed to the agent. Never carries the criterion the result is judged against."
    },
    "cancel_grace_s": {
      "type": "integer",
      "minimum": 1,
      "default": 10,
      "description": "Per request, not global, because each runtime adapter has a different cancel floor."
    },
    "correlation_id": {
      "type": "string",
      "minLength": 1,
      "description": "Explicit attribute set by the caller; never inherited from trace parentage across this boundary."
    },
    "max_turn_requests": {
      "type": "integer",
      "minimum": 1
    }
  }
}
```

**turn-result (proposed summary shape)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:turn-result:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "session_id",
    "stop_reason",
    "terminal",
    "frames_after_terminal",
    "usage"
  ],
  "properties": {
    "session_id": {
      "type": "string",
      "minLength": 1
    },
    "stop_reason": {
      "enum": [
        "end_turn",
        "max_tokens",
        "max_turn_requests",
        "refusal",
        "cancelled",
        "cancel_timeout",
        "adapter_unavailable"
      ],
      "description": "Proposed. The first five are taken from the protocol's own stop reasons as recorded in a design note; the specification text was not read here. cancel_timeout and adapter_unavailable are ours."
    },
    "terminal": {
      "const": true
    },
    "frames_after_terminal": {
      "type": "integer",
      "minimum": 0,
      "maximum": 0
    },
    "cancel_to_terminal_s": {
      "type": "number",
      "minimum": 0
    },
    "usage": {
      "type": "object",
      "required": [
        "wall_ms"
      ],
      "properties": {
        "wall_ms": {
          "type": "integer",
          "minimum": 0
        },
        "tokens_in": {
          "type": "integer",
          "minimum": 0
        },
        "tokens_out": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1"
    }
  }
}
```

**What a failure looks like (proposed): problem details, not prose [caller's view, folded from cap-agent-runtime-use]** (proposed; sources: -)

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
| The capability is the contract and the agent is the adapter: what the core imports is 'an agent is driven through one prompt turn and reports why the turn stopped', and the standard that governs it is the Agent Client Protocol. | sourced | `F-b3-05`, `F-b3-01`, `E-capability-agent-runtime` "Agent runtime** \| Agent Client Protocol" |
| Proposed: the unit is one prompt turn with a stop reason. A turn is over when a terminal frame carrying that reason has arrived, and never because the caller stopped reading, timed out locally, or saw output it liked. Research query: does the ACP specification (once fetched) define a terminal-frame or session/prompt-response boundary in these exact words, beyond the general prompts/sessions/streaming vocabulary already on file? | proposed | `X-cap-agent-runtime-002` |
| Every interactive capability - streaming updates, tool-permission callbacks, mid-turn cancellation - is negotiated at session open and defaults to absent. A capability the interface requires is a capability a one-shot runtime can never supply, which is exactly what build-adapter-pair's design rule 3 (F-b1-04) exists to catch: an interface that ships with only one adapter's assumptions baked in is not proven swappable until a second adapter is attempted. | sourced | `F-b1-04`, `X-cap-agent-runtime-002` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing." |
| On the substrate, cancelling mid-tool-call ends the turn in about 8 seconds against a 45 second operation with zero trailing frames. The knowledge base records this row with status claimed, so it is the reference point for the grace window and not a measurement this repository has reproduced. | sourced | `F-a3-09` "mid-tool-call ends the turn in ~8s against a 45s operation, zero trailing frames" |
| Proposed: cancel is asynchronous, idempotent and bounded. Late frames are legal until the terminal frame; the window is per request with a default of 10 seconds, chosen as the reference point above plus headroom; and expiry of the window is a failure carrying cancel_timeout, never a clean cancellation, because reporting a hard kill as a cancel hides an adapter that cannot cancel. Research query: is there a recorded cancel-latency figure for a second, non-interactive adapter that would confirm the 10-second default is headroom on a shared floor rather than a number fit to the one substrate on file (F-a3-09)? | proposed | `F-a3-09` |
| The transport is adapter detail. The local binding of this protocol launches the agent as a subprocess and speaks JSON-RPC over its standard streams, but what the core imports is the turn, so a runtime reached another way serves the same interface unchanged. | sourced | `F-a3-03`, `X-cap-agent-runtime-006` "Control protocol \| Agent Client Protocol (ACP), JSON-RPC over stdio" |
| Consequence of design rule 6, which agentic-stack states under F-b1-07: the prompt crossing this boundary carries the task and never the criterion, so a stop reason tells a caller why the loop stopped and never whether the work was acceptable. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |
| The swap candidates for this row are a class rather than a list of products, so a caller integrates with any conformant agent; agentic-stack states design rule 4 (F-b1-05) and this row is its consequence here. | sourced | `F-b3-05`, `F-b1-05` "any ACP-speaking agent" |
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a turn through the same call. How the work arrived is not a field of the turn, so one caller-side handler covers all three. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: replacing the runtime, adding a stop reason, turning streaming on, or moving where the turn executes changes nothing in a caller that reads stop_reason, outputs and usage. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the agent's internal reasoning trace, its tool loop bookkeeping and its own model selection. A caller that reads any of them has bound itself to one runtime, and none of them is needed to know that a turn ended and why. Research query: does any recorded ACP transcript or the ACP spec text itself name a reasoning-trace or tool-loop field as part of the wire format, which would mean excluding it here is a documented protocol boundary rather than our own choice? | proposed | - |
| Which product serves the runtime and at what version. agentic-stack states that Part B output must name capabilities and standards, never products (F-part-c-09); here that means the turn shapes carry no runtime identity a caller could branch on. | sourced | `F-part-c-09` "name capabilities and standards, never products" |
| The criterion a result will be judged against, and any grading verdict. Judging is the core's, not the runtime's, and a prompt that carried the criterion would make design rule 6 unenforceable at the one boundary where the agent can read it. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability plus its standard before any agent is named: 'an agent is driven through one prompt turn, per the Agent Client Protocol, protocol version unverified'. Read this row the way the table's template row is read. | build-adapter-pair already states that the interface survives the swap and the implementation does not (F-b3-18). What this adds, as this skill's own consequence and proposed: for a runtime the statement has teeth only if the boundary is written as a turn, because a contract written as a session is a contract only a session-holding runtime can meet. | sourced | `F-b3-05`, `F-b3-18` "the adapter changes and the core does not" |
| 2 | Publish the stop-reason vocabulary as a closed enum in the turn-result shape, adopt the protocol's own reasons for the ordinary endings, and add a value only when the platform can end a turn for a reason the protocol has no cause to carry. | Proposed. A stop reason is the one field every consumer branches on, so an open set makes the branch unwriteable; and the additions must be visibly ours, because the five adopted values were taken from a design note rather than from the specification text. Research query: does the published ACP specification (once fetched, per step 4) enumerate its own stopReason values, and do they match the five this skill assumes? | proposed | `X-cap-agent-runtime-001` |
| 3 | Record the protocol version as unverified until the published specification has been read in an environment that can fetch it, as build-skill-authoring requires; the records naming a stable major version and an SDK version are search-only. | A version number nobody read is a fabrication with a decimal point in it, and every record on file for this standard is a search result rather than the specification. | sourced | `X-cap-agent-runtime-004`, `F-part-c-10` "at v1 stable with SDKs in TypeScript, Python, Rust, Java, and Kotlin" |
| 4 | Bound cancellation with a per-request grace window, keep accepting frames until the terminal frame arrives, and set the default from the observed cancel behaviour of the runtime rather than from a round number chosen in advance. | Proposed. The reference point on the substrate is a turn ending in about 8 seconds against a 45 second operation with zero trailing frames, so 10 seconds is that behaviour plus headroom; a global constant would be wrong for the next adapter, whose floor differs. Research query: is there a recorded cancel-latency measurement for the second adapter (a one-shot runtime) that would confirm 10 seconds plus headroom generalises rather than being fit to the one substrate on file? | proposed | `F-a3-09` |
| 5 | Choose the second adapter on execution model, not on brand: a single-shot runtime with no session to cancel, no stream and no callbacks, and record the axes on which the pair differs the way build-adapter-pair requires. | A second interactive agent of the same shape would leave every interactive assumption untested, whereas a runtime with none of them fails immediately on any requirement that was really adapter detail. | sourced | `F-b1-04`, `F-part-c-05` "chosen to prove the interface is not shaped around its current implementation" |
| 6 | Carry correlation into and out of every turn as an explicit member of the turn shapes, and never rely on trace parentage surviving the agent boundary. | agentic-stack already states the trace-context finding (F-a7-02). What this adds, as this skill's own consequence and proposed: this capability is that boundary, so the correlation member belongs in the turn-request and turn-result shapes here rather than being left to whatever the runtime propagates. | sourced | `F-a7-02`, `F-b4-06` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Return failures as the typed problem object cap-errors defines, and put the stop reason on that object rather than inventing a runtime-specific error shape or handing back the agent's own message text. | cap-errors already owns the failure shape (F-b4-07); what this adds, as this skill's own consequence and proposed is that a turn can fail in ways the protocol has no vocabulary for, and those must land on a registered type rather than in a stop reason invented on the spot. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 8 | Judge a candidate runtime by the cancellation criterion in this skill's definition of done, run against both adapters from the same suite, before deciding it may serve the interface. | agentic-stack and build-definition-of-done already state that a criterion nothing can fail is not a criterion (F-part-c-04). What this adds, as this skill's own consequence and proposed: every other property of a runtime degrades gracefully, but one that cannot reach a terminal frame on request cannot be bounded by any ceiling above it, so cancellation is the property worth gating on here. | sourced | `F-part-c-04`, `F-b1-04` "A criterion nothing can fail is not a criterion" |
| 9 | Send the prompt, a correlation id you chose, and nothing else unless you have a reason. Take the default grace window; take the default capability set. | It has to be simple to use, and every field you fill in is a decision you now own. The defaults are the ones the platform can change under you without breaking your call. | sourced | `T-t3-01` "It has to be simple to use." |
| 10 | Proposed: open references/agent-runtime-shapes.md when implementing or reviewing the full turn shapes, the negotiated capability set or the stop-reason table. The body of this skill is enough to judge a candidate runtime and to call the capability without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full shapes exceed the progressive-disclosure budget for a skill body, and a reader deciding whether to use the capability does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the configuration finding (F-a7-04). What it adds here, as this skill's own consequence and proposed: read back the capability set the session actually negotiated instead of trusting the set that was requested, because a runtime that silently declined streaming looks identical to one that granted it right up to the moment nothing streams. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| agentic-stack already states the green-gate finding (F-a7-03). What it adds here, as this skill's own consequence and proposed: a turn that ran to completion establishes well-formedness, not correctness, so completion is never itself the gate on a turn. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Expect a class of agents rather than one: the standard is described as doing for agents what the language server protocol did for language servers, which is the reason to keep the interface at the level of a turn instead of a runtime's own feature set. | sourced | `X-cap-agent-runtime-002` "After LSP, one language server worked everywhere. ACP does the same for AI agents." |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-goose` | today | open_session, prompt, cancel and both optional callbacks, served by an interactive agent process that the client launches and speaks the protocol to over its standard streams; PASS.md records the runtime and the control protocol as separate rows of the same sandbox. | Proposed: cannot serve a turn without a live bidirectional session, so it cannot be driven from a caller that has no process to attach to, and its cancel latency is a property of its own poll loop rather than of the interface. | Select the runtime by configuration, open a session against the same negotiated capability set, and run the cancellation conformance suite over both adapters; no core change is expected, because the core imports the turn and not the runtime. | claimed | `F-b3-05`, `F-a3-02`, `F-a3-03` "Agent Client Protocol \| goose" |
| `E-swap-candidate-any-acp-speaking-agent` | second | the same prompt turn served by a single-shot non-interactive agent that negotiates no streaming and no client callbacks: it takes a document, runs to completion or failure, and returns one terminal frame. | Proposed: cannot be cancelled mid-turn, cannot ask for tool permission, and emits no in-turn frames. Its cancel path is at best a request to abandon the run, so it reports cancel_timeout where the interactive adapter reports cancelled - which is the honest answer and the reason the pair proves anything. | Proposed: the axes that must differ are prompt_cancellation (cancellable mid-tool-call within the grace window, versus not cancellable once started) and processes_required_for_progress (a live session held open for the turn, versus one invocation that returns). Run the same parameterised suite over both, selecting by configuration with no code edit between runs. | claimed | `F-b3-05`, `F-b1-04` "any ACP-speaking agent" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/containment/test.sh |
| Expected | Proposed tool, built with the first implementation of this interface: `python3 tools/conformance_agent_runtime.py --adapter today --adapter second --op-seconds 45 --cancel-at 5 --grace 10 --report out/agent-runtime-conformance.json`. Per adapter it starts a 45 second tool call, sends cancel at t=5s, and asserts that a terminal frame arrives within cancel_grace_s, that stop_reason == "cancelled", and that frames_after_terminal == 0; across adapters it asserts adapters_run >= 2. exit 0 and one report line per adapter of the form `adapter=<role> cancel_to_terminal_s=<under 10> stop_reason=cancelled frames_after_terminal=0`, followed by `adapters_run=2`. The reference point for the interactive adapter is about 8 seconds against the 45 second operation. Until that proposed tool exists, `bash harness/containment/test.sh` (owned by cap-isolation-implement) is the running gate: every check line reads ok and the script exits 0. |
| Deliberate breakage | Raise that adapter's internal cancel poll interval above the grace window - 30 seconds against a grace of 10 - and change nothing else, then re-run. |
| Expected failure | The terminal frame arrives after cancel_grace_s, the dispatcher hard-stops the unit, and stop_reason becomes cancel_timeout instead of cancelled; the stop_reason assertion fails for that adapter, the run exits non-zero, and the report names which adapter broke while the other still reports stop_reason=cancelled. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a3-09` "ends the turn in ~8s against a 45s operation, zero trailing frames" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`

Used by: `cap-agent-runtime-implement`, `compose-agent`, `seam-dispatch`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What is the protocol's actual stop-reason vocabulary and its protocol version number? | A fetch of the published specification recording the enumerated stop reasons and the protocol version string, with the date. Every record on file for this standard is a search result; one of them reports a stable major version and five language SDKs, which is adoption evidence and not the enumeration. | Carry the five ordinary reasons as a proposed enum in the turn-result shape, keep the version unverified, and treat any consumer branch on a value outside the enum as a conformance failure until the specification is read. | `X-cap-agent-runtime-004` "at v1 stable with SDKs in TypeScript, Python, Rust, Java, and Kotlin" |
| The knowledge base has no entity for a non-interactive single-shot runtime, so which entity should the second adapter be recorded against? | 1-3-1 applied (TARGET T5): the three options were to record it against the protocol-speaking class already in the knowledge base, to mint a new entity, or to name one of the products in the swap-candidate column. Minting an entity would be inventing a record, and naming a product of the same interactive shape would give a pair that differs on no execution-model axis. Recommendation taken: record it against the class, and describe the non-interactive form in the adapter row. | The second adapter is entered as the protocol-speaking class with a row saying it negotiates no callbacks and no streaming. Revisit if a knowledge-base entity for a non-interactive runtime is ever derived from a source. | `F-b3-05`, `T-t5-02` "any ACP-speaking agent" |
| Does the interface need a remote binding, or is a local subprocess binding enough for every runtime we will drive? | A record notes that remote transports are on the roadmap beyond the local subprocess model; the deciding evidence is a specification that defines the remote binding, plus one runtime we need that cannot be launched as a local process. | Define the interface over the turn only and keep the binding out of the contract, so a remote binding arrives as an adapter rather than as a change to the shapes. | `X-cap-agent-runtime-005` "remote transports are on the roadmap to push ACP beyond the local subprocess model" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-agent-runtime 2831cb4f, 2026-09-03 |
