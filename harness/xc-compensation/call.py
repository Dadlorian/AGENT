#!/usr/bin/env python3
"""The minimal call: declare five effects with their classes and their
compensating actions before any of them commits, commit four, fail the fifth,
and walk the register backwards.

    ADAPTER=dryrun python3 harness/xc-compensation/call.py
    ADAPTER=second python3 harness/xc-compensation/call.py

Everything below the CALLER CODE marker is what a caller writes. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the envelope by `envelope()` in driver.py, not asked for by the caller
(F-b1-08), and the declaration is taken at the same crossing rather than
requested.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from driver import SAGA, Effect, Run, envelope                    # noqa: E402
from interface import Problem, load_register                      # noqa: E402
from store import EffectTable                                     # noqa: E402

# Three declarations the platform refuses. Two of them are the reason this
# guarantee is a placement and not error-handling: they are refused before the
# run starts, not discovered when the unwind cannot find a way back.
REFUSED = [
    ("no class at all", Effect("charge-the-card", None, "balance:card-4242", 2500)),
    ("compensable, no compensating action",
     Effect("charge-the-card", "compensable", "balance:card-4242", 2500)),
    ("irreversible, no mandate", Effect("send-the-receipt-email", "irreversible", "mail:sent", 1)),
]


def bind(name: str, tag: str = ""):
    """One name from the environment, one import, one class - and one table the
    register never writes to, so the compensations are counted from outside."""
    out = os.path.join(HERE, "out", f"call-{name}{tag}")
    return load_register(name, out), EffectTable(os.path.join(out, "effects.jsonl"))


def refusal(register, env, effect) -> dict:
    try:
        Run(register, EffectTable(os.path.join(HERE, "out", "refused.jsonl")),
            env).declare([effect])
        return {"type": "NOT REFUSED"}
    except Problem as problem:
        return problem.body


def cancelled(name: str) -> list[str]:
    """The same five effects, cancelled mid-flight rather than failed: the
    fourth effect is on the table with no seal behind it when the cancellation
    lands. Same walk, same order, different reason."""
    register, table = bind(name, "-cancelled")
    run = Run(register, table, envelope("event", f"run-cancel-{name}", "service:alerting"))
    run.run(SAGA, commit_upto=4, kill="inside-effect")
    return run.unwind("cancelled").order


def table_out(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(register, run, plan, report, refusals, cancelled_order, table):
    recs = {r.step_id: r for r in register.records(run.run_id)}
    table_out([(e.step_id, e.irreversibility, e.compensating_operator or "-",
                recs[e.step_id].declared_at_head[7:15],
                (recs[e.step_id].committed_at_head or "-")[7:15] if recs[e.step_id].committed_at_head
                else "-", recs[e.step_id].state) for e in SAGA],
              ("step", "class", "compensating action", "declared", "sealed", "state"))
    print(f"\nunwind_plan before the first effect: would_unwind="
          f"{[p['step_id'] for p in plan.would_unwind]} unreachable={plan.unreachable}")
    print(f"unwind_order={report.order}")
    print("compensations_in_order=" + str([o.step_id for o in report.outcomes
                                           if o.outcome == "compensated"]))
    print(f"outcomes: compensated={report.compensated} not_required={report.not_required} "
          f"unwind_failed={report.unwind_failed} reason={report.reason}")
    print(f"cancelled_mid_flight_order={cancelled_order}")
    print("world after the unwind: " + " ".join(
        f"{e.entity}={run.net(e)}" for e in SAGA[:4]))
    print("refusals: " + json.dumps([{"case": c, "type": b["type"].rsplit(":", 1)[-1],
                                      "status": b.get("status")} for c, b in refusals], indent=None))
    print(f"register_observed={report.register_observed} "
          f"(binding said {register.binding()['register_marker']})")


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    name = os.environ.get("ADAPTER", "dryrun")                  # configuration, never code
    register, table = bind(name)
    env = envelope("human", f"run-saga-{name}", "user:corey")
    try:
        run = Run(register, table, env)
        run.declare(SAGA)                     # five classes, five compensating actions, no commits yet
        plan = register.unwind_plan(run.run_id)          # what an approval gate reads before the first effect
        for effect in SAGA[:4]:
            run.commit(effect)                           # four effects commit
        failed = SAGA[4].step_id                         # the fifth fails: its effect never happens
        report = run.unwind("failed")                    # walk the register backwards
    except Problem as problem:                           # register unreachable, typed
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    refusals = [(case, refusal(register, env, effect)) for case, effect in REFUSED]
    cancelled_order = cancelled(name)                    # same five, cancelled mid-flight
    show(register, run, plan, report, refusals, cancelled_order, table)

    reverse = [e.step_id for e in SAGA[:4]][::-1]
    ran = [o.step_id for o in report.outcomes if o.outcome == "compensated"]
    ok = (ran == reverse                                 # the four compensations, in reverse order
          and report.compensated == 4 and report.unwind_failed == 0
          and all(run.net(e) == 0 for e in SAGA[:4])      # observed in the world, not on the record
          and cancelled_order == report.order            # a cancelled run unwinds the same way
          and [b["type"].rsplit(":", 1)[-1] for _, b in refusals]
              == ["document-invalid", "document-invalid", "policy-denied"]
          and report.register_observed == register.binding()["register_marker"])
    print(f"\n{'OK' if ok else 'FAILED'}: step {failed!r} failed; four effects unwound")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
