---
name: cap-consumption
description: The one consumption contract every capability of this platform shares, written from the caller's side: the four entries of TARGET T6.2 - a human, an event, a schedule, an external system or agent - arrive through one envelope, you supply a small fixed field set and read back either one result or one problem object, and the guarantees you never asked for are already applied. Load it before writing any code that calls this platform, before adding an argument, a flag, a retry loop or a branch on which implementation answered, when deciding what to do with a refusal, and when someone asks 'what is the least I have to write to get this to run', 'what comes back', or 'what changes for me when the thing behind this is replaced'. It does not say how a producer's message is normalised into the envelope, which is cap-work-intake, nor what a failure body contains, which is cap-errors: it fixes only what is identical for a caller across every capability, and each capability's own skill carries its call card.
---

# cap-consumption

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| State once what is the same for every caller of this platform, so a capability skill carries only its own call card and no caller has to learn a new way in per capability. | sourced | `T-t6-01`, `T-t2-01` "There is one way to consume the platform, shown as code end to end: what is called, with what, and what comes back." |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-rfc-9457-problem-details` | unverified | unverified | - | `F-b3-13`, `X-cap-errors-001` |
| `E-standard-cloudevents` | unverified | unverified | - | `F-b3-08` |

- `E-standard-rfc-9457-problem-details` version note: The failure half of the caller contract. Cited from the capability row that names the standard and from a search-only record; the RFC text was not fetched from this environment. cap-errors owns this row and its closed type registry; this skill only fixes what a caller does with the object.
- `E-standard-cloudevents` version note: The entry half. The envelope's wire format belongs to cap-work-intake, which owns the intake row; this skill names it only so a caller knows the shape is a published event format rather than a house format, and the version was not verified here.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| submit (proposed) | one entry envelope: which of the four entry kinds you are, the actor and its delegation chain, the intent (what to run and a one-line why), a correlation identifier, a budget ceiling, an idempotency key, and your payload | an acknowledgement carrying the run and correlation identifiers, or one problem object; there is no third kind of answer and no second call to make first (proposed) | proposed | `T-t6-02`, `F-b3-08` |
| read the result (proposed) | what came back from any capability call or any entry | the one field that capability's skill tells you to branch on, plus data you pass on unread; the outcome never says which implementation produced it (proposed) | proposed | `T-t2-02` |
| read a refusal (proposed) | the problem object returned instead of a result | its type member, which is drawn from a closed registry, plus whether it is retryable; the title and detail are for showing a person and never for deciding (proposed) | proposed | `F-b4-07`, `X-cap-errors-002` |

### Shapes (JSON Schema 2020-12)

**entry-envelope (proposed summary shape; the runnable one is examples/end-to-end/schemas/entry.schema.json)** (proposed; sources: `T-t6-02`, `F-b4-01`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:consumption:entry:0.1",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed summary. One shape for all four entries of TARGET T6.2. kind says which entry produced it and nothing downstream branches on it; the five members after it are required because the platform applies those concerns rather than the caller requesting them.",
  "required": [
    "kind",
    "actor",
    "intent",
    "correlation",
    "budget",
    "idempotency_key",
    "payload"
  ],
  "properties": {
    "kind": {
      "enum": [
        "human",
        "event",
        "schedule",
        "external"
      ]
    },
    "actor": {
      "type": "object",
      "description": "subject of the form user:, service:, agent: or schedule:, plus the explicit delegation chain"
    },
    "intent": {
      "type": "object",
      "description": "what to run and a one-line why; never the criterion the result will be judged against"
    },
    "correlation": {
      "type": "object",
      "description": "run and correlation identifiers set by the caller at entry, not inherited from trace parentage"
    },
    "budget": {
      "type": "object",
      "description": "the ceiling this piece of work may spend"
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1
    },
    "payload": {
      "type": "object"
    }
  }
}
```

