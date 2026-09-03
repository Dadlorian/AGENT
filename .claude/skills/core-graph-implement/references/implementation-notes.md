# Graph implementation notes: fold, bindings, backfill and wiring

Long material for `core-graph-implement`. Everything here is **proposed** unless a kb id is given beside
it. The skill body is enough to review a design and to run the definition of done; open this file when
writing the fold, the backfill, the binding records or the cross-cutting wiring.

Resolve every id with `python3 tools/kb.py show <id>`.

## 1. Module boundaries

| Module | Imports | Must not import | Why |
|---|---|---|---|
| `graph/types` | nothing | anything | the closed kind set and the three edge types as data |
| `graph/check` | `graph/types` | any store, clock or network module | `validate` is a pure function of a graph value (`core-graph`) |
| `graph/fold` | `graph/types`, the persistence interface | `graph/check` | records in, graph value out; folding is not type checking |
| `graph/assert` | `graph/types`, `graph/fold`, the cross-cutting wiring | a concrete binding | the single writer of node and edge fields |

The build check that makes this real: compile and run `graph/check`'s test suite in an environment with no
binding configured and no persistence package installed. If it fails to import, the boundary is wrong,
which is the invariant "the type checker links no persistence code" expressed as a command.

## 2. The two binding records (proposed)

```json
{
  "role": "today",
  "record_kinds": ["node-asserted", "edge-asserted"],
  "fold_order": "by record identity, ascending; file order is not consulted",
  "serves_walk": false,
  "differs_in_execution_model": [
    {"axis": "processes_required_for_progress", "today_value": "zero; the asserter appends to a local file it holds open", "second_value": "one; a served log the asserter and every reader connect to", "measured": false},
    {"axis": "locus_of_durability_and_verification", "today_value": "file order plus a linear chain over the whole file", "second_value": "a per-record position plus a digest recomputed from the record body", "measured": false}
  ]
}
```

```json
{
  "role": "second",
  "record_kinds": ["node-asserted", "edge-asserted"],
  "fold_order": "by record identity, ascending; cursor order is not consulted",
  "serves_walk": false,
  "differs_in_execution_model": [
    {"axis": "processes_required_for_progress", "today_value": "zero; the asserter appends to a local file it holds open", "second_value": "one; a served log the asserter and every reader connect to", "measured": false},
    {"axis": "locus_of_durability_and_verification", "today_value": "file order plus a linear chain over the whole file", "second_value": "a per-record position plus a digest recomputed from the record body", "measured": false}
  ]
}
```

Both bindings pin `fold_order` to record identity rather than to arrival, which is what makes the fold
order-independent and lets the conformance run assert `verdict_mismatches == 0` at all. Two bindings whose
`differs_in_execution_model` arrays are equal on every axis are rejected by the pair check before the
conformance run is worth reading (`build-adapter-pair`).

## 3. Backfill rules for the migration (proposed)

The records that exist today carry no kind, because the typed graph does not exist yet. The backfill is
the only step in the migration that can make a wrong fact permanent, so it is conservative by
construction:

| Recorded today | Backfilled kind | Rule |
|---|---|---|
| a declared unit of work | `document` | one node per declaration, named by its document id |
| a step inside a declaration | `step` | one node per step, named `<document_id>.<step_id>` |
| a named thing a step asked for | `interface` | only where the same name is asked for by two or more steps |
| a runnable that served a step | `implementation` | only where a run record names it as having served |
| anything else | *no node* | left unbackfilled and counted; an unbackfilled record is a finding, not a default |

Two rules make this safe. First, no kind is ever inferred from a string that a human typed freely: an
unrecognised record produces no node and increments an `unbackfilled` count that the migration report
carries. Second, the backfill emits `existence` and `interface` edges only, never an `implementation`
edge, because "this thing implements that interface" is a claim nobody made in the old records and
inventing it would defeat the very type rule the property test protects (`core-graph`, F-b1-02).

Cut-over gate: `verdict_mismatches == 0` over the fully backfilled corpus, `unbackfilled` reviewed row by
row, and the old path read-only for a full retention window.

## 4. Cross-cutting wiring table (proposed)

| Concern | Where it attaches | What makes it non-declinable |
|---|---|---|
| Correlation | in `graph/assert`, as an explicit resource attribute on the record | the constructor sets it; no record field or binding option carries an override (F-a7-02) |
| Policy | consulted in `graph/assert` before the record is appended | the append call is unreachable except through the path that consults |
| Provenance | the record digest is attested at append | the binding refuses a record with no attestation reference |
| Budget | read from the entry envelope as a constant | `on_exceed` terminates the unit; there is no per-assertion ceiling to raise |

Design rule 7 is what this table implements, and `agentic-stack` states it (F-b1-08). The build test is
not that each row exists but that no path reaches `append` without passing through `graph/assert`: a
second entry point into the store is how a concern silently becomes optional.

## 5. The criterion lint (proposed)

For each document, for each declared definition-of-done check, grep the criterion string against every
node `attributes` value and every edge `label` written from that document, and report
`criterion_leaks`. The lint runs over recorded assertions rather than over source, because the leak that
matters is the one a mapper introduced at run time. `core-graph` states the rule (F-b1-07); this is the
command that makes it fail.
