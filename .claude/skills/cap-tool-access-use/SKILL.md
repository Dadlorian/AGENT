---
name: cap-tool-access-use
description: How to let a unit of work reach a tool and read what came back: the two things you declare, the one field you branch on, two worked calls, what a failure looks like, and why changing where a tool lives changes nothing you wrote. Load it when a human, an agent or an event needs something done that the platform itself cannot do, when writing the caller side of a step that reads a file, queries a log or changes something outside, when deciding what a unit is allowed to reach, when a call comes back refused, or when you are about to write a branch on which server answered.
---

# cap-tool-access-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make reaching a tool a two-line decision: name the tools this unit may call, then call one by name. Discovery, schemas, authorization, retries and which server holds the tool are all below the call, because composability hides the complexity. | sourced | `T-t2-01`, `T-t3-01`, `E-capability-tool-access` "Composability hides the complexity." |

## Entities

| Entity |
|---|
| `E-capability-tool-access` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| declare (proposed) | the list of tool names this unit may call | a binding. The list is checked against what is actually published at bind time, so a name that no longer exists fails here rather than in the middle of the work (proposed) | proposed | `T-t3-01` |
| list (proposed) | the binding | what this unit can call: a name, one line of description and whether calling it changes anything. Not the schemas, not the transport, not the server (proposed) | proposed | - |
| call (proposed) | the binding, a tool name from your declared list, and the arguments | one result: ok plus content, or ok false plus a typed problem. Arguments are checked against the tool's own schema before anything leaves, so a bad argument is a problem you get back, never a half-done call (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**Worked call 1 (proposed): a human asks for work and the unit reads a file through a tool** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:read-only",
  "title": "One read-only call",
  "description": "Declared two tools, called one. Nothing was discovered, negotiated, authorized or retried by the caller.",
  "examples": [
    {
      "declared": [
        "read_file",
        "list_dir"
      ],
      "sent": {
        "tool": "read_file",
        "arguments": {
          "path": "src/ledger/fold.py"
        },
        "correlation_id": "run-2026-09-03-0011"
      },
      "returned": {
        "tool": "read_file",
        "ok": true,
        "content": [
          {
            "kind": "text",
            "media_type": "text/x-python",
            "digest": "sha256:0f2b"
          }
        ],
        "correlation_id": "run-2026-09-03-0011"
      }
    }
  ]
}
```

**Worked call 2 (proposed): an event triggers a call that changes something, twice** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:mutating",
  "title": "One mutating call, delivered twice",
  "description": "The caller sent nothing about replay safety. The tool is declared mutating, so the platform leased the key and the second delivery returned the first result instead of doing the work again.",
  "examples": [
    {
      "declared": [
        "incident_search",
        "open_incident"
      ],
      "sent": {
        "tool": "open_incident",
        "arguments": {
          "title": "disk-io latency above ceiling",
          "severity": 3
        },
        "correlation_id": "evt-2026-09-03-0042"
      },
      "returned": {
        "tool": "open_incident",
        "ok": true,
        "content": [
          {
            "kind": "json",
            "value": {
              "incident": "INC-4471"
            }
          }
        ],
        "replayed": true,
        "correlation_id": "evt-2026-09-03-0042"
      }
    }
  ]
}
```

