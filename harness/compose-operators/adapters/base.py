#!/usr/bin/env python3
"""What both engines share: the leaf effect of an operator, and the park store.

Nothing here chooses the next step. Choosing the next step is the whole
difference between the two engines - one reads the tree while it walks, the
other read the tree once before the run and has only transitions left - so the
control flow lives in adapters/dryrun.py and adapters/second.py, and what a
step *does* lives here, imported from the reference runner rather than copied:

    examples/end-to-end/run.py   validate, plan, judge, CRITERIA, Ledger,
                                 Run.call_agent, Run.run_judge, Run.record,
                                 Run.spend, and its two dispatch adapters

That import is deliberate. If each engine had its own copy of what an agent
call, a judge and a ledger record are, two engines agreeing would prove that
two copies of one file agree; with one copy of the effect, an agreement is an
agreement about the control flow, which is the thing under test.

Python 3.11 standard library only. The product name behind the live dispatch
adapter is in adapters/live.py and in README's env table, not here.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(HARNESS))
EXAMPLE = os.path.join(ROOT, "examples", "end-to-end")
if EXAMPLE not in sys.path:
    sys.path.insert(0, EXAMPLE)
if HARNESS not in sys.path:
    sys.path.insert(0, HARNESS)

import run as runner                                            # noqa: E402
from interface import (Problem, RunOutcome, Termination, ParkedGate,   # noqa: E402
                       step_idempotency_key)

# The criterion store lives outside the document and the graded unit never sees
# it (F-b1-07). The reference runner ships one criterion; this harness registers
# one more so a loop can be driven to its iteration ceiling without editing any
# workflow document or any engine. Registering a criterion is not editing run.py.
runner.CRITERIA.setdefault("criterion://never-pass/v1",
                           {"must_contain": ["a-token-no-profile-emits"]})

COST_MICROS = runner.COST_MICROS


class Parked(Exception):
    """The run reached an approval operator with no decision in hand."""

    def __init__(self, step_id: str):
        self.step_id = step_id
        super().__init__(step_id)


class Reenter(Exception):
    """A decider returned the work with notes to a named earlier step."""

    def __init__(self, step_id: str, gate_step_id: str, note: str):
        self.step_id, self.gate_step_id, self.note = step_id, gate_step_id, note
        super().__init__(step_id)


def sid_of(node: dict, iteration: int | None) -> str:
    return node["id"] + (f"#{iteration}" if iteration else "")


class Stepper(runner.Run):
    """The leaf work of one operator, with the four cross-cutting stamps.

    Correlation, actor and the run's idempotency key are already written on
    every record by the runner this subclasses; what this class adds is the
    engine marker read from the running engine and a per-step idempotency key,
    because a run key alone deduplicates a whole submission while a restart
    mid-composition needs the step to be the unit (F-b4-08).
    """

    def __init__(self, envelope, workflow, agents, adapter, ledger, engine_marker,
                 snapshot=None, replay=(), decision=None, note=""):
        super().__init__(envelope, workflow, agents, adapter, ledger, approval=None)
        self.engine_marker = engine_marker
        self.snapshot = dict(snapshot or {})     # sid -> what a replay restores
        self.replay_order = list(replay)         # sids already recorded, in order
        self.replay = set(replay)                # ... and the same as a set
        self.loop_iterations: dict[str, int] = {}
        self.decision, self.note = decision, note
        self.recorded: list[str] = []            # sids this pass appended
        self.rows_by_sid: dict[str, tuple] = {}
        self.ops_seen: list[str] = []
        self.terminations: list[Termination] = []
        self.gates_parked = self.gates_decided = 0
        self.agents_selected: dict[str, str] = {}
        self.verdicts: dict[str, str] = {}
        self.ledger_rows: list[dict] = []

    # -- every record carries the marker of the engine that wrote it --------
    def record(self, kind, **fields):
        fields.setdefault("engine_marker", self.engine_marker)
        fields.setdefault("step_idempotency_key",
                          step_idempotency_key(self.env["idempotency_key"],
                                               str(fields.get("step_id", "-"))))
        rec = super().record(kind, **fields)
        self.ledger_rows.append(rec)
        return rec

    def seen(self, op: str) -> None:
        if op not in self.ops_seen:
            self.ops_seen.append(op)

    # -- the operators that carry other steps -------------------------------
    def enter(self, node: dict) -> None:
        """sequence, parallel and loop do no work of their own; entering one is
        still a step in the ledger, so the run shows all six operators rather
        than only the three that spend."""
        self.seen(node["op"])
        sid = node["id"]
        if sid in self.replay:
            return
        self.record("operator-entered", step_id=sid, op=node["op"], cost_micros=0,
                    detail=f"{node['op']} entered")
        self.recorded.append(sid)
        self.snapshot[sid] = {"kind": "enter"}

    # -- the operators that do work ----------------------------------------
    def call_agent(self, node, iteration=None):
        self.seen("agent")
        sid = sid_of(node, iteration)
        self.agents_selected[sid] = node["agent"]
        if sid in self.replay:
            self.results[node["id"]] = self.snapshot[sid]["out"]
            self.rows.append(tuple(self.snapshot[sid]["row"]))
            return
        super().call_agent(node, iteration)
        self.recorded.append(sid)
        self.rows_by_sid[sid] = self.rows[-1]
        self.snapshot[sid] = {"kind": "agent", "out": self.results[node["id"]],
                              "row": list(self.rows[-1])}

    def run_judge(self, node, iteration=None):
        self.seen("judge")
        sid = sid_of(node, iteration)
        if sid in self.replay:
            verdict = self.snapshot[sid]["verdict"]
            self.results[node["id"]] = {"text": verdict, "verdict": verdict}
            self.rows.append(tuple(self.snapshot[sid]["row"]))
            self.verdicts[sid] = verdict
            return verdict
        verdict = super().run_judge(node, iteration)
        self.verdicts[sid] = verdict
        self.recorded.append(sid)
        self.snapshot[sid] = {"kind": "judge", "verdict": verdict, "row": list(self.rows[-1])}
        return verdict

    def run_approval(self, node):
        self.seen("approval")
        gid = node["id"]
        if self.decision is None:
            self.record("approval-parked", step_id=gid, op="approval", cost_micros=0,
                        decisions=list(node["decisions"]), detail=node["asks"])
            self.gates_parked += 1
            raise Parked(gid)
        self.record("approval-returned", step_id=gid, op="approval", cost_micros=0,
                    decision=self.decision, note=self.note,
                    detail=f"decider returned '{self.decision}' on the same correlation id")
        self.rows.append((gid, "approval", "-", 0, self.remaining, self.decision))
        self.gates_decided += 1
        self.recorded.append(gid)
        if self.decision == "reject" and node.get("on_reject", "stop") == "stop":
            self.stopped = True
            self.terminations.append(Termination(gid, "approval_rejected", "failure"))
        elif self.decision == "return_with_notes":
            raise Reenter(node["return_to_step_id"], gid, self.note)

    def terminate_loop(self, node, reason, iterations_run):
        """A stop carries a result; a cap carries an escalation problem object
        (compose-loop). There is no third way for a loop to end quietly."""
        outcome = {"verdict_pass": "success", "iteration_ceiling": "escalated",
                   "budget_ceiling": "escalated"}[reason]
        term = Termination(node["id"], reason, outcome, iterations_run=iterations_run,
                           unbounded=False)
        if node["id"] in self.replay:      # already terminated before the park
            return next((t for t in self.terminations if t.step_id == node["id"]), term)
        self.terminations.append(term)
        if True:
            self.record("loop-terminated", step_id=node["id"], op="loop", cost_micros=0,
                        reason=reason, outcome=outcome, iterations_run=iterations_run,
                        unbounded=False, detail=f"loop ended: {reason}")
        if reason == "iteration_ceiling":
            raise Problem("deadline-exceeded",
                          f"loop {node['id']!r} reached its declared ceiling after "
                          f"{iterations_run} iterations without the exit verdict",
                          step_id=node["id"], reason=reason,
                          proposed_type="urn:agentic:problem:iteration-ceiling-reached")
        return term

    # -- the state a park hands to a resume ---------------------------------
    def park_state(self) -> dict:
        return {"snapshot": self.snapshot,
                "recorded_all": self.replay_order + self.recorded,
                "results": self.results, "rows": [list(r) for r in self.rows],
                "remaining": self.remaining, "clock": self.clock.isoformat(),
                "gates_parked": self.gates_parked, "gates_decided": self.gates_decided,
                "agents": self.agents_selected, "verdicts": self.verdicts,
                "terminations": [t.__dict__ for t in self.terminations]}

    def restore(self, state: dict) -> None:
        import datetime
        self.snapshot = dict(state["snapshot"])
        self.results = dict(state["results"])
        self.rows = [tuple(r) for r in state["rows"]]
        self.remaining = state["remaining"]
        self.clock = datetime.datetime.fromisoformat(state["clock"])
        self.gates_parked, self.gates_decided = state["gates_parked"], state["gates_decided"]
        self.agents_selected = dict(state["agents"])
        self.verdicts = dict(state["verdicts"])
        self.terminations = [Termination(**t) for t in state["terminations"]]


class ParkStore:
    """Where an engine keeps a parked run and the delivery keys it has already
    applied. Each engine owns its own directory; a caller holds a gate id and
    never a path (T7.2)."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.data = json.load(open(path)) if os.path.exists(path) else {}

    def save(self) -> None:
        with open(self.path, "w") as fh:
            json.dump(self.data, fh, indent=1, default=str)

    def park(self, gate_id: str, state: dict) -> None:
        entry = self.data.setdefault(gate_id, {"applied": [], "closed": False})
        entry.update({"state": state, "closed": False})
        self.save()

    def claim(self, gate_id: str, delivery_key: str) -> dict | None:
        """The one delivery that resumes the run; every later delivery of the
        same key is a no-op the caller can see counted."""
        entry = self.data.get(gate_id)
        if entry is None:
            raise Problem("idempotency-conflict", f"no parked gate {gate_id!r}")
        if delivery_key in entry["applied"] or entry["closed"]:
            return None
        entry["applied"].append(delivery_key)
        self.save()
        return entry["state"]

    def close(self, gate_id: str) -> None:
        self.data[gate_id]["closed"] = True
        self.save()


