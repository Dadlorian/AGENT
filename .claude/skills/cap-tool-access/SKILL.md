---
name: "cap-tool-access"
description: "A unit of work reaches tools published by anyone, per the Model Context Protocol: discovery, descriptors, argument checking before a call leaves, plus how a catalogue is built, counted and swapped. Load it when asking what this agent can actually do, where the list of callable things comes from, or whether a tool endpoint is working or merely answering."
---

# cap-tool-access

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for reaching tools published by anyone, so what the core imports is the capability and its standard, and the endpoint that serves it today is only an adapter. | sourced | `F-b3-06`, `F-b3-01`, `E-capability-tool-access` "Tool access** \| Model Context Protocol" |

## Entities

| Entity |
|---|
| `E-capability-tool-access` |
| `E-standard-model-context-protocol` |
| `E-adapter-mcp-endpoint` |
| `E-swap-candidate-any-mcp-server` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-model-context-protocol` | unverified | unverified | - | `F-b3-06`, `X-cap-tool-access-001`, `X-cap-tool-access-002` |

- `E-standard-model-context-protocol` version note: revision unverified. The skill manifest carries specification revision 2026-07-28 as claimed; the two records on file for it - the specification landing page and a release-candidate announcement describing that revision as the largest since launch - are search-only, and neither was fetched from this environment.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| bind_server (proposed operation set; PASS.md names the standard for this capability, not the calls) | a server reference and the authorization the platform holds for it | a binding handle plus the building blocks that server actually publishes, so a caller learns what is there rather than assuming it (proposed) | proposed | `X-cap-tool-access-001` |
| list_tools (proposed) | a binding handle | the catalogue: zero or more tool descriptors, each carrying a name, a declaration of whether calling it changes anything, and an input schema. The count is part of the answer, because an empty catalogue is a valid response and a useless one (proposed) | proposed | `X-cap-tool-access-001`, `F-a6-03` |
| call_tool (proposed) | a binding handle, a tool name from the catalogue, arguments already validated against that tool's input schema, and the correlation the platform stamps | one tool result, or the typed problem object that cap-errors defines. A tool that reports its own failure inside a successful envelope is mapped onto the problem before the result leaves the adapter (proposed) | proposed | `X-cap-tool-access-001`, `F-b4-07` |
| read_resource (proposed) | a binding handle and a resource URI, which may be constructed from a parameterised template the server publishes | read-only data for context. A read that changes nothing is not a tool call, and keeping the two apart is what lets policy and idempotency above treat them differently (proposed) | proposed | `X-cap-tool-access-001`, `X-cap-tool-access-004` |

### Shapes (JSON Schema 2020-12)

**tool-descriptor (proposed summary shape; the full descriptor, the resource-template shape and the call shapes are in references/tool-access-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:tool-descriptor:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "name",
    "input_schema",
    "effect"
  ],
  "description": "Proposed. One entry of the catalogue list_tools returns. The platform stores it as data; nothing is generated from it at build time.",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "description": "The only identifier a caller uses. Unique within a binding."
    },
    "description": {
      "type": "string",
      "description": "For a person or a model to read. Never parsed by the platform to decide anything."
    },
    "input_schema": {
      "type": "object",
      "description": "A JSON Schema 2020-12 document. Arguments are validated against it before the call leaves the platform."
    },
    "effect": {
      "enum": [
        "read_only",
        "mutating",
        "unknown"
      ],
      "description": "Declared, not inferred from the description text. unknown is treated as mutating by everything above."
    },
    "idempotent": {
      "type": "boolean",
      "default": false,
      "description": "Whether repeating the call with the same arguments is safe. Read by the idempotency guarantee above, never by the caller."
    }
  }
}
```

