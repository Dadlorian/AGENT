#!/usr/bin/env python3
"""The check the isolation-q6 closure names, made runnable.

Two properties, both from the closure's `check`:

1. state-hash test: pause a running sandbox, compute a digest of its memory
   and filesystem state, resume it, and assert the digest recomputed from the
   resumed unit - before any further syscall - equals the pause-time digest.
   Run against `dryrun`, the adapter whose isolation class offers pause/resume/fork.

2. typed-unsupported test: call fork on an adapter whose isolation class does
   not offer it (`second`, single-shot, nothing to checkpoint) and assert it
   answers with the closed problem type isolation-operation-unsupported (501),
   never a crash and never a silent no-op.

  python3 lifecycle_check.py                  # exits 0 when both properties hold
  python3 lifecycle_check.py --break=digest    # deliberately breaks property 1
  python3 lifecycle_check.py --break=silent    # deliberately breaks property 2
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from interface import IsolationDeclaration, Problem, SessionCapabilities, TurnRequest  # noqa: E402
from call import config, context, envelope  # noqa: E402
from adapters import dryrun, second  # noqa: E402


def check_state_hash(cfg, *, break_it: bool) -> bool:
    """Property 1: pause -> resume reproduces the exact state digest."""
    ad = dryrun.Adapter(cfg)
    decl = IsolationDeclaration.from_dict({"profile": "small"})
    env = envelope(cfg, "human", "lifecycle check", {"prompt": "lifecycle probe"})
    handle = ad.admit(decl, context(env))
    session = ad.open_session(handle, SessionCapabilities(True, True, True))
    ad.prompt(session, TurnRequest("lifecycle probe", 0.2, 0.1))
    while ad.next_frame(session.session_id, 0.5) is None:      # run until the probe lands
        pass

    snapshot = ad.pause(handle)
    resumed = ad.resume(snapshot)

    if break_it:
        # Simulate a resume that does not faithfully restore memory state -
        # the flaw the state-hash test exists to catch.
        ad.units[resumed.unit_id].cancel_requested = not ad.units[resumed.unit_id].cancel_requested

    resumed_digest = ad.state_digest(resumed)          # recomputed before any further syscall
    ok = resumed_digest == snapshot.state_digest
    print(f"[state-hash] pause digest={snapshot.state_digest[:23]} "
          f"resume digest={resumed_digest[:23]} equal={ok}")
    return ok


def check_typed_unsupported(cfg, *, silent: bool) -> bool:
    """Property 2: fork on an adapter lacking the operation is a typed refusal,
    not a crash and not a silent no-op."""
    ad = second.Adapter(cfg)
    decl = IsolationDeclaration.from_dict({"profile": "small"})
    env = envelope(cfg, "human", "lifecycle check", {"prompt": "lifecycle probe"})
    handle = ad.admit(decl, context(env))

    if silent:
        # Simulate an adapter that degrades silently instead of refusing -
        # the flaw the typed-unsupported test exists to catch.
        ad.fork = lambda h: h  # type: ignore[method-assign]

    try:
        ad.fork(handle)
        print("[typed-unsupported] fork did not raise: silent degradation")
        return False
    except Problem as problem:
        ok = (problem.body["type"] == "urn:agentic:problem:isolation-operation-unsupported"
              and problem.body["status"] == 501)
        print(f"[typed-unsupported] fork raised type={problem.body['type']} "
              f"status={problem.body['status']} typed={ok}")
        return ok
    except Exception as exc:  # noqa: BLE001 - exactly the crash this property forbids
        print(f"[typed-unsupported] fork crashed instead of a typed refusal: "
              f"{type(exc).__name__}: {exc}")
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--break", dest="break_mode", choices=["digest", "silent"], default=None,
                    help="deliberately break one property to prove the check catches it")
    args = ap.parse_args(argv)
    cfg = config()

    hash_ok = check_state_hash(cfg, break_it=args.break_mode == "digest")
    unsupported_ok = check_typed_unsupported(cfg, silent=args.break_mode == "silent")
    passed = hash_ok and unsupported_ok
    print("lifecycle_check: " + ("pass" if passed else "FAIL")
          + (f"  (--break={args.break_mode})" if args.break_mode else ""))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
