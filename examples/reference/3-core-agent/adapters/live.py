"""live -- Firecracker microVM. Claimed, never measured. STATUS row 37.

"Firecracker microVM - hardware virtualisation, not a container" (F-a3-01) is what this adapter
would be. It is here so the interface has a live implementation at the same signatures, which is
what build-principles.json's `alive_means` requires -- and every method refuses, loudly, because
no harness in this repo has run its live adapter against a real host from a session.

The refusal IS the honest behaviour. A stub returning `stopped` would let a claimed path be read
as a measured one.
"""
from __future__ import annotations

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from interface import Bundle, ClaimedNotMeasured, Inspection, RuntimeSandbox, Unit

WHY = ("live path claimed, not measured: no harness has run against a real host from a "
       "session (STATUS row 37)")


class FirecrackerSandbox(RuntimeSandbox):
    name = "live"
    isolation = "Firecracker microVM: hardware virtualisation, not a container"

    def unpack(self, image: str, profile: str = "default") -> Bundle:
        raise ClaimedNotMeasured(WHY)

    def run(self, bundle: Bundle, unit: Unit) -> str:
        raise ClaimedNotMeasured(WHY)

    def inspect(self, handle: str) -> Inspection:
        raise ClaimedNotMeasured(WHY)

    def stop(self, handle: str) -> Inspection:
        raise ClaimedNotMeasured(WHY)


def build() -> RuntimeSandbox:
    return FirecrackerSandbox()
