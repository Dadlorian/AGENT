#!/usr/bin/env python3
"""Live driver: this repository's own ceremony loop, brought in front of the interface.

The component behind this adapter is the loop that actually runs here today: the
Node script state/loop-workflow.js, which for each manifest section fires research,
authoring, a ceremony review and an improve pass that commits; its records are
kb/ceremonies/ceremony-NN-review.json and ceremony-NN-improve.json, the lessons rows
in state/lessons.jsonl, and the checkpoint in state/loop.json
({last_completed_section, ceremony}). One fire of that script is one iteration here.

Two things about it are stated rather than smoothed over, because they are the
non-conformances compose-improvement-loop-implement names:

  * that loop has no evaluation gate. A reviewer's severity field and a session's
    prose decide whether a finding is applied. Behind this interface the gate is
    the evaluation capability, and promotion_authority reads evaluation_gate - which
    is the migration, not a description of what runs unattended today.
  * that loop promotes by editing the target file in place and committing. This
    adapter never writes into kb/ceremonies, state/lessons.jsonl or state/loop.json:
    it reads them and writes its own records under IMPROVE_LOOP_SHADOW_DIR, which is
    the shadow migration that skill's step 8 requires before any cut-over.

Reached only through environment variables; nothing here is imported unless the
adapter is constructed, and the only non-stdlib reach is subprocess to fire the
script an operator names.

  IMPROVE_LOOP_CEREMONY_DIR  the ceremony records to read (kb/ceremonies)
  IMPROVE_LOOP_SHADOW_DIR    where this adapter writes; never the records above
  IMPROVE_LOOP_STATE_FILE    optional: the loop checkpoint (state/loop.json)
  IMPROVE_LOOP_LESSONS       optional: the lessons file (state/lessons.jsonl)
  IMPROVE_LOOP_FIRE_CMD      optional: the command that fires one iteration, e.g.
                             the Node runner over state/loop-workflow.js. Unset
                             means read-only: the records already on disk are the
                             iterations, and nothing is launched.

Status: claimed. No run of test.sh --live has been performed; every operation below
the reachability check has never executed against the real records.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HARNESS)

from interface import (DriverUnavailable, ImprovementLoopDriverBase, Problem,
                       ScorecardHandle, problem)


def _read(path: str) -> Any:
    with open(path) as fh:
        return json.load(fh)


def _write(path: str, body: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(body, fh, indent=2, sort_keys=True)


class Adapter(ImprovementLoopDriverBase):
    name = "live"
    role = "today"
    execution_model = "session-per-section"
    checkpoint_store = "ceremony-records"
    survives_process_loss = True
    promotion_authority = "evaluation_gate"

    def __init__(self, gate=None, decision_rule=None) -> None:
        ceremonies = os.environ.get("IMPROVE_LOOP_CEREMONY_DIR", "")
        shadow = os.environ.get("IMPROVE_LOOP_SHADOW_DIR", "")
        if not ceremonies or not shadow:
            raise DriverUnavailable(problem(
                "adapter-unavailable",
                "the live driver needs IMPROVE_LOOP_CEREMONY_DIR (the ceremony records to "
                "read) and IMPROVE_LOOP_SHADOW_DIR (where this adapter writes); see the "
                "env-var table in README.md"))
        if not os.path.isdir(ceremonies):
            raise DriverUnavailable(problem(
                "adapter-unavailable",
                f"IMPROVE_LOOP_CEREMONY_DIR={ceremonies!r} is not a directory on this host"))
        from interface import promote_on_pass
        super().__init__(gate=gate, decision_rule=decision_rule or promote_on_pass)
        self.ceremonies = ceremonies
        self.shadow = shadow
        self.state_file = os.environ.get("IMPROVE_LOOP_STATE_FILE", "")
        self.lessons = os.environ.get("IMPROVE_LOOP_LESSONS", "")
        self.fire_cmd = os.environ.get("IMPROVE_LOOP_FIRE_CMD", "")
        for sub in ("scorecards", "loops", "checkpoints"):
            os.makedirs(os.path.join(self.shadow, sub), exist_ok=True)

    def _path(self, *parts: str) -> str:
        return os.path.join(self.shadow, *parts)

    # --- the component: what one fire of the section loop is -----------------
    def fire(self, loop_id: str, index: int) -> None:
        """One iteration of the component. With IMPROVE_LOOP_FIRE_CMD set, this runs
        the section loop once; unset, the records already on disk are the iterations
        and nothing is launched. Either way this adapter writes only its own shadow."""
        if not self.fire_cmd:
            return
        subprocess.run(self.fire_cmd, shell=True, check=False, capture_output=True,
                       text=True, timeout=int(os.environ.get("IMPROVE_LOOP_FIRE_TIMEOUT", "900")))

    def ceremony_numbers(self) -> list[int]:
        """The component's own iteration history, read where it actually lives."""
        out = []
        for name in sorted(os.listdir(self.ceremonies)):
            if name.startswith("ceremony-") and name.endswith("-improve.json"):
                digits = name[len("ceremony-"):-len("-improve.json")]
                if digits.isdigit():
                    out.append(int(digits))
        return sorted(out)

    def last_checkpoint_on_disk(self) -> dict[str, Any] | Problem:
        """state/loop.json is the component's checkpoint: the last completed section
        and the ceremony number it wrote. Read only."""
        if self.state_file and os.path.exists(self.state_file):
            return _read(self.state_file)
        numbers = self.ceremony_numbers()
        if not numbers:
            return problem("criterion-unresolvable",
                           f"no ceremony-NN-improve.json under {self.ceremonies!r}")
        return {"last_completed_section": None, "ceremony": numbers[-1]}

    # --- storage: reads the component's records, writes only the shadow ------
    def store_scorecard(self, handle: ScorecardHandle, body: dict[str, Any]) -> None:
        _write(self._path("scorecards", handle.scorecard_id + ".json"), body)

    def load_scorecard(self, scorecard_id: str):
        path = self._path("scorecards", scorecard_id + ".json")
        if not os.path.exists(path):
            return problem("criterion-unresolvable",
                           f"no scorecard {scorecard_id!r} under the shadow directory")
        return _read(path)

    def store_state(self, loop_id: str, state: dict[str, Any]) -> None:
        _write(self._path("loops", loop_id + ".json"), state)

    def load_state(self, loop_id: str):
        path = self._path("loops", loop_id + ".json")
        if not os.path.exists(path):
            return problem("criterion-unresolvable",
                           f"no loop {loop_id!r} under the shadow directory")
        return _read(path)

    def store_checkpoint(self, body: dict[str, Any]) -> None:
        _write(self._path("checkpoints", body["checkpoint_id"] + ".json"),
               dict(body, component_checkpoint=self.last_checkpoint_on_disk()
                    if not isinstance(self.last_checkpoint_on_disk(), Problem) else None))

    def load_checkpoint(self, checkpoint_id: str):
        path = self._path("checkpoints", checkpoint_id + ".json")
        if not os.path.exists(path):
            return problem("criterion-unresolvable",
                           f"no checkpoint {checkpoint_id!r} under the shadow directory")
        body = _read(path)
        body.pop("component_checkpoint", None)
        return body

    # --- the one place the component is advanced -----------------------------
    def run_iteration(self, loop_id: str, correlation_id: str,
                      idempotency_key: str | None = None):
        state = self.load_state(loop_id)
        if not isinstance(state, Problem):
            self.fire(loop_id, int(state["iteration_index"]))
        return super().run_iteration(loop_id, correlation_id, idempotency_key)

    # --- read-back the conformance run uses ----------------------------------
    def checkpoints_written(self) -> int:
        return len([n for n in os.listdir(self._path("checkpoints")) if n.endswith(".json")])

    def records(self, loop_id: str) -> list[dict[str, Any]]:
        state = self.load_state(loop_id)
        return [] if isinstance(state, Problem) else list(state["records"])
