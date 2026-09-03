---
name: cap-scheduling-use
description: How to use the Scheduling capability as a caller: write one recurrence string and a time zone on the unit of work, add a typed input schema beside it if a person should also be able to start it now, and stop writing timer code. Load it when something should happen every night, every third Tuesday or on the last working day of the month, when a job needs a run-it-now button as well as a clock, when deciding what a fired job carries and how to trace what it did, when a recurring job ran an hour late after a clock change or skipped a date, or when you are about to add a loop that sleeps and checks the time.
---

# cap-scheduling-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-scheduling states the contract this rests on (F-b3-15); this facet reduces it to one thing a caller does: declare when, as a single string with a time zone, on the unit that should run. Everything after that - computing occurrences, firing, identity, correlation, budget and replay safety - is the platform's work. | sourced | `F-b3-15`, `T-t3-01` "RFC 5545 recurrence rules" |

## Entities

| Entity |
|---|
| `E-capability-scheduling` |
| `E-standard-rfc-5545-recurrence-rules` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| declare a schedule (proposed) | on the unit you already have: one recurrence rule string, the instant it counts from, an IANA time zone, and a catch-up answer | the unit now runs itself; each occurrence arrives as an ordinary entry envelope of kind schedule, with the same identity, correlation, budget and idempotency fields any other entry carries | proposed | `F-b3-15`, `T-t6-02` |
| add the run-it-now sibling (proposed) | a typed input schema on the same unit, describing what a person may fill in | a rendered form on the surface and, when someone submits it, the same unit reached through the same envelope; you write no second code path and no second handler | proposed | `X-entry-composition-045`, `X-entry-composition-044` |
| ask when it next runs (proposed) | the unit reference and an instant to look from | the next occurrence, or none when the rule is exhausted; this is a pure read, so asking it in a test costs nothing and never fires anything | proposed | `F-b3-15` |
| read a rejected rule (proposed) | a recurrence string the platform will not accept, or one using a rule part the selected adapter cannot evaluate | a typed problem in the platform's failure shape with retryable false; the fix is a different rule, not a retry. An empty occurrence set is a different thing and is a valid answer, not a failure | proposed | `F-b3-13` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a nightly sweep declared once and fired by the clock** (proposed; sources: `F-b3-15`, `T-t6-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:example:nightly",
  "title": "A declared recurrence fires as an ordinary entry",
  "description": "The declaration is the recurrence string plus its zone; what arrives is the standard entry envelope. Reproduced in examples/end-to-end on 2026-09-03: `python3 run.py --entry entries/schedule.json` exits 0, prints `RESULT  entry=schedule  actor=schedule:nightly-fault-sweep  correlation=corr-schedule-0001`, and closes with `completed: 11 steps, spent 551800 of 1500000 micros, estimate was 750000` - the same workflow the human, event and external entries run.",
  "examples": [
    {
      "declared": {
        "unit_ref": "workflows/triage-and-fix.json",
        "recurrence": "FREQ=DAILY;BYHOUR=2;BYMINUTE=0",
        "timezone": "Europe/London",
        "catch_up": "skip"
      },
      "what_arrives": {
        "kind": "schedule",
        "actor": {
          "subject": "schedule:nightly-fault-sweep"
        },
        "occurred_at": "2026-09-03T02:00:00Z",
        "idempotency_key": "nightly-fault-sweep-2026-09-03",
        "correlation": {
          "run_id": "run-schedule-0001",
          "correlation_id": "corr-schedule-0001"
        }
      },
      "what_you_wrote": "two fields on the unit; no timer, no loop, no scheduler client"
    }
  ]
}
```

**Worked example 2 (proposed): the same unit started by a person, through the sibling trigger** (proposed; sources: `X-entry-composition-045`, `X-entry-composition-044`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:example:manual",
  "title": "Run it now, same unit, same envelope",
  "description": "The manual trigger is declared beside the schedule as a typed input schema, and the surface renders it. Submitting it produces an envelope that differs from example 1 only in kind, actor and idempotency key; nothing downstream branches on which of the two produced it.",
  "examples": [
    {
      "declared_beside_the_schedule": {
        "trigger": {
          "input_schema": {
            "type": "object",
            "required": [
              "window_hours"
            ],
            "properties": {
              "window_hours": {
                "type": "integer",
                "minimum": 1,
                "maximum": 168
              }
            }
          },
          "label": "Run the fault sweep now"
        }
      },
      "what_arrives": {
        "kind": "human",
        "actor": {
          "subject": "user:corey"
        },
        "idempotency_key": "fault-sweep-manual-2026-09-03T14:02:11Z",
        "payload": {
          "window_hours": 24
        }
      },
      "what_you_wrote": "one input schema; no form, no second handler, no second path into the unit"
    }
  ]
}
```

