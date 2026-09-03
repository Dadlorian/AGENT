#!/usr/bin/env bash
# Gate for the improvement-loop harness. Dry-run is measured here; --live drives the
# same conformance run against this repository's own ceremony records, read-only,
# and is skipped with a message when its env vars are unset.
#
#   bash harness/compose-improvement-loop/test.sh          conformance, swap proof, breakage
#   bash harness/compose-improvement-loop/test.sh --live    the same against the live driver
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
  if [ -z "${IMPROVE_LOOP_CEREMONY_DIR:-}" ] || [ -z "${IMPROVE_LOOP_SHADOW_DIR:-}" ]; then
    echo "SKIPPED: live mode needs IMPROVE_LOOP_CEREMONY_DIR and IMPROVE_LOOP_SHADOW_DIR."
    echo "         See README's env-var table. IMPROVE_LOOP_FIRE_CMD is what actually fires"
    echo "         the section loop; unset, the live driver only reads the records on disk."
    exit 0
  fi
  echo "L1. conformance against the live driver"
  ADAPTER=live python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
  check "live conformance exits 0" "$?" "0"
  check "the live driver's checkpoint store" "$(field out/live.json checkpoint_store)" "ceremony-records"
  echo "L2. the live driver wrote its own shadow and nothing else"
  [ -d "$IMPROVE_LOOP_SHADOW_DIR/checkpoints" ] && ok "checkpoints under the shadow directory" \
    || bad "no shadow checkpoints"
  if [ -n "${IMPROVE_LOOP_FIRE_CMD:-}" ]; then
    ok "IMPROVE_LOOP_FIRE_CMD is set, so an iteration fired the component"
  else
    echo "  note IMPROVE_LOOP_FIRE_CMD is unset: the component was read, never fired"
  fi
  echo "L3. swap proof and breakage against live"
  python3 conformance.py --adapter second --report out/live-b.json > out/live-b.log 2>&1
  check "second conformance exits 0" "$?" "0"
  python3 conformance.py --merge out/live.json out/live-b.json --report out/merged-live.json > out/live-merge.log 2>&1
  check "merged swap proof exits 0" "$?" "0"
  ADAPTER=live python3 conformance.py --adapter live --break-gate --report out/brk-live.json > out/brk-live.log 2>&1
  check "breakage exits 1" "$?" "1"
  echo; echo "passed $PASS, failed $FAIL"; [ "$FAIL" -eq 0 ] || exit 1; exit 0
fi

echo "1. conformance against the dry-run driver"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "dryrun conformance exits 0" "$?" "0"
grep -q "conformance PASSED: 25/25" out/dryrun.log && ok "25/25 cases passed" || bad "not 25/25"
check "iterations run"                    "$(field out/before.json iterations_run)" "6"
check "how the loop ended"                "$(field out/before.json terminated_by)" "verdict_pass"
check "the class that ending belongs to"  "$(field out/before.json termination_class)" "stop"
check "the metric each iteration worked"  "$(field out/before.json metric_order)" \
      "measured_done_share,measured_done_share,stale_status_rows,stale_status_rows,proposed_share,measured_done_share"
check "what the gate said each time"      "$(field out/before.json gate_outcomes)" \
      "failed,passed,inconclusive,passed,passed,passed"
check "candidates promoted"               "$(field out/before.json promoted)" "4"
check "candidates declined"               "$(field out/before.json declined)" "2"
check "a failed gate held the checkpoint" "$(field out/before.json checkpoint_held_on_failed_gate)" "True"
check "an unbounded loop is refused with" "$(field out/before.json unbounded_refused_with)" \
      "urn:agentic:problem:document-invalid"
check "the ceiling run ended by"          "$(field out/before.json cap_terminated_by)" "iteration_ceiling"
check "and escalated with"                "$(field out/before.json cap_escalation_type)" \
      "urn:agentic:problem:deadline-exceeded"
check "the budget run ended by"           "$(field out/before.json budget_terminated_by)" "budget_ceiling"
check "cost of the loop, in micros"       "$(field out/before.json cost_micros)" "1500000"
check "a re-delivered iteration is the same record" "$(field out/before.json replayed_record_is_same)" "True"
check "the gate that decided every candidate" "$(field out/before.json gate)" "dryrun"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 -c "import sys; sys.path.insert(0, '..'); import caller_lines; print(caller_lines.count('compose-improvement-loop'))")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 -c "
import sys; sys.path.insert(0, '..'); import caller_lines
hits = caller_lines.storage_hits('compose-improvement-loop')
[print(f'call.py:{n}: {line}') for n, line in hits]
raise SystemExit(1 if hits else 0)" \
  && ok "the caller names no file in the driver's own storage" \
  || bad "call.py reads the driver's storage by path"

echo "2. the minimal call, both drivers"
for A in dryrun second; do
  rm -rf out/fires
  ADAPTER=$A python3 call.py > "out/call-$A.log" 2>&1
  check "$A call exits 0" "$?" "0"
  grep -q "PROOF: every iteration worked the metric furthest from its target" "out/call-$A.log" \
    && ok "$A: the furthest metric is the one worked" || bad "$A: another metric was worked"
  grep -q "PROOF: a gate that said failed left checkpoint" "out/call-$A.log" \
    && ok "$A: a failed gate left the previous checkpoint in place" || bad "$A: a declined iteration moved the checkpoint"
  grep -q "PROOF: a loop with no iteration ceiling is refused" "out/call-$A.log" \
    && ok "$A: an unbounded loop is refused before anything runs" || bad "$A: an unbounded loop was accepted"
