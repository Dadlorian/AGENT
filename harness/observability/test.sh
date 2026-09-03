#!/usr/bin/env bash
# Gate for the observability harness. Dry-run is measured here; --live is claimed
# until it is run on a host that has the backend.
#
#   bash harness/observability/test.sh          conformance, swap proof, breakage
#   bash harness/observability/test.sh --live   the same against the live adapter
set -u
cd "$(dirname "$0")"
MODE="${1:-}"
PASS=0; FAIL=0
ok()    { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()   { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check() { if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field() { python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$1" "$2"; }

rm -rf out && mkdir -p out

if [ "$MODE" = "--live" ]; then
  if [ -z "${TRACE_URL:-}" ] || [ -z "${TRACE_KEY:-}" ]; then
    echo "SKIPPED: live mode needs TRACE_URL and TRACE_KEY (and TRACE_QUERY_URL to read back)."
    echo "         See README's env-var table. Nothing here has been run against a host."
    exit 0
  fi
  echo "L1. conformance against the live adapter"
  ADAPTER=live python3 conformance.py --adapter live --report out/tel-live.json > out/live.log 2>&1
  check "live conformance exits 0" "$?" "0"
  echo "L2. swap proof, live then second"
  python3 conformance.py --adapter second --report out/tel-live-b.json > out/live-b.log 2>&1
  check "second conformance exits 0" "$?" "0"
  python3 conformance.py --merge out/tel-live.json out/tel-live-b.json --report out/merged-live.json > out/live-merge.log 2>&1
  check "merged swap proof exits 0" "$?" "0"
  echo "L3. deliberate breakage against live"
  ADAPTER=live python3 conformance.py --adapter live --break-stamp --report out/brk-live.json > out/brk-live.log 2>&1
  check "breakage exits 1" "$?" "1"
  echo; echo "passed $PASS, failed $FAIL"; [ "$FAIL" -eq 0 ] || exit 1; exit 0
fi

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/tel-a.json > out/a.log 2>&1
check "dryrun conformance exits 0" "$?" "0"
check "levels covered"                "$(field out/tel-a.json levels_covered)" "3"
check "groups on run.id"              "$(field out/tel-a.json run_id_groups)" "1"
check "spans missing run.id"          "$(field out/tel-a.json spans_missing_run_id)" "0"
check "spans missing root dispatch id" "$(field out/tel-a.json spans_missing_root_dispatch_id)" "0"
check "distinct trace ids, reported never constrained" "$(field out/tel-a.json distinct_trace_ids)" "3"
[ -n "$(field out/tel-a.json mapping_version)" ] && ok "mapping version read back off the wire" \
  || bad "no mapping version on the wire"

echo "2. swap proof: conformance before, swap by configuration, conformance after"
cp out/tel-a.json out/before.json
ADAPTER=second python3 conformance.py --report out/tel-b.json > out/b.log 2>&1
check "second conformance exits 0 (ADAPTER=second, no code edit)" "$?" "0"
python3 conformance.py --merge out/before.json out/tel-b.json --report out/merged.json > out/merge.log 2>&1
check "merged swap proof exits 0" "$?" "0"
check "adapters run" "$(field out/merged.json adapters_run)" "2"
check "selected by" "$(field out/merged.json selected_by)" "configuration"
python3 - <<'PY' && ok "both adapters returned identical correlation counters" || bad "the interface did not hold across the swap"
import json
a, b = json.load(open("out/before.json")), json.load(open("out/tel-b.json"))
keys = ("levels_covered", "run_id_groups", "spans_missing_run_id",
        "spans_missing_root_dispatch_id", "mapping_version", "signals_checked")
raise SystemExit(0 if all(a[k] == b[k] for k in keys) else 1)
PY
python3 - <<'PY' && ok "the two adapters are not the same thing twice (different query surface declared)" || bad "the pair does not differ"
import json
a, b = json.load(open("out/before.json")), json.load(open("out/tel-b.json"))
raise SystemExit(0 if a["semantic_queries_supported"] != b["semantic_queries_supported"] else 1)
PY

echo "3. the minimal call, both adapters"
for A in dryrun second; do
  ADAPTER=$A python3 call.py > "out/call-$A.log" 2>&1
  check "$A call exits 0" "$?" "0"
  grep -q "PROOF: one tree, not 3" "out/call-$A.log" \
    && ok "$A: one tree, not 3, grouped on run.id" || bad "$A: did not prove one tree"
done
diff <(grep PROOF out/call-dryrun.log) <(grep PROOF out/call-second.log) > /dev/null \
  && ok "the caller sees the same answer whichever adapter answered" || bad "the caller can tell them apart"

echo "4. deliberate breakage: stop re-stamping at the child-dispatch boundary"
for A in dryrun second; do
  ADAPTER=$A python3 conformance.py --break-stamp --report "out/brk-$A.json" > "out/brk-$A.log" 2>&1
  check "$A breakage exits 1" "$?" "1"
  check "$A levels covered"       "$(field out/brk-$A.json levels_covered)" "1"
  check "$A groups on run.id"     "$(field out/brk-$A.json run_id_groups)" "0"
  check "$A spans missing run.id" "$(field out/brk-$A.json spans_missing_run_id)" "2"
done
diff <(field out/brk-dryrun.json levels_covered) <(field out/brk-second.json levels_covered) > /dev/null \
  && ok "both adapters fail identically, which locates the fault in the dispatch path" \
  || bad "the adapters failed differently"
python3 call.py --break-stamp > out/brk-call.log 2>&1
check "the minimal call fails under the breakage" "$?" "1"

echo "5. the failure path answers with problem details, never an exception"
ADAPTER=live python3 conformance.py --adapter live > out/live-missing.log 2>&1
check "unconfigured live adapter exits 2" "$?" "2"
grep -q "application/problem+json" out/live-missing.log && ok "answer is problem details" || bad "not problem details"
grep -q "urn:agentic:problem:adapter-unavailable" out/live-missing.log && ok "typed from the closed registry" || bad "untyped"
grep -q "Traceback" out/live-missing.log && bad "a traceback reached the caller" || ok "no traceback reached the caller"

echo "6. the boundary holds in the source, not only at runtime"
if grep -riEl "langfuse|clickhouse|phoenix|braintrust|otel-collector|litellm|goose" interface.py call.py conformance.py > /dev/null 2>&1; then
  bad "a product name leaked outside adapters/"
else
  ok "no product name in interface.py, call.py or conformance.py"
fi
CALLER=$(awk '/BEGIN caller code/,/END caller code/' call.py | grep -cve '^\s*$' -e '^\s*#')
[ "$CALLER" -lt 40 ] && ok "caller code is $CALLER lines (under 40)" || bad "caller code is $CALLER lines"
grep -q "parent" interface.py && ok "parentage is named in the interface only to forbid it" || bad "unexpected"
python3 -c "
import sys; sys.path.insert(0,'.')
from interface import TelemetryUnit
from dataclasses import fields
raise SystemExit(0 if not any('parent' in f.name for f in fields(TelemetryUnit)) else 1)" \
  && ok "the unit shape has nowhere to put a parent span" || bad "the unit shape carries parentage"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
