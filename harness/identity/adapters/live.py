#!/usr/bin/env python3
"""Live adapter for the identity component on this host today: there is none.

PASS.md B3 records the adapter for Identity as *absent* (F-b3-14) and PASS.md A6
records "No identity field anywhere in the system" (F-a6-05). So this adapter's
first job is to say so, with a typed refusal, rather than to imply that
something answered. It is the only file here that may name a product, and today
it names none, because none is running.

Reached only through the environment variables in README.md:

  IDENTITY_ISSUER_URL      the token endpoint of an OIDC provider serving the
                           RFC 8693 token-exchange grant
  IDENTITY_ISSUER_TOKEN    the platform's own actor credential, sent as a bearer
  IDENTITY_INTROSPECT_URL  where a presented credential is checked
  WORKLOAD_API_SOCKET      a workload API socket, for the attestation form

With none of them set, every operation returns adapter-unavailable naming the
absence. With them set, the exchange is a real POST of the token-exchange grant:

    grant_type=urn:ietf:params:oauth:grant-type:token-exchange
    subject_token=<the principal the work is done for>
    actor_token=<the agent that will act>
    scope, audience

The grant type and the subject_token / actor_token pair are sourced
(X-cap-identity-002, X-cross-structure-036: "delegation is impossible with only
a subject_token and no actor_token"). Everything about the response - the
access_token and expires_in field names, and whether the returned token's act
claims can be read back - is unverified from here and recorded as a declared
gap: no request in this file has ever reached a provider from this environment.

Standard library only; the import is guarded so this module never breaks a dry
run on a host with no network stack.
"""
from __future__ import annotations

import json
import os
import urllib.parse
from datetime import timedelta

from interface import (AttestRequest, DelegationRequest, Hop, IdentityAdapter, Problem,
                       iso, now, parse_time)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"
ABSENT = ("PASS.md B3 records the adapter for Identity as absent and PASS.md A6 records no identity "
          "field anywhere in the system: nothing on this host issues, exchanges or verifies an actor. "
          "Point IDENTITY_ISSUER_URL and IDENTITY_ISSUER_TOKEN at a provider that serves the "
          "token-exchange grant, or WORKLOAD_API_SOCKET at a workload API, and run this again")


class LiveIssuerAdapter(IdentityAdapter):
    entity = "the identity component on this host (absent today)"
    root_of_trust = "presented-credential-exchange"
    verification_locus = "authority-call-per-verification"
    credential_form = "bearer-token-with-nested-act-claims"
    declared_marker = "live-issuer"
    attested_via = "direct"
    unsupported = ("attest_from_platform_facts",)
    honours_forward_break = False
    declared_gaps = ("the response field names and the act claims of a returned token are unverified: no "
                     "request from this file has reached a provider from this environment",)

    # --- the test seam has nothing to stand in for when nothing runs --------
    def fixture_presented(self, subject: str, scope, audience: str, lifetime_s: int,
                          obtained_via: str = "direct") -> str:
        self._absent_unless_configured()
        # A live run presents a credential the operator supplies; nothing is minted here.
        blob = os.environ.get("IDENTITY_PRESENTED_CREDENTIAL")
        if not blob:
            raise Problem("adapter-unavailable",
                          "IDENTITY_PRESENTED_CREDENTIAL is not set: a live run presents a credential the "
                          "operator holds; this adapter mints no fixtures", retryable=False)
        return blob

    # --- 1. verify --------------------------------------------------------
    def _verify(self, presented: str):
        self._absent_unless_configured()
        url = self._env("IDENTITY_INTROSPECT_URL")
        self.authority_calls += 1
        doc = self._post(url, {"token": presented})
        if not doc.get("active", False):
            self.refusals += 1
            raise Problem("identity-untrusted", "the provider reports this credential is not active")
        subject = doc.get("sub") or ""
        chain = tuple(Hop(hop["actor"], hop.get("obtained_via", "token_exchange"))
                      for hop in doc.get("chain", [{"actor": subject, "obtained_via": "direct"}]))
        self.observed_marker = self.declared_marker
        return self._mint(subject, chain, tuple(sorted((doc.get("scope") or "").split())),
                          doc.get("aud", ""), parse_time(doc["expires_at"]))

    # --- 2. attest --------------------------------------------------------
    def _attest(self, request: AttestRequest):
        self._absent_unless_configured()
        if not request.presented:
            self.refusals += 1
            raise Problem("adapter-unavailable",
                          "this binding issues only against a credential the unit already holds",
                          retryable=False, unsupported_operation="attest_from_platform_facts",
                          unsupported=list(self.unsupported))
        return self._exchange(subject_token=request.presented, actor_token=request.presented,
                              scope=request.scope, audience=request.audience,
                              actor=request.unit, chain=(Hop(request.unit, self.attested_via),),
                              expires=now() + timedelta(seconds=request.lifetime_s))

    # --- 3. delegate ------------------------------------------------------
    def _delegate(self, request: DelegationRequest, expires):
        self._absent_unless_configured()
        chain = (Hop(request.actor.actor, "token_exchange"),) + request.subject.chain
        return self._exchange(subject_token=request.subject.handle, actor_token=request.actor.handle,
                              scope=request.scope, audience=request.audience,
                              actor=request.actor.actor, chain=chain, expires=expires)

    # --- the one request this file makes ----------------------------------
    def _exchange(self, subject_token, actor_token, scope, audience, actor, chain, expires):
        url = self._env("IDENTITY_ISSUER_URL")
        doc = self._post(url, {"grant_type": GRANT_TYPE,
                               "subject_token": subject_token,
                               "actor_token": actor_token,
                               "scope": " ".join(scope),
                               "audience": audience})
        if "access_token" not in doc:
            raise Problem("adapter-unavailable",
                          f"the provider returned no access_token: {sorted(doc)[:6]}", retryable=False)
        if "expires_in" in doc:
            expires = min(expires, now() + timedelta(seconds=int(doc["expires_in"])))
        self.observed_marker = self.declared_marker
        return self._mint(actor, chain, scope, audience, expires)

    def _post(self, url: str, form: dict) -> dict:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retryable=False)
        data = urllib.parse.urlencode(form).encode()
        headers = {"content-type": "application/x-www-form-urlencoded",
                   "authorization": "Bearer " + self._env("IDENTITY_ISSUER_TOKEN"),
                   "x-correlation-id": os.environ.get("CORRELATION_ID", "corr-harness-identity"),
                   "x-run-id": os.environ.get("RUN_ID", "run-harness-identity")}
        try:
            with URLLIB.urlopen(URLLIB.Request(url, data=data, headers=headers),
                                timeout=int(os.environ.get("IDENTITY_TIMEOUT_S", "30"))) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:400].decode("utf-8", "replace")
            if exc.code in (400, 401, 403):
                raise Problem("identity-untrusted",
                              f"the provider refused the exchange: HTTP {exc.code} {detail}") from exc
            raise Problem("adapter-unavailable", f"HTTP {exc.code}: {detail}", retry_after_s=30) from exc
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc

    def _absent_unless_configured(self) -> None:
        if not (os.environ.get("IDENTITY_ISSUER_URL") or os.environ.get("WORKLOAD_API_SOCKET")):
            self.refusals += 1
            raise Problem("adapter-unavailable", ABSENT, retryable=False,
                          issued_at=iso(now()), what_is_missing="identity component")

    def _env(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise Problem("adapter-unavailable", f"{name} is not set; {ABSENT}", retryable=False)
        return value


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveIssuerAdapter
