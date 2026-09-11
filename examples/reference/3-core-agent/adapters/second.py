"""second -- a genuinely different execution model at the same interface.

Not a second implementation of the same idea: the template/claim split. A template is prepared
once and kept ready; a run claims from that pool instead of creating. Kubernetes SIG Agent
Sandbox already ships this -- "The SandboxTemplate describes the pod the warm pool keeps ready"
(X-refmodel-3-3-environment-006) -- and 3-3.json records its absence here as a gap.

The point of the pair is that `call.py` does not change by a character. What changes is the
lifecycle each unit actually goes through: a claim against a ready pool never passes through
`creating`, because nothing was created for it.
"""
from __future__ import annotations

import hashlib

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from interface import Bundle, Inspection, RuntimeSandbox, Unit


class WarmPoolSandbox(RuntimeSandbox):
    name = "second"
    isolation = "warm pool: a template prepared once, claimed per unit"

    def __init__(self) -> None:
        self._trace: dict = {}
        self._warm: dict = {}
        self._pool: set = set()

    def unpack(self, image: str, profile: str = "default") -> Bundle:
        # Preparing the template IS the unpack here: from this point the pool keeps one ready,
        # which is the whole difference between this model and the cold one.
        digest = hashlib.sha256(f"{image}\n{profile}".encode()).hexdigest()[:16]
        self._pool.add(digest)
        return Bundle(image=image, digest=digest, profile=profile)

    def run(self, bundle: Bundle, unit: Unit) -> str:
        handle = f"{self.name}-{bundle.digest}-{unit.unit_id}"
        warm = bundle.digest in self._pool
        # A claim binds a sandbox the pool already created, so this path never passes through
        # `creating`. That absence is the observable difference, not a label.
        self._trace[handle] = (["created"] if warm else ["creating", "created"]) + ["running"]
        self._warm[handle] = warm
        return handle

    def inspect(self, handle: str) -> Inspection:
        trace = self._trace[handle]
        return Inspection(handle=handle, status=trace[-1], adapter=self.name,
                          isolation=self.isolation, warm=bool(self._warm.get(handle)),
                          trace=tuple(trace))

    def stop(self, handle: str) -> Inspection:
        self._trace[handle].append("stopped")
        return self.inspect(handle)


def build() -> RuntimeSandbox:
    return WarmPoolSandbox()
