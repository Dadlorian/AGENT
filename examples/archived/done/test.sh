#!/usr/bin/env bash
# The visible check for examples/done. Everything here is measured, not claimed.
# It prints `passed N, failed 0` with N counting checks that actually ran; a run
# that counts nothing is a defect, not a pass, so the gate at the bottom has two
# halves: no failure, and a floor under the number of checks that ran. A gutted
# copy of this file counts zero and is refused there rather than exiting 0
# (`F-a7-03` "A deterministic gate can be structurally green and mean nothing").
# FLOOR moves with provenance.json's visible_checks_counted.
#
# Every check whose label names a claim was falsified first: the claim was
# broken and this section - not the suite - was required to go red.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=81
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }
# one run of one door, in its own object store so two runs of the same door can
# never accumulate into one partition
door() { OBJSTORE_DIR="out/os-$1" python3 run.py --entry "$2" --ledger "out/$1.jsonl" \
           --records-out "out/$1.state.json" --bundle-out "out/$1.bundle.json" "${@:3}"; }

rm -rf out && mkdir -p out out/v

echo "1. four doors, one closure declaration"
for d in human event schedule external; do
  door "$d" "entries/$d.json" > "out/$d.log" 2>&1
  check "$d exits 0" "$?" "0"
  grep -q "^closed: 4 units" "out/$d.log" && ok "$d closed four units" || bad "$d did not close"
done
py <<'PY' > out/doors.log 2>&1
import json
doors = ("human", "event", "schedule", "external")
rows = {d: [json.loads(l) for l in open(f"out/{d}.jsonl")] for d in doors}
sealed = {d: tuple(r["subject_digest"] for r in v if r["kind"] == "subject-sealed")
          for d, v in rows.items()}
assert len(set(sealed.values())) == 1, f"the doors sealed different subjects: {sealed}"
assert len(sealed["human"]) == 4, sealed["human"]
# the run-output predicate: same materials, same code version, four actors
mats = {}
for d in doors:
    env = [json.loads(l) for l in open(f"out/attestations-{d}.jsonl")]
    import base64
    stmts = [json.loads(base64.b64decode(e["envelope"]["payload"])) for e in env]
    full = [s for s in stmts if s["predicateType"].endswith("agent-action:0.1")]
    assert len(full) == 1, f"{d}: {len(full)} run-output statements"
    p = full[0]["predicate"]
    mats[d] = (tuple(sorted((m["name"], m["digest"]) for m in p["materials"] if m["name"] != "entry-envelope")),
               json.dumps(p["code_version"], sort_keys=True))
assert len(set(mats.values())) == 1, "the doors named different inputs or code versions"
assert len({tuple(sorted((m["name"], m["digest"]) for m in
                         json.loads(base64.b64decode([json.loads(l) for l in open(f"out/attestations-{d}.jsonl")][0]["envelope"]["payload"]))["predicate"]["materials"]))
            for d in doors}) == 4, "the entry envelope did not reach the predicate"
# what section 17 re-reads at the end of the suite: this is the store these
# assertions were made over, so a later run that rewrote it would be caught.
json.dump({d: [json.loads(l)["id"] for l in open(f"out/attestations-{d}.jsonl")]
           for d in doors}, open("out/doors-envelopes.json", "w"))
actors = {d: {r["actor"] for r in v} for d, v in rows.items()}
assert all(len(a) == 1 for a in actors.values()) and len({next(iter(a)) for a in actors.values()}) == 4, actors
corr = {d: {r["correlation_id"] for r in v} for d, v in rows.items()}
assert all(len(c) == 1 for c in corr.values()) and len({next(iter(c)) for c in corr.values()}) == 4, corr
surfaces = {d: [r["surface"] for r in v if r["kind"] == "notified"][0] for d, v in rows.items()}
assert len(set(surfaces.values())) == 4, surfaces
print("one subject set", sealed["human"][0][:19], "| four actors, four correlation ids, four surfaces")
PY
check "four doors seal one subject set and one predicate, under four identities" "$?" "0"
grep -q "^one subject set" out/doors.log && ok "the entry envelope is a material of every statement" \
  || bad "the per-door material did not separate"
py <<'PY' > out/chains.log 2>&1
import json
for d, hops in (("human", 2), ("event", 3), ("schedule", 3), ("external", 4)):
    env = json.load(open(f"entries/{d}.json"))
    declared = [h["actor"] for h in env["actor"]["delegation_chain"]]
    rec = [json.loads(l) for l in open(f"out/{d}.jsonl") if '"identity-resolved"' in l][0]
    assert rec["chain"] == [f"agent:closer-{d}"] + declared, (d, rec["chain"], declared)
    assert rec["hops"] == hops == len(declared) + 1, (d, rec["hops"], hops)
    assert rec["acting_for"] == declared[-1] and rec["executing_identity"] == rec["chain"][0], rec
    assert rec["scope"] == ["write:ledger"], rec["scope"]
print("chains", {d: len(json.load(open(f'entries/{d}.json'))['actor']['delegation_chain']) for d in
                 ("human", "event", "schedule", "external")}, "+1 executing hop each")
PY
check "the issued chain is the declared chain in order, plus one hop for the executor" "$?" "0"

echo "2. the four documents, one published shape"
py <<'PY' > out/schema.log 2>&1
import importlib.util, json, os
spec = importlib.util.spec_from_file_location("ref", "../end-to-end/run.py")
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
schema = json.load(open("../end-to-end/schemas/entry.schema.json"))
for d in ("human", "event", "schedule", "external"):
    errs = ref.validate(json.load(open(f"entries/{d}.json")), schema)
    assert not errs, (d, errs)
print("four entry documents validate against the published entry schema")
PY
check "all four validate with the reference example's own validator" "$?" "0"
py <<'PY' > out/nolib.log 2>&1
import json
for d in ("human", "event", "schedule", "external"):
    blob = json.dumps(json.load(open(f"entries/{d}.json"))).lower()
    for banned in ("import ", "sdk", "client_library", "adapter", "signer", "keyid"):
        assert banned not in blob, (d, banned)
print("four documents, no client library of ours and no signer, key or adapter named in any of them")
PY
check "a caller needs no client library this repository wrote" "$?" "0"
python3 run.py --entry out/v/nothing-here.json > out/missing.log 2>&1
check "an entry document that is not there is a typed refusal, not a traceback" "$?" "2"
grep -q '"status": 422' out/missing.log && ok "the missing document is 422 document-invalid" \
  || bad "the missing document was not typed"
py <<'PY' > out/malformed2.log 2>&1
import json, subprocess
bad = json.load(open("entries/human.json")); del bad["idempotency_key"]
json.dump(bad, open("out/v/malformed.json", "w"))
r = subprocess.run(["python3", "run.py", "--entry", "out/v/malformed.json",
                    "--ledger", "out/v/malformed.jsonl"], capture_output=True, text=True)
assert r.returncode == 2, r.returncode
body = json.JSONDecoder().raw_decode(r.stdout.split("json):\n", 1)[1])[0]
assert body["type"].endswith("document-invalid") and body["status"] == 422, body
assert any("idempotency_key" in c for c in body["causes"]), body["causes"]
import os
assert not os.path.exists("out/v/malformed.jsonl"), "a refused envelope still wrote a receipt"
print("422 document-invalid naming the missing member, no receipt written")
PY
check "422 names the missing member and writes no receipt" "$?" "0"

echo "3. the check report decides, and inconclusive is never passed"
py <<'PY' > out/ladder.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl")]
closed = {r["unit_id"]: r for r in rows if r["kind"] == "unit-closed"}
want = {"fix-checkout-coupon-500s": ("completed", "task success", "accept"),
        "dedupe-incident-notifier": ("failed", "candidate completion", "escalate"),
        "rotate-coupon-cache-keys": ("rejected", "none", "reject"),
        "document-coupon-tiers": ("input-required", "candidate completion", "escalate")}
for unit, (state, rung, disposition) in want.items():
    got = closed[unit]
    assert (got["task_state"], got["ladder_rung"], got["disposition"]) == (state, rung, disposition), got
lifecycle = {"submitted", "working", "input-required", "completed", "failed", "rejected", "canceled"}
assert {r["task_state"] for r in closed.values()} <= lifecycle, "a state name was invented"
zero = closed["document-coupon-tiers"]
assert zero["behavioural_run"] == 0 and zero["deciding_failed"] == [] and zero["ladder_rung"] != "task success"
promoted = [r["unit_id"] for r in rows if r["kind"] == "promoted"]
assert promoted == ["fix-checkout-coupon-500s"], promoted
print("four units, four dispositions; the one with behavioural_run 0 passed every deciding check and "
      "is parked at input-required, not promoted")
PY
check "a report with behavioural_run 0 is inconclusive, never task success" "$?" "0"
grep -q "not promoted$" out/ladder.log && ok "only the unit at task success is promoted" \
  || bad "promotion did not follow the ladder"

