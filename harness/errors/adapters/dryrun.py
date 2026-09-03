#!/usr/bin/env python3
"""Dry-run adapter: deterministic in-process problem factory, no network.

Same bytes every run. This adapter sees the raise site directly -- classify()
is handed the Python exception that was actually raised, which is the
execution model an in-process library has and an edge filter never does
(F-b1-04). Its own failure path (ERRORS_DRYRUN_FAIL=1) exercises the untyped
counter: an internal failure this raise site never typed still returns a
registered Problem, adapter-unavailable, rather than an untyped crash.
"""
from __future__ import annotations

import os

from interface import ErrorsAdapter, Problem, ProblemException, construct


class DryRunAdapter(ErrorsAdapter):
    entity = "dry-run in-process problem factory"
    execution_model = "in-process"
    declared_marker = "dryrun-problem-factory"

    def classify(self, incoming) -> Problem:
        """incoming: a ProblemException already typed at the raise site, or
        any other Exception this site never registered a type for."""
        self.responses_checked += 1
        if isinstance(incoming, ProblemException):
            return incoming.problem
        self.untyped += 1
        return construct("adapter-unavailable", f"{type(incoming).__name__}: {incoming}", retry_after_s=30)

    def demo_untyped_failure(self):
        """The failure path this binding exercises on demand (ERRORS_DRYRUN_FAIL=1)."""
        try:
            raise RuntimeError("an internal fault this raise site never mapped to a registry row")
        except RuntimeError as exc:
            return self.classify(exc)


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunAdapter
