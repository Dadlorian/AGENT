# run — what happens in the sandbox on my behalf; fifty of them at once

One unit of agent work, end to end: a contract hashed before the cell starts, a
contained cell admitted from a resource declaration, one attempt per turn with
both ceilings enforced outside it, one candidate sealed write-once, and the
deciding checks run afterwards in a cell forked from the seeded snapshot. Then
fifty of them at once. `bash examples/run/test.sh` is the visible check.

Every row below is cited to a knowledge-base id, a research id, or a file with
a verbatim quote, or it says **proposed** and gives its reasoning. Nothing here
names a product outside the adapters table.

## 1. Ideal

| Litmus section | The future state this example is held to | Evidence |
|---|---|---|
| `isolation` | "a unit of work runs isolated per the runtime specification, and the isolation request is expressed only as specification-shaped configuration — root filesystem and mount set, namespace and user mapping, resource limits, network posture … never as engine-specific flags"; "the exact set of things allowed to cross the boundary — files in, artifacts out, credentials, network egress — is declared per unit rather than inherited from the host" | `FILE:docs/litmus/questionnaire.json#isolation.future_state`; `F-b3-18` "a unit of work runs isolated, per the OCI Runtime Spec" |
| `agent-runtime` | "the unit of agent execution is one prompt turn closed by an explicit stop reason"; "Cancellation is a first-class contract, not a best-effort kill"; "A second adapter has no interactive client at all … which is what proves the interface never assumed a live editor" | `FILE:docs/litmus/questionnaire.json#agent-runtime.future_state`; `F-b5-02` "**Dispatch** — one unit of agent work executes and returns one result." |
| `tool-access` | "tool exposure is progressive: what enters a turn's context is selected by search or by declared toolset rather than by loading every definition"; "a deterministic policy decision taken per tool and per actor before the call" | `FILE:docs/litmus/questionnaire.json#tool-access.future_state`; `F-b4-04` "Refusal is deterministic and happens before execution, not after spend" |
| `model-access` | "the core imports a model-access capability … so no provider name appears above the boundary"; "Every call carries a ceiling that terminates the unit when exceeded, a named actor, a policy decision taken before the call" | `FILE:docs/litmus/questionnaire.json#model-access.future_state`; `F-a4-01` "Callers request a class, never a vendor. Prefix carries the contract." |
| `capability-packaging` | "Loading is tiered and the tiers are measured, not asserted: only name and description are resident, the body loads when the capability is triggered, and reference material loads only when the work reaches it, with the resident cost per package counted" | `FILE:docs/litmus/questionnaire.json#capability-packaging.future_state`; `X-unit-design-012` "the agent learns only the skill name, path, and description up front, then loads the full SKILL.md only when relevant" |
| `errors` | "every boundary in the platform … returns one problem object with the standard members and a type identifier drawn from a closed registry the platform publishes"; "The type identifier, never the status code and never the prose, is what a caller branches on" | `FILE:docs/litmus/questionnaire.json#errors.future_state`; `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| The unit itself | The contract is "immutable for the life of the unit", its digest "ledgered before the cell starts"; the visible checks "are the checks it will optimise against, which is exactly why they do not decide"; measure "runs in a fresh cell forked from the seeded snapshot, with the unit's sealed output mounted read-only and no egress"; the attempt ceiling parks a person rather than stopping silently | `FILE:docs/consumption/unit-design.md#mounts`, `#checks`, `#escalation` |
| The ladder, not the word | Success is reported on the ladder, never as one word: this example reaches **validation success** when the visible checks pass and **task success** only when every deciding check ran and passed | `FILE:docs/reference/ontology.md#success-is-a-ladder-never-one-word` "Validation Success \| the visible checks passed"; "Task Success \| the success criteria were met" |

## 2. Standards

