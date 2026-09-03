#!/usr/bin/env bash
# Gate for the evaluation harness. Dry-run is measured here; --live is claimed
# until it is run on a host that has the trace backend.
#
#   bash harness/evaluation/test.sh          conformance, swap proof, breakage
#   bash harness/evaluation/test.sh --live   the same against the live adapter
set -u
cd "$(dirname "$0")"
MODE="${1:-}"
PASS=0; FAIL=0
ok()    { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()   { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check() { if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field() { python3 -c "import json,sys;v=json.load(open(sys.argv[1]))[sys.argv[2]];print(','.join(map(str,v)) if isinstance(v,list) else v)" "$1" "$2"; }

rm -rf out && mkdir -p out

if [ "$MODE" = "--live" ]; then
  if [ -z "${EVAL_TRACE_URL:-}" ] || [ -z "${EVAL_TRACE_QUERY_URL:-}" ] || [ -z "${EVAL_TRACE_KEY:-}" ]; then
    echo "SKIPPED: live mode needs EVAL_TRACE_URL, EVAL_TRACE_QUERY_URL and EVAL_TRACE_KEY."
    echo "         See README's env-var table. Nothing here has been run against a host."
    exit 0
  fi
  echo "L1. conformance against the live adapter"
  ADAPTER=live python3 conformance.py --adapter live --report out/eval-live.json > out/live.log 2>&1
  check "live conformance exits 0" "$?" "0"
  echo "L2. swap proof, live then second"
  python3 conformance.py --adapter second --report out/eval-live-b.json > out/live-b.log 2>&1
  check "second conformance exits 0" "$?" "0"
  python3 conformance.py --merge out/eval-live.json out/eval-live-b.json --report out/merged-live.json > out/live-merge.log 2>&1
  check "merged swap proof exits 0" "$?" "0"
  echo "L3. deliberate breakage against live"
  ADAPTER=live python3 conformance.py --adapter live --break-gate --report out/brk-live.json > out/brk-live.log 2>&1
  check "breakage exits 1" "$?" "1"
  echo; echo "passed $PASS, failed $FAIL"; [ "$FAIL" -eq 0 ] || exit 1; exit 0
fi

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "dryrun conformance exits 0" "$?" "0"
grep -q "conformance PASSED: 22/22" out/dryrun.log && ok "22/22 cases passed" || bad "not 22/22"
check "cases executed"                  "$(field out/before.json cases_executed)" "6"
check "outcome at the baseline version"  "$(field out/before.json outcome)" "passed"
check "transitions at the baseline"      "$(field out/before.json transitions)" "0"
check "outcome at the candidate version" "$(field out/before.json regressed_outcome)" "failed"
check "transitions at the candidate"     "$(field out/before.json regressed_transitions)" "1"
check "the case the verdict names"       "$(field out/before.json transitions_named)" "cs-r2"
check "effects served from the record"   "$(field out/before.json served_effects)" "2"
check "effects executed"                 "$(field out/before.json executed_effects)" "0"
check "unrecorded effects refused"       "$(field out/before.json unrecorded_effects)" "1"
check "gate status over a zero-case run" "$(field out/before.json gate_status_zero_case)" "inconclusive"
check "rubric markers seen by the unit"  "$(field out/before.json rubric_markers_seen_by_unit)" "0"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 -c "import sys; sys.path.insert(0, '..'); import caller_lines; print(caller_lines.count('evaluation'))")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 -c "
import sys; sys.path.insert(0, '..'); import caller_lines
hits = caller_lines.storage_hits('evaluation')
[print(f'call.py:{n}: {line}') for n, line in hits]
raise SystemExit(1 if hits else 0)" \
  && ok "the caller names no file in the adapter's own storage" \
  || bad "call.py reads the adapter's storage by path"

echo "2. the minimal call, both adapters"
for A in dryrun second; do
  ADAPTER=$A python3 call.py > "out/call-$A.log" 2>&1
  check "$A call exits 0" "$?" "0"
  grep -q "PROOF: the verdict names cs-r2" "out/call-$A.log" \
    && ok "$A: the verdict names the case that failed" || bad "$A: no case named"
  grep -q "PROOF: a gate cannot report success with every case skipped" "out/call-$A.log" \
    && ok "$A: an empty run cannot read as a pass" || bad "$A: an empty run read as green"
done
diff <(grep -E "^(PROOF|run |cs-|baseline |candidate |skipped )" out/call-dryrun.log) \
     <(grep -E "^(PROOF|run |cs-|baseline |candidate |skipped )" out/call-second.log) > /dev/null \
  && ok "the caller sees the same answer whichever adapter answered" || bad "the caller can tell them apart"

echo "3. swap proof: conformance before, swap by configuration, conformance after"
cp out/before.json out/before-kept.json
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
ADAPTER=second python3 conformance.py --report out/after.json > out/second.log 2>&1
check "second conformance exits 0 (ADAPTER=second, no code edit)" "$?" "0"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
python3 conformance.py --merge out/before-kept.json out/after.json --report out/merged.json > out/merge.log 2>&1
check "merged swap proof exits 0" "$?" "0"
check "adapters run"        "$(field out/merged.json adapters_run)" "2"
check "verdict divergence"  "$(field out/merged.json verdict_divergence)" "0"
check "selected by"         "$(field out/merged.json selected_by)" "configuration"
[ -n "$(field out/merged.json axes_differ)" ] \
  && ok "the pair differs on declared axes ($(field out/merged.json axes_differ))" \
  || bad "the pair is one adapter run twice"
check "the second adapter needs no server"     "$(field out/after.json execution_model)" "no-server"
check "the second adapter reads no live trace" "$(field out/after.json trajectory_source)" "fixture-file"
check "and carries no verdict export"          "$(field out/after.json emit_evaluation_result)" "False"

echo "4. deliberate breakage: the gate reads its status from the exit code"
for A in dryrun second; do
  ADAPTER=$A python3 conformance.py --break-gate --report "out/brk-$A.json" > "out/brk-$A.log" 2>&1
  check "$A breakage exits 1" "$?" "1"
  check "$A gate over a zero-case report" "$(field out/brk-$A.json gate_status_zero_case)" "passed"
  check "$A gate blocked promotion"       "$(field out/brk-$A.json gate_blocks_zero_case)" "False"
  grep -q "FAIL C6 a gate over a zero-case report cannot report success" "out/brk-$A.log" \
    && ok "$A: the failing check names the gate stage" || bad "$A: the breakage was not caught at the gate"
  check "$A corpus outcome is unmoved"    "$(field out/brk-$A.json outcome)" "passed"
  check "$A candidate outcome is unmoved" "$(field out/brk-$A.json regressed_outcome)" "failed"
  check "$A the named case is unmoved"    "$(field out/brk-$A.json transitions_named)" "cs-r2"
done
diff <(grep -c FAIL out/brk-dryrun.log) <(grep -c FAIL out/brk-second.log) > /dev/null \
  && ok "both adapters fail identically, which locates the fault in the gate and not in a harness" \
  || bad "the adapters failed differently"

echo "5. the failure path answers with problem details, never an exception"
ADAPTER=live python3 conformance.py --adapter live > out/live-missing.log 2>&1
check "unconfigured live adapter exits 2" "$?" "2"
grep -q "application/problem+json" out/live-missing.log && ok "answer is problem details" || bad "not problem details"
grep -q "urn:agentic:problem:adapter-unavailable" out/live-missing.log && ok "typed from the closed registry" || bad "untyped"
grep -q "Traceback" out/live-missing.log && bad "a traceback reached the caller" || ok "no traceback reached the caller"

echo "6. the boundary holds in the source, not only at runtime"
if grep -riEl "langfuse|clickhouse|phoenix|braintrust|langsmith|deepeval|litellm|temporal|goose|firecracker" interface.py call.py conformance.py unit_under_test.py > /dev/null 2>&1; then
  bad "a product name leaked outside adapters/"
else
  ok "no product name in interface.py, call.py, conformance.py or the unit under test"
fi
python3 - <<'PY' && ok "the interface carries five operations, none of which executes an effect" || bad "the interface grew a way to execute an effect"
import sys; sys.path.insert(0, ".")
import interface
raise SystemExit(0 if (interface.interface_operations() == (
    "evaluate", "promote_baseline", "register_case_set", "replay_case", "score_trajectory")
    and interface.no_execute_operation()) else 1)
PY
python3 - <<'PY' && ok "a case has a rubric handle and nowhere to put a rubric body" || bad "a rubric body can travel in a case"
import sys; sys.path.insert(0, ".")
import interface
raise SystemExit(0 if interface.case_carries_no_rubric_body() else 1)
PY
grep -q "cases_executed" interface.py && ok "outcome and cases_executed are stated together in the report shape" || bad "unexpected"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
