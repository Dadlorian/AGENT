#!/usr/bin/env bash
# The visible check for examples/steer. Everything here is measured, not claimed.
#
# It prints `passed N, failed 0` with N counting checks that actually ran, and
# the gate at the bottom has two halves: no failure, and a floor under the count.
# A gutted copy of this file counts zero and is refused at the floor rather than
# exiting 0 (`F-a7-03` "A deterministic gate can be structurally green and mean
# nothing"). FLOOR moves with provenance.json's visible_checks_counted, and a
# check below asserts the two agree.
#
# Every extension point in README section 6 is proved here by a differential
# run: the same door or unit twice, one declared value changed, the two records
# asserted different in the named way. A green run at the default value proves
# the default path and nothing else. Each assertion block ends in exactly one
# `check`, so no check reads the exit status of the check before it.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=96
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }
run()  { name=$1; shift; python3 run.py "$@" --ledger "out/$name.jsonl" --report "out/$name.json" \
         > "out/$name.log" 2>&1; echo $?; }

rm -rf out && mkdir -p out

echo "1. four doors, one unit, one steer declaration each"
check "human exits 0"    "$(run human --entry entries/human.json)" "0"
check "event exits 0"    "$(run event --entry entries/event.json)" "0"
check "schedule exits 3" "$(run schedule --entry entries/schedule.json)" "3"
check "external exits 3" "$(run external --entry entries/external.json)" "3"
py <<'PY' > out/doors.log 2>&1
import json, sys
sys.path.insert(0, "../end-to-end")
from run import validate                      # one validator, two document shapes
entry_schema = json.load(open("../end-to-end/schemas/entry.schema.json"))
steer_schema = json.load(open("schemas/steer.schema.json"))
errs = 0
for d in ("human", "event", "schedule", "external"):
    doc = json.load(open(f"entries/{d}.json"))
    errs += len(validate(doc, entry_schema)) + len(validate(doc["payload"]["steer"], steer_schema))
