#!/usr/bin/env python3
"""Reuse, not copy: the loader the run area already wrote, plus the one harness
this area calls that no earlier area did.

`examples/run/harnesses.py` solves the hard part - several harnesses each import
their own top-level `interface` and `adapters`, so they cannot share one process
by name, and its `_load` gives each its own namespace. That file is loaded here
by path, under a name of its own, and extended rather than copied; `examples/steer`
and `examples/watch` extend the same file the same way.

Only one name is added to its drop list: the improvement-loop harness owns a
top-level `conformance` module. It does not own the gate. Its own `interface.py`
loads `harness/evaluation/interface.py` under the module name
`gate_evaluation_interface` and each evaluation adapter under
`gate_evaluation_adapter_<name>`, so the evaluation capability is reached through
the improvement loop's own binding to it and this file never loads a second copy
of it. That is the point of the composition: the gate is not re-declared.

Python 3.11 standard library only.
"""
from __future__ import annotations

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def _adopt(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _adopt("run_area_harnesses", os.path.join(ROOT, "examples", "run", "harnesses.py"))
base.HARNESS_LOCAL = tuple(base.HARNESS_LOCAL) + ("conformance",)

reference = base.reference          # the entry-schema validator and the hash-chained ledger
errors = base.errors                # the one shared problem-object construction point
ROOT = base.ROOT


# The drivers this example may select. `live` is deliberately not loaded: an example
# reaches no live endpoint and no credential (build-example, "no live credential,
# live endpoint or vendor client is reachable from an example").
DRIVERS = ("dryrun", "second")

_loaded: dict = {}


def improvement_loop():
    """The improvement loop, and through it the evaluation gate.

    Returns the capability interface and a factory that builds the driver named by
    configuration: `build("second", gate=..., decision_rule=...)`. Both drivers come
    from one load, so one interface module backs every object this example passes
    between them.

    The factory exists, and the module name is pinned afterwards, because a driver
    resolves its default promotion rule at construction - and again inside
    `next_fire()`, in a fresh binding this file never sees - with
    `from interface import promote_on_pass`. The run area's loader takes the
    harness's own top-level `interface` back out of `sys.modules` so the next
    harness gets a clean slate; this example loads no harness after this one, so the
    name is put back and left, pointing at the module the objects above it came
    from. Without that, a per-fire driver rebinding itself would resolve `interface`
    against whatever else is on `sys.path`.
    """
    if not _loaded:
        _loaded.update(base._load("compose-improvement-loop",
                                  ["interface"] + [f"adapters.{d}" for d in DRIVERS]))
        sys.modules["interface"] = _loaded["interface"]
    interface = _loaded["interface"]

    def build(driver: str, gate=None, decision_rule=None):
        if driver not in DRIVERS:
            raise SystemExit(f"unknown driver {driver!r}; choose one of {', '.join(DRIVERS)}")
        return _loaded[f"adapters.{driver}"].Adapter(gate=gate, decision_rule=decision_rule)

    return interface, build