echo "4. every unit leaves a record, counted rather than assumed"
py <<'PY' > out/coverage.log 2>&1
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("done_emit", "../../harness/provenance/emit.py")
emit = importlib.util.module_from_spec(spec); sys.modules["done_emit"] = emit; spec.loader.exec_module(emit)
root = "out/provenance"
rep = emit.reconcile(root)
assert rep["reconciled"] and not rep["unattested"], rep
subjects = set()
for d in ("human", "event", "schedule", "external"):
    subjects |= {r["subject_digest"] for r in (json.loads(l) for l in open(f"out/{d}.jsonl"))
                 if r["kind"] == "attested"}
produced = emit.produced_artifacts(root)
assert rep["artifacts_produced"] == len(produced) == len(subjects), (rep, len(produced), len(subjects))
registered = {e["artifact_id"] for e in emit.manifest_entries(root)}
assert registered == set(produced), (registered ^ set(produced))
print(f"{rep['artifacts_produced']} distinct artifacts in the store, "
      f"{rep['attestations_valid']} with a statement that resolves, "
      f"{len(emit.manifest_entries(root))} registrations across four doors, 0 unattested")
PY
check "artifacts produced reconcile against statements that resolve" "$?" "0"
py <<'PY' > out/coverage-bypass.log 2>&1
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("done_emit", "../../harness/provenance/emit.py")
emit = importlib.util.module_from_spec(spec); sys.modules["done_emit"] = emit; spec.loader.exec_module(emit)
root = "out/provenance"
before = emit.reconcile(root)
open(f"{root}/artifacts/smuggled-work-product", "wb").write(b"promoted without a statement\n")
after = emit.reconcile(root)
assert before["reconciled"] and not after["reconciled"], (before, after)
assert after["unattested"] == ["smuggled-work-product"], after
try:
    emit.register_or_refuse(root, "smuggled-work-product", "sha256:" + "0" * 64, "x", "urn:made-up")
    raise AssertionError("the one write path accepted an unattested registration")
except Exception as exc:
    refused = type(exc).__name__ == "Problem"
assert refused, "the refusal was not the typed one"
import os
os.remove(f"{root}/artifacts/smuggled-work-product")
assert emit.reconcile(root)["reconciled"], "the store did not come back to reconciled"
print("a file dropped into the artifact store is caught by enumeration, and the one write path "
      "refuses to register it")
PY
check "an artifact written outside the wired path is caught (deliberate breakage)" "$?" "0"

py <<'PYL' > out/light-shape.log 2>&1
import base64, json
# The narrowed sentence in README section 3 says the entry envelope's digest is
# a material of every *run-output* statement. This reads back what the other
# statements of the same run carry, so gap G15 is measured rather than asserted.
full, light = [], []
for d in ("human", "event", "schedule", "external"):
    for line in open(f"out/attestations-{d}.jsonl"):
        doc = json.loads(base64.b64decode(json.loads(line)["envelope"]["payload"]))
        full.append((d, doc))
for line in open("out/provenance/attestations.jsonl"):
    light.append(json.loads(base64.b64decode(json.loads(line)["envelope"]["payload"])))
attested = [r for d in ("human", "event", "schedule", "external")
            for r in (json.loads(l) for l in open(f"out/{d}.jsonl")) if r["kind"] == "attested"]
assert len(full) == 4, f"{len(full)} run-output statements over four doors"
# one light statement per attested record, counted out of the receipts rather
# than written down here: sixteen units over four doors plus the review request
# the pull-request door seals.
assert len(light) == len(attested), (len(light), len(attested))
assert len(light) == 17, f"{len(light)} metadata-light statements, not 17"
for d, doc in full:
    pred = doc["predicate"]
    assert any(m["name"] == "entry-envelope" for m in pred["materials"]), d
    assert pred["code_version"]["scripts_sha256"], d
    assert pred["invocation"]["correlation"]["run_id"].startswith("run-done-"), d
named_run = [x for x in light if x["predicate"]["invocation"]["correlation"]["run_id"] != "n/a"]
named_code = [x for x in light if x["predicate"]["code_version"]["scripts_sha256"]]
with_envelope = [x for x in light
                 if any(m["name"] == "entry-envelope" for m in x["predicate"]["materials"])]
assert (named_run, named_code, with_envelope) == ([], [], []), (
    len(named_run), len(named_code), len(with_envelope))
print(f"{len(full)} run-output statements name the envelope, the code version and the run; "
      f"{len(light)} metadata-light statements, one per attested record, name none of the three "
      f"(gap G15)")
PYL
check "the run-output statement names the run and the code version; the light record names neither" "$?" "0"

py <<'PYG' > out/gap-light.log 2>&1
import base64, json
# F-b4-05 asks every artifact to be attributable to the code version, the inputs
# and the actor. Some statements this example writes cannot be: the gap row has
# to name exactly which ones, in the fields a reader can check, and its counts
# are read back out of the statements rather than out of its neighbours.
def statements(path):
    return [json.loads(base64.b64decode(json.loads(l)["envelope"]["payload"]))
            for l in open(path)]
light = statements("out/provenance/attestations.jsonl")
full = [s for d in ("human", "event", "schedule", "external")
        for s in statements(f"out/attestations-{d}.jsonl")]
def binds(doc):
    # the code version, by the exact digest of every script that ran, and the
    # run: the two a verifier needs to attribute the bytes to a version and an
    # execution. `git_commit` is whatever the environment named and is "unset"
    # in both stores here, so it separates nothing and is not the test.
    pred = doc["predicate"]
    return (bool(pred["code_version"]["scripts_sha256"])
            and pred["invocation"]["correlation"]["run_id"] not in ("", "n/a", "unset"))
cannot = [d for d in light + full if not binds(d)]
assert [d for d in full if not binds(d)] == [], "a run-output statement binds neither"
assert len(cannot) == len(light), (len(cannot), len(light))
rows = [l for l in open("README.md") if l.startswith("| G15 |")]
assert len(rows) == 1, f"{len(rows)} rows of the gap table are G15"
row = rows[0]
for owed in (f"{len(cannot)} of the {len(light) + len(full)}", "metadata-light",
             "attestations.jsonl", "code_version.scripts_sha256",
             "code_version.git_commit", "invocation.correlation.run_id",
             "harness/provenance/emit.py"):
    assert owed in row, f"the gap row does not say {owed!r}"
print(f"{len(cannot)} of {len(light) + len(full)} statements cannot bind the code version and the "
      f"run id, and G15 names exactly those, by store and by field")
PYG
check "the gap row says which statements cannot name the code version and the run" "$?" "0"

echo "5. materiality is read at the decision (differential)"
mkdir -p out/v
py <<'PY' > out/materiality.log 2>&1
import json, os, subprocess
base = json.load(open("units/close-checkout-coupon-fix.json"))
arms = {"declared": base["attestation"]["materiality"],
        "with-refusals": ["produced-artifact", "refusal-worth-auditing"],
        "every-unit": ["every-unit"]}
counts = {}
for label, materiality in arms.items():
    doc = json.loads(json.dumps(base)); doc["attestation"]["materiality"] = materiality
    os.makedirs(f"out/v/{label}", exist_ok=True)
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    entry = json.load(open("entries/human.json"))
    entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"materiality-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    env = dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os")
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    rows = [json.loads(l) for l in open(f"out/v/{label}.jsonl")]
    att = [r for r in rows if r["kind"] == "attested"]
    counts[label] = (sum(1 for a in att if a["fidelity"] == "full"),
                     sum(1 for a in att if a["fidelity"] == "metadata-light"),
                     len([r for r in rows if r["kind"] == "published"]))
assert counts["declared"] == (1, 3, 1), counts
assert counts["with-refusals"] == (2, 2, 2), counts
assert counts["every-unit"] == (4, 0, 4), counts
assert all(c[0] + c[1] == 4 for c in counts.values()), "a unit escaped the record when fidelity moved"
print("full/light/published per materiality:", counts)
PY
check "three materiality values give 1, 2 and 4 full statements over the same 4 records" "$?" "0"
grep -q "'every-unit': (4, 0, 4)" out/materiality.log \
  && ok "every-unit publishes four; the record count never drops" || bad "the every-unit arm did not move"

