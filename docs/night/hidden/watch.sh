#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "watch".
#
# Held out from examples/watch/ on purpose: the grader is never visible to the
# graded (F-b1-07). examples/watch/test.sh is the area's visible feedback
# surface; this script is what decides, and the author of the example never
# sees it. Every assertion here reads a value back from a run report, a ledger
# record, an entry document, a schema or an exit status - never a sentence the
# example wrote about itself, and never a count the README quotes.
#
# The shape of the checks follows the row-75 boundary: for a value the example
# *declares*, do not accept that it is printed - change it and assert the
# records move (h-06, h-07, h-08). A green run at the default value proves the
# default path and nothing else.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/watch.sh
#
# Python 3.11 standard library only. No network.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
# WATCH_AREA exists so this script can be pointed at a deliberately hollowed
# copy and shown to fail; the graded area is the default and nothing in
# examples/watch/ sets it.
AREA="${WATCH_AREA:-$ROOT/examples/watch}"
WORK="${TMPDIR:-/tmp}/hidden-watch-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ] || [ ! -f "$AREA/test.sh" ]; then
  echo "  FAIL examples/watch/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# The visible surface is run once, into a work directory of our own, so every
# assertion below reads artifacts this script produced rather than artifacts
# left lying in the area's out/.
( cd "$AREA" && bash test.sh ) > "$WORK/visible.log" 2>&1
VIS_RC=$?
VIS_LAST="$(grep -E '^passed [0-9]+, failed [0-9]+$' "$WORK/visible.log" | tail -1)"

# --- h-01 the six-part README shape, in order --------------------------------
py "$AREA" <<'PY' && ok "h-01 README carries the six headings in order" || bad "h-01 README shape"
import re, sys
head = [l.strip() for l in open(sys.argv[1] + "/README.md") if l.startswith("## ")]
want = ["ideal", "standards", "the call", "what the user sees", "composition", "extension points"]
got = [re.sub(r"^##\s*\d*\.?\s*", "", h).strip().lower() for h in head]
assert len(got) == 6, f"expected 6 top headings, got {len(got)}: {got}"
for w, g in zip(want, got):
    assert g.startswith(w), f"heading {g!r} is not {w!r}"
print("headings", got)
PY

# --- h-02 four doors, four documents, one envelope shape ---------------------
py "$AREA" <<'PY' && ok "h-02 four entries and four watch declarations validate, one envelope shape" || bad "h-02 the four doors do not share one validated shape"
import json, os, sys
area = sys.argv[1]
sys.path.insert(0, os.path.join(area, "..", "end-to-end"))
from run import validate
entry_schema = json.load(open(os.path.join(area, "..", "end-to-end", "schemas", "entry.schema.json")))
watch_schema = json.load(open(os.path.join(area, "schemas", "watch.schema.json")))
doors = ("human", "event", "schedule", "external")
shapes, kinds = set(), set()
for d in doors:
    doc = json.load(open(os.path.join(area, "entries", d + ".json")))
    e = validate(doc, entry_schema)
    w = validate(doc["payload"]["watch"], watch_schema)
    assert not e and not w, (d, e, w)
    shapes.add(tuple(sorted(doc)))
    kinds.add(doc["kind"])
assert len(shapes) == 1, f"the four entries are not one shape: {shapes}"
assert kinds == set(doors), f"the four doors are not the four kinds: {kinds}"
print("one envelope shape across", sorted(kinds))
PY

# --- h-03 one unit declaration behind the four doors -------------------------
# The visible check's own line for this collapses to a single-element set and
# cannot fail; this one takes the set of the four values themselves.
py "$AREA" <<'PY' && ok "h-03 the four doors name exactly one task specification" || bad "h-03 the four doors do not name one unit"
import json, os, sys
area = sys.argv[1]
refs = {json.load(open(os.path.join(area, "entries", d + ".json")))["intent"]["workflow_ref"]
        for d in ("human", "event", "schedule", "external")}
assert len(refs) == 1, f"four doors named {len(refs)} task specifications: {sorted(refs)}"
ref = refs.pop()
assert os.path.isfile(os.path.join(area, ref)), f"{ref} is not a file"
units = {json.loads(l)["unit"] for d in ("human", "event", "schedule", "external")
         for l in open(os.path.join(area, "out", d + ".jsonl")) if '"unit"' in l}
