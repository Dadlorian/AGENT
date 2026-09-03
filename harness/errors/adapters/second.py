#!/usr/bin/env python3
"""Second adapter: an edge component that answers on behalf of a service.

Where the in-process adapters classify the Python exception they themselves
raised, this one never runs inside the failing process at all: it sees only
the wire response -- a status, a media type and a body -- the way a gateway
sitting in front of a service would (cap-errors-implement adapters,
E-swap-candidate-gateway-problem-filter). That is a genuinely different
execution model (F-b1-04): one more process must run for a failure to reach
this adapter, and rule_id, causes and a raise-site detail are unavailable
unless the upstream body already carried them. This file does not invent
them; it reshapes what the wire gave it, or falls through to
adapter-unavailable and counts the failure as untyped -- never forwards an
unrecognised body unchanged (cap-errors-implement rule 2).

No live route exists to reach here (PASS.md B3: *absent*); classify() is
exercised against the wire dict a caller or the conformance run hands it.
"""
from __future__ import annotations

import json

from interface import (MEDIA_TYPE, PROBLEM_BASE, REGISTRY, ErrorsAdapter, Problem,
                        construct, problem_from_body)


class EdgeFilterAdapter(ErrorsAdapter):
    entity = "edge component that answers on behalf of a service"
    execution_model = "edge-filter"
    declared_marker = "edge-filter-normalized"
    declared_gaps = ("rule_id, causes and the raise-site detail are unavailable unless the "
                      "upstream response already carried them; this adapter reshapes what "
                      "the wire gave it, it never invents context",)

    def classify(self, wire: dict) -> Problem:
        """wire: {"status": int, "media_type": str, "body": dict | str}."""
        self.responses_checked += 1
        media_type = wire.get("media_type", "")
        body = wire.get("body")
        if media_type != MEDIA_TYPE or not isinstance(body, dict):
            self.untyped += 1
            self.wrong_media_type += 1
            raw = body if isinstance(body, str) else json.dumps(body)
            return construct(
                "adapter-unavailable",
                f"upstream answered {wire.get('status')} {media_type or '(no media type)'}: {raw[:200]}",
                retry_after_s=30)
        suffix = str(body.get("type", ""))[len(PROBLEM_BASE):]
        if not body.get("type", "").startswith(PROBLEM_BASE) or suffix not in REGISTRY:
            self.unregistered_types += 1
            self.untyped += 1
            return construct("adapter-unavailable",
                              f"upstream problem type {body.get('type')!r} is not in the closed registry",
                              retry_after_s=30)
        # Already well-formed and registered: reshape only, invent nothing.
        return problem_from_body(body)


# The one name every adapter module exports: the entry point of this module.
Adapter = EdgeFilterAdapter
