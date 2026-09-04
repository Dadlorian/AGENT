#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "run".
#
# Held out from examples/run/ on purpose: the grader is never visible to the
# graded (F-b1-07). examples/run/test.sh is the area's visible feedback
# surface; this script is what decides, and the author of the example never
# sees it. Every assertion here reads a value back from a ledger record, a
# contract mount, a rendered manifest or an exit status - never a log line the
# example wrote about itself.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/run.sh
#
# Python 3.11 standard library only. No network.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/run"
WORK="${TMPDIR:-/tmp}/hidden-run-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
run() { if "$@" >/dev/null 2>&1; then return 0; else return $?; fi; }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/run/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# --- h-01 the six-part README shape, in order --------------------------------
py "$AREA" <<'PY' && ok "h-01 README carries the six headings in order" || bad "h-01 README shape"
import re, sys
head = [l.strip() for l in open(sys.argv[1] + "/README.md") if l.startswith("## ")]
want = ["ideal", "standards", "the call", "what the user sees", "composition", "extension points"]
got = [re.sub(r"^##\s*\d*\.?\s*", "", h).strip().lower() for h in head]
assert len(got) == 6, f"expected 6 top headings, got {len(got)}: {got}"
assert got == want, got
PY

# --- h-02 four doors on disk, all validating against the published schema ----
py "$ROOT" <<'PY' && ok "h-02 four entry documents validate against the reference entry schema" || bad "h-02 doors do not validate"
import importlib.util, json, os, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("e2e", os.path.join(root, "examples", "end-to-end", "run.py"))
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
schema = json.load(open(os.path.join(root, "examples", "end-to-end", "schemas", "entry.schema.json")))
kinds = set()
for door in ("human", "event", "schedule", "external"):
    path = os.path.join(root, "examples", "run", "entries", f"{door}.json")
    assert os.path.exists(path), f"door {door} is described but not on disk"
    doc = json.load(open(path))
    errs = ref.validate(doc, schema)
    assert not errs, f"{door}: {errs}"
    assert doc["kind"] == door, (door, doc["kind"])
    kinds.add(doc["kind"])
assert kinds == {"human", "event", "schedule", "external"}, kinds
PY

# --- run all four doors, plus the two breakages, into our own ledgers --------
for d in human event schedule external; do
  python3 "$AREA/run.py" --entry "$AREA/entries/$d.json" --ledger "$WORK/$d.jsonl" > "$WORK/$d.log" 2>&1
  echo "$?" > "$WORK/$d.rc"
done
python3 "$AREA/run.py" --entry "$AREA/entries/human.json" --widen-contract --attempts 1 \
  --ledger "$WORK/widen.jsonl" > "$WORK/widen.log" 2>&1; echo "$?" > "$WORK/widen.rc"
python3 "$AREA/run.py" --entry "$AREA/entries/human.json" --stuck \
  --ledger "$WORK/stuck.jsonl" > "$WORK/stuck.log" 2>&1; echo "$?" > "$WORK/stuck.rc"

# --- h-03 one unit, one envelope shape, four doors ---------------------------
py "$WORK" "$AREA" <<'PY' && ok "h-03 four doors, one declared contract, one candidate, four actors, four correlation ids" || bad "h-03 the doors do not converge on one unit"
import json, os, sys
work, area = sys.argv[1], sys.argv[2]
doors = ("human", "event", "schedule", "external")
for d in doors:
    assert open(os.path.join(work, f"{d}.rc")).read().strip() == "0", f"{d} did not exit 0"
rows = {d: [json.loads(l) for l in open(os.path.join(work, f"{d}.jsonl"))] for d in doors}
declared, cand, actors, corrs = {}, {}, set(), set()
for d, v in rows.items():
    corr = next(iter({r["correlation_id"] for r in v}))
    corrs.add(corr)
    actors.add(next(iter({r["actor"] for r in v})))
    manifest = json.load(open(os.path.join(area, "out", "units", corr, "contract-manifest-1.json")))
    declared[d] = tuple(sorted((e["path"], e["digest"]) for e in manifest["entries"]
                               if e["path"] not in ("intent.json", "folded-outcome.json")))
    cand[d] = [r["candidate_digest"] for r in v if r["kind"] == "attempt-recorded"][-1]
    assert declared[d], f"{d} rendered an empty contract"
assert len(set(declared.values())) == 1, f"the declared contract differs by door: {declared}"
assert len(set(cand.values())) == 1, f"four doors produced different subjects: {cand}"
assert len(actors) == 4, actors
assert len(corrs) == 4, corrs
PY

# --- h-04 the named ledger records exist, in the order the design requires ---
py "$WORK" <<'PY' && ok "h-04 every named record appears and the contract digest is ledgered before the cell" || bad "h-04 receipt incomplete or out of order"
import json, os, sys
rows = [json.loads(l) for l in open(os.path.join(sys.argv[1], "human.jsonl"))]
kinds = [r["kind"] for r in rows]
for want in ("unit-submitted", "contract-sealed", "cell-admitted", "turn-started", "capability-call",
             "output-sealed", "visible-checks", "cell-terminated", "check-report",
             "attempt-recorded", "unit-completed"):
    assert want in kinds, f"no {want} record in the receipt"
