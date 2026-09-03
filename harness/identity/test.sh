#!/usr/bin/env bash
# Gate for the identity harness. Everything in dry run is measured here.
#   bash harness/identity/test.sh          the minimal call, conformance, the swap proof, one breakage
#   bash harness/identity/test.sh --live   the same against the identity component on this host
#
# There is no identity component on this host (PASS.md B3 records the adapter as
# absent), so --live states that and stops rather than pretending something ran.
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field(){ python3 -c "import json;d=json.load(open('$1'));print(json.dumps(d$2).strip('\"'))"; }
# harness/caller_lines.py is the one method every harness uses; its functions take
# a harness name, so this harness calls them without editing that file's own list.
caller(){ python3 -c "import sys;sys.path.insert(0,'..');import caller_lines as c;print(c.$1('identity'))"; }

rm -rf out && mkdir -p out

if [ "${1:-}" = "--live" ]; then
  echo "LIVE mode: the identity component on this host"
  if [ -z "${IDENTITY_ISSUER_URL:-}" ] && [ -z "${WORKLOAD_API_SOCKET:-}" ]; then
    echo "  SKIPPED: unset -> IDENTITY_ISSUER_URL, WORKLOAD_API_SOCKET"
    echo "  PASS.md B3 records the adapter for Identity as absent and PASS.md A6 records no"
    echo "  identity field anywhere in the system, so there is nothing here to reach. See the"
    echo "  env-var table in README.md and run this again on a host that has an issuer."
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    RC=$?
    grep -q "adapter-unavailable" out/call-live.log \
      && echo "  the live adapter said so with a typed refusal (exit $RC), rather than failing open"
    echo "skipped: live mode needs IDENTITY_ISSUER_URL or WORKLOAD_API_SOCKET"
    exit 0
  fi
  python3 conformance.py --adapter live --min-actions "${MIN_ACTIONS:-50}" --report out/live.json \
    > out/live.log 2>&1
  RC=$?
  if grep -q "adapter-unavailable" out/live.log; then
    ok "the live adapter reported a typed adapter-unavailable rather than failing open"
  else
    check "live conformance exits 0" "$RC" "0"
  fi
  echo; echo "passed $PASS, failed $FAIL"
  [ "$FAIL" -eq 0 ] || exit 1
  echo "live: $PASS checks against the host"
  exit 0
fi

echo "1. the minimal call: one unit of work, one downstream call, one refused hop"
python3 call.py > out/call.log 2>&1
check "call.py exits 0" "$?" "0"
grep -q "hop 0  agent:worker-7" out/call.log && grep -q "hop 2  user:corey" out/call.log \
  && ok "three hops on the issued credential, current actor first, the person last" \
  || bad "the chain is not three hops"
grep -q "obtained_via direct" out/call.log \
  && ok "the chain is rooted in a hop nobody self-asserted" || bad "the chain is unrooted"
grep -q "scope-must-narrow" out/call.log \
  && ok "the hop that widened its scope was refused, typed 403 policy-denied" \
  || bad "the widening hop was not refused"
grep -q "no credential was issued" out/call.log \
  && ok "the refusal says nothing was issued" || bad "the refusal does not say what happened"
LINES=$(caller count)
[ "$LINES" -lt 40 ] && ok "the caller writes $LINES lines, under 40" || bad "the caller writes $LINES lines"
[ "$(caller storage_hits)" = "[]" ] \
  && ok "the caller names no file in an adapter's own storage" || bad "call.py names adapter storage"

echo "1b. the failure paths a caller can actually get"
DRYRUN_FAIL=1 python3 call.py > out/call-fail.log 2>&1
check "an unreachable issuing authority exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"
ADAPTER=live python3 call.py > out/call-live.log 2>&1
check "the absent component exits 2" "$?" "2"
grep -q "no identity field anywhere in the system" out/call-live.log \
  && ok "the live adapter names the absence instead of implying something answered" \
  || bad "the live adapter did not say what is missing"
WIDEN_SCOPE=read:memory python3 call.py > out/call-widen2.log 2>&1
check "a different widening scope is refused the same way" "$?" "0"
grep -q "read:memory" out/call-widen2.log && ok "the refusal names the scope that was asked for" || bad "not named"

echo "2. conformance against the first adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "conformance exits 0" "$?" "0"
grep -q "conformance PASSED: 16/16" out/dryrun.log && ok "16/16 cases passed" || bad "not 16/16"
check "actions checked in the chain corpus" "$(field out/before.json "['actions_checked']")" "50"
check "chains shorter than the hops that occurred" "$(field out/before.json "['short_chains']")" "0"
check "actions whose current actor did not execute" \
      "$(field out/before.json "['executing_unit_mismatch']")" "0"
