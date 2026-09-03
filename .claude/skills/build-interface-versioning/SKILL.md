---
name: "build-interface-versioning"
description: "The discipline of versioning a capability interface: every call declares the interface version it speaks, an unsupported version is refused on that call rather than agreed once at connect time, a core field set is frozen as never-changing, and every deprecation carries a stated window. Load it when adding, renaming or removing a field, operation or error on an interface the core imports; when deciding whether a change is breaking; when an adapter and the core disagree about which revision they speak; when one part of a contract (an attribute mapping, a payload profile) needs to move faster than the transport that carries it; or when writing the refusal a caller gets for a revision no longer served. Also load it when someone proposes one version number for the whole platform, when an extension point is about to be treated as an internal detail, or when a change is called additive and therefore safe."
---

# build-interface-versioning

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make an interface changeable without breaking what is already built on it, so that enhancing one aspect of an element does not touch the rest: an extension point is a public API, and once implementations exist, changing it breaks them. | sourced | `T-t2-02`, `X-cross-structure-060` "Composability allows enhancing particular aspects of any element without touching the rest." |

## Entities

| Entity |
|---|
| `E-rule-b1-1` |
| `E-rule-b1-7` |
| `E-standard-model-context-protocol` |
| `E-standard-otlp` |
| `E-standard-genai-semantic-conventions` |
| `E-standard-json-schema-2020-12` |
| `E-capability-telemetry` |
| `E-finding-a7-2` |
| `E-finding-a7-3` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-model-context-protocol` | revision 2026-07-28 | unverified | https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning | `X-cross-structure-061` |
| `E-standard-otlp` | unverified | unverified | - | `F-b3-10`, `X-cross-structure-012` |
| `E-standard-genai-semantic-conventions` | unverified | unverified | - | `F-b3-10` |
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | - | `F-b3-09` |

- `E-standard-model-context-protocol` version note: revision 2026-07-28 - cited as a pattern for per-call version declaration and a bounded deprecation window, not as a standard that governs this discipline
- `E-standard-otlp` version note: unverified - the stable transport half of the telemetry split, pinned while the attribute mapping moves
- `E-standard-genai-semantic-conventions` version note: unverified - the separately versioned attribute mapping half of the telemetry split; the version each run emitted against is recorded

### Shapes (JSON Schema 2020-12)

**interface_version_declaration (proposed shape; ours, not given by PASS.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "interface_version_declaration",
  "description": "Carried by every call crossing a capability interface. Present per call; a session-level agreement does not satisfy it.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "interface",
    "version"
  ],
  "properties": {
    "interface": {
      "type": "string",
      "minLength": 1,
      "description": "Capability interface id. Never an adapter id, a product name or a hostname."
    },
    "version": {
      "type": "string",
      "minLength": 1,
      "description": "The interface revision this call speaks."
    },
    "frozen_core_fields_digest": {
      "type": "string",
      "description": "Optional digest of the frozen core field set the caller was built against, so a drifted core set is detectable at the call rather than at the next incident."
    }
  }
}
```

