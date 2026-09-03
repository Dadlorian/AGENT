---
name: core-ledger
description: The Ledger: one append-only record that outlives the run and is the single authority on whether a unit of work was already done. Load it before writing anything that records what happened, before answering 'has this already run', when a replay must return a prior result instead of doing the work twice, when a duplicate key is about to overwrite a row, when a planner is about to re-plan finished work, and when someone asks 'what survives the run', 'where is the receipt', 'why can we not just update the status field', or 'how would we know if someone edited history'. Where the entries are kept, and at which snapshot they are read, belong to the state seam: an entry addressed by file offset or row id means the boundary was drawn wrong.
---

# core-ledger

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one append-only record across runs as the single authority on whether work was already done, so a repeated submission returns what happened last time instead of doing the work again. | sourced | `F-b2-06`, `F-b2-01` "append-only across runs; the deduplication authority" |

## Entities

| Entity |
|---|
| `E-core-component-ledger` |
| `E-core-component-document` |
| `E-core-component-planner` |
| `E-seam-state` |
| `E-concern-idempotency` |
| `E-capability-idempotency` |
| `E-capability-errors` |
| `E-standard-idempotency-key-convention` |
| `E-standard-rfc-9457-problem-details` |
| `E-rule-b1-7` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-idempotency-key-convention` | unverified | unverified | - | `F-b3-16`, `F-b1-03` |
| `E-standard-rfc-9457-problem-details` | RFC 9457 | unverified | - | `F-b3-13`, `F-b4-07` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| append (proposed operation; PASS.md names the component, not the calls) | one entry carrying a run_id, a kind from the closed kind set, the acting subject, the idempotency key it was submitted under, and the body of what happened (proposed) | the admitted entry with its sequence number and its chain digest, or a typed problem; the entry that was already there is never replaced, so the same key appended twice leaves two distinguishable entries rather than one overwritten one (proposed) | proposed | `F-b2-06`, `X-core-ledger-006` |
| head (proposed operation; the only call whose answer moves) | a run_id (proposed) | the current chain digest and entry count for that run, which is the snapshot every other call is then made at; proposed as the single non-deterministic call, taken once before planning starts (proposed) | proposed | `F-b1-06` |
| prior_result (proposed operation; the deduplication query) | an idempotency key, the digest of the submitted body, and a head to answer at (proposed) | a replay answer saying whether the key is absent, open, terminal or in conflict, plus the terminal entry when there is one; this is the call that stops a planner planning work that has already been done (proposed) | proposed | `F-b2-06`, `F-b4-08` |
| open_work (proposed operation) | a run_id and a head (proposed) | the entries that are not terminal, so work left hanging by a prior run is reconciled rather than re-planned; proposed as a distinct call because 'never started' and 'started and unfinished' need different handling and a single boolean cannot carry both (proposed) | proposed | `F-b2-06` |
| fold (proposed operation) | a head, and optionally a selector over entry kinds (proposed) | the derived view the caller asked for, recomputed from the entries alone; proposed as the only way a view is produced, so anything that cannot be recomputed from empty is cache and never an authority (proposed) | proposed | `X-core-ledger-003` |
| verify (proposed operation) | a head, and optionally one entry's identity (proposed) | whether the chain from the first entry to that head recomputes, and for one entry the proof that it is in the log; proposed so that a consumer we did not write can check a receipt without being handed the whole log (proposed) | proposed | `F-b4-05`, `X-core-ledger-005` |

### Shapes (JSON Schema 2020-12)

**ledger-entry (proposed summary shape; the full schema, the kind vocabulary, a worked entry for each of TARGET T1's three ways in and a worked rejection are in references/ledger-shapes.md)** (proposed; sources: `F-b2-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:ledger:entry:0.1",
  "title": "LedgerEntry",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "seq",
    "prev",
    "hash",
    "run_id",
    "kind",
    "actor",
    "idempotency_key",
    "recorded_at"
  ],
  "properties": {
    "seq": {
      "type": "integer",
      "minimum": 0,
      "description": "Position in the run's partition. Assigned by the append, never by the caller."
    },
    "prev": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "hash": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Commits to prev and to this entry's own canonical body, so an edit anywhere behind it stops recomputing."
    },
    "run_id": {
      "type": "string",
      "minLength": 1
    },
    "kind": {
      "enum": [
        "run-started",
        "step-observed",
        "judged",
        "approval-parked",
        "approval-returned",
        "run-completed",
        "superseded"
      ]
    },
    "terminal": {
      "type": "boolean",
      "description": "True on the entry that ends the work for this key. What prior_result looks for."
    },
    "actor": {
      "type": "string",
      "pattern": "^(user|agent|service|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "The acting subject in the entry envelope's grammar. Recorded, never branched on."
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1
    },
    "envelope_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest of the submitted body, so the same key with a different body is a conflict and not a replay."
    },
    "criterion_ref": {
      "type": "string",
      "description": "An opaque handle. The criterion behind it is never an entry field; see Deliberately not exposed."
    },
    "supersedes": {
      "type": "string",
      "description": "The hash of the entry this one corrects. A correction is an append, never an edit."
    },
    "recorded_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

