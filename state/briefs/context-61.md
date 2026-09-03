# Context for row 61 (Phase 3: core, seams, cross-cutting — 36 skills)

Step: source (state/briefs/source.md). Goal: proposed rows <=30% of a skill's rows (T-t9-02).
Rows counted the way tools/validate_skills.py `rows_of()` does: instructions + contract.{invariants,
operations,shapes,standards,not_exposed,best_practices} + top-level best_practices/open_questions/
adapters + purpose. Computed by walking every skill.json's `origin` fields.

Total: 1229 rows, 393 proposed (32.0% share) across the 36 skills.

## 1. Four crew parts of nine

Base skills only pair 1:1 with an `-implement` sibling; 9 is odd, so splitting 36 into four
equal nines breaks exactly two pairs (core-planner and xc-identity-delegation) across a part
boundary — flagged below, no other split needed.

**Part A — core, five components (rows/proposed/share%)**
core-document 43/15/34.9, core-document-implement 30/8/26.7, core-graph 42/17/40.5,
core-graph-implement 29/8/27.6, core-judge 42/12/28.6, core-judge-implement 31/5/16.1,
core-ledger 40/11/27.5, core-ledger-implement 32/9/28.1, core-planner 43/12/27.9
(part total 332/97/29.2%; core-planner-implement is in Part B)

**Part B — core tail + both seams + 2 xc pairs**
core-planner-implement 29/9/31.0, seam-dispatch 50/13/26.0, seam-dispatch-implement 25/0/0.0,
seam-state 49/13/26.5, seam-state-implement 27/5/18.5, xc-audit-trail 40/13/32.5,
xc-audit-trail-implement 25/9/36.0, xc-budget 38/17/44.7, xc-budget-implement 25/8/32.0
(part total 308/87/28.2%)

**Part C — 4.5 xc pairs (compensation, correlation, enforcement-chain, idempotency-lease, identity-delegation base)**
xc-compensation 42/14/33.3, xc-compensation-implement 28/12/42.9, xc-correlation 36/10/27.8,
xc-correlation-implement 26/10/38.5, xc-enforcement-chain 40/15/37.5,
xc-enforcement-chain-implement 27/8/29.6, xc-idempotency-lease 40/14/35.0,
xc-idempotency-lease-implement 29/10/34.5, xc-identity-delegation 39/14/35.9
(part total 307/107/34.9%; xc-identity-delegation-implement is in Part D)

**Part D — 4.5 xc pairs (identity-delegation-implement, policy-gate, provenance-chain, tenancy, typed-errors)**
xc-identity-delegation-implement 26/8/30.8, xc-policy-gate 36/19/52.8,
xc-policy-gate-implement 27/8/29.6, xc-provenance-chain 37/14/37.8,
xc-provenance-chain-implement 25/11/44.0, xc-tenancy 37/10/27.0, xc-tenancy-implement 26/7/26.9,
xc-typed-errors 38/13/34.2, xc-typed-errors-implement 30/12/40.0
(part total 282/102/36.2%)

Highest-share skills needing the most levers: xc-policy-gate (52.8%), xc-budget (44.7%),
xc-provenance-chain-implement (44.0%), xc-compensation-implement (42.9%), core-graph (40.5%).

## 2. Knowledge-base records per layer

**Core components (B2, F-b2-01..07).** F-b2-01 five components/zero outward deps; F-b2-02
Document (data: declared intent, DoD, steps); F-b2-03 Planner (pure fn document→plan+cost);
F-b2-04 Graph (typed nodes/edges); F-b2-05 Judge (pure fn (result,criterion)→verdict); F-b2-06
Ledger (append-only, dedup authority); F-b2-07 "entire owned surface, everything else is an adapter."
Governing T-: T-t1-01/02/03 (three entries: human/agent/event), T-t2-02 (composability),
T-t2-03 (state/telemetry/cross-cutting apply everywhere), T-t3-01/02 (simple, not daunting),
T-t6-02 (four entries: human/event/schedule/external), T-t6-05 (agents defined by what they're
good at), T-t6-06 (target >100 agents concurrent).

**Seams (B5, F-b5-01..06).** F-b5-01 "two boundaries have no standard to adopt... only places
original design effort is warranted"; F-b5-02/03 Dispatch (one unit executes, returns one
result; today three implementations, no contract); F-b5-04/05 State (graph+ledger persist;
today a hash-chained JSONL, chain is the valuable idea); F-b5-06 everything else in B3 is
someone else's published decision. Governing T-: same T-t1-01..03, t2-02/03, t3-01, t5-02
(1-3-1 on a problem), t6-02.
Decisions (kb/decisions.jsonl, field `seam`): Dispatch = D-design-001 request_shape, -002
result_shape (A2A state machine, unverified), -003 cancellation (request not kill), -004
timeout_budget (two independent ceilings), -005 partial_result (durable-before-terminal),
-006 failure (RFC 9457). State = D-design-007 write_model (one log of facts, graph+ledger are
folds), -008 concurrency (partition by run_id, fencing lease), -009 integrity (chain +
Merkle proofs), -010 retention (three classes: chain/body/payload), -011 query_surface.

