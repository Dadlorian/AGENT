#!/usr/bin/env python3
"""Second binding: the same chain, out of process, in front of every door.

The axis this pair differs on is placement, not language. The first binding
traverses the chain inside the process that issues the call, so anything not
built to enter the chain is never chained. This one puts the traversal in a
separate process the unit's traffic has to cross - the sidecar shape recorded in
the research as the way cross-cutting concerns are applied to a workload that
cannot be modified (X-cross-structure-020). Three consequences, and they are the
swap:

  locus_of_traversal                a process the traffic crosses, not a library
  processes_required_for_progress   two, and the second's absence is a refusal
  reach_over_unmodified_workloads   full: the workload is not changed at all

Reachability. With CHAIN_EDGE_URL set (see README) this adapter POSTs each
traversal to the admission endpoint the operator supplies whole; nothing about
that endpoint is invented here. With it unset the same program runs beside this
one as a real child process over a pipe (edge.py), which is what a dry run
exercises: the placement, the refusal of anything it did not issue, and the
refusal when it is unreachable are all real either way.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from interface import ChainContext, EnforcementChainAdapter, Problem, Unit

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGE = os.path.join(HERE, "edge.py")

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None


class OutOfProcessChainAdapter(EnforcementChainAdapter):
    entity = "out-of-process chain (an admitting process the traffic must cross)"
    locus = "in a separate process the unit's traffic must cross"
    processes_required = 2
    reach_over_unmodified = "full"
    refuses_unchained = True           # it admits nothing it did not issue a context for
    declared_gaps = (
        "an entirely in-process side effect never crosses its boundary and is invisible to it",
        "it adds a process to every unit's critical path and a hop to every call it wraps",
        "a slot needing state only the unit holds has to stay on the in-process point",
    )

    def __init__(self) -> None:
        super().__init__()
        self.url = os.environ.get("CHAIN_EDGE_URL", "")
        self.proc: subprocess.Popen | None = None
        self.down = os.environ.get("CHAIN_EDGE_DOWN") == "1"

    # --- the boundary the traffic crosses ----------------------------------
    def _ask(self, request: dict) -> dict:
        if self.down:
            raise Problem("adapter-unavailable",
                          "the admitting process is unreachable, so nothing was admitted; "
                          "an unreachable enforcement point is a refusal, never a bypass",
                          retry_after_s=1, enforced_by=self.entity)
        if self.url:                                        # the operator's own admission endpoint
            if URLLIB is None:
                raise Problem("adapter-unavailable", "no HTTP client is available in this runtime",
                              enforced_by=self.entity)
            req = URLLIB.Request(self.url, data=json.dumps(request).encode(),
                                 headers={"content-type": "application/json",
                                          "authorization": "Bearer " + os.environ.get("CHAIN_EDGE_TOKEN", "")})
            try:
                with URLLIB.urlopen(req, timeout=int(os.environ.get("CHAIN_EDGE_TIMEOUT_S", "30"))) as r:
                    return json.load(r)
            except Exception as exc:
                raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}",
                              retry_after_s=1, enforced_by=self.entity) from exc
        if self.proc is None:                               # the same program, beside this one
            self.proc = subprocess.Popen([sys.executable, EDGE], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, text=True, bufsize=1)
        try:
            self.proc.stdin.write(json.dumps(request) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
        except Exception as exc:
            raise Problem("adapter-unavailable", f"the admitting process stopped answering: {exc}",
                          retry_after_s=1, enforced_by=self.entity) from exc
        if not line:
            raise Problem("adapter-unavailable", "the admitting process closed the boundary",
                          retry_after_s=1, enforced_by=self.entity)
        return json.loads(line)

    def traverse(self, point: str, unit: Unit) -> list[dict]:
        return self._ask({"op": "traverse", "point": point, "unit": unit.dict()})["rows"]

    def seal(self, context: ChainContext) -> None:
        self._ask({"op": "seal", "context": context.dict()})

    def close(self) -> None:
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
            self.proc = None


Adapter = OutOfProcessChainAdapter