done
diff <(grep -vE "^adapter=" out/call-dryrun.log) <(grep -vE "^adapter=" out/call-second.log) > /dev/null \
  && ok "the caller sees the same answer whichever driver answered" || bad "the caller can tell them apart"

echo "3. swap proof: conformance before, swap by configuration, conformance after"
cp out/before.json out/before-kept.json
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
rm -rf out/fires
ADAPTER=second python3 conformance.py --report out/after.json > out/second.log 2>&1
check "second conformance exits 0 (ADAPTER=second, no code edit)" "$?" "0"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
python3 conformance.py --merge out/before-kept.json out/after.json --report out/merged.json > out/merge.log 2>&1
check "merged swap proof exits 0" "$?" "0"
check "adapters run"          "$(field out/merged.json adapters_run)" "2"
check "record divergence"     "$(field out/merged.json record_divergence)" "0"
check "selected by"           "$(field out/merged.json selected_by)" "configuration"
check "the iteration records both drivers wrote" "$(field out/after.json records_digest)" \
      "$(field out/before-kept.json records_digest)"
[ -n "$(field out/merged.json axes_differ)" ] \
  && ok "the pair differs on declared axes ($(field out/merged.json axes_differ))" \
  || bad "the pair is one driver run twice"
check "the second driver fires one iteration at a time" "$(field out/after.json execution_model)" "one-iteration-per-fire"
check "and keeps its checkpoints outside the process"   "$(field out/after.json checkpoint_store)" "file"
check "so a lost process does not lose the loop"        "$(field out/after.json survives_process_loss)" "True"
check "which the first driver does not claim"           "$(field out/before-kept.json survives_process_loss)" "False"

echo "4. deliberate breakage: the checkpoint advances whatever the gate said"
for A in dryrun second; do
  rm -rf out/fires
  ADAPTER=$A python3 conformance.py --break-gate --report "out/brk-$A.json" > "out/brk-$A.log" 2>&1
  check "$A breakage exits 1" "$?" "1"
  check "$A a failed gate no longer holds the checkpoint" "$(field out/brk-$A.json checkpoint_held_on_failed_gate)" "False"
  grep -q "FAIL C5 a failed gate declines the candidate" "out/brk-$A.log" \
    && ok "$A: the failing check names the checkpoint rule" || bad "$A: the breakage was not caught at the checkpoint"
  grep -q "FAIL C6 an inconclusive gate is treated exactly like a failed one" "out/brk-$A.log" \
    && ok "$A: an inconclusive gate was silently promoted, and the check says so" || bad "$A: not caught"
  check "$A the unbounded refusal is unmoved" "$(field out/brk-$A.json unbounded_refused_with)" \
        "urn:agentic:problem:document-invalid"
  check "$A the ceiling still caps the loop"  "$(field out/brk-$A.json cap_terminated_by)" "iteration_ceiling"
done
diff <(grep -c FAIL out/brk-dryrun.log) <(grep -c FAIL out/brk-second.log) > /dev/null \
  && ok "both drivers fail identically, which locates the fault in the checkpoint rule and not in a driver" \
  || bad "the drivers failed differently"

echo "5. the failure path answers with problem details, never an exception"
env -u IMPROVE_LOOP_CEREMONY_DIR -u IMPROVE_LOOP_SHADOW_DIR ADAPTER=live \
  python3 conformance.py --adapter live > out/live-missing.log 2>&1
check "unconfigured live driver exits 2" "$?" "2"
grep -q "application/problem+json" out/live-missing.log && ok "answer is problem details" || bad "not problem details"
grep -q "urn:agentic:problem:adapter-unavailable" out/live-missing.log && ok "typed from the closed registry" || bad "untyped"
grep -q "Traceback" out/live-missing.log && bad "a traceback reached the caller" || ok "no traceback reached the caller"

echo "6. the boundary holds in the source, not only at runtime"
if grep -riEl "loop-workflow|kb/ceremonies|state/lessons|state/loop\.json|langfuse|temporal|firecracker|goose|litellm|subprocess" \
     interface.py call.py conformance.py > /dev/null 2>&1; then
  bad "a component or product name leaked outside adapters/"
else
  ok "no component or product name in interface.py, call.py or conformance.py"
fi
python3 - <<'PY' && ok "the interface carries five operations, none of which edits a target" || bad "the interface grew a way to edit a target"
import sys; sys.path.insert(0, ".")
import interface
raise SystemExit(0 if (interface.interface_operations() == (
    "evaluate_exit", "open_loop", "read_checkpoint", "register_scorecard", "run_iteration")
    and interface.no_in_place_edit_operation()) else 1)
PY
python3 - <<'PY' && ok "a candidate has a gate handle and nowhere to put a criterion" || bad "a criterion can travel in a candidate"
import sys; sys.path.insert(0, ".")
import interface
raise SystemExit(0 if interface.candidate_carries_no_criterion() else 1)
PY
python3 - <<'PY' && ok "the gate is the evaluation harness's own interface, imported not re-declared" || bad "this harness declared a second gate"
import sys, os; sys.path.insert(0, ".")
import interface
ev = interface.gate_interface()
same = (interface.EvaluationReport is ev.EvaluationReport and interface.Problem is ev.Problem
        and interface.PASSED == ev.PASSED and interface.INCONCLUSIVE == ev.INCONCLUSIVE
        and os.path.basename(os.path.dirname(ev.__file__)) == "evaluation")
raise SystemExit(0 if same else 1)
PY
grep -q '"iteration_ceiling"' interface.py && ok "the declaration schema requires an iteration ceiling" || bad "unexpected"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
