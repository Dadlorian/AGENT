#!/usr/bin/env python3
"""The two core components this seam is used by: the Planner and the Judge.

Both are pure functions and neither has an adapter of its own (F-b2-03,
F-b2-05). What is adapted beneath the Planner is the store its cost inputs are
read from, which is why `load_cost_inputs` has two read modes and the plan
digest is asserted equal across them; what is adapted beneath the Judge is the
engine that decides a check, which is why `judge` takes the resolved criterion
set as a value and never a handle to a service.

    plan(document, head, cost_inputs) -> Plan      pure: no clock, no network
    judge(result_text, criterion) -> Verdict       pure: total, deterministic

The criterion body is resolved out of band by `resolve_criterion` and reaches
the Judge only. Nothing here ever writes it into a dispatch request, a step
payload or a verdict detail (F-b1-07); `criterion_hits` in the conformance run
is the count that says so.

The step tree, the agent registry and the criterion body are imported from
examples/end-to-end/run.py rather than restated, so this harness and the worked
example price and grade the same document the same way.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field

from interface import Problem, canonical, digest

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.abspath(os.path.join(HERE, "..", "..", "examples", "end-to-end"))
sys.path.insert(0, EXAMPLE)
import run as example  # noqa: E402  the worked example: validator, registry, criteria, unit

validate = example.validate            # JSON Schema 2020-12 subset, reused
CRITERIA = example.CRITERIA            # the criterion bodies, keyed by opaque handle


COST_OBSERVATIONS = os.path.join(HERE, "fixtures", "cost-observations.jsonl")


def cost_source() -> str:
    """Where the measured cost observations are read from. Configuration, so a
    run can point at a working copy without editing a fixture."""
    return os.environ.get("DISPATCH_OBSERVATIONS") or COST_OBSERVATIONS


def cost_inputs_at(head: str, source: str | None = None,
                   read_mode: str = "scan-and-fold") -> dict:
    """The cost table and quantiles at one pinned head, as a value."""
    return load_cost_inputs(source or cost_source(), head, read_mode)


def load_example(rel: str):
    with open(os.path.join(EXAMPLE, rel)) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Cost inputs: records at a pinned head, folded to quantiles. Data the planner
# reads, never a service it calls (F-b5-05).
# --------------------------------------------------------------------------
def observations(path: str) -> list[dict]:
    return [json.loads(line) for line in open(path) if line.strip()]


def head_of(records: list[dict]) -> str:
    return records[-1]["hash"] if records else "sha256:" + "0" * 64


def prefix_at(records: list[dict], head: str) -> list[dict]:
    """The records up to and including the one this head names. A head that
    names no record is a refusal, not a silent read of everything."""
    for i, rec in enumerate(records):
        if rec["hash"] == head:
            return records[:i + 1]
    raise Problem("document-invalid", f"head {head[:19]}... names no record in the cost log")


def quantile(values: list[int], q: float) -> int:
    """Nearest-rank on the sorted sample: integer arithmetic, no interpolation,
    so two processes reading the same records get the same number."""
    ordered = sorted(values)
    rank = max(1, -(-int(q * 100) * len(ordered) // 100))
    return ordered[rank - 1]


def fold(records: list[dict]) -> dict:
    """Fold cost observations into one row per selector: a floor, a worst case,
    and how many observations produced them."""
    by_selector: dict[str, list[int]] = {}
    for rec in records:
        if rec.get("kind") == "cost-observation":
            by_selector.setdefault(rec["selector"], []).append(int(rec["micros"]))
    return {sel: {"floor_micros": quantile(v, 0.50), "worst_micros": quantile(v, 0.95),
                  "observations": len(v), "quantiles": ["p50", "p95"]}
            for sel, v in sorted(by_selector.items())}


def load_cost_inputs(source: str, head: str, read_mode: str) -> dict:
    """The two read modes core-planner-implement's bindings differ on. Neither
    computes a price: a store that did would have taken the Planner's job into
    the persistence boundary. Both must yield the same table at the same head.
    """
    if read_mode == "scan-and-fold":
        return {"head": head, "read_mode": read_mode,
                "platform_ops": PLATFORM_OPS,
                "rows": fold(prefix_at(observations(source), head))}
    if read_mode == "snapshot-by-digest":
        snap = json.load(open(os.path.join(source, head.replace(":", "-") + ".json")))
        if snap["head"] != head:
            raise Problem("document-invalid", "snapshot does not name the head it was fetched by")
        return {"head": head, "read_mode": read_mode,
                "platform_ops": PLATFORM_OPS, "rows": snap["rows"]}
    raise Problem("document-invalid", f"unknown read mode {read_mode!r}")


def materialise(source: str, head: str, out_dir: str) -> str:
    """Build the immutable snapshot the second binding fetches by digest. The
    snapshot is the same fold over the same records, addressed by the head."""
    rows = fold(prefix_at(observations(source), head))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, head.replace(":", "-") + ".json")
    with open(path, "w") as fh:
        json.dump({"head": head, "rows": rows}, fh, sort_keys=True, indent=1)
    return path


# Steps that are platform work rather than a metered call. Declared, so a step
# with no cost row is a refusal rather than a step quietly priced at zero.
PLATFORM_OPS = ["judge", "approval", "sequence", "parallel", "loop"]


# --------------------------------------------------------------------------
# The Planner: document -> plan + cost. Pure, and complete before execution
# begins (F-b1-06, F-b2-03).
# --------------------------------------------------------------------------
@dataclass
class PlanStep:
    step_id: str
    op: str
    agent: str
    model_class: str
    selector: str
    floor_micros: int
    worst_micros: int
    derivation: str


@dataclass
class Plan:
    document_id: str
    head: str
    read_mode: str
    steps: list[PlanStep]
    floor_micros: int
    worst_micros: int
    steps_priced: int
    plan_digest: str = ""

    def dict(self) -> dict:
        d = asdict(self)
        return d


def walk_steps(workflow: dict, agents: dict, loop_iterations: str = "max") -> list[dict]:
    """The step tree of the worked example, in the worked example's own shape.
    `max` prices the worst case; `1` prices the shortest path that can finish."""
    steps: list[dict] = []

    def walk(node, iteration=None):
        op, sid = node["op"], node["id"] + (f"#{iteration}" if iteration else "")
        if op == "sequence":
            for child in node["steps"]:
                walk(child, iteration)
        elif op == "parallel":
            for branch in node["branches"]:
                walk(branch, iteration)
        elif op == "loop":
            for i in range(1, (node["max_iterations"] if loop_iterations == "max" else 1) + 1):
                walk(node["body"], i)
        elif op == "agent":
            profile = agents[node["agent"]]
            steps.append({"id": sid, "op": op, "agent": node["agent"],
                          "model_class": profile["model_class"], "node": node,
                          "iteration": iteration or 1})
        else:
            steps.append({"id": sid, "op": op, "agent": "-", "model_class": "-",
                          "node": node, "iteration": iteration or 1})

    walk(workflow["root"])
    return steps


def price_step(step: dict, cost_inputs: dict) -> tuple[int, int, str, str]:
    """One step, the row its operator and model class select, and the derivation
    that produced the two numbers. A missing row is a refusal naming the step,
    never a default (F-b1-06)."""
    selector = f"{step['op']}:{step['model_class']}"
    if step["op"] in cost_inputs["platform_ops"]:
        return 0, 0, selector, "platform work, declared not metered"
    row = cost_inputs["rows"].get(selector)
    if row is None:
        raise Problem("document-invalid",
                      f"step {step['id']} selects cost row {selector!r}, which the cost "
                      f"inputs at this head do not carry; refused rather than estimated",
                      step_id=step["id"], selector=selector,
                      proposed_type="urn:agentic:problem:step-unpriceable")
    return (row["floor_micros"], row["worst_micros"], selector,
            f"row {selector} p50/p95 over {row['observations']} observations")


def plan(document: dict, head: str, cost_inputs: dict) -> Plan:
    """document -> plan + cost. No clock, no network, no store handle: every
    input is passed as a value, so two runs at the same head are byte-identical.
    """
    if cost_inputs["head"] != head:
        raise Problem("document-invalid",
                      "cost inputs were read at a different head than the plan was asked for")
    workflow = load_example(document["workflow_ref"])
    agents = {a["name"]: a for a in load_example("agents.json")["agents"]}
    worst_steps = walk_steps(workflow, agents, "max")
    floor_steps = walk_steps(workflow, agents, "1")
    priced: list[PlanStep] = []
    for step in worst_steps:
        floor, worst, selector, why = price_step(step, cost_inputs)
        priced.append(PlanStep(step["id"], step["op"], step["agent"], step["model_class"],
                               selector, floor, worst, why))
    floor_total = 0
    for step in floor_steps:
        floor_total += price_step(step, cost_inputs)[0]
    out = Plan(document_id=document["document_id"], head=head,
               read_mode=cost_inputs["read_mode"], steps=priced,
               floor_micros=floor_total,
               worst_micros=sum(s.worst_micros for s in priced),
               steps_priced=sum(1 for s in priced if s.worst_micros > 0))
    # The digest covers the plan a caller acts on. read_mode is which store
    # served the inputs, not part of the plan, so it is excluded by design: two
    # bindings that read the same records must agree byte for byte.
    body = out.dict()
    body.pop("read_mode")
    body.pop("plan_digest")
    out.plan_digest = digest(body)
    return out


def explain(p: Plan) -> list[tuple]:
    """The per-step derivation in reading order, so a reviewer sees why a step
    was priced as it was without re-running the planner."""
    return [(s.step_id, s.selector, s.floor_micros, s.worst_micros, s.derivation)
            for s in p.steps]


# --------------------------------------------------------------------------
# The Judge: (result, criterion) -> verdict. Pure and total (F-b2-05).
# --------------------------------------------------------------------------
@dataclass
class Verdict:
    verdict: str                  # pass | fail
    checks_applied: int
    failed_check_ids: list[str] = field(default_factory=list)
    detail: str = ""              # written from check ids, never from criterion text


def resolve_criterion(criterion_ref: str) -> dict:
    """The out-of-band path the Judge alone may take. The handle travels on the
    request; the body resolved here never goes back the other way."""
    body = CRITERIA.get(criterion_ref)
    if body is None:
        raise Problem("criterion-unresolvable",
                      f"criterion_ref {criterion_ref!r} names nothing")
    return {"criterion_ref": criterion_ref,
            "checks": [{"id": f"c{i + 1}", "kind": "contains", "token": token}
                       for i, token in enumerate(body["must_contain"])]}


def criterion_tokens() -> list[str]:
    """The criterion strings the leak scan looks for. Read from the same store
    the Judge resolves from, so the scan cannot go stale against it."""
    return [t for body in CRITERIA.values() for t in body["must_contain"]]


def judge(result_text: str, criterion: dict, mode: str = "closing") -> Verdict:
    """Deterministic for one (result, criterion): the same inputs give the same
    verdict on every run and under every engine."""
    checks = criterion["checks"]
    if mode == "in_loop":                      # a proper subset, deterministic per grading
        seed = int(hashlib.sha256((result_text + criterion["criterion_ref"]).encode())
                   .hexdigest()[:8], 16)
        checks = [c for i, c in enumerate(checks) if (seed >> i) & 1] or checks[:1]
    failed = [c["id"] for c in checks if c["token"] not in result_text]
    return Verdict("fail" if failed else "pass", len(checks), failed,
                   f"{len(checks) - len(failed)}/{len(checks)} checks satisfied"
                   + (f"; failed {failed}" if failed else ""))


def criterion_hits(paths: list[str]) -> int:
    """Occurrences of any criterion string in anything the graded unit can read:
    the recorded requests, the step payloads and the verdict details."""
    tokens = criterion_tokens()
    hits = 0
    for path in paths:
        if not os.path.exists(path):
            continue
        text = open(path).read()
        hits += sum(text.count(token) for token in tokens)
    return hits


__all__ = ["plan", "Plan", "PlanStep", "explain", "judge", "Verdict", "resolve_criterion",
           "criterion_hits", "criterion_tokens", "load_cost_inputs", "cost_inputs_at",
           "cost_source", "COST_OBSERVATIONS", "materialise",
           "observations", "head_of", "canonical", "validate", "load_example"]
