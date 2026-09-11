#!/usr/bin/env python3
"""Phase controller: run a phase, validate it, self-improve at most twice, then stop.

The point of this tool is the stopping condition. An unattended run that keeps retrying a phase
that will not go green burns a night and produces a mess someone has to unpick. Two failed
self-improvement attempts on the same phase is the signal that the problem is not something the
loop can fix, and the correct action is to stop and leave the evidence.

  python3 tools/phase.py gates                 run every gate, print a table, exit 1 on red
  python3 tools/phase.py open <name>           record that a phase started
  python3 tools/phase.py close <name>          run gates; green closes the phase, red records
                                               an attempt and says whether to retry or stop
  python3 tools/phase.py status                what is open, what stopped, and why

State lives in state/phases.json, which is append-mostly and readable: a phase that stopped says
which gate was red and on which attempt, so the morning after is a read rather than an
investigation.

Gates are the definition of done from bridge.md. `blocking` gates stop a phase; the two currently
red for recorded reasons (row 76, row 77) are carried as `known_red` so they are reported without
halting a phase that did not cause them.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "phases.json"
MAX_ATTEMPTS = 2

# (label, argv, blocking)
GATES = [
    ("skills",         ["python3", "tools/validate_skills.py"], True),
    ("kb chain",       ["python3", "tools/kb.py", "verify"], True),
    ("ledger",         ["python3", "tools/kb.py", "ledger-verify"], True),
    ("egress",         ["python3", "tools/reconcile_egress.py"], True),
    ("card profiles",  ["python3", "tools/validate_card_profiles.py"], True),
    ("gate self-test", ["python3", "tools/card_profile_test.py"], True),
    ("prose",          ["python3", "tools/prose_gate.py"], True),
    ("prose self-test", ["python3", "tools/prose_gate.py", "--selftest"], True),
    ("card map",       ["python3", "tools/check_card_example_map.py"], True),
    ("ref model",      ["python3", "tools/extract_reference_model.py", "--check"], True),
    ("status",         ["python3", "tools/status_check.py", "--freshness"], True),
    ("snippets",       ["python3", "tools/verify_snippets.py", "--check"], False),
    ("standards",      ["python3", "tools/standards.py", "check"], False),
]
KNOWN_RED = {
    "snippets": "47 read-field drifts, 0 snippet-field; measured by tools/knowledge_pool.py",
    "standards": "row 77: JOURNEY.md names archived example paths",
}


def load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"phases": {}}


def save(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")


def run_gates(verbose: bool = True) -> tuple[bool, list[dict]]:
    """Returns (all blocking gates green, per-gate results)."""
    results = []
    for label, argv, blocking in GATES:
        t0 = time.time()
        try:
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=900)
            code, tail = p.returncode, (p.stdout + p.stderr).strip().splitlines()
            last = tail[-1][:96] if tail else ""
        except subprocess.TimeoutExpired:
            code, last = 124, "TIMEOUT after 900s"
        results.append({"gate": label, "exit": code, "blocking": blocking,
                        "known_red": label in KNOWN_RED, "last": last,
                        "seconds": round(time.time() - t0, 1)})
        if verbose:
            if code == 0:
                mark = "PASS"
            elif label in KNOWN_RED:
                mark = "red*"
            else:
                mark = "FAIL"
            print(f"  {mark:5} {label:15} {last}")
    bad = [r for r in results
           if r["exit"] != 0 and r["blocking"] and not r["known_red"]]
    if verbose and KNOWN_RED:
        print("\n  * known red, recorded, does not block:")
        for k, why in KNOWN_RED.items():
            print(f"      {k}: {why}")
    return (not bad), results


def cmd_gates() -> int:
    ok, res = run_gates()
    bad = [r["gate"] for r in res if r["exit"] != 0 and r["blocking"] and not r["known_red"]]
    print(f"\n{sum(1 for r in res if r['exit'] == 0)}/{len(res)} gates green"
          + (f"; BLOCKING RED: {', '.join(bad)}" if bad else ""))
    return 0 if ok else 1


def cmd_open(name: str) -> int:
    d = load()
    ph = d["phases"].setdefault(name, {"attempts": 0, "state": "open", "history": []})
    if ph["state"] == "stopped":
        print(f"STOP: phase {name!r} already stopped after {ph['attempts']} attempts. "
              f"Fix the cause and clear it from state/phases.json deliberately.")
        return 1
    ph["state"] = "open"
    ph["history"].append({"event": "open", "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    save(d)
    print(f"phase {name!r} open (attempt {ph['attempts'] + 1} of {MAX_ATTEMPTS + 1})")
    return 0


def cmd_close(name: str) -> int:
    d = load()
    ph = d["phases"].setdefault(name, {"attempts": 0, "state": "open", "history": []})
    if ph["state"] == "stopped":
        print(f"STOP: phase {name!r} is stopped. Do not retry it unattended.")
        return 1
    print(f"closing phase {name!r} -- running gates\n")
    ok, res = run_gates()
    red = [r["gate"] for r in res if r["exit"] != 0 and r["blocking"] and not r["known_red"]]
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    if ok:
        ph["state"] = "closed"
        ph["history"].append({"event": "closed", "at": stamp})
        save(d)
        print(f"\nphase {name!r} CLOSED, every blocking gate green")
        return 0
    ph["attempts"] += 1
    ph["history"].append({"event": "red", "at": stamp, "attempt": ph["attempts"], "gates": red})
    if ph["attempts"] > MAX_ATTEMPTS:
        ph["state"] = "stopped"
        save(d)
        print(f"\nSTOP. Phase {name!r} failed {ph['attempts']} times on: {', '.join(red)}")
        print("Two self-improvement attempts did not fix it, so the loop is not going to. "
              "Leave the tree as it is; the evidence is more useful than another attempt.")
        return 2
    save(d)
    left = MAX_ATTEMPTS + 1 - ph["attempts"]
    print(f"\nRED on: {', '.join(red)}")
    print(f"Attempt {ph['attempts']} of {MAX_ATTEMPTS + 1}. Self-improve and close again "
          f"({left} attempt(s) left before this phase stops).")
    return 1


def cmd_status() -> int:
    d = load()
    if not d["phases"]:
        print("no phases recorded")
        return 0
    for name, ph in d["phases"].items():
        last = ph["history"][-1] if ph["history"] else {}
        extra = f" on {', '.join(last.get('gates', []))}" if last.get("gates") else ""
        print(f"  {ph['state']:8} {name:28} attempts {ph['attempts']}{extra}")
    stopped = [n for n, p in d["phases"].items() if p["state"] == "stopped"]
    if stopped:
        print(f"\nSTOPPED: {', '.join(stopped)} -- these need a person, not another run.")
        return 1
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "gates":
        return cmd_gates()
    if cmd == "status":
        return cmd_status()
    if cmd in ("open", "close"):
        if len(argv) < 2:
            print(f"usage: python3 tools/phase.py {cmd} <name>")
            return 1
        return cmd_open(argv[1]) if cmd == "open" else cmd_close(argv[1])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
