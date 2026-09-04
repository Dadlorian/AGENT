# Policy adapters: mapping, subsets, swap runbook

Proposed material. The skill body is enough to build either adapter without this file; open it when you
need the per-engine mapping table, the conformance subsets, or the ordered swap runbook.

## 1. Mapping table

One row per element of the interface `cap-policy` fixes. "A" is the out-of-process document query that
wraps the engine already provisioned for the policy concern (claimed, per PASS.md A5). "B" is the
in-process typed-entity evaluator that denies by default.

| Interface element | A: out-of-process document query | B: in-process typed entity |
|---|---|---|
| `decide` | POST canonical `DecisionRequest` to a local decision endpoint; read JSON back | direct function call; entities marshalled from the same canonical request |
| `activate(bundle)` | load a digest-addressed bundle; engine reloads in place | rule set compiled into the deployed artifact; activation is a redeploy |
| `policy_version` | bundle digest reported by the engine at query time | digest of the compiled rule set, baked at build time |
| `rule_id` | identifier carried in the rule's own result object | identifier attached to the matching policy in the compiled set |
| `explain` | re-query the pinned bundle with the recorded input | re-evaluate the recorded input against the pinned compiled set |
| `register_decision_point` | schema held by the platform registry, checked before the query | schema held by the platform registry **and** mirrored in the entity type |
| Failure of the engine itself | `adapter-unavailable`, retryable | not reachable: an in-process failure is a crash of the caller |

The last row is the sharpest difference and it is the reason the pair proves something: A can be down while
the platform is up, and B cannot.

## 2. Declared conformance subsets

An engine that cannot serve a registered decision point declares it here rather than answering `allow`.

| Decision point | A | B | Note |
|---|---|---|---|
| `dispatch-admit` | serves | serves | |
| `tool-invoke` | serves | serves | B is the cheaper of the two on this hot path |
| `model-call` | serves | serves | |
| `state-append` | serves | serves | |
| `artifact-export` | serves | **subset**: destination classes only | B cannot evaluate over an open destination document |

A subset row is a claim that must be re-checked whenever either engine changes; an empty subset column on a
pair that has never run is not evidence of coverage.

## 3. Swap runbook

1. Confirm both engines are built and both are selectable by configuration only. A code edit between runs
   is not a swap; `selected_by` in the report must read `configuration`.
2. Freeze the rule source table and recompile for both engines. Record the two `policy_version` digests.
3. Run the P10 conformance command against A, then against B, with no other change.
4. Merge the two reports. Assert `adapters_run == 2` and `decisions_agree == true`.
5. Classify every disagreement before changing anything: a disagreement is either a translation defect in
   the rule table, or an interface leak. Only the second justifies touching `cap-policy`.
6. Write both runs to the evidence store with the code version, the tree hash and whether the tree was
   dirty, in the form `build-evidence-record` fixes. Label them `claimed` until they have been run.

## 4. Migration checkpoints

Each step is independently revertible; the order matters because every step but the first depends on the
previous one being observable.

| # | State | Observable when done |
|---|---|---|
| 0 | Rule sets exist, nothing consults them (`F-a6-04`) | the starting state, recorded, not a defect introduced here |
| 1 | `decide` wraps the provisioned engine | a decision can be requested by hand and returns a `Decision` |
| 2 | Decision-point registry stands up | an unregistered point is refused, not defaulted to allow |
| 3 | `policy-decided` record written on every decision | the record count equals the decision count, allows included |
| 4 | Consultation moved ahead of the first metered call | `decided_before_first_metered_call == decisions_taken` |
| 5 | Second engine selectable | `adapters_run == 2` in the merged report |

Step 4 is the one that closes the gap `F-a6-04` records. Steps 1 to 3 make it measurable; without them,
step 4 is a claim about code rather than an observation.
