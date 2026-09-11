#!/usr/bin/env bash
# Visible check for examples/reference/3-core-agent -- the one the author can see and tune.
# The hidden check (docs/night/hidden/3-core-agent.sh) is written by someone who never saw this
# file, because a gate its author can tune is not the same evidence as one they cannot.
set -uo pipefail
cd "$(dirname "$0")"
ROOT=$(cd ../../.. && pwd)
passed=0; failed=0
ok()   { passed=$((passed+1)); printf '  ok    %s\n' "$1"; }
bad()  { failed=$((failed+1)); printf '  FAIL  %s\n' "$1"; }
check(){ if eval "$2" >/dev/null 2>&1; then ok "$1"; else bad "$1"; fi; }

echo "card 3.3 Runtime / Sandbox -- contract"
check "call.py is the minimal caller (under 40 lines)" '[ "$(wc -l < call.py)" -lt 40 ]'
check "the caller names no VMM, runtime binary or limit" \
      '! grep -qiE "firecracker|gvisor|kata|docker|podman|qemu|runc|--memory|--cpus" call.py'
check "dryrun runs the caller unchanged"  'ADAPTER=dryrun python3 call.py'
check "second runs the SAME caller unchanged" 'ADAPTER=second python3 call.py'

echo "conformance -- status domain and lifecycle"
check "dryrun conforms" 'python3 conformance.py dryrun'
check "second conforms" 'python3 conformance.py second'
check "every adapter is callable identically" \
      'python3 -c "import conformance,sys; f=conformance.signature_parity(); print(f); sys.exit(1 if f else 0)"'

echo "the swap is real, not a relabelling"
check "the two adapters put a unit through DIFFERENT lifecycles" \
      'test "$(ADAPTER=dryrun python3 call.py | grep -c "creating>")" != "$(ADAPTER=second python3 call.py | grep -c "creating>")"'
check "a claim against a warm pool never passes through creating" \
      '! ADAPTER=second python3 call.py | grep -q "creating>"'
check "a cold create does pass through creating" \
      'ADAPTER=dryrun python3 call.py | grep -q "creating>"'
check "the status a caller reads is always the end of the lifecycle it was given" \
      'python3 -c "
from interface import Unit, load
for n in (\"dryrun\", \"second\"):
    s = load(n); b = s.unpack(\"registry.example/agent-base:2026-09\")
    h = s.run(b, Unit(unit_id=\"t\", intent=\"trace\"))
    i = s.inspect(h); assert i.trace[-1] == i.status, (n, i)
    f = s.stop(h); assert f.trace[-1] == \"stopped\", (n, f)
"'
check "the caller's output shape is identical across adapters" \
      'test "$(ADAPTER=dryrun python3 call.py | awk "{print \$1, \$2, \$3, \$4}")" = "$(ADAPTER=second python3 call.py | awk "{print \$1, \$2, \$3, \$4}")"'

echo "live is claimed, and refuses to look measured -- STATUS row 37"
check "live exists at the same interface" \
      'python3 -c "from interface import load; load(\"live\")"'
check "live refuses rather than returning a plausible status" \
      'python3 -c "
from interface import ClaimedNotMeasured, Unit, load
s = load(\"live\")
try:
    s.unpack(\"x\")
except ClaimedNotMeasured as e:
    assert \"row 37\" in str(e), e
else:
    raise SystemExit(\"live returned a result it cannot have measured\")
"'

echo "deliberate breakage -- prove the gate can fail"
check "conformance REJECTS an adapter with an off-spec status" \
      '! python3 conformance.py _broken_on_purpose'
check "and names the off-spec value rather than just failing" \
      '{ python3 conformance.py _broken_on_purpose 2>&1 || true; } | grep -q "ready"'

echo "claims are cited or proposed"
check "cards.json is structurally honest about what it covers" 'python3 check_cards.py'
check "every knob this area declares changes something, or says it does not" \
      'cd "$ROOT" && python3 tools/inert_check.py examples/reference/3-core-agent'
check "the prose gate reads this area and finds nothing blocking" \
      'cd "$ROOT" && python3 tools/prose_gate.py --corpus examples/reference/3-core-agent'

printf '\npassed %d, failed %d\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
