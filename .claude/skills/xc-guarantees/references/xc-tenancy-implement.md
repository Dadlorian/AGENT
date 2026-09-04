---
name: "xc-tenancy-implement"
description: "How to make the mandatory-principal guarantee real on this stack from a starting point where tenancy as such does not exist: today's nearest measured substrate (a per-VM jail, per-group scoped budget keys, a single hash-chained log), a second adapter that stores each principal separately instead of filtering a shared store, the migration when no field exists to migrate from, where the scope attaches to the enforcement chain's slots, and a definition of done with a breakage the build owns. Load it when writing or reviewing the code that resolves, checks or meters a principal, when a shared store, key group or sandbox pool is about to grow a tenant column, when choosing what the second adapter should be, when a migration would otherwise refuse every unit the platform currently admits, or when a conformance run reports a cross-principal read on one adapter and not the other."
---

# xc-tenancy-implement (folded into `xc-guarantees`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the placement xc-tenancy fixes into something that runs here: a today adapter built from PASS.md A3's per-VM uid jail and A4's scoped budget keys, since PASS.md A6 records no identity field anywhere in the system and no fact anywhere names a tenant, a second adapter chosen because it stores each principal separately rather than filtering one shared store, and a migration that starts red because there is no field on this host to migrate from. | sourced | `F-a6-05`, `F-a3-06`, `F-a4-07` "No identity field anywhere in the system" |

## Entities

| Entity |
|---|
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-object-store` |
| `E-not-running-identity` |
| `E-capability-state-persistence` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:tenancy:pair-axes:0.1",
  "title": "TenancyPairAxes",
  "description": "Proposed. The axes on which the two adapters differ, stated as properties rather than as product names. The axis is where and how the tenant boundary is enforced, not which store technology is used underneath. measured stays false until the swap has been executed and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "locus_of_the_tenant_boundary",
        "today_value": "a principal column filtered at read time within one shared keyspace",
        "second_value": "a wholly separate store instance selected by principal before any read or write",
        "measured": false
      },
      {
        "axis": "failure_mode_of_a_wrong_or_missing_principal",
        "today_value": "returns another principal's rows if the filter is dropped or wrong",
        "second_value": "fails to resolve a store at all, returning nothing",
        "measured": false
      },
      {
        "axis": "provisioning_cost_of_a_new_principal",
        "today_value": "a new principal needs only a new value in an existing column",
        "second_value": "a new principal needs a new store instance created before its first write can succeed",
        "measured": false
      }
    ]
  ]
}
```

