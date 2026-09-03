#!/usr/bin/env bash
# Gate for the gateway harness. Everything here is measured, not claimed.
#   bash harness/gateway/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/gateway/test.sh --live   the same against the gateway on this host, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "12 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 12/12" out/dryrun.log && ok "12/12 cases passed" || bad "not 12/12"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 ../caller_lines.py gateway --count)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 ../caller_lines.py gateway --interface-only \
  && ok "the caller names no file in the adapter's own storage" \
  || bad "call.py reads the adapter's storage by path"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "one completion by class exits 0" "$?" "0"
grep -q "redeemed" out/call.log && ok "the caller read a redeemed ticket" || bad "no redeemed ticket"
VENDOR=a-vendor python3 call.py > out/call-vendor.log 2>&1
check "a request naming a vendor exits 2" "$?" "2"
grep -q "document-invalid" out/call-vendor.log && ok "typed as document-invalid (422)" || bad "not typed"
CEILING_MICROS=100 python3 call.py > out/call-cap.log 2>&1
check "a request over its cap exits 2" "$?" "2"
grep -q "budget-exhausted" out/call-cap.log && ok "typed as budget-exhausted (402)" || bad "not typed"
grep -q "no spend was incurred" out/call-cap.log && ok "refused before the call" || bad "not refused before the call"
MODEL_CLASS=gpt-4o python3 call.py > out/call-class.log 2>&1
check "a vendor's model name is not a class" "$?" "2"

echo "1c. the dry-run adapter's own failure path"
DRYRUN_FAIL=1 python3 call.py > out/call-fail.log 2>&1
check "an unreachable endpoint exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py routing.json | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 12/12" out/second.log && ok "12/12 cases passed on the second adapter" || bad "not 12/12"
AFTER_HASH=$(cat interface.py call.py conformance.py routing.json | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("serving_path", "how a completion is served"),
        ("ticket_state_at_submit", "what submit returns"),
        ("polls_to_claim", "how a result is read"),
        ("cost_status_at_submit", "when cost is known")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:24} {str(before[axis]):20} {str(after[axis]):20} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 12, "both bindings must pass the same cases"
assert before["endpoint_marker"] != after["endpoint_marker"], "the marker did not change with the binding"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=4" out/axes.log && ok "4 axes differ (serving path, submit state, polls, cost timing)" \
  || bad "$(tail -1 out/axes.log)"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: the caller branches on which adapter answered"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py call.py conformance.py routing.json adapters out/breakage/
python3 - <<'PY'
# The product name is assembled here so that this gate stays clean and only the
# copy under out/breakage/ carries the branch the scan is meant to catch.
product = "lite" + "llm"
path = "out/breakage/call.py"
src = open(path).read().replace(
    '    adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()',
    '    name = os.environ.get("ADAPTER", "dryrun")\n'
    f'    if name == "{product}":                     # the breakage: a branch on which adapter answered\n'
    '        name = "live"\n'
    '    adapter = ADAPTERS[name]()')
open(path, "w").write(src)
PY
python3 conformance.py --product-scan out/breakage > out/breakage.log 2>&1
check "the breakage run exits non-zero" "$?" "1"
grep -q "call.py" out/breakage.log && ok "the run names the file that broke it" || bad "file not named"
grep -q "product_hits=1" out/breakage.log && ok "product_hits went from 0 to 1" || bad "hits not counted"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the gateway on this host"
  if [ -z "${GATEWAY_URL:-}" ] || [ -z "${GATEWAY_KEY:-}" ]; then
    echo "  SKIP live mode: set GATEWAY_URL and GATEWAY_KEY (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live gateway exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed the same 12 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
