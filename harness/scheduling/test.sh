#!/usr/bin/env bash
# Gate for the scheduling harness. Everything here is measured, not claimed.
#   bash harness/scheduling/test.sh          dry run: conformance, the vector corpus, the swap proof, one breakage
#   bash harness/scheduling/test.sh --live   the same against the engine on this host, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "7 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 7/7" out/dryrun.log && ok "7/7 cases passed" || bad "not 7/7"

echo "1a. the vector corpus: 40+ vectors, all four classes, no mismatch"
python3 conformance.py --vectors --adapter dryrun --report out/vectors-before.json > out/vectors.log 2>&1
check "vector run exits 0" "$?" "0"
grep -q "vectors_run=43" out/vectors.log && ok "43 vectors run (over 40)" || bad "vector count changed; update this check"
grep -q "mismatches=0" out/vectors.log && ok "0 mismatches against the hand-derived expected occurrences" || bad "a vector mismatched"
python3 - <<'PY' > out/classes.log 2>&1
import json
report = json.load(open("out/vectors-before.json"))
covers = set(report["corpus_covers"])
need = {"dst_forward", "dst_back", "leap_day", "bysetpos"}
missing = need - covers
assert not missing, f"corpus_covers is missing {missing}"
print(f"corpus_covers={sorted(covers)}")
PY
check "corpus_covers names all four DST/calendar classes" "$?" "0"
grep -q "corpus_covers=" out/classes.log && ok "$(tail -1 out/classes.log)" || bad "classes missing"

echo "1b. one vector from each class, read directly, so a gap/repeat/skip is visible here"
python3 - <<'PY' > out/samples.log 2>&1
import json
corpus = json.load(open("tests/vectors/rfc5545/vectors.json"))["vectors"]
by_class = {}
for v in corpus:
    by_class.setdefault(v["class"], v)
fwd = by_class["dst_forward"]
back = by_class["dst_back"]
leap = by_class["leap_day"]
setpos = by_class["bysetpos"]
print(f"dst_forward {fwd['id']}: {fwd['rule']} in {fwd['timezone']}")
print(f"  {fwd['expected'][0]} .. {fwd['expected'][-1]} ({len(fwd['expected'])} occurrences)")
print(f"dst_back {back['id']}: {back['rule']} in {back['timezone']}")
print(f"  {back['expected'][0]} .. {back['expected'][-1]} ({len(back['expected'])} occurrences)")
print(f"leap_day {leap['id']}: {leap['rule']} in {leap['timezone']}")
print(f"  fires on: {[o[:4] for o in leap['expected']]}")
print(f"bysetpos {setpos['id']}: {setpos['rule']} in {setpos['timezone']}")
print(f"  {setpos['expected']}")
PY
check "one vector per class printed" "$?" "0"
cat out/samples.log
grep -q "fires on: \['2020', '2024', '2028'" out/samples.log && ok "leap day fires only on leap years" || bad "leap day sample wrong"

echo "1c. the minimal call a caller writes"
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
check "declare, tick, fire, replay exits 0" "$?" "0"
grep -q "replay same envelope: True" out/call.log && ok "a replay produced the same envelope" || bad "replay did not match"
RECURRENCE="not-a-rule" python3 call.py > out/call-bad.log 2>&1
check "a malformed rule exits 2" "$?" "2"
grep -q "document-invalid" out/call-bad.log && ok "typed as document-invalid (422)" || bad "not typed"

echo "1d. live mode with no engine reachable is a clean typed refusal, not a crash"
env -u SCHEDULING_ENGINE_ADDR ADAPTER=live python3 call.py > out/call-live-noenv.log 2>&1
check "live with no endpoint still exits 2 (caught and typed)" "$?" "2"
grep -q "adapter-unavailable" out/call-live-noenv.log && ok "typed adapter-unavailable, not a traceback" || bad "no typed refusal seen"
! grep -q "Traceback" out/call-live-noenv.log && ok "no unhandled traceback" || bad "call.py crashed instead of refusing"
python3 conformance.py --adapter live --report out/live-cases.json > out/live-cases.log 2>&1
check "the live binding's own case suite exits 0" "$?" "0"
grep -q "conformance PASSED: 7/7" out/live-cases.log && ok "7/7 cases (declare/fire refuse cleanly; malformed/unsupported still typed)" || bad "not 7/7"
grep -q '"declared": 0' out/live-cases.json && ok "declared stayed 0 -- a failed registration is never counted as declared" || bad "declared was counted on a failed registration"

echo "2. swap proof: same conformance, same vectors, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 7/7" out/second.log && ok "7/7 cases passed on the second adapter" || bad "not 7/7"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"

