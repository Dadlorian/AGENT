---
name: core-planner-implement
description: How to build the Planner on this stack: a pricing module that links no client of any metered interface, a loader that pins the head and hands the cost table and quantiles in as values, one plan call every producer maps into, the record store those pinned reads sit in today and a second whose execution model differs, the migration from discovering cost by spending it, where the cross-cutting concerns attach to a plan, and the run that decides whether either store may serve. Load it when writing or reviewing that code, when an estimate is about to be fetched instead of looked up, when a cost row is about to be defaulted, and when someone asks 'where do the numbers actually come from', 'can we change that store without touching the core', or 'why did the same document price differently on two machines'.
---

# core-planner-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what core-planner's contract specifies: one pricing module with no I/O, one loader that pins the head, one plan call, two record stores selected by configuration, and a run that shows the plan bytes and the connect count survive the swap unchanged. | sourced | `F-b2-03`, `F-b1-06` "nothing is pricable before it is spent" |

## Entities

| Entity |
|---|
| `E-core-component-planner` |
| `E-core-component-ledger` |
| `E-seam-state` |
| `E-capability-state-persistence` |
| `E-capability-model-access` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-object-store` |

## Contract

### Shapes (JSON Schema 2020-12)

**plan-inputs-binding (proposed shape; the wiring table, the backfill rules and the migration procedure are in references/implementation-notes.md)** (proposed; sources: `F-meta-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:plan:inputs-binding:0.1",
  "title": "Plan inputs binding",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "record_kinds",
    "read_mode",
    "differs_in_execution_model"
  ],
  "properties": {
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "record_kinds": {
      "type": "array",
      "minItems": 1,
      "description": "The record kinds this binding serves the pinned reads from, e.g. dispatch-result and cost-observation."
    },
    "read_mode": {
      "type": "string",
      "minLength": 1,
      "description": "How a read at a pinned head is served: scanned and folded in-process, or fetched as a materialised snapshot by digest."
    },
    "serves_pricing": {
      "const": false,
      "description": "A store that computes a quantile or a price itself has taken the Planner's job into the persistence boundary; it returns records or snapshots only."
    },
    "differs_in_execution_model": {
      "type": "array",
      "minItems": 1,
      "description": "Proposed: the axes build-adapter-pair defines, carried here so a pair identical on every axis is rejected."
    }
  }
}
```

**planner-conformance-report (proposed shape; the fields the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:plan:conformance-report:0.1",
  "title": "Planner conformance report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "plans_computed",
    "plan_digest_mismatches",
    "connects_inet",
    "steps_priced",
    "criterion_leaks"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    },
    "plans_computed": {
      "type": "integer",
      "minimum": 0
    },
    "plan_digest_mismatches": {
      "type": "integer",
      "minimum": 0,
      "description": "Documents on which two bindings produced different plan bytes at the same head. The count a store that interprets records makes non-zero."
    },
    "connects_inet": {
      "type": "integer",
      "minimum": 0
    },
    "steps_priced": {
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
| core-planner owns the contract - purity, the pinned head, the cost inputs as data, a refusal instead of a guess (F-b1-06, F-b2-03). This skill adds only how it is built: an implementation that fetches an estimate, resolves a second head part-way through, or defaults a missing cost row has produced a defect, not an optimisation. | sourced | `F-b1-06`, `F-b2-03` "Planning is a pure function and completes before execution begins" |
| The pricing module links no client of a metered interface. agentic-stack and build-adapter-pair state the boundary rule (F-b1-02, F-meta-04); the consequence here is a build-level one - the package holding the pricing function imports nothing from the model-access client and nothing from the store, so it compiles and runs with no binding present at all, and a build in which it cannot is where the boundary went wrong. | sourced | `F-b1-02`, `F-meta-04` "The core imports interfaces, never implementations" |
| Proposed: the loader owns every side effect on this path. It resolves the head once, reads the cost table and quantiles at that head, digests them, and hands values to the pricing call; the pricing function has no clock, no environment lookup and no file handle, which is what makes the tracer count in the definition of done a property of the code rather than of the fixture. Research query: see the loader-isolation research query on the sibling instruction row above. | proposed | `F-b5-05`, `F-b1-06` |
| Proposed: a plan is a deterministic function of the document, the head and the cost-inputs digest under either binding. Two bindings that disagree on the plan bytes for one document at one head have disagreed about what the store contained, and that disagreement is the defect the conformance run below exists to find rather than a tolerance to configure away. Research query: is there a fetched source on cross-binding determinism for a pricing function, beyond F-b1-04's general swappability principle and F-meta-04's capability/product boundary rule? | proposed | `F-b1-04`, `F-meta-04` |
| agentic-stack and build-adapter-pair state design rule 7 (F-b1-08, F-b4-01). The consequence on this path is placement: correlation, the policy consultation, the provenance attestation and the ceiling comparison attach where the plan is constructed and admitted, and there is no flag, binding option or cost-input field by which a caller can ask to skip one. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record states the labelling rule (F-part-c-08); the consequence here is that a conformance result is claimed until a run is attached naming the code version and the tree hash under test, and swapping the store behind a pinned read is exactly the change that looks identical in review and differs in a run. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: which binding served the pinned reads, its layout, its lease mechanism and its retention class. A caller of this code sees a plan and a purity report; anything else it can see it will eventually depend on, and the swap stops being possible. | sourced | `F-meta-04` "Part A names products. Part B names capabilities and the standard that governs each." |
| Proposed: criterion text, in any field this code writes onto a plan or a planned step. core-planner states the rule on the plan (F-b1-07); the build consequence is that a step derived from a document carries its check_ids and never the criterion string, and the lint in step 7 is what keeps that true after the next refactor. | sourced | `F-b1-07` "The grader is never visible to the graded" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build pricing as a module that imports no network client, no clock and no store: it takes a document and a cost-inputs value and returns a plan. Put the loader that resolves the head and reads those inputs in a separate module that depends on both. | agentic-stack and build-adapter-pair state the boundary rule (F-b1-02); core-planner requires the pricing call to be pure, and the only version of that which survives a deadline is one where the import graph makes a metered call unreachable rather than merely discouraged. | sourced | `F-b1-02`, `F-b1-06` "The core imports interfaces, never implementations" |
| 2 | Proposed: resolve the head in the loader, read the cost table and the quantiles at that head, digest them, and pass the values and the digest into the pricing call. Never let the pricing module read a default, an environment variable or a file of its own. Research query: is there a fetched source on isolating every side effect in one loader module, beyond F-b5-05's state-persistence specification this row draws its digest requirement from? | Proposed: this is what puts every side effect on the path in one module a reviewer can point at, and it is why the same document prices identically on two machines - the second machine is handed the same values rather than asked to find them. | proposed | `F-b5-05` |
| 3 | Give each producer a thin mapper into one plan call. TARGET T1's three ways in - a human, an agent, and an internal or external event - share the call; a mapper may carry an envelope's requester onto the plan and may not add a step, default a cost row, or pick a different head. | core-planner requires one plan call for every way in; making the mapper unable to touch the priced fields is what stops a fourth producer from quietly acquiring its own cheaper price for the same document. | sourced | `T-t1-02`, `T-t1-01`, `T-t1-03` "An agent must be able to enter the system." |
| 4 | Put the record store the pinned reads are served from behind the binding record: implement role today over the appended, hash-chained file that holds run state now, and role second on a different execution model rather than a different product. Fill in both bindings' execution-model axes before either is used. | build-adapter-pair owns this discipline (F-b1-04). The consequence here is specific: a second appended file would let the loader keep every whole-file, single-writer, local-path assumption, while a store that answers a pinned read with an immutable snapshot fetched by digest forces the head to be a real value and the read to be position-independent. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 5 | Proposed: migrate from spending to pricing in three stages. Backfill a cost table from the run history already recorded; shadow-plan every entry beside the live path without gating on it; compare declared worst case against actual spend per run, and cut over to plan-before-dispatch only when the worst case covered the actual on every run in a full window. Research query: has this three-stage migration (backfill a cost table, shadow-plan, compare worst-case to actual) actually been run, or is the sequencing reasoned from the general migration pattern with no measured run behind it? | Proposed: the migration risk is not a wrong plan but an empty cost table - a planner cut in before quantiles exist either refuses everything or prices everything from a rate card, and both look like the planner failing rather than the data being absent. Shadow planning is also the only way to get the first quantiles without spending to learn them twice. | proposed | `X-core-planner-002`, `F-a5-03` |
| 6 | Wire the cross-cutting concerns into the plan call: stamp the correlation attribute where the plan is constructed, consult policy before the plan is admitted, attest the plan digest together with the document and cost-input digests, and read the ceiling from the envelope as a constant the plan is compared against and never edits. | agentic-stack states design rule 7 (F-b1-08) and the measured trace-context finding (F-a7-02) is why correlation is an explicit attribute set here rather than inherited from whatever called in; a plan with no correlation attribute is a cost nobody can attribute to a run afterwards. | sourced | `F-b1-08`, `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Put two gates in the pipeline: the purity run under the syscall tracer on every change, and a build-time lint that fails when the pricing package imports the model-access client, a network module or the store, plus a grep of every declared criterion string against the plan output. | agentic-stack and build-definition-of-done state that a criterion nothing can fail is not a criterion (F-part-c-04), and core-planner makes the tracer count the form it takes here; a purity rule that is only stated is one the next refactor breaks silently, and the import lint is what catches the breakage at build time rather than after a plan has already spent. | sourced | `F-part-c-04`, `F-b1-07` "A criterion nothing can fail is not a criterion" |
| 8 | Proposed: open references/implementation-notes.md when you are writing the loader, the backfill, the binding records or the wiring, or reviewing someone who did. The body of this skill is enough to review a design and to run the definition of done without it. | Proposed: the wiring table, the two binding records and the backfill rules are longer than the progressive-disclosure budget allows in the body, and a reader judging the build does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-evidence-record already state the configuration finding (F-a7-04). What it adds here: assert the binding actually in effect at run time and log it beside the counts, because a binding written in the documented place and overridden by a stored row produces a conformance run that read one store twice and reported adapters_run=2. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| build-evidence-record already states what the log running today buys (F-a5-03): a closing digest that opens the next run makes a manual edit between runs detectable. What this adds: carry that property onto the cost inputs, because a quantile store without it cannot show the numbers were not edited after the plan that used them was priced. | sourced | `F-a5-03` "a manual edit between runs is detectable" |
| Keep the derivation per step rather than only a total, so an estimate can be reconciled against the actual it is supposed to predict: planning prior art computes cost as a sum of operator costs across the states they are applied in, which is only auditable if each term survives into the plan. | sourced | `X-core-planner-005` "cost computation can consider the state in which each operator is applied" |
| Proposed: run the conformance over both bindings on every change to the loader or the mappers, not only when a binding changes. The failures worth catching come from the read path - a new optional field, a changed sort key, a quantile computed one record later - and they show as a plan digest that moved while no store was touched. Research query: has running the conformance suite on every loader or mapper change caught a plan-digest regression in this repo, or is the practice argued from the adapter-pair discipline alone? | proposed | `F-b1-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | The store the planner's pinned reads are served from today. PASS.md Part B records state persistence as JSONL plus a hash chain, and Part A records the task store as hash-chained with each run's closing digest opening the next. The Planner is owned core surface with no adapter of its own, so what is adapted beneath it is the record store its prior-result and cost-history reads round-trip through - cap-state-persistence's row - and this skill tests the pair there. | Proposed: cannot serve a read at an arbitrary head without scanning from the beginning, cannot be read by another process without sharing a filesystem path, and holds no cost observations at all today, which is what the backfill in step 5 has to produce. | Select the binding by the binding record, point both roles at the same loader and the same pricing module, and run the conformance corpus through both. No core change is expected, because the pricing module never sees the binding. | claimed | `F-b3-17`, `F-a5-03` "JSONL + hash chain" |
| `E-swap-candidate-object-store` | second | The same pinned reads served as immutable snapshots addressed by digest: the loader asks for the snapshot named by the head and gets a whole cost-inputs value back, rather than scanning records and folding them. PASS.md's state-persistence row names this candidate class, and the row names a class rather than a product. | Proposed: cannot answer a query the snapshot was not built for, cannot append a record mid-plan, and cannot hand back a local path - which is the point, since anything it cannot serve was a file-shaped assumption that had leaked into the loader. | Proposed: the execution-model axes that must differ are read_mode (scan and fold in-process versus fetch one materialised snapshot by digest) and locus_of_determinism (file order plus a linear chain versus a content address that is the head). Run one parameterised conformance over both roles and require identical plan bytes and identical connect counts. | claimed | `F-b3-17`, `F-b1-04` "object store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/dispatch/test.sh && python3 harness/dispatch/conformance.py --adapter dryrun --adapter second |
| Expected | What the run proves: docs/decomposition.md section 3.1 row C2, run across both bindings. Proposed tool, built with this component: `python3 tools/planner_conformance.py --binding bindings/today.json --binding bindings/second.json --document fixtures/plan/checkout-500s.json --head H --report out/planner-conformance.json`, which for each binding runs `plan` twice under `strace -f -e trace=connect,sendto`. Per binding it asserts the two plan files are byte-identical, `connects_inet == 0` and `steps_priced > 0`; across bindings it asserts `adapters_run >= 2`, `plan_digest_mismatches == 0` and `criterion_leaks == 0`. \| exit 0, one line per binding of the form `binding=<role> plans_computed=2 identical=yes connects_inet=0 steps_priced=<n>`, then `adapters_run=2 plan_digest_mismatches=0 criterion_leaks=0`. |
| Deliberate breakage | In harness/dispatch/core.py plan, fold the wall clock into the plan digest so the same document at the same head no longer prices identically twice, run the criterion (the purity assertion that two plans of one document share a digest fails under both bindings and the gate exits 1), then git checkout harness/dispatch/core.py. |
| Expected failure | `connects_inet` stays 0 and `criterion_leaks` stays 0 under both bindings, and each binding still reports `identical=yes` because its own two runs read the same head - so neither the purity rule nor the two-run identity check is what moved. The bindings plan at different heads, so `plan_digest_mismatches` becomes non-zero, the run exits non-zero naming the binding whose digest moved, and `adapters_run` stays 2 with `steps_priced` greater than zero. That every per-binding assertion stays green is what isolates the fault to one binding's loader wiring, rather than to the planner sampling a price - which is the fault core-planner's own breakage exercises, and is not repeated here so the pair demonstrates two failure modes rather than one twice. |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-04` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `core-planner`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| PASS.md Part A records no adapter for the Planner itself, so which pair does this skill's swap test actually exercise? | The Part B table has no Planner row: agentic-stack states that the five components are the owned surface and everything else is an adapter, so there is no adapter-today column to read. Applying TARGET T5's 1-3-1, the three options were: declare no pair and record the gap, which leaves swappability untested on the component that makes cost knowable at all; adapt the record store the pinned reads are served from; or reuse the persistence pair cap-state-persistence-implement already owns, which duplicates a sibling and tests nothing about pricing. The second is recommended and is taken in the Adapters section. | The record-store pair above, tested by the conformance run; if a Planner adapter row is ever added to PASS.md, this question is reopened against it. | `F-b2-07`, `T-t5-02` "Everything else is an adapter." |
| Are the cost quantiles computed inside the store, or folded above it from records the store returns? | Measure the record volume a cost-history read transfers at today's history size and at a hundred times it, against the read rate planning generates. A transfer cost that dominates argues for computing the quantile at the store; anything less does not. | Folded above the store, with serves_pricing pinned false in the binding shape. core-planner defines the pinned query surface it reads from (F-b5-05), and a store that computes a quantile has taken the Planner's job into the persistence boundary, and the two bindings would then have to agree on a statistic rather than on a set of records. | `F-b5-05`, `F-b1-02` "the query surface a planner needs" |
| When the cost inputs are stale or thin, does the planner refuse or price from the rate card? | Compare, per selector, the rate-card figure against the measured p95 over a full window. Where the rate card is routinely outside the measured band, pricing from it is a number that will not reconcile and refusal is honest; where it tracks, refusal costs availability for nothing. | Price from the rate card with observations recorded as zero on the derivation, so a reader can see the estimate was not measured, and refuse only when the selector has no row at all - which is the refusal core-planner's open question covers. | `X-core-planner-002` "Structured, repeatable estimation is supported by both the AACE and PMI" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu (core-planner-implement, 2026-09-03) |
