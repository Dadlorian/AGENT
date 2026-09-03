---
name: core-ledger-implement
description: How to build the Ledger on this stack: an append path that links no store code, one entry constructor every producer maps into, an entry identity computed above the store so two stores agree on it, a deduplication projection rebuilt by folding rather than delegated to a store feature, the record store the entries sit in today and a second whose execution model differs, the migration off it, where the cross-cutting fields are stamped so no writer can decline them, and the conformance run that decides whether either store may serve. Load it when writing or reviewing that code, when uniqueness is about to be pushed into a store constraint, when a fold is about to be cached, and when someone asks 'where do the entries actually get written', 'can we change that without touching the core', or 'why did the same key give two different replay answers'.
---

# core-ledger-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what core-ledger's contract specifies (F-b2-06): one append path, one entry identity, a deduplication projection derived by folding, two record stores selected by configuration, and a run that shows the replay answer and the head survive the swap unchanged. | sourced | `F-b2-06`, `F-b1-04` "the deduplication authority" |

## Entities

| Entity |
|---|
| `E-core-component-ledger` |
| `E-seam-state` |
| `E-capability-state-persistence` |
| `E-concern-idempotency` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-relational` |

## Contract

### Shapes (JSON Schema 2020-12)

**ledger-store-binding (proposed shape; the wiring table, the backfill rules and the migration procedure are in references/implementation-notes.md)** (proposed; sources: `F-meta-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:ledger:store-binding:0.1",
  "title": "Ledger store binding",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "role",
    "append_conditional_on",
    "fold_order",
    "enforces_key_uniqueness",
    "differs_in_execution_model"
  ],
  "properties": {
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "append_conditional_on": {
      "type": "string",
      "minLength": 1,
      "description": "What an append is accepted against: the head the writer last saw. A store that accepts an unconditional append cannot refuse a forked chain."
    },
    "fold_order": {
      "type": "string",
      "minLength": 1,
      "description": "How entries are ordered before folding. Two bindings that order differently must still produce one head and one replay answer."
    },
    "enforces_key_uniqueness": {
      "type": "boolean",
      "description": "Whether the store itself can refuse a duplicate terminal key. Recorded, never relied on: the check lives above the binding so both roles behave the same."
    },
    "serves_query": {
      "const": false,
      "description": "A store that answers the deduplication question itself has taken a query language into the boundary; it returns entries only."
    },
    "differs_in_execution_model": {
      "type": "array",
      "minItems": 1,
      "description": "Proposed: the axes build-adapter-pair defines; carried here so a pair identical on every axis is rejected before the conformance run is worth reading."
    }
  }
}
```

**ledger-conformance-report (proposed shape; the counts the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:ledger:conformance-report:0.1",
  "title": "Ledger conformance report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "entries_checked",
    "head_match",
    "terminal_records_for_key",
    "records_appended_on_replay",
    "replay_answer_mismatches",
    "criterion_leaks"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    },
    "entries_checked": {
      "type": "integer",
      "minimum": 0
    },
    "head_match": {
      "type": "boolean"
    },
    "terminal_records_for_key": {
      "type": "integer",
      "minimum": 0
    },
    "records_appended_on_replay": {
      "type": "integer",
      "minimum": 0
    },
    "replay_answer_mismatches": {
      "type": "integer",
      "minimum": 0,
      "description": "Keys on which two bindings returned different replay states. The count a store that interprets entries, or an identity computed below the boundary, makes non-zero."
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
| core-ledger owns the contract - append-only, the deduplication authority, the entry kinds, the four replay states and the pinned head (F-b2-06). This skill adds only how it is built: an implementation that offers an update call, drops the head parameter, or lets a store decide what a duplicate key means has produced a defect, not an optimisation. | sourced | `F-b2-06` "append-only across runs; the deduplication authority" |
| The append path links no store-specific code. agentic-stack and build-adapter-pair state the swap test (F-meta-04); the build-level consequence is that the module holding the entry constructor, the identity and the fold imports nothing from a binding, so it compiles and its unit tests run with no store present at all, and a build in which they cannot is where the boundary went wrong. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| Proposed: the entry's identity is computed above the store. The canonical body is hashed and chained on the previous entry's hash before any binding is called, so two stores that order or encode differently still produce the same head; a store that assigns identity has made the receipt depend on which store happened to answer. Research query: is there a fetched source on computing content-addressed identity above the storage binding rather than inside it, beyond F-a5-03's description of the current task store's own chaining? | proposed | `F-a5-03`, `X-core-ledger-002` |
| Proposed: key uniqueness is enforced above the binding, never delegated to a store feature. One role can refuse a duplicate terminal key at commit and the other cannot, so a design that leans on that refusal is a design that only works on one store - the binding records enforces_key_uniqueness and the append path checks regardless. Research query: is there a fetched source distinguishing a store-level unique-key refusal from an above-the-binding uniqueness check, beyond F-b4-08's general idempotency-replay requirement? | proposed | `F-b1-04`, `F-b4-08` |
| Proposed: the store holds opaque entries and never interprets one. Entries go in, entries come back in fold order, and every projection - the head, the deduplication table, the open-work list - is computed above the binding; a store that knows a terminal entry from an approval has taken the ledger's job into the persistence boundary. Research query: is there a fetched source on an opaque-entry store versus one that interprets an entry kind, beyond F-b5-04's and F-b3-17's one-line state-persistence table entries? | proposed | `F-b5-04`, `F-b3-17` |
| agentic-stack states design rule 7 (F-b1-08, F-b4-01). The consequence on this append path is placement: the acting subject, the correlation attribute, the policy decision and the budget remaining are stamped where the entry is constructed, and there is no flag, entry field or binding option by which a writer can ask to skip one. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| build-evidence-record states the labelling rule (F-part-c-08); the consequence here is that a conformance result is claimed until a run is attached naming the code version and the tree hash under test, and a store swap is exactly the change that looks identical in review and differs in a run. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Apply build-adapter-pair: the two binding records differ on at least one axis of differs_in_execution_model, and two bindings identical on every axis are one store written twice and fail the pair check; proposed pointer, see that skill. | proposed | `F-b1-04` "Every interface ships with at least two adapters" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: which binding served a read, the store's layout or connection topology, its lease mechanism, its transaction boundaries and its retention class. A caller sees entries, a head and a replay answer; anything else it can see it will eventually depend on, and the swap stops being possible. | sourced | `F-meta-04` "Part A names products. Part B names capabilities and the standard that governs each." |
| Proposed: criterion text, in any entry field this code writes. core-ledger states the grader rule for this component (F-b1-07); the build consequence is that a judged entry is constructed from the criterion handle and the verdict alone, and the lint in step 8 is what keeps that true after the next refactor of the judge's caller. | sourced | `F-b1-07` "never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the entry constructor, the identity and the fold as a module that imports no binding: it takes entries and returns a head, a replay answer and the derived views. Put the binding behind a port with three calls - append conditional on a head, read entries from a head, and current head - and nothing else. | core-ledger requires the derived views to be recomputable from entries alone; the only way that survives a deadline is to make a store unreachable from the fold, so the dependency arrow is enforced by the build rather than by review. | sourced | `F-b1-02`, `X-core-ledger-003` "the system state is reconstructed by replaying events from an append-only log" |
| 2 | Give each producer a thin mapper into that one constructor. TARGET T1's three ways in - a human, an agent, and an internal or external event - share it; a mapper may translate its payload and may not add an entry field, default a kind, or mint a key on the way in. | core-ledger requires one entry shape whichever way the work came in; making the constructor the single writer of the chain and cross-cutting fields is what stops a fourth mapper from quietly appending an entry with no key and no correlation. | sourced | `T-t1-03`, `T-t2-03` "An internal or external event must be able to enter the system." |
| 3 | Compute the entry's identity before you call the binding: canonicalise the body, hash it with the previous entry's hash, and hand the store a finished entry. Make the append conditional on the head the writer last saw, and treat a refused append as a lost race to retry from a fresh head, never as an error to log and continue past. | Two stores that encode or order differently must still produce one head, and an unconditional append is how a second writer forks the chain instead of failing; the conditional append is the general form of the property the store running today already has. | sourced | `F-a5-03`, `X-core-ledger-002` "SHA-256 hash chain integrity proofs" |
| 4 | Serve the replay answer from a projection keyed by idempotency key that is rebuilt by folding the entries, and check the terminal-key rule in the append path whether or not the binding could enforce it. Record enforces_key_uniqueness on the binding as information, and branch on it nowhere. | build-adapter-pair states why the second adapter exists (F-b1-04); the specific trap here is that one store can refuse a duplicate at commit and the other cannot, so any logic that leans on the refusal passes the conformance run on one binding and silently double-writes on the other. | sourced | `F-b1-04`, `X-core-ledger-004` "the second exists to prove the first is not load-bearing" |
| 5 | Implement the role today against the appended, hash-chained file that holds run state now, and the role second against a transactional store in a server process where an append commits or aborts against the head. Fill in both bindings' execution-model axes before either is used. | build-adapter-pair owns this discipline. The consequence here is specific: a second appended file would leave the fold free to keep every single-writer, whole-file, local-path assumption, and a store whose durability is a commit in another process is what forces the identity above the boundary and the fold to be order-independent. | sourced | `F-b3-17`, `F-b1-04` "object store · relational · event log" |
| 6 | Migrate by backfill, dual-write and answer-compare: derive an idempotency key and an envelope digest for the runs already recorded, write every new entry to both bindings, fold both over the whole corpus, and cut over only when replay_answer_mismatches and head mismatches are zero and the old path has been read-only for a full retention window. Research query: has this backfill-then-compare migration actually been run over the existing ledger corpus to derive keys and digests, or is the procedure reasoned from the digest-chain pattern with no measured run behind it? | Proposed: the risk is not new entries but the old ones, which carry no key and no envelope digest because the deduplication authority does not exist yet; the backfill is where a wrong key becomes permanent, so the compare must run over the backfilled corpus rather than over new entries only. | proposed | `F-a5-03` |
| 7 | Wire the cross-cutting fields into the constructor: stamp the correlation attribute and the acting subject where the entry is built, carry the policy decision that allowed the step, and write the budget remaining after it. Provide no append that omits them. | agentic-stack states design rule 7 (F-b1-08), and the measured trace-context finding is why correlation is an explicit attribute stamped on the entry rather than something inherited from whatever called in; the ledger is where a reader later checks the guarantees actually held. | sourced | `F-b1-08`, `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 8 | Add a lint over the appended entries that greps each declared criterion string against every field of every entry written from that document, and fail the build when the count is non-zero. | core-ledger states the grader rule for this component (F-b1-07); a ledger is read by everything downstream and by every audit, so a criterion that reaches it has escaped every later attempt to hide it, and a rule that is only stated is one the next refactor breaks silently. | sourced | `F-b1-07` "The grader is never visible to the graded" |
| 9 | Proposed: open references/implementation-notes.md when you are writing the fold, the deduplication projection, the backfill, the two binding records or the wiring, or reviewing someone who did. The body of this skill is enough to review a design and to run the definition of done without it. | Proposed: the wiring table, the two binding records and the backfill rules are longer than the progressive-disclosure budget allows in the body, and a reader judging the build does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| build-evidence-record already states the configuration finding (F-a7-04). What it adds here: assert the binding actually in effect at run time and log it beside the counts, because a binding written in the documented place and overridden by a stored row produces a conformance run that folded the same store twice and reported adapters_run=2. | sourced | `F-a7-04` "had no runtime effect" |
| Test reconstruction, not only the chain: fold to an earlier head and compare the derived views against what was recorded at that head, because prior art for hash-chained ledgers sells integrity and reconstruction together, and a chain can verify perfectly over entries a projection has already drifted from. | sourced | `X-core-ledger-002` "enabling complete state reconstruction at any point in time" |
| If a binding ever prunes, require it to rebuild and re-verify the chain as part of the same operation, and to keep the previously sealed head it must still agree with; prior art treats compaction and chain rebuild as one act, and a prune that does not re-verify is indistinguishable from tampering after the fact. | sourced | `X-core-ledger-005` "Compaction prunes old records and automatically rebuilds the hash chain so it stays consistent and verifiable" |
| Proposed: run the conformance over both bindings on every change, not only when a binding changes. The failures worth catching come from the constructor, the mappers and the projection - a new optional field, a changed canonicalisation - and they show as a head that moved while no store was touched. Research query: has running the conformance suite on every change caught a constructor or projection regression in this repo, or is the practice argued from the adapter-pair discipline alone? | proposed | `F-b1-04` |
| build-evidence-record already states what the hash-chained store running today buys (F-a5-03): a closing digest that opens the next run makes an edit between runs detectable. What this adds: carry that property through the migration, because a ledger without it cannot show that a terminal entry was not written after the replay that read it. | sourced | `F-a5-03` "a manual edit between runs is detectable" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | The record store the entries sit in today. PASS.md Part A records the task store as JSONL, hash-chained, with each run's closing digest opening the next. The Ledger is owned core surface with no adapter row of its own, so what is adapted beneath it is the record store its entries round-trip through - the State persistence row - and this skill tests the pair there. | Proposed: cannot refuse a duplicate terminal key by itself, cannot admit concurrent writers without an external lease, cannot return the entries for one key without scanning, and cannot be folded by a reader in another process without sharing a filesystem path; it also carries no idempotency key on the runs already recorded, which is what the backfill in step 6 has to reconcile. | Select the binding by the binding record, point both roles at the same constructor, identity and fold, and run the conformance corpus through both. No core change is expected, because the fold and the projection never see the binding. | claimed | `F-a5-03`, `F-b3-17` "JSONL, hash-chained" |
| `E-swap-candidate-relational` | second | The same append and read over opaque entries, served by a transactional store in a server process: an append commits or aborts against the head the writer last saw, and the chain is carried as an entry field rather than as file order. The row names the candidate class rather than a product, per the State persistence row's own swap column. | Proposed: cannot rely on file order for the fold, cannot be read without a running server, and cannot hand back a filesystem path - which is the point, since anything it cannot implement was store detail that had leaked into the ledger's fold. It can refuse a duplicate key at commit, which is exactly the capability the append path must not depend on. | Proposed: the execution-model axes that must differ are processes_required_for_progress (zero for a local appended file, one for a served store) and locus_of_durability_and_conflict_detection (file order plus an external lease, versus a commit conditional on the head). Run one parameterised conformance over both roles and require identical heads and identical replay answers for every key. | claimed | `F-b3-17`, `F-b1-04` "object store · relational · event log" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/provenance/test.sh && python3 harness/provenance/conformance.py --adapter dryrun --adapter second && bash harness/state-persistence/test.sh && python3 harness/state-persistence/conformance.py --adapter dryrun --adapter second |
| Expected | each test.sh: exit 0, `passed <n>, failed 0`; provenance conformance.py: exit 0, `conformance PASSED: 26/26 cases, 2 binding(s)`; state-persistence conformance.py: exit 0, `conformance PASSED: 22/22 cases, 2 binding(s)`. Proposed tool (not run): python3 tools/ledger_conformance.py --binding bindings/today.json --binding bindings/second.json --corpus fixtures/runs/ --replay-key <k> --criteria criteria.txt --report out/ledger-conformance.json, asserting per binding entries_checked > 0, head_match == true, terminal_records_for_key == 1, records_appended_on_replay == 0, and across bindings adapters_run >= 2, replay_answer_mismatches == 0, criterion_leaks == 0 (docs/decomposition.md section 3.1 row C5). |
| Deliberate breakage | sed -i '43s#.*#DIGEST = re.compile(r"^sha256:[0-9a-f]{63}$")#' harness/provenance/interface.py |
| Expected failure | provenance conformance.py exits 1: the dryrun binding cannot be reached at all (its 64-hex digests no longer match the narrowed 63-hex pattern, `could not be reached`), and every case that carries a subject digest is refused document-invalid with `subjects[0].digest must match sha256:<64 hex>`; git checkout -- harness/provenance/interface.py restores and the state-persistence half is untouched throughout. |
| Status | measured |
| Evidence | `F-part-c-04`, `F-b1-04` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `core-ledger`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| PASS.md Part A records no adapter for the Ledger itself, so which pair does this skill's swap test actually exercise? | The Part B table has no Ledger row: the five components are the owned surface and everything else is an adapter (F-b2-07), so there is no adapter-today column to read. Applying TARGET T5's 1-3-1, the three options were: declare no pair and record the gap, which leaves swappability untested on the component whose absence means nothing survives the run; adapt the record store the entries round-trip through; or defer entirely to the state seam's pair, which duplicates a sibling and tests nothing about deduplication. The second is recommended and is taken in the Adapters section. | The record-store pair above, tested by the conformance run; if a Ledger adapter row is ever added to PASS.md, this question is reopened against it. | `F-b2-07`, `T-t5-02` "Everything else is an adapter." |
| Is the deduplication projection kept in the store, or rebuilt in the process on start? | Measure rebuild wall time at today's entry count and at a hundred times it, against how often a process starts. A rebuild that is cheap at both makes a stored projection pure cost; one that is not is the first thing to make incremental, with the fold still the authority. | Rebuilt by folding, with a checkpoint added only on a measured trigger. A projection the store owns becomes a second authority on whether work was done, and the two disagree exactly when it matters. | `X-core-ledger-004`, `F-b1-06` "storing one tuple of the form (key, val, ver) for each unique entry key" |
| Does this build ship a linear chain only, or also the inclusion proof a third party would need? | Count the consumers that must verify one receipt without being handed the whole log. If that count is zero the chain is enough; the first such consumer is what justifies the proof structure and the signing that goes with it. | Chain now, with the entry identity already committing to the canonical body so proofs can be added over the same entries later without rewriting them; build-evidence-record states the provenance requirement (F-b4-05) - verifiable with a tool we did not write - and that is what will eventually force the proof. | `F-b4-05`, `X-core-ledger-005` "verifiable with a tool we did not write" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu |
