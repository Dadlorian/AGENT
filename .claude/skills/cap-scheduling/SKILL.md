---
name: "cap-scheduling"
description: "The ideal state of the Scheduling capability: computing when a recurring unit of work is due as a pure function of one recurrence rule, a time zone and a window, governed by RFC 5545 recurrence rules, with the firing occurrence entering the platform through the same envelope as every other entry. Load it when a unit of work needs to happen every night, every third Tuesday or on the last working day of a month, when deciding where recurrence is evaluated and what a firing produces, when a schedule and a manual re-run button are being declared on the same unit, or when judging whether an implementation really evaluates the rule. Also load it when someone proposes taking recurrence from whatever orchestrator happens to run the work, when a job fired an hour late after a clock change or skipped 29 February, when a repeating job needs a catch-up policy, or when a timer is about to become a second, privileged way into the platform."
---

# cap-scheduling

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for deciding when work is due: one portable recurrence rule per unit, evaluated as a pure function, so that recurrence is a capability the platform owns rather than a feature borrowed from whichever engine currently runs the work. | sourced | `F-b3-15`, `E-capability-scheduling`, `E-standard-rfc-5545-recurrence-rules` "RFC 5545 recurrence rules" |

## Entities

| Entity |
|---|
| `E-capability-scheduling` |
| `E-standard-rfc-5545-recurrence-rules` |
| `E-adapter-temporal-schedules` |
| `E-swap-candidate-cron` |
| `E-swap-candidate-any-rfc-5545-parser` |
| `E-capability-work-intake` |
| `E-adapter-schedule` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-rfc-5545-recurrence-rules` | RFC 5545 | unverified | https://www.rfc-editor.org/rfc/rfc5545.html | `F-b3-15`, `X-cap-scheduling-001`, `X-entry-composition-049` |

- `E-standard-rfc-5545-recurrence-rules` version note: RFC 5545, the iCalendar core object specification, of which the recurrence rule (RRULE) grammar is the part adopted here; every record on file for it is search-only and the RFC itself was not fetched from this environment, so no version or revision date is asserted

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| occurrences (operation set the standard's own grammar defines; the recorded row is a data format and a grammar, not a set of calls) | a recurrence rule string, the first instant the rule counts from, an IANA time zone, and a half-open window [from, to) | the ordered, de-duplicated set of occurrence instants that fall inside the window; a pure function, reading no clock and touching no store, so the same four inputs always give the same set. The rule string it reads is the RRULE grammar itself, valid across every frequency the standard defines. | sourced | `F-b3-15`, `X-cap-scheduling-002` "An RRULE is the recurrence rule grammar defined in RFC 5545 that describes a repeating schedule as a single string." |
| next_after | the same rule, first instant and time zone, plus an instant to search from | the first occurrence strictly after that instant, or none when the rule is exhausted; this is the read a caller needs to answer when does this run next without materialising a window | sourced | `F-b3-15` "RFC 5545 recurrence rules" |
| declare | a unit of work, its schedule as one recurrence string, and its manual trigger as a typed input schema | both registered as sibling entries on that one unit, so the same unit can be reached by the clock and by a person without two declarations and without two code paths | sourced | `X-entry-composition-044`, `X-entry-composition-045` "workflow_dispatch triggers the workflow manually from the Actions tab in the repository" |
| fire | one occurrence instant and the unit it belongs to | the platform's standard entry envelope of kind schedule, carrying the occurrence instant, the actor and delegation chain of whoever declared the schedule, correlation, a budget ceiling and an idempotency key derived from unit plus occurrence instant; the evaluator hands over the envelope and executes nothing itself. cap-errors states the same record (T-t6-02) for its own boundary; this row is that rule's consequence at the schedule door | sourced | `T-t6-02`, `F-b3-08` "All four enter through the same shape." |

### Shapes (JSON Schema 2020-12)

**ScheduleDeclaration (summary shape; the full schema, the rule-part subset and the vector corpus are in references/recurrence-vectors.md)** (sourced; sources: `X-entry-composition-049`, `X-entry-composition-045`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:declaration:0.1",
  "title": "ScheduleDeclaration",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "unit_ref",
    "recurrence",
    "starts_at",
    "timezone",
    "catch_up"
  ],
  "properties": {
    "unit_ref": {
      "type": "string",
      "minLength": 1,
      "description": "The one unit of work this schedule and its sibling manual trigger both reach."
    },
    "recurrence": {
      "type": "string",
      "pattern": "^FREQ=[A-Z]+(;[A-Z]+=[^;]+)*$",
      "description": "One RFC 5545 recurrence rule, as a single string."
    },
    "starts_at": {
      "type": "string",
      "format": "date-time",
      "description": "The instant the rule counts from; without it a rule has no anchor."
    },
    "timezone": {
      "type": "string",
      "pattern": "^[A-Za-z]+/[A-Za-z_+-]+$|^UTC$",
      "description": "IANA zone. Required, because the occurrence set is undefined at a clock change without it."
    },
    "catch_up": {
      "enum": [
        "skip",
        "fire_once",
        "fire_all"
      ],
      "description": "Declared policy for occurrences missed while the evaluator was down."
    },
    "trigger": {
      "type": "object",
      "description": "The sibling manual entry: a typed input schema the surface renders. Absent means the unit has no manual trigger."
    }
  }
}
```

