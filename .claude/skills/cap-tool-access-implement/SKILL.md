---
name: cap-tool-access-implement
description: How to build the Tool access capability on this stack: an adapter over the endpoint that already runs, a second adapter that is a catalogue nobody here controls, how to migrate work that reaches its tools by hard-wired code today, where the budget, policy, identity, telemetry, provenance and idempotency guarantees attach to a call, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the client that discovers, validates and dispatches a tool call, when registering something into the endpoint that is live with nothing in it, when deciding what the second catalogue should be, or when a check on the tool surface passes and the unit still cannot do anything.
---

# cap-tool-access-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-tool-access into something that runs here: two catalogues behind one client, the endpoint that is live with zero tools registered filled one tool at a time and counted, and every cross-cutting guarantee attached around the call rather than inside the server. | sourced | `F-a6-03`, `F-b3-06`, `E-capability-tool-access` "MCP endpoint \| Live and authenticated, **zero tools registered**" |

## Entities

| Entity |
|---|
| `E-capability-tool-access` |
| `E-standard-model-context-protocol` |
| `E-adapter-mcp-endpoint` |
| `E-swap-candidate-any-mcp-server` |

## Contract

### Shapes (JSON Schema 2020-12)

**ToolAccessBinding (proposed shape; what selects a catalogue, and the only place a server is named)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "declared_tools",
    "catalogue_authority"
  ],
  "description": "Proposed. Read by the client factory only. Nothing in the core, and no caller, reads this object or branches on adapter.",
  "properties": {
    "adapter": {
      "type": "string",
      "description": "Adapter entity id. Selecting a catalogue is configuration; there is no code path that chooses one."
    },
    "declared_tools": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "description": "The unit's declared surface. Resolved against the catalogue at bind time; a name outside it is refused before dispatch."
    },
    "catalogue_authority": {
      "enum": [
        "ours",
        "external"
      ],
      "description": "Who may change the tool list between runs. external means the binding must re-read the catalogue rather than cache it across runs."
    },
    "server_marker": {
      "type": "string",
      "description": "Read back from the running server at bind time and asserted against, so a swap that never happened is visible."
    }
  }
}
```

**ToolAccessConformanceReport (proposed shape; the counters the definition of done below asserts on)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "per_adapter"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 2,
      "description": "Distinct catalogues exercised. Fewer than two means the swap was not tested."
    },
    "per_adapter": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "adapter",
          "server_marker",
          "conformance_failures",
          "tools_listed",
          "schemas_checked",
          "schemas_invalid",
          "undeclared_refused"
        ],
        "properties": {
          "adapter": {
            "type": "string"
          },
          "server_marker": {
            "type": "string",
            "description": "Read from the running server, not from the binding record."
          },
          "conformance_failures": {
            "type": "integer",
            "minimum": 0,
            "maximum": 0
          },
          "tools_listed": {
            "type": "integer",
            "minimum": 1,
            "description": "The assertion a conformance-only check does not make."
          },
          "schemas_checked": {
            "type": "integer",
            "minimum": 1
          },
          "schemas_invalid": {
            "type": "integer",
            "minimum": 0,
            "maximum": 0
          },
          "undeclared_refused": {
            "type": "integer",
            "minimum": 1,
            "description": "Calls outside the declared surface refused before dispatch."
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two catalogues differ on catalogue_authority and call_locality, in the sense build-adapter-pair defines. One is registered and frozen by us; the other is authored outside this platform and may change between runs. A pair that agrees on both axes is rejected and a different second catalogue is found. | proposed | `F-b1-04` |
| Apply build-adapter-pair: selecting the catalogue is configuration, and no core code and no caller branches on which one answered - the swap test agentic-stack states as design rule 1; proposed pointer, see that skill. | proposed | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| cap-tool-access states the endpoint's recorded state (F-a6-03). What this adds: it is the starting point of the migration, so the work here is registering real tools and counting them rather than standing an endpoint up, and every count below starts at zero. | sourced | `F-a6-03` "Live and authenticated, **zero tools registered**" |
| The endpoint that runs today becomes today's adapter and is not replaced; agentic-stack states this constraint (F-part-c-11) and the consequence here is that no instruction in this skill asks anyone to tear down a running tool endpoint in order to adopt the interface. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| The cross-cutting guarantees are attached around the call, never inside the server: the platform applies each and a caller cannot decline them, so a server offering its own rate limit, its own audit log or its own approval prompt has offered an opt-out that must not be wired in place of the platform's. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them" |
| Every mutating tool call is externally-triggered work from the server's point of view and must be safe to replay, so the idempotency key travels with the call and the lease that makes it mean something is applied above this adapter, not inside the tool. | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| Refusal is decided before the call is dispatched, not after the tool has done its work, which on this boundary means the policy decision and the declared-surface check both sit in front of the client's dispatch rather than in a wrapper around its result. | sourced | `F-b4-04` "Refusal is deterministic and happens before execution, not after spend" |
| Apply build-evidence-record: every statement here about how a server behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test; no adapter here has been run in this repository; proposed pointer, see that skill. | proposed | `F-a5-04`, `F-part-c-08` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's adapter as a thin client over the endpoint that already runs: bind, read the catalogue back from the server, validate each published input schema against the meta-schema, and dispatch calls by name. Add nothing to the interface to accommodate it. | agentic-stack states that Part A is substrate and what runs is not to be replaced (F-part-c-11). What this adds: the endpoint currently publishes nothing, so the temptation is to skip the catalogue read and wire calls straight to code we own - which produces a client that cannot talk to any other server. | sourced | `F-part-c-11`, `F-a6-03` "Do not propose replacing what runs." |
| 2 | Register tools into that endpoint one at a time, each with an input schema, and make the registered count a number the pipeline reports rather than a fact someone remembers. | cap-tool-access states the endpoint's recorded state (F-a6-03) and requires the count in the contract. What this adds here: the count has to appear in the pipeline's own report, because a number nobody prints is a number nobody notices returning to zero. | sourced | `F-a6-03`, `F-part-c-04` "Live and authenticated, **zero tools registered**" |
| 3 | Build the second adapter as a conformant server published outside this platform, reached over the same client with no code of ours inside it, and re-read its catalogue at every bind rather than caching it across runs. | cap-tool-access chooses the pair on execution model (F-b1-04); what this adds is the operational consequence, which is that an external catalogue can change between two runs of the same suite, so any client that cached a tool list starts failing in a way that looks like a server fault and is not. | sourced | `F-b1-04`, `F-b3-06` "any MCP server" |
| 4 | Record the pair's differs_in_execution_model naming catalogue_authority and call_locality, and write the second adapter's gaps down as gaps: it can withdraw a tool, it will not add a field we ask for, and its authorization is not ours to widen. | build-adapter-pair already states that a swap needing a core change means the boundary is drawn wrong (F-meta-04). What this adds: widening the contract until both catalogues satisfy every member is the quiet version of that failure, so the gap is declared and the conformance run asserts on it instead. | sourced | `F-meta-04`, `F-b1-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 5 | Migrate one hard-wired tool path at a time: put the client in front of an existing call site, keep the site working, and count paths converted. Do not attempt a cutover of all of them at once, and do not let a converted path and an unconverted one look alike in the code. | Proposed. The risk on this capability is not that a conversion fails but that a call which still reaches a service directly is indistinguishable from one that went through the catalogue, and only the second is covered by the policy, budget and idempotency wiring below. | proposed | `F-b4-01` |
| 6 | Wire the guarantees around dispatch in this order: identity names the actor and the delegation hop, policy decides, the budget ceiling is checked, the idempotency key is leased for anything mutating, telemetry stamps the correlation explicitly, and provenance records what the call produced. | Each is applied by the platform rather than requested, and on this boundary they must all attach to one place - the client's dispatch - because a tool server we do not own will not apply any of them for us. | sourced | `F-b4-01`, `F-b4-03`, `F-b4-05` "Every action names an actor, including delegated agent actors" |
| 7 | Stamp the correlation attribute explicitly on every call and read it back off every result, on both adapters, and assert in the conformance run that it survived each of them. | agentic-stack already states the trace-context finding (F-a7-02). What this adds: an external server has no reason to propagate anything of ours, so this is the boundary where an inherited context silently becomes nothing at all. | sourced | `F-a7-02`, `F-b4-06` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 8 | Assert which server actually answered by reading a marker back from it at bind time, rather than trusting the adapter name written in the binding. | agentic-stack already states the configuration finding (F-a7-04). What this adds: at the catalogue level the same failure mode produces two green conformance runs against the same endpoint, which reads as a proven swap and is not one. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 9 | Apply build-definition-of-done: run the definition of done below and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: register the smallest useful tool first and run the whole suite against it, rather than designing the full catalogue before anything is callable. One registered tool moves the count off zero, which is the assertion that distinguishes this capability from the state it is in today. | proposed | `F-a6-03` |
| Proposed: validate a published input schema against the meta-schema before validating anything with it, and cache the compiled validator per catalogue_digest. A schema from an external server is untrusted input, and recompiling it per call turns a swap into a latency regression nobody attributes correctly. | proposed | `F-b3-09` |
| agentic-stack already states that callers request a class of model, never a vendor (F-a4-01). What it adds here: a tool that internally calls a model must go through the same gateway rather than holding its own key, or the ceiling around the call cannot see what the call spent. | sourced | `F-a4-01` "Callers request a class, never a vendor" |
| Proposed: let the external catalogue fail honestly instead of pinning a copy of its tool list so both adapters look alike. A pinned copy reports a swap that would not survive the day the external server changes, which is the only day the pair was there to protect against. | proposed | `F-b1-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-mcp-endpoint` | today | bind_server, list_tools, call_tool and read_resource, built as a client over the endpoint PASS.md records as today's adapter for this row. The adapter owns the bind, the catalogue read, the meta-schema check on each published input schema, the declared-surface refusal, and the mapping of every failure onto the problem object. | Proposed: cannot demonstrate discovery, because the catalogue is registered by the same people who call it; and in its recorded state it publishes nothing, so a client written against it alone would never exercise a single tool call. Its authorization and transport are ours, so neither is tested until the second adapter runs. | cap-tool-access records this row of the capability table; what this adds is the operational step. Point the binding at the other adapter, keep the same declared surface, and re-run the conformance suite. No core change is expected. Assert the server marker read back from the running server, not the adapter name written in the binding. | claimed | `F-b3-06`, `F-a6-03` "Model Context Protocol \| MCP endpoint" |
| `E-swap-candidate-any-mcp-server` | second | the same four operations against a conformant server published outside this platform and reached over the same client: its catalogue is authored and versioned elsewhere, its authorization is its own, and the binding re-reads its tool list at every bind. | Proposed: cannot be made to hold its tool list still, cannot be asked to add a field the interface would find convenient, and cannot be given our credentials. Those are its declared gaps, asserted on by the conformance run rather than papered over with a pinned copy of its catalogue. | Proposed: the axes that differ are catalogue_authority (registered and frozen by us, versus authored outside this platform and changeable between runs) and call_locality (a co-located endpoint whose authorization is ours, versus a remote server holding its own). Select by configuration with no code edit between runs, then compare both reports against the same counters. These are the axes cap-tool-access records for this pair. | claimed | `F-b3-06`, `F-b1-04` "any MCP server" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with this implementation: `python3 tools/conformance_tool_access.py --adapter today --adapter second --revision 2026-07-28 --report out/tool-access-conformance.json`. Per adapter it asserts conformance_failures == 0, tools_listed > 0, schemas_checked == tools_listed with schemas_invalid == 0, undeclared_refused >= 1, and server_marker read back from the running server equal to the adapter selected in the binding; across adapters it asserts adapters_run >= 2. |
| Expected | exit 0 and one line per adapter of the form `adapter=<entity> server_marker=<match> conformance_failures=0 tools_listed=<greater than 0> schemas_checked=<equal> schemas_invalid=0 undeclared_refused=1`, followed by `adapters_run=2`. |
| Deliberate breakage | Unregister every tool from the adapter under test, leaving the endpoint live and authenticated and changing nothing else, then re-run both adapters. |
| Expected failure | For that adapter conformance_failures stays 0 while tools_listed and schemas_checked become 0, the non-zero-catalogue assertion fails and the run exits non-zero naming it; the other adapter still reports a non-zero catalogue, so the report singles out the empty one rather than reporting the suite as broken. This is the state PASS.md A6 records for this capability, which a conformance-only check would have called green. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a6-03` "MCP endpoint \| Live and authenticated" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-tool-access`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| cap-tool-access records the swap candidate as a class of servers; how often is such a catalogue re-read, and what happens to a unit whose declared tool disappears mid-run? | Instrument the second adapter over a representative period and count catalogue changes and their kinds: tools added, tools withdrawn, schemas changed. If withdrawals never happen, re-reading at bind is enough; if they do, the refusal needs a type of its own and a retry policy above it. | Re-read the catalogue at every bind, refuse a declared name that is no longer published with the not-found problem type, and never cache a tool list across runs. | `F-b3-06` "any MCP server" |
| Does the platform hold one binding per unit of work, or one long-lived client shared across units? | 1-3-1 applied (TARGET T5). The three options were: one binding per unit; one shared client with per-call declared-surface checks; a pool keyed by server plus declared surface. A shared client makes the declared surface a per-call argument that is easy to omit, and a pool needs an eviction rule nobody has measured. Recommendation taken: one binding per unit of work, since the declared surface is then a property of the binding and cannot be forgotten at a call site. | One binding per unit of work, carrying its declared surface, with connection reuse left to the transport underneath rather than to a shared client object. | `T-t5-02` "use 1-3-1: define the problem" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-tool-access 2831cb4f, 2026-09-03 |
