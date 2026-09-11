# Reference examples

One area built, eight to go. This is the clean break from `examples/archived/`, and the structure
below is derived rather than invented: it is `docs/reference/reference-model.json`, which is itself derived
from the owner's design in `ref_arch/Reference Model.dc.html`.

An example's boundary matches a seam in the architecture, not a stage in a story. That is the whole
reason for the replacement — see `docs/reference/card-example-gaps.md` for the measurement that
justified it.

## The areas

Nine, in journey order. Numbers are the model's, not new ones.

| Dir | Area | Cards | Region |
|---|---|---|---|
| `1-invocation/` | Invocation / Entry Points | 5 | spine |
| `2-orchestration/` | Orchestration & Control Plane | 4 | spine |
| `3-core-agent/` | Core Agent | 5 | spine |
| `4-execution/` | Execution & Runtime | 4 | spine |
| `5-assurance/` | Assurance & Completion | 3 | spine |
| `6-observe/` | Observe | 3 | loop |
| `7-self-improvement/` | Self-Improvement | 4 | loop |
| `base-shared-services/` | Shared Platform Services | 5 | base |
| `rail-cross-cutting/` | Cross-Cutting Concerns | 7 | rail |

Regions matter: **spine** is the journey 1 to 5, **loop** closes 6 to 7 back onto it, **base** is
used by every layer and **rail** spans every layer. A rail example demonstrates a concern applied
across the journey, not a step in it.

`examples/end-to-end/` stays where it is. It is the reference walk across all of them, not one of
them.

## What an area must contain

Each area demonstrates the cards it holds. The card profile under
`docs/reference/cards/<address>.json` carries that card's definition, its standards, the real tools
that fill it, how a caller uses it, and the gaps it cannot yet demonstrate. **Write the example
from the profile** — and know, before you start, how far that will actually get you.

> **Tested once, on 2026-09-11.** `3-core-agent/` was built from `3-3.json` alone to find out.
> Twelve questions came up; **ten could not be answered from the profile**, and an eleventh only
> from prose no gate checks. The profile is a sound evidence base and an incomplete specification:
> it says what a boundary *is* and cites a standard for it, and not what the boundary *does* — its
> verbs, their order, its value domains, its failures, or where the caller's one knob applies.
> `docs/reference/profile-sufficiency.md` has all twelve and the five fields that would close them.

Do not invent what a card means here. If the profile does not say it, either the profile is
incomplete or the claim is not sourced — both are answers, neither is licence to write prose. Write
the gap down instead: that file is where it goes, and it is how the profile schema gets fixed
rather than worked around.

## Rules carried over

These are not new, and the archived areas got them right:

- A **visible check** the author can run (`test.sh`), and a **hidden check** written by someone who
  never saw the example. A gate the author can tune is not the same evidence as one they cannot —
  and on the first area this was not a formality: eighteen author-written checks passed over a
  defect that the hidden check caught on its first run. Budget for the second reviewer.
- Dependency-free Python 3 and bash. No network.
- Dry-run adapters whose **call shape is identical to live**.

## Rules that are new

- **An area covers stated card addresses.** Its README names them; nothing is demonstrated by
  implication. `docs/reference/card-example-map.json` is the join, and
  `tools/check_card_example_map.py` proves every card is addressed.
- **A card an area cannot yet demonstrate is recorded as a gap**, with its address. Eight cards had
  no example under the old structure and nothing said so.
- **Claims cite or say proposed.** A README asserting the platform does something carries the record
  id, or marks itself proposed. Same rule as the card profiles, same reason.

## Where to start

Not with the code. Decide the seams first:

1. Nine areas may be too many if the rail and base do not warrant their own examples — they span
   rather than sit in the journey, and may belong as a dimension of each area instead.
2. Card boundaries are still moving. 31 recorded gaps say the model itself should change: 1.4 and
   1.5 may be one card, 4.2 may fold into 3.3 and 4.1, and two entry doors carry the wrong standard.
   Settle those before an example hard-codes them.

Building nine areas against a model that is about to change is how the last seven ended up here.
