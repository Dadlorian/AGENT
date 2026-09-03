# Context for row 62 (Phase 4: composition — 10 compose skills + examples/end-to-end)

Step: source (state/briefs/source.md). Goal: proposed rows <=30% of a skill's rows (T-t9-02).
Rows counted the way tools/validate_skills.py `rows_of()` does: instructions + contract.{invariants,
operations,shapes,standards,not_exposed,best_practices} + top-level best_practices/open_questions/
adapters + purpose. Computed by walking every skill.json's `origin` fields.

Total: 343 rows, 197 proposed (57.4% share) across the 10 skills. No B6 in PASS.md; F- ids for
workflow/loop/approval/agent composition come from B1/B2/B3/B4/part-c and A7 (grepped by term).

## 1. Two crew parts of five

Five pairs (agent, approval, improvement-loop, loop, operators); splitting into two fives breaks
the improvement-loop pair across the boundary, same as row 61's core-planner split.

**Part 1 — agent + approval pairs, improvement-loop base (rows/proposed/share%)**
compose-agent 45/24/53.3, compose-agent-implement 26/10/38.5, compose-approval 39/19/48.7,
compose-approval-implement 28/9/32.1, compose-improvement-loop 41/21/51.2
(part total 179/83/46.4%; compose-improvement-loop-implement is in Part 2)

**Part 2 — improvement-loop tail, loop pair, operators pair**
compose-improvement-loop-implement 28/14/50.0, compose-loop 38/27/71.1,
compose-loop-implement 27/21/77.8, compose-operators 47/37/78.7,
compose-operators-implement 24/15/62.5
(part total 164/114/69.5%)

Highest-share, most levers needed: compose-operators (78.7%), compose-loop-implement (77.8%),
compose-loop (71.1%), compose-operators-implement (62.5%), compose-improvement-loop-implement (50.0%).

## 2. Knowledge-base records for composition

**F- ids (workflow/loop/approval/agent, grepped — no B6 section exists).**
F-b1-06 "Cost is knowable before commitment. Planning is a pure function"; F-b1-07 "The grader is
never visible to the graded" (agent sees outcome, never criterion); F-b1-08 cross-cutting
guarantees not optional, platform-applied; F-b4-01 "difference between a working system and a
production one... a caller cannot decline them"; F-b4-02 Budget (ceiling terminates the unit, not
the platform); F-b4-03 Identity (every action names an actor, delegation chains explicit);
F-b4-07 Errors typed, never parsed from prose; F-b4-08 Idempotency (externally-triggered action
safe to replay); F-b2-03 Planner pure fn; F-b2-05 Judge pure fn; F-b2-06 Ledger append-only dedup
authority; F-a7-03 a deterministic gate can be structurally green and mean nothing (9-stage
pipeline, every behavioural stage skipped); F-part-c-04 machine-checkable DoD plus the deliberate
breakage that proves it can fail.
**T- ids (T1/T2/T6 governing entries and composition).** T-t1-01/02/03 three entries (human/
agent/event); T-t2-01 "Composability hides the complexity"; T-t2-02 composability enhances one
aspect without touching the rest; T-t2-03 state/telemetry/cross-cutting apply across the whole
structure regardless of entry; T-t6-02 four entries (human/event/schedule/external), same shape;
T-t6-03 any entry can call complex workflows, agents, loops across the stack; T-t6-05 each agent
defined up front by what it's good at; T-t6-06 target >100 agents concurrent.
**D- decisions on operators/composition (kb/decisions.jsonl, kind build_step).** D-build_step-035
compose-workflow depends_on seam-dispatch/seam-state/core-planner/cap-durable-execution/
cap-work-intake, rejects "a specific orchestrator"; D-build_step-036 compose-loop depends_on
compose-workflow/core-judge/xc-budget, rejects a fixed context window; D-build_step-037
compose-approval depends_on compose-workflow/cap-work-intake/cap-scheduling/xc-idempotency-lease,
rejects the durable executor's signal feature; D-build_step-038 compose-agent depends_on
compose-loop/cap-agent-runtime/cap-tool-access/cap-capability-packaging/cap-isolation, rejects
any particular agent product. Gap: no D-build_step names compose-operators or
compose-improvement-loop directly — treat as a research gap, not an invented decision.
**A-standard ids for A2A and AG-UI.** A-standard-a2a-messaging-agent-to-agent-task-protocol
(governs work-intake, human-interaction, capability-registry, dispatch); A-standard-ag-ui-
agent-to-user-interaction-events (governs human-interaction, telemetry).

## 3. Sibling ownership map (composes_with.builds_on, cap-/core-/seam-/xc- only)

compose-agent → cap-agent-runtime, cap-tool-access, cap-capability-packaging, cap-isolation,
core-judge, xc-budget (via compose-loop). compose-agent-implement → same as compose-agent.
compose-approval → cap-work-intake, cap-scheduling, cap-human-interaction, xc-idempotency-lease.
compose-approval-implement → same. compose-improvement-loop → core-judge, cap-evaluation,
cap-capability-registry, compose-loop. compose-improvement-loop-implement → same plus
cap-evaluation-implement. compose-loop → core-planner, core-judge, core-ledger, xc-budget,
seam-dispatch. compose-loop-implement → same. compose-operators → seam-dispatch, core-planner,
core-judge, cap-work-intake, xc-compensation, cap-durable-execution. compose-operators-implement
→ same.

## 4. Harness per compose skill for the measure step (harness/plan.json owner_skill/co_skills)

- workflow (owner cap-durable-execution-implement) serves compose-loop-implement,
  compose-approval-implement
- linked (owner cap-consumption) serves compose-agent-implement
- human-interaction (owner cap-human-interaction-implement) also serves compose-approval-implement
- evaluation (owner cap-evaluation-implement) serves compose-improvement-loop-implement
- xc-compensation (owner xc-compensation-implement) serves compose-operators

No harness names: compose-agent, compose-approval, compose-improvement-loop, compose-loop,
compose-operators-implement (one unserved base/implement skill from every pair but operators,
where the implement side is unserved instead).
Candidate harness for compose-operators from examples/end-to-end/test.sh's check lines: same
workflow document driven through all four entries; agent registry + workflow schema validation;
approval step's return_with_notes/return_to_step_id conditional requirement enforced (not just
described); ledger chain verifies and a tampered ledger is detected (exit 2); idempotent replay
is a no-op (same line count); budget enforcement breaks deliberately (ceiling below plan floor,
ceiling exhausted mid-loop, both exit 2); malformed envelope rejected (exit 2); final chain still
verifies.

## 5. Top three restatement warnings today (python3 tools/validate_skills.py, compose- skills,
grouped by the row's first cited source id, 27 restatement rows total across the 10 skills)

1. T-t4-04 — 7 rows (mostly in compose-improvement-loop). Gist: work every item through a
   self-improvement loop — ceremony re-reviews, improves skills, loop continues.
2. F-b1-07 — 6 rows. Gist: the grader is never visible to the graded; an agent sees its outcome,
   never the criterion it is judged against.
3. F-a7-02 — 3 rows. Gist: W3C trace context does not survive the agent boundary; correlation
   must ride on an explicit resource attribute set at dispatch.

## 6. Exact commands (copied from state/briefs/source.md)

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
