#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "ask".
#
# Held out from examples/ask/ on purpose: the grader is never visible to the
# graded (F-b1-07). examples/ask/test.sh is the area's visible feedback
# surface; this script is what decides, and the author never sees it.
#
# Every assertion reads a value back out of an artifact - a ledger record, an
# entry document, the capability description, an exit status, the kb records a
# row cites - never a log line the example wrote about itself. Two families of
# check exist here that a visible suite structurally cannot run:
#   - the citation family (h-06): a quote in the README must appear verbatim in
#     the record it names, so a plausible paraphrase of a real id is caught;
#   - the inert-declaration family (h-08, h-09, h-10): a declared value must be
#     read at the point of decision. Change it and the record must move. A value
#     nothing reads is decoration, and a green run at the default proves the
#     default path and nothing else (F-a7-03).
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/ask.sh
#
# Python 3.11 standard library only. No network. Nothing under examples/ask/ is
# written to: every run here is given its own ledger and its own declaration
# under $WORK.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/ask"
WORK="${TMPDIR:-/tmp}/hidden-ask-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/ask/ does not exist"
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

# --- h-02 four doors on disk, one shape, one job -----------------------------
py "$ROOT" <<'PY' && ok "h-02 four entry documents validate and carry one identical job" || bad "h-02 the four doors are not one shape"
import importlib.util, json, os, sys
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("e2e", os.path.join(root, "examples", "end-to-end", "run.py"))
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
schema = json.load(open(os.path.join(root, "examples", "end-to-end", "schemas", "entry.schema.json")))
docs = {}
for door in ("human", "event", "schedule", "external"):
    path = os.path.join(root, "examples", "ask", "entries", f"{door}.json")
    assert os.path.exists(path), f"door {door} is described but not on disk"
    doc = json.load(open(path)); docs[door] = doc
    errs = ref.validate(doc, schema)
    assert not errs, f"{door}: {errs}"
    assert doc["kind"] == door, (door, doc["kind"])
# one shape: the same member set at every door bar the optional parent correlation
shapes = {door: tuple(sorted(d)) for door, d in docs.items()}
assert len(set(shapes.values())) == 1, shapes
# one job, four of everything a door owns
jobs = {json.dumps({"intent": d["intent"], "payload": d["payload"]}, sort_keys=True) for d in docs.values()}
assert len(jobs) == 1, f"the four doors do not carry one job: {len(jobs)} distinct"
for member in ("entry_id", "idempotency_key", "correlation"):
    seen = {json.dumps(d[member], sort_keys=True) for d in docs.values()}
    assert len(seen) == 4, (member, seen)
PY

# --- h-03 the boundary sets what the producer cannot -------------------------
py "$AREA" <<'PY' && ok "h-03 no producer body carries a key, a correlation, a run id or a ceiling" || bad "h-03 a producer supplied what the boundary must set"
import json, sys
area = sys.argv[1]
producers = {k: v for k, v in json.load(open(area + "/producers.json")).items() if not k.startswith("_")}
assert set(producers) == {"human", "event", "schedule", "external"}, sorted(producers)
forbidden = ("idempotency_key", "correlation_id", "run_id", "ceiling_micros", "envelope_version")
for door, p in producers.items():
    text = json.dumps(p["body"])
    for f in forbidden:
        assert f not in text, f"{door} producer body carries {f}"
    assert p["transport"]["attested_subject"], door
# and what a producer says about its own identity must not reach any envelope
claims = {"user:root"}
for door in producers:
    envelope = json.dumps(json.load(open(f"{area}/entries/{door}.json")))
    for c in claims:
        assert c not in envelope, f"{door}: a producer's claim about itself reached the envelope"
PY

# --- h-04 the named ledger records, with the members an audit needs ----------
for d in human event schedule external; do
  ( cd "$AREA" && python3 run.py --entry "entries/$d.json" --ledger "$WORK/$d.jsonl" \
      --json > "$WORK/$d.json" 2> "$WORK/$d.err" )
