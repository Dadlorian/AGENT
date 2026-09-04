#!/usr/bin/env python3
"""The check the C01-F closure names, made runnable.

Two properties:

1. coverage: every field UnitContext declares - correlation_id, run_id,
   actor, idempotency_key, ceiling_s, not just actor - is read by a guarantee
   at each of the three points the closure names: admission, dispatch, and a
   capability call. Run the same admit -> dispatch -> capability call ->
   terminate cycle against two independent adapters for the context
   interface (dryrun, second) and read the shared ledger back.

2. enforcement: the guarantee is real, not bookkeeping written for this
   check's sake. A second admission under an idempotency_key that is still
   in flight is refused - the field is read, and reading it changes what
   happens - on both adapters, not one.

  python3 context_check.py                    # exits 0 when both properties hold
  python3 context_check.py --break=uncovered   # deliberately breaks property 1
  python3 context_check.py --break=silent-dup  # deliberately breaks property 2
"""
from __future__ import annotations

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from interface import IsolationDeclaration, Problem, SessionCapabilities, TurnRequest  # noqa: E402
from call import config, context, envelope  # noqa: E402
from adapters import dryrun, second  # noqa: E402
import context_guarantees  # noqa: E402
from context_guarantees import ContextLedger, FIELDS, POINTS  # noqa: E402

ADAPTERS = (dryrun, second)   # two independent adapters for the context interface (interface.py's own)


def run_one_cycle(ad, cfg) -> bool:
    """admit -> dispatch -> capability call -> terminate: the same cases
    every adapter serves, run for real so the coverage below is read from a
    live cycle and not asserted against a stub."""
    decl = IsolationDeclaration.from_dict(cfg["default_declaration"])
    env = envelope(cfg, "human", "context check", {"prompt": "context probe"})
    unit = ad.admit(decl, context(env))
    session = ad.open_session(unit, SessionCapabilities(True, True, True))
    ad.prompt(session, TurnRequest("context probe", 0.1, 0.2))
    terminal = None
    deadline = time.monotonic() + 2.0
    while terminal is None and time.monotonic() < deadline:
        frame = ad.next_frame(session.session_id, 0.05)
        if frame is not None and frame.kind == "terminal":
            terminal = frame
    result = ad.terminate(unit, 0.2)
    return unit is not None and result is not None


def check_coverage(cfg, *, break_it: bool) -> bool:
    """Property 1. `--break=uncovered` restores the exact flaw the evidence
    names: `ceiling_s` stamped onto every unit at admission but never read
    there - the way `run_id`, `actor` and `idempotency_key` looked before
    this module existed."""
    context_guarantees.LEDGER = ContextLedger()   # fresh: this property's coverage only

    original = ContextLedger.guard_admission
    if break_it:
        def patched(self, ctx, unit_id):
            self._read("admission", "actor")
            self._read("admission", "idempotency_key")
            self._read("admission", "correlation_id")
            self._read("admission", "run_id")
            # ceiling_s: not read here - simulates the field this property exists to catch
            self.active_idempotency_keys[ctx.idempotency_key] = unit_id
            self.active_correlation_ids[ctx.correlation_id] = unit_id
            self.run_unit_counts[ctx.run_id] = self.run_unit_counts.get(ctx.run_id, 0) + 1
            self.unit_context[unit_id] = ctx
            self.unit_admitted_at[unit_id] = time.monotonic()
        ContextLedger.guard_admission = patched

    try:
        ok_runs = [run_one_cycle(mod.Adapter(cfg), cfg) for mod in ADAPTERS]
    finally:
        ContextLedger.guard_admission = original

    coverage = context_guarantees.LEDGER.coverage()
    missing = [(point, field) for point in POINTS for field in FIELDS if field not in coverage[point]]
    ok = all(ok_runs) and not missing
    print(f"[coverage] admit/dispatch/terminate passed on both adapters={all(ok_runs)} "
          f"fields={len(FIELDS)} points={len(POINTS)} missing={missing if missing else 'none'}")
    return ok


def check_enforcement(cfg, *, silent: bool) -> bool:
    """Property 2: idempotency_key is read - and enforced - not merely
    carried. Two calls with the same probe text (call.py's envelope() hashes
    the payload into the key, so the key matches) but two different
    correlation ids - a retry of the same logical request, not a repeat of
    the same wire call - and the second one's turn is refused while the
    first is still outstanding. `--break=silent-dup` removes the dispatch
    guarantee entirely, the way a field that is only ever copied into an
    AdmissionHandle looks."""
    ok = True
    for mod in ADAPTERS:
        context_guarantees.LEDGER = ContextLedger()
        if silent:
            context_guarantees.LEDGER.guard_dispatch = lambda ctx, unit_id: None
        ad = mod.Adapter(cfg)
        decl = IsolationDeclaration.from_dict(cfg["default_declaration"])
        ctx1 = context(envelope(cfg, "human", "context check dup", {"prompt": "dup probe"}))
        ctx2 = context(envelope(cfg, "human", "context check dup", {"prompt": "dup probe"}))
        assert ctx1.idempotency_key == ctx2.idempotency_key, "same payload must hash to the same key"
        assert ctx1.correlation_id != ctx2.correlation_id, "two calls, not one replayed wire request"

        unit1 = ad.admit(decl, ctx1)
        session1 = ad.open_session(unit1, SessionCapabilities(True, True, True))
        ad.prompt(session1, TurnRequest("dup probe", 0.05, 0.2))   # first turn: outstanding

        unit2 = ad.admit(decl, ctx2)                                # a second unit, same idempotency_key
        session2 = ad.open_session(unit2, SessionCapabilities(True, True, True))
        refused = False
        try:
            ad.prompt(session2, TurnRequest("dup probe", 0.05, 0.2))   # same key, first still outstanding
        except Problem as problem:
            refused = (problem.body["type"] == "urn:agentic:problem:document-invalid"
                      and problem.body.get("field") == "idempotency_key")
        print(f"[enforcement:{mod.Adapter.name}] duplicate dispatch refused={refused} (silent={silent})")
        if not refused:            # a live guarantee always refuses this; a silenced one does not
            ok = False

        deadline = time.monotonic() + 2.0                          # drain and free both units
        while time.monotonic() < deadline:
            frame = ad.next_frame(session1.session_id, 0.05)
            if frame is not None and frame.kind == "terminal":
                break
        ad.terminate(unit1, 0.2)
        ad.terminate(unit2, 0.2)
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--break", dest="break_mode", choices=["uncovered", "silent-dup"], default=None,
                    help="deliberately break one property to prove the check catches it")
    args = ap.parse_args(argv)
    cfg = config()

    cov_ok = check_coverage(cfg, break_it=args.break_mode == "uncovered")
    enf_ok = check_enforcement(cfg, silent=args.break_mode == "silent-dup")
    passed = cov_ok and enf_ok
    print("context_check: " + ("pass" if passed else "FAIL")
          + (f"  (--break={args.break_mode})" if args.break_mode else ""))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
