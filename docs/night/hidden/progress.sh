#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "progress".
#
# Held out from examples/progress/ on purpose: the grader is never visible to
# the graded (F-b1-07). examples/progress/test.sh is the area's visible feedback
# surface; this script is what decides, and the author of the example never sees
# it. Every assertion reads a value back from a report, a ledger record, an
# executor state directory or a process exit status - never a log line the
# example wrote about itself, and never a count the example spells out.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/progress.sh
#
# Python 3.11 standard library only. No network. Nothing is written inside the
# example: every run this script starts is given its own ledger, report and
# state directory under $WORK.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/progress"
WORK="${TMPDIR:-/tmp}/hidden-progress-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/progress/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# One run of one door, into $WORK. $1 names the run, $2.. is the rest of the
# command line. The exit status is recorded beside the report so that h-04 can
# read the two together from outside the process that produced them.
door() {
  name="$1"; shift
  ( cd "$ROOT" && python3 examples/progress/run.py \
      --ledger "$WORK/$name.jsonl" --report "$WORK/$name.rep.json" \
      --out "$WORK/$name.state" "$@" > "$WORK/$name.log" 2>&1 )
  echo "$?" > "$WORK/$name.rc"
}

for d in human event schedule external; do
  door "$d" --entry "$AREA/entries/$d.json"
done

# The visible check is run once, here, so that h-11 can read the artifacts a full
# suite leaves behind rather than the handful this script starts itself.
( cd "$AREA" && bash test.sh ) > "$WORK/visible.log" 2>&1
VRC=$?

# --- h-01 the six-part README shape, in order --------------------------------
py "$AREA" <<'PY' && ok "h-01 README carries the six headings in order" || bad "h-01 README shape"
import re, sys
head = [l.strip() for l in open(sys.argv[1] + "/README.md") if l.startswith("## ")]
want = ["ideal", "standards", "the call", "what the user sees", "composition", "extension points"]
got = [re.sub(r"^##\s*\d*\.?\s*", "", h).strip().lower() for h in head]
assert got == want, got
PY

# --- h-02 four doors, one published entry shape, two schemas -----------------
py "$ROOT" <<'PY' && ok "h-02 four entries and four progress declarations validate" || bad "h-02 a door does not validate"
import importlib.util, json, os, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("e2e", os.path.join(root, "examples", "end-to-end", "run.py"))
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
entry = json.load(open(os.path.join(root, "examples", "end-to-end", "schemas", "entry.schema.json")))
prog = json.load(open(os.path.join(root, "examples", "progress", "schemas", "progress.schema.json")))
kinds, keys = set(), set()
for door in ("human", "event", "schedule", "external"):
    path = os.path.join(root, "examples", "progress", "entries", f"{door}.json")
    assert os.path.exists(path), f"door {door} is described but not on disk"
    doc = json.load(open(path))
    assert not ref.validate(doc, entry), (door, ref.validate(doc, entry))
    assert not ref.validate(doc["payload"]["progress"], prog), door
    assert doc["kind"] == door, (door, doc["kind"])
    kinds.add(doc["kind"]); keys.add(tuple(sorted(doc)))
assert kinds == {"human", "event", "schedule", "external"}, kinds
assert len(keys) == 1, f"the four doors are not one envelope shape: {keys}"
PY

# --- h-03 one declaration, four doors, one report shape ----------------------
py "$WORK" "$AREA" <<'PY' && ok "h-03 one unit through four doors yields one report shape and four identities" || bad "h-03 the four doors are not one shape"
import json, os, sys
work, area = sys.argv[1], sys.argv[2]
reps = {d: json.load(open(os.path.join(work, f"{d}.rep.json"))) for d in
        ("human", "event", "schedule", "external")}
shapes = {tuple(sorted(r)) for r in reps.values()}
assert len(shapes) == 1, "the four doors return different report shapes"
for field in ("actor", "run_id", "correlation_id"):
    got = {r[field] for r in reps.values()}
    assert len(got) == 4, f"four doors carried {len(got)} distinct {field}: {got}"
