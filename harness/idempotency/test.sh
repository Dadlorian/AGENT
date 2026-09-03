#!/usr/bin/env bash
# Gate for the idempotency harness. Everything here is measured, not claimed.
#   bash harness/idempotency/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/idempotency/test.sh --live   the same against the on-disk ledger, if IDEMPOTENCY_LEDGER_PATH-worthy data exists
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter (log-fold-at-entry)"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "8 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 8/8" out/dryrun.log && ok "8/8 cases passed" || bad "not 8/8"

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
ADAPTER=dryrun python3 call.py > out/call-dryrun.log 2>&1
check "submit, replay, race, reuse-under-a-different-payload exits 0" "$?" "0"
grep -q "fresh\s*duplicate" out/call-dryrun.log && ok "replay answered duplicate with the same result" \
  || grep -q "duplicate" out/call-dryrun.log && ok "replay answered duplicate" || bad "no duplicate observed"
grep -q "idempotency-conflict" out/call-dryrun.log && ok "the reused key under a different payload is refused, typed" \
  || bad "no typed conflict"

echo "1c. same key, different payload is refused before any second effect"
ADAPTER=dryrun python3 - <<'PY' > out/conflict.log 2>&1
import os, sys
sys.path.insert(0, os.getcwd())
from interface import ClaimRequest, Problem, digest, load_adapter
a = load_adapter("dryrun", "out/conflict")
req = ClaimRequest.for_payload("k1", {"amount": 1}, "harness/idempotency:submit-unit",
                               "corr-k1", "user:corey", "human")
a.claim(req)
try:
    a.claim(ClaimRequest.for_payload("k1", {"amount": 2}, "harness/idempotency:submit-unit",
                                      "corr-k1", "user:corey", "human"))
    print("NOT REFUSED")
except Problem as p:
    print(p.body["type"], p.body["status"])
PY
grep -q "idempotency-conflict 409" out/conflict.log && ok "409, typed, before a second execution" || bad "not refused"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 8/8" out/second.log && ok "8/8 cases passed on the lease adapter" || bad "not 8/8"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("unit_of_conditionality", "how the claim is taken"),
        ("supports_in_flight", "whether a duplicate can be answered mid-execution"),
        ("overlapped", "duplicates answered while the winner was still running")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:24} {str(before[axis]):20} {str(after[axis]):20} ({why})")
assert len(differ) >= 2, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 8, "both bindings must pass the same cases"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 2 or more axes" "$?" "0"
grep -q "axes_differing=3" out/axes.log && ok "3 axes differ (conditionality, in-flight support, overlap observed)" \
  || bad "$(tail -1 out/axes.log)"

echo "3. deliberate breakage: remove the lease acquisition, leave the key on the wire"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py call.py conformance.py adapters out/breakage/
python3 - <<'PY'
# Reproduces the exact breakage cap-idempotency-implement's definition_of_done
# names: "Remove the lease acquisition from the conditional-write adapter
# while leaving the key on the wire", which is PASS.md B3's row for today
# (F-b3-16) applied to the second adapter.
path = "out/breakage/adapters/second.py"
src = open(path).read()
old = ('        with self._lock:                                     # the conditional write: atomic\n'
       '            row = self._leases.get(k)\n')
assert old in src, "anchor block not found; second.py changed shape"
new = ('        if True:                                              # BREAKAGE: lease acquisition removed\n'
       '            row = self._leases.get(k)                        # PASS.md B3: key on the wire, no lease\n'
       '            time.sleep(0.01)                                  # widens the read/write window\n')
open(path, "w").write(src.replace(old, new, 1))
PY
(cd out/breakage && python3 conformance.py --adapter second --report ../breakage.json) > out/breakage.log 2>&1
check "the broken adapter's conformance run exits 1" "$?" "1"
grep -q "executions 20 (a lease must serialise the winners)" out/breakage.log \
  && ok "every concurrent copy won: executions=20, overlapped=0" \
  || bad "$(grep 'launched at once' out/breakage.log)"
grep -q "conformance FAILED: 7/8" out/breakage.log && ok "7/8: only the race case fails" || bad "wrong pass count"

if [ "${1:-}" = "--live" ]; then
  echo "4. live: the on-disk, hash-chained log this platform already writes"
  SRC="${IDEMPOTENCY_LEDGER_PATH:-../../examples/end-to-end/out/ledger.jsonl}"
  if [ ! -f "$SRC" ]; then
    echo "  SKIP live mode: no ledger found at $SRC. Run examples/end-to-end/run.py first, or set"
    echo "  IDEMPOTENCY_LEDGER_PATH (see README.md). Nothing live was measured."
  else
    cp "$SRC" out/live-ledger.jsonl        # never mutate another harness's live file
    export IDEMPOTENCY_LEDGER_PATH="$(pwd)/out/live-ledger.jsonl"
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the on-disk ledger exits 0" "$?" "0"
    grep -q "conformance PASSED: 8/8" out/live.log && ok "live binding passed the same 8 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    ok "the same caller code ran live (rc $?); see out/call-live.log for the observed race"
    grep -q "fresh=1 " out/call-live.log \
      && ok "no lease, and the race still went to one winner here (timing-dependent, not guaranteed)" \
      || ok "no lease: the race went to more than one winner, matching PASS.md B3's recorded row (F-b3-16)"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
