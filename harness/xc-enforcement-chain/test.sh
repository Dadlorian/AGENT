#!/usr/bin/env bash
# Gate for the enforcement-chain harness. Everything here is measured, not claimed.
#   bash harness/xc-enforcement-chain/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/xc-enforcement-chain/test.sh --live   the same against the host's own points, if the env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out
EXAMPLE_DIR=$(cd ../../examples/end-to-end && pwd)

echo "1. conformance against the in-process enforcement point"
python3 conformance.py --adapter dryrun --min-units 100 --report out/before.json > out/dryrun.log 2>&1
check "13 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 13/13" out/dryrun.log && ok "13/13 cases passed" || bad "not 13/13"
grep -q "units_checked=104 metered_units=96 slots_missing=0 out_of_order=0 missing_inverse=0" out/dryrun.log \
  && ok "104 units, 96 metered, 0 slots missing, 0 out of order, 0 missing inverse" || bad "the counts line is not clean"
grep -q "ungated_metered_calls=0 chain_context_missing=0" out/dryrun.log \
  && ok "0 ungated metered calls, 0 units with no chain context" || bad "a metered call was reached unchained"
grep -q "ways_in=human,event,schedule,external points=admission,dispatch,call" out/dryrun.log \
  && ok "four doors, three points, one chain" || bad "a door or a point was not covered"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 - <<'PY'
import os, sys
sys.path.insert(0, os.path.abspath(".."))
import caller_lines
caller_lines.HARNESSES = caller_lines.HARNESSES + ("xc-enforcement-chain",)
print(caller_lines.count("xc-enforcement-chain"))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 - <<'PY'
import os, sys
sys.path.insert(0, os.path.abspath(".."))
import caller_lines
caller_lines.HARNESSES = caller_lines.HARNESSES + ("xc-enforcement-chain",)
hits = caller_lines.storage_hits("xc-enforcement-chain")
for n, line in hits:
    print(f"call.py:{n}: names adapter storage: {line}")
sys.exit(1 if hits else 0)
PY
check "the caller names no file in the enforcement point's own storage" "$?" "0"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "one envelope through four doors exits 0" "$?" "0"
grep -q "admission->dispatch->call" out/call.log && ok "every door crossed the same three points" || bad "a door skipped a point"
grep -c "budget-exhausted  402" out/call.log | grep -qx "4" \
  && ok "the same first refusal at all four doors (budget.reserve, 402)" || bad "the doors got different refusals"
grep -q "ungated_metered_calls=1" out/call.log \
  && ok "a caller that skipped the chain was counted" || bad "the skipped link was not counted"
grep -q "fail_open_slots=3 when one slot reports passed" out/call.log \
  && ok "a link that fails open is detected" || bad "a hollow link went undetected"
grep -q "0 in the run above" out/call.log && ok "the honest run has no fail-open link" || bad "a slot already fails open"
DIGEST_A=$(grep "chain records digest" out/call.log | awk '{print $4}')
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the out-of-process point" "$?" "0"
DIGEST_B=$(grep "chain records digest" out/call-second.log | awk '{print $4}')
check "identical chain records from both enforcement points" "$DIGEST_B" "$DIGEST_A"
grep -q "came back refused (policy-denied)" out/call-second.log \
  && ok "out of process, the unchained metered call is refused, not merely counted" || bad "it was not refused"
grep -q "came back unrefused" out/call.log \
  && ok "in process, the same call is only counted - the gap is declared, not hidden" || bad "gap not shown"

echo "1c. the enforcement points' own failure paths"
CHAIN_FAIL=1 ADAPTER=dryrun python3 call.py > out/call-fail.log 2>&1
check "an unreachable in-process chain exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"
grep -q "nothing was admitted and nothing ran" out/call-fail.log && ok "nothing was admitted" || bad "no such claim"
CHAIN_EDGE_DOWN=1 ADAPTER=second python3 call.py > out/call-down.log 2>&1
check "an unreachable admitting process exits 2" "$?" "2"
grep -q "a refusal, never a bypass" out/call-down.log \
  && ok "the second point's absence is a refusal, not a bypass" || bad "absence was not a refusal"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py units.py edge.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --min-units 100 --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 13/13" out/second.log && ok "13/13 cases on the out-of-process point" || bad "not 13/13"