**ledger-replay-answer (proposed shape; the machine-readable answer instruction 3 branches on, with the refusal shape cap-errors governs)** (proposed; sources: `F-b4-08`, `F-b3-13`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:ledger:replay-answer:0.1",
  "title": "ReplayAnswer",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "key",
    "state",
    "records_appended",
    "at_head"
  ],
  "properties": {
    "key": {
      "type": "string",
      "minLength": 1
    },
    "state": {
      "enum": [
        "absent",
        "open",
        "terminal",
        "conflict"
      ],
      "description": "absent: never submitted. open: submitted, no terminal entry yet. terminal: finished, prior_entry is the receipt. conflict: same key, different envelope_digest."
    },
    "prior_entry": {
      "oneOf": [
        {
          "$ref": "urn:agentic:core:ledger:entry:0.1"
        },
        {
          "type": "null"
        }
      ]
    },
    "records_appended": {
      "const": 0,
      "description": "Asking never writes. The definition of done asserts on this after a replay."
    },
    "at_head": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1",
      "description": "Set only when state is conflict, as urn:agentic:problem:idempotency-conflict with status 409, the registered row for a same key with a different request body."
    }
  }
}
```

**ledger-check-report (proposed shape; the counts the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:ledger:check-report:0.1",
  "title": "Ledger check report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "entries_checked",
    "head_match",
    "terminal_records_for_key",
    "records_appended_on_replay",
    "criterion_leaks"
  ],
  "properties": {
    "entries_checked": {
      "type": "integer",
      "minimum": 0
    },
    "head_match": {
      "type": "boolean",
      "description": "The head recomputed by folding from empty equals the stored head."
    },
    "terminal_records_for_key": {
      "type": "integer",
      "minimum": 0,
      "description": "Must be exactly 1. Becomes 2 when a duplicate key is appended twice as terminal, and 0 when one overwrote the other."
    },
    "records_appended_on_replay": {
      "type": "integer",
      "minimum": 0
    },
    "criterion_leaks": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The Ledger is append-only across runs and is the deduplication authority; remove it and nothing survives the run. Every other rule in this contract is a consequence of those two jobs held by one component. | sourced | `F-b2-06` "nothing survives the run" |
| A duplicate key never overwrites. Replay safety is a platform contract rather than a caller's option (F-b4-08); the consequence here is countable - a second submission under a key whose entry is already terminal appends zero entries and returns the prior entry, so 'safe to replay' means the entry count is unchanged and not merely that the effect happened to be the same. | sourced | `F-b4-08`, `F-b3-16` "Every externally-triggered action is safe to replay" |
| Proposed: nothing is ever updated or deleted. A correction is a new entry carrying supersedes set to the entry it corrects, so the same log read twice never loses a fact between reads and the receipt for a run stays the receipt that was issued. | proposed | `X-core-ledger-006`, `F-b2-06` |
| Proposed: an entry commits to its predecessor, so a manual edit between runs is detectable by recomputation rather than by trust. This is the property the store that runs today already has, and this contract requires it of any store that replaces it. | proposed | `F-a5-03`, `X-core-ledger-002` |
| Every read is answered at a pinned head, so the same head gives the same answer forever. agentic-stack states design rule 5 as a test (F-b1-06); the consequence here is that head is the only call whose answer moves, it is taken once before planning starts, and a query that cannot name the head it was answered at cannot be an input to a pure planner. | sourced | `F-b1-06` "Planning is a pure function and completes before execution begins" |
| Where entries are kept is somewhere else. seam-state owns the row in which the graph and the ledger persist (F-b5-04); the consequence here is that this contract carries no file path, no row id, no offset, no lease and no writer count, and an entry identified by any of them is a storage engine's shape that has reached the core. | sourced | `F-b5-04`, `F-b5-05` "the graph and the ledger persist" |
| Proposed: any view over the ledger is a fold, and nothing derived is authoritative. A count, an index or a cached dedup table is recomputable from the entries from empty or it is not state at all, which is what keeps two readers of the same head from disagreeing about what happened. | proposed | `X-core-ledger-003`, `X-core-ledger-007` |
| A refused append or a conflicting key comes back as a typed problem, never as prose. cap-errors owns the shape and the closed type registry, and core-document applies the same rule to a refused declaration (F-b4-07); the consequence here is that a caller that resubmitted with a changed body branches on urn:agentic:problem:idempotency-conflict and reads the key and the two digests from the members, never on a message's wording. | sourced | `F-b4-07`, `F-b3-13` "Typed and machine-readable. Never parsed from prose" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Criterion text, in any entry field, body or detail string. agentic-stack and core-document state design rule 6 (F-b1-07); the consequence on this component is that a judged entry carries criterion_ref and the verdict and nothing else, because the ledger is the one surface every later step and every audit reads, so a criterion written here is a criterion published to everything that was ever graded against it. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |
| Products, endpoints, file paths, offsets, row ids and lease mechanics. agentic-stack, build-skill-authoring and core-document state the rule (F-part-c-09); the consequence here is that an entry says what happened and never where it was written, so the same entries survive every swap of the store beneath them. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| Proposed: an update call, a delete call and a compaction that changes an entry's identity. There is no operation in this contract that makes an existing entry different from what it was, and a store that offers one has offered a way to make the receipt disagree with the run. | proposed | `F-b2-06`, `X-core-ledger-006` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Append one entry for every observable step at the moment it happens - the run starting, each step observed, each verdict, each approval parked and returned, and the run completing - and let no run call itself done before its terminal entry is appended. | The entries are the only thing that outlives the run, so a step that was not recorded did not happen as far as every later reader is concerned, including the planner deciding whether to run it again. | sourced | `F-b2-06`, `X-core-ledger-007` "append-only across runs" |
| 2 | Take the idempotency key from the entry envelope that submitted the work, whichever of TARGET T1's three ways in it came from, and record the digest of that envelope beside it. Do not derive the key from the work, from a timestamp, or from the acting subject. | A human, an agent, and an internal or external event all reach the same work through one envelope, so a key derived per producer would make the same request from a retrying event and a re-clicking human look like two different pieces of work; the digest beside it is what separates a replay from a changed body. | sourced | `T-t1-02`, `T-t1-03`, `F-b3-16` "An agent must be able to enter the system." |
| 3 | Ask prior_result before planning and branch on the four states of the replay answer: absent, plan; open, reconcile the outstanding entries rather than re-plan them; terminal, return the prior entry and append nothing; conflict, refuse with urn:agentic:problem:idempotency-conflict. | agentic-stack states design rule 5 as a test (F-b1-06), and a planner that cannot ask this question will price and then perform work that is already finished; branching on the state rather than on a boolean is what keeps unfinished work from being silently redone. | sourced | `F-b1-06`, `F-b4-08` "Cost is knowable before commitment.**" |
| 4 | Correct by appending. When an entry was wrong, append a new one with supersedes set to the entry it replaces; never edit, never delete, and never compact in a way that changes an entry's identity. | The chain commits to what was written, so an in-place fix breaks recomputation from the fix forward and leaves a reader unable to tell repair from tampering; an append leaves both readings available and says which one is later. | sourced | `X-core-ledger-006` "never updated or deleted" |
| 5 | Resolve a head first, then answer every other query at it, and carry that head on the answer. Do not answer a dedup question, a fold or a verification against whatever the log happens to contain at the moment the call arrives. | The query surface the planner needs is the one part of persistence this component's callers depend on, and a moving answer turns a pure plan into a race; carrying the head on the answer is what lets a later reader reproduce the decision. | sourced | `F-b5-05` "the query surface a planner needs" |
| 6 | Write criterion_ref and the verdict into a judged entry, never the criterion body, and keep a check in the append path that refuses an entry containing a declared criterion string. | core-document states the grader rule for a declaration (F-b1-07); what it costs here is a refusal in the write path, because the ledger is read by everything downstream and a criterion that reaches it has escaped every later attempt to hide it. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| 7 | Stamp the cross-cutting fields on the entry itself - the acting subject and its delegation depth, the correlation attribute, the budget remaining after the step, and the policy decision that allowed it - and provide no flag by which a caller can append an entry without them. | agentic-stack states design rule 7 as a test (F-b1-08); the consequence here is that the ledger is where a reader checks the guarantees actually held for a run, so an entry missing them makes the guarantee unverifiable after the fact even when it was applied. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| 8 | Judge a candidate implementation on four counts, not on an exit code: the head recomputed by folding from empty equals the stored head; exactly one terminal entry exists per key; a replay of a terminal key appends zero entries and returns the prior entry; and no declared criterion string appears in any entry. | agentic-stack and build-definition-of-done state the green-gate finding (F-a7-03); each of these is a count or an absence over entries that were actually written, which is what stops a ledger check from passing over an empty log. | sourced | `F-a7-03`, `F-part-c-04` "Those establish well-formedness, not correctness" |
| 9 | Proposed: open references/ledger-shapes.md when you are writing the full entry schema, the kind vocabulary, the entry a producer kind you have not handled yet would append, or the refusal a conflicting key returns. The body of this skill is enough to append correctly and to judge an implementation without it. | Proposed: the full schema, the three worked entries and the worked rejection are longer than the progressive-disclosure budget allows here, and a reader deciding what to record does not need them; a reader building the append path does. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-definition-of-done already state the green-gate finding (F-a7-03). What it adds here: a chain that verifies has been shown intact, not complete - an entry that was never appended is invisible to every verification - so a passing chain check must be reported alongside the count of entries it covered and never on its own. | sourced | `F-a7-03` "with every behavioural stage skipped" |
| Turn every contended write into an append rather than a competing update; the prior art for event-sourced ledgers treats this as the core mechanical change, and it is also what makes two writers' outcomes distinguishable after the fact instead of one silently winning. | sourced | `X-core-ledger-006` "transform a potentially contentious and complex UPDATE operation into a simple, non-destructive, and highly performant APPEND operation" |
| Proposed: serve the dedup question from a projection keyed by the idempotency key rather than by scanning the log, and rebuild that projection from the entries on start. Prior art for ledgers keeps a versioned key-value view for exactly this lookup; keeping it derived is what stops it becoming a second authority on whether work was done. | proposed | `X-core-ledger-004`, `X-core-ledger-003` |
| Design the verification so a third party can check one receipt without being handed the whole log; the prior art for immutable audit trails does this with inclusion proofs over a root computed from all records, which is the difference between a receipt someone can check and one they have to trust. | sourced | `X-core-ledger-005`, `F-b4-05` "build a Merkle root over all records and generate/verify inclusion proofs" |
| Proposed: keep the entry kind set small enough to hold in mind, and resist adding a kind for each new step type. Seven kinds cover a run's shape; a kind per operator turns the one thing every reader has to understand into a vocabulary they have to look up, which is how a simple record becomes daunting. | proposed | `T-t3-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.1 row C5, made precise. Proposed tool, built with this component: `python3 tools/ledger_check.py --log out/ledger.jsonl --replay-key <k> --criteria criteria.txt --report out/ledger-check.json`. It folds the log from empty and asserts the computed head equals the stored sealed head, then resubmits a unit whose idempotency_key is already terminal, asserting `entries_checked > 0`, `head_match == true`, `terminal_records_for_key == 1`, `records_appended_on_replay == 0` and `criterion_leaks == 0`. |
| Expected | exit 0 and one report line of the form `entries_checked=<n> head_match=true terminal_records_for_key=1 records_appended_on_replay=0 criterion_leaks=0`, with n greater than zero and the replayed key echoed. |
| Deliberate breakage | Make the ledger overwrite rather than append on a duplicate key, changing nothing else. |
| Expected failure | The recomputed head diverges from the stored head so `head_match` becomes false, the entry that was overwritten is gone while the entries chained behind it still commit to it, the dispatch-record count for the key becomes 2, and the run exits non-zero with `entries_checked` unchanged - so the report names the key and the sequence number where recomputation first diverged rather than only that something failed. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b2-06` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `core-document`, `cap-errors`

Used by: `core-ledger-implement`, `seam-state`, `xc-audit-trail`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the deduplication key come from the entry envelope, or from a digest of the work itself? | Count, over recorded runs, how many submissions carry the same envelope key with a different body and how many carry different keys for identical work. Applying TARGET T5's 1-3-1, the three options were: the envelope's idempotency_key alone, which cannot tell a retry from a changed request; a content digest alone, which makes every cosmetic edit a new unit of work and gives an event producer no way to declare its own retry; or the envelope key as the identity with the envelope digest recorded beside it, so equality of key with inequality of digest is a conflict. The third is recommended and is what the shapes above take. | The envelope key, with envelope_digest recorded beside it; the conflict case returns the registered idempotency-conflict type rather than a new one. | `T-t5-02`, `F-b3-16` "use 1-3-1: define the problem" |
| Is a total order across runs required, or is a per-run partition with a sealed opening head enough? | Look for a query that two runs' entries cannot answer without interleaving them: a cross-run dedup over the same key, or a budget ceiling spanning runs. If none exists, the partition is enough and cross-run continuity is carried by the head alone. | Partition per run, with each run's closing head opening the next. A total order buys a guarantee nothing in this contract asks for and costs a single global writer. | `F-a5-03`, `F-b5-05` "a manual edit between runs is detectable" |
| How does append-only survive a lawful deletion, when a body must go but the receipt must still verify? | The count of entry bodies that will ever hold personal data or a secret. If it is zero the question is moot; if not, the mechanism has to be chosen before the first such entry is written, because retrofitting it means rewriting identities. | Proposed: replace the body with a tombstone that preserves the entry's identity and records who redacted it, so the chain and every proof still recompute; the identity commits to the body's digest and never needed the body itself. | `F-b5-05`, `X-core-ledger-005` "retention, and the query surface a planner needs" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
