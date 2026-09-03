#!/usr/bin/env python3
"""Dry-run adapter: deterministic, in-process, no network, no product.

Execution model: an in-process object store. The corpus, the records, the rubrics,
the baselines and the reports are held as serialised dicts and parsed on the way
out, so a read crosses a real boundary even here. It exists so the whole
interface - including the refusal path - runs with nothing installed.

It declares emit_evaluation_result true: it has a carrier for a per-case verdict
(its own store) and reports that it does, which is the axis the second adapter
differs on.
"""
from __future__ import annotations

import copy
import json
import os
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


class Adapter(EvaluationAdapterBase):
    name = "dryrun"
    role = "dryrun"
    execution_model = "in-process"
    trajectory_source = "in-memory-record"
    emit_evaluation_result = True

    def __init__(self) -> None:
        self._case_sets: dict[str, dict] = {}
        self._reports: dict[str, dict] = {}
        self._verdicts_emitted: list[dict] = []          # the carrier, such as it is
        self._records = {name[:-5]: _read(os.path.join(CORPUS, "recorded", name))
                         for name in sorted(os.listdir(os.path.join(CORPUS, "recorded")))}
        self._rubrics = _read(os.path.join(CORPUS, "rubrics.json"))
        base = _read(os.path.join(CORPUS, "baseline.json"))
        self._baselines: dict[str, dict] = {base["baseline_id"]: base}

    # --- storage -------------------------------------------------------------
    def store_case_set(self, handle: CaseSetHandle, cases: list[Case]) -> None:
        self._case_sets[handle.case_set_id] = {
            "handle": {"case_set_id": handle.case_set_id, "version": handle.version,
                       "digest": handle.digest, "case_count": handle.case_count},
            "cases": [{"case_id": c.case_id, "corpus_half": c.corpus_half,
                       "input": copy.deepcopy(c.input), "rubric_ref": c.rubric_ref,
                       "recorded_run_ref": c.recorded_run_ref,
                       "stub_policy": {"mode": c.stub_policy.mode,
                                       "unrecorded_effect": c.stub_policy.unrecorded_effect}}
                      for c in cases]}

    def load_case_set(self, case_set_id: str):
        row = self._case_sets.get(case_set_id)
        if row is None:
            return problem("case-set-unresolved",
                           f"no case set {case_set_id!r} is registered in this store")
        h, cases = row["handle"], []
        for c in row["cases"]:
            cases.append(Case(c["case_id"], c["corpus_half"], copy.deepcopy(c["input"]),
                              c["rubric_ref"], StubPolicy(**c["stub_policy"]),
                              c["recorded_run_ref"]))
        return CaseSetHandle(h["case_set_id"], h["version"], h["digest"], h["case_count"]), cases

    def fetch_record(self, case: Case):
        if case.recorded_run_ref is None:                 # a synthetic case has no record
            return {"run_ref": None, "effects": {}}
        rec = self._records.get(case.recorded_run_ref)
        if rec is None:
            return problem("case-set-unresolved",
                           f"case {case.case_id} names record {case.recorded_run_ref!r}, "
                           "which this store does not hold")
        return copy.deepcopy(rec)

    def resolve_rubric(self, rubric_ref: str):
        rubric = self._rubrics.get(rubric_ref)
        if rubric is None:
            return problem("case-set-unresolved", f"no rubric is stored under {rubric_ref!r}")
        return copy.deepcopy(rubric)                      # resolved here, inside the scorer

    def load_baseline(self, baseline_id: str):
        row = self._baselines.get(baseline_id)
        if row is None:
            return problem("baseline-missing", f"no baseline {baseline_id!r} in this store")
        return copy.deepcopy(row)

    def store_report(self, report: EvaluationReport) -> None:
        body = report.as_dict()
        body["verdicts"] = dict(report.verdicts)
        self._reports[report.report_id] = body
        if self.emit_evaluation_result:                   # one verdict per case, on the carrier
            self._verdicts_emitted += [{"case_id": k, "result": v}
                                       for k, v in sorted(report.verdicts.items())]

    def load_report(self, report_id: str):
        body = self._reports.get(report_id)
        if body is None:
            return problem("case-set-unresolved", f"no report {report_id!r} in this store")
        return EvaluationReport(
            report_id=body["report_id"],
            unit_under_test=UnitRef(**body["unit_under_test"]),
            case_set=CaseSetHandle(body["case_set"]["case_set_id"], "", body["case_set"]["digest"], 0),
            baseline_id=body["baseline_id"], outcome=body["outcome"],
            cases_executed=body["cases_executed"],
            transitions=[Transition(**t) for t in body["transitions"]],
            correlation_id=body["correlation_id"], verdicts=dict(body.get("verdicts", {})))

    def store_baseline(self, baseline_id: str, body: dict) -> None:
        self._baselines[baseline_id] = copy.deepcopy(body)   # appended; nothing is replaced

    # --- read-back the conformance run uses ----------------------------------
    def baseline_ids(self) -> list[str]:
        return sorted(self._baselines)

    def verdicts_emitted(self) -> int:
        return len(self._verdicts_emitted)