**interface_version_policy (proposed shape; summary - the per-member deprecation entry is in references/versioning-policy.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "interface_version_policy",
  "description": "One per capability interface. Published, machine-readable, and the input to the version check.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "interface",
    "supported",
    "frozen_core_fields",
    "deprecation_window_months"
  ],
  "properties": {
    "interface": {
      "type": "string",
      "minLength": 1
    },
    "supported": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      },
      "description": "Every version this interface will admit on a call. Anything else is refused."
    },
    "frozen_core_fields": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      },
      "description": "Field names that must not ever change. Append-only: removal or rename fails the check."
    },
    "deprecation_window_months": {
      "type": "integer",
      "minimum": 12,
      "description": "How long a deprecated member keeps being served after it is marked."
    },
    "deprecated": {
      "type": "array",
      "description": "Deprecated members with their dates; entry shape in references/versioning-policy.md.",
      "items": {
        "type": "object"
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The pattern this discipline copies declares the version per request rather than negotiating it once per session, so what was agreed at connect time is not evidence of what a later call speaks. | sourced | `X-cross-structure-061` "the version is declared per request instead of negotiated once per session" |
| every call crossing a capability interface carries an interface_version_declaration conforming to the shape in this skill's Shapes section; a declaration made once for a session, a connection or a deployment does not satisfy it. | sourced | `X-cross-structure-061` "the version is declared per request instead of negotiated once per session" |
| An extension point is a public API: once implementations are built against an interface, changing it breaks them, so the freedom to enhance one aspect is paid for with a version discipline or with breakage. | sourced | `X-cross-structure-060` "your plugin interface is a public API, and once plugins are built against it, changing it breaks those plugins" |
| The frozen-field model is taken from a specification that hardcodes part of its own attribute set: those attributes are declared unchangeable rather than versioned. | sourced | `X-cross-structure-012` "These resource attributes MUST NOT be ever changed and are considered a hardcoded part of the specification." |
| every interface publishes a frozen core field set in its interface_version_policy. Membership is append-only - a field may be added, never removed or renamed - and a removal fails the check rather than earning a version bump. | sourced | `X-cross-structure-012` "MUST NOT be ever changed and are considered a hardcoded part of the specification" |
| The deprecation windows in both policies cited here are bounded and counted in months rather than left open: one keeps deprecated features for at least twelve months, the other keeps stable APIs available for at least 12 months or three minor releases after deprecation. | sourced | `X-cross-structure-061`, `X-build-interface-versioning-002` "Deprecated features remain in the specification for at least twelve months." |
| A version number is not by itself the contract: the convention was designed for libraries, and a change can be additive at the wire level while still being semantically significant to one consumer and invisible to another. | sourced | `X-build-interface-versioning-006` "SemVer was designed for libraries, but an API contract is different" |
| Proposed: the interface version belongs to the capability, never to whatever implements it. agentic-stack already states design rule 1 (F-b1-02); the consequence here is that an adapter's own release number is never offered as the declared interface version, and swapping adapters does not move it. Research query: unresearched beyond design rule 1 (F-b1-02); no prior-art search has been run for the adapter-release-number-is-never-the-declared-version consequence specifically. | proposed | `F-b1-02`, `E-rule-b1-1` |
| no interface version exists in which a cross-cutting guarantee is optional: a version bump may add or narrow fields but may not be the mechanism by which telemetry, policy, provenance or budget stops applying. | sourced | `F-b1-08`, `E-rule-b1-7` "Cross-cutting guarantees are not optional." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Before assigning any version, name the capability and the standard that governs it, then express the interface version as the profile of that standard we speak - not as a numbering scheme of our own. | Proposed consequence of design rule 2, which build-skill-authoring states (F-b1-03): a private version number over a standard boundary re-introduces the bespoke shape the standard was adopted to avoid. | sourced | `F-b1-03` "Where a standard exists, adopt it whole rather than modelling our own shape." |
| 2 | Publish one interface_version_policy per interface, conforming to the shape in this skill: the supported set, the frozen core field set, and the deprecation window in months. Store it where the check reads it, not in prose. Research query: unresearched; our own design, no prior-art search has been run for a per-interface published version-policy file (supported set, frozen core, deprecation window) as a distinct artifact from prose documentation. | Proposed: a policy that lives only in a document cannot be enforced on a call, and the check in this skill's definition of done takes this file as its input. | proposed | - |
| 3 | Make each call declare the interface version it speaks, and treat a session-level or deployment-level agreement as insufficient. | The pattern cited here moved version declaration from once per session to per request, so a long-lived session cannot go on speaking a revision the interface has stopped serving. | sourced | `X-cross-structure-061` "the version is declared per request instead of negotiated once per session" |
| 4 | Refuse a declared version outside the supported set on that call, with a typed refusal that names every supported version, and never fall back to a default revision. Research query: unresearched beyond the extension-point contract-stability finding (X-cross-structure-060); no prior-art search has been run for a per-call (rather than per-connection) version refusal specifically. | Proposed: an interface is a public API to everything built against it, so a silent downgrade converts a caller's stale assumption into wrong behaviour deeper in the run instead of an answer the caller can act on. | proposed | `X-cross-structure-060` |
| 5 | Choose the smallest field set the interface cannot function without, list it as the frozen core, and document it as never-changing rather than as versioned. | The specification cited here does exactly this with part of its attribute set, hardcoding it instead of versioning it, which gives every consumer a surface that no revision can move under them. | sourced | `X-cross-structure-012` "These resource attributes MUST NOT be ever changed and are considered a hardcoded part of the specification." |
| 6 | State the deprecation window in months per interface, and compute the earliest removal date from the date the member was marked deprecated rather than deciding it when someone wants the code gone. | Both policies cited here bound the window rather than leaving it open, keeping stable members available for at least 12 months or three minor releases after deprecation. | sourced | `X-build-interface-versioning-002`, `X-cross-structure-061` "Stable APIs must remain available for at least 12 months or three minor releases after deprecation before removal." |
| 7 | Classify every proposed change by its effect on a consumer, not by its shape on the wire, and record the classification with the change. Do not treat an added optional field as automatically safe. | A change can be additive at the wire level while still being semantically significant to one consumer and invisible to another, so the wire shape does not settle whether the change is breaking. | sourced | `X-build-interface-versioning-006` "a change can be additive at the wire level while still being semantically significant to one consumer and invisible to another" |
| 8 | When one half of a contract must move faster than the other, split it and version the halves separately: pin the stable transport contract, version the attribute or payload mapping on its own cadence, and record with each run the mapping version it was emitted against. Research query: unresearched; our own design, no prior-art search has been run for splitting a transport contract from an attribute/payload mapping into separately versioned halves. | Proposed, and the first application is the telemetry interface, whose governing row names a transport and a separate attribute mapping side by side; freezing both together would either stall the mapping or churn the transport. | proposed | `F-b3-10`, `E-capability-telemetry` |
| 9 | Carry the version in a metadata field or header rather than in the identity of the thing being addressed, so an id or a path does not change every revision. | Proposed: the header-and-media-type approach is described in the research as the most-correct way of versioning an API, and it keeps the frozen core field set - which is about identity - independent of the revision counter. | sourced | `X-build-interface-versioning-004` "the most-correct way of versioning your API" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: the green-gate finding is stated in the agentic-stack root contract (F-a7-03) and is not restated here. Its consequence for this discipline is to count the refusals a version check actually produced: a suite that never presents an unsupported declaration has proved that supported calls pass and nothing else. Research query: unresearched beyond the green-gate finding (F-a7-03); no prior-art search has been run for counting refusals produced by a version check specifically. | proposed | `F-a7-03`, `E-finding-a7-2` |
| Proposed: build-definition-of-done already carries the runtime-effect finding (F-a7-04). Its consequence here is to read the supported set the running interface enforces on a call, rather than the policy file that declares it, before believing a version has been retired. Research query: unresearched beyond the runtime-effect finding (F-a7-04); no prior-art search has been run for reading a running interface's enforced supported set versus its declared policy file specifically. | proposed | `F-a7-04`, `E-finding-a7-3` |
| To make a breaking change without breaking existing callers, publish multiple versions side by side under distinct namespaces rather than mutating one in place. | sourced | `X-build-interface-versioning-003` "A way to maintain backwards compatibility while making breaking changes is to publish multiple versions of a service." |
| Where the version rides in a header and a media type rather than in the path, the resource keeps one identity across revisions; the research on file calls this the most-correct way of versioning an API. | sourced | `X-build-interface-versioning-004` "Using the Accept and Content-Type header attributes with a custom vendor specific MIME type is the most-correct way of versioning your API." |
| Assume a stated versioning policy is not the practice until a call shows otherwise: on the numbers on file, only 26% of teams actually implement the convention that is recommended nearly everywhere. | sourced | `X-build-interface-versioning-006` "only 26% of teams actually implement it" |
| Proposed: put the correlation attribute that dispatch sets into the frozen core field set. agentic-stack states the boundary finding (F-a7-02); the consequence here is that the one attribute correlation depends on must be in the set no revision can move, since a run that loses it cannot be reassembled after the fact. Research query: unresearched beyond the correlation boundary finding (F-a7-02) and the resource-attribute stability precedent (X-cross-structure-012); no prior-art search has been run for putting a correlation id specifically inside a frozen core field set. | proposed | `F-a7-02`, `X-cross-structure-012` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/check_interface_versions.py --skills .claude/skills --policies kb/interface-versions/ Gap: kb/interface-versions/ has no policy on file, so this cannot run yet (STATUS row 59). |
| Expected | check_interface_versions.py is a proposed tool, built with the first cap- skill that publishes a policy. For every interface with an interface_version_policy it asserts: the policy conforms to the shape in this skill; deprecation_window_months >= 12; every frozen core field present in the previous committed policy is still present; and, replaying one fixture call per adapter, a declaration outside supported produces a typed refusal that names the supported set. exit 0 with `interfaces_checked > 0`, `unsupported_admitted == 0`, `frozen_field_removals == 0`, `refusals_observed == interfaces_checked` |
| Deliberate breakage | Two runs. (a) Add a fixture adapter that declares interface version `0.0.0-unsupported` on one call and leave the interface admitting it. (b) Restore that, then delete one field name from a frozen_core_fields list in a committed policy and re-run. |
| Expected failure | Run (a) exits 1 with `unsupported_admitted == 1`, naming the interface, the declared version and the supported set that should have been quoted back. Run (b) exits 1 with `frozen_field_removals == 1`, naming the interface and the removed field, and does not offer a version bump as a remedy. Claimed: the tool is not written and no interface_version_policy is committed yet, so neither run has been performed in this repository. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-ceremony`, `build-definition-of-done`, `build-research-record`, `build-skill-authoring`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is a twelve-month deprecation window right for an interface whose only consumers are inside this repository, or does the window belong to the consumer set rather than to the interface? | Count, per interface, the consumers that are not rebuilt by our own pipeline. An interface with none can retire a member as soon as every consumer is rebuilt and the rebuild is recorded; an interface with any external consumer cannot. | Every interface states a window of at least twelve months, matching the two policies on file, until the consumer count is recorded. | `X-cross-structure-061`, `X-build-interface-versioning-002` "Deprecated features remain in the specification for at least twelve months." |
| Which of the versioned patterns cited here are current, and at which revision? All research records for this skill are search-only. | A fetch of each cited document recording its revision string and the date fetched, which would let the standards table move from unverified to verified, per the standard-citation rule agentic-stack and build-skill-authoring both state (F-part-c-10). | Every version in the standards table stays unverified and the two policies are cited as patterns rather than as governing standards. | `F-part-c-10` "Cite the standard and its version" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/build-interface-versioning 2831cb4f |
