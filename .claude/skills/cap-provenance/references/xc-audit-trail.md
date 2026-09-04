---
name: "xc-audit-trail"
description: "The audit trail as a guarantee rather than a habit: every action attributable to an actor and its delegation chain, the whole run reachable by one correlation id, the record chained so interference shows, and kept for a stated period - all of it applied by the platform from records it already writes, never logged by the caller. Load it when someone asks who did this and under whose authority, when a reviewer needs everything that happened under one identifier, when an integrity check is only ever run by the same process that writes, when a retention period is about to be picked with no obligation named, when an outsider has to be able to check the record without our credentials, and when a system of record is being confused with the operational signal that watches it."
---

# xc-audit-trail (folded into `cap-provenance`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix what makes a record of what happened evidence rather than a log: attributable to an actor and a delegation chain, reachable by correlation id, chained so that interference is detectable, retained for a stated period, and produced by the platform from the ledger, identity, provenance and correlation guarantees it already applies. cap-provenance settles what a signed statement is, xc-provenance-chain settles that one exists for every artifact, seam-state settles how the log is written and sealed; this guarantee settles that the resulting record answers who, under whose authority, in which run, and that someone other than us can check it. | sourced | `F-b4-03`, `F-b4-05`, `T-t2-03`, `E-concern-identity` "Every action names an actor, including delegated agent actors. Delegation chains are explicit" |

## Entities

