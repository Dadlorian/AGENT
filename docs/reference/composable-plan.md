# Reference: a composable plan, end to end

**Status: reference only. Not a definition.** This is one team's worked answer to the problems this platform is being built to solve, distilled from seven source notes dated 2026-08-31 and consolidated here on 2026-09-03. It describes a possible future state. Nothing in it has been run against this repository. PASS.md and TARGET.md remain the sources of truth; where this page and they disagree, they are right.

Every statement below is **claimed** unless it is marked measured with a PASS.md id. The three measured findings it leans on are the ones PASS.md A7 already records (`F-a7-02`, `F-a7-03`, `F-a7-04`). Products appear only in the one adapter column of section 7, per `F-part-c-09`.

**What to take from it:** the shapes, and the failures more than the shapes. **What to leave:** the field names, the layer count, and the specific engines.

---

## 1. The one idea everything else follows from

**The schema is closed. Its vocabularies are open.**

A caller writes a small fixed set of fields that never grows. When the platform needs to do something new, a file is added that widens the legal values of an existing field. No field is added, and no syntax is added to the call.

The test: can a caller learn the whole interface in one sitting and never relearn it as the platform grows? If new capability means new call syntax, the schema is open and will accrete forever.

| Field | Answers |
|---|---|
| `intent` | what is wanted, in the caller's words |
| `contract` | how "done" is decided, machine-checkable |
| `steps` | how, if the caller happens to know |
| `budget` | what it may cost |

Everything else has a default. Only `intent` is mandatory.

This is the same distinction PASS.md B2 draws for the Document core component: declared intent, definition of done, steps (`F-b2-02`).

## 2. Three sizes, one shape

Nothing new is learned between sizes. Only how much of each step the caller chose to say.

| Size | Caller writes | Everything else |
|---|---|---|
| 1, a sentence | `intent:` only | fully defaulted |
| 2, a plan | `name` `intent` `contract` `budget` `steps` | defaults per step, overridden only where it differs |
| 3, a problem nobody has solved | the same five, plus a unit to fan out over, what each step emits, a stopping rule, a deliverable, and how the judge may see the work | appear only when the problem needs them |

Each step is itself a document, so the shape recurses. There is no separate plan format and task format, and nothing is translated between levels. If a framework's hard case needs a new mental model, its easy case was underspecified rather than simple.

## 3. The core example: one document, four doors

### 3.1 What the caller writes

Size 2. Six lines.

```yaml
name:     triage-regression
intent:   Find which change broke the failing checks, propose the narrowest fix
contract: specs/regression-acceptance.yaml
profile:  standard
steps:
  - locate: {unit: failing-check, fanout: {by: unit, tolerate: {failed: 0}}}
  - fix:    {needs: [locate], model: frontier}
  - review: {gate: human, view: diff-summary}
```

Deliberately not written: retry policy, escalation, containment, the model tier for `locate`, acceptance mechanics, the ledger path, telemetry. All of it is carried by `profile: standard` and by the `locate`, `fix` and `review` capability definitions.

### 3.2 What resolves, and from which layer

Resolution is a pure function, runs before anything is spent, and costs nothing.

| Value | Resolved from | Layer |
|---|---|---|
| budget ceiling, deadline, iteration bound | `profile: standard` | platform default |
| model class for `locate` (balanced) and `fix` (frontier) | profile, then the caller's override on `fix` | capability, then caller |
| containment | the `locate` and `fix` capability defaults | capability default |
| the acceptance instrument | `contract:` | caller |
| the ledger path | derived from `name` | platform, never authored |
| `view: diff-summary` | caller, and required because `gate: human` is present | caller |

**Precedence is fixed and total: caller override, then capability default, then platform default.** Every resolved value traces to exactly one of the three. An override is legal, logged, and tagged non-conformant: the rules can always be broken, and the platform always records that they were.

### 3.3 The card, before any spend

