#!/usr/bin/env python3
"""Runnable check for cap-scheduling's ticker-ownership closure (C14-F).

Property: kill the active ticker process and a new leader is elected and
resumes firing within a bounded window, with no duplicate or missed
occurrence at the handoff boundary.

    python3 harness/scheduling/tests/leader_failover_check.py                    # exits 0: property holds
    LEADER_ELECTION=0 python3 harness/scheduling/tests/leader_failover_check.py   # deliberate breakage: exits 1

LEADER_ELECTION=0 passes --no-election to both spawned leader_ticker.py
processes, so neither elects before touching the shared queue -- each
behaves as a single unelected process silently assumed to be the only one
running (the alternative the closure names as being abandoned). Two such
processes racing one queue file duplicate or drop occurrences, which the
assertions below are what notices; nothing here waits for or expects that
outcome; it is on this check by construction.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time

SCHED_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(SCHED_DIR, "out", "leader-election")

N_MESSAGES = 12
FIRE_DELAY_S = 0.15
KILL_AFTER_FIRED = 4
POLL_S = 0.03
TAKEOVER_BOUND_S = 3.0          # "resumes firing within a bounded window"
DRAIN_TIMEOUT_S = 12.0          # outer bound so the check itself terminates


def read_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def wait_until(predicate, timeout_s: float, interval_s: float = 0.02):
    deadline = time.time() + timeout_s
    result = predicate()
    while not result and time.time() < deadline:
        time.sleep(interval_s)
        result = predicate()
    return result


def main() -> int:
    elect = os.environ.get("LEADER_ELECTION", "1") != "0"

    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)

    lease_path = os.path.join(WORK, "lease.lock")
    queue_path = os.path.join(WORK, "queue.jsonl")
    fired_path = os.path.join(WORK, "fired.jsonl")
    leadership_path = os.path.join(WORK, "leadership.jsonl")
    decl_path = os.path.join(WORK, "declarations.json")
    err1_path = os.path.join(WORK, "T1.stderr")
    err2_path = os.path.join(WORK, "T2.stderr")

    with open(decl_path, "w") as fh:
        json.dump([{"unit_ref": "nightly-report", "recurrence": "FREQ=DAILY",
                    "starts_at": "2026-01-01T00:00:00", "timezone": "UTC", "catch_up": "skip"}], fh)

    with open(queue_path, "w") as fh:
        for i in range(N_MESSAGES):
            month = 1 + i // 28
            day = 1 + i % 28
            fh.write(json.dumps({"unit_ref": "nightly-report",
                                 "occurrence": f"2026-{month:02d}-{day:02d}T00:00:00Z"}) + "\n")

    def spawn(ticker_id: str, err_path: str) -> subprocess.Popen:
        cmd = [sys.executable, os.path.join(SCHED_DIR, "leader_ticker.py"),
              "--id", ticker_id, "--lease", lease_path, "--queue", queue_path,
              "--fired", fired_path, "--leadership", leadership_path,
              "--declarations", decl_path, "--poll", str(POLL_S), "--fire-delay", str(FIRE_DELAY_S)]
        if not elect:
            cmd.append("--no-election")
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=open(err_path, "w"))

    p1 = spawn("T1", err1_path)
    p2 = spawn("T2", err2_path)
    procs = {"T1": p1, "T2": p2}

    try:
        got_first_batch = wait_until(lambda: len(read_jsonl(fired_path)) >= KILL_AFTER_FIRED, timeout_s=5.0)
        if not got_first_batch:
            print(f"FAIL: fewer than {KILL_AFTER_FIRED} occurrences fired before timeout "
                 f"(fired={len(read_jsonl(fired_path))})")
            return 1

        leaders_before = read_jsonl(leadership_path)
        if not leaders_before:
            print("FAIL: no leader was ever elected")
            return 1
        leader_id = leaders_before[0]["leader"]
        victim = procs[leader_id]
        kill_time = time.time()
        victim.send_signal(signal.SIGKILL)
        victim.wait(timeout=5)

        resumed = wait_until(lambda: len(read_jsonl(fired_path)) >= N_MESSAGES, timeout_s=DRAIN_TIMEOUT_S)

        fired = read_jsonl(fired_path)
        leaders_after = read_jsonl(leadership_path)
        keys = [f["idempotency_key"] for f in fired]
        occs = [f["occurrence"] for f in fired]
        distinct_leaders = sorted({row["leader"] for row in leaders_after})

        failures = []
        if len(fired) != N_MESSAGES:
            failures.append(f"missed occurrence(s): fired {len(fired)} of {N_MESSAGES}")
        if len(set(keys)) != len(keys):
            failures.append(f"duplicate occurrence(s): {len(keys) - len(set(keys))} "
                            f"idempotency key(s) fired more than once")
        if len(set(occs)) != len(occs):
            failures.append("duplicate occurrence instant(s) fired more than once")
        if len(distinct_leaders) < 2:
            failures.append(f"no failover observed: only {distinct_leaders} ever led")
        else:
            new_leader_rows = [r for r in leaders_after if r["leader"] != leader_id and r["at"] >= kill_time]
            if not new_leader_rows:
                failures.append("no new leader was elected after the kill")
            elif new_leader_rows[0]["at"] - kill_time > TAKEOVER_BOUND_S:
                failures.append(f"failover took {new_leader_rows[0]['at'] - kill_time:.2f}s, "
                                f"over the {TAKEOVER_BOUND_S}s bound")
        if not resumed:
            failures.append(f"drain did not complete within {DRAIN_TIMEOUT_S}s "
                            f"(only {len(fired)}/{N_MESSAGES} fired)")

        summary = (f"election={'on' if elect else 'off (deliberate breakage)'} "
                  f"leaders={distinct_leaders} fired={len(fired)}/{N_MESSAGES} "
                  f"distinct_keys={len(set(keys))} killed={leader_id}")
        if failures:
            for f in failures:
                print(f"FAIL: {f}")
            print(summary)
            return 1

        print(f"OK: {summary}")
        return 0
    finally:
        for p in procs.values():
            if p.poll() is None:
                p.send_signal(signal.SIGKILL)
                try:
                    p.wait(timeout=5)
                except Exception:
                    pass


if __name__ == "__main__":
    sys.exit(main())
