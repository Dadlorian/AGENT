#!/usr/bin/env python3
"""Policy: one decision for one unit of work, taken before anything is spent.

Read it in this order. DecisionRequest is the whole caller vocabulary: a
registered decision point, who is asking, what they intend, what is acted on,
the run context, and the policy version the answer must be pinned to. Decision
is what comes back - an effect, the rule that decided it, the version it was
decided under, and the digest of the question - and nothing about the engine
that answered.

PolicyAdapter.decide() and PolicyAdapter.admit() are template methods: the
decision point registry, the declared-shape check, the version pin, the input
digest and the ordering (decide, then and only then the metered call) are
enforced here, so no adapter and no caller can decline the gate. The adapter
supplies _evaluate() and nothing else.

`Meter` is the unit of "after spend": every metered call is charged through it
and carries a sequence number from the same counter the decision journal uses,
so "the decision preceded the first metered call" is a comparison, not a
belief (F-b4-04, F-a6-04).

No product, engine, rule language or bundle name appears in this file
(F-b1-02, F-part-c-09). Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
# Found by walking up from this file's own directory, not by a fixed "../errors"
# offset: several harnesses' test.sh copy interface.py into out/breakage/ (and
# deeper) for a deliberate-breakage run, and a fixed relative offset would miss
# harness/errors/problem.py from there. The walk stays inside the repository
# tree either way (out/breakage/ is still nested under this harness's own
# directory), and stops at the first "errors" sibling that actually has it.
_search_dir = _errors_os.path.dirname(_errors_os.path.abspath(__file__))
for _ in range(10):
    _candidate = _errors_os.path.join(_search_dir, "errors")
    if _errors_os.path.isfile(_errors_os.path.join(_candidate, "problem.py")):
        if _candidate not in _errors_sys.path:
            _errors_sys.path.append(_candidate)  # appended, never inserted at 0: this
            # harness's own adapters/ package must resolve before errors/adapters/ does
        break
    _up = _errors_os.path.dirname(_search_dir)
    if _up == _search_dir:
        break
    _search_dir = _up
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

import hashlib
import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

INTERFACE_VERSION = "0.1"
HERE = os.path.dirname(os.path.abspath(__file__))

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07) -----
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "policy-denied": (403, "Refused before execution", False),
    "document-invalid": (422, "The decision request is not a well-formed request", False),
    "decision-point-unregistered": (422, "No decision point is registered under that name", False),
    "policy-version-unknown": (409, "That policy version is not resolvable here", False),
    "adapter-unavailable": (503, "No engine answered the decision", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


def canonical(doc) -> bytes:
    """The bytes two engines must agree were the question (sorted, no padding)."""
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()


def digest_of(doc) -> str:
    return "sha256:" + hashlib.sha256(canonical(doc)).hexdigest()


VERSION_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

# --- The caller vocabulary --------------------------------------------------
# Closed, so there is no field a caller can send that turns the decision off
# (F-b4-01: the platform applies each; a caller cannot decline them).
ALLOWED = {"decision_point", "subject", "action", "resource", "context", "policy_version"}
SUBJECT_REQUIRED = {"id", "tenant"}
CONTEXT_REQUIRED = {"run_id", "root_dispatch_id"}
TYPES = {"string": str, "integer": int, "object": dict, "array": list, "boolean": bool}


@dataclass(frozen=True)
class DecisionRequest:
    decision_point: str
    subject: dict
    action: str
    resource: dict
    context: dict
    policy_version: str

    @classmethod
    def from_dict(cls, doc: dict) -> "DecisionRequest":
        """The one gate a request passes. An advisory or bypass field never gets past it."""
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a decision request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the decision request vocabulary; there is no advisory "
                          f"mode, no dry-run flag and no bypass on this path",
                          rejected_fields=extra)
        missing = sorted(ALLOWED - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required fields {missing}", missing=missing)
        if not isinstance(doc["decision_point"], str) or not doc["decision_point"]:
            raise Problem("document-invalid", "decision_point must be a non-empty string")
        if not isinstance(doc["action"], str) or not doc["action"]:
            raise Problem("document-invalid", "action must be a non-empty string")
        for name, required in (("subject", SUBJECT_REQUIRED), ("context", CONTEXT_REQUIRED)):
            value = doc[name]
            if not isinstance(value, dict):
                raise Problem("document-invalid", f"{name} must be an object")
            absent = sorted(required - set(value))
            if absent:
                raise Problem("document-invalid", f"{name} is missing {absent}", missing=absent)
        if not isinstance(doc["resource"], dict):
            raise Problem("document-invalid", "resource must be an object")
        if not isinstance(doc["policy_version"], str) or not VERSION_PATTERN.match(doc["policy_version"]):
            raise Problem("document-invalid",
                          "policy_version must be a sha256: digest, so the decision can be replayed",
                          policy_version=doc["policy_version"])
        return cls(doc["decision_point"], doc["subject"], doc["action"],
                   doc["resource"], doc["context"], doc["policy_version"])

    def as_dict(self) -> dict:
        return asdict(self)

    def digest(self) -> str:
        """Computed over canonical bytes before evaluation, so two engines agree
        on what the question was regardless of key order or whitespace."""
        return digest_of(self.as_dict())


@dataclass(frozen=True)
class Decision:
    effect: str            # allow | deny
    rule_id: str           # required for allow as well as deny
    policy_version: str
    decision_point: str
    input_digest: str
    decided_at: str
    problem: dict | None = None   # required when effect is deny (F-b4-07)


def decision_as_dict(decision: Decision) -> dict:
    """The caller-visible view. Nothing here names an engine, a language or a bundle."""
    doc = asdict(decision)
    return {k: v for k, v in doc.items() if v is not None}


# --- Spend: what "before execution, not after spend" is measured against ----
class Meter:
    """Every metered call of a dispatch goes through here and is stamped with a
    sequence number from the adapter's counter, the same counter the decision
    journal uses. Ordering is then a comparison of two integers."""

    def __init__(self, tick):
        self._tick = tick
        self.calls: list[tuple[str, int, int]] = []   # (dispatch_id, micros, seq)

    def charge(self, dispatch_id: str, micros: int = 1000) -> int:
        self.calls.append((dispatch_id, int(micros), self._tick()))
        return int(micros)

    def spend(self, dispatch_id: str | None = None) -> int:
        return sum(m for d, m, _ in self.calls if dispatch_id in (None, d))

    def first_seq(self, dispatch_id: str) -> int | None:
        seqs = [s for d, _, s in self.calls if d == dispatch_id]
        return min(seqs) if seqs else None


# --- Registry and bundle, as data beside the interface ----------------------
def load_points() -> dict:
    with open(os.path.join(HERE, "decision_points.json")) as fh:
        return json.load(fh)["points"]


def load_bundle() -> dict:
    with open(os.path.join(HERE, "bundle.json")) as fh:
        return json.load(fh)


def check_shape(schema: dict, doc: dict, where: str) -> None:
    """The decision point's declared shape, checked before evaluation.

    cap-document-validation owns the dialect and the real checker (F-b3-09);
    what matters here is only that an unvalidated input is refused rather than
    evaluated against a shape the rule author assumed. Proposed.
    """
    for name, kind in schema.get("required", {}).items():
        if name not in doc:
            raise Problem("document-invalid",
                          f"{where} is missing {name!r}, declared by this decision point; the request was "
                          f"refused before evaluation rather than evaluated against an assumed shape",
                          missing=[name])
        if not isinstance(doc[name], TYPES[kind]) or isinstance(doc[name], bool) is (kind != "boolean"):
            raise Problem("document-invalid", f"{where}.{name} must be a {kind}", field=name)
    if not schema.get("additional", True):
        extra = sorted(set(doc) - set(schema.get("required", {})) - set(schema.get("optional", {})))
        if extra:
            raise Problem("document-invalid", f"{where} carries undeclared fields {extra}",
                          rejected_fields=extra)


# --- The interface the core imports -----------------------------------------
class PolicyAdapter(ABC):
    """One decision API. Four operations: decide, activate, explain,
    register_decision_point - plus admit, the gate that composes decide with
    the unit of work so nothing runs on the far side of a deny.

    decide and admit are concrete. An adapter supplies _evaluate and nothing
    else, so no engine can decide whether to be asked, in what order, or
    whether an unregistered point defaults to allow.
    """

    entity = "adapter"
    decision_model = "unset"        # what the engine reads to decide
    activation_model = "unset"      # how a new rule set starts serving
    processes_required = "unset"    # what must be reachable for a decision at all
    declared_marker = "unset"       # what an answer from this binding should say
    report_adapter = "unset"        # the decision model this binding reports as
    conformance_subset: tuple = ()  # registered points this engine declares it cannot serve

    def __init__(self, bundle: dict | None = None, points: dict | None = None):
        self._seq = 0
        self.meter = Meter(self._tick)
        self.journal: list[dict] = []          # policy-decided records, in order
        self.points = dict(points if points is not None else load_points())
        self.bundles: dict[str, dict] = {}
        self.observed_marker = ""
        self.denies = 0
        self.evaluations = 0
        self.active_version = self.activate(bundle if bundle is not None else load_bundle())

    def _tick(self) -> int:
        self._seq += 1
        return self._seq

    @staticmethod
    def _now() -> str:
        base = os.environ.get("POLICY_CLOCK")      # a fixed clock keeps a dry run deterministic
        now = datetime.fromisoformat(base) if base else datetime.now(timezone.utc)
        return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # 1. activate -- a bundle and its digest; the previous version stays resolvable
    def activate(self, bundle: dict) -> str:
        version = digest_of(bundle)
        self.bundles[version] = bundle
        self.active_version = version
        self._activated(bundle, version)
        return version

    # 2. register_decision_point -- an unregistered point is refused, never assumed
    def register_decision_point(self, name: str, schema: dict) -> str:
        self.points[name] = schema
        return name

    # 3. decide -- pure in the request and the pinned version
    def decide(self, request: DecisionRequest) -> Decision:
        point = self.points.get(request.decision_point)
        if point is None:
            raise Problem("decision-point-unregistered",
                          f"{request.decision_point!r} is not a registered decision point; an unregistered "
                          f"point is a conformance failure, not a default-allow",
                          decision_point=request.decision_point)
        check_shape(point.get("resource_schema", {}), request.resource, "resource")
        bundle = self.bundles.get(request.policy_version)
        if bundle is None:
            raise Problem("policy-version-unknown",
                          f"policy_version {request.policy_version} is not resolvable here, so the decision "
                          f"could not be pinned and no answer was given",
                          policy_version=request.policy_version)
        if request.decision_point in self.conformance_subset:
            raise Problem("adapter-unavailable",
                          f"this binding declares {request.decision_point!r} outside the subset it can serve "
                          f"and did not answer; a declared subset is not an allow",
                          decision_point=request.decision_point,
                          declared_subset=list(self.conformance_subset), retry_after_s=0)
        input_digest = request.digest()
        self.evaluations += 1
        effect, rule_id, detail = self._evaluate(request, bundle)
        if effect not in ("allow", "deny") or not rule_id:
            raise Problem("adapter-unavailable",
                          "the binding returned neither an attributable allow nor an attributable deny",
                          retry_after_s=0)
        problem = None
        if effect == "deny":
            self.denies += 1
            problem = {"type": PROBLEM_BASE + "policy-denied", "title": REGISTRY["policy-denied"][1],
                       "status": 403, "detail": detail, "rule_id": rule_id, "retryable": False,
                       "spend_delta_micros": 0}
        decision = Decision(effect, rule_id, request.policy_version, request.decision_point,
                            input_digest, self._now(), problem)
        # The record is written before the call is issued, not after the outcome is known.
        self.journal.append({"seq": self._tick(), "dispatch_id": request.context["root_dispatch_id"],
                             "request": request, "decision": decision})
        return decision

    # 4. admit -- the gate: work only ever runs on the far side of an allow
    def admit(self, request: DecisionRequest, work):
        dispatch = request.context["root_dispatch_id"]
        decision = self.decide(request)
        if decision.effect == "deny":
            body = dict(decision.problem)
            body["spend_delta_micros"] = self.meter.spend(dispatch)
            raise Problem("policy-denied", body["detail"], rule_id=decision.rule_id,
                          decision_point=decision.decision_point, policy_version=decision.policy_version,
                          input_digest=decision.input_digest,
                          spend_delta_micros=body["spend_delta_micros"])
        return decision, work(self.meter)

    # 5. explain -- recomputed from the pinned version, never a stored narrative
    def explain(self, input_digest: str, policy_version: str) -> Decision:
        for row in self.journal:
            if row["decision"].input_digest == input_digest and row["decision"].policy_version == policy_version:
                bundle = self.bundles.get(policy_version)
                if bundle is None:
                    raise Problem("policy-version-unknown",
                                  f"{policy_version} is no longer resolvable, so the decision cannot be replayed",
                                  policy_version=policy_version)
                effect, rule_id, detail = self._evaluate(row["request"], bundle)
                return Decision(effect, rule_id, policy_version, row["decision"].decision_point,
                                input_digest, self._now(),
                                row["decision"].problem if effect == "deny" else None)
        raise Problem("document-invalid", f"no decision on file for {input_digest} under {policy_version}",
                      input_digest=input_digest)

    # --- reads the conformance run needs ------------------------------------
    def ordering(self) -> tuple[int, int]:
        """(decisions taken, decisions whose record precedes that dispatch's first metered call)."""
        before = 0
        for row in self.journal:
            first = self.meter.first_seq(row["dispatch_id"])
            if first is None or row["seq"] < first:
                before += 1
        return len(self.journal), before

    def denied_spend_micros(self) -> int:
        return sum(self.meter.spend(row["dispatch_id"]) for row in self.journal
                   if row["decision"].effect == "deny")

    def rule_id_present(self) -> bool:
        return all(row["decision"].rule_id for row in self.journal)

    # --- what an adapter supplies -------------------------------------------
    @abstractmethod
    def _evaluate(self, request: DecisionRequest, bundle: dict) -> tuple[str, str, str]:
        """(effect, rule_id, detail). Reached only after the point, the shape and
        the version pin have held."""

    def _activated(self, bundle: dict, version: str) -> None:
        """What this binding does when a rule set starts serving. Default: nothing."""
