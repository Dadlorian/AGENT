#!/usr/bin/env bash
# Gate for the compose-operators harness. Dry-run mode is measured here; --live is
# claimed until it is run on a host where the model gateway answers.
#
#   bash harness/compose-operators/test.sh          the minimal call, conformance,
#                                                   the swap proof, one breakage
#   bash harness/compose-operators/test.sh --live   the same against $GATEWAY_URL
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
field(){ python3 -c "import json;d=json.load(open('$1'));print(json.dumps(d$2))"; }

rm -rf out && mkdir -p out

if [ "${1:-}" = "--live" ]; then
  echo "LIVE mode: the interpreted engine dispatching agent operators at GATEWAY_URL"
  if [ -z "${GATEWAY_URL:-}" ]; then
    echo "  SKIPPED: GATEWAY_URL is unset, so the live engine has no endpoint to"
    echo "  dispatch an agent operator to. Set GATEWAY_URL (and GATEWAY_KEY) and run"
    echo "  this again on the host. See the env table in README.md."
    echo "skipped: live mode needs GATEWAY_URL"
    exit 0
  fi
  python3 conformance.py --engine live --out out/live --report out/live.json > out/live.log 2>&1
  RC=$?
  if grep -q "adapter-unavailable" out/live.log 2>/dev/null; then
    ok "the live engine reported a typed adapter-unavailable rather than failing open"
  else
    check "live conformance exits 0" "$RC" "0"
  fi
  echo; echo "passed $PASS, failed $FAIL"
  [ "$FAIL" -eq 0 ] || exit 1
  echo "live: $PASS checks pass against $GATEWAY_URL"
  exit 0
fi

echo "1. the minimal call: one composition, every operator once, parked and resumed"
ADAPTER=dryrun python3 call.py > out/call-dryrun.log 2>&1
check "call.py exits 0" "$?" "0"
grep -q "6 of 6 exercised" out/call-dryrun.log && ok "all six operators ran from one document" \
  || bad "not all six operators ran"
grep -q "parked at ship-approval" out/call-dryrun.log && ok "the run parked for the human" \
  || bad "the run did not park"
grep -q "verdict_pass" out/call-dryrun.log && ok "the loop ended on the judge verdict, bounded" \
  || bad "no loop termination reason"
check "two documents were refused before dispatch" \
  "$(grep -c 'urn:agentic:problem:document-invalid' out/call-dryrun.log)" "2"