```text
━━ plan ━━  triage-regression

STEPS  3 declared · 1 gate
  1  locate    standard   ~$1   ~10m   unit=failing-check  fanout=4  tolerate=0
  2  fix       deep       ~$3   ~25m   model=frontier
  3  review    standard   ~$0   ~5m    GATE → view: diff-summary

BUDGET  est=$4   range=$3–$6   cap=$10   headroom=$4
CLOCK   est 40m

SCOPE   writes  artifacts/ · state/ledger/
        reads   src/ — read-only
        never   the instruments · anything outside artifacts/

RECONCILE  3 steps = 3 bounded + 0 capped   ✔ every step accounted

INSTRUMENTS  held out — not readable from inside a step
  regression-check   score  blind  sla=2s   OK

Done   = artifacts/fix.patch · artifacts/diff-summary · manifest.json
Broken = an instrument misses SLA · the ledger is unwritable · fanout tolerates 0 and one fails
▶ "go" to launch · "revise" to change
```

Two things on the card matter more than the numbers. The **reconcile** line proves every step is either bounded or capped. The **instruments** block shows each grading criterion was probed for liveness at gather time and is held out from the thing it grades (`F-b1-07`).

### 3.4 The four doors

The document is byte-identical through all four. Only resolution differs. This is TARGET.md T6.2's four entries (`T-t6-02`); the source's names are kept in the first row so the mapping is visible.

| | Human | Time (schedule) | External (system or agent) | Internal (event) |
|---|---|---|---|---|
| What fires it | a person submits it | a schedule fires | a push, a webhook, a partner agent | a running plan reports a result |
| Starts or steers | both | starts only | both | **steers only** |
| Whose identity | the person | whoever registered the schedule | the external party, authenticated | the parent run |
| Whose money | theirs, at submit | a standing allocation | a pre-authorised ceiling per source | subdivided from the parent |
| What the gate does | asks, live | queues for later | escalates | escalates to the parent's owner |
| Where the card goes | the terminal | the schedule's owner, on next open | the originating system, as a check | the parent run's view |

**Internal steers but never starts.** Every unit of work therefore traces back to a person, a clock, or an outside event. A loop that can mint its own root work has no provenance and no ceiling. This is the constraint any self-improvement loop (`T-t4-04`) has to live inside.

### 3.5 What comes back

Identical shape from every door, whether one unit ran or a hundred:

```yaml
id:       t-9f2a
status:   submitted | working | completed | failed
artifact: {name: fix.patch, sha256: 3b1f...}
verdict:  {passed: true, checks: [{name: regression-check, status: pass}]}
usage:    {tokens_in: 41020, tokens_out: 8800, cost_usd: 3.71}
trace:    {run_id: t-9f2a, trace_id: 4bf9...}
```

Plus, on disk: the resolved manifest, the card exactly as approved, one artifact per step, and the ledger append. Nothing requires reading a transcript.

## 4. The six stages

The session is the clerk. It frames, gathers, gates and delivers. It never runs the work and never judges the result.

| Stage | Owner | Required output | Cost | Refuse here if |
|---|---|---|---|---|
| 0 Invoke | caller | freeform intent | none | never |
| 1 Frame | session | the four fields resolved into a document | one turn | the document fails schema validation |
| 2 Gather | session | evidence assembled by shell, a liveness probe of every instrument, the blast radius of every unbound decision | **zero, no model call** | an instrument is dead, or a gate has no view |
| 3 Gate | caller | go or revise | none | the caller refuses the number |
| 4 Execute | engine | one output file per step | the real spend | a cap trips |
| 5 Deliver | session | artifacts, manifest, actual versus estimate, the ledger append | one turn | never |

Gather runs **before** the gate. Resolution being pure and free is what lets the card carry real numbers rather than an estimate of an estimate (`F-b1-06`). A dead instrument is a gather-time failure, not a run-time one.

## 5. Composition: four mechanisms, and where each breaks

Composition is not one idea. It is four mechanisms with four failure modes, and a platform needs all four to be more than a task runner.

### 5.1 By extension: add a file, widen a field

| Add a file | Widens | Which lets you |
|---|---|---|
| a capability definition | legal step verbs | teach a new verb once, with its defaults, checks, containment, tier |
| a profile | `profile:` `containment:` `model:` | name a whole constraint bundle in one word |
| a driver definition | what `model: cheap` resolves to | swap a vendor without a caller noticing |
| an instrument definition | `accept.instrument:` | add a held-out criterion with verb, blindness, relativity, SLA |
| a view definition | `view:` | add a rendering a human can decide from |
| an input adapter | what can call in | add an event source as a new **instance**, never a new category |

Entry categories are a closed set of four. What is inside each is open. That is what stops a platform growing a new front door every quarter.

### 5.2 By nesting: depth, and the cost lie

