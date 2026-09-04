#!/usr/bin/env python3
"""The ticker that drives cap-scheduling's pure evaluator, with exactly one
instance active at a time.

Closure for C14-F (cap-scheduling SKILL.md, Open questions: "Where does the
occurrence-instant clock come from once evaluation is pure, and who owns the
ticker that asks it?"): a single ticker instance is active at a time, chosen
and re-chosen by leader election over a consensus protocol, and it asks the
pure evaluator (interface.py, reached here through adapters.dryrun's fire())
for occurrences and drains a queue of them; it owns no scheduling logic of
its own -- FREQ/BYDAY/leap-day/DST math never appears below this line.

Election here is a held file lock (fcntl.flock, LOCK_EX): a process is
leader for exactly as long as it holds that lock, and the moment its process
dies the kernel releases the lock for it -- the same contract a real
consensus store gives a leader (an etcd lease or a ZooKeeper ephemeral znode:
leadership is tied to a live session, and the session ending is what frees
it for the next claimant), given here as a single-host advisory lock instead
of a distributed lock service, on the same axis adapters/second.py already
uses a JSONL file as a stand-in for a durable queue: what is swappable is the
store behind the primitive, not the primitive's contract (T-t2-02). A
deployment with more than one host swaps LeaseFile's flock for etcd/ZooKeeper
without the election loop below changing at all.

--no-election is the mechanism this file exists to demonstrate the absence
of: every process just assumes "got = True" unconditionally, i.e. it behaves
as a single unelected process silently assumed to be the only one running
(the alternative the closure names as being abandoned). Run two of them
against one shared queue with it set and the queue is drained twice.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adapters.dryrun import DryRunAdapter  # noqa: E402


class LeaseFile:
    """An exclusive advisory lock (fcntl.flock) held on one file. try_acquire
    is non-blocking so a follower can poll it in the same loop that also
    checks for shutdown; release() (and process death) both free it via the
    kernel, atomically, with no read-then-write race for two processes to
    fall into -- the property a lease store must have to be a real election
    primitive rather than a TTL guess."""

    def __init__(self, path: str):
        self.path = path
        self._fh = None

    def try_acquire(self) -> bool:
        if self._fh is not None:
            return True   # already held by this process
        os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".", exist_ok=True)
        fh = open(self.path, "a+")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self._fh = fh
        return True

    def release(self) -> None:
        if self._fh is not None:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()
            self._fh = None


def _append_json(path: str, doc: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(doc) + "\n")


def _read_queue(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _write_queue(path: str, messages: list) -> None:
    with open(path, "w") as fh:
        for m in messages:
            fh.write(json.dumps(m) + "\n")


def run(ticker_id: str, lease_path: str, queue_path: str, fired_path: str,
        leadership_path: str, declarations_path: str, poll_s: float,
        fire_delay_s: float, elect: bool) -> None:
    adapter = DryRunAdapter()
    with open(declarations_path) as fh:
        for doc in json.load(fh):
            adapter.declare(doc)

    lease = LeaseFile(lease_path)
    is_leader = False
    try:
        while True:
            if not is_leader:
                # step 5 of cap-scheduling-implement stays the ticker's only
                # job here: ask "am I the one asking the evaluator", nothing
                # about the rule. --no-election answers that question with a
                # constant instead of an election (the breakage this file
                # exists to show).
                got = lease.try_acquire() if elect else True
                if got:
                    is_leader = True
                    _append_json(leadership_path, {"leader": ticker_id, "at": time.time()})

            if is_leader:
                queued = _read_queue(queue_path)
                if queued:
                    message, remaining = queued[0], queued[1:]
                    # Dequeue before firing: only the leader ever reaches this
                    # line (elect=True) or, under the deliberate breakage,
                    # both processes race it unsynchronized -- that race is
                    # exactly what the check's duplicate/missed assertions
                    # are built to catch.
                    _write_queue(queue_path, remaining)
                    envelope = adapter.fire(message["unit_ref"], message["occurrence"])
                    _append_json(fired_path, {"ticker": ticker_id,
                                              "idempotency_key": envelope["idempotency_key"],
                                              "occurrence": message["occurrence"],
                                              "at": time.time()})
                    time.sleep(fire_delay_s)
                    continue  # check the queue again immediately

            time.sleep(poll_s)
    finally:
        lease.release()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--lease", required=True)
    ap.add_argument("--queue", required=True)
    ap.add_argument("--fired", required=True)
    ap.add_argument("--leadership", required=True)
    ap.add_argument("--declarations", required=True)
    ap.add_argument("--poll", type=float, default=0.03)
    ap.add_argument("--fire-delay", type=float, default=0.1)
    ap.add_argument("--no-election", action="store_true",
                    help="deliberate breakage: skip the lease, assume sole ownership")
    args = ap.parse_args()
    run(args.id, args.lease, args.queue, args.fired, args.leadership, args.declarations,
        args.poll, args.fire_delay, elect=not args.no_election)
    return 0


if __name__ == "__main__":
    sys.exit(main())
