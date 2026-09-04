# core-planner-implement: wiring, bindings, backfill

Long material for `core-planner-implement`. Open it when writing the loader, the backfill, the
binding records or the cross-cutting wiring, or when reviewing someone who did. The skill body is
enough to review a design and to run the definition of done without this file.

Everything here is **proposed** unless it cites a knowledge-base id. `core-planner` owns the
contract these notes implement; nothing below may relax it.

## 1. Module layout (proposed)

| Module | May import | Must not import | Why |
|---|---|---|---|
| `plan/price.py` | the plan and cost-input shapes | anything with a socket, a clock, a path or a store handle | The tracer count in the definition of done is a property of this import graph, not of the fixture. |
| `plan/loader.py` | the state-seam client, `plan/price.py` | the model-access client | One module owns head resolution and the two pinned reads; a reviewer can point at it. |
| `plan/mappers/*.py` | `plan/loader.py` | the priced fields | A mapper carries the requester onto the plan and touches nothing that has a number in it. |
| `plan/wiring.py` | correlation, policy, provenance, budget | - | Design rule 7's placement (F-b1-08): applied here, never requested by a caller. |

The import lint in step 7 is one rule per row of the "must not import" column, run at build time.

## 2. The two bindings (proposed)

```json
{
  "role": "today",
  "record_kinds": ["dispatch-result", "cost-observation"],
  "read_mode": "scan the appended records from the beginning and fold them at the pinned head, in the reader's own process",
  "serves_pricing": false,
  "differs_in_execution_model": [
    "read_mode: scan-and-fold in-process",
    "locus_of_determinism: file order plus a linear chain",
    "head_form: a record offset local to one file"
  ]
}
```

```json
{
  "role": "second",
  "record_kinds": ["dispatch-result", "cost-observation"],
  "read_mode": "fetch one immutable snapshot addressed by digest and use it whole; no scan, no fold, no ordering",
  "serves_pricing": false,
  "differs_in_execution_model": [
    "read_mode: fetch-one-snapshot by content address",
    "locus_of_determinism: the content address is the head",
    "head_form: a digest that is meaningful outside any one process"
  ]
}
```

Two bindings identical on every axis are one store read twice; `build-adapter-pair` owns that test.
The axes above are the ones the pair check reads, and the conformance run requires identical plan
bytes and identical connect counts across both.

## 3. Backfill and migration (proposed)

Today nothing is priced before it runs, so the migration's hard part is producing the first cost
table rather than swapping a store.

1. **Backfill.** Walk the recorded run history; for every completed step emit a `cost-observation`
   record keyed by `operator/model_class` with the micros actually spent. Steps whose operator
   cannot be recovered are skipped and counted; a backfill that silently guesses an operator
   produces a quantile nobody can defend.
2. **Compute.** Fold the observations into `p50_micros`, `p95_micros` and `observations` per
   selector, at a pinned head. A selector under the configured minimum observation count keeps its
   rate-card figure and records `observations: 0`.
3. **Shadow.** Plan every entry alongside the live path and record the plan beside the run, gating
   nothing. This is the only stage that yields quantiles without paying twice to learn them.
4. **Compare.** Per run, declared worst case against actual spend. Cut over only when the worst case
   covered the actual on every run in a full window; a single uncovered run means the ceiling would
   have been set below what the work needed.
5. **Cut over.** Plan before dispatch, with the refusal path live. Keep shadow recording for one
   further window so a regression shows as a coverage number rather than as a support ticket.

## 4. Where each cross-cutting concern attaches (proposed)

| Concern | Attach point | What it writes |
|---|---|---|
| Correlation | plan construction | The explicit resource attribute (F-a7-02), carried from the envelope; never inherited from the caller's ambient context. |
| Policy | plan admission, before the plan is returned | A deterministic allow or deny with the rule id, taken before anything is dispatched. |
| Provenance | after pricing | An attestation over `plan_digest`, `document_digest` and `cost_inputs_digest` together, so a later reader can show which numbers priced which work. |
| Budget | plan admission | Compare `floor_micros` against the envelope's ceiling. The planner compares; it never edits the ceiling. `xc-budget` owns the guarantee. |
| Identity | plan construction | The requester and the delegation chain from the envelope, recorded on the plan and never branched on. |
| Idempotency | before pricing a step | The prior-result read at the pinned head; a step with a result is planned as a replay at zero. |

## 5. Reading the conformance report

`plan_digest_mismatches` is the field that earns the pair. A non-zero value means the two bindings
disagreed about what the store contained at one head - almost always a fold that depends on arrival
order, or a snapshot built from a different record set. `connects_inet` above zero under exactly one
binding means the binding itself is calling out, not the planner. `steps_priced` at zero with
everything else green is the structurally-green case: the run proved nothing, and is reported as
inconclusive rather than passed.
