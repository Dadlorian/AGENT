---
name: "cap-scheduling-implement"
description: "How to build the Scheduling capability on this stack: what today's engine-owned schedules give you and what they cost, a standalone recurrence evaluator that computes occurrences as a pure call and enqueues them, the migration between the two with the declaration held still, where firing is wired so an occurrence cannot bypass identity, correlation, budget or replay safety, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that decides a recurring unit is due, when moving recurrence out of the engine that runs the work, when a repeating job fired at the wrong hour after a clock change, when choosing where the ticker lives and how far ahead it looks, or when a conformance run reports a computed occurrence set that does not match its vector."
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

### Shapes (JSON Schema 2020-12)

**SchedulingAdapterConfig (the only thing that differs between the two conformance runs)** (sourced; sources: `T-t7-02`)

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

**RecurrenceConformanceReport (what the definition of done below asserts against)** (sourced; sources: `T-t9-06`)

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
| Cross-cutting wiring is not optional for a firing: concerns are managed across the entire structure, whichever entry point was used, so the fired envelope carries the declaring actor and delegation chain, the correlation identifier, the budget ceiling and the derived idempotency key before it reaches the entry path, not after. | sourced | `T-t2-03` "whichever entry point was used" |
| build-evidence-record owns what an evidence record contains, and F-part-c-08 fixes the claimed-versus-measured distinction. The consequence here is that every claim this facet makes about an adapter's behaviour is claimed until a vector run produces it: the conformance report shape above is the artefact that upgrades a claim, and a report with `vectors_run: 0` upgrades nothing. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| cap-scheduling already fixes the declaration as the whole surface, and F-part-c-09 fixes that products belong in the adapter column only. The build consequence: neither adapter's internals reach the declaration. The engine's schedule identifier, its pause state and its own calendar expression stay inside the adapter, as does the standalone evaluator's queue name and ticker window. | sourced | `F-part-c-09` "Products belong in the adapter column only." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start by writing the declaration and the vector corpus, before either adapter exists: the recurrence string, anchor, zone and catch-up policy per unit, and the four vector classes cap-scheduling requires. Store the corpus under tests/vectors/rfc5545/. | Proposed sequencing. The corpus is simultaneously the correctness test and the swap test, so writing it first means neither adapter can be built to its own idea of correct; a corpus derived from a running adapter would encode that adapter's translation bugs as expectations. Research query: does RFC 5545 itself (fetched, not the table row F-b3-15) fix four canonical test-vector classes, or is that vector-corpus shape this facet's own testing design? | proposed | `F-b3-15` |
| 2 | Build the standalone evaluator first, not second: a library call that takes rule, anchor, zone and window and returns the occurrence set, with no clock read and no store access, plus a ticker that asks it for a short forward window and enqueues one message per occurrence. The engine-owned candidate is not a live option to start from: the recorded inventory already shows its orchestration server not listening (F-a6-02). | Proposed ordering, and a departure worth stating. The recorded adapter today is the engine's own schedules, but PASS.md A6 records that engine as not listening, so building against it first would leave the capability untestable; the pure evaluator can be driven by the corpus on a laptop. | sourced | `F-a6-02` "server not listening on `7233`/`8233`" |
| 3 | Build the engine-owned adapter as the second implementation behind the same interface: register the declared string with the engine, let it own the timer, and map its firing back onto the same entry envelope. Do not let it own the declaration. | Proposed. build-adapter-pair states design rule 3, and the axis these two differ on is where the timer lives: coupled to the engine that executes, or a separate process that only decides. Keeping the declaration outside both is what makes the swap a configuration change. Research query: does a fetched engine-adapter integration guide for the recorded orchestration candidate fix that the engine must not own the declaration, or is that boundary this facet's own reading of build-adapter-pair's design rule 3? | proposed | `F-b1-04`, `F-b3-15` |
| 4 | Wire the cross-cutting concerns at one place, the point where an occurrence becomes an envelope, and stamp actor, delegation chain, correlation, budget ceiling and the idempotency key derived from unit plus occurrence instant. Give no adapter its own envelope builder. | Two envelope builders become two answers to what a firing carries. Concerns are managed across the entire structure, whichever entry point was used, so a schedule with its own builder is a hole in that guarantee that only shows up in an audit. | sourced | `T-t2-03` "whichever entry point was used" |
| 5 | Derive the idempotency key from the unit reference and the occurrence instant, never from the wall clock at firing time, and let a catch-up firing reuse it. | Proposed. A key minted at firing time is new on every retry and every catch-up, so a double fire looks like two intents; a key derived from the occurrence makes a late fire and a normal fire of the same occurrence one request, which is what makes catch_up safe to declare at all. Research query: does xc-idempotency-lease's own key-derivation rule name unit-reference-plus-occurrence-instant as the required input, which would source this row by pointing to that skill instead of restating the derivation here? | proposed | `F-b3-15` |
| 6 | Refuse at declare time any rule part the selected adapter cannot evaluate, and record the refused parts in `unsupported_parts` rather than accepting the declaration and firing approximately. | Proposed, and the reason the report carries that field. An adapter that silently approximates a rule part it does not implement produces a schedule that looks declared and fires at the wrong time, which is worse than a rejected declaration because nothing reports it. Research query: does F-a7-03's structurally-green finding, already cited elsewhere in this facet for a subset-declaration pattern, extend to a declare-time refusal of an unsupported rule part specifically, or is refuse-at-declare-time this facet's own choice? | proposed | `F-b3-15` |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: keep the ticker window short and the evaluator stateless, and let re-asking be cheap. Because occurrences is pure, asking twice for an overlapping window costs nothing and the derived idempotency key collapses the duplicate, so a ticker that crashes mid-window needs no recovery logic of its own. Research query: does cap-scheduling's own purity claim for occurrences (already established, non-kb) get a kb citation once fetched from RFC 5545's own definition of the recurrence function, which would source the re-asking-is-cheap consequence rather than leave it a proposed practice? | proposed | `F-b3-15` |
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
| Criterion | bash harness/scheduling/test.sh && python3 harness/scheduling/conformance.py --vectors --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at d6473df: exit 0; last lines: # adapter standalone-evaluator vectors_run=43 mismatches=0 corpus_covers=['bysetpos', 'dst_back', 'dst_forward', 'leap_day'] unsupported_parts=[] \| conformance PASSED (vectors): 2 binding(s) |
| Deliberate breakage | In harness/scheduling/interface.py idempotency_key(), mint the key from the wall clock instead of unit and occurrence, run the criterion (the replay case fails on both adapters while the vector corpus still shows mismatches 0, and the gate exits 1), then git checkout harness/scheduling/interface.py. |
| Expected failure | Measured by tools/measure.py at d6473df: exit 1; last lines:   File "<stdin>", line 14, in <module> \| AssertionError: the breakage pattern was not found; test.sh is out of sync with interface.py |
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
