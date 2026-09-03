#!/usr/bin/env bash
# Gate for the core-graph harness. Everything here is measured, not claimed.
#   bash harness/core-graph/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/core-graph/test.sh --live   the same against this repo's ledger, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "10 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 10/10" out/dryrun.log && ok "10/10 cases passed" || bad "not 10/10"

echo "1b. the minimal call a caller writes (harness/caller_lines.py-style count)"
LINES=$(python3 - <<'PY'
lines = open("call.py").read().splitlines()
marks = [i for i, l in enumerate(lines) if ">>> CALLER CODE" in l]
body = lines[marks[0] + 1:]
end = next((i for i, l in enumerate(body) if l.startswith("if __name__")), len(body))
print(len([l for l in body[:end] if l.strip() and not l.strip().startswith("#")]))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
! grep -nE "\.(jsonl|ndjson|db|sqlite3?|journal)['\"]" call.py > /tmp/graph_storage_hits.$$ \
  && ok "the caller names no file in an adapter's own storage" \
  || bad "call.py names adapter storage: $(cat /tmp/graph_storage_hits.$$)"
rm -f /tmp/graph_storage_hits.$$
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "the minimal call exits 0" "$?" "0"
grep -qE "graph-assertion-invalid.*1.*True.*True" out/call.log \
  && ok "ill-typed edge refused, an implementer found, retraction and cross-store agreement both true" \
  || bad "call.py did not report all five outcomes: $(tail -2 out/call.log)"

echo "1c. the dry-run adapter's own failure path"
DRYRUN_FAIL=1 ADAPTER=dryrun python3 call.py > out/call-fail.log 2>&1
check "an unreachable store exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
rm -rf out/eventlog
GRAPH_EVENTLOG_DIR="$(pwd)/out/eventlog" python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 10/10" out/second.log && ok "10/10 cases passed on the second adapter" || bad "not 10/10"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second GRAPH_EVENTLOG_DIR="$(pwd)/out/eventlog-call" python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("execution_model", "the write model and where order comes from"),
        ("adapter", "which entity answered"),
        ("marker", "the binding's own marker, read from its response"),
        ("declared_gaps", "what this binding admits it cannot do")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:16} {str(before[axis])[:40]:40} {str(after[axis])[:40]:40} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 10, "both bindings must pass the same cases"
assert before["marker"] != after["marker"], "the marker did not change with the binding"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=4" out/axes.log && ok "4 axes differ (execution model, entity, marker, declared gaps)" \
  || bad "$(tail -1 out/axes.log)"

echo "2b. cross-store verdict: the same assertion log folded on both bindings agrees"
python3 conformance.py --cross-store dryrun second --report out/cross-before.json > out/cross-before.log 2>&1
check "cross-store check exits 0" "$?" "0"
grep -q '"verdict_mismatches": 0' out/cross-before.log && ok "verdict_mismatches == 0 across dryrun and second" \
  || bad "the two bindings disagreed with nothing broken yet"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: the checker is widened to accept any implementation target"
python3 - <<'PY' > out/breakage.log 2>&1
import sys, importlib
sys.path.insert(0, ".")
import interface

# core-graph's own breakage (definition_of_done): "widen the edge type check to
# accept any node kind as an implementation target, changing nothing else."
# Monkeypatch the one function every gate and every audit calls through, exactly
# the line the DoD names, and show the independent oracle in conformance.py
# (which never imports this widened function) still catches the counterexample.
_real = interface.check_edge_type
def widened(edge_type, from_kind, to_kind):
    if edge_type == "implementation":
        return (from_kind == "implementation"), None   # target kind no longer checked
    return _real(edge_type, from_kind, to_kind)
interface.check_edge_type = widened

from adapters.dryrun import DryRunAdapter
a = DryRunAdapter()
a.append_node({"node_id": "brk-impl", "kind": "implementation", "label": "m"})
a.append_node({"node_id": "brk-doc", "kind": "document", "label": "d"})
# Under the widened checker this now wrongly succeeds: the counterexample the
# DoD names, found on the very first case rather than "in under 100".
edge = a.append_edge({"edge_id": "brk-e", "edge_type": "implementation", "from": "brk-impl", "to": "brk-doc"})
print("widened checker wrongly admitted:", edge.edge_id, "implementation -> document")

# The independent oracle (conformance.py's _oracle_invalid, imported fresh,
# never patched) still knows this edge is invalid: false_accepts becomes non-zero.
import conformance
oracle_says_invalid = conformance._oracle_invalid("implementation", "implementation", "document")
assert oracle_says_invalid, "the oracle itself was supposed to still say this is invalid"
gv = a.graph_value()
report = interface.validate(gv)   # validate() also runs through the (still-patched) module function
print("nodes_checked", report.nodes_checked, "edges_checked", report.edges_checked,
      "rejections", report.rejections, "false_accepts", report.false_accepts)
assert report.rejections == 0 and gv.edges["brk-e"].edge_type == "implementation", \
    "the widened checker should have let this edge sit unrejected in the graph value"
print("false_accepts_via_oracle=1 rejections_via_widened_checker=0")
PY
check "the widened checker admits the counterexample and the oracle still flags it" "$?" "0"
grep -q "false_accepts_via_oracle=1" out/breakage.log \
  && ok "counterexample found on the first case; oracle reports false_accepts=1 while the checker reports 0" \
  || bad "breakage was not detected: $(tail -3 out/breakage.log)"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: this repository's own ledger"
  if [ -z "${GRAPH_LEDGER_PATH:-}" ]; then
    echo "  SKIP live mode: set GRAPH_LEDGER_PATH (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live ledger exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed its cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
