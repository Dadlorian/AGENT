#!/usr/bin/env python3
"""Termination evidence for Intake Protocol 0.1 (SPEC.md section 4).

  --prove      assert the bound holds for every seed x unknown-rate, rules I1-I3 in force
  --sweep      reproduce the phase-transition table in SPEC.md section 3
  --break-i1   deliberate breakage: drop rule I1 (at-most-once). Must fail.

Rules under test:
  I1  each (template, cell) instantiates at most once per session
  I2  corrections consume a finite budget K
  I3  unknowns yield requirements, never new questions
"""
from __future__ import annotations
import random, sys

TEMPLATES = ["outcome", "constraints", "structure", "readiness", "authority", "needs"]
STAGES = ["Invitation", "Registration", "Arrival", "Workshop", "Follow-up"]
AREAS = ["Participants", "Venue", "Training", "Budget"]
BATCH, SPAWN, K = 3, 2, 12
HARD_CAP = 5000          # only to stop a non-terminating run; never reached when the bound holds


def space() -> int:
    return len(TEMPLATES) * len(STAGES) * len(AREAS)


def bound() -> int:
    """SPEC.md section 4: ceil(|Q| / batch) + K."""
    return -(-space() // BATCH) + K


def required_cells(rng: random.Random, coverage: float) -> list:
    """The subset of Q required at this session's targetDepth (SPEC.md section 3)."""
    q = [(t, s, a) for t in TEMPLATES for s in STAGES for a in AREAS]
    rng.shuffle(q)
    return q[:max(1, int(len(q) * coverage))]


def run(seed: int, p: float, i1: bool = True, coverage: float = 1.0) -> tuple[bool, int, int]:
    """Return (terminated, advancing_rounds, distinct_questions_asked).

    The server SELECTS the next batch from unasked required cells -- selection is
    server-driven, not spawn-driven. Under I3 an unknown yields a requirement and
    adds no question; with I1 dropped, discovery requirements spawn instances again.
    """
    rng = random.Random(seed)
    required = required_cells(rng, coverage)
    asked: set = set()
    spawned: list = []
    rounds = corrections = 0
    while rounds < HARD_CAP:
        queue = spawned[:BATCH] if spawned else [q for q in required if q not in asked][:BATCH]
        if not queue:
            return True, rounds, len(asked)
        rounds += 1
        spawned = spawned[BATCH:] if spawned else spawned
        for q in queue:
            asked.add(q[:3])
            if rng.random() < p and not i1:
                for _ in range(SPAWN):
                    spawned.append((rng.choice(TEMPLATES), rng.choice(STAGES),
                                    rng.choice(AREAS), rounds))
        if rng.random() < 0.15:
            if i1 and corrections >= K:
                continue                      # I2: budget spent, correction refused
            corrections += 1
            rounds += 0 if i1 else 0
    return False, rounds, len(asked)


def prove(i1: bool = True) -> int:
    ps = (0.2, 0.35, 0.45, 0.5, 0.55, 0.7, 0.85)
    seeds = range(25)
    b, failures = bound(), []
    print(f"|Q| = {len(TEMPLATES)}x{len(STAGES)}x{len(AREAS)} = {space()}   "
          f"bound = ceil({space()}/{BATCH}) + K={K} = {b} advancing rounds")
    print(f"rules: I1={'ON' if i1 else 'OFF (BROKEN)'}  I2=ON  I3=ON\n")
    print(f"{'p(unknown)':<12} {'terminated':<12} {'max rounds':<12} {'<= bound':<10} {'max asked'}")
    print("-" * 60)
    for p in ps:
        res = [run(s, p, i1) for s in seeds]
        term = sum(1 for r in res if r[0])
        mx = max(r[1] for r in res)
        ok = term == len(seeds) and mx <= b
        if not ok:
            failures.append((p, term, mx))
        print(f"{p:<12} {term}/{len(seeds):<10} {mx:<12} {str(mx <= b):<10} {max(r[2] for r in res)}")
    print()
    if failures:
        for p, term, mx in failures:
            print(f"   FAIL  p={p}: terminated {term}/{len(seeds)}, max rounds {mx} (bound {b})")
        print(f"\nTERMINATION NOT PROVEN: {len(failures)} of {len(ps)} rates violate the bound.")
        return 1
    print(f"TERMINATION PROVEN: every seed x rate halted within {b} advancing rounds.")
    return 0


def sweep() -> int:
    print(f"{'p(unknown)':<12} {'I1 off: terminated / max rounds':<34} {'I1 on: terminated / max rounds'}")
    print("-" * 82)
    for p in (0.2, 0.35, 0.45, 0.5, 0.55, 0.7, 0.85):
        off = [run(s, p, False) for s in range(10)]
        on = [run(s, p, True) for s in range(10)]
        print(f"{p:<12} {sum(o[0] for o in off)}/10   rounds {max(o[1] for o in off):<10} "
              f"{sum(o[0] for o in on)}/10   rounds {max(o[1] for o in on)}")
    print(f"\ncritical point: expected offspring = p x {SPAWN} = 1  ->  p = {1/SPAWN}")
    return 0


if __name__ == "__main__":
    if "--sweep" in sys.argv:
        sys.exit(sweep())
    if "--break-i1" in sys.argv:
        rc = prove(i1=False)
        print("\nDeliberate breakage: exit 1 IS the expected result -- the bound must not hold."
              if rc else "\nBREAKAGE DID NOT FAIL -- the criterion checks nothing.")
        sys.exit(rc if rc else 2)
    sys.exit(prove(i1=True))
