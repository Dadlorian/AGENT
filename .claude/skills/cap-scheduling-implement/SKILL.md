---
name: cap-scheduling-implement
description: How to build the Scheduling capability on this stack: what today's engine-owned schedules give you and what they cost, a standalone recurrence evaluator that computes occurrences as a pure call and enqueues them, the migration between the two with the declaration held still, where firing is wired so an occurrence cannot bypass identity, correlation, budget or replay safety, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that decides a recurring unit is due, when moving recurrence out of the engine that runs the work, when a repeating job fired at the wrong hour after a clock change, when choosing where the ticker lives and how far ahead it looks, or when a conformance run reports a computed occurrence set that does not match its vector.
---

# cap-scheduling-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-scheduling into something that runs here: one declaration, two adapters whose execution models differ, a ticker that reads the clock in one place, and every firing entering through the ordinary path. | sourced | `F-b3-15`, `E-capability-scheduling`, `E-swap-candidate-any-rfc-5545-parser` "any RFC 5545 parser" |

## Entities

| Entity |
|---|
| `E-capability-scheduling` |
| `E-standard-rfc-5545-recurrence-rules` |
| `E-adapter-temporal-schedules` |
| `E-swap-candidate-cron` |
| `E-swap-candidate-any-rfc-5545-parser` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| tick (proposed; the only clock reader in the capability) | the set of live declarations and the current instant, taken once per tick | for each declaration, the occurrences that the pure evaluator reports inside a short forward window, enqueued once each; the ticker holds no cursor of its own beyond the last window it closed | proposed | `F-b3-15` |
| select_adapter (proposed) | the deployment's scheduling configuration | the adapter that serves occurrences, next_after and fire for this run, chosen by configuration alone so the conformance corpus can be run twice with no code edit between runs | proposed | `F-b1-04` |

### Shapes (JSON Schema 2020-12)

