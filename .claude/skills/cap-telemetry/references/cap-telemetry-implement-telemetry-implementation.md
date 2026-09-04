# Telemetry implementation — long material

Proposed unless a record id is given. Open this for the migration checklist, the per-adapter
capability table, or the failure modes each adapter can and cannot detect. The skill body is
enough to build either adapter without this file.

## 1. Migration checklist

Each stage is independently revertible. The revert step is the point of writing them down.

| # | Stage | Done when | Revert |
|---|---|---|---|
| 1 | Correlation identifiers set once per run at dispatch | Every state record carries the run and correlation identifiers | Already true today; nothing to revert |
| 2 | Transport emitter, placeholder operation names, exporting to the running backend | A depth-3 run produces spans that a `run.id` query returns for all three levels | Disable the exporter; the identifiers stay |
| 3 | Mapping adapter loaded from a versioned table, version stamped on the run | `mapping_version` readable off the wire in the conformance report | Pin the previous table version; emitters unchanged |
| 4 | Pipeline process in front of both backends | Redaction and sampling live as pipeline stages, not in emitters | Export direct; stages are lost, emitters unchanged |
| 5 | Second backend selected by configuration | `adapters_run == 2` and `selected_by == "configuration"` in the merged report | Point the endpoint back; no code change either way |

If any stage needs an emitter edit to revert, the emitter had been bound to something it should
not have been bound to, and that is the finding.

## 2. Per-adapter capability table

| Property | Hosted trace UI and ingestion API | Collector pipeline into a columnar store |
|---|---|---|
| Accepts the standard payload unchanged | yes | yes |
| Correlation by resource attribute | yes | yes |
| Answers a semantic question about a model call | yes | declared unsupported |
| Runs with no separate service reachable | no | yes |
| Query surface | its own API and UI | whatever queries the store |
| Redaction point | pipeline stage | pipeline stage |

The row that matters for design rule 3 is the third: it is the only property the two do not share,
and any field on the interface that exists to serve it is a field shaped around one adapter.

## 3. Failure modes and which adapter surfaces them

| Failure | Surfaced by | Notes |
|---|---|---|
| Correlation attribute never injected | Both, as `run_id_groups == 0` | This is the definition-of-done breakage |
| Attribute injected twice with different values | Both, as `run_id_groups == 2` | The reason for a single injection point |
| Exporter configured but inert | Both, as zero spans returned | `F-a7-04`: configuration can validate, review correctly and have no runtime effect |
| Vocabulary revision renames an attribute | The report, as a changed `mapping_version` | `X-entry-composition-051`: the vocabulary is pre-stable |
| Backend silently discards an unknown attribute | Only the pipeline adapter, by storing it | The hosted adapter's ingestion model may drop it without an error |
| Trace context lost at an agent boundary | Neither, by design | `F-a7-02` records it as expected; `distinct_trace_ids` is reported, never asserted |

## 4. What is deliberately not built

- No sampling decision exposed to a caller. A dropped emission is counted on an instrument.
- No second injection site for the correlation attributes, however convenient.
- No attribute key from the pre-stable vocabulary written as a literal inside an emitter.
- No assertion anywhere that a run has one trace tree.
