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
           "max_output_tokens", "deadline",
           # Mechanisms beyond a plain completion (X-maturity-b-001, X-maturity-b-002):
           # every one of these is optional and defaults to the plain-completion
           # behaviour above, so a caller that sends none of them is unaffected.
           "stream", "tools", "response_schema", "cache", "reasoning_effort"}
REQUIRED = {"model_class", "messages", "idempotency_key", "ceiling_micros"}
ROLES = {"system", "user", "assistant", "tool"}
REASONING_EFFORTS = ("none", "low", "medium", "high")
REASONING_BUDGET = {"none": 0, "low": 16, "medium": 48, "high": 112}  # reasoning tokens, counted in cost
CACHE_DIRECTIVES = ("ephemeral",)


@dataclass(frozen=True)
class CompletionRequest:
    model_class: str
    messages: list
    idempotency_key: str
    ceiling_micros: int
    max_output_tokens: int = 256
    deadline: str | None = None
    stream: bool = False
    tools: list | None = None
    response_schema: dict | None = None
    cache: str | None = None
    reasoning_effort: str = "none"

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
        stream = doc.get("stream", False)
        if not isinstance(stream, bool):
            raise Problem("document-invalid", "stream must be a boolean")
        tools = doc.get("tools")
        if tools is not None:
            if not isinstance(tools, list) or not tools:
                raise Problem("document-invalid", "tools must be a non-empty array")
            for i, t in enumerate(tools):
                if not isinstance(t, dict) or not isinstance(t.get("name"), str) or not t["name"]:
                    raise Problem("document-invalid", f"tools[{i}] needs a string name")
                if "parameters" in t and not isinstance(t["parameters"], dict):
                    raise Problem("document-invalid", f"tools[{i}].parameters must be an object schema")
        schema = doc.get("response_schema")
        if schema is not None:
            if not isinstance(schema, dict) or schema.get("type") != "object" \
                    or not isinstance(schema.get("properties", {}), dict):
                raise Problem("document-invalid",
                              "response_schema must be an object schema with a properties map")
        cache = doc.get("cache")
        if cache is not None and cache not in CACHE_DIRECTIVES:
            raise Problem("document-invalid", f"cache must be one of {CACHE_DIRECTIVES}", cache=cache)
        reasoning_effort = doc.get("reasoning_effort", "none")
        if reasoning_effort not in REASONING_EFFORTS:
            raise Problem("document-invalid", f"reasoning_effort must be one of {REASONING_EFFORTS}",
                          reasoning_effort=reasoning_effort)
        return cls(klass, msgs, doc["idempotency_key"], ceiling, mot, doc.get("deadline"),
                   stream, tools, schema, cache, reasoning_effort)

    def digest(self) -> str:
        body = {k: v for k, v in asdict(self).items() if k != "idempotency_key"}
        return "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class CompletionResult:
    """The usage record every adapter returns, whichever mechanism was used.

    tokens_in is the prompt total (a cache hit is a subset of it, in
    cached_tokens); tokens_out is the completion total (a reasoning turn is a
    subset of it, in reasoning_tokens) - the same split providers name
    differently in their own usage objects (no governing standard unifies
    them; this is the one shape both adapters answer through - see the
    Adapters section of this capability's skill for which provider fields
    these stand in for). Reasoning tokens are already inside tokens_out, so
    cost_micros (priced from tokens_in + tokens_out) counts them without a
    separate line item.
    """
    text: str
    cost_micros: int
    tokens_in: int
    tokens_out: int
    cost_status: str  # committed | reconciled
    cached_tokens: int = 0        # subset of tokens_in that was a cache hit, not a directive that was set
    reasoning_tokens: int = 0     # subset of tokens_out spent on hidden reasoning, counted in cost
    tool_calls: list | None = None       # a tool-call turn: the model asked for a tool instead of answering
    structured_output: dict | None = None  # present, and schema-conformant, when response_schema was set
    stream_chunks: list | None = None      # >1 chunks whose join equals text, present only when stream was set


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


# --- Mechanisms beyond a plain completion, shared by every non-live adapter --
# (X-maturity-b-001, X-maturity-b-002). One synthesis function so a dry-run and
# a batch adapter answer the same schema-validated, cache-accounted, reasoning-
# accounted shape from two different execution models, rather than each
# reimplementing (and drifting on) the same five mechanisms.
def _type_ok(kind: str, value) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "array":
        return isinstance(value, list)
    if kind == "object":
        return isinstance(value, dict)
    return True


