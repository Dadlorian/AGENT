---
name: build-definition-of-done
description: The discipline that gives every piece a machine-checkable criterion, a deliberate breakage that makes that criterion fail, and the recorded output of both runs. Load it when you are writing or reviewing a Definition of done section, deciding what a green check actually proved, wiring a gate or CI stage that reports pass or fail, choosing the breakage that shows the check can fail, or judging whether a passing run checked anything at all. Also load it when a pipeline reports success with every behavioural stage skipped, when an assertion rests on an exit code alone, or when configuration was written in the documented place and you need evidence that it took effect rather than the file that declared it.
---

# build-definition-of-done

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Give every piece a criterion a machine can check, a breakage that makes that criterion fail, and the recorded output of both runs, so a green result is evidence rather than a habit. | sourced | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion." |

## Entities

| Entity |
|---|
| `E-ask-item-c-3` |
| `E-finding-a7-2` |
| `E-finding-a7-3` |
| `E-standard-in-toto` |
| `E-standard-dsse` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | - | `F-b3-09` |
| `E-standard-in-toto` | Statement v1 (unverified) | unverified | - | `F-b3-12`, `X-cross-structure-050`, `X-build-definition-of-done-004` |
| `E-standard-dsse` | unverified | unverified | - | `F-b3-12`, `X-cross-structure-050` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| state_done | a piece id, a criterion command, the expected output, a reversible breakage edit, and the expected failure | a definition-of-done record with status claimed (proposed operation) | proposed | - |
| run_criterion | a definition-of-done record and the tree under test | a gate-outcome carrying verdict pass, fail or inconclusive, a per-stage applicability report, and checked counts (proposed operation) | proposed | - |
| run_breakage | the same record, the same tree, with the breakage edit applied | a gate-outcome whose verdict is fail and whose output matches expected_failure; anything else means the criterion cannot fail (proposed operation) | proposed | - |
| attest_effective_configuration | an adapter at start-up | an in-toto Statement inside a DSSE envelope whose predicate is the configuration the adapter actually resolved (proposed operation) | proposed | - |
| compare_configuration | the declared configuration and the attested effective configuration | mismatched_keys; a non-empty list is a failed definition of done for that adapter (proposed operation) | proposed | - |

### Shapes (JSON Schema 2020-12)

