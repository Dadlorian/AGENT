---
name: core-document
description: The Document: the one declarable artifact this platform owns - declared intent, a definition of done that is a list of runnable checks with risk tiers, and steps drawn from a closed operator vocabulary - produced in the same shape whether a human, an agent or an event entered, and written before anything reads it. Load it before adding a field to what a caller declares, before an intake path stamps a default of its own, when a unit of work is about to be described in free text, and when someone asks 'where does the task actually live', 'what does done mean here and who checks it', 'why may the planner not rewrite this', or 'why did the same request produce two different digests'.
---

# core-document

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one declarable artifact - declared intent, definition of done and steps - so that every way in produces the same reviewable, diffable, replayable data, and nothing downstream has to guess what was asked for. | sourced | `F-b2-02`, `F-b2-01` "declared intent, definition of done, steps" |

## Entities

| Entity |
|---|
| `E-core-component-document` |
| `E-core-component-planner` |
| `E-core-component-judge` |
| `E-rule-b1-5` |
| `E-rule-b1-6` |
| `E-capability-document-validation` |
| `E-capability-errors` |
| `E-standard-json-schema-2020-12` |
| `E-standard-rfc-9457-problem-details` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | https://json-schema.org/draft/2020-12 | `F-b3-09`, `F-b1-03` |
| `E-standard-rfc-9457-problem-details` | RFC 9457 | unverified | - | `F-b3-13`, `F-b1-03` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| declare (proposed operation; PASS.md names the data, not the calls) | an intent summary, a definition of done as a list of checks, and an ordered list of steps naming operators from the closed set (proposed) | an immutable document instance plus its content digest, or a typed problem naming every field that failed (proposed) | proposed | `F-b2-02` |
| digest (proposed operation) | a document instance (proposed) | a stable digest over its canonical form, so two entries that declared the same work are provably the same declaration (proposed) | proposed | - |
| validate (imported from cap-document-validation, not implemented here) | a document instance, the schema resource urn:agentic:core:document:0.1, and the dialect that schema declares | the validation outcome cap-document-validation defines; the core imports that interface and hand-rolls no field checks of its own | sourced | `F-b3-09`, `F-b1-02` "in place \| any 2020-12 validator" |
| steps_of (proposed accessor) | a document instance (proposed) | the ordered steps and the operator each names, with no payload body, so the Planner can price the work without reading what the work is about (proposed) | proposed | `F-b2-03` |
| criterion_of (proposed accessor, reachable by the Judge only) | a document instance and a check id (proposed) | the criterion text of that check; this is the only path by which criterion text leaves the document, and it never returns through a dispatch request (proposed) | proposed | `F-b1-07` |

### Shapes (JSON Schema 2020-12)

**document (proposed summary shape; the full schema, the step vocabulary, a worked example for each of TARGET T1's three ways in and a worked rejection are in references/document-shapes.md)** (proposed; sources: `F-b2-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:document:0.1",
  "title": "Document",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "document_version",
    "document_id",
    "intent",
    "definition_of_done",
    "steps"
  ],
  "properties": {
    "document_version": {
      "const": "0.1"
    },
    "document_id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]{2,63}$"
    },
    "intent": {
      "type": "object",
      "required": [
        "summary"
      ],
      "properties": {
        "summary": {
          "type": "string",
          "minLength": 1,
          "maxLength": 400
        }
      }
    },
    "definition_of_done": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "urn:agentic:core:document:check:0.1"
      }
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "description": "Each step names one operator from the closed set; the step schema is in references/document-shapes.md."
    },
    "declared_by": {
      "type": "string",
      "description": "The subject that declared it. Never the entry kind: nothing downstream may branch on which way in produced this."
    }
  }
}
```

**definition-of-done-check (proposed shape for the machine-readable fields named in the invariants and instructions below)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:document:check:0.1",
  "title": "Definition-of-done check",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "check_id",
    "kind",
    "risk_tier",
    "command",
    "expected"
  ],
  "properties": {
    "check_id": {
      "type": "string",
      "minLength": 1
    },
    "kind": {
      "enum": [
        "behavioural",
        "well_formedness"
      ]
    },
    "risk_tier": {
      "enum": [
        "low",
        "standard",
        "high"
      ]
    },
    "command": {
      "type": "string",
      "minLength": 1
    },
    "expected": {
      "type": "string",
      "minLength": 1
    },
    "breakage": {
      "type": "string",
      "description": "The deliberate change that must make this check fail."
    }
  }
}
```