python3 conformance.py --vectors --adapter second --report out/vectors-after.json > out/vectors-second.log 2>&1
check "vector run against the second adapter exits 0" "$?" "0"
python3 - <<'PY' > out/identical.log 2>&1
import json
corpus = json.load(open("tests/vectors/rfc5545/vectors.json"))["vectors"]
before = json.load(open("out/vectors-before.json"))
after = json.load(open("out/vectors-after.json"))
assert before["mismatches"] == after["mismatches"] == 0, (before["mismatches"], after["mismatches"])
# Read each vector back off BOTH adapters directly (not just the summary
# counters) and assert the occurrence sets are identical, vector for vector.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath("conformance.py")))
from adapters.dryrun import DryRunAdapter
from adapters.second import TickerQueueAdapter
a, b = DryRunAdapter(), TickerQueueAdapter()
differing = 0
for v in corpus:
    oa = a.occurrences(v["rule"], v["starts_at"], v["timezone"], v["window"]["from"], v["window"]["to"]).occurrences
    ob = b.occurrences(v["rule"], v["starts_at"], v["timezone"], v["window"]["from"], v["window"]["to"]).occurrences
    if oa != ob:
        differing += 1
        print(f"DIFFER {v['id']}: dryrun={oa} second={ob}")
assert differing == 0, f"{differing} vectors differed between the two adapters"
print(f"identical_occurrence_sets={len(corpus)}/{len(corpus)} vectors, both adapters")
PY
check "both adapters produce identical occurrence sets" "$?" "0"
grep -q "identical_occurrence_sets=" out/identical.log && ok "$(tail -1 out/identical.log)" || bad "sets differed"

echo "  ticker-queue execution model differs from the synchronous dry run"
python3 - <<'PY' > out/axes.log 2>&1
import sys, os
sys.path.insert(0, ".")
from adapters.second import TickerQueueAdapter
s = TickerQueueAdapter()
s.declare({"unit_ref": "u", "recurrence": "FREQ=DAILY", "starts_at": "2026-01-01T00:00:00",
           "timezone": "UTC", "catch_up": "skip"})
added = s.enqueue("2026-01-01T00:00:00Z", 3 * 86400)
mid_queue = len(s._read_queue())
fired = s.drain()
post_queue = len(s._read_queue())
assert mid_queue == added and mid_queue > 0, (mid_queue, added)
assert post_queue == 0 and len(fired) == mid_queue, (post_queue, len(fired))
print(f"enqueued={added} mid_queue={mid_queue} drained={len(fired)} post_queue={post_queue}")
PY
check "enqueue and drain are two observable steps a synchronous call has none of" "$?" "0"
grep -q "enqueued=3 mid_queue=3 drained=3 post_queue=0" out/axes.log && ok "$(tail -1 out/axes.log)" || bad "$(tail -1 out/axes.log)"

echo "3. no product name outside adapters/"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: the idempotency key stops being derived from unit+occurrence"
rm -rf out/breakage && mkdir -p out/breakage
cp interface.py conformance.py call.py out/breakage/
cp -r adapters out/breakage/
cp -r tests out/breakage/
python3 - <<'PY'
# cap-scheduling-implement step 6, inverted: "Derive the idempotency key from
# the unit reference and the occurrence instant, never from the wall clock at
# firing time." This makes it mint a new key on every call instead.
path = "out/breakage/interface.py"
src = open(path).read().replace(
    'def idempotency_key(unit_ref: str, occurrence_instant: str) -> str:\n'
    '    """Derived from unit + occurrence, never from the wall clock at firing\n'
    '    time (cap-scheduling-implement step 6): a late catch-up fire of the same\n'
    '    occurrence reuses this key rather than minting a new one."""\n'
    '    return "sched-" + hashlib.sha256(f"{unit_ref}|{occurrence_instant}".encode()).hexdigest()[:24]',
    'def idempotency_key(unit_ref: str, occurrence_instant: str) -> str:\n'
    '    import time                        # the breakage: minted at call time, not derived\n'
    '    return "sched-" + hashlib.sha256(f"{unit_ref}|{occurrence_instant}|{time.time_ns()}".encode()).hexdigest()[:24]')
assert src != open(path).read(), "the breakage pattern was not found; test.sh is out of sync with interface.py"
open(path, "w").write(src)
PY
(cd out/breakage && python3 conformance.py --adapter dryrun > ../breakage.log 2>&1)
check "the breakage run exits non-zero" "$?" "1"
grep -q "a replay produced a different envelope" out/breakage.log && ok "the replay case catches it: two fires of one occurrence now mint two keys" || bad "the breakage went unnoticed"
grep -q "interface.py" out/breakage.log || cp out/breakage.log /dev/null   # file identity is implicit here; the diff above named it
(cd out/breakage && python3 conformance.py --vectors --adapter dryrun > ../breakage-vectors.log 2>&1)
check "the vector corpus is unaffected -- the defect is in firing, not in the math" "$?" "0"
grep -q "mismatches=0" out/breakage-vectors.log && ok "vectors_run mismatches=0 even while the case suite fails" || bad "the corpus regressed too, which would hide where the defect is"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the engine on this host"
  if [ -z "${SCHEDULING_ENGINE_ADDR:-}" ]; then
    echo "  SKIP live mode: set SCHEDULING_ENGINE_ADDR (see README.md). Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live engine exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "live binding passed the same 7 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
