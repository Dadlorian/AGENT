---
name: xc-tenancy
description: The isolation guarantee applied across principals rather than across runs: every unit of work carries a mandatory principal, bound at the same enforcement-chain slot that already binds its actor, and verified at every shared choke point so that one principal's state, memory, budget, identity and telemetry can never be read, spent or exhausted by another's. Load it when more than one principal shares the platform, when deciding what a record, a memory item or a budget reservation must carry before it is scoped, when a store, a sandbox pool or a routing-class key is shared infrastructure and someone asks whether one caller can see or spend against another's share, when reviewing whether isolation is enforced structurally or only by a query filter someone remembered to add, or when a cross-tenant read, recall or spend needs a name for what refused it.
---

# xc-tenancy

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| PASS.md's B4 table of cross-cutting concerns has no row for tenancy, and no section of PASS.md names a principal boundary between units of work sharing the platform (research-gap): TARGET states that PASS.md's list is a limited baseline, and the obligation is to make up the gaps in it and solve them. This skill fixes the guarantee that follows once more than one principal shares the same substrate: a mandatory principal on every unit of work, applied by the platform at the same choke points that already apply identity, policy and budget, so that a caller cannot decline it by leaving a field blank any more than they can decline telemetry. | sourced | `T-t4-03`, `F-b1-08` "make up for the gaps, and solve it" |

## Entities

| Entity |
|---|
| `E-concern-identity` |
| `E-concern-budget` |
| `E-concern-policy` |
| `E-capability-identity` |
| `E-capability-isolation` |
| `E-capability-state-persistence` |
| `E-not-running-identity` |
| `E-sandbox-property-jail` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| bind_scope (proposed operation set; PASS.md states no calls for this concern, only that cross-cutting guarantees are applied by the platform and not requested) | the chain context xc-enforcement-chain's identity.resolve slot already produced for this unit, carrying the actor xc-identity-delegation bound at entry (proposed) | the same chain context with one additional required field, principal, resolved from that actor; a chain context whose actor resolves to no principal is the refusal of identity.resolve, not a unit that proceeds unscoped (proposed) | proposed | `F-b4-03`, `F-b4-01` |
| check_scope (proposed) | the requesting principal and the principal already stamped on the record, memory item, budget reservation or isolation admission being crossed (proposed) | passed only if the two principals are equal; otherwise the typed refusal of policy.decide, and for a read or a recall, nothing returned - not a redacted view, not a count that discloses the target exists (proposed) | proposed | `F-b4-04` |
| meter_scope (proposed) | the requesting principal and the unit's reservation at budget.reserve (proposed) | a ceiling checked against that principal's remaining budget in addition to the run's own; exceeding it terminates the unit under that principal, never another principal's remaining ceiling or the platform (proposed) | proposed | `F-b4-02` |

### Shapes (JSON Schema 2020-12)