AFTER_HASH=$(cat interface.py call.py conformance.py units.py edge.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
python3 conformance.py --adapter dryrun --adapter second --min-units 100 --report out/merged.json > out/merged.log 2>&1
check "both enforcement points in one merged run exit 0" "$?" "0"
grep -q "adapters_run=2" out/merged.log && ok "adapters_run=2" || bad "the merged run does not show two"
grep -q "identical chain records from 2 enforcement points" out/merged.log \
  && ok "identical chain records across the pair" || bad "the two points disagree on the records"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
merged = json.load(open("out/merged.json"))
axes = [("locus_of_traversal", "where the traversal runs"),
        ("processes_required_for_progress", "how many must be up for a unit to proceed"),
        ("reach_over_unmodified_workloads", "can it chain a workload it did not build")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:34} {str(before[axis]):58} {str(after[axis]):58} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test a library, not the placement"
assert before["adapter"] != after["adapter"], "both runs report the same enforcement point"
assert before["cases_passed"] == after["cases_passed"] == 13, "both points must pass the same cases"
assert before["records_digest"] == after["records_digest"], "the two points produced different chain records"
assert before["unchained_refused"] is False and after["unchained_refused"] is True, \
    "the pair does not differ on what happens to a unit that never entered the chain"
assert {r["adapters_run"] for r in merged} == {2}, "the merged report does not show adapters_run 2"
assert {r["binding_selected_by"] for r in merged} == {"configuration"}, "a point was not selected by configuration"
for r in merged:
    for count in ("slots_missing", "out_of_order", "missing_inverse", "ungated_metered_calls",
                  "chain_context_missing", "fail_open_slots"):
        assert r[count] == 0, f"{r['adapter']}: {count}={r[count]}"
    assert r["units_checked"] >= 100 and r["metered_units"] > 0, r["units_checked"]
    assert r["slots_noop_by_absent_owner"] == 592, r["slots_noop_by_absent_owner"]
print(f"axes_differing={len(differ)} records_digest={before['records_digest'][7:19]} "
      f"adapters_run=2 slots_noop_by_absent_owner=592")
PY
check "the two enforcement points differ on 3 or more axes" "$?" "0"
grep -q "axes_differing=3" out/axes.log && ok "3 axes differ (locus, processes required, reach)" || bad "$(tail -1 out/axes.log)"
grep -q "slots_noop_by_absent_owner=592" out/axes.log \
  && ok "592 slots recorded no-op by an absent owner, on both points, never passed" || bad "an absent owner was passed"

echo "3. no product name outside adapters/ and the env-var table"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: one door's intake path is unbound from the admission point"
rm -rf out/breakage && mkdir -p out/breakage
cp interface.py call.py conformance.py units.py edge.py out/breakage/
cp -r adapters out/breakage/adapters
python3 - <<'PY'
path = "out/breakage/interface.py"
src = open(path).read().replace(
    """        ctx = None
        try:""",
    """        ctx = None
        try:
            if unit.kind == "event":        # the breakage: this one door's intake
                adapter.meter(unit, None)   # path is no longer bound to the chain
                continue""")
open(path, "w").write(src)
PY
CHAIN_EXAMPLE_DIR="$EXAMPLE_DIR" python3 out/breakage/conformance.py --adapter dryrun --adapter second \
  --min-units 100 --report out/breakage.json > out/breakage.log 2>&1
check "the unbound-door run exits non-zero" "$?" "1"
python3 - <<'PY'
import json
broken = json.load(open("out/breakage.json"))
before = json.load(open("out/before.json"))
for r in broken:
    doors = r["by_door"]
    assert doors["event"]["chain_context_missing"] > 0, "the unbound door was not detected"
    assert doors["event"]["ungated_metered_calls"] > 0, "the unbound door's calls were not counted"
    for other in ("human", "schedule", "external"):
        assert doors[other]["chain_context_missing"] == 0, f"{other} was affected too"
        assert doors[other]["ungated_metered_calls"] == 0, f"{other} was affected too"
    assert r["units_checked"] >= 100, r["units_checked"]
    assert r["adapters_run"] == 2, r["adapters_run"]
    assert r["verdict"] == "fail", r["verdict"]
inproc, outproc = broken
assert inproc["metered_units"] > outproc["metered_units"], \
    "the out-of-process point did not refuse the calls the in-process one let through"
print(f"event: chain_context_missing={inproc['by_door']['event']['chain_context_missing']} "
      f"ungated_metered_calls={inproc['by_door']['event']['ungated_metered_calls']}; "
      f"human/schedule/external: 0 on both counts; units_checked={inproc['units_checked']} "
      f"adapters_run=2; unbound calls that still spent in process: "
      f"{inproc['metered_units'] - outproc['metered_units']}, refused out of process")
PY
check "the breakage names the one door that lost its binding" "$?" "0"
grep -q "FAIL one envelope through the human, event, schedule and external doors" out/breakage.log \
  && ok "the run names the case that broke it" || bad "case not named"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the enforcement points this host actually runs"
  if [ -z "${APPROVE_URL:-}" ]; then
    echo "  SKIP live mode: set APPROVE_URL and the slot endpoints (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --min-units 100 --report out/live.json > out/live.log 2>&1
    check "conformance against the host's points exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "the host binding passed the same 13 cases" || bad "the host binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs against the host's points" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
