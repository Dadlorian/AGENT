#!/usr/bin/env bash
# Hidden (deciding) checks for the user-view area "done".
#
# Held out from examples/done/ on purpose: the grader is never visible to the
# graded (F-b1-07). examples/done/test.sh is the area's visible feedback
# surface; this script is what decides, and the author of the example never
# sees it. Every assertion here reads a value back from a receipt line, a
# state record, an attestation envelope, a file on disk or an exit status -
# never a log line the example wrote about itself, and never a literal this
# script set.
#
# Three shapes the row-75 boundary asks for are the backbone here:
#   * a quote is grepped verbatim out of the record it names (h-03);
#   * a declared value is falsified - set to a second value - and the two
#     records are required to differ (h-04, h-05), so a value that is carried
#     but never read at the point of decision fails rather than passes;
#   * a sentence that names its own proof is executed rather than read (h-09,
#     h-10, h-12), with a floor under every count.
#
# It prints `hidden passed N, failed M` and exits non-zero on any failure.
#
#   bash docs/night/hidden/done.sh
#
# Python 3.11 standard library only. No network.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AREA="$ROOT/examples/done"
WORK="${TMPDIR:-/tmp}/hidden-done-$$"
mkdir -p "$WORK"
trap 'rm -rf "$WORK"' EXIT

