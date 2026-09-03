#!/usr/bin/env python3
"""Live binding: the intake path this deployment runs today.

Product names are allowed in this file and nowhere else. What PASS.md records
about intake here is thin and is not enlarged: an Ansible role named
`git_events` is one of the nine configuration-management roles on this host
(PASS.md A5, F-a5-01), and PASS.md B3 records the producers today as CLI, git
event, HTTP and schedule (F-b3-08). No endpoint, path, port or payload profile
for any of them is recorded anywhere on file, so none is invented here: the
whole URL comes from the operator through INTAKE_URL, and the event is sent in
the structured content mode of the event standard, whose version is unverified
because every record on file for it is a search result rather than fetched
specification text.

Two gaps are declared rather than papered over, both recorded facts of this
host: there is no identity field anywhere in the system (F-a6-05), so the
delegation chain this mapper builds is new construction and starts as a single
attested hop supplied by the producer; and typed errors are absent (F-a6-06),
so an HTTP failure body is turned into a registered problem here rather than
being assumed to arrive as one.

Standard library only; the import is guarded so this module never breaks a dry
run on a host with no network stack.
"""
from __future__ import annotations

import json
import os
from typing import Any, Mapping

from interface import Envelope, Problem, ProducerMessage, WorkIntakeAdapter, digest

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None


class DeployedHttpIntakeAdapter(WorkIntakeAdapter):
    entity = "the intake endpoint on this host (the git_events Ansible role's receiver today)"
    execution_model = "synchronous-request-pushed"
    declared_marker = "entry-recorded-by-endpoint"
    ack_delivery = "in-request"
    idempotency_source = "the producer's own message identity (source plus id)"
    registered_mappers = ("cloudevents-http",)
    declared_gaps = ("no identity field exists on this host, so the delegation chain is new construction",
                     "typed errors are absent on this host, so a failure body is typed here")

    def _env(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the intake endpoint cannot be reached and "
                          f"nothing was admitted", retry_after_s=30)
        return value

    # --- the producer side --------------------------------------------------
    def render_message(self, door: Mapping[str, Any], subject: Mapping[str, Any]) -> ProducerMessage:
        """One document as a structured event pushed over a request. All four
        producers reach this endpoint the same way; the door is an attribute,
        not a route, so no producer gets a path of its own."""
        job = {"intent": subject["intent"], "budget": subject["budget"],
               "payload": subject["payload"], "envelope_version": subject["envelope_version"]}
        body = {"specversion": "1.0",
                "type": "job.submitted." + door["kind"],
                "source": "/producers/" + door["kind"],
                "id": door["entry_id"],
                "time": door["occurred_at"],
                "subject": door["message_identity"],
                "datacontenttype": "application/json",
                "submitter": door["actor_subject"],
                "onbehalfof": [list(hop) for hop in door["chain"]],
                "priority": "high",                    # producer-specific; dropped, never carried
                "data": job}
        transport = {"handle": f"transport-handle-{door['kind']}-http",
                     "content_type": "application/cloudevents+json"}
        return ProducerMessage("cloudevents-http", body, transport)

    # --- normalise ----------------------------------------------------------
    def normalise(self, message: ProducerMessage) -> Envelope:
        body = message.body
        job = body["data"]
        kind = body["type"].rsplit(".", 1)[-1]
        key = digest(job)[7:19]
        return Envelope(
            kind=kind,
            entry_id=body["id"],
            occurred_at=body["time"],
            actor={"subject": body["submitter"],
                   "delegation_chain": [{"actor": a, "obtained_via": v} for a, v in body["onbehalfof"]]},
            intent=dict(job["intent"]),
            correlation={"run_id": f"run-{kind}-{key}", "correlation_id": f"corr-{kind}-{key}", "depth": 0},
            budget=dict(job["budget"]),
            # source plus id is what the producer must keep unique; the key is
            # derived from it and is never minted on arrival.
            idempotency_key=body["subject"],
            payload=dict(job["payload"]),
            envelope_version=job["envelope_version"],
        )

    def _record(self, envelope: Envelope) -> str:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment",
                          retry_after_s=30)
        url = self._env("INTAKE_URL")
        event = {"specversion": "1.0", "type": "job.submitted." + envelope.kind,
                 "source": "/intake/" + envelope.kind, "id": envelope.entry_id,
                 "time": envelope.occurred_at, "datacontenttype": "application/json",
                 "data": envelope.dict()}
        headers = {"content-type": "application/cloudevents+json",
                   "idempotency-key": envelope.idempotency_key,
                   "x-correlation-id": envelope.correlation["correlation_id"]}
        token = os.environ.get("INTAKE_TOKEN")
        if token:
            headers["authorization"] = "Bearer " + token
        req = URLLIB.Request(url, data=json.dumps(event).encode(), headers=headers)
        try:
            with URLLIB.urlopen(req, timeout=int(os.environ.get("INTAKE_TIMEOUT_S", "30"))) as resp:
                json.load(resp)
                return resp.headers.get("x-intake-marker", self.declared_marker)
        except urllib.error.HTTPError as exc:                      # pragma: no cover - live only
            detail = exc.read()[:400].decode("utf-8", "replace")
            if exc.code == 409:
                raise Problem("idempotency-conflict", f"the endpoint refused the key: {detail}",
                              instance=envelope.idempotency_key) from exc
            if exc.code == 422:
                raise Problem("document-invalid", f"the endpoint refused the envelope: {detail}",
                              instance=envelope.entry_id) from exc
            raise Problem("adapter-unavailable", f"HTTP {exc.code}: {detail}", retry_after_s=30) from exc
        except Exception as exc:                                   # pragma: no cover - live only
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc


Adapter = DeployedHttpIntakeAdapter
