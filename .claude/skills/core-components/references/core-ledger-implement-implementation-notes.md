# Ledger implementation notes: bindings, wiring, backfill

Long material for `core-ledger-implement`. Proposed throughout unless a row cites a knowledge-base id; the
skill body is enough to review a design and to run the definition of done without this file. Open it when
you are writing the fold, the deduplication projection, the backfill, the two binding records or the
cross-cutting wiring, or reviewing someone who did.

The contract these notes serve belongs to `core-ledger`; nothing here may relax it. Resolve every id with
`python3 tools/kb.py show <id>`.

## 1. Module layout (proposed)

| Module | Contains | May import |
|---|---|---|
| `ledger/entry.py` | The one entry constructor, the canonical encoding, the identity and chain computation | nothing in `ledger/store/` |
| `ledger/fold.py` | Head, deduplication projection, open-work list, derived views | `ledger/entry.py` |
| `ledger/port.py` | The three-call port: `append(entry, expected_head)`, `read(from_head)`, `head()` | `ledger/entry.py` |
| `ledger/store/today.py` | Role `today` binding | `ledger/port.py` |
| `ledger/store/second.py` | Role `second` binding | `ledger/port.py` |
| `ledger/mappers/*.py` | One thin mapper per producer kind | `ledger/entry.py` |

The arrow that matters is that `entry.py` and `fold.py` import nothing under `store/`. Enforce it with an
import check in the build, not with a review convention: it is the build-level form of the swap test
(`F-meta-04`).

## 2. The two binding records (proposed)

```json
{
  "role": "today",
  "append_conditional_on": "the hash of the last entry the writer read; the append is rejected when the file's last line no longer carries it",
  "fold_order": "file order, which the fold re-sorts by (run_id, seq) so it does not depend on it",
  "enforces_key_uniqueness": false,
  "serves_query": false,
  "differs_in_execution_model": [
    "processes_required_for_progress: 0",
    "locus_of_durability_and_conflict_detection: file order plus an external lease",
    "readers_outside_the_writer_process: only by sharing a filesystem path"
  ]
}
```

```json
{
  "role": "second",
  "append_conditional_on": "a commit that aborts when the stored head differs from the head the writer read",
  "fold_order": "primary-key order within a run partition; the fold applies the same (run_id, seq) sort",
  "enforces_key_uniqueness": true,
  "serves_query": false,
  "differs_in_execution_model": [
    "processes_required_for_progress: 1",
    "locus_of_durability_and_conflict_detection: a commit conditional on the head",
    "readers_outside_the_writer_process: any client of the server"
  ]
}
```

`enforces_key_uniqueness` differs between the roles, and that is the trap the pair exists to expose: the
append path checks the terminal-key rule itself in both cases and branches on this field nowhere. A design
that leaned on the second role's constraint would pass its own conformance run and double-write on the
first (`F-b1-04`).

## 3. Cross-cutting wiring table (proposed)

| Concern | Where it is attached | What the entry carries | How the conformance run sees it |
|---|---|---|---|
| Correlation | The entry constructor, from the envelope | `correlation_id` on every entry | Count of entries with an absent or empty value must be 0 |
| Identity | The entry constructor, from the envelope's actor and chain | `actor`, `delegation_depth` | Same, and the actor must match the envelope's grammar |
| Policy | Before the append is issued | `policy_decision` | An entry with `deny` and a following step entry is a failure |
| Budget | After the step returns, before the append | `budget_remaining_micros` | Monotonically non-increasing within a run |
| Provenance | The identity computation | `hash`, `prev`, `output_digest` | The head recomputes from empty |
| Idempotency | The constructor, from the envelope | `idempotency_key`, `envelope_digest` | Exactly one terminal entry per key |

None of these is a parameter. There is no append that omits them, which is what design rule 7 costs at
this boundary (`F-b1-08`, `F-b4-01`, stated by `agentic-stack`).

## 4. Backfill rules for the migration (proposed)

The runs already recorded carry no idempotency key and no envelope digest, because the deduplication
authority does not exist yet. Backfill is therefore the risky half of the migration, not the dual-write.

1. **Derive, never invent.** A backfilled key is `sha256` over the canonical form of the recorded request
   for that run, prefixed `backfill:`. The prefix means a backfilled key can never collide with one a
   producer minted, and a later audit can tell them apart.
2. **Mark the terminal entry by outcome, not by position.** The last line of a run is not necessarily its
   terminal entry; a run that was killed has no terminal entry at all, and inventing one turns abandoned
   work into work the planner will never retry.
3. **Leave unresolvable runs open.** A run whose request cannot be reconstructed gets no key. It shows up
   in `open_work` and is reconciled by a human, which is the honest outcome.
4. **Compare over the backfilled corpus, not over new entries.** The dual-write window only exercises new
   shapes; the mismatches that matter live in the old ones.
5. **Cut over on two zeros and a window.** `replay_answer_mismatches == 0` and head mismatches `== 0`
   across the whole corpus, and the old path read-only for a full retention window first.

## 5. Migration procedure (proposed)

| Phase | Action | Exit condition |
|---|---|---|
| 0 | Stand up the `second` binding empty; run the conformance corpus through it alone | `head_match=true`, `entries_checked>0` |
| 1 | Backfill keys and digests into a copy of the recorded corpus | Every run has a key, or is listed as unresolvable |
| 2 | Dual-write every new entry to both bindings | No append refused for a reason other than a lost race |
| 3 | Fold both over the whole corpus and compare | `replay_answer_mismatches=0`, heads equal per run |
| 4 | Make the old path read-only | One full retention window with no read failures |
| 5 | Cut over; keep the old path readable | Conformance still reports `adapters_run=2` |

Record each phase's run as an evidence record naming the code version and the tree hash under test
(`F-a5-04`, owned by `build-evidence-record`). A phase without a record is a phase that is claimed.

## 6. What a reviewer should look for

- An `update` or `delete` anywhere in `ledger/store/`.
- A branch on `enforces_key_uniqueness`.
- A projection written by anything other than the fold.
- An append issued without `expected_head`.
- A criterion string in any entry field, which the step 8 lint should already have failed the build on.