**ScopeAssignmentRecord (proposed; what one unit's principal resolution writes through the state seam, for the shadow-migration report to read back)** (proposed; sources: `F-a5-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:tenancy:scope-assignment:0.1",
  "title": "ScopeAssignmentRecord",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. One record per unit, appended rather than mutated, so the adapter a corpus check reads back is the adapter that actually resolved the unit and not the one the configuration selected.",
  "required": [
    "run_id",
    "unit_id",
    "principal",
    "adapter",
    "written_at"
  ],
  "properties": {
    "run_id": {
      "type": "string",
      "minLength": 1
    },
    "unit_id": {
      "type": "string",
      "format": "uuid"
    },
    "principal": {
      "type": "string",
      "minLength": 1
    },
    "adapter": {
      "type": "string",
      "description": "Read from the stamp the resolution produced, never from the configuration that selected it."
    },
    "written_at": {
      "type": "string"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two adapters differ on three of build-adapter-pair's axes - locus_of_the_tenant_boundary, failure_mode_of_a_wrong_or_missing_principal, and provisioning_cost_of_a_new_principal - recorded in the shape above. A second store that only relocated the same filter would agree with the first on all three, so swapping to it would test a database and not the boundary shape. | proposed | `F-b1-04` "Swappability is a tested property, not an intention." |
| build-adapter-pair and agentic-stack state design rule 1 (F-b1-02). Its consequence here: which adapter resolved a unit's store is configuration, and no core code, no workflow and no policy rule branches on it; the adapter appears in the conformance report, never in a field a caller can read and route on. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| There is no identity field anywhere in the system and no fact in PASS.md names a tenant, so the today adapter is written rather than replaced and every assertion in the definition of done below is red until it exists (F-a6-05; xc-tenancy owns the placement and records tenancy's absence from the substrate). | sourced | `F-a6-05` "No identity field anywhere in the system" |
| cap-state-persistence's own recorded row, which xc-tenancy also cites, names JSONL plus hash chain as today's adapter and an object store, a relational store or an event log as swap candidates for the whole capability (F-b3-17). This skill's pair answers a narrower question than that row does: not which store cap-state-persistence should use, but whether the store's tenant boundary is a filter over shared partitions or a partition of its own - so the two adapter tables can share entities without re-answering the same question. | sourced | `F-b3-17` "JSONL + hash chain" |
| The research on file names three multi-tenant database patterns - shared database with shared schema, shared database with separate schemas, and database per tenant (X-xc-tenancy-001). The two adapters below sit at the two ends of that range: a principal column on the shared log today, and database-per-tenant as the second. | sourced | `X-xc-tenancy-001` "Database per Tenant" |
| Principal is stamped beside the explicit resource attribute correlation uses at dispatch rather than inferred from it, so a scope-assignment record and a correlation record are written from the same call and can never name two different runs for one unit; correlation must ride on that explicit attribute because parentage did not survive the agent boundary (F-a7-02; agentic-stack and build-adapter-pair own that rule). | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| agentic-stack and build-definition-of-done state the structurally-green-gate finding (F-a7-03). What it costs here: a corpus replayed through two adapters can leave one of them with only a single principal represented and still report every cross-principal count at zero, so report principals_covered per adapter and fail when either is below two. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Apply build-evidence-record: every statement here about how an adapter behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test, and rewording a sentence never upgrades a label; proposed pointer, see that skill. | proposed | `F-a5-04` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the today adapter as the observed substrate, not an incumbent that already enforces tenancy: a principal column added to every record cap-state-persistence appends, filtered at read time, sitting beside a per-VM uid jail and per-group scoped budget keys that already run for unrelated reasons and carry no principal concept of their own. | PASS.md A6 records no identity field anywhere in the system and no fact names a tenant; the jail and the keys are the nearest measured analogues, not evidence that tenancy already runs, so the first adapter to exist is the one described here. | sourced | `F-a6-05`, `F-a3-06`, `F-a4-07` "No identity field anywhere in the system" |
| 2 | Proposed: build the second adapter on the database-per-tenant pattern - each principal's records resolve to a separate store instance selected before any append or read, so a missing or wrong principal fails to resolve a store at all rather than under-filtering one. | Proposed: this breaks the assumption behind the today adapter that isolation is a query filter someone remembered to add. It also fails differently - provisioning a new principal needs a new store instance, not a new value in a column - which is what makes the pair a test of the boundary shape rather than of a database product. | proposed | `X-xc-tenancy-001`, `F-b1-04` |
| 3 | Apply build-adapter-pair: record differs_in_execution_model from the shape above, leave measured false until the swap has actually run, and write each adapter's gaps down as gaps rather than as caveats; proposed pointer, see that skill. | differs_in_execution_model and the rule that measured stays false until the swap has run belong to build-adapter-pair; naming the axes here without restating that rule keeps one owner for it. | proposed | `F-b1-04` "Swappability is a tested property, not an intention." |
| 4 | Migrate in three steps from nothing: add principal as optional and stamp it wherever an adapter can, recording how often it could not; run the corpus check in shadow over that period and reconcile what it would have refused; then make principal required, refuse a write or a read with none, and keep the shadow report as the regression baseline. | There is no principal field anywhere in the system today, so making it required on day one would refuse every unit the platform currently accepts. The shadow period is where the paths that cannot yet establish a principal are found, before the refusal is live. | sourced | `F-a6-05`, `F-part-c-11` "No identity field anywhere in the system" |
| 5 | Wire the cross-cutting attachments at both adapters: stamp principal beside the run identifier on the same explicit attribute correlation already uses at dispatch, append one scope-assignment record per unit through the state seam, and hand the policy gate the resolved principal alongside the current actor. | Correlation must ride on an explicit resource attribute set at dispatch because parentage did not survive the agent boundary (F-a7-02; agentic-stack and build-adapter-pair own that rule); a principal that rode on inference instead of that same attribute would be unattributable for the same reason, and the policy gate cannot decide a cross-principal refusal it was never handed the principal for. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Read the adapter and the principal from the stamp or the refusal that actually came back, rather than the value the configuration selected, and report both per unit. | Settings written in the documented place had no runtime effect when measured on this host (F-a7-04; agentic-stack and build-evidence-record own the silently-discarded-configuration finding), and a scope believed enforced because it was configured is that failure with an audit trail attached. | sourced | `F-a7-04` "had no runtime effect" |
| 7 | Apply build-definition-of-done: run the definition of done below over both adapters and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating what every sibling -implement skill already states once. | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Expect the two adapters to disagree during the shadow step and treat the difference as the finding. build-adapter-pair states why a second adapter exists (F-b1-04); the gap it exposes here is concrete: the units the shared-store adapter can filter correctly and the ones it cannot are the ones nobody was actually scoping. | sourced | `F-b1-04` "Every interface ships with at least two adapters" |
| agentic-stack and build-definition-of-done state the structurally-green-gate finding (F-a7-03). What it costs here: a corpus with one principal represented can report cross_tenant_reads at zero and prove nothing; require principals_covered >= 2 per adapter, not only across the merged report. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| The research on file (X-xc-tenancy-003) places namespace and cgroup isolation at the containment layer, not the store layer. Do not re-decide cap-isolation's own namespace-versus-dedicated-pool question here: this pair is about cap-state-persistence's row, and xc-tenancy's own open question already tracks whether the isolation pair is a second load-bearing swap or the same axis proven twice. | sourced | `X-xc-tenancy-003` "Namespaces provide process isolation by creating separate views of system resources" |
| Apply build-evidence-record's naming rule to every claim in this skill about how an adapter behaves: claimed until the conformance run has actually produced the exact output recorded, and rewording a sentence never upgrades the label. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-hash-chain` | today | row-level, key-scoped tenancy on shared infrastructure. As xc-tenancy already notes, the nearest measured analogues PASS.md records are the per-VM uid jail, `0700` and owned by a per-VM uid with no passwd entry, verified live (F-a3-06), and the per-group scoped model-access virtual keys carrying a hard budget cap, verified to terminate spend rather than merely record it (F-a4-07), sitting beside the single hash-chained JSONL log every run's records fold into (F-b3-17). None of the three carries a tenant or a principal concept: the jail scopes a VM, the key scopes a routing class, the log partitions by run_id. Tenancy as such is absent - no field on any of the three names a tenant, and no query filters by one - so this adapter is what a principal column is added to, not an incumbent that already enforces one. | Cannot refuse a cross-tenant read today: nothing in the substrate carries a principal to check, so a caller who can name another run's record, another routing class's key, or another VM's jail path meets no scope check at all, only whichever isolation or budget boundary that resource already has for an unrelated reason. Once a principal column is added, it still cannot prevent isolation structurally - a dropped filter returns another principal's rows rather than failing to resolve anything. | Add principal as a required field in every appended record's canonical body and a required claim on every routing-class key stamp, so filtering by tenant becomes a check over the store's existing partition key rather than a second store. Select the adapter by configuration with no code edit between runs, replay the identical corpus through both, and require the merged report to show adapters_run == 2 with adapter read from the stamp rather than the configuration. | claimed | `F-a3-06`, `F-a4-07`, `F-b3-17` "JSONL + hash chain" |
| `E-swap-candidate-object-store` | second | database-per-tenant: each principal's records resolve to a separate store instance, selected by principal before any append or read, so isolation is structural rather than a filter over one shared store - the pattern the research on file names as database per tenant (X-xc-tenancy-001), realised on the same swap candidate cap-state-persistence's own B3 row already names for a different reason (F-b3-17). | Proposed: cannot answer a cross-tenant query at all, even an authorised platform-level audit, without a second read that unions every tenant's store; and cannot share one fenced writer per run_id across tenants the way the shared store does, because the store boundary is now per tenant as well as per run, so a writer's fencing lease has to be taken per tenant-and-run pair instead of per run alone. | Proposed: the axes that differ are locus_of_the_tenant_boundary (a filtered column versus a separate store instance), failure_mode_of_a_wrong_or_missing_principal (returns the wrong rows versus resolves no store) and provisioning_cost_of_a_new_principal (a new column value versus a new store instance). Select the store by principal at the same slot identity.resolve already resolves the actor at, before dispatch; replay the identical corpus through both adapters and assert the merged report shows adapters_run == 2, with cross_tenant_reads forced to zero structurally on this adapter and only by the added filter on the first. | claimed | `F-b3-17`, `X-xc-tenancy-001`, `F-b1-04` "Database per Tenant" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/xc-tenancy/test.sh && python3 harness/xc-tenancy/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 844f32b: exit 0; last lines:   adapter=database-per-tenant cases=9 passed=9 units_checked=11 principals_covered=2 no_principal_admitted=0 cross_tenant_reads=0 cross_tenant_recalls=0 cross_tenant_spend=0 \| conformance PASSED: 18/18 cases, 2 binding(s), adapters_run=2 |
| Deliberate breakage | In harness/xc-tenancy/adapters/dryrun.py, drop the principal filter on reads so every record is returned regardless of principal, run the criterion (the cross-tenant read is served instead of refused, conformance fails on the first adapter while the second stays 9 of 9, and the gate exits 1), then git checkout harness/xc-tenancy/adapters/dryrun.py. |
| Expected failure | Measured by tools/measure.py at 844f32b: exit 1; last lines:   ok   singling out one adapter: the other is still 9/9 \| passed 22, failed 7 |
| Status | measured |
| Evidence | `F-part-c-04`, `F-a6-05` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `xc-tenancy`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| This guarantee has no adapter or swap-candidate entity of its own, on top of the absence xc-tenancy already records for tenancy generally: both entities used above belong to cap-state-persistence's B3 row (F-b3-17, JSONL + hash chain today). Should the tenancy pair get its own entities instead of sharing that row's? | 1-3-1 applied (TARGET T5), the same way xc-identity-delegation-implement records its own entity gap. Options: (a) mint E-adapter-shared-keyspace-tenancy and E-swap-candidate-store-per-tenant, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) record the pair against cap-state-persistence's existing entities and state in each row which question that table answers, which is what this skill does; (c) leave the pair unentitied until a later wave, which would leave this guarantee with no tested swap at all. Recommendation followed: (b). The question closes when a ceremony rebuilds the knowledge base and the two entities exist. | Keep the pair on cap-state-persistence's existing entities, with the difference from that capability's own adapter table stated in both rows above so a reader is not sent to the wrong question. | `F-b3-17`, `T-t5-02` "JSONL + hash chain" |
| xc-tenancy's own open question asks whether cap-isolation's namespace-versus-dedicated-pool pair and this skill's store-per-tenant pair are the same axis proven twice or two genuinely different swaps. Does the isolation pair belong in this skill too, or stay entirely in a future cap-isolation-implement? | Run both pairs' conformance reports once they exist and compare the refusals each catches that the other does not, exactly as xc-tenancy's open question proposes at the guarantee level. | Leave the isolation pair to cap-isolation-implement. This skill's adapters answer only cap-state-persistence's row; naming a second pair here before cap-isolation-implement exists would answer a question that skill has not been written to ask yet. | `F-b3-02`, `T-t5-02` "OCI Runtime Spec" |
| The refusal both adapters raise for a cross-principal read, recall or spend is urn:agentic:problem:cross-tenant-denied, which has no row in the closed registry in docs/decomposition.md section 2.1.6 and is therefore pending registration: should the registry gain that row, or should a cross-principal refusal be carried as the registered policy-denied (403, a deterministic pre-execution refusal carrying rule_id)? | Proposed, and 1-3-1 applied (TARGET T5): the closed registry in docs/decomposition.md section 2.1.6 is extended only by adding a row and states that an unregistered type is a conformance failure, so the harness output recorded in the definition of done above states a type that registry does not yet carry. Options: (a) add a cross-tenant-denied row to section 2.1.6, which is the smallest edit and keeps the refusal readable as its own class; (b) carry it as policy-denied with a rule_id naming the principal boundary, which needs no registry edit but merges a tenancy refusal into the policy class; (c) leave it unregistered, which is the conformance failure the registry exists to prevent. Recommendation: (a), taken by the ceremony that owns docs/decomposition.md, since this skill's scope is the build and not the registry. | Until the row exists, read cross-tenant-denied as pending registration wherever this skill states it, and treat the registered policy-denied as the fallback type an adapter emits if it must answer today. | `F-b4-07`, `T-t5-02` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-tenancy-implement 2831cb4f, 2026-09-03 |
