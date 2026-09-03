#!/usr/bin/env python3
"""One run that parks on an ask, and resumes on a decision.

The run is here so the harness has something to suspend. It is three steps -
draft, gate, publish - and the gate is the only interesting one: the run emits an
ask and then *stops*, holding no connection to anyone. The pause is a state of
the run, not a call the client makes (X-cap-human-interaction-003).

Two objects, on purpose. `park_run()` builds the ask and returns; the object that
did it is then thrown away. `resume_run()` is constructed from the store and the
decision alone, which is what proves the parked state belongs to the platform and
not to whoever was holding the screen: between the two calls the surface may
crash, reload or be replaced by a different one entirely
(X-entry-composition-022).

Nothing in here branches on which surface served. No product name appears in this
file. Python 3.11 standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from interface import HumanAsk, HumanSurface, ResumeAck, StreamEvent


@dataclass
class RunResult:
    correlation_id: str
    outcome: str                    # published | rejected | expired
    artifact: dict = field(default_factory=dict)
    steps: list[str] = field(default_factory=list)
    resumed_from: str = ""          # where the artifact came from: store | client-held copy
    problem: dict | None = None


def draft(payload: dict) -> dict:
    """Step 1. What the agent proposes. The human publishes; the agent does not."""
    return {"headline": payload.get("headline", "Release " + payload.get("release", "?")),
            "body": payload.get("notes", ""),
            "channel": payload.get("channel", "changelog")}


def park_run(surface: HumanSurface, envelope: dict, now: str, ask_id: str,
             deadline_at: str, allowed=None) -> HumanAsk:
    """Steps 1 and 2: draft, then park at the gate before the irreversible step.

    The events emitted before the ask are what a person watching the run sees;
    a surface that cannot show a run in flight simply shows fewer of them.
    """
    correlation_id = envelope["correlation"]["correlation_id"]
    store = surface.store
    store.emit_event("run.started", correlation_id, now,
                {"run_id": envelope["correlation"]["run_id"],
                 "entry_kind": envelope["kind"], "actor": envelope["actor"]["subject"]})
    artifact = draft(envelope["payload"])
    store.emit_event("step.progress", correlation_id, now, {"step": "draft", "state": "complete"})
    store.emit_event("tool.proposed", correlation_id, now,
                {"step": "publish", "irreversibility": "irreversible"})
    ask = HumanAsk(
        ask_id=ask_id,
        correlation_id=correlation_id,                       # the run's own id, not a new one
        prompt="Publish this release note to the public changelog?",
        # One schema, and it has to accept both things a decision may carry: the
        # edited artifact the run will publish, and a plain answer to the question.
        # additionalProperties is false, so a field nobody declared cannot ride in.
        response_schema={"$schema": "https://json-schema.org/draft/2020-12/schema",
                         "type": "object", "additionalProperties": False,
                         "properties": {"headline": {"type": "string", "minLength": 1},
                                        "body": {"type": "string"},
                                        "channel": {"type": "string"},
                                        "notes": {"type": "string"},
                                        "answer": {"type": "string"}}},
        proposed={"action": "publish the release note",
                  "diff": f"+ {artifact['headline']}\n+ {artifact['body']}",
                  "irreversibility": "irreversible",
                  "artifact": artifact},
        deadline_at=deadline_at,
        allowed_decisions=tuple(allowed) if allowed else HumanAsk.allowed_decisions,
    )
    surface.ask(ask, envelope, now)          # stored first, delivered second
    return ask                               # ... and this run object is now done


def resume_run(ack: ResumeAck, now: str, store=None) -> RunResult:
    """Step 3, in a new object built from the decision alone.

    `ack.artifact` is what the run continues with. On an edit that is the
    reviewer's body; handing this step `parked.ask["proposed"]["artifact"]`
    instead is the deliberate breakage the definition of done names.
    """
    steps = ["draft", "gate"]
    if ack.decision == "reject":
        outcome, artifact = "rejected", ack.artifact
    else:
        outcome, artifact = "published", ack.artifact
        steps.append("publish")
    if store is not None:
        store.emit_event("run.finished", ack.correlation_id, now,
                    {"outcome": outcome, "decision": ack.decision})
    return RunResult(correlation_id=ack.correlation_id, outcome=outcome, artifact=artifact,
                     steps=steps, resumed_from=ack.stamps.get("resumed_from", "store"))


def stream_types(events: list[StreamEvent]) -> list[str]:
    return [e.type for e in events]
