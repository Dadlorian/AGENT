#!/usr/bin/env python3
"""Second adapter: attested workload identity, with a different execution model.

Where the first adapter exchanges a credential the client already holds and asks
an authority to verify every presentation, this one issues only after the
platform has observed where a unit runs, and then verifies a presented document
locally against distributed trust material with no call to an authority at all.
Those are the axes the swap proof measures: the root of trust, where a
verification happens, and how many authority calls one run costs.

PASS.md B3 names SPIFFE/SPIRE as the swap candidate for Identity (F-b3-14).
Product names are allowed in this file: SPIRE agents attest a workload against
platform facts and issue a short-lived SVID, peers verify presented SVIDs
locally against distributed trust bundles, and the Delegated Identity API issues
to workloads the agent cannot attest in place. Nothing of that runs on this
host, so this adapter runs the same state machine in process; with
WORKLOAD_API_SOCKET set it probes the socket first and returns a typed refusal
rather than inventing a wire protocol it has never spoken (see README.md).

What it declares it cannot do: `attest_from_presented_credential`. A bearer
credential a unit hands over is not a platform fact, and this binding ties an
identity to conditions it observed itself. The subset is declared, not answered
with something weaker.

On the chain: an X.509 identity document names one workload and cannot express
an on-behalf-of chain. This adapter is the document-with-claims form, which
cap-identity-implement records as the open question on that limit; the chain
rides in the document's claims, so delegate is served here rather than declared
unsupported. The X.509 form would declare it instead, and the report's
`unsupported` list is where that difference would show.
"""
from __future__ import annotations

import os
from datetime import timedelta

from interface import (AttestRequest, DelegationRequest, Hop, IdentityAdapter, Problem,
                       TRUST, iso, now, opens, parse_time, seal)

BUNDLE = TRUST["trust_material"]["trust-bundle"]


class AttestedWorkloadAdapter(IdentityAdapter):
    entity = "attested workload identity with a local trust bundle"
    root_of_trust = "platform-fact-attestation"
    verification_locus = "local-trust-bundle"
    credential_form = "signed-document-with-chain-claims"
    declared_marker = "workload-attestor"
    attested_via = "workload_attestation"
    unsupported = ("attest_from_presented_credential",)
    honours_forward_break = False
    forward_break_refusal = ("a document this binding issues names the unit it attested as the current "
                             "actor; there is no incoming token for it to forward unchanged")

    def __init__(self):
        super().__init__()
        self._bundle: dict[str, dict] = {}     # the trust material every peer holds a copy of

    # --- the test seam: what arrives at the door from outside ---------------
    def fixture_presented(self, subject: str, scope, audience: str, lifetime_s: int,
                          obtained_via: str = "direct") -> str:
        payload = {"subject": subject, "scope": sorted(scope), "audience": audience,
                   "obtained_via": obtained_via,
                   "expires_at": iso(now() + timedelta(seconds=lifetime_s))}
        blob = seal(payload, BUNDLE)
        self._bundle[blob] = payload           # distributed to peers, not held by an authority
        return blob

    # --- 1. verify: locally, against the bundle, no authority call ----------
    def _verify(self, presented: str) -> "object":
        self._probe_socket_if_named()
        payload = self._bundle.get(presented)
        if payload is None or not opens(presented, payload, BUNDLE):
            self.refusals += 1
            raise Problem("identity-untrusted",
                          "no trust material in the local bundle verifies this document")
        self.observed_marker = self.declared_marker
        return self._mint(payload["subject"], (Hop(payload["subject"], payload["obtained_via"]),),
                          payload["scope"], payload["audience"], parse_time(payload["expires_at"]))

    # --- 2. attest: only after the platform has observed the unit -----------
    def _attest(self, request: AttestRequest):
        self._probe_socket_if_named()
        if not (request.platform_facts or request.vouched_by):
            self.refusals += 1
            raise Problem("adapter-unavailable",
                          "this binding issues only against platform facts it observed itself, or to an "
                          "already-attested party vouching for a unit it cannot observe in place; neither "
                          "was supplied and no credential was issued",
                          retryable=False, unsupported_operation="attest_from_presented_credential",
                          unsupported=list(self.unsupported))
        if request.vouched_by is not None and not request.platform_facts:
            if request.vouched_by.remaining_s() <= 0:
                self.refusals += 1
                raise Problem("identity-untrusted",
                              f"the vouching party {request.vouched_by.subject} presented a credential that "
                              f"expired at {request.vouched_by.expires_at}",
                              subject=request.vouched_by.subject)
        expires = now() + timedelta(seconds=request.lifetime_s)
        return self._mint(request.unit, (Hop(request.unit, self.attested_via),),
                          request.scope, request.audience, expires)

    # --- 3. delegate: a fresh document each hop, chain in its claims --------
    def _delegate(self, request: DelegationRequest, expires):
        self._probe_socket_if_named()
        chain = (Hop(request.actor.actor, "token_exchange"),) + request.subject.chain
        return self._mint(request.actor.actor, chain, request.scope, request.audience, expires)

    def _probe_socket_if_named(self) -> None:
        """With WORKLOAD_API_SOCKET set, say what is really there rather than pretend.

        No SVID wire protocol is spoken here: it has never been spoken from this
        environment, so this returns a typed refusal naming what is missing.
        """
        socket_path = os.environ.get("WORKLOAD_API_SOCKET")
        if not socket_path:
            return
        raise Problem("adapter-unavailable",
                      f"WORKLOAD_API_SOCKET={socket_path} names a workload API this adapter has never "
                      f"spoken to: the SVID fetch protocol is not implemented here, and no credential was "
                      f"issued. Unset the variable to run the same state machine in process.",
                      retryable=False, socket_path=socket_path)


# The one name every adapter module exports: the entry point of this module.
Adapter = AttestedWorkloadAdapter