**Cross-cutting concerns (B4, F-b4-01..08).** F-b4-01 "difference between a working system and
a production one... applies to everything, not requested"; F-b4-02 Budget (ceiling per unit,
exceeding terminates the unit not the platform); F-b4-03 Identity (every action names an
actor, delegation chains); F-b4-04 Policy (deterministic refusal, before execution); F-b4-05
Provenance (every artifact attributable to code+inputs+actor); F-b4-06 Telemetry (correlation
on explicit attributes, not trace parentage); F-b4-07 Errors (typed, machine-readable, never
prose); F-b4-08 Idempotency (externally-triggered action safe to replay). Governing T-: same
core set plus T-t4-03 (PASS.md's list is a limited baseline; find and close gaps).
A-standard-* per concern (kb/architecture.jsonl, id+name; grep only, kb.py show does not
index this file): xc-provenance-chain & xc-audit-trail →
A-standard-in-toto-attestation-framework / the combined
A-standard-in-toto-statement-v1-in-a-dsse-envelope-with-slsa-predicates; xc-policy-gate &
xc-enforcement-chain → A-standard-rego-opa-decision-api; xc-typed-errors →
A-standard-rfc-9457-problem-details; xc-correlation → A-standard-otlp; xc-identity-delegation
→ A-standard-oauth-2-0-token-exchange-rfc-8693 and A-standard-workload-identity-spiffe-spire-shape;
xc-idempotency-lease & xc-compensation → A-standard-idempotency-key-header-convention.
Gap: xc-budget, xc-tenancy have no capability→standard edge in kb/edges.jsonl and no matching
A-standard-* record found — treat as a research gap, not an invented standard.

## 3. Sibling ownership map

xc- concern → cap- skill whose interface it places (from composes_with.builds_on, cap- entries):
audit-trail→cap-provenance(+cap-scheduling); budget→none found (builds on cap-errors,
cap-model-access only — gap); compensation→cap-durable-execution+cap-idempotency;
correlation→cap-telemetry; enforcement-chain→cap-policy(+cap-work-intake);
idempotency-lease→cap-idempotency+cap-state-persistence; identity-delegation→cap-identity;
policy-gate→cap-policy(+cap-errors); provenance-chain→cap-provenance; tenancy→cap-isolation
(+cap-identity, cap-state-persistence); typed-errors→cap-errors.

core- skill → capabilities it imports (composes_with.builds_on, cap- entries only):
core-document→cap-document-validation, cap-errors; core-graph→cap-errors;
core-judge→cap-errors; core-ledger→cap-errors; core-planner→none (pure function, no cap-
import). seam-dispatch→cap-isolation, cap-agent-runtime, cap-durable-execution, cap-errors
(plus every xc- listed above except audit-trail/compensation/enforcement-chain/tenancy).
seam-state→cap-state-persistence, cap-errors (plus xc-provenance-chain).

## 4. Top three quote collisions today (core-/seam-/xc- only)

Counted by grouping origin=sourced rows whose text matches the "already states / what X adds"
restatement marker without saying "proposed", by cited source id (78 such rows total across
these 36 skills):
1. F-a7-03 — 22 rows. Gist: a deterministic gate can be structurally green and mean nothing.
2. F-a7-04 — 18 rows. Gist: configuration written in the documented place was silently discarded.
3. F-a5-03 / F-a5-04 — 5 rows each (tie). Gists: task store is hash-chained JSONL dedup
   authority; evidence store is append-only JSONL naming script SHA-256 and tree hash.

## 5. Exact commands (copied from state/briefs/source.md)

- Render + validate one skill after any edit:
  `python3 tools/render_skill.py .claude/skills/<name> && python3 tools/validate_skills.py --only <name>`
  → must be zero errors, no new warnings under that skill's name.
- KB lookups: `python3 tools/kb.py show <id>` (F-, T-, E-, X- ids only — D- and A- ids are not
  indexed by `show` and must be grepped directly from kb/decisions.jsonl / kb/architecture.jsonl);
  `grep -i` over kb/facts.jsonl (F-), kb/target-facts.jsonl (T-), kb/reference-facts.jsonl (REF-),
  kb/research.jsonl (X-), kb/decisions.jsonl (D-), kb/architecture.jsonl (A-), kb/ledger.jsonl (L-).
- Ledger at the end of a step:
  `python3 tools/kb.py ledger '{"kind":"ceremony","status_row":<row>,"ceremony":"<label>","agent":"<model>","result":"<one line>","status":"measured"}'`
- Scope claim/release (captain-level): `python3 tools/scopes.py claim <label> <paths...>` /
  `python3 tools/scopes.py release <label>`.
