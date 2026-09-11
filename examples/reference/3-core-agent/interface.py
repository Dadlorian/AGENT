"""Card 3.3 Runtime / Sandbox -- the contract, and nothing behind it.

The shape here is not invented. It is the lifecycle the card's own evidence describes:
an image is unpacked into a bundle, and the bundle is run (X-refmodel-3-3-environment-011);
what you may then ask of it is a required `status` (X-maturity-c-010).

One rule decides what does NOT belong in this file: the caller never configures isolation.
REF-3-02 lists isolation among the things the platform decides for the caller, so no method
here takes a VMM, a runtime binary, a network mode or a resource limit. An adapter names its
own mechanism, on the way out, in `Inspection.isolation` -- an assertion the caller reads,
never one it makes.
"""
from __future__ import annotations

from dataclasses import dataclass

# Verbatim in X-maturity-c-010's snippet; NOT stamped, because no card profile cites the
# enumeration -- only the sentence saying a status is required. See finding 1 in
# docs/reference/profile-sufficiency.md. Marked `proposed` in cards.json for that reason.
STATUS_VALUES = ("creating", "created", "running", "stopped")


class ClaimedNotMeasured(RuntimeError):
    """Raised by an adapter whose path has never run. STATUS row 37.

    An adapter that cannot run must say so in a way a caller cannot mistake for a result.
    A stub returning a plausible `stopped` would make a claimed path indistinguishable from
    a measured one, which is the single thing this repo's evidence rules exist to prevent.
    """


@dataclass(frozen=True)
class Bundle:
    """An OCI Runtime filesystem bundle: what an image becomes before it can be run.

    It carries the profile it was resolved for, because that is the caller's one configurable
    word and a bundle picked for `default` is not the bundle picked for anything else.
    """
    image: str
    digest: str
    profile: str = "default"


@dataclass(frozen=True)
class Unit:
    """The unit of work that runs isolated (F-b3-18).

    `profile` is one word, and only when the default bundle chosen for the intent is wrong
    (REF-3-02). There is deliberately no field for a runtime, an image override or a limit.
    """
    unit_id: str
    intent: str
    profile: str = "default"


@dataclass(frozen=True)
class Inspection:
    handle: str
    status: str
    adapter: str
    isolation: str
    warm: bool
    trace: tuple = ()
    """Every status this handle has held, in order.

    Without it the earlier states are unobservable -- a sandbox that went straight to `running`
    and one that was created first are indistinguishable through `status` alone, and half the
    status domain is decoration. The trace is also where the two execution models differ: a cold
    create passes through `creating`, a claim against a warm pool does not.
    """


class RuntimeSandbox:
    """Every adapter implements exactly this. The caller sees no other surface."""

    name = "abstract"

    def unpack(self, image: str, profile: str = "default") -> Bundle:
        """Resolve the bundle for this profile.

        `profile` is here and not on `run` for a structural reason: it selects the bundle, so it
        has to reach the step that picks one. An earlier cut of this interface took it only on
        `Unit`, where it could never affect anything — found by the hidden check (h-10), not by
        this file's author.
        """
        raise NotImplementedError

    def run(self, bundle: Bundle, unit: Unit) -> str:
        raise NotImplementedError

    def inspect(self, handle: str) -> Inspection:
        raise NotImplementedError

    def stop(self, handle: str) -> Inspection:
        raise NotImplementedError


def load(name: str) -> RuntimeSandbox:
    from importlib import import_module
    mod = import_module(f"adapters.{name}")
    return mod.build()
