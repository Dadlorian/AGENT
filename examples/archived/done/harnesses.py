#!/usr/bin/env python3
"""Reuse, not copy: the loaders the run area already wrote, plus the four
harnesses this area calls that it did not need.

`examples/run/harnesses.py` solves the hard part - several harnesses each
import their own top-level `interface` and `adapters`, so they cannot share one
process by name, and `_load` gives each its own namespace. That file is loaded
here by path, under a name of its own, and extended rather than copied, the way
`examples/steer/harnesses.py` and `examples/watch/harnesses.py` extend it.

Two additions this area needs:

  * three more names on the drop list (`store`, `emit`, `coverage`), because the
    harnesses called here own top-level modules the run area's list did not
    cover;
  * `emit()`, which loads `harness/provenance/emit.py` by path rather than
    through `_load`. That module deliberately loads its own interface privately
    (see its docstring) because it is imported from inside other harnesses'
    processes; loading it by path here keeps that property and keeps this
    example calling the same wired boundary `examples/end-to-end/run.py` and
    `harness/linked/linked.py` call, instead of a second copy of it.

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
base.HARNESS_LOCAL = tuple(base.HARNESS_LOCAL) + ("store", "emit", "coverage")

reference = base.reference          # the entry-schema validator and the hash-chained ledger
errors = base.errors                # the one shared problem-object construction point
ROOT = base.ROOT


def provenance(adapter: str = "dryrun"):
    """Provenance. `interface` carries the whole verification path: verify() is
    a module function that reads no store and no adapter, which is the property
    a third party's check rests on, and attest() is concrete on the base class
    so no binding can decline the code-version/inputs/actor check."""
    mods = base._load("provenance", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def state(adapter: str = "second"):
    """State persistence. `append` is concrete on the interface, so no binding
    can decline the expected-head check or the fencing check."""
    mods = base._load("state-persistence", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def identity(adapter: str = "dryrun"):
    """Identity. verify, attest and delegate are concrete on the interface, so
    no binding can decline scope narrowing, lifetime shortening or acyclicity."""
    mods = base._load("identity", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def emit():
    """The one wired boundary a producing path calls to get a record, loaded by
    path so this example calls the same module object shape the reference
    example and the linked harness call, not a copy."""
    return _adopt("done_provenance_emit", os.path.join(ROOT, "harness", "provenance", "emit.py"))


def state_external_verifier() -> str:
    """The independent verifier's path. It imports no interface and no adapter,
    so it is run as a subprocess, never imported."""
    return os.path.join(ROOT, "harness", "state-persistence", "verify_external.py")