| Capability | Standard | Version | Version status | Why it holds this example | Evidence |
|---|---|---|---|---|---|
| Isolation | OCI Runtime Spec | v1.3.0 | unverified | The declaration a caller writes carries a profile, an egress policy and a credential mode; a field describing a machine is refused at 422 | `F-b3-02` "OCI Runtime Spec"; `X-litmus-a-001` "The OCI Runtime Spec v1.3.0 was released, containing 24 pull requests that were merged since the 1.2.1 release." |
| Agent runtime | Agent Client Protocol | v1 | unverified | The unit of execution is one prompt turn closed by an explicit stop reason; capabilities are negotiated at session open and every one defaults to absent | `F-b3-05` "Agent Client Protocol"; `X-litmus-a-015` "The cancelled stop reason must be returned when the client sends a session/cancel notification" |
| Tool access | Model Context Protocol | 2026-07-28 | unverified | The catalogue is discovered at bind time, arguments are checked against the published schema before the call leaves, and the declared surface is narrower than the catalogue | `F-b3-06` "Model Context Protocol"; `X-litmus-a-024` "Dynamic toolsets maintain essentially flat initial token usage" |
| Capability packaging | Agent Skills spec | v1 (published 2025-12-18) | unverified | The contract carries name and description resident; the body loads on the trigger and the reference only when the work reaches it | `F-b3-07` "Agent Skills spec"; `X-litmus-a-025` "a three-tier progressive-disclosure architecture for how agents load capabilities" |
| Model access | Completions wire convention | contested | unverified | The caller names a routing class; a request naming a vendor never gets past the request gate | `F-b3-03` "OpenAI-compatible completions"; `X-litmus-a-005` "In 2026, OpenAI-compatible APIs have become the de facto standard" |
| Errors | RFC 9457 problem details | RFC 9457 (July 2023) | unverified | Every refusal here is built at one construction point against a closed registry and served as `application/problem+json` | `F-b3-13` "RFC 9457 problem details"; `X-litmus-b-023` "a single machine-readable error body, served as application/problem+json … with five standard members: type, title, status, detail, and instance" |
| Document validation | JSON Schema 2020-12 | 2020-12 | unverified | All four entry documents validate against the reference example's published entry schema, with its validator, not a second one | `F-b3-09` "JSON Schema 2020-12" |
| Task lifecycle | published task states | unversioned here | unverified | submitted, working, input-required, completed, failed — adopted, never invented | `X-litmus-b-003` "Tasks progress through a defined lifecycle including submitted, working, input-required, completed, and failed states."; `FILE:docs/consumption/unit-design.md#states` "Do not invent a state name." |
| Why every version status is `unverified` | — | — | — | No specification page was fetched by this session or the ones before it; the repository's own status row records the condition | `FILE:STATUS.md` "\| 14 \| Standard versions \| Each version is verified against its spec \| Blocked \| Page fetch is blocked \|" |

## 3. The call

