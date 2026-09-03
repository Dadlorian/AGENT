#!/usr/bin/env python3
"""The admitting process: the same chain, run where the traffic has to cross it.

This program is the second enforcement point. It is not a library the unit
calls: it is a process in front of the unit that reads one request per line on
stdin and writes one response per line on stdout. It runs the same declared
slots, in the same declared order, through the same evaluate() the in-process
point uses - which is why the two produce identical chain records - and it keeps
the claim table and the reservations itself, so a unit that never asked it for a
context has nothing to present at a metered call.

    echo '{"op":"traverse","point":"admission","unit":{...}}' | python3 edge.py

Requests: traverse (point, unit) -> rows; seal (context) -> ok; ping -> ok.
Python 3.11 standard library only. No product name appears here.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface import Unit, slot_rows                                    # noqa: E402


def main() -> int:
    state: dict = {}
    issued: set[str] = set()          # the contexts this process handed out
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request = json.loads(line)
        op = request.get("op")
        if op == "traverse":
            unit = Unit(**request["unit"])
            rows = slot_rows(request["point"], unit, state)
            if not any(r["outcome"] == "refused" for r in rows):
                issued.add(f"{unit.unit_id}:{request['point']}")
            response = {"rows": rows}
        elif op == "seal":
            context = request["context"]
            issued.discard(f"{context['unit_id']}:{context['point']}")
            response = {"ok": True, "held": len(issued)}
        elif op == "ping":
            response = {"ok": True, "issued": len(issued)}
        else:
            response = {"error": f"unknown op {op!r}"}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
