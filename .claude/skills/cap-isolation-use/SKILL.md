---
name: cap-isolation-use
description: How to run one piece of work contained and read what came back: the one field you supply, the three you read, two worked units, what a refusal looks like, and why changing what contains the work changes nothing you wrote. Load it when a human, an agent or an event needs a piece of work run safely, when a step in a workflow or a loop has to execute untrusted or generated code, when work needs to reach one named destination and nothing else, when a credential is about to be handed to something that will run on its own, or when you are about to write a branch on what contained the work.
---

# cap-isolation-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make running one piece of work contained a call with nothing to configure: hand over the work, get back what it produced. Resource envelopes, egress rules, credential brokering and the containment technology itself all sit below the call, because composability hides the complexity. | sourced | `T-t2-01`, `T-t3-01`, `E-capability-isolation` "Composability hides the complexity." |

## Entities

| Entity |
|---|
| `E-capability-isolation` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| run_contained (proposed) | the work: a handle to what should run and the document it runs on, plus a correlation id you choose. Optionally the destinations the work must reach, if any. Nothing else has to be supplied (proposed) | one unit result: the exit status, the outputs it produced with their digests, and what it used. There is no second call to make before you have an answer (proposed) | proposed | `T-t3-01` |
| read (proposed) | the unit result | exit status, outputs, usage. A refusal or a failure arrives instead as a typed problem, so there is no error text to parse and nothing in the result names what contained the work (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**Worked unit 1 (proposed): a human runs generated code and never mentions containment** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:example:contained-run",
  "title": "One unit of work, run to completion with no isolation fields supplied",
  "description": "Sent: the work and a correlation id. Returned: what it produced. The caller wrote no profile, no egress rule and no credential; all three were resolved below the call.",
  "examples": [
    {
      "sent": {
        "work": "unit://run-tests/v1",
        "document": "doc:sha256:1c04\u2026",
        "correlation_id": "run-2026-09-03-0031"
      },
      "returned": {
        "exit_status": 0,
        "outputs": [
          {
            "digest": "sha256:9d17\u2026",
            "media_type": "application/json"
          }
        ],
        "usage": {
          "wall_ms": 21400
        },
        "correlation_id": "run-2026-09-03-0031"
      }
    }
  ]
}
```

**Worked unit 2 (proposed): an event starts work that must reach exactly one destination** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:example:named-destination",
  "title": "One unit of work that names where it must reach, and reaches nowhere else",
  "description": "The only isolation field a caller ever writes is the list of destinations the work must reach. Everything the work tried that was not on that list was refused, and the counters say so.",
  "examples": [
    {
      "sent": {
        "work": "unit://fetch-and-summarise/v1",
        "document": "doc:sha256:44be\u2026",
        "correlation_id": "evt-2026-09-03-0104",
        "reach": [
          "artifacts.internal"
        ]
      },
      "returned": {
        "exit_status": 0,
        "outputs": [
          {
            "digest": "sha256:0ab3\u2026",
            "media_type": "text/markdown"
          }
        ],
        "usage": {
          "wall_ms": 8800
        },
        "containment": {
          "egress_attempts_made": 4,
          "egress_attempts_blocked": 3
        },
        "correlation_id": "evt-2026-09-03-0104"
      }
    }
  ]
}
```

