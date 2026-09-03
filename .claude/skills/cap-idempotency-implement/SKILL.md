---
name: cap-idempotency-implement
description: How to build the Idempotency capability on this stack: what the key on the wire already gives you and what it does not, a first enforcing adapter that folds the append-only log at entry, a second with a different execution model that takes a conditional-write lease before execution, the migration between them, where the claim is wired so no entry can skip it, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that decides a request is a repeat, when adding a claim to an entry or a step boundary, when choosing where the claim record is stored, when two copies of one request can be in flight at once, or when a conformance run reports more than one execution under a single key.
---

# cap-idempotency-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-idempotency into something that runs here: one claim call, two adapters behind it whose execution models differ, and every externally-triggered entry and recorded step boundary going through it. | sourced | `F-b3-16`, `F-b4-08`, `E-capability-idempotency` "any keyed lease store" |

## Entities

| Entity |
|---|
| `E-capability-idempotency` |
| `E-adapter-key-on-the-wire` |
| `E-adapter-no-lease` |
| `E-swap-candidate-any-keyed-lease-store` |
| `E-core-component-ledger` |

## Contract

### Shapes (JSON Schema 2020-12)

**IdempotencyConformanceReport (proposed shape; the counters the definition of done below asserts on, per adapter)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:report:0.1",
  "title": "IdempotencyConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "concurrency",
    "executions",
    "duplicates",
    "conflicts",
    "overlapped",
    "adapters_run"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "log-fold-at-entry",
        "conditional-write-lease"
      ]
    },
    "concurrency": {
      "type": "integer",
      "minimum": 1
    },
    "executions": {
      "type": "integer",
      "minimum": 0,
      "description": "Side-effecting executions observed for the one key. Must be 1."
    },
    "duplicates": {
      "type": "integer",
      "minimum": 0
    },
    "conflicts": {
      "type": "integer",
      "minimum": 0
    },
    "overlapped": {
      "type": "integer",
      "minimum": 0,
      "description": "Duplicates answered while the first execution had not finished. 0 means the race never happened."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    },
    "selected_by": {
      "const": "configuration",
      "description": "Recorded at runtime. A code edit between runs would not be a swap."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the claim is taken before the first side-effecting step of the request, never after it. A check that runs after the effect can report a duplicate but cannot prevent one, which is the difference between deduplicating and counting. Research query: is there a recorded conformance run showing a post-effect check reporting a duplicate it could not prevent, which would turn this into a measured distinction rather than an asserted one? | proposed | `F-b4-08` |
| Both adapters implement the identical claim and ClaimOutcome from cap-idempotency, and the running adapter is chosen by configuration with no code edit between runs. build-adapter-pair states that the second adapter exists to prove the first is not load-bearing (F-b1-04); what this facet adds is that the selection must be observable in the conformance report, because an unobservable swap is indistinguishable from running the same adapter twice. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| Proposed: the log-fold adapter answers only for keys whose execution has completed, so it must declare in_flight unsupported rather than answer false. A documented conformance subset is honest; an adapter that reports the property it cannot provide is the failure this pair exists to expose. Research query: is there a recorded conformance subset declaration on this stack for an adapter that cannot answer in_flight, confirming this pattern is already used elsewhere rather than proposed fresh here? | proposed | `F-b3-16` |
| Proposed: the payload digest is computed over canonical bytes, so two independent claimants of one key agree on whether the payloads match. Comparing serialised forms would make key ordering or whitespace look like a conflict. Research query: is there a recorded canonicalisation scheme (for example the one cap-idempotency or core-document already fixes for digesting a document) that this row could point to by name instead of asserting canonical bytes afresh? | proposed | `X-cap-idempotency-002` |
| Proposed: exactly one claimant may hold a key at a time, enforced by a conditional write carrying a monotonic fencing token rather than by there being one process. A claimant that paused, was presumed dead and woke up must not be able to seal over a newer claim. Research query: is there a recorded fencing-token mechanism already implemented on this substrate (for a lock, a lease or a queue) that this row could cite by name instead of asserting the pattern fresh here? | proposed | `F-b1-04` |
| The claim is wired into the platform's entry path and its step-boundary recorder, not into each caller. TARGET T2.3, also cited by cap-idempotency and build-definition-of-done, states that every cross-cutting concern is managed across the entire structure, whichever entry point was used; what this facet adds is the wiring rule that a new entry kind inherits the claim by construction, because it reaches execution through the same path. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| Proposed: cap-idempotency already fixes when the idempotency-conflict type is raised and that cap-errors owns the failure shape; this facet adds no failure object of its own and returns the conflict through that same registered type. | proposed | `F-b4-07` |
| Apply build-evidence-record: the race run and its breakage are written to the evidence store naming the code version and the tree hash under test, and stay claimed until they have actually been run here; proposed pointer, see that skill. | proposed | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from what is already true on the wire: the key is carried and required on the entry envelope, and nothing claims it. Do not re-derive the contract; cap-idempotency states the recorded row (F-b3-16) and the replay contract (F-b4-08), and this facet only builds against them. | Proposed sequencing. The field exists, so the first change is enforcement rather than a new envelope; treating this as a green-field capability would put a second key on requests that already have one. | sourced | `F-b3-16`, `F-b4-08` "key on the wire, no lease" |
| 2 | Build the first enforcing adapter as a fold over the append-only log at entry: look for a completed record under this key, compare the stored payload digest with this request's, and short-circuit to the recorded result. Take no new process and no new store. | Demonstrated in examples/end-to-end, where a replayed entry is recognised and nothing is appended. cap-idempotency and agentic-stack both record that the Ledger is append-only across runs and is the deduplication authority; the cheapest correct first step reads it rather than adding a dependency. | sourced | `F-b2-06` "append-only across runs; the deduplication authority" |
| 3 | Build the second adapter as a conditional-write lease taken before execution: a compare-and-set on the key that exactly one claimant wins, holding in-flight state, a fencing token and the declared retention window, released or sealed when execution ends. | Proposed second adapter, per the manifest and the recorded swap-candidate column. It breaks a different assumption than the first: the fold decides after the fact from a completed record and cannot see a request that is still running, while the lease decides before the fact and can answer a duplicate mid-flight. That is the axis the pair has to differ on. Research query: is there a recorded conformance run or evidence record proving the conditional-write lease actually rejects a second concurrent claimant, rather than this being the intended mechanism only? | proposed | `F-b3-16`, `F-b1-04` |
| 4 | Migrate in that order and keep both adapters live behind the same call: key on the wire only, then fold-at-entry, then lease selected by configuration. Do not delete the fold adapter once the lease exists. | Proposed migration. Each step is independently revertible, and keeping the fold is what makes the pair testable later: an interface with one surviving implementation drifts back into the shape of whatever runs. Research query: is there a recorded migration ledger entry from another capability in this platform that kept an earlier adapter live behind the same call after a later one shipped, confirming this is the platform's established pattern rather than invented here? | proposed | `F-b1-04` |
| 5 | Wire the claim at two places only: the entry path every externally-triggered request passes through, and the recorder that writes a step boundary. Give callers no way to pass a flag that skips it. | Proposed wiring, following cap-idempotency's placement rule from TARGET T2.3. Two enforcement points cover every arrival and every retry inside a run; a third would be a caller deciding for itself, which is the property this concern does not have. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |
| 6 | Record on the claim what the platform applies rather than what the caller asked for: the explicit correlation identifier, the actor, the entry kind and the retention window. Branch on none of them. | Proposed. agentic-stack states the correlation finding (F-a7-02); the consequence here is that a duplicate answered from a claim is often the only record that the second request ever arrived, so the fields have to be on the claim rather than only on the execution that never happened. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch." |
| 7 | Apply build-adapter-pair: run one conformance run parameterised over the adapters, selected by configuration with no code edit between runs, and record `selected_by` and the adapter that actually answered in the one report shape; proposed pointer, see that skill's references/conformance-run-shape.md. | The parameterised suite and the configuration-only swap are build-adapter-pair's step; the report shape it did not state was added there as references/conformance-run-shape.md rather than written out again in five capability skills (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-b1-04` "Every interface ships with at least two adapters" |
| 8 | Open references/idempotency-adapters.md when you need the per-adapter mapping table, the failure modes each adapter can and cannot detect, or the step-by-step swap procedure. This skill body is enough to build either adapter without it. | Proposed, progressive disclosure. The mapping table and the swap runbook are long material that a reader building the first adapter does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Prove the lease with overlap, not with repetition. Concurrency handling is exactly what differs between implementations of this convention, and a suite that fires requests one after another passes on an adapter with no lease at all. | sourced | `X-cap-idempotency-007` "concurrency handling all differ between providers" |
| Keep a uniqueness constraint under the claim as the last line: use database constraints as your final safety net for critical operations. If the claim is ever bypassed by a code path nobody remembered, the constraint is what turns a double effect into a failed write. | sourced | `X-cap-idempotency-006` "use database constraints as your final safety net for critical operations" |
| Verify the runtime effect of the retention window rather than the file that declares it, the same discipline build-evidence-record and agentic-stack apply to a case where configuration written in the documented place had no runtime effect (F-a7-04); a window is only observable by claiming a key, waiting past the window and claiming it again, which is a test, not a review. | sourced | `F-a7-04` "had no runtime effect" |
| Give every claim the same shape whichever entry kind produced it, and resist an entry-specific fast path, following TARGET T2.3's rule (also cited by cap-idempotency and build-definition-of-done) that every cross-cutting concern is managed across the entire structure whichever entry point was used. The moment one kind of arrival claims differently, the concurrent case has to be re-proved for each kind. | sourced | `T-t2-03` "managed across the entire structure, whichever entry point was used" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-key-on-the-wire` | today | What is recorded today is the key on the wire, no lease: the key is carried, required on the envelope and written into the log, and no call claims it. The first adapter that actually enforces anything, and the one the second is paired against, is the fold over the append-only log at entry described in this skill, which examples/end-to-end runs. | Cannot see a request that is still running, so it cannot answer a duplicate in flight and cannot stop two concurrent copies of one request from both executing. It also depends on the log being readable at entry, so it inherits that store's retention rather than declaring its own. | Introduce the claim call in front of execution, back it with the log fold, and leave the wire format untouched; the envelope field does not change, only who reads it and when. | claimed | `F-b3-16`, `E-adapter-no-lease` "**Idempotency** \| idempotency-key convention \| key on the wire, no lease \|" |
| `E-swap-candidate-any-keyed-lease-store` | second | A conditional-write lease store on a transactional store: claim is a compare-and-set taken before execution begins, carrying a fencing token, in-flight state and the declared retention window, sealed or released when execution ends. | Cannot run with no store of its own, and cannot make progress if that store is unreachable, where the fold needs nothing beyond the log the platform already writes. Its execution model is the opposite of the fold's: it decides before the fact under contention rather than after the fact from a completed record. | cap-idempotency already records the two roles and the axis they differ on (F-b3-16, F-b1-04); what this facet adds is the procedure. Select the adapter by configuration only, run the identical race suite against each, and require the merged report to show adapters_run == 2 with selected_by == configuration and a per-adapter conformance subset recorded for the fold. | claimed | `F-b3-16`, `F-b1-04` "any keyed lease store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/idempotency/test.sh && python3 harness/idempotency/conformance.py --adapter dryrun --adapter second |
| Expected | The gate and the conformance run together prove one claim over a key and a payload digest under a log-fold-at-entry adapter and a conditional-write lease adapter: a replayed key returns the stored result with no second effect, a reused key under a different payload is refused as a typed idempotency-conflict, and the lease adapter alone serialises a 20-way concurrent race to exactly one execution while the fold adapter honestly declares in-flight unsupported (adapters_run=2). Earlier criterion named tools/conformance/idempotency_race.py, replaced by the harness on 2026-09-03. |
| Deliberate breakage | In harness/idempotency/adapters/second.py, remove the `with self._lock:` guard around the conditional write in claim() (replacing it with an unlocked read that widens the race window) and change nothing else (the harness README's breakage); restore with git checkout -- harness/idempotency/adapters/second.py. |
| Expected failure | The lease adapter's 20-way concurrent race case fails: every concurrent copy wins (executions=20, overlapped=0) instead of serialising to one winner, and the conformance run drops to 15/16 cases and exits non-zero naming that adapter; the fold adapter's cases are untouched, which is the point — without a lease every concurrent copy wins, reproducing PASS.md's own row for today (F-b3-16). |
| Status | measured |
| Evidence | `F-b3-16`, `F-b1-04` "key on the wire, no lease" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-idempotency`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which of the two adapters is primary once both exist? | Measure, for the P15 race under each: executions under contention, added latency per request, and the number of separate processes that must be running for a claim to be answered. The last number is the one that decides it, given how much of what is defined here is currently not running. | Proposed: the conditional-write lease is primary because it is the only one of the two that satisfies the concurrent half of the criterion; the fold stays as the second implementation and as the fallback when the lease store is unreachable. | `F-b1-04` |
| Does a step-boundary claim use the same key space as the entry claim, or a derived one? | Count, across recorded runs, how often two different steps of one run would produce the same derived key, and whether any step is re-entered after the run's entry key has been sealed. | Proposed: a derived key of the form entry key plus step identifier, in the same store and under the same retention window, so a step retry is deduplicated without the entry key being released. | `T-t2-03` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-idempotency 2831cb4f, 2026-09-03 |