**OccurrenceSet (summary shape; what occurrences returns and what a test vector asserts against)** (sourced; sources: `F-b3-15`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:occurrences:0.1",
  "title": "OccurrenceSet",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "recurrence",
    "timezone",
    "window",
    "occurrences"
  ],
  "properties": {
    "recurrence": {
      "type": "string"
    },
    "timezone": {
      "type": "string"
    },
    "window": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "from",
        "to"
      ],
      "properties": {
        "from": {
          "type": "string",
          "format": "date-time"
        },
        "to": {
          "type": "string",
          "format": "date-time"
        }
      }
    },
    "occurrences": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "date-time"
      },
      "description": "Ascending, de-duplicated, half-open on the window: from is included, to is not."
    },
    "truncated": {
      "type": "boolean",
      "description": "True when the rule is unbounded and the window was capped rather than exhausted."
    }
  }
}
```

**The failure you handle (proposed): problem details, measured [caller's view, folded from cap-scheduling-use]** (proposed; sources: `F-b3-13`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:example:problem",
  "title": "A rejected schedule entry",
  "$ref": "urn:agentic:problem:0.1",
  "description": "cap-errors owns this shape and its registry; scheduling adds no failure format of its own. Measured in examples/end-to-end on 2026-09-03 by changing the schedule entry's kind to a private one: exit code 2, media type application/problem+json, nothing executed and nothing written.",
  "examples": [
    {
      "type": "urn:agentic:problem:document-invalid",
      "title": "Envelope failed schema validation",
      "status": 422,
      "detail": "$.kind: must be one of ['human', 'event', 'schedule', 'external']",
      "retryable": false,
      "instance": "entries/schedule.json"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The recorded row for this capability names RFC 5545 recurrence rules as the standard, an orchestrator's own schedules as the adapter today, and cron or any RFC 5545 parser as the swap candidates. | sourced | `F-b3-15`, `E-capability-scheduling`, `E-swap-candidate-cron`, `E-swap-candidate-any-rfc-5545-parser` "cron · any RFC 5545 parser" |
| A schedule is declared as one string and nothing more: the recurrence rule grammar defined in RFC 5545 describes a repeating schedule as a single string, so the declaration is portable between adapters, diffable in review, and small enough to sit on the unit it belongs to. | sourced | `X-entry-composition-049`, `X-cap-scheduling-002` "describes a repeating schedule as a single string" |
| Proposed: evaluating a rule is a pure function of rule, anchor, time zone and window. It reads no clock, holds no cursor and writes nothing, so an occurrence set is reproducible from its inputs alone and a test vector is a complete specification of a case. agentic-stack states design rule 5 for planning (F-b1-06); this is the same shape of claim applied to recurrence, and it is ours, not PASS.md's. Research query: has a pure occurrences() function actually been run against the vector corpus in step 4 on both the RFC 5545 adapter and a second, cron-based adapter, and shown to give the same answer, or is purity still an assumption? | proposed | `F-b1-06`, `F-b3-15` |
| A firing schedule is one of TARGET T6.2's four entries, not a fifth privileged way in: a human, an event, a schedule (time), and an external system or agent all enter through the same shape, so an occurrence produces the standard entry envelope and inherits identity, correlation, budget and idempotency from it. cap-errors states the same record (T-t6-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t6-02` "All four enter through the same shape." |
| Prior art on file shows one widely used system declaring the clock and the person as siblings under a single trigger key: push triggers the workflow on code pushes to the repository, while schedule triggers the workflow at specific times or intervals, and workflow_dispatch triggers the workflow manually. | sourced | `X-entry-composition-044` "schedule triggers the workflow at specific times or intervals, and workflow_dispatch triggers the workflow manually" |
| Proposed, generalising that prior art into our rule: a schedule and a manual trigger are sibling entries declared on the same unit, the schedule as one recurrence string and the trigger as a typed input schema the surface renders, and both produce the same envelope. A re-run button that reaches the unit by another path is a second implementation of entry that will drift. | sourced | `X-entry-composition-044`, `X-entry-composition-045`, `T-t1-03` "A widely-used system exposes git event, schedule and human trigger as sibling entries under one declaration key." |
| The grammar is chosen for portability rather than expressiveness alone: RRULEs are understood by Google Calendar, Outlook, Apple Calendar and most scheduling software because they are part of the iCalendar standard RFC 5545, so a declared schedule can be read by tools the platform does not own. | sourced | `X-cap-scheduling-004` "RRULEs are understood by Google Calendar, Outlook, Apple Calendar and most scheduling software because they are part of the iCalendar standard RFC 5545." |
| Proposed: the time zone is part of the rule's meaning, not deployment configuration. Two occurrence sets computed from the same rule in different zones legitimately differ, and at a daylight-saving transition a rule evaluated without a declared zone has no defined answer at all, which is exactly where a fixed-interval substitute looks correct and is not. Research query: does RFC 5545 itself state that an RRULE without a paired time zone (a 'floating' time, in its terms) is legitimately ambiguous at a DST transition, which would source this row directly instead of by inference from the standard's existence? | proposed | `F-b3-15` |
| All three of TARGET T1's ways in reach a scheduled unit the same way. A human reaches it through the sibling manual trigger, an agent or external system reaches it by submitting the same envelope, and an internal or external event must be able to enter the system on the same shape; the clock is a fourth producer of that one envelope, not a fourth door. this skill cites TARGET T6.2's four entries for the envelope itself; this row is about the three ways a caller reaches an already-scheduled unit. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: swapping the evaluator behind the interface, changing a catch-up policy, or adding a new entry kind changes nothing in a unit that declared one recurrence string, because the string is the only thing it was ever asked for. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: this interface never executes work. It answers when, and hands an envelope to the entry path; anything that runs, retries or checkpoints belongs to the capabilities that own those things. An interface that both decides and executes cannot be swapped for a library. Research query: does the F-b3-15 adapter-today row's own workflow orchestrator already separate the 'when' decision from execution in its API, which would confirm this split is an existing seam rather than one this skill is drawing fresh? | proposed | `F-b3-15` |
| No adapter-shaped handle is exposed. No schedule identifier minted by an orchestrator, no cron string, no scheduler cursor and no paused or unpaused engine state appear in the contract; the declaration and the occurrence set are the whole surface. agentic-stack and cap-errors both state the rule this follows (F-part-c-09). | sourced | `F-part-c-09` "Products belong in the adapter column only." |
| The criterion a result will be judged against never rides on a schedule declaration or on a fired envelope. agentic-stack states design rule 6 (F-b1-07); the consequence here is only that a recurring unit gets no privileged view of its own grading. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Declare each recurring unit's schedule as one recurrence rule string stored on the unit, with its anchor instant and its IANA time zone beside it. Do not decompose the rule into fields of our own. | The recurrence rule grammar defined in RFC 5545 describes a repeating schedule as a single string, so one field carries the whole intent and moves between adapters unchanged. A decomposed rule is a second grammar to maintain and to translate. | sourced | `X-entry-composition-049` "describes a repeating schedule as a single string" |
| 2 | Declare the manual trigger next to it as a typed input schema on the same unit, and let the surface render that schema rather than building a form. | Proposed, generalised from prior art on file where you can optionally specify inputs, which GitHub will present as form elements in the UI. A declared schema gives the human entry the same validation the envelope already gets, and keeps the clock and the person on one unit instead of two. | sourced | `X-entry-composition-045`, `X-entry-composition-044` "You can optionally specify inputs, which GitHub will present as form elements in the UI." |
| 3 | Implement occurrences and next_after as pure functions and keep every clock read, cursor and store write outside them, in a thin ticker that asks the pure function what is due. | Proposed separation. Deciding when is testable offline against fixed vectors; doing the work is not. Fusing the two is what makes recurrence untestable and ties it to whatever process happens to be running. Research query: has this repository's own reference adapter over F-b3-15's RFC 5545 parser actually been split into a pure occurrences() and a separate ticker, or does the current adapter still fuse deciding and doing? | proposed | `F-b3-15` |
| 4 | Build the vector corpus before choosing an evaluator, and require it to contain at least a spring-forward transition, a fall-back transition, 29 February in a leap year, and a rule using BYSETPOS. | Proposed acceptance corpus, from docs/decomposition.md section 3.2 row P14. A fixed-interval substitute passes everything else: the four cases above are precisely the ones where counting seconds and evaluating the rule give different answers, so a corpus without them cannot tell the two apart. Research query: does the RFC 5545 conformance guidance name spring-forward, fall-back, 29 February and BYSETPOS as the standard's own recommended edge cases, or is this corpus assembled independently of any published test-vector set? | proposed | `F-b3-15` |
| 5 | Require an explicit time zone on every declaration and refuse a rule that arrives without one; treat UTC as a value someone chose, never as a fallback applied on their behalf. | Proposed. A missing zone is not a small omission: it is the difference between an occurrence set that is defined at a clock change and one that is not, and a silent default hides the choice at exactly the moment the vectors in step 4 are designed to expose. Research query: does RFC 5545 require a VTIMEZONE or TZID component on a recurring rule, which would make refusing an unzoned rule a spec-conformance check rather than a policy this skill adds? | proposed | `F-b3-15` |
| 6 | Ship the pair recorded for this capability and make the axis explicit: an in-engine schedule owned by an execution engine, and a standalone evaluator that computes occurrences and enqueues them. Record how their execution models differ, not merely that there are two. | build-adapter-pair and agentic-stack state design rule 3: every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing. What is new here is the axis: whether firing is coupled to the engine that executes, or is a separate process that only decides. | sourced | `F-b1-04`, `F-b3-15` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing" |
| 7 | On firing, build the standard entry envelope: kind schedule, the occurrence instant as the time it occurred, the declaring actor and delegation chain, correlation, a budget ceiling, and an idempotency key derived from unit plus occurrence instant. Then hand it to the ordinary entry path. | All four enter through the same shape, so a schedule that opens its own path would be a fourth entry the cross-cutting concerns are not applied to. Deriving the key from the occurrence instant also makes a double fire and a catch-up replay the same request rather than two. cap-errors states the same record (T-t6-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t6-02`, `F-b3-08` "All four enter through the same shape." |
| 8 | Return an unparseable rule, an unsupported rule part or a rule with no occurrences in the requested window as a typed problem from cap-errors' registry, and never as a log line or an empty result that reads like success. | cap-errors owns the failure shape and the closed registry for this platform (F-b3-13); the consequence here is that the three ways a declaration can be wrong must be distinguishable by a caller, because an empty occurrence set is a legitimate answer and a rejected rule is not. | sourced | `F-b3-13`, `F-b4-07` "RFC 9457 problem details" |
| 9 | Put one recurrence rule string on the unit, with the instant it counts from and an IANA time zone beside it. Write the zone even when it is UTC. | Proposed usage of the contract this skill states (F-b3-15, X-entry-composition-049): the rule is one string and the zone is part of its meaning. For you the consequence is small - two extra fields - and the job no longer drifts by an hour twice a year. | sourced | `F-b3-15`, `X-entry-composition-049` "RFC 5545 RRULE is a portable, single-string schedule declaration usable as a schedule entry point." |
| 10 | Open references/recurrence-vectors.md when you need the full declaration schema, the vector corpus with its expected occurrence sets, or the rule-part subset each adapter must support. This skill body is enough to judge an implementation without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The vector table is long material and a reader deciding where recurrence lives does not need it yet. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Test any candidate evaluator across the whole frequency range before adopting it, because the FREQ rule part identifies the type of recurrence rule with valid values including SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, and YEARLY: an implementation that only handles the middle of that range fails on the rules people actually write for month ends. | sourced | `X-cap-scheduling-003` "The FREQ rule part identifies the type of recurrence rule with valid values including SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, and YEARLY" |
| Use readability as a design check: FREQ=WEEKLY;BYDAY=MO means every Monday, and a rule a reviewer can read aloud is a rule whose intent can be checked in review rather than only in production. | sourced | `X-cap-scheduling-002` "For example FREQ=WEEKLY;BYDAY=MO means every Monday." |
| Treat the wider ecosystem as an acceptance test rather than a nice-to-have: RRULEs are understood by Google Calendar, Outlook, Apple Calendar and most scheduling software, so a rule those tools cannot read is a rule the platform has quietly extended, and the extension will not survive a swap. | sourced | `X-cap-scheduling-004` "RRULEs are understood by Google Calendar, Outlook, Apple Calendar and most scheduling software" |
| Proposed: a schedule is not a trusted actor. The fired envelope names the schedule as its subject and carries the delegation chain back to the person or service that declared it, so an audit of what a recurring job did never dead-ends at the clock. Research query: does xc-audit-trail or xc-identity-delegation's own skill state this same non-actor rule for a schedule specifically, which this row could cite by name instead of restating the delegation-chain requirement? | proposed | `T-t2-03` |
| Proposed: make catch-up a declared field with three answers (skip, fire once, fire all) rather than a property of whichever evaluator is running. An outage is when the difference between those answers costs money, and that is the worst moment to discover which one an adapter chose. Research query: does the workflow-orchestrator adapter's own scheduling feature on file (X-cap-scheduling-005/006) document a catch-up policy with exactly these three answers, which would source the enum directly instead of this row inventing it? | proposed | `F-b3-15` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-temporal-schedules` | today | Temporal schedules: the recurrence lives inside the workflow orchestrator as a schedule object, the orchestrator owns the firing timer, and firing starts a workflow execution inside the same engine. It maps declare and fire; it does not offer occurrences or next_after as a pure call a test can drive offline. | Cannot decide when anything is due while that engine is unavailable, and PASS.md A6 records exactly that state: data directory present; server not listening on `7233`/`8233`. Its calendar expression is also the engine's own, since there are two kinds of Schedule Spec: a simple interval like every 30 minutes, and a calendar-based expression similar to cron expressions, so a declared RFC 5545 rule is translated rather than evaluated and the translation is where BYSETPOS and daylight-saving cases are lost. | Keep the declaration as the single recurrence string and move only who reads it: register the same string with the engine today, and hand it to the standalone evaluator tomorrow, with no change to the unit's declaration. cap-scheduling-implement owns the migration steps and the per-adapter conformance subset; this row records the roles PASS.md B3 fixes and the axis the pair differs on. | claimed | `F-b3-15`, `F-a6-02`, `X-cap-scheduling-006`, `E-adapter-temporal-schedules` "Temporal schedules" |
| `E-swap-candidate-any-rfc-5545-parser` | second | A standalone RFC 5545 evaluator driving a queue: a library computes the occurrence set from rule, anchor, zone and window as a pure call, a thin ticker enqueues one message per occurrence, and any consumer of that queue turns the message into the standard entry envelope. The recorded swap candidates for this row are cron · any RFC 5545 parser, and cron is deliberately not the one chosen, because a fixed-interval expression is the substitute the definition of done below is built to catch. | Cannot execute, resume or checkpoint anything, and needs a queue and a consumer that the in-engine schedule does not. That is the axis: the first adapter's timer is coupled to the engine that executes the work and fires inside it, while the second only decides and is a separate process from anything that runs, so an interface that both pass cannot have been shaped around either. | Select the adapter by configuration only, with no code edit between runs, and run the identical vector corpus against each; the merged report must show adapters_run >= 2. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is that the same corpus is the swap test and the correctness test, because a rule evaluator has no state to compare. | claimed | `F-b3-15`, `F-b1-04`, `E-swap-candidate-cron` "cron · any RFC 5545 parser" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/scheduling/test.sh && python3 harness/scheduling/conformance.py --vectors --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at d6473df: exit 0; last lines: # adapter standalone-evaluator vectors_run=43 mismatches=0 corpus_covers=['bysetpos', 'dst_back', 'dst_forward', 'leap_day'] unsupported_parts=[] \| conformance PASSED (vectors): 2 binding(s) |
| Deliberate breakage | In harness/scheduling/interface.py idempotency_key(), mint the key from the wall clock instead of unit and occurrence, run the criterion (the replay case fails on both adapters while the vector corpus still shows mismatches 0, and the gate exits 1), then git checkout harness/scheduling/interface.py. |
| Expected failure | Measured by tools/measure.py at d6473df: exit 1; last lines:   File "<stdin>", line 14, in <module> \| AssertionError: the breakage pattern was not found; test.sh is out of sync with interface.py |
| Status | measured |
| Evidence | `F-b3-15`, `F-b1-04`, `F-a6-02` "cron · any RFC 5545 parser" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `cap-scheduling-implement` | Turn the contract in cap-scheduling into something that runs here: one declaration, two adapters whose execution models differ, a ticker that reads the clock in one place, and every firing entering through the ordinary path. | `references/cap-scheduling-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-evidence`, `build-skill-authoring`, `cap-errors`

Used by: `cap-human-interaction`, `cap-provenance`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the platform accept the full RFC 5545 recurrence grammar, or a documented subset that every adapter must support? | Run the vector corpus against each candidate evaluator and record which rule parts each cannot evaluate; if the failing set is small and unused by any declared schedule, a written subset is the honest answer, and if an adapter fails a part that real schedules use, that adapter is not a member of the pair. | Accept the full grammar in the declaration and publish a per-adapter conformance subset, refusing at declare time any rule part the selected adapter cannot evaluate rather than accepting it and firing at the wrong time. | `F-b3-15` "RFC 5545 recurrence rules" |
| When the evaluator was down across one or more firings, does the schedule fire late, fire once, or skip? | Across the recurring units actually declared, count how many are idempotent reconciliations, where firing late is harmless, against how many are notifications or reports, where a burst of late firings is worse than a miss. | Proposed: catch_up is a required declared field with skip as the value chosen when the author does not decide, and every catch-up firing keeps the idempotency key derived from its own occurrence instant so a late fire and a normal fire of the same occurrence are one request. | `F-b3-15` |
| Where does the occurrence-instant clock come from once evaluation is pure, and who owns the ticker that asks it? | Measure, for a window of declared schedules, the drift between the instant an occurrence was computed for and the instant its envelope actually entered, under each adapter; the number that matters is the worst case, not the mean. | Proposed: a single ticker per deployment asks the pure evaluator for the occurrences in a short forward window and enqueues them, so the clock is read in one place and the evaluator stays testable offline. | `F-b3-15` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-scheduling 2831cb4f, 2026-09-03 |
