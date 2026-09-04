#!/usr/bin/env python3
"""Second adapter: a different serving path with a different execution model.

Where the live adapter answers inside one HTTP call, this one submits the work
to a provider's own asynchronous batch route and hands back a ticket to be
claimed later: submit -> pending, claim -> not-yet with an earliest_retry, claim
again -> redeemed. Cost is committed when the work is submitted and reconciled
when it is claimed. Nothing can be stopped once submitted, so tickets carry
cancellable false and a cancel is recorded rather than honoured.

PASS.md A4 records this path already running on this substrate: batch goes
through Gemini's native :batchGenerateContent via LiteLLM passthrough, not the
OpenAI-shaped /v1/batches route, which branches only on openai/azure/vertex_ai
and refuses Gemini (F-a4-08). Product names are allowed in this file.

Reachability: with BATCH_SUBMIT_URL and BATCH_STATUS_URL set (see README) this
adapter POSTs and polls those routes with urllib. Both are supplied whole by the
operator, because no batch route is invented here. With them unset it runs the
same state machine in process, which is what a dry run exercises: the shape and
the swap procedure are real either way.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from interface import (CancelAck, ClaimTicket, CompletionRequest, CompletionResult,
                       ModelAccessAdapter, Problem, RouteDecision, apply_mechanisms,
                       estimate_tokens_in, price_micros)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

POLLS_BEFORE_READY = int(os.environ.get("BATCH_POLLS", "2"))   # in-process simulation only


class BatchClaimAdapter(ModelAccessAdapter):
    entity = "provider-native asynchronous batch (claim-and-poll)"
    serving_path = "asynchronous-batch"
    declared_marker = "batch-job-accepted"
    declared_gaps = ("a submitted job cannot be stopped; its cost may still be owed",)

    def __init__(self):
        super().__init__()
        self._jobs: dict[str, dict] = {}

    # --- submit: post the job, return a pending ticket ----------------------
    def _submit(self, request: CompletionRequest, decision: RouteDecision, estimate: int) -> ClaimTicket:
        job_id = "job-" + hashlib.sha256((decision.member + request.digest()).encode()).hexdigest()[:16]
        url = os.environ.get("BATCH_SUBMIT_URL")
        if url:
            job_id = self._post(url, {"model": decision.member,
                                      "messages": [dict(m) for m in request.messages],
                                      "max_tokens": request.max_output_tokens})
        # Cache is a property of the prompt, known before dispatch even though the
        # rest of the result only resolves when the job is claimed - so it is
        # observed against the store here, at submit, not invented at claim.
        cache_hit = self.note_cache(request)
        self._jobs[job_id] = {"request": request, "decision": decision, "estimate": estimate,
                              "polls": 0, "cache_hit": cache_hit}
        self.observed_marker = self.declared_marker
        return ClaimTicket(
            ticket_id=job_id,
            state="pending",
            model_class=request.model_class,
            result=CompletionResult("", estimate, estimate_tokens_in(request), 0, "committed"),
            earliest_retry=self._retry_at(),
            cancellable=False,
        )

    # --- claim: poll until the result is ready ------------------------------
    def claim(self, ticket: ClaimTicket) -> ClaimTicket:
        job = self._jobs.get(ticket.ticket_id)
        if job is None:
            raise Problem("adapter-unavailable", f"no batch job {ticket.ticket_id} is known to this binding",
                          retry_after_s=30)
        if ticket.state != "pending":
            return ticket
        job["polls"] += 1
        ready, payload = self._poll(ticket.ticket_id, job)
        if not ready:
            ticket.earliest_retry = self._retry_at()
            return ticket
        request, decision = job["request"], job["decision"]
        seed = hashlib.sha256((decision.member + request.digest()).encode()).hexdigest()
        base_tokens_out = min(request.max_output_tokens, len(payload) // 4 + 1)
        mech = apply_mechanisms(request, seed, job["cache_hit"], payload, base_tokens_out)
        ticket.state = "redeemed"
        ticket.earliest_retry = None
        ticket.result = CompletionResult(mech["text"], price_micros(decision, mech["tokens_in"], mech["tokens_out"]),
                                         mech["tokens_in"], mech["tokens_out"], "reconciled",
                                         cached_tokens=mech["cached_tokens"], reasoning_tokens=mech["reasoning_tokens"],
                                         tool_calls=mech["tool_calls"], structured_output=mech["structured_output"],
                                         stream_chunks=mech["stream_chunks"])
        self.observed_marker = self.declared_marker
        return ticket

    def cancel(self, ticket: ClaimTicket) -> CancelAck:
        owed = ticket.result.cost_micros if ticket.result else 0
        if ticket.state == "pending":
            ticket.state = "cancelled"
        return CancelAck(ticket.ticket_id, "recorded", owed,
                         "the job was already submitted; the stop was recorded and the committed cost may still be owed")

    # --- the two ways this adapter can be reached ---------------------------
    def _poll(self, job_id: str, job: dict) -> tuple[bool, str]:
        url = os.environ.get("BATCH_STATUS_URL")
        if url:
            doc = self._get(url.replace("{job_id}", job_id))
            state = str(doc.get("state", doc.get("status", "")))
            if state.upper() not in ("SUCCEEDED", "COMPLETED", "DONE"):
                return False, ""
            return True, json.dumps(doc.get("response", doc))[:400]
        if job["polls"] <= POLLS_BEFORE_READY:                    # in-process state machine
            return False, ""
        request, decision = job["request"], job["decision"]
        seed = hashlib.sha256((decision.member + request.digest()).encode()).hexdigest()
        return True, (f"[class {request.model_class} / {decision.contract}] "
                      f"{request.messages[-1]['content'][:60]} -> settled overnight (seed {seed[:8]})")

    def _post(self, url: str, body: dict) -> str:
        doc = self._http(url, json.dumps(body).encode())
        job_id = doc.get("name") or doc.get("id")
        if not job_id:
            raise Problem("adapter-unavailable", "the batch route returned no job identifier", retry_after_s=30)
        return str(job_id)

    def _get(self, url: str) -> dict:
        return self._http(url, None)

    def _http(self, url: str, data: bytes | None) -> dict:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        headers = {"content-type": "application/json"}
        key = os.environ.get("BATCH_KEY")
        if key:
            headers["authorization"] = "Bearer " + key
        try:
            with URLLIB.urlopen(URLLIB.Request(url, data=data, headers=headers),
                                timeout=int(os.environ.get("BATCH_TIMEOUT_S", "120"))) as resp:
                return json.load(resp)
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc

    @staticmethod
    def _retry_at() -> str:
        base = os.environ.get("BATCH_CLOCK")                      # fixed clock keeps a dry run deterministic
        now = datetime.fromisoformat(base) if base else datetime.now(timezone.utc)
        return (now + timedelta(seconds=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# The one name every adapter module exports: the entry point of this module.
# Binding is by module, never by a per-capability class-name table (the
# divergence harness/linked/components.py used to paper over). The descriptive
# class name above stays - `binding()` reports it, so a report still says which
# adapter answered.
Adapter = BatchClaimAdapter
