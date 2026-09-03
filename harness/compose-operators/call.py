#!/usr/bin/env python3
"""The minimal call: one composition, every operator once, through one engine.

    ADAPTER=dryrun  python3 harness/compose-operators/call.py
    ADAPTER=second  python3 harness/compose-operators/call.py

Everything below the CALLER CODE marker is what a caller writes. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the envelope here, not asked for by the caller (F-b4-01), and the
document declares that it carries them rather than choosing them.

The caller names an engine once, as configuration. It never names an operator
handler, a transition, a state row, a ledger file or a park file: an engine
keeps its state where it likes, and a caller that opens it by path has left the
interface (T7.2).

Python 3.11 standard library only.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXAMPLE = os.path.join(ROOT, "examples", "end-to-end")
for path in (HERE, EXAMPLE):
    if path not in sys.path:
        sys.path.insert(0, path)

import run as runner                                     # noqa: E402  the reference runner
from interface import Envelope, Problem, load_engine     # noqa: E402

OUT = os.path.join(HERE, "out")
WORKFLOW = os.path.join(EXAMPLE, "workflows", "triage-and-fix.json")
SCHEMA = os.path.join(EXAMPLE, "schemas", "workflow.schema.json")
AGENTS = os.path.join(EXAMPLE, "agents.json")


def fixtures(out_dir: str):
    """The document under test, its schema, and the declared agent profiles.
    A fresh working directory; the engine's own storage lives under it and is
    the engine's, never opened here."""
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    return (json.load(open(SCHEMA)), json.load(open(WORKFLOW)),
            {a["name"]: a for a in json.load(open(AGENTS))["agents"]})


def build_envelope(kind="human", subject="user:corey") -> dict:
    """The one envelope of cap-consumption. The four stamps are applied here."""
    return Envelope(
        kind=kind, entry_id="human-checkout-500s", occurred_at="2026-09-03T09:12:00Z",
        actor={"subject": subject,                                    # identity
               "delegation_chain": [{"actor": subject, "obtained_via": "direct"}]},
        intent={"workflow_ref": "workflows/triage-and-fix.json",
                "summary": "Checkout returns 500 on coupon apply; find it and fix it."},
        correlation={"run_id": "run-ops-0001",                        # correlation
                     "correlation_id": "corr-ops-0001", "depth": 0},
        budget={"ceiling_micros": 1500000, "currency": "USD",         # budget
                "on_exceed": "terminate_unit"},
        idempotency_key="compose-operators-triage-2026-09-03",        # idempotency
        payload={"report_text": "POST /checkout/coupon returns 500 at pricing/coupon.py:88",
                 "source_kind": "typed by a person in a chat surface", "window_hours": 12},
    ).dict()


def outside_the_set(doc: dict) -> dict:
    """The same document with a seventh operator appended to the root."""
    bad = copy.deepcopy(doc)
    bad["root"]["steps"].append({"op": "branch", "id": "pick", "cases": []})
    return bad


def unbounded_loop(doc: dict) -> dict:
    """The same document with the loop's ceiling removed."""
    bad = copy.deepcopy(doc)
    for step in bad["root"]["steps"]:
        if step["op"] == "loop":
            step.pop("max_iterations")
    return bad


def report(adapter, parked, done, dup, refusals) -> int:
    """Presentation. Every number below came from the interface."""
    loop = next((t for t in done.terminations if t.reason.endswith("_pass")
                 or "ceiling" in t.reason), None)
    print(f"\nADAPTER={adapter}  engine_marker={done.engine_marker}")
    rows = [("start", f"{len(parked.ledger)} steps, parked at {parked.parked.step_id}",
             f"asks: {parked.parked.asks[:34]}", f"{parked.gates_parked} gate parked"),
            ("resume", f"{len(done.ledger)} more steps, outcome {done.outcome}",
             f"decision applied {done.gates_decided}x",
             f"{dup.duplicate_deliveries_ignored} redelivery ignored"),
            ("loop", loop.reason if loop else "-", f"{loop.iterations_run} iterations",
             f"unbounded={str(loop.unbounded).lower()}"),
            ("agents", f"{len(done.agents)} agent steps selected",
             ", ".join(sorted(set(done.agents.values()))[:3]) + ", ...", ""),
            ("verdict", "; ".join(f"{k}={v}" for k, v in done.verdicts.items()),
             f"spent {done.spent_micros} micros", ""),
            ("operators", f"{len(set(parked.operators_exercised) | set(done.operators_exercised))} of 6 exercised",
             ", ".join(sorted(set(parked.operators_exercised) | set(done.operators_exercised))), "")]
    rows += [("refused", name, body["type"], body["detail"][:40]) for name, body in refusals]
    for row in rows:
        print("  " + "  ".join(str(c).ljust(w) for c, w in
                               zip(row + ("",) * 4, (11, 44, 34, 30))))
    return 0 if done.outcome == "completed" and len(refusals) == 2 else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = os.environ.get("ADAPTER", "dryrun")            # configuration, not code
    schema, workflow, agents = fixtures(os.path.join(OUT, "call-" + adapter))
    envelope = build_envelope()
    refusals = []
    try:
        engine = load_engine(adapter, schema, os.path.join(OUT, "call-" + adapter),
                             runner.validate)               # one name, one binding
        parked = engine.start(envelope, workflow, agents)    # parks at the approval
        gate = parked.parked
        done = engine.resume(gate.gate_id, "approve", "delivery-1")
        dup = engine.resume(gate.gate_id, "approve", "delivery-1")   # a redelivery
        for name, bad in (("an operator outside the closed set", outside_the_set(workflow)),
                          ("a loop with no ceiling", unbounded_loop(workflow))):
            try:
                engine.start(envelope, bad, agents)
            except Problem as refused:                       # typed, before dispatch
                refusals.append((name, refused.body))
    except Problem as problem:
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    return report(adapter, parked, done, dup, refusals)


if __name__ == "__main__":
    sys.exit(main())
