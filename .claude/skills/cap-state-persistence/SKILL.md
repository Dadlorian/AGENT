---
name: "cap-state-persistence"
description: "The ideal state of the State persistence capability: put an opaque record somewhere durable, read it back at a pinned snapshot, and hand someone a proof that nothing was changed, without making them hold the whole log. Load it when designing or judging the store behind the graph and the ledger, when deciding what a record's identity is, when two writers could append at once, when a planner needs an answer that will not move underneath it, or when retention and redaction have to coexist with integrity. Also load it when someone proposes proving one record by rehashing the entire file, when a store is called tamper-proof, when a log's file format is being treated as the contract, or when a proposed second implementation is a different database of the same shape."
---

# cap-state-persistence

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for a durable, tamper-evident store of opaque records: append under a head the writer expects, read at a pinned snapshot, and prove one record's membership to a party that holds neither the log nor our code. The graph and the ledger are its consumers, not its vocabulary. | sourced | `F-b5-04`, `F-b3-17`, `E-capability-state-persistence`, `E-seam-state` "**State** — the graph and the ledger persist." |

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

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| append (proposed operation set; no standard fixes a call surface for this capability, so the set below is ours) | an opaque record body, its kind tag, the partition it belongs to, the record id the writer expects to be the current head, and the fencing token the writer holds | the accepted record's content-addressed id and the new head, or a rejection naming which of the two conditions failed: the head moved, or the token is behind one already seen | proposed | `F-b5-05`, `X-cross-structure-049` |
| resolve_head (proposed) | a partition | the current head as tree size, root hash, chain digest and whether it is sealed; this is the only call in the set that is allowed to be non-deterministic, and it is made once before a plan is computed | proposed | `F-b5-05`, `F-b1-06` |
| read_at (proposed) | a selector and a head | the records the selector matches, deterministic at that head: the same head returns the same answer forever, whatever has been appended since | proposed | `F-b5-05`, `F-b1-06` |
| prove (proposed) | a record id and a head | an inclusion proof that the record is in the log at that head, checkable by a party that holds the record, the proof and the head and nothing else; never a re-read of the log | proposed | `X-cross-structure-052`, `F-b5-05` |
| prove_consistency (proposed) | an earlier head and a later head | a proof that the later log extends the earlier one with nothing removed and nothing reordered, which is how a reader who saw the log yesterday checks it today without storing it | proposed | `X-cross-structure-052`, `F-a5-03` |
| redact (proposed) | a record id and the authority under which the body is being removed | a tombstone that keeps the record id and the chain position and drops the body, so every prior proof still verifies; the store has no delete | proposed | `F-b5-05` |

### Shapes (JSON Schema 2020-12)

