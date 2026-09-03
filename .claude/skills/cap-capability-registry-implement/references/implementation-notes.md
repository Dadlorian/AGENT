# Capability registry - migration procedure and wiring table

Opened while running the shadow migration, wiring the resolution path, or reviewing a binding record. The
body of `cap-capability-registry-implement` is enough to build and judge the adapter pair without this
file. Facts established in `cap-capability-registry` are referenced here by skill name and id, not
re-argued. Resolve ids with `python3 tools/kb.py show <id>`.

## 1. Where this starts

PASS.md Part A records the tool endpoint as live and authenticated with `zero tools registered`
(`F-a6-03`), and there is no registry row in the capability table at all. So the honest starting state is
red: nothing is registered anywhere, and the first adapter's first green conformance run is the first
thing this capability proves. Do not write the migration up as though its first half already happened.

The one integrity discipline that does run today is the hash chain on the task store, where
`each run's closing digest is the next run's opening digest` (`F-a5-03`, stated by
`build-evidence-record`). The registry index inherits it rather than inventing a second scheme.

## 2. Shadow migration, in order

| Step | Action | Done when |
|---|---|---|
| M1 | Publish one record per package that exists today: namespace, name, a semantic version, the digest of the package tree, a signature. Nothing is deleted or edited. | `records_checked` equals the number of packages, `index_chain_broken == 0`. |
| M2 | Run the resolver in shadow beside the path joins callers use now, over the same name and constraint set, and write both answers. | Every entry resolves to the same tree; a difference is a list, not a surprise. |
| M3 | Diff digests, not names. A name can agree while the tree behind it has moved on. | `record_divergence == 0` across the shadow pair. |
| M4 | Point one caller at `resolve` and leave the rest on path joins for one full section. | The switched caller's runs carry a resolved version in their records. |
| M5 | Switch the remaining callers; delete the path joins from core and seam in the same change. | The containment grep in the definition of done returns no files. |
| M6 | Stand the second store up, publish the same records to it, and add its binding to the conformance run. | `adapters_run >= 2` with `record_divergence == 0`. |

Rollback at any step is a binding-record change plus a restart. No published record is ever rewritten to
undo a migration step; the registry's own rule is that a change is a new version
(`cap-capability-registry`, `X-cap-capability-registry-007`).

## 3. Cross-cutting wiring

Design rule 7 is applied by the platform and cannot be declined (`F-b1-08`, `F-b4-01`, stated by
`agentic-stack`). On this capability that means six places, all on the resolution and publication paths:

| Concern | Where it attaches | What fails without it |
|---|---|---|
| Telemetry | A span per `resolve`, `publish` and `verify`, carrying the correlation attribute set explicitly at dispatch (`F-a7-02`). | A capability enters a run with no trace of which run pulled it in. |
| Policy | Before a record from a namespace this platform does not own is resolved. | An outside namespace becomes reachable by naming it. |
| Provenance | One record per publish, naming the code version, the tree hash and the actor (`F-a5-04`). | A published record cannot be attributed to what produced it. |
| Budget | Resolution and fetch counted against the calling unit's ceiling (`F-b4-02`). | Resolution cost is invisible until it terminates something. |
| Identity | The signing key and the trust anchor named in the binding record, attested at start-up. | The store verifies against whatever key it happens to hold. |
| Errors | Every refusal is a problem details object with a `urn:agentic:problem:` type, per `cap-capability-registry`. | A refusal has to be parsed from prose. |

## 4. Binding records, side by side (proposed)

```json
{ "role": "today", "resolution": "signed-index",
  "location": "var/registry/index.jsonl", "trust_anchor": "keys/registry-host.pub",
  "cache": null,
  "execution_model": { "where_record_bytes_come_from": "local signed index",
                       "identity_is": "a path plus a version string", "network_required": false } }
```

```json
{ "role": "second", "resolution": "registry-fetch",
  "location": "oci://registry.example.internal/agentic/records", "trust_anchor": "keys/registry-fleet.pub",
  "cache": "var/registry/cache",
  "execution_model": { "where_record_bytes_come_from": "network fetch",
                       "identity_is": "a content digest", "network_required": true } }
```

Two bindings that agree on every `execution_model` member are one adapter written twice. The axes above
are the ones this pair differs on; if a future store differs on neither, it is not the second adapter.

## 5. Conformance fixtures

Three records under one name, published to every configured store:

| Fixture | What it is | Expected outcome on every store |
|---|---|---|
| `good` | Signature verifies, digest matches the tree. | Resolved under `>=1.0.0 <2.0.0`. |
| `unsigned` | Signature member absent. | Refused, `urn:agentic:problem:record-unsigned`. |
| `stale-digest` | Signature verifies over a tree that was then edited. | Refused, `urn:agentic:problem:record-digest-mismatch`. |

`served_unverified` counts any record handed on when either check did not pass. It is the counter the
definition of done breaks on purpose, by downgrading the digest check to a warning.
