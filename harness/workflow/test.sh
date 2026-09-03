#!/usr/bin/env bash
# Gate for the workflow harness. Dry-run mode is measured here; --live is claimed
# until it is run on the host.
#
#   bash harness/workflow/test.sh          conformance, the swap proof, the breakage
#   bash harness/workflow/test.sh --live   the same against the engine named by WORKFLOW_ADDR
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field(){ python3 -c "import json,sys;d=json.load(open('$1'));print(json.dumps(d$2))"; }

rm -rf out && mkdir -p out

if [ "${1:-}" = "--live" ]; then
  echo "LIVE mode: the durable executor named by WORKFLOW_ADDR"
  if [ -z "${WORKFLOW_ADDR:-}" ]; then
    echo "  SKIPPED: WORKFLOW_ADDR is unset, so live mode has no endpoint."
    echo "  Set WORKFLOW_ADDR (and WORKFLOW_NAMESPACE, WORKFLOW_TASK_QUEUE, WORKFLOW_API_KEY"
    echo "  where the frontend needs them) and run this again on the host. See README."
    echo "skipped: live mode needs WORKFLOW_ADDR"
    exit 0
  fi
  python3 conformance.py --adapter live --out out/live --report out/live.json > out/live.log 2>&1
  RC=$?
  if grep -q "adapter-unavailable" out/live.log out/live/live/*/result-*.json 2>/dev/null; then
    ok "the live adapter reported a typed adapter-unavailable rather than failing open"
  else
    check "live conformance exits 0" "$RC" "0"
  fi
  echo; echo "passed $PASS, failed $FAIL"
  [ "$FAIL" -eq 0 ] || exit 1
  echo "live: $PASS checks pass against $WORKFLOW_ADDR"
  exit 0
fi

echo "1. the minimal call: one durable flow, crashed and resumed"
ADAPTER=dryrun python3 call.py > out/call-dryrun.log 2>&1
check "call.py exits 0" "$?" "0"
grep -q "rc -9" out/call-dryrun.log && ok "attempt 1 really died (SIGKILL, not a return)" \
  || bad "attempt 1 did not die"
grep -q "1 row(s) in effects.jsonl" out/call-dryrun.log \
  && ok "the side effect happened exactly once across the crash" || bad "effect repeated or lost"

echo "2. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --out out/c1 --report out/before.json > out/c1.log 2>&1
check "dry-run conformance exits 0" "$?" "0"
sed -n 's/^adapter=/  /p' out/c1.log
check "every check passed" "$(field out/before.json "['per_adapter'][0]['failures']")" "[]"

echo "3. swap proof: the same cases, before and after the swap"
python3 conformance.py --adapter dryrun --out out/before --report out/swap-before.json > out/before.log 2>&1
check "before: dry-run adapter" "$?" "0"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the minimal call is unchanged under the second adapter" "$?" "0"
python3 conformance.py --adapter second --out out/after --report out/swap-after.json > out/after.log 2>&1
check "after: queue-plus-state-machine adapter" "$?" "0"
B=$(field out/swap-before.json "['per_adapter'][0]['executor_marker']")
A=$(field out/swap-after.json "['per_adapter'][0]['executor_marker']")
echo "  before marker $B, after marker $A"
[ "$B" != "$A" ] && ok "a different executor really answered" || bad "the same executor answered twice"
BC=$(field out/swap-before.json "['per_adapter'][0]['checks_total']")
AC=$(field out/swap-after.json "['per_adapter'][0]['checks_total']")
check "the same cases ran on both sides of the swap" "$BC" "$AC"
python3 conformance.py --adapter dryrun --adapter second --out out/both --report out/both.json > out/both.log 2>&1
check "both executors in one report" "$?" "0"
check "adapters_run" "$(field out/both.json "['adapters_run']")" "2"
check "distinct executor markers" "$(field out/both.json "['distinct_markers']" | tr -d ' ' | python3 -c "import sys,json;print(len(json.load(sys.stdin)))")" "2"
diff <(field out/both.json "['per_adapter'][0]['effects_for_killed_step']") \
     <(field out/both.json "['per_adapter'][1]['effects_for_killed_step']") > /dev/null \
  && ok "both executors produced exactly one effect for the killed step" \
  || bad "the executors disagree on the effect count"

echo "4. deliberate breakage: the step record carries no idempotency key"
python3 conformance.py --adapter dryrun --adapter second --break-idempotency \
  --out out/broken --report out/broken.json > out/broken.log 2>&1
BRC=$?
check "the breakage run exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "the keyed-effect executor repeats the side effect" \
  "$(field out/broken.json "['per_adapter'][0]['duplicate_effects']")" "1"
check "both executors report failures, so the defect is in the step record" \
  "$(python3 -c "import json;d=json.load(open('out/broken.json'));print(all(p['failures'] for p in d['per_adapter']))")" "True"
check "the kill still landed, so this is duplication and not a missing crash" \
  "$(python3 -c "import json;d=json.load(open('out/broken.json'));print(all(p['resume_point_at_start']>0 for p in d['per_adapter']))")" "True"
python3 conformance.py --adapter dryrun --out out/repair --report out/repair.json > out/repair.log 2>&1
check "the same suite passes again once the key is restored" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "dry-run: $PASS checks pass, swap proven across 2 executors, breakage fails both"