PASS=0; FAIL=0
ok()  { echo "  ok   $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
py()  { python3 - "$@"; }

if [ ! -d "$AREA" ]; then
  echo "  FAIL examples/done/ does not exist"
  echo; echo "hidden passed 0, failed 1"; exit 1
fi

# ---------------------------------------------------------------- phase A ---
# Static reads. Nothing has been run yet, so nothing below can be answered by
# an artifact this script's own probes produced.

# --- h-01 the six-part README shape, in order --------------------------------
py "$AREA" <<'PY' && ok "h-01 README carries the six headings in order" || bad "h-01 README shape"
import re, sys
head = [l.strip() for l in open(sys.argv[1] + "/README.md") if l.startswith("## ")]
want = ["ideal", "standards", "the call", "what the user sees", "composition", "extension points"]
got = [re.sub(r"^##\s*\d*\.?\s*", "", h).strip().lower() for h in head]
assert len(got) == 6, f"expected 6 top headings, got {len(got)}: {got}"
for g, w in zip(got, want):
    assert g.startswith(w) or w in g, f"heading {g!r} is not {w!r}"
PY

# --- h-02 every quote is verbatim in the record it names ---------------------
# One pass over every prose file of the area, not only the two test.sh checks.
py "$AREA" "$ROOT" <<'PY' && ok "h-02 every quote is verbatim in the record it names" || bad "h-02 a quote is not in the record it cites"
import glob, json, os, re, sys
area, root = sys.argv[1], sys.argv[2]
records = {}
for path in glob.glob(f"{root}/kb/*.jsonl") + glob.glob(f"{root}/kb/research/*.jsonl"):
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("id"):
            records.setdefault(obj["id"], []).append(json.dumps(obj, ensure_ascii=False))
kb = re.compile(r"`((?:F|T|X|D|R)-[A-Za-z0-9-]+)`\s*[\"“]([^\"”]+)[\"”]")
fl = re.compile(r"`FILE:([^`#]+)(?:#[^`]*)?`\s*[\"“]([^\"”]+)[\"”]")
files = ["README.md", "provenance.json"] + sorted(glob.glob(f"{area}/units/*.json")) \
    + sorted(glob.glob(f"{area}/entries/*.json"))
checked, bad = 0, []
for rel in files:
    path = rel if os.path.isabs(rel) else os.path.join(area, rel)
    text = open(path).read()
    for rid, quote in kb.findall(text):
        checked += 1
        blobs = records.get(rid)
        if blobs is None:
            bad.append((os.path.relpath(path, root), rid, "no such record id"))
        elif not any(quote in b for b in blobs):
            bad.append((os.path.relpath(path, root), rid, quote[:70]))
    for rel_file, quote in fl.findall(text):
        checked += 1
        named = os.path.join(root, rel_file.strip())
        if not os.path.exists(named):
            bad.append((os.path.relpath(path, root), rel_file, "no such file"))
        elif quote not in open(named).read():
            bad.append((os.path.relpath(path, root), rel_file, quote[:70]))
assert checked >= 30, f"only {checked} quotes found in {len(files)} files; the rows are not citing"
assert not bad, f"{len(bad)} of {checked} quotes are not in the record they name: {bad[:4]}"
print(f"{checked} quotes over {len(files)} files")
PY

# --- h-03 provenance.cites is exactly what the rows carry, both ways ---------
py "$AREA" "$ROOT" <<'PY' && ok "h-03 provenance.cites agrees with the rows in both directions" || bad "h-03 cites disagree with the rows"
import glob, json, os, re, sys
area, root = sys.argv[1], sys.argv[2]
walked = sorted(glob.glob(f"{area}/*.md") + glob.glob(f"{area}/*.py") + glob.glob(f"{area}/*.sh")
                + glob.glob(f"{area}/*.json") + glob.glob(f"{area}/entries/*.json")
                + glob.glob(f"{area}/units/*.json"))
assert len(walked) >= 9, walked
pattern = re.compile(r"\b((?:F|T|X|D)-[a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b")
carried = set()
for path in walked:
    carried |= set(pattern.findall(open(path).read()))
prov = json.load(open(f"{area}/provenance.json"))
declared = set(prov["cites"])
refs = {c for c in declared if c.startswith("REF-")}
missing = [r for r in refs if not os.path.exists(os.path.join(root, r[4:].split("#")[0]))]
assert not missing, f"REF- entries naming files that are not there: {missing}"
ids = declared - refs
assert ids == carried, {"declared not carried": sorted(ids - carried),
                        "carried not declared": sorted(carried - ids)}
for key in ("measured", "claimed", "litmus_sections", "doors"):
    assert prov.get(key), f"provenance.json has no {key}"
print(f"{len(ids)} ids and {len(refs)} file references over {len(walked)} files")
PY

# --- h-04 section 5 accounts for all six composition operators ---------------
py "$AREA" <<'PY' && ok "h-04 all six operators are accounted for in section 5" || bad "h-04 an operator has no row"
import re, sys
lines = open(sys.argv[1] + "/README.md").read().splitlines()
start = next(i for i, l in enumerate(lines) if re.match(r"^## 5\.", l))
end = next(i for i, l in enumerate(lines[start + 1:], start + 1) if l.startswith("## "))
labels = " | ".join(l.strip().strip("|").split("|")[0].lower() for l in lines[start:end]
                    if l.startswith("| "))
missing = [op for op in ("sequence", "parallel", "bounded loop", "approval gate",
                         "agent call", "judge") if op not in labels]
assert not missing, f"section 5 has no row for {missing}; an operator that is not used needs a row saying so"
print("six operators accounted for")
PY

# ---------------------------------------------------------------- phase B ---
# Probes. Each runs the shipped runner against a document or a declaration the
# shipped example does not ship, and reads the records back.

# --- h-05 the four doors, run here, converge on one subject set --------------
py "$AREA" "$WORK" <<'PY' && ok "h-05 four doors, one closure, one subject set, four identities" || bad "h-05 the four doors do not converge"
import base64, json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
doors = ("human", "event", "schedule", "external")
sealed, actors, corrs, surfaces, full = {}, {}, {}, {}, {}
for d in doors:
    entry = json.load(open(f"{area}/entries/{d}.json"))
    assert entry["kind"] == d, (d, entry["kind"])
    env = dict(os.environ, OBJSTORE_DIR=f"{work}/os-{d}")
    r = subprocess.run(["python3", "run.py", "--entry", f"entries/{d}.json",
                        "--ledger", f"{work}/{d}.jsonl", "--prov-root", f"{work}/prov"],
                       cwd=area, capture_output=True, text=True, env=env)
    assert r.returncode == 0, (d, (r.stdout + r.stderr)[-400:])
    rows = [json.loads(l) for l in open(f"{work}/{d}.jsonl")]
    sealed[d] = tuple(x["subject_digest"] for x in rows if x["kind"] == "subject-sealed")
    actors[d] = {x["actor"] for x in rows}
    corrs[d] = {x["correlation_id"] for x in rows}
    surfaces[d] = [x["surface"] for x in rows if x["kind"] == "notified"][0]
    stmts = [json.loads(base64.b64decode(json.loads(l)["envelope"]["payload"]))
             for l in open(f"{area}/out/attestations-{d}.jsonl")]
    full[d] = [s for s in stmts if not s["predicateType"].endswith("build:0.1")]
    assert len(full[d]) == 1, (d, [s["predicateType"] for s in stmts])
assert len(set(sealed.values())) == 1, f"the doors sealed different subjects: {sealed}"
assert len(sealed["human"]) == 4, sealed["human"]
assert len({next(iter(a)) for a in actors.values()}) == 4, actors
assert len({next(iter(c)) for c in corrs.values()}) == 4, corrs
assert len(set(surfaces.values())) == 4, surfaces
mats = {d: tuple(sorted((m["name"], m["digest"]) for m in full[d][0]["predicate"]["materials"]))
        for d in doors}
assert len(set(mats.values())) == 4, "the entry envelope is not a material of the statement"
print(f"four doors: {len(sealed['human'])} subjects each, four actors, four correlation ids, "
      f"four surfaces")
PY

# --- h-06 every statement is attributable, not only the full one -------------
# The future state is that *every* artifact carries a statement naming the code
# version, the inputs and the actor. This reads every envelope the run above
# wrote, of either fidelity, and asks that of each.
py "$AREA" "$WORK" <<'PY' && ok "h-06 every statement names a code version and the run it came from" || bad "h-06 a statement names neither the code version nor the run"
import base64, glob, json, sys
area, work = sys.argv[1], sys.argv[2]
paths = sorted(glob.glob(f"{work}/prov/attestations.jsonl")
               + glob.glob(f"{area}/out/attestations-*.jsonl"))
assert len(paths) >= 5, paths
thin, total = [], 0
for path in paths:
    for line in open(path):
        if not line.strip():
            continue
        statement = json.loads(base64.b64decode(json.loads(line)["envelope"]["payload"]))
        predicate = statement["predicate"]
        total += 1
        version = predicate.get("code_version") or {}
        corr = ((predicate.get("invocation") or {}).get("correlation")) or {}
        if not version.get("scripts_sha256") or corr.get("run_id") in (None, "", "n/a"):
            thin.append((path.rsplit("/", 1)[-1], statement["predicateType"].rsplit(":", 2)[-2],
                         sorted(version), corr.get("run_id")))
assert total >= 20, f"only {total} statements found across {len(paths)} stores"
# The escape hatch a correct example may take instead: say so in the gap table.
gaps = " ".join(open(f"{area}/README.md").read().split())
written_up = any(term in gaps for term in ("metadata-light record names no code version",
                                           "metadata-light statement names no code version",
                                           "metadata-light statement carries no code version",
                                           "metadata-light record carries no code version"))
assert not thin or written_up, (
    f"{len(thin)} of {total} statements carry no code version or no run id, and no gap row says so: "
    f"{thin[:3]}")
print(f"{total} statements over {len(paths)} stores, {len(thin)} of them thin, "
      f"written up: {written_up}")
PY

# --- h-07 a declared gate rule is read at the decision (differential) --------
# Falsify the declaration rather than read it: drop one rule the closure
# declares and require the same deliberate breakage to be decided differently.
py "$AREA" "$WORK" <<'PY' && ok "h-07 dropping a declared gate rule changes the decision" || bad "h-07 a declared gate rule is decoration"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
base = json.load(open(f"{area}/units/close-checkout-coupon-fix.json"))
rules = base["promotion"]["gate_rules"]
assert "subject-digest-must-match" in rules, rules
seen = {}
for label, declared in (("with", rules), ("without", [r for r in rules if r != "subject-digest-must-match"])):
    doc = json.loads(json.dumps(base)); doc["promotion"]["gate_rules"] = declared
    json.dump(doc, open(f"{work}/closure-{label}.json", "w"))
    entry = json.load(open(f"{area}/entries/human.json"))
    entry["intent"]["workflow_ref"] = os.path.relpath(f"{work}/closure-{label}.json", area)
    entry["correlation"] = {"run_id": f"run-h07-{label}", "correlation_id": f"corr-h07-{label}",
                            "depth": 0}
    entry["idempotency_key"] = f"h07-{label}"
    json.dump(entry, open(f"{work}/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"{work}/entry-{label}.json",
                        "--ledger", f"{work}/h07-{label}.jsonl",
                        "--prov-root", f"{work}/h07-{label}/prov", "--break", "mutate-subject"],
                       cwd=area, capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"{work}/h07-{label}/os"))
    rows = [json.loads(l) for l in open(f"{work}/h07-{label}.jsonl")]
    decided = [x for x in rows if x["kind"] == "promotion-decided"]
    seen[label] = (r.returncode, len([x for x in rows if x["kind"] == "promoted"]),
                   decided[0]["rule_id"] if decided else "",
                   decided[0]["rule_id"] in declared if decided else None)
