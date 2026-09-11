#!/usr/bin/env python3
"""The minimal caller: how you would actually call a sandbox. `ADAPTER=dryrun|second|live`.

It names no VMM, runtime binary, network mode or resource limit: isolation is decided for the
caller, who writes an intent and at most one word of profile (REF-3-02).
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from interface import Unit, load

IMAGE = "registry.example/agent-base:2026-09"
WORK = [
    Unit(unit_id="u1", intent="summarise the incident log"),
    Unit(unit_id="u2", intent="summarise the incident log"),
    Unit(unit_id="u3", intent="render the weekly chart", profile="gpu"),
]


def main() -> int:
    sandbox = load(os.environ.get("ADAPTER", "dryrun"))
    bundles: dict = {}
    for unit in WORK:
        if unit.profile not in bundles:   # one bundle per profile, resolved once
            bundles[unit.profile] = sandbox.unpack(IMAGE, unit.profile)
        handle = sandbox.run(bundles[unit.profile], unit)
        running = sandbox.inspect(handle)
        final = sandbox.stop(handle)
        print(f"{unit.unit_id}  {unit.profile:7} {running.status:8} -> {final.status:8} "
              f"warm={str(final.warm):5}  {'>'.join(final.trace):38}  {final.isolation}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
