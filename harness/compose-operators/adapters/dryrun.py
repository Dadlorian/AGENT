#!/usr/bin/env python3
"""The interpreted engine: the tree is read as it is executed.

This is the engine that runs today. examples/end-to-end/run.py walks the
operator tree node by node in one process, and this adapter is that walk with
one structural defect repaired: the set of operators it can execute is no
longer an if-else chain written beside a schema that also writes the set. The
dispatch table is built by asking, for every operator name the schema admits,
for a handler of that name - so an operator the schema does not admit has
nowhere to be reached from, and an operator this engine can run that the schema
does not admit shows up as drift instead of as a door nobody knows about.

Declared execution model: the tree is read during the walk, progress is a call
stack frame, nothing is durable between steps except at the gate boundary, and
a failure is reported as a position in the tree.

Python 3.11 standard library only. No product name appears in this file.
"""
from __future__ import annotations

import json
import os

from base import (COST_MICROS, ParkStore, Parked, Reenter, Stepper,  # noqa: E402
                  as_interface_problem, gate_of, outcome_from, preflight, runner)
from interface import CompositionEngine, Problem, RunOutcome, digest  # noqa: E402


class Adapter(CompositionEngine):
    engine_marker = "interpreted-walk/0.1"
    tree_read_at = "during-walk"
    progress_unit = "call-stack-frame"
    durable_at = "gate-boundary"
    failure_locus = "tree-position"

    def __init__(self, schema, out_dir, validator, extra_ops=(), dispatch=None):
        super().__init__(schema, out_dir, validator)
        os.makedirs(out_dir, exist_ok=True)
        self.ledger_path = os.path.join(out_dir, "interpreted-ledger.jsonl")
        self.store = ParkStore(os.path.join(out_dir, "interpreted-parks.json"))
        self.dispatch_adapter = dispatch or runner.DryRunAdapter()
        for name in extra_ops:            # the deliberate breakage lives here
            setattr(self, "_op_" + name, self._arm_the_schema_does_not_admit)
        self._path: list[str] = []
        self._failed_path: list[str] = []

    # -- the binding assertion: what this engine can dispatch ---------------
    def executor_ops(self) -> tuple[str, ...]:
        """Read from the running engine's own inventory of operator arms, never
        from the schema and never from the binding record that selected it."""
        return tuple(sorted(n[len("_op_"):] for n in dir(self) if n.startswith("_op_")))

    def _table(self) -> dict:
        """One arm per operator name the schema admits, and no other way in."""
        return {name: getattr(self, "_op_" + name)
                for name in self.schema_ops() if hasattr(self, "_op_" + name)}

    def _arm_the_schema_does_not_admit(self, st, node, iteration):
        raise Problem("document-invalid", "reached an arm the schema does not admit")

    # -- the six arms -------------------------------------------------------
    def _op_sequence(self, st, node, iteration):
        st.enter(node)
        for child in node["steps"]:
            self._step(st, child, iteration)

    def _op_parallel(self, st, node, iteration):
        st.enter(node)
        for branch in node["branches"]:     # the fan-out is the contract, not the threading
            self._step(st, branch, iteration)

    def _op_loop(self, st, node, iteration):
        st.enter(node)
        exit_when, ran = node["exit_when"], 0
        for i in range(1, node["max_iterations"] + 1):
            self._step(st, node["body"], i)
            ran = st.loop_iterations[node["id"]] = i   # iterations completed, not started
            if st.results.get(exit_when["judge_step"], {}).get("verdict") == exit_when["verdict"]:
                st.terminate_loop(node, "verdict_pass", ran)
                return
        st.terminate_loop(node, "iteration_ceiling", ran)

    def _op_agent(self, st, node, iteration):
        st.call_agent(node, iteration)

    def _op_judge(self, st, node, iteration):
        st.run_judge(node, iteration)

    def _op_approval(self, st, node, iteration):
        st.run_approval(node)

    # -- the walk -----------------------------------------------------------
    def _step(self, st, node, iteration):
        if st.stopped:                    # a rejected gate stops the composition
            return
        table = self._table()
        arm = table.get(node["op"])
        if arm is None:
            raise Problem("document-invalid",
                          f"step {node['id']!r} names operator {node['op']!r}, which is "
                          f"not in the closed set {list(self.schema_ops())}",
                          step_id=node["id"])
        self._path.append(node["id"])
        try:
            arm(st, node, iteration)
        except (Problem, runner.Problem):
            if not self._failed_path:     # the innermost frame owns the position
                self._failed_path = list(self._path)
            raise
        finally:
            self._path.pop()

    # -- one pass over the document -----------------------------------------
    def _pass(self, envelope, doc, agents, state=None, decision=None, note="",
              replay=(), reentered=None, started=False, carry=()):
        ledger = runner.Ledger(self.ledger_path)
        st = Stepper(envelope, doc, agents, self.dispatch_adapter, ledger,
                     self.engine_marker, decision=decision, note=note)
        if state:
            st.restore(state)
        st.replay_order, st.replay = list(replay), set(replay)
        st.ledger_rows = list(carry)      # rows this delivery already appended
        self._path, self._failed_path = [], []
        if not started:
            st.record("run-started", step_id="-", op="-", cost_micros=0,
                      envelope_digest=digest(envelope),
                      detail=envelope["intent"]["summary"])
        try:
            self._step(st, doc["root"], None)
        except Parked as parked:
            gate = gate_of(doc, parked.step_id)
            gate.correlation_id = envelope["correlation"]["correlation_id"]
            state = st.park_state()
            state["ctx"] = {"envelope": envelope, "doc": doc, "agents": agents}
            self.store.park(gate.gate_id, state)
            return outcome_from(st, self, "parked", parked=gate, reentered=reentered)
        except Reenter as re_:
            state = st.park_state()
            state["ctx"] = {"envelope": envelope, "doc": doc, "agents": agents}
            trunc = _before(state["recorded_all"], re_.step_id)
            return self._pass(envelope, doc, agents, state=state, replay=trunc,
                              reentered=re_.step_id, started=True,
                              carry=st.ledger_rows)
        except (Problem, runner.Problem) as raised:
            problem = as_interface_problem(raised)
            loop = self._enclosing_loop(doc, self._failed_path)
            if loop is not None and problem.body["type"].endswith("budget-exhausted"):
                st.terminate_loop(loop, "budget_ceiling", st.loop_iterations.get(loop["id"], 0))
            locus = {"path": "/".join(self._failed_path)}
            problem.body.setdefault("locus", locus)
            st.record("run-refused",
                      step_id=self._failed_path[-1] if self._failed_path else "-", op="-",
                      cost_micros=0, problem_type=problem.body["type"],
                      detail=problem.body["detail"])
            return outcome_from(st, self, "refused", problem=problem.body, locus=locus,
                                reentered=reentered)
        outcome = "stopped-on-reject" if st.stopped else "completed"
        st.record("run-completed", step_id="-", op="-", cost_micros=st.env["budget"]
                  ["ceiling_micros"] - st.remaining, detail=outcome)
        return outcome_from(st, self, outcome, reentered=reentered)

    @staticmethod
    def _enclosing_loop(doc, path):
        by_id = {n["id"]: n for n, _d in CompositionEngine._walk(doc["root"])}
        for step_id in reversed(path):
            node = by_id.get(step_id, {})
            if node.get("op") == "loop":
                return node
        return None

    # -- the two operations a caller makes ----------------------------------
    def start(self, envelope, workflow, agents) -> RunOutcome:
        errs = self.validate_workflow(workflow)
        if errs:
            raise Problem("document-invalid", "; ".join(errs[:4]), errors=len(errs),
                          refused_before="pricing and dispatch")
        preflight(self, workflow, agents, envelope)
        return self._pass(envelope, workflow, agents)

    def resume(self, gate_id, decision, delivery_key, note="") -> RunOutcome:
        state = self.store.claim(gate_id, delivery_key)
        if state is None:                     # a redelivery of a decision already applied
            return RunOutcome(engine_marker=self.engine_marker, outcome="parked",
                              duplicate_deliveries_ignored=1, gates_parked=0)
        ctx = state["ctx"]
        self.store.close(gate_id)
        return self._pass(ctx["envelope"], ctx["doc"], ctx["agents"], state=state,
                          decision=decision, note=note, replay=state["recorded_all"],
                          started=True)


def _before(order, step_id):
    """Everything recorded before the step the decider returned the work to."""
    base = [s.split("#")[0] for s in order]
    return order[:base.index(step_id)] if step_id in base else order