**The failure you handle (proposed): problem details, measured** (proposed; sources: `F-b3-13`)

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
| All three of TARGET T1's ways in reach a scheduled unit the same way. A human reaches it through the sibling manual trigger, an agent or external system reaches it by submitting the same envelope, and an internal or external event must be able to enter the system on the same shape; the clock is a fourth producer of that one envelope, not a fourth door. cap-scheduling cites TARGET T6.2's four entries for the envelope itself; this row is about the three ways a caller reaches an already-scheduled unit. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| Proposed: one string and a zone are the whole obligation. There is no scheduler client to hold, no timer to run, no cursor to persist and no way to ask for or decline the cross-cutting fields the fired envelope carries; cap-scheduling fixes the contract and cap-scheduling-implement wires the firing. | proposed | `F-b3-15`, `T-t3-01` |
| Enhancing one aspect leaves the rest untouched: swapping the evaluator behind the interface, changing a catch-up policy, or adding a new entry kind changes nothing in a unit that declared one recurrence string, because the string is the only thing it was ever asked for. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The declaration is kept to one string, one zone, one anchor and one catch-up answer because a contract that is daunting or overly complex will not be used, and a team that finds declaring a schedule expensive will write a sleep loop instead, which is the outcome this capability exists to prevent. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |
| A scheduled entry has no private path in, and this is checked rather than asserted. cap-scheduling states the entry rule from TARGET T6.2 (T-t6-02); what this facet adds is the measurement: the schedule envelope is validated by the same validator, against the same enumeration of entry kinds, as every other entry, and an entry kind of the scheduler's own is refused. Measured in examples/end-to-end on 2026-09-03; the run is the definition of done below. | sourced | `T-t6-02`, `F-b3-13` "All four enter through the same shape." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: you never see the ticker, the queue, the occurrence expansion or which adapter fired. A firing looks like an entry, which is the point; if a caller could tell the two adapters apart it would start writing code that depends on one of them. | proposed | - |
| Proposed: there is no schedule handle to pause, resume or re-point. Changing when something runs is an edit to the declared string, reviewed like any other change to the unit, rather than a live call that leaves no diff. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Put one recurrence rule string on the unit, with the instant it counts from and an IANA time zone beside it. Write the zone even when it is UTC. | Proposed usage of the contract cap-scheduling states (F-b3-15, X-entry-composition-049): the rule is one string and the zone is part of its meaning. For you the consequence is small - two extra fields - and the job no longer drifts by an hour twice a year. | proposed | `F-b3-15`, `X-entry-composition-049` |
| 2 | If a person should also be able to start the unit on demand, declare a typed input schema beside the schedule instead of building a button that calls something else. | Proposed. cap-scheduling records the prior art for declaring the clock and the person as siblings on one unit; using it means the manual run gets the same validation, the same envelope and the same audit trail as the nightly one, and you maintain one path rather than two. | proposed | `X-entry-composition-044`, `X-entry-composition-045` |
| 3 | Delete any code that sleeps, polls the clock, or asks whether it is time yet. Declare, and let the occurrence arrive. | Proposed. A timer inside a unit is a second scheduler with no vectors behind it, no time-zone handling and no idempotency key, and it is invisible to everything that traces what the platform did. | proposed | `T-t2-03` |
| 4 | Read what fired from the entry envelope the unit receives - kind, occurred_at, actor and correlation - rather than from any scheduler-side API. | Proposed. The envelope is the same one the other entries carry, so anything you write to handle it keeps working when the schedule is replaced by a webhook, and when the evaluator behind the interface is swapped. | proposed | `T-t6-02` |
| 5 | Answer catch-up deliberately when you declare: skip, fire once, or fire all. Do not leave it to whatever the platform happens to do after an outage. | Proposed. For a reconciliation, firing late is harmless; for a notification, a burst of late firings is worse than a miss. Only you know which yours is, and the outage is the wrong moment to find out. | proposed | `F-b3-15` |
| 6 | Before declaring a rule you are unsure of, ask for its next few occurrences and read them. It is a pure read and it fires nothing. | Proposed. A wrong rule is silent until the calendar reaches the case it gets wrong, which can be months; five printed instants take a second and catch nearly every mistake worth catching. | proposed | `F-b3-15` |
| 7 | Handle exactly one failure: a rule the platform refuses, returned in the platform's problem-details shape with retryable false. Fix the rule; do not retry it. Everything else is the ordinary answer. | cap-scheduling already routes a refused rule through cap-errors' registry rather than defining a failure of its own (F-b3-13), so a caller that already reads type and retryable needs no new branch here. An empty occurrence set is not this failure: it is a valid answer meaning the rule has nothing due in that window. | sourced | `F-b3-13` "RFC 9457 problem details" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Write the rule so a reviewer can read it aloud. cap-scheduling cites the same record for the grammar's readability (X-cap-scheduling-002): FREQ=WEEKLY;BYDAY=MO means every Monday, and a rule whose intent survives code review is one you will not have to debug from a calendar. | sourced | `X-cap-scheduling-002` "For example FREQ=WEEKLY;BYDAY=MO means every Monday." |
| Think of the schedule and the manual button as one named thing rather than two features: prior art on file describes an entry point that listens for a specific external event or a predefined schedule, which is the mental model that keeps non-experts from building a second path in. | sourced | `X-entry-composition-057` "listens for a specific external event or a predefined schedule" |
| Proposed: name the unit for its intent, not its cadence. A unit called nightly-sweep has to be renamed the day the rule becomes weekly, and the rename reaches logs, dashboards and everyone's muscle memory; the recurrence string already says when. | proposed | `F-b3-15` |
| Proposed: let a scheduled unit be re-runnable by hand from the start, even when nobody asks for it. The first incident is when someone needs to run the nightly job at noon, and adding the sibling trigger then is a change to a unit that is already on fire. | proposed | `X-entry-composition-044` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `cd examples/end-to-end && bash test.sh`. Section 1 runs `entries/schedule.json`, whose payload carries the recurrence `FREQ=DAILY;BYHOUR=2;BYMINUTE=0`, through the same validator and the same workflow as the human, event and external entries, and asserts exit code 0 and that the run reached completed. |
| Expected | exit 0 and a closing line `passed 29, failed 0`, with section 1 printing `ok   schedule exits 0 (0)` and `ok   schedule reached completed`; the standalone run `python3 run.py --entry entries/schedule.json` prints `RESULT  entry=schedule  actor=schedule:nightly-fault-sweep  correlation=corr-schedule-0001` and `completed: 11 steps, spent 551800 of 1500000 micros, estimate was 750000`. |
| Deliberate breakage | In `examples/end-to-end/entries/schedule.json`, change `"kind": "schedule"` to `"kind": "cronjob"`, a private entry kind of the scheduler's own. Change nothing else, and re-run the same command. |
| Expected failure | exit 1 and `passed 27, failed 2`: section 1 reports `FAIL schedule exits 0 (expected 0, got 2)` and `FAIL schedule did not complete`, and the entry's own output is problem details with media type application/problem+json, `"type": "urn:agentic:problem:document-invalid"`, `"status": 422` and `"detail": "$.kind: must be one of ['human', 'event', 'schedule', 'external']"`. The other three entries still pass, which is the useful part: the failure is exactly the schedule's attempt to enter on a shape of its own. Measured in session cap-scheduling 2831cb4f on 2026-09-03; both runs were performed and entries/schedule.json was restored. |
| Status | measured |
| Evidence | `T-t6-02`, `F-b3-13` "All four enter through the same shape." |

## Composes with

Builds on: `cap-scheduling`, `cap-scheduling-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What does a caller see when an occurrence fired while the unit's previous run was still going? | Count, across declared units, how often one occurrence overlaps the previous run, and whether any of those units are safe to run concurrently with themselves. | Proposed: the second occurrence enters as an ordinary entry and the unit's own idempotency and state decide, rather than the scheduler suppressing it silently. A suppression a caller cannot see is a missed run they will look for in the wrong place. | `F-b3-15` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-scheduling 2831cb4f, 2026-09-03 |
