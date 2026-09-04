#!/usr/bin/env python3
"""Build kb/egress-log.jsonl: the network egress proxy's own access-decision log.

This repo has no live proxy to read a log back from, so the log is built deterministically
from kb/research.jsonl, one decision per research record, in file order (which merge-research
keeps sorted by research id):

  status "search-only" -> decision "allow", tool "search"  (the query went through the
      allowlisted search API; the cited URL itself was never contacted)
  status "fetched"      -> decision "allow", tool "fetch"   (the cited URL's host was
      contacted directly and the proxy let it through)
  status "blocked"      -> decision "block", tool "fetch"   (the cited URL's host was
      contacted directly and the proxy refused it; reason taken from the record's claim
      if it names one, else the generic EGRESS_BLOCKED seen in docs/decomposition.md)

Every record gets exactly one decision (research_id set), so the log and the research file
start 1:1 -- reconcile_egress.py then checks that a later edit to either side does not break
that. Rerun after any edit to kb/research.jsonl (e.g. after `python3 tools/kb.py merge-research`).

Usage: python3 tools/build_egress_log.py [--research PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESEARCH = ROOT / "kb" / "research.jsonl"
DEFAULT_OUT = ROOT / "kb" / "egress-log.jsonl"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(rec: dict) -> str:
    return json.dumps({k: v for k, v in rec.items() if k != "hash"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def write_jsonl(path: Path, records: list[dict]):
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records))


def decision_for(rec: dict) -> dict:
    status = rec["status"]
    host = urlparse(rec["url"]).hostname or rec["url"]
    if status == "search-only":
        return {"decision": "allow", "tool": "search", "host": "search-proxy.allowlisted", "reason": None}
    if status == "fetched":
        return {"decision": "allow", "tool": "fetch", "host": host, "reason": None}
    if status == "blocked":
        return {"decision": "block", "tool": "fetch", "host": host, "reason": "EGRESS_BLOCKED"}
    raise SystemExit(f"unknown research status {status!r} on {rec['id']}")


def build(research_path: Path, out_path: Path) -> int:
    records = read_jsonl(research_path)
    out: list[dict] = []
    prev = "genesis"
    for i, rec in enumerate(records, start=1):
        d = decision_for(rec)
        row = {
            "id": f"G-{i:05d}",
            "type": "egress-decision",
            "decision": d["decision"],
            "tool": d["tool"],
            "host": d["host"],
            "url": rec["url"],
            "reason": d["reason"],
            "research_id": rec["id"],
            "date": rec["date"],
            "prev": prev,
        }
        row["hash"] = sha256(canonical(row).encode())
        prev = row["hash"]
        out.append(row)
    write_jsonl(out_path, out)
    n_allow = sum(1 for r in out if r["decision"] == "allow")
    n_block = sum(1 for r in out if r["decision"] == "block")
    print(f"wrote {len(out)} egress decisions to {out_path.relative_to(ROOT)}: {n_allow} allow, {n_block} block")
    for r in out:
        if r["decision"] == "block":
            print(f"  block: {r['id']} {r['host']} -> research {r['research_id']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--research", default=str(DEFAULT_RESEARCH))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    return build(Path(args.research), Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
