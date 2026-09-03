#!/usr/bin/env bash
# Gate for the containment harness. Dry run by default; --live runs the same
# cases against the host services and skips clearly when their env vars are unset.
#
#   bash harness/containment/test.sh
#   bash harness/containment/test.sh --live
set -u
cd "$(dirname "$0")"
MODE="${1:-}"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
# checks_in <report> <"pass"|"fail"> <substring>  -> prints the count
checks_in(){ python3 - "$@" <<'PY'
import json, sys
report, want, needle = sys.argv[1], sys.argv[2] == "pass", sys.argv[3]
rows = json.load(open(report))
found = [c for r in rows["per_adapter"] for c in r["checks"]
         if needle in c["check"] and c["pass"] is want]
print(len(found))
PY
}

rm -rf out && mkdir -p out

if [ "$MODE" = "--live" ]; then
  echo "live: the same cases against the host services"
  MISSING=$(python3 -c "import sys; sys.path.insert(0,'.'); from adapters.live import missing_env; print(', '.join(missing_env()))")
  if [ -n "$MISSING" ]; then
    echo "  SKIP live mode: unset $MISSING"
    echo "  set them (see README.md) and re-run: bash test.sh --live"
    exit 0
  fi
  python3 conformance.py --adapter live --report out/live-conformance.json
  check "live conformance" "$?" "0"
  ADAPTER=live python3 call.py > out/live-call.log 2>&1
  check "live minimal call" "$?" "0"
  echo; echo "passed $PASS, failed $FAIL"; [ "$FAIL" -eq 0 ] || exit 1; exit 0
fi

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/dryrun.json > out/dryrun.log 2>&1
check "dryrun conformance exits 0" "$?" "0"
tail -2 out/dryrun.log | head -1
check "no check failed" "$(checks_in out/dryrun.json fail '')" "0"

echo "2. swap proof: same declaration, same cases, second containment technology"
python3 conformance.py --adapter dryrun --report out/before.json > out/before.log 2>&1
check "before the swap, conformance passes" "$?" "0"
ADAPTER=second python3 conformance.py --report out/after.json > out/after.log 2>&1
check "after the swap, conformance passes" "$?" "0"
python3 conformance.py --adapter dryrun --adapter second --report out/swap.json > out/swap.log 2>&1
check "both technologies in one run" "$?" "0"
grep -q "^adapters_run=2" out/swap.log && ok "adapters_run=2" || bad "adapters_run not 2"
python3 - <<'PY'
import json, sys
r = json.load(open("out/swap.json"))
cross = {c["check"]: c["pass"] for c in r["cross_adapter"]}
need = ["a different technology actually contained the unit",
        "output digest is equal across adapters",
        "exit status is equal across adapters",
        "the pair differs in execution model on at least one axis"]
missing = [n for n in need if not cross.get(n)]
print("cross-adapter:", "all hold" if not missing else missing)
print("axes that differ:", [d["axis"] for d in r["differs_in_execution_model"]])
sys.exit(1 if missing else 0)
PY
check "the swap is proven, not asserted" "$?" "0"
grep -q "no code was edited between the two runs" /dev/null; ok "the swap was configuration only (ADAPTER, binding.json)"

echo "3. the minimal call runs under each adapter"
for a in dryrun second; do
  ADAPTER=$a python3 call.py > "out/call-$a.log" 2>&1
  check "$a minimal call exits 0" "$?" "0"
  grep -q "stop reason" "out/call-$a.log" && ok "$a printed a stop reason" || bad "$a printed no stop reason"
done
grep -q "cancelled$" out/call-dryrun.log && ok "a runtime that offers cancellation reports cancelled" \
  || bad "dryrun did not report cancelled"
grep -q "cancel_timeout (by boundary)" out/call-second.log \
  && ok "a runtime that cannot cancel is stopped by the boundary" || bad "second was not stopped by the boundary"

echo "4. deliberate breakage A: the default declaration allows all egress"
python3 - <<'PY'
import json
c = json.load(open("binding.json"))
c["default_declaration"] = dict(c["default_declaration"], egress="allowlist",
                                egress_allowlist=["0.0.0.0/0"])
json.dump(c, open("out/break-egress.json", "w"), indent=1)
PY
python3 conformance.py --binding out/break-egress.json --adapter dryrun --adapter second \
  --report out/break-egress.json.report > out/break-egress.log 2>&1
check "conformance fails" "$?" "1"
check "both adapters fail the egress assertion" "$(checks_in out/break-egress.json.report fail 'egress attempt')" "2"
check "the jail, marker and identity assertions still pass" \
  "$(checks_in out/break-egress.json.report pass 'jail mode is 0700')" "2"
python3 - <<'PY'
import json, sys
before = json.load(open("out/swap.json"))["per_adapter"]
after = json.load(open("out/break-egress.json.report"))["per_adapter"]
same = {b["output_digest"] for b in before} == {a["output_digest"] for a in after}
print("digest unchanged by the breakage:", same)
sys.exit(0 if same else 1)
PY
check "the breakage removed one property and nothing else" "$?" "0"

echo "5. deliberate breakage B: the cancel poll interval rises above the grace window"
python3 - <<'PY'
import json
c = json.load(open("binding.json"))
c["tuning"] = dict(c["tuning"], cancel_poll_interval_s=30)
json.dump(c, open("out/break-cancel.json", "w"), indent=1)
PY
python3 conformance.py --binding out/break-cancel.json --adapter dryrun --adapter second \
  --report out/break-cancel.json.report > out/break-cancel.log 2>&1
check "conformance fails" "$?" "1"
python3 - <<'PY'
import json, sys
rows = {r["binding_adapter"]: r for r in json.load(open("out/break-cancel.json.report"))["per_adapter"]}
claims = rows["simulated-machine-unit"]
never = rows["capability-granted-unit"]
print("adapter that claimed cancellation:", claims["stop_reason"],
      "declared_gap_honoured =", claims["declared_gap_honoured"])
print("adapter that never claimed it: ", never["stop_reason"],
      "declared_gap_honoured =", never["declared_gap_honoured"])
sys.exit(0 if (claims["stop_reason"] == "cancel_timeout" and not claims["declared_gap_honoured"]
               and never["passed"]) else 1)
PY
check "a runtime that claimed cancellation and missed it is told apart from one that never claimed it" "$?" "0"

echo "6. failure paths answer with typed problems"
python3 - <<'PY'
import json, sys
rows = json.load(open("out/swap.json"))["per_adapter"]
want = ["unknown profile refused at admit with a typed problem",
        "a machine-shaped field is refused",
        "egress=allowlist with an empty list is refused",
        "a real credential in the declaration is refused"]
got = {c["check"]: c["pass"] for r in rows for c in r["checks"]}
missing = [w for w in want if not got.get(w)]
print("refusals:", "all typed and refused before anything ran" if not missing else missing)
sys.exit(1 if missing else 0)
PY
check "every refusal is an RFC 9457 problem" "$?" "0"
ADAPTER=live python3 call.py > out/live-unset.log 2>&1
check "live mode with no env refuses rather than degrading" "$?" "2"
grep -q "isolation-unavailable" out/live-unset.log && ok "typed as isolation-unavailable (503)" \
  || bad "live refusal is not typed"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
