#!/usr/bin/env python3
"""Reuse, not copy: this area calls five harnesses and the reference example's
validator, and it loads them through the loader `examples/run/harnesses.py`
already publishes rather than re-typing the namespace dance.

`examples/run/harnesses.py` isolates each harness in its own namespace because
every harness imports its own top-level `interface`, `adapters` and helpers, so
two of them cannot be imported into one process by name. That module owns the
mechanism; this one owns the list of names the progress area needs, which is a
different list, and it widens the module's HARNESS_LOCAL tuple with the extra
top-level names these five harnesses own (`journal`, `store`, `unit_under_test`,
`flow`, `driver`, `base`, `conformance`) so those are dropped again too.

Selecting an adapter stays configuration: a caller passes a name and this module
resolves `adapters.<name>.Adapter`, the one export rule every adapter module in
the repository follows.

Python 3.11 standard library only.
"""
from __future__ import annotations

import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

_spec = importlib.util.spec_from_file_location(
    "progress_run_harnesses", os.path.join(ROOT, "examples", "run", "harnesses.py"))
_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_run)

# The extra top-level names these five harnesses own, so the loader drops them
# again and the next harness imports its own.
_run.HARNESS_LOCAL = tuple(sorted(set(_run.HARNESS_LOCAL) | {
    "journal", "store", "unit_under_test", "flow", "driver", "base", "conformance"}))

reference = _run.reference          # the end-to-end example's validator and ledger


def durable(adapter: str = "dryrun"):
    """Durable execution: begin_run, checkpoint_step, resume_point, read_run,
    read_receipt, park_gate, record_decision - plus the shapes the run declares.

    The journal module comes back with it: its keyed, append-only table is the
    one this area's outward-call table is, so the count of calls that left the
    unit is kept the same way the count of effects is, and by neither this
    example nor the executor that is being asked about."""
    mods = _run._load("workflow", ["interface", f"adapters.{adapter}", "adapters.journal"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter, mods["adapters.journal"]


def scheduling():
    """Scheduling: the pure recurrence evaluator, the declaration, the envelope
    builder and the (unit, occurrence) idempotency key. No adapter is bound: the
    schedule door here expands and fires through the shared pure functions."""
    return _run._load("scheduling", ["interface"])["interface"]


def compensation(adapter: str = "dryrun"):
    """Compensation: the irreversibility class, the declared undo, the register."""
    mods = _run._load("xc-compensation", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def evaluation():
    """Evaluation: the case, the case-set handle, the scorer, the report and the
    release gate whose status is read from the report's own counters."""
    return _run._load("evaluation", ["interface"])["interface"]


def errors():
    """The one shared construction point for a problem body, and the closed
    registry the suffix and its extension members are checked against."""
    return _run.errors()


def operators():
    """Composition operators: the closed set, read from the schema the engine is
    handed and never re-typed here."""
    return _run._load("compose-operators", ["interface"])["interface"]
