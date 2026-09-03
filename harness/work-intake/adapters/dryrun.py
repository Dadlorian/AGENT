#!/usr/bin/env python3
"""Dry-run binding: the request-pushed producers, in process, no network.

The same execution model as the intake path this deployment runs today - a
producer builds a message, hands it over in one hop, and gets an acknowledgement
back inside that hop - with the four producers PASS.md B3 records mapped one
each: a command line, a repository event, a schedule occurrence and a formatted
event pushed over a request. Deterministic: same bytes every run, so a gate can
assert on them.

Every mapper here does the same three things: take the producer's own message
identity and clock, take the job unchanged, and drop everything else. The
refusal, the schema check and the replay check are the interface's, not this
file's.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

from interface import Envelope, Problem, ProducerMessage, WorkIntakeAdapter, digest

# One mapper per producer, and the door each one serves.
MAPPERS = {"human": "cli-argv", "event": "git-event",
           "schedule": "schedule-occurrence", "external": "cloudevents-http"}


class RequestPushedIntakeAdapter(WorkIntakeAdapter):
    entity = "request-pushed producers (a message built, handed over, acknowledged in one hop)"
    execution_model = "synchronous-request-pushed"
    declared_marker = "entry-recorded-in-request"
    ack_delivery = "in-request"
    idempotency_source = "the producer's own message identity (source plus id)"
    registered_mappers = tuple(MAPPERS.values())

    # --- the producer side --------------------------------------------------
    def render_message(self, door: Mapping[str, Any], subject: Mapping[str, Any]) -> ProducerMessage:
        """How each of these four producers expresses one document natively."""
        fmt = MAPPERS[door["kind"]]
        job = {"intent": subject["intent"], "budget": subject["budget"],
               "payload": subject["payload"], "envelope_version": subject["envelope_version"]}
        common = {"message_id": door["entry_id"],
                  "message_identity": door["message_identity"], "time": door["occurred_at"],
                  "submitter": door["actor_subject"],
                  "on_behalf_of": [list(hop) for hop in door["chain"]],
                  "job": job,
                  # A producer-specific attribute, sent on every message. It is
                  # mapped onto an envelope field or it is dropped; it never
                  # rides along.
                  "priority": "high"}
        bodies = {
            "cli-argv": {**common, "argv": ["submit", "--intent", subject["intent"].get("summary", "")]},
            "git-event": {**common, "event": "workflow_run", "repository": "the-repository"},
            "schedule-occurrence": {**common, "recurrence": subject["payload"].get("recurrence", "")},
            "cloudevents-http": {**common, "specversion": "1.0", "type": "job.submitted",
                                 "source": "/producers/" + door["kind"], "id": door["entry_id"]},
        }
        transport = {"handle": f"transport-handle-{door['kind']}-0001",
                     "content_type": "application/json"}
        return ProducerMessage(fmt, bodies[fmt], transport)

    # --- normalise ----------------------------------------------------------
    def normalise(self, message: ProducerMessage) -> Envelope:
        body = message.body
        job = body["job"]
        kind = next(k for k, fmt in MAPPERS.items() if fmt == message.format)
        key = digest(job)[7:19]
        return Envelope(
            kind=kind,
            # The producer's own message identity, never minted here.
            entry_id=body["message_id"],
            occurred_at=body["time"],
            actor={"subject": body["submitter"],
                   "delegation_chain": [{"actor": a, "obtained_via": v} for a, v in body["on_behalf_of"]]},
            intent=dict(job["intent"]),
            correlation={"run_id": f"run-{kind}-{key}", "correlation_id": f"corr-{kind}-{key}", "depth": 0},
            budget=dict(job["budget"]),
            idempotency_key=body["message_identity"],
            payload=dict(job["payload"]),
            envelope_version=job["envelope_version"],
        )

    def _record(self, envelope: Envelope) -> str:
        if os.environ.get("INTAKE_FAIL") == "1":       # the failure path, exercised on demand
            raise Problem("adapter-unavailable",
                          "the dry-run intake path was made unreachable by INTAKE_FAIL=1; "
                          "nothing was admitted",
                          retry_after_s=1)
        return self.declared_marker


# The one name every adapter module exports: the entry point of this module.
Adapter = RequestPushedIntakeAdapter
