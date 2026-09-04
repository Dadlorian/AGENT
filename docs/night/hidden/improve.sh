#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "improve".
#
# Held out from examples/improve/ on purpose: the grader is never visible to the
# graded (F-b1-07). examples/improve/test.sh is the area's visible feedback
# surface; this script decides, and the author of the example never sees it.
#
# Every assertion reads a value back out of a ledger record, a document on disk,
# a knowledge-base record or an exit status - never a sentence the example wrote
# about itself. Where a declared value is at stake the check varies it and
# re-runs, because a green run at the default value proves the default path and
# nothing else.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/improve.sh
#
# Python 3.11 standard library only. No network.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/improve"
WORK="${TMPDIR:-/tmp}/hidden-improve-$$"
# The runner resolves intent.workflow_ref against the example directory, so a
# probe document has to live inside it; it is removed on the way out.
PROBE="$AREA/out/hidden-probe"
mkdir -p "$WORK" "$PROBE"
trap 'rm -rf "$WORK" "$PROBE"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/improve/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# --- h-01 the six-part README shape, in order --------------------------------
py "$AREA" <<'PY' && ok "h-01 README carries the six headings in order" || bad "h-01 README shape"
import re, sys
head = [l.strip() for l in open(sys.argv[1] + "/README.md") if l.startswith("## ")]
want = ["ideal", "standards", "the call", "what the user sees", "composition", "extension points"]
got = [re.sub(r"^##\s*\d*\.?\s*", "", h).strip().lower() for h in head]
assert got == want, got
PY

# --- h-02 four doors, each validating against the published schemas ----------
py "$ROOT" <<'PY' && ok "h-02 four entry documents, payload.improve and the task specification all validate" || bad "h-02 the documents do not validate"
import importlib.util, json, os, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("e2e", os.path.join(root, "examples", "end-to-end", "run.py"))
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
area = os.path.join(root, "examples", "improve")
entry_schema = json.load(open(os.path.join(root, "examples", "end-to-end", "schemas", "entry.schema.json")))
pass_schema = json.load(open(os.path.join(area, "schemas", "improve.schema.json")))
unit_schema = json.load(open(os.path.join(area, "schemas", "unit.schema.json")))
kinds, units = set(), set()
for door in ("human", "event", "schedule", "external"):
    path = os.path.join(area, "entries", f"{door}.json")
    assert os.path.exists(path), f"door {door} is described but not on disk"
    doc = json.load(open(path))
    assert not ref.validate(doc, entry_schema), (door, ref.validate(doc, entry_schema))
    assert doc["kind"] == door, (door, doc["kind"])
    kinds.add(doc["kind"])
    imp = doc["payload"]["improve"]
    assert not ref.validate(imp, pass_schema), (door, ref.validate(imp, pass_schema))
    units.add(doc["intent"]["workflow_ref"])
assert kinds == {"human", "event", "schedule", "external"}, kinds
assert len(units) == 1, f"the four doors point at {len(units)} specifications, not one"
unit = json.load(open(os.path.join(area, list(units)[0])))
assert not ref.validate(unit, unit_schema), ref.validate(unit, unit_schema)
PY

# --- the baseline runs this script decides on --------------------------------
# Four doors, run here rather than read out of whatever out/ happened to hold.
for D in human event external; do
  (cd "$ROOT" && python3 examples/improve/run.py --entry "examples/improve/entries/$D.json" \
     --ledger "$PROBE/h-$D.jsonl") > "$WORK/h-$D.log" 2>&1
done
FIRES=0
until grep -q "^completed:" "$WORK/h-schedule.log" 2>/dev/null || [ "$FIRES" -ge 9 ]; do
  (cd "$ROOT" && python3 examples/improve/run.py --entry examples/improve/entries/schedule.json \
     --ledger "$PROBE/h-schedule.jsonl") > "$WORK/h-schedule.log" 2>&1
  FIRES=$((FIRES + 1))
done

