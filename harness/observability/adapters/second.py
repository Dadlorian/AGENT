#!/usr/bin/env python3
"""Second adapter: a plain OTLP collector pipeline into a columnar store.

A different execution model, not a different product of the same shape. The first
adapter is a hosted service with a model-aware object model reached over the
network; this is a local receive-process-export pipeline that stores rows and
interprets nothing. It cannot answer a semantic question about a model call and
declares that rather than pretending.

Different wire, same interface: every signal is serialised to OTLP/HTTP JSON
(resourceSpans / resourceMetrics), handed to the receiver, redacted by a
processor, and exported as flat rows. Reads parse the rows back, so an interface
that had leaked in-memory object types could not be fed to this adapter at all.

  COLLECTOR_URL    optional; when set, the identical bytes are also POSTed to the
                   collector's OTLP/HTTP receiver. When unset the pipeline runs
                   in process and the columnar store is local: a faithful stub
                   whose shape and swap procedure are real, exercised by test.sh.
  COLLECTOR_STORE  optional path; the store is written there as JSON lines too.

Swap procedure: ADAPTER=second. Configuration only, no code edit, no change to
call.py, conformance.py or interface.py.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (MAPPING_VERSION, OPERATION_NAMES, RUN_ID_KEY, CorrelationRecord,
                       EmissionContext, INSTRUMENT_NAMES, LogRecord, MappingDescription, Problem,
                       Signal, TelemetryAdapter, TelemetryUnit, problem)

try:                                    # guarded; the pipeline runs without it
    import urllib.request
    _URLLIB = True
except ImportError:                     # pragma: no cover
    _URLLIB = False

REDACT = ("prompt", "completion", "api_key", "authorization")


def _nanos(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1_000_000_000)


def _attrs(d: dict) -> list[dict]:
    """OTLP JSON key/value list. Proposed encoding, unverified against the spec text on file."""
    out = []
    for k, v in d.items():
        val = ({"intValue": str(v)} if isinstance(v, int) and not isinstance(v, bool)
               else {"doubleValue": v} if isinstance(v, float)
               else {"boolValue": v} if isinstance(v, bool)
               else {"stringValue": str(v)})
        out.append({"key": k, "value": val})
    return out


def _unattrs(items: list[dict]) -> dict:
    out = {}
    for kv in items:
        v = kv["value"]
        out[kv["key"]] = (int(v["intValue"]) if "intValue" in v
                          else v.get("doubleValue", v.get("boolValue", v.get("stringValue"))))
    return out


# kind -> (resource-bucket key, scope-list key). log_record follows the
# OpenTelemetry Logs Data Model's own bucket names (resourceLogs/scopeLogs);
# problem_object has no OTel signal of its own, so it gets a platform-specific
# bucket built the same shape as the other three rather than being folded into
# one of them, which is exactly the "outside the correlation model" arrangement
# C09-F closes.
_BUCKETS = {"span": ("resourceSpans", "scopeSpans"),
            "metric": ("resourceMetrics", "scopeMetrics"),
            "log_record": ("resourceLogs", "scopeLogs"),
            "problem_object": ("resourceProblems", "scopeProblems")}


def otlp_body(signals: list[dict]) -> dict:
    """One OTLP/HTTP JSON body for a batch of signals. Shared with adapters/live.py
    so both backends receive byte-identical payloads."""
    body: dict = {}
    for sig in signals:
        kind = sig["kind"]
        res_key, scope_key = _BUCKETS[kind]
        res = {"resource": {"attributes": _attrs(sig["resource"])}, scope_key: []}
        scope = {"scope": {"name": "agentic.platform", "version": MAPPING_VERSION}}
        u = sig["unit"]
        if kind == "span":
            scope["spans"] = [{
                "traceId": u.get("trace_id") or "", "spanId": "", "name": u["operation"],
                "kind": 1, "startTimeUnixNano": str(_nanos(u["started_at"])),
                "endTimeUnixNano": str(_nanos(u["ended_at"])),
                "status": {"code": 1 if u["outcome"] == "ok" else 2},
                "attributes": _attrs(u.get("attributes") or {})}]
        elif kind == "metric":
            scope["metrics"] = [{"name": u["instrument"], "gauge": {"dataPoints": [
                {"asDouble": u["value"], "attributes": _attrs(u.get("attributes") or {})}]}}]
        elif kind == "log_record":
            # TraceId, SpanId and TraceFlags as top-level fields, per the
            # OpenTelemetry Logs Data Model (stable specification) - never
            # folded into resource attributes.
            scope["logRecords"] = [{
                "traceId": u.get("trace_id") or "", "spanId": u.get("span_id") or "",
                "flags": u.get("trace_flags") or 0, "severityText": u.get("severity_text", ""),
                "body": {"stringValue": u.get("body", "")},
                "attributes": _attrs(u.get("attributes") or {})}]
        else:  # problem_object
            scope["problems"] = [{
                "traceId": u.get("trace_id") or "", "spanId": u.get("span_id") or "",
                "type": u.get("type", ""), "title": u.get("title", ""),
                "status": u.get("status", 0), "detail": u.get("detail", ""),
                "retryable": u.get("retryable", False),
                "correlationId": u.get("correlation_id") or ""}]
        res[scope_key].append(scope)
        body.setdefault(res_key, []).append(res)
    return body


class Adapter(TelemetryAdapter):
    name = "second"
    semantic_queries_supported = False    # declared, not reported false-with-an-asterisk

    def __init__(self) -> None:
        self._rows: list[dict] = []       # the columnar store: flat rows, no object model
        self._store_path = os.environ.get("COLLECTOR_STORE")
        self._url = os.environ.get("COLLECTOR_URL")

    def bind(self, correlation: CorrelationRecord) -> EmissionContext:
        return EmissionContext(resource=correlation.as_resource())

    def emit(self, ctx: EmissionContext, unit: TelemetryUnit) -> None:
        self._receive(otlp_body([{"kind": "span", "resource": copy.deepcopy(ctx.resource),
                                  "unit": asdict(unit)}]))

    def measure(self, ctx: EmissionContext, instrument: str, value: float,
                attributes: dict | None = None) -> None:
        self._receive(otlp_body([{"kind": "metric", "resource": copy.deepcopy(ctx.resource),
                                  "unit": {"instrument": INSTRUMENT_NAMES.get(instrument, instrument),
                                           "value": value, "attributes": attributes or {}}}]))

    def log(self, ctx: EmissionContext, record: LogRecord) -> None:
        self._receive(otlp_body([{"kind": "log_record", "resource": copy.deepcopy(ctx.resource),
                                  "unit": asdict(record)}]))

    def emit_problem(self, ctx: EmissionContext, prob: Problem) -> None:
        self._receive(otlp_body([{"kind": "problem_object", "resource": copy.deepcopy(ctx.resource),
                                  "unit": prob.as_dict()}]))

    def describe_mapping(self) -> MappingDescription:
        return MappingDescription(version=MAPPING_VERSION, operations=dict(OPERATION_NAMES))

    def fetch_run(self, run_id: str) -> list[Signal] | Problem:
        hits = [Signal(r["kind"], json.loads(r["resource_json"]), json.loads(r["unit_json"]))
                for r in self._rows if r["run_id"] == run_id]
        if not hits:
            return problem("telemetry-unavailable",
                           f"run.id {run_id} returned no rows from the columnar store",
                           correlation_id=run_id)
        return hits

    # --- the pipeline: receive -> process -> export --------------------------
    def _receive(self, body: dict) -> None:
        if self._url and _URLLIB:                     # the deployed collector, best effort
            try:
                urllib.request.urlopen(urllib.request.Request(
                    self._url, data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"}), timeout=10).close()
            except Exception:
                pass
        self._export(self._process(body))

    @staticmethod
    def _process(body: dict) -> dict:
        """One redaction stage, applied to both backends because it lives in the
        pipeline rather than in an emitter."""
        for group in list(body.values()):
            for res in group:
                for scope in res.get("scopeSpans", []) + res.get("scopeMetrics", []):
                    for item in scope.get("spans", []):
                        item["attributes"] = [a for a in item["attributes"]
                                              if not any(w in a["key"].lower() for w in REDACT)]
        return body

    def _export(self, body: dict) -> None:
        item_key = {"span": "spans", "metric": "metrics",
                    "log_record": "logRecords", "problem_object": "problems"}
        unit_of = {"span": self._span_unit, "metric": self._metric_unit,
                   "log_record": self._log_unit, "problem_object": self._problem_unit}
        for kind, (key, inner) in _BUCKETS.items():
            for res in body.get(key, []):
                resource = _unattrs(res["resource"]["attributes"])
                for scope in res[inner]:
                    for item in scope.get(item_key[kind], []):
                        unit = unit_of[kind](item)
                        row = {"kind": kind, "run_id": resource.get(RUN_ID_KEY, ""),
                               "resource_json": json.dumps(resource), "unit_json": json.dumps(unit)}
                        self._rows.append(row)
                        if self._store_path:
                            with open(self._store_path, "a") as fh:
                                fh.write(json.dumps(row) + "\n")

    @staticmethod
    def _span_unit(span: dict) -> dict:
        iso = lambda n: datetime.utcfromtimestamp(int(n) / 1e9).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"operation": span["name"], "started_at": iso(span["startTimeUnixNano"]),
                "ended_at": iso(span["endTimeUnixNano"]),
                "outcome": "ok" if span["status"]["code"] == 1 else "error",
                "attributes": _unattrs(span["attributes"]), "trace_id": span["traceId"] or None}

    @staticmethod
    def _metric_unit(metric: dict) -> dict:
        point = metric["gauge"]["dataPoints"][0]
        return {"instrument": metric["name"], "value": point["asDouble"],
                "attributes": _unattrs(point["attributes"])}

    @staticmethod
    def _log_unit(rec: dict) -> dict:
        return {"body": rec["body"].get("stringValue", ""), "severity_text": rec["severityText"],
                "trace_id": rec["traceId"] or None, "span_id": rec["spanId"] or None,
                "trace_flags": rec.get("flags") or None, "attributes": _unattrs(rec["attributes"])}

    @staticmethod
    def _problem_unit(p: dict) -> dict:
        return {"type": p["type"], "title": p["title"], "status": p["status"],
                "detail": p["detail"], "retryable": p["retryable"],
                "correlation_id": p.get("correlationId") or None,
                "trace_id": p["traceId"] or None, "span_id": p["spanId"] or None}
