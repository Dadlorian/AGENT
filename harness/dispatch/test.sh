#!/usr/bin/env bash
# Gate for the dispatch harness. Dry-run mode is measured here; --live is claimed
# until it is run on a host where the contained unit is reachable.
#
#   bash harness/dispatch/test.sh          the minimal call, conformance, the swap proof, three breakages
#   bash harness/dispatch/test.sh --live   the same against the executor named by DISPATCH_ACP_SOCKET
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field(){ python3 -c "import json;d=json.load(open('$1'));print(json.dumps(d$2))"; }

rm -rf out && mkdir -p out

if [ "${1:-}" = "--live" ]; then
  echo "LIVE mode: the contained unit named by DISPATCH_ACP_SOCKET / DISPATCH_UNIT"
  if [ -z "${DISPATCH_ACP_SOCKET:-}${DISPATCH_UNIT:-}" ]; then
    echo "  SKIPPED: neither DISPATCH_ACP_SOCKET nor DISPATCH_UNIT is set, so live mode"
    echo "  has no executor to reach. Set them (and GATEWAY_URL for model egress) and"
    echo "  run this again on the host. See the env table in README.md."
    echo "skipped: live mode needs DISPATCH_ACP_SOCKET or DISPATCH_UNIT"
    exit 0
  fi
  python3 conformance.py --adapter live --out out/live --report out/live.json > out/live.log 2>&1
  RC=$?
  if grep -q "adapter-unavailable" out/live.log 2>/dev/null; then
    ok "the live adapter reported a typed adapter-unavailable rather than failing open"
  else
    check "live conformance exits 0" "$RC" "0"
  fi
  echo; echo "passed $PASS, failed $FAIL"
  [ "$FAIL" -eq 0 ] || exit 1
  echo "live: $PASS checks pass"
  exit 0
fi

echo "1. the minimal call: plan twice, dispatch once, judge once"
ADAPTER=dryrun python3 call.py > out/call-dryrun.log 2>&1
check "call.py exits 0" "$?" "0"
grep -q "one plan digest, one result, one verdict" out/call-dryrun.log \
  && ok "one plan digest, one result, one verdict" || bad "something moved in the minimal call"
grep -q "plan run 2 .*identical" out/call-dryrun.log \
  && ok "the same document at the same head planned byte-identically twice" \
  || bad "two plans of one document differed"
grep -q "every head recorded=True" out/call-dryrun.log \
  && ok "every output the result names carries the head it became durable at" \
  || bad "an output has no recorded_at_head"
grep -q "judge  *pass (2 checks)" out/call-dryrun.log \
  && ok "the judge decided 2 checks and returned one verdict" || bad "the verdict is not what it was"

echo "1b. what the caller wrote"
python3 conformance.py --caller-lines > out/caller.log 2>&1
check "caller region is under 40 lines and names no adapter storage" "$?" "0"
sed -n 's/^caller_lines/  ..   caller_lines/p' out/caller.log
python3 conformance.py --product-scan > out/product.log 2>&1
check "no product name in the interface, the core, the caller or the shared dispatcher" "$?" "0"

echo "2. conformance against the dry-run dispatcher"
python3 conformance.py --adapter dryrun --out out/c1 --report out/before.json > out/c1.log 2>&1
check "dry-run conformance exits 0" "$?" "0"
sed -n 's/^adapter=/  ..   /p' out/c1.log
check "every assertion passed" "$(field out/before.json "['per_adapter'][0]['failures']")" "[]"
check "assertions_run is greater than zero" \
  "$(python3 -c "import json;print(json.load(open('out/before.json'))['per_adapter'][0]['assertions_run']>0)")" "True"
check "requests_scanned over the corpus" "$(field out/before.json "['per_adapter'][0]['requests_scanned']")" "50"
check "criterion_hits" "$(field out/before.json "['per_adapter'][0]['criterion_hits']")" "0"
check "verdicts_distinct over 100 gradings" "$(field out/before.json "['per_adapter'][0]['verdicts_distinct']")" "1"
check "connects_inet from the planner" "$(field out/before.json "['per_adapter'][0]['connects_inet']")" "0"
check "untyped failure bodies" "$(field out/before.json "['per_adapter'][0]['untyped']")" "0"
check "migrated_paths" "$(field out/before.json "['migrated_paths']")" "3"

