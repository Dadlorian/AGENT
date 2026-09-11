#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "3-core-agent" (card 3.3, Runtime / Sandbox).
#
# Held out from examples/reference/3-core-agent/ on purpose: the grader is never visible to the
# graded (F-b1-07). test.sh is the area's visible feedback surface; this script is what decides,
# and the author of the example never sees it. Every assertion here reads a value back from the
# code under test -- a returned object, an exit status, a signature -- never a log line the
# example printed about itself.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/3-core-agent.sh
#
# Python 3 standard library only. No network, no pip, no files outside $WORK.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/reference/3-core-agent"
WORK="${TMPDIR:-/tmp}/hidden-3-core-agent-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/reference/3-core-agent/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# --- h-01 both runnable adapters honour the image->bundle->run->status lifecycle -------------
py "$AREA" <<'PY' && ok "h-01 dryrun and second both go unpack->run(running)->stop(stopped) in lifecycle order, each naming its own isolation" || bad "h-01 lifecycle/status contract"
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from interface import STATUS_VALUES, Unit, load

isolations = {}
for name in ("dryrun", "second"):
    sandbox = load(name)
    bundle = sandbox.unpack("registry.example/agent-base:2026-09")
    assert bundle.image and bundle.digest, f"{name}: unpack returned an empty bundle"
    handle = sandbox.run(bundle, Unit(unit_id="h1", intent="hidden-check"))
    running = sandbox.inspect(handle)
    assert running.status in STATUS_VALUES, f"{name}: status {running.status!r} not in {STATUS_VALUES}"
    assert running.status == "running", f"{name}: status after run is {running.status!r}, not 'running'"
    assert running.isolation, f"{name}: inspect did not name an isolation mechanism"
    assert running.trace, f"{name}: inspect returned no trace, the lifecycle is unobservable"
    assert all(s in STATUS_VALUES for s in running.trace), f"{name}: trace {running.trace} outside {STATUS_VALUES}"
    assert list(running.trace) == sorted(running.trace, key=STATUS_VALUES.index), (
        f"{name}: trace {running.trace} is not in lifecycle order")
    assert running.trace[-1] == "running", f"{name}: trace does not end at 'running': {running.trace}"
    stopped = sandbox.stop(handle)
    assert stopped.status == "stopped", f"{name}: status after stop is {stopped.status!r}, not 'stopped'"
    assert stopped.trace[-1] == "stopped", f"{name}: trace does not end at 'stopped': {stopped.trace}"
    isolations[name] = running.isolation

assert isolations["dryrun"] != isolations["second"], (
    "dryrun and second report the same isolation string -- they are not naming distinct mechanisms")
PY

# --- h-02 second is a genuinely different execution model, not a relabelled dryrun -----------
py "$AREA" <<'PY' && ok "h-02 second's claim against a prepared template skips 'creating'; dryrun's cold create never does" || bad "h-02 the two adapters do not differ in observable lifecycle"
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from interface import Unit, load

image = "registry.example/agent-base:2026-09"

dry = load("dryrun")
dbundle = dry.unpack(image)
dh = dry.run(dbundle, Unit(unit_id="u1", intent="repeat"))
dinsp = dry.inspect(dh)
assert dinsp.warm is False, f"dryrun: expected warm=False, got {dinsp.warm}"
assert "creating" in dinsp.trace, f"dryrun: expected a full cold create, trace was {dinsp.trace}"

warm_pool = load("second")
wbundle = warm_pool.unpack(image)
wh = warm_pool.run(wbundle, Unit(unit_id="u1", intent="repeat"))
winsp = warm_pool.inspect(wh)
assert winsp.warm is True, f"second: expected warm=True once the template is prepared, got {winsp.warm}"
assert "creating" not in winsp.trace, (
    f"second: a claim against an already-unpacked template should skip 'creating', trace was {winsp.trace}")