One line does the nesting. `plan: fix-module@v3` on a step makes each unit a full sub-plan with its own resolution, budget and card.

```yaml
name:     harden-service
intent:   Close every finding in the auth surface, module by module
contract: specs/harden-acceptance.yaml
profile:  standard
steps:
  - survey:    {unit: module, fanout: {by: unit, tolerate: {failed: 0}}}
  - remediate: {needs: [survey], unit: module, plan: fix-module@v3}
  - verify:    {needs: [remediate], accept: {instrument: harden-check, blindness: blind}}
  - report:    {gate: human, view: harden-summary}
```

```text
━━ plan ━━  harden-service                    est $28   cap $50   headroom $22
  1  survey       ~$2    unit=module  fanout=6  tolerate=0
  2  remediate    ~$24   unit=module  × 6 sub-plans
  3  verify       ~$2    accept=harden-check · blind
  4  report       ~$0    GATE → view: harden-summary

  └─ 2 · remediate               6 × fix-module@v3          est $24
       └─ fix-module@v3 (plan)   per module                 est $4.00
            loop   evaluator-optimizer@v2   max 3 cycles     ~$3.10
            rule   production-incident-guard@v1              $0
            view   module-diff   (bound to no gate — advisory)

RECONCILE  6 sub-plans × $4.00 = $24.00   ✔ parent estimate is the sum, not a guess
           depth 3 · max allowed 3        ✔ within bound
```

Two failures live here.

- **A nested plan lies about cost unless costs sum upward.** A parent estimate that is its own guess rather than the sum of its children is fiction the moment anything nests. Every kind must declare its cost contribution in its own envelope, and the parent reconciles against the sum. The source marks this specified and **not built**.
- **Depth must be bounded, and checked at resolve time, not run time.** A sub-plan that would nest past the limit is refused before anything executes. A widely used reference implementation caps inline sub-workflows at one level and tracks spawn depth per agent: unbounded nesting is a hazard people have already met.

The transferable test: ask for the cost of a three-level plan, then ask each child independently and add them up. If the numbers differ, the planner is guessing at the top.

A sub-plan receives its unit and its budget slice. It does **not** re-resolve its parent's context. Re-resolution at each depth is how a depth-3 tree costs three times its arithmetic.

### 5.3 By fan-out: many units, one result

| Control | Sits at | Fires when | Result |
|---|---|---|---|
| per-unit budget | the step | one unit exceeds its share | throws, hard ceiling |
| `tolerate: {failed: N}` | the fan-out | more than N units fail | the whole fan-out fails |
| `stop: {marginal_gain_below, window}` | the step | returns flatten | **terminates as success** |
| `cap: {hours}` with `on_cap: escalate` | the step | an unbounded step runs long | **terminates as failure**, to a human |
| depth bound | the plan | a child would nest past the limit | refused at resolve |
| policy rule | admission | an incident window is open | refused at admission |

Failure tolerance is a property of the fan-out, not the unit and not the plan. On the unit you cannot say "any failure is fatal". On the plan you cannot say "tolerate two of forty".

**`stop` and `cap` are opposites and must not be collapsed.** `stop` firing means done. `cap` firing means escalate. The source records merging them into one "halt" as a mistake already made once.

### 5.4 By reference: late binding

This is the mechanism that makes a large plan survivable, and the one most often missing.

Late binding here means **plan time, not run time**. A structural decision, which storage engine, which algorithm, which vendor, is bound at the last point in the plan where it can responsibly be bound. Everything above the contract is authored against the interface rather than the choice. Work above the contract proceeds while the decision is still open.

```yaml
name:     build-service
intent:   Build the auth service across all tiers
contract: specs/service-acceptance.yaml
profile:  standard

assumptions:
  - storage-choice:
      status:          proposed                          # proposed -> accepted | superseded
      assumed:         contracts/repository.schema.yaml  # 6 operations, no vendor
      validated_by:    {plan: storage-bakeoff@v1, lane: batch}
      while_unresolved: hold

steps:
  - contract:  {skill: define-repository, deliverable: contract}
  - frontend:  {skill: build-ui,      needs: [contract], api: [storage-choice], fanout: {by: unit}}
  - routes:    {skill: build-routes,  needs: [contract], api: [storage-choice]}
  - cache:     {skill: build-cache,   needs: [contract], api: [storage-choice]}
  - dao:       {skill: build-dao,     needs: [contract], implementation: [storage-choice]}
  - migrate:   {skill: write-migrations,                 implementation: [storage-choice]}
  - perf:      {skill: tune-queries,  needs: [dao],      implementation: [storage-choice]}
  - verify:    {skill: integration,   needs: [frontend, routes, cache, dao]}
  - report:    {gate: human, view: build-summary}
```

