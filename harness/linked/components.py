#!/usr/bin/env python3
"""How the four finished component harnesses are reached from here.

They are imported as modules and driven through their own capability
interfaces; not one line of their code is copied. Each of them owns a module
called `interface` and a package called `adapters`, so all four cannot sit in
one import namespace at once: `Component.active()` installs one component's
modules for the duration of a call and takes them out again afterwards, and
`Bound` wraps an adapter so every call into it runs inside that window - a
component may import lazily at call time, and a lazy import must find its own
package rather than a neighbour's.

Selection is configuration and nothing else:

    ADAPTER_CONTAINMENT | ADAPTER_GATEWAY | ADAPTER_TRACE | ADAPTER_WORKFLOW
        = dryrun (default) | second | live

No product name appears in this file: it names components by their capability
and reads adapter names from the environment.
"""
from __future__ import annotations

import contextlib
import glob
import importlib
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.dirname(HERE)
REPO = os.path.dirname(HARNESS)

# capability -> (directory, environment variable, adapter class per adapter name)
COMPONENTS = {
    "containment": ("containment", "ADAPTER_CONTAINMENT",
                    {"dryrun": "Adapter", "second": "Adapter", "live": "Adapter"}),
    "gateway": ("gateway", "ADAPTER_GATEWAY",
                {"dryrun": "DryRunAdapter", "second": "BatchClaimAdapter",
                 "live": "LiveGatewayAdapter"}),
    "trace": ("observability", "ADAPTER_TRACE",
              {"dryrun": "Adapter", "second": "Adapter", "live": "Adapter"}),
    "workflow": ("workflow", "ADAPTER_WORKFLOW",
                 {"dryrun": "JournalExecutor", "second": "QueueStateMachineExecutor",
                  "live": "WorkflowEngineExecutor"}),
}
SHARED_NAMES = ("interface", "adapters", "flow", "call", "conformance", "run")


def _conflicting() -> dict[str, Any]:
    return {k: v for k, v in sys.modules.items()
            if k.split(".")[0] in SHARED_NAMES}


class Component:
    """One component harness, imported once and callable many times."""

    def __init__(self, capability: str) -> None:
        directory, env_var, classes = COMPONENTS[capability]
        self.capability = capability
        self.dir = os.path.join(HARNESS, directory)
        self.env_var = env_var
        self.adapter_name = os.environ.get(env_var, "dryrun")
        if self.adapter_name not in classes:
            raise SystemExit(f"{env_var}={self.adapter_name!r}: choose dryrun, second or live")
        self.class_name = classes[self.adapter_name]
        self.modules: dict[str, Any] = {}
        self.import_errors: dict[str, str] = {}
        with self._window():
            self.interface = importlib.import_module("interface")
            importlib.import_module("adapters")
            for path in sorted(glob.glob(os.path.join(self.dir, "adapters", "*.py"))):
                name = os.path.basename(path)[:-3]
                if name == "__init__":
                    continue
                try:                       # an adapter that cannot import is a typed gap,
                    importlib.import_module(f"adapters.{name}")   # never an import crash here
                except Exception as exc:   # noqa: BLE001
                    self.import_errors[name] = f"{type(exc).__name__}: {exc}"

    # -- the import window ---------------------------------------------------
    @contextlib.contextmanager
    def _window(self):
        """This component's modules are the only ones called `interface` or
        `adapters` while the body runs."""
        saved_path, saved_mods = list(sys.path), _conflicting()
        for key in saved_mods:
            del sys.modules[key]
        sys.modules.update(self.modules)
        sys.path[:] = [self.dir] + [p for p in saved_path
                                    if not os.path.abspath(p or ".").startswith(HARNESS)]
        try:
            yield
        finally:
            self.modules = _conflicting()
            for key in list(self.modules):
                del sys.modules[key]
            sys.modules.update(saved_mods)
            sys.path[:] = saved_path

    active = _window

    def build(self, *args, **kwargs):
        """The adapter instance, wrapped so every later call re-enters the window."""
        with self.active():
            module = sys.modules[f"adapters.{self.adapter_name}"]
            return Bound(self, getattr(module, self.class_name)(*args, **kwargs))


class Bound:
    """An adapter reached through its component's import window. It forwards
    attribute access and nothing else: no method is added, renamed or removed,
    so what runs here is the component's own interface."""

    def __init__(self, component: Component, target: Any) -> None:
        object.__setattr__(self, "_component", component)
        object.__setattr__(self, "_target", target)

    def __getattr__(self, name: str):
        attr = getattr(self._target, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            with self._component.active():
                return attr(*args, **kwargs)
        return call


def entry_schema() -> tuple:
    """The published entry schema and the validator the reference runner uses,
    both reached by path rather than reimplemented here."""
    example = os.path.join(REPO, "examples", "end-to-end")
    saved = list(sys.path)
    sys.path.insert(0, example)
    try:
        runner = importlib.import_module("run")
    finally:
        sys.path[:] = saved
    import json
    with open(os.path.join(example, "schemas", "entry.schema.json")) as fh:
        return json.load(fh), runner.validate
