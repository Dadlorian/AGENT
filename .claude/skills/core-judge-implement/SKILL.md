---
name: core-judge-implement
description: How to build the Judge on this stack: a verdict function that links no model client and no store, a criterion store the graded unit cannot reach, a derived-seed sampler and a held-out audit, two grading engines behind one binding - a deterministic check gate and a model-graded rubric judge - the migration off the gate that decides done today, where the cross-cutting concerns attach, and the conformance run that decides whether either engine may serve. Load it when writing or reviewing that code, when a grading is about to call a model, when a criterion file is about to be mounted somewhere convenient, and when someone asks 'where does the verdict actually come from', 'can we change the grader without touching the core', or 'why did the same result get two different verdicts on two runs'.
---

# core-judge-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what core-judge's contract specifies (F-b2-05): one pure verdict function, one out-of-band criterion store, a deterministic sampler, two grading engines selected by configuration, and a run that shows the verdict survives the swap and the criterion never leaves. | sourced | `F-b2-05`, `F-b1-04` "pure function `(result, criterion) → verdict`" |

## Entities

| Entity |
|---|
| `E-core-component-judge` |
| `E-rule-b1-6` |
| `E-finding-a7-2` |
| `E-capability-model-access` |
| `E-seam-dispatch` |
| `E-concern-budget` |

## Contract

### Shapes (JSON Schema 2020-12)

