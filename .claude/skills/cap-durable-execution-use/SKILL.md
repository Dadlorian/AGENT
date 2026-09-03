---
name: cap-durable-execution-use
description: How to run a multi-step piece of work that survives a crash: the two things you supply, the one thing you read, two worked runs, what a failure looks like, and why you never write the resume logic yourself. Load it when a human, an agent or an event needs several steps done as one piece of work, when a job is long enough that a restart in the middle is realistic, when you are about to write your own retry loop, checkpoint table or 'did I already do this' flag, or when you are deciding what to do with a run that came back saying it continued from step 11.
---

# cap-durable-execution-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make a multi-step run callable with a key and a list of steps, and readable as one outcome: call it again after a crash and it continues where it stopped. Everything about checkpoints and resumption is hidden behind the call, because composability hides the complexity. | sourced | `T-t2-01`, `T-t3-01`, `E-capability-durable-execution` "Composability hides the complexity." |

## Entities

| Entity |
|---|
| `E-capability-durable-execution` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| run (proposed) | your run key and the steps to execute, in order; everything else has a default | one run result: the outcome, what each step produced, and how many steps were replayed rather than re-executed. Calling it again with the same key continues the same run instead of starting a second one (proposed) | proposed | `T-t3-01` |
| read (proposed) | a run key | the run's outcome and its step results. A failure arrives as a typed problem rather than as a status string to interpret, and there is no separate call to find out where it got to (proposed) | proposed | `F-b4-07` |

### Shapes (JSON Schema 2020-12)

**Worked run 1 (proposed): a human submits twenty steps and they all complete** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:example:completed",
  "title": "One run, no crash",
  "description": "Sent: a key and the steps. Returned: an outcome. steps_replayed is 0 because nothing was interrupted; you did not write a checkpoint, a retry or a resume.",
  "examples": [
    {
      "sent": {
        "run_key": "human-checkout-500s-2026-09-03",
        "steps": [
          "triage",
          "repro",
          "fix",
          "regression"
        ]
      },
      "returned": {
        "outcome": "completed",
        "steps_committed": 4,
        "steps_replayed": 0,
        "results": {
          "triage": "sha256:0c7ac1\u2026",
          "repro": "sha256:4c0dc2\u2026",
          "fix": "sha256:06db78\u2026",
          "regression": "sha256:8e42c8\u2026"
        }
      }
    }
  ]
}
```

**Worked run 2 (proposed): the machine died mid-run and an event called the same key again** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:example:resumed",
  "title": "The same call, after a crash",
  "description": "The caller sent the identical request. Two steps were already committed, so they were replayed rather than re-executed and their side effects did not happen twice. The only new field to read is steps_replayed.",
  "examples": [
    {
      "sent": {
        "run_key": "human-checkout-500s-2026-09-03",
        "steps": [
          "triage",
          "repro",
          "fix",
          "regression"
        ]
      },
      "returned": {
        "outcome": "completed",
        "steps_committed": 4,
        "steps_replayed": 2,
        "results": {
          "triage": "sha256:0c7ac1\u2026",
          "repro": "sha256:4c0dc2\u2026",
          "fix": "sha256:06db78\u2026",
          "regression": "sha256:8e42c8\u2026"
        }
      }
    }
  ]
}
```

