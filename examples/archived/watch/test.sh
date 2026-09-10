#!/usr/bin/env bash
# The visible check for examples/watch. Everything here is measured, not claimed.
#
# It prints `passed N, failed 0` with N counting checks that actually ran, and
# the gate at the bottom has two halves: no failure, and a floor under the count.
# A gutted copy of this file counts zero and is refused at the floor rather than
# exiting 0 (`F-a7-03` "A deterministic gate can be structurally green and mean
# nothing"). FLOOR moves with provenance.json's visible_checks_counted, and a
# check below asserts the two agree.
#
# Every extension point in README section 6 is proved here by a differential run:
# the same door twice, one declared value changed, the two records asserted
# different in the named way. A green run at the default value proves the default
# path and nothing else.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=73
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }

rm -rf out && mkdir -p out

echo "1. four doors, one unit, one declared observation each"
for d in human event schedule external; do
  python3 run.py --entry "entries/$d.json" --ledger "out/$d.jsonl" --report "out/$d.json" \
    > "out/$d.log" 2>&1
  check "$d exits 0" "$?" "0"
  grep -q "^completed:" "out/$d.log" && ok "$d reached completed" || bad "$d did not complete"
done
py <<'PY' > out/doors.log 2>&1
import json, sys
sys.path.insert(0, "../end-to-end")
from run import validate                      # one validator, two document shapes
entry_schema = json.load(open("../end-to-end/schemas/entry.schema.json"))
watch_schema = json.load(open("schemas/watch.schema.json"))
errs = 0
for d in ("human", "event", "schedule", "external"):
    doc = json.load(open(f"entries/{d}.json"))
    errs += len(validate(doc, entry_schema)) + len(validate(doc["payload"]["watch"], watch_schema))
assert errs == 0, f"{errs} validation errors across the four documents"
print("four entry documents and four watch declarations validate")
PY
check "four documents validate with the reference example's own validator" "$?" "0"
py <<'PY' > out/one-unit.log 2>&1
import json
doors = ("human", "event", "schedule", "external")
rep = {d: json.load(open(f"out/{d}.json")) for d in doors}
led = {d: [json.loads(l) for l in open(f"out/{d}.jsonl")] for d in doors}
units = {r["unit"] for rows in led.values() for r in rows if "unit" in r}
refs = {json.load(open(f"entries/{d}.json"))["intent"]["workflow_ref"] for d in doors}
assert len(refs) == 1, f"the four doors name {len(refs)} task specifications: {sorted(refs)}"
assert units == {json.load(open(next(iter(refs))))["unit"]}, (units, refs)
assert len({r["run_id"] for rows in led.values() for r in rows}) == 4, "four doors did not carry four run ids"
assert len({r["correlation_id"] for rows in led.values() for r in rows}) == 4, "four correlation ids expected"
assert len({r["actor"] for rows in led.values() for r in rows}) == 4, "four actors expected"
missing = sum(v["missing_run_id"] + v["missing_correlation_id"]
              for d in doors for v in rep[d]["audit"]["per_kind"].values())
assert missing == 0, f"{missing} signals carry no run id or no correlation id"
groups = {d: rep[d]["audit"]["signal_groups"] for d in doors}
assert set(groups.values()) == {1}, groups
print("one unit declaration, four actors, four run ids, four correlation ids, one group each")
PY
check "one unit through four doors, every signal stamped, one group per run" "$?" "0"

echo "1b. the unit is the one the envelope points at, and only its declared steps are observed"
py <<'PY2'
import json
doc = json.load(open("units/observe-checkout-fault.json"))
doc["attempt_class"] = "f-grunt"                 # a free class: a different price and a different span
json.dump(doc, open("out/unit-free.json", "w"))
entry = json.load(open("entries/human.json"))
entry["intent"]["workflow_ref"] = "out/unit-free.json"
entry["correlation"] = {"run_id": "run-watch-free-0001", "correlation_id": "corr-watch-free-0001", "depth": 0}
json.dump(entry, open("out/entry-free.json", "w"))
short = json.load(open("units/observe-checkout-fault.json"))
short["observation"]["step_kinds"] = ["entry", "dispatch", "model"]
json.dump(short, open("out/unit-short.json", "w"))
PY2
python3 run.py --entry out/entry-free.json --ledger out/free.jsonl --report out/free.json > out/free.log 2>&1
check "the unit named by intent.workflow_ref runs, with no --unit flag" "$?" "0"
py <<'PY2' > out/workflow-ref.log 2>&1
import json
free, paid = (json.load(open(f"out/{n}.json")) for n in ("free", "human"))
rows = [json.loads(l) for l in open("out/free.jsonl")]
sub = [r for r in rows if r["kind"] == "unit-submitted"][0]
assert sub["workflow_ref"] == "out/unit-free.json" and sub["attempt_class"] == "f-grunt", sub
assert sub["summary"] == json.load(open("entries/human.json"))["intent"]["summary"], sub["summary"]
klass = lambda rep: [s["unit"]["attributes"]["gen_ai.request.model_class"]
                     for s in rep["audit"]["signals"]
                     if s["kind"] == "span" and "gen_ai.request.model_class" in s["unit"]["attributes"]]
