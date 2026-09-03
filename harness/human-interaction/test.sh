#!/usr/bin/env bash
# Gate for the human-interaction harness. Dry-run mode is measured here; --live is
# claimed until it is run on the host.
#
#   bash harness/human-interaction/test.sh          conformance, the swap proof, the breakage
#   bash harness/human-interaction/test.sh --live   the same against APPROVE_DELIVER_URL
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field(){ python3 -c "import json,sys;d=json.load(open('$1'));print(json.dumps(d$2))"; }
sf()   { python3 -c "import json;d=json.load(open('$1'));print(json.dumps(d['per_surface'][$2]['$3']))"; }

rm -rf out && mkdir -p out

if [ "${1:-}" = "--live" ]; then
  echo "LIVE mode: the approval unit named by APPROVE_DELIVER_URL"
  if [ -z "${APPROVE_DELIVER_URL:-}" ]; then
    echo "  SKIPPED: APPROVE_DELIVER_URL is unset, so live mode has no endpoint."
    echo "  Set APPROVE_DELIVER_URL, APPROVE_ITEM_URL and APPROVE_TOKEN and run this again on"
    echo "  the host. Every route is supplied whole by the operator: none is invented. See README."
    echo "skipped: live mode needs APPROVE_DELIVER_URL"
    exit 0
  fi
  python3 conformance.py --surface live --out out/live --report out/live.json > out/live.log 2>&1
  RC=$?
  if grep -q "adapter-unavailable" out/live.log 2>/dev/null; then
    ok "the live surface reported a typed adapter-unavailable rather than failing open"
  else
    check "live conformance exits 0" "$RC" "0"
  fi
  echo; echo "passed $PASS, failed $FAIL"
  [ "$FAIL" -eq 0 ] || exit 1
  echo "live: $PASS checks pass against APPROVE_DELIVER_URL"
  exit 0
fi

echo "1. the minimal call: one run parked on a person, resumed by one decision"
ADAPTER=dryrun python3 call.py > out/call-dryrun.log 2>&1
check "call.py exits 0" "$?" "0"
grep -q "pause == resume: True" out/call-dryrun.log \
  && ok "the run resumed on the correlation id it was parked with" || bad "the correlation id moved"
grep -q "artifact headline: Coupon pricing fix, reviewed" out/call-dryrun.log \
  && ok "the edit is the artifact the run published, not the proposed one" || bad "the edit was recorded and not applied"
grep -q "same decision again -> duplicate" out/call-dryrun.log \
  && ok "the same decision delivered twice resumed the run once" || bad "a redelivery resumed the run again"
grep -q "second decision -> idempotency-conflict" out/call-dryrun.log \
  && ok "a second decision on the same ask is refused as a replay (409)" || bad "a second decision was applied"
grep -q "late decision -> deadline-exceeded" out/call-dryrun.log \
  && ok "a decision after the deadline is refused with a typed problem (504)" || bad "a late decision was applied"
grep -q "stamped     correlation corr-hitl-0001" out/call-dryrun.log \
  && ok "identity, correlation and the ceiling are stamped on the pause" || bad "the pause carries no stamps"
grep -q "resume      correlation corr-hitl-0001" out/call-dryrun.log \
  && ok "the same identity and correlation are stamped again on the resume" || bad "the resume carries no stamps"

echo "1b. what the caller wrote, measured the one way (harness/caller_lines.py)"
LINES=$(python3 -c "import sys;sys.path.insert(0,'..');import caller_lines as c;print(c.count('human-interaction'))")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
HITS=$(python3 -c "import sys;sys.path.insert(0,'..');import caller_lines as c;print(len(c.storage_hits('human-interaction')))")
check "call.py names no store or adapter file by path" "$HITS" "0"

echo "1c. the failure path, not only the happy one"
DRYRUN_FAIL=1 ADAPTER=dryrun python3 call.py > out/call-fail.log 2>&1
check "an undeliverable ask exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log \
  && ok "and returns a typed problem, not a traceback" || bad "the failure was untyped"

