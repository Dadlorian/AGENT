#!/usr/bin/env python3
"""Second binding: an autonomous agent submits a task and detaches.

The axis this pair differs on is liveness. The first binding's producer holds
the submission open and is there to be told what happened; this one's submits
through the agent messaging protocol and may be gone before anything runs, so
the acknowledgement is recorded for collection rather than read off the wire by
whoever sent it. An envelope both bindings can produce therefore cannot have
been shaped around either one's presence - which is the whole point of the pair.

What the mapper does differently, and all of it lands in door fields:
  - the message identifier becomes the idempotency key
  - the submitting agent's attested identity becomes the first hop of the chain
  - the agent's own correlation becomes the parent correlation, not the correlation

Reachability: with INTAKE_A2A_URL set (see README) this adapter POSTs the mapped
message to the route the operator supplies whole, under the method name the
operator supplies; no route and no method name is invented here, because both
records on file for the protocol are search results rather than fetched
specification text. With it unset the same state machine runs in process, which
is what a dry run exercises: the shape and the swap procedure are real either way.
"""
from __future__ import annotations

import json
import os
from typing import Any, Mapping

from interface import Envelope, Problem, ProducerMessage, WorkIntakeAdapter, digest

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None


class AgentMessageIntakeAdapter(WorkIntakeAdapter):
    entity = "agent messaging (the producer submits a task and detaches)"
    execution_model = "detached-message-submitted"
    declared_marker = "task-message-accepted"
    ack_delivery = "recorded-for-later-collection"
    idempotency_source = "the submitting agent's message identifier"
    registered_mappers = ("a2a-message",)
    declared_gaps = ("the producer is not present when the job ends, so nothing may be told to it later",
                     "no human is assumed to read a refusal, so every refusal has to be typed")

    def __init__(self) -> None:
        super().__init__()
        self.producer_present_at_ack = False
        self.collected: dict[str, dict] = {}      # correlation id -> the ack left for collection

    # --- the producer side --------------------------------------------------
    def render_message(self, door: Mapping[str, Any], subject: Mapping[str, Any]) -> ProducerMessage:
        """One document as a task message from an agent acting for this door."""
        job = {"intent": subject["intent"], "budget": subject["budget"],
               "payload": subject["payload"], "envelope_version": subject["envelope_version"]}
        body = {"role": "agent",
                "messageId": door["message_identity"],
                "taskId": door["entry_id"],
                "entryKind": door["kind"],
                "contextId": "ctx-" + door["kind"],          # the agent's own correlation
                "sentAt": door["occurred_at"],
                "submittedBy": f"agent:{door['kind']}-submitter",
                "onBehalfOf": {"subject": door["actor_subject"],
                               "chain": [list(hop) for hop in door["chain"]]},
                "parts": [{"kind": "data", "data": job}],
                "priority": "high"}                          # producer-specific; dropped, never carried
        transport = {"handle": f"transport-handle-{door['kind']}-a2a", "content_type": "application/json"}
        return ProducerMessage("a2a-message", body, transport)

    # --- normalise ----------------------------------------------------------
    def normalise(self, message: ProducerMessage) -> Envelope:
        body = message.body
        job = next(p["data"] for p in body["parts"] if p["kind"] == "data")
        kind = body["entryKind"]
        key = digest(job)[7:19]
        chain = [{"actor": body["submittedBy"], "obtained_via": "workload_attestation"}]
        chain += [{"actor": a, "obtained_via": v} for a, v in body["onBehalfOf"]["chain"]]
        return Envelope(
            kind=kind,
            entry_id=body["taskId"],
            occurred_at=body["sentAt"],
            actor={"subject": body["onBehalfOf"]["subject"], "delegation_chain": chain},
            intent=dict(job["intent"]),
            # The agent's own correlation is the parent, never the correlation.
            correlation={"run_id": f"run-{kind}-{key}", "correlation_id": f"corr-{kind}-{key}",
                         "parent_correlation_id": body["contextId"], "depth": 1},
            budget=dict(job["budget"]),
            idempotency_key=body["messageId"],
            payload=dict(job["payload"]),
            envelope_version=job["envelope_version"],
        )

    def _record(self, envelope: Envelope) -> str:
        """The producer has detached: the entry is recorded and its
        acknowledgement is left where a later call can collect it."""
        url = os.environ.get("INTAKE_A2A_URL")
        marker = self.declared_marker
        if url:
            marker = self._send(url, envelope)
        self.collected[envelope.correlation["correlation_id"]] = {
            "entry_id": envelope.entry_id, "collected": False}
        return marker

    def _send(self, url: str, envelope: Envelope) -> str:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment",
                          retry_after_s=30)
        method = os.environ.get("INTAKE_A2A_METHOD")
        if not method:
            raise Problem("adapter-unavailable",
                          "INTAKE_A2A_METHOD is not set; the protocol's method name is supplied by the "
                          "operator because no fetched specification is on file for it",
                          retry_after_s=30)
        payload = json.dumps({"jsonrpc": "2.0", "id": envelope.entry_id, "method": method,
                              "params": {"message": envelope.dict()}}).encode()
        headers = {"content-type": "application/json",
                   "x-correlation-id": envelope.correlation["correlation_id"]}
        token = os.environ.get("INTAKE_A2A_TOKEN")
        if token:
            headers["authorization"] = "Bearer " + token
        try:
            with URLLIB.urlopen(URLLIB.Request(url, data=payload, headers=headers),
                                timeout=int(os.environ.get("INTAKE_TIMEOUT_S", "30"))) as resp:
                json.load(resp)
                return resp.headers.get("x-intake-marker", self.declared_marker)
        except urllib.error.HTTPError as exc:                      # pragma: no cover - live only
            raise Problem("adapter-unavailable",
                          f"HTTP {exc.code}: {exc.read()[:200].decode('utf-8', 'replace')}",
                          retry_after_s=30) from exc
        except Exception as exc:                                   # pragma: no cover - live only
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc

    def collect(self, correlation_id: str) -> dict:
        """What a detached producer does instead of holding the call open. Not
        part of the interface: nothing in the core calls it, and it returns the
        entry identifier, never an outcome."""
        record = self.collected[correlation_id]
        record["collected"] = True
        return record


Adapter = AgentMessageIntakeAdapter
