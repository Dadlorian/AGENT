"""Not an adapter anyone should use. It exists so the gate can be shown to fail.

A criterion nothing can fail is not a criterion. This one returns `ready` -- a status no OCI
runtime defines -- and `test.sh` asserts conformance.py rejects it. If that assertion ever
passes silently, the conformance check has stopped checking.
"""
from __future__ import annotations

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from adapters.dryrun import DryRunSandbox
from interface import Inspection, RuntimeSandbox


class BrokenSandbox(DryRunSandbox):
    name = "_broken_on_purpose"

    def inspect(self, handle: str) -> Inspection:
        return Inspection(handle=handle, status="ready", adapter=self.name,
                          isolation=self.isolation, warm=False, trace=("ready",))


def build() -> RuntimeSandbox:
    return BrokenSandbox()
