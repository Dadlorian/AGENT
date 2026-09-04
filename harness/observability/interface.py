#!/usr/bin/env python3
"""Telemetry capability interface - the whole contract, with no backend in sight.

Read in this order:
  CorrelationRecord   what the platform stamps at entry (xc-correlation's field set)
  RESOURCE_KEYS       how that record becomes resource attributes on every signal
  TelemetryUnit       one completed unit of work - note there is no parent field
  TelemetryAdapter    the operations the core imports: bind, emit, measure,
                      describe_mapping, fetch_run
  Problem             RFC 9457 problem details, minted only from a closed registry

Governing standard: OTLP with GenAI semantic conventions (unverified) - see
provenance.json. No product name appears in this file, in call.py or in
conformance.py; they appear only inside adapters/ and in README's env-var table.
Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
# Found by walking up from this file's own directory, not by a fixed "../errors"
# offset: several harnesses' test.sh copy interface.py into out/breakage/ (and
# deeper) for a deliberate-breakage run, and a fixed relative offset would miss
# harness/errors/problem.py from there. The walk stays inside the repository
# tree either way (out/breakage/ is still nested under this harness's own
# directory), and stops at the first "errors" sibling that actually has it.
_search_dir = _errors_os.path.dirname(_errors_os.path.abspath(__file__))
for _ in range(10):
    _candidate = _errors_os.path.join(_search_dir, "errors")
    if _errors_os.path.isfile(_errors_os.path.join(_candidate, "problem.py")):
        if _candidate not in _errors_sys.path:
            _errors_sys.path.append(_candidate)  # appended, never inserted at 0: this
            # harness's own adapters/ package must resolve before errors/adapters/ does
        break
    _up = _errors_os.path.dirname(_search_dir)
    if _up == _search_dir:
        break
    _search_dir = _up
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import importlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Any

# --- the separately versioned half: the attribute mapping --------------------
# The transport half is pinned; this vocabulary half is pre-stable and versioned
# on its own cadence. Emitters never carry a literal attribute key - they ask the
# mapping for one - so revising this table is a version bump that touches no
# emitter and no adapter. Both adapters report the same version because the table
# sits in front of both.
MAPPING_VERSION = "agentic-genai-mapping/0.1"
OPERATION_NAMES = {          # platform unit of work -> operation name
    "entry": "invoke_agent",
    "dispatch": "invoke_agent",
    "tool": "execute_tool",
}
INSTRUMENT_NAMES = {         # platform measure -> instrument name
    "step_duration": "gen_ai.client.operation.duration",
}

# The correlation record as resource attributes. Resource attributes are the
# carrier because that surface is declared unchangeable by the specification that
# defines it, so correlation is not riding on a field that may be renamed.
RESOURCE_KEYS = {
    "run_id": "run.id",
    "root_dispatch_id": "correlation.id",   # xc-correlation names this root_dispatch_id
    "parent_dispatch_id": "correlation.parent_id",
    "depth": "correlation.depth",
    "entry_kind": "entry.kind",
}
MAPPING_VERSION_KEY = "telemetry.mapping_version"
RUN_ID_KEY = RESOURCE_KEYS["run_id"]
ROOT_DISPATCH_ID_KEY = RESOURCE_KEYS["root_dispatch_id"]


# --- shapes ------------------------------------------------------------------
@dataclass(frozen=True)
class CorrelationRecord:
    """Stamped by the platform at entry and re-stamped at every child dispatch.
    run_id is the grouping key; root_dispatch_id is the dispatch the run entered
    through. parent_dispatch_id records lineage and is never used to reassemble."""
    run_id: str
    root_dispatch_id: str
    parent_dispatch_id: str | None = None
    depth: int = 0
    entry_kind: str = "human"

    def as_resource(self) -> dict[str, Any]:
        out = {RESOURCE_KEYS["run_id"]: self.run_id,
               RESOURCE_KEYS["root_dispatch_id"]: self.root_dispatch_id,
               RESOURCE_KEYS["depth"]: self.depth,
               RESOURCE_KEYS["entry_kind"]: self.entry_kind,
               MAPPING_VERSION_KEY: MAPPING_VERSION}
        if self.parent_dispatch_id is not None:
            out[RESOURCE_KEYS["parent_dispatch_id"]] = self.parent_dispatch_id
        return out


@dataclass(frozen=True)
class EmissionContext:
    """What bind() returns. Every signal emitted beneath it inherits these
    resource attributes; an emitter cannot construct or edit them."""
    resource: dict[str, Any]


@dataclass(frozen=True)
class TelemetryUnit:
    """One completed unit of work. There is deliberately no parent_span_id and no
    parent argument anywhere on this interface: reassembly is a group-by on an
    attribute, never a walk up a parent chain. trace_id is carried, reported and
    never load-bearing - several distinct values inside one run are expected."""
    operation: str
    started_at: str
    ended_at: str
    outcome: str                       # "ok" | "error"
    attributes: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None


@dataclass(frozen=True)
class LogRecord:
    """One log record beneath a unit of work - the second of the three emission
    kinds xc-correlation's guarantee binds. trace_id, span_id and trace_flags
    are top-level fields here, never resource attributes, per the OpenTelemetry
    Logs Data Model (stable specification): TraceId, SpanId and TraceFlags are
    top-level log-record fields. run_id and root_dispatch_id still arrive
    through the resource the emission context carries; this shape adds only
    what that resource cannot hold - the identifiers scoped to this one record."""
    body: str
    severity_text: str
    trace_id: str | None = None
    span_id: str | None = None
    trace_flags: int | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Signal:
    """One stored signal, as read back off the wire by fetch_run."""
    kind: str                          # "span" | "metric" | "log_record" | "problem_object"
    resource: dict[str, Any]
    unit: dict[str, Any]


@dataclass(frozen=True)
class MappingDescription:
    version: str
    operations: dict[str, str]


@dataclass(frozen=True)
class Problem:
    """RFC 9457 problem details. The only failure shape this interface returns.
    trace_id and span_id are the third emission kind's stamp: xc-correlation's
    guarantee treats the failure body as in scope, not an exception to it, so a
    problem object is bound to the same trace identity as the span and log
    record of the unit that raised it rather than being outside the
    correlation model."""
    type: str
    title: str
    status: int
    detail: str
    retryable: bool
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return render_body(self.type, self.title, self.status, self.detail, self.retryable,
                            {"correlation_id": self.correlation_id, "trace_id": self.trace_id,
                             "span_id": self.span_id})


PROBLEM_BASE = "urn:agentic:problem:"
# Closed registry. registered=False marks a row that is proposed and not yet in
# the registry cap-errors owns, so nothing may mint it: the fallback is returned
# instead, 503 and retryable where a passed retention window is neither - which
# is itself the argument for adding the row.
REGISTRY: dict[str, dict[str, Any]] = {
    "adapter-unavailable": {"status": 503, "retryable": True, "registered": True,
                            "title": "The telemetry adapter could not be reached"},
    "telemetry-unavailable": {"status": 404, "retryable": False, "registered": False,
                              "title": "No telemetry is retained for that run"},
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
    problem details; it is never raised out of emit()."""

    def __init__(self, problem_: Problem):
        super().__init__(problem_.detail)
        self.problem = problem_


