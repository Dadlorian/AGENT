#!/usr/bin/env python3
"""Today's component: the interpreted engine with real dispatch behind it.

The engine is the same walk adapters/dryrun.py runs - the workflow runner in
examples/end-to-end/run.py, which is what executes a composition on this host
today - with one thing changed: an agent operator is dispatched through the
model gateway PASS.md B3 records as the model-access adapter in place, which on
this host is **LiteLLM** at `$GATEWAY_URL`, rather than through the
deterministic stub. Nothing above this file names it: the operators, the
schema, the documents and both other engines are untouched by which endpoint
answers an agent step.

This file and the env-var table in README.md are the only places a product name
appears in this harness.

Reachability is probed before the run and a failure is reported as the typed
`urn:agentic:problem:adapter-unavailable` rather than failing open. Everything
below the probe is CLAIMED: it has never been executed against a running
endpoint from this harness.

Python 3.11 standard library only; the network is reached with urllib, so this
module imports nothing that is unavailable here.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request

from base import runner                       # noqa: E402
from dryrun import Adapter as InterpretedAdapter    # noqa: E402
from interface import Problem, RunOutcome     # noqa: E402

ENV = ("GATEWAY_URL", "GATEWAY_KEY", "GATEWAY_TIMEOUT_S")


class Adapter(InterpretedAdapter):
    """The interpreted engine, dispatching agent operators over the gateway."""

    engine_marker = "interpreted-walk-gateway/0.1"
    durable_at = "gate-boundary"

    def __init__(self, schema, out_dir, validator, extra_ops=(), dispatch=None):
        super().__init__(schema, out_dir, validator, extra_ops=extra_ops,
                         dispatch=dispatch or runner.OpenAICompatibleAdapter())
        self.ledger_path = os.path.join(out_dir, "live-ledger.jsonl")

    def probe(self) -> None:
        """One reachability check before anything is dispatched. A gateway that
        is not there is one adapter reporting itself unavailable, never an
        outage of the operator vocabulary."""
        url = os.environ.get("GATEWAY_URL", "").rstrip("/")
        if not url:
            raise Problem("adapter-unavailable",
                          "GATEWAY_URL is unset, so the live engine has no endpoint to "
                          "dispatch an agent operator to", env_required=list(ENV))
        req = urllib.request.Request(url + "/v1/models", headers={
            "authorization": "Bearer " + os.environ.get("GATEWAY_KEY", "")})
        try:
            with urllib.request.urlopen(
                    req, timeout=int(os.environ.get("GATEWAY_TIMEOUT_S", "5"))) as resp:
                resp.read(1)
        except Exception as exc:              # urllib.error, socket, ssl, all of them
            raise Problem("adapter-unavailable",
                          f"{type(exc).__name__}: {exc}", endpoint=url) from exc

    def start(self, envelope, workflow, agents) -> RunOutcome:
        self.probe()
        return super().start(envelope, workflow, agents)

    def resume(self, gate_id, decision, delivery_key, note="") -> RunOutcome:
        self.probe()
        return super().resume(gate_id, decision, delivery_key, note=note)