| Entity |
|---|
| `E-concern-identity` |
| `E-concern-telemetry` |
| `E-concern-provenance` |
| `E-provisioning-concern-task-store` |
| `E-provisioning-concern-evidence-store` |
| `E-standard-in-toto` |
| `E-standard-dsse` |
| `E-standard-slsa` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-in-toto` | Statement v1 (unverified) | unverified | https://github.com/in-toto/attestation | `F-b3-12`, `X-cross-structure-050`, `X-end-to-end-052` |
| `E-standard-dsse` | unverified | unverified | - | `F-b3-12`, `X-cross-structure-050` |
| `E-standard-slsa` | v1.1, unverified | unverified | https://slsa.dev/spec/v1.1/ | `F-b3-12`, `X-end-to-end-051` |

- `E-standard-in-toto` version note: cap-provenance owns this row (F-b3-12) and this skill repeats it only because the retained evidence an outsider checks is a statement in this format; a search-only record names the statement type and the specification was not fetched from this environment, so the version stays unverified.
- `E-standard-dsse` version note: cap-provenance owns this row; no record on file names a version, the envelope format is named rather than versioned. It matters here because the envelope is what lets a third party check a retained statement without holding our keys.
- `E-standard-slsa` version note: One search-only record on file names v1.1; cap-provenance's open question records the disagreement with v1.0 and owns the row. Nothing was fetched here, so no level is claimed anywhere in this skill.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| trail (proposed operation set; the recorded standards fix document and envelope formats rather than a set of calls, and seam-state owns the log these operations read) | a selector - one correlation id, run id or actor - and a pinned head (proposed) | the ordered audit entries matching the selector, each naming its actor, delegation chain, action, outcome and the sealed head it falls under; deterministic at that head, so the same selector and head always give the same answer (proposed) | proposed | `F-b4-03`, `F-b4-06` |
| scan (proposed; the independent monitor, run on a schedule rather than on request) | two heads bounding a window, and the identity the monitor runs under, which is not the identity that appends (proposed) | a monitor report carrying entries_checked, chain_breaks, inclusion_proofs_checked, consistency_proofs_checked, oldest_retained_entry_age_days and the problem documents raised; the report is itself appended, so a monitor that did not run is visible as a gap (proposed) | proposed | `X-cross-structure-053`, `F-a7-03` |
| evidence (proposed; what leaves the platform for someone who holds none of our credentials) | one entry id, held by a party who has the entry and nothing else (proposed) | the entry, its inclusion proof, and the signed sealed head covering it, fetchable and checkable with a verifier we did not write; no payload body and no criterion travels with it (proposed) | proposed | `F-b4-05`, `X-end-to-end-052` |

### Shapes (JSON Schema 2020-12)

**audit-entry (proposed summary shape; the full entry, the monitor report, the three worked entries and the worked rejection are in references/usage.md)** (proposed; sources: `F-b4-03`, `X-xc-audit-trail-002`, `X-xc-audit-trail-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:audit-trail:entry:0.1",
  "title": "AuditEntry",
  "description": "Proposed. A projection of records the platform already writes, never a second thing a caller logs. It carries identifiers, digests and decisions; it never carries a payload body or a grading criterion.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "entry_id",
    "prev_entry_id",
    "chain_digest",
    "occurred_at",
    "actor",
    "delegation_chain",
    "action",
    "outcome",
    "correlation",
    "retention_class"
  ],
  "properties": {
    "entry_id": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "prev_entry_id": {
      "type": [
        "string",
        "null"
      ],
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "chain_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "occurred_at": {
      "type": "string",
      "format": "date-time"
    },
    "actor": {
      "type": "string",
      "description": "user:, agent:, service: or schedule:, spelled the way the identity capability spells it."
    },
    "delegation_chain": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Explicit hops, root workload identity last. Empty is not a valid value; a direct action is a chain of one."
    },
    "action": {
      "type": "object",
      "description": "What was attempted: kind, the target named by digest or id, and the policy decision that admitted or refused it."
    },
    "outcome": {
      "enum": [
        "allowed",
        "denied",
        "succeeded",
        "failed"
      ]
    },
    "correlation": {
      "type": "object",
      "required": [
        "run_id",
        "root_dispatch_id",
        "correlation_id"
      ]
    },
    "sealed_head": {
      "type": "string",
      "description": "The sealed head this entry falls under. seam-state owns the sealing; this field only names it."
    },
    "retention_class": {
      "enum": [
        "chain",
        "body",
        "payload"
      ]
    }
  }
}
```

**monitor-report (proposed summary shape; the fields the definition of done asserts on, expanded in references/usage.md)** (proposed; sources: `X-cross-structure-053`, `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:audit-trail:monitor-report:0.1",
  "title": "AuditMonitorReport",
  "description": "Proposed. One report per scheduled scan, appended to the same trail it scans. Counts are asserted on directly, because an empty window and a clean window produce the same exit code.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "scanned_at",
    "from_head",
    "to_head",
    "entries_checked",
    "chain_breaks",
    "independent",
    "scheduled"
  ],
  "properties": {
    "scanned_at": {
      "type": "string",
      "format": "date-time"
    },
    "from_head": {
      "type": "string"
    },
    "to_head": {
      "type": "string"
    },
    "entries_checked": {
      "type": "integer",
      "minimum": 0
    },
    "actors_missing": {
      "type": "integer",
      "minimum": 0
    },
    "correlation_missing": {
      "type": "integer",
      "minimum": 0
    },
    "chain_breaks": {
      "type": "integer",
      "minimum": 0
    },
    "inclusion_proofs_checked": {
      "type": "integer",
      "minimum": 0
    },
    "consistency_proofs_checked": {
      "type": "integer",
      "minimum": 0
    },
    "external_verifications": {
      "type": "integer",
      "minimum": 0,
      "description": "Checks completed by a verifier we did not write, with our own reader unavailable."
    },
    "oldest_retained_entry_age_days": {
      "type": "integer",
      "minimum": 0
    },
    "retention_floor_days": {
      "type": "integer",
      "minimum": 0
    },
    "entry_kinds_seen": {
      "type": "array",
      "items": {
        "enum": [
          "user",
          "agent",
          "service",
          "schedule"
        ]
      },
      "description": "TARGET T6.2's four entries as the identity capability spells the actor prefix, not T1's three ways in: a window with no schedule-originated entry has not been checked over a door that starts root work."
    },
    "independent": {
      "type": "boolean",
      "description": "Read from the identity and credentials the scan actually ran under, never from the configuration that selected them."
    },
    "scheduled": {
      "type": "boolean",
      "description": "True only when the scan was started by a schedule entry rather than by a request."
    },
    "problems": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": "Typed problem documents raised by this scan; cap-errors owns the object."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every entry names an actor, including delegated agent actors, and its delegation chain is explicit rather than implied by nesting. An entry whose actor is null is not a weak entry, it is a hole: nothing downstream can attribute the action, and no retention or proof machinery repairs it later. | sourced | `F-b4-03`, `E-concern-identity` "Every action names an actor, including delegated agent actors. Delegation chains are explicit" |
| The trail is queryable by correlation id because correlation rides on explicit attributes, not trace parentage, stamped on every entry at the point the platform writes it. A trail that can only be read by walking parent links reproduces the failure A7 finding 1 records, one level down: the entries exist and cannot be gathered. | sourced | `F-b4-06`, `E-concern-telemetry` "Correlation rides on explicit attributes, not trace parentage" |
| Tamper-evidence is a property of the record plus something that reads it, never of the writer alone. build-definition-of-done states the sentence that a transparency log is tamper-evident but not tamper-proof (X-cross-structure-053); the consequence here is that the scheduled independent scan is part of this guarantee rather than an operational extra, since the point of monitoring is ensuring that the transparency log satisfies the desired properties of immutability and being append-only. | sourced | `X-cross-structure-053` "ensuring that the transparency log satisfies the desired properties of immutability and being append-only" |
| agentic-stack states design rule 7: telemetry, policy, provenance and budget are applied by the platform, not requested by the caller. xc-enforcement-chain names the structure that carries this at admission, dispatch and call: an entry has no field for an audit call, an audit flag or an exempt list because there is no field for a bypass of any slot at all. This guarantee's consequence is narrower and specific - the trail is a projection over what four of those six slots already wrote (`identity.resolve` for the actor and delegation chain, `policy.decide` for the outcome, `provenance.open` for the sealed head, `telemetry.open` for the correlation triple), never a second logging call bolted beside them. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| An audit trail is not telemetry, and the difference is stated rather than assumed: an audit trail can be complete yet still be easy to alter, while a tamper-evident trail is designed to reveal interference. One prior-art record on file describes such a trail as capturing who invoked an AI agent, which tool it called, what policy decision was made, and when it happened, for forensic reconstruction, compliance review, and incident response. | sourced | `X-xc-audit-trail-003`, `X-xc-audit-trail-001` "An audit trail can be complete yet still be easy to alter, while a tamper-evident trail is designed to reveal interference." |
| Proposed, the operational consequence of that difference: telemetry may sample, may drop under load, may expire on a short window and may be exported best-effort, because a missing span degrades a signal. The trail may do none of those, because a missing entry is itself the finding. Where the two disagree the trail wins, and a run that could not append an entry does not proceed as though it had. Research query: is there a record contrasting telemetry's sampling/best-effort export behaviour against an audit trail's no-loss requirement, rather than this skill inferring the contrast from telemetry's own correlation clause (F-b4-06)? | proposed | `F-b4-06`, `X-xc-audit-trail-003` |
| Retention is stated per class with a named obligation behind it, never inherited from whatever the store defaults to. One record on file names a concrete floor in one regime: under the EU AI Act, high-risk AI systems must automatically log events across their entire lifetime, and deployers must retain those logs for at least six months. Which regime a deployment falls under is a question this skill records rather than answers, and seam-state owns the three retention classes the floor is applied to. | sourced | `X-end-to-end-049`, `X-end-to-end-050` "high-risk AI systems must automatically log events across their entire lifetime, and deployers must retain those logs for at least six months" |
| What an outsider can verify is the whole point, and it is narrower than what we can verify. cap-provenance fixes the criterion and xc-provenance-chain applies it artifact by artifact, both resting on the same clause (F-b4-05) that a record is verifiable with a tool we did not write; what this guarantee adds is that the object checked is an inclusion proof against a signed sealed head, not our own reader rehashing our own file. A rehash by our reader is a claim about our copy, and it is exactly the evidence a party who distrusts us cannot use. | sourced | `F-b4-05`, `E-concern-provenance` "verifiable with a tool we did not write" |
| Proposed: this guarantee owns two persisted artifacts beyond the ledger it reads, neither of which the blueprint's state inventory names today - the scan operation's monitor report (entries_checked, chain_breaks, inclusion_proofs_checked, consistency_proofs_checked, oldest_retained_entry_age_days, appended on its own schedule) and the evidence operation's evidence bundle (one entry, its inclusion proof and the signed sealed head, handed to a party who holds none of our credentials). Recorded here as a row the blueprint's own review should carry too, since enumeration before pruning is the first rule of that lens. Research query: has the blueprint's state inventory actually been re-run since this row was written to confirm the monitor report and evidence bundle are still absent from it, or is the gap only asserted here? | proposed | `X-cross-structure-053`, `F-a7-03`, `F-b4-05` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: there is no write operation on this interface. Nothing a caller, an agent or a workflow can call appends an entry, edits one, marks one as not audit-relevant or suppresses one, because an interface that lets the audited party write the audit is a formatting convention rather than a guarantee. Research query: does any fetched (not search-only) audit-log specification state read-only-to-callers as an explicit requirement, rather than this row deriving it from design rule 7's general non-optionality? | proposed | `F-b1-08`, `F-b4-01` |
| The criterion a result is judged against never appears in an entry, a monitor report or an evidence bundle. agentic-stack states design rule 6 (F-b1-07), and cap-provenance and cap-scheduling carry the same sentence for their own records; the consequence here is that an entry over a judged action records the actor, the action and the verdict and stops there, so reading one's own audit trail is not a way around the grader rule. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Derive the trail from records the platform already writes - ledger entries, policy decisions, dispatch observations, attestations - rather than adding a logging call anywhere. If a kind of action is missing from the trail, add it to what the platform records, never to what the caller is asked to remember. | agentic-stack states design rule 7 (F-b1-08): guarantees are applied, not requested. A trail assembled from caller-side logging is complete exactly where callers were diligent, which is the one property an audit trail cannot be allowed to have. | sourced | `F-b1-08`, `F-b4-01` "The platform applies each; a caller cannot decline them." |
| 2 | Stamp actor, delegation chain and the correlation triple onto every entry at the moment the platform writes the underlying record, and index by correlation id so one identifier gathers the whole run across components. | Correlation rides on explicit attributes, not trace parentage, and identity requires the delegation chain to be explicit. Stamping later means stamping from whatever context survived, which is where a sub-agent's actions become unattributable. | sourced | `F-b4-06`, `F-b4-03` "Correlation rides on explicit attributes, not trace parentage" |
| 3 | Fix the entry field set against prior art before inventing one: the minimum operational fields a log-management guide names, plus the agent-specific fields the audit-trail draft on file names, plus this platform's correlation triple and delegation chain. | One record on file says at minimum each event should capture timestamp, event, status, and/or error codes, service/command/application name, user or system account associated with an event; another describes a format with explicit fields for agent identity, action classification, outcome tracking, and trust level reporting. Between them they cover what a reviewer asks for, and neither had to be guessed. | sourced | `X-xc-audit-trail-005`, `X-xc-audit-trail-002` "explicit fields for agent identity, action classification, outcome tracking, and trust level reporting" |
| 4 | Chain each entry to its predecessor and record which sealed head it falls under; leave the write model, the sealing, the inclusion and consistency proofs and the retention classes to seam-state and name them rather than restating them here. | agentic-stack states the property the chained store that runs today already gives (F-a5-03), where each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable. The consequence here is that reimplementing the chain inside the audit layer would give the platform two integrity mechanisms that can disagree, and a reviewer no way to tell which one to believe. | sourced | `E-provisioning-concern-task-store`, `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| 5 | Run the scan as a scheduled entry under its own identity and read-only credentials, not as a function the writer calls at the end of an append, and have it read a window between two heads rather than the current state. | cap-scheduling owns the recurrence declaration and the schedule entry this uses. What is new here is why it must be a schedule: the guarantee is that something other than the writer looks, and a check invoked by the writer inherits every failure the writer has. | sourced | `X-cross-structure-053`, `F-b3-15` "it becomes important to have a tool to monitor the transparency log for any evidence of tampering" |
| 6 | Append the monitor report itself to the trail, and assert on its counts - entries_checked, actors_missing, correlation_missing, chain_breaks, consistency_proofs_checked - rather than on the scan's exit status. | agentic-stack states the structurally-green-gate finding (F-a7-03): those establish well-formedness, not correctness. What this guarantee adds, as its own consequence and proposed: a scan over an empty window reports exactly what a clean window reports, and a monitor whose runs are not themselves recorded cannot be shown to have run at all. | sourced | `F-a7-03`, `F-a5-04` "Those establish well-formedness, not correctness" |
| 7 | On a detected break, emit a typed problem document naming the entry and the two heads, and stop treating the window as verified; do not repair the chain, and do not let a scan that failed be retried until it passes. | Proposed. A break is a finding about the record, not a transient condition, so the honest response is a typed refusal that a machine can route rather than a retry that eventually produces a green line. The suffix urn:agentic:problem:audit-chain-broken is proposed and pending registration in the closed registry; until it has a row, the scan returns the registered adapter-unavailable problem and names the break in detail, because a store whose chain does not verify cannot be relied on to serve. Research query: is there a fetched source recommending stop-scanning-until-fixed over retry-until-green for a detected chain break specifically, or is that this row's own reasoning about what a break means? | proposed | `F-b4-07`, `X-cross-structure-053` |
| 8 | Publish sealed heads and retained statements where a party holding none of our credentials can fetch them, and prove the path by running at least one check with our own reader unavailable. | cap-provenance sets the criterion and xc-provenance-chain states it for artifact digests (F-b4-05): every artifact is attributable to the code version, inputs and actor that produced it, verifiable with a tool we did not write. Its consequence for a trail, proposed here, is sharper than for a single artifact - a verification served from our own index proves our index is self-consistent, which is precisely the claim a party investigating us would not accept. | sourced | `F-b4-05`, `X-end-to-end-052` "Every artifact is attributable to the code version, inputs and actor that produced it, verifiable with a tool we did not write" |
| 9 | State the retention floor per class in one place, name the obligation it comes from, and have the scan assert the oldest retained entry is at least that old rather than assuming expiry never ran. | A floor with no named obligation is a guess that nobody can review; one record on file names a management-system standard whose obligations map closely to record-keeping (Article 12) and the other regulation articles around it, which is the kind of citation a retention number needs. Asserting the age turns the policy into something a run can fail. | sourced | `X-end-to-end-050`, `X-end-to-end-049` "record-keeping (Article 12)" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Give the monitor its own identity and its own schedule, and check both from the report rather than from the configuration. agentic-stack states the silently-overridden-configuration finding (F-a7-04): a monitor declared as independent in a file is not a monitor that ran independently. What it adds here, as this guarantee's own consequence and proposed: independence is the one property this guarantee cannot verify after the fact. | sourced | `F-a7-04`, `X-cross-structure-053` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Do not describe the trail as tamper-proof. What is on file is that such records are engineered so that post-event changes, deletions, or gaps are detectable, preserving evidentiary value; detectable is a smaller and more defensible claim than prevented, and the smaller claim is the one the mechanism actually supports. | sourced | `X-xc-audit-trail-001` "post-event changes, deletions, or gaps are detectable, preserving evidentiary value" |
| Retain the verifier alongside the evidence. Proposed: a statement kept for six months whose verification tool, key material or format reader has moved on in the meantime is retained rather than verifiable, so record the verifier version in the monitor report and re-run one historical verification on every scan. Research query: is there a fetched record on verifier/key-material obsolescence for long-retained signed evidence (e.g. in-toto or DSSE key-rotation guidance), rather than this row reasoning from the general six-month retention floor alone? | proposed | `X-end-to-end-049`, `F-b4-05` |
| Keep claimed and measured apart when talking about your own chain, the way build-evidence-record fixes it: our reader recomputing our own digests is a measurement of our file and a claim about everything else. Say which of the two a green line is before offering it to anyone outside. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Watch for the gap rather than the edit. A chain makes an alteration detectable, but the cheapest attack on a trail is a run that never wrote an entry at all, so pair the chain check with a coverage check - actions observed against entries present - and treat an unexplained absence as the same severity as a broken digest. | sourced | `X-xc-audit-trail-001`, `F-a7-03` "post-event changes, deletions, or gaps are detectable" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/xc-audit-trail/test.sh |
| Expected | exit 0, `passed 18, failed 0`, and the scan line `chain_breaks=0 entries_checked=24 adapters_run=1 independent=False scheduled=False`. The gate reads every entry in the window, asserts on the counters rather than on an exit code, and its tamper case shows a chain break being named rather than passed over. Claimed, and the counters themselves state the gap: `entries_checked=24` against the 100 this facet asserts, `independent=False` and `scheduled=False` because no monitor identity and no schedule exist here, no retention floor is measured (`oldest_retained_entry_age_days >= 180` is asserted nowhere), no third-party in-toto/DSSE verifier is invoked with our own reader unavailable, and `entry_kinds_seen` covering user, agent, service and schedule is not checked. `tools/conformance_audit_trail.py` does not exist; this gate, which xc-audit-trail-implement owns, is the nearest thing that runs. The criterion above was run on 2026-09-03 and exited 0. |
| Deliberate breakage | Flip one byte inside a historical entry that the window covers - one character of an actor name is enough - leave every other entry untouched, and let the monitor reach its next scheduled run. |
| Expected failure | `chain_breaks` becomes 1, the scan names the entry whose chain digest no longer verifies, exits non-zero and emits the typed problem document, while `entries_checked` stays at or above 100 and `actors_missing` stays 0 - which is what shows the failure is the altered record rather than a window that was never read. Claimed: no audit entry, monitor, schedule or conformance tool exists on this stack today. The nearest analogue that does run here was measured separately over this repository's own chained run ledger and is recorded in the adapter row of xc-audit-trail-implement. |
| Status | claimed |
| Evidence | `F-part-c-04`, `X-cross-structure-053` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-evidence-record`, `build-research-record`, `build-ceremony`, `cap-provenance`, `cap-scheduling`, `core-ledger`, `xc-provenance-chain`, `seam-state`, `xc-enforcement-chain`

Used by: `xc-audit-trail-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The append-only Merkle log specification whose inclusion and consistency proofs this guarantee leans on, the management-system standard behind the retention floor and the regulation that sets it have no E-standard- entity in the knowledge base, so none can be entered in contract.standards. How should they be recorded until then? | 1-3-1 applied (TARGET T5), the same protocol xc-provenance-chain applied to the same gap for the log specification: (a) add the entities and rebuild the knowledge base, which invalidates the provenance heads of every skill already written; (b) name each in capability and regime terms in the invariants and instructions, citing the search-only records that name them, and record the missing entities here; (c) leave them unnamed, which would leave the retention floor with no stated source. Recommendation followed: (b). | Each is named in capability or regime terms with no version asserted, because every record naming them is a search result rather than a page that was read. The question closes at a ceremony that adds the entities during a rebuild. | `T-t5-02`, `X-end-to-end-050` "When a problem comes up, use 1-3-1" |
| The closed problem-type registry in docs/decomposition.md section 2.1.6 has no row for an integrity failure found in the record itself. What type does a detected chain break return? | The row this skill would add is `\| audit-chain-broken \| 500 \| no \| The audit monitor found an entry whose chain digest does not verify \|`: not retryable, because rescanning the same window returns the same break, and not a policy refusal, because nothing was denied. cap-errors owns the registry and the object, and core-ledger already states the clause it rests on (F-b4-07, F-b3-13) that failures are typed and machine-readable, never parsed from prose; the suffix here is proposed and pending registration until a row exists. | The scan returns the registered adapter-unavailable problem with the break named in detail, which is the closest registered row: a store whose chain does not verify cannot be relied on to serve. The cost of that fallback is that it reads as retryable, which this failure is not, and that is the argument for the row. | `F-b4-07`, `F-b3-13` "Typed and machine-readable. Never parsed from prose" |
| Does the trail need a copy outside our control, or is a signed sealed head published to a third party enough? | Prior art on file describes a distributed ledger system that creates an immutable record of transactions across a network of computers, which removes our ability to withhold the record entirely, at the cost of publishing what we hold. Decide by counting how many entries could be published at all once payload bodies and correlation identifiers are excluded, and whether any party actually needs the entries rather than the proof. | Proposed: publish signed sealed heads and serve entries on request against them, rather than replicating the trail. Reversible: replicating later changes where an entry is fetched from and nothing the scan asserts on. | `X-xc-audit-trail-004`, `F-b4-05` "an immutable record of transactions across a network of computers" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-audit-trail 2831cb4f, 2026-09-03 |
