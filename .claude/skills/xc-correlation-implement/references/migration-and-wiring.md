# Correlation on this stack: migration checklist, wiring table, per-adapter conformance subset

Proposed unless a row says otherwise. Open this only when you are wiring a boundary, deploying the second
implementation, or writing the audit; the skill body is enough to plan and judge the build without it.
Every id resolves with `python3 tools/kb.py show <id>`. The guarantee itself, its field set and its scope
belong to `xc-correlation`; nothing here restates them.

## 1. Boundary-by-boundary migration checklist (proposed)

Each row can ship on its own. The order matters only in that the request field has to exist before
anything can read it.

| # | Boundary | Change | Done when |
|---|---|---|---|
| 1 | Dispatch request | Correlation record becomes a required member; a request without it fails validation | A request missing it is refused with the registered type `urn:agentic:problem:document-invalid` |
| 2 | Entry points | Each of the four entries stamps depth 0 and its own `entry_kind` | The audit fixture for each entry produces a record without hand-editing |
| 3 | Child dispatch | `derive_child` at the point the child request is built, never at the point it is emitted | Depth values in the audit cover 0, 1 and 2 |
| 4 | Isolated unit | The record travels as an explicit request field into the unit | The unit's own emissions carry the same `run_id` as its parent |
| 5 | Emission sites | Resource attributes bound once per unit, read by every emitter in that unit | `signals_checked > 0` for the span kind under every entry |
| 6 | Failure path | The record is a declared member of the problem object | `signals_checked > 0` for the problem-object kind; red until typed errors exist (`F-a6-06`) |
| 7 | Ledger records | The record is written beside the actor on every recorded action (`F-b4-03`) | A recorded action can be joined to its run without a second lookup |
| 8 | Pipeline stage | The verifying processor is deployed and its dead-letter count is published | `adapters_run == 2` in the merged report |

Step 6 and step 7 are the two that are usually forgotten, for the same reason: both happen on paths where
the emission context has already been torn down or was never bound.

## 2. Cross-cutting wiring (proposed)

| Concern | What correlation adds to it | What it must not do |
|---|---|---|
| Identity | The run identifier sits beside the actor and the delegation chain, so "who did this" and "as part of what" are one join (`F-b4-03`) | Carry any part of the actor's credentials |
| Errors | The record is a declared member of the problem object, so a failure names its run in a field rather than in prose (`F-b4-07`) | Introduce a new problem type; the registry in `docs/decomposition.md` 2.1.6 is closed |
| Provenance | Every attestation subject can be traced to the run that produced it | Replace the artifact digest as the attestation subject |
| Budget | A spend record joins to its run without reading a trace tree | Become a budget key; a ceiling is per unit, not per run |
| State | Records written under one run share the grouping key | Become the single-writer partition key by accident; that is decomposition open question 4 |

## 3. Per-adapter conformance subset (proposed)

Both implementations run the identical audit. What differs is what each can be asked, and the report
declares the difference rather than the audit branching on it.

| Assertion | In-process implementation | Pipeline implementation |
|---|---|---|
| `missing_run_id == 0` per kind | Read back through the hosted query surface | Read back from the columnar store |
| `missing_root_dispatch_id == 0` per kind | Same | Same |
| `signals_checked > 0` per kind | Same | Same |
| `run_id_groups == 1` | Same | Same |
| `distinct_trace_ids` | Reported | Reported |
| Non-conformant record disposition | Not observable; the SDK stamps or it does not | Counted in a dead-letter and published |
| Semantic questions about a model call | Available | Declared unsupported rather than faked |

An assertion an implementation cannot answer is declared unsupported in its report. It is never quietly
skipped, because a skipped assertion is indistinguishable from a passing one in the merged output.

## 4. What starts red, and why that is correct

`F-a6-06` records that typed errors are absent, and `F-b3-13` records that the standard for them has been
named and not adopted, so the problem-object count cannot reach `signals_checked > 0` today. `F-a7-02`
records that the platform currently injects a trace header the agent runtime does not honour, so no
correlation record is stamped anywhere. Both facts mean the definition of done starts failing. A first run
that passed would mean the audit collected nothing and asserted on an empty population, which is why
`signals_checked > 0` is an assertion and not a diagnostic.
