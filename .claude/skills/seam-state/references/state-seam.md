# State seam: the long material

Opened from instruction 10 of `seam-state`. The skill body is enough to decide where a record goes and what a
read may assume; this file carries the four things that are too long to state there. Everything below is
**proposed** and taken from `docs/decomposition.md` section 2.2 unless a kb id is named. Source ids resolve with
`python3 tools/kb.py show <id>`.

## 1. The closed record-kind list (canonical, version 1)

**This table is the one canonical enumeration of record kinds.** Every other appearance of the kind
list anywhere in this repo — the `StateRecord` example in `SKILL.md`, the full-shape schema in
section 2 below, the prose in `docs/decomposition.md` 2.2.1, and any future generated doc — derives
from it and must name the same ten kinds, in count and in membership. `tools/check_record_kinds.py`
parses this table plus every other occurrence and fails the build on a mismatch, so a change in
cardinality here can no longer silently diverge from a paraphrase elsewhere. A change to the list
bumps the version above; readers must know which version of a kind an old record was written under
(see `kind_version` in section 2).

One log holds all of it. The kind is what this seam interprets and what the store beneath it never reads
(`cap-state-persistence` keeps the record opaque).

| Kind | Written when | Folds into |
|---|---|---|
| `node-asserted` | a typed node enters the graph | the graph projection (`core-graph`) |
| `edge-asserted` | a typed existence, interface or implementation edge is asserted, or withdrawn by setting `retracts` | the graph projection |
| `document-declared` | a document is declared and validated | `get_document` |
| `dispatch-submitted` | one unit of agent work is submitted | `open_dispatches`, `prior_result` |
| `dispatch-observed` | that unit reaches a terminal or partial state | `open_dispatches`, `cost_history` |
| `ledger-entry` | anything the ledger is the authority for, including spend | the ledger projection (`core-ledger`) |
| `policy-decided` | a policy decision is taken, carrying its `rule_id` | the policy audit projection |
| `attestation-recorded` | a statement over an artifact digest is recorded (`xc-provenance-chain`) | provenance closure |
| `head-sealed` | a run closes: `{tree_size, root_hash, chain_digest, sealed_at}` | cross-run continuity |
| `tombstone` | a body is redacted; `record_id` is preserved and the authority recorded | nothing; the chain is unaffected |

Withdrawal is a new record naming the one it withdraws. There is no update and no delete.

## 2. The full record shape

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:seam-record:0.1",
  "title": "StateRecord",
  "type": "object",
  "additionalProperties": false,
  "required": ["record_id", "prev_record_id", "chain_digest", "kind", "run_id",
               "fencing_token", "written_at", "declared_by", "body"],
  "properties": {
    "record_id":      { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                        "description": "sha256 over the RFC 8785 canonical JSON of body." },
    "prev_record_id": { "type": ["string", "null"], "pattern": "^sha256:[0-9a-f]{64}$" },
    "chain_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                        "description": "sha256(prev_chain_digest || record_id)." },
    "kind":           { "enum": ["node-asserted", "edge-asserted", "document-declared",
                                 "dispatch-submitted", "dispatch-observed", "ledger-entry",
                                 "policy-decided", "attestation-recorded", "head-sealed",
                                 "tombstone"] },
    "kind_version":   { "type": "integer", "minimum": 1, "default": 1,
                        "description": "Old records stay as written, so a fold must know which version it reads." },
    "run_id":         { "type": "string", "description": "The write partition." },
    "fencing_token":  { "type": "integer", "minimum": 0 },
    "written_at":     { "type": "string", "format": "date-time" },
    "declared_by":    { "type": "string",
                        "description": "user: | agent: | service: | schedule: prefix, per TARGET T1 and T6.2." },
    "correlation":    { "type": "object",
                        "description": "run id and root dispatch id, stamped by the platform on the append path." },
    "retracts":       { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "body":           { "type": ["object", "null"],
                        "description": "Null only for a tombstone; record_id still commits to the original body." },
    "retention": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "class":      { "enum": ["chain", "body", "payload"] },
        "expires_at": { "type": "string", "format": "date-time" },
        "hold":       { "type": "boolean", "default": false },
        "redacted_by":{ "type": "string" },
        "authority":  { "type": "string" }
      }
    }
  }
}
```

## 3. The eight projections a planner may read

Every one takes `at_head` and is deterministic at that head; `resolve_head` is the only call whose answer moves,
and it is made once before planning starts. This is design rule 5 made checkable (`F-b1-06`).

| Projection | Signature | Why the planner needs it |
|---|---|---|
| `resolve_head` | `resolve_head(run_id) -> {tree_size, root_hash, chain_digest, sealed}` | Pins the snapshot everything else reads at. |
| `get_document` | `get_document(document_id, at_head) -> Document` | The plan is a function of the document. |
| `neighbors` | `neighbors(node_id, edge_type, direction, at_head) -> [node]` | Expanding a step into candidates is a walk over typed edges. |
| `path_exists` | `path_exists(from, to, edge_types, max_depth, at_head) -> {found, path}` | Answers reachability without loading the graph. |
| `prior_result` | `prior_result(idempotency_key or document_digest, at_head) -> result or null` | The ledger is the deduplication authority; a planner that cannot ask plans work already done. |
| `cost_history` | `cost_history(selector, window, at_head) -> {p50_micros, p95_micros, n}` | Turns a cost prediction into a lookup, which is what makes purity affordable. |
| `open_dispatches` | `open_dispatches(run_id, at_head) -> [dispatch]` | Non-terminal work from a prior run is reconciled, not re-planned. |
| `verify` | `verify(record_id, at_head) -> inclusion_proof` | Lets a consumer we did not write check one record without the log. |

Adding a ninth means adding a row here first, then to the `projection` enum in the skill's `ProjectionQuery`
shape. A projection that would need to read the live head is not a projection.

## 4. Retention, and redaction that keeps the proofs

| Class | Content | Default retention | Deletable |
|---|---|---|---|
| chain | record headers: `record_id`, `prev_record_id`, `chain_digest`, kind, timestamps, sealed heads | forever | no |
| body | the record's fields | 400 days | yes, by tombstone |
| payload | large artifacts referenced by digest | 90 days, extendable by a hold flag | yes, by tombstone |

The chain commits to `record_id`, which is the digest of the canonical body, and never to the body itself. So a
body may be replaced by a tombstone that preserves `record_id` and records who redacted it and under what
authority: the chain and every inclusion proof still verify, because neither ever needed the body. A `hold`
suspends expiry, and a hold is itself a record.

## 5. What this file does not carry

The store beneath the seam - `append`, `read_at`, `prove`, the head shape and the inclusion-proof shape - belongs
to `cap-state-persistence` and its `references/state-shapes.md`. Independent monitoring of the sealed heads
belongs to `xc-audit-trail`, because a transparency log is tamper-evident and not tamper-proof
(`X-cross-structure-053`). The failure objects belong to `cap-errors`.