echo "6. the admission gate refuses before anything is promoted (four breakages)"
for pair in unattested:attested-subject-required mutate-subject:subject-digest-must-match \
            build-predicate:run-output-predicate-required resign:statement-must-verify; do
  brk=${pair%%:*}; rule=${pair##*:}
  OBJSTORE_DIR="out/v/brk-$brk/os" python3 run.py --entry entries/human.json \
    --ledger "out/v/brk-$brk.jsonl" --prov-root "out/v/brk-$brk/prov" --break "$brk" \
    > "out/v/brk-$brk.log" 2>&1
  check "--break $brk ends the closure" "$?" "2"
  grep -q "\"rule_id\": \"$rule\"" "out/v/brk-$brk.log" \
    && ok "--break $brk is refused by $rule" || bad "--break $brk did not name $rule"
done
py <<'PY' > out/gate.log 2>&1
import json
for brk, rule in (("unattested", "attested-subject-required"),
                  ("mutate-subject", "subject-digest-must-match"),
                  ("build-predicate", "run-output-predicate-required"),
                  ("resign", "statement-must-verify")):
    rows = [json.loads(l) for l in open(f"out/v/brk-{brk}.jsonl")]
    decided = [r for r in rows if r["kind"] == "promotion-decided"]
    assert len(decided) == 1 and decided[0]["admitted"] is False, (brk, decided)
    assert decided[0]["rule_id"] == rule, (brk, decided[0])
    assert rule in decided[0]["gate_rules"], "the rule that decided is not one the closure declared"
    assert not [r for r in rows if r["kind"] == "promoted"], f"{brk} promoted anyway"
    rejected = [r for r in rows if r["kind"] == "run-rejected"]
    assert len(rejected) == 1 and rejected[0]["rule_id"] == rule, (brk, rejected)
    assert [r for r in rows if r["kind"] == "attested"], f"{brk} left no record of the units it closed"
good = [json.loads(l) for l in open("out/human.jsonl")]
assert [r for r in good if r["kind"] == "promotion-decided"][0]["admitted"] is True
assert [r["verification_checks"] for r in good if r["kind"] == "promotion-decided"] == [4]
print("four refusals, each named by the declared rule that decided; a refused run is itself recorded")
PY
check "each refusal names its rule, promotes nothing, and is recorded" "$?" "0"
grep -q "^four refusals" out/gate.log && ok "all four declared rules refuse something" \
  || bad "the four breakages did not each refuse"

py <<'PY2' > out/gate-rules.log 2>&1
import json, os, subprocess
# the gate rules are a list the closure declares, not a branch in the runner.
# Each of the four is removed in turn, against the breakage only that rule
# catches: with it declared the run is refused and names it, without it the
# same breakage walks straight through and the subject is promoted.
BREAKAGE = {"attested-subject-required": "unattested",
            "subject-digest-must-match": "mutate-subject",
            "run-output-predicate-required": "build-predicate",
            "statement-must-verify": "resign"}
base = json.load(open("units/close-checkout-coupon-fix.json"))
declared = base["promotion"]["gate_rules"]
assert sorted(declared) == sorted(BREAKAGE), (declared, sorted(BREAKAGE))
seen = {}
for rule, brk in BREAKAGE.items():
    for arm, rules in (("with", declared), ("without", [r for r in declared if r != rule])):
        label = f"{arm}-{rule}"
        doc = json.loads(json.dumps(base)); doc["promotion"]["gate_rules"] = rules
        json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
        entry = json.load(open("entries/human.json"))
        entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
        entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
        entry["idempotency_key"] = f"rules-{label}-2026-09-03"
        json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
        r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                            "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov",
                            "--break", brk], capture_output=True, text=True,
                           env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
        rows = [json.loads(l) for l in open(f"out/v/{label}.jsonl")]
        decided = [x for x in rows if x["kind"] == "promotion-decided"][0]
        seen[label] = (r.returncode, [x["kind"] for x in rows].count("promoted"), decided["rule_id"])
        assert rule in decided["gate_rules"] if arm == "with" else rule not in decided["gate_rules"]
for rule in BREAKAGE:
    assert seen[f"with-{rule}"] == (2, 0, rule), (rule, seen[f"with-{rule}"])
    assert seen[f"without-{rule}"] == (0, 1, ""), (rule, seen[f"without-{rule}"])
assert len(seen) == 8, seen
print(f"{len(BREAKAGE)} declared rules, {len(seen)} arms: each rule removed lets through exactly the "
      f"breakage it was the only rule to catch")
PY2
check "each of the four gate rules is read where it decides (differential)" "$?" "0"
grep -q "^4 declared rules, 8 arms" out/gate-rules.log \
  && ok "no declared rule is a label the gate never reads" || bad "a declared rule decided nothing"
py <<'PY7' > out/predicate-declared.log 2>&1
import base64, json, os, subprocess
# attestation.full_predicate is a name the closure declares; the URI it resolves
# to is the interface's. Swapping the declared name moves the predicate type on
# the statement the run writes and the type the gate says it will accept.
base = json.load(open("units/close-checkout-coupon-fix.json"))
seen = {}
for label, name in (("pred-agent-action", "agent-action"), ("pred-build", "build")):
    doc = json.loads(json.dumps(base)); doc["attestation"]["full_predicate"] = name
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    entry = json.load(open("entries/human.json"))
    entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"predicate-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    assert r.returncode == 0, r.stdout + r.stderr
    rows = [json.loads(l) for l in open(f"out/v/{label}.jsonl")]
    recorded = [x["predicate_type"] for x in rows if x["kind"] == "attested" and
                x["fidelity"] == "full"]
    envelope = [json.loads(l) for l in open(f"out/v/{label}/prov/envelopes-human.jsonl")]
    on_statement = [json.loads(base64.b64decode(e["envelope"]["payload"]))["predicateType"]
                    for e in envelope]
    seen[label] = (recorded, on_statement, [x["kind"] for x in rows].count("promoted"))
assert seen["pred-agent-action"][0] == seen["pred-agent-action"][1], seen["pred-agent-action"]
assert seen["pred-build"][0] == seen["pred-build"][1], seen["pred-build"]
assert seen["pred-agent-action"][0] != seen["pred-build"][0], seen
assert seen["pred-agent-action"][0][0].endswith("agent-action:0.1"), seen
assert seen["pred-build"][0][0].endswith("build:0.1"), seen
assert seen["pred-agent-action"][2] == seen["pred-build"][2] == 1, seen
print("the declared predicate name reaches the statement and the gate's expectation together:",
      [seen[k][0][0].rsplit(":", 2)[-2] for k in ("pred-agent-action", "pred-build")])
PY7
check "attestation.full_predicate is read where the statement is made (differential)" "$?" "0"
py <<'PY9' > out/predicate-light.log 2>&1
import base64, json, os, subprocess
# attestation.light_predicate names the type this closure expects the wired
# boundary to put on the metadata-light statement. The boundary takes no
# argument for it (gap G15), so the declaration is read against the type that
# boundary publishes, before any subject is sealed: declaring a type it does
# not attest with ends the run with a typed problem and no statement written.
base = json.load(open("units/close-checkout-coupon-fix.json"))
declared = base["attestation"]["light_predicate"]
assert declared != base["attestation"]["full_predicate"], base["attestation"]
seen = {}
for label, name in (("light-declared", declared), ("light-wrong", base["attestation"]["full_predicate"])):
    doc = json.loads(json.dumps(base)); doc["attestation"]["light_predicate"] = name
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    entry = json.load(open("entries/human.json"))
    entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"light-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    seen[label] = r
ok_run = seen["light-declared"]
assert ok_run.returncode == 0, ok_run.stdout + ok_run.stderr
rows = [json.loads(l) for l in open("out/v/light-declared.jsonl")]
light = [x["predicate_type"] for x in rows if x["kind"] == "attested"
         and x["fidelity"] == "metadata-light"]
# what the boundary actually wrote, read back out of its own store rather than
# off the record that claims it
written = {json.loads(base64.b64decode(json.loads(l)["envelope"]["payload"]))["predicateType"]
           for l in open("out/v/light-declared/prov/attestations.jsonl")}
assert len(light) == 3 and set(light) == written, (light, written)
assert all(t.endswith(f"{declared}:0.1") for t in light), light
wrong = seen["light-wrong"]
assert wrong.returncode == 2, wrong.stdout + wrong.stderr
body = json.JSONDecoder().raw_decode(wrong.stdout.split("json):\n", 1)[1])[0]
assert body["status"] == 422 and body["type"].endswith("document-invalid"), body
assert base["attestation"]["full_predicate"] in body["detail"], body
assert not os.path.exists("out/v/light-wrong/prov/attestations.jsonl"), "a statement was written"
assert not os.path.exists("out/v/light-wrong.jsonl"), "a record was written before the refusal"
print(f"the declared light predicate {declared!r} is the type on all {len(light)} metadata-light "
      f"records and in the boundary's own store; declaring "
      f"{base['attestation']['full_predicate']!r} for it is refused 422 with nothing attested")
PY9
check "attestation.light_predicate is read against the boundary that types it (differential)" "$?" "0"
PROVENANCE_FAIL=1 OBJSTORE_DIR=out/v/capability-refusal/os python3 run.py \
  --entry entries/human.json --ledger out/v/capability-refusal.jsonl \
  --prov-root out/v/capability-refusal/prov > out/v/capability-refusal.log 2>&1
check "a capability that refuses after admission ends the closure" "$?" "2"
py <<'PY8' > out/capability-refusal.log 2>&1
import json
rows = [json.loads(l) for l in open("out/v/capability-refusal.jsonl")]
kinds = [r["kind"] for r in rows]
body = json.JSONDecoder().raw_decode(
    open("out/v/capability-refusal.log").read().split("json):\n", 1)[1])[0]