```text
STEPS  9 declared · 1 gate · 5 proceed · 3 hold · 1 blocked
  ...
  5  dao       ⏸ HOLD — inside area of effect
  6  migrate   ⏸ HOLD — inside area of effect
  7  perf      ⏸ HOLD — inside area of effect
  8  verify    ⏸ blocked — needs 5

⚠  OPEN CLAIM   storage-choice      assumed: contracts/repository.schema.yaml
   resolved by     storage-bakeoff@v1 · batch lane · ETA ~24h
   AREA OF EFFECT  3 steps HOLD       dao · migrate · perf
   OUTSIDE         4 steps PROCEED    contract · frontend · routes · cache    $36 · ~4h
   IF REFUTED      3 steps stale · rework exposure $24 of $71 · nothing already spent is lost

RECONCILE  area of effect computed from 3 implementation edges, not declared
```

**This only works if edges are typed, and typed edges are where most graphs are wrong.**

| Edge kind | Means | Cascades on change? | PASS.md B2 Graph edge |
|---|---|---|---|
| `needs:` (ordering) | B runs after A | never | existence |
| `api:` (interface) | B depends on A's contract | only if the contract changes | interface |
| `implementation:` | B depends on how A does it | **yes, the only edge that does** | implementation |

The vocabulary is borrowed. Mainstream build systems distinguish a dependency visible to consumers from one that is not, because that distinction decides what must be rebuilt. A work graph asks the same question. PASS.md B2 already gives Graph these three edge kinds (`F-b2-04`).

**Counting dependents to size blast radius is wrong, and wrong in the worst direction.** A walk that counts everything downstream, every edge weighted the same, over-estimates most when the encapsulation is best, because good layering produces many interface edges and few implementation ones. The better the design, the more the heuristic punishes it. Count implementation edges instead. In this example that is the difference between an area of effect of three steps and nine. The same error appears in chokepoint detection by read count.

**A decision comes back three ways, not two.**

| Outcome | What happens | Cost |
|---|---|---|
| confirms the assumed interface | held steps release, bound to the winner | no rework |
| refutes it | held steps go stale, the contract is re-cut, replan from `contract` | the exposure shown on the card; nothing already spent is lost |
| returns a tradeoff | no mechanical answer exists; resolves to a human gate rendering the comparison | one interruption |

Any framework that models a judgement as a boolean will eventually meet a result that is genuinely a tradeoff, and will silently record a decision nobody made.

One assumption stated rather than hidden: putting several candidates behind one interface works only if their semantics are compatible. If one is transactional and one is eventually consistent, no interface hides that, the edges become implementation-level, and the area of effect grows back. The plan should be refused if the contract cannot actually hold.

### 5.5 What must never compose

Three things do not appear at any depth, by design: the judging criterion, the record of what was already attempted, and the referent a result is compared against.

Anything on the wire is readable by the thing being judged. A leaked comparison target is something to imitate rather than beat. A leaked history of rejected attempts is a map of what to avoid saying rather than what to avoid doing. If these can travel with the work, every verdict below that point is self-graded. This is PASS.md rule 6 (`F-b1-07`), enforced at four independent points in the source: a criterion may not ride on the wire, be echoed inside a verdict, be inlined rather than referenced, or be reachable by a path the executing side could dereference.

## 6. Observation and control across depth

| Depth | Visible | Carrier |
|---|---|---|
| plan | run id, resolved manifest, the approved card | the run directory |
| step | per-step artifact, verdict, usage | one artifact file per step |
| sub-plan | its own run id, its own card, a parent link | a nested run directory |
| loop cycle | attempt N of M, why it re-ran | the ledger append |
| capability call | tokens, cost, model actually used | a telemetry span |

**Parent-to-child correlation must ride on resource attributes, not span parentage.** Measured, per PASS.md A7 (`F-a7-02`): an injected trace context was ignored at the agent runtime boundary and the runtime minted its own root trace, so a depth-3 tree came back as three unrelated traces. Resource attributes set at dispatch landed on every span. The standards make this silent: a propagator that cannot parse an incoming carrier must not throw and must not store a value. Any design that assumes trace propagation across an agent boundary is broken before it starts.