assert len({r["unit_ref"] for r in reps.values()}) == 1
refs = {json.load(open(os.path.join(area, "entries", f"{d}.json")))["intent"]["workflow_ref"]
        for d in reps}
assert len(refs) == 1, refs
PY

# --- h-04 the exit-code rule, read from outside the process ------------------
door belowfloor --entry "$WORK/e-belowfloor.json" 2>/dev/null || true
py "$WORK" "$AREA" <<'PY' && ok "h-04 exit 2 means nothing spent and exit 3 means it ran and stopped" || bad "h-04 the exit code does not follow the spend"
import copy, json, os, subprocess, sys
work, area = sys.argv[1], sys.argv[2]
# one more run, a ceiling below the plan floor, so both exit codes are exercised
env = json.load(open(os.path.join(area, "entries", "human.json")))
env = copy.deepcopy(env); env["budget"]["ceiling_micros"] = 260000
low = os.path.join(work, "e-low.json"); json.dump(env, open(low, "w"))
rc = subprocess.run([sys.executable, os.path.join(area, "run.py"), "--entry", low,
                     "--ledger", os.path.join(work, "low.jsonl"),
                     "--report", os.path.join(work, "low.rep.json"),
                     "--out", os.path.join(work, "low.state")],
                    capture_output=True, text=True).returncode
open(os.path.join(work, "low.rc"), "w").write(str(rc))
seen = {}
for name in ("human", "event", "schedule", "external", "low"):
    rc = int(open(os.path.join(work, f"{name}.rc")).read().strip())
    rep = json.load(open(os.path.join(work, f"{name}.rep.json")))
    spent, outcome = rep["budget"]["spent_micros"], rep["outcome"]
    seen[rc] = seen.get(rc, 0) + 1
    if rc == 0:
        assert outcome == "completed" and spent > 0, (name, rc, outcome, spent)
    elif rc == 2:
        assert spent == 0 and rep["problem"], f"{name}: exit 2 with {spent} spent"
    elif rc == 3:
        assert spent > 0 and outcome == "failed", f"{name}: exit 3 with {spent} spent"
    else:
        raise AssertionError(f"{name}: exit {rc} is not one of 0, 2, 3")
assert {0, 2, 3} <= set(seen), f"not every exit code was exercised: {seen}"
PY

# --- h-05 the ledger says what happened, and says it in a verifiable chain ----
py "$WORK" "$ROOT" <<'PY' && ok "h-05 the human door's receipt carries every named record kind and verifies" || bad "h-05 the receipt is missing a record kind or does not verify"
import json, os, subprocess, sys
work, root = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(os.path.join(work, "human.jsonl"))]
kinds = {r["kind"] for r in rows}
WANT = {"unit-submitted", "plan-priced", "run-bound", "stage-entered", "step-committed",
        "loop-terminated", "evaluation-gated", "approval-parked", "approval-decided",
        "effect-declared", "unwind-plan-read", "effect-sealed", "unit-completed"}
missing = sorted(WANT - kinds)
assert not missing, f"the receipt never names: {missing}"
for r in rows:                       # every record names who, which run and which door
    for field in ("run_id", "correlation_id", "actor", "entry_kind", "idempotency_key", "unit"):
        assert field in r, (r["kind"], field)
out = subprocess.run([sys.executable, os.path.join(root, "examples", "progress", "run.py"),
                      "--verify-ledger", "--ledger", os.path.join(work, "human.jsonl")],
                     capture_output=True, text=True)
assert out.returncode == 0 and "verified" in out.stdout, out.stdout + out.stderr
PY

# --- h-06 the disposition is one of the ontology's four words ----------------
py "$WORK" "$ROOT" <<'PY' && ok "h-06 every run ends on one of the ontology's four dispositions" || bad "h-06 a run ended on a word the ontology does not carry"
import glob, json, os, re, sys
work, root = sys.argv[1], sys.argv[2]
row = [l for l in open(os.path.join(root, "docs", "reference", "ontology.md"))
       if l.startswith("| Disposition")][0]
