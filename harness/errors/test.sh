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

echo "2b. one construction point: no second place builds a Problem (errors-q5)"
python3 conformance.py --construction-scan . > out/construction-scan.log 2>&1
check "construction scan exits 0" "$?" "0"
grep -q "^owner=problem.py:" out/construction-scan.log \
  && ok "the shared point ($(grep '^owner=' out/construction-scan.log | cut -d= -f2)) is the sole Problem(...) call site" \
  || bad "no single owning call site found"
grep -q "^stray_construction_hits=0$" out/construction-scan.log \
  && ok "0 Problem(...) constructions outside problem.py" || bad "a second construction path exists"

echo "2c. platform-wide: the same property held over harness/errors alone is now checked over all of harness/ (errors-q5's own gap: 'the scan covers only that directory')"
python3 platform_conformance.py --construction-scan .. > out/platform-scan.log 2>&1
check "the platform-wide construction scan exits 0" "$?" "0"
grep -q "^platform_stray_construction_hits=0$" out/platform-scan.log \
  && ok "0 hand-built RFC 9457 dicts anywhere under harness/, outside problem.py" || bad "a stray construction exists somewhere under harness/"
python3 platform_conformance.py --raise-all .. > out/platform-raise.log 2>&1
check "raising every typed condition of every harness under harness/ exits 0" "$?" "0"
grep -q "^conditions_raised=" out/platform-raise.log \
  && ok "$(grep '^conditions_raised=' out/platform-raise.log)" || bad "raise-all did not report a count"

echo "2d. deliberate breakage: a capability's own registry gate builds its own body by hand instead of calling render_body (the exact defect errors-q5's re-answer found: nine registries, eight titles, a stray content_type member, a composition layer building a 28th body)"
rm -rf out/platform-breakage && mkdir -p out/platform-breakage/harness/errors out/platform-breakage/harness/idempotency
cp problem.py out/platform-breakage/harness/errors/
cp ../idempotency/interface.py out/platform-breakage/harness/idempotency/interface.py
python3 - <<'PY'
path = "out/platform-breakage/harness/idempotency/interface.py"
src = open(path).read().replace(
    '        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)\n',
    '        # the breakage: this adapter invents its own failure shape instead of\n'
    '        # rendering through the one shared point (errors-q5)\n'
    '        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,\n'
    '                     "detail": detail, "retryable": retryable, **ext}\n')
assert src != open(path).read(), "the breakage pattern was not found; test.sh is out of sync with the migrated body-construction line"
open(path, "w").write(src)
PY
python3 platform_conformance.py --construction-scan out/platform-breakage > out/platform-breakage-scan.log 2>&1
check "the breakage run exits non-zero (construction scan)" "$?" "1"
grep -q "idempotency/interface.py" out/platform-breakage-scan.log && ok "the scan names the file the breakage broke" || bad "file not named"
python3 platform_conformance.py --raise-all out/platform-breakage > out/platform-breakage-raise.log 2>&1
check "the breakage run exits non-zero (raise-all)" "$?" "1"
grep -q "render_body() ran 0 times" out/platform-breakage-raise.log \
  && ok "raise-all independently catches the same defect at runtime, not just by grepping source" || bad "raise-all missed it"

echo "3. no product name anywhere in this harness"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits (PASS.md B3 records no component for this element)" || bad "product name found"

echo "4. deliberate breakage: the edge adapter forwards an untyped upstream body unchanged"
rm -rf out/breakage && mkdir -p out/breakage
cp interface.py conformance.py call.py problem.py out/breakage/
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

echo "4b. deliberate breakage: a capability adapter invents its own failure shape"
rm -rf out/breakage2 && mkdir -p out/breakage2
cp interface.py conformance.py call.py problem.py out/breakage2/
cp -r adapters out/breakage2/
python3 - <<'PY'
# The exact defect errors-q5 asks whether the platform can still have: a new
# capability adapter builds a Problem itself instead of raising through
# construct(). This edits the edge adapter's own untyped/wrong-media-type
# fallback to build the wire body's dataclass by hand -- same field values,
# but a second Problem(...) call site outside problem.py.
path = "out/breakage2/adapters/second.py"
src = open(path).read().replace(
    '            return construct(\n'
    '                "adapter-unavailable",\n'
    '                f"upstream answered {wire.get(\'status\')} {media_type or \'(no media type)\'}: {raw[:200]}",\n'
    '                retry_after_s=30)\n',
    '            # the breakage: this adapter invents its own Problem instead of\n'
    '            # raising into the one shared construction point\n'
    '            return Problem(PROBLEM_BASE + "adapter-unavailable",\n'
    '                "A capability adapter is down, or raised an untyped failure", 503,\n'
    '                f"upstream answered {wire.get(\'status\')} {media_type or \'(no media type)\'}: {raw[:200]}",\n'
    '                True, None, (), {"retry_after_s": 30})\n')
assert src != open(path).read(), "the breakage pattern was not found; test.sh is out of sync with second.py"
open(path, "w").write(src)
PY
(cd out/breakage2 && python3 conformance.py --construction-scan . > ../breakage2.log 2>&1)
check "the construction-scan run exits non-zero" "$?" "1"
grep -q "adapters/second.py" out/breakage2.log && ok "the scan names the file the breakage broke" || bad "file not named"
grep -q "^stray_construction_hits=1$" out/breakage2.log && ok "a second Problem(...) call site is caught" || bad "the breakage went unnoticed"

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