assert klass(free) == ["f-grunt"] and klass(paid) == ["i-fast"], (klass(free), klass(paid))
print("two workflow_refs, two attempt classes on the wire:", klass(paid), klass(free))
PY2
check "changing intent.workflow_ref changes the class the model span carries" "$?" "0"
python3 run.py --entry entries/human.json --unit out/unit-short.json --ledger out/short.jsonl > out/short.log 2>&1
check "a step the unit did not declare is refused, not observed" "$?" "1"
grep -q "'tool' is not one of them" out/short.log && ok "the undeclared step kind is named"   || bad "the refusal does not name the kind"

echo "1c. every leaf a second legal value has to move: the receipt carries what was declared"
py <<'PY2'
import json
base = json.load(open("units/observe-checkout-fault.json"))
def variant(name, **patch):
    doc = json.loads(json.dumps(base))
    for section, fields in patch.items():
        doc[section].update(fields)
    json.dump(doc, open(f"out/unit-{name}.json", "w"))
# egress_allowlist alone: egress is `allowlist` in both arms, only the list moves
variant("allow1", isolation={"egress": "allowlist", "egress_allowlist": ["telemetry.example.invalid"]})
variant("allow2", isolation={"egress": "allowlist",
                             "egress_allowlist": ["telemetry.example.invalid", "notes.example.invalid"]})
variant("allow0", isolation={"egress": "allowlist", "egress_allowlist": []})
variant("grace",  ceilings={"cancel_grace_s": 0.01})    # below the adapter's own cancel floor
variant("grace2", ceilings={"cancel_grace_s": 1.25})    # a second legal grace, over the same floor
variant("wall",   ceilings={"wall_seconds": 9.0})       # a second legal ceiling, never reached
variant("calls",  tools={"ceiling_calls": 3})           # a second legal ceiling, never crossed
variant("tiny",   ceilings={"wall_seconds": 0.001})     # the same ceiling at its threshold
variant("zero",   tools={"ceiling_calls": 0})           # the same ceiling at its threshold
variant("server", tools={"server_ref": "tools://second"})
PY2
for v in allow1 allow2 server grace2 wall calls; do
  python3 run.py --entry entries/human.json --unit "out/unit-$v.json" --ledger "out/$v.jsonl" \
    --report "out/$v.json" > "out/$v.log" 2>&1
done
py <<'PY2' > out/allowlist.log 2>&1
import json
def admitted(name):
    return [json.loads(l) for l in open(f"out/{name}.jsonl") if json.loads(l)["kind"] == "cell-admitted"][0]
one, two, base = admitted("allow1"), admitted("allow2"), admitted("human")
assert one["egress"] == two["egress"] == "allowlist", (one["egress"], two["egress"])
assert one["egress_allowlist"] != two["egress_allowlist"], one["egress_allowlist"]
assert len(two["egress_allowlist"]) - len(one["egress_allowlist"]) == 1, two["egress_allowlist"]
assert base["egress_allowlist"] == [] and base["egress"] == "none", base
print("one field changed:", one["egress_allowlist"], "->", two["egress_allowlist"])
PY2
check "isolation.egress_allowlist alone moves the admitted record" "$?" "0"
python3 run.py --entry entries/human.json --unit out/unit-allow0.json --ledger out/allow0.jsonl \
  --report out/allow0.json > out/allow0.log 2>&1
check "an allowlist that lists nothing is refused, not admitted as an open unit" "$?" "2"
grep -q "empty list is a malformed declaration" out/allow0.log \
  && ok "the refusal names what is wrong with the declaration" || bad "the refusal is untyped prose"
grep -q "cell-admitted" out/allow0.jsonl && bad "a cell was admitted on a malformed declaration" \
  || ok "no cell was admitted on a malformed declaration"
python3 run.py --entry entries/human.json --unit out/unit-grace.json --ledger out/grace.jsonl \
  --report out/grace.json > out/grace.log 2>&1
check "a cancel grace below the runtime's own floor is refused at the turn" "$?" "2"
grep -q "below this adapter's cancel floor" out/grace.log && ok "the floor the host enforces is named" \
  || bad "the refusal does not name the floor"
py <<'PY2' > out/grace-window.log 2>&1
import json
# A refusal proves the illegal value. Two legal values have to move the record
# too, or the field is decoration that happens to have a validator: the accepted
# window and the floor it was accepted against are on the dispatch step, so 0.5s
# and 1.25s are two different runs and not the same run relabelled.
def window(name):
    rep = json.load(open(f"out/{name}.json"))
    attrs = [s["unit"]["attributes"] for s in rep["audit"]["signals"]
             if s["kind"] == "span" and "cancel_grace_s" in s["unit"]["attributes"]][0]
    return attrs["cancel_grace_s"], attrs["cancel_floor_s"]
one, two = window("human"), window("grace2")
assert one[0] != two[0], (one, two)
assert one[1] == two[1], f"the floor is the host's, not the caller's: {one[1]} vs {two[1]}"
assert one[0] >= one[1] and two[0] >= two[1], (one, two)
# and in prose on the log record, not only as a number on a span
bodies = [s["unit"]["body"] for s in json.load(open("out/grace2.json"))["audit"]["signals"]
          if s["kind"] == "log_record" and "cancel window" in s["unit"].get("body", "")]
