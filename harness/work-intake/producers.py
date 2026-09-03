#!/usr/bin/env python3
"""The four producers, and the one document all of them submit.

TARGET T6.2's four entries are a human, an event, a schedule and an external
system or agent. They are four producers, not four ways in. Nothing is invented
here: the door identities and the document are read from the fixtures the
end-to-end example already ships (examples/end-to-end/entries/*.json), so the
harness and the example cannot drift apart.

  DOORS    per door: its kind, the producer's own message identity and clock,
           who is acting and the delegation chain behind them. All door fields.
  SUBJECT  the one logical job - intent, budget, payload - taken from the human
           entry and driven through every door unchanged. build-entry-conformance
           states the rule: the subject of the suite is one document, not four.

Each adapter renders this pair into its own producers' native messages; no
producer-native format appears in this file.
"""
from __future__ import annotations

import json
import os
from typing import Any

from interface import ENTRIES_DIR, ENTRY_KINDS

FIXTURES: dict[str, dict] = {
    kind: json.load(open(os.path.join(ENTRIES_DIR, f"{kind}.json"))) for kind in ENTRY_KINDS
}

# One logical job. Taken from the human fixture; every door sends this object
# unchanged, so a digest over it is recorded once and compared per door.
SUBJECT: dict[str, Any] = {k: FIXTURES["human"][k]
                           for k in ("intent", "budget", "payload", "envelope_version")}

# The door identities, straight from the fixtures. `message_identity` is the
# producer's own unique identity for the message: the event standard on file
# obliges the producer to make it unique, so intake derives the idempotency key
# from it and never mints one on arrival.
DOORS: tuple[dict[str, Any], ...] = tuple(
    {"kind": kind,
     "entry_id": FIXTURES[kind]["entry_id"],
     "occurred_at": FIXTURES[kind]["occurred_at"],
     "actor_subject": FIXTURES[kind]["actor"]["subject"],
     "chain": tuple((hop["actor"], hop["obtained_via"])
                    for hop in FIXTURES[kind]["actor"]["delegation_chain"]),
     "message_identity": FIXTURES[kind]["idempotency_key"]}
    for kind in ENTRY_KINDS)


def malformed(subject: dict) -> dict:
    """One document a producer got wrong: the task names no summary. Used for
    the typed refusal, at every door and on every binding."""
    intent = {k: v for k, v in subject["intent"].items() if k != "summary"}
    return {**subject, "intent": intent}


def other_job(subject: dict) -> dict:
    """A different job under the same producer message identity: the conflict."""
    return {**subject, "payload": {**subject["payload"], "window_hours": 999}}