# --- the interface -----------------------------------------------------------
class TelemetryAdapter(ABC):
    """Seven operations and nothing else. There is no flag that switches emission
    off, no sampling decision a caller can make, and no operation that names a
    destination, a query language or a UI concept. log() and emit_problem() are
    the C09-F addition: xc-correlation's guarantee binds all three emission
    kinds - spans, log records and problem objects - not spans alone, and an
    adapter that only carried emit()/measure() left two of the three kinds with
    nowhere to be stamped."""

    name: str = "unnamed"
    semantic_queries_supported: bool = False

    @abstractmethod
    def bind(self, correlation: CorrelationRecord) -> EmissionContext:
        """The single injection point. Called at the dispatch seam and nowhere else."""

    @abstractmethod
    def emit(self, ctx: EmissionContext, unit: TelemetryUnit) -> None:
        """Hand one completed unit to the pipeline. Returns nothing: a caller who
        could read a result back would start branching on the backend."""

    @abstractmethod
    def measure(self, ctx: EmissionContext, instrument: str, value: float,
                attributes: dict[str, Any] | None = None) -> None:
        """Same transport, same resource attributes, so a metric joins to a span
        on the run id."""

    @abstractmethod
    def log(self, ctx: EmissionContext, record: LogRecord) -> None:
        """Hand one log record to the pipeline, stamped with the same resource
        attributes as the unit's span. Second of the three emission kinds."""

    @abstractmethod
    def emit_problem(self, ctx: EmissionContext, prob: Problem) -> None:
        """Hand one problem/error object to the pipeline, stamped with the same
        resource attributes as the unit that raised it. Third of the three
        emission kinds - the one a correlation model that stops at spans and
        logs leaves outside it."""

    @abstractmethod
    def describe_mapping(self) -> MappingDescription:
        """Which vocabulary this body of telemetry was emitted against."""

    @abstractmethod
    def fetch_run(self, run_id: str) -> list[Signal] | Problem:
        """Proposed read half: every signal carrying run.id == run_id, from the
        backend's own query surface. Returns problem details, never an exception,
        when the run cannot be shown."""


