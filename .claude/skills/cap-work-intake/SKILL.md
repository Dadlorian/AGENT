---
name: cap-work-intake
description: The ideal state of the Work intake capability: whatever produced a job - a person, an alert, a clock, another agent - it becomes one canonical envelope before anything downstream sees it, governed by the CloudEvents event format and A2A messaging. Load it when deciding how work gets into the platform, when a new producer wants to submit jobs, when writing or reviewing the code that turns a request into a job, when routing or auditing needs fields the payload does not carry, or when judging whether an intake implementation really normalises. Also load it when a second submission path is being added beside the first, when someone proposes a special endpoint for one caller, when a producer wants to attach a field of its own to every job, or when two ways of asking for the same work behave differently once they are running.
---

# cap-work-intake

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for accepting a job from any producer and turning it into one canonical envelope, so that a producer's transport, format and origin stop being visible the moment work enters, and every entry carries the same identity, correlation, budget and replay fields whichever producer sent it. | sourced | `F-b3-08`, `E-capability-work-intake`, `E-standard-cloudevents`, `E-standard-a2a-messaging` "A2A messaging · CloudEvents" |

## Entities

| Entity |
|---|
| `E-capability-work-intake` |
| `E-standard-cloudevents` |
| `E-standard-a2a-messaging` |
| `E-adapter-http` |
| `E-adapter-cli` |
| `E-adapter-git-event` |
| `E-adapter-schedule` |
| `E-swap-candidate-any-conformant-producer` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-cloudevents` | unverified | unverified | https://cloudevents.io/ | `F-b3-08`, `X-cap-work-intake-001`, `X-cap-work-intake-005` |
| `E-standard-a2a-messaging` | unverified | unverified | https://a2a-protocol.org/latest/ | `F-b3-08`, `X-cap-work-intake-002` |
| `E-standard-openapi-asyncapi` | OpenAPI 3.1.0 (2021-02-17); AsyncAPI 3.0.0, 3.1.0 minor | unverified | - | `F-b1-05`, `X-gap-a-006` |

- `E-standard-cloudevents` version note: the manifest records CloudEvents v1.0.2 for this row; every research record on file for it is search-only and the specification text was not fetched from this environment, so no version string is asserted here
- `E-standard-a2a-messaging` version note: the manifest records A2A protocol v1.0 for this row and notes that the specification text could not be fetched because the domain was egress-blocked; both records on file are search-only, so no version string is asserted here
- `E-standard-openapi-asyncapi` version note: Same proposed entity id as cap-consumption's row (pending registration in kb/entities.jsonl; architecture-layer equivalent is A-standard-openapi-and-asyncapi-descriptions). X-gap-a-006 (search-only, not fetched): "AsyncAPI 3.0.0 is now available and OpenAPI 3.1.0 was released on February 17, 2021. AsyncAPI 3.1.0 is a minor release with no breaking changes". Describes the normalisation contract this skill owns. Row owned by cap-work-intake.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| accept (operation set the recorded standards govern; an event format and a messaging protocol, not a set of calls the core can import as they stand) | one producer-native message plus the transport metadata the adapter observed - a request over HTTP, a command line, a repository hook payload, a fired occurrence, or a message from another agent | either one canonical entry envelope, or a typed problem; intake returns no result and starts no work, so accept is the whole of what a producer can cause directly | sourced | `F-b3-08` "A2A messaging · CloudEvents" |
| normalise | a producer-native message and the name of the format it claims | the canonical envelope fields - kind, actor with delegation chain, intent, correlation, budget ceiling, idempotency key and an opaque payload - with every producer-specific attribute either mapped onto one of them or dropped; a field that can be mapped for one producer and not another is a field the envelope should not have. cap-errors states the same record (T-t6-02) for its own boundary; this row is that rule's consequence for the envelope intake writes | sourced | `F-b3-08`, `T-t6-02` "All four enter through the same shape." |
| job_digest | a canonical envelope | a content digest over the normalised job only - intent and payload - excluding the per-submission identity fields, so that one logical job submitted by three producers yields one digest and three distinct submissions; this is the read that makes producer equivalence checkable rather than asserted, the same uniqueness obligation the governing event standard places on the producer's own source and id | sourced | `F-b3-08`, `X-cap-work-intake-005` "Producers MUST ensure that source + id is unique for each distinct event." |
| admit | a validated canonical envelope | an acknowledgement carrying the entry identifier and the correlation identifier, and nothing about the outcome; the envelope is handed to the ordinary entry path and the producer is free to be gone before anything runs | sourced | `T-t6-03` "Any entry can call complex workflows, agents, and loops that run across the entire stack." |

### Shapes (JSON Schema 2020-12)

**EntryEnvelope (summary shape; its kind enum is TARGET T6.2's four producer classes, the same record cap-errors carries for its own boundary; the full schema, the per-producer mapping table and the fixture corpus are in references/intake-envelope.md)** (sourced; sources: `T-t6-02`, `F-b3-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:envelope:0.1",
  "title": "EntryEnvelope",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "envelope_version",
    "kind",
    "entry_id",
    "occurred_at",
    "actor",
    "intent",
    "correlation",
    "budget",
    "idempotency_key",
    "payload"
  ],
  "properties": {
    "envelope_version": {
      "type": "string",
      "description": "The envelope's own version, so a producer and the platform can disagree about the job and still agree about the shape."
    },
    "kind": {
      "enum": [
        "human",
        "event",
        "schedule",
        "external"
      ],
      "description": "Which producer class submitted this. Recorded for audit and routing; nothing downstream of intake branches on it."
    },
    "entry_id": {
      "type": "string",
      "minLength": 1,
      "description": "Identifies this submission, not the job. Two submissions of one job have two entry_ids."
    },
    "occurred_at": {
      "type": "string",
      "format": "date-time",
      "description": "When the thing happened at the producer, not when intake saw it."
    },
    "actor": {
      "type": "object",
      "description": "Subject plus an explicit delegation chain, oldest hop last. Required on every entry, including one an agent sent."
    },
    "intent": {
      "type": "object",
      "required": [
        "workflow_ref",
        "summary"
      ],
      "description": "What to run and why. Part of the job digest."
    },
    "correlation": {
      "type": "object",
      "required": [
        "run_id",
        "correlation_id"
      ],
      "description": "Explicit correlation attributes set at entry, never inferred from transport parentage."
    },
    "budget": {
      "type": "object",
      "required": [
        "ceiling_micros",
        "currency",
        "on_exceed"
      ],
      "description": "The ceiling this entry runs under. on_exceed is a const, so no producer can opt out."
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1,
      "description": "Derived from the producer's own unique identity for the message, not minted at intake."
    },
    "payload": {
      "type": "object",
      "description": "Opaque to routing, policy and audit. Part of the job digest."
    }
  }
}
```

**IntakeAcknowledgement (the whole of what a producer gets back synchronously)** (sourced; sources: `F-b3-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:ack:0.1",
  "title": "IntakeAcknowledgement",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "entry_id",
    "correlation_id",
    "job_digest",
    "accepted"
  ],
  "properties": {
    "entry_id": {
      "type": "string",
      "minLength": 1
    },
    "correlation_id": {
      "type": "string",
      "minLength": 1,
      "description": "The handle a producer follows to find out what happened, later and by another call."
    },
    "job_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Equal across producers for one logical job; this is what a conformance run compares."
    },
    "accepted": {
      "const": true,
      "description": "A const: a refusal is not an acknowledgement with a false flag, it is a typed problem instead."
    },
    "duplicate_of": {
      "type": "string",
      "description": "Set when this idempotency key was already accepted; the submission is a no-op and this names the first."
    }
  }
}
```

**The failure you handle (proposed): problem details, measured [caller's view, folded from cap-work-intake-use]** (proposed; sources: `F-b3-13`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:example:problem",
  "title": "A refused submission",
  "$ref": "urn:agentic:problem:0.1",
  "description": "cap-errors owns this shape and its registry; intake adds no failure format of its own. Measured in examples/end-to-end on 2026-09-03 by adding a producer-specific field to the event entry: exit code 2, media type application/problem+json, nothing admitted and nothing written.",
  "examples": [
    {
      "type": "urn:agentic:problem:document-invalid",
      "title": "Envelope failed schema validation",
      "status": 422,
      "detail": "$: property 'priority' is not allowed",
      "retryable": false,
      "instance": "entries/event.json"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The recorded row for this capability names A2A messaging and CloudEvents as the standards, a command line, a repository event, an HTTP request and a schedule as the adapters today, and any conformant producer as the swap candidate. | sourced | `F-b3-08`, `E-capability-work-intake`, `E-adapter-http`, `E-swap-candidate-any-conformant-producer` "CLI, git event, HTTP, schedule" |
| The event format is adopted for interoperability rather than for expressiveness: it is a specification for describing event data in common formats to provide interoperability across services, platforms and systems, which is exactly the property a boundary with unknown future producers needs. | sourced | `X-cap-work-intake-001` "to provide interoperability across services, platforms and systems" |
| Uniqueness is the producer's obligation, not intake's guess: producers MUST ensure that source + id is unique for each distinct event. | sourced | `X-cap-work-intake-005` "Producers MUST ensure that source + id is unique for each distinct event." |
| As our consequence of that obligation (proposed): the idempotency key is derived from the producer's own unique identity for the message and never minted at intake, the way the governing event standard already requires producers to ensure that source + id is unique for each distinct event. A key minted on arrival is new on every retry, so the same submission arriving twice becomes two jobs, and the replay guarantee applied above intake has nothing stable to key on. | sourced | `X-cap-work-intake-005`, `F-b4-08` "Producers MUST ensure that source + id is unique for each distinct event." |
| Routing and audit read the envelope, never the body: the standard attributes type, source, subject and time provide essential metadata about the event itself, independent of the payload, which is invaluable for routing, filtering, auditing, and debugging event streams. | sourced | `X-cap-work-intake-003` "independent of the payload, which is invaluable for routing, filtering, auditing, and debugging" |
| Intake is the one shape for TARGET T6.2's four entries - a human, an event, a schedule (time), and an external system or agent - so no producer gets a door of its own, and the cross-cutting fields on the envelope are the reason a fifth producer costs a mapper rather than a new path. cap-errors states the same record (T-t6-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t6-02` "All four enter through the same shape." |
| The agent producer is first-class rather than an integration: the protocol on file exists to enable agents to communicate, collaborate, and delegate tasks securely without human intervention or ad-hoc integration code, and ad-hoc integration code written per producer is precisely the failure this interface is drawn to prevent. | sourced | `X-cap-work-intake-002` "without human intervention or ad-hoc integration code" |
| Proposed: one logical job has one job digest whichever producer submitted it, and each submission has its own entry identifier. Those two facts together are the definition of normalised, and they are what the definition of done below measures; an intake that satisfies only the second has renamed the producers rather than normalised them. Research query: has the equivalence fixture actually been run across all four producers to confirm the job digest is identical regardless of which one submitted, or is normalisation only defined, not yet measured? | proposed | `F-b3-08` |
| Proposed: intake admits, it does not execute. Its output is an envelope and an acknowledgement; planning, dispatch, retry and checkpointing belong to the capabilities that own them. An intake that also runs work cannot be swapped for a mapper, and a producer that gets a result back synchronously has been given a promise the platform cannot keep for a long job. Research query: has an intake implementation that also executes actually been attempted and found unswappable, or is this boundary asserted ahead of any such attempt? | proposed | `T-t6-03` |
| All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach this capability the same way, and enhancing one aspect of it leaves the rest untouched: a new producer, a swapped mapper behind the interface, a changed routing table or an added entry kind changes nothing in code that already fills the envelope, because the envelope is the only thing it was ever asked for. cap-document-validation states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion a result will be judged against never travels in an entry envelope: an agent sees its outcome, never the criterion it is judged against. agentic-stack states design rule 6 (F-b1-07); what this interface forbids (proposed) is a producer putting a definition of done in intent or payload, because intake hands the payload to the graded unit unchanged. At most an opaque criterion handle is carried, and a producer that submits the criterion itself has handed the graded unit its own grader. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |
| Proposed: no transport handle escapes the adapter. A request identifier, a repository ref, a command line, a broker offset, a message identifier minted by another agent's runtime - none appear in the envelope; they are mapped onto entry_id, occurred_at and the idempotency key or they are dropped. Research query: does the CloudEvents mapping guide name transport-native identifiers as explicitly out of scope for the canonical event, or is this exclusion list this repo's own extension of the products-only rule? | proposed | `F-part-c-09` |
| Proposed: intake exposes no outcome. The acknowledgement carries the entry identifier, the correlation identifier and the job digest, and there is no synchronous variant that returns a result, because such a variant would be a second, privileged way in for whoever could hold a connection open. Research query: has a caller actually attempted a synchronous result-returning call against this interface and been refused, or is the 'privileged way in' risk argued rather than observed? | proposed | `T-t6-02` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Fix one canonical envelope first and treat every producer as a mapper into it. Do not carry two first-class intake schemas and translate at the far end. Research query: has an equivalence fixture actually been run across all four producer mappers to confirm one canonical envelope holds, or is the claim argued from the shape of the table alone? | Proposed, and the default recorded for open question 10 below. One canonical shape is what makes producer equivalence checkable at all: with two first-class schemas there is no single digest to compare and no single validator to run. | proposed | `F-b3-08` |
| 2 | Require kind, actor with delegation chain, intent, correlation, budget ceiling, idempotency key and payload on every envelope, and refuse an entry that is missing any of them rather than filling one in downstream. | The platform applies each; a caller cannot decline them - so the fields those concerns need must be present at the moment work enters, not attached later by whichever component first notices they are absent. An envelope completed downstream has a window in which an entry exists with no actor and no ceiling. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them." |
| 3 | Derive the idempotency key from the producer's own unique identity for the message, and record how each adapter derives it in the mapping table rather than leaving it to the adapter's discretion. | Producers MUST ensure that source + id is unique for each distinct event, so the uniqueness the replay guarantee needs already exists upstream; deriving from it makes a retried submission the same request, while minting a key at intake makes every retry a new job. | sourced | `X-cap-work-intake-005`, `F-b4-08` "Producers MUST ensure that source + id is unique for each distinct event." |
| 4 | Validate the normalised envelope against the published envelope schema before anything else touches it, using the platform's one validator rather than a check inside each adapter. | cap-document-validation owns the validation contract and the dialect (F-b3-09); the consequence here is only that validation happens after normalisation and once, so every producer is held to the same shape and an adapter cannot be lenient about a field it finds inconvenient to map. | sourced | `F-b3-09` "any 2020-12 validator" |
| 5 | Route, meter, log and audit on envelope fields only, and treat the payload as opaque from the moment it is accepted. If routing needs something, map it onto an envelope field in the adapter. | The standard attributes are metadata about the event itself, independent of the payload, which is invaluable for routing, filtering, auditing, and debugging event streams. A router that reaches into the payload has to know each producer's body format, which is the coupling normalisation was supposed to remove. | sourced | `X-cap-work-intake-003` "independent of the payload, which is invaluable for routing, filtering, auditing, and debugging" |
| 6 | Return every refusal as a typed problem from the platform's registry, with the offending field named, and never as a transport status alone or a log line the producer cannot see. | cap-errors owns the failure shape and the closed registry (F-b3-13); the consequence here is that intake is the boundary where most producer mistakes surface, so a refusal that does not name the field turns every new producer into an exchange of screenshots. | sourced | `F-b3-13`, `F-b4-07` "— adopt the RFC directly" |
| 7 | Refuse an entry of the internal kind that names no run it is steering: an internal event may steer work that already exists and may never start a root job. Map it onto the run it reports into, or refuse it as a typed problem naming the missing parent. | Proposed, following the reference example in docs/reference/composable-plan.md: only the internal entry is steer-only, so every admitted unit of work traces back to a person, a clock or an outside event. An intake that lets a running plan mint root work has admitted a job with nothing above it to authorise the spend or to answer for it. | proposed | `REF-3-4-15`, `REF-12-09` "A loop that can mint its own root work has no provenance and no ceiling" |
| 8 | Ship the pair recorded for this capability and state the axis: a producer that pushes a formatted event over a request and waits for the acknowledgement, and an autonomous agent that submits a task and is not present for the outcome. Record how the two execution models differ, not merely that there are two. | build-adapter-pair and agentic-stack state design rule 3, that every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing. What is new here is the axis: whether the producer is still there when the job finishes, which is what decides whether the acknowledgement may carry a result. | sourced | `F-b1-04`, `F-b3-08` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing" |
| 9 | Fill the envelope: kind, who is acting and on whose behalf, which workflow and a one-line why, a correlation identifier, a ceiling, a key for this submission, and your body as payload. Send it. Keep the identifier you get back. | It has to be simple to use. What this adds (proposed usage of the contract this skill states, F-b3-08): this is the whole interface; anything else you were going to build - a queue of your own, a retry wrapper, a status poller - is either already here or belongs somewhere else. | sourced | `F-b3-08`, `T-t3-01` "It has to be simple to use." |
| 10 | Open references/intake-envelope.md when you need the full envelope schema, the per-producer mapping table or the equivalence fixture corpus. This skill body is enough to judge an intake implementation without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The mapping table and the fixture corpus are long material, and a reader deciding whether a producer needs a new path does not need them yet. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Name an entry for what happened rather than for what should be done about it: an event represents the fact that something has happened within the system, and an entry named for its remedy freezes today's remedy into an audit trail that will outlive it. | sourced | `X-cap-work-intake-004` "An event represents the fact that something has happened within the system" |
| Treat intake as the routing surface and nothing else: prior art on file describes intake and orchestration systems that act as a system of engagement that route different request types to different systems intelligently, and keeping the decision here while keeping execution elsewhere is what lets a producer be added without touching anything that runs. | sourced | `X-cap-work-intake-006` "act as a system of engagement that route different request types to different systems intelligently" |
| Expect producers you have not met: the boundary is deliberately drawn so that a specification for describing event data in common formats is the only thing a new producer has to satisfy, which is why the swap candidate recorded for this row is any conformant producer rather than a named list. | sourced | `X-cap-work-intake-001`, `F-b3-08`, `E-swap-candidate-any-conformant-producer` "any conformant producer" |
| Proposed: add a producer by writing a mapper and a fixture, never by adding a field to the envelope. A field added for one producer is a field every other producer must now be asked about, and the first such field is how an envelope stops being canonical. Research query: has a fifth producer actually been added by this mapper-and-fixture route, or does the rule rest only on the four producers named in the standards row (F-b3-08)? | proposed | `F-b3-08` |
| Proposed: keep the acknowledgement boring. The producer gets an entry identifier, a correlation identifier and the job digest; anything richer becomes an interface producers depend on, and the richer it is the harder it is to serve from a producer that has already disconnected. Research query: has a richer acknowledgement actually been tried and shown to create a dependency producers then relied on, or is 'boring' argued from the general any-entry-covers-everything finding (T-t6-03) alone? | proposed | `T-t6-03` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-http` | today | A formatted event pushed over a request: the producer builds a CloudEvent and sends it to intake, which normalises, validates and acknowledges within the request. The sibling entities recorded on the same row - a command line, a repository event and a schedule occurrence - are the same execution model with a different trigger, since each builds an event and hands it over in one synchronous hop. | Cannot serve a producer that is gone before the job finishes anything more than an acknowledgement, and cannot originate work itself: something else has to decide to send. It also cannot carry an agent-side task lifecycle, because the request ends at the acknowledgement and there is nothing left to attach a later state to. | Keep the canonical envelope still and move only who builds it. cap-work-intake-implement owns the migration steps and the per-producer mapping; this row records the roles PASS.md B3 fixes and the axis the pair differs on. | claimed | `F-b3-08`, `E-adapter-http`, `E-adapter-cli`, `E-adapter-git-event`, `E-adapter-schedule` "CLI, git event, HTTP, schedule" |
| `E-swap-candidate-any-conformant-producer` | second | An autonomous agent submitting a task through the agent messaging protocol, mapped into the same envelope: the agent sends a message, receives an identifier, and follows the job later through correlation rather than through the submitting call. The recorded swap candidate for this row is any conformant producer, and this is the member of that set that breaks a different assumption than the first. | Cannot rely on being present for the outcome, cannot be given a synchronous result, and cannot assume a human will read a refusal - which is why every refusal has to be typed rather than prose. That is the axis: the first adapter's producer holds the submission open and is available to be told what happened, while the second's producer submits and detaches, so an envelope both can produce cannot have been shaped around either one's liveness. | Select the producer adapter by configuration only, with no code edit between runs, and run the identical equivalence fixture through each; the merged report must show adapters_run >= 2 and one job digest across producers. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is that the swap test and the normalisation test are the same run, because equivalence is the only property intake has. | claimed | `F-b3-08`, `F-b1-04`, `E-swap-candidate-any-conformant-producer` "any conformant producer" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/conformance/intake_equivalence.py --producer cloudevents-http --producer a2a-message --producer schedule-occurrence --job fixtures/intake/one-job.json --report out/intake.json |
| Expected | docs/decomposition.md section 3.2 row P7, made precise and run over the adapter pair above: that command (proposed tool, built with the first producer adapter), the producer selected by configuration with no code edit between runs. It submits one logical job three ways and asserts `distinct_job_digests == 1` over the three resulting envelopes, `distinct_entry_ids == 3`, every envelope valid against the published envelope schema, and `adapters_run >= 2` across the request-pushed producer and the agent-message producer. exit 0 with `distinct_job_digests: 1`, `distinct_entry_ids: 3`, `invalid: 0` and `adapters_run: 2` |
| Deliberate breakage | Let the request-pushed intake path stamp a default `priority` field onto the envelope it builds, changing nothing else, and re-run the same command. |
| Expected failure | exit 1 with `distinct_job_digests == 2`: the envelope from the request-pushed producer no longer digests to the same value as the other two, so the equality assertion fails while `distinct_entry_ids` is still 3, which is the useful part - the failure is normalisation, not identity. Claimed: the fixture, the producers and the runner do not exist here and neither run has been performed, so this check starts red by construction. |
| Status | claimed |
| Evidence | `F-b3-08`, `F-b1-04` "any conformant producer" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-document-validation`, `cap-errors`

