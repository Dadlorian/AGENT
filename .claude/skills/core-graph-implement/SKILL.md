---
name: core-graph-implement
description: How to build the Graph on this stack: a type checker that links no persistence code, one assertion path every producer maps into, node and edge assertions appended as records and folded into a graph value, the log those records sit in today and a second whose execution model differs, the migration off it, where the cross-cutting concerns are wired so no asserter can decline them, and the conformance run that decides whether either log may serve. Load it when writing or reviewing that code, when a fold is about to be cached or a walk pushed into the store, and when someone asks 'where do nodes and edges actually get written', 'can we change that without touching the core', or 'why did the same assertions produce two different verdicts'.
---

# core-graph-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what core-graph's contract specifies (F-b2-04): one in-memory type checker, one assertion path, a deterministic fold, two logs selected by configuration, and a run that shows the type verdict survives the swap unchanged. | sourced | `F-b2-04`, `F-b1-04` "nothing composes" |

## Entities

| Entity |
|---|
| `E-core-component-graph` |
| `E-seam-state` |
| `E-capability-state-persistence` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-event-log` |

## Contract

### Shapes (JSON Schema 2020-12)

**graph-store-binding (proposed shape; the wiring table, the backfill rules and the migration procedure are in references/implementation-notes.md)** (proposed; sources: `F-meta-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:store-binding:0.1",
  "title": "Graph store binding",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "record_kinds",
    "fold_order",
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
      "description": "The assertion record kinds this binding stores, e.g. node-asserted and edge-asserted."
    },
    "fold_order": {
      "type": "string",
      "minLength": 1,
      "description": "How records are ordered before folding. Two bindings that order differently must still produce one graph value."
    },
    "serves_walk": {
      "const": false,
      "description": "A store that answers neighbors or path_exists itself has taken a query language into the boundary; it returns records only."
    },
    "differs_in_execution_model": {
      "type": "array",
      "minItems": 1,
      "description": "Proposed: the shape build-adapter-pair defines; carried here so the pair is rejected when both roles are identical on every axis."
    }
  }
}
```

**graph-conformance-report (proposed shape; the fields the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:conformance-report:0.1",
  "title": "Graph conformance report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "graphs_folded",
    "edges_checked",
    "rejections",
    "false_accepts",
    "verdict_mismatches",
    "criterion_leaks"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    },
    "graphs_folded": {
      "type": "integer",
      "minimum": 0
    },
    "edges_checked": {
      "type": "integer",
      "minimum": 0
    },
    "rejections": {
      "type": "integer",
      "minimum": 0
    },
    "false_accepts": {
      "type": "integer",
      "minimum": 0
    },
    "verdict_mismatches": {
      "type": "integer",
      "minimum": 0,
      "description": "Structures on which two bindings disagreed about validity. The count a store that interprets records makes non-zero."
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
| core-graph owns the contract - the closed kind set, the three edge types, the type rules and the purity of validate (F-b2-04). This skill adds only how it is built: an implementation that adds a kind, relaxes a rule, or accepts a store handle as an argument to validate has produced a defect, not an extension. | sourced | `F-b2-04` "typed nodes, typed edges (existence / interface / implementation)" |
| The type checker links no persistence code. agentic-stack and build-adapter-pair state the swap test (F-meta-04); the consequence here is a build-level one - the module holding validate imports nothing from the store module, so the type checker compiles and runs with no binding present at all, and a build in which it cannot is where the boundary went wrong. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| Proposed: the store holds opaque records and never interprets one. Node and edge assertions are appended as records, the graph value is a fold over them, and the fold lives above the store; a binding that knows an edge from a ledger entry has taken seam-state's job into the persistence boundary. | proposed | `F-b5-04`, `F-b3-17` |
| Proposed: the fold is deterministic. The same records produce the same graph value and the same validity verdict under either binding, whatever order the store returns them in, because the fold sorts by the assertion's own identity rather than by arrival. A verdict that depends on which store answered is the defect the conformance run below exists to find. | proposed | `F-b1-06` |
| agentic-stack states design rule 7 (F-b1-08, F-b4-01). The consequence on this assertion path is placement: correlation, the policy consultation, the provenance attestation and the budget ceiling are attached where an assertion is made, and there is no flag, record field or binding option by which an asserter can ask to skip one. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record and agentic-stack state the labelling rule (F-part-c-08); the consequence here is that a conformance result is claimed until a run is attached naming the code version and the tree hash under test, and a store swap is exactly the change that looks identical in review and differs in a run. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Apply build-adapter-pair: the two binding records differ on at least one axis of differs_in_execution_model, and two bindings identical on every axis are one log written twice and fail the pair check; proposed pointer, see that skill. | proposed | `F-b1-04` "Every interface ships with at least two adapters" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: which binding served a fold, the store's file layout or stream topology, its lease mechanism, and its retention class. A caller sees a graph value and a validity report; anything else it can see it will eventually depend on, and the swap stops being possible. | proposed | `F-meta-04` |
| Proposed: criterion text, in any node attribute or edge label this code writes. core-graph states the grader rule on this structure (F-b1-07); the build consequence is that an assertion derived from a document step carries the check_id and never the criterion string, and the lint in step 7 is what keeps that true after the next refactor. | proposed | `F-b1-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the type checker as a module that imports no persistence code: it takes a graph value and returns a validity report, and the fold from records to a graph value lives in a separate module that depends on both. | core-graph requires validity to be decidable in memory; the only way that survives a deadline is to make it impossible to reach a store from the checker, so the dependency arrow is enforced by the build rather than by review. | sourced | `F-b1-02`, `X-core-graph-004` "The class AbstractGraph offers a minimal implementation of this Graph interface" |
| 2 | Give each producer a thin mapper into one assertion path. TARGET T1's three ways in - a human, an agent, and an internal or external event - share the constructor; a mapper may translate its payload and may not add a node, default a kind, or repair an endpoint on the way in. | core-graph requires one structure from every producer; making the constructor the single writer of node and edge fields is what stops a fourth mapper from quietly assigning a kind that the type rules would have refused. | sourced | `T-t1-01`, `T-t1-03` "An internal or external event must be able to enter the system." |
| 3 | Append every assertion as a record and derive the graph by folding those records; never mutate a stored node or edge in place, and write a retraction as a record carrying the edge_id it withdraws. | core-graph forbids removal, and a fold over immutable records is what makes the same walk reproducible across two stores; an update in place turns the store into the authority on history, which is the thing the swap is meant to be able to replace. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest" |
| 4 | Put the store behind the binding record, implement the role today against the appended, hash-chained file that holds run state now, and implement the role second on a different execution model rather than a different product. Fill in both bindings' execution-model axes before either is used. | build-adapter-pair owns this discipline (F-b1-04). The consequence here is specific: a second appended file would leave the fold free to keep every single-writer, whole-file, local-path assumption, and a log consumed by cursor from another process is what forces the fold to be order-independent and the records to be self-identifying. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| 5 | Migrate by backfill, dual-write and verdict-compare: assign kinds to the structures already recorded, write every new assertion to both bindings, fold and type-check both over the whole corpus, and cut over only when verdict_mismatches is zero and the old path has been read-only for a full retention window. | Proposed: the migration's risk is not new rejections but the old records, which carry no kind at all because the typed graph does not exist yet; the backfill is where a wrong kind becomes permanent, so the compare must run over the backfilled corpus before cut-over rather than over new assertions only. | proposed | `F-a5-03` |
| 6 | Wire the cross-cutting concerns into the assertion path: stamp the correlation attribute where the assertion is constructed, consult policy before the record is appended, attest the record digest, and read the budget ceiling from the envelope as a constant no asserter can override. | agentic-stack states design rule 7 (F-b1-08); the build consequence is placement, and the measured trace-context finding is why correlation is an explicit attribute set at the assertion rather than something inherited from whatever called in. | sourced | `F-b1-08`, `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Add a lint over the recorded assertions that greps each declared criterion string against every node attribute and edge label written from that document, and fail the build when the count is non-zero. | core-graph states the grader rule on this structure (F-b1-07), and on a graph it bites hardest because everything asserted is reachable by whatever walks it; a rule that is only stated is one the next refactor breaks silently, and the grep is what turns it into something that fails. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| 8 | Proposed: open references/implementation-notes.md when you are writing the fold, the backfill, the binding records or the wiring, or reviewing someone who did. The body of this skill is enough to review a design and to run the definition of done without it. | Proposed: the wiring table, the two binding records and the backfill rules are longer than the progressive-disclosure budget allows in the body, and a reader judging the build does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-evidence-record already state the configuration finding (F-a7-04). What it adds here: assert the binding actually in effect at run time and log it beside the counts, because a binding written in the documented place and overridden by a stored row produces a conformance run that folded the same log twice and reported adapters_run=2. | sourced | `F-a7-04` "had no runtime effect" |
| Proposed: run the conformance over both bindings on every change, not only when a binding changes. The failures worth catching come from the fold and the mappers - a new optional attribute, a changed sort key - and they show as a verdict that moved while no store was touched. | proposed | `F-b1-04` |
| build-evidence-record already states what the log that runs today buys (F-a5-03): a closing digest that opens the next run makes a manual edit between runs detectable. What this adds: carry that property through the migration, because a graph store without it cannot show that an edge was not asserted after the plan that walked it was priced. | sourced | `F-a5-03` "a manual edit between runs is detectable" |
| Keep the fold behind the same operations whichever binding served it, so the walk can be reimplemented without a contract change; the prior art for in-memory graphs stores nodes and edges in arrays with pointer-based references, which is an implementation choice a caller must never be able to observe. | sourced | `X-core-graph-008`, `T-t2-02` "Node and edge objects can be stored in arrays in an in-memory representation" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | The log the assertions sit in today. PASS.md Part A records the task store as JSONL, hash-chained, with each run's closing digest opening the next. The Graph is owned core surface with no adapter of its own, so what is adapted beneath it is the record store its node and edge assertions round-trip through - cap-state-persistence's row - and this skill tests the pair there. | Proposed: cannot admit concurrent asserters without an external lease, cannot return a subset of records without scanning the file, and cannot be folded by a reader in another process without sharing a filesystem path; it also holds no typed nodes today, which is what the backfill in step 5 has to reconcile. | Select the binding by the binding record, point both roles at the same fold and the same type checker, and run the conformance corpus through both. No core change is expected, because the fold and the checker never see the binding. | claimed | `F-a5-03`, `F-b3-17` "JSONL, hash-chained" |
| `E-swap-candidate-event-log` | second | The same append and read over opaque assertion records, served as a log consumed by cursor from outside the asserter's process, with each append conditional on the position the reader last saw. The row names the candidate class rather than a product, and the chain is kept as a record field rather than as file order. | Proposed: cannot rely on file order for the fold, cannot be read without a running server, and cannot hand back a filesystem path - which is the point, since anything it cannot implement was store detail that had leaked into the Graph's fold. | Proposed: the execution-model axes that must differ are processes_required_for_progress (zero for a local appended file, one for a served log) and locus_of_durability_and_verification (file order plus a linear chain, versus a per-record position plus a recomputed digest). Run one parameterised conformance over both roles and require identical graph values and identical validity verdicts. | claimed | `F-b3-17`, `F-b1-04` "event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.1 row C3, run across both bindings. Proposed tool, built with this component: `python3 tools/graph_conformance.py --binding bindings/today.json --binding bindings/second.json --generate 10000 --seed 1 --assertion-log out/recorded-assertions.jsonl --report out/graph-conformance.json`. Per binding it appends the generated assertions, folds them back and runs core-graph's property test, asserting `edges_checked > 0`, `rejections > 0` and `false_accepts == 0`; across bindings it asserts `adapters_run >= 2`, `verdict_mismatches == 0` and `criterion_leaks == 0`. |
| Expected | exit 0, one line per binding of the form `binding=<role> graphs_folded=10000 edges_checked=<m> rejections=<r> false_accepts=0`, then `adapters_run=2 verdict_mismatches=0 criterion_leaks=0`. |
| Deliberate breakage | Make the binding in role today collapse a retraction into a delete - drop the retracted edge's record instead of appending the retracting one - and change nothing else. |
| Expected failure | That binding now folds to a graph value missing the retracted edge and the record that withdrew it, the two bindings disagree on every structure containing a retraction, `verdict_mismatches` becomes non-zero, and the run exits non-zero while the other binding still reports `false_accepts=0` - so the report names which store broke rather than only that something did. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-04` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `core-graph`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| PASS.md Part A records no adapter for the Graph itself, so which pair does this skill's swap test actually exercise? | The Part B table has no Graph row: agentic-stack states (F-b2-07) that the five components are the owned surface and everything else is an adapter, so there is no adapter-today column to read. Applying TARGET T5's 1-3-1 to the gap, the three options were: declare no pair and record the gap, which leaves swappability untested on the component whose absence means nothing composes; adapt the record store the assertions round-trip through; or reuse the persistence pair cap-state-persistence-implement already owns, which duplicates a sibling and tests nothing about folding a graph. The second is recommended and is taken in the Adapters section. | The record-store pair above, tested by the conformance run; if a Graph adapter row is ever added to PASS.md, this question is reopened against it. | `F-b2-07`, `T-t5-02` "Everything else is an adapter." |
| Is the folded graph value cached per head, or recomputed on every read? | Measure fold wall time at today's record count and at a hundred times it, against the read rate the planner actually generates. A fold that is cheap at both makes a cache pure cost; a fold that is not is the first thing to make incremental. | Recompute, and add a cache only on a measured trigger. Anything that cannot be derived by folding the records from empty is not state, and a cache introduced before it is needed becomes a second authority on what the graph contains. | `F-b1-06` "Planning is a pure function and completes before execution begins." |
| Should the second binding serve neighbors and path_exists itself, rather than returning records for an in-memory fold? | Compare the record volume a bounded walk would have to transfer against the walk executed at the store, at the scale of well over a hundred agents running at a time. A transfer cost that dominates argues for pushing the walk down; anything less does not. | Records only, with serves_walk pinned false in the binding shape. core-graph's operations are defined over a graph value, and a store that answers walks becomes a query language the type checker would then be written against. | `T-t6-06`, `F-b2-04` "The target scale is well over a hundred agents running at a time" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