assert bodies and f"{two[0]}s cancel window" in bodies[0], bodies
print("one field changed:", one, "->", two)
PY2
check "a second legal cancel grace moves the window on the record" "$?" "0"
py <<'PY2' > out/grace-receipt.log 2>&1
import json
def keys(name):
    return [r["attributes"] for r in (json.loads(l) for l in open(f"out/{name}.jsonl"))
            if r["kind"] == "step-observed" and r["step"] == "dispatch"][0]
for name in ("human", "grace2"):
    assert "cancel_grace_s" in keys(name) and "cancel_floor_s" in keys(name), (name, keys(name))
print("the accepted window is on the receipt as well as on the wire:", keys("human"))
PY2
check "the accepted cancel window reaches the ledger, not only the report" "$?" "0"
py <<'PY2' > out/ceilings.log 2>&1
import json
# Both of these are enforced at a threshold, so a differential that crosses the
# threshold proves the enforcement and says nothing about a run that stayed
# inside it. A run that stayed inside has to carry the ceiling it stayed inside.
def admitted(name):
    return [json.loads(l) for l in open(f"out/{name}.jsonl") if json.loads(l)["kind"] == "cell-admitted"][0]
base, wide = admitted("human"), admitted("wall")
assert base["wall_ceiling_s"] != wide["wall_ceiling_s"], (base, wide)
def tool_span(name):
    rep = json.load(open(f"out/{name}.json"))
    return [s["unit"]["attributes"] for s in rep["audit"]["signals"]
            if s["kind"] == "span" and "calls_permitted" in s["unit"]["attributes"]][0]
one, few = tool_span("human"), tool_span("calls")
assert one["calls_permitted"] != few["calls_permitted"], (one, few)
assert one["calls_attempted"] == few["calls_attempted"], "the same unit made the same calls"
assert one["calls_attempted"] <= few["calls_permitted"], (one, few)
print("two ceilings neither run reached, both on the record:",
      base["wall_ceiling_s"], "->", wide["wall_ceiling_s"], "and",
      one["calls_permitted"], "->", few["calls_permitted"])
PY2
check "a ceiling a run stayed inside is on the record, not only at the threshold" "$?" "0"
python3 run.py --entry entries/human.json --unit out/unit-tiny.json --ledger out/tiny.jsonl \
  --report out/tiny.json > out/tiny.log 2>&1
check "the wall ceiling at its threshold ends the unit at the boundary" "$?" "3"
grep -q "stop reason terminated" out/tiny.log && ok "the boundary, not the unit, reports the stop reason" \
  || bad "the terminated stop reason is not on the caller's last line"
python3 run.py --entry entries/human.json --unit out/unit-zero.json --ledger out/zero.jsonl \
  --report out/zero.json > out/zero.log 2>&1
check "a tool ceiling of zero refuses at the point of call and does not end the run" "$?" "0"
py <<'PY2' > out/callceiling.log 2>&1
import json
led = [json.loads(l) for l in open("out/zero.jsonl")]
refusals = [r for r in led if r["kind"] == "refusal" and r["step"] == "tool"]
types = [r["problem_type"] for r in refusals]
assert any(t.endswith("budget-exhausted") for t in types), types
assert all(r["ends_unit"] is False for r in refusals), refusals
base = [r for r in (json.loads(l) for l in open("out/human.jsonl"))
        if r["kind"] == "refusal" and r["step"] == "tool"]
assert len(refusals) == len(base) + 1, (len(refusals), len(base))
print("the declared call ceiling raises one more typed refusal and the unit still completes:", types)
PY2
check "the tool ceiling is enforced at the point of call, as a typed refusal" "$?" "0"
py <<'PY2' > out/server-ref.log 2>&1
import json
def binding(name):
    rep = json.load(open(f"out/{name}.json"))
    return [s["unit"]["attributes"]["tool_binding"] for s in rep["audit"]["signals"]
            if s["kind"] == "span" and "tool_binding" in s["unit"]["attributes"]][0]
a, b = binding("human"), binding("server")
assert a != b, (a, b)
assert a.startswith("bind-") and b.startswith("bind-"), (a, b)
print("tools.server_ref moves the binding the capability derived:", a, "->", b)
PY2
check "tools.server_ref moves the binding handle on the wire" "$?" "0"

echo "2. the three emission kinds are bound to one run and to one trace"
py <<'PY' > out/kinds.log 2>&1
import json
rep = json.load(open("out/human.json"))
per = rep["audit"]["per_kind"]
for kind in ("span", "metric", "log_record", "problem_object"):
    assert per[kind]["read_back"] > 0, f"{kind}: nothing was read back off the query surface"
