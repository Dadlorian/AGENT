#!/usr/bin/env python3
"""Tool access: a unit of work reaches tools published by anyone.

Read it in this order.

  ToolDescriptor      one catalogue entry. A name, an input schema, a declared
                      effect. `from_dict` is the meta-schema gate: a server that
                      publishes a tool with no schema publishes something this
                      interface cannot call, so the descriptor never enters a
                      catalogue and is counted as invalid instead (F-b3-09).
  Binding             what bind_server returns: a handle, the catalogue that was
                      read from the server at that moment, the declared surface
                      resolved against it, and the marker read back.
  CallContext         what the platform stamps around every call without the
                      caller asking: correlation, run, actor, idempotency key,
                      the protocol revision this call declares, the call ceiling
                      and the policy verdict (F-b4-01).
  ToolCallResult      what a call returns. `ok` false carries the problem object;
                      there is no third state to interpret.
  CatalogueHealth     a health answer that counts. Its vocabulary is serving /
                      empty / unreachable. There is no green (F-a6-03, F-a7-03).
  ToolAccessAdapter   the four operations the core imports - bind_server,
                      list_tools, call_tool, read_resource - plus begin_call,
                      claim and cancel, which are call_tool taken apart so a call
                      can be stopped while it is still in flight.

Two failure channels, kept apart on purpose. A refusal *raises* Problem: the
call never left the platform and no result exists. A tool that fails while doing
the work *returns* ToolCallResult(ok=False, problem=...): the call happened. A
tool reporting its own failure inside a successful envelope is mapped onto the
problem before the result leaves the adapter (F-b4-07).

Every gate runs before dispatch, in one order, in this file, so no adapter can
decline one (F-b4-04): revision, catalogue, declared surface, policy verdict,
arguments, idempotency, ceiling.

No product name, endpoint, transport or protocol method name appears here
(T-t7-02, F-part-c-09). Python 3.11 standard library only.
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

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

INTERFACE_VERSION = "0.1"

# The revision a call declares. Claimed, not verified: every record on file for
# this standard is a search result (X-cap-tool-access-001, X-cap-tool-access-002).
# It is declared per call rather than agreed once at bind (X-cross-structure-061).
DEFAULT_REVISION = "2026-07-28"

# --- Typed failures: RFC 9457 problem details (F-b4-07) ---------------------
# Proposed local registry. cap-errors owns the closed one; `policy-denied` is the
# registered type this boundary uses for an undeclared tool, because
# `tool-not-declared` is pending registration (cap-tool-access, shapes).
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "The published descriptor is not a tool this interface can call", False),
    "arguments-invalid": (422, "Arguments do not satisfy the tool's declared input schema", False),
    "policy-denied": (403, "The call was refused before anything was dispatched", False),
    "tool-unknown": (404, "No tool of that name is in this binding's catalogue", False),
    "tool-failed": (502, "The tool reported a failure while doing the work", False),
    "budget-exhausted": (402, "The call would cross the ceiling", False),
    "idempotency-conflict": (409, "Same idempotency key, different arguments", False),
    "protocol-unsupported": (400, "This call declares a protocol revision the server does not serve", False),
    "call-cancelled": (409, "The call was cancelled before it produced a result", False),
    "adapter-unavailable": (503, "No server serves this binding", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --- The published schema, checked before it is trusted ---------------------
# cap-document-validation owns the dialect and its validator (F-b3-09). What runs
# here is a declared subset of JSON Schema 2020-12 - type, properties, required,
# additionalProperties, enum, minLength, minimum, items - because a harness must
# not quietly become the platform's validator. The point being made is the order:
# the schema arrives from a server we may not control, so it is checked against
# the meta-schema before any argument is checked against it.
TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool,
         "array": list, "object": dict}
EFFECTS = ("read_only", "mutating", "unknown")


def check_schema(schema) -> None:
    """The meta-schema gate. Raises document-invalid for a schema we cannot use."""
    if not isinstance(schema, dict):
        raise Problem("document-invalid", "an input schema must be a JSON Schema object")
    if schema.get("type") != "object":
        raise Problem("document-invalid", "an input schema must declare type object")
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        raise Problem("document-invalid", "properties must be an object")
    for name, sub in props.items():
        if not isinstance(sub, dict) or sub.get("type") not in TYPES:
            raise Problem("document-invalid",
                          f"property {name!r} declares no type this subset validator supports")
    required = schema.get("required", [])
    if not isinstance(required, list) or any(r not in props for r in required):
        raise Problem("document-invalid", "required must list declared properties")


def check_arguments(schema: dict, args) -> None:
    """Arguments against the tool's declared input schema, before the call leaves."""
    if not isinstance(args, dict):
        raise Problem("arguments-invalid", "arguments must be an object")
    props, required = schema.get("properties", {}), schema.get("required", [])
    missing = [r for r in required if r not in args]
    if missing:
        raise Problem("arguments-invalid", f"missing required arguments {missing}", missing=missing)
    if schema.get("additionalProperties") is False:
        extra = sorted(set(args) - set(props))
        if extra:
            raise Problem("arguments-invalid", f"arguments {extra} are not declared by this tool",
                          rejected_arguments=extra)
    for name, value in args.items():
        sub = props.get(name)
        if sub is None:
            continue
        want = sub["type"]
        wrong = not isinstance(value, TYPES[want])
        if want in ("integer", "number") and isinstance(value, bool):
            wrong = True                       # a boolean is not a number here
        if wrong:
            raise Problem("arguments-invalid", f"argument {name!r} must be a {want}", argument=name)
        if "enum" in sub and value not in sub["enum"]:
            raise Problem("arguments-invalid", f"argument {name!r} must be one of {sub['enum']}", argument=name)
        if "minLength" in sub and len(value) < sub["minLength"]:
            raise Problem("arguments-invalid", f"argument {name!r} is shorter than {sub['minLength']}",
                          argument=name)
        if "minimum" in sub and value < sub["minimum"]:
            raise Problem("arguments-invalid", f"argument {name!r} is below {sub['minimum']}", argument=name)