# --- h-03 one declaration, four doors, four identities -----------------------
py "$PROBE" "$AREA" <<'PY' && ok "h-03 one specification and one scorecard at four doors, four identities, derived depths" || bad "h-03 the four doors are not one declaration"
import json, os, sys
probe, area = sys.argv[1], sys.argv[2]
doors = ("human", "event", "schedule", "external")
rows = {}
for d in doors:
    path = os.path.join(probe, f"h-{d}.jsonl")
    assert os.path.exists(path), f"{d} wrote no receipt"
    rows[d] = [json.loads(l) for l in open(path)]
sub = {d: [r for r in rows[d] if r["kind"] == "pass-submitted"][0] for d in doors}
reg = {d: [r for r in rows[d] if r["kind"] == "scorecard-registered"][0] for d in doors}
assert len({sub[d]["unit_digest"] for d in doors}) == 1, "the doors ran different specifications"
assert len({reg[d]["scorecard_digest"] for d in doors}) == 1, "the doors registered different scorecards"
for field in ("actor", "run_id", "correlation_id"):
    per = {d: {r[field] for r in rows[d] if field in r} for d in doors}
    assert all(len(v) == 1 for v in per.values()), (field, per)
    assert len({next(iter(v)) for v in per.values()}) == 4, (field, per)
# the depth on every record is derived from the document's own chain, not declared
for d in doors:
    doc = json.load(open(os.path.join(area, "entries", f"{d}.json")))
    want = len(doc["actor"]["delegation_chain"]) - 1
    got = {r["delegation_depth"] for r in rows[d]}
    assert got == {want}, (d, got, want, doc["correlation"].get("depth"))
    if doc["correlation"].get("depth") not in (None, want):
        assert got == {want}, f"{d}: the declared depth reached a record"
closing = {d: [r["kind"] for r in rows[d] if r["kind"].startswith("pass-")][-1] for d in doors}
assert set(closing.values()) <= {"pass-completed", "pass-escalated", "pass-failed"}, closing
assert len(set(closing.values())) >= 2, f"every door ended the same way: {closing}"
PY

# --- h-04 a declared value the visible check never varies --------------------
# per_iteration_micros is the number the plan floor, the budget stop and the
# learned table are all priced from. Halve it and every one of them must halve;
# a runner holding the price anywhere but in the document fails here.
py "$AREA" "$PROBE" <<'PY' && ok "h-04 loop.per_iteration_micros differential: halving it halves the plan floor, the spend and the learned micros" || bad "h-04 per_iteration_micros is not read at the point of decision"
import json, os, subprocess, sys
area, probe = sys.argv[1], sys.argv[2]
root = os.path.abspath(os.path.join(area, "..", ".."))
unit = json.load(open(os.path.join(area, "units", "improve-platform-scorecard.json")))
base_price = int(unit["loop"]["per_iteration_micros"])
unit["loop"]["per_iteration_micros"] = base_price // 2
json.dump(unit, open(os.path.join(probe, "u-half.json"), "w"), indent=2)
entry = json.load(open(os.path.join(area, "entries", "human.json")))
entry["intent"]["workflow_ref"] = "out/hidden-probe/u-half.json"
json.dump(entry, open(os.path.join(probe, "e-half.json"), "w"), indent=2)
led = os.path.join(probe, "h-half.jsonl")
out = subprocess.run(["python3", "examples/improve/run.py", "--entry",
                      os.path.join(probe, "e-half.json"), "--ledger", led],
                     cwd=root, capture_output=True, text=True)
assert out.returncode == 0, out.stdout[-800:] + out.stderr[-800:]
half = [json.loads(l) for l in open(led)]
full = [json.loads(l) for l in open(os.path.join(probe, "h-human.jsonl"))]
def close(rows):
    return [r for r in rows if r["kind"] in ("pass-completed", "pass-escalated")][-1]
def learn(rows):
    return [r for r in rows if r["kind"] == "learned"][-1]
def its(rows):
    return [r for r in rows if r["kind"] == "iteration-recorded"]
