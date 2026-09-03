#!/usr/bin/env bash
# Gate for the capability-packaging harness. Everything here is measured, not claimed.
#   bash harness/capability-packaging/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/capability-packaging/test.sh --live   the same against this host's .claude/skills/ tree, if SKILLS_ROOT is set
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

echo "1b. the minimal call a caller writes (below the >>> CALLER CODE marker in call.py)"
LINES=$(python3 - <<'PY'
lines = open("call.py").read().splitlines()
marks = [i for i, l in enumerate(lines) if ">>> CALLER CODE" in l]
assert len(marks) == 1, marks
body = lines[marks[0] + 1:]
end = next((i for i, l in enumerate(body) if l.startswith("if __name__")), len(body))
print(len([l for l in body[:end] if l.strip() and not l.strip().startswith("#")]))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
grep -n '\.jsonl\|\.ndjson\|\.db\|\.sqlite' call.py | grep -v '^[0-9]*:#' > out/storage.log
[ ! -s out/storage.log ] && ok "the caller names no file in an adapter's own storage" \
  || bad "call.py reads an adapter's storage by path"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "discover, load at 3 tiers, refuse, show second loader exits 0" "$?" "0"
grep -q "resident,body,reference" out/call.log && ok "all three tiers loaded for one package" || bad "not all 3 tiers"
grep -q '"missing": \[' out/call.log && ok "the missing-field package was refused with a typed problem" || bad "no typed refusal"
grep -q '"source": "registry"' out/call.log && grep -q 'sha256:' out/call.log \
  && ok "the same package was shown resolved by digest from the second loader" || bad "no digest from the second loader"

echo "1c. refusal cases through the caller's own envelope"
IDENTITY=no-such-package python3 call.py > out/call-unresolved.log 2>&1
check "an identity nothing publishes exits 2" "$?" "2"
grep -q "document-invalid" out/call-unresolved.log && ok "typed as document-invalid (422)" || bad "not typed"
IDENTITY=broken-legacy-importer python3 call.py > out/call-missing.log 2>&1
check "a package missing a required field exits 2" "$?" "2"
grep -q '"missing": \[' out/call-missing.log && ok "the missing field is named" || bad "field not named"
REFERENCE_PATH=references/nope.md python3 call.py > out/call-undeclared.log 2>&1
check "an undeclared reference path exits 2" "$?" "2"
grep -q "document-invalid" out/call-undeclared.log && ok "typed as document-invalid (422)" || bad "not typed"

echo "1d. the dry-run adapter's own failure path"
DRYRUN_FAIL=1 python3 call.py > out/call-fail.log 2>&1
check "an unreachable source exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 12/12" out/second.log && ok "12/12 cases passed on the second adapter" || bad "not 12/12"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("source", "where the resident tier came from"),
        ("digest_at_resolve", "whether identity carries a content digest")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:20} {str(before[axis]):10} {str(after[axis]):70} ({why})")
assert len(differ) == 2, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 12, "both bindings must pass the same cases"
assert before["source_marker"] != after["source_marker"], "the marker did not change with the binding"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 2 or more axes" "$?" "0"
grep -q "axes_differing=2" out/axes.log && ok "2 axes differ (where bytes come from, whether identity carries a digest)" \
  || bad "$(tail -1 out/axes.log)"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: a package is required to carry a third resident field"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py call.py conformance.py adapters out/breakage/
python3 - <<'PY'
# The breakage widens the required-field list past what the spec requires
# (cap-capability-packaging step 2: "reject any proposal to make a third one
# required"). A conformant package that carries only name and description is
# then wrongly refused, and the case that checks it turns FAIL.
path = "out/breakage/interface.py"
src = open(path).read().replace(
    'REQUIRED_RESIDENT = ("name", "description")',
    'REQUIRED_RESIDENT = ("name", "description", "owner")')
open(path, "w").write(src)
PY
(cd out/breakage && python3 conformance.py --adapter dryrun) > out/breakage.log 2>&1
check "the breakage run exits non-zero" "$?" "1"
grep -q "FAIL" out/breakage.log && ok "the run reports a FAIL case" || bad "no FAIL reported"
grep -q "conformance FAILED" out/breakage.log && ok "conformance FAILED, not PASSED" || bad "still reported PASSED"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: this host's .claude/skills/ tree"
  if [ -z "${SKILLS_ROOT:-}" ]; then
    echo "  SKIP live mode: set SKILLS_ROOT (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live tree exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed every case it could run (3 skipped: no broken fixture on a checked-in tree)" \
      || bad "live binding failed"
    ADAPTER=live IDENTITY="${LIVE_IDENTITY:-cap-capability-packaging}" \
      TRIGGER="packaging a capability" REFERENCE_PATH=references/packaging-shapes.md \
      python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
