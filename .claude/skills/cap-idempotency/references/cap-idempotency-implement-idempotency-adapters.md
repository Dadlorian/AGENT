# Idempotency adapters: mapping, failure modes, swap runbook

Long material for `cap-idempotency-implement`. Proposed: the skill body is enough to build
either adapter; open this when you are mapping the claim onto a store, deciding what an
adapter may honestly claim, or running the swap. Ids resolve with `python3 tools/kb.py show <id>`.

## 1. Mapping the claim onto each adapter (proposed)

| Claim operation | Fold over the append-only log at entry | Conditional-write lease |
|---|---|---|
| `claim` fresh | No completed record found for the key; execution proceeds | Compare-and-set inserts the claim; exactly one caller wins |
| `claim` duplicate, sealed | Completed record found, digests equal, recorded result returned | Claim row in state `sealed`, `result_ref` returned |
| `claim` duplicate, in flight | **not supported** — an unfinished execution has written no completed record | Claim row in state `in_flight`, answered with `in_flight: true` |
| `claim` conflict | Completed record found, digests differ | Claim row found, digests differ |
| `complete` | The completion record already written to the log is the seal | Update to `sealed` guarded by the fencing token |
| `resolve` | Scan or index the log by key | Point read on the key |
| `expire` | Inherited from the log's retention; not independently declarable | Declared `retention_s` on the row |

The "not supported" cell is the whole reason the pair proves something. It is declared, not
hidden: an adapter that answered `in_flight: false` there would be reporting a property it
cannot provide.

## 2. What each adapter can and cannot detect (claimed)

| Duplicate arrives… | Fold | Lease |
|---|---|---|
| after the first finished | caught | caught |
| while the first is still running | **missed, both execute** | caught |
| after the retention window | correctly treated as fresh | correctly treated as fresh |
| with a different payload | conflict | conflict |
| when the claim store is unreachable | still works, the log is local | fails closed; execution must not proceed |

The last row is the one to decide deliberately. Proposed: fail closed. A lease store that is
down is not a licence to execute twice; it is a `adapter-unavailable` problem from `cap-errors`
with `retryable: true`.

## 3. Swap runbook (proposed)

1. Confirm both adapters are registered behind the single claim call and that nothing outside
   that call reads the idempotency key to make a decision.
2. Run the race suite with `--adapter log-fold-at-entry`. Record the report.
3. Change configuration only — no code edit, no rebuild of the caller — and run with
   `--adapter conditional-write-lease`. Record the report.
4. Assert the merged report shows `adapters_run == 2` and `selected_by == "configuration"`.
5. Assert the fold's declared conformance subset matches what it actually reported: it must
   have skipped the `overlapped` assert, not passed it.
6. Apply the breakage from the definition of done to the lease adapter alone and confirm the
   fold run is unaffected. A breakage that fails both adapters was applied above the interface.
7. Write both runs and the breakage run to the evidence store in the form `build-evidence-record`
   fixes, and label them claimed until they have been run against a real implementation.

## 4. Cross-cutting wiring checklist (proposed)

- Entry path: every externally-triggered arrival claims before planning. No flag skips it.
- Step recorder: every recorded step boundary claims a derived key before its side effect.
- Correlation: the explicit correlation attribute is copied onto the claim, because a duplicate
  that never executed leaves no other trace (`F-a7-02`, stated by `agentic-stack`).
- Failure: conflicts and unreachable claim stores return registered problem types from
  `cap-errors`; this capability defines no failure object.
- Evidence: the race run, the breakage run and the swap are recorded per `build-evidence-record`.
