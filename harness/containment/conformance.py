#!/usr/bin/env python3
"""The conformance run every adapter must pass.

The same cases against any adapter, from one declaration. It is the only reader
of adapter identity in the harness, and it never trusts the binding for what
actually contained the unit: the marker is read back from the running unit.

  python3 conformance.py --adapter dryrun --adapter second --report out/containment-conformance.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from interface import (IsolationDeclaration, Problem, SessionCapabilities, TurnRequest,  # noqa: E402
                       as_json)
from call import Dispatch, config, context, envelope  # noqa: E402


def build(name, cfg):
    return importlib.import_module(f"adapters.{name}").Adapter(cfg)


def one_turn(ad, cfg, *, cancel=True, ceiling_s=None, decl_doc=None, grace_s=None):
    """One contained unit, one turn, optionally cancelled mid-turn."""
    turn_cfg = cfg["turn"]
    decl = IsolationDeclaration.from_dict(decl_doc or cfg["default_declaration"])
    env = envelope(cfg, "human", "containment conformance", {"prompt": "conformance probe"})
    env["budget"]["ceiling_s"] = float(ceiling_s if ceiling_s is not None else turn_cfg["ceiling_s"])
    unit = ad.admit(decl, context(env))
    session = ad.open_session(unit, SessionCapabilities(True, True, True))
    grace = float(grace_s if grace_s is not None else turn_cfg["grace_s"])
    dispatch = Dispatch(ad, unit, session, TurnRequest("conformance probe", turn_cfg["op_seconds"],
                                                       grace)).start()
    if cancel:
        time.sleep(turn_cfg["cancel_at_s"])
        dispatch.cancel()
    result, unit_result = dispatch.finish()
    return unit, session, result, unit_result, ad.inspect_containment(unit)


def run_adapter(name, cfg):
    """Every case, one adapter. Returns the per-adapter report row."""
    checks, row = [], {"adapter": name}

    def check(label, ok, got=""):
        checks.append({"check": label, "pass": bool(ok), "observed": str(got)})

    binding = build(name, cfg).binding()
    row["binding_adapter"] = binding.adapter
    row["marker_expected"] = binding.containment_marker
    row["execution_model"] = dict(binding.execution_model)
    row["declared_gap"] = list(binding.declared_gap)
    offers_cancel = binding.capabilities_offered.cancellation

    # 1-2. one contained unit, one turn, cancelled mid-turn
    ad = build(name, cfg)
    unit, session, result, unit_result, report = one_turn(ad, cfg)
    row.update(containment_marker=report.containment_marker, exit_status=unit_result.exit_status,
               output_digest=unit_result.output_digest, stop_reason=result.stop_reason,
               cancel_to_terminal_s=result.cancel_to_terminal_s,
               frames_after_terminal=result.frames_after_terminal,
               containment=as_json(report))
    check("containment marker read from the unit equals the adapter in the binding",
          report.containment_marker == binding.containment_marker, report.containment_marker)
    check("jail mode is 0700", report.jail_mode == "0700", report.jail_mode)
    check("owning identity has no host passwd entry", report.owner_in_host_passwd is False,
          report.owner_in_host_passwd)
    check("the unit attempted egress at all", report.egress_attempts_made > 0,
          report.egress_attempts_made)
    check("every egress attempt was blocked",
          report.egress_attempts_blocked == report.egress_attempts_made,
          f"{report.egress_attempts_blocked}/{report.egress_attempts_made}")
    check("no real secret inside the unit", report.secrets_seen_inside == 0, report.secrets_seen_inside)
    check("containment asserted from outside the unit", report.observed_from == "host",
          report.observed_from)
    check("no frame arrived after the terminal frame", result.frames_after_terminal == 0,
          result.frames_after_terminal)
    if offers_cancel:
        expected, honoured = "cancelled", result.stop_reason == "cancelled"
        check("terminal frame arrived inside the grace window",
              result.cancel_to_terminal_s is not None
              and result.cancel_to_terminal_s <= cfg["turn"]["grace_s"], result.cancel_to_terminal_s)
    else:
        expected, honoured = "cancel_timeout", result.stop_reason == "cancel_timeout"
    check(f"stop reason is {expected} for a runtime that "
          f"{'offers' if offers_cancel else 'declares it cannot do'} cancellation",
          honoured, result.stop_reason)
    row["declared_gap_honoured"] = honoured
    check("the adapter behaved as its declared gap says", honoured, honoured)

    # 3. the ceiling is enforced from outside, on every adapter
    ad = build(name, cfg)
    _, _, ceiling_result, ceiling_unit, _ = one_turn(ad, cfg, cancel=False,
                                                     ceiling_s=cfg["turn"]["op_seconds"] / 4)
    check("a ceiling shorter than the turn ends the unit through the boundary",
          ceiling_result.stop_reason == "terminated" and ceiling_result.terminated_by == "budget-ceiling",
          f"{ceiling_result.stop_reason}/{ceiling_result.terminated_by}")
    check("the unit was destroyed, not asked to stop itself", ceiling_unit.stop == "forced",
          ceiling_unit.stop)

    # 4. a profile the adapter cannot resolve is refused at admission, not approximated
    ad = build(name, cfg)
    try:
        ad.admit(IsolationDeclaration.from_dict({"profile": "no-such-profile"}),
                 context(envelope(cfg, "human", "refusal", {})))
        check("unknown profile refused at admit", False, "admitted")
    except Problem as problem:
        check("unknown profile refused at admit with a typed problem",
              problem.body["type"] == "urn:agentic:problem:isolation-unavailable"
              and problem.body["status"] == 503 and problem.body["retryable"] is True,
              problem.body["type"])
        check("nothing was admitted for the refused declaration", not getattr(ad, "units", {}),
              len(getattr(ad, "units", {})))

    # 5-7. declarations the interface refuses before any adapter sees them
    for label, doc, want in (
            ("a machine-shaped field is refused", {"profile": "small", "kernel_args": "console=ttyS0"},
             "urn:agentic:problem:document-invalid"),
            ("egress=allowlist with an empty list is refused",
             {"profile": "small", "egress": "allowlist"}, "urn:agentic:problem:document-invalid"),
            ("a real credential in the declaration is refused",
             {"profile": "small", "credentials": "inline"}, "urn:agentic:problem:document-invalid")):
        try:
            IsolationDeclaration.from_dict(doc)
            check(label, False, "accepted")
        except Problem as problem:
            check(label, problem.body["type"] == want and problem.body["status"] == 422,
                  problem.body["type"])

    # 8. a grace below the adapter's own floor is refused, or accepted when it has none
    ad = build(name, cfg)
    floor = binding.cancel_floor_s
    try:
        one_turn(ad, cfg, grace_s=floor / 2 if floor else 0.0)
        check("grace below the adapter's cancel floor is refused", floor == 0, f"floor={floor}")
    except Problem as problem:
        check("grace below the adapter's cancel floor is refused with a typed problem",
              floor > 0 and problem.body["status"] == 422, problem.body["type"])

    row["checks"] = checks
    row["passed"] = all(c["pass"] for c in checks)
    return row


def cross_adapter(rows):
    """What only a swap can show."""
    out = []

    def check(label, ok, got=""):
        out.append({"check": label, "pass": bool(ok), "observed": str(got)})

    markers = {r["containment_marker"] for r in rows}
    check("two distinct containment technologies ran", len(rows) >= 2, len(rows))
    check("a different technology actually contained the unit", len(markers) == len(rows),
          sorted(markers))
    check("output digest is equal across adapters", len({r["output_digest"] for r in rows}) == 1,
          sorted({r["output_digest"][:23] for r in rows}))
    check("exit status is equal across adapters", len({r["exit_status"] for r in rows}) == 1,
          sorted({r["exit_status"] for r in rows}))
    differs = []
    if len(rows) >= 2:
        first, second = rows[0]["execution_model"], rows[1]["execution_model"]
        differs = [{"axis": axis, "today_value": first[axis], "second_value": second.get(axis, "")}
                   for axis in first if first[axis] != second.get(axis)]
    check("the pair differs in execution model on at least one axis", bool(differs),
          [d["axis"] for d in differs])
    return out, differs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", action="append", default=[],
                    help="repeatable; defaults to $ADAPTER or dryrun")
    ap.add_argument("--binding", help="configuration file (default binding.json)")
    ap.add_argument("--report", default=os.path.join(HERE, "out", "containment-conformance.json"))
    args = ap.parse_args(argv)
    cfg = config(args.binding)
    names = args.adapter or [os.environ.get("ADAPTER", cfg.get("adapter", "dryrun"))]

    rows = [run_adapter(name, cfg) for name in names]
    cross, differs = (cross_adapter(rows) if len(rows) > 1 else ([], []))
    report = {"adapters_run": len(rows), "per_adapter": rows, "cross_adapter": cross,
              "differs_in_execution_model": differs,
              "passed": all(r["passed"] for r in rows) and all(c["pass"] for c in cross)}
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)

    for row in rows:
        containment = row["containment"]
        marker_ok = "match" if row["containment_marker"] == row["marker_expected"] else "MISMATCH"
        print(f"adapter={row['binding_adapter']} containment_marker={marker_ok}"
              f" exit={row['exit_status']} digest={row['output_digest'][:23]}"
              f" jail_mode={containment['jail_mode']}"
              f" owner_in_host_passwd={str(containment['owner_in_host_passwd']).lower()}"
              f" egress_made={containment['egress_attempts_made']}"
              f" egress_blocked={containment['egress_attempts_blocked']}"
              f" stop_reason={row['stop_reason']}"
              f" declared_gap_honoured={str(row['declared_gap_honoured']).lower()}"
              f" checks={sum(1 for c in row['checks'] if c['pass'])}/{len(row['checks'])}")
        for chk in row["checks"]:
            if not chk["pass"]:
                print(f"  FAIL [{row['binding_adapter']}] {chk['check']} -> {chk['observed']}")
    for chk in cross:
        if not chk["pass"]:
            print(f"  FAIL [cross-adapter] {chk['check']} -> {chk['observed']}")
    print(f"adapters_run={len(rows)}")
    print("conformance: " + ("pass" if report["passed"] else "FAIL") + f"  report={args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
