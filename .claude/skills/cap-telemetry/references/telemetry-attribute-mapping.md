# Telemetry attribute mapping — long material

Proposed unless a record id is given. Open this only when you need the per-operation table,
the instrument list, or the record of what each cited snippet does and does not establish.
The skill body is enough to judge an implementation without this file.

## 1. The two halves of the interface

| Half | What it fixes | Cadence | Records |
|---|---|---|---|
| Transport and shape | The wire format for spans, metrics and logs, and the resource-attribute carrier | Pinned; moves rarely | `X-cross-structure-011` "The OTLP specification is stable for the trace, metric and log signals."; `X-cross-structure-012` "These resource attributes MUST NOT be ever changed" |
| Attribute mapping | Which operation names and attribute keys a unit of work emits | Versioned separately; expected to move | `X-entry-composition-050`; `X-entry-composition-051` "and not one is marked Stable"; `X-cross-structure-010` |

An emitter binds to the first half. It reaches the second through `describe_mapping`, so a
revision of the vocabulary is a change to one adapter and to no emitter.

## 2. Operation names (proposed mapping, drawn from the cited vocabulary)

`X-entry-composition-050` records that the vocabulary's operation attribute "covers the full agent
lifecycle — including create_agent, invoke_agent, invoke_workflow, execute_tool, retrieval, plan,
plus memory operations". `X-cross-structure-009` records the expected shape: "The span tree
includes a top-level invoke_agent span with child chat spans for each LLM call and execute_tool
spans for each tool invocation."

| Platform unit of work | Proposed operation name | Notes |
|---|---|---|
| A workflow executing | `invoke_workflow` | One per run at depth 0 |
| An agent step | `invoke_agent` | One per agent call, whatever its depth |
| A model completion | `chat` | Child of the agent step in the same process; a separate root elsewhere |
| A tool or capability call | `execute_tool` | Includes calls that leave the process |
| A planning pass | `plan` | Emitted before execution begins, per design rule 5 |

Anything with no name in the vocabulary is emitted under a platform-owned namespace, never under
the vocabulary's namespace, so a mapping revision cannot collide with it.

## 3. Correlation attributes

The full shape is `CorrelationResourceAttributes` in the skill body. Two points that do not fit there:

- The set is stamped once, at dispatch, as resource attributes. A per-emitter derivation is the
  failure mode `X-cross-structure-015` records, where instrumentation "creates a completely
  separate entry in traces" even inside one process.
- `correlation.parent_id` records lineage and is never used to reassemble a run. Reassembly is a
  group-by on `run.id` alone, which is what makes the depth-3 assertion in the definition of done
  meaningful.

## 4. What the cited records do and do not establish

| Record | Establishes | Does not establish |
|---|---|---|
| `X-cross-structure-011` | A version string and a stability claim for the transport, from a search result | That the version was read from the specification; the record is search-only |
| `X-entry-composition-051` | That every relevant attribute carried a Development badge as of mid-July 2026 | Which version this platform should pin |
| `X-cross-structure-010` | That the conventions were experimental as of March 2026 | Any date after that |
| `X-cross-structure-012` | That some resource attributes are declared unchangeable | That every resource attribute is |
| `X-cross-structure-008` | That the vocabulary has no session grouping attribute | That one is coming |
| `F-a7-02` | That a depth-3 tree produced three unrelated root traces here | That parentage fails in every runtime |

## 5. Instruments (proposed)

| Instrument | Kind | Attributes permitted |
|---|---|---|
| `step.duration` | Histogram | operation, outcome, model class |
| `step.cost` | Counter | operation, model class |
| `run.depth` | Histogram | entry kind |
| `emission.dropped` | Counter | reason |

Every instrument carries the correlation resource attributes, so a metric can be joined to a span
on `run.id` without a second lookup.
