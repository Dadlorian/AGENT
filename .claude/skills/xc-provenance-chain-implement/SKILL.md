---
name: xc-provenance-chain-implement
description: How to close the provenance chain on this stack: a first enforcement point that binds a statement at release and sweeps for orphans over the append-only records that already exist, a second that moves the refusal out of our process to the store that accepts the result, the migration from a tree where nothing is attested and nothing is counted, where correlation, identity, policy, budget and typed failures attach to a binding, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that records an attestation for an output, when a result can be published while its statement is still queued, when deciding what the second enforcement point should be, when an orphan sweep passes on one enforcement point and fails on the other, or when a report says zero orphans and nobody can say over how many artifacts.
---

# xc-provenance-chain-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the closure guarantee xc-provenance-chain states into two enforcement points on this stack, chosen the way build-adapter-pair requires, selectable by configuration, with a migration that never leaves a window in which an output can be released unattested, and a run that can actually fail. | sourced | `F-b1-04`, `F-b4-05` "Every interface ships with at least two adapters" |

## Entities

| Entity |
|---|
| `E-concern-provenance` |
| `E-capability-provenance` |
| `E-adapter-jsonl-evidence-records` |
| `E-swap-candidate-any-attestation-store` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines; the axis names are its closed enum)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:pair-axes:0.1",
  "title": "ProvenanceChainPairAxes",
  "description": "Proposed. The three axes on which the two enforcement points differ, stated as properties rather than as product names. measured stays false until the swap has been executed and recorded as evidence.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "locus_of_durability_and_verification",
        "today_value": "a local append-only file whose integrity our own reader recomputes",
        "second_value": "a store outside the writing process, queried and checked by a party holding none of our credentials",
        "measured": false
      },
      {
        "axis": "processes_required_for_progress",
        "today_value": "none beyond the writer; the sweep reads records that are already on disk and can run long after the release",
        "second_value": "the store must be reachable at release, and an unreachable store refuses the release rather than deferring it",
        "measured": false
      },
      {
        "axis": "result_or_claim_ticket",
        "today_value": "a completed orphan count over a corpus that was already written, so an orphan is detected after it exists",
        "second_value": "an accepted write returned at release, so the orphan is never created in the first place",
        "measured": false
      }
    ]
  ]
}
```

**provenance-chain conformance report (proposed; written once per enforcement point and once across them, and the fields the definition of done asserts on)** (proposed; sources: `F-a7-03`, `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:conformance-report:0.1",
  "title": "ProvenanceChainConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. The sweep report of xc-provenance-chain plus the two fields only a pair run can carry, so a green run names what it checked and on which enforcement point rather than only its exit code.",
  "required": [
    "adapter",
    "artifacts_checked",
    "attestations_matched",
    "orphans",
    "entry_kinds_seen",
    "enforcement_point_observed"
  ],
  "properties": {
    "adapter": {
      "type": "string",
      "description": "The entity id of the enforcement point under test."
    },
    "at_head": {
      "type": "string"
    },
    "artifacts_checked": {
      "type": "integer",
      "minimum": 0
    },
    "attestations_matched": {
      "type": "integer",
      "minimum": 0
    },
    "orphans": {
      "type": "integer",
      "minimum": 0
    },
    "orphan_digests": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "external_resolutions": {
      "type": "integer",
      "minimum": 0,
      "description": "Resolutions served from the published statement with our own store unreachable."
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
      }
    },
    "enforcement_point_observed": {
      "type": "string",
      "description": "Read from what actually refused or accepted the release, never from the binding that selected the adapter."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two enforcement points differ on three of build-adapter-pair's axes, per the shape above, and the difference that matters is when the orphan can exist at all: the first counts orphans that were already created, the second refuses the write that would create one. A second store of the same shape, swept the same way, would prove nothing. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| xc-provenance-chain states the guarantee, the record shape and the zero-orphan criterion (F-b4-05), and build-adapter-pair states the rule this pair is built under (F-b1-04). What this skill adds on this stack is that neither enforcement point is the guarantee: the guarantee is the assertion that runs over both, and a chain closed only where the sweep happens to run is a chain that has not been shown to close. | sourced | `F-b4-05`, `F-b1-04` "Swappability is a tested property, not an intention." |
| agentic-stack states that Part A is substrate (F-part-c-11). Its consequence here: the append-only records that already exist are not replaced, they become the payload the first enforcement point signs over, so the migration adds a statement and a sweep rather than a second store. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| Proposed: the migration has no window in which an output can be released unattested. The sweep runs in shadow and reports orphans while nothing yet refuses; the release path begins refusing only once the shadow sweep has reported zero orphans over a full corpus; the store admission is turned on last, with the release-path refusal still in place. At no step is the only thing standing between an output and an orphan a check that was just switched off. | proposed | `F-b4-05`, `T-t2-03` |
| agentic-stack states design rule 1 (F-b1-02). Its consequence here: which enforcement point refused a release is configuration, and no component above the release path may branch on it. The conformance report carries enforcement_point_observed precisely so that the branch lives in a test rather than in the platform. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| build-evidence-record owns what a record of a run must contain (F-a5-04). What this adds: every statement in this skill about how an enforcement point behaves is claimed until such a record exists for it, and a claim is never upgraded to a measurement by rewording the sentence that makes it. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the first enforcement point inside the release path: at the moment a result is assembled, collect its artifact digests, obtain a statement for each through the attestation capability, append one attestation-recorded record per subject digest into the append-only store that already exists, and only then publish the result. | The store that runs today is append-only and already records the code version and tree under test for every run - build-evidence-record owns what that record contains (F-a5-04) - so the record this guarantee needs is a new kind in a writer that exists rather than a new store. Binding inside the release path is what makes the sweep an audit of something enforced rather than the enforcement itself. | sourced | `F-a5-04`, `F-b3-12` "Append-only JSONL" |
| 2 | Proposed: build the second enforcement point at the store that accepts the result. Offer the result together with the subject digests it references; the store refuses the write unless a statement is already resolvable for every one of them, and returns the registered adapter-unavailable problem when it cannot check. | Proposed. Moving the refusal outside our writing process is what breaks the first enforcement point's assumption that the same code both creates the obligation and decides whether it was met. It also changes when an orphan can exist: under the first it exists until the sweep finds it, under the second it is never written. | proposed | `F-b1-04`, `F-b3-12` |
| 3 | Proposed: migrate in four steps with no gap - wrap what the append-only store already writes into a statement without changing the release path; run the sweep in shadow and report orphans while nothing refuses; switch the release path to refuse once a full corpus reports zero; enable the store admission last, leaving the release-path refusal in place. | Nothing is attested and nothing is counted today, so the first two steps buy the number that tells you whether the third is safe. Turning refusal on before the count exists means discovering the corpus's real orphan rate as a wave of refused releases. | proposed | `F-part-c-11`, `F-b4-05` |
| 4 | Wire the cross-cutting attachments identically at both enforcement points: stamp the run identifier and the root dispatch identifier onto every attestation-recorded record as explicit attributes, carry the actor and a reference to its delegation chain, key the binding by subject digest so a replayed release produces no second statement, and count the signing cost against the root unit's ceiling. | xc-provenance-chain states the same wiring rule for the guarantee (T-t2-03): every cross-cutting concern is managed across the entire structure whichever entry point was used. Its consequence at the enforcement points is concrete - a record that carries the digest but not the run cannot be joined to anything, and a replayed release that mints a second statement turns one artifact into two attributions. | sourced | `T-t2-03` "every cross-cutting concern are managed across the entire structure, whichever entry point was used" |
| 5 | Read enforcement_point_observed from what actually accepted or refused the release rather than from the configuration that selected it, and put that observed value in the conformance report. | agentic-stack's silently-discarded-configuration finding, measured on this host: 'configuration written in the documented place was silently discarded.' A report that names the enforcement point it was told to use cannot tell a real swap from a configuration that silently fell back, which is the one thing a pair run exists to establish. | sourced | `F-a7-04` "Configuration written in the documented place was silently discarded" |
| 6 | Apply build-definition-of-done: run the definition of done below over both enforcement points with the same corpus and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the structurally-green-gate finding (F-a7-03). What it adds here: a pair run over a corpus containing no artifacts reports zero orphans twice and looks like proof of a swap, so assert artifacts_checked and adapters_run before reading the orphan count as good news. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack already states the silently-overridden-configuration finding (F-a7-04). What it adds here: an enforcement point selected in a configuration file is not the enforcement point that ran, so read it back from the refusal, which is exactly what enforcement_point_observed is for. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| xc-provenance-chain's closure line is cap-provenance's contract, 'verifiable with a tool we did not write' (F-b4-05), which a queued-but-unwritten statement cannot yet satisfy: do not let a queued binding become an accepted design. A statement that is promised and not yet written is indistinguishable from a missing one to everyone downstream, and the queue is where a chain quietly stops closing under load rather than under a bug. | sourced | `F-b4-05` "verifiable with a tool we did not write" |
| agentic-stack's structurally-green-gate finding (F-a7-03) applies to a pair run as much as to a single sweep: 'Those establish well-formedness, not correctness' when a corpus contains nothing to check against. Prefer widening the corpus over widening the assertion - the cheapest way to make a chain look closed is to sweep only the artifacts the release path already attests; sample from what consumers actually hold instead, and let the orphan count be a surprise while surprises are still cheap. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-evidence-records` | today | The adapter PASS.md B3 records for this capability is JSONL evidence records, and PASS.md A5 records that store as append-only with each record naming the script hash, the commit and the tree under test. The first enforcement point binds inside the release path and writes one attestation-recorded record per subject digest into that store, then sweeps it at a pinned head to count orphans. cap-provenance owns the statement itself; this row records only where the closure is enforced. | Cannot stop an orphan from existing: the sweep runs over records already written, so between a release and the next sweep an unattested output is indistinguishable from an attested one. Its integrity is a rehash by our own reader over a file we hold, so it also cannot answer the question a third party is asking. | Select the enforcement point by configuration with no code edit between runs, replay the identical corpus through each, and merge the per-adapter reports; the merged report must show adapters_run >= 2 and enforcement_point_observed read from the refusal rather than the binding. xc-provenance-chain owns the criterion; this row records the roles PASS.md B3 fixes. | claimed | `F-b3-12`, `F-a5-04`, `E-adapter-jsonl-evidence-records` "JSONL evidence records" |
| `E-swap-candidate-any-attestation-store` | second | The recorded swap candidates for this capability are a keyless-signing service or any attestation store. The second enforcement point takes the second of those and puts the refusal in it: the store accepts a result only when a statement is already resolvable for every subject digest the result references, so the closure is checked by a process that did not produce the output. | Cannot admit a release while it is unreachable, where the first enforcement point needs nothing beyond the local writer and can bind offline; and it cannot see an artifact that never reaches it, so it bounds what is written to it rather than everything a unit produced. The axis the pair is chosen for is when an orphan can exist at all: detected after the fact by our own sweep, against refused at the moment of the write by a process outside ours. That is a different execution model, not a different product of the same shape. | Run the identical conformance corpus against it with the store standing in for the release-path check, and assert the same three numbers plus external_resolutions greater than zero with our own store unmounted. Design rule 3 is stated by agentic-stack and by build-adapter-pair (F-b1-04); what is new here is the axis, not the rule. | claimed | `F-b3-12`, `F-b1-04`, `E-swap-candidate-any-attestation-store` "Sigstore · any attestation store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first enforcement point (docs/decomposition.md section 3.4 row X4): `python3 tools/conformance_provenance_chain.py --adapter today --adapter second --corpus out/results.jsonl --at-head <sealed head> --min-artifacts 100 --report out/provenance-chain.json`, the enforcement point selected by configuration with no code edit between runs. It replays the same corpus of at least 100 artifacts through each enforcement point and asserts, per point, that every artifact digest referenced by a result has an attestation-recorded record whose subject_digest matches it, that `entry_kinds_seen` contains all three of TARGET T1's ways in, that `external_resolutions > 0` with our own store unmounted, and that `enforcement_point_observed` was read from the accept or the refusal rather than from the binding. Across points it asserts `adapters_run >= 2`, `artifacts_checked >= 100` and `orphans == 0`. |
| Expected | exit 0 and one line per enforcement point of the form `adapter=<entity> artifacts_checked=100 attestations_matched=100 orphans=0 external_resolutions=<n> entry_kinds_seen=user,agent,service enforcement_point_observed=<entity>`, followed by `adapters_run=2`. |
| Deliberate breakage | Emit an output without recording an attestation: remove the attestation-recorded append from one release path, push the same corpus through it unchanged, and re-run the command exactly as written. |
| Expected failure | The orphan count becomes non-zero: `orphans` becomes 1 under the first enforcement point, which reports the unattested subject digest and exits non-zero, while the second refuses the release outright and returns the registered adapter-unavailable problem instead of writing, so the same breakage surfaces as a count on one point and as a refused write on the other. `adapters_run` stays 2 and `artifacts_checked` stays at or above 100, which is what shows the failure is the missing statement rather than one point having failed to run. Claimed: neither enforcement point is built, no attestation-recorded record is written anywhere on this stack today and the conformance tool does not exist, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-05` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `xc-provenance-chain`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the release-path refusal stay on once the store admission is enabled, or does it become redundant? | Measure how many releases never reach the store at all: an artifact written to a unit's own filesystem and referenced by a result never crosses the store boundary, so the store admission cannot see it. If that count is non-zero on a representative workload, the release-path check is the only one covering those and stays. | Proposed: both stay on. The store admission is the stronger check where it applies and the release-path check is the wider one, and build-adapter-pair's rule (F-b1-04) cuts the other way here - removing either before the count exists would be removing a check because a newer one looked better. | `F-b4-05`, `F-b1-04` "the second exists to prove the first is not load-bearing" |
| How does a sweep prove zero orphans over artifacts that have been retained past the point where their bodies were deleted? | Whether the digest and the statement reference survive a retention tombstone while the body does not; the retention classes in docs/decomposition.md section 2.2.4 keep chain headers forever and delete bodies, which would leave the digest resolvable and the payload gone. Confirm that against a real tombstoned record before relying on it. xc-provenance-chain applies the same 1-3-1 protocol to its own missing standard entities (T-t5-02). | Proposed: the sweep asserts on digests and statement references only, so a tombstoned body leaves the orphan count unchanged. Recorded here rather than assumed, because a sweep that needs the body would start failing at day 401 for reasons no reader would connect to retention. | `F-b4-05`, `T-t5-02` "When a problem comes up, use 1-3-1" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-provenance-chain 2831cb4f, 2026-09-03 |
