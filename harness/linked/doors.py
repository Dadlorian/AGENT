#!/usr/bin/env python3
"""The four doors, and the one document that goes through all of them.

TARGET T6.2's four entries are a human, an event, a schedule and an external
system or agent. They are four producers, not four ways in: each one takes the
same subject document and returns the same envelope, differing only on the
members interface.DOOR_FIELDS names - which door, that producer's own message
identity and clock, who is acting and on whose behalf, the correlation the
platform minted, and the key that makes the submission safe to repeat.

Correlation, the ceiling and the idempotency key are stamped here, on the
platform's side of the boundary. No door offers a way to supply or decline
them, and no door has a field the others lack.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Mapping

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import ENVELOPE_VERSION, Entry, Envelope, digest  # noqa: E402

# --- the one document -------------------------------------------------------
# One fault, one thing to do about it, one ceiling. Every door sends this
# object unchanged; the digest of it is recorded once and compared per door.
SUBJECT: dict[str, Any] = {
    "intent": {
        "workflow_ref": "linked-triage/0.1",
        "summary": "Checkout returns 500 on coupon apply; triage the fault and report the cause.",
    },
    "budget": {"ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit"},
    "payload": {
        "report_text": "POST /checkout/coupon returns 500. Traceback ends at "
                       "pricing/coupon.py line 88, KeyError: 'tier'.",
        "window_hours": 12,
    },
    "envelope_version": ENVELOPE_VERSION,
}


class Door(Entry):
    """One producer. Everything a door decides is declared in these four
    attributes; the envelope it builds is assembled by the same code for all
    four, so a door cannot grow a member of its own."""

    kind = "unset"
    entry_id = "unset"
    occurred_at = "2026-09-03T00:00:00Z"
    subject_line: str = "unset"
    chain: tuple[tuple[str, str], ...] = ()

    def envelope(self, subject: Mapping[str, Any]) -> Envelope:
        key = digest({k: v for k, v in subject.items()})[7:19]
        return Envelope(
            kind=self.kind,
            entry_id=self.entry_id,
            occurred_at=self.occurred_at,
            actor={"subject": self.subject_line,
                   "delegation_chain": [{"actor": a, "obtained_via": v} for a, v in self.chain]},
            correlation={"run_id": f"run-{self.kind}-{key}",
                         "correlation_id": f"corr-{self.kind}-{key}", "depth": 0},
            idempotency_key=f"{self.entry_id}-{key}",
            intent=dict(subject["intent"]),
            budget=dict(subject["budget"]),
            payload=dict(subject["payload"]),
            envelope_version=subject["envelope_version"],
        )


class HumanDoor(Door):
    """A person types it in a chat surface."""
    kind = "human"
    entry_id = "human-checkout-500s"
    occurred_at = "2026-09-03T09:12:00Z"
    subject_line = "user:corey"
    chain = (("user:corey", "direct"),)


class EventDoor(Door):
    """An internal producer emits a structured event."""
    kind = "event"
    entry_id = "event-alert-checkout-500s"
    occurred_at = "2026-09-03T09:07:41Z"
    subject_line = "service:alerting"
    chain = (("service:alerting", "workload_attestation"),
             ("service:intake", "token_exchange"))


class ScheduleDoor(Door):
    """A recurrence rule fires."""
    kind = "schedule"
    entry_id = "schedule-nightly-fault-sweep"
    occurred_at = "2026-09-03T02:00:00Z"
    subject_line = "schedule:nightly-fault-sweep"
    chain = (("schedule:nightly-fault-sweep", "workload_attestation"),
             ("user:corey", "token_exchange"))


class ExternalDoor(Door):
    """Another system or agent submits the task."""
    kind = "external"
    entry_id = "external-partner-agent-task"
    occurred_at = "2026-09-03T09:20:15Z"
    subject_line = "agent:partner-sre-bot"
    chain = (("agent:partner-sre-bot", "workload_attestation"),
             ("service:intake", "token_exchange"),
             ("user:corey", "direct"))


DOORS: tuple[Door, ...] = (HumanDoor(), EventDoor(), ScheduleDoor(), ExternalDoor())


def envelopes(subject: Mapping[str, Any] | None = None) -> list[Envelope]:
    """One document, four envelopes."""
    return [door.envelope(subject or SUBJECT) for door in DOORS]
