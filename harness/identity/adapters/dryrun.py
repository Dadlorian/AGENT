#!/usr/bin/env python3
"""Dry-run adapter: an exchange-issuing provider, in process, no network.

This is the first adapter of the pair. It models the provider shape recorded for
this capability: a client presents a credential it already holds, an authority
exchanges it for one scoped to the next destination, and every verification is a
call back to that authority. Deterministic: same bytes every run, so a gate can
assert on them.

What it declares it cannot do: `attest_from_platform_facts`. A client gets a
token here only by presenting a credential it already holds, so a unit the
platform can observe but that holds nothing has to be handed a secret before it
can obtain an identity at all. The subset is declared rather than answered with
something weaker.

The failure path is exercised on demand with DRYRUN_FAIL=1 (the authority is
unreachable) and the deliberate breakage with IDENTITY_BREAK=forward-token,
which this adapter can express because a bearer credential can be forwarded
unchanged.
"""
from __future__ import annotations

import os
from datetime import timedelta

from interface import (AttestRequest, Credential, DelegationRequest, Hop, IdentityAdapter, Problem,
                       TRUST, iso, now, opens, parse_time, seal)

KEY = TRUST["trust_material"]["issuer-key"]


class ExchangeIssuingAdapter(IdentityAdapter):
    entity = "in-process exchange-issuing provider"
    root_of_trust = "presented-credential-exchange"
    verification_locus = "authority-call-per-verification"
    credential_form = "bearer-token-with-nested-act-claims"
    declared_marker = "exchange-issuer"
    attested_via = "direct"
    unsupported = ("attest_from_platform_facts",)
    honours_forward_break = True

    def __init__(self):
        super().__init__()
        self._records: dict[str, dict] = {}   # what the authority remembers it issued
        self._forwarded = 0

    # --- the test seam: what an outside issuer hands a caller ----------------
    def fixture_presented(self, subject: str, scope, audience: str, lifetime_s: int,
                          obtained_via: str = "direct") -> str:
        payload = {"subject": subject, "scope": sorted(scope), "audience": audience,
                   "obtained_via": obtained_via,
                   "expires_at": iso(now() + timedelta(seconds=lifetime_s))}
        blob = seal(payload, KEY)
        self._records[blob] = payload
        return blob

    # --- 1. verify: one call to the authority, every time --------------------
    def _verify(self, presented: str) -> Credential:
        self._unreachable_if_asked()
        self.authority_calls += 1          # the axis: this binding asks an authority per verification
        payload = self._records.get(presented)
        if payload is None or not opens(presented, payload, KEY):
            self.refusals += 1
            raise Problem("identity-untrusted",
                          "the authority holds no record of this credential, so nothing about it verifies")
        self.observed_marker = self.declared_marker
        return self._mint(payload["subject"],
                          (Hop(payload["subject"], payload["obtained_via"]),),
                          payload["scope"], payload["audience"], parse_time(payload["expires_at"]))

    # --- 2. attest: exchange the credential the unit already holds -----------
    def _attest(self, request: AttestRequest) -> Credential:
        self._unreachable_if_asked()
        if not request.presented:
            self.refusals += 1
            raise Problem("adapter-unavailable",
                          "this binding issues only against a credential the unit already holds; the unit "
                          "presented none and no credential was issued",
                          retryable=False, unsupported_operation="attest_from_platform_facts",
                          unsupported=list(self.unsupported))
        held = self._verify(request.presented)
        if held.subject != request.unit:
            self.refusals += 1
            raise Problem("identity-untrusted",
                          f"the presented credential names {held.subject} and the attestation asks for "
                          f"{request.unit}; this binding cannot name a unit it did not authenticate",
                          subject=held.subject, unit=request.unit)
        expires = min(parse_time(held.expires_at),
                      now() + timedelta(seconds=request.lifetime_s))
        return self._mint(request.unit, (Hop(request.unit, self.attested_via),),
                          request.scope, request.audience, expires)

    # --- 3. delegate: one exchange, the acting party prepended ---------------
    def _delegate(self, request: DelegationRequest, expires) -> Credential:
        self._unreachable_if_asked()
        chain = (Hop(request.actor.actor, "token_exchange"),) + request.subject.chain
        if self._break_this_hop(request):
            # The deliberate breakage: forward the incoming credential unchanged
            # instead of exchanging it for the agent actor. The chain is one hop
            # short and its current actor is not the unit that will execute.
            self._forwarded += 1
            self.observed_marker = self.declared_marker
            return request.subject
        return self._mint(request.actor.actor, chain, request.scope, request.audience, expires)

    def _break_this_hop(self, request: DelegationRequest) -> bool:
        return (os.environ.get("IDENTITY_BREAK") == "forward-token"
                and request.actor.actor.startswith("agent:") and self._forwarded == 0)

    def _unreachable_if_asked(self) -> None:
        if os.environ.get("DRYRUN_FAIL") == "1":
            raise Problem("adapter-unavailable",
                          "the issuing authority was made unreachable by DRYRUN_FAIL=1; no credential was "
                          "issued and no chain was extended", retry_after_s=1)


# The one name every adapter module exports: the entry point of this module.
Adapter = ExchangeIssuingAdapter
