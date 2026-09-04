#!/usr/bin/env python3
"""Coverage: the guarantee that no artifact escapes attestation.

interface.py and call.py answer "can one caller get one signed statement over
one artifact it hands us." concern-provenance-q3 asks the question they leave
open (docs/litmus/answers/d.jsonl, score 0): does every artifact PRODUCED over
a period have a record, can that be shown by counting rather than assumed, and
can a component produce one through a path that emits nothing at all.

The first build of this file answered that against two functions it defined
inside itself, with a manifest wiped on every process invocation and a bypass
that was written and then merely noticed. This build fixes all three:

  1. component_a/component_b below the CALLER CODE marker call no attestation
     API of their own, exactly as before -- but emit.attest_and_record(), the
     function that gives them a record anyway, is the SAME function
     examples/end-to-end/run.py's Run.call_agent() and harness/linked/
     linked.py's Linked._run() call at their own real production boundary
     (grep -c attest across both: no longer zero). The demonstration here and
     the wiring there are one piece of code, not two.
  2. emit.py's store is not wiped by construction; `--reset` wipes it exactly
     once, and this file is invoked more than once in test.sh step 6 with no
     reset between the calls, so `artifacts_produced` in `reconcile` grows
     across separate process invocations -- a real period, not a truncated one.
  3. Two breakages, matching the closure's two enforcement layers:
       --break bypass-refused    calls the manifest's only write path with no
                                  attestation and asserts it raises (refused,
                                  not merely counted afterward).
       --break filesystem-escape writes a file straight into the artifact
                                  store's directory, the one route this
                                  process cannot refuse (it does not own the
                                  filesystem) -- and shows reconcile() catches
                                  it anyway because it enumerates the store,
                                  not a self-reported log.

Standard: reuses interface.py's in-toto Statement / DSSE envelope / verify
machinery already cited there (in-toto Attestation Framework + SLSA
provenance). No standard mandates the coverage guarantee itself -- it is
pipeline and admission-policy design, per this item's closure.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emit                                     # noqa: E402  -- THE boundary; see emit.py
# Problem and digest_of come from emit's own privately-loaded interface module
# (see emit.py's docstring on why), not a second, separately-imported copy --
# a `Problem` from a different module instance would not be caught by
# `except Problem` below.
Problem, digest_of = emit.Problem, emit.digest_of


# --------------------------------------------------------------------------
# >>> CALLER CODE: two producing components. Neither imports interface.py,
# neither knows an adapter exists, and both still end up with a record
# because the harness routes their output through emit.attest_and_record().
def component_a(source: bytes) -> bytes:
    return b"summary: " + source[:8] + b"\n"


def component_b(source: bytes) -> bytes:
    return b"digest-report: " + source[::-1] + b"\n"
# --------------------------------------------------------------------------


def _admission_over_ground_truth(root: str) -> dict:
    """Admission checked against every artifact actually on disk, computing
    the digest from the bytes that are really there -- so a file that reached
    the store with no manifest entry at all (the filesystem-escape breakage)
    is still checked, not skipped because it has no entry to look up."""
    admitted = {}
    for artifact_id in emit.produced_artifacts(root):
        with open(os.path.join(root, "artifacts", artifact_id), "rb") as f:
            digest = digest_of(f.read())
        admitted[artifact_id] = emit.admission_check(root, digest)
    return admitted


def main() -> int:
    root = "out/coverage"
    if "--root" in sys.argv:
        root = sys.argv[sys.argv.index("--root") + 1]
    if "--reset" in sys.argv:
        emit.reset(root)
        print(f"period reset: {root} starts empty")

    breakage = None
    if "--break" in sys.argv:
        breakage = sys.argv[sys.argv.index("--break") + 1]
        if breakage not in ("bypass-refused", "filesystem-escape"):
            print(f"unknown --break mode {breakage!r}")
            return 2

    r1 = emit.attest_and_record(root, "component_a", component_a(b"hello world"))
    r2 = emit.attest_and_record(root, "component_b", component_b(b"hello world"))
    print(f"produced via boundary: {r1['artifact_id']}, {r2['artifact_id']} "
          f"(component_a/component_b call no attestation API of their own)")

    if breakage == "bypass-refused":
        # The manifest's one write path, called the way a component skipping
        # attestation would have to call it: no statement_id at all. This
        # must be REFUSED, not written and caught later.
        digest = digest_of(b"snuck in with no attestation\n")
        try:
            emit.register_or_refuse(root, "bypass-artifact", digest, "bypass", statement_id=None)
            print("BYPASS NOT REFUSED: a manifest entry was written with no attestation")
        except Problem as p:
            print(f"bypass refused at write time: {p.body['detail']}")

    elif breakage == "filesystem-escape":
        # The one route attest_and_record cannot refuse, because refusing it
        # would require owning the filesystem, not just the manifest API: a
        # file dropped straight into the artifact store's directory, with no
        # call to attest_and_record and no manifest line at all.
        payload = b"snuck in with no attestation, no manifest line either\n"
        artifacts_dir = os.path.join(root, "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        with open(os.path.join(artifacts_dir, "bypass-artifact"), "wb") as f:
            f.write(payload)
        print("deliberate breakage: a file was written directly into the artifact store's "
              "directory, bypassing attest_and_record and the manifest entirely -- this is "
              "the escape reconcile() must catch by enumerating the store, not by trusting it")

    report = emit.reconcile(root)
    print("reconcile: " + json.dumps(report))

    admitted = _admission_over_ground_truth(root)
    print("admission_check: " + json.dumps(admitted))

    ok = report["reconciled"] and all(admitted.values())
    print("COVERAGE OK: artifacts actually in the store equal attestations that resolve for them, "
          "nothing admitted without one"
          if ok else
          "COVERAGE VIOLATION: an artifact exists in the store with no attestation the adapter "
          "can resolve, and admission_check refuses it")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