assert units == {json.load(open(os.path.join(area, ref)))["unit"]}, units
print("one workflow_ref", ref, "and one unit on all four ledgers:", units)
PY

# --- h-04 the visible check counts, and its gate has a floor -----------------
py "$AREA" "$WORK/visible.log" <<'PY' && ok "h-04 the visible check counts >= 20 and gates on a floor" || bad "h-04 the visible gate can be structurally green and mean nothing"
import re, sys
area, log = sys.argv[1], sys.argv[2]
text = open(area + "/test.sh").read()
floor = re.search(r"^FLOOR=(\d+)$", text, re.M)
assert floor, "test.sh declares no FLOOR"
assert re.search(r'\[\s*"?\$PASS"?\s+-ge\s+"?\$FLOOR"?\s*\]', text), "the gate does not compare PASS to FLOOR"
assert re.search(r'\[\s*"?\$FAIL"?\s+-eq\s+0\s*\]', text), "the gate does not compare FAIL to 0"
line = [l for l in open(log) if re.match(r"^passed \d+, failed \d+$", l.strip())]
assert line, "the visible check printed no `passed N, failed M` line"
n, m = map(int, re.findall(r"\d+", line[-1]))
assert m == 0, f"the visible check failed {m} checks"
assert n >= 20, f"the visible check counted only {n}"
assert n >= int(floor.group(1)) >= 20, (n, floor.group(1))
print("visible", line[-1].strip(), "with FLOOR", floor.group(1))
PY

# --- h-05 the named ledger lines of a watched unit ---------------------------
py "$AREA" <<'PY' && ok "h-05 every lifecycle ledger line is present, chained and stamped" || bad "h-05 a named ledger line is missing"
import json, os, sys
area = sys.argv[1]
def rows(name):
    return [json.loads(l) for l in open(os.path.join(area, "out", name + ".jsonl"))]
human = rows("human")
need = {"unit-submitted", "cell-admitted", "step-observed", "refusal", "unit-completed"}
got = {r["kind"] for r in human}
assert need <= got, f"missing from the human ledger: {sorted(need - got)}"
ext = rows("external")
need2 = {"approval-parked", "approval-returned"}
assert need2 <= {r["kind"] for r in ext}, f"missing from the external ledger: {sorted(need2 - {r['kind'] for r in ext})}"
for name in ("human", "event", "schedule", "external"):
    for r in rows(name):
        for field in ("run_id", "correlation_id", "actor", "delegation_depth", "entry_kind",
                      "idempotency_key", "hash", "prev"):
            assert field in r, (name, r["kind"], field)
states = [r["state"] for r in ext if "state" in r]
assert states == ["submitted", "input-required", "working", "completed"], states
print("ledger kinds", sorted(got | {r["kind"] for r in ext}))
PY

# --- h-06 differential: a declared pause is read, not printed ----------------
# payload.watch.pause_for_decision is an extension point the visible check
# never varies on one door: it compares two different doors instead. Run the
# same envelope twice, one declared value changed, and assert the records move.
py "$AREA" "$WORK" <<'PY' && ok "h-06 differential: pause_for_decision changes the record on one door" || bad "h-06 pause_for_decision is declared but not decisive"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
env = json.load(open(os.path.join(area, "entries", "human.json")))
out = {}
for tag, value in (("pon", True), ("poff", False)):
    e = json.loads(json.dumps(env))
    e["payload"]["watch"]["pause_for_decision"] = value
    e["correlation"] = {"run_id": f"run-hidden-{tag}", "correlation_id": f"corr-hidden-{tag}", "depth": 0}
    p = os.path.join(work, tag + ".entry.json")
    json.dump(e, open(p, "w"))
    r = subprocess.run([sys.executable, "run.py", "--entry", p,
                        "--ledger", os.path.join(work, tag + ".jsonl"),
                        "--report", os.path.join(work, tag + ".json")],
                       cwd=area, capture_output=True, text=True)
    assert r.returncode == 0, (tag, r.returncode, r.stdout[-400:], r.stderr[-400:])
    out[tag] = json.load(open(os.path.join(work, tag + ".json")))
