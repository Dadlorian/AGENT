#!/usr/bin/env bash
# Gate for the policy harness. Everything here is measured, not claimed.
#   bash harness/policy/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/policy/test.sh --live   the same against the policy engine on this host, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "14 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 14/14" out/dryrun.log && ok "14/14 cases passed" || bad "not 14/14"
grep -q "decided_before_first_metered_call=9 spend_delta_micros=0 rule_id_present=True" out/dryrun.log \
  && ok "every decision preceded the first metered call, no denied dispatch spent, every decision names a rule" \
  || bad "the definition-of-done counters did not hold"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 -c "import sys; sys.path.insert(0, '..'); import caller_lines; print(caller_lines.count('policy'))")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 -c "
import sys; sys.path.insert(0, '..'); import caller_lines
hits = caller_lines.storage_hits('policy')
print(*[f'policy/call.py:{n}: {line}' for n, line in hits], sep='\n')
sys.exit(1 if hits else 0)" \
  && ok "the caller names no file in the adapter's own storage" \
  || bad "call.py reads the adapter's storage by path"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "one decision for one unit of work exits 0" "$?" "0"
grep -q "allow-internal-tool-call" out/call.log && ok "an allow that names the rule that permitted it" || bad "no rule_id on the allow"
grep -q "unit of work ran" out/call.log && ok "the work ran on the far side of the allow" || bad "the work did not run"
SCOPE=external python3 call.py > out/call-deny.log 2>&1
check "a denied action exits 2" "$?" "2"
grep -q "policy-denied" out/call-deny.log && ok "typed as policy-denied (403)" || bad "not typed"
grep -q '"spend_delta_micros": 0' out/call-deny.log && ok "the deny cost nothing" || bad "the deny spent"
grep -q "deny-external-tool-without-mandate" out/call-deny.log && ok "the deny names the rule that fired" || bad "no rule_id"
SCOPE=external MANDATE=1 python3 call.py > out/call-mandate.log 2>&1
check "the same action under a mandate exits 0" "$?" "0"
DECLINE=1 python3 call.py > out/call-decline.log 2>&1
check "a caller trying to decline the gate exits 2" "$?" "2"
grep -q "document-invalid" out/call-decline.log && ok "typed as document-invalid (422)" || bad "not typed"
grep -q "no bypass on this path" out/call-decline.log && ok "there is no advisory mode and no bypass field" || bad "bypass not refused by vocabulary"
RESOURCE_TENANT=tenant-other python3 call.py > out/call-tenant.log 2>&1
check "a cross-tenant resource exits 2" "$?" "2"
grep -q "deny-cross-tenant-resource" out/call-tenant.log && ok "denied by the tenancy rule" || bad "not denied"

echo "1c. the dry-run adapter's own failure path"
POLICY_FAIL=1 python3 call.py > out/call-fail.log 2>&1
check "an unreachable decision endpoint exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"
grep -q "was not admitted" out/call-fail.log && ok "no decision, no admission" || bad "not refused"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py bundle.json decision_points.json | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 14/14" out/second.log && ok "14/14 cases passed on the second adapter" || bad "not 14/14"
AFTER_HASH=$(cat interface.py call.py conformance.py bundle.json decision_points.json | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
ADAPTER=dryrun,second python3 call.py > out/call-both.log 2>&1
check "both engines answer the same question" "$?" "0"
grep -q "decisions_agree=true" out/call-both.log && ok "the same effect and the same rule from both" || bad "the two engines disagreed"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("decision_model", "what the engine reads"),
        ("activation_model", "how a new rule set starts serving"),
        ("processes_required", "what must be reachable to decide at all"),
        ("conformance_subset", "what it declares it cannot serve")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:20} {str(before[axis])[:46]:48} {str(after[axis])[:46]:48} ({why})")
shared = set(before["decisions"]) & set(after["decisions"])
disagree = [d for d in shared if before["decisions"][d] != after["decisions"][d]]
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert not disagree, f"the two engines disagreed on {len(disagree)} decisions: {disagree[:2]}"
assert len(shared) >= 5, f"only {len(shared)} decisions were asked of both"
assert before["marker"] != after["marker"], "the marker did not change with the binding"
cards = [before["policy_conformance_report"], after["policy_conformance_report"]]
assert {c["adapter"] for c in cards} == {"out-of-process-document-query", "in-process-typed-entity"}, cards
for card in cards:
    assert card["selected_by"] == "configuration", card
    assert card["spend_delta_micros"] == 0 and card["rule_id_present"], card
    assert card["decided_before_first_metered_call"] == card["decisions_taken"], card
