---
name: "cap-capability-registry-implement"
description: "How to build the capability registry on this stack: a signed, append-only index beside the packages that run today, a second store that fetches content-addressed records over a network, the migration from resolving by directory path to resolving by name and version constraint, where a resolution and a publish are wired so the platform's guarantees ride on them, and the run that decides whether either store may serve. Load it when writing or reviewing the resolver or the publisher, when a component is about to join a path to reach a capability, when planning the move off hard-wired versions, when someone asks 'where does resolution actually happen', 'can we serve records from somewhere else without touching the core', or 'why did this name resolve to that version', and before recording any registry conformance result as passing."
---

# cap-capability-registry-implement (folded into `cap-capability-packaging`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what cap-capability-registry specifies: two record stores chosen by configuration, one conformance run that resolves the same names and constraints through both and diffs records, digests and refusals, and the wiring that makes a resolution a recorded step rather than an unobserved file read. build-adapter-pair owns why there are two. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |

## Entities

| Entity |
|---|
| `E-capability-capability-packaging` |
| `E-adapter-skill-files` |
| `E-swap-candidate-any-spec-conformant-registry` |
| `E-not-running-mcp-endpoint` |

## Contract

### Shapes (JSON Schema 2020-12)

**registry-binding (proposed shape; the migration procedure and the wiring table are in references/cap-capability-registry-implement-implementation-notes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "resolution",
    "location",
    "trust_anchor",
    "execution_model"
  ],
  "properties": {
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "resolution": {
      "enum": [
        "signed-index",
        "registry-fetch"
      ]
    },
    "location": {
      "type": "string",
      "minLength": 1
    },
    "trust_anchor": {
      "type": "string",
      "minLength": 1
    },
    "cache": {
      "type": [
        "string",
        "null"
      ],
      "default": null
    },
    "execution_model": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "where_record_bytes_come_from",
        "identity_is",
        "network_required"
      ],
      "properties": {
        "where_record_bytes_come_from": {
          "enum": [
            "local signed index",
            "network fetch"
          ]
        },
        "identity_is": {
          "enum": [
            "a path plus a version string",
            "a content digest"
          ]
        },
        "network_required": {
          "type": "boolean"
        }
      }
    }
  }
}
```

**registry-conformance-report (proposed shape; the per-record rows are in references/cap-capability-registry-implement-implementation-notes.md)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:conformance:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "records_checked",
    "served_unverified",
    "refusals",
    "refusals_typed",
    "record_divergence"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    },
    "records_checked": {
      "type": "integer",
      "minimum": 0
    },
    "resolved_records": {
      "type": "integer",
      "minimum": 0
    },
    "served_unverified": {
      "type": "integer",
      "minimum": 0
    },
    "refusals": {
      "type": "integer",
      "minimum": 0
    },
    "refusals_typed": {
      "type": "integer",
      "minimum": 0
    },
    "record_divergence": {
      "type": "integer",
      "minimum": 0
    },
    "index_chain_broken": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| cap-capability-registry owns the contract, including that a published record is never edited (X-cap-capability-registry-007). This skill adds only how it is built: an implementation that rewrites a record in place, serves a record whose verification did not pass, or resolves a name its binding record does not describe has produced a defect, not an extension. | sourced | `X-cap-capability-registry-007` "rather than in-place edits" |
| build-adapter-pair states the swap test (F-meta-04). The consequence here is that both stores are selected by a binding record read as configuration: if choosing between the host index and the network store requires editing a file the core owns, the boundary is drawn wrong and the pair has found the defect it exists to find. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| agentic-stack states design rule 7 as a test (F-b1-08, F-b4-01). What this skill adds: a resolution and a publish are steps like any other, so each is recorded with the correlation attribute set at dispatch and counted against the unit's ceiling, and there is no flag by which a caller resolves a capability unobserved. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record states the labelling rule (F-part-c-08). The consequence here is that 'both stores resolve the same records' is claimed until a run is attached naming the command, the name and constraint set, the code version and the counts. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| The index that runs on this host today is append-only and chained so that an edit between runs is detectable, as build-evidence-record states of the task store (F-a5-03). The consequence here is that the registry index inherits the chain rather than inventing a second integrity scheme: a record appended out of chain is an index that fails its own check before any signature is looked at. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest" |
| Apply build-adapter-pair: this pair's differing axes (where_record_bytes_come_from, identity_is) are recorded in the adapters section below and in the second adapter's swap_procedure; this row does not restate them. Two bindings identical on every axis are one adapter written twice and fail the pair check. proposed pointer, see that skill. | proposed | `F-b1-04` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: cap-capability-registry already owns this exclusion for the storage layout, the transport and the index or tag format; applied at the pair level, which store served a resolution is visible only as a member of the resolution outcome, never as a difference in the record a caller receives. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put every record store behind the binding record and keep path joins, index parsers, signature libraries and network clients inside the adapter directory; core and seam modules import resolve, list_versions, describe, publish and verify only. | agentic-stack states design rule 1 as a test (F-b1-02), and a hard-coded index path is that failure in executable form: it is a decision about where records live, written into code that is supposed to be indifferent to it. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| 2 | Build today's adapter as a signed, append-only index beside the package directories on this host, chained so each append names the previous head, and say plainly in its binding record that nothing is registered anywhere today: the tool endpoint that runs is live and authenticated with nothing registered against it. | Starting the record honestly is what keeps the first adapter from being described as a migration that already happened; PASS.md Part A records a live endpoint with an empty registry, so this adapter starts red and its first green run is the first thing it proves. | sourced | `F-a6-03`, `F-a5-03` "zero tools registered" |
| 3 | Build the second adapter against a network store of content-addressed records: resolve a namespace-scoped name and constraint, fetch the record, verify its digest before it is parsed, then verify the signature, and cache it. Fill in both execution-model axes in its binding record. | build-adapter-pair owns why a second adapter exists (F-b1-04), and cap-capability-registry already states the content-addressed record it resolves (X-end-to-end-069). The consequence stated here is this skill's own and proposed: a second index file on this host would let the resolver keep assuming records and packages share a filesystem, while a fetched, digest-verified record forces identity and integrity to become contractual. | sourced | `F-b1-04`, `X-end-to-end-069` "content-addressed foundation for agent discovery" |
| 4 | Proposed migration, in this order: publish one record for every package that exists today; run the new resolver in shadow beside the path joins that callers use now, over the same name and constraint set; require identical record, identical digest and identical refusal on every entry; only then let a caller stop joining a path. Never rewrite a published record during the migration. | Proposed: the migration risk is not a loud failure but a quiet one, where the registry resolves a name to a version nobody chose because a record was published from a tree that had moved on; a shadow run that diffs digests turns that into a list before anything depends on it. Research query: is there a recorded migration record (kb/ceremonies or an evidence record) from another capability in this platform that ran a shadow resolver or a diffed cutover the same way, confirming this is the platform's own established migration pattern rather than invented here? | proposed | - |
| 5 | Wire the cross-cutting concerns on the resolution and publication paths: set the correlation attribute explicitly at dispatch and carry it on every resolution, consult policy before a record from a namespace this platform does not own is resolved, write a provenance record for every publish, and count both against the unit's ceiling. | agentic-stack records that correlation did not survive the agent boundary and must ride on an attribute set at dispatch (F-a7-02); a resolution that is not correlated is a capability that entered a run with no trace of which run pulled it in. | sourced | `F-a7-02`, `F-b1-08` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Have each adapter report, at start-up, the store it actually reached, the index head or registry reference it read, and the trust anchor it is verifying against, and compare all three against its binding record; a mismatch fails the definition of done for that store. | build-definition-of-done and build-evidence-record both require effective configuration to be attested rather than assumed, because configuration written in the documented place has been observed to validate, review correctly and take no effect at all (F-a7-04). | sourced | `F-a7-04` "had no runtime effect" |
| 7 | Write one conformance run parameterised over the binding records: resolve the same name and constraint set through every configured store, assert the per-store counters, and diff the resolved records, their digests and their refusals across stores. | build-adapter-pair owns the rule that every interface ships with two adapters (F-b1-04); one run over two stores is what makes the swap a tested property, because a per-store suite would let each store define conformance as whatever it happens to do. | sourced | `F-b1-04` "Swappability is a tested property, not an intention." |
| 8 | Proposed: open references/cap-capability-registry-implement-implementation-notes.md when running the shadow migration, wiring the resolution path, or reviewing a binding record. The body of this skill is enough to build and to judge the pair without it. | Proposed: the migration procedure and the wiring table are longer than the body's budget and are needed only while doing those two jobs. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| build-definition-of-done already states the structurally-green finding (F-a7-03). What this skill adds, as its own consequence and proposed: make records_checked and adapters_run assertions rather than log lines, because a conformance run pointed at an empty namespace or a mistyped binding resolves nothing, refuses nothing and exits zero. | sourced | `F-a7-03` "Only diff, syntax and format ran." |
| Proposed: verify the digest before the record is parsed, not after. A store that parses first has already spent untrusted bytes on its own parser, which is the one place an unverified record gets to run code. Research query: is there a recorded parser-security finding on this stack or a comparable registry showing an unverified record reaching a parser, which would source this as a known risk rather than a precaution? | proposed | - |
| Proposed: resolve a constraint once per run and carry the resolved version for the rest of it, recording that version in the run's own record. A composition that re-resolves mid-run can change capability underneath itself when someone publishes. Research query: is there a recorded composition run on this platform where a mid-run re-resolution actually changed the version underneath a caller, confirming this failure mode rather than only anticipating it? | proposed | - |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-skill-files` | today | the five operations of cap-capability-registry served by a signed, append-only, hash-chained index file kept beside the package directories on this host: resolve and list_versions read the index, verify checks the index chain, the record signature and the digest against the tree, publish appends. PASS.md records no registry row at all, and describing this store as a filesystem registry with a signed index and semver resolution is the manifest's entry, proposed here. | Proposed: cannot serve a caller without access to this filesystem, cannot be verified by a party that does not trust this host's signing key, and cannot distinguish two records whose only difference is content unless the index says so. | Change the binding record's resolution, location and trust_anchor, restart, confirm the reported store, index head and trust anchor match the record, then run the conformance run over the same name and constraint set. No core file is edited. | claimed | `F-b3-07`, `F-a5-03` "skill files" |
| `E-swap-candidate-any-spec-conformant-registry` | second | the same five operations of cap-capability-registry served by content-addressed records held in an OCI registry, fetched over a network and verified by digest and signature before parse; the row names the candidate class rather than a product. | Proposed: cannot hand back a path, cannot be edited between runs by whoever holds this host, and cannot serve a record whose identity is a directory name - so anything it cannot implement was a filesystem assumption that had leaked into the contract. | Its binding record differs from today's on where_record_bytes_come_from (network fetch versus local signed index) and on identity_is (a content digest versus a path plus a version string). One parameterised conformance run covers both, and the pair stays claimed until that run is recorded. | claimed | `F-b3-07`, `X-end-to-end-069` "spec-conformant registry" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/capability-registry/test.sh && python3 harness/capability-registry/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 0283c7b: exit 0; last lines: adapters_run=2 \| conformance PASSED: 22/22 cases, 2 binding(s) |
| Deliberate breakage | In harness/capability-registry/interface.py, make resolution serve a record whose signature verifies but whose digest does not match (drop the digest_matched condition on the serve branch), run the criterion (served_unverified becomes 1 and the gate exits 1), then git checkout harness/capability-registry/interface.py. |
| Expected failure | Measured by tools/measure.py at 0283c7b: exit 1; last lines:   ..   served_unverified=1 refusals=1 resolved_records=2 \| passed 13, failed 7 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-02` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-capability-registry`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which store is the default when the platform starts? | Measure cold-start resolution latency for the full name set under each binding, and the failure mode when the network store is unreachable at the moment a capability is first needed. Nothing is registered remotely today, so the measurement cannot be taken until the second store holds records. | The host-local signed index, because it needs no process beyond the caller to make progress; the network store stays a conformance-run peer and a publication target until the measurement says otherwise. | `F-a6-03` "zero tools registered" |
| Does resolving a capability spend the calling unit's ceiling, or the platform's? | Count, over a run of the reference consumption example, how much of a unit's ceiling is spent on resolutions rather than on work, and whether any unit is terminated by resolution cost alone. | Charge it to the calling unit, since every unit of work carries a ceiling and exceeding it terminates the unit rather than the platform; revisit if resolution cost alone ever terminates a unit. | `F-b4-02` "Every unit of work carries a ceiling" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-capability-registry 2831cb4f, 2026-09-03 |
