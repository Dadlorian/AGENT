#!/usr/bin/env python3
"""The compiled engine: the document is lowered once, before the run.

Every operator becomes one or more transitions, the transitions are the queue,
and progress is one committed state row per transition. By run time there is no
tree: no worker ever holds one, nothing is resolved by looking at a parent, and
a failure can only be reported as a state and a transition. That is the axis
this pair turns on - when the operator tree is read - and it is why a field the
compiler has to guess at is a field the schema was missing rather than a bug in
either engine.

It accepts the same document bytes as the interpreted engine, with no pre-pass
of its own: `compile()` is handed exactly what the caller validated.

Declared execution model: the tree is read before the run, progress is a
committed transition row, every step is durable, and a failure is a state and a
transition.

Python 3.11 standard library only. No product name appears in this file.
"""
from __future__ import annotations

import json
import os

from base import (ParkStore, Parked, Reenter, Stepper, as_interface_problem,  # noqa: E402
                  gate_of, outcome_from, preflight, runner)
from interface import CHILD_SLOTS, CompositionEngine, Problem, RunOutcome, digest  # noqa: E402


def flat(node: dict) -> dict:
    """One step's declared fields with its child slots removed: an instruction,
    not a subtree. Nothing downstream can navigate from it."""
    return {k: v for k, v in node.items() if k not in CHILD_SLOTS}


