#!/usr/bin/env python3
"""Reuse, not copy: load the five harnesses this example calls, and the
reference example's validator, without either drifting from the other.

Every harness under harness/ imports its own top-level `interface`, `adapters`
and helper modules, so five of them cannot be imported into one process by
name. `_load` gives each its own namespace: it puts one harness directory on
the path, imports what was asked for, then removes from sys.modules the
harness-local names it created. The module objects it returns keep working -
their globals hold direct references - and the next harness imports its own
`interface` into a clean slate.

Nothing here is a copy of a harness. Selecting an adapter stays configuration:
the caller passes a name and this module resolves `adapters.<name>.Adapter`,
which is the one export rule every adapter module in the repository follows.

Python 3.11 standard library only.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HARNESS = os.path.join(ROOT, "harness")

# The top-level module names a harness directory owns. Anything imported under
# one of these while a harness is on the path is that harness's, and is dropped
# again so the next harness gets its own.
HARNESS_LOCAL = ("interface", "adapters", "context_guarantees", "problem", "mechanisms", "call")


def _load(directory: str, names):
    path = os.path.join(HARNESS, directory)
    before = set(sys.modules)
    sys.path.insert(0, path)
    try:
        loaded = {name: importlib.import_module(name) for name in names}
    finally:
        while path in sys.path:                 # a harness module may insert its own copy
            sys.path.remove(path)
        for key in list(sys.modules):
            if key not in before and key.split(".")[0] in HARNESS_LOCAL:
                del sys.modules[key]
    return loaded


def _file_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference():
    """The reference example's runner: its schema validator, its hash-chained
    ledger and its canonical JSON form. Loaded by path under a name of its own
    so this example's own run.py never shadows it."""
    return _file_module("e2e_reference", os.path.join(ROOT, "examples", "end-to-end", "run.py"))


def containment(adapter: str):
    """Isolation, and the agent-runtime operations one contained cell serves.

    `call` comes back with it: the harness's own Dispatch is where both ceilings
    are enforced from outside the unit, and an example that re-typed that loop
    would be maintaining a second copy of the thing it is demonstrating.
    """
    mods = _load("containment", ["interface", f"adapters.{adapter}", "call"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter, mods["call"]


def gateway(adapter: str = "dryrun"):
    """Model access: one completion by class. No vendor name reaches it."""
    mods = _load("gateway", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def tool_access(adapter: str = "dryrun"):
    """Tool access: a catalogue discovered at bind time, never compiled in."""
    mods = _load("tool-access", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def packaging(adapter: str = "dryrun"):
    """Capability packaging: resident, body and reference tiers."""
    mods = _load("capability-packaging", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def errors():
    """The one shared construction point for a problem object."""
    mods = _load("errors", ["problem", "interface"])
    return mods["interface"], mods["problem"]
