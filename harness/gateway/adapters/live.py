#!/usr/bin/env python3
"""Live adapter for the model gateway running on this host today.

Product names are allowed in this file and nowhere else. Today that gateway is
LiteLLM (PASS.md A1: service gateway-litellm-1, image
ghcr.io/berriai/litellm-database:v1.97.0, bound to 127.0.0.1:4000, one
OpenAI-compatible API over every provider; F-a1-02), with a companion cli-bridge
exposing coding CLIs as chat-completions endpoints behind the same class prefix
(F-a1-03). Reached only through the environment variables in README.md.

Serving path is synchronous: one POST /v1/chat/completions, one redeemed ticket.
Standard library only; the import is guarded so this module never breaks a
dry run on a host with no network stack available.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import (CancelAck, ClaimTicket, CompletionRequest, CompletionResult,
                       ModelAccessAdapter, Problem, RouteDecision, estimate_tokens_in, price_micros)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None


class LiveGatewayAdapter(ModelAccessAdapter):
    entity = "model gateway on this host (LiteLLM today)"
    serving_path = "synchronous"
    declared_marker = "gateway-routed-member"
    declared_gaps = ("cost is reconciled only when the gateway response carries a cost field",)

    def _env(self, name: str, default: str | None = None) -> str:
        value = os.environ.get(name, default)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the live gateway cannot be reached and no spend was incurred",
                          retry_after_s=30)
        return value

    def _submit(self, request: CompletionRequest, decision: RouteDecision, estimate: int) -> ClaimTicket:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        url = self._env("GATEWAY_URL").rstrip("/") + "/v1/chat/completions"
        # The routed member is what the gateway's group is named; the caller only ever sent a class.
        body = json.dumps({"model": decision.member,
                           "messages": [dict(m) for m in request.messages],
                           "max_tokens": request.max_output_tokens}).encode()
        headers = {"content-type": "application/json",
                   # The scoped virtual key carries the group's hard budget cap (F-a4-07):
                   # the gateway-side enforcement point behind the platform's pre-dispatch check.
                   "authorization": "Bearer " + self._env("GATEWAY_KEY"),
                   # Correlation rides on an explicit header, never on trace parentage (F-a7-02).
                   "x-correlation-id": os.environ.get("CORRELATION_ID", "corr-harness-gateway"),
                   "x-run-id": os.environ.get("RUN_ID", "run-harness-gateway")}
        req = URLLIB.Request(url, data=body, headers=headers)
        try:
            with URLLIB.urlopen(req, timeout=int(os.environ.get("GATEWAY_TIMEOUT_S", "120"))) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:                     # a cap hit at the gateway lands here
            detail = exc.read()[:400].decode("utf-8", "replace")
            if exc.code in (402, 429) and "budget" in detail.lower():
                raise Problem("budget-exhausted",
                              f"the scoped key refused the call at the gateway: {detail}",
                              model_class=request.model_class, ceiling_micros=request.ceiling_micros,
                              enforcement_point="gateway-scoped-key") from exc
            raise Problem("adapter-unavailable", f"HTTP {exc.code}: {detail}", retry_after_s=30) from exc
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc
        usage = data.get("usage", {}) or {}
        tokens_in = int(usage.get("prompt_tokens", 0)) or estimate_tokens_in(request)
        tokens_out = int(usage.get("completion_tokens", 0)) or 1
        reported = data.get("cost")
        cost = int(round(float(reported) * 1_000_000)) if reported is not None \
            else price_micros(decision, tokens_in, tokens_out)
        self.observed_marker = self.declared_marker if data.get("model") else ""
        return ClaimTicket(
            ticket_id="tkt-" + hashlib.sha256((str(data.get("id", "")) + request.idempotency_key).encode()).hexdigest()[:16],
            state="redeemed",
            model_class=request.model_class,
            result=CompletionResult(data["choices"][0]["message"]["content"], cost, tokens_in, tokens_out,
                                    "reconciled" if reported is not None else "committed"),
            cancellable=False,
        )

    def claim(self, ticket: ClaimTicket) -> ClaimTicket:
        return ticket                                   # already redeemed when the POST returned

    def cancel(self, ticket: ClaimTicket) -> CancelAck:
        owed = ticket.result.cost_micros if ticket.result else 0
        return CancelAck(ticket.ticket_id, "recorded", owed,
                         "the completion had already returned; the stop was recorded only")


# The one name every adapter module exports: the entry point of this module.
# Binding is by module, never by a per-capability class-name table (the
# divergence harness/linked/components.py used to paper over). The descriptive
# class name above stays - `binding()` reports it, so a report still says which
# adapter answered.
Adapter = LiveGatewayAdapter