done
py "$WORK" <<'PY' && ok "h-04 every entry-admitted record names run, correlation, key, and both identities" || bad "h-04 a record is missing what an audit needs"
import json, os, sys
work = sys.argv[1]
need = ("run_id", "correlation_id", "attested_subject", "entry_id", "idempotency_key",
        "job_digest", "door", "producer_format")
kinds = set()
for door in ("human", "event", "schedule", "external"):
    path = os.path.join(work, f"{door}.jsonl")
    assert os.path.exists(path) and os.path.getsize(path) > 0, f"{door} wrote no ledger record"
    rows = [json.loads(l) for l in open(path)]
    assert len(rows) == 1, (door, len(rows))
    r = rows[0]
    kinds.add(r["kind"])
    assert r["kind"] == "entry-admitted", (door, r["kind"], r.get("problem"))
    for n in need:
        assert r.get(n), (door, n)
    ident = r["identity"]
    assert ident["executing_identity"] and ident["triggering_identity"], (door, ident)
    assert r["units_started"] == 0, f"{door} started work at intake"
    assert set(r["receipt"]) <= {"entry_id", "correlation_id", "job_digest", "accepted",
                                 "duplicate_of"}, r["receipt"]
    assert r["round_trip"] == "exact", (door, r["round_trip"])
assert kinds == {"entry-admitted"}, kinds
PY

# --- h-05 a replay is answered from the record, not from the effect ----------
( cd "$AREA" && python3 run.py --door event --again --ledger "$WORK/replay.jsonl" \
    --json > "$WORK/replay.json" 2>&1 )
py "$WORK" <<'PY' && ok "h-05 a replay returns the stored receipt, keeps the correlation, records nothing new" || bad "h-05 the replay was not answered from the record"
import json, os, sys
rows = json.load(open(os.path.join(sys.argv[1], "replay.json")))
assert len(rows) == 2, len(rows)
first, second = rows
assert (first["claim"], second["claim"]) == ("fresh", "duplicate"), (first["claim"], second["claim"])
assert second["receipt"] == first["receipt"], "the replay did not return the stored acknowledgement"
assert second["correlation_id"] == first["correlation_id"], "the replay lost the original correlation"
assert second["replay"] is True and second["entries_recorded"] == 1, second["entries_recorded"]
# and the ledger agrees with the response
ledger = [json.loads(l) for l in open(os.path.join(sys.argv[1], "replay.jsonl"))]
assert len(ledger) == 2 and [r["claim"] for r in ledger] == ["fresh", "duplicate"], ledger
PY

# --- h-06 every quoted citation is verbatim in the record it names -----------
py "$ROOT" <<'PYX' && ok "h-06 every quoted citation in README is verbatim in the record it names" || bad "h-06 a citation is not what the record says"
import glob, json, os, re, sys
root = sys.argv[1]
readme = open(os.path.join(root, "examples", "ask", "README.md")).read()

def norm(text):
    """Line wrapping and markdown emphasis are the author's; the wording is the
    record's. Compare wording, so a rewrapped or de-bolded quote still matches
    and only a changed word fails."""
    return re.sub(r"\s+", " ", text.replace("*", "")).strip()