assert body["status"] == 503 and body["type"].endswith("adapter-unavailable"), body
rejected = [r for r in rows if r["kind"] == "run-rejected"]
assert len(rejected) == 1 and rejected[0]["problem_type"] == body["type"], (rejected, body)
assert kinds[-1] == "run-rejected", kinds
for receipt in ("out/v/capability-refusal.jsonl", "out/human.jsonl", "out/external.jsonl"):
    lines = [json.loads(l) for l in open(receipt)]
    sealed = sum(1 for r in lines if r["kind"] == "subject-sealed")
    attested = sum(1 for r in lines if r["kind"] == "attested")
    assert sealed <= attested, (receipt, sealed, attested)
assert not [r for r in rows if r["kind"] == "subject-sealed"], "a subject was sealed but not attested"
print("a signer that refuses after the entry was admitted leaves one run-rejected record, "
      "and no receipt ends with more subjects sealed than attested")
PY8
check "a refusal a capability raised is recorded like one this runner raised" "$?" "0"

echo "7. verification reads the envelope, not our store"
cat > out/v/verify_alone.py <<'PY'
"""A holder of the artifact, the statement and the public material, and nothing
else: no adapter is imported and the working directory is not ours."""
import importlib.util, json, os, sys
bundle = json.load(open(os.path.abspath(sys.argv[1])))
iface_path = os.path.abspath(sys.argv[2])
if len(sys.argv) > 3 and sys.argv[3] == "--falsify":      # one byte of the artifact moves
    # every subject the policy expects, not the first: a policy that expects
    # none has nothing to falsify, which is what a closure that does not declare
    # subject-digest-must-match hands its third party.
    for name, digest in list(bundle["policy"]["expected_subjects"].items()):
        bundle["policy"]["expected_subjects"][name] = digest[:-1] + ("0" if digest[-1] != "0" else "1")
os.chdir("/")
spec = importlib.util.spec_from_file_location("prov_iface", iface_path)
iface = importlib.util.module_from_spec(spec)
sys.modules["prov_iface"] = iface
spec.loader.exec_module(iface)
result = iface.verify(bundle["envelope"], iface.TrustPolicy.from_dict(bundle["policy"]),
                      bundle["proof"], bundle["material"])
print(json.dumps({"accepted": result.accepted, "checks": len(result.checks),
                  "subject_mismatches": result.subject_mismatches,
                  "predicate_type": result.predicate_type,
                  "adapters_imported": [m for m in sys.modules if m.startswith("adapters")]}))
sys.exit(0 if result.accepted else 3)
PY
python3 out/v/verify_alone.py out/human.bundle.json ../../harness/provenance/interface.py \
  > out/verify-alone.log 2>&1
check "the promoted statement verifies with no store mounted" "$?" "0"
py <<'PY' > out/verify-alone2.log 2>&1
import json
got = json.loads(open("out/verify-alone.log").read())
assert got["accepted"] and got["adapters_imported"] == [], got
assert got["predicate_type"].endswith("agent-action:0.1"), got
assert got["checks"] >= 4, got
print("verified from the envelope alone,", got["checks"], "checks, no adapter imported")
PY
check "the verifier imported no adapter of ours" "$?" "0"
python3 out/v/verify_alone.py out/human.bundle.json ../../harness/provenance/interface.py --falsify \
  > out/verify-falsified.log 2>&1
check "one byte of the artifact moved makes that same verification fail" "$?" "3"
grep -q '"subject_mismatches": 1' out/verify-falsified.log \
  && ok "the falsified arm fails on the subject digest, not on something else" \
  || bad "the falsified arm failed for the wrong reason"
py <<'PYB' > out/bundle-rules.log 2>&1
import json, os, subprocess
# The policy in the bundle is the second place subject-digest-must-match
# decides, and the one that decides for someone who is not us: it is what a
# third party holding only the envelope refuses on. It is built by the same
# run.py:trust_policy() the gate decides with, so the same declaration reaches
# both. Same door twice, one declared rule dropped: with it, the party has the
# subject expectation and one byte moved makes them refuse; without it, the
# bundle carries no subject expectation and the same moved byte is accepted -
# the rule is not an expectation only the published policy still carries.
base = json.load(open("units/close-checkout-coupon-fix.json"))
seen = {}
for arm, rules in (("with", base["promotion"]["gate_rules"]),
                   ("without", [r for r in base["promotion"]["gate_rules"]
                                if r != "subject-digest-must-match"])):
    label = f"bundle-{arm}"
    doc = json.loads(json.dumps(base)); doc["promotion"]["gate_rules"] = rules
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    entry = json.load(open("entries/human.json"))
    entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"bundle-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov",
                        "--bundle-out", f"out/v/{label}.bundle.json"], capture_output=True,
                       text=True, env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    assert r.returncode == 0, r.stdout + r.stderr
    policy = json.load(open(f"out/v/{label}.bundle.json"))["policy"]
    moved = subprocess.run(["python3", "out/v/verify_alone.py", f"out/v/{label}.bundle.json",
                            "../../harness/provenance/interface.py", "--falsify"],
                           capture_output=True, text=True)
    seen[arm] = (sorted(policy["expected_subjects"]), moved.returncode,
                 json.loads(moved.stdout)["subject_mismatches"])
assert seen["with"] == (["patch-checkout-coupon"], 3, 1), seen["with"]
assert seen["without"] == ([], 0, 0), seen["without"]
print("the declared rule reaches the policy the third party decides with:", seen)
PYB
check "the same declared rule reaches the gate and the published policy (differential)" "$?" "0"
grep -q "'without': (\[\], 0, 0)" out/bundle-rules.log \
  && ok "with the rule undeclared the third party has no subject expectation to refuse on" \
  || bad "the bundle kept an expectation the closure does not declare"

echo "8. the append-only log: pinned, proved, and checkable by a verifier that imports nothing of ours"
py <<'PY' > out/state.log 2>&1
import json, subprocess, sys
sys.path.insert(0, ".")
import harnesses
VERIFIER = harnesses.state_external_verifier()      # the loader names the path, not this file
for d in ("human", "external"):
    records = json.load(open(f"out/{d}.state.json"))
    rows = [json.loads(l) for l in open(f"out/{d}.jsonl")]
    assert len(records) == rows[-1]["state_head_size"] == len(rows), (len(records), len(rows))
    out = subprocess.run(["python3", VERIFIER],
                         input=json.dumps(records), capture_output=True, text=True)
    got = json.loads(out.stdout)
    assert got["chain_break_at"] == -1, got
    assert got["root_hash"] == rows[-1]["state_root_hash"], (d, got["root_hash"], rows[-1]["state_root_hash"])
    assert got["count"] == len(records)
print("the independent verifier recomputes the head the store returned, for two doors")
PY
check "an independent verifier recomputes the same root from the records alone" "$?" "0"
py <<'PY' > out/state-tamper.log 2>&1
import json, subprocess, sys
sys.path.insert(0, ".")
import harnesses
VERIFIER = harnesses.state_external_verifier()
records = json.load(open("out/human.state.json"))
def verify(rs):
    out = subprocess.run(["python3", VERIFIER],
                         input=json.dumps(rs), capture_output=True, text=True)
    return json.loads(out.stdout)
head = json.loads(open("out/human.jsonl").read().strip().splitlines()[-1])["state_root_hash"]
edited = json.loads(json.dumps(records))
edited[4]["body"]["subject_digest"] = "sha256:" + "0" * 64      # one record, mid-history
assert verify(edited)["chain_break_at"] == 4, verify(edited)
truncated = records[:-2]                                        # the two most recent removed
assert verify(truncated)["root_hash"] != head, "a truncated history recomputed the same root"
assert verify(truncated)["chain_break_at"] == -1, "truncation is caught by the root, not by the chain"
assert verify(records)["root_hash"] == head
print("mid-history edit caught at index 4; truncation caught by the root, not by the record chain")
PY
check "an edit mid-history and a truncated tail are both detected" "$?" "0"
py <<'PY' > out/state-race.log 2>&1
import json, os, sys
sys.path.insert(0, ".")
os.environ["OBJSTORE_DIR"] = "out/os-human"
import harnesses
iface, Adapter = harnesses.state("second")
partition = "done-checkout-coupon-corr-done-human-0001"
a, b = Adapter(), Adapter()
head = a.resolve_head(partition)
before = head.size
rec, moved = a.append(iface.AppendRequest.from_dict({
    "partition": partition, "kind": "late-note", "body": {"writer": "A"},
    "fencing_token": head.size + 1, "expected_head": head.chain_digest}))
try:
    b.append(iface.AppendRequest.from_dict({
        "partition": partition, "kind": "late-note", "body": {"writer": "B"},
        "fencing_token": head.size + 1, "expected_head": head.chain_digest}))
    raise AssertionError("two writers both landed on one head: the store forked")
except iface.Problem as problem:
    assert problem.body["type"].endswith("head-moved") and problem.body["status"] == 409, problem.body
final = a.resolve_head(partition)
assert final.size == before + 1, (before, final.size)
print(f"writer A landed at {final.size}, writer B refused 409 head-moved, no fork")
PY
check "two writers racing for one head: the first lands, the second is refused 409" "$?" "0"

