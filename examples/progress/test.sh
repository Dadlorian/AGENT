#!/usr/bin/env bash
# The visible check for examples/progress. Everything here is measured, not claimed.
#
# It prints `passed N, failed 0` with N counting checks that actually ran, and
# the gate at the bottom has two halves: no failure, and a floor under the count.
# A gutted copy of this file counts zero and is refused at the floor rather than
# exiting 0 (`F-a7-03` "A deterministic gate can be structurally green and mean
# nothing."). FLOOR moves with provenance.json's visible_checks_counted, and a
# check in section 13 asserts the two agree.
#
# Every extension point in README section 6 and every declared field in section 3
# is proved here by a differential run: the same door or unit twice, one declared
# value changed in a document written to out/, the two records asserted different
# in the named way. A green run at the default value proves the default path and
# nothing else. Each assertion block ends in exactly one `check`, so no check
# reads the exit status of the check before it.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=131
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }
run()  { name=$1; shift; python3 run.py "$@" --ledger "out/$name.jsonl" \
         --report "out/$name.rep.json" --out "out/$name.state" > "out/$name.log" 2>&1; rc=$?; \
         echo "$rc" > "out/$name.rc"; echo "$rc"; }

rm -rf out __pycache__ && mkdir -p out

# The variant documents every differential below runs against: one declared value
# changed, everything else identical, written to out/ and named on the command
# line. No flag stands in for a declared field.
py <<'PY' > out/variants.log 2>&1
import copy, json
P = json.load(open("pipelines/release-coupon-fix.json"))
E = {d: json.load(open(f"entries/{d}.json")) for d in ("human", "event", "schedule", "external")}
def stage(doc, sid): return next(s for s in doc["stages"] if s["id"] == sid)
def w(name, doc): json.dump(doc, open(f"out/{name}.json", "w"), indent=1)

d = copy.deepcopy(P); stage(d, "develop")["iterations_permitted"] = 1;              w("p-iter1", d)
d = copy.deepcopy(P); stage(d, "develop")["per_iteration_ceiling_micros"] = 50000;  w("p-periter", d)
d = copy.deepcopy(P); stage(d, "test")["shards"] = [
    {"id": "unit", "cases": ["c-tier-missing", "c-null-coupon"]},
    {"id": "rest", "cases": ["c-checkout-500", "c-schema-drift"]}];                 w("p-2shard", d)
d = copy.deepcopy(P); stage(d, "test")["shards"][1]["cases"] = ["c-not-in-the-set"]; w("p-badcase", d)
d = copy.deepcopy(P); stage(d, "test")["evaluation"]["case_set_ref"] = \
    "cases/release-coupon-regressed.json";                                          w("p-regressed", d)
d = copy.deepcopy(P); stage(d, "release")["decisions_offered"] = ["approve", "reject"]; w("p-noedit", d)
d = copy.deepcopy(P); stage(d, "production")["enter_when"] = {"stage": "release", "outcome": "approve"}
w("p-approveonly", d)
d = copy.deepcopy(P); c = stage(d, "production")["compensation"]
c["irreversibility"] = "irreversible"; c.pop("compensating_action");               w("p-irrev", d)
d = copy.deepcopy(d); stage(d, "production")["compensation"]["mandate_ref"] = "mandate://release/production/v1"
w("p-irrev-mandate", d)

d = copy.deepcopy(P); stage(d, "develop")["on_cap"] = "reject"
stage(d, "develop")["iterations_permitted"] = 1;                                   w("p-iter1-reject", d)
d = copy.deepcopy(P); stage(d, "develop")["exit_when"] = {"judge_step": "judge", "verdict": "green"}
w("p-greenverdict", d)
d = copy.deepcopy(P); stage(d, "release")["deadline_minutes"] = 60;                w("p-deadline60", d)
d = copy.deepcopy(P); d["stages"].insert(1, {
    "id": "canary", "op": "sequence", "enter_when": {"stage": "plan", "outcome": "priced"},
    "outcome_on_success": "priced", "steps": [{"id": "canary-step", "cost_micros": 5000}]})
stage(d, "develop")["enter_when"] = {"stage": "canary", "outcome": "priced"}
w("p-canary", d)
c = copy.deepcopy(d); stage(c, "canary")["outcome_on_success"] = "estimated"
w("p-canary-estimated", c)
d = copy.deepcopy(P); stage(d, "test")["op"] = "branch";                           w("p-badop", d)
d = copy.deepcopy(P); stage(d, "develop")["body"][0]["reaches_outside"] = False;   w("p-noreach", d)
d = copy.deepcopy(P); del d["carries"]; del d["summary"];                          w("p-nocarries", d)
d = copy.deepcopy(P); stage(d, "develop")["body"][1]["criterion_ref"] = \
    "criterion://does-not-exist/v1";                                               w("p-badcriterion", d)

e = copy.deepcopy(E["human"]); e["budget"]["ceiling_micros"] = 260000;              w("e-belowfloor", e)
e = copy.deepcopy(E["human"]); e["budget"]["ceiling_micros"] = 300000
e["payload"]["progress"]["passes_on_iteration"] = 3;                               w("e-midfan", e)
e = copy.deepcopy(E["human"]); e["payload"]["progress"]["passes_on_iteration"] = 1; w("e-pass1", e)
e = copy.deepcopy(E["human"]); e["payload"]["progress"]["decision"] = "reject";     w("e-reject", e)
e = copy.deepcopy(E["human"]); e["correlation"]["correlation_id"] = "corr-someone-else"
w("e-othercorr", e)
e = copy.deepcopy(E["human"]); del e["budget"];                                     w("e-malformed", e)
for name, mut in (("e-s-skip", {"catch_up": "skip"}), ("e-s-all", {"catch_up": "fire_all"}),
                  ("e-s-look2", {"lookback_days": 2}), ("e-s-utc", {"timezone": "UTC"}),
                  ("e-s-badrule", {"recurrence": "FREQ=SECONDLY;BYHOUR=2"})):
    e = copy.deepcopy(E["schedule"]); e["payload"]["progress"]["schedule"].update(mut); w(name, e)
e = copy.deepcopy(E["schedule"]); e["idempotency_key"] = "sched-not-the-nominal-key"; w("e-s-wrongkey", e)
print("variant documents written")
PY
check "the differential documents are written, one declared value changed each" "$?" "0"

echo "1. four doors, one unit, one declaration"
check "human exits 0"    "$(run human    --entry entries/human.json)" "0"
check "event exits 0"    "$(run event    --entry entries/event.json)" "0"
check "schedule exits 3" "$(run schedule --entry entries/schedule.json)" "3"
check "external exits 3" "$(run external --entry entries/external.json)" "3"
py <<'PY' > out/doors.log 2>&1
import json, sys
sys.path.insert(0, "../end-to-end")
from run import validate                       # one validator, two document shapes
entry_schema = json.load(open("../end-to-end/schemas/entry.schema.json"))
prog_schema = json.load(open("schemas/progress.schema.json"))
errs = 0
for d in ("human", "event", "schedule", "external"):
    doc = json.load(open(f"entries/{d}.json"))
    errs += len(validate(doc, entry_schema)) + len(validate(doc["payload"]["progress"], prog_schema))
assert errs == 0, f"{errs} validation errors across the four documents"
print("four entry documents and four progress declarations validate")
PY
check "four documents validate with the reference example's own validator" "$?" "0"
py <<'PY' > out/one-unit.log 2>&1
import json
doors = ("human", "event", "schedule", "external")
led = {d: [json.loads(l) for l in open(f"out/{d}.jsonl")] for d in doors}
refs = {json.load(open(f"entries/{d}.json"))["intent"]["workflow_ref"] for d in doors}
assert len(refs) == 1, refs
for field, want in (("run_id", 4), ("correlation_id", 4), ("actor", 4)):
    got = len({r[field] for rows in led.values() for r in rows})
    assert got == want, f"four doors carried {got} distinct {field}"
assert len({r["unit"] for rows in led.values() for r in rows}) == 1
print("one unit declaration, four actors, four run ids, four correlation ids")
PY
check "one unit through four doors, four actors, four run ids, four correlations" "$?" "0"
py <<'PY' > out/order.log 2>&1
import json
declared = [s["id"] for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]]
for d in ("human", "event", "schedule", "external"):
    rep = json.load(open(f"out/{d}.rep.json"))
    seen = [s["stage"] for s in rep["stages"]]
    assert seen == declared[:len(seen)], (d, seen)
    entered = [json.loads(l)["stage"] for l in open(f"out/{d}.jsonl")
               if json.loads(l)["kind"] in ("stage-entered", "stage-skipped")]
    assert entered == declared[:len(entered)], (d, entered)
full = [d for d in ("human", "event", "schedule", "external")
        if [json.loads(l)["stage"] for l in open(f"out/{d}.jsonl")
            if json.loads(l)["kind"] in ("stage-entered", "stage-skipped")] == declared]
assert len(full) == 3, full          # the schedule door ends inside release and never reaches production
print("every door walks a prefix of the declared stage order and", len(full),
      "walk all of it:", " -> ".join(declared))
PY
check "the stage sequence at every door is the declaration's order" "$?" "0"
py <<'PY' > out/stamps.log 2>&1
import json
rows = [json.loads(l) for d in ("human", "event", "schedule", "external")
        for l in open(f"out/{d}.jsonl")]
for r in rows:
    for field in ("run_id", "correlation_id", "actor", "delegation_depth", "entry_kind",
                  "idempotency_key", "unit", "task_state"):
        assert field in r, (r["kind"], field)
declared = json.load(open("pipelines/release-coupon-fix.json"))
for d in ("human", "event", "schedule", "external"):
    sub = [json.loads(l) for l in open(f"out/{d}.jsonl") if json.loads(l)["kind"] == "unit-submitted"][0]
    assert sub["sequence_id"] == declared["sequence_id"] and sub["tenant"] == declared["tenant"]
    assert sub["unit"] == declared["unit_ref"], sub["unit"]
depths = {json.load(open(f"out/{d}.rep.json"))["entry_kind"]:
          json.load(open(f"out/{d}.rep.json"))["delegation_depth"]
          for d in ("human", "event", "schedule", "external")}
assert depths == {"human": 1, "event": 2, "schedule": 2, "external": 3}, depths
print(len(rows), "records, every one stamped; delegation depths", depths)
PY
check "every record names the actor, the chain depth and the door it came in by" "$?" "0"
py <<'PY' > out/doorblind.log 2>&1
import json
doc = json.dumps(json.load(open("pipelines/release-coupon-fix.json")))
for word in ("human", "event", "schedule", "external", "entry_kind", "kind"):
    assert word not in doc, word
print("the unit declaration names no door and no entry kind; the door is carried, not read")
PY
check "the door the work came in by is carried on every record and read by no stage" "$?" "0"
py <<'PY' > out/dispositions.log 2>&1
import ast, glob, json, re
row = [l for l in open("../../docs/reference/ontology.md") if l.startswith("| Disposition |")][0]
declared = tuple(w.strip() for w in row.split("|")[2].split(":", 1)[1].split(","))
runner = open("run.py").read()
in_file = ast.literal_eval(re.search(r"^DISPOSITIONS = (\(.+?\))$", runner, re.M).group(1))
assert set(in_file) == set(declared), (in_file, declared)
# one place a disposition is set, the way move() is the one place a state is set
assert len(re.findall(r"self\.disposition = ", runner)) == 2, "a disposition is set outside dispose()"
assert re.search(r"def dispose\(self, word: str\)", runner)
seen = set()
for path in sorted(glob.glob("out/*.rep.json")):
    d = json.load(open(path))["disposition"]
    assert d in declared, (path, d)
    seen.add(d)
assert len(seen) >= 3, sorted(seen)
print(len(declared), "dispositions parsed out of the ontology row, set through one gate;",
      len(seen), "reached here:", sorted(seen))
PY
check "every disposition is one of the ontology's four, set through one checked gate" "$?" "0"

echo "2. cost before commitment"
py <<'PY' > out/plan-first.log 2>&1
import json
for d in ("human", "event", "schedule", "external"):
    kinds = [json.loads(l)["kind"] for l in open(f"out/{d}.jsonl")]
    assert kinds.index("plan-priced") < kinds.index("run-bound"), d
    assert "step-committed" not in kinds[:kinds.index("run-bound")], d
print("in every run the plan is priced before an executor is bound and before any step")
PY
check "the plan is priced before anything is bound and before any step runs" "$?" "0"
py <<'PY' > out/plan-sum.log 2>&1
import json
rep = json.load(open("out/human.rep.json"))
rows = rep["plan"]["rows"]
assert sum(r[3] for r in rows) == rep["plan"]["floor_micros"], rows
assert sum(r[4] for r in rows) == rep["plan"]["worst_micros"], rows
assert rep["plan"]["floor_micros"] == 290000 and rep["plan"]["worst_micros"] == 450000, rep["plan"]
print("floor", rep["plan"]["floor_micros"], "worst", rep["plan"]["worst_micros"],
      "= the sums of the priced rows")
PY
check "the plan's floor and worst case are the sums of its own rows" "$?" "0"
check "a unit declaring one permitted iteration prices a worst case equal to its floor" \
      "$(run p-iter1 --entry entries/human.json --pipeline out/p-iter1.json)" "3"
py <<'PY' > out/plan-diff.log 2>&1
import json
three = json.load(open("out/human.rep.json"))["plan"]
one = json.load(open("out/p-iter1.rep.json"))["plan"]
assert three["worst_micros"] == 450000 and three["floor_micros"] == 290000, three
assert one["worst_micros"] == one["floor_micros"] == 290000, one
print("iterations_permitted 3 prices worst", three["worst_micros"],
      "; 1 prices worst", one["worst_micros"], "= its floor")
PY
check "the loop bound is read by the planner: 3 prices 450000 worst, 1 prices 290000" "$?" "0"

echo "3. the stage gates"
check "the event door's edit enters production where the unit admits it" \
      "$(run gate-edit --entry entries/event.json)" "0"
check "the same door skips production where the unit admits approve alone" \
      "$(run gate-approveonly --entry entries/event.json --pipeline out/p-approveonly.json)" "3"
py <<'PY' > out/gate-diff.log 2>&1
import json
wide = json.load(open("out/gate-edit.rep.json"))
narrow = json.load(open("out/gate-approveonly.rep.json"))
def prod(rep): return next(s for s in rep["stages"] if s["stage"] == "production")
assert prod(wide)["entered"] and prod(wide)["outcome"] == "sealed", prod(wide)
assert not prod(narrow)["entered"], prod(narrow)
assert prod(narrow)["why"] == "release is 'edit', not 'approve'", prod(narrow)["why"]
assert wide["outcome"] == "completed" and narrow["outcome"] == "failed"
skipped = [json.loads(l) for l in open("out/gate-approveonly.jsonl")
           if json.loads(l)["kind"] == "stage-skipped"]
assert skipped and skipped[0]["required"] == {"stage": "release", "outcome": "approve"}
assert skipped[0]["actual"] == "edit", skipped[0]
print("enter_when read at the walk: outcome_in [approve, edit] enters, outcome approve skips")
PY
check "enter_when is read at the point of decision, not transcribed" "$?" "0"
check "a rejected release skips production" "$(run reject --entry out/e-reject.json)" "3"
py <<'PY' > out/reject.log 2>&1
import json
rep = json.load(open("out/reject.rep.json"))
assert rep["approval"]["decision"] == "reject" and rep["disposition"] == "reject"
prod = next(s for s in rep["stages"] if s["stage"] == "production")
assert not prod["entered"] and rep["effect_rows"] == 0, (prod, rep["effect_rows"])
assert rep["success_ladder"]["promotion"] is False
print("reject: production not entered, zero effect rows, disposition reject")
PY
check "a rejected release commits no effect and the disposition is reject" "$?" "0"

check "the same unit with its carries and summary members deleted" \
      "$(run nocarries --entry entries/human.json --pipeline out/p-nocarries.json)" "0"
py <<'PY' > out/carries.log 2>&1
import json
def kinds(n): return [(json.loads(l)["kind"], json.loads(l).get("step")) for l in open(f"out/{n}.jsonl")]
with_it, without = json.load(open("out/human.rep.json")), json.load(open("out/nocarries.rep.json"))
shipped = json.load(open("pipelines/release-coupon-fix.json"))
assert "carries" in shipped and "summary" in shipped
assert kinds("human") == kinds("nocarries"), "deleting them changed the record sequence"
for field in ("steps_committed", "steps_executed", "outward_calls", "effect_rows", "outcome"):
    assert with_it[field] == without[field], field
assert with_it["budget"]["spent_micros"] == without["budget"]["spent_micros"]
for member in ('"carries"', '"summary"'):
    assert member not in open("run.py").read(), f"{member} is read somewhere after all"
print("carries and summary are carried and not consumed: the same", len(kinds("human")),
      "records, the same spend and the same effect rows with both members deleted")
PY
check "the two members nothing reads are proved unread by deleting them" "$?" "0"

check "the same loop whose candidate step declares it reaches nothing outside" \
      "$(run noreach --entry entries/human.json --pipeline out/p-noreach.json)" "0"
py <<'PY' > out/reaches-outside.log 2>&1
import json
out, inside = (json.load(open(f"out/{n}.rep.json")) for n in ("human", "noreach"))
declared = {n: next(st for st in json.load(open(f))["stages"]
                    if st["id"] == "develop")["body"][0].get("reaches_outside")
            for n, f in (("human", "pipelines/release-coupon-fix.json"),
                         ("noreach", "out/p-noreach.json"))}
assert declared == {"human": True, "noreach": False}, declared
assert (out["outward_calls"], inside["outward_calls"]) == (3, 1), (out, inside)
for field in ("steps_committed", "outcome", "effect_rows"):
    assert out[field] == inside[field], field
assert out["budget"]["spent_micros"] == inside["budget"]["spent_micros"]
key = inside["run_key"]
rows = [json.loads(l)["operator"] for l in open(f"out/noreach.state/{key}/outward-calls.jsonl")]
assert rows == ["publish-release"], rows
print("reaches_outside is read per body step:", out["outward_calls"], "calls leave the unit",
      "where it is declared and", inside["outward_calls"], "where it is not, same 11 steps")
PY
check "the step that reaches outside is declared, and the outward table follows it" "$?" "0"
check "a stage row added to the declaration, with nothing in run.py touched" \
      "$(run canary --entry entries/human.json --pipeline out/p-canary.json)" "0"
py <<'PY' > out/e1-canary.log 2>&1
import json
declared = [s["id"] for s in json.load(open("out/p-canary.json"))["stages"]]
base = [s["id"] for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]]
assert declared == ["plan", "canary", "develop", "test", "release", "production"], declared
added = json.load(open("out/canary.rep.json"))
plain = json.load(open("out/human.rep.json"))
assert [s["stage"] for s in added["stages"]] == declared, added["stages"]
entered = [json.loads(l)["stage"] for l in open("out/canary.jsonl")
           if json.loads(l)["kind"] == "stage-entered"]
assert entered == declared, entered                      # walked in declared order, canary second
gate = next(st for st in json.load(open("out/p-canary.json"))["stages"]
            if st["id"] == "develop")["enter_when"]
assert gate == {"stage": "canary", "outcome": "priced"}, gate      # and it gates the next stage
committed = [json.loads(l)["step"] for l in open("out/canary.jsonl")
             if json.loads(l)["kind"] == "step-committed"]
assert "canary-step" in committed, committed
assert added["steps_committed"] == plain["steps_committed"] + 1 == 12, added["steps_committed"]
assert added["outcome"] == "completed" and added["disposition"] == "accept"
# priced through the pricing arm an unspecialised operator falls to, and charged
cost = next(st for st in json.load(open("out/p-canary.json"))["stages"]
            if st["id"] == "canary")["steps"][0]["cost_micros"]
assert cost == 5000
priced = [r for r in added["plan"]["rows"] if r[0] == "canary"]
assert priced == [["canary", "sequence", str(cost), cost, cost]], priced
for field in ("floor_micros", "worst_micros"):
    assert added["plan"][field] == plain["plan"][field] + cost, (field, added["plan"], plain["plan"])
assert added["budget"]["spent_micros"] == plain["budget"]["spent_micros"] + cost, added["budget"]
assert '"canary"' not in open("run.py").read(), "the walk was taught the new stage by hand"
assert set(base) - set(declared) == set(), (base, declared)
print("a sixth stage row is walked in declared order and commits its own step:",
      " -> ".join(entered))
PY
check "a stage added to the document is walked, and the walk names no stage" "$?" "0"
check "the same six-stage unit with the added stage reporting a different outcome" \
      "$(run canary-estimated --entry entries/human.json --pipeline out/p-canary-estimated.json)" "3"
py <<'PY' > out/outcome-on-success.log 2>&1
import json
priced = json.load(open("out/canary.rep.json"))
other = json.load(open("out/canary-estimated.rep.json"))
declared = {n: next(st for st in json.load(open(f"out/{f}.json"))["stages"]
                    if st["id"] == "canary")["outcome_on_success"]
            for n, f in (("priced", "p-canary"), ("other", "p-canary-estimated"))}
assert declared == {"priced": "priced", "other": "estimated"}, declared
def row(rep, stage): return next(s for s in rep["stages"] if s["stage"] == stage)
assert row(priced, "canary")["outcome"] == "priced"
assert row(other, "canary")["outcome"] == "estimated", row(other, "canary")
assert row(priced, "develop")["entered"] and not row(other, "develop")["entered"]
assert row(other, "develop")["why"] == "canary is 'estimated', not 'priced'", row(other, "develop")
assert other["outcome"] == "failed" and other["stop_reason"] == "stage-gate-not-met"
assert other["budget"]["spent_micros"] == 5000, other["budget"]      # it ran, and it stopped
assert priced["outcome"] == "completed"
print("outcome_on_success is what the stage reports and the gate after it compares:",
      declared["priced"], "runs the loop and", declared["other"], "leaves it unentered")
PY
check "the outcome a stage reports is the document's, and the next gate reads it" "$?" "0"
check "a stage declaring an operator nothing serves" \
      "$(run bad-op --entry entries/human.json --pipeline out/p-badop.json)" "2"
