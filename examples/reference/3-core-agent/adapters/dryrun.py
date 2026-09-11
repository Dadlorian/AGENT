"""dryrun -- the cold path, deterministic, no infrastructure.

Cold means the bundle is unpacked for this run and thrown away with it: every unit pays the
whole create. That is the behaviour the second adapter exists to contrast with.
"""
from __future__ import annotations

import hashlib

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from interface import Bundle, Inspection, RuntimeSandbox, Unit


class DryRunSandbox(RuntimeSandbox):
    name = "dryrun"
    isolation = "dry-run: nothing is contained, and this adapter says so"

    def __init__(self) -> None:
        self._trace: dict = {}

    def unpack(self, image: str, profile: str = "default") -> Bundle:
        digest = hashlib.sha256(f"{image}\n{profile}".encode()).hexdigest()[:16]
        return Bundle(image=image, digest=digest, profile=profile)

    def run(self, bundle: Bundle, unit: Unit) -> str:
        handle = f"{self.name}-{bundle.digest}-{unit.unit_id}"
        # The cold path creates a sandbox for this unit, so it passes through `creating`.
        self._trace[handle] = ["creating", "created", "running"]
        return handle

    def inspect(self, handle: str) -> Inspection:
        trace = self._trace[handle]
        return Inspection(handle=handle, status=trace[-1], adapter=self.name,
                          isolation=self.isolation, warm=False, trace=tuple(trace))

    def stop(self, handle: str) -> Inspection:
        self._trace[handle].append("stopped")
        return self.inspect(handle)


def build() -> RuntimeSandbox:
    return DryRunSandbox()
