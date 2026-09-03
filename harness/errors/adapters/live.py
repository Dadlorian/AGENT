#!/usr/bin/env python3
"""Live adapter: today's component for Errors.

PASS.md Part B3 records the tool for this element as *absent* (F-b3-13):
"RFC 9457 problem details | *absent*". No separate errors service runs on
this host. The in-process problem-details library in interface.py --
construct(), REGISTRY, retry_advice() -- is therefore the first adapter to
exist for this capability, not an incumbent being wrapped
(E-adapter-errors-absent). There is no endpoint, key or socket to dial, so
this binding is reached only through the two environment variables that
stand in for genuine deployment context: a real run's correlation id and run
id, supplied by whoever is running the platform, rather than the fixed
values a dry run uses. Standard library only; no import is guarded here
because none is needed -- there is nothing on the network to reach.
"""
from __future__ import annotations

import os

from interface import ErrorsAdapter, Problem, ProblemException, construct


class LiveProblemFactory(ErrorsAdapter):
    entity = "in-process problem factory (today's recorded component: PASS.md B3 records none; F-b3-13)"
    execution_model = "in-process"
    declared_marker = "live-problem-factory"
    declared_gaps = ("no separate errors service exists to reach; this binding differs from "
                      "dryrun only in taking correlation context from real environment "
                      "variables instead of a fixed test value",)

    def _require_live_context(self) -> str:
        run_id = os.environ.get("ERRORS_RUN_ID")
        corr = os.environ.get("ERRORS_CORRELATION_ID")
        if not run_id or not corr:
            self.responses_checked += 1
            raise ProblemException(construct(
                "adapter-unavailable",
                "ERRORS_RUN_ID and ERRORS_CORRELATION_ID are not set; live mode has no real "
                "deployment context to attribute a failure to and no component to fall back on",
                retry_after_s=5))
        return corr

    def raise_problem(self, suffix: str, detail: str, correlation_id: str | None = None,
                       **ext) -> ProblemException:
        corr = correlation_id or self._require_live_context()
        return super().raise_problem(suffix, detail, corr, **ext)

    def classify(self, incoming) -> Problem:
        self._require_live_context()
        self.responses_checked += 1
        if isinstance(incoming, ProblemException):
            return incoming.problem
        self.untyped += 1
        return construct("adapter-unavailable", f"{type(incoming).__name__}: {incoming}", retry_after_s=30)


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveProblemFactory
