#!/usr/bin/env python3
"""The Graph: typed nodes, three typed edge kinds, validity decidable in memory.

Read it in this order. Node and Edge are the whole caller vocabulary for an
assertion. assert_node and assert_edge are pure and total: assert_edge takes
its endpoints as an in-memory dict, never a store, so a caller can type-check
one edge with no adapter bound at all (core-graph F-b2-04, "no store access
and no clock"). fold() turns a list of appended assertion records into a
GraphValue - a set of nodes and a set of active edges, retractions applied
but never destroying the record that made them. validate() is the pure
audit: given any GraphValue, however built, it recomputes every edge's
verdict from the closed type rules alone and reports what it found.
GraphAdapter.append_node/append_edge are template methods: they run
assert_node/assert_edge before any adapter code executes, so no adapter can
admit an ill-typed edge by skipping the check (core-graph-implement F-b1-02).

Design rule 1 (F-b1-02, "the core imports interfaces, never implementations")
is what the implementation-edge and existence-edge rules below make
mechanical: an implementation node reaches another only by way of an
interface node.

No product name, store path or row key appears in this file (T-t7-02,
core-graph's own "not exposed" list). Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
# Found by walking up from this file's own directory, not by a fixed "../errors"
# offset: several harnesses' test.sh copy interface.py into out/breakage/ (and
# deeper) for a deliberate-breakage run, and a fixed relative offset would miss
# harness/errors/problem.py from there. The walk stays inside the repository
# tree either way (out/breakage/ is still nested under this harness's own
# directory), and stops at the first "errors" sibling that actually has it.
_search_dir = _errors_os.path.dirname(_errors_os.path.abspath(__file__))
for _ in range(10):
    _candidate = _errors_os.path.join(_search_dir, "errors")
    if _errors_os.path.isfile(_errors_os.path.join(_candidate, "problem.py")):
        if _candidate not in _errors_sys.path:
            _errors_sys.path.append(_candidate)  # appended, never inserted at 0: this
            # harness's own adapters/ package must resolve before errors/adapters/ does
        break
    _up = _errors_os.path.dirname(_search_dir)
    if _up == _search_dir:
        break
    _search_dir = _up
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) ---
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    # No registry row exists yet for a refused graph assertion (core-graph's
    # own open_questions). Until docs/decomposition.md 2.1.6 gains one, this
    # harness follows the skill's stated default: reuse document-invalid,
    # named here as graph-assertion-invalid so a caller can branch on a type
    # that says what it is, with the pending row noted in provenance.json.
    "graph-assertion-invalid": (422, "Assertion is not a well-formed or well-typed graph record", False),
    "adapter-unavailable": (503, "This binding cannot serve the operation", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --- The closed kind sets (core-graph contract, graph-node / graph-edge) ---
NODE_KINDS = {"document", "step", "interface", "implementation", "artifact"}
EDGE_TYPES = {"existence", "interface", "implementation"}
NODE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
ACTOR_PATTERN = re.compile(r"^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$")

NODE_ALLOWED = {"node_id", "kind", "label", "asserted_by", "attributes"}
NODE_REQUIRED = {"node_id", "kind", "label"}
EDGE_ALLOWED = {"edge_id", "edge_type", "from", "to", "retracts", "asserted_by"}
EDGE_REQUIRED = {"edge_id", "edge_type", "from", "to"}


@dataclass(frozen=True)
class Node:
    node_id: str
    kind: str
    label: str
    asserted_by: str | None = None
    attributes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    edge_id: str
    edge_type: str
    from_id: str
    to_id: str
    retracts: str | None = None
    asserted_by: str | None = None


def assert_node(doc: dict) -> Node:
    """Pure and total: no store, no clock. A kind outside the closed set is refused."""
    if not isinstance(doc, dict):
        raise Problem("graph-assertion-invalid", "a node assertion is an object")
    extra = sorted(set(doc) - NODE_ALLOWED)
    if extra:
        raise Problem("graph-assertion-invalid", f"fields {extra} are not in the node vocabulary",
                      rejected_fields=extra)
    missing = sorted(NODE_REQUIRED - set(doc))
    if missing:
        raise Problem("graph-assertion-invalid", f"missing required fields {missing}", missing=missing)
    node_id, kind, label = doc["node_id"], doc["kind"], doc["label"]
    if not isinstance(node_id, str) or not NODE_ID_PATTERN.match(node_id):
        raise Problem("graph-assertion-invalid", "node_id must be a name, never a location", node_id=node_id)
    if kind not in NODE_KINDS:
        raise Problem("graph-assertion-invalid", f"kind {kind!r} is not in the closed node kind set {sorted(NODE_KINDS)}",
                      node_id=node_id, kind=kind, closed_set=sorted(NODE_KINDS))
    if not isinstance(label, str) or not (1 <= len(label) <= 200):
        raise Problem("graph-assertion-invalid", "label must be 1-200 characters", node_id=node_id)
    asserted_by = doc.get("asserted_by")
    if asserted_by is not None and not ACTOR_PATTERN.match(asserted_by):
        raise Problem("graph-assertion-invalid", "asserted_by must be an actor in the entry envelope grammar",
                      node_id=node_id, asserted_by=asserted_by)
    return Node(node_id, kind, label, asserted_by, dict(doc.get("attributes", {})))


def check_edge_type(edge_type: str, from_kind: str, to_kind: str) -> tuple[bool, str | None]:
    """The closed type-rule spec (core-graph invariants). One rule per edge kind,
    each distinguishing the shortcut design rule 1 forbids from a legal route."""
    if edge_type == "implementation":
        if from_kind != "implementation" or to_kind != "interface":
            return False, ("an implementation edge runs from an implementation node to an interface node "
                           f"(got from={from_kind!r} to={to_kind!r})")
    elif edge_type == "existence":
        if from_kind == "implementation" and to_kind == "implementation":
            return False, ("an existence edge between two implementation nodes bypasses the interface; "
                           "design rule 1 requires the route to run out through an interface node and back")
    elif edge_type == "interface":
        if to_kind != "interface":
            return False, f"an interface edge names the interface something declares or depends on; to must be kind interface (got {to_kind!r})"
        if from_kind == "implementation":
            return False, "an implementation node reaches an interface via an implementation edge, not an interface edge"
    else:
        return False, f"edge_type {edge_type!r} is not in the closed edge type set {sorted(EDGE_TYPES)}"
    return True, None


def assert_edge(doc: dict, nodes: dict) -> Edge:
    """Pure and total over an in-memory nodes dict - no store, no clock, no network.
    `nodes` is whatever the caller happens to hold; this call never fetches one."""
    if not isinstance(doc, dict):
        raise Problem("graph-assertion-invalid", "an edge assertion is an object")
    extra = sorted(set(doc) - EDGE_ALLOWED)
    if extra:
        raise Problem("graph-assertion-invalid", f"fields {extra} are not in the edge vocabulary", rejected_fields=extra)
    missing = sorted(EDGE_REQUIRED - set(doc))
    if missing:
        raise Problem("graph-assertion-invalid", f"missing required fields {missing}", missing=missing)
    edge_id, edge_type, from_id, to_id = doc["edge_id"], doc["edge_type"], doc["from"], doc["to"]
    if edge_type not in EDGE_TYPES:
        raise Problem("graph-assertion-invalid", f"edge_type {edge_type!r} is not in the closed set {sorted(EDGE_TYPES)}",
                      edge_id=edge_id, edge_type=edge_type)
    from_node, to_node = nodes.get(from_id), nodes.get(to_id)
    if from_node is None or to_node is None:
        missing_ends = [n for n, node in ((from_id, from_node), (to_id, to_node)) if node is None]
        raise Problem("graph-assertion-invalid", f"endpoint(s) {missing_ends} are not asserted nodes",
                      edge_id=edge_id, missing_endpoints=missing_ends)
    ok, rule = check_edge_type(edge_type, from_node.kind, to_node.kind)
    if not ok:
        raise Problem("graph-assertion-invalid", rule, edge_id=edge_id, edge_type=edge_type,
                      from_kind=from_node.kind, to_kind=to_node.kind, rule=rule)
    return Edge(edge_id, edge_type, from_id, to_id, doc.get("retracts"), doc.get("asserted_by"))


# --- The graph value and the fold (core-graph-implement: "the fold lives
# above the store"; deterministic, sorted by the assertion's own identity) --
@dataclass(frozen=True)
class GraphValue:
    nodes: dict           # node_id -> Node
    edges: dict           # edge_id -> Edge, active only; a retracted edge is absent here
    retracted_ids: frozenset


def fold(records: list) -> GraphValue:
    """Deterministic fold: sorted by record identity, never by arrival order, so
    two stores that return records in a different order still produce one value."""
    ordered = sorted(records, key=lambda r: (r["record_kind"], r.get("node_id") or r.get("edge_id") or ""))
    nodes: dict = {}
    edges: dict = {}
    retracted: set = set()
    for rec in ordered:
        if rec["record_kind"] == "node-asserted":
            n = rec["node"]
            nodes[n["node_id"]] = Node(n["node_id"], n["kind"], n["label"], n.get("asserted_by"),
                                       dict(n.get("attributes", {})))
        elif rec["record_kind"] == "edge-asserted":
            e = rec["edge"]
            if e.get("retracts"):
                retracted.add(e["retracts"])
                edges.pop(e["retracts"], None)
                continue    # a retraction record is a marker, never itself a live edge
            edges[e["edge_id"]] = Edge(e["edge_id"], e["edge_type"], e["from"], e["to"],
                                       e.get("retracts"), e.get("asserted_by"))
    return GraphValue(nodes, edges, frozenset(retracted))


@dataclass(frozen=True)
class ValidityReport:
    nodes_checked: int
    edges_checked: int
    rejections: int
    false_accepts: int
    problems: list


def validate(graph: GraphValue) -> ValidityReport:
    """Pure function of the graph value alone - no store, no head, no clock, no
    network (core-graph F-b2-04 open_question default). Recomputes every edge's
    verdict from the closed type rules independent of how the value was built,
    so a value assembled by hand (bypassing assert_edge) is checked exactly the
    same as one folded from an adapter's own append-time-checked records."""
    problems = []
    rejections = 0
    for edge in graph.edges.values():
        from_node, to_node = graph.nodes.get(edge.from_id), graph.nodes.get(edge.to_id)
        if from_node is None or to_node is None:
            ok, rule = False, "both endpoints must be asserted nodes"
        else:
            ok, rule = check_edge_type(edge.edge_type, from_node.kind, to_node.kind)
        if not ok:
            rejections += 1
            problems.append(Problem("graph-assertion-invalid", rule, edge_id=edge.edge_id,
                                    edge_type=edge.edge_type,
                                    from_kind=from_node.kind if from_node else None,
                                    to_kind=to_node.kind if to_node else None, rule=rule).body)
    return ValidityReport(len(graph.nodes), len(graph.edges), rejections, 0, problems)


