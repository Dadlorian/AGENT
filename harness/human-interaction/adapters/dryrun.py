#!/usr/bin/env python3
"""Dry-run surface: one parked item, request and response, in process, no network.

The execution model of the surface that runs on this host today, with the host,
the network and the product name removed: a decider opens one parked item, sees
the diff and four buttons, and posts one decision. Nothing streams; the run in
flight is not visible, because this surface appears only once there is something
to approve.

Its declared gaps are the point of the pair, not a defect to be papered over:

  renders_run_in_flight = False      a reviewer sees the question, not the work
  replayable_from_position = False   there is no position; there is one item
  max_edit_bytes = 256               an edit is a form field, so a larger one is
                                     refused with a type rather than truncated

Deterministic: same bytes every run, so a gate can assert on them. The failure
path is exercised on demand with DRYRUN_FAIL=1.
"""
from __future__ import annotations

import os

from interface import HumanDecision, HumanSurface, ParkedAsk, Problem, StreamEvent

RENDERED = ("human.ask", "human.decided", "human.refused", "ask.expired")


class ParkedItemSurface(HumanSurface):
    surface_marker = "parked-item-request-response/0.1"
    delivery_model = "request_response"
    renders_run_in_flight = False
    replayable_from_position = False
    requires_open_session = False
    max_edit_bytes = 256

    def deliver(self, parked: ParkedAsk) -> dict:
        if os.environ.get("DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable",
                          "the parked-item surface was made unreachable by DRYRUN_FAIL=1",
                          ask_id=parked.ask["ask_id"], retry_after_s=1)
        # One item, rendered whole: the diff above four buttons. It is queued for
        # whoever opens the surface next; it is not pushed to anyone.
        return {"surface": self.surface_marker, "delivered": True, "mode": "queued-for-open",
                "at": parked.stored_at, "rendered_bytes": len(parked.ask["proposed"]["diff"]),
                "buttons": list(parked.ask["allowed_decisions"])}

    def project(self, events: list[StreamEvent]) -> list[StreamEvent]:
        """It can only show what is decidable. Everything the run did before the
        ask is invisible here - which is the declared gap, made observable."""
        return [e for e in events if e.type in RENDERED]

    def authenticate(self, decision: HumanDecision) -> str:
        """The person who opened the item. A surface authenticates and puts the
        subject on the decision; the store never trusts the surface's word about
        who it was without one (F-b4-03)."""
        if not decision.actor:
            raise Problem("document-invalid", "the parked item was posted with no signed-in subject",
                          ask_id=decision.ask_id)
        return decision.actor


Adapter = ParkedItemSurface
