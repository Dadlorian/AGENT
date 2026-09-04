# Scheduling adapters: mapping, failure modes, migration runbook

Proposed reference material for `cap-scheduling-implement`. The skill body is enough to build either
adapter without this file; open it when you are filling in the mapping table, deciding what a given
adapter can detect, or executing the migration.

Ids resolve with `python3 tools/kb.py show <id>`. The recorded row for this capability is `F-b3-15`.

## 1. Mapping table

| Interface call | In-engine schedule (today, `E-adapter-temporal-schedules`) | Standalone evaluator (second, `E-swap-candidate-any-rfc-5545-parser`) |
|---|---|---|
| `occurrences(rule, anchor, zone, window)` | Not offered as a pure call; the engine's schedule object owns its own expansion. Served by the platform evaluator even when this adapter is selected. | The whole point: a library call, no clock, no store. |
| `next_after(rule, anchor, zone, instant)` | Not offered. | Same library, single result. |
| `declare(unit, recurrence, trigger)` | Registers the declared string with the engine and stores the returned handle inside the adapter. | Writes the declaration and nothing else; the ticker discovers it. |
| `fire(occurrence)` | The engine's timer fires and calls back; the adapter maps the callback onto the shared envelope builder. | The ticker enqueues one message per occurrence; a consumer calls the same builder. |

## 2. What each adapter can and cannot detect

| Condition | In-engine schedule | Standalone evaluator |
|---|---|---|
| Rule part the adapter cannot evaluate | Detected only if the translation to the engine's own expression is checked; otherwise it fires approximately. Record it in `unsupported_parts` at declare time. | Detected by the library at parse time, before the declaration is accepted. |
| Daylight-saving transition handled wrongly | Not detectable from inside the adapter; only the vector corpus shows it. | Same: the corpus is the detector, which is why the corpus is written first. |
| Missed occurrences during an outage | The engine's own catch-up behaviour applies, whatever it is. | The ticker's next window sees them; `catch_up` decides what happens. |
| Duplicate firing | Absorbed downstream by the idempotency key derived from unit plus occurrence instant. | Same mechanism, same key. |
| Firing while the execution engine is down | Impossible: firing and executing are the same engine. | Firing continues; the queue holds the envelopes. |

## 3. Migration runbook (proposed)

Each step is revertible because the declaration never changes.

1. **Declare, do not fire.** Write every recurring unit's declaration: recurrence string, anchor,
   zone, `catch_up`, actor, budget, and the sibling manual trigger's input schema. Validate them
   against `ScheduleDeclaration`. Nothing fires yet. Revert: delete the declarations.
2. **Corpus green.** Run the vector corpus against the standalone evaluator until `mismatches == 0`
   with all four corpus classes present. Revert: nothing is live.
3. **Fire through the ordinary path.** Turn on the ticker. Every occurrence becomes an entry envelope
   built by the one shared builder and enters exactly as a human, an event or an external system
   does. Revert: stop the ticker; declarations remain.
4. **Add the second adapter.** Register the same declared strings with the engine, map its callback
   to the same builder, and add `adapter` to the deployment configuration. Run the corpus a second
   time with `--adapter in-engine-schedule`. Revert: change one configuration value back.
5. **Keep both.** Do not delete either adapter. An interface with one surviving implementation drifts
   into the shape of whatever runs, which is the failure the pair exists to prevent (`F-b1-04`).

## 4. What a passing run does not prove

- It does not prove either adapter fires on time; it proves both compute the same occurrence sets.
  Drift between the occurrence instant and the envelope's arrival is a separate measurement, and it
  is the subject of the first open question in the skill body.
- It does not prove the engine adapter works at all: PASS.md A6 records the engine as not listening
  (`F-a6-02`), so its results stay claimed until a run against a listening server exists.
