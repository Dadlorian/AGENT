---
name: cap-work-intake-implement
description: How to build the Work intake capability on this stack: the repository-event producer that already runs as a deployment role, an agent-message producer as the second implementation behind the same interface, the migration between them with the canonical envelope held still, the one place cross-cutting fields are stamped so no producer can enter without them, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that turns a producer message into a job, when adding a submission path beside the one that runs today, when an actor or a correlation identifier is missing from something that already entered, when deciding where the envelope is built and validated, or when an equivalence run reports two digests for one job.
---

# cap-work-intake-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract cap-work-intake states into something that runs here: one envelope schema published first, one builder that every producer mapper goes through, two producer adapters whose execution models differ, and refusals that are typed from the first commit rather than after the first integration argument. | sourced | `F-b3-08`, `E-capability-work-intake`, `E-swap-candidate-any-conformant-producer` "any conformant producer" |

## Entities

| Entity |
|---|
| `E-capability-work-intake` |
| `E-standard-cloudevents` |
| `E-standard-a2a-messaging` |
| `E-adapter-http` |
| `E-adapter-git-event` |
| `E-adapter-cli` |
| `E-adapter-schedule` |
| `E-swap-candidate-any-conformant-producer` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| register_mapper (proposed; how a producer joins without the envelope changing) | a producer format name, the mapping from its native fields onto the envelope's fields, and the rule by which its idempotency key is derived | the mapper is callable by name and appears in the equivalence report; a producer with no registered mapper is refused with a typed problem rather than admitted on a best guess | proposed | `F-b3-08` |
| build_envelope (proposed; the single writer of every cross-cutting field) | the mapped fields from one producer plus the platform context at entry | one envelope carrying actor and delegation chain, correlation, budget ceiling, derived idempotency key and opaque payload, validated before it is returned; no adapter may construct an envelope by any other route | proposed | `F-b4-01` |
| select_producer_adapter (proposed) | the deployment's intake configuration | the producer adapter this run accepts through, chosen by configuration alone so the equivalence corpus can be run twice with no code edit between runs | proposed | `F-b1-04` |

### Shapes (JSON Schema 2020-12)