assert rep["audit"]["problem_objects_without_a_span_trace"] == 0, rep["audit"]
print({k: v["read_back"] for k, v in per.items()})
PY
check "spans, metrics, log records and problem objects all read back, all bound" "$?" "0"
py <<'PY' > out/parentage.log 2>&1
import json
rep = json.load(open("out/human.json"))
a = rep["audit"]
spans = a["per_kind"]["span"]["read_back"]
assert a["distinct_trace_ids"] == spans > 1, (a["distinct_trace_ids"], spans)
assert a["run_id_groups"] == 1 and a["spans_missing_run_id"] == 0, a
assert not any("parent" in s["unit"] for s in a["signals"]), "a span carried a parent field"
print(f"{spans} spans, {a['distinct_trace_ids']} minted traces, 1 group on run.id")
PY
check "one run reassembles from N minted traces by grouping, never by parentage" "$?" "0"
py <<'PY' > out/resume.log 2>&1
import json
rep = json.load(open("out/external.json"))
a = rep["audit"]
assert a["levels_covered"] == 2, f"a parked and resumed run covered {a['levels_covered']} level(s)"
assert a["run_id_groups"] == 1 and a["signal_groups"] == 1, a
d = rep["outcome"]["decision"]
assert d["resumed_on_same_correlation"] is True, d
assert d["decision"] == "approve" and d["applied"] is True, d
assert d["second_decision_refused"].endswith("idempotency-conflict"), d
assert a["per_kind"]["problem_object"]["read_back"] == 2, a["per_kind"]
assert rep["events_on_the_stream"].count("human.refused") == 1, rep["events_on_the_stream"]
print("resumed at depth 1 on the run's own correlation id, one group; the second decision refused 409")
PY
check "a run parked on a person and resumed still joins its predecessors" "$?" "0"
python3 run.py --entry entries/human.json --pause --ledger out/pause.jsonl \
  --report out/pause.json > out/pause.log 2>&1
python3 run.py --entry entries/external.json --no-pause --ledger out/nopause.jsonl \
  --report out/nopause.json > out/nopause.log 2>&1
py <<'PY3' > out/pause-diff.log 2>&1
import json
# the same door twice, one declared value changed: pause_for_decision, and nothing else
for door, on, off in (("human", "pause", "human"), ("external", "external", "nopause")):
    yes, no = (json.load(open(f"out/{n}.json")) for n in (on, off))
    assert yes["watch"]["pause_for_decision"] is True and no["watch"]["pause_for_decision"] is False
    assert yes["audit"]["levels_covered"] == 2 and no["audit"]["levels_covered"] == 1, \
        (door, yes["audit"]["levels_covered"], no["audit"]["levels_covered"])
    assert "human.ask" in yes["events_on_the_stream"] and "human.ask" not in no["events_on_the_stream"]
    assert yes["outcome"]["decision"] and no["outcome"]["decision"] is None, door
    assert yes["audit"]["run_id_groups"] == no["audit"]["run_id_groups"] == 1
    assert len(yes["events_on_the_stream"]) - len(no["events_on_the_stream"]) == 3, \
        (door, yes["events_on_the_stream"], no["events_on_the_stream"])
print("both doors, one field: levels 2 -> 1, the ask on and off the stream, the decision row and none")
PY3
check "pause_for_decision true vs false, on both doors, nothing else changed" "$?" "0"
python3 run.py --entry entries/external.json --mint-on-resume --ledger out/mint.jsonl \
  --report out/mint.json > out/mint.log 2>&1
py <<'PY' > out/mint2.log 2>&1
import json
one, two = (json.load(open(f"out/{n}.json"))["audit"] for n in ("external", "mint"))
assert one["run_id_groups"] == 1 and two["run_id_groups"] == 0, (one["run_id_groups"], two["run_id_groups"])
assert two["per_kind"]["span"]["read_back"] == one["per_kind"]["span"]["read_back"] - 1, two["per_kind"]
print("re-stamped:", one["run_id_groups"], "minted at the child boundary:", two["run_id_groups"])
PY
check "deliberate breakage: a resume that mints its own run id leaves the run in pieces" "$?" "0"

echo "3. detail: the whole unit as one operation, or one per step"
python3 run.py --entry entries/human.json --detail unit --ledger out/d-unit.jsonl \
  --report out/d-unit.json > out/d-unit.log 2>&1
py <<'PY' > out/detail.log 2>&1
import json
steps, unit = (json.load(open(f"out/{n}.json")) for n in ("human", "d-unit"))
s, u = steps["audit"]["per_kind"]["span"]["read_back"], unit["audit"]["per_kind"]["span"]["read_back"]
assert (s, u) == (4, 1), f"detail steps gave {s} spans and detail unit gave {u}"
assert steps["audit"]["distinct_trace_ids"] == 4 and unit["audit"]["distinct_trace_ids"] == 1
kinds = {sig["unit"]["attributes"].get("operation.unmapped_kind")
         for sig in steps["audit"]["signals"] if sig["kind"] == "span"}
assert "model" in kinds, kinds
assert steps["unmapped_operations"] == ["model"] and unit["unmapped_operations"] == []
print("steps:", s, "spans; unit:", u, "span")
PY
check "detail steps gives one operation per step, detail unit gives one for the unit" "$?" "0"
py <<'PY' > out/mapping.log 2>&1
import json, sys
sys.path.insert(0, ".")
import harnesses
oi, Adapter, _ = harnesses.observability("dryrun")
mapping = Adapter().describe_mapping()
rep = json.load(open("out/human.json"))
emitted = {s["unit"]["operation"] for s in rep["audit"]["signals"] if s["kind"] == "span"}
assert emitted <= set(mapping.operations.values()), (emitted, mapping.operations)
assert "model" not in mapping.operations, "the mapping now carries a model-call operation; update gap G8"
assert not hasattr(mapping, "instruments"), "the mapping description now publishes instruments; update gap G8"
assert rep["instruments_published_by_the_mapping"] is False
print("operations on the wire", sorted(emitted), "from", mapping.version)
PY
check "operation names are read from the published mapping, never transcribed" "$?" "0"

echo "4. sampling: declared by the caller, and it cannot decline a retention"
python3 run.py --entry entries/human.json --head-percent 0 --ledger out/h0.jsonl \
  --report out/h0.json > out/h0.log 2>&1
