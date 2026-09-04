---
name: "cap-evaluation"
description: "Evaluation contract and build: score a versioned unit against a versioned case set of synthetic scenarios and replayed recorded runs, returning passed, failed or inconclusive against a stored baseline. Load it before a prompt, model, skill or workflow change ships, when an improvement loop needs a gate that can say no, or when a green run scored nothing."
---

# cap-evaluation

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for scoring a versioned unit of work against a versioned case set and a stored baseline, so a change can be refused before it ships and the harness that does the scoring stays an adapter. PASS.md has no evaluation row in any section: this capability exists because TARGET requires the gaps in that baseline to be found and filled, and because an evaluation harness is a different artifact from the runtime Judge. | sourced | `T-t4-03`, `X-end-to-end-009` "make up for the gaps, and solve it" |

## Entities

| Entity |
|---|
| `E-standard-genai-semantic-conventions` |
| `E-core-component-judge` |
| `E-capability-telemetry` |
| `E-capability-errors` |
| `E-standard-rfc-9457-problem-details` |
| `E-standard-json-schema-2020-12` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-genai-semantic-conventions` | unverified | unverified | - | `F-b3-10`, `X-end-to-end-006`, `X-cap-evaluation-006` |

- `E-standard-genai-semantic-conventions` version note: docs/skill-manifest.json records the governing standard for this capability as the OpenTelemetry GenAI semantic conventions and the gen_ai.evaluation.result carrier at v1.37 or later, and marks that version unverified. No specification was fetched from this environment, so the version stays unverified here. cap-telemetry owns the OTLP and GenAI semantic-conventions rows for the Telemetry row of PASS.md B3 (F-b3-10); this row names the same conventions only as the carrier a verdict travels on, because the conventions represent an evaluation result and do not perform one.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| register_case_set (call name is ours; a version-controlled corpus is the sourced half) | cases - synthetic scenarios and recorded runs - each with its inputs, a rubric handle, and a stub policy saying which external effects are served from the record; plus a semantic version | a case_set_id and a content digest; registering identical cases twice returns the same digest (proposed) | sourced | `X-cap-evaluation-002`, `X-end-to-end-039` "a generated, labeled, version-controlled evaluation corpus" |
| evaluate (call name is ours; regression detection against a stored baseline is the sourced practice) | a versioned reference to the unit under test, a case_set_id, a baseline_id, and a mode of live or replay | an evaluation_report_id and an outcome of passed, failed or inconclusive - the one field a caller branches on (proposed) | sourced | `X-cap-evaluation-001`, `X-end-to-end-040` "Regression testing catches performance degradation when prompts, models, or integrations change before production deployment." |
| replay_case (call name is ours; substituting the stored result for execution is the sourced mechanism) | one recorded run reference and the stub policy its case declares | the trajectory the unit produces this time, with every recorded external effect served from the record instead of executed (proposed) | sourced | `X-cap-evaluation-005` "wherever a recorded operation appears it substitutes the stored result instead of executing it" |
| score_trajectory (call name is ours; the four dimensions it scores are the sourced ones) | one trajectory and the case's rubric handle, never the rubric body | per-dimension scores over the ordered trace and one per-case verdict (proposed) | sourced | `X-cap-evaluation-003`, `X-end-to-end-010` "trajectory (the path of steps), tool use (correct tool selection and arguments), task completion (whether the user's goal was met)" |
| promote_baseline (call name is ours; retaining the prior baseline rather than overwriting it is the sourced improvement-loop discipline) | an evaluation_report_id and the reason it may become the reference point | a baseline_id later reports are compared against; the previous baseline is retained, not overwritten (proposed) | sourced | `X-end-to-end-040`, `T-t4-04` "A regression suite is the gate that makes a self-improvement loop safe to run automatically." |

### Shapes (JSON Schema 2020-12)

**CaseSet (proposed summary shape; the full schema, the stub-policy grammar and the worked calls are in references/usage.md)** (sourced; sources: `X-cap-evaluation-002`, `X-cap-evaluation-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:evaluation:case-set:0.1",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed summary. A versioned corpus of cases. Nothing here names a harness, a metric implementation or a store.",
  "required": [
    "case_set_id",
    "version",
    "digest",
    "cases"
  ],
  "properties": {
    "case_set_id": {
      "type": "string"
    },
    "version": {
      "type": "string",
      "description": "semantic version of the corpus, not of the unit under test"
    },
    "digest": {
      "type": "string",
      "description": "content digest over the canonical cases; two registrations of identical cases agree"
    },
    "cases": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "case_id",
          "corpus_half",
          "input",
          "rubric_ref",
          "stub_policy"
        ],
        "properties": {
          "case_id": {
            "type": "string"
          },
          "input": {
            "type": "object"
          },
          "rubric_ref": {
            "type": "string",
            "description": "opaque handle; the rubric body never appears in a case"
          },
          "recorded_run_ref": {
            "type": "string",
            "description": "set when corpus_half is recorded; the trajectory replay reads its effects from"
          },
          "stub_policy": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "mode"
            ],
            "properties": {
              "mode": {
                "enum": [
                  "record",
                  "replay"
                ]
              },
              "unrecorded_effect": {
                "enum": [
                  "fail",
                  "refuse"
                ],
                "description": "what happens when replay meets an effect the record does not hold; executing it is not an option"
              }
            }
          },
          "corpus_half": {
            "enum": [
              "recorded",
              "synthetic"
            ],
            "description": "which half of the corpus this case came from: recorded from a real run, or synthetic"
          }
        }
      }
    }
  }
}
```

**EvaluationReport (proposed summary shape): outcome is a three-valued word, never a bare boolean** (sourced; sources: `X-end-to-end-040`, `X-cap-evaluation-003`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:evaluation:report:0.1",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed summary. One report per evaluate call. inconclusive exists so that a run which executed nothing cannot read as a pass.",
  "required": [
    "report_id",
    "unit_under_test",
    "case_set",
    "baseline_id",
    "outcome",
    "cases_executed",
    "transitions",
    "correlation_id"
  ],
  "properties": {
    "report_id": {
      "type": "string"
    },
    "unit_under_test": {
      "type": "object",
      "required": [
        "ref",
        "version"
      ],
      "properties": {
        "ref": {
          "type": "string"
        },
        "version": {
          "type": "string"
        }
      },
      "description": "pinned; a report that cannot name the version it scored is not comparable to any other report"
    },
    "case_set": {
      "type": "object",
      "required": [
        "case_set_id",
        "digest"
      ],
      "properties": {
        "case_set_id": {
          "type": "string"
        },
        "digest": {
          "type": "string"
        }
      }
    },
    "baseline_id": {
      "type": "string"
    },
    "outcome": {
      "enum": [
        "passed",
        "failed",
        "inconclusive"
      ]
    },
    "cases_executed": {
      "type": "integer",
      "minimum": 0
    },
    "transitions": {
      "type": "array",
      "description": "per-case movement against the baseline; an aggregate delta is not a substitute",
      "items": {
        "type": "object",
        "required": [
          "case_id",
          "was",
          "now"
        ],
        "properties": {
          "case_id": {
            "type": "string"
          },
          "was": {
            "enum": [
              "pass",
              "fail",
              "absent"
            ]
          },
          "now": {
            "enum": [
              "pass",
              "fail"
            ]
          },
          "dimension_scores": {
            "type": "object"
          }
        }
      }
    },
    "correlation_id": {
      "type": "string"
    }
  }
}
```

