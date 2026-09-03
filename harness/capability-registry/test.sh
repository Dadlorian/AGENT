#!/usr/bin/env bash
# Gate for the capability-registry harness. Everything here is measured, not claimed.
#   bash harness/capability-registry/test.sh          dry run: conformance, the swap proof, breakage
#   bash harness/capability-registry/test.sh --live   the same against .claude/skills/, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the signed-index (dry-run) adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "conformance exits 0" "$?" "0"
grep -oE "conformance PASSED: [0-9]+/[0-9]+" out/dryrun.log | sed 's/^/  ..   /'
grep -q "resolved_records=1 served_unverified=0" out/dryrun.log \
  && ok "the good fixture resolves and nothing unverified is served" || bad "an unverified record was served"
grep -q "refusals=2 refusals_typed=2" out/dryrun.log \
  && ok "the unsigned and the digest-mismatch fixtures are refused, both typed" || bad "a refusal was not typed"

echo "1b. the minimal call a caller writes"
python3 conformance.py --caller-lines > out/caller.log 2>&1
check "caller region is under 40 lines and names no adapter storage" "$?" "0"
grep -o "caller_lines=[0-9]*" out/caller.log | head -1 | sed 's/^/  ..   /'
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "publish, resolve, verify, rollback, refuse: exits 0" "$?" "0"
grep -qE "True\s+no \(refused\)" out/call.log && ok "digest matches and the in-place edit was refused" || bad "not shown"
grep -qE "1\.0\.0\s+True\s+no \(refused\)\s+1\.0\.0\s+no" out/call.log \
  && ok "rolled back to 1.0.0 and the forged signature was not accepted" || bad "rollback or forgery check failed"

echo "1c. the dry-run adapter's own failure path"
REGISTRY_FAIL=1 python3 call.py > out/call-fail.log 2>&1
check "an unreadable signing key exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"
grep -q "no record was appended" out/call-fail.log && ok "nothing was written" || bad "silence about the store"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the content-addressed adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("resolution", "how the record bytes are reached"),
        ("identity_is", "what identity means"),
        ("network_required", "whether the network is on the critical path"),
        ("trust_anchor", "what a verifier trusts"),
        ("store_kind", "what the record store looks like")]
differ = [a for a, _ in axes if before.get(a) != after.get(a)]
for axis, why in axes:
    print(f"{axis:18} {str(before.get(axis)):28} {str(after.get(axis)):28} ({why})")
for report in (before, after):
    assert report["served_unverified"] == 0, report["binding"]
    assert report["resolved_records"] == 1 and report["records_checked"] == 3, report["binding"]
    assert report["refusals"] == 2 and report["refusals_typed"] == 2, report["binding"]
    assert report["selected_by"] == "configuration", "a code edit between runs would not be a swap"
assert before["adapter"] == "signed-index" and after["adapter"] == "registry-fetch"
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
divergence = int(before["record_divergence"] != 0 or after["record_divergence"] != 0
                 or before["resolved_records"] != after["resolved_records"])
print(f"axes_differing={len(differ)} adapters_run={before['adapters_run'] + after['adapters_run']} "
      f"record_divergence={divergence} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "record_divergence=0" out/axes.log && ok "the two stores resolve the same fixture set identically" || bad "$(tail -1 out/axes.log)"
grep -q "adapters_run=2" out/axes.log && ok "the merged report shows 2 adapters run, selected by configuration" || bad "adapters_run is not 2"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: the digest check is downgraded from a refusal to a warning"
python3 conformance.py --adapter dryrun --break digest-warning --report out/break-1.json > out/break-1.log 2>&1
check "the breakage run exits non-zero" "$?" "1"
python3 - <<'PY' > out/break-check.log 2>&1
import json
one = json.load(open("out/break-1.json"))
assert one["served_unverified"] == 1, one["served_unverified"]
assert one["refusals"] == 1, one["refusals"]
print(f"served_unverified={one['served_unverified']} refusals={one['refusals']} "
      f"resolved_records={one['resolved_records']}")
PY
check "the digest-mismatch fixture was served and the unsigned fixture is still refused" "$?" "0"
cat out/break-check.log | sed 's/^/  ..   /'
grep -q "urn:agentic:problem:document-invalid" out/break-1.log && ok "the immutability and unknown-name refusals stayed typed under breakage" || true

if [ "${1:-}" = "--live" ]; then
  echo "5. live: skills resolved by directory path on this host"
  if [ -z "${SKILLS_DIR:-}" ] || [ -z "${SKILL_MANIFEST:-}" ] || [ -z "${REGISTRY_KEY_FILE:-}" ]; then
    echo "  SKIP live mode: set SKILLS_DIR, SKILL_MANIFEST and REGISTRY_KEY_FILE (see README.md)."
    echo "       Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live skill-file store exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "the live binding passed the same cases over its own fixtures" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
