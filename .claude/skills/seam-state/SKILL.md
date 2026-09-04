---
name: "seam-state"
description: "The State seam, contract and build: graph and ledger as two projections of one append-only, tamper-evident log, one writer per run, read at a pinned snapshot. Load it when deciding where a node, edge, entry, policy decision or attestation is written, when a query must answer the same twice, or before opening a second store."
---

# seam-state

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Settle the one boundary where the graph and the ledger persist: a single append-only, tamper-evident log of immutable facts, one writer per run, every read pinned to a head, with the graph and the ledger as folds over it rather than as two stores. core-components' graph and ledger rows (formerly core-graph and core-ledger) both defer persistence to this row (F-b5-04); cap-state-persistence supplies the opaque record store underneath, and this seam fixes what the records mean, who may write them and what a planner may ask. | sourced | `F-b5-04`, `F-b5-05`, `E-seam-state` "the graph and the ledger persist" |

## Entities

| Entity |
|---|
| `E-seam-state` |
| `E-core-component-graph` |
| `E-core-component-ledger` |
| `E-capability-state-persistence` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-object-store` |
| `E-swap-candidate-event-log` |
| `E-swap-candidate-relational` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-rfc-9162-certificate-transparency` | unverified | unverified | - | `X-xc-provenance-chain-006`, `F-b5-05` |
| `E-standard-rfc-8785-json-canonicalization` | unverified | unverified | - | `X-xc-provenance-chain-006`, `F-b5-05` |
| `E-standard-in-toto` | Statement v1 (unverified) | unverified | - | `F-b3-12`, `X-cross-structure-052` |