**answer (proposed summary shape): a result or a problem, never both and never a third kind** (proposed; sources: `F-b4-07`, `X-cap-errors-002`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:consumption:answer:0.1",
  "description": "Proposed. Every capability answers in one of these two shapes. A caller writes one handler for the second and reuses it everywhere.",
  "oneOf": [
    {
      "type": "object",
      "required": [
        "correlation_id"
      ],
      "description": "the capability's own result; its skill names the one field to branch on"
    },
    {
      "type": "object",
      "required": [
        "type",
        "title",
        "status"
      ],
      "description": "problem details: type is a URI from the closed registry, status the code, detail for a person; retryable and correlation_id are extension members this platform adds",
      "properties": {
        "type": {
          "type": "string",
          "pattern": "^urn:agentic:problem:"
        },
        "title": {
          "type": "string"
        },
        "status": {
          "type": "integer"
        },
        "detail": {
          "type": "string"
        },
        "retryable": {
          "type": "boolean"
        },
        "correlation_id": {
          "type": "string"
        }
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Four entries, one shape: a human, an event, a schedule (time), and an external system or agent are the four entries TARGET T6.2 enumerates, and all four enter through the same envelope. Which one produced the work is a value in the envelope, never a different way in. | sourced | `T-t6-02` "All four enter through the same shape." |
| TARGET T1's three ways in - a human, an agent, an internal or external event - are a different enumeration from T6.2's four entries, and a skill must name which one it is citing. This page uses the four entries for the envelope and the three ways in for the question of who may reach the platform at all. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| What a caller supplies is fixed and small: who is acting and on whose behalf, what to run and why, a correlation identifier, a ceiling, a key that makes the submission safe to repeat, and the payload. Those members are required rather than optional because the platform applies identity, correlation, budget and replay safety on the caller's behalf, so there is nothing to configure and nothing to opt into. | sourced | `F-b4-01`, `F-b4-03`, `F-b4-06`, `F-b4-08` "The platform applies each; a caller cannot decline them." |
| Proposed: what a caller reads back is one result or one problem object. There is no third kind of answer, no partially-typed failure and no free-text error, so a caller writes one refusal handler and reuses it against every capability. | proposed | `F-b4-07` |
| A failure is typed and machine-readable and is never parsed from prose: branch on the type member, which is a URI from a closed registry cap-errors owns, and use the retryable member as given. The title and detail exist to show a person. | sourced | `F-b4-07`, `X-cap-errors-002` "Typed and machine-readable. Never parsed from prose" |
| Swapping the thing behind a capability changes nothing a caller wrote: enhancing one aspect of any element leaves the rest untouched, so a new adapter, a new model in a class, a new store or a new runtime arrives as configuration and never as a field, an argument or a branch on which implementation answered. | sourced | `T-t2-02`, `F-b1-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Composability hides the complexity, and here that is a measurable claim: a caller writes no retry loop, no checkpoint table, no correlation propagation, no signing step and no telemetry call, because each of those is applied across the whole structure whichever entry point was used. | sourced | `T-t2-01`, `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| Any entry can call complex workflows, agents and loops that run across the entire stack, so size belongs to the composition above the call and never to the call. A capability call that grows fields to express sequencing, retries or approval has moved the composition inward, which is the failure this contract exists to prevent. | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| Proposed, following the reference example in docs/reference/composable-plan.md: of the four entries, the internal one steers and never starts. A running plan may report a result into work that already exists; it may not mint a root job, so every unit of work traces back to a person, a clock or an outside event. A loop that can start itself has no provenance above it and no ceiling to draw from, which is the constraint any self-improvement loop lives inside. | proposed | `REF-3-4-15`, `REF-3-4-10`, `REF-12-09` "Internal steers but never starts" |
| Proposed, following the same reference: every value the caller did not write resolves from exactly one of three layers, in a precedence that is fixed and total - the caller's override, then the capability's default, then the platform's default - so a caller can always ask where a value came from and get one answer. An override is legal and is logged as non-conformant; a value that two layers could supply at once is a defaulting bug, not a convenience. | proposed | `REF-3-1-01`, `REF-3-2-11`, `REF-12-03` "Precedence is fixed and total: caller override, then capability default, then platform default" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion a result will be judged against. agentic-stack states design rule 6 (F-b1-07); the consequence for the caller contract is that no envelope member, no capability call and no result carries the criterion, and a caller that wants a verdict asks the Judge for one rather than reading a completion. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| Proposed: which implementation answered. No result member names a product, a vendor, an endpoint, a store or a runtime, because a caller that can read it will branch on it and the next swap becomes the caller's problem. | proposed | `T-t2-02` |
| Proposed: the platform's internal bookkeeping - step indices, attempt counters, lease records, span identifiers and checkpoint state. A caller that needs to know where a run got to reads the run's own result, not the machinery that produced it. | proposed | `T-t2-01` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Enter through the entry envelope whichever of the four entries you are, and set kind to say which one. Do not build a second submission path for your own case. | All four enter through the same shape, so a private path is a fifth entry that the cross-cutting concerns are not applied to, and it is the one change that makes every guarantee on this page conditional. | sourced | `T-t6-02` "All four enter through the same shape." |
| 2 | Fill the envelope's required members and stop: actor and delegation chain, intent, correlation identifier, ceiling, idempotency key, payload. Take every default below that. | It has to be simple to use, and each field a caller fills is a decision that caller now owns. Everything the platform defaults it can change under you without breaking your call. | sourced | `T-t3-01` "It has to be simple to use." |
| 3 | Branch on the one field the capability's own skill names, and on nothing else. Read the rest of the result as data to pass on. | Proposed. Each capability names exactly one field for this - a stop reason, a resolved flag, a decision, an outcome - and a branch on any other field is a branch on something the boundary is free to change. | proposed | `T-t2-02` |
| 4 | Handle a refusal once: branch on the problem's type member, use retryable and any retry hint as given, and never match on words, status codes alone, log lines or exit codes. | The failure half of every boundary is typed and machine-readable and never parsed from prose, so one handler written against the type registry covers every capability, and a new failure type added later is a new case rather than a rewrite. | sourced | `F-b4-07`, `X-cap-errors-002` "Typed and machine-readable. Never parsed from prose" |
| 5 | Do not request the cross-cutting guarantees and do not try to decline them: send no telemetry flag, no policy assertion, no signing option, no sampling decision and no 'already approved' field, and delete any you inherited from another system. | The platform applies each and a caller cannot decline them, so such a field is at best ignored and at worst a habit that survives into a system where it would be trusted. | sourced | `F-b4-01`, `F-b1-08` "The platform applies each; a caller cannot decline them." |
| 6 | Compose upward, not inward: one capability call is one step, and retries, sequences, parallel branches, approvals and whole agents are assembled above it rather than added to it as arguments. | Any entry can call complex workflows, agents and loops that run across the entire stack, so the composition layer is where size is allowed to live; a call that grows to express sequencing has taken on work the operators already do. | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |
| 7 | To change what serves a call - the adapter, the store, the runtime, where it runs - change configuration. Do not add an argument, and do not write a branch on which one answered. | Enhancing one aspect of an element must leave the rest untouched; a caller-side branch on the implementation is the boundary leaking, and it turns every future swap into a change the caller has to make. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| 8 | Ask for a model class, never a vendor or a model name, and let one gateway route it. | Callers request a model class rather than a vendor, so a class that moves to a different serving path, a local fleet or a new provider is a routing change and not a caller change. | sourced | `T-t6-04` "callers request a model class, not a vendor" |
| 9 | Pick an agent by what it is declared good at, and sequence it from that declaration rather than from what you have seen it do. | Each agent is defined up front by what it is good at, so callers know how to call it and how to sequence it; choosing by reputation instead re-derives the profile in every caller and goes stale silently. | sourced | `T-t6-05` "Each agent is defined up front by what it is good at, so callers know how to call it and how to sequence it." |
| 10 | Proposed: for the per-capability part - the exact fields, the one field to branch on, the worked call and the worked rejection - open that capability's own skill and its references/usage.md. Read this page once; do not copy it into a capability skill. | Proposed: this page holds only what the consolidation audit measured as identical across capabilities, and keeping the per-capability card in the capability keeps this page from becoming a page every caller must study before calling anything. | proposed | `T-t3-02` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Set the correlation identifier yourself, once per piece of work, and reuse it on every step and every failure path, so the whole run is findable from one value whichever entry point started it. | sourced | `T-t2-03`, `F-b4-06` "Correlation rides on explicit attributes, not trace parentage" |
| Generate the idempotency key when you decide to do the thing, not when you send, and store it with the intent: a key minted at send time is a new key on every retry, which is the one caller-side habit that defeats replay safety. | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| Proposed: measure the size of this contract in what a first successful call requires, and defend that number. It cannot be daunting or overly complex or no one will use it, which makes the caller surface a property to hold down rather than a documentation problem to solve later. | proposed | `T-t3-02` |
| Integrate through the published shapes rather than a client library of ours: agentic-stack states design rule 4 (F-b1-05), and the consequence for a caller is that no single standard covers the agent surface, so a caller that can only reach the platform through our SDK is a boundary drawn where a standard already existed. | sourced | `F-b1-05`, `X-end-to-end-036` "If integration requires our SDK, a boundary is bespoke where a standard existed" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `bash examples/end-to-end/test.sh`, the runnable reference for this contract: it submits all four of TARGET T6.2's entries - human, event, schedule, external - through the one envelope, checks that each reaches a result, that a replayed key appends nothing, that a ceiling below the plan floor refuses before anything runs, and that a malformed envelope is refused as problem details. |
| Expected | `passed 29, failed 0` and exit 0. |
| Deliberate breakage | Delete the required `idempotency_key` member from one entry envelope - `python3 -c "import json;d=json.load(open('examples/end-to-end/entries/human.json'));d.pop('idempotency_key');json.dump(d,open('/tmp/human-nokey.json','w'))"` - and run `python3 examples/end-to-end/run.py --entry /tmp/human-nokey.json`. |
| Expected failure | exit 2 and `PROBLEM (application/problem+json):` carrying `"type": "urn:agentic:problem:document-invalid"`, `"status": 422`, `"detail": "$: missing required property 'idempotency_key'"` and `"retryable": false` - a typed refusal rather than a stack trace, which is what makes the one-answer-or-one-problem rule checkable. Measured in session consolidation-A 2831cb4f on 2026-09-03: the gate printed `passed 29, failed 0` at exit 0, and the breakage produced exactly that problem object at exit 2. |
| Status | measured |
| Evidence | `T-t6-01`, `X-end-to-end-076` "There is one way to consume the platform, shown as code end to end: what is called, with what, and what comes back." |

## Composes with

Builds on: `agentic-stack`

Used by: `build-worked-example`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| This skill ships no adapter pair of its own - where does the pair that proves it live? | 1-3-1 applied (TARGET T5): the three options were to give this skill its own adapters, to defer to the capability skills, or to drop the adapter requirement for it. agentic-stack states design rule 3 (F-b1-04); this skill is not a capability interface with an implementation behind it; it is the contract every capability's pair already has to preserve. The deciding evidence is the conformance runs of those pairs: if any capability's second adapter forces a caller-visible change, this contract is wrong rather than that capability's. | No adapters[] here. Each capability ideal skill carries its own pair and asserts adapters_run >= 2; this skill's own check is the four-entry run above, and the swap evidence is that no adapter row in any capability changes a caller-visible field. | `F-b1-04`, `T-t5-02` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing" |
| Should this skill build on cap-work-intake, which owns the envelope's wire format? | The consolidation plan put this skill at wave 2 and cap-work-intake at wave 3, and the manifest requires a skill to build only on lower waves. The deciding evidence is whether a caller reading this page ever needs the normalising rules: if it does, this skill moves to wave 4 and takes the link; if it does not, the current split is right. | builds_on is agentic-stack alone, and cap-work-intake is named in the description and in the standards note instead of linked. Recorded so the link is not added later without moving the wave. | `F-b3-08` "A2A messaging · CloudEvents" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session consolidation-A 2831cb4f, 2026-09-03 |