assert seen["with"][3] is True, f"the refusal names a rule the closure does not declare: {seen['with']}"
assert seen["without"][3] is not False, (
    f"with subject-digest-must-match dropped the gate still refuses by it, so the rule is not read "
    f"at the decision: {seen}")
assert seen["with"][:3] != seen["without"][:3], (
    f"dropping a declared gate rule changed nothing: {seen}")
print("with/without the rule:", seen)
PY

# --- h-08 a declared predicate name is read at the decision (differential) ---
py "$AREA" "$WORK" <<'PY' && ok "h-08 the closure's declared predicate names are read" || bad "h-08 full_predicate/light_predicate are carried and never read"
import base64, json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
base = json.load(open(f"{area}/units/close-checkout-coupon-fix.json"))
declared = base.get("attestation", {})
for member in ("full_predicate", "light_predicate"):
    assert member in declared, f"the closure does not declare {member}"
seen = {}
for label, full_predicate in (("as-declared", declared["full_predicate"]),
                              ("swapped", declared["light_predicate"])):
    doc = json.loads(json.dumps(base)); doc["attestation"]["full_predicate"] = full_predicate
    json.dump(doc, open(f"{work}/pred-{label}.json", "w"))
    entry = json.load(open(f"{area}/entries/human.json"))
    entry["intent"]["workflow_ref"] = os.path.relpath(f"{work}/pred-{label}.json", area)
    entry["correlation"] = {"run_id": f"run-h08-{label}", "correlation_id": f"corr-h08-{label}",
                            "depth": 0}
    entry["idempotency_key"] = f"h08-{label}"
    json.dump(entry, open(f"{work}/entry-h08-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"{work}/entry-h08-{label}.json",
                        "--ledger", f"{work}/h08-{label}.jsonl",
                        "--prov-root", f"{work}/h08-{label}/prov"],
                       cwd=area, capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"{work}/h08-{label}/os"))
    assert r.returncode == 0, (label, (r.stdout + r.stderr)[-300:])
    rows = [json.loads(l) for l in open(f"{work}/h08-{label}.jsonl")]
    seen[label] = sorted({x["predicate_type"] for x in rows if x["kind"] == "attested"})
