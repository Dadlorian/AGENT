---
name: cap-document-validation
description: The document-validation capability: one contract for checking a declared shape against a published schema dialect, JSON Schema 2020-12, with the operations the core imports, the outcome shape, and the criteria that decide whether a candidate validator is good enough. Load it before writing or changing any schema this platform ships, when deciding whether a payload may enter, when someone asks 'is this envelope well-formed', 'why was this request rejected before it ran', 'which checker do we use and can we replace it', or 'the file in the repo no longer matches the data', and whenever a boundary is about to grow its own hand-written field checks instead of a declared schema.
---

# cap-document-validation

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for validating a declared shape against a published schema dialect, so the core imports the validation interface and any conformant validator can serve it. | sourced | `F-b3-09`, `F-b3-01` "The middle column is the contract" |

## Entities

| Entity |
|---|
| `E-capability-document-validation` |
| `E-standard-json-schema-2020-12` |
| `E-adapter-in-place` |
| `E-swap-candidate-any-2020-12-validator` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | https://json-schema.org/draft/2020-12 | `F-b3-09`, `X-cap-document-validation-001` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| validate | an instance document, the schema resource it is validated against, and the dialect that schema declares | an outcome carrying valid true or false and, when false, every violation located inside the instance, produced in one pass | sourced | `X-cap-document-validation-005` "All errors are reported in a single pass instead of stopping at the first failure." |
| check_schema | a schema resource and the dialect it declares | whether the schema is itself a valid schema of that dialect, judged against the dialect's meta-schema | sourced | `X-cap-document-validation-003` "validates the schemas themselves against the JSON Schema meta-schema" |
| prepare (proposed operation) | a schema resource plus the schema store its references resolve against | a reusable prepared-validator handle, so the cost of reading the schema is paid once and reused across instances (proposed) | proposed | - |
| dialect_in_effect (proposed operation) | a prepared-validator handle | the dialect URI the adapter actually resolved at run time, which is not necessarily the one the schema file declares (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**validation-request (proposed summary shape; the full shape is in references/document-validation-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:request:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_uri",
    "dialect",
    "instance"
  ],
  "properties": {
    "schema_uri": {
      "type": "string",
      "minLength": 1
    },
    "dialect": {
      "type": "string",
      "minLength": 1
    },
    "instance": {},
    "offline": {
      "type": "boolean",
      "default": true
    }
  }
}
```

**validation-outcome (proposed summary shape; the error unit and the conformance report are in references/document-validation-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:outcome:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "valid",
    "dialect",
    "schema_uri",
    "errors",
    "keywords_checked"
  ],
  "properties": {
    "valid": {
      "type": "boolean"
    },
    "dialect": {
      "type": "string"
    },
    "schema_uri": {
      "type": "string"
    },
    "keywords_checked": {
      "type": "integer",
      "minimum": 0
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "instance_location",
          "keyword_location",
          "message"
        ],
        "properties": {
          "instance_location": {
            "type": "string"
          },
          "keyword_location": {
            "type": "string"
          },
          "absolute_keyword_location": {
            "type": "string"
          },
          "message": {
            "type": "string"
          }
        }
      }
    }
  }
}
```

