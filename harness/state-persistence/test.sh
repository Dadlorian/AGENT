#!/usr/bin/env bash
# Gate for the state-persistence harness. Everything here is measured, not claimed.
#   bash harness/state-persistence/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/state-persistence/test.sh --live   the same against this repo's ledger, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "11 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 11/11" out/dryrun.log && ok "11/11 cases passed" || bad "not 11/11"

echo "1b. the minimal call a caller writes (harness/caller_lines.py-style count)"
LINES=$(python3 - <<'PY'
lines = open("call.py").read().splitlines()
marks = [i for i, l in enumerate(lines) if ">>> CALLER CODE" in l]
body = lines[marks[0] + 1:]
end = next((i for i, l in enumerate(body) if l.startswith("if __name__")), len(body))
print(len([l for l in body[:end] if l.strip() and not l.strip().startswith("#")]))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
! grep -nE "\.(jsonl|ndjson|db|sqlite3?|journal)['\"]" call.py > /tmp/state_storage_hits.$$ \
  && ok "the caller names no file in an adapter's own storage" \
  || bad "call.py names adapter storage: $(cat /tmp/state_storage_hits.$$)"
rm -f /tmp/state_storage_hits.$$
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "the minimal call exits 0" "$?" "0"
grep -q "True.*True" out/call.log && ok "the caller read a verified proof and no fork" || bad "call.py did not report both true"

echo "1c. the dry-run adapter's own failure path"
DRYRUN_FAIL=1 ADAPTER=dryrun python3 call.py > out/call-fail.log 2>&1
check "an unreachable store exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py verify_external.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 11/11" out/second.log && ok "11/11 cases passed on the second adapter" || bad "not 11/11"
AFTER_HASH=$(cat interface.py call.py conformance.py verify_external.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("execution_model", "the write model and where order comes from"),
        ("adapter", "which entity answered"),
        ("marker", "the binding's own marker, read from its response"),
        ("declared_gaps", "what this binding admits it cannot do")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:16} {str(before[axis])[:40]:40} {str(after[axis])[:40]:40} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 11, "both bindings must pass the same cases"
assert before["marker"] != after["marker"], "the marker did not change with the binding"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=4" out/axes.log && ok "4 axes differ (execution model, entity, marker, declared gaps)" \
  || bad "$(tail -1 out/axes.log)"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: one record body edited in place in the store"
rm -rf out/breakage && mkdir -p out/breakage
OBJSTORE_DIR="$(pwd)/out/breakage/objectstore" python3 - <<'PY' > out/breakage-setup.log 2>&1
import sys
sys.path.insert(0, ".")
from interface import AppendRequest
from adapters.second import ObjectStoreAdapter
a = ObjectStoreAdapter()
partition = "breakage-demo"
head = a.resolve_head(partition)
for i in range(5):
    head = a.append(AppendRequest.from_dict(
        {"partition": partition, "kind": "probe", "body": {"n": i},
         "fencing_token": head.size + 1,
         "expected_head": head.chain_digest if head.size else None}))[1]
print("appended", head.size, "records, head", head.chain_digest)
PY
cat out/breakage-setup.log
python3 - <<'PY' > out/breakage-before.json
import sys, json
sys.path.insert(0, ".")
import os
os.environ["OBJSTORE_DIR"] = os.path.join(os.getcwd(), "out", "breakage", "objectstore")
from adapters.second import ObjectStoreAdapter
a = ObjectStoreAdapter()
partition = "breakage-demo"
head = a.resolve_head(partition)
docs = [{"record_id": r.record_id, "kind": r.kind, "partition": r.partition, "body": r.body}
        for r in a.read_at(partition, head)]
json.dump(docs, sys.stdout)
PY
python3 verify_external.py < out/breakage-before.json > out/breakage-before-report.json
grep -q '"chain_break_at": -1' out/breakage-before-report.json \
  && ok "before tampering: chain_break_at is -1" || bad "the untampered log already reports a break"

# Tamper one object's body in place. record_id (the filename and the tree leaf) is left untouched -
# exactly the breakage the definition of done names: the file changed, its claimed identity did not.
OBJ_DIR="out/breakage/objectstore/breakage-demo/objects"
OBJ_FILE=$(ls "$OBJ_DIR" | sort | sed -n '3p')
python3 - "$OBJ_DIR/$OBJ_FILE" <<'PY'
import json, sys
path = sys.argv[1]
doc = json.load(open(path))
doc["body"] = {"n": "TAMPERED"}
json.dump(doc, open(path, "w"), sort_keys=True)
PY
ok "tampered $OBJ_FILE in place, record_id unchanged"

python3 - <<'PY' > out/breakage-after.json
import sys, json, os
sys.path.insert(0, ".")
os.environ["OBJSTORE_DIR"] = os.path.join(os.getcwd(), "out", "breakage", "objectstore")
from adapters.second import ObjectStoreAdapter
a = ObjectStoreAdapter()
partition = "breakage-demo"
head = a.resolve_head(partition)
docs = [{"record_id": r.record_id, "kind": r.kind, "partition": r.partition, "body": r.body}
        for r in a.read_at(partition, head)]
json.dump(docs, sys.stdout)
PY
python3 verify_external.py < out/breakage-after.json > out/breakage-after-report.json
cat out/breakage-after-report.json
python3 - <<'PY'
import json
report = json.load(open("out/breakage-after-report.json"))
assert report["chain_break_at"] == 2, report
print("chain_break_at =", report["chain_break_at"])
PY
check "the tampered run reports the edited index" "$?" "0"
grep -q '"chain_break_at": 2' out/breakage-after-report.json \
  && ok "chain_break_at went from -1 to 2, the tampered record" || bad "break not detected"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: this repository's own ledger"
  if [ -z "${STATE_LEDGER_PATH:-}" ]; then
    echo "  SKIP live mode: set STATE_LEDGER_PATH (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live ledger exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed its cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
