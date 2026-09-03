---
name: cap-capability-registry
description: The capability-registry contract: one record per capability or agent, resolved by name and a version constraint, signed, digest-matched against the package it names, and never edited in place. Load it before anything asks 'which version of this capability do I get', when a capability or an agent has to be found rather than hard-wired, when another party's agent must be discoverable by what it is good at and how to authenticate to it, when a new version of a skill, workflow or agent profile is about to be rolled out or rolled back, when someone asks 'where is the version number', 'how do we know this is the same thing we signed', 'can an outside team publish here', or 'how do we take a bad version back', and before any code joins a path to reach a capability instead of naming it.
---

# cap-capability-registry

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for finding a capability or an agent by name and version constraint and getting back a signed, digest-matched record, so the core imports resolution and the store that holds the records stays an adapter. | sourced | `F-b1-02`, `X-end-to-end-069` "content-addressed foundation for agent discovery" |

## Entities

| Entity |
|---|
| `E-capability-capability-packaging` |
| `E-standard-agent-skills-spec` |
| `E-standard-a2a-messaging` |
| `E-adapter-skill-files` |
| `E-swap-candidate-any-spec-conformant-registry` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-agent-skills-spec` | unversioned | unverified | https://agentskills.io/specification | `F-b3-07`, `X-end-to-end-025`, `X-end-to-end-023` |
| `E-standard-a2a-messaging` | unverified | unverified | https://a2a-protocol.org/latest/specification/ | `F-b3-08`, `X-cap-capability-registry-006` |

- `E-standard-agent-skills-spec` version note: no published version string was read; the record, not the package format, carries the semantic version this interface orders on
- `E-standard-a2a-messaging` version note: no version string was read from the specification in this environment

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| resolve | a namespace-scoped record name and a version constraint | exactly one record, chosen by semantic-version ordering - the ordering cap-capability-packaging leaves to a registry to supply - carrying the digest of the artifact it names and the signature over that record | sourced | `X-end-to-end-023` "the registry attempts to parse versions as semantic versions for proper ordering" |
| list_versions | a namespace-scoped record name | every published version under that name in resolution order; a version that is not a semantic version falls to the back of that order, ordered by when it was published | sourced | `X-end-to-end-023` "Non-semantic versions are allowed but will be ordered by publication timestamp." |
| describe | one resolved record identity | the record's machine-readable description: what it is good at, its input and output modalities, and the authentication schemes a caller must satisfy to reach it | sourced | `X-cap-capability-registry-006` "each agent publishes a machine-readable description of its capabilities, input and output modalities, and authentication requirements" |
| publish | a candidate record naming a namespace, a name, a semantic version, the digest of the artifact it names and a rollback target, plus a signature over it | a new immutable version record; a change to a published record is a new version, never an edit to the one that is there | sourced | `X-cap-capability-registry-007` "Mutable metadata are represented as new versioned records rather than in-place edits" |
| verify | a record as it came back from a store | accept, or a refusal: the signature must verify and the digest must match the artifact the record names, and both are checked before any of the record's content is handed on | sourced | `X-end-to-end-069`, `X-cap-capability-registry-005` "cryptographic signing" |

### Shapes (JSON Schema 2020-12)

**capability-record (proposed summary shape; the full record, the rollout members and the standards table are in references/registry-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:record:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "namespace",
    "name",
    "version",
    "kind",
    "digest",
    "signature",
    "record_schema_version"
  ],
  "properties": {
    "namespace": {
      "type": "string",
      "minLength": 1
    },
    "name": {
      "type": "string",
      "minLength": 1
    },
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:[-+][0-9A-Za-z.-]+)*$"
    },
    "kind": {
      "enum": [
        "capability",
        "agent"
      ]
    },
    "digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "signature": {
      "type": "string",
      "minLength": 1
    },
    "record_schema_version": {
      "type": "string",
      "minLength": 1
    },
    "good_at": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 20
      }
    },
    "auth_schemes": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "acceptance_criteria_ref": {
      "type": [
        "string",
        "null"
      ],
      "default": null
    },
    "rollback_to": {
      "type": [
        "string",
        "null"
      ],
      "default": null
    },
    "published_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

**resolution-outcome (proposed summary shape; the refusal members are in references/registry-shapes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:resolution:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "resolved",
    "verification"
  ],
  "properties": {
    "query": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "name",
        "constraint"
      ],
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1
        },
        "constraint": {
          "type": "string",
          "minLength": 1
        }
      }
    },
    "resolved": {
      "type": "boolean"
    },
    "record": {
      "$ref": "urn:agentic:cap:capability-registry:record:0.1"
    },
    "verification": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "signature_verified",
        "digest_matched"
      ],
      "properties": {
        "signature_verified": {
          "type": "boolean"
        },
        "digest_matched": {
          "type": "boolean"
        }
      }
    },
    "problem": {
      "type": [
        "object",
        "null"
      ],
      "default": null
    }
  }
}
```

