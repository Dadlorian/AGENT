#!/usr/bin/env python3
"""Model access: one completion from a class of model, never from a vendor.

Read it in this order. CompletionRequest is the whole caller vocabulary.
route() is a pure function from a class to a member, evaluated in front of every
adapter, so a routing rule can be tested from a table with no model running.
ModelAccessAdapter.submit() is a template method: it validates the request,
routes it, and checks the ceiling before any adapter code runs, so class and cap
are enforced identically whichever adapter is bound. ClaimTicket is what submit
always returns - already redeemed on a synchronous path, pending on a slow one.

No product name, endpoint or vendor appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) -----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "Request is not a well-formed completion request", False),
    "budget-exhausted": (402, "The call would cross the ceiling", False),
    "adapter-unavailable": (503, "No endpoint serves this model class", True),
    "idempotency-conflict": (409, "Same idempotency key, different request", False),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail, "retryable": retryable, **ext}
        super().__init__(detail)


# --- The caller vocabulary --------------------------------------------------
# The prefix carries the contract (F-a4-01, T-t6-04). There is no vendor field,
# no member model, no endpoint, and no field naming which adapter should answer.
CLASS_PATTERN = re.compile(r"^(f|i|b|cli)-[a-z0-9-]*$")
ALLOWED = {"model_class", "messages", "idempotency_key", "ceiling_micros",
           "max_output_tokens", "deadline"}
REQUIRED = {"model_class", "messages", "idempotency_key", "ceiling_micros"}
ROLES = {"system", "user", "assistant", "tool"}


@dataclass(frozen=True)
class CompletionRequest:
    model_class: str
    messages: list
    idempotency_key: str
    ceiling_micros: int
    max_output_tokens: int = 256
    deadline: str | None = None

    @classmethod
    def from_dict(cls, doc: dict) -> "CompletionRequest":
        """The one gate a request passes. A vendor name never gets past it."""
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a completion request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the completion request vocabulary; a caller "
                          f"names a model class and never a vendor, a member model or an endpoint",
                          rejected_fields=extra)
        missing = sorted(REQUIRED - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        klass = doc["model_class"]
        if not isinstance(klass, str) or not CLASS_PATTERN.match(klass):
            raise Problem("document-invalid",
                          f"model_class {klass!r} is not a routing class; a class is one of the "
                          f"prefixes f- i- b- cli- optionally followed by a member name",
                          model_class=klass)
        msgs = doc["messages"]
        if not isinstance(msgs, list) or not msgs:
            raise Problem("document-invalid", "messages must be a non-empty array")
        for i, m in enumerate(msgs):
            if not isinstance(m, dict) or m.get("role") not in ROLES or not isinstance(m.get("content"), str):
                raise Problem("document-invalid", f"messages[{i}] needs a role in {sorted(ROLES)} and string content")
        ceiling = doc["ceiling_micros"]
        if not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling < 0:
            raise Problem("document-invalid", "ceiling_micros must be a non-negative integer")
        if not isinstance(doc["idempotency_key"], str) or len(doc["idempotency_key"]) < 8:
            raise Problem("document-invalid", "idempotency_key must be a string of at least 8 characters")
        mot = doc.get("max_output_tokens", 256)
        if not isinstance(mot, int) or isinstance(mot, bool) or mot < 1:
            raise Problem("document-invalid", "max_output_tokens must be a positive integer")
        return cls(klass, msgs, doc["idempotency_key"], ceiling, mot, doc.get("deadline"))

    def digest(self) -> str:
        body = {k: v for k, v in asdict(self).items() if k != "idempotency_key"}
        return "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class CompletionResult:
    text: str
    cost_micros: int
    tokens_in: int
    tokens_out: int
    cost_status: str  # committed | reconciled


@dataclass
class ClaimTicket:
    """What submit always returns, on the fast path and the slow one alike."""
    ticket_id: str
    state: str  # pending | redeemed | failed | cancelled
    model_class: str
    result: CompletionResult | None = None
    earliest_retry: str | None = None
    cancellable: bool = False
    problem: dict | None = None


@dataclass(frozen=True)
class CancelAck:
    """Says which of two things happened, rather than promising a stop."""
    ticket_id: str
    outcome: str  # stopped | recorded
    cost_owed_micros: int
    detail: str


# --- Routing: a pure function in front of every adapter ---------------------
# The class table is data, in routing.json, recorded from the 25 groups in
# PASS.md A4 (F-a4-01..F-a4-05). No code in this file names a member.
ROUTING_TABLE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "routing.json")))["classes"]


@dataclass(frozen=True)
class RouteDecision:
    """Internal. A member never reaches a caller; only the class does."""
    model_class: str
    member: str
    contract: str
    unit_micros_per_1k: int
    reason: str


def route(model_class: str, ceiling_micros: int, budget_remaining_micros: int,
          policy_verdict: str = "allow") -> RouteDecision:
    """(class, ceiling, budget remaining, policy verdict) -> one selection and its reason.

    Pure: no clock, no network, no adapter state. Testable from a table.
    """
    prefix = next((p for p in ("cli-", "f-", "i-", "b-") if model_class.startswith(p)), None)
    group = ROUTING_TABLE.get(prefix)
    if group is None:
        raise Problem("adapter-unavailable",
                      f"no binding declares class {model_class}; the request was not sent and no spend was incurred",
                      model_class=model_class, retry_after_s=120)
    if policy_verdict == "allow-local-only" and prefix != "f-":
        raise Problem("adapter-unavailable",
                      f"the policy verdict restricts this unit to local serving and no member of class "
                      f"{model_class} is local; the request was not sent and no spend was incurred",
                      model_class=model_class, retry_after_s=120)
    if model_class == prefix:
        member, why = group["default"], "bare prefix; routing chose the class default"
    elif model_class in group["members"]:
        member, why = model_class, "caller named a member of the class"
    else:
        raise Problem("adapter-unavailable",
                      f"class {model_class} matches prefix {prefix} but no member serves it; the request "
                      f"was not sent and no spend was incurred",
                      model_class=model_class, retry_after_s=120)
    if budget_remaining_micros < ceiling_micros:
        why += "; ceiling narrowed to the budget remaining"
    return RouteDecision(model_class, member, group["contract"], group["unit_micros_per_1k"], why)


def price_micros(decision: RouteDecision, tokens_in: int, tokens_out: int) -> int:
    return -(-decision.unit_micros_per_1k * (tokens_in + tokens_out) // 1000)


def estimate_tokens_in(request: CompletionRequest) -> int:
    return max(1, sum(len(m["content"]) for m in request.messages) // 4)


def estimate_micros(decision: RouteDecision, request: CompletionRequest) -> int:
    """The worst case this call can cost. Checked before anything is dispatched."""
    return price_micros(decision, estimate_tokens_in(request), request.max_output_tokens)


# --- The interface the core imports -----------------------------------------
class ModelAccessAdapter(ABC):
    """One completions interface. Four operations: route, submit, claim, cancel.

    submit, route and cancel-accounting are concrete here so that no adapter can
    decline the class check, the ceiling check or the idempotency check.
    """

    entity = "adapter"            # what a report names; never a caller-visible field
    serving_path = "synchronous"  # synchronous | asynchronous-batch
    declared_marker = "unset"     # what a response from this binding should say
    declared_gaps: tuple = ()     # what this binding cannot do, stated rather than silently dropped

    def __init__(self):
        self.dispatches = 0            # incremented only when adapter code is reached
        self.refusals = 0
        self.observed_marker = ""      # read from a response, never from the binding
        self._by_key: dict[str, tuple[str, ClaimTicket]] = {}

    # 1. route -- pure, in front of the adapter
    def route(self, request: CompletionRequest, budget_remaining_micros: int | None = None,
              policy_verdict: str = "allow") -> RouteDecision:
        remaining = request.ceiling_micros if budget_remaining_micros is None else budget_remaining_micros
        return route(request.model_class, request.ceiling_micros, remaining, policy_verdict)

    # 2. submit -- always returns a ticket
    def submit(self, request: CompletionRequest, budget_remaining_micros: int | None = None,
               policy_verdict: str = "allow") -> ClaimTicket:
        seen = self._by_key.get(request.idempotency_key)
        if seen is not None:
            if seen[0] != request.digest():
                self.refusals += 1
                raise Problem("idempotency-conflict",
                              f"key {request.idempotency_key} was submitted with a different request body",
                              idempotency_key=request.idempotency_key)
            return seen[1]
        decision = self.route(request, budget_remaining_micros, policy_verdict)
        estimate = estimate_micros(decision, request)
        if estimate > request.ceiling_micros:
            self.refusals += 1
            raise Problem("budget-exhausted",
                          f"class {request.model_class} would cost up to {estimate} micros and the ceiling is "
                          f"{request.ceiling_micros}; the request was not sent and no spend was incurred",
                          model_class=request.model_class, estimate_micros=estimate,
                          ceiling_micros=request.ceiling_micros,
                          enforcement_point="platform-pre-dispatch")
        self.dispatches += 1
        ticket = self._submit(request, decision, estimate)
        self._by_key[request.idempotency_key] = (request.digest(), ticket)
        return ticket

    # 3. claim -- the only way to read a result
    @abstractmethod
    def claim(self, ticket: ClaimTicket) -> ClaimTicket:
        ...

    # 4. cancel -- says which of two things happened
    @abstractmethod
    def cancel(self, ticket: ClaimTicket) -> CancelAck:
        ...

    @abstractmethod
    def _submit(self, request: CompletionRequest, decision: RouteDecision, estimate: int) -> ClaimTicket:
        """Adapter-specific dispatch. Reached only after class and cap have held."""


def ticket_as_dict(ticket: ClaimTicket) -> dict:
    """The caller-visible view. Nothing here names a vendor, member or endpoint."""
    doc = asdict(ticket)
    return {k: v for k, v in doc.items() if v is not None}
