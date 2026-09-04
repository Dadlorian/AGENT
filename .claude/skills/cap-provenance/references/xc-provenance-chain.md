---
name: "xc-provenance-chain"
description: "The provenance chain as a closure guarantee: every artifact digest a result hands back has a signed statement over exactly that digest, recorded before the result is released, so the orphan count is zero. Load it when an output is about to leave the platform, when deciding where the statement is produced and what refuses a release without one, when a sweep reports nothing wrong over a corpus that contained nothing, when someone asks how an outsider could tell that this file came from that run, when a result names a document, a file or a model output nobody can account for, when a store's own rehash is being offered as proof, and when a review asks whether a human entry, an agent entry and an event entry all leave the same trail."
---

# xc-provenance-chain (folded into `cap-provenance`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the closure half of provenance: cap-provenance settles what a statement is and how an outsider checks one, build-evidence-record marks the same boundary from the other side by keeping note-taking out of attestation (F-b4-05), and this guarantee settles that a statement exists for every artifact digest that leaves, applied by the platform at the point of release rather than requested by whoever produced the output. | sourced | `F-b4-05`, `F-b1-08`, `E-concern-provenance` "verifiable with a tool we did not write" |

## Entities

| Entity |
|---|
| `E-concern-provenance` |
| `E-capability-provenance` |
| `E-standard-in-toto` |
| `E-standard-dsse` |
| `E-standard-slsa` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-in-toto` | Statement v1 (unverified) | unverified | https://github.com/in-toto/attestation | `F-b3-12`, `X-xc-provenance-chain-001`, `X-xc-provenance-chain-007` |
| `E-standard-dsse` | unverified | unverified | https://secure-systems-lab.org/ | `F-b3-12`, `X-xc-provenance-chain-002` |
| `E-standard-slsa` | v1.0, unverified | unverified | https://slsa.dev/spec/v1.0/provenance | `F-b3-12`, `X-xc-provenance-chain-003` |

- `E-standard-in-toto` version note: cap-provenance owns this row (F-b3-12); it is repeated here because the chain guarantee's join key is the Statement's subject and nothing else. A search-only record names the Statement and its Subjects; the specification was not fetched from this environment, so the version stays unverified.
- `E-standard-dsse` version note: No version string appears in any record on file: the envelope format is named, not versioned. cap-provenance owns this row; it matters here only because the envelope is what lets a third party check a statement without holding our keys.
- `E-standard-slsa` version note: One search-only record on file names the v1.0 provenance predicate and the subject binding; cap-provenance's open question records a second record naming v1.1 and leaves the disagreement open. Neither specification was fetched here, so the version stays unverified and no level is claimed anywhere in this skill.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| bind (proposed operation set; the recorded standards fix a document format rather than a set of calls, and cap-provenance owns the attest call this one wraps) | a result about to be released, the set of artifact digests it references, and the actor and code version that produced them | one attestation-recorded record per subject digest, appended in the same write as the result, or a typed refusal that stops the release (proposed) | proposed | `F-b4-05`, `X-xc-provenance-chain-003` |
| sweep (proposed) | a corpus of results read at one pinned state head (proposed) | artifacts_checked, attestations_matched and orphans, where an orphan is an output digest with no statement whose subject matches it (proposed) | proposed | `F-b4-05`, `F-a7-03` |
| resolve (proposed) | one artifact digest, held by someone who has the bytes and nothing else (proposed) | the statement whose subject is that digest and the sealed head it was recorded under, fetchable without our credentials so the check can be run by a tool we did not write (proposed) | proposed | `F-b4-05`, `X-xc-provenance-chain-002` |

### Shapes (JSON Schema 2020-12)

**attestation-recorded (proposed summary shape of the record kind named in docs/decomposition.md section 2.2.1; the full record, the sweep report and the expanded worked instances are in references/provenance-chain-shapes.md)** (proposed; sources: `F-b4-05`, `X-xc-provenance-chain-001`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:attestation-recorded:0.1",
  "title": "AttestationRecorded",
  "description": "Proposed. One record per subject digest. This is the only machine-readable field set the orphan sweep reads, which is why it carries digests and references and never payloads.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "subject_digest",
    "statement_ref",
    "envelope_digest",
    "actor",
    "code_version",
    "run_id",
    "recorded_at"
  ],
  "properties": {
    "subject_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "The join key between an artifact and the statement that vouches for it. Matched by digest over canonical bytes, never by name, path or timestamp."
    },
    "statement_ref": {
      "type": "string",
      "description": "Where a party who does not hold our credentials fetches the signed statement."
    },
    "envelope_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "actor": {
      "type": "string",
      "description": "The producer, spelled the way the identity capability spells it: user:, agent:, service: or schedule:."
    },
    "code_version": {
      "type": "string"
    },
    "run_id": {
      "type": "string"
    },
    "sealed_head": {
      "type": "string",
      "description": "The state head this record was sealed under. seam-state owns the sealing; this field only names it, so the chain guarantee and the log guarantee stay separable."
    },
    "recorded_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

**worked instances, one per T6.2 door (TARGET T6.2 names four doors and the same record shape covers all four, which is the whole claim)** (sourced; sources: `T-t6-02`, `T-t2-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:instances:0.1",
  "title": "AttestationRecordedInstances",
  "description": "Four records produced by the same binding, differing only in the actor that entered the system. Nothing in the shape, the sweep or the refusal branches on which door was used.",
  "type": "array",
  "items": {
    "$ref": "urn:agentic:xc:provenance-chain:attestation-recorded:0.1"
  },
  "examples": [
    [
      {
        "subject_digest": "sha256:1f0a4c2d9b7e5613a8c04f2e6d13b8a75c9e02f4a61d8b3c7e50f9a2d64b81c3",
        "statement_ref": "attest://run-human-0001/stmt-01",
        "envelope_digest": "sha256:9c31b7d0e5a24f68c1de73f0a2b95c48d6e70a13f5c92b84d0e17a36c48b9f52",
        "actor": "user:corey",
        "code_version": "git:8f3c1a2",
        "run_id": "run-human-0001",
        "sealed_head": "head:4b7e...",
        "recorded_at": "2026-09-03T10:14:02Z"
      },
      {
        "subject_digest": "sha256:2b8e01c7d4a9f36502be7c1d8a0f45e93c26b7d1058fa9e3b47c02d16e8a5f70",
        "statement_ref": "attest://run-agent-0042/stmt-07",
        "envelope_digest": "sha256:5d92c48b0e17a3f6c81de07b34a95f2c6e8017d4b93a0c5f2e64d18b70a9c3f5",
        "actor": "agent:planner-01",
        "code_version": "git:8f3c1a2",
        "run_id": "run-agent-0042",
        "sealed_head": "head:4b7e...",
        "recorded_at": "2026-09-03T10:16:41Z"
      },
      {
        "subject_digest": "sha256:3c7d19a0b6e24f85d1c0378ae59b2f46071da8c3f9e50b27a4c86d10f35b7e92",
        "statement_ref": "attest://run-event-0007/stmt-02",
        "envelope_digest": "sha256:7a05c3e91d48b60f2c7ea15d039b48c7f20e6a91d53c087b4f62a19c05d38e7b",
        "actor": "service:git-webhook",
        "code_version": "git:8f3c1a2",
        "run_id": "run-event-0007",
        "sealed_head": "head:4b7e...",
        "recorded_at": "2026-09-03T10:19:08Z"
      },
      {
        "subject_digest": "sha256:4d8e20b1c7f35a96e2d1489bf60c3a75d1e02f8b7c04d61a9e3f75b02c68d914",
        "statement_ref": "attest://run-schedule-0001/stmt-01",
        "envelope_digest": "sha256:8b13d04c7e29a5f1c60de83b04a95f2c6e7108d4b93a0c5f2e64d18b70a9c3f6",
        "actor": "schedule:nightly-fault-sweep",
        "code_version": "git:8f3c1a2",
        "run_id": "run-schedule-0001",
        "sealed_head": "head:4b7e...",
        "recorded_at": "2026-09-03T02:00:07Z"
      }
    ]
  ]
}
```

**refused release (proposed worked rejection; the type is the registered adapter-unavailable row of the closed registry in docs/decomposition.md section 2.1.6, and cap-errors owns the object)** (proposed; sources: `F-b4-07`, `F-b4-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:refusal-instance:0.1",
  "title": "RefusedReleaseInstance",
  "description": "Proposed. The one failure this guarantee returns, shown rather than described: no statement could be produced over the output digest, so the release was refused instead of emitted unattested. It is a problem object, never prose, and it is retryable because the signer being unreachable is a condition that clears.",
  "allOf": [
    {
      "$ref": "urn:agentic:problem:0.1"
    }
  ],
  "examples": [
    {
      "type": "urn:agentic:problem:adapter-unavailable",
      "title": "No attestation could be produced for the output",
      "status": 503,
      "detail": "result res-0007 references sha256:3c7d19a0b6e2... and no statement could be signed over it; the release was refused rather than emitted unattested",
      "retryable": true,
      "retry_after_s": 30,
      "correlation": {
        "run_id": "run-event-0007",
        "correlation_id": "corr-event-0007"
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| docs/decomposition.md section 3.4 row X4, made precise as an operationalisation of cap-provenance's per-artifact clause - 'the code version, inputs and actor that produced it, verifiable with a tool we did not write' - applied to the whole set of a result's outputs rather than to any one of them: every artifact digest referenced by a result has an attestation-recorded record whose subject digest matches it, and the number of orphans is zero. An orphan is an output digest with no statement over it, and it is the only failure mode this guarantee exists to make impossible. | sourced | `F-b4-05`, `T-t2-03` "code version, inputs and actor that produced it, verifiable with a tool we did not write" |
| cap-provenance owns what a statement is, what it must contain and what counts as an outside check, and build-evidence-record owns the note a reader of this repo gets instead (F-b4-05). What this guarantee adds is the closure over that contract: not that a statement can be produced for an artifact, but that one exists for every artifact, which is a property of the set of outputs rather than of any one of them. | sourced | `F-b4-05`, `E-concern-provenance` "verifiable with a tool we did not write" |
| agentic-stack states design rule 7 (F-b1-08). Its consequence here: no request shape carries an attest flag, a skip list or an unattested mode, and a producer that would rather not be attributed has no field in which to say so. A guarantee with an off switch is a default. | sourced | `F-b1-08`, `F-b4-01` "applied by the platform, not requested by the caller" |
| Proposed: the boundary between the three provenance skills is fixed and load-bearing. Producing and signing the statement belongs to cap-provenance; chaining a recorded attestation to a sealed log head belongs to seam-state; this guarantee owns only the completeness relation between the digests a result names and the statements that exist. Merging any two of the three is how a store's own integrity check ends up quoted as an outside check. Research query: is there a fetched source drawing this exact three-way boundary (producing/signing, chaining-to-a-log-head, completeness), or is that this skill's own decomposition of the provenance concern? | proposed | `F-b4-05`, `X-xc-provenance-chain-006` |
| The subject digest is the only join key. A statement is matched to an artifact by digest, never by file name, path, run label or timestamp, because those are the fields that keep pointing at something after the bytes change. The framework this platform adopts already binds a statement to Subjects rather than to names. | sourced | `X-xc-provenance-chain-003`, `X-xc-provenance-chain-001` "associates it with the built artifact via the subject field" |
| An artifact that has been attested is not thereby verified. What the recorded standards buy is that a check exists at all, performed automatically by tools against verifiable metadata; a chain nobody sweeps is a chain whose orphans have simply not been counted yet, and the count is the guarantee. | sourced | `X-xc-provenance-chain-005` "Verification is performed automatically by tools against verifiable metadata." |
| agentic-stack already states the structurally-green-gate finding (F-a7-03). Its consequence here, as this skill's own proposed consequence: a sweep that found no mismatches over a corpus containing no artifacts reports exactly what a clean sweep reports, so artifacts_checked is asserted alongside orphans and neither number is ever inferred from an exit code. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| When a statement cannot be produced, the release is refused and the caller receives the registered adapter-unavailable problem object shown above; cap-errors owns the object and its closed type registry (F-b4-07). Emitting the output anyway and reconciling later would make the orphan count a lagging report rather than an enforced zero. | sourced | `F-b4-07`, `F-b4-05` "Typed and machine-readable. Never parsed from prose" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the artifact bytes never enter a record or a statement, only their digest. The consequence for this guarantee specifically is that the orphan sweep needs read access to no payload at all, so the check that proves accountability is not itself a disclosure. Research query: is there a fetched source stating a provenance record must carry only digests and never payload bytes as a security property (versus a size or performance rationale), or is that this skill's own reading of cap-provenance's contract? | proposed | `F-b4-05` |
| There is no field anywhere that names which outputs are exempt: no exemption list, no attest:false, and no per-caller policy that turns the binding off - 'the platform applies each; a caller cannot decline them' (F-b4-01) - because a guarantee whose scope a caller can edit is a request. | sourced | `F-b4-01`, `F-b1-08` "The platform applies each; a caller cannot decline them" |
| The criterion a result was judged against never appears in a subject name, a predicate or a sweep report. agentic-stack states design rule 6 (F-b1-07); the consequence here is that a statement over a judged output records the verdict and the digests and stops there. | sourced | `F-b1-07` "The grader is never visible to the graded." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | At the moment a result is assembled, enumerate every artifact digest it references and treat that set as an obligation list: each member needs a statement before the result is released. | Proposed. The orphan is created at release, not at production, so the only place the set is knowable and still changeable is where the result is put together. Enumerating later means enumerating from whatever survived. Research query: is there a fetched source recommending an obligation-list model captured at result-assembly time specifically, or is that this row's own reasoning about when the artifact set is still knowable? | proposed | `F-b4-05` |
| 2 | Bind each digest by calling the attestation capability cap-provenance defines and appending one attestation-recorded record per subject digest in the same write as the result, never on a best-effort queue behind it. | Proposed. A separate queue turns a guarantee into a race: the result is visible and the statement is not yet written, which is exactly the window in which an orphan is indistinguishable from a pending append. Research query: is there a fetched source arguing against a best-effort attestation queue specifically (versus the same-write requirement cap-provenance already states generally), or is that this row's own extension of it? | proposed | `F-b4-05`, `X-xc-provenance-chain-003` |
| 3 | Wire the binding once at the boundary results leave through, not once per producer, and prove it by replaying one corpus through each of TARGET T1's three ways in: a human entering the system, an agent entering the system, and an internal or external event entering the system. | A cross-cutting concern is managed across the entire structure whichever entry point was used, so a binding wired only on the door someone remembered is declinable by choosing another door. Replaying one corpus through each is what turns 'cannot be declined' into a count. | sourced | `T-t2-03`, `T-t1-01`, `T-t1-02`, `T-t1-03` "every cross-cutting concern are managed across the entire structure, whichever entry point was used" |
| 4 | Refuse the release with the registered adapter-unavailable problem object above when no statement can be produced, and leave the result unpublished rather than publishing it with a note that attestation is pending. | Proposed. A published output with a pending statement is an orphan under a friendlier name, and every downstream consumer that copies it inherits the orphan without inheriting the note. Research query: is there a fetched source recommending refuse-rather-than-publish-pending for an unattested release specifically, or is that this row's own extension of the closure requirement? | proposed | `F-b4-07`, `F-b4-05` |
| 5 | Run the sweep as a standing check at a pinned head and report artifacts_checked, attestations_matched and orphans as numbers, then assert on all three rather than on the exit status. | agentic-stack already states the structurally-green-gate finding (F-a7-03); the consequence for a sweep, stated here as this skill's own and proposed, is that an empty corpus and a clean corpus produce the same green, and only the count of artifacts actually examined separates them. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| 6 | Resolve each orphan candidate through the published statement reference rather than through our own record index, and run at least one sampled resolution with our store unreachable. | cap-provenance sets the criterion that the check is performed by a tool we did not write (F-b4-05); the consequence for the sweep is that a resolution served from our index proves the index is complete, which is a different claim from the one this guarantee makes. | sourced | `F-b4-05`, `X-xc-provenance-chain-005` "inputs and actor that produced it, verifiable with a tool we did not write" |
| 7 | Record which sealed head each attestation-recorded record was written under, and leave the sealing itself, the inclusion proof and the consistency proof to seam-state. | An append-only Merkle log supplies inclusion and consistency proofs, and those belong to the log guarantee. Naming the head here is what lets a reader move from an artifact to a proof without this guarantee growing a second copy of the log's machinery. | sourced | `X-xc-provenance-chain-006` "RFC 9162 defines an append-only Merkle log with inclusion and consistency proofs." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Monitor the store rather than trusting it. A transparency log records every signature in a non-modifiable way, and that property is worth exactly as much as the frequency with which someone checks it; schedule the sweep, do not run it on demand when a reviewer asks. | sourced | `X-xc-provenance-chain-004` "transparency log recording every signature in a non-modifiable way" |
| Hash a canonical form, not a serialisation. A canonical byte form is what lets two independent writers agree that two spellings of the same object are the same subject, and without it the join key silently stops joining the moment a field order changes. | sourced | `X-xc-provenance-chain-006` "RFC 8785 defines JSON Canonicalization Scheme for canonical byte form to hash." |
| Keep the statement portable enough that the check survives losing us: attestations produced by one tool can be verified by another tool, without shared infrastructure or vendor lock-in. A chain whose verification needs our reader is a chain we are asking people to take on trust. | sourced | `X-xc-provenance-chain-007` "attestations produced by one tool can be verified by another tool, without shared infrastructure or vendor lock-in" |
| agentic-stack already states the silently-overridden-configuration finding (F-a7-04). What it adds here, as this skill's own proposed consequence: a binding declared in a hook file is not a binding that ran, so prove the chain by observing an attestation-recorded record for a digest you just produced, never by reading the configuration that says one should exist. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Say what the record claims rather than calling it proof. An attestation is a digitally signed document making claims about software artifacts, their origins, processes used to create them, and security measures applied during lifecycle; describing a run's outputs as proven because a record exists overstates every one of those clauses. | sourced | `X-xc-provenance-chain-005` "digitally signed document making claims about software artifacts, their origins, processes used to create them, and security measures applied during lifecycle" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 harness/provenance/conformance.py --adapter dryrun --adapter second |
| Expected | exit 0, last line `conformance PASSED: 26/26 cases, 2 binding(s)`, with one line per binding reading `cases=13 passed=13 emitted=2 verified=1 subject_mismatches=0 orphan_subjects=0 log_inclusion_proofs=1 product_hits=0`: an envelope whose subject digest does not match the artifact is refused, and the artifacts actually examined are counted rather than inferred from the exit code. What this run stands in for: the criterion this facet carried before ceremony 61 (finding R61B-018) moved its prose out of the criterion field, which is the check this guarantee ultimately needs and which nothing on disk runs yet - Proposed tool, built with the first implementation of this guarantee (docs/decomposition.md section 3.4 row X4): `python3 tools/conformance_provenance_chain.py --corpus out/results.jsonl --at-head <sealed head> --min-artifacts 100 --report out/provenance-chain.json`. It reads every result in the corpus at one pinned head, collects every artifact digest each result references, and asserts that each has an attestation-recorded record whose subject_digest matches it byte for byte. It reports `artifacts_checked`, `attestations_matched`, `orphans` and `entry_kinds_seen`, and asserts `artifacts_checked >= 100`, `orphans == 0` and that `entry_kinds_seen` contains all three of the ways in named in TARGET T1, so a chain closed only on one door cannot pass. Expected of that check: exit 0 and one summary line `artifacts_checked=100 attestations_matched=100 orphans=0 entry_kinds_seen=user,agent,service`, with the three entry kinds present so the wiring assertion had something to assert on. |
| Deliberate breakage | sed -i 's/result.subjects_matched, result.subject_mismatches = matched, mismatched/result.subjects_matched, result.subject_mismatches = matched, 0/' harness/provenance/interface.py -- verify() never reports a subject mismatch, so an artifact whose digest differs from the attested subject verifies clean. Restore with git checkout harness/provenance/interface.py. |
| Expected failure | exit 1 on both bindings at the tampered-subject case, which asserts subject_mismatches == 1 and gets 0, while emitted, verified and orphan_subjects hold their values - which is what shows the failure is the lost mismatch rather than a corpus that was never read. Status claimed: tools/measure.py has recorded neither run for this pair here. The breakage the prose criterion above stood for, and what it expected: Emit one output without recording an attestation: remove the attestation-recorded append from a single release path, run the same corpus through it unchanged, and re-run the command exactly as written. The orphan count becomes non-zero: `orphans` becomes 1, the run exits non-zero naming the unattested subject digest and the result that referenced it, and `artifacts_checked` stays at or above 100 - which is what shows the failure is a missing statement rather than a corpus that was never read. Claimed: no attestation-recorded record is written anywhere today, the release path this would attach to is the dispatch boundary that does not yet exist, and the conformance tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-05` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-evidence-record`, `build-skill-authoring`, `cap-provenance`

Used by: `seam-dispatch`, `seam-state`, `xc-audit-trail`, `xc-provenance-chain-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The append-only Merkle log specification and the canonicalization scheme this guarantee leans on have no E-standard- entity in the knowledge base, so neither can be entered in contract.standards without a knowledge-base rebuild, which would invalidate the provenance heads of every skill already written. How should they be recorded until then? | 1-3-1 applied (TARGET T5): (a) add both entities and rebuild the knowledge base, which breaks every written skill's provenance; (b) name both in capability terms in an invariant, an instruction and a best practice, citing the research record that names them, and record the missing entities here; (c) leave them unnamed until a later wave, which would leave the join key and the proof mechanism unstated. Recommendation followed: (b). The question closes at a ceremony that adds the entities as part of a rebuild, at which point each becomes a contract.standards row with version_status unverified until the specification is actually fetched. | Both are named in capability terms only, with no version asserted, because the record naming them is a search result rather than a page that was read. | `X-xc-provenance-chain-006`, `T-t5-02` "When a problem comes up, use 1-3-1" |
| Is one statement emitted per artifact digest, or one statement carrying many subjects per result? | Measure statement volume and signing latency for a representative run against the cost of the coarser grain: a multi-subject statement cannot be published for one subject without publishing the digests of its siblings, which is a disclosure question rather than a performance one. The framework permits either, since a Statement applies to one or more subjects. | Proposed: one statement per result carrying every subject digest it produced, with the per-digest record above as the index into it, because that keeps one signing operation per release while the orphan sweep still reads a row per digest. Reversible: splitting later changes statement_ref and nothing the sweep asserts on. | `X-xc-provenance-chain-001` "applying to one or more software supply chain Subjects" |
| What is an artifact for the purposes of this guarantee: only the outputs a result names, or also every intermediate a step produced and discarded? | cap-provenance owns the contract sentence this question cites (F-b4-05); what is open here is which artifacts fall inside it. Count the intermediates a representative workflow produces and ask which of them another party could ever hold. An intermediate nobody can obtain cannot be presented as evidence of anything, so attesting it buys nothing; an intermediate a step wrote to a shared store can be. | Proposed: every digest a released result references, plus every artifact written to a store outside the unit that produced it. Intermediates confined to a unit's own filesystem are out of scope until one of them is observed leaving. | `F-b4-05` "Every artifact is attributable to the code version, inputs and actor that produced it" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-provenance-chain 2831cb4f, 2026-09-03 |
