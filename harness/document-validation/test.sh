#!/usr/bin/env bash
# Gate for the document-validation harness. Everything here is measured, not claimed.
#   bash harness/document-validation/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/document-validation/test.sh --live   the same against DOCVALID_SCHEMA_STORE_DIR, if set
set -u
HARNESS="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HARNESS/../.." && pwd)"
cd "$REPO_ROOT"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf harness/document-validation/out && mkdir -p harness/document-validation/out
OUT=harness/document-validation/out
HD=harness/document-validation

echo "1. conformance against the dry-run adapter"
python3 "$HD/conformance.py" --adapter dryrun --report "$OUT/before.json" > "$OUT/dryrun.log" 2>&1
check "conformance exits 0" "$?" "0"
grep -q "conformance PASSED: 14/14" "$OUT/dryrun.log" && ok "14/14 cases passed" || bad "not 14/14 ($(tail -1 "$OUT/dryrun.log"))"

echo "1b. the minimal call a caller writes"
MARKERLINE=$(grep -n ">>> CALLER CODE" "$HD/call.py" | wc -l)
[ "$MARKERLINE" -eq 1 ] || bad "call.py has $MARKERLINE CALLER CODE markers, expected 1"
LINES=$(awk '/>>> CALLER CODE/{f=1; next} f && /^if __name__/{exit} f && NF && $0 !~ /^[[:space:]]*#/{n++} END{print n+0}' "$HD/call.py")
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
if grep -A100 ">>> CALLER CODE" "$HD/call.py" | grep -vE '^\s*#' | grep -qE '\.(jsonl|ndjson|db|sqlite3?|journal)["'"'"']'; then
  bad "call.py reads an adapter's own storage by path"
else
  ok "the caller names no file in an adapter's own storage"
fi
ADAPTER=dryrun python3 "$HD/call.py" > "$OUT/call.log" 2>&1
check "one call against entry.schema.json exits 0" "$?" "0"
grep -q "^False" "$OUT/call.log" && ok "the default malformed envelope reads valid=False" || bad "expected valid=False"
grep -q "/actor" "$OUT/call.log" && ok "the failing pointer names /actor" || bad "no /actor pointer"
INSTANCE_KIND=valid ADAPTER=dryrun python3 "$HD/call.py" > "$OUT/call-valid.log" 2>&1
check "a valid envelope exits 0" "$?" "0"
grep -q "^True" "$OUT/call-valid.log" && ok "a well-formed envelope reads valid=True" || bad "expected valid=True"
SCHEMA_URI="$HD/schemas/bad-dialect.schema.json" ADAPTER=dryrun python3 "$HD/call.py" > "$OUT/call-baddialect.log" 2>&1
check "a schema declaring draft-07 exits 2" "$?" "2"
grep -q "dialect-unsupported" "$OUT/call-baddialect.log" && ok "typed as dialect-unsupported (422)" || bad "not typed"

echo "1c. the dry-run adapter's own failure path"
DRYRUN_FAIL=1 ADAPTER=dryrun python3 "$HD/call.py" > "$OUT/call-fail.log" 2>&1
check "an unreachable schema store exits 2" "$?" "2"
grep -q "schema-unavailable" "$OUT/call-fail.log" && ok "typed as schema-unavailable (503)" || bad "not typed"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat "$HD/interface.py" "$HD/call.py" "$HD/conformance.py" | sha256sum | cut -d' ' -f1)
python3 "$HD/conformance.py" --adapter second --report "$OUT/after.json" > "$OUT/second.log" 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 14/14" "$OUT/second.log" && ok "14/14 cases passed on the second adapter" || bad "not 14/14"
AFTER_HASH=$(cat "$HD/interface.py" "$HD/call.py" "$HD/conformance.py" | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 "$HD/call.py" > "$OUT/call-second.log" 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<PY > "$OUT/axes.log" 2>&1
import json
before, after = json.load(open("$OUT/before.json")), json.load(open("$OUT/after.json"))
axes = [("execution_model", "how the schema is read and checked"),
        ("schema_reads", "how many times the raw schema is re-walked")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:16} {str(before[axis]):28} {str(after[axis]):28} ({why})")
assert len(differ) >= 2, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 14, "both bindings must pass the same cases"
mismatch = [k for k in before["outcomes"] if before["outcomes"][k] != after["outcomes"][k]]
assert not mismatch, f"outcomes differ on fixtures {mismatch}"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']} "
      f"fixtures_compared={len(before['outcomes'])} fixture_mismatches=0")
PY
check "the two adapters differ in execution model on 2 or more axes" "$?" "0"
grep -q "fixture_mismatches=0" "$OUT/axes.log" \
  && ok "both adapters gave the same outcome on every shared fixture ($(grep -o 'fixtures_compared=[0-9]*' "$OUT/axes.log"))" \
  || bad "$(tail -1 "$OUT/axes.log")"

echo "3. no validator library name in the interface, the caller or the conformance run"
python3 "$HD/conformance.py" --product-scan "$HD" > "$OUT/scan.log" 2>&1
check "library-name scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" "$OUT/scan.log" && ok "0 hits outside adapters/" || bad "a library name leaked"

echo "4. deliberate breakage: a validator library imported directly outside adapters/"
rm -rf "$OUT/breakage" && mkdir -p "$OUT/breakage"
cp -r "$HD/interface.py" "$HD/call.py" "$HD/conformance.py" "$HD/adapters" "$OUT/breakage/"
# The library name is assembled here so this gate's own source stays clean and
# only the copy under out/breakage/ carries the import the scan is meant to catch.
python3 - <<PY
lib = "json" + "schema"
path = "$OUT/breakage/call.py"
src = open(path).read().replace(
    "from interface import DIALECT_2020_12, Problem, ValidationRequest",
    f"import {lib}  # the breakage: a validator library imported outside adapters/\n"
    "from interface import DIALECT_2020_12, Problem, ValidationRequest")
open(path, "w").write(src)
PY
python3 "$HD/conformance.py" --product-scan "$OUT/breakage" > "$OUT/breakage.log" 2>&1
check "the breakage run exits non-zero" "$?" "1"
grep -q "call.py" "$OUT/breakage.log" && ok "the run names the file that broke it" || bad "file not named"
grep -q "product_hits=1" "$OUT/breakage.log" && ok "product_hits went from 0 to 1" || bad "hits not counted"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the schema store named by DOCVALID_SCHEMA_STORE_DIR"
  if [ -z "${DOCVALID_SCHEMA_STORE_DIR:-}" ]; then
    echo "  SKIP live mode: set DOCVALID_SCHEMA_STORE_DIR (see README.md). Nothing live was measured."
  else
    python3 "$HD/conformance.py" --adapter live --report "$OUT/live.json" > "$OUT/live.log" 2>&1
    check "conformance against the live schema store exits 0" "$?" "0"
    grep -q "conformance PASSED" "$OUT/live.log" && ok "live binding passed the same cases" || bad "live binding failed"
    ADAPTER=live python3 "$HD/call.py" > "$OUT/call-live.log" 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
