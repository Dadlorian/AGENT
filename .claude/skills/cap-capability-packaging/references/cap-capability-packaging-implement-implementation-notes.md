# Capability packaging - implementation notes

Proposed. Open this only while running the migration diff, wiring the load path, or reviewing a
binding record. The body of `cap-capability-packaging-implement` is enough to build and judge the
adapter pair without it.

## 1. The two binding records, side by side (proposed)

| Field | today | second |
|---|---|---|
| `role` | `today` | `second` |
| `resolution` | `directory-scan` | `registry-fetch` |
| `location` | the configured package root | the registry endpoint plus namespace |
| `cache` | `null` | a local cache directory |
| `where_bytes_come_from` | local directory read | network fetch |
| `identity_is` | a path | a namespace-scoped name with a content digest |
| `network_required` | `false` | `true` |

Two bindings that agree on every `execution_model` row are one adapter written twice. That is the
condition the pair check exists to fail on.

## 2. Migration from directories to a registry (proposed)

| Step | Action | Stop condition |
|---|---|---|
| 1 | Render every package from its data and record a digest per package tree. | `packages_checked` equals the number of package directories. |
| 2 | Publish every rendered tree through the registry adapter under its namespace-scoped identity. | Every identity resolves through the registry binding. |
| 3 | Resolve the whole identity set through both bindings and diff resident fields, bodies, reference sets and digests. | `resolution_divergence == 0` and `digest_mismatch == 0`. |
| 4 | Record the run as an evidence record, then switch the default binding. | The evidence record names the command, the identity set, the code version and the counts. |
| 5 | Only then may a directory stop being the source of truth. | Not before step 4 is recorded; a green run with no record is claimed, not measured. |

The risk this order manages is not a loud failure. It is a registry that serves a re-rendered or
stale copy differing in one reference file, which no smoke test notices and a digest diff catches
on the first run.

## 3. Wiring table: what rides on a resolution (proposed)

| Concern | Applied where | What a caller can do about it |
|---|---|---|
| Telemetry | the resolver records every resolution with the correlation attribute set at dispatch | nothing; there is no flag |
| Policy | consulted before a package from a namespace the platform does not own is loaded | nothing; refusal is deterministic and happens before the fetch |
| Budget | the resolution is counted against the calling unit's ceiling | nothing; the ceiling is on the unit, not the call |
| Provenance | the resolved digest is attached to whatever the loaded package produces | nothing; it is attached, not requested |

## 4. Per-package rows of the conformance report (proposed)

```json
{
  "identity": "cap-capability-packaging",
  "sources": [
    {"role": "today",  "resolved": true, "digest": "<sha256>", "tiers_loaded": ["resident", "body"]},
    {"role": "second", "resolved": true, "digest": "<sha256>", "tiers_loaded": ["resident", "body"]}
  ],
  "divergence": [],
  "digest_match": true
}
```

`divergence` is the list of member paths that differ between sources, empty on a passing run. It is
a list and not a boolean because the first question after a red run is always *which part* differed.
