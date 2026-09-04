#!/usr/bin/env python3
"""Authorization and transport mechanisms for a remote tool surface, verified
from a captured exchange over real sockets rather than from configuration,
documentation, or two halves of the same flow calling each other's Python
methods directly.

Answers tool-access-q2 (docs/maturity/closures.json). The closure names six
things a mature build must show are actually in force, each checked here by
reading a transcript built from genuine HTTP request/response cycles, never by
reading a setting:

  1. transport      the MCP calls travel over Streamable HTTP - one POST
                     endpoint that may upgrade to text/event-stream - never the
                     deprecated two-endpoint HTTP+SSE transport. (X-cross-
                     structure-061 already records the revision header on
                     Streamable HTTP for this harness; this file is the
                     transport claim itself, checked against a real socket.)
  2. PKCE            the authorization request carries code_challenge and
                     code_challenge_method=S256 (RFC 7636), and the token
                     request's code_verifier is checked against it, by a
                     process on the other end of a TCP connection, before a
                     code is redeemed.
  3. metadata        the client discovers the authorization server from a 401's
                     RFC 9728 protected-resource metadata, then discovers that
                     authorization server's endpoints from its RFC 8414
                     metadata - both fetched over HTTP, never read from a value
                     typed into configuration.
  4. resource        every authorization request AND every token request -
                     the initial exchange AND every refresh - carries an
                     RFC 8707 `resource` parameter naming the one target
                     server, and the issued token's audience is checked to
                     match only that server by that server's own process.
  5. audience proof  a captured token replayed against a second, independent
                     HTTP server is rejected by that server on the audience
                     check alone.
  6. output schema   a tool result is checked against the tool's declared
                     output schema before it is treated as structured data,
                     rather than parsed out of prose.

X-maturity-c-001 records that the 2025-06-18 MCP authorization revision makes
1-4 the governing mechanism. X-maturity-c-002 records the real production gap
this file's default breakage reproduces: a client (documented against a major
open-source MCP client) that sends `resource` on the initial token request but
drops it on refresh - the exact asymmetry the closure's check calls out
("including the resource indicator on refresh").

Real sockets, not in-process dicts. `LocalDeployment` starts one authorization
server and two protected-resource servers as three independent HTTP servers on
loopback TCP ports (`http.server`, one per port, each in its own thread).
`obtain_access_token` and `call_tool` are an ordinary HTTP client: they open
real connections with `urllib.request`, the same primitive `adapters/live.py`
uses, and parse real HTTP status codes, real `WWW-Authenticate` headers and
real JSON bodies out of what came back on the wire. `--check` runs that client
against this file's own local deployment; `--live-demo` points the actual
`adapters/live.py` adapter - unmodified, the same code call.py dispatches
through - at the same local deployment, sourcing its bearer token through
`obtain_access_token` instead of a token typed into an environment variable,
refresh included. Nothing here reaches a real remote host (dry-run only, no
product name outside a comment), but nothing here is in-process either: every
request in every transcript this file prints crossed a real TCP socket.
Python 3.11 standard library only.

    python3 harness/tool-access/adapters/auth_exchange.py --check
    AUTH_BREAK=refresh-omit-resource python3 harness/tool-access/adapters/auth_exchange.py --check
    python3 harness/tool-access/adapters/auth_exchange.py --live-demo
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

# So `--live-demo` can `import adapters.live` and `import interface` however
# this file itself was invoked (as a script, or imported as adapters.auth_exchange).
_TOOL_ACCESS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOL_ACCESS_DIR not in sys.path:
    sys.path.insert(0, _TOOL_ACCESS_DIR)

# --- the declared subset of JSON Schema this gate checks output against -----
# The same shape interface.py's check_arguments uses for input, aimed at a
# tool's declared output instead. cap-document-validation owns the real
# dialect (F-b3-09); this is a harness-local gate, not that validator.
_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool,
          "array": list, "object": dict}


def validate_output(schema: dict, data) -> list:
    """Returns the list of violations; empty means the result satisfies the
    tool's declared output schema. Never raises - the caller decides what a
    violation means, so both a strict gate and its deliberate bypass can share
    one checker."""
    problems = []
    if not isinstance(data, dict):
        return [f"result must be an object, got {type(data).__name__}"]
    props = schema.get("properties", {})
    for name in schema.get("required", []):
        if name not in data:
            problems.append(f"missing required output field {name!r}")
    for name, value in data.items():
        sub = props.get(name)
        if sub is None:
            if schema.get("additionalProperties") is False:
                problems.append(f"output field {name!r} is not declared by the tool's output schema")
            continue
        want = sub.get("type")
        if want in _TYPES and not isinstance(value, _TYPES[want]):
            problems.append(f"output field {name!r} must be a {want}, got {type(value).__name__}")
    return problems


# --- PKCE (RFC 7636) ---------------------------------------------------------
def pkce_pair() -> tuple:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


# --- a token: a plain signed-looking envelope, not a real JWT library -------
def mint_token(aud: str, sub: str, kind: str) -> str:
    payload = {"aud": aud, "sub": sub, "kind": kind, "jti": secrets.token_hex(8)}
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).rstrip(b"=").decode()
    return f"tok.{body}.sig-{hashlib.sha256((body + aud).encode()).hexdigest()[:12]}"


def token_audience(token: str) -> str:
    body = token.split(".")[1]
    padded = body + "=" * (-len(body) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))["aud"]


# =============================================================================
# SERVER SIDE - two roles, each served over a real HTTP socket. Business logic
# only; nothing here touches sockets or headers directly, so it is exercised
# identically whether the request came from this file's own client below or
# from adapters/live.py.
# =============================================================================
class AuthorizationServer:
    """RFC 8414 metadata, PKCE, RFC 8707 resource binding on every grant."""

    def __init__(self, issuer: str):
        self.issuer = issuer
        self.metadata = {
            "issuer": issuer,
            "authorization_endpoint": issuer + "/authorize",
            "token_endpoint": issuer + "/token",
            "code_challenge_methods_supported": ["S256"],
        }
        self._codes: dict = {}          # code -> {resource, challenge, client_id}
        self._refresh: dict = {}        # refresh_token -> {resource, client_id}

    def handle_authorize(self, params: dict) -> tuple:
        """-> (status, body). A real endpoint would 302 a browser back to the
        client's redirect_uri with the code; answering the code directly here
        skips the browser step this dry run has no way to drive, without
        touching what is actually being verified - every parameter below was
        read off the real HTTP GET request, not passed as a Python argument."""
        resource = params.get("resource") or None
        code_challenge = params.get("code_challenge") or None
        code_challenge_method = params.get("code_challenge_method") or None
        client_id = params.get("client_id", "mcp-client")
        if not resource:
            return 400, {"error": "invalid_request", "error_description": "resource is required (RFC 8707)"}
        if code_challenge_method != "S256" or not code_challenge:
            return 400, {"error": "invalid_request", "error_description": "PKCE S256 is required"}
        code = "code-" + secrets.token_hex(8)
        self._codes[code] = {"resource": resource, "challenge": code_challenge, "client_id": client_id}
        return 200, {"code": code}

    def handle_token(self, params: dict) -> tuple:
        grant_type = params.get("grant_type")
        resource = params.get("resource") or None
        if grant_type == "authorization_code":
            entry = self._codes.pop(params.get("code"), None)
            if entry is None:
                return 400, {"error": "invalid_grant", "error_description": "unknown code"}
            if not resource:
                return 400, {"error": "invalid_request", "error_description": "resource is required (RFC 8707)"}
            if resource != entry["resource"]:
                return 400, {"error": "invalid_target", "error_description": "resource does not match the code"}
            verifier_hash = base64.urlsafe_b64encode(
                hashlib.sha256((params.get("code_verifier") or "").encode()).digest()).rstrip(b"=").decode()
            if verifier_hash != entry["challenge"]:
                return 400, {"error": "invalid_grant",
                             "error_description": "code_verifier does not match the authorization "
                                                  "request's code_challenge"}
            rt = "refresh-" + secrets.token_hex(8)
            self._refresh[rt] = {"resource": resource, "client_id": entry["client_id"]}
            return 200, {"access_token": mint_token(resource, entry["client_id"], "access"),
                        "refresh_token": rt, "token_type": "Bearer", "expires_in": 60}
        if grant_type == "refresh_token":
            # RFC 8707 sec. 2 requires `resource` on every token request, refresh
            # included. Modeled tolerant of a client that omits it (the real gap
            # X-maturity-c-002 records) so the omission surfaces as a transcript
            # finding the checks below catch, rather than a request this server
            # simply refuses to answer - the point being made is that the wire
            # exchange itself is what a verifier must read.
            entry = self._refresh.get(params.get("refresh_token"))
            bound_resource = entry["resource"] if entry else resource
            client_id = entry["client_id"] if entry else "mcp-client"
            if not bound_resource:
                return 400, {"error": "invalid_target", "error_description": "no resource bound to this "
                                                                             "refresh token and none supplied"}
            return 200, {"access_token": mint_token(bound_resource, client_id, "access"),
                        "refresh_token": params.get("refresh_token", ""), "token_type": "Bearer",
                        "expires_in": 60, "resource_supplied_on_refresh": bool(resource)}
        return 400, {"error": "unsupported_grant_type", "error_description": repr(grant_type)}


class ProtectedResource:
    """RFC 9728 metadata, an audience check on every call, one tool whose
    result is gated against its own declared output schema."""

    def __init__(self, resource_id: str, authorization_server_issuer: str):
        self.resource_id = resource_id
        self.prm_url = resource_id + "/.well-known/oauth-protected-resource"
        self.metadata = {"resource": resource_id, "authorization_servers": [authorization_server_issuer]}
        self._output_schema = {"type": "object", "required": ["path", "content"],
                               "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}

    def tool_descriptor(self) -> dict:
        """This harness's own tool-descriptor shape (interface.py's
        ToolDescriptor.from_dict): a real MCP `tools/list` entry uses
        camelCase `inputSchema`/`outputSchema`; this repository's proposed
        mapping is snake_case, unverified against a real server (README.md)."""
        return {"name": "notes.read", "effect": "read_only", "idempotent": True,
                "description": "Read one note.", "input_schema": {"type": "object", "properties": {}},
                "output_schema": self._output_schema}

    def handle_tool_call(self, name: str, bad_output: bool, skip_gate: bool) -> tuple:
        """-> (status, body-without-jsonrpc-envelope). Callers wrap this in a
        JSON-RPC result or error object."""
        if name != "notes.read":
            return 404, {"error": {"code": -32602, "message": f"unknown tool {name!r}"}}
        structured = {"path": "notes/decisions.md"} if bad_output \
            else {"path": "notes/decisions.md", "content": "..."}
        if not skip_gate:
            violations = validate_output(self._output_schema, structured)
            if violations:
                return 502, {"error": {"code": -32003, "message": "output-schema-rejected", "data": violations}}
        return 200, {"result": {"content": [{"type": "text", "text": structured.get("content", "")}],
                                "structuredContent": structured, "isError": False}}


# =============================================================================
# WIRE - real HTTP servers (loopback sockets) and a real HTTP client.
# =============================================================================
class _JSONHandler(http.server.BaseHTTPRequestHandler):
    def _json(self, status: int, body: dict, headers: dict | None = None) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def log_message(self, fmt, *args) -> None:      # silence: this is a test double, not a log source
        pass


class _ASHandler(_JSONHandler):
    def do_GET(self) -> None:
        as_ = self.server.as_
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/.well-known/oauth-authorization-server":
            self._json(200, as_.metadata)
        elif parsed.path == "/authorize":
            params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
            status, body = as_.handle_authorize(params)
            self._json(status, body)
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        as_ = self.server.as_
        if self.path == "/token":
            raw = self._read_body()
            params = dict(urllib.parse.parse_qsl(raw.decode())) if raw else {}
            status, body = as_.handle_token(params)
            self._json(status, body)
        else:
            self._json(404, {"error": "not_found"})


class _ResourceHandler(_JSONHandler):
    def do_GET(self) -> None:
        res = self.server.resource
        if self.path == "/.well-known/oauth-protected-resource":
            self._json(200, res.metadata)
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        res = self.server.resource
        if self.path != "/mcp":
            self._json(404, {"error": "not_found"})
            return
        raw = self._read_body()
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {}
        rpc_id = body.get("id", 1)
        auth = self.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            # RFC 9728: a 401 carries a pointer to this resource's own metadata.
            self._json(401, {"jsonrpc": "2.0", "id": rpc_id,
                             "error": {"code": -32001, "message": "unauthorized"}},
                      headers={"WWW-Authenticate": f'Bearer resource_metadata="{res.prm_url}"'})
            return
        try:
            aud = token_audience(auth[len("Bearer "):])
        except Exception:
            aud = ""
        if aud != res.resource_id:
            self._json(403, {"jsonrpc": "2.0", "id": rpc_id,
                             "error": {"code": -32002,
                                       "message": f"audience {aud!r} does not name this "
                                                 f"resource {res.resource_id!r}"}})
            return
        method = body.get("method")
        if method == "tools/list":
            self._json(200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": [res.tool_descriptor()]}})
            return
        if method == "tools/call":
            params = body.get("params", {})
            status, result_body = res.handle_tool_call(
                params.get("name", ""),
                self.headers.get("X-Test-Bad-Output") == "1",
                self.headers.get("X-Test-Skip-Gate") == "1")
            self._json(status, {"jsonrpc": "2.0", "id": rpc_id, **result_body})
            return
        self._json(400, {"jsonrpc": "2.0", "id": rpc_id,
                         "error": {"code": -32601, "message": f"method not found: {method!r}"}})


def _start(handler_cls, **attrs) -> http.server.HTTPServer:
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler_cls)
    for k, v in attrs.items():
        setattr(httpd, k, v)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


class LocalDeployment:
    """One authorization server and two protected-resource servers, each a
    real HTTP server bound to its own loopback port. Nothing here is reached
    by a direct Python call from the client below - every exchange crosses a
    real socket."""

    def __init__(self):
        self.as_httpd = _start(_ASHandler)
        self.issuer = f"http://127.0.0.1:{self.as_httpd.server_port}"
        self.as_httpd.as_ = AuthorizationServer(self.issuer)

        self.r1_httpd = _start(_ResourceHandler)
        self.resource1 = ProtectedResource(f"http://127.0.0.1:{self.r1_httpd.server_port}", self.issuer)
        self.r1_httpd.resource = self.resource1

        self.r2_httpd = _start(_ResourceHandler)
        self.resource2 = ProtectedResource(f"http://127.0.0.1:{self.r2_httpd.server_port}", self.issuer)
        self.r2_httpd.resource = self.resource2

    def stop(self) -> None:
        for httpd in (self.as_httpd, self.r1_httpd, self.r2_httpd):
            httpd.shutdown()
            httpd.server_close()


# --- the client: urllib.request, the same primitive adapters/live.py uses ---
def _fetch(method: str, url: str, headers: dict | None = None, data: bytes | None = None) -> tuple:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return resp.status, resp.headers, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {}
        return exc.code, exc.headers, body


def _resource_metadata_url(www_authenticate: str) -> str:
    marker = 'resource_metadata="'
    i = www_authenticate.find(marker)
    if i == -1:
        return ""
    j = www_authenticate.find('"', i + len(marker))
    return www_authenticate[i + len(marker):j] if j != -1 else ""


def obtain_access_token(resource_base_url: str, break_mode: str = "", transcript: list | None = None) -> dict:
    """The OAuth 2.1 + PKCE + RFC 8707 client, over real HTTP: probes the
    resource, follows its RFC 9728 pointer, discovers the authorization
    server's RFC 8414 metadata, redeems a PKCE-bound authorization code with
    the resource indicator, and refreshes with the resource indicator too.
    Returns the token response body (`access_token` present on success).

    This is the one function `adapters/live.py` calls to source its bearer
    token, so the live adapter and this file's own `--check` run the same
    client code, over the same wire, against whatever `resource_base_url`
    answers - this file's own `LocalDeployment` for `--check` and
    `--live-demo`, or (unmodified) a real remote deployment if one existed."""
    t = transcript if transcript is not None else []
    mcp_url = resource_base_url.rstrip("/") + "/mcp"

    # 1. probe with no Authorization -> 401 carrying the RFC 9728 pointer
    status, headers, _ = _fetch("POST", mcp_url,
                                headers={"Content-Type": "application/json",
                                        "Accept": "application/json, text/event-stream"},
                                data=json.dumps({"jsonrpc": "2.0", "id": 0, "method": "tools/list"}).encode())
    www_authenticate = headers.get("WWW-Authenticate", "") if status == 401 else ""
    t.append({"step": "unauthenticated_probe", "status": status, "www_authenticate": www_authenticate})
    if status != 401:
        return {"error": f"expected 401 from an unauthenticated probe, got {status}"}
    prm_url = _resource_metadata_url(www_authenticate)
    if not prm_url:
        return {"error": "401 carried no resource_metadata pointer (RFC 9728)"}

    # 2. RFC 9728 protected-resource metadata, fetched from the pointer above
    _, _, prm = _fetch("GET", prm_url)
    t.append({"step": "protected_resource_metadata", "endpoint": prm_url, "body": prm})
    issuer = (prm.get("authorization_servers") or [None])[0]
    if not issuer:
        return {"error": "protected-resource metadata named no authorization server"}

    # 3. RFC 8414 authorization-server metadata, fetched from the issuer above
    asm_url = issuer.rstrip("/") + "/.well-known/oauth-authorization-server"
    _, _, asm = _fetch("GET", asm_url)
    t.append({"step": "authorization_server_metadata", "endpoint": asm_url, "body": asm})

    # 4. PKCE (RFC 7636)
    verifier, challenge = pkce_pair()
    challenge_param = None if break_mode == "no-pkce" else challenge
    method_param = None if break_mode == "no-pkce" else "S256"

    # 5. authorization request, resource-bound (RFC 8707), against the endpoint
    #    RFC 8414 metadata just named - never a value typed into configuration
    resource = prm.get("resource", resource_base_url)
    authz_resource = None if break_mode == "authz-omit-resource" else resource
    authz_params = {"client_id": "mcp-client", "response_type": "code"}
    if authz_resource:
        authz_params["resource"] = authz_resource
    if challenge_param:
        authz_params["code_challenge"] = challenge_param
    if method_param:
        authz_params["code_challenge_method"] = method_param
    authz_status, _, authz_body = _fetch(
        "GET", asm["authorization_endpoint"] + "?" + urllib.parse.urlencode(authz_params))
    t.append({"step": "authorization_request", "endpoint": asm["authorization_endpoint"],
             "params": {"client_id": "mcp-client", "response_type": "code", "resource": authz_resource,
                       "code_challenge": challenge_param, "code_challenge_method": method_param}})
    t.append({"step": "authorization_response", **authz_body})
    if authz_status != 200 or "code" not in authz_body:
        return {"error": authz_body.get("error_description", authz_body.get("error", "authorization failed"))}

    # 6. initial token request, resource-bound
    token_endpoint = asm["token_endpoint"]
    initial_form = {"grant_type": "authorization_code", "resource": resource,
                    "code": authz_body["code"], "code_verifier": verifier, "client_id": "mcp-client"}
    _, _, tok_body = _fetch("POST", token_endpoint,
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                            data=urllib.parse.urlencode(initial_form).encode())
    t.append({"step": "token_request[authorization_code]", "endpoint": token_endpoint,
             "params": {"grant_type": "authorization_code", "resource": resource,
                       "code": authz_body["code"], "code_verifier": "***"}})
    t.append({"step": "token_response", **tok_body})
    if "access_token" not in tok_body:
        return tok_body

    # 7. refresh, resource-bound - the gap X-maturity-c-002 records when omitted
    refresh_resource = None if break_mode == "refresh-omit-resource" else resource
    refresh_form = {"grant_type": "refresh_token", "refresh_token": tok_body.get("refresh_token", "")}
    if refresh_resource:
        refresh_form["resource"] = refresh_resource
    _, _, ref_body = _fetch("POST", token_endpoint,
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                            data=urllib.parse.urlencode(refresh_form).encode())
    t.append({"step": "token_request[refresh_token]", "endpoint": token_endpoint,
             "params": {"grant_type": "refresh_token", "resource": refresh_resource, "refresh_token": "***"}})
    t.append({"step": "token_response", **ref_body})
    return ref_body


def call_tool(resource_base_url: str, access_token: str, name: str, transcript: list,
              *, bad_output: bool = False, skip_gate: bool = False) -> dict:
    """One real Streamable HTTP call: POST the single `/mcp` endpoint with
    `Accept: application/json, text/event-stream`, never a `GET /sse` plus a
    second `POST /messages`."""
    mcp_url = resource_base_url.rstrip("/") + "/mcp"
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
              "Authorization": f"Bearer {access_token}"}
    if bad_output:
        headers["X-Test-Bad-Output"] = "1"
    if skip_gate:
        headers["X-Test-Skip-Gate"] = "1"
    status, _, body = _fetch("POST", mcp_url, headers=headers,
                             data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                              "params": {"name": name, "arguments": {}}}).encode())
    transcript.append({"step": "tool_call", "resource": resource_base_url, "endpoint": mcp_url,
                       "http_method": "POST", "accept": headers["Accept"], "tool": name})
    entry = {"step": "tool_call_response", "status": status}
    if status == 200 and "result" in body:
        entry["result"] = body["result"].get("structuredContent", {})
    elif "error" in body:
        err = body["error"]
        if status == 502:
            entry["gate"] = "output-schema-rejected"
            entry["violations"] = err.get("data", [])
        else:
            entry["error"] = err.get("message", "")
    transcript.append(entry)
    return entry


# --- the self-check: this file's own local deployment, over real sockets ----
def run_exchange(break_mode: str = "") -> dict:
    """Starts a real local deployment, runs the client through it once, and
    returns the transcript plus the pieces `verify` reads back out of it."""
    deployment = LocalDeployment()
    try:
        transcript: list = []
        token = obtain_access_token(deployment.resource1.resource_id, break_mode, transcript)
        gate_on = break_mode != "skip-output-validation"
        bad_output = break_mode in ("bad-output-schema", "skip-output-validation")
        call = call_tool(deployment.resource1.resource_id, token.get("access_token", ""), "notes.read",
                         transcript, bad_output=bad_output, skip_gate=not gate_on)
        # 9. replay the same access token against a second, unrelated server
        replay = call_tool(deployment.resource2.resource_id, token.get("access_token", ""), "notes.read",
                           transcript, bad_output=bad_output, skip_gate=not gate_on)
        initial_token = next((e for e in transcript if e["step"] == "token_response"), {})
        return {"transcript": transcript, "issuer": deployment.issuer,
               "resource1": deployment.resource1.resource_id, "resource2": deployment.resource2.resource_id,
               "authz": next((e for e in transcript if e["step"] == "authorization_response"), {}),
               "initial_token": initial_token, "refreshed_token": token, "call": call, "replay": replay}
    finally:
        deployment.stop()


# --- verification: every check reads the transcript, never the config above -
def verify(run: dict) -> dict:
    t = run["transcript"]
    by_step = {}
    for entry in t:
        by_step.setdefault(entry["step"], []).append(entry)
    checks = {}

    probe = by_step.get("unauthenticated_probe", [{}])[0]
    checks["401_carries_protected_resource_metadata_pointer"] = (
        probe.get("status") == 401 and "resource_metadata=" in probe.get("www_authenticate", ""))

    checks["protected_resource_metadata_discovered"] = "protected_resource_metadata" in by_step
    checks["authorization_server_metadata_discovered"] = "authorization_server_metadata" in by_step

    authz_reqs = by_step.get("authorization_request", [])
    checks["pkce_s256_on_authorization_request"] = bool(
        authz_reqs and authz_reqs[0]["params"].get("code_challenge")
        and authz_reqs[0]["params"].get("code_challenge_method") == "S256")
    checks["resource_on_authorization_request"] = bool(
        authz_reqs and authz_reqs[0]["params"].get("resource") == run["resource1"])

    token_reqs = {e["step"]: e for e in t if e["step"].startswith("token_request")}
    initial = token_reqs.get("token_request[authorization_code]", {})
    refresh = token_reqs.get("token_request[refresh_token]", {})
    checks["resource_on_initial_token_request"] = initial.get("params", {}).get("resource") == run["resource1"]
    checks["resource_on_refresh_token_request"] = refresh.get("params", {}).get("resource") == run["resource1"]

    checks["pkce_verifier_checked_before_code_redeemed"] = "access_token" in run["initial_token"]
    checks["refresh_did_not_fail_open_on_missing_resource_alone"] = "access_token" in run["refreshed_token"]

    issued_aud_ok = False
    if "access_token" in run["refreshed_token"]:
        issued_aud_ok = token_audience(run["refreshed_token"]["access_token"]) == run["resource1"]
    checks["issued_token_audience_matches_target_server_only"] = issued_aud_ok

    tool_calls = by_step.get("tool_call", [])
    checks["transport_is_streamable_single_endpoint"] = bool(
        tool_calls and all(c["http_method"] == "POST" and c["endpoint"].endswith("/mcp")
                           and "text/event-stream" in c["accept"] for c in tool_calls)
        and len({c["endpoint"] for c in tool_calls}) == len({c["resource"] for c in tool_calls}))

    call_resp = run["call"]
    checks["target_server_accepted_correctly_audienced_token"] = call_resp.get("status") == 200
    checks["tool_result_validated_against_output_schema"] = (
        "gate" not in call_resp) and ("result" in call_resp) and not validate_output(
        {"type": "object", "required": ["path", "content"],
         "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}, call_resp.get("result", {}))

    replay_resp = run["replay"]
    checks["replayed_token_rejected_by_second_server_on_audience"] = replay_resp.get("status") == 403

    return checks


# --- live-demo: adapters/live.py, unmodified, sourcing its token from here --
def live_demo() -> int:
    """Points the actual `adapters/live.py` adapter - the same networked code
    `call.py` dispatches every live call through, `_headers`, `_post`, `_rpc`
    and all - at a real local MCP endpoint (`LocalDeployment.resource1`), with
    `TOOL_OAUTH_DISCOVER=1` so its bearer token comes from `obtain_access_token`
    (probe, RFC 9728 + RFC 8414 discovery, PKCE, a resource-bound refresh)
    instead of a static `TOOL_ENDPOINT_TOKEN`. Then replays the same token
    against the second server directly, over the wire, to prove the audience
    check holds outside this file's own client too. Prints a summary and
    returns 0 only if every one of those held."""
    deployment = LocalDeployment()
    old_env = {k: os.environ.get(k) for k in
              ("TOOL_ENDPOINT_URL", "TOOL_ENDPOINT_TOKEN", "TOOL_OAUTH_DISCOVER", "TOOL_OAUTH_RESOURCE")}
    try:
        os.environ["TOOL_ENDPOINT_URL"] = deployment.resource1.resource_id + "/mcp"
        os.environ["TOOL_OAUTH_DISCOVER"] = "1"
        os.environ.pop("TOOL_ENDPOINT_TOKEN", None)
        os.environ.pop("TOOL_OAUTH_RESOURCE", None)

        from adapters.live import LiveEndpointAdapter          # noqa: E402 -- deliberately lazy, see module docstring
        from interface import CallContext                      # noqa: E402

        adapter = LiveEndpointAdapter()
        ctx = CallContext(correlation_id="cor-livedemo", run_id="run-livedemo", actor="user:corey",
                          idempotency_key="idem-livedemo")
        binding = adapter.bind_server(deployment.resource1.resource_id, ["notes.read"], ctx)
        names = binding.names()
        if "notes.read" not in names:
            print(f"live-demo FAIL: tool not listed by the live adapter, catalogue={names}")
            return 1
        result = adapter.call_tool(binding, "notes.read", {}, ctx)
        if not result.ok:
            print(f"live-demo FAIL: the live adapter's call reported a failure: {result.problem}")
            return 1
        token = getattr(adapter, "_oauth_token_cache", None)
        if not token:
            print("live-demo FAIL: the live adapter did not cache a token from obtain_access_token")
            return 1
        replay = call_tool(deployment.resource2.resource_id, token, "notes.read", [])
        if replay.get("status") != 403:
            print(f"live-demo FAIL: the live adapter's token was not rejected by the second server: {replay}")
            return 1
        print("live-demo PASS: adapters/live.py listed and called notes.read over a real HTTP socket "
             "(http.server, loopback) with a bearer token sourced entirely from obtain_access_token - "
             "the 401 probe, RFC 9728 and RFC 8414 discovery, PKCE, the resource-bound authorization "
             "code grant and the resource-bound refresh all included - and that same token, replayed "
             f"by this file's own client against a second, independent server ({deployment.resource2.resource_id}), "
             "was rejected on the audience check alone.")
        return 0
    finally:
        deployment.stop()
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="run the exchange and print every check")
    ap.add_argument("--report", help="write the transcript and checks to this JSON file")
    ap.add_argument("--live-demo", action="store_true",
                    help="point adapters/live.py at a real local endpoint, token sourced via OAuth")
    args = ap.parse_args(argv)

    if args.live_demo:
        return live_demo()

    break_mode = os.environ.get("AUTH_BREAK", "")
    run = run_exchange(break_mode)
    checks = verify(run)

    if args.report:
        with open(args.report, "w") as fh:
            json.dump({"break_mode": break_mode, "transcript": run["transcript"], "checks": checks}, fh, indent=2)

    passed = sum(checks.values())
    total = len(checks)
    if args.check or not args.report:
        width = max(len(k) for k in checks)
        for name, ok in checks.items():
            print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
        print(f"\nAUTH_EXCHANGE break_mode={break_mode or 'none'} checks_passed={passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