**Mid-run human input at depth is a real constraint, not a detail.** A depth-3 plan with four gates is exactly the case that makes "who may answer a gate, over what wire" load-bearing. The common workaround, run each stage as its own workflow, is a constraint the source names rather than hides.

## 7. Swap seams, with exit cost

A seam is only real if you can state what breaks when you use it. Products appear here and nowhere else on this page.

| Capability | Today's adapter in the source stack | Replaceable by | What breaks on swap |
|---|---|---|---|
| Inference | a local serving engine on owned GPUs plus hosted APIs | any OpenAI-compatible server | caching behaviour differs per engine; economics that depend on owning hardware disappear |
| Gateway | LiteLLM | any gateway with the same shape | provider-specific passthrough routes are not portable |
| Model admission | a host-side broker over vsock | any host-side broker | the held-out-judge pattern uses the same mechanism, so swapping costs both |
| Isolation | Firecracker with jailer | container or workspace-level containment | isolation profiles resolve to weaker guarantees; scope enforcement degrades |
| Agent runtime | goose, claude-code, cursor over ACP | any harness speaking the same agent protocol | trace continuity is runtime-dependent (section 6) |
| Durable execution | Temporal | any durable executor | nothing; the contract above it is unchanged. The cleanest seam |
| Telemetry | OpenTelemetry plus Langfuse | any OTLP collector | nothing. The safest swap |

The pattern to take: write the exit cost next to every dependency **before** adopting it. Two of the seven cost nothing to leave. Knowing which two is the difference between a stack you can evolve and one you can only rewrite. This is rule 3 (`F-b1-04`) with the price attached.

## 8. The dissection method: hop by hop

The source's fourth note walks a minimal plan through twenty hops, from submit to ledger append, and asks the same questions at each. The method is more reusable than the walk.

**Per hop, fourteen questions:** contract (what crosses, what it emits), requirements (testable, with ids), alignment (what the rungs above and below assume), built (what exists, at file and line), gap (the delta as work), standard (which one, at what tier), binding (a standard is acceptable, a vendor is not), failure (what breaks and what it returns), confidence, constraints (what cannot change, and who may call it), state (who owns it, is there a single writer), idempotency (what happens if it runs twice, and what the key is), reuse, and proof (the drill).

**Every requirement gets one of four tags:**

| Tag | Means | What happens to it |
|---|---|---|
| STANDARD | met by a published standard | keep, cite it |
| STACK | met by working code | keep, labelled as best practice or not |
| HOMEGROWN | works, but bespoke where something exists | becomes an **abstraction seam**: name what replaces it |
| ABSENT | nothing meets it | work item |

**The rollup is the deliverable, not the per-hop score.** Requirements that recur across hops become framework components. Homegrown answers that recur become seams. Two of the source's seams were the same defect appearing in two files, a closed tuple of legal values compiled into code, which is exactly what "closed schema, open vocabularies" exists to prevent. Neither hop alone showed it.

Two findings from the walk transfer directly:

- **"Uncalled" hides the work.** A hop first recorded as "zero callers" turned out, on reading the code, to meet six requirements already and four more by bespoke means. The gap was narrower and differently shaped than "nothing exists". Recon before answer, every time.
- **Contradictions are resolved by 1-3-1**, the same protocol TARGET.md T5.2 names (`T-t5-02`): state the problem, three candidate solutions, pick one, rate it on evidence, standard, stack, constraint and reversibility, and name a closing action for every rating that is not green. All amber is the fake: it means the success criterion is undefined.

## 9. The rubric

Six criteria. Each has a failure mode that is easy to spot once named.

| | Criterion | Fails when |
|---|---|---|
| R-1 | Compact: the caller writes only what differs from the default | the example restates a value a profile already carries |
| R-2 | Composed, not restated: complexity lives in a named file | control flow is spelled out inline that a profile should name |
| R-3 | Priced before spend: the card carries measured numbers | any number on the card is an estimate of an estimate |
| R-4 | Decidable: every gate has a view | a human is shown raw output |
| R-5 | Swappable: every engine is named with its seam | the example names a vendor in the caller's document |
| R-6 | Provable: the return carries verdict, usage and trace | the result must be read from a transcript |

