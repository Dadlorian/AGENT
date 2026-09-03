#!/usr/bin/env python3
"""Evaluation capability interface - the whole contract, with no harness in sight.

Read in this order:
  Case, StubPolicy       one scenario: an input, a rubric handle (never a rubric
                         body) and the policy that says a replayed effect is
                         served from the record, never executed
  CaseSetHandle          a versioned corpus reduced to an id and a content digest
  Trajectory             the ordered trace a unit produced this time: plan, tool
                         calls, observations, answer - scoring reads all of it
  CaseVerdict            per-dimension scores and one per-case pass or fail
  EvaluationReport       outcome is passed | failed | inconclusive, beside
                         cases_executed, so a run that executed nothing cannot
                         read as a pass
  GateStageResult        what a release gate records; its status is copied from
                         the report's counters and never from an exit code
  EvaluationAdapter      the five operations the core imports: register_case_set,
                         evaluate, replay_case, score_trajectory, promote_baseline
  Problem                RFC 9457 problem details, minted only from a closed registry

Governing standard: none adopted. The GenAI semantic conventions carry a verdict
and do not produce one, so the case-set, replay and verdict shapes here are this
repository's own design; see provenance.json for the research records behind each.
No product name appears in this file, in call.py or in conformance.py; they appear
only inside adapters/ and in README's env-var table. Python 3.11 stdlib only.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Any, Callable

# The dimensions a trajectory is scored on. Sourced research names four; the
# fourth (multi-turn quality) needs more than one turn and is out of this
# harness's scope - recorded in provenance.json rather than silently dropped.
DIMENSIONS = ("trajectory", "tool_use", "task_completion")

# Three-valued, in the order a caller should read them. There is no boolean here
# and nowhere to put one.
PASSED, FAILED, INCONCLUSIVE = "passed", "failed", "inconclusive"
OUTCOMES = (PASSED, FAILED, INCONCLUSIVE)

# The only way an external effect may reach a replayed case.
EFFECT_MODES = ("served-from-record",)

OPERATIONS = ("register_case_set", "evaluate", "replay_case", "score_trajectory",
              "promote_baseline")


# --- shapes ------------------------------------------------------------------
@dataclass(frozen=True)
class StubPolicy:
    """mode is replay here throughout; unrecorded_effect says what happens when
    replay meets an effect the record does not hold. Executing it is not one of
    the choices, which is why there is no third value."""
    mode: str = "replay"
    unrecorded_effect: str = "refuse"      # "refuse" | "fail"


@dataclass(frozen=True)
class Case:
    """One scenario. rubric_ref is an opaque handle: the text this case is scored
    against is resolved inside the scorer, after the trajectory exists, so a unit
    that reads its whole input still cannot read what it is graded on."""
    case_id: str
    corpus_half: str                        # "recorded" | "synthetic"
    input: dict[str, Any]
    rubric_ref: str
    stub_policy: StubPolicy = field(default_factory=StubPolicy)
    recorded_run_ref: str | None = None


@dataclass(frozen=True)
class CaseSetHandle:
    case_set_id: str
    version: str
    digest: str
    case_count: int


@dataclass(frozen=True)
class UnitRef:
    """Pinned. A report that cannot name the version it scored is comparable to
    no other report."""
    ref: str
    version: str


@dataclass(frozen=True)
class Trajectory:
    """The ordered trace, not the answer. served_effects counts results read from
    the record; executed_effects exists to be asserted zero - a replay that
    executed one is a live run mislabelled."""
    case_id: str
    unit: UnitRef
    steps: list[dict[str, Any]]
    served_effects: int = 0
    executed_effects: int = 0
    unit_saw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CaseVerdict:
    case_id: str
    verdict: str                            # "pass" | "fail"
    dimension_scores: dict[str, str]        # dimension -> "pass" | "fail"


@dataclass(frozen=True)
class Transition:
    case_id: str
    was: str                                # "pass" | "fail" | "absent"
    now: str                                # "pass" | "fail"
    dimension_scores: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationReport:
    report_id: str
    unit_under_test: UnitRef
    case_set: CaseSetHandle
    baseline_id: str
    outcome: str
    cases_executed: int
    transitions: list[Transition]
    correlation_id: str
    verdicts: dict[str, str] = field(default_factory=dict)
    unrecorded_effects: int = 0
    executed_effects: int = 0
    served_effects: int = 0
    refusals: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "unit_under_test": {"ref": self.unit_under_test.ref,
                                "version": self.unit_under_test.version},
            "case_set": {"case_set_id": self.case_set.case_set_id,
                         "digest": self.case_set.digest},
            "baseline_id": self.baseline_id, "outcome": self.outcome,
            "cases_executed": self.cases_executed,
            "transitions": [{"case_id": t.case_id, "was": t.was, "now": t.now,
                             "dimension_scores": t.dimension_scores}
                            for t in self.transitions],
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True)
class GateStageResult:
    """The stage record a pipeline writes. status is read from the report's
    counters; skipped and inconclusive both block promotion and neither may be
    reported as green."""
    stage: str
    status: str                             # passed | failed | inconclusive | skipped
    cases_executed: int
    report_id: str
    adapters_run: int
    evidence_record_id: str

    def as_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "status": self.status,
                "cases_executed": self.cases_executed, "report_id": self.report_id,
                "adapters_run": self.adapters_run,
                "evidence_record_id": self.evidence_record_id}

    @property
    def blocks_promotion(self) -> bool:
        return self.status != PASSED


@dataclass(frozen=True)
class Problem:
    """RFC 9457 problem details. The only failure shape this interface returns."""
    type: str
    title: str
    status: int
    detail: str
    retryable: bool
    correlation_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"type": self.type, "title": self.title, "status": self.status,
                "detail": self.detail, "retryable": self.retryable,
                "correlation_id": self.correlation_id}


PROBLEM_BASE = "urn:agentic:problem:"
# Closed registry. registered=False marks a row that is proposed and not yet in
# the registry cap-errors owns; nothing may mint it, so the fallback is returned
# instead - which is itself the argument for adding the row.
REGISTRY: dict[str, dict[str, Any]] = {
    "adapter-unavailable": {"status": 503, "retryable": True, "registered": True,
                            "title": "The evaluation adapter could not be reached"},
    "case-set-unresolved": {"status": 404, "retryable": False, "registered": True,
                            "title": "No case set is registered under that id"},
    "unrecorded-effect": {"status": 422, "retryable": False, "registered": True,
                          "title": "Replay met an effect the record does not hold"},
    "baseline-missing": {"status": 404, "retryable": False, "registered": False,
                         "title": "No baseline is stored under that id"},
}
FALLBACK_PROBLEM = "adapter-unavailable"


def problem(kind: str, detail: str, correlation_id: str | None = None) -> Problem:
    row = REGISTRY[kind]
    if not row["registered"]:
        kind, row = FALLBACK_PROBLEM, REGISTRY[FALLBACK_PROBLEM]
    return Problem(PROBLEM_BASE + kind, row["title"], row["status"], detail,
                   row["retryable"], correlation_id)


class AdapterUnavailable(Exception):
    """Raised at construction when an adapter's configuration is absent. Carries
    problem details; it is never raised out of an operation."""

    def __init__(self, problem_: Problem):
        super().__init__(problem_.detail)
        self.problem = problem_


class UnrecordedEffect(Exception):
    """Replay met an effect the record does not hold. Re-exported from the unit's
    module so an adapter never needs to import the unit to catch it."""

    def __init__(self, tool: str, args: dict):
        super().__init__(f"no recorded result for {tool}({args})")
        self.tool, self.args = tool, args


# --- content addressing ------------------------------------------------------
def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def effect_key(tool: str, args: dict[str, Any]) -> str:
    """One spelling of an effect, so a record written by one adapter is readable
    by another."""
    return f"{tool}|{canonical(args)}"


def digest_cases(cases: list[Case]) -> str:
    """Content digest over the canonical cases: registering identical cases twice
    agrees, whichever adapter stored them."""
    body = canonical([{"case_id": c.case_id, "corpus_half": c.corpus_half,
                       "input": c.input, "rubric_ref": c.rubric_ref,
                       "recorded_run_ref": c.recorded_run_ref,
                       "stub_policy": {"mode": c.stub_policy.mode,
                                       "unrecorded_effect": c.stub_policy.unrecorded_effect}}
                      for c in cases])
    return "sha256:" + hashlib.sha256(body.encode()).hexdigest()[:32]


def report_id_for(unit: UnitRef, digest: str, baseline_id: str,
                  verdicts: dict[str, str]) -> str:
    """Derived from what was scored, not from who scored it: two adapters that
    agree produce the same id, and the merge can say so without trusting either."""
    body = canonical([unit.ref, unit.version, digest, baseline_id, sorted(verdicts.items())])
    return "er-" + hashlib.sha256(body.encode()).hexdigest()[:12]


# --- scoring -----------------------------------------------------------------
def score_steps(steps: list[dict[str, Any]], rubric: dict[str, Any]) -> dict[str, str]:
    """The scoring rules belong to the capability; where the rubric was stored
    belongs to the adapter. Reads the ordered trace, not only the final answer:
    a case whose answer is right and whose tool calls are wrong fails."""
    kinds = [s["kind"] for s in steps]
    ordered, at = True, -1
    for required in rubric.get("required_steps", []):
        nxt = next((i for i, k in enumerate(kinds) if k == required and i > at), None)
        if nxt is None:
            ordered = False
            break
        at = nxt
    called = {s["tool"] for s in steps if s["kind"] == "tool_call"}
    answers = [s.get("detail", "") for s in steps if s["kind"] == "answer"]
    want = rubric.get("answer_contains", "")
    return {
        "trajectory": "pass" if ordered else "fail",
        "tool_use": "pass" if set(rubric.get("required_tools", [])) <= called else "fail",
        "task_completion": "pass" if any(want in a for a in answers) else "fail",
    }


def verdict_of(scores: dict[str, str]) -> str:
    return "pass" if all(v == "pass" for v in scores.values()) else "fail"


def outcome_for(cases_executed: int, verdicts: dict[str, str]) -> str:
    """A run in which no case executed takes the third value. An empty selector,
    a case set that failed to resolve or a harness that stopped before the first
    case reports inconclusive, never passed."""
    if cases_executed == 0 or not verdicts:
        return INCONCLUSIVE
    return FAILED if any(v == "fail" for v in verdicts.values()) else PASSED


def transitions_for(verdicts: dict[str, str], baseline: dict[str, str]) -> list[Transition]:
    """Per case, never an aggregate delta: the movement is what names the case."""
    out = []
    for case_id, now in sorted(verdicts.items()):
        was = baseline.get(case_id, "absent")
        if was != now:
            out.append(Transition(case_id=case_id, was=was, now=now))
    return out


# --- the release gate --------------------------------------------------------
def gate_stage(report: EvaluationReport | None, evidence_record_id: str,
               adapters_run: int = 1) -> GateStageResult:
    """Status is copied from the report's own counters. A stage that ran nothing
    exits zero, so an exit code cannot be the source of this field."""
    if report is None:
        return GateStageResult("evaluation", "skipped", 0, "", adapters_run, evidence_record_id)
    status = report.outcome if report.cases_executed > 0 else INCONCLUSIVE
    return GateStageResult("evaluation", status, report.cases_executed,
                           report.report_id, adapters_run, evidence_record_id)


def gate_stage_from_exit_code(report: EvaluationReport | None, evidence_record_id: str,
                              exit_code: int, adapters_run: int = 1) -> GateStageResult:
    """THE DELIBERATE BREAKAGE, reached only under conformance.py --break-gate.
    Same stage record, status derived from the exit code alone - the structurally
    green pipeline, reproduced on purpose so the check that catches it can fail."""
    executed = report.cases_executed if report else 0
    return GateStageResult("evaluation", PASSED if exit_code == 0 else FAILED, executed,
                           report.report_id if report else "", adapters_run, evidence_record_id)


# --- the interface -----------------------------------------------------------
class EvaluationAdapter(ABC):
    """Five operations and nothing else. There is no operation that executes an
    effect, none that names a metric class, a dataset loader, a test-runner or a
    collector, and none that carries a rubric body."""

    name: str = "unnamed"
    role: str = "dryrun"                    # "today" | "second" | "dryrun"
    execution_model: str = "in-process"     # collector-backed | no-server | in-process
    trajectory_source: str = "in-memory-record"  # trace-backend | fixture-file | in-memory-record
    emit_evaluation_result: bool = False    # whether verdicts leave on the standard carrier

    @abstractmethod
    def register_case_set(self, cases: list[Case], version: str,
                          case_set_id: str) -> CaseSetHandle | Problem:
        """Store the corpus and return its id and content digest."""

    @abstractmethod
    def replay_case(self, unit: UnitRef, case: Case) -> Trajectory | Problem:
        """Run the unit again with every recorded external effect served from the
        record. Returns problem details, never an exception, when the record
        cannot serve one."""

    @abstractmethod
    def score_trajectory(self, trajectory: Trajectory, rubric_ref: str) -> CaseVerdict | Problem:
        """Resolve the handle inside the scorer, score the ordered trace."""

    @abstractmethod
    def evaluate(self, unit: UnitRef, case_set_id: str, baseline_id: str,
                 correlation_id: str, mode: str = "replay",
                 case_filter: str | None = None) -> EvaluationReport | Problem:
        """The one call a gate makes. Returns one report or one problem."""

    @abstractmethod
    def promote_baseline(self, report_id: str, reason: str) -> str | Problem:
        """Append a new baseline; the previous one is retained, never overwritten."""


class EvaluationAdapterBase(EvaluationAdapter):
    """Everything that is the capability's, implemented once: the replay loop, the
    scoring rules, the three-valued outcome and the baseline comparison. What an
    adapter supplies is where the bytes live - the corpus, the record, the rubric,
    the baseline and the report sink. Nothing below reaches a store directly."""

    # --- storage hooks an adapter fills in ----------------------------------
    @abstractmethod
    def store_case_set(self, handle: CaseSetHandle, cases: list[Case]) -> None: ...

    @abstractmethod
    def load_case_set(self, case_set_id: str) -> tuple[CaseSetHandle, list[Case]] | Problem: ...

    @abstractmethod
    def fetch_record(self, case: Case) -> dict[str, Any] | Problem: ...

    @abstractmethod
    def resolve_rubric(self, rubric_ref: str) -> dict[str, Any] | Problem: ...

    @abstractmethod
    def load_baseline(self, baseline_id: str) -> dict[str, Any] | Problem: ...

    @abstractmethod
    def store_report(self, report: EvaluationReport) -> None: ...

    @abstractmethod
    def store_baseline(self, baseline_id: str, body: dict[str, Any]) -> None: ...

    @abstractmethod
    def load_report(self, report_id: str) -> EvaluationReport | Problem: ...

    # --- the five operations -------------------------------------------------
    def register_case_set(self, cases: list[Case], version: str,
                          case_set_id: str) -> CaseSetHandle | Problem:
        handle = CaseSetHandle(case_set_id, version, digest_cases(cases), len(cases))
        self.store_case_set(handle, cases)
        return handle

    def replay_case(self, unit: UnitRef, case: Case) -> Trajectory | Problem:
        record = self.fetch_record(case)
        if isinstance(record, Problem):
            return record
        effects, served = record.get("effects", {}), []

        def serve(tool: str, args: dict[str, Any]) -> Any:
            key = effect_key(tool, args)
            if key not in effects:            # executing it is not an option
                raise UnrecordedEffect(tool, args)
            served.append(key)
            return effects[key]

        try:
            steps, seen = self._run_unit(unit, case, serve)
        except UnrecordedEffect as exc:
            return problem("unrecorded-effect",
                           f"case {case.case_id} asked for {exc.tool}({canonical(exc.args)}) and the "
                           f"record does not hold it; stub policy is {case.stub_policy.unrecorded_effect}",
                           correlation_id=case.case_id)
        return Trajectory(case_id=case.case_id, unit=unit, steps=steps,
                          served_effects=len(served), executed_effects=0, unit_saw=seen)

    def _run_unit(self, unit: UnitRef, case: Case, serve: Callable):
        """The one place the unit under test is reached. Isolated so an adapter
        never imports it and the interface never executes an effect itself."""
        import unit_under_test
        try:
            return unit_under_test.run(unit.version, case.input, serve)
        except unit_under_test.UnrecordedEffect as exc:      # the unit's own class
            raise UnrecordedEffect(exc.tool, exc.args) from None

    def score_trajectory(self, trajectory: Trajectory, rubric_ref: str) -> CaseVerdict | Problem:
        rubric = self.resolve_rubric(rubric_ref)
        if isinstance(rubric, Problem):
            return rubric
        scores = score_steps(trajectory.steps, rubric)
        return CaseVerdict(trajectory.case_id, verdict_of(scores), scores)

    def evaluate(self, unit: UnitRef, case_set_id: str, baseline_id: str,
                 correlation_id: str, mode: str = "replay",
                 case_filter: str | None = None) -> EvaluationReport | Problem:
        loaded = self.load_case_set(case_set_id)
        if isinstance(loaded, Problem):
            return loaded
        handle, cases = loaded
        baseline = self.load_baseline(baseline_id)
        if isinstance(baseline, Problem):
            return baseline
        selected = [] if case_filter == "none" else [
            c for c in cases if case_filter in (None, "all") or c.case_id == case_filter]
        verdicts: dict[str, str] = {}
        dims: dict[str, dict[str, str]] = {}
        refusals: list[dict[str, Any]] = []
        unrecorded = served = executed = 0
        for case in selected:
            traj = self.replay_case(unit, case)
            if isinstance(traj, Problem):
                verdicts[case.case_id] = "fail"
                dims[case.case_id] = {d: "fail" for d in DIMENSIONS}
                refusals.append(traj.as_dict())
                unrecorded += 1
                continue
            served += traj.served_effects
            executed += traj.executed_effects
            scored = self.score_trajectory(traj, case.rubric_ref)
            if isinstance(scored, Problem):
                refusals.append(scored.as_dict())
                continue
            verdicts[case.case_id] = scored.verdict
            dims[case.case_id] = scored.dimension_scores
        per_case = baseline.get("per_case", {})
        moves = [Transition(t.case_id, t.was, t.now, dims.get(t.case_id, {}))
                 for t in transitions_for(verdicts, per_case)]
        report = EvaluationReport(
            report_id=report_id_for(unit, handle.digest, baseline_id, verdicts),
            unit_under_test=unit, case_set=handle, baseline_id=baseline_id,
            outcome=outcome_for(len(verdicts), verdicts), cases_executed=len(verdicts),
            transitions=moves, correlation_id=correlation_id, verdicts=verdicts,
            unrecorded_effects=unrecorded, executed_effects=executed,
            served_effects=served, refusals=refusals)
        self.store_report(report)
        return report

    def promote_baseline(self, report_id: str, reason: str) -> str | Problem:
        report = self.load_report(report_id)
        if isinstance(report, Problem):
            return report
        new_id = "bl-" + hashlib.sha256(
            canonical([report.report_id, reason]).encode()).hexdigest()[:10]
        self.store_baseline(new_id, {"baseline_id": new_id, "case_set_id": report.case_set.case_set_id,
                                     "unit": {"ref": report.unit_under_test.ref,
                                              "version": report.unit_under_test.version},
                                     "per_case": dict(report.verdicts),
                                     "promoted_from": report.report_id, "reason": reason})
        return new_id


ADAPTERS = ("dryrun", "live", "second")


def load_adapter(name: str) -> EvaluationAdapter:
    """Selection is configuration only - ADAPTER=dryrun|live|second. A code edit
    between runs would not be a swap."""
    if name not in ADAPTERS:
        raise SystemExit(f"unknown adapter {name!r}; choose one of {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter()


# --- design assertions, checked by the conformance run -----------------------
def interface_operations() -> tuple[str, ...]:
    """The operations the core may import. Anything else on an adapter is the
    adapter's own business and no caller may reach it."""
    return tuple(sorted(n for n in dir(EvaluationAdapter)
                        if not n.startswith("_")
                        and callable(getattr(EvaluationAdapter, n, None))
                        and n not in ("name", "role")))


