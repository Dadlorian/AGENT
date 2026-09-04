#!/usr/bin/env python3
"""Tenancy: the mandatory principal every unit of work carries, checked at the
same choke points that already check identity, policy and budget.

Read it in this order. ScopeRequest is the whole caller vocabulary: an
operation (write, read, recall or spend), an actor, a key or query, and the
run context. There is no separate "tenant" field a caller fills in - the
principal rides on the actor, exactly as xc-tenancy's TenantScope shape fixes
(F-b4-03), and it is resolved once, at the same slot xc-enforcement-chain
names identity.resolve.

TenancyAdapter.admit() is a template method: resolve_scope() runs first and
unconditionally, so a unit with no principal is refused at entry before any
store, budget or index is touched (F-a6-05: no identity field anywhere in the
system today, so this is the first place one is required, not a filter added
to one that already existed). Only then does the requested operation run,
through one of four adapter-supplied primitives. No adapter can reorder this
or decline the entry check - admit() is concrete here, not overridden.

The two adapters differ on where the boundary is enforced (F-b1-04, the
differs_in_execution_model shape xc-tenancy-implement fixes):
  - adapters/dryrun.py:  one shared keyspace, a principal column filtered at
    read/recall/spend time. A dropped filter still returns the wrong
    principal's data - the deliberate breakage this harness exercises.
  - adapters/second.py:  one store instance per principal, selected before any
    read or write. A wrong or missing principal resolves no store at all, so
    there is no filter to drop.
Cross-tenant leak counters (cross_tenant_reads/recalls/spend) are therefore
computed by conformance.py from the corpus's actual outcomes, not
self-reported by an adapter that might itself be the thing under test.

No product name appears in this file (F-b1-02). Python 3.11 standard library
only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
_errors_path = _errors_os.path.join(
    _errors_os.path.dirname(_errors_os.path.abspath(__file__)), "..", "errors")
if _errors_path not in _errors_sys.path:
    _errors_sys.path.append(_errors_path)  # appended, never inserted at 0: this
    # harness's own adapters/ package must resolve before errors/adapters/ does
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) ----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "no-principal": (422, "Refused at entry: the unit carries no principal", False),
    "document-invalid": (422, "The scope request is not a well-formed request", False),
    "cross-tenant-denied": (403, "Refused: crossed a principal boundary", False),
    "budget-exceeded": (403, "This principal's own budget ceiling was exceeded", False),
    "adapter-unavailable": (503, "No store answered the scope request", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --- The caller vocabulary ---------------------------------------------------
# Closed, so there is no advisory field and no bypass (F-b1-08: the platform
# applies each cross-cutting guarantee; a caller cannot decline it).
ALLOWED = {"operation", "actor", "key", "value", "query", "amount_micros", "target_principal", "context"}
OPERATIONS = {"write", "read", "recall", "spend"}
CONTEXT_REQUIRED = {"run_id", "root_dispatch_id"}


@dataclass(frozen=True)
class ScopeRequest:
    operation: str
    actor: dict                 # {"id": ..., "principal": ...}; principal may be absent - that is the refusal
    context: dict
    key: str | None = None
    value: object = None
    query: str | None = None
    amount_micros: int | None = None
    target_principal: str | None = None   # spend only: who the spend is charged to, default the actor's own

    @classmethod
    def from_dict(cls, doc: dict) -> "ScopeRequest":
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a scope request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the scope request vocabulary; there is no advisory mode "
                          f"and no bypass on this path", rejected_fields=extra)
        if doc.get("operation") not in OPERATIONS:
            raise Problem("document-invalid", f"operation must be one of {sorted(OPERATIONS)}",
                          operation=doc.get("operation"))
        actor = doc.get("actor")
        if not isinstance(actor, dict) or not actor.get("id"):
            raise Problem("document-invalid", "actor must be an object naming at least id")
        context = doc.get("context")
        if not isinstance(context, dict):
            raise Problem("document-invalid", "context must be an object")
        missing = sorted(CONTEXT_REQUIRED - set(context))
        if missing:
            raise Problem("document-invalid", f"context is missing {missing}", missing=missing)
        op = doc["operation"]
        if op == "write" and (not doc.get("key") or "value" not in doc):
            raise Problem("document-invalid", "write requires key and value")
        if op == "read" and not doc.get("key"):
            raise Problem("document-invalid", "read requires key")
        if op == "spend" and not isinstance(doc.get("amount_micros"), int):
            raise Problem("document-invalid", "spend requires an integer amount_micros")
        return cls(op, actor, context, doc.get("key"), doc.get("value"), doc.get("query"),
                   doc.get("amount_micros"), doc.get("target_principal"))

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ScopeAssignmentRecord:
    """One record per admitted unit, appended rather than mutated - the shape
    xc-tenancy-implement's ScopeAssignmentRecord fixes."""
    run_id: str
    unit_id: str
    principal: str
    adapter: str          # read from the stamp the resolution produced, never from configuration
    operation: str
    resolved_at: str      # always "identity.resolve" - there is no second slot
    written_at: str


