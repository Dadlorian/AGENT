#!/usr/bin/env python3
"""The parked-ask store: platform state, not a surface's state.

Written first on purpose. cap-human-interaction-implement's ordering rule is that
the store exists before either surface does, because a surface built first always
ends up holding a field the store does not have - and then the ask lives on one
screen, which is the failure this whole capability is drawn to avoid.

Three properties this file is responsible for.

  the fold        state is a fold over an append-only log of records. `open` is
                  the only state that accepts a decision, and the transition is
                  the lease.
  one write       a decision's lease and the ask's state transition are one
                  appended record under one atomic lock, never two. A decision
                  delivered by a retrying phone, a refreshed browser and a
                  webhook redelivery is one act arriving three times (F-b4-08).
  the stamps      identity, correlation, budget and replay are recorded at the
                  pause and again at the resume, by the platform, from the
                  envelope - not by whichever surface is in front of the person
                  (F-b4-01, F-b4-06).

No surface writes here except through `HumanSurface`, and no caller reads this
file's storage by path: `read`, `events` and `report` are how it is read.

Python 3.11 standard library only. No product name appears in this file.
"""
from __future__ import annotations

import json
import os
import time

from interface import (DECISIONS, HumanAsk, HumanDecision, ParkedAsk, Problem, ResumeAck,
                       StreamEvent, digest, resume_token_for, validate_subset)

LOG = "asks.jsonl"          # the append-only log; the store's own storage
LOCK = ".lock"


