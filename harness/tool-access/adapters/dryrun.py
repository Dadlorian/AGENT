#!/usr/bin/env python3
"""Dry-run adapter: a catalogue this platform registers itself, served in process.

This is today's shape with nothing behind it: the tools are registered by the
same people who call them, so the tool list is known before the binding is
opened, the authorization is ours and the transport is ours. That is exactly the
assumption the second adapter exists to break (F-b1-04).

Deterministic: same bytes every run, so a gate can assert on them. The slow tool
takes three polls, which is what makes a cancel mid-flight observable without a
clock. TOOLS_UNREGISTERED=1 empties the catalogue, reproducing the state PASS.md
A6 records for the endpoint on this host (F-a6-03); DRYRUN_UNREACHABLE=1
exercises the failure path.
"""
from __future__ import annotations

import hashlib
import os

from interface import (Binding, CallContext, CallHandle, CancelAck, Problem, ResourceRead,
                       ToolAccessAdapter, ToolDescriptor)

# The catalogue this platform registers. Data, read at bind time, never compiled
# into a client: the conformance run discovers it and builds its arguments from
# these schemas rather than from constants of its own.
CATALOGUE = [
    {"name": "notes.read", "effect": "read_only", "idempotent": True,
     "description": "Read one note by path.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"path": {"type": "string", "minLength": 1}},
                      "required": ["path"]}},
    {"name": "notes.append", "effect": "mutating", "idempotent": False,
     "description": "Append one line to a note.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"path": {"type": "string", "minLength": 1},
                                     "line": {"type": "string", "minLength": 1}},
                      "required": ["path", "line"]}},
    {"name": "notes.scan", "effect": "read_only", "idempotent": True,
     "description": "Scan every note. Slow enough to be cancelled while it runs.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"root": {"type": "string", "minLength": 1},
                                     "depth": {"type": "integer", "minimum": 1}},
                      "required": ["root"]}},
    {"name": "notes.flaky", "effect": "mutating", "idempotent": False,
     "description": "Always reports its own failure inside a successful envelope.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"path": {"type": "string", "minLength": 1}},
                      "required": ["path"]}},
    {"name": "local.echo", "effect": "read_only", "idempotent": True,
     "description": "Registered here and nowhere else.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"text": {"type": "string"}}, "required": ["text"]}},
]
RESOURCES = {"note:///readme": "the resource a read returns; changing nothing, costing no call ceiling",
             "note:///changelog": "one line per change"}
POLLS_BEFORE_READY = 3          # what makes notes.scan cancellable mid-flight


class DryRunToolAdapter(ToolAccessAdapter):
    entity = "dry-run in-process tool catalogue"
    server_marker = "catalogue:registered-here"
    catalogue_authority = "registered-here"
    call_locality = "co-located"
    catalogue_stability = "frozen"
    cancellation = "stopped"
    declared_gaps = ("the tool list is ours, so discovery is never actually tested by this adapter alone",)

    def _open(self, server_ref: str, ctx: CallContext) -> tuple:
        if os.environ.get("DRYRUN_UNREACHABLE") == "1":
            raise Problem("adapter-unavailable",
                          "the dry-run catalogue was made unreachable by DRYRUN_UNREACHABLE=1",
                          retry_after_s=1)
        if os.environ.get("TOOLS_UNREGISTERED") == "1":
            # Live and authenticated, zero tools registered (F-a6-03).
            return [], self.server_marker, []
        return list(CATALOGUE), self.server_marker, sorted(RESOURCES)

    def _begin(self, binding: Binding, tool: ToolDescriptor, args: dict, ctx: CallContext) -> CallHandle:
        seed = hashlib.sha256((tool.name + repr(sorted(args.items()))).encode()).hexdigest()
        handle = CallHandle("call-" + seed[:16], tool.name, "in_flight", tool.effect, ctx.correlation_id)
        handle.payload = {"seed": seed}
        if tool.name != self.conformance_roles["slow"]:
            self._settle(handle, tool, args)          # fast tools settle on the first poll
        return handle

    def _poll(self, handle: CallHandle) -> None:
        if handle.state != "in_flight":
            return
        if handle.polls >= POLLS_BEFORE_READY:
            handle.state = "done"
            handle.payload = {"content": [{"type": "text",
                                           "text": f"scanned in {handle.polls} polls "
                                                   f"(seed {handle.payload['seed'][:8]})"}]}

    def _settle(self, handle: CallHandle, tool: ToolDescriptor, args: dict) -> None:
        seed = handle.payload["seed"]
        if tool.name == self.conformance_roles["in_band_failure"]:
            # The second failure channel: a success envelope carrying a failure.
            handle.state = "done"
            handle.payload = {"is_error": True, "error": f"upstream refused {args} (seed {seed[:8]})"}
            return
        handle.state = "done"
        handle.payload = {"content": [{"type": "text",
                                       "text": f"{tool.name}({args}) -> ok (seed {seed[:8]})"}]}

    def _cancel(self, handle: CallHandle) -> CancelAck:
        return CancelAck(handle.call_id, "stopped", handle.effect == "mutating",
                         "the call was stopped before it produced a result")

    def _read(self, binding: Binding, uri: str, ctx: CallContext) -> ResourceRead:
        if uri not in RESOURCES:
            raise Problem("tool-unknown", f"{uri!r} is not a resource this binding publishes", tool=uri)
        return ResourceRead(uri, [{"type": "text", "text": RESOURCES[uri]}])


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunToolAdapter
