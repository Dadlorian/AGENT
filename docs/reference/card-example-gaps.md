# Card / example gap report

Source: `docs/reference/card-example-map.json` (hand mapping, `origin: proposed`
on every row), checked by `python3 tools/check_card_example_map.py` ->
`40 entries checked, 40 cards in the model, 8 example areas, 23 litmus sections, 0 errors`.

`examples/end-to-end/` is excluded throughout: it is the original reference the
seven areas build on, not one of the seven user-view areas the owner's question
is about ("the seven example areas are too simplistic").

Inclusion test used for every row of the map: an area is credited with a card
only when that area's own README proves something about that card's specific
subject — a named run-steps command, an Extension-points row backed by a
differential run, or a recorded gap — not merely because the area happens to
touch the door, capability or record shape in passing. 13 of the 40 cards have
no profile under `docs/reference/cards/`, so those rows rest on the card's name
and sub-line in `reference-model.json` alone and are lower-confidence.

## 1. Cards with no example (8 of 40)

| Address | Card | Why no area earns it |
|---|---|---|
| 1.4 | External Event | every area's "external" door is `agent:partner-*` (card 1.5), not a webhook/queue from outside the platform |
| 2.4 | Workflow & Dispatch | the card bundles four concerns (schedule, durable state, route, handoff) that this repo already keeps separate and that the seven areas demonstrate individually under 1.2/4.3/3.2/3.1 |
| 3.4 | Workspace | no area exercises a mutable shared workspace; mounts are read-only, output is sealed write-once |
| 4.2 | Compute Resources | run's own gap #8 says its fleet of 50 is threads in one process, not machines, and measures no per-sandbox cost |
| 4.4 | Context / Memory Handling | no area reads or writes a memory or retrieval store; watch's gap G1 says a turn exposes only a frame count |
| 7.1 | Analyze | no area mines failures into named opportunities; improve's metric selection (furthest-from-target) is not failure analysis |
| base.3 | Knowledge | no area retrieves from a shared corpus; evaluation cases are a fixed replay set, not RAG |
| rail.7 | Operations | no area runs a deploy, monitor loop or incident response |

## 2. Distribution across the seven areas (the crux)

| Area | Raw card count | Distinctive (cards unique to it) |
|---|---|---|
| ask | 10 | 4 |
| run | 12 | 5 |
| watch | 6 | 1 |
| steer | 7 | 1 |
| progress | 6 | **0** |
| done | 9 | 6 |
| improve | 8 | 3 |

The areas are not evenly cut. `run` carries twice the raw load of `watch` or
`progress` (12 vs. 6). More striking than the raw column: **progress owns zero
cards outright** — every one of its 6 cards (1.2, 2.3, 4.3, 5.1, 6.2, rail.4) is
also demonstrated by another area, despite `progress` having the longest README
(234 lines) and the most extension-point rows (9) of any area. `watch` and
`steer` each own exactly one card (6.1 Telemetry and rail.2 Governance
respectively) — their remaining cards are all shared. `done` is the most
self-contained area (6 of 9 cards unique to it: 5.2, 5.3, 6.3, base.1, base.2,
base.4), and `ask` and `run` are the next most self-contained.

## 3. Cards demonstrated by more than one area (12 of 40)

| Address | Card | Areas |
|---|---|---|
| 1.2 | Scheduled | ask, progress, done |
| 2.2 | Policy | ask, run, steer |
| 2.3 | Planning | ask, run, watch, steer, progress, improve |
| 3.3 | Runtime / Sandbox | run, steer, watch |
| 4.1 | Isolated Runtime Profiles | run, steer |
| 4.3 | State & Recovery | progress, steer, improve |
| 5.1 | Validation | run, progress, improve |
| 6.2 | Evaluation Data | progress, improve |
| rail.1 | Security | ask, done |
| rail.3 | Reliability | ask, run, watch |
| rail.4 | Cost Management | ask, run, watch, steer, progress, improve |
| rail.5 | Data Privacy | watch, done |

Two of these (2.3 Planning, rail.4 Cost Management) are demonstrated by six of
the seven areas — both are platform-applied guarantees (pure pre-execution
planning, ceiling enforcement) that every area's README shows independently
rather than a seam specific to one area. The other ten overlaps cluster in
pairs the reference model itself keeps as separate cards even though one
example mechanism proves both: `harness/containment` alone is the entire
evidence base for both 3.3 Runtime/Sandbox and 4.1 Isolated Runtime Profiles
(run's step 9 and steer's section 6 are the only differentials either card
has); 4.3 State & Recovery and base.4 Metadata & State both describe the
durable-execution/state-persistence pairing the card 4.3 profile itself says
this repo "keeps as separate skills"; and 2.2 Policy vs. rail.2 Governance
split one decision point (steer's `Gate.gated()`) into a single-call card and
a cross-cutting-posture card.

## 4. Do the seven areas map cleanly onto the model's nine?

No. Every area but `ask` reaches four to six of the model's nine areas:

| Example area | Model areas it touches |
|---|---|
| ask | Invocation / Entry Points, Orchestration & Control Plane, Cross-Cutting Concerns (3) |
| run | Core Agent, Orchestration & Control Plane, Execution & Runtime, Assurance & Completion, Shared Platform Services, Cross-Cutting Concerns (6) |
| watch | Core Agent, Orchestration & Control Plane, Observe, Cross-Cutting Concerns (4) |
| steer | Core Agent, Orchestration & Control Plane, Execution & Runtime, Cross-Cutting Concerns (4) |
| progress | Invocation / Entry Points, Orchestration & Control Plane, Execution & Runtime, Assurance & Completion, Observe, Cross-Cutting Concerns (6) |
| done | Invocation / Entry Points, Assurance & Completion, Observe, Shared Platform Services, Cross-Cutting Concerns (5) |
| improve | Orchestration & Control Plane, Execution & Runtime, Assurance & Completion, Observe, Self-Improvement, Cross-Cutting Concerns (6) |

Only `ask` is close to one model area (Entry Points) plus incidental spillover.
Every other area is a vertical slice through most of the journey (spine, loop,
rail and base all at once) rather than a horizontal slice matching one of the
model's nine boxes. The seven areas and the nine model areas are two different
partitions of the same territory, cut on different axes: the reference model
cuts by *layer* (what kind of thing), the seven examples cut by *user question*
(what does the caller see happen). Cross-Cutting Concerns is the one model area
every single example area touches — unsurprising, since concerns are
platform-applied everywhere by design.

## 5. Opinion (mine, not sourced)

The seven areas are the right seams for their stated purpose — showing a
caller "what do I see happen" at each point of one unit's life — but they are
the wrong seams for **capability coverage**, which is what the reference model
measures. `progress` owning zero cards outright is the sharpest symptom: it is
the richest single README by extension-point count, yet every mechanism it
demonstrates (scheduling, checkpoint/resume, evaluation gates, planning,
budget) is also shown somewhere else, narrower and often more clearly (ask's
idempotency differential is a tighter proof than progress's; steer's
checkpoint/restart is a tighter proof of 4.3 than progress's crash test, which
the area's own gap G1 admits is single-process only). Meanwhile 8 of 40 cards
have no proof anywhere in the seven areas, and they are not a random 8: as of
this reading of `reference-model.json` (a file under active correction
elsewhere in this session — re-check before relying on the exact split), 5 of
the 8 (External Event, Workflow & Dispatch, Context/Memory Handling, Analyze,
Knowledge) are marked `planned` rather than `built`, so the examples' silence
there plausibly reflects the platform's own build status rather than an
authoring gap. The other 3 (Workspace, Compute Resources, Operations) are
marked `built`, so their silence in the seven areas is not explained by build
status at all — no example's door or scenario was ever built to reach them,
independent of what the underlying capability has shipped. If the owner's goal is "one example area per capability the model
tracks," a better seam would follow the model's own boundary between the
spine (1-5, one path a unit walks) and the rail (cross-cutting, checked once
per area) — e.g. one area per spine stage (entry+intake, agent+execute,
assure) plus one area that exhaustively drives every rail card once, rather
than the current seven areas each re-deriving planning and budget enforcement
from scratch. That would trade the current "user question" framing for a
"capability coverage" framing; the two are not the same goal, and the seven
areas were built for the first one.