**Worked calls (proposed): the same evaluate request from a human, from an agent and from an event** (proposed; sources: `T-t1-01`, `T-t1-02`, `T-t1-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:evaluation:worked-calls:0.1",
  "description": "Proposed. agentic-stack (formerly cap-consumption) owns the entry envelope and the caller doctrine; these are this capability's payloads inside it, one per way in. TARGET T1 lists the three ways in that these instances cover; references/usage.md carries them in full with the answers.",
  "type": "object",
  "examples": [
    {
      "kind": "human",
      "actor": {
        "subject": "user:corey",
        "delegation_chain": [
          {
            "actor": "user:corey",
            "obtained_via": "direct"
          }
        ]
      },
      "intent": {
        "capability": "evaluation",
        "operation": "evaluate",
        "why": "gate the release-reviewer prompt change"
      },
      "payload": {
        "unit_under_test": {
          "ref": "agent:release-reviewer",
          "version": "1.4.0"
        },
        "case_set_id": "cs-release-review",
        "baseline_id": "bl-2026-08-27",
        "mode": "replay"
      }
    },
    {
      "kind": "external",
      "actor": {
        "subject": "agent:improvement-loop",
        "delegation_chain": [
          {
            "actor": "user:corey",
            "obtained_via": "direct"
          },
          {
            "actor": "agent:improvement-loop",
            "obtained_via": "rfc8693_token_exchange"
          }
        ]
      },
      "intent": {
        "capability": "evaluation",
        "operation": "evaluate",
        "why": "check the candidate rewrite before proposing it"
      },
      "payload": {
        "unit_under_test": {
          "ref": "skill:cap-evaluation-implement",
          "version": "0.2.0-candidate"
        },
        "case_set_id": "cs-release-review",
        "baseline_id": "bl-2026-08-27",
        "mode": "replay"
      }
    },
    {
      "kind": "event",
      "actor": {
        "subject": "service:git-webhook",
        "delegation_chain": [
          {
            "actor": "service:git-webhook",
            "obtained_via": "workload_attestation"
          }
        ]
      },
      "intent": {
        "capability": "evaluation",
        "operation": "evaluate",
        "why": "a merge landed on the default branch"
      },
      "payload": {
        "unit_under_test": {
          "ref": "workflow:nightly-triage",
          "version": "9f2c1ab"
        },
        "case_set_id": "cs-triage",
        "baseline_id": "bl-2026-08-30",
        "mode": "live"
      }
    }
  ]
}
```

**The failure shape (proposed): an evaluation whose rubric handle does not resolve** (proposed; sources: `F-b3-13`, `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:evaluation:problem-instance:0.1",
  "description": "Proposed. cap-errors owns the problem object and the closed type registry; this is the instance a caller of this capability actually receives. criterion-unresolvable is the registered row that fits, because a rubric handle is the criterion reference a case carries. A refusal is never an outcome value: passed, failed and inconclusive describe a run that happened.",
  "type": "object",
  "examples": [
    {
      "type": "urn:agentic:problem:criterion-unresolvable",
      "title": "Rubric handle does not resolve",
      "status": 422,
      "detail": "case_set cs-release-review case 12 names rubric_ref rub:tone-v3, which no version of the rubric store resolves",
      "retryable": false,
      "correlation_id": "01JB8W3Q0Z9K2M4N6P8R"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Evaluation is offline and dev-time work, and is a different artifact from the runtime Judge. core-components (formerly core-judge) owns the runtime verdict on one result against one criterion (F-b2-05). Proposed consequence: this interface may therefore be slow, expensive and repeated, because nothing is waiting on its answer. | sourced | `X-end-to-end-009`, `F-b2-05` "An eval harness is strictly for offline/dev-time validation, distinct from runtime guardrails." |
| Proposed, extending one sourced half: an evaluation corpus is version-controlled (X-cap-evaluation-002), and this interface additionally requires the report to pin the version of the unit under test beside the corpus digest. A report missing either cannot be compared with another report, so it cannot show a regression and is not evidence of anything. Research query: is there a recorded evaluation-framework record that pins the unit-under-test version alongside the corpus digest in the report itself, or is that pairing this repository's own addition to the sourced half? | proposed | `X-cap-evaluation-002` |
| Scoring reads the ordered trace, not only the final answer. core-components records the trajectory gap in PASS.md's Judge signature (X-end-to-end-010). Proposed consequence on this interface: a case whose final answer is right and whose tool calls were wrong is a failing case, and a scorer that cannot see the steps cannot serve here. | sourced | `X-end-to-end-010`, `X-cap-evaluation-003` "including reasoning, tool calls, observations, and intermediate steps" |
| A replayed case serves every recorded external effect from the record rather than executing it. Proposed consequence: a run that re-executes an effect is a live run mislabelled - neither free of side effects nor deterministic - and its verdict is not comparable to a baseline that a replay produced. | sourced | `X-cap-evaluation-005` "wherever a recorded operation appears it substitutes the stored result instead of executing it" |
| Outcome has three values and a run in which no case executed takes the third. An empty selector, a case set that failed to resolve or a harness that crashed before the first case reports inconclusive, never passed. build-evidence (formerly build-definition-of-done) owns the rule that a check which cannot fail is not a check; this is the shape that keeps a vacuous evaluation from reading as evidence. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion." |
| build-ceremony owns the improvement loop this interface feeds (T-t4-04): a ceremony re-reviews a section's output, improves the skills that produced it, and the loop continues, so this capability's verdicts are what that loop turns on. | sourced | `T-t4-04` "improves the skills that produced it, and the loop continues" |
| Proposed consequence of the row above: reports and baselines are appended and retained, never overwritten. Promoting a new baseline keeps the old one, so a loop that made things worse can be shown to have done so rather than argued about. No record in kb/ states a retention rule for evaluation reports; this is the author's extension and is owed research. | proposed | - |
| The core imports this interface and never a harness. agentic-stack states design rule 1 (F-b1-02); on this interface it forbids a metric class, a dataset loader, a test-runner decorator or a collector client appearing in a core signature, because those are the parts that differ between the two adapters. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| The conventions named in the Standards table carry an evaluation result and do not produce one, so a platform that emits the attribute has not thereby evaluated anything. Proposed consequence: a per-case verdict leaves this interface on that carrier, and replacing the scorer changes nothing a reader consumes. | sourced | `X-end-to-end-006` "Evaluation is represented—but not performed—by OpenTelemetry" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The rubric body. agentic-stack states design rule 6 (F-b1-07) and core-components states it for the runtime verdict; on this interface it forbids exactly one thing: the text a case is scored against may never travel into the unit under test. A case carries rubric_ref, an opaque handle, and the handle is resolved inside the scorer after the trajectory exists, so a unit that reads its whole input still cannot read what it is graded on. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| Proposed: the metric implementations, the score thresholds, the dataset storage layout, and whether a telemetry collector is running at all. None of them is a field of a request or of a report; a caller that had to know them would be coding against the harness rather than against this interface. Research query: does cap-telemetry's own not_exposed table already exclude collector-running status as its own row, which this row could point to by name instead of restating it here? | proposed | `X-cap-evaluation-001` |
| Proposed: which model, ensemble or human review a scorer used to reach a verdict. A caller reads scores, dimensions and transitions; making the judging model a field would make every stored report incomparable the day it changes. Research query: does the held-out gold-judge pattern on file (X-cap-evaluation-007) say anything about the judge's identity being reported alongside a verdict, which would confirm or contradict this exclusion? | proposed | `X-cap-evaluation-007` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the case set before the evaluator, and build it from both halves: hand-curated cases taken from real recorded runs, and synthetic scenarios written for the edges those runs never reached. | A corpus of only recorded runs scores the distribution you already survived; a corpus of only synthetic scenarios scores a world you invented. The split is what makes a pass mean something about production. | sourced | `X-cap-evaluation-002`, `X-end-to-end-039` "A 50/50 split between hand-curated production traces and synthetic data" |
| 2 | Give every case a stub policy that names which external effects are served from the record, and make an unrecorded effect fail or refuse the case rather than reach the real thing. | Replay is only cheap and deterministic while nothing escapes to a live system. The moment one unrecorded call goes out, the run has side effects and its result stops being reproducible. | sourced | `X-cap-evaluation-005` "it is fast, free of side effects, and lands on the same state every time" |
| 3 | Score each trajectory across the dimensions the trace supports - the path of steps, whether the right tool was called with the right arguments, whether the task completed, and whether quality held across turns - and record the per-dimension scores next to the verdict. | A single number tells you a case regressed and not where. The dimensions are what turn a failing case into a fix rather than into an argument. | sourced | `X-cap-evaluation-003` "trajectory (the path of steps), tool use (correct tool selection and arguments), task completion (whether the user's goal was met), and multi-turn quality" |
| 4 | Compare the report to the stored baseline case by case and report the transitions - which case_id moved from pass to fail - rather than an aggregate score delta. | An aggregate can stay flat while one case flips, and a flat aggregate is exactly the shape a regression hides in. A named case that moved is also the smallest reproduction anyone needs. | sourced | `X-end-to-end-040` "Regression testing catches performance degradation when prompts, models, or integrations change before production deployment." |
| 5 | Emit each per-case verdict on the standard evaluation-result carrier from the Standards table, and keep the platform's own scoring separate from the emission. | cap-telemetry owns the carrier and the collector for the Telemetry row of PASS.md B3, and core-components already records that the conventions carry an evaluator verdict without producing one (X-end-to-end-006); the consequence here is that a reader of evaluation results learns no second format, while the scoring itself stays inside this capability where it can be swapped. | sourced | `X-end-to-end-006`, `F-b3-10` "gen_ai.evaluation.result providing a standard carrier for evaluator scores and explanations" |
| 6 | Pass rubric_ref into a case and resolve it only inside the scorer, after the trajectory is complete. Never let the resolved body into the unit's input, its context, its tool results or a replayed effect. | Design rule 6 is agentic-stack's, and core-components holds it for the runtime verdict (F-b1-07): the grader is never visible to the graded, and an evaluation harness inherits that rule unchanged. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| 7 | Give a case a rubric handle and no field a rubric body could be written into, so handing the graded unit its own criterion takes a schema change rather than one line. Research query: unresearched; no prior-art search has been run for evaluation-harness case schemas that structurally exclude the rubric body, beyond design rule 6 (F-b1-07). | Proposed: an evaluation harness is the one component structurally placed to break design rule 6, because it holds both the rubric and the case input; a case shape with nowhere to put the body is what makes the rule checkable in the fixture rather than trusted in the scorer. | proposed | `F-b1-07` |
| 8 | Run the same registered case set through both adapters in the Adapters table and require identical per-case verdicts before either is allowed to gate anything. | build-evidence (formerly build-adapter-pair) owns design rule 3; the consequence here is specific - a verdict that only reproduces on the adapter with a collector attached is a property of that collector, not of the unit under test, and would silently become the thing the whole gate rests on. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 9 | Proposed: open references/usage.md when you need the full CaseSet and EvaluationReport schemas, the three ways in with a worked call and answer for each, and the worked rejection. The body of this skill is enough to write a caller without it. | Proposed: progressive disclosure. The schemas and the worked calls are long, and a reader who only needs to know what to send and what comes back should not have to page through them first. | proposed | `T-t1-01` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Add replay of the recorded half of the case set to continuous integration rather than running it by hand before a release. Proposed emphasis: the cases that catch non-determinism are worthless on the day someone remembers to run them. | sourced | `X-end-to-end-038` "you can add replay testing to your CI" |
| Reserve model-judged scoring for the offline held-out portion of the corpus and keep deterministic checks for everything that can be checked deterministically; a judged case costs a full model call, which is affordable per corpus and not per production turn. | sourced | `X-cap-evaluation-007` "LLM-as-judge is fine for offline scoring on a held-out sample, where cost and variance are bounded" |
| When absolute scores cluster and stop separating candidates, compare trajectories against each other instead of against a threshold; preference between two runs stays informative where a score has already saturated. | sourced | `X-cap-evaluation-004` "trajectory-aware preferences reduce ties to roughly 35%, improving discriminative power, ranking stability, and data efficiency" |
| Write synthetic cases as scenarios with a persona and a multi-turn shape rather than as single prompts, because the failures worth catching in an agent appear across turns and tool calls, not in one answer. | sourced | `X-end-to-end-039` "testing AI agents in controlled environments that approximate multi-turn user interactions, tool usage, and varied personas" |
| Where the unit under test reaches its tools over a published protocol, drive the evaluation over that same protocol, so the cases exercise the boundary the unit actually uses instead of a test double of it. | sourced | `X-cap-evaluation-008` "allowing evaluation of agent behavior across standard tool-use patterns and external service calls" |
| As the operating consequence of the improvement loop TARGET describes: make passing this gate a precondition for a self-improvement loop applying its own change, not a report the loop writes afterwards. A loop that can rewrite the thing it is scored on and promote the baseline in the same pass has no gate at all. | sourced | `X-end-to-end-040` "A regression suite is the gate that makes a self-improvement loop safe to run automatically." |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-otel-trace-scoring-harness` | today | Proposed adapter, and a proposed entity id: PASS.md has no Evaluation row in B3, so kb/entities.jsonl carries no adapter entity for this capability and none may be added without rewriting the entity chain every written skill pins in provenance. What docs/skill-manifest.json records as today's adapter is a trace-native scoring harness that reads the ordered trace a run already emits and writes one gen_ai.evaluation.result per case, with register_case_set mapped onto its dataset registration, evaluate onto its experiment run, and score_trajectory onto its function-calling and trajectory evaluators. | Proposed: cannot score a run that emitted no trace, cannot be run where no collector or backend is reachable, and cannot produce a verdict a developer can reproduce on a laptop before pushing - so the gate is only as available as the observability stack behind it, and a case that fails there cannot be re-run in isolation. | Select the harness by configuration only, with no core edit, and run the identical registered case set through both; cap-evaluation-implement owns the migration and the wiring, this row records what the pair is and the axis it differs on. | claimed | `X-end-to-end-011`, `X-end-to-end-006` "OTel-native, agent function-calling eval" |
| `E-swap-candidate-local-fixture-replay-harness` | second | Proposed adapter, and a proposed entity id: a test-runner-shaped local harness with no collector and no server, where each case is a test function, the recorded run is a fixture on disk, and the assertion is the per-case verdict against the stored baseline. It reads the same CaseSet and writes the same EvaluationReport, so the corpus registered for the first adapter runs here unchanged. | Proposed: cannot score a production run it did not record, cannot aggregate across a fleet, and cannot show a trend over time without something else keeping the reports. That is the axis build-evidence asks for: the first adapter scores traces that a running collector delivers, the second scores fixtures on a filesystem with nothing running, so any operation shaped around a live trace stream fails outright here rather than degrading. | One conformance run puts the identical case set through both adapters against the same baseline and diffs per-case verdicts, transitions and refusal types; the merged report must show adapters_run >= 2 and verdict_divergence == 0. Design rule 3 is agentic-stack's and build-evidence's (F-b1-04); what is new here is that the second adapter is chosen for having no server at all, not for being a different evaluation product of the same shape. | claimed | `X-cap-evaluation-001`, `F-b1-04` "It works like Pytest for LLM applications, with test cases, reusable metrics, assertions, thresholds, and a runner designed for local development and CI/CD." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/evaluation/test.sh && ADAPTER=dryrun python3 harness/evaluation/conformance.py && ADAPTER=second python3 harness/evaluation/conformance.py |
| Expected | Measured by tools/measure.py at bf17237: exit 0; last lines:   ok   C12b an unregistered problem type falls back rather than being minted   [urn:agentic:problem:adapter-unavailable] \| conformance PASSED: 22/22 cases, adapter=second |
| Deliberate breakage | In harness/evaluation/interface.py outcome_for(), make a run that executed zero cases report passed instead of inconclusive, run the criterion (conformance case C6, a gate over a zero-case report cannot report success, fails on both adapters and the gate exits 1), then git checkout harness/evaluation/interface.py. |
| Expected failure | Measured by tools/measure.py at bf17237: exit 1; last lines:   ok   outcome and cases_executed are stated together in the report shape \| passed 47, failed 8 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-a7-03` "the deliberate breakage that proves the check can fail" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `cap-evaluation-implement` | Turn the cap-evaluation contract into something that runs here: which adapter is built first and on what, what the second one deliberately lacks, how a pipeline whose behavioural stages skipped and still went green becomes a gate with a stored baseline, and what a run must print before either adapter is allowed to refuse a change. | `references/cap-evaluation-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-ceremony`, `build-evidence`, `build-skill-authoring`, `cap-errors`, `cap-telemetry`, `core-components`

Used by: `compose-improvement-loop`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which entity ids should the two adapter rows carry, given that PASS.md B3 has no Evaluation row and so kb/entities.jsonl holds no adapter entity for this capability? | `python3 tools/kb.py tree` returns no capability, adapter or swap-candidate entity for Evaluation, and kb/meta.json's entity head is pinned in the provenance of every skill already written, so appending an entity would invalidate all of them. Applying 1-3-1: (1) reuse a swap candidate from the Telemetry row, which resolves but sends a reader to another capability's row; (2) mint proposed ids and say in each row that they are proposed, which is what cap-state-persistence (formerly cap-memory) and cap-human-interaction did for the same gap; (3) carry no adapters here and defer the pair to cap-evaluation-implement, which hides the pair from the reader who loads only the ideal facet. Recommendation and choice: (2). | Both rows carry minted ids and say so in maps_to. If an Evaluation row is ever added to the knowledge base, replace the ids and delete this question. | `T-t5-02`, `F-b1-04` "define the problem, identify the three best possible solutions that align to the goal" |
| Can the governing standard's version be verified from this environment, and is the evaluation-result carrier stable enough to pin a report format to? | A fetch of the GenAI semantic conventions recording the version string and the stability of the evaluation attributes on the date fetched. No specification was fetched in this session. | The Standards row reads unverified, and the report format is this platform's own shape with the carrier used for emission only, so a change in the conventions changes what is exported and not what a caller reads. | `X-cap-evaluation-006`, `F-b1-03` "In May 2026, the Cloud Native Computing Foundation (CNCF) graduated OpenTelemetry to Graduated status." |
| Does a refusal that is specific to evaluation - a case set that does not resolve, a baseline that was never promoted - need a registry row of its own, or is the registered criterion-unresolvable row the honest fit? | cap-errors owns the problem object and the closed registry, and core-components states the same typed-failure rule for a verdict (F-b3-13, F-b4-07). That registry, in docs/decomposition.md section 2.1.6, raises criterion-unresolvable when a criterion reference does not resolve; a rubric handle is a criterion reference, and a baseline that was never promoted is a reference that does not resolve either. No case has yet been found where a caller would branch differently. | Reuse criterion-unresolvable for an unresolvable rubric handle, case set or baseline, and document-invalid for a malformed evaluation request. No new suffix is proposed and none is stated anywhere in this skill. | `F-b3-13`, `F-b4-07` "Typed and machine-readable. Never parsed from prose" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation cap-evaluation author 2026-09-03 |