R-5 is the one that quietly fails. A vendor name in the caller's document means the abstraction leaked all the way to the top.

## 10. What the source itself declares open

Stated because a reference that hides its gaps is marketing. None of these are solved in the source.

| Gap | Why it matters |
|---|---|
| Cost declaration per kind, summed up the tree | until it exists, a nested card is trusted rather than checked |
| A depth bound checked at resolve time | unbounded nesting is a known hazard, not a theoretical one |
| Parent-to-child correlation as an explicit attribute | span parentage does not survive the runtime boundary |
| A third resolution outcome for an assumption | a boolean launders a tradeoff into a settled fact |
| A deadline on an open assumption | nothing otherwise stops a plan sitting on a guess forever |
| Who may answer a gate, over what wire | depth and holds make this load-bearing |
| Typed edges in the work graph | every blast-radius number is wrong until this lands |
| Only one of the four doors runs | the other three all wait on one missing caller |

## 11. Mapping onto this repository

How the reference's concepts land on PASS.md Part B, TARGET.md, and the skills in `docs/skill-manifest.json`. The right-hand column is where the concept is a gap here too.

| Reference concept | Here | Skill | Gap here |
|---|---|---|---|
| the four fields, recursing per step | Document (`F-b2-02`) | `core-document` | recursion of the step shape is not stated |
| resolution as a free pure function before the gate | Planner (`F-b2-03`), rule 5 | `core-planner` | cost contribution per kind, summed across depth |
| ordering, interface, implementation edges | Graph (`F-b2-04`) | `core-graph` | blast radius over implementation edges only; depth bound at resolve |
| held-out instrument, blindness, relativity | Judge (`F-b2-05`), rule 6 | `core-judge` | the three things that never travel with the work, as a stated rule |
| ledger append, dedupe authority, never on the wire | Ledger (`F-b2-06`) | `core-ledger` | |
| four doors, identical document | `T-t6-02` | `cap-work-intake`, `cap-consumption` | "Internal steers but never starts" as a stated invariant |
| gate with a required view | nothing direct; nearest is `T-t3-01` | `cap-human-interaction`, `compose-approval` | a view as a required field on every gate; who may answer, over what wire |
| the card and the six stages | rule 5 | `seam-dispatch`, `seam-state` | a card renderer |
| profile, driver, instrument, view files | rule 1, rule 4 | `cap-capability-packaging`, `cap-model-access` | |
| correlation on resource attributes | `F-a7-02` (measured) | `xc-correlation` | |
| per-unit budget, cap versus stop | `F-b4-01` | `xc-budget`, `compose-loop` | `stop` and `cap` as distinct terminations |
| typed refusal at every boundary | RFC 9457 | `cap-errors`, `xc-typed-errors` | |
| `assumptions:` with `validated_by` and `while_unresolved` | none | none | the whole late-binding mechanism |
| hop-by-hop dissection and rollup | `T-t5-02`, ceremonies | `build-ceremony` | the four requirement tags |

## 12. What to take, and what to leave

**Take:** the closed-schema, open-vocabulary rule. Difficulty levels that use the same shape. Exit costs written next to every dependency before adoption. The grader never visible to the graded. Counting what executed, not what passed (`F-a7-03`, measured). Typed edges and blast radius over implementation edges only.

**Leave, or decide here:** the specific engines. The layer decomposition; twenty hops was right for the source's problem and is not a target. The field names; `intent` and `contract` are one naming, and the distinction between what is wanted and how done-ness is decided is what matters.

**The single sentence, if you take nothing else:** a caller should need no client library we wrote (`F-b1-05`).

## Provenance

Consolidated from seven source notes supplied on 2026-09-03: a methodology page, a worked example, a composed plan, a late-binding example, its hop-by-hop dissection, the dissection's question card, and an external summary. The source notes cite their own owning specification, which is not in this repository. The four-door example, the composed plan and the late-binding plan are reproduced with their numbers as the source gave them; the numbers are illustrative and were never measured. PASS.md ids cited: `F-b1-04` `F-b1-05` `F-b1-06` `F-b1-07` `F-b2-02` `F-b2-03` `F-b2-04` `F-b2-05` `F-b2-06` `F-b4-01` `F-a7-02` `F-a7-03` `F-a7-04` `F-part-c-09`. TARGET.md ids: `T-t3-01` `T-t4-04` `T-t5-02` `T-t6-02`.
