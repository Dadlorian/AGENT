#!/usr/bin/env python3
"""The minimal call: one document in through four doors, one job out.

    ADAPTER=dryrun python3 harness/work-intake/call.py
    ADAPTER=second python3 harness/work-intake/call.py

Everything below the CALLER CODE marker is what a caller writes: hand each
producer the same document, read one envelope and one acknowledgement back,
resolve the manifest, see the typed refusal a malformed task gets, and replay
one submission. Everything above it is the platform: the correlation id, the
budget ceiling, the idempotency key and the actor's delegation chain are
stamped onto the envelope by the mapper and the interface without the producer
asking for them or being able to decline them, and one environment variable
binds one of three adapters.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import producers                                                     # noqa: E402
from interface import Problem, resolve_manifest                      # noqa: E402
from adapters.dryrun import Adapter as DryRunAdapter                 # noqa: E402
from adapters.live import Adapter as LiveAdapter                     # noqa: E402
from adapters.second import Adapter as SecondAdapter                 # noqa: E402

BINDINGS = {"dryrun": DryRunAdapter, "live": LiveAdapter, "second": SecondAdapter}


def table(rows, header) -> None:
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def fail(problem: Problem) -> int:
    print("PROBLEM (application/problem+json):")
    print(json.dumps(problem.body, indent=2))
    return 2


def show(adapter, rows, refusal, replay) -> int:
    """Presentation, so the caller region below is calls and results only."""
    table([(e.kind, e.actor_subject, e.identity_hops, a.entry_id, a.job_digest[7:19],
            m.digest()[7:19], e.ceiling_micros, e.correlation["correlation_id"])
           for _, e, a, m in rows],
          ("door", "actor", "hops", "entry_id", "job_digest", "manifest", "ceiling", "correlation"))
    print(f"\none job: {len({a.job_digest for _, _, a, _ in rows})} job digest   "
          f"{len({m.digest() for _, _, _, m in rows})} resolved manifest   "
          f"{len({a.entry_id for _, _, a, _ in rows})} submissions   "
          f"{adapter.records} entries recorded   {adapter.work_started} units of work started")
    print(f"replay of {replay.entry_id}: duplicate_of={replay.duplicate_of}, "
          f"still {adapter.records} entries recorded")
    print("\na malformed task, at the same door:")
    print(json.dumps(refusal, indent=2) if refusal else "  ADMITTED - the refusal did not happen")
    print(f"\nbound by configuration: ADAPTER={os.environ.get('ADAPTER', 'dryrun')} "
          f"({adapter.execution_model})   read from the binding: {adapter.observed_marker}")
    return 0 if refusal else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method every harness uses.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = BINDINGS[os.environ.get("ADAPTER", "dryrun")]()      # configuration, not code
    rows = []
    try:
        for door in producers.DOORS:                               # human, event, schedule, external
            envelope = adapter.accept(adapter.render_message(door, producers.SUBJECT))
            rows.append((door, envelope, adapter.admit(envelope), resolve_manifest(envelope)))
        replay = adapter.admit(rows[0][1])                         # the same key again: free
    except Problem as problem:                                     # one refusal shape, branched on type
        return fail(problem)
    try:                                                           # one malformed task, one typed refusal
        adapter.accept(adapter.render_message(producers.DOORS[0],
                                              producers.malformed(producers.SUBJECT)))
        refusal = None
    except Problem as problem:
        refusal = problem.body
    return show(adapter, rows, refusal, replay)


if __name__ == "__main__":
    sys.exit(main())
