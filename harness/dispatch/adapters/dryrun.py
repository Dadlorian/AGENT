#!/usr/bin/env python3
"""Dry-run dispatcher: a session held open in this process for the life of the
unit, deterministic, no network, no spend.

Execution model: the dispatcher starts the unit, keeps a control channel to it
for as long as it runs, and probes that channel after every checkpoint - so a
cancel accepted mid-unit is seen at the next step boundary and the unit stops
with `cancelled` and its partial outputs already durable.

This is the shape of the executor that runs today (one contained unit per
dispatch, driven over a control protocol, stoppable inside its grace window);
the product behind it is named only in adapters/live.py.

The per-step work is the worked example's deterministic unit, imported rather
than re-written, so this harness and examples/end-to-end produce the same text,
the same costs and the same verdict for the same document.

Python 3.11 standard library only.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import core  # noqa: E402
from adapters.base import SeamDispatcher, run_steps  # noqa: E402


class Adapter(SeamDispatcher):
    dispatcher_marker = "session-held-inprocess/0.1"
    unit_lifetime = "session_held"
    cancellation_reach = "mid_call"
    keeps_own_journal = False
    executor_reached_over = "in-process control channel"
    binding_role = "today"
    cost_read_mode = "scan-and-fold"
    breakable = True              # the shim the durability breakage targets

    def __init__(self, out_dir: str):
        super().__init__(out_dir)
        self.unit = core.example.DryRunAdapter()

    def execute_unit(self, req_body: dict, plan: dict, prior: dict) -> dict:
        """The session runs the steps here and stays reachable while it does."""
        os.environ["DISPATCH_BREAKABLE"] = "1"      # only this shim is targeted
        dispatch_id = req_body["dispatch_id"]

        def probe_cancel() -> bool:
            record = self.cancel_record(dispatch_id)
            return bool(record) and not record.get("already_terminal")

        try:
            return run_steps(req_body, plan, self.log, self.unit.complete, probe_cancel, prior)
        finally:
            os.environ.pop("DISPATCH_BREAKABLE", None)
