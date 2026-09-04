# compose-operators: the caller's view

Proposed. The body of `compose-operators` is enough to write, refuse and reason about a composition; open this file for the minimal inputs and outputs, one worked composition from each of TARGET T1's three ways in, and the worked rejection in full.

The caller doctrine that is identical for every capability - the four entries of TARGET T6.2 arriving through one envelope, one result or one problem object back, composing upward instead of adding arguments, and cross-cutting guarantees that are applied rather than requested - is stated once in `cap-consumption` and is not repeated here. What is specific to this layer is that **the composition is data the caller hands in, and the same data is what a second engine reads**.

Ids resolve with `python3 tools/kb.py show <id>`.

## Minimal inputs and outputs

| Call | You supply | You read back | Origin |
|---|---|---|---|
| `compose` | an ordered list of steps, each naming one operator from the closed set of six; children go in that operator's child slot | one workflow document rooted at a single step, or a typed problem naming the step whose operator is not in the set | proposed |
| `price` (via `core-planner`) | the workflow document | a floor and a worst case per step, one total, and the reconciliation showing each parent equals the sum of its children | proposed |
| `resolved_default` | a step id and one field name | the value in force and which single layer it came from: `caller`, `capability` or `platform` | proposed |
| any run | the workflow document, unchanged, plus the engine you want it run on | the same step order and the same terminal outcome from either engine; the document is the invariant, the engine is not | proposed |

Nothing above asks the caller for a retry policy, a checkpoint table, a correlation identifier to thread through, or an engine name. Those are carried (`F-b4-01`).

## Way in 1 - a human composes and runs (`declared_by` a `user:` subject)

A person types a fault report; the composition they run is the one already on disk. The entry envelope carries who is acting, and the workflow document carries only control flow.

```json
{
  "kind": "human",
  "actor": {
    "subject": "user:corey",
    "delegation_chain": [{"actor": "user:corey", "obtained_via": "direct"}]
  },
  "intent": {
    "workflow_ref": "workflows/triage-and-fix.json",
    "summary": "Checkout returns 500 on coupon apply since this morning; find it and fix it."
  },
  "budget": {"ceiling_micros": 1500000, "currency": "USD", "on_exceed": "terminate_unit"}
}
```

The composition it names uses every operator once, in this nesting:

```text
sequence root
├─ agent    triage
├─ parallel decompose            branches: repro | logs | dedup      tolerate {failed: 0}
├─ loop     fix-loop             max_iterations 3 · exit_when fix-judge = pass
│   └─ sequence attempt
│        ├─ agent  fix
│        └─ judge  fix-judge     criterion_ref criterion://fix-acceptable/v1
├─ agent    brief
├─ approval ship-approval        view: patch-summary · approve | edit | reject
└─ agent    regression
```

Three things to read off it. The loop names all three of its terminations (the verdict, `max_iterations`, and the ceiling it inherits from the envelope). The judge carries a handle, never the criterion. And no line names an engine, a model or a vendor, which is why the same six lines run under either adapter.

## Way in 2 - an agent submits the same composition (an `agent:` subject)

An outside agent submits the identical workflow reference. Only the envelope differs: a longer delegation chain, a parent correlation id, and a non-zero depth.

```json
{
  "kind": "external",
  "actor": {
    "subject": "agent:partner-sre-bot",
    "delegation_chain": [
      {"actor": "agent:partner-sre-bot", "obtained_via": "workload_attestation"},
      {"actor": "service:intake", "obtained_via": "rfc8693_token_exchange"},
      {"actor": "user:corey", "obtained_via": "direct"}
    ]
  },
  "intent": {"workflow_ref": "workflows/triage-and-fix.json"},
  "correlation": {"parent_correlation_id": "corr-partner-77c1", "depth": 1}
}
```

`depth: 1` is what the depth bound is checked against at resolve time (`REF-5-2-13`). A submitted composition that would nest past the bound is refused here, before its first step is priced, and the refusal names the step.

## Way in 3 - an event and a schedule steer the same composition (`service:` and `schedule:` subjects)

```json
{
  "kind": "event",
  "actor": {"subject": "service:alerting",
            "delegation_chain": [{"actor": "service:alerting", "obtained_via": "workload_attestation"}]},
  "intent": {"workflow_ref": "workflows/triage-and-fix.json"}
}
```

```json
{
  "kind": "schedule",
  "actor": {"subject": "schedule:nightly-fault-sweep",
            "delegation_chain": [{"actor": "schedule:nightly-fault-sweep", "obtained_via": "workload_attestation"},
                                 {"actor": "user:corey", "obtained_via": "rfc8693_token_exchange"}]},
  "intent": {"workflow_ref": "workflows/triage-and-fix.json"}
}
```

The composition is byte-identical across all four. What differs is the envelope, and no operator may read the entry kind to choose a branch - if it could, one vocabulary would have quietly become four.

One rule bites here specifically: an operator inside a run may **steer** that run and may never **start** a new one (`REF-3-4-15`, stated by `cap-consumption`). A judge verdict can send a loop round again; it cannot submit a fresh entry. Every unit of work still traces back to a person, a clock or an outside event.

## Worked rejection - an operator outside the closed set

The caller adds a `branch` step, expecting the platform to route on a model's answer:

```json
{"op": "branch", "id": "pick", "cases": []}
```

The composition is refused before it is priced, graphed or dispatched. What comes back is a problem object, not prose:

```json
{
  "type": "urn:agentic:problem:document-invalid",
  "title": "Document invalid",
  "status": 422,
  "detail": "1 validation error against urn:agentic:example:workflow:0.1",
  "errors": [
    {"pointer": "$.root", "message": "matches none of the allowed step shapes"}
  ],
  "retryable": false,
  "correlation_id": "corr-human-0001"
}
```

`type` is the member a caller branches on; `retryable` is a field, never an inference from the status code. The suffix is the registered `document-invalid` row of the closed registry in `docs/decomposition.md` section 2.1.6 - a refused composition is a refused document, and this layer mints no problem type of its own.

Measured on 2026-09-03: running the unmodified document through the example's validator returned `valid`; with the `branch` step appended it returned exactly one error, `$.root: matches none of the allowed step shapes`. The closed set is closed by something that can fail.

## What a caller does instead of a seventh operator

| The caller wanted | What they write | What changed in the platform |
|---|---|---|
| a branch on a result | a `judge` step and a `loop` whose `exit_when` reads its verdict | nothing |
| a new kind of analysis | an `agent` step naming a new profile | one file in the agent registry |
| a different acceptance rule | the same `judge` step with a different `criterion_ref` | one criterion resource |
| a human decision rendered differently | the same `approval` step with a different `view` | one view definition |

That table is the closed-schema, open-vocabulary rule (`REF-1-02`) from the caller's side: the document stays the size it was, and the platform grew.
