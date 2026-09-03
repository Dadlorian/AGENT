#!/usr/bin/env bash
# Gate for the compensation harness. Everything here is measured, not claimed.
#   bash harness/xc-compensation/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/xc-compensation/test.sh --live   the same against the engine named in README, when its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run register (an engine-held step journal)"
python3 conformance.py --register dryrun --report out/before.json > out/dryrun.log 2>&1
check "25 cases and 11 assertions exit 0" "$?" "0"
grep -q "conformance PASSED: 25/25" out/dryrun.log && ok "25/25 cases passed" || bad "not 25/25"
grep -q "ways_in_covered=4" out/dryrun.log && ok "one corpus through all four entries of T6.2" || bad "not four entries"
grep -q "runs_killed=12 replayed=28 compensated=36" out/dryrun.log \
  && ok "12 runs killed; 28 replayed + 36 compensated = the 64 effects they had committed" \
  || bad "$(grep '^  register=' out/dryrun.log)"

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
check "declare five, commit four, fail the fifth, unwind: exits 0" "$?" "0"
grep -q "compensations_in_order=\['provision-the-workspace', 'open-the-incident-ticket', 'charge-the-card', 'reserve-the-inventory'\]" out/call-dryrun.log \
  && ok "the four compensations ran in reverse order" || bad "$(grep compensations_in_order out/call-dryrun.log)"
grep -q "inventory:sku-1188=0 balance:card-4242=0 tickets:open=0 workspaces:live=0" out/call-dryrun.log \
  && ok "every reversal observed in the world, not read off the record" || bad "the world is not back to zero"
grep -q '"type": "document-invalid", "status": 422' out/call-dryrun.log \
  && ok "an undeclared class and a missing compensating action are refused, 422" || bad "no 422"
grep -q '"type": "policy-denied", "status": 403' out/call-dryrun.log \
  && ok "an irreversible effect with no mandate is refused, 403" || bad "no 403"

echo "2. swap proof: the same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py driver.py store.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --register second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 25/25" out/second.log && ok "25/25 cases passed on the chained-log register" || bad "not 25/25"
AFTER_HASH=$(cat interface.py call.py conformance.py driver.py store.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second register" "$?" "0"
diff <(grep -E "^(unwind_order|compensations_in_order|cancelled_mid_flight_order)=" out/call-dryrun.log) \
     <(grep -E "^(unwind_order|compensations_in_order|cancelled_mid_flight_order)=" out/call-second.log) \
     > out/order.diff 2>&1
check "identical unwind order from both registers" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
b, a = before["binding_report"], after["binding_report"]
axes = [("where_the_register_lives", "who holds the record"),
        ("what_must_be_up_to_unwind", "what has to be running for a reverse walk"),
        ("what_drives_the_reverse_walk", "who walks it"),
        ("unwinds_from_cold_reader", "can a process that declared nothing unwind"),
        ("processes_required_for_progress", "how many processes must be up")]
differ = [k for k, _ in axes if b[k] != a[k]]
for axis, why in axes:
    print(f"{axis:32} {str(b[axis])[:34]:36} {str(a[axis])[:34]:36} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test a vendor, not the guarantee"
assert before["cases_passed"] == after["cases_passed"] == 25, "both registers must pass the same cases"
assert before["register_observed"] != after["register_observed"], "the register was read from the binding"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} "
      f"cases_after={after['cases_passed']} adapters_run={after['adapters_run']}")
PY
check "the two registers differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=5" out/axes.log && ok "5 declared axes differ, 3 of them xc-compensation-implement's own" \
  || bad "$(tail -1 out/axes.log)"

echo "3. deliberate breakage: on the second register only, write the record with the effect"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py call.py conformance.py driver.py store.py adapters out/breakage/
python3 - <<'PY'
# xc-compensation-implement's own definition_of_done breakage: "On the second
# register only, write the compensation record on the same append as the effect
# instead of on a strictly earlier one - leave the class vocabulary, the gate,
# the mandate check and the first register untouched."
path = "out/breakage/adapters/second.py"
src = open(path).read()
old = ('        row = self._append(self.log.head(), kind="declare", run_id=req.run_id,\n'
       '                           step_id=req.step_id, record=rec.dict())\n'
       '        rec.declared_at_head = row["hash"]        # durable now, before the effect\n'
       '        return rec\n')
