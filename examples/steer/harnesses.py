#!/usr/bin/env python3
"""Reuse, not copy: the loaders the run area already wrote, plus the two
harnesses this area calls that it did not need.

`examples/run/harnesses.py` solves the hard part - several harnesses each
import their own top-level `interface` and `adapters`, so they cannot share one
process by name, and `_load` gives each its own namespace. That file is loaded
here by path, under a name of its own, and extended rather than copied: a second
copy of that loader would be a second thing to keep true. `examples/watch`
extends the same file the same way.

Two names are added to its drop list because the harnesses this area calls own
two more top-level modules (`store`, `run`) than the ones the run area calls.
Without that, a human-interaction `run` module would sit in `sys.modules` under
the same name as this example's own runner.

Python 3.11 standard library only.
"""
from __future__ import annotations

import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def _adopt(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _adopt("run_area_harnesses", os.path.join(ROOT, "examples", "run", "harnesses.py"))
base.HARNESS_LOCAL = tuple(base.HARNESS_LOCAL) + ("store", "run", "conformance", "resume")

reference = base.reference          # the entry-schema validator and the hash-chained ledger
containment = base.containment      # isolation + the agent-runtime operations one cell serves
gateway = base.gateway              # model access: one completion by class
errors = base.errors                # the one shared problem-object construction point
ROOT = base.ROOT


def policy(engine: str = "dryrun"):
    """The decision point. `interface` carries the gate itself - decide() and
    admit() are concrete there, so no engine and no caller can decline the
    registry check, the declared-shape check, the version pin or the ordering.
    An engine supplies `_evaluate` and nothing else."""
    mods = base._load("policy", ["interface", f"adapters.{engine}"])
    return mods["interface"], mods[f"adapters.{engine}"].Adapter


def human(surface: str = "dryrun"):
    """Human interaction. `store` comes with it: the parked state and the typed
    event log belong to the platform, never to whichever surface renders them."""
    mods = base._load("human-interaction", ["interface", "store", f"adapters.{surface}"])
    return mods["interface"], mods["store"], mods[f"adapters.{surface}"].Adapter