assert seen["as-declared"] != seen["swapped"], (
    f"attestation.full_predicate is not read where the predicate type is chosen: {seen}")
print("predicate types per arm:", seen)
PY

# --- h-09 a schema-valid document a reader could write is refused, not crashed
py "$AREA" "$WORK" <<'PY' && ok "h-09 a schema-valid entry the shipped set does not reach is typed, not a traceback" || bad "h-09 a schema-valid entry crashes instead of refusing"
import importlib.util, json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("ref_runner", f"{area}/../end-to-end/run.py")
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
schema = json.load(open(f"{area}/../end-to-end/schemas/entry.schema.json"))
entry = json.load(open(f"{area}/entries/human.json"))
entry["actor"]["subject"] = "agent:deep-partner"
entry["actor"]["delegation_chain"] = [
    {"actor": "agent:deep-partner", "obtained_via": "token_exchange"},
    {"actor": "agent:partner-sre-bot", "obtained_via": "token_exchange"},
    {"actor": "service:partner-gateway", "obtained_via": "token_exchange"},
    {"actor": "service:alerting", "obtained_via": "token_exchange"},
    {"actor": "user:corey", "obtained_via": "direct"}]
entry["correlation"] = {"run_id": "run-h09", "correlation_id": "corr-h09", "depth": 0}
entry["idempotency_key"] = "h09-deep-chain"
errs = ref.validate(entry, schema)
assert not errs, f"the probe document is not schema-valid, so it decides nothing: {errs}"
json.dump(entry, open(f"{work}/entry-h09.json", "w"))
r = subprocess.run(["python3", "run.py", "--entry", f"{work}/entry-h09.json",
                    "--ledger", f"{work}/h09.jsonl", "--prov-root", f"{work}/h09/prov"],
                   cwd=area, capture_output=True, text=True,
                   env=dict(os.environ, OBJSTORE_DIR=f"{work}/h09/os"))