caps = {r["capability"] for r in rows if r["kind"] == "capability-call"}
assert caps == {"capability-packaging", "tool-access", "model-access"}, caps
seal = [r for r in rows if r["kind"] == "contract-sealed"]
admit = [r for r in rows if r["kind"] == "cell-admitted"]
assert len(seal) == len(admit) >= 1, (len(seal), len(admit))
for s, a in zip(seal, admit):
    assert s["seq"] < a["seq"], "a cell was admitted before its contract digest was ledgered"
    assert s["contract_digest"] == a["contract_digest"], (s["contract_digest"], a["contract_digest"])
assert len({s["stable_prefix_digest"] for s in seal}) == 1, "the stable prefix moved between attempts"
for r in rows:
    assert r.get("run_id") and r.get("correlation_id") and r.get("actor"), f"record with no correlation: {r['kind']}"
PY

# --- h-05 the visible set is green while the deciding set is red -------------
py "$WORK" <<'PY' && ok "h-05 attempt 1 passes every visible check and still fails a deciding check" || bad "h-05 the visible set decided"
import json, os, sys
rows = [json.loads(l) for l in open(os.path.join(sys.argv[1], "human.jsonl"))]
vis = [r for r in rows if r["kind"] == "visible-checks"][0]
rep = [r for r in rows if r["kind"] == "check-report"][0]
assert vis["outcomes"] and all(o["outcome"] == "pass" for o in vis["outcomes"]), vis
assert vis["decides"] is False, "a visible check claimed to decide"
assert rep["outcome"] == "failed", "the deciding set agreed with the visible set on attempt 1"
assert rep["behavioural_run"] > 0 and rep["checks_run"] > rep["behavioural_run"], rep
PY

# --- h-06 the deliberate breakage is caught by a deciding check --------------
py "$WORK" <<'PY' && ok "h-06 a contract widened after its digest was ledgered does not complete" || bad "h-06 the breakage passed"
import json, os, sys
work = sys.argv[1]
assert open(os.path.join(work, "widen.rc")).read().strip() == "3", "a widened contract completed"
rows = [json.loads(l) for l in open(os.path.join(work, "widen.jsonl"))]
rep = [r for r in rows if r["kind"] == "check-report"][-1]
assert rep["outcome"] == "failed", rep
PY

# --- h-07 escalation is evidence-gated and parks rather than stopping --------
py "$WORK" <<'PY' && ok "h-07 one evidence-gated class step, then an approval gate at input-required" || bad "h-07 escalation or parking wrong"
import json, os, sys
work = sys.argv[1]
assert open(os.path.join(work, "stuck.rc")).read().strip() == "3", "an attempter that never learns completed"
rows = [json.loads(l) for l in open(os.path.join(work, "stuck.jsonl"))]
esc = [r for r in rows if r["kind"] == "escalated"]
att = [r for r in rows if r["kind"] == "attempt-recorded"]
park = [r for r in rows if r["kind"] == "approval-parked"]
assert len(esc) == 1, f"expected exactly one class step, got {len(esc)}"
assert att[0]["cold"] is True, "no attempt of the unit ran cold"
assert att[0]["model_class"] == att[1]["model_class"], "the class stepped before the evidence repeated"
assert att[-1]["model_class"] != att[0]["model_class"], "the class never stepped"
assert park and park[0]["state"] == "input-required", "the ceiling fired and nothing parked"
PY

# --- h-08 the loop bound lives on the declaration, never inside the loop -----
py "$AREA" "$WORK" <<'PY' && ok "h-08 escalation.class_steps_permitted on the declaration decides the class step" || bad "h-08 the class-step bound is not read from the declaration"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
doc = json.load(open(os.path.join(area, "units", "fix-checkout-coupon-500s.json")))
doc["escalation"]["class_steps_permitted"] = 0
path = os.path.join(work, "no-step.json")
json.dump(doc, open(path, "w"))
ledger = os.path.join(work, "nostep.jsonl")
subprocess.run([sys.executable, os.path.join(area, "run.py"),
                "--entry", os.path.join(area, "entries", "human.json"),
                "--unit", path, "--stuck", "--ledger", ledger],
               capture_output=True, text=True)
rows = [json.loads(l) for l in open(ledger)]
esc = [r for r in rows if r["kind"] == "escalated"]
classes = {r["model_class"] for r in rows if r["kind"] == "attempt-recorded"}
assert not esc, ("a unit declaring class_steps_permitted 0 stepped its class anyway; the bound is "
                 f"hardcoded in the loop rather than read from the document: {esc}")
assert len(classes) == 1, f"the class moved though no class step was permitted: {classes}"
PY

# --- h-09 the criterion never reaches anything the unit can read -------------
py "$AREA" "$WORK" <<'PY' && ok "h-09 no criterion body, held-out fixture or check name reaches a contract mount" || bad "h-09 the grader leaked to the graded"
import importlib.util, os, sys
area, work = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("assessor_hidden", os.path.join(area, "assessor.py"))
assessor = importlib.util.module_from_spec(spec); spec.loader.exec_module(assessor)

