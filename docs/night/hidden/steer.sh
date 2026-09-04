#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "steer".
#
# Held out from examples/steer/ on purpose: the grader is never visible to the
# graded (F-b1-07). examples/steer/test.sh is that area's visible feedback
# surface; this script is what decides, and the author of the example never
# sees it. Every assertion reads a value back out of a report the runner wrote,
# a ledger record, an exit status or a source file - never a sentence the
# example wrote about itself, and never a counter the runner assigned as a
# literal.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/steer.sh
#
# Python 3.11 standard library only. No network.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/steer"
WORK="${TMPDIR:-/tmp}/hidden-steer-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"; rm -f "$AREA"/out/hid-*.jsonl; rm -rf "$AREA"/out/asks/hid-*' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/steer/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# --- the visible surface runs first: h-09 reads it, and h-13 needs the
#     ledgers its named steps refer to ----------------------------------------
( cd "$AREA" && bash test.sh ) > "$WORK/visible.log" 2>&1
VRC=$?

# --- our own runs, into our own ledgers --------------------------------------
hrun() {  # hrun <name> <args...>
  n="$1"; shift
  python3 "$AREA/run.py" "$@" --ledger "$AREA/out/hid-$n.jsonl" \
      --report "$WORK/$n.json" > "$WORK/$n.log" 2>&1
  echo "$?" > "$WORK/$n.rc"
}
for d in human event schedule external; do hrun "$d" --entry "$AREA/entries/$d.json"; done
hrun revise --entry "$AREA/entries/human.json" --revise-policy
hrun carry  --entry "$AREA/entries/human.json" --revise-policy --carry-decision
hrun late   --entry "$AREA/entries/schedule.json" --decision approve --delay 400
hrun early  --entry "$AREA/entries/schedule.json" --decision none --delay 10
for p in admission.entry dispatch.model_call dispatch.tool_call steer.decision steer.intervention; do
  hrun "down-$(echo "$p" | tr '.' '-')" --entry "$AREA/entries/event.json" --engine-down-at "$p"
done

# --- h-01 the six-part README shape, in order --------------------------------
py "$AREA" <<'PY' && ok "h-01 README carries the six headings in order" || bad "h-01 README shape"
import re, sys
head = [l.strip() for l in open(sys.argv[1] + "/README.md") if l.startswith("## ")]
want = ["ideal", "standards", "the call", "what the user sees", "composition", "extension points"]
got = [re.sub(r"^##\s*\d*\.?\s*", "", h).strip().lower() for h in head]
assert got == want, got
PY

# --- h-02 four doors on disk, both documents validating -----------------------
py "$ROOT" <<'PY' && ok "h-02 four entries and four steer declarations validate with the reference validator" || bad "h-02 the doors do not validate"
import importlib.util, json, os, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("e2e", os.path.join(root, "examples", "end-to-end", "run.py"))
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
entry_schema = json.load(open(os.path.join(root, "examples", "end-to-end", "schemas", "entry.schema.json")))
steer_schema = json.load(open(os.path.join(root, "examples", "steer", "schemas", "steer.schema.json")))
actors, corrs, refs = set(), set(), set()
for door in ("human", "event", "schedule", "external"):
    path = os.path.join(root, "examples", "steer", "entries", f"{door}.json")
    assert os.path.exists(path), f"door {door} is described but not on disk"
    doc = json.load(open(path))
    assert doc["kind"] == door, (door, doc["kind"])
    assert not ref.validate(doc, entry_schema), ref.validate(doc, entry_schema)
    steer = doc.get("payload", {}).get("steer")
    assert steer is not None, f"{door} carries no payload.steer"
    assert not ref.validate(steer, steer_schema), ref.validate(steer, steer_schema)
    actors.add(doc["actor"]["subject"]); corrs.add(doc["correlation"]["correlation_id"])
    refs.add(doc["intent"]["workflow_ref"])
assert len(actors) == len(corrs) == 4, (actors, corrs)
assert len(refs) == 1, f"the four doors do not converge on one task specification: {refs}"
PY

