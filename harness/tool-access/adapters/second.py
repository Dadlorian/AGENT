#!/usr/bin/env python3
"""Second adapter: a catalogue nobody here controls, reached over the same client.

It differs from today's adapter on the two axes cap-tool-access-implement names
for this pair: catalogue_authority (registered and frozen by us, versus authored
and versioned outside this platform) and call_locality (a co-located endpoint
whose authorization is ours, versus a remote server holding its own). Two more
follow from those and the swap report reads them too: the catalogue is re-read at
every bind and can change between them, and a cancel is *recorded* rather than
honoured, because a remote server cannot be made to stop.

Product names are allowed in this file. This adapter speaks the Model Context
Protocol to any conformant server; nothing about it is specific to one product,
which is the point of the swap candidate on file: "any MCP server" (F-b3-06).

Reachability. With SECOND_SERVER_URL set it POSTs JSON-RPC to that URL over
urllib, declaring the revision per request in the MCP-Protocol-Version header
(X-cross-structure-061). With it unset it runs the same state machine in
process, against a catalogue that is deliberately not ours: different tool
names, an extra required argument on one shared tool, and one tool that is
withdrawn between the first bind and the second. The shape and the swap
procedure are real either way; only the bytes are local.

The JSON-RPC method names below are this adapter's proposed mapping of the four
operations onto the protocol. Both records on file for the specification are
search-only (X-cap-tool-access-001, X-cap-tool-access-002), so they are
overridable by environment variable rather than asserted as fact.
"""
from __future__ import annotations

import hashlib
import json
import os

from interface import (Binding, CallContext, CallHandle, CancelAck, Problem, ResourceRead,
                       ToolAccessAdapter, ToolDescriptor)

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

METHOD_LIST = os.environ.get("SECOND_METHOD_LIST", "tools/list")        # proposed, unverified
METHOD_CALL = os.environ.get("SECOND_METHOD_CALL", "tools/call")        # proposed, unverified
METHOD_READ = os.environ.get("SECOND_METHOD_READ", "resources/read")    # proposed, unverified
POLLS_BEFORE_READY = 2                 # the remote scan settles on a different poll count

# The catalogue as it stands at the partner's first revision. The three declared
# names are the same, because a tool name is what survives a swap; everything
# else about them differs, including an argument this platform never asked for.
PARTNER_CATALOGUE = [
    {"name": "notes.read", "effect": "read_only", "idempotent": True,
     "description": "Fetch one note.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"path": {"type": "string", "minLength": 1}},
                      "required": ["path"]}},
    {"name": "notes.append", "effect": "mutating", "idempotent": False,
     "description": "Append a line. This server also requires an author.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"path": {"type": "string", "minLength": 1},
                                     "line": {"type": "string", "minLength": 1},
                                     "author": {"type": "string", "minLength": 1}},
                      "required": ["path", "line", "author"]}},
    {"name": "notes.scan", "effect": "read_only", "idempotent": True,
     "description": "Walk the corpus. Slow, and cannot be stopped once started.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"root": {"type": "string", "minLength": 1},
                                     "page_size": {"type": "integer", "minimum": 1}},
                      "required": ["root"]}},
    {"name": "notes.flaky", "effect": "mutating", "idempotent": False,
     "description": "Returns its own failure inside a successful envelope.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"path": {"type": "string", "minLength": 1}},
                      "required": ["path"]}},
    {"name": "partner.search", "effect": "read_only", "idempotent": True,
     "description": "Published by the partner, unknown to this platform.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"q": {"type": "string", "minLength": 1}}, "required": ["q"]}},
    {"name": "partner.ephemeral", "effect": "mutating", "idempotent": False,
     "description": "Withdrawn by the partner after the first bind.",
     "input_schema": {"type": "object", "additionalProperties": False,
                      "properties": {"id": {"type": "string"}}, "required": ["id"]}},
]
WITHDRAWN_AFTER_FIRST_BIND = "partner.ephemeral"
PARTNER_RESOURCES = {"note:///readme": "the partner's own read-only data, versioned by the partner"}


