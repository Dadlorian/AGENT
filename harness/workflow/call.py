#!/usr/bin/env python3
"""The minimal call: one durable flow, crashed and resumed, through the interface.

    ADAPTER=dryrun python3 harness/workflow/call.py

Everything below the CALLER CODE marker is what a caller writes. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the envelope here, not asked for by the caller (F-b4-01).

Where the calls are. Two interface calls are made in this file: `resume_point`
after the crash, and `read_receipt` after the resume. The rest of the flow -
begin_run, checkpoint_step, park_gate, record_decision, read_run - is made by
flow.py, which runs as a subprocess so that `--crash-at` can be a real `kill -9`
rather than a raised exception; flow.py is the durable driver, and its file
header reads in the order the flow executes. Nothing here opens the executor's
journal, its queue or its effect table: an executor keeps its state where it
likes, and a caller that reads it by path has left the interface (T7.2).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import Envelope, Problem, Receipt, load_executor  # noqa: E402

OUT = os.path.join(HERE, "out")


def build_envelope(run_key="wf-release-publish-2026-09-03", ceiling_micros=1_500_000,
                   kind="human", subject="user:corey") -> dict:
    """The one envelope of cap-consumption. The four stamps are applied here."""
    return Envelope(
        kind=kind, entry_id="wf-release-publish", occurred_at="2026-09-03T09:12:00Z",
        actor={"subject": subject,                                   # identity
               "delegation_chain": [{"actor": subject, "obtained_via": "direct"}]},
        intent={"workflow_ref": "flow.py:durable-publish/0.1",
                "summary": "Draft, review and publish the release note."},
        correlation={"run_id": "run-wf-0001",                        # correlation
                     "correlation_id": "corr-wf-0001", "depth": 0},
        budget={"ceiling_micros": ceiling_micros, "currency": "USD",  # budget
                "on_exceed": "terminate_unit"},
        idempotency_key=run_key,                                     # idempotency
        payload={"release": "2026.09.3", "notes": "coupon pricing fix"},
    ).dict()


def entry_file(out_dir: str, env: dict) -> str:
    """A fresh working directory and the caller's own entry document in it. The
    executor's storage lives under here too, but it is the executor's: this
    function makes the directory and never looks inside it again."""
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.json")
    with open(path, "w") as fh:
        json.dump(env, fh, indent=2)
    return path


def attempt(entry: str, adapter: str, out_dir: str, result: str, *extra) -> int:
    """One attempt of the durable flow, in its own process so a crash is a crash."""
    cmd = [sys.executable, os.path.join(HERE, "flow.py"), "--entry", entry,
           "--adapter", adapter, "--out", out_dir, "--result", result, *extra]
    return subprocess.run(cmd, capture_output=True, text=True).returncode


def report(adapter: str, rc1: int, rc2: int, resume, done: dict, receipt: Receipt) -> int:
    """Presentation. Every number below came from the interface or from the
    attempt's own result document; none of it was read out of the executor."""
    print(f"\nADAPTER={adapter}  executor_marker={receipt.executor_marker}  "
          f"({done['effect_commit_mode']})")
    rows = [("attempt 1", f"killed at publish (rc {rc1})", "-", "-"),
            ("crash", f"resume_point {resume.resume_point} read through the interface",
             f"{resume.steps_committed} steps committed", f"{resume.spent_micros} micros spent"),
            ("attempt 2", f"resumed at step {done['resume_point_at_start']} (rc {rc2})",
             f"{done['steps_replayed']} replayed", f"{done['steps_executed']} run"),
            ("gate", f"{receipt.gates_parked} parked, 10 deliveries each",
             f"{receipt.gates_decided} decisions applied",
             f"{done['gates_parked']} re-parked after the crash"),
            ("loop", done["loop"]["terminated_by"], f"{done['loop']['iterations_run']} iterations",
             done["loop"]["termination_class"]),
            ("effect", f"{len(receipt.effects)} effect row on the receipt", "1 expected",
             "no repeat"),
            ("budget", f"{done['spent_micros']} spent",
             f"{done['budget_remaining_micros']} left of {done['budget_ceiling_micros']}",
             "recomputed at resume"),
            ("outcome", done["outcome"], done["correlation_id"],
             f"correlation from {done['correlation_source']}")]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(w) for c, w in
                               zip(r + ("",) * 4, (10, 46, 26, 26))))
    return 0 if (rc2 == 0 and len(receipt.effects) == 1) else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = os.environ.get("ADAPTER", "dryrun")          # configuration, not code
    out_dir = os.path.join(OUT, "call-" + adapter)
    env = build_envelope()
    entry = entry_file(out_dir, env)
    run_key = env["idempotency_key"]
    try:
        executor = load_executor(adapter, out_dir)         # one name, one binding
        rc1 = attempt(entry, adapter, out_dir, os.path.join(out_dir, "attempt-1.json"),
                      "--crash-at", "publish", "--decision", "return_with_notes:user:corey",
                      "--decision", "approve:agent:release-bot", "--deliveries", "10")
        resume = executor.resume_point(run_key)            # where a restart continues
        rc2 = attempt(entry, adapter, out_dir, os.path.join(out_dir, "attempt-2.json"),
                      "--decision", "return_with_notes:user:corey",
                      "--decision", "approve:agent:release-bot", "--deliveries", "10")
        receipt = executor.read_receipt(run_key)            # gates, effects, spend
    except Problem as problem:                             # one refusal shape, typed
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    done = json.load(open(os.path.join(out_dir, "attempt-2.json")))       # the run's own result
    return report(adapter, rc1, rc2, resume, done, receipt)


if __name__ == "__main__":
    sys.exit(main())
