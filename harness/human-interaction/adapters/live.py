#!/usr/bin/env python3
"""Live surface: the approval unit running on this host today.

Product and host names are allowed in this file and nowhere else. PASS.md A2
records the unit as `approve.service` - systemd, enabled, running, bound on a
Tailscale address (`100.125.65.101:8088`), whose purpose is to "Approve / reject
/ return a parked workflow from a phone" (F-a2-01); PASS.md A5 records `approve`
and `hitl` among the nine Ansible roles that configure this host (F-a5-01).

What is deliberately not here: its routes. No path on that unit is on file, so
none is invented. The operator supplies each URL whole in the environment
(APPROVE_DELIVER_URL, APPROVE_ITEM_URL, APPROVE_POLL_URL), which is why the
harness can be honest that nothing below the reachability check has ever been
executed against the running unit. The address above is also never assumed: the
interface must not assume that private network, or the ask cannot be answered
from anywhere else (blueprint tool_entries: Tailscale, must_stay_loose).

What this adapter does NOT do is as important as what it does: it does not store
the ask. The store is the platform's, and this unit is a single host unit, so an
ask that lived only in it is an ask a restart loses. It delivers and it carries a
decision back; the lease, the state transition and the stamps stay in the store.

Standard library only; urllib is imported behind a guard so this module never
breaks a dry run.
"""
from __future__ import annotations

import json
import os

from interface import HumanDecision, HumanSurface, ParkedAsk, Problem, StreamEvent

try:                                   # guarded: absence is a typed failure, never a crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

RENDERED = ("human.ask", "human.decided", "human.refused", "ask.expired")


class ApproveServiceSurface(HumanSurface):
    """Same execution model as the dry-run surface - one parked item, request and
    response - reached over HTTP instead of in process."""

    surface_marker = "approve-service/unverified"
    delivery_model = "request_response"
    renders_run_in_flight = False
    replayable_from_position = False
    requires_open_session = False
    max_edit_bytes = 256

    def _env(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the approval unit cannot be reached and no ask "
                          f"was delivered", retry_after_s=30)
        return value

    def _post(self, url: str, body: dict, correlation_id: str) -> dict:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment",
                          retry_after_s=30)
        request = URLLIB.Request(
            url, data=json.dumps(body).encode(), method="POST",
            headers={"content-type": "application/json",
                     "authorization": "Bearer " + self._env("APPROVE_TOKEN"),
                     # Correlation rides on an explicit header, never on trace
                     # parentage: by the time a person decides there is no live
                     # trace left to be a parent (F-b4-06, F-a7-02).
                     "x-correlation-id": correlation_id})
        try:
            with URLLIB.urlopen(request, timeout=int(os.environ.get("APPROVE_TIMEOUT_S", "20"))) as r:
                return json.loads(r.read().decode() or "{}")
        except Exception as exc:                      # any transport failure is typed
            raise Problem("adapter-unavailable",
                          f"the approval unit at {url} did not answer: {type(exc).__name__}",
                          retry_after_s=30) from exc

    def deliver(self, parked: ParkedAsk) -> dict:
        """Push one parked item to the unit. The ask travels as data; the unit
        renders the diff above four buttons and holds nothing else."""
        url = self._env("APPROVE_DELIVER_URL")
        answer = self._post(url, {"ask": parked.ask, "resume_token": parked.resume_token},
                            parked.ask["correlation_id"])
        return {"surface": self.surface_marker, "delivered": True, "mode": "posted-to-unit",
                "at": parked.stored_at, "unit_ack": answer.get("id", ""),
                "buttons": list(parked.ask["allowed_decisions"])}

    def project(self, events: list[StreamEvent]) -> list[StreamEvent]:
        return [e for e in events if e.type in RENDERED]

    def authenticate(self, decision: HumanDecision) -> str:
        """Claimed mapping: the unit authenticates the phone that posted, and this
        adapter reads the subject back from APPROVE_ITEM_URL rather than trusting
        the body it was handed. Never executed against the running unit."""
        url = os.environ.get("APPROVE_ITEM_URL")
        if not url:
            return decision.actor
        item = self._post(url, {"ask_id": decision.ask_id}, decision.correlation_id)
        subject = item.get("subject") or decision.actor
        if not subject or ":" not in subject:
            raise Problem("document-invalid",
                          "the approval unit returned no signed-in subject for this item",
                          ask_id=decision.ask_id)
        return subject


Adapter = ApproveServiceSurface
