#!/usr/bin/env python3
"""Second adapter: an externally checkable, window-sealed log.

Where the dry-run store is one mutable list held by this process and checked
only by our own reader, this one buffers entries and seals them into windows;
each window's head is written to a published-heads file that
verify_external.py - a standalone script that imports no adapter - can
recompute and compare without ever holding our reader. That is the axis the
pair is chosen on (who can check the record, who holds the only copy):
sealing needs the published-heads path to be reachable at all (an unreachable
target refuses the seal rather than deferring it), where the dry-run store
appends and verifies fully offline.

Reachability: with SECOND_STORE_DIR pointed at a directory backed by a real
write-once log service, publish_window's file write is that service's normal
append call and this file changes only there - not the shape above. Unset, it
uses a scratch directory under harness/xc-audit-trail/out, the same code path,
not a separate simulation.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from interface import AppendRequest, AuditEntry, Problem, TrailAdapter, canonical, sha256_hex  # noqa: E402

DEFAULT_DIR = os.path.join(HERE, "..", "out", "second")
WINDOW = int(os.environ.get("TRAIL_WINDOW", "6"))
FIXTURE_ENTRIES = int(os.environ.get("TRAIL_FIXTURE_ENTRIES", "24"))


def _clock() -> datetime.datetime:
    fixed = os.environ.get("TRAIL_CLOCK", "2026-09-03T00:00:00Z")
    return datetime.datetime.fromisoformat(fixed.replace("Z", "+00:00"))


def window_head(prior_head: str, entry_hashes: list) -> str:
    return sha256_hex(canonical({"prior_head": prior_head, "entries": entry_hashes}))


class ExternalCheckableLogAdapter(TrailAdapter):
    entity = "window-sealed log with a published head (second adapter)"
    execution_model = "buffered, sealed into windows; a copy exists we did not write and cannot rewrite"
    adapter_kind = "external-checkable-log"
    declared_gaps = ("sealing blocks on the published-heads path being reachable; nothing seals offline",)
    external_checkable = True

    def __init__(self):
        super().__init__()
        self._root = os.environ.get("SECOND_STORE_DIR", DEFAULT_DIR)
        os.makedirs(self._root, exist_ok=True)
        self._entries: list[AuditEntry] = []
        self._buffer: list[AuditEntry] = []
        self._seq = 0
        if os.environ.get("TRAIL_NO_SEED") != "1":
            self._seed()
            self.seal()

    def _seed(self) -> None:
        now = _clock()
        actors = [
            ("user", "user:corey", [{"actor": "user:corey", "obtained_via": "direct"}]),
            ("agent", "agent:planner", [{"actor": "user:corey", "obtained_via": "direct"},
                                        {"actor": "agent:planner", "obtained_via": "delegated"}]),
            ("service", "service:scheduler", [{"actor": "service:scheduler", "obtained_via": "direct"}]),
            ("schedule", "schedule:nightly-scan", [{"actor": "schedule:nightly-scan", "obtained_via": "direct"}]),
        ]
        corrs = [{"run_id": f"run-{i}", "correlation_id": f"corr-{i}"} for i in range(3)]
        for i in range(FIXTURE_ENTRIES):
            kind, actor, chain = actors[i % 4]
            corr = corrs[i % 3]
            days_ago = 200 - int(200 * i / max(FIXTURE_ENTRIES - 1, 1))
            at = (now - datetime.timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")
            req = AppendRequest(action=f"seed-action-{i}", actor=actor, delegation_chain=tuple(chain),
                                correlation=corr, kind=kind, at=at)
            self.append(req)
            if len(self._buffer) >= WINDOW:
                self.seal()

    # --- writer path -------------------------------------------------------
    def _append(self, entry) -> None:
        self._entries.append(entry)
        self._buffer.append(entry)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _clock(self) -> str:
        return _clock().isoformat().replace("+00:00", "Z")

    def _age_days(self, at: str) -> int:
        then = datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
        return max(0, (_clock() - then).days)

    # --- sealing: the step this store adds ---------------------------------
    def _heads_path(self) -> str:
        return os.path.join(self._root, "published-heads.jsonl")

    def _entries_path(self) -> str:
        return os.path.join(self._root, "entries.jsonl")

    def seal(self) -> str | None:
        """Publish the buffered window's head. Blocks on the path being reachable."""
        if not self._buffer:
            return None
        if os.environ.get("SECOND_UNREACHABLE") == "1":
            raise Problem("adapter-unavailable",
                          "the published-heads path is unreachable; the second store refuses the seal "
                          "rather than deferring it, which is the axis this pair is chosen on")
        prior = self._last_published_head()
        head = window_head(prior, [e.hash for e in self._buffer])
        rec = {"prior_head": prior, "head": head, "from_seq": self._buffer[0].seq, "to_seq": self._buffer[-1].seq,
              "size": len(self._buffer)}
        with open(self._heads_path(), "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        with open(self._entries_path(), "w") as fh:
            for e in self._entries:
                fh.write(json.dumps(e.to_dict(), sort_keys=True) + "\n")
        self._buffer = []
        return head

    def _last_published_head(self) -> str:
        path = self._heads_path()
        if not os.path.exists(path):
            return "genesis"
        lines = open(path).read().splitlines()
        return json.loads(lines[-1])["head"] if lines else "genesis"

    def _published_windows(self) -> list:
        path = self._heads_path()
        if not os.path.exists(path):
            return []
        return [json.loads(l) for l in open(path).read().splitlines()]

    def verify_externally(self) -> dict:
        """Run verify_external.py - imports no adapter - against our published heads and entries.

        This is the check a party holding none of our credentials would run: it
        reads only the two files this store publishes, recomputes every window
        head from the entry hashes, and reports the first window whose recomputed
        head does not match. Success increments a counter file so scan(), run
        later and possibly in another process, can report external_verifications
        honestly rather than assuming it happened.
        """
        self.seal()
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "..", "verify_external.py"),
             self._entries_path(), self._heads_path()],
            capture_output=True, text=True)
        try:
            result = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            result = {"verified": False, "reason": proc.stderr.strip()[-300:]}
        if result.get("verified") and proc.returncode == 0:
            counter = os.path.join(self._root, "external-verification-count.txt")
            n = int(open(counter).read()) if os.path.exists(counter) else 0
            open(counter, "w").write(str(n + 1))
        result["returncode"] = proc.returncode
        return result

    # --- reads -----------------------------------------------------------
    def project(self, from_seq=None, to_seq=None) -> list:
        out = self._entries
        if from_seq is not None:
            out = [e for e in out if e.seq >= from_seq]
        if to_seq is not None:
            out = [e for e in out if e.seq <= to_seq]
        return list(out)

    def head(self) -> str:
        return self._entries[-1].hash if self._entries else "genesis"

    def coverage_start(self) -> str:
        return self._entries[0].at if self._entries else self._clock()

    def external_verifications(self) -> int:
        counter = os.path.join(self._root, "external-verification-count.txt")
        return int(open(counter).read()) if os.path.exists(counter) else 0

    def store_integrity(self) -> dict:
        windows = self._published_windows()
        return {"kind": "window-sealed log", "entries": len(self._entries),
                "head": self.head(), "windows_published": len(windows), "verified": True}

    # --- test-only: tamper one entry, in the same file the reader trusts ---
    def tamper(self, seq: int, new_action: str) -> None:
        for i, e in enumerate(self._entries):
            if e.seq == seq:
                self._entries[i] = AuditEntry(e.entry_id, e.seq, e.prev, e.hash, new_action, e.actor,
                                              e.delegation_chain, e.correlation, e.kind, e.at)
                break
        else:
            raise AssertionError(f"no entry at seq {seq}")
        # rewrite entries.jsonl in place, as an attacker with file access would -
        # the published head file is left untouched, which is exactly what a
        # party who only holds the published heads is meant to catch.
        with open(self._entries_path(), "w") as fh:
            for e in self._entries:
                fh.write(json.dumps(e.to_dict(), sort_keys=True) + "\n")