- `E-standard-rfc-9162-certificate-transparency` version note: Named by the search-only record X-xc-provenance-chain-006; the specification was not fetched from this environment, so the version reads unverified. Proposed entity id: kb/entities.jsonl carries no E-standard record for this RFC, so this id is ours and resolves nowhere until one is added, and the open question below records the gap.
- `E-standard-rfc-8785-json-canonicalization` version note: Same record, same caveat: named by X-xc-provenance-chain-006, not fetched, so unverified. Proposed entity id, minted here because the knowledge base has no E-standard record for it. It governs only the byte form a record is hashed in, which is what lets two independent writers agree on an identity.
- `E-standard-in-toto` version note: cap-provenance (formerly xc-provenance-chain) owns this row and its version; it appears here only because the sealed head is the object they sign, so this seam produces the head and never the signature.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| append (proposed operation set; no standard fixes a call surface for this seam, so the set below is ours) | run_id, expected_head, records[] each carrying a kind from the closed kind list, a body and a retention class, plus the fencing token the writer holds | the new Head, or a refusal; proposed - accepted only when expected_head is the current head and the token is not behind | proposed | `X-cross-structure-049`, `F-b5-05` |
| resolve_head (proposed) | run_id | Head; proposed - the only call in this contract whose answer moves, made once before planning starts | proposed | `F-b1-06` |
| query (proposed; the planner's whole read surface, as named projections) | projection name from the closed list, its arguments, and at_head | the projection's answer; proposed - deterministic at that head, forever | proposed | `F-b5-05`, `F-b1-06` |
| seal (proposed) | run_id | a head-sealed record carrying tree size, root hash, chain digest and the time; proposed - the closing head of one run is the opening head of the next | proposed | `F-a5-03`, `X-cross-structure-052` |
| prove (proposed) | record_id and at_head, or a pair of heads | an inclusion proof for the record, or a consistency proof between the two heads; proposed - never a rehash of the log | proposed | `X-seam-state-002`, `X-xc-provenance-chain-006` |
| snapshot (proposed) | projection name and at_head | a materialised fold at that head; proposed - a cache with a head on it, recomputable from empty and never authoritative | proposed | `X-seam-state-004`, `X-cross-structure-047` |
| redact (proposed) | record_id, the authority under which the body is removed, and who exercised it | a tombstone that preserves record_id; proposed - the body goes, the digest and every proof over it stay | proposed | `F-b5-05` |

### Shapes (JSON Schema 2020-12)

**StateRecord (proposed summary shape; the full record schema, the closed kind list, the eight planner projections and the retention classes are in references/state-seam.md)** (proposed; sources: `F-b5-05`, `F-b5-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:seam-record:0.1",
  "title": "StateRecord",
  "type": "object",
  "required": [
    "record_id",
    "prev_record_id",
    "chain_digest",
    "kind",
    "run_id",
    "fencing_token",
    "written_at",
    "declared_by",
    "body"
  ],
  "properties": {
    "record_id": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest over the canonical bytes of body. Identity, never a line number or a row id."
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
      "enum": [
        "node-asserted",
        "edge-asserted",
        "document-declared",
        "dispatch-submitted",
        "dispatch-observed",
        "ledger-entry",
        "policy-decided",
        "attestation-recorded",
        "head-sealed",
        "tombstone"
      ],
      "description": "Closed at authoring time. This seam interprets the kind; the store beneath it does not."
    },
    "run_id": {
      "type": "string",
      "description": "The write partition. Exactly one writer at a time."
    },
    "fencing_token": {
      "type": "integer",
      "minimum": 0
    },
    "written_at": {
      "type": "string",
      "format": "date-time"
    },
    "declared_by": {
      "type": "string",
      "description": "The actor prefix says which way in produced the record: user:, agent:, service: or schedule:."
    },
    "retracts": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Withdrawal is a new record naming the one it withdraws. There is no delete."
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
          "type": "boolean",
          "default": false
        }
      }
    }
  }
}
```

**ProjectionQuery (proposed): the shape of every read, and the reason design rule 5 is checkable here** (proposed; sources: `F-b1-06`, `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:query:0.1",
  "title": "ProjectionQuery",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "projection",
    "at_head",
    "args"
  ],
  "properties": {
    "projection": {
      "enum": [
        "get_document",
        "neighbors",
        "path_exists",
        "prior_result",
        "cost_history",
        "open_dispatches",
        "verify",
        "resolve_head"
      ],
      "description": "Closed list. A caller that needs a ninth reads references/state-seam.md and adds a row there first."
    },
    "at_head": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Required, with no default. There is no call that reads the newest state."
    },
    "args": {
      "type": "object"
    }
  }
}
```

**Worked appends, one per way in (proposed; TARGET T1 names three ways in and the same record shape carries all three, which is the whole claim)** (proposed; sources: `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t6-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:example:appends",
  "title": "Three appends, one log",
  "$ref": "urn:agentic:state:seam-record:0.1",
  "description": "Proposed. A human approving a step, an agent asserting an edge and an event arriving on a schedule differ only in declared_by; every other field, the head they append under and the refusal they get are identical. agentic-stack (formerly cap-consumption) owns the caller doctrine these three share.",
  "examples": [
    {
      "record_id": "sha256:0c7ac1...",
      "prev_record_id": "sha256:d09619...",
      "chain_digest": "sha256:50873a...",
      "kind": "ledger-entry",
      "run_id": "run-2026-09-03-17",
      "fencing_token": 12,
      "written_at": "2026-09-03T09:14:02Z",
      "declared_by": "user:corey",
      "body": {
        "decision": "approved",
        "step": 4
      },
      "retention": {
        "class": "body",
        "expires_at": "2027-10-07T09:14:02Z"
      }
    },
    {
      "record_id": "sha256:9b4f20...",
      "prev_record_id": "sha256:0c7ac1...",
      "chain_digest": "sha256:1f28cd...",
      "kind": "edge-asserted",
      "run_id": "run-2026-09-03-17",
      "fencing_token": 12,
      "written_at": "2026-09-03T09:14:07Z",
      "declared_by": "agent:planner-7",
      "body": {
        "type": "implementation",
        "from": "impl:jsonl-store",
        "to": "iface:state"
      },
      "retention": {
        "class": "chain"
      }
    },
    {
      "record_id": "sha256:77aa31...",
      "prev_record_id": "sha256:9b4f20...",
      "chain_digest": "sha256:aa9012...",
      "kind": "dispatch-submitted",
      "run_id": "run-2026-09-03-17",
      "fencing_token": 12,
      "written_at": "2026-09-03T09:15:00Z",
      "declared_by": "service:nightly-intake",
      "body": {
        "dispatch_id": "8f1e...",
        "idempotency_key": "nightly-2026-09-03"
      },
      "retention": {
        "class": "body",
        "expires_at": "2027-10-07T09:15:00Z"
      }
    }
  ]
}
```

**Worked rejection (proposed): the append a second writer lost** (proposed; sources: `F-b4-07`, `X-cross-structure-048`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:example:problem",
  "title": "Problem details from this seam",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. A refused append comes back as RFC 9457 problem details, the object cap-errors owns; nothing here returns a status alone or a message to be parsed. cap-state-persistence already states this refusal for the store beneath: urn:agentic:problem:head-moved is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns, and until that row lands an implementation returns the registered idempotency-conflict with the expected and current heads in detail. The seam adds nothing to the shape and one thing to the advice: re-read the head and re-derive, because the fact you were about to write may already have been written by the winner.",
  "examples": [
    {
      "type": "urn:agentic:problem:head-moved",
      "title": "Another writer advanced the head for this run first",
      "status": 409,
      "detail": "run-2026-09-03-17: expected head sha256:9b4f20... but the current head is sha256:77aa31...; fencing token 11 is behind 12",
      "retryable": true,
      "retry_after_s": 0,
      "correlation": {
        "run_id": "run-2026-09-03-17"
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| One log, two projections. core-components hands the graph's and the ledger's persistence to cap-state-persistence (F-b5-04), and the consequence here is that there is no graph store and no ledger store: there is one log of immutable facts and both components are folds over it, so the two can never disagree about what happened and no distributed transaction is needed to keep them together. | sourced | `F-b5-04`, `F-b2-04`, `F-b2-06` "the graph and the ledger persist" |
| What this seam must settle is fixed by the source and not by taste: the write model, concurrency and single-writer guarantees, the integrity mechanism, retention, and the query surface a planner needs. cap-state-persistence states the same list for the store beneath (F-b5-05); the consequence here is that this seam answers all five in the vocabulary of records and projections, and an answer given only by an adapter is not an answer. | sourced | `F-b5-05`, `F-b5-06` "the write model, concurrency and single-writer guarantees" |
| Records are facts, never updates: proposed, from docs/decomposition.md section 2.2.1. The prior art is the same shape - you persist every state change as an immutable event, with your database becoming an append-only log of facts about what happened in your system - and the consequence taken here is that withdrawal is a new record carrying retracts, deletion is a tombstone, and anything that cannot be derived by folding the log from empty is a cache and not state. | sourced | `X-cross-structure-047`, `F-b5-05` "you persist every state change as an immutable event, with your database becoming an append-only log of facts about what happened in your system" |
| Every append is conditional and every writer is fenced. Proposed partition: one writer at a time per run, the append naming the head it expects and the token it holds, refused when either is behind. cap-state-persistence states the store-level check (X-cross-structure-048), where it enforces optimistic concurrency control; what this seam adds is that a refusal is never resolved by branching the log, so a paused writer that wakes up cannot fork a run. | sourced | `X-cross-structure-048`, `X-cross-structure-049` "It enforces optimistic concurrency control" |
| Every query takes at_head and is deterministic at that head. agentic-stack states design rule 5 as a test (F-b1-06); the consequence here is the one constraint that makes it checkable rather than aspirational, because a pure function cannot read a moving store: resolve_head is the only call whose answer moves, it is made once before planning starts, and there is no read with a default head. | sourced | `F-b1-06`, `F-b5-05` "Planning is a pure function and completes before execution begins" |
| The chain is kept and a tree is added over the same records. The source asks for exactly this - the chain is the valuable idea and should survive - and build-evidence (formerly build-adapter-pair) cites the same sentence for the swap; the consequence here is a change of verification cost, since hash chaining requires scanning the entire prefix of the log for verification, while Merkle trees improve this by allowing proofs of inclusion (X-seam-state-003). | sourced | `F-b5-05`, `X-seam-state-003` "The chain is the valuable idea and should survive" |
| Continuity across runs is a sealed head, not an interleaving. build-evidence (formerly build-evidence-record) and core-components (formerly core-ledger) both rely on the property the store already has (F-a5-03), that a manual edit between runs is detectable; the consequence here is that the closing sealed head of one run is the opening head of the next, cross-run total order is neither guaranteed nor needed, and detection becomes a consistency proof rather than a rehash. | sourced | `F-a5-03`, `X-seam-state-002` "a manual edit between runs is detectable" |
| Redaction is a tombstone that preserves the record digest, never a deletion: proposed, from docs/decomposition.md section 2.2.4. The chain commits to the digest of the canonical body and never to the body, so replacing a body with a tombstone that records who redacted it and under what authority leaves every chain digest and every inclusion proof still verifying. A store that cannot do this ends up choosing between compliance and integrity. Research query: see the docs/decomposition.md citability research query on the sibling instruction row above — does a citable kb record state the tombstone-preserves-digest rule this row currently sources only to an external design doc? | proposed | `F-b5-05` |
| Tamper-evident is not tamper-proof, and this seam does not claim otherwise: transparency logs are tamper-evident but not tamper-proof, so the guarantee is only delivered if something independently monitors the log. That monitoring is cap-provenance's job (formerly xc-audit-trail), and the consequence here is that this seam must expose proofs an outside monitor can take, not a self-report that the log verified. | sourced | `X-cross-structure-053`, `X-seam-state-008` "Transparency logs are tamper-evident but not tamper-proof" |
| Whichever of TARGET T1's three ways in produced a record - a human, an agent, an internal or external event - it is written through the same append under the same head, and the platform stamps the actor, the correlation identifier, the policy decision and the attestation on that one path rather than the caller supplying them. agentic-stack states design rule 7 (F-b1-08); agentic-stack (formerly cap-consumption) owns the caller doctrine and is named here instead of restated. | sourced | `F-b1-08`, `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-03` "Telemetry, policy, provenance and budget are applied by the platform" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion a result is judged against. agentic-stack states design rule 6 (F-b1-07), which core-components applies to the Judge's criterion: an agent sees its outcome, never the criterion. The consequence on this seam is concrete, because a log is the easiest place for it to leak: no record body carries criterion text, no projection returns it, and a graded unit reading the log at its own head finds the handle and never the text. | sourced | `F-b1-07` "An agent sees its outcome" |
| The medium. Proposed: no file path, byte offset, row id, bucket name, object key or table appears in a record, a projection answer or a head. core-components states the rule this follows (F-part-c-09); the consequence here is that a consumer cannot tell which adapter answered, which is the property the swap depends on. | sourced | `F-part-c-09`, `F-b3-17` "Products belong in the adapter column only" |
| Proposed: there is no read without a head, no operation that rehashes the whole log, and no update or delete call. core-components carries design rule 5 for the planner (F-b1-06); each absence here is load-bearing - a default head would make planning impure, a full rehash would be unimplementable over a store of any size and is therefore a file-format detail, and an update would make every proof taken before it a lie. | sourced | `F-b1-06`, `F-b5-05` "Cost is knowable before commitment" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write one log, not two stores: give the graph and the ledger the same append path, the same head and the same partition, and derive each as a named fold over the records. | core-components' graph and ledger rows (formerly core-graph and core-ledger) both defer persistence to this row (F-b5-04), and two stores would need a distributed transaction to stay consistent where one log needs none. The prior art is the ledger itself: an immutable audit trail that enables reconstruction of system state at any point in time. | sourced | `F-b5-04`, `X-seam-state-007` "forming an immutable audit trail that enables reconstruction of system state at any point in time" |
| 2 | Fix the closed kind list and content-addressed identity before anything writes: the record id is the digest of the canonical bytes of the body, and the kind comes from the one canonical, versioned enumeration in references/state-seam.md #1 - every other appearance (this shape, the full schema, docs/decomposition.md 2.2.1) mirrors it and must not re-declare it by hand; tools/check_record_kinds.py fails the build if a mirror's count or member set disagrees with the canonical list. | Proposed. Identity is what every later mechanism rests on - the tree's leaves are record ids, a tombstone preserves one, and two adapters can only be compared if they agree on what a record is called. Canonical bytes are what let two independent writers reach the same id for the same fact. | sourced | `X-xc-provenance-chain-006`, `F-b5-05` "RFC 8785 defines JSON Canonicalization Scheme for canonical byte form to hash" |
| 3 | Make every append conditional: partition by run, take a lease with a monotonically increasing fencing token, state the head you expect, and refuse the write when the head has moved or the token is behind. Run a two-writer race in the test suite from the day the lease lands. | The check is the general form of what an event store does with a version: the specified expectedVersion is compared to the currentVersion of the stream. A rejection counter that is never exercised reads exactly like a store with no lease at all, which is how a forked chain gets shipped. | sourced | `X-cross-structure-049`, `X-cross-structure-048` "The specified expectedVersion is compared to the currentVersion of the stream." |
| 4 | Add the append-only Merkle tree over the record ids the chain already commits to, and write a head-sealed record at run close carrying tree size, root hash and chain digest; make that head the opening head of the next run. | Proposed, and it changes what verification costs rather than what is stored: leaf nodes are added in an append-only fashion and which allows producing logarithmic proofs witnessing that arbitrary two versions of the tree are consistent, so a third party can check one record without holding the log. Nothing already written is rewritten, which is what makes the step revertible. | sourced | `X-seam-state-002`, `F-a5-03` "leaf nodes are added in an append-only fashion and which allows producing logarithmic proofs witnessing that arbitrary two versions of the tree are consistent" |
| 5 | Expose the planner's reads as the eight named projections in references/state-seam.md, each taking at_head, and give none of them a default head. Add a ninth only by adding a row there. | Design rule 5 requires cost to be knowable before commitment (F-b1-06, stated by agentic-stack), and a pure function cannot read a moving store; core-components' ledger row (formerly core-ledger) cites the same phrase from F-b5-05 for its own deduplication query, and what this seam adds is that the list is closed and shared. A closed, named projection list is also what makes the snapshot-pinning assertion in the definition of done finite: eight projections, one head, identical answers. | sourced | `F-b1-06`, `F-b5-05` "the query surface a planner needs" |
| 6 | Add periodic snapshots per projection, each labelled with the head it was taken at, and treat every one as a cache: delete them all and the platform still answers, more slowly. | Snapshots are how a fold stays affordable as the log grows - instead of replaying all 50,000 events, the system loads the snapshot at event 49,500 and replays only the 500 events that came after - and labelling them with a head is what stops one being served to a query pinned somewhere else. | sourced | `X-seam-state-004`, `X-cross-structure-047` "the system loads the snapshot at event 49,500 and replays only the 500 events that came after" |
| 7 | Implement retention as three classes - chain, body, payload - with a hold flag, and implement deletion as a tombstone that preserves the record id and records the authority for the removal. The table is in references/state-seam.md. Research query: docs/decomposition.md is not a citable kb id under this schema (only F-, E-, R-, T-, X- and REF- ids qualify) — does PASS.md or TARGET.md state a retention-class or tombstone requirement anywhere that would let this row cite a real kb record instead of an external design doc? | Proposed, from docs/decomposition.md section 2.2.4. One retention policy for all three classes will be wrong for two of them, and a redaction that removes the record instead of the body breaks every chain digest and inclusion proof after it, which is how a store comes to be asked to choose between compliance and integrity. | proposed | `F-b5-05` |
| 8 | Return every refusal as problem details: a lost race as head-moved, an unverifiable proof as record-unverifiable, both proposed and pending registration in the closed registry cap-errors owns, with the registered fallbacks cap-state-persistence names until those rows land. | cap-errors requires failures to be typed and machine-readable, never parsed from prose (F-b4-07), and the distinction a caller acts on is retryable: a lost race is retried after re-reading the head, a broken chain never is. Minting a suffix at the call site would give callers a URI no conformant implementation may emit. | sourced | `F-b4-07`, `F-b5-05` "Typed and machine-readable. Never parsed from prose" |
| 9 | Ship the two adapters below behind this one contract, selected by configuration with no code edit between runs, and make the conformance suite report which one answered. | build-evidence (formerly build-adapter-pair) states design rule 3 (F-b1-04), where the second exists to prove the first is not load-bearing; what this seam adds is the axis that matters here - one adapter finds its head by reading the last line of a file and verifies by rehashing, the other has immutable objects, an eventually consistent listing and verification only through proofs. | sourced | `F-b1-04`, `F-b3-17` "the second exists to prove the first is not load-bearing" |
| 10 | Open references/state-seam.md when you need the full record schema, the closed kind list, the eight projections with their signatures or the retention table; this skill body is enough to decide where a record goes and what a read may assume without it. | Proposed: our convention. Long material behind one pointer keeps the contract readable, which is the usability requirement TARGET T3 states and core-components cites for the Document, and keeps one copy of the schema instead of a paraphrase in every skill that touches state. | sourced | `T-t3-01` "It has to be simple to use." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Size verification against where the store is going, not where it is. build-evidence (formerly build-evidence-record) cites the scale that exists (F-a5-04), ~2,445 records across 308 runs; rehashing that is tractable and rehashing a hundred times that is not, which is the practical half of the argument for adding proofs rather than tuning the chain. | sourced | `F-a5-04` "~2,445 records across 308 runs" |
| A chain that verifies over an empty or trivial store proves nothing. agentic-stack states the structurally-green finding (F-a7-03) - those establish well-formedness, not correctness - and here that means every integrity run reports how many records it covered and how many concurrent appends it actually raced, so a stage that never ran cannot read as a stage that passed. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Version the record kinds from the first release, because event versions allow our system to grow and evolve over time and a log is the one place a shape change cannot be migrated by rewriting: old records stay exactly as written, so a reader must be able to tell which version of a kind it is folding. build-evidence (formerly build-interface-versioning) owns the discipline. | sourced | `X-seam-state-006` "Event versions allow our system to grow and evolve over time." |
| Prefer proofs an outsider can check over reports our own reader produces: the target is a log where the logger must prove that every logged entry is still present and that one snapshot of the log is consistent with any previous version. A verifier we wrote agreeing with a store we wrote is one program agreeing with itself. | sourced | `X-seam-state-001`, `X-cross-structure-052` "the logger must prove that every logged entry is still present and that one snapshot of the log is consistent with any previous version" |
| Proposed: keep durable-execution journals and this log the same shape but not the same concern. The cross-structure record on durable execution describes the same mechanism, where each step of the execution is compared to its log, so cap-durable-execution's steps are records here rather than a second private store, and a resumed run reads its own history at a head like anything else. | sourced | `X-cross-structure-043` "each step of the execution is compared to its log" |
| Proposed: when a record kind, a projection or a retention rule is genuinely undecided, apply 1-3-1 rather than adding a knob - define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation - and record the choice as an open question here. A knob added to a log is permanent, because every record written under it stays. | sourced | `T-t5-02` "identify the three best possible solutions that align to the goal, and follow the recommendation" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | cap-state-persistence already records this role for the store (F-b3-17, F-a5-03): a JSONL, hash-chained append-only file with a single file writer. What this seam adds is what goes in it - graph assertions, ledger entries, policy decisions and attestations in one partitioned log - and that every planner read is answered from that log at a head rather than from a component's own memory. | Cannot serve an inclusion or a consistency proof, so verification is a rehash of the whole prefix and a third party must be handed the file. Cannot hold more than one writer per file, cannot redact a body without rewriting the file, and cannot answer a read at an old head once a snapshot has been compacted over it. | Additive and staged: record ids over canonical bytes, then the tree and the sealed head, then the fencing lease, each stage revertible by not reading the field the previous one added, and no record already written is rewritten. | claimed | `F-b3-17`, `F-a5-03`, `E-adapter-jsonl-hash-chain` "JSONL, hash-chained" |
| `E-swap-candidate-object-store` | second | A content-addressed Merkle log over an object store: one immutable object per record named by the digest of its canonical bytes, the tree persisted alongside, the head a single small object advanced by compare-and-swap, and the writer fenced by a lease. Proofs are served from the tree, so a consumer verifies one record from a proof and a head alone. cap-state-persistence records the same candidate column for the store beneath (F-b3-17: object store, relational or event log). | Cannot assume write order, cannot read the previous line to find the head, cannot take a file lock, and cannot cheaply scan every record: a listing is eventually consistent and an object may land after one written later. It is unimplementable against any interface that keeps a full-log rehash, which is why this contract has none. | Select by configuration only. Replay the same record sequence through both, then require the merged conformance report to show adapters_run == 2, the same head digest per sequence, and the eight projections identical at a pinned head under each. | claimed | `F-b3-17`, `F-b1-04`, `X-cross-structure-052`, `E-swap-candidate-object-store` "object store · relational · event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/state-persistence/test.sh && python3 harness/state-persistence/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at fb96f80: exit 0; last lines:   adapter=content-addressed merkle log over an object store (second adapter) cases=11 passed=11 appends=10 refusals=2 product_hits=0 \| conformance PASSED: 22/22 cases, 2 binding(s) |
| Deliberate breakage | sed -i '76s#.*#LEAF_PREFIX = b"\\x02"#' harness/state-persistence/interface.py |
| Expected failure | Measured by tools/measure.py at fb96f80: exit 1; last lines:   ok   chain_break_at went from -1 to 2, the tampered record \| passed 14, failed 6 |
| Status | measured |
| Evidence | `F-b5-05`, `F-b1-06`, `F-part-c-04` "concurrency and single-writer guarantees" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `seam-state-implement` | Turn the contract in seam-state into something that runs here: one append path behind two adapters whose execution models differ, built out of the JSONL, hash-chained store that already exists rather than beside it, so the chain that is the valuable idea survives the move. | `references/seam-state-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-evidence`, `build-skill-authoring`, `cap-errors`, `cap-provenance`, `cap-state-persistence`, `core-components`

Used by: `cap-provenance`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the Merkle tree replace the linear hash chain or wrap it? | Measure full-verification wall time for the store that exists, about 2,445 records across 308 runs, under both arrangements, and audit whether any current consumer depends on strict linear order or on the opening-digest property between runs. If none does and verification is dominated by the tree, replacing is cheaper to maintain. | Wrap: keep the chain and add the tree over the same record ids. The cross-run opening-digest property is already relied on and is cheap to keep, and wrapping makes the migration additive rather than a rewrite of every stored record. | `F-b5-05`, `F-a5-04` "The chain is the valuable idea and should survive" |
| What is the single-writer partition key: the run, the document root, or one global writer? | Measure write contention per candidate key and, over the recorded run history, the frequency of edges and ledger entries that cross run boundaries. A high cross-run rate argues for a coarser partition, because every crossing edge is then a fact whose two ends were written under different heads. | Proposed: the run. It matches how work is already grouped, keeps the writer count equal to the concurrent run count, and leaves cross-run continuity to the sealed head, which this contract needs anyway. | `F-b5-05` |
| Where do the E-standard entities for the two integrity RFCs live, given that the knowledge base has none and both standards rows above carry ids this skill minted? | Whether kb/entities.jsonl is regenerated from a source that names them: if the entity extractor reads PASS.md alone, neither RFC will ever appear there, and the ids stay proposed however many skills cite them. | Applying 1-3-1 (T-t5-02): the three options were to drop the rows, to cite the standards only in prose, or to state them as standards rows with the minted ids marked proposed in version_note. The third is recommended and taken, because a reader must be able to see which published standard governs the integrity mechanism, and hiding it in prose to keep the entity file clean would cost the reader more than the honest footnote does. | `T-t5-02`, `X-xc-provenance-chain-006` "identify the three best possible solutions that align to the goal, and follow the recommendation" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session seam-state 2831cb4f, 2026-09-03 |