# Same caller-visible interface (Unit in, handle out, Inspection out); materially different
# lifecycles recorded in `trace` -- this is the load-bearing evidence that it's a genuine swap.
assert dinsp.trace != winsp.trace, "dryrun and second produced identical traces -- not a real swap"
PY

# --- h-03 all three adapters share one signature, and none of it configures isolation --------
py "$AREA" <<'PY' && ok "h-03 dryrun/second/live share the contract signature; no method takes a runtime/network/limit argument" || bad "h-03 signature parity or a leaked isolation-config parameter"
import inspect as _i
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from interface import RuntimeSandbox, load
import conformance

findings = conformance.signature_parity()
assert not findings, f"conformance's own signature_parity found: {findings}"

CONTRACT = ("unpack", "run", "inspect", "stop")
FORBIDDEN = ("runtime", "vmm", "network", "limit", "resource", "cpu", "memory", "mode", "sandbox_type")
for name in ("dryrun", "second", "live"):
    sandbox_cls = type(load(name))
    for m in CONTRACT:
        params = [p for p in _i.signature(getattr(sandbox_cls, m)).parameters if p != "self"]
        leaked = [p for p in params for f in FORBIDDEN if f in p.lower()]
        assert not leaked, f"{name}.{m} exposes an isolation-config parameter: {leaked}"
PY

# --- h-04 the caller's Unit cannot configure isolation ----------------------------------------
py "$AREA" <<'PY' && ok "h-04 Unit carries only unit_id/intent/profile -- no runtime, image override or limit field" || bad "h-04 the caller can configure isolation directly"
import dataclasses
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from interface import Unit

fields = {f.name for f in dataclasses.fields(Unit)}
assert fields == {"unit_id", "intent", "profile"}, f"Unit fields are {fields}, caller has an extra knob"
default_profile = dataclasses.fields(Unit)[[f.name for f in dataclasses.fields(Unit)].index("profile")].default
assert default_profile == "default", f"profile does not default to 'default': {default_profile!r}"
PY

# --- h-05 the live adapter cannot be mistaken for a measured result --------------------------
py "$AREA" <<'PY' && ok "h-05 every live method refuses with ClaimedNotMeasured instead of returning a result" || bad "h-05 live silently returned something a caller could read as measured"
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from interface import Bundle, ClaimedNotMeasured, RuntimeSandbox, Unit, load

live = load("live")
assert isinstance(live, RuntimeSandbox), "live adapter is not a RuntimeSandbox at all"
assert issubclass(ClaimedNotMeasured, RuntimeError), "ClaimedNotMeasured is not even a RuntimeError"

calls = {
    "unpack": lambda: live.unpack("registry.example/agent-base:2026-09"),
    "run": lambda: live.run(Bundle(image="x", digest="y"), Unit(unit_id="c1", intent="x")),
    "inspect": lambda: live.inspect("some-handle"),
    "stop": lambda: live.stop("some-handle"),
}
for method, call in calls.items():
    try:
        result = call()
    except ClaimedNotMeasured as e:
        assert "measured" in str(e).lower() or "claimed" in str(e).lower(), (
            f"live.{method} raised ClaimedNotMeasured but the message does not say so: {e!r}")
    except Exception as e:
        raise AssertionError(f"live.{method} raised {type(e).__name__}, not ClaimedNotMeasured") from e
    else:
        raise AssertionError(f"live.{method} returned {result!r} instead of refusing")
PY

# --- h-06 neither the CLI conformance check nor the minimal caller lets live pass quietly -----
python3 "$AREA/conformance.py" live >/dev/null 2>&1
CONF_LIVE_RC=$?
ADAPTER=live python3 "$AREA/call.py" >/dev/null 2>&1
CALL_LIVE_RC=$?
if [ "$CONF_LIVE_RC" -ne 0 ] && [ "$CALL_LIVE_RC" -ne 0 ]; then
  ok "h-06 conformance.py and call.py both exit non-zero against the live adapter"