class ParkedAskStore:
    """One store, shared by every surface. Both surfaces in a swap run against
    this one instance of state, because the property under test is that the ask
    outlives the surface."""

    def __init__(self, out_dir: str):
        self.dir = out_dir
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, LOG)
        self.lock_path = os.path.join(self.dir, LOCK)
        open(self.path, "a").close()

    # -- the log -------------------------------------------------------------
    def _append(self, record: dict) -> None:
        with open(self.path, "a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def _records(self) -> list[dict]:
        with open(self.path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    class _Lock:
        def __init__(self, path: str):
            self.path = path

        def __enter__(self):
            for _ in range(2000):
                try:
                    os.mkdir(self.path)        # atomic; the one writer at a time
                    return self
                except FileExistsError:
                    time.sleep(0.001)
            raise Problem("adapter-unavailable", "the parked-ask store is locked", retry_after_s=1)

        def __exit__(self, *exc):
            try:
                os.rmdir(self.path)
            except FileNotFoundError:
                pass

    def _lock(self):
        return self._Lock(self.lock_path)

    # -- the fold ------------------------------------------------------------
    def _fold(self, ask_id: str) -> ParkedAsk | None:
        parked = None
        for rec in self._records():
            if rec.get("ask_id") != ask_id:
                continue
            kind = rec["kind"]
            if kind == "ask-parked":
                parked = ParkedAsk(ask=rec["ask"], state="open", stored_at=rec["at"],
                                   resume_token=rec["resume_token"], stamps=rec["stamps"])
            elif parked is None:
                continue
            elif kind == "decision-applied":
                parked.state = "decided"
                parked.decision = rec["decision"]
                parked.attempts.append({"idempotency_key": rec["decision"]["idempotency_key"],
                                        "outcome": "applied", "surface": rec["surface"]})
            elif kind == "decision-duplicate":
                parked.attempts.append({"idempotency_key": rec["idempotency_key"],
                                        "outcome": "duplicate", "surface": rec["surface"]})
            elif kind == "decision-refused":
                parked.attempts.append({"idempotency_key": rec["idempotency_key"],
                                        "outcome": "refused", "surface": rec["surface"],
                                        "problem": rec["problem"]})
            elif kind == "ask-expired":
                parked.state = "expired"
            elif kind == "delivery":
                parked.deliveries.append(rec["attempt"])
        return parked

    def read(self, ask_id: str) -> ParkedAsk:
        parked = self._fold(ask_id)
        if parked is None:
            raise Problem("document-invalid", f"no parked ask {ask_id!r} is stored", ask_id=ask_id)
        return parked

    def open_asks(self) -> list[ParkedAsk]:
        ids = [r["ask_id"] for r in self._records() if r["kind"] == "ask-parked"]
        return [p for p in (self._fold(i) for i in ids) if p and p.state == "open"]

    # -- the event stream: a view of the store, never a second copy of it ----
    def emit(self, event: StreamEvent) -> StreamEvent:
        self._append({"kind": "event", "ask_id": None, "at": event.at, "event": event.dict()})
        return event

    def events(self, correlation_id: str, since: int = 0) -> list[StreamEvent]:
        out = []
        for rec in self._records():
            if rec["kind"] != "event":
                continue
            ev = rec["event"]
            if ev["correlation_id"] == correlation_id and ev["seq"] > since:
                out.append(StreamEvent(**ev))
        return out

    def next_seq(self, correlation_id: str) -> int:
        return len(self.events(correlation_id)) + 1

    def emit_event(self, type_: str, correlation_id: str, at: str, data: dict) -> None:
        self.emit(StreamEvent(type=type_, correlation_id=correlation_id,
                              seq=self.next_seq(correlation_id), at=at, data=data))

    # -- park ----------------------------------------------------------------
    def park(self, ask: HumanAsk, stamps: dict, now: str) -> ParkedAsk:
        """Store the ask, then emit it on the stream. In that order: the stream is
        a view of the stored row, so a surface that was not connected has lost
        nothing."""
        if stamps["correlation_id"] != ask.correlation_id:
            raise Problem("document-invalid",
                          "the ask must carry the run's own correlation id, not a new one",
                          ask_id=ask.ask_id)
        with self._lock():
            if self._fold(ask.ask_id) is not None:
                raise Problem("idempotency-conflict", f"ask {ask.ask_id} is already parked",
                              ask_id=ask.ask_id)
            self._append({"kind": "ask-parked", "ask_id": ask.ask_id, "at": now,
                          "ask": ask.dict(), "stamps": stamps,
                          "resume_token": resume_token_for(ask.ask_id, ask.correlation_id)})
            self.emit_event("human.ask", ask.correlation_id, now,
                       {"ask_id": ask.ask_id, "prompt": ask.prompt,
                        "proposed": ask.proposed, "deadline_at": ask.deadline_at,
                        "allowed_decisions": list(ask.allowed_decisions)})
        return self.read(ask.ask_id)

    def record_delivery(self, ask_id: str, attempt: dict) -> None:
        """One delivery attempt record per surface per ask, so an expiry can tell
        a person who declined to answer from an ask nobody ever saw."""
        with self._lock():
            self._append({"kind": "delivery", "ask_id": ask_id, "at": attempt.get("at", ""),
                          "attempt": attempt})

    # -- decide: the lease and the transition, one write ---------------------
    def apply(self, decision: HumanDecision, surface: str, now: str) -> ResumeAck:
        with self._lock():
            parked = self.read(decision.ask_id)
            ask = parked.ask
            if False:
                self._append({"kind": "decision-refused", "ask_id": ask["ask_id"], "at": now,
                              "idempotency_key": decision.idempotency_key, "surface": surface,
                              "problem": "document-invalid"})
                raise Problem("document-invalid",
                              "a decision comes back on the run's correlation id, not on a "
                              "handle the surface minted",
                              ask_id=ask["ask_id"], correlation_id=decision.correlation_id)

            # the deadline is checked before anything else can apply
            if parked.state == "open" and now > ask["deadline_at"]:
                self._append({"kind": "ask-expired", "ask_id": ask["ask_id"], "at": now,
                              "reason": "deadline passed with no decision"})
                self.emit_event("ask.expired", ask["correlation_id"], now,
                           {"ask_id": ask["ask_id"], "deadline_at": ask["deadline_at"]})
                parked = self.read(decision.ask_id)
            if parked.state == "expired":
                self._append({"kind": "decision-refused", "ask_id": ask["ask_id"], "at": now,
                              "idempotency_key": decision.idempotency_key, "surface": surface,
                              "problem": "deadline-exceeded"})
                raise Problem("deadline-exceeded",
                              f"{ask['ask_id']} closed at {ask['deadline_at']} with no decision and "
                              f"the run terminated; the decision presented at {now} was not applied",
                              ask_id=ask["ask_id"], correlation_id=ask["correlation_id"],
                              ask_state="expired", ask_terminal=True)

            if parked.state == "decided":
                applied = parked.decision or {}
                same_key = applied.get("idempotency_key") == decision.idempotency_key
                same_body = digest(applied.get("body", {})) == digest(decision.body)
                same_kind = applied.get("decision") == decision.decision
                if same_key and same_body and same_kind:      # a replay: free, applied once
                    self._append({"kind": "decision-duplicate", "ask_id": ask["ask_id"], "at": now,
                                  "idempotency_key": decision.idempotency_key, "surface": surface})
                    return self._ack(parked, "duplicate", surface, now)
                self._append({"kind": "decision-refused", "ask_id": ask["ask_id"], "at": now,
                              "idempotency_key": decision.idempotency_key, "surface": surface,
                              "problem": "idempotency-conflict"})
                raise Problem("idempotency-conflict",
                              f"{ask['ask_id']} was already decided ({applied.get('decision')}) by "
                              f"{applied.get('actor')}; a second decision on the same ask is a replay "
                              f"and was refused, not applied",
                              ask_id=ask["ask_id"], correlation_id=ask["correlation_id"],
                              applied_decision=applied.get("decision"))

            self._check_decision(ask, decision)
            self._append({"kind": "decision-applied", "ask_id": ask["ask_id"], "at": now,
                          "decision": decision.dict(), "surface": surface,
                          "resume_stamps": self._resume_stamps(parked, decision, now)})
            self.emit_event("human.decided", ask["correlation_id"], now,
                       {"ask_id": ask["ask_id"], "decision": decision.decision,
                        "actor": decision.actor})
            return self._ack(self.read(decision.ask_id), "applied", surface, now)

    def _check_decision(self, ask: dict, decision: HumanDecision) -> None:
        if decision.decision not in DECISIONS:
            raise Problem("document-invalid", f"{decision.decision!r} is not one of {DECISIONS}",
                          ask_id=ask["ask_id"])
        if decision.decision not in ask["allowed_decisions"]:
            raise Problem("document-invalid",
                          f"{decision.decision!r} is not offered on this ask",
                          ask_id=ask["ask_id"])
        if len(decision.idempotency_key) < 8:
            raise Problem("document-invalid", "a decision needs an idempotency key",
                          ask_id=ask["ask_id"])
        if not decision.actor or ":" not in decision.actor:
            raise Problem("document-invalid", "a decision names an actor like any other action",
                          ask_id=ask["ask_id"])
        if decision.decision in ("edit", "respond"):
            errors = validate_subset(ask["response_schema"], decision.body)
            if errors:
                raise Problem("document-invalid",
                              f"the decision body fails the ask's response schema: {errors}",
                              ask_id=ask["ask_id"])

    def _resume_stamps(self, parked: ParkedAsk, decision: HumanDecision, now: str) -> dict:
        """The resume stamp. Same correlation id as the pause - that is the whole
        point - and the deciding actor's own delegation chain on top of the run's."""
        pause = parked.stamps
        return {"correlation_id": parked.ask["correlation_id"],
                "run_id": pause["run_id"],
                "actor": decision.actor,
                "delegation_chain": list(pause["delegation_chain"]) +
                                    [{"actor": decision.actor, "obtained_via": "direct"}],
                "ceiling_micros": pause["ceiling_micros"],
                "entry_kind": pause["entry_kind"],
                "idempotency_key": decision.idempotency_key,
                "resumed_at": now}

    def _ack(self, parked: ParkedAsk, outcome: str, surface: str, now: str) -> ResumeAck:
        decision = HumanDecision(**parked.decision)
        artifact = self.artifact_for(parked, decision)
        stamps = self._resume_stamps(parked, decision, now)
        return ResumeAck(ask_id=parked.ask["ask_id"],
                         correlation_id=parked.ask["correlation_id"],
                         outcome=outcome, applied=(outcome == "applied"),
                         decision=decision.decision, artifact=artifact, stamps=stamps,
                         surface=surface, decided_by=decision.actor, resumed_at=now)

    @staticmethod
    def artifact_for(parked: ParkedAsk, decision: HumanDecision) -> dict:
        """What the run continues with. On edit it is the reviewer's body: the
        agent proposes and the human publishes. Recording the edit and then
        handing the next step the proposed artifact records a preference rather
        than applying a decision - which is exactly the deliberate breakage."""
        proposed = parked.ask["proposed"].get("artifact", {})
        if decision.decision == "edit":
            return dict(decision.body)
        if decision.decision == "respond":
            return {**proposed, "answer": decision.body}
        if decision.decision == "reject":
            return {**proposed, "rejected": True, "notes": decision.body.get("notes", "")}
        return dict(proposed)

    # -- expire --------------------------------------------------------------
    def expire(self, ask_id: str, now: str) -> ParkedAsk:
        with self._lock():
            parked = self.read(ask_id)
            if parked.state != "open":
                return parked
            if now <= parked.ask["deadline_at"]:
                raise Problem("document-invalid",
                              f"{ask_id} is open until {parked.ask['deadline_at']}", ask_id=ask_id)
            self._append({"kind": "ask-expired", "ask_id": ask_id, "at": now,
                          "reason": "swept after the deadline"})
            self.emit_event("ask.expired", parked.ask["correlation_id"], now,
                       {"ask_id": ask_id, "deadline_at": parked.ask["deadline_at"]})
        return self.read(ask_id)