# --- h-03 one unit, four doors, one decision on the effect --------------------
py "$WORK" "$AREA" <<'PY' && ok "h-03 the four doors decide the same effect the same way, and each ends as its own declaration says" || bad "h-03 the doors diverge"
import json, os, sys
work, area = sys.argv[1], sys.argv[2]
seen = set()
for door in ("human", "event", "schedule", "external"):
    rep = json.load(open(os.path.join(work, f"{door}.json")))
    steer = json.load(open(os.path.join(area, "entries", f"{door}.json")))["payload"]["steer"]
    row = [r for r in rep["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
    seen.add((row["decision_point"], row["action"], row["effect"], row["rule_id"],
              json.dumps(row["resource"], sort_keys=True)))
    if steer["decision"] == "approve":
        assert rep["status"] == "completed" and rep["run"]["effect_fired"] is True, door
    if steer["decision"] == "none":
        assert rep["status"] == "failed" and rep["run"]["effect_fired"] is False, door
        assert any(r["type"].endswith("deadline-exceeded") for r in rep["run"]["refusals"]), door
    if steer["decision"] == "reject":
        assert rep["run"]["escalations"] >= 1, f"{door} spent its attempts and never escalated"
assert len(seen) == 1, seen
PY

# --- h-04 the receipt: every record stamped, and every kind the runner can
#         emit is named in the README's own enumeration ------------------------
py "$WORK" "$AREA" <<'PY' && ok "h-04 every record is stamped and every emitted record kind is named in the README" || bad "h-04 the receipt is unstamped or under-enumerated"
import json, os, re, sys
work, area = sys.argv[1], sys.argv[2]
stamps = ("run_id", "correlation_id", "actor", "delegation_depth", "entry_kind", "idempotency_key")
emitted = set()
for name in ("human", "event", "schedule", "external", "revise", "carry"):
    path = os.path.join(area, "out", f"hid-{name}.jsonl")
    if not os.path.exists(path):
        continue
    for line in open(path):
        rec = json.loads(line)
        emitted.add(rec["kind"])
        for field in stamps:
            assert field in rec, (name, rec["kind"], field)
readme = open(os.path.join(area, "README.md")).read()
receipt = [l for l in readme.splitlines() if "out/*.jsonl" in l]
assert receipt, "the README has no receipt row naming the record kinds"
named = set(re.findall(r"`([a-z][a-z-]+)`", receipt[0])) | set(
    re.findall(r"([a-z][a-z-]+)", receipt[0].replace("`", " ")))
missing = sorted(k for k in emitted if k not in named)
assert not missing, f"record kinds the runner emits and the README does not name: {missing}"
PY

# --- h-05 a declared value is read at the point of decision, or written up ----
py "$WORK" "$AREA" <<'PY' && ok "h-05 correlation.depth changes a record, or is written up as carried and not consumed" || bad "h-05 a declared value is decoration"
import copy, json, os, re, subprocess, sys
work, area = sys.argv[1], sys.argv[2]
base = json.load(open(os.path.join(area, "entries", "external.json")))
a = copy.deepcopy(base); a["correlation"]["depth"] = 99
b = copy.deepcopy(base); b["correlation"].pop("depth", None)
out = {}
for tag, doc in (("d99", a), ("dnil", b)):
    p = os.path.join(work, f"{tag}.json")
    json.dump(doc, open(p, "w"))
    subprocess.run([sys.executable, os.path.join(area, "run.py"), "--entry", p,
                    "--ledger", os.path.join(area, "out", f"hid-{tag}.jsonl"),
                    "--report", os.path.join(work, f"{tag}.rep.json")],
                   capture_output=True)
    rep = json.load(open(os.path.join(work, f"{tag}.rep.json")))
    out[tag] = (rep["status"], rep["run"]["disposition"], rep["run"]["effect_fired"],
                [(r["decision_point"], r["action"], r["effect"], r["rule_id"]) for r in rep["decisions"]],
                [x["type"] for x in rep["run"]["refusals"]])
readme = open(os.path.join(area, "README.md")).read()
block = readme.split("### Carried and not consumed")[-1].split("###")[0] if \
    "### Carried and not consumed" in readme else ""
written_up = "correlation.depth" in block or re.search(r"\|\s*`?depth`?\s*\|", block) is not None
assert out["d99"] != out["dnil"] or written_up, (
    "correlation.depth is declared on every entry and advertised in section 3, no record "
    "changes when it is set to 99 or deleted, and it is not in the carried-and-not-consumed table")
PY

# --- h-06 an allow is spent, counted out of the decision rows ------------------
py "$WORK" "$AREA" <<'PY' && ok "h-06 the resumed effect is decided again, and carrying the pre-pause allow is caught" || bad "h-06 the allow outlives its action"
import json, os, sys
work, area = sys.argv[1], sys.argv[2]
honest = json.load(open(os.path.join(work, "revise.json")))
broken = json.load(open(os.path.join(work, "carry.json")))
plain = json.load(open(os.path.join(work, "human.json")))
count = lambda rep: len([r for r in rep["decisions"] if r["decision_point"] == "dispatch.tool_call"])
assert count(plain) == 2, f"the effect was decided {count(plain)} time(s) on an unrevised run"
assert count(honest) == 2, count(honest)
assert count(broken) == 1, f"the breakage still took {count(broken)} effect decisions"
after = [r for r in honest["decisions"] if r["decision_point"] == "dispatch.tool_call"][-1]
before = [r for r in honest["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
assert (before["effect"], after["effect"]) == ("allow", "deny"), (before, after)
assert before["policy_version"] != after["policy_version"], "one version served both decisions"
assert honest["status"] == "failed" and honest["run"]["effect_fired"] is False
rows = [json.loads(l) for l in open(os.path.join(area, "out", "hid-revise.jsonl"))]
assert not [r for r in rows if r["kind"] == "effect-applied"], "the frozen effect was applied"
brows = [json.loads(l) for l in open(os.path.join(area, "out", "hid-carry.jsonl"))]
applied = [r for r in brows if r["kind"] == "effect-applied"]
assert applied and applied[0]["decided_again"] is False, applied
PY

# --- h-07 the deadline, in both directions, typed either way ------------------
py "$WORK" <<'PY' && ok "h-07 a late decision is a typed 504 and an early sweep is a typed refusal, not a traceback" || bad "h-07 a legal declaration produced an untyped failure"
import json, os, sys
work = sys.argv[1]
late = json.load(open(os.path.join(work, "late.json")))
assert late["status"] == "failed" and late["run"]["effect_fired"] is False, late["status"]
assert any(r["type"].endswith("deadline-exceeded") and r["status"] == 504
           for r in late["run"]["refusals"]), late["run"]["refusals"]
log = open(os.path.join(work, "early.log")).read()
rc = open(os.path.join(work, "early.rc")).read().strip()
assert "Traceback" not in log, (
    "a schema-valid steer declaration (decision 'none' with a delay inside the deadline) "
    "ended in an uncaught exception instead of a problem object:\n" + log[-400:])
assert "application/problem+json" in log, log[-400:]
assert rc != "0", rc
PY

# --- h-08 fail closed at every registered enforcement point -------------------
py "$WORK" <<'PY' && ok "h-08 an unreachable engine refuses at all five points, records undecided, and runs nothing" || bad "h-08 a point did not fail closed"
import json, os, sys
work = sys.argv[1]
points = ("admission.entry", "dispatch.model_call", "dispatch.tool_call",
          "steer.decision", "steer.intervention")
for point in points:
    rep = json.load(open(os.path.join(work, "down-" + point.replace(".", "-") + ".json")))
    rows = rep["decisions"]
    undecided = [r for r in rows if r["effect"] == "undecided"]
    assert undecided, f"{point}: nothing was refused"
    first = undecided[0]
    assert first["decision_point"] == point, (point, first["decision_point"])
    assert first["problem_type"].endswith("adapter-unavailable"), first
    assert first["work_ran"] is False, first
    assert first["spend_after_micros"] == first["spend_before_micros"], first
    assert first["rule_id"] == "-", first
    assert rep["status"] in ("rejected", "failed"), (point, rep["status"])
PY

# --- h-09 the visible check counts something, and gates on the count ----------
py "$WORK" "$AREA" <<'PY' && ok "h-09 the visible check counts at least 40, fails none, and its gate has a floor" || bad "h-09 the visible gate can be structurally green and mean nothing"
import json, os, re, sys
work, area = sys.argv[1], sys.argv[2]
lines = [l for l in open(os.path.join(work, "visible.log")) if l.startswith("passed ")]
assert lines, "test.sh printed no `passed N, failed M` line"
n, m = map(int, re.match(r"passed (\d+), failed (\d+)", lines[-1].strip()).groups())
assert m == 0, f"the visible check failed {m}"
assert n >= 40, f"the visible check counted only {n}"
body = open(os.path.join(area, "test.sh")).read()
floor = re.search(r"^FLOOR=(\d+)$", body, re.M)
assert floor, "test.sh declares no floor, so a gutted copy that counts nothing exits 0"
assert re.search(r'\[\s*"\$PASS"\s*-ge\s*"\$FLOOR"\s*\]', body), "the floor is declared and never gated on"
assert re.search(r'\[\s*"\$FAIL"\s*-eq\s*0\s*\]', body), "the gate does not fail on a failure"
declared = json.load(open(os.path.join(area, "provenance.json")))["visible_checks_counted"]
assert declared == int(floor.group(1)) == n, (declared, floor.group(1), n)
PY

# --- h-10 every quote is verbatim in the record it is attributed to -----------
py "$ROOT" "$AREA" <<'PY' && ok "h-10 every id-attributed quote in the README is verbatim in that record" || bad "h-10 a quote is not the text of the id it is attributed to"
import glob, json, os, re, sys
root, area = sys.argv[1], sys.argv[2]
def norm(s):
    s = s.replace("\\|", "|").replace('\\"', '"').replace("*", "")
    return re.sub(r"\s+", " ", s).strip()
index = {}
sources = ["kb/facts.jsonl", "kb/target-facts.jsonl", "kb/reference-facts.jsonl", "kb/research.jsonl"]
sources += sorted(glob.glob(os.path.join(root, "kb", "research", "*.jsonl")))
for rel in sources:
    path = rel if os.path.isabs(rel) else os.path.join(root, rel)
    if not os.path.exists(path):
        continue
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("id"):
            index.setdefault(rec["id"], []).append(norm(json.dumps(rec, ensure_ascii=False)))
text = open(os.path.join(area, "README.md")).read()
pairs = re.findall(r"`([FTXER]-[a-z][a-z0-9]*-[a-z0-9-]+)`\s*\"((?:[^\"]|\\\")+)\"", text)
assert len(pairs) >= 20, f"only {len(pairs)} id-attributed quotes found"
wrong = []
for ident, quote in pairs:
    if ident not in index:
        wrong.append((ident, "no such record")); continue
    for fragment in quote.split("…"):
        fragment = norm(fragment)
        if len(fragment) < 10:
            continue
        if not any(fragment in blob for blob in index[ident]):
            wrong.append((ident, fragment[:120]))
assert not wrong, f"quotes not verbatim in the record cited: {wrong[:4]}"
PY

# --- h-11 no product or policy-language name outside its column ---------------
py "$AREA" <<'PY' && ok "h-11 no product, engine or policy-language name outside the standards and adapter tables" || bad "h-11 a product name reached the caller"
import os, re, sys
area = sys.argv[1]
NAMES = re.compile(r"\b(opa|rego|cedar|styra|openfga|firecracker|gvisor|kubernetes|docker|"
                   r"openai|anthropic|langfuse|temporal|spiffe)\b", re.I)
bad_rows = []
for root, dirs, files in os.walk(area):
    dirs[:] = [d for d in dirs if d not in ("out", "__pycache__")]
    for name in files:
        if not name.endswith((".py", ".sh", ".json")):
            continue
        full = os.path.join(root, name)
        for i, line in enumerate(open(full, errors="ignore"), 1):
            if "grep" in line:            # a check asserting the rule may name what it forbids
                continue
            m = NAMES.search(line)
            if m:
                bad_rows.append((os.path.relpath(full, area), i, m.group(0)))
readme = open(os.path.join(area, "README.md")).read().splitlines()
allowed = False
for i, line in enumerate(readme, 1):
    if line.startswith("## 2."):
        allowed = True
    elif line.startswith("## ") and not line.startswith("## 2."):
        allowed = False
    if line.startswith("### Adapters"):
        allowed = True
    elif line.startswith("### ") and not line.startswith("### Adapters"):
        allowed = allowed and not line.startswith("### ")
    m = NAMES.search(line)
    if m and not allowed:
        bad_rows.append(("README.md", i, m.group(0)))
assert not bad_rows, f"product names outside their column: {bad_rows[:6]}"
PY

# --- h-12 no count is written that was not read out of the artifact -----------
py "$WORK" "$AREA" <<'PY' && ok "h-12 the record-kind counts in the README and provenance match the ledgers" || bad "h-12 a count was written that no artifact carries"
import json, os, re, sys
work, area = sys.argv[1], sys.argv[2]
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
         "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}
per_ledger = {}
for name in os.listdir(os.path.join(area, "out")):
    if not (name.startswith("hid-") and name.endswith(".jsonl")):
        continue
    kinds = {json.loads(l)["kind"] for l in open(os.path.join(area, "out", name)) if l.strip()}
    per_ledger[name] = len(kinds)
assert per_ledger, "no ledger was produced to read a count out of"
biggest = max(per_ledger.values())
blobs = [(("provenance.json"), json.dumps(json.load(open(os.path.join(area, "provenance.json"))))),
         (("README.md"), open(os.path.join(area, "README.md")).read())]
claims = []
for where, blob in blobs:
    for m in re.finditer(r"(\b[a-z]+\b|\b\d+\b) record kinds", blob):
        token = m.group(1)
        value = WORDS.get(token, int(token) if token.isdigit() else None)
        if value is None:
            continue
        if value > biggest:
            claims.append((where, m.group(0), f"largest ledger carries {biggest}"))
assert not claims, f"counts no artifact supports: {claims}"
PY

# --- h-13 the run steps are runnable as they are printed ----------------------
rm -f "$AREA/out/run.jsonl"; rm -rf "$AREA/out/asks/run"
py "$AREA" "$ROOT" "$WORK" <<'PY' && ok "h-13 the README's run steps run in the order they are listed" || bad "h-13 a documented run step refuses when the one before it has run"
import os, re, subprocess, sys
area, root, work = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(os.path.join(area, "README.md")).read()
table = text.split("### Run steps")[-1].split("## ")[0]
cmds = []
for line in table.splitlines():
    cells = [c.strip() for c in line.split("|")]
    if len(cells) < 5 or not cells[1].isdigit():
        continue
    m = re.search(r"`([^`]+)`", cells[3])
    if m and m.group(1).startswith("python3 "):
        cmds.append((cells[1], m.group(1)))
assert len(cmds) >= 4, f"only {len(cmds)} runnable steps parsed from the table"
broken = []
for step, cmd in cmds:
    proc = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
    blob = proc.stdout + proc.stderr
    # a refusal folded into the record is expected; a refusal that *ends* the
    # step is printed as the problem body and leaves the step showing nothing
    terminal = blob.split("PROBLEM (application/problem+json)")[1] if \
        "PROBLEM (application/problem+json)" in blob else ""
    if "idempotency-conflict" in terminal or "Traceback" in blob:
        broken.append((step, cmd, (terminal or blob).strip().splitlines()[0][:90]))
assert not broken, f"steps that cannot be run as printed: {broken[:4]}"
PY

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