out = r.stdout + r.stderr
assert "Traceback" not in out, (
    f"a document that validates against the published entry schema ends in a traceback, "
    f"not a problem object: {out.strip().splitlines()[-1]}")
assert r.returncode in (0, 2), (r.returncode, out[-300:])
if r.returncode == 2:
    body = json.JSONDecoder().raw_decode(out.split("json):\n", 1)[1])[0]
    assert body["type"].startswith("urn:") and isinstance(body["status"], int), body
print("a five-hop schema-valid chain exits", r.returncode, "with no traceback")
PY

# --- h-10 a refusal after admission is recorded, not swallowed ---------------
py "$AREA" "$WORK" <<'PY' && ok "h-10 a capability refusal after admission still leaves a record" || bad "h-10 a refusal after admission is swallowed"
import json, os, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
entry = json.load(open(f"{area}/entries/human.json"))
entry["correlation"] = {"run_id": "run-h10", "correlation_id": "corr-h10", "depth": 0}
entry["idempotency_key"] = "h10-signer-down"
json.dump(entry, open(f"{work}/entry-h10.json", "w"))
r = subprocess.run(["python3", "run.py", "--entry", f"{work}/entry-h10.json",
                    "--ledger", f"{work}/h10.jsonl", "--prov-root", f"{work}/h10/prov"],
                   cwd=area, capture_output=True, text=True,
                   env=dict(os.environ, OBJSTORE_DIR=f"{work}/h10/os", PROVENANCE_FAIL="1"))
assert r.returncode == 2, (r.returncode, (r.stdout + r.stderr)[-300:])
assert os.path.exists(f"{work}/h10.jsonl"), "the refused run wrote no receipt at all"
kinds = [json.loads(l)["kind"] for l in open(f"{work}/h10.jsonl")]
assert "run-rejected" in kinds, (
    f"the signer refused after the entry was admitted and the run left no run-rejected record; "
    f"the receipt ends at {kinds[-1]!r}: {kinds}")
sealed = kinds.count("subject-sealed")
assert sealed == kinds.count("attested"), (
    f"{sealed} subjects sealed and {kinds.count('attested')} attested in the same receipt")
print("refused after admission, recorded:", kinds)
PY

# ---------------------------------------------------------------- phase C ---
# The visible surface, run rather than read. This also leaves examples/done/out
# as `bash examples/done/test.sh` leaves it, whatever the probes above wrote.

VIS="$WORK/visible.log"
( cd "$ROOT" && bash examples/done/test.sh ) > "$VIS" 2>&1
VIS_EXIT=$?
VIS_LAST=$(tail -n 1 "$VIS")

py "$AREA" "$VIS" "$VIS_EXIT" <<'PY' && ok "h-11 the visible check is green at the count three files promise" || bad "h-11 the visible check is not green at the promised count"
import json, re, sys
area, log, exit_status = sys.argv[1], sys.argv[2], int(sys.argv[3])
last = open(log).read().strip().splitlines()[-1]
match = re.match(r"^passed (\d+), failed (\d+)$", last)
assert match, f"the visible check's last line is not a count: {last!r}"
counted, failed = int(match.group(1)), int(match.group(2))
floor = int(re.search(r"^FLOOR=(\d+)$", open(f"{area}/test.sh").read(), re.M).group(1))
declared = json.load(open(f"{area}/provenance.json"))["visible_checks_counted"]
promised = [l for l in open(f"{area}/README.md") if "test.sh" in l and "passed" in l]
assert len(promised) == 1, f"{len(promised)} README rows promise a count"
readme = int(re.search(r"passed (\d+), failed 0", promised[0]).group(1))
assert floor >= 20, f"the floor is {floor}; a suite this small cannot decide the area"
assert failed == 0 and exit_status == 0, (
    f"the visible check printed {last!r} and exited {exit_status}")