py <<'PY' > out/sampling.log 2>&1
import json
full, none = (json.load(open(f"out/{n}.json")) for n in ("human", "h0"))
a, b = full["audit"], none["audit"]
assert (a["per_kind"]["span"]["read_back"], b["per_kind"]["span"]["read_back"]) == (4, 0)
assert (full["sampled_out"], none["sampled_out"]) == (0, 4)
assert a["metric_cost_micros_total"] == b["metric_cost_micros_total"] > 0, \
    (a["metric_cost_micros_total"], b["metric_cost_micros_total"])
assert a["per_kind"]["problem_object"]["read_back"] == b["per_kind"]["problem_object"]["read_back"] == 1
print("spans 4 -> 0; cost on metrics", a["metric_cost_micros_total"], "unchanged")
PY
check "head_percent 100 vs 0: spans go, cost and refusals stay" "$?" "0"
py <<'PY' > out/orphan.log 2>&1
import json
full, none = (json.load(open(f"out/{n}.json"))["audit"] for n in ("human", "h0"))
assert full["problem_objects_without_a_span_trace"] == 0
assert none["problem_objects_without_a_span_trace"] == 1, none
print("sampling the spans away orphans the retained problem object's trace id - gap G3")
PY
check "a retained failure keeps its trace id and loses the span it named" "$?" "0"
py <<'PY'
import json
doc = json.load(open("entries/human.json"))
doc["payload"]["watch"]["sampling"]["retain_errors"] = False
json.dump(doc, open("out/decline.json", "w"))
PY
python3 run.py --entry out/decline.json --ledger out/decline.jsonl > out/decline.log 2>&1
check "a caller declaring retain_errors false exits 2" "$?" "2"
grep -q "document-invalid" out/decline.log && ok "the guarantee is refused at 422, not honoured" \
  || bad "the declaration was accepted"
grep -q "retain_errors' is not allowed" out/decline.log && ok "the refused member is named" \
  || bad "the refusal does not name the member"
python3 run.py --entry entries/human.json --budget-micros 1000 --head-percent 0 \
  --ledger out/low0.jsonl --report out/low0.json > out/low0.log 2>&1
py <<'PY' > out/retain.log 2>&1
import json
rep = json.load(open("out/low0.json"))
assert rep["status"] == "rejected"
assert rep["audit"]["per_kind"]["span"]["read_back"] == 1, rep["audit"]["per_kind"]
print("a rejected run at head_percent 0 still exports its span: retain_always names outcome:error")
PY
check "retain_always outranks the caller's sampling for an error outcome" "$?" "0"

echo "5. redaction: applied on the shared path, widened by the caller, never narrowed"
python3 run.py --entry entries/human.json --redact-additional task_summary \
  --ledger out/red.jsonl --report out/red.json > out/red.log 2>&1
python3 run.py --entry entries/human.json --redact-additional "" \
  --ledger out/nored.jsonl --report out/nored.json > out/nored.log 2>&1
py <<'PY' > out/redact.log 2>&1
import json
def attrs(name):
    rep = json.load(open(f"out/{name}.json"))
    out = {}
    for sig in rep["audit"]["signals"]:
        out.update(sig["unit"].get("attributes", {}))
    return rep, out
wide_rep, wide = attrs("red")
narrow_rep, narrow = attrs("nored")
assert wide_rep["redact_set"] == ["completion", "prompt", "task_summary"], wide_rep["redact_set"]
assert narrow_rep["redact_set"] == ["completion", "prompt"], narrow_rep["redact_set"]
assert wide["task_summary"] == "[redacted]", wide["task_summary"]
assert narrow["task_summary"] != "[redacted]", "the widened set did not change anything"
for name in ("red", "nored", "human", "event", "schedule", "external"):
    _, seen = attrs(name)
    for key in ("prompt", "completion"):
        if key in seen:
            assert seen[key] == "[redacted]", f"{name}: {key} reached the wire as {seen[key]!r}"
print("widened:", wide_rep["redact_set"], "narrowed to:", narrow_rep["redact_set"])
PY
check "redact_additional widens the set and cannot narrow the unit's own" "$?" "0"
py <<'PY' > out/leak.log 2>&1
import json
rep = json.load(open("out/nored.json"))
prompt = "Read the retained window"          # the unit's task text, which the prompt embeds
hits = [s for s in rep["audit"]["signals"] if prompt in json.dumps(s)]
assert not hits, f"{len(hits)} signal(s) carry the prompt text"
subject = json.load(open("entries/human.json"))["payload"]["subject"]
carried = [s for s in rep["audit"]["signals"] if subject in json.dumps(s)]
assert carried, "expected the same text under an unredacted key - gap G5 would be closed"
print(f"prompt text in 0 signals; the same content under task_summary in {len(carried)} - gap G5")
PY
check "the prompt attribute never reaches the wire; the same text under another key does" "$?" "0"

echo "6. the surface the caller declared, and the position it asked for"
python3 run.py --entry entries/human.json --surface poll --ledger out/poll.jsonl \
  --report out/poll.json > out/poll.log 2>&1