four = set(re.search(r"what happens next: ([^|]+)", row).group(1).replace(".", "").split(", "))
four = {w.strip() for w in four}
assert len(four) == 4, four
seen = set()
for path in sorted(glob.glob(os.path.join(work, "*.rep.json"))):
    d = json.load(open(path))["disposition"]
    assert d in four, f"{os.path.basename(path)} ended on {d!r}, not one of {sorted(four)}"
    seen.add(d)
assert len(seen) >= 2, seen
PY

# --- h-07 every quote in the README, not only the ones beside an id ----------
py "$AREA" "$ROOT" <<'PY' && ok "h-07 every quoted string in the README is verbatim in a record its row cites" || bad "h-07 a quoted string is not in the record the row cites"
import json, os, re, sys
area, root = sys.argv[1], sys.argv[2]
records = {}
for name in os.listdir(os.path.join(root, "kb")):
    if not name.endswith(".jsonl"):
        continue
    for line in open(os.path.join(root, "kb", name)):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("id"):
            records.setdefault(o["id"], []).append(
                " ".join(str(o.get(k) or "") for k in ("text", "snippet", "claim", "title")
                         ) + " " + " ".join(str(v) for v in (o.get("columns") or {}).values()))
for sub in ("research",):
    d = os.path.join(root, "kb", sub)
    for name in os.listdir(d) if os.path.isdir(d) else []:
        for line in open(os.path.join(d, name)):
            if line.strip():
                o = json.loads(line)
                records.setdefault(o["id"], []).append(
                    " ".join(str(o.get(k) or "") for k in ("text", "snippet", "claim", "title")))
flat = lambda s: " ".join(s.split())
bad = []
for n, line in enumerate(open(os.path.join(area, "README.md")), 1):
    ids = re.findall(r"`((?:REF|F|T|X|E|R)-[^`]+)`", line)
    quotes = [q for q in re.findall(r'"([^"]{12,})"', line)
              if "|" not in q and "`" not in q]
    if not ids or not quotes:
        continue
    bodies = []
    for cid in ids:
        if cid.startswith("REF-"):
            path = os.path.join(root, cid[4:].split("#", 1)[0])
            if os.path.exists(path):
                bodies.append(flat(open(path, errors="replace").read()))
        else:
            bodies += [flat(b) for b in records.get(cid, [])]
    for q in quotes:
        want = flat(q.replace("\\|", "|"))
        if not any(want in b for b in bodies):
            bad.append(f"README.md:{n}: {want[:90]!r} is in none of {ids}")
assert not bad, "\n".join(bad[:6])
PY

# --- h-08 a declared value that changes nothing is decoration ----------------
py "$AREA" "$WORK" <<'PY' && ok "h-08 on_cap is read at the point of decision, not copied into prose" || bad "h-08 on_cap changes nothing but a sentence"
import copy, json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
base = json.load(open(os.path.join(area, "pipelines", "release-coupon-fix.json")))
def variant(name, value):
    d = copy.deepcopy(base)
    st = next(s for s in d["stages"] if s["id"] == "develop")
    st["iterations_permitted"] = 1          # so the cap that on_cap governs is reached
    st["on_cap"] = value
    path = os.path.join(work, f"p-oncap-{name}.json")
    json.dump(d, open(path, "w"))
    subprocess.run([sys.executable, os.path.join(area, "run.py"),
                    "--entry", os.path.join(area, "entries", "human.json"),
                    "--pipeline", path,
                    "--ledger", os.path.join(work, f"oncap-{name}.jsonl"),
                    "--report", os.path.join(work, f"oncap-{name}.rep.json"),
                    "--out", os.path.join(work, f"oncap-{name}.state")],
                   capture_output=True, text=True)
    rep = json.load(open(os.path.join(work, f"oncap-{name}.rep.json")))
    for volatile in ("process_nonce", "nonces", "executor", "register"):
        rep.pop(volatile, None)
    if rep.get("problem"):
        rep["problem"].pop("detail", None)   # prose is not a record
    for r in rep.get("refusals", []):
        r.pop("detail", None)
    return rep
a, b = variant("escalate", "escalate"), variant("continue", "continue")
assert a != b, ("the declaration carries on_cap and nothing reads it: two runs differing only "
                "in that value produce the same disposition, the same loop record and the same "
                "typed refusal, so the member is decoration or an unrecorded gap")