class Adapter(CompositionEngine):
    engine_marker = "compiled-state-machine/0.1"
    tree_read_at = "before-run"
    progress_unit = "committed-transition-row"
    durable_at = "every-step"
    failure_locus = "state-and-transition"

    def __init__(self, schema, out_dir, validator, extra_ops=(), dispatch=None):
        super().__init__(schema, out_dir, validator)
        os.makedirs(out_dir, exist_ok=True)
        self.ledger_path = os.path.join(out_dir, "compiled-ledger.jsonl")
        self.state_path = os.path.join(out_dir, "compiled-state.jsonl")
        self.store = ParkStore(os.path.join(out_dir, "compiled-parks.json"))
        self.dispatch_adapter = dispatch or runner.DryRunAdapter()
        for name in extra_ops:
            setattr(self, "_lower_" + name, self._arm_the_schema_does_not_admit)

    # -- the binding assertion ---------------------------------------------
    def executor_ops(self) -> tuple[str, ...]:
        return tuple(sorted(n[len("_lower_"):] for n in dir(self) if n.startswith("_lower_")))

    def _table(self) -> dict:
        return {name: getattr(self, "_lower_" + name)
                for name in self.schema_ops() if hasattr(self, "_lower_" + name)}

    def _arm_the_schema_does_not_admit(self, node, iteration, out, loop):
        raise Problem("document-invalid", "reached an arm the schema does not admit")

    # -- compile: the only time the tree is read ----------------------------
    def compile(self, doc: dict) -> list[dict]:
        out: list[dict] = []
        self._lower(doc["root"], None, out, None)
        for i, t in enumerate(out):
            t["i"] = i
        return out

    def _lower(self, node, iteration, out, loop):
        arm = self._table().get(node["op"])
        if arm is None:
            raise Problem("document-invalid",
                          f"step {node['id']!r} names operator {node['op']!r}, which is "
                          f"not in the closed set {list(self.schema_ops())}",
                          step_id=node["id"])
        arm(node, iteration, out, loop)

    def _lower_sequence(self, node, iteration, out, loop):
        out.append({"kind": "enter", "op": "sequence", "step_id": node["id"], "loop": loop})
        for child in node["steps"]:
            self._lower(child, iteration, out, loop)

    def _lower_parallel(self, node, iteration, out, loop):
        out.append({"kind": "enter", "op": "parallel", "step_id": node["id"], "loop": loop})
        for branch in node["branches"]:
            self._lower(branch, iteration, out, loop)

    def _lower_loop(self, node, iteration, out, loop):
        """Every iteration the ceiling admits is lowered ahead of the run, with
        one check transition after each. Nothing is decided here: the check
        reads a verdict at run time and jumps."""
        out.append({"kind": "enter", "op": "loop", "step_id": node["id"], "loop": loop})
        checks = []
        for i in range(1, node["max_iterations"] + 1):
            self._lower(node["body"], i, out, node["id"])
            checks.append(len(out))
            out.append({"kind": "loop-check", "step_id": node["id"], "iteration": i,
                        "judge_step": node["exit_when"]["judge_step"],
                        "verdict": node["exit_when"]["verdict"],
                        "last": i == node["max_iterations"], "loop": node["id"]})
        ok = len(out)
        out.append({"kind": "loop-end", "step_id": node["id"], "reason": "verdict_pass",
                    "loop": loop})
        cap = len(out)
        out.append({"kind": "loop-end", "step_id": node["id"], "reason": "iteration_ceiling",
                    "loop": loop})
        after = len(out)
        for idx in checks:
            out[idx].update({"on_pass": ok, "on_cap": cap})
        out[ok]["goto"] = after
        out[cap]["goto"] = after

    def _lower_agent(self, node, iteration, out, loop):
        out.append({"kind": "call", "op": "agent", "step": flat(node),
                    "step_id": node["id"], "iteration": iteration, "loop": loop})

    def _lower_judge(self, node, iteration, out, loop):
        out.append({"kind": "call", "op": "judge", "step": flat(node),
                    "step_id": node["id"], "iteration": iteration, "loop": loop})

    def _lower_approval(self, node, iteration, out, loop):
        out.append({"kind": "call", "op": "approval", "step": flat(node),
                    "step_id": node["id"], "iteration": iteration, "loop": loop})

    # -- run: a worker advances the machine, one committed row per step -----
    def _commit(self, run_key: str, t: dict) -> None:
        with open(self.state_path, "a") as fh:
            fh.write(json.dumps({"run_key": run_key, "state": f"s{t['i']}",
                                 "transition": t["kind"], "step_id": t.get("step_id"),
                                 "engine_marker": self.engine_marker}) + "\n")

    def _advance(self, st, transitions, cursor, envelope):
        while cursor < len(transitions) and not st.stopped:
            t = transitions[cursor]
            self._commit(envelope["idempotency_key"], t)
            self._cursor = cursor
            if t["kind"] == "enter":
                st.enter({"id": t["step_id"], "op": t["op"]})
            elif t["kind"] == "call":
                if t["op"] == "agent":
                    st.call_agent(t["step"], t["iteration"])
                elif t["op"] == "judge":
                    st.run_judge(t["step"], t["iteration"])
                else:
                    st.run_approval(t["step"])
            elif t["kind"] == "loop-check":
                st.loop_iterations[t["step_id"]] = t["iteration"]
                passed = (st.results.get(t["judge_step"], {}).get("verdict") == t["verdict"])
                cursor = t["on_pass"] if passed else (t["on_cap"] if t["last"] else cursor + 1)
                continue
            elif t["kind"] == "loop-end":
                st.terminate_loop({"id": t["step_id"], "op": "loop"}, t["reason"],
                                  st.loop_iterations.get(t["step_id"], 0))
                cursor = t["goto"]
                continue
            cursor += 1
        return cursor

    def _pass(self, envelope, doc, agents, transitions, cursor=0, state=None,
              decision=None, note="", reentered=None, started=False, carry=()):
        ledger = runner.Ledger(self.ledger_path)
        st = Stepper(envelope, doc, agents, self.dispatch_adapter, ledger,
                     self.engine_marker, decision=decision, note=note)
        if state:
            st.restore(state)
        st.ledger_rows = list(carry)      # rows this delivery already appended
        self._cursor = cursor
        if not started:
            st.record("run-started", step_id="-", op="-", cost_micros=0,
                      envelope_digest=digest(envelope),
                      detail=envelope["intent"]["summary"])
        try:
            self._advance(st, transitions, cursor, envelope)
        except Parked as parked:
            gate = gate_of(doc, parked.step_id)
            gate.correlation_id = envelope["correlation"]["correlation_id"]
            state = st.park_state()
            state["ctx"] = {"envelope": envelope, "doc": doc, "agents": agents}
            state["cursor"] = self._cursor
            self.store.park(gate.gate_id, state)
            return outcome_from(st, self, "parked", parked=gate, reentered=reentered)
        except Reenter as re_:
            state = st.park_state()
            state["ctx"] = {"envelope": envelope, "doc": doc, "agents": agents}
            back = next(t["i"] for t in transitions
                        if t.get("step_id") == re_.step_id and t["kind"] in ("call", "enter"))
            return self._pass(envelope, doc, agents, transitions, cursor=back, state=state,
                              reentered=re_.step_id, started=True, carry=st.ledger_rows)
        except (Problem, runner.Problem) as raised:
            problem = as_interface_problem(raised)
            t = transitions[self._cursor]
            if t.get("loop") and problem.body["type"].endswith("budget-exhausted"):
                st.terminate_loop({"id": t["loop"], "op": "loop"}, "budget_ceiling",
                                  st.loop_iterations.get(t["loop"], 0))
            locus = {"state": f"s{self._cursor}", "transition": t["kind"]}
            problem.body.setdefault("locus", locus)
            st.record("run-refused", step_id=t.get("step_id", "-"), op="-", cost_micros=0,
                      problem_type=problem.body["type"], detail=problem.body["detail"])
            return outcome_from(st, self, "refused", problem=problem.body, locus=locus,
                                reentered=reentered)
        outcome = "stopped-on-reject" if st.stopped else "completed"
        st.record("run-completed", step_id="-", op="-", cost_micros=st.env["budget"]
                  ["ceiling_micros"] - st.remaining, detail=outcome)
        return outcome_from(st, self, outcome, reentered=reentered)

    # -- the two operations a caller makes ----------------------------------
    def start(self, envelope, workflow, agents) -> RunOutcome:
        errs = self.validate_workflow(workflow)
        if errs:
            raise Problem("document-invalid", "; ".join(errs[:4]), errors=len(errs),
                          refused_before="pricing and dispatch")
        preflight(self, workflow, agents, envelope)
        transitions = self.compile(workflow)          # the last time the tree is read
        return self._pass(envelope, workflow, agents, transitions)

    def resume(self, gate_id, decision, delivery_key, note="") -> RunOutcome:
        state = self.store.claim(gate_id, delivery_key)
        if state is None:
            return RunOutcome(engine_marker=self.engine_marker, outcome="parked",
                              duplicate_deliveries_ignored=1, gates_parked=0)
        ctx = state["ctx"]
        self.store.close(gate_id)
        transitions = self.compile(ctx["doc"])
        return self._pass(ctx["envelope"], ctx["doc"], ctx["agents"], transitions,
                          cursor=state["cursor"], state=state, decision=decision,
                          note=note, started=True)
