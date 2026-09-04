#!/usr/bin/env python3
"""The Isolation capability interface, and the Agent runtime operations one
contained unit serves. Shapes and one abstract adapter class - nothing else.

No product name appears in this file. Read it in this order: the declaration a
caller may write, the report the host asserts about the unit, the turn shapes,
the closed problem registry, then the adapter class every containment
technology implements.

Standard: OCI Runtime Spec for containment (unverified), Agent Client Protocol
for the turn (unverified). Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Mapping, Optional, Sequence

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry ---------------
PROBLEM_BASE = "urn:agentic:problem:"
PROBLEM_REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "The declaration or request is malformed", False),
    "isolation-unavailable": (503, "No isolation adapter could admit the unit", True),
    "runtime-unavailable": (503, "No agent runtime could serve the turn", True),
    "budget-exhausted": (402, "The unit would cross its ceiling", False),
    "isolation-operation-unsupported": (501,
        "This adapter does not serve this sandbox lifecycle operation", False),
}


class Problem(Exception):
    """A failure a caller branches on without parsing prose."""

    def __init__(self, suffix: str, detail: str, **ext: Any) -> None:
        status, title, retryable = PROBLEM_REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail, "retryable": retryable, **ext}
        super().__init__(detail)


# --- What a caller may say about containment ---------------------------------
@dataclass(frozen=True)
class IsolationDeclaration:
    """Declared resources and declared egress. Never a machine description.

    `profile` is a name the adapter resolves; a set of numbers, boot arguments,
    a block-device layout or a guest kernel would pin this interface to one
    containment technology, so `from_dict` refuses any field not listed here.
    """
    profile: str
    egress: str = "none"                       # "none" | "allowlist"
    egress_allowlist: Sequence[str] = ()
    credentials: str = "broker_only"           # const: no real secret enters the unit

    FIELDS = ("profile", "egress", "egress_allowlist", "credentials")

    @classmethod
    def from_dict(cls, doc: Mapping[str, Any]) -> "IsolationDeclaration":
        extra = [k for k in doc if k not in cls.FIELDS]
        if extra:
            raise Problem("document-invalid",
                          f"declaration carries fields that describe a machine, not a resource "
                          f"declaration: {sorted(extra)}")
        if not doc.get("profile"):
            raise Problem("document-invalid", "declaration is missing required property 'profile'")
        if doc.get("egress", "none") not in ("none", "allowlist"):
            raise Problem("document-invalid", f"egress must be none or allowlist, got {doc.get('egress')!r}")
        if doc.get("egress", "none") == "allowlist" and not doc.get("egress_allowlist"):
            raise Problem("document-invalid",
                          "egress=allowlist with an empty list is a malformed declaration, not an open unit")
        if doc.get("credentials", "broker_only") != "broker_only":
            raise Problem("document-invalid", "credentials is a const: broker_only")
        return cls(profile=doc["profile"], egress=doc.get("egress", "none"),
                   egress_allowlist=tuple(doc.get("egress_allowlist", ())),
                   credentials=doc.get("credentials", "broker_only"))


@dataclass(frozen=True)
class UnitContext:
    """The stamps the platform applies around every unit. A caller asks for none of them.

    Every field here is read - not merely carried - by a guarantee at each of
    admission, dispatch and a capability call: see context_guarantees.py,
    wired the same way into every adapter (dryrun, second, live). C01-F.
    """
    correlation_id: str
    run_id: str
    actor: str
    idempotency_key: str
    ceiling_s: float          # wall-clock ceiling enforced outside the unit


@dataclass(frozen=True)
class AdmissionHandle:
    """What admit returns. Nothing here names a containment technology."""
    unit_id: str
    profile: str
    context: UnitContext


# --- What the host asserts about the unit, from outside it -------------------
@dataclass(frozen=True)
class ContainmentReport:
    observed_from: str                 # "host". A unit never reports on its own containment.
    jail_mode: str                     # octal mode of the unit's own directory, e.g. "0700"
    owner_in_host_passwd: bool         # false is the passing value
    egress_attempts_made: int
    egress_attempts_blocked: int
    secrets_seen_inside: int           # must be 0
    containment_marker: str            # read from the running unit, not from the binding


@dataclass(frozen=True)
class SnapshotHandle:
    """What pause returns: a checkpoint of a unit's memory and filesystem state,
    never the unit itself. `state_digest` is the digest a resume (or a fork off
    this snapshot) must reproduce before any further syscall runs."""
    snapshot_id: str
    unit_id: str
    state_digest: str


@dataclass(frozen=True)
class UnitResult:
    """Returned by terminate, in the same shape whether the stop was requested or forced."""
    exit_status: int
    output_digest: str
    wall_seconds: float
    egress_attempts_made: int
    egress_attempts_blocked: int
    stop: str                          # "requested" | "forced"


# --- One prompt turn ---------------------------------------------------------
STOP_REASONS = ("end_turn", "cancelled", "cancel_timeout", "terminated")


@dataclass(frozen=True)
class SessionCapabilities:
    """Every member defaults to false, so nothing interactive is a precondition."""
    streaming: bool = False
    permission_callbacks: bool = False
    cancellation: bool = False


@dataclass(frozen=True)
class Session:
    session_id: str
    unit_id: str
    negotiated: SessionCapabilities
    runtime_marker: str                # emitted by the running adapter at session open


@dataclass(frozen=True)
class TurnRequest:
    prompt: str                        # the task, never the criterion the result is judged against
    op_seconds: float                  # how long the tool call inside the turn runs
    grace_s: float                     # per-request cancel grace window


@dataclass(frozen=True)
class TurnFrame:
    seq: int
    kind: str                          # "update" | "terminal"
    text: str = ""
    stop_reason: Optional[str] = None


@dataclass(frozen=True)
class TurnResult:
    stop_reason: str
    frames: int
    frames_after_terminal: int
    cancel_to_terminal_s: Optional[float]
    output_digest: str
    terminated_by: Optional[str] = None   # set when the boundary destroyed the unit


@dataclass(frozen=True)
class LifecycleCapabilities:
    """Every member defaults to false: an adapter offers none of these until it
    says so. Machine-state lifecycle operations, not agent-runtime ones -
    `pause`/`resume`/`fork` act on the sandbox, never on the turn it serves."""
    pause: bool = False
    resume: bool = False
    fork: bool = False


@dataclass(frozen=True)
class AdapterBinding:
    """Read by the adapter factory and by the conformance run. No core code and
    no caller reads this object or branches on `adapter`."""
    adapter: str
    profiles: Mapping[str, Mapping[str, Any]]
    declared_gap: Sequence[str]
    capabilities_offered: SessionCapabilities
    cancel_floor_s: float
    containment_marker: str
    execution_model: Mapping[str, str]   # axis -> this adapter's value; the pair is compared, never one
    lifecycle_offered: LifecycleCapabilities = field(default_factory=LifecycleCapabilities)


# --- The interface every containment technology implements -------------------
class ContainedAgentAdapter(ABC):
    """One contained unit that serves one agent turn.

    Isolation operations (admit, terminate, inspect_containment) and agent
    runtime operations (open_session, prompt, next_frame, cancel) sit on one
    class because a unit and the turn it serves have the same lifetime here.
    The isolation contract's `run` is served by prompt plus next_frame: the
    unit's work is one agent turn, and its unit result comes back from
    terminate.
    """

    interface_version = INTERFACE_VERSION

    # -- configuration -------------------------------------------------------
    @abstractmethod
    def binding(self) -> AdapterBinding:
        """Selecting a containment technology is configuration, not a code path."""

    # -- Isolation -----------------------------------------------------------
    @abstractmethod
    def admit(self, declaration: IsolationDeclaration, context: UnitContext) -> AdmissionHandle:
        """Refuse here what this adapter cannot resolve, rather than downgrading it silently."""

    @abstractmethod
    def terminate(self, handle: AdmissionHandle, grace_s: float) -> UnitResult:
        """Destroy the unit. This is the operation every ceiling above it depends on."""

    @abstractmethod
    def inspect_containment(self, handle: AdmissionHandle) -> ContainmentReport:
        """Assert containment from outside the unit."""

    # -- Machine-state lifecycle ----------------------------------------------
    # Capability operations, not ad hoc scripting: a caller calls them the same
    # way on every adapter. Where the isolation class beneath an adapter cannot
    # serve one, the operation returns a defined, typed unsupported result
    # (urn:agentic:problem:isolation-operation-unsupported, 501) rather than
    # silently degrading or emulating it - so the base class raises that by
    # default, and only an adapter whose binding declares the capability
    # overrides it with a real implementation.
    def pause(self, handle: AdmissionHandle) -> SnapshotHandle:
        """Checkpoint the unit's memory and filesystem state."""
        raise Problem("isolation-operation-unsupported",
                      f"{self.binding().adapter} does not serve pause: not offered by "
                      f"this isolation class", operation="pause", unit_id=handle.unit_id)

    def resume(self, snapshot: SnapshotHandle) -> AdmissionHandle:
        """Restore a paused unit from its snapshot. The state digest of the
        resumed unit, taken before any further syscall, must equal
        `snapshot.state_digest`."""
        raise Problem("isolation-operation-unsupported",
                      f"{self.binding().adapter} does not serve resume: not offered by "
                      f"this isolation class", operation="resume", snapshot_id=snapshot.snapshot_id)

    def fork(self, handle: AdmissionHandle) -> AdmissionHandle:
        """Clone a paused or running unit from a shared base, without
        re-provisioning (re-running admission's own resolution and validation)."""
        raise Problem("isolation-operation-unsupported",
                      f"{self.binding().adapter} does not serve fork: not offered by "
                      f"this isolation class", operation="fork", unit_id=handle.unit_id)

    # -- Agent runtime -------------------------------------------------------
    @abstractmethod
    def open_session(self, handle: AdmissionHandle, offered: SessionCapabilities) -> Session:
        """Negotiate; return what was actually agreed, never what was asked for."""

    @abstractmethod
    def prompt(self, session: Session, request: TurnRequest) -> str:
        """Start one turn. Returns a turn id; the turn is over only at the terminal frame."""

    @abstractmethod
    def next_frame(self, turn_id: str, timeout_s: float) -> Optional[TurnFrame]:
        """Bounded receive_updates. Returns None when no frame arrived in the window.
        An adapter that negotiated no streaming yields only the terminal frame."""

    @abstractmethod
    def cancel(self, session: Session, grace_s: float) -> None:
        """Acceptance of a request, not a kill. The caller keeps taking frames."""


# --- helpers shared by every adapter and by the runs -------------------------
def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def as_json(obj: Any) -> Any:
    """Dataclasses to plain JSON for the conformance report."""
    return json.loads(json.dumps(obj, default=lambda o: asdict(o) if hasattr(o, "__dataclass_fields__") else str(o)))