py <<'PY' > out/surface.log 2>&1
import json
stream, poll = (json.load(open(f"out/{n}.json")) for n in ("human", "poll"))
assert stream["binding"]["delivery_model"] == "stream", stream["binding"]
assert poll["binding"]["delivery_model"] == "request_response", poll["binding"]
assert stream["binding"]["replayable_from_position"] is True
assert poll["binding"]["replayable_from_position"] is False
assert len(stream["events_rendered"]) == 8 and len(poll["events_rendered"]) == 0, \
    (stream["events_rendered"], poll["events_rendered"])
assert stream["events_on_the_stream"] == poll["events_on_the_stream"], "the store differed by surface"
print("one store, two surfaces:", len(stream["events_rendered"]), "vs", len(poll["events_rendered"]),
      "of", len(stream["events_on_the_stream"]), "events rendered")
PY
check "the declared surface changes what is rendered, not what the platform kept" "$?" "0"
python3 run.py --entry entries/external.json --since 0 --ledger out/since0.jsonl \
  --report out/since0.json > out/since0.log 2>&1
py <<'PY' > out/since.log 2>&1
import json
zero, two = (json.load(open(f"out/{n}.json")) for n in ("since0", "external"))
assert two["watch"]["since"] == 2 and zero["watch"]["since"] == 0
a, b = zero["events_rendered"], two["events_rendered"]
assert len(a) - len(b) == 2, (len(a), len(b))
assert a[2:] == b and a[-1] == b[-1] == "run.finished", (a, b)
print("since 0 renders", len(a), "events; since 2 renders", len(b), "ending at the same event")
PY
check "since replays from a position: exactly the events after it" "$?" "0"
python3 run.py --entry entries/human.json --surface poll --since 2 --ledger out/ps.jsonl \
  --report out/ps.json > out/ps.log 2>&1
check "a position on a surface that cannot replay still exits 0" "$?" "0"
py <<'PY' > out/refuse.log 2>&1
import json
rep = json.load(open("out/ps.json"))
assert rep["status"] == "completed", rep["status"]
assert rep["watch_problem"]["status"] == 422 and \
    rep["watch_problem"]["type"].endswith("document-invalid"), rep["watch_problem"]
assert rep["watch_problem"]["correlation_id"] == "corr-watch-human-0001"
print("the observation was refused with a type; the run was not")
PY
check "the refusal is typed, names the surface, and refuses the observation not the run" "$?" "0"

echo "7. the published task lifecycle, projected from the stream"
py <<'PY' > out/status.log 2>&1
import json, sys
sys.path.insert(0, ".")
from run import TASK_STATES, task_status
import harnesses
hi, hstore, _ = harnesses.human("second")
rep = json.load(open("out/external.json"))
seen = [r["state"] for r in (json.loads(l) for l in open("out/external.jsonl")) if "state" in r]
assert seen == ["submitted", "input-required", "working", "completed"], seen
assert set(seen) <= set(TASK_STATES), seen
assert rep["events_on_the_stream"].count("human.ask") == 1
print("lifecycle on the ledger:", seen)
PY
check "submitted, input-required, working, completed - adopted, never invented" "$?" "0"
python3 run.py --entry entries/human.json --cancel --ledger out/can.jsonl --report out/can.json \
  > out/can.log 2>&1
check "a cancelled turn does not report completed" "$?" "3"
py <<'PY' > out/cancel.log 2>&1
import json
rep = json.load(open("out/can.json"))
assert rep["status"] == "cancelled" and rep["outcome"]["stop_reason"] == "cancelled", rep["outcome"]
assert rep["events_on_the_stream"][-1] == "run.finished"
assert rep["outcome"]["frames"] < json.load(open("out/human.json"))["outcome"]["frames"]
neg = [s for s in rep["audit"]["signals"] if s["kind"] == "span"
       and s["unit"]["attributes"].get("cancellation_negotiated") is True]
assert neg, "cancellation was not negotiated at session open"
print("stop reason", rep["outcome"]["stop_reason"], "after", rep["outcome"]["frames"], "frames")
PY
check "cancellation is negotiated, enforced outside, and ends in a terminal state" "$?" "0"

echo "8. failures: three kinds, measured differently"
python3 run.py --entry entries/human.json --budget-micros 1000 --ledger out/low.jsonl \
  --report out/low.json > out/low.log 2>&1