assert counted == floor == declared == readme, (
    f"printed {counted}, FLOOR {floor}, provenance {declared}, README {readme}")
print(f"passed {counted}, failed {failed}; floor, provenance and README all {floor}")
PY

# --- h-12 the gate has a floor: a gutted copy of the suite cannot pass -------
py "$AREA" "$WORK" <<'PY' && ok "h-12 a gutted copy of the visible check exits non-zero" || bad "h-12 a suite that counts nothing still passes"
import os, re, subprocess, sys
area, work = sys.argv[1], sys.argv[2]
body = open(f"{area}/test.sh").read()
floor = re.search(r"^FLOOR=(\d+)$", body, re.M).group(1)
gate = [l for l in body.splitlines() if l.startswith("[ \"$FAIL\"") or l.startswith("[ \"$PASS\"")]
assert len(gate) == 2, f"the suite does not gate on both halves: {gate}"
hollow = f"{work}/hollow.sh"
open(hollow, "w").write("set -u\nFLOOR=%s\nPASS=0; FAIL=0\necho\necho \"passed $PASS, failed $FAIL\"\n%s\n"
                        % (floor, "\n".join(gate)))
r = subprocess.run(["bash", hollow], capture_output=True, text=True)
assert r.returncode != 0, "a copy of the suite that counts nothing exited 0"
print(f"a hollow copy counting 0 against a floor of {floor} exits {r.returncode}")
PY

# --- h-13 no product name outside the standards and adapters tables ---------
py "$AREA" <<'PY' && ok "h-13 no product name outside the two exempt README tables" || bad "h-13 a product is named outside the adapters"
import os, re, sys
area = sys.argv[1]
names = re.compile(r"\b(sigstore|rekor|fulcio|cosign|kyverno|spiffe|spire|tekton|github|gitlab|"
                   r"s3|aws|amazon|azure|gcs|npm|pypi|maven|opa|rego|firecracker|openai|anthropic|"
                   r"datadog|jaeger|kubernetes|vault|postgres|kafka)\b", re.I)
lines = open(f"{area}/README.md").read().splitlines()
starts = {t: next(i for i, l in enumerate(lines) if l.startswith(t))
          for t in ("## 2. Standards", "## 3. The call", "### Adapters", "### Run steps")}
exempt = set(range(starts["## 2. Standards"], starts["## 3. The call"])) \
    | set(range(starts["### Adapters"], starts["### Run steps"]))
sources, artifacts, hits, marked = [], [], [], 0
for root, dirs, files in os.walk(area):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for name in sorted(files):
        path = os.path.join(root, name)
        (artifacts if os.path.relpath(path, area).startswith("out/") else sources).append(path)
assert len(sources) >= 8, f"only {len(sources)} source files found"
assert len(artifacts) >= 100, f"only {len(artifacts)} artifacts found; the object stores were missed"
for path in sources + artifacts:
    if path.endswith(".pyc"):
        continue
    for i, line in enumerate(open(path, errors="replace").read().splitlines()):
        if "namecheck" in line:
            marked += 1
            continue
        if path.endswith("README.md") and os.path.dirname(path) == area and i in exempt:
            continue
        if names.search(line):
            hits.append(f"{os.path.relpath(path, area)}:{i + 1}")
assert marked <= 4, f"{marked} lines exempt themselves with a marker; the escape hatch is load-bearing"
assert not hits, hits[:6]
print(f"{len(sources)} source files and {len(artifacts)} artifacts scanned, {marked} marked lines, "
      f"no product named outside the two tables")
PY

echo
echo "hidden passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge 8 ] || { echo "only $PASS hidden checks ran"; exit 1; }