**Worked example 2 (proposed): an agent resolves a name and is refused [caller's view, folded from cap-capability-registry-use]** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:example:refused",
  "title": "An unsigned record comes back as a problem, not a warning",
  "description": "The agent asked for the newest version satisfying its constraint. The one record that satisfies it carries no signature, so the outcome carries resolved false and a problem details body. The caller branches on type, shows detail to a person, and does not retry. `urn:agentic:problem:record-unsigned` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `identity-untrusted`, which is also 401 and not retryable, with the unsigned version named in detail, as the open question below records.",
  "examples": [
    {
      "actor": "agent:triage-router",
      "query": {
        "name": "partner-co/log-summariser",
        "constraint": ">=2.1.0"
      },
      "resolved": false,
      "verification": {
        "signature_verified": false,
        "digest_matched": false
      },
      "problem": {
        "type": "urn:agentic:problem:record-unsigned",
        "title": "The record that satisfies this constraint is not signed",
        "status": 401,
        "detail": "partner-co/log-summariser 2.4.0 carries no signature; 2.0.6 is signed but does not satisfy '>=2.1.0'",
        "retryable": false,
        "correlation_id": "run-2026-09-03-0042"
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| cap-capability-packaging already states that the packaging format is not published as an explicitly versioned artifact (X-end-to-end-025). The consequence here is where design rule 2's version lives: the record carries the semantic version and the ordering, so a caller names a constraint and not a directory, and the package format never has to grow a version field it does not have. | sourced | `X-end-to-end-025` "Anthropic does not currently publish the skill format as an explicitly versioned artifact." |
| A record is immutable. A change is a new version record under a globally unique namespace, name and version, and the identifier a caller writes down resolves to content, so two records that differ in one byte are two records. | sourced | `X-cap-capability-registry-007` "Mutable metadata are represented as new versioned records rather than in-place edits, all capability-bearing identifiers map first to CIDs, and extension collision avoidance requires globally unique (namespace, name, version) triples." |
| cap-provenance owns attribution of an artifact to what produced it (F-b4-05). The consequence on this interface is a refusal rule, not a report: a record whose signature does not verify, or whose digest does not match the artifact it names, is refused, and there is no configuration under which it is served with a warning instead. | sourced | `X-end-to-end-069`, `F-b4-05` "cryptographic signing" |
| Resolution is by name and constraint only. A caller that has to know where a record is stored, in which index file or under which tag, is holding an adapter's detail, and the same query must return the same record from any conformant store. | sourced | `X-cap-capability-registry-002` "a standardized interface for MCP host applications" |
| A record describes another party's agent by the same operations as one of ours: what it is good at, its input and output modalities and how a caller authenticates to it, which is what lets an agent enter the system without a bespoke integration. | sourced | `X-cap-capability-registry-006`, `T-t1-02` "Agent Cards serve as a discovery mechanism" |
| cap-errors owns the failure shape for the whole platform (F-b3-13). The consequence here is that this interface adds no failure vocabulary of its own: an unknown name, an unsatisfiable constraint, a bad signature and a digest mismatch all come back as problem details on the resolution outcome, never as a store's own exception. | sourced | `F-b3-13` "— adopt the RFC directly" |
| cap-document-validation owns deciding whether a declared shape conforms (F-b3-09). The consequence here is that a record's conformance to the record schema is decided by that capability against a published schema, so a store cannot define conformance as whatever it happens to accept. | sourced | `F-b3-09` "any 2020-12 validator" |
| Publication is staged rather than instantaneous: a candidate is evaluated, gated, put in front of a fraction of traffic, and expanded or rolled back on what that showed. Proposed consequence for this interface: the rollback target is a member of the record, so taking a version back is a resolution that changes and never an edit to a capability that is running. | sourced | `X-end-to-end-026`, `T-t4-04` "evaluate locally, gate in CI, canary in production, then expand or roll back based on quality metrics" |
| Three ways in, one query. TARGET T1's three ways in are a human, an agent and an event - a different enumeration from T6.2's four entries - and all three write down the same two strings, a name and a constraint, and get the same record back. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "A human must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: publishing a new version, moving every record to a different store, adding a rollback target or signing with a new key changes nothing in a caller that named a name and a constraint, because those two strings are all it was ever asked to write down. cap-capability-packaging states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion a resolved capability's output will be judged against. agentic-stack states design rule 6 (F-b1-07); on this interface it forbids exactly one thing: the record may carry an acceptance_criteria_ref, an opaque identifier the publisher and the improvement loop resolve, and the criterion body never travels in a resolution outcome, a describe response or anything else handed to the capability that is about to be run. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| The storage layout, the transport and the index or tag format. A caller names a record and a constraint; whether the record arrived from a file on this host or over a network is the adapter's business and never a field of the query. | sourced | `X-cap-capability-registry-002` "MCP registries are metaregistries that host metadata about packages, but not the package code or binaries." |
| Proposed: the publisher's evaluation scores, the canary traffic share and the identity of who approved a promotion. They belong to the rollout record, not to what a resolving caller receives. Research query: does any of the researched registry standards (MCP Registry, OASF, AGNTCY ADS) define a rollout or canary record separate from the resolvable capability record, which would confirm this split is a documented pattern rather than invented here? | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability plus its governing standards before any store is named: 'a capability or agent record is resolved by name and version constraint from a signed registry'. Name the record schema and the discovery-record specification, and write every version as unverified until one is read. | agentic-stack states rule 2 as a test (F-b1-03): an interface without a cited standard is either mis-drawn or belongs in the seam layer, and this one has standards to adopt, so it is not a seam. | sourced | `F-b1-03`, `F-part-c-10` "Each interface names the standard that governs it." |
| 2 | Require a semantic version on every published record and refuse a publish without one, rather than accepting the version string a publisher happens to use. | Ordering is the whole point of the interface, and a version a registry cannot parse falls back to being ordered by when it was published, which makes a re-publish silently reorder what a constraint resolves to. | sourced | `X-end-to-end-023` "Non-semantic versions are allowed but will be ordered by publication timestamp." |
| 3 | Make verification a precondition of resolution: check the signature, then check the digest against the artifact the record names, and return the refusal before any record content is handed on. Do not implement a mode that logs and continues. | A registry that serves an unverified record has moved the trust decision to every caller, and callers do not make it; content-addressed identifiers plus signing are what make the record and the artifact the same claim. | sourced | `X-cap-capability-registry-005` "content-addressed foundation for agent discovery in multi-agent systems" |
| 4 | Validate every record against the published record schema through the document-validation capability before it is published and again when it is resolved, and let that capability report the violations. | cap-document-validation owns checking a declared shape (F-b3-09); reusing it is what keeps the record check identical across every store that serves this interface, instead of each store deciding what a valid record is. | sourced | `F-b3-09` "any 2020-12 validator" |
| 5 | Publish a changed capability as a new record through evaluate, gate, canary and rollback, and never by editing a capability that is already running. Keep the rollback target on the record so a bad version is undone by resolving differently. | This is the established shape for rolling out a changed prompt or skill, and it is what makes the self-improvement loop safe to run at the end of each section: the loop writes records here, so a regression costs a resolution and not a live capability. | sourced | `X-end-to-end-026`, `T-t4-04` "The common pattern is: evaluate locally, gate in CI, canary in production, then expand or roll back based on quality metrics." |
| 6 | Register another party's agent as a record of the same shape, carrying what it is good at, its modalities and its authentication schemes, and resolve it with the same operations used for our own capabilities. | An agent must be able to enter the system, and it can only do so without a bespoke integration if being found and being described are the same two operations for an outside agent as for one of ours. | sourced | `T-t1-02`, `X-cap-capability-registry-006` "The client discovers the server's required authentication schemes via the securitySchemes field in the AgentCard." |
| 7 | Choose the second adapter on a different distribution model: content-addressed records fetched from a network registry, not a second index file on the same host. Name the axis the two execution models differ on before writing either. | build-adapter-pair owns why there is a second adapter (F-b1-04). The consequence here is specific: two host-local indexes would leave the interface free to keep assuming the records and the packages share a filesystem, and only a fetched, digest-verified record forces identity and integrity to become contractual. | sourced | `F-b1-04`, `X-end-to-end-069` "Every interface ships with at least two adapters" |
| 8 | Expose the interface as a specification other people implement rather than as an API of ours, and require no client library of ours to publish or resolve. | agentic-stack states rule 4 as a test (F-b1-05): a boundary that needs our client is bespoke where a standard existed, and a registry interface that downstream aggregators can implement is exactly the case where one existed. | sourced | `F-b1-05`, `X-cap-capability-registry-002` "The MCP Registry defines an OpenAPI spec that other MCP registries can implement" |
| 9 | To use a capability or an agent: write down its namespace-scoped name and a version constraint, call resolve, and read what comes back. Do not join a path, open an index, pick a store or pin a digest yourself. | The store, the index format and the transport are the capability's business, and a caller that reaches around them has bound itself to today's store and will break the first time it changes. | sourced | `T-t2-01` "Composability hides the complexity." |
| 10 | Proposed: open references/registry-shapes.md when you are implementing the record schema, wiring the rollout members, or reviewing a record someone published. The body of this skill is enough to judge this interface and to call it without opening that file. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full record schema, the rollout members and the standards table are longer than the body's budget allows, and a reader deciding whether to resolve or publish does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the structurally-green finding (F-a7-03). What it adds here: assert records_checked and adapters_run as numbers, because a registry conformance run pointed at an empty namespace resolves nothing, refuses nothing, and exits zero. | sourced | `F-a7-03` "A deterministic gate can be structurally green and mean nothing." |
| Keep the record pointing at the artifact rather than containing it: a registry holds metadata about packages, not the package bytes, so a record stays small enough to sign, to list and to compare. | sourced | `X-cap-capability-registry-002` "MCP registries are metaregistries that host metadata about packages, but not the package code or binaries." |
| Require every record to state the record-schema version it is valid against, so a schema change is a readable fact about each record instead of an assumption about the whole store. | sourced | `X-cap-capability-registry-003` "records must specify the OASF schema version they need to be valid against" |
| Treat a preview interface as a moving target and pin what you depend on: the registry interface this design follows is published as a frozen preview version rather than a settled release, so depend on the operations, not on fields a preview may still add. | sourced | `X-cap-capability-registry-001` "The Registry API has entered an API freeze (v0.1)" |
| Write each record's good_at entries specific enough to sequence on, the way the reference consumption example's agent profiles are, so a caller can pick and order agents from records alone rather than by asking whoever wrote them. | sourced | `T-t6-05` "Each agent is defined up front by what it is good at, so callers know how to call it and how to sequence it." |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-skill-files` | today | the five operations served by a signed index file kept beside the package directories on this host: resolve and list_versions read the index, verify checks the index signature and the per-record digest against the tree, publish appends a new record. cap-capability-packaging owns this adapter for the packaging row (F-b3-07); PASS.md has no registry row at all, so calling it a filesystem registry with a signed index and semver resolution is the manifest's entry and is proposed here. | Proposed: cannot serve a caller that has no access to this filesystem, cannot hold two versions of a record that differ only in content without a naming convention on top, and cannot be read by a party that does not trust this host's index signature. | Point the resolver at the other store by configuration, resolve the same name and constraint set through both, and require identical records, identical digests and identical refusals. No core file is edited, because the core imports resolve, list_versions, describe, publish and verify. | claimed | `F-b3-07` "skill files" |
| `E-swap-candidate-any-spec-conformant-registry` | second | the same five operations served by content-addressed records held in an OCI registry and fetched over a network, verified by digest and signature before use; the row names the candidate class, and cap-capability-packaging cites the same class for the packaging row (F-b3-07). | Proposed: cannot hand back a path, cannot be edited between runs by whoever holds the host, and cannot serve a record whose identity is a directory name - which is the point, since it breaks the assumption that a capability is a directory of files on the same host. | One conformance run resolves the same name and constraint set through both stores and diffs the records, the digests and the refusals. Proposed: the execution-model axes that must differ are where the record bytes come from (a local signed index versus a network fetch) and what identity is (a path plus a version string versus a content digest). | claimed | `F-b3-07`, `X-end-to-end-069` "spec-conformant registry" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | One conformance run over both stores, from the repository root, with a proposed tool: `python3 tools/conformance_capability_registry.py --adapter config/registry/today.json --adapter config/registry/oci.json --fixtures tests/fixtures/registry --report out/registry-conformance.json`. The fixture set holds three records under one name: a good one, one whose signature is absent, and one whose digest names a tree that was edited after signing. Assert adapters_run >= 2, records_checked > 0, resolved_records == 1 per adapter with the constraint `>=1.0.0 <2.0.0`, served_unverified == 0, refusals == 2 per adapter, and refusals_typed == refusals with every refusal carrying a `urn:agentic:problem:` type. |
| Expected | exit 0 with one line per adapter reading `adapter=<role> records_checked=3 resolved_records=1 served_unverified=0 refusals=2 refusals_typed=2` followed by `adapters_run=2 record_divergence=0`. |
| Deliberate breakage | In the resolver, downgrade the digest check from a refusal to a logged warning and return the record anyway, leaving the signature check as it is. |
| Expected failure | exit non-zero on both adapters with `served_unverified=1 refusals=1`, naming the digest-mismatch fixture as served and the unsigned fixture as still refused. The signature refusal surviving is what shows the run distinguishes the two checks rather than passing or failing as a block. |
| Status | claimed |
| Evidence | `F-part-c-04`, `X-end-to-end-069` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-ceremony`, `build-definition-of-done`, `build-research-record`, `build-skill-authoring`, `cap-capability-packaging`, `cap-document-validation`, `cap-errors`, `cap-provenance`

Used by: `build-entry-conformance`, `cap-capability-registry-implement`, `compose-improvement-loop`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The registry interface and the content-addressed record schema this design follows have no E-standard- entity in this knowledge base, so contract.standards cannot name them by id. Which of three ways closes that? | Applying 1-3-1 (T-t5-02): (1) add entities for them, which rehashes the entity chain and invalidates every written skill's provenance heads; (2) drop contract.standards and leave rule 2 unsatisfied on this interface; (3) name the two standard entities the knowledge base does carry and record the registry interface and the record schema in prose against their research records. Recommendation and choice: (3). Deciding evidence would be a knowledge-base rebuild that adds the two entities, or a fetch of either specification recording a version string. | contract.standards names the two entities that resolve today; the registry interface is cited as a research record and its version is recorded unverified, because the record on file describes a preview under an API freeze rather than a settled release. | `T-t5-02`, `X-cap-capability-registry-001` "The Registry API has entered an API freeze (v0.1)" |
| Is the reference consumption example's agent profile registry the same registry as this one, or a projection of it? | The example ships a single flat file of profiles with one registry_version and no per-record signature, digest or version constraint; resolve the same profile through it and through a signed record and compare what a caller gets. The disagreement is recorded here rather than resolved: the change this skill proposes is a namespace, a version and a signature per profile. | Treat the example's flat profile file as today's adapter rendering its index, and require the signature and digest members before any profile describing a party outside this platform is admitted. | `T-t6-05`, `X-cap-capability-registry-006` "Agent Cards serve as a discovery mechanism through which each agent publishes a machine-readable description of its capabilities" |
| Are a capability record and an agent record one kind with a discriminator, or two schemas? | Publish both through one schema and count the fields only one kind ever populates; a record format that already requires each record to name the schema version it validates against can carry both, and the count says whether that is one shape or two wearing one name. | One record shape with a kind discriminator, because two shapes double what a conformant store must implement to serve anything at all. | `X-cap-capability-registry-003` "OASF records use semantic versioning to indicate the current version" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-capability-registry 2831cb4f, 2026-09-03 |
