#!/usr/bin/env python3
"""The integrity scan, run as its own process.

    python3 scan.py --adapter dryrun --identity actor:scanner --scheduled
    python3 scan.py --adapter dryrun --identity actor:writer-process   # the breakage: inline, unscheduled

independent and scheduled are never assumed - they are read from the
--identity and --scheduled flags this invocation was actually given, compared
against the adapter's own writer_identity (F-a7-04). Exits non-zero, naming
the identity, whenever independent or scheduled comes back false: a scan is
not evidence of anything if the process that ran it is the one that appends.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import Problem  # noqa: E402


def adapters():
    from adapters.dryrun import LocalChainedTrailAdapter
    from adapters.live import LiveLedgerTrailAdapter
    from adapters.second import ExternalCheckableLogAdapter
    return {"dryrun": LocalChainedTrailAdapter, "live": LiveLedgerTrailAdapter,
            "second": ExternalCheckableLogAdapter}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", choices=("dryrun", "live", "second"), default="dryrun")
    ap.add_argument("--identity", default="actor:scanner")
    ap.add_argument("--scheduled", action="store_true")
    ap.add_argument("--min-entries", type=int, default=1)
    ap.add_argument("--report", help="write the report JSON here")
    args = ap.parse_args(argv)

    adapter = adapters()[args.adapter]()
    try:
        report = adapter.scan(args.identity, args.scheduled)
    except Problem as problem:
        print(json.dumps(problem.body))
        return 2
    doc = report.to_dict()
    doc["min_entries"] = args.min_entries
    if args.report:
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        json.dump(doc, open(args.report, "w"), indent=1, sort_keys=True)
    print(json.dumps(doc, sort_keys=True))

    if doc["entries_checked"] < args.min_entries:
        print(f"scan-refused: only {doc['entries_checked']} entries, wanted >= {args.min_entries}")
        return 1
    if not doc["independent"] or not doc["scheduled"]:
        print(f"scan-not-independent: identity={args.identity} independent={doc['independent']} "
              f"scheduled={doc['scheduled']}")
        return 1
    if doc["chain_breaks"]:
        print(f"chain-broken: {doc['chain_breaks']} break(s), first at seq {doc['first_break_at']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
