---
name: compose-loop
description: A bounded loop assembled from lower layers: a body that runs, a verdict that decides, and two ceilings that end it. Load it when work has to be attempted more than once - fix-and-check, evaluator-optimizer, a self-improvement cycle - when writing a loop's exit condition, when deciding what an iteration may see of the criterion it is graded against, when a nested loop's cost or depth has to be known before it starts, when an iteration has to survive a crash, and when someone asks what stops this running forever, why did this stop, who pays for iteration nine, whether a running step may start a loop of its own, or how a run that ended for a fourth reason should be classified.
---

# compose-loop

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed: compose a graded verdict, a declared iteration ceiling and a budget ceiling into one bounded iteration, so that every loop terminates for exactly one of three nameable reasons and can be priced before it starts. | proposed | `F-b2-05`, `F-b4-02`, `F-b1-06`, `REF-12-14` |

## Entities

| Entity |
|---|
| `E-core-component-judge` |
| `E-core-component-planner` |
| `E-concern-budget` |
| `E-rule-b1-5` |
| `E-rule-b1-6` |
| `E-capability-durable-execution` |
| `E-seam-dispatch` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| resolve_loop (proposed operation set; a composition introduces no new interface, so these are assembly points over interfaces the lower layers already publish) | a loop declaration - the body, criterion_ref, max_iterations, the budget slice - plus the depth already consumed by the plan above it (proposed) | a priced plan whose worst case is max_iterations times the body's cost and whose floor is one iteration, or a refusal issued before anything executes when the depth bound or the remaining ceiling would be crossed (proposed) | proposed | `F-b1-06`, `REF-5-2-13` |
| run_iteration (proposed) | the iteration index, the body's dispatch, that iteration's budget slice, and the checkpoint committed by the previous index (proposed) | the body's result and a checkpoint committed for this index, so a restart resumes at the first incomplete iteration instead of replaying committed work (proposed) | proposed | `F-b4-08`, `F-b3-04` |
| evaluate_exit (proposed) | the iteration's result and the opaque criterion_ref the loop declaration carries (proposed) | a verdict of pass or fail, computed outside the body by the grading contract core-judge owns; the body is re-entered with the verdict and the failed check ids and never with the criterion (proposed) | proposed | `F-b2-05`, `F-b1-07` |
| close_loop (proposed) | the last verdict, the iteration counter and what remains of the ceiling (proposed) | one loop-outcome naming exactly one of verdict_pass, iteration_ceiling or budget_ceiling, classed as a stop that returns a result or a cap that escalates to a human with a typed problem object (proposed) | proposed | `REF-5-3-08`, `F-b4-07` |

### Shapes (JSON Schema 2020-12)

