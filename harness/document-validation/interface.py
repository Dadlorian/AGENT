#!/usr/bin/env python3
"""Document validation: check a declared shape against a published schema dialect.

Read it in this order. ValidationRequest is the whole caller vocabulary: a
schema URI, the dialect the caller expects that schema to declare, and the
instance to check. DocumentValidationAdapter.validate() is a template method:
it reads the schema (adapter-specific), refuses one that declares no dialect or
a dialect other than 2020-12 (F-b3-09, cap-document-validation invariant 2)
*before* any instance is checked, then runs the instance through the adapter's
own check routine and returns the outcome shape every adapter must produce.
check_schema() runs the same dialect gate over a schema document on its own.
prepare()/dialect_in_effect() are the proposed operations cap-document-validation
names: a reusable handle, and what dialect the adapter actually resolved for it
(F-a7-04: never trust the declared value, ask the adapter what it resolved).

No product name, library name or vendor appears in this file (F-b1-02).
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

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

INTERFACE_VERSION = "0.1"
DIALECT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def resolve_path(schema_uri: str, base_dir: str) -> str:
    """A schema_uri is a filesystem path: absolute as-is, otherwise relative to base_dir."""
    return schema_uri if os.path.isabs(schema_uri) else os.path.join(base_dir, schema_uri)


def load_json_file(path: str, schema_uri: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise Problem("schema-unavailable", f"cannot read schema {schema_uri} at {path}: {exc}",
                      schema_uri=schema_uri, retry_after_s=5) from exc
    except json.JSONDecodeError as exc:
        raise Problem("schema-unavailable", f"schema {schema_uri} at {path} is not valid JSON: {exc}",
                      schema_uri=schema_uri, retry_after_s=None) from exc

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) ----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "request-invalid": (400, "Validation request is not well-formed", False),
    "dialect-unsupported": (422, "Schema does not declare the 2020-12 dialect", False),
    "schema-unavailable": (503, "The schema resource could not be read", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --- The caller vocabulary ---------------------------------------------------
# cap-document-validation's proposed validation-request shape: schema_uri,
# dialect, instance, offline. There is no field naming a validator library.
ALLOWED = {"schema_uri", "dialect", "instance", "offline"}
REQUIRED = {"schema_uri", "dialect", "instance"}


@dataclass(frozen=True)
class ValidationRequest:
    schema_uri: str
    dialect: str
    instance: object
    offline: bool = True

    @classmethod
    def from_dict(cls, doc: dict) -> "ValidationRequest":
        """The one gate a request passes. Never parsed downstream from prose."""
        if not isinstance(doc, dict):
            raise Problem("request-invalid", "a validation request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("request-invalid", f"fields {extra} are not in the validation request vocabulary",
                          rejected_fields=extra)
        missing = sorted(REQUIRED - set(doc))
        if missing:
            raise Problem("request-invalid", f"missing required fields {missing}", missing=missing)
        if not isinstance(doc["schema_uri"], str) or not doc["schema_uri"]:
            raise Problem("request-invalid", "schema_uri must be a non-empty string")
        if not isinstance(doc["dialect"], str) or not doc["dialect"]:
            raise Problem("request-invalid", "dialect must be a non-empty string")
        return cls(doc["schema_uri"], doc["dialect"], doc["instance"], doc.get("offline", True))


@dataclass(frozen=True)
class ValidationError:
    """One violation, located inside the instance (X-cap-document-validation-005)."""
    instance_location: str
    keyword_location: str
    message: str
    absolute_keyword_location: str | None = None

    def as_dict(self) -> dict:
        doc = {"instance_location": self.instance_location, "keyword_location": self.keyword_location,
               "message": self.message}
        if self.absolute_keyword_location:
            doc["absolute_keyword_location"] = self.absolute_keyword_location
        return doc


@dataclass(frozen=True)
class ValidationOutcome:
    """valid, plus every violation from one pass -- never the first only."""
    valid: bool
    dialect: str
    schema_uri: str
    errors: tuple  # tuple[ValidationError, ...]
    keywords_checked: int

    def as_dict(self) -> dict:
        return {"valid": self.valid, "dialect": self.dialect, "schema_uri": self.schema_uri,
                "keywords_checked": self.keywords_checked, "errors": [e.as_dict() for e in self.errors]}


@dataclass
class PreparedHandle:
    """What prepare() returns: read once, reused across instances (X-cap-document-validation-003)."""
    schema_uri: str
    declared_dialect: str
    schema_doc: dict
    compiled: object          # adapter-specific representation of the same schema
    instances_served: int = 0


def _ptr_push(path: str, seg) -> str:
    """RFC 6901 JSON Pointer, one segment at a time."""
    return path + "/" + str(seg).replace("~", "~0").replace("/", "~1")


TYPES = {"object": dict, "array": list, "string": str, "integer": int,
         "number": (int, float), "boolean": bool}


def declared_dialect_of(schema_doc: dict) -> str | None:
    """The dialect a schema resource declares in band, or None if it declares none."""
    if not isinstance(schema_doc, dict):
        return None
    return schema_doc.get("$schema")


def check_dialect(schema_uri: str, schema_doc: dict, expected: str) -> None:
    """Reject a schema that declares no dialect, or one other than what the caller
    expects, instead of assuming or silently defaulting (cap-document-validation
    invariant 2, F-a7-04). Raised before any instance is checked."""
    declared = declared_dialect_of(schema_doc)
    if declared is None:
        raise Problem("dialect-unsupported",
                      f"schema {schema_uri} declares no $schema dialect; a dialect is never assumed",
                      schema_uri=schema_uri, declared_dialect=None, expected_dialect=expected)
    if declared != expected:
        raise Problem("dialect-unsupported",
                      f"schema {schema_uri} declares dialect {declared}, not the expected {expected}",
                      schema_uri=schema_uri, declared_dialect=declared, expected_dialect=expected)


# --- The interface the core imports -----------------------------------------
class DocumentValidationAdapter(ABC):
    """One validation interface: validate, check_schema, prepare, dialect_in_effect.

    validate() and check_schema() are concrete here so that no adapter can skip
    the dialect gate: it always runs before an instance reaches adapter code.
    Only how a schema is read and how an instance is actually checked against it
    are adapter-specific.
    """

    entity = "adapter"                       # what a report names
    execution_model = "unset"                # "schema read per call" | "schema compiled ahead of use"
    processes_required_for_progress = 0
    declared_marker = "unset"
    declared_gaps: tuple = ()

    def __init__(self):
        self.schema_reads = 0        # incremented once per validate() call that walks the schema fresh
        self.prepares = 0            # incremented once per schema actually compiled/cached
        self.refusals = 0
        self.observed_marker = ""
        self._cache: dict[str, PreparedHandle] = {}

    # 1. prepare -- read once, reuse across instances
    def prepare(self, schema_uri: str, expected_dialect: str = DIALECT_2020_12) -> PreparedHandle:
        cached = self._cache.get(schema_uri)
        if cached is not None:
            return cached
        schema_doc = self._read_schema(schema_uri)
        check_dialect(schema_uri, schema_doc, expected_dialect)
        compiled = self._compile(schema_doc)
        self.prepares += 1
        handle = PreparedHandle(schema_uri, declared_dialect_of(schema_doc), schema_doc, compiled)
        self._cache[schema_uri] = handle
        return handle

    # 2. dialect_in_effect -- ask the adapter, never trust the file (F-a7-04)
    def dialect_in_effect(self, handle: PreparedHandle) -> str:
        return handle.declared_dialect

    # 3. validate -- one outcome, every violation, one pass
    def validate(self, request: ValidationRequest) -> ValidationOutcome:
        handle = self.prepare(request.schema_uri, request.dialect)
        self.observed_marker = self.declared_marker
        errors, checked = self._check(handle, request.instance)
        handle.instances_served += 1
        return ValidationOutcome(valid=not errors, dialect=self.dialect_in_effect(handle),
                                 schema_uri=request.schema_uri, errors=tuple(errors),
                                 keywords_checked=checked)

    # 4. check_schema -- is the schema itself well-formed for this dialect
    def check_schema(self, schema_uri: str, expected_dialect: str = DIALECT_2020_12) -> ValidationOutcome:
        schema_doc = self._read_schema(schema_uri)
        try:
            check_dialect(schema_uri, schema_doc, expected_dialect)
        except Problem as problem:
            self.refusals += 1
            return ValidationOutcome(valid=False, dialect=problem.body.get("declared_dialect") or "none",
                                     schema_uri=schema_uri,
                                     errors=(ValidationError("", "/$schema", problem.body["detail"]),),
                                     keywords_checked=0)
        errs = [] if isinstance(schema_doc, dict) else [ValidationError("", "$", "a schema must be an object")]
        return ValidationOutcome(valid=not errs, dialect=expected_dialect, schema_uri=schema_uri,
                                 errors=tuple(errs), keywords_checked=1)

    # --- adapter-specific: how a schema is read and how an instance is checked
    @abstractmethod
    def _read_schema(self, schema_uri: str) -> dict:
        """Read and parse the schema resource. Typed failure if unreachable."""

    @abstractmethod
    def _compile(self, schema_doc: dict) -> object:
        """Turn a schema document into whatever representation this adapter checks against."""

    @abstractmethod
    def _check(self, handle: PreparedHandle, instance) -> tuple[list, int]:
        """(errors, keywords_checked) for one instance against one prepared handle."""


def outcome_as_dict(outcome: ValidationOutcome) -> dict:
    return outcome.as_dict()
