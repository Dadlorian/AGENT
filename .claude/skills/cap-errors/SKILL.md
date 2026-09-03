---
name: cap-errors
description: The ideal state of the Errors capability: one typed, machine-readable failure object for every boundary in the platform, governed by RFC 9457 problem details and a closed registry of problem types. Load it when deciding what a failure returns, when adding a failure mode or a new type URI, when judging whether an implementation's failure paths are conformant, or when a review asks why an error carries the fields it does. Also load it when a component is about to define its own error object, when a caller would have to read a message to learn what went wrong, when a status code alone is being used to decide whether to retry, or when someone proposes handing a stack trace, a log line or free text back to whoever called.
---

# cap-errors

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Give every failure in the platform one typed, machine-readable shape so no caller ever parses prose, by adopting the standard named for this capability whole instead of designing an error object of our own. | sourced | `F-b4-07`, `F-b3-13`, `E-concern-errors`, `E-capability-errors` "Typed and machine-readable. Never parsed from prose" |

## Entities

| Entity |
|---|
| `E-capability-errors` |
| `E-concern-errors` |
| `E-standard-rfc-9457-problem-details` |
| `E-adapter-errors-absent` |
| `E-not-running-typed-errors` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-rfc-9457-problem-details` | RFC 9457 (a search-only research record dates it July 2023 and says it obsoletes RFC 7807; the specification was not fetched from this environment) | unverified | https://www.rfc-editor.org/info/rfc9457/ | `F-b3-13`, `X-cross-structure-039`, `X-cap-errors-001`, `X-cap-errors-005` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| raise (proposed operation set; PASS.md names the standard, not the calls) | a registered type suffix, a detail string written for the caller, and the extension members that type declares | a Problem value carrying type, title, status, detail and those extensions; construction fails when the suffix has no row in the closed registry | proposed | `F-b3-13` |
| render (proposed) | a Problem value and the transport it leaves through | the problem-details JSON object plus the media type application/problem+json; the same object serialises for a stdio, message or HTTP seam, so the shape does not oblige a transport | proposed | `X-cap-errors-002` |
| classify (proposed) | any failure raised beneath a capability adapter, including one the adapter did not type | a registered Problem, or adapter-unavailable carrying the untyped payload in detail and incrementing the adapter's untyped counter | proposed | - |
| retry_advice (proposed) | a Problem value | the explicit retryable boolean and the optional retry_after_s, read from the members and never inferred from the status code | proposed | `X-cap-errors-004` |
| chain (proposed) | an outer Problem and the inner Problem that caused it | the outer Problem with the inner appended to causes, innermost last, so a delegated failure keeps its origin instead of being flattened into a sentence | proposed | - |

### Shapes (JSON Schema 2020-12)

**Problem (proposed shape, from docs/decomposition.md section 2.1.6; the full schema and the closed type registry are in references/problem-registry.md)** (proposed; sources: `X-cap-errors-002`, `X-cross-structure-040`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:0.1",
  "title": "Problem",
  "type": "object",
  "required": [
    "type",
    "title",
    "status"
  ],
  "properties": {
    "type": {
      "type": "string",
      "format": "uri",
      "description": "urn:agentic:problem:<suffix>. The suffix must have a row in the closed registry; an unregistered value is a conformance failure."
    },
    "title": {
      "type": "string"
    },
    "status": {
      "type": "integer",
      "minimum": 100,
      "maximum": 599
    },
    "detail": {
      "type": "string",
      "description": "Written so the caller can act. Never a stack trace, and never the criterion a result is judged against."
    },
    "instance": {
      "type": "string",
      "format": "uri"
    },
    "retryable": {
      "type": "boolean",
      "description": "Explicit. The platform profile emits it on every problem even though the standard keeps its members optional."
    },
    "retry_after_s": {
      "type": "integer",
      "minimum": 0
    },
    "correlation_id": {
      "type": "string"
    },
    "causes": {
      "type": "array",
      "items": {
        "$ref": "urn:agentic:problem:0.1"
      },
      "description": "Delegated failure chain, innermost last."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every failure the platform returns is typed and machine-readable; a caller branches on the type member and never on the words in the message. | sourced | `F-b4-07`, `E-concern-errors` "Typed and machine-readable. Never parsed from prose" |
| The governing standard is RFC 9457 problem details and the recorded instruction for this capability is to adopt the RFC directly, so there is no bespoke error object to design here. agentic-stack states design rule 2 (F-b1-03); this row is only its application to Errors. | sourced | `F-b3-13`, `F-b1-03`, `E-standard-rfc-9457-problem-details` "— adopt the RFC directly" |
| The starting point is nothing rather than something: what runs today records Typed errors as Absent, so this capability is adopted, not migrated. | sourced | `F-a6-06`, `E-not-running-typed-errors`, `E-adapter-errors-absent` "Typed errors \| Absent" |
| Proposed (from docs/decomposition.md section 2.1.6): every failure body of every seam and every adapter carries the media type application/problem+json, whatever transport it leaves through, and the members are the standard five with declared extensions. | proposed | `X-cap-errors-002` |
| Proposed: the type member must resolve to a row in the closed registry in docs/decomposition.md section 2.1.6. An unregistered type URI is a conformance failure, and extending the set means adding a row there before any code emits it. | proposed | `X-cap-errors-003` |
| Proposed: retryable is a member, never an inference from the status code, so a 503 that must not be retried says so. The base problem schema keeps all standard members optional, which is why the platform profile is what requires it on emission rather than the standard. | proposed | `X-cross-structure-040` |
| Proposed: a failure that cannot be typed is itself a conformance failure of the adapter that raised it. It is returned as adapter-unavailable with the untyped payload in detail and it is counted; an adapter whose untyped count is non-zero is not conformant, however green its own tests are. | proposed | - |
| Proposed consequence of design rule 6, which agentic-stack states under F-b1-07: a problem body is caller-visible, so the criterion a result is judged against must never appear in detail, in causes, or in any extension member. | proposed | `F-b1-07` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: stack traces, internal hostnames, credentials and adapter identities stay out of the problem body. agentic-stack states the products-in-adapters-only rule (F-part-c-09); the consequence here is that a caller cannot tell which implementation failed from the failure it receives. | proposed | `F-part-c-09` |
| Proposed: the criterion the Judge grades against is not exposed through the failure path, which is the one path most likely to leak it while explaining why something did not pass. | proposed | `F-b1-07` |
| Proposed: the transport is not part of the contract. The shape and its media type are adopted; the HTTP binding is not required for this object to be the failure shape of a stdio or message-based seam. | proposed | `X-cap-errors-002` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Take the member set and the media type of the standard as given and design nothing: the recorded instruction for this capability is to adopt the RFC directly. | The swap-candidate column for Errors is not a list of alternatives; it is the instruction. An original error object here would be original design where a published decision already exists. | sourced | `F-b3-13` "— adopt the RFC directly" |
| 2 | Define the failure object as the five standard members and treat everything else as an extension member: type identifying the error category, title, status, detail, instance identifying the specific request. | A response uses the application/problem+json content type and includes fields: type (URI identifying the error category), title (short human-readable summary), status (HTTP status code), detail (specific explanation), and instance (URI identifying the specific request). | sourced | `X-cap-errors-002` "uses the application/problem+json content type and includes fields: type (URI identifying the error category), title (short human-readable summary), status (HTTP status code), detail (specific explanation), and instance (URI identifying the specific request)" |
| 3 | Proposed: register the platform's own problem-type namespace as urn:agentic:problem:<suffix> and keep it a closed registry, each row fixing the suffix, the status, whether it is retryable and when it is raised. Add a row to docs/decomposition.md section 2.1.6 before any code emits a new suffix. When a failure mode has no row in that registry, apply 1-3-1 rather than minting a suffix at the call site: state the problem, list the three best registry changes, follow the recommendation, and record it as an open question with the row you would add. | Proposed, from docs/decomposition.md section 2.1.6. The standard's own registry promotes reuse of widely used problem types and requires Specification Required registration for new entries, and a namespace that anyone may extend at the call site is not a registry. The same act governs the missing row: applying the operating protocol, when a problem comes up, use 1-3-1: define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation. | proposed | `X-cap-errors-003`, `T-t5-02` |
| 4 | Declare, per problem type, the extension members a client should expect to parse, and put the declaration next to the registry row rather than inferring it from whatever a handler happened to attach. | The specification makes a clearer association between problem types and the additional fields that a client should expect to parse, which is what makes an extension member usable by a machine rather than by a reader. | sourced | `X-cap-errors-007`, `X-cross-structure-040` "The specification makes a clearer association between problem types and the additional fields that a client should expect to parse." |
| 5 | Proposed: emit retryable on every problem, and pair it with retry_after_s where the wait is knowable, instead of leaving a caller to read the status code. | Proposed platform profile. Best practice for this standard is to include Retry-After on 429 and 503 responses, and a boolean alone cannot carry the rate-limited case; the status code alone cannot distinguish a 503 that will clear from one that will not. | proposed | `X-cap-errors-004` |
| 6 | Return all validation errors at once with field-level detail, in one problem, rather than one problem per offending field. | Return all validation errors at once with field-level detail; a caller that has to resubmit once per field learns the shape of its own mistake one round trip at a time. | sourced | `X-cap-errors-004` "return all validation errors at once with field-level detail" |
| 7 | Proposed: treat an untyped failure as a defect of the adapter that raised it. Map it to adapter-unavailable, carry the untyped payload in detail, count it, and judge an implementation conformant only when that count is zero. | Proposed, from docs/decomposition.md section 2.1.6. Without the counter, the adapters that never learned to type their failures are exactly the ones a conformance run cannot see, because they answer with something rather than nothing. | proposed | - |
| 8 | Proposed: keep the object bound to its media type and not to HTTP, so a stdio, message or in-process seam returns the identical body and a caller writes one branch for all of them. | Proposed, from docs/decomposition.md section 1. The standard defines a media type and a member set; nothing forces the transport to be HTTP for the shape to be adopted, and binding it to one transport would make the failure path the only part of a seam that cannot be swapped. | proposed | `X-cap-errors-002` |
| 9 | Proposed: before declaring an implementation done, grep every problem body it can emit for the text of the criterion the result is judged against, and treat a hit as a rule-6 breach rather than a wording problem. | Proposed check. agentic-stack states design rule 6 under F-b1-07; the consequence specific to this capability is that the failure path is the path most tempted to explain why something did not pass. | proposed | `F-b1-07` |
| 10 | Proposed: open references/problem-registry.md when you need the full JSON Schema, the closed type registry with its statuses and retryability, or the declared extension members per type. This skill body is enough to judge an implementation without it. | Proposed, progressive disclosure. The full schema and a ten-row registry are long material; inlining them would make the contract harder to read than the thing it governs. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Write detail for the person who has to fix it: the detail field should help developers fix the problem without contacting support. A detail that only names the failure repeats the type member. | sourced | `X-cap-errors-004` "The detail field should help developers fix the problem without contacting support." |
| Prefer a widely used registered problem type to a locally minted one: the standard's registry promotes reuse of widely used problem types and requires Specification Required registration for new entries, so a private suffix is a cost paid by every client that has to learn it. | sourced | `X-cap-errors-003` "The registry promotes reuse of widely used problem types and requires Specification Required registration for new entries." |
| The reason to adopt rather than invent is stated by the standard itself: it exists to carry machine-readable details of errors in HTTP response content, avoiding the need to define new error response formats. Every bespoke error object is one more format a client must learn. | sourced | `X-cap-errors-001` "to carry machine-readable details of errors in HTTP response content" |
| Proposed: copy the correlation identifier onto the problem body, not only into the log line. Structured logs should include correlation IDs for error tracking, and agentic-stack states the correlation finding (F-a7-02); what this adds is that the failure a caller holds is often the only artifact that survives the boundary. | proposed | `X-cap-errors-006`, `F-a7-02` |
| Cite the current RFC, not the one a library's documentation names: RFC 7807 has been succeeded by RFC 9457, so a dependency that still speaks of 7807 is describing an older member set than the one this contract adopts. | sourced | `X-cap-errors-005`, `X-cross-structure-039` "RFC 7807 has been succeeded by RFC 9457" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P12, made precise: `python3 tools/conformance/errors_fuzz.py --adapters all --iterations 250 --report out/errors.json` (proposed tool, built with the first Errors adapter). It fuzzes every adapter's failure paths and asserts that every failure response carries the media type application/problem+json, that every type value has a row in the registry in docs/decomposition.md section 2.1.6, that `responses_checked > 200`, and that `untyped == 0`. |
| Expected | exit 0 with `responses_checked > 200`, `untyped == 0`, `unregistered_types == 0`, `adapters_run >= 2` |
| Deliberate breakage | Have one adapter return a plain-text HTTP 500 on one failure path, leaving every other adapter untouched. |
| Expected failure | exit 1 with `untyped == 1`, the report naming the adapter and the path, while the other adapters still report zero. Claimed: typed errors are absent today and the fuzz tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-b4-07`, `F-a6-06` "Typed and machine-readable. Never parsed from prose" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-adapter-pair`, `build-skill-authoring`

Used by: `cap-agent-runtime`, `cap-capability-packaging`, `cap-capability-registry`, `cap-durable-execution`, `cap-errors-implement`, `cap-errors-use`, `cap-evaluation`, `cap-human-interaction`, `cap-idempotency`, `cap-identity`, `cap-isolation`, `cap-mandate-broker`, `cap-memory`, `cap-model-access`, `cap-policy`, `cap-provenance`, `cap-scheduling`, `cap-state-persistence`, `cap-telemetry`, `cap-tool-access`, `cap-work-intake`, `core-document`, `core-graph`, `core-judge`, `core-ledger`, `seam-agent-ingress`, `seam-dispatch`, `seam-entry-envelope`, `seam-state`, `xc-budget`, `xc-policy-gate`, `xc-typed-errors`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Do problem details need a structured retry policy or a boolean? (docs/decomposition.md section 5 question 9) | Across the run history, count how many distinct failure types actually differ in the retry behaviour a caller should adopt. If the answer is two or three, a policy object is over-modelled. | The boolean plus retry_after_s, as in this skill's Problem shape. It is one optional member and it covers the rate-limited case that a boolean alone cannot. | `X-cap-errors-004` "Include Retry-After on 429 and 503 responses" |
| Whose spelling of the type suffixes is normative? The manifest's fold-in names budget-exceeded, cancelled, timeout, schema-invalid and partial-result, while the closed registry in docs/decomposition.md section 2.1.6 spells the same concerns budget-exhausted, cancel-timeout, deadline-exceeded and document-invalid, and has no partial-result row at all. | An edit to docs/decomposition.md section 2.1.6 that renames or adds the rows, which is the only sanctioned way to change a closed registry. Until that edit exists, the two lists are the same set of concerns under different names. | 1-3-1 applied and recorded on 2026-09-03. Options considered: (a) rename the registry to the manifest's words; (b) keep the registry's words and read the manifest's list as the same concerns; (c) carry both as aliases. Recommendation and default: (b). The registry is closed and renaming it without the row edit is the move the note itself forbids, aliases would let two spellings of one type reach clients, and partial-result is not a failure at all because a partial result returns through the result shape rather than through a problem body. | `T-t5-02`, `X-cap-errors-003` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |
| Where does the adapter pair for this capability live, given that Errors has no incumbent implementation to pair against? | Whether a reviewer reading only this skill can name both adapters and the axis on which they differ; if not, the pair belongs here as well as in the implement facet. | The pair, its execution-model difference and the swap procedure are recorded once in cap-errors-implement, which builds on build-adapter-pair, rather than being restated here. This skill states only that the pair is owed. | `F-b1-04` "Every interface ships with at least two adapters" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-errors 2831cb4f, 2026-09-03 |
