#!/usr/bin/env python3
"""Dry-run driver: a bounded loop held in one process, no network, no product.

Execution model: the whole loop lives in this object. The scorecard, the loop state
and the checkpoints are held as serialised dicts and parsed on the way out, so a
read crosses a real boundary even here, but nothing survives the process - a second
binding of this driver cannot resume a loop the first one opened, which is the axis
the second driver differs on and the reason it exists.

It declares survives_process_loss false: it has no store outside this object and
reports that it does not, rather than pretending.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from typing import Any

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HARNESS)

from interface import ImprovementLoopDriverBase, Problem, ScorecardHandle, problem


class Adapter(ImprovementLoopDriverBase):
    name = "dryrun"
    role = "dryrun"
    execution_model = "bounded-in-process"
    checkpoint_store = "in-memory"
    survives_process_loss = False
    promotion_authority = "evaluation_gate"

    def __init__(self, gate=None, decision_rule=None) -> None:
        from interface import promote_on_pass
        super().__init__(gate=gate, decision_rule=decision_rule or promote_on_pass)
        self._scorecards: dict[str, str] = {}
        self._states: dict[str, str] = {}
        self._checkpoints: dict[str, str] = {}

    # --- storage -------------------------------------------------------------
    def store_scorecard(self, handle: ScorecardHandle, body: dict[str, Any]) -> None:
        self._scorecards[handle.scorecard_id] = json.dumps(body, sort_keys=True)

    def load_scorecard(self, scorecard_id: str):
        row = self._scorecards.get(scorecard_id)
        if row is None:
            return problem("criterion-unresolvable",
                           f"no scorecard {scorecard_id!r} is registered in this driver")
        return json.loads(row)

    def store_state(self, loop_id: str, state: dict[str, Any]) -> None:
        self._states[loop_id] = json.dumps(state, sort_keys=True)

    def load_state(self, loop_id: str):
        row = self._states.get(loop_id)
        if row is None:
            return problem("criterion-unresolvable",
                           f"no loop {loop_id!r} is open in this driver; a loop opened by "
                           "another binding of it did not survive")
        return json.loads(row)

    def store_checkpoint(self, body: dict[str, Any]) -> None:
        self._checkpoints[body["checkpoint_id"]] = json.dumps(body, sort_keys=True)

    def load_checkpoint(self, checkpoint_id: str):
        row = self._checkpoints.get(checkpoint_id)
        if row is None:
            return problem("criterion-unresolvable", f"no checkpoint {checkpoint_id!r} here")
        return json.loads(row)

    # --- read-back the conformance run uses ----------------------------------
    def checkpoints_written(self) -> int:
        return len(self._checkpoints)

    def records(self, loop_id: str) -> list[dict[str, Any]]:
        state = self.load_state(loop_id)
        return [] if isinstance(state, Problem) else copy.deepcopy(state["records"])
