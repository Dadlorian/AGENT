#!/usr/bin/env python3
"""The assessor: the deciding checks, and the only thing that says done.

Host-side. Nothing in this module is ever written into a contract mount, put
into a prompt, or returned to the unit: what travels back is a list of opaque
check ids and pass or fail, which is the whole of what an attempt learns about
its grade. The criterion body is keyed by an opaque handle the unit declaration
carries (`criterion://coupon-behaviour/v1`), so the declaration names its grader
without naming its grade.

It runs after the graded cell is terminal, against the sealed output mounted
read-only, in a cell forked from the seeded snapshot - never against a
filesystem the unit still controls.

The report rule is the platform's, not this example's: an outcome is passed
only if every deciding check ran and passed, and a run in which no behavioural
check executed is inconclusive rather than passed.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os

KINDS = ("behavioural", "well_formedness", "rubric")


def _load_candidate(path: str, tag: str):
    spec = importlib.util.spec_from_file_location(f"candidate_{tag}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_digest(root: str) -> str:
    """Bytes of a whole tree, in one digest. Used to assert the source
    snapshot's own test files came out of the attempt unchanged."""
    rows = []
    for base, _, files in os.walk(root):
        for name in sorted(files):
            if name.endswith(".pyc"):
                continue
            full = os.path.join(base, name)
            rows.append((os.path.relpath(full, root),
                         hashlib.sha256(open(full, "rb").read()).hexdigest()))
    return "sha256:" + hashlib.sha256(json.dumps(sorted(rows)).encode()).hexdigest()


# --- The criterion store. Opaque from the unit's side. ----------------------
def _behavioural(candidate_path, tag):
    module = _load_candidate(candidate_path, tag)
    return module.apply_coupon


def _d_known_tier(ctx):
    return _behavioural(ctx["candidate"], ctx["tag"])({"total": 100.0}, {"tier": "gold"}) == 90.0


def _d_missing_tier(ctx):
    return _behavioural(ctx["candidate"], ctx["tag"])({"total": 100.0}, {}) == 95.0


def _d_unknown_tier(ctx):
    return _behavioural(ctx["candidate"], ctx["tag"])({"total": 100.0}, {"tier": "diamond"}) == 95.0


def _d_source_tests_unchanged(ctx):
    return tree_digest(ctx["source_tests"]) == ctx["source_tests_digest_before"]


def _d_contract_digest_held(ctx):
    return ctx["contract_digest_read_back"] == ctx["contract_digest_ledgered"]


CRITERIA = {
    "criterion://coupon-behaviour/v1": [
        {"check_id": "d-01", "kind": "behavioural", "run": _d_known_tier},
        {"check_id": "d-02", "kind": "behavioural", "run": _d_missing_tier},
        {"check_id": "d-03", "kind": "behavioural", "run": _d_unknown_tier},
        {"check_id": "d-04", "kind": "well_formedness", "run": _d_source_tests_unchanged},
        {"check_id": "d-05", "kind": "well_formedness", "run": _d_contract_digest_held},
    ],
}


def measure(criterion_ref: str, ctx: dict, kinds=KINDS) -> dict:
    """(candidate, criterion) -> check report. A pure function of its inputs;
    it calls no model and reaches no network, so escalating the attempter never
    escalates the measurer."""
    criterion = CRITERIA.get(criterion_ref)
    if criterion is None:
        return {"outcome": "inconclusive", "criterion_ref": criterion_ref, "checks": [],
                "behavioural_run": 0, "detail": "criterion_ref does not resolve"}
    rows, behavioural_run, failed = [], 0, 0
    for check in criterion:
        if check["kind"] not in kinds:
            continue
        try:
            passed = bool(check["run"](ctx))
            detail = ""
        except Exception as exc:                       # a check that errors is a check that failed
            passed, detail = False, f"{type(exc).__name__}: {exc}"
        if check["kind"] == "behavioural":
            behavioural_run += 1
        failed += 0 if passed else 1
        rows.append({"check_id": check["check_id"], "kind": check["kind"],
                     "outcome": "pass" if passed else "fail", "detail": detail})
    outcome = "passed" if (failed == 0 and behavioural_run > 0) else \
              ("inconclusive" if behavioural_run == 0 else "failed")
    return {"outcome": outcome, "criterion_ref": criterion_ref, "checks": rows,
            "behavioural_run": behavioural_run, "checks_run": len(rows), "failed": failed,
            "rubric_reached": False}


def outcomes_for_unit(report: dict) -> list:
    """What the next attempt receives, folded into its contract as declared
    context: an opaque check id and pass or fail. Not the command, not the
    expected value, not the diff, not how many hidden checks exist."""
    return [(row["check_id"], row["outcome"]) for row in report["checks"]]


def failure_signature(report: dict) -> str:
    """The evidence the escalation policy gates on: which deciding checks
    failed, in order. The same signature twice is a capability failure; a
    different one is a different problem."""
    return ",".join(row["check_id"] for row in report["checks"] if row["outcome"] == "fail")
