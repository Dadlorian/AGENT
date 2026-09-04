# improve — what the platform learned: spend per done, attempts, which template held

One improvement pass, run at a boundary. It works the metric furthest from its
target, puts every candidate revision through an evaluation gate that may say no,
and leaves the standing checkpoint in place when it does. What comes back is not
"it improved": it is how many attempts and how much spend each metric took, which
named template held under the gate and which did not, and — for the one revision
an outside agent offered — a decline that the caller cannot argue with.
`bash examples/improve/test.sh` is the visible check.

Every row below is cited to a knowledge-base id, a research id, or a file with a
verbatim quote, or it says **proposed** and gives its reasoning. File evidence is
cited as `REF-<path>#<anchor>`; one grep over this directory finds every id a row
carries, `provenance.json`'s `cites` list is checked against it in both
directions, and every quoted string is grepped back verbatim out of one of the
records its own line names — with a `REF-<path>#<anchor>` on a source file
narrowed to the definition the anchor names rather than the file it sits in
(`test.sh` sections 10 and 11). Nothing here names a product outside the
standards table.

## 1. Ideal

| What this example is held to | The future state, in the words of the record | Evidence |
|---|---|---|
| The area's own row | "what the platform learned: tokens per done, attempts, which template held", exercising "evaluation, improvement loop" | `REF-state/briefs/context-75.md#areas` |
| Litmus sections moved: none | The area's litmus column reads "(none; measured by tools/improvement_loop.py)". The questionnaire has no evaluation and no improvement-loop section, so this example moves no section and says so rather than claiming one; what it is measured against is the loop rule and the scorecard below | `REF-state/briefs/context-75.md#areas` |
| The loop rule | "The improvement loop works the metric furthest from its target and stops when every target holds or the owner says stop." | `T-t9-01` |
| When it runs | "Self-improvement runs at a ceremony, phase or structure boundary, never per iteration" | `REF-OWNER.md#2026-09-03-self-improvement` |
| What is improved | "the improvement loop improves the template, not the run" | `REF-OWNER.md#2026-09-04-decomposition` |
| Where the pass sits | "Work through every item with a self-improvement loop: at the end of each section a ceremony re-reviews the output, improves the skills that produced it, and the loop continues." | `T-t4-04` |
| What a change must prove | "Self-modifications should be accepted only on measured evidence, using two splits: a held-in split that checks the targeted weakness was resolved, and a held-out split the proposer never sees that checks nothing else regressed." | `X-compose-improvement-loop-006` |
| The stopping point | "a goal describes what success looks like, and a stop condition describes when to stop trying. A verifiable goal can be confirmed without relying on the agent's own judgment." | `X-compose-improvement-loop-005` |
| The gate that can say no | "A deterministic gate can be structurally green and mean nothing." | `F-a7-03` |
| The object this area is about | Evaluation — "the process judging a candidate", whose home is "the Judge and the hidden checks" — and its Result, "the typed verdict" | `REF-docs/reference/ontology.md#objects` |
| The ladder, not the word | A pass that reaches `completed` here has **execution success** and **instruction completion**, and it reports **task success** for each candidate as the gate's verdict — nothing above. Nothing was released, so there is no promotion success: "Promotion Success \| the accepted artifact entered the downstream lifecycle \| branch merged, released, deployed" is the rung this example does not reach, because promotion here moves a checkpoint and a metric value and writes no target file | `REF-docs/reference/ontology.md#success-ladder` |
| Not in this area | The criterion. A candidate names the gate it will be put through and never the rule it is judged by: "it has nowhere to carry the criterion, which is the evaluation capability's and is resolved inside the scorer." | `REF-harness/compose-improvement-loop/interface.py#GateSpec`; `F-b1-07` |

## 2. Standards

