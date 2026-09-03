# State persistence adapters — long material

Open this when you need the per-adapter mapping, the failure each adapter can and cannot detect, or
the swap runbook. The skill body is enough to build either adapter without it. Everything here is
**proposed** unless a kb id is given.

## 1. Operation-by-operation mapping

| Operation (cap-state-persistence) | `jsonl-hash-chain` | `merkle-object-store` |
|---|---|---|
| `append` | Write one line, `prev_record_id` = the id of the last line, chain digest folded forward. Conditional append is a compare-and-swap on the in-memory head plus a fencing token checked against a lease file. | PUT the record as an immutable object named by its content address, add the leaf to the tree, then compare-and-swap the head object. The PUT is idempotent because the name is the digest: a retried write is a no-op. |
| `resolve_head` | Read the last line of the file. | GET the head object. |
| `read_at` | Scan forward to the record whose chain digest equals the pinned head, then filter. Cheap while the file is small. | Resolve the tree at that head and fetch by content address. Never a listing, which is eventually consistent. |
| `prove` | Unsupported before the tree lands (`null` in the report, not `false`). After it, the proof is computed from the persisted tree. | Native: the proof is a path of sibling digests read from the tree objects. |
| `prove_consistency` | Same: unsupported, then computed from two persisted tree states. | Native, between two head objects. |
| `redact` | Rewrite the line with the body replaced by a tombstone, keeping `record_id` and `chain_digest`. The file is mutated in place, which is the one operation that makes this adapter's durability assumptions visible. | Write a tombstone object and advance the head; the original object is deleted by lifecycle rule. Nothing is mutated. |

## 2. What each adapter can and cannot detect

| Failure | `jsonl-hash-chain` | `merkle-object-store` |
|---|---|---|
| A record body edited in place | Detected by rehash, at the cost of reading the whole file | Detected by the inclusion proof for that record alone |
| A record removed from the middle | Detected: the chain breaks at that index | Detected: the consistency proof between the two heads fails |
| A whole run's file replaced with a self-consistent forgery | **Not detected** without an external copy of the sealed head | Detected if the head object is signed or published |
| Two writers forking the log | Detected only after the fact, by a fold that disagrees, unless the lease is present | Detected at write time: the head compare-and-swap fails |
| A reader served a stale snapshot | Not distinguishable from a correct read at an older head — this is why every read carries `at_head` |

## 3. Swap runbook

1. Bring both adapters to the same record sequence: replay the 1500-record fixture through each.
2. Select the adapter by configuration only — one environment value, no import change, no branch in a
   caller. A code edit between runs is not a swap (`F-b1-04`, stated by build-adapter-pair).
3. Run the identical conformance suite against each and merge the two reports.
4. Require `adapters_run == 2`, `selected_by == "configuration"` and `head_digests_equal == true`.
   Equal heads over the same sequence is the assertion that says the two really implement one
   interface rather than two similar ones.
5. Record unsupported members as `null`, never as `false`. A stage that never ran and a stage that
   failed are different facts (`F-a7-03`, stated by build-definition-of-done).
6. Write both runs and the breakage to the evidence store in the form build-evidence-record fixes,
   labelled `claimed` until they have actually been executed.

## 4. Migration order, and what each stage is revertible by

| Stage | Adds | Reverted by |
|---|---|---|
| 1 | `record_id` over canonical bytes, written into each record | Ignoring the field |
| 2 | Merkle tree over those ids, sealed head per run | Stopping the tree writer; the chain is untouched |
| 3 | Fencing lease, conditional append | Dropping the token check; the store keeps working with one writer |
| 4 | `merkle-object-store` adapter behind the same interface | Switching the configuration value back |

No stage rewrites a record already written, which is what makes each one revertible without a
restore. The file adapter is never deleted: an interface with one surviving implementation drifts
back into the shape of whatever runs.
