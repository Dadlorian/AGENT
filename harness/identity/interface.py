#!/usr/bin/env python3
"""Identity: every action names an actor, and the chain that produced the right
to act travels with the call.

Read it in this order. Credential is the whole caller vocabulary: a handle, a
subject, a chain, a scope, one audience and an expiry. There is no token field,
no certificate, no issuer and no trust material on it, so nothing a caller holds
can be replayed and nothing it prints can leak a secret (X-cross-structure-006).

Three operations, the ones cap-identity's contract names:

  verify(presented)   the only way an actor comes into existence here. An actor
                      object a caller constructed is an assertion, never a fact.
  attest(request)     a unit of work gets a short-lived credential naming it.
  delegate(request)   a subject credential plus an actor credential yield one
                      scoped credential for one destination, with the acting
                      party prepended to the chain (F-b3-14, X-entry-composition-048).

attest, delegate and verify are concrete template methods here. Scope narrowing,
lifetime shortening, acyclicity, single-audience and expiry are checked in front
of every adapter, so no adapter can decline them, and each adapter supplies only
the minting and the trust resolution underneath (_attest, _delegate, _verify).

What this file deliberately does NOT do: it does not re-derive the chain the
adapter returned. The delegation-chain corpus in conformance.py is where a hop
that forwarded an incoming token unchanged is caught, which is the check
cap-identity-implement's definition of done words as P13.

No product name, issuer, endpoint or trust-domain URL appears in this file
(T-t7-02, F-b1-02). Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

INTERFACE_VERSION = "0.1"
HERE = os.path.dirname(os.path.abspath(__file__))
TRUST = json.load(open(os.path.join(HERE, "trust.json")))
SCOPE_VOCABULARY = tuple(TRUST["scope_vocabulary"])
ROOT_OBTAINED_VIA = tuple(TRUST["root_obtained_via"])

# --- Typed failures: RFC 9457 problem details, from the closed registry -------
# docs/decomposition.md 2.1.6. Nothing new is invented here: a declared
# conformance subset is reported as adapter-unavailable with retryable false,
# which that section explicitly allows ("a 503 that is not retryable must say so").
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "The request is not a well-formed identity request", False),
    "identity-untrusted": (401, "The delegation chain does not verify", False),
    "policy-denied": (403, "A hop asked for more than it was given", False),
    "adapter-unavailable": (503, "No identity adapter can serve this operation", True),
    "identity-withdrawn": (403, "The identity used for this call has been withdrawn", False),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, retryable: bool | None = None, **ext):
        status, title, default_retryable = REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail,
                     "retryable": default_retryable if retryable is None else retryable,
                     **ext}
        super().__init__(detail)


# --- The caller vocabulary ---------------------------------------------------
SUBJECT_PATTERN = re.compile(r"^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$")
AUDIENCE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.:-]*$")
OBTAINED_VIA = ("direct", "token_exchange", "workload_attestation")


@dataclass(frozen=True)
class Hop:
    """One link of the chain: who acted, and how the right to act was obtained."""
    actor: str
    obtained_via: str


@dataclass(frozen=True)
class Credential:
    """What a caller holds. A handle, never the material behind it.

    chain[0] is the current actor and the last element is the root, which is the
    order the entry envelope in examples/end-to-end already carries. Prior hops
    are informational: authorise() reads chain[0] and the top-level scope only
    (X-cross-structure-038).
    """
    handle: str
    subject: str
    chain: tuple[Hop, ...]
    scope: tuple[str, ...]
    audience: str
    issued_at: str
    expires_at: str

    @property
    def actor(self) -> str:
        return self.chain[0].actor

    def remaining_s(self, at: datetime | None = None) -> int:
        return int((parse_time(self.expires_at) - (at or now())).total_seconds())


@dataclass(frozen=True)
class AttestRequest:
    """A unit of work asking for an identity of its own.

    platform_facts is what the platform can observe about where the unit runs.
    presented is a credential the unit was already handed. vouched_by is an
    already-attested party obtaining an identity on behalf of a unit the platform
    cannot observe in place. An adapter that cannot serve one of these forms
    declares it in `unsupported` rather than answering with something weaker.
    """
    unit: str
    audience: str
    scope: tuple[str, ...]
    lifetime_s: int
    platform_facts: dict = field(default_factory=dict)
    presented: str | None = None
    vouched_by: Credential | None = None

    @classmethod
    def from_dict(cls, doc: dict) -> "AttestRequest":
        need = {"unit", "audience", "scope", "lifetime_s"}
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "an attestation request is an object")
        missing = sorted(need - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        check_subject(doc["unit"], "unit")
        return cls(doc["unit"], check_audience(doc["audience"]), check_scope(doc["scope"]),
                   check_lifetime(doc["lifetime_s"]), dict(doc.get("platform_facts") or {}),
                   doc.get("presented"), doc.get("vouched_by"))


@dataclass(frozen=True)
class DelegationRequest:
    """One hop. The principal the work is for, the agent that will act, and the
    scope and audience the issued credential is for."""
    subject: Credential
    actor: Credential
    scope: tuple[str, ...]
    audience: str
    lifetime_s: int

    @classmethod
    def from_dict(cls, doc: dict) -> "DelegationRequest":
        need = {"subject", "actor", "scope", "audience", "lifetime_s"}
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a delegation request is an object")
        missing = sorted(need - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        for name in ("subject", "actor"):
            if not isinstance(doc[name], Credential):
                raise Problem("document-invalid",
                              f"{name} must be a credential produced by verify or attest, not a value "
                              f"the caller built", rejected_field=name)
        return cls(doc["subject"], doc["actor"], check_scope(doc["scope"]),
                   check_audience(doc["audience"]), check_lifetime(doc["lifetime_s"]))


def check_subject(name, what="actor") -> str:
    if not isinstance(name, str) or not SUBJECT_PATTERN.match(name):
        raise Problem("document-invalid",
                      f"{what} {name!r} is not a subject; a subject is user:, service:, agent: or "
                      f"schedule: followed by a name", rejected_field=what)
    return name


def check_scope(scope) -> tuple[str, ...]:
    if isinstance(scope, str) or not isinstance(scope, (list, tuple)) or not scope:
        raise Problem("document-invalid", "scope must be a non-empty array of scope tokens")
    unknown = sorted(set(scope) - set(SCOPE_VOCABULARY))
    if unknown:
        raise Problem("document-invalid",
                      f"scope tokens {unknown} are not in the declared vocabulary", unknown_scope=unknown)
    return tuple(sorted(set(scope)))


def check_audience(audience) -> str:
    if not isinstance(audience, str) or not AUDIENCE_PATTERN.match(audience):
        raise Problem("document-invalid",
                      f"audience {audience!r} must be exactly one destination identifier",
                      rejected_field="audience")
    return audience


def check_lifetime(lifetime_s) -> int:
    if not isinstance(lifetime_s, int) or isinstance(lifetime_s, bool) or lifetime_s < 1:
        raise Problem("document-invalid", "lifetime_s must be a positive integer number of seconds")
    return lifetime_s


# --- The clock, fixed so a dry run is byte-stable ----------------------------
def now() -> datetime:
    return parse_time(os.environ.get("IDENTITY_CLOCK", "2026-09-03T09:12:00Z"))


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(when: datetime) -> str:
    return when.replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- Pure functions in front of every adapter --------------------------------
def classify_scope(held: tuple[str, ...], wanted: tuple[str, ...]) -> str:
    """narrower | equal | wider. Pure: no clock, no adapter, no network."""
    held_set, wanted_set = set(held), set(wanted)
    if not wanted_set <= held_set:
        return "wider"
    return "equal" if wanted_set == held_set else "narrower"


def classify_chain(chain: tuple[Hop, ...], actor: str) -> str:
    """rooted | cyclic | unrooted, for the chain that prepending `actor` would make."""
    if any(hop.actor == actor for hop in chain):
        return "cyclic"
    if not chain or chain[-1].obtained_via not in ROOT_OBTAINED_VIA:
        return "unrooted"
    return "rooted"


# --- Credential material stays behind the boundary ---------------------------
def seal(payload: dict, key: str) -> str:
    """What an outside issuer hands a caller: an opaque blob, not a Credential."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    mac = hmac.new(key.encode(), body.encode(), hashlib.sha256).hexdigest()[:16]
    return "presented." + hashlib.sha256(body.encode()).hexdigest()[:16] + "." + mac


