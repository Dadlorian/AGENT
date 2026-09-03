#!/usr/bin/env python3
"""Dry-run adapter: deterministic completions, in process, no network, no spend.

Same bytes every run, so a gate can assert on them. Serving path is synchronous,
so submit returns a ticket that is already redeemed. Class and cap are enforced
by the interface's submit(), which every adapter inherits; this file only
produces the answer and its cost.
"""
from __future__ import annotations

import hashlib
import os

from interface import (CancelAck, ClaimTicket, CompletionRequest, CompletionResult,
                       ModelAccessAdapter, Problem, RouteDecision, estimate_tokens_in, price_micros)


class DryRunAdapter(ModelAccessAdapter):
    entity = "dry-run in-process completions"
    serving_path = "synchronous"
    declared_marker = "dryrun-completions"

    def _submit(self, request: CompletionRequest, decision: RouteDecision, estimate: int) -> ClaimTicket:
        if os.environ.get("DRYRUN_FAIL") == "1":       # the failure path, exercised on demand
            raise Problem("adapter-unavailable",
                          "the dry-run endpoint was made unreachable by DRYRUN_FAIL=1",
                          model_class=request.model_class, retry_after_s=1)
        seed = hashlib.sha256((decision.member + request.digest()).encode()).hexdigest()
        tokens_in = estimate_tokens_in(request)
        tokens_out = min(request.max_output_tokens, 40 + int(seed[:2], 16) % 24)
        text = (f"[class {request.model_class} / {decision.contract}] "
                f"{request.messages[-1]['content'][:60]} -> settled in {tokens_out} tokens (seed {seed[:8]})")
        self.observed_marker = self.declared_marker    # what the response said
        return ClaimTicket(
            ticket_id="tkt-" + seed[:16],
            state="redeemed",
            model_class=request.model_class,
            result=CompletionResult(text, price_micros(decision, tokens_in, tokens_out),
                                    tokens_in, tokens_out, "reconciled"),
            cancellable=False,
        )

    def claim(self, ticket: ClaimTicket) -> ClaimTicket:
        return ticket                                   # already redeemed when submit returned

    def cancel(self, ticket: ClaimTicket) -> CancelAck:
        owed = ticket.result.cost_micros if ticket.result else 0
        return CancelAck(ticket.ticket_id, "recorded", owed,
                         "the work had already finished when submit returned; the stop was recorded only")
