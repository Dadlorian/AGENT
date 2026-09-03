---
name: "cap-telemetry"
description: "The ideal state of the Telemetry capability: traces and metrics emitted in a form any collector can ingest, with correlation carried on explicit attributes set at dispatch rather than on trace parentage, and with the stable transport half of the interface kept apart from the pre-stable attribute vocabulary. Load it when deciding what a unit of work must emit, when choosing where a run identifier lives, when a run shows up as several unrelated trees instead of one, when judging whether an observability backend can be swapped, or when someone proposes reconstructing a run from span parents. Also load it when an attribute naming convention is about to be adopted wholesale, when spans and metrics must line up with a run that crossed an agent or process boundary, and when a review asks what an emitter is allowed to put on the wire."
---

# cap-telemetry

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for emitting traces and metrics that a collector we did not write can ingest, and make reassembling a run a property of explicit attributes rather than of a trace tree that has already been measured not to survive the agent boundary. | sourced | `F-b3-10`, `F-b4-06`, `E-capability-telemetry`, `E-concern-telemetry` "Correlation rides on explicit attributes, not trace parentage" |

## Entities

| Entity |
|---|
| `E-capability-telemetry` |
| `E-concern-telemetry` |
| `E-standard-otlp` |
| `E-standard-genai-semantic-conventions` |
| `E-adapter-langfuse-opentelemetry` |
| `E-swap-candidate-any-otlp-collector` |
| `E-swap-candidate-phoenix` |
| `E-swap-candidate-braintrust` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-otlp` | 1.11.0 (unverified) | unverified | https://opentelemetry.io/docs/specs/otlp/ | `F-b3-10`, `X-cross-structure-011`, `X-cap-telemetry-001` |
| `E-standard-genai-semantic-conventions` | pre-stable (unverified) | unverified | https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/ | `F-b3-10`, `X-entry-composition-051`, `X-cross-structure-010`, `X-entry-composition-050` |

- `E-standard-otlp` version note: 1.11.0 named by one search-only record, which also says the specification is stable for the trace, metric and log signals; the specification was not fetched from this environment, so the version stays unverified
- `E-standard-genai-semantic-conventions` version note: pre-stable; two search-only records place every attribute at Development stability in 2026 and no record on file fixes a version this platform has adopted, so the mapping version is recorded per run rather than asserted here

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| bind (proposed operation set; the recorded row fixes a transport and a vocabulary, not a set of calls) | the correlation attribute set for a unit of dispatch: run id, correlation id, optional parent correlation id and depth | an emission context whose resource attributes carry that set, stamped onto every span, metric and log emitted beneath it; the core imports this call at dispatch and nowhere else | proposed | `F-b4-06`, `X-cross-structure-012` |
| emit | a completed unit of work: an operation name drawn from the attribute mapping, start and end instants, an outcome, and the attributes the mapping defines for that operation | nothing to the caller; the unit is handed to the pipeline, and a caller that could read a result back would start branching on the backend. The operation name is drawn from the vocabulary's own lifecycle attribute, which already spans create_agent, invoke_agent, invoke_workflow and execute_tool. | sourced | `F-b3-10`, `X-entry-composition-050` "including create_agent, invoke_agent, invoke_workflow, execute_tool, retrieval, plan, plus memory operations" |
| measure | an instrument name, a value, and the attribute subset the mapping permits on that instrument | nothing to the caller; metrics are the raw numeric data collected from various sources and travel the same transport, stable for the metric signal exactly as it is for traces, carrying the same correlation resource attributes as spans so one signal can be joined to another on the run id | sourced | `X-cap-telemetry-006`, `X-cross-structure-011` "Metrics are the raw numeric data collected from various sources" |
| describe_mapping (proposed) | nothing | the attribute-mapping version in force, recorded with the run, so a reader can tell which vocabulary a body of telemetry was emitted against without guessing from the attribute names | proposed | `X-entry-composition-051`, `X-cross-structure-010` |

### Shapes (JSON Schema 2020-12)

**CorrelationResourceAttributes: the field set stamped at dispatch, the machine-readable form of the invariant below** (sourced; sources: `F-b4-06`, `X-cross-structure-012`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:correlation-attributes:0.1",
  "title": "CorrelationResourceAttributes",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "run.id",
    "correlation.id",
    "entry.kind"
  ],
  "properties": {
    "run.id": {
      "type": "string",
      "minLength": 1,
      "description": "The grouping key. Every span, metric and log of one run carries it; grouping on it must yield exactly one group per run whatever the trace ids say."
    },
    "correlation.id": {
      "type": "string",
      "minLength": 1
    },
    "correlation.parent_id": {
      "type": "string",
      "description": "Present below depth 0. It records lineage without making reassembly depend on it."
    },
    "correlation.depth": {
      "type": "integer",
      "minimum": 0
    },
    "entry.kind": {
      "type": "string",
      "description": "Which entry the run came in through; the vocabulary belongs to the entry envelope, not to this capability."
    },
    "telemetry.mapping_version": {
      "type": "string",
      "description": "The attribute-mapping version this emission was produced against, per describe_mapping."
    }
  }
}
```