**judge-engine-binding (proposed shape; the wiring table, the determinism configuration and the migration procedure are in references/implementation-notes.md)** (proposed; sources: `F-meta-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:judge:engine-binding:0.1",
  "title": "Judge engine binding",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "check_kinds_served",
    "determinism",
    "differs_in_execution_model"
  ],
  "properties": {
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "check_kinds_served": {
      "type": "array",
      "minItems": 1,
      "description": "The check kinds this engine can decide. A binding that claims to serve a kind it cannot decide is what makes a pass meaningless."
    },
    "determinism": {
      "type": "object",
      "required": [
        "guaranteed_by"
      ],
      "properties": {
        "guaranteed_by": {
          "enum": [
            "construction",
            "pinned_configuration"
          ]
        },
        "pins": {
          "type": "array",
          "description": "For pinned_configuration: model class, decoding settings, prompt version, seed. Recorded in every grading record so a verdict replays."
        }
      }
    },
    "serves_closing_grading": {
      "type": "boolean",
      "description": "False for any engine that has not held verdicts_distinct == 1 over the conformance run."
    },
    "differs_in_execution_model": {
      "type": "array",
      "minItems": 1,
      "description": "Proposed: the shape build-adapter-pair defines; carried here so the pair is rejected when both roles are identical on every axis."
    }
  }
}
```

**judge-conformance-report (proposed shape; the fields the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:judge:conformance-report:0.1",
  "title": "Judge conformance report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "runs",
    "verdicts_distinct",
    "checks_applied_min",
    "requests_scanned",
    "criterion_hits",
    "verdict_mismatches",
    "gold_divergences"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    },
    "runs": {
      "type": "integer",
      "minimum": 0
    },
    "verdicts_distinct": {
      "type": "integer",
      "minimum": 0,
      "description": "Distinct verdicts over repeated gradings of one result. Anything but 1 is a non-deterministic engine."
    },
    "checks_applied_min": {
      "type": "integer",
      "minimum": 0,
      "description": "The smallest checks_applied over the corpus. Zero means some grading decided nothing."
    },
    "requests_scanned": {
      "type": "integer",
      "minimum": 0
    },
    "criterion_hits": {
      "type": "integer",
      "minimum": 0,
      "description": "Occurrences of a criterion string in anything the graded unit can read."
    },
    "verdict_mismatches": {
      "type": "integer",
      "minimum": 0,
      "description": "Results on which the two engines disagreed, over the check kinds both claim to serve."
    },
    "gold_divergences": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| core-judge owns the contract - the signature, purity, the handle, sampling, the audit and what may travel back (F-b2-05). This skill adds only how it is built: an implementation that widens the signature, resolves a criterion inside the graded unit, or returns more than the verdict shape has produced a defect, not an extension. | sourced | `F-b2-05` "pure function `(result, criterion) → verdict`" |
| The verdict function links no model client and no store. agentic-stack and build-adapter-pair state the swap test (F-meta-04); the build consequence is that the module holding the function imports nothing from either engine, so it compiles and runs with no engine bound at all, and a build in which it cannot is where the boundary went wrong. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| Proposed: the criterion store is unreachable from the graded unit by construction, not by convention. No mount into the unit's filesystem, no environment variable, no field on the request, and no telemetry payload the unit can read; core-judge states the rule (F-b1-07) and the lint in step 8 is what keeps it true after the next refactor. | proposed | `F-b1-07` |
| Proposed: a non-deterministic engine may grade inside a loop and may not close work. A binding whose determinism is guaranteed by pinned configuration rather than by construction carries its pins in every grading record, and serves_closing_grading stays false until the conformance run holds verdicts_distinct at 1 over 100 gradings of one result. | proposed | `F-part-c-04`, `X-core-judge-002` |
| agentic-stack states design rule 7 (F-b1-08, F-b4-01). The consequence on this call path is placement: correlation is stamped where the grading is constructed, policy is consulted before any metered call an engine makes, the grading record is attested, and the budget ceiling is read from the envelope - with no flag, binding option or criterion-set field by which a caller can skip one. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record and agentic-stack state the labelling rule (F-part-c-08); the consequence here is that a conformance result is claimed until a run is attached naming the code version and the tree hash under test, and a grading engine is exactly the component that reviews identically and behaves differently once it is asked the same question a hundred times. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Proposed: each engine ships a binding record conforming to the shape above, and the two records differ on at least one axis of the differs_in_execution_model shape build-adapter-pair defines. Two engines that both run local deterministic checks are one engine configured twice, and the pair check rejects them before the conformance run is worth reading. | proposed | `F-b1-04` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: which engine graded, its determinism pins, and the model class a model-graded engine asked for. A caller that can see the engine will branch on it, and the pair stops being swappable; the verdict shape core-judge defines is the whole of what a caller reads. | proposed | `F-meta-04` |
| Proposed: criterion text inside anything this code emits - a prompt sent to a model-graded engine, the trace payload of that call, an error message, a cached grading. core-judge states the grader rule on this contract (F-b1-07); the build consequence is that a model-graded engine's telemetry is redacted at the emitter, because a criterion pasted into a prompt is a criterion in a trace store the graded unit's own tooling may read. | proposed | `F-b1-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the verdict function as a module that imports no model client and no store: it takes a result and a resolved criterion set and returns a verdict, and both the criterion resolver and the grading engine are injected at the edge. | agentic-stack states design rule 1 as a test (F-b1-02) and core-judge requires the function to be pure and total; the only version of that which survives a deadline is one where reaching a network or a store from inside the function is impossible, so the dependency arrow is enforced by the build rather than by review. | sourced | `F-b2-05`, `F-b1-02` "The core imports interfaces, never implementations" |
| 2 | Put criterion sets in a store keyed by criterion_ref and versioned immutably, served only to the Judge process: no mount into the graded unit, no environment variable, no field on the dispatch request, and no read path from inside isolation. | core-judge states that the handle travels and the set does not (F-b1-07); open question 6's default puts the Judge outside isolation precisely so the criterion never crosses that boundary, and an immutable version is what lets a verdict be replayed against exactly the set that produced it. | sourced | `F-b1-07`, `X-core-judge-008` "The grader is never visible to the graded" |
| 3 | Implement both engines behind one binding record: role today the deterministic check gate that runs each declared check and counts what applied, role second a model-graded rubric judge reached through the model-access interface asking for a model class. Fill in both records' determinism block and execution-model axes before either is used. | build-adapter-pair owns this discipline (F-b1-04). The consequence here is specific: a second deterministic runner would leave every in-process, no-network, verdict-is-a-function-of-the-code assumption in place, and an engine that samples a model is what forces the pins, the redaction and the closing-grading rule to exist at all. | sourced | `F-b1-04`, `F-a4-01` "the second exists to prove the first is not load-bearing" |
| 4 | Implement the sampler and the audit from core-judge's contract: derive the sample seed from the result digest, the criterion-set digest and the dispatch id; keep the held-out set out of every routine grading; re-grade a sample against it on an unpredictable cadence and raise an alarm on divergence. | Hiding the criterion is necessary and not sufficient, and the derived seed is what lets sampling coexist with the determinism assertion: a drawn seed would make the same grading return two verdicts and take the C4 criterion down with it. | sourced | `X-end-to-end-012`, `X-end-to-end-013` "a policy trained against a fixed rubric long enough will learn to exploit the difference" |
| 5 | Migrate off the gate that decides done today by dual-grading: keep running it, grade the same work through the Judge, record both outcomes with checks_applied, and cut over only when every grading in the corpus reports checks_applied above zero and each disagreement has an explanation on file. | What runs today reports a stage exit code rather than a count of checks that applied, and PASS.md records it running structurally green with every behavioural stage skipped; migrating on agreement alone would carry that failure across, so the count is the cut-over condition rather than the verdict. | sourced | `F-a7-03` "Our 9-stage pipeline recently ran with every behavioural stage skipped" |
| 6 | Wire the cross-cutting concerns into the grading call: stamp the correlation attribute where the grading is constructed, consult policy before any metered call an engine makes, attest the grading record, and read the budget ceiling from the envelope as a constant no criterion set can raise. | agentic-stack states design rule 7 (F-b1-08); the build consequence is placement, and the measured trace-context finding is why correlation is an explicit attribute set at the call rather than something inherited from whatever invoked the grading. | sourced | `F-b1-08`, `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Add a leak lint that greps every criterion string of a run against the recorded dispatch requests, the step payloads, the verdict details, and the telemetry and prompt payloads reachable by the graded unit, and fail the build when the count is non-zero. | core-judge states the grader rule for this contract (F-b1-07); the build consequence is that the model-graded engine opens a path the deterministic one does not, since a criterion pasted into a prompt lands in a trace store, and a rule that is only stated is one the next refactor breaks silently. | sourced | `F-b1-07`, `F-b4-06` "An agent sees its outcome, never the criterion it is judged against" |
| 8 | Record every conformance run as an evidence record naming what was run, the code version and the tree hash under test, whether the tree was dirty, and the output; label the result claimed until such a record exists. | build-evidence-record owns the record's fields (F-a5-04); the consequence here is that a grading engine's defect shows only at a repetition count nobody reaches in review, so the run and its tree hash are the only things separating a claim from a measurement. | sourced | `F-a5-04` "tree hash under test, and whether the tree was dirty" |
| 9 | Proposed: open references/implementation-notes.md when you are writing the sampler, the redaction, the binding records, the wiring or the dual-grade migration, or reviewing someone who did. The body of this skill is enough to review a design and to run the definition of done without it. | Proposed: the wiring table, the two binding records and the migration procedure are longer than the progressive-disclosure budget allows in the body, and a reader judging the build does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-evidence-record already state the configuration finding (F-a7-04). What it adds here: assert the engine actually in effect at run time and log it beside the counts, because an engine selected in the documented place and overridden by a stored row produces a conformance run that graded everything twice with one engine and reported adapters_run=2. | sourced | `F-a7-04` "had no runtime effect" |
| Split the criterion set by what each check can decide rather than by which engine is convenient: the production pattern is metric-based for what is measurable, a model judge for what requires reasoning, and human review for the small fraction either flags. | sourced | `X-core-judge-006`, `X-core-judge-005` "hybrid: metric-based for what is measurable, LLM-judge for what requires reasoning, human review for the failing 1-5% of samples flagged by either" |
| Treat verification as layered rather than as one engine's job, so a check that a solver or a typed rule can settle is never routed to a sampler; the field is converging on that split, and it is also what keeps the deterministic engine's share of the criterion set large enough to matter. | sourced | `X-core-judge-007` "The field has shifted toward a layered approach rather than relying on a single evaluation method." |
| agentic-stack states that callers request a class, never a vendor (F-a4-01). What it adds here: the model-graded engine's determinism pins name a class and a decoding configuration, so re-pointing the class is a configuration change and never a code change in the Judge. | sourced | `F-a4-01` "Callers request a class, never a vendor" |
| Proposed: run the conformance over both engines on every change, not only when an engine changes. The failures worth catching come from the sampler and the criterion sets - a new check kind, a changed sort order in the sample - and they show as a verdict that moved while no engine was touched. | proposed | `F-b1-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-deterministic-check-gate` | today | What decides done today: a fixed pipeline of deterministic stages run over the work, plus the deployment phases each carrying automated verification. As a grading engine it maps onto the check kinds a document declares, running each declared check in process and returning the counts the verdict is computed from. | Proposed: cannot decide anything not expressible as a tool run, so a criterion about whether the work is useful has no stage to land in; cannot report how many checks actually applied, which is the measured failure PASS.md records - stages that matched nothing still exited green; and cannot hold a criterion out of the graded unit's sight when the stage configuration lives in the same tree as the work. | Select the engine by the binding record, point both roles at the same verdict function and the same criterion store, and run the conformance corpus through both. No core change is expected, because the verdict function never sees the binding. | claimed | `F-a7-03`, `F-a5-02` "Our 9-stage pipeline recently ran with every behavioural stage skipped" |
| `E-swap-candidate-model-graded-rubric-judge` | second | The same grading of a result against the same criterion set, decided by a strong language model scoring the result against the criteria through the model-access interface, asking for a model class. The row names the engine class rather than a product, and determinism is held by pinned configuration rather than by construction. | Proposed: cannot make progress without a served model endpoint, cannot guarantee an identical verdict by construction, and cannot be given the criterion without that text entering a prompt and its trace - which is the point, since every one of those is an assumption the deterministic engine let the Judge keep for free. | Proposed: the execution-model axes that must differ are processes_required_for_progress (zero beyond the check runner, versus one served model endpoint), replay_determinism_required (guaranteed by construction, versus held only by recorded pins), and unit_of_resource_granted (a local process slice, versus a metered call against the envelope's ceiling). Run one parameterised conformance over both roles and require identical verdicts on every check kind both claim to serve. | claimed | `F-b1-04`, `X-core-judge-001` "using a strong language model to score the outputs of another model against a rubric" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.1 row C4, run across both engines. Proposed tool, built with this component: `python3 tools/judge_conformance.py --binding bindings/today.json --binding bindings/second.json --result fixtures/result.json --criterion-ref criterion://fix-acceptable/v1 --runs 100 --requests out/recorded-dispatch-requests.jsonl --report out/judge-conformance.json`. Per engine it grades the same result 100 times and asserts `verdicts_distinct == 1` and `checks_applied_min > 0`; across engines it asserts `adapters_run >= 2` and `verdict_mismatches == 0` over the check kinds both serve; and over a corpus of at least 50 recorded requests it asserts `requests_scanned >= 50` and `criterion_hits == 0`, where criterion_hits counts occurrences of the criterion string in the requests, the step payloads, the verdict details and the prompt and telemetry payloads the graded unit can read. |
| Expected | exit 0, one line per engine of the form `engine=<role> runs=100 verdicts_distinct=1 checks_applied_min=2`, then `adapters_run=2 verdict_mismatches=0 requests_scanned=50 criterion_hits=0 gold_divergences=0`. |
| Deliberate breakage | Inline the criterion text into the document's `definition_of_done` field that is passed to dispatch, re-record the 50 requests, and change nothing else in either engine. |
| Expected failure | The criterion string is now present in every recorded request, `criterion_hits` reports 50, the run exits non-zero - and it fails identically under both engines while `verdicts_distinct` stays 1 for each, which is the report saying what the design says: hiding the criterion is a property of what dispatch may put in a request, not of the engine that grades. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-07` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `core-judge`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| May the model-graded engine ever serve the closing grading, or only gradings inside a loop? | Run the 100-grading determinism assertion against the pinned engine over a corpus spanning result sizes and check kinds, and count how often verdicts_distinct exceeds 1. A run that holds at 1 across the corpus argues for letting it close work; anything else pins it to in-loop gradings. | In-loop only, with serves_closing_grading false, because a verdict that closes work is the one a loop terminates on and a re-run that disagrees would reopen finished work. The deterministic engine closes until the measurement exists. | `X-core-judge-002`, `F-part-c-04` "uncontrolled judges are unreliable for ranking decisions" |
| Is a model-graded grading metered against the graded unit's budget ceiling or against a platform grading budget? | Measure grading cost as a share of unit cost across a run history, and count how often a unit that failed on budget had spent a material part of it on being graded. A material share means charging the unit makes the budget a grading tax; a negligible one means a separate ceiling is bookkeeping nobody reads. | A separate platform grading ceiling, because a unit that can exhaust its budget by being graded can also lower its own grading rate, which puts the grader inside the graded unit's control. Every unit of work still carries a ceiling either way. | `F-b4-02` "Every unit of work carries a ceiling" |
| Where does the criterion store physically live, given that the Judge runs outside isolation by default? | Grep every payload the graded unit could read across at least 200 recorded dispatches for the criterion string, under each candidate placement. A placement with any hit is disqualified regardless of how convenient it is. | Beside the Judge process and behind resolve_criterion, reachable by no path the graded unit has, with the state seam owning durability. It is recorded as an open question rather than settled because the placement that is easiest to operate - the criterion in the same tree as the work - is exactly the one the lint exists to catch. | `F-b1-07`, `T-t5-02` "define the problem, identify the three best possible solutions that align to the goal" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
