#!/usr/bin/env bash
# Gate for the xc-tenancy harness. Everything here is measured, not claimed.
#   bash harness/xc-tenancy/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/xc-tenancy/test.sh --live   the same against the budget-key component, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "9 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 9/9" out/dryrun.log && ok "9/9 cases passed" || bad "not 9/9"
grep -q "principals_covered=2 no_principal_admitted=0 cross_tenant_reads=0 cross_tenant_recalls=0 cross_tenant_spend=0" \
  out/dryrun.log && ok "the definition-of-done counters hold: 2 principals covered, zero of every leak" \
  || bad "the definition-of-done counters did not hold"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 -c "import sys; sys.path.insert(0, '..'); import caller_lines; print(caller_lines.count('xc-tenancy'))")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 -c "
import sys; sys.path.insert(0, '..'); import caller_lines
hits = caller_lines.storage_hits('xc-tenancy')
print(*[f'xc-tenancy/call.py:{n}: {line}' for n, line in hits], sep='\n')
sys.exit(1 if hits else 0)" \
  && ok "the caller names no file in the adapter's own storage" \
  || bad "call.py reads the adapter's storage by path"
python3 call.py > out/call.log 2>&1
check "the minimal call's five steps exit 2 (two of the five are deliberate refusals)" "$?" "2"
grep -q "read-own .*tenant-northwind .*northwind's record .*ok" out/call.log \
  && ok "a write and a read under tenant A are scoped to A" || bad "the own-tenant read did not show A's value"
grep -q "spend .*tenant-northwind .*498800 .*ok" out/call.log && ok "spend is scoped to A" || bad "spend not scoped"
grep -q "cross-tenant-denied" out/call.log && ok "a read across to tenant B is refused, typed cross-tenant-denied" \
  || bad "the cross-tenant read was not refused"
grep -q "no-principal" out/call.log && ok "a unit with no tenant is refused at entry, typed no-principal" \
  || bad "the no-principal unit was not refused"
grep -q "scoping_decisions_agree=true" out/call.log && ok "the demo's own steps agree with themselves" \
  || bad "steps disagreed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 9/9" out/second.log && ok "9/9 cases passed on the second adapter" || bad "not 9/9"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "2"
ADAPTER=dryrun,second python3 call.py > out/call-both.log 2>&1
check "both enforcement points answer the same question" "$?" "2"
grep -q "scoping_decisions_agree=true" out/call-both.log \
  && ok "identical scoping decisions from both enforcement points, at every step" \
  || bad "the two adapters disagreed on at least one step"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("locus_of_the_tenant_boundary", "where the boundary is enforced"),
        ("failure_mode_of_a_wrong_or_missing_principal", "what a wrong or missing principal does"),
        ("provisioning_cost_of_a_new_principal", "what a new principal costs to provision")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:46} {str(before[axis])[:40]:42} {str(after[axis])[:40]:42} ({why})")
assert len(differ) == 3, f"only {len(differ)} of 3 axes differ; the swap would test configuration, not the boundary"
bcard, acard = before["tenancy_conformance_report"], after["tenancy_conformance_report"]
assert {bcard["adapter"], acard["adapter"]} == {"shared-keyspace-principal-column", "database-per-tenant"}, (bcard, acard)
for card in (bcard, acard):
    assert card["selected_by"] == "configuration", card
    assert card["principals_covered"] >= 2, card
    assert card["no_principal_admitted"] == 0, card
    assert card["cross_tenant_reads"] == card["cross_tenant_recalls"] == card["cross_tenant_spend"] == 0, card
print(f"axes_differing={len(differ)} adapters_run={bcard['adapters_run'] + acard['adapters_run']} "
      f"selected_by=configuration")
PY
check "the two adapters differ in execution model on all 3 named axes, both zero on every leak" "$?" "0"
grep -q "axes_differing=3" out/axes.log && ok "3 axes differ: locus, failure mode, provisioning cost" \
  || bad "$(tail -1 out/axes.log)"
grep -q "adapters_run=2 selected_by=configuration" out/axes.log && ok "adapters_run=2, selected_by=configuration" \
  || bad "the swap was not by configuration"

