#!/usr/bin/env python3
"""The driver: one run of declared effects, committed, abandoned, resumed and
unwound. No register logic and no product name.

It exists so the minimal call and the conformance run drive the guarantee the
same way. Three things it does that a caller never has to ask for, because the
platform applies them (F-b1-08):

  * the declaration is made before the effect, at the same crossing budget and
    idempotency claims are taken - `commit()` cannot be reached without it;
  * every compensating action carries its own idempotency key and its own
    timeout, derived the way the forward effect's key was (instruction 6);
  * the effect and its reversal are appended to a table someone else counts,
    so "the compensation ran" is observed in the world rather than read off the
    record that promised it (best practice 5, F-a7-04).

The kill points are chosen to be the two that matter:

  kill="inside-effect"  the effect row is on the table and the seal never
                        happened. This is the crash window the declaration-
                        before-effect ordering exists for.
  kill="between-steps"  the last effect was sealed. A run killed here is
                        resumed, and its sealed responses are replayed rather
                        than compensated (instruction 7).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import (CompensatingAction, DeclareEffect, Envelope,  # noqa: E402
                       NothingToReverse, digest)
from store import EffectTable                                        # noqa: E402


@dataclass(frozen=True)
class Effect:
    """One side-effecting step as a caller declares it."""
    step_id: str
    irreversibility: str | None          # None is what an undeclared class looks like
    entity: str
    delta: int
    compensating_operator: str | None = None
    mandate_ref: str | None = None


# The five effects of the minimal call: declared before any of them commits.
SAGA = [
    Effect("reserve-the-inventory", "compensable", "inventory:sku-1188", 3, "inventory.release"),
    Effect("charge-the-card", "compensable", "balance:card-4242", 2500, "payments.void"),
    Effect("open-the-incident-ticket", "compensable", "tickets:open", 1, "tickets.close"),
    Effect("provision-the-workspace", "compensable", "workspaces:live", 1, "workspace.deprovision"),
    Effect("publish-the-release-note", "compensable", "notes:published", 1, "notes.retract"),
]

# The same five plus the two classes the saga does not exercise: an effect a
# later run re-derives, and one nothing can take back.
CORPUS = SAGA + [
    Effect("write-the-sweep-report", "reversible", "reports:swept", 1),
    Effect("send-the-receipt-email", "irreversible", "mail:sent", 1,
           mandate_ref="mandate:receipts:2026-09-03"),
]


def envelope(kind: str, run_id: str, actor: str) -> dict:
    """One entry envelope (cap-consumption). The stamps the platform applies -
    correlation id, budget ceiling, idempotency key, actor - are put on here,
    not asked for by the caller. Nothing below branches on `kind`."""
    return Envelope(
        kind=kind, entry_id=f"compensation-{kind}", occurred_at="2026-09-03T09:12:00Z",
        actor={"subject": actor, "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
        intent={"workflow_ref": "harness/xc-compensation", "summary": "one saga with five effects"},
        correlation={"run_id": run_id, "correlation_id": "corr-" + run_id, "depth": 0},
        budget={"ceiling_micros": 500_000, "currency": "USD", "on_exceed": "terminate_unit"},
        idempotency_key="key-" + run_id, payload={"effects": len(SAGA)},
    ).dict()


def effect_key(run_id: str, step_id: str) -> str:
    return "sha256:" + digest(f"{run_id}|{step_id}")[7:39]


def compensation_key(run_id: str, step_id: str) -> str:
    """Derived the same way the forward key was, so an unwind interrupted
    halfway is a duplicate delivery like any other (instruction 6)."""
    return "sha256:" + digest(f"{run_id}|{step_id}|compensate")[7:39]


def handlers(table: EffectTable, fail_operator: str | None = None):
    """The compensating operators this process can execute. Each one is a new
    forward operation that is the logical inverse of the effect: it appends a
    row that moves the entity onward, and never deletes the row it undoes
    (best practice 3, X-xc-compensation-003)."""
    def make(operator: str):
        def handle(action: dict) -> str:
            forward = next((r for r in table.forward()
                            if r["key"] == action["undoes_key"]), None)
            if forward is None:
                raise NothingToReverse(f"no forward row under {action['undoes_key'][:14]}…")
            if operator == fail_operator:
                raise TimeoutError(f"{operator} did not answer within "
                                   f"{action.get('timeout_s')}s")
            table.ensure("compensation", action["idempotency_key"],
                         run_id=forward["run_id"], step_id=forward["step_id"],
                         entity=forward["entity"], delta=-forward["delta"],
                         operator=operator, undoes=action["undoes_key"])
            return digest({"compensated": action["undoes_key"], "by": operator})
        return handle
    operators = {e.compensating_operator for e in CORPUS if e.compensating_operator}
    return {op: make(op) for op in operators}


class Run:
    """One run against one register. The register is chosen by configuration
    above this class; nothing here knows which one answered."""

    def __init__(self, register, table: EffectTable, env: dict):
        self.reg, self.table, self.env = register, table, env
        self.run_id = env["correlation"]["run_id"]
        self.declared: dict = {}
        self.handlers = handlers(table, os.environ.get("FAIL_OPERATOR") or None)
        # A register that replays history into the declaring code needs the
        # operators registered here; one that folds a log takes the same
        # dispatcher at unwind time. The caller writes one line either way.
        self.reg.register_handlers(self.handlers)

    # -- declare every class and every compensating action, before any commit --
    def declare(self, effects) -> list:
        out = []
        for e in effects:
            action = None
            if e.compensating_operator:
                action = CompensatingAction(
                    operator=e.compensating_operator,
                    input_ref=f"step.{e.step_id}.out.ref",
                    idempotency_key=compensation_key(self.run_id, e.step_id),
                    timeout_s=30)
            rec = self.reg.declare_effect(DeclareEffect(
                run_id=self.run_id, step_id=e.step_id,
                effect_digest=digest({"step": e.step_id, "entity": e.entity, "delta": e.delta}),
                irreversibility=e.irreversibility,
                idempotency_key=effect_key(self.run_id, e.step_id),
                correlation_id=self.env["correlation"]["correlation_id"],
                actor=self.env["actor"]["subject"], entry_kind=self.env["kind"],
                compensating_action=action, mandate_ref=e.mandate_ref))
            self.declared[e.step_id] = (e, rec)
            out.append(rec)
        return out

    def entity(self, e: Effect) -> str:
        """One entity per run, so "the effect was reversed" is a balance this
        run can be held to rather than a total several runs share."""
        return f"{e.entity}@{self.run_id}"

    def net(self, e: Effect) -> int:
        return self.table.net(self.entity(e))

    # -- commit one effect: the world first, then the seal ---------------------
    def commit(self, e: Effect, seal: bool = True) -> None:
        _, rec = self.declared[e.step_id]
        self.table.ensure("effect", rec.idempotency_key, run_id=self.run_id,
                          step_id=e.step_id, entity=self.entity(e), delta=e.delta,
                          head_at_commit=self.reg.head())      # the head the effect happened under
        if seal:
            self.reg.seal_effect(rec, digest({"effect": e.step_id, "ok": True}))

    def run(self, effects, commit_upto: int, kill: str | None = None) -> dict:
        """Declare every effect first, then commit the first `commit_upto`.
        `kill` abandons the run at that point: "inside-effect" leaves the last
        effect on the table with no seal behind it."""
        self.declare(effects)
        for i, e in enumerate(effects[:commit_upto]):
            last = (i == commit_upto - 1)
            self.commit(e, seal=not (last and kill == "inside-effect"))
        return {"committed": commit_upto, "killed": kill}

    # -- what a resuming driver does with a sealed record ---------------------
    def replay(self) -> list[str]:
        """Prefer replay to compensation: where the effect is held under a live
        key and the run is resuming rather than being abandoned, the sealed
        response is returned instead of re-committing (instruction 7)."""
        return [r.sealed_response_ref for r in self.reg.records(self.run_id)
                if r.sealed_response_ref and r.state == "committed"]

    def dispatch(self, action: dict) -> str:
        handler = self.handlers.get(action.get("operator", ""))
        if handler is None:
            raise RuntimeError(f"operator {action.get('operator')!r} has no handler here")
        return handler(action)

    def unwind(self, reason: str, stop_after: int | None = None):
        return self.reg.unwind(self.run_id, reason, executor=self.dispatch,
                               stop_after=stop_after)
