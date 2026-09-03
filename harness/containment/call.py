#!/usr/bin/env python3
"""The minimal call: start one contained unit, run one agent turn, cancel it
mid-turn, read the stop reason and the containment report.

Two halves. Everything above THE CALLER'S MINIMAL CALL is the platform: it
stamps the correlation id, the budget ceiling, the idempotency key and the actor
that the caller never asks for, and it enforces both ceilings from outside the
unit. Everything below it is what a caller writes - under 40 lines, and it names
no containment technology and no runtime.

  ADAPTER=dryrun|second|live python3 call.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from interface import (ContainmentReport, IsolationDeclaration, Problem, SessionCapabilities,  # noqa: E402
                       TurnRequest, TurnResult, UnitContext, UnitResult)

# --- platform side: applied, not requested -----------------------------------
def config(path=None):
    with open(path or os.environ.get("BINDING", os.path.join(HERE, "binding.json"))) as fh:
        return json.load(fh)


def adapter(cfg):
    """Selecting a containment technology is configuration. There is no code path
    that chooses one, and nothing downstream branches on which answered."""
    name = os.environ.get("ADAPTER", cfg.get("adapter", "dryrun"))
    return importlib.import_module(f"adapters.{name}").Adapter(cfg), name


def envelope(cfg, kind, summary, payload):
    """cap-consumption's entry envelope. The caller supplies intent and payload;
    the five stamped members are applied by the platform."""
    run_id = "run-" + uuid.uuid4().hex[:8]
    body = json.dumps(payload, sort_keys=True)
    return {"kind": kind,
            "actor": {"subject": "user:corey", "delegation_chain": ["agent:containment-harness"]},
            "intent": {"summary": summary},
            "correlation": {"run_id": run_id, "correlation_id": "cor-" + uuid.uuid4().hex[:8]},
            "budget": {"ceiling_s": float(cfg["turn"]["ceiling_s"])},
            "idempotency_key": "idem-" + hashlib.sha256(body.encode()).hexdigest()[:16],
            "payload": payload}


def context(env) -> UnitContext:
    return UnitContext(correlation_id=env["correlation"]["correlation_id"],
                       run_id=env["correlation"]["run_id"], actor=env["actor"]["subject"],
                       idempotency_key=env["idempotency_key"], ceiling_s=env["budget"]["ceiling_s"])


class Dispatch:
    """Both ceilings live out here: a monotonic timer and the cancel grace window
    each end the unit through the boundary's own destroy path. A unit is never
    asked to enforce a ceiling on itself, and a runtime that cannot cancel is
    stopped anyway."""

    def __init__(self, ad, handle, session, request):
        self.ad, self.handle, self.session, self.request = ad, handle, session, request
        self.cancelled_at = None

    def start(self):
        self.t0 = time.monotonic()
        self.deadline = self.t0 + self.handle.context.ceiling_s
        self.turn = self.ad.prompt(self.session, self.request)
        return self

    def cancel(self):
        self.cancelled_at = time.monotonic()
        self.ad.cancel(self.session, self.request.grace_s)     # acceptance, not a kill

    def _drain(self, window_s=0.15):
        end, seen = time.monotonic() + window_s, 0
        while time.monotonic() < end:
            if self.ad.next_frame(self.turn, 0.02) is not None:
                seen += 1
        return seen

    def finish(self):
        frames, stop, by = 0, None, None
        while stop is None:
            now = time.monotonic()
            if now >= self.deadline:
                stop, by = "terminated", "budget-ceiling"
                break
            if self.cancelled_at and now - self.cancelled_at > self.request.grace_s:
                stop, by = "cancel_timeout", "boundary"
                break
            frame = self.ad.next_frame(self.turn, 0.02)
            if frame is None:
                continue
            frames += 1
            if frame.kind == "terminal":
                stop = frame.stop_reason
        if by is None:                       # a terminal frame arrived: nothing may follow it
            after = self._drain()
            unit_result = self.ad.terminate(self.handle, self.request.grace_s)
        else:                                # the boundary stopped it: destroy first, then look
            unit_result = self.ad.terminate(self.handle, self.request.grace_s)
            after = self._drain()
        cancel_to_terminal = round(time.monotonic() - self.cancelled_at, 3) if self.cancelled_at else None
        return TurnResult(stop_reason=stop, frames=frames, frames_after_terminal=after,
                          cancel_to_terminal_s=cancel_to_terminal,
                          output_digest=unit_result.output_digest, terminated_by=by), unit_result


# --- THE CALLER'S MINIMAL CALL -----------------------------------------------
PROMPT = "Read the repository and summarise the failing test. Then wait."


def minimal_call(cfg):
    ad, name = adapter(cfg)                                     # ADAPTER=dryrun|second|live
    turn_cfg = cfg["turn"]
    decl = IsolationDeclaration.from_dict(cfg["default_declaration"])
    env = envelope(cfg, "human", "cancel one contained agent turn", {"prompt": PROMPT})
    unit = ad.admit(decl, context(env))                         # refused here, or nothing runs
    session = ad.open_session(unit, SessionCapabilities(streaming=True, permission_callbacks=True,
                                                        cancellation=True))
    request = TurnRequest(PROMPT, turn_cfg["op_seconds"], turn_cfg["grace_s"])
    turn = Dispatch(ad, unit, session, request).start()
    time.sleep(turn_cfg["cancel_at_s"])
    turn.cancel()                                               # mid-turn, mid-tool-call
    result, unit_result = turn.finish()                         # stop reason
    report = ad.inspect_containment(unit)                       # asserted by the host, not the unit
    return {"adapter_selected": name, "binding": ad.binding(), "envelope": env, "unit": unit,
            "session": session, "result": result, "unit_result": unit_result, "report": report}
# --- end of the caller's minimal call ----------------------------------------


def table(rows):
    width = max(len(r[0]) for r in rows)
    for key, value in rows:
        print(f"  {key.ljust(width)}  {value}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--binding", help="configuration file (default binding.json)")
    args = ap.parse_args(argv)
    cfg = config(args.binding)
    try:
        out = minimal_call(cfg)
    except Problem as problem:
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    r, u, c, s, b = out["result"], out["unit_result"], out["report"], out["session"], out["binding"]
    print(f"CONTAINED TURN  correlation={out['envelope']['correlation']['correlation_id']}  "
          f"actor={out['envelope']['actor']['subject']}  profile={out['unit'].profile}")
    table([
        ("adapter selected (configuration)", b.adapter),
        ("containment marker (read from the unit)", c.containment_marker),
        ("negotiated capabilities", f"streaming={s.negotiated.streaming} "
                                    f"callbacks={s.negotiated.permission_callbacks} "
                                    f"cancellation={s.negotiated.cancellation}"),
        ("stop reason", r.stop_reason + (f" (by {r.terminated_by})" if r.terminated_by else "")),
        ("cancel to terminal frame", f"{r.cancel_to_terminal_s}s within a {cfg['turn']['grace_s']}s grace"),
        ("frames / after terminal", f"{r.frames} / {r.frames_after_terminal}"),
        ("unit result", f"exit={u.exit_status} stop={u.stop} digest={u.output_digest[:23]}..."),
        ("jail mode", c.jail_mode),
        ("owner in host passwd", str(c.owner_in_host_passwd)),
        ("egress attempts made / blocked", f"{c.egress_attempts_made} / {c.egress_attempts_blocked}"),
        ("secrets seen inside the unit", str(c.secrets_seen_inside)),
        ("observed from", c.observed_from),
    ])
    return 0


if __name__ == "__main__":
    sys.exit(main())
