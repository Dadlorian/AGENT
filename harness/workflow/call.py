#!/usr/bin/env python3
"""The minimal call: one durable flow, crashed and resumed, through the interface.

    ADAPTER=dryrun python3 harness/workflow/call.py

Everything a caller writes is between the two rules below. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the envelope here, not asked for by the caller (F-b4-01).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import Envelope  # noqa: E402

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


def attempt(entry: str, adapter: str, out_dir: str, result: str, *extra) -> int:
    cmd = [sys.executable, os.path.join(HERE, "flow.py"), "--entry", entry,
           "--adapter", adapter, "--out", out_dir, "--result", result, *extra]
    return subprocess.run(cmd, capture_output=True, text=True).returncode


# --------------------------------------------------------------------------
# The whole call a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = os.environ.get("ADAPTER", "dryrun")          # configuration, not code
    out_dir = os.path.join(OUT, "call-" + adapter)
    os.makedirs(out_dir, exist_ok=True)
    for stale in ("journal.jsonl", "queue.jsonl", "effects.jsonl"):
        if os.path.exists(os.path.join(out_dir, stale)):
            os.remove(os.path.join(out_dir, stale))
    entry = os.path.join(out_dir, "entry.json")
    json.dump(build_envelope(), open(entry, "w"), indent=2)

    rc1 = attempt(entry, adapter, out_dir, os.path.join(out_dir, "attempt-1.json"),
                  "--crash-at", "publish", "--decision", "return_with_notes:user:corey",
                  "--decision", "approve:agent:release-bot", "--deliveries", "10")
    rc2 = attempt(entry, adapter, out_dir, os.path.join(out_dir, "attempt-2.json"),
                  "--decision", "return_with_notes:user:corey",
                  "--decision", "approve:agent:release-bot", "--deliveries", "10")
    done = json.load(open(os.path.join(out_dir, "attempt-2.json")))
    effects = [json.loads(l) for l in open(os.path.join(out_dir, "effects.jsonl"))]
    # --------------------------------------------------------------------
    print(f"\nADAPTER={adapter}  executor_marker={done['executor_marker']}  "
          f"({done['effect_commit_mode']})")
    rows = [("attempt 1", f"killed at publish (rc {rc1})", "-", "-"),
            ("attempt 2", f"resumed at step {done['resume_point_at_start']} (rc {rc2})",
             f"{done['steps_replayed']} replayed", f"{done['steps_executed']} run"),
            ("gate", f"{done['gates_parked']} parked, 10 deliveries each",
             f"{done['resumes_per_gate_max']} resume per gate",
             ),
            ("loop", done["loop"]["terminated_by"], f"{done['loop']['iterations_run']} iterations",
             done["loop"]["termination_class"]),
            ("effect", f"{len(effects)} row(s) in effects.jsonl", "1 expected", "no repeat"),
            ("budget", f"{done['spent_micros']} spent",
             f"{done['budget_remaining_micros']} left of {done['budget_ceiling_micros']}",
             "recomputed at resume"),
            ("outcome", done["outcome"], done["correlation_id"],
             f"correlation from {done['correlation_source']}")]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(w) for c, w in
                               zip(r + ("",) * 4, (10, 40, 26, 26))))
    return 0 if (rc2 == 0 and len(effects) == 1) else 1


if __name__ == "__main__":
    sys.exit(main())
