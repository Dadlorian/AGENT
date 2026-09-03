#!/usr/bin/env bash
# Dry-run gate for the reference example. Everything here is measured, not claimed.
# Checks: four entries run clean, the ledger chain verifies (and can fail),
# budget enforcement trips at plan time and mid-run, a replay is a no-op,
# and a malformed envelope returns RFC 9457 problem details.
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out
L=out/ledger.jsonl

echo "1. four entries, dry run, same workflow"
for e in human event schedule external; do
  python3 run.py --entry "entries/$e.json" > "out/$e.log" 2>&1
  check "$e exits 0" "$?" "0"
  grep -q "^completed:" "out/$e.log" && ok "$e reached completed" || bad "$e did not complete"
done
grep -q "fail" out/human.log && grep -q "pass" out/human.log \
  && ok "loop ran again after a judge fail, then passed" || bad "judge loop did not fail-then-pass"
grep -qi "criterion" out/human.log && bad "criterion text leaked into caller output" \
  || ok "criterion never appears in what the agent or caller sees"

echo "1b. the other two documents validate with the same validator"
python3 - <<'PY' > out/schemas.log 2>&1
import json, sys
sys.path.insert(0, ".")
from run import validate
bad = 0
for doc, sch in (("agents.json", "schemas/agent-profile.schema.json"),
                 ("workflows/triage-and-fix.json", "schemas/workflow.schema.json")):
    errs = validate(json.load(open(doc)), json.load(open(sch)))
    print(doc, errs or "valid")
    bad += len(errs)
sys.exit(1 if bad else 0)
PY
check "agent registry and workflow validate" "$?" "0"

echo "1c. the approval step's conditional requirement is enforced, not just described"
python3 - <<'PYA' > out/approval.log 2>&1
import copy, json, sys
sys.path.insert(0, ".")
from run import validate
sch = json.load(open("schemas/workflow.schema.json"))
app = sch["$defs"]["approval"]
wf = json.load(open("workflows/triage-and-fix.json"))
def steps(o):
    if isinstance(o, dict):
        if o.get("op") == "approval":
            yield o
        for v in o.values():
            yield from steps(v)
    elif isinstance(o, list):
        for v in o:
            yield from steps(v)
good = next(steps(wf))
assert not validate(good, app, sch), "shipped approval step should validate"
bad = copy.deepcopy(good); del bad["return_to_step_id"]
errs = validate(bad, app, sch)
assert any("return_to_step_id" in e for e in errs), f"return_with_notes without return_to_step_id was accepted: {errs}"
ok = copy.deepcopy(bad); ok["decisions"] = [d for d in ok["decisions"] if d != "return_with_notes"]
assert not validate(ok, app, sch), "return_to_step_id must not be required without return_with_notes"
print("enforced:", errs)
PYA
check "return_with_notes without return_to_step_id is rejected" "$?" "0"

echo "2. ledger"
LINES=$(wc -l < "$L")
python3 run.py --verify-ledger > out/verify.log 2>&1
check "chain verifies" "$?" "0"
[ "$LINES" -ge 40 ] && ok "$LINES records written" || bad "only $LINES records"
sed '5s/"cost_micros": [0-9]*/"cost_micros": 1/' "$L" > out/tampered.jsonl
python3 run.py --verify-ledger --ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a tampered ledger is detected" "$?" "2"

echo "3. idempotent replay is a no-op"
python3 run.py --entry entries/human.json > out/replay.log 2>&1
check "replay exits 0" "$?" "0"
grep -q "^REPLAY:" out/replay.log && ok "replay recognised" || bad "replay not recognised"
check "no records appended" "$(wc -l < "$L")" "$LINES"

echo "4. budget enforcement (deliberate breakage)"
python3 run.py --entry entries/human.json --budget-micros 50000 --ledger out/low.jsonl > out/low.log 2>&1
check "ceiling below the plan floor exits 2" "$?" "2"
grep -q "budget-exhausted" out/low.log && ok "typed as budget-exhausted (402)" || bad "not typed"
grep -q "refused before execution" out/low.log && ok "refused before any step ran" || bad "ran anyway"
grep -q "agent-called" out/low.jsonl 2>/dev/null && bad "a step was dispatched anyway" || ok "no dispatch in the ledger"
python3 run.py --entry entries/human.json --budget-micros 400000 --ledger out/mid.jsonl > out/mid.log 2>&1
check "ceiling that runs dry mid-loop exits 2" "$?" "2"
grep -q '"step_id": "fix#2"' out/mid.log && ok "tripped at the step that would cross it" || bad "wrong step"

echo "5. malformed envelope"
python3 - <<'PY'
import json
e = json.load(open("entries/human.json"))
del e["budget"]; e["kind"] = "telepathy"
json.dump(e, open("out/malformed.json", "w"))
PY
python3 run.py --entry out/malformed.json --ledger out/bad.jsonl > out/bad.log 2>&1
check "malformed envelope exits 2" "$?" "2"
grep -q "application/problem+json" out/bad.log && ok "answer is problem details" || bad "not problem details"
grep -q "document-invalid" out/bad.log && ok "typed as document-invalid (422)" || bad "not typed"
grep -q "missing required property 'budget'" out/bad.log && ok "names the missing field" || bad "field not named"
[ -f out/bad.jsonl ] && bad "an invalid envelope wrote to a ledger" || ok "nothing written for an invalid envelope"

echo "6. ledger still verifies after everything"
python3 run.py --verify-ledger > /dev/null 2>&1
check "final chain verifies" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
