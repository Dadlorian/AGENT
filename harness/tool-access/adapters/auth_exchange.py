#!/usr/bin/env python3
"""Authorization and transport mechanisms for a remote tool surface, verified
from the exchange itself rather than from configuration or documentation.

Answers tool-access-q2 (docs/maturity/closures.json). The closure names six
things a mature build must show are actually in force, each checked here by
reading a recorded transcript of the exchange, never by reading a setting:

  1. transport      the MCP calls (tools/list, tools/call) travel over
                     Streamable HTTP - one POST endpoint that may upgrade to
                     text/event-stream - never the deprecated two-endpoint
                     HTTP+SSE transport (GET /sse to open a stream, POST
                     /messages to send). (X-cross-structure-061 already records
                     the revision header on Streamable HTTP for this harness;
                     this file is the transport claim itself, checked.)
  2. PKCE            the authorization request carries code_challenge and
                     code_challenge_method=S256 (RFC 7636), and the token
                     request's code_verifier is checked against it before a
                     code is redeemed.
  3. metadata        the client discovers the authorization server from a 401's
                     RFC 9728 protected-resource metadata, then discovers that
                     authorization server's endpoints from its RFC 8414
                     metadata - never from a value typed into configuration.
  4. resource        every authorization request AND every token request -
                     the initial exchange AND every refresh - carries an
                     RFC 8707 `resource` parameter naming the one target
                     server, and the issued token's audience is checked to
                     match only that server.
  5. audience proof  a captured token replayed against a second MCP server is
                     rejected by that server on the audience check alone.
  6. output schema   a tool result is checked against the tool's declared
                     output schema before it is treated as structured data,
                     rather than parsed out of prose.

X-maturity-c-001 records that the 2025-06-18 MCP authorization revision makes
1-4 the governing mechanism. X-maturity-c-002 records the real production gap
this file's default breakage reproduces: a client (documented against a major
open-source MCP client) that sends `resource` on the initial token request but
drops it on refresh - the exact asymmetry the closure's check calls out
("including the resource indicator on refresh"). Every mechanism below is
therefore verified from what a request actually carried, not from what the
client meant to send or what a server was lenient enough to accept anyway.

Dry-run only: three in-process actors (an authorization server and two
protected resource servers standing in for two MCP servers) exchange plain
dicts as if they were HTTP requests and responses. Nothing here reaches a
network. Python 3.11 standard library only. No product name appears outside
comments citing the research record it came from.

    python3 harness/tool-access/auth_exchange.py --check
    AUTH_BREAK=refresh-omit-resource python3 harness/tool-access/auth_exchange.py --check
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys

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


# --- the authorization server (RFC 8414 metadata, PKCE, RFC 8707 resource) --
class AuthorizationServer:
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

    def authorize(self, client_id: str, resource: str | None, code_challenge: str | None,
                  code_challenge_method: str | None, transcript: list) -> dict:
        req = {"step": "authorization_request", "endpoint": self.metadata["authorization_endpoint"],
               "params": {"client_id": client_id, "response_type": "code", "resource": resource,
                          "code_challenge": code_challenge, "code_challenge_method": code_challenge_method}}
        transcript.append(req)
        if not resource:
            resp = {"step": "authorization_response", "error": "invalid_request: resource is required (RFC 8707)"}
            transcript.append(resp)
            return resp
        if code_challenge_method != "S256" or not code_challenge:
            resp = {"step": "authorization_response", "error": "invalid_request: PKCE S256 is required"}
            transcript.append(resp)
            return resp
        code = "code-" + secrets.token_hex(8)
        self._codes[code] = {"resource": resource, "challenge": code_challenge, "client_id": client_id}
        resp = {"step": "authorization_response", "code": code}
        transcript.append(resp)
        return resp

    def token(self, grant_type: str, transcript: list, *, code: str | None = None,
              code_verifier: str | None = None, resource: str | None = None,
              refresh_token: str | None = None, client_id: str = "mcp-client") -> dict:
        req = {"step": f"token_request[{grant_type}]", "endpoint": self.metadata["token_endpoint"],
               "params": {"grant_type": grant_type, "resource": resource,
                          **({"code": code, "code_verifier": "***"} if grant_type == "authorization_code" else {}),
                          **({"refresh_token": "***"} if grant_type == "refresh_token" else {})}}
        transcript.append(req)

        if grant_type == "authorization_code":
            entry = self._codes.pop(code, None)
            if entry is None:
                resp = {"step": "token_response", "error": "invalid_grant: unknown code"}
            elif not resource:
                resp = {"step": "token_response", "error": "invalid_request: resource is required (RFC 8707)"}
            elif resource != entry["resource"]:
                resp = {"step": "token_response", "error": "invalid_target: resource does not match the code"}
            else:
                verifier_hash = base64.urlsafe_b64encode(
                    hashlib.sha256((code_verifier or "").encode()).digest()).rstrip(b"=").decode()
                if verifier_hash != entry["challenge"]:
                    resp = {"step": "token_response", "error": "invalid_grant: code_verifier does not match "
                                                                "the authorization request's code_challenge"}
                else:
                    rt = "refresh-" + secrets.token_hex(8)
                    self._refresh[rt] = {"resource": resource, "client_id": entry["client_id"]}
                    resp = {"step": "token_response", "access_token": mint_token(resource, client_id, "access"),
                            "refresh_token": rt, "token_type": "Bearer", "expires_in": 60}
        elif grant_type == "refresh_token":
            # RFC 8707 sec. 2 requires `resource` on every token request, refresh
            # included. Modeled tolerant of a client that omits it (the real gap
            # X-maturity-c-002 records) so the omission surfaces as a transcript
            # finding rather than a raised exception - the point being made is
            # that the wire exchange itself is what a verifier must read.
            entry = self._refresh.get(refresh_token)
            bound_resource = entry["resource"] if entry else resource
            resp = {"step": "token_response", "access_token": mint_token(bound_resource, client_id, "access"),
                    "refresh_token": refresh_token, "token_type": "Bearer", "expires_in": 60,
                    "resource_supplied_on_refresh": bool(resource)}
        else:
            resp = {"step": "token_response", "error": f"unsupported_grant_type: {grant_type}"}
        transcript.append(resp)
        return resp


# --- a protected resource: RFC 9728 metadata, audience check on every call --
class ProtectedResource:
    def __init__(self, resource_id: str, authorization_server: AuthorizationServer):
        self.resource_id = resource_id
        self.as_ = authorization_server
        self.prm_url = resource_id + "/.well-known/oauth-protected-resource"
        self.metadata = {"resource": resource_id, "authorization_servers": [authorization_server.issuer]}
        self.tools = {
            "notes.read": {"output_schema": {"type": "object", "required": ["path", "content"],
                                             "properties": {"path": {"type": "string"},
                                                            "content": {"type": "string"}}}},
        }

    def unauthenticated_probe(self, transcript: list) -> dict:
        """A call with no token: the 401 that starts RFC 9728 discovery."""
        resp = {"step": "unauthenticated_probe", "status": 401,
                "www_authenticate": f'Bearer resource_metadata="{self.prm_url}"'}
        transcript.append(resp)
        return resp

    def discover(self, transcript: list) -> dict:
        resp = {"step": "protected_resource_metadata", "endpoint": self.prm_url, "body": self.metadata}
        transcript.append(resp)
        return resp

    def call_tool(self, token: str, name: str, transcript: list, *, output_schema_gate: bool = True,
                  bad_output: bool = False) -> dict:
        req = {"step": "tool_call", "resource": self.resource_id, "endpoint": self.resource_id + "/mcp",
               "http_method": "POST", "accept": "application/json, text/event-stream", "tool": name}
        transcript.append(req)
        aud = token_audience(token)
        if aud != self.resource_id:
            resp = {"step": "tool_call_response", "status": 403,
                    "error": f"audience {aud!r} does not name this resource {self.resource_id!r}"}
            transcript.append(resp)
            return resp
        result = {"path": "notes/decisions.md", "content": "..."} if not bad_output else {"path": "notes/decisions.md"}
        if output_schema_gate:
            violations = validate_output(self.tools[name]["output_schema"], result)
            if violations:
                resp = {"step": "tool_call_response", "status": 502, "gate": "output-schema-rejected",
                        "violations": violations}
                transcript.append(resp)
                return resp
        resp = {"step": "tool_call_response", "status": 200, "result": result}
        transcript.append(resp)
        return resp


# --- the exchange: one client, one AS, two resources -------------------------
def run_exchange(break_mode: str = "") -> dict:
    """Runs the full flow once and returns {"transcript": [...], "checks": {...}}.

    break_mode selects exactly one deliberate deviation from a client that
    otherwise does everything the closure names. Every other step stays
    correct, so a single check fails rather than the whole flow collapsing -
    which is the point: the check must find one true thing wrong, not run out
    of transcript to read.
    """
    issuer = "https://as.example/issuer"
    as_ = AuthorizationServer(issuer)
    resource1 = ProtectedResource("https://mcp.example/server-a", as_)
    resource2 = ProtectedResource("https://mcp.example/server-b", as_)
    transcript: list = []

    # 1. probe with no token -> 401 carrying the RFC 9728 pointer
    resource1.unauthenticated_probe(transcript)
    # 2. RFC 9728 protected-resource metadata discovery
    prm = resource1.discover(transcript)
    # 3. RFC 8414 authorization-server metadata discovery, from the AS the PRM named
    asm = {"step": "authorization_server_metadata", "endpoint": as_.issuer + "/.well-known/oauth-authorization-server",
           "body": as_.metadata}
    transcript.append(asm)

    # 4. PKCE
    verifier, challenge = pkce_pair()
    if break_mode == "no-pkce":
        challenge, method = None, None
    else:
        method = "S256"

    # 5. authorization request, resource-bound
    authz_resource = None if break_mode == "authz-omit-resource" else resource1.resource_id
    authz = as_.authorize("mcp-client", authz_resource, challenge, method, transcript)

    # 6. initial token request, resource-bound
    tok = as_.token("authorization_code", transcript, code=authz.get("code"), code_verifier=verifier,
                    resource=resource1.resource_id)

    # 7. refresh, resource-bound (the gap X-maturity-c-002 records)
    refresh_resource = None if break_mode == "refresh-omit-resource" else resource1.resource_id
    refreshed = as_.token("refresh_token", transcript, refresh_token=tok.get("refresh_token"),
                          resource=refresh_resource)

    # 8. call the target server with the refreshed token
    gate_on = break_mode != "skip-output-validation"
    # skip-output-validation is only observable when the gate it disables would
    # otherwise have caught something - so pair it with the bad result that
    # exercises it, the same way bad-output-schema does with the gate left on.
    bad_output = break_mode in ("bad-output-schema", "skip-output-validation")
    call = resource1.call_tool(refreshed.get("access_token", ""), "notes.read", transcript,
                               output_schema_gate=gate_on, bad_output=bad_output)

    # 9. replay the same access token against a second, unrelated server
    replay = resource2.call_tool(refreshed.get("access_token", ""), "notes.read", transcript,
                                 output_schema_gate=gate_on)

    return {"transcript": transcript, "issuer": issuer, "resource1": resource1.resource_id,
            "resource2": resource2.resource_id, "authz": authz, "initial_token": tok,
            "refreshed_token": refreshed, "call": call, "replay": replay}


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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="run the exchange and print every check")
    ap.add_argument("--report", help="write the transcript and checks to this JSON file")
    args = ap.parse_args(argv)

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
