#!/usr/bin/env python3
"""Second adapter: a test-runner-shaped harness with no collector and no server.

A different execution model, not a different product of the same shape. The first
adapter reads a trajectory a running trace backend delivers; this one has nothing
running at all - every case is a file, every recorded run is a fixture on disk,
every report is a file written beside them, and a verdict is an assertion. An
operation shaped around a live trace stream fails here outright rather than
degrading, which is what makes the pair a test of the interface rather than one
thing run twice.

Same interface, different bytes: the corpus, the records, the rubrics and the
baselines are materialised into this adapter's own root at construction and
parsed back from disk on every call, so an interface that had leaked in-memory
objects could not be fed to it.

  EVAL_FIXTURE_ROOT  optional path; defaults to harness/evaluation/out/fixtures.
                     The whole store is here: no process, no port, no credential.

Swap procedure: ADAPTER=second. Configuration only - no code edit, and no change
to interface.py, call.py or conformance.py.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Any

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HARNESS)

from interface import (Case, CaseSetHandle, EvaluationAdapterBase, EvaluationReport,
                       Problem, StubPolicy, Transition, UnitRef, problem)

CORPUS = os.path.join(HARNESS, "corpus")


def _read(path: str) -> Any:
    with open(path) as fh:
        return json.load(fh)


def _write(path: str, body: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(body, fh, indent=2, sort_keys=True)


class Adapter(EvaluationAdapterBase):
    name = "second"
    role = "second"
    execution_model = "no-server"
    trajectory_source = "fixture-file"
    emit_evaluation_result = False      # no carrier here; the report a caller reads is unchanged

    def __init__(self) -> None:
        self.root = os.environ.get("EVAL_FIXTURE_ROOT", os.path.join(HARNESS, "out", "fixtures"))
        os.makedirs(os.path.join(self.root, "records"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "baselines"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "reports"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "case-sets"), exist_ok=True)
        for name in sorted(os.listdir(os.path.join(CORPUS, "recorded"))):
            shutil.copyfile(os.path.join(CORPUS, "recorded", name),
                            os.path.join(self.root, "records", name))
        shutil.copyfile(os.path.join(CORPUS, "rubrics.json"),
                        os.path.join(self.root, "rubrics.json"))
        base = _read(os.path.join(CORPUS, "baseline.json"))
        _write(os.path.join(self.root, "baselines", base["baseline_id"] + ".json"), base)

    def _path(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    # --- storage -------------------------------------------------------------
    def store_case_set(self, handle: CaseSetHandle, cases: list[Case]) -> None:
        _write(self._path("case-sets", handle.case_set_id + ".json"), {
            "case_set_id": handle.case_set_id, "version": handle.version,
            "digest": handle.digest,
            "cases": [{"case_id": c.case_id, "corpus_half": c.corpus_half, "input": c.input,
                       "rubric_ref": c.rubric_ref, "recorded_run_ref": c.recorded_run_ref,
                       "stub_policy": {"mode": c.stub_policy.mode,
                                       "unrecorded_effect": c.stub_policy.unrecorded_effect}}
                      for c in cases]})

    def load_case_set(self, case_set_id: str):
        path = self._path("case-sets", case_set_id + ".json")
        if not os.path.exists(path):
            return problem("case-set-unresolved",
                           f"no case set file for {case_set_id!r} under this fixture root")
        row = _read(path)
        cases = [Case(c["case_id"], c["corpus_half"], c["input"], c["rubric_ref"],
                      StubPolicy(**c["stub_policy"]), c["recorded_run_ref"])
                 for c in row["cases"]]
        return CaseSetHandle(row["case_set_id"], row["version"], row["digest"], len(cases)), cases

    def fetch_record(self, case: Case):
        if case.recorded_run_ref is None:
            return {"run_ref": None, "effects": {}}
        path = self._path("records", case.recorded_run_ref + ".json")
        if not os.path.exists(path):
            return problem("case-set-unresolved",
                           f"case {case.case_id} names record {case.recorded_run_ref!r}, "
                           "which is not a file under this fixture root")
        return _read(path)

    def resolve_rubric(self, rubric_ref: str):
        rubrics = _read(self._path("rubrics.json"))
        if rubric_ref not in rubrics:
            return problem("case-set-unresolved", f"no rubric file entry for {rubric_ref!r}")
        return rubrics[rubric_ref]

    def load_baseline(self, baseline_id: str):
        path = self._path("baselines", baseline_id + ".json")
        if not os.path.exists(path):
            return problem("baseline-missing", f"no baseline file for {baseline_id!r}")
        return _read(path)

    def store_report(self, report: EvaluationReport) -> None:
        body = report.as_dict()
        body["verdicts"] = dict(report.verdicts)
        _write(self._path("reports", report.report_id + ".json"), body)

    def load_report(self, report_id: str):
        path = self._path("reports", report_id + ".json")
        if not os.path.exists(path):
            return problem("case-set-unresolved", f"no report file for {report_id!r}")
        body = _read(path)
        return EvaluationReport(
            report_id=body["report_id"],
            unit_under_test=UnitRef(**body["unit_under_test"]),
            case_set=CaseSetHandle(body["case_set"]["case_set_id"], "", body["case_set"]["digest"], 0),
            baseline_id=body["baseline_id"], outcome=body["outcome"],
            cases_executed=body["cases_executed"],
            transitions=[Transition(**t) for t in body["transitions"]],
            correlation_id=body["correlation_id"], verdicts=dict(body.get("verdicts", {})))

    def store_baseline(self, baseline_id: str, body: dict) -> None:
        _write(self._path("baselines", baseline_id + ".json"), body)   # a new file, never a rewrite

    # --- read-back the conformance run uses ----------------------------------
    def baseline_ids(self) -> list[str]:
        return sorted(n[:-5] for n in os.listdir(self._path("baselines")))

    def verdicts_emitted(self) -> int:
        return 0                       # declared, not pretended: there is no carrier here
