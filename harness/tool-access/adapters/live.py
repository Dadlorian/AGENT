#!/usr/bin/env python3
"""Live adapter for the tool endpoint on this host today.

Product names are allowed in this file and nowhere else. Today's adapter for
this row is the MCP endpoint: PASS.md B3 records the Model Context Protocol as
the standard and the MCP endpoint as the adapter today (F-b3-06), and PASS.md A6
records that same endpoint as "Live and authenticated, **zero tools
registered**" (F-a6-03).

That recorded state is the whole reason this adapter exists in this shape. A
bind against it is expected to succeed: the endpoint answers and authenticates.
The catalogue then comes back empty, health reports `empty` rather than green,
and the conformance run fails on the count instead of passing on the shape.
Nothing here works around that; the empty answer is the measurement.

Reached only through the environment variables in README.md. Standard library
only; the import is guarded so this module never breaks a dry run.

The JSON-RPC method names and the header below are this adapter's proposed
mapping of the four operations onto the protocol. The revision is declared per
request rather than agreed once at bind, which is what the versioning record on
file describes (X-cross-structure-061: "the version is declared per request
instead of negotiated once per session ... carried on Streamable HTTP as the
MCP-Protocol-Version header"). Both specification records on file are
search-only (X-cap-tool-access-001, X-cap-tool-access-002), so every method name
is overridable rather than asserted as fact.
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

METHOD_LIST = os.environ.get("TOOL_METHOD_LIST", "tools/list")          # proposed, unverified
METHOD_CALL = os.environ.get("TOOL_METHOD_CALL", "tools/call")          # proposed, unverified
METHOD_READ = os.environ.get("TOOL_METHOD_READ", "resources/read")      # proposed, unverified
METHOD_CANCEL = os.environ.get("TOOL_METHOD_CANCEL", "notifications/cancelled")   # proposed, unverified
REVISION_HEADER = os.environ.get("TOOL_REVISION_HEADER", "MCP-Protocol-Version")


class LiveEndpointAdapter(ToolAccessAdapter):
    entity = "tool endpoint on this host (MCP endpoint today)"
    server_marker = "catalogue:endpoint-on-this-host"
    catalogue_authority = "registered-here"
    call_locality = "co-located"
    catalogue_stability = "frozen"
    cancellation = "recorded"
    declared_gaps = (
        "recorded live and authenticated with zero tools registered, so a bind succeeds and the "
        "catalogue is empty until tools are registered into it (F-a6-03)",
        "cancellation is a notification; whether the endpoint stops the call is not verified from here",
    )

    def _env(self, name: str, default: str | None = None) -> str:
        value = os.environ.get(name, default)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the tool endpoint cannot be reached and nothing was dispatched",
                          retry_after_s=30)
        return value

    def _open(self, server_ref: str, ctx: CallContext) -> tuple:
        doc = self._rpc(METHOD_LIST, {}, ctx)
        tools = list(doc.get("tools", []))
        marker = str(doc.get("serverInfo", {}).get("name") or self.server_marker)
        return tools, marker, list(doc.get("resources", []))

    def _begin(self, binding: Binding, tool: ToolDescriptor, args: dict, ctx: CallContext) -> CallHandle:
        seed = hashlib.sha256((tool.name + repr(sorted(args.items()))).encode()).hexdigest()
        handle = CallHandle("call-" + seed[:16], tool.name, "in_flight", tool.effect, ctx.correlation_id)
        doc = self._rpc(METHOD_CALL, {"name": tool.name, "arguments": args}, ctx)
        handle.state = "done"
        # Two failure channels. `isError` is the tool's own failure inside an
        # otherwise successful envelope; the interface maps it onto the problem.
        handle.payload = {"content": doc.get("content", []), "is_error": bool(doc.get("isError")),
                          "error": doc.get("error", "")}
        return handle

    def _poll(self, handle: CallHandle) -> None:
        return                                   # one request, one answer

    def _cancel(self, handle: CallHandle) -> CancelAck:
        try:
            self._notify(METHOD_CANCEL, {"requestId": handle.call_id})
        except Problem:
            pass                                 # a cancel that could not be sent is still recorded
        return CancelAck(handle.call_id, "recorded", handle.effect == "mutating",
                         "the cancel was sent as a notification; the endpoint does not acknowledge a stop")

    def _read(self, binding: Binding, uri: str, ctx: CallContext) -> ResourceRead:
        doc = self._rpc(METHOD_READ, {"uri": uri}, ctx)
        return ResourceRead(uri, doc.get("contents", []))

    # --- transport ----------------------------------------------------------
    def _headers(self, ctx: CallContext | None = None) -> dict:
        headers = {"content-type": "application/json",
                   "authorization": "Bearer " + self._env("TOOL_ENDPOINT_TOKEN")}
        if ctx is not None:
            headers[REVISION_HEADER] = ctx.protocol_revision       # declared per request
            headers["x-correlation-id"] = ctx.correlation_id       # explicit, never trace parentage
            headers["x-run-id"] = ctx.run_id
        return headers

    def _post(self, body: dict, ctx: CallContext | None) -> dict | None:
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        url = self._env("TOOL_ENDPOINT_URL")
        req = URLLIB.Request(url, data=json.dumps(body).encode(), headers=self._headers(ctx))
        try:
            with URLLIB.urlopen(req, timeout=int(os.environ.get("TOOL_TIMEOUT_S", "60"))) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:400].decode("utf-8", "replace")
            if exc.code in (400, 426) and "version" in detail.lower():
                raise Problem("protocol-unsupported",
                              f"the endpoint refused revision {ctx.protocol_revision if ctx else '?'}: {detail}",
                              declared_revision=ctx.protocol_revision if ctx else None) from exc
            if exc.code in (401, 403):
                raise Problem("policy-denied", f"the endpoint refused the call: HTTP {exc.code} {detail}",
                              rule_id="endpoint-authorization",
                              enforcement_point="server-side") from exc
            raise Problem("adapter-unavailable", f"HTTP {exc.code}: {detail}", retry_after_s=30) from exc
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc

    def _rpc(self, method: str, params: dict, ctx: CallContext) -> dict:
        doc = self._post({"jsonrpc": "2.0", "id": ctx.correlation_id, "method": method,
                          "params": params}, ctx) or {}
        if "error" in doc:
            raise Problem("adapter-unavailable", f"the endpoint returned {doc['error']}", retry_after_s=30)
        return doc.get("result", {})

    def _notify(self, method: str, params: dict) -> None:
        self._post({"jsonrpc": "2.0", "method": method, "params": params}, None)


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveEndpointAdapter
