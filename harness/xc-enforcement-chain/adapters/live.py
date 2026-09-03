#!/usr/bin/env python3
"""Live binding: the three points that actually refuse on this host today.

This is the only file in the harness where a product may be named, and the only
way to reach one is an environment variable the operator sets:

  admission        the approval unit (approve.service, PASS.md A2) parks a
                   workflow for a person to approve, reject or return
  policy           the decision engine (OPA, PASS.md B3) - present on this host
                   but not wired into the enforcement path (A6), so the slot is
                   consulted only when POLICY_URL is set and records a no-op
                   otherwise, which is what A6 says is true
  budget           the model gateway's scoped virtual key with a hard cap
                   (LiteLLM, PASS.md B3), which terminates spend rather than
                   recording it (A4)
  call credential  the host-side broker over vsock, which holds the real key and
                   drops model and destination overrides by name (A3)

Nothing here invents a route: every endpoint is supplied whole by the operator,
and with none of them set the binding refuses with a typed problem rather than
guessing. Until this has been run on that host, every sentence about it is
claimed.
"""
from __future__ import annotations

import json
import os

from interface import (DECLARED_SLOTS, OWNERS, ChainContext, EnforcementChainAdapter,
                       Problem, Unit, evaluate)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

# The environment variable each slot is reached through. None of these has a
# default: an unset variable is a slot with no owner reachable, never a guess.
ENDPOINTS = {"identity.resolve": "IDENTITY_URL",     # nothing serves this on the host today
             "policy.decide": "POLICY_URL",          # the decision engine, off the path today
             "budget.reserve": "GATEWAY_URL",        # the scoped virtual key with a hard cap
             "telemetry.open": "TELEMETRY_URL",      # the trace backend
             "idempotency.claim": "STATE_URL",       # the hash-chained task store
             "provenance.open": "EVIDENCE_URL"}      # the append-only evidence store
ADMISSION_URL = "APPROVE_URL"                        # the approval unit at the admission point
BROKER_SOCKET = "BROKER_SOCKET"                      # the host-side broker at the call point


class HostChainAdapter(EnforcementChainAdapter):
    entity = "host chain (the approval unit, the dispatcher, the broker and the scoped key)"
    locus = "in the process that constructs the unit, calling the host's own points"
    processes_required = 1
    reach_over_unmodified = "none"
    refuses_unchained = False
    declared_gaps = ("every statement about this binding is claimed until it is run on that host",
                     "the decision engine is not on the enforcement path on this host (F-a6-04)",
                     "there is no identity field anywhere in the system (F-a6-05)")

    def __init__(self) -> None:
        super().__init__()
        self.state: dict = {}
        self.configured = [s for s in DECLARED_SLOTS if os.environ.get(ENDPOINTS[s])]

    def _post(self, url: str, body: dict) -> dict:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "no HTTP client is available in this runtime",
                          enforced_by=self.entity)
        req = URLLIB.Request(url, data=json.dumps(body).encode(),
                             headers={"content-type": "application/json",
                                      "authorization": "Bearer " + os.environ.get("GATEWAY_KEY", ""),
                                      "x-correlation-id": body["correlation"]["correlation_id"]})
        try:
            with URLLIB.urlopen(req, timeout=int(os.environ.get("CHAIN_TIMEOUT_S", "30"))) as r:
                return json.load(r)
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}",
                          retry_after_s=1, enforced_by=self.entity) from exc

    def traverse(self, point: str, unit: Unit) -> list[dict]:
        if point == "admission" and not os.environ.get(ADMISSION_URL):
            raise Problem("adapter-unavailable",
                          f"the admission point is not configured: set {ADMISSION_URL} "
                          f"(see README.md). Nothing live was reached",
                          retry_after_s=0, enforced_by=self.entity)
        if point == "call" and not os.environ.get(BROKER_SOCKET):
            raise Problem("adapter-unavailable",
                          f"the call point holds no credential source: set {BROKER_SOCKET}",
                          retry_after_s=0, enforced_by=self.entity)
        rows = []
        for slot in DECLARED_SLOTS:
            url = os.environ.get(ENDPOINTS[slot])
            if not url:
                # An owner that is not reachable is a no-op with its reason, and
                # is counted as such. It is never rendered as a passed slot.
                rows.append({"slot": slot, "outcome": "no-op", "owner_running": OWNERS[slot][0],
                             "detail": f"{ENDPOINTS[slot]} is unset: {OWNERS[slot][1]}"})
                continue
            answer = self._post(url, {"point": point, "slot": slot, "unit": unit.dict(),
                                      "correlation": unit.correlation})
            outcome = answer.get("outcome", "")
            if outcome not in ("passed", "no-op", "refused"):
                raise Problem("adapter-unavailable",
                              f"slot {slot} answered with an untyped outcome {outcome!r}",
                              enforced_by=self.entity)
            row = {"slot": slot, "outcome": outcome, "owner_running": OWNERS[slot][0],
                   "detail": answer.get("detail", "")[:200]}
            if outcome == "refused":
                suffix = answer.get("problem", {}).get("type", "").rsplit(":", 1)[-1]
                row["problem"] = {"suffix": suffix or "policy-denied",
                                  "detail": answer.get("detail", "refused by the host point"),
                                  "ext": {"correlation": unit.correlation}}
            rows.append(row)
            if outcome == "refused":
                break
        # A slot with an endpoint the host does not serve would have refused
        # above; the local evaluation below never runs for a configured slot.
        if not self.configured:
            return [{"slot": s, "outcome": o, "owner_running": OWNERS[s][0], "detail": d,
                     **({"problem": p} if p else {})}
                    for s, (o, d, p) in ((s, evaluate(s, point, unit, self.state))
                                         for s in DECLARED_SLOTS)]
        return rows

    def seal(self, context: ChainContext) -> None:
        url = os.environ.get(ENDPOINTS["provenance.open"])
        if url:
            self._post(url, {"op": "seal", "context": context.dict(),
                             "correlation": context.correlation})


Adapter = HostChainAdapter
