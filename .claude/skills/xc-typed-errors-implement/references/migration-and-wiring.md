# Typed errors: conversion checklist, wiring table, per-implementation conformance subset

Long material for `xc-typed-errors-implement`. The skill body is enough to plan and judge the
build; open this when converting a specific boundary, when deciding what each implementation is
allowed to assert, or when wiring a cross-cutting guarantee onto a failure body.

Statements are marked **proposed** unless a knowledge-base id is given in brackets.

## 1. Conversion checklist, in order (proposed)

Step 2 of the skill body says the migration ships in three parts. This is the order inside part
one. Each row is done when its consumers branch on `type` and its producer returns the object.

| # | Boundary | Convert consumer first | Done when |
|---|---|---|---|
| 1 | Dispatch seam result shape | n/a - this is the type narrowing | The result shape declares the typed object as its only failure return |
| 2 | Envelope validation | the entry adapters | A malformed envelope returns `document-invalid` under all four entry kinds |
| 3 | Policy refusal | the caller's refusal branch | The refusal carries `rule_id` and one type under all three ways in |
| 4 | Budget termination | the retry loop above it | Termination returns `budget-exhausted` with `retryable: false` |
| 5 | Identity verification | the delegation checker | A chain that does not verify returns `identity-untrusted` |
| 6 | Idempotency claim | the replay path | A key reused with a different body returns `idempotency-conflict` |
| 7 | Every capability adapter | the adapter's own error handling | The adapter's untyped counter reads zero over a fuzz run |

Rows 3, 4 and 2 are the three the fold-in requires to agree across entries, which is why they
precede everything except the type narrowing.

## 2. Where the cross-cutting guarantees land on a failure body (proposed)

Step 5 of the skill body says these are declared extension members on the problem shape, not
fields a logging helper adds. One row per guarantee.

| Guarantee | Member on the problem body | Why it has to be here |
|---|---|---|
| Correlation | the run and root dispatch identifiers | The failure body is often the only artifact that crosses the boundary and outlives the process |
| Identity | the actor subject and its delegation chain | "Every action names an actor" including delegated agent actors [F-b4-03]; a refusal is an action |
| Budget | the spend at the moment a unit was terminated | Without it a caller learns that it stopped, not how close it was |
| Policy | `rule_id` on a `policy-denied` problem | The registry row already declares it; a refusal that cannot name its rule cannot be appealed or replayed |
| Idempotency | the key the attempt was made under | A conflict that does not name the key sends the caller looking for it in a log |
| Provenance | the digest of any partial output already recorded | A partial is durable before the dispatch is terminal, so a failure must not orphan it |

None of these adds a problem type. All of them are extension members on the object `cap-errors`
owns, which is what makes them parseable rather than readable
["RFC 9457 explicitly allows Extension Members." - X-xc-typed-errors-002].

## 3. Per-implementation conformance subset (proposed)

Both implementations run the same assertions against `TypedErrorsConformanceReport`. They differ
in what they can populate, so the subset each is responsible for is stated rather than inferred.

| Assertion | Tree scan (`checks_at: build_time`) | Response interceptor (`checks_at: run_time`) |
|---|---|---|
| `string_match_sites == 0` | authoritative over the source tree | authoritative over decisions actually taken |
| `untyped == 0` | cannot observe; reports null | authoritative |
| `unregistered_types == 0` | reports types found in source | authoritative over emitted bodies |
| `failures_checked` | counts failure sites found | counts failure bodies seen |
| `observed_population` | files scanned | responses intercepted |
| `shared_refusal_type` | cannot observe | authoritative |

A run where an implementation reports a value it is not authoritative for is the finding. So is a
run where both report zero and neither reports a population: the platform has already measured
once that a gate can be structurally green and mean nothing, and that
"Those establish well-formedness, not correctness" [F-a7-03].

## 4. Migration blind spots (proposed)

1. **A boundary that writes its response directly.** The interceptor is registered and bypassed.
   Only `observed_population` per boundary reveals it; a global count hides it.
2. **A converted producer under an unconverted consumer.** The words moved, the substring match
   stopped firing, and behaviour changed with no error anywhere. This is why step 6 converts
   consumers first.
3. **A dormant heuristic.** The tree scan catches it; the interceptor never will until the day it
   fires. This is the axis the pair exists for.
4. **A dirty tree.** An audit run from a modified working tree is labelled claimed, never measured
   [F-a5-04].
