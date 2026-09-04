#!/usr/bin/env python3
"""Composition operators: the capability interface, and nothing else.

The whole vocabulary is a step, an operator name read from the schema, a
termination, a parked gate and a typed problem. There is no engine handle, no
task queue, no call stack and no state row here on purpose: an engine that
lowers the document into a state machine before the run could never implement a
contract written in tree positions, and an engine that walks the tree could
never implement one written in transitions - so a contract naming either is a
contract shaped around whichever engine runs today (F-b1-04).

The operator set is NOT written in this file. `operator_names()` reads it from
the schema handed to the engine, and every engine derives its dispatch from the
same call, so the set is written once and a set written twice cannot drift
silently (compose-operators-implement, invariant 1).

No product name appears in this file. They appear in adapters/live.py and in the
env-var table of README.md, and nowhere else.

Read it in this order: `operator_names` is where the closed set comes from;
Envelope and Problem are the caller's two shapes; RunOutcome is what an engine
returns; CompositionEngine is the four operations an engine implements and the
five document operations every engine shares.

Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
_errors_path = _errors_os.path.join(
    _errors_os.path.dirname(_errors_os.path.abspath(__file__)), "..", "errors")
if _errors_path not in _errors_sys.path:
    _errors_sys.path.append(_errors_path)  # appended, never inserted at 0: this
    # harness's own adapters/ package must resolve before errors/adapters/ does
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal

INTERFACE_VERSION = "urn:agentic:compose:operators:0.1"

# The four concerns the document declares as constants so a reader can see them
# and a caller cannot set them (F-b4-01). Their values are read from the
# document's `carries` block, never from a caller argument.
CARRIES = ("correlation", "budget", "actor", "idempotency")


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode()).hexdigest()


def step_idempotency_key(run_key: str, step_id: str) -> str:
    """Per step, not per run: a restart mid-composition needs the step to be the
    unit of deduplication (compose-operators-implement, step 5)."""
    return "sha256:" + hashlib.sha256(f"{run_key}|{step_id}".encode()).hexdigest()[:32]


# --------------------------------------------------------------------------
# The closed set, read from the schema and nowhere else
# --------------------------------------------------------------------------
def operator_names(schema: dict) -> tuple[str, ...]:
    """The operator names the schema admits, in the order it lists them.

    Read at load from the `anyOf` over step and each arm's `op` const. Nothing
    in this harness retypes them: an engine's dispatch table is built by asking
    for a handler per name returned here, so a name the schema does not admit
    has nowhere to be reached from."""
    step = schema["$defs"]["step"]
    names: list[str] = []
    for branch in step["anyOf"]:
        arm = schema["$defs"][branch["$ref"].rsplit("/", 1)[-1]]
        names.append(arm["properties"]["op"]["const"])
    return tuple(names)


CHILD_SLOTS = ("steps", "branches", "body")   # the slots an operator carries a step in


def child_steps(node: dict) -> list[tuple[str, dict]]:
    """(slot, child) for every step this step carries, in declared order."""
    out: list[tuple[str, dict]] = []
    for slot in CHILD_SLOTS:
        value = node.get(slot)
        if isinstance(value, list):
            out += [(slot, child) for child in value]
        elif isinstance(value, dict):
            out.append((slot, value))
    return out


# --------------------------------------------------------------------------
# The entry envelope (cap-consumption). One shape for all four entries of
# TARGET T6.2; kind says which door produced it and nothing below branches on it.
# --------------------------------------------------------------------------
@dataclass
class Envelope:
    kind: Literal["human", "event", "schedule", "external"]
    entry_id: str
    occurred_at: str
    actor: dict                 # {subject, delegation_chain}
    intent: dict                # {workflow_ref, summary} - never the criterion
    correlation: dict           # {run_id, correlation_id, depth}
    budget: dict                # {ceiling_micros, currency, on_exceed}
    idempotency_key: str
    payload: dict
    envelope_version: str = "0.1"

    def dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Typed failures (cap-errors / RFC 9457). One closed registry; a failure whose
# type is not a row here is an untyped failure and the conformance run counts it.
# --------------------------------------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":       (422, "The workflow document fails validation", False),
    "criterion-unresolvable": (422, "criterion_ref does not resolve", False),
    "budget-exhausted":       (402, "A step would cross the budget ceiling", False),
    "deadline-exceeded":      (504, "A declared ceiling was reached", True),
    "adapter-unavailable":    (503, "A capability adapter is unreachable", True),
    "idempotency-conflict":   (409, "Same key, different request body", False),
}


class Problem(Exception):
    """A failure a caller branches on without parsing prose (F-b4-07)."""

    def __init__(self, suffix: str, detail: str, **ext: Any):
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


def is_typed(body: dict | None) -> bool:
    if not body:
        return False
    t = str(body.get("type", ""))
    return t.startswith(PROBLEM_BASE) and t[len(PROBLEM_BASE):] in REGISTRY


# --------------------------------------------------------------------------
# What an engine returns
# --------------------------------------------------------------------------
TERMINATION_REASONS = ("verdict_pass", "iteration_ceiling", "budget_ceiling",
                       "tolerate_exceeded", "approval_rejected")


@dataclass
class Termination:
    """compose-operators' termination shape. `reason` reuses compose-loop's
    LoopOutcome.terminated_by vocabulary verbatim for the three loop reasons, so
    a nested loop and a bare loop declaration report the same string for the
    same event. There is no fourth loop reason to write, which is what makes a
    defect show up instead of passing."""
    step_id: str
    reason: Literal["verdict_pass", "iteration_ceiling", "budget_ceiling",
                    "tolerate_exceeded", "approval_rejected"]
    outcome: Literal["success", "failure", "escalated"]
    iterations_run: int = 0
    units_failed: int = 0
    unbounded: bool = False


@dataclass
class ParkedGate:
    """The resume seam a decision arrives on (compose-approval). The caller gets
    a gate id and nothing about where the engine kept the run."""
    gate_id: str
    step_id: str
    asks: str
    decisions: tuple[str, ...]
    correlation_id: str
    return_to_step_id: str | None = None


@dataclass
class RunOutcome:
    engine_marker: str                     # read from the running engine
    outcome: Literal["completed", "parked", "refused", "stopped-on-reject"]
    ledger: list[dict] = field(default_factory=list)     # the rows this run appended
    terminations: list[Termination] = field(default_factory=list)
    parked: ParkedGate | None = None
    verdicts: dict[str, str] = field(default_factory=dict)
    agents: dict[str, str] = field(default_factory=dict)  # step id -> profile selected
    spent_micros: int = 0
    operators_exercised: tuple[str, ...] = ()
    gates_parked: int = 0
    gates_decided: int = 0
    duplicate_deliveries_ignored: int = 0
    reentered_step: str | None = None
    problem: dict | None = None
    locus: dict | None = None              # where the engine says the failure was

    def step_order(self) -> list[tuple[str, str, str]]:
        """The ledger of steps, as the swap proof compares it: kind, step, op."""
        return [(r["kind"], r.get("step_id", "-"), r.get("op", "-")) for r in self.ledger]


@dataclass
class Graph:
    nodes: list[dict]
    edges: list[dict]

    def key(self) -> str:
        return digest({"nodes": sorted(self.nodes, key=canonical),
                       "edges": sorted(self.edges, key=canonical)})


@dataclass
class Priced:
    step_id: str
    op: str
    estimate_micros: int
    children: list["Priced"] = field(default_factory=list)

    def reconciles(self) -> bool:
        """A parent's total is the sum of its children's declared contributions
        rather than a figure of its own (compose-operators, price)."""
        if not self.children:
            return True
        return (self.estimate_micros == sum(c.estimate_micros for c in self.children)
                and all(c.reconciles() for c in self.children))

    def flat(self) -> list["Priced"]:
        return [self] + [n for c in self.children for n in c.flat()]


@dataclass
class ResolvedDefault:
    step_id: str
    field: str
    value: Any
    resolved_from: Literal["caller", "capability", "platform"]


# --------------------------------------------------------------------------
# The adapter
# --------------------------------------------------------------------------
class CompositionEngine(ABC):
    """One engine over one closed operator set.

    Four class attributes are the engine's declared execution model. The
    conformance run asserts the engine behaved as declared rather than widening
    the contract until both members satisfy it, and build-adapter-pair rejects a
    pair whose axes agree (F-b1-04).
    """

    engine_marker: str = "unset"                  # read back from the running engine
    tree_read_at: Literal["during-walk", "before-run"] = "during-walk"
    progress_unit: Literal["call-stack-frame", "committed-transition-row"] = "call-stack-frame"
    durable_at: Literal["gate-boundary", "every-step"] = "gate-boundary"
    failure_locus: Literal["tree-position", "state-and-transition"] = "tree-position"

    def __init__(self, schema: dict, out_dir: str, validator: Callable[[Any, dict], list[str]]):
        self.schema = schema
        self.out_dir = out_dir
        self._validate = validator            # cap-document-validation, imported

    # -- what the binding record says, and what the running engine says -----
    def binding(self) -> dict:
        return {"adapter": type(self).__name__, "engine_marker": self.engine_marker,
                "tree_read_at": self.tree_read_at, "progress_unit": self.progress_unit,
                "durable_at": self.durable_at, "failure_locus": self.failure_locus,
                "interface_version": INTERFACE_VERSION}

    def schema_ops(self) -> tuple[str, ...]:
        return operator_names(self.schema)

    @abstractmethod
    def executor_ops(self) -> tuple[str, ...]:
        """The operator names this engine can actually dispatch, read from the
        running engine's own dispatch table. Compared against schema_ops(): the
        symmetric difference is `drift`, and a conformant build has it empty."""

    @abstractmethod
    def start(self, envelope: dict, workflow: dict, agents: dict) -> RunOutcome:
        """Run the composition from the entry envelope. Parks rather than
        deciding when it reaches an approval operator."""

    @abstractmethod
    def resume(self, gate_id: str, decision: str, delivery_key: str,
               note: str = "") -> RunOutcome:
        """Deliver one decision to one parked gate. N deliveries of the same
        decision under the same key resume the run once."""

    # -- the document operations, identical for every engine ----------------
    def validate_workflow(self, doc: Any) -> list[str]:
        """Imported from cap-document-validation, not implemented here: an
        operator outside the closed set is refused by the same validator that
        refuses a malformed envelope."""
        return self._validate(doc, self.schema)

    def compose(self, root: dict, name: str, description: str = "") -> dict:
        """An ordered tree of steps -> one workflow document, or a typed problem
        naming the step whose operator is not in the set. The refusal happens
        before pricing and before dispatch."""
        allowed = set(self.schema_ops())
        for node, _depth in self._walk(root):
            if node.get("op") not in allowed:
                raise Problem("document-invalid",
                              f"step {node.get('id', '?')!r} names operator "
                              f"{node.get('op')!r}, which is not in the closed set "
                              f"{sorted(allowed)}", step_id=node.get("id"))
        doc = {"workflow_version": self.schema["properties"]["workflow_version"]["const"],
               "name": name,
               "carries": {c: self.schema["properties"]["carries"]["properties"][c]["const"]
                           for c in CARRIES},
               "root": root}
        if description:
            doc["description"] = description
        return doc

    def to_graph(self, doc: dict, depth_bound: int = 8) -> Graph:
        """One node per step and one existence edge per parent-to-child slot, or
        a refusal naming the step that would nest past the bound. The bound is
        checked here, at resolve, not while the run is walking."""
        nodes, edges = [], []
        for node, depth in self._walk(doc["root"]):
            if depth > depth_bound:
                raise Problem("document-invalid",
                              f"step {node['id']!r} nests at depth {depth}, past the "
                              f"declared bound {depth_bound}", step_id=node["id"],
                              depth_bound_checked_at="resolve")
            nodes.append({"id": node["id"], "kind": "step", "op": node["op"], "depth": depth})
            for slot, child in child_steps(node):
                edges.append({"kind": "existence", "from": node["id"],
                              "to": child["id"], "slot": slot})
        return Graph(nodes, edges)

    def price(self, doc: dict, agents: dict, cost_table: dict,
              loop_iterations: str = "max") -> Priced:
        """core-planner's call site: a parent's total is the sum of its
        children's declared contributions, never a figure of its own."""
        def node_price(node: dict) -> Priced:
            kids = [node_price(child) for _slot, child in child_steps(node)]
            if node["op"] == "agent":
                return Priced(node["id"], "agent",
                              cost_table[agents[node["agent"]]["cost_class"]])
            if node["op"] == "loop":
                n = node["max_iterations"] if loop_iterations == "max" else 1
                body = kids[0]
                return Priced(node["id"], "loop", body.estimate_micros * n,
                              [body] * n)
            return Priced(node["id"], node["op"],
                          sum(k.estimate_micros for k in kids), kids)
        return node_price(doc["root"])

    def step_of(self, doc: dict, step_id: str) -> dict:
        """That step's operator, its child slots and its declared fields, with no
        payload body: a reader walks the control flow without reading what the
        work is about."""
        for node, depth in self._walk(doc["root"]):
            if node["id"] == step_id:
                return {"id": step_id, "op": node["op"], "depth": depth,
                        "slots": {slot: [c["id"] for _s, c in child_steps(node) if _s == slot]
                                  for slot in CHILD_SLOTS if slot in node},
                        "fields": {k: v for k, v in node.items()
                                   if k not in CHILD_SLOTS and k not in ("op", "id")}}
        raise Problem("document-invalid", f"no step {step_id!r} in this document")

    def resolved_default(self, doc: dict, step_id: str, field_name: str) -> ResolvedDefault:
        """The value in force and which single layer it came from, so a caller
        can always ask where a value came from and get one answer."""
        step = self.step_of(doc, step_id)
        if field_name in step["fields"]:
            return ResolvedDefault(step_id, field_name, step["fields"][field_name], "caller")
        if field_name in CARRIES:
            return ResolvedDefault(step_id, field_name, doc["carries"][field_name], "platform")
        arm = self.schema["$defs"].get(step["op"], {}).get("properties", {}).get(field_name, {})
        if "default" in arm or "const" in arm:
            return ResolvedDefault(step_id, field_name, arm.get("default", arm.get("const")),
                                   "capability")
        raise Problem("document-invalid",
                      f"step {step_id!r} has no field {field_name!r} at any layer")

    # -- shared walk over the document, used by the operations above --------
    @staticmethod
    def _walk(node: dict, depth: int = 0):
        yield node, depth
        for _slot, child in child_steps(node):
            yield from CompositionEngine._walk(child, depth + 1)


ADAPTERS = ("dryrun", "second", "live")


def load_engine(name: str, schema: dict, out_dir: str,
                validator: Callable[[Any, dict], list[str]], **kw) -> CompositionEngine:
    """Binding is configuration: one name, one import, one class. Every adapter
    module exports its entry point as `Adapter`, so there is no per-adapter
    class-name table here or anywhere else. `binding()` still reports the class
    that answered, and `engine_marker` is read from the engine that ran."""
    import importlib
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (here, os.path.join(here, "adapters")):
        if path not in sys.path:
            sys.path.insert(0, path)
    if name not in ADAPTERS:
        raise Problem("document-invalid",
                      f"unknown adapter {name!r}: choose {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter(schema, out_dir, validator, **kw)