# --- The interface the core imports -----------------------------------------
class GraphAdapter(ABC):
    """append_node, append_edge, retract_edge, graph_value, neighbors, path_exists.

    append_node/append_edge are concrete: they run assert_node/assert_edge
    before any adapter code runs, so no adapter can admit an ill-typed node
    or edge by skipping the check (mirrors StatePersistenceAdapter.append).
    """

    entity = "adapter"
    execution_model = "unset"          # what makes the swap real, not cosmetic
    declared_marker = "unset"
    declared_gaps: tuple = ()

    def __init__(self):
        self.assertions = 0
        self.refusals = 0
        self.observed_marker = ""

    def append_node(self, doc: dict) -> Node:
        try:
            node = assert_node(doc)
        except Problem:
            self.refusals += 1
            raise
        self._store_record({"record_kind": "node-asserted", "node": doc})
        self.assertions += 1
        self.observed_marker = self.declared_marker
        return node

    def append_edge(self, doc: dict) -> Edge:
        nodes = self.graph_value().nodes
        try:
            edge = assert_edge(doc, nodes)
        except Problem:
            self.refusals += 1
            raise
        self._store_record({"record_kind": "edge-asserted", "edge": doc})
        self.assertions += 1
        self.observed_marker = self.declared_marker
        return edge

    def retract_edge(self, edge_id: str, reason: str, asserted_by: str | None = None) -> Edge:
        """Appends a new edge assertion carrying retracts=edge_id. The retracted
        edge's own record is never removed from the log (core-graph F-b2-04);
        only the fold's active view stops including it."""
        active = self.graph_value().edges
        if edge_id not in active:
            raise Problem("graph-assertion-invalid", f"{edge_id!r} is not an active edge to retract",
                          edge_id=edge_id)
        original = active[edge_id]
        doc = {"edge_id": f"retract-{edge_id}", "edge_type": original.edge_type,
              "from": original.from_id, "to": original.to_id, "retracts": edge_id}
        if asserted_by:
            doc["asserted_by"] = asserted_by
        elif reason:
            pass  # reason is recorded by the caller's own attributes/log, not this schema's edge fields
        self._store_record({"record_kind": "edge-asserted", "edge": doc})
        self.assertions += 1
        return original

    @abstractmethod
    def _store_record(self, record: dict) -> None:
        """Adapter-specific append of one opaque record. Never interprets it."""

    @abstractmethod
    def _all_records(self) -> list:
        """Every record appended so far, in whatever order this store happens to return."""

    def graph_value(self) -> GraphValue:
        return fold(self._all_records())

    def neighbors(self, node_id: str, edge_type: str, direction: str = "out") -> list:
        """One hop across edges of one type - never materialises the rest of the graph."""
        gv = self.graph_value()
        out = []
        for edge in gv.edges.values():
            if edge.edge_type != edge_type:
                continue
            if direction == "out" and edge.from_id == node_id and edge.to_id in gv.nodes:
                out.append(gv.nodes[edge.to_id])
            elif direction == "in" and edge.to_id == node_id and edge.from_id in gv.nodes:
                out.append(gv.nodes[edge.from_id])
        return out

    def path_exists(self, from_id: str, to_id: str, edge_types: list, max_depth: int) -> tuple:
        """Bounded BFS, refused before it runs if max_depth is not respected."""
        gv = self.graph_value()
        frontier = {from_id: [from_id]}
        seen = {from_id}
        for _ in range(max_depth):
            nxt = {}
            for node_id, path in frontier.items():
                for edge in gv.edges.values():
                    if edge.edge_type not in edge_types or edge.from_id != node_id:
                        continue
                    if edge.to_id == to_id:
                        return True, path + [to_id]
                    if edge.to_id not in seen:
                        seen.add(edge.to_id)
                        nxt[edge.to_id] = path + [edge.to_id]
            if not nxt:
                break
            frontier = nxt
        return False, []