echo "9. retention is declared per stream (differential)"
py <<'PY' > out/retention.log 2>&1
import json, os, subprocess
base = json.load(open("units/close-checkout-coupon-fix.json"))
words = json.load(open("entries/human.json"))["intent"]["summary"]
seen = {}
for label, redactable in (("redactable", True), ("not-redactable", False)):
    doc = json.loads(json.dumps(base)); doc["retention"]["redactable"] = redactable
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    entry = json.load(open("entries/human.json"))
    entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"retention-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov",
                        "--records-out", f"out/v/{label}.state.json"],
                       capture_output=True, text=True, env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    assert r.returncode == 0, r.stdout + r.stderr
    rows = [json.loads(l) for l in open(f"out/v/{label}.jsonl")]
    kinds = [x["kind"] for x in rows]
    records = json.load(open(f"out/v/{label}.state.json"))
    notified = [x for x in records if x["kind"] == "notified"]
    seen[label] = ("redaction-recorded" in kinds, "redaction-refused" in kinds,
                   words in json.dumps(records), [x for x in records if "body" not in x] != [])
assert seen["redactable"] == (True, False, False, True), seen
assert seen["not-redactable"] == (False, True, True, False), seen
print("redactable true: a tombstone, the words gone; false: a recorded refusal, the words retained")
PY
check "redactable true tombstones the record; false records a refusal and keeps it" "$?" "0"
py <<'PY' > out/retention2.log 2>&1
import json, subprocess, sys
sys.path.insert(0, ".")
import harnesses
records = json.load(open("out/human.state.json"))
tomb = [r for r in records if "body" not in r]
assert len(tomb) == 1 and tomb[0]["kind"] == "notified", tomb
out = subprocess.run(["python3", harnesses.state_external_verifier()],
                     input=json.dumps(records), capture_output=True, text=True)
assert json.loads(out.stdout)["chain_break_at"] == -1, out.stdout
pre = json.dumps(json.load(open("out/human.state-pre.json")))
words = json.load(open("entries/human.json"))["intent"]["summary"]
assert words in pre and words not in json.dumps(records)
import glob, os
# scope: every file the human door's own run wrote - its object store, its
# receipt, its record dump, its log - which is exactly the scope of the sentence
# this backs. The variant runs below keep the words on purpose: that is the
# not-redactable arm of the differential in this same section.
mine = [p for p in glob.glob("out/os-human/**/*", recursive=True) + glob.glob("out/human.*")
        if os.path.isfile(p)]
elsewhere = [p for p in mine if "state-pre" not in p and words in open(p, errors="replace").read()]
assert not elsewhere, elsewhere
assert [p for p in mine if "state-pre" in p], "the pre-redaction dump was not written"
assert len(mine) > 20, f"only {len(mine)} files scanned; the object store was not walked"
print(f"{len(mine)} files of the human door's own run scanned: the words are in the "
      f"pre-redaction dump the check asked for and in none of the others")
PY
check "after redaction the words are in no retained record, and the proof still verifies" "$?" "0"

echo "10. identity: one chain, hop by hop, and two declared values that change it"
py <<'PY' > out/identity.log 2>&1
import json
rec = [json.loads(l) for l in open("out/external.jsonl") if '"identity-resolved"' in l][0]
trace = rec["hop_trace"]                     # one chain, four hops of it, in order
assert [h["hop"] for h in trace] == [0, 1, 2, 3], trace
for older, newer in zip(trace, trace[1:]):
    assert set(newer["scope"]) <= set(older["scope"]), (older, newer)
    assert newer["remaining_s"] < older["remaining_s"], (older, newer)
    assert newer["chain_length"] == older["chain_length"] + 1, (older, newer)
assert [len(h["scope"]) for h in trace] == [3, 2, 1, 1], trace
assert trace[-1]["scope"] == ["write:ledger"] == json.load(
    open("units/close-checkout-coupon-fix.json"))["promotion"]["requires_scope"]
assert trace[0]["obtained_via"] == "direct" and {h["obtained_via"] for h in trace[1:]} == {"token_exchange"}
assert [h["declared_obtained_via"] for h in trace] == [
    h["obtained_via"] for h in json.load(open("entries/external.json"))["actor"]["delegation_chain"][::-1]
] + [None], trace
print("one chain: scope", " -> ".join(str(len(h["scope"])) for h in trace), "and lifetime",
      " -> ".join(str(h["remaining_s"]) for h in trace))
PY
check "along one chain, every hop narrows scope and shortens the lifetime" "$?" "0"
py <<'PY' > out/identity-root.log 2>&1
import json, os, subprocess
seen = {}
for label, via in (("direct-root", "direct"), ("exchanged-root", "token_exchange")):
    entry = json.load(open("entries/human.json"))
    entry["actor"]["delegation_chain"][-1]["obtained_via"] = via
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"root-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    seen[label] = (r.returncode, os.path.exists(f"out/v/{label}.jsonl"),
                   json.JSONDecoder().raw_decode(r.stdout.split("json):\n", 1)[1])[0]
                   ["type"].rsplit(":", 1)[-1] if r.returncode else "")
assert seen["direct-root"] == (0, True, ""), seen
assert seen["exchanged-root"] == (2, False, "identity-untrusted"), seen
print("a root obtained by exchange is refused 401 identity-untrusted before anything is recorded")
PY
check "obtained_via is read where the root is admitted (differential)" "$?" "0"
py <<'PY' > out/identity-scope.log 2>&1
import json, os, subprocess
base = json.load(open("units/close-checkout-coupon-fix.json"))
seen = {}
for label, required in (("scope-ledger", ["write:ledger"]),
                        ("scope-deploy", ["write:ledger", "deploy:prod"])):
    doc = json.loads(json.dumps(base)); doc["promotion"]["requires_scope"] = required
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    entry = json.load(open("entries/human.json"))
    entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"scope-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    body = json.JSONDecoder().raw_decode(r.stdout.split("json):\n", 1)[1])[0] if r.returncode else {}
    seen[label] = (r.returncode, body.get("rule_id", ""), body.get("enforcement_point", ""))
assert seen["scope-ledger"] == (0, "", ""), seen
assert seen["scope-deploy"] == (2, "scope-must-narrow", "platform-pre-issue"), seen
print("a promotion declaring a scope the chain does not hold is refused before any credential is issued")
PY
check "requires_scope is read where the hop is issued (differential)" "$?" "0"
py <<'PY9' > out/identity-hop-via.log 2>&1
import json, os, subprocess
# a hop that is not the root: the value the envelope declares reaches the
# credential that hop presents and is carried on the record, and the value the
# issued hop carries is the binding's (README gap G14).
seen = {}
for label, via in (("hop-exchanged", "token_exchange"), ("hop-attested", "workload_attestation")):
    entry = json.load(open("entries/external.json"))
    entry["actor"]["delegation_chain"][1]["obtained_via"] = via
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 1}
    entry["idempotency_key"] = f"hopvia-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    assert r.returncode == 0, r.stdout + r.stderr
    trace = [x for x in (json.loads(l) for l in open(f"out/v/{label}.jsonl"))
             if x["kind"] == "identity-resolved"][0]["hop_trace"]
    hop = [h for h in trace if h["actor"] == "service:partner-gateway"][0]
    seen[label] = (hop["declared_obtained_via"], hop["obtained_via"])
assert seen["hop-exchanged"] == ("token_exchange", "token_exchange"), seen
assert seen["hop-attested"] == ("workload_attestation", "token_exchange"), seen
print("the declared value moves with the declaration; the issued value is the binding's either way:",
      seen)
PY9
check "a non-root hop's declared obtained_via is read and recorded (differential)" "$?" "0"
py <<'PYA' > out/identity-deep.log 2>&1
import json, os, subprocess
# The entry schema puts no upper bound on the declared chain and nothing in the
# runner does either: how deep a chain is acted on is declared by the closure
# (delegation.max_declared_hops) and read before any credential is issued. Both
# arms run the same five-hop document, longer than any shipped one.
entry = json.load(open("entries/external.json"))
entry["actor"]["delegation_chain"] = [
    {"actor": "agent:partner-sre-bot", "obtained_via": "token_exchange"},
    {"actor": "service:partner-gateway", "obtained_via": "token_exchange"},
    {"actor": "service:partner-broker", "obtained_via": "token_exchange"},
    {"actor": "service:partner-edge", "obtained_via": "token_exchange"},
    {"actor": "user:corey", "obtained_via": "direct"}]
entry["correlation"] = {"run_id": "run-deep-chain", "correlation_id": "corr-deep-chain", "depth": 1}
entry["idempotency_key"] = "deep-chain-2026-09-03"
shipped = max(len(json.load(open(f"entries/{d}.json"))["actor"]["delegation_chain"])
              for d in ("human", "event", "schedule", "external"))
