# cap-scheduling: the caller's view

Proposed. Folded in from the former `cap-scheduling-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-scheduling` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-scheduling states the contract this rests on (F-b3-15); this facet reduces it to one thing a caller does: declare when, as a single string with a time zone, on the unit that should run. Everything after that - computing occurrences, firing, identity, correlation, budget and replay safety - is the platform's work.  
  _sourced_ - `F-b3-15`, `T-t3-01` "RFC 5545 recurrence rules"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| declare a schedule (proposed) | on the unit you already have: one recurrence rule string, the instant it counts from, an IANA time zone, and a catch-up answer | the unit now runs itself; each occurrence arrives as an ordinary entry envelope of kind schedule, with the same identity, correlation, budget and idempotency fields any other entry carries | proposed | `F-b3-15`, `T-t6-02` |
| add the run-it-now sibling (proposed) | a typed input schema on the same unit, describing what a person may fill in | a rendered form on the surface and, when someone submits it, the same unit reached through the same envelope; you write no second code path and no second handler | proposed | `X-entry-composition-045`, `X-entry-composition-044` |
| ask when it next runs (proposed) | the unit reference and an instant to look from | the next occurrence, or none when the rule is exhausted; this is a pure read, so asking it in a test costs nothing and never fires anything | proposed | `F-b3-15` |
| read a rejected rule (proposed) | a recurrence string the platform will not accept, or one using a rule part the selected adapter cannot evaluate | a typed problem in the platform's failure shape with retryable false; the fix is a different rule, not a retry. An empty occurrence set is a different thing and is a valid answer, not a failure | proposed | `F-b3-13` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-scheduling` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a nightly sweep declared once and fired by the clock

_proposed_ - sources: `F-b3-15`, `T-t6-02`.

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

### Worked example 2 (proposed): the same unit started by a person, through the sibling trigger

_proposed_ - sources: `X-entry-composition-045`, `X-entry-composition-044`.

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

### The failure you handle (proposed): problem details, measured

_proposed_ - sources: `F-b3-13`.  Also carried in the body of `cap-scheduling` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-scheduling` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **If a person should also be able to start the unit on demand, declare a typed input schema beside the schedule instead of building a button that calls something else.**  
  _why:_ Proposed. cap-scheduling records the prior art for declaring the clock and the person as siblings on one unit; using it means the manual run gets the same validation, the same envelope and the same audit trail as the nightly one, and you maintain one path rather than two.  
  _proposed_ - `X-entry-composition-044`, `X-entry-composition-045`
- **Delete any code that sleeps, polls the clock, or asks whether it is time yet. Declare, and let the occurrence arrive.**  
  _why:_ Proposed. A timer inside a unit is a second scheduler with no vectors behind it, no time-zone handling and no idempotency key, and it is invisible to everything that traces what the platform did.  
  _proposed_ - `T-t2-03`
- **Read what fired from the entry envelope the unit receives - kind, occurred_at, actor and correlation - rather than from any scheduler-side API.**  
  _why:_ Proposed. The envelope is the same one the other entries carry, so anything you write to handle it keeps working when the schedule is replaced by a webhook, and when the evaluator behind the interface is swapped.  
  _proposed_ - `T-t6-02`
- **Answer catch-up deliberately when you declare: skip, fire once, or fire all. Do not leave it to whatever the platform happens to do after an outage.**  
  _why:_ Proposed. For a reconciliation, firing late is harmless; for a notification, a burst of late firings is worse than a miss. Only you know which yours is, and the outage is the wrong moment to find out.  
  _proposed_ - `F-b3-15`
- **Before declaring a rule you are unsure of, ask for its next few occurrences and read them. It is a pure read and it fires nothing.**  
  _why:_ Proposed. A wrong rule is silent until the calendar reaches the case it gets wrong, which can be months; five printed instants take a second and catch nearly every mistake worth catching.  
  _proposed_ - `F-b3-15`
- **Handle exactly one failure: a rule the platform refuses, returned in the platform's problem-details shape with retryable false. Fix the rule; do not retry it. Everything else is the ordinary answer.**  
  _why:_ cap-scheduling already routes a refused rule through cap-errors' registry rather than defining a failure of its own (F-b3-13), so a caller that already reads type and retryable needs no new branch here. An empty occurrence set is not this failure: it is a valid answer meaning the rule has nothing due in that window.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"

## Other caller invariants

- Proposed: one string and a zone are the whole obligation. There is no scheduler client to hold, no timer to run, no cursor to persist and no way to ask for or decline the cross-cutting fields the fired envelope carries; cap-scheduling fixes the contract and cap-scheduling-implement wires the firing.  
  _proposed_ - `F-b3-15`, `T-t3-01`
- A scheduled entry has no private path in, and this is checked rather than asserted. cap-scheduling states the entry rule from TARGET T6.2 (T-t6-02); what this facet adds is the measurement: the schedule envelope is validated by the same validator, against the same enumeration of entry kinds, as every other entry, and an entry kind of the scheduler's own is refused. Measured in examples/end-to-end on 2026-09-03; the run is the definition of done below.  
  _sourced_ - `T-t6-02`, `F-b3-13` "All four enter through the same shape."

## Caller practices

- Write the rule so a reviewer can read it aloud. cap-scheduling cites the same record for the grammar's readability (X-cap-scheduling-002): FREQ=WEEKLY;BYDAY=MO means every Monday, and a rule whose intent survives code review is one you will not have to debug from a calendar.  
  _sourced_ - `X-cap-scheduling-002` "For example FREQ=WEEKLY;BYDAY=MO means every Monday."
- Think of the schedule and the manual button as one named thing rather than two features: prior art on file describes an entry point that listens for a specific external event or a predefined schedule, which is the mental model that keeps non-experts from building a second path in.  
  _sourced_ - `X-entry-composition-057` "listens for a specific external event or a predefined schedule"
- Proposed: name the unit for its intent, not its cadence. A unit called nightly-sweep has to be renamed the day the rule becomes weekly, and the rename reaches logs, dashboards and everyone's muscle memory; the recurrence string already says when.  
  _proposed_ - `F-b3-15`
- Proposed: let a scheduled unit be re-runnable by hand from the start, even when nobody asks for it. The first incident is when someone needs to run the nightly job at noon, and adding the sibling trigger then is a change to a unit that is already on fire.  
  _proposed_ - `X-entry-composition-044`

## Open questions carried over

- **What does a caller see when an occurrence fired while the unit's previous run was still going?**  
  _deciding evidence:_ Count, across declared units, how often one occurrence overlaps the previous run, and whether any of those units are safe to run concurrently with themselves.  
  _default until then:_ Proposed: the second occurrence enters as an ordinary entry and the unit's own idempotency and state decide, rather than the scheduler suppressing it silently. A suppression a caller cannot see is a missed run they will look for in the wrong place.  
  `F-b3-15`

