---
name: "cap-agent-runtime-implement"
description: "How to build the Agent runtime capability on this stack: an interactive adapter over the runtime that already runs, a second adapter that has no session at all, how to migrate execution paths that today share no contract, where the budget, policy, identity, telemetry, provenance and idempotency guarantees attach to a turn, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that starts, streams, permits or cancels an agent turn, when wiring a runtime behind the turn interface, when a ceiling above the turn needs somewhere to terminate it, when choosing what the second runtime should be, or when a cancellation test passes on one runtime and times out on another."
---

# cap-agent-runtime-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-agent-runtime into something that runs here: two runtimes behind one turn interface, the execution paths that share no contract today brought in front of it one at a time, and every cross-cutting ceiling attached around the turn rather than inside it. | sourced | `F-b5-03`, `F-b3-05`, `E-capability-agent-runtime` "Today there are three implementations and no contract between them." |

## Entities

| Entity |
|---|
| `E-capability-agent-runtime` |
| `E-standard-agent-client-protocol` |
| `E-swap-candidate-any-acp-speaking-agent` |

## Contract

### Shapes (JSON Schema 2020-12)

**AgentRuntimeAdapterBinding (proposed shape; what selects a runtime, and the only place a runtime is named)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:adapter-binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "capabilities_offered",
    "cancel_floor_s"
  ],
  "description": "Proposed. Read by the runtime factory only. Nothing in the core, and no caller, reads this object or branches on adapter.",
  "properties": {
    "adapter": {
      "type": "string",
      "description": "Adapter entity id. Selecting a runtime is configuration; there is no code path that chooses one."
    },
    "capabilities_offered": {
      "$ref": "urn:agentic:cap:agent-runtime:session-capabilities:0.1"
    },
    "cancel_floor_s": {
      "type": "number",
      "minimum": 0,
      "description": "This adapter's observed floor for reaching a terminal frame after cancel. cancel_grace_s is refused below it."
    },
    "runtime_marker": {
      "type": "string",
      "description": "Emitted by the running adapter at session open and asserted against, so a swap that never happened is visible."
    }
  }
}
```

**AgentRuntimeConformanceReport (proposed shape; the counters the definition of done below asserts on)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:agent-runtime:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "per_adapter"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 2,
      "description": "Distinct runtimes exercised. Fewer than two means the swap was not tested."
    },
    "per_adapter": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "adapter",
          "runtime_marker",
          "cancel_to_terminal_s",
          "stop_reason",
          "frames_after_terminal",
          "declared_gap_honoured"
        ],
        "properties": {
          "adapter": {
            "type": "string"
          },
          "runtime_marker": {
            "type": "string",
            "description": "Read from the running process, not from the binding record."
          },
          "cancel_to_terminal_s": {
            "type": "number",
            "minimum": 0
          },
          "stop_reason": {
            "type": "string"
          },
          "frames_after_terminal": {
            "type": "integer",
            "minimum": 0,
            "maximum": 0
          },
          "declared_gap_honoured": {
            "type": "boolean",
            "description": "True when the adapter behaved as its declared gap says it will, including when the declared behaviour is that it cannot cancel."
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: this pair's differing axes (prompt_cancellation, processes_required_for_progress) are recorded in the adapters section below and in each adapter's swap_procedure; this row does not restate them. See build-adapter-pair for why a pair agreeing on both axes is rejected. | proposed | `F-b1-04` |
| Apply build-adapter-pair: selecting the runtime is configuration, and no core code and no caller branches on which one answered - the swap test agentic-stack states as design rule 1; proposed pointer, see that skill. | proposed | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| The migration target is a contract, not a replacement: agent execution has three implementations today with nothing agreed between them, and it is the boundary that decides whether agent execution is pluggable at all, so the work is bringing those paths in front of one turn interface. | sourced | `F-b5-03` "This is the seam that decides whether agent execution is pluggable at all." |
| The runtime that runs today becomes today's adapter and is not replaced; agentic-stack states this constraint (F-part-c-11) and the consequence here is that no instruction in this skill asks anyone to swap out what is already executing agents. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| The cross-cutting guarantees are attached around the turn, never inside the runtime: the platform applies each and a caller cannot decline them, so a runtime that offers its own budget or policy option has offered an opt-out that must not be wired. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them" |
| A ceiling ends the turn and nothing above it: exceeding a budget terminates the unit, not the platform, which is only true if the runtime can be driven to a terminal frame on request - so the cancellation criterion below is what makes the budget guarantee implementable at all. | sourced | `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| Metered spend for a turn is observable outside the unit, because model egress leaves through a host broker that holds the real key and picks the endpoint; that is what lets a ceiling be enforced without the runtime cooperating. | sourced | `F-a3-07` "vsock → host broker, which holds the real key and picks the endpoint" |
| Apply build-evidence-record: every statement here about how a runtime behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test; no adapter here has been run in this repository; proposed pointer, see that skill. | proposed | `F-a5-04`, `F-part-c-08` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's adapter as a thin translation onto the runtime that already executes agents: launch it, open a session, negotiate the interactive capabilities it does support, and map its terminal frame onto the turn-result stop reason. Add nothing to the interface to accommodate it. | agentic-stack states that Part A is substrate and what runs is not to be replaced (F-part-c-11). What this adds, as this skill's own consequence and proposed: the risk on this capability is the opposite direction - not replacing the runtime but importing its feature set into the contract, where every later runtime then has to imitate it. | sourced | `F-part-c-11`, `F-b3-05` "Do not propose replacing what runs." |
| 2 | Build the second adapter from the single-shot path that already exists on this substrate - the bridge that exposes coding CLIs as chat-completions endpoints - wrapped so it answers the turn interface while negotiating no streaming and no callbacks. | The pair is then grounded in something that already runs rather than in a hypothetical batch runtime, and the single-shot path is the honest opposite of a live session: one invocation, one answer, nothing to cancel. | sourced | `F-a1-03`, `F-b1-04` "Exposes coding CLIs as chat-completions endpoints" |
| 3 | Record the pair's differs_in_execution_model naming prompt_cancellation and processes_required_for_progress, and write the second adapter's gaps down as gaps: it cannot report cancelled, cannot raise a permission request, and emits no in-turn frames. | build-adapter-pair already states that a swap needing a core change means the boundary is drawn wrong (F-meta-04). What this adds, as this skill's own consequence and proposed: widening the contract until both runtimes satisfy every member is the quiet version of that failure, so the gap is declared and the conformance run asserts on it instead. | sourced | `F-meta-04`, `F-b1-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 4 | Migrate one execution path at a time: put the turn interface in front of an existing path, keep the path running, and count paths converted. Do not attempt a cutover of all of them at once, and do not let a path that has not been converted look finished. | There are three implementations today and no contract between them, so the risk is not that a conversion fails but that a converted path and an unconverted one become indistinguishable to whoever reads the code next. | sourced | `F-b5-03` "Today there are three implementations and no contract between them." |
| 5 | Enforce both ceilings outside the unit: a monotonic wall-clock timer and the spend reservation each terminate a turn by issuing cancel and then applying the grace rules, and neither is ever handed to the runtime to enforce for itself. | A unit that enforces its own ceiling can decline to. The substrate already shows the right pattern, with scoped keys carrying hard budget caps verified to terminate spend rather than merely record it. | sourced | `F-a4-07`, `F-b4-02` "verified to terminate spend rather than merely record it" |
| 6 | Set the correlation attribute explicitly on the session and on every frame of both adapters, and assert in the conformance run that it survives each of them. | cap-agent-runtime already states that correlation crosses this boundary only as an explicit attribute (F-a7-02). What this adds, as this skill's own consequence and proposed: the single-shot adapter mints its context per invocation and has no session to hang it on, so it is the adapter where an inherited context silently becomes a fresh root. | sourced | `F-a7-02`, `F-b4-06` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Evaluate policy before the session is opened and identity before the prompt is sent, and let a refusal return the typed problem rather than an aborted turn. | Refusal is deterministic and happens before execution, not after spend, so a policy check placed after the first metered call has already spent the money it exists to protect; and every action must name an actor, including the delegated agent actor a turn creates. | sourced | `F-b4-04`, `F-b4-03` "Refusal is deterministic and happens before execution, not after spend" |
| 8 | Assert which runtime actually answered by reading a marker the running adapter emits at session open, rather than trusting the binding record that selected it. | cap-agent-runtime already states the configuration finding (F-a7-04) for the negotiated capability set. What this adds, as this skill's own consequence and proposed: at the adapter level the same failure mode produces two green conformance runs of the same runtime, which reads as a proven swap and is not one. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 9 | Apply build-definition-of-done: run the definition of done below and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: implement cancel before implementing streaming. Streaming is a comfort for whoever is watching; cancellation is the property every ceiling above the turn depends on, and it is the one the definition of done gates on. Research query: is there a recorded run or design note establishing that a cancellation gate was implemented and conformance-tested before streaming on this substrate, rather than the reverse order? | proposed | `F-b4-02` |
| Proposed: keep one grace default and store each adapter's observed cancel floor beside it in the binding, so a slow runtime shows up as a number in configuration rather than as an intermittent cancel_timeout in production. Research query: is there a recorded measurement of cancel_to_terminal_s across more than one host class that would turn the single observed floor (F-a3-09) into a distribution the default grace and per-adapter floor could be set from? | proposed | `F-a3-09` |
| agentic-stack already states that callers request a class of model, never a vendor (F-a4-01). What it adds here, as this skill's own consequence and proposed: the runtime adapter must not pin a model name of its own, or the class request is decided twice and the second decision is invisible to the caller. | sourced | `F-a4-01` "Callers request a class, never a vendor" |
| Apply build-adapter-pair: let the second adapter fail the cases it cannot serve honestly instead of emulating the first so both look alike; a declared gap the conformance run asserts on beats a silent emulation that would not survive a real cancellation. proposed pointer, see that skill. | proposed | `F-b1-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-goose` | today | open_session, prompt, cancel and both optional callbacks. Built as a translation layer over the interactive agent runtime recorded in PASS.md A3, goose v1.46.0, driven with Agent Client Protocol JSON-RPC over stdio inside the per-agent microVM; the adapter owns the launch, the session, the frame stream and the mapping of the terminal frame onto a stop reason. | Proposed: cannot serve a turn without a process it launched and holds open, so it cannot be driven from a host that has nowhere to put a long-lived child; and its cancel latency is a property of its own poll loop, which is why the binding carries a per-adapter cancel floor rather than one global constant. | Point the binding at the other adapter, offer the same capability set, and re-run the cancellation conformance suite. No core change is expected. Assert the runtime marker read from the running process, not the adapter name written in the binding. | claimed | `F-a3-02`, `F-a3-03`, `F-b3-05` "Agent Client Protocol (ACP), JSON-RPC over stdio" |
| `E-swap-candidate-any-acp-speaking-agent` | second | the same prompt turn served by a single-shot non-interactive runtime that negotiates no streaming and no client callbacks. On this substrate the shortest route to one is the existing cli-bridge path, which exposes coding CLIs as chat-completions endpoints, wrapped so one invocation produces one terminal frame. | Proposed: cannot be cancelled mid-turn, cannot raise a tool-permission request and emits no in-turn frames, so it reports cancel_timeout where the interactive adapter reports cancelled. That is its declared gap, asserted on by the conformance run rather than papered over. | Proposed: the axes that differ are prompt_cancellation and processes_required_for_progress. Select by configuration with no code edit between runs, then compare both reports against the same declared gaps. The entity recorded here is the protocol-speaking class because the knowledge base carries no entity for a non-interactive runtime; cap-agent-runtime records that choice as an open question. | claimed | `F-b3-05`, `F-b1-04`, `F-a1-03` "· any ACP-speaking agent" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/containment/test.sh && python3 harness/containment/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 16d354c: exit 0; last lines: adapters_run=2 \| conformance: pass  report=/home/user/AGENT/harness/containment/out/containment-conformance.json |
| Deliberate breakage | Raise harness/containment/binding.json's tuning.cancel_poll_interval_s to 30, above the 0.5s grace window, and change nothing else (the harness README's breakage B); restore with git checkout -- harness/containment/binding.json. |
| Expected failure | Measured by tools/measure.py at 16d354c: exit 1; last lines:   ok   typed as isolation-unavailable (503) \| passed 20, failed 5 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-a3-09` "ends the turn in ~8s against a 45s operation, zero trailing frames" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-agent-runtime`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should a runtime that never negotiated cancellation report cancel_timeout, or a distinct reason saying it was never cancellable? | Count how often a consumer of the turn result would take a different action for the two cases. If it never would, the extra reason is vocabulary nobody branches on; if a retry policy would differ, it earns a row in the stop-reason table. | Report cancel_timeout with a problem whose detail names the negotiated capability set, so the distinction is readable without widening the enum before anyone needs it. | `F-b4-07` "Never parsed from prose" |
| Where is each adapter's cancel floor measured, and does it hold across hosts? | Run the cancellation criterion repeatedly on each host class and record the distribution of cancel_to_terminal_s, not one figure. The reference point on file is a single observation recorded with status claimed, so it is a starting value rather than a floor. | Carry one grace default of 10 seconds and a per-adapter floor in the binding, and refuse a cancel_grace_s below the recorded floor. | `F-a3-09` "`session/cancel` mid-tool-call ends the turn" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-agent-runtime 2831cb4f, 2026-09-03 |