declared = len(entry["actor"]["delegation_chain"])
assert declared > shipped, shipped
base = json.load(open("units/close-checkout-coupon-fix.json"))
assert base["delegation"]["max_declared_hops"] < declared, base["delegation"]
import importlib.util
spec = importlib.util.spec_from_file_location("ref", "../end-to-end/run.py")
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
seen = {}
for label, limit in (("deep-refused", base["delegation"]["max_declared_hops"]), ("deep-admitted", 6)):
    doc = json.loads(json.dumps(base)); doc["delegation"]["max_declared_hops"] = limit
    json.dump(doc, open(f"out/v/closure-{label}.json", "w"))
    doc_entry = json.loads(json.dumps(entry))
    doc_entry["intent"]["workflow_ref"] = f"out/v/closure-{label}.json"
    doc_entry["correlation"]["run_id"] = f"run-{label}"
    doc_entry["correlation"]["correlation_id"] = f"corr-{label}"
    doc_entry["idempotency_key"] = f"{label}-2026-09-03"
    json.dump(doc_entry, open(f"out/v/entry-{label}.json", "w"))
    # the document a reader would write is schema-valid at both limits: what
    # separates the arms is the declaration, not the entry.
    assert not ref.validate(doc_entry, json.load(open("../end-to-end/schemas/entry.schema.json")))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    assert "Traceback" not in r.stderr, r.stderr[-400:]
    seen[label] = r
refused = seen["deep-refused"]
assert refused.returncode == 2, refused.stdout + refused.stderr
body = json.JSONDecoder().raw_decode(refused.stdout.split("json):\n", 1)[1])[0]
assert body["status"] == 403 and body["type"].endswith("policy-denied"), body
assert body["rule_id"] == "delegation-depth-exceeded", body
assert not os.path.exists("out/v/deep-refused.jsonl"), "a record was written before the refusal"
admitted = seen["deep-admitted"]
assert admitted.returncode == 0, admitted.stdout + admitted.stderr
trace = [x for x in (json.loads(l) for l in open("out/v/deep-admitted.jsonl"))
         if x["kind"] == "identity-resolved"][0]["hop_trace"]
assert len(trace) == declared + 1, trace
for older, newer in zip(trace, trace[1:]):
    assert set(newer["scope"]) <= set(older["scope"]), (older, newer)
    assert newer["remaining_s"] < older["remaining_s"], (older, newer)
assert trace[-1]["scope"] == base["promotion"]["requires_scope"], trace[-1]
print(f"a {declared}-hop declaration, longer than any shipped one ({shipped}): refused 403 "
      f"{body['rule_id']} at a declared ceiling of {base['delegation']['max_declared_hops']} with "
      f"no record written, and at a ceiling of 6 it issues {len(trace)} hops onto the required scope")
PYA
check "a chain deeper than the closure declares is refused before a credential is issued" "$?" "0"
grep -q "issues 6 hops onto the required scope" out/identity-deep.log \
  && ok "the ladder is as long as the declared chain, not as long as a list here" \
  || bad "the raised ceiling did not issue the whole declared chain"

echo "11. the promotion the door asked for (differential)"
py <<'PY' > out/promotion.log 2>&1
import json, os, subprocess
seen = {}
for label, kind in (("as-branch", "branch"), ("as-pull-request", "pull_request")):
    entry = json.load(open("entries/human.json"))
    entry["payload"]["promotion"]["kind"] = kind
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"promotion-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    assert r.returncode == 0, r.stdout + r.stderr
    rows = [json.loads(l) for l in open(f"out/v/{label}.jsonl")]
    promoted = [x for x in rows if x["kind"] == "promoted"][0]
    seen[label] = (promoted["promotion_kind"], promoted["subject_count"],
                   len([x for x in rows if x["kind"] == "attested"]),
                   promoted["subjects"][0])
assert seen["as-branch"][:3] == ("branch", 1, 4), seen
assert seen["as-pull-request"][:3] == ("pull_request", 2, 5), seen
assert seen["as-branch"][3] == seen["as-pull-request"][3], "the promoted subject changed with the target"
print("branch: 1 subject, 4 records; pull request: 2 subjects, 5 records; same promoted subject")
PY
check "promotion.kind is read where the subject set is decided (differential)" "$?" "0"

echo "12. notification by the door (differential)"
py <<'PY' > out/notify.log 2>&1
import json, os, subprocess
seen = {}
for label, surface in (("as-shell", "shell-line"), ("as-status", "task-status"), ("as-unknown", "pager")):
    entry = json.load(open("entries/human.json"))
    entry["payload"]["notify"]["surface"] = surface
    entry["correlation"] = {"run_id": f"run-{label}", "correlation_id": f"corr-{label}", "depth": 0}
    entry["idempotency_key"] = f"notify-{label}-2026-09-03"
    json.dump(entry, open(f"out/v/entry-{label}.json", "w"))
    r = subprocess.run(["python3", "run.py", "--entry", f"out/v/entry-{label}.json",
                        "--ledger", f"out/v/{label}.jsonl", "--prov-root", f"out/v/{label}/prov"],
                       capture_output=True, text=True,
                       env=dict(os.environ, OBJSTORE_DIR=f"out/v/{label}/os"))
    if r.returncode:
        seen[label] = (r.returncode,
                       json.JSONDecoder().raw_decode(r.stdout.split("json):\n", 1)[1])[0]["status"])
        continue
    rec = [json.loads(l) for l in open(f"out/v/{label}.jsonl") if '"notified"' in l][0]
    seen[label] = (rec["surface"], rec["rendered_as"], rec["receipt"]["cost_micros"])
assert seen["as-shell"][0] == "shell-line" and seen["as-status"][0] == "task-status"
assert seen["as-shell"][1] != seen["as-status"][1], seen
assert seen["as-shell"][2] == seen["as-status"][2] == 721000, seen
assert seen["as-unknown"] == (2, 422), seen
print("two surfaces render differently on one receipt; a surface this platform does not serve is 422")
PY
check "notify.surface is read where the notification is rendered (differential)" "$?" "0"

echo "13. the receipt"
python3 run.py --verify-ledger out/human.jsonl > out/verify.log 2>&1
check "the chain verifies" "$?" "0"
sed '3s/"cost_micros": [0-9]*/"cost_micros": 1/' out/human.jsonl > out/tampered.jsonl
python3 run.py --verify-ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a one-character edit in the receipt is detected" "$?" "2"
OBJSTORE_DIR=out/os-human python3 run.py --entry entries/human.json --ledger out/human.jsonl \
  --prov-root out/v/replay > out/replay.log 2>&1
check "the same key again exits 0" "$?" "0"
py <<'PY' > out/replay2.log 2>&1
import json, os
rows = [json.loads(l) for l in open("out/human.jsonl")]
assert "REPLAY:" in open("out/replay.log").read(), open("out/replay.log").read()[:200]
assert len(rows) == rows[-1]["state_head_size"], (len(rows), rows[-1])
assert not os.path.exists("out/v/replay/artifacts"), "a replay produced artifacts"
print(f"replay appended nothing: {len(rows)} records before and after, no artifact written")
PY
check "a replay appends no record and produces no artifact" "$?" "0"
py <<'PY' > out/cost.log 2>&1
import glob, json
declared = json.load(open("units/close-checkout-coupon-fix.json"))["closes"]
want = sum(u["cost_micros"] for u in declared)
rows = [json.loads(l) for l in open("out/human.jsonl")]
closing = [r for r in rows if r["kind"] == "run-completed"][-1]
assert closing["total_cost_micros"] == want, (closing["total_cost_micros"], want)
assert sum(r["cost_micros"] for r in rows) == want, "the line total is not the sum of the lines"
assert [r for r in rows if r["kind"] == "notified"][0]["receipt"]["cost_micros"] == want
assert want <= json.load(open("entries/human.json"))["budget"]["ceiling_micros"]
print(f"cost {want} micros: the closing line, the notification receipt and the sum of the "
      f"{len(rows)} records agree")
PY
check "the cost on the closing line is the sum of the records, not a number set beside them" "$?" "0"
py <<'PY' > out/kinds.log 2>&1
import glob, json, re
# every receipt this run wrote, found by shape rather than by name: a receipt
# line carries both a record kind and the state record it was projected from.
candidates = sorted(glob.glob("out/*.jsonl") + glob.glob("out/v/*.jsonl"))
def is_receipt(path):
    first = open(path).readline()
    return bool(first.strip()) and "state_record_id" in json.loads(first)
ledgers = [p for p in candidates if "tampered" not in p and is_receipt(p)]
assert len(ledgers) >= 10, f"only {len(ledgers)} receipts of {len(candidates)} files scanned"
written = {json.loads(l)["kind"] for p in ledgers for l in open(p)}
line = [l for l in open("README.md") if l.startswith("| The receipt")][0]
named = {t for t in re.findall(r"`([a-z][a-z-]+)`", line) if "/" not in t and "." not in t}
assert written == named, {"written not named": sorted(written - named),
                          "named not written": sorted(named - written)}
print(f"{len(written)} record kinds, read out of {len(ledgers)} receipts and named in README section 4, "
      f"both directions")
PY
check "every record kind the README names is written, and every kind written is named" "$?" "0"

echo "14. the same call, other bindings"
OBJSTORE_DIR=out/v/prov2/os python3 run.py --entry entries/human.json --ledger out/v/prov2.jsonl \
  --prov-adapter second --prov-root out/v/prov2/prov --bundle-out out/v/prov2.bundle.json \
  > out/v/prov2.log 2>&1
