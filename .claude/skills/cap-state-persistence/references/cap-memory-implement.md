---
name: "cap-memory-implement"
description: "How to build the memory capability on this stack: a ranked store behind a binding record, a second store that answers by exact scope key, the migration from handing a run its predecessor's transcript to writing items it can recall, where a write and a recall are wired so the platform's guarantees ride on them, and the run that decides whether either store may be called done. Load it when standing up a memory store, when choosing what goes inside an adapter and what stays in the interface, when an item survives an expiry it should not have, when a recall works on one store and not the other, or when a memory change has to be shown to have taken effect rather than merely configured."
---

# cap-memory-implement (folded into `cap-state-persistence`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Build what cap-memory specifies: two stores selected by configuration, one conformance run that writes and recalls the same fixtures through both and diffs items, scope leaks, expiries and refusal types, and the wiring that makes a write and a recall recorded steps rather than unobserved calls. build-adapter-pair owns why there are two. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |

## Entities

| Entity |
|---|
| `E-capability-identity` |
| `E-capability-state-persistence` |
| `E-capability-errors` |
| `E-concern-provenance` |
| `E-standard-json-schema-2020-12` |

## Contract

### Shapes (JSON Schema 2020-12)

**MemoryBinding (): the record that selects a store, one per adapter, the only file that differs between them** (sourced; sources: `T-t10-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:memory:binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "binding_id",
    "role",
    "retrieval_model",
    "scope_dimensions",
    "expiry_enforcement",
    "declares"
  ],
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "role": {
      "enum": [
        "today",
        "second"
      ]
    },
    "retrieval_model": {
      "enum": [
        "ranked",
        "exact-key"
      ],
      "description": "the axis the pair differs on"
    },
    "scope_dimensions": {
      "type": "array",
      "items": {
        "enum": [
          "principal",
          "agent",
          "run",
          "org"
        ]
      },
      "minItems": 1
    },
    "expiry_enforcement": {
      "type": "array",
      "items": {
        "enum": [
          "on-read",
          "swept"
        ]
      },
      "contains": {
        "const": "on-read"
      }
    },
    "declares": {
      "type": "object",
      "required": [
        "reached",
        "trust_anchor"
      ],
      "properties": {
        "reached": {
          "type": "string",
          "description": "what the adapter reported reaching at start-up, not what this file asked for"
        },
        "trust_anchor": {
          "type": "string"
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| cap-memory owns the contract - scope on every write, a staleness policy on every write, provenance on every item, ranking absent from the signature. What this skill adds is where those are enforced: at the adapter boundary, so a store that cannot express a scope filter is rejected at start-up rather than quietly returning more than it should. | sourced | `X-cap-memory-002` "Every search must include at least one of these dimensions in filters" |
| Both stores are selected by a binding record and nothing else. build-adapter-pair states the swap test (F-meta-04): if an implementation cannot be swapped without touching the core, the boundary is drawn wrong. Here that is checkable - the two bindings are the only files that differ between a conformance run over the ranked store and one over the key store. | sourced | `F-meta-04` "the boundary is drawn wrong" |
| agentic-stack states design rule 7 as a test (F-b4-01): the platform applies each; a caller cannot decline them. What this skill adds is the two places they attach - the write path and the recall path - so an item carries the correlation attribute, the policy decision and the provenance of the run that produced it without a caller passing any of them. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them" |
| Proposed: expiry is enforced on read in every adapter, and a sweeper is an optimisation on top. An expired item that is still on disk must not be recallable between sweeps, which is why expiry_enforcement in the binding record must contain on-read. Research query: does X-cap-memory-004 or X-cap-memory-005, read in full rather than as a search snippet, say enforcement happens on read specifically (as opposed to only naming TTL/expiry as a policy), which would source the read-versus-sweep distinction rather than leave it proposed? | proposed | `X-cap-memory-005` "Systems must actively update or expire memories rather than treat them as immutable logs" |
| Proposed pointer, see cap-memory's invariant that cross-principal isolation holds by construction, never by a filter someone remembered to add: the build consequence is that the scope predicate must be part of the query the store executes, never a filter applied to results afterwards, because post-filtering satisfies the same assertion on a small fixture and fails in production, where a limit is applied before the filter and the ranked store's timings then leak how much it declined to show. | proposed | `X-cap-memory-002` "keeps cross-user contamination out of results by construction" |
| build-evidence-record owns the labelling rule (F-part-c-08). The consequence here is that 'both stores agree' is claimed until the conformance run has been executed and its output recorded; nothing in this skill has been run in this tree, so every status it carries is claimed. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put every store behind the binding record and keep embedding clients, index parameters, file paths and query strings inside the adapter directory. Core and seam code names remember, recall, supersede and forget and nothing else. | Every external dependency sits behind a capability interface, and here the leak is specific: a scope key format or an index name in core code is what makes the second store impossible to add later without editing the thing that was supposed to be independent of it. | sourced | `F-b1-02` "Every external dependency sits behind a capability interface" |
| 2 | Build today's adapter against a hosted store that embeds queries and stored items: map remember, recall, supersede and forget onto its write, search, update and delete calls, map cap-memory's four scope dimensions onto its filter tags, and refuse a write with no staleness policy at the adapter boundary rather than defaulting one. | The store's own model is to place the top-ranked memories into the model context, so the adapter's whole job is to constrain that: a scope filter on every search, an expiry comparison on every result, and a refusal where the contract requires a field the store treats as optional. | sourced | `X-cap-memory-001`, `X-cap-memory-002` "place the top-ranked memories into the model context" |
| 3 | Build the second adapter against a file-backed store - one document per scope, or a single-file relational database - where recall is an exact lookup on the scope key, the need string is used only to select among items at that key, and expiry is a timestamp comparison performed on read. | cap-memory states the axis the pair must differ on: approximate ranking over an index versus exact lookup on a key. Building the second one is also how the ranking-shaped assumptions in the first get found, because anything that cannot be answered without a ranker fails here outright instead of degrading. | sourced | `X-cap-memory-005`, `F-b1-04` "raw episodic data should always carry one" |
| 4 | Migrate in this order: keep the current hand-off of a predecessor run's transcript in place and write memory items alongside it; then read from memory with the transcript still passed and diff what a run would have done; then stop passing the transcript and keep the diff running for a period; only then delete the hand-off path. | Proposed migration. There is no memory store to migrate from - PASS.md's inventory of what is defined but not running is stated because an inventory that omits this is not an inventory, and memory is in none of its rows - so the thing being replaced is the habit of passing a whole transcript, and the diff is the only evidence that items carry what the transcript did. Research query: does a dispatch or ledger record in this repository already show the diff-then-cutover order for a similar hand-off removal, which would fix this order rather than leave it a proposal? | proposed | `F-a6-01`, `X-cap-memory-003` "Stated because an inventory that omits this is not an inventory." |
| 5 | Wire the cross-cutting concerns onto the write path and the recall path: set the correlation attribute explicitly at dispatch and copy it into the item's provenance, consult policy before an item crosses a scope wider than the writer's, charge the recall to the run's budget, and emit one telemetry span per operation naming the binding but not the store's address. | agentic-stack states design rule 7 (F-b4-01, F-b1-08): the platform applies each; a caller cannot decline them. Attaching them at these two points is what makes an item's origin recoverable later, and it is why an adapter never receives a correlation id as an argument it could omit. | sourced | `F-b4-01`, `F-b1-08` "The platform applies each; a caller cannot decline them" |
| 6 | Have each adapter report at start-up what it actually reached - the endpoint or the file it opened, and the trust anchor it verified against - and compare that against the binding record's declares.reached, failing start-up on a mismatch. | PASS.md records that configuration written in the documented place was silently discarded on this stack, so a binding file that says one store proves nothing about which store answered. The comparison is what turns a configured swap into an observed one. | sourced | `F-a7-04` "Configuration written in the documented place was silently discarded" |
| 7 | Write one conformance run parameterised over the binding records: write the same fixture items through every configured store, recall them at the same scopes from a later process, and assert the per-store counters and zero divergence on which item ids are recallable. | cap-memory's criterion is defined over the pair, not over one store, and build-adapter-pair states the rule it comes from. Parameterising the run is what stops the second adapter from getting a smaller test than the first, which is the usual way a pair turns out to be one store and a stub. | sourced | `F-b1-04` "Every interface ships with at least two adapters" |
| 8 | Record each conformance run as an evidence record naming the command, the fixture set, the code version and tree hash under test, and whether the tree was dirty, and leave the pair labelled claimed until a run exists. | build-evidence-record owns the record's fields and the labelling; what this skill adds is which run gets recorded - the cross-store one, not a unit test of either store, because a passing unit test of the ranked store says nothing about whether the interface is swappable. | sourced | `F-a5-04` "and whether the tree was dirty" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Verify the swap by what answered, not by what was configured: build-evidence-record carries the finding that values written to YAML validated, reviewed correctly, and had no runtime effect (F-a7-04), so a binding read from a file is evidence of an intention and not of a store. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Proposed: the memory conformance report records declares.reached from each adapter's own start-up line, so a run against two bindings that both reached the same store is caught rather than counted as a pair. Research query: unresearched; no prior-art search has been run for how conformance harnesses establish that two bindings reached distinct backing stores rather than the same one under two names. | proposed | `F-a7-04` |
| Proposed: run the expiry fixture with the sweeper disabled. A store that only passes expiry checks while a background job is running has not enforced expiry on read, and the binding record's expiry_enforcement claim is then false in the only case that matters. Research query: does a definition-of-done record for another expiry-bearing capability in this repository already run its breakage with the background sweep disabled, which would source this test discipline rather than leave it a proposed practice? | proposed | `X-cap-memory-005` "A time-to-live (TTL) is the cheapest forgetting mechanism" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-embedding-ranked-memory-store` | today | Proposed adapter and a proposed entity id, carried forward from cap-memory because PASS.md has no memory row and kb/entities.jsonl therefore has no adapter entity for this capability. Built here as: a client for a hosted store that embeds queries and stored memories, a scope filter compiled into every search, an expiry comparison applied to every candidate before it is returned, and a write path that refuses an item with no staleness policy. | Proposed: cannot serve a recall while the embedding endpoint is unreachable, cannot return an item by key without ranking it against the query, and cannot be inspected by a person reading a file - which is why the adapter also logs the item ids it returned and the scope it applied. | Change the binding record only. The conformance run in the definition of done writes and recalls the same fixtures through both bindings and requires identical recallable item ids, identical refusal types and zero cross-scope hits. | claimed | `X-cap-memory-001`, `X-cap-memory-002` "embed the query, find the closest stored embeddings" |
| `E-swap-candidate-scope-keyed-file-store` | second | Proposed adapter and a proposed entity id: a file-backed store, one document per scope key or a single-file relational database, where recall is an exact lookup, expiry is a timestamp comparison on read, and supersession appends a replacement and marks the previous item superseded_by. It differs in execution model, not in product class: no network call, no index, no ranker, and the whole store can be read by a person. | Proposed: cannot answer a need expressed only in words, cannot serve concurrent writers without a lock, and cannot grow past one host. Those limits are the point - an operation that cannot be implemented here is an operation cap-memory drew around the ranked store, which is exactly what the pair exists to detect. | Run the same conformance command with the second binding record and diff the two reports; assert adapters_run >= 2, result_divergence == 0, and that each adapter's start-up line reported reaching a different store. | claimed | `X-cap-memory-002`, `F-b1-04` "which are tagging dimensions, not nested layers" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/memory/test.sh && python3 harness/memory/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at ba83b69: exit 0; last lines: adapters_run=2 stores_reached_distinct=2 result_divergence=0 \| conformance PASSED: 20/20 cases, 2 binding(s) |
| Deliberate breakage | Remove the on-read expiry filter from recall() in harness/memory/interface.py (the line calling _expired), run the criterion (the conformance run reports expired_served above zero on both adapters and exits 1), then git checkout harness/memory/interface.py. |
| Expected failure | Measured by tools/measure.py at ba83b69: exit 1; last lines:   ok   cross_scope_hits=0 still holds: the scope check and the expiry check fail independently \| passed 13, failed 10 |
| Status | measured |
| Evidence | `F-part-c-04`, `X-cap-memory-005` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-memory`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does an item written at organisation scope need the integrity mechanism the task store already has - a chain where each record names the previous head - or is provenance on each item enough? | Whether anything downstream acts on a memory item in a way that must be defensible after the fact. If a recalled item can change a spend or a deployment, an item that can be edited between runs without detection is a hole; if memory only ever informs a draft, provenance is enough. cap-state-persistence owns the chained store and would be the place to put it. | Proposed: provenance only, and supersession rather than editing, until a recalled item is shown to drive an irreversible action. The chain costs a single-writer constraint that the two stores in this pair do not otherwise need. | `F-a5-03` "each run's closing digest is the next run's opening digest" |
| Which store answers an organisation-scoped recall when the two adapters disagree about who may read it - the file store has no tenancy model of its own and the ranked store does? | A conformance case that writes one item at org scope and recalls it as two principals in the same organisation and one outside it, run against both bindings. If the file store can only satisfy it by adding a check the ranked store does not need, the tenancy check belongs above both adapters rather than inside either. | Proposed: the scope check is applied above the adapters, in the capability cap-memory defines, and each adapter is required only to execute the selector it is handed. That keeps the file store implementable and makes a tenancy bug one bug rather than two. | `X-end-to-end-002` "each memory write is tagged with one or more identity scopes" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation cap-memory author 2026-09-03 |
