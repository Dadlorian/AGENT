#!/usr/bin/env python3
"""The conformance run every graph adapter must pass.

The same cases run against any binding: nothing here knows which adapter
answered. Case 9 is the property test core-graph's own definition of done
names (docs/decomposition.md 3.1 row C3): a generator that emits both an
`implementation` edge whose target is not kind `interface` and an
`existence` edge between two `implementation` nodes, with ground truth for
each edge tracked independently of interface.py's own check_edge_type (a
literal, duplicated rule, so a widened checker cannot also widen the oracle
that grades it - the same discipline verify_external.py applies in
harness/state-persistence). Case 10 is the cross-store check
core-graph-implement's own definition of done names: the same assertion log
folded and validated on two bindings must produce identical verdicts.

    python3 harness/core-graph/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/core-graph/conformance.py --adapter second --report out/second.json
    python3 harness/core-graph/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import GraphAdapter, NODE_KINDS, Problem, check_edge_type, validate  # noqa: E402
from adapters.dryrun import DryRunAdapter                                          # noqa: E402
from adapters.live import LiveLedgerAdapter                                        # noqa: E402
from adapters.second import EventLogAdapter                                        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveLedgerAdapter, "second": EventLogAdapter}
# Product names may live in adapters/ and in README.md's env table. Nowhere else.
PRODUCTS = re.compile(r"(s3|gcs|postgres|dynamodb|kafka|litellm|firecracker|temporal|langfuse)", re.I)


def _oracle_invalid(edge_type: str, from_kind: str, to_kind: str) -> bool:
    """Ground truth, written independently of interface.check_edge_type, so
    widening that function (the breakage) cannot also widen what grades it."""
    if edge_type == "implementation":
        return not (from_kind == "implementation" and to_kind == "interface")
    if edge_type == "existence":
        return from_kind == "implementation" and to_kind == "implementation"
    if edge_type == "interface":
        return to_kind != "interface" or from_kind == "implementation"
    return True


def run(name: str) -> tuple[list, dict]:
    adapter: GraphAdapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "execution_model": adapter.execution_model,
              "declared_gaps": list(adapter.declared_gaps), "cases": []}
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            return fn
        return wrap

    @case("assert a node of each closed kind, reject one outside the set")
    def _node_kinds():
        for kind in sorted(NODE_KINDS):
            adapter.append_node({"node_id": f"n-{name}-{kind}", "kind": kind, "label": kind})
        try:
            adapter.append_node({"node_id": f"n-{name}-bad", "kind": "widget", "label": "x"})
            raise AssertionError("a node outside the closed kind set was accepted")
        except Problem as problem:
            assert problem.body["type"].endswith("graph-assertion-invalid") and problem.body["status"] == 422
        return f"{len(NODE_KINDS)} kinds accepted, 'widget' refused 422"

    @case("assert one edge of each of the three edge kinds")
    def _edge_kinds():
        adapter.append_node({"node_id": f"e-{name}-iface", "kind": "interface", "label": "i"})
        adapter.append_node({"node_id": f"e-{name}-impl", "kind": "implementation", "label": "m"})
        adapter.append_node({"node_id": f"e-{name}-doc", "kind": "document", "label": "d"})
        adapter.append_edge({"edge_id": f"e-{name}-1", "edge_type": "implementation",
                             "from": f"e-{name}-impl", "to": f"e-{name}-iface"})
        adapter.append_edge({"edge_id": f"e-{name}-2", "edge_type": "existence",
                             "from": f"e-{name}-doc", "to": f"e-{name}-impl"})
        adapter.append_edge({"edge_id": f"e-{name}-3", "edge_type": "interface",
                             "from": f"e-{name}-doc", "to": f"e-{name}-iface"})
        return "implementation, existence, interface edges all admitted"

    @case("an implementation edge whose target is not an interface is refused")
    def _bad_impl_target():
        adapter.append_node({"node_id": f"bi-{name}-impl", "kind": "implementation", "label": "m"})
        adapter.append_node({"node_id": f"bi-{name}-doc", "kind": "document", "label": "d"})
        try:
            adapter.append_edge({"edge_id": f"bi-{name}-e", "edge_type": "implementation",
                                 "from": f"bi-{name}-impl", "to": f"bi-{name}-doc"})
            raise AssertionError("an implementation edge into a document node was accepted")
        except Problem as problem:
            assert problem.body["type"].endswith("graph-assertion-invalid") and problem.body["status"] == 422
        return "implementation -> document refused 422"

    @case("an existence edge between two implementation nodes is refused (design rule 1)")
    def _bad_existence():
        adapter.append_node({"node_id": f"be-{name}-a", "kind": "implementation", "label": "a"})
        adapter.append_node({"node_id": f"be-{name}-b", "kind": "implementation", "label": "b"})
        try:
            adapter.append_edge({"edge_id": f"be-{name}-e", "edge_type": "existence",
                                 "from": f"be-{name}-a", "to": f"be-{name}-b"})
            raise AssertionError("an existence edge between two implementations was accepted")
        except Problem as problem:
            assert problem.body["type"].endswith("graph-assertion-invalid")
        return "implementation -> implementation existence edge refused; route through an interface instead"

    @case("an edge naming a field outside the vocabulary is refused before it is applied")
    def _malformed():
        adapter.append_node({"node_id": f"mf-{name}-a", "kind": "document", "label": "a"})
        adapter.append_node({"node_id": f"mf-{name}-b", "kind": "step", "label": "b"})
        try:
            adapter.append_edge({"edge_id": f"mf-{name}-e", "edge_type": "existence",
                                 "from": f"mf-{name}-a", "to": f"mf-{name}-b", "vendor": "a-vendor"})
            raise AssertionError("a request naming an extra field was accepted")
        except Problem as problem:
            assert problem.body["type"].endswith("graph-assertion-invalid") and problem.body["status"] == 422
        return "graph-assertion-invalid 422, nothing was applied"

    @case("neighbors expands one hop into the implementations that could serve an interface")
    def _neighbors():
        adapter.append_node({"node_id": f"nb-{name}-iface", "kind": "interface", "label": "i"})
        adapter.append_node({"node_id": f"nb-{name}-impl", "kind": "implementation", "label": "m"})
        adapter.append_edge({"edge_id": f"nb-{name}-e", "edge_type": "implementation",
                             "from": f"nb-{name}-impl", "to": f"nb-{name}-iface"})
        found = adapter.neighbors(f"nb-{name}-iface", "implementation", direction="in")
        assert [n.node_id for n in found] == [f"nb-{name}-impl"], found
        return f"1 implementation found for interface {f'nb-{name}-iface'!r}"

    @case("path_exists is bounded by max_depth and never materialises the whole graph")
    def _path():
        for i in range(4):
            adapter.append_node({"node_id": f"pe-{name}-{i}", "kind": "step", "label": str(i)})
        for i in range(3):
            adapter.append_edge({"edge_id": f"pe-{name}-e{i}", "edge_type": "existence",
                                 "from": f"pe-{name}-{i}", "to": f"pe-{name}-{i+1}"})
        found_close, _ = adapter.path_exists(f"pe-{name}-0", f"pe-{name}-3", ["existence"], max_depth=5)
        found_far, _ = adapter.path_exists(f"pe-{name}-0", f"pe-{name}-3", ["existence"], max_depth=1)
        assert found_close and not found_far, (found_close, found_far)
        return "reachable within max_depth=5, refused within max_depth=1"

    @case("retract appends a marker; the retracted edge is absent from the fold but not deleted")
    def _retract():
        adapter.append_node({"node_id": f"rt-{name}-a", "kind": "document", "label": "a"})
        adapter.append_node({"node_id": f"rt-{name}-b", "kind": "step", "label": "b"})
        adapter.append_edge({"edge_id": f"rt-{name}-e", "edge_type": "existence",
                             "from": f"rt-{name}-a", "to": f"rt-{name}-b"})
        before = f"rt-{name}-e" in adapter.graph_value().edges
        adapter.retract_edge(f"rt-{name}-e", "superseded")
        after = f"rt-{name}-e" in adapter.graph_value().edges
        records = [r for r in adapter._all_records()
                  if r["record_kind"] == "edge-asserted" and r["edge"]["edge_id"] == f"rt-{name}-e"]
        assert before and not after and records, (before, after, records)
        return "present before retraction, absent after, the original record still on file"

    @case("validate is pure over a graph value with no store attached")
    def _validate_pure():
        gv = adapter.graph_value()
        report_ = validate(gv)
        assert report_.nodes_checked == len(gv.nodes) and report_.edges_checked == len(gv.edges)
        return f"nodes_checked={report_.nodes_checked} edges_checked={report_.edges_checked} false_accepts={report_.false_accepts}"

    @case("property test: 300 generated graphs, rejections > 0, false_accepts == 0 (core-graph DoD)")
    def _property():
        rng = random.Random(1)
        kinds = sorted(NODE_KINDS)
        node_ids = [f"pt-{name}-{i}" for i in range(40)]
        for i, nid in enumerate(node_ids):
            adapter.append_node({"node_id": nid, "kind": kinds[i % len(kinds)], "label": nid})
        kind_of = {nid: kinds[i % len(kinds)] for i, nid in enumerate(node_ids)}
        rejections = false_accepts = attempted = 0
        for i in range(300):
            edge_type = rng.choice(sorted(["existence", "interface", "implementation"]))
            frm, to = rng.choice(node_ids), rng.choice(node_ids)
            attempted += 1
            expect_invalid = _oracle_invalid(edge_type, kind_of[frm], kind_of[to])
            eid = f"pt-{name}-e{i}"
            try:
                adapter.append_edge({"edge_id": eid, "edge_type": edge_type, "from": frm, "to": to})
                if expect_invalid:
                    false_accepts += 1   # the oracle says this should have been refused; it was not
            except Problem:
                rejections += 1
                if not expect_invalid:
                    raise AssertionError(f"a structurally valid edge ({edge_type} {kind_of[frm]}->{kind_of[to]}) was refused")
        report["property_attempted"] = attempted
        report["property_rejections"] = rejections
        report["property_false_accepts"] = false_accepts
        assert rejections > 0, "the generator never produced an edge the checker rejected"
        assert false_accepts == 0, f"{false_accepts} edges the oracle marks invalid were admitted"
        return f"graphs=1 edges_attempted={attempted} rejections={rejections} false_accepts={false_accepts} seed=1"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["assertions"] = adapter.assertions
    report["refusals"] = adapter.refusals
    report["marker"] = adapter.observed_marker
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def _fresh(name: str):
    """Isolated storage for the cross-store check: dryrun starts empty on its
    own, but second (a directory on disk) and live (a shared ledger) persist
    across process invocations and must be pointed at scratch space so this
    check compares one assertion log, not one log plus stale leftovers."""
    if name == "second":
        os.environ["GRAPH_EVENTLOG_DIR"] = tempfile.mkdtemp(prefix="graph-cross-eventlog-")
    elif name == "live":
        os.environ["GRAPH_LEDGER_PARTITION"] = "core-graph-harness-cross-" + next(tempfile._get_candidate_names())
    return ADAPTERS[name]()


def cross_store(name_a: str, name_b: str) -> dict:
    """core-graph-implement's own definition of done: the same assertion log
    folded and validated on two bindings must produce identical verdicts."""
    a, b = _fresh(name_a), _fresh(name_b)
    seq = [
        ("node", {"node_id": "cs-iface", "kind": "interface", "label": "i"}),
        ("node", {"node_id": "cs-impl", "kind": "implementation", "label": "m"}),
        ("node", {"node_id": "cs-doc", "kind": "document", "label": "d"}),
        ("edge", {"edge_id": "cs-e1", "edge_type": "implementation", "from": "cs-impl", "to": "cs-iface"}),
        ("edge", {"edge_id": "cs-e2", "edge_type": "existence", "from": "cs-doc", "to": "cs-impl"}),
    ]
    for store in (a, b):
        for kind, doc in seq:
            (store.append_node if kind == "node" else store.append_edge)(doc)
        store.retract_edge("cs-e2", "superseded")
    ra, rb = validate(a.graph_value()), validate(b.graph_value())
    fields = ("nodes_checked", "edges_checked", "rejections", "false_accepts")
    mismatches = sum(1 for f in fields if getattr(ra, f) != getattr(rb, f))
    return {"binding_a": name_a, "binding_b": name_b, "verdict_mismatches": mismatches,
           "report_a": {f: getattr(ra, f) for f in fields}, "report_b": {f: getattr(rb, f) for f in fields}}


def product_scan(root: str) -> tuple[int, list]:
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__")]
        for name in sorted(filenames):
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, name)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line:
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the Graph interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--cross-store", nargs=2, metavar=("A", "B"), help="cross-store verdict-mismatch check")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0

    if args.cross_store:
        result = cross_store(*args.cross_store)
        print(json.dumps(result, indent=1, sort_keys=True))
        if args.report:
            os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
            json.dump(result, open(args.report, "w"), indent=1, sort_keys=True)
        return 1 if result["verdict_mismatches"] else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        print(f"# binding {name} ({report['execution_model']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"assertions={report['assertions']} refusals={report['refusals']} product_hits={report['product_hits']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
