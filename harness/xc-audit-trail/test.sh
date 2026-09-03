#!/usr/bin/env bash
# Gate for the xc-audit-trail harness. Everything here is measured, not claimed.
#   bash harness/xc-audit-trail/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/xc-audit-trail/test.sh --live   the same, projected over this repository's own ledger
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "6 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 6/6" out/dryrun.log && ok "6/6 cases passed" || bad "not 6/6: $(tail -1 out/dryrun.log)"

echo "1b. no product name outside adapters/"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "1c. the minimal call a caller writes"
LINES_OUT=$(python3 conformance.py --caller-lines 2>&1)
CALLER_EXIT=$?
echo "$LINES_OUT"
[ "$CALLER_EXIT" -eq 0 ] && ok "caller code under 40 lines, no storage named" || bad "caller-lines check failed"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "the minimal call exits 0" "$?" "0"
grep -q "attributed to" out/call.log && ok "the caller read entries, a correlation fetch and an attribution" \
  || bad "call.py did not report attribution"

echo "1d. the dry-run adapter's own failure path"
TRAIL_DRYRUN_FAIL=1 ADAPTER=dryrun python3 call.py > out/call-fail.log 2>&1
check "an unreachable store exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py scan.py verify_external.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 7/7" out/second.log \
  && ok "7/7 cases passed on the second adapter (one more: its own external verifier)" || bad "not 7/7"
AFTER_HASH=$(cat interface.py call.py conformance.py scan.py verify_external.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"

python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("execution_model", "the write model and who holds the only copy"),
        ("adapter", "which entity answered"),
        ("external_checkable", "whether a party holding none of our credentials can verify")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:20} {str(before[axis])[:44]:44} {str(after[axis])[:44]:44} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_run"] == 6 and after["cases_run"] == 7, (before["cases_run"], after["cases_run"])
assert before["cases_passed"] == before["cases_run"], "the dry-run binding must pass all its cases"
assert after["cases_passed"] == after["cases_run"], "the second binding must pass all its cases (one more: its own external verifier)"
assert before["external_verifications"] == 0, before["external_verifications"]
assert after["external_verifications"] >= 1, "the second store's own external verifier never ran"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=3" out/axes.log && ok "3 axes differ; only the second store is externally checkable" \
  || bad "$(tail -1 out/axes.log)"

echo "3. deliberate breakage: the scan's schedule declaration is gone, called inline from the writer"
python3 conformance.py --adapter dryrun --break wiring-fault --report out/breakage-report.json \
  > out/breakage.log 2>&1
BREAK_EXIT=$?
[ "$BREAK_EXIT" -ne 0 ] && ok "the broken wiring exits non-zero ($BREAK_EXIT)" || bad "the breakage did not fail"
grep -q "scan-not-independent: identity=actor:writer-process independent=False scheduled=False" out/breakage.log \
  && ok "the failure names the identity: the writer's, not a scanner's" || bad "no identity named in the failure"
python3 - <<'PY' > out/breakage-check.log 2>&1
import json
r = json.load(open("out/breakage-report.json"))
scan = r["independent_scan"]
assert scan["chain_breaks"] == 0, scan["chain_breaks"]
assert scan["entries_checked"] == 24, scan["entries_checked"]
assert scan["adapters_run"] == 1, scan["adapters_run"]
assert scan["independent"] is False and scan["scheduled"] is False, scan
print(f"chain_breaks={scan['chain_breaks']} entries_checked={scan['entries_checked']} "
     f"adapters_run={scan['adapters_run']} independent={scan['independent']} scheduled={scan['scheduled']}")
PY
check "the record itself held: only the wiring broke" "$?" "0"
cat out/breakage-check.log

if [ "${1:-}" = "--live" ]; then
  echo "4. live: this repository's own ledger, kb/ledger.jsonl via tools/kb.py"
  if [ -z "${AUDIT_TRAIL_LEDGER_PATH:-}" ]; then
    echo "  SKIP live mode: set AUDIT_TRAIL_LEDGER_PATH (see README.md). Nothing live was measured."
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