check "a ceiling below the plan floor exits 2" "$?" "2"
grep -q "budget-exhausted" out/low.log && ok "typed as budget-exhausted (402)" || bad "not typed"
grep -q "cell-admitted" out/low.jsonl && bad "a cell was admitted anyway" || ok "no cell was admitted"
py <<'PY' > out/refusal-signal.log 2>&1
import json
rep = json.load(open("out/low.json"))
assert rep["audit"]["per_kind"]["problem_object"]["read_back"] == 1, rep["audit"]["per_kind"]
assert rep["events_on_the_stream"] == ["run.finished"], rep["events_on_the_stream"]
assert rep["registry_refused_members"] and "ceiling_micros" in rep["registry_refused_members"][0]
assert "3324" in rep["problem"]["detail"] and "ceiling_micros" not in rep["problem"]
print("the overage is in prose because the registry refused the member - gap G4")
PY
check "a refusal that ends the unit is a signal and an event, and loses its numbers" "$?" "0"
py <<'PY' > out/folded.log 2>&1
import json
rep = json.load(open("out/human.json"))
assert rep["status"] == "completed", "a refused tool call ended the unit"
assert rep["outcome"]["refused_rules"] == ["read-only-verdict"], rep["outcome"]["refused_rules"]
rows = [json.loads(l) for l in open("out/human.jsonl")]
refusals = [r for r in rows if r["kind"] == "refusal"]
assert len(refusals) == 1 and refusals[0]["ends_unit"] is False, refusals
assert refusals[0]["rule_id"] == "read-only-verdict", refusals[0]
assert rep["outcome"]["published"] > 3, "the catalogue was not larger than the declared surface"
print("one refusal folded into the record, rule", refusals[0]["rule_id"])
PY
check "a refused tool call is folded into the record and does not end the unit" "$?" "0"
py <<'PY'
import json
e = json.load(open("entries/human.json"))
del e["budget"]; e["kind"] = "telepathy"
json.dump(e, open("out/malformed.json", "w"))
PY
python3 run.py --entry out/malformed.json --ledger out/bad.jsonl --report out/bad.json > out/bad.log 2>&1
check "a malformed envelope exits 2" "$?" "2"
grep -q "document-invalid" out/bad.log && ok "typed as document-invalid (422)" || bad "not typed"
grep -q "missing required property 'budget'" out/bad.log && ok "names the missing field" || bad "field not named"
[ -f out/bad.jsonl ] && bad "an invalid envelope wrote to a ledger" || ok "no ledger for an invalid envelope"
[ -f out/bad.json ] && bad "an invalid envelope produced a report" \
  || ok "no telemetry for a failure that has no trusted correlation - gap G6"
py <<'PY' > out/vocab.log 2>&1
import json, sys
sys.path.insert(0, ".")
import harnesses
hi, _, _ = harnesses.human("dryrun")
seen = set()
for d in ("human", "event", "schedule", "external"):
    seen |= set(json.load(open(f"out/{d}.json"))["events_on_the_stream"])
assert seen <= set(hi.EVENT_TYPES), seen - set(hi.EVENT_TYPES)
assert len(seen) == 7, sorted(seen)
assert set(hi.EVENT_TYPES) - seen == {"ask.expired"}, set(hi.EVENT_TYPES) - seen
print("emitted", len(seen), "of", len(hi.EVENT_TYPES), "published event types")
PY
check "every event type emitted is one the capability publishes" "$?" "0"
py <<'PY4' > out/gate.log 2>&1
import json
# The vocabulary check lives in Observation.event, so every name on the stream has
# to have passed through it - including the two the surface puts there itself.
for d in ("human", "event", "schedule", "external"):
    rep = json.load(open(f"out/{d}.json"))
    gate, stream = rep["events_through_the_gate"], rep["events_on_the_stream"]
    assert gate == stream, (d, gate, stream)
ext = json.load(open("out/external.json"))["events_through_the_gate"]
assert {"human.ask", "human.decided"} <= set(ext), ext
print("the gate list and the stream agree on all four doors, ask and decided included")
PY4
check "every name on the stream passed the one vocabulary gate" "$?" "0"
py <<'PY4' > out/bypass.log 2>&1
import re
src = open("run.py").read()
writes = re.findall(r"^\s*(?:obs|self)\.events\.append\(", src, re.M)
assert len(writes) == 1, f"{len(writes)} writers to the event list; only Observation.event may write"
assert "def event(self, type_, at, data, emitted_by_surface" in src
print("one writer to the event list, inside the gate")
PY4
check "nothing appends to the event list around the gate" "$?" "0"

echo "9. the swap: a second telemetry backend, one call shape"
ADAPTER=second python3 run.py --entry entries/human.json --ledger out/second.jsonl \
  --report out/second.json > out/second.log 2>&1
check "the second backend exits 0" "$?" "0"
py <<'PY' > out/swap.log 2>&1
import json
one, two = (json.load(open(f"out/{n}.json")) for n in ("human", "second"))
assert one["audit"]["per_kind"] == two["audit"]["per_kind"], (one["audit"]["per_kind"], two["audit"]["per_kind"])
for field in ("run_id_groups", "distinct_trace_ids", "spans_missing_run_id",
              "spans_missing_correlation_id", "metric_cost_micros_total",
              "mapping_version_on_the_wire"):
    assert one["audit"][field] == two["audit"][field], (field, one["audit"][field], two["audit"][field])
assert one["events_on_the_stream"] == two["events_on_the_stream"]
print("six counters identical across two execution models")
PY
check "the same six counters across two backends, selected by configuration" "$?" "0"
py <<'PY' > out/marker.log 2>&1
import json, sys
sys.path.insert(0, ".")
import harnesses
names = []
for name in ("dryrun", "second"):
    _, Adapter, _ = harnesses.observability(name)
    a = Adapter()
    names.append((a.name, a.semantic_queries_supported))
assert names[0][0] != names[1][0], names
assert names[0][1] != names[1][1], "the pair does not differ on a declared capability"
print(names)
PY
check "the pair is two execution models, not one run twice" "$?" "0"
py <<'PY5' > out/product.log 2>&1
import os, re
# The rule is about the example, not about one door's stdout: everything a caller
# reads before running anything, everything the run writes, and the runner itself.
# A check cannot spell the names it forbids without failing itself, so the
# needles are assembled here rather than written down. Generic English words
# ("vendor", "product") are not needles: the rule is about naming a product.
NAMES = re.compile("|".join(["lang" + "fuse", "otlp collect" + "or", "open" + "ai",
                             "anthrop" + "ic", "firecrack" + "er", "goo" + "se",
                             "bedro" + "ck", "vert" + "ex ai"]), re.I)