Used by: `build-entry-conformance`, `cap-human-interaction`, `cap-work-intake-implement`, `compose-approval`, `xc-enforcement-chain`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does work intake keep both recorded standards as first-class intake schemas, or one canonical envelope with translators? | docs/decomposition.md open question 10: implement the agent-protocol-to-event-format translator and measure whether any field of the agent protocol is lossy, in particular its conversation-grouping identifier and any task-state field with no equivalent in the event format. Lossless means one canonical envelope. | One canonical envelope, with the agent messaging protocol as a producer that maps into it, both recorded with version unverified. One canonical shape is what makes the digest-equality check in the definition of done possible at all; two first-class schemas leave nothing to compare. | `F-b3-08` "A2A messaging · CloudEvents" |
| Is a fired schedule occurrence a producer of intake, or a capability that reaches the platform its own way? | Whether any declared recurring unit needs a field the envelope does not carry, and whether an occurrence can be replayed on the same key as a manual re-run of the same unit; if both answers are no, the occurrence is one producer among several. | One producer among several. The manifest note for this row records that scheduling and replay safety look like dependencies of intake and are not: a schedule is one producer, and the replay lease is applied above intake rather than built into the envelope. | `F-b3-08`, `E-adapter-schedule` "CLI, git event, HTTP, schedule" |
| What exactly does the job digest cover, given it must be equal across producers while each submission stays distinct? | Take the fixture corpus and compute the digest over successively larger field sets; the largest set that still yields one digest across all three producers for one logical job is the answer, and any field that has to be excluded is a field the envelope carries for identity rather than for meaning. | Proposed: intent plus payload, excluding entry_id, occurred_at, actor, correlation and the idempotency key. That is the smallest set that makes the definition of done meaningful, and every exclusion is recorded rather than inferred from what happened to pass. | `F-b3-08` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-work-intake 2831cb4f, 2026-09-03 |