assert len(its(half)) == len(its(full)), "halving the price changed the pass, not the price"
assert close(half)["cost_micros"] * 2 == close(full)["cost_micros"], \
    (close(half)["cost_micros"], close(full)["cost_micros"])
assert learn(half)["micros"] * 2 == learn(full)["micros"], (learn(half)["micros"], learn(full)["micros"])
assert {r["spend_micros"] for r in its(half)} == {base_price // 2}, \
    {r["spend_micros"] for r in its(half)}
floor = lambda log: int([w for w in log.split("floor ")[1].split()][0])
assert floor(out.stdout) * 2 == 3 * base_price, (floor(out.stdout), base_price)
PY

# --- h-05 the gate decides, and the decision is the gate's -------------------
py "$AREA" "$PROBE" <<'PY' && ok "h-05 the gate differential: 1.4.1-rc declines and holds the checkpoint, 1.4.0 promotes and advances" || bad "h-05 the gate's verdict does not decide"
import json, os, subprocess, sys
area, probe = sys.argv[1], sys.argv[2]
root = os.path.abspath(os.path.join(area, "..", ".."))
unit = json.load(open(os.path.join(area, "units", "improve-platform-scorecard.json")))
first = unit["candidates"][0]
assert first["gate"]["unit_version"] != "1.4.0", "the shipped first candidate no longer fails its gate"
first["gate"]["unit_version"] = "1.4.0"
json.dump(unit, open(os.path.join(probe, "u-pinned.json"), "w"), indent=2)
entry = json.load(open(os.path.join(area, "entries", "human.json")))
entry["intent"]["workflow_ref"] = "out/hidden-probe/u-pinned.json"
json.dump(entry, open(os.path.join(probe, "e-pinned.json"), "w"), indent=2)
led = os.path.join(probe, "h-pinned.jsonl")
out = subprocess.run(["python3", "examples/improve/run.py", "--entry",
                      os.path.join(probe, "e-pinned.json"), "--ledger", led],
                     cwd=root, capture_output=True, text=True)
assert out.returncode == 0, out.stdout[-800:] + out.stderr[-800:]
its = lambda p: [json.loads(l) for l in open(p) if '"iteration-recorded"' in l]
ship, pinned = its(os.path.join(probe, "h-human.jsonl")), its(led)
assert ship[0]["candidate_id"] == pinned[0]["candidate_id"] == first["candidate_id"]
assert (ship[0]["gate_outcome"], ship[0]["decision"]) == ("failed", "declined"), ship[0]
assert ship[0]["checkpoint_advanced"] is False, "a declined candidate moved the checkpoint"
assert ship[0]["checkpoint_id"] == ship[0]["rollback_to_checkpoint_id"], "the rollback state moved too"
assert (pinned[0]["gate_outcome"], pinned[0]["decision"]) == ("passed", "promoted"), pinned[0]
assert pinned[0]["checkpoint_advanced"] is True, pinned[0]
assert len(pinned) < len(ship), (len(pinned), len(ship))
PY

# --- h-06 the spend is read out of the rows, not recomputed beside them ------
py "$PROBE" <<'PY' && ok "h-06 the learned micros and the closing cost equal the sum of the rows' own spend_micros at four doors" || bad "h-06 the spend totals are not the rows' own"
import json, os, sys
probe = sys.argv[1]
for door in ("human", "event", "schedule", "external"):
    rows = [json.loads(l) for l in open(os.path.join(probe, f"h-{door}.jsonl"))]
    its = [r for r in rows if r["kind"] == "iteration-recorded"]
    assert its, f"{door} recorded no iteration"
    assert all("spend_micros" in r for r in its), f"{door}: an iteration record carries no spend"
    total = sum(r["spend_micros"] for r in its)
    said = [r for r in rows if r["kind"] == "learned"][-1]
    assert said["micros"] == total, (door, said["micros"], total)
    assert said["iterations"] == len(its), (door, said["iterations"], len(its))
    assert said["promoted"] + said["declined"] == len(its), (door, said)
    close = [r for r in rows if r["kind"] in ("pass-completed", "pass-escalated", "pass-failed")]
    if close and "cost_micros" in close[-1]:
        assert close[-1]["cost_micros"] == total, (door, close[-1]["cost_micros"], total)
PY

# --- h-07 every quote is verbatim in the record its own line names -----------
py "$ROOT" <<'PY' && ok "h-07 every quoted string sits verbatim in a record the same line names" || bad "h-07 a quoted string is not in the record it names"
import glob, json, os, re, sys
root = sys.argv[1]
bodies = {}
for name in ("facts", "target-facts", "reference-facts", "research"):
    path = os.path.join(root, "kb", f"{name}.jsonl")
    if not os.path.exists(path):
        continue
    for line in open(path):
        row = json.loads(line)
        bodies.setdefault(row["id"], []).append(
            " ".join(str(row.get(k, "")) for k in ("text", "claim", "snippet")))
for path in glob.glob(os.path.join(root, "kb", "research", "*.jsonl")):
    for line in open(path):
        row = json.loads(line)
        bodies.setdefault(row["id"], []).append(
            " ".join(str(row.get(k, "")) for k in ("text", "claim", "snippet")))
norm = lambda s: re.sub(r"\s+", " ", s).replace("—", "-").replace("\\|", "|").strip()
def sources(cite):
    if cite.startswith("REF-"):
        path = os.path.join(root, cite[4:].split("#")[0])
        return [norm(open(path, errors="replace").read())] if os.path.exists(path) else None
    return [norm(b) for b in bodies[cite]] if cite in bodies else None
ids = re.compile(r"`((?:F|E|R|T|X|REF)-[A-Za-z0-9][A-Za-z0-9./_#,-]*)`")
quotes = re.compile(r'"([^"]{12,})"')
checked, misses, unresolved = 0, [], []
for n, line in enumerate(open(os.path.join(root, "examples", "improve", "README.md")), 1):
    named = ids.findall(line)
    if not named:
        continue
    pairs = [(i, sources(i)) for i in named]
    unresolved += [i for i, b in pairs if b is None]
    for quote in quotes.findall(line):
        want = norm(quote)
        checked += 1
        if not any(want in body for _, bs in pairs if bs for body in bs):
            misses.append((n, named, want[:90]))
assert not unresolved, f"ids resolving to no record: {sorted(set(unresolved))}"
assert not misses, f"quotes not in the record their line names: {misses}"
assert checked >= 25, f"only {checked} quoted strings carried an id to check against"
print(f"  (h-07 checked {checked} quoted strings)")
PY

# --- h-08 a value that decides nothing is written up as deciding nothing -----
# The mechanical form: change the field, re-run, and compare the decisions. If
# every decision is identical the field is decoration, and decoration has to sit
# in the README's carried-and-not-consumed table with its research query.
py "$AREA" "$PROBE" <<'PY' && ok "h-08 every unit field whose change moves no decision is named in the carried-and-not-consumed table" || bad "h-08 an inert declared value is written up as if it were read"
import json, os, re, subprocess, sys
area, probe = sys.argv[1], sys.argv[2]
root = os.path.abspath(os.path.join(area, "..", ".."))
readme = open(os.path.join(area, "README.md")).read()
block = readme.split("Carried and not consumed", 1)
assert len(block) == 2, "the README has no carried-and-not-consumed table"
carried = set()
for line in block[1].splitlines():
    if not line.startswith("|"):
        if carried:
            break
        continue
    for tok in re.findall(r"`([^`]+)`", line.split("|")[1]):
        if "/" in tok or tok.endswith((".json", ".md", ".py", ".sh")):
            continue                          # a path, not a member name
        carried.add(tok.replace("[]", "").split(".")[-1])
base_unit = json.load(open(os.path.join(area, "units", "improve-platform-scorecard.json")))
def probes():
    yield "template", lambda u: u.__setitem__("template", "template:probe-alternative")
    yield "unit_id", lambda u: u.__setitem__("unit_id", "probe-alternative-unit")
    yield "loop_ref", lambda u: u["loop"].__setitem__("loop_ref", "probe-alternative-loop")
    yield "slot", lambda u: [c.__setitem__("slot", "probe.alternative") for c in u["candidates"]]
    yield "rationale", lambda u: [c.__setitem__("rationale", "probe alternative") for c in u["candidates"]]
    yield "means", lambda u: [m.__setitem__("means", "probe alternative")
                              for m in u["scorecard"]["metrics"]]
def fingerprint(path):
    rows = [json.loads(l) for l in open(path)]
    keys = ("iteration_index", "metric_id", "candidate_id", "gate_outcome", "cases_executed",
            "decision", "checkpoint_id", "checkpoint_advanced", "distance_after")
    out = [tuple(r[k] for k in keys) for r in rows if r["kind"] == "iteration-recorded"]
    close = [r for r in rows if r["kind"].startswith("pass-") and r["kind"] != "pass-submitted"]
    out.append(tuple(str(close[-1].get(k)) for k in
                     ("kind", "terminated_by", "iterations_run", "targets_held", "cost_micros")))
    return out
base = fingerprint(os.path.join(probe, "h-human.jsonl"))
inert = []
for name, mutate in probes():
    unit = json.loads(json.dumps(base_unit))
    mutate(unit)
    upath = os.path.join(probe, f"u-x-{name}.json")
    json.dump(unit, open(upath, "w"), indent=2)
    entry = json.load(open(os.path.join(area, "entries", "human.json")))
    entry["intent"]["workflow_ref"] = f"out/hidden-probe/u-x-{name}.json"
    epath = os.path.join(probe, f"e-x-{name}.json")
    json.dump(entry, open(epath, "w"), indent=2)
    led = os.path.join(probe, f"h-x-{name}.jsonl")
    out = subprocess.run(["python3", "examples/improve/run.py", "--entry", epath, "--ledger", led],
                         cwd=root, capture_output=True, text=True)
    assert out.returncode == 0, (name, out.stdout[-600:], out.stderr[-600:])
    if fingerprint(led) == base and name not in carried:
        inert.append(name)
assert not inert, ("declared in the task specification, decides nothing, and is not in the "
                   f"carried-and-not-consumed table: {sorted(inert)}; that table names {sorted(carried)}")
PY

# --- h-09 a field table row names a field the documents actually carry -------
py "$AREA" <<'PY' && ok "h-09 every field the README says is read exists in a document or a schema" || bad "h-09 the README reads a field nothing declares"
import glob, json, os, re, sys
area = sys.argv[1]
declared = set()
for path in (glob.glob(os.path.join(area, "entries", "*.json"))
             + glob.glob(os.path.join(area, "units", "*.json"))
             + glob.glob(os.path.join(area, "schemas", "*.json"))):
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                declared.add(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.load(open(path)))
lines = open(os.path.join(area, "README.md")).read().splitlines()
rows, inside = [], False
for line in lines:
    if re.match(r"^\|\s*Field\s*\|", line):
        inside = True
        continue
    if inside and not line.startswith("|"):
        inside = False
        continue
    if inside and not re.match(r"^\|[\s|:-]+\|$", line):
        rows.append(line)
assert len(rows) >= 12, f"only {len(rows)} field rows parsed out of the README"
missing = []
for line in rows:
    first = line.split("|")[1]
    if "absent by design" in line:            # a member the schema refuses on purpose
        continue
    for tok in re.findall(r"`([^`]+)`", first):
        if "/" in tok or tok.endswith((".json", ".md", ".py", ".sh")):
            continue                          # a path, not a member name
        leaf = tok.replace("[]", "").split(".")[-1]
        if leaf not in declared:
            missing.append((leaf, first.strip()))
assert not missing, f"field rows naming a member no document or schema declares: {missing}"
print(f"  (h-09 checked {len(rows)} field rows against {len(declared)} declared members)")
PY

# --- h-10 a run step's label agrees with the line the step really prints -----
py "$AREA" <<'PY' && ok "h-10 every run step's label agrees with its own promised last line" || bad "h-10 a run step's label contradicts its last line"
import re, sys
text = open(sys.argv[1] + "/README.md").read()
rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$", text, re.M)
assert len(rows) >= 8, f"only {len(rows)} run steps parsed"
wrong = []
for n, label, cmd, last in rows:
    low = label.lower()
    closes = any(w in low for w in ("closes", "closed it", "finishes", "completes"))
    parks = "park" in low
    if closes and not re.match(r"^(completed|escalated):", last):
        wrong.append((n, label, last[:60]))
    if parks and not closes and not last.startswith("parked:"):
        wrong.append((n, label, last[:60]))
assert not wrong, f"run steps whose label is not what the command prints: {wrong}"
print(f"  (h-10 checked {len(rows)} run steps)")
PY

# --- h-11 no product name anywhere in the area -------------------------------
py "$AREA" <<'PY' && ok "h-11 no product name appears outside an adapter column" || bad "h-11 a product name is named outside an adapter"
import os, re, sys
area = sys.argv[1]
names = ["firecracker", "gvisor", "kata", "docker", "kubernetes", "podman", "temporal",
         "langfuse", "langchain", "langsmith", "litellm", "openai", "anthropic", "claude",
         "goose", "opa", "rego", "cedar", "jaeger", "datadog", "grafana", "prometheus",
         "redis", "postgres", "sqlite", "e2b", "modal", "daytona", "braintrust", "mlflow",
         "arize", "phoenix", "bedrock", "vertex", "azure", "aws", "gcp"]
pattern = re.compile(r"\b(" + "|".join(names) + r")\b", re.I)
hits, scanned = [], 0
for base, dirs, files in os.walk(area):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "hidden-probe")]
    for name in sorted(files):
        if name.endswith(".pyc"):
            continue
        full = os.path.join(base, name)
        scanned += 1
        for i, line in enumerate(open(full, errors="ignore"), 1):
            if "grep" in line or "CITES-SCAN" in line:   # a check may name what it forbids
                continue
            m = pattern.search(line)
            if m:
                hits.append((os.path.relpath(full, area), i, m.group(0)))
