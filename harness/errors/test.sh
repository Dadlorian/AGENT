#!/usr/bin/env bash
# Gate for the errors harness. Everything here is measured, not claimed.
#   bash harness/errors/test.sh          dry run: conformance, the swap proof, one deliberate breakage
#   bash harness/errors/test.sh --live   the same against live mode, if ERRORS_RUN_ID/ERRORS_CORRELATION_ID are set
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

echo "1b. the minimal call a caller writes"
LINES=$(python3 - <<'PY'
lines = open("call.py").read().splitlines()
marks = [i for i, l in enumerate(lines) if ">>> CALLER CODE" in l]
assert len(marks) == 1, f"expected exactly one marker, found {len(marks)}"
body = lines[marks[0] + 1:]
end = next((i for i, l in enumerate(body) if l.startswith("if __name__")), len(body))
print(len([l for l in body[:end] if l.strip() and not l.strip().startswith("#")]))
PY
)
[ "$LINES" -lt 40 ] && ok "caller code is $LINES lines, under 40" || bad "caller code is $LINES lines"
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "one typed problem for a registry refusal exits 0" "$?" "0"
grep -q "urn:agentic:problem:budget-exhausted" out/call.log && ok "typed budget-exhausted (402)" || bad "not typed"
grep -q "rejected before a body was ever built" out/call.log && ok "an unregistered type is refused at construction" || bad "not rejected"
grep -q "byte_identical_on_second" out/call.log && ok "the table reports the byte-identical check" || bad "check missing from output"
ADAPTER=dryrun SUFFIX=deadline-exceeded DETAIL="wall clock ceiling reached" python3 call.py > out/call-retry.log 2>&1
grep -q "retry after" out/call-retry.log && ok "a retryable type advises retry, read from the type alone" || bad "retry advice missing"
ADAPTER=dryrun SUFFIX=policy-denied DETAIL="wall clock ceiling reached" python3 call.py > out/call-noretry.log 2>&1
grep -q "do not retry" out/call-noretry.log && ok "a non-retryable type with the SAME detail text advises no retry" || bad "retry advice ignored the type"

echo "1c. live mode without deployment context is a clean typed refusal, not a crash"
env -u ERRORS_RUN_ID -u ERRORS_CORRELATION_ID ADAPTER=live python3 call.py > out/call-live-noenv.log 2>&1
check "live with no context still exits 0 (caught and reported)" "$?" "0"
grep -q "adapter refused before the registry check: urn:agentic:problem:adapter-unavailable" out/call-live-noenv.log \
  && ok "the missing-context refusal is typed adapter-unavailable, not a traceback" || bad "no typed refusal seen"
! grep -q "Traceback" out/call-live-noenv.log && ok "no unhandled traceback" || bad "call.py crashed instead of refusing"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 9/9" out/second.log && ok "9/9 cases passed on the second adapter" || bad "not 9/9"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("execution_model", "how many processes must run to answer"),
        ("wrong_media_type", "whether an untyped upstream response is even possible"),
        ("declared_gaps", "what raise-site context this binding can populate")]
differ = [(a, before[a], after[a]) for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:16} {str(before[axis]):40} {str(after[axis]):40} ({why})")
assert len(differ) >= 2, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 9, "both bindings must pass the same cases"
print(f"axes_differing={len(differ)} cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 2 or more axes" "$?" "0"
grep -q "axes_differing=" out/axes.log && ok "$(tail -1 out/axes.log)" || bad "axes did not differ"

echo "3. no product name anywhere in this harness"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits (PASS.md B3 records no component for this element)" || bad "product name found"

echo "4. deliberate breakage: the edge adapter forwards an untyped upstream body unchanged"
rm -rf out/breakage && mkdir -p out/breakage
cp interface.py conformance.py call.py out/breakage/
cp -r adapters out/breakage/
python3 - <<'PY'
# The bug cap-errors-implement names directly: an edge filter's most likely
# defect is silently forwarding an upstream body it did not understand
# (cap-errors-implement best_practices). This removes the one guard that
# stops that: the media-type / registered-type check before reshaping.
path = "out/breakage/adapters/second.py"
src = open(path).read().replace(
    '        media_type = wire.get("media_type", "")\n'
    '        body = wire.get("body")\n'
    '        if media_type != MEDIA_TYPE or not isinstance(body, dict):\n'
    '            self.untyped += 1\n'
    '            self.wrong_media_type += 1\n'
    '            raw = body if isinstance(body, str) else json.dumps(body)\n'
    '            return construct(\n'
    '                "adapter-unavailable",\n'
    '                f"upstream answered {wire.get(\'status\')} {media_type or \'(no media type)\'}: {raw[:200]}",\n'
    '                retry_after_s=30)\n',
    '        body = wire.get("body")           # the breakage: no media-type or shape check first\n')
assert src != open(path).read(), "the breakage pattern was not found; test.sh is out of sync with second.py"
open(path, "w").write(src)
PY
(cd out/breakage && python3 conformance.py --adapter second > ../breakage.log 2>&1)
check "the breakage run exits non-zero" "$?" "1"
grep -q "adapters/second.py" out/breakage.log && ok "the run names the file the breakage broke" || bad "file not named"
grep -Eq "FAIL|Traceback" out/breakage.log && ok "an untyped upstream body is no longer converted; the check catches it" || bad "the breakage went unnoticed"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: real deployment context"
  if [ -z "${ERRORS_RUN_ID:-}" ] || [ -z "${ERRORS_CORRELATION_ID:-}" ]; then
    echo "  SKIP live mode: set ERRORS_RUN_ID and ERRORS_CORRELATION_ID (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live binding exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed the same 9 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
