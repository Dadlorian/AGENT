#!/usr/bin/env python3
"""Second dispatcher: queue-and-poll. No session at all.

Execution model, and the two axes on which it differs from the first shim:

  unit_lifetime      one request-response into an executor that runs somewhere
                     else - here, a one-shot worker process - instead of a
                     session held open in the dispatcher for the life of the unit.
  cancellation_reach none. The job is submitted, the worker starts, and nothing
                     can reach it before it finishes; a cancel accepted after
                     submission is honestly terminal as `cancel_timeout`, where
                     the first shim reports `cancelled`.

Because the executor keeps no journal and cannot be asked anything mid-flight,
the dispatcher's own step records are the only thing that makes resume and
replay work - which is exactly why the seam puts them there and not in the
executor. Run this adapter first after any shape change: a new dependence on a
held-open session, a callback or a host-side socket fails the day it is written.

This is the shape a hosted single-shot executor has; no product is named here.
The module doubles as its own worker (`--worker <job>`), which is what makes the
one-shot execution a real second process rather than a flag.

Python 3.11 standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import core  # noqa: E402
from adapters.base import SeamDispatcher, run_steps  # noqa: E402
from adapters.steplog import StepLog  # noqa: E402
from interface import Problem  # noqa: E402


class Adapter(SeamDispatcher):
    dispatcher_marker = "queue-and-poll-oneshot/0.1"
    unit_lifetime = "request_response"
    cancellation_reach = "none"
    keeps_own_journal = False
    executor_reached_over = "job queue directory"
    binding_role = "second"
    cost_read_mode = "snapshot-by-digest"
    breakable = False
    poll_interval_s = 0.01
    poll_timeout_s = 60

    def execute_unit(self, req_body: dict, plan: dict, prior: dict) -> dict:
        """Submit one job, poll for one terminal result. Nothing is held open
        between the two, and there is nothing to interrupt in between."""
        queue = os.path.join(self.out_dir, "queue")
        os.makedirs(queue, exist_ok=True)
        job_path = os.path.join(queue, req_body["dispatch_id"] + ".job.json")
        out_path = os.path.join(queue, req_body["dispatch_id"] + ".result.json")
        with open(job_path, "w") as fh:
            json.dump({"request": req_body, "plan": plan, "prior": prior,
                       "log": self.log.path, "result_path": out_path}, fh)
        proc = subprocess.Popen([sys.executable, os.path.abspath(__file__),
                                 "--worker", job_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + self.poll_timeout_s
        while time.monotonic() < deadline:
            if os.path.exists(out_path):
                return json.load(open(out_path))
            if proc.poll() is not None and not os.path.exists(out_path):
                err = proc.stderr.read().decode()[-400:]
                raise Problem("adapter-unavailable",
                              f"the one-shot executor exited without a result: {err}",
                              dispatch_id=req_body["dispatch_id"])
            time.sleep(self.poll_interval_s)
        raise Problem("deadline-exceeded",
                      f"no terminal result within {self.poll_timeout_s}s of polling",
                      dispatch_id=req_body["dispatch_id"])


def worker(job_path: str) -> int:
    """The one-shot executor. It reads nothing while it runs and is reachable by
    nothing while it runs; there is no cancel probe here because there is
    nowhere for one to arrive."""
    job = json.load(open(job_path))
    outcome = run_steps(job["request"], job["plan"], StepLog(job["log"]),
                        core.example.DryRunAdapter().complete,
                        lambda: False, job["prior"])
    # Written atomically: the poller in execute_unit learns the result exists
    # by os.path.exists(result_path), and open()+dump() would let it see that
    # name the instant it is created (truncated to zero bytes) rather than
    # once it is complete - a race that reads as a JSONDecodeError or a
    # FileNotFoundError depending on timing. Writing to a same-directory temp
    # file first and renaming into place means the final name never appears
    # until the content behind it is whole; os.replace is one atomic syscall
    # on POSIX, so there is no window in which the name exists but the body
    # does not.
    tmp_path = job["result_path"] + f".{os.getpid()}.tmp"
    with open(tmp_path, "w") as fh:
        json.dump(outcome, fh)
    os.replace(tmp_path, job["result_path"])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The one-shot executor behind the second shim.")
    ap.add_argument("--worker", required=True, help="path to the job document")
    sys.exit(worker(ap.parse_args().worker))