**IntakeAdapterConfig (proposed; the only thing that differs between the two equivalence runs)** (proposed; sources: `F-b1-04`, `F-b3-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:adapter-config:0.1",
  "title": "IntakeAdapterConfig",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "selected_by",
    "registered_mappers",
    "refuse_unmapped"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "request-pushed-event",
        "agent-message"
      ]
    },
    "selected_by": {
      "const": "configuration",
      "description": "A const, so no code path can choose the producer adapter at runtime."
    },
    "registered_mappers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Producer format names this deployment will map. Declared, not discovered."
    },
    "refuse_unmapped": {
      "const": true,
      "description": "A const: an unregistered producer format is refused, never admitted on a guess."
    },
    "ack_carries_result": {
      "const": false,
      "description": "A const. The second adapter's producer may be gone before the job finishes, so no adapter may promise a result in the acknowledgement."
    }
  }
}
```

**IntakeEquivalenceReport (proposed; what the definition of done below asserts against)** (proposed; sources: `F-b1-04`, `F-a6-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:intake:equivalence:0.1",
  "title": "IntakeEquivalenceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "selected_by",
    "producers_run",
    "distinct_job_digests",
    "distinct_entry_ids",
    "invalid"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "request-pushed-event",
        "agent-message"
      ]
    },
    "selected_by": {
      "const": "configuration"
    },
    "producers_run": {
      "type": "integer",
      "minimum": 1,
      "description": "How many producer renderings of the one logical job were submitted in this run."
    },
    "distinct_job_digests": {
      "type": "integer",
      "minimum": 0,
      "description": "Must be 1. Two means a producer left a fingerprint on the job."
    },
    "distinct_entry_ids": {
      "type": "integer",
      "minimum": 0,
      "description": "Must equal producers_run. Fewer means submissions were collapsed."
    },
    "invalid": {
      "type": "integer",
      "minimum": 0,
      "description": "Envelopes that failed the published schema. Must be 0."
    },
    "untyped_refusals": {
      "type": "integer",
      "minimum": 0,
      "description": "Refusals returned as anything other than problem details. Must be 0; today's starting value is every refusal."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1,
      "description": "Merged across runs. Must reach 2."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The actor field this capability must stamp on every entry does not exist yet: the recorded gap is that there is no identity field anywhere in the system. So stamping actor and delegation chain at intake is new construction, and every claim about it starts unmeasured. | sourced | `F-a6-05` "No identity field anywhere in the system" |
| The refusal shape intake depends on is also recorded as absent today, so the typed registry has to exist before intake can refuse properly; until it does, a producer's mistake reaches it as a transport status and a log line. | sourced | `F-a6-06`, `F-b3-13` "Typed errors \| Absent" |
| This is not a green field: a repository-event producer already runs as one of the deployment roles alongside the approval surface, so the first adapter is an existing path to be brought behind the envelope rather than something to write from nothing. | sourced | `F-a5-01`, `E-adapter-git-event` "`git_events`, `approve`, `cells`" |
| Proposed: the published envelope schema is the migration boundary and does not move. cap-work-intake fixes the canonical envelope and its fields (F-b3-08); every step below changes only which producer builds it, so any step can be reverted without touching a producer that already works. Research query: is there a fetched read of the A2A/CloudEvents standard (F-b3-08) that fixes the envelope schema itself as the migration boundary, or is treating cap-work-intake's canonical envelope as the fixed boundary this facet's own reading of its contract? | proposed | `F-b3-08` |
| Proposed pointer, see build-adapter-pair's design rule 3 (F-b1-04) that swappability is a tested property: the build consequence is that which producer adapter accepts is a configuration value and nothing else, expressed as `selected_by: configuration` in IntakeAdapterConfig above. If choosing the second producer needs a code edit, the two equivalence runs are not the same test and the pair proves nothing. | proposed | `F-b1-04` |
| Proposed: there is exactly one envelope builder, and every mapper goes through it. Two builders become two answers to what an entry carries, and the second answer is always the one written in a hurry for the producer that had a deadline. Research query: does F-b4-01's cross-cutting-guarantees finding extend to fixing 'exactly one envelope builder' as a structural requirement, or is one-builder-no-exceptions this facet's own reading of what avoiding a second, hurried answer requires? | proposed | `F-b4-01` |
| build-evidence-record owns what an evidence record contains, and F-part-c-08 fixes the claimed-versus-measured distinction. The consequence here: every statement this facet makes about an adapter's behaviour is claimed until an equivalence run produces it - the report shape above is the artefact that upgrades a claim, and a report with `producers_run: 1` upgrades nothing about normalisation. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| cap-work-intake already fixes the envelope as the whole surface, and F-part-c-09 fixes that products belong in the adapter column only. The build consequence: neither adapter's internals reach the envelope. The request path's headers and status codes, the repository hook's delivery metadata, the agent protocol's own task identifiers and conversation grouping stay inside the mapper. | sourced | `F-part-c-09` "Products belong in the adapter column only." |
| Proposed: no configuration flag lets a producer skip the builder or receive a result in its acknowledgement, which is why both are consts in IntakeAdapterConfig. A fast path is exactly how a favoured producer becomes a second, unwired way in. Research query: does F-b4-01 or xc-enforcement-chain fix, with a kb citation, that no configuration flag may let a producer bypass the builder, which would source this row rather than leave it this facet's own restatement of the fast-path danger already used elsewhere in this layer? | proposed | `F-b4-01` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Publish the envelope schema and the equivalence fixture corpus before writing any mapper, and keep the corpus in version control beside the schema. | Proposed sequencing. The corpus is simultaneously the normalisation test and the swap test, so writing it first means no mapper can be built to its own idea of equivalent; a corpus derived from the producer that already runs would encode that producer's fingerprints as expectations. Research query: does a fetched read of A2A messaging or CloudEvents (F-b3-08's cited standards) fix publish-schema-and-corpus-before-any-mapper as a required discipline, or is that build ordering this facet's own choice? | proposed | `F-b3-08` |
| 2 | Bring the producer that already runs behind the envelope first: keep its trigger and its transport, and change only that it now calls the shared builder and gets an acknowledgement back instead of doing its own thing. | A repository-event producer is already a deployment role, so this step is reversible and observable on real traffic. Rewriting the transport at the same time as introducing the envelope would leave no way to tell which change caused a regression. | sourced | `F-a5-01`, `E-adapter-git-event` "`git_events`, `approve`, `cells`" |
| 3 | Build the agent-message producer as the second implementation behind the same builder, and give it no privileges the first does not have: no synchronous result, no field of its own, no separate validator. | Proposed. build-adapter-pair states design rule 3 and cap-work-intake states the axis this pair differs on (F-b3-08, F-b1-04): whether the producer is still there when the job finishes. Granting the agent producer a shortcut would collapse the axis and leave two adapters of the same shape. Research query: does F-b3-08's 'any conformant producer' row, read from a fetched A2A/CloudEvents source, fix that a second producer gets no field or validator of its own, or is that no-extra-privilege rule this facet's own reading of build-adapter-pair? | proposed | `F-b1-04`, `F-b3-08` |
| 4 | Migrate in three revertible steps and keep both producers live at the end: envelope built and validated but the old path still authoritative, then the envelope authoritative for one producer, then both producers selectable by configuration. Delete neither. | Proposed migration. Each step is revertible because the schema does not change, and an interface with one surviving implementation drifts back into the shape of whatever runs, which is the failure the pair exists to prevent. Research query: does a migration record for another two-producer capability in this repository already show the same three-stage revertible order (built-not-authoritative, one-producer-authoritative, both-selectable), which would source this order rather than leave it a proposal? | proposed | `F-b1-04` |
| 5 | Stamp actor and delegation chain, correlation, budget ceiling and the derived idempotency key in the builder, at the single point where a producer message becomes an envelope, and refuse the entry if any of them cannot be filled. | cap-work-intake already states the rule that the platform applies each; a caller cannot decline them (F-b4-01). What this facet adds is our own placement consequence, proposed: a single builder no producer can route around. Stamping later means an entry exists, briefly, with no actor and no ceiling, and that window is where the audit trail loses its first record. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them." |
| 6 | Build the identity fields as new construction rather than as a mapping of something existing: attest the producer's workload identity, exchange it for the platform's own subject, and record both hops in the chain, oldest last. | There is no identity field anywhere in the system today, so nothing upstream can be trusted to supply one and there is no legacy shape to preserve. Every action names an actor, including delegated agent actors, and the agent-message producer is precisely the case that makes a one-hop chain wrong. | sourced | `F-a6-05`, `F-b4-03` "Every action names an actor, including delegated agent actors." |
| 7 | Return refusals as typed problems from the registry from the first commit, and count untyped refusals in the equivalence report rather than assuming there are none. | cap-errors owns the shape and the registry (F-b3-13) and the recorded gap here is that typed errors are absent, so the starting value of that counter is every refusal. Counting it makes the gap visible in a report instead of in a producer's inbox. | sourced | `F-a6-06`, `F-b3-13` "Typed errors \| Absent" |
| 8 | Apply build-adapter-pair: run one equivalence runner parameterised over the producer adapters, selected by configuration with no code edit between runs, and record `selected_by` and the producer that actually answered in the one report shape; proposed pointer, see that skill's references/conformance-run-shape.md. | The parameterised suite and the configuration-only swap are build-adapter-pair's step; the report shape it did not state was added there as references/conformance-run-shape.md rather than written out again in five capability skills (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-b1-04` "Every interface ships with at least two adapters" |
| 9 | Open references/intake-adapters.md when you need the per-producer mapping table, the failure modes each adapter can and cannot detect, or the step-by-step migration runbook. This skill body is enough to build either producer without it. | Proposed, progressive disclosure. The mapping table and the runbook are long material a reader wiring the builder does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: derive the idempotency key in the mapper, never in the builder, and write the derivation rule down per producer. The builder cannot know whether two producer messages are the same act; only the producer's own identifiers can say, and a rule that lives in code review rather than in a table is a rule that changes silently. Research query: does F-b4-08's replay-safety contract, read in full, fix that the idempotency key must be derived in the mapper rather than the builder, or is that placement this facet's own reading of who can tell two producer messages apart? | proposed | `F-b4-08` |
| Set correlation explicitly in the builder rather than reading it off the transport, because correlation rides on explicit attributes, not trace parentage - and intake is the earliest point at which a producer could have handed us a parentage that will not survive the next hop. | sourced | `F-b4-06` "Correlation rides on explicit attributes, not trace parentage" |
| Proposed: run the equivalence corpus in CI on every change to either mapper, not only at the swap. A normalisation regression has no symptom until two producers submit the same job, which may be months after the change that caused it, and the corpus is the only place it surfaces the same week it is written. Research query: does an evidence-store record already show a normalisation regression surfacing only months after the causing change for another equivalence-checked capability in this repository, which would source this specific failure mode rather than leave it a proposed practice? | proposed | `F-b1-04` |
| build-evidence-record owns the record's fields, and F-part-c-08 fixes the claimed-versus-measured distinction. What matters here: record each equivalence run as an evidence record naming the adapter, the code version and the corpus hash, and label the result claimed until that record exists - two producers make it easy to report a green run without saying which producer was green. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Proposed: when a producer asks for a new envelope field, write the mapper that avoids it first and only then discuss the field. Most such requests are the producer's own identifier, its retry counter or its own status, and all three already have somewhere to go. Research query: does F-b3-08's canonical-envelope row, read in full, already list producer identifier, retry counter and status as fields with somewhere to go, or is 'write the mapper that avoids the new field first' this facet's own review discipline? | proposed | `F-b3-08` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-http` | today | cap-work-intake records this row and the axis the pair differs on (F-b3-08); what this facet adds is the mapping. A formatted event pushed over a request, with the repository-event producer that already runs as a deployment role as its first mapper and the command line and schedule occurrence as further mappers of the same execution model. Each builds an event, hands it over in one hop, and gets an acknowledgement back inside that hop. | Cannot stamp an actor from anything that exists today, since no identity field exists anywhere in the system (F-a6-05), so its delegation chain is new construction and starts as a single attested hop. Cannot refuse in the typed shape either until the registry exists, which is why `untyped_refusals` is a counter in the report rather than an assumption. | Keep the published envelope schema and the corpus still; register the second producer's mapper and flip the configuration. Reverting is the same flip, and any producer the builder refuses is visible in the report before it reaches real traffic. | claimed | `F-b3-08`, `F-a5-01`, `F-a6-05`, `E-adapter-http`, `E-adapter-git-event` "`git_events`, `approve`, `cells`" |
| `E-swap-candidate-any-conformant-producer` | second | An autonomous agent submitting through the agent messaging protocol, mapped into the same envelope by a registered mapper: the message identifier becomes the idempotency key, the submitting agent's attested identity becomes the first hop of the delegation chain, and the agent's own correlation, when it sends one, becomes the parent correlation rather than the correlation itself. | Cannot be told anything synchronously beyond the acknowledgement, cannot be assumed present when the job ends, and cannot be assumed to have a human reading its refusals. cap-work-intake already records that axis (F-b3-08); what this facet adds is its consequence in code - `ack_carries_result` is a const false in IntakeAdapterConfig, so the first adapter cannot quietly acquire a synchronous result path that the second could never serve. | Set `adapter` in IntakeAdapterConfig and re-run the identical corpus with no code edit between runs; merge the two reports and require `adapters_run == 2`, `selected_by == "configuration"` in both, `distinct_job_digests == 1` in each, and `untyped_refusals == 0` in each. | claimed | `F-b3-08`, `F-b1-04`, `E-swap-candidate-any-conformant-producer` "any conformant producer" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/work-intake/test.sh && python3 harness/work-intake/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 372cdc1: exit 0; last lines:   producers_run=4 distinct_job_digests=1 distinct_entry_ids=4 invalid=0 untyped_refusals=0 records=4 work_started=0 marker=task-message-accepted product_hits=0 verdict=pass \| conformance PASSED: 30/30 cases, 2 binding(s) |
| Deliberate breakage | Append a product-name comment (`# breakage: litellm`) to the end of harness/work-intake/call.py, outside adapters/. Restored with `git checkout -- harness/work-intake/call.py`. |
| Expected failure | Measured by tools/measure.py at 372cdc1: exit 1; last lines:   ok   the breakage singles out one adapter and leaves the other green (0) \| passed 20, failed 8 |
| Status | measured |
| Evidence | `F-b3-08`, `F-b1-04`, `F-a6-06`, `F-a6-05` "any conformant producer" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-work-intake`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the builder mint the correlation run identifier, or accept one a producer supplies? | Across submissions from an agent producer, count how many arrive carrying a correlation of their own and how many of those correlations are still resolvable in this platform's telemetry an hour later; a correlation that resolves nowhere is a string, not a link. | Proposed: the builder mints the run identifier always, and a producer-supplied correlation becomes the parent correlation. That keeps every run identifier resolvable here while preserving the link back to the submitter, which is what the depth field is for. | `F-b4-06` "Correlation rides on explicit attributes, not trace parentage" |
| How is the agent-message producer's delegation chain attested before an identity capability exists? | Whether the submitting agent can present an attestable workload credential at all in this environment, and whether the exchange that turns it into a platform subject can be performed without the identity capability being finished; if neither is available, the second adapter can be built and its chain assertion cannot. | Build the mapper to record the hops it can attest and mark the chain incomplete rather than fabricating a hop, and record every result about identity as claimed. The recorded state is that there is no identity field anywhere in the system, so an intake that reports a full chain today is reporting something it did not obtain. | `F-a6-05`, `F-b4-03` "No identity field anywhere in the system" |
| Is the second producer retained once the request-pushed path carries all real traffic? | Whether any producer that cannot hold a submission open actually submits work here, and whether the equivalence corpus would still detect a fingerprint if only one adapter ever ran it. | Retain it as the configured second adapter and record its results as claimed until a run against a real agent producer exists. A pair whose second member has never accepted anything is a pair on paper, and saying so is cheaper than pretending otherwise. | `F-b1-04` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-work-intake 2831cb4f, 2026-09-03 |