check "cyclic chains" "$(field out/before.json "['cyclic']")" "0"
check "actions with no subject" "$(field out/before.json "['missing_subject']")" "0"
check "how the adapter was selected" "$(field out/before.json "['selected_by']")" "configuration"

echo "3. swap proof: the second adapter, no code edit between the two runs"
BEFORE_HASH=$(cat interface.py call.py conformance.py trust.json | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 16/16" out/second.log && ok "16/16 cases passed on the second adapter" || bad "not 16/16"
AFTER_HASH=$(cat interface.py call.py conformance.py trust.json | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
names(){ python3 -c "import json;print(chr(10).join(c['case'].split(':')[0] for c in json.load(open('$1'))['cases']))"; }
diff <(names out/before.json) <(names out/after.json) > /dev/null \
  && ok "the same 16 cases ran on both sides of the swap" || bad "the case list changed"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("root_of_trust", "how a root credential comes to exist"),
        ("verification_locus", "where a presented credential is checked"),
        ("credential_form", "what is behind a handle"),
        ("authority_calls", "calls to an authority for one conformance run"),
        ("unsupported", "the operation form each binding declares it cannot serve"),
        ("marker", "what the answer said")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:20} {str(before[axis]):46} {str(after[axis]):46} ({why})")
same = ["actions_checked", "short_chains", "cyclic", "executing_unit_mismatch", "missing_subject",
        "cases_run", "cases_passed", "chain", "lifetimes_s", "enforcement_point_observed"]
moved = [k for k in same if before[k] != after[k]]
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert not moved, f"the contract moved with the binding: {moved}"
assert before["cases_passed"] == after["cases_passed"] == 16, "both bindings must pass the same cases"
print(f"axes_differing={len(differ)} contract_fields_unchanged={len(same)}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=6 contract_fields_unchanged=10" out/axes.log \
  && ok "6 axes differ and 10 contract facts are identical across the swap" \
  || bad "$(tail -1 out/axes.log)"
CALLSUM=$(python3 -c "import hashlib;print(hashlib.sha256(open('call.py','rb').read()).hexdigest()[:16])")
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
NOW=$(python3 -c "import hashlib;print(hashlib.sha256(open('call.py','rb').read()).hexdigest()[:16])")
check "call.py is byte-identical across the swap" "$NOW" "$CALLSUM"
diff <(grep "^  hop " out/call.log) <(grep "^  hop " out/call-second.log) > /dev/null \
  && ok "the caller reads the same three-hop chain from both adapters" || bad "the chain changed"
grep -q "authority calls 3" out/call.log && grep -q "authority calls 0" out/call-second.log \
  && ok "the first asked an authority 3 times, the second none: the swap really happened" \
  || bad "the two adapters did the same work"

echo "3b. both bindings in one run, as the definition of done words it"
python3 conformance.py --adapter dryrun --adapter second --report out/pair.json > out/pair.log 2>&1
check "the pair run exits 0" "$?" "0"
check "adapters run" "$(field out/pair.json "[0]['adapters_run']")" "2"
check "selected by" "$(field out/pair.json "[1]['selected_by']")" "configuration"
check "each binding declares the subset it does not serve" \
      "$(python3 -c "
import json;d=json.load(open('out/pair.json'));print(all(r['unsupported'] for r in d))")" "True"

echo "4. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped code exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "5. deliberate breakage: one hop forwards the incoming credential instead of exchanging it"
IDENTITY_BREAK=forward-token python3 conformance.py --adapter dryrun --report out/broken.json \
  > out/broken.log 2>&1
BRC=$?
check "the breakage run exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "chains shorter than the hops that occurred" "$(field out/broken.json "['short_chains']")" "1"
check "actions whose current actor did not execute" \
      "$(field out/broken.json "['executing_unit_mismatch']")" "1"
check "still 50 actions, so this is a defect and not a missing run" \
      "$(field out/broken.json "['actions_checked']")" "50"
grep -q "is shorter than the 3 hops that occurred" out/broken.log \
  && ok "the run names the action and the chain it found" || bad "the finding is not named"
IDENTITY_BREAK=forward-token python3 conformance.py --adapter second --report out/broken2.json \
  > out/broken2.log 2>&1
check "the same breakage leaves the second adapter green" "$?" "0"
check "its chains are still whole" "$(field out/broken2.json "['short_chains']")" "0"
ok "the breakage singles out one binding: a document naming its attested unit cannot be forwarded"
python3 conformance.py --adapter dryrun --report out/repair.json > out/repair.log 2>&1
check "the same suite passes again once the hop is restored" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "dry-run: $PASS checks pass, 16 conformance cases on each of 2 adapters, 50-action chain corpus, breakage fails one binding and not the other"
