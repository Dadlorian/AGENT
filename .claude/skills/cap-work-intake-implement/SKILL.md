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
| Proposed: the published envelope schema is the migration boundary and does not move. cap-work-intake fixes the canonical envelope and its fields (F-b3-08); every step below changes only which producer builds it, so any step can be reverted without touching a producer that already works. | proposed | `F-b3-08` |
| Proposed: which producer adapter accepts is a configuration value and nothing else, expressed as `selected_by: configuration` in IntakeAdapterConfig above. If choosing the second producer needs a code edit, the two equivalence runs are not the same test and the pair proves nothing. | proposed | `F-b1-04` |
| Proposed: there is exactly one envelope builder, and every mapper goes through it. Two builders become two answers to what an entry carries, and the second answer is always the one written in a hurry for the producer that had a deadline. | proposed | `F-b4-01` |
| Proposed: every statement this facet makes about an adapter's behaviour is claimed until an equivalence run produces it. build-evidence-record owns what an evidence record contains; the consequence here is that the report shape above is the artefact that upgrades a claim, and a report with `producers_run: 1` upgrades nothing about normalisation. | proposed | `F-b1-04` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: neither adapter's internals reach the envelope. The request path's headers and status codes, the repository hook's delivery metadata, the agent protocol's own task identifiers and conversation grouping stay inside the mapper; cap-work-intake already fixes the envelope as the whole surface. | proposed | `F-part-c-09` |
| Proposed: no configuration flag lets a producer skip the builder or receive a result in its acknowledgement, which is why both are consts in IntakeAdapterConfig. A fast path is exactly how a favoured producer becomes a second, unwired way in. | proposed | `F-b4-01` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Publish the envelope schema and the equivalence fixture corpus before writing any mapper, and keep the corpus in version control beside the schema. | Proposed sequencing. The corpus is simultaneously the normalisation test and the swap test, so writing it first means no mapper can be built to its own idea of equivalent; a corpus derived from the producer that already runs would encode that producer's fingerprints as expectations. | proposed | `F-b3-08` |
| 2 | Bring the producer that already runs behind the envelope first: keep its trigger and its transport, and change only that it now calls the shared builder and gets an acknowledgement back instead of doing its own thing. | A repository-event producer is already a deployment role, so this step is reversible and observable on real traffic. Rewriting the transport at the same time as introducing the envelope would leave no way to tell which change caused a regression. | sourced | `F-a5-01`, `E-adapter-git-event` "`git_events`, `approve`, `cells`" |
| 3 | Build the agent-message producer as the second implementation behind the same builder, and give it no privileges the first does not have: no synchronous result, no field of its own, no separate validator. | Proposed. build-adapter-pair states design rule 3 and cap-work-intake states the axis this pair differs on (F-b3-08, F-b1-04): whether the producer is still there when the job finishes. Granting the agent producer a shortcut would collapse the axis and leave two adapters of the same shape. | proposed | `F-b1-04`, `F-b3-08` |
| 4 | Migrate in three revertible steps and keep both producers live at the end: envelope built and validated but the old path still authoritative, then the envelope authoritative for one producer, then both producers selectable by configuration. Delete neither. | Proposed migration. Each step is revertible because the schema does not change, and an interface with one surviving implementation drifts back into the shape of whatever runs, which is the failure the pair exists to prevent. | proposed | `F-b1-04` |
| 5 | Stamp actor and delegation chain, correlation, budget ceiling and the derived idempotency key in the builder, at the single point where a producer message becomes an envelope, and refuse the entry if any of them cannot be filled. | cap-work-intake already states the rule that the platform applies each; a caller cannot decline them (F-b4-01). What this facet adds is where: a single builder no producer can route around. Stamping later means an entry exists, briefly, with no actor and no ceiling, and that window is where the audit trail loses its first record. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them." |
| 6 | Build the identity fields as new construction rather than as a mapping of something existing: attest the producer's workload identity, exchange it for the platform's own subject, and record both hops in the chain, oldest last. | There is no identity field anywhere in the system today, so nothing upstream can be trusted to supply one and there is no legacy shape to preserve. Every action names an actor, including delegated agent actors, and the agent-message producer is precisely the case that makes a one-hop chain wrong. | sourced | `F-a6-05`, `F-b4-03` "Every action names an actor, including delegated agent actors." |
| 7 | Return refusals as typed problems from the registry from the first commit, and count untyped refusals in the equivalence report rather than assuming there are none. | cap-errors owns the shape and the registry (F-b3-13) and the recorded gap here is that typed errors are absent, so the starting value of that counter is every refusal. Counting it makes the gap visible in a report instead of in a producer's inbox. | sourced | `F-a6-06`, `F-b3-13` "Typed errors \| Absent" |
| 8 | Apply build-adapter-pair: run one equivalence runner parameterised over the producer adapters, selected by configuration with no code edit between runs, and record `selected_by` and the producer that actually answered in the one report shape; proposed pointer, see that skill's references/conformance-run-shape.md. | The parameterised suite and the configuration-only swap are build-adapter-pair's step; the report shape it did not state was added there as references/conformance-run-shape.md rather than written out again in five capability skills (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-b1-04` "Every interface ships with at least two adapters" |
| 9 | Open references/intake-adapters.md when you need the per-producer mapping table, the failure modes each adapter can and cannot detect, or the step-by-step migration runbook. This skill body is enough to build either producer without it. | Proposed, progressive disclosure. The mapping table and the runbook are long material a reader wiring the builder does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: derive the idempotency key in the mapper, never in the builder, and write the derivation rule down per producer. The builder cannot know whether two producer messages are the same act; only the producer's own identifiers can say, and a rule that lives in code review rather than in a table is a rule that changes silently. | proposed | `F-b4-08` |
| Set correlation explicitly in the builder rather than reading it off the transport, because correlation rides on explicit attributes, not trace parentage - and intake is the earliest point at which a producer could have handed us a parentage that will not survive the next hop. | sourced | `F-b4-06` "Correlation rides on explicit attributes, not trace parentage" |
| Proposed: run the equivalence corpus in CI on every change to either mapper, not only at the swap. A normalisation regression has no symptom until two producers submit the same job, which may be months after the change that caused it, and the corpus is the only place it surfaces the same week it is written. | proposed | `F-b1-04` |
| Proposed: record each equivalence run as an evidence record naming the adapter, the code version and the corpus hash, and label the result claimed until that record exists. build-evidence-record owns the record's fields; what matters here is that two producers make it easy to report a green run without saying which producer was green. | proposed | `F-b1-04` |
| Proposed: when a producer asks for a new envelope field, write the mapper that avoids it first and only then discuss the field. Most such requests are the producer's own identifier, its retry counter or its own status, and all three already have somewhere to go. | proposed | `F-b3-08` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-http` | today | cap-work-intake records this row and the axis the pair differs on (F-b3-08); what this facet adds is the mapping. A formatted event pushed over a request, with the repository-event producer that already runs as a deployment role as its first mapper and the command line and schedule occurrence as further mappers of the same execution model. Each builds an event, hands it over in one hop, and gets an acknowledgement back inside that hop. | Cannot stamp an actor from anything that exists today, since no identity field exists anywhere in the system (F-a6-05), so its delegation chain is new construction and starts as a single attested hop. Cannot refuse in the typed shape either until the registry exists, which is why `untyped_refusals` is a counter in the report rather than an assumption. | Keep the published envelope schema and the corpus still; register the second producer's mapper and flip the configuration. Reverting is the same flip, and any producer the builder refuses is visible in the report before it reaches real traffic. | claimed | `F-b3-08`, `F-a5-01`, `F-a6-05`, `E-adapter-http`, `E-adapter-git-event` "`git_events`, `approve`, `cells`" |
| `E-swap-candidate-any-conformant-producer` | second | An autonomous agent submitting through the agent messaging protocol, mapped into the same envelope by a registered mapper: the message identifier becomes the idempotency key, the submitting agent's attested identity becomes the first hop of the delegation chain, and the agent's own correlation, when it sends one, becomes the parent correlation rather than the correlation itself. | Cannot be told anything synchronously beyond the acknowledgement, cannot be assumed present when the job ends, and cannot be assumed to have a human reading its refusals. cap-work-intake already records that axis (F-b3-08); what this facet adds is its consequence in code - `ack_carries_result` is a const false in IntakeAdapterConfig, so the first adapter cannot quietly acquire a synchronous result path that the second could never serve. | Set `adapter` in IntakeAdapterConfig and re-run the identical corpus with no code edit between runs; merge the two reports and require `adapters_run == 2`, `selected_by == "configuration"` in both, `distinct_job_digests == 1` in each, and `untyped_refusals == 0` in each. | claimed | `F-b3-08`, `F-b1-04`, `E-swap-candidate-any-conformant-producer` "any conformant producer" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P7, extended with the swap: `python3 tools/conformance/intake_equivalence.py --adapter request-pushed-event --job fixtures/intake/one-job.json --report out/intake-a.json` then the same command with `--adapter agent-message --report out/intake-b.json`, the adapter chosen by configuration with no code edit between runs. Both reports must validate against the IntakeEquivalenceReport shape above and assert, per adapter, `distinct_job_digests == 1`, `distinct_entry_ids == producers_run`, `invalid == 0` and `untyped_refusals == 0`; the merged report must show `adapters_run == 2` and `selected_by == "configuration"` in both. |
| Expected | both runs exit 0; each report shows `distinct_job_digests: 1`, `distinct_entry_ids` equal to `producers_run`, `invalid: 0` and `untyped_refusals: 0`, and the merged report shows `adapters_run: 2` |
| Deliberate breakage | Let the request-pushed producer's mapper stamp a default `priority` field onto the envelope it builds, leaving the agent-message mapper and the corpus untouched, and re-run both commands. |
| Expected failure | the request-pushed run exits 1 with `distinct_job_digests: 2` and `invalid: 3` naming that adapter, because the stamped field is not in the published schema and the envelope it produces no longer digests to the same value as the corpus expects, while the agent-message run still exits 0. Singling out one adapter is the point: a run that fails both, or neither, has not tested the swap. Claimed: neither mapper, the corpus nor the runner exists here, the typed registry the refusal counter needs is recorded as absent and there is no identity field to build the actor from, so this check starts red by construction. |
| Status | claimed |
| Evidence | `F-b3-08`, `F-b1-04`, `F-a6-06`, `F-a6-05` "any conformant producer" |

## Composes with

Builds on: `cap-work-intake`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: `cap-work-intake-use`

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