PY

# --- h-09 a stage is a row a builder adds, or the refusal is typed -----------
py "$AREA" "$WORK" <<'PY' && ok "h-09 a stage added to the declaration is walked in declared order" || bad "h-09 adding a declared stage is not a document change"
import copy, json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
d = json.load(open(os.path.join(area, "pipelines", "release-coupon-fix.json")))
d = copy.deepcopy(d)
d["stages"].insert(1, {"id": "canary", "op": "sequence",
                       "enter_when": {"stage": "plan", "outcome": "priced"},
                       "outcome_on_success": "priced",
                       "steps": [{"id": "canary-step", "cost_micros": 0}]})
path = os.path.join(work, "p-canary.json"); json.dump(d, open(path, "w"))
out = subprocess.run([sys.executable, os.path.join(area, "run.py"),
                      "--entry", os.path.join(area, "entries", "human.json"),
                      "--pipeline", path,
                      "--ledger", os.path.join(work, "canary.jsonl"),
                      "--report", os.path.join(work, "canary.rep.json"),
                      "--out", os.path.join(work, "canary.state")],
                     capture_output=True, text=True)
assert "Traceback" not in out.stderr, (
    "a stage added to the declaration crashes the walk instead of being entered or refused: "
    + out.stderr.strip().splitlines()[-1])
assert out.returncode in (0, 2, 3), out.returncode
rows = [json.loads(l) for l in open(os.path.join(work, "canary.jsonl"))]
walked = [r["stage"] for r in rows if r["kind"] in ("stage-entered", "stage-skipped")]
assert walked[:2] == ["plan", "canary"], f"the declared order was not walked: {walked}"
PY

# --- h-10 the same envelope twice converges on one answer --------------------
py "$AREA" "$WORK" <<'PY' && ok "h-10 replaying one envelope against its own state returns the same result" || bad "h-10 a replay returns a different disposition"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
lines = []
for i in (1, 2):
    out = subprocess.run([sys.executable, os.path.join(area, "run.py"),
                          "--entry", os.path.join(area, "entries", "schedule.json"),
                          "--ledger", os.path.join(work, "replay.jsonl"),
                          "--report", os.path.join(work, f"replay{i}.rep.json"),
                          "--out", os.path.join(work, "replay.state")],
                         capture_output=True, text=True)
    lines.append([l for l in out.stdout.splitlines() if l.startswith("RESULT ")][-1])
a = json.load(open(os.path.join(work, "replay1.rep.json")))
b = json.load(open(os.path.join(work, "replay2.rep.json")))
assert lines[0] == lines[1], (
    f"one envelope, one run key, two answers:\n  first  {lines[0]}\n  second {lines[1]}")
assert a["disposition"] == b["disposition"] and a["task_states_seen"] == b["task_states_seen"]
PY

# --- h-11 provenance counts are read back out of the artifacts ---------------
py "$AREA" "$WORK" <<'PY' && ok "h-11 every count provenance.json spells out equals the artifact's" || bad "h-11 a count in provenance.json is not the one the artifacts hold"
import glob, json, os, re, sys
area, work = sys.argv[1], sys.argv[2]
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "twenty": 20,
         "twenty-one": 21, "twenty-two": 22}
blob = open(os.path.join(area, "provenance.json")).read()
types, kinds = set(), set()
out = os.path.join(area, "out")
for path in glob.glob(os.path.join(out, "*.rep.json")) + glob.glob(os.path.join(work, "*.rep.json")):
    rep = json.load(open(path))
    for r in ([rep["problem"]] if rep["problem"] else []) + rep["refusals"]:
        types.add(r["type"])
for path in glob.glob(os.path.join(out, "*.jsonl")) + glob.glob(os.path.join(work, "*.jsonl")):
    kinds |= {json.loads(l)["kind"] for l in open(path) if l.strip()}
