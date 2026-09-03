---
name: core-document-implement
description: How to build the Document on this stack: one construction path every way in maps into, the schema resource shipped for the validation interface to check, a content digest that survives a store swap, the store that holds declared work today and a second whose execution model differs, the migration off it, where the cross-cutting concerns are wired so no declarer can decline them, and the round-trip run that decides whether either store may serve. Load it when writing or reviewing that code, when an intake path is about to normalise a document on write, and when someone asks 'where do declarations actually get persisted', 'can we change that without touching the core', or 'why did the same declaration come back with a different digest'.
---

# core-document-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what core-document specifies: one construction path, one schema resource, one digest, two stores selected by configuration, and a run that proves a declaration survives the swap byte for byte. | sourced | `F-b2-02`, `F-b1-04` "nothing is declarable" |

## Entities

| Entity |
|---|
| `E-core-component-document` |
| `E-capability-document-validation` |
| `E-capability-state-persistence` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-relational` |

## Contract

### Shapes (JSON Schema 2020-12)

**document-store-binding (proposed shape; the migration procedure and the wiring table are in references/implementation-notes.md)** (proposed; sources: `F-meta-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:document:store-binding:0.1",
  "title": "Document store binding",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "schema_store",
    "digest_algorithm",
    "differs_in_execution_model"
  ],
  "properties": {
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "schema_store": {
      "type": "string",
      "minLength": 1
    },
    "digest_algorithm": {
      "type": "string",
      "minLength": 1
    },
    "normalises_on_write": {
      "const": false,
      "description": "A store that re-serialises a document cannot return the bytes it was given, and the digest stops being a property of the declaration."
    },
    "differs_in_execution_model": {
      "type": "array",
      "minItems": 1,
      "description": "Proposed: the shape build-adapter-pair defines; carried here so the pair can be rejected when both roles are identical on every axis."
    }
  }
}
```

**document-roundtrip-report (proposed shape; the fields the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:document:roundtrip-report:0.1",
  "title": "Document round-trip report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "documents_round_tripped",
    "digest_mismatches",
    "byte_mismatches",
    "criterion_leaks"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    },
    "documents_round_tripped": {
      "type": "integer",
      "minimum": 0
    },
    "digest_mismatches": {
      "type": "integer",
      "minimum": 0
    },
    "byte_mismatches": {
      "type": "integer",
      "minimum": 0
    },
    "criterion_leaks": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| core-document owns the contract - the fields, the immutability, the digest and the grader rule on this artifact (F-b2-02). This skill adds only how it is built: an implementation that adds a field, normalises a value or widens the step vocabulary has produced a defect, not an extension. | sourced | `F-b2-02` "data — declared intent, definition of done, steps" |
| agentic-stack and build-adapter-pair state the swap test (F-meta-04). The consequence here: both stores are selected by a binding record read as configuration, and if choosing one requires editing a file the core owns, the boundary is drawn wrong and the pair has found the defect it exists to find. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| Proposed: the store returns the bytes it was given. No re-serialisation, no key re-ordering, no defaulting on write or on read, so the digest stays a property of the declaration rather than of whichever store held it. Research query: is there a fetched source on byte-preserving storage for content-addressed records, beyond F-a5-03's digest-chain description of the current task store? | proposed | `F-a5-03` |
| agentic-stack states design rule 7 (F-b1-08, F-b4-01). The consequence on this construction path is that correlation, policy consultation, provenance and the budget ceiling are attached where the document is built, and there is no flag, header or document field by which a declarer can ask to skip one. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record states the labelling rule (F-part-c-08); the consequence here is that a round-trip result is claimed until a run is attached naming the code version and tree hash under test, and no amount of rewording upgrades it. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| build-adapter-pair states design rule 4 (F-b1-05); the consequence here is that a document is a plain dialect JSON resource a third party reads and validates with their own tooling, so consuming a declaration of ours never requires importing code of ours. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| Apply build-adapter-pair: the two binding records differ on at least one axis of differs_in_execution_model, and two bindings identical on every axis are one store written twice and fail the pair check; proposed pointer, see that skill. | proposed | `F-b1-04` "Every interface ships with at least two adapters" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: which store served a read, the store's file layout or table schema, its lease mechanism, and its retention policy. A caller sees a document and its digest; anything else it can see it will eventually depend on. | sourced | `F-meta-04` "Part A names products. Part B names capabilities and the standard that governs each." |
| Proposed: criterion text, in anything this code builds from a document. core-document states the grader rule on this artifact (F-b1-07); the build consequence is that the dispatch request assembled from a step carries the check_id and never the criterion string, and the lint in step 7 is what keeps that true after the next refactor. | sourced | `F-b1-07` "The grader is never visible to the graded" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Ship the document schema as a plain dialect resource in the schema store and validate through the cap-document-validation interface; import no checking library into core or seam modules. | agentic-stack states design rule 1 as a test (F-b1-02) and core-document states that validation is imported rather than implemented here; a direct import of a checker is that rule failing in executable form. | sourced | `F-b1-02`, `F-b3-09` "in place \| any 2020-12 validator" |
| 2 | Build one construction path and give each way in a thin mapper into it. TARGET T1's three ways in - a human, an agent, and an internal or external event - share the constructor; a mapper may translate its payload and may not add, default or reorder a field. | core-document requires one shape from every way in; the only way that survives contact with a fourth intake path is to make the constructor the single writer of document fields, so a new mapper cannot quietly stamp a default. | sourced | `T-t1-01`, `T-t1-03` "An internal or external event must be able to enter the system." |
| 3 | Implement the digest over the canonical form of intent, definition_of_done and steps only, and record the algorithm in the binding record. Compute it in the constructor, never in a store adapter. | core-document owns the field list this digest covers (F-b2-02). What this adds is where it is computed: a digest computed by the store is a property of the store, and computing it once at construction is what makes cross-store and cross-entry equality assertable at all, and it is the assertion the definition of done below rests on. | sourced | `F-b2-02` "declared intent, definition of done, steps" |
| 4 | Put the store behind the binding record, implement the role today against the store that holds declared work now, and implement the role second on a different execution model rather than a different product. Fill in both binding records' execution-model axes before either is used. | build-adapter-pair owns this discipline (F-b1-04). The consequence here is specific: a second file-backed appender would leave the interface free to keep every single-writer, local-path assumption, and a transactional multi-writer store is what forces documents to be addressed rather than located. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 5 | Migrate by dual-write and digest-compare: write every new declaration to both the store that runs today and the new one, compare digests and bytes on read back, and cut over only when mismatches are zero over the full corpus and the old path has been read-only for a full retention window. Research query: has a dual-write-and-digest-compare migration actually been run against this repo's task store, or is the procedure reasoned from the general append-only migration pattern with no measured run behind it? | Proposed: the migration's risk is not new rejections but the old acceptances - work that was recorded today with no declared definition of done at all - so the compare must be run over the existing corpus before cut-over, not after. | proposed | `F-a5-03` |
| 6 | Wire the cross-cutting concerns into the construction path: stamp the correlation attribute at construction, consult policy before the first metered call, attest the document digest, and read the budget ceiling from the envelope as a constant the declarer cannot override. | agentic-stack states design rule 7 (F-b1-08); the build consequence is placement - a concern attached after construction is a concern a second intake path can be written without. | sourced | `F-b1-08`, `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Add a lint over recorded dispatch requests that greps each declared criterion string against every request built from that document, and fail the build when the count is non-zero. | core-document states the grader rule on this artifact (F-b1-07). A rule that is only stated is a rule the next refactor breaks silently; the grep is what turns it into something that fails. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| 8 | Record every round-trip run as an evidence record naming what was run, the code version and tree hash under test, whether the tree was dirty, and the output; label the result claimed until such a record exists. | build-evidence-record owns the record's fields (F-a5-04); the consequence here is that a store swap is the kind of change that looks identical in review and differs in a run, so the run is the only thing that separates a claim from a measurement. | sourced | `F-a5-04` "tree hash under test, and whether the tree was dirty" |
| 9 | Proposed: open references/implementation-notes.md when you are writing the construction path, the migration script or the wiring, or reviewing someone who did. The body of this skill is enough to review a design and to run the definition of done without it. | Proposed: the wiring table and the migration procedure are longer than the progressive-disclosure budget allows in the body, and a reader judging the build does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-evidence-record already state the configuration finding (F-a7-04). What it adds here: assert the store binding that is actually in effect at run time and log it beside the round-trip counts, because a binding written in the documented place and overridden by a stored row produces a run that tested one store twice. | sourced | `F-a7-04` "had no runtime effect" |
| Proposed: version the fixture corpus with the schema and add a fixture for every defect found in review, so the corpus grows with the failures the platform actually had rather than with the ones its authors imagined. Research query: does build-definition-of-done's own breakage-corpus guidance name versioning the fixture corpus with the schema, or is that this skill's own extension? | proposed | `F-part-c-04` |
| Proposed: run the round-trip over both stores on every change, not only when a store changes. The failures worth catching come from the constructor - a new optional field, a changed default - and they show up as a digest that moved while no store was touched. Research query: has a round-trip-on-every-change discipline actually been measured to catch a digest-drift defect in this repo, or is the practice argued from the swappability principle alone? | proposed | `F-b1-04` |
| build-evidence-record already states what the store that runs today buys (F-a5-03): a closing digest that opens the next run makes a manual edit between runs detectable. What this adds: keep that property through the migration, because a document store without it cannot show that a declaration was not amended after the work was priced. | sourced | `F-a5-03` "a manual edit between runs is detectable" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | The store declared work sits in today. PASS.md Part A records the task store as JSONL, hash-chained, with each run's closing digest opening the next. The Document itself is owned core surface with no adapter of its own, so what is adapted beneath it is the store its instances round-trip through - cap-state-persistence's row - and this skill tests the pair there. | Proposed: cannot admit concurrent writers without an external lease, cannot be queried except by scanning, and cannot serve a reader in another process without sharing a filesystem path; it also holds no declared definition of done today, which is what the migration in step 5 has to reconcile. | Select the store by the binding record, point both roles at the same schema store and digest algorithm, and run the round-trip corpus through both. No core change is expected, because the constructor computes the digest and the store only puts and gets bytes. | claimed | `F-a5-03`, `F-b3-17` "JSONL, hash-chained" |
| `E-swap-candidate-relational` | second | The same put and get over document bytes, served by a transactional record store reached out of the caller's process. The row names the candidate class rather than a product, and the chain is kept as a computed column rather than as file order. | Proposed: cannot rely on file order for the chain, cannot be reached without a running server, and cannot hand back a filesystem path - which is the point, since anything it cannot implement was store detail leaking into the Document's contract. | Proposed: the execution-model axes that must differ are processes_required_for_progress (zero for a local appended file, one for a separate server) and locus_of_durability_and_verification (file order and a linear chain versus a transaction log and a recomputed digest). Run one parameterised round-trip over both roles and require identical bytes and identical digests. | claimed | `F-b3-17`, `F-b1-04` "object store · relational · event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/document-validation/test.sh && python3 harness/document-validation/conformance.py --adapter dryrun --adapter second |
| Expected | test.sh: exit 0, `passed <n>, failed 0`; conformance.py: exit 0, `conformance PASSED: 28/28 cases, 2 binding(s)`, one binding=dryrun and one binding=second line each showing cases=14 passed=14 product_hits=0. Proposed tool (not run): python3 tools/document_roundtrip.py --binding bindings/today.json --binding bindings/second.json --corpus fixtures/ --dispatch-log out/recorded-dispatch-requests.jsonl --report out/document-roundtrip.json, asserting per binding documents_round_tripped >= 21 with byte_mismatches == 0, and across bindings adapters_run >= 2, digest_mismatches == 0 and criterion_leaks == 0. |
| Deliberate breakage | sed -i '28s#.*#DIALECT_2020_12 = "https://json-schema.org/draft/2020-12/schema-broken"#' harness/document-validation/interface.py |
| Expected failure | conformance.py exits 1: both bindings refuse every schema-carrying case as dialect-unsupported because the shared dialect constant no longer matches what the on-disk schemas declare, dropping to 6/28 cases (3 passed per binding, cases_passed=3 each), and test.sh's own dialect checks (step 1, step 4 product-scan aside) fail too; git checkout -- harness/document-validation/interface.py restores. |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-04` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `core-document`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| PASS.md Part A records no adapter for the Document itself, so which pair does this skill's swap test actually exercise? | The Part B table has no Document row: agentic-stack states (F-b2-07) that the Document is owned core surface and everything else is an adapter, so no adapter-today column exists to read. Applying TARGET T5's 1-3-1 to the gap, the three options were: declare no pair and record the gap; adapt the store the document round-trips through; or reuse the validation pair cap-document-validation-implement already owns. The third duplicates a sibling and the first leaves swappability untested, so the store pair is taken and recorded here. | The store pair in the Adapters section, tested by the round-trip run above; if a Document adapter row is ever added to PASS.md, this question is reopened against it. | `F-b2-07`, `T-t5-02` "This is the entire owned surface. Everything else is an adapter." |
| Does the content digest become the document_id, or travel beside it? | Count, over the fixture corpus and the existing run history, how often a declaration is superseded. Frequent supersession argues for a human-readable id with the digest beside it; rare supersession argues for the digest as the id and no second field to keep consistent. | Beside it, with core-document's document_id pattern unchanged. A readable id is what a person types into an approval and a log query, and a document that is superseded keeps a stable name across its versions. | `F-b2-02` "nothing is declarable" |
| Does the document store keep its own hash chain after the migration, or delegate integrity to the state seam? | Measure full-verification wall time for the document corpus under both, and audit whether any consumer depends on strict linear order of documents rather than of records. | Delegate to the state seam and keep the chain property. build-adapter-pair already states why (F-b5-05): the chain is the idea worth keeping and the file is not, so a document store that reimplements it has duplicated the seam it should be importing. | `F-b5-05` "The chain is the valuable idea and should survive; the file is not" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