check "the whole closure runs on the other attestation store" "$?" "0"
py <<'PY' > out/swap-prov.log 2>&1
import json
first = [json.loads(l) for l in open("out/human.jsonl")]
second = [json.loads(l) for l in open("out/v/prov2.jsonl")]
def pub(rows):
    return [r for r in rows if r["kind"] == "published"][0]
assert pub(first)["inclusion_proof"] is False and pub(first)["inclusion_proof_supported"] is False
assert pub(second)["inclusion_proof"] is True and pub(second)["inclusion_proof_supported"] is True
assert pub(first)["store"] != pub(second)["store"], (pub(first)["store"], pub(second)["store"])
sealed = [r["subject_digest"] for r in first if r["kind"] == "subject-sealed"]
assert sealed == [r["subject_digest"] for r in second if r["kind"] == "subject-sealed"]
assert [r for r in second if r["kind"] == "promoted"], "the second binding promoted nothing"
print("one binding declares inclusion proofs unsupported and the other returns one; "
      "the sealed subjects are the same bytes either way")
PY
check "the second attestation store returns an inclusion proof where the first declares none" "$?" "0"
python3 out/v/verify_alone.py out/v/prov2.bundle.json ../../harness/provenance/interface.py \
  > out/v/prov2-verify.log 2>&1
check "the second store's statement verifies from the envelope too" "$?" "0"
py <<'PY' > out/swap-state.log 2>&1
import json, os, subprocess, sys
sys.path.insert(0, ".")
import harnesses
r = subprocess.run(["python3", "run.py", "--entry", "out/v/entry-as-branch.json",
                    "--ledger", "out/v/state-dryrun.jsonl", "--state-adapter", "dryrun",
                    "--prov-root", "out/v/state-dryrun/prov",
                    "--records-out", "out/v/state-dryrun.state.json"],
                   capture_output=True, text=True,
                   env=dict(os.environ, OBJSTORE_DIR="out/v/state-dryrun/os"))
assert r.returncode == 0, r.stdout + r.stderr
memory = json.load(open("out/v/state-dryrun.state.json"))
store = json.load(open("out/v/as-branch.state.json")) if os.path.exists(
    "out/v/as-branch.state.json") else None
rows = [json.loads(l) for l in open("out/v/state-dryrun.jsonl")]
assert len(memory) == rows[-1]["state_head_size"], (len(memory), rows[-1])
out = subprocess.run(["python3", harnesses.state_external_verifier()],
                     input=json.dumps(memory), capture_output=True, text=True)
got = json.loads(out.stdout)
assert got["root_hash"] == rows[-1]["state_root_hash"] and got["chain_break_at"] == -1, got
assert not os.path.exists("out/v/state-dryrun/os"), "the in-memory binding wrote objects to disk"
print("the in-memory binding produces a history the same verifier checks, and writes no object")
PY
check "the whole closure runs on the in-memory state binding, proved by the same verifier" "$?" "0"

py <<'PY5' > out/swap-identity.log 2>&1
import json, os, subprocess
r = subprocess.run(["python3", "run.py", "--entry", "out/v/entry-as-branch.json",
                    "--ledger", "out/v/identity-second.jsonl", "--identity-adapter", "second",
                    "--prov-root", "out/v/identity-second/prov"], capture_output=True, text=True,
                   env=dict(os.environ, OBJSTORE_DIR="out/v/identity-second/os"))
assert r.returncode == 0, r.stdout + r.stderr
first = [json.loads(l) for l in open("out/v/as-branch.jsonl")]
second = [json.loads(l) for l in open("out/v/identity-second.jsonl")]
def ident(rows):
    return [x for x in rows if x["kind"] == "identity-resolved"][0]
assert ident(first)["chain"] == ident(second)["chain"], (ident(first), ident(second))
assert ident(first)["scope"] == ident(second)["scope"]
assert ident(first)["authority_calls"] == 2 and ident(second)["authority_calls"] == 0, (
    ident(first)["authority_calls"], ident(second)["authority_calls"])
sealed = [x["subject_digest"] for x in first if x["kind"] == "subject-sealed"]
assert sealed == [x["subject_digest"] for x in second if x["kind"] == "subject-sealed"]
assert [x for x in second if x["kind"] == "promoted"], "the second identity binding promoted nothing"
print("the same chain and the same subjects on both identity bindings;",
      ident(first)["authority_calls"], "authority calls against", ident(second)["authority_calls"])
PY5
check "the whole closure runs on the attested-workload identity binding" "$?" "0"
py <<'PY6' > out/wired.log 2>&1
import importlib.util, os, sys
# the claim is that this example calls the same wired boundary two other
# production paths call, so the check reads those two files rather than ours.
callers = ["../../examples/end-to-end/run.py", "../../harness/linked/linked.py"]
for path in callers:
    body = open(path).read()
    assert "attest_and_record" in body, f"{path} does not call the wired boundary"
    assert "harness/provenance" in body or "provenance" in body, path
boundary = os.path.realpath("../../harness/provenance/emit.py")
spec = importlib.util.spec_from_file_location("wired_emit", boundary)
emit = importlib.util.module_from_spec(spec); sys.modules["wired_emit"] = emit
spec.loader.exec_module(emit)
sys.path.insert(0, ".")
import harnesses
mine = harnesses.emit()
assert os.path.realpath(mine.attest_and_record.__code__.co_filename) \
    == os.path.realpath(emit.attest_and_record.__code__.co_filename) == boundary, \
    "this example loaded a copy, not the boundary"
print(f"the boundary this example calls is the file {len(callers) + 1} production paths call, "
      f"not a copy of it")
PY6
check "the wired boundary is the one other production paths call, not a copy" "$?" "0"

echo "15. capabilities and standards, never products"
py <<'PY' > out/products.log 2>&1
import json, os, re
# The sentence this backs is about the whole example, so the scan is over every
# source file in this directory and every artifact the run has written by now,
# word-anchored. Only two README tables and lines marked `namecheck` are exempt.
NAMES = (r"\bsigstore\b|\brekor\b|\bfulcio\b|\bcosign\b|\bkyverno\b|\bspiffe\b|\bspire\b|"
         r"\btekton\b|\bgithub\b|\bgitlab\b|\bs3\b|\baws\b|\bamazon\b|\bazure\b|\bgcs\b|"
         r"\bnpm\b|\bpypi\b|\bmaven\b|\bopa\b|\brego\b|\bfirecracker\b|\bopenai\b|"
         r"\banthropic\b|\bdatadog\b|\bjaeger\b|\bhomebrew\b")   # namecheck: the forbidden list itself
MARK = "namecheck"                                                # namecheck
pattern = re.compile(NAMES, re.I)

def exempt_readme_lines():
    lines = open("README.md").read().splitlines()
    starts = {t: next(i for i, l in enumerate(lines) if l.startswith(t))
              for t in ("## 2. Standards", "## 3. The call", "### Adapters", "### Run steps")}
    return (set(range(starts["## 2. Standards"], starts["## 3. The call"]))
            | set(range(starts["### Adapters"], starts["### Run steps"])))

sources, artifacts = [], []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for name in sorted(files):
        path = os.path.join(root, name)
        (artifacts if path.startswith("./out/") else sources).append(path)
assert len(sources) >= 9, f"only {len(sources)} source files found"
assert len(artifacts) >= 100, f"only {len(artifacts)} artifacts found; the walk missed the object stores"
exempt, hits = exempt_readme_lines(), []
for path in sources + artifacts:
    if path.endswith(".pyc"):
        continue
    for i, line in enumerate(open(path, errors="replace").read().splitlines()):
        if MARK in line or (path == "./README.md" and i in exempt):
            continue
        if pattern.search(line):
            hits.append(f"{path}:{i + 1}")
assert not hits, hits[:8]
print(f"{len(sources)} source files and {len(artifacts)} artifacts scanned, no product named "
      f"outside the standards and adapters tables")
PY
check "no product is named outside the standards and adapters tables" "$?" "0"

echo "16. every quote is grepped back, and the cites list is exactly what the rows carry"
py <<'PY' > out/quotes.log 2>&1
import json, re, subprocess
ROOT = "../.."
files = ["README.md", "provenance.json"]
kb = re.compile(r"`((?:F|T|X|R)-[A-Za-z0-9-]+)`\s+\"([^\"]+)\"")
fl = re.compile(r"`FILE:([^`#]+)(?:#[^`]*)?`\s+\"([^\"]+)\"")
cache, checked, misquotes = {}, 0, []
for path in files:
    text = open(path).read()
    for rid, quote in kb.findall(text):
        if rid not in cache:
            out = subprocess.run(["python3", "tools/kb.py", "show", rid], cwd=ROOT,
                                 capture_output=True, text=True)
            assert out.returncode == 0, (rid, out.stderr[:200])
            cache[rid] = " || ".join(str(v) for v in json.loads(out.stdout).values())
        checked += 1
        if quote not in cache[rid]:
            misquotes.append((path, rid, quote[:60]))
    for rel, quote in fl.findall(text):
        checked += 1
        if quote not in open(f"{ROOT}/{rel.strip()}").read():
            misquotes.append((path, rel, quote[:60]))
