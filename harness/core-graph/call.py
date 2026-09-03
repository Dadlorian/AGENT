#!/usr/bin/env python3
"""The minimal call: assert a typed graph, refuse an ill-typed edge with no
store attached, expand one step, retract an edge, and swap the store.

    ADAPTER=dryrun python3 harness/core-graph/call.py

Everything below the CALLER CODE marker is what a caller writes. Everything
above it is the platform: it derives the actor and stamps it onto every
assertion (F-b1-08, cap-consumption), and it binds one of three adapters from
one environment variable. assert_sample() is the one shared assertion path
every producer maps into (core-graph-implement step 2); it lives above the
marker exactly as state-persistence's request() helper does, because it is
called identically against two stores below to prove the swap.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import Problem, assert_edge, validate                              # noqa: E402
from adapters.dryrun import DryRunAdapter                                          # noqa: E402
from adapters.live import LiveLedgerAdapter                                        # noqa: E402
from adapters.second import EventLogAdapter                                        # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveLedgerAdapter, "second": EventLogAdapter}
IDS = {"iface": "iface-sort", "impl": "impl-quicksort", "doc": "doc-spec", "step": "step-implement"}


def assert_sample(adapter, actor: str) -> dict:
    """One node of three kinds and one edge of each of the three edge kinds."""
    nodes = {"iface": ("interface", "Sort interface"), "impl": ("implementation", "Quicksort"),
             "doc": ("document", "Spec document"), "step": ("step", "Implement sort")}
    out = {}
    for key, (kind, label) in nodes.items():
        out[key] = adapter.append_node({"node_id": IDS[key], "kind": kind, "label": label, "asserted_by": actor})
    edges = [("edge-impl", "implementation", IDS["impl"], IDS["iface"]),
            ("edge-exist", "existence", IDS["doc"], IDS["step"]),
            ("edge-iface", "interface", IDS["step"], IDS["iface"])]
    for edge_id, edge_type, frm, to in edges:
        adapter.append_edge({"edge_id": edge_id, "edge_type": edge_type, "from": frm, "to": to, "asserted_by": actor})
    return out


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all five harnesses use.
# --------------------------------------------------------------------------
def main() -> int:
    actor = os.environ.get("ACTOR", "user:corey")
    primary = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()   # configuration, not code
    other = ADAPTERS["second"] if os.environ.get("ADAPTER", "dryrun") != "second" else DryRunAdapter
    counterpart = other()
    try:
        nodes = assert_sample(primary, actor)                    # one node + one edge of each of 3 kinds
        try:                                                     # ill-typed, no store attached at all
            assert_edge({"edge_id": "bad", "edge_type": "implementation", "from": IDS["doc"], "to": IDS["iface"]},
                        {"iface": nodes["iface"], "doc": nodes["doc"]})
            refused = None
        except Problem as problem:
            refused = problem.body["type"]
        implementers = primary.neighbors(IDS["iface"], "implementation", direction="in")   # expand one step
        primary.retract_edge("edge-exist", "no longer applies", actor)
        assert_sample(counterpart, actor)                         # the same assertions on the other store
        counterpart.retract_edge("edge-exist", "no longer applies", actor)
    except Problem as problem:                                    # one refusal shape, branched on type
        print("PROBLEM (application/problem+json):")
        print(problem.body)
        return 2
    rep_a, rep_b = validate(primary.graph_value()), validate(counterpart.graph_value())
    same = (rep_a.nodes_checked, rep_a.edges_checked, rep_a.rejections, rep_a.false_accepts) == \
          (rep_b.nodes_checked, rep_b.edges_checked, rep_b.rejections, rep_b.false_accepts)
    table([(primary.entity[:28], refused, len(implementers), "edge-exist" not in primary.graph_value().edges, same)],
          ("store", "ill_typed_refused_as", "implementers_found", "retracted", "both_stores_agree"))
    return 0 if refused and implementers and same else 1


if __name__ == "__main__":
    sys.exit(main())