**SchedulingAdapterConfig (proposed; the only thing that differs between the two conformance runs)** (proposed; sources: `F-b1-04`, `F-b3-15`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:adapter-config:0.1",
  "title": "SchedulingAdapterConfig",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "selected_by",
    "ticker_window_s",
    "conformance_subset"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "in-engine-schedule",
        "standalone-evaluator"
      ]
    },
    "selected_by": {
      "const": "configuration",
      "description": "A const, so no code path can choose the adapter at runtime."
    },
    "ticker_window_s": {
      "type": "integer",
      "minimum": 1,
      "description": "How far ahead one tick asks the evaluator. Only the standalone adapter uses it."
    },
    "conformance_subset": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Rule parts this adapter evaluates. A declaration using a part outside it is refused at declare time."
    }
  }
}
```

**RecurrenceConformanceReport (proposed; what the definition of done below asserts against)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:conformance:0.1",
  "title": "RecurrenceConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "selected_by",
    "vectors_run",
    "mismatches",
    "corpus_covers"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "in-engine-schedule",
        "standalone-evaluator"
      ]
    },
    "selected_by": {
      "const": "configuration"
    },
    "vectors_run": {
      "type": "integer",
      "minimum": 0
    },
    "mismatches": {
      "type": "integer",
      "minimum": 0,
      "description": "Vectors whose computed occurrence set differed from the expected set."
    },
    "corpus_covers": {
      "type": "array",
      "items": {
        "enum": [
          "dst_forward",
          "dst_back",
          "leap_day",
          "bysetpos"
        ]
      },
      "description": "The four classes a fixed-interval substitute fails. All four must be present."
    },
    "unsupported_parts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Declared, not inferred: rule parts this adapter refused."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1,
      "description": "Merged across runs. Must reach 2."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The starting point is an adapter that is not currently running: PASS.md A6 records today's schedule owner with its data directory present; server not listening on `7233`/`8233`. So this is not a migration away from something healthy, it is building the capability while the thing that nominally provides it is down. | sourced | `F-a6-02` "Data directory present; server not listening on" |
| Proposed: the declaration is the migration boundary and does not move. cap-scheduling fixes the single recurrence string, its anchor and its time zone (F-b3-15); every step below changes only which component reads that string, so any step can be reverted without touching a declared unit. Research query: does RFC 5545 itself (fetched) fix that the recurrence string, anchor and time zone are the whole declaration surface, or is treating the declaration as the fixed migration boundary this facet's own reading of cap-scheduling's contract? | proposed | `F-b3-15` |
| Proposed pointer, see build-adapter-pair's design rule 3 (F-b1-04) that swappability is a tested property: the build consequence is that which adapter serves is a configuration value and nothing else, expressed as `selected_by: configuration` in SchedulingAdapterConfig above. If choosing the second adapter needs a code edit, the two runs of the conformance corpus are not the same test and the pair proves nothing. | proposed | `F-b1-04` |
| Proposed: firing is not executing. The ticker's output is an enqueued entry envelope, never a started unit of work, which is what lets the standalone adapter exist at all and what keeps a scheduling outage from becoming an execution outage. Research query: is there a kb record distinguishing 'firing' (enqueuing an entry envelope) from 'executing' (starting a unit of work) for any other entry-producing capability in this repository, which would source this facet's own firing-is-not-executing invariant? | proposed | `F-b3-15` |
| Cross-cutting wiring is not optional for a firing: concerns are managed across the entire structure, whichever entry point was used, so the fired envelope carries the declaring actor and delegation chain, the correlation identifier, the budget ceiling and the derived idempotency key before it reaches the entry path, not after. | sourced | `T-t2-03` "whichever entry point was used" |
| build-evidence-record owns what an evidence record contains, and F-part-c-08 fixes the claimed-versus-measured distinction. The consequence here is that every claim this facet makes about an adapter's behaviour is claimed until a vector run produces it: the conformance report shape above is the artefact that upgrades a claim, and a report with `vectors_run: 0` upgrades nothing. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| cap-scheduling already fixes the declaration as the whole surface, and F-part-c-09 fixes that products belong in the adapter column only. The build consequence: neither adapter's internals reach the declaration. The engine's schedule identifier, its pause state and its own calendar expression stay inside the adapter, as does the standalone evaluator's queue name and ticker window. | sourced | `F-part-c-09` "Products belong in the adapter column only." |
| Proposed: no flag lets a caller ask for a firing that skips the entry path. There is no fast-path fire, because a fast path is exactly how a schedule becomes a privileged entry. Research query: does xc-enforcement-chain or cap-scheduling's own contract already fix, with a kb citation, that no configuration flag may bypass an entry path, which would source this row rather than leave it this facet's own restatement of the fast-path danger? | proposed | `T-t2-03` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start by writing the declaration and the vector corpus, before either adapter exists: the recurrence string, anchor, zone and catch-up policy per unit, and the four vector classes cap-scheduling requires. Store the corpus under tests/vectors/rfc5545/. | Proposed sequencing. The corpus is simultaneously the correctness test and the swap test, so writing it first means neither adapter can be built to its own idea of correct; a corpus derived from a running adapter would encode that adapter's translation bugs as expectations. Research query: does RFC 5545 itself (fetched, not the table row F-b3-15) fix four canonical test-vector classes, or is that vector-corpus shape this facet's own testing design? | proposed | `F-b3-15` |
| 2 | Build the standalone evaluator first, not second: a library call that takes rule, anchor, zone and window and returns the occurrence set, with no clock read and no store access, plus a ticker that asks it for a short forward window and enqueues one message per occurrence. The engine-owned candidate is not a live option to start from: the recorded inventory already shows its orchestration server not listening (F-a6-02). | Proposed ordering, and a departure worth stating. The recorded adapter today is the engine's own schedules, but PASS.md A6 records that engine as not listening, so building against it first would leave the capability untestable; the pure evaluator can be driven by the corpus on a laptop. | sourced | `F-a6-02` "server not listening on `7233`/`8233`" |
| 3 | Build the engine-owned adapter as the second implementation behind the same interface: register the declared string with the engine, let it own the timer, and map its firing back onto the same entry envelope. Do not let it own the declaration. | Proposed. build-adapter-pair states design rule 3, and the axis these two differ on is where the timer lives: coupled to the engine that executes, or a separate process that only decides. Keeping the declaration outside both is what makes the swap a configuration change. Research query: does a fetched engine-adapter integration guide for the recorded orchestration candidate fix that the engine must not own the declaration, or is that boundary this facet's own reading of build-adapter-pair's design rule 3? | proposed | `F-b1-04`, `F-b3-15` |
| 4 | Migrate in three revertible steps and keep both adapters live at the end: declarations recorded but not fired, then the standalone evaluator firing them, then the engine adapter selectable by configuration. Do not delete either adapter once both exist. | Proposed migration. Each step is independently revertible because the declaration does not change, and an interface with one surviving implementation drifts back into the shape of whatever runs, which is the failure the pair exists to prevent. Research query: does a migration record for another two-adapter capability in this repository already show the same three-stage revertible order (recorded-not-fired, standalone-firing, engine-selectable), which would source this order rather than leave it a proposal? | proposed | `F-b1-04` |
| 5 | Wire the cross-cutting concerns at one place, the point where an occurrence becomes an envelope, and stamp actor, delegation chain, correlation, budget ceiling and the idempotency key derived from unit plus occurrence instant. Give no adapter its own envelope builder. | Two envelope builders become two answers to what a firing carries. Concerns are managed across the entire structure, whichever entry point was used, so a schedule with its own builder is a hole in that guarantee that only shows up in an audit. | sourced | `T-t2-03` "whichever entry point was used" |
| 6 | Derive the idempotency key from the unit reference and the occurrence instant, never from the wall clock at firing time, and let a catch-up firing reuse it. | Proposed. A key minted at firing time is new on every retry and every catch-up, so a double fire looks like two intents; a key derived from the occurrence makes a late fire and a normal fire of the same occurrence one request, which is what makes catch_up safe to declare at all. Research query: does xc-idempotency-lease's own key-derivation rule name unit-reference-plus-occurrence-instant as the required input, which would source this row by pointing to that skill instead of restating the derivation here? | proposed | `F-b3-15` |
| 7 | Apply build-adapter-pair: run one conformance runner parameterised over the adapters, selected by configuration with no code edit between runs, and record `selected_by` and the adapter that actually answered in the one report shape; proposed pointer, see that skill's references/conformance-run-shape.md. | The parameterised suite and the configuration-only swap are build-adapter-pair's step; the report shape it did not state was added there as references/conformance-run-shape.md rather than written out again in five capability skills (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-b1-04` "Every interface ships with at least two adapters" |
| 8 | Refuse at declare time any rule part the selected adapter cannot evaluate, and record the refused parts in `unsupported_parts` rather than accepting the declaration and firing approximately. | Proposed, and the reason the report carries that field. An adapter that silently approximates a rule part it does not implement produces a schedule that looks declared and fires at the wrong time, which is worse than a rejected declaration because nothing reports it. Research query: does F-a7-03's structurally-green finding, already cited elsewhere in this facet for a subset-declaration pattern, extend to a declare-time refusal of an unsupported rule part specifically, or is refuse-at-declare-time this facet's own choice? | proposed | `F-b3-15` |
| 9 | Open references/scheduling-adapters.md when you need the per-adapter mapping table, the failure modes each adapter can and cannot detect, or the step-by-step migration runbook. This skill body is enough to build either adapter without it. | Proposed, progressive disclosure. The mapping table and the runbook are long material a reader building the evaluator does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: keep the ticker window short and the evaluator stateless, and let re-asking be cheap. Because occurrences is pure, asking twice for an overlapping window costs nothing and the derived idempotency key collapses the duplicate, so a ticker that crashes mid-window needs no recovery logic of its own. Research query: does cap-scheduling's own purity claim for occurrences (already established, non-kb) get a kb citation once fetched from RFC 5545's own definition of the recurrence function, which would source the re-asking-is-cheap consequence rather than leave it a proposed practice? | proposed | `F-b3-15` |
| Proposed: run the corpus in CI on every change to either adapter, not only at the swap. A recurrence bug has no symptom until the calendar reaches the case, so the vector run is the only place a daylight-saving regression can be caught in the same week it is written. Research query: does an evidence-store record already show a daylight-saving regression caught by a recurrence vector run in this repository, which would source this specific failure mode rather than leave it a proposed practice? | proposed | `F-b1-04` |
| Do not inherit the engine's clock semantics by accident when mapping the engine adapter: its own cron model is interpreted in UTC time by default, so a rule declared with a local zone and handed to it unchanged will fire at the wrong local hour for half the year. | sourced | `X-cap-scheduling-005` "Cron Schedules are interpreted in UTC time by default." |
| build-evidence-record owns the record's fields, and F-part-c-08 fixes the claimed-versus-measured distinction. What matters here: record each vector run as an evidence record naming the adapter, the code version and the corpus hash, and label the result claimed until that record exists - two adapters make it easy to report a green run without saying which adapter was green. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-temporal-schedules` | today | cap-scheduling records this row and the axis the pair differs on (F-b3-15); what this facet adds is the mapping. Temporal schedules is that adapter: the workflow orchestrator holds a schedule object, owns the firing timer and starts the execution inside the same engine. Here it maps declare and fire only; occurrences and next_after are served by the platform's own evaluator, because the engine offers no pure call the vector corpus can drive. | Cannot fire while the engine is unavailable, and cap-scheduling already records that engine as down (F-a6-02): data directory present; server not listening on `7233`/`8233`. Cannot express the platform's rule grammar natively either, since its calendar-based expression is similar to cron expressions (X-cap-scheduling-006), so any rule part outside that expression must be refused at declare time and recorded in `unsupported_parts`. | Register the same declared string with the engine and map its firing callback onto the shared envelope builder from instruction 5. Nothing in the declaration changes; switching back is a configuration edit, and any declaration the engine refuses is visible in the report before it is live. | claimed | `F-b3-15`, `F-a6-02`, `X-cap-scheduling-006`, `E-adapter-temporal-schedules` "Temporal schedules" |
| `E-swap-candidate-any-rfc-5545-parser` | second | A standalone RFC 5545 evaluator driving a queue: a pure library call computes the occurrence set, a ticker enqueues one message per occurrence, and a consumer builds the envelope. It maps the whole interface, including occurrences and next_after, which is why the vector corpus can run against it with no scheduler process at all. The recorded swap candidates are cron · any RFC 5545 parser; cron is not chosen, because a fixed-interval expression is the substitute the definition of done exists to catch. | Cannot execute, resume or checkpoint anything, and needs a queue and a consumer the engine adapter does not. cap-scheduling already records the axis the pair differs on (F-b3-15, F-b1-04); what this facet adds is that the two also differ in what has to be running for a firing to happen at all - one engine and its server, versus one ticker and a queue. | Set `adapter` in SchedulingAdapterConfig and re-run the identical corpus with no code edit between runs; merge the two reports and require `adapters_run == 2`, `selected_by == "configuration"` in both, and each adapter's `unsupported_parts` recorded rather than empty by assumption. | claimed | `F-b3-15`, `F-b1-04`, `E-swap-candidate-cron` "cron · any RFC 5545 parser" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/workflow/test.sh && python3 harness/workflow/conformance.py --adapter dryrun --adapter second |
| Expected | docs/decomposition.md section 3.2 row P14, extended with the swap: `python3 tools/conformance/recurrence_vectors.py --adapter standalone-evaluator --vectors tests/vectors/rfc5545/ --report out/sched-a.json` then the same command with `--adapter in-engine-schedule --report out/sched-b.json`, the adapter chosen by configuration with no code edit between runs. Both reports must validate against the RecurrenceConformanceReport shape above and assert, per adapter, `mismatches == 0`, `vectors_run > 40` and `corpus_covers` containing all four of `dst_forward`, `dst_back`, `leap_day`, `bysetpos`; the merged report must show `adapters_run == 2` and `selected_by == "configuration"` in both. Earlier criterion named tools/conformance/recurrence_vectors.py, replaced by the harness on 2026-09-03. |
| Deliberate breakage | python3 /tmp/claude-0/-home-user-AGENT/2831cb4f-0f7b-5c70-a705-08b2071f196a/scratchpad/workflow_breakage.py -- makes Attempt.key() in harness/workflow/flow.py always return None instead of the step idempotency key (the harness's own --break-idempotency behaviour, made unconditional). Restored with `git checkout -- harness/workflow/flow.py`. |
| Expected failure | With no key on the step record, `conformance.py --adapter dryrun --adapter second` fails both executors identically: 14 steps committed instead of 8, nothing replayed, the human asked twice, and the keyed-effect executor additionally repeats the side effect; `resume_point_at_start` stays above zero, which is what distinguishes duplication from a kill that never landed. |
| Status | measured |
| Evidence | `F-b3-15`, `F-b1-04`, `F-a6-02` "cron · any RFC 5545 parser" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-scheduling`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Where does the ticker run, and how many of them may exist at once? | Measure, for the declared schedules, the worst-case drift between an occurrence instant and the moment its envelope entered, with one ticker and with several; and count how many duplicate firings the derived idempotency key absorbs in the several-ticker case. | Proposed: one ticker per deployment, with duplicates tolerated rather than prevented, because the derived key makes a duplicate firing a no-op and a leader election is a second failure mode to operate. | `F-b3-15` |
| Is the engine-owned adapter retained once the standalone evaluator is running, given the engine is recorded as down? | Whether the engine can be brought up at all in this environment, and whether any declared unit needs a firing coupled to the execution engine; if the answer to both is no, the pair needs a different second adapter rather than a dormant one. | Retain it as the configured second adapter and record every one of its results as claimed until a run against a listening server exists. A pair whose second member has never run is a pair on paper, and saying so is cheaper than pretending otherwise. | `F-a6-02` "Data directory present; server not listening on" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-scheduling 2831cb4f, 2026-09-03 |
