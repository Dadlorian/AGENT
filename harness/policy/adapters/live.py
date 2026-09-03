#!/usr/bin/env python3
"""Live adapter for the policy engine this stack names today.

Product names are allowed in this file and nowhere else. Today that engine is
OPA with Rego: PASS.md A5 records the policy provisioning concern as
"Rego / Open Policy Agent" (F-a5-05) and PASS.md B3 names OPA as the adapter
today for this capability (F-b3-11). PASS.md A6 also records what is true of it
here: "Conformance checks exist; not wired into the enforcement path"
(F-a6-04) - so this binding is adoption into the path, not migration within it.

Decision model: the engine is queried with a JSON input and answers with a JSON
decision (X-cross-structure-031: "To make an authorization decision, an
application queries OPA with JSON input, and OPA evaluates the input against the
specified policies to return an access decision in JSON").

No route is invented here. POLICY_DECISION_URL is supplied whole by the
operator (see README.md), exactly as the batch routes are in harness/gateway.
The mapping of the answer - result.effect / result.allow and result.rule_id -
is proposed: no decision-log or decision-API response schema has been fetched
on this host, so it stays claimed until run against a real engine.

Standard library only; the import is guarded so this module never breaks a dry
run on a host with no network stack available.
"""
from __future__ import annotations

import json
import os

from interface import DecisionRequest, PolicyAdapter, Problem, canonical

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None


class LivePolicyAdapter(PolicyAdapter):
    entity = "policy engine on this host (OPA / Rego today)"
    decision_model = "open JSON document query, out of process"
    activation_model = "bundle reloaded in place by the engine; the process keeps running"
    processes_required = "the decision endpoint must be reachable for any dispatch to be admitted"
    declared_marker = "engine-decision"
    report_adapter = "out-of-process-document-query"

    def _activated(self, bundle: dict, version: str) -> None:
        # The engine serves whatever bundle the operator loaded into it. Its digest
        # is declared here rather than pushed from the harness, so a request pinned
        # to the served version resolves. Claimed: never checked against an engine.
        served = os.environ.get("POLICY_BUNDLE_VERSION")
        if served:
            self.bundles[served] = bundle

    def _env(self, name: str, default: str | None = None) -> str:
        value = os.environ.get(name, default)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the policy engine cannot be reached, so no decision was taken "
                          f"and the unit of work was not admitted",
                          retry_after_s=30)
        return value

    def _evaluate(self, request: DecisionRequest, bundle: dict) -> tuple[str, str, str]:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        url = self._env("POLICY_DECISION_URL")
        headers = {"content-type": "application/json",
                   # Correlation rides on an explicit header, never on trace parentage (F-a7-02).
                   "x-correlation-id": os.environ.get("CORRELATION_ID", "corr-harness-policy"),
                   "x-run-id": request.context["run_id"]}
        token = os.environ.get("POLICY_TOKEN")
        if token:
            headers["authorization"] = "Bearer " + token
        # Canonical bytes: the same question, byte for byte, that every other binding is asked.
        body = canonical({"input": request.as_dict()})
        try:
            with URLLIB.urlopen(URLLIB.Request(url, data=body, headers=headers),
                                timeout=int(os.environ.get("POLICY_TIMEOUT_S", "30"))) as response:
                answer = json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:400].decode("utf-8", "replace")
            raise Problem("adapter-unavailable", f"HTTP {exc.code}: {detail}", retry_after_s=30) from exc
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc
        result = answer.get("result")
        if not isinstance(result, dict):
            raise Problem("adapter-unavailable",
                          "the engine returned no decision object, so nothing was admitted", retry_after_s=30)
        effect = result.get("effect") or ("allow" if result.get("allow") is True else "deny")
        rule_id = result.get("rule_id") or ""
        detail = result.get("detail") or f"decided by {rule_id or 'an unnamed rule'}"
        self.observed_marker = self.declared_marker
        return effect, rule_id, detail


# The one name every adapter module exports: the entry point of this module.
Adapter = LivePolicyAdapter