assert old in src, "anchor block not found in _declare; second.py changed shape"
new = ('        return rec                                # BREAKAGE: nothing durable yet\n')
src = src.replace(old, new, 1)
old2 = ('        row = self._append(None, kind="seal", run_id=record.run_id, step_id=record.step_id,\n')
assert old2 in src, "anchor block not found in seal_effect"
new2 = ('        drow = self._append(None, kind="declare", run_id=record.run_id,   # BREAKAGE: the\n'
        '                            step_id=record.step_id, record=record.dict())  # record is written\n'
        '        record.declared_at_head = drow["hash"]                             # with the effect\n'
        '        row = self._append(None, kind="seal", run_id=record.run_id, step_id=record.step_id,\n')
open(path, "w").write(src.replace(old2, new2, 1))
PY
(cd out/breakage && python3 conformance.py --register second --report ../breakage-second.json) > out/breakage-second.log 2>&1
check "the broken register's conformance run exits 1" "$?" "1"
(cd out/breakage && python3 conformance.py --register dryrun --report ../breakage-dryrun.json) > out/breakage-dryrun.log 2>&1
FAILED_CASES=$(grep -c "^  FAIL" out/breakage-dryrun.log)
check "the first register fails nothing of its own" "$FAILED_CASES" "1"
grep -q "FAIL both registers walk one identical order" out/breakage-dryrun.log \
  && ok "its one failure is the cross-register order comparison, which walks the broken register" \
  || bad "the first register failed something of its own: $(grep -m1 '^  FAIL' out/breakage-dryrun.log)"
python3 - <<'PY' > out/breakage.log 2>&1
import json
broken = json.load(open("out/breakage-second.json"))
good = json.load(open("out/breakage-dryrun.json"))
print("broken second: " + " ".join(f"{k}={broken[k]}" for k in (
    "effects_checked", "undeclared_class_admitted", "records_after_effect",
    "runs_killed", "replayed", "compensated", "unwind_failed", "adapters_run")))
assert broken["records_after_effect"] > 0, "the ordering assertion did not notice"
assert broken["unwind_failed"] > 0, "the effects killed between the effect and its record were reversed anyway"
assert broken["undeclared_class_admitted"] == 0, "the class vocabulary was disturbed too"
assert broken["irreversible_without_mandate"] == 0, "the mandate gate was disturbed too"
assert broken["adapters_run"] == 2, "the broken run stopped exercising both registers"
assert good["records_after_effect"] == 0 and good["cases_passed"] == 24, "the first register broke too"
assert good["unwind_failed"] == 0, "the first register left effects unreversed too"
print(f"records_after_effect={broken['records_after_effect']} "
      f"unwind_failed={broken['unwind_failed']} first_register_own_cases_passed={good['cases_passed']}/24")
PY
check "one register fails, the other does not: the binding was tested, not the harness" "$?" "0"
grep -q "records_after_effect=" out/breakage.log && ok "$(tail -1 out/breakage.log)" || bad "$(tail -2 out/breakage.log)"

if [ "${1:-}" = "--live" ]; then
  echo "4. live: the durable-execution engine named in README's env-var table"
  if [ -z "${COMPENSATION_ADDR:-}" ]; then
    echo "  SKIP live mode: COMPENSATION_ADDR is unset, so there is no endpoint to reach."
    echo "  PASS.md A6 records that engine as installed with nothing listening (F-a6-02);"
    echo "  set COMPENSATION_ADDR and the rest of README's table to measure it. Nothing live was measured."
  else
    python3 conformance.py --register live --report out/live.json > out/live.log 2>&1
    check "conformance against the live register exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "the live register passed the same 25 cases" \
      || bad "live register: $(grep -m1 'adapter-unavailable' out/live.log)"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