on, off = out["pon"], out["poff"]
assert on["audit"]["levels_covered"] == 2 and off["audit"]["levels_covered"] == 1, \
    (on["audit"]["levels_covered"], off["audit"]["levels_covered"])
assert on["audit"]["run_id_groups"] == off["audit"]["run_id_groups"] == 1
assert "human.ask" in on["events_on_the_stream"] and "human.ask" not in off["events_on_the_stream"]
assert on["outcome"]["decision"] and off["outcome"]["decision"] is None
assert len(on["events_on_the_stream"]) > len(off["events_on_the_stream"])
print("pause true ->", len(on["events_on_the_stream"]), "events at 2 levels; false ->",
      len(off["events_on_the_stream"]), "at 1")
PY

# --- h-07 differential: a declared tool ceiling is read at the point of call --
py "$AREA" "$WORK" <<'PY' && ok "h-07 differential: tools.ceiling_calls is enforced, not echoed" || bad "h-07 tools.ceiling_calls is decoration"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
unit = json.load(open(os.path.join(area, "units", "observe-checkout-fault.json")))
env = json.load(open(os.path.join(area, "entries", "human.json")))
reports = {}
for tag, ceiling in (("cc8", unit["tools"]["ceiling_calls"]), ("cc0", 0)):
    u = json.loads(json.dumps(unit)); u["tools"]["ceiling_calls"] = ceiling
    up = os.path.join(work, tag + ".unit.json"); json.dump(u, open(up, "w"))
    e = json.loads(json.dumps(env))
    e["intent"]["workflow_ref"] = os.path.relpath(up, area)
    e["correlation"] = {"run_id": f"run-hidden-{tag}", "correlation_id": f"corr-hidden-{tag}", "depth": 0}
    p = os.path.join(work, tag + ".entry.json"); json.dump(e, open(p, "w"))
    r = subprocess.run([sys.executable, "run.py", "--entry", p,
                        "--ledger", os.path.join(work, tag + ".jsonl"),
                        "--report", os.path.join(work, tag + ".json")],
                       cwd=area, capture_output=True, text=True)
    reports[tag] = json.load(open(os.path.join(work, tag + ".json")))
lo, hi = reports["cc0"]["audit"]["per_kind"], reports["cc8"]["audit"]["per_kind"]
assert lo["problem_object"]["read_back"] > hi["problem_object"]["read_back"], (lo, hi)
types = {s["unit"]["type"] for s in reports["cc0"]["audit"]["signals"] if s["kind"] == "problem_object"}
assert any(t.endswith("budget-exhausted") for t in types), types
print("ceiling 0 raised", lo["problem_object"]["read_back"], "problem objects against",
      hi["problem_object"]["read_back"], "at the declared ceiling")
PY

# --- h-08 every field the unit declares is decisive, or written up as carried -
# The mechanical form of the row-75 boundary: delete the value, re-run, and if
# the records are identical the row is decoration unless the README's
# carried-and-not-consumed table already says so.
py "$AREA" "$WORK" <<'PY' && ok "h-08 every declared unit field is read at the point of decision or written up" || bad "h-08 a declared unit field is neither consumed nor written up"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
unit = json.load(open(os.path.join(area, "units", "observe-checkout-fault.json")))
env = json.load(open(os.path.join(area, "entries", "human.json")))
readme = open(os.path.join(area, "README.md")).read()

ALT = {  # a second legal value for each leaf the declaration carries
    ("isolation", "egress_allowlist"): ["example.invalid"],
    ("tools", "server_ref"): "tools://second",
    ("tools", "ceiling_calls"): 0,
    ("tools", "revision"): "2026-07-27",
    ("observation", "instrument"): "hidden_probe_duration",
    ("ceilings", "wall_seconds"): 0.002,
    ("ceilings", "cancel_grace_s"): 1.25,
    ("ask", "deadline_seconds"): 61,
}