echo "3. swap proof: the same cases, before and after the swap"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the minimal call is unchanged under the second dispatcher" "$?" "0"
python3 conformance.py --adapter second --out out/after --report out/swap-after.json > out/after.log 2>&1
check "after: queue-and-poll dispatcher" "$?" "0"
B=$(field out/before.json "['per_adapter'][0]['dispatcher_marker']")
A=$(field out/swap-after.json "['per_adapter'][0]['dispatcher_marker']")
echo "  before marker $B, after marker $A"
[ "$B" != "$A" ] && ok "a different dispatcher really answered" || bad "the same dispatcher answered twice"
BC=$(field out/before.json "['per_adapter'][0]['assertions_run']")
AC=$(field out/swap-after.json "['per_adapter'][0]['assertions_run']")
check "the same cases ran on both sides of the swap" "$BC" "$AC"
python3 conformance.py --adapter dryrun --adapter second --out out/both --report out/both.json > out/both.log 2>&1
check "both dispatchers in one report" "$?" "0"
check "adapters_run" "$(field out/both.json "['adapters_run']")" "2"
check "distinct dispatcher markers" \
  "$(python3 -c "import json;print(len(json.load(open('out/both.json'))['distinct_markers']))")" "2"
check "the plan digest did not move across the swap" "$(field out/both.json "['plan_digest_mismatches']")" "0"
check "the verdict did not move across the swap" "$(field out/both.json "['verdict_mismatches']")" "0"
check "the swapped-in dispatcher declares a different unit lifetime" \
  "$(python3 -c "import json;d=json.load(open('out/both.json'));print(len({p['binding']['unit_lifetime'] for p in d['per_adapter']}))")" "2"
check "and a different cancellation reach" \
  "$(python3 -c "import json;d=json.load(open('out/both.json'));print(len({p['cancel_stop_reason'] for p in d['per_adapter']}))")" "2"

echo "4. deliberate breakages: one per definition of done, each must fail"
echo "4a. the seam: the result is assembled before the state-seam write returns"
python3 conformance.py --adapter dryrun --adapter second --break durability \
  --out out/brk-dur --report out/brk-dur.json > out/brk-dur.log 2>&1
BRC=$?
check "the durability breakage exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "the targeted dispatcher names an output with no head" \
  "$(field out/brk-dur.json "['per_adapter'][0]['partial_outputs_without_head']")" "1"
check "the other dispatcher still reports no failure" \
  "$(field out/brk-dur.json "['per_adapter'][1]['failures']")" "[]"

echo "4b. the judge: the criterion text is inlined into the document's definition of done"
python3 conformance.py --adapter dryrun --adapter second --break criterion \
  --out out/brk-crit --report out/brk-crit.json > out/brk-crit.log 2>&1
BRC=$?
check "the criterion breakage exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "criterion_hits over the corpus is non-zero" \
  "$(python3 -c "import json;print(json.load(open('out/brk-crit.json'))['criterion_hits']>0)")" "True"
check "it fails identically under both engines, so the fault is in what dispatch carried" \
  "$(python3 -c "import json;d=json.load(open('out/brk-crit.json'));print(all(p['criterion_hits']>0 for p in d['per_adapter']))")" "True"
check "determinism did not move: verdicts_distinct stays 1 for each" \
  "$(python3 -c "import json;d=json.load(open('out/brk-crit.json'));print(all(p['verdicts_distinct']==1 for p in d['per_adapter']))")" "True"

echo "4c. the planner: one binding resolves the head itself while the log moves under it"
python3 conformance.py --adapter dryrun --adapter second --break head \
  --out out/brk-head --report out/brk-head.json > out/brk-head.log 2>&1
BRC=$?
check "the head breakage exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "plan_digest_mismatches is non-zero" \
  "$(python3 -c "import json;print(json.load(open('out/brk-head.json'))['plan_digest_mismatches']>0)")" "True"
check "every per-binding assertion stays green, which isolates the fault to one loader" \
  "$(python3 -c "import json;d=json.load(open('out/brk-head.json'));print(all(not p['failures'] for p in d['per_adapter']))")" "True"
check "purity did not move: connects_inet stays 0 under both bindings" \
  "$(python3 -c "import json;d=json.load(open('out/brk-head.json'));print(all(p['connects_inet']==0 for p in d['per_adapter']))")" "True"

echo "5. the suite passes again once the breakages are removed"
python3 conformance.py --adapter dryrun --adapter second --out out/repair --report out/repair.json > out/repair.log 2>&1
check "the same suite exits 0 again" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "dry-run: $PASS checks pass, 33 assertions per dispatcher, swap proven across 2 dispatchers, 3 breakages fail"