assert not hits, f"product names in the example: {hits[:6]}"
assert scanned >= 20, f"only {scanned} files scanned"
print(f"  (h-11 scanned {scanned} files for {len(names)} product names)")
PY

# --- h-12 the visible check counts something, and the README says what -------
bash "$AREA/test.sh" > "$WORK/visible.log" 2>&1
VRC=$?
py "$WORK" "$AREA" <<'PY' && ok "h-12 the visible check counts at least 40 checks, fails none, and is the count the README promises" || bad "h-12 the visible check did not decide anything"
import os, re, sys
work, area = sys.argv[1], sys.argv[2]
lines = open(os.path.join(work, "visible.log")).read().splitlines()
printed = [l for l in lines if re.match(r"^passed \d+, failed \d+$", l.strip())]
assert printed, "test.sh printed no `passed N, failed M` line"
n, m = map(int, re.match(r"passed (\d+), failed (\d+)", printed[-1].strip()).groups())
assert m == 0, f"the visible check failed {m}"
assert n >= 40, f"the visible check counted only {n}; a run that counts nothing is not a pass"
promised = re.search(r"`passed (\d+), failed 0`", open(os.path.join(area, "README.md")).read())
assert promised, "the README promises no count"
assert int(promised.group(1)) == n, (int(promised.group(1)), n)
floor = re.search(r"^FLOOR=(\d+)$", open(os.path.join(area, "test.sh")).read(), re.M)
assert floor and int(floor.group(1)) >= 40, "test.sh gates on no floor under its own count"
PY
if [ "$VRC" -eq 0 ]; then ok "h-13 the visible check exits 0"; else bad "h-13 the visible check exited $VRC"; fi

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