# --- The interface the core imports -----------------------------------------
class TenancyAdapter(ABC):
    """One scope API: resolve_scope (the entry gate) and admit (resolve, then
    perform the operation through one of four adapter-supplied primitives).

    resolve_scope and admit are concrete: no adapter decides whether to be
    asked for a principal, or in what order. An adapter supplies _write,
    _read, _recall and _spend and nothing else.
    """

    entity = "adapter"
    report_adapter = "unset"                              # the locus this binding reports as
    locus_of_the_tenant_boundary = "unset"
    failure_mode_of_a_wrong_or_missing_principal = "unset"
    provisioning_cost_of_a_new_principal = "unset"

    def __init__(self):
        self.journal: list[ScopeAssignmentRecord] = []

    @staticmethod
    def _now() -> str:
        base = os.environ.get("TENANCY_CLOCK")     # a fixed clock keeps a dry run deterministic
        now = datetime.fromisoformat(base) if base else datetime.now(timezone.utc)
        return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def resolve_scope(self, actor: dict) -> str:
        """The identity.resolve slot xc-tenancy's contract names: the principal
        travels on the actor xc-identity-delegation already binds. A unit whose
        actor resolves to no principal is refused here, before any store is
        touched - not admitted and filtered out later (F-a6-05, F-b4-03)."""
        principal = (actor or {}).get("principal")
        if not principal:
            raise Problem("no-principal",
                          "the actor carries no principal; a unit of work with no tenant is refused at "
                          "admission, before any read, write or spend was attempted",
                          actor=(actor or {}).get("id", "unknown"))
        return principal

    def admit(self, request: ScopeRequest) -> tuple[ScopeAssignmentRecord, object]:
        principal = self.resolve_scope(request.actor)     # always first; unconditional
        if request.operation == "write":
            outcome = self._write(principal, request.key, request.value, request.context)
        elif request.operation == "read":
            outcome = self._read(principal, request.key, request.context)
        elif request.operation == "recall":
            outcome = self._recall(principal, request.context)
        elif request.operation == "spend":
            target = request.target_principal or principal
            outcome = self._spend(principal, target, request.amount_micros, request.context)
        else:  # pragma: no cover - from_dict already closes the vocabulary
            raise Problem("document-invalid", f"operation {request.operation!r} is not in the vocabulary")
        record = ScopeAssignmentRecord(request.context["run_id"], str(uuid.uuid4()), principal,
                                       self.report_adapter, request.operation, "identity.resolve", self._now())
        self.journal.append(record)
        return record, outcome

    # --- reads the conformance run needs ------------------------------------
    def counters(self) -> dict:
        """units_checked, principals_covered and no_principal_admitted only.

        The cross_tenant_reads/recalls/spend counters xc-tenancy-implement's
        definition of done also names are measured by conformance.py from the
        corpus's actual outcomes - whether a deliberately cross-tenant attempt
        was refused or, under the breakage, silently admitted - never
        self-reported by the adapter that might itself be the thing broken.
        """
        principals = {r.principal for r in self.journal}
        return {"adapter": self.report_adapter,
                "units_checked": len(self.journal),
                "principals_covered": len(principals),
                "no_principal_admitted": sum(1 for r in self.journal if not r.principal)}

    # --- what an adapter supplies --------------------------------------------
    @abstractmethod
    def _write(self, principal: str, key: str, value, context: dict):
        """Append. A record with no principal never reaches here - resolve_scope refused it."""

    @abstractmethod
    def _read(self, principal: str, key: str, context: dict):
        """Return the value, or raise cross-tenant-denied. Never a redacted view."""

    @abstractmethod
    def _recall(self, principal: str, context: dict) -> list:
        """Return only what this principal wrote. Never a count that discloses another's."""

    @abstractmethod
    def _spend(self, principal: str, target_principal: str, amount_micros: int, context: dict) -> int:
        """Charge target_principal's own ceiling. Exceeding it terminates that principal's
        unit, never the platform's or another principal's remaining ceiling (F-b4-02)."""