def as_interface_problem(exc):
    """The reference runner has a registry of its own, a subset of this
    interface's. A failure it raises is re-typed here rather than allowed to
    escape as a second error class a caller would have to know about."""
    if isinstance(exc, Problem):
        return exc
    body = dict(exc.body)
    suffix = str(body.pop("type")).rsplit(":", 1)[-1]
    for drop in ("title", "status", "retryable"):
        body.pop(drop, None)
    return Problem(suffix, body.pop("detail", ""), **body)


def preflight(engine, doc, agents, envelope) -> None:
    """The refusal that happens before anything is dispatched: a composition
    whose shortest finishing path cannot be afforded is refused, not started."""
    floor = engine.price(doc, agents, COST_MICROS, loop_iterations="1").estimate_micros
    ceiling = envelope["budget"]["ceiling_micros"]
    if floor > ceiling:
        raise Problem("budget-exhausted",
                      f"shortest finishing path costs {floor}, ceiling is {ceiling}; "
                      f"refused before execution", correlation=envelope["correlation"])


def outcome_from(stepper: Stepper, engine, outcome: str, parked=None, problem=None,
                 locus=None, reentered=None, duplicates=0) -> RunOutcome:
    return RunOutcome(
        engine_marker=engine.engine_marker, outcome=outcome,
        ledger=stepper.ledger_rows, terminations=stepper.terminations, parked=parked,
        verdicts=stepper.verdicts, agents=stepper.agents_selected,
        spent_micros=stepper.env["budget"]["ceiling_micros"] - stepper.remaining,
        operators_exercised=tuple(stepper.ops_seen),
        gates_parked=stepper.gates_parked, gates_decided=stepper.gates_decided,
        duplicate_deliveries_ignored=duplicates, reentered_step=reentered,
        problem=problem, locus=locus)


def gate_of(doc: dict, step_id: str) -> ParkedGate | None:
    for node, _d in _walk(doc["root"]):
        if node["id"] == step_id and node["op"] == "approval":
            return ParkedGate(gate_id=step_id, step_id=step_id, asks=node["asks"],
                              decisions=tuple(node["decisions"]), correlation_id="",
                              return_to_step_id=node.get("return_to_step_id"))
    return None


def _walk(node, depth=0):
    from interface import child_steps
    yield node, depth
    for _slot, child in child_steps(node):
        yield from _walk(child, depth + 1)
