---
name: cap-capability-registry-use
description: How to find and publish a capability or an agent without knowing where records are kept: one name and one version constraint to resolve, one artifact and one semantic version to publish, one outcome to read. Load it when a caller needs a capability it should not hard-wire, when you are about to ship a new version of a skill, workflow or agent profile, when an event says a version was promoted or taken back, when you need another team's agent and only know what it should be good at, when someone asks 'which version am I actually running', 'what do I write down to get this', or 'what comes back when the thing is not signed', and before anyone joins a path or reads an index file directly.
---

# cap-capability-registry-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make the registry usable in three moves: name a record and a constraint to resolve one, hand over an artifact and a semantic version to publish one, read one outcome to know what happened. Nothing else is required of a caller. | sourced | `T-t3-01` "It has to be simple to use." |

## Entities

| Entity |
|---|
| `E-capability-capability-packaging` |
| `E-adapter-skill-files` |
| `E-swap-candidate-any-spec-conformant-registry` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| resolve (proposed): what an agent does | a namespace-scoped name and a version constraint, as two strings | one verified record: the version it chose, the digest of the artifact it names, and what that capability or agent is good at (proposed) | proposed | - |
| publish (proposed): what a human does | the artifact, a namespace-scoped name and a semantic version | a new record; the version now resolvable, nothing already published changed (proposed) | proposed | - |
| refresh (proposed): what an event does | a notification that a version was published, promoted or rolled back, carrying the name | the same resolution, re-run for that one name; no caller changes and no index is rebuilt (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a human publishes a version and an event takes it back** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:example:publish-and-rollback",
  "title": "A rollback is a resolution that changes, not an edit",
  "description": "A person publishes version 1.2.0 of a capability. The canary watch, entering as an event, reports a regression and the rollback target on the record is what resolution falls back to. Nothing published is rewritten: 1.2.0 stays resolvable by exact version and stops satisfying the constraint.",
  "examples": [
    {
      "publish": {
        "actor": "user:ana",
        "record": {
          "namespace": "platform",
          "name": "incident-triage",
          "version": "1.2.0",
          "kind": "capability",
          "digest": "sha256:9f2c1b7a4e6d08f35c1ab29d4e77b0c6d3a51e8f42bb90c7de13f5a6802c4419",
          "rollback_to": "1.1.3"
        }
      },
      "rollback": {
        "actor": "service:canary-watch",
        "reason": "acceptance criteria not met at canary",
        "effect": "1.2.0 yanked; nothing edited"
      },
      "resolution_after": {
        "query": {
          "name": "platform/incident-triage",
          "constraint": ">=1.0.0 <2.0.0"
        },
        "resolved": true,
        "record": {
          "version": "1.1.3",
          "digest": "sha256:1d40c8e5b9a27f61034de8c2957ab4416f0d3e8b7c25a9016fbb34d7e0592aac"
        },
        "verification": {
          "signature_verified": true,
          "digest_matched": true
        }
      }
    }
  ]
}
```

**Worked example 2 (proposed): an agent resolves a name and is refused** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-registry:example:refused",
  "title": "An unsigned record comes back as a problem, not a warning",
  "description": "The agent asked for the newest version satisfying its constraint. The one record that satisfies it carries no signature, so the outcome carries resolved false and a problem details body. The caller branches on type, shows detail to a person, and does not retry.",
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
| Three ways in, one query. TARGET T1's three ways in are a human, an agent and an event - a different enumeration from T6.2's four entries - and all three write down the same two strings, a name and a constraint, and get the same record back. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "A human must be able to enter the system." |
| The whole consuming surface is two strings in and one outcome out. cap-capability-registry states the record shape and the ordering; a caller never has to hold any of it in mind to ask for a capability. | sourced | `T-t3-01` "It has to be simple to use." |
| Enhancing one aspect leaves the rest untouched: publishing a new version, moving every record to a different store, adding a rollback target or signing with a new key changes nothing in a caller that named a name and a constraint, because those two strings are all it was ever asked to write down. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The complexity is hidden on purpose: a caller never chooses a store, an index, a transport, a digest algorithm or a trust anchor. Those exist, and cap-capability-registry-implement is where they are decided; none of them appears in what a caller writes. | sourced | `T-t2-01` "Composability hides the complexity." |
| Failure arrives as a problem details object, the shape cap-capability-registry adopts for this interface (F-b3-13), never as a missing-file exception, a warning line or a record served anyway. A caller branches on the type member and reads retryable; it never matches on wording. | sourced | `F-b3-13` "RFC 9457 problem details" |
| Nothing that comes back tells you how you will be scored. cap-capability-registry states design rule 6 on this interface (F-b1-07): a record may point at an acceptance criterion, and the criterion itself is never in a resolution outcome or a description handed to the capability about to run. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | To use a capability or an agent: write down its namespace-scoped name and a version constraint, call resolve, and read what comes back. Do not join a path, open an index, pick a store or pin a digest yourself. | The store, the index format and the transport are the capability's business, and a caller that reaches around them has bound itself to today's store and will break the first time it changes. | sourced | `T-t2-01` "Composability hides the complexity." |
| 2 | To publish: hand over the artifact, a namespace-scoped name and a semantic version. To change something you already published, publish another version; never edit or replace a version that is out. | cap-capability-registry states that a record is immutable and that a change is a new version (X-cap-capability-registry-007); for a publisher that means the cost of a mistake is one more version, and the cost of an in-place fix would be every caller that already resolved the old one. | sourced | `X-cap-capability-registry-007` "new versioned records" |
| 3 | On an event that says a version was published, promoted or rolled back, re-resolve that one name. Do not rebuild a local index, restart the caller, or hold a copy of the record. | An event is one of the three ways into the system, and it must reach this capability the same way a human or an agent does: by naming a record and a constraint. | sourced | `T-t1-03` "An internal or external event must be able to enter the system." |
| 4 | Read the outcome's resolved member, and when it is false branch on the problem's type member. Show detail to a person; never parse it, key metrics on it, or match on its wording. | cap-capability-registry adopts the platform's failure shape rather than inventing one (F-b3-13), and title and detail are written for readers and may be reworded without notice, while the type is the part a caller was promised. | sourced | `F-b3-13` "RFC 9457 problem details" |
| 5 | Write the constraint, not the version, and record the version you actually got in the run's own record. Resolve once at the start of a run and use that version for the whole of it. | Proposed: a pinned exact version stops you receiving fixes, and re-resolving mid-run lets a publication change the capability underneath a composition that is already running; the constraint plus a recorded answer gives you both. | proposed | - |
| 6 | To reach an agent another team owns, resolve it by the same two strings and read what it is good at and which authentication schemes it requires. Do not build a second way to discover outside agents. | An agent must be able to enter the system, and it only can without a bespoke integration if finding one of ours and finding someone else's are the same call with the same two arguments. | sourced | `T-t1-02` "An agent must be able to enter the system." |
| 7 | Read the two worked examples above, then stop. Open cap-capability-registry only if you have to judge whether a record or a store is conformant, and cap-capability-registry-implement only if you are building a store rather than using one. | A name, a constraint and one outcome is the whole consuming surface; making someone read the contract and the build guidance before they can ask for a capability is the kind of weight that stops a platform from being used at all. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Write what a record is good at specifically enough to sequence on, because that text is what a caller picks and orders on; 'good at code' is not something anyone can sequence, and callers cannot ask you what you meant at resolution time. | sourced | `T-t6-05` "so callers know how to call it and how to sequence it" |
| Proposed: do not retry a refusal that says retryable false. An unsigned record is unsigned on the second attempt too, and a constraint that nothing satisfies will not start being satisfied by asking again. | proposed | - |
| Proposed: if you cannot write a version constraint for what you want, you are naming a build rather than a capability. Publish it under a name and a version first, then resolve it like everything else. | proposed | - |
| Proposed: keep the resolved version in whatever you report at the end of a run. It costs one field and it is the difference between 'the capability regressed' and 'version 1.2.0 regressed'. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | The smallest round trip, from the repository root, with the proposed registry tool: publish one record with `python3 tools/registry.py publish --name platform/incident-triage --version 1.1.3 --artifact .claude/skills/agentic-stack`, then resolve it with `python3 tools/registry.py resolve --name platform/incident-triage --constraint '>=1.0.0 <2.0.0' --report out/registry-use.json`. It asserts resolved == true, version == '1.1.3', signature_verified == true and digest_matched == true, and that the outcome carries no acceptance criterion body. |
| Expected | exit 0 and one line reading `name=platform/incident-triage resolved=true version=1.1.3 signature_verified=true digest_matched=true`. |
| Deliberate breakage | Remove the signature member from that published record in the store, leaving the record and its digest otherwise untouched. |
| Expected failure | exit non-zero with `resolved=false signature_verified=false`, and the outcome carries a problem details body whose type is `urn:agentic:problem:record-unsigned` and whose detail names the version that failed verification. The record is refused rather than served with a warning, which is the property a caller is relying on when it does not check anything itself. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `cap-capability-registry`, `cap-capability-registry-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What does a caller do when the only version satisfying its constraint is yanked? | Count, over a period of real use, how often a constraint is satisfied only by a yanked version and whether callers that fall back to the previous version get a worse outcome than callers that refuse. | Refuse with the constraint-unsatisfiable problem type and name the nearest resolvable version in detail, so the choice to widen the constraint stays with the caller rather than being made silently. | `T-t3-02` "It cannot be daunting or overly complex" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-capability-registry 2831cb4f, 2026-09-03 |