**What a failure looks like (proposed): problem details, not prose** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:not-declared",
  "title": "A tool the unit did not declare",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Refused before anything was dispatched. Branch on type; read detail only to report it.",
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
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a tool through the same call. How the work arrived is not a field of the call, so one caller-side handler covers all three. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Proposed: two things go in - the declared list and the call - and one field is branched on. Discovery, input schemas, meta-schema checks, authorization, transports, catalogue changes and the identity of the server are all below the call, and a caller that never mentions them still gets every one of them handled. | proposed | `T-t3-01`, `T-t2-01` |
| Enhancing one aspect leaves the rest untouched: moving a tool to another server, adding a tool to the catalogue, tightening its input schema or changing how it is authorized changes nothing in a caller that declares names and reads ok, content and problem. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Budget, policy, identity, telemetry, provenance and idempotency are applied around every call whichever entry point started it, and there is no field for asking for them or declining them. | sourced | `T-t2-03`, `F-b4-01` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| Proposed: a failure arrives as the typed problem object, which cap-tool-access requires this boundary to return and cap-errors defines (F-b4-07). Branch on its type; read detail only to show a person, and never to decide anything. | proposed | `F-b4-07` |
| Proposed: the declared list is the whole of what this unit can reach. It is checked when the binding opens and again on every call, so a tool that appears in the catalogue tomorrow does not silently become something this unit can do. | proposed | `F-b4-04` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Declare the tool names this unit needs, then call one by name with its arguments. Do not fetch the catalogue, do not read schemas, and do not pass a server address. | It has to be simple to use, and every field you fill in is a decision you now own. The declared list is the one decision worth making, because it is what anyone reading later uses to know what this unit could do. | sourced | `T-t3-01` "It has to be simple to use." |
| 2 | Declare the smallest list that does the job, and add to it when a call is refused rather than in advance. | Proposed. A list written wide 'just in case' is indistinguishable from a list that was thought about, and it is the one thing in this call that cannot be tightened later without finding out which entries were real. | proposed | `T-t2-03` |
| 3 | Branch on ok and, when ok is false, on the problem's type. Treat content as data to pass on, not as something to parse for signs of failure. | cap-tool-access requires this boundary to map every failure onto a typed problem, including a tool that reports its own failure inside a successful envelope (F-b4-07); what this adds for a caller is that reading the content for the word 'error' is exactly the parsing that mapping exists to remove. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 4 | Send the same call again if you have to. Do not invent your own deduplication, do not check first whether the work was already done, and do not add a flag saying this is a retry. | cap-tool-access-implement wires the key and the lease around every mutating call (F-b4-08). What this adds for a caller: writing your own deduplication on top produces two mechanisms that disagree at exactly the moment one of them matters. | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| 5 | Ask for read-only data by reading a resource, not by calling a tool that returns it. | Proposed. A read costs nothing to repeat and a call may not be repeatable at all, so modelling a read as a call spends a mutating-call budget, a policy decision and a lease on something that changed nothing. | proposed | `T-t2-03` |
| 6 | Compose upward, not inward: one call is one step. Retries across several tools, a fallback when a tool is missing, an approval before a destructive call and a whole agent are built above this call rather than by adding fields to it. | Any entry can call complex workflows, agents and loops that run across the entire stack, so the complexity belongs to the composition and this call stays the same size no matter how large the thing above it gets. | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| 7 | To change where a tool lives, who publishes it or how it is reached, change configuration. Do not add an argument, and do not write a branch on which server answered. | A caller-side branch on the implementation is the boundary leaking, and it is the one change that would make every future move of a tool your problem instead of a configuration change. | sourced | `T-t2-02`, `F-b1-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| 8 | If this page starts to feel like something you must study before calling, stop and cut it rather than adding to it: the caller-facing surface is a declared list, a call, and one field to branch on. | It cannot be daunting or overly complex, or no one will use it - which makes size a property of the interface to defend, not a documentation problem to solve later. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Set the correlation id yourself and reuse it across every call of the same piece of work, including the refused ones, so the whole run can be found from one value whichever entry point started it. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| cap-tool-access already states that an empty catalogue answers every check and does nothing (F-a6-03). What it adds for a caller: if a binding opens and your declared list resolves to nothing, stop rather than proceeding without tools, because a unit that silently does less looks exactly like one that had nothing to do. | sourced | `F-a6-03` "zero tools registered" |
| Proposed: keep whatever a partially completed sequence of calls produced. A refused call in the middle is a stopping point, not a reason to discard the results of the calls that succeeded, which the platform has already recorded. | proposed | - |
| Proposed: write the declared list where a reviewer can read it next to what the unit is for. It is the only place in the system that answers 'what could this unit actually do', and a list assembled at run time answers it for nobody. | proposed | `T-t2-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/render_skill.py .claude/skills/cap-tool-access-use && python3 tools/validate_skills.py --only cap-tool-access-use`. This skill has no Adapters section, so the validator's product-purity check covers the whole page: it proves that nothing a caller reads here - the operations, the worked calls, the failure - names the server that holds the tool, which is the promise this facet makes. |
| Expected | `rendered cap-tool-access-use/SKILL.md` then `cap-tool-access-use: 0 errors, 0 warnings`, exit 0. |
| Deliberate breakage | In the second worked call, replace the argument value `"disk-io latency above ceiling"` with the name of the durable-execution product PASS.md B3 records as today's adapter for that row, re-render, and re-run the validator. |
| Expected failure | exit 1 with `cap-tool-access-use: product name(s) ['<that product>'] outside Adapters, in section 'Contract'` and a closing `cap-tool-access-use: 1 errors, 0 warnings`. Measured in session cap-tool-access 2831cb4f on 2026-09-03: editing only that argument value in skill.json and re-rendering produced exactly that error line with the product name in the list, 1 errors, 0 warnings and exit 1; restoring the file returned 0 errors, 0 warnings and exit 0. Editing the string in the breakage description as well produces a second identical error naming the Definition of done section, so the edit is made in the shape and nowhere else. |
| Status | measured |
| Evidence | `F-part-c-04`, `T-t2-01` "Composability hides the complexity." |

## Composes with

Builds on: `cap-tool-access`, `cap-tool-access-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should a caller ever be allowed to name the server it wants a tool from? | Count the cases where a composition genuinely cannot proceed without a specific server rather than a specific tool name. If every such case turns out to be a tool that exists in one catalogue and not another, the declared list already covers it and no server selector is needed. | No server selector on the call. A caller declares tool names and the platform resolves them; adding a selector later is cheaper than removing one after callers depend on it. | `T-t2-01` "Composability hides the complexity" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-tool-access 2831cb4f, 2026-09-03 |
