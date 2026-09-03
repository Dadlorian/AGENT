#!/usr/bin/env python3
"""Provenance: a signed statement binding an artifact to what produced it.

Read it in this order. AttestRequest is the whole caller vocabulary: subject
digests, a predicate, and who it is made on behalf of - never the artifact
bytes. statement() and pae() build the two layers a foreign verifier reads;
verify() is a module-level function that touches no adapter and no store, which
is the property the concern actually asks for (F-b4-05): it is importable and
runnable on its own, so the conformance run can execute it in a separate
process with our store unreachable. ProvenanceAdapter.attest() is a template
method - it checks that the predicate binds code version, inputs and actor
before any adapter code runs, so no binding can decline that check.

Three layers stay distinct (X-cross-structure-050): the envelope carries the
signature, the statement names the subjects, the predicate carries everything
of ours. Only the third is this platform's own.

No product name, endpoint or store path appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only; hashlib and hmac are the only primitives.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

INTERFACE_VERSION = "0.1"

# The outer two layers are fixed by the standards on file, not by us.
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"      # X-cross-structure-050
PAYLOAD_TYPE = "application/vnd.in-toto+json"           # cap-provenance shape
# The predicate type URIs are this platform's own and are proposed: no record on
# file carries a fetched predicate-type URI for a build or for an agent action
# (cap-provenance instruction 4). The agent-action id is the one that skill
# already fixes; the build id mirrors it.
PREDICATE_BUILD = "urn:agentic:provenance:predicate:build:0.1"
PREDICATE_AGENT_ACTION = "urn:agentic:provenance:predicate:agent-action:0.1"

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) -----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "The attestation request or envelope is not well formed", False),
    "adapter-unavailable": (503, "No signer or store serves this binding", True),
}
# cap-provenance records `urn:agentic:problem:attestation-unverifiable` as
# proposed and not yet in the registry cap-errors owns. Until it has a row, a
# statement that does not check out is returned as the registered
# document-invalid, and the intended type travels as an extension field.
PROPOSED_TYPE = PROBLEM_BASE + "attestation-unverifiable"


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail, "retryable": retryable, **ext}
        super().__init__(detail)


# --- The caller vocabulary --------------------------------------------------
# There is no attest flag, no signer field, no store field and no way to opt out
# (F-b1-08). The artifact never travels here, only its digest (cap-provenance).
ALLOWED = {"subjects", "predicate_type", "predicate", "actor", "correlation", "idempotency_key"}
REQUIRED = {"subjects", "predicate_type", "predicate", "actor"}


def digest_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Subject:
    name: str          # a stable identifier, never a path or a URL (cap-provenance step 2)
    digest: str


@dataclass(frozen=True)
class AttestRequest:
    subjects: tuple
    predicate_type: str
    predicate: dict
    actor: str
    correlation: dict = field(default_factory=dict)
    idempotency_key: str = ""

    @classmethod
    def from_dict(cls, doc: dict) -> "AttestRequest":
        """The one gate a request passes. Artifact bytes never get past it."""
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "an attestation request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the attestation vocabulary; provenance is applied by "
                          f"the platform, so there is nothing to opt into and the artifact itself never "
                          f"travels in a request - only its digest",
                          rejected_fields=extra)
        missing = sorted(REQUIRED - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        subjects = doc["subjects"]
        if not isinstance(subjects, list) or not subjects:
            raise Problem("document-invalid", "subjects must be a non-empty array")
        out = []
        for i, s in enumerate(subjects):
            if not isinstance(s, dict) or not isinstance(s.get("name"), str) or not s["name"]:
                raise Problem("document-invalid", f"subjects[{i}] needs a stable name")
            if "/" in s["name"] or "://" in s["name"]:
                raise Problem("document-invalid",
                              f"subjects[{i}].name {s['name']!r} looks like a path or a URL; a subject is named "
                              f"by a stable identifier so a statement cannot follow the wrong bytes",
                              subject=s["name"])
            if not isinstance(s.get("digest"), str) or not DIGEST.match(s["digest"]):
                raise Problem("document-invalid", f"subjects[{i}].digest must match sha256:<64 hex>")
            out.append(Subject(s["name"], s["digest"]))
        if not isinstance(doc["predicate"], dict) or not doc["predicate"]:
            raise Problem("document-invalid", "predicate must be a non-empty object")
        if not isinstance(doc["predicate_type"], str) or ":" not in doc["predicate_type"]:
            raise Problem("document-invalid", "predicate_type must be a URI")
        if not isinstance(doc["actor"], str) or not doc["actor"]:
            raise Problem("document-invalid", "actor must be a non-empty string")
        return cls(tuple(out), doc["predicate_type"], doc["predicate"], doc["actor"],
                   doc.get("correlation", {}) or {}, doc.get("idempotency_key", ""))


def bindings(predicate: dict) -> dict:
    """The three things F-b4-05 requires, found in any predicate type.

    An extension point is not a hole: a new predicate type may carry any fields
    it likes, but it does not get to drop the code version, the inputs or the
    actor, so this check is here rather than in a per-type table.
    """
    actor = predicate.get("actor") or (predicate.get("builder") or {}).get("actor")
    code_version = predicate.get("code_version")
    inputs = predicate.get("materials") or predicate.get("argument_digest")
    absent = [n for n, v in (("actor", actor), ("code_version", code_version), ("inputs", inputs)) if not v]
    if absent:
        raise Problem("document-invalid",
                      f"the predicate binds no {', '.join(absent)}; every artifact is attributable to the "
                      f"code version, inputs and actor that produced it, so a predicate missing any of the "
                      f"three is not a statement this capability can make",
                      absent=absent)
    return {"actor": actor, "code_version": code_version, "inputs": inputs}


# --- The two layers a foreign verifier reads --------------------------------
def canonical(doc: dict) -> bytes:
    """Sorted-key JSON, standing in for a canonical form (RFC 8785 unverified)."""
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()


def statement(subjects, predicate_type: str, predicate: dict) -> dict:
    return {"_type": STATEMENT_TYPE,
            "subject": [{"name": s.name, "digest": {"sha256": s.digest.split(":", 1)[1]}} for s in subjects],
            "predicateType": predicate_type,
            "predicate": predicate}


def pae(payload_type: str, payload: bytes) -> bytes:
    """Pre-Authentication Encoding: signed instead of the raw JSON (X-cap-provenance-003).

    Spelling is DSSEv1 SP len(type) SP type SP len(body) SP body. The DSSE
    version string is unverified here: no fetched record of the spec is on file.
    """
    return b"DSSEv1 %d %s %d %s" % (len(payload_type), payload_type.encode(), len(payload), payload)


def mac(key: bytes, message: bytes) -> str:
    """hashlib and hmac only. This is a shared-secret MAC standing in for a
    signature: it proves the envelope was made by a holder of the key, and it
    does NOT give public verifiability. Swapping it for an asymmetric signer
    changes this function and nothing else in the file."""
    return hmac.new(key, message, hashlib.sha256).hexdigest()


@dataclass
class Envelope:
    payloadType: str
    payload: str            # base64 of the canonical statement
    signatures: list        # [{"keyid": ..., "sig": ...}]

    def to_dict(self) -> dict:
        return {"payloadType": self.payloadType, "payload": self.payload, "signatures": self.signatures}

    def statement(self) -> dict:
        return json.loads(base64.b64decode(self.payload))


@dataclass(frozen=True)
class Receipt:
    """What attest returns: the envelope, and who signed it."""
    envelope: Envelope
    statement_id: str
    signer: dict            # keyid, authority, and (where it expires) the window


@dataclass(frozen=True)
class Location:
    """Where a third party fetches the envelope, without holding our credentials."""
    uri: str
    store: str
    inclusion_proof: dict | None = None


@dataclass(frozen=True)
class TrustPolicy:
    """Accepted signers and expected values. Nothing here names a store."""
    accepted_signers: dict                      # keyid or issuer -> verifying material
    expected_subjects: dict                     # subject name -> digest the holder computed
    expected_predicate_types: tuple = ()
    require_inclusion_proof: bool = False
    now: str = ""                               # for an identity whose authority expires

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, doc: dict) -> "TrustPolicy":
        return cls(doc["accepted_signers"], doc["expected_subjects"],
                   tuple(doc.get("expected_predicate_types", ())),
                   bool(doc.get("require_inclusion_proof", False)), doc.get("now", ""))


@dataclass
class VerifyResult:
    accepted: bool
    reason: str
    checks: list
    signer: str = ""
    subjects_matched: int = 0
    subject_mismatches: int = 0
    predicate_type: str = ""
    inclusion_proof_verified: bool = False

    def problem(self) -> dict:
        """The failure body a caller gets. The registered type, not the proposed one."""
        return {"type": PROBLEM_BASE + "document-invalid", "title": REGISTRY["document-invalid"][1],
                "status": 422, "detail": self.reason, "retryable": False,
                "proposed_type": PROPOSED_TYPE, "proposed_type_status": "not yet in the registry cap-errors owns"}


# --- Verification: a function, not a service --------------------------------
def _leaf(data: bytes) -> str:
    return hashlib.sha256(b"\x00" + data).hexdigest()


def _node(left: str, right: str) -> str:
    return hashlib.sha256(b"\x01" + bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()


def verify_inclusion(entry: bytes, proof: dict) -> bool:
    """Recompute the log root from the entry and its audit path.

    Append-only-log shaped (X-cross-structure-052); the hashing is domain
    separated per leaf and node. Conformance to a published log spec is
    unverified: no fetched record of one is on file.
    """
    try:
        index, size, path, root = proof["leaf_index"], proof["tree_size"], proof["path"], proof["root"]
    except (KeyError, TypeError):
        return False

    def up(h: str, i: int, n: int, siblings: list) -> str | None:
        if n == 1:
            return h if not siblings else None
        if not siblings:
            return None
        k = 1 << ((n - 1).bit_length() - 1)
        rest, sib = siblings[:-1], siblings[-1]
        if i < k:
            sub = up(h, i, k, rest)
            return _node(sub, sib) if sub else None
        sub = up(h, i - k, n - k, rest)
        return _node(sib, sub) if sub else None

    return up(_leaf(entry), index, size, list(path)) == root


def verify(envelope: dict, policy: TrustPolicy, proof: dict | None = None,
           material: dict | None = None) -> VerifyResult:
    """Envelope in, verdict out. Reads no store, no adapter and no file.

    This is the whole verification path: the adapters call it, and the
    conformance run executes it in a separate process with our store
    unreachable, which is the only way to show the store is not load-bearing
    (cap-provenance step 5).
    """
    checks = []

    def fail(reason):
        return VerifyResult(False, reason, checks)

    if not isinstance(envelope, dict) or set(envelope) != {"payloadType", "payload", "signatures"}:
        raise Problem("document-invalid", "an envelope carries exactly payloadType, payload and signatures")
    if envelope["payloadType"] != PAYLOAD_TYPE:
        raise Problem("document-invalid", f"payloadType {envelope['payloadType']!r} is not {PAYLOAD_TYPE}")
    if not envelope["signatures"]:
        return fail("the envelope carries no signature")
    checks.append("envelope well formed")
    try:
        payload = base64.b64decode(envelope["payload"], validate=True)
        doc = json.loads(payload)
    except Exception as exc:
        raise Problem("document-invalid", f"the payload is not base64 of a JSON statement: {exc}") from exc
    if doc.get("_type") != STATEMENT_TYPE:
        raise Problem("document-invalid", f"_type {doc.get('_type')!r} is not {STATEMENT_TYPE}")
    checks.append("statement type is the published one")

    sig = envelope["signatures"][0]
    keyid = sig.get("keyid", "")
    accepted = policy.accepted_signers
    key = accepted.get(keyid)
    if key is None and material and material.get("keyid") == keyid:
        issuer = material.get("issuer", "")
        if issuer in accepted:                       # an identity, accepted by its issuer
            key = material.get("material")
            if policy.now and not (material.get("not_before", "") <= policy.now <= material.get("not_after", "")):
                return fail(f"the signing identity {keyid} was not valid at {policy.now}")
            checks.append(f"identity {keyid} accepted by issuer {issuer} and inside its window")
    if key is None:
        return fail(f"no accepted signer matches keyid {keyid!r}")
    if not hmac.compare_digest(mac(bytes.fromhex(key), pae(envelope["payloadType"], payload)), sig.get("sig", "")):
        return fail("the signature does not check out over the pre-authentication encoding")
    checks.append("signature checks out over the PAE, not over the raw JSON")

    matched = mismatched = 0
    named = {s["name"]: "sha256:" + s["digest"]["sha256"] for s in doc.get("subject", [])}
    for name, want in policy.expected_subjects.items():
        got = named.get(name)
        if got is None:
            return fail(f"the statement names no subject {name!r}")
        if got != want:
            mismatched += 1
        else:
            matched += 1
    if mismatched:
        result = fail(f"subject digest for {name!r} in the statement does not match the artifact supplied")
        result.subjects_matched, result.subject_mismatches = matched, mismatched
        result.signer, result.predicate_type = keyid, doc.get("predicateType", "")
        return result
    checks.append(f"{matched} subject digest(s) match the artifact the holder has")

    if policy.expected_predicate_types and doc.get("predicateType") not in policy.expected_predicate_types:
        return fail(f"predicateType {doc.get('predicateType')!r} is not one the policy expects")
    proved = False
    if policy.require_inclusion_proof:
        if not proof or not verify_inclusion(canonical(envelope), proof):
            return fail("no inclusion proof accompanies the envelope, or it does not recompute the log root")
        proved = True
        checks.append(f"inclusion proof recomputes log root {proof['root'][:12]} at size {proof['tree_size']}")
    return VerifyResult(True, "accepted", checks, keyid, matched, 0, doc.get("predicateType", ""), proved)


# --- The interface the core imports -----------------------------------------
class ProvenanceAdapter(ABC):
    """One provenance interface. Four operations: attest, verify, resolve, publish.

    attest is concrete so that no adapter can decline the vocabulary check or
    the code-version/inputs/actor check; verify delegates to the module function
    above so that every binding is judged by the same envelope-only verifier.
    """

    entity = "adapter"
    signer_authority = "unset"        # possession | expiring-identity
    key_lifetime = "unset"
    store_kind = "unset"
    material_source = "unset"         # out-of-band trust policy | published with the envelope
    offline_capable = True
    declared_gaps: tuple = ()         # what this binding cannot do, stated rather than dropped
    supports_inclusion_proof = False

    def __init__(self):
        self.attestations = 0
        self.refusals = 0

    # 1. attest -- always returns a signed envelope
    def attest(self, request: AttestRequest) -> Receipt:
        try:
            bound = bindings(request.predicate)
        except Problem:
            self.refusals += 1
            raise
        doc = statement(request.subjects, request.predicate_type, request.predicate)
        payload = canonical(doc)
        keyid, key, signer = self._signer(request)
        envelope = Envelope(PAYLOAD_TYPE, base64.b64encode(payload).decode(),
                            [{"keyid": keyid, "sig": mac(key, pae(PAYLOAD_TYPE, payload))}])
        statement_id = "urn:agentic:attestation:" + hashlib.sha256(payload).hexdigest()[:24]
        self._append(statement_id, envelope, request, bound)
        self.attestations += 1
        return Receipt(envelope, statement_id, signer)

    # 2. verify -- the envelope alone, by the module function above
    def verify(self, envelope: Envelope | dict, policy: TrustPolicy,
               proof: dict | None = None, material: dict | None = None) -> VerifyResult:
        doc = envelope.to_dict() if isinstance(envelope, Envelope) else envelope
        return verify(doc, policy, proof, material)

    # 3. resolve -- every envelope naming this digest as a subject
    @abstractmethod
    def resolve(self, subject_digest: str) -> list:
        ...

    # 4. publish -- a location a third party can fetch from
    @abstractmethod
    def publish(self, receipt: Receipt) -> Location:
        ...

    @abstractmethod
    def fetch(self, uri: str) -> dict:
        """The bundle at a location: the envelope, the verifying material, the proof."""

    @abstractmethod
    def store_integrity(self) -> dict:
        """What this binding can say about its own store. Never what verification rests on."""

    @abstractmethod
    def verifying_material(self, keyid: str) -> dict:
        """What a verifier must be given for this keyid, and where it came from.

        A trust policy is an input to verification (cap-provenance operation
        verify), so somebody has to hand the verifier one. Which is the axis the
        pair differs on: a held key is distributed out of band, an expiring
        identity publishes its material with the envelope.
        """

    @abstractmethod
    def _signer(self, request: AttestRequest) -> tuple:
        """(keyid, key bytes, signer description). Where the key comes from is the adapter's business."""

    @abstractmethod
    def _append(self, statement_id: str, envelope: Envelope, request: AttestRequest, bound: dict) -> None:
        """Write the envelope beside the record, never in place of it."""

    def binding(self) -> dict:
        """What a report says about who answered. No caller ever reads this."""
        return {"adapter": self.adapter_kind, "entity": self.entity,
                "signer_authority": self.signer_authority, "key_lifetime": self.key_lifetime,
                "store_kind": self.store_kind, "material_source": self.material_source,
                "offline_capable": self.offline_capable,
                "log_inclusion_proofs": "supported" if self.supports_inclusion_proof else "unsupported",
                "declared_gaps": list(self.declared_gaps)}

    adapter_kind = "unset"            # local-signed-jsonl | keyless-transparency-log
