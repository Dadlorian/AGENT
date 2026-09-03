#!/usr/bin/env bash
# Gate for the tool-access harness. Everything here is measured, not claimed.
#   bash harness/tool-access/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/tool-access/test.sh --live   the same against the tool endpoint on this host, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "17 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 17/17" out/dryrun.log && ok "17/17 cases passed" || bad "not 17/17"
grep -q "cases_not_exercised=0" out/dryrun.log && ok "every case was exercised, none skipped" || bad "a case was not exercised"
grep -q "tools_listed=5 schemas_checked=5 schemas_invalid=0" out/dryrun.log \
  && ok "the counts have teeth: 5 tools listed, 5 schemas checked, 0 invalid" || bad "counts missing"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
# caller_lines.py restricts its command line to the five harnesses named in plan.json;
# tool-access is measured by the same two functions until the plan row is merged.
LINES=$(python3 -c "import sys; sys.path.insert(0, '..'); import caller_lines; print(caller_lines.count('tool-access'))")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
HITS=$(python3 -c "import sys; sys.path.insert(0, '..'); import caller_lines; print(len(caller_lines.storage_hits('tool-access')))")
check "the caller names no file in the adapter's own storage" "$HITS" "0"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "discover, check, call, cancel, health exits 0" "$?" "0"
grep -q "tools discovered at bind" out/call.log && ok "the caller discovered the catalogue rather than assuming it" || bad "no discovery"
grep -q "cancel mid-flight  *stopped" out/call.log && ok "the second call was stopped in flight" || bad "no mid-flight cancel"
grep -q "health status  *serving (tools_listed=5" out/call.log && ok "health counted 5 tools rather than answering green" || bad "health did not count"

echo "1c. refusals a caller sees, each typed and before dispatch"
python3 - <<'PY'
import json
cfg = json.load(open("binding.json"))
undeclared = dict(cfg, call={"tool": "local.echo", "arguments": {"text": "hello"}})
json.dump(undeclared, open("out/binding-undeclared.json", "w"))
badargs = dict(cfg, call={"tool": "notes.read", "arguments": {"path": 17}})
json.dump(badargs, open("out/binding-badargs.json", "w"))
PY
ADAPTER=dryrun python3 call.py --binding out/binding-undeclared.json > out/call-undeclared.log 2>&1
check "a tool outside the declared surface exits 2" "$?" "2"
grep -q "policy-denied" out/call-undeclared.log && ok "typed as policy-denied (403)" || bad "not typed"
grep -q "platform-pre-dispatch" out/call-undeclared.log && ok "refused before dispatch, not after spend" || bad "no enforcement point"
ADAPTER=dryrun python3 call.py --binding out/binding-badargs.json > out/call-badargs.log 2>&1
check "arguments the published schema rejects exit 2" "$?" "2"
grep -q "arguments-invalid" out/call-badargs.log && ok "typed as arguments-invalid (422)" || bad "not typed"
REVISION=1999-01-01 ADAPTER=dryrun python3 call.py > out/call-revision.log 2>&1
check "a call declaring an unserved revision exits 2" "$?" "2"
grep -q "protocol-unsupported" out/call-revision.log && ok "typed as protocol-unsupported (400), refused per call" || bad "not typed"
CEILING_CALLS=1 ADAPTER=dryrun python3 call.py > out/call-ceiling.log 2>&1
check "a second call over the ceiling exits 2" "$?" "2"
grep -q "budget-exhausted" out/call-ceiling.log && ok "typed as budget-exhausted (402)" || bad "not typed"
DRYRUN_UNREACHABLE=1 ADAPTER=dryrun python3 call.py > out/call-unreachable.log 2>&1
check "an unreachable server exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-unreachable.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py binding.json | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 17/17" out/second.log && ok "17/17 cases passed on the second adapter" || bad "not 17/17"
AFTER_HASH=$(cat interface.py call.py conformance.py binding.json | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("catalogue_authority", "who authors the tool list"),
        ("call_locality", "whose endpoint and whose authorization"),
        ("catalogue_stability", "whether the list can change between binds"),
        ("cancel_outcome", "what a cancel mid-flight can promise")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:22} {str(before[axis]):24} {str(after[axis]):26} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 17, "both bindings must pass the same cases"
assert before["server_marker_observed"] != after["server_marker_observed"], \
    "the marker read back did not change with the binding"
assert before["tools_listed"] != after["tools_listed"], \
    "both servers published the same number of tools; the catalogue was not discovered"
assert before["declared_surface"] == after["declared_surface"], "the declared surface changed with the binding"
assert before["happy_tool"] == after["happy_tool"], "the same tool name was not served by both"
print(f"axes_differing={len(differ)} tools_before={before['tools_listed']} tools_after={after['tools_listed']} "
      f"cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=4" out/axes.log && ok "4 axes differ (authority, locality, stability, cancellation)" \
  || bad "$(tail -1 out/axes.log)"
python3 - <<'PY'
import json
after = json.load(open("out/after.json"))
assert after["catalogue_digest_first"] != after["catalogue_digest_second"], \
    "the second server's catalogue did not change between two binds"
print("the second server withdrew a tool between binds and the declared surface still held")
PY
check "the catalogue is re-read at every bind on the second adapter" "$?" "0"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: unregister every tool, changing nothing else"
# The state PASS.md A6 records for this capability: live and authenticated, zero
# tools registered. A conformance-only check calls that green.
TOOLS_UNREGISTERED=1 python3 conformance.py --adapter dryrun --report out/broken.json > out/breakage.log 2>&1
check "the breakage run exits non-zero" "$?" "1"
grep -q "conformance_failures=0" out/breakage.log \
  && ok "every shape assertion still passes: conformance_failures stays 0" || bad "the shape cases changed"
grep -q "tools_listed=0 schemas_checked=0" out/breakage.log \
  && ok "tools_listed and schemas_checked went 5 -> 0" || bad "the counts did not move"
grep -q "FAIL           tools_listed > 0" out/breakage.log \
  && ok "the run fails on the count and names it" || bad "the count assertion did not fail"
grep -q "status=empty" out/breakage.log \
  && ok "health says empty, not green, over a live authenticated server" || bad "health still answered green"
BROKEN_SKIPPED=$(python3 -c "import json; print(json.load(open('out/broken.json'))['cases_not_exercised'])")
[ "$BROKEN_SKIPPED" -ge 8 ] && ok "$BROKEN_SKIPPED cases reported NOT EXERCISED rather than passing" \
  || bad "only $BROKEN_SKIPPED cases were reported as not exercised"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the tool endpoint on this host"
  if [ -z "${TOOL_ENDPOINT_URL:-}" ] || [ -z "${TOOL_ENDPOINT_TOKEN:-}" ]; then
    echo "  SKIP live mode: set TOOL_ENDPOINT_URL and TOOL_ENDPOINT_TOKEN (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    LIVE=$?
    grep -q "conformance_failures=0" out/live.log && ok "the live binding broke no shape assertion" || bad "shape assertions failed live"
    LISTED=$(python3 -c "import json; print(json.load(open('out/live.json'))['tools_listed'])")
    if [ "$LISTED" -gt 0 ]; then
      check "conformance against the live endpoint exits 0" "$LIVE" "0"
      ADAPTER=live python3 call.py > out/call-live.log 2>&1
      check "the same caller code runs live" "$?" "0"
    else
      echo "  NOTE live endpoint answered and authenticated with $LISTED tools registered."
      echo "       That is the state PASS.md A6 records (F-a6-03). The run fails on the count, not on the shape."
      check "an empty live catalogue fails the run rather than passing it" "$LIVE" "1"
    fi
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