**What a refusal looks like (proposed): problem details, not prose** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:example:isolation-unavailable",
  "title": "Nothing could contain this work as asked",
  "$ref": "urn:agentic:problem:0.1",
  "description": "The work was refused before it ran, rather than run with weaker containment. Branch on type; read detail only to report it.",
  "examples": [
    {
      "type": "urn:agentic:problem:isolation-unavailable",
      "title": "No isolation adapter could admit the unit",
      "status": 503,
      "detail": "profile 'large-gpu' is not resolvable by any configured adapter on this host",
      "retryable": true,
      "retry_after_s": 60,
      "correlation_id": "evt-2026-09-03-0104"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a contained unit through the same call. How the work arrived is not a field of it, so one caller-side handler covers all three. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Proposed: in the ordinary case a caller writes no isolation fields at all. The resource profile, the credential mode and the containment technology are resolved below the call from the agent's profile and the policy in force, which is why the end-to-end consumption example's entry envelope carries no isolation field for any of its four entries. | proposed | `T-t3-01`, `T-t2-01` |
| Enhancing one aspect leaves the rest untouched: replacing what contains the work, adding a resource profile, tightening an egress rule or moving where the unit runs changes nothing in a caller that reads exit status, outputs and usage. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Budget, policy, identity, telemetry and provenance are applied around every contained unit whichever entry point started it, and there is no field for asking for them or declining them. | sourced | `T-t2-03`, `F-b4-01` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| The work gets no network unless you name where it must reach, and no real credential ever: cap-isolation makes both of these properties of the boundary (F-a3-04, F-a3-05), so a caller does not switch them on, off, or in. | sourced | `F-a3-04`, `F-a3-05` "Egress is a flag, default off" |
| Proposed: a refusal arrives as the typed problem object, which cap-isolation requires this boundary to return and cap-errors defines. Work that could not be contained as asked is refused before it runs, never run with weaker containment, so a result you receive at all is a result that was contained as asked. | proposed | `F-b4-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Send the work, the document it runs on, and a correlation id you chose. Write no profile, no egress rule and no credential unless you have a reason. | It has to be simple to use, and every field you fill in is a decision you now own. The fields you leave alone are the ones the platform can change under you without breaking your call. | sourced | `T-t3-01` "It has to be simple to use." |
| 2 | If the work must reach something, name the destinations in `reach` and nothing more. Never ask for 'network', and never ask for a machine size, a kernel option or a filesystem path. | Naming destinations is a statement about the work that any containment technology can honour; asking for a machine is a statement about one of them, and it is the request that would stop your call working the day the platform runs it somewhere else. | sourced | `T-t2-02` "enhancing particular aspects of any element without touching the rest" |
| 3 | Read exit status, outputs and usage. Do not branch on anything else in the result, and do not expect a field naming what contained the work, because there is not one. | Proposed. Those three answer every question a caller actually has - did it work, what did it make, what did it cost - and a branch on anything below them is the boundary leaking into your code. | proposed | `T-t2-02` |
| 4 | Read a failure as a problem object: branch on `type`, use `retryable` and `retry_after_s` as given, and never parse the words. | cap-isolation requires this boundary to return typed failures and cap-isolation-implement wires the untyped paths onto them (F-b4-07); what this adds for a caller is that a refusal to contain the work is a normal, retryable outcome rather than an exception to handle specially. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 5 | To bound work that might not stop, set a deadline when you start it and let the platform end the unit. Do not reach into the unit, and do not write your own timer and killer. | Proposed. The boundary is the thing that can actually destroy a unit, and letting it do so means the same rules apply whichever entry started the work and whatever is containing it that day. | proposed | `T-t2-03` |
| 6 | Compose upward, not inward: one contained unit is one step. Retries, several units in sequence, a fan-out, an approval in the middle and a whole agent are built above this call rather than by adding fields to it. | Any entry can call complex workflows, agents and loops that run across the entire stack, so the complexity belongs to the composition and this call stays the same size no matter how large the thing above it gets. | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| 7 | To change what contains your work, how much it gets, or where it runs, change configuration. Do not add an argument, and do not write a branch on what answered. | A caller-side branch on the implementation is the boundary leaking, and it is the one change that would make every future swap your problem instead of a configuration change. | sourced | `T-t2-02`, `F-b1-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| 8 | If this page starts to feel like something you must study before running a piece of work, cut it rather than adding to it: the caller-facing surface is the work in, three fields out, and one optional list of destinations. | It cannot be daunting or overly complex, or no one will use it - which makes size a property of the interface to defend, not a documentation problem to solve later. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Set the correlation id yourself and reuse it across every step of the same piece of work, including the failure paths, so the whole run can be found from one value whichever entry point started it. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| Proposed: name the narrowest set of destinations that lets the work finish, and re-read it when the work changes. A `reach` list that grew for a step you removed is a permission nobody is using and nobody will notice. | proposed | `T-t2-02` |
| Proposed: never hand the work a secret. If it needs to call something authenticated, that is a destination to name, not a key to pass; cap-isolation makes the broker rather than the unit the holder of the real credential (F-a3-05, F-a3-07), and a key you pass in is the one thing that survives the containment. | proposed | `F-a3-05`, `F-a3-07` |
| cap-isolation already states the green-gate finding (F-a7-03). What it adds for a caller: an exit status of 0 means the work ran, not that the work was contained and not that the work was right - if you need to know whether the result is acceptable, ask the Judge. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/render_skill.py .claude/skills/cap-isolation-use && python3 tools/validate_skills.py --only cap-isolation-use`. This skill has no Adapters section, so the validator's product-purity check covers the whole page: it proves that nothing a caller reads here - the operations, the worked units, the refusal - names the technology that contains the work, which is the promise this facet makes. |
| Expected | `rendered cap-isolation-use/SKILL.md` then `cap-isolation-use: 0 errors, 0 warnings`, exit 0. |
| Deliberate breakage | In the second worked unit, replace the `reach` entry `artifacts.internal` with the name of the containment technology PASS.md A3 names in its Isolation row, re-render, and re-run the validator. |
| Expected failure | exit 1 with `cap-isolation-use: product name(s) ['<the A3 containment technology>'] outside Adapters, in section 'Contract'` and a closing `cap-isolation-use: 1 errors, 0 warnings`. Measured in session cap-isolation 2831cb4f on 2026-09-03: the breakage produced exactly that line with that technology's name in the list, and exit 1; restoring the file returned 0 errors, 0 warnings and exit 0. |
| Status | measured |
| Evidence | `F-part-c-04`, `T-t2-01` "Composability hides the complexity." |

## Composes with

Builds on: `cap-isolation`, `cap-isolation-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should a caller ever be allowed to name a resource profile, or only the destinations the work must reach? | Count the cases where a composition genuinely cannot proceed without a named envelope rather than without more of something the platform could give it anyway. If every such case is really a duration or a memory ceiling the platform already knows from the agent's profile, no caller-facing profile field is needed. | No profile on the call. A caller states the destinations the work must reach and nothing else; adding a profile field later is cheaper than removing one after callers depend on it. | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-isolation 2831cb4f, 2026-09-03 |
