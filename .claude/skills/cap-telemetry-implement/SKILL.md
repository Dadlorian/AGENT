---
name: cap-telemetry-implement
description: How to build the Telemetry capability on this stack: what the trace UI and ingestion API already running gives you and what it does not, an emitter bound to the pinned transport half, a separately versioned attribute-mapping adapter behind it, a second backend with a different execution model that understands no model calls at all, the migration order, where the correlation attribute set is injected so no step can skip it, and a definition of done with the breakage that makes it fail. Load it when writing the code that emits a span or a metric, when adding an exporter or a pipeline stage, when a run arrives at the backend as several unrelated trees, when a vocabulary revision lands, or when a conformance run reports a step with no run identifier on it.
---

# cap-telemetry-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-telemetry into something that runs here: one injection point at dispatch, an emitter bound only to the pinned transport, a mapping adapter that can be revised on its own, and two backends behind the same interface whose execution models differ. | sourced | `F-b3-10`, `F-a1-05`, `E-capability-telemetry` "Trace UI and ingestion API" |

## Entities

| Entity |
|---|
| `E-capability-telemetry` |
| `E-concern-telemetry` |
| `E-standard-otlp` |
| `E-standard-genai-semantic-conventions` |
| `E-adapter-langfuse-opentelemetry` |
| `E-swap-candidate-any-otlp-collector` |

## Contract

### Shapes (JSON Schema 2020-12)