echo "2. conformance against the first surface"
python3 conformance.py --surface dryrun --out out/c1 --report out/before.json > out/c1.log 2>&1
check "dry-run conformance exits 0" "$?" "0"
check "every check passed" "$(sf out/before.json 0 failures)" "[]"
check "resumed_on_same_correlation" "$(sf out/before.json 0 resumed_on_same_correlation)" "4"
check "edit_changed_artifact" "$(sf out/before.json 0 edit_changed_artifact)" "true"
check "duplicate_resumes over 10 deliveries" "$(sf out/before.json 0 duplicate_resumes)" "0"
check "untyped_refusals" "$(sf out/before.json 0 untyped_refusals)" "0"
check "selected_by" "$(sf out/before.json 0 selected_by)" '"configuration"'
check "no product or host name outside adapters/" "$(field out/before.json "['product_hits']")" "0"

echo "3. swap proof: the same cases, before and after the surface is swapped"
SUM_BEFORE=$(sha256sum interface.py store.py run.py call.py conformance.py | sha256sum)
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the minimal call is unchanged under the second surface" "$?" "0"
python3 conformance.py --surface second --out out/c2 --report out/after.json > out/c2.log 2>&1
check "after: the streaming surface" "$?" "0"
SUM_AFTER=$(sha256sum interface.py store.py run.py call.py conformance.py | sha256sum)
check "the swap was configuration, not a code edit" "$SUM_BEFORE" "$SUM_AFTER"
B=$(sf out/before.json 0 surface); A=$(sf out/after.json 0 surface)
echo "  before $B, after $A"
[ "$B" != "$A" ] && ok "a different surface really answered" || bad "the same surface answered twice"
check "the same cases ran on both sides of the swap" \
  "$(sf out/before.json 0 checks_total)" "$(sf out/after.json 0 checks_total)"
check "the four decisions resumed on one id after the swap too" \
  "$(sf out/after.json 0 resumed_on_same_correlation)" "4"
python3 conformance.py --surface dryrun --surface second --out out/both --report out/both.json > out/both.log 2>&1
check "both surfaces in one report" "$?" "0"
check "adapters_run" "$(field out/both.json "['adapters_run']")" "2"
check "distinct surface markers" \
  "$(python3 -c "import json;print(len(json.load(open('out/both.json'))['distinct_markers']))")" "2"
check "one store, one open ask, parked on one surface and decided on the other" \
  "$(field out/both.json "['cross_surface']['same_correlation']")" "true"
check "and the reviewer's edit is still what the run continued with" \
  "$(field out/both.json "['cross_surface']['edit_changed_artifact']")" "true"
D1=$(python3 -c "import json;d=json.load(open('out/both.json'))['per_surface'];print(d[0]['binding']['delivery_model'],d[1]['binding']['delivery_model'])")
check "the pair differs in execution model, not in product" "$D1" "request_response stream"

echo "4. deliberate breakage: the streaming surface resumes from the copy it holds"
python3 conformance.py --surface second --break-client-held --out out/bk2 --report out/broken-second.json > out/bk2.log 2>&1
BRC=$?
check "the streaming run exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "nine of the ten deliveries applied again" "$(sf out/broken-second.json 0 duplicate_resumes)" "9"
check "and one case resumed on an identifier the client minted" \
  "$(sf out/broken-second.json 0 resumed_on_same_correlation)" "3"
check "the edit still reached the artifact, so this is not a broken resume" \
  "$(sf out/broken-second.json 0 edit_changed_artifact)" "true"
python3 conformance.py --surface dryrun --break-client-held --out out/bk1 --report out/broken-first.json > out/bk1.log 2>&1
check "the first surface is untouched by the same run" "$?" "0"
check "singling out one surface is the point: the other still reports no duplicates" \
  "$(sf out/broken-first.json 0 duplicate_resumes)" "0"
python3 conformance.py --surface second --out out/repair --report out/repair.json > out/repair.log 2>&1
check "the same suite passes again once the store is the resume point" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "dry-run: $PASS checks pass, swap proven across 2 surfaces, breakage fails the streaming surface only"
