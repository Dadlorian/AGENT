# Binding records, wiring, redaction and the dual-grade migration

Long material for `core-judge-implement`. Everything here is **proposed** unless a kb id is given beside
it. The skill body is enough to review a design and to run the definition of done; open this file when
writing the sampler, the redaction, the binding records, the cross-cutting wiring or the migration.

Resolve every id below with `python3 tools/kb.py show <id>`.

## 1. The two binding records (proposed)

```json
{
  "role": "today",
  "check_kinds_served": ["command_exit", "output_match", "artifact_present"],
  "determinism": {"guaranteed_by": "construction"},
  "serves_closing_grading": true,
  "differs_in_execution_model": [
    {"axis": "processes_required_for_progress", "today_value": "zero beyond the local check runner", "second_value": "one served model endpoint", "measured": false},
    {"axis": "replay_determinism_required", "today_value": "identical verdict by construction", "second_value": "identical verdict only under recorded pins", "measured": false},
    {"axis": "unit_of_resource_granted", "today_value": "a local process slice", "second_value": "a metered call against the envelope ceiling", "measured": false}
  ]
}
```

```json
{
  "role": "second",
  "check_kinds_served": ["command_exit", "output_match", "artifact_present", "rubric_judgement"],
  "determinism": {
    "guaranteed_by": "pinned_configuration",
    "pins": ["model_class", "decoding_settings", "prompt_version", "seed"]
  },
  "serves_closing_grading": false,
  "differs_in_execution_model": "as above, from the second_value column"
}
```

`check_kinds_served` is what makes the conformance comparison meaningful: the engines are compared only on
the kinds both claim, and `rubric_judgement` is the kind the deterministic engine honestly cannot decide -
deterministic checks are reliable but narrow (X-core-judge-005). A binding that claimed a kind it cannot
decide would report agreement it did not earn.

## 2. Cross-cutting wiring, per concern (proposed)

| Concern | Where it attaches on the grading path | What a caller cannot do |
|---|---|---|
| Telemetry | correlation stamped as an explicit attribute where the grading is constructed (F-a7-02) | omit the attribute; it is set by the constructor, not passed in |
| Policy | consulted before any metered call an engine makes, so a refusal costs nothing (F-b4-04) | reach an engine without passing the gate |
| Provenance | the grading record is attested to the code version, criterion version and actor (F-b4-05) | record a verdict with no attestation |
| Budget | the ceiling is read from the envelope; a grading that would cross it stops (F-b4-02) | raise the ceiling from a criterion set |
| Errors | an unresolvable handle returns `urn:agentic:problem:criterion-unresolvable`, a registered row (F-b4-07) | receive a prose failure |
| Identity | the actor and delegation chain ride on the grading record (F-b4-03) | grade anonymously |
| Idempotency | a re-submitted grading under the same key returns the recorded verdict (F-b4-08) | double-charge a re-grade |

Design rule 7 (F-b1-08) is what makes this a table of placements rather than a table of options.

## 3. Redaction, and why the second engine needs it (proposed)

The deterministic engine never serialises the criterion anywhere; the model-graded engine puts it in a
prompt by definition. Three rules keep that from becoming a leak:

1. The prompt is built inside the Judge process and is never written to a trace payload the graded unit's
   tooling can read; only a prompt hash and the criterion version are emitted.
2. The engine's response is reduced to check ids and a verdict before it leaves the process, so a model's
   own restatement of the criterion cannot travel in `detail`.
3. The lint in the skill body greps the criterion strings of a run across requests, step payloads, verdict
   details, prompt logs and trace payloads. `criterion_hits` counts all of them, not only requests.

Rule 6 is stated once, in `core-judge`; these three are the build-level consequences of it on a path that
did not exist before the second engine.

## 4. The dual-grade migration (proposed)

| Stage | What runs | Cut-over condition |
|---|---|---|
| 1. shadow | the gate that decides done today, plus the Judge on the same work, verdicts recorded, neither blocking | the Judge produced a grading record for every unit |
| 2. compare | both, with every disagreement triaged into: criterion set wrong, check kind unserved, or gate was green on nothing | `checks_applied_min > 0` over the whole corpus |
| 3. authoritative | the Judge decides; the gate still runs as a check kind inside the criterion set | one full retention window with no unexplained disagreement |
| 4. retire | the gate runs only as the deterministic engine behind the binding | - |

The measured reason for staging it this way is F-a7-03: a gate can be structurally green and mean nothing,
so agreement between the two during stage 2 is not evidence unless `checks_applied` was non-zero on both
sides. Agreement on nothing is the failure being migrated away from.

## 5. What the conformance run must not do (proposed)

- Do not let the two engines share a criterion resolution cache; a mismatch caused by one engine reading a
  stale set is a bug the report would attribute to the engine.
- Do not compare engines on a kind only one serves; compare on `check_kinds_served` intersection, and
  report the difference separately so an engine cannot pass by claiming less.
- Do not seed the sampler from the wall clock in the harness, which would make `verdicts_distinct` a
  property of how fast the runs happened.
- Do not report `adapters_run=2` without asserting the engine actually in effect per run; configuration
  written in the documented place has been observed to have no runtime effect (F-a7-04).
