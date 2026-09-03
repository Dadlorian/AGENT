#!/usr/bin/env python3
"""The minimal call: register a scorecard, run the loop that works the metric
furthest from its target, and watch a failed gate leave the previous checkpoint in
place and an unbounded loop be refused before anything runs.

Two regions. The caller region below the CALLER CODE marker is everything a caller
writes: an intent and a payload per run. Everything above it is the platform - it
stamps the correlation id, the budget ceiling, the idempotency key and the actor
without being asked, registers the scorecard, drives the five interface operations,
and reads the outcome off the loop's own records. Nothing here names a driver, a
store or a product.

  ADAPTER=dryrun|live|second GATE=dryrun|second python3 call.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import (CandidateChange, DriverUnavailable, GateSpec, Gate, Metric, Problem,
                       Scorecard, LoopSpec, load_driver, load_gate_adapter)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SCORECARD_FILE = "scorecard.json"
BUDGET_CEILING_MICROS = 3_000_000
PER_ITERATION_MICROS = 250_000        # the ceiling is checked per iteration, not once per loop


# --- platform: the cross-cutting stamps the caller never asks for ------------
def stamp(kind: str, intent: dict, payload: dict) -> dict:
    """Build the entry envelope. correlation, budget, idempotency_key and actor are
    applied here; there is no argument by which a caller supplies or declines them."""
    key = hashlib.sha256(json.dumps([kind, intent, payload], sort_keys=True).encode()).hexdigest()[:16]
    return {
        "kind": kind,
        "actor": {"subject": {"human": "user:corey", "event": "service:ceremony-closed",
                              "schedule": "schedule:nightly", "external": "agent:partner"}[kind],
                  "delegation": []},
        "intent": intent,
        "correlation": {"run_id": f"run-{kind}-{key[:8]}", "root_dispatch_id": f"d-{kind}-{key[:8]}",
                        "depth": 0, "entry_kind": kind},
        "budget": {"ceiling_micros": BUDGET_CEILING_MICROS,
                   "per_iteration_micros": PER_ITERATION_MICROS},
        "idempotency_key": key,
        "payload": payload,
    }


def scorecard_fixture(name: str = SCORECARD_FILE) -> tuple[Scorecard, list[CandidateChange]]:
    """The scorecard a caller points at, read as data: metrics with targets, and the
    candidate changes offered for them. A candidate names the gate it will be put
    through and carries no criterion."""
    with open(os.path.join(FIXTURES, name)) as fh:
        row = json.load(fh)
    metrics = tuple(Metric(m["metric_id"], m["direction"], float(m["current"]),
                           float(m["target"]), float(m["scale"])) for m in row["metrics"])
    candidates = [CandidateChange(c["candidate_id"], c["metric_id"], GateSpec(**c["gate"]),
                                  float(c["value_if_promoted"]), c["rationale"])
                  for c in row["candidates"]]
    return Scorecard(row["scorecard_id"], metrics), candidates


def distances(scorecard: Scorecard, values: dict[str, float]) -> dict[str, float]:
    return {m.metric_id: m.distance for m in scorecard.with_values(values).metrics}


def enter(kind: str, intent: dict, payload: dict, adapter: str = "dryrun",
          gate: str = "dryrun") -> dict:
    """One entry envelope in, one answer out: a loop outcome, a refusal, or problem
    details. Registers the scorecard, opens the loop, and runs iterations until
    evaluate_exit says stop - the five operations and nothing else."""
    env = stamp(kind, intent, payload)
    cid = env["correlation"]["root_dispatch_id"]
    try:
        driver = load_driver(adapter, gate=Gate(load_gate_adapter(gate)))
    except DriverUnavailable as exc:
        return exc.problem.as_dict()
    scorecard, candidates = scorecard_fixture()
    handle = driver.register_scorecard(scorecard, candidates)
    if isinstance(handle, Problem):
        return handle.as_dict()
    spec = LoopSpec(payload["loop"]["loop_id"], payload["loop"]["iteration_ceiling"],
                    env["budget"]["ceiling_micros"], env["budget"]["per_iteration_micros"])
    opened = driver.open_loop(spec, handle.scorecard_id)
    if isinstance(opened, Problem):                  # refused before any iteration ran
        return {"adapter": driver.name, "gate": driver.gate.name, "loop_id": spec.loop_id,
                "refused": opened.as_dict(), "iterations": [], "correlation_id": cid}
    iterations, outcome = [], driver.evaluate_exit(spec.loop_id)
    while outcome is None:
        driver = driver.next_fire()                  # a scheduled driver starts a new fire here
        before = driver.read_checkpoint(spec.loop_id)
        record = driver.run_iteration(spec.loop_id, correlation_id=cid)
        if isinstance(record, Problem):
            return record.as_dict()
        iterations.append(dict(record.as_dict(), checkpoint_before=before.checkpoint_id,
                               distances_before=distances(scorecard, before.values)))
        outcome = driver.evaluate_exit(spec.loop_id)
        if isinstance(outcome, Problem):
            return outcome.as_dict()
    return {"adapter": driver.name, "gate": driver.gate.name, "loop_id": spec.loop_id,
            "scorecard_digest": handle.digest, "iterations": iterations,
            "outcome": outcome.as_dict(), "ceiling_micros": env["budget"]["ceiling_micros"],
            "correlation_id": cid, "refused": None}


def _table(rows: list[tuple[str, ...]]) -> str:
    w = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = ["  ".join(c.ljust(w[i]) for i, c in enumerate(rows[0])),
           "  ".join("-" * x for x in w)]
    out += ["  ".join(c.ljust(w[i]) for i, c in enumerate(r)) for r in rows[1:]]
    return "\n".join(out)


def report(runs: dict[str, dict]) -> int:
    """Presentation and the three proofs it prints, so the caller region below is the
    call, the answer and the one branch on a problem - nothing else."""
    main, capped, unbounded = runs["loop"], runs["capped"], runs["unbounded"]
    out = main["outcome"]
    print(f"adapter={main['adapter']}  gate={main['gate']}  scorecard digest={main['scorecard_digest']}  "
          f"correlation.id={main['correlation_id']}  budget={out['cost_micros']}/"
          f"{main['ceiling_micros']} micros ({PER_ITERATION_MICROS} per iteration)")
    print(_table([("it", "metric worked", "distance", "candidate", "gate", "decision",
                   "checkpoint", "moved")]
                 + [(str(r["iteration_index"]), r["metric_id"],
                     f"{r['distance_before']:.2f} -> {r['distance_after']:.2f}", r["candidate_id"],
                     r["gate_outcome"], r["decision"], r["checkpoint_id"],
                     "yes" if r["checkpoint_advanced"] else "held")
                    for r in main["iterations"]]))
    print(f"\nterminated_by={out['terminated_by']} ({out['termination_class']})  "
          f"iterations_run={out['iterations_run']}  targets held {out['targets_held']}/"
          f"{out['targets_total']}  final checkpoint={out['final_checkpoint_id']}")

    picked_furthest = all(
        r["metric_id"] == sorted(r["distances_before"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for r in main["iterations"])
    print()
    if picked_furthest:
        first = main["iterations"][0]
        print(f"PROOF: every iteration worked the metric furthest from its target - iteration 0 took "
              f"{first['metric_id']} at {first['distance_before']:.2f} over "
              + ", ".join(f"{k} at {v:.2f}" for k, v in sorted(first["distances_before"].items())
                          if k != first["metric_id"]))
    else:
        print("PROOF FAILED: an iteration worked a metric that was not the furthest from its target")
    declined = [r for r in main["iterations"] if r["decision"] == "declined"]
    held = declined and all(r["checkpoint_id"] == r["checkpoint_before"]
                            and not r["checkpoint_advanced"] for r in declined)
    if held:
        r = declined[0]
        print(f"PROOF: a gate that said {r['gate_outcome']} left checkpoint {r['checkpoint_id']} in "
              f"place - {len(declined)} declined iteration(s), none of which moved a checkpoint")
    else:
        print("PROOF FAILED: a declined iteration moved the checkpoint")
    refusal = unbounded["refused"] or {}
    refused = (refusal.get("type", "").endswith("document-invalid") and refusal.get("status") == 422
               and not unbounded["iterations"])
    if refused:
        print(f"PROOF: a loop with no iteration ceiling is refused before anything runs - "
              f"{refusal['type']} ({refusal['status']}), 0 iterations")
    else:
        print("PROOF FAILED: a loop with no iteration ceiling was accepted")
    cap = capped["outcome"]
    print(f"the same scorecard under a ceiling of 2: terminated_by={cap['terminated_by']} "
          f"({cap['termination_class']}), escalation={cap['escalation']['type']}")
    return 0 if (picked_furthest and held and refused
                 and out["terminated_by"] == "verdict_pass"
                 and cap["terminated_by"] == "iteration_ceiling") else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method every harness uses.
# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--adapter", default=os.environ.get("ADAPTER", "dryrun"))
    parser.add_argument("--gate", default=os.environ.get("GATE", "dryrun"))
    args = parser.parse_args()
    runs = {}
    for label, loop in (("loop", {"loop_id": "il-scorecard", "iteration_ceiling": 8}),
                        ("capped", {"loop_id": "il-capped", "iteration_ceiling": 2}),
                        ("unbounded", {"loop_id": "il-unbounded", "iteration_ceiling": None})):
        answer = enter(                                  # the whole call
            kind="human",
            intent={"run": "improve-the-scorecard",
                    "why": "the metric furthest from its target is worked first, and a gate may say no"},
            payload={"scorecard": "sc-target-t9", "loop": loop},
            adapter=args.adapter, gate=args.gate,
        )
        if "type" in answer:                             # one problem, never both
            print("application/problem+json")
            print(json.dumps(answer, indent=2))
            return 2
        runs[label] = answer
    return report(runs)


if __name__ == "__main__":
    raise SystemExit(main())