| Capability | Standard | Version | Version status | Why it holds this example | Evidence |
|---|---|---|---|---|---|
| Evaluation | none adopted | — | — | The case-set, replay and verdict shapes are this repository's design, and the capability says so in its own provenance: "none adopted; the case-set, replay and verdict shapes are this repository's design". This example adopts them whole rather than restating them | `REF-harness/evaluation/provenance.json#standard`; `F-b1-03` |
| Improvement loop | none adopted | — | — | Likewise: "none adopted; the loop shape (one iteration moves the metric furthest from its target, gated by an evaluation that can say no, checkpointed each fire) is this repository's design". The composition this example writes is the caller's side of that shape and adds no seventh operation | `REF-harness/compose-improvement-loop/provenance.json#standard` |
| Evaluation (the corpus) | none found on file | — | — | The corpus shape a mature build uses is a versioned split of recorded and synthetic cases: "A 50/50 split between hand-curated production traces and synthetic data covers real distribution plus edge cases." The registered corpus every candidate here is gated over is three recorded and three synthetic cases | `X-cap-evaluation-002` |
| Evaluation (replay) | none found on file | — | — | "wherever a recorded operation appears it substitutes the stored result instead of executing it" — which is why gating a candidate costs no side effect, and why `executed_effects` is a number to be asserted zero rather than a setting | `X-cap-evaluation-005` |
| Document validation | JSON Schema 2020-12 | 2020-12 | unverified | All three documents a caller writes or points at — the entry envelope, the `payload.improve` declaration and the task specification — validate against published schemas with the reference example's one validator | `F-b3-09` |
| Errors | RFC 9457 problem details | RFC 9457 | unverified | Every refusal is built at the improvement-loop capability's one construction point against its closed registry, and a caller branches on `type` and `status`, never on the sentence | `F-b3-13`; `F-b4-07` |
| Correlation | none adopted | — | — | The run id and correlation id ride as explicit attributes on every record, because trace parentage does not survive the hops: "Correlation must ride on an explicit resource attribute set at dispatch." | `F-a7-02` |
| Why every version status is `unverified` | — | — | — | No specification page was fetched by this session or the ones before it; the repository's own status row records the condition | `REF-STATUS.md#row-14` |

## 3. The call