**What a failure looks like (proposed): problem details, not prose** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:durable-execution:example:unresumable",
  "title": "The run exists and cannot be continued",
  "$ref": "urn:agentic:problem:0.1",
  "description": "A run that cannot be resumed is a failure with a type. It is never quietly restarted from the first step. Branch on type; read detail only to report it. `urn:agentic:problem:durable-run-unresumable` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `idempotency-conflict`, which is also 409 and not retryable, with the run key and the last committed step in detail.",
  "examples": [
    {
      "type": "urn:agentic:problem:durable-run-unresumable",
      "title": "Run cannot be resumed",
      "status": 409,
      "detail": "step records for run_key human-checkout-500s-2026-09-03 end at step 11 with no committed effect record; continuing would repeat a side effect",
      "retryable": false,
      "correlation_id": "corr-human-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a run through the same call with the same two fields. Which one started it is not a field of the run, so a crash and a restart are handled identically whichever way the work arrived. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Proposed: two fields go in and one outcome comes back. There is no separate resume call, no checkpoint you write, no step table you own, and no place to ask which executor is running; calling with the same key is both 'start' and 'continue'. | proposed | `T-t3-01`, `T-t2-01` |
| Enhancing one aspect leaves the rest untouched: changing the executor, moving where checkpoints are stored, or adding steps to the sequence changes nothing in a caller that sends a key and reads an outcome. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Budget, policy, identity, telemetry and provenance are applied around every step and around every restart, whichever entry point started the work, and there is no field for asking for them or declining them. A resumed run continues under the ceiling it had left. | sourced | `T-t2-03`, `F-b4-01` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| Proposed: a failure arrives as the typed problem object cap-errors defines and cap-durable-execution requires this boundary to return. Branch on its type; a run that cannot be continued is never silently begun again, so 'it started over' is not an outcome you have to detect yourself. | proposed | `F-b4-07` |
| Proposed: the run key is yours and it is the whole of your replay safety. The same key means the same run; a different key means a second run that will do the work again, whatever the first one already did. | proposed | `F-b4-08` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Send a run key you can reproduce and the steps in order. Take every default. Do not send a resume flag, an attempt number or a starting index - there is no field for them and you would not want to own the decision. | It has to be simple to use, and every field you fill in is a decision you now own; the resume point is derived from what is already committed, which is a fact the platform has and you do not. | sourced | `T-t3-01` "It has to be simple to use." |
| 2 | Derive the run key from the work itself - the request that arrived, the day, the subject - never from the clock at call time or a fresh random value. | cap-durable-execution states that the key is what makes a replay safe (F-b4-08). What this adds for a caller: a key you cannot reproduce turns your retry into a second run, and you will only find out when the side effect has happened twice. | sourced | `F-b4-08` "safe to replay" |
| 3 | After any interruption, make the identical call again with the same key. Do not write a loop that inspects which steps finished, and do not skip steps by hand. | Proposed. Continuing is the same call, so the retry you would have written is one line; a caller that reconstructs the resume point is reimplementing the capability and will disagree with it the first time a step half-finished. | proposed | `T-t2-01` |
| 4 | Read the outcome, and read steps_replayed only when you want to know whether an interruption happened. Do not branch on which executor answered or on how durability was achieved. | Proposed. Those are the fields that would break on the next configuration change; the outcome and the step results are the ones that will not. | proposed | `T-t2-02` |
| 5 | Read a failure as a problem object: branch on type, use retryable as given, and never parse the words. Treat 'cannot be resumed' as a stop, not as an invitation to start again with a new key. | cap-durable-execution requires this boundary to return the typed problem object that cap-errors defines (F-b4-07); what this adds for a caller is that a new key would be a new run, so the one recovery that feels natural here is the one that repeats every side effect the first run already committed. | sourced | `F-b4-07` "Never parsed from prose" |
| 6 | Compose upward, not inward: a durable run is one step of something larger. Approvals in the middle, several runs in sequence, a loop over runs and a whole workflow are built above this call rather than by adding fields to it. | Any entry can call complex workflows, agents and loops that run across the entire stack, so the complexity belongs to the composition and this call stays the same size however large the thing above it gets. | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| 7 | If this page starts to feel like something you must study before calling, stop and cut it rather than adding to it: the caller-facing surface is a key, a list of steps, and an outcome. | It cannot be daunting or overly complex, or no one will use it - which makes size a property of the interface to defend, not a documentation problem to solve later. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Make each step do one thing that is worth not repeating. A step that bundles four side effects can only be resumed before or after all four, so the size of your steps is the granularity of your crash recovery. | sourced | `X-cap-durable-execution-001` "journals every step so an agent can resume from exactly where it stopped" |
| Reuse one correlation id across the whole run, including the calls made after an interruption, so the run before the crash and the run after it are one thing in the record rather than two. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| Proposed: keep what a partial run already produced. Steps committed before an interruption are results, not debris, and discarding them in the caller throws away work the platform already made durable and already charged you for. | proposed | `T-t2-01` |
| cap-durable-execution already states that a resume check which never crashed proves nothing (F-a7-03). What it adds for a caller: a run that returns steps_replayed 0 has told you nothing about whether resumption works, so do not treat a clean run as evidence that your keys are right. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/render_skill.py .claude/skills/cap-durable-execution-use && python3 tools/validate_skills.py --only cap-durable-execution-use`. This skill has no Adapters section, so the validator's product-purity check covers the whole page: it proves that nothing a caller reads here - the two operations, the worked runs, the failure - names the executor that keeps the run durable, which is the promise this facet makes. |
| Expected | `rendered cap-durable-execution-use/SKILL.md` then `cap-durable-execution-use: 0 errors, 0 warnings`, exit 0. |
| Deliberate breakage | In the second worked run, replace the value of one result digest with the name of the workflow orchestrator PASS.md B3 names in the Durable execution adapter column, re-render, and re-run the validator. |
| Expected failure | exit 1 with `cap-durable-execution-use: product name(s) ['<the B3 orchestrator name>'] outside Adapters, in section 'Contract'` and a closing `cap-durable-execution-use: 1 errors, 0 warnings`. Measured in session cap-durable-execution 2831cb4f on 2026-09-03: the breakage produced exactly that line with the orchestrator's name in the list, and exit 1; restoring the file returned 0 errors, 0 warnings and exit 0. |
| Status | measured |
| Evidence | `F-part-c-09`, `T-t2-01` "Products belong in the adapter column only" |

## Composes with

Builds on: `cap-durable-execution`, `cap-durable-execution-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should a caller ever be able to ask for a run to start again from the beginning under the same key? | Count the cases where someone genuinely wants the committed steps re-executed rather than a new run under a new key. If every case turns out to be 'the inputs changed', then it is a different run and a different key already covers it. | No restart flag. A new run needs a new key, which keeps the key the whole of the caller's replay safety and keeps this call at two fields. | `T-t3-02` "It cannot be daunting or overly complex" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-durable-execution 2831cb4f, 2026-09-03 |