def no_execute_operation() -> bool:
    """Nothing on this interface executes an effect, and the only mode by which
    one may reach a replayed case is reading it out of the record."""
    return (EFFECT_MODES == ("served-from-record",)
            and not any(re.search(r"execute|invoke_tool|call_tool", n)
                        for n in interface_operations()))


def case_carries_no_rubric_body() -> bool:
    """A case has a handle and nowhere to put the text it is graded against."""
    names = {f.name for f in fields(Case)}
    return "rubric_ref" in names and not any(
        re.search(r"rubric_(body|text)|criterion|grading_prompt", n) for n in names)


def report_pins_versions(report: EvaluationReport) -> bool:
    return bool(report.unit_under_test.version and report.case_set.digest)


# --- the conformance report shape --------------------------------------------
REPORT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:agentic:evaluation:conformance:0.1",
    "title": "EvaluationConformanceReport",
    "type": "object",
    "additionalProperties": False,
    "required": ["adapter", "role", "execution_model", "trajectory_source",
                 "emit_evaluation_result", "checks_total", "checks_passed",
                 "cases_executed", "outcome", "transitions", "transitions_named",
                 "regressed_outcome", "regressed_transitions", "unrecorded_effects",
                 "executed_effects",
                 "served_effects", "digest", "report_id", "verdicts",
                 "gate_status_zero_case", "gate_blocks_zero_case",
                 "rubric_markers_seen_by_unit", "baseline_retained",
                 "selected_by", "adapters_run"],
    "properties": {
        "adapter": {"enum": list(ADAPTERS)},
        "role": {"enum": ["today", "second", "dryrun"]},
        "execution_model": {"enum": ["collector-backed", "no-server", "in-process"]},
        "trajectory_source": {"enum": ["trace-backend", "fixture-file", "in-memory-record"]},
        "emit_evaluation_result": {"type": "boolean"},
        "checks_total": {"type": "integer", "minimum": 1},
        "checks_passed": {"type": "integer", "minimum": 0},
        "cases_executed": {"type": "integer", "minimum": 0},
        "outcome": {"enum": list(OUTCOMES)},
        "transitions": {"type": "integer", "minimum": 0},
        "transitions_named": {"type": "array", "items": {"type": "string"}},
        "regressed_outcome": {"enum": list(OUTCOMES)},
        "regressed_transitions": {"type": "integer", "minimum": 0},
        "unrecorded_effects": {"type": "integer", "minimum": 0},
        "executed_effects": {"type": "integer", "minimum": 0},
        "served_effects": {"type": "integer", "minimum": 0},
        "digest": {"type": "string", "minLength": 8},
        "report_id": {"type": "string", "minLength": 3},
        "verdicts": {"type": "object"},
        "gate_status_zero_case": {"enum": list(OUTCOMES) + ["skipped"]},
        "gate_blocks_zero_case": {"type": "boolean"},
        "rubric_markers_seen_by_unit": {"type": "integer", "minimum": 0},
        "baseline_retained": {"type": "boolean"},
        "selected_by": {"const": "configuration"},
        "adapters_run": {"type": "integer", "minimum": 1},
        # present only on a merged report, which is why they are not required
        "adapters": {"type": "array", "items": {"type": "string"}},
        "verdict_divergence": {"type": "integer", "minimum": 0},
        "axes_differ": {"type": "array", "items": {"type": "string"}},
    },
}