echo "3. no product name outside adapters/live.py"
python3 - <<'PY' > out/scan.log 2>&1
import os, re
PRODUCTS = re.compile(r"\b(litellm|firecracker|goose|temporal|langfuse|opentelemetry)\b", re.I)
hits = []
for dirpath, dirnames, filenames in os.walk("."):
    dirnames[:] = [d for d in dirnames if d not in ("out", "__pycache__")]
    for name in sorted(filenames):
        if not name.endswith((".py", ".sh")) or dirpath.endswith("adapters") and name == "live.py":
            continue
        path = os.path.join(dirpath, name)
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            found = PRODUCTS.search(line)
            if found and "PRODUCTS = re.compile" not in line:
                hits.append(f"{path}:{i}: {found.group(0)}")
print("\n".join(hits) or "no product name outside adapters/live.py")
print(f"product_hits={len(hits)}")
PY
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/live.py" || bad "a product name leaked"

echo "4. deliberate breakage: the shared-keyspace filter dropped, on one adapter's read path only"
rm -rf out/breakage && mkdir -p out/breakage
cp -r interface.py call.py conformance.py adapters out/breakage/
python3 - <<'PY'
path = "out/breakage/adapters/dryrun.py"
src = open(path).read()
before = src
src = src.replace(
    '''        if rec["principal"] != principal:            # the filter: the line the breakage removes
            raise Problem("cross-tenant-denied",
                          f"key {key!r} belongs to a different principal than the requesting actor",
                          key=key, rule_id="tenancy-scope")
        return rec["value"]''',
    '''        return rec["value"]''')
src = src.replace(
    '''        if target_principal != principal:             # the filter: the line the breakage removes
            raise Problem("cross-tenant-denied",
                          f"a spend by {principal!r} named a different target principal {target_principal!r}",
                          rule_id="tenancy-scope")
        balance''',
    '''        balance''')
src = src.replace(
    'return sorted(key for key, rec in self._store.items() if rec["principal"] == principal)',
    'return sorted(self._store.keys())')
assert src != before, "no replacement matched; the breakage patched nothing"
open(path, "w").write(src)
PY
check "the patch matched real source lines" "$?" "0"
python3 out/breakage/conformance.py --adapter dryrun --report out/breakage-a.json > out/breakage.log 2>&1
check "the breakage run exits non-zero on the adapter that lost the filter" "$?" "1"
grep -q "conformance FAILED: 6/9" out/breakage.log && ok "6/9 cases pass; the 3 cross-tenant cases fail" \
  || bad "$(tail -1 out/breakage.log)"
python3 - <<'PY' > out/breakage-counters.log 2>&1
import json
green = json.load(open("out/before.json"))["tenancy_conformance_report"]
broken = json.load(open("out/breakage-a.json"))["tenancy_conformance_report"]
assert green["cross_tenant_reads"] == green["cross_tenant_recalls"] == green["cross_tenant_spend"] == 0, green
assert broken["cross_tenant_reads"] > 0 and broken["cross_tenant_recalls"] > 0 and broken["cross_tenant_spend"] > 0, broken
print(f"cross_tenant_reads 0 -> {broken['cross_tenant_reads']}, "
      f"cross_tenant_recalls 0 -> {broken['cross_tenant_recalls']}, "
      f"cross_tenant_spend 0 -> {broken['cross_tenant_spend']}")
PY
check "every leak counter inverted from zero" "$?" "0"
ok "$(cat out/breakage-counters.log)"
python3 out/breakage/conformance.py --adapter second --report out/breakage-b.json > out/breakage-second.log 2>&1
check "the untouched second adapter still exits 0" "$?" "0"
grep -q "conformance PASSED: 9/9" out/breakage-second.log && ok "singling out one adapter: the other is still 9/9" \
  || bad "both adapters failed"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the per-group virtual-key budget cap on this host"
  if [ -z "${TENANCY_BUDGET_URL:-}" ]; then
    echo "  SKIP live mode: set TENANCY_BUDGET_URL and TENANCY_BUDGET_TOKEN (see README.md). Nothing live was measured."
  else
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
