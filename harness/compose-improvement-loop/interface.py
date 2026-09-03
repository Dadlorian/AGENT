#!/usr/bin/env python3
"""Improvement-loop capability interface - the whole contract, with no driver in sight.

Read in this order:
  Metric, Scorecard      what is being improved: a value, a target, a direction and
                         the span the distance is normalised by. `furthest` is the
                         only selection rule, so an iteration cannot pick a metric
                         because it is the easiest one
  CandidateChange        one change offered for one metric: the gate it will be put
                         through and the value it claims if the gate passes. It
                         carries no criterion and no rubric
  GateSpec, Gate         the gate is harness/evaluation's own interface, imported
                         and used unchanged: outcome is passed | failed |
                         inconclusive, and inconclusive is treated exactly like
                         failed
  LoopSpec               a declaration with a required iteration ceiling; one
                         without a ceiling is refused before anything runs
  IterationRecord        what one iteration wrote: metric, candidate, gate outcome,
                         decision, and the checkpoint in force after it
  Checkpoint             the scorecard values a fire may resume from
  LoopOutcome            compose-loop's own shape: terminated_by is exactly three
                         values, termination_class is stop or cap
  ImprovementLoopDriver  the five operations the core imports: register_scorecard,
                         open_loop, run_iteration, evaluate_exit, read_checkpoint
  Problem                RFC 9457 problem details, minted only from a closed registry

Governing standard: none adopted. The loop shape - one iteration moves the metric
furthest from its target, gated by an evaluation that can say no, checkpointed each
fire - is this repository's design (TARGET T9.1 and the compose-improvement-loop
skill); JSON Schema 2020-12 governs the declaration check, and RFC 9457 the failure
body. No product name appears in this file, in call.py or in conformance.py; they
appear only inside adapters/ and in README's env-var table. Python 3.11 stdlib only.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Any, Callable

HERE = os.path.dirname(os.path.abspath(__file__))
GATE_HARNESS = os.path.join(os.path.dirname(HERE), "evaluation")


# --- the gate: imported, never re-invented -----------------------------------
def _load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def gate_interface():
    """harness/evaluation/interface.py, loaded under its own module name so this
    harness reuses that capability's shapes rather than declaring a second set of
    them. Nothing here re-implements a case set, a rubric, a verdict or a baseline."""
    if "gate_evaluation_interface" not in sys.modules:
        _load_module("gate_evaluation_interface", os.path.join(GATE_HARNESS, "interface.py"))
    return sys.modules["gate_evaluation_interface"]


EV = gate_interface()
Problem = EV.Problem                      # RFC 9457 problem details, one shape for both
EvaluationReport = EV.EvaluationReport
EvaluationAdapter = EV.EvaluationAdapter
UnitRef = EV.UnitRef
PASSED, FAILED, INCONCLUSIVE = EV.PASSED, EV.FAILED, EV.INCONCLUSIVE
OUTCOMES = EV.OUTCOMES
canonical = EV.canonical
validate = EV.validate

GATE_ADAPTERS = ("dryrun", "second")


def load_gate_adapter(name: str = "dryrun") -> "EvaluationAdapter":
    """The evaluation harness's own adapter, loaded by path under its own module
    names. Its modules say `from interface import ...`; that name is this harness's
    module here, so it is swapped for the duration of the load and put back."""
    if name not in GATE_ADAPTERS:
        raise SystemExit(f"unknown gate {name!r}; choose one of {', '.join(GATE_ADAPTERS)}")
    key = f"gate_evaluation_adapter_{name}"
    if key not in sys.modules:
        saved_module, saved_path = sys.modules.get("interface"), list(sys.path)
        sys.modules["interface"] = gate_interface()
        try:
            _load_module(key, os.path.join(GATE_HARNESS, "adapters", f"{name}.py"))
        finally:
            if saved_module is None:
                sys.modules.pop("interface", None)
            else:
                sys.modules["interface"] = saved_module
            # The gate's own module puts its harness first on the path; put the path
            # back, with that harness last, so this harness's adapters/ still wins and
            # the unit the gate replays is still importable when it runs.
            sys.path[:] = saved_path
            if GATE_HARNESS not in sys.path:
                sys.path.append(GATE_HARNESS)
    return sys.modules[key].Adapter()


# --- shapes ------------------------------------------------------------------
DIRECTIONS = ("down", "up")
TOLERANCE = 1e-9
DECISIONS = ("promoted", "declined")
TERMINATED_BY = ("verdict_pass", "iteration_ceiling", "budget_ceiling")
TERMINATION_CLASS = {"verdict_pass": "stop", "iteration_ceiling": "cap",
                     "budget_ceiling": "cap"}


@dataclass(frozen=True)
class Metric:
    """One row of the scorecard. scale is the span the gap is divided by, so metrics
    in different units are comparable and `furthest` means something."""
    metric_id: str
    direction: str                          # "down" | "up"
    current: float
    target: float
    scale: float = 1.0

    @property
    def distance(self) -> float:
        gap = (self.current - self.target) if self.direction == "down" else (self.target - self.current)
        return round(max(0.0, gap / self.scale), 6)

    @property
    def holds(self) -> bool:
        return self.distance <= TOLERANCE


@dataclass(frozen=True)
class Scorecard:
    scorecard_id: str
    metrics: tuple[Metric, ...]

    def values(self) -> dict[str, float]:
        return {m.metric_id: m.current for m in self.metrics}

    def with_values(self, values: dict[str, float]) -> "Scorecard":
        return Scorecard(self.scorecard_id, tuple(
            Metric(m.metric_id, m.direction, values.get(m.metric_id, m.current), m.target, m.scale)
            for m in self.metrics))

    def furthest(self) -> Metric | None:
        """One rule: the largest normalised distance, ties broken by metric id so two
        drivers cannot disagree. None when every target holds."""
        open_rows = [m for m in self.metrics if not m.holds]
        if not open_rows:
            return None
        return sorted(open_rows, key=lambda m: (-m.distance, m.metric_id))[0]

    def holds(self) -> bool:
        return all(m.holds for m in self.metrics)

    @property
    def digest(self) -> str:
        body = canonical([[m.metric_id, m.direction, round(m.current, 6), round(m.target, 6),
                           m.scale] for m in self.metrics])
        return "sha256:" + hashlib.sha256(body.encode()).hexdigest()[:32]


@dataclass(frozen=True)
class ScorecardHandle:
    scorecard_id: str
    digest: str
    metric_count: int
    candidate_count: int


@dataclass(frozen=True)
class GateSpec:
    """What the candidate is put through. It names a unit and a registered case set;
    it has nowhere to carry the criterion, which is the evaluation capability's and
    is resolved inside the scorer."""
    unit_ref: str
    unit_version: str
    case_set_id: str
    baseline_id: str
    case_filter: str | None = None


@dataclass(frozen=True)
class CandidateChange:
    """One authored change. value_if_promoted is what the metric reads if - and only
    if - the gate passes; nothing here can move a metric on its own."""
    candidate_id: str
    metric_id: str
    gate: GateSpec
    value_if_promoted: float
    rationale: str


@dataclass(frozen=True)
class LoopSpec:
    loop_id: str
    iteration_ceiling: int | None
    budget_ceiling_micros: int
    per_iteration_micros: int
    on_cap: str = "escalate"

    def as_dict(self) -> dict[str, Any]:
        row = {"loop_id": self.loop_id, "budget_ceiling_micros": self.budget_ceiling_micros,
               "per_iteration_micros": self.per_iteration_micros, "on_cap": self.on_cap}
        if self.iteration_ceiling is not None:
            row["iteration_ceiling"] = self.iteration_ceiling
        return row


LOOP_SPEC_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:agentic:compose:improvement-loop:spec:0.1",
    "title": "ImprovementLoopSpec",
    "type": "object",
    "additionalProperties": False,
    "description": "iteration_ceiling is required: there is no unbounded variant to declare.",
    "required": ["loop_id", "iteration_ceiling", "budget_ceiling_micros",
                 "per_iteration_micros", "on_cap"],
    "properties": {
        "loop_id": {"type": "string", "minLength": 3},
        "iteration_ceiling": {"type": "integer", "minimum": 1},
        "budget_ceiling_micros": {"type": "integer", "minimum": 1},
        "per_iteration_micros": {"type": "integer", "minimum": 0},
        "on_cap": {"const": "escalate"},
    },
}


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    loop_id: str
    iteration_index: int
    values: dict[str, float]
    written_by: str                         # "open_loop" | "iteration"

    def as_dict(self) -> dict[str, Any]:
        return {"checkpoint_id": self.checkpoint_id, "loop_id": self.loop_id,
                "iteration_index": self.iteration_index,
                "values": {k: round(v, 6) for k, v in sorted(self.values.items())},
                "written_by": self.written_by}


@dataclass(frozen=True)
class IterationRecord:
    """One iteration, as both drivers write it. Derived from what happened, never
    from who ran it: two drivers that agree produce byte-identical records."""
    record_id: str
    loop_id: str
    iteration_index: int
    metric_id: str
    distance_before: float
    distance_after: float
    candidate_id: str
    gate_outcome: str
    report_id: str
    cases_executed: int
    decision: str
    reason: str | None
    checkpoint_id: str
    checkpoint_advanced: bool
    spend_micros: int
    idempotency_key: str
    correlation_id: str

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


@dataclass(frozen=True)
class LoopOutcome:
    """compose-loop's own shape. terminated_by has exactly three members; a fourth
    reason has nowhere to be written."""
    loop_id: str
    terminated_by: str
    termination_class: str
    iterations_run: int
    cost_micros: int
    final_checkpoint_id: str
    targets_held: int
    targets_total: int
    escalation: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# --- the closed problem registry ---------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
# registered=True rows are in the closed registry of docs/decomposition.md 2.1.6.
# iteration-ceiling-reached is not: compose-loop marks it proposed and pending
# registration, and its default returns the registered deadline-exceeded meanwhile.
REGISTRY: dict[str, dict[str, Any]] = {
    "adapter-unavailable": {"status": 503, "retryable": True, "registered": True,
                            "title": "The loop driver could not be reached"},
    "document-invalid": {"status": 422, "retryable": False, "registered": True,
                         "title": "The loop declaration is not valid"},
    "criterion-unresolvable": {"status": 422, "retryable": False, "registered": True,
                               "title": "The candidate's case set or baseline does not resolve"},
    "budget-exhausted": {"status": 402, "retryable": False, "registered": True,
                         "title": "The loop's budget ceiling would be crossed"},
    "deadline-exceeded": {"status": 504, "retryable": True, "registered": True,
                          "title": "The loop ran its ceiling without every target holding"},
    "iteration-ceiling-reached": {"status": 504, "retryable": False, "registered": False,
                                  "title": "Iteration ceiling reached without every target holding"},
}
FALLBACK_PROBLEM = "deadline-exceeded"


def problem(kind: str, detail: str, correlation_id: str | None = None) -> Problem:
    """An unregistered suffix is never minted: the registered fallback is returned
    and the proposed suffix is carried in detail, so no caller branches on a URI no
    conformant implementation may emit."""
    row = REGISTRY[kind]
    if not row["registered"]:
        detail = f"{detail} [proposed type {PROBLEM_BASE}{kind}, pending registration]"
        kind, row = FALLBACK_PROBLEM, REGISTRY[FALLBACK_PROBLEM]
    return Problem(PROBLEM_BASE + kind, row["title"], row["status"], detail,
                   row["retryable"], correlation_id)


class DriverUnavailable(Exception):
    """Raised at construction when a driver's configuration is absent. Carries
    problem details; it is never raised out of an operation."""

    def __init__(self, problem_: Problem):
        super().__init__(problem_.detail)
        self.problem = problem_


# --- the gate binding --------------------------------------------------------
class Gate:
    """The evaluation capability, reached through its own interface and nothing
    else. This harness registers the corpus once and then only ever calls evaluate:
    no rubric, no scoring rule and no baseline logic is re-stated here."""

    def __init__(self, adapter: "EvaluationAdapter", corpus_file: str = "case-set.json") -> None:
        self.adapter = adapter
        self.name = getattr(adapter, "name", "unknown")
        with open(os.path.join(GATE_HARNESS, "corpus", corpus_file)) as fh:
            row = json.load(fh)
        cases = [EV.Case(c["case_id"], c["corpus_half"], c["input"], c["rubric_ref"],
                         EV.StubPolicy(**c["stub_policy"]), c.get("recorded_run_ref"))
                 for c in row["cases"]]
        self.handle = adapter.register_case_set(cases, row["version"], row["case_set_id"])

    def run(self, spec: GateSpec, correlation_id: str) -> EvaluationReport | Problem:
        report = self.adapter.evaluate(UnitRef(spec.unit_ref, spec.unit_version),
                                       spec.case_set_id, spec.baseline_id,
                                       correlation_id=correlation_id, mode="replay",
                                       case_filter=spec.case_filter)
        if isinstance(report, Problem):                 # the gate's own refusal, re-typed here
            return problem("criterion-unresolvable",
                           f"the candidate's gate did not resolve: {report.detail}", correlation_id)
        return report


# --- the decision rule -------------------------------------------------------
def promote_on_pass(outcome: str) -> bool:
    """passed promotes. failed and inconclusive do not, and inconclusive is not a
    softer failed: both leave the previous checkpoint in place."""
    return outcome == PASSED


def promote_regardless(outcome: str) -> bool:
    """THE DELIBERATE BREAKAGE, reached only under conformance.py --break-gate. The
    gate still runs, still returns failed, and the checkpoint advances anyway - a
    gate that cannot say no, reproduced on purpose so the check that catches it can
    fail."""
    return True


# --- the interface -----------------------------------------------------------
class ImprovementLoopDriver(ABC):
    """Five operations and nothing else. There is no operation that edits a target
    in place, none that scores anything itself, and none that opens a loop without a
    ceiling."""

    name: str = "unnamed"
    role: str = "dryrun"                       # "today" | "second" | "dryrun"
    execution_model: str = "bounded-in-process"    # bounded-in-process | one-iteration-per-fire | session-per-section
    checkpoint_store: str = "in-memory"            # in-memory | file | ceremony-records
    survives_process_loss: bool = False
    promotion_authority: str = "evaluation_gate"   # evaluation_gate | session_reviewer

    @abstractmethod
    def register_scorecard(self, scorecard: Scorecard,
                           candidates: list[CandidateChange]) -> ScorecardHandle | Problem:
        """Store the metrics, their targets and the candidates offered for them."""

    @abstractmethod
    def open_loop(self, spec: LoopSpec, scorecard_id: str) -> Checkpoint | Problem:
        """Refuse a declaration with no iteration ceiling; otherwise write the
        checkpoint the first fire resumes from."""

    @abstractmethod
    def run_iteration(self, loop_id: str, correlation_id: str,
                      idempotency_key: str | None = None) -> IterationRecord | Problem:
        """One iteration: pick the metric furthest from its target, take the next
        candidate for it, put it through the gate, and checkpoint only on passed."""

    @abstractmethod
    def evaluate_exit(self, loop_id: str) -> LoopOutcome | None | Problem:
        """None while the loop should continue; one outcome when it must stop."""

    @abstractmethod
    def read_checkpoint(self, loop_id: str) -> Checkpoint | Problem:
        """What a fire resumes from - the whole of what survives between iterations."""

    def next_fire(self) -> "ImprovementLoopDriver":
        """The driver that runs the next iteration. In-process drivers hand back
        themselves; a driver whose iterations are separate fires hands back a fresh
        binding that has to read its checkpoint from the store."""
        return self


class ImprovementLoopDriverBase(ImprovementLoopDriver):
    """Everything that is the capability's, implemented once: metric selection, the
    candidate order, the gate call, the promotion rule, the checkpoint rule, the
    budget arithmetic and the three-valued termination. What a driver supplies is
    where the state lives between iterations."""

    def __init__(self, gate: Gate | None = None,
                 decision_rule: Callable[[str], bool] = promote_on_pass) -> None:
        self.gate = gate if gate is not None else Gate(load_gate_adapter("dryrun"))
        self.decision_rule = decision_rule

    # --- storage hooks a driver fills in -------------------------------------
    @abstractmethod
    def store_scorecard(self, handle: ScorecardHandle, body: dict[str, Any]) -> None: ...

    @abstractmethod
    def load_scorecard(self, scorecard_id: str) -> dict[str, Any] | Problem: ...

    @abstractmethod
    def store_state(self, loop_id: str, state: dict[str, Any]) -> None: ...

    @abstractmethod
    def load_state(self, loop_id: str) -> dict[str, Any] | Problem: ...

    @abstractmethod
    def store_checkpoint(self, body: dict[str, Any]) -> None: ...

    @abstractmethod
    def load_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | Problem: ...

    # --- the five operations -------------------------------------------------
    def register_scorecard(self, scorecard: Scorecard,
                           candidates: list[CandidateChange]) -> ScorecardHandle | Problem:
        body = {
            "scorecard_id": scorecard.scorecard_id,
            "metrics": [{"metric_id": m.metric_id, "direction": m.direction,
                         "current": m.current, "target": m.target, "scale": m.scale}
                        for m in scorecard.metrics],
            "candidates": [{"candidate_id": c.candidate_id, "metric_id": c.metric_id,
                            "value_if_promoted": c.value_if_promoted, "rationale": c.rationale,
                            "gate": {"unit_ref": c.gate.unit_ref, "unit_version": c.gate.unit_version,
                                     "case_set_id": c.gate.case_set_id,
                                     "baseline_id": c.gate.baseline_id,
                                     "case_filter": c.gate.case_filter}}
                           for c in candidates],
        }
        handle = ScorecardHandle(scorecard.scorecard_id, scorecard.digest,
                                 len(scorecard.metrics), len(candidates))
        self.store_scorecard(handle, body)
        return handle

    def open_loop(self, spec: LoopSpec, scorecard_id: str) -> Checkpoint | Problem:
        errs = validate(spec.as_dict(), LOOP_SPEC_SCHEMA)
        if errs:
            return problem("document-invalid",
                           f"loop {spec.loop_id!r} was refused before any iteration ran: "
                           + "; ".join(errs))
        card = self.load_scorecard(scorecard_id)
        if isinstance(card, Problem):
            return card
        values = {m["metric_id"]: float(m["current"]) for m in card["metrics"]}
        checkpoint = self._checkpoint(spec.loop_id, 0, values, "open_loop")
        self.store_checkpoint(checkpoint.as_dict())
        self.store_state(spec.loop_id, {
            "loop_id": spec.loop_id, "scorecard_id": scorecard_id, "spec": spec.as_dict(),
            "values": values, "iteration_index": 0, "checkpoint_id": checkpoint.checkpoint_id,
            "spend_micros": 0, "attempts": {}, "records": [], "keys": {}, "closed": False,
            "outcome": None})
        return checkpoint

    def run_iteration(self, loop_id: str, correlation_id: str,
                      idempotency_key: str | None = None) -> IterationRecord | Problem:
        state = self.load_state(loop_id)
        if isinstance(state, Problem):
            return state
        card = self.load_scorecard(state["scorecard_id"])
        if isinstance(card, Problem):
            return card
        key = idempotency_key or self._key(loop_id, state["iteration_index"])
        if key in state["keys"]:                       # a re-delivered fire, not a second one
            return IterationRecord(**state["keys"][key])

        scorecard = self._scorecard(card).with_values(state["values"])
        metric = scorecard.furthest()
        if metric is None:
            return problem("document-invalid",
                           f"loop {loop_id!r} has no metric away from its target; "
                           "evaluate_exit closes it rather than running an iteration",
                           correlation_id)
        attempt = int(state["attempts"].get(metric.metric_id, 0))
        offered = [c for c in card["candidates"] if c["metric_id"] == metric.metric_id]
        if attempt >= len(offered):
            return problem("criterion-unresolvable",
                           f"metric {metric.metric_id!r} has no candidate left to author at "
                           f"attempt {attempt}", correlation_id)
        row = offered[attempt]
        spec = GateSpec(**row["gate"])
        report = self.gate.run(spec, correlation_id)
        if isinstance(report, Problem):
            return report

        promote = self.decision_rule(report.outcome)
        values = dict(state["values"])
        if promote:
            values[metric.metric_id] = float(row["value_if_promoted"])
        after = self._scorecard(card).with_values(values)
        index = state["iteration_index"] + 1
        if promote:
            checkpoint = self._checkpoint(loop_id, index, values, "iteration")
            self.store_checkpoint(checkpoint.as_dict())
            checkpoint_id = checkpoint.checkpoint_id
        else:
            checkpoint_id = state["checkpoint_id"]     # the previous checkpoint stays in place
        record = self._record(
            loop_id=loop_id, index=state["iteration_index"], metric=metric,
            distance_after=next(m.distance for m in after.metrics if m.metric_id == metric.metric_id),
            candidate_id=row["candidate_id"], report=report, promote=promote,
            checkpoint_id=checkpoint_id, spend=int(state["spec"]["per_iteration_micros"]),
            key=key, correlation_id=correlation_id)
        state.update(values=values, iteration_index=index, checkpoint_id=checkpoint_id,
                     spend_micros=state["spend_micros"] + int(state["spec"]["per_iteration_micros"]))
        state["attempts"][metric.metric_id] = attempt + 1
        state["records"].append(record.as_dict())
        state["keys"][key] = record.as_dict()
        self.store_state(loop_id, state)
        return record

    def evaluate_exit(self, loop_id: str) -> LoopOutcome | None | Problem:
        state = self.load_state(loop_id)
        if isinstance(state, Problem):
            return state
        card = self.load_scorecard(state["scorecard_id"])
        if isinstance(card, Problem):
            return card
        scorecard = self._scorecard(card).with_values(state["values"])
        spec, spend = state["spec"], int(state["spend_micros"])
        held = sum(1 for m in scorecard.metrics if m.holds)
        outcome = None
        if scorecard.holds():
            outcome = self._outcome(state, "verdict_pass", held, len(scorecard.metrics), None)
        elif state["iteration_index"] >= int(spec["iteration_ceiling"]):
            outcome = self._outcome(
                state, "iteration_ceiling", held, len(scorecard.metrics),
                problem("iteration-ceiling-reached",
                        f"loop {loop_id} ran {state['iteration_index']} of "
                        f"{spec['iteration_ceiling']} iterations; "
                        f"{len(scorecard.metrics) - held} target(s) still away from target",
                        state["records"][-1]["correlation_id"] if state["records"] else None))
        elif spend + int(spec["per_iteration_micros"]) > int(spec["budget_ceiling_micros"]):
            outcome = self._outcome(
                state, "budget_ceiling", held, len(scorecard.metrics),
                problem("budget-exhausted",
                        f"loop {loop_id} has spent {spend} of {spec['budget_ceiling_micros']} "
                        f"micros; one more iteration would cross the ceiling",
                        state["records"][-1]["correlation_id"] if state["records"] else None))
        if outcome is not None and not state["closed"]:
            state.update(closed=True, outcome=outcome.as_dict())
            self.store_state(loop_id, state)
        return outcome

    def read_checkpoint(self, loop_id: str) -> Checkpoint | Problem:
        state = self.load_state(loop_id)
        if isinstance(state, Problem):
            return state
        body = self.load_checkpoint(state["checkpoint_id"])
        if isinstance(body, Problem):
            return body
        return Checkpoint(body["checkpoint_id"], body["loop_id"], body["iteration_index"],
                          dict(body["values"]), body["written_by"])

    # --- helpers -------------------------------------------------------------
    @staticmethod
    def _scorecard(card: dict[str, Any]) -> Scorecard:
        return Scorecard(card["scorecard_id"], tuple(
            Metric(m["metric_id"], m["direction"], float(m["current"]), float(m["target"]),
                   float(m["scale"])) for m in card["metrics"]))

    @staticmethod
    def _key(loop_id: str, index: int) -> str:
        return "idem-" + hashlib.sha256(canonical([loop_id, index]).encode()).hexdigest()[:12]

    @staticmethod
    def _checkpoint(loop_id: str, index: int, values: dict[str, float], written_by: str) -> Checkpoint:
        body = canonical([loop_id, index, sorted((k, round(v, 6)) for k, v in values.items())])
        return Checkpoint("ck-" + hashlib.sha256(body.encode()).hexdigest()[:12],
                          loop_id, index, dict(values), written_by)

    def _record(self, loop_id: str, index: int, metric: Metric, distance_after: float,
                candidate_id: str, report: EvaluationReport, promote: bool,
                checkpoint_id: str, spend: int, key: str, correlation_id: str) -> IterationRecord:
        reason = None if promote else ("gate_failed" if report.outcome == FAILED
                                       else "gate_inconclusive")
        body = canonical([loop_id, index, metric.metric_id, candidate_id, report.outcome,
                          report.report_id, "promoted" if promote else "declined"])
        return IterationRecord(
            record_id="ir-" + hashlib.sha256(body.encode()).hexdigest()[:12], loop_id=loop_id,
            iteration_index=index, metric_id=metric.metric_id, distance_before=metric.distance,
            distance_after=distance_after, candidate_id=candidate_id,
            gate_outcome=report.outcome, report_id=report.report_id,
            cases_executed=report.cases_executed,
            decision="promoted" if promote else "declined", reason=reason,
            checkpoint_id=checkpoint_id, checkpoint_advanced=bool(promote), spend_micros=spend,
            idempotency_key=key, correlation_id=correlation_id)

    @staticmethod
    def _outcome(state: dict[str, Any], terminated_by: str, held: int, total: int,
                 escalation: Problem | None) -> LoopOutcome:
        return LoopOutcome(
            loop_id=state["loop_id"], terminated_by=terminated_by,
            termination_class=TERMINATION_CLASS[terminated_by],
            iterations_run=int(state["iteration_index"]), cost_micros=int(state["spend_micros"]),
            final_checkpoint_id=state["checkpoint_id"], targets_held=held, targets_total=total,
            escalation=escalation.as_dict() if escalation is not None else None)


DRIVERS = ("dryrun", "live", "second")


def load_driver(name: str, gate: Gate | None = None,
                decision_rule: Callable[[str], bool] = promote_on_pass) -> ImprovementLoopDriver:
    """Selection is configuration only - ADAPTER=dryrun|live|second. A code edit
    between runs would not be a swap."""
    if name not in DRIVERS:
        raise SystemExit(f"unknown driver {name!r}; choose one of {', '.join(DRIVERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter(gate=gate, decision_rule=decision_rule)


# --- design assertions, checked by the conformance run -----------------------
def interface_operations() -> tuple[str, ...]:
    """The operations the core may import. Anything else on a driver is the driver's
    own business and no caller may reach it."""
    return tuple(sorted(n for n in dir(ImprovementLoopDriver)
                        if not n.startswith("_")
                        and callable(getattr(ImprovementLoopDriver, n, None))
                        and n not in ("next_fire",)))


def no_in_place_edit_operation() -> bool:
    """Nothing on this interface writes a target: a promotion moves a checkpoint and
    a metric value, and there is nowhere to put a file path."""
    banned = ("apply", "edit", "write_target", "commit", "publish")
    return not any(b in n for n in interface_operations() for b in banned)


def candidate_carries_no_criterion() -> bool:
    """A candidate names the gate it will be put through and has nowhere to put the
    text it is graded against."""
    names = {f.name for f in fields(CandidateChange)} | {f.name for f in fields(GateSpec)}
    return "gate" in names and not any(
        n in names for n in ("rubric", "rubric_body", "criterion", "criterion_text", "grading_prompt"))


def ceiling_is_required() -> bool:
    return "iteration_ceiling" in LOOP_SPEC_SCHEMA["required"]


# --- the conformance report shape --------------------------------------------
REPORT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:agentic:compose:improvement-loop:conformance:0.1",
    "title": "ImprovementLoopConformanceReport",
    "type": "object",
    "additionalProperties": False,
    "required": ["adapter", "role", "execution_model", "checkpoint_store",
                 "survives_process_loss", "promotion_authority", "gate", "checks_total",
                 "checks_passed", "iterations_run", "terminated_by", "termination_class",
                 "metric_order", "gate_outcomes", "decisions", "promoted", "declined",
                 "checkpoint_held_on_failed_gate", "checkpoints_written", "records_digest",
                 "unbounded_refused_with", "cap_terminated_by", "cap_escalation_type",
                 "budget_terminated_by", "cost_micros", "scorecard_digest",
                 "replayed_record_is_same", "selected_by", "adapters_run"],
    "properties": {
        "adapter": {"enum": list(DRIVERS)},
        "role": {"enum": ["today", "second", "dryrun"]},
        "execution_model": {"enum": ["bounded-in-process", "one-iteration-per-fire",
                                     "session-per-section"]},
        "checkpoint_store": {"enum": ["in-memory", "file", "ceremony-records"]},
        "survives_process_loss": {"type": "boolean"},
        "promotion_authority": {"enum": ["evaluation_gate", "session_reviewer"]},
        "gate": {"type": "string", "minLength": 3},
        "checks_total": {"type": "integer", "minimum": 1},
        "checks_passed": {"type": "integer", "minimum": 0},
        "iterations_run": {"type": "integer", "minimum": 0},
        "terminated_by": {"enum": list(TERMINATED_BY)},
        "termination_class": {"enum": ["stop", "cap"]},
        "metric_order": {"type": "array", "items": {"type": "string"}},
        "gate_outcomes": {"type": "array", "items": {"type": "string"}},
        "decisions": {"type": "array", "items": {"type": "string"}},
        "promoted": {"type": "integer", "minimum": 0},
        "declined": {"type": "integer", "minimum": 0},
        "checkpoint_held_on_failed_gate": {"type": "boolean"},
        "checkpoints_written": {"type": "integer", "minimum": 1},
        "records_digest": {"type": "string", "minLength": 8},
        "unbounded_refused_with": {"type": "string"},
        "cap_terminated_by": {"enum": list(TERMINATED_BY)},
        "cap_escalation_type": {"type": "string"},
        "budget_terminated_by": {"enum": list(TERMINATED_BY)},
        "cost_micros": {"type": "integer", "minimum": 0},
        "scorecard_digest": {"type": "string", "minLength": 8},
        "replayed_record_is_same": {"type": "boolean"},
        "selected_by": {"const": "configuration"},
        "adapters_run": {"type": "integer", "minimum": 1},
        # present only on a merged report, which is why they are not required
        "adapters": {"type": "array", "items": {"type": "string"}},
        "record_divergence": {"type": "integer", "minimum": 0},
        "axes_differ": {"type": "array", "items": {"type": "string"}},
    },
}


def records_digest(records: list[dict[str, Any]]) -> str:
    """One digest over the iteration records a driver wrote, correlation included.
    Two drivers that ran the same loop agree on it, and the merge can say so without
    trusting either."""
    return "sha256:" + hashlib.sha256(canonical(records).encode()).hexdigest()[:32]
