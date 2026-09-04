#!/usr/bin/env python3
"""Live adapter for today's component: Langfuse (observe-langfuse-web-1, trace UI
and ingestion API, with observe-langfuse-worker-1 behind it), reached over OTLP.

Product names are allowed in this file and nowhere outside adapters/ and the
env-var table in README. It is reached only through environment variables:

  TRACE_URL          required, the OTLP/HTTP JSON trace ingestion endpoint
  TRACE_KEY          required, the credential value the backend expects
  TRACE_AUTH_SCHEME  optional, default "Bearer"; the operator sets "Basic" where
                     the deployment authenticates that way
  TRACE_QUERY_URL    optional, the read-back surface; the run id is appended as
                     the run_id query parameter. Without it fetch_run returns
                     problem details rather than guessing at an endpoint.
  TRACE_TIMEOUT      optional, seconds, default 10

Nothing here has been run against a host: live mode is claimed, not measured.
"""
from __future__ import annotations

import base64
import copy
import json
import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (MAPPING_VERSION, OPERATION_NAMES, RUN_ID_KEY, AdapterUnavailable,
                       CorrelationRecord, EmissionContext, INSTRUMENT_NAMES, LogRecord,
                       MappingDescription, Problem, Signal, TelemetryAdapter,
                       TelemetryUnit, problem)

try:                                    # guarded: stdlib, but the guard is the contract
    import urllib.error
    import urllib.request
    _URLLIB = True
except ImportError:                     # pragma: no cover
    _URLLIB = False


def configured() -> bool:
    return bool(os.environ.get("TRACE_URL") and os.environ.get("TRACE_KEY"))


def _otlp(signals: list[dict]) -> dict:
    """The same OTLP/HTTP JSON body the second adapter builds; it is built by
    adapters/second.py and imported here so one wire format serves both."""
    from adapters.second import otlp_body
    return otlp_body(signals)


class Adapter(TelemetryAdapter):
    name = "live"
    semantic_queries_supported = True     # its ingestion API has a model-aware object model

    def __init__(self) -> None:
        if not _URLLIB:
            raise AdapterUnavailable(problem("adapter-unavailable", "urllib is not importable here"))
        if not configured():
            raise AdapterUnavailable(problem(
                "adapter-unavailable",
                "TRACE_URL and TRACE_KEY are unset; the live trace backend is not reachable"))
        self._url = os.environ["TRACE_URL"]
        self._scheme = os.environ.get("TRACE_AUTH_SCHEME", "Bearer")
        self._timeout = float(os.environ.get("TRACE_TIMEOUT", "10"))
        self._pending: list[dict] = []

    # --- the interface -------------------------------------------------------
    def bind(self, correlation: CorrelationRecord) -> EmissionContext:
        return EmissionContext(resource=correlation.as_resource())

    def emit(self, ctx: EmissionContext, unit: TelemetryUnit) -> None:
        self._post({"kind": "span", "resource": copy.deepcopy(ctx.resource), "unit": asdict(unit)})

    def measure(self, ctx: EmissionContext, instrument: str, value: float,
                attributes: dict | None = None) -> None:
        self._post({"kind": "metric", "resource": copy.deepcopy(ctx.resource),
                    "unit": {"instrument": INSTRUMENT_NAMES.get(instrument, instrument),
                             "value": value, "attributes": attributes or {}}})

    def log(self, ctx: EmissionContext, record: LogRecord) -> None:
        self._post({"kind": "log_record", "resource": copy.deepcopy(ctx.resource),
                    "unit": asdict(record)})

    def emit_problem(self, ctx: EmissionContext, prob: Problem) -> None:
        self._post({"kind": "problem_object", "resource": copy.deepcopy(ctx.resource),
                    "unit": prob.as_dict()})

    def describe_mapping(self) -> MappingDescription:
        return MappingDescription(version=MAPPING_VERSION, operations=dict(OPERATION_NAMES))

    def fetch_run(self, run_id: str) -> list[Signal] | Problem:
        query = os.environ.get("TRACE_QUERY_URL")
        if not query:
            return problem("adapter-unavailable",
                           "TRACE_QUERY_URL is unset; this deployment exposes no read-back surface",
                           correlation_id=run_id)
        sep = "&" if "?" in query else "?"
        req = urllib.request.Request(f"{query}{sep}run_id={run_id}", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                rows = json.loads(resp.read().decode())
        except Exception as exc:                       # never raised at the caller
            return problem("adapter-unavailable", f"read-back failed: {exc}", correlation_id=run_id)
        hits = [Signal(r.get("kind", "span"), r.get("resource", {}), r.get("unit", {}))
                for r in rows]
        if not hits:                                   # an empty read is not a result
            return problem("telemetry-unavailable",
                           f"run.id {run_id} has no retained telemetry at the read-back surface",
                           correlation_id=run_id)
        return hits

    # --- transport -----------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        key = os.environ["TRACE_KEY"]
        if self._scheme == "Basic" and ":" in key:
            key = base64.b64encode(key.encode()).decode()
        return {"Content-Type": "application/json", "Authorization": f"{self._scheme} {key}"}

    def _post(self, signal: dict) -> None:
        """A failed export is counted, never raised: a caller that could see one
        would start deciding whether telemetry mattered."""
        body = json.dumps(_otlp([signal])).encode()
        try:
            urllib.request.urlopen(
                urllib.request.Request(self._url, data=body, headers=self._headers()),
                timeout=self._timeout).close()
        except Exception:
            self._pending.append(signal)