assert not misquotes, misquotes
assert checked >= 20, f"only {checked} quotes checked; the rows are not carrying their evidence"
print(f"{checked} quotes in {len(files)} files, each grepped verbatim out of the record or file it names")
PY
check "every quote is pasted out of the record it cites, not remembered" "$?" "0"
py <<'PY' > out/cites.log 2>&1
import glob, json, os, re
walked = ["README.md", "provenance.json", "run.py", "harnesses.py", "test.sh"] \
    + sorted(glob.glob("entries/*.json")) + sorted(glob.glob("units/*.json"))
pattern = re.compile(r"\b((?:F|T|X)-[a-z][a-z0-9]*(?:-[a-z0-9]+)+|R[0-9]{2}[A-Z]+-[0-9]{3})\b")
carried = set()
for path in walked:
    carried |= set(pattern.findall(open(path).read()))
declared = set(json.load(open("provenance.json"))["cites"])
refs = {c for c in declared if c.startswith("REF-")}
for ref in refs:
    rel = ref[len("REF-"):].split("#")[0]
    assert os.path.exists(os.path.join("../..", rel)), f"{ref} names a file that is not there"
ids = declared - refs
assert ids == carried, {"declared not carried": sorted(ids - carried),
                        "carried not declared": sorted(carried - ids)}
assert len(walked) >= 10, walked
print(f"{len(ids)} record ids and {len(refs)} file references, walked over {len(walked)} files, "
      f"agreeing in both directions")
PY
check "provenance.cites is exactly the ids the example's rows carry" "$?" "0"

echo "17. the commands the README prints, run as printed"
rm -f out/demo-*.jsonl
py <<'PY' > out/commands.log 2>&1
import re, subprocess
lines = open("README.md").read().splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("### Run steps"))
rows = [l for l in lines[start:] if re.match(r"^\| [0-9]+ \|", l) and "python3 examples/done/" in l]
assert len(rows) >= 5, f"only {len(rows)} run-step rows found under the README's run-steps heading"
ran = 0
for line in rows:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    command = cells[2].strip("`")
    promised = cells[3].strip("`")
    out = subprocess.run(["bash", "-c", command], cwd="../..", capture_output=True, text=True)
    last = (out.stdout + out.stderr).strip().splitlines()[-1]
    assert last.startswith(promised), (command, promised, last)
    ran += 1
print(f"{ran} printed commands executed from the repository root; each last line is the one printed")
PY
check "every command in the run-steps table prints the last line printed beside it" "$?" "0"
py <<'PY' > out/argparse.log 2>&1
import re, subprocess
helptext = subprocess.run(["python3", "run.py", "--help"], capture_output=True, text=True).stdout
flags = set(re.findall(r"(--[a-z][a-z-]+)", open("README.md").read()))
missing = [f for f in flags if f not in helptext]
assert not missing, missing
assert len(flags) >= 4, flags
print(f"{len(flags)} flags named in the README, all of them in the runner's own --help")
PY
check "every flag the README names is one the runner declares" "$?" "0"
py <<'PYB' > out/argparse-values.log 2>&1
import re, subprocess
# a flag in --help that names one of its two values sends a reader of --help
# alone to a binding the README proves and the runner serves.
helptext = " ".join(subprocess.run(["python3", "run.py", "--help"],
                                   capture_output=True, text=True).stdout.split())
readme = open("README.md").read()
adapter_flags = sorted(set(re.findall(r"(--[a-z]+-adapter)", readme)))
assert len(adapter_flags) == 3, adapter_flags
values = set()
for flag in adapter_flags:
    assert flag in helptext, flag
    tail = helptext.rsplit(flag, 1)[1]        # the options section, not the usage line
    segment = re.split(r" --[a-z]", tail)[0]
    named = [v for v in ("dryrun", "second") if v in segment]
    assert named == ["dryrun", "second"], (flag, segment[:90])
    values |= set(named)
print(f"{len(adapter_flags)} adapter flags, each naming both of its {len(values)} bindings in --help")
PYB
check "every adapter value the README proves is named in --help too" "$?" "0"

py <<'PY4' > out/sections.log 2>&1
import re
# a reader sent to "section N" must land on a section that exists, and the
# sections are numbered in one place: the echoed headings of this file.
headings = {int(m) for m in re.findall(r'^echo "([0-9]+)\. ', open("test.sh").read(), re.M)}
text = " ".join(open("README.md").read().split())      # a reference may wrap a line
referenced = {int(n) for group in re.findall(r"`test\.sh` sections? ([0-9][0-9,and ]*)", text)
              for n in re.findall(r"[0-9]+", group)}
missing = sorted(referenced - headings)
assert not missing, f"the README sends a reader to sections that do not exist: {missing}"
assert len(referenced) >= 8, f"only {len(referenced)} section references found"
print(f"{len(referenced)} section references in the README, each landing in one of "
      f"{len(headings)} sections of this file")
PY4
check "every section the README sends a reader to exists here" "$?" "0"
py <<'PYC' > out/gaps.log 2>&1
import glob, re
# a reader sent to gap G<n> must land on a gap that exists. The table is keyed
# by id rather than by position precisely so a reference survives renumbering,
# so the reference is resolved against the keys and never against a row number.
readme = open("README.md").read()
keys = set(re.findall(r"^\| (G[0-9]+) \|", readme, re.M))
walked = ["README.md", "provenance.json", "run.py", "harnesses.py", "test.sh"] \
    + sorted(glob.glob("entries/*.json")) + sorted(glob.glob("units/*.json"))
referenced = {}
for path in walked:
    for ref in re.findall(r"(?<![A-Za-z0-9])(G[0-9]{1,2})\b", open(path).read()):
        referenced.setdefault(ref, []).append(path)
rows = re.findall(r"^\| (G[0-9]+) \|", readme, re.M)
assert len(rows) == len(keys) == len(set(rows)), rows
dangling = {r: sorted(set(p)) for r, p in referenced.items() if r not in keys}
assert not dangling, dangling
assert len(referenced) >= 10, sorted(referenced)
print(f"{len(referenced)} distinct gap references across {len(walked)} files, each resolving to one "
      f"of {len(keys)} keys in the gap table")
PYC
check "every gap reference resolves to a key in the gap table" "$?" "0"
py <<'PYD' > out/envelopes-stable.log 2>&1
import json
# section 1 asserted over the statements the four doors signed at the default
# period. The suite has run every command in the README since, and every
# differential arm besides, many of them closing the same doors at other
# periods: this re-reads the period's own copy of those envelopes, written
# beside its artifacts and its manifest, and the door store as the tree ends.
was = json.load(open("out/doors-envelopes.json"))
now = {d: [json.loads(l)["id"] for l in open(f"out/provenance/envelopes-{d}.jsonl")] for d in was}
assert now == was, {d: (was[d], now[d]) for d in was if now[d] != was[d]}
assert all(len(v) == 1 for v in now.values()), now
# and the door store itself: keyed by the door alone, it holds the last run of
# that door, whichever period it belonged to - which is why the period keeps a
# copy. Every statement in it is one this suite wrote.
ids = {d: [json.loads(l)["id"] for l in open(f"out/attestations-{d}.jsonl")] for d in was}
assert all(v for v in ids.values()), ids
print(f"the {len(now)} periods section 1 read hold the same statements at the end of the suite: "
      f"one --prov-root names one period")
PYD
check "the statements section 1 asserted over are the ones its period is left with" "$?" "0"

py <<'PY3' > out/floor.log 2>&1
import json, re
floor = int(re.search(r"^FLOOR=(\d+)$", open("test.sh").read(), re.M).group(1))
counted = json.load(open("provenance.json"))["visible_checks_counted"]
promised = [l for l in open("README.md")
            if "bash examples/done/test.sh" in l and "passed" in l]
assert len(promised) == 1, f"{len(promised)} README rows promise a count for the visible check"
printed = re.search(r"passed (\d+), failed 0", promised[0]).group(1)
assert floor == counted == int(printed), (floor, counted, printed)
print(f"the floor, provenance.visible_checks_counted and the line the README promises agree at {floor}")
PY3
check "the number of checks is one number in three files" "$?" "0"

echo
LAST="passed $PASS, failed $FAIL"
echo "$LAST"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
# and the last half of the gate: the line this run actually printed, against the
# line the README promises beside the command. Section 17 compares FLOOR,
# provenance.json and the README to each other; only this compares any of them
# to the program, so a count agreed in three files and printed by none is caught.
PROMISED=$(python3 - <<'PYE'
import re
row = [l for l in open("README.md") if "bash examples/done/test.sh" in l and "passed" in l]
print(re.search(r"passed \d+, failed 0", row[0]).group(0) if len(row) == 1 else "no single row")
PYE
)
[ "$LAST" = "$PROMISED" ] || { echo "the README promises '$PROMISED'; this run printed '$LAST'"; exit 1; }
