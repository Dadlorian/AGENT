#!/usr/bin/env python3
"""Compensation: the capability interface, and nothing else.

The whole vocabulary is four operations over one record - declare_effect,
seal_effect, unwind, unwind_plan - plus the two reads a caller and a checker
make of a register (`records`, `head`/`head_ordinal`). xc-compensation names
that operation set and marks it proposed, because no published specification
governs compensation: the saga / compensating-transaction pattern is prior art,
not a contract (blueprint standards row, X-xc-compensation-002).

Three things this interface refuses to leave to an implementation:

  1. The class is declared, never defaulted. An effect-committing step with no
     irreversibility class is refused here, in `declare_effect`, before any
     register is asked to write anything - so a register cannot be lenient and
     no operator can commit an effect around the declaration point.
  2. The declaration is durable strictly before the effect's own record. The
     record carries the head it became durable at and the head it was sealed
     at, and `head_ordinal` lets an outside checker compare the two without
     knowing where the register keeps them.
  3. A compensating action is a step in its own right - operator, input
     reference, its own idempotency key, its own timeout - not a callback
     attached to the forward step (xc-compensation instruction 3).

Worker registration, event-history formats, replay determinism, a task queue
and any server address are absent on purpose: a register that is a fold over an
append-only log could never implement them, so a contract that names them is a
contract shaped around one engine (F-a6-02).

No product name appears in this file. They appear in adapters/live.py and in
the env-var table of README.md, and nowhere else.

Python 3.11 standard library only.
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

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal

INTERFACE_VERSION = "urn:agentic:xc:compensation:0.1"

# The three members, and no fourth. There is no default: an absent class is a
# refused declaration, not a reversible effect (xc-compensation invariant 2).
CLASSES = ("reversible", "compensable", "irreversible")

# The reasons an unwind runs. "refused" is an after-the-fact refusal.
REASONS = ("failed", "cancelled", "refused")


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --------------------------------------------------------------------------
# The entry envelope (cap-consumption). One shape for all four entries of
# TARGET T6.2; kind says which door produced it and nothing below branches on it.
# --------------------------------------------------------------------------
@dataclass
class Envelope:
    kind: Literal["human", "event", "schedule", "external"]
    entry_id: str
    occurred_at: str
    actor: dict                 # {subject, delegation_chain}
    intent: dict                # {workflow_ref, summary} - never the criterion
    correlation: dict           # {run_id, correlation_id, depth}
    budget: dict                # {ceiling_micros, currency, on_exceed}
    idempotency_key: str
    payload: dict
    envelope_version: str = "0.1"

    def dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Typed failures (cap-errors / RFC 9457). The closed registry is the set this
# harness may raise from; this guarantee supplies no new failure format
# (xc-compensation instruction 8).
# --------------------------------------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":    (422, "Document invalid", False),
    "policy-denied":       (403, "Policy denied", False),
    "adapter-unavailable": (503, "A capability adapter is down", True),
}

# xc-compensation open question 2: an unwind that leaves records unwind-failed
# has no registered row. Until `compensation-unresolved` lands in the closed
# registry (docs/decomposition.md 2.1.6), an implementation returns the
# registered adapter-unavailable - also 503, also retryable - carrying the
# records it could not unwind in `causes`, and names the proposed type in the
# detail rather than minting one at the call site.
PROPOSED_UNRESOLVED = PROBLEM_BASE + "compensation-unresolved"


class NothingToReverse(Exception):
    """Raised by a compensating action that found nothing to reverse: the
    forward effect never became durable. It is the difference between an unwind
    that had no work and an unwind that failed, and it is why a run killed
    between the declaration and the effect is recoverable at all."""


class Problem(Exception):
    """A failure a caller branches on by type, never by reading prose (F-b4-07)."""

    def __init__(self, suffix: str, detail: str, **ext: Any):
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --------------------------------------------------------------------------
# The record and its parts (xc-compensation contract.shapes: CompensationRecord)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class CompensatingAction:
    """A new forward operation that is the logical inverse of the effect,
    declared as a step in its own right so it is planned, priced and graded like
    any other - with its own key and its own timeout (instructions 3 and 6)."""
    operator: str
    input_ref: str
    idempotency_key: str
    timeout_s: int = 30

    def dict(self) -> dict:
        return asdict(self)


@dataclass
class DeclareEffect:
    """What a caller declares before the step commits anything."""
    run_id: str
    step_id: str
    effect_digest: str
    irreversibility: str | None          # None is a refusal, never a default
    idempotency_key: str
    correlation_id: str
    actor: str
    entry_kind: str
    compensating_action: CompensatingAction | None = None
    mandate_ref: str | None = None


@dataclass
class CompensationRecord:
    run_id: str
    step_id: str
    effect_digest: str
    irreversibility: str
    idempotency_key: str
    declared_at_head: str
    state: Literal["declared", "committed", "compensated", "not-required", "unwind-failed"]
    compensating_action: dict | None = None
    mandate_ref: str | None = None
    committed_at_head: str | None = None
    sealed_response_ref: str | None = None
    correlation_id: str = ""
    actor: str = ""
    entry_kind: str = ""
    register_observed: str = ""          # emitted by the register that answered
    unwind_reason: str | None = None
    note: str = ""

    def dict(self) -> dict:
        return asdict(self)


@dataclass
class UnwindPlan:
    """The read an approval gate and a planner need before the first effect
    rather than after the last (xc-compensation operation 4)."""
    run_id: str
    would_unwind: list[dict] = field(default_factory=list)   # ordered, reverse of commit
    unreachable: list[dict] = field(default_factory=list)    # irreversible: no unwind reaches these
    register_observed: str = ""


@dataclass
class UnwindOutcome:
    step_id: str
    outcome: Literal["compensated", "not-required", "unwind-failed", "already-compensated"]
    operator: str | None = None
    detail: str = ""


@dataclass
class UnwindReport:
    run_id: str
    reason: str
    order: list[str] = field(default_factory=list)           # step ids, in the order walked
    outcomes: list[UnwindOutcome] = field(default_factory=list)
    compensated: int = 0
    not_required: int = 0
    unwind_failed: int = 0
    already_compensated: int = 0
    interrupted: bool = False
    register_observed: str = ""
    problem: dict | None = None

    def dict(self) -> dict:
        return {**asdict(self)}


# --------------------------------------------------------------------------
# The adapter
# --------------------------------------------------------------------------
class CompensationRegister(ABC):
    """Four operations and two reads.

    Every implementation declares how it behaves rather than being asked to
    behave alike: the class attributes below are its declared gaps, and the
    conformance run asserts the register behaved as declared instead of
    widening the contract until both members satisfy it.
    """

    register_marker: str = "unset"                  # read back from the record that answered
    where_the_register_lives: str = "unset"
    what_must_be_up_to_unwind: str = "unset"
    what_drives_the_reverse_walk: str = "unset"
    unwinds_from_cold_reader: bool = False          # can a process that declared nothing unwind?
    processes_required_for_progress: int = 1
    _handlers: dict = {}                            # set by register_handlers()

    def binding(self) -> dict:
        return {"adapter": type(self).__name__,
                "register_marker": self.register_marker,
                "where_the_register_lives": self.where_the_register_lives,
                "what_must_be_up_to_unwind": self.what_must_be_up_to_unwind,
                "what_drives_the_reverse_walk": self.what_drives_the_reverse_walk,
                "unwinds_from_cold_reader": self.unwinds_from_cold_reader,
                "processes_required_for_progress": self.processes_required_for_progress,
                "interface_version": INTERFACE_VERSION}

    def register_handlers(self, handlers: dict[str, Callable[[dict], str]]) -> None:
        """Declare the compensating operators this process can execute. A
        register that replays its history into the declaring code needs this
        before it can unwind; a register that folds a log does not, and takes a
        dispatcher at unwind time instead. That difference is one of the three
        axes the pair differs on, and it is declared, not discovered."""
        self._handlers = dict(handlers)

    def _fold(self, rows: list[dict]) -> list[CompensationRecord]:
        """Reconstruct the current records from this register's own append-only
        rows, in commit order. A declaration is never edited: a seal and an
        unwind outcome are further rows referencing it, and the fold is what
        turns them back into one record (xc-compensation invariant 5)."""
        by_step: dict[str, CompensationRecord] = {}
        order: list[str] = []
        for row in rows:
            step = row.get("step_id")
            if row.get("kind") == "declare":
                rec = CompensationRecord(**row["record"])
                rec.declared_at_head = row["hash"]
                by_step[step] = rec
                if step not in order:
                    order.append(step)
            elif step in by_step and row.get("kind") == "seal":
                rec = by_step[step]
                rec.state = "committed"
                rec.committed_at_head = row["hash"]
                rec.sealed_response_ref = row.get("sealed_response_ref")
            elif step in by_step and row.get("kind") == "outcome":
                rec = by_step[step]
                rec.state = row["state"]
                rec.unwind_reason = row.get("unwind_reason")
                rec.note = row.get("note") or ""
                if row.get("sealed_response_ref"):
                    rec.sealed_response_ref = row["sealed_response_ref"]
        recs = [by_step[s] for s in order]
        # Commit order, which is the order the reverse walk reverses.
        return sorted(recs, key=lambda r: self.head_ordinal(r.committed_at_head)
                      if r.committed_at_head else 10 ** 9)

    # -- the declaration point, identical on every register -------------------
    @staticmethod
    def validate(req: DeclareEffect) -> None:
        """The refusals xc-compensation states, applied here rather than in a
        register, so no register can be the lenient one. A caller repairing a
        declaration branches on the type, never on the sentence."""
        corr = {"run_id": req.run_id, "correlation_id": req.correlation_id, "depth": 0}
        if not req.irreversibility:
            raise Problem("document-invalid",
                          f"step {req.step_id!r} commits an effect and declares no "
                          "irreversibility class; there is no default",
                          correlation=corr)
        if req.irreversibility not in CLASSES:
            raise Problem("document-invalid",
                          f"step {req.step_id!r} declares irreversibility "
                          f"{req.irreversibility!r}; the class has three members: "
                          + ", ".join(CLASSES), correlation=corr)
        if not str(req.effect_digest).startswith("sha256:"):
            raise Problem("document-invalid",
                          f"step {req.step_id!r} declares no digest of the effect's request",
                          correlation=corr)
        if req.irreversibility == "compensable" and req.compensating_action is None:
            raise Problem("document-invalid",
                          f"step {req.step_id!r} is declared compensable and names no "
                          "compensating action; the class that admits one requires one",
                          correlation=corr)
        if req.irreversibility == "irreversible" and not req.mandate_ref:
            raise Problem("policy-denied",
                          f"step {req.step_id!r} is declared irreversible and carries no "
                          "mandate_ref; nothing can unwind it",
                          rule_id="compensation.irreversible-requires-mandate",
                          correlation=corr)
        if req.irreversibility == "irreversible" and req.compensating_action is not None:
            raise Problem("document-invalid",
                          f"step {req.step_id!r} is declared irreversible and names a "
                          "compensating action; the class that cannot be reversed produces "
                          "a gate, not a compensation", correlation=corr)

    def declare_effect(self, req: DeclareEffect) -> CompensationRecord:
        """Validate, then make the declaration durable. The template is here so
        that the refusal is the interface's and the durability is the
        register's; an adapter overrides `_declare`, never this."""
        self.validate(req)
        return self._declare(req)

    # -- what each register implements ---------------------------------------
    @abstractmethod
    def _declare(self, req: DeclareEffect) -> CompensationRecord:
        """Make the declaration durable and return the record, carrying the head
        it became durable at. Strictly earlier than the head the effect's own
        record will carry."""

    @abstractmethod
    def seal_effect(self, record: CompensationRecord, response_ref: str) -> CompensationRecord:
        """The effect returned: move the record to committed and seal it against
        that response, which is what a later replay returns instead of
        re-committing the effect."""

    @abstractmethod
    def unwind(self, run_id: str, reason: str,
               executor: Callable[[dict], str] | None = None,
               stop_after: int | None = None) -> UnwindReport:
        """Walk the committed records in reverse, run each compensating action
        under its own key, and record a per-record outcome. `stop_after` is the
        interruption a resumed unwind continues from; it is not a caller
        feature, it is how an interrupted unwind is made observable."""

    @abstractmethod
    def unwind_plan(self, run_id: str) -> UnwindPlan:
        """What would be unwound, and separately the effects no unwind reaches."""

    @abstractmethod
    def records(self, run_id: str) -> list[CompensationRecord]:
        """The read a resuming driver makes: a sealed record is replayed rather
        than compensated (xc-compensation instruction 7)."""

    @abstractmethod
    def head(self) -> str:
        """The register's current head."""

    @abstractmethod
    def head_ordinal(self, head: str) -> int:
        """Where a head stands in this register's own order. An outside checker
        compares two heads with this and learns nothing else about the store."""

    # -- the reverse walk, shared -------------------------------------------
    def _walk(self, walkable: list[CompensationRecord], reason: str,
              dispatch: Callable[[dict], str], stop_after: int | None,
              save: Callable[[CompensationRecord], None]) -> UnwindReport:
        """One unwinder per run drives the reverse walk, and the records being
        unwound do not listen for each other (xc-compensation invariant 6).
        Shared here because the *order* is the guarantee and must not differ by
        register; what differs is who holds the records and who may drive it."""
        rep = UnwindReport(run_id=walkable[0].run_id if walkable else "", reason=reason,
                           register_observed=self.register_marker)
        for i, rec in enumerate(reversed(walkable)):
            if stop_after is not None and i >= stop_after:
                rep.interrupted = True
                break
            rep.order.append(rec.step_id)
            if rec.state == "compensated":
                rep.already_compensated += 1
                rep.outcomes.append(UnwindOutcome(rec.step_id, "already-compensated"))
                continue
            if rec.irreversibility == "reversible":
                rec.state, rec.unwind_reason = "not-required", reason
                rec.note = "reversible: re-derived by the next run"
                save(rec)
                rep.not_required += 1
                rep.outcomes.append(UnwindOutcome(rec.step_id, "not-required"))
                continue
            if rec.irreversibility == "irreversible":
                rec.state, rec.unwind_reason = "not-required", reason
                rec.note = f"irreversible: no unwind exists; admitted under {rec.mandate_ref}"
                save(rec)
                rep.not_required += 1
                rep.outcomes.append(UnwindOutcome(rec.step_id, "not-required",
                                                  detail="no unwind reaches this effect"))
                continue
            action = dict(rec.compensating_action or {})
            try:
                ref = dispatch({**action, "run_id": rec.run_id, "step_id": rec.step_id,
                                "undoes_key": rec.idempotency_key})
                rec.state, rec.unwind_reason, rec.sealed_response_ref = "compensated", reason, ref
                save(rec)
                rep.compensated += 1
                rep.outcomes.append(UnwindOutcome(rec.step_id, "compensated",
                                                  operator=action.get("operator")))
            except NothingToReverse as exc:                 # declared, but the effect never happened
                rec.state, rec.unwind_reason = "not-required", reason
                rec.note = f"nothing to reverse: {exc}"
                save(rec)
                rep.not_required += 1
                rep.outcomes.append(UnwindOutcome(rec.step_id, "not-required",
                                                  operator=action.get("operator"),
                                                  detail="the effect never became durable"))
            except Exception as exc:                        # a destination that would not answer
                rec.state, rec.unwind_reason = "unwind-failed", reason
                rec.note = f"{type(exc).__name__}: {exc}"
                save(rec)
                rep.unwind_failed += 1
                rep.outcomes.append(UnwindOutcome(rec.step_id, "unwind-failed",
                                                  operator=action.get("operator"),
                                                  detail=f"{type(exc).__name__}: {exc}"))
        if rep.unwind_failed:
            causes = [{"step_id": o.step_id, "operator": o.operator, "detail": o.detail}
                      for o in rep.outcomes if o.outcome == "unwind-failed"]
            rep.problem = Problem(
                "adapter-unavailable",
                f"unwind of {rep.run_id} left {rep.unwind_failed} of {len(rep.outcomes)} "
                f"records unwind-failed; proposed type {PROPOSED_UNRESOLVED}",
                causes=causes).body
        return rep


ADAPTERS = ("dryrun", "second", "live")


def load_register(name: str, out_dir: str) -> CompensationRegister:
    """Binding is configuration: one name from the environment, one import, one
    class. Every adapter module exports its entry point as `Adapter`, so no code
    anywhere holds a per-register class-name table. `binding()` still reports
    the class that answered, so a report says which register ran without a
    caller naming it (F-b1-02)."""
    import importlib
    if name not in ADAPTERS:
        raise Problem("document-invalid",
                      f"unknown register {name!r}: choose {', '.join(ADAPTERS)}")
    return importlib.import_module(f"adapters.{name}").Adapter(out_dir)
