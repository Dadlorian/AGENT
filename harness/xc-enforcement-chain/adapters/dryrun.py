#!/usr/bin/env python3
"""Dry-run binding: the chain in the process that constructs the unit.

This is the shape of the first implementation the owner skill names - the three
points that already refuse on this host joined by one shared context: the
approval unit at admission, the dispatcher at dispatch, and the host broker with
the gateway's scoped key at the call. Here they are stood up in process with no
network, deterministic, so a gate can assert on the bytes.

What it cannot do is written down rather than smoothed over: a unit whose code
was not built to enter the chain is never chained, and a metered call reached
with no context is counted but not stopped, because the thing that would stop it
is the same process that lost the context.
"""
from __future__ import annotations

import os

from interface import ChainContext, EnforcementChainAdapter, Problem, Unit, slot_rows


class InProcessChainAdapter(EnforcementChainAdapter):
    entity = "in-process chain (the three points that already refuse, one shared context)"
    locus = "in the process that constructs the unit and issues the call"
    processes_required = 1
    reach_over_unmodified = "none"
    refuses_unchained = False          # nothing here can stop a call it never saw
    declared_gaps = (
        "a unit not built to enter the chain is never chained",
        "a chain fault and a unit fault are the same process, so a crash removes both",
        "three of the six slots have no owner running on this host and record a no-op",
    )

    def __init__(self) -> None:
        super().__init__()
        self.state: dict = {}
        self.sealed: list[dict] = []

    def traverse(self, point: str, unit: Unit) -> list[dict]:
        if os.environ.get("CHAIN_FAIL") == "1":     # the failure path, exercised on demand
            raise Problem("adapter-unavailable",
                          "the in-process chain was made unreachable by CHAIN_FAIL=1; "
                          "nothing was admitted and nothing ran",
                          retry_after_s=1, enforced_by=self.entity)
        return slot_rows(point, unit, self.state)

    def seal(self, context: ChainContext) -> None:
        self.sealed.append(context.dict())


Adapter = InProcessChainAdapter
