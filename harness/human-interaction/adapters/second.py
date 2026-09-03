#!/usr/bin/env python3
"""Second surface: a streaming browser client, subscribed to the run's events.

The pair differs in execution model, not in product (F-b1-04). The first surface
is request/response over a single parked item; this one is a stream a person
watches for the whole run: run.started, step.progress and tool.proposed arrive as
they happen, the ask arrives inline as one more typed event, and the decision goes
back on the same correlation id. A second approval page of the same shape would
not have tested this interface at all.

The wire is server-sent events. `_sse` below is the framing a browser's
EventSource consumes - `id:`, `event:`, `data:` and a blank line - encoded from
the store's own event log and decoded back, so the shape and the replay
procedure are real even though no browser is attached here. Set STREAM_URL to
point the same client at a real endpoint: that path is claimed, never measured
(see README).

Its declared gaps, which are the first surface's strengths:

  requires_open_session = True       nobody sees an ask while disconnected...
  replayable_from_position = True    ... unless the stream is replayed from a
                                     position, which is why watch(since=n) works
                                     here and is refused on the first surface
  max_edit_bytes = 65536             a diff-sized edit fits, unlike a form field

--break-client-held is the deliberate breakage the definition of done names: the
client resumes from the copy of the ask it is holding rather than from the stored
row. Nothing else changes, and only this surface fails.

No product name appears in this file; a protocol name and a URL from the
environment do.
"""
from __future__ import annotations

import json
import os

from interface import (HumanDecision, HumanSurface, ParkedAsk, Problem, ResumeAck,
                       StreamEvent, digest)


def _sse(event: StreamEvent) -> str:
    """One event, framed the way a stream delivers it."""
    return (f"id: {event.seq}\n"
            f"event: {event.type}\n"
            f"data: {json.dumps(event.dict(), sort_keys=True)}\n\n")


def _parse_sse(text: str) -> list[StreamEvent]:
    events = []
    for block in text.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                events.append(StreamEvent(**json.loads(line[6:])))
    return events


class EventStreamSurface(HumanSurface):
    surface_marker = "event-stream-client/0.1"
    delivery_model = "stream"
    renders_run_in_flight = True
    replayable_from_position = True
    requires_open_session = True
    max_edit_bytes = 65536

    #: set by conformance.py --break-client-held; nothing else reads it
    client_held = False

    def __init__(self, store):
        super().__init__(store)
        self.endpoint = os.environ.get("STREAM_URL", "")     # unset: the stream is in process
        self.last_event_id: dict[str, int] = {}   # a position per run, as a client keeps one
        self._held: dict[str, dict] = {}                      # the client's own copy of an ask

    # -- delivery ------------------------------------------------------------
    def deliver(self, parked: ParkedAsk) -> dict:
        corr = parked.ask["correlation_id"]
        events = self.store.events(corr, self.last_event_id.get(corr, 0))
        if not events:
            raise Problem("adapter-unavailable",
                          "the stream produced no events for this run", ask_id=parked.ask["ask_id"])
        wire = "".join(_sse(e) for e in events)               # what goes down the socket
        seen = _parse_sse(wire)
        self.last_event_id[corr] = seen[-1].seq
        self._held[parked.ask["ask_id"]] = dict(parked.ask)   # what the client is now holding
        return {"surface": self.surface_marker, "delivered": True, "mode": "streamed-inline",
                "at": parked.stored_at, "wire_bytes": len(wire),
                "event_types": [e.type for e in seen],
                "last_event_id": self.last_event_id[corr]}

    def project(self, events: list[StreamEvent]) -> list[StreamEvent]:
        """Everything, in order: this is the surface that can show a run in
        flight, so nothing is filtered out."""
        return list(events)

    def authenticate(self, decision: HumanDecision) -> str:
        if not decision.actor:
            raise Problem("document-invalid", "the stream posted a decision with no subject",
                          ask_id=decision.ask_id)
        return decision.actor

    # -- the breakage --------------------------------------------------------
    def decide(self, decision: HumanDecision, now: str) -> ResumeAck:
        if not self.client_held:
            return super().decide(decision, now)
        # BREAKAGE: resume from the ask this client is holding, not from the store.
        # There is no lease and no state transition, so every redelivery applies
        # again, and the partial case resumes on an identifier the client minted.
        held = self._held.get(decision.ask_id)
        if held is None:
            return super().decide(decision, now)
        correlation = (held["correlation_id"] if decision.decision != "respond"
                       else "stream-" + decision.ask_id)
        parked = ParkedAsk(ask=held, state="open", stored_at=now,
                           resume_token="client-" + digest(held)[7:23],
                           stamps={"run_id": "?", "delegation_chain": [],
                                   "ceiling_micros": 0, "entry_kind": "human",
                                   "correlation_id": correlation})
        artifact = self.store.artifact_for(parked, decision)
        return ResumeAck(ask_id=decision.ask_id, correlation_id=correlation,
                         outcome="applied", applied=True, decision=decision.decision,
                         artifact=artifact,
                         stamps={"correlation_id": correlation, "run_id": "?",
                                 "actor": decision.actor, "delegation_chain": [],
                                 "ceiling_micros": 0, "entry_kind": "human",
                                 "idempotency_key": decision.idempotency_key,
                                 "resumed_at": now, "resumed_from": "client-held copy"},
                         surface=self.surface_marker, decided_by=decision.actor, resumed_at=now)


Adapter = EventStreamSurface