**StateRecord (proposed summary shape; the full record schema, the planner query table and the retention classes are in references/state-shapes.md)** (proposed; sources: `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:record:0.1",
  "title": "StateRecord",
  "type": "object",
  "required": [
    "record_id",
    "prev_record_id",
    "chain_digest",
    "kind",
    "partition",
    "fencing_token",
    "written_at",
    "body"
  ],
  "properties": {
    "record_id": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest over the canonical bytes of body. Identity, not position."
    },
    "prev_record_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "The head the writer expected. The append is refused if it is not the head."
    },
    "chain_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "kind": {
      "type": "string",
      "description": "An opaque tag. This interface never interprets it; the State seam does."
    },
    "partition": {
      "type": "string",
      "description": "Exactly one writer at a time per partition."
    },
    "fencing_token": {
      "type": "integer",
      "minimum": 0
    },
    "written_at": {
      "type": "string",
      "format": "date-time"
    },
    "body": {
      "type": [
        "object",
        "null"
      ],
      "description": "Null only for a tombstone, where record_id still commits to the original body."
    },
    "retention": {
      "type": "object",
      "properties": {
        "class": {
          "enum": [
            "chain",
            "body",
            "payload"
          ]
        },
        "expires_at": {
          "type": "string",
          "format": "date-time"
        },
        "hold": {
          "type": "boolean"
        }
      }
    }
  }
}
```

**Head: the value every read is pinned to and every proof is taken against** (sourced; sources: `F-a5-03`, `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:head:0.1",
  "title": "Head",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "partition",
    "size",
    "root_hash",
    "chain_digest"
  ],
  "properties": {
    "partition": {
      "type": "string"
    },
    "size": {
      "type": "integer",
      "minimum": 0
    },
    "root_hash": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "chain_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "sealed_at": {
      "type": [
        "string",
        "null"
      ],
      "format": "date-time",
      "description": "Set when the head closes a run. A sealed head is the opening head of the next run."
    }
  }
}
```

**InclusionProof: what prove returns, sized by the log rather than by its content** (sourced; sources: `X-cross-structure-052`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:inclusion-proof:0.1",
  "title": "InclusionProof",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "record_id",
    "leaf_index",
    "head",
    "path"
  ],
  "properties": {
    "record_id": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "leaf_index": {
      "type": "integer",
      "minimum": 0
    },
    "head": {
      "$ref": "urn:agentic:state:head:0.1"
    },
    "path": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^sha256:[0-9a-f]{64}$"
      },
      "description": "Sibling digests from the leaf to the root. Its length grows with the logarithm of the log size, which is the property that makes the proof servable by a store that cannot cheaply read every record."
    }
  }
}
```

**The failure shape (proposed): what a refused write or an unverifiable record looks like [caller's view, folded from cap-state-persistence-use]** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:example:problem",
  "title": "Problem details from this capability",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Failures arrive as RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns; nothing here returns a bare status or a message to be parsed. Both types below are proposed and need rows in that registry before anything may raise them. The distinction that matters to a caller is retryable: a lost race is retried after re-reading the head, a broken chain never is. Both are proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns: until the rows land an implementation returns `idempotency-conflict` for `urn:agentic:problem:head-moved` and `document-invalid` for `urn:agentic:problem:record-unverifiable`, accepting that `idempotency-conflict` is not retryable while a lost race is, which is itself the argument for the head-moved row.",
  "examples": [
    {
      "type": "urn:agentic:problem:head-moved",
      "title": "Another writer advanced the head first",
      "status": 409,
      "detail": "expected head sha256:d09619... but the current head is sha256:50873a...",
      "retryable": true
    },
    {
      "type": "urn:agentic:problem:record-unverifiable",
      "title": "The proof does not check out against the head you supplied",
      "status": 422,
      "detail": "inclusion proof for sha256:0c7ac1... does not reconstruct root sha256:...",
      "retryable": false
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The recorded row for this capability names no standard and forwards to B5 for the design, a hash chain over line-delimited JSON as the adapter today, and an object store, a relational store or an event log as the swap candidates. It is the one row in that table whose standard column is a forward reference rather than a specification, so conformance to somebody else's document is not available as a criterion here. | sourced | `F-b3-17`, `E-capability-state-persistence` "— *(no standard; see B5)* \| JSONL + hash chain \| object store · relational · event log \|" |
| With no standard to conform to, the interface is judged instead by whether it settles the five things the source names: this must specify: the write model, concurrency and single-writer guarantees, the integrity mechanism, retention, and the query surface a planner needs. Anything left open among those five is a gap in the contract, not a decision delegated to the adapter. | sourced | `F-b5-05`, `E-seam-state` "This must specify: the write model, concurrency and single-writer guarantees, the integrity mechanism, retention, and the query surface a planner needs." |
| agentic-stack states that two boundaries have no standard to adopt and that they are the only places original design effort is warranted (F-b5-01, F-b5-06); the consequence for this capability is that original design here is the deliverable rather than an indulgence, and a review asking which specification we failed to adopt is asking the wrong question of this boundary. | sourced | `F-b5-01`, `F-b5-06` "They are the only places original design effort is warranted, and they carry the weight of the platform." |
| One consumer is a core component with a hard requirement: the Ledger is append-only across runs; the deduplication authority. A store that cannot answer whether a key already reached a terminal result, at a head that will not move while the answer is being used, breaks the Ledger rather than merely inconveniencing it. | sourced | `F-b2-06`, `F-b5-04` "append-only across runs; the deduplication authority" |
| Records are opaque here. A record carries a kind tag, canonical bytes, a partition and a retention class, and nothing in this interface knows that one is a graph edge and another a ledger entry. The graph and the ledger are folds over the same log, and that projection belongs to the State seam; a store that grows a graph-shaped query has absorbed a consumer's vocabulary and can no longer be swapped for one that has not. | sourced | `F-b5-04`, `E-seam-state` "the graph and the ledger persist" |
| Proposed: a record's identity is the digest of its canonical bytes, never its position in a file or a row number, so two independent writers reach the same id for the same fact and a holder can check an id without the store. The canonicalisation scheme is fixed in docs/decomposition.md section 2.2.1; naming it here as a governing standard would be a claim this repository has not verified, so the open question below carries it instead. | proposed | `F-b5-05`, `F-b3-17` |
| Concurrency is settled by making every append conditional rather than by trusting that only one process is running: two concurrent writers trying to append at the same version will fail, and one will need to retry. An append names the head it expects and is accepted only if that is still the head, which turns a silently forked log into a rejected write. | sourced | `X-cross-structure-048`, `X-cross-structure-049` "two concurrent writers trying to append at the same version will fail, and one will need to retry" |
| Every read takes a head and is deterministic at it, and there is no default head. This is not ergonomics: agentic-stack states design rule 5 (F-b1-06), which requires cost to be knowable before commitment, and a pure planning function cannot be pure over a store that moves underneath it. A read without a head is the single change that would make rule 5 unprovable for this platform. | sourced | `F-b1-06`, `F-b5-05` "Cost is knowable before commitment.** Planning is a pure function and completes before execution begins" |
| Integrity is judged by what an outsider can do, not by what our own reader reports: the target is a log of which a valid log can be cryptographically verified by any third-party. A check only our code can run is an internal consistency check, and confusing the two is the specific failure this capability exists to prevent. | sourced | `X-cross-structure-052`, `F-b5-05` "a valid log can be cryptographically verified by any third-party" |
| All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach this capability the same way, and enhancing one aspect of it leaves the rest untouched: the store can move from a local file to content-addressed objects, gain proofs, gain a lease and change its retention classes, and a caller holding a head and a proof changes nothing, because a head and a proof are the only things it was ever given. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| No operation returns a judging criterion to the thing being judged. agentic-stack states design rule 6 (F-b1-07); the consequence on this interface is that a verdict record stores the verdict and a reference to the criterion, never the criterion body, and read_at offers no selector that would let a graded agent fetch one. A store that hands back whole bodies by kind would deliver the grader's rule to the graded through the back door while every other rule still passed. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |
| The medium is not part of the contract. Whether a record is a line in a file, a row, an immutable object under a content address or an entry in a stream is invisible to every operation above. A caller that can name a file offset, a table or a bucket has been handed the adapter instead of the interface, and the swap stops being free the moment one does. | sourced | `F-b3-17` "object store · relational · event log" |
| There is no call that rehashes the whole log. Verification is always a proof about one record at one head. An interface whose only integrity operation is a full scan cannot be implemented over a store whose expensive part is reading every record, so exposing one would make the second adapter unimplementable by construction rather than by choice. | sourced | `F-b5-05` "the write model, concurrency and single-writer guarantees, the integrity mechanism" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Begin from the row and the paragraph rather than from a store you already like: write down the five things the source says this design must settle and treat each as a section that has to exist before an implementation is discussed. | A capability that adopts a standard is judged by conformance to it. This one has none, so an explicit list of what must be decided is the only defence against an interface quietly shaped around whatever is running: the source itself names the integrity mechanism, retention, and the query surface a planner needs among them. | sourced | `F-b5-05`, `F-b3-17` "the integrity mechanism, retention, and the query surface a planner needs" |
| 2 | Define the unit as an opaque, kind-tagged fact with canonical bytes, a partition, a retention class and a content-addressed id, and keep every projection out: no graph edge type, no ledger column, no decision field appears in this schema. | Proposed. The moment a projection's vocabulary reaches the record schema, the store and its consumer are one thing, and the second adapter has to reimplement a consumer to be conformant. Opaque records are what make the same interface serve the graph, the ledger and anything a later section adds. | sourced | `F-b5-04`, `F-b3-17` "the graph and the ledger persist" |
| 3 | Make every append conditional on the head the writer expects and carry a monotonic fencing token alongside it; reject an append whose token is below the highest already seen. | It is possible to make an optimistic concurrency check during the append by specifying the version at which you expect the stream to be, and that check is what turns the dangerous case, a writer that paused, was presumed dead and woke up still believing it holds the log, into a rejected write rather than a fork nobody notices until a fold disagrees. | sourced | `X-cross-structure-049`, `X-cross-structure-048` "specifying the version at which you expect the stream to be" |
| 4 | Give every read a required head argument, and make resolve_head the only call whose answer may change between two invocations. | Proposed. Isolating non-determinism in exactly one call is what makes the planner's purity checkable rather than aspirational: pin once, plan against the pin, and any later divergence is attributable to a named call rather than to the store in general. | sourced | `F-b1-06`, `F-b5-05` "the integrity mechanism, retention, and the query surface a planner needs." |
| 5 | Keep the chain and add proofs on top of it: an inclusion proof for one record at a head, and a consistency proof between two heads. Do not replace the chain to get them. | agentic-stack already cites the chain property this platform relies on (F-a5-03), where a JSONL, hash-chained store makes an edit between runs detectable. What proofs add is the thing a chain cannot give cheaply: a valid log can be cryptographically verified by any third-party, one record at a time, without that party ever holding the log. | sourced | `X-cross-structure-052`, `F-a5-03` "a valid log can be cryptographically verified by any third-party" |
| 6 | Split retention into classes with different lifetimes, and make removal a tombstone that preserves the record id and the chain position while dropping the body. | Proposed, and it is what keeps compliance and integrity from becoming a choice between two. The chain and every proof commit to the digest of the body, never to the body, so a body can be replaced by a tombstone and every earlier proof still verifies; a store without that will eventually be asked to delete something and will have to break itself to do it. | sourced | `F-b5-05` "the integrity mechanism, retention" |
| 7 | Judge a candidate implementation on four things and nothing softer: more than a thousand records written through the interface with no fork, an independent verifier recomputing the same head from the records alone, an inclusion proof for a randomly chosen record verifying without the rest of the log, and a body edited in place reported as a break at that index. | build-definition-of-done owns the discipline (F-part-c-04) that a criterion nothing can fail is not a criterion; the consequence for this capability is that the fourth item is not an extra, it is the only one of the four that can fail on a store which happens to be empty, and the first exists so that a green run over three records cannot be mistaken for a result. | sourced | `F-part-c-04`, `F-b5-05` "the deliberate breakage that proves the check can fail" |
| 8 | Send what you were already sending. There is no durability option, no consistency level and no store to name; nothing about persistence is something you opt into. | Proposed usage of the placement this skill fixes. The platform applies this rather than offering it, so a caller-side switch would be a hole rather than a feature, and a caller that could turn it off would eventually be the reason a run cannot be reconstructed. | sourced | `F-b1-08` "applied by the platform, not requested by the caller" |
| 9 | Proposed: open references/state-shapes.md when you need the full record schema, the planner query table with signatures, or the retention class table with its defaults. This skill body is enough to judge an implementation without opening it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The query table alone runs to eight signatures and the record schema past the length at which a contract stops being read; a reader deciding whether a store is acceptable does not need either to decide. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Treat anything that cannot be derived by folding the log from empty as cache rather than state. The Ledger's requirement is to be append-only across runs; the deduplication authority, and a value that only exists because something wrote it to a side table is a value no fold can rebuild after a restart. | sourced | `F-b2-06` "append-only across runs; the deduplication authority" |
| Keep snapshots on the cache side of that line: snapshots are periodically saved states of an aggregate to speed up event replay, which makes them an optimisation that must be rebuildable and discardable, never the record of what happened. | sourced | `X-cross-structure-047` "Snapshots are periodically saved states of an aggregate to speed up event replay" |
| Resist a design that keeps only the latest value, whatever store is underneath: event logs preserve all state transitions as immutable facts, and the platform's questions, what did this cost, has this been done, who decided, are all questions about transitions rather than about the current value. | sourced | `X-cap-state-persistence-003` "Event logs preserve all state transitions as immutable facts" |
| Spend real design effort here rather than treating the store as plumbing: one search-only record on file reports a 2026 agent-engineering survey that ties more than 60% of production incidents to state management. Read that as a reason this boundary earns original design, not as a measurement of this platform, which has not been surveyed. | sourced | `X-cap-state-persistence-005` "ties more than 60% of production incidents to state management" |
| Once proofs exist, someone has to look at them: a store is worth monitoring for evidence of tampering, ensuring that the transparency log satisfies the desired properties of immutability and being append-only. A proof nobody re-checks buys the ability to detect an edit and never exercises it. | sourced | `X-cross-structure-053` "ensuring that the transparency log satisfies the desired properties of immutability and being append-only" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | The recorded adapter is JSONL + hash chain: one append-only local file per store, order carried by position in the file, identity carried by sequence number, integrity carried by a digest of the previous record folded into the next one. It serves append and read_at directly, and resolve_head by reading the last line. | Cannot serve prove or prove_consistency at all: the only integrity operation the shape admits is a sequential rehash of every record, performed by our own reader over a file only we hold. Its execution model is a single writer holding a single mutable file, where the order of writes is the order of bytes. | Keep the chain and add the tree over the same records rather than replacing the file: the digests already computed become leaves, so an existing store can be turned into a provable one without rewriting a record. cap-state-persistence-implement owns the migration, the per-adapter conformance subsets and the runbook; this row records the roles PASS.md B3 fixes and the axis the pair differs on. | claimed | `F-b3-17`, `F-a5-03`, `E-adapter-jsonl-hash-chain` "JSONL + hash chain" |
| `E-swap-candidate-object-store` | second | A content-addressed log over an object store: each record is an immutable object named by the digest of its canonical bytes, order is carried by an append-only Merkle tree rather than by file position, and the head is a small signed object. It serves prove and prove_consistency natively, since a valid log can be cryptographically verified by any third-party from a proof and a head alone. | Cannot rely on write order, on reading the previous line to find the head, or on a single process owning a file: objects arrive out of order, a listing is eventually consistent, and the head has to be a compare-and-swap on one small object rather than a position. It also cannot cheaply scan every record, which is exactly why the interface must not offer a full-log rehash. | Select the adapter by configuration alone, with no code edit between runs, and run the identical conformance suite against each; the merged report must show adapters_run >= 2 and the same head digest recomputed by an independent verifier under both. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is the axis: a single mutable file whose order is byte order and whose trust is possession, against immutable content-addressed objects whose order is a tree and whose trust is a proof. That is a different execution model, not a different database of the same shape. | claimed | `F-b3-17`, `F-b1-04`, `X-cross-structure-052`, `E-swap-candidate-object-store` "object store · relational · event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/conformance/state_persistence.py --adapter jsonl-hash-chain --adapter merkle-object-store --records 1500 --report out/state.json |
| Expected | docs/decomposition.md section 3.2 row P16, made precise and run over the adapter pair above: that command (proposed tool), the adapter selected by configuration with no code edit between runs. Per adapter it appends N records through the interface, then asserts that an independent verifier we did not write recomputes the same head digest from the stored records alone, that an inclusion proof for a uniformly random record verifies without the rest of the log, and that `records_written > 1000`; across adapters it asserts `head_digests_equal == true` and `adapters_run >= 2`. exit 0 with, per adapter, `records_written == 1500`, `external_head_matches == true`, `inclusion_proof_verified == true` and `chain_break_at == -1`, followed by `head_digests_equal=true adapters_run=2`. |
| Deliberate breakage | Edit one record body in place in the store, leaving both adapters, the record count and the command untouched. |
| Expected failure | exit 1 under both adapters: the independent verifier reports a chain break at that index and the inclusion proof for that record fails, so `chain_break_at` becomes the edited index, `external_head_matches == false` and `inclusion_proof_verified == false`. A run where the object-store adapter still exits 0 means its proof was served from a cached head instead of recomputed, which is the failure this breakage is aimed at rather than an incidental one. Claimed: neither adapter is written, no conformance tool exists here, and no run has been performed. The measured starting state is recorded in cap-state-persistence-use: the reference runner's chain verifies over 56 records across 4 runs and produces zero inclusion proofs, zero content-addressed record ids and zero sealed heads. |
| Status | claimed |
| Evidence | `F-b5-05`, `F-b3-17` "the integrity mechanism" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`