else
  bad "h-06 conformance.py live rc=$CONF_LIVE_RC, call.py live rc=$CALL_LIVE_RC (a claimed path passed as if measured)"
fi

# --- h-07 the same caller runs unmodified against both real adapters -------------------------
ADAPTER=dryrun python3 "$AREA/call.py" >/dev/null 2>&1
DRY_RC=$?
ADAPTER=second python3 "$AREA/call.py" >/dev/null 2>&1
SECOND_RC=$?
if [ "$DRY_RC" -eq 0 ] && [ "$SECOND_RC" -eq 0 ]; then
  ok "h-07 call.py exits 0 against dryrun and second with no code change, only ADAPTER"
else
  bad "h-07 call.py dryrun rc=$DRY_RC, second rc=$SECOND_RC"
fi

# --- h-08 a contract-violating adapter constructed here is actually rejected -----------------
py "$AREA" <<'PY' && ok "h-08 conformance.check() rejects an adapter that never names its isolation mechanism" || bad "h-08 the conformance gate passed a broken adapter"
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from adapters.dryrun import DryRunSandbox
import conformance

class SilentSandbox(DryRunSandbox):
    """Built here, not shipped with the area: behaves like dryrun in every way except it
    never names what it asserts. The one thing a caller must never be left to guess."""
    name = "hidden-check-silent"
    isolation = ""

findings = conformance.check(SilentSandbox())
assert findings, "conformance.check() found nothing wrong with an adapter that names no isolation"
assert any("isolation" in f.lower() for f in findings), f"findings did not mention isolation: {findings}"
exit_code = 1 if findings else 0
assert exit_code == 1, "main()'s own exit-code logic would have passed this adapter"
PY

# --- h-09 a trace that is present but out of lifecycle order is actually rejected ------------
py "$AREA" <<'PY' && ok "h-09 conformance.check() rejects a trace that holds valid states in the wrong order" || bad "h-09 the trace-order gate passed a broken adapter"
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from adapters.dryrun import DryRunSandbox
import conformance

class OutOfOrderSandbox(DryRunSandbox):
    """Built here, not shipped with the area: every state it reports is a real STATUS_VALUES
    member, but recorded out of lifecycle order -- the one thing the isolation-string check
    cannot catch, and the newest thing conformance.check() added to guard against."""
    name = "hidden-check-outoforder"

    def run(self, bundle, unit):
        handle = f"{self.name}-{bundle.digest}-{unit.unit_id}"
        self._trace[handle] = ["running", "creating"]  # both valid states, wrong order
        return handle

findings = conformance.check(OutOfOrderSandbox())
assert findings, "conformance.check() found nothing wrong with a trace recorded out of order"
assert any("order" in f.lower() for f in findings), f"no finding named the ordering problem: {findings}"
PY

# --- h-10 `profile`, the one word the card grants the caller, has no path to a bundle --------
py "$AREA" <<'PY' && ok "h-10 profile can reach bundle selection" || bad "h-10 unpack(image) admits no profile parameter, so the caller's one configurable word can never pick a different default bundle"
import inspect as _i
import sys
area = sys.argv[1]
sys.path.insert(0, area)
from interface import RuntimeSandbox

sig = _i.signature(RuntimeSandbox.unpack)
try:
    sig.bind(None, "registry.example/agent-base:2026-09", profile="hidden-check-alt-profile")
    can_select = True
except TypeError:
    can_select = False

assert can_select, (
    "RuntimeSandbox.unpack(self, image) has no parameter for `profile`, and the caller (call.py) "
    "resolves the bundle once, before any Unit -- and therefore any profile -- exists. The card's "
    "usage section grants the caller exactly one configurable word, `profile`, to pick a different "
    "default bundle when the platform's choice is wrong; as declared, that word can structurally "
    "never reach bundle selection. Either profile needs a path to unpack, or the field is "
    "unimplementable as specified.")
PY

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