GATE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:agentic:evaluation:gate-stage:0.1",
    "title": "GateStageResult",
    "type": "object",
    "additionalProperties": False,
    "required": ["stage", "status", "cases_executed", "report_id", "adapters_run",
                 "evidence_record_id"],
    "properties": {
        "stage": {"const": "evaluation"},
        "status": {"enum": [PASSED, FAILED, INCONCLUSIVE, "skipped"]},
        "cases_executed": {"type": "integer", "minimum": 0},
        "report_id": {"type": "string"},
        "adapters_run": {"type": "integer", "minimum": 1},
        "evidence_record_id": {"type": "string"},
    },
}

_TYPES = {"object": dict, "array": list, "string": str, "integer": int,
          "number": (int, float), "boolean": bool}


def validate(inst: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Return human-readable errors; empty means valid. Supports exactly the
    keywords the two schemas above use."""
    errs: list[str] = []
    t = schema.get("type")
    if t:
        bad = not isinstance(inst, _TYPES[t]) or (t == "integer" and isinstance(inst, bool))
        if bad:
            return [f"{path}: expected {t}, got {type(inst).__name__}"]
    if "const" in schema and inst != schema["const"]:
        errs.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: must be one of {schema['enum']}")
    if isinstance(inst, str) and len(inst) < schema.get("minLength", 0):
        errs.append(f"{path}: shorter than minLength {schema['minLength']}")
    if isinstance(inst, int) and not isinstance(inst, bool):
        if inst < schema.get("minimum", inst):
            errs.append(f"{path}: below minimum {schema['minimum']}")
    if isinstance(inst, list):
        for i, item in enumerate(inst):
            errs += validate(item, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(inst, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in inst:
                errs.append(f"{path}: missing required property '{req}'")
        if schema.get("additionalProperties") is False:
            errs += [f"{path}: property '{k}' is not allowed" for k in inst if k not in props]
        for k, v in inst.items():
            if k in props:
                errs += validate(v, props[k], f"{path}.{k}")
    return errs
