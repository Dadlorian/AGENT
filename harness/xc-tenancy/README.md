# Tenancy harness — the mandatory principal every unit of work carries

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/xc-tenancy/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/xc-tenancy/call.py` |
| 3. See a typed cross-tenant refusal, in the same run | (the call above already shows it — no flag needed) |
| 4. Swap the boundary | `ADAPTER=second python3 harness/xc-tenancy/call.py` |
| 5. Ask both enforcement points the same question | `ADAPTER=dryrun,second python3 harness/xc-tenancy/call.py` |
| 6. Prove the interface held | `python3 harness/xc-tenancy/conformance.py --adapter dryrun --adapter second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `ScopeRequest`, `ScopeAssignmentRecord`, `Problem`, and `TenancyAdapter` with `resolve_scope` (the entry gate) and `admit` (resolve, then perform write/read/recall/spend). Both are concrete, so no adapter can decline the entry check or reorder it |
| `adapters/dryrun.py` | Today's substrate: one shared keyspace, a principal column checked by one `!=` comparison per operation. No network |
| `adapters/live.py` | Reached at `TENANCY_BUDGET_URL`. Write/read/recall are refused as absent (PASS.md A6: no identity field anywhere in the system); spend reaches the per-group virtual-key budget cap PASS.md A4 records (F-a4-07) — the only measured tenancy-adjacent component on this host. Product name lives here |
| `adapters/second.py` | The second boundary: one store instance per principal, selected before any read or write, plus a routing index (key → owning principal, metadata only) so a cross-tenant request is refused by name rather than a bare not-found |
| `call.py` | The minimal call. 19 lines below the `>>> CALLER CODE` marker |
| `conformance.py` | The 9 cases every adapter passes, the definition-of-done counters, measured by observing corpus outcomes rather than adapter self-report |
| `test.sh` | The gate: conformance, the swap proof, a product-name scan, and one deliberate breakage |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |
| `plan-entry.json` | This harness's row, in the shape of an entry in `harness/plan.json`, for the orchestrator to merge |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `for adapter in bindings():` | One name or several, from `ADAPTER`. Configuration, not code |
| `for step, op, principal, payload in steps:` | Write under tenant A, read under A, spend under A, read across to tenant B, then a unit with no principal at all |
| `ask = envelope(op, "user:corey", principal, **payload)` | One entry envelope; the platform stamps correlation id, ceiling and idempotency key without being asked |
| `record, outcome = adapter.admit(ScopeRequest.from_dict(ask["payload"]))` | `resolve_scope` runs first, unconditionally; only then does the operation run |
| `except Problem as problem: report(problem)` | One handler for every failure, branched on `type`, never on prose |
| `show(rows)` | Binding, step, principal, outcome, and `scoping_decisions_agree` — true only if every binding asked reached the same kind of outcome at every step |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live`, `second`, or a comma-separated list to ask several the same five steps |
| `ENTRY_KIND` | `human` | Which of TARGET T6.2's four entries the demo's envelope claims to be from |
| `TENANCY_CLOCK` | unset | Fixes `written_at` on every `ScopeAssignmentRecord`, which is never an input to a scoping decision |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `TENANCY_STORE_URL` | no | Where a tenancy-scoped write/read/recall store would be reached. Unset today — none exists on this host, so write/read/recall return `adapter-unavailable` naming the absence |
| `TENANCY_BUDGET_URL` | for spend | The key-info endpoint of the per-group virtual-key budget component (LiteLLM today, F-a4-07) |
| `TENANCY_BUDGET_TOKEN` | for spend | The admin credential for that endpoint |
| `TENANCY_TIMEOUT_S` | no | Per-call timeout in seconds, default 30 |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 9/9 | Admission, the entry-refusal, scoped read/write/spend, cross-tenant refusal on read/recall/spend, and the closed vocabulary all hold with nothing reachable |
| 1 | `principals_covered=2 no_principal_admitted=0 cross_tenant_reads=0 cross_tenant_recalls=0 cross_tenant_spend=0` | The counters xc-tenancy-implement's definition of done names, measured per adapter from corpus outcomes, not self-reported |
| 1b | Caller code is 19 lines, under 40, names no adapter storage | One admission is one call. Measured by `harness/caller_lines.py`, the one method the harnesses share |
| 1b | One `call.py` run exits 2 and shows a write, an own-tenant read, a scoped spend, a refused cross-tenant read, and a refused no-principal unit | The five things `minimal_call` asks for, in one invocation |
| 2 | Conformance before (dryrun) and after (second), 9/9 each | The interface held across a swap of the enforcement mechanism |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | 3 named axes differ (locus of the boundary, failure mode, provisioning cost); `scoping_decisions_agree=true` over every step of the demo run on both bindings | The second adapter breaks a different assumption and still refuses the same things the first refuses |
| 3 | `product_hits=0` outside `adapters/live.py` | No product name leaks past the one file allowed to carry one |
| 4 | The shared-keyspace filter's three `!=` comparisons removed, in a copy, on `adapters/dryrun.py` only | The green run can fail: 9/9 falls to 6/9, `cross_tenant_reads`/`cross_tenant_recalls`/`cross_tenant_spend` rise from 0 to 1/5/1, and the untouched second adapter is still 9/9 — singling out one adapter, because its isolation is structural and a filter was never in its path to drop |
| 5 | `--live`: the same caller code against `TENANCY_BUDGET_URL` | Skipped with a message when the env var is unset. Nothing live has been measured here |

## The two adapters behind one interface

| Axis | `adapters/dryrun.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Locus of the tenant boundary | a principal column filtered at read time within one shared keyspace | a wholly separate store instance selected by principal before any read or write |
| Failure mode of a wrong or missing principal | returns another principal's rows if the filter is dropped | fails to resolve a store at all, returning nothing |
| Provisioning cost of a new principal | a new value in an existing column | a new store instance before its first write can succeed |
| What it cannot do | refuse a cross-tenant read structurally — the filter is the only thing standing between the read and the wrong data | answer a cross-tenant query at all, even an authorised platform-level audit, without a second read that unions every store |
| Swap procedure | `ADAPTER=dryrun` | `ADAPTER=second`; no code edit, same 9 cases, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:no-principal` | 422 | The actor carries no principal. Refused at `resolve_scope`, before any store, index or ledger is touched |
| `urn:agentic:problem:document-invalid` | 422 | The request carries a field outside the vocabulary — a bypass flag included — or names an unknown key or operation |
| `urn:agentic:problem:cross-tenant-denied` | 403 | A read, recall or spend named a key or a target principal that belongs to a different principal than the requesting actor. Never a redacted view, never a count |
| `urn:agentic:problem:budget-exceeded` | 403 | The named principal's own ceiling was exceeded. Only that principal's unit is terminated; every other principal's remaining ceiling is untouched |
| `urn:agentic:problem:adapter-unavailable` | 503 | The live binding's tenancy-scoped store is unconfigured, or the budget endpoint could not be reached |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A "tenant" field a caller supplies and the platform trusts | `principal` rides on the actor xc-identity-delegation already binds; `resolve_scope` is the only place it is read, and it is not in the request's own top-level vocabulary |
| A filter someone remembered to add at read time, with nothing to compare it against | `adapters/second.py` proves the alternative: isolation with no filter in its path at all, so the swap tests the boundary shape, not a database product |
| A cross-tenant refusal that leaks existence through a redacted view or a count | `_read` and `_recall` return the caller's own data or nothing; `cross-tenant-denied` never carries a `value` field, asserted in conformance case `_read_cross` |
| A budget ceiling that, once exceeded, stops the platform or another tenant | Every ledger — shared dict keyed by principal in `dryrun`, one instance per principal in `second` — is scoped to the principal named; conformance case `_spend_own` asserts one principal's spend never moves another's balance |
| A migration that refuses every unit the platform admits today, because no principal field exists yet | Out of scope for this harness (xc-tenancy-implement's own three-step shadow migration); this harness only proves the two enforcement points once a principal is present |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof, the product scan and the breakage | Measured by `test.sh`: 29 checks, 0 failures |
| Live mode against `TENANCY_BUDGET_URL` | Claimed. The key-info endpoint shape (`GET {url}/key/info?key=...` → `{"info": {"spend", "max_budget"}}`) is proposed, not fetched from a live document; no request from `adapters/live.py` has ever reached an endpoint from this environment |
| `adapters/live.py`'s write/read/recall | Absent by design, not a stub standing in for a real store: PASS.md A6 records no identity field anywhere in the system, and no fact names a tenant |
| `adapters/second.py` | A faithful in-process model of the database-per-tenant execution model, not a binding to a real per-tenant deployment. Its shape, its routing index and its swap procedure are real; no external store is linked in |
| The standard | "none adopted; the tenant boundary as a placement is this repo's design" — xc-tenancy cites T-t4-03 and F-b1-08 for the placement, F-a6-05/F-a3-06/F-a4-07 for the absence and the nearest measured analogues, and X-xc-tenancy-001 for the database-per-tenant pattern this pair realises |
