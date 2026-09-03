---
name: cap-evaluation-implement
description: How to build the Evaluation capability on this stack: a scoring adapter over the trace backend that already ingests every run, a second adapter with no collector and no server that replays fixtures from disk, the migration from a deterministic pipeline whose behavioural stages can all skip and still report green, where budget, policy, identity, telemetry, provenance and idempotency attach to an evaluation and to each case, and a definition of done with the regression that makes it fail. Load it when writing or reviewing the code that registers a case set, replays a recorded run or scores a trajectory, when wiring an evaluation into a release gate or a self-improvement loop, when deciding what the second harness should be, when a verdict reproduces on one harness and not the other, or when a gate reported success having executed nothing.
---

# cap-evaluation-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the cap-evaluation contract into something that runs here: which adapter is built first and on what, what the second one deliberately lacks, how a pipeline whose behavioural stages skipped and still went green becomes a gate with a stored baseline, and what a run must print before either adapter is allowed to refuse a change. | sourced | `F-a7-03`, `F-a5-02` "A deterministic gate can be structurally green and mean nothing." |

## Entities

| Entity |
|---|
| `E-finding-a7-2` |
| `E-finding-a7-3` |
| `E-capability-telemetry` |
| `E-core-component-judge` |
| `E-standard-genai-semantic-conventions` |

## Contract

### Shapes (JSON Schema 2020-12)