def record(tag, doc):
    up = os.path.join(work, "h08-" + tag + ".unit.json"); json.dump(doc, open(up, "w"))
    e = json.loads(json.dumps(env))
    e["intent"]["workflow_ref"] = os.path.relpath(up, area)
    e["payload"]["watch"]["pause_for_decision"] = True     # reach the ask, so ask.* is live
    e["correlation"] = {"run_id": "run-hidden-h08", "correlation_id": "corr-hidden-h08", "depth": 0}
    p = os.path.join(work, "h08-" + tag + ".entry.json"); json.dump(e, open(p, "w"))
    led = os.path.join(work, "h08-" + tag + ".jsonl")
    rep = os.path.join(work, "h08-" + tag + ".json")
    for path in (led, rep):
        if os.path.exists(path):
            os.remove(path)
    r = subprocess.run([sys.executable, "run.py", "--entry", p, "--ledger", led, "--report", rep],
                       cwd=area, capture_output=True, text=True)
    rows = []
    if os.path.exists(led):
        for line in open(led):
            row = json.loads(line)
            rows.append({k: v for k, v in row.items()
                         if k not in ("hash", "prev", "ts", "workflow_ref", "unit_id")})
    body = None
    if os.path.exists(rep):
        body = json.load(open(rep))
        def scrub(o):
            if isinstance(o, dict):
                return {k: scrub(v) for k, v in o.items()
                        if k not in ("value", "started_at", "ended_at", "watch", "overrides")}
            if isinstance(o, list):
                return [scrub(x) for x in o]
            return o
        body = scrub(body)
    return json.dumps({"rc": r.returncode, "rows": rows, "report": body}, sort_keys=True)

base = record("base", unit)
inert = []
for (section, key), alt in ALT.items():
    doc = json.loads(json.dumps(unit))
    doc[section][key] = alt
    if record(f"{section}-{key}", doc) == base:
        inert.append(f"{section}.{key}")
excused = [f for f in inert if f"`{f}`" in readme and "Carried and not consumed" in readme
           and readme.split("Carried and not consumed", 1)[1].split("### Gaps", 1)[0].count(f"`{f}`")]
unexcused = [f for f in inert if f not in excused]
assert not unexcused, ("declared in units/observe-checkout-fault.json, identical records when changed, "
                       "and not in the README's carried-and-not-consumed table: " + ", ".join(unexcused))
print("no inert declared unit field")
PY

# --- h-09 the quotes in the README are the words the cited record holds ------
py "$AREA" "$ROOT" <<'PY' && ok "h-09 every quote attributed to a cited file is verbatim in that file" || bad "h-09 a quote is not in the record it cites"
import json, os, re, sys
area, root = sys.argv[1], sys.argv[2]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
readme = open(os.path.join(area, "README.md")).read()
cache = {}
def text(path):
    if path not in cache:
        full = os.path.join(root, path)
        cache[path] = norm(open(full).read()) if os.path.isfile(full) else None
    return cache[path]
bad = []
for line in readme.split("\n"):
    if not line.startswith("|"):
        continue
    refs = [r.split("#")[0] for r in re.findall(r"REF-([A-Za-z0-9_./#,+-]+)", line)]
    refs = [r for r in refs if text(r) is not None]
    if not refs:
        continue
    for quote in re.findall(r'"([^"]{40,})"', norm(line)):
        q = norm(quote.replace("\\|", "|").replace("\\`", "`"))
        parts = [norm(p) for p in q.split("...") if norm(p)]
        if any(all(p in text(r) for p in parts) for r in refs):
            continue
        # a quote in the same row may instead belong to a kb id cited beside the file
        ids = re.findall(r"\b[FTXER]-[a-z][a-z0-9]*-[a-z0-9-]+\b", line)
        blob = ""
        for f in ("kb/facts.jsonl", "kb/target-facts.jsonl", "kb/reference-facts.jsonl",
                  "kb/research.jsonl", "kb/architecture.jsonl", "kb/entities.jsonl"):
            p = os.path.join(root, f)
            if not os.path.isfile(p):
                continue
            for l in open(p):
                if any(f'"{i}"' in l for i in ids):
                    blob += norm(l) + " "
        if all(norm(p.replace("**", "")) in blob.replace("**", "") for p in parts):
            continue
        bad.append((refs, q[:150]))
assert not bad, "quotes not found in the record they cite: " + json.dumps(bad, indent=1)
print("every REF-cited quote is verbatim")
PY

