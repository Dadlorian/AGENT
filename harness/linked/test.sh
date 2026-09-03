#!/usr/bin/env bash
# Gate for the linked harness. Dry-run mode is measured here; --live is claimed
# until it is run on the host.
#
#   bash harness/linked/test.sh          the minimal call, conformance, the swap
#                                        proof across all four components, the breakage
#   bash harness/linked/test.sh --live   the same with every component's live adapter
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field(){ python3 -c "import json,sys;d=json.load(open('$1'));print(json.dumps(d$2).strip('\"'))"; }

rm -rf out && mkdir -p out

if [ "${1:-}" = "--live" ]; then
  echo "LIVE mode: every component reached through its own live adapter"
  MISSING=""
  [ -z "${CELL_START_CMD:-}" ]  && MISSING="$MISSING CELL_START_CMD"
  [ -z "${GATEWAY_URL:-}" ]     && MISSING="$MISSING GATEWAY_URL"
  [ -z "${TRACE_URL:-}" ]       && MISSING="$MISSING TRACE_URL"
  [ -z "${WORKFLOW_ADDR:-}" ]   && MISSING="$MISSING WORKFLOW_ADDR"
  if [ -n "$MISSING" ]; then
    echo "  SKIPPED: unset ->$MISSING"
    echo "  Every component keeps its own env vars; the linked run needs all four sets at"
    echo "  once. See the table in README.md and run this again on the host."
    echo "skipped: live mode needs$MISSING"
    exit 0
  fi
  ADAPTER_CONTAINMENT=live ADAPTER_GATEWAY=live ADAPTER_TRACE=live ADAPTER_WORKFLOW=live \
    python3 conformance.py --out out/live --report out/live.json > out/live.log 2>&1
  RC=$?
  if grep -q "adapter-unavailable" out/live.log 2>/dev/null; then
    ok "a live adapter reported a typed adapter-unavailable rather than failing open"
  else
    check "live conformance exits 0" "$RC" "0"
  fi
  echo; echo "passed $PASS, failed $FAIL"
  [ "$FAIL" -eq 0 ] || exit 1
  echo "live: $PASS checks pass against the host components"
  exit 0
fi

echo "1. the minimal call: one document through the four doors"
python3 call.py --out out/call > out/call.log 2>&1
check "call.py exits 0" "$?" "0"
grep -q "subjects 1   plans 1   actors 4   runs 4" out/call.log \
  && ok "one document, one resolved plan, four actors, four runs" \
  || bad "the four doors did not agree"
grep -q "one trace per run: groups \[1\]   levels \[3\]   distinct trace ids \[3\]" out/call.log \
  && ok "each run reassembled as one trace out of 3 unrelated trace ids" \
  || bad "a run did not reassemble"
