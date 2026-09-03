#!/usr/bin/env python3
"""Second driver: one iteration per fire, with no process between iterations.

A different execution model, not a different product of the same shape. The first
driver holds the loop in one process for its whole life; this one holds nothing
between iterations - every operation reads the loop's state and its checkpoint back
from files and writes them again before returning, so a scheduler, a webhook or a
person can fire the next iteration hours later into a process that has never seen
this loop. `next_fire` hands back a fresh binding for exactly that reason: the
conformance run drives it through a new object per iteration, which is what a
scheduled driver does and what the in-process driver cannot survive.

Same interface, different bytes: nothing above this file changes, and the iteration
records both drivers write are byte-identical.

  IMPROVE_LOOP_FIRE_ROOT  optional path; defaults to
                          harness/compose-improvement-loop/out/fires. The whole
                          store is here: no process, no port, no credential.

Swap procedure: ADAPTER=second. Configuration only - no code edit, and no change to
interface.py, call.py or conformance.py.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HARNESS)

from interface import ImprovementLoopDriverBase, Problem, ScorecardHandle, problem


def _read(path: str) -> Any:
    with open(path) as fh:
        return json.load(fh)


def _write(path: str, body: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(body, fh, indent=2, sort_keys=True)


class Adapter(ImprovementLoopDriverBase):
    name = "second"
    role = "second"
    execution_model = "one-iteration-per-fire"
    checkpoint_store = "file"
    survives_process_loss = True
    promotion_authority = "evaluation_gate"

    def __init__(self, gate=None, decision_rule=None) -> None:
        from interface import promote_on_pass
        super().__init__(gate=gate, decision_rule=decision_rule or promote_on_pass)
        self.root = os.environ.get("IMPROVE_LOOP_FIRE_ROOT",
                                   os.path.join(HARNESS, "out", "fires"))
        for sub in ("scorecards", "loops", "checkpoints"):
            os.makedirs(os.path.join(self.root, sub), exist_ok=True)

    def _path(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    def next_fire(self) -> "Adapter":
        """The next iteration runs in a binding that has read nothing yet."""
        return Adapter(gate=self.gate, decision_rule=self.decision_rule)

    # --- storage -------------------------------------------------------------
    def store_scorecard(self, handle: ScorecardHandle, body: dict[str, Any]) -> None:
        _write(self._path("scorecards", handle.scorecard_id + ".json"), body)

    def load_scorecard(self, scorecard_id: str):
        path = self._path("scorecards", scorecard_id + ".json")
        if not os.path.exists(path):
            return problem("criterion-unresolvable",
                           f"no scorecard file for {scorecard_id!r} under this fire root")
        return _read(path)

    def store_state(self, loop_id: str, state: dict[str, Any]) -> None:
        _write(self._path("loops", loop_id + ".json"), state)

    def load_state(self, loop_id: str):
        path = self._path("loops", loop_id + ".json")
        if not os.path.exists(path):
            return problem("criterion-unresolvable",
                           f"no loop file for {loop_id!r} under this fire root")
        return _read(path)

    def store_checkpoint(self, body: dict[str, Any]) -> None:
        # A new file per checkpoint; a superseded one is retained, never rewritten.
        _write(self._path("checkpoints", body["checkpoint_id"] + ".json"), body)

    def load_checkpoint(self, checkpoint_id: str):
        path = self._path("checkpoints", checkpoint_id + ".json")
        if not os.path.exists(path):
            return problem("criterion-unresolvable",
                           f"no checkpoint file for {checkpoint_id!r} under this fire root")
        return _read(path)

    # --- read-back the conformance run uses ----------------------------------
    def checkpoints_written(self) -> int:
        return len([n for n in os.listdir(self._path("checkpoints")) if n.endswith(".json")])

    def records(self, loop_id: str) -> list[dict[str, Any]]:
        state = self.load_state(loop_id)
        return [] if isinstance(state, Problem) else list(state["records"])
