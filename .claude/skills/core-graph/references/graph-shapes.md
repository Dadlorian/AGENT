# Graph shapes, the edge typing table and worked examples

Long material for `core-graph`. Everything here is **proposed** unless a kb id is given beside it.
The skill body is enough to assert into the graph and to judge an implementation; open this file only
when writing the full schemas, the typing table, the property-test generator, or a rejection instance.

Resolve every id below with `python3 tools/kb.py show <id>`.

## 1. Full node and edge schemas (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:node:0.1",
  "title": "GraphNode",
  "description": "Typed node. PASS.md fixes typed nodes and three typed edge kinds (F-b2-04); the five kinds are ours.",
  "type": "object",
  "additionalProperties": false,
  "required": ["node_id", "kind", "label"],
  "properties": {
    "node_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{2,127}$"},
    "kind": {"enum": ["document", "step", "interface", "implementation", "artifact"]},
    "label": {"type": "string", "minLength": 1, "maxLength": 200},
    "asserted_by": {
      "type": "string",
      "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "Recorded for audit. No consumer may branch on it."
    },
    "attributes": {
      "type": "object",
      "additionalProperties": true,
      "description": "Free data. May carry a check_id; may never carry criterion text (F-b1-07)."
    }
  }
}
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:graph:edge:0.1",
  "title": "GraphEdge",
  "type": "object",
  "additionalProperties": false,
  "required": ["edge_id", "edge_type", "from", "to"],
  "properties": {
    "edge_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{2,127}$"},
    "edge_type": {"enum": ["existence", "interface", "implementation"]},
    "from": {"type": "string"},
    "to": {"type": "string"},
    "retracts": {"type": "string", "description": "edge_id withdrawn by this assertion. Never a delete."},
    "asserted_by": {"type": "string", "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$"}
  }
}
```

JSON Schema alone cannot express a constraint that relates one instance to the kinds of two others, so
the table in section 2 is checked by the type checker, not by the dialect. That is why the definition of
done in the skill body is a property test and not a validation run.

## 2. The edge typing table (proposed)

| Edge type | Legal `from` kind | Legal `to` kind | Reads as | Rejected because |
|---|---|---|---|---|
| `existence` | `document`, `step`, `artifact` | `document`, `step`, `artifact`, `interface` | this thing exists within, or was derived from, that thing | never between two `implementation` nodes: that edge records one implementation reaching another directly (F-b1-02) |
| `interface` | `step`, `implementation` | `interface` | this thing requires that interface | a target that is not an `interface` node is a requirement on something never declared an interface |
| `implementation` | `implementation` | `interface` | this thing implements that interface | a target that is not an `interface` node is the row `docs/decomposition.md` section 3.1 C3 makes the property test find |

Two consequences worth stating once. First, an implementation reaches another implementation only as
`implementation -> interface <- implementation`, a path of length two, which is why `path_exists` takes a
`max_depth` and the planner's question is reachability rather than adjacency. Second, an `interface` node
with no incoming `implementation` edge is a **valid** graph and a **failed** composition; the type checker
must not conflate the two, and the walk is what reports the second.

## 3. Worked example A: a human asserts (proposed)

TARGET T1 lists three ways in (T-t1-01, T-t1-02, T-t1-03). None of them touches the graph directly: an
entry produces a document, and the document's steps are asserted as nodes. The producer survives only as
`asserted_by`, in the same actor grammar the entry envelope uses.

```json
{
  "nodes": [
    {"node_id": "fix-auth-timeout", "kind": "document", "label": "Sessions drop after 60s on the auth service", "asserted_by": "user:corey"},
    {"node_id": "fix-auth-timeout.triage", "kind": "step", "label": "name the failing component", "asserted_by": "user:corey"},
    {"node_id": "iface.fault-localisation", "kind": "interface", "label": "naming the failing component from a fault report", "asserted_by": "user:corey"}
  ],
  "edges": [
    {"edge_id": "e1", "edge_type": "existence", "from": "fix-auth-timeout", "to": "fix-auth-timeout.triage", "asserted_by": "user:corey"},
    {"edge_id": "e2", "edge_type": "interface", "from": "fix-auth-timeout.triage", "to": "iface.fault-localisation", "asserted_by": "user:corey"}
  ]
}
```

## 4. Worked example B: an event asserts, and an implementation appears (proposed)

The same structure entered by an internal producer (T-t1-03). The only differences are `asserted_by` and
the two rows that bind an implementation to the interface, which is what makes the step plannable.

```json
{
  "nodes": [
    {"node_id": "impl.triage-agent", "kind": "implementation", "label": "an agent that names the failing component", "asserted_by": "service:alerting"},
    {"node_id": "impl.log-scanner", "kind": "implementation", "label": "a scanner over recent traces", "asserted_by": "schedule:nightly-index"}
  ],
  "edges": [
    {"edge_id": "e3", "edge_type": "implementation", "from": "impl.triage-agent", "to": "iface.fault-localisation", "asserted_by": "service:alerting"},
    {"edge_id": "e4", "edge_type": "implementation", "from": "impl.log-scanner", "to": "iface.fault-localisation", "asserted_by": "schedule:nightly-index"}
  ]
}
```

`path_exists("fix-auth-timeout.triage", "impl.triage-agent", ["interface", "implementation"], 2)` now
returns found, and that is the whole of "this step composes".

## 5. Worked example C: an agent asserts, and withdraws (proposed)

An agent entering the system (T-t1-02) asserts and later withdraws. Retraction is an assertion:

```json
{
  "edges": [
    {"edge_id": "e5", "edge_type": "implementation", "from": "impl.log-scanner", "to": "iface.fault-localisation",
     "asserted_by": "agent:partner-sre-bot"},
    {"edge_id": "e6", "edge_type": "implementation", "from": "impl.log-scanner", "to": "iface.fault-localisation",
     "retracts": "e5", "asserted_by": "agent:partner-sre-bot"}
  ]
}
```

A, B and C are three producers of one structure. The only field that differs is `asserted_by`, and nothing
downstream may branch on it.

## 6. Worked example D: the failure shape (proposed)

What an asserter receives when an edge is refused. `cap-errors` owns the shape and its closed registry
(F-b3-13); `core-graph` adds no failure format of its own. The type suffix here is **pending
registration** - see the skill's first open question - and until the registry row lands an implementation
returns `document-invalid` with the same `causes` rather than inventing a type at the call site.

```json
{
  "sent": {
    "edge_id": "e7",
    "edge_type": "existence",
    "from": "impl.triage-agent",
    "to": "impl.log-scanner",
    "asserted_by": "agent:partner-sre-bot"
  },
  "received_on_the_wire": {
    "media_type": "application/problem+json",
    "type": "urn:agentic:problem:graph-assertion-invalid",
    "title": "Graph edge violates a type rule",
    "status": 422,
    "detail": "1 refused edge; see causes",
    "retryable": false,
    "instance": "urn:agentic:core:graph:edge:e7",
    "causes": [
      {
        "type": "urn:agentic:problem:graph-assertion-invalid",
        "title": "existence edge between two implementation nodes",
        "status": 422,
        "detail": "from kind 'implementation', to kind 'implementation'; rule: existence is never accepted between two implementation nodes",
        "retryable": false
      }
    ]
  },
  "what_the_asserter_does": "declares the interface both sides share, then asserts two implementation edges to it; there is no second round of discovery"
}
```

The asserter branches on `type` and reads `from kind` and `to kind` from the members, never on the wording
of `detail`. This instance is what the invariant "every rejected assertion comes back as a typed problem"
looks like on the wire, and it is the same refusal design rule 1 (F-b1-02) states in prose.

## 7. Property-test generator (proposed)

The generator behind the skill's definition of done. It must emit, among random well-typed graphs, at
least these classes, each at a known rate so `rejections` is non-zero by construction:

| Class | Shape | Expected |
|---|---|---|
| well-typed | every edge legal per section 2 | admitted |
| bad implementation target | `implementation` edge to a `document`, `step` or `artifact` node | rejected |
| implementation shortcut | `existence` edge between two `implementation` nodes | rejected |
| dangling endpoint | edge naming a `node_id` that was never asserted | rejected |
| unknown kind | node whose `kind` is outside the closed set | rejected |
| criterion leak | node `attributes` carrying a `criterion` key | rejected (F-b1-07) |

The seed is echoed in the report so a failing run is reproducible; a generator whose seed is not recorded
turns a counterexample into an anecdote.
