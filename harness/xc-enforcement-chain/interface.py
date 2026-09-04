#!/usr/bin/env python3
"""The enforcement chain: one ordered traversal every unit makes, whichever way in.

Read it in this order. DECLARED_SLOTS is the closed, ordered slot list and
CONCERNS maps each slot to the caller-facing concern that attaches to it, so a
reader can see where tenancy and correlation land without a seventh and eighth
slot. OWNERS is host truth: a slot whose owner is not running here records a
no-op and is counted, never reported as passed. evaluate() is the one pure
function both enforcement points call, which is why their chain records are
identical rather than merely similar. ChainContext is what one traversal
produces. EnforcementChainAdapter.enter(), .exit() and .meter() are template
methods: the order, the totality, the inverse unwinding and the refusal of a
metered call that holds no context are the interface's, not an adapter's, so a
binding cannot shorten the chain and a caller has no argument with which to
skip a link. drive() is the platform-side path from a door to a metered call.

No product name, endpoint or socket path appears in this file.
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
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

INTERFACE_VERSION = "0.1"
CONTEXT_VERSION = "0.1"

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.abspath(os.environ.get("CHAIN_EXAMPLE_DIR")
                          or os.path.join(HERE, "..", "..", "examples", "end-to-end"))
ENTRIES_DIR = os.path.join(EXAMPLE, "entries")

# --- The chain ---------------------------------------------------------------
# The three named enforcement points, and the closed slot list in its one
# declared order (xc-enforcement-chain's chain-context shape, F-b4-01). A caller
# supplies neither: there is no parameter anywhere below in which an order, a
# subset or an exemption could be passed.
POINTS = ("admission", "dispatch", "call")
DECLARED_SLOTS = ("identity.resolve", "policy.decide", "budget.reserve",
                  "telemetry.open", "idempotency.claim", "provenance.open")
# The inverse of each slot, run on exit in the reverse of the entry order, on
# the failure path as well as the success path.
INVERSES = {"identity.resolve": "identity.release", "policy.decide": "policy.record",
            "budget.reserve": "budget.settle", "telemetry.open": "telemetry.close",
            "idempotency.claim": "idempotency.release", "provenance.open": "provenance.seal"}
# Where the six checks a caller hears about actually attach. Tenancy is not a
# seventh slot: xc-tenancy binds the principal at identity.resolve and refuses a
# cross-principal action at policy.decide and budget.reserve. Correlation is not
# an eighth: it is stamped by telemetry.open and carried into provenance.open.
CONCERNS = {"identity.resolve": "identity, and the tenancy principal it carries",
            "policy.decide": "policy, including a cross-principal refusal",
            "budget.reserve": "budget, including a per-principal ceiling",
            "telemetry.open": "correlation, stamped onto every record",
            "idempotency.claim": "idempotency",
            "provenance.open": "correlation, carried into the provenance statement"}
# Host truth, read from PASS.md A6 and not from any adapter: three slots have an
# owner running here and three do not. A slot with no owner records a no-op with
# its reason; a slot that reports passed with no owner running is a link that
# fails open, and attest() counts it.
OWNERS = {"identity.resolve": (False, "no identity field anywhere in the system (F-a6-05)"),
          "policy.decide": (False, "conformance checks exist; not wired into the enforcement path (F-a6-04)"),
          "budget.reserve": (True, "the scoped key with a hard cap terminates spend (F-a4-07)"),
          "telemetry.open": (True, "the trace backend is running (F-a1-05)"),
          "idempotency.claim": (True, "the hash-chained task store holds the key (F-a5-03)"),
          "provenance.open": (True, "the append-only evidence store is written (F-a5-04)")}

# --- Typed failures: RFC 9457, closed registry (docs/decomposition.md 2.1.6) --
# Nothing is minted here. `enforced_by` is this harness's one declared extension
# member, set from the refusal that came back so a report can read which
# enforcement point answered without reading the binding that selected it.
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":     (422, "The unit fails validation", False),
    "identity-untrusted":   (401, "The delegation chain does not verify", False),
    "policy-denied":        (403, "A deterministic pre-execution refusal", False),
    "budget-exhausted":     (402, "A metered call would cross the ceiling", False),
    "idempotency-conflict": (409, "Same key, different request body", False),
    "adapter-unavailable":  (503, "An enforcement point is unreachable", True),
}


class Problem(Exception):
    """The one return type of the chain's failure path: a slot refuses in the
    shape every slot refuses in, so the chain has one return type and not six."""

    def __init__(self, suffix: str, detail: str, **ext: Any) -> None:
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)

    @staticmethod
    def registered(type_uri: str) -> bool:
        return type_uri.startswith(PROBLEM_BASE) and type_uri[len(PROBLEM_BASE):] in REGISTRY


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --- What crosses a point ----------------------------------------------------
@dataclass(frozen=True)
class Unit:
    """One unit of work about to cross a point. `kind` is the door it entered
    by; nothing else in this object differs per door."""
    unit_id: str
    kind: str
    actor: dict
    correlation: dict
    ceiling_micros: int
    estimate_micros: int
    idempotency_key: str
    body_digest: str
    metered: bool = True

    def dict(self) -> dict:
        return {"unit_id": self.unit_id, "kind": self.kind, "actor": self.actor,
                "correlation": self.correlation, "ceiling_micros": self.ceiling_micros,
                "estimate_micros": self.estimate_micros, "idempotency_key": self.idempotency_key,
                "body_digest": self.body_digest, "metered": self.metered}


@dataclass
class SlotRecord:
    slot: str
    seq: int
    outcome: str                 # passed | no-op | refused
    owner_running: bool
    detail: str
    inverse: str = ""
    inverse_seq: int | None = None

    def dict(self) -> dict:
        return {"slot": self.slot, "seq": self.seq, "outcome": self.outcome,
                "owner_running": self.owner_running, "detail": self.detail,
                "inverse": self.inverse, "inverse_seq": self.inverse_seq}


@dataclass
class ChainContext:
    """One traversal of one point. Identical from either enforcement point:
    nothing in it names where the traversal ran."""
    point: str
    unit_id: str
    kind: str
    correlation: dict
    entered_seq: int
    slots: list[SlotRecord] = field(default_factory=list)
    refused_at: str | None = None
    sealed: bool = False
    outcome: str = "open"

    def dict(self) -> dict:
        return {"context_version": CONTEXT_VERSION, "point": self.point, "unit_id": self.unit_id,
                "kind": self.kind, "correlation": self.correlation, "entered_seq": self.entered_seq,
                "refused_at": self.refused_at, "sealed": self.sealed, "outcome": self.outcome,
                "slots": [s.dict() for s in self.slots]}


# --- The one evaluation both enforcement points run --------------------------
def evaluate(slot: str, point: str, unit: Unit, state: dict) -> tuple[str, str, dict | None]:
    """(slot, point, unit, the point's own state) -> outcome, detail, refusal.

    Pure but for `state`, which is the claim table and the reservation the point
    keeps. Both enforcement points call this, which is why the records they
    produce are the same bytes and a swap is comparable rather than plausible.
    """
    running, reason = OWNERS[slot]
    fail_open = os.environ.get("CHAIN_FAIL_OPEN", "")
    if not running:
        if slot == fail_open:                       # the link that fails open, on demand
            return "passed", f"reported passed with no owner running: {reason}", None
        return "no-op", reason, None
    if slot == "budget.reserve":
        # The ceiling is this unit's, so the reservation is kept per unit: one
        # unit cannot spend another's allocation, and a run's own points share it.
        held = state.setdefault("reserved", {}).setdefault(unit.unit_id, {})
        remaining = unit.ceiling_micros - sum(held.values())
        if unit.metered and unit.estimate_micros > remaining:
            return "refused", f"{unit.estimate_micros} micros needed, {remaining} left", {
                "suffix": "budget-exhausted",
                "detail": f"enforcement point {point}, slot budget.reserve: the metered call would "
                          f"cross the ceiling of {unit.correlation['run_id']}",
                "ext": {"correlation": unit.correlation, "retry_after_s": 0}}
        # Only the call point spends, so only the call point reserves; admission
        # and dispatch check that the ceiling could cover the call at all.
        spend = unit.estimate_micros if (unit.metered and point == "call") else 0
        held[point] = spend
        return "passed", f"reserved {spend} of {remaining}", None
    if slot == "telemetry.open":
        return "passed", f"span opened on correlation {unit.correlation['correlation_id']}", None
    if slot == "idempotency.claim":
        claims = state.setdefault("claims", {})
        first = claims.get(unit.idempotency_key)
        if first is not None and first != unit.body_digest:
            return "refused", "the key is held for a different body", {
                "suffix": "idempotency-conflict",
                "detail": f"enforcement point {point}, slot idempotency.claim: key "
                          f"{unit.idempotency_key} is held for a different body; nothing ran",
                "ext": {"correlation": unit.correlation}}
        claims[unit.idempotency_key] = unit.body_digest
        return ("passed", "claim held" if first is None else "replay of a held claim", None)
    return "passed", f"statement opened over {unit.body_digest[7:19]}", None


def slot_rows(point: str, unit: Unit, state: dict) -> list[dict]:
    """One traversal's rows, in the declared order, stopping at the first
    refusal. Both enforcement points build their rows here, so identical
    records are a property of the chain rather than of a review."""
    rows: list[dict] = []
    for slot in DECLARED_SLOTS:
        outcome, detail, problem = evaluate(slot, point, unit, state)
        row = {"slot": slot, "outcome": outcome, "owner_running": OWNERS[slot][0], "detail": detail}
        if problem is not None:
            row["problem"] = problem
        rows.append(row)
        if outcome == "refused":
            break
    return rows


# --- The interface the core imports ------------------------------------------
class EnforcementChainAdapter(ABC):
    """Three operations: enter, exit, attest, plus the metered call they wrap.

    enter() and exit() are concrete. An adapter supplies where the traversal
    happens and what it does with a sealed context; it does not get to choose
    the slot list, the order, whether the inverses run, or whether a metered
    call with no context for its point is a defect.
    """

    entity = "unset"
    locus = "unset"                      # where the traversal runs
    processes_required = 0               # how many must be up for a unit to proceed
    reach_over_unmodified = "unset"      # can it chain a workload it did not build
    refuses_unchained = False            # is an unchained metered call refused or merely counted
    declared_gaps: tuple[str, ...] = ()
    selected_by = "configuration"

    def __init__(self) -> None:
        self.seq = 0
        self.contexts: list[ChainContext] = []
        self.unchained: list[dict] = []          # metered calls reached with no context
        self.metered_calls = 0
        self.spend_micros = 0
        self.observed = ""                       # read from a refusal, never from the binding

    # --- the one adapter-specific operation --------------------------------
    @abstractmethod
    def traverse(self, point: str, unit: Unit) -> list[dict]:
        """Run the declared slots for this unit at this point and return one
        record per slot. Where this runs is the axis the pair differs on."""

    @abstractmethod
    def seal(self, context: ChainContext) -> None:
        """Record the sealed context wherever this enforcement point keeps it."""

    # --- enter: the order and the totality, not an adapter's choice ---------
    def enter(self, point: str, unit: Unit, parent: ChainContext | None = None) -> ChainContext:
        if point not in POINTS:
            raise Problem("document-invalid", f"{point!r} is not a named enforcement point")
        if point != "admission" and parent is None:
            raise Problem("policy-denied",
                          f"point {point} was reached with no chain context from the point before it",
                          rule_id="chain-context-required", enforced_by=self.entity)
        self.seq += 1
        ctx = ChainContext(point=point, unit_id=unit.unit_id, kind=unit.kind,
                           correlation=unit.correlation, entered_seq=self.seq)
        rows = self.traverse(point, unit)
        for i, slot in enumerate(DECLARED_SLOTS):          # the declared order, checked at the boundary
            row = rows[i] if i < len(rows) else None
            if row is None or row["slot"] != slot:
                raise Problem("document-invalid",
                              f"the enforcement point returned {row['slot'] if row else 'nothing'} "
                              f"where slot {i} of the declared chain is {slot}",
                              enforced_by=self.entity)
            ctx.slots.append(SlotRecord(slot=slot, seq=i, outcome=row["outcome"],
                                        owner_running=row["owner_running"], detail=row["detail"],
                                        inverse=INVERSES[slot]))
            if row["outcome"] == "refused":
                ctx.refused_at = slot
                problem = Problem(row["problem"]["suffix"], row["problem"]["detail"],
                                  **row["problem"].get("ext", {}))
                problem.body["enforced_by"] = self.entity      # read the point from the refusal
                self.exit(ctx, "refused")                      # inverses run on the failure path too
                raise problem
        self.contexts.append(ctx)
        return ctx

    # --- exit: the inverses, in the reverse of the entry order --------------
    def exit(self, context: ChainContext, outcome: str) -> ChainContext:
        for j, record in enumerate(reversed(context.slots)):
            record.inverse_seq = j
        context.outcome = outcome
        context.sealed = True
        if context.refused_at and context not in self.contexts:
            self.contexts.append(context)
        self.seal(context)
        return context

    # --- the metered call the chain exists to stand in front of -------------
    def meter(self, unit: Unit, context: ChainContext | None) -> dict:
        """The one thing that spends. A context for the call point is not a
        courtesy: without one this is a defect, counted either way, and refused
        outright by an enforcement point placed where the traffic must cross it."""
        if context is None or context.point != "call" or context.unit_id != unit.unit_id:
            self.unchained.append({"unit_id": unit.unit_id, "kind": unit.kind, "point": "call",
                                   "reason": "no chain context for the call point"})
            if self.refuses_unchained:
                raise Problem("policy-denied",
                              f"unit {unit.unit_id} arrived at a metered call with no context this "
                              f"enforcement point issued; nothing ran",
                              rule_id="chain-context-required", enforced_by=self.entity)
            self.metered_calls += 1                # in process, nothing stops it: that is the gap
            self.spend_micros += unit.estimate_micros
            return {"spent_micros": unit.estimate_micros, "chained": False}
        self.metered_calls += 1
        self.spend_micros += unit.estimate_micros
        return {"spent_micros": unit.estimate_micros, "chained": True}

    def axes(self) -> dict:
        return {"locus_of_traversal": self.locus,
                "processes_required_for_progress": self.processes_required,
                "reach_over_unmodified_workloads": self.reach_over_unmodified}

    def close(self) -> None:
        """Release anything the enforcement point holds. Idempotent."""


# --- The path from a door to a metered call ----------------------------------
def drive(adapter: EnforcementChainAdapter, units: list[Unit],
          on_refusal: Callable[[Unit, dict], None] | None = None) -> None:
    """Every unit crosses admission, then dispatch, then call, and only then
    spends. This is the one traversal path; the doors differ in what they put in
    the unit and in nothing else."""
    for unit in units:
        ctx = None
        try:
            for point in POINTS:
                ctx = adapter.enter(point, unit, parent=ctx if point != "admission" else None)
                if point != "call":
                    adapter.exit(ctx, "passed")
            adapter.meter(unit, ctx)
            adapter.exit(ctx, "passed")
        except Problem as problem:
            if ctx is not None and not ctx.sealed:
                adapter.exit(ctx, "refused")
            if on_refusal:
                on_refusal(unit, problem.body)


# --- attest_chain: reads records, not call sites ------------------------------
def attest(adapter: EnforcementChainAdapter, units: list[Unit]) -> dict:
    """(the records one enforcement point produced, the corpus) -> the report the
    definition of done asserts on. Counts, never prose."""
    report = {"adapter": adapter.entity, "adapter_observed": adapter.observed or "unread",
              # The doors the chain actually covered, read from the records and
              # not from the corpus: a door whose intake path lost its binding
              # is missing here, which is how one unbound door is named.
              "ways_in": sorted({c.kind for c in adapter.contexts}),
              "points_covered": sorted({c.point for c in adapter.contexts}, key=POINTS.index),
              "units_checked": len(units), "metered_units": adapter.metered_calls,
              "slots_missing": 0, "out_of_order": 0, "missing_inverse": 0,
              "ungated_metered_calls": len(adapter.unchained),
              "chain_context_missing": len({u["unit_id"] for u in adapter.unchained}),
              "slots_noop_by_absent_owner": 0, "fail_open_slots": 0, "adapters_run": 1,
              "contexts": len(adapter.contexts), "refusals_by_slot": {},
              "by_door": {u.kind: {"units": 0, "chain_context_missing": 0,
                                   "ungated_metered_calls": 0} for u in units}}
    for unit in units:
        report["by_door"][unit.kind]["units"] += 1
    for row in adapter.unchained:
        door = report["by_door"].setdefault(
            row["kind"], {"units": 0, "chain_context_missing": 0, "ungated_metered_calls": 0})
        door["chain_context_missing"] += 1
        door["ungated_metered_calls"] += 1
    for ctx in adapter.contexts:
        expected = (DECLARED_SLOTS[:DECLARED_SLOTS.index(ctx.refused_at) + 1]
                    if ctx.refused_at else DECLARED_SLOTS)
        got = [s.slot for s in ctx.slots]
        report["slots_missing"] += len([s for s in expected if s not in got])
        if got != list(expected) or [s.seq for s in ctx.slots] != sorted(s.seq for s in ctx.slots):
            report["out_of_order"] += 1
        inverses = [s.inverse_seq for s in ctx.slots]
        if not ctx.sealed or None in inverses or inverses != sorted(inverses, reverse=True):
            report["missing_inverse"] += 1
        for slot in ctx.slots:
            if slot.outcome == "no-op" and not slot.owner_running:
                report["slots_noop_by_absent_owner"] += 1
            if slot.outcome == "passed" and not slot.owner_running:
                report["fail_open_slots"] += 1     # a link reported as held that nothing holds
        if ctx.refused_at:
            report["refusals_by_slot"][ctx.refused_at] = \
                report["refusals_by_slot"].get(ctx.refused_at, 0) + 1
    report["records_digest"] = digest([c.dict() for c in adapter.contexts])
    return report