# What the deciding set knows: the names of its check bodies and the literal
# fixtures they exercise. Anything the visible surface already publishes is not
# a leak - the deciding checks cover the same observable behaviour on purpose -
# so the visible surface is subtracted and what is left is held out by
# construction: if it appears on a mount or in caller output, it escaped.
visible = ""
for path in (os.path.join(area, "contract", "checks.visible.json"),
             os.path.join(area, "source", "tests", "test_coupon_visible.py"),
             os.path.join(area, "contract", "system.md")):
    if os.path.exists(path):
        visible += open(path, errors="ignore").read()
held = set()
for ref, checks in assessor.CRITERIA.items():
    for c in checks:
        held.add(c["run"].__name__)
        for k in c["run"].__code__.co_consts:
            if isinstance(k, str) and len(k) > 3:
                held.add(k)
held = {h for h in held if h and h not in visible}
assert held, "the deciding set has no held-out detail at all; there is nothing to keep from the unit"

leaked = []
for base, _, files in os.walk(os.path.join(area, "out", "units")):
    if os.path.basename(base) != "contract" and os.sep + "contract" not in base:
        continue
    for name in files:
        text = open(os.path.join(base, name), errors="ignore").read()
        leaked += [(os.path.join(base, name), h) for h in held if h in text]
assert not leaked, f"held-out criterion detail inside a contract mount: {sorted(set(leaked))[:5]}"
for door in ("human", "widen", "stuck"):
    text = open(os.path.join(work, f"{door}.log"), errors="ignore").read()
    escaped = [h for h in held if h in text]
    assert not escaped, f"held-out criterion detail reached the caller in {door}.log: {escaped}"
PY

# --- h-10 the receipt is tamper-evident --------------------------------------
python3 "$AREA/run.py" --verify-ledger --ledger "$WORK/human.jsonl" > "$WORK/verify.log" 2>&1
V=$?
sed '5s/"cost_micros": [0-9]*/"cost_micros": 1/' "$WORK/human.jsonl" > "$WORK/tampered.jsonl"
python3 "$AREA/run.py" --verify-ledger --ledger "$WORK/tampered.jsonl" > "$WORK/tamper.log" 2>&1
T=$?
if [ "$V" -eq 0 ] && [ "$T" -ne 0 ]; then ok "h-10 the chain verifies and a one-character edit is detected"
else bad "h-10 ledger verify=$V tampered=$T"; fi

# --- h-11 no product name outside the standards table and the adapter rows ---
py "$AREA" <<'PY' && ok "h-11 no product or vendor name outside the standards table and the adapter rows" || bad "h-11 a product name escaped its column"
import os, re, sys
area = sys.argv[1]
NAMES = re.compile(r"firecracker|gvisor|kata containers|cloud hypervisor|goose|litellm|openrouter|"
                   r"openai|anthropic|claude|gemini|cursor|jetbrains|vllm|sglang|temporal|"
                   r"kubernetes|docker|systemd", re.I)
ALLOWED = ("## 2. Standards", "### Adapters")
bad_rows = []
block, allowed = "", False
for i, line in enumerate(open(os.path.join(area, "README.md")), 1):
    if line.startswith("## ") or line.startswith("### "):
        block = line.strip()
        allowed = any(block.startswith(a) for a in ALLOWED)
    if not allowed:
        m = NAMES.search(line)
        if m:
            bad_rows.append(("README.md", i, m.group(0)))
for base, dirs, files in os.walk(area):
    dirs[:] = [d for d in dirs if d not in ("out", "__pycache__")]
    for name in files:
        if not name.endswith((".py", ".json", ".md", ".sh")) or name == "README.md":
            continue
        full = os.path.join(base, name)
        for i, line in enumerate(open(full, errors="ignore"), 1):
            if "grep" in line:            # a test asserting the rule may name what it forbids
                continue
            m = NAMES.search(line)
            if m:
                bad_rows.append((os.path.relpath(full, area), i, m.group(0)))
assert not bad_rows, f"product names outside their column: {bad_rows[:6]}"
PY

# --- h-12 the visible check counts something ---------------------------------
bash "$AREA/test.sh" > "$WORK/visible.log" 2>&1
VRC=$?
py "$WORK" <<'PY' && ok "h-12 the visible check counts at least 20 checks and fails none" || bad "h-12 the visible check counted too little"
import os, re, sys
line = [l for l in open(os.path.join(sys.argv[1], "visible.log")) if l.startswith("passed ")]
assert line, "test.sh printed no `passed N, failed M` line"
n, m = map(int, re.match(r"passed (\d+), failed (\d+)", line[-1].strip()).groups())
assert m == 0, f"the visible check failed {m}"
assert n >= 20, f"the visible check counted only {n} checks; a run that counts nothing is not a pass"
PY
if [ "$VRC" -eq 0 ]; then ok "h-13 the visible check exits 0"; else bad "h-13 the visible check exited $VRC"; fi

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