**check-report (proposed shape; outcome is inconclusive whenever behavioural_run is 0)** (proposed; sources: `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:document:check-report:0.1",
  "title": "Definition-of-done run report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "document_digest",
    "checks_declared",
    "checks_run",
    "behavioural_run",
    "outcome"
  ],
  "properties": {
    "document_digest": {
      "type": "string",
      "minLength": 1
    },
    "checks_declared": {
      "type": "integer",
      "minimum": 0
    },
    "checks_run": {
      "type": "integer",
      "minimum": 0
    },
    "behavioural_run": {
      "type": "integer",
      "minimum": 0
    },
    "outcome": {
      "enum": [
        "passed",
        "failed",
        "inconclusive"
      ]
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The Document is data, not a service: it carries declared intent, a definition of done and steps, and without it nothing in the platform is declarable. | sourced | `F-b2-02` "nothing is declarable" |
| The document is written before anything reads it. agentic-stack states design rule 5 as a test (F-b1-06); the consequence on this artifact is that a component which rewrites, enriches or normalises the document on the planner's behalf has made planning impure, because the Planner is a pure function of the document it was handed. | sourced | `F-b2-03`, `F-b1-06` "pure function `document → plan + cost`" |
| The definition of done lives in the document, but its criterion text does not travel with the work. agentic-stack and build-definition-of-done state design rule 6 (F-b1-07); the consequence here is that criterion_of is the Judge's path only, and a criterion string reachable from a dispatch request, a document handle given to a graded unit, or a step payload is a defect in this component, not in the Judge. | sourced | `F-b1-07` "never the criterion it is judged against" |
| Validation is imported, never implemented here. agentic-stack states design rule 1 as a test (F-b1-02); the consequence for the Document is that its schema is a plain dialect resource checked through the cap-document-validation interface, so a field check written inside the core is the rule failing rather than a shortcut. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| Proposed: one document schema, and every entry adapter produces it. TARGET T1 lists three ways in - a human, an agent, and an internal or external event (T-t1-01, T-t1-02, T-t1-03) - and all three yield an instance of the same shape; the way in is recorded, never branched on downstream. | proposed | `T-t1-01`, `T-t1-02`, `T-t1-03`, `X-entry-composition-005` |
| Proposed: a document is immutable once declared and is addressed by the digest of its canonical form. Amending declared work produces a new document with a new digest and a link to the old one; there is no edit-in-place, because a replay whose input can change is not a replay. | proposed | `X-entry-composition-052` |
| Proposed: a definition of done is a list of runnable checks, each carrying a kind and a risk tier per the check shape above. build-definition-of-done owns the discipline and the measured green-gate finding (F-a7-03); the consequence for this artifact is a reporting rule - a run in which behavioural_run is 0 is reported inconclusive, never passed, so a document cannot be closed by checks that never applied to it. | proposed | `F-a7-03`, `X-end-to-end-078` |
| Every rejection of a document is a typed problem, not prose. cap-errors owns the shape and the standard that governs it (F-b4-07, F-b3-13); the consequence here is that a caller repairing a declaration branches on the problem type and reads the located field list, and never on the wording of a message. | sourced | `F-b4-07`, `F-b3-13` "Typed and machine-readable. Never parsed from prose" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion text of any definition-of-done check, to the unit that will be graded against it. agentic-stack states design rule 6 (F-b1-07); on this interface it forbids criterion text inside a step payload, inside a dispatch request, and inside any document view handed to an executing agent. | sourced | `F-b1-07` "An agent sees its outcome" |
| Products, endpoints, model vendors and store paths. agentic-stack states the rule (F-part-c-09); the consequence here is that a document declares what must be true, never which implementation is to make it true, so the same document survives every adapter swap beneath it. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| Proposed: cost, plan, schedule and result. The document declares; it does not record. A plan belongs to the Planner, a verdict to the Judge, and a receipt to the Ledger, and folding any of them back in is what makes a document unreplayable. | proposed | `F-b2-03` |
| Proposed: the entry kind as a branch point. It is recorded on the envelope for audit, but no consumer of a document may read it to choose behaviour, or the single shape has become four shapes wearing one name. | proposed | `T-t1-01` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the document first, in full, before any consumer of it exists: intent summary, the definition of done as checks, and the ordered steps. Do not leave a field for a later component to fill in. | agentic-stack states design rule 5 as a test (F-b1-06). The consequence here is ordering, not style: a field that is completed downstream is a field the Planner priced before it existed, and cost stops being knowable before commitment. | sourced | `F-b1-06`, `F-b2-03` "Cost is knowable before commitment" |
| 2 | State the definition of done as a list of checks conforming to the check shape above: each with a check_id, a kind of behavioural or well_formedness, a risk_tier, a command, an expected result, and the breakage that must make it fail. | A definition of done written as a sentence cannot be run, and a check with no declared breakage has never been shown capable of failing; agentic-stack, build-skill-authoring and build-definition-of-done all state the criterion rule (F-part-c-04); the field layout above is what carries it into the document rather than into a review comment. | sourced | `F-part-c-04`, `X-end-to-end-077` "A criterion nothing can fail is not a criterion" |
| 3 | Draw every step from the closed operator vocabulary the composition layer publishes, and put no free text in the step position. Anything the vocabulary cannot express is a gap to raise, not a string to smuggle. | A closed vocabulary is what lets the Planner price a document, the Graph type it, and a reader learn the whole surface in one sitting; an open string field would make each of those a parsing problem. | sourced | `T-t3-02`, `X-entry-composition-052` "It cannot be daunting or overly complex, or no one will use it." |
| 4 | Produce the document from every way in through the same construction path. TARGET T1's three ways in - a human, an agent, and an internal or external event - normalise at the edge, so the difference between them survives only as recorded provenance on the envelope. | Normalising at the edge is what keeps one shape from becoming several: prior art shows trigger endpoints doing exactly this before an agent sees the work, and every branch that survives the edge is a branch every downstream component then has to carry. | sourced | `T-t1-01`, `T-t1-03`, `X-entry-composition-005` "All trigger endpoints normalize the incoming event into a consistent JSON structure" |
| 5 | Keep the minimal input small enough to type: an intent summary, one definition-of-done check, and one step is a valid document. Everything else is optional with a declared default, and no default is stamped by an intake path. | TARGET T3 makes usability a requirement rather than a courtesy; and a default added by one intake path breaks digest equality between two entries that declared the same work, which is the property the C1 fixtures exist to protect. | sourced | `T-t3-01`, `T-t3-02` "It has to be simple to use." |
| 6 | Validate every document through the cap-document-validation interface against urn:agentic:core:document:0.1, and return every violation at once, located inside the instance. | cap-document-validation owns the contract and the one-pass rule; importing it rather than restating it is what keeps a hand-rolled keyword check out of the core and lets the checker be replaced without a core change. | sourced | `F-b3-09`, `F-b1-02` "Document validation** \| JSON Schema 2020-12" |
| 7 | Return every rejection as the problem shape cap-errors defines, carrying the type, the located field list and a detail written for the declarer; never raise the validator's own exception across this boundary. | cap-errors owns the standard for this (F-b3-13). The consequence here is that declaring is the platform's first touch point, so it is the first place a caller learns whether failures are machine-readable or prose. | sourced | `F-b3-13`, `F-b4-07` "— adopt the RFC directly" |
| 8 | Judge a candidate implementation on four criteria: positive and negative fixtures both counted with checked greater than zero; identical digests for the same work declared through different ways in; no criterion string reachable from a step payload; and a check report that reports inconclusive when behavioural_run is 0. | These are the four properties every other component then relies on, and each is a count rather than an exit code: build-definition-of-done owns the measured finding (F-a7-03) of a gate that ran structurally green with every behavioural stage skipped, and a count is what that finding costs to satisfy. | sourced | `F-a7-03`, `F-part-c-04` "with every behavioural stage skipped" |
| 9 | Record the schema dialect as unverified until its published specification has been read in an environment that can fetch it, and write no version string that was not read. | build-skill-authoring requires the standard and its version to be cited rather than recalled, and a version number nobody read is a fabrication with a decimal point in it. | sourced | `F-part-c-10` "Cite the standard and its version" |
| 10 | Proposed: open references/document-shapes.md when you are writing the full document schema, the step vocabulary or the fixture corpus, when you need the worked declaration for a producer kind you have not handled yet, or when you are rendering a rejection and want the problem instance rather than the rule. The body of this skill is enough to declare a document and to judge an implementation without it. | Proposed: the full schema, the three producer examples and the worked rejection are longer than the progressive-disclosure budget allows in the body, and a reader deciding what to declare does not need them; a reader repairing a refused declaration does. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| cap-document-validation already states the well-formedness finding (F-a7-03). What it adds here: a document that validates has been shown declarable, not achievable, so a schema pass must never be reported as an approval or as progress against the definition of done. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: treat digest equality across the ways in as a standing test, not a design intention. The cheapest way to lose it is a courtesy default - a priority, a timestamp, a normalised title - added by one intake path and by no other. | proposed | `T-t1-01` |
| Prior art for a declarative unit of work is portability across runtimes, so keep the document free of anything only one executor could honour; a document that is readable, diffable and replayable is worth more than one that is convenient for today's executor. | sourced | `X-entry-composition-052` "portable, shareable, platform-agnostic configuration language" |
| Write the acceptance criteria as something the executing agent can run, not as something a reviewer will interpret later; a criterion the agent cannot execute becomes a criterion nobody executes. | sourced | `X-end-to-end-077` "the agent needs criteria it can execute, which means machine-verifiable" |
| Proposed: keep the document's review surface to one screen. A declaration a human will not read is a declaration nobody checks, and the definition of done is precisely the part that stops being read first. | proposed | `T-t3-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.1 row C1, made precise: `document-validate --schema urn:agentic:core:document:0.1 fixtures/positive/*.json fixtures/negative/*.json` exits 0 and reports `positive=12 passed`, `negative=9 rejected` and `checked>0`, where the negative corpus includes `missing-dod.json` (no definition_of_done) and `criterion-in-payload.json` (criterion text inside a step payload). |
| Expected | exit 0 and the three lines `positive=12 passed`, `negative=9 rejected`, `checked=21`. |
| Deliberate breakage | Remove `"definition_of_done"` from the schema's `required` array and re-run, changing nothing else. |
| Expected failure | The negative fixture `missing-dod.json` now validates, the negative count drops to `negative=8 rejected`, the asserted count of 9 is not met, and the run exits non-zero. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b2-02` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `cap-document-validation`, `cap-errors`

Used by: `compose-operators`, `core-document-implement`, `core-graph`, `core-judge`, `core-ledger`, `core-planner`, `seam-dispatch`, `xc-compensation`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does a document carry its steps inline, or reference a named workflow that carries them? | Count, over a representative corpus of declarations, how many reuse an existing step list unchanged. High reuse argues for a reference plus overrides; low reuse argues for inline steps and one artifact to read. | Inline steps, with an optional reference for the reuse case, because the reference consumption example in examples/end-to-end/ already carries a workflow reference on the envelope and one artifact a reader can diff is the simpler default. | `T-t3-01` "It has to be simple to use." |
| How many risk tiers does a definition-of-done check need, and what evidence does each tier oblige? | Across the run history, count how many distinct evidence levels callers actually distinguish. If the answer is two, three tiers are over-modelled; if reviewers keep adding an ad hoc tier, three are too few. | Three tiers - low, standard, high - with the obligation attached per tier in references/document-shapes.md, since evidence appropriate to risk is the property being bought and a single tier collapses back into an unconditional gate. | `X-end-to-end-078` "it is accepted because it satisfies evidence appropriate to its risk level" |
| Is the document digest computed over correlation and budget fields, or over the declared work alone? | Submit one logical job through each way in and diff the canonical forms field by field; any field that differs purely because of the way in must be outside the digest for cross-entry digest equality to be assertable at all. | Over the declared work alone - intent, definition of done and steps - because digest equality across the ways in is the property this component is judged on, and correlation and budget necessarily differ per entry. | `T-t1-02`, `F-b2-02` "declared intent, definition of done, steps" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
