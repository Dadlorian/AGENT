#!/usr/bin/env python3
"""The mechanism the C01-F closure names: `UnitContext` (interface.py, the
five stamps a caller never constructs by hand) read - not merely carried - at
the three points the closure names, by every adapter, not one.

Before this module, `correlation_id` was interpolated into a handful of error
messages, `ceiling_s` was read once (by the caller's own `Dispatch`, in
call.py, to compute a deadline it enforces from outside every adapter), and
`run_id`, `actor` and `idempotency_key` were only ever copied into an
`AdmissionHandle` or an env var and never read again. That is what the
evidence names: one field forwarded unchanged, the rest carried and dropped.

This module is where each of the five fields is read by something that can
act on it - refuse, dedupe, cap, or bind - at each of:

  admission        - before a unit is created (`admit`)
  dispatch          - before a turn is started on an admitted unit (`prompt`)
  capability_call   - before the unit reaches for a capability the host
                      brokers (a credential, an egress attempt, a model call)

The same three functions are called, in the same order, by every adapter
(dryrun.py, second.py, live.py) - the interface a caller programs against is
what depends on this module, not one concrete adapter.
"""
from __future__ import annotations

import time
from typing import Dict, Set, Tuple

from interface import Problem, UnitContext

POINTS = ("admission", "dispatch", "capability_call")
FIELDS = tuple(UnitContext.__dataclass_fields__.keys())   # declaration order, from the interface itself

MAX_CONCURRENT_UNITS_PER_RUN = 4     # run_id: a run-level admission budget
MAX_CEILING_S = 3600.0               # ceiling_s: refuse a ceiling no adapter here would ever honour


