---
name: core-graph
description: The Graph: typed nodes and three typed edge kinds - existence, interface, implementation - whose validity is decidable in memory with no store attached, so that design rule 1 stops being a review convention and becomes a check a machine runs. Load it before adding a node kind or an edge kind, before relaxing a type rule so a rejected edge can get through, when a step has to be expanded into the implementations that could serve it, and when someone asks 'how do we know this composes', 'why can one adapter not just call another', 'where does the platform record what implements what', or 'why does this structure not have a head or a snapshot'. Persistence belongs to the state seam; a node identified by a file offset or a row key means the boundary was drawn wrong.
---

# core-graph

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one typed structure - typed nodes and typed existence, interface and implementation edges - as the thing without which nothing composes, and keep its validity decidable from the structure alone. | sourced | `F-b2-04`, `F-b2-01` "typed nodes, typed edges (existence / interface / implementation)" |

## Entities

| Entity |
|---|
| `E-core-component-graph` |
| `E-core-component-document` |
| `E-core-component-planner` |
| `E-seam-state` |
| `E-rule-b1-1` |
| `E-rule-b1-6` |
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
| assert_node (this component's own call; PASS.md names the structure, not the calls) | a node record carrying a node_id, a kind drawn from the closed kind set, a label and free attributes | the admitted node, or a typed problem naming the kind that is not in the set; pure and total, with no store access and no clock | sourced | `F-b2-04` "typed nodes, typed edges (existence / interface / implementation)" |
| assert_edge (this component's own call; the edge_type enum is PASS.md's, the operation's pure I/O contract is not) | an edge record carrying an edge_type of existence, interface or implementation, and the node_ids of its two endpoints | the admitted edge, or a typed problem naming the endpoint kinds and the type rule the edge violated; pure and total | sourced | `F-b2-04` "typed nodes, typed edges (existence / interface / implementation)" |
| validate (proposed operation; the operation this component is judged on) | a graph value: a set of nodes and a set of edges, held in memory (proposed) | a validity report counting nodes_checked, edges_checked, rejections and false_accepts, plus one typed problem per rejected edge; a pure function of the value alone (proposed) | proposed | `F-b2-04`, `X-core-graph-002` |
| neighbors (proposed accessor) | a node_id, one edge_type, and a direction (proposed) | the nodes reachable in exactly one hop across edges of that type, without materialising the rest of the graph (proposed) | proposed | `X-core-graph-003` |
| path_exists (proposed accessor) | a from node_id, a to node_id, the edge types the walk may cross, and a max_depth (proposed) | found plus the path that was taken, so 'is an implementation reachable for this interface' is answerable without loading the graph (proposed) | proposed | `X-core-graph-003` |
| retract (proposed operation) | the edge_id to retract and the reason (proposed) | a new edge assertion carrying retracts set to that edge_id; the retracted edge is never removed, so a graph read twice never loses a fact between reads (proposed) | proposed | `F-b2-04` |

### Shapes (JSON Schema 2020-12)

**graph-node (proposed summary shape; the full node and edge schemas, the edge typing table, a worked assertion for each of TARGET T1's three ways in and a worked rejection are in references/graph-shapes.md)** (proposed; sources: `F-b2-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:node:0.1",
  "title": "GraphNode",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "node_id",
    "kind",
    "label"
  ],
  "properties": {
    "node_id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9._-]{2,127}$",
      "description": "A name, never a location. A file offset or a row key here is the storage engine's shape leaking into the core."
    },
    "kind": {
      "enum": [
        "document",
        "step",
        "interface",
        "implementation",
        "artifact"
      ]
    },
    "label": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "asserted_by": {
      "type": "string",
      "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "The subject that asserted it, in the entry envelope's actor grammar. Recorded, never branched on."
    },
    "attributes": {
      "type": "object",
      "description": "Free key/value data. Criterion text is forbidden here; see Deliberately not exposed."
    }
  }
}
```

**graph-edge (proposed summary shape; the three type rules in full are in references/graph-shapes.md)** (proposed; sources: `F-b2-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:edge:0.1",
  "title": "GraphEdge",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "edge_id",
    "edge_type",
    "from",
    "to"
  ],
  "properties": {
    "edge_id": {
      "type": "string",
      "minLength": 1
    },
    "edge_type": {
      "enum": [
        "existence",
        "interface",
        "implementation"
      ]
    },
    "from": {
      "$ref": "urn:agentic:core:graph:node:0.1#/properties/node_id"
    },
    "to": {
      "$ref": "urn:agentic:core:graph:node:0.1#/properties/node_id"
    },
    "retracts": {
      "type": "string",
      "description": "edge_id this assertion retracts. Retraction is an assertion, never a delete."
    },
    "asserted_by": {
      "$ref": "urn:agentic:core:graph:node:0.1#/properties/asserted_by"
    }
  }
}
```

**graph-validity-report (proposed shape; the fields the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:validity-report:0.1",
  "title": "Graph validity report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "nodes_checked",
    "edges_checked",
    "rejections",
    "false_accepts"
  ],
  "properties": {
    "nodes_checked": {
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
      "minimum": 0,
      "description": "Edges admitted that a type rule forbids. The count a widened check makes non-zero."
    },
    "problems": {
      "type": "array",
      "items": {
        "$ref": "urn:agentic:problem:0.1"
      },
      "description": "One typed problem per rejection, in the shape cap-errors defines."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The Graph is typed structure, not a service: typed nodes and three typed edge kinds - existence, interface and implementation - and without it nothing composes. | sourced | `F-b2-04` "nothing composes" |
| Design rule 1 is decidable here rather than argued in review. agentic-stack states the rule as a test (F-b1-02); the consequence on this structure is that an existence edge between two implementation nodes is rejected, because such an edge records one implementation reaching another directly, and the only legal route between two implementations runs out through an interface node and back. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| Proposed: an implementation edge's target is always a node of kind interface, and its source is always a node of kind implementation. An implementation edge pointing at anything else is the assertion that something implements a thing that was never declared an interface, which is the same defect one step earlier. Research query: does PASS.md's three-edge-kind fact (F-b2-04) itself state the source/target kind constraint on an implementation edge, or is that this skill's own refinement? | proposed | `F-b2-04`, `X-core-graph-001` |
| Proposed: validity is decidable in memory. validate is a pure function of the graph value alone - no store, no head, no clock, no network - so a rule that cannot be decided without a lookup is a seam concern and does not belong in this contract. Research query: is there a fetched primary source on pure in-memory graph validation, beyond the search-only distributed-graph-database record (X-core-graph-002) whose validation context is a sharded write path rather than a pure function? | proposed | `X-core-graph-002` |
| Persistence is somewhere else. seam-state owns the row in which the graph and the ledger persist (F-b5-04); the consequence here is that this contract carries no head, no at_head parameter, no retention class and no write model, and a node_id that is a file offset or a row key is a storage engine's shape that has reached the core. | sourced | `F-b5-04` "the graph and the ledger persist" |
| Proposed: the node kind set and the edge type set are both closed. PASS.md fixes three edge kinds (F-b2-04); the five node kinds are ours, and either set grows only by changing this contract, because a kind smuggled into a label or an attribute is a rule that can be checked only by parsing a string. | sourced | `F-b2-04`, `T-t3-02` "typed nodes, typed edges (existence / interface / implementation)" |
| Every rejected assertion comes back as a typed problem. cap-errors owns the shape and the standard that governs it, and core-document already applies the same rule to a refused declaration (F-b4-07); the consequence here is that a caller repairing a graph branches on the problem type and reads the offending edge and rule from the members, never on a message's wording. | sourced | `F-b4-07`, `F-b3-13` "Never parsed from prose" |
| Proposed, following the reference example in docs/reference/composable-plan.md: the blast radius of a change is counted over implementation edges only. A walk that counts everything downstream with every edge weighted the same over-estimates most where the encapsulation is best, because good layering produces many interface edges and few implementation ones, so the better the design the more the heuristic punishes it; a walk that sizes the effect of a change without filtering by edge type is a defect in the walk rather than a conservative estimate. | proposed | `REF-5-4-26`, `REF-12-06` "Count implementation edges instead" |
| Proposed, following the same reference: depth is bounded, and the bound is checked when the structure is resolved rather than when the work runs. A composition that would nest past the bound is refused before anything executes, which is why max_depth is a parameter of the walk in this contract and not a counter kept by an executor; unbounded nesting is a hazard already met in practice, not a theoretical one. | proposed | `REF-5-2-13`, `REF-5-3-05` "Depth must be bounded, and checked at resolve time, not run time" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Criterion text, as a node attribute, an edge label or anything else reachable by a walk. agentic-stack and core-document state design rule 6 (F-b1-07); on this structure it bites harder than elsewhere, because everything on the graph is reachable by whatever is allowed to walk it, including the unit being graded, so the graph holds a check_id and never the criterion behind it. | sourced | `F-b1-07` "never the criterion it is judged against" |
| Products, endpoints, store paths, row keys and file offsets. agentic-stack states the rule (F-part-c-09); the consequence here is that a node names a thing and never says where the thing is kept, so the same graph survives every swap of the store beneath it. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| Proposed: the head, the snapshot, the fencing token and the retention class. Those are seam-state's, and importing any of them here would make a pure validity check depend on which records happened to have been written. | sourced | `F-b5-04` "the graph and the ledger persist" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Give every node a kind from the closed set before you assert it, and never encode the kind in the label or in an attribute. If the thing you are asserting has no kind, that is the finding, not an inconvenience. | The type rules decide validity from kinds alone; a kind that lives inside a string can only be checked by parsing, and a parser in the middle of a type check is where the check quietly stops being decidable. | sourced | `X-core-graph-001`, `F-b2-04` "A typed graph schema defines a set of named labeled nodes with properties of specific data types" |
| 2 | Assert each edge with its type and let the type rules reject it. Do not pre-filter in the caller to avoid a rejection, and do not repair an endpoint kind on the way in. | Rejections are the evidence the check runs at all. agentic-stack states the criterion rule (F-part-c-04); the consequence here is that the definition of done below asserts rejections greater than zero, and a caller that filters first produces a report in which nothing was ever rejected and nothing was ever checked. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| 3 | Route every implementation-to-implementation relation through an interface node: assert the interface, an implementation edge from each side, and no existence edge between the two implementations. | agentic-stack states design rule 1 as a test (F-b1-02); this step is what makes the rule mechanical here, because the shortcut edge is exactly the one the type rule refuses and the one a hurried author reaches for. | sourced | `F-b1-02`, `X-core-graph-004` "The Graph interface, at the top of the hierarchy, defines all high-level graph operations." |
| 4 | Expand a step into candidate implementations by walking typed edges - neighbors for one hop, path_exists with a max_depth for reachability - never by materialising the whole graph and filtering it. | agentic-stack states design rule 5 as a test (F-b1-06); a bounded walk is answerable at a pinned snapshot and its cost is knowable in advance, while 'load the graph and filter' has a cost that depends on how much unrelated history happens to have accumulated. | sourced | `F-b1-06`, `X-core-graph-003` "These methods have O(1) complexity." |
| 5 | Keep every validity rule decidable from the graph value. When a proposed rule needs a store lookup, a head or a timestamp, raise it as a state-seam concern instead of adding a query to this contract. | The manifest note for this component is that persistence is a separate seam, and a single query parameter accepted here is how the graph acquires a storage engine's shape one field at a time. | sourced | `F-b5-04`, `X-core-graph-005` "The implementer has the flexibility to change the module as long as the module still satisfies its interface." |
| 6 | Return every rejection as the problem shape cap-errors defines, carrying the offending edge_id, both endpoint kinds and the rule that refused it; never raise a bare type error across this boundary, and never invent a problem type suffix at the call site. | cap-errors owns the closed registry and the standard behind it, and core-document already adopts it for a refused declaration (F-b3-13, F-b4-07). What this adds: a rejection is the only thing a caller ever sees from this component, so it is where a graph author either gets a machine-readable refusal or a sentence. | sourced | `F-b3-13`, `F-b4-07` "— adopt the RFC directly" |
| 7 | Judge a candidate implementation on four properties: rejections greater than zero and false_accepts equal to zero over generated graphs; identical validity verdicts for the same structure asserted through any of TARGET T1's three ways in; no criterion string reachable as a node attribute or an edge label; and a validate call that completes with no store configured at all. | Each is a count or an absence rather than an exit code, which is what the measured green-gate finding agentic-stack and build-definition-of-done state (F-a7-03) costs to satisfy; the fourth is the one that catches a persistence dependency that crept in, because it fails only when a store was quietly required. | sourced | `F-a7-03`, `T-t1-01` "Those establish well-formedness, not correctness" |
| 8 | Record the schema dialect and the problem-details standard as unverified until their published specifications have been read in an environment that can fetch them, and write no version string that was not read. | build-skill-authoring requires a standard and its version to be cited rather than recalled, and a version number nobody read is a fabrication with a decimal point in it. | sourced | `F-part-c-10` "Cite the standard and its version" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-definition-of-done already state the green-gate finding (F-a7-03). What it adds here: a graph that validates has been shown well-typed, not composable - a walk that finds no implementation for a declared interface is a valid graph and a failed composition - so a passing type check must never be reported as evidence that the work can be planned. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Validate nodes first, then edges, so that an edge rejection is never a symptom of an endpoint whose kind was never checked; the prior art for graph type conformance identifies conforming nodes first and uses that to check edges by the same procedure. | sourced | `X-core-graph-002` "nodes are identified that conform to each node type, and this information is used to identify edges that conform to each edge type" |
| Proposed: generate the property-test corpus rather than hand-writing it, and keep the seed in the report. Hand-written cases encode the rules their author already believed, and the false-accept this component exists to prevent is by definition one nobody thought to write down. Research query: does F-part-c-04's breakage-corpus discipline itself recommend generating rather than hand-writing the corpus, or is that this skill's own extension? | proposed | `F-part-c-04` |
| Keep the operations free of anything only one traversal strategy could serve, so the walk can be reimplemented without a contract change; the prior art for graph libraries keeps storage and indexing behind the interface for exactly this reason. | sourced | `X-core-graph-004`, `T-t2-02` "without explicitly defining the data structures for storage and indexing as these are managed by the graph backend" |
| Keep the closed kind set small enough that a reader can hold it in mind while drawing a graph on paper. Five node kinds and three edge kinds fit; a fifteenth kind added to avoid one awkward assertion is what turns a structure people can reason about into one they only query - core-document cites the same usability requirement for its own closed step vocabulary; this row applies it to the Graph's node and edge kinds instead. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.1 row C3, made precise. Proposed tool, built with this component: `python3 tools/graph_typecheck.py --generate 10000 --seed 1 --report out/graph-validity.json`. It runs the property test over 10,000 generated graphs whose generator emits both an `implementation` edge whose target node is not of kind `interface` and an `existence` edge between two `implementation` nodes, and asserts `rejections > 0`, `false_accepts == 0`, `nodes_checked > 0` and `edges_checked > 0`, with no store configured in the environment. |
| Expected | exit 0 and one report line of the form `graphs=10000 nodes_checked=<n> edges_checked=<m> rejections=<r> false_accepts=0`, with n, m and r each greater than zero and the seed echoed. |
| Deliberate breakage | Widen the edge type check to accept any node kind as an `implementation` target, changing nothing else. |
| Expected failure | A counterexample - an `implementation` edge pointing at a node of kind `document` - is found in under 100 generated cases, `false_accepts` becomes non-zero, `rejections` drops by the count of that class, and the run exits non-zero while `nodes_checked` and `edges_checked` are unchanged, so the report names which rule was widened rather than only that something failed. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b2-04` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`, `core-document`

Used by: `compose-operators`, `core-graph-implement`, `core-planner`, `seam-state`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| cap-errors' closed problem registry has no row for a refused graph assertion, so which type does a rejected edge carry? | cap-errors requires 1-3-1 rather than minting a suffix at the call site, so the three options were: reuse `document-invalid`, which misnames the artifact and makes a caller repairing an edge parse a document error; mint a suffix locally, which the closed registry forbids; or add one row `graph-assertion-invalid` (422, not retryable, extension member `causes`, one per refused edge) to docs/decomposition.md section 2.1.6 and use it. The third is recommended and is what references/graph-shapes.md shows, pending that row. | `urn:agentic:problem:graph-assertion-invalid`, marked proposed and pending registration; until the row lands, an implementation returns `document-invalid` with the offending edge in `causes` rather than inventing a type. | `T-t5-02`, `F-b3-13` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |
| Is an agent a node kind of its own, or an `implementation` node bound to an `interface` node that names what it is good at? | Count, over the agent registry, how many agents carry an attribute no implementation node can hold and how many selections need a rule that is not reachability. A non-trivial count argues for a sixth kind; a count near zero argues that agents are implementations and nothing more. | An `implementation` node, because TARGET T6.5 defines an agent by what it is good at, which is exactly an interface it implements, and this keeps the closed kind set at five and reuses the walk the planner already performs. | `T-t6-05`, `F-b2-04` "Each agent is defined up front by what it is good at" |
| Does one `existence` edge type carry both containment and derivation, or do those need separate types? | Audit the walks the planner and the composition layer actually perform: if either has to filter existence edges by an attribute to get a correct answer, the single type is doing two jobs and the filter is a fourth edge type in disguise. | One `existence` type. PASS.md fixes three edge kinds, and adding a fourth changes the core's own surface, so the bar for it is a measured walk that cannot be written correctly without it. | `F-b2-04`, `F-b2-07` "This is the entire owned surface." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
