---
name: seam-state-implement
description: How to build the State seam on this stack: the hash-chained line-delimited task store that already runs, carried forward in stages into one partitioned log with content-addressed records, a fencing lease, a Merkle tree and sealed heads; a second adapter over an object store whose execution model differs; the migration of graph and ledger writes onto one append path; where correlation, identity, policy, provenance, budget and idempotency attach to an append and to a seal; and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code behind append, seal, a projection or a proof, when a component still has its own store, when a resumed run must read its own history, when a conformance run reports a forked chain or a query whose answers drift, and before recording any State seam result as passing.
---

# seam-state-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in seam-state into something that runs here: one append path behind two adapters whose execution models differ, built out of the JSONL, hash-chained store that already exists rather than beside it, so the chain that is the valuable idea survives the move. | sourced | `F-a5-03`, `F-b5-05`, `E-adapter-jsonl-hash-chain` "Today a JSONL file with a hash chain" |

## Entities

| Entity |
|---|
| `E-seam-state` |
| `E-capability-state-persistence` |
| `E-core-component-graph` |
| `E-core-component-ledger` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-object-store` |
| `E-swap-candidate-relational` |
| `E-swap-candidate-event-log` |

## Contract

### Shapes (JSON Schema 2020-12)

**StateSeamConformanceReport (proposed shape; the counters the definition of done below asserts on, one per adapter plus a merged report)** (proposed; sources: `F-b1-04`, `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:seam-report:0.1",
  "title": "StateSeamConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "runs",
    "consistency_proof_verified",
    "external_verifier_exit",
    "projections_checked",
    "distinct_results_per_projection",
    "concurrent_appends_observed",
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
    "runs": {
      "type": "integer",
      "minimum": 2,
      "description": "At least two, because the consistency assertion is between one run's sealed head and the next."
    },
    "consistency_proof_verified": {
      "type": [
        "boolean",
        "null"
      ],
      "description": "Null means the adapter declares proofs unsupported at this stage; false means it tried and failed. Never merged."
    },
    "external_verifier_exit": {
      "type": "integer",
      "description": "Exit code of a verifier we did not write, given the stored records and the two sealed heads, with no access to our reader."
    },
    "projections_checked": {
      "type": "integer",
      "minimum": 0
    },
    "distinct_results_per_projection": {
      "type": "array",
      "items": {
        "type": "integer",
        "minimum": 1
      },
      "description": "One entry per projection: how many distinct answers 100 pinned repeats produced. Every entry must be 1."
    },
    "concurrent_appends_observed": {
      "type": "integer",
      "minimum": 0,
      "description": "Appends the second writer actually landed during the repeats. Zero means the race never ran and nothing was tested."
    },
    "records_migrated": {
      "type": "integer",
      "minimum": 0,
      "description": "Records carried out of the pre-migration store and still readable through the interface."
    },
    "sealed_head_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
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
| Proposed: the build starts from the file that already runs, not from a new store. seam-state records what exists (F-a5-03), a JSONL, hash-chained task store whose closing digest opens the next run; the migration adds identity, kinds, a lease and a tree to that file. A green-field store would leave the platform running the old one anyway, and the swap would be untestable because only one implementation would ever hold real records. | sourced | `F-a5-03`, `F-b5-05` "JSONL, hash-chained" |
| seam-state fixes one log with the graph and the ledger as folds over it (F-b5-04); the build consequence is that the migration is finished only when core-graph and core-ledger have no write path of their own left. Two stores that agree today are two stores that will disagree after the first partial failure, and the point of the move is to make that class of bug unrepresentable rather than monitored. | sourced | `F-b5-04`, `F-b2-06` "the graph and the ledger persist" |
| Proposed: each migration stage ships alone and is revertible by not reading the field the previous stage added, and no record already written is ever rewritten. That is what makes it safe to run the platform half-migrated, and it is only possible because the tree's leaves are the record ids the chain already commits to. | proposed | `F-a5-03`, `F-b5-05` |
| Proposed: both adapters implement the identical operation set seam-state fixes, and the running one is chosen by configuration with no code edit between runs. build-adapter-pair states design rule 3 (F-b1-04); what this facet adds is that the selection is reported in the shape above, because a swap nobody can observe in the output is indistinguishable from running one adapter twice. | proposed | `F-b1-04`, `F-b3-17` |
| Proposed: no component reaches the store except through append, and the platform stamps the actor, the correlation attributes, the policy decision and the attestation reference on that one path. agentic-stack states design rule 7 (F-b1-08); the build consequence is that the append function is the single place a cross-cutting guarantee can be made undeclinable, and it is also the only place a fork could appear, so the two audits are the same audit. | proposed | `F-b1-08`, `T-t2-03` |
| Proposed: an adapter that cannot yet serve a property declares it unsupported rather than reporting a zero. In the report shape above consistency_proof_verified is null before the tree lands and false once it tries and fails; merging those two into one falsy value is exactly how a stage that never ran comes to read as a stage that passed, which agentic-stack records as a measured failure mode (F-a7-03). | proposed | `F-a7-03`, `F-b1-04` |
| Proposed: identity is added at the append path or it is added nowhere, because there is currently no identity field anywhere in the system. Until the delegation chain is real, declared_by is written with the process identity and marked as such rather than left empty, so the migration never produces a backlog of records whose author cannot be recovered. | sourced | `F-a6-05`, `F-b4-01` "No identity field anywhere in the system" |
| Apply build-evidence-record: the conformance run, the breakage and the migration counts go to the evidence store naming the code version and the tree hash under test, and every one of them stays claimed until it has been run here. Nothing in this facet has been executed on this platform; proposed pointer, see that skill. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Read seam-state first and inventory what is actually stored today before changing anything: which files exist, what each record already carries, and which components write directly to them. | The contract is stated once in seam-state and this facet only builds it; and the migration's cost is decided by what is already on disk. build-evidence-record cites the scale to plan against, ~2,445 records across 308 runs, which is small enough to rewrite in place and large enough that a mistake is not recoverable by hand. | sourced | `F-a5-04`, `F-b5-05` "~2,445 records across 308 runs" |
| 2 | Stage 1, inside the existing file: compute each record's id from the canonical bytes of its body, write the id and the kind tag from seam-state's closed list into the record, and keep the line position as a hint rather than as identity. Backfill the existing records read-only, into a new file, and compare the two chains before cutting over. | Proposed. Identity is what every later stage depends on: the tree's leaves are record ids, a tombstone preserves one, and the two adapters can only be compared at all if they agree on what each record is called. Doing it first means the object-store adapter is written against a settled identity instead of inventing one. | proposed | `F-a5-03`, `F-b5-05` |
| 3 | Stage 2, the migration proper: put core-graph's and core-ledger's writes behind one append call partitioned by run, and delete their private write paths in the same change that adds the shared one. Keep their read paths working by serving them as projections. | Proposed sequencing. seam-state states the one-log rule (F-b5-04); the build reason for doing it in one change is that a period with two write paths is a period where the two projections can disagree and no proof covers the gap. A read-side shim keeps the change reviewable, because only the writer moves. | proposed | `F-b5-04`, `F-b2-04` |
| 4 | Stage 3: take a lease with a monotonically increasing fencing token per run, make every append state the head it expects, refuse the write when the head has moved or the token is behind, and land the two-writer race test in the same change. | seam-state states the conditional-append rule from the event-store prior art (X-cross-structure-048), where two concurrent writers trying to append at the same version will fail, and one will need to retry. The build addition is the ordering: shipping the lease without the race test gives a rejection counter that nobody has ever seen increment. | sourced | `X-cross-structure-048`, `X-cross-structure-049` "two concurrent writers trying to append at the same version will fail, and one will need to retry" |
| 5 | Stage 4: build the append-only Merkle tree over the record ids, write a head-sealed record at run close, and put an external verifier into the pipeline as a subprocess that is handed the stored records and the two sealed heads and nothing else. | Proposed. seam-state requires proofs an outsider can take rather than a self-report (X-cross-structure-053); the build consequence is that the verifier must be a separate program from the start, because a verifier sharing our reader would pass on a store our reader cannot see is broken. The sealed head is also the only object the signing path needs, so provenance over state costs one signature per run. | proposed | `X-cross-structure-052`, `F-b4-05` |
| 6 | Stage 5: implement the eight projections with a required at_head, add per-projection snapshots labelled with the head they were taken at, and grep the tree for any read that resolves the head itself. Every hit is either converted or is the deliberate breakage. | Proposed. seam-state makes design rule 5 checkable by pinning every read (F-b1-06); at build time the failure is always the same shape - one convenience call that resolves the head internally - and it is invisible until a writer is running concurrently, which is exactly what the definition of done arranges. | proposed | `F-b1-06`, `F-b5-05` |
| 7 | Build the second adapter over an object store: one immutable object per record named by its content address, the tree persisted as objects, the head one small object advanced by compare-and-swap. Do not port the file adapter's assumption that write order is byte order. | build-adapter-pair requires the second adapter to break a different assumption (F-b1-04); the object store does, because it has out-of-order arrivals, an eventually consistent listing, no cheap full scan and verification only through proofs. A relational store would have preserved the ordered-append assumption rather than tested it, which is why it is the recorded alternative and not the choice. | sourced | `F-b1-04`, `F-b3-17` "Every interface ships with at least two adapters" |
| 8 | Wire the cross-cutting guarantees into append and seal rather than into callers: correlation attributes and the actor on every record, the policy decision as a policy-decided record written before the first metered call, spend as ledger-entry records, the attestation reference as attestation-recorded, and the idempotency claim read back through the prior_result projection. | Proposed wiring. seam-state states that the platform stamps these on the one write path (F-b1-08). The build detail worth stating is the ordering guarantee each cross-cutting check asserts on - policy before spend, attestation before release - which is only assertable because all of them are records in one totally ordered partition. | proposed | `F-b1-08`, `F-b4-08` |
| 9 | Run the conformance suite in the definition of done over both adapters, then run the breakage, and write both outcomes to the evidence store labelled claimed or measured according to whether they were actually executed on a clean tree. | agentic-stack states the rule this criterion is built to satisfy (F-part-c-04, F-a7-03), and build-definition-of-done and build-evidence-record turn it into the two runs and the label: the label follows the run rather than the intent. A measurement from a dirty tree is not reproducible, and a green suite whose race never happened is the failure mode this seam is most likely to ship. | sourced | `F-part-c-04`, `F-a7-03` "A criterion nothing can fail is not a criterion" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Confirm which adapter actually wrote by reading a record back and looking at its shape, not by reviewing the configuration file. agentic-stack records that configuration written in the documented place was silently discarded (F-a7-04), and a store is the worst place to learn that late, because the wrong adapter will have been accumulating real records the entire time. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Proposed: run the deliberate breakage against a copy of a real store, not a fixture of ten records. A fixture cannot show whether the verifier stops at the right index or merely reports that something is wrong, and the index is the part a person acts on when a store is found to have been edited. | proposed | `F-part-c-04` |
| Proposed: keep the evidence store out of the migration. It is append-only JSONL with its own record shape and its own owner in build-evidence-record, and folding it into the state log would put measurements about the platform inside the thing being measured. Two logs with different jobs is not the two-stores problem seam-state forbids, which is about one fact split across two writers. | sourced | `F-a5-04`, `F-b5-04` "Append-only JSONL" |
| Proposed: treat the first sealed head as the migration's cut line and keep the pre-migration file readable, unchanged, beside it. A rollback is then stopping the tree and reading the old file, not restoring a backup, and the report's records_migrated count is checkable against a file nobody has rewritten. | proposed | `F-a5-03` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | seam-state records this role (F-b3-17): the store that runs is a hash-chained append-only line-delimited file with one writer. What this facet adds is the staged build on it - record ids over canonical bytes and kind tags, then one shared append path for graph and ledger writes, then the fencing lease, then the tree and the sealed head, then pinned projections - each stage shipping on its own with the file readable by every existing reader throughout. | Cannot serve a proof before the tree lands, and says unsupported rather than zero while it cannot. Even complete it is one mutable file: the head is a byte position, one process owns it, redaction means rewriting the file, and a consumer that wants integrity without the tree must be handed every record. | Additive in five stages, each revertible by not reading the field the previous stage added. The pre-migration file stays beside the new one until the first sealed head verifies under both adapters. | claimed | `F-b3-17`, `F-a5-03`, `E-adapter-jsonl-hash-chain` "JSONL + hash chain" |
| `E-swap-candidate-object-store` | second | A content-addressed Merkle log over an object store with a fencing-lease writer: one immutable object per record, the tree persisted alongside, the head a single small object advanced by compare-and-swap, and inclusion and consistency proofs served in time logarithmic in the log size. seam-state records the pair and the axis; this facet fixes the procedure for running both. | Cannot assume write order, cannot find the head by reading the previous line, cannot take a file lock and cannot cheaply scan every record. It is also unimplementable against any interface that keeps a full-log rehash, which is the assumption the file adapter would have left in the contract had it been built alone. | Select by configuration only, replay the identical record sequence and the identical eight projections through each, and require the merged report to show adapters_run == 2, selected_by == configuration, the same sealed_head_digest for the same sequence, and the file adapter's unsupported members recorded as null rather than asserted false. | claimed | `F-b3-17`, `F-b1-04`, `X-cross-structure-052`, `E-swap-candidate-object-store` "object store · relational · event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.3 row S2, made runnable over the migrated store: `python3 tools/conformance/state_seam.py --adapter jsonl-hash-chain --runs 2 --repeats 100 --report out/seam-state-a.json` then the same command with `--adapter merkle-object-store --report out/seam-state-b.json`, the adapter chosen by configuration with no code edit between runs. Each run asserts: (a) the consistency proof between run N's sealed head and run N+1's sealed head verifies with an external Merkle verifier invoked as a subprocess, given only the stored records and the two heads; (b) each of the eight projections, run 100 times at a fixed `at_head` while a second writer appends to the same run, returns 100 byte-identical results. Both reports validate against the StateSeamConformanceReport shape above and assert `projections_checked == 8`, `concurrent_appends_observed > 0`, `records_migrated > 0` and `selected_by == "configuration"`. |
| Expected | both runs exit 0; per adapter `consistency_proof_verified == true`, `external_verifier_exit == 0`, `distinct_results_per_projection == [1,1,1,1,1,1,1,1]`, `concurrent_appends_observed > 0`, and the merged report shows `adapters_run == 2` with the same `sealed_head_digest` under both adapters for the same record sequence. |
| Deliberate breakage | Let one projection - `open_dispatches` - resolve the head itself and read live instead of reading at the `at_head` it was passed. Same adapters, same record sequence, same command. |
| Expected failure | Exit 1 under both adapters: that projection's 100 results diverge as soon as the concurrent writer appends, so its entry in `distinct_results_per_projection` rises above 1 while assertion (a) still passes, isolating the fault to the query surface rather than to the integrity mechanism. Two further readings are failures rather than passes: `concurrent_appends_observed == 0` means the race never ran, and `records_migrated == 0` means the suite exercised a fresh store instead of the migrated one. Claimed: neither adapter is written, tools/conformance/state_seam.py does not exist, no migration has been performed, and nothing here has been run on this platform. |
| Status | claimed |
| Evidence | `F-b5-05`, `F-b1-06`, `F-part-c-04` "concurrency and single-writer guarantees" |

## Composes with

Builds on: `seam-state`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is the writer one process per run, or a lease service that any process may take a token from? | Measure, over the recorded run history, how many runs are concurrent at peak and how often a writer pauses long enough to be presumed dead. If concurrency is low and pauses are rare, a process per run needs no lease service at all and the token is bookkeeping. | Proposed: a lease with a fencing token from the first stage, whoever holds it. The token costs one integer per record and it is the only thing that survives a writer that pauses, is presumed dead and wakes up; adding it later would mean re-deciding the shape of every record already written. | `F-b5-05` |
| Which projections may be served from a snapshot on the hot path, given that a snapshot is a cache with a head on it? | Measure fold time per projection over the migrated store at the head sizes reached in practice. A projection whose fold is already fast does not earn a snapshot, and every snapshot is another thing that can be served at the wrong head. | Proposed: none at first. Ship the projections as folds, add a snapshot only where a measurement shows the fold on the planning path, and label every snapshot with the head it was taken at so serving it to a differently pinned query is a type error rather than a silent wrong answer. | `X-seam-state-004`, `F-b1-06` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session seam-state 2831cb4f, 2026-09-03 |
