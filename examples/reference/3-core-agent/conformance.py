#!/usr/bin/env python3
"""Does this adapter honour card 3.3's contract? Returns findings, never a bare boolean.

    python3 conformance.py <adapter>      exit 1 on any finding

What it checks is only what the card's evidence supports: the lifecycle runs image -> bundle ->
run (X-refmodel-3-3-environment-011), inspection yields a status, and that status is one of the
four the OCI runtime spec defines. It does not check isolation actually happened -- no adapter
here can demonstrate that, and saying so is the point of the `isolation` string.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from interface import STATUS_VALUES, RuntimeSandbox, Unit, load

CONTRACT = ("unpack", "run", "inspect", "stop")


def check(sandbox) -> list:
    findings = []
    for method in CONTRACT:
        if not callable(getattr(sandbox, method, None)):
            findings.append(f"missing contract method `{method}`")
    if findings:
        return findings

    bundle = sandbox.unpack("registry.example/agent-base:2026-09")
    for field in ("image", "digest"):
        if not getattr(bundle, field, None):
            findings.append(f"unpack returned no `{field}`")
    other = sandbox.unpack("registry.example/agent-base:2026-09", "gpu")
    if other.profile != "gpu":
        findings.append(f"unpack ignored the profile: bundle reports {other.profile!r}")
    if other.digest == bundle.digest:
        findings.append("unpack returned the same bundle for two different profiles: the "
                        "caller's one configurable word selects nothing")

    handle = sandbox.run(bundle, Unit(unit_id="c1", intent="conformance"))
    running = sandbox.inspect(handle)
    stopped = sandbox.stop(handle)

    for label, got in (("after run", running.status), ("after stop", stopped.status)):
        if got not in STATUS_VALUES:
            findings.append(f"{label}: status {got!r} is not one of {list(STATUS_VALUES)}")
    if running.status in STATUS_VALUES and running.status != "running":
        findings.append(f"after run: status is {running.status!r}, expected 'running'")
    if stopped.status in STATUS_VALUES and stopped.status != "stopped":
        findings.append(f"after stop: status is {stopped.status!r}, expected 'stopped'")
    for label, got in (("after run", running), ("after stop", stopped)):
        off = [s for s in got.trace if s not in STATUS_VALUES]
        if off:
            findings.append(f"{label}: trace holds {off} outside {list(STATUS_VALUES)}")
        elif list(got.trace) != sorted(got.trace, key=STATUS_VALUES.index):
            findings.append(f"{label}: trace {list(got.trace)} is not in lifecycle order")
        if got.trace and got.trace[-1] != got.status:
            findings.append(f"{label}: status {got.status!r} is not the end of trace "
                            f"{list(got.trace)}")
    if not running.trace:
        findings.append("inspect returned an empty trace: the lifecycle is unobservable")
    if not running.isolation:
        findings.append("inspect returned no `isolation`: an adapter must name what it asserts")
    if running.adapter != sandbox.name:
        findings.append(f"inspect reports adapter {running.adapter!r}, adapter is {sandbox.name!r}")
    return findings


def signature_parity() -> list:
    """Every adapter must be callable identically -- that is what makes the swap a swap."""
    import inspect as _i
    findings = []
    base = {m: str(_i.signature(getattr(RuntimeSandbox, m))) for m in CONTRACT}
    for name in ("dryrun", "second", "live"):
        got = {m: str(_i.signature(getattr(type(load(name)), m))) for m in CONTRACT}
        for m in CONTRACT:
            if got[m] != base[m]:
                findings.append(f"{name}.{m}{got[m]} differs from contract {base[m]}")
    return findings


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
    findings = check(load(name))
    for f in findings:
        print(f"  finding: {f}")
    print(f"{name}: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
