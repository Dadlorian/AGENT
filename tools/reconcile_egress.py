#!/usr/bin/env python3
"""Reconcile kb/egress-log.jsonl (the egress proxy's own access-decision log) against
kb/research.jsonl (the research-record file), per the A2-F closure check:

  "every URL cited with status 'search-only' has a matching allow decision in the log,
   and every EGRESS_BLOCKED event has a corresponding record rather than being silently
   dropped."

Generalised to all three statuses (search-only, fetched, blocked), since a mature build
must reconcile fetched and blocked the same way it reconciles search-only:

  R1  every research record with status in {search-only, fetched} has exactly one log
      entry with decision=allow, research_id equal to the record's id.
  R2  every log entry with decision=block has research_id set, and that id names a
      research record with status=blocked -- a block that names no record, or one that
      names a record in the wrong status, is a blocked attempt silently dropped from the
      citation trail.
  R3  every research record with status=blocked has exactly one log entry with
      decision=block, research_id equal to the record's id -- the reverse of R2: a
      "blocked" claim with no proxy decision behind it is a claim invented rather than
      corroborated.

Exit 0 and print a summary when all three hold for every record. Exit 1 and list every
violation, one per line, otherwise.

Usage: python3 tools/reconcile_egress.py [--research PATH] [--log PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESEARCH = ROOT / "kb" / "research.jsonl"
DEFAULT_LOG = ROOT / "kb" / "egress-log.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def reconcile(research: list[dict], log: list[dict]) -> list[str]:
    problems: list[str] = []
    by_research_id: dict[str, list[dict]] = {}
    for row in log:
        by_research_id.setdefault(row.get("research_id"), []).append(row)

    research_by_id = {r["id"]: r for r in research}

    # R1 + reverse of R2/R3 bookkeeping: walk every research record.
    for rec in research:
        rid = rec["id"]
        status = rec["status"]
        matches = by_research_id.get(rid, [])
        if len(matches) != 1:
            problems.append(f"R1: {rid} (status {status}) has {len(matches)} egress-log entries, want exactly 1")
            continue
        entry = matches[0]
        if status in ("search-only", "fetched"):
            if entry["decision"] != "allow":
                problems.append(f"R1: {rid} is status {status} but its egress-log entry {entry['id']} is decision={entry['decision']}, want allow")
        elif status == "blocked":
            if entry["decision"] != "block":
                # R3: a blocked claim with no block decision behind it
                problems.append(f"R3: {rid} is status blocked but its egress-log entry {entry['id']} is decision={entry['decision']}, want block")
        else:
            problems.append(f"{rid}: unknown status {status!r}")

    # R2: every block decision must be claimed by a blocked research record, not dropped.
    for row in log:
        if row["decision"] != "block":
            continue
        rid = row.get("research_id")
        if rid is None:
            problems.append(f"R2: {row['id']} (host {row['host']}) is a block decision with no research_id -- a blocked attempt silently dropped from the citation trail")
            continue
        rec = research_by_id.get(rid)
        if rec is None:
            problems.append(f"R2: {row['id']} names research_id {rid}, which does not exist in kb/research.jsonl")
        elif rec["status"] != "blocked":
            problems.append(f"R2: {row['id']} is a block decision naming {rid}, but {rid} is status {rec['status']}, not blocked")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--research", default=str(DEFAULT_RESEARCH))
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    args = ap.parse_args()

    research = read_jsonl(Path(args.research))
    log = read_jsonl(Path(args.log))

    problems = reconcile(research, log)

    n_search_only = sum(1 for r in research if r["status"] == "search-only")
    n_fetched = sum(1 for r in research if r["status"] == "fetched")
    n_blocked = sum(1 for r in research if r["status"] == "blocked")
    n_allow = sum(1 for r in log if r["decision"] == "allow")
    n_block = sum(1 for r in log if r["decision"] == "block")
    print(f"research: {len(research)} records ({n_search_only} search-only, {n_fetched} fetched, {n_blocked} blocked)")
    print(f"egress-log: {len(log)} decisions ({n_allow} allow, {n_block} block)")

    if problems:
        print(f"NOT RECONCILED: {len(problems)} problem(s)")
        for p in problems:
            print(f"  FAIL {p}")
        return 1

    print(f"RECONCILED: every search-only/fetched record has a matching allow decision, "
          f"every block decision names a blocked record, no blocked attempt was dropped ({n_block} block event(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