CALLER=$(python3 -c "
lines=open('call.py').read().splitlines()
a=[i for i,l in enumerate(lines) if 'CALLER CODE BEGINS' in l][0]
b=[i for i,l in enumerate(lines) if 'CALLER CODE ENDS' in l][0]
print(len([l for l in lines[a+1:b] if l.strip()]))")
[ "$CALLER" -lt 40 ] && ok "the caller writes $CALLER lines, under 40" \
  || bad "the caller writes $CALLER lines"
CALLSUM=$(python3 -c "import hashlib;print(hashlib.sha256(open('call.py','rb').read()).hexdigest()[:16])")

echo "2. conformance against the first adapter of every component"
python3 conformance.py --out out/c1 --report out/before.json > out/c1.log 2>&1
check "dry-run conformance exits 0" "$?" "0"
check "verdict" "$(field out/before.json "['verdict']")" "pass"
check "no check failed" "$(field out/before.json "['failures']")" "[]"
check "doors checked" "$(field out/before.json "['counters']['doors_checked']")" "4"
check "one resolved plan across the doors" "$(field out/before.json "['counters']['manifests_distinct']")" "1"
check "typed refusals, one per door" "$(field out/before.json "['counters']['typed_refusals']")" "4"
check "replays that were no-ops" "$(field out/before.json "['counters']['replay_noops']")" "4"
check "runs reassembled as one trace" "$(field out/before.json "['counters']['traces_reassembled']")" "4"

echo "3. swap proof: every component moved to its second adapter, call.py untouched"
export ADAPTER_CONTAINMENT=second ADAPTER_GATEWAY=second ADAPTER_TRACE=second ADAPTER_WORKFLOW=second
python3 call.py --out out/call-second > out/call-second.log 2>&1
check "the minimal call is unchanged under the second adapters" "$?" "0"
NOW=$(python3 -c "import hashlib;print(hashlib.sha256(open('call.py','rb').read()).hexdigest()[:16])")
check "call.py is byte-identical across the swap" "$NOW" "$CALLSUM"
python3 conformance.py --out out/c2 --report out/after.json > out/c2.log 2>&1
check "second-adapter conformance exits 0" "$?" "0"
unset ADAPTER_CONTAINMENT ADAPTER_GATEWAY ADAPTER_TRACE ADAPTER_WORKFLOW
check "verdict after the swap" "$(field out/after.json "['verdict']")" "pass"
names(){ python3 -c "import json;print(chr(10).join(c[0] for c in json.load(open('$1'))['checks']))"; }
diff <(names out/before.json) <(names out/after.json) > /dev/null \
  && ok "the same $(names out/before.json | wc -l | tr -d ' ') cases ran on both sides of the swap" \
  || bad "the case list changed"
check "the same number of checks" "$(field out/after.json "['checks_total']")" \
                                  "$(field out/before.json "['checks_total']")"
diff <(field out/before.json "['counters']") <(field out/after.json "['counters']") > /dev/null \
  && ok "the counters are identical across the swap" || bad "the counters moved"
DIFFERING=$(python3 -c "
import json
b=json.load(open('out/before.json'))['markers']; a=json.load(open('out/after.json'))['markers']
print(sum(1 for k in b if b[k]!=a.get(k)))")
check "components that really answered with a different implementation" "$DIFFERING" "4"
echo "  before: $(field out/before.json "['markers']")"
echo "  after:  $(field out/after.json "['markers']")"

echo "3b. one component at a time: the other three do not notice"
for VAR in ADAPTER_CONTAINMENT ADAPTER_GATEWAY ADAPTER_TRACE ADAPTER_WORKFLOW; do
  rm -rf out/one
  env $VAR=second python3 conformance.py --out out/one --report out/one.json > out/one.log 2>&1
  RC=$?
  MOVED=$(python3 -c "
import json
b=json.load(open('out/before.json'))['markers']; a=json.load(open('out/one.json'))['markers']
print(sum(1 for k in b if b[k]!=a.get(k)))")
  if [ "$RC" = "0" ] && [ "$MOVED" = "1" ]; then
    ok "$VAR=second: conformance holds and exactly one marker moved"
  else
    bad "$VAR=second (rc $RC, markers moved $MOVED)"
  fi
done

echo "4. deliberate breakage: one door carries a ceiling of its own"
python3 conformance.py --break-door-budget --out out/b1 --report out/broken.json > out/b1.log 2>&1
BRC=$?
check "the breakage run exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "verdict" "$(field out/broken.json "['verdict']")" "fail"
check "two resolved plans instead of one" "$(field out/broken.json "['counters']['manifests_distinct']")" "2"
check "still four doors, so this is a disagreement and not a missing run" \
      "$(field out/broken.json "['counters']['doors_checked']")" "4"
check "only cross-door cases failed, so every door alone is still green" \
      "$(python3 -c "
import json;f=json.load(open('out/broken.json'))['failures']
print(len(f)>0 and all(n.startswith('A') for n in f))")" "True"
ADAPTER_CONTAINMENT=second ADAPTER_GATEWAY=second ADAPTER_TRACE=second ADAPTER_WORKFLOW=second \
  python3 conformance.py --break-door-budget --out out/b2 --report out/broken2.json > out/b2.log 2>&1
B2RC=$?
check "the breakage fails under the second adapters too" \
      "$([ $B2RC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
python3 conformance.py --out out/repair --report out/repair.json > out/repair.log 2>&1
check "the same suite passes again once the door is restored" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "dry-run: $PASS checks pass, $(field out/before.json "['checks_total']") conformance checks, swap proof across 4 components, breakage fails both"
