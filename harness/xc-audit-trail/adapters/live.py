#!/usr/bin/env python3
"""Live adapter: a projection over the chained append-only file this repository
already writes and checks. Reached only through AUDIT_TRAIL_LEDGER_PATH (README.md);
unset, every operation refuses as adapter-unavailable rather than guessing a path.

This is the first store xc-audit-trail-implement names: kb/ledger.jsonl via
tools/kb.py is "the JSONL evidence records PASS.md B3 names" (blueprint tool
entry). What it is missing today is not durability but attribution and an
index (adapter row, "cannot"): its records carry an `agent` field, not an
`actor`, no delegation chain, no correlation triple, and no entry kind, so
this adapter adds those at projection time from what the record already has
and marks the rest absent rather than guessing it. Its own chain integrity is
still checked the way this repository already checks it - `tools/kb.py
ledger-verify`, run as a guarded subprocess - and reported separately in
store_integrity() so that check is never mistaken for the audit chain's own
recompute, which run against the projected entries exactly as the other two
adapters' do (F-a7-04: no adapter may look verified by borrowing a check that
ran over different data).
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from interface import AppendRequest, AuditEntry, Problem, TrailAdapter, entry_hash  # noqa: E402

ENV_VAR = "AUDIT_TRAIL_LEDGER_PATH"


def _now() -> str:
    fixed = os.environ.get("TRAIL_CLOCK")
    dt = (datetime.datetime.fromisoformat(fixed.replace("Z", "+00:00")) if fixed
         else datetime.datetime.now(datetime.timezone.utc))
    return dt.isoformat().replace("+00:00", "Z")


class LiveLedgerTrailAdapter(TrailAdapter):
    entity = "projection over kb/ledger.jsonl (live)"
    execution_model = "the platform's own append-only file, read through tools/kb.py"
    adapter_kind = "jsonl-hash-chain"
    declared_gaps = ("pre-existing records carry no actor, delegation chain or correlation id; "
                     "coverage_start marks where projected attribution begins",)
    external_checkable = False

    def __init__(self):
        super().__init__()
        self._loaded = False
        self._entries: list[AuditEntry] = []
        self._seq = 0
        self._ledger_path = os.environ.get(ENV_VAR, "")

    def _load(self) -> None:
        if self._loaded:
            return
        if not self._ledger_path:
            raise Problem("adapter-unavailable",
                          f"set {ENV_VAR} to the path of the chained append-only file (see README.md)")
        if not os.path.isfile(self._ledger_path):
            raise Problem("adapter-unavailable", f"{self._ledger_path} does not exist")
        prev = "genesis"
        for line in open(self._ledger_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            actor = f"agent:{rec.get('agent')}" if rec.get("agent") else ""
            corr_id = rec.get("harness") or rec.get("skill") or rec.get("section") or ""
            chain = [{"actor": actor, "obtained_via": "direct"}] if actor else []
            action = rec.get("action") or rec.get("kind") or "ledger-record"
            at = rec.get("time", _now())
            h = entry_hash(prev, action, actor, tuple(chain),
                           {"run_id": rec.get("id", ""), "correlation_id": corr_id}, "agent", at)
            self._seq += 1
            self._entries.append(AuditEntry(
                entry_id="urn:agentic:audit:" + h[:24], seq=self._seq, prev=prev, hash=h,
                action=action, actor=actor, delegation_chain=tuple(chain),
                correlation={"run_id": rec.get("id", ""), "correlation_id": corr_id},
                kind="agent", at=at))
            prev = h
        self._loaded = True

    # --- writer path: appending live is out of scope for this harness ------
    def _append(self, entry) -> None:
        raise Problem("adapter-unavailable",
                      "this harness projects the live ledger read-only; it does not append to the "
                      "repository's own record")

    def _next_seq(self) -> int:
        self._load()
        return self._seq + 1

    def _clock(self) -> str:
        return _now()

    def _age_days(self, at: str) -> int:
        then = datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
        now = datetime.datetime.fromisoformat(_now().replace("Z", "+00:00"))
        return max(0, (now - then).days)

    # --- reads -------------------------------------------------------------
    def project(self, from_seq=None, to_seq=None) -> list:
        self._load()
        out = self._entries
        if from_seq is not None:
            out = [e for e in out if e.seq >= from_seq]
        if to_seq is not None:
            out = [e for e in out if e.seq <= to_seq]
        return list(out)

    def head(self) -> str:
        self._load()
        return self._entries[-1].hash if self._entries else "genesis"

    def coverage_start(self) -> str:
        self._load()
        for e in self._entries:
            if e.actor:
                return e.at
        return self._clock()

    def external_verifications(self) -> int:
        return 0     # this binding publishes nothing outside the repository

    def store_integrity(self) -> dict:
        """The repository's own chain check, run as a guarded subprocess - kept
        separate from the audit chain's own recompute (F-a7-04)."""
        self._load()
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        tool = os.path.join(root, "tools", "kb.py")
        verified, detail = False, "tools/kb.py not found"
        if os.path.isfile(tool):
            try:
                proc = subprocess.run([sys.executable, tool, "ledger-verify"], capture_output=True,
                                      text=True, cwd=root, timeout=30)
                detail = (proc.stdout or proc.stderr).strip()
                verified = proc.returncode == 0
            except Exception as exc:            # pragma: no cover - defensive only
                detail = str(exc)
        return {"kind": "kb.py ledger-verify (subprocess, guarded)", "entries": len(self._entries),
                "head": self.head(), "verified": verified, "detail": detail}