class ContextLedger:
    """One ledger. Records which field was read, by which guarantee, at which
    point - the `coverage()` a check reads back - and holds exactly the state
    each guarantee needs to be a real check rather than a log line: an
    idempotency-key registry, a correlation-id registry, a per-run concurrent-
    unit count, and the actor/ceiling/admission-time recorded per unit so
    dispatch and the capability call can catch a context that drifted, or ran
    out of budget, after admission.
    """

    def __init__(self) -> None:
        self.reads: list[Tuple[str, str]] = []
        self.active_idempotency_keys: Dict[str, str] = {}     # key -> unit_id with an outstanding dispatch
        self.active_correlation_ids: Dict[str, str] = {}      # correlation_id -> unit_id
        self.run_unit_counts: Dict[str, int] = {}              # run_id -> concurrently admitted units
        self.unit_context: Dict[str, UnitContext] = {}         # unit_id -> context at admission
        self.unit_admitted_at: Dict[str, float] = {}           # unit_id -> monotonic admission time

    # -- what a check reads back ---------------------------------------------
    def coverage(self) -> Dict[str, Set[str]]:
        out: Dict[str, Set[str]] = {p: set() for p in POINTS}
        for point, field in self.reads:
            out[point].add(field)
        return out

    def _read(self, point: str, field: str) -> None:
        self.reads.append((point, field))

    # -- admission: five checks, one per field, before a unit exists --------
    #
    # idempotency_key's own dedup lives at dispatch, not here: this harness's
    # idempotency_key is content-addressed (call.py hashes the payload), so
    # two unrelated calls that happen to carry the same probe text share one
    # key by design, and a claim held only at admission would outlive a unit
    # that is admitted and then abandoned (refused at dispatch for an
    # unrelated reason, e.g. a grace window below the adapter's cancel
    # floor) - the one path in this harness that never reaches `terminate`
    # and so never releases a claim. Dispatch is also where cap-idempotency
    # places the claim: before the spend a repeated turn would cause, not
    # before the admission that merely reserves a place for one.
    def guard_admission(self, ctx: UnitContext, unit_id: str) -> None:
        self._read("admission", "actor")
        if ":" not in ctx.actor or not ctx.actor.split(":", 1)[1]:
            raise Problem("document-invalid",
                          f"actor {ctx.actor!r} does not resolve to an identity (expected kind:name)",
                          field="actor", point="admission")

        self._read("admission", "idempotency_key")
        if not ctx.idempotency_key or not ctx.idempotency_key.strip():
            raise Problem("document-invalid",
                          "idempotency_key is empty: nothing to deduplicate a retry against",
                          field="idempotency_key", point="admission")

        self._read("admission", "correlation_id")
        holder = self.active_correlation_ids.get(ctx.correlation_id)
        if holder is not None:
            raise Problem("document-invalid",
                          f"correlation_id {ctx.correlation_id!r} is already bound to unit "
                          f"{holder!r}: two units cannot share one correlation",
                          field="correlation_id", point="admission")

        self._read("admission", "run_id")
        count = self.run_unit_counts.get(ctx.run_id, 0)
        if count >= MAX_CONCURRENT_UNITS_PER_RUN:
            raise Problem("budget-exhausted",
                          f"run {ctx.run_id!r} already has {count} units admitted and concurrent",
                          field="run_id", point="admission")

        self._read("admission", "ceiling_s")
        if not (0 < ctx.ceiling_s <= MAX_CEILING_S):
            raise Problem("budget-exhausted",
                          f"ceiling_s {ctx.ceiling_s} is not a resolvable budget: expected "
                          f"(0, {MAX_CEILING_S}]", field="ceiling_s", point="admission")

        # every field read and none refused: bind the unit to this context
        self.active_correlation_ids[ctx.correlation_id] = unit_id
        self.run_unit_counts[ctx.run_id] = count + 1
        self.unit_context[unit_id] = ctx
        self.unit_admitted_at[unit_id] = time.monotonic()

    # -- dispatch: the turn does not start on a context that drifted, or a
    # second time for one idempotency_key while the first is still running --
    def guard_dispatch(self, ctx: UnitContext, unit_id: str) -> None:
        admitted_ctx = self.unit_context.get(unit_id)

        self._read("dispatch", "actor")
        if admitted_ctx is not None and ctx.actor != admitted_ctx.actor:
            raise Problem("document-invalid",
                          f"actor drifted between admission ({admitted_ctx.actor!r}) and dispatch "
                          f"({ctx.actor!r}) for unit {unit_id!r}", field="actor", point="dispatch")

        self._read("dispatch", "correlation_id")
        if admitted_ctx is not None and ctx.correlation_id != admitted_ctx.correlation_id:
            raise Problem("document-invalid",
                          f"correlation_id drifted between admission and dispatch for unit "
                          f"{unit_id!r}", field="correlation_id", point="dispatch")

        self._read("dispatch", "idempotency_key")
        held_by = self.active_idempotency_keys.get(ctx.idempotency_key)
        if held_by is not None and held_by != unit_id:
            raise Problem("document-invalid",
                          f"idempotency_key {ctx.idempotency_key!r} already has an outstanding turn "
                          f"on unit {held_by!r}: a caller does not get a second turn for one request",
                          field="idempotency_key", point="dispatch")

        self._read("dispatch", "run_id")
        if ctx.run_id not in self.run_unit_counts:
            raise Problem("budget-exhausted",
                          f"run {ctx.run_id!r} has no admission on record to dispatch this turn "
                          f"against", field="run_id", point="dispatch")

        self._read("dispatch", "ceiling_s")
        admitted_at = self.unit_admitted_at.get(unit_id)
        if admitted_at is not None and (time.monotonic() - admitted_at) >= ctx.ceiling_s:
            raise Problem("budget-exhausted",
                          f"unit {unit_id!r} has no ceiling_s left to dispatch a turn against",
                          field="ceiling_s", point="dispatch")

        self.active_idempotency_keys[ctx.idempotency_key] = unit_id   # claim is now outstanding

    # -- capability call: what the unit reaches for, each time it reaches ----
    def guard_capability_call(self, ctx: UnitContext, unit_id: str, op: str) -> None:
        self._read("capability_call", "actor")
        if not ctx.actor:
            raise Problem("document-invalid",
                          f"capability call {op!r} carries no actor to scope the credential to",
                          field="actor", point="capability_call")

        self._read("capability_call", "ceiling_s")
        admitted_at = self.unit_admitted_at.get(unit_id)
        if admitted_at is not None and (time.monotonic() - admitted_at) > ctx.ceiling_s:
            raise Problem("budget-exhausted",
                          f"capability call {op!r} would run past unit {unit_id!r}'s ceiling",
                          field="ceiling_s", point="capability_call")

        self._read("capability_call", "correlation_id")
        if not ctx.correlation_id:
            raise Problem("document-invalid",
                          f"capability call {op!r} carries no correlation_id to attribute it to a run",
                          field="correlation_id", point="capability_call")

        self._read("capability_call", "run_id")
        if not ctx.run_id:
            raise Problem("document-invalid", f"capability call {op!r} carries no run_id",
                          field="run_id", point="capability_call")

        self._read("capability_call", "idempotency_key")
        if not ctx.idempotency_key:
            raise Problem("document-invalid", f"capability call {op!r} carries no idempotency_key",
                          field="idempotency_key", point="capability_call")

    # -- release: freed on terminate, whether requested or forced -----------
    def release(self, unit_id: str) -> None:
        ctx = self.unit_context.pop(unit_id, None)
        self.unit_admitted_at.pop(unit_id, None)
        if ctx is None:
            return
        if self.active_idempotency_keys.get(ctx.idempotency_key) == unit_id:
            del self.active_idempotency_keys[ctx.idempotency_key]
        if self.active_correlation_ids.get(ctx.correlation_id) == unit_id:
            del self.active_correlation_ids[ctx.correlation_id]
        if ctx.run_id in self.run_unit_counts:
            self.run_unit_counts[ctx.run_id] = max(0, self.run_unit_counts[ctx.run_id] - 1)


LEDGER = ContextLedger()
