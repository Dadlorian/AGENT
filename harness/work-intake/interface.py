#!/usr/bin/env python3
"""Work intake: whatever produced a job, one canonical envelope comes out.

Read it in this order. ProducerMessage is everything a producer hands over:
the format it claims, the transport metadata the adapter observed, and its own
body. Envelope is the one canonical shape; DOOR_FIELDS names the members a
producer is allowed to differ on and no others. job_digest() is the read that
makes producer equivalence checkable: one logical job digests to one value
however many producers submitted it. resolve_manifest() is a pure function of
the envelope, evaluated outside every adapter, because intake admits and does
not execute - the manifest is what a caller compares across doors without
running anything. WorkIntakeAdapter.accept() and .admit() are template methods:
the unmapped-producer refusal, the schema check and the replay check run in
front of any adapter code, so no binding can decline them.

No product name, endpoint or transport handle appears in this file.
Python 3.11 standard library only.
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
import importlib.util
import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Mapping

INTERFACE_VERSION = "0.1"
ENVELOPE_VERSION = "0.1"
ENTRY_KINDS = ("human", "event", "schedule", "external")

HERE = os.path.dirname(os.path.abspath(__file__))
# The fixtures and the schema are the ones examples/end-to-end already ships;
# the override exists so the tree can be copied elsewhere (the gate's breakage
# run does exactly that) without a second copy of either.
EXAMPLE = os.path.abspath(os.environ.get("INTAKE_EXAMPLE_DIR")
                          or os.path.join(HERE, "..", "..", "examples", "end-to-end"))
SCHEMA_PATH = os.path.join(EXAMPLE, "schemas", "entry.schema.json")
ENTRIES_DIR = os.path.join(EXAMPLE, "entries")


def _validator():
    """The one JSON Schema validator already in this repository, imported by
    path rather than copied, so there is not a second one to disagree with."""
    spec = importlib.util.spec_from_file_location("_e2e_run", os.path.join(EXAMPLE, "run.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate


validate = _validator()
ENTRY_SCHEMA = json.load(open(SCHEMA_PATH))


# --- Typed failures: RFC 9457 problem details, closed registry --------------
# Every row is a row of the registry in docs/decomposition.md 2.1.6. Nothing is
# minted here: an intake that needed a new failure type would need that table
# changed first.
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY: dict[str, tuple[int, str, bool]] = {
    "document-invalid":     (422, "The entry envelope fails validation", False),
    "policy-denied":        (403, "A deterministic pre-admission refusal", False),
    "idempotency-conflict": (409, "Same idempotency key, different job", False),
    "adapter-unavailable":  (503, "The intake adapter is unreachable", True),
}


class Problem(Exception):
    """A failure a producer branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext: Any) -> None:
        if suffix not in REGISTRY:
            raise KeyError(f"{suffix} has no row in the closed problem registry")
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)

    @staticmethod
    def registered(type_uri: str) -> bool:
        return type_uri.startswith(PROBLEM_BASE) and type_uri[len(PROBLEM_BASE):] in REGISTRY