def schema_conforms(schema: dict, value) -> bool:
    """Minimal JSON Schema 2020-12 conformance check: type, required, properties,
    items - enough to prove structured output was actually constrained by the
    schema, never enough to be mistaken for a general validator."""
    if not isinstance(schema, dict):
        return True
    kind = schema.get("type")
    if kind and not _type_ok(kind, value):
        return False
    if kind == "object" and isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                return False
        for name, sub in schema.get("properties", {}).items():
            if name in value and not schema_conforms(sub, value[name]):
                return False
    if kind == "array" and isinstance(value, list):
        items = schema.get("items")
        if items:
            return all(schema_conforms(items, v) for v in value)
    return True


def synthesize_from_schema(schema: dict, seed: str) -> dict:
    """A deterministic value that conforms to `schema` - filled from a seed, not
    invented per call, so a run is reproducible bytes like the rest of this
    adapter."""
    def value(sub: dict, s: str):
        kind = sub.get("type", "string")
        h = hashlib.sha256(s.encode()).hexdigest()
        if kind == "integer":
            return int(h[:4], 16) % 1000
        if kind == "number":
            return round((int(h[:4], 16) % 1000) / 10, 1)
        if kind == "boolean":
            return int(h[0], 16) % 2 == 0
        if kind == "array":
            return []
        if kind == "object":
            return {k: value(v, s + k) for k, v in sub.get("properties", {}).items()}
        return h[:12]

    props = schema.get("properties", {})
    required = schema.get("required") or list(props)
    return {name: value(props.get(name, {"type": "string"}), seed + name) for name in required}


def apply_mechanisms(request: CompletionRequest, seed: str, cache_hit: bool,
                     base_text: str, base_tokens_out: int) -> dict:
    """Turn a plain-completion (base_text, base_tokens_out) into what every
    mechanism the request asked for actually produces, verified from the
    fields it returns rather than from the request being merely accepted.

    A request with none of stream/tools/response_schema/cache/reasoning_effort
    set returns base_text and base_tokens_out unchanged - this only ever adds
    to the plain-completion behaviour, never changes it.
    """
    tokens_in = estimate_tokens_in(request)
    last = request.messages[-1]
    text, tool_calls, structured_output = base_text, None, None

    if last.get("role") == "tool":
        # Second turn of a tool-call round trip: the caller supplied the tool's
        # own result, and the completion that follows has to show it was used.
        text = f"{base_text} | tool result incorporated: {str(last.get('content', ''))[:60]}"
    elif request.tools and last.get("role") == "user" and str(last.get("content", "")).startswith("tool:"):
        # First turn: the model defers to a tool instead of answering directly.
        rest = last["content"][len("tool:"):].strip()
        parts = rest.split(" ", 1)
        name = parts[0] if parts else ""
        tool = next((t for t in request.tools if t.get("name") == name), None)
        if tool is not None:
            params = tool.get("parameters")
            args = synthesize_from_schema(params, seed + name) if params else \
                {"query": parts[1] if len(parts) > 1 else ""}
            tool_calls = [{"id": "call-" + seed[:8], "name": name, "arguments": args}]
            text = ""

    if request.response_schema:
        structured_output = synthesize_from_schema(request.response_schema, seed)
        if not text:
            text = json.dumps(structured_output, sort_keys=True)

    reasoning_tokens = REASONING_BUDGET.get(request.reasoning_effort, 0)
    visible_tokens = base_tokens_out if text == base_text else max(1, len(text) // 4 or 1)
    tokens_out = min(request.max_output_tokens, visible_tokens + reasoning_tokens)
    reasoning_tokens = min(reasoning_tokens, max(0, tokens_out - 1))

    stream_chunks = None
    if request.stream and text:
        stream_chunks = [text[i:i + 8] for i in range(0, len(text), 8)] or [text]

    # A cache hit is observed against a store, never assumed from the directive
    # being set: cached_tokens is nonzero only when this exact prompt digest was
    # already seen with a cache directive on it.
    cached_tokens = tokens_in if (request.cache and cache_hit) else 0

    return {"text": text, "tool_calls": tool_calls, "structured_output": structured_output,
            "tokens_in": tokens_in, "tokens_out": tokens_out, "reasoning_tokens": reasoning_tokens,
            "stream_chunks": stream_chunks, "cached_tokens": cached_tokens}


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
        self._cache_digests: set[str] = set()   # prompt digests seen under a cache directive

    def note_cache(self, request: CompletionRequest) -> bool:
        """True if this exact request (minus idempotency_key) was already seen
        under a cache directive - a cache hit read back from a store, never
        assumed because the directive was set. Records the digest either way,
        so a first sighting is a cold cache and a repeat is a hit."""
        if not request.cache:
            return False
        digest = request.digest()
        hit = digest in self._cache_digests
        self._cache_digests.add(digest)
        return hit

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