Used by: `cap-memory`, `cap-state-persistence-implement`, `seam-state`, `xc-idempotency-lease`, `xc-tenancy`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which standard, if any, may this interface cite, given that the recorded row forwards to B5 while docs/skill-manifest.json names a transparency-log RFC for integrity and a canonicalisation RFC for canonical bytes? | A fetch of each specification recording its number, title and version, and an E-standard- entity for it in kb/entities.jsonl. Neither RFC has a record in the knowledge base, and documentation fetches were blocked from this environment, so neither can be cited as a standard from here. | Applying 1-3-1 (T-t5-02: use 1-3-1: define the problem). Problem: the manifest names two RFCs the knowledge base cannot resolve, while the interface needs a standards position. (a) Add the two entities to kb/entities.jsonl - rejected: it rewrites the entity chain and invalidates the provenance heads recorded in every skill already written, to gain two rows. (b) Carry no standards table, state the recorded position from F-b3-17, and name the two RFCs only in proposed rows and in docs/decomposition.md's design - recommended, and what this skill does. (c) Borrow the attestation standards already in the knowledge base for the signed sealed head - deferred to cap-state-persistence-implement, where the signing adapter lives. Reversible: one fetch and one entity per row turns (b) into a standards table without touching any other row. | `T-t5-02`, `F-b3-17` "use 1-3-1: define the problem" |
| What are the retention defaults per class, and who is allowed to authorise a tombstone? | The longest window any consumer actually reads back over, measured against a real corpus, and the shortest window any obligation requires a body to be removable within. docs/decomposition.md section 2.2.4 proposes chain forever, body 400 days and payload 90 days extendable by a hold; none of those numbers is measured, and none appears in PASS.md. | Proposed: keep the three classes and the tombstone mechanism, which is the part that is load-bearing for integrity, and treat the numbers as configuration carrying no guarantee until a corpus has been measured. Authorisation is an identity and policy question and is not answered on this interface. | `F-b5-05` |
| Is a total order across partitions ever needed, or is a sealed head enough to carry continuity between runs? | Whether any consumer's fold produces a different answer under two different interleavings of records from two partitions. If none does, cross-partition ordering is cost with no buyer; if one does, that consumer names the guarantee it needs. | Proposed: one writer per partition, no cross-partition order, and continuity carried by a sealed head where each run's closing digest is the opening digest of the next, which is the property the store already relies on today (F-a5-03, stated by agentic-stack). | `F-a5-03`, `F-b5-04` "JSONL, hash-chained" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-state-persistence 2831cb4f, 2026-09-03 |
