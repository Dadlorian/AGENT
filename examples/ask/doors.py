#!/usr/bin/env python3
"""The four doors: one mapper per producer format, and the intake binding that
derives what the producer never sent.

Read it in this order. MAPPERS is one function per registered producer format,
each turning that producer's own native message into the two members of the job
- intent and payload - and nothing else. `derive_key` composes the idempotency
key from the members of the producer's own message identity that the admission
declaration names for that format, so replay safety is a property of the entry
rather than a courtesy of the caller (X-litmus-d-023). `chain_for` builds the
delegation chain from the identity the transport attested plus the principals
the declaration registered as having authorised that producer, so nothing the
producer's body says about who it is can reach the envelope.

`binding()` returns an adapter class over the work-intake capability interface
in harness/work-intake: accept(), admit() and job_digest() are that interface's
concrete template methods and are not re-implemented here, so the unmapped
producer refusal, the schema check and the replay check run in front of
anything in this file. What a binding supplies is the mapping and the place the
entry is recorded, which is all an adapter is allowed to decide.

No product name appears in this file. Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _short(*parts: str) -> str:
    return hashlib.sha256("".join(parts).encode()).hexdigest()[:12]


# --- the four mappers -------------------------------------------------------
# Each takes the producer's own body and returns (intent, payload). Every other
# member of that body is dropped here: it is producer-specific, it is not part
# of the job, and there is nowhere in the envelope for it to ride along.
def _from_cli_argv(body: dict) -> tuple[dict, dict]:
    argv = list(body["argv"])
    flags = {argv[i]: argv[i + 1] for i in range(1, len(argv) - 1, 2)}
    return ({"workflow_ref": flags["--workflow"], "summary": flags["--summary"]},
            {"report_text": flags["--report"], "window_hours": int(flags["--window-hours"])})


def _from_cloudevents_http(body: dict) -> tuple[dict, dict]:
    data = body["data"]
    return ({"workflow_ref": data["workflow_ref"], "summary": data["summary"]},
            {"report_text": data["report_text"], "window_hours": int(data["window_hours"])})


def _from_schedule_occurrence(body: dict) -> tuple[dict, dict]:
    task = body["task"]
    return ({"workflow_ref": task["workflow"], "summary": task["why"]},
            {"report_text": task["finding"], "window_hours": int(task["window_hours"])})


def _from_a2a_message(body: dict) -> tuple[dict, dict]:
    data = next(part["data"] for part in body["parts"] if part["kind"] == "data")
    return ({"workflow_ref": data["workflow_ref"], "summary": data["summary"]},
            {"report_text": data["report_text"], "window_hours": int(data["window_hours"])})


MAPPERS = {"cli-argv": _from_cli_argv, "cloudevents-http": _from_cloudevents_http,
           "schedule-occurrence": _from_schedule_occurrence, "a2a-message": _from_a2a_message}

# Per format: the body members the mapper reads, and the member that carries the
# producer's own clock. Everything else in a body is dropped, and `dropped` on
# the receipt is computed from these rather than listed by hand, so a member
# that stops being read starts being reported as dropped in the same change.
READS = {"cli-argv": (("argv",), "sent_at"), "cloudevents-http": (("data",), "time"),
         "schedule-occurrence": (("task",), "occurrence"),
         "a2a-message": (("parts", "contextId"), "sentAt")}


def dropped_by(declaration: dict, fmt: str, body: dict) -> list[str]:
    """What the producer sent that reached no envelope field: producer-specific
    attributes, and identity claims a body has no standing to make."""
    reads, clock = READS[fmt]
    consumed = set(reads) | {clock} | set(declaration["key_fields"][fmt])
    return sorted(k for k in body if k not in consumed)


# --- what the boundary sets, and the producer cannot ------------------------
def derive_key(declaration: dict, fmt: str, body: dict, attested: str) -> str:
    """The idempotency key, composed at the boundary from the members of this
    producer's own message identity that the declaration names for its format.

    The producer supplies no key. For the event door those members are the event
    envelope's source and id, which is the settling deduplication identity
    (X-litmus-c-012); for the schedule door they are the recurring item's
    identity and the nominal occurrence, never the wall clock at which the
    firing was received, so a catch-up delivery of the same occurrence derives
    the same key (docs/maturity/closures.md, concern-idempotency).
    """
    fields = declaration["key_fields"][fmt]
    missing = [f for f in fields if f not in body]
    if missing:
        raise KeyError(f"the {fmt} message carries none of the identity members {missing} "
                       f"the declaration derives its key from")
    door = declaration["producers"][fmt]["door"]
    return f"{door}-{_short(fmt, attested, *[str(body[f]) for f in fields])}"


def parent_correlation(declaration: dict, fmt: str, body: dict) -> str | None:
    """The correlation the producer already had, if the declaration names the
    member of that producer's body carrying it.

    Which door was used does not decide this and neither does this file: a
    format with no row in `parent_correlation_fields` has no parent and depth 0,
    and the depth on the envelope is a consequence of having a parent rather
    than a literal written per format. The producer's own correlation becomes
    the parent of this entry and never this run's correlation id, so a partner's
    context cannot be adopted as ours.
    """
    field = declaration.get("parent_correlation_fields", {}).get(fmt)
    return body[field] if field and field in body else None


def chain_for(declaration: dict, fmt: str, attested: str) -> list[dict]:
    """The delegation chain, built from the identity the transport attested and
    the principals the declaration registered behind that producer.

    chain[0] is the acting party and the last element is the root, the order the
    entry envelope already carries. Nothing the producer's body says about who
    it is or whom it acts for is read here, which is what "a caller can neither
    supply, forge, omit nor overwrite it" has to mean in code.
    """
    registration = declaration["producers"][fmt]
    authorised = list(registration["authorised_by"])
    chain = [{"actor": attested, "obtained_via": registration["acting_via"]}]
    for index, principal in enumerate(authorised):
        last = index == len(authorised) - 1
        chain.append({"actor": principal, "obtained_via": "direct" if last else "token_exchange"})
    return chain


def load_producers(path: str | None = None) -> dict:
    """The four native messages, as they arrive. Read, never constructed here."""
    doc = json.load(open(path or os.path.join(HERE, "producers.json")))
    return {k: v for k, v in doc.items() if not k.startswith("_")}


# --- the binding ------------------------------------------------------------
def binding(interface, declaration: dict):
    """One intake adapter class over the work-intake capability interface.

    The class is built here rather than at import time because the interface is
    the harness's, loaded by configuration; this module never imports a harness
    by a fixed path, and it never re-implements accept() or admit().
    """

    class DerivingIntakeAdapter(interface.WorkIntakeAdapter):
        entity = "request-pushed producers, keys derived at the boundary"
        execution_model = "synchronous-request-pushed"
        declared_marker = "entry-recorded-in-request"
        ack_delivery = "in-request"
        idempotency_source = "the members of the producer's own message identity the declaration names"
        registered_mappers = tuple(declaration["producers"])
        producer_present_at_ack = True

        def __init__(self) -> None:
            super().__init__()
            self.declaration = declaration
            self.dropped: dict[str, list[str]] = {}

        def render_message(self, door, subject):
            """The producer side: hand back exactly what arrived at this door."""
            return interface.ProducerMessage(door["format"], dict(door["body"]), dict(door["transport"]))

        def normalise(self, message):
            fmt = message.format
            body, transport = message.body, message.transport
            attested = transport["attested_subject"]
            intent, payload = MAPPERS[fmt](body)
            key = derive_key(self.declaration, fmt, body, attested)
            correlation = {"run_id": "run-" + _short(key), "correlation_id": "corr-" + _short(key),
                           "depth": 0}
            parent = parent_correlation(self.declaration, fmt, body)
            if parent is not None:   # the submitting party's own correlation is the parent,
                correlation["parent_correlation_id"] = parent      # never this run's
                correlation["depth"] = 1   # derived from having a parent, not from which door was used
            self.dropped[fmt] = dropped_by(self.declaration, fmt, body)
            return interface.Envelope(
                kind=self.declaration["producers"][fmt]["door"],
                entry_id=self.declaration["producers"][fmt]["door"] + "-" + _short(key, fmt),
                occurred_at=body[READS[fmt][1]],
                actor={"subject": attested, "delegation_chain": chain_for(self.declaration, fmt, attested)},
                intent=intent,
                correlation=correlation,
                budget=dict(self.declaration["budget"]),      # stamped, never asked for
                idempotency_key=key,
                payload=payload,
                envelope_version=interface.ENVELOPE_VERSION,
            )

        def _record(self, envelope):
            if os.environ.get("INTAKE_FAIL") == "1":     # the failure path, exercised on demand
                raise interface.Problem(
                    "adapter-unavailable",
                    "the intake path was made unreachable by INTAKE_FAIL=1; nothing was admitted",
                    retry_after_s=1)
            return self.declared_marker

    return DerivingIntakeAdapter


def detached_binding(interface, harness_adapter, declaration: dict):
    """The second execution model, from harness/work-intake/adapters/second.py:
    an agent submits a task and detaches, so the acknowledgement is recorded for
    collection rather than read off the wire by whoever sent it.

    Only the door shape differs, so this wrapper translates the four doors into
    the shape that adapter's own render_message reads. Its mapper, its key
    source and its chain are its own; nothing of the deriving binding's is
    reused, which is what makes the two comparable.
    """

    class DetachedIntakeAdapter(harness_adapter):
        def render_message(self, door, subject):
            fmt = door["format"]
            attested = door["transport"]["attested_subject"]
            intent, payload = MAPPERS[fmt](door["body"])
            return super().render_message(
                {"kind": declaration["producers"][fmt]["door"],
                 "entry_id": declaration["producers"][fmt]["door"] + "-"
                 + _short(derive_key(declaration, fmt, door["body"], attested), fmt),
                 "occurred_at": door["body"][READS[fmt][1]],
                 "actor_subject": attested,
                 "chain": tuple((hop["actor"], hop["obtained_via"])
                                for hop in chain_for(declaration, fmt, attested)),
                 "message_identity": derive_key(declaration, fmt, door["body"], attested)},
                {"intent": intent, "payload": payload, "budget": dict(declaration["budget"]),
                 "envelope_version": interface.ENVELOPE_VERSION})

    return DetachedIntakeAdapter


def mutate(fmt: str, body: dict, *, window_hours: int | None = None,
           occurrence: str | None = None, received_at: str | None = None) -> dict:
    """A producer sending a different message: the same message identity with a
    changed job, or the same schedule with a different nominal occurrence or a
    different wall clock at which the firing was received. Producer-side, in the
    producer's own native shape, because that is where a real change happens.
    """
    body = json.loads(json.dumps(body))
    if window_hours is not None:
        if fmt == "cli-argv":
            body["argv"][body["argv"].index("--window-hours") + 1] = str(window_hours)
        elif fmt == "cloudevents-http":
            body["data"]["window_hours"] = window_hours
        elif fmt == "schedule-occurrence":
            body["task"]["window_hours"] = window_hours
        else:
            next(p["data"] for p in body["parts"] if p["kind"] == "data")["window_hours"] = window_hours
    if occurrence is not None:
        body["occurrence"] = occurrence
    if received_at is not None:
        body["received_at"] = received_at
    return body