assert errs == 0, f"{errs} validation errors across the four documents"
print("four entry documents and four steer declarations validate")
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
assert len({r["unit"] for rows in led.values() for r in rows if "unit" in r}) == 1
print("one unit declaration, four actors, four run ids, four correlation ids")
PY
check "one unit through four doors, four actors, four correlations" "$?" "0"
py <<'PY' > out/same-decision.log 2>&1
import json
seen = set()
for d in ("human", "event", "schedule", "external"):
    rep = json.load(open(f"out/{d}.json"))
    row = [r for r in rep["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
    seen.add((row["decision_point"], row["action"], row["effect"], row["rule_id"],
              json.dumps(row["resource"], sort_keys=True)))
assert len(seen) == 1, seen
print("one effect, four doors, one decision:", sorted(seen)[0][:4])
PY
check "the same action is decided the same way through every door" "$?" "0"
py <<'PY' > out/entry-kind.log 2>&1
import json
bundles = [json.load(open(f"policy/bundle.{v}.json")) for v in ("v1", "v2")]
paths = [c["path"] for b in bundles for r in b["rules"] for c in r["when"]]
paths += [c["value"] for b in bundles for r in b["rules"] for c in r["when"]
          if c["op"].endswith("_field")]
assert "context.entry_kind" not in paths, paths
print("the door is carried on the input and read by no rule:", sorted(set(paths)))
PY
check "the door the work came in by is carried and read by no rule" "$?" "0"

echo "1b. the unit is the one the envelope points at"
py <<'PY2'
import copy, json
u = json.load(open("units/steer-checkout-coupon-fix.json"))
def w(name, doc): json.dump(doc, open(f"out/{name}.json", "w"), indent=1)
d = copy.deepcopy(u); d["attempt_class"] = "f-grunt"; w("unit-free", d)
d = copy.deepcopy(u); d["tenant"] = "tenant-other"; w("unit-cross-tenant", d)
d = copy.deepcopy(u); d["effect"]["scope"] = "external"; w("unit-external-scope", d)
d = copy.deepcopy(u); d["steering"]["decisions_offered"] = ["approve", "reject"]; w("unit-no-edit", d)
d = copy.deepcopy(u); d["intervention_policy"]["permitted"] = ["reconnect"]; w("unit-no-replace", d)
d = copy.deepcopy(u); d["intervention_policy"]["checkpoint_before_turn"] = False; w("unit-nocheckpoint", d)
e = json.load(open("entries/human.json"))
f = copy.deepcopy(e); f["intent"]["workflow_ref"] = "out/unit-free.json"
f["correlation"] = {"run_id": "run-steer-free", "correlation_id": "corr-steer-free", "depth": 0}
w("entry-free", f)
s = copy.deepcopy(e); s["actor"] = {"subject": "user:stranger",
                                    "delegation_chain": [{"actor": "user:stranger", "obtained_via": "direct"}]}
s["correlation"] = {"run_id": "run-steer-stranger", "correlation_id": "corr-steer-stranger", "depth": 0}
w("entry-stranger", s)
p = copy.deepcopy(e); p["payload"]["steer"]["policy_version"] = "sha256:" + "0" * 64; w("entry-pinned", p)
m = copy.deepcopy(e); del m["budget"]; m["kind"] = "telepathy"; w("malformed", m)
x = json.load(open("entries/external.json"))          # the door that declares correlation.depth
d = copy.deepcopy(x); d["correlation"]["depth"] = 99; w("entry-depth99", d)
d = copy.deepcopy(x); del d["correlation"]["depth"]; w("entry-nodepth", d)
PY2
check "the unit named by intent.workflow_ref runs, with no --unit flag" "$(run free --entry out/entry-free.json)" "0"
py <<'PY' > out/workflow-ref.log 2>&1
import json
free, paid = (json.load(open(f"out/{n}.json")) for n in ("free", "human"))
klass = lambda rep: [r["resource"]["model_class"] for r in rep["decisions"]
                     if r["decision_point"] == "dispatch.model_call"]
assert klass(free) == ["f-grunt"] and klass(paid) == ["i-fast"], (klass(free), klass(paid))
assert free["run"]["cost_micros"] == 0 < paid["run"]["cost_micros"], \
    (free["run"]["cost_micros"], paid["run"]["cost_micros"])
rows = [json.loads(l) for l in open("out/free.jsonl")]
sub = [r for r in rows if r["kind"] == "unit-submitted"][0]
assert sub["workflow_ref"] == "out/unit-free.json" and sub["attempt_class"] == "f-grunt", sub
print("two workflow_refs, two classes on the decision:", klass(paid), klass(free))
PY
check "changing intent.workflow_ref changes the class the decision names and the price" "$?" "0"
# The carried-and-not-consumed table claims `correlation.depth` is carried and
# read by nothing. That is a differential like any other: the same door twice,
# the declared value at 99 and then absent, and the two runs asserted to agree
# on every record - while the depth that is on the record is the one derived
# from the chain, which neither run declared.
run depth99 --entry out/entry-depth99.json > /dev/null
run nodepth  --entry out/entry-nodepth.json  > /dev/null
py <<'PY' > out/depth.log 2>&1
import json
a, b = (json.load(open(f"out/{n}.json")) for n in ("depth99", "nodepth"))
declared = [json.load(open(f"out/entry-{n}.json"))["correlation"].get("depth")
            for n in ("depth99", "nodepth")]
assert declared == [99, None], declared
def key(rep):                # the minted unit id is the clock's, not the declaration's
    rows = []
    for r in rep["decisions"]:
        res = {k: ("<minted>" if k == "unit_id" else v) for k, v in r["resource"].items()}
        rows.append((r["decision_point"], r["action"], r["effect"], r["rule_id"],
                     json.dumps(res, sort_keys=True)))
    return rows
assert key(a) == key(b) and len(key(a)) == 9, (len(key(a)), key(a), key(b))
assert a["status"] == b["status"], (a["status"], b["status"])
# the frame count is the boundary's wall clock, so the stream is compared with
# the per-frame progress events collapsed
stream = lambda rep: [t for t in rep["events_on_the_stream"] if t != "step.progress"]
assert stream(a) == stream(b), (stream(a), stream(b))
assert "step.progress" in a["events_on_the_stream"] and "step.progress" in b["events_on_the_stream"]
for field in ("disposition", "effect_fired", "retries", "escalations", "cost_micros"):
    assert a["run"][field] == b["run"][field], field
assert [r["type"] for r in a["run"]["refusals"]] == [r["type"] for r in b["run"]["refusals"]]
chain = len(json.load(open("entries/external.json"))["actor"]["delegation_chain"])
for name in ("depth99", "nodepth"):
    depths = {r["delegation_depth"] for r in (json.loads(l) for l in open(f"out/{name}.jsonl"))}
    assert depths == {chain}, (name, depths)
print("depth 99 and no depth at all decide identically; every record carries", chain)
PY
check "correlation.depth is carried and consumed by nothing, measured both ways" "$?" "0"

echo "2. the decision precedes the action it admits, at every point"
py <<'PY' > out/ordering.log 2>&1
import json
for d in ("human", "event", "schedule", "external"):
    j = json.load(open(f"out/{d}.json"))["journal"]
    assert j["decisions_taken"] == j["decided_before_that_action_spent"] > 0, (d, j)
    assert j["denied_dispatch_spend_micros"] == 0, (d, j)
print("every decision preceded the first metered call of the action it admits")
PY
check "every action's decision precedes that action's own spend" "$?" "0"
py <<'PY' > out/attributable.log 2>&1
import json, re
digest = re.compile(r"^sha256:[0-9a-f]{64}$")
n = 0
for d in ("human", "event", "schedule", "external"):
    rep = json.load(open(f"out/{d}.json"))
    assert rep["journal"]["rule_id_present_on_every_decision"] is True, d
    for row in rep["decisions"]:
        assert row["rule_id"] not in ("", "-"), row          # allow as well as deny
        assert digest.match(row["policy_version"]), row
        assert digest.match(row["input_digest"]), row
        n += 1
print(n, "decisions, every one attributable to a rule and pinned to a version")
PY
check "an allow is attributed and pinned, not only a deny" "$?" "0"

echo "3. an allow is spent: the pause, and the rules in force on the far side"
check "a rule set revised while the unit is parked exits 3" \
      "$(run revise --entry entries/human.json --revise-policy)" "3"
py <<'PY' > out/spent.log 2>&1
import json
plain, revised = (json.load(open(f"out/{n}.json")) for n in ("human", "revise"))
assert len(plain["policy_versions"]) == 1 and len(revised["policy_versions"]) == 2
a, b = (r["run"]["effect_decision_before_pause"] for r in (plain, revised))
c, d = (r["run"]["effect_decision_after_resume"] for r in (plain, revised))
assert (a["effect"], c["effect"]) == ("allow", "allow"), (a, c)
assert (b["effect"], d["effect"]) == ("allow", "deny"), (b, d)
assert d["rule_id"] == "deny-effect-under-change-freeze", d
assert b["policy_version"] != d["policy_version"], "the two decisions were pinned to one version"
# counted out of the decision rows, not read off the field the runner wrote
# about itself: a gutted fire_effect that decided nothing could still set it
at_effect = lambda rep: len([r for r in rep["decisions"] if r["decision_point"] == "dispatch.tool_call"])
assert at_effect(plain) == at_effect(revised) == 2, (at_effect(plain), at_effect(revised))
assert plain["run"]["decisions_at_effect"] == revised["run"]["decisions_at_effect"] == 2
print("pre-pause allow under", b["policy_version"][:14], "post-resume deny under", d["policy_version"][:14])
PY
check "the resumed effect is decided again, under the rules in force then" "$?" "0"
py <<'PY' > out/notfired.log 2>&1
import json
plain, revised = (json.load(open(f"out/{n}.json")) for n in ("human", "revise"))
assert plain["run"]["effect_fired"] is True and revised["run"]["effect_fired"] is False
assert revised["status"] == "failed", revised["status"]
rows = [json.loads(l) for l in open("out/revise.jsonl")]
assert not [r for r in rows if r["kind"] == "effect-applied"], "the frozen effect was applied"
refusal = [r for r in rows if r["kind"] == "refusal" and r["step"] == "effect-resumed"][0]
assert refusal["rule_id"] == "deny-effect-under-change-freeze" and refusal["ends_unit"] is True
print("the unit that was admitted to fire the effect ends failed, and it never fired")
PY
check "a unit admitted to fire an effect holds no residual authorisation" "$?" "0"
py <<'PY' > out/replay.log 2>&1
import json
rep = json.load(open("out/revise.json"))
before, replayed = rep["run"]["effect_decision_before_pause"], rep["replayed_pre_pause_decision"]
assert replayed["effect"] == "allow" and replayed["rule_id"] == before["rule_id"], (before, replayed)
assert replayed["policy_version"] == before["policy_version"] == rep["policy_versions"]["v1"]
assert rep["policy_versions"]["v2"] != rep["policy_versions"]["v1"]
print("the pre-pause decision still replays to", replayed["effect"], "under its pinned version")
PY
check "a decision replays against the bundle version it was pinned to" "$?" "0"
check "the deliberate breakage exits 0 where the honest run exits 3" \
      "$(run carry --entry entries/human.json --revise-policy --carry-decision)" "0"
py <<'PY' > out/breakage.log 2>&1
import json
honest, broken = (json.load(open(f"out/{n}.json")) for n in ("revise", "carry"))
# the 2 -> 1 is counted out of the decision rows that carry the fact; the
# runner's own decisions_at_effect field is then asserted to agree with them
at_effect = lambda rep: len([r for r in rep["decisions"] if r["decision_point"] == "dispatch.tool_call"])
assert at_effect(honest) == 2 and at_effect(broken) == 1, (at_effect(honest), at_effect(broken))
assert honest["run"]["decisions_at_effect"] == at_effect(honest)
assert broken["run"]["decisions_at_effect"] == at_effect(broken)
assert honest["run"]["effect_fired"] is False and broken["run"]["effect_fired"] is True
assert broken["run"]["effect_decision_after_resume"]["carried"] is True
rows = [json.loads(l) for l in open("out/carry.jsonl")]
applied = [r for r in rows if r["kind"] == "effect-applied"][0]
assert applied["decided_again"] is False and applied["policy_version"] == honest["policy_versions"]["v1"]
print("carrying the pre-pause allow fires an effect the rules in force now refuse")
PY
check "carrying the pre-pause allow fires an effect the current rules refuse" "$?" "0"
py <<'PY' > out/bundles.log 2>&1
import json
v1, v2 = (json.load(open(f"policy/bundle.{v}.json")) for v in ("v1", "v2"))
assert v1["entity_model"] == v2["entity_model"], "the two bundles declare different entity models"
assert v2["rules"] == v1["rules"][:1] + [v2["rules"][1]] + v1["rules"][1:], "v2 is not v1 plus one rule"
assert v2["rules"][1]["rule_id"] == "deny-effect-under-change-freeze"
assert v1["default"] == v2["default"] and v1["default"]["effect"] == "deny"
print(len(v1["rules"]), "rules, then", len(v2["rules"]), "- one rule apart, deny by default in both")
PY
check "the second bundle is the first plus exactly one rule, and both deny by default" "$?" "0"

echo "4. approve, edit, reject, retry, escalate"
py <<'PY' > out/decisions.log 2>&1
import json
approved, edited = (json.load(open(f"out/{n}.json")) for n in ("human", "event"))
proposed = json.load(open("units/steer-checkout-coupon-fix.json"))["gate"]["proposed"]["artifact"]
reviewer = json.load(open("entries/event.json"))["payload"]["steer"]["decision_body"]
assert approved["run"]["artifact"] == proposed, approved["run"]["artifact"]
assert edited["run"]["artifact"] == reviewer != proposed, edited["run"]["artifact"]
assert approved["run"]["disposition"] == edited["run"]["disposition"] == "accept"
print("approve continues with the proposal; edit continues with the reviewer's body")
PY
check "approve keeps the proposal, edit replaces it with the reviewer's own" "$?" "0"
BIG=$(python3 -c "import json;print(json.dumps({'component':'pricing/coupon.py','note':'x'*400}))")
check "a diff-sized edit on the parked-item surface exits 3" \
      "$(run bigparked --entry entries/event.json --decision edit --decision-body "$BIG")" "3"
check "the same edit on the stream surface exits 0" \
      "$(run bigstream --entry entries/event.json --surface stream --decision edit --decision-body "$BIG")" "0"
py <<'PY' > out/surface.log 2>&1
import json
small, big, wide = (json.load(open(f"out/{n}.json")) for n in ("event", "bigparked", "bigstream"))
assert small["binding"]["max_edit_bytes"] == big["binding"]["max_edit_bytes"] == 256
assert wide["binding"]["max_edit_bytes"] == 65536, wide["binding"]
assert small["binding"]["delivery_model"] == "request_response"
assert wide["binding"]["delivery_model"] == "stream"
refused = [r for r in big["run"]["refusals"] if r["where"] == "decision"][0]
assert refused["status"] == 422 and refused["type"].endswith("document-invalid"), refused
assert big["run"]["artifact"] is None and wide["run"]["artifact"]["note"].startswith("xxx")
assert len(wide["events_rendered"]) > len(small["events_rendered"]), "one store, two projections"
print("the same edit body:", small["binding"]["max_edit_bytes"], "refuses it,",
      wide["binding"]["max_edit_bytes"], "applies it")
PY
check "the declared surface changes what a decision may carry, not what the platform stores" "$?" "0"
check "retries_permitted 0 exits 3" "$(run r0 --entry entries/external.json --retries 0)" "3"
check "escalation steps_permitted 0 exits 3" \
      "$(run e0 --entry entries/external.json --escalation-steps 0)" "3"
py <<'PY' > out/retry.log 2>&1
import json
def count(n, kind): return sum(1 for l in open(f"out/{n}.jsonl") if json.loads(l)["kind"] == kind)
assert (count("external", "retry"), count("r0", "retry")) == (1, 0), "the retry bound was not read"
assert (len(json.load(open("out/external.json"))["run"]["attempts"]),
        len(json.load(open("out/r0.json"))["run"]["attempts"])) == (2, 1)
print("retries 1 -> one retry row and two attempts; retries 0 -> none and one")
PY
check "the declared retry bound is read at the loop, not written into it" "$?" "0"
py <<'PY' > out/escalation.log 2>&1
import json
def count(n, kind): return sum(1 for l in open(f"out/{n}.jsonl") if json.loads(l)["kind"] == kind)
assert (count("external", "escalation"), count("e0", "escalation")) == (1, 0)
assert count("e0", "escalation-declined") == 1, "a declined escalation left no record"
assert json.load(open("out/external.json"))["run"]["escalations"] == 1
assert json.load(open("out/e0.json"))["run"]["escalated_ask"] is None
print("one class of step, taken once where permitted and not at all where it is not")
PY
check "the declared escalation step is taken exactly once, or not at all" "$?" "0"
py <<'PY' > out/escalated.log 2>&1
import json
rep = json.load(open("out/external.json"))
unit = json.load(open("units/steer-checkout-coupon-fix.json"))
ask = rep["run"]["escalated_ask"]
assert ask["escalated"] is True and ask["decided_by"] == unit["steering"]["escalation"]["authority"]
rows = [json.loads(l) for l in open("out/external.jsonl")]
esc = [r for r in rows if r["kind"] == "escalation"][0]
assert esc["authority"] == unit["steering"]["escalation"]["authority"], esc
assert esc["trigger"] == unit["steering"]["escalation"]["trigger"], esc
assert [p["escalated"] for p in rows if p["kind"] == "approval-parked"] == [False, False, True]
print("escalated to", esc["authority"], "after", esc["attempts_spent"], "attempts")
PY
check "the escalation goes to the authority the unit names, on its declared trigger" "$?" "0"
check "the escalation authority may approve, and the unit completes" \
      "$(run escok --entry entries/external.json --escalation-decision approve)" "0"
check "a decider who is not the named authority is refused" \
      "$(run wrongauth --entry entries/external.json --escalation-decision approve --decider user:corey)" "3"
py <<'PY' > out/authority.log 2>&1
import json
good, bad = (json.load(open(f"out/{n}.json")) for n in ("escok", "wrongauth"))
g = [r for r in good["decisions"] if r["decision_point"] == "steer.decision"][-1]
b = [r for r in bad["decisions"] if r["decision_point"] == "steer.decision"][-1]
assert (g["effect"], b["effect"]) == ("allow", "deny"), (g, b)
assert b["rule_id"] == "deny-decision-outside-named-authority", b
assert b["work_ran"] is False and b["spend_after_micros"] == b["spend_before_micros"]
assert good["run"]["effect_fired"] is True and bad["run"]["effect_fired"] is False
print("the named authority decides; anyone else is refused by", b["rule_id"])
PY
check "who may decide an escalated ask is a rule, not a convention" "$?" "0"
check "a decision the unit does not offer exits 3" \
      "$(run noedit --entry entries/event.json --unit out/unit-no-edit.json)" "3"
py <<'PY' > out/offered.log 2>&1
import json
rep = json.load(open("out/noedit.json"))
unit = json.load(open("out/unit-no-edit.json"))
refusal = [r for r in rep["run"]["refusals"] if r["where"] == "decision"][0]
assert refusal["type"].endswith("document-invalid") and refusal["status"] == 422, refusal
rows = [json.loads(l) for l in open("out/noedit.jsonl")]
parked = [r for r in rows if r["kind"] == "approval-parked"][0]
assert parked["offered"] == ",".join(unit["steering"]["decisions_offered"]), parked
assert "edit" not in parked["offered"]
assert json.load(open("out/event.json"))["status"] == "completed"
print("the same door and the same decision:", parked["offered"], "-> refused 422")
PY
check "steering.decisions_offered is read: a decision not offered is refused 422" "$?" "0"
py <<'PY' > out/replayed-decision.log 2>&1
import json
rep = json.load(open("out/human.json"))
row = rep["run"]["attempts"][0]
assert row["replay_outcome"] == "duplicate", row["replay_outcome"]
assert row["second_decision_refused"].endswith("idempotency-conflict"), row
assert row["resumed_on_same_correlation"] is True, row
assert row["resume_delegation_depth"] == 2, row["resume_delegation_depth"]
assert rep["events_on_the_stream"].count("human.decided") == 1, rep["events_on_the_stream"]
print("one decision applied once, redelivered free, contradicted at 409")
PY
check "a redelivered decision is free and a contradicting one is 409" "$?" "0"
run twice --entry entries/human.json > /dev/null
check "the same envelope submitted twice parks no second ask" \
      "$(run twice --entry entries/human.json)" "2"

echo "5. the deadline, and the door with nobody behind it"
py <<'PY' > out/expired.log 2>&1
import json
rep = json.load(open("out/schedule.json"))
steer = json.load(open("entries/schedule.json"))["payload"]["steer"]
unit = json.load(open("units/steer-checkout-coupon-fix.json"))
assert steer["decision_delay_seconds"] > unit["gate"]["deadline_seconds"], steer
assert rep["events_on_the_stream"].count("ask.expired") == 1, rep["events_on_the_stream"]
assert "human.decided" not in rep["events_on_the_stream"]
refusal = [r for r in rep["run"]["refusals"] if r["where"] == "ask"][0]
assert refusal["type"].endswith("deadline-exceeded") and refusal["status"] == 504, refusal
assert rep["status"] == "failed" and rep["run"]["effect_fired"] is False
expired = [json.loads(l) for l in open("out/schedule.jsonl")]
assert [r for r in expired if r["kind"] == "ask-expired"][0]["ask_state"] == "expired"
print("the ask closed at its deadline and the unit ended rather than waiting")
PY
check "an ask nobody answers is terminal, and the run ends failed not hung" "$?" "0"
# the other side of the same declared value: `decision_delay_seconds` is read
# against `gate.deadline_seconds`, so the pair is the one run past it and the
# one run short of it. The deadline is the store's to enforce; a sweep asked for
# before the ask is due is refused, typed, rather than crashing the runner.
check "an ask swept before its deadline exits 3" \
      "$(run early --entry entries/schedule.json --decision none --delay 10)" "3"
py <<'PY' > out/early.log 2>&1
import json
late, early = (json.load(open(f"out/{n}.json")) for n in ("schedule", "early"))
unit = json.load(open("units/steer-checkout-coupon-fix.json"))["gate"]["deadline_seconds"]
delays = [json.load(open("entries/schedule.json"))["payload"]["steer"]["decision_delay_seconds"], 10]
assert delays[0] > unit > delays[1], (delays, unit)
lr = [r for r in late["run"]["refusals"] if r["where"] == "ask"][0]
er = [r for r in early["run"]["refusals"] if r["where"] == "ask"][0]
assert (lr["type"].rsplit(":", 1)[-1], lr["status"]) == ("deadline-exceeded", 504), lr
assert (er["type"].rsplit(":", 1)[-1], er["status"]) == ("document-invalid", 422), er
assert late["events_on_the_stream"].count("ask.expired") == 1
assert "ask.expired" not in early["events_on_the_stream"], early["events_on_the_stream"]
assert early["events_on_the_stream"][-2:] == ["human.refused", "run.finished"]
rows = [json.loads(l) for l in open("out/early.jsonl")]
assert not [r for r in rows if r["kind"] == "ask-expired"], "an ask that is still open was swept"
assert [r for r in rows if r["kind"] == "refusal" and r["step"] == "gate"][0]["status"] == 422
assert early["status"] == "failed" and early["run"]["effect_fired"] is False
assert "Traceback" not in open("out/early.log").read()
print("past the deadline 504 and the ask expires; short of it 422 and the ask stays open")
PY
check "a decision that never comes is typed on both sides of the deadline" "$?" "0"
py <<'PY' > out/vocab.log 2>&1
import json, sys
sys.path.insert(0, ".")
import harnesses
hi, _, _ = harnesses.human("dryrun")
seen = set()
for d in ("human", "event", "schedule", "external"):
    seen |= set(json.load(open(f"out/{d}.json"))["events_on_the_stream"])
assert seen <= set(hi.EVENT_TYPES), seen - set(hi.EVENT_TYPES)
assert seen == set(hi.EVENT_TYPES), set(hi.EVENT_TYPES) - seen
print("emitted", len(seen), "of", len(hi.EVENT_TYPES), "published event types")
PY
check "every event type emitted is published, and all eight are produced" "$?" "0"
py <<'PY' > out/lifecycle.log 2>&1
import json, sys
sys.path.insert(0, ".")
from run import TASK_STATES, DISPOSITIONS
for door, want in (("human", ["submitted", "input-required", "working", "completed"]),
                   ("schedule", ["submitted", "input-required", "failed", "failed"])):
    seen = [r["state"] for r in (json.loads(l) for l in open(f"out/{door}.jsonl")) if "state" in r]
    assert seen == want, (door, seen)
    assert set(seen) <= set(TASK_STATES), seen
dispositions = {json.load(open(f"out/{d}.json"))["run"]["disposition"]
                for d in ("human", "event", "schedule", "external", "escok")}
assert dispositions == {"accept", "reject"} <= set(DISPOSITIONS), dispositions
print("lifecycle adopted, never invented; dispositions", sorted(dispositions))
PY
check "the task lifecycle and the dispositions are adopted, never invented" "$?" "0"

echo "6. the operator: reconnect, restart, replace"
py <<'PY' > out/reconnect.log 2>&1
import json
rec = json.load(open("out/event.json"))["run"]["interventions"][0]
assert rec["operation"] == "reconnect" and rec["served"] is True
assert rec["unit_after"] == rec["unit_before"], rec
assert rec["negotiated"] == {"streaming": True, "permission_callbacks": True, "cancellation": True}
assert rec["reprovisioned"] is False
print("reconnect kept the unit id and negotiated what the class offers")
PY
check "reconnect re-attaches without a new unit and without re-resolving anything" "$?" "0"
py <<'PY' > out/restart.log 2>&1
import json
res = json.load(open("out/schedule.json"))["run"]["interventions"][0]
assert res["operation"] == "restart" and res["served"] is True
assert res["unit_after"] != res["unit_before"], res
assert res["state_digest_after"] == res["checkpoint_digest"], res
assert res["reprovisioned"] is False
print("restart returned a new unit at the checkpoint digest, unchanged")
PY
check "restart restores the checkpoint digest unchanged before any further call" "$?" "0"
py <<'PY' > out/replace.log 2>&1
import json
rep = json.load(open("out/external.json"))["run"]["interventions"][0]
assert rep["operation"] == "replace" and rep["served"] is True
assert rep["unit_after"] != rep["unit_before"], rep
assert rep["state_digest_after"] == rep["unit_digest_at_intervention"], rep
assert rep["state_digest_after"] != rep["checkpoint_digest"], "replace returned the checkpoint's state"
print("replace returned a clone of the stuck state, not of the checkpoint")
PY
check "replace carries the stuck unit's own state, which is not the checkpoint's" "$?" "0"
py <<'PY' > out/stuck.log 2>&1
import json
stuck = json.load(open("out/event.json"))["run"]["attempts"][0]
healthy = json.load(open("out/human.json"))["run"]["attempts"][0]
assert stuck["stuck"] is True and stuck["stop_reason"] == "terminated"
assert stuck["terminated_by"] == "budget-ceiling", stuck
assert healthy["stuck"] is False and healthy["stop_reason"] == "end_turn"
assert stuck["frames"] > healthy["frames"], (stuck["frames"], healthy["frames"])
assert json.load(open("out/external.json"))["run"]["attempts"][1]["stop_reason"] == "end_turn"
print("the ceiling ended the stuck turn from outside it:", stuck["stop_reason"],
      "by", stuck["terminated_by"])
PY
check "stall_first_turn is read: the boundary ends the stuck turn, the retry finishes" "$?" "0"
py <<'PY' > out/attach.log 2>&1
import json
rec = json.load(open("out/event.json"))["run"]["interventions"][0]
assert rec["attached_to_a_unit_the_boundary_had_destroyed"] is True, rec
assert json.load(open("out/event.json"))["run"]["attempts"][0]["stop_reason"] == "terminated"
print("reconnect succeeded against a unit the boundary had already destroyed - gap 3")
PY
check "reconnect attaches to a destroyed unit, and no operation says so" "$?" "0"
check "a unit that takes no checkpoint before its turn exits 3" \
      "$(run nocheckpoint --entry entries/schedule.json --unit out/unit-nocheckpoint.json)" "3"
py <<'PY' > out/checkpoint.log 2>&1
import json
with_, without = (json.load(open(f"out/{n}.json")) for n in ("schedule", "nocheckpoint"))
assert with_["run"]["attempts"][0]["checkpointed"] is True
assert without["run"]["attempts"][0]["checkpointed"] is False
assert [json.loads(l)["kind"] for l in open("out/nocheckpoint.jsonl")].count("cell-checkpointed") == 0
assert [json.loads(l)["kind"] for l in open("out/schedule.jsonl")].count("cell-checkpointed") == 1
a, b = (r["run"]["interventions"][0] for r in (with_, without))
assert a["checkpoint_digest"] != a["unit_digest_at_intervention"], a
assert b["checkpoint_digest"] == b["unit_digest_at_intervention"], b
assert a["state_digest_after"] != b["state_digest_after"], "restart returned the same state either way"
print("with a pre-turn checkpoint restart returns the state before the turn; without, the state after it")
PY
check "checkpoint_before_turn is read: it decides which state a restart returns" "$?" "0"
check "an intervention the unit does not permit exits 0" \
      "$(run notpermitted --entry entries/event.json --intervention replace --unit out/unit-no-replace.json)" "0"
py <<'PY' > out/permitted.log 2>&1
import json
rep = json.load(open("out/notpermitted.json"))
unit = json.load(open("out/unit-no-replace.json"))
row = rep["run"]["interventions"][0]
assert row["served"] is False and row["refused_by"] == "the unit's intervention policy", row
assert row["problem"]["status"] == 422 and row["problem"]["type"].endswith("document-invalid")
assert "replace" not in unit["intervention_policy"]["permitted"]
assert not [d for d in rep["decisions"] if d["decision_point"] == "steer.intervention"], \
    "an unpermitted operation still reached the decision point"
print("refused by the unit's own declaration, before any decision was asked for")
PY
check "intervention_policy.permitted is read before the decision point is reached" "$?" "0"
check "replace without a mandate exits 0 with the intervention refused" \
      "$(run noreplace --entry entries/human.json --intervention replace --stall)" "0"
py <<'PY' > out/mandate.log 2>&1
import json
without, with_ = (json.load(open(f"out/{n}.json")) for n in ("noreplace", "external"))
a = [d for d in without["decisions"] if d["decision_point"] == "steer.intervention"][0]
b = [d for d in with_["decisions"] if d["decision_point"] == "steer.intervention"][0]
assert (a["effect"], b["effect"]) == ("deny", "allow"), (a, b)
assert a["rule_id"] == "deny-replace-without-mandate" and a["work_ran"] is False
assert b["rule_id"] == "allow-intervention" and b["work_ran"] is True
assert without["run"]["interventions"][0]["served"] is False
assert without["status"] == "completed", "a refused intervention ended the unit"
print("the same verb, two delegation chains:", a["effect"], "and", b["effect"])
PY
check "the mandate comes from the delegation chain, and it decides the verb" "$?" "0"
check "a containment class that cannot serve the verb exits 3" \
      "$(run cell2 --entry entries/schedule.json --cell second)" "3"
py <<'PY' > out/unsupported.log 2>&1
import json
one, two = (json.load(open(f"out/{n}.json")) for n in ("schedule", "cell2"))
assert one["cell_binding"]["lifecycle_offered"] == {"pause": True, "resume": True, "fork": True}
assert two["cell_binding"]["lifecycle_offered"] == {"pause": False, "resume": False, "fork": False}
row = two["run"]["interventions"][0]
assert row["served"] is False and row["problem"]["status"] == 501, row
assert row["problem"]["type"].endswith("isolation-operation-unsupported")
assert two["run"]["attempts"][0]["checkpointed"] is False
assert one["run"]["attempts"][0]["checkpointed"] is True
axes = set(one["cell_binding"]["execution_model"]) & set(two["cell_binding"]["execution_model"])
differ = [a for a in axes if one["cell_binding"]["execution_model"][a]
          != two["cell_binding"]["execution_model"][a]]
assert len(differ) == 4, differ
print("restart refused 501 on a class that offers no checkpoint;", len(differ), "axes differ")
PY
check "a lifecycle operation the class cannot serve is typed 501, never emulated" "$?" "0"
py <<'PY' > out/absent.log 2>&1
import json, sys
sys.path.insert(0, ".")
import harnesses
iface, _ = harnesses.errors()
rep = json.load(open("out/cell2.json"))
assert rep["run"]["interventions"][0]["problem"].get("registry") == "absent"
assert "isolation-operation-unsupported" not in iface.REGISTRY, "the registry now carries the row"
assert any(t.endswith("isolation-operation-unsupported") for t in rep["unregistered_types"])
print("the 501 has no row in the closed registry and is reported absent, not re-typed - gap 2")
PY
check "a type the closed registry has no row for is reported, never re-typed" "$?" "0"

echo "7. fail closed: an undecided request is refused at every enforcement point"
for point in admission.entry steer.intervention dispatch.model_call dispatch.tool_call steer.decision; do
  name="down-$(echo "$point" | tr '.' '-')"
  run "$name" --entry entries/event.json --engine-down-at "$point" > /dev/null
  py "$name" "$point" <<'PY' > "out/$name.check" 2>&1
import json, sys
name, point = sys.argv[1], sys.argv[2]
rep = json.load(open(f"out/{name}.json"))
rows = rep["decisions"]
first = [r for r in rows if r["effect"] == "undecided"]
assert first and first[0]["decision_point"] == point, (point, [r["effect"] for r in rows])
assert first[0]["problem_type"].endswith("adapter-unavailable"), first[0]
assert first[0]["work_ran"] is False, first[0]
assert first[0]["spend_after_micros"] == first[0]["spend_before_micros"], first[0]
after = rows[rows.index(first[0]) + 1:]
assert not [r for r in after if r["effect"] == "allow"], after
assert rep["status"] in ("rejected", "failed"), rep["status"]
print(point, "-> undecided, refused, nothing ran")
PY
  check "an unreachable engine refuses at $point, and nothing runs" "$?" "0"
done
py <<'PY' > out/distinct.log 2>&1
import json
undecided = json.load(open("out/down-admission-entry.json"))["decisions"][0]
assert undecided["effect"] == "undecided" and undecided["rule_id"] == "-"
rows = [json.loads(l) for l in open("out/down-admission-entry.jsonl")]
row = [r for r in rows if r["kind"] == "policy-decided"][0]
assert row["effect"] == "undecided" and row["problem_type"].endswith("adapter-unavailable")
assert row["rule_id"] == "-", row
print("an undecided request is recorded as undecided, with no rule to attribute it to")
PY
check "the fail-closed refusal is recorded as undecided, not as a policy deny" "$?" "0"
# The extension point the row claims: a builder adds a sixth enforcement point
# by registering its declared shape and calling admit there. The differential is
# the same request twice, the declared value being whether the point is
# registered - decided on one side, refused 422 with nothing run on the other.
py <<'PY' > out/sixth.log 2>&1
import copy, json, sys
sys.path.insert(0, ".")
import harnesses
pi, Adapter = harnesses.policy("dryrun")

SIXTH = "dispatch.data_query"
points = json.load(open("policy/points.json"))["points"]
shape = {"taken_at": "dispatch, before a free-form query reaches a store",
         "resource_schema": {"required": {"tenant": "string", "query": "string"},
                             "optional": {}, "additional": False}}
bundle = json.load(open("policy/bundle.v1.json"))
bundle = copy.deepcopy(bundle)
bundle["bundle_version_label"] = "six"
bundle["rules"] = [{"rule_id": "allow-data-query-in-tenant", "decision_point": SIXTH,
                    "effect": "allow", "detail": "a query inside the tenant's own store",
                    "when": [{"path": "resource.query", "op": "nonempty"}]}] + bundle["rules"]
json.dump(bundle, open("out/bundle.six.json", "w"), indent=1)

def request(engine):
    return pi.DecisionRequest.from_dict({
        "decision_point": SIXTH, "action": "query",
        "subject": {"id": "agent:partner-sre-bot", "tenant": "tenant-acme", "mandates": []},
        "resource": {"tenant": "tenant-acme", "query": "coupons where expired"},
        "context": {"run_id": "run-steer-sixth", "root_dispatch_id": "d-sixth"},
        "policy_version": engine.active_version})

def take(engine):
    ran = {"work": False}
    def work(meter):
        ran["work"] = True
        return meter.charge("d-sixth", 500)
    try:
        decision, _ = engine.admit(request(engine), work)
        return {"decided": True, "effect": decision.effect, "rule_id": decision.rule_id,
                "ran": ran["work"], "spent": engine.meter.spend("d-sixth")}
    except pi.Problem as exc:
        return {"decided": False, "type": exc.body["type"].rsplit(":", 1)[-1],
                "status": exc.body["status"], "ran": ran["work"],
                "spent": engine.meter.spend("d-sixth")}

registered = Adapter(bundle=bundle, points=points)
assert SIXTH not in registered.points, "the shipped registry already carries the sixth point"
name = registered.register_decision_point(SIXTH, shape)
assert name == SIXTH and SIXTH in registered.points
unregistered = Adapter(bundle=bundle, points=points)

a, b = take(registered), take(unregistered)
assert a == {"decided": True, "effect": "allow", "rule_id": "allow-data-query-in-tenant",
             "ran": True, "spent": 500}, a
assert b == {"decided": False, "type": "decision-point-unregistered", "status": 422,
             "ran": False, "spent": 0}, b
assert len(registered.journal) == 1 and not unregistered.journal, "an unregistered point was journalled"
print("registered ->", a["effect"], "by", a["rule_id"], "; unregistered -> 422, nothing ran")
PY
check "a sixth enforcement point is decided once registered and refused 422 until then" "$?" "0"
py <<'PY' > out/subset.log 2>&1
import json, sys
sys.path.insert(0, ".")
import harnesses
pi, Typed = harnesses.policy("second")

SIXTH = "dispatch.data_query"
points = json.load(open("policy/points.json"))["points"]
shipped = json.load(open("policy/bundle.v1.json"))
six = json.load(open("out/bundle.six.json"))          # the same bundle plus one rule
assert [r["rule_id"] for r in six["rules"]][1:] == [r["rule_id"] for r in shipped["rules"]]
assert "resource.query" not in six["entity_model"]["Resource"], "the model now declares it"

base = Typed(bundle=shipped, points=points)
assert list(base.conformance_subset) == [], base.conformance_subset
# and the field the runs carry says the same thing: on the shipped bundle no
# point is declared a subset, so every point either answered or refused
for name in ("human", "event", "schedule", "external"):
    assert json.load(open(f"out/{name}.json"))["journal"]["declared_subset"] == [], name

engine = Typed(bundle=six, points=points)
engine.register_decision_point(SIXTH, {"resource_schema": {"required": {"tenant": "string",
                                                                       "query": "string"},
                                                           "optional": {}, "additional": False}})
assert list(engine.conformance_subset) == [SIXTH], engine.conformance_subset
ran = {"work": False}
def work(meter):
    ran["work"] = True
    return meter.charge("d-subset", 500)
req = pi.DecisionRequest.from_dict({
    "decision_point": SIXTH, "action": "query",
    "subject": {"id": "agent:partner-sre-bot", "tenant": "tenant-acme", "mandates": []},
    "resource": {"tenant": "tenant-acme", "query": "coupons where expired"},
    "context": {"run_id": "run-steer-subset", "root_dispatch_id": "d-subset"},
    "policy_version": engine.active_version})
try:
    engine.admit(req, work)
    raise AssertionError("a point the binding declares outside its model answered")
except pi.Problem as exc:
    assert exc.body["type"].endswith("adapter-unavailable"), exc.body
    assert exc.body["declared_subset"] == [SIXTH], exc.body
assert ran["work"] is False and engine.meter.spend("d-subset") == 0
print("a rule outside the entity model makes the point a declared subset, refused not allowed")
PY
check "a declared subset is refused rather than answered allow" "$?" "0"

echo "8. refusals a caller branches on by type"
check "a cross-tenant unit exits 2" \
      "$(run xtenant --entry entries/human.json --unit out/unit-cross-tenant.json)" "2"
py <<'PY' > out/xtenant.check 2>&1
import json
rep = json.load(open("out/xtenant.json"))
assert rep["problem"]["status"] == 403 and rep["problem"]["rule_id"] == "deny-cross-tenant-resource"
assert rep["status"] == "rejected", rep["status"]
assert rep["admission"]["work_ran"] is False and rep["journal"]["denied_dispatch_spend_micros"] == 0
rows = [json.loads(l) for l in open("out/xtenant.jsonl")]
assert not [r for r in rows if r["kind"] == "cell-admitted"], "a cell was admitted anyway"
assert [r for r in rows if r["kind"] == "refusal"][0]["rule_id"] == "deny-cross-tenant-resource"
print("refused at admission, before a cell existed, naming", rep["problem"]["rule_id"])
PY
check "a refusal at admission names its rule and admits no cell" "$?" "0"
check "a principal the platform holds no tenancy for exits 2" \
      "$(run stranger --entry out/entry-stranger.json)" "2"
py <<'PY' > out/stranger.check 2>&1
import json
rep = json.load(open("out/stranger.json"))
assert rep["problem"]["status"] == 401 and rep["problem"]["type"].endswith("identity-untrusted")
assert rep["decisions"] == [], "a decision was asked for on an input that could not be assembled"
print("an unknown principal is not a principal with no mandates")
PY
check "an input that cannot be assembled is refused before any decision" "$?" "0"
check "a malformed envelope exits 2" "$(run bad --entry out/malformed.json)" "2"
grep -q "document-invalid" out/bad.log && ok "typed as document-invalid (422)" || bad "not typed"
grep -q "missing required property 'budget'" out/bad.log && ok "names the missing field" || bad "field not named"
[ -f out/bad.jsonl ] && bad "an invalid envelope wrote to a ledger" || ok "no ledger for an invalid envelope"
check "a caller pinning its own policy version exits 2" "$(run pinned --entry out/entry-pinned.json)" "2"
grep -q "'policy_version' is not allowed" out/pinned.log \
  && ok "the member a caller may not declare is named" || bad "the refusal does not name the member"
check "a caller trying to turn the gate off exits 2" "$(run bypass --entry entries/human.json --bypass)" "2"
grep -q "no advisory mode, no dry-run flag and no bypass" out/bypass.log \
  && ok "the vocabulary is closed: there is no bypass on this path" || bad "the bypass was not refused"
check "a ceiling that no longer covers the effect exits 3" \
      "$(run lowbudget --entry entries/human.json --budget-micros 4000)" "3"
py <<'PY' > out/budget.check 2>&1
import json
low, full = (json.load(open(f"out/{n}.json")) for n in ("lowbudget", "human"))
a = [r for r in low["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
b = [r for r in full["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
assert (a["effect"], b["effect"]) == ("deny", "allow"), (a, b)
assert a["rule_id"] == "deny-effect-with-no-budget-left", a
assert low["run"]["effect_fired"] is False and full["run"]["effect_fired"] is True
print("the ceiling is a rule the platform evaluates, not an alert it raises")
PY
check "the remaining ceiling is read by a rule, not by a branch in the runner" "$?" "0"
check "an external-scope effect without a mandate exits 3" \
      "$(run extscope-h --entry entries/human.json --unit out/unit-external-scope.json)" "3"
check "the same effect with a mandate exits 0" \
      "$(run extscope-x --entry entries/external.json --unit out/unit-external-scope.json --decision approve)" "0"
py <<'PY' > out/scope.check 2>&1
import json
h, x = (json.load(open(f"out/{n}.json")) for n in ("extscope-h", "extscope-x"))
a = [r for r in h["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
b = [r for r in x["decisions"] if r["decision_point"] == "dispatch.tool_call"][0]
assert a["resource"]["scope"] == b["resource"]["scope"] == "external"
assert (a["effect"], b["effect"]) == ("deny", "allow"), (a, b)
assert a["rule_id"] == "deny-external-effect-without-mandate"
assert b["rule_id"] == "allow-external-effect-under-mandate"
print("effect.scope is read: the same effect, two chains,", a["effect"], "and", b["effect"])
PY
check "effect.scope and the chain's mandates decide together" "$?" "0"
py <<'PY' > out/registry.check 2>&1
import json
rep = json.load(open("out/xtenant.json"))
dropped = set(rep["dropped_registry_members"])
assert {"policy-denied:decision_point", "policy-denied:input_digest",
        "policy-denied:policy_version", "policy-denied:spend_delta_micros"} <= dropped, dropped
assert "rule_id" in rep["problem"], rep["problem"]
assert "policy_version" not in rep["problem"], rep["problem"]
print("the closed registry carries the rule and drops the version - gap 1")
PY
check "the closed registry keeps the rule and drops the version a caller needs" "$?" "0"

echo "9. the swap: a second decision engine, one call shape"
for d in human event schedule external; do
  case "$d" in human|event) want=0 ;; *) want=3 ;; esac
  check "the second engine on the $d door exits $want" \
        "$(run "engine2-$d" --entry "entries/$d.json" --engine second)" "$want"
done
py <<'PY' > out/swap.log 2>&1
import json
key = lambda rep: [(r["decision_point"], r["action"], r["effect"], r["rule_id"]) for r in rep["decisions"]]
total = digests = 0
for d in ("human", "event", "schedule", "external"):
    one, two = json.load(open(f"out/{d}.json")), json.load(open(f"out/engine2-{d}.json"))
    assert key(one) == key(two), (d, key(one), key(two))
    assert one["status"] == two["status"] and one["run"]["disposition"] == two["run"]["disposition"]
    assert one["run"]["effect_fired"] == two["run"]["effect_fired"]
    for a, b in zip(one["decisions"], two["decisions"]):
        # the one input that differs between two runs of one door is the unit id a
        # fresh cell was given; where the input was the same bytes, so is its digest
        if a["resource"] == b["resource"]:
            assert a["input_digest"] == b["input_digest"], (d, a, b)
            digests += 1
        else:
            assert set(a["resource"]) == set(b["resource"]) == {"tenant", "operation", "unit_id"}
    total += len(key(one))
assert (total, digests) == (24, 21), (total, digests)
print(total, "decisions over four doors, identical across two engines;",
      digests, "byte-identical inputs, both digested the same")
PY
check "two engines answer the same corpus identically, from one call shape" "$?" "0"
py <<'PY' > out/pair.log 2>&1
import json
one, two = (json.load(open(f"out/{n}.json")) for n in ("human", "engine2-human"))
a, b = one["journal"]["engine"], two["journal"]["engine"]
differ = [k for k in a if a[k] != b[k]]
assert len(differ) == 4, differ
assert one["engine_adapter"] != two["engine_adapter"]
print("the pair differs on", len(differ), "execution-model axes:", sorted(differ))
PY
check "the pair is two decision models, not one engine run twice" "$?" "0"
py <<'PY' > out/namecheck.log 2>&1
import os, re
# The claim is about this whole directory and everything a run of it writes, not
# about one log: a product name in a comment, in a rule's detail, in a unit
# declaration or on any other door's output would have passed the one-file grep
# this replaces. The lines that carry the list itself are marked and skipped.
NAMES = r"\bopa\b|rego|cedar|styra|openfga|firecracker|openai|anthropic|langfuse"   # grep: namecheck, a list of product names that are forbidden elsewhere
CALLER_ONLY = r"\bvendors?\b"                                                       # namecheck
MARK = "namecheck"                                                                  # namecheck
name_re, caller_re = re.compile(NAMES, re.I), re.compile(CALLER_ONLY, re.I)

def allowed_readme_lines():
    """The two tables a product may be named in, as line numbers."""
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
assert len(sources) > 10 and len(artifacts) > 40, (len(sources), len(artifacts))

exempt = allowed_readme_lines()
hits = []
for path in sources + artifacts:
    if path.endswith((".pyc", ".png")):
        continue
    for i, line in enumerate(open(path, errors="replace").read().splitlines()):
        if MARK in line or (path == "./README.md" and i in exempt):
            continue
        pattern = caller_re if path.startswith("./out/") else None
        if name_re.search(line) or (pattern and pattern.search(line)):
            hits.append(f"{path}:{i + 1}")
assert not hits, hits
print(len(sources), "source files and", len(artifacts), "artifacts scanned, no product named")
PY
check "no product or engine is named outside the standards and adapters tables" "$?" "0"
py <<'PY' > out/nolib.log 2>&1
import json
for d in ("human", "event", "schedule", "external"):
    blob = json.dumps(json.load(open(f"entries/{d}.json"))).lower()
    for banned in ("import ", "sdk", "client_library", "adapter", "engine", "policy_version"):
        assert banned not in blob, (d, banned)
print("four documents, no client library of ours and no engine named in any of them")
PY
check "a caller needs no client library this repository wrote" "$?" "0"

echo "10. the receipt"
python3 run.py --verify-ledger --ledger out/human.jsonl > out/verify.log 2>&1
check "the chain verifies" "$?" "0"
sed '3s/"cost_micros": [0-9]*/"cost_micros": 1/' out/human.jsonl > out/tampered.jsonl
python3 run.py --verify-ledger --ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a one-character edit is detected" "$?" "2"
py <<'PY' > out/receipt.log 2>&1
import json
rows = [json.loads(l) for l in open("out/external.jsonl")]
kinds = [r["kind"] for r in rows]
for want in ("unit-submitted", "policy-decided", "cell-admitted", "cell-checkpointed",
             "turn-observed", "intervention", "model-called", "approval-parked",
             "approval-returned", "retry", "escalation", "refusal", "unit-failed"):
    assert want in kinds, want
assert len(set(kinds)) == 13, sorted(set(kinds))
# the kind that carries this area's central claim - a rule set starting to serve
# while the unit is parked - is on the ledger of the run that revises one
revised = {r["kind"] for r in (json.loads(l) for l in open("out/revise.jsonl"))}
assert "policy-activated" in revised, sorted(revised)
for r in rows:
    for field in ("run_id", "correlation_id", "actor", "delegation_depth", "entry_kind",
                  "idempotency_key"):
        assert field in r, (r["kind"], field)
print(len(rows), "records, every one stamped, covering", len(set(kinds)), "kinds")
PY
check "every record is stamped with the actor, the chain depth and the door" "$?" "0"
py <<'PY' > out/kinds.log 2>&1
import glob, json, re
# no count of record kinds is written that was not read back out of the ledgers:
# the README's receipt row is asserted against the kinds every run actually wrote
written = set()
for path in glob.glob("out/*.jsonl"):
    written |= {json.loads(line)["kind"] for line in open(path)}
row = [l for l in open("README.md") if l.startswith("| The receipt:")][0]
named = {token.strip() for span in re.findall(r"`([^`]+)`", row) for token in span.split(r"\|")}
named = {t for t in named if re.fullmatch(r"[a-z]+(?:-[a-z]+)*", t)}
assert named == written, (f"named and never written: {sorted(named - written)}; "
                          f"written and never named: {sorted(written - named)}")
assert len(written) == 19, len(written)
print(len(written), "record kinds on the ledgers, and the receipt row names exactly those")
PY
check "the receipt row names every record kind the runs write, and no others" "$?" "0"

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
doc = json.load(open("../../docs/architecture/proposed/steer.json"))
assert doc["area"] == "fleet state management"
assert len(doc["gaps"]) >= 6 and all(g["research_query"] and g["status"] == "unresearched"
                                     for g in doc["gaps"]), doc["gaps"]
assert all(r["origin"] == "proposed" for r in doc["state_types"] + doc["tool_entries"])
print(len(doc["gaps"]), "proposed blueprint gaps, every one with a research query")
PY
check "the proposed blueprint rows are proposed and every gap carries a query" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