**definition-of-done (proposed summary shape; the full schema, with the measured_at requirement and the breakage scope rule, is in references/definition-of-done-shapes.md)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:definition-of-done:0.1",
  "title": "definition-of-done",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "piece",
    "criterion",
    "expected",
    "breakage",
    "expected_failure",
    "status"
  ],
  "properties": {
    "piece": {
      "type": "string",
      "minLength": 1
    },
    "criterion": {
      "type": "object",
      "required": [
        "command",
        "asserts_nonzero_count_of"
      ],
      "properties": {
        "command": {
          "type": "string",
          "minLength": 1
        },
        "asserts_nonzero_count_of": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string"
          }
        },
        "criterion_ref": {
          "type": "string"
        }
      }
    },
    "expected": {
      "type": "string",
      "minLength": 1
    },
    "breakage": {
      "type": "object",
      "required": [
        "edit",
        "reversible"
      ],
      "properties": {
        "edit": {
          "type": "string",
          "minLength": 1
        },
        "reversible": {
          "const": true
        },
        "scope": {
          "enum": [
            "subject",
            "harness"
          ]
        }
      }
    },
    "expected_failure": {
      "type": "string",
      "minLength": 1
    },
    "status": {
      "enum": [
        "claimed",
        "measured"
      ]
    },
    "measured_at": {
      "type": "object",
      "required": [
        "session",
        "date",
        "tree_dirty"
      ]
    }
  }
}
```

**gate-outcome (proposed summary shape; the full schema and the ordered decision rule are in references/definition-of-done-shapes.md)** (proposed; sources: `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:gate-outcome:0.1",
  "title": "gate-outcome",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "piece",
    "verdict",
    "stages",
    "counts"
  ],
  "properties": {
    "piece": {
      "type": "string",
      "minLength": 1
    },
    "verdict": {
      "enum": [
        "pass",
        "fail",
        "inconclusive"
      ]
    },
    "stages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "name",
          "kind",
          "applicable",
          "ran",
          "checked"
        ],
        "properties": {
          "name": {
            "type": "string"
          },
          "kind": {
            "enum": [
              "structural",
              "behavioural"
            ]
          },
          "applicable": {
            "type": "boolean"
          },
          "ran": {
            "type": "boolean"
          },
          "checked": {
            "type": "integer",
            "minimum": 0
          },
          "skip_reason": {
            "type": "string"
          }
        }
      }
    },
    "counts": {
      "type": "object",
      "required": [
        "applicable_behavioural",
        "ran_behavioural",
        "checked_total"
      ],
      "properties": {
        "applicable_behavioural": {
          "type": "integer",
          "minimum": 0
        },
        "ran_behavioural": {
          "type": "integer",
          "minimum": 0
        },
        "checked_total": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "exit_code": {
      "type": "integer"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every piece carries a criterion a machine can check and the deliberate breakage that proves the check can fail. A criterion with no stated breakage is not finished. | sourced | `F-part-c-04`, `E-ask-item-c-3` "A criterion nothing can fail is not a criterion." |
| A criterion asserts on a non-zero count of things actually checked. An exit code alone is not an assertion: a nine-stage pipeline ran green because the generated work contained nothing those tools applied to. | sourced | `F-a7-03` "because the generated work contained nothing those tools apply to" |
| A gate reports which stages were applicable, and a run with zero applicable behavioural stages is inconclusive rather than green (proposed: this is our remedy for the measured failure in F-a7-03, expressed in the gate-outcome shape's counts.applicable_behavioural field). | proposed | `F-a7-03` "with every behavioural stage skipped" |
| agentic-stack already states the well-formedness finding (F-a7-03): structural stages settle well-formedness only. What this skill adds is the consequence for a gate - a verdict of pass may not rest on them alone, which is why the gate-outcome records kind, applicable, ran and checked per stage instead of a single exit code. | sourced | `F-a7-03` "Those establish well-formedness, not correctness." |
| The declared configuration is not evidence that the configuration took effect; configuration written in the documented place has been observed to validate, review correctly and change nothing at runtime. | sourced | `F-a7-04`, `E-finding-a7-3` "Values written to YAML validated, reviewed correctly, and had no runtime effect." |
| Proposed: each adapter emits at start-up the configuration it actually resolved, as an attested record whose predicate a validator compares against the declared configuration; a non-empty mismatched_keys fails that adapter's definition of done whatever the gate's exit code said. | proposed | `X-build-definition-of-done-005`, `X-cross-structure-050` "The values supplied in the attestation evidence are compared against reference values." |
| Proposed: the breakage edits the subject and nothing else, and is reversible. A breakage that also disables the harness makes every criterion fail and so proves nothing about this one. | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |
| One definition of done governs a piece whichever entry point reached it, because every cross-cutting concern is managed across the whole structure rather than per entry point. | sourced | `T-t2-03`, `F-b4-01` "managed across the entire structure, whichever entry point was used" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion body does not travel with the work under test. Per the rule agentic-stack states as design rule 6 (F-b1-07), the record carries criterion_ref, an opaque handle the runner resolves; a criterion the graded thing can read is a target. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| Proposed: the gate's exit code is not part of the contract and no consumer may read it as the verdict. The verdict is the three-valued gate-outcome.verdict field plus its counts; exit_code is kept for debugging only. | proposed | `F-a7-03` "Those establish well-formedness, not correctness." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from the row for your piece in the definition-of-done table and rewrite its criterion as one command with named counters, then fill a definition-of-done record: piece, criterion.command, criterion.asserts_nonzero_count_of, expected, breakage.edit, expected_failure, status. | The record, not the prose, is what a later reader and a later checker both read. A criterion nothing can fail is not a criterion, so the breakage is written at the same time as the criterion, never after. | sourced | `F-part-c-04`, `E-ask-item-c-3` "A criterion nothing can fail is not a criterion." |
| 2 | Make every assertion count things actually checked - cases run, fixtures rejected, adapters exercised, records verified - and require each named counter to be greater than zero. Never assert on an exit code alone. | A nine-stage pipeline ran with every behavioural stage skipped and reported green, because the generated work contained nothing those tools apply to. Counting is what separates a check that ran from a check that was present. | sourced | `F-a7-03`, `E-finding-a7-2` "because the generated work contained nothing those tools apply to" |
| 3 | Have the gate emit a gate-outcome: one entry per stage with kind structural or behavioural, applicable, ran and checked, plus counts. Resolve the verdict in order - any failed stage is fail; zero applicable behavioural stages is inconclusive; zero checked_total is inconclusive; otherwise pass. | Proposed: agentic-stack already carries the well-formedness finding (F-a7-03), so this step adds only what is new here - reporting applicability is what makes the structurally-green failure visible instead of silent, so a run carried by structural stages alone resolves to inconclusive rather than pass. | proposed | `F-a7-03` "Those establish well-formedness, not correctness." |
| 4 | Write the breakage as a single reversible edit inside the subject, apply it, run the criterion, and record the exact failing output including which counter moved. Then restore and run the criterion again. | An executable check is the only verification that a criterion has been met, and a pass is only meaningful once the same command has been seen to produce a fail. Restoring and re-running proves the breakage, not the harness, caused it. | sourced | `X-build-definition-of-done-002`, `F-part-c-04` "They are executable and can be run manually by a QA engineer or automated using a test framework, producing a result of pass or fail." |
| 5 | Label the record measured only after both runs happened, naming the session, the date and whether the tree was dirty; otherwise leave it claimed. Do not reword a claim into a measurement. | agentic-stack fixes claimed versus measured for the whole repo (F-part-c-08); this skill only adds where the line falls for a gate - a definition of done is claimed until the criterion and its breakage have both been run. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 6 | Have each adapter emit, at start-up, the configuration it actually resolved after every overlay - not the file it was handed - as an in-toto Statement inside a DSSE envelope, and run a validator that compares it against the declared configuration. | Proposed fold-in of the effective-configuration gap: configuration written in the documented place validated, reviewed correctly and had no runtime effect, so only the resolved value is evidence. Attested values compared against reference values is the established shape for this check. | proposed | `F-a7-04`, `X-build-definition-of-done-005`, `X-cross-structure-050` "Values written to YAML validated, reviewed correctly, and had no runtime effect." |
| 7 | Make the record structural rather than advisory: inject a definition-of-done record at admission, then validate it, so a piece that lacks one cannot be admitted at all. | Proposed: the mutate-then-validate ordering, where the mutating step is called first and can alter the resource before validation, is what turns an obligation into something a caller cannot skip. The platform applies each guarantee; a caller cannot decline them. | proposed | `X-cross-structure-023`, `F-b4-01` "Mutating webhooks are called first and can alter resource definitions" |
| 8 | Re-run the criterion on a schedule and on every change, and keep the outcomes; do not treat a single green run at build time as a standing property. | Proposed: a tamper-evident record only delivers its guarantee if something independently monitors it, and the same holds for a gate - the applicable stages change as the work changes, so yesterday's pass says nothing about today's tree. | proposed | `X-cross-structure-053` "Transparency logs are tamper-evident but not tamper-proof, so it becomes important to have a tool to monitor the transparency log for any evidence of tampering" |
| 9 | Apply one record per piece regardless of which entry point produced the work, and state the criterion once rather than per entry path. | State, telemetry and every cross-cutting concern are managed across the entire structure whichever entry point was used, and a gate that differs by entry point is an opt-out in disguise. | sourced | `T-t2-03`, `F-b4-01` "managed across the entire structure, whichever entry point was used" |
| 10 | If you cannot find a breakage that fails only this criterion, do not ship the criterion and do not stall: define the problem in one line, list the three best breakages, take the recommended one, and record the choice as an open question with the evidence that would settle it. | 1-3-1 keeps a blocked gate from becoming an unstated gate. The alternative in practice is a criterion shipped with no breakage, which is the exact defect this discipline exists to prevent. | sourced | `T-t5-02`, `F-part-c-04` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Keep the two apart: acceptance criteria are specific to one item, while the definition of done applies universally to all. Repo-wide gates belong in the second; per-piece assertions belong in the first. | sourced | `X-build-definition-of-done-001` "the definition of done applies universally to all" |
| State each criterion as a boolean invariant a pipeline can validate, so the assertion is configuration a gate reads rather than judgement a reviewer applies. | sourced | `X-build-definition-of-done-003` "Assertions and assumptions define the boundaries of acceptable behavior, allowing developers to configure CI/CD pipelines to validate changes simply and securely." |
| Keep the history of criterion runs across build variants; without it a red result cannot be attributed to the change rather than to the harness. | sourced | `X-build-definition-of-done-006` "maintaining a representation of recent test history for each combination of a test and build flags" |
| Let the evidence corroborate: a property proven at the design level and checked again at the implementation level is worth more than either alone, because evidence from one process supports evidence from the others. | sourced | `X-build-definition-of-done-008` "Evidence generated by one V&V process supports evidence generated by the others" |
| Prefer an attestation format a tool you did not write can verify; the framework generates verifiable claims about how a piece of software was produced, which is what makes an outside check possible at all. | sourced | `X-build-definition-of-done-004`, `X-cross-structure-050` "The in-toto Attestation Framework provides a specification for generating verifiable claims about any aspect of how a piece of software is produced." |
| Proposed: name in the record which counter the breakage is expected to move. A breakage described only as 'the test fails' cannot be distinguished from a broken harness when someone re-runs it a year later. | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |
| Proposed: keep the three attestation layers distinct when recording configuration evidence - the envelope, the statement header, and the predicate that carries the payload - so a validator can check the signature without understanding our fields. | proposed | `X-cross-structure-050` "the in-toto Statement: the attestation header, and the predicate: the attestation payload" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Run from the repository root: python3 -c "import json,pathlib,sys; root=pathlib.Path(sys.argv[1]); dirs=sorted(p for p in root.iterdir() if p.is_dir()); req=('criterion','expected','breakage','expected_failure','status'); dod=lambda p: (json.loads((p/'skill.json').read_text()).get('definition_of_done') or {}) if (p/'skill.json').is_file() else {}; missing=[p.name for p in dirs if not all(str(dod(p).get(k) or '').strip() for k in req)]; print('skills_total',len(dirs),'skills_checked',len(dirs),'missing',len(missing),missing); sys.exit(1 if missing or not dirs else 0)" .claude/skills . It asserts skills_checked == skills_total (every directory under .claude/skills is opened), missing == 0 (every skill.json carries a non-empty criterion, expected, breakage, expected_failure and status), and skills_checked > 0 (an empty tree exits 1 rather than passing vacuously). |
| Expected | Prints 'skills_total N skills_checked N missing 0 []' with N greater than 0, and exits 0. |
| Deliberate breakage | Two, each applied to a copy of .claude/skills and the command re-run against that copy. (a) Add a skill directory build-no-breakage whose skill.json has a criterion and an expected result but an empty breakage and empty expected_failure. (b) Point the command at an empty skills directory, so nothing is checked. |
| Expected failure | Measured in session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 on 2026-09-03 in /home/user/AGENT. Baseline against .claude/skills printed: skills_total 4 skills_checked 4 missing 0 [] , exit 0; re-run after this skill landed printed skills_total 6 skills_checked 6 missing 0 [] , exit 0. N moves as skills land, so the assertions are on missing and on skills_checked > 0, never on N. Breakage (a), a copy of .claude/skills with an extra build-no-breakage directory whose definition_of_done had an empty breakage and empty expected_failure, printed: skills_total 5 skills_checked 5 missing 1 [build-no-breakage] , exit 1. Breakage (b), the same command pointed at an empty skills directory, printed: skills_total 0 skills_checked 0 missing 0 [] , exit 1 - the vacuous-pass guard fires because skills_checked is 0, so an empty tree cannot report green. Both breakages were applied to copies under the session scratchpad; no repository file was edited, so no restore was needed and the tree stayed clean. |
| Status | measured |
| Evidence | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion." |

## Composes with

Builds on: `agentic-stack`

Used by: `build-entry-conformance`, `build-interface-versioning`, `build-simplicity-budget`, `cap-agent-runtime`, `cap-agent-runtime-implement`, `cap-capability-packaging`, `cap-capability-packaging-implement`, `cap-capability-registry`, `cap-capability-registry-implement`, `cap-document-validation`, `cap-document-validation-implement`, `cap-durable-execution`, `cap-durable-execution-implement`, `cap-errors`, `cap-errors-implement`, `cap-evaluation`, `cap-evaluation-implement`, `cap-human-interaction`, `cap-human-interaction-implement`, `cap-idempotency`, `cap-idempotency-implement`, `cap-identity`, `cap-identity-implement`, `cap-isolation`, `cap-isolation-implement`, `cap-mandate-broker`, `cap-mandate-broker-implement`, `cap-memory`, `cap-memory-implement`, `cap-model-access`, `cap-model-access-implement`, `cap-policy`, `cap-policy-implement`, `cap-provenance`, `cap-provenance-implement`, `cap-scheduling`, `cap-scheduling-implement`, `cap-state-persistence`, `cap-state-persistence-implement`, `cap-telemetry`, `cap-telemetry-implement`, `cap-tool-access`, `cap-tool-access-implement`, `cap-work-intake`, `cap-work-intake-implement`, `compose-agent`, `compose-agent-implement`, `compose-approval`, `compose-approval-implement`, `compose-improvement-loop`, `compose-improvement-loop-implement`, `compose-loop`, `compose-loop-implement`, `compose-operators`, `compose-operators-implement`, `core-document`, `core-document-implement`, `core-graph`, `core-graph-implement`, `core-judge`, `core-judge-implement`, `core-ledger`, `core-ledger-implement`, `core-planner`, `core-planner-implement`, `seam-dispatch`, `seam-dispatch-implement`, `seam-state`, `seam-state-implement`, `xc-audit-trail`, `xc-audit-trail-implement`, `xc-budget`, `xc-budget-implement`, `xc-compensation`, `xc-compensation-implement`, `xc-correlation`, `xc-correlation-implement`, `xc-enforcement-chain`, `xc-enforcement-chain-implement`, `xc-idempotency-lease`, `xc-idempotency-lease-implement`, `xc-identity-delegation`, `xc-identity-delegation-implement`, `xc-policy-gate`, `xc-policy-gate-implement`, `xc-provenance-chain`, `xc-provenance-chain-implement`, `xc-tenancy`, `xc-tenancy-implement`, `xc-typed-errors`, `xc-typed-errors-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which of the nine pipeline stages are behavioural for a given piece, and who decides applicability - the stage itself or the record? | Run the gate over a corpus of at least 50 changes of mixed kind and count, per stage, how often it self-reports not applicable versus how often the piece's record declares it out of scope. A large gap means the stage's own judgement cannot be trusted as the applicability signal. | Proposed: the stage self-reports applicable and the record may only narrow it, never widen it; a stage that cannot report applicability is counted as not applicable and therefore pushes the verdict towards inconclusive. | `F-a7-03` "with every behavioural stage skipped" |
| Can effective-configuration attestation be produced by every adapter, or only by those whose configuration resolution is observable from inside the process? | For each adapter, attempt to dump the resolved configuration at start-up and compare it with the declared file; an adapter that cannot expose its resolved values is the counterexample. This agent has no access to the running host, so nothing here has been attempted. | Proposed: an adapter that cannot emit its effective configuration is recorded as unverified for the configuration half of its definition of done, and that half stays claimed rather than being dropped. | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