print(f"axes_differing={len(differ)} decisions_agree=true shared_decisions={len(shared)} "
      f"adapters_run={sum(c['adapters_run'] for c in cards)} selected_by=configuration")
PY
check "the two adapters differ in execution model on 3 or more axes and agree on every shared decision" "$?" "0"
grep -q "axes_differing=4 decisions_agree=true" out/axes.log && ok "4 axes differ, both engines agreed on every decision asked of both" \
  || bad "$(tail -1 out/axes.log)"
grep -q "adapters_run=2 selected_by=configuration" out/axes.log && ok "adapters_run=2, selected_by=configuration" || bad "the swap was not by configuration"

echo "3. no engine, rule-language or vendor name outside adapters/"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "engine names leaked"

echo "4. deliberate breakage: the decision moved after the first metered call, on one adapter only"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py call.py conformance.py bundle.json decision_points.json adapters out/breakage/
python3 - <<'PY'
path = "out/breakage/adapters/dryrun.py"
src = open(path).read().replace(
    "\n\n# The one name every adapter module exports",
    '''
    def admit(self, request, work):            # the breakage: decide moved after the first metered call
        outcome = work(self.meter)
        decision = self.decide(request)
        if decision.effect == "deny":
            raise Problem("policy-denied", decision.problem["detail"], rule_id=decision.rule_id,
                          spend_delta_micros=self.meter.spend(request.context["root_dispatch_id"]))
        return decision, outcome


# The one name every adapter module exports''')
open(path, "w").write(src)
PY
python3 out/breakage/conformance.py --adapter dryrun --report out/breakage-a.json > out/breakage.log 2>&1
check "the breakage run exits non-zero on the adapter that lost the ordering" "$?" "1"
python3 - <<'PY' > out/breakage-counters.log 2>&1
import json
green = json.load(open("out/before.json"))["policy_conformance_report"]
broken = json.load(open("out/breakage-a.json"))["policy_conformance_report"]
assert green["decided_before_first_metered_call"] == green["decisions_taken"], green
assert broken["decided_before_first_metered_call"] < broken["decisions_taken"], broken
assert green["spend_delta_micros"] == 0 and broken["spend_delta_micros"] > 0, (green, broken)
print(f"decided_before_first_metered_call {green['decided_before_first_metered_call']}/"
      f"{green['decisions_taken']} -> {broken['decided_before_first_metered_call']}/"
      f"{broken['decisions_taken']}, spend_delta_micros on denied dispatches "
      f"{green['spend_delta_micros']} -> {broken['spend_delta_micros']}")
PY
check "the ordering and zero-spend counters inverted" "$?" "0"
ok "$(cat out/breakage-counters.log)"
grep -q "the binding overrides admit" out/breakage.log && ok "the run names what broke: the binding took over the gate" || bad "the override is not named"
python3 out/breakage/conformance.py --adapter second --report out/breakage-b.json > out/breakage-second.log 2>&1
check "the untouched adapter still exits 0" "$?" "0"
grep -q "conformance PASSED: 14/14" out/breakage-second.log && ok "singling out one adapter: the other is still 14/14" || bad "both adapters failed"

echo "5. concern-policy-q3: work resumed after a pause, queue or restart is decided again"
python3 resume.py > out/resume.log 2>&1
check "the resume check exits 0" "$?" "0"
grep -q "RESUME_CHECK PASSED" out/resume.log && ok "8/8 resume assertions passed" || bad "resume check did not pass"
grep -q "post_resume=denied:deny-tool-call-after-policy-change" out/resume.log \
  && ok "the rule changed mid-interval governed the resumed work, not the rule in force at admission" \
  || bad "the resumed work was not decided under the changed rule"
POLICY_TRUST_STALE_DECISION=1 python3 resume.py > out/resume-breakage.log 2>&1
check "the breakage (trusting the pre-pause decision) exits non-zero" "$?" "1"
grep -q "RESUME_CHECK FAILED" out/resume-breakage.log && ok "the breakage is caught, not silently green" || bad "the breakage passed"
grep -q "work_ran=True" out/resume-breakage.log \
  && ok "under the breakage the resumed work ran on a stale decision, which is exactly the defect this check exists to catch" \
  || bad "the breakage did not reproduce the defect"
python3 resume.py > out/resume-restored.log 2>&1
check "the property holds again after the breakage run (no state carried over)" "$?" "0"

if [ "${1:-}" = "--live" ]; then
  echo "6. live: the policy engine on this host"
  if [ -z "${POLICY_DECISION_URL:-}" ]; then
    echo "  SKIP live mode: set POLICY_DECISION_URL (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live engine exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed the same 14 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