py <<'PY' > out/e1-badop.log 2>&1
import importlib.util, json
rep = json.load(open("out/bad-op.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:document-invalid", rep["problem"]
assert rep["problem"]["status"] == 422
assert rep["problem"]["causes"] == [{"stage": "test", "op": "branch"}], rep["problem"]["causes"]
assert rep["budget"]["spent_micros"] == 0 and rep["executor"]["marker"] is None
# the set the refusal names is the composition capability's own, read from the
# schema an engine is handed, and this file re-types neither half of it
spec = importlib.util.spec_from_file_location("prog_h", "harnesses.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
schema = json.load(open("../end-to-end/schemas/workflow.schema.json"))
capability = list(mod.operators().operator_names(schema))
assert str(capability) in rep["problem"]["detail"], (capability, rep["problem"]["detail"])
walked = [s["op"] for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]]
local = [o for o in walked if o not in capability]
assert local == ["effect"], local          # the one name this area adds, written up as gap G12
print("the operator set is the schema's", capability, "plus", local,
      "; 'branch' is refused 422 before an executor is bound")
PY
check "the operator vocabulary is the capability's, and an unknown one is refused 422" "$?" "0"

echo "4. the bounded loop"
check "a unit permitting one iteration where the candidate passes on two caps" \
      "$(run loop-iter1 --entry entries/human.json --pipeline out/p-iter1.json)" "3"
check "a unit whose per-iteration ceiling is below the body cost caps at once" \
      "$(run loop-periter --entry entries/human.json --pipeline out/p-periter.json)" "2"
check "a candidate that passes on iteration one runs one iteration" \
      "$(run loop-pass1 --entry out/e-pass1.json)" "0"
py <<'PY' > out/loop-diff.log 2>&1
import json
base = json.load(open("out/human.rep.json"))["loop"]
iter1 = json.load(open("out/loop-iter1.rep.json"))["loop"]
per = json.load(open("out/loop-periter.rep.json"))["loop"]
pass1 = json.load(open("out/loop-pass1.rep.json"))["loop"]
assert (base["terminated_by"], base["iterations_run"]) == ("verdict_pass", 2), base
assert (iter1["terminated_by"], iter1["termination_class"]) == ("iteration_ceiling", "cap"), iter1
assert iter1["iterations_permitted"] == 1 and iter1["iterations_run"] == 1, iter1
assert (per["terminated_by"], per["iterations_run"]) == ("budget_ceiling", 0), per
assert (pass1["terminated_by"], pass1["iterations_run"]) == ("verdict_pass", 1), pass1
print("iterations_permitted, per_iteration_ceiling_micros and passes_on_iteration each move "
      "the termination:", base["terminated_by"], iter1["terminated_by"], per["terminated_by"])
PY
check "three declared values, three different loop terminations" "$?" "0"
py <<'PY' > out/loop-reasons.log 2>&1
import json, os, sys
sys.path.insert(0, "..")
import importlib.util
spec = importlib.util.spec_from_file_location("prog_h", "harnesses.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
iface, _, _ = mod.durable("dryrun")
import typing
declared = set(typing.get_type_hints(iface.LoopOutcome, vars(iface))["terminated_by"].__args__)
written = {json.loads(l)["terminated_by"] for name in ("human", "loop-iter1", "loop-periter")
           for l in open(f"out/{name}.jsonl") if json.loads(l)["kind"] == "loop-terminated"}
assert written == declared, (sorted(written), sorted(declared))
print(len(declared), "termination reasons declared by the capability, and all", len(written),
      "are reached here:", sorted(written))
PY
check "the loop's termination reasons are the capability's closed set, all reached" "$?" "0"
py <<'PY' > out/loop-cap.log 2>&1
import json
rep = json.load(open("out/loop-iter1.rep.json"))
assert rep["disposition"] == "escalate", rep["disposition"]
assert rep["problem"]["type"] == "urn:agentic:problem:deadline-exceeded", rep["problem"]
assert "iteration-ceiling-reached" in rep["problem"]["detail"], rep["problem"]["detail"]
assert rep["problem"]["retryable"] is True
print("a cap escalates:", rep["problem"]["type"], "naming the proposed type in the detail")
PY
check "a cap escalates as a registered type naming the proposed one it stands in for" "$?" "0"
check "the same cap under a unit declaring on_cap reject" \
      "$(run loop-reject --entry entries/human.json --pipeline out/p-iter1-reject.json)" "3"
py <<'PY' > out/loop-oncap.log 2>&1
import json
esc = json.load(open("out/loop-iter1.rep.json"))
rej = json.load(open("out/loop-reject.rep.json"))
for name, rep, want in (("p-iter1", esc, "escalate"), ("p-iter1-reject", rej, "reject")):
    declared = next(st for st in json.load(open(f"out/{name}.json"))["stages"]
                    if st["id"] == "develop")["on_cap"]
    assert declared == want and rep["disposition"] == want, (name, declared, rep["disposition"])
assert esc["disposition"] != rej["disposition"], "on_cap moved nothing"
assert esc["loop"] == rej["loop"], "the two runs differ in more than the disposition"
assert esc["problem"]["type"] == rej["problem"]["type"], "the type is the errors capability's"
assert esc["problem"]["status"] == rej["problem"]["status"] == 504
print("on_cap is read at the cap: the same termination answers", esc["disposition"],
      "under one declaration and", rej["disposition"], "under the other")
PY
check "on_cap is read at the cap and moves the disposition, not a word of prose" "$?" "0"
check "a loop whose declared exit verdict the judge never returns" \
      "$(run loop-green --entry entries/human.json --pipeline out/p-greenverdict.json)" "3"
py <<'PY' > out/loop-exitwhen.log 2>&1
import json
green = json.load(open("out/loop-green.rep.json"))
base = json.load(open("out/human.rep.json"))
declared = next(st for st in json.load(open("out/p-greenverdict.json"))["stages"]
                if st["id"] == "develop")["exit_when"]
assert declared == {"judge_step": "judge", "verdict": "green"}, declared
assert green["loop"]["terminated_by"] == "iteration_ceiling", green["loop"]
assert green["loop"]["iterations_run"] == 3 and green["loop"]["last_verdict"] == "pass"
assert base["loop"]["terminated_by"] == "verdict_pass", base["loop"]
assert declared["verdict"] in green["problem"]["detail"], green["problem"]["detail"]
# the comparison is the document's; the vocabulary the judge answers in is not
verdicts = {json.loads(l)["verdict"] for l in open("out/loop-green.jsonl")
            if json.loads(l)["kind"] == "judge-verdict"}
assert declared["verdict"] not in verdicts and verdicts <= {"pass", "fail"}, verdicts
print("exit_when is compared against, not assumed: a declared verdict of",
      repr(declared["verdict"]), "never matches the judge's", sorted(verdicts),
      "and the loop runs to its cap (gap G13)")
PY
check "the verdict the loop exits on is the document's, and the judge's set is not" "$?" "0"
check "a unit naming a criterion handle that does not resolve" \
      "$(run bad-criterion --entry entries/human.json --pipeline out/p-badcriterion.json)" "3"
py <<'PY' > out/criterion-ref.log 2>&1
import json
rep = json.load(open("out/bad-criterion.rep.json"))
declared = next(s for s in json.load(open("out/p-badcriterion.json"))["stages"]
                if s["id"] == "develop")["body"][1]["criterion_ref"]
assert rep["problem"]["type"] == "urn:agentic:problem:criterion-unresolvable", rep["problem"]
assert rep["problem"]["status"] == 422
assert declared in rep["problem"]["detail"], rep["problem"]["detail"]
assert rep["budget"]["spent_micros"] > 0, "the loop reached the judge"
good = json.load(open("out/human.rep.json"))
assert good["problem"] is None and good["loop"]["terminated_by"] == "verdict_pass"
print("criterion_ref is resolved from the document, not from a literal: the shipped handle "
      "resolves and", declared, "is refused 422")
PY
check "the criterion handle is the document's: an unresolvable one is refused by name" "$?" "0"
py <<'PY' > out/criterion.log 2>&1
import json, os
# The scope of the sentence is every artifact a run of this suite has written by
# now, executor and register state directories included - not the top level of
# out/, where the journals a step output lands in cannot be seen.
MEMBERS = ("must_contain", "required_steps", "required_tools", "answer_contains")
SECRET = "regression verified"
def under(node, key=None):
    """the keys, other than a candidate's own text, whose value carries the phrase"""
    if isinstance(node, dict):
        return [k for key2, v in node.items() for k in under(v, key2)]
    if isinstance(node, list):
        return [k for v in node for k in under(v, key)]
    return [key] if isinstance(node, str) and SECRET in node and key != "text" else []
scanned, members, misplaced, carrying = 0, [], [], 0
for root, dirs, files in os.walk("out"):
    for name in sorted(files):
        path = os.path.join(root, name)
        text = open(path, errors="replace").read()
        scanned += 1
        members += [f"{path}: {m}" for m in MEMBERS if m in text]
        if SECRET not in text:
            continue
        carrying += 1
        for i, line in enumerate(text.splitlines(), 1):
            if SECRET not in line:
                continue
            try:
                keys = under(json.loads(line))
            except json.JSONDecodeError:
                misplaced.append(f"{path}:{i}: not a record at all")
                continue
            misplaced += [f"{path}:{i}: under {k!r}" for k in keys]
assert not members, "criterion or rubric member names in artifacts: " + "; ".join(members[:5])
assert not misplaced, "the criterion phrase outside candidate text: " + "; ".join(misplaced[:5])
assert scanned >= 40 and carrying > 0, (scanned, carrying)
print(scanned, "artifacts scanned including every state directory;", carrying,
      "carry the criterion phrase and every occurrence is a candidate's own text;",
      "no criterion or rubric member name appears in any of them")
PY
check "the criterion body reaches no report, no ledger field and no table" "$?" "0"

echo "5. the fan-out and the evaluation gate"
check "a unit declaring two shards over the same four cases runs" \
      "$(run fan2 --entry entries/human.json --pipeline out/p-2shard.json)" "0"
py <<'PY' > out/fan-diff.log 2>&1
import json
three = json.load(open("out/human.rep.json"))
two = json.load(open("out/fan2.rep.json"))
def shard_steps(name):
    return [json.loads(l)["step"] for l in open(f"out/{name}.jsonl")
            if json.loads(l)["kind"] == "step-committed" and json.loads(l)["step"].startswith("shard-")]
a, b = shard_steps("human"), shard_steps("fan2")
assert len(a) == 3 and len(b) == 2, (a, b)
assert three["evaluation"]["shards_declared"] == 3 and two["evaluation"]["shards_declared"] == 2
assert three["evaluation"]["cases_executed"] == two["evaluation"]["cases_executed"] == 4
assert three["evaluation"]["verdicts"] == two["evaluation"]["verdicts"]
assert three["budget"]["spent_micros"] - two["budget"]["spent_micros"] == 40000, \
    (three["budget"], two["budget"])
print("width read from the document:", len(a), "shard steps against", len(b),
      "; same 4 cases, same verdicts, one shard price apart")
PY
check "the fan-out width is declared: 3 shards run 3 steps, 2 run 2, same verdicts" "$?" "0"
py <<'PY' > out/fan-balance.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl") if json.loads(l)["kind"] == "step-committed"]
shards = [r for r in rows if r["step"].startswith("shard-")]
remaining = [r["budget_remaining_micros"] for r in shards]
assert remaining == sorted(remaining, reverse=True), remaining
assert all(a - b == 40000 for a, b in zip(remaining, remaining[1:])), remaining
declared = json.load(open("pipelines/release-coupon-fix.json"))
cost = next(s for s in declared["stages"] if s["id"] == "test")["shard_cost_micros"]
assert remaining[0] - remaining[-1] == cost * (len(shards) - 1), remaining
print(len(shards), "shards draw from one balance, monotonically:", remaining)
PY
check "the shards draw from the parent's one remaining balance, never a fresh one" "$?" "0"
check "the regressed case set is gated" \
      "$(run eval-regressed --entry entries/human.json --pipeline out/p-regressed.json)" "3"
py <<'PY' > out/eval-diff.log 2>&1
import json
clean = json.load(open("out/human.rep.json"))["evaluation"]
bad = json.load(open("out/eval-regressed.rep.json"))["evaluation"]
assert clean["gate"]["status"] == "passed" and clean["blocks_promotion"] is False
assert bad["gate"]["status"] == "failed" and bad["blocks_promotion"] is True
moved = {t["case_id"]: (t["was"], t["now"]) for t in bad["transitions"]}
assert moved == {"c-checkout-500": ("pass", "fail")}, moved
scores = bad["dimension_scores"]["c-checkout-500"]
assert scores["tool_use"] == "fail" and scores["task_completion"] == "pass", scores
# The two corpora hold the same scenarios and differ only in one recorded
# trajectory, so the case-set digest is equal by construction and the report id,
# which covers the verdicts, is not. That is the shape of the difference.
assert clean["case_set"]["digest"] == bad["case_set"]["digest"], "the scenarios differ too"
assert clean["case_set"]["case_set_id"] != bad["case_set"]["case_set_id"]
assert clean["report_id"] != bad["report_id"], (clean["report_id"], bad["report_id"])
ev = next(s for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]
          if s["id"] == "test")["evaluation"]
baseline = json.load(open(ev["baseline_ref"]))
gated = [json.loads(l) for l in open("out/human.jsonl")
         if json.loads(l)["kind"] == "evaluation-gated"][0]
assert gated["baseline_id"] == baseline["baseline_id"], gated
assert clean["unit_under_test"] == {"ref": ev["unit_ref"], "version": ev["unit_version"]}
print("case_set_ref read: passed vs failed, the named case", *moved,
      "moved pass->fail on tool_use while its answer still passes")
PY
check "the case set is read and the ordered trace is scored, not the final answer" "$?" "0"
py <<'PY' > out/eval-block.log 2>&1
import json
rep = json.load(open("out/eval-regressed.rep.json"))
entered = {s["stage"]: s["entered"] for s in rep["stages"]}
assert entered == {"plan": True, "develop": True, "test": True,
                   "release": False, "production": False}, entered
assert rep["stop_reason"] == "evaluation-gate-blocked-promotion" and rep["problem"] is None
assert rep["disposition"] == "retry" and rep["effect_rows"] == 0
assert rep["success_ladder"]["validation"] is False and rep["success_ladder"]["promotion"] is False
print("a blocked gate is not a refusal: no problem body, release and production never entered")
PY
check "a gate that blocks promotion stops the pipeline with no problem body" "$?" "0"
check "a fan-out naming a case its case set does not carry is refused" \
      "$(run fan-badcase --entry entries/human.json --pipeline out/p-badcase.json)" "3"
py <<'PY' > out/eval-badcase.log 2>&1
import json
rep = json.load(open("out/fan-badcase.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:document-invalid", rep["problem"]
assert rep["problem"]["status"] == 422
assert rep["problem"]["causes"] == [{"case_id": "c-not-in-the-set"}], rep["problem"]
print("the unknown case is refused 422 naming it, rather than scored as absent")
PY
check "a case the corpus does not carry is a typed refusal, never a silent zero" "$?" "0"
py <<'PY' > out/rubric.log 2>&1
import glob, json
for path in glob.glob("out/*.rep.json") + glob.glob("out/*.jsonl") + glob.glob("out/*.log"):
    text = open(path, errors="replace").read()
    for token in ("required_tools", "answer_contains", "required_steps"):
        assert token not in text, (path, token)
for path in glob.glob("out/*.rep.json"):
    ev = json.load(open(path)).get("evaluation")
    if ev:
        refs = {c: v for c, v in ev["verdicts"].items()}
        assert refs, path
print("no rubric body in any report, ledger or log; only handles, verdicts and dimension scores")
PY
check "the rubric body reaches no report, no ledger and no log" "$?" "0"

echo "6. the release gate"
check "a unit that does not offer edit refuses the same door's edit" \
      "$(run gate-noedit --entry entries/event.json --pipeline out/p-noedit.json)" "3"
py <<'PY' > out/gate-offered.log 2>&1
import json
ok = json.load(open("out/event.rep.json"))
no = json.load(open("out/gate-noedit.rep.json"))
assert ok["approval"]["decision"] == "edit" and ok["outcome"] == "completed"
assert no["problem"]["type"] == "urn:agentic:problem:document-invalid", no["problem"]
assert no["problem"]["causes"] == [{"decision": "edit",
                                    "offered": ["approve", "reject"]}], no["problem"]
print("decisions_offered read at the gate: edit accepted where offered, 422 where not")
PY
check "decisions_offered is read at the gate, not transcribed" "$?" "0"
py <<'PY' > out/gate-park.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl")]
parked = [r for r in rows if r["kind"] == "approval-parked"][0]
decided = [r for r in rows if r["kind"] == "approval-decided"][0]
declared = next(s for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]
                if s["id"] == "release")
assert parked["view"] == declared["view"] and parked["decisions_offered"] == declared["decisions_offered"]
assert parked["task_state"] == "input-required", parked["task_state"]
assert decided["resumed_the_run"] == 1
rep = json.load(open("out/human.rep.json"))
assert rep["task_states_seen"] == ["submitted", "working", "input-required", "working", "completed"]
assert rep["gates_parked"] == 1 and rep["gates_decided"] == 1
prog = json.load(open("entries/human.json"))["payload"]["progress"]
assert parked["decider"] == decided["decider"] == prog["decider"], (parked, prog)
assert parked["return_to_stage"] == declared["return_to_stage"], parked
print("the gate parks at input-required with the declared view, decider and return stage, "
      "and one decision resumes the run")
PY
check "the gate parks the unit at input-required and one decision resumes it" "$?" "0"
check "ten deliveries of one decision" "$(run gate-10 --entry entries/human.json --deliveries 10)" "0"
py <<'PY' > out/gate-deliv.log 2>&1
import json
one = json.load(open("out/human.rep.json"))["approval"]
ten = json.load(open("out/gate-10.rep.json"))["approval"]
assert (one["deliveries"], one["applied"]) == (1, 1), one
assert (ten["deliveries"], ten["applied"]) == (10, 1), ten
assert json.load(open("out/gate-10.rep.json"))["gates_decided"] == 1
print("1 delivery applies once and 10 deliveries apply once: the gate-scoped key deduplicates")
PY
check "ten deliveries of one decision resume the run exactly once" "$?" "0"
check "a second, different decision on a decided gate" \
      "$(run gate-contra --entry entries/human.json --contradict)" "0"
py <<'PY' > out/gate-contra.log 2>&1
import json
rep = json.load(open("out/gate-contra.rep.json"))
folded = [r for r in rep["refusals"] if r["ends_unit"] is False]
assert len(folded) == 1 and folded[0]["type"] == "urn:agentic:problem:idempotency-conflict"
assert folded[0]["status"] == 409
assert rep["outcome"] == "completed" and rep["approval"]["decision"] == "approve"
rows = [json.loads(l) for l in open("out/gate-contra.jsonl") if json.loads(l)["kind"] == "refusal"]
assert len(rows) == 1 and rows[0]["ends_unit"] is False
ending = json.load(open("out/schedule.rep.json"))["refusals"]
assert ending and ending[0]["ends_unit"] is True
print("a contradiction is 409 folded into the record and the unit completes; "
      "a refusal that ends the unit is a different row")
PY
check "a contradicting decision is refused 409 and folded in, and the unit continues" "$?" "0"
py <<'PY' > out/gate-expired.log 2>&1
import datetime as dt, json
rep = json.load(open("out/schedule.rep.json"))
declared = next(s for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]
                if s["id"] == "release")
occurred = json.load(open("entries/schedule.json"))["occurred_at"]
# the instant is computed from the envelope and the declared minutes here too,
# so a runner stamping either of them as a literal fails this check
want = (dt.datetime.strptime(occurred, "%Y-%m-%dT%H:%M:%SZ")
        + dt.timedelta(minutes=declared["deadline_minutes"])).strftime("%Y-%m-%dT%H:%M:%SZ")
assert rep["problem"]["type"] == "urn:agentic:problem:deadline-exceeded", rep["problem"]
assert rep["approval"]["deadline_at"] == want == "2026-11-06T07:00:00Z", (rep["approval"], want)
assert declared["deadline_minutes"] == 1440
assert rep["approval"]["deadline_at"] in rep["problem"]["detail"]
assert rep["effect_rows"] == 0 and rep["compensation"]["declared"] is None
print("nobody answers: 504 at", want, "=", occurred, "+", declared["deadline_minutes"],
      "declared minutes, and no effect was ever declared")
PY
check "nobody at the door: the gate closes at its declared deadline and nothing ships" "$?" "0"
check "the same door under a unit declaring an hour instead of a day" \
      "$(run gate-deadline60 --entry entries/schedule.json --pipeline out/p-deadline60.json)" "3"
py <<'PY' > out/gate-deadline.log 2>&1
import datetime as dt, json
day = json.load(open("out/schedule.rep.json"))
hour = json.load(open("out/gate-deadline60.rep.json"))
minutes = {n: next(s for s in json.load(open(f))["stages"] if s["id"] == "release")["deadline_minutes"]
           for n, f in (("day", "pipelines/release-coupon-fix.json"), ("hour", "out/p-deadline60.json"))}
assert minutes == {"day": 1440, "hour": 60}, minutes
def at(rep): return dt.datetime.strptime(rep["approval"]["deadline_at"], "%Y-%m-%dT%H:%M:%SZ")
gap = (at(day) - at(hour)).total_seconds() / 60
assert gap == minutes["day"] - minutes["hour"] == 1380, (gap, minutes)
for rep in (day, hour):
    assert rep["approval"]["deadline_at"] in rep["problem"]["detail"], rep["problem"]["detail"]
assert day["approval"]["deadline_at"] != hour["approval"]["deadline_at"]
parked = {n: [json.loads(l)["deadline_at"] for l in open(f"out/{f}.jsonl")
              if json.loads(l)["kind"] == "approval-parked"]
          for n, f in (("day", "schedule"), ("hour", "gate-deadline60"))}
assert parked["day"] != parked["hour"] and len(parked["day"]) == len(parked["hour"]) == 1, parked
print("deadline_minutes is read at the gate:", minutes["day"], "and", minutes["hour"],
      "minutes stamp deadlines", int(gap), "minutes apart, each named by its own refusal")
PY
check "deadline_minutes is read into the parked gate and into the refusal that names it" "$?" "0"

py <<'PY' > out/gate-body.log 2>&1
import json
def note(name):
    key = json.load(open(f"out/{name}.rep.json"))["run_key"]
    rows = [json.loads(l) for l in open(f"out/{name}.state/{key}/effects.jsonl")]
    return [r["release_note"] for r in rows]
plain, edited = note("human"), note("gate-edit")
declared = json.load(open("entries/event.json"))["payload"]["progress"]["decision_body"]
assert len(plain) == len(edited) == 1, (plain, edited)
assert plain != edited, (plain, edited)
assert edited[0] == declared["release_note"], (edited, declared)
print("decision_body is read into the effect: the edited door ships the reviewer's note,",
      "the approving door ships the default")
PY
check "the reviewer's edit is what ships, read out of the effect table" "$?" "0"

echo "7. the effect, its class and its unwind"
check "an effect declared irreversible with no mandate" \
      "$(run comp-irrev --entry entries/external.json --pipeline out/p-irrev.json)" "3"
check "the same effect with a mandate" \
      "$(run comp-mandate --entry entries/external.json --pipeline out/p-irrev-mandate.json)" "3"
py <<'PY' > out/comp-class.log 2>&1
import json
comp = json.load(open("out/external.rep.json"))["compensation"]
denied = json.load(open("out/comp-irrev.rep.json"))
mandated = json.load(open("out/comp-mandate.rep.json"))["compensation"]
assert comp["declared"]["irreversibility"] == "compensable"
assert comp["unwind"]["compensated"] == 1 and comp["unwind"]["not_required"] == 0
assert denied["problem"]["type"] == "urn:agentic:problem:policy-denied", denied["problem"]
assert denied["problem"]["status"] == 403
assert denied["problem"]["rule_id"] == "compensation.irreversible-requires-mandate"
assert denied["effect_rows"] == 0, "the effect was refused before it committed"
assert mandated["declared"]["irreversibility"] == "irreversible"
assert mandated["unwind"]["not_required"] == 1 and mandated["unwind"]["compensated"] == 0
assert mandated["plan"]["would_unwind"] == [] and len(mandated["plan"]["unreachable"]) == 1
print("three readings of one declared class: compensated, denied 403 before the effect, "
      "and not-required against a plan that already named it unreachable")
PY
check "the irreversibility class is read before the effect commits, and each member differs" "$?" "0"
py <<'PY' > out/comp-order.log 2>&1
import json
rows = [json.loads(l) for l in open("out/external.jsonl")]
kinds = [r["kind"] for r in rows]
assert kinds.index("effect-declared") < kinds.index("unwind-plan-read") \
       < kinds.index("effect-sealed"), kinds
committed = [i for i, r in enumerate(rows)
             if r["kind"] == "step-committed" and r["step"] == "production"][0]
assert kinds.index("effect-declared") < committed, "declared after the effect committed"
print("declaration, then the plan, then the effect, then the seal")
PY
check "the declaration and the unwind plan are durable before the effect commits" "$?" "0"
py <<'PY' > out/comp-verify.log 2>&1
import json
sealed = json.load(open("out/human.rep.json"))
unwound = json.load(open("out/external.rep.json"))
assert sealed["compensation"]["sealed"] and sealed["compensation"]["unwind"] is None
assert sealed["success_ladder"]["promotion"] is True and sealed["outcome"] == "completed"
assert unwound["compensation"]["sealed"] and unwound["compensation"]["unwind"]["reason"] == "failed"
assert unwound["stop_reason"] == "post-release-verification-failed"
assert unwound["disposition"] == "retry" and unwound["success_ladder"]["promotion"] is False
print("verify_outcome read after the seal: pass reaches promotion, fail walks the register back")
PY
check "verify_outcome is read after the seal: pass promotes, fail unwinds" "$?" "0"
py <<'PY' > out/comp-undo.log 2>&1
import json
declared = next(s for s in json.load(open("pipelines/release-coupon-fix.json"))["stages"]
                if s["id"] == "production")["compensation"]["compensating_action"]
rep = json.load(open("out/external.rep.json"))
out = rep["compensation"]["unwind"]["outcomes"][0]
assert out["operator"] == declared["operator"] and out["outcome"] == "compensated", out
rows = [json.loads(l) for l in
        open(f"out/external.state/{rep['run_key']}/outward-calls.jsonl")]
undo = [r for r in rows if r.get("operator") == declared["operator"]]
assert len(undo) == 1, undo
assert rep["outward_calls"] == 4 and json.load(open("out/human.rep.json"))["outward_calls"] == 3
print("the undo is one forward operation under its own key:", declared["operator"],
      "- 4 outward calls where the sealed run made 3")
PY
check "the compensating action is a forward operation under its own key" "$?" "0"

echo "8. the schedule door"
check "catch_up skip"     "$(run s-skip  --entry out/e-s-skip.json)" "3"
check "catch_up fire_all" "$(run s-all   --entry out/e-s-all.json)" "3"
check "a two-day lookback" "$(run s-look2 --entry out/e-s-look2.json)" "3"
check "the same rule declared in UTC" "$(run s-utc --entry out/e-s-utc.json)" "3"
py <<'PY' > out/s-catchup.log 2>&1
import json
def sched(n): return json.load(open(f"out/{n}.rep.json"))["schedule"]
once, skip, allf = sched("schedule"), sched("s-skip"), sched("s-all")
assert (once["declaration"]["catch_up"], len(once["fired"])) == ("fire_once", 1), once
assert (skip["declaration"]["catch_up"], len(skip["fired"])) == ("skip", 0), skip
assert (allf["declaration"]["catch_up"], len(allf["fired"])) == ("fire_all", 3), allf
assert len(once["missed"]) == len(skip["missed"]) == len(allf["missed"]) == 3
fired = {n: len([json.loads(l) for l in open(f"out/{n}.jsonl")
                 if json.loads(l)["kind"] == "schedule-fired"])
         for n in ("schedule", "s-skip", "s-all")}
assert fired == {"schedule": 1, "s-skip": 0, "s-all": 3}, fired
print("three missed occurrences, one declared policy each:", fired)
PY
check "catch_up is read after the missed set: skip 0, fire_once 1, fire_all 3" "$?" "0"
py <<'PY' > out/s-lookback.log 2>&1
import json
wide = json.load(open("out/schedule.rep.json"))["schedule"]
narrow = json.load(open("out/s-look2.rep.json"))["schedule"]
assert wide["declaration"]["lookback_days"] == 14 and len(wide["missed"]) == 3, wide
assert narrow["declaration"]["lookback_days"] == 2 and len(narrow["missed"]) == 1, narrow
assert narrow["window"]["from"] > wide["window"]["from"]
print("lookback_days bounds the catch-up window: 14 days ->", len(wide["missed"]),
      "missed, 2 days ->", len(narrow["missed"]))
PY
check "lookback_days bounds how far back catch-up reaches" "$?" "0"
py <<'PY' > out/s-dst.log 2>&1
import json
zoned = json.load(open("out/schedule.rep.json"))["schedule"]
utc = json.load(open("out/s-utc.rep.json"))["schedule"]
assert zoned["declaration"]["timezone"] == "America/New_York"
assert utc["declaration"]["timezone"] == "UTC"
# the transition falls between the second and third occurrence of the zoned set
before, after = zoned["occurrences"][1], zoned["occurrences"][2]
assert before.endswith("06:00:00Z") and after.endswith("07:00:00Z"), (before, after)
assert all(o.endswith("02:00:00Z") for o in utc["occurrences"]), utc["occurrences"]
assert zoned["occurrences"] != utc["occurrences"]
print("the declared zone is read: local 02:00 survives the transition as",
      before[-9:], "then", after[-9:], "; declared UTC gives 02:00:00Z on both sides")
PY
check "the declared time zone is read: local wall time survives the transition" "$?" "0"
py <<'PY' > out/s-key.log 2>&1
import json
s = json.load(open("out/schedule.rep.json"))["schedule"]
env = json.load(open("entries/schedule.json"))
assert s["key_matches_envelope"] is True
assert s["nominal_key"] == env["idempotency_key"], (s["nominal_key"], env["idempotency_key"])
assert s["backfill_key"] == s["nominal_key"], "a backfill of the same occurrence must key the same"
assert s["next_key"] != s["nominal_key"], "the next occurrence must key differently"
assert s["next_occurrence"] == "2026-11-10T07:00:00Z", s["next_occurrence"]
declared = env["payload"]["progress"]["schedule"]
for field in ("unit_ref", "recurrence", "starts_at", "timezone", "catch_up", "lookback_days"):
    assert s["declaration"][field] == declared[field], field
print("the fire key is (unit, nominal occurrence): on-time and backfill agree,",
      "the next occurrence does not")
PY
check "the replay key is derived from the nominal fire time, so a backfill converges" "$?" "0"
check "an envelope whose key is not the one its occurrence derives" \
      "$(run s-wrongkey --entry out/e-s-wrongkey.json)" "2"
py <<'PY' > out/s-wrongkey.log 2>&1
import json
rep = json.load(open("out/s-wrongkey.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:idempotency-conflict", rep["problem"]
assert rep["problem"]["status"] == 409 and rep["budget"]["spent_micros"] == 0
print("a fire key minted anywhere but from the nominal occurrence is refused 409")
PY
check "a scheduled envelope carrying any other key is refused before anything runs" "$?" "0"
check "a recurrence part the evaluator does not serve" "$(run s-badrule --entry out/e-s-badrule.json)" "2"
py <<'PY' > out/s-badrule.log 2>&1
import json
rep = json.load(open("out/s-badrule.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:unsupported-rule-part", rep["problem"]
assert rep["problem"]["status"] == 422 and rep["problem"]["unsupported_parts"] == ["FREQ=SECONDLY"]
assert rep["budget"]["spent_micros"] == 0 and rep["executor"]["marker"] is None
print("the grammar gate refuses before a declaration exists:", rep["problem"]["unsupported_parts"])
PY
check "an unsupported rule part is refused at the grammar gate with nothing bound" "$?" "0"
py <<'PY' > out/s-interval.log 2>&1
import json, datetime as dt
occ = json.load(open("out/s-all.rep.json"))["schedule"]["occurrences"]
t = [dt.datetime.strptime(o, "%Y-%m-%dT%H:%M:%SZ") for o in occ]
gaps = {(b - a).total_seconds() for a, b in zip(t, t[1:])}
assert len(gaps) > 1, gaps
rule = json.load(open("entries/schedule.json"))["payload"]["progress"]["schedule"]["recurrence"]
assert "BYDAY=TU,TH" in rule, rule
print("the rule is not reducible to a fixed interval: gaps", sorted(int(g) for g in gaps))
PY
check "the recurrence in use is inexpressible as a fixed interval" "$?" "0"
py <<'PY' > out/s-samepath.log 2>&1
import json
human = {json.loads(l)["kind"] for l in open("out/human.jsonl")}
sched = {json.loads(l)["kind"] for l in open("out/s-all.jsonl")}
elsewhere = set()
for name in ("human", "event", "external", "reject", "loop-iter1"):
    elsewhere |= {json.loads(l)["kind"] for l in open(f"out/{name}.jsonl")}
door_only = sched - elsewhere
assert door_only == {"schedule-expanded", "schedule-fired"}, sorted(door_only)
shared = {"unit-submitted", "plan-priced", "run-bound", "stage-entered",
          "step-committed", "evaluation-gated", "approval-parked"}
assert shared <= sched and shared <= human, sorted(shared - sched)
print("a fire travels the same path: the only kinds unique to the schedule door are",
      sorted(door_only))
PY
check "a scheduled fire takes the same downstream path as a person's" "$?" "0"

echo "9. crash and resume"
python3 run.py --entry entries/human.json --ledger out/crash.jsonl --report out/crash-a.rep.json \
    --out out/crashstate --crash-at 'shard-integration' > out/crash-a.log 2>&1
check "the crash is a process death, not a return value" "$?" "137"
check "the resumed process completes" \
      "$(python3 run.py --entry entries/human.json --ledger out/crash.jsonl \
         --report out/crash-b.rep.json --out out/crashstate > out/crash-b.log 2>&1; echo $?)" "0"
py <<'PY' > out/resume.log 2>&1
import json
b = json.load(open("out/crash-b.rep.json"))
first = json.load(open("out/human.rep.json"))
assert b["resume_point_at_start"] == 6, b["resume_point_at_start"]
assert b["steps_replayed"] == 6 and b["steps_executed"] == 5, b
assert b["steps_replayed"] + b["steps_executed"] == first["steps_committed"] == 11
assert b["outcome"] == "completed"
assert b["run_key"] == json.load(open("entries/human.json"))["idempotency_key"], b["run_key"]
assert b["run_key"] == first["run_key"], "the resume began a different run"
assert first["resume_point_at_start"] == 0 and first["steps_replayed"] == 0, first
print("resumed at step", b["resume_point_at_start"], ":", b["steps_replayed"],
      "replayed,", b["steps_executed"], "run, 11 committed in all")
PY
check "the resumed run continues at the first incomplete step, replaying the rest" "$?" "0"
py <<'PY' > out/replay-not-rerun.log 2>&1
import json
rows = [json.loads(l) for l in open("out/crash.jsonl")]
nonces = [r["process_nonce"] for r in rows if r["kind"] == "unit-submitted"]
assert len(nonces) == 2 and nonces[0] != nonces[1], nonces
b = json.load(open("out/crash-b.rep.json"))
assert b["process_nonce"] == nonces[1], "the report is the second process's"
assert b["nonces"]["draft"] == nonces[0], (b["nonces"], nonces)
assert b["nonces"]["judge"] == nonces[0]
print("the replayed results carry the first process's nonce, not the reader's: journalled, "
      "not re-run")
PY
check "a journalled result is replayed from the journal rather than re-executed" "$?" "0"
py <<'PY' > out/resume-budget.log 2>&1
import json
b = json.load(open("out/crash-b.rep.json"))
assert b["budget"]["spent_before_this_process_micros"] == 200000, b["budget"]
assert b["budget"]["remaining_at_bind_micros"] == 1500000 - 200000, b["budget"]
assert b["budget"]["spent_micros"] == 370000 == json.load(
    open("out/human.rep.json"))["budget"]["spent_micros"]
bound = [json.loads(l) for l in open("out/crash.jsonl") if json.loads(l)["kind"] == "run-bound"]
assert [r["spent_micros"] for r in bound] == [0, 200000], bound
print("the resume began with", b["budget"]["spent_before_this_process_micros"],
      "already spent and", b["budget"]["remaining_at_bind_micros"],
      "left, not a fresh ceiling")
PY
check "the resumed run continues under the ceiling it had left, not a fresh one" "$?" "0"
py <<'PY' > out/resume-corr.log 2>&1
import json, os
rows = [json.loads(l) for l in open("out/crash.jsonl")]
assert len({r["correlation_id"] for r in rows}) == 1, "the resume opened a new correlation"
b = json.load(open("out/crash-b.rep.json"))
assert b["correlation_source"] == "step-record", b["correlation_source"]
assert not os.path.exists("out/crash-a.rep.json"), \
    "the killed process wrote a report, so the crash was not a process death"
bound = [r["correlation_source"] for r in rows if r["kind"] == "run-bound"]
assert bound == ["envelope", "step-record"], bound
print("one correlation id across the discontinuity, re-attached from the record on the resume")
PY
check "the correlation chain survives the crash and is re-attached from the record" "$?" "0"
py <<'PY' > out/resume-effects.log 2>&1
import json
b = json.load(open("out/crash-b.rep.json"))
key = b["run_key"]
outward = [json.loads(l) for l in open(f"out/crashstate/{key}/outward-calls.jsonl")]
assert len(outward) == 3, [r["operator"] for r in outward]
assert b["outward_calls"] == 3 and b["effect_rows"] == 1
assert len({r["key"] for r in outward}) == 3
print(len(outward), "outward calls and 1 effect row across two processes: no duplicate")
PY
check "the crash repeats no outward call and no effect, counted from outside the executor" "$?" "0"
python3 run.py --entry entries/human.json --ledger out/crash2.jsonl --report out/crash2-a.rep.json \
    --out out/crash2state --crash-at 'draft#2' > out/crash2-a.log 2>&1
check "a crash between the outward call and its checkpoint is a process death" "$?" "137"
check "the run resumes over the uncheckpointed step" \
      "$(python3 run.py --entry entries/human.json --ledger out/crash2.jsonl \
         --report out/crash2-b.rep.json --out out/crash2state > out/crash2-b.log 2>&1; echo $?)" "0"
py <<'PY' > out/resume-keyed.log 2>&1
import json
b = json.load(open("out/crash2-b.rep.json"))
key = b["run_key"]
outward = [json.loads(l) for l in open(f"out/crash2state/{key}/outward-calls.jsonl")]
drafts = [r for r in outward if r["operator"] == "propose-patch"]
assert len(drafts) == 2, drafts
assert b["resume_point_at_start"] == 3 and b["steps_replayed"] == 3, b
assert b["outward_calls"] == 3 and b["outcome"] == "completed"
print("the step whose checkpoint the crash ate was re-executed and did not call out twice: ",
      len(drafts), "proposals for 2 iterations")
PY
check "an at-least-once step is effectively-once because its outward call is keyed" "$?" "0"
check "the human door's envelope submitted a second time against its own state" \
      "$(run again-human --entry entries/human.json)" "0"
check "the schedule door's envelope submitted a second time against its own state" \
      "$(run again-sched --entry entries/schedule.json)" "3"
py <<'PY' > out/resubmit.log 2>&1
import json, subprocess, sys
# The same envelope, the same run key, the same state directory: a redelivery is
# a replay of one run, so the answer a caller reads is the one it already had -
# including the answer the release gate reached by expiring.
def again(name, entry, out):
    rc = subprocess.run([sys.executable, "run.py", "--entry", entry, "--ledger", f"out/{name}.jsonl",
                         "--report", f"out/{name}.rep.json", "--out", out],
                        capture_output=True, text=True)
    last = (rc.stdout + rc.stderr).strip().splitlines()[-1]
    return rc.returncode, last, json.load(open(f"out/{name}.rep.json"))
pairs = []
for door, entry, out in (("human", "entries/human.json", "out/again-human.state"),
                         ("sched", "entries/schedule.json", "out/again-sched.state")):
    first_rc = int(open(f"out/again-{door}.rc").read().strip())
    first = json.load(open(f"out/again-{door}.rep.json"))
    first_last = open(f"out/again-{door}.log").read().strip().splitlines()[-1]
    second_rc, second_last, second = again(f"again2-{door}", entry, out)
    assert first_last == second_last, (door, first_last, second_last)
    assert first_rc == second_rc, (door, first_rc, second_rc)
    for field in ("disposition", "outcome", "stop_reason", "run_key"):
        assert first[field] == second[field], (door, field, first[field], second[field])
    # The lifecycle is the same answer, minus the ask nobody is asked twice: a
    # gate already decided is replayed and never parks again, where a gate that
    # expired parks and expires again.
    def without_gate(states):
        out = []
        for state in states:
            if state != "input-required" and (not out or out[-1] != state):
                out.append(state)
        return out
    want = first["task_states_seen"] if door == "sched" else without_gate(first["task_states_seen"])
    assert second["task_states_seen"] == want, (door, second["task_states_seen"], want)
    assert ("input-required" in second["task_states_seen"]) == (door == "sched"), door
    assert second["steps_replayed"] > 0 and second["steps_executed"] == 0, second
    assert (first["problem"] or {}).get("type") == (second["problem"] or {}).get("type"), door
    pairs.append((door, second["disposition"], second_rc, second["steps_replayed"]))
assert [p[1] for p in pairs] == ["accept", "escalate"], pairs
assert pairs[1][2] == 3 and "input-required" in json.load(
    open("out/again2-sched.rep.json"))["task_states_seen"]
print("two envelopes resubmitted against their own state, each answering exactly as before:",
      pairs)
PY
check "one envelope answers the same on a redelivery, gate expiry included" "$?" "0"

echo "10. budget"
check "a ceiling below the plan floor" "$(run below-floor --entry out/e-belowfloor.json)" "2"
py <<'PY' > out/budget-floor.log 2>&1
import json, os
rep = json.load(open("out/below-floor.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:budget-exhausted", rep["problem"]
assert rep["problem"]["status"] == 402
assert rep["problem"]["stop_reason"] == "estimate-exceeds-ceiling"
assert rep["budget"]["spent_micros"] == 0 and rep["executor"]["marker"] is None
assert not os.path.exists("out/below-floor.state"), "an executor was bound anyway"
kinds = {json.loads(l)["kind"] for l in open("out/below-floor.jsonl")}
assert "run-bound" not in kinds and "step-committed" not in kinds, sorted(kinds)
print("the estimate loses before anything is bound: 402, zero spend, no executor state")
PY
check "the estimate is compared before commitment and nothing is created when it loses" "$?" "0"
check "a ceiling that runs dry inside the fan-out" "$(run mid-fan --entry out/e-midfan.json)" "3"
py <<'PY' > out/budget-midfan.log 2>&1
import json
rep = json.load(open("out/mid-fan.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:budget-exhausted"
assert rep["problem"]["stop_reason"] == "ceiling-reached", rep["problem"]
assert rep["budget"]["spent_micros"] <= rep["budget"]["ceiling_micros"], rep["budget"]
assert rep["budget"]["spent_micros"] == 280000 and rep["budget"]["ceiling_micros"] == 300000
committed = [json.loads(l)["step"] for l in open("out/mid-fan.jsonl")
             if json.loads(l)["kind"] == "step-committed"]
assert "shard-unit" in committed and "shard-integration" not in committed, committed
assert "shard-integration" in rep["problem"]["detail"], rep["problem"]["detail"]
print("the check is before the call, not after it: stopped at shard-integration with",
      rep["budget"]["spent_micros"], "of", rep["budget"]["ceiling_micros"], "spent")
PY
check "the ceiling is checked before each call, so the stop lands under it" "$?" "0"
py <<'PY' > out/budget-partial.log 2>&1
import json
rep = json.load(open("out/mid-fan.rep.json"))
test = next(s for s in rep["stages"] if s["stage"] == "test")
assert test["entered"] is True and test["outcome"] is None, test
assert rep["steps_committed"] == rep["steps_executed"] == 8, rep["steps_committed"]
assert rep["outward_calls"] == 3 and rep["effect_rows"] == 0
assert rep["task_state"] == "failed" and rep["success_ladder"]["candidate"] is True
print("only the unit stops: the stage it stopped in is entered with no outcome, and",
      rep["steps_committed"], "committed steps and", rep["outward_calls"],
      "outward calls are retained")
PY
check "exhaustion terminates the unit and retains its partial results" "$?" "0"
py <<'PY' > out/budget-nocaller.log 2>&1
import json
schema = json.load(open("schemas/progress.schema.json"))
assert schema["additionalProperties"] is False
for banned in ("ceiling_micros", "budget", "executor", "register", "policy_version", "criterion"):
    assert banned not in schema["properties"], banned
entry = json.load(open("../end-to-end/schemas/entry.schema.json"))
assert entry["properties"]["budget"]["properties"]["on_exceed"] == {"const": "terminate_unit"}
print("no member by which a caller raises its own ceiling or opts out of the guarantee")
PY
check "no caller can raise its own ceiling or decline the guarantee" "$?" "0"
py <<'PY' > out/budget-exits.log 2>&1
import glob, json, re
rc = {}
for path in sorted(glob.glob("out/*.rep.json")):
    rep = json.load(open(path))
    rc[path] = (rep["outcome"], rep["budget"]["spent_micros"], rep["problem"] is not None)
zero_spend_failures = [p for p, (o, s, _) in rc.items() if o == "failed" and s == 0]
spent_failures = [p for p, (o, s, _) in rc.items() if o == "failed" and s > 0]
assert zero_spend_failures and spent_failures, (zero_spend_failures, spent_failures)
# every zero-spend failure carries a problem body; every completed run carries none
for p, (o, s, has) in rc.items():
    if o == "completed":
        assert not has and s > 0, p
    if s == 0:
        assert has, p
print(len(rc), "reports:", len(zero_spend_failures), "refused with nothing spent,",
      len(spent_failures), "ran and stopped")
PY
check "a refusal with nothing spent and a unit that ran and stopped are different outcomes" "$?" "0"
py <<'PY' > out/exit-codes.log 2>&1
import glob, json, os
# The sentence is about the mapping from exit code to spend, so the exit status
# is recorded beside the report and the pair is walked. Nothing here reads a
# code the suite compared against a literal and threw away.
pairs = []
for rc_path in sorted(glob.glob("out/*.rc")):
    name = os.path.basename(rc_path)[:-3]
    rep_path = f"out/{name}.rep.json"
    if not os.path.exists(rep_path):
        continue
    rep = json.load(open(rep_path))
    pairs.append((name, int(open(rc_path).read().strip()), rep["outcome"],
                  rep["budget"]["spent_micros"], rep["problem"] is not None))
for name, code, outcome, spent, problem in pairs:
    if code == 0:
        assert outcome == "completed" and spent > 0 and not problem, name
    elif code == 2:
        assert problem and spent == 0, name
    elif code == 3:
        assert outcome == "failed" and spent > 0, name
    else:
        raise AssertionError(f"{name} exited {code}")
codes = {c for _, c, _, _, _ in pairs}
assert codes == {0, 2, 3}, sorted(codes)
assert len(pairs) >= 20, len(pairs)
print(len(pairs), "runs with their exit status recorded beside their report; all three codes",
      sorted(codes), "occur and each holds the mapping the README states")
PY
check "the exit code is read beside the report: 0 spent, 2 zero-spend refusal, 3 spent failure" "$?" "0"

echo "11. refusals"
check "a malformed envelope" \
      "$(python3 run.py --entry out/e-malformed.json --ledger out/malformed.jsonl \
         --report out/malformed.rep.json --out out/malformed.state > out/malformed.log 2>&1; echo $?)" "2"
py <<'PY' > out/malformed.log2 2>&1
import json, os
assert not os.path.exists("out/malformed.jsonl"), "a ledger was written for a document never admitted"
assert not os.path.exists("out/malformed.state")
body = json.loads("".join(open("out/malformed.log").read().splitlines(True)[1:]))
assert body["type"] == "urn:agentic:problem:document-invalid" and body["status"] == 422
assert any("budget" in json.dumps(c) for c in body["causes"]), body["causes"]
print("a malformed envelope is refused 422 naming the missing member, with no ledger")
PY
check "a malformed envelope is refused before admission and writes no ledger" "$?" "0"
check "a run key returning under a different correlation id" \
      "$(python3 run.py --entry out/e-othercorr.json --ledger out/othercorr.jsonl \
         --report out/othercorr.rep.json --out out/human.state > out/othercorr.log 2>&1; echo $?)" "2"
py <<'PY' > out/othercorr.log2 2>&1
import json
rep = json.load(open("out/othercorr.rep.json"))
assert rep["problem"]["type"] == "urn:agentic:problem:idempotency-conflict", rep["problem"]
assert rep["problem"]["status"] == 409 and rep["budget"]["spent_micros"] == 0
print("one run key, one correlation: a second correlation on the same key is 409")
PY
check "a run key that returns under another correlation id is refused 409" "$?" "0"
py <<'PY' > out/refusal-set.log 2>&1
import glob, json
seen = {}
for path in glob.glob("out/*.rep.json"):
    rep = json.load(open(path))
    for r in [rep["problem"]] + rep["refusals"] if rep["problem"] else rep["refusals"]:
        if r:
            seen[r["type"]] = r["status"]
want = {"urn:agentic:problem:criterion-unresolvable": 422,
        "urn:agentic:problem:budget-exhausted": 402,
        "urn:agentic:problem:deadline-exceeded": 504,
        "urn:agentic:problem:document-invalid": 422,
        "urn:agentic:problem:policy-denied": 403,
        "urn:agentic:problem:idempotency-conflict": 409,
        "urn:agentic:problem:unsupported-rule-part": 422}
assert seen == want, (f"produced and not named: {sorted(set(seen) - set(want))}; "
                      f"named and not produced: {sorted(set(want) - set(seen))}")
print(len(seen), "failure types produced by this example, and the README names exactly those")
PY
check "the refusal table names every type these runs produce, and no others" "$?" "0"
py <<'PY' > out/refusal-registered.log 2>&1
import glob, importlib.util, json
spec = importlib.util.spec_from_file_location("prog_h", "harnesses.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
errors_iface, _ = mod.errors()
sched_iface = mod.scheduling()
registered = set(errors_iface.REGISTRY) | set(sched_iface.REGISTRY)
produced = set()
for path in glob.glob("out/*.rep.json"):
    rep = json.load(open(path))
    for r in ([rep["problem"]] if rep["problem"] else []) + rep["refusals"]:
        produced.add(r["type"].rsplit(":", 1)[-1])
assert produced <= registered, sorted(produced - registered)
assert len(produced) == 7, sorted(produced)
print(len(produced), "types produced, every one a row of a capability's own closed registry")
PY
check "every failure type is a registered suffix, never one minted at a call site" "$?" "0"
py <<'PY' > out/refusal-retryable.log 2>&1
import glob, json
rows = []
for path in glob.glob("out/*.rep.json"):
    rep = json.load(open(path))
    for r in ([rep["problem"]] if rep["problem"] else []) + rep["refusals"]:
        rows.append((r["type"].rsplit(":", 1)[-1], r["status"], r["retryable"]))
by_type = {t: (s, rt) for t, s, rt in rows}
assert by_type["deadline-exceeded"] == (504, True), by_type["deadline-exceeded"]
assert by_type["budget-exhausted"] == (402, False), by_type["budget-exhausted"]
assert by_type["idempotency-conflict"] == (409, False)
assert by_type["policy-denied"] == (403, False)
print("retryable is a member of the body, read not inferred:", sorted(by_type.items()))
PY
check "retryable is carried on the body and is not a function of the status" "$?" "0"
py <<'PY' > out/refusal-onepath.log 2>&1
import re
sources = ["run.py", "harnesses.py"]
hits = []
for path in sources:
    text = open(path).read()
    for m in re.finditer(r'"type"\s*:', text):
        hits.append((path, text[:m.start()].count("\n") + 1))
    assert 'application/problem+json' in text or path != "run.py"
assert not hits, hits
assert open("run.py").read().count("ERRI.construct(") == 1
print("no source file here assembles a problem body; one call site reaches the registry gate")
PY
check "nothing in this example builds a problem body of its own" "$?" "0"

echo "12. swappability"
check "the second executor" "$(run swap-exec --entry entries/human.json --executor second)" "0"
check "the second register"  "$(run swap-reg --entry entries/external.json --register second)" "3"
py <<'PY' > out/swap.log 2>&1
import json
one, two = (json.load(open(f"out/{n}.rep.json")) for n in ("human", "swap-exec"))
assert one["executor"]["marker"] != two["executor"]["marker"], one["executor"]
assert one["executor"]["effect_commit_mode"] != two["executor"]["effect_commit_mode"]
assert one["steps_committed"] == two["steps_committed"] == 11
assert one["effect_rows"] == two["effect_rows"] == 1
assert one["outcome"] == two["outcome"] == "completed"
assert one["budget"]["spent_micros"] == two["budget"]["spent_micros"]
print("the swap moves the marker and the commit mode and leaves the run identical:",
      one["executor"]["marker"], "vs", two["executor"]["marker"])
PY
check "the executor swap moves the marker and the commit mode, same eleven steps" "$?" "0"
py <<'PY' > out/swap-reg.log 2>&1
import json
one, two = (json.load(open(f"out/{n}.rep.json"))["compensation"]
            for n in ("external", "swap-reg"))
assert one["declared"]["register_observed"] != two["declared"]["register_observed"]
assert one["unwind"]["order"] == two["unwind"]["order"], (one["unwind"], two["unwind"])
assert one["unwind"]["compensated"] == two["unwind"]["compensated"] == 1
print("the register swap moves the marker and leaves the reverse walk identical:",
      one["declared"]["register_observed"], "vs", two["declared"]["register_observed"])
PY
check "the register swap moves the marker and leaves the unwind order identical" "$?" "0"
py <<'PY' > out/swap-config.log 2>&1
import hashlib, re
digest = hashlib.sha256(open("run.py", "rb").read()).hexdigest()
text = open("run.py").read()
# the walk names no executor and no register: both arrive as a name on the command line
walk = text[text.index("def stage_sequence"):text.index("def bind")]
for banned in ("dryrun", "H.durable", "H.compensation", "executor_cls",
               "register_cls", "Adapter", "EffectTable"):
    assert banned not in walk, banned
assert re.search(r'choices=\("dryrun", "second"\)', text)
print("both bindings are one name from the command line; the walk names neither. run.py",
      digest[:12], "unchanged between the two runs")
PY
check "the swap is configuration: the walk names no executor and no register" "$?" "0"

echo "13. the example's own bookkeeping"
py <<'PY' > out/quotes.log 2>&1
import glob, json, os, re, subprocess, sys
REPO = os.path.abspath("../..")
research = {}
for path in glob.glob(os.path.join(REPO, "kb", "research", "*.jsonl")):
    for line in open(path):
        if line.strip():
            row = json.loads(line)
            research[row["id"]] = row

def record_text(cid):
    if cid.startswith("REF-"):
        return open(os.path.join(REPO, cid[4:].split("#", 1)[0]), errors="replace").read()
    if cid.startswith("X-"):
        row = research[cid]
        return " ".join(str(row.get(k) or "") for k in ("snippet", "claim", "title", "url"))
    out = subprocess.run([sys.executable, "tools/kb.py", "show", cid],
                         capture_output=True, text=True, cwd=REPO)
    if out.returncode != 0:
        raise KeyError(cid)
    doc = json.loads(out.stdout)
    return " ".join([str(doc.get("text") or "")]
                    + [str(v) for v in (doc.get("columns") or {}).values()])

# A quotation is checked against the records its own row cites, not against the
# id that happens to sit next to it: in every table here the ids are in the
# evidence column, to the right of the cell the quotation is in. The population
# is every quoted string in the file outside a code span, and the floor below is
# on that population, so narrowing the regex fails the check instead of shrinking
# what it looks at.
ID = re.compile(r"`((?:F|T|E|R|X|REF)-[^`<>]+)`")     # the angle-bracketed form is the
CODE = re.compile(r"`[^`]*`")                         # convention being stated, not a citation
QUOTE = re.compile(r'"([^"]+)"')
cache = {}
def resolved(cid):
    if cid not in cache:
        cache[cid] = " ".join(record_text(cid).split())
    return cache[cid]
checked, quoted, bad = 0, 0, []
for path in ("README.md", "provenance.json"):
    for n, line in enumerate(open(path), 1):
        ids = ID.findall(line)
        quotes = QUOTE.findall(CODE.sub(" ", line)) if path.endswith(".md") else []
        if path.endswith(".json"):                     # no table rows: the pair rule
            quotes = [q for _, q in re.findall(r'`((?:F|T|E|R|X|REF)-[^`]+)`\s+."([^"]+)."', line)]
        quoted += len(quotes)
        if quotes and not ids:
            bad.append(f"{path}:{n}: {quotes[0][:60]!r} is quoted on a row that cites nothing")
            continue
        texts = []
        for cid in ids:
            try:
                texts.append(resolved(cid))
            except Exception as exc:
                bad.append(f"{path}:{n}: {cid} does not resolve ({exc})")
        for quote in quotes:
            checked += 1
            want = " ".join(quote.replace("\\|", "|").split())
            if not any(want in text for text in texts):
                bad.append(f"{path}:{n}: none of {ids} carries {want[:70]!r}")
assert not bad, "\n".join(bad)
assert checked == quoted, (checked, quoted)
assert checked >= 81, checked
print(checked, "quoted strings across README.md and provenance.json - every one on the file,",
      "outside a code span - each verbatim in a record its own row cites")
PY
check "every quote is verbatim in a record its own row cites, by lookup not by memory" "$?" "0"
py <<'PY' > out/cites.log 2>&1
import json, os, re
ID = re.compile(r"REF-[A-Za-z0-9_./#,+-]+|\b[FTXER]-[a-z][a-z0-9]*-[a-z0-9-]+\b")
found, scanned = set(), 0
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ("out", "__pycache__")]
    for name in sorted(files):
        if name.endswith((".md", ".py", ".sh", ".json")) and name != "provenance.json":
            found |= set(ID.findall(open(os.path.join(root, name), errors="replace").read()))
            scanned += 1
cites = set(json.load(open("provenance.json"))["cites"])
assert found == cites, (f"only in the files: {sorted(found - cites)}; "
                        f"only in provenance.cites: {sorted(cites - found)}")
print(len(cites), "ids across", scanned, "files, and provenance.cites is exactly those")
PY
check "provenance.cites is exactly the ids the rows carry, both directions" "$?" "0"
py <<'PY' > out/kinds.log 2>&1
import glob, json, re
written = set()
for path in glob.glob("out/*.jsonl"):
    written |= {json.loads(line)["kind"] for line in open(path)}
row = [l for l in open("README.md") if l.startswith("| The receipt:")][0]
named = {t.strip() for span in re.findall(r"`([^`]+)`", row) for t in span.split(",")}
named = {t for t in named if re.fullmatch(r"[a-z]+(?:-[a-z]+)*", t)}
assert named == written, (f"named and never written: {sorted(named - written)}; "
                          f"written and never named: {sorted(written - named)}")
counted = re.search(r"The ([\w-]+) kinds these runs write", row).group(1)
words = {"twenty-one": 21, "twenty": 20, "nineteen": 19, "twenty-two": 22}
assert words.get(counted) == len(written), (counted, len(written))
print(len(written), "record kinds on the ledgers, and the receipt row names exactly those")
PY
check "the receipt row names every record kind these runs write, and counts them right" "$?" "0"
py <<'PY' > out/headings.log 2>&1
import re
WANT = ["1. Ideal", "2. Standards", "3. The call", "4. What the user sees",
        "5. Composition", "6. Extension points"]
tops = re.findall(r"^## (.+)$", open("README.md").read(), re.M)
assert tops == WANT, tops
print(len(tops), "top-level headings, in order:", "; ".join(tops))
PY
check "the README carries the six headings the example shape enumerates, in order" "$?" "0"
py <<'PY' > out/numbers.log 2>&1
import glob, json, re
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twenty-one": 21}
readme = open("README.md").read()
human = json.load(open("out/human.rep.json"))
types = set()
for path in glob.glob("out/*.rep.json"):
    rep = json.load(open(path))
    for r in ([rep["problem"]] if rep["problem"] else []) + rep["refusals"]:
        types.add(r["type"])
kinds = set()
for path in glob.glob("out/*.jsonl"):
    kinds |= {json.loads(l)["kind"] for l in open(path)}
prov = open("provenance.json").read()
# Both files, so a count that drifts in one of them is caught in the file it
# drifted in rather than in the one that still happens to be right.
CLAIMS = [("README.md", readme, r"The ([\w-]+) kinds these runs write", len(kinds), "record kinds"),
          ("README.md", readme, r"([A-Za-z-]+) types, each measured", len(types), "failure types"),
          ("README.md", readme, r"The same ([a-z-]+) steps commit either way",
           human["steps_committed"], "steps"),
          ("README.md", readme, r"([A-Za-z-]+) rungs reported separately",
           len(human["success_ladder"]), "ladder rungs"),
          ("provenance.json", prov, r"the ([\w-]+) kinds these runs write", len(kinds),
           "record kinds"),
          ("provenance.json", prov, r"exactly ([a-z-]+) failure types are produced", len(types),
           "failure types"),
          ("provenance.json", prov, r"- ([\w-]+) record kinds", len(kinds), "record kinds"),
          ("provenance.json", prov, r"record kinds, ([\w-]+) failure types", len(types),
           "failure types"),
          ("provenance.json", prov, r"failure types, ([\w-]+) committed steps",
           human["steps_committed"], "steps"),
          ("provenance.json", prov, r"committed steps, ([\w-]+) ladder rungs",
           len(human["success_ladder"]), "ladder rungs")]
for path, text, pattern, measured, what in CLAIMS:
    m = re.search(pattern, text)
    assert m, (path, pattern)
    word = m.group(1).lower()
    assert WORDS.get(word) == measured, \
        f"{path}: {what}: it says {word!r}, the artifacts hold {measured}"
print(len(CLAIMS), "counts written in words across README.md and provenance.json, each equal "
      "to the number read back out of the artifacts it describes")
PY
check "every count either file spells out equals the one read back out of the artifacts" "$?" "0"
py <<'PY' > out/onepath.log 2>&1
import re
runner = open("run.py").read()
assert runner.count("self.ledger.append(") == 1, "a second emission path onto the ledger"
assert runner.count("def record(") == 1
assert runner.count("self.ledger.") == 1, \
    "the ledger is reached outside the one record() call"
loader = open("harnesses.py").read()
assert "def _load" not in loader and "sys.modules" not in loader, "a second loader lives here"
assert 'examples", "run", "harnesses.py"' in loader
print("one emission path onto the ledger, and no loader of our own beside the one we import")
PY
check "one path onto the ledger, and no copy of the loader this area imports" "$?" "0"
py <<'PY' > out/runsteps.log 2>&1
import json, re, subprocess, sys, os
REPO = os.path.abspath("../..")
rows = []
text = open("README.md").read()
table = text[text.index("### Run steps"):text.index("### Adapters")]
for line in table.splitlines():
    m = re.match(r"\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line)
    if m:
        rows.append((int(m.group(1)), m.group(2), m.group(3)))
assert len(rows) == 6, rows
floor = int(re.search(r"^FLOOR=(\d+)$", open("test.sh").read(), re.M).group(1))
assert rows[0][2] == f"passed {floor}, failed 0", (rows[0][2], floor)
for n, cmd, last in rows[1:]:
    out = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=REPO)
    got = (out.stdout + out.stderr).strip().splitlines()[-1]
    assert got == last, f"step {n}: printed {got!r}, README promises {last!r}"
print(len(rows), "printed commands; step 1's promise equals FLOOR and steps 2-6 were run "
      "as printed and matched")
PY
check "the README's commands run as printed and print the line it promises" "$?" "0"
py <<'PY' > out/argparse.log 2>&1
import re, subprocess, sys
usage = subprocess.run([sys.executable, "run.py", "--help"], capture_output=True, text=True).stdout
real = set(re.findall(r"^  (--[a-z-]+)", usage, re.M))
spans = re.findall(r"`([^`]+)`", open("README.md").read())
named = {f for span in spans for f in re.findall(r"(?<![-\w])(--[a-z][a-z-]*)", span)}
named |= {"--help"}
missing = named - real - {"--help"}
assert not missing, f"the README names flags run.py does not have: {sorted(missing)}"
unnamed = real - named - {"--help"}
assert not unnamed, f"run.py has flags the README never names: {sorted(unnamed)}"
print(len(real), "flags in the runner's own argparse, and the README names exactly those")
PY
check "every flag the README names exists, and every flag the runner has is named" "$?" "0"
py <<'PY' > out/nolib.log 2>&1
import json
for d in ("human", "event", "schedule", "external"):
    blob = json.dumps(json.load(open(f"entries/{d}.json"))).lower()
    for banned in ("import ", "sdk", "client_library", "adapter", "executor", "register"):
        assert banned not in blob, (d, banned)
doc = json.dumps(json.load(open("pipelines/release-coupon-fix.json"))).lower()
for banned in ("import ", "sdk", "adapter", "executor", "queue", "worker"):
    assert banned not in doc, banned
print("five documents a caller writes, and none of them names a library, an adapter or a queue")
PY
check "a caller needs no client library this repository wrote" "$?" "0"
python3 run.py --verify-ledger --ledger out/human.jsonl > out/verify.log 2>&1
check "the ledger chain verifies" "$?" "0"
sed '3s/"budget_remaining_micros": [0-9]*/"budget_remaining_micros": 1/' out/human.jsonl > out/tampered.jsonl
python3 run.py --verify-ledger --ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a one-character edit to the ledger is detected" "$?" "2"
py <<'PY' > out/floor.log 2>&1
import json, re
declared = json.load(open("provenance.json"))["visible_checks_counted"]
floor = int(re.search(r"^FLOOR=(\d+)$", open("test.sh").read(), re.M).group(1))
assert declared == floor, (declared, floor)
gate = open("test.sh").read()
assert '[ "$PASS" -ge "$FLOOR" ]' in gate and '[ "$FAIL" -eq 0 ]' in gate
print("FLOOR", floor, "== provenance.visible_checks_counted", declared,
      "and the gate has both halves")
PY
check "the floor, the recorded count and the two-halved gate agree" "$?" "0"
py <<'PY' > out/namecheck.log 2>&1
import os, re
# The claim is about this whole directory and everything a run of it has written
# by now, not about one log. Word-anchored, and the lines carrying the list
# itself are marked and skipped.
NAMES = (r"\btemporal\b|\brestate\b|\bdbos\b|\binngest\b|\bcadence\b|\bwindmill\b|"
         r"\bopa\b|\brego\b|\bcedar\b|\bfirecracker\b|\bgvisor\b|\bkata\b|\bdocker\b|"
         r"\bkubernetes\b|\bopenai\b|\banthropic\b|\bazure\b|\baws\b|\bgoogle\b|"
         r"\blitellm\b|\bjaeger\b|\bdatadog\b|\bprometheus\b|\bpostgres\b|\bredis\b|"
         r"\bsqlite\b|\bgithub\b|\bstyra\b|\bopenfga\b|\blangfuse\b")   # namecheck
MARK = "namecheck"                                                       # namecheck
name_re = re.compile(NAMES, re.I)
sources, artifacts = [], []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for name in sorted(files):
        path = os.path.join(root, name)
        (artifacts if path.startswith("./out/") else sources).append(path)
assert len(sources) >= 12 and len(artifacts) >= 100, (len(sources), len(artifacts))
hits = []
for path in sources + artifacts:
    if path.endswith((".pyc", ".png")):
        continue
    for i, line in enumerate(open(path, errors="replace").read().splitlines()):
        if MARK in line:
            continue
        if name_re.search(line):
            hits.append(f"{path}:{i + 1}: {line.strip()[:90]}")
assert not hits, "\n".join(hits[:10])
print(len(sources), "source files and", len(artifacts),
      "artifacts scanned word-anchored against", len(NAMES.split("|")),
      "names; no product named anywhere")
PY
check "no product is named in any source file or any artifact of this example" "$?" "0"
py <<'PY' > out/grader-hidden.log 2>&1
import os
# Section 4 makes this claim over the tree as it stood then; this is the same
# claim over the finished one, every state directory of every run included.
MEMBERS = ("must_contain", "required_steps", "required_tools", "answer_contains")
scanned, hits = 0, []
for root, dirs, files in os.walk("out"):
    for name in sorted(files):
        path = os.path.join(root, name)
        text = open(path, errors="replace").read()
        scanned += 1
        hits += [f"{path}: {m}" for m in MEMBERS if m in text]
assert not hits, "; ".join(hits[:5])
assert scanned >= 200, scanned
print("no criterion or rubric member name in any of", scanned,
      "artifacts this suite wrote, state directories included")
PY
check "no criterion or rubric member name reaches any artifact of the finished suite" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
