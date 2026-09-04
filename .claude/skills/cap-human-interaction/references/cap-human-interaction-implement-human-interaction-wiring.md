# Human interaction: cross-cutting wiring, migration and surface checklist

Long material for `cap-human-interaction-implement`. The skill body is enough to build and judge the
surface pair; open this when you are wiring a concern, planning the cutover, or reviewing a new
surface. Everything here is **proposed** unless a kb id is named on the row.

## 1. Per-concern wiring (proposed)

Two stamping points only: the code path that parks an ask (**park**) and the code path that applies a
decision (**resume**). Anything else that writes a `ParkedAsk` is a path that bypassed them.

| Concern | At park | At resume | Refuses when |
|---|---|---|---|
| Identity (`F-b4-03`) | the run's actor is copied onto the ask | the surface's authenticated subject plus its delegation chain go on the decision | actor absent, or the subject does not match a member of `ask.audience` when one is set |
| Correlation (`F-b4-06`) | `correlation_id` copied from the run, never minted | carried unchanged onto the decision and the resumed run | ids differ between ask and decision |
| Budget (`F-b4-02`) | the run's ceiling and spend so far are attached to the ask for the reviewer to see | remaining ceiling re-checked before the run continues | remaining ceiling is zero; the run terminates rather than resuming |
| Policy (`F-b4-04`) | who may decide is evaluated once and written to `ask.audience` | re-evaluated at resume, because membership can change while an ask is open | decider is outside the audience |
| Provenance (`F-b4-05`) | the ask is appended to the evidence chain | the decision and its actor are appended | append fails; the resume does not proceed on an unrecorded decision |
| Telemetry (`F-b4-06`) | `human.ask` event with the explicit correlation attribute | `human.decided` event, plus the wall-clock time the ask was open | — |
| Idempotency (`F-b4-08`) | `resume_token` derived from `ask_id` + `correlation_id` | lease taken on the decision's `idempotency_key`; state moves `open` → `decided` in the same act | key already applied: the delivery is a `duplicate`, not an error |

## 2. Migration, one reversible step at a time (proposed)

| # | Step | Rollback |
|---|---|---|
| 1 | Stand up the parked-ask store; nothing writes to it yet | drop the store |
| 2 | Park new asks into the store as well as into the running unit's own state (dual write) | stop writing to the store |
| 3 | Point the running unit at the store for reads; its own state becomes a shadow copy | point it back at its own state |
| 4 | Move resume through the store's lease; the unit posts a `HumanDecision` | the unit posts to its old endpoint again |
| 5 | Delete the shadow copy once no open ask predates step 2 | none needed; step 5 is only taken when the set is empty |
| 6 | Add the streaming surface against the same store, selected by configuration | set the configuration back to the first surface |
| 7 | Run the four-decision fixture through both surfaces against one open ask | — |

No step edits a workflow that parks. If one does, the pause was defined in the surface's terms
(`F-b1-02`: the core imports interfaces, never implementations).

## 3. Surface conformance checklist (proposed)

A new surface is conformant when all of these hold. This is the list `--surface <name>` runs.

1. Renders every field of a stored `HumanAsk`, including `proposed.diff` and `proposed.irreversibility`.
2. Offers exactly the members of `ask.allowed_decisions`, and no others.
3. Generates its input form from `ask.response_schema` rather than from a hand-written form per workflow.
4. Posts a `HumanDecision` whose `correlation_id` is the ask's, unchanged.
5. Derives `idempotency_key` from the ask and the decision, not from the click.
6. Renders a refusal as the problem-details object it received (`F-b3-13`), including `detail`.
7. Holds no state the run needs: killing the surface between ask and decision loses nothing.
8. Reports a runtime marker naming itself, so a conformance report cannot be green for a surface that never served (`F-a7-04`).

## 4. What starts red

Nothing in section 1 can be measured today: the identity field does not exist anywhere in the system
(`F-a6-05`), the typed error registry is recorded as absent (`F-b3-13`), and the orchestrator the
signal delivery would use is recorded as down (`F-a6-02`). Every row above is therefore **claimed**
until a run produces it, per `build-evidence-record`.