ADAPTERS = ("dryrun", "live", "second")


def load_adapter(name: str) -> TelemetryAdapter:
    """Selection is configuration only - ADAPTER=dryrun|live|second. A code edit
    between runs would not be a swap."""
    if name not in ADAPTERS:
        raise SystemExit(f"unknown adapter {name!r}; choose one of {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter()


# --- the conformance report shape --------------------------------------------
# cap-telemetry-implement's proposed TelemetryConformanceReport, with two
# harness extensions recorded in provenance.json: the adapter enum is widened to
# the three adapters shipped here, and spans_missing_root_dispatch_id is added so
# xc-correlation's second required field is counted as well as run.id.
REPORT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:agentic:telemetry:report:0.1",
    "title": "TelemetryConformanceReport",
    "type": "object",
    "additionalProperties": False,
    "required": ["adapter", "levels_covered", "run_id_groups", "distinct_trace_ids",
                 "mapping_version", "spans_missing_run_id",
                 "spans_missing_root_dispatch_id", "signals_checked",
                 "semantic_queries_supported", "selected_by", "adapters_run"],
    "properties": {
        "adapter": {"enum": list(ADAPTERS)},
        "levels_covered": {"type": "integer", "minimum": 0},
        "run_id_groups": {"type": "integer", "minimum": 0},
        "distinct_trace_ids": {"type": "integer", "minimum": 0},
        "mapping_version": {"type": "string", "minLength": 1},
        "spans_missing_run_id": {"type": "integer", "minimum": 0},
        "spans_missing_root_dispatch_id": {"type": "integer", "minimum": 0},
        "signals_checked": {"type": "integer", "minimum": 0},
        "semantic_queries_supported": {"type": "boolean"},
        "selected_by": {"const": "configuration"},
        "adapters_run": {"type": "integer", "minimum": 1},
    },
}

_TYPES = {"object": dict, "array": list, "string": str, "integer": int,
          "number": (int, float), "boolean": bool}


def validate(inst: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Return human-readable errors; empty means valid. Supports exactly the
    keywords REPORT_SCHEMA uses."""
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
    if isinstance(inst, str):
        if len(inst) < schema.get("minLength", 0):
            errs.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errs.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(inst, int) and not isinstance(inst, bool):
        if inst < schema.get("minimum", inst):
            errs.append(f"{path}: below minimum {schema['minimum']}")
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


def unit_has_no_parent_field() -> bool:
    """Design assertion, checked by the conformance run: the interface offers
    nowhere to put a parent, so no implementation can quietly rely on one."""
    return not any(f.name in ("parent_span_id", "parent", "traceparent")
                   for f in fields(TelemetryUnit))
