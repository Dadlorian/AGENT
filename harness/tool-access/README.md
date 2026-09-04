# Tool access harness

One binding, one catalogue discovered at bind time, one call whose arguments are
checked against the schema the server published, one call cancelled while it is
still in flight, and a health answer that counts registered tools. The tool
server sits behind an adapter and is chosen by configuration.

The capability is "a unit of work reaches tools published by anyone", governed
by the Model Context Protocol, revision on file 2026-07-28 and unverified. The
endpoint that serves it today is only an adapter, and PASS.md A6 records that
endpoint as live and authenticated with zero tools registered (F-a6-03). That
recorded state is why this harness counts tools instead of reporting green.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/tool-access/test.sh` |
| 2. Watch one call | `ADAPTER=dryrun python3 harness/tool-access/call.py` |
| 3. Swap the server | `ADAPTER=second python3 harness/tool-access/call.py` |
| 4. Prove the interface held | `python3 harness/tool-access/conformance.py --adapter dryrun --adapter second` |
| 5. Run against the host | `bash harness/tool-access/test.sh --live` |
| 6. Check the authorization and transport mechanisms (tool-access-q2), over real loopback sockets | `python3 harness/tool-access/adapters/auth_exchange.py --check` |
| 7. Reproduce the real refresh gap (X-maturity-c-002) | `AUTH_BREAK=refresh-omit-resource python3 harness/tool-access/adapters/auth_exchange.py --check` |
| 8. Point adapters/live.py, unmodified, at a real local endpoint with its token sourced via the same OAuth exchange | `python3 harness/tool-access/adapters/auth_exchange.py --live-demo` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 484 | The capability interface: the tool descriptor and its meta-schema gate, the binding, the call context the platform stamps, the result, the cancel ack, the counting health answer, the closed problem registry, one abstract adapter class. No product, endpoint, transport or protocol method name appears in it |
| `adapters/dryrun.py` | 117 | Deterministic in-process adapter. A catalogue this platform registers itself, five tools, one slow enough to cancel mid-flight, one that fails inside a successful envelope. No network, no privileges |
| `adapters/live.py` | 149 | Today's component: the MCP endpoint on this host, reached over JSON-RPC with the revision declared per request. Reached only through the env vars below |
| `adapters/second.py` | 191 | The second server: a conformant catalogue published outside this platform. Different tool names, an extra required argument on a shared tool, one tool withdrawn between binds, a cancel that can only be recorded. Faithful stub here; `SECOND_SERVER_URL` points it at a real server |
| `adapters/auth_exchange.py` | ~700 | Answers tool-access-q2: which authorization and transport mechanisms are actually in force, verified from a transcript built over real loopback TCP sockets (`LocalDeployment`: an authorization server and two protected-resource servers, each an `http.server` on its own port, an `urllib.request` client on the other end) rather than from configuration or from two halves of the flow calling each other's Python methods directly - the 401's RFC 9728 pointer, RFC 9728 and RFC 8414 metadata discovery, PKCE S256, an RFC 8707 `resource` parameter on the authorization request and on every token request including refresh, the issued token's audience, Streamable HTTP, a captured token rejected by a second server, and a tool result checked against its declared output schema. `AUTH_BREAK=<mode>` isolates one deliberate deviation at a time (`refresh-omit-resource` reproduces X-maturity-c-002's real client gap). `obtain_access_token` is also the function `adapters/live.py` calls (`TOOL_OAUTH_DISCOVER=1`) to source its own bearer token, and `--live-demo` points that unmodified adapter at the local deployment to prove it |
| `binding.json` | 12 | Configuration. Which adapter, the server reference, the declared surface, the call, the call to cancel, the ceiling, the revision |
| `call.py` | 139 | The minimal call. 15 lines of caller code below the `>>> CALLER CODE` marker, counted by `harness/caller_lines.py`; everything above it is the platform |
| `conformance.py` | 466 | The same 17 cases and 6 counts against any adapter, with every argument built from the schema the server published |
| `test.sh` | 166 | The gate: 43 checks, dry run by default, `--live` for the host |
| `provenance.json` | - | Owner skill, co-skills, kb and research ids, what was measured, what stays claimed |
| `out/` | written | Conformance reports, run logs, the two variant bindings the refusal checks use |

## The minimal call

`ADAPTER=dryrun python3 harness/tool-access/call.py`

| # | Line a caller writes | What the platform did without being asked |
|---|---|---|
| 1 | `ad, name = adapter(cfg)` | Selected the tool server from configuration; nothing downstream branches on which answered |
| 2 | `env = envelope(cfg, "human", ...)` | Stamped the correlation id, the run id, the actor and delegation chain, the budget ceiling and the envelope's idempotency key |
| 3 | `stamp = stamper(env, cfg)` | Derived a per-call idempotency key and attached the protocol revision this call declares and the policy verdict |
| 4 | `binding = ad.bind_server(...)` | Read the catalogue from the server, checked every published input schema against the meta-schema, resolved the declared surface, read the marker back |
| 5 | `catalogue = ad.list_tools(binding)` | Handed back data discovered at bind time; nothing was generated at build time |
| 6 | `tool = ad.find(binding, ...)` | Refused a name the catalogue does not carry, before any call |
| 7 | `ad.check_arguments(tool, args)` | Checked the arguments against that tool's own published schema |
| 8 | `ad.call_tool(...)` | Re-ran every gate - revision, catalogue, declared surface, policy verdict, arguments, idempotency, ceiling - then dispatched, and mapped an in-band tool failure onto the problem object |
| 9 | `ad.begin_call(...)` / `ad.cancel(scan)` | Cancelled a second call while it was in flight and said which of two things happened |
| 10 | `ad.health(binding)` | Counted registered tools and checked schemas; the vocabulary is serving / empty / unreachable, never green |

| Result field | dryrun | second |
|---|---|---|
| tools discovered at bind | 5 | 6, then 5 at the next bind |
| declared surface | `notes.read, notes.append, notes.scan, notes.flaky` | identical |
| server marker read back | `catalogue:registered-here` | `catalogue:published-elsewhere` |
| arguments for the shared mutating tool | `path, line` | `path, line, author` |
| cancel mid-flight | `stopped` | `recorded`, effect may still be owed |
| health | `serving (tools_listed=5)` | `serving (tools_listed=6)` |
| caller lines | 15 | 15, unchanged |

## Environment variables

| Variable | Mode | What it names |
|---|---|---|
| `ADAPTER` | any | `dryrun`, `second` or `live`. Overrides `binding.json` |
| `BINDING` | any | Configuration file to read instead of `binding.json` |
| `REVISION` | any | The protocol revision each call declares. Default `2026-07-28` (claimed, unverified) |
| `CEILING_CALLS` | any | Tool calls this run may make. Default from `binding.json` |
| `POLICY_VERDICT` | any | `allow` or `allow-read-only` |
| `ACTOR` / `ENTRY_KIND` | any | The stamped subject and which of the four entries this is |
| `TOOL_ENDPOINT_URL` | live | The MCP endpoint's JSON-RPC URL on this host |
| `TOOL_ENDPOINT_TOKEN` | live | Static bearer token for it. Ignored when `TOOL_OAUTH_DISCOVER=1` |
| `TOOL_OAUTH_DISCOVER` | live | `1` sources the bearer token from `adapters/auth_exchange.py`'s `obtain_access_token` (401 probe, RFC 9728 + RFC 8414 discovery, PKCE, resource-bound authorization code grant and refresh) instead of `TOOL_ENDPOINT_TOKEN` |
| `TOOL_OAUTH_RESOURCE` | live | The resource origin to run that OAuth exchange against. Defaults to `TOOL_ENDPOINT_URL` with a trailing `/mcp` stripped |
| `TOOL_TIMEOUT_S` | live | Request timeout. Default 60 |
| `TOOL_METHOD_LIST` / `_CALL` / `_READ` / `_CANCEL` | live | Method names, default `tools/list`, `tools/call`, `resources/read`, `notifications/cancelled`. Proposed mapping, overridable because both specification records on file are search-only |
| `TOOL_REVISION_HEADER` | live | Header carrying the per-request revision. Default `MCP-Protocol-Version` |
| `SECOND_SERVER_URL` | second | A conformant server published elsewhere. Unset, the adapter runs the same state machine in process |
| `SECOND_SERVER_TOKEN` | second | The partner's own authorization, never ours |
| `SECOND_METHOD_LIST` / `_CALL` / `_READ` | second | The same overridable method names |
| `TOOLS_UNREGISTERED` | dryrun | `1` empties the catalogue: the deliberate breakage |
| `DRYRUN_UNREACHABLE` | dryrun | `1` makes the server unreachable: the failure path |

## What each test proves

| # | Check | What it proves | Would pass if the property were absent? |
|---|---|---|---|
| 1 | 17 cases against the dry-run adapter | Every operation the contract names is implemented and every case is answered | No |
| 1 | `cases_not_exercised=0` | Nothing was reported green because there was nothing to test | No |
| 1b | 15 lines of caller code, no adapter storage named | The minimal call is one call sequence and it stays on the interface | No |
| 1b | `tools discovered at bind` in the caller's own output | The catalogue was read at run time, not compiled into the client | No |
| 1c | Undeclared tool, bad arguments, unserved revision, ceiling, unreachable server | Five failure modes, each a typed problem object, each refused before dispatch where a refusal is possible | No |
| 2 | Conformance before, swap, conformance after | The interface held across two servers, from one declaration, with no code edited between runs (the tree hash is identical across both runs) | No |
| 2 | Marker read back from the running server | A different server actually answered, rather than the same one with a new name in the binding | No |
| 2 | 4 axes differ | The second server breaks a different assumption instead of being a different product of the same shape | No |
| 2 | `tools_listed` differs, declared surface identical | The tool list is discovered per server while a tool name survives the swap | No |
| 2 | The second server's catalogue changes between two binds | A catalogue this platform does not control can move, and the binding re-reads rather than caching | No |
| 3 | Product scan over `.py` and `.sh` outside `adapters/` | No caller can branch on which server answered | No |
| 4 | Breakage: unregister every tool | `conformance_failures` stays 0 while `tools_listed` and `schemas_checked` go 5 to 0, 11 cases report NOT EXERCISED, health says `empty`, and the run exits 1 naming the count | No |
| 5 | Live with no env set | Says clearly that nothing live was measured, rather than passing | No |
| 5 | Live with an empty catalogue | Fails on the count and not on the shape, and says so | No |

## What would pin this interface, and how the boundary avoids it

Source: the blueprint's `MCP endpoint (live, authenticated, zero tools registered)` tool entry, whose `would_pin` reads "A tool named by a server-specific path, or a session-scoped version handshake that cannot refuse one later call", and whose `must_stay_loose` reads "The tool list a unit holds after admission must equal its declared list exactly, and the protocol version must be declared per call rather than agreed once."

| Would pin it | How this harness avoids it | Where to look |
|---|---|---|
| A tool named by a server-specific path | A call names a tool from the catalogue and nothing else; the server reference lives in `binding.json` and never in a call | `interface.py` `begin_call`, conformance case "nothing names a server, a product or a transport on the way out" |
| A version handshake agreed once at bind | The revision is a field of every `CallContext`; an unserved revision is refused on that call and the binding stays usable | `interface.py` `_revision`, conformance case "the protocol revision is declared per call and refused per call" |
| A tool list known before the binding is opened | Every argument the conformance run sends is built from the schema the server published; the second server requires a field this platform never heard of and is still called correctly | `conformance.py` `synth`, `adapters/second.py` `notes.append` |
| A catalogue compiled into the client at build time | The catalogue is read at every bind and compared; the second server withdraws a tool between binds and the run asserts the digest moved | conformance case "the catalogue is read at every bind, not compiled in" |
| Trusting a schema a server published | Every descriptor passes the meta-schema gate before it enters a catalogue, and a tool with no schema never becomes callable | `interface.py` `ToolDescriptor.from_dict`, `check_schema` |
| A health check that answers green | The health vocabulary is serving / empty / unreachable; `empty` is what a live, authenticated, tool-less server gets | `interface.py` `health`, the breakage in step 4 |
| A unit inheriting every tool anyone registers later | The declared surface is resolved at bind and an undeclared name is refused before dispatch with a `rule_id` | `interface.py` `begin_call`, conformance case "a tool outside the declared surface is refused before dispatch" |
| A guarantee the server offers instead of the platform | Correlation, ceiling, idempotency and policy are applied around the call in `interface.py`, where no adapter can decline them | `call.py` `stamper`, `interface.py` `begin_call` |

## Swap procedure

| Step | Action |
|---|---|
| 1 | Run `python3 conformance.py --adapter dryrun --report out/before.json` |
| 2 | Point `binding.json` (or `ADAPTER`) at the other adapter. No code edit |
| 3 | Run `python3 conformance.py --adapter second --report out/after.json` |
| 4 | Compare the two reports: `catalogue_authority`, `call_locality`, `catalogue_stability` and `cancel_outcome` must differ, `server_marker_observed` must differ, `declared_surface` must not, and both must report `conformance_failures=0` with `tools_listed` above zero |

## What is claimed rather than measured

| Claim | Why it is not measured here |
|---|---|
| Live mode against the product endpoint | `adapters/live.py` has never reached the tool endpoint PASS.md A6 records on this host; the request shape, the method names, the header and the failure mapping are unverified against that real server. Its OAuth 2.1 client path is no longer unmeasured in general: `--live-demo` runs the same unmodified adapter, token sourced via `TOOL_OAUTH_DISCOVER=1`, against a real local HTTP endpoint end to end (step 8 above) |
| The protocol revision `2026-07-28` | Both specification records on file are search results, never fetched pages (X-cap-tool-access-001, X-cap-tool-access-002). The standard stick is recorded absent by the owner while fetch is blocked |
| The JSON-RPC method names | This harness's proposed mapping of the four operations onto the protocol; every one is overridable by environment variable |
| The networked form of the second adapter | Until `SECOND_SERVER_URL` points at a real server, the dry run exercises its state machine in process; the shape and the swap procedure are real either way |
| Schema checking | `interface.py` implements a declared subset of JSON Schema 2020-12. cap-document-validation owns the dialect and its validator; a real deployment binds that capability here instead |