assert len(types) >= 5, f"only {len(types)} failure types were produced; nothing to count"
human = json.load(open(os.path.join(work, "human.rep.json")))
CLAIMS = [(r"([a-z-]+) failure types", len(types), "failure types"),
          (r"([a-z-]+) committed steps", human["steps_committed"], "committed steps"),
          (r"([a-z-]+) ladder rungs", len(human["success_ladder"]), "ladder rungs")]
bad = []
for pattern, measured, what in CLAIMS:
    for word in set(re.findall(pattern, blob)):
        if word in WORDS and WORDS[word] != measured:
            bad.append(f"provenance.json says {word} {what}; the artifacts hold {measured}")
assert not bad, "; ".join(bad)
PY

# --- h-12 the grader's own body reaches nothing the run wrote ----------------
py "$AREA" "$WORK" <<'PY' && ok "h-12 no criterion or rubric body appears in any artifact of a run" || bad "h-12 a grading body leaked into an artifact"
import os, sys
area, work = sys.argv[1], sys.argv[2]
BODIES = ("must_contain", "required_steps", "required_tools", "answer_contains")
scanned, hits = 0, []
for root, dirs, files in os.walk(work):
    for name in sorted(files):
        path = os.path.join(root, name)
        scanned += 1
        text = open(path, errors="replace").read()
        for b in BODIES:
            if b in text:
                hits.append(f"{os.path.relpath(path, work)}: {b}")
assert scanned >= 20, f"only {scanned} artifacts scanned; the runs wrote nothing"
assert not hits, f"{len(hits)} leaks, first: {hits[:4]}"
PY

# --- h-13 no product name anywhere the example is written --------------------
py "$AREA" <<'PY' && ok "h-13 no product is named in any source file of the example" || bad "h-13 a product is named outside an adapter"
import os, re, sys
area = sys.argv[1]
NAMES = re.compile(r"\b(temporal|restate|dbos|inngest|cadence|windmill|opa|rego|cedar|"
                   r"firecracker|gvisor|kata|docker|kubernetes|openai|anthropic|azure|aws|"
                   r"litellm|jaeger|datadog|prometheus|postgres|redis|sqlite|github|celery|"
                   r"airflow|argo|step functions)\b", re.I)
scanned, hits = 0, []
for root, dirs, files in os.walk(area):
    dirs[:] = [d for d in dirs if d not in ("out", "__pycache__")]
    for name in sorted(files):
        if not name.endswith((".md", ".py", ".sh", ".json")):
            continue
        path = os.path.join(root, name)
        scanned += 1
        for i, line in enumerate(open(path, errors="replace").read().splitlines(), 1):
            if "namecheck" in line or "\\b" in line:      # the rule may name what it forbids
                continue
            m = NAMES.search(line)
            if m:
                hits.append(f"{os.path.relpath(path, area)}:{i}: {m.group(0)}")
assert scanned >= 10, f"only {scanned} source files scanned"
assert not hits, f"{len(hits)} product names, first: {hits[:5]}"
PY

# --- h-14 the visible check counts something, and its floor is real ----------
py "$WORK" "$AREA" <<'PY' && ok "h-14 the visible check counts at least 40 checks and fails none" || bad "h-14 the visible check counted too little"
import json, os, re, sys
work, area = sys.argv[1], sys.argv[2]
line = [l for l in open(os.path.join(work, "visible.log")) if l.startswith("passed ")]
assert line, "test.sh printed no `passed N, failed M` line"
n, m = map(int, re.match(r"passed (\d+), failed (\d+)", line[-1].strip()).groups())
assert m == 0, f"the visible check failed {m}"
assert n >= 40, f"the visible check counted only {n}; a run that counts nothing is not a pass"
floor = int(re.search(r"^FLOOR=(\d+)$", open(os.path.join(area, "test.sh")).read(), re.M).group(1))
declared = json.load(open(os.path.join(area, "provenance.json")))["visible_checks_counted"]
assert floor == declared == n, (floor, declared, n)
assert '[ "$PASS" -ge "$FLOOR" ]' in open(os.path.join(area, "test.sh")).read()
PY
if [ "$VRC" -eq 0 ]; then ok "h-15 the visible check exits 0"; else bad "h-15 the visible check exited $VRC"; fi

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