**loop-spec (proposed summary shape, field names kept identical to the loop operator in examples/end-to-end; the full schema, the three worked declarations and the worked rejections are in references/usage.md)** (proposed; sources: `F-b1-06`, `F-b4-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:loop:spec:0.1",
  "title": "LoopSpec",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. Bounded repetition: it ends on the exit condition, on max_iterations, or on the budget ceiling, and there is no unbounded variant to declare.",
  "required": [
    "op",
    "id",
    "max_iterations",
    "exit_when",
    "body",
    "on_cap"
  ],
  "properties": {
    "op": {
      "const": "loop"
    },
    "id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]{1,47}$"
    },
    "max_iterations": {
      "type": "integer",
      "minimum": 1,
      "maximum": 25,
      "description": "Required, so the worst case is priceable before the first iteration runs."
    },
    "exit_when": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "judge_step",
        "verdict"
      ],
      "properties": {
        "judge_step": {
          "type": "string"
        },
        "verdict": {
          "enum": [
            "pass",
            "fail"
          ]
        }
      }
    },
    "body": {
      "type": "object",
      "description": "One step of the closed operator set; the criterion behind judge_step is not part of it."
    },
    "on_cap": {
      "const": "escalate",
      "description": "A cap termination is a failure that goes to a human. There is no value here that means carry on."
    },
    "per_iteration_ceiling_micros": {
      "type": "integer",
      "minimum": 0,
      "description": "The slice each iteration may draw from the root ceiling xc-budget holds."
    },
    "max_depth": {
      "type": "integer",
      "minimum": 1,
      "description": "Nesting bound checked when the plan resolves, not when the loop runs."
    }
  }
}
```

**loop-outcome (proposed shape; this is what a caller and the ledger read, and it is what the definition of done asserts over)** (proposed; sources: `REF-5-3-08`, `F-b2-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:loop:outcome:0.1",
  "title": "LoopOutcome",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. terminated_by is an enum of exactly three members: a fourth reason has nowhere to be written, which is how a defect becomes visible rather than plausible.",
  "required": [
    "loop_id",
    "terminated_by",
    "termination_class",
    "iterations_run",
    "cost_micros"
  ],
  "properties": {
    "loop_id": {
      "type": "string"
    },
    "terminated_by": {
      "enum": [
        "verdict_pass",
        "iteration_ceiling",
        "budget_ceiling"
      ]
    },
    "termination_class": {
      "enum": [
        "stop",
        "cap"
      ],
      "description": "stop means done and returns the result; cap means escalate and carries a problem object."
    },
    "iterations_run": {
      "type": "integer",
      "minimum": 1
    },
    "cost_micros": {
      "type": "integer",
      "minimum": 0,
      "description": "The sum of the iterations and their descendants, reconciled against the plan rather than re-estimated."
    },
    "last_verdict": {
      "type": "object",
      "description": "The verdict shape core-judge owns: verdict, failed check ids, detail."
    },
    "escalation": {
      "type": "object",
      "description": "Present when termination_class is cap: the problem object handed to the human."
    }
  }
}
```

**cap escalation (proposed worked instance; the suffix below is proposed and pending registration in the closed registry, and the registered fallback named in this skill's open question is returned meanwhile)** (proposed; sources: `F-b4-07`, `REF-5-3-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:loop:cap-instance:0.1",
  "title": "LoopCapInstance",
  "description": "Proposed. What a cap termination hands back, shown rather than described. The type suffix iteration-ceiling-reached has no row in the closed registry yet: it is proposed and pending registration, and until the row lands the platform returns the registered fallback this skill's open question names.",
  "examples": [
    {
      "type": "urn:agentic:problem:iteration-ceiling-reached",
      "title": "Iteration ceiling reached without a pass verdict",
      "status": 504,
      "detail": "loop fix-loop ran 3 of 3 iterations on run-human-0001; last verdict fail on checks patch-applies, test-passes",
      "retryable": false,
      "correlation": {
        "run_id": "run-human-0001",
        "correlation_id": "corr-human-0001",
        "depth": 0
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: a loop terminates on exactly one of three conditions - a verdict of pass, the declared iteration ceiling, or the budget ceiling - and the outcome names which one. core-judge owns the verdict (F-b2-05) and xc-budget owns the ceiling (F-b4-02); what this composition adds is that those three are the whole set, so a run that ends for a fourth reason, or does not end at all, is a defect rather than a variation. | proposed | `F-b2-05`, `F-b4-02`, `REF-12-14` |
| Proposed, following the reference example: stop and cap are opposites and must not be collapsed into one halt. A pass verdict is a stop and ends the loop as success with a result; the iteration ceiling is a cap and ends it as a failure that escalates to a human. Collapsing them hides from everyone downstream which of the two happened. | proposed | `REF-5-3-08`, `REF-5-3-03`, `REF-5-3-04` "`stop` firing means done. `cap` firing means escalate." |
| Proposed: xc-budget states the ceiling contract (F-b4-02); what a loop adds is that each iteration draws a slice of one root ceiling and the loop's cost is the sum of its iterations and their descendants, reconciled against the plan. A loop that reports a top-level estimate of its own is guessing the moment anything inside it nests. | proposed | `F-b4-02`, `REF-5-2-12` "A parent estimate that is its own guess rather than the sum of its children is fiction the moment anything nests." |
| Proposed, following the reference example: nesting is bounded and the bound is checked when the plan resolves, not while it runs, so a loop whose body would nest past the limit is refused before any iteration executes and before any money is spent. | proposed | `REF-5-2-13`, `REF-5-3-05` "A sub-plan that would nest past the limit is refused before anything executes." |
| agentic-stack states design rule 5 as a test (F-b1-06, F-b2-03). Its consequence here: the declared iteration ceiling is what makes a loop priceable at all, since the worst case is the ceiling times the body and the floor is one iteration. A loop with no ceiling cannot be planned, so it is refused at resolve rather than started and watched. | sourced | `F-b1-06`, `F-b2-03` "Planning is a pure function and completes before execution begins" |
| core-judge owns the grading contract and agentic-stack states it as design rule 6 (F-b1-07). What a loop adds: the exit condition is evaluated outside the body, and the body is re-entered with the verdict and the failed check ids only. A loop that feeds the criterion back as guidance for the next attempt breaks the rule once per iteration, which is the most expensive way to break it. | sourced | `F-b1-07`, `F-b2-05` "An agent sees its outcome, never the criterion it is judged against" |
| Proposed: one iteration is one durable step. The checkpoint and the iteration's effect commit together under a key of the loop id and the iteration index, so a restart resumes at the first incomplete iteration instead of replaying committed work or double-spending it. cap-durable-execution owns step, checkpoint and resume point (F-b3-04); this composition only fixes what one step is. | proposed | `F-b4-08`, `F-b3-04` |
| Proposed, following the reference example and consistent with cap-consumption: an internal event steers a loop and never starts one. A running iteration may report a result into work that already exists; it may not mint a new root loop, because a loop that starts itself has no ceiling to spend against and no actor to attribute to. | proposed | `REF-3-4-15`, `REF-3-4-10`, `T-t4-04` "A loop that can mint its own root work has no provenance and no ceiling." |
| Proposed: a composition introduces no new interface. The loop reaches dispatch, grading, checkpointing and the ceiling through capability interfaces only, as agentic-stack requires of the core (F-b1-02), so the same declaration runs on a second executor with no edit to the loop. | proposed | `F-b1-02`, `F-b1-04` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion behind criterion_ref, the checks sampled for a grading and the criterion-set digest never enter the body or anything the body can read; core-judge owns the resolution path and agentic-stack states the rule. The body reads a verdict and failed check ids, which are labels the declaration already carried. | sourced | `F-b1-07` "The grader is never visible to the graded." |
| Proposed: the loop's own control state - how many iterations remain, how much of the ceiling is left, which termination class is pending - is not readable by the body either. A body that can see the counter optimises against the counter, which is design rule 6 broken through a side door. | proposed | `F-b1-07` |
| Proposed: no loop declaration names the engine that runs it. Which executor advances the iterations is configuration, so swapping it is not a change a caller writes. | proposed | `T-t2-02`, `F-b1-02` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Declare the loop before running it: the body, an opaque criterion_ref, max_iterations, the per-iteration slice, the root ceiling and on_cap. Resolve it to a priced plan - floor of one iteration, worst case of max_iterations - and refuse at resolve if the floor already crosses what remains. | Cost is knowable before commitment only because the ceiling is declared: it is the ceiling that turns an open-ended attempt into an arithmetic worst case. | sourced | `F-b1-06`, `F-b2-03` "Cost is knowable before commitment." |
| 2 | Evaluate the exit condition outside the body: hand the iteration's result and the criterion_ref to the grading contract core-judge owns, and pass back into the next iteration only the verdict and the failed check ids. | The loop is the place design rule 6 is most easily lost, because the obvious way to make the next attempt better is to show it the criterion. | sourced | `F-b1-07`, `F-b2-05` ""done" becomes an opinion" |
| 3 | Proposed: give each iteration a slice of one root ceiling rather than a ceiling of its own, sum the iterations and their descendants into the loop's cost, and reconcile that sum against the plan when the loop closes. | A nested plan lies about cost unless costs sum upward, and a loop is the cheapest place to nest by accident: three iterations of a fanned-out body is a tree, not a line. | proposed | `REF-5-2-12`, `F-b4-02` |
| 4 | Proposed: check the depth bound when the plan resolves. If the body contains a sub-plan or another loop that would nest past max_depth, refuse there, with the depth that would have been reached, rather than discovering it at iteration two. | Unbounded nesting is a hazard others have already met, and a refusal at resolve costs nothing while a refusal at run time has already spent money and left partial work. | proposed | `REF-5-2-13`, `REF-5-3-05` |
| 5 | Commit one checkpoint per iteration, keyed by the loop id and the iteration index, together with that iteration's effect; on restart read the resume point and continue at the first incomplete index. | Every externally-triggered action is safe to replay only if the replay knows what already happened; a loop that checkpoints once at the end replays its whole body after a crash and pays twice. | sourced | `F-b4-08`, `F-b3-04` "Every externally-triggered action is safe to replay" |
| 6 | Proposed: write the two ceilings as different outcomes - a pass verdict closes the loop as a stop with the result; the iteration ceiling closes it as a cap with on_cap escalate and a problem object for a human; the budget ceiling closes it as a cap with the registered budget refusal. | Merging stop and cap into one halt is a mistake the reference records as already made once: everything downstream then has to guess whether the work is done or abandoned. | proposed | `REF-5-3-08`, `REF-5-3-04` |
| 7 | Emit one loop-outcome per run naming terminated_by, termination_class, iterations_run and cost_micros, and assert over a population of runs that the reason is always one of the three and that unbounded is zero. | build-definition-of-done owns this discipline (F-part-c-04): a criterion nothing can fail is not a criterion. The enum plus the counter is what makes a fourth exit path a test failure here instead of an anecdote in a log. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion." |
| 8 | Proposed: let internal results steer a running loop - a verdict, a partial result, a revised input - but never let one start a loop. A new root loop is admitted only from a person, a clock, or an outside event, through the same entry envelope. | Every unit of work has to trace back to an actor and a ceiling; a self-started loop has neither, and this is the constraint a self-improvement loop in particular has to live inside. | proposed | `REF-3-4-15`, `T-t4-04`, `T-t6-02` |
| 9 | Reach the loop the way any capability is reached, per cap-consumption: one entry envelope, whichever of the four entries you are, with the loop named in the workflow the intent points at. Do not add a per-entry loop path, and do not branch on which executor answered. | Any entry can call complex workflows, agents and loops that run across the entire stack, so size belongs to the composition and not to the call. | sourced | `T-t6-03`, `T-t6-02` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| 10 | Proposed: open references/usage.md for the full loop-spec schema, a worked declaration for each of the three ways in, and the two worked rejections. The body of this skill is enough to write a conformant loop without it. | Proposed: the long material would push the reader past the point where the rule itself is visible; the reference file is where it belongs. | proposed | `T-t3-01` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: test the loop with a body that never passes, not with one that passes on the second attempt. The happy path exercises the verdict; only a permanently failing body exercises the ceiling, which is the part that keeps a loop from running forever. | proposed | `F-part-c-04` |
| Proposed: treat the ceiling as enforcement, not as advice in the body's instructions. The records on file describe an agent running in an unintended loop for 264 hours and conclude that enforcement belongs outside the prompt; they are search results rather than pages that were read, so take the shape and not a measurement from them. | proposed | `X-build-simplicity-budget-003`, `X-end-to-end-063` "Enforcement must live outside the agent's prompt; real enforcement is code, not prose." |
| Proposed: bound what each iteration carries forward as well as how many iterations there are. The records on file name history growth as the reason long-running loops have to be restarted deliberately in workflow engines, so carry a digest and a bounded window rather than the whole transcript. | proposed | `X-compose-loop-002`, `X-cap-state-persistence-006` "to avoid running into the history scalability issue when workflows involve long-running loops" |
| Proposed: a loop that terminated is not a loop that succeeded. Report the termination class, never a bare completion, so a cap that escalated is not counted as green by whatever reads the run afterwards - the same trap as a gate that is structurally green, which agentic-stack states as the well-formedness finding (F-a7-03). | proposed | `F-a7-03`, `REF-5-3-08` |
| Proposed: unlimited retries are not a reliability strategy, and neither is a very large ceiling. Pick max_iterations from what the body can plausibly improve in one attempt, and let the cap escalate rather than raising the number until the failures stop being visible. | proposed | `X-compose-loop-003` "unlimited retries are not a reliability strategy" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Run the loop conformance suite over 100 runs, mixing bodies that pass at the first attempt, bodies that never pass, and bodies that exhaust the ceiling mid-iteration: `python3 tools/loop_conformance.py --runs 100`. Assert that every run emits one loop-outcome whose terminated_by is one of verdict_pass, iteration_ceiling or budget_ceiling, that runs_checked == 100, that unbounded == 0, and that every cap termination carries an escalation problem object while every stop carries a result. |
| Expected | loop-conformance: runs_checked=100, verdict_pass=34, iteration_ceiling=33, budget_ceiling=33, unbounded=0, fourth_reason=0, escalations=66; exit 0 |
| Deliberate breakage | Remove the iteration ceiling from the loop declaration - delete max_iterations and the check that reads it - and run the never-passing body against a large budget. |
| Expected failure | The run never terminates and the suite stops it: `TIMEOUT after 600s: run 7 reached iteration 412 with no termination`, with unbounded=1 and runs_checked=6 while verdict_pass and budget_ceiling stay green on the runs that did finish. Status claimed: tools/loop_conformance.py does not exist in this repository yet, so neither run has been executed. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-evidence-record`, `core-judge`, `xc-budget`

Used by: `compose-agent`, `compose-improvement-loop`, `compose-loop-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What problem type does a cap termination return? The closed registry in docs/decomposition.md section 2.1.6 has no row for an iteration ceiling reached without a pass verdict. The row proposed here is `iteration-ceiling-reached`, status 504, retryable no, raised when the declared iteration ceiling is reached and the verdict is still fail; it is marked proposed and pending registration wherever this skill states it. | A registry row added in section 2.1.6, which is where the closed set lives and where the validator reads it from. cap-errors owns the failure object and core-judge and xc-budget state the same rule for their own boundaries (F-b4-07); until the row lands the nearest registered row is deadline-exceeded, whose retryable value is yes - which tells a caller to retry a loop that ended because it ran out of attempts, and that cost is the argument for the row. | Return the registered `urn:agentic:problem:deadline-exceeded` with the loop-outcome attached, so no caller branches on a URI that cannot legally come back, and record the substitution in the outcome's escalation member. | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| Should compose-loop build on the durable-execution capability? Its contract fixes one iteration as one durable step, but docs/skill-manifest.json lists neither cap-durable-execution nor cap-state-persistence under this skill's builds_on, so the checkpoint obligation is stated here with no link to the skill that owns it. Reported, not edited: composes_with equals the manifest exactly. | A manifest revision adding the link, or a decision that a composition may name a capability it does not build on. The same question applies to compose-approval, whose parking is durable in the same way. | Name cap-durable-execution and its kb ids (F-b3-04, F-b4-08) in the rows that need it, and leave builds_on as the manifest has it. | `F-b3-04` |
| Is the reference example's marginal-gain stop - terminate as success when returns flatten over a window - a fourth termination condition, or a criterion the verdict already covers? | A run where marginal gain flattens while the criterion still fails. If the right answer there is to stop as success, the three-condition rule is wrong; if it is to keep going to the cap, marginal gain is an input to the criterion and not a termination. | Treat it as a criterion the grader evaluates, so the outcome enum stays at three members and a flattening loop terminates on a pass verdict or on its ceiling. | `REF-5-3-03`, `REF-5-3-08` "\| `stop: {marginal_gain_below, window}` \| the step \| returns flatten \| **terminates as success** \|" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation compose-loop 2026-09-03 |