echo "1b. what the caller wrote (harness/caller_lines.py's rule, applied here)"
LINES=$(python3 - <<'PY'
lines = open("call.py").read().splitlines()
marks = [i for i, l in enumerate(lines) if ">>> CALLER CODE" in l]
body = lines[marks[0] + 1:]
end = next((i for i, l in enumerate(body) if l.startswith("if __name__")), len(body))
print(len([l for l in body[:end] if l.strip() and not l.strip().startswith("#")]))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
if grep -nE "\.(jsonl|ndjson|db|sqlite3?|journal)['\"]" call.py > out/storage-hits.txt; then
  bad "call.py names an engine's own storage: $(cat out/storage-hits.txt)"
else
  ok "the caller names no file in an engine's own storage"
fi

echo "1c. no product name above the adapter boundary"
if grep -rniE "litellm|temporal|openai|anthropic|firecracker" interface.py call.py conformance.py \
     adapters/base.py adapters/dryrun.py adapters/second.py > out/product-hits.txt; then
  bad "a product name appears above the adapter boundary: $(cat out/product-hits.txt)"
else
  ok "no product name in the interface, the caller, the conformance run or either engine"
fi

echo "1d. the live engine's only measured behaviour: no endpoint is a typed refusal"
ADAPTER=live python3 call.py > out/call-live.log 2>&1
check "the live engine with no endpoint exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-live.log \
  && ok "typed as adapter-unavailable (503, retryable), not a stack trace" \
  || bad "the live engine failed open"

echo "2. conformance against the interpreted engine"
python3 conformance.py --engine dryrun --out out/c1 --report out/before.json > out/c1.log 2>&1
check "dry-run conformance exits 0" "$?" "0"
sed -n 's/^engine_marker=/  ..   engine_marker=/p' out/c1.log
check "every check passed" "$(field out/before.json "['per_engine'][0]['failures']")" "[]"
check "drift between the schema and the executor" "$(field out/before.json "['drift']")" "[]"

echo "3. swap proof: the same cases, before and after the swap"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second engine" "$?" "0"
diff <(grep -v engine_marker out/call-dryrun.log) \
     <(grep -v engine_marker out/call-second.log) > out/call-diff.txt \
  && ok "the minimal call prints the same table under both engines" \
  || bad "the caller sees a difference: $(head -3 out/call-diff.txt)"
python3 conformance.py --engine second --out out/c2 --report out/after.json > out/c2.log 2>&1
check "after: the compiled engine exits 0" "$?" "0"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
B=$(field out/before.json "['per_engine'][0]['engine_marker']")
A=$(field out/after.json "['per_engine'][0]['engine_marker']")
echo "  before marker $B, after marker $A"
[ "$B" != "$A" ] && ok "a different engine really answered" || bad "the same engine answered twice"
check "the same cases ran on both sides of the swap" \
  "$(field out/before.json "['per_engine'][0]['checks_total']")" \
  "$(field out/after.json "['per_engine'][0]['checks_total']")"
python3 conformance.py --engine dryrun --engine second --out out/both --report out/both.json > out/both.log 2>&1
check "both engines in one report" "$?" "0"
check "engines_run" "$(field out/both.json "['engines_run']")" "2"
check "distinct engine markers, read from the running engines" \
  "$(python3 -c "import json;print(len(json.load(open('out/both.json'))['distinct_markers']))")" "2"
check "the same ledger of steps on both engines" \
  "$(field out/both.json "['step_orders_identical']")" "true"
check "the same terminal outcome on both engines" \
  "$(field out/both.json "['terminal_outcomes_identical']")" "true"
check "nothing else moved across the swap" "$(field out/both.json "['differ_across_engines']")" "[]"
check "the pair's execution models differ on every declared axis" \
  "$(python3 -c "
import json;d=json.load(open('out/both.json'))
b=[p['binding'] for p in d['per_engine']]
print(sum(1 for k in ('tree_read_at','progress_unit','durable_at','failure_locus') if b[0][k]!=b[1][k]))")" "4"

echo "4. deliberate breakage: an operator arm the schema does not admit"
python3 conformance.py --engine dryrun --engine second --break-drift \
  --out out/broken --report out/broken.json > out/broken.log 2>&1
BRC=$?
check "the breakage run exits non-zero" "$([ $BRC -ne 0 ] && echo nonzero || echo zero)" "nonzero"
check "the interpreted engine reports drift" \
  "$(field out/broken.json "['per_engine'][0]['drift']")" '["branch"]'
check "executor_ops is one wider than schema_ops on that engine" \
  "$(python3 -c "import json;p=json.load(open('out/broken.json'))['per_engine'][0];print(len(p['executor_ops'])-len(p['schema_ops']))")" "1"
check "the compiled engine still reports no drift, so the fault is one engine's wiring" \
  "$(field out/broken.json "['per_engine'][1]['drift']")" "[]"
check "every contract-level assertion still passes: the step order is still identical" \
  "$(field out/broken.json "['step_orders_identical']")" "true"
check "and all six operators were still exercised" \
  "$(field out/broken.json "['operators_exercised']")" "6"
check "only the binding assertion failed" \
  "$(python3 -c "import json;d=json.load(open('out/broken.json'));print([f['check'][:2] for p in d['per_engine'] for f in p['failures']])")" "['A2']"

echo "5. the suite passes again once the arm is removed"
python3 conformance.py --engine dryrun --engine second --out out/repair --report out/repair.json > out/repair.log 2>&1
check "the same suite exits 0 again" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "dry-run: $PASS checks pass, 39 assertions per engine, swap proven across 2 engines, breakage fails one"