**TenantScope (proposed summary shape; the full ScopedRecord schema and the complete worked entries are in references/usage.md)** (proposed; sources: `F-b4-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:tenancy:scope:0.1",
  "title": "TenantScope",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. The mandatory scope key. It is carried on the actor identity xc-identity-delegation already binds, never supplied as a separate caller-chosen field, and it is decided in exactly one place.",
  "required": [
    "principal",
    "resolved_at"
  ],
  "properties": {
    "principal": {
      "type": "string",
      "minLength": 1,
      "description": "The tenant boundary. Opaque to every consumer above this contract."
    },
    "resolved_at": {
      "enum": [
        "identity.resolve"
      ],
      "description": "Always the same enforcement-chain slot xc-enforcement-chain names; there is no second slot where a principal is decided."
    }
  }
}
```

**ScopedRecord (proposed; the mandatory field every record cap-state-persistence appends and every item cap-memory writes carries in addition to its own required fields)** (proposed; sources: `F-b3-17`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:tenancy:scoped-record:0.1",
  "title": "ScopedRecord",
  "type": "object",
  "additionalProperties": true,
  "description": "Proposed. A record or item with no principal is refused at write time; it is not appended and then filtered out at read time.",
  "required": [
    "principal"
  ],
  "properties": {
    "principal": {
      "type": "string",
      "minLength": 1
    }
  }
}
```

**ScopeByWayIn (proposed worked instances, one per TARGET T1 way in; the complete envelopes are in references/usage.md)** (proposed; sources: `T-t1-01`, `T-t1-02`, `T-t1-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:tenancy:entry:0.1",
  "title": "ScopeByWayIn",
  "type": "object",
  "description": "Proposed. The caller supplies nothing beyond the entry envelope cap-consumption already fixes; the principal rides on the actor the driving adapter stamped, and it is present at admission for all three ways in.",
  "examples": [
    {
      "entry": {
        "kind": "human",
        "actor": {
          "subject": "user:corey",
          "principal": "tenant-northwind"
        }
      },
      "chain": {
        "point": "admission",
        "slot": "identity.resolve",
        "principal": "tenant-northwind"
      }
    },
    {
      "entry": {
        "kind": "external",
        "actor": {
          "subject": "agent:partner-sre-bot",
          "principal": "tenant-acme"
        }
      },
      "chain": {
        "point": "admission",
        "slot": "identity.resolve",
        "principal": "tenant-acme"
      }
    },
    {
      "entry": {
        "kind": "event",
        "actor": {
          "subject": "service:alerting",
          "principal": "tenant-acme"
        }
      },
      "chain": {
        "point": "admission",
        "slot": "identity.resolve",
        "principal": "tenant-acme"
      }
    }
  ]
}
```

**worked refusal (proposed instance; the type is the registered policy-denied row of the closed registry in docs/decomposition.md section 2.1.6, and cap-errors owns the object)** (proposed; sources: `F-b4-04`, `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:tenancy:refusal:0.1",
  "title": "TenancyRefusalInstance",
  "description": "Proposed. What a caller receives when a read, a recall or a spend crosses a principal boundary: the point and the rule that refused it, never the other principal's record.",
  "allOf": [
    {
      "$ref": "urn:agentic:problem:0.1"
    }
  ],
  "examples": [
    {
      "type": "urn:agentic:problem:policy-denied",
      "title": "Cross-tenant access denied",
      "status": 403,
      "detail": "enforcement point call, slot policy.decide: the requested record belongs to a different principal than the requesting actor",
      "rule_id": "tenancy-scope",
      "retryable": false
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| agentic-stack states design rule 7 as a test: telemetry, policy, provenance and budget are applied by the platform, never requested by the caller (F-b1-08). Tenancy is the same test aimed at one more axis: a principal is bound by the platform at identity.resolve, never accepted as a field a caller supplies and asks the platform to trust. | sourced | `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| xc-identity-delegation already fixes where the actor is bound - at entry, by the driving adapter, stamped onto the envelope (F-b4-03). What tenancy adds: the principal travels as a property of that same actor and is resolved at the same slot, identity.resolve, rather than a second binding step, so there is exactly one place a principal can be wrong and it is the place an actor already is. | sourced | `F-b4-03` "Every action names an actor, including delegated agent actors" |
| Proposed: xc-enforcement-chain fixes six named slots at three named points. Tenancy attaches to three of them rather than adding a seventh: identity.resolve is where the principal is bound, policy.decide is where a cross-principal read, recall or write is refused, and budget.reserve is where a ceiling is drawn against the requesting principal's remaining budget and not only the run's. | proposed | `F-b4-01` |
| cap-isolation already states that a unit of work runs contained with declared resources and declared egress, governed by the OCI Runtime Spec (F-b3-02). What tenancy adds at the isolation boundary: a sandbox slot exhausted by one principal must not block another principal's admission - the axis xc-tenancy-implement's second adapter is chosen to break. | sourced | `F-b3-02` "OCI Runtime Spec" |
| cap-state-persistence already forwards the write model and the query surface to seam-state's design, with no standard to conform to (F-b3-17). What tenancy adds: every record carries a principal alongside whatever partition key seam-state already uses, so a read at a pinned head is narrowed to one principal's records as a property of the record, not a filter a caller remembers to add - no recall, no spend, no read crosses a principal. | sourced | `F-b3-17` "JSONL + hash chain" |
| xc-budget and, at the isolation admission slot, cap-isolation and xc-enforcement-chain already state that a unit of work carries a ceiling and exceeding it terminates that unit, not the platform (F-b4-02). What tenancy adds: budget.reserve draws against a ceiling scoped to the requesting principal as well as the run's, so one principal exhausting its quota terminates only that principal's units - the platform's remaining capacity and every other principal's remaining ceiling stay untouched, the same noisy-neighbour boundary the research on file places at the shared choke points. | sourced | `F-b4-02`, `X-end-to-end-033` "Exceeding it terminates the unit, not the platform" |
| cap-memory already states that every write and recall carries a scope dimension, principal among them, so cross-principal contamination is kept out of results by construction rather than by a filter someone remembered to add (X-cap-memory-002). What tenancy adds: principal is not one dimension a caller may omit in favour of another, it is the mandatory one - a recall naming no principal, or a different principal than the actor's, is refused before ranking runs. | sourced | `X-cap-memory-002` "Every search must include at least one of these dimensions in filters" |
| cap-identity and xc-identity-delegation already state that PASS.md A6 records no identity field anywhere in the system (F-a6-05); tenancy has even less: no fact in PASS.md names a tenant or a principal at all, so tenancy as such is absent from the substrate. The nearest measured analogues are the per-VM uid jail (F-a3-06) and the per-group scoped model-access virtual keys with hard budget caps (F-a4-07), and xc-tenancy-implement treats both as the starting point rather than as evidence that tenancy already runs. | sourced | `F-a6-05`, `F-a3-06`, `F-a4-07` "identity field anywhere in the system" |
| xc-enforcement-chain already wires the identical chain on all three of TARGET T1's ways in - a human, an agent, an internal or external event. What tenancy adds: the principal rides on the same actor whichever driving adapter stamped, so enhancing one aspect (adding a fourth scope dimension, moving the store, tightening a sandbox quota) leaves how a caller reaches it untouched. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "A human must be able to enter the system." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: no operation returns another principal's data as a redacted view, a filtered page, or a count. A cross-principal read, recall or admission returns nothing - the typed refusal, or an empty result - never a shape that discloses the target exists. | proposed | `F-b4-04` |
| agentic-stack already states that products belong in the adapter column only (F-part-c-09). The consequence here: which store, sandbox pool or key group implements the scope boundary is not part of the contract, so no caller and no policy rule can branch on whether isolation is namespace-based or a dedicated pool per principal. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| agentic-stack states design rule 6 (F-b1-07). Tenancy opens no new place for the grading criterion to leak: the principal rides on the same actor structure a unit's output-judging criterion is already kept off, and no shape in this contract adds a second field for it to travel on. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Bind the principal at identity.resolve only - the same enforcement-chain slot and the same admission point xc-identity-delegation already binds the actor at - and never add a second, tenancy-specific binding step. | xc-identity-delegation fixes the placement of the actor binding; a second binding step for the principal would give the same question two owners and let them drift apart under load. | sourced | `F-b4-03` "Every action names an actor, including delegated agent actors" |
| 2 | Make the principal mandatory and total: a unit whose actor resolves to no principal is refused at admission, before policy.decide or budget.reserve run - there is no unscoped-but-admitted state. | agentic-stack states cross-cutting guarantees are applied by the platform, not requested (F-b1-08); an optional principal is a caller-declinable one, which fails that test as directly as an optional budget ceiling would. | sourced | `F-b1-08` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| 3 | Scope every persisted record: extend cap-state-persistence's record and cap-memory's item with the mandatory ScopedRecord field above, enforced at write time, so an append or a write with no principal never reaches the store. | cap-state-persistence forwards its write model to seam-state's design (F-b3-17); adding the field at write time rather than filtering at read time is what keeps a read from ever having to trust that the filter was applied. | sourced | `F-b3-17` "JSONL + hash chain" |
| 4 | Scope every recall: require principal as cap-memory's mandatory scope dimension, and return an empty result - never an error that discloses the item exists - when a recall names no principal or a different one than the actor's. | cap-memory already keeps cross-principal contamination out of results by construction once a scope dimension is required in every search; tenancy makes principal the one dimension that cannot be substituted for another. | sourced | `X-cap-memory-002` "Every search must include at least one of these dimensions in filters" |
| 5 | Scope every budget reservation: at budget.reserve, draw against a ceiling keyed to the requesting principal in addition to the run's own ceiling, so exceeding one principal's quota terminates only that principal's units. | xc-budget, cap-isolation and xc-enforcement-chain already state a ceiling terminates the unit, not the platform; the research on file places noisy-neighbour risk exactly at the choke points every principal shares, which is where a per-principal ceiling has to attach. | sourced | `F-b4-02`, `X-end-to-end-033` "Exceeding it terminates the unit, not the platform" |
| 6 | Scope isolation admission: when a sandbox pool is shared infrastructure, tag each slot with the principal that holds it, so a principal that exhausts its own sandbox slots refuses only its own new admissions, never another principal's. | cap-isolation states a unit runs contained with declared resources; tenancy's consequence for that contract is that resource exhaustion is a property of one principal's declared share, not of the pool as a whole. | sourced | `F-b3-02` "OCI Runtime Spec" |
| 7 | Wire the identical scope check on all three of TARGET T1's ways in - a human, an agent, and an internal or external event - by replaying one corpus with at least two principals represented through each door and asserting the same zero cross-principal counts for all three. | xc-enforcement-chain already wires the identical chain on all three ways in; a guarantee wired only on the door someone remembered is declined by choosing another door, and replaying through all three while requiring more than one principal in the corpus is what keeps a single-tenant test from reporting a false zero. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "A human must be able to enter the system." |
| 8 | For usability, add nothing to the caller's side: a human, an agent and an event all reach this guarantee by submitting the entry envelope cap-consumption fixes, supply no principal field and no scope flag, and read back either the normal result - narrowed to their own principal by construction - or one urn:agentic:problem:policy-denied naming the enforcement-chain point and the rule_id that refused. | cap-consumption states the caller doctrine once; restating it here would give it a second owner. The principal already rides on the actor xc-identity-delegation stamps, so there is nothing tenancy-shaped for a caller to configure. | sourced | `T-t6-02`, `T-t3-01` "All four enter through the same shape." |
| 9 | Attest the guarantee by replaying a corpus at a pinned state head and counting cross-principal reads, recalls and spend directly, the way xc-enforcement-chain's attest_chain counts slots - never by reading the absence of an error. | agentic-stack states the structurally-green-gate finding: well-formedness checks are not correctness checks, and a gate whose behavioural stages all skipped proves nothing. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| 10 | Proposed: open references/usage.md when you need the full ScopedRecord schema, the three complete worked entries, or the worked refusal in full. The body of this skill is enough to judge whether a boundary is tenant-scoped without it. | Proposed: the complete envelopes exceed the progressive-disclosure budget for a skill body, and a reader deciding whether a choke point is scoped does not need them open. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the structurally-green-gate finding (F-a7-03). What it costs here: a corpus with only one principal represented can report every cross-principal count at zero and prove nothing, so require at least two principals covered in every report, the same discipline xc-enforcement-chain's attest_chain applies to its three ways in. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack states the silently-discarded-configuration finding (F-a7-04). What it adds here: prove a store or a sandbox pool is scoped by principal by watching a live cross-principal request actually refused, not by reading the migration that added the column. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| The research on file (X-xc-tenancy-004) states isolation must be enforced at token level, middleware level, policy level, database level and encryption level, with tenant context mandatory in every request path. Treat the enforcement-chain's named slots as that layering rather than inventing a parallel tenancy-specific stack. | sourced | `X-xc-tenancy-004` "Tenant context should be mandatory in every request path" |
| The research on file (X-xc-tenancy-006) separates decision from enforcement: a policy engine answers whether a principal has permission, and an enforcement layer applies that decision uniformly across every API, service and data layer. Tenancy is one more input into that same decision, not a second gate beside it. | sourced | `X-xc-tenancy-006` "decision-making is separated from enforcement" |
| The research on file (X-xc-tenancy-005) names the riskiest noisy-neighbour points as exactly the resources PASS.md's substrate already shares across everything running on it - compute and model access - which is why budget.reserve and the isolation admission slot are where a quota test is cheapest to write first. | sourced | `X-xc-tenancy-005` "Sharing the same resources may result in noisy neighbor effects" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool, built with the first enforcement point: `python3 tools/conformance/tenancy.py --corpus out/units.jsonl --principals tenant-northwind,tenant-acme --min-units 100 --report out/tenancy.json`. Reading a pinned state head, for every unit it asserts a principal was present before admission, and for every read, recall and budget draw the unit performed it asserts the target's own principal equalled the requesting actor's. It reports `units_checked`, `principals_covered`, `no_principal_admitted`, `cross_principal_reads`, `cross_principal_recalls`, and `cross_principal_spend`, and asserts `units_checked >= 100`, `principals_covered >= 2`, and `no_principal_admitted == cross_principal_reads == cross_principal_recalls == cross_principal_spend == 0`. |
| Expected | exit 0 and one summary line `units_checked=100 principals_covered=2 no_principal_admitted=0 cross_principal_reads=0 cross_principal_recalls=0 cross_principal_spend=0`. |
| Deliberate breakage | Submit one state read whose query names a record_id known to belong to a different principal than the requesting actor, everything else in the corpus unchanged. |
| Expected failure | exit 1 with `cross_principal_reads == 1` naming that record and both principals, while `no_principal_admitted`, `cross_principal_recalls` and `cross_principal_spend` stay 0 and `units_checked` stays at or above 100 - showing the corpus was still read and the other three counters still meant something. Claimed: no fact in PASS.md names a tenant or a principal, the tool does not exist, and this run has not been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a6-05` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `build-research-record`, `build-ceremony`, `cap-identity`, `cap-isolation`, `cap-state-persistence`, `xc-identity-delegation`, `xc-enforcement-chain`

Used by: `xc-tenancy-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Is a principal a claim carried on the actor cap-identity's delegation chain already verifies, or a wholly separate concern with its own store and its own verification - the same actor can act for different principals across different units, so who-acted and whose-account-it-acted-for may not be the same question even when the same identity is behind both. | 1-3-1 applied (TARGET T5): (a) treat principal as a claim verified the same way cap-identity verifies any other claim on the chain, needing no new verification path; (b) treat principal as a wholly separate concern with its own attestation, since an actor's chain proves who acted, not on whose behalf they were allowed to act, and conflating the two would let a valid chain stand in for a scope check it never performed; (c) leave the question open until the first enforcement point exists. Recommendation followed: (b), because cap-identity's own not_exposed section keeps prior actors out of the authorisation decision, and folding a scope decision into the identity chain would put exactly that decision back in. | Verify principal as a separate claim at identity.resolve, alongside the actor rather than nested inside its chain, until this is run and reconsidered. | `F-b4-03`, `T-t5-02` "Every action names an actor, including delegated agent actors" |
| cap-isolation's proposed second adapter compares namespace isolation to a dedicated sandbox pool per principal, while cap-state-persistence's natural second adapter compares row-level scoping to a store-per-tenant; are these the same axis proven twice, or two genuinely different swaps that both need running before this guarantee is trusted? | Count, once both pairs exist, how many refusals each swap catches that the other does not. If the sets are identical the isolation pair is redundant with the state pair for this guarantee's purposes; if they diverge, both are load-bearing because they break different assumptions at different choke points. | Treat both as load-bearing until xc-tenancy-implement's conformance run says otherwise, since one governs admission to a sandbox and the other governs a persisted record, and PASS.md draws them as separate B3 rows. | `F-b3-02`, `F-b3-17` "JSONL + hash chain" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-tenancy 2831cb4f, 2026-09-03 |
