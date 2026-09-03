#!/usr/bin/env python3
"""The minimal call: a run parked on a human, resumed by one decision.

    ADAPTER=dryrun  python3 harness/human-interaction/call.py
    ADAPTER=second  python3 harness/human-interaction/call.py
    ADAPTER=live    python3 harness/human-interaction/call.py     (needs the env vars in README)

It does the five things the plan's minimal call names: parks one run on an ask
with a deadline, delivers a decision through the surface, resumes the run,
presents a second decision on the same ask and gets a typed refusal, and presents
a decision after a deadline and gets another. Identity and correlation are
printed from the pause and from the resume so they can be compared.

Everything below the CALLER CODE marker is what a caller writes. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the envelope and on the decision here, and the caller never asks for them
(F-b4-01). Nothing in this file opens the store's log or an adapter's storage by
path: what a caller reads, it reads through the interface.

Python 3.11 standard library only. No product name appears in this file.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import (HumanDecision, Problem, ResumeAck, load_surface,  # noqa: E402
                       resume_token_for)
from run import park_run, resume_run  # noqa: E402
from store import ParkedAskStore  # noqa: E402

OUT = os.path.join(HERE, "out")
T_PARK = "2026-09-03T10:00:00Z"
DEADLINE = "2026-09-03T18:00:00Z"
T_DECIDE = "2026-09-03T11:30:00Z"
T_LATE = "2026-09-03T18:04:11Z"


def build_envelope(kind="human", subject="user:corey") -> dict:
    """The one envelope of cap-consumption (TARGET T6.2). The four stamps are
    applied here; a human answers the gate, but the run behind it may have
    entered through any of the four doors and nothing below branches on which."""
    from interface import Envelope
    return Envelope(
        kind=kind, entry_id="hitl-release-publish", occurred_at=T_PARK,
        actor={"subject": subject,                                    # identity
               "delegation_chain": [{"actor": subject, "obtained_via": "direct"}]},
        intent={"workflow_ref": "run.py:release-publish/0.1",
                "summary": "Draft a release note and publish it once a person agrees."},
        correlation={"run_id": "run-hitl-0001",                       # correlation
                     "correlation_id": "corr-hitl-0001", "depth": 0},
        budget={"ceiling_micros": 1_500_000, "currency": "USD",       # budget
                "on_exceed": "terminate_unit"},
        idempotency_key="hitl-release-2026.09.3",                     # replay
        payload={"release": "2026.09.3", "headline": "Release 2026.09.3",
                 "notes": "coupon pricing fix", "channel": "changelog"},
    ).dict()


def decision(ask, kind: str, body: dict, actor="user:corey") -> HumanDecision:
    """One decision, with the platform's stamps on it. The idempotency key is
    derived from the ask and the decision, not asked of the person: the same
    decision delivered ten times resumes the run once (F-b4-08)."""
    return HumanDecision(ask_id=ask.ask_id, correlation_id=ask.correlation_id,
                         decision=kind, actor=actor,
                         idempotency_key=f"dec-{ask.ask_id}-{kind}", body=body)


def fresh(path: str) -> str:
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    return path


def report(adapter, surface, pause, ack: ResumeAck, dup: ResumeAck, result,
           seen, replay: dict, expired: dict) -> int:
    """Presentation. Every value below came from the interface: the parked row,
    the resume acknowledgement, the projected stream, or a problem body."""
    binding = surface.binding()
    print(f"\nADAPTER={adapter}  surface={binding['surface_marker']}  "
          f"({binding['delivery_model']}, selected_by={binding['selected_by']})")
    rows = [
        ("pause", f"ask {pause.ask['ask_id']} parked, state {pause.state}",
         f"deadline {pause.ask['deadline_at']}", f"{len(pause.deliveries)} delivery attempt"),
        ("stamped", f"correlation {pause.stamps['correlation_id']}",
         f"actor {pause.stamps['actor']}", f"ceiling {pause.stamps['ceiling_micros']} micros"),
        ("decision", f"{ack.decision} by {ack.decided_by}", f"outcome {ack.outcome}",
         f"applied {ack.applied}"),
        ("resume", f"correlation {ack.stamps['correlation_id']}",
         f"actor {ack.stamps['actor']}", f"chain {len(ack.stamps['delegation_chain'])} hops"),
        ("same id", f"pause == resume: "
                    f"{pause.stamps['correlation_id'] == ack.stamps['correlation_id']}",
         f"resume token {resume_token_for(ack.ask_id, ack.correlation_id)[:14]}",
         "derived, not minted"),
        ("run", f"{result.outcome} after {len(result.steps)} steps",
         f"artifact headline: {result.artifact.get('headline', '')[:34]}",
         f"from the {result.resumed_from}"),
        ("replayed", f"same decision again -> {dup.outcome}", f"applied {dup.applied}",
         "one act, delivered twice"),
        ("refused", f"second decision -> {replay['type'].rsplit(':', 1)[-1]}",
         f"status {replay.get('status')}", f"retryable {replay.get('retryable')}"),
        ("expired", f"late decision -> {expired['type'].rsplit(':', 1)[-1]}",
         f"status {expired.get('status')}", f"terminal {expired.get('ask_terminal')}"),
        ("watched", f"{len(seen)} events on this surface",
         ",".join(sorted({e.type for e in seen}))[:44], "each carries a type"),
    ]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(w) for c, w in zip(r, (10, 44, 40, 26))))
    ok = (ack.applied and not dup.applied
          and pause.stamps["correlation_id"] == ack.stamps["correlation_id"]
          and result.artifact.get("headline") == "Coupon pricing fix, reviewed by a person"
          and replay["type"].endswith("idempotency-conflict")
          and expired["type"].endswith("deadline-exceeded"))
    print("  " + ("OK" if ok else "FAILED") + ": the run resumed on its own correlation id, the "
          "edit is what it published, and both late arrivals were typed refusals")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = os.environ.get("ADAPTER", "dryrun")               # configuration, not code
    store = ParkedAskStore(fresh(os.path.join(OUT, "call-" + adapter)))
    surface = load_surface(adapter, store)                      # one name, one binding
    envelope = build_envelope()
    try:
        ask = park_run(surface, envelope, T_PARK, "ask-release-0001", DEADLINE)
        late = park_run(surface, envelope, T_PARK, "ask-changelog-0002", DEADLINE)
        edit = decision(ask, "edit", {"headline": "Coupon pricing fix, reviewed by a person",
                                      "body": "Coupon pricing is fixed.", "channel": "changelog"})
        pause = store.read(ask.ask_id)                          # the parked row, as stored
        ack = surface.decide(edit, T_DECIDE)                    # one decision, one resume
        dup = surface.decide(edit, T_DECIDE)                    # the same one again: free
        result = resume_run(ack, T_DECIDE, store)               # the run continues, same id
        seen = surface.watch(ask.correlation_id)                # what this surface shows
    except Problem as problem:                                  # one refusal shape, typed
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    try:
        surface.decide(decision(ask, "approve", {}), T_DECIDE)  # a second, different decision
        replay = {"type": "none: a second decision was applied"}
    except Problem as problem:
        replay = problem.body
    try:
        surface.decide(decision(late, "approve", {}), T_LATE)   # after the deadline
        expired = {"type": "none: a late decision was applied"}
    except Problem as problem:
        expired = problem.body
    return report(adapter, surface, pause, ack, dup, result, seen, replay, expired)


if __name__ == "__main__":
    sys.exit(main())
