# Document validation: migration, wiring, binding review

Proposed throughout unless a kb id is named. The body of `cap-document-validation-implement` is enough
to build and judge the adapter pair; open this file while running the migration diff, wiring the
admission path, or reviewing a binding record. Ids resolve with `python3 tools/kb.py show <id>`.

## 1. Migration corpus procedure (proposed)

What runs now, in the reference consumption example, is a hand-rolled routine that supports only the
keywords its own schemas use and ignores the rest. That is not a defect to be embarrassed about; it is
a dependency-free example. It is a defect to keep once the capability exists, because ignoring unknown
keywords means accepting documents the schema forbids.

| Step | Action | Stop condition |
|---|---|---|
| 1 | Collect a corpus: every instance the platform has admitted, every fixture under the schema store, and every negative fixture. | Corpus size recorded; fewer than a few hundred instances means the diff proves little. |
| 2 | Run the old routine and the new adapter over the corpus, storing both outcomes per instance. | Both runs complete; no instance is skipped. |
| 3 | Diff. Partition into: agreed-valid, agreed-invalid, newly-rejected, newly-accepted. | Every instance lands in exactly one partition. |
| 4 | Read every newly-rejected instance by hand. Each is either a real defect the old routine missed, or a schema that was wrong. | Zero unexplained newly-rejected instances. |
| 5 | Treat any newly-accepted instance as a blocker. The new adapter must reject a superset. | `newly_accepted == 0`. |
| 6 | Delete the old routine in the same change that makes the adapter the admission path. | No second checker survives; two checkers means two answers. |

## 2. Wiring table: where validation sits (proposed)

Cross-cutting concerns are applied by the platform, not requested by the caller (`F-b1-08`, `F-b4-01`).
The placement below is what makes that true for this capability.

| Concern | Placement relative to validation | Why this order |
|---|---|---|
| Identity | Resolved before validation | The rejection record needs an actor, or a flood of malformed submissions is unattributable. |
| Budget | Validation happens before the first metered call | A malformed document must cost nothing but the check itself. |
| Policy | After validation, before dispatch | A policy rule reads fields; evaluating rules against an unvalidated document is evaluating rules against anything. |
| Telemetry | The outcome is recorded with the correlation attribute set at dispatch | Trace parentage does not survive the agent boundary (`F-a7-02`, stated in agentic-stack). |
| Errors | The typed failure is produced by the consumer of the outcome, not by the adapter | Keeps the adapter replaceable by one in another language runtime. |
| Provenance | The schema URI, dialect and adapter role are part of the admission record | Otherwise nobody can say later which rules a document was admitted under. |

## 3. Binding record review checklist (proposed)

Reviewing a `validator-adapter-binding` (shape in the skill body):

1. `declared_dialect` is a dialect URI, not a version word, and matches what the adapter reports at
   start-up. A mismatch is a failed definition of done, not a warning (`F-a7-04`).
2. `schema_store` resolves every reference the platform's schemas make, offline. If a reference points
   outside it, that is the open question in `cap-document-validation`, not a local decision.
3. `execution_model` differs from the other binding on at least one axis. Two bindings identical on
   every axis are one adapter written twice (`F-b1-04`).
4. `prepared_cache` true, with the reuse count observable. A prepared handle serving one instance is a
   cache that is not working, and the cost shows up on the admission path first.
5. Nothing in the record names a library. The library lives inside its adapter directory; the record
   names roles, dialects and paths (`F-part-c-09`, stated in agentic-stack).

## 4. What a reviewer should refuse

- A validation call in a component that also does the work being validated. One admission point.
- A caller-supplied flag that skips validation, under any name, including a test-only one.
- An outcome field that only one adapter can populate, unless it is optional and marked so.
- A conformance result labelled measured with no attached run (`F-part-c-08`).
