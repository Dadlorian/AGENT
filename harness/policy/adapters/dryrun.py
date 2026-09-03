#!/usr/bin/env python3
"""Dry-run adapter: the open-JSON-document decision model, in process, no network.

Stands in for an engine that is queried with a JSON input and answers with a
JSON decision (X-cross-structure-031). It reads the bundle as an open document:
a rule names a path into the request and an operator, and the first matching
rule decides. Deterministic - same request, same bundle, same answer, every run
- so a gate can assert on it with nothing reachable.

Class, point, shape, version pin and ordering are enforced by the interface's
decide() and admit(), which every adapter inherits; this file only says which
rule fired. Failure path on POLICY_FAIL=1.
"""
from __future__ import annotations

import os

from interface import DecisionRequest, PolicyAdapter, Problem


def read(doc: dict, path: str):
    """One path into the request document. A missing path is None, never an error."""
    cur = doc
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def holds(condition: dict, doc: dict) -> bool:
    got, op, value = read(doc, condition["path"]), condition["op"], condition.get("value")
    if op == "eq":
        return got == value
    if op == "ne":
        return got != value
    if op == "exists":
        return got is not None
    if op == "empty":
        return not got
    if op == "nonempty":
        return bool(got)
    if op == "eq_field":
        return got == read(doc, value)
    if op == "ne_field":
        return got != read(doc, value)
    raise Problem("adapter-unavailable", f"the bundle uses operator {op!r}, which this binding cannot evaluate",
                  retry_after_s=0)


def first_match(request: DecisionRequest, bundle: dict) -> tuple[str, str, str]:
    doc = request.as_dict()
    for rule in bundle["rules"]:
        if rule["decision_point"] not in ("*", request.decision_point):
            continue
        if all(holds(condition, doc) for condition in rule["when"]):
            return rule["effect"], rule["rule_id"], rule["detail"]
    fallback = bundle["default"]
    return fallback["effect"], fallback["rule_id"], fallback["detail"]


class DryRunPolicyAdapter(PolicyAdapter):
    entity = "dry-run in-process document query"
    decision_model = "open JSON document query"
    activation_model = "bundle swapped in place; the serving binding keeps running"
    processes_required = "none for the dry run; the document-query model needs a decision endpoint in live use"
    declared_marker = "dryrun-decision"
    report_adapter = "out-of-process-document-query"

    def _evaluate(self, request: DecisionRequest, bundle: dict) -> tuple[str, str, str]:
        if os.environ.get("POLICY_FAIL") == "1":     # the failure path, exercised on demand
            raise Problem("adapter-unavailable",
                          "the decision endpoint was made unreachable by POLICY_FAIL=1; no decision was taken "
                          "and the unit of work was not admitted",
                          decision_point=request.decision_point, retry_after_s=1)
        self.observed_marker = self.declared_marker  # what the answer said
        return first_match(request, bundle)


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunPolicyAdapter
