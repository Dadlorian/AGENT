#!/usr/bin/env python3
"""Reuse, not copy: the five capabilities this example calls, loaded through the
loader examples/run already wrote.

Every harness under harness/ imports its own top-level `interface` and
`adapters`, so several cannot be imported into one process by name. That
problem was solved once, in examples/run/harnesses.py; this module imports that
file by path and calls its loader rather than carrying a second copy of the
same namespace juggling. `_load` is private to that module and used here
deliberately: a second copy of it is a second thing to keep true, and the
alternative - copying forty lines - is what the reuse rule exists to stop.

Selecting an adapter stays configuration: a name comes in from the admission
declaration or the command line, and `adapters.<name>.Adapter` is resolved,
which is the one export rule every adapter module in this repository follows.

Python 3.11 standard library only.
"""
from __future__ import annotations

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def _file_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_shared = _file_module("run_harnesses", os.path.join(ROOT, "examples", "run", "harnesses.py"))


def _load(directory: str, names):
    """The shared loader, plus one thing this example needs and examples/run did
    not: harnesses whose import path touches the reference runner leave a path of
    their own on sys.path. `adapters` is a namespace package, so one path left
    behind makes the next `adapters.second` resolve to a different harness's
    file. So each name is imported on its own, sys.path is put back between them,
    and the modules already loaded are re-registered first, so a sibling import
    inside an adapter resolves to the very interface object this call returns
    rather than to a second copy of it.
    """
    loaded: dict = {}
    for name in names:
        saved = list(sys.path)
        for key, module in loaded.items():
            sys.modules.setdefault(key, module)
        try:
            loaded.update(_shared._load(directory, [name]))
        finally:
            sys.path[:] = saved
            for key in loaded:
                sys.modules.pop(key, None)
    return loaded


def reference():
    """The reference example's runner: its schema validator, its hash-chained
    ledger and its canonical JSON form."""
    return _shared.reference()


def work_intake(adapter: str | None = None):
    """Whatever produced a job, one canonical envelope comes out."""
    names = ["interface"] + ([f"adapters.{adapter}"] if adapter else [])
    mods = _load("work-intake", names)
    return (mods["interface"], mods[f"adapters.{adapter}"].Adapter if adapter else None)


def document_validation(adapter: str = "dryrun"):
    """A declared shape against a published dialect, checked at the boundary."""
    mods = _load("document-validation", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def identity(adapter: str = "dryrun"):
    """Attest, exchange, attenuate, verify - and nothing above the interface
    learns which issuer answered."""
    mods = _load("identity", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def policy(adapter: str = "dryrun"):
    """One decision for one unit of work, before anything is spent."""
    mods = _load("policy", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def idempotency(adapter: str = "dryrun"):
    """One claim over a key and a payload digest."""
    mods = _load("idempotency", ["interface", f"adapters.{adapter}"])
    return mods["interface"], mods[f"adapters.{adapter}"].Adapter


def errors():
    """The closed problem-type registry, and the one construction point every
    typed refusal in the platform is rendered through."""
    mods = _load("errors", ["problem", "interface"])
    return mods["interface"], mods["problem"]
