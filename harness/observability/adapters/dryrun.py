#!/usr/bin/env python3
"""Dry-run adapter: deterministic, in-process, no network, no product.

Execution model: an in-memory store of serialised signals with a semantic object
model over them, so it can answer a question about a model call without anyone
writing a query. It exists so the whole interface - including the failure path -
runs here with nothing installed.
"""
from __future__ import annotations

import copy
import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import (MAPPING_VERSION, OPERATION_NAMES, RUN_ID_KEY, CorrelationRecord,
                       EmissionContext, INSTRUMENT_NAMES, MappingDescription, Problem,
                       Signal, TelemetryAdapter, TelemetryUnit, problem)


class Adapter(TelemetryAdapter):
    name = "dryrun"
    semantic_queries_supported = True

    def __init__(self) -> None:
        self._store: list[dict] = []          # serialised on the way in, parsed on the way out

    def bind(self, correlation: CorrelationRecord) -> EmissionContext:
        return EmissionContext(resource=correlation.as_resource())

    def emit(self, ctx: EmissionContext, unit: TelemetryUnit) -> None:
        self._store.append({"kind": "span", "resource": copy.deepcopy(ctx.resource),
                            "unit": asdict(unit)})

    def measure(self, ctx: EmissionContext, instrument: str, value: float,
                attributes: dict | None = None) -> None:
        self._store.append({"kind": "metric", "resource": copy.deepcopy(ctx.resource),
                            "unit": {"instrument": INSTRUMENT_NAMES.get(instrument, instrument),
                                     "value": value, "attributes": attributes or {}}})

    def describe_mapping(self) -> MappingDescription:
        return MappingDescription(version=MAPPING_VERSION, operations=dict(OPERATION_NAMES))

    def fetch_run(self, run_id: str) -> list[Signal] | Problem:
        hits = [Signal(r["kind"], r["resource"], r["unit"]) for r in self._store
                if r["resource"].get(RUN_ID_KEY) == run_id]
        if not hits:
            return problem("telemetry-unavailable",
                           f"run.id {run_id} has no retained telemetry in this store",
                           correlation_id=run_id)
        return hits
