#!/usr/bin/env bash
# Gate for the work-intake harness. Everything here is measured, not claimed.
#   bash harness/work-intake/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/work-intake/test.sh --live   the same against the intake endpoint on this host, if set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out
EXAMPLE_DIR=$(cd ../../examples/end-to-end && pwd)

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "15 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 15/15" out/dryrun.log && ok "15/15 cases passed" || bad "not 15/15"
grep -q "distinct_job_digests=1 distinct_entry_ids=4" out/dryrun.log \
  && ok "one job digest, four submissions" || bad "producers are not equivalent"
grep -q "invalid=0 untyped_refusals=0" out/dryrun.log \
  && ok "0 invalid envelopes, 0 untyped refusals" || bad "invalid or untyped"

echo "1b. the minimal call a caller writes (harness/caller_lines.py, the one method)"
LINES=$(python3 - <<'PY'
import os, sys
sys.path.insert(0, os.path.abspath(".."))
import caller_lines
caller_lines.HARNESSES = caller_lines.HARNESSES + ("work-intake",)
print(caller_lines.count("work-intake"))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
python3 - <<'PY'
import os, sys
sys.path.insert(0, os.path.abspath(".."))
import caller_lines
caller_lines.HARNESSES = caller_lines.HARNESSES + ("work-intake",)
hits = caller_lines.storage_hits("work-intake")
for n, line in hits:
    print(f"call.py:{n}: names adapter storage: {line}")
sys.exit(1 if hits else 0)
PY
check "the caller names no file in the adapter's own storage" "$?" "0"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "one document through four doors exits 0" "$?" "0"
grep -q "1 job digest   1 resolved manifest   4 submissions" out/call.log \
  && ok "one identical envelope job, one identical resolved manifest, four submissions" \
  || bad "$(grep -c . out/call.log) lines and no equivalence line"
grep -q "duplicate_of=human-checkout-500s, still 4 entries recorded" out/call.log \
  && ok "a replay under the same key wrote nothing" || bad "the replay was not free"
grep -q "urn:agentic:problem:document-invalid" out/call.log \
  && ok "a malformed task returns a typed refusal (422)" || bad "the refusal is not typed"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"

echo "1c. the dry-run adapter's own failure path"
INTAKE_FAIL=1 ADAPTER=dryrun python3 call.py > out/call-fail.log 2>&1
check "an unreachable intake path exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"
grep -q "nothing was admitted" out/call-fail.log && ok "nothing was admitted" || bad "no such claim"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py producers.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 15/15" out/second.log && ok "15/15 cases passed on the second adapter" || bad "not 15/15"
AFTER_HASH=$(cat interface.py call.py conformance.py producers.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
python3 conformance.py --adapter dryrun --adapter second --report out/merged.json > out/merged.log 2>&1
check "both bindings in one merged run exit 0" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
merged = json.load(open("out/merged.json"))
axes = [("execution_model", "how a producer submits"),
        ("ack_delivery", "how the acknowledgement is delivered"),
        ("idempotency_source", "which producer identity becomes the key"),
        ("endpoint_marker", "what the binding stamped")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:20} {str(before[axis]):34} {str(after[axis]):46} ({why})")
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["adapter"] != after["adapter"], "both runs report the same configured adapter"
assert before["cases_passed"] == after["cases_passed"] == 15, "both bindings must pass the same cases"
assert before["job_digest"] == after["job_digest"], "the same job digested differently on the two bindings"
assert before["manifest_digest"] == after["manifest_digest"], "the resolved manifest differs across bindings"
assert {r["adapters_run"] for r in merged} == {2}, "the merged report does not show adapters_run 2"
assert {r["selected_by"] for r in merged} == {"configuration"}, "a binding was not selected by configuration"
print(f"axes_differing={len(differ)} job_digest={before['job_digest'][7:19]} "
      f"manifest_digest={before['manifest_digest'][7:19]} adapters_run=2")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=4" out/axes.log && ok "4 axes differ (submission, acknowledgement, key source, marker)" \
  || bad "$(tail -1 out/axes.log)"
grep -q "adapters_run=2" out/axes.log \
  && ok "one job digest and one resolved manifest across both bindings" || bad "digests differ across bindings"

echo "3. no product name in the interface, the caller, the producers or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: the request-pushed mapper stamps a default field"
rm -rf out/breakage && mkdir -p out/breakage
cp interface.py call.py conformance.py producers.py out/breakage/
cp -r adapters out/breakage/adapters
python3 - <<'PY'
path = "out/breakage/adapters/dryrun.py"
src = open(path).read().replace(
    '            intent=dict(job["intent"]),',
    '            intent={**job["intent"], "priority": "high"},   # the breakage: a stamped default')
open(path, "w").write(src)
PY
INTAKE_EXAMPLE_DIR="$EXAMPLE_DIR" python3 out/breakage/conformance.py --adapter dryrun \
  --report out/breakage-a.json > out/breakage-a.log 2>&1
check "the request-pushed run exits non-zero" "$?" "1"
grep -q "invalid=4" out/breakage-a.log && ok "invalid went from 0 to 4" || bad "invalid not counted"
grep -q "FAIL one document through the four producers" out/breakage-a.log \
  && ok "the run names the case that broke it" || bad "case not named"
INTAKE_EXAMPLE_DIR="$EXAMPLE_DIR" python3 out/breakage/conformance.py --adapter second \
  --report out/breakage-b.json > out/breakage-b.log 2>&1
check "the agent-message run still exits 0" "$?" "0"
python3 - <<'PY'
import json
a, b = json.load(open("out/breakage-a.json")), json.load(open("out/breakage-b.json"))
before = json.load(open("out/before.json"))
assert a["verdict"] == "fail" and b["verdict"] == "pass", (a["verdict"], b["verdict"])
assert a["invalid"] == 4 and b["invalid"] == 0, (a["invalid"], b["invalid"])
assert a["job_digest"] != before["job_digest"], "the stamped field left the job digest alone"
assert b["job_digest"] == before["job_digest"], "the untouched binding changed too"
print(f"request-pushed: invalid {before['invalid']} -> {a['invalid']}, verdict {a['verdict']}; "
      f"agent-message: invalid {b['invalid']}, verdict {b['verdict']}, job digest unchanged "
      f"({b['job_digest'][7:19]})")
PY
check "the breakage singles out one adapter and leaves the other green" "$?" "0"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the intake endpoint on this host"
  if [ -z "${INTAKE_URL:-}" ]; then
    echo "  SKIP live mode: set INTAKE_URL (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live endpoint exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed the same 15 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