class PartnerServerAdapter(ToolAccessAdapter):
    entity = "conformant tool server published outside this platform"
    server_marker = "catalogue:published-elsewhere"
    catalogue_authority = "published-elsewhere"
    call_locality = "remote"
    catalogue_stability = "re-read-at-every-bind"
    cancellation = "recorded"
    declared_gaps = (
        "the tool list cannot be held still: it is authored and versioned by the partner",
        "a call cannot be promised a stop; a cancel is recorded and the effect may still be owed",
        "the credentials are the partner's own and are never ours",
    )

    def _url(self) -> str | None:
        return os.environ.get("SECOND_SERVER_URL")

    def _open(self, server_ref: str, ctx: CallContext) -> tuple:
        url = self._url()
        if url:
            doc = self._rpc(METHOD_LIST, {}, ctx)
            return list(doc.get("tools", [])), str(doc.get("serverInfo", {}).get("name",
                                                                                 self.server_marker)), \
                list(doc.get("resources", []))
        catalogue = [dict(t) for t in PARTNER_CATALOGUE
                     if not (self.binds >= 1 and t["name"] == WITHDRAWN_AFTER_FIRST_BIND)]
        return catalogue, self.server_marker, sorted(PARTNER_RESOURCES)

    def _begin(self, binding: Binding, tool: ToolDescriptor, args: dict, ctx: CallContext) -> CallHandle:
        seed = hashlib.sha256((tool.name + repr(sorted(args.items()))).encode()).hexdigest()
        handle = CallHandle("rpc-" + seed[:16], tool.name, "in_flight", tool.effect, ctx.correlation_id)
        handle.payload = {"seed": seed}
        if self._url():
            doc = self._rpc(METHOD_CALL, {"name": tool.name, "arguments": args}, ctx)
            handle.state = "done"
            handle.payload = {"content": doc.get("content", []), "is_error": bool(doc.get("isError")),
                              "error": doc.get("error", "")}
            return handle
        if tool.name != self.conformance_roles["slow"]:
            self._settle(handle, tool, args)
        return handle

    def _poll(self, handle: CallHandle) -> None:
        if handle.state != "in_flight":
            return
        if handle.polls >= POLLS_BEFORE_READY:
            handle.state = "done"
            handle.payload = {"content": [{"type": "text",
                                           "text": f"partner scan page {handle.polls} "
                                                   f"(seed {handle.payload['seed'][:8]})"}]}

    def _settle(self, handle: CallHandle, tool: ToolDescriptor, args: dict) -> None:
        seed = handle.payload["seed"]
        if tool.name == self.conformance_roles["in_band_failure"]:
            handle.state = "done"
            handle.payload = {"is_error": True, "error": f"partner refused {args} (seed {seed[:8]})"}
            return
        handle.state = "done"
        handle.payload = {"content": [{"type": "text",
                                       "text": f"partner {tool.name}({args}) -> ok (seed {seed[:8]})"}]}

    def _cancel(self, handle: CallHandle) -> CancelAck:
        # A cancel notification is sent; a stop is never claimed. The partner may
        # already have done the work, so a mutating call still owes its effect.
        return CancelAck(handle.call_id, "recorded", handle.effect == "mutating",
                         "the cancel was sent to a server that does not promise to stop; "
                         "the effect of a mutating call may still be owed")

    def _read(self, binding: Binding, uri: str, ctx: CallContext) -> ResourceRead:
        if self._url():
            doc = self._rpc(METHOD_READ, {"uri": uri}, ctx)
            return ResourceRead(uri, doc.get("contents", []))
        if uri not in PARTNER_RESOURCES:
            raise Problem("tool-unknown", f"{uri!r} is not a resource this binding publishes", tool=uri)
        return ResourceRead(uri, [{"type": "text", "text": PARTNER_RESOURCES[uri]}])

    # --- the networked form -------------------------------------------------
    def _rpc(self, method: str, params: dict, ctx: CallContext) -> dict:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        body = json.dumps({"jsonrpc": "2.0", "id": ctx.correlation_id, "method": method,
                           "params": params}).encode()
        headers = {"content-type": "application/json",
                   # Declared per request, never agreed once at bind (X-cross-structure-061).
                   "MCP-Protocol-Version": ctx.protocol_revision,
                   # Correlation rides on an explicit header, never on trace parentage (F-a7-02).
                   "x-correlation-id": ctx.correlation_id, "x-run-id": ctx.run_id}
        token = os.environ.get("SECOND_SERVER_TOKEN")
        if token:                       # the partner's own authorization, never ours
            headers["authorization"] = "Bearer " + token
        try:
            with URLLIB.urlopen(URLLIB.Request(self._url(), data=body, headers=headers),
                                timeout=int(os.environ.get("SECOND_TIMEOUT_S", "60"))) as resp:
                doc = json.load(resp)
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc
        if "error" in doc:
            raise Problem("adapter-unavailable", f"the server returned {doc['error']}", retry_after_s=30)
        return doc.get("result", {})


# The one name every adapter module exports: the entry point of this module.
Adapter = PartnerServerAdapter