# --- h-10 the run-step table is twelve distinct calls, not a padded list -----
py "$AREA" <<'PY' && ok "h-10 no two run-step rows are the same command" || bad "h-10 the run-step table repeats a command"
import re, sys
readme = open(sys.argv[1] + "/README.md").read()
block = readme.split("### Run steps", 1)
assert len(block) == 2, "no Run steps table"
rows = [l for l in block[1].split("\n") if l.startswith("| ") and re.match(r"^\|\s*\d+\s*\|", l)]
assert len(rows) >= 10, f"only {len(rows)} run steps"
cmds = {}
for r in rows:
    cells = [c.strip() for c in r.strip("|").split("|")]
    n, cmd = cells[0], cells[2].strip("`")
    cmds.setdefault(cmd, []).append(n)
dupes = {c: v for c, v in cmds.items() if len(v) > 1}
assert not dupes, f"the same command appears on rows {dupes}"
print(len(rows), "run steps,", len(cmds), "distinct commands")
PY

# --- h-11 no product name outside the adapters and standards tables ----------
py "$AREA" <<'PY' && ok "h-11 no product or vendor name in the runnable files" || bad "h-11 a product name reached a runnable file"
import os, re, sys
area = sys.argv[1]
names = re.compile(r"(?i)\b(langfuse|jaeger|datadog|honeycomb|grafana|tempo|clickhouse|openai|"
                   r"anthropic|claude|gemini|bedrock|firecracker|kubernetes|docker|gvisor|goose|"
                   r"langchain|langgraph|temporal\.io)\b")
hits = []
for name in ("run.py", "test.sh", "harnesses.py", "provenance.json",
             "schemas/watch.schema.json", "units/observe-checkout-fault.json",
             "entries/human.json", "entries/event.json", "entries/schedule.json",
             "entries/external.json"):
    path = os.path.join(area, name)
    if not os.path.isfile(path):
        continue
    for i, line in enumerate(open(path), 1):
        # test.sh may name products inside the grep pattern that forbids them
        if name == "test.sh" and "grep -qiE" in line:
            continue
        m = names.search(line)
        if m:
            hits.append(f"{name}:{i} {m.group(0)}")
assert not hits, hits
print("no product name in the runnable files")
PY

# --- h-12 the typed event vocabulary is the capability's, and it is exercised -
py "$AREA" <<'PY' && ok "h-12 the emitted event types are the published ones, and seven are produced" || bad "h-12 the event vocabulary is minted or unexercised"
import json, os, sys
area = sys.argv[1]
sys.path.insert(0, area)
import harnesses
hi, _, _ = harnesses.human("dryrun")
published = set(hi.EVENT_TYPES)
seen = set()
for d in ("human", "event", "schedule", "external"):
    rep = json.load(open(os.path.join(area, "out", d + ".json")))
    seen |= set(rep["events_on_the_stream"])
assert seen <= published, f"minted event types: {sorted(seen - published)}"
assert len(seen) >= 7, f"only {len(seen)} of {len(published)} published types are produced: {sorted(seen)}"
print(len(seen), "of", len(published), "published event types produced")
PY

# --- h-13 the receipt is tamper-evident from outside the example -------------
py "$AREA" "$WORK" <<'PY' && ok "h-13 the ledger chain verifies and one edited byte is detected" || bad "h-13 the receipt is not tamper-evident"
import os, shutil, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
src = os.path.join(area, "out", "human.jsonl")
good = subprocess.run([sys.executable, "run.py", "--verify-ledger", "--ledger", src],
                      cwd=area, capture_output=True, text=True)
assert good.returncode == 0 and "chain verifies" in good.stdout, good.stdout
lines = open(src).read().split("\n")
target = next(i for i, l in enumerate(lines) if '"kind": "cell-admitted"' in l)
lines[target] = lines[target].replace('"actor": "user:corey"', '"actor": "user:mallory"')
bent = os.path.join(work, "bent.jsonl")
open(bent, "w").write("\n".join(lines))
broke = subprocess.run([sys.executable, "run.py", "--verify-ledger", "--ledger", bent],
                       cwd=area, capture_output=True, text=True)
assert broke.returncode != 0, "an edited actor was not detected"
print("chain verifies; an edited actor is detected with exit", broke.returncode)
PY

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge 10 ] || { echo "the hidden check counted $PASS, below its own floor of 10"; exit 1; }
[ "$VIS_RC" -eq 0 ] || { echo "the visible check exited $VIS_RC ($VIS_LAST)"; exit 1; }