# --- The caller vocabulary --------------------------------------------------
@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    input_schema: dict
    effect: str                 # read_only | mutating | unknown
    description: str = ""
    idempotent: bool = False

    @classmethod
    def from_dict(cls, doc) -> "ToolDescriptor":
        """The gate a published descriptor passes before it enters a catalogue."""
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a tool descriptor is an object")
        name = doc.get("name")
        if not isinstance(name, str) or not name:
            raise Problem("document-invalid", "a tool descriptor needs a non-empty name")
        if "input_schema" not in doc:
            raise Problem("document-invalid",
                          f"tool {name!r} publishes no input schema, so this interface cannot call it",
                          tool=name)
        check_schema(doc["input_schema"])
        effect = doc.get("effect", "unknown")
        if effect not in EFFECTS:
            raise Problem("document-invalid", f"tool {name!r} declares effect {effect!r}", tool=name)
        return cls(name, doc["input_schema"], effect, doc.get("description", ""),
                   bool(doc.get("idempotent", False)))


@dataclass(frozen=True)
class ResourceRead:
    """A read that changes nothing. Not a tool call, and never counted as one."""
    uri: str
    content: list
    mime_type: str = "text/plain"


@dataclass(frozen=True)
class CallContext:
    """What the platform stamps. A caller fills none of it in by hand."""
    correlation_id: str
    run_id: str
    actor: str
    idempotency_key: str
    protocol_revision: str = DEFAULT_REVISION
    ceiling_calls: int = 8
    policy_verdict: str = "allow"          # allow | allow-read-only


@dataclass
class Binding:
    handle: str
    server_marker: str                     # read back from the server, not from the binding
    revision: str
    catalogue: tuple                       # ToolDescriptor, discovered at bind time
    declared_surface: tuple                # the names this unit may call
    catalogue_digest: str
    resources: tuple = ()
    schemas_checked: int = 0               # for this binding, not for the process
    schemas_invalid: int = 0
    unresolved: tuple = ()                 # declared names this server does not publish

    def names(self) -> list:
        return [t.name for t in self.catalogue]