surface = ["run.py", "harnesses.py", "test.sh", "provenance.json"]
for d in ("schemas", "units", "entries"):
    surface += [os.path.join(d, n) for n in sorted(os.listdir(d))]
surface += [os.path.join("out", n) for n in sorted(os.listdir("out"))
            if n.endswith((".log", ".json", ".jsonl"))]
hits = []
for path in surface:
    for i, line in enumerate(open(path, errors="replace"), 1):
        if NAMES.search(line):
            hits.append(f"{path}:{i}")
assert not hits, hits
assert len(surface) > 30, f"only {len(surface)} files were read; the walk found nothing to check"
print(f"no product or vendor name in {len(surface)} files of the runnable surface")
PY5
check "no product name anywhere the caller reads or the run writes" "$?" "0"

echo "10. the receipt"
python3 run.py --verify-ledger --ledger out/human.jsonl > out/verify.log 2>&1
check "the chain verifies" "$?" "0"
sed '3s/"cost_micros": [0-9]*/"cost_micros": 1/' out/human.jsonl > out/tampered.jsonl
python3 run.py --verify-ledger --ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a one-character edit is detected" "$?" "2"

echo "11. the example's own bookkeeping"
py <<'PY' > out/cites.log 2>&1
import json, os, re
ID = re.compile(r"REF-[A-Za-z0-9_./#,+-]+|\b[FTXER]-[a-z][a-z0-9]*-[a-z0-9-]+\b")
found = set()
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ("out", "__pycache__")]
    for name in files:
        if name.endswith((".md", ".py", ".sh", ".json")) and name != "provenance.json":
            found |= set(ID.findall(open(os.path.join(root, name)).read()))
cites = set(json.load(open("provenance.json"))["cites"])
# The area ships a second deliverable outside this directory - the proposed
# blueprint - and its rows carry ids too, so the both-directions claim has to
# cross the boundary the deliverable crosses.
BLUEPRINT = "REF-" + "docs/architecture/proposed/"        # written in parts: this file is walked too
outside = sorted(c[len("REF-"):].split("#")[0] for c in cites if c.startswith(BLUEPRINT))
assert outside, "the blueprint this area also ships is not cited"
for rel in outside:
    found |= set(ID.findall(open(os.path.join("..", "..", rel)).read()))
assert found == cites, (f"only in the files: {sorted(found - cites)}; "
                        f"only in provenance.cites: {sorted(cites - found)}")
print(len(cites), "ids, and the rows carry exactly those")
PY
check "provenance.cites is exactly the ids the rows carry, both directions" "$?" "0"
py <<'PY' > out/floor.log 2>&1
import json, re
declared = json.load(open("provenance.json"))["visible_checks_counted"]
floor = int(re.search(r"^FLOOR=(\d+)$", open("test.sh").read(), re.M).group(1))
assert declared == floor, (declared, floor)
print("FLOOR", floor, "== provenance.visible_checks_counted", declared)
PY
check "the floor and the recorded count of visible checks agree" "$?" "0"
py <<'PY' > out/proposed.log 2>&1
import json
doc = json.load(open("../../docs/architecture/proposed/watch.json"))
assert doc["area"] == "inside-unit observability"
assert len(doc["gaps"]) >= 6 and all(g["research_query"] and g["status"] == "unresearched"
                                     for g in doc["gaps"]), doc["gaps"]
assert all(r["origin"] == "proposed" for r in doc["state_types"] + doc["tool_entries"])
print(len(doc["gaps"]), "proposed blueprint gaps, every one with a research query")
PY
check "the proposed blueprint rows are proposed and every gap carries a query" "$?" "0"
py <<'PY6' > out/gapids.log 2>&1
import json, re
# The gap list is keyed by an id, not by a position in the table, because five
# other places point into it and a row inserted anywhere renumbered them all
# (two assertion messages here once pointed a maintainer at the wrong rows).
readme = open("README.md").read()
ids = re.findall(r"^\| (G\d+) \| ", readme, re.M)
assert len(ids) == len(set(ids)) >= 10, ids
rows = dict(re.findall(r"^\| (G\d+) \| ([^|]+)\|", readme, re.M))
refs = []
for name in ("README.md", "test.sh", "run.py", "provenance.json"):
    refs += [(name, m) for m in re.findall(r"\bgap ([A-Za-z]?\d+)", open(name).read())]
dangling = [(f, g) for f, g in refs if g not in rows]
assert not dangling, f"references that name no row of the gap table: {dangling}"
assert len(refs) >= 12, f"only {len(refs)} gap references found; the walk read nothing"
# and the two messages the mapping check carries name the row that is about it
mapping_gap = [g for g, claim in rows.items() if "instruments" in claim]
assert len(mapping_gap) == 1, mapping_gap
checked = 0
for line in open("test.sh"):
    if line.lstrip().startswith("assert") and "update gap" in line:
        assert f"gap {mapping_gap[0]}" in line, line.strip()
        checked += 1
assert checked == 2, f"{checked} mapping assertions carry a gap pointer, expected 2"
print(len(refs), "gap references, every one resolving into", len(rows), "keyed rows")
PY6
check "every gap reference resolves to a row keyed by id, not by position" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
