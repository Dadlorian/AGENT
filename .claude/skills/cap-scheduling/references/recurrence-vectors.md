# Recurrence vectors and the full declaration schema

Proposed reference material for `cap-scheduling`. The skill body is enough to judge an
implementation without this file; open it when you are building the vector corpus, writing the
declaration validator, or deciding what rule parts an adapter must support.

Every id resolves with `python3 tools/kb.py show <id>`.

## 1. The four vector classes that separate a rule evaluator from a fixed interval

Proposed, from `docs/decomposition.md` section 3.2 row P14. A fixed-interval substitute that adds a
constant period to the previous firing passes almost every other case, so a corpus without these
four cannot tell the two implementations apart.

| Class | Why it separates them | What a fixed interval does instead |
|---|---|---|
| `dst_forward` | A wall-clock rule in a zone that springs forward has one fewer real hour that day; the occurrence stays at the declared local time. | Fires one hour off, and stays off until the next transition. |
| `dst_back` | The repeated local hour must yield one occurrence, not two. | Fires twice, or once at the wrong instant. |
| `leap_day` | A yearly rule anchored on 29 February has occurrences only in leap years. | Produces 1 March, or an occurrence every year. |
| `bysetpos` | Rules such as the last working day of the month are positional within a set, not periodic. | Cannot express the rule at all; the computed set is empty. |

Each vector is `{recurrence, starts_at, timezone, window: {from, to}, expected: [instant, ...]}` and
asserts set equality against `OccurrenceSet.occurrences`. The definition of done requires
`vectors_run > 40` and all four classes present.

## 2. Full ScheduleDeclaration schema (proposed)

The summary shape in `contract.shapes` carries the required fields. The full form adds the sibling
manual trigger, which `X-entry-composition-045` records as a declared input schema the surface
renders, and the fields the entry envelope needs at fire time.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:schedule:declaration:0.1",
  "title": "ScheduleDeclaration",
  "type": "object",
  "additionalProperties": false,
  "required": ["unit_ref", "recurrence", "starts_at", "timezone", "catch_up", "actor"],
  "properties": {
    "unit_ref":   {"type": "string", "minLength": 1},
    "recurrence": {"type": "string", "pattern": "^FREQ=[A-Z]+(;[A-Z]+=[^;]+)*$"},
    "starts_at":  {"type": "string", "format": "date-time"},
    "ends_at":    {"type": ["string", "null"], "format": "date-time"},
    "timezone":   {"type": "string"},
    "catch_up":   {"enum": ["skip", "fire_once", "fire_all"]},
    "actor": {
      "type": "object",
      "required": ["subject", "delegation_chain"],
      "description": "Who the firing acts for. A schedule is not a trusted actor; the chain ends at a person or a service."
    },
    "budget": {
      "type": "object",
      "required": ["ceiling_micros", "currency", "on_exceed"],
      "description": "Carried onto every fired envelope. Not declinable."
    },
    "trigger": {
      "type": "object",
      "additionalProperties": false,
      "required": ["input_schema"],
      "properties": {
        "input_schema": {"type": "object", "description": "JSON Schema 2020-12. The surface renders it as the manual entry form."},
        "label":        {"type": "string"}
      }
    }
  }
}
```

## 3. Rule-part subset (proposed)

`X-cap-scheduling-003` records the `FREQ` values as `SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY,
MONTHLY, and YEARLY`. Open question 1 in the skill body leaves the accepted subset undecided; until
it is decided, an adapter publishes the parts it evaluates and the declaration is refused at declare
time for any part that adapter cannot handle.

| Group | Parts | Notes |
|---|---|---|
| Frequency | `FREQ`, `INTERVAL` | Every adapter must support all seven `FREQ` values or say which it does not. |
| Bounds | `COUNT`, `UNTIL` | Mutually exclusive. `UNTIL` is an instant, so it needs the zone too. |
| Day and date selection | `BYDAY`, `BYMONTHDAY`, `BYMONTH`, `BYYEARDAY`, `BYWEEKNO` | The common cases. |
| Positional | `BYSETPOS` | The part a fixed interval cannot express; required by the vector corpus. |
| Week start | `WKST` | Changes which week a `BYDAY` occurrence falls in near year boundaries. |

## 4. What is deliberately not in the declaration

- No adapter handle: no orchestrator-minted schedule id, no cron string, no scheduler cursor.
- No execution detail: retries, checkpoints and step keys belong to other capabilities.
- No criterion: a recurring unit gets no privileged view of how it will be graded.