**TelemetryConformanceReport (proposed shape; the counters the definition of done below asserts on, per adapter)** (proposed; sources: `F-b1-04`, `F-b4-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:report:0.1",
  "title": "TelemetryConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "levels_covered",
    "run_id_groups",
    "distinct_trace_ids",
    "mapping_version",
    "spans_missing_run_id",
    "selected_by",
    "adapters_run"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "llm-trace-ui",
        "otlp-collector-columnar"
      ]
    },
    "levels_covered": {
      "type": "integer",
      "minimum": 0,
      "description": "How many levels of the depth-3 tree the run.id query returned. Must equal 3."
    },
    "run_id_groups": {
      "type": "integer",
      "minimum": 0,
      "description": "Groups produced by grouping the returned spans on run.id. Must equal 1."
    },
    "distinct_trace_ids": {
      "type": "integer",
      "minimum": 0,
      "description": "Reported, never constrained. More than one is permitted and expected."
    },
    "mapping_version": {
      "type": "string",
      "minLength": 1,
      "description": "The attribute-mapping version the run emitted against, read back from the telemetry rather than from configuration."
    },
    "spans_missing_run_id": {
      "type": "integer",
      "minimum": 0
    },
    "semantic_queries_supported": {
      "type": "boolean",
      "description": "Declared unsupported by the pipeline adapter rather than reported false-with-an-asterisk."
    },
    "selected_by": {
      "const": "configuration",
      "description": "A code edit between runs would not be a swap."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the correlation attribute set is injected at exactly one place, the dispatch path, and no emitter constructs it. cap-telemetry states the contract that correlation rides on explicit attributes (F-b4-06); what this facet adds is the wiring rule, that a second injection site is a second definition and the first divergence between them is invisible until a query returns two groups. | proposed | `F-b4-06`, `F-a7-02` |
| Proposed: emitters link against the pinned transport half only. The operation names and attribute keys come from the mapping adapter at emission time, so a vocabulary revision is a swap of that adapter and touches no emitter, and no emitter contains a literal attribute key from the pre-stable vocabulary. | proposed | `X-cross-structure-011`, `X-entry-composition-051` |
| Proposed: the mapping version is read back out of the emitted telemetry in the conformance report, never taken from the configuration that was supposed to set it. agentic-stack states the finding that configuration written in the documented place can be silently overridden (F-a7-04); the consequence here is that mapping_version in the report shape above is a value observed on the wire. | proposed | `F-a7-04` |
| Proposed: both adapters implement the identical bind, emit, measure and describe_mapping calls, and the running adapter is chosen by configuration with no code edit between runs. build-adapter-pair states design rule 3 (F-b1-04); what this adds is that the selection appears in the report as selected_by, because an unobservable swap is indistinguishable from running one adapter twice. | proposed | `F-b1-04` |
| Proposed: the pipeline adapter declares semantic queries unsupported rather than reporting them as failing. A documented conformance subset is honest; an adapter that claims a property it cannot provide is the failure the pair exists to expose. | proposed | `F-b3-10`, `F-b1-04` |
| Proposed: what runs today already carries the correlation half and none of the emission half. Every ledger record written by the reference runner carries a run identifier and a correlation identifier, and nothing anywhere emits a span, so the first change is an exporter over values that already exist rather than a new identifier scheme. | proposed | `F-b4-06`, `T-t2-03` |
| Proposed: a failure to emit, export or map is returned as problem details from the registry cap-errors owns, and this capability mints no failure object of its own; a dropped emission is counted on an instrument rather than raised at the caller, because a caller that could see an export failure would start deciding whether telemetry mattered. | proposed | `F-b4-07`, `F-b1-08` |
| Proposed: the conformance run and its breakage are written to the evidence store in the form build-evidence-record fixes, naming the code version and the tree under test, and stay labelled claimed until they have been run here. | proposed | `F-a5-04` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from what is already true rather than from a green field: the correlation identifiers exist on every record and no span is emitted anywhere. Do not re-derive the contract; cap-telemetry states the recorded row (F-b3-10) and the concern's contract (F-b4-06), and this facet builds against them. | Proposed sequencing. The run and correlation identifiers are already set once per run in the reference runner, so the first change is an exporter over existing values; treating this as new work would mint a second identifier for runs that already have one, which is the divergence the single injection point exists to prevent. | proposed | `F-b3-10`, `F-b4-06` |
| 2 | Build the emitter against the pinned transport half first, with the correlation set as resource attributes and a placeholder operation name, and get it exporting before any attribute vocabulary is adopted. | The transport is the stable half, so an emitter written against it is finished work; adopting the vocabulary first would mean the first thing built is the thing most likely to change. The protocol is what carries telemetry to any ingestion endpoint, so an emitter with no vocabulary is already useful. | sourced | `X-cap-telemetry-001`, `X-cross-structure-011` "OTLP serves as the protocol for transmitting telemetry data across the OpenTelemetry ecosystem" |
| 3 | Add the attribute mapping as a separate, versioned component behind describe_mapping: a table from platform units of work to operation names and attribute keys, loaded at start, with its version stamped on the run. | Proposed. cap-telemetry states why the interface is split; the build consequence is that the mapping is a data table and not code inside the emitter, so revising it is an edit to one file and a version bump, and the run records which table it used. | proposed | `X-entry-composition-050`, `X-entry-composition-051` |
| 4 | Wire bind at the dispatch path only, so every step below it inherits the attribute set, and give callers no flag that skips emission or changes sampling. | Proposed wiring, following cap-telemetry's placement rule. One enforcement point covers every step of every entry, and a second would be a component deciding for itself, which is the property a cross-cutting guarantee does not have. | proposed | `F-b1-08`, `T-t2-03` |
| 5 | Build the second adapter as a pipeline into a columnar store with no model-aware interface, and keep the exporter code identical: only the endpoint and the pipeline configuration differ. | Proposed second adapter, per the manifest and the recorded swap-candidate column. It breaks a different assumption than the first: the running backend is a hosted service with a semantic object model that can answer a question about a model call, the second is a receive-process-export process that stores rows and interprets nothing. If the exporter needs editing to feed it, the interface had been shaped around the first. | proposed | `F-b3-10`, `F-b1-04` |
| 6 | Migrate in this order and keep both adapters live behind the same call: correlation identifiers only, then transport emission to the running backend, then the mapping adapter, then the pipeline backend selected by configuration. Do not remove the first backend once the second exists. | Proposed migration. Each step is independently revertible, and keeping both is what makes the pair testable later; an interface with one surviving implementation drifts back into the shape of whatever runs, which is the failure design rule 3 exists to catch. | proposed | `F-b1-04` |
| 7 | Put a pipeline process between the emitters and both backends from the start, even when only one backend exists, and add redaction, sampling and aggregation as stages in it. | Proposed. Its building blocks are separate components that ingest, modify and export, so a rule added there reaches both adapters at once; a rule added in the emitter has to be re-implemented per backend and is the first thing that diverges. | sourced | `X-cross-structure-057`, `T-t2-02` "Receivers (entry points that ingest telemetry data)" |
| 8 | Make the conformance run adapter-parameterised and depth-3 from the start: one command, one report shape, `--adapter` selecting the backend, and the query issued against that backend's own query surface rather than against our exporter's memory. | Proposed. A suite that reads what the exporter believes it sent tests the exporter, not the path; and a suite written against one backend and adapted later encodes that backend's query model in its assertions, which is exactly what the second adapter cannot satisfy. | proposed | `F-b1-04`, `F-a7-03` |
| 9 | Proposed: open references/telemetry-implementation.md when you need the per-adapter mapping table, the migration checklist with its revert step, or the list of failure modes each adapter can and cannot detect. This skill body is enough to build either adapter without it. | Proposed, progressive disclosure. The checklist and the failure-mode table are long material that a reader building the first exporter does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Verify the exporter's runtime effect, not the configuration that declares it. agentic-stack states the configuration finding (F-a7-04); the consequence here is that the only proof a deployment exports where it meant to is a span read back out of the backend, because a value that validated and was reviewed correctly can still have had no runtime effect. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Do not add a fast path that skips emission for cheap steps. agentic-stack states design rule 7 (F-b1-08), that telemetry, policy, provenance and budget are applied by the platform, not requested by the caller; the build consequence is that the moment one kind of step emits differently, the depth-3 assertion has to be re-proved per step kind, and a dropped emission belongs on a counter rather than in a branch. | sourced | `F-b1-08`, `T-t2-03` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| Instrument the boundary you do not control by handing it the attribute set in the payload, not in a header. Framework-native tracing cannot span boundaries between heterogeneous stacks, and the boundary that already failed here is an agent runtime that ignores an injected header and mints its own root trace. | sourced | `X-cross-structure-014`, `X-entry-composition-015` "Correlation IDs should be preserved at every boundary" |
| Proposed: build the depth-3 fixture before the exporter, and keep it as the smallest thing that reproduces the recorded failure. A fixture written after the exporter tends to assert what the exporter does; one written first asserts what the concern requires. | proposed | `F-a7-02`, `F-a7-03` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-langfuse-opentelemetry` | today | cap-telemetry already records this role (F-b3-10): the adapter today is Langfuse + OpenTelemetry, and Part A runs it as a trace UI and ingestion API with an async worker behind it. What this facet adds is the build: the SDK exporter carries the correlation set as resource attributes and the mapping adapter supplies the operation names, so the ingestion API receives a standard payload rather than a payload shaped for it. | Cannot be reached at all without its service and its store running, and cannot accept an attribute its ingestion model does not know without discarding it silently. Anything that exists only in its object model, such as a score attached to an observation, is a field the pipeline adapter cannot accept and therefore must not appear on the interface. | Point the exporter endpoint at the pipeline by configuration and change no exporter code; if any code change is needed, the interface had been shaped around this backend and that is the finding, not an inconvenience. | claimed | `F-b3-10`, `F-a1-05`, `E-adapter-langfuse-opentelemetry` "Langfuse + OpenTelemetry" |
| `E-swap-candidate-any-otlp-collector` | second | A plain collector pipeline writing to a columnar store: receivers accept the same payload, processors redact and aggregate, an exporter writes rows, and a query is written by whoever asks the question. No UI, no model-aware object model, no ingestion API of its own. | Cannot answer a semantic question about a model call, and declares semantic_queries_supported false rather than pretending. It runs as a local process with no hosted service behind it, which is the axis: a hosted semantic service against a local pipeline stage, a different execution model rather than a different product of the same shape. | cap-telemetry already records the two roles and the axis they differ on (F-b3-10, F-b1-04); what this facet adds is the procedure. Select by configuration only, run the identical depth-3 correlation suite against each backend's own query surface, and require the merged report to show adapters_run == 2, selected_by == configuration, and the pipeline adapter's declared subset recorded rather than asserted. | claimed | `F-b3-10`, `F-b1-04`, `E-swap-candidate-any-otlp-collector` "any OTLP collector" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P9, extended with the swap: `python3 tools/conformance/telemetry_correlate.py --adapter llm-trace-ui --depth 3 --report out/tel-a.json` then the same command with `--adapter otlp-collector-columnar --report out/tel-b.json`, the adapter chosen by configuration with no code edit between runs. Each run executes a depth-3 task tree, then queries that backend for every span carrying resource attribute `run.id == R`. Both reports must validate against the TelemetryConformanceReport shape above and assert, per adapter, `levels_covered == 3`, `run_id_groups == 1`, `spans_missing_run_id == 0` and a non-empty `mapping_version` read back off the wire; `distinct_trace_ids` is reported and never constrained, and the pipeline adapter declares `semantic_queries_supported` false rather than asserting it. |
| Expected | both runs exit 0; the merged report shows `adapters_run == 2`, `selected_by == "configuration"`, `levels_covered == 3` and `run_id_groups == 1` for each adapter, `distinct_trace_ids >= 1` recorded without assertion, and the same `mapping_version` string under both. |
| Deliberate breakage | Remove the `run.id` resource attribute injection at dispatch, leaving both adapters, the mapping table and the command untouched. |
| Expected failure | Both runs exit 1 with `levels_covered == 1`, `run_id_groups == 0` and `spans_missing_run_id` equal to the span count below the top level: the query returns only the top level and correlation collapses into three unrelated trees, reproducing PASS.md A7 finding 1. A run where either adapter still exits 0 means the query walked span parents instead of grouping on the attribute, and the suite is testing the wrong property. Claimed: no exporter is wired, neither backend receives anything from this platform and the conformance tool does not exist, so neither run has been performed here; the measured starting state is recorded in cap-telemetry-use, where the reference corpus carries correlation on every record and emits zero spans. |
| Status | claimed |
| Evidence | `F-b4-06`, `F-b1-04` "Correlation rides on explicit attributes, not trace parentage" |

## Composes with

Builds on: `cap-telemetry`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: `cap-telemetry-use`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which backend is primary once both exist, and does a deployment with no hosted service get the pipeline or no telemetry at all? | Measure, per adapter: emission latency added to the step path, how many separate processes must be running for a span to be stored at all, and whether the question a reader actually asks can be answered from the rows the adapter keeps. The second number decides whether the backend can sit behind the emission path in a constrained deployment. | Proposed: the pipeline is primary and the hosted service is fed from it as one exporter among several, so a deployment with no hosted service still stores telemetry and records the reduced query surface rather than emitting nothing. | `F-b1-04`, `X-cross-structure-057` |
| Where does the mapping version live so that a query can filter on it: a resource attribute on every span, a per-run record in the state log, or both? | Whether either backend can filter on a resource attribute cheaply at the volumes a real workload produces, and whether any reader needs the version without also having the run record next to it. | Proposed: a resource attribute on every emission, because the report reads it back off the wire, plus a per-run record in the state log so a reader who has the run but not the telemetry can still date it. Reversible by dropping the attribute, which changes the report's read path and nothing else. | `X-entry-composition-051`, `F-a7-04` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-telemetry 2831cb4f, 2026-09-03 |