**TelemetryUnit (proposed summary shape; the per-operation attribute table and the full instrument list are in references/telemetry-attribute-mapping.md)** (proposed; sources: `X-entry-composition-050`, `X-cross-structure-009`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:unit:0.1",
  "title": "TelemetryUnit",
  "type": "object",
  "required": [
    "operation",
    "started_at",
    "ended_at",
    "outcome",
    "resource"
  ],
  "properties": {
    "operation": {
      "type": "string",
      "description": "A name from the attribute mapping, not a name of ours. The mapping's own vocabulary spans agent, workflow and tool operations."
    },
    "started_at": {
      "type": "string",
      "format": "date-time"
    },
    "ended_at": {
      "type": "string",
      "format": "date-time"
    },
    "outcome": {
      "enum": [
        "ok",
        "error"
      ]
    },
    "resource": {
      "$ref": "urn:agentic:telemetry:correlation-attributes:0.1"
    },
    "attributes": {
      "type": "object",
      "description": "Mapping-defined attributes only. An attribute this platform invented lives under a namespace of ours so a mapping revision cannot collide with it."
    },
    "trace_id": {
      "type": "string",
      "description": "Optional and never load-bearing. Several distinct values within one run.id are permitted."
    }
  }
}
```

**Worked example 2 (proposed): the failure shape, when a run cannot be shown [caller's view, folded from cap-telemetry-use]** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:example:unavailable",
  "title": "A run with nothing to show",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Ask for a run whose retention window has passed, or one whose identifier never existed. The answer is RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns. The type below is proposed and needs a row added to that registry before anything may raise it. Note what is not here: a failure to export is never raised at you, because a caller who could see one would start deciding whether telemetry mattered. The type is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns: until `urn:agentic:problem:telemetry-unavailable` has a row, an implementation returns the registered `adapter-unavailable` with the run id and the retention window in detail, accepting that it is 503 and retryable where a passed retention window is neither, which is itself the argument for the row.",
  "examples": [
    {
      "type": "urn:agentic:problem:telemetry-unavailable",
      "title": "No telemetry is retained for that run",
      "status": 404,
      "detail": "run.id run-human-0001 has no retained telemetry; the retention window for this deployment is 30 days",
      "retryable": false,
      "correlation_id": "corr-human-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The recorded row for this capability names OTLP and the GenAI semantic conventions as the governing standards, an SDK-plus-trace-UI pairing as the adapter today, and a general-purpose collector among the swap candidates. | sourced | `F-b3-10`, `E-capability-telemetry` "OTLP · GenAI semantic conventions" |
| The concern's contract is one sentence and it is the whole design: correlation rides on explicit attributes, not trace parentage. Reassembling a run is a group-by on an attribute the platform set, never a walk up a parent chain. | sourced | `F-b4-06`, `E-concern-telemetry` "Correlation rides on explicit attributes, not trace parentage" |
| Parentage may be present and is never relied on. More than one distinct trace id inside one run is a permitted outcome, not a defect, because a depth-3 task tree produces three unrelated root traces. agentic-stack states the remedy as a best practice (F-a7-02); the consequence for this interface is that no operation takes a parent span as an input and no query on the interface starts from one. | sourced | `F-a7-02` "A depth-3 task tree produces three unrelated root traces." |
| The correlation set is carried as resource attributes rather than span attributes because that surface is declared unchangeable by the specification that defines it: these resource attributes MUST NOT be ever changed. build-interface-versioning reads the same record as the model for a frozen field set; the consequence here is that the carrier for correlation is chosen for stability, not convenience. | sourced | `X-cross-structure-012`, `F-b4-06` "These resource attributes MUST NOT be ever changed" |
| Proposed: this interface is two contracts on two cadences, not one. The transport and shape half is pinned and rarely moves, the attribute-mapping half is versioned separately and may be revised without touching a single emitter. build-interface-versioning states the general discipline and names this interface as its first application; what is added here is that the split is part of the capability's contract rather than a release habit. Research query: has a GenAI semantic-convention revision actually landed since this repo was built, so the mapping-adapter split can be measured against a real version bump rather than argued from the maturity difference alone? | proposed | `F-b3-10`, `X-cross-structure-011`, `X-entry-composition-051` |
| The split is justified by maturity, not taste: the transport specification is stable for the trace, metric and log signals, while the attribute vocabulary is not. An interface that versioned both together would either freeze the vocabulary or churn the transport. | sourced | `X-cross-structure-011` "The OTLP specification is stable for the trace, metric and log signals." |
| The attribute vocabulary is adopted as pre-stable and cited as such: as of mid-July 2026 the registry marks every relevant attribute Development, and not one is marked Stable. Every emission therefore records the mapping version it was produced against, so a later revision is a readable change rather than a silent one. | sourced | `X-entry-composition-051`, `X-cross-structure-010` "and not one is marked Stable" |
| Proposed: the platform's own correlation fields are independent of the attribute mapping. A revision of the vocabulary changes the mapping adapter and nothing in the entry envelope, which is what keeps a pre-stable dependency from reaching the one shape every caller fills in. Research query: is there a fetched (not search-only) record of the GenAI semantic-conventions stability status, to confirm 'pre-stable' still holds rather than being a stale assumption? | proposed | `T-t2-02`, `X-entry-composition-051` |
| One vocabulary covers agent, workflow and tool work rather than one per kind of step, because the mapping's own operation attribute already spans them; a platform-invented name per step kind would make a run unreadable to any collector that knows the conventions. | sourced | `X-entry-composition-050`, `X-cross-structure-009` "The gen_ai.operation.name attribute covers the full agent lifecycle" |
| Telemetry is applied by the platform and cannot be requested or declined. agentic-stack states design rule 7 (F-b1-08, F-b4-01); the consequence for this interface is that there is no emit flag on any request shape and no sampling decision a caller can make, so a step that produced no telemetry is a defect rather than a caller's choice. All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach it the same way, and there is no caller-side difference between them; what enhancing one aspect leaves untouched is stated by this table's row on the platform's own correlation fields being independent of the attribute mapping, and the caller's view is in references/usage.md. | sourced | `F-b1-08`, `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The criterion a result is judged against never appears as a span attribute, a metric label or a resource attribute: an agent sees its outcome, never the criterion it is judged against. agentic-stack states design rule 6 (F-b1-07); what this interface forbids specifically (proposed) is a judged step emitting the rule alongside its verdict, because telemetry is the one signal that reaches every backend and every reader, including the agent's own tooling. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |
| Prompt and completion payloads, credentials and personal data are not on this interface: use the propagated key-value store judiciously and avoid storing sensitive values in it. cap-identity reads the same record for that store; the rule here (proposed) is the emitter's: an attribute value is a non-secret reference, and a payload that must be inspected is fetched from the store by its digest rather than copied onto a span. | sourced | `X-cross-structure-006` "avoid storing sensitive values" |
| Proposed: the identity of the backend is not visible on the interface. No operation names a destination, a query language or a UI concept, because a caller that could tell one backend from another would encode the difference and the swap would stop being free. Research query: does the OTLP export protocol itself define a backend-identity field the interface must actively suppress, or is there simply nothing in the wire format that names one? | proposed | `F-b1-05` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Draw the interface as two halves before writing an emitter: a pinned transport and shape contract, and a separately versioned attribute mapping. Emitters bind to the first half only and reach the second through a lookup. Research query: see the two-cadence research query on the sibling invariant row above. | Proposed. The two halves have measurably different maturities, so binding an emitter to both means every vocabulary revision edits every emitter. Splitting them makes a revision a change to one adapter. | proposed | `X-cross-structure-011`, `X-entry-composition-051`, `F-b3-10` |
| 2 | Set the correlation attribute set as resource attributes at dispatch, in the CorrelationResourceAttributes shape above, and set it in exactly one place rather than at each emission site. | One place is the only version that survives a boundary: a value re-derived per emitter is a value some emitter will re-derive differently, and the whole contract is that a group-by returns one group. | sourced | `F-b4-06`, `X-cross-structure-012` "Correlation rides on explicit attributes, not trace parentage" |
| 3 | Permit several trace ids per run explicitly: assert on the group count under the run attribute and never assert that the run has one trace tree. | Nine times out of ten when spans show up as disconnected root spans instead of forming a proper trace tree, the problem is that you crossed an async boundary and the trace context did not come with you. A conformance check that demanded a single tree would fail on correct behaviour and be switched off. | sourced | `X-cross-structure-013`, `F-a7-02` "the problem is that you crossed an async boundary and the trace context did not come with you" |
| 4 | Map every unit of work onto the mapping's own operation vocabulary, including the workflow and tool operations, and put anything this platform invents under a namespace of ours. | The vocabulary already spans the agent lifecycle, so adopting it makes a run readable to a collector that knows the conventions and nothing else; a separate namespace for our own attributes means a vocabulary revision cannot collide with a field the platform depends on. | sourced | `X-entry-composition-050`, `X-cross-structure-009` "top-level invoke_agent span with child chat spans for each LLM call and execute_tool spans for each tool invocation" |
| 5 | Record the attribute-mapping version with the run, next to the telemetry rather than in a release note, and treat a body of telemetry with no recorded mapping version as unreadable. | The vocabulary is pre-stable, so a mapping version is what tells a later reader whether an attribute is missing or merely renamed. Without it, the only way to date a body of telemetry is to guess from the attribute names. | sourced | `X-cross-structure-010`, `X-entry-composition-051` "As of March 2026, most GenAI semantic conventions are in experimental status" |
| 6 | Judge a candidate implementation on four questions: can a collector nobody here wrote ingest the output unchanged; does a group-by on the run attribute return one group across a depth-3 tree; is the mapping version present on every run; and can the backend be replaced by editing configuration only. | These are the criteria the definition of done below mechanises. agentic-stack states design rule 4 (F-b1-05), that if integration requires our SDK, a boundary is bespoke where a standard existed; the consequence for this boundary is the first question, because a backend nobody else can feed is exactly that bespoke boundary wearing a standard's name. | sourced | `F-b1-05`, `F-b1-04` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| 7 | Put the pipeline between the emitters and the backends, and add filtering, redaction or aggregation as a stage in it rather than as a change to what an emitter sends. | The pipeline model is receivers, processors and exporters as separate building blocks, which is a working example of enhancing one aspect without touching the rest: a redaction rule becomes a processor, and no emitter and no backend is edited to get it. | sourced | `X-cross-structure-057`, `T-t2-02` "Processors (components that modify, enhance, filter, or aggregate telemetry data)" |
| 8 | Send what you were already sending. Do not add a tracing call, a span of your own, or a request to be observed; there is nothing to opt into. | Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller. What this adds (proposed): a caller-side switch would be a hole rather than a feature, and a span you mint yourself is the one thing in the run with no correlation attributes on it. | sourced | `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller." |
| 9 | Proposed: open references/telemetry-attribute-mapping.md when you need the per-operation attribute table, the instrument list, or the record of what each cited research snippet does and does not establish. This skill body is enough to judge an implementation without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The mapping table is long material that moves on its own cadence, which is precisely why it does not belong in the part of the contract that is meant to stay still. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Keep the propagated key-value store for references, never for values that matter: it may be sent to unintended downstream services, so an identifier belongs there and a secret or a payload does not. | sourced | `X-cross-structure-006`, `X-cross-structure-004` "may be sent to unintended downstream services" |
| Expect the vocabulary to move and design for it rather than around it. Two independent records place the conventions at pre-stable in 2026, so an adopter must pin a version and plan for churn; treating them as settled is how a mapping revision becomes an outage in the emitters. | sourced | `X-cross-structure-010`, `X-entry-composition-051` "most GenAI semantic conventions are in experimental status" |
| Join the signals on the correlation attribute rather than keeping three stores: metrics, logs and traces are the foundational pillars and each serves a distinct purpose, so the value of one correlation key set once is that a latency spike, a log line and a span belong to the same run without a second lookup. | sourced | `X-cap-telemetry-006`, `F-b4-06` "Three telemetry signals are the foundational pillars of observability: metrics, logs, and traces." |
| Do not expect framework-native tracing to bridge a mixed fleet: it cannot span boundaries between heterogeneous stacks, so an explicit attribute set in the handoff payload is the only thing that survives a hop into a runtime whose instrumentation we do not control. | sourced | `X-cross-structure-014`, `X-entry-composition-015` "Framework-native tracing cannot span boundaries between heterogeneous stacks" |
| Measure the correlation property on a depth-3 tree, never on a single call: a depth-3 task tree produces three unrelated root traces under the substrate's default behaviour. Depth 1 passes under both designs (proposed), so a suite that only exercises one hop will report green on exactly the arrangement that has already been measured to fail. | sourced | `F-a7-02` "A depth-3 task tree produces three unrelated root traces." |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-langfuse-opentelemetry` | today | The recorded adapter today is Langfuse + OpenTelemetry: an OTLP SDK exporting to a hosted trace UI with an LLM-aware ingestion API and its own object model of traces, observations and scores. It serves bind, emit and measure, and it is the only one of the pair that can answer a question about an LLM call without someone writing the query. | Cannot be the whole interface: its object model is richer than the transport, so any field that exists only in its ingestion API is a field the second adapter cannot accept. Its execution model is a hosted service reached over the network with a semantic model of LLM work built in. | Point the exporter at the other endpoint by configuration and change nothing else; cap-telemetry-implement owns the migration, the per-adapter conformance subsets and the full procedure, and this row records the roles PASS.md B3 fixes and the axis the pair differs on. | claimed | `F-b3-10`, `E-adapter-langfuse-opentelemetry` "Langfuse + OpenTelemetry" |
| `E-swap-candidate-any-otlp-collector` | second | A plain OTLP collector writing to a columnar store, with no LLM-specific interface at all: a receive-process-export pipeline process, no UI, no notion of a model call, correctness judged by rows landing in a table and answering a query. | Cannot render a trace tree, score a generation or interpret any attribute semantically; it stores what it is given. That is the axis the pair is chosen for, and it is a different execution model rather than a different product of the same shape: one is a hosted semantic service that understands LLM work, the other a local pipeline stage that understands none of it, so an interface secretly shaped around the first cannot be fed to the second at all. | Select the adapter by configuration only, with no code edit between runs, and run the identical depth-3 correlation suite against each; the merged report must show adapters_run >= 2. agentic-stack already states design rule 3 (F-b1-04): the second adapter exists to prove the first is not load-bearing. What is new here is the axis, not the rule. | claimed | `F-b3-10`, `F-b1-04`, `E-swap-candidate-any-otlp-collector`, `X-cap-telemetry-001` "any OTLP collector" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/conformance/telemetry_correlate.py --adapter llm-trace-ui --adapter otlp-collector-columnar --depth 3 --report out/tel.json |
| Expected | docs/decomposition.md section 3.2 row P9, made precise and run over the adapter pair above: that command (proposed tool), the adapter selected by configuration with no code edit between runs. Per adapter it executes a depth-3 task tree, then queries that backend for every span carrying resource attribute `run.id == R` and asserts that the returned spans cover all three levels, that grouping by `run.id` yields exactly one group, that `distinct_trace_ids >= 1` is permitted rather than asserted equal to 1, and that `mapping_version` is non-empty on the run; across adapters it asserts `adapters_run >= 2`. exit 0 with, per adapter, `levels_covered == 3`, `run_id_groups == 1`, `mapping_version` present, and `distinct_trace_ids` reported without being constrained, followed by `adapters_run=2` |
| Deliberate breakage | Remove the `run.id` resource attribute injection at dispatch, leaving both adapters and the command untouched. |
| Expected failure | exit 1 under both adapters with `levels_covered == 1` and `run_id_groups == 0`: the query returns only the top level and correlation collapses into three unrelated trees, reproducing PASS.md A7 finding 1. A run that still exits 0 means the query fell back to trace parentage, which is the failure this capability exists to avoid. Claimed: neither adapter is wired, the conformance tool does not exist and no span is emitted anywhere today, so neither run has been performed here. The measured starting state is recorded in cap-telemetry-use, where the reference corpus carries the correlation attributes on every record and emits zero spans. |
| Status | claimed |
| Evidence | `F-b4-06`, `F-a7-02` "A depth-3 task tree produces three unrelated root traces." |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`

Used by: `cap-evaluation`, `cap-telemetry-implement`, `xc-correlation`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is the correlation identifier a resource attribute, a span attribute, or both? | docs/decomposition.md section 5 question 8: emit both for one week across depth-3 trees and measure which survives the agent boundary and which is dropped or truncated by each collector in the path. | The resource attribute, because it is the direct remedy for a measured failure and because that surface is the one the specification declares unchangeable. Reversible by adding the span attribute alongside it, which costs one emitter change and no interface change. | `F-a7-02`, `X-cross-structure-012` "These resource attributes MUST NOT be ever changed" |
| Which attribute-mapping version does this platform pin, and can any version string be cited as verified? | A fetch of the conventions registry recording the version string and the stability badge on the attributes this platform emits; the records on file are search-only, one naming a transport version and two describing the vocabulary as pre-stable, and none was read. | The transport half stays version_status unverified with the version named by the record, the mapping half is pinned per deployment and recorded per run by describe_mapping, and no skill states a stability claim about an individual attribute until a fetch has happened. | `X-cross-structure-011`, `X-entry-composition-051`, `F-part-c-10` "The current OTLP specification version available is 1.11.0." |
| What groups several runs of one multi-agent session, given that the vocabulary has no session attribute? | Whether a platform-owned session attribute is needed at all: count, over real workloads, how many questions require joining more than one run, since the run attribute already answers everything inside one run. | Proposed: no session attribute until the count is non-trivial. The existing conversation attribute is designed for single conversation flows, not multi-conversation sessions, so borrowing it would encode a meaning the vocabulary does not have. | `X-cross-structure-008` "not multi-conversation sessions" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-telemetry 2831cb4f, 2026-09-03 |
