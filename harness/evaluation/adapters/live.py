#!/usr/bin/env python3
"""Live adapter for today's component: the trace backend every run already lands
in - Langfuse (observe-langfuse-web-1, trace UI and ingestion API, with
observe-langfuse-worker-1 and ClickHouse behind it), PASS.md A1 (F-a1-05).

There is no Evaluation row anywhere in PASS.md: nothing here scores anything
today. What does run is the store, so this adapter binds the capability to it -
a recorded run is a stored trajectory read back from the trace store instead of
re-executed, a case set is a dataset registered beside the traces, a report is
written back, and each per-case verdict leaves as a gen_ai.evaluation.result on
the OpenTelemetry GenAI semantic conventions (version unverified).

Product names are allowed in this file and nowhere outside adapters/ and the
env-var table in README. It is reached only through environment variables:

  EVAL_TRACE_URL         required, the ingestion endpoint case sets, reports and
                         per-case verdicts are written to
  EVAL_TRACE_QUERY_URL   required, the read-back surface; `run_ref` is appended
                         as a query parameter to fetch one recorded trajectory
  EVAL_TRACE_KEY         required, the credential value the backend expects
  EVAL_TRACE_AUTH_SCHEME optional, default "Bearer"; operators set "Basic" where
                         the deployment authenticates that way
  EVAL_TRACE_TIMEOUT     optional, seconds, default 10
  EVAL_CASE_SET_ROOT     optional, where rubric bodies are resolved from; default
                         harness/evaluation/corpus. Rubric bodies deliberately do
                         not travel to the backend: the unit under test reads its
                         own traces, so a rubric stored beside them would be
                         readable by the thing being graded.

Nothing here has been run against a host: live mode is claimed, not measured.
Two things this adapter cannot do, recorded rather than hidden: it cannot score a
run whose trace never reached the backend, and it cannot give a developer a
verdict in a checkout where no collector, ClickHouse or Langfuse is reachable.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from typing import Any

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HARNESS)

from interface import (Case, CaseSetHandle, EvaluationAdapterBase, EvaluationReport,
                       Problem, StubPolicy, Transition, UnitRef, AdapterUnavailable, problem)

try:                                    # guarded: stdlib, but the guard is the contract
    import urllib.error
    import urllib.request
    _URLLIB = True
except ImportError:                     # pragma: no cover
    _URLLIB = False

REQUIRED = ("EVAL_TRACE_URL", "EVAL_TRACE_QUERY_URL", "EVAL_TRACE_KEY")


def configured() -> bool:
    return all(os.environ.get(k) for k in REQUIRED)


class Adapter(EvaluationAdapterBase):
    name = "live"
    role = "today"
    execution_model = "collector-backed"
    trajectory_source = "trace-backend"
    emit_evaluation_result = True

    def __init__(self) -> None:
        if not _URLLIB:
            raise AdapterUnavailable(problem("adapter-unavailable", "urllib is not importable here"))
        if not configured():
            missing = ", ".join(k for k in REQUIRED if not os.environ.get(k))
            raise AdapterUnavailable(problem(
                "adapter-unavailable",
                f"{missing} unset; the trace backend that holds the recorded runs is not reachable"))
        self._url = os.environ["EVAL_TRACE_URL"].rstrip("/")
        self._query = os.environ["EVAL_TRACE_QUERY_URL"]
        self._scheme = os.environ.get("EVAL_TRACE_AUTH_SCHEME", "Bearer")
        self._timeout = float(os.environ.get("EVAL_TRACE_TIMEOUT", "10"))
        self._root = os.environ.get("EVAL_CASE_SET_ROOT", os.path.join(HARNESS, "corpus"))

    # --- transport -----------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        key = os.environ["EVAL_TRACE_KEY"]
        if self._scheme == "Basic" and ":" in key:
            key = base64.b64encode(key.encode()).decode()
        return {"Content-Type": "application/json", "Authorization": f"{self._scheme} {key}"}

    def _get(self, url: str) -> Any | Problem:
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=self._headers()), timeout=self._timeout) as r:
                return json.loads(r.read().decode())
        except Exception as exc:                       # never raised at the caller
            return problem("adapter-unavailable", f"read from the trace backend failed: {exc}")

    def _post(self, path: str, body: dict) -> Any | Problem:
        try:
            req = urllib.request.Request(f"{self._url}/{path.lstrip('/')}",
                                         data=json.dumps(body).encode(), headers=self._headers())
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
        except Exception as exc:
            return problem("adapter-unavailable", f"write to the trace backend failed: {exc}")

    # --- storage -------------------------------------------------------------
    def store_case_set(self, handle: CaseSetHandle, cases: list[Case]) -> None:
        self._post("case-sets", {
            "case_set_id": handle.case_set_id, "version": handle.version, "digest": handle.digest,
            "cases": [{"case_id": c.case_id, "corpus_half": c.corpus_half, "input": c.input,
                       "rubric_ref": c.rubric_ref, "recorded_run_ref": c.recorded_run_ref,
                       "stub_policy": {"mode": c.stub_policy.mode,
                                       "unrecorded_effect": c.stub_policy.unrecorded_effect}}
                      for c in cases]})

    def load_case_set(self, case_set_id: str):
        sep = "&" if "?" in self._query else "?"
        row = self._get(f"{self._query}{sep}case_set_id={case_set_id}")
        if isinstance(row, Problem):
            return row
        if not row:
            return problem("case-set-unresolved", f"the backend holds no case set {case_set_id!r}")
        cases = [Case(c["case_id"], c["corpus_half"], c["input"], c["rubric_ref"],
                      StubPolicy(**c.get("stub_policy", {})), c.get("recorded_run_ref"))
                 for c in row["cases"]]
        return CaseSetHandle(row["case_set_id"], row["version"], row["digest"], len(cases)), cases

    def fetch_record(self, case: Case):
        """The recorded trajectory is read out of the trace store, not re-executed."""
        if case.recorded_run_ref is None:
            return {"run_ref": None, "effects": {}}
        sep = "&" if "?" in self._query else "?"
        row = self._get(f"{self._query}{sep}run_ref={case.recorded_run_ref}")
        if isinstance(row, Problem):
            return row
        if not row:
            return problem("case-set-unresolved",
                           f"the trace store holds no run {case.recorded_run_ref!r}; a case whose "
                           "trace never arrived cannot be replayed here")
        return row

    def resolve_rubric(self, rubric_ref: str):
        path = os.path.join(self._root, "rubrics.json")
        if not os.path.exists(path):
            return problem("case-set-unresolved", f"no rubric store at {path}")
        with open(path) as fh:
            rubrics = json.load(fh)
        if rubric_ref not in rubrics:
            return problem("case-set-unresolved", f"no rubric under {rubric_ref!r}")
        return rubrics[rubric_ref]

    def load_baseline(self, baseline_id: str):
        sep = "&" if "?" in self._query else "?"
        row = self._get(f"{self._query}{sep}baseline_id={baseline_id}")
        if isinstance(row, Problem):
            return row
        return row or problem("baseline-missing", f"the backend holds no baseline {baseline_id!r}")

    def store_report(self, report: EvaluationReport) -> None:
        body = report.as_dict()
        body["verdicts"] = dict(report.verdicts)
        self._post("reports", body)
        if self.emit_evaluation_result:        # one gen_ai.evaluation.result per case
            self._post("evaluation-results", {
                "correlation_id": report.correlation_id,
                "results": [{"gen_ai.evaluation.name": "case-verdict",
                             "gen_ai.evaluation.score.label": v, "case_id": k,
                             "gen_ai.response.id": report.report_id}
                            for k, v in sorted(report.verdicts.items())]})

    def load_report(self, report_id: str):
        sep = "&" if "?" in self._query else "?"
        body = self._get(f"{self._query}{sep}report_id={report_id}")
        if isinstance(body, Problem):
            return body
        if not body:
            return problem("case-set-unresolved", f"the backend holds no report {report_id!r}")
        return EvaluationReport(
            report_id=body["report_id"], unit_under_test=UnitRef(**body["unit_under_test"]),
            case_set=CaseSetHandle(body["case_set"]["case_set_id"], "", body["case_set"]["digest"], 0),
            baseline_id=body["baseline_id"], outcome=body["outcome"],
            cases_executed=body["cases_executed"],
            transitions=[Transition(**t) for t in body["transitions"]],
            correlation_id=body["correlation_id"], verdicts=dict(body.get("verdicts", {})))

    def store_baseline(self, baseline_id: str, body: dict) -> None:
        self._post("baselines", body)          # appended by id; the previous one is not touched

    # --- read-back the conformance run uses ----------------------------------
    def baseline_ids(self) -> list[str]:
        sep = "&" if "?" in self._query else "?"
        rows = self._get(f"{self._query}{sep}baselines=all")
        return [] if isinstance(rows, Problem) else sorted(r.get("baseline_id", "") for r in rows)

    def verdicts_emitted(self) -> int:
        return -1                              # only the backend knows; never asserted here
