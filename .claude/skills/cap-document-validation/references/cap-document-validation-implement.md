---
name: "cap-document-validation-implement"
description: "How to build the document-validation capability on this stack: the adapter that runs today, a second adapter whose execution model differs, the migration off the keyword-subset checks that run now, where validation is wired so no caller can decline it, and the conformance run that decides whether either adapter may serve. Load it when you are writing or reviewing that adapter, when a schema check is about to be hand-rolled inside a component, when someone asks 'where does the checking actually happen', 'can we replace the checker without touching the core', or 'why did this document pass here and fail there', and before recording any conformance result as passing."
---

# cap-document-validation-implement (folded into `cap-document-validation`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what cap-document-validation specifies: two adapters selected by configuration, one conformance run that judges both, and the wiring that puts validation before spend rather than beside it. | sourced | `F-b3-09`, `F-b1-04` "any 2020-12 validator" |

## Entities

| Entity |
|---|
| `E-capability-document-validation` |
| `E-standard-json-schema-2020-12` |
| `E-adapter-in-place` |
| `E-swap-candidate-any-2020-12-validator` |

## Contract

### Shapes (JSON Schema 2020-12)

**validator-adapter-binding (proposed shape; the migration corpus procedure and the wiring table are in references/cap-document-validation-implement-implementation-notes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "declared_dialect",
    "schema_store",
    "execution_model"
  ],
  "properties": {
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "declared_dialect": {
      "type": "string",
      "minLength": 1
    },
    "schema_store": {
      "type": "string",
      "minLength": 1
    },
    "prepared_cache": {
      "type": "boolean",
      "default": true
    },
    "execution_model": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "start_and_teardown_cost",
        "processes_required_for_progress"
      ],
      "properties": {
        "start_and_teardown_cost": {
          "enum": [
            "schema read per call",
            "schema compiled ahead of use"
          ]
        },
        "processes_required_for_progress": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| cap-document-validation owns the contract (F-b3-09, F-b3-01). This skill adds only how it is built: an implementation that changes the outcome shape, adds a keyword, or narrows the dialect has produced a defect, not an extension. | sourced | `F-b3-01`, `F-b3-09` "The middle column is the contract" |
| Per the boundary-drawn-wrong finding agentic-stack and build-adapter-pair carry (F-meta-04), both adapters are chosen by a binding record read as configuration. If selecting one requires editing a file the core owns, the boundary is drawn wrong and the pair has found the defect it exists to find. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| build-adapter-pair states rule 4 (F-b1-05); the consequence here is that the schemas this platform publishes are plain dialect documents a third party validates with their own tooling, so integrating with us never means importing a checker of ours. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| agentic-stack already states this as design rule 7 (F-b1-08, F-b4-01): telemetry, policy, provenance and budget are applied by the platform, not requested by the caller. What this skill adds, as its own consequence and proposed: for validation that means the admission path applies it before the first metered call, and there is no flag, header or field by which a caller can ask to skip it. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record states the labelling rule (F-part-c-08); the consequence here is that a conformance result is claimed until a run is attached naming the suite revision, the adapter roles and the counts, and no amount of rewording upgrades it. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Apply build-adapter-pair: this pair's differing axes (start_and_teardown_cost, processes_required_for_progress) are recorded in the adapters section below and in the second adapter's swap_procedure; this row does not restate them. Two bindings identical on every axis are one adapter written twice and fail the pair check. proposed pointer, see that skill. | proposed | `F-b1-04` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: cap-document-validation already owns this exclusion for the adapter's native error objects and library-specific wording; applied at the pair level, which adapter served a call is not visible to a caller except as the outcome's adapter_role field, and never as a difference in the errors it reads. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put every validator behind the binding record and keep the import of any checking library inside its own adapter directory; core and seam modules import the capability's operations only. | agentic-stack states design rule 1 as a test (F-b1-02): a product name inside core code fails it, and a direct import is that name in executable form. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| 2 | Build the adapter that runs today as a thin wrapper: prepare a schema once per schema URI and dialect, expose validate, check_schema and dialect_in_effect, and translate the library's native errors into the outcome shape at the wrapper's edge. | cap-document-validation carries the row that records this adapter as already in place (F-b3-09), so the work is not writing a validator but confining one, and the translation at the edge is what stops the library's error class becoming the platform's error contract. | sourced | `F-b3-09` "JSON Schema 2020-12 \| in place" |
| 3 | Build the second adapter on a different execution model rather than a different vendor: a validator that compiles the schema ahead of use, in a natively compiled runtime, reached out of the caller's process. Record both adapters' values for the two axes in their binding records. | build-adapter-pair owns this discipline (F-b1-04). The consequence here is specific: two tree-walking validators in one runtime would leave the interface free to keep any in-process assumption, and the compiled out-of-process adapter is what forces the schema store and the prepared handle to be addressable rather than object references. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 4 | Proposed migration: the reference consumption example currently checks documents with a hand-rolled routine that supports only the keywords its own schemas use and ignores the rest. Run it and the new adapter over the same corpus of instances, diff the outcomes, and require the adapter to reject a superset before the old routine is deleted. | Proposed: a checker that ignores unknown keywords accepts documents its schema forbids, so the migration's risk is not new rejections but the old acceptances that were never real passes; the diff is what turns that into a list. Research query: is there a recorded migration record (kb/ceremonies or an evidence record) from another capability in this platform that ran a shadow resolver or a diffed cutover the same way, confirming this is the platform's own established migration pattern rather than invented here? | proposed | - |
| 5 | Wire validation at admission: validate the entry document before any metered call, record the outcome with the correlation attribute the platform sets at dispatch, and return a typed failure rather than raising the adapter's exception. | agentic-stack states that cross-cutting guarantees are applied not requested (F-b1-08) and that correlation must ride on an explicit attribute; a rejection that is not recorded is a rejection nobody can count. | sourced | `F-b4-01`, `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| 6 | Write one conformance run parameterised over the binding records, point it at a vendored copy of the official suite for the dialect at a pinned revision, and run it for every adapter on every change. | cap-document-validation names the official suite this pins (X-cap-document-validation-004). One suite over two adapters is what makes the swap a tested property; pinning the suite is what makes a new failure attributable to our change rather than to the suite moving underneath it. | sourced | `X-cap-document-validation-004` "The JSON Schema Test Suite is a language agnostic test suite for validator implementations" |
| 7 | Have each adapter report, at start-up, the dialect it actually resolved, and compare it against its binding record's declared dialect; a mismatch fails the definition of done for that adapter. | build-definition-of-done requires the effective configuration to be attested rather than assumed, and cap-document-validation carries why this capability in particular needs it (F-a7-04). | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 8 | Proposed: open references/cap-document-validation-implement-implementation-notes.md when running the migration diff, wiring the admission path, or reviewing a binding record. The body of this skill is enough to build and judge the pair without it. | Proposed: the migration corpus procedure and the wiring table are longer than the body's budget and are needed only while doing those two jobs. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| cap-document-validation and build-evidence-record already state the configuration finding for this capability (F-a7-04). What this skill adds, as its own consequence and proposed: make the comparison a start-up assertion rather than a review item, because a validator silently bound to an older draft passes almost every document and fails only on the newest keywords, which is the shape of a defect that ships. | sourced | `F-a7-04` "had no runtime effect" |
| Proposed: vendor the official suite at a pinned revision and upgrade it deliberately, in its own change, so a red conformance run is always attributable to one of two things and you know which. Research query: is there a recorded pin (a version file, lockfile entry or CI config) for the JSON Schema Test Suite on this repository, which would let this row cite the actual pinned revision instead of describing the practice in the abstract? | proposed | - |
| Proposed: never add a keyword the dialect does not define. A custom keyword makes every other conformant validator wrong about our documents, which is the swap this pair exists to keep possible. Research query: is there a recorded schema in this repository or its conformance suite that was checked and found free of non-dialect keywords, confirming this rule was actually enforced rather than only stated? | proposed | - |
| Proposed, over the cross-language dialect row cap-document-validation carries (X-cap-document-validation-006): run both adapters over the platform's own instances, not only over the suite. The suite tests the validator; the diff tests whether our schemas mean the same thing to implementations in other language runtimes, which is the property the swap depends on. | sourced | `X-cap-document-validation-006` "implementations in all major languages can validate against the same dialect" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-in-place` | today | validate, check_schema and dialect_in_effect served in-process by a Python jsonschema validator loaded inside the adapter directory. cap-document-validation carries the row that records this adapter only as in place (F-b3-09); naming the library is the manifest's entry and is proposed here. | Proposed: cannot serve a caller in another runtime without a process boundary being added, and reads the schema on the interpreted path, so its per-instance cost scales with schema size rather than being paid once at compile time. | Change the binding record's role and schema_store, restart, confirm the reported dialect matches the declared one, then run the conformance suite and the instance diff. No core file is edited. | claimed | `F-b3-09` "JSON Schema 2020-12 \| in place" |
| `E-swap-candidate-any-2020-12-validator` | second | the same three operations served by a compiled-schema validator in a different language runtime, for example a Rust or Go 2020-12 implementation invoked out of process or through a foreign function boundary. | Proposed: cannot receive the caller's live objects, exception types or file handles, and cannot be handed a schema outside the declared dialect - so anything it cannot implement was an in-process assumption leaking into the contract. | cap-document-validation chooses the pair on execution model (F-b3-09, F-b1-04). Its binding record differs from today's on start_and_teardown_cost (schema compiled ahead of use versus schema read per call) and on processes_required_for_progress. One parameterised conformance run covers both, and the pair stays claimed until that run is recorded. | claimed | `F-b3-09`, `F-b1-04` "any 2020-12 validator" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/document-validation/test.sh && python3 harness/document-validation/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 16d354c: exit 0; last lines:   adapter=compiled-schema checker (compile once, check many) cases=14 passed=14 prepares=6 schema_reads=0 dialect_in_effect=https://json-schema.org/draft/2020-12/schema product_hits=0 \| conformance PASSED: 28/28 cases, 2 binding(s) |
| Deliberate breakage | Import a validator library (jsonschema) directly at the top of harness/document-validation/call.py and change nothing else (the harness README's breakage); restore with git checkout -- harness/document-validation/call.py. |
| Expected failure | Measured by tools/measure.py at 16d354c: exit 1; last lines:   FAIL hits not counted \| passed 7, failed 17 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-02` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-document-validation`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which adapter is the default on the admission path? | Measure, for the entry envelope schema under both bindings, per-instance validation latency at the tail, the cost of the first call after start-up, and the number of processes that must be running for an admission to succeed. | The adapter that runs today, because processes_required_for_progress for it is zero beyond the caller; the second adapter stays a conformance-run peer until the measurement says otherwise. | `F-b3-09` "in place" |
| Should the second adapter run in shadow on live admissions to detect divergence, or only in the conformance run? | Count outcome divergences between the two adapters over a corpus of real admissions, and measure the added latency of shadowing on the admission path. | Conformance run only. Proposed: shadowing doubles the work on the path that must never be the reason validation gets switched off, and the suite plus the instance diff already cover the known divergence sources. | `X-cap-document-validation-004` "several hundred tests for each version totaling over 6,000 tests" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
