#!/usr/bin/env bash
# Gate for the memory harness. Everything here is measured, not claimed.
#   bash harness/memory/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/memory/test.sh --live   the same against a live-stub store path, if MEMORY_LIVE_STORE_PATH is set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "10 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 10/10" out/dryrun.log && ok "10/10 cases passed" || bad "not 10/10"

echo "1b. the minimal call a caller writes"
LINES=$(python3 - <<'PY'
lines = open("call.py").read().splitlines()
marks = [i for i, l in enumerate(lines) if ">>> CALLER CODE" in l]
body = lines[marks[0] + 1:]
end = next((i for i, l in enumerate(body) if l.startswith("if __name__")), len(body))
print(len([l for l in body[:end] if l.strip() and not l.strip().startswith("#")]))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
! grep -nE "\.(jsonl|ndjson|db|sqlite3?)['\"]" call.py > /tmp/memory_storage_hits.$$ \
  && ok "the caller names no file in an adapter's own storage" \
  || bad "call.py names adapter storage: $(cat /tmp/memory_storage_hits.$$)"
rm -f /tmp/memory_storage_hits.$$
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "the minimal call exits 0" "$?" "0"
grep -q "True.*True.*True" out/call.log \
  && ok "the caller shows its own item recalled, expiry excluded, cross-scope excluded" \
  || bad "call.py did not report all three true"

echo "1c. the dry-run adapter's own failure path"
DRYRUN_FAIL=1 ADAPTER=dryrun python3 - <<'PY' > out/call-fail.log 2>&1
import sys, json
sys.path.insert(0, ".")
from interface import Problem, RememberRequest
from adapters.dryrun import DryRunAdapter
a = DryRunAdapter()
try:
    a.remember(RememberRequest.from_dict({"scope": {"principal": "user:corey"}, "kind": "semantic",
        "body": {"n": 1}, "produced_by": "user:corey", "correlation_id": "c1", "expires_at": "2099-01-01T00:00:00Z"}))
    sys.exit(0)
except Problem as p:
    print(json.dumps(p.body, indent=2))
    sys.exit(2)
PY
check "an unreachable store exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
rm -rf out/scope-store
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 10/10" out/second.log && ok "10/10 cases passed on the second adapter" || bad "not 10/10"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"

echo "2b. the same recall, from both stores, over the same fixtures"
rm -rf out/scope-store
python3 conformance.py --adapter dryrun --adapter second --report out/both.json > out/both.log 2>&1
check "the combined conformance run exits 0" "$?" "0"
grep -q "conformance PASSED: 20/20" out/both.log && ok "20/20 cases across both bindings" || bad "not 20/20"
grep -q "adapters_run=2 stores_reached_distinct=2 result_divergence=0" out/both.log \
  && ok "adapters_run=2, two distinct markers reached, result_divergence=0" \
  || bad "$(grep adapters_run out/both.log)"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("execution_model", "where a candidate is found"),
        ("retrieval_model", "ranked vs exact-key"),
        ("adapter", "which entity answered"),
        ("marker", "the binding's own marker, read from its response"),
        ("declared_gaps", "what this binding admits it cannot do")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:16} {str(before[axis])[:40]:40} {str(after[axis])[:40]:40} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 10, "both bindings must pass the same cases"
assert before["marker"] != after["marker"], "the marker did not change with the binding"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ on 3 or more axes" "$?" "0"
grep -q "axes_differing=5" out/axes.log && ok "5 axes differ (execution model, retrieval model, entity, marker, gaps)" \
  || bad "$(tail -1 out/axes.log)"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: on-read expiry moved out of the shared recall path"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py adapters call.py conformance.py out/breakage/
sed -i \
  's/kept = \[it for it in candidates if not _expired(it, at)\]/kept = list(candidates)  # BREAKAGE: expiry only enforced by sweep(), never on read/' \
  out/breakage/interface.py
grep -q "BREAKAGE" out/breakage/interface.py && ok "the on-read expiry filter was removed from recall()" \
  || bad "sed did not find the line to break"
( cd out/breakage && rm -rf out && python3 conformance.py --adapter dryrun --adapter second --report /dev/null \
    > breakage.log 2>&1 )
BREAK_STATUS=$?
[ "$BREAK_STATUS" -ne 0 ] && ok "conformance exits non-zero under the breakage" \
  || bad "conformance still exited 0 with expiry unenforced"
grep -q "expired_served=1" out/breakage/breakage.log \
  && ok "expired_served=1 on both bindings: the stale item was served" \
  || bad "expired_served did not go to 1: $(grep expired_served out/breakage/breakage.log)"
grep -q "cross_scope_hits=0" out/breakage/breakage.log \
  && ok "cross_scope_hits=0 still holds: the scope check and the expiry check fail independently" \
  || bad "the scope check broke too, which would hide that this breakage targets expiry alone"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the stub store path (remember/recall only - PASS.md has no memory row, so"
  echo "   supersede and forget have no component to reach and are a declared gap, not run here)"
  if [ -z "${MEMORY_LIVE_STORE_PATH:-}" ]; then
    echo "  SKIP live mode: set MEMORY_LIVE_STORE_PATH (see README.md). Nothing live was measured."
  else
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the minimal call runs against the live stub path" "$?" "0"
    grep -q "True.*True.*True" out/call-live.log \
      && ok "live stub: own item recalled, expiry excluded, cross-scope excluded" \
      || bad "live stub did not report all three true"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