Four entries cover nearly every situation and all four enter through the same
shape (`T-t6-02` "Four entries cover nearly every situation: a human, an event, a
schedule (time), and an external system or agent. All four enter through the same
shape."). Each document validates against
`REF-examples/end-to-end/schemas/entry.schema.json` with that example's own
validator; `payload.improve` validates against `schemas/improve.schema.json` and
the task specification against `schemas/unit.schema.json`, with the *same*
validator. No client library from this repository is involved (`F-b1-05` "A
caller needs no client library we wrote.").

| Door | The one line a caller writes | The document behind it | What is different | What is identical |
|---|---|---|---|---|
| human (a shell or an IDE) | `python3 examples/improve/run.py --entry examples/improve/entries/human.json` | `entries/human.json` — `user:corey`, one direct hop, a ceremony boundary, the full ceiling | the whole pass runs in one process and every target holds: 5 iterations, one of them declined | one task specification, one envelope shape, one scorecard digest, one gate |
| event | `python3 examples/improve/run.py --entry examples/improve/entries/event.json` | `entries/event.json` — `service:ceremony-runner`, two hops, a structure boundary, the smaller ceiling an unattended fire is given | the ceiling stops it: 4 iterations, 2 of 3 targets held, `budget_ceiling`, and a typed escalation | the same specification, envelope shape, scorecard digest and gate |
| schedule | `python3 examples/improve/run.py --entry examples/improve/entries/schedule.json` | `entries/schedule.json` — `schedule:nightly-improvement-boundary`, acting on a user's behalf, a phase boundary | nobody is in the process: one iteration per fire, parked in between, resumed from the checkpoint by a process that has never seen the loop | the same specification, envelope shape, scorecard digest and gate |
| external (another agent) | `python3 examples/improve/run.py --entry examples/improve/entries/external.json` | `entries/external.json` — `agent:partner-eval-bot`, three hops, a partner-finding boundary, one offered revision, and two members nothing reads: `parent_correlation_id` and `depth: 1` | the partner's own revision is tried first for its metric and **declined**: its gate selected no case, so the report is inconclusive and the checkpoint does not move | the same specification, envelope shape, scorecard digest and gate |
| the specification behind all four | `intent.workflow_ref` → `units/improve-platform-scorecard.json` | the scorecard, the candidate revisions offered per metric, the loop's ceilings, and the promotion rule | nothing | one declaration, four doors |

Measured, not asserted: the four doors carry four actors, four run ids and four
correlation ids through one task specification, and every record of every door
carries the same unit digest and the same scorecard digest (`test.sh` section 1).

### What `payload.improve` declares, and where each field is read

| Field | Read at | What changes when it changes | Proved by |
|---|---|---|---|
| `boundary.kind` | `read_documents()`, deciding who may offer a revision, and in the loop id | both arms are refused 422 before anything is registered: a `partner-finding` boundary that names no revision, and a ceremony, phase or structure boundary that carries one | `test.sh` section 7, two differentials |
| `boundary.ref` | `loop_id_for()`, deriving the loop id | one boundary is one pass: re-firing the same boundary resumes that loop at the next iteration index, and a different `ref` opens a second loop that starts at index 0 | `test.sh` section 6, differential |
| `fire_mode` | `run_pass()`, choosing the loop driver | `in-one-process` closes the pass in one process; `one-iteration-per-fire` records one iteration and parks, and the next process resumes from the checkpoint. The same five iteration records, byte for byte, either way | `test.sh` section 5, differential |
| `revision_offered` | `scorecard_of()`, put ahead of the unit's own candidates for its metric | with it, the iteration that works `template_hold_rate` first authors `rev-xp-01` and the pass takes 6 iterations; without it, that iteration authors `rev-th-01` and the pass takes 5 | `test.sh` section 4, differential |
| `revision_offered.gate.case_filter` | the evaluation capability's `evaluate`, selecting cases | `none` executes 0 cases and the report is `inconclusive`, which declines exactly as `failed` does; removed, the same revision executes 6 cases, passes, and is promoted | `test.sh` section 4, differential |
| `promotion_authority`, `decision_rule` — **absent by design** | the schema, at admission | a caller that adds either is refused 422: a caller cannot pin, choose or soften the rule its own change is judged by | `test.sh` section 7 |

And the fields outside `payload.improve` that this example is equally obliged to read:

| Field | Read at | What changes when it changes | Proved by |
|---|---|---|---|
| `intent.workflow_ref` (envelope) | `read_documents()`, resolving the task specification | pointing it at a specification whose `attempts_per_done` scale is 1.0 rather than 3.0 makes that metric the furthest at iteration 0, so a different metric is worked first with no flag given | `test.sh` section 2, differential |
| `budget.ceiling_micros` (envelope) | `print_plan()` on a **first** fire, and `evaluate_exit()` after each iteration, at the value the loop was opened with | a ceiling below the plan floor refuses 402 with no case replayed and no loop opened; a ceiling of 1000000 stops the same pass at 4 iterations with 2 of 3 targets held where 3000000 runs it to `verdict_pass`. On a fire that *resumes* an open loop it reaches neither: the same 500000 that refuses a first fire lets a resumed pass run to `verdict_pass` and print `spent 1250000 of 500000 micros`. Gap G11 | `test.sh` sections 2 and 7, three differentials |
| `actor.delegation_chain` (envelope) | `Pass.__init__`, as the derived delegation depth on every record | the depth on the records is the chain's length less one — 0, 1, 1 and 2 across the four doors — and is never the declared `correlation.depth` | `test.sh` sections 1 and 8 |
| `scorecard.metrics[].scale` (unit) | the capability's `Scorecard.furthest()`, through `REF-harness/compose-improvement-loop/interface.py#Metric` | "the span the gap is divided by, so metrics in different units are comparable and `furthest` means something" — change it and the order the metrics are worked in changes | `test.sh` section 2, differential |
| `scorecard.metrics[].direction` (unit) | the capability's `Metric.distance` | flipping `template_hold_rate` to `down` puts it at distance 0, so it is never worked and the pass closes in 4 iterations rather than 5 | `test.sh` section 2, differential |
| `candidates[].gate.unit_version` (unit) | the evaluation capability's `evaluate` | `1.4.1-rc` fails the gate and is declined; the same candidate at `1.4.0` passes and is promoted, and the pass takes one iteration fewer | `test.sh` section 3, differential |
| `candidates[].value_if_promoted` (unit) | the capability's `run_iteration`, on a passing gate only | a value that reaches the target closes the metric in one iteration; the shipped value reaches it in two | `test.sh` section 2, differential |
| `candidates[].template` (unit) | `learned()`, grouping what held by the template it revised | rename the template `rev-mp-02` revises and the learned table names that template as the one that held, from the same records | `test.sh` section 9, differential |
| `loop.iteration_ceiling` (unit) | the capability's `evaluate_exit` | 8 closes by `verdict_pass`; 2 closes by `iteration_ceiling` with one target held and a typed escalation. The capability refuses a declaration with no ceiling at all, and this example's own schema refuses it first | `test.sh` section 2, differential |
| `loop.per_iteration_micros` (unit) | the plan, the ceiling check and every iteration record's `spend_micros` | halving it to 125000 halves the plan floor (750000 → 375000), every record's `spend_micros`, the learned table's micros and the closing `cost_micros`, over the same five iterations | `test.sh` section 9, differential |
| `promotion.authority` (unit) | `run_pass()`, choosing the decision rule | one legal value: a specification declaring any other is refused 422 before a case is replayed | `test.sh` section 7, differential |
| `promotion.rollback_to` (unit) | every iteration record, naming the state a rollback would restore | `previous_checkpoint` names the checkpoint standing when the iteration ran; `open_loop_checkpoint` names the one the pass opened at, and the two differ from iteration 1 onwards | `test.sh` section 8, differential |

## 4. What the user sees

| Surface | Content | Evidence |
|---|---|---|
| The plan table, before anything runs | Every metric with its direction, its value now, its target, its normalised distance and how many candidate revisions are offered for it; then the floor if every gate passes first time, the worst case at the iteration ceiling, and the ceiling itself. Printed at every fire, before a case is replayed | `F-b1-06` "Cost is knowable before commitment." and "Planning is a pure function and completes before execution begins." |
| The iteration table | One row per iteration: the metric worked and its distance before and after, the candidate revision authored, the template it revises, the gate's outcome, how many cases the gate executed, promoted or declined, the checkpoint in force after it, whether that checkpoint moved, and the state a rollback would restore | `T-t9-01`; `REF-harness/compose-improvement-loop/interface.py#IterationRecord` |
| The learned table | Per metric: attempts spent, micros spent, the candidate that held, the template that held, and the distance closed. Then per template: revisions gated, held, did not hold. Then the totals — iterations, promoted, declined, micros over targets held. Every number is computed from the `iteration-recorded` rows of the receipt — the micros included, as the sum of the `spend_micros` those rows each carry rather than a row count times the declared price — and `test.sh` recomputes all of them the same way, and checks the closing `cost_micros` against that same sum | proposed: this is the area's own answer to its row, "tokens per done, attempts, which template held", in the units this example actually has (micros, attempts, templates) |
| The closing line | Disposition, `terminated_by` and its class, iterations run, targets held out of total, spend against the ceiling, and the rollback state. Disposition is one of the four words the ontology fixes and there is no fifth | `REF-docs/reference/ontology.md#objects` |
| The receipt line | The path, the record count and the head digest of the hash chain, printed before the closing line so the promised last line of a command does not move when a record is added | `F-b2-06` "append-only across runs; the deduplication authority" |
| The receipt: `out/*.jsonl` | One hash-chained record per thing that happened — `pass-submitted`, `scorecard-registered`, `revision-offered`, `loop-opened`, `iteration-recorded`, `pass-parked`, `learned`, `refusal`, `pass-completed`, `pass-escalated`, `pass-failed` — the eleven kinds these runs write, asserted set for set against the ledgers themselves rather than counted by hand — each stamped with run id, correlation id, actor, derived delegation depth, entry kind, idempotency key and the boundary it ran at | `F-b4-03` "Every action names an actor, including delegated agent actors. Delegation chains are explicit"; `F-b2-06` |
| An escalation | Not a refusal of the request: the pass ran correctly and its disposition is escalate, so the escalation problem object is printed under the outcome and the exit code stays 0. A capped loop escalates `urn:agentic:problem:budget-exhausted` (402) or, at the iteration ceiling, the registered `deadline-exceeded` (504) carrying the proposed `iteration-ceiling-reached` suffix in its detail, because an unregistered type is never minted | `F-b4-07`; `REF-harness/compose-improvement-loop/interface.py#problem` |
| A refusal that ends the pass | `application/problem+json` on stdout and exit 2, before or instead of the work it refuses ("Refusal is deterministic and happens before execution, not after spend"). Three registered types over eight measured documents: `document-invalid` (422) for a malformed envelope, for a `payload.improve` carrying a member a caller may not declare, for a revision smuggled in at a boundary that may not offer one, for a partner finding that names no revision, for a task specification declaring a promotion authority that is not the gate, and for one declaring no iteration ceiling; `budget-exhausted` (402) when the plan's floor exceeds the ceiling, with no case replayed and no loop opened; and `criterion-unresolvable` (422) when a metric has no candidate left to author — a problem the capability itself returned from `run_iteration`, re-raised unchanged, which ends the pass rather than becoming a fourth termination reason | `F-b4-04`; `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| A refusal folded into the record | None. Every refusal this example produces ends the pass; a declined candidate is not a refusal but a decision, and it is recorded as one. That the two are different rows and are counted differently is the point | proposed: our reading of the run area's finding that a refusal ending the unit and a refusal folded into a record are two different rows |
| Per door, the lifecycle and what a caller may do | Three transitions, and they are record kinds rather than a state member: `pass-submitted` → `pass-completed`, `pass-escalated` or `pass-failed`, with `pass-parked` in between on a `one-iteration-per-fire` pass, which any later fire resumes. No record here carries a lifecycle *state*: the published five (`working` and `input-required` among them) are what a mature build names, and this area's own row does not ask for them — so the gap is said rather than dressed. A decision is applied once: the same envelope key on a closed pass is a `REPLAY:` line and zero new records | `X-litmus-b-003` "Tasks progress through a defined lifecycle including submitted, working, input-required, completed, and failed states."; `F-b4-08` "Every externally-triggered action is safe to replay" |
| What a caller never sees | The rubric bodies and the criterion. A case "carries a rubric handle and never a rubric body, so what is graded cannot travel into what is graded", and nothing in this directory can resolve one | `REF-harness/evaluation/call.py#corpus_cases`; `F-b1-07` "The grader is never visible to the graded." |

## 5. Composition

| Piece | What it is here | Built from | Evidence |
|---|---|---|---|
| bounded loop | the whole pass: iterations bounded by `loop.iteration_ceiling` read at the exit condition, and by the envelope's ceiling read at the same place | the capability's `evaluate_exit`, called from `run.py:run_pass()` | `T-t9-01`; `REF-harness/compose-improvement-loop/interface.py#LOOP_SPEC_SCHEMA` "iteration_ceiling is required: there is no unbounded variant to declare." |
| judge | the gate. One candidate, one versioned case set, one stored baseline, one three-valued verdict; the runner never scores anything and never sees a rubric | the evaluation capability's `evaluate`, reached through the loop's own `Gate` | `F-b2-05` "pure function `(result, criterion) → verdict`"; `X-cap-evaluation-007` |
| sequence | per iteration: read the standing checkpoint → author the next candidate for the furthest metric → gate it → promote or decline → record | `run.py:run_pass()` | `X-compose-improvement-loop-004` "Skill evolution executes, diagnoses, revises, re-executes, and selects the first verifier-passing version under a bounded budget" |
| approval gate, parallel, agent call | none. This area gates changes against a corpus; it asks no person, fans out over nothing, and calls no model. Using an operator it did not need would be demonstrating the operator rather than the area | — | `F-part-c-09` |
| the one selection rule | which metric an iteration works is not a choice this example makes: "One rule: the largest normalised distance, ties broken by metric id so two drivers cannot disagree." | the capability's `Scorecard.furthest()` | `REF-harness/compose-improvement-loop/interface.py#Scorecard` |
| the one promotion rule | a metric moves only on a passing gate: "value_if_promoted is what the metric reads if - and only if - the gate passes; nothing here can move a metric on its own." An inconclusive gate is not a softer failure — "both leave the previous checkpoint in place" | the capability's `promote_on_pass`, chosen from `promotion.authority` | `REF-harness/compose-improvement-loop/interface.py#CandidateChange`; `REF-harness/compose-improvement-loop/interface.py#promote_on_pass` |
| the rollback state | every iteration record names the checkpoint a rollback would restore, and a declined iteration leaves the standing one in force. Nothing here performs a rollback: the capability publishes no restore operation. See gap G4 | `run.py:run_pass()` | proposed: naming the state on the record is this example's own addition; the gap says what is missing |
| reuse, not copy | the entry schema, the schema validator and the hash-chained ledger come from `REF-examples/end-to-end/run.py#validate,Ledger`; the harness loader comes from `examples/run/harnesses.py`, extended rather than copied; the loop and the gate are called through their interfaces and no case set, rubric, verdict, baseline or loop rule is re-stated here | `harnesses.py`, `run.py` | `F-b1-02` "The core imports interfaces, never implementations."; `T-t7-02` "Every harness call goes through the capability interface, and the component sits behind an adapter." |

### Adapters (the only place a product may be named — and none is named here)

| Capability | Adapter used here | Selected by | The second adapter, its execution model, and where it is proved |
|---|---|---|---|
| Improvement loop | `harness/compose-improvement-loop/adapters/dryrun.py` — the whole loop held in one process, checkpoints in memory, nothing surviving it | `payload.improve.fire_mode: in-one-process` | `adapters/second.py` — one iteration per fire: no process between iterations, a file per checkpoint, and a fresh binding that resumes a loop it has never seen. **Proved here**: `test.sh` section 5 runs one document both ways and asserts the five iteration records are byte-identical while the two execution models differ on all three declared axes |
| Evaluation | `harness/evaluation/adapters/dryrun.py` — replay in process, the recorded runs held in memory, a verdict carrier present | `--gate dryrun\|second`, or `GATE=` | `adapters/second.py` — no server and no collector: cases, records, baselines and reports are files and a verdict is an assertion. **Proved here**: `test.sh` section 5 runs the human door on both and asserts the same five iteration records, the same `learned` record and the same closing record — outcome, `terminated_by`, iterations, targets held, cost and final checkpoint — across three differing axes |
| Errors | the improvement-loop capability's own closed registry, rendered through the shared construction point | — | — (one construction point; there is no second place a failure body is built) |

Both swaps are run here rather than asserted, which is the rule the repository
holds every section to (`T-t9-06` "Swaps proven: every harness section executes
one adapter swap with the conformance run before and after."). The live adapter of
each capability exists and is deliberately not loaded here:
`harnesses.py` offers `dryrun` and `second` only, so no live credential, live
endpoint or vendor client is reachable from this directory, and the call shape is
the one the live adapter takes (`F-b1-04` "Swappability is a tested property, not
an intention.").

### Run steps

`test.sh` clears `out/` before it starts and gives every run its own `--ledger`
name; the steps below do the same, and for the same reason — the receipt is the
idempotency authority, so two passes that share one ledger name are one pass and
the second is a replay (two receipts of the same *basename* in different
directories are two passes, and are measured being two in `test.sh` section 6).
Run them in order, from the repository root. Steps 4 and 5 are the first two of
the five fires the schedule boundary takes: each records one iteration and parks,
and the fifth prints a `completed:` line — repeat step 5 three more times to see
it. Each line's promised last line is executed as printed and diffed against real
stdout, and each label is held to the verb its own last line uses, by `test.sh`
section 12.

| # | Step | Command | Its last line |
|---|---|---|---|
| 1 | the visible check | `bash examples/improve/test.sh` | `passed 88, failed 0` |
| 2 | a person, at a ceremony boundary: the pass completes | `python3 examples/improve/run.py --entry examples/improve/entries/human.json --ledger examples/improve/out/run-human.jsonl` | `completed: disposition accept, terminated_by verdict_pass (stop), 5 iterations, targets held 3/3, spent 1250000 of 3000000 micros, rollback state ck-86bf244b1045` |
| 3 | an unattended fire, under a smaller ceiling: it escalates | `python3 examples/improve/run.py --entry examples/improve/entries/event.json --ledger examples/improve/out/run-event.jsonl` | `escalated: disposition escalate, terminated_by budget_ceiling (cap), 4 iterations, targets held 2/3, spent 1000000 of 1000000 micros, rollback state ck-92d92499549f` |
| 4 | nobody in the process: one iteration, then park | `python3 examples/improve/run.py --entry examples/improve/entries/schedule.json --ledger examples/improve/out/run-schedule.jsonl` | `parked: iteration 0 of il-ae83f41269fd recorded; the next fire resumes from checkpoint ck-21d89405ad88` |
| 5 | the second fire of that boundary: one more iteration, and it parks again | `python3 examples/improve/run.py --entry examples/improve/entries/schedule.json --ledger examples/improve/out/run-schedule.jsonl` | `parked: iteration 1 of il-ae83f41269fd recorded; the next fire resumes from checkpoint ck-5130a6a6754f` |
| 6 | a partner's revision, gated and declined; the pass completes | `python3 examples/improve/run.py --entry examples/improve/entries/external.json --ledger examples/improve/out/run-external.jsonl` | `completed: disposition accept, terminated_by verdict_pass (stop), 6 iterations, targets held 3/3, spent 1500000 of 3000000 micros, rollback state ck-b425716c8b88` |
| 7 | the same pass, the second evaluation adapter: it completes identically | `python3 examples/improve/run.py --entry examples/improve/entries/human.json --gate second --ledger examples/improve/out/run-gate2.jsonl` | `completed: disposition accept, terminated_by verdict_pass (stop), 5 iterations, targets held 3/3, spent 1250000 of 3000000 micros, rollback state ck-86bf244b1045` |
| 8 | the deliberate breakage: a gate that cannot say no, and the pass completes an iteration early | `python3 examples/improve/run.py --entry examples/improve/entries/human.json --promote-regardless --ledger examples/improve/out/run-break.jsonl` | `completed: disposition accept, terminated_by verdict_pass (stop), 4 iterations, targets held 3/3, spent 1000000 of 3000000 micros, rollback state ck-4e53b8220174` |
| 9 | re-fire a closed pass | `python3 examples/improve/run.py --entry examples/improve/entries/human.json --ledger examples/improve/out/run-human.jsonl` | `REPLAY: improve-human-ceremony-75-run-review already closed as pass-completed at seq 9; 0 records appended` |
| 10 | read the receipt step 2 wrote | `python3 examples/improve/run.py --verify-ledger --ledger examples/improve/out/run-human.jsonl` | `chain verifies: 10 records, head sha256:1f1de6252631c218ae641329f3bba41a2ea084ff88e0a7947d8520c28c43e1ee` |

A deciding check for this example itself is held out and is **not** in this
directory; `test.sh` is the visible surface only (`X-unit-design-023` "most tasks
provide visible feedback surface for agent use during development while reserving
stricter hidden checks for final scoring"; `F-b1-07`).

## 6. Extension points

| Where a builder adds | Without touching | How | Proved by a differential run |
|---|---|---|---|
| A different scorecard | `run.py`, the entry documents, either schema | write a task specification with its own metrics, targets, scales and candidate revisions, and point `intent.workflow_ref` at it | `test.sh` section 2: the same door on a specification whose `attempts_per_done` scale is 1.0 works that metric at iteration 0 where the shipped scale of 3.0 works `micros_per_done`, with no flag given and no branch in the runner |
| A different candidate revision | `run.py` | append it to the metric's list; attempt *n* for a metric authors the *n*th candidate offered for it | `test.sh` section 3: the same specification with `rev-mp-01` pinned at `1.4.0` instead of `1.4.1-rc` promotes at iteration 0 and closes the pass in 4 iterations rather than 5 |
| A revision offered from outside | `run.py`, the task specification | submit it in `payload.improve.revision_offered` at a `partner-finding` boundary; it is tried first for its metric and gated identically | `test.sh` section 4: the external door with the revision takes 6 iterations and declines `rev-xp-01` on 0 cases executed; the same document with the revision removed and its boundary changed to `ceremony` - a partner-finding boundary must name one - takes 5 and never authors it |
| A different loop bound | `run.py` | change `loop.iteration_ceiling` | `test.sh` section 2: 8 closes by `verdict_pass` with 3/3 held; 2 closes by `iteration_ceiling` with 1/3 held and a typed escalation, from the same scorecard |
| A different ceiling, **on the fire that opens the loop** | `run.py`, the task specification | change `budget.ceiling_micros` on the envelope; the plan prices the pass against it before anything runs, and the exit condition reads the value the loop was opened with after every iteration. A later fire of an open loop declares a ceiling that reaches neither — gap G11 | `test.sh` sections 2 and 7: 3000000 runs to `verdict_pass`, 1000000 stops at 4 iterations by `budget_ceiling`, 500000 is refused 402 before a case is replayed on a first fire, and the same 500000 on resumed fires closes the pass at 1250000 micros with no refusal |
| A different fire mode | `run.py`, the task specification | declare `one-iteration-per-fire` and let a scheduler fire it; the loop resumes from its checkpoint in a process that has never seen it | `test.sh` section 5: one document both ways gives 1 process against 5, and the same five iteration records byte for byte |
| A different evaluation adapter | `run.py`, the documents | set `--gate`/`GATE=`; the gate, the corpus, the baseline and the verdict rules are the capability's | `test.sh` section 5: both adapters give the same iteration records, the same learned record and the same closing record, compared row for row, while differing on `execution_model`, `trajectory_source` and `emit_evaluation_result` |
| A different rollback target | `run.py` | change `promotion.rollback_to` | `test.sh` section 8: `previous_checkpoint` and `open_loop_checkpoint` name different states from iteration 1 onwards, on the same run |
| A different corpus | — | **not available.** The gate replays the evaluation harness's own registered corpus; nothing in this example's documents can name another case set that resolves. See gap G1 | — (this row is a gap, not an extension point) |
| Promoting into a registry | — | **not available.** A promotion here moves a checkpoint and a metric value and writes no target file; the capability has no operation that names one. See gap G3 | — (this row is a gap, not an extension point) |

### Carried and not consumed

| Field | Where | Why it is here anyway | Research query |
|---|---|---|---|
| `correlation.depth` | the entry envelope | The caller declares a hop count and the platform derives its own: every record carries `len(actor.delegation_chain) - 1`, so the declared member reaches nothing. Measured rather than asserted — the external door run with `depth: 99` returns the same records, byte for byte, as the shipped document (`test.sh` section 8) | should a caller-declared depth bound anything at all, or is a hop count the platform derives from the chain the only one that may decide |
| `correlation.parent_correlation_id` on `entries/external.json` | the entry envelope | The partner's upstream correlation reaches this pass and becomes an attribute of nothing; this pass binds its own root | how does a correlation identifier minted by another organisation's platform join to one minted here — a second attribute, a span link, or a hop in the delegation chain |
| `envelope_version`, `budget.on_exceed` | the entry envelope | The shared entry schema fixes both as a `const`: one legal value each, so reading them could only confirm the constant | how does an envelope version stop being a constant — what admits a second version, and is mapping the older shape forward a validator's job or an intake adapter's |
| `budget.currency` | the entry envelope | Every price here is in micros and nothing converts between currencies, so the field records the unit of account and no decision reads it | at what boundary does a budget ceiling stop being a number and become a currency |
| `entry_id`, `occurred_at`, `intent.summary`, `payload.source_kind` | the entry envelope | Recorded on the receipt through the envelope and read by nothing: the pass is identified by its correlation id and its idempotency key, and its shape by the boundary | what is the smallest envelope a work-intake boundary can accept, and which of these members does an audit actually need |
| `unit_id`, `template`, `note` (unit) | the task specification | The three members that say *what is being improved* decide nothing. Measured: the human door against a specification renamed to `totally-different-id` / `template:something-else` with a different `note` writes ten records against ten, and exactly one of them moves — `pass-submitted`, in `unit_id`, `template` and `unit_digest` (`test.sh` section 8). The template the learned table reports as having held is `candidates[].template`, a different field: the one naming the composition this pass improves is a string on one record | what identifies a task specification across versions of one template — and what would have to read `template` for "the loop improves the template, not the run" to be measured here rather than named |
| `scorecard.metrics[].means` | the task specification | It is printed in the plan table so a reader knows what the metric counts, and no decision reads it. A sentence rather than a definition: nothing checks that the number was computed the way the sentence says | can a metric's definition be machine-checkable — a named measurement procedure the platform can re-run — rather than a sentence beside the number |
| `candidates[].rationale`, `candidates[].slot` | the task specification | Both travel onto the receipt and neither decides anything: the slot says which part of the template the revision changes, and nothing here applies a revision to a template at all. See gap G3 | what is the smallest machine-readable description of a change to a named template with slots, such that a platform can apply it, roll it back, and tell two revisions of one slot apart |
| `loop.on_cap` (unit) | the task specification | A `const` with one behaviour, and read: it is passed to the capability's own declaration, whose schema refuses `on_cap: "continue"` at `open_loop` with a 422 naming the member, and this example's schema refuses such a specification before that. It is in this table because one legal value means reading it can only confirm the constant | what does a second cap behaviour cost — is "stop and keep the checkpoint" a different loop, or one declaration away |
| `loop.loop_ref` (unit) | the task specification | Carried and consumed by nothing: it names the composition this pass is an instance of and reaches no code, no schema and no record. `LoopSpec` has five fields and none is a `loop_ref`; the capability's `LOOP_SPEC_SCHEMA` does not name it; changing it moves nothing but the specification's own digest (`test.sh` section 8) | should a composition reference be resolvable — a registry entry with a version — rather than a name a reader recognises |

### Gaps this example exposed

| # | Claim that is not supported here | Research query |
|---|---|---|
| G1 | The corpus is not this platform's own. Every candidate is gated over the evaluation harness's registered corpus of six release-review cases at two pinned versions of one fixture unit, so "which template held" is measured against that corpus and not against recorded runs of the templates named on the candidates. The metric names and starting values are fixtures too, chosen so one pass meets a failed, an inconclusive and four passing gates | what does a case set built from an agent platform's own recorded runs look like — how are traces selected, how is the recorded/synthetic split maintained as the platform changes, and what invalidates a stored baseline |
| G2 | Nothing is promoted to a baseline. The evaluation capability publishes `promote_baseline` and this example never calls it: a passing gate moves a checkpoint and a metric value, and the stored baseline the next pass compares against is the same one every time | when a candidate passes, what promotes the baseline and on whose authority — and how is a baseline promoted by a regression prevented from hiding the regression next time |
| G3 | Nothing is written to a template. `slot` and `rationale` describe a change to a named composition and no code here applies one; the capability has no operation that names a target file, which its own provenance records as the open gap rather than simulating it | what does applying and reverting a versioned revision to a named template with slots look like end to end — the diff format, the registry entry, and what the rollback restores |
| G4 | There is no rollback. Every iteration record names the state a rollback would restore and nothing restores it: the capability publishes `read_checkpoint` and no operation that resumes from an earlier one | what does a restore operation on an improvement loop look like — does it rewind the metric values, the promoted artefacts, or both, and what stops a restore from being taken as a new promotion |
| G5 | The held-in and held-out split is one corpus. The record this example is held to asks for two splits, one of which "the proposer never sees"; here every candidate is gated over the same six cases, and the only thing held out is this area's own deciding check | how is a proposer prevented from reading the held-out split in a platform where the proposer, the gate and the corpus all run in one system |
| G6 | An improvement pass is not itself evaluated. The learned table says what this pass cost and which template held; nothing compares it to the pass before it, and no record says whether the loop is getting better at improving | what is the metric for an improvement loop itself, and what does a regression in the loop rather than in the candidate look like in the record |
| G7 | The escalation has nowhere to go. A capped pass escalates a typed problem and the process exits 0; no person is asked, no queue receives it, and the next fire would re-open the same loop and continue | where does a capped improvement loop escalate to — a person, a wider ceiling authorised by someone, or a smaller scorecard — and who decides |
| G8 | Two closed registries disagree. `iteration-ceiling-reached` is not in the platform's registry, so a loop that runs out of iterations answers with the registered `deadline-exceeded` and carries the proposed suffix in its detail. Measured, not smoothed over | what governs adding a type to a closed problem-type registry, and how does a caller discover which suffixes a capability may return |
| G9 | Nothing here is a real loop over real work. Both drivers and both gate adapters run in process with no network, so "the improvement loop improves the template" is measured across two execution models and claimed against the repository's own ceremony loop, which the capability's provenance records as promoting by editing a target file with a session reviewer's judgment as the only authority | run one section of a real improvement loop through this interface and compare: what the gate said, what was promoted, and what the ledger holds afterwards |
| G11 | A resumed fire's declared ceiling reaches nothing. `evaluate_exit` reads the `LoopSpec` stored at `open_loop`, and the plan's 402 is inside the first-fire branch, so a later fire of an open loop can declare any ceiling: the schedule door resumed under 500000 closes at `verdict_pass` printing `spent 1250000 of 500000 micros`, refusing nothing. Measured in `test.sh` section 7, not smoothed over | what may a fire change about a loop it is resuming — the ceiling, the scorecard, the candidate list — and where is that re-priced, given that the loop's own record of what it was opened with is what stops it |
| G10 | The area has a visible check and no hidden one. The index expects a held-out check outside `examples/`; this author's brief permits touching only `examples/improve/`, so the area is, by the skill's own rule, incomplete rather than passing | where does an area's held-out check live, who writes it, and what does the index report for an area with a README and no hidden check |