def strings(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            strings(v, out)
    elif isinstance(node, list):
        for v in node:
            strings(v, out)

parts = []
for path in (glob.glob(os.path.join(root, "kb", "*.jsonl"))
             + glob.glob(os.path.join(root, "kb", "research", "*.jsonl"))):
    for line in open(path):
        try:
            strings(json.loads(line), parts)
        except ValueError:
            pass
for path in (os.path.join(root, "docs", "litmus", "questionnaire.json"),
             os.path.join(root, "docs", "reference", "ontology.md"),
             os.path.join(root, "docs", "consumption", "unit-design.json"),
             os.path.join(root, "docs", "maturity", "closures.md"),
             os.path.join(root, "STATUS.md")):
    if not os.path.exists(path):
        continue
    try:
        strings(json.load(open(path)), parts)
    except ValueError:
        parts.append(open(path).read())
blob = norm(" | ".join(parts))

def fragments(quote):
    quote = quote.replace("\\|", "|").replace("\\`", "`")
    return [f.strip() for f in quote.split("…") if len(f.strip()) >= 20]

bad = []
for record_id, quote in re.findall(r"`((?:F|T|X|E|R|REF)-[a-z0-9-]+)`\s+\"([^\"]{20,})\"", readme):
    for frag in fragments(quote):
        if norm(frag) not in blob:
            bad.append((record_id, norm(frag)[:120]))
for path, quote in re.findall(r"`FILE:([^`#]+?)(?:#[^`]*)?`\s*\"([^\"]{20,})\"", readme):
    full = os.path.join(root, path.strip())
    if not os.path.exists(full):
        bad.append((path, "no such file"))
        continue
    text = norm(open(full).read())
    for frag in fragments(quote):
        if norm(frag) not in text:
            bad.append((path, norm(frag)[:120]))
assert not bad, "citations that no record supports: " + json.dumps(bad, indent=1)
PYX

# --- h-07 every command the README shows actually runs -----------------------
py "$ROOT" "$WORK" <<'PY' && ok "h-07 every run.py invocation the README shows is accepted by its command line" || bad "h-07 the README shows a command the example does not serve"
import os, re, shlex, subprocess, sys
root, work = sys.argv[1], sys.argv[2]
readme = open(os.path.join(root, "examples", "ask", "README.md")).read()
cmds = []
for span in re.findall(r"`([^`\n]+)`", readme):
    span = span.strip()
    if span.startswith("python3 examples/ask/run.py"):
        cmds.append(span)
    elif span.startswith("RACE_DELAY_S=") and "run.py" in span:
        cmds.append(span.split(" ", 1)[1])
assert cmds, "the README shows no invocation at all"
broken = []
for i, cmd in enumerate(sorted(set(cmds))):
    argv = shlex.split(cmd)
    if "--ledger" not in argv and "--verify-ledger" not in argv:
        argv += ["--ledger", os.path.join(work, f"readme-{i}.jsonl")]
    proc = subprocess.run([sys.executable] + argv[1:], cwd=root,
                          capture_output=True, text=True)
    err = proc.stderr
    if ("unrecognized arguments" in err or "invalid choice" in err
            or "expected one argument" in err or "Traceback" in err):
        broken.append((cmd, err.strip().splitlines()[-1][:140]))
assert not broken, "commands the README shows that the example does not serve: " + repr(broken)
PY

# --- h-08 a declared value is read at the point of decision ------------------
# The mechanical form: change one declared value, run every door, and require at
# least one record or the capability description to move. A value that changes
# nothing anywhere is decoration unless the README writes it up as carried and
# not consumed. Knobs whose two sides move together by construction (the
# declaration's own tenant against the resource's, the claim scope, the currency
# label on the ceiling) are out of this sweep: a one-value differential cannot
# observe them, and a check that cannot fail honestly is worse than no check.
py "$ROOT" "$WORK" <<'PYX' && ok "h-08 every declared knob moves a record or the description when it changes" || bad "h-08 a declared value is carried and never read"
import copy, json, os, re, subprocess, sys
root, work = sys.argv[1], sys.argv[2]
area = os.path.join(root, "examples", "ask")
base_decl = json.load(open(os.path.join(area, "admission.json")))
readme = open(os.path.join(area, "README.md")).read()
carried = (readme.split("### Carried and not consumed")[-1].split("### Gaps")[0]
           if "### Carried and not consumed" in readme else "")
DOORS = ("human", "event", "schedule", "external")

def state(decl, tag):
    path = os.path.join(work, "knob-%s.json" % tag)
    json.dump(decl, open(path, "w"))
    seen = {}
    for door in DOORS:
        out = subprocess.run([sys.executable, "run.py", "--door", door,
                              "--admission", path,
                              "--ledger", os.path.join(work, "knob-%s-%s.jsonl" % (tag, door)),
                              "--json"], cwd=area, capture_output=True, text=True)
        try:
            record = json.loads(out.stdout)[0]
        except Exception:
            record = {"rc": out.returncode, "stderr": out.stderr[-300:]}
        record.pop("at", None)
        seen[door] = record
    seen["describe"] = subprocess.run(
        [sys.executable, "run.py", "--describe", "--admission", path],
        cwd=area, capture_output=True, text=True).stdout
    return json.dumps(seen, sort_keys=True)

baseline = state(copy.deepcopy(base_decl), "base")
KNOBS = {
    "budget.ceiling_micros": 1000,
    "audience": "svc:other-intake",
    "identity.max_delegation_depth": 1,
    "identity.hop_lifetime_s": [11, 7, 5, 3],
    "policy.action": "delete-everything",
    "policy.decision_point": "admission.somewhere-else",
    "idempotency.retention_s": 60,
    "declaration_version": "9.9",
    "lifecycle.initial": "working",
}
inert = []
for path, value in KNOBS.items():
    decl = copy.deepcopy(base_decl)
    node, parts = decl, path.split(".")
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value
    if state(decl, path.replace(".", "_")) == baseline:
        if re.search(re.escape(parts[-1]), carried):
            continue          # written up as carried and not consumed: allowed
        inert.append(path)
assert not inert, ("declared values that no door and no description reads, and that no row in "
                   "'Carried and not consumed' admits: " + json.dumps(inert))
PYX

# --- h-09 the scope ladder can express one rung per hop it admits ------------
py "$AREA" <<'PY' && ok "h-09 the declared scope ladder narrows at every hop the doors actually use" || bad "h-09 hops past the ladder are issued the same scope"
import glob, json, os, sys
area = sys.argv[1]
decl = json.load(open(os.path.join(area, "admission.json")))
scopes = decl["identity"]["scopes"]
lifetimes = decl["identity"]["hop_lifetime_s"]
deepest = max(len(json.load(open(p))["actor"]["delegation_chain"])
              for p in glob.glob(os.path.join(area, "entries", "*.json")))
assert len(scopes) >= deepest, (
    f"the scope ladder has {len(scopes)} rungs for a chain of {deepest} hops: every hop past "
    f"rung {len(scopes)} is issued the same scope, so per-hop narrowing is claimed, not served")
assert len(lifetimes) >= deepest, (len(lifetimes), deepest)
assert lifetimes[:deepest] == sorted(lifetimes[:deepest], reverse=True), lifetimes
PY

# --- h-10 the differential the README promises is the one that ran -----------
# key_fields is the declaration's own dedup identity: set it to the wall clock
# and one occurrence must split into two keys and two entries.
py "$ROOT" "$WORK" <<'PY' && ok "h-10 DIFFERENTIAL key_fields: the declared derivation, not a hardcoded one, decides the key" || bad "h-10 the key derivation ignores the declaration"
import json, os, subprocess, sys
root, work = sys.argv[1], sys.argv[2]
area = os.path.join(root, "examples", "ask")

def two_deliveries(decl_path, tag):
    ledger = os.path.join(work, f"kf-{tag}.jsonl")
    argv = [sys.executable, "run.py", "--door", "schedule",
            "--again-received-at", "2026-09-04T06:00:00Z",
            "--ledger", ledger, "--json"]
    if decl_path:
        argv += ["--admission", decl_path]
    out = subprocess.run(argv, cwd=area, capture_output=True, text=True)
    return json.loads(out.stdout)

declared = two_deliveries(None, "declared")
assert declared[0]["idempotency_key"] == declared[1]["idempotency_key"], \
    "the wall clock reached the key under the declared derivation"
assert [r["claim"] for r in declared] == ["fresh", "duplicate"], [r["claim"] for r in declared]
assert declared[1]["entries_recorded"] == 1, declared[1]["entries_recorded"]

decl = json.load(open(os.path.join(area, "admission.json")))
decl["key_fields"]["schedule-occurrence"] = ["schedule", "occurrence", "received_at"]
path = os.path.join(work, "wallclock.json")
json.dump(decl, open(path, "w"))
moved = two_deliveries(path, "wallclock")
assert moved[0]["idempotency_key"] != moved[1]["idempotency_key"], \
    "key_fields is not read at derivation: naming the wall clock changed nothing"
assert [r["claim"] for r in moved] == ["fresh", "fresh"], [r["claim"] for r in moved]
assert moved[1]["entries_recorded"] == 2, moved[1]["entries_recorded"]
PY

# --- h-11 the tenant deny costs nothing and records nothing ------------------
( cd "$AREA" && python3 run.py --door human --resource-tenant tenant-other \
    --ledger "$WORK/tenant.jsonl" > "$WORK/tenant.log" 2>&1 )
TRC=$?
py "$WORK" <<'PY' && ok "h-11 a refusal is typed, audited, spends nothing and admits nothing" || bad "h-11 the refusal path is not audited or not typed"
import json, os, sys
work = sys.argv[1]
rows = [json.loads(l) for l in open(os.path.join(work, "tenant.jsonl"))]
assert len(rows) == 1, len(rows)
r = rows[0]
assert r["kind"] == "entry-refused", r["kind"]
p = r["problem"]
assert p["type"].startswith("urn:agentic:problem:") and isinstance(p["status"], int), p
assert p["status"] == 403 and p.get("rule_id"), p
assert p.get("spend_delta_micros") == 0, p
assert r["entries_recorded"] == 0 and r["units_started"] == 0, r
# a refusal is audited like an admission: same two identities, same attested subject
assert r["identity"]["executing_identity"] and r["identity"]["triggering_identity"], r["identity"]
assert r["attested_subject"] == "user:corey", r["attested_subject"]
PY
if [ "$TRC" -eq 2 ]; then ok "h-12 a typed refusal exits 2, not 0"; else bad "h-12 a refusal exited $TRC"; fi

# --- h-13 the receipt is tamper-evident --------------------------------------
sed '1s/"units_started": 0/"units_started": 9/' "$WORK/human.jsonl" > "$WORK/tampered.jsonl"
( cd "$AREA" && python3 run.py --verify-ledger --ledger "$WORK/human.jsonl" >/dev/null 2>&1 )
CLEAN=$?
( cd "$AREA" && python3 run.py --verify-ledger --ledger "$WORK/tampered.jsonl" >/dev/null 2>&1 )
DIRTY=$?
if [ "$CLEAN" -eq 0 ] && [ "$DIRTY" -ne 0 ]; then
  ok "h-13 the chain verifies clean and a one-character edit is detected"
else
  bad "h-13 tamper evidence: clean=$CLEAN tampered=$DIRTY"
fi

# --- h-14 no product name outside README's standards and adapters tables -----
py "$AREA" <<'PYX' && ok "h-14 no product name outside the standards and adapters tables" || bad "h-14 a product name escaped its column"
import glob, os, re, sys
area = sys.argv[1]
products = (r"\bopenai\b", r"\banthropic\b", r"\bclaude\b", r"\baws\b", r"\bazure\b", r"\bgcp\b",
            r"\bkubernetes\b", r"\bdocker\b", r"\btemporal\b", r"\bstripe\b", r"\bopa\b",
            r"\brego\b", r"\bspire\b", r"\bspiffe\b", r"\blitellm\b", r"\bpostgres\w*\b",
            r"\bredis\b", r"\bkafka\b", r"\bfirecracker\b", r"\bgvisor\b", r"\bcedar\b",
            r"\bjaeger\b", r"\bdatadog\b")
files = (glob.glob(os.path.join(area, "*.py")) + glob.glob(os.path.join(area, "*.json"))
         + glob.glob(os.path.join(area, "entries", "*.json")))
assert len(files) >= 8, "only %d source files scanned" % len(files)
hits = [(os.path.basename(f), p) for f in files for p in products
        if re.search(p, open(f).read(), re.I)]
assert not hits, hits
readme = open(os.path.join(area, "README.md")).read()
allowed = set()
for block in (readme.split("## 2. Standards")[1].split("## 3.")[0],
              readme.split("### Adapters")[1].split("### Run steps")[0]):
    allowed |= set(block.splitlines())
rows = []
for i, line in enumerate(readme.splitlines(), 1):
    if line in allowed:
        continue
    for p in products:
        m = re.search(p, line, re.I)
        if m:
            rows.append((i, m.group(0)))
assert not rows, "product names outside their column: %r" % (rows[:6],)
PYX

# --- h-15 the visible check counts something, and its floor bites ------------
( cd "$AREA" && bash test.sh > "$WORK/visible.log" 2>&1 )
VRC=$?
py "$AREA" "$WORK" <<'PY' && ok "h-15 the visible check counts >= 20, fails none, and agrees with provenance" || bad "h-15 the visible count does not hold up"
import json, os, re, sys
area, work = sys.argv[1], sys.argv[2]
lines = [l for l in open(os.path.join(work, "visible.log")) if l.startswith("passed ")]
assert lines, "test.sh printed no `passed N, failed M` line"
n, m = map(int, re.match(r"passed (\d+), failed (\d+)", lines[-1].strip()).groups())
assert m == 0, f"the visible check failed {m}"
assert n >= 20, f"the visible check counted only {n}: a run that counts nothing is not a pass"
# the number in provenance and the floor in test.sh must be read back out of the run
prov = json.load(open(os.path.join(area, "provenance.json")))
assert prov["visible_checks_counted"] == n, (prov["visible_checks_counted"], n)
floor = re.search(r"^FLOOR=(\d+)", open(os.path.join(area, "test.sh")).read(), re.M)
assert floor, "test.sh declares no FLOOR"
assert int(floor.group(1)) == n, (floor.group(1), n)
PY
if [ "$VRC" -eq 0 ]; then ok "h-16 the visible check exits 0"; else bad "h-16 the visible check exited $VRC"; fi

# the floor gate itself, run over the real gate lines with nothing counted
{ grep -E '^(FLOOR=|PASS=0; FAIL=0)' "$AREA/test.sh"
  echo 'echo "passed $PASS, failed $FAIL"'
  grep -E '^\[ "\$(FAIL|PASS)"' "$AREA/test.sh"; } > "$WORK/gate.sh"
bash "$WORK/gate.sh" > "$WORK/gate.log" 2>&1
GRC=$?
if [ "$GRC" -ne 0 ] && grep -q "passed 0" "$WORK/gate.log"; then
  ok "h-17 the floor gate refuses a run that counted nothing"
else
  bad "h-17 a gutted test.sh counting 0 checks would still exit $GRC"
fi

# --- h-18 provenance: cites in both directions, and nothing measured on trust -
py "$AREA" "$WORK" <<'PY' && ok "h-18 provenance cites exactly what the rows carry, and unmeasured claims sit under claimed" || bad "h-18 provenance does not match the example"
import glob, json, os, re, sys
area, work = sys.argv[1], sys.argv[2]
prov = json.load(open(os.path.join(area, "provenance.json")))
for field in ("area", "doors", "cites", "measured", "claimed", "litmus_sections"):
    assert field in prov, f"provenance is missing {field}"
assert prov["area"] == "ask" and sorted(prov["doors"]) == ["event", "external", "human", "schedule"]
assert len(prov["measured"]) >= 10 and len(prov["claimed"]) >= 3, (len(prov["measured"]), len(prov["claimed"]))
cited = set(prov.pop("cites"))
sources = {"provenance.json": json.dumps(prov)}
for path in [os.path.join(area, "README.md"), os.path.join(area, "test.sh")] + \
        glob.glob(os.path.join(area, "*.py")) + glob.glob(os.path.join(area, "*.json")):
    if os.path.basename(path) != "provenance.json":
        sources[path] = open(path).read()
ids = set()
for text in sources.values():
    ids |= set(re.findall(r"\b(?:F|E|R|T|X|REF)-[a-z0-9-]+\b", text))
assert cited == ids, {"cited, never carried by a row": sorted(cited - ids),
                      "carried by a row, never cited": sorted(ids - cited)}
# every gap the README lists must be answered somewhere in claimed
gaps = re.findall(r"^\| (\d+) \|", os.linesep.join(
    open(os.path.join(area, "README.md")).read().split("### Gaps this example exposed")[-1].splitlines()), re.M)
assert len(gaps) >= 5, f"only {len(gaps)} gaps listed"
claimed = " ".join(prov["claimed"]).lower()
missing = [g for g in gaps if f"gap {g}" not in claimed]
assert not missing, f"gaps with no row under provenance.claimed: {missing}"
PY

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
