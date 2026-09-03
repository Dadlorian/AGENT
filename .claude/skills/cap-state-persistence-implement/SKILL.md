---
name: cap-state-persistence-implement
description: How to build the State persistence capability on this stack: what the hash-chained line-delimited stores that already run give you and what they cannot give anyone else, a first adapter that adds content-addressed ids, a Merkle tree and sealed heads to the file that exists, a second adapter with a different execution model built from immutable objects under a content address and a compare-and-swap head, the migration between them, where the append path is wired so no writer can bypass it, and a definition of done with the breakage that makes it fail. Load it when writing the code behind append, read_at or prove, when adding a lease to a store that assumed one process, when a conformance run reports a forked log, or when deciding what to do with the file that is already there.
---

# cap-state-persistence-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-state-persistence into something that runs here: one interface, two adapters whose execution models differ, and an existing hash-chained file carried forward rather than replaced. | sourced | `F-b3-17`, `F-b5-05`, `E-capability-state-persistence` "Today a JSONL file with a hash chain" |

## Entities

| Entity |
|---|
| `E-capability-state-persistence` |
| `E-seam-state` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-object-store` |
| `E-swap-candidate-relational` |
| `E-swap-candidate-event-log` |

## Contract

### Shapes (JSON Schema 2020-12)

**StateConformanceReport (proposed shape; the counters the definition of done below asserts on, per adapter)** (proposed; sources: `F-b1-04`, `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:report:0.1",
  "title": "StateConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "records_written",
    "chain_break_at",
    "external_head_matches",
    "inclusion_proof_verified",
    "concurrent_appends_rejected",
    "adapters_run",
    "selected_by"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "jsonl-hash-chain",
        "merkle-object-store"
      ]
    },
    "records_written": {
      "type": "integer",
      "minimum": 0
    },
    "chain_break_at": {
      "type": "integer",
      "minimum": -1,
      "description": "-1 when no break was found; otherwise the index the verifier stopped at."
    },
    "external_head_matches": {
      "type": "boolean",
      "description": "Recomputed by a verifier we did not write, from the stored records alone."
    },
    "inclusion_proof_verified": {
      "type": [
        "boolean",
        "null"
      ],
      "description": "Null means the adapter declares the property unsupported at this stage; false means it tried and failed. The two are never merged."
    },
    "concurrent_appends_rejected": {
      "type": "integer",
      "minimum": 0,
      "description": "Appends refused because the expected head had moved or the fencing token was stale. Zero means the race was never run."
    },
    "tombstone_proof_still_verifies": {
      "type": [
        "boolean",
        "null"
      ]
    },
    "head_digests_equal": {
      "type": "boolean",
      "description": "Set on the merged report: both adapters produced the same head over the same record sequence."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    },
    "selected_by": {
      "const": "configuration",
      "description": "A code edit between runs would not be a swap."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: what runs today is two append-only hash-chained line-delimited stores, a task store and an evidence store, and neither is deleted by this work. The migration adds identity, a tree and a lease to the file that exists; a green-field store would leave the platform running the old one anyway and would make the swap untestable because only one implementation would ever hold real records. | proposed | `F-a5-03`, `F-a5-04` |
| Proposed: the chain is kept and the tree is added over the same values. cap-state-persistence states why the pair of proofs is needed (X-cross-structure-052); the consequence for the build is that the leaves of the tree are the record ids the chain already commits to, so an existing store becomes provable without a single record being rewritten, and a rollback is stopping the tree rather than restoring a file. | proposed | `F-a5-03`, `X-cross-structure-052` |
| Proposed: both adapters implement the identical operation set from cap-state-persistence, and the running adapter is chosen by configuration with no code edit between runs. build-adapter-pair states design rule 3 (F-b1-04); what this adds is that the selection appears in the report shape above, because a swap nobody can observe in the output is indistinguishable from running one adapter twice. | proposed | `F-b1-04` |
| Proposed: the two adapters hold the head in different places and must behave identically at the interface. The file adapter's head is the last line it wrote; the object-store adapter's head is one small object updated by compare-and-swap. Both reject an append whose expected head has moved or whose fencing token is below the highest seen, and the conformance report counts those rejections rather than assuming the race happened. | proposed | `X-cross-structure-048`, `F-b5-05` |
| Proposed: an adapter that cannot yet serve a property declares it unsupported rather than reporting zero. In the report shape above, inclusion_proof_verified is null for the file adapter before the tree lands and false once it tries and fails, and merging those two into one falsy value is precisely how a stage that never ran comes to look like a stage that passed. | proposed | `F-a7-03`, `F-b1-04` |
| Proposed: no writer reaches the store except through append, and the platform stamps the actor, the partition and the correlation attributes onto every record on that one path. A second write path would be a caller deciding for itself whether a record is attributable, which is the property a cross-cutting guarantee does not have, and it would also be the place a fork appears. | proposed | `F-b1-08`, `T-t2-03` |
| Proposed: a refused append, a stale token, a missing record and an unverifiable proof are returned as problem details from the registry cap-errors owns, and this capability mints no failure object of its own; a new registry row is required before any new type is raised. A caller must be able to tell a lost race, which is retryable after re-reading the head, from a broken chain, which is not. | proposed | `F-b4-07` |
| Proposed: every conformance run and its breakage are written to the evidence store in the form build-evidence-record fixes, naming the code version and the tree under test, and stay labelled claimed until they have actually been run here. Nothing in this facet has been executed on this platform. | proposed | `F-a5-04`, `F-part-c-08` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from the file that exists rather than from a new store: the task store already appends JSONL, hash-chained records, so the first three changes are identity, a tree and a lease on that same file, not a replacement for it. | agentic-stack states the chain property this store relies on (F-a5-03) and cap-state-persistence carries it into this capability's open question about cross-run continuity. What this facet adds is the observation that every later step is additive over that file, so each one is revertible on its own and the platform never runs a half-migrated store it cannot read. | sourced | `F-a5-03`, `F-b5-05` "JSONL, hash-chained" |
| 2 | Add content-addressed identity first, while still in the file: compute the record id from the canonical bytes of the body, write it into each record, and keep the sequence number as a position hint rather than as identity. | Proposed. Identity is the change every later step depends on: the tree's leaves are record ids, the tombstone preserves a record id, and two adapters can only be compared on the same head if they agree on what each record is called. Doing it inside the file adapter means the object-store adapter is written against a settled identity rather than inventing one. | proposed | `F-b5-05` |
| 3 | Add the append-only Merkle tree over those record ids and write a sealed head at run close carrying the tree size, the root hash and the chain digest; make the closing sealed head of one run the opening head of the next. | Proposed, and it preserves the property the platform already depends on while changing how it is checked: detection stops being a rehash of the whole file and becomes a proof, which is what lets a third party check one record. The sealed head is also the only object the signing path needs, so provenance over state costs one signature per run rather than one per record. | proposed | `F-a5-03`, `X-cross-structure-052` |
| 4 | Add the fencing lease and make every append conditional: the writer states the head it expects and the token it holds, and the store refuses the write if either is behind. Run the two-writer race in the test suite from the day the lease lands. | The check is the general form of what an event store does with a version: it enforces optimistic concurrency control, and this prevents lost updates without requiring locks. Running the race immediately matters because a rejection counter that is never exercised reads exactly like a store that has no lease at all. | sourced | `X-cross-structure-048`, `X-cross-structure-049` "This prevents lost updates without requiring locks" |
| 5 | Build the second adapter over an object store: one immutable object per record named by its content address, the tree persisted as objects, and the head as a single small object updated by compare-and-swap. Do not port the file adapter's assumption that write order is byte order. | Proposed second adapter, per the recorded swap-candidate column. It breaks a different assumption than the first: the file adapter owns one mutable file, finds its head by reading the last line, and rehashes to verify, while this one has out-of-order arrivals, an eventually consistent listing, no cheap full scan, and verification only through proofs. cap-state-persistence records the axis; what this adds is that the object store is chosen over the other two candidates precisely because a relational store would preserve the single-writer, ordered-append assumption rather than test it. | proposed | `F-b3-17`, `F-b1-04` |
| 6 | Migrate in that order and keep both adapters live behind one interface: identity, then tree and sealed heads, then lease, then the object-store adapter selected by configuration. Do not delete the file adapter once the object store works. | Proposed migration. Each step is independently revertible and the store stays readable throughout. Keeping the file adapter is what makes the pair testable later; an interface with one surviving implementation drifts back into the shape of whatever runs, which is the failure design rule 3 exists to catch. | proposed | `F-b1-04` |
| 7 | Wire the cross-cutting concerns onto the single append path: the actor and the correlation attributes are stamped by the platform, the retention class is assigned at write, a tombstone is itself a record, and there is no flag that skips any of it. | Proposed wiring. One path is what makes the guarantee hold whichever entry produced the work, and it is also the cheapest place to enforce retention: a record that arrives without a class is refused at the boundary rather than found later by a sweep that has to guess. | proposed | `F-b1-08`, `T-t2-03` |
| 8 | Make the conformance suite adapter-parameterised from the first line, with one command, one report shape and an external verifier invoked as a subprocess that is given the records and never the store's own reader. | Proposed. A suite written against the file adapter and generalised later encodes byte order and full-scan verification into its assertions, and a suite allowed to call our reader will eventually be satisfied by it, which is the outcome the capability's integrity invariant forbids. | proposed | `F-b1-04`, `F-b5-05` |
| 9 | Proposed: open references/state-adapters.md when you need the per-adapter mapping table, the failure each adapter can and cannot detect, or the step-by-step swap runbook. This skill body is enough to build either adapter without it. | Proposed, progressive disclosure. The mapping table and the runbook are long material that a reader writing the first adapter does not yet need, and inlining them would push the part that decides the design below the fold. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: check that the configured adapter is the one that actually wrote, by reading a record back and looking at its shape, not by reviewing the configuration file. agentic-stack states the finding (F-a7-04) that configuration written in the documented place can be silently overridden; a store is the worst place to learn that late, because the wrong adapter will have been accumulating records the whole time. | proposed | `F-a7-04` |
| Size the verification cost against where this is going, not against where it is. build-evidence-record already cites the store's scale (F-a5-04), ~2,445 records across 308 runs; rehashing that is tractable and rehashing a hundred times that is not, which is the practical half of the reason the tree is added rather than the chain merely tuned. | sourced | `F-a5-04` "~2,445 records across 308 runs" |
| Keep operational state and historical facts in the same log but not in the same record: one search-only record on file says operational workflow state includes execution status, variable values, loop counters, and idempotency keys, and those change often. Write each change as a new fact rather than editing a record, or the store acquires an update path and every proof taken before it becomes a lie. | sourced | `X-cap-state-persistence-006` "execution status, variable values, loop counters, and idempotency keys" |
| Proposed: run the deliberate breakage on a copy of a real store, not on a fixture of ten records. A fixture cannot show whether the verifier stops at the right index or merely reports that something is wrong, and the index is the part a person acts on when a store is actually found to be edited. | proposed | `F-part-c-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | cap-state-persistence already records this role (F-b3-17): JSONL + hash chain is the adapter today. What this facet adds is the staged build on top of the file that exists: record ids over canonical bytes, then a Merkle tree over those ids with a sealed head per run, then a fencing lease with conditional append. Each stage ships on its own and the file stays readable by every existing reader throughout. | Cannot serve a proof at all before the tree lands, and declares that member unsupported rather than reporting zero. Even complete it cannot escape a single mutable file: its head is a byte position, one process owns it, and a reader that wants integrity without the tree must fetch every record. | Additive, in four stages, each revertible by not reading the field the previous stage added; nothing already written is rewritten, because the tree's leaves are ids the chain already commits to. | claimed | `F-b3-17`, `F-a5-03`, `E-adapter-jsonl-hash-chain` "JSONL + hash chain" |
| `E-swap-candidate-object-store` | second | A content-addressed Merkle log over an object store: one immutable object per record named by the digest of its canonical bytes, the tree persisted alongside them, and the head a single small object advanced by compare-and-swap. Proofs are served from the tree, so a consumer verifies one record from the proof and the head alone. | Cannot assume write order, cannot read the previous line to find the head, cannot take a lock on a file, and cannot cheaply scan every record; a listing is eventually consistent and an object may arrive after one written later. It also cannot be made to work if the interface ever grows a full-log rehash, which is why cap-state-persistence forbids one. | cap-state-persistence records the two roles and the axis they differ on (F-b3-17, F-b1-04); what this facet adds is the procedure. Select by configuration only, replay the same record sequence through each, and require the merged report to show adapters_run == 2, selected_by == configuration, head_digests_equal == true, and the file adapter's unsupported members recorded as null rather than asserted false. | claimed | `F-b3-17`, `F-b1-04`, `X-cross-structure-052`, `E-swap-candidate-object-store` "object store · relational · event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P16, extended with the swap: `python3 tools/conformance/state_persistence.py --adapter jsonl-hash-chain --records 1500 --report out/state-a.json` then the same command with `--adapter merkle-object-store --report out/state-b.json`, the adapter chosen by configuration with no code edit between runs. Each run appends the identical 1500-record sequence through the interface, races two writers on one partition at least once, then hands the stored records to an independent verifier we did not write, invoked as a subprocess with no access to our reader. Both reports must validate against the StateConformanceReport shape above and assert, per adapter, `records_written > 1000`, `chain_break_at == -1`, `external_head_matches == true`, `inclusion_proof_verified == true` for a uniformly random record, `concurrent_appends_rejected > 0` and `tombstone_proof_still_verifies == true`. |
| Expected | both runs exit 0; the merged report shows `adapters_run == 2`, `selected_by == "configuration"`, `head_digests_equal == true`, and per adapter `records_written == 1500`, `chain_break_at == -1`, `external_head_matches == true`, `inclusion_proof_verified == true`, `concurrent_appends_rejected == 1`. |
| Deliberate breakage | Edit one record body in place in the store, leaving both adapters, the record sequence and the command untouched. |
| Expected failure | Both runs exit 1: the independent verifier reports a chain break at that index, so `chain_break_at` becomes the edited index, `external_head_matches == false`, and the inclusion proof for that record fails with `inclusion_proof_verified == false`. A run where the object-store adapter still exits 0 means its proof came from a cached head rather than from the stored records, and a run where `concurrent_appends_rejected == 0` means the race never happened and the lease was never tested. Claimed: neither adapter is written, the conformance tool does not exist, and no run has been performed here. The measured starting state is recorded in cap-state-persistence-use, where the reference runner's chain verifies over 56 records and produces zero proofs. |
| Status | claimed |
| Evidence | `F-b5-05`, `F-b3-17` "concurrency and single-writer guarantees" |

## Composes with

Builds on: `cap-state-persistence`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: `cap-state-persistence-use`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which adapter is primary once both exist, and does a deployment with no outbound network get the file adapter or no store at all? | Measure, per adapter: append latency added to the write path, the number of external services that must be reachable for a record to be durable, and whether a consumer holding only a proof and a head can verify without reaching us. The last is the capability's contract; the second decides whether the object store can sit on the hot path. | Proposed: the file adapter stays primary for the per-step append path and the object-store adapter holds sealed heads and anything a third party is expected to verify, both selected by configuration. A deployment with no outbound network runs the file adapter and records the reduced guarantee rather than losing the store. | `F-b1-04` |
| Is the sealed head signed by this capability or by the provenance capability, given that both want the same object? | Whether any consumer needs a signed head without also needing an attestation, and whether the signing identity for a head differs from the one used for an artifact. If neither differs, one signing path serves both and this capability emits an unsigned head. | Proposed: this capability produces the sealed head and stops there; signing is the provenance capability's call over that object, so the store gains no signing key and the swap between adapters stays a storage decision. Reversible: moving the signature here would change which skill owns the key, not the head's shape. | `F-b4-05`, `F-b5-05` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-state-persistence 2831cb4f, 2026-09-03 |