**tool-call-result (proposed summary shape)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:tool-call-result:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "tool",
    "ok",
    "correlation_id"
  ],
  "description": "Proposed. What call_tool returns. ok is false only when the platform has already produced the problem object; there is no third state a caller has to interpret.",
  "properties": {
    "tool": {
      "type": "string",
      "minLength": 1
    },
    "ok": {
      "type": "boolean"
    },
    "content": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "What the tool produced, as typed blocks. Opaque to the platform."
    },
    "correlation_id": {
      "type": "string",
      "minLength": 1,
      "description": "Stamped explicitly by the platform on the way out and on the way back; never inherited from a trace context that crossed the boundary."
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1",
      "description": "Present when ok is false. The failure shape cap-errors defines."
    }
  }
}
```

**What a failure looks like (proposed): problem details, not prose [caller's view, folded from cap-tool-access-use]** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:not-declared",
  "title": "A tool the unit did not declare",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Refused before anything was dispatched. Branch on type; read detail only to report it. `urn:agentic:problem:tool-not-declared` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `policy-denied`, which is also 403 and not retryable, with the called name and the declared surface in detail and a rule_id naming the declaration rule.",
  "examples": [
    {
      "type": "urn:agentic:problem:tool-not-declared",
      "title": "Tool is not in this unit's declared surface",
      "status": 403,
      "detail": "called 'delete_branch'; declared surface is read_file, list_dir",
      "retryable": false,
      "correlation_id": "run-2026-09-03-0011"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The capability is the contract and the endpoint is the adapter: what the core imports is 'a unit of work reaches tools published by anyone', and the standard that governs it is the Model Context Protocol. | sourced | `F-b3-06`, `F-b3-01`, `E-capability-tool-access` "Tool access** \| Model Context Protocol \| MCP endpoint" |
| The swap candidate for this row is a class rather than a list of products, so a unit reaches any conformant server over the same client and nobody has to link against a library of ours; agentic-stack states design rule 4 (F-b1-05) and this row is its consequence here. | sourced | `F-b3-06`, `F-b1-05` "any MCP server" |
| Live and authenticated is not the same as working: the endpoint recorded on this substrate is live and authenticated with zero tools registered, which is a conformant answer to every call and a capability that does nothing. The count of registered tools is therefore part of the contract, not part of the monitoring. The record carries status claimed. | sourced | `F-a6-03` "Live and authenticated, **zero tools registered**" |
| Every tool descriptor carries an input schema in the dialect cap-document-validation governs (F-b3-09), and arguments are validated against it before the call leaves the platform. A server that publishes a tool with no schema publishes something this interface cannot call. | sourced | `F-b3-09` "JSON Schema 2020-12" |
| The three building blocks stay distinct at the boundary - a tool is called and may change something, a resource is read and changes nothing, a prompt is a template. Collapsing a read into a tool call is what makes policy, budget and idempotency above unable to tell the two apart. | sourced | `X-cap-tool-access-001`, `X-cap-tool-access-004` "Tools are software functions that an LLM can directly call to gain access to external resource data, Resources are passive data sources that can provide read only access to data for context, and Prompts are pre-built instruction templates" |
| Session affinity is not a requirement this interface imposes. The revision the manifest names is described as having a stateless core that scales on ordinary infrastructure, so a binding is addressable rather than pinned, and any adapter that needs a sticky session declares that as its own gap. | sourced | `X-cap-tool-access-002` "a stateless core that scales on ordinary HTTP infrastructure" |
| A failed tool call returns the typed problem object cap-errors owns (F-b4-07), never the server's own error text and never a success envelope with a failure written inside it, because a caller that has to read the words to know what happened is parsing prose. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a tool through the same call. How the work arrived is not a field of the call, so one caller-side handler covers all three. cap-document-validation states the same record (T-t1-01) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: moving a tool to another server, adding a tool to the catalogue, tightening its input schema or changing how it is authorized changes nothing in a caller that declares names and reads ok, content and problem. cap-document-validation states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion a result will be judged against. agentic-stack and cap-document-validation both state design rule 6 (F-b1-07); it forbids it on this interface specifically - it never appears in a tool's arguments, in a tool description a unit can read, or in any resource reachable through a binding the unit holds - because tools are the one surface a unit can enumerate and read at will. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |
| Which product serves a tool, at what version, on what host, over what transport. None of it appears in a descriptor, a call or a result, so no caller can branch on it; products belong in the adapter rows below. agentic-stack and cap-errors both state the rule this follows (F-part-c-09). | sourced | `F-part-c-09` "Products belong in the adapter column only." |
| The server's own credentials and its internal implementation of a tool. A unit learns a tool's name, its effect and its input schema, and nothing about how the work gets done - which is what lets the same name be served by a different server tomorrow. | sourced | `F-b3-06` "any MCP server" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability plus its standard before any endpoint is named: 'a unit of work reaches tools published by anyone, per the Model Context Protocol, revision unverified'. Read this row the way the table's template row is read. | build-adapter-pair already states that the interface survives the swap and the implementation does not (F-b3-18), and cap-document-validation reads that same line for its checker. What this adds is our own consequence, proposed: for tool access the pull is the opposite of the usual one - the tools that happen to be registered today are so easy to enumerate that a contract written around them looks complete right up to the moment someone else publishes one. | sourced | `F-b3-06`, `F-b3-18` "the adapter changes and the core does not" |
| 2 | Import the three building blocks the protocol publishes and keep them distinct: tools that are called, resources that are read, prompts that are templates. Do not fold reads into calls to shorten the interface. | The distinction is in the standard rather than ours, and it is the distinction every guarantee above this boundary needs: a read costs nothing to repeat, a call may not be repeatable at all. | sourced | `X-cap-tool-access-001` "Tools are software functions that an LLM can directly call to gain access to external resource data, Resources are passive data sources" |
| 3 | Require an input schema on every tool descriptor, validate arguments against it before the call leaves the platform, and refuse a tool that publishes none. | cap-document-validation owns the dialect and its validator (F-b3-09). What this adds here is our own consequence, proposed: the schema arrives from a server we may not control, so it is untrusted input that must itself be checked against the meta-schema before anything is validated with it. | sourced | `F-b3-09` "JSON Schema 2020-12 \| in place \| any 2020-12 validator" |
| 4 | Give every unit of work a declared tool surface: the list of tool names it may call, resolved against the catalogue at bind time, with an undeclared name refused before any call is made. | Proposed. A unit that can call whatever a binding happens to publish inherits every future tool anyone registers, which makes both policy and the isolation guarantee above unable to say what the unit could do; the declared list is also the thing a composition can assert on afterwards. | sourced | `F-b4-04` "before execution, not after spend" |
| 5 | Count tools, never only health. Any check on this capability asserts a non-zero catalogue and a non-zero number of schemas validated, in addition to conformance. | The endpoint on this substrate is recorded live and authenticated with zero tools registered, so conformance alone reports green over a capability that can do nothing; the count is the assertion that has teeth. | sourced | `F-a6-03`, `F-part-c-04` "Live and authenticated, **zero tools registered**" |
| 6 | Record the protocol revision as unverified until the published specification has been read in an environment that can fetch it, and keep the revision the manifest names as a claim rather than a fact. | build-skill-authoring already requires a standard to carry a version or the unverified marker (F-part-c-10). What this adds is our own consequence, proposed: both records on file for this standard are search results, one of them an announcement of a release candidate, which is the weakest kind of version evidence there is. | sourced | `F-part-c-10`, `X-cap-tool-access-002` "The 2026-07-28 release is the largest revision of the protocol since launch" |
| 7 | Choose the second adapter on execution model, not on brand: a catalogue we register into and run ourselves against a catalogue published by someone else, changing without us, reached over the same client. | build-adapter-pair owns the test (F-b1-04, F-part-c-05). What this adds here is our own consequence, proposed: a second endpoint of our own would leave the assumption that we know the tool list in advance completely untested, and that assumption is the one that decides whether this interface is real. | sourced | `F-b1-04`, `F-part-c-05` "chosen to prove the interface is not shaped around its current implementation" |
| 8 | Map every failure onto the typed problem object before it leaves the adapter, including a tool that reports its own failure inside an otherwise successful envelope. | cap-errors owns the failure shape (F-b4-07); what this adds, as our own consequence and proposed, is that this boundary has two failure channels - the transport and the tool's own result - and only one of them looks like a failure, so the second is where untyped errors survive. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 9 | Declare the tool names this unit needs, then call one by name with its arguments. Do not fetch the catalogue, do not read schemas, and do not pass a server address. | It has to be simple to use, and every field you fill in is a decision you now own. The declared list is the one decision worth making, because it is what anyone reading later uses to know what this unit could do. | sourced | `T-t3-01` "It has to be simple to use." |
| 10 | Proposed: open references/tool-access-shapes.md when implementing or reviewing the full descriptor, the resource-template shape, or the call and result shapes. The body of this skill is enough to judge a candidate server and to decide what the core imports without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full shapes exceed the progressive-disclosure budget for a skill body, and a reader deciding whether a server may serve this interface does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the green-gate finding (F-a7-03). What it adds here, as our own consequence and proposed: an empty catalogue is that finding in this capability's own shape, because every conformance assertion passes and nothing was ever exercised. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Prefer a resource to a tool for anything read-only, and publish a parameterised template rather than one tool per file. A read modelled as a call spends a mutating-call budget, a policy decision and an idempotency key on something that changes nothing. | sourced | `X-cap-tool-access-004` "Resources are passive data sources that provide read-only access to structured data." |
| Proposed: treat the catalogue as versioned data and diff it between runs. A tool that quietly disappeared is a behaviour change that no code review will show, and on this capability the observable symptom is a unit that suddenly does less while every check stays green. Research query: has the recorded live endpoint (F-a6-03, zero tools registered) actually been diffed against a later catalogue state to confirm a disappearance is detectable this way, or is that still a hypothetical failure mode? | proposed | `F-a6-03` |
| Expect a class of servers rather than one: the protocol is described as defining a universal way to expose and reach tools independently of which model is used, which is the reason to keep the contract at the level of the catalogue and the call rather than at the level of whatever is registered today. | sourced | `X-cap-tool-access-003` "defining a universal protocol for exposing and accessing tools independent of which LLM you use" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-mcp-endpoint` | today | bind_server, list_tools, call_tool and read_resource served by the endpoint this platform runs and registers tools into itself. PASS.md records it in the capability table as today's adapter for this row, and separately as live and authenticated with zero tools registered. | Proposed: cannot demonstrate that the catalogue is discovered rather than assumed, because the same people write the tools, register them and call them. Its authorization is ours, its transport is ours, and its tool list changes only when we change it - so every assumption about knowing the surface in advance holds trivially and is never tested. | Point the binding at the other adapter and run the same conformance suite: zero conformance failures, a non-zero catalogue, every input schema valid against the 2020-12 meta-schema, and an undeclared tool name refused. No core change is expected, because the core imports the catalogue and the call rather than the endpoint. | claimed | `F-b3-06`, `F-a6-03` "Model Context Protocol \| MCP endpoint" |
| `E-swap-candidate-any-mcp-server` | second | the same four operations served by a conformant server published by someone else, reached over the same client with no code of ours inside it: its catalogue is authored, versioned and changed outside this platform, and its authorization is its own. | Proposed: cannot promise a stable tool list, cannot be made to add a field the interface would like, and may withdraw a tool between two runs. That is the point of the pair - it breaks the assumption that the catalogue is known before the binding is opened, which is the assumption a same-shape second endpoint of ours would leave untouched. | Proposed: the axes that must differ are catalogue_authority (a tool list we register and freeze, versus one authored and changed outside this platform between runs) and call_locality (a co-located endpoint whose authorization is ours, versus a remote server holding its own). Select by configuration with no code edit between runs, then compare both reports against the same assertions. | claimed | `F-b3-06`, `F-b1-04` "any MCP server" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/tool-access/test.sh && python3 harness/tool-access/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 372cdc1: exit 0; last lines: adapters_run=2 \| conformance PASSED: 34/34 cases, 2 binding(s) |
| Deliberate breakage | Append a product-name comment (`# breakage: litellm`) to the end of harness/tool-access/call.py, outside adapters/. Restored with `git checkout -- harness/tool-access/call.py`. |
| Expected failure | Measured by tools/measure.py at 372cdc1: exit 1; last lines:   ok   11 cases reported NOT EXERCISED rather than passing \| passed 30, failed 6 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-a6-03` "MCP endpoint \| Live and authenticated" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `cap-tool-access-implement` | Turn the contract in cap-tool-access into something that runs here: two catalogues behind one client, the endpoint that is live with zero tools registered filled one tool at a time and counted, and every cross-cutting guarantee attached around the call rather than inside the server. | `references/cap-tool-access-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-evidence`, `build-skill-authoring`, `cap-document-validation`, `cap-errors`

Used by: `compose-workflow`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which revision of the protocol does this interface target, and does the endpoint that runs today speak it? | A fetch of the published specification recording the revision string and the negotiated protocol version reported by each adapter at bind time, with the date. Both records on file are search results, and one of them describes the named revision as a release candidate rather than a ratified revision. | Carry the revision the manifest names as claimed, record version_status unverified, and treat any conformance result as claimed until the specification has been read and the negotiated version read back from a running adapter. | `X-cap-tool-access-002`, `F-part-c-10` "The 2026-07-28 MCP Specification Release Candidate" |
| Do resources and prompts belong in the contract the core imports, or only tools? | Count, over a representative set of units, how many need read-only context that no tool call could serve, and how many use a server-published prompt template rather than one of ours. If both counts are zero, the imported surface is call_tool and list_tools alone. | Import all three blocks, require only tools of an adapter, and let a server that publishes no resources answer read_resource with an empty list rather than an error. | `X-cap-tool-access-001` "three primary building blocks" |
| Where is a unit's declared tool surface enforced - in the client the platform owns, or by the server? | 1-3-1 applied (TARGET T5). The three options were: enforce in the platform's client before dispatch; ask each server to scope its catalogue per caller; do both. Server-side scoping cannot be relied on for a server published by someone else, and doing both doubles the place a refusal can come from. Recommendation taken: enforce in the client, and treat any server-side scoping as defence in depth that is never the assertion a check reads. | The declared surface is enforced in the platform's client, before dispatch, and the conformance suite asserts the refusal there. | `T-t5-02`, `F-b3-06` "identify the three best possible solutions that align to the goal" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-tool-access 2831cb4f, 2026-09-03 |
