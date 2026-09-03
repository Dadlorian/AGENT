#!/usr/bin/env python3
"""The corpus: one envelope, four doors, and enough units to attest over.

Nothing is invented here. The four doors, the actor and the delegation chain
behind them, the correlation, the ceiling and the idempotency key are read from
the fixtures the end-to-end example already ships
(examples/end-to-end/entries/*.json), so the harness and the example cannot
drift apart. One logical job - the intent, the budget and the payload of the
human entry - is driven through every door unchanged; a door differs in who
knocked and in nothing else.

Per door the corpus carries 26 units: one plain unit, one whose ceiling cannot
cover the metered call (the refusal, identical at all four doors), one that
reuses a held idempotency key for a different body, and 23 more plain units so
the attestation has at least a hundred units to read.
"""
from __future__ import annotations

import json
import os

from interface import ENTRIES_DIR, Unit, digest

DOORS = ("human", "event", "schedule", "external")
PER_DOOR = 26

FIXTURES: dict[str, dict] = {
    kind: json.load(open(os.path.join(ENTRIES_DIR, f"{kind}.json"))) for kind in DOORS
}
# One logical job, taken from the human fixture and sent through every door.
SUBJECT = {k: FIXTURES["human"][k] for k in ("intent", "budget", "payload", "envelope_version")}
JOB_DIGEST = digest(SUBJECT)
# What one metered call is estimated to cost. Deterministic, from the job itself.
ESTIMATE_MICROS = 210000 + len(json.dumps(SUBJECT, sort_keys=True))


def unit(kind: str, index: int) -> Unit:
    """One unit at one door. The index fixes the variant, everywhere and for
    every binding, so a case in a gate and a line in the minimal call mean the
    same unit: 1 is the unit whose ceiling cannot cover one metered call, 2
    reuses unit 0's idempotency key for a different body, and the rest are plain.
    """
    fixture = FIXTURES[kind]
    ceiling = ESTIMATE_MICROS - 1 if index == 1 else fixture["budget"]["ceiling_micros"]
    key = (f"{fixture['idempotency_key']}-000" if index == 2
           else f"{fixture['idempotency_key']}-{index:03d}")
    body = digest({**SUBJECT, "window_hours": 999}) if index == 2 else JOB_DIGEST
    return Unit(unit_id=f"{fixture['entry_id']}-{index:03d}",
                kind=kind,
                actor=fixture["actor"],
                correlation={**fixture["correlation"], "unit": index},
                ceiling_micros=ceiling,
                estimate_micros=ESTIMATE_MICROS,
                idempotency_key=key,
                body_digest=body)


def corpus(doors: tuple[str, ...] = DOORS) -> list[Unit]:
    """The units every enforcement point is attested over, in a fixed order."""
    return [unit(kind, i) for kind in doors for i in range(PER_DOOR)]