def digest(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --- What a producer hands over --------------------------------------------
@dataclass(frozen=True)
class ProducerMessage:
    """A producer-native message and the transport metadata the adapter saw.

    `transport` is what the adapter observed and is not part of the contract:
    every member of it is mapped onto an envelope field or dropped. A request
    identifier, a repository ref, a command line or a broker offset never
    reaches the envelope.
    """
    format: str
    body: dict
    transport: dict


# --- The one canonical envelope --------------------------------------------
# A producer may differ on these members and on nothing else: which door it
# was, that producer's own message identity and clock, who is acting and on
# whose behalf, the correlation the platform minted, and the key that makes
# the submission safe to repeat.
DOOR_FIELDS = ("kind", "entry_id", "occurred_at", "actor", "correlation", "idempotency_key")


@dataclass(frozen=True)
class Envelope:
    kind: str
    entry_id: str
    occurred_at: str
    actor: dict
    intent: dict
    correlation: dict
    budget: dict
    idempotency_key: str
    payload: dict
    envelope_version: str = ENVELOPE_VERSION

    def dict(self) -> dict:
        return asdict(self)

    def job(self) -> dict:
        """The normalised job: what to run and with what, and nothing about
        who submitted it or when. This is what one logical job means."""
        return {"intent": self.intent, "payload": self.payload}

    def subject(self) -> dict:
        """Everything a producer may not change."""
        return {k: v for k, v in self.dict().items() if k not in DOOR_FIELDS}

    @property
    def actor_subject(self) -> str:
        return self.actor["subject"]

    @property
    def identity_hops(self) -> int:
        return len(self.actor["delegation_chain"])

    @property
    def ceiling_micros(self) -> int:
        return int(self.budget["ceiling_micros"])


@dataclass(frozen=True)
class Acknowledgement:
    """The whole of what a producer gets back. There is no result here and no
    room for one: the producer may be gone before anything runs."""
    entry_id: str
    correlation_id: str
    job_digest: str
    accepted: bool = True
    duplicate_of: str | None = None

    def dict(self) -> dict:
        out = asdict(self)
        if out["duplicate_of"] is None:
            del out["duplicate_of"]
        return out


# --- The resolved manifest: a pure function, outside every adapter ----------
# Intake admits, it does not execute, so no adapter resolves this. A caller
# resolves it from the envelope to compare doors without running anything
# (build-entry-conformance: the comparison is of the resolved manifest, not of
# the final status).
WORKFLOWS: dict[str, tuple[tuple[str, str, int], ...]] = {
    "workflows/triage-and-fix.json": (("read-report", "f-smoke", 1200),
                                      ("locate-fault", "i-fast", 48000),
                                      ("propose-fix", "b-deep", 210000),
                                      ("judge-the-fix", "f-smoke", 1800)),
}


@dataclass(frozen=True)
class Manifest:
    workflow_ref: str
    steps: tuple[tuple[str, str, int], ...]
    total_micros: int
    ceiling_micros: int

    def digest(self) -> str:
        return digest({"workflow_ref": self.workflow_ref, "steps": [list(s) for s in self.steps],
                       "total_micros": self.total_micros, "ceiling_micros": self.ceiling_micros})


def resolve_manifest(envelope: Envelope) -> Manifest:
    """(envelope) -> the priced plan, before anything executes. Reads the job
    and the ceiling; a door field cannot reach it, because none is passed."""
    ref = envelope.intent["workflow_ref"]
    if ref not in WORKFLOWS:
        raise Problem("document-invalid", f"workflow_ref {ref!r} does not resolve to a declared unit",
                      instance=ref)
    weight = 1 + len(json.dumps(envelope.payload, sort_keys=True)) // 200
    steps = tuple((sid, klass, est * weight) for sid, klass, est in WORKFLOWS[ref])
    return Manifest(ref, steps, sum(s[2] for s in steps), envelope.ceiling_micros)


# --- The interface the core imports ----------------------------------------
class WorkIntakeAdapter(ABC):
    """Four operations: accept, normalise, job_digest, admit.

    accept() and admit() are concrete. An adapter supplies the mapping and the
    place the entry is recorded; it does not get to decide whether an
    unregistered producer is refused, whether the envelope is validated, or
    whether a replay is free.
    """

    entity = "unset"
    execution_model = "unset"        # what the producer's submission looks like
    declared_marker = "unset"        # what this binding's transport stamped, read into reports
    ack_delivery = "unset"
    idempotency_source = "unset"     # which producer-side identity becomes the key
    declared_gaps: tuple[str, ...] = ()
    registered_mappers: tuple[str, ...] = ()
    # Consts, not options: every adapter must be able to serve a producer that
    # detaches, so none may promise a result in the acknowledgement, and an
    # unregistered producer format is never admitted on a guess.
    ack_carries_result = False
    refuse_unmapped = True
    selected_by = "configuration"

    def __init__(self) -> None:
        self.admitted: dict[str, Envelope] = {}   # idempotency key -> the first submission
        self.records = 0                          # durable entries written
        self.refusals = 0
        self.work_started = 0                     # intake starts none; counted so it can fail
        self.observed_marker = ""

    # --- normalise: the only adapter-specific operation --------------------
    @abstractmethod
    def normalise(self, message: ProducerMessage) -> Envelope:
        """A producer-native message and the format it claims -> the canonical
        fields, with every producer-specific attribute mapped or dropped."""

    @abstractmethod
    def render_message(self, door: Mapping[str, Any], subject: Mapping[str, Any]) -> ProducerMessage:
        """The producer side: how this binding's producers express one document
        natively. It is here so the same equivalence run drives any binding."""

    @abstractmethod
    def _record(self, envelope: Envelope) -> str:
        """Write the entry where this binding keeps it; return its marker."""

    # --- accept: the whole of what a producer can cause directly -----------
    def accept(self, message: ProducerMessage) -> Envelope:
        if message.format not in self.registered_mappers:
            self.refusals += 1
            raise Problem("policy-denied",
                          f"no registered mapper serves producer format {message.format!r}; "
                          f"an unregistered producer is refused, never admitted on a guess",
                          rule_id="refuse-unmapped-producer", registered=list(self.registered_mappers))
        try:
            envelope = self.normalise(message)
        except Problem:
            raise
        except Exception as exc:      # a mapper that trips is still a typed refusal: no
            self.refusals += 1        # producer, and no agent, is ever handed a stack trace
            raise Problem("document-invalid",
                          f"the {message.format} mapper could not map this message: "
                          f"{type(exc).__name__}: {exc}", instance=message.format) from exc
        errors = validate(envelope.dict(), ENTRY_SCHEMA)
        if errors:
            self.refusals += 1
            raise Problem("document-invalid", "; ".join(errors[:3]), instance=message.format,
                          errors=len(errors))
        return envelope

    def job_digest(self, envelope: Envelope) -> str:
        """One logical job, one digest, whichever producer submitted it."""
        return digest(envelope.job())

    # --- admit: an acknowledgement, and nothing about the outcome ----------
    def admit(self, envelope: Envelope) -> Acknowledgement:
        key, job = envelope.idempotency_key, self.job_digest(envelope)
        first = self.admitted.get(key)
        if first is not None:
            if self.job_digest(first) != job:
                self.refusals += 1
                raise Problem("idempotency-conflict",
                              f"key {key} was accepted for a different job; nothing was admitted",
                              instance=first.entry_id)
            return Acknowledgement(first.entry_id, first.correlation["correlation_id"], job,
                                   duplicate_of=first.entry_id)      # a replay is free
        self.observed_marker = self._record(envelope)
        self.admitted[key] = envelope
        self.records += 1
        return Acknowledgement(envelope.entry_id, envelope.correlation["correlation_id"], job)

    # --- what a report says about a binding --------------------------------
    def axes(self) -> dict:
        return {"execution_model": self.execution_model, "ack_delivery": self.ack_delivery,
                "idempotency_source": self.idempotency_source, "endpoint_marker": self.declared_marker}
