# Memory adapters: mapping tables, shadow migration, refusal placement (proposed)

Proposed long material for `cap-memory-implement`. The body of that skill is enough to build and
review either adapter without this file; open it when writing a binding record, running the shadow
migration, or deciding what a store must refuse rather than default.

## 1. Operation mapping, per adapter (proposed)

| cap-memory operation | Ranked store (role today) | Scope-keyed file store (role second) |
|---|---|---|
| `remember` | embed body, write with scope tags and `expires_at` as store metadata | append a record under `scope_key(scope)`; fsync; no embedding |
| `recall` | search with a filter built from the selector, then drop candidates past `expires_at` | read the document at the scope key, drop expired records, select on `key` or a substring of `need` |
| `supersede` | write the replacement, then update the old record's `superseded_by` and exclude it from search | append the replacement and rewrite the previous record's `superseded_by` field in place |
| `forget` | delete by id, or by filter for a scope-wide erasure | delete the record; a scope-wide erasure removes the document |

Two rules hold in both columns: the scope filter is compiled into the query, and expiry is compared
on read (`expiry_enforcement` must contain `on-read` in the binding record).

## 2. What each adapter refuses rather than defaults (proposed)

| Condition | Refusal type | Why not a default |
|---|---|---|
| write with no `staleness` object | `urn:agentic:problem:memory-staleness-policy-missing` | a defaulted TTL is invisible and becomes permanent by accident |
| recall with an empty scope selector | `urn:agentic:problem:memory-scope-required` | an unfiltered search is the cross-tenant failure mode |
| recall naming a scope the actor does not hold | `urn:agentic:problem:memory-scope-denied` | returning zero would hide a permission bug as an empty result |
| store unreachable | `urn:agentic:problem:memory-store-unavailable` | empty means "nothing learned"; unavailable means "do not proceed as if nothing was learned" |

## 3. Shadow migration (proposed)

There is nothing to migrate from: no memory store appears anywhere in PASS.md's inventory. What is
being replaced is the practice of handing a run its predecessor's whole transcript.

1. **Write-alongside.** Every run that would hand over a transcript also writes items. Nothing reads
   them. Measure: items per run, and how many carry a non-default expiry.
2. **Read-and-diff.** Runs receive both the transcript and a recall. Record, per run, whether the
   recall contained what the run actually used from the transcript. Measure: `recall_covered_use`.
3. **Transcript off, diff on.** Stop passing the transcript; keep writing the diff record for a
   period long enough to include a slow-moving workflow.
4. **Delete the hand-off path.** Only once `recall_covered_use` has held above the agreed threshold
   for the whole period.

Each step is an evidence record, per `build-evidence-record`, naming the command, the code version,
the tree hash and whether the tree was dirty.

## 4. Binding record example (proposed)

```json
{
  "binding_id": "memory-today",
  "role": "today",
  "retrieval_model": "ranked",
  "scope_dimensions": ["principal", "agent", "run", "org"],
  "expiry_enforcement": ["on-read", "swept"],
  "declares": {
    "reached": "reported by the adapter at start-up, compared against this value; start-up fails on a mismatch",
    "trust_anchor": "the credential set the adapter authenticated with"
  }
}
```