**worked example 1 (proposed): a person submits a malformed entry and gets everything wrong with it, at once [caller's view, folded from cap-document-validation-use]** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:example:rejected:0.1",
  "title": "Rejected submission, end to end (proposed)",
  "type": "object",
  "examples": [
    {
      "sent": {
        "schema_uri": "urn:agentic:seam:entry:0.1",
        "instance": {
          "kind": "human",
          "intent": "restart the ingest job",
          "budget": {
            "ceiling_micros": "50000"
          }
        }
      },
      "outcome": {
        "valid": false,
        "errors": [
          {
            "instance_location": "/actor",
            "keyword_location": "/required",
            "message": "required property 'actor' is missing"
          },
          {
            "instance_location": "/budget/ceiling_micros",
            "keyword_location": "/properties/budget/properties/ceiling_micros/type",
            "message": "expected integer, got string"
          }
        ]
      },
      "received_on_the_wire": {
        "media_type": "application/problem+json",
        "type": "urn:agentic:problem:document-invalid",
        "title": "Document failed schema validation",
        "status": 422,
        "detail": "2 violations; see errors",
        "errors": "the list above, unchanged"
      },
      "what_the_caller_does": "fixes both violations in one edit and resubmits; there is no second round of discovery"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The capability is the contract and the validator is the adapter: what the core imports is 'a declared shape is validated against a published dialect', and the dialect that governs it is JSON Schema 2020-12. | sourced | `F-b3-09`, `F-b3-01` "Document validation** \| JSON Schema 2020-12" |
| Every schema resource declares its dialect in band, so no instance is ever validated against an assumed dialect and a schema with no declared dialect is rejected rather than defaulted. | sourced | `X-cap-document-validation-001` "Declare your schemas to have the dialect metaschema using the $schema keyword" |
| A failed validation reports every violation, each located inside the instance, rather than aborting at the first one: a caller repairing a document needs the whole list, not the first line of it. | sourced | `X-cap-document-validation-005` "Error reports list failures using RFC 6901 JSON Pointer notation in the path field" |
| Conformance is decided by the official language-agnostic test suite for the dialect, never by fixtures we wrote: our fixtures test our schemas, the suite tests the validator. | sourced | `X-cap-document-validation-004` "The JSON Schema Test Suite is a language agnostic test suite for validator implementations" |
| agentic-stack states design rule 3 as a test (F-b1-04); the consequence here is that the swap candidate is a class, not a product - any 2020-12 validator - so an adapter that needs a schema written outside the declared dialect, or a schema keyword of its own, has failed the interface rather than extended it. | sourced | `F-b3-09`, `F-b1-04` "any 2020-12 validator" |
| Proposed: validation is a pure offline function of instance, schema and dialect. Remote references are resolved into the supplied schema store before the call, no fetch happens while validating, and the same three inputs always produce the same outcome. | proposed | - |
| Proposed: what crosses the interface is the outcome shape defined here, never an adapter's own exception type, error class or message string; two conformant adapters must be indistinguishable to a caller that reads only the outcome. | proposed | - |
| All three ways in reach the same check: a person, an agent, and an internal or external event submit through one envelope, against one shape identifier, and read one outcome shape back. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t6-02` "All four enter through the same shape" |
| Tightening a schema, replacing the validator behind the interface, and changing how a rejection is rendered are three independent changes; none of them alters what a caller sends or the outcome shape they read. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the adapter's native error objects, exception types and library-specific wording. A caller that pattern-matches on one adapter's message text has bound itself to that adapter. | proposed | - |
| Proposed: translating a validation outcome into a transport error body is not part of this interface. That mapping belongs to the consumer, and keeping it out is what lets the validator be replaced by one in another language runtime. | proposed | - |
| Proposed: the schema store's on-disk layout and the internal form of a prepared-validator handle. Both are adapter detail; only the schema URI and the dialect are contractual. | proposed | - |
| Proposed: a schema, a dialect declaration and a validation outcome never carry the criterion a judged result will be scored against. agentic-stack states design rule 6 (F-b1-07); the consequence here is that a schema says what shape is admissible and the outcome says which keywords failed, so validating a document can never be the channel that shows an agent its grading rule. | proposed | `F-b1-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability plus its standard before any validator is named: 'a declared shape is validated against a published dialect, per JSON Schema 2020-12, version unverified'. Read the row the way the table's template row is read. | The contract has to survive the implementation, so that when a validation need changes the adapter changes and the core does not. | sourced | `F-b3-09`, `F-b3-18` "the adapter changes and the core does not" |
| 2 | Give every schema resource an explicit dialect declaration and a stable identifier, and reject a schema that declares no dialect instead of assuming one. | An assumed dialect is how a document silently gets checked by the wrong rules; declaring it in band makes the check auditable from the document alone. | sourced | `X-cap-document-validation-001` "Declare your schemas to have the dialect metaschema using the $schema keyword" |
| 3 | Keep the schema resources together in one directory and add a gate stage that validates the schemas themselves against the dialect's meta-schema before any instance is validated against them. | A malformed schema does not fail loudly; it quietly accepts documents it should reject, so the schemas need a check of their own. | sourced | `X-cap-document-validation-003` "Keep all schemas in a schemas/ directory at the repo root, and add a CI step that validates the schemas themselves against the JSON Schema meta-schema." |
| 4 | Judge a candidate validator by running the official suite for the dialect and requiring every required case to pass, with the count of cases actually run reported; the exact thresholds are in this skill's definition of done. | A suite we did not write is the only check that cannot be shaped around the validator we already have, and build-definition-of-done makes the case count non-negotiable (F-a7-03): a pass rate with no count of what ran is an exit code wearing a percentage. | sourced | `X-cap-document-validation-004`, `F-part-c-04`, `F-a7-03` "implementations that achieve a perfect score confirm the correctness of their implementation" |
| 5 | Return every violation from one pass, each carrying its location inside the instance and the schema keyword that rejected it; never stop at the first failure and never collapse the list into a sentence. | A caller repairing a document repairs all of it at once, and a machine consumer needs a located, enumerable list rather than prose. | sourced | `X-cap-document-validation-005` "All errors are reported in a single pass instead of stopping at the first failure." |
| 6 | Choose the second adapter on a different execution model, not a different vendor: build-adapter-pair owns that discipline (F-b1-04), and for this capability the choice is unusually cheap because conformant implementations exist across language runtimes. | A second tree-walking validator in the same runtime proves nothing about the interface; a validator that compiles the schema in another runtime exercises the parts of the contract that leak. | sourced | `X-cap-document-validation-006`, `F-b1-04` "implementations in all major languages can validate against the same dialect" |
| 7 | Prepare each schema once and reuse the handle across instances, and report how many instances a handle served. | Repeated validation against the same schema is the normal case at an entry boundary, and paying schema-reading cost per instance is the difference between a check that is always on and one that gets switched off. | sourced | `X-cap-document-validation-003` "Caching the compiled validation function is recommended for repeated validation against the same schema" |
| 8 | Record the dialect version as unverified until the published specification has been read in an environment that can fetch it, as build-skill-authoring requires; the record naming 2020-12 here is search-only. | A version number nobody read is a fabrication with a decimal point in it. | sourced | `F-part-c-10`, `X-cap-document-validation-001` "Cite the standard and its version" |
| 9 | Send the document together with the identifier of the shape it claims to be, through the same envelope whether you are a person typing it, an agent submitting it, or an event carrying it. | All three must be able to enter, and one entry shape is what lets the same check, the same outcome and the same record apply to all of them. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| 10 | Proposed: open references/document-validation-shapes.md when you are implementing the outcome shape, the error unit, or the conformance report, or reviewing someone who did. The body of this skill is enough to judge and to call the capability without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full shapes are longer than the progressive-disclosure budget allows in the body, and a reader deciding whether to use the capability does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the configuration finding (F-a7-04). What it adds here: ask the adapter which dialect it actually resolved rather than trusting the schema file, because a validator quietly configured for an older draft still accepts almost every document and fails only on the newer keywords. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| agentic-stack already states the green-gate finding (F-a7-03). What it adds here: a document that validates is well-formed, not correct - schema validity says nothing about whether the intent it declares is achievable, so a validation pass must never be reported as an approval. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: keep the outcome in the standard's own vocabulary - instance location, keyword location, message - and let each consumer translate into whatever error body its transport uses. One translation per consumer is cheaper than one bespoke outcome per adapter. | proposed | - |
| Speed and conformance are separate properties: one implementation converts a schema into generated code before any instance is seen, which is an adapter property worth having on the entry path, while whether an adapter may serve the interface at all is decided by the official suite. | sourced | `X-cap-document-validation-002`, `X-cap-document-validation-004` "converts it into a very efficient JavaScript code that validates your data according to the schema" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-in-place` | today | validate and check_schema, served in-process in the same managed runtime as the caller. PASS.md records this adapter only as in place; which library serves it is named in cap-document-validation-implement (proposed). | Proposed: cannot be reached from a runtime that cannot load it, and pays schema-reading cost on the interpreted path rather than generating code ahead of the first instance, so its per-instance cost is a function of schema size. | Select the adapter by configuration, point it at the same schema store and dialect, and run the official suite plus the platform's own instances through both; no core change is expected because the core imports the interface. | claimed | `F-b3-09` "JSON Schema 2020-12 \| in place" |
| `E-swap-candidate-any-2020-12-validator` | second | the same two operations, served by a validator that compiles the schema ahead of use in a different, natively compiled language runtime; the row names the candidate class rather than a product. | Proposed: cannot share the caller's process objects or exception types, and cannot be handed a schema outside the declared dialect - which is the point, since anything it cannot implement was adapter detail leaking into the contract. | Run one parameterised conformance run over both adapters against the same suite and the same instances and require identical outcomes. Proposed: the execution-model axes that must differ are start and teardown cost (schema compiled ahead of use versus read per call) and processes required for progress (in-process library versus a separate native runtime). | claimed | `F-b3-09`, `F-b1-04` "any 2020-12 validator" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first implementation of this interface: `python3 tools/conformance_document_validation.py --suite third_party/JSON-Schema-Test-Suite/tests/draft2020-12 --adapter today --adapter second --report out/document-validation-conformance.json`. It asserts, per adapter, required_failed == 0, cases_run > 1000, and dialect_in_effect equal to the 2020-12 dialect URI the adapter reports at run time, and across adapters adapters_run >= 2. |
| Expected | exit 0, and one report line per adapter of the form `adapter=<role> cases_run=<N greater than 1000> required_failed=0 dialect_in_effect=<the 2020-12 dialect URI>`, followed by `adapters_run=2`. |
| Deliberate breakage | Configure one adapter for draft-07 instead of the 2020-12 dialect, change nothing else, and re-run. |
| Expected failure | For that adapter the `$dynamicRef` and `$recursiveRef` cases fail, required_failed becomes non-zero, its reported dialect_in_effect no longer equals the 2020-12 URI, and the run exits non-zero while the other adapter still reports required_failed=0 - so the report names which adapter broke rather than only that something did. |
| Status | claimed |
| Evidence | `F-part-c-04`, `X-cap-document-validation-004` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-adapter-pair`, `build-skill-authoring`

Used by: `cap-capability-packaging`, `cap-capability-registry`, `cap-document-validation-implement`, `cap-human-interaction`, `cap-policy`, `cap-tool-access`, `cap-work-intake`, `compose-operators`, `core-document`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is the dialect version string that this skill records actually the current published one? | A fetch of the dialect's published specification recording its version and date; the record naming 2020-12 here is search-only, and documentation fetches were blocked in this environment. | version 2020-12 with version_status unverified everywhere it appears, and no version number written that was not read. | `X-cap-document-validation-001`, `F-part-c-10` "The current version is 2020-12" |
| Which fields of the standard's validation output are required at this interface and which are optional? | Run the official suite under two adapters and diff their outputs field by field; a field that only one adapter can populate is optional, a field both populate identically is required. | Require instance location, keyword location and a message; treat everything richer as optional, since a caller repairing a document needs the location before it needs the annotation. | `X-cap-document-validation-005` "Validation output includes evaluation path, schema location, instance location, and specific errors with descriptions." |
| May an adapter resolve a remote reference at validation time, or must every reference be present in the supplied schema store? | Count, across the platform's own schemas, how many references point outside the store, and measure the added tail latency and the failure mode when the remote is unreachable at an entry boundary. | Offline only: every reference resolves inside the supplied store, because a validation that can fail on someone else's outage is not a gate. | `X-cap-document-validation-006` "implementations in all major languages can validate against the same dialect" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