def opens(blob: str, payload: dict, key: str) -> bool:
    return isinstance(blob, str) and blob == seal(payload, key)


def credential_as_dict(cred: Credential) -> dict:
    """The caller-visible view. No material, no issuer, no trust bundle."""
    doc = asdict(cred)
    doc["chain"] = [dict(h) if isinstance(h, dict) else asdict(h) for h in cred.chain]
    doc["scope"] = list(cred.scope)
    return doc


# --- The interface the core imports ------------------------------------------
class IdentityAdapter(ABC):
    """One identity interface: verify, attest, delegate.

    Every check that makes a chain trustworthy is concrete here, so an adapter
    can only decline an operation by declaring it in `unsupported`, never by
    answering it with something weaker (cap-identity-implement invariant 2).
    """

    entity = "adapter"
    root_of_trust = "unset"            # how a root credential comes to exist
    verification_locus = "unset"       # where a presented credential is checked
    credential_form = "unset"          # what the material behind a handle is
    declared_marker = "unset"          # what an answer from this binding says
    unsupported: tuple = ()            # operations this binding declares it does not serve
    honours_forward_break = False      # whether the deliberate breakage is even expressible here

    def __init__(self):
        self.attestations = 0
        self.exchanges = 0
        self.verifications = 0
        self.refusals = 0
        self.authority_calls = 0       # calls to an authority to verify one credential
        self.observed_marker = ""      # read from an answer, never from the binding
        self.hops: list[dict] = []     # one DelegationHopRecord per hop, appended, never mutated
        self.current_action = "action"
        self._issued: dict[str, dict] = {}   # handle -> the material, which never leaves this object
        self._withdrawn: dict[str, dict] = {}   # subject -> {withdrawn_by, withdrawn_at, reason}

    # --- 1. verify: the only way an actor comes into existence ---------------
    def verify(self, presented: str) -> Credential:
        self.verifications += 1
        cred = self._verify(presented)
        if cred.remaining_s() <= 0:
            self.refusals += 1
            raise Problem("identity-untrusted",
                          f"the presented credential for {cred.subject} expired at {cred.expires_at}",
                          subject=cred.subject, expired_at=cred.expires_at)
        state = classify_chain(cred.chain[1:], cred.chain[0].actor) if len(cred.chain) > 1 \
            else ("rooted" if cred.chain[0].obtained_via in ROOT_OBTAINED_VIA else "unrooted")
        if state != "rooted":
            self.refusals += 1
            raise Problem("identity-untrusted",
                          f"the chain presented for {cred.subject} is {state}: a chain must be acyclic and "
                          f"end at a hop obtained by {list(ROOT_OBTAINED_VIA)}, not at a name a caller "
                          f"supplied for itself",
                          subject=cred.subject, chain_state=state)
        return cred

    # --- 2. attest: a unit of work gets an identity --------------------------
    def attest(self, request: AttestRequest) -> Credential:
        form = ("attest_from_presented_credential" if request.presented and not request.platform_facts
                else "attest_from_platform_facts" if request.platform_facts and not request.presented
                else "attest_on_behalf_of" if request.vouched_by and not request.platform_facts
                else "attest")
        self._refuse_if_unsupported(form)
        if not (request.platform_facts or request.presented or request.vouched_by):
            self.refusals += 1
            raise Problem("document-invalid",
                          "an attestation names either what the platform observed about the unit, a "
                          "credential the unit already holds, or the attested party vouching for it")
        cred = self._attest(request)
        self.attestations += 1
        self._record(cred, action=f"attest-{request.unit}", executing_unit=request.unit)
        return cred

    # --- 3. delegate: one hop, narrower and shorter than the one before it ---
    def delegate(self, request: DelegationRequest) -> Credential:
        self._refuse_if_unsupported("delegate")
        subject, actor = request.subject, request.actor
        at = now()
        for role, cred in (("subject", subject), ("actor", actor)):
            if cred.remaining_s(at) <= 0:
                self.refusals += 1
                raise Problem("identity-untrusted",
                              f"the {role} credential for {cred.subject} expired at {cred.expires_at}; "
                              f"no credential was issued",
                              role=role, subject=cred.subject, expired_at=cred.expires_at)
        widened = classify_scope(subject.scope, request.scope)
        if widened == "wider":
            self.refusals += 1
            raise Problem("policy-denied",
                          f"hop {actor.actor} asked for scope {sorted(set(request.scope) - set(subject.scope))} "
                          f"that the credential it delegates from does not hold; a hop narrows scope and never "
                          f"widens it, so no credential was issued",
                          rule_id="scope-must-narrow", actor=actor.actor,
                          held_scope=sorted(subject.scope), requested_scope=sorted(request.scope),
                          enforcement_point="platform-pre-issue")
        state = classify_chain(subject.chain, actor.actor)
        if state == "cyclic":
            self.refusals += 1
            raise Problem("policy-denied",
                          f"hop {actor.actor} already appears in the chain it would extend; a chain is "
                          f"acyclic, so no credential was issued",
                          rule_id="chain-must-be-acyclic", actor=actor.actor,
                          chain=[h.actor for h in subject.chain], enforcement_point="platform-pre-issue")
        if state == "unrooted":
            self.refusals += 1
            raise Problem("identity-untrusted",
                          f"the chain {[h.actor for h in subject.chain]} is rooted in a hop obtained by "
                          f"token_exchange; nothing attested or authenticated it, so no credential was issued",
                          chain_state=state, enforcement_point="platform-pre-issue")
        expires = at + timedelta(seconds=request.lifetime_s)
        if expires > parse_time(subject.expires_at):
            self.refusals += 1
            raise Problem("policy-denied",
                          f"hop {actor.actor} asked for {request.lifetime_s}s, longer than the "
                          f"{subject.remaining_s(at)}s left on the credential it delegates from; a hop "
                          f"shortens the lifetime and never extends it, so no credential was issued",
                          rule_id="lifetime-must-not-extend", actor=actor.actor,
                          requested_lifetime_s=request.lifetime_s,
                          subject_remaining_s=subject.remaining_s(at),
                          enforcement_point="platform-pre-issue")
        cred = self._delegate(request, expires)
        self.exchanges += 1
        self._record(cred, action=f"delegate-{actor.actor}-to-{request.audience}",
                     executing_unit=actor.actor)
        return cred

    # --- withdrawal: takes effect on the very next capability call -----------
    def withdraw(self, subject: str, withdrawn_by: str, reason: str = "withdrawn") -> dict:
        """Record that `subject`'s identity is withdrawn.

        No signal reaches a unit already running under `subject`: the platform
        does not enforce per-session trust, so nothing here needs to interrupt a
        loop or close a socket. Enforcement is per-request instead (concern-
        identity-q5): `authorise` re-checks this registry on every capability
        call, so the very next call a running unit makes is the one that stops.
        """
        record = {"subject": check_subject(subject, "subject"),
                  "withdrawn_by": check_subject(withdrawn_by, "withdrawn_by"),
                  "withdrawn_at": iso(now()), "reason": reason}
        self._withdrawn[subject] = record
        return record

    # --- what an authorisation decision is allowed to read -------------------
    def authorise(self, cred: Credential, required: str) -> str:
        """Reads the top-level scope and the current actor. Prior hops are not offered.

        X-cross-structure-038: prior actors identified by nested act claims are
        informational only, so a rule that wanted to read one cannot get at it here.

        Checked first, ahead of scope: a withdrawn identity is refused before its
        scope is even read, and the refusal, plus who withdrew it and where the
        run stopped, is written as one record to the same audit trail every hop
        already writes to (`self.hops`) — never a signal the unit had to notice.
        """
        withdrawal = self._withdrawn.get(cred.actor)
        if withdrawal is not None:
            self.refusals += 1
            stop = {"run_id": os.environ.get("RUN_ID", "run-harness-identity"),
                    "action_id": self.current_action, "kind": "withdrawal-stop",
                    "subject": cred.actor, "handle": cred.handle,
                    "withdrawn_by": withdrawal["withdrawn_by"],
                    "withdrawn_at": withdrawal["withdrawn_at"], "stopped_at": iso(now())}
            self.hops.append(stop)
            raise Problem("identity-withdrawn",
                          f"{cred.actor}'s identity was withdrawn by {withdrawal['withdrawn_by']} at "
                          f"{withdrawal['withdrawn_at']}; the call stopped here and nothing proceeded",
                          subject=cred.actor, withdrawn_by=withdrawal["withdrawn_by"],
                          withdrawn_at=withdrawal["withdrawn_at"], stopped_at=stop["stopped_at"])
        if required not in cred.scope:
            raise Problem("policy-denied",
                          f"{cred.actor} holds {sorted(cred.scope)} and the action needs {required!r}; the "
                          f"scope of a hop earlier in the chain is not consulted",
                          rule_id="scope-must-cover-the-action", actor=cred.actor,
                          enforcement_point="platform-pre-issue")
        return cred.actor

    # --- adapter seams -------------------------------------------------------
    @abstractmethod
    def _verify(self, presented: str) -> Credential:
        """Resolve a presented credential against this binding's trust material."""

    @abstractmethod
    def _attest(self, request: AttestRequest) -> Credential:
        """Mint an identity for a unit of work. Reached only after the form is supported."""

    @abstractmethod
    def _delegate(self, request: DelegationRequest, expires) -> Credential:
        """Mint one hop. Reached only after narrowing, acyclicity and lifetime have held."""

    @abstractmethod
    def fixture_presented(self, subject: str, scope, audience: str, lifetime_s: int,
                          obtained_via: str = "direct") -> str:
        """Test seam: the blob an outside issuer would have handed a caller.

        It stands in for what arrives at the entry door from outside the platform.
        It is never called from the caller region of call.py.
        """

    # --- housekeeping --------------------------------------------------------
    def _refuse_if_unsupported(self, operation: str) -> None:
        if operation in self.unsupported:
            self.refusals += 1
            raise Problem("adapter-unavailable",
                          f"this binding does not serve {operation}: {self.entity}. It declares the subset "
                          f"rather than answering with a weaker credential; no credential was issued",
                          retryable=False, unsupported_operation=operation,
                          unsupported=list(self.unsupported))

    def _record(self, cred: Credential, action: str, executing_unit: str) -> None:
        """One DelegationHopRecord per hop, appended so a later edit is detectable.

        executing_unit is the unit the platform asked for, not the subject of the
        credential that came back: a hop that forwarded an incoming credential
        unchanged is only visible because those two differ. enforcement_point is
        read from the marker the answer carried, never from the configuration
        that selected the adapter.
        """
        run_id = os.environ.get("RUN_ID", "run-harness-identity")
        for index, hop in enumerate(cred.chain):
            self.hops.append({"run_id": run_id, "action_id": f"{self.current_action}/{action}",
                              "hop_index": index,
                              "actor": hop.actor, "obtained_via": hop.obtained_via,
                              "enforcement_point": self.observed_marker,
                              "written_at": iso(now()), "executing_unit": executing_unit,
                              "handle": cred.handle})

    def _mint(self, subject: str, chain: tuple[Hop, ...], scope, audience: str, expires) -> Credential:
        """Give a credential a handle and keep the material where a caller cannot read it."""
        material = "MATERIAL-" + hashlib.sha256(
            (self.declared_marker + subject + audience + iso(expires) +
             "|".join(h.actor for h in chain)).encode()).hexdigest()
        handle = "cred-" + hashlib.sha256(material.encode()).hexdigest()[:20]
        self._issued[handle] = {"material": material, "subject": subject}
        self.observed_marker = self.declared_marker
        return Credential(handle=handle, subject=subject, chain=tuple(chain), scope=tuple(scope),
                          audience=audience, issued_at=iso(now()), expires_at=iso(expires))

    def material_of(self, handle: str) -> str:
        """Only the conformance run calls this, to prove the material never got out."""
        return self._issued.get(handle, {}).get("material", "")

    def binding(self) -> dict:
        return {"entity": self.entity, "root_of_trust": self.root_of_trust,
                "verification_locus": self.verification_locus,
                "credential_form": self.credential_form, "marker": self.declared_marker,
                "unsupported": list(self.unsupported)}
