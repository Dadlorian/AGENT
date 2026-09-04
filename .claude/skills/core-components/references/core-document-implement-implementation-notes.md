# Building the Document: construction path, wiring, migration

Long material for `core-document-implement`. Everything here is **proposed** unless a kb id is given
beside it. The skill body is enough to review a design and to run the definition of done; open this file
when writing the construction path, the migration script, or the cross-cutting wiring.

Resolve every id with `python3 tools/kb.py show <id>`. The contract itself lives in `core-document` -
this file never restates it.

## 1. Construction path (proposed)

One constructor, three mappers, no other writer of document fields.

| Stage | Does | Must not |
|---|---|---|
| mapper | translates one way in's payload into constructor arguments | add a field, default a value, reorder steps |
| constructor | builds the instance, computes the digest, stamps correlation | consult a model, read a plan, resolve a criterion |
| validate | calls the `cap-document-validation` interface against `urn:agentic:core:document:0.1` | hand-roll a keyword check |
| put | hands opaque bytes plus the digest to the bound store | re-serialise, sort keys, strip whitespace |

The constructor is the single writer. A fourth way in is a fourth mapper and nothing else; if a new intake
path needs a constructor change, the change belongs in `core-document`'s contract, not here.

## 2. Cross-cutting wiring table (proposed)

Design rule 7 is stated in `agentic-stack` (F-b1-08, F-b4-01). This table is only where each concern is
attached on this path.

| Concern | Attached at | Cannot be declined because |
|---|---|---|
| correlation | constructor, as an explicit resource attribute (F-a7-02) | it is a constructor argument with no caller-supplied alternative |
| policy | before the first metered call that the document's steps imply | the constructor returns a handle the dispatcher will not accept unpoliced |
| provenance | attestation over the document digest, at `put` | the store records digest and attestation together or rejects the write |
| budget | ceiling read from the entry envelope, `on_exceed` a constant | the field is a `const` in the envelope schema, so an opt-out is not expressible |

## 3. Binding records (proposed)

```json
{
  "role": "today",
  "schema_store": "schemas/",
  "digest_algorithm": "sha256-over-canonical-json",
  "normalises_on_write": false,
  "differs_in_execution_model": [
    {"axis": "processes_required_for_progress", "today_value": "0, an appended local file", "second_value": "1, a separate server", "measured": false},
    {"axis": "locus_of_durability_and_verification", "today_value": "file order plus a linear chain", "second_value": "a transaction log plus a recomputed digest", "measured": false}
  ]
}
```

The `differs_in_execution_model` shape and its seven axes belong to `build-adapter-pair`; the two entries
above are this pair's values. `measured` stays `false` until a run observed the difference.

## 4. Migration procedure (proposed)

| Phase | Action | Exit condition |
|---|---|---|
| 0 | Inventory the existing corpus; count records with no declared definition of done | a number, recorded |
| 1 | Backfill: each legacy record becomes a document whose `definition_of_done` is the checks that actually ran for it, or a single `well_formedness` check when none did | every legacy record maps or is listed as unmappable |
| 2 | Dual-write every new declaration to both stores | 0 write failures over a full retention window |
| 3 | Digest-compare and byte-compare on read back, across the full corpus | `digest_mismatches == 0`, `byte_mismatches == 0` |
| 4 | Old path read-only | no writer holds it for a full retention window |
| 5 | Cut over; keep the old store readable until phase 3 is re-run against the new primary | the re-run reproduces phase 3's counts |

The risk is phase 1, not phase 3: work recorded today with no declared definition of done was never a real
pass, so backfilling a `well_formedness` check where nothing behavioural ran is the honest mapping and
keeps `behavioural_run == 0` reporting `inconclusive` rather than inventing a history of green runs.

## 5. Criterion-leak lint (proposed)

```
for each document D in the corpus:
  for each check C in D.definition_of_done:
    grep -F -c "C.command" out/recorded-dispatch-requests.jsonl   # must be 0
    grep -F -c "C.expected" out/recorded-dispatch-requests.jsonl  # must be 0
```

`criterion_leaks` in the round-trip report is the sum of those counts. It is asserted `== 0` by the
definition of done in the skill body, and it is the build-time form of the grader rule (F-b1-07) that
`core-document` states on the artifact.

## 6. Evidence record fields (proposed)

`build-evidence-record` owns the record. A round-trip result is `claimed` until one exists naming what was
run, the code version and tree hash under test, whether the tree was dirty, the output, and the status
label. A store swap looks identical in review and differs in a run; the record is the only thing that
separates the two.
