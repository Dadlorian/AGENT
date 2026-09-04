# cap-capability-registry: the caller's view

Proposed. Folded in from the former `cap-capability-registry-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-capability-registry` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 0 row(s) of that kind were dropped in the fold.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make the registry usable in three moves: name a record and a constraint to resolve one, hand over an artifact and a semantic version to publish one, read one outcome to know what happened. Nothing else is required of a caller.  
  _sourced_ - `T-t3-01` "It has to be simple to use."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| resolve (proposed): what an agent does | a namespace-scoped name and a version constraint, as two strings | one verified record: the version it chose, the digest of the artifact it names, and what that capability or agent is good at (proposed) | proposed | - |
| publish (proposed): what a human does | the artifact, a namespace-scoped name and a semantic version | a new record; the version now resolvable, nothing already published changed (proposed) | proposed | - |
| refresh (proposed): what an event does | a notification that a version was published, promoted or rolled back, carrying the name | the same resolution, re-run for that one name; no caller changes and no index is rebuilt (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-capability-registry` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a human publishes a version and an event takes it back

_proposed_ - sources: -.

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

### Worked example 2 (proposed): an agent resolves a name and is refused

_proposed_ - sources: -.  Also carried in the body of `cap-capability-registry` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-capability-registry` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **To publish: hand over the artifact, a namespace-scoped name and a semantic version. To change something you already published, publish another version; never edit or replace a version that is out.**  
  _why:_ cap-capability-registry states that a record is immutable and that a change is a new version (X-cap-capability-registry-007); for a publisher that means the cost of a mistake is one more version, and the cost of an in-place fix would be every caller that already resolved the old one.  
  _sourced_ - `X-cap-capability-registry-007` "new versioned records"
- **On an event that says a version was published, promoted or rolled back, re-resolve that one name. Do not rebuild a local index, restart the caller, or hold a copy of the record.**  
  _why:_ An event is one of the three ways into the system, and it must reach this capability the same way a human or an agent does: by naming a record and a constraint.  
  _sourced_ - `T-t1-03` "An internal or external event must be able to enter the system."
- **Read the outcome's resolved member, and when it is false branch on the problem's type member. Show detail to a person; never parse it, key metrics on it, or match on its wording.**  
  _why:_ cap-capability-registry adopts the platform's failure shape rather than inventing one (F-b3-13), and title and detail are written for readers and may be reworded without notice, while the type is the part a caller was promised.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"
- **Write the constraint, not the version, and record the version you actually got in the run's own record. Resolve once at the start of a run and use that version for the whole of it.**  
  _why:_ Proposed: a pinned exact version stops you receiving fixes, and re-resolving mid-run lets a publication change the capability underneath a composition that is already running; the constraint plus a recorded answer gives you both.  
  _proposed_ - -
- **To reach an agent another team owns, resolve it by the same two strings and read what it is good at and which authentication schemes it requires. Do not build a second way to discover outside agents.**  
  _why:_ An agent must be able to enter the system, and it only can without a bespoke integration if finding one of ours and finding someone else's are the same call with the same two arguments.  
  _sourced_ - `T-t1-02` "An agent must be able to enter the system."
- **Read the two worked examples above, then stop. Open cap-capability-registry only if you have to judge whether a record or a store is conformant, and cap-capability-registry-implement only if you are building a store rather than using one.**  
  _why:_ A name, a constraint and one outcome is the whole consuming surface; making someone read the contract and the build guidance before they can ask for a capability is the kind of weight that stops a platform from being used at all.  
  _sourced_ - `T-t3-02` "It cannot be daunting or overly complex, or no one will use it."

## Other caller invariants

- The whole consuming surface is two strings in and one outcome out. cap-capability-registry states the record shape and the ordering; a caller never has to hold any of it in mind to ask for a capability.  
  _sourced_ - `T-t3-01` "It has to be simple to use."
- The complexity is hidden on purpose: a caller never chooses a store, an index, a transport, a digest algorithm or a trust anchor. Those exist, and cap-capability-registry-implement is where they are decided; none of them appears in what a caller writes.  
  _sourced_ - `T-t2-01` "Composability hides the complexity."
- Failure arrives as a problem details object, the shape cap-capability-registry adopts for this interface (F-b3-13), never as a missing-file exception, a warning line or a record served anyway. A caller branches on the type member and reads retryable; it never matches on wording.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"
- Nothing that comes back tells you how you will be scored. cap-capability-registry states design rule 6 on this interface (F-b1-07): a record may point at an acceptance criterion, and the criterion itself is never in a resolution outcome or a description handed to the capability about to run.  
  _sourced_ - `F-b1-07` "An agent sees its outcome, never the criterion it is judged against"

## Caller practices

- Write what a record is good at specifically enough to sequence on, because that text is what a caller picks and orders on; 'good at code' is not something anyone can sequence, and callers cannot ask you what you meant at resolution time.  
  _sourced_ - `T-t6-05` "so callers know how to call it and how to sequence it"
- Proposed: do not retry a refusal that says retryable false. An unsigned record is unsigned on the second attempt too, and a constraint that nothing satisfies will not start being satisfied by asking again.  
  _proposed_ - -
- Proposed: if you cannot write a version constraint for what you want, you are naming a build rather than a capability. Publish it under a name and a version first, then resolve it like everything else.  
  _proposed_ - -
- Proposed: keep the resolved version in whatever you report at the end of a run. It costs one field and it is the difference between 'the capability regressed' and 'version 1.2.0 regressed'.  
  _proposed_ - -

## Open questions carried over

- **What does a caller do when the only version satisfying its constraint is yanked?**  
  _deciding evidence:_ Count, over a period of real use, how often a constraint is satisfied only by a yanked version and whether callers that fall back to the previous version get a worse outcome than callers that refuse.  
  _default until then:_ Refuse rather than serve the yanked version, and name the nearest resolvable version in detail so the choice to widen the constraint stays with the caller rather than being made silently. The refusal carries `urn:agentic:problem:constraint-unsatisfiable`, proposed and pending registration alongside `record-unsigned` in docs/decomposition.md section 2.1.6; until that row lands an implementation returns the registered `document-invalid` with the constraint and the yanked version in detail.  
  `T-t3-02` "It cannot be daunting or overly complex"
- **cap-errors' closed problem registry has no row for a record whose signature is absent or does not verify, so which type does a refused resolve carry?**  
  _deciding evidence:_ cap-errors requires 1-3-1 rather than minting a suffix at the call site, so the three options were: reuse the registered `identity-untrusted`, which is 401 and not retryable but is defined as a delegation chain that does not verify, so a caller repairing a publisher's signature would be reading an identity error; reuse `document-invalid`, which misnames a verification failure as a schema failure; or add two rows, `record-unsigned` (401, not retryable, extension member version) and `record-digest-mismatch` (401, not retryable), to docs/decomposition.md section 2.1.6 and use them. The third is recommended and is what the worked example and the definition of done show, pending those rows.  
  _default until then:_ `urn:agentic:problem:record-unsigned`, marked proposed and pending registration, with `record-digest-mismatch` as its sibling row for a signature that verifies over an edited tree; until the rows land an implementation returns `identity-untrusted` with the version and the verification result in detail rather than inventing a type.  
  `T-t5-02`, `F-b3-13` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation"

