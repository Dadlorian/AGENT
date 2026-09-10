#!/usr/bin/env python3
"""The driver: what the harness does inside the cell, on one attempt.

Separated from the assessor on purpose. This module may read the contract, the
source snapshot and the visible checks; it may write one candidate into the
output role. It never sees a deciding check, and there is no import path from
here to assessor.py.

The work itself is a deterministic stand-in for a model-driven harness: the
model door is real (the completion comes back through the gateway capability,
by class, with its tokens and cost), and the edit the stand-in makes depends on
one thing only - whether a folded outcome from a previous attempt named a
behavioural check that failed. That is what makes attempt 1 (cold) and attempt
2 (folded) different runs rather than the same run twice.

Python 3.11 standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

HEAD = '''"""Candidate produced inside the cell. Written to the output role,
never back into the read-only source snapshot."""

TIERS = {"standard": 0.05, "gold": 0.10, "platinum": 0.15}


def apply_coupon(order, coupon):
'''

# Handles the missing tier the report named. An unknown tier still raises.
PARTIAL = HEAD + '''    rate = TIERS[coupon.get("tier", "standard")]
    return round(order["total"] * (1 - rate), 2)
'''

# Handles both shapes of the same fault: absent, and present but unminted.
FULL = HEAD + '''    rate = TIERS.get(coupon.get("tier", "standard"), TIERS["standard"])
    return round(order["total"] * (1 - rate), 2)
'''


def prompt(manifest: dict, task: str) -> str:
    """What leaves the cell for the model door. Built from the contract mount,
    so a widened seed would change the prompt as well as the digest."""
    resident = ", ".join(f"{e['path']}@{e['digest'][7:15]}" for e in manifest["entries"])
    return (f"{task}\nContract {manifest['contract_digest'][7:19]} attempt {manifest['attempt']}; "
            f"resident entries: {resident}. Return one candidate for pricing/coupon.py.")


def produce(manifest: dict, folded, stuck: bool, completion_text: str, out_dir: str) -> dict:
    """One candidate, written once. The output role is append-only from inside:
    an attempt writes its own entry and never overwrites attempt n-1's."""
    learned = any(outcome == "fail" for _, outcome in (folded or []))
    body = PARTIAL if (stuck or not learned) else FULL
    note = json.dumps({"attempt": manifest["attempt"], "cold": not folded,
                       "model_note": completion_text[:120]}, sort_keys=True)
    target = os.path.join(out_dir, "coupon.py")
    if os.path.exists(target):
        raise RuntimeError("output entries are write-once; attempt n cannot overwrite attempt n-1")
    os.makedirs(out_dir, exist_ok=True)
    with open(target, "w") as fh:
        fh.write(body)
    with open(os.path.join(out_dir, "note.json"), "w") as fh:
        fh.write(note)
    return {"path": target, "bytes": len(body.encode()), "shape": "partial" if body is PARTIAL else "full"}


def run_visible(candidate_path: str) -> list:
    """The unit's own feedback surface, run as often as it likes. These do not
    decide: they are the checks the unit optimises against, which is the reason
    the deciding set is held out."""
    spec = importlib.util.spec_from_file_location("candidate_visible", candidate_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    visible = importlib.util.spec_from_file_location(
        "visible_checks", os.path.join(HERE, "source", "tests", "test_coupon_visible.py"))
    checks = importlib.util.module_from_spec(visible)
    visible.loader.exec_module(checks)
    return [(check_id, "pass" if ok else "fail")
            for check_id, ok in checks.visible_checks(module.apply_coupon)]
