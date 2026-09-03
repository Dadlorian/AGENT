#!/usr/bin/env python3
"""The unit under test: a small deterministic release reviewer, pinned by version.

It is here so the harness has something to score that is not the harness. It is
not part of the capability interface: nothing in interface.py, call.py or
conformance.py imports it except through an adapter's replay.

Two versions ship. 1.4.0 reads the change with the diff tool before answering;
1.4.1-rc drops that call and answers straight from the release description - the
regression cap-evaluation's definition of done names. Both answer the same words,
so a scorer that reads only the final answer cannot tell them apart.

An external effect is never executed here. The unit asks `serve(tool, args)` and
the adapter answers from the record; when the record does not hold that effect
the call raises UnrecordedEffect and the case refuses. There is no other path.
"""
from __future__ import annotations

UNIT_REF = "agent:release-reviewer"
BASELINE_VERSION = "1.4.0"
REGRESSED_VERSION = "1.4.1-rc"

# version -> does it call the diff tool before answering
CALLS_DIFF = {BASELINE_VERSION: True, REGRESSED_VERSION: False}


class UnrecordedEffect(Exception):
    """Raised by the serve callback when replay meets an effect the record does
    not hold. Executing it is not an option, so there is nothing to fall back to."""

    def __init__(self, tool: str, args: dict):
        super().__init__(f"no recorded result for {tool}({args})")
        self.tool, self.args = tool, args


def run(version: str, case_input: dict, serve) -> tuple[list[dict], dict]:
    """Return the ordered trajectory and, for the harness to assert on, exactly
    what this unit was given. Every step is recorded, not only the answer."""
    seen = dict(case_input)
    steps: list[dict] = [{"kind": "plan", "detail": "read the change, then answer"}]
    if case_input.get("diff_size", 0) > 0 and CALLS_DIFF.get(version, True):
        args = {"pr": case_input["pr"]}
        result = serve("diff", args)
        steps.append({"kind": "tool_call", "tool": "diff", "args": args})
        steps.append({"kind": "observation", "tool": "diff", "result": result})
    if case_input.get("lint"):
        args = {"release": case_input["release"]}
        result = serve("lint", args)
        steps.append({"kind": "tool_call", "tool": "lint", "args": args})
        steps.append({"kind": "observation", "tool": "lint", "result": result})
    answer = "hold the release" if case_input.get("risk") == "high" else "approve the release"
    steps.append({"kind": "answer", "detail": answer})
    return steps, seen