@dataclass
class CallHandle:
    """One call in flight. Terminal states: done, failed, cancelled."""
    call_id: str
    tool: str
    state: str                             # in_flight | done | failed | cancelled
    effect: str
    correlation_id: str
    polls: int = 0
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCallResult:
    tool: str
    ok: bool
    content: list
    correlation_id: str
    problem: dict | None = None


@dataclass(frozen=True)
class CancelAck:
    """Says which of two things happened, rather than promising a stop."""
    call_id: str
    outcome: str                           # stopped | recorded
    effect_owed: bool
    detail: str


@dataclass(frozen=True)
class CatalogueHealth:
    """A health answer that counts. There is no green in this vocabulary."""
    status: str                            # serving | empty | unreachable
    tools_listed: int
    schemas_checked: int
    schemas_invalid: int
    resources_listed: int
    revision: str
    server_marker: str
    detail: str


def digest(doc) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(doc, sort_keys=True, default=str).encode()).hexdigest()


# --- The interface the core imports -----------------------------------------
class ToolAccessAdapter(ABC):
    """Four operations the core imports, plus the three a cancellable call needs.

    Concrete here so no adapter can decline them: the meta-schema check on every
    published descriptor, the declared-surface refusal, the policy verdict, the
    argument check, the idempotency replay, the call ceiling, and the mapping of
    an in-band tool failure onto the problem object.
    """

    entity = "adapter"
    server_marker = "unset"
    supported_revisions: tuple = (DEFAULT_REVISION,)
    # The two axes build-adapter-pair requires this pair to differ on.
    catalogue_authority = "registered-here"     # registered-here | published-elsewhere
    call_locality = "co-located"                # co-located | remote
    # Two more the swap report reads, so a same-shape second adapter is visible.
    catalogue_stability = "frozen"              # frozen | re-read-at-every-bind
    cancellation = "recorded"                   # stopped | recorded
    declared_gaps: tuple = ()
    # Which discovered tool the conformance run exercises for each role. Names,
    # not shapes: the suite still reads the descriptor and builds its arguments
    # from the published schema, so nothing here is hard-wired to one server.
    conformance_roles = {"read_only": "notes.read", "mutating": "notes.append",
                         "slow": "notes.scan", "in_band_failure": "notes.flaky"}

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.dispatches = 0          # incremented only when adapter code is reached
        self.refusals = 0
        self.tool_calls = 0
        self.resource_reads = 0
        self.schemas_checked = 0
        self.schemas_invalid = 0
        self.undeclared_refused = 0
        self.binds = 0
        self.observed_marker = ""
        self._by_key: dict[str, tuple[str, CallHandle]] = {}
        self._calls_by_run: dict[str, int] = {}      # the ceiling attaches to a run, not to a process

    # 1. bind_server -----------------------------------------------------
    def bind_server(self, server_ref: str, declared_surface, ctx: CallContext) -> Binding:
        """Read the catalogue from the server, check every schema, resolve the surface."""
        self._revision(ctx)
        raw, marker, resources = self._open(server_ref, ctx)
        catalogue, invalid = [], 0
        for doc in raw:
            try:
                catalogue.append(ToolDescriptor.from_dict(doc))
            except Problem:
                invalid += 1                      # published, but not callable through this interface
        self.schemas_checked += len(catalogue)
        self.schemas_invalid += invalid
        self.binds += 1
        self.observed_marker = marker
        names = [t.name for t in catalogue]
        # The declared surface is resolved here, at bind time. A name the server
        # does not publish is recorded rather than raised, because the binding
        # itself is fine - the endpoint answered and authenticated - and calling
        # that name is refused before any call is made. An endpoint that is live
        # and authenticated with nothing registered is a binding whose whole
        # surface is unresolved, which is the state to report, not to hide
        # behind an exception (F-a6-03).
        unresolved = tuple(n for n in declared_surface if n not in names)
        return Binding(handle="bind-" + digest([server_ref, sorted(names)])[7:23],
                       server_marker=marker, revision=ctx.protocol_revision,
                       catalogue=tuple(catalogue), declared_surface=tuple(declared_surface),
                       catalogue_digest=digest([[t.name, t.effect, t.input_schema] for t in catalogue]),
                       resources=tuple(resources), schemas_checked=len(catalogue),
                       schemas_invalid=invalid, unresolved=unresolved)

    # 2. list_tools ------------------------------------------------------
    def list_tools(self, binding: Binding) -> list:
        """The catalogue, as data read at bind time. Never generated at build time."""
        return list(binding.catalogue)

    def find(self, binding: Binding, name: str) -> ToolDescriptor:
        for tool in binding.catalogue:
            if tool.name == name:
                return tool
        raise Problem("tool-unknown", f"{name!r} is not in this binding's catalogue {binding.names()}",
                      tool=name)

    def check_arguments(self, tool: ToolDescriptor, args) -> None:
        """The caller-visible pre-check. begin_call runs it again regardless."""
        check_arguments(tool.input_schema, args)

    # 3. call_tool -------------------------------------------------------
    def call_tool(self, binding: Binding, name: str, args: dict, ctx: CallContext,
                  max_polls: int = 16) -> ToolCallResult:
        handle = self.begin_call(binding, name, args, ctx)
        return self.claim(handle, max_polls)

    def begin_call(self, binding: Binding, name: str, args: dict, ctx: CallContext) -> CallHandle:
        """Every gate, in one order, before anything is dispatched (F-b4-04)."""
        self._revision(ctx)                                            # declared per call
        tool = self.find(binding, name)                                # 404 if not published
        if name not in binding.declared_surface:                       # 403, the policy gate
            self.refusals += 1
            self.undeclared_refused += 1
            raise Problem("policy-denied",
                          f"called {name!r}; declared surface is {list(binding.declared_surface)}",
                          rule_id="declared-surface", tool=name,
                          enforcement_point="platform-pre-dispatch")
        if ctx.policy_verdict == "allow-read-only" and tool.effect != "read_only":
            self.refusals += 1
            raise Problem("policy-denied",
                          f"the policy verdict allows read-only tools and {name!r} declares effect "
                          f"{tool.effect!r}; nothing was dispatched",
                          rule_id="read-only-verdict", tool=name,
                          enforcement_point="platform-pre-dispatch")
        self.check_arguments(tool, args)                               # 422 against the published schema
        key_digest = digest([name, args])
        seen = self._by_key.get(ctx.idempotency_key)
        if seen is not None:
            if seen[0] != key_digest:
                self.refusals += 1
                raise Problem("idempotency-conflict",
                              f"key {ctx.idempotency_key} was used with different arguments",
                              idempotency_key=ctx.idempotency_key)
            return seen[1]                                             # a replay is free
        spent = self._calls_by_run.get(ctx.run_id, 0)
        if spent >= ctx.ceiling_calls:
            self.refusals += 1
            raise Problem("budget-exhausted",
                          f"run {ctx.run_id} has made {spent} tool calls and the ceiling is "
                          f"{ctx.ceiling_calls}; the call was not dispatched",
                          ceiling_calls=ctx.ceiling_calls, calls_made=spent,
                          enforcement_point="platform-pre-dispatch")
        self.dispatches += 1
        self.tool_calls += 1
        self._calls_by_run[ctx.run_id] = spent + 1
        handle = self._begin(binding, tool, args, ctx)
        self._by_key[ctx.idempotency_key] = (key_digest, handle)
        return handle

    def claim(self, handle: CallHandle, max_polls: int = 16) -> ToolCallResult:
        """Poll until terminal, then map an in-band failure onto the problem object."""
        while handle.state == "in_flight" and handle.polls < max_polls:
            handle.polls += 1
            self._poll(handle)
        if handle.state == "cancelled":
            raise Problem("call-cancelled", f"call {handle.call_id} was cancelled before it produced a result",
                          tool=handle.tool)
        if handle.state == "in_flight":
            raise Problem("adapter-unavailable", f"call {handle.call_id} did not settle in {max_polls} polls",
                          tool=handle.tool, retry_after_s=30)
        payload = handle.payload
        if handle.state == "failed" or payload.get("is_error"):
            # The second failure channel: a tool reporting its own failure inside
            # an otherwise successful envelope. Mapped here, not handed on as text.
            problem = Problem("tool-failed",
                              f"{handle.tool} reported: {payload.get('error', 'no detail')}",
                              tool=handle.tool, correlation_id=handle.correlation_id,
                              channel="tool-result").body
            return ToolCallResult(handle.tool, False, [], handle.correlation_id, problem)
        return ToolCallResult(handle.tool, True, list(payload.get("content", [])), handle.correlation_id)

    def cancel(self, handle: CallHandle) -> CancelAck:
        """Says which of two things happened while the call was still in flight."""
        if handle.state != "in_flight":
            return CancelAck(handle.call_id, "recorded", False,
                             f"the call was already {handle.state} when the cancel arrived")
        ack = self._cancel(handle)
        handle.state = "cancelled"
        return ack

    # 4. read_resource ---------------------------------------------------
    def read_resource(self, binding: Binding, uri: str, ctx: CallContext) -> ResourceRead:
        """A read changes nothing, so it spends no call ceiling and no idempotency key."""
        self._revision(ctx)
        self.resource_reads += 1
        return self._read(binding, uri, ctx)

    # health -------------------------------------------------------------
    def health(self, binding: Binding) -> CatalogueHealth:
        """Counts registered tools. A live, authenticated, empty server is `empty`."""
        listed = len(binding.catalogue)
        status = "serving" if listed else "empty"
        detail = (f"{listed} tools registered, {binding.schemas_checked} schemas checked, "
                  f"{binding.schemas_invalid} invalid") if listed else \
            "the binding is open and authenticated and the server publishes no tool at all"
        return CatalogueHealth(status, listed, binding.schemas_checked, binding.schemas_invalid,
                               len(binding.resources), binding.revision, binding.server_marker, detail)

    def axes(self) -> dict:
        """What a swap report compares. Not caller-visible."""
        return {"entity": self.entity, "catalogue_authority": self.catalogue_authority,
                "call_locality": self.call_locality, "catalogue_stability": self.catalogue_stability,
                "cancellation": self.cancellation, "declared_gaps": list(self.declared_gaps)}

    def _revision(self, ctx: CallContext) -> None:
        """Declared per call, refused on that call, with the binding left usable."""
        if ctx.protocol_revision not in self.supported_revisions:
            self.refusals += 1
            raise Problem("protocol-unsupported",
                          f"this call declares revision {ctx.protocol_revision} and this server serves "
                          f"{list(self.supported_revisions)}; the binding is unaffected",
                          declared_revision=ctx.protocol_revision,
                          served_revisions=list(self.supported_revisions))

    # --- what an adapter implements -------------------------------------
    @abstractmethod
    def _open(self, server_ref: str, ctx: CallContext) -> tuple:
        """-> (raw tool descriptors, marker read back from the server, resource uris)."""

    @abstractmethod
    def _begin(self, binding: Binding, tool: ToolDescriptor, args: dict, ctx: CallContext) -> CallHandle:
        """Dispatch. Reached only after every gate above has held."""

    @abstractmethod
    def _poll(self, handle: CallHandle) -> None:
        """Advance one in-flight call, setting state and payload when it settles."""

    @abstractmethod
    def _cancel(self, handle: CallHandle) -> CancelAck:
        """Stop it, or record that it could not be stopped. Never claim both."""

    @abstractmethod
    def _read(self, binding: Binding, uri: str, ctx: CallContext) -> ResourceRead:
        """Read-only data for context."""


def result_as_dict(result: ToolCallResult) -> dict:
    """The caller-visible view. Nothing here names a server, product or transport."""
    doc = asdict(result)
    return {k: v for k, v in doc.items() if v is not None}
