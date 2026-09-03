# cap-durable-execution: the caller's view

Proposed. Folded in from the former `cap-durable-execution-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-durable-execution` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 5 row(s) of that kind were dropped in the fold: ambient-guarantees, compose-upward, problem-details, size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make a multi-step run callable with a key and a list of steps, and readable as one outcome: call it again after a crash and it continues where it stopped. Everything about checkpoints and resumption is hidden behind the call, because composability hides the complexity.  
  _sourced_ - `T-t2-01`, `T-t3-01`, `E-capability-durable-execution` "Composability hides the complexity."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| run (proposed) | your run key and the steps to execute, in order; everything else has a default | one run result: the outcome, what each step produced, and how many steps were replayed rather than re-executed. Calling it again with the same key continues the same run instead of starting a second one (proposed) | proposed | `T-t3-01` |
| read (proposed) | a run key | the run's outcome and its step results. A failure arrives as a typed problem rather than as a status string to interpret, and there is no separate call to find out where it got to (proposed) | proposed | `F-b4-07` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-durable-execution` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked run 1 (proposed): a human submits twenty steps and they all complete

_proposed_ - sources: -.

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
          "triage": "sha256:0c7ac1…",
          "repro": "sha256:4c0dc2…",
          "fix": "sha256:06db78…",
          "regression": "sha256:8e42c8…"
        }
      }
    }
  ]
}
```

### Worked run 2 (proposed): the machine died mid-run and an event called the same key again

_proposed_ - sources: -.

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
          "triage": "sha256:0c7ac1…",
          "repro": "sha256:4c0dc2…",
          "fix": "sha256:06db78…",
          "regression": "sha256:8e42c8…"
        }
      }
    }
  ]
}
```

### What a failure looks like (proposed): problem details, not prose

_proposed_ - sources: -.  Also carried in the body of `cap-durable-execution` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-durable-execution` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Derive the run key from the work itself - the request that arrived, the day, the subject - never from the clock at call time or a fresh random value.**  
  _why:_ cap-durable-execution states that the key is what makes a replay safe (F-b4-08). What this adds for a caller: a key you cannot reproduce turns your retry into a second run, and you will only find out when the side effect has happened twice.  
  _sourced_ - `F-b4-08` "safe to replay"
- **After any interruption, make the identical call again with the same key. Do not write a loop that inspects which steps finished, and do not skip steps by hand.**  
  _why:_ Proposed. Continuing is the same call, so the retry you would have written is one line; a caller that reconstructs the resume point is reimplementing the capability and will disagree with it the first time a step half-finished.  
  _proposed_ - `T-t2-01`
- **Read the outcome, and read steps_replayed only when you want to know whether an interruption happened. Do not branch on which executor answered or on how durability was achieved.**  
  _why:_ Proposed. Those are the fields that would break on the next configuration change; the outcome and the step results are the ones that will not.  
  _proposed_ - `T-t2-02`

## Other caller invariants

- Proposed: two fields go in and one outcome comes back. There is no separate resume call, no checkpoint you write, no step table you own, and no place to ask which executor is running; calling with the same key is both 'start' and 'continue'.  
  _proposed_ - `T-t3-01`, `T-t2-01`
- Proposed: the run key is yours and it is the whole of your replay safety. The same key means the same run; a different key means a second run that will do the work again, whatever the first one already did.  
  _proposed_ - `F-b4-08`

## Caller practices

- Make each step do one thing that is worth not repeating. A step that bundles four side effects can only be resumed before or after all four, so the size of your steps is the granularity of your crash recovery.  
  _sourced_ - `X-cap-durable-execution-001` "journals every step so an agent can resume from exactly where it stopped"
- Reuse one correlation id across the whole run, including the calls made after an interruption, so the run before the crash and the run after it are one thing in the record rather than two.  
  _sourced_ - `T-t2-03` "managed across the entire structure, whichever entry point was used"
- Proposed: keep what a partial run already produced. Steps committed before an interruption are results, not debris, and discarding them in the caller throws away work the platform already made durable and already charged you for.  
  _proposed_ - `T-t2-01`
- cap-durable-execution already states that a resume check which never crashed proves nothing (F-a7-03). What it adds for a caller: a run that returns steps_replayed 0 has told you nothing about whether resumption works, so do not treat a clean run as evidence that your keys are right.  
  _sourced_ - `F-a7-03` "Those establish well-formedness, not correctness"

## Open questions carried over

- **Should a caller ever be able to ask for a run to start again from the beginning under the same key?**  
  _deciding evidence:_ Count the cases where someone genuinely wants the committed steps re-executed rather than a new run under a new key. If every case turns out to be 'the inputs changed', then it is a different run and a different key already covers it.  
  _default until then:_ No restart flag. A new run needs a new key, which keeps the key the whole of the caller's replay safety and keeps this call at two fields.  
  `T-t3-02` "It cannot be daunting or overly complex"

