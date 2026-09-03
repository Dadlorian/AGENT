# State persistence — long material

Open this only when you need the full record schema, the planner query table, or the retention
defaults. The skill body is enough to judge an implementation without it. Everything here is
**proposed** unless a kb id is given; resolve any id with `python3 tools/kb.py show <id>`.

## 1. Full record schema (proposed)

The summary shape in `contract.shapes` omits the fields below. The full schema is the one in
`docs/decomposition.md` section 2.2.5, restated here with the kind enum kept open because this
interface treats a kind as an opaque tag (see the invariant on opaque records).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:record:0.1",
  "title": "StateRecord",
  "type": "object",
  "additionalProperties": false,
  "required": ["record_id", "prev_record_id", "chain_digest", "kind",
               "partition", "fencing_token", "written_at", "actor", "body"],
  "properties": {
    "record_id":      { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                        "description": "Digest over the canonical bytes of body." },
    "prev_record_id": { "type": ["string", "null"], "pattern": "^sha256:[0-9a-f]{64}$" },
    "chain_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                        "description": "sha256(prev_chain_digest || record_id)." },
    "kind":           { "type": "string",
                        "description": "Opaque to this interface. The State seam owns the vocabulary." },
    "partition":      { "type": "string", "description": "One writer at a time." },
    "fencing_token":  { "type": "integer", "minimum": 0 },
    "written_at":     { "type": "string", "format": "date-time" },
    "actor":          { "type": "object", "description": "Shape owned by the identity capability." },
    "retracts":       { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                        "description": "Retraction is a new record, never a delete." },
    "body":           { "type": ["object", "null"],
                        "description": "Null only for a tombstone, where record_id still commits to the original body." },
    "retention": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "class":      { "enum": ["chain", "body", "payload"] },
        "expires_at": { "type": "string", "format": "date-time" },
        "hold":       { "type": "boolean", "default": false }
      }
    }
  }
}
```

## 2. The query surface a planner needs (proposed)

`F-b5-05` names the query surface a planner needs as one of the five things this boundary must
specify. Every signature below takes `at_head` and is deterministic at that head; `resolve_head`
is the one exception and is the only call allowed to return a different answer twice.

| Query | Signature | Why the planner needs it |
|---|---|---|
| resolve head | `resolve_head(partition) -> Head` | Pins the snapshot. Called once, before planning starts. |
| get document | `get_document(document_id, at_head) -> Document` | The plan is a function of the document. |
| neighbors | `neighbors(node_id, edge_type, direction, at_head) -> [node]` | Expanding a step into candidates is a walk over typed edges. |
| path exists | `path_exists(from, to, edge_types, max_depth, at_head) -> {found, path}` | Answers reachability without loading the graph. |
| prior result | `prior_result(key, at_head) -> Result or null` | The Ledger is the deduplication authority (`F-b2-06`). |
| cost history | `cost_history(selector, window, at_head) -> {p50, p95, n}` | Turns a cost prediction into a lookup, which is what makes rule 5 affordable. |
| open dispatches | `open_dispatches(partition, at_head) -> [dispatch]` | Non-terminal work from a prior run is reconciled, not re-planned. |
| verify | `verify(record_id, at_head) -> InclusionProof` | Lets a consumer we did not write check one record without the log. |

The four graph- and ledger-shaped rows are the State seam's surface, folded over this store's
opaque records; they are listed here so a reader can see what the store has to make possible, not
because this interface understands a document or an edge.

## 3. Retention classes and defaults (proposed, unmeasured)

| Class | Content | Proposed default | Deletable |
|---|---|---|---|
| chain | record ids, previous ids, chain digests, kinds, timestamps, sealed heads | forever | no |
| body | the record's fields | 400 days | yes, by tombstone |
| payload | large artifacts referenced by digest | 90 days, extendable by a hold | yes, by tombstone |

The numbers are configuration and carry no guarantee until a corpus has been measured; the open
question in the skill body records that. The mechanism is the load-bearing part: a tombstone keeps
`record_id` and the chain position and drops the body, so the chain and every inclusion proof still
verify, because neither ever needed the body — only its digest.

## 4. What a conformance suite asserts per adapter (proposed)

| Assertion | Why it is here |
|---|---|
| `records_written > 1000` | A green run over three records is not a result (`F-a7-03`, stated by build-definition-of-done). |
| `external_head_matches == true` | The head is recomputed by a verifier we did not write, from the records alone. |
| `inclusion_proof_verified == true` | A uniformly random record, proved without the rest of the log. |
| `chain_break_at == -1` | No fork; with the deliberate breakage applied, this becomes the edited index. |
| `concurrent_append_rejected > 0` | Two writers raced and one was refused, rather than both succeeding. |
| `tombstone_proof_still_verifies == true` | Redaction did not invalidate an earlier proof. |
| `adapters_run >= 2` | Swappability is a tested property (`F-b1-04`, stated by build-adapter-pair). |