**EvaluationBinding (proposed): the record that selects a harness - the only file that differs between the two adapters** (proposed; sources: `F-b1-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:evaluation:binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. One binding per adapter, selected by configuration. Nothing in cap-evaluation's operations, CaseSet or EvaluationReport changes when the binding changes; if a field has to move into a request to make a harness work, the field belongs to the harness and not to the capability.",
  "required": [
    "binding_id",
    "role",
    "execution_model",
    "trajectory_source",
    "case_set_root",
    "report_sink"
  ],
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "execution_model": {
      "enum": [
        "collector-backed",
        "no-server"
      ],
      "description": "the axis the pair differs on; two bindings with the same value are not a pair"
    },
    "trajectory_source": {
      "enum": [
        "trace-backend",
        "fixture-file"
      ],
      "description": "where a trajectory to be scored comes from"
    },
    "case_set_root": {
      "type": "string",
      "description": "resolved corpus location or endpoint; never read by a caller"
    },
    "report_sink": {
      "type": "string"
    },
    "emit_evaluation_result": {
      "type": "boolean",
      "default": true,
      "description": "whether per-case verdicts are also exported on the standard carrier; the second binding may leave this false without changing the report a caller reads"
    }
  }
}
```

**GateStageResult (proposed): what the release gate reports, so a stage that ran nothing cannot read as green** (proposed; sources: `F-a7-03`, `F-a5-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:evaluation:gate-stage:0.1",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. The stage record the pipeline writes. status is copied from the report's outcome and is never derived from an exit code, because a stage that skipped exits zero.",
  "required": [
    "stage",
    "status",
    "cases_executed",
    "report_id",
    "adapters_run"
  ],
  "properties": {
    "stage": {
      "const": "evaluation"
    },
    "status": {
      "enum": [
        "passed",
        "failed",
        "inconclusive",
        "skipped"
      ],
      "description": "skipped and inconclusive both block promotion; neither may be reported as green"
    },
    "cases_executed": {
      "type": "integer",
      "minimum": 0
    },
    "report_id": {
      "type": "string"
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    },
    "evidence_record_id": {
      "type": "string",
      "description": "the appended record naming the script digest, the commit, the tree hash and whether the tree was dirty"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The core imports cap-evaluation's five operations and never a harness. A harness is reached only through an EvaluationBinding selected by configuration, so agentic-stack's design rule 1 and cap-evaluation's restatement of it (F-b1-02) are enforced by there being no other path to one. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| A gate stage that executed no case reports inconclusive or skipped and blocks promotion. agentic-stack and build-definition-of-done both state the finding this comes from (F-a7-03): the 9-stage pipeline that runs here has already gone green with every behavioural stage skipped, so an evaluation stage that copies its status from an exit code repeats that defect exactly. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Neither adapter gates anything until both have scored the same registered case set and agreed case by case. build-adapter-pair owns design rule 3 and cap-evaluation states the pair for this capability (F-b1-04); the consequence in the code is that the conformance run, not the first green pipeline, is what promotes a harness to gating. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| Budget, policy, identity, telemetry, provenance and idempotency attach at the evaluate boundary and again per case, and no field of an evaluation request can decline them. agentic-stack states the rule (F-b1-08); what is specific here is that a corpus of cases is the cheapest way to spend a budget by accident, so the ceiling is checked per case and not once per report. | sourced | `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| Every conformance and gate result is labelled claimed until a run produced it, and the run that produces it is appended to the evidence store with the tree it tested. build-evidence-record owns the record shape and the claimed-versus-measured labelling (F-part-c-08); this skill's own definition of done is claimed, because nothing described here exists in this tree yet. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the binding itself. Which harness scored a report, where the corpus was resolved from and whether a collector was attached are absent from CaseSet, EvaluationReport and the problem object, so a caller cannot come to depend on the adapter that happens to be selected. cap-evaluation owns the full not-exposed list for this capability, including what the grader rule forbids here. Research query: is there a recorded conformance report shape (a binding record schema already in this facet's contract.shapes) that fixes exactly which binding fields exist, so this exclusion can cite that shape by name instead of asserting the list here? | proposed | `F-b1-02` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Implement cap-evaluation's five operations as the module the core imports, and put the harness behind an EvaluationBinding resolved at startup. Do not let a metric class, a dataset loader, a test-runner decorator or a collector client appear in a signature the core calls. | Everything that differs between a collector-backed harness and a harness with no server lives in exactly those four things. If one of them reaches a core signature, the second adapter cannot be written without editing the core, and the pair stops being a swap. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| 2 | Build today's adapter on the trace stack that already runs: read the stored trajectory for a recorded run out of the trace backend, score it per case, write the EvaluationReport, and export each per-case verdict on the standard evaluation-result carrier. | Traces are already being ingested and stored on this host, so the recorded half of the corpus costs nothing to obtain and the first adapter needs no new storage. See the Adapters table for what this binding is and what it cannot do. | sourced | `F-b3-10`, `F-a1-05` "OTLP · GenAI semantic conventions" |
| 3 | Build the second adapter with no collector, no backend and no server: each case is a test function, each recorded run is a fixture file on disk, and the assertion is the per-case verdict against the stored baseline. Read the same CaseSet and write the same EvaluationReport. | cap-evaluation names the axis the pair must differ on. Choosing a second harness that also needs a running collector would prove only that two products of the same shape exist, which is the failure build-adapter-pair is written to prevent. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 4 | Harvest the recorded half of the first corpus rather than authoring it: take runs the evidence store already names, pair each with the trajectory the trace backend holds for it, and register them as cases with mode replay. Author only the synthetic half. | There are already thousands of appended records over hundreds of runs, and build-evidence-record states what each one names (F-a5-04) - which is exactly the provenance a case needs to be worth replaying. Writing a corpus from scratch also writes in the assumptions the system already has. | sourced | `F-a5-04` "tree hash under test, and whether the tree was dirty" |
| 5 | Freeze the first baseline from a single report over the harvested corpus, record it as claimed, and do not promote a second baseline in the same change that alters a unit under test. | A baseline promoted alongside the change it was meant to judge is not a baseline. Keeping promotion a separate, separately authorised call is what stops a self-improvement loop from grading itself into approval, and build-evidence-record owns the labelling that keeps the frozen baseline honest until a run produced it (F-part-c-08). | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 6 | Replace the behavioural stage of the deterministic pipeline with one evaluate call, and have the stage copy its status from the report's outcome. Make skipped and inconclusive block promotion, and never derive the stage status from an exit code. | The pipeline here has already run green with every behavioural stage skipped, because the tools had nothing to apply to. A stage that reads an exit code cannot tell that case from a real pass, so the count of executed cases has to be the thing it reports. | sourced | `F-a7-03` "Our 9-stage pipeline recently ran with every behavioural stage skipped" |
| 7 | Wire the cross-cutting guarantees at the evaluate boundary and again around each case: the budget ceiling checked per case, the policy decision taken before the first case runs, the actor and its delegation chain carried onto every case, the correlation id set at dispatch, the report appended to the provenance chain, and the idempotency key covering the whole evaluation rather than one case. | agentic-stack states that these are applied by the platform and not requested by the caller (F-b1-08). A corpus is where that rule bites hardest: one evaluate call can fan out into hundreds of metered model calls, so a ceiling checked once at the top stops nothing. | sourced | `F-b1-08` "Cross-cutting guarantees are not optional." |
| 8 | Prove the binding took runtime effect rather than that it was written: run the same corpus under both bindings in one command and diff the per-case verdicts, instead of asserting that the configuration file names the harness you expect. | agentic-stack records the finding (F-a7-04): configuration written in the documented place on this host has already been silently overridden by a stored row. The consequence here is specific - a scoring harness selected but not actually used produces a plausible report from the wrong code, and a diff of two verdict sets is the cheapest thing that can tell. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 9 | Append every conformance and gate run to the evidence store as a record naming the script digest, the commit, the tree hash under test and whether the tree was dirty, and cite that record id from the gate stage result. | build-evidence-record owns the record shape; the consequence here is that a report claiming a regression was caught is only evidence if the tree it scored can be named afterwards, and a dirty tree makes the whole report unreproducible. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit" |
| 10 | Proposed: open references/wiring.md for the per-concern attachment table, the migration order with what is claimed at each step, and the conformance command in full. The body of this skill is enough to build both adapters without it. | Proposed: progressive disclosure. The attachment table and the migration order are long and are needed once, when the wiring is written, not every time someone reads how the pair works. | proposed | `F-b1-08` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Set the correlation id on an explicit attribute at dispatch and carry it onto every case, rather than relying on trace parentage to link a case back to the evaluation that ran it. agentic-stack states the finding (F-a7-02); it matters twice here, because today's adapter reads the very traces that lost their parentage. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| Do not let the existence of conformance checks stand in for their being wired in. A check that exists and is not in the enforcement path is the state this host is already in for policy, and an evaluation harness that runs beside the gate rather than inside it will read as adopted while refusing nothing. | sourced | `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |
| Keep the replay half of the corpus in continuous integration and the live half out of it. cap-evaluation states the practice and its source (X-end-to-end-038); the split matters in the code because a live case in CI turns every pull request into real spend and real side effects. | sourced | `X-end-to-end-038` "To proactively guard against non-determinism errors" |
| Proposed practice, on a sourced fact: the deployment phases here already report automated verification green across the board (F-a5-02), so treat all-green as a question rather than an answer - the first useful thing a new corpus does is fail on something that was green yesterday. | sourced | `F-a5-02` "8, each with automated verification, all currently green" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-otel-trace-scoring-harness` | today | Proposed adapter, and a proposed entity id: PASS.md B3 has no Evaluation row, so kb/entities.jsonl carries no adapter entity for this capability; cap-evaluation mints the same id and records the gap as an open question. What it binds to does run: the Langfuse trace UI and ingestion API with ClickHouse behind it, already ingesting and storing every trace on this host. register_case_set writes the corpus beside the traces, replay_case reads a stored trajectory instead of re-running the unit, score_trajectory scores that trajectory, and each verdict is exported as a gen_ai.evaluation.result against the OpenTelemetry GenAI semantic conventions. | Proposed: cannot score a run whose trace never reached the backend, cannot run in a pull-request checkout where no collector, ClickHouse or Langfuse instance is reachable, and cannot give a developer a verdict they can reproduce locally before pushing. It also inherits the correlation defect: goose mints its own root trace, so a case assembled from trace parentage alone can be the wrong trajectory. | Change binding.execution_model from collector-backed to no-server in the EvaluationBinding and re-run; no core file is edited, because the core imports cap-evaluation's five operations. | claimed | `F-a1-05`, `F-a1-07`, `F-b3-10` "Trace UI and ingestion API" |
| `E-swap-candidate-local-fixture-replay-harness` | second | Proposed adapter, and a proposed entity id: a test-runner-shaped harness with no collector and no server. Cases are test functions, recorded trajectories are fixture files committed beside the corpus, and the per-case verdict is the assertion. It reads the same CaseSet and writes the same EvaluationReport, with emit_evaluation_result false, so it runs in a checkout with nothing else installed. | Proposed: cannot score a production run it did not record, cannot aggregate across a fleet and cannot show a trend without something else keeping the reports. That is the axis: the first binding needs a collector, a trace store and a backend running; the second needs a filesystem. An operation shaped around a live trace stream fails here outright rather than degrading, which is what makes the pair a test of the interface. | One conformance run puts the identical registered corpus through both bindings against the same baseline and diffs per-case verdicts, transitions and refusal types; the merged report must show adapters_run >= 2 and verdict_divergence == 0 before either binding is allowed to gate a promotion. | claimed | `X-cap-evaluation-001`, `F-b1-04` "a runner designed for local development and CI/CD" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Two runs from the repository root with a proposed tool. First the pair: `python3 tools/conformance_evaluation.py --binding config/eval/trace-scoring.json --binding config/eval/local-fixture.json --unit agent:release-reviewer@1.4.0 --case-set corpus/cs-release-review --baseline corpus/bl-2026-08-27.json --report out/eval-conformance.json` over six cases, three harvested from recorded runs and three synthetic, all passing at the baseline. Then the gate: `python3 tools/gate.py --stage evaluation --report out/eval-conformance.json --emit out/gate-stage.json`. Assert `adapters_run == 2`, `cases_executed == 6`, `outcome == passed`, `transitions == 0`, `verdict_divergence == 0`, that `out/gate-stage.json` validates against GateStageResult with `status=passed`, and that re-running the gate against a report with `cases_executed=0` yields `status=inconclusive` and exit 1. Gap: no harness covers this capability yet (STATUS row 60). |
| Expected | `adapter=today cases_executed=6 outcome=passed transitions=0` and `adapter=second cases_executed=6 outcome=passed transitions=0`, then `adapters_run=2 verdict_divergence=0`, then `stage=evaluation status=passed cases_executed=6 evidence_record_id=<id>`; the zero-case gate run printing `stage=evaluation status=inconclusive cases_executed=0` and exiting 1. |
| Deliberate breakage | In the gate, derive `status` from the conformance tool's exit code alone - `status=passed` whenever it exits 0 - instead of from `cases_executed` and `outcome` in the report. Change nothing else: not the corpus, not the baseline, not either binding, not the unit under test. |
| Expected failure | Both bindings still report `outcome=passed transitions=0` and `adapters_run=2 verdict_divergence=0`, so neither harness is what moved. The zero-case run is the one that fails: the gate prints `stage=evaluation status=passed cases_executed=0` and exits 0 where `status=inconclusive` and exit 1 are required, so that assertion fails and the definition-of-done run exits non-zero naming the gate stage rather than a case. A gate reporting passed having executed nothing is the structurally-green pipeline F-a7-03 records, and catching it here is what shows the stage status is read from the report's counters rather than from an exit code - a build-level fault, distinct from the regression in the unit under test that cap-evaluation's own breakage introduces. Claimed: neither binding, the corpus, the gate stage nor the tool exists in this tree, so this starts red by construction. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a7-03` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `cap-evaluation`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should the recorded half of the corpus be stored beside the code or in the trace backend that already holds the trajectories? | A measurement of how large one replay fixture actually is for a representative run, and whether the trace backend can export a trajectory in a form the no-server binding can read without it. Applying 1-3-1: (1) fixtures in the repository, which makes the no-server binding self-contained and the corpus reviewable in a diff but adds weight to every checkout; (2) fixtures in the trace backend only, which is free until the second binding needs one and then blocks it entirely; (3) fixtures in the repository by digest with the bodies in the blob store the trace stack already runs, which keeps the checkout small but reintroduces a running service the second binding was chosen to do without. Recommendation and choice: (1) until a fixture is measured large enough to hurt, because option 3 defeats the axis the pair differs on. | Fixtures live beside the corpus in the repository, and the binding's trajectory_source says which one is read. | `T-t5-02`, `F-b1-04` "identify the three best possible solutions that align to the goal" |
| Does the durable orchestrator that is installed but not listening become the thing that runs a long evaluation, or does the harness fan cases out itself? | PASS.md A6 records the orchestrator's data directory present and the server not listening. Deciding needs a measurement of how long a full corpus takes under each binding and whether a crash mid-corpus is common enough to need resumption at the first incomplete case. | The harness fans out cases itself and re-running the whole corpus is the recovery. cap-durable-execution owns the step, checkpoint and resume vocabulary if that stops being acceptable; nothing in cap-evaluation's operations changes either way. | `F-a6-02` "Data directory present; server not listening" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation cap-evaluation-implement author 2026-09-03 |