Four entries cover nearly every situation and all four enter through the same
shape (`T-t6-02` "Four entries cover nearly every situation: a human, an event,
a schedule (time), and an external system or agent."). Each document below
validates against `examples/end-to-end/schemas/entry.schema.json` with that
example's own validator; no client library from this repository is involved
(`F-b1-05` "A caller needs no client library we wrote.").

| Door | The one line a caller writes | The document behind it | What is different | What is identical |
|---|---|---|---|---|
| human (a shell or an IDE) | `python3 examples/run/run.py --entry examples/run/entries/human.json` | `entries/human.json` — `user:corey`, one-hop delegation chain | free text a person typed; `fleet_size: 1` | envelope shape, unit declaration, contract entries, candidate digest |
| event | `python3 examples/run/run.py --entry examples/run/entries/event.json` | `entries/event.json` — `service:alerting`, two-hop chain via token exchange | a structured alert body | as above |
| schedule | `python3 examples/run/run.py --entry examples/run/entries/schedule.json` | `entries/schedule.json` — `schedule:nightly-fault-sweep`, acting on a user's behalf | `payload.fleet_size: 50` is what fans this door out to fifty units — the width is in the document, and `--fleet` only overrides it (`test.sh` step 11). `payload.recurrence` is carried and **not** consumed here: recurrence belongs to the scheduling capability, which the `progress` area exercises | as above |
| external (another agent) | `python3 examples/run/run.py --entry examples/run/entries/external.json` | `entries/external.json` — `agent:partner-sre-bot`, three-hop chain, `parent_correlation_id`, `depth: 1` | submitted by another system | as above |
| the unit behind all four | `intent.workflow_ref` → `units/fix-checkout-coupon-500s.json` | the task specification: isolation declaration, source ref, attempt class, escalation class, three ceilings, contract entries, the opaque criterion handle | nothing | one declaration, four doors |

Measured, not asserted: the four doors render byte-identical declared contract
entries and produce one candidate digest, while carrying four actors and four
correlation ids (`test.sh` step 1). Correlation rides on explicit attributes
stamped on every ledger record, never on trace parentage (`F-a7-02`
"Correlation must ride on an explicit resource attribute set at dispatch").

## 4. What the user sees

| Surface | Content | Evidence |
|---|---|---|
| Plan table, before anything runs | Every step of the unit — attempt 1..N, measure 1..N, the one permitted class step — with its operator, its model class and its estimate in micros; then the worst case, the shortest finishing path and the ceiling | `F-b1-06` "Cost is knowable before commitment. Planning is a pure function and completes before execution begins."; `F-b2-03` "pure function `document → plan + cost`" |
| Typed events from inside the turn | Session capabilities as actually negotiated (streaming, permission callbacks, cancellation — each defaults to absent), update frames, one terminal frame with a stop reason, and the count of frames after it | `FILE:docs/litmus/questionnaire.json#agent-runtime.future_state` "one prompt turn closed by an explicit stop reason"; `X-litmus-a-015` "session setup, prompt turns, streamed messages and tool status … cancellation" |
| The attempt table | Per attempt: model class, whether the attempt was cold or folded, stop reason, candidate digest, outcome, which deciding checks failed, cost | `FILE:docs/consumption/unit-design.md#states` "each attempt of a unit is recorded as a candidate row - attempt number, class used, candidate digest, check report, tokens, cost, wall time" |
| The deciding-check table (caller only) | One row per deciding check: opaque id, kind (`behavioural` / `well_formedness`), pass or fail. The unit itself receives only the id and the outcome, folded into the next attempt's contract | `F-b1-07` "The grader is never visible to the graded. An agent sees its outcome, never the criterion it is judged against." |
| The visible-check line | The unit's own feedback surface, printed and labelled as not deciding | `X-unit-design-023` "most tasks provide visible feedback surface for agent use during development while reserving stricter hidden checks for final scoring" |
| The containment report | Read by the host about the cell: jail mode, whether the owning identity exists in the host account database, egress attempts made and blocked, secrets seen inside, and the marker read back from the running unit | `F-a3-06` "`0700`, owned by a per-VM uid with no passwd entry — verified live"; `F-a3-04` "**None.** Egress is a flag, default off" |
| The receipt: `out/*.jsonl` | One hash-chained record per thing that happened — `unit-submitted`, `contract-sealed`, `cell-admitted`, `turn-started`, `capability-call` (×3), `output-sealed`, `visible-checks`, `cell-terminated`, `check-report`, `attempt-recorded`, `escalated`, `approval-parked`, `unit-completed \| unit-failed \| unit-parked \| unit-rejected` — each stamped with run id, correlation id, actor, delegation depth, entry kind and idempotency key | `F-b4-06` "Correlation rides on explicit attributes, not trace parentage"; `F-b4-05` "Every artifact is attributable to the code version, inputs and actor that produced it" |
| On a refusal that ends the unit | `application/problem+json` on stdout and exit 2. Two of them, both measured (`test.sh` steps 7, 13): `document-invalid` (422) for a malformed envelope, and `budget-exhausted` (402) when the shortest finishing path exceeds the ceiling — refused before any cell is admitted | `F-b4-07` "Typed and machine-readable. Never parsed from prose"; `F-b4-04` "Refusal is deterministic and happens before execution, not after spend" |
| On a refusal taken inside the unit | A refused tool call does not end the unit and is never printed as a problem body to the caller: it is folded into the `capability-call` record's `refused` list by its deciding rule id. Two of them, both measured (`test.sh` step 10): `declared-surface` for a tool outside the declared surface, `read-only-verdict` against the policy verdict. The second isolation class answers an unserved snapshot operation the same way, with `isolation-operation-unsupported` (501), recorded rather than degraded (`test.sh` step 9). A suffix the closed registry does not carry is recorded as a gap, never minted — gap 1 | `F-b4-04` "Refusal is deterministic and happens before execution, not after spend"; `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| Per door, the lifecycle the work passes through | submitted → working → completed, or → input-required when the attempt ceiling parks a person, or → failed when a cap fires, or → rejected before anything ran. The reader may cancel: cancellation is negotiated at session open and the boundary enforces the grace window from outside | `X-litmus-b-003` "submitted, working, input-required, completed, and failed states" |
| The fleet line | Fifty units, their states, fifty distinct correlation ids, and the candidate digest they agreed on. Read back from the receipt: 50 units × 2 attempts = 100 attempt cells and 100 measure cells, 200 distinct cell ids and no id reused | proposed: the fleet summary is this example's own surface; the counts above are read back from `out/fleet.jsonl` and asserted by `test.sh` step 11 |

## 5. Composition

| Piece | What it is here | Built from | Evidence |
|---|---|---|---|
| unit | contract + cell + harness + model door + measure step + ledger record; it is what Dispatch dispatches and it returns exactly one result | `run.py:unit()` | `F-b5-02` "**Dispatch** — one unit of agent work executes and returns one result." |
| attempt (execution) | one prompt turn in one cell, one candidate, one check report | `run.py:attempt()` | `FILE:docs/reference/ontology.md#pins` "**Run** in this platform is one execution of one attempt: one harness invocation in one cell." |
| sequence | render contract → admit → turn → seal → measure → record, in that order, per attempt | `run.py:attempt()` | `FILE:docs/consumption/unit-design.md#steps` |
| bounded loop | attempts 1..N and class steps 0..M, both bounds read off the unit declaration (`ceilings.attempts`, `escalation.class_steps_permitted`) and neither written inside the loop; the ceiling parks a person rather than stopping | `run.py:unit()` | `FILE:docs/consumption/unit-design.md#escalation` "When the attempt ceiling or the budget ceiling fires, park an approval gate - never stop silently." |
| judge | `(candidate, criterion) → verdict`, pure, calling no model, so escalating the attempter never escalates the measurer | `assessor.py:measure()` | `F-b2-05` "pure function `(result, criterion) → verdict`" |
| approval gate | the attempt ceiling parks at `input-required` on the same correlation id | `run.py:unit()` `approval-parked` | `X-litmus-b-003` "input-required" |
| parallel | fifty units at once, each its own run id, correlation id, idempotency key, contract digest, cell and jail | `run.py:fleet()` | proposed: the fan-out here is fifty independent units rather than branches of one workflow, because the run area's question is fifty sandboxes, not one plan with fifty steps |
| agent call | one completion by class through the model door; the class is a routing prefix, and the ladder a class step walks is `run.ladder()`, which sorts the gateway's own routing table by its recorded unit price at call time | `run.py:brokered_calls()`, `run.py:ladder()` | `F-a4-01` "Callers request a class, never a vendor."; proposed: the price ordering of the ladder is this example's reading of "escalate exactly one class" |
| reuse, not copy | the entry schema, the schema validator and the hash-chained ledger come from `examples/end-to-end/run.py`; the five capabilities come from `harness/{containment,gateway,tool-access,capability-packaging,errors}` through `harnesses.py`, which gives each its own module namespace | `harnesses.py` | proposed: our reuse convention — a copied runner drifts and then two things must be kept true |

### Adapters (the only place a product may be named)

| Capability | Adapter used here | Selected by | Second adapter on file, its execution model, and where it is proved |
|---|---|---|---|
| Isolation + agent runtime | `harness/containment/adapters/dryrun.py` — a machine granted, a process held open, cancellable mid-turn | `ADAPTER=dryrun\|second` | `adapters/second.py` — capability grants instead of a machine, single-shot, no snapshot; it answers `isolation-operation-unsupported` (501) rather than degrading. **Proved here**, in this run: `test.sh` step 9 |
| Model access | `harness/gateway/adapters/dryrun.py` | `GATEWAY_ADAPTER` | `adapters/second.py` — a provider's asynchronous batch route: submit returns a ticket, claim polls it, cost is committed at submit and reconciled at claim, and nothing can be cancelled once submitted. Proved in that harness's own gate, not here |
| Tool access | `harness/tool-access/adapters/dryrun.py` | `TOOLS_ADAPTER` | `adapters/second.py` — a catalogue authored and versioned outside this platform, on a remote server holding its own authorization: the catalogue is re-read at every bind and may change between them, and a cancel is recorded rather than honoured. Proved in that harness's own gate, not here |
| Capability packaging | `harness/capability-packaging/adapters/dryrun.py` | `PACKAGING_ADAPTER` | `adapters/second.py` — a registry loader rather than a second directory: a namespace-scoped identity is resolved to a content digest, and the digest is verified against the bytes returned, before anything is read. Proved in that harness's own gate, not here |
| Errors | `harness/errors` construction point and closed registry | — | — (one construction point; it has no second implementation to swap) |

No live credential, live endpoint or vendor client is reachable from this
directory: the dry-run adapters run in process with no network, and the call
shape is the one the live adapter takes (`F-b1-04` "Swappability is a tested
property, not an intention.").

### Run steps

| # | Step | Command | Last line |
|---|---|---|---|
| 1 | the visible check | `bash examples/run/test.sh` | `passed 50, failed 0` |
| 2 | one unit, human door | `python3 examples/run/run.py --entry examples/run/entries/human.json` | `completed: 2 attempts, class stepped False, …` |
| 3 | fifty at once, schedule door (the width is `payload.fleet_size`) | `python3 examples/run/run.py --entry examples/run/entries/schedule.json` | `FLEET  50 units, 50 completed, …` |
| 4 | the other containment technology | `ADAPTER=second python3 examples/run/run.py --entry examples/run/entries/human.json` | the marker moves, the candidate digest does not |
| 5 | an attempter that never learns | `python3 examples/run/run.py --entry examples/run/entries/human.json --stuck` | `input-required: 3 attempts, class stepped True, …` |
| 6 | widen the seed after it was ledgered | `python3 examples/run/run.py --entry examples/run/entries/human.json --widen-contract --attempts 1` | deciding check `d-05` fails |
| 7 | a ceiling below the plan floor | `python3 examples/run/run.py --entry examples/run/entries/human.json --budget-micros 1000` | 402, refused before execution, no cell admitted |
| 8 | a wall-clock ceiling shorter than the turn | `python3 examples/run/run.py --entry examples/run/entries/human.json --ceiling-seconds 0.02 --attempts 1` | `failed`, terminated by the boundary |
| 9 | nothing behavioural ran | `python3 examples/run/run.py --entry examples/run/entries/human.json --criteria wellformedness-only --attempts 1` | check report `inconclusive`, never `passed` |
| 10 | read the receipt | `python3 examples/run/run.py --verify-ledger --ledger examples/run/out/human.jsonl` | `chain verifies` |

A deciding check for this example itself is held out and is **not** in this
directory; `test.sh` is the visible surface only (`F-b1-07` "The grader is never
visible to the graded."). The deciding checks for the *unit* live host-side in
`assessor.py`, outside every contract mount, and `test.sh` asserts mechanically
that neither the held-out fixture nor a criterion body name reaches a mount.

## 6. Extension points

| Where a builder adds | Without touching | How | Evidence |
|---|---|---|---|
| A different containment class | `run.py`, `assessor.py`, the entry documents | write an adapter under `harness/containment/adapters/` exporting `Adapter` and set `ADAPTER`; the run's call shape does not change | `F-b1-02` "The core imports interfaces, never implementations."; measured: `test.sh` step 9 runs the whole example on the second class |
| A different subject and criterion | the runner | add a row to `assessor.CRITERIA` under a new `criterion://…` handle and point `deciding_criteria_ref` at it; the unit declaration names its grader without naming its grade | proposed: the opaque `criterion://` handle is this example's own convention, chosen so the declaration can name a grader without carrying the grade (`F-b1-07` "The grader is never visible to the graded.") |
| More contract entries | the contract renderer's callers | add a row to `contract_entries` in the unit declaration with its `load_tier`; the manifest, the digest and the resident token count follow | proposed: a manifest rather than a directory listing is this example's own convention, so the load tier and the token count per entry are data a pre-flight card can read rather than habit |
| A different class ladder | `run.py`, and any call site | reprice or add a class in `harness/gateway/routing.json`; `run.ladder()` sorts that table by `unit_micros_per_1k` at call time, so the ladder moves with the table and no prefix is written down in this example | `F-a4-01` "Callers request a class, never a vendor. Prefix carries the contract."; measured: `test.sh` step 5 asserts the ladder is the routing table in price order, that the top rung does not step past itself, and that a class the table does not carry is not stepped |
| A different attempt policy | the attempt itself | change `ceilings.attempts` and `escalation.class_steps_permitted` on the declaration; the loop bound lives on the document, never inside the loop | `FILE:docs/consumption/unit-design.md#escalation`; measured: `test.sh` step 5 runs the same unit at `class_steps_permitted` 0 and 1 and gets no class step and exactly one |

### Gaps this example exposed

| # | Claim that is not supported here | Research query |
|---|---|---|
| 1 | The errors capability's closed registry has no row for `isolation-operation-unsupported` or `runtime-unavailable`, which the isolation interface raises. The run records the mismatch (`gap: problem types raised with no row in the closed registry`) rather than minting a suffix, but a typed refusal a caller cannot look up is only half typed. | what governs adding a problem type to a closed registry — who may mint one, what makes a suffix stable, and what a caller does with a type its registry copy does not carry |
| 2 | Stop reasons do not line up. The isolation interface names four (`end_turn`, `cancelled`, `cancel_timeout`, `terminated`) and the design record names ten. This example reports whichever the adapter returned, so `terminated` stands in for both a budget ceiling and a deadline. | how is one stop-reason vocabulary held across an agent-runtime protocol's own set and a platform's wider set of endings, without inventing a state name |
| 3 | The measure cell is forked from the seeded snapshot only where the isolation class offers snapshot operations; the second adapter falls back to a fresh admission, which is a different anti-tamper story with the same words. | what does an isolation interface return when it cannot fork, such that a grader still runs somewhere the graded unit provably never controlled |
| 4 | Nothing here signs anything. The contract digest is hash-chained in a ledger this repository wrote, so an outside verifier cannot check it with a tool we did not write, which is what provenance asks for. | what minimal attestation binds a contract digest, an isolation declaration and a source ref to a dispatch id such that an independently maintained verifier can check it |
| 5 | The candidate is produced by a deterministic stand-in, not by a model turn: the model door is real and its tokens and cost are recorded, but the edit itself is scripted, so the attempt ledger measures the platform and not the attempter. Tokens per done and attempts to done are therefore claimed, not measured. | run the bounded attempt loop against two model classes on a live gateway and record done rate, tokens per done and attempts to done per class |
| 6 | The visible/hidden split here is two visible and five deciding checks, roughly the ratio current practice uses, but the ratio is copied rather than derived. | what determines the visible/hidden ratio for a given task shape, and what is the failure mode when too little is visible at long horizons |
| 7 | A policy allow has no scope or lifetime here: the tool verdict is read from the contract once and every attempt of the unit runs under it, though each attempt is a new dispatch. | what scope and lifetime should an allow carry so that attempt n+1 is decided again before its next side effect |
| 8 | Fifty units at once is fifty threads in one process. Concurrency is real enough to exercise the run-level admission budget and one hash chain under a lock, but it is not fifty machines, and nothing here measures what fifty concurrent cells cost. | what does per-sandbox cost and start latency look like at a fleet of fifty on each isolation class, measured rather than quoted |
| 9 | The `example-provenance` shape has no member for the producing identity, though a provenance predicate is supposed to carry one; this example records its author in a `measured` line, which is the wrong place for it (`X-litmus-d-006` "The official specification describes provenance predicates capturing builder identity, build instructions, parameters, environment variables, and dependency digests"). | should an example's provenance record carry the producing identity and input digests as first-class members, and what verifies them |
| 10 | The measure cell is admitted from the seeded snapshot, ledgered and terminated, but the deciding check bodies run in the host process against the sealed candidate on the host filesystem: nothing is mounted into that cell and no check executes inside it. The isolation interface publishes admit, terminate, snapshot and one prompt turn, and no operation that runs a host-supplied check inside a cell — so the anti-tamper story README section 1 quotes ("a fresh cell forked from the seeded snapshot, with the unit's sealed output mounted read-only") is claimed here, not measured. The `check-report` record says so in `checks_ran: host-side` rather than leaving it to be assumed. | what operation should an isolation interface publish so a grader's own bytes run inside a cell forked from the graded unit's snapshot, and what does the grader return through when it has no session of its own |
| 11 | The area has a visible check and no hidden one. The index expects `docs/night/hidden/run.sh`; this author's brief permits touching only `examples/run/`, so the row reads `-` and the area is, by the skill's own rule, incomplete rather than passing. | where does an area's held-out check live, who writes it, and what does the index report for an area with a README and no hidden check |
